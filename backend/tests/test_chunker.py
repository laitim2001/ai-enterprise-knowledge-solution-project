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
    """H1 sections under H2 root → section_path depth correct + 3 chunks."""
    paragraphs = [
        _heading(2, "Chapter 1", 0),
        _heading(3, "1.1 Intro", 1),
        _para("Intro body paragraph one. " * 20, 2),
        _heading(3, "1.2 Steps", 3),
        _para("Step description body. " * 20, 4),
        _heading(3, "1.3 Conclusion", 5),
        _para("Conclusion body. " * 20, 6),
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
