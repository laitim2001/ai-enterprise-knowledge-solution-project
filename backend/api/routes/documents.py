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
"""

import json
import logging
import re
import shutil
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, status

from api.schemas.kb import FailureRecord
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
from ingestion.embedding.base import Embedder
from ingestion.orchestrator import IngestionOrchestrator
from ingestion.parsers import select_parser
from ingestion.screenshots.uploader import ScreenshotUploader
from kb_management import KBNotFoundError, KBService, get_kb_service
from retrieval.retrieval_engine import RetrievalEngine
from storage.settings import get_settings

logger = structlog.get_logger(__name__)
_stdlib_logger = logging.getLogger(__name__)

_SUPPORTED_EXTS = {".docx", ".pdf", ".pptx"}
_DOC_ID_RE = re.compile(r"[^a-z0-9-]+")

router = APIRouter()

KbServiceDep = Annotated[KBService, Depends(get_kb_service)]


@dataclass(slots=True, frozen=True)
class _IngestionDeps:
    """CH-001 — the four ingestion-side services resolved from app.state.

    Embedder + IndexPopulator are lifespan-managed Azure clients (one per app
    lifetime); Chunker is stateless. Parser is constructed per-request via
    select_parser(file_extension) inside the route handlers (depends on input
    file type, can't be lifespan-bound).
    """

    embedder: Embedder
    populator: IndexPopulator
    chunker: Chunker


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
    if embedder is None or populator is None or chunker is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Ingestion services not initialized — check Azure OpenAI + AI Search "
                ".env config (AZURE_OPENAI_API_KEY + AZURE_SEARCH_ADMIN_KEY)."
            ),
        )
    return _IngestionDeps(embedder=embedder, populator=populator, chunker=chunker)


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
    kb_id: str, request: Request, service: KbServiceDep,
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

    return [DocumentSummary(**row) for row in rows]


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
                    url=blob_url,
                    doc_id=doc_id,
                    doc_name=doc_title,
                    ocr_text=str(img.get("alt_text") or ""),
                )

    items = list(seen.values())
    total = len(items)
    paginated = items[offset : offset + limit]
    return KbImagesResponse(items=paginated, total=total, limit=limit, offset=offset)


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
            seen_images[sha] = ImageRef(
                blob_url=blob_url,
                alt_text=str(img.get("alt_text") or ""),
                checksum_sha256=sha,
                width=int(img.get("width") or 0),
                height=int(img.get("height") or 0),
            )

    low_value_count = sum(1 for c in chunks if c.get("low_value_flag"))

    # Pull chunk_strategy from KbConfig (KB already verified via _verify_kb_or_404).
    kb_record = await service.get(kb_id)
    chunk_strategy = kb_record.config.chunk_strategy

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
    engine: RetrievalEngine, kb_id: str, doc_id: str,
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

        parser = select_parser(tmp_path)
        # W20 F4.2 — read the KB's KbConfig so the orchestrator honours the
        # ADR-0028 Step-4 multimodal toggles (`extract_embedded_images`, etc).
        # `service.get` already ran upstream via `_assert_kb_exists`, so this
        # second read is a cheap in-memory lookup / single Postgres SELECT.
        try:
            kb_record = await service.get(kb_id)
            kb_config = kb_record.config
        except Exception:  # noqa: BLE001 — defensive: fall back to W2 baseline
            kb_config = None
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
                chunker=deps.chunker,
                embedder=deps.embedder,
                uploader=uploader,
            )
            result = await orchestrator.ingest(
                source=tmp_path,
                kb_id=kb_id,
                doc_id=doc_id,
                source_url=f"upload://{filename}",
                kb_config=kb_config,
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
                    kb_id, append_failure=failure_record, last_indexed_at=now,
                )
            except Exception:  # noqa: BLE001 — counter sync is non-fatal
                _stdlib_logger.exception("record_doc_event_failed_on_ingest_failure kb_id=%s", kb_id)
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
                    kb_id, append_failure=failure_record, last_indexed_at=now,
                )
            except Exception:  # noqa: BLE001
                _stdlib_logger.exception("record_doc_event_failed_on_partial_index_failure kb_id=%s", kb_id)
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
                last_indexed_at=now,
            )
        except Exception:  # noqa: BLE001 — counter drift is recoverable
            _stdlib_logger.exception("record_doc_event_failed_on_success kb_id=%s doc_id=%s", kb_id, doc_id)

        logger.info(
            "doc_uploaded",
            kb_id=kb_id,
            doc_id=doc_id,
            chunks=upload_result.succeeded,
            images_uploaded=result.images_uploaded,
            images_deduped=result.images_deduped,
        )
        return {
            "doc_id": doc_id,
            "chunks_emitted": upload_result.succeeded,
            "images_uploaded": result.images_uploaded,
            "images_deduped": result.images_deduped,
        }
    finally:
        if tmp_dir is not None:
            shutil.rmtree(tmp_dir, ignore_errors=True)


@router.post("/kb/{kb_id}/documents", status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    kb_id: str,
    request: Request,
    service: KbServiceDep,
    file: UploadFile,
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
        upload_file=file, kb_id=kb_id, doc_id=doc_id, deps=deps, service=service,
    )
    return {"status": "indexed", **body}


@router.delete("/kb/{kb_id}/documents/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    kb_id: str, doc_id: str, request: Request, service: KbServiceDep,
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
        _stdlib_logger.exception("record_doc_event_failed_on_delete kb_id=%s doc_id=%s", kb_id, doc_id)

    logger.info("doc_deleted", kb_id=kb_id, doc_id=doc_id, chunks_deleted=deleted_count)


@router.post("/kb/{kb_id}/documents/{doc_id}/reindex", status_code=status.HTTP_202_ACCEPTED)
async def reindex_document(
    kb_id: str,
    doc_id: str,
    request: Request,
    service: KbServiceDep,
    file: UploadFile,
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
            kb_id, documents_delta=-1, chunks_delta=-deleted_count,
            last_indexed_at=datetime.now(UTC),
        )
    except Exception:  # noqa: BLE001 — counter drift recoverable
        _stdlib_logger.exception("reindex_delete_counter_sync_failed kb_id=%s doc_id=%s", kb_id, doc_id)

    # Step 4 — run the ingest pipeline under the same doc_id (no dup check —
    # we just deleted it). The pipeline handles its own counter sync on success/failure;
    # if the re-ingest fails mid-pipeline, the KB is in a deleted-but-not-re-ingested
    # state — the 502 below surfaces that with an actionable hint.
    try:
        body = await _run_ingest_pipeline(
            upload_file=file, kb_id=kb_id, doc_id=doc_id, deps=deps, service=service,
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
