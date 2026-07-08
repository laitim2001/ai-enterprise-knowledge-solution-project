"""Layout-aware chunker unit tests (per CLAUDE.md §5.6 H6 — chunker is critical pipeline).

Synthetic ParserResult fixtures avoid real .docx parsing latency in unit tests.
End-to-end smoke (real .docx → chunk) lives in scripts/run_chunker_sanity.py.
"""

from pathlib import Path

from ingestion.chunker.base import ChunkSpec
from ingestion.chunker.layout_aware import LayoutAwareChunker
from ingestion.chunker.strategies import select_chunker
from ingestion.parsers.base import (
    EmbeddedImage,
    ParagraphItem,
    ParserResult,
    Table,
)


def _heading(level: int, text: str, doc_order: int) -> ParagraphItem:
    return ParagraphItem(text=text, kind="heading", doc_order=doc_order, heading_level=level)


def _para(text: str, doc_order: int) -> ParagraphItem:
    return ParagraphItem(text=text, kind="text", doc_order=doc_order)


def _build_result(
    paragraphs: list[ParagraphItem],
    tables: list[Table] | None = None,
    images: list[EmbeddedImage] | None = None,
) -> ParserResult:
    return ParserResult(
        source_path=Path("synthetic.docx"),
        doc_format="docx",
        doc_title="Synthetic Doc",
        paragraphs=paragraphs,
        tables=tables or [],
        embedded_images=images or [],
    )


def test_simple_three_section_doc_emits_three_chunks() -> None:
    """H1 sections under H2 root → section_path depth correct + 3 chunks.

    W25 / ADR-0033 (b): paragraph sizes bumped from *20 (~100 tokens) to *40
    (~200 tokens) so each section stays above _MIN_CHUNK_MERGE_FLOOR (160)
    and the section-boundary behaviour under test is preserved without
    being swallowed by adjacent-short-merge consolidation.
    """
    paragraphs = [
        _heading(2, "Chapter 1", 0),
        _heading(3, "1.1 Intro", 1),
        _para("Intro body paragraph one. " * 40, 2),
        _heading(3, "1.2 Steps", 3),
        _para("Step description body. " * 40, 4),
        _heading(3, "1.3 Conclusion", 5),
        _para("Conclusion body. " * 40, 6),
    ]
    chunks = LayoutAwareChunker().chunk(_build_result(paragraphs))

    text_chunks = [c for c in chunks if c.chunk_kind == "text"]
    assert len(text_chunks) == 3, f"expected 3 text chunks, got {len(text_chunks)}"

    # All chunks under "Chapter 1" → depth-2 section_path
    titles = [c.chunk_title for c in text_chunks]
    assert titles == ["1.1 Intro", "1.2 Steps", "1.3 Conclusion"]
    for c in text_chunks:
        assert c.section_path[0] == "Chapter 1"
        assert len(c.section_path) == 2


def test_section_under_target_emits_one_chunk_with_low_value_flag_when_below_floor() -> None:
    """Section text < 100 tokens (architecture.md §3.3 soft floor) → low_value_flag=True."""
    paragraphs = [
        _heading(2, "Tiny Section", 0),
        _para("Short text.", 1),
    ]
    chunks = LayoutAwareChunker().chunk(_build_result(paragraphs))

    assert len(chunks) == 1
    assert chunks[0].low_value_flag is True
    assert chunks[0].chunk_token_count < 100


def test_long_section_splits_at_paragraph_boundaries() -> None:
    """Section accumulating > target_tokens splits at paragraph boundary."""
    # Each para ~100 tokens, target=200 → expect ~3 chunks for 6 paragraphs
    paragraphs = [
        _heading(2, "Long Section", 0),
        *[_para(f"Paragraph {i}: " + "word " * 95, i + 1) for i in range(6)],
    ]
    chunker = LayoutAwareChunker(target_tokens=200, hard_cap_tokens=600)
    chunks = chunker.chunk(_build_result(paragraphs))

    assert len(chunks) >= 2, f"expected at least 2 chunks, got {len(chunks)}"
    # Each emitted chunk respects hard cap
    for c in chunks:
        assert c.chunk_token_count <= 600
    # All chunks share section_path
    for c in chunks:
        assert c.section_path == ["Long Section"]
        assert c.chunk_title == "Long Section"


def test_table_emits_independent_chunk_with_kind_table() -> None:
    """Per architecture.md §3.3 — table 獨立 chunk with section_path inheritance."""
    paragraphs = [
        _heading(2, "With Table", 0),
        _para("Pre-table text", 1),
    ]
    table = Table(
        rows=[["a", "b"], ["c", "d"]],
        headers=["Col1", "Col2"],
        doc_order=2,
    )
    chunks = LayoutAwareChunker().chunk(_build_result(paragraphs, tables=[table]))

    table_chunks = [c for c in chunks if c.chunk_kind == "table"]
    assert len(table_chunks) == 1
    tc = table_chunks[0]
    assert tc.chunk_kind == "table"
    assert tc.section_path == ["With Table"]
    assert "Col1 | Col2" in tc.chunk_text
    assert "a | b" in tc.chunk_text


