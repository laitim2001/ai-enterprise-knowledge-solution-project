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

from api.schemas.query import ChunkPreview, QueryRequest, QueryResponse
from generation.citation_enrichment import build_citations
from generation.crag import CragLoop
from generation.stream_composer import compose_query_stream
from generation.synthesizer import Synthesizer
from observability.observe import observe_async, observe_streaming
from retrieval.retrieval_engine import RetrievalEngine

logger = structlog.get_logger(__name__)

router = APIRouter()

_W2_PLACEHOLDER_ANSWER = (
    "[W2 baseline: retrieval-only response; synthesis answer wired W3 per "
    "architecture.md §3.1 CRAG pipeline]"
)


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

    try:
        result = await engine.retrieve(
            query=payload.query,
            top_k=payload.top_k_rerank,
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
    reranker_used = "cohere-v3.5" if result.reranked else "off"

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

    try:
        synth = await synthesizer.synthesize(payload.query, result.chunks)
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
        outcome = await crag_loop.refine(payload.query, result, synth)
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

    citations = build_citations(final_synth.citation_ids, final_chunks)

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
        {"type":"done","model","latency_ms","refused","reranker_used"}  final
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
            top_k=payload.top_k_rerank,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"retrieval failure: {type(exc).__name__}: {exc}",
        ) from exc

    async def event_serializer():
        # W10 D1 F4.1 — observe_streaming wraps compose_query_stream so the
        # terminal `done` frame's model + token counts flow to Langfuse
        # generation event(closes W9 D4 SSE flow capture carry-over)。
        # Cancellation mid-stream still emits a generation event with
        # status=cancelled so partial-spend cost attribution stays accurate。
        try:
            synth_stream = synthesizer.synthesize_stream(payload.query, result.chunks)
            observed = observe_streaming(
                compose_query_stream(result, synth_stream),
                name="api.query.stream",
                extra_metadata_fields=("refused", "reranker_used"),
            )
            async for event in observed:
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        except asyncio.CancelledError:
            logger.info("query_stream_cancelled", query_chars=len(payload.query))
            raise

    return StreamingResponse(event_serializer(), media_type="text/event-stream")
