"""Parent-Document / Section-Level Retrieval step per architecture.md §3.1 + ADR-0037 W26 F2.

Per architecture.md §3.1 RAG pipeline (post-Context Expander insertion locus):

    [Cohere Rerank → top 5]
        ↓
    [Context Expander]               ← ADR-0020 (prev/next ±1 chunk, unchanged)
        ↓
    [Parent-Document Retriever]      ← THIS MODULE (ADR-0037 NEW per W26 F2)
        ↓
    [CRAG Confidence Judge]
        ↓
    [GPT-5.5 Synthesis with Citation]

Trigger memo: `docs/09-analysis/rag_retrieval_quality_investigation_20260525.md`
+ W26 F1 empirical refutation 2026-05-25 D1 (Cohere v4.0-pro scores
P25=0.83 / min=0.67 cannot differentiate failed vs passed enumeration
queries — threshold cutoff approach refuted). Brief §6 step 4 escalation
activated via Chris AskUserQuestion pivot pick (C) 2026-05-25 D1.

Algorithm (single batched fetch per unique parent — minimizes latency):

1. Anchor selection — take top `parent_doc_top_k` chunks (default 1) as anchors
2. Compute parent section paths per anchor:
   - Default: `parent_path = anchor.section_path[:-section_depth_offset]`
   - Shallow chunks (section_path too shallow for offset): fallback to
     longest available prefix if `fallback_to_doc_on_shallow=True`, else skip
3. Deduplicate (doc_id, parent_path) tuples — multiple anchors may share parent
4. Batch fetch each unique parent via `HybridSearcher.fetch_chunks_by_section_path`
   (single Azure Search call per parent; @retry decorator on the searcher
   handles transient errors transparently)
5. For each anchor: assemble `parent_section_text` by concatenating sibling
   chunk_text in `chunk_index` ASC order (already sorted by the searcher's
   `orderby chunk_index asc` payload), tail-drop truncating at
   `max_tokens_per_parent` token budget
6. Pass through any non-anchor reranked chunks unchanged — their prev/next
   expansion via ADR-0020 stays intact (Q6 Both on coexistence policy)

Citation invariant preserved (per ADR-0020 + architecture.md §3.5):
`Citation.chunk_text = original_chunk.chunk_text` — LLM sees parent section
context, but citations reference original anchor chunks. `prompt_builder`
dispatch chain `parent_section_text > expanded_text > chunk_text` consumes
the new key; emitted citations still reference anchor `chunk_id`.

Edge cases (all fall back gracefully to anchor without parent expansion):
- Empty input (`reranked_chunks=[]`) — empty result + zero stats
- Anchor missing `section_path` or `doc_id` — pass through unchanged
- Shallow `section_path` (`len ≤ section_depth_offset`) — fallback or skip
- Empty parent_path computed — skip (cost guard upstream)
- Lookup miss (parent section returns 0 chunks) — pass anchor unchanged
- Network error during batch fetch — log + return anchors unchanged

Default Settings (locked via Chris AskUserQuestion 2026-05-25 D1 cont per
ADR-0037 Decision Log — `Settings.parent_doc_*`):
- `enable_parent_doc_retrieval=False` (Q4 — measurement-experiment opt-in)
- `parent_doc_section_depth_offset=1` (Q2 — parent = drop last level)
- `parent_doc_top_k=1` (Q1 — top-1 anchor only, conservative)
- `parent_doc_max_tokens_per_parent=4000` (Q3 — ~15 sibling envelope)
- `parent_doc_max_chunks_per_parent=50` (safety cap)
- `parent_doc_fallback_to_doc_on_shallow=True` (graceful fallback)
"""

from __future__ import annotations

import time
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

import structlog

from observability.observe import emit_stage_metadata
from retrieval.hybrid import HybridSearcher, HybridSearchHit

logger = structlog.get_logger(__name__)

# Langfuse stage name for V6 Debug View 10-stage scaffold per ADR-0037 Q5
# Option A — explicit「Parent-Document Retriever」stage card insert between
# Context Expander + CRAG. Frontend `STAGE_DEFS` array in
# `frontend/app/debug/[traceId]/page.tsx` matches this prefix.
_STAGE_NAME = "generation.parent_doc_retrieval"


