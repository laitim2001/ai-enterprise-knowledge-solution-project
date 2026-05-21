"""/groups Groups tab route tests (W24c F6 per ADR-0027 Option A).

Covers F6.1 (GET /groups — list + member counts) + F6.2 (POST
/groups/sync-from-entra — graceful skip when Entra unconfigured / upsert when
configured / 502 on Graph failure) + the require_role('admin') gate + the
503-on-unwired-backend path.

`entra_graph.fetch_entra_groups` is mocked — the live Microsoft Graph call is
a deferred pre-Beta smoke (W24c plan §3 PARTIAL PASS / R-W24c-6).
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.auth import entra_graph
from api.routes import groups
from storage.rbac_storage import InMemoryRbacBackend
from storage.settings import Settings, get_settings

_HEADERS = {"Authorization": "Bearer dev-token"}


def _app(
    mock_role: str = "admin", *, wire: bool = True, tenant_id: str = ""
) -> FastAPI:
    app = FastAPI()
    app.include_router(groups.router)
    if wire:
        app.state.rbac_backend = InMemoryRbacBackend()
    app.dependency_overrides[get_settings] = lambda: Settings(
        feature_auth_mock=True, auth_mock_role=mock_role, azure_tenant_id=tenant_id
    )
    return app


async def _fake_fetch() -> list[entra_graph.EntraGroup]:
    return [
        entra_graph.EntraGroup(
            object_id="g-admins", display_name="grp-ekp-admins", description="Admins"
        ),
        entra_graph.EntraGroup(
            object_id="g-editors", display_name="grp-ekp-editors", description=None
        ),
    ]


async def _failing_fetch() -> list[entra_graph.EntraGroup]:
    raise RuntimeError("graph unreachable")


# ---- F6.1 — GET /groups ----------------------------------------------------


def test_list_groups_empty() -> None:
    with TestClient(_app()) as client:
        r = client.get("/groups", headers=_HEADERS)
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 0
    assert body["groups"] == []


def test_list_groups_requires_admin() -> None:
    with TestClient(_app("editor")) as client:
        r = client.get("/groups", headers=_HEADERS)
    assert r.status_code == 403


def test_list_groups_401_without_credentials() -> None:
    with TestClient(_app()) as client:
        r = client.get("/groups")
    assert r.status_code == 401


def test_list_groups_503_when_backend_unwired() -> None:
    with TestClient(_app(wire=False)) as client:
        r = client.get("/groups", headers=_HEADERS)
    assert r.status_code == 503


# ---- F6.2 — POST /groups/sync-from-entra -----------------------------------


def test_sync_skipped_when_entra_unconfigured() -> None:
    with TestClient(_app(tenant_id="")) as client:
        r = client.post("/groups/sync-from-entra", headers=_HEADERS)
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "skipped"
    assert body["synced_count"] == 0


def test_sync_from_entra_synced(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(entra_graph, "fetch_entra_groups", _fake_fetch)
    with TestClient(_app(tenant_id="test-tenant")) as client:
        r = client.post("/groups/sync-from-entra", headers=_HEADERS)
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "synced"
    assert body["synced_count"] == 2


def test_synced_groups_listed_with_shape(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(entra_graph, "fetch_entra_groups", _fake_fetch)
    with TestClient(_app(tenant_id="test-tenant")) as client:
        client.post("/groups/sync-from-entra", headers=_HEADERS)
        r = client.get("/groups", headers=_HEADERS)
    body = r.json()
    assert body["total"] == 2
    first = body["groups"][0]  # ordered by name — 'grp-ekp-admins' first
    assert first["name"] == "grp-ekp-admins"
    assert first["source"] == "entra"
    assert first["entra_object_id"] == "g-admins"
    assert first["synced_at"] is not None
    assert first["member_count"] == 0


def test_sync_requires_admin() -> None:
    with TestClient(_app("editor", tenant_id="test-tenant")) as client:
        r = client.post("/groups/sync-from-entra", headers=_HEADERS)
    assert r.status_code == 403


def test_sync_502_on_graph_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(entra_graph, "fetch_entra_groups", _failing_fetch)
    with TestClient(_app(tenant_id="test-tenant")) as client:
        r = client.post("/groups/sync-from-entra", headers=_HEADERS)
    assert r.status_code == 502
