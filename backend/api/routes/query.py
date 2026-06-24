"""Query endpoints (per architecture.md §4.4 #1-2).

W3 D2: full RAG pipeline wired
- Hybrid retrieval (W2)
- Optional Cohere Rerank (W3 D1 scaffold + W3 D2 wire)
- GPT-5.5 synthesis with citation parsing (W3 D2 F2)
- Citation enrichment with embedded images (W3 D2 F3)

If synthesizer is None (missing OpenAI deps), endpoint falls back to
retrieval-only response with a placeholder answer (W2 behavior preserved
for tests / local dev). SSE /query/stream remains 501 — F4 W3 D3 scope.
"""

import asyncio
import json
from collections.abc import Awaitable, Callable
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse

from api.auth.dependency import get_current_user
from api.auth.models import AuthenticatedUser
from api.middleware.acl import assert_kb_access
from api.routes.documents import screenshot_proxy_url
from api.schemas.kb import KbConfig
from api.schemas.query import ChunkPreview, Citation, QueryRequest, QueryResponse
from generation.citation_enrichment import build_citations, cap_images_per_answer
from generation.citation_image_neighbors import (
    attach_neighbour_images,
    pin_chapter_overview_images,
)
from generation.crag import CragLoop
from generation.effective_config import (
    EffectiveConfig,
    PerQueryOverrides,
    resolve_effective_config,
)
from generation.query_reformulator import QueryReformulator
from generation.section_anchor_markers import inject_section_anchored_markers
from generation.stream_composer import compose_query_stream
from generation.synthesizer import Synthesizer
from kb_management.doc_config_store import DocConfigStore
from kb_management.service import KBService, get_kb_service
from kb_management.storage import KBNotFoundError
from observability.observe import observe_async, observe_streaming
from retrieval.result_fusion import fused_retrieve
from retrieval.retrieval_engine import RetrievalEngine, RetrievalResult
from storage.settings import Settings, get_settings

logger = structlog.get_logger(__name__)

router = APIRouter()

KbServiceDep = Annotated[KBService, Depends(get_kb_service)]


# W57 / ADR-0050 — given the dominant cited doc_id, return the per-request
# `EffectiveConfig` with that doc's per-doc config overlaid (or the base config
# unchanged). Built per request by `_make_doc_overlay`; consumed by
# `execute_query_pipeline` + the stream path after retrieval.
DocOverlayResolver = Callable[[str | None], Awaitable[EffectiveConfig]]


async def _get_kb_config(service: KBService, kb_id: str) -> KbConfig | None:
    """Fetch the per-KB `KbConfig`; ``None`` when the KB has no metadata row
    (a query against an index with no KB record → global-default config, pre-W43
    back-compat)."""
    try:
        return (await service.get(kb_id)).config
    except KBNotFoundError:
        return None


def _doc_config_store(request: Request) -> DocConfigStore | None:
    """W57 — the per-doc config store wired on app.state (None in tests / when the
    server didn't wire it → no per-doc overlay, behaves as per-KB)."""
    return getattr(request.app.state, "doc_config_store", None)


def _dominant_doc_id(chunks: list) -> str | None:
    """ADR-0050 — the ``doc_id`` appearing most across the reranked chunk set.

    Ties resolve to the highest-ranked doc: chunks arrive rank-ordered (best first),
    and Python's ``max`` returns the first key reaching the max while dict iteration
    preserves insertion (== rank) order. ``None`` when no chunk carries a doc_id.
    """
    counts: dict[str, int] = {}
    for c in chunks:
        fields = getattr(c, "fields", None)
        doc_id = str(fields.get("doc_id", "")) if isinstance(fields, dict) else ""
        if doc_id:
            counts[doc_id] = counts.get(doc_id, 0) + 1
    if not counts:
        return None
    return max(counts, key=lambda d: counts[d])


