"""KB-level reindex endpoint tests (W16 F5.3.1 CO_F3c closure).

Per W16 plan F5.3 acceptance criteria + Decision B.1 (Azure cleanup defer
Track A;in-memory baseline preserved). Coverage:
- Happy path: kb_id valid → 202 ACCEPTED + task_id mock
- KB not found: 404
- Per-doc reindex still 501 (Karpathy §1.3 surgical: untouched scope verify)
- DELETE behavior unchanged (Decision B.1 docstring annotation only)
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routes import documents as documents_routes
from api.routes import kb as kb_routes
from api.schemas.kb import KbConfig, KbCreate
from kb_management import KBService, get_kb_service
from kb_management.storage import InMemoryKBBackend


def _build_app(kb_service: KBService) -> FastAPI:
    app = FastAPI()
    app.include_router(kb_routes.router)
    app.include_router(documents_routes.router)
    app.dependency_overrides[get_kb_service] = lambda: kb_service
    return app


@pytest.fixture
async def kb_service_with_drive() -> KBService:
    service = KBService(InMemoryKBBackend())
    await service.create(KbCreate(
        kb_id="drive_user_manuals",
        name="Drive",
        description="",
        config=KbConfig(),
    ))
    return service


@pytest.fixture
async def kb_service_empty() -> KBService:
    return KBService(InMemoryKBBackend())


@pytest.mark.asyncio
async def test_reindex_kb_happy_path(kb_service_with_drive: KBService) -> None:
    """POST /kb/{kb_id}/reindex returns 202 ACCEPTED + mock task_id."""
    app = _build_app(kb_service_with_drive)
    client = TestClient(app)

    resp = client.post("/kb/drive_user_manuals/reindex")
    assert resp.status_code == 202, resp.text
    body = resp.json()
    assert body["kb_id"] == "drive_user_manuals"
    assert body["status"] == "queued"
    assert body["task_id"].startswith("reindex-")
    assert "Track A" in body["note"]  # Decision B.1 transparency


@pytest.mark.asyncio
async def test_reindex_kb_not_found_returns_404(kb_service_empty: KBService) -> None:
    """Unknown kb_id → 404 (KB existence guard before mock task_id)."""
    app = _build_app(kb_service_empty)
    client = TestClient(app)

    resp = client.post("/kb/nonexistent_kb/reindex")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_per_doc_reindex_still_501_per_karpathy_surgical(
    kb_service_with_drive: KBService,
) -> None:
    """Per Karpathy §1.3 surgical: F5.3 only adds per-KB reindex;per-doc
    reindex `POST /kb/{kb_id}/documents/{doc_id}/reindex` (documents.py:41)
    remains 501 stub (out of W16 F5 scope per W2 implementation reference)."""
    app = _build_app(kb_service_with_drive)
    client = TestClient(app)

    resp = client.post("/kb/drive_user_manuals/documents/doc-A/reindex")
    assert resp.status_code == 501


@pytest.mark.asyncio
async def test_delete_kb_in_memory_baseline_preserved_per_b1(
    kb_service_with_drive: KBService,
) -> None:
    """Per Decision B.1: DELETE /kb/{kb_id} in-memory cleanup preserved;
    Azure AI Search index + Blob container drop deferred Track A W17+.
    Test verifies the in-memory delete works (no Azure-touch errors)."""
    app = _build_app(kb_service_with_drive)
    client = TestClient(app)

    # Delete works on in-memory baseline
    resp = client.delete("/kb/drive_user_manuals")
    assert resp.status_code == 204

    # Subsequent GET returns 404 (KB record purged)
    resp2 = client.get("/kb/drive_user_manuals")
    assert resp2.status_code == 404
