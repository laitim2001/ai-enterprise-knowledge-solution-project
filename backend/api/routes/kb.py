"""Knowledge Base management endpoints (per architecture.md §4.4 #4-8 + §3.4)."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from api.schemas.kb import KbConfig, KbCreate, KbStatus
from kb_management import KBAlreadyExistsError, KBNotFoundError, KBService, get_kb_service

router = APIRouter()

KbServiceDep = Annotated[KBService, Depends(get_kb_service)]


@router.get("/kb", response_model=list[KbStatus])
async def list_kbs(service: KbServiceDep) -> list[KbStatus]:
    """List all KBs (architecture.md §4.4 #4 + §3.4 multi-KB)."""
    return await service.list_all()


@router.post("/kb", response_model=KbStatus, status_code=status.HTTP_201_CREATED)
async def create_kb(payload: KbCreate, service: KbServiceDep) -> KbStatus:
    """Create KB (architecture.md §4.4 #5; first KB = drive_user_manuals)."""
    try:
        return await service.create(payload)
    except KBAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.get("/kb/{kb_id}", response_model=KbStatus)
async def get_kb(kb_id: str, service: KbServiceDep) -> KbStatus:
    """KB detail + stats (architecture.md §4.4 #6)."""
    try:
        return await service.get(kb_id)
    except KBNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.delete("/kb/{kb_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_kb(kb_id: str, service: KbServiceDep) -> None:
    """Delete KB + cleanup (architecture.md §4.4 #7).

    W1: in-memory backend — purges only the KB record.
    W2 D1: Azure AI Search backend — cleanup will also drop the index
    `ekp-kb-{kb_id}-v{version}` and the per-KB Blob container.
    """
    try:
        await service.delete(kb_id)
    except KBNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.patch("/kb/{kb_id}/settings", response_model=KbConfig)
async def update_kb_settings(kb_id: str, config: KbConfig, service: KbServiceDep) -> KbConfig:
    """Update KB config: embedding model, chunk strategy (architecture.md §4.4 #8).

    Treats the request body as a full replacement of `KbConfig` (all fields
    have defaults, so omitted fields are reset). Partial PATCH is W2+ if needed.
    """
    try:
        updated = await service.update_config(kb_id, config)
        return updated.config
    except KBNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
