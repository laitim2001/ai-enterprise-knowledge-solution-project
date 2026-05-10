"""Retrieval Testing endpoint tests (ADR-0021 — POST /kb/{kb_id}/retrieval-test).

Per CLAUDE.md §5.6 H6 + ADR-0021 §Implementation Deliverables. Coverage:
- Happy path (hybrid): ranked chunks + timings + reranker label + total_hits
- mode passed through to RetrievalEngine.retrieve
- rerank=False → reranker label "none"
- score_threshold filters vector/hybrid; ignored for fulltext (BM25 unbounded)
- KB not found → 404 (engine.retrieve not called); engine absent → 503; engine raises → 502
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routes import retrieval_test as retrieval_test_routes
from api.schemas.kb import KbConfig, KbCreate
from kb_management import KBService, get_kb_service
from kb_management.storage import InMemoryKBBackend
from retrieval.retrieval_engine import RetrievalResult, RetrievedChunk


def _chunk(chunk_id: str, score: float, *, doc_id: str = "doc-A") -> RetrievedChunk:
    return RetrievedChunk(
        score=score,
        fields={
            "chunk_id": chunk_id,
            "doc_id": doc_id,
            "doc_title": "Vendor Onboarding",
            "chunk_title": f"Section for {chunk_id}",
            "chunk_index": int(chunk_id.split("-")[-1]) if chunk_id[-1].isdigit() else 0,
            "section_path": ["Onboarding", "Step 1"],
            "chunk_text": "a" * 400,  # > preview length so truncation kicks in
        },
    )


def _result(chunks: list[RetrievedChunk], *, reranked: bool) -> RetrievalResult:
    return RetrievalResult(
        chunks=chunks,
        embed_latency_ms=12,
        search_latency_ms=34,
        rerank_latency_ms=56 if reranked else 0,
        total_latency_ms=102,
        reranked=reranked,
    )


def _build_app(engine: object | None, kb_service: KBService) -> FastAPI:
    app = FastAPI()
    app.include_router(retrieval_test_routes.router)
    app.dependency_overrides[get_kb_service] = lambda: kb_service
    app.state.retrieval_engine = engine
    return app


@pytest.fixture
async def kb_service_with_drive() -> KBService:
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
    return KBService(InMemoryKBBackend())


@pytest.mark.asyncio
async def test_retrieval_test_happy_path_hybrid(kb_service_with_drive: KBService) -> None:
    engine = MagicMock()
    engine.retrieve = AsyncMock(
        return_value=_result([_chunk("c-1", 0.92), _chunk("c-2", 0.71)], reranked=True),
    )
    client = TestClient(_build_app(engine, kb_service_with_drive))

    resp = client.post(
        "/kb/drive_user_manuals/retrieval-test",
        json={"query": "how do I reconcile AR invoices?"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["kb_id"] == "drive_user_manuals"
    assert body["mode"] == "hybrid"
    assert body["reranked"] is True
    assert body["reranker"] == "cohere-v4.0-pro"
    assert body["total_hits"] == 2
    assert body["search_latency_ms"] == 34
    assert body["rerank_latency_ms"] == 56
    assert [c["rank"] for c in body["chunks"]] == [1, 2]
    assert body["chunks"][0]["chunk_id"] == "c-1"
    assert body["chunks"][0]["score"] == 0.92
    assert body["chunks"][0]["chunk_text_preview"].endswith("…")  # truncated
    # default mode + rerank flag forwarded to the engine
    kwargs = engine.retrieve.await_args.kwargs
    assert kwargs["mode"] == "hybrid"
    assert kwargs["rerank"] is True
    assert kwargs["kb_id"] == "drive_user_manuals"


@pytest.mark.asyncio
async def test_retrieval_test_mode_and_rerank_off_forwarded(
    kb_service_with_drive: KBService,
) -> None:
    engine = MagicMock()
    engine.retrieve = AsyncMock(return_value=_result([_chunk("c-1", 0.5)], reranked=False))
    client = TestClient(_build_app(engine, kb_service_with_drive))

    resp = client.post(
        "/kb/drive_user_manuals/retrieval-test",
        json={"query": "paper jam", "mode": "vector", "rerank": False, "top_k": 3},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["mode"] == "vector"
    assert body["reranked"] is False
    assert body["reranker"] == "none"
    kwargs = engine.retrieve.await_args.kwargs
    assert kwargs["mode"] == "vector"
    assert kwargs["rerank"] is False
    assert kwargs["top_k"] == 3


@pytest.mark.asyncio
async def test_retrieval_test_score_threshold_filters_vector(
    kb_service_with_drive: KBService,
) -> None:
    engine = MagicMock()
    engine.retrieve = AsyncMock(return_value=_result(
        [_chunk("c-1", 0.80), _chunk("c-2", 0.30), _chunk("c-3", 0.55)], reranked=False,
    ))
    client = TestClient(_build_app(engine, kb_service_with_drive))

    resp = client.post(
        "/kb/drive_user_manuals/retrieval-test",
        json={"query": "x", "mode": "vector", "rerank": False, "score_threshold": 0.5},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["total_hits"] == 3  # before filter
    assert [c["chunk_id"] for c in body["chunks"]] == ["c-1", "c-3"]  # 0.30 dropped
    assert [c["rank"] for c in body["chunks"]] == [1, 2]  # ranks re-numbered


@pytest.mark.asyncio
async def test_retrieval_test_score_threshold_ignored_for_fulltext(
    kb_service_with_drive: KBService,
) -> None:
    """BM25 scores are unbounded above and have no 0–1 meaning → threshold ignored."""
    engine = MagicMock()
    engine.retrieve = AsyncMock(return_value=_result(
        [_chunk("c-1", 4.2), _chunk("c-2", 0.1)], reranked=False,
    ))
    client = TestClient(_build_app(engine, kb_service_with_drive))

    resp = client.post(
        "/kb/drive_user_manuals/retrieval-test",
        json={"query": "x", "mode": "fulltext", "rerank": False, "score_threshold": 0.9},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert [c["chunk_id"] for c in body["chunks"]] == ["c-1", "c-2"]  # nothing dropped


@pytest.mark.asyncio
async def test_retrieval_test_kb_not_found_returns_404(kb_service_empty: KBService) -> None:
    engine = MagicMock()
    engine.retrieve = AsyncMock()
    client = TestClient(_build_app(engine, kb_service_empty))

    resp = client.post("/kb/nope/retrieval-test", json={"query": "x"})
    assert resp.status_code == 404
    engine.retrieve.assert_not_awaited()


@pytest.mark.asyncio
async def test_retrieval_test_engine_absent_returns_503(
    kb_service_with_drive: KBService,
) -> None:
    client = TestClient(_build_app(None, kb_service_with_drive))
    resp = client.post("/kb/drive_user_manuals/retrieval-test", json={"query": "x"})
    assert resp.status_code == 503


@pytest.mark.asyncio
async def test_retrieval_test_engine_failure_returns_502(
    kb_service_with_drive: KBService,
) -> None:
    engine = MagicMock()
    engine.retrieve = AsyncMock(side_effect=ConnectionError("Azure unreachable"))
    client = TestClient(_build_app(engine, kb_service_with_drive))

    resp = client.post("/kb/drive_user_manuals/retrieval-test", json={"query": "x"})
    assert resp.status_code == 502
    assert "ConnectionError" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_retrieval_test_rejects_empty_query(kb_service_with_drive: KBService) -> None:
    engine = MagicMock()
    engine.retrieve = AsyncMock()
    client = TestClient(_build_app(engine, kb_service_with_drive))

    resp = client.post("/kb/drive_user_manuals/retrieval-test", json={"query": ""})
    assert resp.status_code == 422  # Pydantic min_length=1
    engine.retrieve.assert_not_awaited()
