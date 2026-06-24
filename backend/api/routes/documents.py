"""Document management endpoints (per architecture.md §4.4 #9-12 + §3.3).

W16 F5.1.1 closure (CO_F3a):
    GET /kb/{kb_id}/documents — replaced 501 stub with Azure AI Search
    aggregation via RetrievalEngine.list_documents (kb_id-scoped chunks
    grouped by doc_id; returns list[DocumentSummary]).

CH-001 (2026-05-12) — closes CO_F3a fully:
    POST /kb/{kb_id}/documents — multipart UploadFile → tempfile →
        select_parser → IngestionOrchestrator → IndexPopulator.upload(kb_id=)
        → 200/202 with {doc_id, status:"indexed", chunks_emitted, ...}.
    DELETE /kb/{kb_id}/documents/{doc_id} — IndexPopulator.delete_doc → 204
        on success / 404 if no chunks match (clean idempotency).
    POST /kb/{kb_id}/documents/{doc_id}/reindex (Decision A = (ii)) — multipart
        re-upload → delete existing chunks → ingest new under same doc_id
        → 202 atomic replace.
    7 error codes (validation.unsupported_format / kb.not_found /
    azure.config_missing / ingestion.{parse,embed,index}_failed /
    document.duplicate / reindex.{doc_id_mismatch,partial_failure}).

W88 P0 F5 (2026-06-24) — the 4 write endpoints (upload / delete / reindex /
profile-override) now gate on require_kb_acl("edit"): per-KB document content
mutations follow the kb.edit_config / kb.trigger_reindex matrix lane (admin +
editor with an edit grant). Workspace admins pass unconditionally (ADR-0027);
GET listing / outline / image-proxy routes stay ungated (P2 retrieval trimming).
"""

import io
import json
import logging
import re
import shutil
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, cast

import structlog
from azure.core.exceptions import ResourceNotFoundError
from fastapi import APIRouter, Depends, HTTPException, Request, Response, UploadFile, status

from api.middleware.acl import require_kb_acl, require_role, resolve_kb_principals
from api.schemas.doc_classification import (
    ClassificationUpdateRequest,
    DocClassificationInfo,
)
from api.schemas.doc_profile import DocProfileInfo, ProfileOverrideRequest
from api.schemas.kb import FailureRecord, KbConfig
from api.schemas.listing import (
    DocumentDetail,
    DocumentSummary,
    KbImageItem,
    KbImagesResponse,
    OutlineNode,
)
from api.schemas.query import ImageRef
from indexing.populate import IndexPopulator
from ingestion.chunker.base import Chunker
from ingestion.chunker.heading_aware import HeadingAwareChunker
from ingestion.embedding.base import Embedder
from ingestion.orchestrator import IngestionOrchestrator
from ingestion.parsers import select_parser
from ingestion.profile_presets import resolve_preset
from ingestion.profiler import DocProfile, DocumentProfiler, ProfileResult, is_scan_pdf
from ingestion.screenshots.uploader import ScreenshotUploader, download_screenshot
from ingestion.source_store import download_source_document, upload_source_document
from kb_management import KBNotFoundError, KBService, get_kb_service
from kb_management.doc_classification_store import DocClassificationStore
from kb_management.doc_config_store import DocConfigStore
from kb_management.doc_profile_store import DocProfileStore
from kb_management.preset_override_store import PresetOverrideStore
from retrieval.retrieval_engine import RetrievalEngine
from storage.kb_naming import kb_id_to_screenshot_container
from storage.rbac_storage import RbacBackend
from storage.settings import get_settings

logger = structlog.get_logger(__name__)
_stdlib_logger = logging.getLogger(__name__)

_SUPPORTED_EXTS = {".docx", ".pdf", ".pptx"}
_DOC_ID_RE = re.compile(r"[^a-z0-9-]+")
# BUG-010 — screenshot blob names are `{sha256}.{ext}`; gates the proxy route's
# path param (defence-in-depth alongside `Path(...).name` traversal stripping).
_SCREENSHOT_BLOB_RE = re.compile(r"^[a-f0-9]{64}\.[a-z0-9]{2,5}$")

# W80 / ADR-0059 — profile-only backfill reuses a stateless pure-rule profiler
# (same DocumentProfiler the orchestrator holds; multiple instances are harmless).
_PROFILER = DocumentProfiler()

router = APIRouter()

KbServiceDep = Annotated[KBService, Depends(get_kb_service)]


@dataclass(slots=True, frozen=True)
class _IngestionDeps:
    """CH-001 — the four ingestion-side services resolved from app.state.

    Embedder + IndexPopulator are lifespan-managed Azure clients (one per app
    lifetime); Chunker is stateless. Parser is constructed per-request via
    select_parser(file_extension) inside the route handlers (depends on input
    file type, can't be lifespan-bound).

    `chunker` is the global-cap singleton (inherit path); `make_chunker` (W45 /
    ADR-0042) is the per-KB factory used when a KB sets `chunker_max_images_per_chunk`.
    `make_chunker=None` (e.g. a test that wires only the singleton) falls back to
    the singleton — safe because such a KB carries no per-KB cap to honour.
    """

    embedder: Embedder
    populator: IndexPopulator
    chunker: Chunker
    make_chunker: Callable[[int | None], Chunker] | None = None
    # W73 / ADR-0056 層 A — per-doc config store for profile→preset routing
    # (None when the store isn't wired, e.g. some tests → routing skips silently).
    doc_config_store: DocConfigStore | None = None
    # W76 / ADR-0056 層 A 段③ 前置 — per-doc profile store (persist on ingest for the
    # read surface). None when not wired → persist skips silently (advisory).
    doc_profile_store: DocProfileStore | None = None
    # W82 / ADR-0063 層 A 段③ 缺口 B — global preset-override store. None when unwired →
    # `_route_profile_preset` resolves the factory preset (production-preserve).
    preset_override_store: PresetOverrideStore | None = None
    # ADR-0066 / W90 P2.1 — RBAC backend for retrieval-layer ACL stamping. None
    # when unwired (some tests, or a deploy before the RBAC backend lands) →
    # `resolve_kb_principals` returns [] → chunks stamp no principals (fail-open
    # transition, the P2.2 filter treats empty as public). production-preserve.
    rbac_backend: RbacBackend | None = None
    # ADR-0066 / W90 P2.3 — per-doc classification store. None when unwired → ingest
    # stamps the default `internal` (a restricted tag won't survive re-ingest until
    # the store is wired); the admin tag endpoint 503s without it. production-preserve.
    doc_classification_store: DocClassificationStore | None = None


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


def _doc_profile_store(request: Request) -> DocProfileStore | None:
    """Resolve the lifespan-wired per-doc profile store (W76 / ADR-0056 層 A 段③ 前置).

    Read paths (list_documents / doc_detail) join the store best-effort — an absent
    store (unwired, or some tests) just leaves profile fields None (graceful degrade).
    """
    return getattr(request.app.state, "doc_profile_store", None)


def _preset_override_store(request: Request) -> PresetOverrideStore | None:
    """Resolve the lifespan-wired global preset-override store (W82 / ADR-0063).

    Absent (unwired, or some tests) → routing / override fall back to the factory
    preset via `resolve_preset(profile, None)` (production-preserve, graceful degrade).
    """
    return getattr(request.app.state, "preset_override_store", None)


def _doc_classification_store(request: Request) -> DocClassificationStore | None:
    """Resolve the lifespan-wired per-doc classification store (W90 P2.3 / ADR-0066).

    Absent (unwired, or some tests) → the tag endpoint 503s and ingest stamps the
    default `internal` (a restricted tag won't survive re-ingest). production-preserve.
    """
    return getattr(request.app.state, "doc_classification_store", None)


