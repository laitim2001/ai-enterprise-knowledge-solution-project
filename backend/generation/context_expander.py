"""Context Expander step per architecture.md §3.1 + ADR-0020 W16+ Phase 3.

Per architecture.md §3.1 RAG pipeline:
    [Cohere Rerank → top 5]
        ↓
    [Context Expander] ← prev/next 相鄰 chunk        ← THIS MODULE
        ↓
    [CRAG Confidence Judge]

W15 D5 audit (audit-W15-d5-vs-spec.md §1.5 C05 Major drift #3 + §CC-3) found
prev_chunk_id + next_chunk_id populated in ChunkRecord (orchestrator + index)
but no retrieval/generation code consumed them. ADR-0020 Phase 3 P0.3 batch
decision: deliver code (Option A) reaffirming spec §3.1 + §5.7 9-stage rather
than amend spec.

Algorithm (single batch fetch — minimizes latency overhead):
1. Collect all prev_chunk_id + next_chunk_id from top-K reranked chunks
2. Filter out None / empty / cross-doc boundary (prev/next chunk in different doc)
3. Single Azure Search call via HybridSearcher.fetch_by_chunk_ids() — search.in() filter
4. Build chunk_id → chunk_text lookup dict
5. For each top-K chunk: prepend prev_text + append next_text → expanded_text
6. Return list[ExpandedChunk] — duck-typed compatible with RetrievedChunk for synthesizer

Edge cases (all return ExpandedChunk with expansion_applied=False, falling back to
original chunk_text in prompt_builder via expanded_text-or-chunk_text dispatch):
- First chunk in document (prev_chunk_id is None / empty)
- Last chunk in document (next_chunk_id is None / empty)
- Cross-doc boundary (prev/next chunk_id has different doc_id prefix)
- Lookup miss (chunk_id not in index — orphaned reference)
- Network error during batch fetch (graceful degradation — log + skip)

Citation invariant preserved: build_citations() still uses chunk_id (unchanged) +
original chunk_text from RetrievedChunk for Citation.chunk_text rendering. LLM
sees expanded context but cited chunks display original content (per architecture.md
§3.5 Citation contract — Citation.chunk_text = original_chunk.chunk_text).
"""

from __future__ import annotations

import time
from dataclasses import dataclass

import structlog

from observability.observe import emit_stage_metadata
from retrieval.hybrid import HybridSearcher
from retrieval.retrieval_engine import RetrievedChunk

logger = structlog.get_logger(__name__)

# Langfuse stage name for the Context Expander step — must match the frontend
# observation-name → conceptual-stage mapping in
# `frontend/app/debug/[traceId]/page.tsx` (ADR-0020 §5.7 V6 9-stage Debug View).
_STAGE_NAME = "generation.context_expansion"


@dataclass(slots=True, frozen=True)
class ExpandedChunk:
    """Reranked chunk with prev/next neighbor expansion for LLM context.

    Duck-typed compatible with RetrievedChunk for prompt_builder consumption — same
    score + fields shape; fields dict gains 'expanded_text' key when expansion_applied
    is True, otherwise prompt_builder falls back to fields['chunk_text'].

    Fields:
    - score: from reranker (unchanged from RetrievedChunk)
    - fields: copy of RetrievedChunk.fields with NEW 'expanded_text' key when expanded
    - prev_chunk_text: prev neighbor text (None if first/cross-doc/missing)
    - next_chunk_text: next neighbor text (None if last/cross-doc/missing)
    - expansion_applied: True if prev or next was merged
    """

    score: float
    fields: dict
    prev_chunk_text: str | None
    next_chunk_text: str | None
    expansion_applied: bool

    @classmethod
    def no_expansion(cls, chunk: RetrievedChunk) -> ExpandedChunk:
        """Wrap RetrievedChunk without expansion (feature-flag-disabled / empty top-K)."""
        return cls(
            score=chunk.score,
            fields=chunk.fields,
            prev_chunk_text=None,
            next_chunk_text=None,
            expansion_applied=False,
        )


