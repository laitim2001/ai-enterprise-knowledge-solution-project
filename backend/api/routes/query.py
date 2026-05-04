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

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import StreamingResponse

from api.schemas.query import ChunkPreview, QueryRequest, QueryResponse
from generation.citation_enrichment import build_citations
from generation.synthesizer import Synthesizer
from retrieval.retrieval_engine import RetrievalEngine

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
async def query(payload: QueryRequest, request: Request) -> QueryResponse:
    """Main RAG query — hybrid → (rerank) → synthesis → citations."""
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

    citations = build_citations(synth.citation_ids, result.chunks)

    return QueryResponse(
        answer=synth.answer,
        citations=citations,
        retrieved_chunks=chunk_previews,
        crag_triggered=False,  # W4 CRAG loop
        crag_iterations=0,
        latency_ms=result.total_latency_ms + synth.latency_ms,
        trace_id="",  # W3 — Langfuse trace id
        model_used=synth.deployment,
        reranker_used=reranker_used,
        refused=synth.refused,
    )


@router.post("/query/stream")
async def query_stream(payload: QueryRequest) -> StreamingResponse:
    """SSE streaming variant of /query.

    W1 stub: 501. Real impl W3 with Vercel AI SDK SSE protocol.
    """
    _ = payload
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="W3 streaming implementation per architecture.md §3.1",
    )