def _ingestion_deps_or_503(request: Request) -> _IngestionDeps:
    """Resolve the lifespan-wired ingestion services or 503.

    Upload + reindex routes need all three (embedder for chunk embedding,
    populator for Azure AI Search push/delete, chunker for layout-aware
    chunking). Absence of any → 503 `azure.config_missing` (the populator is
    None when Azure cred isn't configured per CH-001 spec §6.2 Approach A).
    """
    embedder = getattr(request.app.state, "embedder", None)
    populator = getattr(request.app.state, "index_populator", None)
    chunker = getattr(request.app.state, "ingestion_chunker", None)
    # W45 / ADR-0042 — per-KB chunker factory (lifespan-wired in server.py).
    # Absent in tests that only set the singleton → make_chunker=None → inherit path.
    make_chunker = getattr(request.app.state, "make_ingestion_chunker", None)
    # W73 / ADR-0056 層 A — doc-config store for profile→preset auto-write.
    doc_config_store = getattr(request.app.state, "doc_config_store", None)
    # W76 / ADR-0056 層 A 段③ 前置 — doc-profile store for read-surface persist.
    doc_profile_store = getattr(request.app.state, "doc_profile_store", None)
    # W82 / ADR-0063 層 A 段③ 缺口 B — global preset-override store for effective routing.
    preset_override_store = getattr(request.app.state, "preset_override_store", None)
    # ADR-0066 / W90 P2.1 — RBAC backend for retrieval-layer ACL stamping (optional;
    # None → resolve_kb_principals returns [] = fail-open transition).
    rbac_backend = getattr(request.app.state, "rbac_backend", None)
    # ADR-0066 / W90 P2.3 — per-doc classification store (optional; None → ingest stamps
    # default internal, tag endpoint 503s).
    doc_classification_store = getattr(request.app.state, "doc_classification_store", None)
    if embedder is None or populator is None or chunker is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Ingestion services not initialized — check Azure OpenAI + AI Search "
                ".env config (AZURE_OPENAI_API_KEY + AZURE_SEARCH_ADMIN_KEY)."
            ),
        )
    return _IngestionDeps(
        embedder=embedder,
        populator=populator,
        chunker=chunker,
        make_chunker=make_chunker,
        doc_config_store=doc_config_store,
        doc_profile_store=doc_profile_store,
        preset_override_store=preset_override_store,
        rbac_backend=rbac_backend,
        doc_classification_store=doc_classification_store,
    )


def _select_chunker(deps: _IngestionDeps, kb_config: KbConfig | None) -> Chunker:
    """Pick the chunker for this ingest run (W45 / ADR-0042; W53 / ADR-0044).

    Dispatch on `kb_config.chunk_strategy` first (W53 / ADR-0044):
      * `heading_aware` → `HeadingAwareChunker` (section-bounded coarse; combines
        the per-KB image cap when set). Re-index is what makes a strategy change
        take effect — this closes the W46 reindex over-promise gap where
        `chunk_strategy` was read into DocumentDetail but never reached ingest.
      * `layout_aware` / `slide_based` / `auto` → existing LayoutAwareChunker path
        (bit-identical fall-through), driven by `chunker_max_images_per_chunk`:
        - None (or no kb_config / no factory) → the global-cap singleton
          (`deps.chunker`) — zero construct cost + bit-identical to pre-W45.
        - positive int → a per-ingest chunker with that per-KB cap, built via the
          `deps.make_chunker` factory (keeps this route decoupled from the concrete
          chunker class).
    """
    cap_override = kb_config.chunker_max_images_per_chunk if kb_config else None
    strategy = kb_config.chunk_strategy if kb_config else "auto"
    if strategy == "heading_aware":
        # cap None → inherit the global default cap (parity with the layout_aware
        # singleton); positive int → per-KB cap on the section-bounded chunker.
        if cap_override is None:
            return HeadingAwareChunker()
        return HeadingAwareChunker(max_images_per_chunk=cap_override)
    if cap_override is None or deps.make_chunker is None:
        return deps.chunker
    return deps.make_chunker(cap_override)


async def _verify_kb_or_404(kb_id: str, service: KBService) -> None:
    try:
        await service.get(kb_id)
    except KBNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


async def _refuse_if_archived(kb_id: str, service: KBService) -> None:
    """W20 F5.1 — soft-archive guard for ingest write paths (upload + reindex).

    Reads the KB record and returns 403 `kb.archived` when `archived=True` so
    no new chunks are written into the index. Pairs with `POST /kb/{kb_id}/archive`
    (per ADR-0025 `/kb/[id]` Settings → Danger zone). Read-only paths (GET docs,
    chunks, query, retrieval test) deliberately don't flip 403 — the chat surface
    keeps citing past content from an archived KB."""
    try:
        kb = await service.get(kb_id)
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


@router.get("/kb/{kb_id}/documents", response_model=list[DocumentSummary])
async def list_documents(
    kb_id: str,
    request: Request,
    service: KbServiceDep,
) -> list[DocumentSummary]:
    """W16 F5.1.1 — list docs in KB via Azure AI Search aggregation.

    Verifies kb_id exists via KBService (404 if missing); then aggregates
    chunks in the kb_id-scoped index by doc_id, returning doc-level metadata.
    Empty index → empty list (kb exists but no chunks ingested).
    """
    await _verify_kb_or_404(kb_id, service)

    engine = _engine_or_503(request)
    try:
        rows = await engine.list_documents(kb_id)
    except Exception as exc:  # noqa: BLE001 — surface downstream Azure errors as 502
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"document listing failure: {type(exc).__name__}: {exc}",
        ) from exc

    summaries = [DocumentSummary(**row) for row in rows]
    # W76 / ADR-0056 層 A 段③ 前置 — join the persisted profile (label + confidence)
    # best-effort. Absent store / join failure → profile fields stay None (graceful).
    store = _doc_profile_store(request)
    if store is not None:
        try:
            profiles = await store.list_for_kb(kb_id)
        except Exception:  # noqa: BLE001 — advisory join; degrade to None
            profiles = {}
        for summary in summaries:
            persisted = profiles.get(summary.doc_id)
            if persisted is not None:
                # ADR-0058 — L2 badge 顯示 effective profile (manual_override 優先於 system auto).
                # override = human-set → 無 confidence 概念 (L2 badge 唔顯示 % + 唔黃旗);
                # auto → 顯示 system 信心度 (低信心黃旗).
                summary.profile = persisted.manual_override or persisted.profile
                summary.profile_confidence = (
                    None if persisted.manual_override is not None else persisted.confidence
                )
    return summaries


@router.get("/kb/{kb_id}/images", response_model=KbImagesResponse)
async def list_kb_images(
    kb_id: str,
    request: Request,
    service: KbServiceDep,
    limit: int = 50,
    offset: int = 0,
) -> KbImagesResponse:
    """W20 F5.2 — paginated image list across the KB (per ADR-0025 KB Detail Tab 3).

    Walks the KB's documents → per-doc chunks → flattens `embedded_images_json`
    → deduplicates by `checksum_sha256` (image identity). Pagination by simple
    slicing post-dedup (Tier 1 — image counts stay modest, no need for
    server-side pagination yet).

    Newly-ingested chunks carry real `embedded_images_json` once the KB opted
    into `extract_embedded_images` (BUG-009 wired the orchestrator's screenshot
    uploader; R12 resolved via the `UseDevelopmentStorage=true` connection
    string). Text-only KBs still flatten to an empty list with 200 OK.

    Returns 404 when `kb_id` doesn't exist (KB not found). 503 when retrieval
    engine isn't initialized (Azure config missing).
    """
    await _verify_kb_or_404(kb_id, service)
    limit = max(1, min(limit, 200))  # clamp pagination
    offset = max(0, offset)

    engine = _engine_or_503(request)

    try:
        docs = await engine.list_documents(kb_id)
    except Exception as exc:  # noqa: BLE001 — Azure surfacing
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"document listing failure: {type(exc).__name__}: {exc}",
        ) from exc

    seen: dict[str, KbImageItem] = {}
    for doc in docs:
        doc_id = str(doc.get("doc_id", ""))
        doc_title = str(doc.get("doc_title", doc_id))
        if not doc_id:
            continue
        try:
            chunks = await engine.list_chunks(kb_id, doc_id)
        except Exception as exc:  # noqa: BLE001 — Azure surfacing
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"chunk listing failure for doc {doc_id!r}: {type(exc).__name__}: {exc}",
            ) from exc

        for chunk in chunks:
            raw = chunk.get("embedded_images_json") or "[]"
            try:
                images = json.loads(raw) if isinstance(raw, str) else raw
            except (TypeError, ValueError):
                continue  # skip malformed JSON — same fail-soft as W17 F4.1
            if not isinstance(images, list):
                continue
            for img in images:
                if not isinstance(img, dict):
                    continue
                sha = str(img.get("checksum_sha256") or "")
                blob_url = str(img.get("blob_url") or "")
                if not sha or sha in seen or not blob_url:
                    continue
                seen[sha] = KbImageItem(
                    id=sha,
                    url=screenshot_proxy_url(request, kb_id, blob_url),
                    doc_id=doc_id,
                    doc_name=doc_title,
                    ocr_text=str(img.get("alt_text") or ""),
                )

    items = list(seen.values())
    total = len(items)
    paginated = items[offset : offset + limit]
    return KbImagesResponse(items=paginated, total=total, limit=limit, offset=offset)


