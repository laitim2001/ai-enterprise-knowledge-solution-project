"""Chunks listing endpoint tests (W16 F5.1.2 CO_F3a closure).

Per W16 plan F5.1 acceptance criteria + CLAUDE.md §5.6 H6 test coverage.
Coverage:
- Happy path: kb_id+doc_id with chunks → ordered ChunkSummary list
- Doc not found / empty doc: empty list (consistent with Azure Search semantics)
- KB not found: 404 envelope
- Engine not initialized: 503 envelope
- Searcher failure: 502 envelope
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routes import chunks as chunks_routes
from api.schemas.kb import KbConfig, KbCreate
from kb_management import KBService, get_kb_service
from kb_management.storage import InMemoryKBBackend


def _build_app(searcher: AsyncMock | None, kb_service: KBService) -> FastAPI:
    app = FastAPI()
    app.include_router(chunks_routes.router)
    app.dependency_overrides[get_kb_service] = lambda: kb_service

    if searcher is not None:
        class _MockEngine:
            def __init__(self, s: AsyncMock) -> None:
                self._searcher = s

            async def list_chunks(self, kb_id: str, doc_id: str, top: int = 1000) -> list[dict]:
                return await self._searcher.list_chunks(kb_id, doc_id, top=top)

        app.state.retrieval_engine = _MockEngine(searcher)
    else:
        app.state.retrieval_engine = None

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
async def test_list_chunks_happy_path(kb_service_with_drive: KBService) -> None:
    """Searcher returns ordered chunk metadata; route surfaces as ChunkSummary list."""
    searcher = AsyncMock()
    searcher.list_chunks = AsyncMock(return_value=[
        {
            "chunk_id": "kb-drive_doc-A_chunk-0001",
            "chunk_index": 1,
            "chunk_total": 3,
            "chunk_title": "Step 1: Verify Credit",
            "section_path": ["Vendor Onboarding", "Credit Check"],
            "enabled": True,
            "low_value_flag": False,
        },
        {
            "chunk_id": "kb-drive_doc-A_chunk-0002",
            "chunk_index": 2,
            "chunk_total": 3,
            "chunk_title": "Step 2: Approve",
            "section_path": ["Vendor Onboarding"],
            "enabled": True,
            "low_value_flag": False,
        },
        {
            "chunk_id": "kb-drive_doc-A_chunk-0003",
            "chunk_index": 3,
            "chunk_total": 3,
            "chunk_title": "Disabled placeholder",
            "section_path": [],
            "enabled": False,
            "low_value_flag": True,
        },
    ])

    app = _build_app(searcher=searcher, kb_service=kb_service_with_drive)
    client = TestClient(app)

    resp = client.get("/kb/drive_user_manuals/documents/doc-A/chunks")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert len(body) == 3
    assert body[0]["chunk_index"] == 1
    assert body[0]["chunk_title"] == "Step 1: Verify Credit"
    assert body[0]["section_path"] == ["Vendor Onboarding", "Credit Check"]
    assert body[2]["enabled"] is False
    assert body[2]["low_value_flag"] is True


@pytest.mark.asyncio
async def test_list_chunks_doc_not_found_returns_empty_list(
    kb_service_with_drive: KBService,
) -> None:
    """KB exists but doc has no chunks → empty list (consistent with Azure Search
    semantics — differentiating doc 404 vs empty doc requires extra query, deferred)."""
    searcher = AsyncMock()
    searcher.list_chunks = AsyncMock(return_value=[])

    app = _build_app(searcher=searcher, kb_service=kb_service_with_drive)
    client = TestClient(app)

    resp = client.get("/kb/drive_user_manuals/documents/nonexistent_doc/chunks")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_list_chunks_kb_not_found_returns_404(kb_service_empty: KBService) -> None:
    """Unknown kb_id → 404 from KBService check (before searcher call)."""
    searcher = AsyncMock()
    searcher.list_chunks = AsyncMock()

    app = _build_app(searcher=searcher, kb_service=kb_service_empty)
    client = TestClient(app)

    resp = client.get("/kb/nonexistent_kb/documents/doc-A/chunks")
    assert resp.status_code == 404
    searcher.list_chunks.assert_not_called()


@pytest.mark.asyncio
async def test_list_chunks_engine_not_initialized_returns_503(
    kb_service_with_drive: KBService,
) -> None:
    """app.state.retrieval_engine = None → 503."""
    app = _build_app(searcher=None, kb_service=kb_service_with_drive)
    client = TestClient(app)

    resp = client.get("/kb/drive_user_manuals/documents/doc-A/chunks")
    assert resp.status_code == 503


@pytest.mark.asyncio
async def test_list_chunks_searcher_failure_returns_502(
    kb_service_with_drive: KBService,
) -> None:
    """Searcher raises Azure error → 502 envelope (graceful degrade)."""
    searcher = AsyncMock()
    searcher.list_chunks = AsyncMock(side_effect=ConnectionError("Azure unreachable"))

    app = _build_app(searcher=searcher, kb_service=kb_service_with_drive)
    client = TestClient(app)

    resp = client.get("/kb/drive_user_manuals/documents/doc-A/chunks")
    assert resp.status_code == 502
    assert "ConnectionError" in resp.json()["detail"]
