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
from api.schemas.listing import DocumentSummary
from indexing.populate import IndexPopulator
from ingestion.chunker.base import Chunker
from ingestion.embedding.base import Embedder
from ingestion.orchestrator import IngestionOrchestrator
from ingestion.parsers import select_parser
from kb_management import KBNotFoundError, KBService, get_kb_service
from retrieval.retrieval_engine import RetrievalEngine

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
        orchestrator = IngestionOrchestrator(
            parser=parser,
            chunker=deps.chunker,
            embedder=deps.embedder,
            uploader=None,  # R12 — Azurite signature mismatch; screenshot blob upload skipped
        )
        result = await orchestrator.ingest(
            source=tmp_path,
            kb_id=kb_id,
            doc_id=doc_id,
            source_url=f"upload://{filename}",
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

    `uploader=None` on the orchestrator — R12 Azurite signature mismatch is
    still open; screenshot blob upload is skipped (text retrieval unaffected
    per architecture.md §3.5 ChunkRecord schema; citation thumbnails will be
    empty until R12 is fixed at W16+ cloud Blob switch).
    """
    await _verify_kb_or_404(kb_id, service)
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
    await _verify_kb_or_404(kb_id, service)
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
