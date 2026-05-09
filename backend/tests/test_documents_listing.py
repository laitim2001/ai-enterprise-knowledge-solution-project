"""Documents listing endpoint tests (W16 F5.1.1 CO_F3a closure).

Per W16 plan F5.1 acceptance criteria + CLAUDE.md §5.6 H6 test coverage.
Coverage:
- Happy path: kb_id with chunks → aggregated DocumentSummary list
- Empty KB: kb_id exists but no chunks → empty list
- KB not found: 404 envelope
- Engine not initialized: 503 envelope
- Searcher failure: 502 envelope
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routes import documents as documents_routes
from api.schemas.kb import KbConfig, KbCreate
from kb_management import KBService, get_kb_service
from kb_management.storage import InMemoryKBBackend


def _build_app(searcher: AsyncMock | None, kb_service: KBService) -> FastAPI:
    """FastAPI app with documents router + mock retrieval engine + injected KBService."""
    app = FastAPI()
    app.include_router(documents_routes.router)
    app.dependency_overrides[get_kb_service] = lambda: kb_service

    if searcher is not None:
        class _MockEngine:
            def __init__(self, s: AsyncMock) -> None:
                self._searcher = s

            async def list_documents(self, kb_id: str, max_chunks: int = 1000) -> list[dict]:
                return await self._searcher.list_documents(kb_id, max_chunks=max_chunks)

        app.state.retrieval_engine = _MockEngine(searcher)
    else:
        app.state.retrieval_engine = None

    return app


@pytest.fixture
async def kb_service_with_drive() -> KBService:
    """Fresh in-memory KBService with `drive_user_manuals` KB seeded."""
    service = KBService(InMemoryKBBackend())
    await service.create(KbCreate(
        kb_id="drive_user_manuals",
        name="Drive Project — User Manuals",
        description="D365 F&O ERP user manuals",
        config=KbConfig(),
    ))
    return service


@pytest.fixture
async def kb_service_empty() -> KBService:
    """KBService with no KBs seeded (for kb_not_found test)."""
    return KBService(InMemoryKBBackend())


@pytest.mark.asyncio
async def test_list_documents_happy_path(kb_service_with_drive: KBService) -> None:
    """Searcher returns aggregated doc-level metadata; route surfaces as
    DocumentSummary list."""
    searcher = AsyncMock()
    searcher.list_documents = AsyncMock(return_value=[
        {
            "doc_id": "doc-A",
            "doc_title": "Vendor Onboarding",
            "doc_format": "docx",
            "total_chunks": 12,
            "last_indexed_at": "2026-05-09T10:00:00Z",
            "source_url": "https://drive/vendor-onboard.docx",
            "tags": ["finance"],
        },
        {
            "doc_id": "doc-B",
            "doc_title": "AP Invoice Processing",
            "doc_format": "pdf",
            "total_chunks": 8,
            "last_indexed_at": "2026-05-08T15:30:00Z",
            "source_url": None,
            "tags": [],
        },
    ])

    app = _build_app(searcher=searcher, kb_service=kb_service_with_drive)
    client = TestClient(app)

    resp = client.get("/kb/drive_user_manuals/documents")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert len(body) == 2
    assert body[0]["doc_id"] == "doc-A"
    assert body[0]["doc_title"] == "Vendor Onboarding"
    assert body[0]["total_chunks"] == 12
    assert body[0]["tags"] == ["finance"]
    assert body[1]["doc_id"] == "doc-B"
    assert body[1]["source_url"] is None


@pytest.mark.asyncio
async def test_list_documents_empty_kb_returns_empty_list(kb_service_with_drive: KBService) -> None:
    """KB exists but no chunks ingested → empty list (not 404)."""
    searcher = AsyncMock()
    searcher.list_documents = AsyncMock(return_value=[])

    app = _build_app(searcher=searcher, kb_service=kb_service_with_drive)
    client = TestClient(app)

    resp = client.get("/kb/drive_user_manuals/documents")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_list_documents_kb_not_found_returns_404(kb_service_empty: KBService) -> None:
    """Unknown kb_id → 404 from KBService check (before searcher call)."""
    searcher = AsyncMock()
    searcher.list_documents = AsyncMock()  # should NOT be called

    app = _build_app(searcher=searcher, kb_service=kb_service_empty)
    client = TestClient(app)

    resp = client.get("/kb/nonexistent_kb/documents")
    assert resp.status_code == 404
    searcher.list_documents.assert_not_called()


@pytest.mark.asyncio
async def test_list_documents_engine_not_initialized_returns_503(
    kb_service_with_drive: KBService,
) -> None:
    """app.state.retrieval_engine = None → 503 (KB check passes first; engine 503)."""
    app = _build_app(searcher=None, kb_service=kb_service_with_drive)
    client = TestClient(app)

    resp = client.get("/kb/drive_user_manuals/documents")
    assert resp.status_code == 503


@pytest.mark.asyncio
async def test_list_documents_searcher_failure_returns_502(
    kb_service_with_drive: KBService,
) -> None:
    """Searcher raises Azure error → 502 envelope (graceful degrade)."""
    searcher = AsyncMock()
    searcher.list_documents = AsyncMock(side_effect=ConnectionError("Azure unreachable"))

    app = _build_app(searcher=searcher, kb_service=kb_service_with_drive)
    client = TestClient(app)

    resp = client.get("/kb/drive_user_manuals/documents")
    assert resp.status_code == 502
    assert "ConnectionError" in resp.json()["detail"]
