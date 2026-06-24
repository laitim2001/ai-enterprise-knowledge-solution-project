"""Query route RBAC guard (W90 P2.0 / ADR-0066 G1).

`/query` + `/query/stream` gate on `assert_kb_access("query")`. Their `kb_id` is
in the `QueryRequest` body, so `require_kb_acl` (path-based) can't gate them — the
handlers take `get_current_user` + call `assert_kb_access`. A non-admin with no
`kb_acl` grant is rejected (403); missing credentials → 401. The guard fires
before the handler touches the retrieval engine, so the 403/401 paths need no
engine wiring. The admin / grant-pass paths run the full pipeline and are covered
by test_query_per_kb_config / _doc_config_overlay / _observe_query_route /
_e1_e5_e12_smoke (all admin-wired).
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routes import query as query_route
from storage.rbac_storage import InMemoryRbacBackend
from storage.settings import Settings, get_settings

_HEADERS = {"Authorization": "Bearer dev-token"}
_PAYLOAD = {"query": "hello", "kb_id": "kb-1"}


def _app(mock_role: str = "user") -> FastAPI:
    app = FastAPI()
    app.include_router(query_route.router)
    app.state.rbac_backend = InMemoryRbacBackend()
    app.dependency_overrides[get_settings] = lambda: Settings(
        feature_auth_mock=True, auth_mock_role=mock_role
    )
    return app


def test_query_non_admin_without_grant_forbidden() -> None:
    with TestClient(_app("editor")) as client:
        r = client.post("/query", json=_PAYLOAD, headers=_HEADERS)
    assert r.status_code == 403


def test_query_stream_non_admin_without_grant_forbidden() -> None:
    with TestClient(_app("editor")) as client:
        r = client.post("/query/stream", json=_PAYLOAD, headers=_HEADERS)
    assert r.status_code == 403


def test_query_401_without_credentials() -> None:
    with TestClient(_app("editor")) as client:
        r = client.post("/query", json=_PAYLOAD)
    assert r.status_code == 401


def test_query_stream_401_without_credentials() -> None:
    with TestClient(_app("editor")) as client:
        r = client.post("/query/stream", json=_PAYLOAD)
    assert r.status_code == 401
