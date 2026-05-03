"""Query endpoints (per architecture.md §4.4 #1-2).

W3+ implementation per architecture.md §3.1 (L2 CRAG pipeline).
"""

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse

from api.schemas.query import QueryRequest, QueryResponse

router = APIRouter()


@router.post("/query", response_model=QueryResponse)
async def query(payload: QueryRequest) -> QueryResponse:
    """Main RAG query.

    W1 stub: route registered, returns 501.
    Real impl W3 per architecture.md §3.1 (Hybrid retrieval + Cohere rerank + GPT-5.5 + CRAG).
    """
    _ = payload
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="W3 implementation per architecture.md §3.1",
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
