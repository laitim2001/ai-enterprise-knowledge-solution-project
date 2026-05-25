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
from typing import Literal

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
        mode: Literal["hybrid", "vector", "fulltext"] = "hybrid",
        rerank: bool = True,
    ) -> RetrievalResult:
        """Embed query + search (mode-selectable) + optional rerank; ordered chunks + timings.

        ADR-0021: `mode` selects hybrid (default) / vector / fulltext at the
        searcher; `rerank=False` skips the reranker even when one is wired
        (the V4 Retrieval Testing tab's "Rerank Model toggle"). `mode="fulltext"`
        skips query embedding (BM25 doesn't use the vector).

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

        if mode == "fulltext":
            query_vector: list[float] = []
            embed_latency_ms = 0
        else:
            embed_start = time.perf_counter()
            query_embedding = await self._embedder.embed(query)
            query_vector = query_embedding.vector
            embed_latency_ms = int((time.perf_counter() - embed_start) * 1000)

        do_rerank = self._reranker is not None and rerank
        # When reranking, fetch a wider candidate set then rerank to top_k.
        fetch_k = max(top_k, self._hybrid_overfetch) if do_rerank else top_k
        search_start = time.perf_counter()
        hits = await self._searcher.search(
            query_text=query,
            query_vector=query_vector,
            kb_id=kb_id,
            top_k=fetch_k,
            filter_clause=filter_clause if filter_clause is not None
            else "enabled eq true",  # per ADR-0035 W25 F5 D2 (was: + " and low_value_flag eq false")
            mode=mode,
        )
        search_latency_ms = int((time.perf_counter() - search_start) * 1000)

        rerank_latency_ms = 0
        reranked = False
        if do_rerank and hits:
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
            mode=mode,
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

    async def expand_context_for_chunks(
        self,
        chunks: list[RetrievedChunk],
        kb_id: str,
    ):
        """Wrap top-K reranked chunks with prev/next neighbor context per ADR-0020.

        Delegates to generation.context_expander.expand_context using the engine's
        searcher (encapsulation preserved — caller doesn't need direct searcher access).
        Returns (list[ExpandedChunk], ExpansionStats) — see context_expander.py for shape.
        """
        # Local import avoids circular dependency: context_expander imports from
        # retrieval.retrieval_engine for RetrievedChunk; engine→expander would cycle.
        from generation.context_expander import expand_context  # noqa: PLC0415

        return await expand_context(chunks, kb_id=kb_id, searcher=self._searcher)

    async def aggregate_parent_sections_for_chunks(
        self,
        chunks: list[RetrievedChunk],
        kb_id: str,
        *,
        section_depth_offset: int = 1,
        parent_doc_top_k: int = 1,
        max_tokens_per_parent: int = 4000,
        max_chunks_per_parent: int = 50,
        fallback_to_doc_on_shallow: bool = True,
    ):
        """Aggregate parent sections for top-K reranked anchors per ADR-0037 W26 F2.

        Public wrapper preserving searcher encapsulation (caller doesn't reach into
        `_searcher` directly — matches `expand_context_for_chunks` pattern). Accepts
        `list[RetrievedChunk]` or `list[ExpandedChunk]` (duck-typed on score+fields)
        so the step composes after Context Expander upstream (Q6 Both on policy).

        Returns (list[ParentSectionChunk], ParentDocStats) — see
        `generation.parent_doc_retriever.py` for shape + algorithm.

        Default kwargs reflect Chris AskUserQuestion 2026-05-25 D1 cont picks
        (Q1 + Q2 + Q3 + fallback) but callers SHOULD pass values from `Settings`
        so production tuning flows via `.env` not module defaults.
        """
        # Local import avoids circular dependency (parallel to expand_context above).
        from generation.parent_doc_retriever import aggregate_parent_sections  # noqa: PLC0415

        return await aggregate_parent_sections(
            chunks,
            kb_id=kb_id,
            searcher=self._searcher,
            section_depth_offset=section_depth_offset,
            parent_doc_top_k=parent_doc_top_k,
            max_tokens_per_parent=max_tokens_per_parent,
            max_chunks_per_parent=max_chunks_per_parent,
            fallback_to_doc_on_shallow=fallback_to_doc_on_shallow,
        )

    async def list_documents(self, kb_id: str, max_chunks: int = 1000) -> list[dict]:
        """W16 F5.1.1 — delegate to searcher.list_documents (encapsulation preserved).

        Returns aggregated doc-level metadata for kb_id-scoped chunks. See
        HybridSearcher.list_documents for shape + Beta-scale assumptions.
        """
        return await self._searcher.list_documents(kb_id, max_chunks=max_chunks)

    async def list_chunks(self, kb_id: str, doc_id: str, top: int = 1000) -> list[dict]:
        """W16 F5.1.2 — delegate to searcher.list_chunks (encapsulation preserved).

        Returns chunk-level metadata for kb_id+doc_id-scoped chunks ordered by
        chunk_index. See HybridSearcher.list_chunks for shape.
        """
        return await self._searcher.list_chunks(kb_id, doc_id, top=top)
