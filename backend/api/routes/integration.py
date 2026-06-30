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

from collections.abc import AsyncIterator
from pathlib import Path
from typing import Annotated
from urllib.parse import urlparse

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, Request, UploadFile, status
from pydantic import BaseModel

from api.auth.models import AuthenticatedUser
from api.middleware.acl import assert_kb_access, require_role
from api.routes.documents import (
    KbServiceDep,
    _ingestion_deps_or_503,
    _IngestionDeps,
    _run_ingest_pipeline,
)
from integration.import_service import (
    ImportSummary,
    IngestCallable,
    import_documents,
    import_selected_documents,
)
from integration.models import SourceContainer, SourceDocumentRef
from integration.sharepoint.connector import SharePointConnector
from integration.sharepoint.graph_client import SharePointCredentials
from kb_management import KBService
from storage.settings import Settings, get_settings

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/integration/sharepoint", tags=["integration"])

# D-6: server-side cap on browse/list results (大 library 防爆;HTTP transit of
# continuation tokens is 階段 2). Drained results past this are dropped + logged.
_LIST_CAP = 2000


class SourceContainerOut(BaseModel):
    """A browsable container (site / library / folder) for the wizard step-2 tree."""

    id: str
    name: str
    type: str
    parent_id: str | None = None


class SourceDocumentRefOut(BaseModel):
    """A listable document + change-detection metadata for the step-2 picker (②③)."""

    id: str
    name: str
    path: str
    container_id: str
    etag: str | None = None
    version: str | None = None
    last_modified: str | None = None  # ISO-8601 (datetime serialised for transport)
    size: int | None = None


class SourceDocumentRefIn(BaseModel):
    """A document ref the wizard sends back for individual-file import (#1 / D-3)."""

    id: str
    name: str
    path: str
    container_id: str
    etag: str | None = None
    version: str | None = None
    size: int | None = None


class ResolveSiteRequest(BaseModel):
    site_url: str


class BrowseResponse(BaseModel):
    containers: list[SourceContainerOut]


class DocumentsResponse(BaseModel):
    documents: list[SourceDocumentRefOut]


class SharePointImportRequest(BaseModel):
    kb_id: str
    # Either whole containers (W100, container-level) OR individually-picked document
    # refs (#1 / D-3, the wizard step-2 selection). At least one must be non-empty
    # (validated in-route — Pydantic can't express "exactly one of" cleanly here).
    container_ids: list[str] = []  # drive:: / folder:: ids from a prior browse
    documents: list[SourceDocumentRefIn] = []


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


def _new_connector(settings: Settings) -> SharePointConnector:
    """Build a SharePoint connector from server-side config (H5 — credentials live in
    .env / Key Vault, never the request body). 503 if unconfigured."""
    creds = _sharepoint_credentials_or_503(settings)
    return SharePointConnector(creds, anyone_policy=settings.sharepoint_anyone_policy)


def _parse_site_url(site_url: str) -> tuple[str, str]:
    """`https://contoso.sharepoint.com/sites/manuals` → (hostname, server-relative path)."""
    parsed = urlparse(site_url if "://" in site_url else f"https://{site_url}")
    hostname, site_path = parsed.netloc, parsed.path.strip("/")
    if not hostname or not site_path:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="invalid SharePoint site URL (expected https://<tenant>.sharepoint.com/sites/<name>)",
        )
    return hostname, site_path


async def _collect_capped[T](gen: AsyncIterator[T]) -> list[T]:
    """Drain an async generator into a list, capped (D-6). Logs on truncation so the
    cap is never silent (CLAUDE.md 'no silent caps')."""
    out: list[T] = []
    async for item in gen:
        out.append(item)
        if len(out) >= _LIST_CAP:
            logger.warning("integration_list_cap_hit", cap=_LIST_CAP)
            break
    return out


def _container_out(c: SourceContainer) -> SourceContainerOut:
    return SourceContainerOut(id=c.id, name=c.name, type=c.type, parent_id=c.parent_id)


