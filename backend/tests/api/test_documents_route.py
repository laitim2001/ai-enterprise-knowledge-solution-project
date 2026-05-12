"""Document routes tests (CH-001 — closes CO_F3a + ADR-0018 Phase 3 upload-side).

Covers, against `backend/api/routes/documents.py`:
- POST /kb/{kb_id}/documents (upload + ingest)
- DELETE /kb/{kb_id}/documents/{doc_id}
- POST /kb/{kb_id}/documents/{doc_id}/reindex (Decision A = (ii) replace-in-place)

And against `backend/api/routes/kb.py` (Phase 1.5 / Decision B = (β)):
- POST /kb (auto-provision per-KB Azure AI Search index)
- DELETE /kb (auto-drop per-KB Azure AI Search index)

Real Azure REST calls are `scripts/run_populate_sanity.py` smoke-script territory;
this file monkeypatches `IngestionOrchestrator` + `select_parser` and uses a
`MagicMock`-shaped IndexPopulator on `app.state.index_populator`.

Acceptance ref:spec.md §3 AC1-AC10 + AC18-AC22 + AC9.1-AC9.3.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.error_handlers import register_error_handlers
from api.routes import documents as documents_routes
from api.routes import kb as kb_routes
from api.schemas.kb import KbConfig, KbCreate
from ingestion.orchestrator import FailureRecord as IngFailureRecord
from ingestion.orchestrator import IngestionResult
from kb_management import KBService, get_kb_service
from kb_management.storage import InMemoryKBBackend

# --------------------------------------------------------------------------- #
# Fixtures / builders
# --------------------------------------------------------------------------- #


class _FakeUploadResult:
    """Shape-match for `indexing.populate.IndexUploadResult` — avoid importing the real class."""

    def __init__(self, succeeded: int, failed: int = 0, failed_keys: list[str] | None = None) -> None:
        self.succeeded = succeeded
        self.failed = failed
        self.failed_keys = failed_keys or []


def _populator_mock(
    *,
    upload_result: _FakeUploadResult | None = None,
    upload_raises: Exception | None = None,
    delete_doc_count: int = 12,
    delete_doc_raises: Exception | None = None,
    create_index_raises: Exception | None = None,
    delete_index_returns: bool = True,
    delete_index_raises: Exception | None = None,
) -> MagicMock:
    """MagicMock IndexPopulator with all four CH-001 methods as AsyncMock attrs."""
    populator = MagicMock(name="IndexPopulator")
    if upload_raises is not None:
        populator.upload = AsyncMock(side_effect=upload_raises)
    else:
        populator.upload = AsyncMock(return_value=upload_result or _FakeUploadResult(succeeded=12))

    if delete_doc_raises is not None:
        populator.delete_doc = AsyncMock(side_effect=delete_doc_raises)
    else:
        populator.delete_doc = AsyncMock(return_value=delete_doc_count)

    if create_index_raises is not None:
        populator.create_index_for_kb = AsyncMock(side_effect=create_index_raises)
    else:
        populator.create_index_for_kb = AsyncMock(return_value=None)

    if delete_index_raises is not None:
        populator.delete_index = AsyncMock(side_effect=delete_index_raises)
    else:
        populator.delete_index = AsyncMock(return_value=delete_index_returns)

    return populator


def _engine_mock(
    *, list_docs: list[dict[str, Any]] | None = None, list_raises: Exception | None = None,
) -> MagicMock:
    """MagicMock RetrievalEngine with `list_documents` AsyncMock."""
    engine = MagicMock(name="RetrievalEngine")
    if list_raises is not None:
        engine.list_documents = AsyncMock(side_effect=list_raises)
    else:
        engine.list_documents = AsyncMock(return_value=list_docs or [])
    return engine


def _patch_orchestrator(
    monkeypatch: pytest.MonkeyPatch,
    *,
    ingest_result: IngestionResult | None = None,
) -> AsyncMock:
    """Monkeypatch `select_parser` (→ dummy) + `IngestionOrchestrator` (→ stub).

    Returns the `ingest` AsyncMock so tests can assert call args / call count.
    """
    monkeypatch.setattr(documents_routes, "select_parser", lambda _path: MagicMock(name="Parser"))

    ingest_mock = AsyncMock(
        return_value=ingest_result
        or IngestionResult(
            chunks=[MagicMock(name=f"ChunkRecord-{i}") for i in range(12)],
            failure=None,
            images_uploaded=0,
            images_deduped=0,
        ),
    )

    def _orch_factory(*_args: Any, **_kwargs: Any) -> MagicMock:
        stub = MagicMock(name="IngestionOrchestrator")
        stub.ingest = ingest_mock
        return stub

    monkeypatch.setattr(documents_routes, "IngestionOrchestrator", _orch_factory)
    return ingest_mock


def _build_app(
    *,
    kb_service: KBService,
    populator: MagicMock | None = None,
    engine: MagicMock | None = None,
    include_kb_router: bool = False,
    with_error_handlers: bool = False,
) -> FastAPI:
    """FastAPI app with the two routers + injected KBService + app.state shape.

    `with_error_handlers=True` wires `api.error_handlers.register_error_handlers`
    so the route's `_api_error` HTTPException is serialized into the production
    `{"error": {code, message, actionable_hint}}` envelope (CH-002 F5 — verifies
    the route-supplied hint actually reaches the response). The default keeps the
    raw `{"detail": {...}}` shape the bulk of these tests assert against.
    """
    app = FastAPI()
    app.include_router(documents_routes.router)
    if include_kb_router:
        app.include_router(kb_routes.router)
    if with_error_handlers:
        register_error_handlers(app)
    app.dependency_overrides[get_kb_service] = lambda: kb_service

    # Embedder + chunker exist only to satisfy `_ingestion_deps_or_503`;they are
    # never called when `IngestionOrchestrator` is monkeypatched.
    if populator is not None:
        app.state.embedder = MagicMock(name="Embedder")
        app.state.ingestion_chunker = MagicMock(name="Chunker")
        app.state.index_populator = populator
    else:
        app.state.embedder = None
        app.state.ingestion_chunker = None
        app.state.index_populator = None

    app.state.retrieval_engine = engine
    return app


@pytest.fixture
async def kb_service_with_drive() -> KBService:
    service = KBService(InMemoryKBBackend())
    await service.create(KbCreate(
        kb_id="drive_user_manuals", name="Drive", description="", config=KbConfig(),
    ))
    return service


@pytest.fixture
async def kb_service_empty() -> KBService:
    return KBService(InMemoryKBBackend())


def _docx_files(
    filename: str = "doc-a.docx", content: bytes = b"\x00\x01\x02",
) -> dict[str, tuple[str, bytes, str]]:
    """Multipart `files=` payload helper."""
    return {
        "file": (
            filename,
            content,
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ),
    }


# =========================================================================== #
# POST /kb/{kb_id}/documents — AC1-AC7, AC10, AC22
# =========================================================================== #


@pytest.mark.asyncio
async def test_upload_happy_path_returns_202_indexed(
    kb_service_with_drive: KBService, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC1 — POST .docx happy path → 202 with the indexed-doc body."""
    ingest_mock = _patch_orchestrator(monkeypatch)
    populator = _populator_mock(upload_result=_FakeUploadResult(succeeded=12))
    engine = _engine_mock(list_docs=[])  # no dup

    app = _build_app(kb_service=kb_service_with_drive, populator=populator, engine=engine)
    client = TestClient(app)

    resp = client.post("/kb/drive_user_manuals/documents", files=_docx_files("vendor-manual.docx"))
    assert resp.status_code == 202, resp.text

    body = resp.json()
    assert body == {
        "status": "indexed",
        "doc_id": "vendor-manual",
        "chunks_emitted": 12,
        "images_uploaded": 0,
        "images_deduped": 0,
    }
    ingest_mock.assert_awaited_once()
    populator.upload.assert_awaited_once()