# Token estimate heuristic: 4 chars ≈ 1 token (per ADR-0034 P95<5s budget
# framing). Approximate but sufficient for tail-drop truncation decisions;
# the precise tokenizer round-trip would inflate per-aggregation latency
# without changing the policy outcome.
def _estimate_tokens(text: str) -> int:
    """4-char-per-token rough estimate (Karpathy §1.2 simplicity-first)."""
    return max(1, len(text) // 4)


@dataclass(slots=True, frozen=True)
class ParentSectionChunk:
    """Reranked chunk with parent section aggregation per ADR-0037.

    Duck-typed compatible with `RetrievedChunk` + `ExpandedChunk` for
    `prompt_builder` dispatch chain (`parent_section_text > expanded_text >
    chunk_text` fallback in `build_prompt`). `fields` dict gains a
    `parent_section_text` key when aggregation applied; otherwise
    `prompt_builder` falls back to `expanded_text` (if Context Expander ran)
    or raw `chunk_text`.

    Citation rendering uses original anchor `chunk_id` + `chunk_text` —
    parent section is LLM-input-only enrichment per architecture.md §3.5
    Citation contract.
    """

    score: float
    fields: dict[str, Any]
    parent_section_text: str | None
    parent_path: list[str] | None
    sibling_count: int
    truncated: bool

    @classmethod
    def no_aggregation(cls, chunk: object) -> ParentSectionChunk:
        """Wrap an upstream chunk without parent aggregation (flag-off / shallow /
        missing metadata / lookup miss). Duck-typed on `score` + `fields`."""
        return cls(
            score=float(getattr(chunk, "score", 0.0)),
            fields=dict(getattr(chunk, "fields", {}) or {}),
            parent_section_text=None,
            parent_path=None,
            sibling_count=0,
            truncated=False,
        )


@dataclass(slots=True, frozen=True)
class ParentDocStats:
    """Aggregate stats per ADR-0037 §Observability + V6 Debug View 10-stage."""

    requested_anchors: int
    parents_fetched: int      # parents with ≥1 sibling fetched
    siblings_aggregated: int  # total sibling chunks consumed across all parents
    truncated_count: int       # anchors whose parent section hit token budget cap
    skipped_shallow_count: int  # anchors skipped due to shallow / missing section_path
    fetch_latency_ms: int      # total batch fetch wall-clock


def _emit_parent_doc_stage(stats: ParentDocStats) -> None:
    """Surface ParentDocStats to Langfuse / V6 Debug View per ADR-0037 §7.

    Latency keyed as `duration_ms` (= total batch fetch latency) so
    `langfuse_trace._extract_stage` maps it to `TraceStage.latency_ms`
    uniformly with `observe_async`-emitted stages and ADR-0020 Context
    Expander stage. Remaining counts land in `TraceStage.details`.
    """
    emit_stage_metadata(
        _STAGE_NAME,
        duration_ms=stats.fetch_latency_ms,
        requested_anchors=stats.requested_anchors,
        parents_fetched=stats.parents_fetched,
        siblings_aggregated=stats.siblings_aggregated,
        truncated_count=stats.truncated_count,
        skipped_shallow_count=stats.skipped_shallow_count,
    )


def _compute_parent_path(
    section_path: list[str],
    *,
    section_depth_offset: int,
    fallback_to_doc_on_shallow: bool,
) -> list[str] | None:
    """Compute parent path per Q2 + Q-fallback locked decisions.

    Returns None when no usable parent_path can be derived (caller skips
    that anchor with `skipped_shallow_count` increment).
    """
    if not section_path:
        return None
    if len(section_path) > section_depth_offset:
        # Normal case — drop the last `section_depth_offset` levels
        return section_path[:-section_depth_offset]
    if fallback_to_doc_on_shallow:
        # Shallow — preserve at least the top-1 segment as parent so caller
        # gets some aggregation (e.g. anchor in `["Doc"]` with offset=1 →
        # parent = `["Doc"]`, which fetches the whole doc within hard cap).
        return section_path[:1]
    return None


async def aggregate_parent_sections(
    reranked_chunks: Sequence[object],
    kb_id: str,
    searcher: HybridSearcher,
    *,
    section_depth_offset: int = 1,
    parent_doc_top_k: int = 1,
    max_tokens_per_parent: int = 4000,
    max_chunks_per_parent: int = 50,
    fallback_to_doc_on_shallow: bool = True,
) -> tuple[list[ParentSectionChunk], ParentDocStats]:
    """Aggregate parent sections for top-K reranked anchors per ADR-0037 W26 F2.

    `reranked_chunks` accepts `list[RetrievedChunk]` or `list[ExpandedChunk]`
    (duck-typed on `score` + `fields`) so the step composes with ADR-0020
    Context Expander upstream (Q6 Both on coexistence policy).

    `kb_id` required per ADR-0018 multi-KB invariant (searcher routes per-KB
    index_name dynamically).

    Returns `(parent_section_chunks, stats)` — see `ParentSectionChunk`
    docstring for dispatch chain semantics + `ParentDocStats` for
    observability fields.
    """
    if not reranked_chunks:
        empty_stats = ParentDocStats(
            requested_anchors=0,
            parents_fetched=0,
            siblings_aggregated=0,
            truncated_count=0,
            skipped_shallow_count=0,
            fetch_latency_ms=0,
        )
        _emit_parent_doc_stage(empty_stats)
        return [], empty_stats

    # Step 1 — anchor selection per parent_doc_top_k (default 1 = top-1 only
    # per Q1 Recommended pick; conservative to minimize off-topic leak).
    anchors = list(reranked_chunks[:parent_doc_top_k])
    passthrough = list(reranked_chunks[parent_doc_top_k:])

    # Step 2 + 3 — compute parent paths per anchor + deduplicate (doc_id, parent_path)
    # tuples. anchor_specs preserves anchor order so per-anchor result mapping stays
    # stable; parent_fetch_specs uses ordered dict semantics for dedup.
    anchor_specs: list[tuple[object, str, list[str] | None]] = []
    parent_fetch_specs: dict[tuple[str, tuple[str, ...]], None] = {}
    skipped_shallow_count = 0
    for anchor in anchors:
        fields = dict(getattr(anchor, "fields", {}) or {})
        section_path_raw = fields.get("section_path") or []
        section_path = [str(s) for s in section_path_raw if s is not None]
        doc_id = str(fields.get("doc_id", ""))
        if not doc_id:
            anchor_specs.append((anchor, doc_id, None))
            skipped_shallow_count += 1
            continue
        parent_path = _compute_parent_path(
            section_path,
            section_depth_offset=section_depth_offset,
            fallback_to_doc_on_shallow=fallback_to_doc_on_shallow,
        )
        if parent_path is None or not parent_path:
            anchor_specs.append((anchor, doc_id, None))
            skipped_shallow_count += 1
            continue
        anchor_specs.append((anchor, doc_id, parent_path))
        parent_fetch_specs[(doc_id, tuple(parent_path))] = None

    # Step 4 — batch fetch each unique (doc_id, parent_path); per-parent network
    # error caught + logged so a single failure doesn't blow up the whole pipeline.
    fetch_start = time.perf_counter()
    parent_lookup: dict[tuple[str, tuple[str, ...]], list[HybridSearchHit]] = {}
    for doc_id, parent_tuple in parent_fetch_specs:
        siblings: list[HybridSearchHit]
        try:
            siblings = await searcher.fetch_chunks_by_section_path(
                parent_path=list(parent_tuple),
                doc_id=doc_id,
                kb_id=kb_id,
                max_chunks=max_chunks_per_parent,
            )
        except Exception as exc:  # noqa: BLE001 — graceful degradation per ADR-0020 precedent
            logger.warning(
                "parent_doc_fetch_failed",
                error=f"{type(exc).__name__}: {exc}",
                kb_id=kb_id,
                doc_id=doc_id,
                parent_path=list(parent_tuple),
            )
            siblings = []
        parent_lookup[(doc_id, parent_tuple)] = siblings
    fetch_latency_ms = int((time.perf_counter() - fetch_start) * 1000)

    # Step 5 — assemble per-anchor parent section text with token-budget truncation
    result: list[ParentSectionChunk] = []
    truncated_count = 0
    total_siblings_used = 0
    parents_fetched_count = 0
    seen_parents: set[tuple[str, tuple[str, ...]]] = set()
    for anchor, doc_id, parent_path in anchor_specs:
        if parent_path is None or not doc_id:
            result.append(ParentSectionChunk.no_aggregation(anchor))
            continue

        siblings = parent_lookup.get((doc_id, tuple(parent_path)), [])
        if not siblings:
            # Lookup miss — caller still gets anchor unchanged via fallback
            result.append(
                ParentSectionChunk(
                    score=float(getattr(anchor, "score", 0.0)),
                    fields=dict(getattr(anchor, "fields", {}) or {}),
                    parent_section_text=None,
                    parent_path=parent_path,
                    sibling_count=0,
                    truncated=False,
                )
            )
            continue

        key = (doc_id, tuple(parent_path))
        if key not in seen_parents:
            seen_parents.add(key)
            parents_fetched_count += 1

        # Tail-drop truncation preserving narrative start (siblings already
        # ordered by chunk_index ASC from the searcher's `orderby` payload).
        sibling_texts: list[str] = []
        token_count = 0
        truncated = False
        for sibling in siblings:
            sib_fields = dict(getattr(sibling, "fields", {}) or {})
            text = str(sib_fields.get("chunk_text", ""))
            if not text:
                continue
            sib_tokens = _estimate_tokens(text)
            # Always include the first sibling even if it alone exceeds budget,
            # so a degenerate large-chunk doc still gets some context (truncated
            # flag surfaces the situation to observability).
            if token_count + sib_tokens > max_tokens_per_parent and sibling_texts:
                truncated = True
                break
            sibling_texts.append(text)
            token_count += sib_tokens

        if not sibling_texts:
            result.append(
                ParentSectionChunk(
                    score=float(getattr(anchor, "score", 0.0)),
                    fields=dict(getattr(anchor, "fields", {}) or {}),
                    parent_section_text=None,
                    parent_path=parent_path,
                    sibling_count=0,
                    truncated=False,
                )
            )
            continue

        parent_section_text = "\n\n".join(sibling_texts)
        original_fields = dict(getattr(anchor, "fields", {}) or {})
        new_fields = {**original_fields, "parent_section_text": parent_section_text}
        result.append(
            ParentSectionChunk(
                score=float(getattr(anchor, "score", 0.0)),
                fields=new_fields,
                parent_section_text=parent_section_text,
                parent_path=parent_path,
                sibling_count=len(sibling_texts),
                truncated=truncated,
            )
        )
        total_siblings_used += len(sibling_texts)
        if truncated:
            truncated_count += 1

    # Step 6 — pass through any non-anchor reranked chunks unchanged so their
    # ADR-0020 prev/next expansion stays intact per Q6 Both on coexistence policy.
    for chunk in passthrough:
        result.append(ParentSectionChunk.no_aggregation(chunk))

    stats = ParentDocStats(
        requested_anchors=len(anchors),
        parents_fetched=parents_fetched_count,
        siblings_aggregated=total_siblings_used,
        truncated_count=truncated_count,
        skipped_shallow_count=skipped_shallow_count,
        fetch_latency_ms=fetch_latency_ms,
    )

    logger.info(
        "parent_doc_aggregation_complete",
        kb_id=kb_id,
        requested_anchors=stats.requested_anchors,
        parents_fetched=stats.parents_fetched,
        siblings_aggregated=stats.siblings_aggregated,
        truncated_count=stats.truncated_count,
        skipped_shallow_count=stats.skipped_shallow_count,
        fetch_latency_ms=stats.fetch_latency_ms,
    )
    _emit_parent_doc_stage(stats)
    return result, stats
