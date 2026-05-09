"""Chunk management endpoints (per architecture.md §4.4 #13-14 + §3.5).

W16 F5.1.2 closure (CO_F3a):
    GET /kb/{kb_id}/documents/{doc_id}/chunks — replaced 501 stub with Azure
    AI Search query (kb_id + doc_id filter; ordered by chunk_index).

PATCH /kb/{kb_id}/chunks/{chunk_id} remains 501 stub pending W2 admin chunk
toggle implementation (architecture.md §3.5 + §7.1 F13;out of W16 F5 batch).
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from api.schemas.listing import ChunkSummary
from kb_management import KBNotFoundError, KBService, get_kb_service
from retrieval.retrieval_engine import RetrievalEngine

router = APIRouter()

KbServiceDep = Annotated[KBService, Depends(get_kb_service)]


class ChunkPatch(BaseModel):
    """Per architecture.md §3.5 — Admin Console can disable chunk without re-ingest."""

    enabled: bool | None = None
    chunk_title: str | None = None


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


async def _verify_kb_or_404(kb_id: str, service: KBService) -> None:
    try:
        await service.get(kb_id)
    except KBNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.get(
    "/kb/{kb_id}/documents/{doc_id}/chunks",
    response_model=list[ChunkSummary],
)
async def list_chunks(
    kb_id: str, doc_id: str, request: Request, service: KbServiceDep,
) -> list[ChunkSummary]:
    """W16 F5.1.2 — list chunks of a doc (kb_id + doc_id filter;
    ordered by chunk_index ascending).

    Verifies kb_id exists via KBService (404 if missing); doc_id non-existence
    returns empty list (consistent with Azure Search "no results" semantics —
    differentiating doc 404 vs empty doc requires extra index query, deferred).
    """
    await _verify_kb_or_404(kb_id, service)

    engine = _engine_or_503(request)
    try:
        rows = await engine.list_chunks(kb_id, doc_id)
    except Exception as exc:  # noqa: BLE001 — surface downstream Azure errors as 502
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"chunk listing failure: {type(exc).__name__}: {exc}",
        ) from exc

    return [ChunkSummary(**row) for row in rows]


@router.patch("/kb/{kb_id}/chunks/{chunk_id}")
async def patch_chunk(kb_id: str, chunk_id: str, payload: ChunkPatch) -> dict:
    """Toggle chunk enabled / edit metadata (W2 implementation, F13 acceptance)."""
    _ = kb_id, chunk_id, payload
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="W2 implementation per architecture.md §3.5 + §7.1 F13",
    )
