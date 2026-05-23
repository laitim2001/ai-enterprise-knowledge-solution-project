"""Layout-aware chunker unit tests (per CLAUDE.md §5.6 H6 — chunker is critical pipeline).

Synthetic ParserResult fixtures avoid real .docx parsing latency in unit tests.
End-to-end smoke (real .docx → chunk) lives in scripts/run_chunker_sanity.py.
"""

from pathlib import Path

import pytest

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
