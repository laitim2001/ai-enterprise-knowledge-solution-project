"""Knowledge Base management endpoints (per architecture.md §4.4 #4-8 + §3.4).

CH-001 (2026-05-12) — POST /kb + DELETE /kb now also provision/drop the per-KB
Azure AI Search index (closes ADR-0018 Phase 3 upload-side):
- POST /kb: after the storage record is created, IndexPopulator.create_index_for_kb
  PUT-creates `ekp-kb-{kb_id}-v1` from `backend/indexing/schema.json`. Failure
  rolls back the storage record so subsequent retries with a fixed kb_id work.
- DELETE /kb: after the storage record is deleted, IndexPopulator.delete_index
  drops the per-KB Azure index. Fail-soft on 404 (index already gone — common
  for pre-CH-001 legacy KBs or after a partial-create rollback).
- Per-KB Azurite blob screenshot container (`ekp-kb-{kb_id}-screenshots` per
  ADR-0005) stays deferred — R12 Azurite signature mismatch unresolved + W16+
  Track A cloud Blob switch (CH-001 spec §6.6).
"""

import logging
import uuid
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, status

from api.schemas.kb import KbConfig, KbCreate, KbMetadataPatch, KbStatus
from indexing.populate import IndexPopulator
from kb_management import KBAlreadyExistsError, KBNotFoundError, KBService, get_kb_service

router = APIRouter()
logger = structlog.get_logger(__name__)
_stdlib_logger = logging.getLogger(__name__)

KbServiceDep = Annotated[KBService, Depends(get_kb_service)]


def _get_populator(request: Request) -> IndexPopulator | None:
    """Resolve the lifespan-wired IndexPopulator, or None when Azure cred missing.

    The populator is wired in `api/server.py` lifespan only when AZURE_OPENAI +
    AZURE_SEARCH credentials are present. POST /kb + DELETE /kb fail-soft when
    None — the storage record still mutates (preserves the W16 F5.3 Decision B.1
    in-memory baseline + the existing `test_delete_kb_in_memory_baseline_preserved`
    contract);only the Azure index side-effect is skipped + logged as a warning.
    Upload routes still require Azure(503 via `_engine_or_503`-style helper in
    routes/documents.py) since they can't function without it.
    """
    return getattr(request.app.state, "index_populator", None)


@router.get("/kb", response_model=list[KbStatus])
async def list_kbs(service: KbServiceDep) -> list[KbStatus]:
    """List all KBs (architecture.md §4.4 #4 + §3.4 multi-KB)."""
    return await service.list_all()


