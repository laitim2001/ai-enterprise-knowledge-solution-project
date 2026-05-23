"""Layout-aware chunker (per architecture.md §3.3 + components/C01-ingestion.md §1).

Algorithm:
1. Walk ParserResult.paragraphs in doc_order; maintain a heading-level stack to
   compute section_path (e.g., ["1 Scope", "1.2 Process List"]).
2. Within each section, accumulate paragraph text; when accumulated text exceeds
   target_tokens (500), flush as a chunk; respect hard cap (1500) — split at
   paragraph boundaries; never split mid-paragraph for W2 baseline (per spec).
3. Tables: emit each table as 1 chunk (architecture.md §3.3 "table 獨立 chunk"),
   inheriting section_path from the most recent heading at the table's doc_order.
4. Embedded image positions: associate by doc_order — each image attached to the
   chunk whose section spans its doc_order.
5. low_value_flag heuristic (per architecture.md §3.3 + checklist F2):
   - chunk_token_count < 60 (soft floor lowered W25 D3 per ADR-0033;
     was 100, see ADR §Decision (a) for the 60% low_value ratio empirical
     signal that triggered the change) OR
   - chunk title or text matches TOC pattern OR version statement.
6. Adjacent-short-merge post-process (W25 D3 per ADR-0033 §Decision (b)):
   - After main event loop emits raw chunks, walk pairs (prev, curr) and
     consolidate consecutive text chunks where both fall below
     _MIN_CHUNK_MERGE_FLOOR (160). Tables stay independent.
   - Merge respects hard_cap_tokens (skip merge if combined would exceed).
   - Re-indexes chunks 0..N-1 contiguous after merge pass.

Carry-over from W2 D1: 6 sample chunk count expected to land below plan §2 F2
estimate "2000-3000 chunks total" — that estimate assumed per-row table chunks,
but architecture spec mandates 1-chunk-per-table. Revised expectation per W2 D2
sanity report; non plan deviation since architecture spec is authoritative.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, replace

import tiktoken

from ingestion.chunker.base import ChunkSpec
from ingestion.parsers.base import ParagraphItem, ParserResult, Table

_TOKEN_TARGET = 500
_TOKEN_HARD_CAP = 1500
_TOKEN_LOW_VALUE_FLOOR = 60  # lowered 100→60 W25 D3 per ADR-0033 (amends §3.3)
_MIN_CHUNK_MERGE_FLOOR = 160  # adjacent-short-merge threshold per ADR-0033 (b)

_TOC_PATTERNS = (
    re.compile(r"^\s*table of contents\s*$", re.IGNORECASE),
    re.compile(r"^\s*目錄\s*$"),
    re.compile(r"^\s*目次\s*$"),
)
_VERSION_PATTERNS = (
    re.compile(r"^\s*ver(?:sion)?[\s.:]*\d", re.IGNORECASE),
    re.compile(r"^\s*revision history\s*$", re.IGNORECASE),
    re.compile(r"^\s*版本[\s.:]"),
)


@dataclass(slots=True)
class _SectionAccumulator:
    """Internal accumulator for an open text section."""

    section_path: list[str]
    chunk_title: str
    heading_anchor: str | None
    paragraphs: list[str]
    token_count: int
    image_positions: list[str]
    start_doc_order: int  # doc_order where this section opened (after the heading)


class LayoutAwareChunker:
    """Heading-aware section chunker for .docx (and W2 D5+ .pdf via Docling parser)."""

    def __init__(
        self,
        target_tokens: int = _TOKEN_TARGET,
        hard_cap_tokens: int = _TOKEN_HARD_CAP,
        low_value_floor: int = _TOKEN_LOW_VALUE_FLOOR,
        min_chunk_merge_floor: int = _MIN_CHUNK_MERGE_FLOOR,
    ) -> None:
        self.target_tokens = target_tokens
        self.hard_cap_tokens = hard_cap_tokens
        self.low_value_floor = low_value_floor
        self.min_chunk_merge_floor = min_chunk_merge_floor
        self._enc = tiktoken.get_encoding("cl100k_base")

    def chunk(self, parser_result: ParserResult) -> list[ChunkSpec]:
        if parser_result.parse_failed:
            return []

        chunks: list[ChunkSpec] = []
        chunk_index_counter = 0

        # Build merged document-order event list:
        # paragraphs (text/heading/list_item), images (image_pos), tables.
        events = self._merge_events(parser_result)

        # Active section stack: list[(level, heading_text, anchor)]
        section_stack: list[tuple[int, str, str]] = []
        accumulator: _SectionAccumulator | None = None

        for ev_kind, ev in events:
            if ev_kind == "paragraph":
                p: ParagraphItem = ev
                if p.kind == "heading":
                    # Flush current accumulator before opening new section
                    if accumulator is not None:
                        chunks.extend(self._flush_text_section(accumulator, chunk_index_counter))
                        chunk_index_counter = len(chunks)
                        accumulator = None

                    # Update heading stack: pop deeper-or-equal levels, push this
                    while section_stack and section_stack[-1][0] >= (p.heading_level or 1):
                        section_stack.pop()
                    section_stack.append(((p.heading_level or 1), p.text, f"t{p.doc_order}"))

                    accumulator = _SectionAccumulator(
                        section_path=[h[1] for h in section_stack],
                        chunk_title=p.text,
                        heading_anchor=f"t{p.doc_order}",
                        paragraphs=[],
                        token_count=0,
                        image_positions=[],
                        start_doc_order=p.doc_order,
                    )
                else:
                    # Body text under current section (or pre-heading orphan)
                    if accumulator is None:
                        # Pre-first-heading orphan: aggregate under synthetic root
                        accumulator = _SectionAccumulator(
                            section_path=[parser_result.doc_title],
                            chunk_title=parser_result.doc_title,
                            heading_anchor=None,
                            paragraphs=[],
                            token_count=0,
                            image_positions=[],
                            start_doc_order=p.doc_order,
                        )
                    self._add_paragraph(accumulator, p.text, chunks, chunk_index_counter)
                    # Refresh chunk_index_counter in case _add_paragraph flushed
                    chunk_index_counter = len(chunks)

            elif ev_kind == "image":
                img_pos = ev  # doc_order int
                if accumulator is not None:
                    accumulator.image_positions.append(f"img@{img_pos}")
                # else: image before any text/heading — orphan, dropped for W2 baseline

            elif ev_kind == "table":
                tbl: Table = ev
                # Tables become their own chunks; attach current section_path
                section_path = (
                    [h[1] for h in section_stack] if section_stack else [parser_result.doc_title]
                )
                table_chunk = self._build_table_chunk(
                    tbl,
                    section_path=section_path,
                    chunk_index=len(chunks),
                )
                chunks.append(table_chunk)

        # Flush any trailing section
        if accumulator is not None:
            chunks.extend(self._flush_text_section(accumulator, len(chunks)))

        # ADR-0033 (b): consolidate adjacent short text chunks before returning.
        return self._merge_adjacent_shorts(chunks)

    def _merge_events(
        self,
        parser_result: ParserResult,
    ) -> list[tuple[str, object]]:
        """Merge paragraphs / images / tables into a single doc_order-sorted event stream."""
        events: list[tuple[int, str, object]] = []
        for p in parser_result.paragraphs:
            events.append((p.doc_order, "paragraph", p))
        for img in parser_result.embedded_images:
            events.append((img.doc_order, "image", img.doc_order))
        for tbl in parser_result.tables:
            events.append((tbl.doc_order, "table", tbl))
        events.sort(key=lambda e: e[0])
        return [(kind, payload) for _, kind, payload in events]

    def _add_paragraph(
        self,
        acc: _SectionAccumulator,
        text: str,
        chunks: list[ChunkSpec],
        base_index: int,
    ) -> None:
        """Add a paragraph to accumulator; flush as chunk if hard cap reached."""
        para_tokens = len(self._enc.encode(text))

        # If single paragraph exceeds hard cap, emit it standalone (rare, but safe)
        if para_tokens >= self.hard_cap_tokens and not acc.paragraphs:
            chunks.append(self._build_text_chunk(acc, [text], para_tokens, len(chunks)))
            return

        prospective = acc.token_count + para_tokens
        if prospective > self.hard_cap_tokens and acc.paragraphs:
            # Flush before adding (hard cap)
            chunks.append(self._build_text_chunk(
                acc, acc.paragraphs, acc.token_count, len(chunks)),
            )
            acc.paragraphs = []
            acc.token_count = 0
            # Keep image_positions on the open section — they belong to whole section

        acc.paragraphs.append(text)
        acc.token_count += para_tokens

        # Soft target: flush early if past target on a clean paragraph boundary
        if acc.token_count >= self.target_tokens:
            chunks.append(self._build_text_chunk(
                acc, acc.paragraphs, acc.token_count, len(chunks)),
            )
            acc.paragraphs = []
            acc.token_count = 0

    def _flush_text_section(
        self,
        acc: _SectionAccumulator,
        base_index: int,
    ) -> list[ChunkSpec]:
        """Emit any remaining buffered paragraphs as a final chunk for the section."""
        if not acc.paragraphs:
            return []
        return [self._build_text_chunk(acc, acc.paragraphs, acc.token_count, base_index)]

    def _build_text_chunk(
        self,
        acc: _SectionAccumulator,
        paragraphs: list[str],
        token_count: int,
        chunk_index: int,
    ) -> ChunkSpec:
        chunk_content = "\n\n".join(paragraphs)
        chunk_text = f"{acc.chunk_title}\n\n{chunk_content}" if acc.chunk_title else chunk_content
        full_token_count = len(self._enc.encode(chunk_text))
        return ChunkSpec(
            section_path=list(acc.section_path),
            chunk_title=acc.chunk_title,
            chunk_text=chunk_text,
            chunk_token_count=full_token_count,
            chunk_kind="text",
            chunk_index=chunk_index,
            low_value_flag=self._is_low_value(acc.chunk_title, chunk_content, full_token_count),
            embedded_image_positions=list(acc.image_positions),
            heading_anchor=acc.heading_anchor,
        )

    def _build_table_chunk(
        self,
        table: Table,
        section_path: list[str],
        chunk_index: int,
    ) -> ChunkSpec:
        # Render table as pipe-delimited rows for text retrieval (BM25 + embedding compatible)
        lines: list[str] = []
        if table.headers:
            lines.append(" | ".join(str(h) for h in table.headers))
            lines.append("-" * 4)
        for row in table.rows:
            lines.append(" | ".join(str(c) for c in row))
        table_body = "\n".join(lines)

        chunk_title = section_path[-1] if section_path else "Table"
        chunk_text = f"{chunk_title}\n\n{table_body}"
        token_count = len(self._enc.encode(chunk_text))

        return ChunkSpec(
            section_path=list(section_path),
            chunk_title=chunk_title,
            chunk_text=chunk_text,
            chunk_token_count=token_count,
            chunk_kind="table",
            chunk_index=chunk_index,
            low_value_flag=self._is_low_value(chunk_title, table_body, token_count),
            embedded_image_positions=[],
            heading_anchor=None,
        )

    def _is_low_value(self, title: str, body: str, token_count: int) -> bool:
        if token_count < self.low_value_floor:
            return True
        for pat in _TOC_PATTERNS:
            if pat.match(title) or pat.match(body):
                return True
        for pat in _VERSION_PATTERNS:
            if pat.match(title):
                return True
        return False

    def _merge_adjacent_shorts(self, chunks: list[ChunkSpec]) -> list[ChunkSpec]:
        """Per ADR-0033 (b) — consolidate consecutive text chunks where both
        fall below min_chunk_merge_floor. Tables stay independent. Merges
        backward into prev (inherits prev's section_path / chunk_title /
        heading_anchor). Respects hard_cap_tokens. Re-indexes 0..N-1.
        """
        if not chunks:
            return chunks

        merged: list[ChunkSpec] = []
        for chunk in chunks:
            if not merged:
                merged.append(chunk)
                continue

            prev = merged[-1]
            if not self._should_merge(prev, chunk):
                merged.append(chunk)
                continue

            combined_text = f"{prev.chunk_text}\n\n{chunk.chunk_text}"
            combined_token_count = len(self._enc.encode(combined_text))

            # Safety: never break hard cap (re-checked post-encode because
            # token counts are not strictly additive).
            if combined_token_count > self.hard_cap_tokens:
                merged.append(chunk)
                continue

            combined_images = list(prev.embedded_image_positions) + list(
                chunk.embedded_image_positions,
            )
            merged[-1] = ChunkSpec(
                section_path=list(prev.section_path),
                chunk_title=prev.chunk_title,
                chunk_text=combined_text,
                chunk_token_count=combined_token_count,
                chunk_kind="text",
                chunk_index=prev.chunk_index,  # re-indexed below
                low_value_flag=self._is_low_value(
                    prev.chunk_title, combined_text, combined_token_count,
                ),
                embedded_image_positions=combined_images,
                heading_anchor=prev.heading_anchor,
            )

        # Re-index 0..N-1 contiguous after any merges.
        return [replace(c, chunk_index=i) for i, c in enumerate(merged)]

    def _should_merge(self, prev: ChunkSpec, curr: ChunkSpec) -> bool:
        """Both text-kind + both below merge floor. Hard-cap check happens
        post-encode in _merge_adjacent_shorts (token counts are not strictly
        additive after rejoining)."""
        if prev.chunk_kind != "text" or curr.chunk_kind != "text":
            return False
        if prev.chunk_token_count >= self.min_chunk_merge_floor:
            return False
        if curr.chunk_token_count >= self.min_chunk_merge_floor:
            return False
        return True