def _ref_out(r: SourceDocumentRef) -> SourceDocumentRefOut:
    return SourceDocumentRefOut(
        id=r.id,
        name=r.name,
        path=r.path,
        container_id=r.container_id,
        etag=r.etag,
        version=r.version,
        last_modified=r.last_modified.isoformat() if r.last_modified else None,
        size=r.size,
    )


def _ref_in_to_model(d: SourceDocumentRefIn) -> SourceDocumentRef:
    return SourceDocumentRef(
        id=d.id,
        name=d.name,
        path=d.path,
        container_id=d.container_id,
        etag=d.etag,
        version=d.version,
        size=d.size,
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


@router.post("/resolve-site", response_model=SourceContainerOut)
async def resolve_site(
    body: ResolveSiteRequest,
    actor: Annotated[AuthenticatedUser, Depends(require_role("admin", "editor"))],
    settings: Annotated[Settings, Depends(get_settings)],
) -> SourceContainerOut:
    """Resolve a SharePoint site URL → a site container (wizard step 1 'Test connection'
    + step 2 tree root). Connect / auth / 403-no-grant failures surface as 5xx (fatal,
    §8.1)."""
    hostname, site_path = _parse_site_url(body.site_url)
    connector = _new_connector(settings)
    handle = await connector.connect()
    try:
        container = await connector.resolve_site(handle, hostname, site_path)
    finally:
        await handle.aclose()
        await connector.aclose()
    return _container_out(container)


@router.get("/browse", response_model=BrowseResponse)
async def browse(
    actor: Annotated[AuthenticatedUser, Depends(require_role("admin", "editor"))],
    settings: Annotated[Settings, Depends(get_settings)],
    container_id: Annotated[str | None, Query()] = None,
) -> BrowseResponse:
    """List child containers (site → library → folder) for the step-2 tree (②).
    `container_id` omitted = top level (sites)."""
    connector = _new_connector(settings)
    handle = await connector.connect()
    try:
        containers = await _collect_capped(connector.browse(handle, container_id))
    finally:
        await handle.aclose()
        await connector.aclose()
    return BrowseResponse(containers=[_container_out(c) for c in containers])


@router.get("/documents", response_model=DocumentsResponse)
async def list_documents(
    actor: Annotated[AuthenticatedUser, Depends(require_role("admin", "editor"))],
    settings: Annotated[Settings, Depends(get_settings)],
    container_id: Annotated[str, Query()],
) -> DocumentsResponse:
    """List file documents in a drive / folder for the step-2 picker (②③)."""
    connector = _new_connector(settings)
    handle = await connector.connect()
    try:
        refs = await _collect_capped(connector.list_documents(handle, container_id))
    finally:
        await handle.aclose()
        await connector.aclose()
    return DocumentsResponse(documents=[_ref_out(r) for r in refs])


@router.post("/import", response_model=ImportSummaryOut)
async def import_sharepoint(
    body: SharePointImportRequest,
    request: Request,
    actor: Annotated[AuthenticatedUser, Depends(require_role("admin", "editor"))],
    deps: Annotated[_IngestionDeps, Depends(_ingestion_deps_or_503)],
    service: KbServiceDep,
    settings: Annotated[Settings, Depends(get_settings)],
) -> ImportSummaryOut:
    """Import selected SharePoint content into a KB (按需手動匯入, §8.3) — either whole
    containers (`container_ids`, W100) or individually-picked documents (`documents`,
    #1 / D-3, the wizard step-2 selection).

    Auth/connect failures are fatal (surface from `connect()` → 5xx); per-doc failures
    are recorded in the summary (⑦ / §8.1), not raised.
    """
    # Per-KB edit gate (body-aware — kb_id is in the body, W90 P2.0 pattern).
    await assert_kb_access(request, body.kb_id, actor, "edit")
    if not body.container_ids and not body.documents:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="provide container_ids (container-level) or documents (individual files)",
        )
    connector = _new_connector(settings)
    ingest = make_pipeline_ingest(deps, service)
    handle = await connector.connect()
    try:
        if body.documents:
            refs = [_ref_in_to_model(d) for d in body.documents]
            summary = await import_selected_documents(
                connector, handle, kb_id=body.kb_id, refs=refs, ingest=ingest
            )
        else:
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