def test_image_position_attaches_to_open_section() -> None:
    """Embedded image at doc_order under a heading → recorded in chunk.embedded_image_positions."""
    paragraphs = [
        _heading(2, "Section With Image", 0),
        _para("Body text " * 30, 1),
    ]
    image = EmbeddedImage(
        image_bytes=b"\x89PNG\r\n",
        alt_text="alt",
        doc_order=2,
        ext="png",
        sha256="0" * 64,
    )
    chunks = LayoutAwareChunker().chunk(_build_result(paragraphs, images=[image]))

    text_chunks = [c for c in chunks if c.chunk_kind == "text"]
    assert text_chunks
    assert any("img@2" in c.embedded_image_positions for c in text_chunks)


def test_parse_failed_returns_empty_chunks() -> None:
    """parse_failed=True → empty chunk list (orchestrator records FailureRecord)."""
    result = ParserResult(
        source_path=Path("broken.docx"),
        doc_format="docx",
        doc_title="Broken",
        paragraphs=[],
        parse_failed=True,
        parse_error="ZipFileError",
    )
    chunks = LayoutAwareChunker().chunk(result)
    assert chunks == []


def test_chunk_text_format_is_title_concat_body_per_spec() -> None:
    """architecture.md §3.3 — chunk_text = chunk_title + '\\n\\n' + chunk_content."""
    paragraphs = [
        _heading(2, "My Title", 0),
        _para("Body content " * 30, 1),
    ]
    chunks = LayoutAwareChunker().chunk(_build_result(paragraphs))
    assert chunks
    assert chunks[0].chunk_text.startswith("My Title\n\n")


def test_strategy_selector_routes_docx_auto_to_layout_aware() -> None:
    chunker = select_chunker("docx", "auto")
    assert isinstance(chunker, LayoutAwareChunker)


def test_strategy_selector_routes_pdf_auto_to_layout_aware() -> None:
    chunker = select_chunker("pdf", "auto")
    assert isinstance(chunker, LayoutAwareChunker)


def test_strategy_selector_pptx_auto_returns_layout_aware() -> None:
    """W4 D1 F9: slide_based now delegates to LayoutAwareChunker since
    PptxParser emits the same heading-paragraph-table-image structure
    (per slide synthetic 'Slide N' heading + title + body + tables + pictures)."""
    chunker = select_chunker("pptx", "auto")
    assert isinstance(chunker, LayoutAwareChunker)


def test_strategy_selector_explicit_layout_aware_returns_layout_aware() -> None:
    chunker = select_chunker("docx", "layout_aware")
    assert isinstance(chunker, LayoutAwareChunker)


# ─── W25 / ADR-0033 (a) floor lowered 100 → 60 ─────────────────────


def test_w25_floor_60_marks_chunks_below_60_low_value() -> None:
    """ADR-0033 (a): floor lowered 100→60. Body ~30 tokens still low_value."""
    paragraphs = [
        _heading(2, "Tiny Section", 0),
        _para("word " * 30, 1),  # ~30 token body, well below 60 floor
    ]
    # Disable merge so floor behaviour can be inspected on a single chunk.
    chunks = LayoutAwareChunker(min_chunk_merge_floor=0).chunk(_build_result(paragraphs))
    assert len(chunks) == 1
    assert chunks[0].low_value_flag is True
    assert chunks[0].chunk_token_count < 60


def test_w25_floor_60_keeps_60_to_99_token_chunks_high_value() -> None:
    """ADR-0033 (a): chunks in [60, 100) range no longer flagged (was pre-W25).

    Demonstrates the reclamation envelope — body sized to land between the
    old floor (100) and the new floor (60) so the chunk would have been
    low_value=True under the W2 baseline but stays high_value post-W25.
    """
    paragraphs = [
        _heading(2, "Mid Section", 0),
        _para("alpha beta gamma delta " * 18, 1),  # ~70 token body
    ]
    chunks = LayoutAwareChunker(min_chunk_merge_floor=0).chunk(_build_result(paragraphs))
    assert len(chunks) == 1
    chunk = chunks[0]
    assert chunk.chunk_token_count >= 60
    assert chunk.chunk_token_count < 100  # in the reclamation envelope
    assert chunk.low_value_flag is False


# ─── W25 / ADR-0033 (b) adjacent-short-merge ───────────────────────


