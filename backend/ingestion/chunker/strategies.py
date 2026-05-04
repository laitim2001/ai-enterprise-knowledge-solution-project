"""Chunk strategy selector (per architecture.md §4.5 KbConfig.chunk_strategy + components/C01-ingestion.md §1).

Strategy mapping:
- layout_aware — W2 baseline (.docx / .pdf via Docling) using LayoutAwareChunker
- slide_based — W4 D1 F9 (.pptx via python-pptx) — also LayoutAwareChunker since
  PptxParser emits the same heading-paragraph-table-image structure as Docling
  (per slide: synthetic level=1 "Slide N" heading + level=2 title + body
  paragraphs + tables + pictures). LayoutAwareChunker walks heading levels
  generically so a dedicated SlideBasedChunker class would be redundant —
  per Karpathy §1.2 simplicity-first.
- heading_aware — W3+ standalone strategy deferred (layout_aware already
  provides heading-bounded sections; standalone variant only needed if a
  dedicated heading-merge / cross-heading strategy emerges)

`auto` routing per doc_format (per architecture.md §3.3 Multi-Format Strategy):
- docx → layout_aware
- pdf  → layout_aware
- pptx → slide_based (currently same chunker; left distinct in `KbConfig` to
  preserve forward extensibility if PPT-specific chunking emerges)
"""

from __future__ import annotations

from typing import Literal

from ingestion.chunker.base import Chunker
from ingestion.chunker.layout_aware import LayoutAwareChunker
from ingestion.parsers.base import DocFormat

ChunkStrategy = Literal["heading_aware", "layout_aware", "slide_based", "auto"]


def select_chunker(doc_format: DocFormat, strategy: ChunkStrategy = "auto") -> Chunker:
    """Return a Chunker for the given doc_format + KbConfig strategy."""
    resolved = _resolve_auto(doc_format, strategy)

    if resolved in ("layout_aware", "slide_based"):
        # Both delegate to LayoutAwareChunker — see module docstring.
        return LayoutAwareChunker()
    if resolved == "heading_aware":
        raise NotImplementedError(
            "heading_aware as a standalone strategy is W3+ scope; "
            "layout_aware already provides heading-bounded sections for W2 baseline",
        )
    raise ValueError(f"unknown chunk strategy: {strategy!r} (resolved={resolved!r})")


def _resolve_auto(doc_format: DocFormat, strategy: ChunkStrategy) -> ChunkStrategy:
    if strategy != "auto":
        return strategy
    if doc_format in ("docx", "pdf"):
        return "layout_aware"
    if doc_format == "pptx":
        return "slide_based"
    raise ValueError(f"cannot auto-resolve strategy for doc_format={doc_format!r}")