@pytest.mark.asyncio
async def test_upload_targets_per_kb_index_not_legacy(
    kb_service_with_drive: KBService, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC22 — `populator.upload` must be called with `kb_id=<kb_id>` (not None),
    so chunks land in the per-KB index `ekp-kb-{kb_id}-v1`, NOT the legacy."""
    _patch_orchestrator(monkeypatch)
    populator = _populator_mock()
    engine = _engine_mock(list_docs=[])

    app = _build_app(kb_service=kb_service_with_drive, populator=populator, engine=engine)
    client = TestClient(app)

    resp = client.post("/kb/drive_user_manuals/documents", files=_docx_files("manual.docx"))
    assert resp.status_code == 202

    populator.upload.assert_awaited_once()
    assert populator.upload.call_args.kwargs["kb_id"] == "drive_user_manuals"


@pytest.mark.asyncio
async def test_upload_records_counter_event_on_success(
    kb_service_with_drive: KBService, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC10 — `KBService.record_doc_event(documents_delta=+1, chunks_delta=N)` on success."""
    _patch_orchestrator(monkeypatch)
    populator = _populator_mock(upload_result=_FakeUploadResult(succeeded=7))
    engine = _engine_mock(list_docs=[])

    record_spy = AsyncMock(return_value=MagicMock())
    kb_service_with_drive.record_doc_event = record_spy  # type: ignore[method-assign]

    app = _build_app(kb_service=kb_service_with_drive, populator=populator, engine=engine)
    client = TestClient(app)

    resp = client.post("/kb/drive_user_manuals/documents", files=_docx_files("m.docx"))
    assert resp.status_code == 202

    record_spy.assert_awaited()
    kwargs = record_spy.call_args.kwargs
    assert kwargs["documents_delta"] == 1
    assert kwargs["chunks_delta"] == 7
    assert kwargs["last_indexed_at"] is not None


@pytest.mark.asyncio
@pytest.mark.parametrize("filename,mime", [
    ("doc-b.pdf", "application/pdf"),
    ("deck.pptx", "application/vnd.openxmlformats-officedocument.presentationml.presentation"),
])
async def test_upload_supports_pdf_and_pptx(
    kb_service_with_drive: KBService,
    monkeypatch: pytest.MonkeyPatch,
    filename: str,
    mime: str,
) -> None:
    """AC2 — .pdf (per ADR-0019) and .pptx (W3 D5) also succeed via the same path."""
    _patch_orchestrator(monkeypatch)
    populator = _populator_mock()
    engine = _engine_mock(list_docs=[])

    app = _build_app(kb_service=kb_service_with_drive, populator=populator, engine=engine)
    client = TestClient(app)

    resp = client.post(
        "/kb/drive_user_manuals/documents",
        files={"file": (filename, b"\x00", mime)},
    )
    assert resp.status_code == 202, resp.text


@pytest.mark.asyncio
async def test_upload_unsupported_format_returns_422(
    kb_service_with_drive: KBService, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC3 — .txt is not in {.docx, .pdf, .pptx} → 422 `validation.unsupported_format`."""
    _patch_orchestrator(monkeypatch)
    populator = _populator_mock()
    engine = _engine_mock(list_docs=[])

    app = _build_app(kb_service=kb_service_with_drive, populator=populator, engine=engine)
    client = TestClient(app)

    resp = client.post(
        "/kb/drive_user_manuals/documents",
        files={"file": ("notes.txt", b"hello", "text/plain")},
    )
    assert resp.status_code == 422
    assert resp.json()["detail"]["code"] == "validation.unsupported_format"


@pytest.mark.asyncio
async def test_upload_unknown_kb_returns_404(
    kb_service_empty: KBService, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC4 — POST to unknown kb_id → 404 before any orchestrator/populator call."""
    _patch_orchestrator(monkeypatch)
    populator = _populator_mock()
    engine = _engine_mock(list_docs=[])

    app = _build_app(kb_service=kb_service_empty, populator=populator, engine=engine)
    client = TestClient(app)

    resp = client.post("/kb/nonexistent/documents", files=_docx_files())
    assert resp.status_code == 404
    populator.upload.assert_not_awaited()


@pytest.mark.asyncio
async def test_upload_no_populator_returns_503(
    kb_service_with_drive: KBService, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC5 — `app.state.index_populator is None` → 503 (azure cred missing)."""
    _patch_orchestrator(monkeypatch)
    engine = _engine_mock(list_docs=[])

    app = _build_app(kb_service=kb_service_with_drive, populator=None, engine=engine)
    client = TestClient(app)

    resp = client.post("/kb/drive_user_manuals/documents", files=_docx_files())
    assert resp.status_code == 503


@pytest.mark.asyncio
@pytest.mark.parametrize("stage,expected_code", [
    ("parse", "ingestion.parse_failed"),
    ("embed", "ingestion.embed_failed"),
])
async def test_upload_parse_or_embed_failure_returns_502(
    kb_service_with_drive: KBService,
    monkeypatch: pytest.MonkeyPatch,
    stage: str,
    expected_code: str,
) -> None:
    """AC6 — orchestrator returns FailureRecord(stage=...) → 502 `ingestion.{stage}_failed`."""
    failure = IngFailureRecord(doc_id="doc-a", stage=stage, error=f"{stage} broke")
    failed_result = IngestionResult(chunks=[], failure=failure, images_uploaded=0, images_deduped=0)
    _patch_orchestrator(monkeypatch, ingest_result=failed_result)
    populator = _populator_mock()
    engine = _engine_mock(list_docs=[])

    app = _build_app(kb_service=kb_service_with_drive, populator=populator, engine=engine)
    client = TestClient(app)

    resp = client.post("/kb/drive_user_manuals/documents", files=_docx_files("doc-a.docx"))
    assert resp.status_code == 502
    assert resp.json()["detail"]["code"] == expected_code
    populator.upload.assert_not_awaited()  # didn't reach the populator


@pytest.mark.asyncio
async def test_upload_index_partial_failure_returns_502(
    kb_service_with_drive: KBService, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC6 — `populator.upload` returns `failed > 0` → 502 `ingestion.index_failed`."""
    _patch_orchestrator(monkeypatch)
    populator = _populator_mock(
        upload_result=_FakeUploadResult(succeeded=8, failed=4, failed_keys=["c-9", "c-10", "c-11", "c-12"]),
    )
    engine = _engine_mock(list_docs=[])

    app = _build_app(kb_service=kb_service_with_drive, populator=populator, engine=engine)
    client = TestClient(app)

    resp = client.post("/kb/drive_user_manuals/documents", files=_docx_files())
    assert resp.status_code == 502
    assert resp.json()["detail"]["code"] == "ingestion.index_failed"


@pytest.mark.asyncio
async def test_upload_duplicate_doc_id_returns_409(
    kb_service_with_drive: KBService, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC7 — engine.list_documents already has the doc_id → 409 `document.duplicate`."""
    _patch_orchestrator(monkeypatch)
    populator = _populator_mock()
    engine = _engine_mock(list_docs=[{"doc_id": "manual"}])

    app = _build_app(kb_service=kb_service_with_drive, populator=populator, engine=engine)
    client = TestClient(app)

    resp = client.post("/kb/drive_user_manuals/documents", files=_docx_files("manual.docx"))
    assert resp.status_code == 409
    assert resp.json()["detail"]["code"] == "document.duplicate"
    populator.upload.assert_not_awaited()


# =========================================================================== #
# DELETE /kb/{kb_id}/documents/{doc_id} — AC8
# =========================================================================== #


@pytest.mark.asyncio
async def test_delete_happy_returns_204_and_records_counter(
    kb_service_with_drive: KBService,
) -> None:
    """AC8 happy path + AC10 counter event:204, `populator.delete_doc` called,
    `record_doc_event(documents_delta=-1, chunks_delta=-N)`."""
    populator = _populator_mock(delete_doc_count=5)

    record_spy = AsyncMock(return_value=MagicMock())
    kb_service_with_drive.record_doc_event = record_spy  # type: ignore[method-assign]

    app = _build_app(kb_service=kb_service_with_drive, populator=populator, engine=None)
    client = TestClient(app)

    resp = client.delete("/kb/drive_user_manuals/documents/doc-a")
    assert resp.status_code == 204
    populator.delete_doc.assert_awaited_once_with("drive_user_manuals", "doc-a")

    record_spy.assert_awaited_once()
    kwargs = record_spy.call_args.kwargs
    assert kwargs["documents_delta"] == -1
    assert kwargs["chunks_delta"] == -5


@pytest.mark.asyncio
async def test_delete_not_found_returns_404(kb_service_with_drive: KBService) -> None:
    """AC8 — `delete_doc` returns 0 → 404 `document.not_found` (clean idempotency)."""
    populator = _populator_mock(delete_doc_count=0)

    app = _build_app(kb_service=kb_service_with_drive, populator=populator, engine=None)
    client = TestClient(app)

    resp = client.delete("/kb/drive_user_manuals/documents/doc-missing")
    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "document.not_found"


@pytest.mark.asyncio
async def test_delete_azure_error_returns_502(kb_service_with_drive: KBService) -> None:
    """AC8 — `delete_doc` raises → 502 `index.delete_failed`."""
    populator = _populator_mock(delete_doc_raises=ConnectionError("Azure unreachable"))

    app = _build_app(kb_service=kb_service_with_drive, populator=populator, engine=None)
    client = TestClient(app)

    resp = client.delete("/kb/drive_user_manuals/documents/doc-a")
    assert resp.status_code == 502
    assert resp.json()["detail"]["code"] == "index.delete_failed"


# =========================================================================== #
# POST /kb/{kb_id}/documents/{doc_id}/reindex — AC9.1-AC9.3 (Decision A = (ii))
# =========================================================================== #


@pytest.mark.asyncio
async def test_reindex_happy_returns_202_reindexed(
    kb_service_with_drive: KBService, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC9.1 — happy path:doc exists → delete_doc → ingest → 202 `reindexed`."""
    _patch_orchestrator(monkeypatch)
    populator = _populator_mock(delete_doc_count=8, upload_result=_FakeUploadResult(succeeded=15))
    engine = _engine_mock(list_docs=[{"doc_id": "manual"}])

    app = _build_app(kb_service=kb_service_with_drive, populator=populator, engine=engine)
    client = TestClient(app)

    resp = client.post(
        "/kb/drive_user_manuals/documents/manual/reindex", files=_docx_files("manual.docx"),
    )
    assert resp.status_code == 202, resp.text
    body = resp.json()
    assert body["status"] == "reindexed"
    assert body["doc_id"] == "manual"
    assert body["chunks_emitted"] == 15

    populator.delete_doc.assert_awaited_once_with("drive_user_manuals", "manual")
    populator.upload.assert_awaited_once()


@pytest.mark.asyncio
async def test_reindex_doc_not_found_returns_404(
    kb_service_with_drive: KBService, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC9 — `_doc_exists_in_kb` returns False → 404 `document.not_found`."""
    _patch_orchestrator(monkeypatch)
    populator = _populator_mock()
    engine = _engine_mock(list_docs=[])  # doc doesn't exist

    app = _build_app(kb_service=kb_service_with_drive, populator=populator, engine=engine)
    client = TestClient(app)

    resp = client.post(
        "/kb/drive_user_manuals/documents/ghost/reindex", files=_docx_files("ghost.docx"),
    )
    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "document.not_found"
    populator.delete_doc.assert_not_awaited()  # didn't even start the destructive path


@pytest.mark.asyncio
async def test_reindex_doc_id_mismatch_returns_422(
    kb_service_with_drive: KBService, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC9 — uploaded filename slugifies to a different doc_id → 422 `reindex.doc_id_mismatch`.

    Path doc_id = "manual", but the uploaded filename is "wrong-doc.docx" → 422.
    """
    _patch_orchestrator(monkeypatch)
    populator = _populator_mock()
    engine = _engine_mock(list_docs=[{"doc_id": "manual"}])

    app = _build_app(kb_service=kb_service_with_drive, populator=populator, engine=engine)
    client = TestClient(app)

    resp = client.post(
        "/kb/drive_user_manuals/documents/manual/reindex", files=_docx_files("wrong-doc.docx"),
    )
    assert resp.status_code == 422
    assert resp.json()["detail"]["code"] == "reindex.doc_id_mismatch"
    populator.delete_doc.assert_not_awaited()


@pytest.mark.asyncio
async def test_reindex_missing_filename_returns_422(
    kb_service_with_drive: KBService, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC9.2 — empty filename on the multipart part → 422 (FastAPI's own
    `UploadFile` validation fires first; the destructive `delete_doc` is never
    reached). The route's own `validation.file_required` guard is defensive code
    for an unreachable-via-HTTP path."""
    _patch_orchestrator(monkeypatch)
    populator = _populator_mock()
    engine = _engine_mock(list_docs=[{"doc_id": "manual"}])

    app = _build_app(kb_service=kb_service_with_drive, populator=populator, engine=engine)
    client = TestClient(app)

    resp = client.post(
        "/kb/drive_user_manuals/documents/manual/reindex",
        files={"file": ("", b"\x00", "application/octet-stream")},
    )
    assert resp.status_code == 422
    populator.delete_doc.assert_not_awaited()


@pytest.mark.asyncio
async def test_reindex_mid_pipeline_failure_returns_502_partial(
    kb_service_with_drive: KBService, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC9.3 — orchestrator returns FailureRecord AFTER delete_doc was called
    → 502 `reindex.partial_failure` (the doc is now in a deleted-but-not-
    re-ingested state; the hint points to retry via POST upload)."""
    failure = IngFailureRecord(doc_id="manual", stage="embed", error="azure 5xx mid-embed")
    failed_result = IngestionResult(chunks=[], failure=failure, images_uploaded=0, images_deduped=0)
    _patch_orchestrator(monkeypatch, ingest_result=failed_result)
    populator = _populator_mock(delete_doc_count=8)
    engine = _engine_mock(list_docs=[{"doc_id": "manual"}])

    app = _build_app(kb_service=kb_service_with_drive, populator=populator, engine=engine)
    client = TestClient(app)

    resp = client.post(
        "/kb/drive_user_manuals/documents/manual/reindex", files=_docx_files("manual.docx"),
    )
    assert resp.status_code == 502
    assert resp.json()["detail"]["code"] == "reindex.partial_failure"
    populator.delete_doc.assert_awaited_once()  # delete DID run before the failure


# =========================================================================== #
# POST /kb + DELETE /kb (Decision B = (β)) — AC18-AC21
# =========================================================================== #


@pytest.mark.asyncio
async def test_post_kb_calls_create_index_for_kb(kb_service_empty: KBService) -> None:
    """AC18 — POST /kb success → `populator.create_index_for_kb(kb_id)` called once;
    no rollback;the KB is queryable via GET /kb/{kb_id} (201 storage record present)."""
    populator = _populator_mock()

    app = _build_app(
        kb_service=kb_service_empty, populator=populator, engine=None, include_kb_router=True,
    )
    client = TestClient(app)

    resp = client.post("/kb", json={
        "kb_id": "ch001-smoke", "name": "CH-001 smoke", "description": "", "config": {},
    })
    assert resp.status_code == 201, resp.text
    populator.create_index_for_kb.assert_awaited_once_with("ch001-smoke")

    # Storage record present (not rolled back).
    get_resp = client.get("/kb/ch001-smoke")
    assert get_resp.status_code == 200


@pytest.mark.asyncio
async def test_post_kb_index_create_fail_rolls_back_returns_502(
    kb_service_empty: KBService,
) -> None:
    """AC19 — `create_index_for_kb` raises → 502 `index.create_failed` +
    `service.delete(kb_id)` rollback (verify via GET → 404 after the failed POST)."""
    populator = _populator_mock(create_index_raises=ValueError("Azure rejected kb_id: uppercase"))

    app = _build_app(
        kb_service=kb_service_empty, populator=populator, engine=None, include_kb_router=True,
    )
    client = TestClient(app)

    resp = client.post("/kb", json={
        "kb_id": "BadKbId", "name": "x", "description": "", "config": {},
    })
    assert resp.status_code == 502
    populator.create_index_for_kb.assert_awaited_once()
    # Storage record rolled back.
    get_resp = client.get("/kb/BadKbId")
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_kb_calls_delete_index(kb_service_with_drive: KBService) -> None:
    """AC20 — DELETE /kb success → `populator.delete_index(kb_id)` called + 204."""
    populator = _populator_mock(delete_index_returns=True)

    app = _build_app(
        kb_service=kb_service_with_drive, populator=populator, engine=None, include_kb_router=True,
    )
    client = TestClient(app)

    resp = client.delete("/kb/drive_user_manuals")
    assert resp.status_code == 204
    populator.delete_index.assert_awaited_once_with("drive_user_manuals")


@pytest.mark.asyncio
async def test_delete_kb_index_already_gone_fail_soft_returns_204(
    kb_service_with_drive: KBService,
) -> None:
    """AC21 — `delete_index` returns False (404 / index already gone) → still 204
    (fail-soft for pre-CH-001 legacy KBs or partial-create rollback orphans)."""
    populator = _populator_mock(delete_index_returns=False)

    app = _build_app(
        kb_service=kb_service_with_drive, populator=populator, engine=None, include_kb_router=True,
    )
    client = TestClient(app)

    resp = client.delete("/kb/drive_user_manuals")
    assert resp.status_code == 204
    populator.delete_index.assert_awaited_once_with("drive_user_manuals")


# =========================================================================== #
# CH-002 — F5 (route hint reaches the {"error": ...} envelope) + F2 (tempfile
# named after the original basename, traversal-safe).
# =========================================================================== #


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("scenario", "expected_status", "expected_code", "hint_substring"),
    [
        ("duplicate", 409, "document.duplicate", "reindex"),
        ("unsupported_format", 422, "validation.unsupported_format", "Convert"),
        ("not_found_delete", 404, "document.not_found", "Verify the doc_id"),
        ("reindex_mismatch", 422, "reindex.doc_id_mismatch", "Reindex requires"),
    ],
)
async def test_ch002_f5_route_hint_surfaces_in_error_envelope(
    kb_service_with_drive: KBService,
    monkeypatch: pytest.MonkeyPatch,
    scenario: str,
    expected_status: int,
    expected_code: str,
    hint_substring: str,
) -> None:
    """CH-002 F5 (AC5) — when the global error handlers are registered, the
    route-supplied `actionable_hint` is non-null in the response envelope (the
    `_api_error` detail uses the `"hint"` key the handler reads — previously it
    used `"actionable_hint"` which the handler dropped, leaving the envelope's
    `actionable_hint` null)."""
    _patch_orchestrator(monkeypatch)

    if scenario == "duplicate":
        engine = _engine_mock(list_docs=[{"doc_id": "vendor-manual"}])  # dup
        app = _build_app(
            kb_service=kb_service_with_drive,
            populator=_populator_mock(),
            engine=engine,
            with_error_handlers=True,
        )
        resp = TestClient(app).post(
            "/kb/drive_user_manuals/documents", files=_docx_files("vendor-manual.docx"),
        )
    elif scenario == "unsupported_format":
        app = _build_app(
            kb_service=kb_service_with_drive,
            populator=_populator_mock(),
            engine=_engine_mock(list_docs=[]),
            with_error_handlers=True,
        )
        resp = TestClient(app).post(
            "/kb/drive_user_manuals/documents",
            files={"file": ("notes.txt", b"hello", "text/plain")},
        )
    elif scenario == "not_found_delete":
        app = _build_app(
            kb_service=kb_service_with_drive,
            populator=_populator_mock(delete_doc_count=0),  # no chunks → 404
            engine=None,
            with_error_handlers=True,
        )
        resp = TestClient(app).delete("/kb/drive_user_manuals/documents/ghost-doc")
    else:  # reindex_mismatch
        engine = _engine_mock(list_docs=[{"doc_id": "real-doc"}])  # doc exists
        app = _build_app(
            kb_service=kb_service_with_drive,
            populator=_populator_mock(),
            engine=engine,
            with_error_handlers=True,
        )
        resp = TestClient(app).post(
            "/kb/drive_user_manuals/documents/real-doc/reindex",
            files=_docx_files("wrong-name.docx"),
        )

    assert resp.status_code == expected_status, resp.text
    err = resp.json()["error"]
    assert err["code"] == expected_code
    assert err["actionable_hint"] is not None
    assert hint_substring.lower() in err["actionable_hint"].lower()


@pytest.mark.asyncio
async def test_ch002_f2_tempfile_named_after_original_basename(
    kb_service_with_drive: KBService, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """CH-002 F2 (AC7) — the ingest pipeline writes the upload to a tempfile
    whose name is the *original* basename, so the parser's `doc_title =
    source.stem` is the real stem rather than an opaque `tmpXXXX`."""
    ingest_mock = _patch_orchestrator(monkeypatch)
    app = _build_app(
        kb_service=kb_service_with_drive, populator=_populator_mock(), engine=_engine_mock(list_docs=[]),
    )
    resp = TestClient(app).post(
        "/kb/drive_user_manuals/documents", files=_docx_files("My Report 2026.docx"),
    )
    assert resp.status_code == 202, resp.text
    source: Path = ingest_mock.await_args.kwargs["source"]
    assert source.name == "My Report 2026.docx"
    assert source.stem == "My Report 2026"
    assert not source.name.startswith("tmp")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "evil_filename",
    ["../../etc/passwd.docx", r"..\..\evil.docx", "/abs/path/leak.docx"],
)
async def test_ch002_f2_upload_filename_traversal_stripped(
    kb_service_with_drive: KBService, monkeypatch: pytest.MonkeyPatch, evil_filename: str,
) -> None:
    """CH-002 F2 (AC7 / R1) — directory components in the upload filename are
    stripped before building the tempfile path; the file never escapes the
    fresh `mkdtemp()` dir."""
    ingest_mock = _patch_orchestrator(monkeypatch)
    app = _build_app(
        kb_service=kb_service_with_drive, populator=_populator_mock(), engine=_engine_mock(list_docs=[]),
    )
    resp = TestClient(app).post(
        "/kb/drive_user_manuals/documents",
        files={
            "file": (
                evil_filename, b"x",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ),
        },
    )
    assert resp.status_code == 202, resp.text
    source: Path = ingest_mock.await_args.kwargs["source"]
    assert "/" not in source.name and "\\" not in source.name
    assert ".." not in source.parts
    assert source.is_absolute()  # lives inside the mkdtemp() dir, an absolute path
