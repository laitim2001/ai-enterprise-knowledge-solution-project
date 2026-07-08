"""Parser package: format-specific parsers emitting ParserResult.

- base.py: Parser Protocol + ParserResult / Heading / EmbeddedImage / Table dataclasses
- docx_parser.py: Docling-based .docx parser (W2 D1 F1)
- pdf_parser.py:  Docling-based .pdf parser (W2 D5 deferred → W16+ Phase 3 ADR-0019)
- pptx_parser.py: python-pptx parser (W3 D1)

W4 D1 F9: `select_parser()` factory dispatches by file extension so the
ingestion orchestrator can be wired generically (caller passes file Path
without pre-deciding parser).
"""

from __future__ import annotations

from pathlib import Path

from .base import Parser
from .docx_parser import DoclingDocxParser
from .pdf_parser import DoclingPdfParser
from .pptx_parser import PptxParser


def select_parser(source: Path, *, extract_images: bool = False, do_ocr: bool = False) -> Parser:
    """Dispatch to the parser implementation by file extension.

    Recognized formats: .docx → DoclingDocxParser, .pdf → DoclingPdfParser,
    .pptx → PptxParser (per architecture.md §3.3 + components/C01 §1 + ADR-0019).

    `extract_images` (ADR-0057): when True the .pdf parser extracts embedded
    pictures (generate_picture_images=True). Threaded from the KB's
    `extract_embedded_images` toggle by the ingest caller; default False keeps every
    existing caller + the .docx / .pptx paths bit-identical.

    `do_ocr` (BUG-044): when True the .pdf parser runs Docling OCR. Default False —
    Tier 1 born-digital PDFs have a text layer, so OCR is ~60s of waste. The ingest
    caller threads do_ocr=force_scan so only a user-confirmed scan (ADR-0065) pays it.
    No effect on .docx / .pptx (no OCR path).
    """
    suffix = source.suffix.lower()
    if suffix == ".docx":
        return DoclingDocxParser()
    if suffix == ".pdf":
        return DoclingPdfParser(generate_picture_images=extract_images, do_ocr=do_ocr)
    if suffix == ".pptx":
        return PptxParser()
    raise ValueError(
        f"unsupported file extension {suffix!r} (source={source.name}); "
        "supported: .docx / .pdf / .pptx per architecture.md §3.3",
    )
