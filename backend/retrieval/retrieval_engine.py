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
from retrieval.reranker.base import RerankedChunk, Reranker

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
        reranker_cross_section_deboost: float = 1.0,
        reranker_section_path_prefix_depth: int = 2,
        reranker_overfetch_multiplier: int = 1,
    ) -> None:
        self._embedder = embedder
        self._searcher = searcher
        self._reranker = reranker
        self._hybrid_overfetch = hybrid_overfetch_for_rerank
        # W38 — post-rerank cross-section deboost (per ADR-0035 W25 symmetric pattern;
        # non-architectural per H1, post-rerank client-side score multiply only).
        # deboost=1.0 disabled (W38 baseline preserve W37); 0.85 = typical 15% penalty.
        self._reranker_cross_section_deboost = reranker_cross_section_deboost
        self._reranker_section_path_prefix_depth = reranker_section_path_prefix_depth
        # W40 F2 — Cohere overfetch multiplier (per W39 insight 1). When deboost
        # active AND multiplier > 1, rerank fetches top_k * multiplier candidates
        # so deboost loop can swap-in same-section from positions 6-50; post-deboost
        # truncates to original top_k preserving caller contract. multiplier=1
        # (default) preserves W38 baseline behavior.
        self._reranker_overfetch_multiplier = reranker_overfetch_multiplier

    @property
    def reranker(self) -> Reranker | None:
        """Read-only handle to the configured reranker (``None`` = hybrid-only).

        The engine stores it privately as ``self._reranker``; this public
        accessor exists so ``/health._check_cohere`` (and any caller) can probe
        "is a reranker wired?" without reaching into a private attr. Without it,
        ``getattr(engine, "reranker", None)`` silently fell through to ``None``
        and a live Cohere reranker was misreported ``not_configured`` (BUG-029;
        cosmetic, surfaced W26 D1 + W27 D2 before being fixed here).
        """
        return self._reranker

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
        overfetch: int | None = None,
        user_principals: list[str] | None = None,
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
        # CH-007: `overfetch` overrides the per-engine `self._hybrid_overfetch` default
        # so a per-KB `default_top_k` can size the rerank candidate pool. `None` keeps
        # the W38 baseline (the global Settings.hybrid_top_k_retrieval the engine was
        # built with) → bit-identical to pre-CH-007 for callers that don't pass it.
        effective_overfetch = overfetch if overfetch is not None else self._hybrid_overfetch
        fetch_k = max(top_k, effective_overfetch) if do_rerank else top_k
        search_start = time.perf_counter()
        hits = await self._searcher.search(
            query_text=query,
            query_vector=query_vector,
            kb_id=kb_id,
            top_k=fetch_k,
            filter_clause=filter_clause if filter_clause is not None
            else "enabled eq true",  # per ADR-0035 W25 F5 D2 (was: + " and low_value_flag eq false")
            mode=mode,
            user_principals=user_principals,
        )
        search_latency_ms = int((time.perf_counter() - search_start) * 1000)

        rerank_latency_ms = 0
        reranked = False
        rerank_top_k = top_k  # W40 F2 — observability default; overridden when overfetch active
        if do_rerank and hits:
            rerank_start = time.perf_counter()
            # W40 F2 — Cohere overfetch when deboost active (per W39 insight 1).
            # Pass top_k * multiplier so deboost loop has wider candidate pool to
            # swap-in same-section from positions 6-50. When multiplier=1 (default)
            # OR deboost disabled, behavior preserves W38 baseline (rerank to exact top_k).
            # Cohere v4.0-pro API self-caps via top_n=min(top_k, len(candidates))
            # so safe up to fetch_k=hybrid_overfetch_for_rerank=50.
            if (self._reranker_cross_section_deboost < 1.0
                    and self._reranker_overfetch_multiplier > 1):
                rerank_top_k = top_k * self._reranker_overfetch_multiplier
            reranked_chunks = await self._reranker.rerank(
                query=query, candidates=hits, top_k=rerank_top_k,
            )
            # W38 — post-rerank cross-section deboost (H1 non-architectural;
            # symmetric pattern per ADR-0035 W25 F5 D2; preserves Cohere v4.0-pro
            # API contract). When deboost<1.0, candidates whose section_path[:depth]
            # ≠ anchor's section_path[:depth] get rerank_score *= deboost; then
            # re-sort by rerank_score descending. Default disabled (deboost=1.0).
            #
            # NOTE: `RerankedChunk` is frozen=True (per base.py:18), so deboost is
            # implemented via rebuild — new RerankedChunk instances replace deboosted
            # candidates, unchanged candidates pass through by reference.
            if self._reranker_cross_section_deboost < 1.0 and reranked_chunks:
                anchor_sp_raw = reranked_chunks[0].fields.get("section_path")
                anchor_sp = anchor_sp_raw if isinstance(anchor_sp_raw, list) else []
                depth = self._reranker_section_path_prefix_depth
                # W40 F1 — anchor-prefix length-mismatch fix (W39 insight 2). When
                # anchor_sp shorter than depth (e.g. corpus chapter intro chunk
                # section_path=['8. Integration scenarios...'] length 1 with depth=2),
                # cap effective_depth to anchor length to avoid silently comparing
                # length-1 anchor_prefix against length-2 cand_prefix (which always
                # not-equal → over-deboost zoom-ins like ['§8','§8.1'] incorrectly).
                # When anchor_sp empty (effective_depth=0), anchor_prefix=[] and all
                # cand_prefix=[] → no deboost (defensive — can't classify w/o anchor).
                effective_depth = min(depth, len(anchor_sp))
                anchor_prefix = list(anchor_sp[:effective_depth])
                deboost_count = 0
                new_reranked: list[RerankedChunk] = []
                for r in reranked_chunks:
                    cand_sp_raw = r.fields.get("section_path")
                    if not isinstance(cand_sp_raw, list):
                        # malformed → defensive skip (preserve rank by passing through)
                        new_reranked.append(r)
                        continue
                    cand_prefix = list(cand_sp_raw[:effective_depth])
                    if cand_prefix and cand_prefix != anchor_prefix:
                        new_reranked.append(RerankedChunk(
                            fields=r.fields,
                            rerank_score=r.rerank_score * self._reranker_cross_section_deboost,
                            hybrid_score=r.hybrid_score,
                            original_index=r.original_index,
                        ))
                        deboost_count += 1
                    else:
                        new_reranked.append(r)
                # Re-sort post-deboost — rerank_score descending invariant preserved
                new_reranked.sort(key=lambda r: r.rerank_score, reverse=True)
                reranked_chunks = new_reranked
                logger.info(
                    "reranker_cross_section_deboost_applied",
                    anchor_prefix=anchor_prefix,
                    depth=depth,
                    effective_depth=effective_depth,
                    deboost_factor=self._reranker_cross_section_deboost,
                    deboost_count=deboost_count,
                    total_candidates=len(reranked_chunks),
                )
            rerank_latency_ms = int((time.perf_counter() - rerank_start) * 1000)
            chunks = [
                RetrievedChunk(score=r.rerank_score, fields=r.fields)
                for r in reranked_chunks
            ]
            # W40 F2 — truncate to original top_k (overfetch only helps deboost see
            # wider pool; final result must respect caller's top_k contract per
            # RetrievalResult.chunks invariant). No-op when rerank_top_k == top_k.
            chunks = chunks[:top_k]
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
            rerank_top_k=rerank_top_k,
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
        *,
        use_marked: bool = False,
        user_principals: list[str] | None = None,
    ):
        """Wrap top-K reranked chunks with prev/next neighbor context per ADR-0020.

        Delegates to generation.context_expander.expand_context using the engine's
        searcher (encapsulation preserved — caller doesn't need direct searcher access).
        `use_marked` (W70 / ADR-0055) passes through to assemble the marked variant.
        Returns (list[ExpandedChunk], ExpansionStats) — see context_expander.py for shape.
        """
        # Local import avoids circular dependency: context_expander imports from
        # retrieval.retrieval_engine for RetrievedChunk; engine→expander would cycle.
        from generation.context_expander import expand_context  # noqa: PLC0415

        return await expand_context(
            chunks,
            kb_id=kb_id,
            searcher=self._searcher,
            use_marked=use_marked,
            user_principals=user_principals,
        )

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
        use_marked: bool = False,
        user_principals: list[str] | None = None,
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
            use_marked=use_marked,
            user_principals=user_principals,
        )

    async def list_documents(self, kb_id: str, max_chunks: int = 1000) -> list[dict]:
        """W16 F5.1.1 — delegate to searcher.list_documents (encapsulation preserved).

        Returns aggregated doc-level metadata for kb_id-scoped chunks. See
        HybridSearcher.list_documents for shape + Beta-scale assumptions.
        """
        return await self._searcher.list_documents(kb_id, max_chunks=max_chunks)

    async def list_chunks(
        self,
        kb_id: str,
        doc_id: str,
        top: int = 1000,
        user_principals: list[str] | None = None,
    ) -> list[dict]:
        """W16 F5.1.2 — delegate to searcher.list_chunks (encapsulation preserved).

        Returns chunk-level metadata for kb_id+doc_id-scoped chunks ordered by
        chunk_index. See HybridSearcher.list_chunks for shape. `user_principals`
        (W90 P2.2) threads ACL trimming for the citation-expansion query path; None
        (GET listing routes) = no ACL filter.
        """
        return await self._searcher.list_chunks(
            kb_id, doc_id, top=top, user_principals=user_principals
        )

    async def fetch_by_chunk_ids(
        self,
        chunk_ids: list[str],
        kb_id: str,
        user_principals: list[str] | None = None,
    ) -> dict[str, dict]:
        """W52 — delegate to searcher.fetch_by_chunk_ids (encapsulation preserved).

        Batch-fetch chunks by id (no ranking) returning FULL fields incl.
        chunk_text — used by the synthetic-QA recall harness to read sampled
        chunks' text (list_chunks omits chunk_text by design for the Beta client).
        See HybridSearcher.fetch_by_chunk_ids for shape + ADR-0020/ADR-0018 notes.
        `user_principals` (W90 P2.2) threads ACL trimming; None = no ACL filter.
        """
        return await self._searcher.fetch_by_chunk_ids(
            chunk_ids, kb_id, user_principals=user_principals
        )
