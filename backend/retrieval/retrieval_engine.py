"""Retrieval engine public API (per architecture.md §3.1 + components/C04 §1).

W3 D2 pipeline (rerank wired W3 D1 後段 + D2; W16+ ADR-0018 kb_id propagation):
    query string + kb_id + top_k
        → embed query (Azure OpenAI text-embedding-3-large 1024d)
        → hybrid search (Azure AI Search BM25 + vector RRF + kb_id-scoped)
            top hybrid_overfetch
        → optional Cohere Rerank (Path A Marketplace) → top top_k
        → return list[RetrievedChunk]

W16+ ADR-0018 multi-KB invariant: retrieve() requires kb_id parameter. kb_id
propagates to HybridSearcher for dynamic index_name + filter clause scoping
(audit-W15-d5-vs-spec.md §CC-1 closure). Reranker signature unchanged — chunks
arrive already KB-scoped from searcher per Karpathy §1.2 simplicity-first.

When reranker is None, engine returns hybrid hits directly (W2 baseline behavior
preserved for local dev / tests / pre-procurement). Live rerank engages once
Chris populates `cohere_endpoint` + `cohere_api_key` in `.env`.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

import structlog

from ingestion.embedding.base import Embedder
from observability.observe import observe_async
from retrieval.hybrid import HybridSearcher
from retrieval.reranker.base import Reranker

logger = structlog.get_logger(__name__)


@dataclass(slots=True, frozen=True)
class RetrievedChunk:
    """One retrieval hit — score + ChunkRecord-shaped fields dict.

    fields dict keys match Azure AI Search index schema (per architecture.md §3.6),
    notably:
    - chunk_id, kb_id, doc_id, doc_title, doc_format
    - chunk_index, chunk_total, chunk_title, chunk_text, chunk_token_count
    - section_path, embedded_images_json (string), tags
    - prev_chunk_id, next_chunk_id, source_url, ingested_at
    Caller (e.g. /query route) decides which subset to expose to client.
    """

    score: float
    fields: dict


@dataclass(slots=True, frozen=True)
class RetrievalResult:
    """Aggregate retrieval response — chunks + timing for trace + observability."""

    chunks: list[RetrievedChunk]
    embed_latency_ms: int
    search_latency_ms: int
    rerank_latency_ms: int
    total_latency_ms: int
    reranked: bool  # True when reranker was invoked, False when hybrid-only


class RetrievalEngine:
    """Coordinator for query embedding + hybrid search + optional Cohere rerank.

    Caller manages embedder + searcher + reranker lifecycles (all context-managers).
    """

    def __init__(
        self,
        embedder: Embedder,
        searcher: HybridSearcher,
        reranker: Reranker | None = None,
        hybrid_overfetch_for_rerank: int = 50,
    ) -> None:
        self._embedder = embedder
        self._searcher = searcher
        self._reranker = reranker
        self._hybrid_overfetch = hybrid_overfetch_for_rerank

    @observe_async(
        name="retrieval.retrieve",
        capture_attrs=(
            "embed_latency_ms",
            "search_latency_ms",
            "rerank_latency_ms",
            "total_latency_ms",
            "reranked",
        ),
    )
    async def retrieve(
        self,
        query: str,
        kb_id: str,
        top_k: int = 50,
        filter_clause: str | None = None,
    ) -> RetrievalResult:
        """Embed query + hybrid search + optional rerank; return ordered chunks + timings.

        kb_id required per ADR-0018 multi-KB invariant — propagates to HybridSearcher
        for dynamic index_name + kb_id eq filter clause (per-KB scoping mandatory).
        """
        if not query or not query.strip():
            return RetrievalResult(
                chunks=[],
                embed_latency_ms=0,
                search_latency_ms=0,
                rerank_latency_ms=0,
                total_latency_ms=0,
                reranked=False,
            )

        total_start = time.perf_counter()

        embed_start = time.perf_counter()
        query_embedding = await self._embedder.embed(query)
        embed_latency_ms = int((time.perf_counter() - embed_start) * 1000)

        # When reranker present, fetch wider candidate set then rerank to top_k.
        fetch_k = (
            max(top_k, self._hybrid_overfetch)
            if self._reranker is not None
            else top_k
        )
        search_start = time.perf_counter()
        hits = await self._searcher.search(
            query_text=query,
            query_vector=query_embedding.vector,
            kb_id=kb_id,
            top_k=fetch_k,
            filter_clause=filter_clause if filter_clause is not None
            else "enabled eq true and low_value_flag eq false",
        )
        search_latency_ms = int((time.perf_counter() - search_start) * 1000)

        rerank_latency_ms = 0
        reranked = False
        if self._reranker is not None and hits:
            rerank_start = time.perf_counter()
            reranked_chunks = await self._reranker.rerank(
                query=query, candidates=hits, top_k=top_k,
            )
            rerank_latency_ms = int((time.perf_counter() - rerank_start) * 1000)
            chunks = [
                RetrievedChunk(score=r.rerank_score, fields=r.fields)
                for r in reranked_chunks
            ]
            reranked = True
        else:
            chunks = [
                RetrievedChunk(score=h.score, fields=h.fields)
                for h in hits[:top_k]
            ]

        total_latency_ms = int((time.perf_counter() - total_start) * 1000)

        logger.info(
            "retrieval_complete",
            kb_id=kb_id,
            query_chars=len(query),
            top_k=top_k,
            fetch_k=fetch_k,
            chunks_returned=len(chunks),
            reranked=reranked,
            embed_latency_ms=embed_latency_ms,
            search_latency_ms=search_latency_ms,
            rerank_latency_ms=rerank_latency_ms,
            total_latency_ms=total_latency_ms,
        )

        return RetrievalResult(
            chunks=chunks,
            embed_latency_ms=embed_latency_ms,
            search_latency_ms=search_latency_ms,
            rerank_latency_ms=rerank_latency_ms,
            total_latency_ms=total_latency_ms,
            reranked=reranked,
        )
