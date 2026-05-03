"""Retrieval engine public API (per architecture.md §3.1 + components/C04 §1).

W2 baseline pipeline:
    query string + kb_id + top_k
        → embed query (Azure OpenAI text-embedding-3-large 1024d)
        → hybrid search (Azure AI Search BM25 + vector RRF)
        → return list[RetrievedChunk] (top_k)

W3 will insert Cohere Rerank between hybrid and final return; W2 baseline returns
hybrid hits directly to support Gate 1 R@5 ≥ 80% measurement (no rerank yet).
"""

from __future__ import annotations

import time
from dataclasses import dataclass

import structlog

from ingestion.embedding.base import Embedder
from retrieval.hybrid import HybridSearcher

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
    total_latency_ms: int


class RetrievalEngine:
    """Coordinator for query embedding + hybrid search.

    Caller manages embedder + searcher lifecycles (both context-managers).
    """

    def __init__(
        self,
        embedder: Embedder,
        searcher: HybridSearcher,
    ) -> None:
        self._embedder = embedder
        self._searcher = searcher

    async def retrieve(
        self,
        query: str,
        top_k: int = 50,
        filter_clause: str | None = None,
    ) -> RetrievalResult:
        """Embed query + hybrid search; return ordered chunks + timings.

        kb_id is implicit via the searcher's index_name (caller wires per-KB
        searcher when multi-KB lands; W2 baseline = single Drive KB).
        """
        if not query or not query.strip():
            return RetrievalResult(chunks=[], embed_latency_ms=0, search_latency_ms=0, total_latency_ms=0)

        total_start = time.perf_counter()

        embed_start = time.perf_counter()
        query_embedding = await self._embedder.embed(query)
        embed_latency_ms = int((time.perf_counter() - embed_start) * 1000)

        search_start = time.perf_counter()
        hits = await self._searcher.search(
            query_text=query,
            query_vector=query_embedding.vector,
            top_k=top_k,
            filter_clause=filter_clause if filter_clause is not None
            else "enabled eq true and low_value_flag eq false",
        )
        search_latency_ms = int((time.perf_counter() - search_start) * 1000)

        total_latency_ms = int((time.perf_counter() - total_start) * 1000)

        chunks = [RetrievedChunk(score=h.score, fields=h.fields) for h in hits]

        logger.info(
            "retrieval_complete",
            query_chars=len(query),
            top_k=top_k,
            chunks_returned=len(chunks),
            embed_latency_ms=embed_latency_ms,
            search_latency_ms=search_latency_ms,
            total_latency_ms=total_latency_ms,
        )

        return RetrievalResult(
            chunks=chunks,
            embed_latency_ms=embed_latency_ms,
            search_latency_ms=search_latency_ms,
            total_latency_ms=total_latency_ms,
        )
