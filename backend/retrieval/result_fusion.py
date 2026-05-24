"""Reciprocal Rank Fusion (RRF) over multi-variant retrieval per ADR-0034.

Given N query variants from QueryReformulator, run each through the
RetrievalEngine in parallel, then fuse the per-variant top-K results via
the canonical RRF formula:

    rrf_score(chunk) = sum over variants of 1 / (rrf_k + rank_in_variant)

where `rank_in_variant` is 1-indexed position in that variant's top-K
results. Chunks not present in a variant's top-K contribute 0 from that
variant. Top-K of the fused set (by descending RRF score, deduped by
chunk_id) becomes the final result.

Per ADR-0034 §Decision (b): RRF rank-floor constant 60 follows Cormack
et al. 2009 SIGIR paper canonical recommendation. The function is
parallel — N variants kicked off concurrently via asyncio.gather; total
latency ≈ max(per-variant latencies) not the sum (assuming concurrent
Azure capacity headroom).

Per ADR-0034 §Implementation Mapping: this module replaces the single
`engine.retrieve(query, ...)` call when `Settings.enable_query_expansion=
True`; original path bit-identical when False (caller branches at
query.py route).
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass

import structlog

from retrieval.retrieval_engine import RetrievalEngine, RetrievalResult, RetrievedChunk

logger = structlog.get_logger(__name__)


RRF_K_DEFAULT = 60  # Cormack et al. 2009 canonical rank-floor constant


@dataclass(slots=True, frozen=True)
class FusedRetrievalResult:
    """Aggregate result of fused_retrieve — shape parallels RetrievalResult.

    Fields mirror RetrievalResult so the downstream pipeline (Cohere rerank
    timing is folded into per-variant total_latency_ms; CRAG loop,
    synthesizer, citation_enrichment) can consume the result with minimal
    branching. Caller adapts to RetrievalResult via `as_retrieval_result()`
    if a uniform shape is needed.
    """

    chunks: list[RetrievedChunk]
    variant_count: int                # = len(variants) actually issued (not LLM max)
    fused_top_k: int                  # = top_k requested by caller
    per_variant_latency_ms: list[int]  # for trace / Langfuse correlation
    fusion_latency_ms: int             # RRF computation alone (typically < 1ms)
    total_latency_ms: int              # wall-clock incl. parallel retrieves + fusion
    reranked: bool                     # True iff any variant ran rerank (= engine.retrieve(rerank=True))

    def as_retrieval_result(self) -> RetrievalResult:
        """Adapt to RetrievalResult so downstream code (CRAG, synthesizer)
        accepts fused output without branching on type. Per-variant timings
        flattened into a single embed/search/rerank/total — sum of
        per-variant total (over-estimate for serial sum vs parallel max);
        caller surfaces fused_top_k + variant_count separately via logs.
        """
        total = sum(self.per_variant_latency_ms) + self.fusion_latency_ms
        return RetrievalResult(
            chunks=self.chunks,
            # Per-variant breakdown isn't surfaced; lump everything under
            # search_latency_ms so the downstream observers see "all the
            # retrieval cost lives in the search stage" without surprise.
            embed_latency_ms=0,
            search_latency_ms=total - self.fusion_latency_ms,
            rerank_latency_ms=0,
            total_latency_ms=self.total_latency_ms,
            reranked=self.reranked,
        )


async def fused_retrieve(
    variants: list[str],
    kb_id: str,
    top_k: int,
    engine: RetrievalEngine,
    rrf_k: int = RRF_K_DEFAULT,
    per_variant_overfetch: int = 2,
) -> FusedRetrievalResult:
    """Run hybrid retrieve per variant in parallel, fuse via RRF, return top-K.

    `per_variant_overfetch`: each variant fetches `per_variant_overfetch *
    top_k` candidates so chunks ranking just outside one variant's top-K
    still contribute to the fused set if they rank highly in other
    variants. Default 2× balances recall vs Azure Search cost. Engine's
    rerank stays ON per variant — RRF over reranked per-variant lists is
    the canonical RAG-fusion shape (Option A per ADR-0034 reasoning trace).

    Empty `variants` → empty FusedRetrievalResult (no LLM/Azure cost).
    Single variant → behaves as `engine.retrieve(variant, ...)` plain
    (RRF over 1 list = identity ordering). Both edge cases preserve
    downstream pipeline stability without erroring.
    """
    if not variants:
        return FusedRetrievalResult(
            chunks=[],
            variant_count=0,
            fused_top_k=top_k,
            per_variant_latency_ms=[],
            fusion_latency_ms=0,
            total_latency_ms=0,
            reranked=False,
        )

    total_start = time.perf_counter()
    fetch_k_per_variant = top_k * per_variant_overfetch

    # Parallel fan-out: each variant is independent IO-bound work (embed
    # + Azure Search + optional Cohere rerank). asyncio.gather kicks them
    # off concurrently; total latency ≈ slowest variant not sum.
    variant_results: list[RetrievalResult] = await asyncio.gather(
        *(
            engine.retrieve(
                query=variant,
                kb_id=kb_id,
                top_k=fetch_k_per_variant,
            )
            for variant in variants
        ),
    )

    # RRF fusion: accumulate score per chunk_id across all variant rankings.
    fusion_start = time.perf_counter()
    rrf_scores: dict[str, float] = {}
    chunk_by_id: dict[str, RetrievedChunk] = {}
    for vresult in variant_results:
        for rank, chunk in enumerate(vresult.chunks, start=1):
            chunk_id = str(chunk.fields.get("chunk_id", "") or "")
            if not chunk_id:
                # Defensive: malformed chunk without chunk_id — skip rather
                # than collide on empty-string key.
                continue
            rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0.0) + 1.0 / (rrf_k + rank)
            # First occurrence wins for stored chunk fields (the variants
            # return the same Azure Search documents, so any copy is fine).
            chunk_by_id.setdefault(chunk_id, chunk)

    # Sort by descending RRF score, then by chunk_id ascending for stable
    # tie-breaking (matters when N variants produce identical rankings).
    ranked_ids = sorted(rrf_scores.keys(), key=lambda cid: (-rrf_scores[cid], cid))
    top_chunks = [
        RetrievedChunk(score=rrf_scores[cid], fields=chunk_by_id[cid].fields)
        for cid in ranked_ids[:top_k]
    ]
    fusion_latency_ms = int((time.perf_counter() - fusion_start) * 1000)

    total_latency_ms = int((time.perf_counter() - total_start) * 1000)
    reranked_any = any(v.reranked for v in variant_results)

    logger.info(
        "fused_retrieve_complete",
        kb_id=kb_id,
        variant_count=len(variants),
        per_variant_fetch_k=fetch_k_per_variant,
        unique_chunks_across_variants=len(rrf_scores),
        returned_top_k=len(top_chunks),
        fusion_latency_ms=fusion_latency_ms,
        total_latency_ms=total_latency_ms,
        reranked=reranked_any,
    )

    return FusedRetrievalResult(
        chunks=top_chunks,
        variant_count=len(variants),
        fused_top_k=top_k,
        per_variant_latency_ms=[v.total_latency_ms for v in variant_results],
        fusion_latency_ms=fusion_latency_ms,
        total_latency_ms=total_latency_ms,
        reranked=reranked_any,
    )