def test_w25_adjacent_short_merge_combines_two_subsections() -> None:
    """ADR-0033 (b): two short text chunks (< 160 each) consolidate to one."""
    paragraphs = [
        _heading(2, "Parent", 0),
        _heading(3, "Sub A", 1),
        _para("alpha " * 60, 2),  # ~60 token body
        _heading(3, "Sub B", 3),
        _para("beta " * 60, 4),  # ~60 token body
    ]
    chunks = LayoutAwareChunker().chunk(_build_result(paragraphs))
    text_chunks = [c for c in chunks if c.chunk_kind == "text"]
    assert len(text_chunks) == 1, f"expected 1 merged chunk, got {len(text_chunks)}"
    # Backward-merge: combined chunk keeps prev's chunk_title + section_path
    assert text_chunks[0].chunk_title == "Sub A"
    assert "alpha" in text_chunks[0].chunk_text
    assert "beta" in text_chunks[0].chunk_text


def test_w25_merge_does_not_combine_with_table_chunk() -> None:
    """ADR-0033 (b): tables stay independent — no merge across kind boundary."""
    paragraphs = [
        _heading(2, "Section", 0),
        _para("short before table " * 8, 1),  # short text chunk
    ]
    table = Table(rows=[["a", "b"]], headers=["c1", "c2"], doc_order=2)
    chunks = LayoutAwareChunker().chunk(_build_result(paragraphs, tables=[table]))
    text_chunks = [c for c in chunks if c.chunk_kind == "text"]
    table_chunks = [c for c in chunks if c.chunk_kind == "table"]
    assert len(text_chunks) == 1
    assert len(table_chunks) == 1


def test_w25_merge_respects_hard_cap() -> None:
    """ADR-0033 (b): combined token count > hard_cap → merge skipped."""
    # Two ~140-token chunks (< merge floor 160) but combined > hard_cap 200.
    paragraphs = [
        _heading(2, "Parent", 0),
        _heading(3, "Sub A", 1),
        _para("alpha " * 130, 2),
        _heading(3, "Sub B", 3),
        _para("beta " * 130, 4),
    ]
    chunker = LayoutAwareChunker(
        target_tokens=500, hard_cap_tokens=200, min_chunk_merge_floor=160,
    )
    chunks = chunker.chunk(_build_result(paragraphs))
    for c in chunks:
        assert c.chunk_token_count <= 200, "hard_cap must be respected even when merge skipped"


def test_w25_merge_reindexes_contiguous_zero_to_n() -> None:
    """ADR-0033 (b): post-merge chunks have chunk_index 0..N-1 contiguous."""
    paragraphs = [
        _heading(2, "Parent", 0),
        _heading(3, "Sub A", 1), _para("alpha " * 60, 2),
        _heading(3, "Sub B", 3), _para("beta " * 60, 4),
        _heading(3, "Sub C", 5), _para("gamma word " * 50, 6),
    ]
    chunks = LayoutAwareChunker().chunk(_build_result(paragraphs))
    indices = [c.chunk_index for c in chunks]
    assert indices == list(range(len(chunks))), (
        f"expected contiguous 0..{len(chunks) - 1}, got {indices}"
    )


def test_w25_long_sections_do_not_merge() -> None:
    """ADR-0033 (b): sections both ≥ merge floor 160 stay independent."""
    paragraphs = [
        _heading(2, "Parent", 0),
        _heading(3, "Sub A", 1),
        _para("alpha beta gamma delta " * 60, 2),  # ~240 token body
        _heading(3, "Sub B", 3),
        _para("eta theta iota kappa " * 60, 4),  # ~240 token body
    ]
    chunks = LayoutAwareChunker().chunk(_build_result(paragraphs))
    text_chunks = [c for c in chunks if c.chunk_kind == "text"]
    assert len(text_chunks) == 2
    assert text_chunks[0].chunk_title == "Sub A"
    assert text_chunks[1].chunk_title == "Sub B"


def test_w25_merge_concatenates_embedded_image_positions() -> None:
    """ADR-0033 (b): merged chunk inherits union of both chunks' image positions."""
    paragraphs = [
        _heading(2, "Parent", 0),
        _heading(3, "Sub A", 1),
        _para("alpha " * 60, 2),
        _heading(3, "Sub B", 4),
        _para("beta " * 60, 5),
    ]
    images = [
        EmbeddedImage(image_bytes=b"\x89PNG", alt_text="a", doc_order=3, ext="png", sha256="a" * 64),
        EmbeddedImage(image_bytes=b"\x89PNG", alt_text="b", doc_order=6, ext="png", sha256="b" * 64),
    ]
    chunks = LayoutAwareChunker().chunk(_build_result(paragraphs, images=images))
    text_chunks = [c for c in chunks if c.chunk_kind == "text"]
    assert len(text_chunks) == 1  # both short sub-sections merged
    # Merged chunk carries both image positions
    positions = text_chunks[0].embedded_image_positions
    assert "img@3" in positions
    assert "img@6" in positions


