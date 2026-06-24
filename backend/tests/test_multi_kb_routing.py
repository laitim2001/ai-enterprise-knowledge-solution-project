"""Multi-KB query routing integration tests (ADR-0018 W16+ Phase 3 Session 2).

Per ADR-0018 multi-KB invariant closure (audit-W15-d5-vs-spec.md §CC-1):
- /query endpoint reads payload.kb_id (no longer ignored)
- RetrievalEngine.retrieve(query, kb_id, ...) propagates kb_id
- HybridSearcher.search(kb_id, ...) constructs dynamic index_name + filter prepend

These integration tests verify the kb_id propagation chain end-to-end at the API
contract layer using FastAPI TestClient. We mock the Azure Search HTTP layer
(httpx.AsyncClient) so no live Azure dependency, and assert the URL + filter
clause for each kb_id distinctly to prove zero cross-KB leakage.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.auth.dependency import get_current_user
from api.auth.models import AuthenticatedUser
from ingestion.embedding.base import EmbeddingResult
from retrieval.hybrid import HybridSearcher
from retrieval.retrieval_engine import RetrievalEngine


def _mock_search_response(status_code: int = 200, body: dict | None = None) -> MagicMock:
    """Mock httpx.Response shape for HybridSearcher.search() POST."""
    response = MagicMock(spec=httpx.Response)
    response.status_code = status_code
    response.is_success = 200 <= status_code < 300
    response.json = MagicMock(return_value=body or {"value": []})
    response.raise_for_status = MagicMock()
    return response


class _FakeEmbedder:
    """Minimal embedder stub returning constant 1024d vector."""

    embedding_dimension = 1024

    async def embed(self, text: str) -> EmbeddingResult:  # noqa: ARG002
        return EmbeddingResult(vector=[0.5] * 1024, input_tokens=3)

    async def embed_batch(self, texts: list[str]) -> list[EmbeddingResult]:
        return [EmbeddingResult(vector=[0.5] * 1024, input_tokens=1) for _ in texts]


def _build_app_with_engine(engine: RetrievalEngine) -> FastAPI:
    """Build minimal FastAPI app with /query route + injected RetrievalEngine."""
    from api.routes.query import router

    app = FastAPI()
    app.state.retrieval_engine = engine
    app.state.synthesizer = None  # retrieval-only fallback
    app.state.crag_loop = None
    # W90 P2.0 — /query now requires auth (assert_kb_access). Override with an admin
    # so the KB-level guard passes without a wired rbac_backend; admin →
    # principals_for_user None → NO ACL clause, so the kb_id-scope filter assertions
    # below stay byte-identical to the pre-P2.0/P2.2 baseline.
    app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(
        oid="oid-admin", tid="t", preferred_username="admin@ricoh.com", role="admin"
    )
    app.include_router(router)
    return app


@pytest.mark.asyncio
async def test_query_route_propagates_legacy_kb_id_to_searcher() -> None:
    """/query with kb_id='drive_user_manuals' → searcher hits ekp-kb-drive-v1 (legacy alias)."""
    captured_calls = []

    with patch("retrieval.hybrid.httpx.AsyncClient") as MockClient:
        instance = MockClient.return_value
        instance.aclose = AsyncMock()

        async def capture_post(url, **kwargs):
            captured_calls.append({"url": url, "content": kwargs.get("content")})
            return _mock_search_response(200, {"value": []})

        instance.post = AsyncMock(side_effect=capture_post)

        async with HybridSearcher("https://x", "k", "ekp-kb-drive-v1") as searcher:
            embedder = _FakeEmbedder()
            engine = RetrievalEngine(embedder=embedder, searcher=searcher)
            app = _build_app_with_engine(engine)

            with TestClient(app) as client:
                resp = client.post(
                    "/query",
                    json={
                        "query": "how to post sales order",
                        "kb_id": "drive_user_manuals",
                        "top_k_retrieval": 5,
                        "top_k_rerank": 5,
                    },
                )

    assert resp.status_code == 200
    assert len(captured_calls) == 1
    # ADR-0018: legacy alias kb_id="drive_user_manuals" → URL hits self.index_name
    assert "/indexes/ekp-kb-drive-v1/" in captured_calls[0]["url"]
    payload = json.loads(captured_calls[0]["content"])
    # ADR-0018: filter must scope to kb_id (multi-KB invariant)
    assert payload["filter"].startswith("kb_id eq 'drive_user_manuals'")


@pytest.mark.asyncio
async def test_query_route_propagates_new_kb_id_to_searcher_dynamic_index() -> None:
    """/query with kb_id='finance_dept' → searcher hits ekp-kb-finance_dept-v1 (ADR-0005 convention)."""
    captured_calls = []

    with patch("retrieval.hybrid.httpx.AsyncClient") as MockClient:
        instance = MockClient.return_value
        instance.aclose = AsyncMock()

        async def capture_post(url, **kwargs):
            captured_calls.append({"url": url, "content": kwargs.get("content")})
            return _mock_search_response(200, {"value": []})

        instance.post = AsyncMock(side_effect=capture_post)

        async with HybridSearcher("https://x", "k", "ekp-kb-drive-v1") as searcher:
            embedder = _FakeEmbedder()
            engine = RetrievalEngine(embedder=embedder, searcher=searcher)
            app = _build_app_with_engine(engine)

            with TestClient(app) as client:
                resp = client.post(
                    "/query",
                    json={
                        "query": "expense reimbursement policy",
                        "kb_id": "finance_dept",
                        "top_k_retrieval": 5,
                        "top_k_rerank": 5,
                    },
                )

    assert resp.status_code == 200
    assert len(captured_calls) == 1
    # ADR-0018: new kb_id → dynamic index_name per ADR-0005 (NOT legacy)
    assert "/indexes/ekp-kb-finance_dept-v1/" in captured_calls[0]["url"]
    payload = json.loads(captured_calls[0]["content"])
    assert payload["filter"].startswith("kb_id eq 'finance_dept'")


@pytest.mark.asyncio
async def test_query_route_two_kb_zero_cross_leakage() -> None:
    """ADR-0018: 2 sequential queries on different KBs → distinct index_name + filter; zero leakage."""
    captured_calls = []

    with patch("retrieval.hybrid.httpx.AsyncClient") as MockClient:
        instance = MockClient.return_value
        instance.aclose = AsyncMock()

        async def capture_post(url, **kwargs):
            captured_calls.append({"url": url, "content": kwargs.get("content")})
            return _mock_search_response(200, {"value": []})

        instance.post = AsyncMock(side_effect=capture_post)

        async with HybridSearcher("https://x", "k", "ekp-kb-drive-v1") as searcher:
            embedder = _FakeEmbedder()
            engine = RetrievalEngine(embedder=embedder, searcher=searcher)
            app = _build_app_with_engine(engine)

            with TestClient(app) as client:
                # Query KB-1 (Drive)
                resp1 = client.post(
                    "/query",
                    json={
                        "query": "post sales order",
                        "kb_id": "drive_user_manuals",
                        "top_k_retrieval": 5,
                        "top_k_rerank": 5,
                    },
                )
                # Query KB-2 (HR)
                resp2 = client.post(
                    "/query",
                    json={
                        "query": "annual leave policy",
                        "kb_id": "hr_handbook",
                        "top_k_retrieval": 5,
                        "top_k_rerank": 5,
                    },
                )

    assert resp1.status_code == 200
    assert resp2.status_code == 200
    assert len(captured_calls) == 2

    # Each query hit its own index (zero cross-leakage)
    assert "/indexes/ekp-kb-drive-v1/" in captured_calls[0]["url"]
    assert "/indexes/ekp-kb-hr_handbook-v1/" in captured_calls[1]["url"]

    # Each query scoped via kb_id eq filter (multi-KB invariant)
    payload1 = json.loads(captured_calls[0]["content"])
    payload2 = json.loads(captured_calls[1]["content"])
    assert "kb_id eq 'drive_user_manuals'" in payload1["filter"]
    assert "kb_id eq 'hr_handbook'" in payload2["filter"]

    # Filter must NOT contain the OTHER kb_id (no cross-contamination)
    assert "hr_handbook" not in payload1["filter"]
    assert "drive_user_manuals" not in payload2["filter"]


@pytest.mark.asyncio
async def test_query_route_missing_kb_id_returns_422() -> None:
    """Pydantic schema validation: kb_id is required field; missing → 422 Unprocessable Entity."""
    embedder = _FakeEmbedder()
    searcher = MagicMock()
    searcher.search = AsyncMock(return_value=[])
    engine = RetrievalEngine(embedder=embedder, searcher=searcher)
    app = _build_app_with_engine(engine)

    with TestClient(app) as client:
        resp = client.post(
            "/query",
            json={
                "query": "test query without kb_id",
                # kb_id intentionally omitted
            },
        )

    assert resp.status_code == 422
    detail = resp.json()
    # FastAPI default 422 response shape includes "detail" field
    assert "detail" in detail
