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

import structlog
from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import StreamingResponse

from api.routes.documents import screenshot_proxy_url
from api.schemas.query import ChunkPreview, Citation, QueryRequest, QueryResponse
from generation.citation_enrichment import build_citations
from generation.citation_image_neighbors import attach_neighbour_images
from generation.crag import CragLoop
from generation.query_reformulator import QueryReformulator
from generation.stream_composer import compose_query_stream
from generation.synthesizer import Synthesizer
from observability.observe import observe_async, observe_streaming
from retrieval.result_fusion import fused_retrieve
from retrieval.retrieval_engine import RetrievalEngine, RetrievalResult
from storage.settings import get_settings

logger = structlog.get_logger(__name__)

router = APIRouter()

_W2_PLACEHOLDER_ANSWER = (
    "[W2 baseline: retrieval-only response; synthesis answer wired W3 per "
    "architecture.md §3.1 CRAG pipeline]"
)


def _proxy_citation_images(
    citations: list[Citation], request: Request, kb_id: str,
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
async def query(payload: QueryRequest, request: Request) -> QueryResponse:
    """Main RAG query — hybrid → (rerank) → synthesis → citations.

    W9 D4 F5.2 cont — top-level @observe_async wraps the orchestration;
    nested observe_llm_async on synthesizer/crag stages produce a single
    hierarchical Langfuse trace per request when client wired (W11+).
    """
    engine = _engine_or_503(request)
    synthesizer: Synthesizer | None = getattr(request.app.state, "synthesizer", None)
    settings = get_settings()
    reformulator: QueryReformulator | None = getattr(
        request.app.state, "query_reformulator", None,
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
                top_k=payload.top_k_rerank,
                engine=engine,
                rrf_k=settings.query_expansion_rrf_k,
                per_variant_overfetch=settings.query_expansion_per_variant_overfetch,
                mode=payload.mode,  # W39 F2 — propagate Path A additive mode field
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
                top_k=payload.top_k_rerank,
                mode=payload.mode,  # W39 F2 — propagate Path A additive mode field
            )
    except Exception as exc:  # noqa: BLE001 — surface downstream Azure errors as 502
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"retrieval failure: {type(exc).__name__}: {exc}",
        ) from exc

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
    try:
        expanded_chunks, _expansion_stats = await engine.expand_context_for_chunks(
            result.chunks, kb_id=payload.kb_id,
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
    if settings.enable_parent_doc_retrieval:
        try:
            expanded_chunks, _parent_stats = await engine.aggregate_parent_sections_for_chunks(
                expanded_chunks,
                kb_id=payload.kb_id,
                section_depth_offset=settings.parent_doc_section_depth_offset,
                parent_doc_top_k=settings.parent_doc_top_k,
                max_tokens_per_parent=settings.parent_doc_max_tokens_per_parent,
                max_chunks_per_parent=settings.parent_doc_max_chunks_per_parent,
                fallback_to_doc_on_shallow=settings.parent_doc_fallback_to_doc_on_shallow,
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
        synth = await synthesizer.synthesize(
            payload.query, expanded_chunks, engine=engine, kb_id=payload.kb_id,
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
        outcome = await crag_loop.refine(payload.query, result, synth, kb_id=payload.kb_id)
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
    if settings.enable_citation_neighbour_images:
        try:
            citations = await attach_neighbour_images(
                citations,
                kb_id=payload.kb_id,
                engine=engine,
                max_aux_per_citation=settings.citation_neighbour_max_aux_images,
                neighbour_window=settings.citation_neighbour_window,
                section_path_prefix_depth=(
                    settings.citation_neighbour_section_path_prefix_depth
                ),
            )
        except Exception as exc:  # noqa: BLE001 — graceful degradation per ADR-0034 §Consequences
            logger.warning(
                "neighbour_images_attach_failed_using_original",
                error=f"{type(exc).__name__}: {exc}",
            )

    citations = _proxy_citation_images(citations, request, payload.kb_id)

    return QueryResponse(
        answer=final_synth.answer,
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
async def query_stream(payload: QueryRequest, request: Request) -> StreamingResponse:
    """SSE streaming variant of /query (W3 D3 F4).

    Vercel AI SDK SSE protocol — `data: {json}\\n\\n` event frames:
        {"type":"text-delta","content":str}  during streaming
        {"type":"citation","citation":{...}}  one per cited chunk
        {"type":"done","model","cost","latency_ms","refused","reranker_used"}  final
    """
    engine = _engine_or_503(request)
    synthesizer: Synthesizer | None = getattr(request.app.state, "synthesizer", None)
    if synthesizer is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Synthesizer not initialized — check Azure OpenAI .env config "
                "(Q4 dependency)."
            ),
        )

    try:
        result = await engine.retrieve(
            query=payload.query,
            kb_id=payload.kb_id,
            top_k=payload.top_k_rerank,
            mode=payload.mode,  # W39 F2 — propagate Path A additive mode field
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"retrieval failure: {type(exc).__name__}: {exc}",
        ) from exc

    # ADR-0020 Context Expander parallel to /query happy path (graceful degradation).
    try:
        expanded_chunks, _expansion_stats = await engine.expand_context_for_chunks(
            result.chunks, kb_id=payload.kb_id,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "context_expansion_stream_failed_using_raw",
            error=f"{type(exc).__name__}: {exc}",
        )
        expanded_chunks = result.chunks

    # W25 F5 D1 / W26 F2 — settings used both by parent-doc gate below + by the
    # neighbour-image augmentation callback further down (moved earlier here so
    # the parent-doc block can read the flag without double-calling get_settings()).
    stream_settings = get_settings()

    # ADR-0037 W26 F2: parent-document retrieval parallel to /query happy path
    # (flag-gated default OFF per Q4; graceful fallback on exception keeps
    # expanded_chunks intact — no degradation vs ADR-0020 baseline).
    if stream_settings.enable_parent_doc_retrieval:
        try:
            expanded_chunks, _parent_stats = await engine.aggregate_parent_sections_for_chunks(
                expanded_chunks,
                kb_id=payload.kb_id,
                section_depth_offset=stream_settings.parent_doc_section_depth_offset,
                parent_doc_top_k=stream_settings.parent_doc_top_k,
                max_tokens_per_parent=stream_settings.parent_doc_max_tokens_per_parent,
                max_chunks_per_parent=stream_settings.parent_doc_max_chunks_per_parent,
                fallback_to_doc_on_shallow=stream_settings.parent_doc_fallback_to_doc_on_shallow,
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
        if not stream_settings.enable_citation_neighbour_images:
            return citations
        try:
            return await attach_neighbour_images(
                citations,
                kb_id=payload.kb_id,
                engine=engine,
                max_aux_per_citation=stream_settings.citation_neighbour_max_aux_images,
                neighbour_window=stream_settings.citation_neighbour_window,
                section_path_prefix_depth=(
                    stream_settings.citation_neighbour_section_path_prefix_depth
                ),
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "stream_neighbour_images_attach_failed_using_original",
                error=f"{type(exc).__name__}: {exc}",
            )
            return citations

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
                payload.query, expanded_chunks, engine=engine, kb_id=payload.kb_id,
            )
            observed = observe_streaming(
                compose_query_stream(
                    result,
                    synth_stream,
                    citation_post_process=_augment_stream_citations,
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
                                request, payload.kb_id, image["blob_url"],
                            )
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        except asyncio.CancelledError:
            logger.info("query_stream_cancelled", query_chars=len(payload.query))
            raise

    return StreamingResponse(event_serializer(), media_type="text/event-stream")