# ─── W25 / ADR-0033 (a)+(b) regression envelope ────────────────────


def test_w25_synthetic_corpus_chunk_count_within_twenty_percent_envelope() -> None:
    """ADR-0033 acceptance F1.3.3: synthetic 6-section corpus chunk count
    must remain within ±20% of the pre-W25 expectation under the *same*
    paragraph sizes (mid-size 100-200 token sub-sections — the regime
    where W25 merge most aggressively consolidates).

    Pre-W25: 6 sections each ~100 tokens emitted as 6 distinct chunks.
    Post-W25 W expected: same 6 sections may consolidate to 2-4 chunks
    (3-section runs combine if all < 160). The ±20% envelope is enforced
    against an explicit upper bound (6 chunks pre = 7 chunks tolerance)
    and lower bound (2 chunks tolerance).
    """
    paragraphs = [
        _heading(2, "Chapter 1", 0),
        _heading(3, "1.1", 1), _para("text alpha " * 50, 2),
        _heading(3, "1.2", 3), _para("text beta " * 50, 4),
        _heading(3, "1.3", 5), _para("text gamma " * 50, 6),
        _heading(2, "Chapter 2", 7),
        _heading(3, "2.1", 8), _para("text delta " * 50, 9),
        _heading(3, "2.2", 10), _para("text epsilon " * 50, 11),
        _heading(3, "2.3", 12), _para("text zeta " * 50, 13),
    ]
    chunks = LayoutAwareChunker().chunk(_build_result(paragraphs))
    text_chunks = [c for c in chunks if c.chunk_kind == "text"]
    # Pre-W25 baseline = 6; W25 post-merge expected 2-4. Envelope = [2, 7].
    assert 2 <= len(text_chunks) <= 7, (
        f"chunk count {len(text_chunks)} outside ±20% envelope [2, 7]"
    )
    # All emitted chunks have contiguous indices.
    assert [c.chunk_index for c in chunks] == list(range(len(chunks)))


# ─── BUG-017 sibling-only merge guard regression coverage ──────────


def test_bug017_merge_does_not_cross_section_boundary() -> None:
    """BUG-017: two short text chunks under DIFFERENT top-level sections
    must NOT merge — preserves section semantic identity + image attribution.

    Reproduces the production scenario: section "3. Architectural" last
    short chunk + section "4. High-level architecture" intro short chunk.
    Pre-fix: backward-merge into section 3's last chunk, inheriting wrong
    section_path. Post-fix: same-parent guard skips merge → 2 distinct
    chunks preserved, each with its own correct section_path.
    """
    paragraphs = [
        _heading(1, "3. Architectural principles", 0),
        _heading(2, "3.7 Idempotency and retry safety", 1),
        _para("All operations must be idempotent " * 10, 2),  # ~60 tokens
        _heading(1, "4. High-level architecture", 3),
        _para("The diagram below presents " * 10, 4),  # ~60 tokens (intro)
    ]
    chunks = LayoutAwareChunker().chunk(_build_result(paragraphs))
    text_chunks = [c for c in chunks if c.chunk_kind == "text"]
    assert len(text_chunks) == 2, (
        f"BUG-017: cross-section merge must not fire, got {len(text_chunks)} chunks: "
        f"{[c.chunk_title for c in text_chunks]}"
    )
    # Section 3.7 chunk retains its identity
    assert text_chunks[0].section_path == [
        "3. Architectural principles", "3.7 Idempotency and retry safety",
    ]
    # Section 4 chunk retains its (separate) identity
    assert text_chunks[1].section_path == ["4. High-level architecture"]


def test_bug017_within_section_siblings_still_merge() -> None:
    """BUG-017 positive control: sibling sub-sections under same non-trivial
    parent still merge per W25 F1 ADR-0033 (b) intent (e.g., 1.1 + 1.2 under
    "Chapter 1"). Existing W25 F1 envelope test depends on this behaviour;
    this is a focused assertion that the sibling-only guard doesn't over-
    restrict the W25 F1 within-section consolidation benefit.
    """
    paragraphs = [
        _heading(1, "Chapter 1", 0),
        _heading(2, "1.1", 1), _para("alpha " * 60, 2),
        _heading(2, "1.2", 3), _para("beta " * 60, 4),
    ]
    chunks = LayoutAwareChunker().chunk(_build_result(paragraphs))
    text_chunks = [c for c in chunks if c.chunk_kind == "text"]
    assert len(text_chunks) == 1, (
        f"BUG-017 sibling merge: siblings under same parent must merge, "
        f"got {len(text_chunks)} chunks"
    )
    # Backward-merge inherits prev (1.1) identity
    assert text_chunks[0].chunk_title == "1.1"
    assert "alpha" in text_chunks[0].chunk_text
    assert "beta" in text_chunks[0].chunk_text


