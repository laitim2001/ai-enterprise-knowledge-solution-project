"""DoclingPdfParser structural tests (ADR-0019 W16+ Phase 3 P0.2 deliver; per CLAUDE.md §5.6 H6).

Tier 1 PDF parser scope per ADR-0019:
- Text-extractable PDF only (Word → PDF export, LibreOffice export, Adobe with text layer)
- Scanned PDF (OCR) + encrypted PDF (decryption) defer Tier 2 per architecture.md §11

Test coverage tiers:
- This file: structural tests that don't need sample PDF
  - Parser Protocol conformance (doc_format = "pdf", isinstance check via runtime_checkable)
  - select_parser routes .pdf → DoclingPdfParser
  - parse() with non-existent file → ParserResult(parse_failed=True) with error message
  - parse() never raises (Parser Protocol contract)
  - ParserResult.doc_format == "pdf" on parse failure (correct format attribution)

- Session 2 (post-sample-PDF acquisition from Chris):
  - Real D365 manual PDF parse → paragraphs/tables/images extraction
  - Heading hierarchy preservation (level 1-5)
  - level >= 6 anomaly demote-to-text rule
  - Multi-page document handling
  - Edge case: scanned PDF → minimal text extraction (orchestrator FailureRecord)
  - Edge case: encrypted PDF → parse_failed=True with actionable error

These tests use no fixtures (sample PDF not yet acquired); they verify the Parser
Protocol contract + factory dispatch + graceful failure on missing input. Real-PDF
tests are flagged with pytest.mark.skip + reason cross-referencing ADR-0019.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ingestion.parsers import select_parser
from ingestion.parsers.base import Parser, ParserResult
from ingestion.parsers.pdf_parser import DoclingPdfParser


def test_pdf_parser_doc_format_attribute() -> None:
    """DoclingPdfParser.doc_format must be 'pdf' (correct attribution per ADR-0019)."""
    parser = DoclingPdfParser()
    assert parser.doc_format == "pdf"


def test_pdf_parser_implements_parser_protocol() -> None:
    """DoclingPdfParser conforms to Parser Protocol (runtime_checkable per base.py:107)."""
    parser = DoclingPdfParser()
    assert isinstance(parser, Parser)


def test_pdf_parser_parse_nonexistent_file_returns_failed_result() -> None:
    """Parser Protocol contract: parse() MUST NOT raise; return ParserResult(parse_failed=True)."""
    parser = DoclingPdfParser()
    result = parser.parse(Path("/nonexistent/path/missing.pdf"))

    assert isinstance(result, ParserResult)
    assert result.parse_failed is True
    assert result.parse_error is not None
    assert result.doc_format == "pdf"  # correct format attribution even on failure
    assert result.doc_title == "missing"  # source.stem


def test_pdf_parser_failed_result_preserves_source_path() -> None:
    """ParserResult.source_path matches input even when parse fails (orchestrator FailureRecord wiring)."""
    source = Path("/nonexistent/path/some_doc.pdf")
    parser = DoclingPdfParser()
    result = parser.parse(source)

    assert result.source_path == source


def test_pdf_parser_failed_result_no_paragraphs_or_images() -> None:
    """Failed parse returns empty paragraphs/images/tables (chunker safe to handle)."""
    parser = DoclingPdfParser()
    result = parser.parse(Path("/nonexistent/path/missing.pdf"))

    assert result.paragraphs == []
    assert result.embedded_images == []
    assert result.tables == []


def test_pdf_parser_do_ocr_off_by_default() -> None:
    """BUG-044 — OCR OFF by default: born-digital Tier 1 PDF has a text layer, so Docling
    OCR is ~60s of waste for zero text gain (ADR-0019 text-extractable scope)."""
    parser = DoclingPdfParser()
    assert parser.do_ocr is False


def test_pdf_parser_do_ocr_opt_in() -> None:
    """BUG-044 — the scan path (force_scan=True) threads do_ocr=True to recover a real
    scan's text (ADR-0065); that is the only OCR caller."""
    parser = DoclingPdfParser(do_ocr=True)
    assert parser.do_ocr is True


def test_select_parser_threads_do_ocr_to_pdf() -> None:
    """BUG-044 — select_parser(do_ocr=...) reaches the .pdf parser; documents.py wires
    do_ocr=force_scan so a normal (born-digital) upload gets do_ocr=False."""
    off = select_parser(Path("brochure.pdf"))
    on = select_parser(Path("scan.pdf"), do_ocr=True)
    assert isinstance(off, DoclingPdfParser) and off.do_ocr is False
    assert isinstance(on, DoclingPdfParser) and on.do_ocr is True


# Session 2 deferred — real-PDF tests pending sample PDF acquisition from Chris (ADR-0019)


@pytest.mark.skip(reason="Sample PDF acquisition pending Chris (ADR-0019 W16 D1 active flip dependency)")
def test_pdf_parser_real_d365_manual_extracts_paragraphs() -> None:
    """Real D365 F&O ERP user manual PDF → ParserResult with non-empty paragraphs."""
    raise NotImplementedError("Sample PDF fixture pending — see ADR-0019 deliverables")


@pytest.mark.skip(reason="Sample PDF acquisition pending Chris (ADR-0019 W16 D1 active flip dependency)")
def test_pdf_parser_heading_hierarchy_preserved() -> None:
    """Multi-level headings (H1-H5) preserved in paragraphs[].heading_level."""
    raise NotImplementedError("Sample PDF fixture pending — see ADR-0019 deliverables")


@pytest.mark.skip(reason="Sample PDF acquisition pending Chris (ADR-0019 W16 D1 active flip dependency)")
def test_pdf_parser_level_6_anomaly_demoted_to_text() -> None:
    """level >= 6 heading anomaly demoted to plain text paragraph (consistency with docx_parser)."""
    raise NotImplementedError("Sample PDF fixture pending — see ADR-0019 deliverables")


@pytest.mark.skip(reason="Sample PDF acquisition pending Chris (ADR-0019 W16 D1 active flip dependency)")
def test_pdf_parser_table_extraction() -> None:
    """PDF embedded tables extracted via Docling DocItemLabel.TABLE."""
    raise NotImplementedError("Sample PDF fixture pending — see ADR-0019 deliverables")


@pytest.mark.skip(reason="Sample PDF acquisition pending Chris (ADR-0019 W16 D1 active flip dependency)")
def test_pdf_parser_image_extraction_with_sha256() -> None:
    """PDF embedded images extracted with PNG bytes + SHA256 hash for dedup."""
    raise NotImplementedError("Sample PDF fixture pending — see ADR-0019 deliverables")


@pytest.mark.skip(reason="Sample encrypted PDF fixture pending — Tier 2 OCR/decryption defer")
def test_pdf_parser_encrypted_pdf_returns_failed_result() -> None:
    """Tier 1 scope: encrypted PDF → ParserResult(parse_failed=True) with actionable error."""
    raise NotImplementedError("Encrypted PDF fixture pending — Tier 2 deferral per ADR-0019")


@pytest.mark.skip(reason="Sample scanned PDF fixture pending — Tier 2 OCR defer")
def test_pdf_parser_scanned_pdf_minimal_text_extraction() -> None:
    """Tier 1 scope: scanned PDF (no text layer) → minimal text; orchestrator records FailureRecord."""
    raise NotImplementedError("Scanned PDF fixture pending — Tier 2 deferral per ADR-0019")