def _make_doc_overlay(
    *,
    base: EffectiveConfig,
    settings: Settings,
    kb_config: KbConfig | None,
    per_query: PerQueryOverrides,
    store: DocConfigStore | None,
    kb_id: str,
) -> DocOverlayResolver | None:
    """W57 / ADR-0050 — build the per-document config overlay for a request.

    Returns ``None`` (no overlay → pipeline keeps the per-KB ``base``) when no store
    is wired. Otherwise a callback that, given the dominant cited doc_id, re-resolves
    the full chain with that doc's `DocConfig` inserted (per-query > per-DOC > per-KB
    > global). When the dominant doc has NO per-doc config it returns ``base``
    unchanged — so an answer over un-configured docs is bit-identical to pre-W57.
    """
    if store is None:
        return None

    async def _overlay(dominant_doc_id: str | None) -> EffectiveConfig:
        if not dominant_doc_id:
            return base
        doc_config = await store.get(kb_id, dominant_doc_id)
        if doc_config is None:
            return base
        return resolve_effective_config(settings, kb_config, per_query, doc_config)

    return _overlay


async def _resolve_effective_config(
    service: KBService,
    settings: Settings,
    kb_id: str,
    per_query: PerQueryOverrides | None = None,
) -> EffectiveConfig:
    """W43 F1.3 (ADR-0040) — resolve the per-request retrieval / citation config.

    Fetches the per-KB `KbConfig` and resolves it against the global `Settings`
    (per-query > per-KB > global). A missing KB record (`KBNotFoundError` — e.g. a
    query against an index that has no KB metadata row) falls back to the global
    defaults, so the request behaves exactly as pre-W43 (G7 back-compat).

    CH-007 — `per_query` carries the request's explicit top_k overrides (the eval
    harness / tests that DO send `top_k_*`); when `None` (the chat path), the KB's
    `default_top_k` / `default_rerank_k` win, which is the whole point of this change.
    """
    kb_config = await _get_kb_config(service, kb_id)
    return resolve_effective_config(settings, kb_config, per_query)


def _per_query_from_payload(payload: QueryRequest) -> PerQueryOverrides:
    """CH-007 — fold the request's explicit top_k fields into a `PerQueryOverrides`
    so the resolver treats them as the highest-priority override. Both fields are
    `None` for the chat path (which sends neither), letting the per-KB
    `default_top_k` / `default_rerank_k` win.
    """
    return PerQueryOverrides(
        default_top_k=payload.top_k_retrieval,
        default_rerank_k=payload.top_k_rerank,
    )


_W2_PLACEHOLDER_ANSWER = (
    "[W2 baseline: retrieval-only response; synthesis answer wired W3 per "
    "architecture.md §3.1 CRAG pipeline]"
)


def _proxy_citation_images(
    citations: list[Citation],
    request: Request,
    kb_id: str,
) -> list[Citation]:
    """BUG-010 — rewrite citation `embedded_images` blob URLs to the screenshot
    proxy route. The screenshot container is private; a chat-surface `<img>`
    can't read the blob directly, so URLs go through the API proxy.
    """
    proxied: list[Citation] = []
    for citation in citations:
        images = [
            image.model_copy(
                update={"blob_url": screenshot_proxy_url(request, kb_id, image.blob_url)},
            )
            if image.blob_url
            else image
            for image in citation.embedded_images
        ]
        proxied.append(citation.model_copy(update={"embedded_images": images}))
    return proxied


def _engine_or_503(request: Request) -> RetrievalEngine:
    engine = getattr(request.app.state, "retrieval_engine", None)
    if engine is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "RetrievalEngine not initialized — check Azure OpenAI + AI Search "
                ".env config (Q3 + Q4 dependencies)."
            ),
        )
    return engine


@router.post("/query", response_model=QueryResponse)
@observe_async(
    name="api.query",
    capture_attrs=(
        "latency_ms",
        "model_used",
        "reranker_used",
        "refused",
        "crag_triggered",
        "crag_iterations",
    ),
)
async def query(
    payload: QueryRequest,
    request: Request,
    service: KbServiceDep,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
) -> QueryResponse:
    """Main RAG query — hybrid → (rerank) → synthesis → citations.

    W9 D4 F5.2 cont — top-level @observe_async wraps the orchestration;
    nested observe_llm_async on synthesizer/crag stages produce a single
    hierarchical Langfuse trace per request when client wired (W11+).

    W43 F1.3 (ADR-0040) — per-KB tunable config is resolved at entry
    (`effective`) and threaded through the pipeline. The pipeline body lives in
    `execute_query_pipeline` (shared with the W43 F2 config-test harness so the
    harness runs the IDENTICAL pipeline).
    """
    # W90 P2.0 (ADR-0066 G1) — KB-level query authorization. kb_id is in the body,
    # so require_kb_acl (path-based) can't gate this; assert_kb_access does.
    await assert_kb_access(request, payload.kb_id, current_user, "query")
    settings = get_settings()
    kb_config = await _get_kb_config(service, payload.kb_id)
    per_query = _per_query_from_payload(payload)
    effective = resolve_effective_config(settings, kb_config, per_query)
    # W57 / ADR-0050 — per-document config overlay (no-op when no store / no per-doc
    # config for the dominant cited doc).
    overlay = _make_doc_overlay(
        base=effective,
        settings=settings,
        kb_config=kb_config,
        per_query=per_query,
        store=_doc_config_store(request),
        kb_id=payload.kb_id,
    )
    return await execute_query_pipeline(
        payload,
        request,
        effective,
        settings,
        doc_overlay=overlay,
    )


