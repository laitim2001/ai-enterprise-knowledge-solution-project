"""SharePoint integration import endpoint (C17 / ADR-0070 階段 1, W100 F6).

Thin HTTP surface over the SharePoint connector + import_service. RBAC: workspace
`require_role("admin","editor")` + per-KB edit on the target KB (`assert_kb_access`,
body-aware since `kb_id` is in the body) — same write lane as the documents upload.

The production ingest adapter writes the source ACL as doc-level rows so the EXISTING
`_run_ingest_pipeline` resolves `allowed_principals` via its 5.2 override path —
ingestion core untouched (§7.2). The live path (real SharePoint + ingestion + Azure
index) runs per runbook §10 階段 C/D (needs a real tenant + Sites.Selected; not
verifiable locally, D4). Tests cover RBAC, not-configured, validation, and the adapter
structure with mocks.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, status
from pydantic import BaseModel

from api.auth.models import AuthenticatedUser
from api.middleware.acl import assert_kb_access, require_role
from api.routes.documents import (
    KbServiceDep,
    _ingestion_deps_or_503,
    _IngestionDeps,
    _run_ingest_pipeline,
)
from integration.import_service import ImportSummary, IngestCallable, import_documents
from integration.sharepoint.connector import SharePointConnector
from integration.sharepoint.graph_client import SharePointCredentials
from kb_management import KBService
from storage.settings import Settings, get_settings

router = APIRouter(prefix="/integration/sharepoint", tags=["integration"])


class SharePointImportRequest(BaseModel):
    kb_id: str
    container_ids: list[str]  # drive:: / folder:: ids from a prior browse


class DocImportResultOut(BaseModel):
    doc_id: str
    name: str
    status: str
    error: str | None = None


class ImportSummaryOut(BaseModel):
    total: int
    succeeded: int
    failed: int
    results: list[DocImportResultOut]


def _sharepoint_credentials_or_503(settings: Settings) -> SharePointCredentials:
    has_auth = bool(settings.sharepoint_client_secret or settings.sharepoint_certificate_path)
    if not (settings.sharepoint_tenant_id and settings.sharepoint_client_id and has_auth):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "SharePoint integration not configured — set SHAREPOINT_TENANT_ID / "
                "SHAREPOINT_CLIENT_ID / SHAREPOINT_CLIENT_SECRET (or "
                "SHAREPOINT_CERTIFICATE_PATH) in .env (H5: never commit)."
            ),
        )
    return SharePointCredentials(
        tenant_id=settings.sharepoint_tenant_id,
        client_id=settings.sharepoint_client_id,
        client_secret=settings.sharepoint_client_secret or None,
        certificate_path=settings.sharepoint_certificate_path or None,
    )


def make_pipeline_ingest(deps: _IngestionDeps, service: KBService) -> IngestCallable:
    """Adapter from the import seam to EKP's existing ingest pipeline (§7.2 — core
    untouched). Writes the source ACL as doc-level rows so `_run_ingest_pipeline`'s
    `resolve_doc_principals` (5.2 override) stamps them, then wraps the connector's
    temp file as an `UploadFile` and runs the UNCHANGED pipeline."""

    async def _ingest(
        *,
        content_path: object,
        name: str,
        kb_id: str,
        doc_id: str,
        allowed_principals: list[str],
        source_url: str,
    ) -> None:
        if allowed_principals:
            acl_store = deps.doc_acl_store
            if acl_store is None:
                # Can't persist the source ACL → the pipeline would fall back to KB
                # inheritance (possibly more permissive). Refuse (recorded per-doc).
                raise RuntimeError(
                    "doc_acl_store unwired — cannot persist SharePoint ACL; refusing to ingest"
                )
            for pid in allowed_principals:
                # principal_type is bookkeeping only — retrieval matching is by
                # principal_id string (resolve_doc_principals), so a uniform "group"
                # type is functionally correct. access_role "query" admits the
                # principal to the retrieval filter (role rank only gates writes).
                await acl_store.add(
                    kb_id=kb_id,
                    doc_id=doc_id,
                    principal_type="group",
                    principal_id=pid,
                    access_role="query",
                    granted_by=f"sharepoint-import:{source_url}"[:200],
                )
        path = Path(str(content_path))
        with path.open("rb") as fh:
            upload = UploadFile(file=fh, filename=name)
            await _run_ingest_pipeline(
                upload_file=upload, kb_id=kb_id, doc_id=doc_id, deps=deps, service=service
            )

    return _ingest


def _to_out(summary: ImportSummary) -> ImportSummaryOut:
    return ImportSummaryOut(
        total=summary.total,
        succeeded=summary.succeeded,
        failed=summary.failed,
        results=[
            DocImportResultOut(doc_id=r.doc_id, name=r.name, status=r.status, error=r.error)
            for r in summary.results
        ],
    )


@router.post("/import", response_model=ImportSummaryOut)
async def import_sharepoint(
    body: SharePointImportRequest,
    request: Request,
    actor: Annotated[AuthenticatedUser, Depends(require_role("admin", "editor"))],
    deps: Annotated[_IngestionDeps, Depends(_ingestion_deps_or_503)],
    service: KbServiceDep,
    settings: Annotated[Settings, Depends(get_settings)],
) -> ImportSummaryOut:
    """Import selected SharePoint containers into a KB (按需手動匯入, §8.3).

    Auth/connect failures are fatal (surface from `connect()` → 5xx); per-doc
    failures are recorded in the summary (⑦ / §8.1), not raised.
    """
    # Per-KB edit gate (body-aware — kb_id is in the body, W90 P2.0 pattern).
    await assert_kb_access(request, body.kb_id, actor, "edit")
    creds = _sharepoint_credentials_or_503(settings)
    connector = SharePointConnector(creds, anyone_policy=settings.sharepoint_anyone_policy)
    ingest = make_pipeline_ingest(deps, service)
    handle = await connector.connect()
    try:
        summary = await import_documents(
            connector,
            handle,
            kb_id=body.kb_id,
            container_ids=body.container_ids,
            ingest=ingest,
        )
    finally:
        await handle.aclose()
        await connector.aclose()
    return _to_out(summary)