@dataclass(slots=True, frozen=True)
class ExpansionStats:
    """Aggregate stats for observability + V6 Debug View display per ADR-0020."""

    requested_count: int      # how many top-K chunks went in
    expanded_count: int       # how many had prev or next merged
    boundary_skip_count: int  # how many were first/last/cross-doc (no neighbor available)
    fetch_latency_ms: int     # batch Azure Search fetch latency


def _emit_expansion_stage(stats: ExpansionStats) -> None:
    """Surface ExpansionStats to Langfuse / V6 Debug View per ADR-0020 §C.

    Latency keyed as `duration_ms` (= batch fetch latency) so
    `langfuse_trace._extract_stage` maps it to `TraceStage.latency_ms`
    uniformly with `observe_async`-emitted stages; the remaining counts land
    in `TraceStage.details`.
    """
    emit_stage_metadata(
        _STAGE_NAME,
        duration_ms=stats.fetch_latency_ms,
        requested_count=stats.requested_count,
        expanded_count=stats.expanded_count,
        boundary_skip_count=stats.boundary_skip_count,
    )


def _doc_id_of(chunk_id: str) -> str:
    """Extract doc_id substring from chunk_id format kb-{kb_id}_doc-{doc_id}_chunk-{idx}.

    Per architecture.md §3.5 chunk_id naming convention. Used for cross-doc boundary check
    so prev/next from different doc are rejected (semantic adjacency assumption violated).
    """
    if not chunk_id:
        return ""
    # Find doc-{...}_chunk- segment; conservative parsing: anything after last "_doc-" up to
    # next "_chunk-" is doc_id. Falls back to chunk_id itself if format unexpected.
    doc_marker = "_doc-"
    chunk_marker = "_chunk-"
    di = chunk_id.find(doc_marker)
    ci = chunk_id.find(chunk_marker)
    if di == -1 or ci == -1 or ci <= di:
        return chunk_id
    return chunk_id[di + len(doc_marker):ci]


def _is_cross_doc_neighbor(neighbor_chunk_id: str, parent_chunk_id: str) -> bool:
    """Return True if neighbor chunk_id belongs to a different doc than parent."""
    if not neighbor_chunk_id or not parent_chunk_id:
        return False  # no neighbor or parent → handled separately
    return _doc_id_of(neighbor_chunk_id) != _doc_id_of(parent_chunk_id)


def _chunk_text_of(fields: dict, *, use_marked: bool) -> str:
    """W70 / ADR-0055 — pick the marked variant when the knob is on; "" (chunk has
    no markers OR pre-W70 index) falls back to the clean text. use_marked=False is
    the pre-W70 read, bit-identical."""
    text = str(fields.get("chunk_text", ""))
    if use_marked:
        return str(fields.get("chunk_text_marked") or "") or text
    return text


