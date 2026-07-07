"""Parser Protocol + ParserResult dataclasses (per components/C01-ingestion.md §1, §2).

Parsers consume a file (.docx / .pdf / .pptx) and emit a ParserResult containing
heading-aware paragraphs, embedded image inventory, and table structure — all in
document order via the shared `doc_order` index. F2 chunker walks the interleaved
sequence to build layout-aware chunks with correct section_path context for tables
and images alike.

Design notes:
- Sync parse() — parsers are CPU/IO-bound (zipfile + XML); the orchestrator runs
  it via asyncio.to_thread (BUG-040) so a large file never blocks the event loop.
- @dataclass (not Pydantic) — internal pipeline types, no API boundary validation needed.
- Heading.level uses 1-indexed (H1=1, H2=2, ...) matching Word/Markdown convention.
- doc_order is a monotonic index across all item types (paragraphs / tables / images)
  shared from `doc.iterate_items()` traversal — F2 chunker uses it to interleave.
- raw_text / heading_tree / paragraphs_total are @property derivations from
  paragraphs (single source of truth).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Protocol, runtime_checkable

DocFormat = Literal["docx", "pdf", "pptx"]
ParagraphKind = Literal["heading", "text", "list_item"]


@dataclass(slots=True)
class ParagraphItem:
    """A single paragraph-level item from the parsed document, in document order."""

    text: str
    kind: ParagraphKind
    doc_order: int
    heading_level: int | None = None  # set only when kind == "heading"


@dataclass(slots=True)
class Heading:
    """Derived view of paragraph headings — used by external consumers that only
    need the heading-tree summary without scanning paragraphs."""

    level: int
    text: str
    anchor: str  # "t{doc_order}"
    detected_via: Literal["style", "font_size_heuristic"] = "style"


@dataclass(slots=True)
class EmbeddedImage:
    """Embedded image (raw bytes + position metadata for chunk-image association)."""

    image_bytes: bytes
    alt_text: str
    doc_order: int  # position in document (shared with paragraphs)
    ext: str       # "png" / "jpg" / "wmf" / "emf" / "svg" — pre-conversion
    sha256: str    # for SHA256 dedup at F3 screenshot uploader


@dataclass(slots=True)
class Table:
    """Table structure (rows + optional headers, doc_order for chunker placement)."""

    rows: list[list[str]]
    headers: list[str] | None
    doc_order: int


@dataclass(slots=True)
class ParserResult:
    """Output of any format-specific parser (per C01-ingestion §1 §2 contract).

    Contract for downstream F2 chunker:
    - paragraphs: ordered list (document order via doc_order index)
    - embedded_images / tables: each item has doc_order to interleave with paragraphs
    - parse_failed=True signals C02 KB Manager to record a FailureRecord
    """

    source_path: Path
    doc_format: DocFormat
    doc_title: str
    paragraphs: list[ParagraphItem] = field(default_factory=list)
    embedded_images: list[EmbeddedImage] = field(default_factory=list)
    tables: list[Table] = field(default_factory=list)
    parse_failed: bool = False
    parse_error: str | None = None

    @property
    def raw_text(self) -> str:
        return "\n\n".join(p.text for p in self.paragraphs if p.text)

    @property
    def heading_tree(self) -> list[Heading]:
        return [
            Heading(level=p.heading_level or 1, text=p.text, anchor=f"t{p.doc_order}")
            for p in self.paragraphs
            if p.kind == "heading" and p.heading_level is not None
        ]

    @property
    def paragraphs_total(self) -> int:
        return len(self.paragraphs)


@runtime_checkable
class Parser(Protocol):
    """Format-specific parser contract (.docx / .pdf / .pptx implementations).

    Implementations MUST be deterministic for a given input file (no external
    network calls during parse — parsing is offline structural extraction).
    """

    doc_format: DocFormat

    def parse(self, source: Path) -> ParserResult:
        """Parse a single file. MUST NOT raise on malformed input — return
        ParserResult(parse_failed=True, parse_error=...) instead, so the
        orchestrator can record a FailureRecord without aborting the batch.
        """
        ...