def test_bug017_image_section_identity_preserved_under_short_intro() -> None:
    """BUG-017 image attribution: when section B has a small intro chunk
    holding an image, and section A's last chunk is also small, the merge
    must NOT fire — preserves the image's section_path identity (section B).

    This is the exact failure mode reported in W25 D2 user-eye verify:
    Figure 1 belongs to section 4 visually but was attributed to section
    3.7's chunk via cross-section backward-merge.
    """
    paragraphs = [
        _heading(1, "3. Architectural principles", 0),
        _heading(2, "3.7 Idempotency", 1),
        _para("idempotent ops " * 10, 2),  # ~30 tokens, short
        _heading(1, "4. High-level architecture", 3),
        _para("The diagram below " * 10, 4),  # ~30 tokens, short — has image
    ]
    images = [
        EmbeddedImage(
            image_bytes=b"\x89PNG",
            alt_text="Figure 1",
            doc_order=5,  # AFTER section 4 intro paragraph
            ext="png",
            sha256="f" * 64,
        ),
    ]
    chunks = LayoutAwareChunker().chunk(_build_result(paragraphs, images=images))
    text_chunks = [c for c in chunks if c.chunk_kind == "text"]
    assert len(text_chunks) == 2, (
        f"BUG-017 image isolation: section-boundary merge must not fire, "
        f"got {len(text_chunks)} chunks"
    )
    # Section 4's chunk owns the image — NOT section 3.7's
    section_3_chunk = text_chunks[0]
    section_4_chunk = text_chunks[1]
    assert section_3_chunk.section_path == [
        "3. Architectural principles", "3.7 Idempotency",
    ]
    assert section_3_chunk.embedded_image_positions == [], (
        "BUG-017: section 3.7's chunk must NOT carry section 4's image"
    )
    assert section_4_chunk.section_path == ["4. High-level architecture"]
    assert "img@5" in section_4_chunk.embedded_image_positions, (
        "BUG-017: section 4's chunk must own its image"
    )


def test_chunkspec_has_all_required_fields_for_orchestrator() -> None:
    """F5 orchestrator + F4 embedder need these fields to build ChunkRecord (architecture.md §3.5)."""
    paragraphs = [
        _heading(2, "Root", 0),
        _para("Body " * 30, 1),
    ]
    chunks = LayoutAwareChunker().chunk(_build_result(paragraphs))
    assert chunks
    c = chunks[0]
    assert isinstance(c, ChunkSpec)
    # Required for ChunkRecord conversion at F5
    assert c.section_path
    assert c.chunk_title
    assert c.chunk_text
    assert c.chunk_token_count > 0
    assert c.chunk_kind in ("text", "table")
    assert c.chunk_index >= 0
    assert isinstance(c.low_value_flag, bool)
    assert isinstance(c.embedded_image_positions, list)


# ─── W44 / ADR-0041 切法 D — image-density deep fix ─────────────────


def _dense_images(count: int, start_doc_order: int = 2) -> list[EmbeddedImage]:
    """N synthetic embedded images at consecutive doc_orders (image-dense section)."""
    return [
        EmbeddedImage(
            image_bytes=b"\x89PNG",
            alt_text=f"fig{i}",
            doc_order=start_doc_order + i,
            ext="png",
            sha256=f"{i:064x}",
        )
        for i in range(count)
    ]


def test_w44_image_cap_force_splits_dense_section() -> None:
    """ADR-0041 切法 D — an image-dense section (20 imgs, default cap 8) force-splits
    into sub-chunks so no single chunk exceeds the cap (root fix for 圖洪 ci=15=57)."""
    paragraphs = [_heading(2, "Dense Steps", 0), _para("Short step body.", 1)]
    chunks = LayoutAwareChunker().chunk(
        _build_result(paragraphs, images=_dense_images(20)),
    )
    text_chunks = [c for c in chunks if c.chunk_kind == "text"]
    assert text_chunks
    assert all(len(c.embedded_image_positions) <= 8 for c in text_chunks), (
        f"a chunk exceeded the image cap: "
        f"{[len(c.embedded_image_positions) for c in text_chunks]}"
    )
    # 20 imgs / cap 8 → at least 3 sub-chunks; all carry the same section_path
    assert len(text_chunks) >= 3
    assert all(c.section_path == ["Dense Steps"] for c in text_chunks)


