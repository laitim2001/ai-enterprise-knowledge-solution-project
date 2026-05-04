"""Parser package: format-specific parsers emitting ParserResult.

- base.py: Parser Protocol + ParserResult / Heading / EmbeddedImage / Table dataclasses
- docx_parser.py: Docling-based .docx parser (W2 D1 F1)
- pdf_parser.py:  Docling-based .pdf parser (W2 D5)
- pptx_parser.py: python-pptx parser (W3 D1)

W4 D1 F9: `select_parser()` factory dispatches by file extension so the
ingestion orchestrator can be wired generically (caller passes file Path
without pre-deciding parser).
"""

from __future__ import annotations

from pathlib import Path

from .base import Parser
from .docx_parser import DoclingDocxParser
from .pptx_parser import PptxParser


def select_parser(source: Path) -> Parser:
    """Dispatch to the parser implementation by file extension.

    Recognized formats: .docx → DoclingDocxParser, .pptx → PptxParser.
    .pdf is W2 D5 scope — currently routes to DoclingDocxParser since Docling
    handles both .docx and .pdf via the same converter (per architecture.md
    §3.3 + components/C01 §1).
    """
    suffix = source.suffix.lower()
    if suffix == ".docx":
        return DoclingDocxParser()
    if suffix == ".pdf":
        # Docling handles .pdf via the same DocumentConverter; reuse the
        # docx-named class since W2 D5 did not split it. Rename deferred per
        # CLAUDE.md §1.3 surgical (no rename without trigger).
        return DoclingDocxParser()
    if suffix == ".pptx":
        return PptxParser()
    raise ValueError(
        f"unsupported file extension {suffix!r} (source={source.name}); "
        "supported: .docx / .pdf / .pptx per architecture.md §3.3",
    )