@router.post("/kb", response_model=KbStatus, status_code=status.HTTP_201_CREATED)
async def create_kb(payload: KbCreate, service: KbServiceDep, request: Request) -> KbStatus:
    """Create KB + provision the per-KB Azure AI Search index (architecture.md §4.4 #5 + ADR-0018).

    Two-step (closes CH-001 Phase 1.5):
    1. `service.create(payload)` — KB storage record (in-memory or Postgres per ADR-0023)
    2. `populator.create_index_for_kb(kb_id)` — Azure AI Search index `ekp-kb-{kb_id}-v1`
       from the canonical schema at `backend/indexing/schema.json`

    If step 2 fails (e.g. Azure rejects the kb_id format), the storage record from
    step 1 is rolled back via `service.delete(kb_id)` so the user can retry with a
    clean kb_id. If the rollback itself fails (rare — db down between steps), we
    still raise the 502 and log `storage_rollback_failed`; the user may end up with
    an orphan storage record they need to DELETE manually (per CH-001 spec R10).
    """
    try:
        kb = await service.create(payload)
    except KBAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    populator = _get_populator(request)
    if populator is None:
        # No Azure cred → fail-soft (W16 F5.3 Decision B.1 baseline preserved).
        # The KB record exists in storage but uploads will 503 until cred is wired.
        logger.warning(
            "kb_create_no_index_provision",
            kb_id=payload.kb_id,
            reason="IndexPopulator not initialized (AZURE_OPENAI / AZURE_SEARCH .env missing) — "
                   "subsequent POST /kb/{kb_id}/documents will 503 until cred is wired.",
        )
        return kb

    try:
        await populator.create_index_for_kb(payload.kb_id)
    except Exception as exc:  # noqa: BLE001 — Azure failure surfaces as a uniform 502
        _stdlib_logger.exception("index_create_failed for kb_id=%s", payload.kb_id)
        # Roll back the storage record so the user can retry with a different kb_id.
        try:
            await service.delete(payload.kb_id)
        except Exception as rollback_exc:  # noqa: BLE001 — log but don't shadow the original error
            logger.error(
                "storage_rollback_failed",
                kb_id=payload.kb_id,
                rollback_error=f"{type(rollback_exc).__name__}: {rollback_exc}",
                original_error=f"{type(exc).__name__}: {exc}",
            )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=(
                f"Azure AI Search index_create_failed for kb_id={payload.kb_id}: "
                f"{type(exc).__name__}: {exc}. "
                "Check kb_id matches Azure index-name rules: "
                "2-128 chars, lowercase a-z + 0-9 + dashes, no leading/trailing dash, "
                "no consecutive dashes."
            ),
        ) from exc

    return kb


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
async def delete_kb(kb_id: str, service: KbServiceDep, request: Request) -> None:
    """Delete KB + drop the per-KB Azure AI Search index (architecture.md §4.4 #7 + ADR-0018).

    CH-001 (2026-05-12) — closes the W16 F5.3 Decision B.1 deferral:
    1. `service.delete(kb_id)` — KB storage record (in-memory or Postgres per ADR-0023)
    2. `populator.delete_index(kb_id)` — Azure AI Search index `ekp-kb-{kb_id}-v1`
       (fail-soft on 404 — common for pre-CH-001 legacy KBs or partial-rollback
       orphans; warning logged but the response is still 204)

    Per-KB Azurite blob screenshot container drop (`ekp-kb-{kb_id}-screenshots`
    per ADR-0005) stays deferred — R12 Azurite signature mismatch unresolved +
    W16+ Track A cloud Blob switch (CH-001 spec §6.6 + ADR-0018 Phase 3 blob-side).

    Failure ordering note: storage delete runs FIRST; if Azure index drop then
    5xx-errors, the storage record is already gone (forward-only) — the user
    sees a 502 but should treat the KB as deleted and may need to re-attempt
    DELETE via direct Azure REST or `scripts/create_index.py delete` if the
    Azure index lingers.
    """
    try:
        await service.delete(kb_id)
    except KBNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    populator = _get_populator(request)
    if populator is None:
        # No Azure cred → fail-soft (W16 F5.3 Decision B.1 baseline preserved).
        # Storage record is gone; the Azure index drop is skipped.
        logger.warning(
            "kb_delete_no_index_drop",
            kb_id=kb_id,
            reason="IndexPopulator not initialized — Azure index (if any) not dropped here.",
        )
        return

    try:
        await populator.delete_index(kb_id)
        # delete_index() returns True (204) or False (404 — fail-soft); both OK.
    except Exception as exc:  # noqa: BLE001 — Azure 5xx surfaces as 502 with storage already gone
        _stdlib_logger.exception("index_delete_failed for kb_id=%s", kb_id)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=(
                f"Azure AI Search index_delete_failed for kb_id={kb_id}: "
                f"{type(exc).__name__}: {exc}. "
                "The storage record is already deleted — the Azure index may linger "
                "and can be dropped via `python -m scripts.create_index delete "
                f"--name ekp-kb-{kb_id}-v1 --yes`."
            ),
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


@router.post("/kb/{kb_id}/archive", response_model=KbStatus)
async def archive_kb(kb_id: str, service: KbServiceDep) -> KbStatus:
    """W20 F5.1 — soft-archive a KB per ADR-0025 (`/kb/[id]` Settings → Danger zone).

    Idempotent. Returns the updated KbStatus with `archived=True`. The route
    handler in `documents.py` (`_run_ingest_pipeline`) refuses to ingest into
    an archived KB (403); the Azure AI Search index + screenshot blobs are
    preserved so the chat surface keeps citing past content (per ADR-0025
    Settings → Danger zone semantics — archive is reversible via re-create).

    Tier 1 scope: no `unarchive` endpoint yet — Wave B+ surfaces both arms
    via a single `body={'archived': bool}` PATCH if user demand emerges.
    """
    try:
        return await service.archive(kb_id, archived=True)
    except KBNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