def test_w44_image_cap_no_image_loss() -> None:
    """ADR-0041 — force-split distributes ALL images; none dropped (total preserved)."""
    chunks = LayoutAwareChunker().chunk(
        _build_result([_heading(2, "Dense", 0), _para("body", 1)], images=_dense_images(20)),
    )
    all_positions = [p for c in chunks for p in c.embedded_image_positions]
    assert len(all_positions) == 20
    assert sorted(all_positions) == sorted(f"img@{2 + i}" for i in range(20))


def test_w44_cap_none_preserves_whole_section_pile_on() -> None:
    """ADR-0041 — cap=None → pre-W44 whole-section pile-on (bit-identical): all
    images land on a single section chunk, no force-split."""
    chunks = LayoutAwareChunker(max_images_per_chunk=None).chunk(
        _build_result([_heading(2, "Dense", 0), _para("body", 1)], images=_dense_images(20)),
    )
    text_chunks = [c for c in chunks if c.chunk_kind == "text"]
    assert max(len(c.embedded_image_positions) for c in text_chunks) == 20


def test_w44_merge_image_guard_blocks_over_cap_consolidation() -> None:
    """ADR-0041 — two short sibling sub-sections whose combined images exceed the
    cap must NOT be merged by ADR-0033 adjacent-short-merge (image-guard)."""
    paragraphs = [
        _heading(2, "Parent", 0),
        _heading(3, "Sub A", 1),
        _para("alpha", 2),
        _heading(3, "Sub B", 8),
        _para("beta", 9),
    ]
    images = [
        EmbeddedImage(image_bytes=b"\x89PNG", alt_text=f"a{i}", doc_order=3 + i,
                      ext="png", sha256=f"a{i:063x}")
        for i in range(5)  # Sub A: 5 imgs (doc_order 3-7)
    ] + [
        EmbeddedImage(image_bytes=b"\x89PNG", alt_text=f"b{i}", doc_order=10 + i,
                      ext="png", sha256=f"b{i:063x}")
        for i in range(5)  # Sub B: 5 imgs (doc_order 10-14)
    ]
    text_chunks = [
        c for c in LayoutAwareChunker().chunk(_build_result(paragraphs, images=images))
        if c.chunk_kind == "text"
    ]
    # 5 + 5 = 10 > cap 8 → guard blocks merge → 2 separate chunks, each ≤ cap
    assert len(text_chunks) == 2, (
        f"image-guard must block over-cap merge, got {len(text_chunks)} chunks"
    )
    assert all(len(c.embedded_image_positions) <= 8 for c in text_chunks)


def test_w44_residual_images_flushed_on_section_tail() -> None:
    """ADR-0041 — a section-tail image batch left after a force-split (images but
    no new text) is still flushed, never dropped."""
    chunks = LayoutAwareChunker().chunk(
        _build_result([_heading(2, "Dense", 0), _para("body", 1)], images=_dense_images(10)),
    )
    all_positions = [p for c in chunks for p in c.embedded_image_positions]
    assert len(all_positions) == 10  # 8 + 2 residual, none lost
    img_counts = sorted(
        len(c.embedded_image_positions) for c in chunks if c.chunk_kind == "text"
    )
    assert img_counts == [2, 8]


# ─── W70 / ADR-0055 inline image markers (chunk_text_marked) ────────


def test_w70_marked_text_interleaves_markers_by_doc_order() -> None:
    """ADR-0055 AC2 — chunk_text_marked carries [IMG@<doc_order>] placeholders
    strictly at the image's document position; chunk_text stays clean."""
    paragraphs = [
        _heading(2, "Section", 0),
        _para("Step one body.", 1),
        _para("Step two body.", 3),
    ]
    images = [
        EmbeddedImage(
            image_bytes=b"\x89PNG", alt_text="a", doc_order=2, ext="png", sha256="a" * 64
        ),
        EmbeddedImage(
            image_bytes=b"\x89PNG", alt_text="b", doc_order=4, ext="png", sha256="b" * 64
        ),
    ]
    chunks = LayoutAwareChunker().chunk(_build_result(paragraphs, images=images))
    assert len(chunks) == 1
    c = chunks[0]
    assert c.chunk_text == "Section\n\nStep one body.\n\nStep two body."
    assert c.chunk_text_marked == (
        "Section\n\nStep one body.\n\n[IMG@2]\n\nStep two body.\n\n[IMG@4]"
    )
    assert c.embedded_image_positions == ["img@2", "img@4"]