def screenshot_proxy_url(request: Request, kb_id: str, blob_url: str) -> str:
    """BUG-010 + BUG-012 — rewrite a raw screenshot blob URL to a same-origin
    proxy path routed through the Next.js `/api/backend/[...path]` catch-all
    (W11 D2 R8 mitigation per `frontend/app/api/backend/[...path]/route.ts`).

    The stored `blob_url` ends in `/{container}/{sha}.{ext}`; the browser can't
    read the private blob directly, so image URLs are served via
    `GET /kb/{kb_id}/screenshots/{blob_name}`. The previous BUG-010 build used
    `str(request.base_url)` to produce an absolute URL — but that resolved to
    the backend's own origin (`http://127.0.0.1:8000`) which is cross-origin
    from the frontend dev server (`http://localhost:3001`). A cross-origin
    `<img>` GET does not send the `ekp_session` cookie by default, so the
    proxy route returned 401 and every thumbnail fell back to the placeholder
    via BUG-011's `onError` handler (DevTools Network 8/8 red 2026-05-24).

    Returning a path-only URL makes the browser resolve it relative to the
    current page origin → same-origin from `localhost:3001` → cookies flow →
    backend `get_current_user` cookie path authenticates → 200 with bytes.

    `request` is kept in the signature for caller-shape stability with the
    chat citation path (`query.py::_proxy_citation_images`); `del request`
    explicitly marks it intentionally unused post-fix.
    """
    del request  # unused after BUG-012 fix; signature retained for caller stability
    blob_name = blob_url.rsplit("/", 1)[-1]
    return f"/api/backend/kb/{kb_id}/screenshots/{blob_name}"


@router.get("/kb/{kb_id}/screenshots/{blob_name}")
async def get_kb_screenshot(
    kb_id: str,
    blob_name: str,
    request: Request,
    service: KbServiceDep,
) -> Response:
    """BUG-010 — stream a private screenshot blob to the browser.

    The screenshot container has no public read and no SAS, so a browser
    `<img>` can't authenticate to Azure Blob directly. This route proxies the
    bytes — the API holds the connection string. Auth is the `/kb` prefix's
    existing middleware; a logged-in browser sends its session cookie on the
    `<img>` request automatically.
    """
    await _verify_kb_or_404(kb_id, service)
    if Path(blob_name).name != blob_name or not _SCREENSHOT_BLOB_RE.match(blob_name):
        raise _api_error(
            "validation.bad_blob_name",
            f"screenshot blob name {blob_name!r} is not a valid '{{sha256}}.{{ext}}'",
            "Use a URL returned by GET /kb/{kb_id}/images.",
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        )
    settings = get_settings()
    container = kb_id_to_screenshot_container(
        kb_id,
        legacy_default_container=settings.azure_blob_container_screenshots,
    )
    try:
        data, content_type = await download_screenshot(
            settings.azure_blob_connection_string,
            container,
            blob_name,
        )
    except ResourceNotFoundError as exc:
        raise _api_error(
            "screenshot.not_found",
            f"screenshot {blob_name!r} not found for KB {kb_id!r}",
            "The image may not be ingested yet, or the KB was re-created.",
            status.HTTP_404_NOT_FOUND,
        ) from exc
    return Response(content=data, media_type=content_type)


@router.get("/kb/{kb_id}/docs/{doc_id}", response_model=DocumentDetail)
async def get_document_detail(
    kb_id: str,
    doc_id: str,
    request: Request,
    service: KbServiceDep,
) -> DocumentDetail:
    """W21 F1 (per ADR-0029 Option C) — per-document deep inspection enriched response.

    Powers the 3-pane Doc Detail view (`/kb/[id]/docs/[docId]`):
      - Doc-level metadata via `RetrievalEngine.list_documents(kb_id)` filtered
        to the requested `doc_id` (404 when the doc has no chunks in the KB).
      - Outline reconstructed from chunks' `section_path[]` (one OutlineNode per
        unique non-empty section path; level = path depth; chunk_count = number
        of chunks at that exact path).
      - Image refs aggregated from chunks' `embedded_images_json` and deduped by
        SHA-256 (same algorithm as `GET /kb/{kb_id}/images`).
      - `chunk_strategy` from `KbConfig.chunk_strategy` (already verified-present
        via `_verify_kb_or_404`).

    F1.3 duration seam: `parse_duration_ms` + `embed_duration_ms` carry `None`
    today — wired when ingestion result persistence lands Wave C+ (forward-compat
    documented per ADR-0029 §3). UI surfaces "—" + tooltip per plan §2 F3.6.

    URL convention `/kb/{kb_id}/docs/{doc_id}` (not `/documents/{doc_id}`) matches
    ADR-0029 Option C frontend route + W19 F4 §2 backend gap item 9 — deliberate
    departure from the existing `/documents/{doc_id}` delete/reindex routes to
    keep the front-end IA + backend endpoint paired (per plan §1).

    Returns 404 when `kb_id` doesn't exist (via `_verify_kb_or_404`) or when
    `doc_id` has no chunks in the KB (post-list-documents lookup). Returns 502 on
    upstream Azure failures. Returns 503 when RetrievalEngine isn't initialized.
    """
    await _verify_kb_or_404(kb_id, service)

    engine = _engine_or_503(request)

    # Pull doc-level row from the KB-scoped aggregation; 404 when absent.
    try:
        docs = await engine.list_documents(kb_id)
    except Exception as exc:  # noqa: BLE001 — surface Azure errors as 502
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"document listing failure: {type(exc).__name__}: {exc}",
        ) from exc

    doc_row = next((d for d in docs if d.get("doc_id") == doc_id), None)
    if doc_row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"document {doc_id!r} not found in kb {kb_id!r}",
        )

    # Pull chunks for outline + image_refs + low_value count.
    try:
        chunks = await engine.list_chunks(kb_id, doc_id)
    except Exception as exc:  # noqa: BLE001 — surface Azure errors as 502
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"chunk listing failure for doc {doc_id!r}: {type(exc).__name__}: {exc}",
        ) from exc

    # Reconstruct outline — one OutlineNode per unique non-empty section_path.
    section_counts: dict[tuple[str, ...], int] = {}
    for chunk in chunks:
        path_raw = chunk.get("section_path") or []
        path = tuple(str(p) for p in path_raw)
        if not path:
            continue
        section_counts[path] = section_counts.get(path, 0) + 1
    outline = [
        OutlineNode(level=len(path), title=path[-1], chunk_count=count, page=None)
        for path, count in sorted(section_counts.items())
    ]

    # Aggregate image refs by SHA256 dedup (mirrors list_kb_images logic).
    seen_images: dict[str, ImageRef] = {}
    for chunk in chunks:
        raw = chunk.get("embedded_images_json") or "[]"
        try:
            images = json.loads(raw) if isinstance(raw, str) else raw
        except (TypeError, ValueError):
            continue  # malformed JSON — fail-soft (same as W17 F4.1 + W20 F5.2)
        if not isinstance(images, list):
            continue
        for img in images:
            if not isinstance(img, dict):
                continue
            sha = str(img.get("checksum_sha256") or "")
            blob_url = str(img.get("blob_url") or "")
            if not sha or sha in seen_images or not blob_url:
                continue
            # BUG-015 — override the ingestion-time raw Azurite URL with the
            # same-origin proxy path (mirrors `/kb/{kb_id}/images` aggregator
            # post-BUG-012); raw Azurite blob URLs are browser-blocked (no CORS
            # / no SAS / private blob — BUG-009 设计初心 = proxy through auth).
            seen_images[sha] = ImageRef(
                blob_url=screenshot_proxy_url(request, kb_id, blob_url),
                alt_text=str(img.get("alt_text") or ""),
                checksum_sha256=sha,
                width=int(img.get("width") or 0),
                height=int(img.get("height") or 0),
            )

    low_value_count = sum(1 for c in chunks if c.get("low_value_flag"))

    # Pull chunk_strategy from KbConfig (KB already verified via _verify_kb_or_404).
    kb_record = await service.get(kb_id)
    chunk_strategy = kb_record.config.chunk_strategy

    # W76 / ADR-0056 層 A 段③ 前置 — join the persisted profile (full signals) best-effort.
    doc_profile = None
    profile_store = _doc_profile_store(request)
    if profile_store is not None:
        try:
            doc_profile = await profile_store.get(kb_id, doc_id)
        except Exception:  # noqa: BLE001 — advisory join; degrade to None
            doc_profile = None

    return DocumentDetail(
        doc_id=doc_id,
        title=str(doc_row.get("doc_title") or ""),
        source=None,
        source_url=doc_row.get("source_url"),
        file_type=str(doc_row.get("doc_format") or ""),
        size_kb=None,
        pages=None,
        language=None,
        chunk_strategy=chunk_strategy,
        total_chunks=int(doc_row.get("total_chunks") or len(chunks)),
        total_images=len(seen_images),
        total_tokens=None,
        low_value_chunks=low_value_count,
        parse_duration_ms=None,
        embed_duration_ms=None,
        indexed_at=str(doc_row.get("last_indexed_at") or ""),
        outline=outline,
        image_refs=list(seen_images.values()),
        profile=doc_profile,
    )


