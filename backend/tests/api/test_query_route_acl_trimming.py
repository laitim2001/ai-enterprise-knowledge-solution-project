"""Query route end-to-end ACL trimming wiring (W90 P2.2c / ADR-0066 G2).

Proves the principal-threading chain: an authenticated non-admin's principal
reaches the Azure Search `filter` (so server-side trimming acts on the RIGHT
subject), two different users get two DIFFERENT filters (no cross-leakage), and an
admin's query carries NO ACL clause (sees all).

The actual Azure drop of unauthorized chunks is a server-side behaviour verified by
the P2.2b live smoke after the index rebuild — here we prove the WIRING (the right
principal reaches the right query) with the Azure HTTP layer mocked. The route runs
retrieval-only (synthesizer=None) so exactly one search() fires before the early
return, making the captured filter unambiguous.
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
from api.routes import query as query_route
from ingestion.embedding.base import EmbeddingResult
from retrieval.hybrid import HybridSearcher
from retrieval.retrieval_engine import RetrievalEngine
from storage.rbac_storage import InMemoryRbacBackend


class _FakeEmbedder:
    embedding_dimension = 1024

    async def embed(self, text: str) -> EmbeddingResult:  # noqa: ARG002
        return EmbeddingResult(vector=[0.5] * 1024, input_tokens=1)

    async def embed_batch(self, texts: list[str]) -> list[EmbeddingResult]:
        return [EmbeddingResult(vector=[0.5] * 1024, input_tokens=1) for _ in texts]


def _resp() -> MagicMock:
    r = MagicMock(spec=httpx.Response)
    r.status_code = 200
    r.is_success = True
    r.json = MagicMock(return_value={"value": []})
    r.raise_for_status = MagicMock()
    return r


def _user(oid: str, role: str = "user") -> AuthenticatedUser:
    return AuthenticatedUser(
        oid=oid, tid="t", preferred_username=f"{oid}@ricoh.com", role=role
    )


async def _run_query_capture(
    user: AuthenticatedUser, *, grant_oid: str | None = None
) -> tuple[object, list[dict]]:
    """Run /query as `user` (granted query on kb-1 if grant_oid set) with the Azure
    HTTP layer mocked; return (response, [captured search payloads])."""
    captured: list[dict] = []

    with patch("retrieval.hybrid.httpx.AsyncClient") as MockClient:
        instance = MockClient.return_value
        instance.aclose = AsyncMock()

        async def capture_post(url: str, **kwargs: object) -> MagicMock:  # noqa: ARG001
            captured.append(json.loads(kwargs["content"]))  # type: ignore[arg-type]
            return _resp()

        instance.post = AsyncMock(side_effect=capture_post)

        async with HybridSearcher("https://x", "k", "ekp-kb-drive-v1") as searcher:
            engine = RetrievalEngine(embedder=_FakeEmbedder(), searcher=searcher)
            app = FastAPI()
            app.state.retrieval_engine = engine
            app.state.synthesizer = None  # retrieval-only → exactly one search()
            app.state.crag_loop = None
            backend = InMemoryRbacBackend()
            if grant_oid is not None:
                await backend.add_kb_acl(
                    kb_id="kb-1", principal_type="user", principal_id=grant_oid,
                    access_role="query", granted_by="admin",
                )
            app.state.rbac_backend = backend
            app.dependency_overrides[get_current_user] = lambda: user
            app.include_router(query_route.router)

            with TestClient(app) as client:
                resp = client.post(
                    "/query",
                    json={
                        "query": "q", "kb_id": "kb-1",
                        "top_k_retrieval": 5, "top_k_rerank": 5,
                    },
                )
    return resp, captured


@pytest.mark.asyncio
async def test_granted_user_principal_reaches_search_filter() -> None:
    resp, captured = await _run_query_capture(_user("oid-alice"), grant_oid="oid-alice")
    assert resp.status_code == 200
    assert len(captured) == 1
    filter_str = captured[0]["filter"]
    assert "kb_id eq 'kb-1'" in filter_str  # KB scope preserved
    assert "allowed_principals/any(p: search.in(p, 'oid-alice', ','))" in filter_str
    assert "not allowed_principals/any()" in filter_str  # fail-open disjunct
    # P2.3 — the non-admin route query also carries the classification clearance clause.
    assert "classification eq 'internal'" in filter_str


@pytest.mark.asyncio
async def test_two_users_get_distinct_trimming_filters_no_leakage() -> None:
    _, cap_a = await _run_query_capture(_user("oid-alice"), grant_oid="oid-alice")
    _, cap_b = await _run_query_capture(_user("oid-bob"), grant_oid="oid-bob")
    f_a, f_b = cap_a[0]["filter"], cap_b[0]["filter"]
    assert "search.in(p, 'oid-alice', ',')" in f_a
    assert "search.in(p, 'oid-bob', ',')" in f_b
    # Cross-check: alice's filter must NOT carry bob's principal (no subject leakage).
    assert "oid-bob" not in f_a
    assert "oid-alice" not in f_b


@pytest.mark.asyncio
async def test_admin_query_carries_no_acl_clause() -> None:
    resp, captured = await _run_query_capture(_user("oid-admin", role="admin"))
    assert resp.status_code == 200
    # admin → principals_for_user None → unfiltered (sees all); no ACL clause.
    assert "allowed_principals" not in captured[0]["filter"]