def test_w70_chunk_text_never_contains_markers_and_token_count_stays_clean() -> None:
    """ADR-0055 G3 — across a composite doc (dense images forcing 切法 D splits,
    plus a table), chunk_text carries no marker and chunk_token_count is still
    computed from the clean text only."""
    import tiktoken

    paragraphs = [
        _heading(2, "Dense Steps", 0),
        _para("Short step body.", 1),
        _heading(2, "Plain", 30),
        _para("Plain body " * 40, 31),
    ]
    table = Table(rows=[["a", "b"]], headers=["c1", "c2"], doc_order=32)
    chunks = LayoutAwareChunker().chunk(
        _build_result(paragraphs, tables=[table], images=_dense_images(12)),
    )
    enc = tiktoken.get_encoding("cl100k_base")
    assert chunks
    for c in chunks:
        assert "[IMG@" not in c.chunk_text
        assert c.chunk_token_count == len(enc.encode(c.chunk_text))


def test_w70_marked_empty_when_no_images() -> None:
    """ADR-0055 — marker-less chunks (text, table, and post-merge text) carry
    chunk_text_marked == "" so downstream falls back to chunk_text."""
    paragraphs = [
        _heading(2, "Parent", 0),
        _heading(3, "Sub A", 1),
        _para("alpha " * 60, 2),
        _heading(3, "Sub B", 3),
        _para("beta " * 60, 4),
    ]
    table = Table(rows=[["a", "b"]], headers=["c1", "c2"], doc_order=5)
    chunks = LayoutAwareChunker().chunk(_build_result(paragraphs, tables=[table]))
    assert chunks
    assert all(c.chunk_text_marked == "" for c in chunks)


def test_w70_soft_target_flush_resets_flow_between_subchunks() -> None:
    """ADR-0055 — soft-target flush point: each sub-chunk's marked text carries
    only its own paragraphs + markers; nothing leaks across the flush."""
    para_a = "alpha " * 220  # ~220 tokens ≥ target 200 → flush on append
    para_b = "beta " * 220
    paragraphs = [
        _heading(2, "Sec", 0),
        _para(para_a, 2),
        _para(para_b, 4),
    ]
    images = [
        EmbeddedImage(
            image_bytes=b"\x89PNG", alt_text="a", doc_order=1, ext="png", sha256="a" * 64
        ),  # before para A
        EmbeddedImage(
            image_bytes=b"\x89PNG", alt_text="b", doc_order=3, ext="png", sha256="b" * 64
        ),  # between A and B
    ]
    chunker = LayoutAwareChunker(target_tokens=200, hard_cap_tokens=600)
    chunks = chunker.chunk(_build_result(paragraphs, images=images))
    text_chunks = [c for c in chunks if c.chunk_kind == "text"]
    assert len(text_chunks) == 2
    first, second = text_chunks
    assert first.chunk_text_marked == f"Sec\n\n[IMG@1]\n\n{para_a}"
    assert second.chunk_text_marked == f"Sec\n\n[IMG@3]\n\n{para_b}"


def test_w70_hard_cap_preflush_keeps_pending_paragraph_out_of_marked() -> None:
    """ADR-0055 — hard-cap pre-flush point: the flushed chunk's marked text ends
    at the marker; the paragraph that triggered the flush starts the next flow."""
    para_a = "alpha " * 150  # ~150 tokens
    para_b = "beta " * 150  # prospective 300 > hard cap 200 → pre-flush
    paragraphs = [
        _heading(2, "Sec", 0),
        _para(para_a, 1),
        _para(para_b, 3),
    ]
    images = [
        EmbeddedImage(
            image_bytes=b"\x89PNG", alt_text="a", doc_order=2, ext="png", sha256="a" * 64
        ),  # after para A
    ]
    chunker = LayoutAwareChunker(target_tokens=500, hard_cap_tokens=200)
    chunks = chunker.chunk(_build_result(paragraphs, images=images))
    text_chunks = [c for c in chunks if c.chunk_kind == "text"]
    assert len(text_chunks) == 2
    first, second = text_chunks
    assert first.chunk_text_marked == f"Sec\n\n{para_a}\n\n[IMG@2]"
    assert second.chunk_text_marked == ""
    assert "beta" in second.chunk_text


def test_w70_force_flush_marker_batches_match_image_positions() -> None:
    """ADR-0055 — 切法 D force-flush point: each sub-chunk's markers mirror its
    embedded_image_positions batch exactly; 10 imgs / cap 8 → 8 + 2, no leak."""
    import re as _re

    chunks = LayoutAwareChunker().chunk(
        _build_result([_heading(2, "Dense", 0), _para("body", 1)], images=_dense_images(10)),
    )
    text_chunks = [c for c in chunks if c.chunk_kind == "text"]
    assert len(text_chunks) == 2
    for c in text_chunks:
        markers = _re.findall(r"\[IMG@(\d+)\]", c.chunk_text_marked)
        assert [f"img@{m}" for m in markers] == c.embedded_image_positions
    total_markers = [
        m for c in text_chunks for m in _re.findall(r"\[IMG@\d+\]", c.chunk_text_marked)
    ]
    assert len(total_markers) == 10
    assert len(set(total_markers)) == 10