async def expand_context(
    reranked_chunks: list[RetrievedChunk],
    kb_id: str,
    searcher: HybridSearcher,
    *,
    use_marked: bool = False,
) -> tuple[list[ExpandedChunk], ExpansionStats]:
    """Expand top-K reranked chunks with prev/next neighbor text per architecture.md §3.1.

    kb_id required per ADR-0018 multi-KB invariant (searcher.fetch_by_chunk_ids needs it).

    use_marked (W70 / ADR-0055): True assembles `expanded_text` from the marked
    text variants (anchor + neighbours) so inline image markers survive the
    expansion path. `fields['chunk_text']` is never touched (citation invariant).

    Returns (expanded_chunks, stats). Stats useful for V6 Debug View + Langfuse trace
    per ADR-0020 observability requirements.
    """
    if not reranked_chunks:
        empty_stats = ExpansionStats(
            requested_count=0,
            expanded_count=0,
            boundary_skip_count=0,
            fetch_latency_ms=0,
        )
        _emit_expansion_stage(empty_stats)
        return [], empty_stats

    # Step 1: collect all neighbor chunk_ids needed (skip None / cross-doc / empty)
    neighbor_ids_needed: set[str] = set()
    for chunk in reranked_chunks:
        chunk_id = str(chunk.fields.get("chunk_id", ""))
        prev_id = str(chunk.fields.get("prev_chunk_id") or "")
        next_id = str(chunk.fields.get("next_chunk_id") or "")
        if prev_id and not _is_cross_doc_neighbor(prev_id, chunk_id):
            neighbor_ids_needed.add(prev_id)
        if next_id and not _is_cross_doc_neighbor(next_id, chunk_id):
            neighbor_ids_needed.add(next_id)

    # Step 2: batch fetch all needed neighbors in single Azure Search call
    fetch_start = time.perf_counter()
    if neighbor_ids_needed:
        try:
            neighbors_lookup = await searcher.fetch_by_chunk_ids(
                list(neighbor_ids_needed),
                kb_id=kb_id,
            )
        except Exception as exc:  # noqa: BLE001 — graceful degradation per ADR-0020 spec
            logger.warning(
                "context_expansion_fetch_failed",
                error=f"{type(exc).__name__}: {exc}",
                kb_id=kb_id,
                requested=len(neighbor_ids_needed),
            )
            neighbors_lookup = {}
    else:
        neighbors_lookup = {}
    fetch_latency_ms = int((time.perf_counter() - fetch_start) * 1000)

    # Step 3: build ExpandedChunk per top-K chunk
    expanded: list[ExpandedChunk] = []
    expanded_count = 0
    boundary_skip_count = 0

    for chunk in reranked_chunks:
        chunk_id = str(chunk.fields.get("chunk_id", ""))
        prev_id = str(chunk.fields.get("prev_chunk_id") or "")
        next_id = str(chunk.fields.get("next_chunk_id") or "")
        original_text = _chunk_text_of(chunk.fields, use_marked=use_marked)

        # Resolve prev neighbor (None if missing, cross-doc, or lookup miss)
        prev_text: str | None = None
        if prev_id and not _is_cross_doc_neighbor(prev_id, chunk_id):
            prev_fields = neighbors_lookup.get(prev_id)
            if prev_fields:
                prev_text = _chunk_text_of(prev_fields, use_marked=use_marked) or None
        else:
            boundary_skip_count += 1 if not prev_id else 0  # first chunk of doc

        # Resolve next neighbor (None if missing, cross-doc, or lookup miss)
        next_text: str | None = None
        if next_id and not _is_cross_doc_neighbor(next_id, chunk_id):
            next_fields = neighbors_lookup.get(next_id)
            if next_fields:
                next_text = _chunk_text_of(next_fields, use_marked=use_marked) or None
        else:
            boundary_skip_count += 1 if not next_id else 0  # last chunk of doc

        # Compose expanded_text — order: prev → original → next
        expansion_applied = bool(prev_text or next_text)
        if expansion_applied:
            expanded_count += 1
            parts: list[str] = []
            if prev_text:
                parts.append(prev_text)
            parts.append(original_text)
            if next_text:
                parts.append(next_text)
            expanded_text = "\n\n".join(parts)
            new_fields = {**chunk.fields, "expanded_text": expanded_text}
        else:
            new_fields = chunk.fields  # no expanded_text key — prompt_builder falls back

        expanded.append(
            ExpandedChunk(
                score=chunk.score,
                fields=new_fields,
                prev_chunk_text=prev_text,
                next_chunk_text=next_text,
                expansion_applied=expansion_applied,
            ),
        )

    stats = ExpansionStats(
        requested_count=len(reranked_chunks),
        expanded_count=expanded_count,
        boundary_skip_count=boundary_skip_count,
        fetch_latency_ms=fetch_latency_ms,
    )

    logger.info(
        "context_expansion_complete",
        kb_id=kb_id,
        requested_count=stats.requested_count,
        expanded_count=stats.expanded_count,
        boundary_skip_count=stats.boundary_skip_count,
        fetch_latency_ms=stats.fetch_latency_ms,
        neighbors_fetched=len(neighbors_lookup),
        neighbors_requested=len(neighbor_ids_needed),
    )
    _emit_expansion_stage(stats)

    return expanded, stats
