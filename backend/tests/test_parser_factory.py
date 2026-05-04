"""Parser factory + slide_based chunker unit tests (W4 D1 F9; per CLAUDE.md §5.6 H6).

Coverage:
- select_parser dispatches by file extension (.docx → DoclingDocxParser,
  .pptx → PptxParser, .pdf → DoclingDocxParser)
- select_parser raises ValueError for unsupported extension
- select_chunker(doc_format='pptx', strategy='auto') returns LayoutAwareChunker
  (slide_based delegates per W4 D1 F9 simplification)
- select_chunker still NotImplementedError for heading_aware standalone
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ingestion.chunker.layout_aware import LayoutAwareChunker
from ingestion.chunker.strategies import select_chunker
from ingestion.parsers import select_parser
from ingestion.parsers.docx_parser import DoclingDocxParser
from ingestion.parsers.pptx_parser import PptxParser


def test_select_parser_returns_pptx_parser_for_pptx() -> None:
    parser = select_parser(Path("/some/path/deck.pptx"))
    assert isinstance(parser, PptxParser)
    assert parser.doc_format == "pptx"


def test_select_parser_returns_docling_for_docx() -> None:
    parser = select_parser(Path("/some/path/manual.docx"))
    assert isinstance(parser, DoclingDocxParser)


def test_select_parser_returns_docling_for_pdf() -> None:
    parser = select_parser(Path("/some/path/report.pdf"))
    assert isinstance(parser, DoclingDocxParser)


def test_select_parser_uppercase_extension_normalised() -> None:
    parser = select_parser(Path("/some/path/DECK.PPTX"))
    assert isinstance(parser, PptxParser)


def test_select_parser_unsupported_extension_raises() -> None:
    with pytest.raises(ValueError, match=r"unsupported file extension"):
        select_parser(Path("/some/path/sheet.xlsx"))


def test_select_chunker_pptx_auto_returns_layout_aware() -> None:
    chunker = select_chunker(doc_format="pptx", strategy="auto")
    assert isinstance(chunker, LayoutAwareChunker)


def test_select_chunker_pptx_explicit_slide_based_returns_layout_aware() -> None:
    chunker = select_chunker(doc_format="pptx", strategy="slide_based")
    assert isinstance(chunker, LayoutAwareChunker)


def test_select_chunker_heading_aware_still_not_implemented() -> None:
    with pytest.raises(NotImplementedError, match=r"heading_aware"):
        select_chunker(doc_format="docx", strategy="heading_aware")
