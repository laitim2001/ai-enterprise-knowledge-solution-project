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
from typing import Annotated

import httpx
import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, status

from api.schemas.kb import KbConfig, KbCreate, KbMetadataPatch, KbStatus
from indexing.populate import IndexPopulator
from kb_management import KBAlreadyExistsError, KBNotFoundError, KBService, get_kb_service
from storage.audit_log_storage import AuditLogBackend

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


def _index_create_hint(exc: Exception) -> str:
    """An actionable hint for an index-create failure, matched to the cause.

    Azure AI Search returns 429 for two different things — a hard index-quota
    breach (delete an index / upgrade the tier) and transient throttling (wait
    and retry); the body's "quota" wording tells them apart. A 5xx is an outage,
    a 400 means Azure rejected the index name. Surfacing a blanket "check your
    kb_id" hint on any of these sent users debugging a non-issue.
    """
    if isinstance(exc, httpx.HTTPStatusError):
        code = exc.response.status_code
        if code == 429:
            if "quota" in exc.response.text.lower():
                return (
                    "Azure AI Search index quota is full — the Free tier caps at 3 "
                    "indexes. The KB record was rolled back. Delete an unused index "
                    "or upgrade the Search tier (Standard S1), then retry."
                )
            return (
                "Azure AI Search throttled the request (429) — the KB record was "
                "rolled back; wait ~1 min and retry."
            )
        if code >= 500:
            return (
                "Azure AI Search returned a server error — the KB record was rolled "
                "back; retry shortly."
            )
        if code == 400:
            return (
                "Azure rejected the index name — check kb_id: 2-128 chars, lowercase "
                "a-z + 0-9 + dashes, no leading/trailing dash, no consecutive dashes."
            )
    return "The KB record was rolled back — check backend logs (index_create_failed) and retry."


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
                f"{type(exc).__name__}: {exc}. " + _index_create_hint(exc)
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
async def update_kb_settings(
    kb_id: str, config: KbConfig, service: KbServiceDep, request: Request
) -> KbConfig:
    """Update KB config: embedding model, chunk strategy (architecture.md §4.4 #8).

    Treats the request body as a full replacement of `KbConfig` (all fields
    have defaults, so omitted fields are reset). Partial PATCH is W2+ if needed.

    W24c F7 — writes a `kb.config.changed` audit row when an audit backend is
    wired. `actor` stays None; per-endpoint actor extraction is a middleware-
    level Wave C2+ concern (per the audit_log schema doc).
    """
    try:
        updated = await service.update_config(kb_id, config)
    except KBNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    audit: AuditLogBackend | None = getattr(request.app.state, "audit_log_backend", None)
    if audit is not None:
        await audit.append(
            actor=None,
            action="kb.config.changed",
            resource=f"kb/{kb_id}",
            payload=config.model_dump(mode="json"),
        )
    return updated.config


@router.post("/kb/{kb_id}/reindex", status_code=status.HTTP_202_ACCEPTED)
async def reindex_kb(kb_id: str, request: Request, service: KbServiceDep) -> dict[str, object]:
    """W46 / ADR-0043 — real KB-level reindex of every document in the KB.

    Distinct from `POST /kb/{kb_id}/documents/{doc_id}/reindex` (per-doc). Was a
    Beta-baseline stub (mock task_id) until W46; now re-ingests each doc from its
    stored original source under the KB's CURRENT config — so a UI `chunk_strategy`
    / per-KB image-cap change actually takes effect. Synchronous (Tier 1 — no task
    queue). Docs with no stored source (ingested before W46, or whose best-effort
    source-persist failed) are skipped + reported under `skipped_no_source`
    (re-upload them via doc-level reindex to make them reindexable).

    Production zero-downtime (v1→v2 atomic index switch) stays deferred to Track A;
    W46 does in-place per-doc delete+reingest (brief inconsistency window, ADR-0043).

    Returns 202 + {status, kb_id, documents_total, documents_reindexed, reindexed,
    skipped_no_source, failed, chunks_total}.
    """
    try:
        kb = await service.get(kb_id)  # 404 guard
    except KBNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    if kb.archived:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"KB '{kb_id}' is archived — re-create the KB to resume ingest",
        )

    # Local import avoids a documents↔kb route-module import cycle (reindex-only path).
    from api.routes.documents import run_kb_reindex

    return await run_kb_reindex(kb_id=kb_id, request=request, service=service)


@router.post("/kb/{kb_id}/profiles/backfill", status_code=status.HTTP_202_ACCEPTED)
async def backfill_kb_profiles(
    kb_id: str, request: Request, service: KbServiceDep
) -> dict[str, object]:
    """W80 / ADR-0059 — profile-only backfill for every doc in the KB.

    The profiler only landed in ingest at W73, so docs ingested before W73 carry no
    profile (read surface null). This backfills each already-indexed doc — re-parse +
    compute profile + persist — WITHOUT re-chunk / re-embed / re-upsert (zero retrieval
    impact + zero disturbance to already-tuned per-KB config). Idempotent (skips a doc
    that already has a profile); a doc with no stored source (pre-W46 ingest) is reported
    under `skipped_no_source`. Synchronous (Tier 1). Returns 202 + {status, kb_id,
    documents_total, profiled, skipped_has_profile, skipped_no_source, failed, profiles}.
    """
    try:
        kb = await service.get(kb_id)  # 404 guard
    except KBNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    if kb.archived:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"KB '{kb_id}' is archived — re-create the KB to resume ingest",
        )

    # Local import avoids a documents↔kb route-module import cycle (backfill-only path).
    from api.routes.documents import run_kb_profile_backfill

    return await run_kb_profile_backfill(kb_id=kb_id, request=request, service=service)


@router.patch("/kb/{kb_id}", response_model=KbStatus)
async def update_kb_metadata(
    kb_id: str,
    patch: KbMetadataPatch,
    service: KbServiceDep,
) -> KbStatus:
    """W16 F5.2 CO_F3b — partial PATCH of KB name + description fields.

    Per Decision A.1 (separation of concern): this endpoint covers metadata
    only (name + description); KbConfig settings remain in
    `PATCH /kb/{kb_id}/settings`. All fields Optional — omitted = preserve
    existing value (true partial PATCH semantics).
    """
    try:
        return await service.update_metadata(
            kb_id,
            name=patch.name,
            description=patch.description,
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