async def execute_query_pipeline(
    payload: QueryRequest,
    request: Request,
    effective: EffectiveConfig,
    settings: Settings,
    doc_overlay: DocOverlayResolver | None = None,
) -> QueryResponse:
    """W43 F2 — the shared `/query` full pipeline (retrieve → context-expand →
    parent-doc → synth → CRAG → citations → neighbour-images → image-cap),
    parameterised by a resolved `EffectiveConfig`.

    Both `/query` (saved per-KB config) and the config-test harness
    (`POST /kb/{kb_id}/config-test`, draft config) call this — so the harness
    measures the IDENTICAL pipeline a real query runs (F2.6 trust requirement).

    W57 / ADR-0050 — `doc_overlay` (when supplied by `/query`) re-resolves the
    post-retrieval knobs using the dominant cited doc's per-doc config, applied
    AFTER retrieval (the retrieval-entry knobs in `effective` already drove the
    fetch). `None` (config-test / tests) → no overlay, behaves as the passed config.
    """
    engine = _engine_or_503(request)
    synthesizer: Synthesizer | None = getattr(request.app.state, "synthesizer", None)
    reformulator: QueryReformulator | None = getattr(
        request.app.state,
        "query_reformulator",
        None,
    )

    try:
        # W25 F3 D4 — ADR-0034 RAG-fusion branch.
        # When `enable_query_expansion=True` AND the reformulator is wired
        # (Azure OpenAI creds present), reformulate to N variants + parallel
        # retrieve + RRF fuse. Otherwise preserve the original single-query
        # path bit-identical (Tier 1 backward-compat baseline).
        if settings.enable_query_expansion and reformulator is not None:
            reform = await reformulator.reformulate(payload.query)
            fused = await fused_retrieve(
                variants=reform.variants,
                kb_id=payload.kb_id,
                # CH-007 — per-KB rerank depth + overfetch (resolved EffectiveConfig).
                top_k=effective.default_rerank_k,
                engine=engine,
                rrf_k=settings.query_expansion_rrf_k,
                per_variant_overfetch=settings.query_expansion_per_variant_overfetch,
                mode=payload.mode,  # W39 F2 — propagate Path A additive mode field
                overfetch=effective.default_top_k,
            )
            result: RetrievalResult = fused.as_retrieval_result()
            logger.info(
                "query_expansion_used",
                variant_count=fused.variant_count,
                fallback_used=reform.fallback_used,
                fusion_latency_ms=fused.fusion_latency_ms,
                total_latency_ms=fused.total_latency_ms,
            )
        else:
            result = await engine.retrieve(
                query=payload.query,
                kb_id=payload.kb_id,
                # CH-007 — per-KB rerank depth + overfetch (resolved EffectiveConfig).
                top_k=effective.default_rerank_k,
                overfetch=effective.default_top_k,
                mode=payload.mode,  # W39 F2 — propagate Path A additive mode field
            )
    except Exception as exc:  # noqa: BLE001 — surface downstream Azure errors as 502
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"retrieval failure: {type(exc).__name__}: {exc}",
        ) from exc

    # W57 / ADR-0050 — per-document config overlay. Now that retrieval is done we
    # know the cited docs; re-resolve the post-retrieval knobs using the dominant
    # doc's per-doc config (no-op when no overlay / no per-doc config).
    if doc_overlay is not None:
        effective = await doc_overlay(_dominant_doc_id(result.chunks))

    chunk_previews = [
        ChunkPreview(
            chunk_id=str(c.fields.get("chunk_id", "")),
            chunk_title=str(c.fields.get("chunk_title", "")),
            chunk_text=str(c.fields.get("chunk_text", "")),
            relevance_score=c.score,
        )
        for c in result.chunks
    ]
    reranker_used = "cohere-v4.0-pro" if result.reranked else "off"  # ADR-0012 production lock

    if synthesizer is None:
        # Retrieval-only fallback (W2 baseline behavior preserved).
        return QueryResponse(
            answer=_W2_PLACEHOLDER_ANSWER,
            citations=[],
            retrieved_chunks=chunk_previews,
            crag_triggered=False,
            crag_iterations=0,
            latency_ms=result.total_latency_ms,
            trace_id="",
            model_used="(retrieval-only)",
            reranker_used=reranker_used,
            refused=False,
        )

    # ADR-0020 Context Expander: wrap top-K with prev/next neighbor text before synthesis.
    # Synthesizer.synthesize() accepts ExpandedChunk via duck-type (same score+fields shape);
    # prompt_builder reads fields['expanded_text'] if present, else falls back to chunk_text.
    # W70 / ADR-0055 — use_marked threads the inline-image-markers knob so the
    # expanded/parent text variants carry [IMG#sha8] markers when the knob is on.
    try:
        expanded_chunks, _expansion_stats = await engine.expand_context_for_chunks(
            result.chunks,
            kb_id=payload.kb_id,
            use_marked=effective.enable_inline_image_markers,
        )
    except Exception as exc:  # noqa: BLE001 — graceful degradation per ADR-0020
        logger.warning(
            "context_expansion_failed_using_raw",
            error=f"{type(exc).__name__}: {exc}",
        )
        expanded_chunks = result.chunks  # fallback: no expansion (raw chunks)

    # ADR-0037 W26 F2: parent-document retrieval (flag-gated default OFF per Q4).
    # Layered over ADR-0020 Context Expander (Q6 Both on coexistence) — top-1 anchor's
    # parent section text supersedes its expanded_text via prompt_builder dispatch chain
    # (parent_section_text > expanded_text > chunk_text); top-2..top-K non-anchor chunks
    # pass through with expanded_text preserved. Graceful fallback on exception keeps
    # expanded_chunks intact (no degradation vs ADR-0020 baseline).
    if effective.enable_parent_doc_retrieval:
        try:
            expanded_chunks, _parent_stats = await engine.aggregate_parent_sections_for_chunks(
                expanded_chunks,
                kb_id=payload.kb_id,
                section_depth_offset=effective.parent_doc_section_depth_offset,
                parent_doc_top_k=effective.parent_doc_top_k,
                max_tokens_per_parent=effective.parent_doc_max_tokens_per_parent,
                max_chunks_per_parent=effective.parent_doc_max_chunks_per_parent,
                fallback_to_doc_on_shallow=effective.parent_doc_fallback_to_doc_on_shallow,
                use_marked=effective.enable_inline_image_markers,  # W70 / ADR-0055
            )
        except Exception as exc:  # noqa: BLE001 — graceful degradation per ADR-0037
            logger.warning(
                "parent_doc_aggregation_failed_using_expanded",
                error=f"{type(exc).__name__}: {exc}",
            )
            # expanded_chunks unchanged — fallback to Context Expander result

    try:
        # W32 F1.4.a — pass engine + kb_id to enable engine-fetch citation expansion
        # per (h') single-axis ship. Backward compat: synthesize() defaults engine=None,
        # kb_id=None → expansion no-op.
        # W43 F1.5 — effective_config carries the per-KB-resolved expansion knobs.
        synth = await synthesizer.synthesize(
            payload.query,
            expanded_chunks,
            engine=engine,
            kb_id=payload.kb_id,
            effective_config=effective,
            detail_level=effective.answer_detail,  # CH-006 per-KB answer detail
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"synthesis failure: {type(exc).__name__}: {exc}",
        ) from exc

    # W4 D1 F1: CRAG L2 correction loop (non-stream path only per architecture.md
    # §3.5; stream path is L3-only — token-by-token UX precludes mid-stream
    # rewrite). Skipped when crag_loop unset (test/local) OR caller disables.
    crag_loop: CragLoop | None = getattr(request.app.state, "crag_loop", None)
    crag_triggered = False
    crag_iterations = 0
    final_synth = synth
    final_chunks = result.chunks
    if crag_loop is not None and payload.enable_crag:
        outcome = await crag_loop.refine(
            payload.query,
            result,
            synth,
            kb_id=payload.kb_id,
            effective_config=effective,
        )
        crag_triggered = outcome.triggered
        crag_iterations = outcome.iterations
        final_synth = outcome.synthesis
        final_chunks = outcome.chunks
        if crag_triggered and not outcome.fallback_used:
            chunk_previews = [
                ChunkPreview(
                    chunk_id=str(c.fields.get("chunk_id", "")),
                    chunk_title=str(c.fields.get("chunk_title", "")),
                    chunk_text=str(c.fields.get("chunk_text", "")),
                    relevance_score=c.score,
                )
                for c in final_chunks
            ]

    # W32 F1.8 integration fix — extend final_chunks with W32 engine-fetched neighbor
    # chunks before build_citations to avoid Rule 5「hallucinated」filter dropping
    # post-hoc expansion citation_ids (per W32 F2 reload-v1 evidence — answer text
    # carried 3-6 markers but API response dropped 2-5 added citations per run when
    # build_citations restricted to top-K reranked set)。
    final_chunks_with_expanded = final_chunks + list(final_synth.expanded_neighbor_chunks)
    citations = build_citations(final_synth.citation_ids, final_chunks_with_expanded)

    # W25 F5 D1 — attach neighbour-chunk images per ADR-0034 §Implementation
    # Mapping. When the LLM cites an intro / meta chunk (eg. §8 "Integration
    # scenarios" intro) that itself has no images but adjacent walkthrough
    # chunks (§8.1-8.5) do, this surfaces those neighbour images on the
    # cited citation so the chat UI renders them. Default-on per Settings;
    # graceful fallback to original citations on exception.
    if effective.enable_citation_neighbour_images:
        try:
            citations = await attach_neighbour_images(
                citations,
                kb_id=payload.kb_id,
                engine=engine,
                max_aux_per_citation=effective.citation_neighbour_max_aux_images,
                neighbour_window=effective.citation_neighbour_window,
                section_path_prefix_depth=(effective.citation_neighbour_section_path_prefix_depth),
            )
        except Exception as exc:  # noqa: BLE001 — graceful degradation per ADR-0034 §Consequences
            logger.warning(
                "neighbour_images_attach_failed_using_original",
                error=f"{type(exc).__name__}: {exc}",
            )

    # CH-010 / ADR-0047 — pin the chapter §X.1 Overview figures to the lead citation
    # front BEFORE the cap, so a procedural answer leads with the overview/flow
    # diagram (the cap is citation-order; without the pin the far, low-relevance
    # overview images are starved). Graceful fallback to current citations on error.
    if effective.enable_chapter_overview_pin:
        try:
            citations = await pin_chapter_overview_images(
                citations,
                kb_id=payload.kb_id,
                engine=engine,
            )
        except Exception as exc:  # noqa: BLE001 — graceful degradation
            logger.warning(
                "chapter_overview_pin_failed_using_current",
                error=f"{type(exc).__name__}: {exc}",
            )

    # W43 F1.6 — per-KB blunt image cap (None = no backend cap, frontend caps display).
    citations = cap_images_per_answer(citations, effective.max_images_per_answer)
    citations = _proxy_citation_images(citations, request, payload.kb_id)

    # W75 / ADR-0056 段②d — section-anchored aux image injection（方案 A）. Gated;
    # graceful fallback to the un-injected answer on error (per ADR-0034 §Consequences).
    answer_text = final_synth.answer
    if effective.enable_section_anchored_aux_images:
        try:
            answer_text = inject_section_anchored_markers(
                answer_text,
                citations,
                max_per_anchor=effective.section_anchor_max_per_anchor,
            )
        except Exception as exc:  # noqa: BLE001 — graceful degradation
            logger.warning(
                "section_anchor_inject_failed_using_original",
                error=f"{type(exc).__name__}: {exc}",
            )

    return QueryResponse(
        answer=answer_text,
        citations=citations,
        retrieved_chunks=chunk_previews,
        crag_triggered=crag_triggered,
        crag_iterations=crag_iterations,
        latency_ms=result.total_latency_ms + final_synth.latency_ms,
        trace_id="",  # W3 — Langfuse trace id
        model_used=final_synth.deployment,
        reranker_used=reranker_used,
        refused=final_synth.refused,
    )