def test_w70_oversized_standalone_paragraph_snapshots_prior_markers() -> None:
    """ADR-0055 — oversized-standalone emit point mirrors the pre-existing
    image snapshot semantics: the standalone chunk carries the accumulated
    markers WITHOUT resetting them (so the residual-image tail chunk repeats
    them, exactly like embedded_image_positions does today)."""
    para_huge = "huge " * 320  # ≥ hard cap 300, emitted standalone
    paragraphs = [
        _heading(2, "Sec", 0),
        _para(para_huge, 2),
    ]
    images = [
        EmbeddedImage(
            image_bytes=b"\x89PNG", alt_text="a", doc_order=1, ext="png", sha256="a" * 64
        ),
    ]
    chunker = LayoutAwareChunker(target_tokens=200, hard_cap_tokens=300)
    chunks = chunker.chunk(_build_result(paragraphs, images=images))
    text_chunks = [c for c in chunks if c.chunk_kind == "text"]
    assert len(text_chunks) == 2  # standalone + residual-image tail
    standalone, tail = text_chunks
    assert standalone.chunk_text_marked == f"Sec\n\n[IMG@1]\n\n{para_huge}"
    # Tail repeats the snapshot — parallel to its embedded_image_positions.
    assert tail.embedded_image_positions == ["img@1"]
    assert tail.chunk_text_marked == "Sec\n\n[IMG@1]"


def test_w70_merge_combines_marked_with_clean_text_fallback() -> None:
    """ADR-0055 — adjacent-short-merge: a marker-less side contributes its
    clean chunk_text so the merged marked stream stays complete."""
    paragraphs = [
        _heading(1, "Chapter 1", 0),
        _heading(2, "1.1", 1),
        _para("alpha " * 60, 2),
        _heading(2, "1.2", 4),
        _para("beta " * 60, 5),
    ]
    images = [
        EmbeddedImage(
            image_bytes=b"\x89PNG", alt_text="a", doc_order=3, ext="png", sha256="a" * 64
        ),  # in Sub 1.1, after its paragraph
    ]
    chunks = LayoutAwareChunker().chunk(_build_result(paragraphs, images=images))
    text_chunks = [c for c in chunks if c.chunk_kind == "text"]
    assert len(text_chunks) == 1  # short siblings merged
    merged = text_chunks[0]
    assert "[IMG@" not in merged.chunk_text
    assert "[IMG@3]" in merged.chunk_text_marked
    # Marker-less Sub 1.2 entered the marked stream via its clean text.
    assert "1.2" in merged.chunk_text_marked
    assert "beta" in merged.chunk_text_marked


def test_w70_cap_none_pile_on_marked_mirrors_image_accumulation() -> None:
    """ADR-0055 — cap=None (pre-W44 pile-on): image events survive each flush
    exactly like embedded_image_positions, so later sub-chunks re-emit earlier
    markers in lockstep with their (pile-on) image lists."""
    para_a = "alpha " * 220
    para_b = "beta " * 220
    paragraphs = [
        _heading(2, "Sec", 0),
        _para(para_a, 2),
        _para(para_b, 3),
    ]
    images = [
        EmbeddedImage(
            image_bytes=b"\x89PNG", alt_text="a", doc_order=1, ext="png", sha256="a" * 64
        ),
    ]
    chunker = LayoutAwareChunker(target_tokens=200, max_images_per_chunk=None)
    chunks = chunker.chunk(_build_result(paragraphs, images=images))
    text_chunks = [c for c in chunks if c.chunk_kind == "text"]
    assert len(text_chunks) == 2
    first, second = text_chunks
    assert first.chunk_text_marked == f"Sec\n\n[IMG@1]\n\n{para_a}"
    # Pile-on: second chunk re-carries the image AND its marker; not para A.
    assert second.embedded_image_positions == ["img@1"]
    assert second.chunk_text_marked == f"Sec\n\n[IMG@1]\n\n{para_b}"


def test_w44_under_cap_doc_identical_to_no_cap() -> None:
    """ADR-0041 — a normal section carrying < cap images produces the SAME chunks
    with cap=8 (default) and cap=None (no-op for under-cap, no-flush docs)."""
    paragraphs = [_heading(2, "Section", 0), _para("Body text " * 30, 1)]
    images = _dense_images(3)  # 3 < cap 8
    capped = LayoutAwareChunker(max_images_per_chunk=8).chunk(
        _build_result(paragraphs, images=images),
    )
    uncapped = LayoutAwareChunker(max_images_per_chunk=None).chunk(
        _build_result(paragraphs, images=images),
    )
    assert len(capped) == len(uncapped)
    assert [c.embedded_image_positions for c in capped] == [
        c.embedded_image_positions for c in uncapped
    ]
