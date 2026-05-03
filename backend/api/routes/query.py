"""Query endpoints (per architecture.md §4.4 #1-2).

W2 baseline: hybrid retrieval only (no rerank, no synthesis).
- POST /query → 200 with retrieved chunks + timings (synthesis answer = placeholder)
- POST /query/stream → still 501 until W3 synthesis lands

W3 will wire Cohere Rerank + GPT-5.5 synthesis + CRAG loop per architecture.md §3.1.
"""

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import StreamingResponse

from api.schemas.query import ChunkPreview, QueryRequest, QueryResponse
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
    """Main RAG query — W2 baseline returns retrieval-only result.

    Real synthesis + Cohere rerank + CRAG loop wired W3 per architecture.md §3.1.
    """
    engine = _engine_or_503(request)
    try:
        result = await engine.retrieve(
            query=payload.query,
            top_k=payload.top_k_retrieval,
        )
    except Exception as exc:  # noqa: BLE001 — surface as 502 for downstream Azure errors
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

    return QueryResponse(
        answer=_W2_PLACEHOLDER_ANSWER,
        citations=[],  # W3 — citation format with image refs
        retrieved_chunks=chunk_previews,
        crag_triggered=False,
        crag_iterations=0,
        latency_ms=result.total_latency_ms,
        trace_id="",  # W3 — Langfuse trace id
        model_used="(retrieval-only)",
        reranker_used="off",
        refused=False,
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
