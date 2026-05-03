"""Chunk management endpoints (per architecture.md §4.4 #13-14 + §3.5)."""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

router = APIRouter()


class ChunkPatch(BaseModel):
    """Per architecture.md §3.5 — Admin Console can disable chunk without re-ingest."""

    enabled: bool | None = None
    chunk_title: str | None = None


@router.get("/kb/{kb_id}/documents/{doc_id}/chunks")
async def list_chunks(kb_id: str, doc_id: str) -> list[dict]:
    """List chunks of a doc (W2 implementation)."""
    _ = kb_id, doc_id
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="W2 implementation per architecture.md §3.5",
    )


@router.patch("/kb/{kb_id}/chunks/{chunk_id}")
async def patch_chunk(kb_id: str, chunk_id: str, payload: ChunkPatch) -> dict:
    """Toggle chunk enabled / edit metadata (W2 implementation, F13 acceptance)."""
    _ = kb_id, chunk_id, payload
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="W2 implementation per architecture.md §3.5 + §7.1 F13",
    )