@router.put(
    "/kb/{kb_id}/docs/{doc_id}/profile",
    response_model=DocProfileInfo,
    dependencies=[Depends(require_kb_acl("edit"))],
)
async def override_doc_profile(
    kb_id: str,
    doc_id: str,
    payload: ProfileOverrideRequest,
    request: Request,
    service: KbServiceDep,
) -> DocProfileInfo:
    """ADR-0058 — 人手覆寫 doc profile: 套對應 preset 落 per-doc config + 記 manual_override.

    Explicit user action — 套 preset **覆蓋** 現有 per-doc config (per ADR-0056 D3「套 preset」,
    非 merge; user 可之後 L3 逐 knob fine-tune). 唔用 `_route_profile_preset` (嗰個 D6 skip-if-manual
    係 ingest auto-route 用). system auto profile/confidence/signals 保留 (W76 read-only fact); 只加
    `manual_override` annotation. UI effective = `manual_override ?? profile`. re-ingest preserve 此
    annotation (per `_run_ingest_pipeline` ADR-0058 D6 守).

    404 if no stored profile (未 ingest / 未 profiled — 唔可 override 一個未偵測嘅 doc).
    422 if the target profile has no routable preset (too_small / unknown / invalid label).
    """
    await _verify_kb_or_404(kb_id, service)
    await _refuse_if_archived(kb_id, service)

    # override 唔需 ingestion services (embedder/populator/chunker) — 只需兩個 store
    # (唔用 `_ingestion_deps_or_503` 嗰個 require ingestion services 否則 503).
    profile_store = _doc_profile_store(request)
    config_store: DocConfigStore | None = getattr(request.app.state, "doc_config_store", None)
    if profile_store is None or config_store is None:
        raise _api_error(
            "profile.store_unavailable",
            "Profile / config store not configured.",
            "Persistent stores require DATABASE_URL; the in-memory fallback is wired on startup.",
            status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    # payload.profile is a free-form str (API boundary); resolve_preset narrows via
    # preset_for's dict.get — an invalid / non-routable label returns None → 422 below.
    # W82 / ADR-0063 — resolve_preset overlays the admin-edited global mapping so a
    # manual override applies the EDITED preset (None store → factory). cast for mypy.
    preset = await resolve_preset(
        cast(DocProfile, payload.profile), _preset_override_store(request)
    )
    if preset is None:
        raise _api_error(
            "profile.no_preset",
            f"Profile '{payload.profile}' has no routable preset.",
            "Use one of P1_sop_imgdense / P1_sop_text / P2_prose / P3_slide_imgdense / "
            "P3_slide_text / P4_scan_imgdense / P5_form.",
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    existing = await profile_store.get(kb_id, doc_id)
    if existing is None:
        raise _api_error(
            "profile.not_found",
            f"No profile for doc '{doc_id}' in kb '{kb_id}' — not yet ingested / profiled.",
            "Re-index the document so the profiler runs before overriding its profile.",
            status.HTTP_404_NOT_FOUND,
        )

    # 1. 套對應 preset 落 per-doc config (覆蓋 — explicit user action, ADR-0056 D3).
    await config_store.upsert(kb_id, doc_id, preset)
    # 2. 記 manual_override annotation (保 system auto profile/confidence/signals 不變).
    updated = existing.model_copy(update={"manual_override": payload.profile})
    await profile_store.upsert(kb_id, doc_id, updated)
    return updated


@router.patch(
    "/kb/{kb_id}/docs/{doc_id}/classification",
    response_model=DocClassificationInfo,
    dependencies=[Depends(require_role("admin"))],
)
async def set_doc_classification(
    kb_id: str,
    doc_id: str,
    payload: ClassificationUpdateRequest,
    request: Request,
    service: KbServiceDep,
) -> DocClassificationInfo:
    """ADR-0066 / W90 P2.3 — admin-only: tag a doc internal/restricted + restamp index.

    DG1 2-level classification. Persists to `doc_classification_store` FIRST (so the tag
    survives a later re-ingest via `_run_ingest_pipeline`), THEN merge-restamps every
    chunk's `classification` field in the live index with NO re-ingest
    (`IndexPopulator.update_doc_classification`). The P2.3 retrieval filter then drops
    `restricted` chunks for non-admin (internal-clearance) callers; admins bypass the
    filter entirely (`principals_for_user` → None), so they keep seeing restricted.

    Guard = `require_role("admin")` (workspace admin only) — classification is a security
    control, so admin-only is the conservative Tier-1 default (P3 may relax to
    `require_kb_acl("manage")` if KB managers need to classify their own docs).

    404 if the KB is missing / the doc has no chunks. 403 if the KB is archived. 503 if
    the classification store isn't wired (it backs the persist-on-tag + re-stamp seam).
    """
    await _verify_kb_or_404(kb_id, service)
    await _refuse_if_archived(kb_id, service)

    deps = _ingestion_deps_or_503(request)
    store = deps.doc_classification_store
    if store is None:
        raise _api_error(
            "classification.store_unavailable",
            "Classification store not configured.",
            "The in-memory fallback is wired on startup; check lifespan logs.",
            status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    engine = _engine_or_503(request)
    if not await _doc_exists_in_kb(engine, kb_id, doc_id):
        raise _api_error(
            "document.not_found",
            f"No document '{doc_id}' in kb '{kb_id}' — nothing to classify.",
            "Upload / index the document before tagging its classification.",
            status.HTTP_404_NOT_FOUND,
        )

    # 1. Persist first — so a re-ingest racing this restamp can't lose the tag.
    await store.upsert(kb_id, doc_id, payload.classification)
    # 2. Merge-restamp the live index's classification field (no re-ingest).
    restamped = await deps.populator.update_doc_classification(
        kb_id, doc_id, payload.classification
    )
    return DocClassificationInfo(
        kb_id=kb_id,
        doc_id=doc_id,
        classification=payload.classification,
        chunks_restamped=restamped,
    )


def _slugify_doc_id(filename_stem: str) -> str:
    """Slugify a filename stem into a doc_id matching Azure index-name rules.

    Lowercase + replace runs of non-[a-z0-9-] with `-` + strip leading/trailing
    dashes + collapse consecutive dashes. Returns "" on empty / fully-stripped
    input so the caller can reject with 422.
    """
    s = _DOC_ID_RE.sub("-", filename_stem.lower())
    s = re.sub(r"-+", "-", s).strip("-")
    return s


def _api_error(code: str, message: str, hint: str, http_status: int) -> HTTPException:
    """Build the uniform ApiError-envelope HTTPException.

    Matches the existing W7 D4 F4.1 error-handlers convention — `detail` is a
    `{code, message, hint}` dict that the global error-handler reads (it looks
    for the `"hint"` key per the W13 F5 structured-detail contract) and
    serializes into `{"error": {code, message, actionable_hint}}`.

    CH-002 F5 fix: the key is `"hint"` (not `"actionable_hint"`) — that's the
    name `api/error_handlers.http_exception_handler` reads; using the wrong key
    silently dropped the hint and the envelope's `actionable_hint` came back null.
    """
    return HTTPException(
        status_code=http_status,
        detail={"code": code, "message": message, "hint": hint},
    )


async def _doc_exists_in_kb(
    engine: RetrievalEngine,
    kb_id: str,
    doc_id: str,
) -> bool:
    """Check whether `doc_id` already has chunks in `kb_id`'s Azure index.

    Uses the existing `RetrievalEngine.list_documents` aggregation (kept Tier 1
    < 1000 chunks assumption). Returns False on Azure errors — fail-open lets
    the upload proceed; the worst case is a duplicate chunk_id collision in
    the index, which IndexPopulator's `mergeOrUpload` action handles
    idempotently (W2 design).
    """
    try:
        rows = await engine.list_documents(kb_id)
    except Exception:  # noqa: BLE001 — best-effort dup check; fail-open
        return False
    return any(row.get("doc_id") == doc_id for row in rows)


async def _run_ingest_pipeline(
    *,
    upload_file: UploadFile,
    kb_id: str,
    doc_id: str,
    deps: _IngestionDeps,
    service: KBService,
    force_scan: bool = False,
) -> dict[str, object]:
    """The shared ingest pipeline used by BOTH POST upload + POST reindex.

    Streams `upload_file` to a tempfile, dispatches via `select_parser`,
    runs the IngestionOrchestrator, pushes chunks to the per-KB Azure
    index, records counter updates / failure records via KBService, and
    returns the response shape (the caller picks the status= and the
    `status` field — "indexed" vs "reindexed"). Tempfile is always cleaned
    up in `finally`.
    """
    filename = upload_file.filename or ""
    ext = Path(filename).suffix.lower()
    if ext not in _SUPPORTED_EXTS:
        raise _api_error(
            "validation.unsupported_format",
            f"file extension {ext!r} not in {{.docx, .pdf, .pptx}}",
            "Convert the file to one of the supported formats.",
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    tmp_dir: str | None = None
    tmp_path: Path | None = None
    try:
        # Stream the UploadFile to a tempfile so the sync parser can read it as
        # a Path (Docling / python-pptx both want a filesystem path). The
        # spooled-temp inside UploadFile.file is sync-readable.
        #
        # CH-002 F2: name the tempfile after the *original* basename so the
        # parser's `doc_title = source.stem` reflects the real filename, not an
        # opaque `tmpXXXX` stem. `Path(filename.replace("\\", "/")).name` strips
        # every directory component (path-traversal-safe on both POSIX + Windows);
        # the file lives in a fresh `mkdtemp()` dir which is rmtree'd in `finally`.
        tmp_dir = tempfile.mkdtemp(prefix="ekp-ingest-")
        safe_name = Path(filename.replace("\\", "/")).name or f"upload{ext}"
        tmp_path = Path(tmp_dir) / safe_name
        with tmp_path.open("wb") as tmp:
            shutil.copyfileobj(upload_file.file, tmp)

        # ADR-0065 — P4 scan pre-parse guard. A scanned PDF needs Docling OCR which
        # blocks the SYNCHRONOUS ingest 8–9.5 min/file. The pypdfium2 pre-OCR probe
        # (秒級, no OCR) detects it BEFORE the slow parse; without force_scan we 422 so
        # the user can confirm via the upload UI's "仍要繼續" button. born-digital PDF
        # probes non-scan → proceeds (production-preserve); docx/pptx skip the probe.
        if ext == ".pdf" and not force_scan and is_scan_pdf(tmp_path):
            raise _api_error(
                "ingest.scan_requires_confirm",
                f"{filename!r} looks like a scanned PDF (empty text layer) — OCR will "
                "take ~8–9.5 minutes and block this request.",
                "Retry with force_scan=true to ingest it anyway (the request will be slow).",
                status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        # W20 F4.2 — read the KB's KbConfig so the orchestrator honours the
        # ADR-0028 Step-4 multimodal toggles (`extract_embedded_images`, etc).
        # `service.get` already ran upstream via `_assert_kb_exists`, so this
        # second read is a cheap in-memory lookup / single Postgres SELECT.
        # ADR-0057 — read BEFORE select_parser so the PDF parser can honour the
        # per-KB extract_embedded_images toggle (generate_picture_images).
        try:
            kb_record = await service.get(kb_id)
            kb_config = kb_record.config
        except Exception:  # noqa: BLE001 — defensive: fall back to W2 baseline
            kb_config = None
        # ADR-0057 — thread the per-KB image toggle to the PDF parser: a KB that opts
        # into images extracts born-digital PDF pictures; a text-only KB pays nothing.
        parser = select_parser(
            tmp_path,
            extract_images=bool(kb_config and kb_config.extract_embedded_images),
        )
        # BUG-009 — wire the screenshot uploader (was `uploader=None` while R12
        # blocked Azurite). The orchestrator only invokes it for a KB that opted
        # into `extract_embedded_images`, so a text-only KB pays nothing beyond a
        # lazy (no-network) client construct/close. `UseDevelopmentStorage=true`
        # in local `.env` routes the SDK to Azurite; cloud sets a real connection
        # string — the env var is the only switch, app code stays unchanged.
        settings = get_settings()
        async with ScreenshotUploader(
            connection_string=settings.azure_blob_connection_string,
            container_name=settings.azure_blob_container_screenshots,
        ) as uploader:
            orchestrator = IngestionOrchestrator(
                parser=parser,
                # W45 / ADR-0042 — per-KB image cap: use the KB's cap when set,
                # else the global-cap singleton (inherit).
                chunker=_select_chunker(deps, kb_config),
                embedder=deps.embedder,
                uploader=uploader,
            )
            # ADR-0066 / W90 P2.1 — resolve the KB's principals (5.1 KB inheritance)
            # so every emitted chunk carries the retrieval-layer ACL. fail-open: a
            # backend-less ingest resolves to [] → the P2.2 filter treats empty as
            # public (production-preserve).
            allowed_principals = await resolve_kb_principals(deps.rbac_backend, kb_id)
            # ADR-0066 / W90 P2.3 — preserve a doc's restricted tag across re-ingest /
            # reindex / backfill: read the persisted classification (admin-set via the
            # tag endpoint) and re-stamp it. No row → default "internal". Without the
            # store wired → default "internal" (production-preserve).
            classification = "internal"
            if deps.doc_classification_store is not None:
                stored = await deps.doc_classification_store.get(kb_id, doc_id)
                if stored is not None:
                    classification = stored
            result = await orchestrator.ingest(
                source=tmp_path,
                kb_id=kb_id,
                doc_id=doc_id,
                source_url=f"upload://{filename}",
                kb_config=kb_config,
                allowed_principals=allowed_principals,
                classification=classification,
            )

        now = datetime.now(UTC)

        if result.failure is not None:
            # Record the failure for the dashboard's `failed_documents` panel + raise 502.
            failure_record = FailureRecord(
                doc_id=doc_id,
                error=f"[{result.failure.stage}] {result.failure.error}",
                failed_at=now,
            )
            try:
                await service.record_doc_event(
                    kb_id,
                    append_failure=failure_record,
                    last_indexed_at=now,
                )
            except Exception:  # noqa: BLE001 — counter sync is non-fatal
                _stdlib_logger.exception(
                    "record_doc_event_failed_on_ingest_failure kb_id=%s", kb_id
                )
            stage_code = f"ingestion.{result.failure.stage}_failed"
            raise _api_error(
                stage_code,
                f"{result.failure.stage} stage failed: {result.failure.error}",
                "Check the file isn't corrupt or password-protected, then retry.",
                status.HTTP_502_BAD_GATEWAY,
            )

        # Push chunks to the per-KB Azure index (kb_id resolves via kb_id_to_index_name).
        try:
            upload_result = await deps.populator.upload(result.chunks, kb_id=kb_id)
        except Exception as exc:  # noqa: BLE001 — surface Azure REST errors as 502
            _stdlib_logger.exception("index_upload_failed kb_id=%s doc_id=%s", kb_id, doc_id)
            raise _api_error(
                "ingestion.index_failed",
                f"Azure AI Search push failed: {type(exc).__name__}: {exc}",
                "Check Azure AI Search admin-key + that the per-KB index exists "
                f"(re-create via DELETE+POST /kb/{kb_id} if needed).",
                status.HTTP_502_BAD_GATEWAY,
            ) from exc

        if upload_result.failed > 0:
            failure_record = FailureRecord(
                doc_id=doc_id,
                error=f"[index] partial — {upload_result.failed}/{upload_result.succeeded + upload_result.failed} chunks rejected",
                failed_at=now,
            )
            try:
                await service.record_doc_event(
                    kb_id,
                    append_failure=failure_record,
                    last_indexed_at=now,
                )
            except Exception:  # noqa: BLE001
                _stdlib_logger.exception(
                    "record_doc_event_failed_on_partial_index_failure kb_id=%s", kb_id
                )
            raise _api_error(
                "ingestion.index_failed",
                f"Azure AI Search partial-upload: {upload_result.failed} of "
                f"{upload_result.succeeded + upload_result.failed} chunks failed",
                "Inspect Azure AI Search index for schema mismatches; retry the upload.",
                status.HTTP_502_BAD_GATEWAY,
            )

        # All chunks indexed — sync KB counters.
        try:
            await service.record_doc_event(
                kb_id,
                documents_delta=+1,
                chunks_delta=upload_result.succeeded,
                screenshots_delta=result.images_uploaded,  # BUG-010 — feed the Images-tab counter
                last_indexed_at=now,
            )
        except Exception:  # noqa: BLE001 — counter drift is recoverable
            _stdlib_logger.exception(
                "record_doc_event_failed_on_success kb_id=%s doc_id=%s", kb_id, doc_id
            )

        logger.info(
            "doc_uploaded",
            kb_id=kb_id,
            doc_id=doc_id,
            chunks=upload_result.succeeded,
            images_uploaded=result.images_uploaded,
            images_deduped=result.images_deduped,
        )
        # W46 / ADR-0043 — best-effort persist the original upload so a later
        # UI-triggered KB-level reindex can re-parse it (the stored chunks can't be
        # re-chunked). A failure never fails the ingest — the doc just won't be
        # KB-reindexable until re-uploaded (reindex reports it as skipped_no_source).
        await upload_source_document(
            settings.azure_blob_connection_string,
            kb_id,
            doc_id,
            data=tmp_path.read_bytes(),
            filename=safe_name,
        )

        # W73 / ADR-0056 層 A — route the doc profile to a per-doc preset
        # (conservative auto-write, D6 守 — never overwrite a manual per-doc config).
        # Advisory: a routing failure never fails the ingest (doc is already indexed).
        if result.profile is not None and deps.doc_config_store is not None:
            try:
                await _route_profile_preset(
                    store=deps.doc_config_store,
                    kb_id=kb_id,
                    doc_id=doc_id,
                    profile=result.profile,
                    preset_override_store=deps.preset_override_store,
                )
            except Exception:  # noqa: BLE001 — profile routing is advisory, never fatal
                _stdlib_logger.exception("profile_routing_failed kb_id=%s doc_id=%s", kb_id, doc_id)

        # W76 / ADR-0056 層 A 段③ 前置 — persist the profile for the read surface
        # (DocumentSummary/Detail.profile). Advisory: a persist failure never fails the
        # ingest (the doc is already indexed; profile just won't show until re-index).
        if result.profile is not None and deps.doc_profile_store is not None:
            try:
                fresh = DocProfileInfo.from_result(result.profile, profiled_at=now.isoformat())
                # ADR-0058 D6 守 — re-ingest 更新 system detect 信號, 但 preserve 人手 override
                # annotation (override 後 re-index 唔失人手覆寫;config 端由 _route_profile_preset
                # D6 skip-if-manual 守).
                prior = await deps.doc_profile_store.get(kb_id, doc_id)
                if prior is not None and prior.manual_override is not None:
                    fresh = fresh.model_copy(update={"manual_override": prior.manual_override})
                await deps.doc_profile_store.upsert(kb_id, doc_id, fresh)
            except Exception:  # noqa: BLE001 — profile persist is advisory, never fatal
                _stdlib_logger.exception("profile_persist_failed kb_id=%s doc_id=%s", kb_id, doc_id)

        return {
            "doc_id": doc_id,
            "chunks_emitted": upload_result.succeeded,
            "images_uploaded": result.images_uploaded,
            "images_deduped": result.images_deduped,
        }
    finally:
        if tmp_dir is not None:
            shutil.rmtree(tmp_dir, ignore_errors=True)


async def _route_profile_preset(
    *,
    store: DocConfigStore,
    kb_id: str,
    doc_id: str,
    profile: ProfileResult,
    preset_override_store: PresetOverrideStore | None = None,
) -> None:
    """W73 / ADR-0056 層 A — conservatively auto-write the profile's per-doc preset.

    D6 admin override 守: if the doc already has a manual per-doc DocConfig, skip
    (never overwrite). D7 保守: a profile with no preset (too_small / unknown) inherits
    the per-KB / global config — no per-doc row is written.

    W82 / ADR-0063 — the preset is resolved via `resolve_preset` so an admin-edited
    global mapping override (`preset_override_store`) takes effect here. ``None`` store
    (unwired) → factory preset (production-preserve, bit-identical to pre-W82).
    """
    preset = await resolve_preset(profile.profile, preset_override_store)
    if preset is None:
        return  # too_small / unknown — inherit (D7)
    existing = await store.get(kb_id, doc_id)
    if existing is not None:
        _stdlib_logger.info(
            "profile_routing_skip_manual kb_id=%s doc_id=%s profile=%s",
            kb_id,
            doc_id,
            profile.profile,
        )
        return  # D6 — manual per-doc config wins
    await store.upsert(kb_id, doc_id, preset)
    _stdlib_logger.info(
        "profile_routing_applied kb_id=%s doc_id=%s profile=%s confidence=%.2f",
        kb_id,
        doc_id,
        profile.profile,
        profile.confidence,
    )


def _bytes_to_upload_file(data: bytes, filename: str) -> UploadFile:
    """Wrap stored source bytes as a Starlette `UploadFile` so the KB-level reindex
    path reuses `_run_ingest_pipeline` unchanged (W46 / ADR-0043) — no signature
    refactor, no risk to the live upload path. `.file` reads from an in-memory
    `BytesIO`; `.filename` carries the original ext for `select_parser`."""
    return UploadFile(file=io.BytesIO(data), filename=filename)


async def run_kb_reindex(
    *,
    kb_id: str,
    request: Request,
    service: KBService,
) -> dict[str, object]:
    """W46 / ADR-0043 — real KB-level reindex: re-ingest every doc from its stored
    original source under the KB's current config (so a UI `chunk_strategy` / image-cap
    change takes effect). Synchronous (Tier 1 — no task queue).

    Per doc, mirrors the doc-level reindex (delete chunks + counter -1, then re-ingest
    +1 via `_run_ingest_pipeline`) so KB counters stay balanced. A doc with no stored
    source (pre-W46 ingest, or a best-effort persist that failed) is skipped + reported
    under `skipped_no_source` (re-upload it via doc-level reindex to make it reindexable).
    In-place per-doc delete+reingest accepts a brief inconsistency window — production
    zero-downtime v1→v2 atomic switch stays deferred to Track A (ADR-0043).
    """
    deps = _ingestion_deps_or_503(request)
    engine = _engine_or_503(request)
    settings = get_settings()

    try:
        rows = await engine.list_documents(kb_id)
    except Exception as exc:  # noqa: BLE001 — surface Azure errors as 502
        _stdlib_logger.exception("kb_reindex_list_failed kb_id=%s", kb_id)
        raise _api_error(
            "reindex.list_failed",
            f"failed to list documents for kb_id={kb_id!r}: {type(exc).__name__}: {exc}",
            "Check Azure AI Search is reachable + the per-KB index exists.",
            status.HTTP_502_BAD_GATEWAY,
        ) from exc

    doc_ids = [str(r["doc_id"]) for r in rows if r.get("doc_id")]
    reindexed: list[str] = []
    skipped_no_source: list[str] = []
    failed: list[dict[str, str]] = []
    chunks_total = 0

    for doc_id in doc_ids:
        source = await download_source_document(
            settings.azure_blob_connection_string,
            kb_id,
            doc_id,
        )
        if source is None:
            skipped_no_source.append(doc_id)
            continue
        data, filename = source

        # Delete existing chunks + counter -1 (the re-ingest below adds +1 back) so
        # KB counters stay balanced — mirrors the doc-level reindex contract.
        now = datetime.now(UTC)
        try:
            deleted_count = await deps.populator.delete_doc(kb_id, doc_id)
            await service.record_doc_event(
                kb_id,
                documents_delta=-1,
                chunks_delta=-deleted_count,
                last_indexed_at=now,
            )
        except Exception as exc:  # noqa: BLE001 — one doc's failure must not abort the batch
            _stdlib_logger.exception(
                "kb_reindex_predelete_failed kb_id=%s doc_id=%s", kb_id, doc_id
            )
            failed.append({"doc_id": doc_id, "error": f"pre-delete: {type(exc).__name__}: {exc}"})
            continue

        try:
            body = await _run_ingest_pipeline(
                upload_file=_bytes_to_upload_file(data, filename),
                kb_id=kb_id,
                doc_id=doc_id,
                deps=deps,
                service=service,
                # ADR-0065 — KB-level reindex re-ingests EXISTING docs (already indexed);
                # a scan doc force-ingested before must not be blocked by the guard
                # mid-batch, so force here (trusted, user-initiated bulk reindex).
                force_scan=True,
            )
            reindexed.append(doc_id)
            emitted = body.get("chunks_emitted", 0)
            chunks_total += emitted if isinstance(emitted, int) else 0
        except HTTPException as exc:
            detail = exc.detail if isinstance(exc.detail, dict) else {"message": str(exc.detail)}
            failed.append({"doc_id": doc_id, "error": str(detail.get("message", exc.detail))})

    logger.info(
        "kb_reindexed",
        kb_id=kb_id,
        reindexed=len(reindexed),
        skipped_no_source=len(skipped_no_source),
        failed=len(failed),
        chunks_total=chunks_total,
    )
    return {
        "status": "reindexed",
        "kb_id": kb_id,
        "documents_total": len(doc_ids),
        "documents_reindexed": len(reindexed),
        "reindexed": reindexed,
        "skipped_no_source": skipped_no_source,
        "failed": failed,
        "chunks_total": chunks_total,
    }


async def _backfill_one_doc_profile(
    *,
    kb_id: str,
    doc_id: str,
    data: bytes,
    filename: str,
    kb_config: KbConfig | None,
    profile_store: DocProfileStore,
    config_store: DocConfigStore | None,
    preset_override_store: PresetOverrideStore | None = None,
) -> str:
    """W80 / ADR-0059 — re-parse one stored doc + compute its profile + persist,
    WITHOUT re-chunk / re-embed / re-upsert (零 retrieval 影響).

    Mirrors the ingest-time profile persist + route (W73 / W76 / ADR-0058) but skips
    every retrieval-mutating stage — backfill only writes the advisory profile + its
    preset (D6 守). Returns the computed profile label. Tempfile cleaned in `finally`.
    """
    tmp_dir = tempfile.mkdtemp(prefix="ekp-profile-backfill-")
    try:
        safe_name = Path(filename.replace("\\", "/")).name or "source"
        tmp_path = Path(tmp_dir) / safe_name
        tmp_path.write_bytes(data)

        # 對齊正常 ingest 嘅 img extraction → profiler img_density 信號一致 (ADR-0057):
        # a KB that extracts PDF/embedded pictures profiles on the same signals it would
        # at ingest time; a text-only KB pays nothing.
        parser = select_parser(
            tmp_path,
            extract_images=bool(kb_config and kb_config.extract_embedded_images),
        )
        result = parser.parse(tmp_path)
        if result.parse_failed:
            raise RuntimeError(f"parse failed: {result.parse_error or 'unknown'}")
        profile = _PROFILER.profile(result, tmp_path)

        now = datetime.now(UTC)
        # Persist the profile. D6 守 — preserve a prior manual_override (idempotent skip
        # means there's normally no prior row here, but keep the merge so a future
        # force-mode backfill never clobbers a human override).
        fresh = DocProfileInfo.from_result(profile, profiled_at=now.isoformat())
        prior = await profile_store.get(kb_id, doc_id)
        if prior is not None and prior.manual_override is not None:
            fresh = fresh.model_copy(update={"manual_override": prior.manual_override})
        await profile_store.upsert(kb_id, doc_id, fresh)

        # Route the profile's preset to per-doc config (D6 skip-if-manual config).
        if config_store is not None:
            await _route_profile_preset(
                store=config_store,
                kb_id=kb_id,
                doc_id=doc_id,
                profile=profile,
                preset_override_store=preset_override_store,
            )
        return profile.profile
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


async def run_kb_profile_backfill(
    *,
    kb_id: str,
    request: Request,
    service: KBService,
) -> dict[str, object]:
    """W80 / ADR-0059 — profile-only backfill: compute + persist a profile for every
    already-indexed doc in the KB, WITHOUT re-chunking / re-embedding / re-upserting.

    Distinct from `run_kb_reindex` (which re-ingests). The profiler only landed in
    `orchestrator.ingest()` at W73, so docs ingested before W73 carry no profile —
    their read surface (DocumentSummary/Detail.profile) is null. This backfill reuses
    the reindex source path (`download_source_document`) + the standalone profiler +
    the ingest persist/route, but drops every retrieval-mutating stage → zero impact
    on retrieval quality / already-tuned per-KB config.

    Per doc:
      - already has a profile → skip (`skipped_has_profile`, idempotent).
      - no stored source (pre-W46 ingest, or a failed best-effort persist) → skip
        (`skipped_no_source` — re-upload via doc-level reindex to make it backfillable).
      - else re-parse → profile → persist (D6 守 preserve manual_override) + route preset.
    One doc's failure never aborts the batch (`failed`). Synchronous (Tier 1).
    """
    engine = _engine_or_503(request)
    profile_store = _doc_profile_store(request)
    if profile_store is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Doc-profile store not initialized — backfill has nowhere to persist "
                "profiles (check DATABASE_URL + lifespan wiring)."
            ),
        )
    config_store = getattr(request.app.state, "doc_config_store", None)
    # W82 / ADR-0063 — effective preset routing honours the admin-edited global mapping.
    preset_override_store = _preset_override_store(request)
    settings = get_settings()

    # KB-level config read once — all docs share the KB's extract_embedded_images toggle.
    try:
        kb_record = await service.get(kb_id)
        kb_config = kb_record.config
    except Exception:  # noqa: BLE001 — defensive: fall back to no-config (text-only) profiling
        kb_config = None

    try:
        rows = await engine.list_documents(kb_id)
    except Exception as exc:  # noqa: BLE001 — surface Azure errors as 502
        _stdlib_logger.exception("profile_backfill_list_failed kb_id=%s", kb_id)
        raise _api_error(
            "backfill.list_failed",
            f"failed to list documents for kb_id={kb_id!r}: {type(exc).__name__}: {exc}",
            "Check Azure AI Search is reachable + the per-KB index exists.",
            status.HTTP_502_BAD_GATEWAY,
        ) from exc

    doc_ids = [str(r["doc_id"]) for r in rows if r.get("doc_id")]
    profiled: dict[str, str] = {}
    skipped_has_profile: list[str] = []
    skipped_no_source: list[str] = []
    failed: list[dict[str, str]] = []

    for doc_id in doc_ids:
        # Idempotent — a doc with a profile is left untouched (its manual_override, if
        # any, is preserved; re-profiling it is the override-aware W79 path, not backfill).
        if await profile_store.get(kb_id, doc_id) is not None:
            skipped_has_profile.append(doc_id)
            continue

        source = await download_source_document(
            settings.azure_blob_connection_string,
            kb_id,
            doc_id,
        )
        if source is None:
            skipped_no_source.append(doc_id)
            continue
        data, filename = source

        try:
            label = await _backfill_one_doc_profile(
                kb_id=kb_id,
                doc_id=doc_id,
                data=data,
                filename=filename,
                kb_config=kb_config,
                profile_store=profile_store,
                config_store=config_store,
                preset_override_store=preset_override_store,
            )
            profiled[doc_id] = label
        except Exception as exc:  # noqa: BLE001 — one doc's failure must not abort the batch
            _stdlib_logger.exception(
                "profile_backfill_doc_failed kb_id=%s doc_id=%s", kb_id, doc_id
            )
            failed.append({"doc_id": doc_id, "error": f"{type(exc).__name__}: {exc}"})

    logger.info(
        "kb_profile_backfilled",
        kb_id=kb_id,
        documents_total=len(doc_ids),
        profiled=len(profiled),
        skipped_has_profile=len(skipped_has_profile),
        skipped_no_source=len(skipped_no_source),
        failed=len(failed),
    )
    return {
        "status": "profiled",
        "kb_id": kb_id,
        "documents_total": len(doc_ids),
        "profiled": len(profiled),
        "skipped_has_profile": skipped_has_profile,
        "skipped_no_source": skipped_no_source,
        "failed": failed,
        "profiles": profiled,
    }


@router.post(
    "/kb/{kb_id}/documents",
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(require_kb_acl("edit"))],
)
async def upload_document(
    kb_id: str,
    request: Request,
    service: KbServiceDep,
    file: UploadFile,
    force_scan: bool = False,
) -> dict[str, object]:
    """Upload + ingest a document into a KB (per architecture.md §3.3 + ADR-0018).

    CH-001 closes CO_F3a — the W2 ingestion pipeline is now reachable via HTTP
    instead of only via scripts/run_populate_sanity.py. Per-KB Azure AI Search
    index is auto-targeted via `kb_id_to_index_name(kb_id)`.

    Status 202 on success (the response body is the indexed-doc summary, not
    a queue ticket — the ingest is synchronous in Tier 1, no background job).

    Format dispatch via `select_parser` — `.docx` → Docling, `.pdf` → Docling
    (per ADR-0019), `.pptx` → python-pptx. Other extensions → 422
    `validation.unsupported_format`.

    The orchestrator's screenshot uploader is wired (BUG-009) — blob upload runs
    when the KB opted into `extract_embedded_images`; R12 (Azurite SharedKey
    signature mismatch) is resolved via the `UseDevelopmentStorage=true`
    connection string. Text retrieval is unaffected either way per
    architecture.md §3.5 (`embedded_images` is citation-render metadata).
    """
    await _refuse_if_archived(kb_id, service)
    deps = _ingestion_deps_or_503(request)
    engine = _engine_or_503(request)

    filename = file.filename or ""
    if not filename:
        raise _api_error(
            "validation.file_required",
            "filename missing on the upload — must be a .docx / .pdf / .pptx file",
            "Re-attach the file (some uploaders strip the filename for empty bodies).",
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    doc_id = _slugify_doc_id(Path(filename).stem)
    if not doc_id:
        raise _api_error(
            "validation.invalid_doc_id",
            f"filename {filename!r} slugifies to empty — needs at least one alphanumeric character",
            "Rename the file to use lowercase letters / digits / dashes.",
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    if await _doc_exists_in_kb(engine, kb_id, doc_id):
        raise _api_error(
            "document.duplicate",
            f"doc_id={doc_id!r} already exists in kb_id={kb_id!r}",
            f"DELETE /kb/{kb_id}/documents/{doc_id} first, "
            f"or POST .../reindex to replace it in-place, or upload with a different filename.",
            status.HTTP_409_CONFLICT,
        )

    body = await _run_ingest_pipeline(
        upload_file=file,
        kb_id=kb_id,
        doc_id=doc_id,
        deps=deps,
        service=service,
        force_scan=force_scan,
    )
    return {"status": "indexed", **body}


@router.delete(
    "/kb/{kb_id}/documents/{doc_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_kb_acl("edit"))],
)
async def delete_document(
    kb_id: str,
    doc_id: str,
    request: Request,
    service: KbServiceDep,
) -> None:
    """Delete a doc's chunks from the per-KB Azure AI Search index.

    Idempotency contract: returns **204** only when chunks were actually
    deleted (count > 0); **404** when no chunks match (clean — DELETE-on-
    missing surfaces an error so the caller knows the operation was a no-op,
    not silently succeeding on a typo).

    Counter sync: `documents_delta=-1, chunks_delta=-N, last_indexed_at=now`.
    No Azurite screenshot blob cleanup yet (R12 — text retrieval unaffected;
    the thumbnails for the deleted doc become orphaned blobs which is a
    future-tier cleanup concern, not a Tier 1 blocker).
    """
    await _verify_kb_or_404(kb_id, service)
    deps = _ingestion_deps_or_503(request)

    try:
        deleted_count = await deps.populator.delete_doc(kb_id, doc_id)
    except Exception as exc:  # noqa: BLE001 — surface Azure errors as 502
        _stdlib_logger.exception("index_delete_doc_failed kb_id=%s doc_id=%s", kb_id, doc_id)
        raise _api_error(
            "index.delete_failed",
            f"Azure AI Search delete failed: {type(exc).__name__}: {exc}",
            "Inspect the Azure index state; the chunks may be partially deleted.",
            status.HTTP_502_BAD_GATEWAY,
        ) from exc

    if deleted_count == 0:
        raise _api_error(
            "document.not_found",
            f"no chunks for doc_id={doc_id!r} in kb_id={kb_id!r}",
            f"Verify the doc_id via GET /kb/{kb_id}/documents.",
            status.HTTP_404_NOT_FOUND,
        )

    try:
        await service.record_doc_event(
            kb_id,
            documents_delta=-1,
            chunks_delta=-deleted_count,
            last_indexed_at=datetime.now(UTC),
        )
    except Exception:  # noqa: BLE001 — counter drift is recoverable
        _stdlib_logger.exception(
            "record_doc_event_failed_on_delete kb_id=%s doc_id=%s", kb_id, doc_id
        )

    logger.info("doc_deleted", kb_id=kb_id, doc_id=doc_id, chunks_deleted=deleted_count)


@router.post(
    "/kb/{kb_id}/documents/{doc_id}/reindex",
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(require_kb_acl("edit"))],
)
async def reindex_document(
    kb_id: str,
    doc_id: str,
    request: Request,
    service: KbServiceDep,
    file: UploadFile,
    force_scan: bool = False,
) -> dict[str, object]:
    """Re-index a doc — atomic replace per CH-001 Decision A = (ii) replace-in-place.

    Workflow:
        1. Verify kb_id + doc_id exist (doc_id presence via Azure aggregation)
        2. Verify the uploaded file's slugified-stem == doc_id (UX safety check —
           catches "user picked the wrong file" before destructive delete)
        3. Delete existing chunks for (kb_id, doc_id)
        4. Run the same ingest pipeline as POST upload, under the SAME doc_id
        5. 202 with the response shape `{doc_id, status:"reindexed", chunks_emitted, ...}`

    Failure mid-pipeline (after delete, before re-ingest succeeds) → 502
    `reindex.partial_failure`. The KB ends up in a deleted-but-not-re-ingested
    state (observable = "doc gone"); the actionable_hint points to retry via
    POST upload (the source file is the same — re-upload reconstructs the doc).
    """
    await _refuse_if_archived(kb_id, service)
    deps = _ingestion_deps_or_503(request)
    engine = _engine_or_503(request)

    # Step 1 — doc_id must exist (we're replacing, not creating).
    if not await _doc_exists_in_kb(engine, kb_id, doc_id):
        raise _api_error(
            "document.not_found",
            f"doc_id={doc_id!r} not found in kb_id={kb_id!r} — reindex requires an existing doc",
            f"POST /kb/{kb_id}/documents to create a new doc, or check the doc_id via GET /kb/{kb_id}/documents.",
            status.HTTP_404_NOT_FOUND,
        )

    # Step 2 — uploaded-file doc_id must match the path doc_id (UX safety).
    filename = file.filename or ""
    if not filename:
        raise _api_error(
            "validation.file_required",
            "filename missing on the reindex upload",
            "Re-attach the file (some uploaders strip the filename for empty bodies).",
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        )
    uploaded_doc_id = _slugify_doc_id(Path(filename).stem)
    if uploaded_doc_id != doc_id:
        raise _api_error(
            "reindex.doc_id_mismatch",
            f"uploaded filename {filename!r} slugifies to {uploaded_doc_id!r}, "
            f"but path doc_id is {doc_id!r}",
            "Reindex requires the same source file as the original upload "
            "(rename to match the existing doc_id, or use POST /kb/{kb_id}/documents "
            "for a new doc).",
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    # Step 3 — delete existing chunks.
    try:
        deleted_count = await deps.populator.delete_doc(kb_id, doc_id)
    except Exception as exc:  # noqa: BLE001 — Azure errors → 502
        _stdlib_logger.exception("reindex_pre_delete_failed kb_id=%s doc_id=%s", kb_id, doc_id)
        raise _api_error(
            "reindex.partial_failure",
            f"failed to delete existing chunks for doc_id={doc_id!r}: {type(exc).__name__}: {exc}",
            "Retry via DELETE then POST /kb/{kb_id}/documents to recover.",
            status.HTTP_502_BAD_GATEWAY,
        ) from exc

    # Counter sync for the delete half (the re-ingest will increment counters back).
    try:
        await service.record_doc_event(
            kb_id,
            documents_delta=-1,
            chunks_delta=-deleted_count,
            last_indexed_at=datetime.now(UTC),
        )
    except Exception:  # noqa: BLE001 — counter drift recoverable
        _stdlib_logger.exception(
            "reindex_delete_counter_sync_failed kb_id=%s doc_id=%s", kb_id, doc_id
        )

    # Step 4 — run the ingest pipeline under the same doc_id (no dup check —
    # we just deleted it). The pipeline handles its own counter sync on success/failure;
    # if the re-ingest fails mid-pipeline, the KB is in a deleted-but-not-re-ingested
    # state — the 502 below surfaces that with an actionable hint.
    try:
        body = await _run_ingest_pipeline(
            upload_file=file,
            kb_id=kb_id,
            doc_id=doc_id,
            deps=deps,
            service=service,
            force_scan=force_scan,
        )
    except HTTPException as exc:
        # Re-wrap the pipeline error to flag the "partial failure" (mid-replace).
        detail_obj = exc.detail if isinstance(exc.detail, dict) else {"message": str(exc.detail)}
        original_code = detail_obj.get("code", "unknown")
        original_message = detail_obj.get("message", "")
        raise _api_error(
            "reindex.partial_failure",
            f"re-ingest after delete failed ({original_code}): {original_message}",
            "The old chunks are gone — retry via POST /kb/{kb_id}/documents with the same file.",
            status.HTTP_502_BAD_GATEWAY,
        ) from exc

    return {"status": "reindexed", **body}