@router.post("/query/stream")
async def query_stream(
    payload: QueryRequest,
    request: Request,
    service: KbServiceDep,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
) -> StreamingResponse:
    """SSE streaming variant of /query (W3 D3 F4).

    Vercel AI SDK SSE protocol — `data: {json}\\n\\n` event frames:
        {"type":"text-delta","content":str}  during streaming
        {"type":"citation","citation":{...}}  one per cited chunk
        {"type":"done","model","cost","latency_ms","refused","reranker_used"}  final

    W43 F1.4 (ADR-0040) — per-KB tunable config resolved at entry (`effective`)
    and threaded through the same wire points as `/query`.
    """
    # W90 P2.0 (ADR-0066 G1) — KB-level query authorization (kb_id in body).
    await assert_kb_access(request, payload.kb_id, current_user, "query")
    engine = _engine_or_503(request)
    synthesizer: Synthesizer | None = getattr(request.app.state, "synthesizer", None)
    if synthesizer is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Synthesizer not initialized — check Azure OpenAI .env config (Q4 dependency)."
            ),
        )

    settings = get_settings()
    kb_config = await _get_kb_config(service, payload.kb_id)
    per_query = _per_query_from_payload(payload)
    effective = resolve_effective_config(settings, kb_config, per_query)
    # W57 / ADR-0050 — per-document overlay built here, applied after retrieval below.
    overlay = _make_doc_overlay(
        base=effective,
        settings=settings,
        kb_config=kb_config,
        per_query=per_query,
        store=_doc_config_store(request),
        kb_id=payload.kb_id,
    )

    try:
        result = await engine.retrieve(
            query=payload.query,
            kb_id=payload.kb_id,
            # CH-007 — rerank depth + overfetch from the resolved per-KB config
            # (per-query override > per-KB default > global). The chat path sends
            # neither top_k field, so the KB's saved values take effect here.
            top_k=effective.default_rerank_k,
            overfetch=effective.default_top_k,
            mode=payload.mode,  # W39 F2 — propagate Path A additive mode field
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"retrieval failure: {type(exc).__name__}: {exc}",
        ) from exc

    # W57 / ADR-0050 — re-resolve post-retrieval knobs via the dominant cited doc's
    # per-doc config. Reassigns `effective` BEFORE synth + the citation-augment
    # closure (both read this `effective`), so the stream honours per-doc config.
    if overlay is not None:
        effective = await overlay(_dominant_doc_id(result.chunks))

    # ADR-0020 Context Expander parallel to /query happy path (graceful degradation).
    # W70 / ADR-0055 — use_marked threading parallel to the non-stream path.
    try:
        expanded_chunks, _expansion_stats = await engine.expand_context_for_chunks(
            result.chunks,
            kb_id=payload.kb_id,
            use_marked=effective.enable_inline_image_markers,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "context_expansion_stream_failed_using_raw",
            error=f"{type(exc).__name__}: {exc}",
        )
        expanded_chunks = result.chunks

    # ADR-0037 W26 F2: parent-document retrieval parallel to /query happy path
    # (flag-gated default OFF per Q4; graceful fallback on exception keeps
    # expanded_chunks intact — no degradation vs ADR-0020 baseline).
    # W43 F1.4 — reads the per-request `effective` config (resolved at entry).
    if effective.enable_parent_doc_retrieval:
        try:
            expanded_chunks, _parent_stats = await engine.aggregate_parent_sections_for_chunks(
                expanded_chunks,
                kb_id=payload.kb_id,
                section_depth_offset=effective.parent_doc_section_depth_offset,
                parent_doc_top_k=effective.parent_doc_top_k,
                max_tokens_per_parent=effective.parent_doc_max_tokens_per_parent,
                max_chunks_per_parent=effective.parent_doc_max_chunks_per_parent,
                fallback_to_doc_on_shallow=effective.parent_doc_fallback_to_doc_on_shallow,
                use_marked=effective.enable_inline_image_markers,  # W70 / ADR-0055
            )
        except Exception as exc:  # noqa: BLE001 — graceful degradation per ADR-0037
            logger.warning(
                "parent_doc_aggregation_stream_failed_using_expanded",
                error=f"{type(exc).__name__}: {exc}",
            )

    # W25 F5 D1 — neighbour-image augmentation callback for the stream's
    # citation batch (see compose_query_stream's citation_post_process hook).
    # Graceful fallback to original citations on exception per ADR-0034.

    async def _augment_stream_citations(citations: list[Citation]) -> list[Citation]:
        augmented = citations
        if effective.enable_citation_neighbour_images:
            try:
                augmented = await attach_neighbour_images(
                    citations,
                    kb_id=payload.kb_id,
                    engine=engine,
                    max_aux_per_citation=effective.citation_neighbour_max_aux_images,
                    neighbour_window=effective.citation_neighbour_window,
                    section_path_prefix_depth=(
                        effective.citation_neighbour_section_path_prefix_depth
                    ),
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "stream_neighbour_images_attach_failed_using_original",
                    error=f"{type(exc).__name__}: {exc}",
                )
                augmented = citations
        # CH-010 / ADR-0047 — pin chapter §X.1 Overview figures to lead-citation
        # front before the cap (parallel to /query path).
        if effective.enable_chapter_overview_pin:
            try:
                augmented = await pin_chapter_overview_images(
                    augmented,
                    kb_id=payload.kb_id,
                    engine=engine,
                )
            except Exception as exc:  # noqa: BLE001 — graceful degradation
                logger.warning(
                    "stream_chapter_overview_pin_failed_using_current",
                    error=f"{type(exc).__name__}: {exc}",
                )
        # W43 F1.6 — per-KB blunt image cap (parallel to /query path).
        return cap_images_per_answer(augmented, effective.max_images_per_answer)

    def _inject_stream_answer(answer: str, citations: list[Citation]) -> str:
        # W75 / ADR-0056 段②d — section-anchored aux image injection（方案 A）on the
        # done frame's canonical answer (the frontend replaces the streamed text with
        # it per BUG-028 ②, so injected markers render inline with no frontend change).
        # Gated; graceful fallback to the un-injected answer on error.
        if not effective.enable_section_anchored_aux_images:
            return answer
        try:
            return inject_section_anchored_markers(
                answer,
                citations,
                max_per_anchor=effective.section_anchor_max_per_anchor,
            )
        except Exception as exc:  # noqa: BLE001 — graceful degradation
            logger.warning(
                "stream_section_anchor_inject_failed_using_original",
                error=f"{type(exc).__name__}: {exc}",
            )
            return answer

    async def event_serializer():
        # W10 D1 F4.1 — observe_streaming wraps compose_query_stream so the
        # terminal `done` frame's model + token counts flow to Langfuse
        # generation event(closes W9 D4 SSE flow capture carry-over)。
        # Cancellation mid-stream still emits a generation event with
        # status=cancelled so partial-spend cost attribution stays accurate。
        try:
            # W32 F1.4.b — pass engine + kb_id to enable engine-fetch citation expansion
            # in stream path (final `result` event carries expanded values).
            synth_stream = synthesizer.synthesize_stream(
                payload.query,
                expanded_chunks,
                engine=engine,
                kb_id=payload.kb_id,
                effective_config=effective,
                detail_level=effective.answer_detail,  # CH-006 per-KB answer detail
            )
            observed = observe_streaming(
                compose_query_stream(
                    result,
                    synth_stream,
                    citation_post_process=_augment_stream_citations,
                    answer_post_process=_inject_stream_answer,
                ),
                name="api.query.stream",
                extra_metadata_fields=("refused", "reranker_used"),
            )
            async for event in observed:
                # BUG-010 — rewrite citation image URLs to the screenshot proxy
                # route (private blob → browser <img> can't read it directly).
                if event.get("type") == "citation":
                    for image in event.get("citation", {}).get("embedded_images", []):
                        if isinstance(image, dict) and image.get("blob_url"):
                            image["blob_url"] = screenshot_proxy_url(
                                request,
                                payload.kb_id,
                                image["blob_url"],
                            )
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        except asyncio.CancelledError:
            logger.info("query_stream_cancelled", query_chars=len(payload.query))
            raise

    return StreamingResponse(event_serializer(), media_type="text/event-stream")
