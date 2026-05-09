"""Knowledge Base management endpoints (per architecture.md §4.4 #4-8 + §3.4)."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from api.schemas.kb import KbConfig, KbCreate, KbMetadataPatch, KbStatus
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

    Current behavior: in-memory backend purges the KB record only.

    Per W16 F5.3 Decision B.1 (Beta hardening minimal — Azure cleanup defer
    Track A IT cred trigger):
    - In-memory delete cleanup preserved as Beta baseline (kb_management.storage)
    - Azure AI Search index drop `ekp-kb-{kb_id}-v{version}` — defer Track A
      W17+ candidate (requires admin-key + index-management permissions)
    - Per-KB Blob container drop — defer Track A W17+ candidate (requires
      storage-account-management permissions)

    Per architecture.md §3.4 multi-KB notes: W2 D1 Azure backend promise was
    documented but Beta-blocking on Track A IT cred populate event trigger
    (W11 retro CO16);real cleanup wiring deferred to W17+ housekeeping per
    W16 plan §3 PARTIAL PASS allowance.
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


@router.post("/kb/{kb_id}/reindex", status_code=status.HTTP_202_ACCEPTED)
async def reindex_kb(kb_id: str, service: KbServiceDep) -> dict:
    """W16 F5.3.1 — trigger reindex of all documents in KB (per-KB level).

    Distinct from `POST /kb/{kb_id}/documents/{doc_id}/reindex` which is per-doc.

    Current Tier 1 baseline: returns mock `task_id` for tracking; KBService
    side-effect = no-op stub (Beta minimal per Decision B.1 + W16 plan §3
    PARTIAL PASS). Real reindex trigger (Azure AI Search index rebuild + per-KB
    Blob container re-ingest cascade) deferred Track A IT cred trigger →
    W17+ housekeeping per architecture.md §3.4 multi-KB rebuild semantics.

    Returns 202 ACCEPTED + {"task_id", "status": "queued", "kb_id"}.
    """
    try:
        await service.get(kb_id)  # 404 guard before queueing
    except KBNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    task_id = f"reindex-{uuid.uuid4().hex[:12]}"
    return {
        "task_id": task_id,
        "status": "queued",
        "kb_id": kb_id,
        "note": "Beta baseline mock — real reindex trigger pending Track A IT cred (W17+)",
    }


@router.patch("/kb/{kb_id}", response_model=KbStatus)
async def update_kb_metadata(
    kb_id: str, patch: KbMetadataPatch, service: KbServiceDep,
) -> KbStatus:
    """W16 F5.2 CO_F3b — partial PATCH of KB name + description fields.

    Per Decision A.1 (separation of concern): this endpoint covers metadata
    only (name + description); KbConfig settings remain in
    `PATCH /kb/{kb_id}/settings`. All fields Optional — omitted = preserve
    existing value (true partial PATCH semantics).
    """
    try:
        return await service.update_metadata(
            kb_id, name=patch.name, description=patch.description,
        )
    except KBNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
