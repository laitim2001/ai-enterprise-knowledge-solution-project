"""/roles Roles tab route tests (W24c F5 per ADR-0027 Option A).

Covers F5.1 (GET /roles — 4 role definitions, order, Power User Tier 2
disabled affordance) + F5.2 (GET /roles/permissions — flat 92-cell matrix)
+ the require_role('admin') gate + the 503-on-unwired-backend path.

The RBAC backend is wired onto `app.state` (not a module-level singleton like
F4's users_repo) and seeded per test; mock-auth drives the caller's role.
"""

from __future__ import annotations

import asyncio

from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routes import roles
from storage.rbac_storage import InMemoryRbacBackend
from storage.settings import Settings, get_settings

_HEADERS = {"Authorization": "Bearer dev-token"}


def _app(mock_role: str = "admin", *, wire: bool = True) -> FastAPI:
    app = FastAPI()
    app.include_router(roles.router)
    if wire:
        backend = InMemoryRbacBackend()
        asyncio.run(backend.seed_defaults())
        app.state.rbac_backend = backend
    app.dependency_overrides[get_settings] = lambda: Settings(
        feature_auth_mock=True, auth_mock_role=mock_role
    )
    return app


# ---- F5.1 — GET /roles -----------------------------------------------------


def test_list_roles_returns_four() -> None:
    with TestClient(_app()) as client:
        r = client.get("/roles", headers=_HEADERS)
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 4
    assert len(body["roles"]) == 4


def test_list_roles_order() -> None:
    with TestClient(_app()) as client:
        r = client.get("/roles", headers=_HEADERS)
    keys = [role["role_key"] for role in r.json()["roles"]]
    assert keys == ["admin", "editor", "user", "power"]


def test_list_roles_power_user_is_tier2_disabled() -> None:
    with TestClient(_app()) as client:
        r = client.get("/roles", headers=_HEADERS)
    power = next(role for role in r.json()["roles"] if role["role_key"] == "power")
    assert power["tier"] == 2
    assert power["active"] is False


def test_list_roles_tier1_roles_active() -> None:
    with TestClient(_app()) as client:
        r = client.get("/roles", headers=_HEADERS)
    tier1 = [role for role in r.json()["roles"] if role["role_key"] != "power"]
    assert all(role["tier"] == 1 and role["active"] is True for role in tier1)


def test_list_roles_requires_admin() -> None:
    with TestClient(_app("editor")) as client:
        r = client.get("/roles", headers=_HEADERS)
    assert r.status_code == 403


def test_list_roles_401_without_credentials() -> None:
    with TestClient(_app()) as client:
        r = client.get("/roles")
    assert r.status_code == 401


def test_list_roles_503_when_backend_unwired() -> None:
    with TestClient(_app(wire=False)) as client:
        r = client.get("/roles", headers=_HEADERS)
    assert r.status_code == 503


# ---- F5.2 — GET /roles/permissions -----------------------------------------


def test_list_permissions_returns_full_matrix() -> None:
    with TestClient(_app()) as client:
        r = client.get("/roles/permissions", headers=_HEADERS)
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 92  # 23 permissions × 4 roles
    assert len(body["permissions"]) == 92


def test_list_permissions_has_23_distinct_keys() -> None:
    with TestClient(_app()) as client:
        r = client.get("/roles/permissions", headers=_HEADERS)
    keys = {p["permission_key"] for p in r.json()["permissions"]}
    assert len(keys) == 23


def test_list_permissions_has_five_areas() -> None:
    with TestClient(_app()) as client:
        r = client.get("/roles/permissions", headers=_HEADERS)
    areas = {p["area"] for p in r.json()["permissions"]}
    assert areas == {
        "Knowledge bases",
        "Documents",
        "Chat & queries",
        "Eval & ops",
        "Platform config",
    }


def test_list_permissions_admin_grants_everything() -> None:
    with TestClient(_app()) as client:
        r = client.get("/roles/permissions", headers=_HEADERS)
    admin = [p for p in r.json()["permissions"] if p["role_key"] == "admin"]
    assert len(admin) == 23
    assert all(p["granted"] for p in admin)


def test_list_permissions_end_user_denied_kb_create() -> None:
    with TestClient(_app()) as client:
        r = client.get("/roles/permissions", headers=_HEADERS)
    cell = next(
        p
        for p in r.json()["permissions"]
        if p["role_key"] == "user" and p["permission_key"] == "kb.create"
    )
    assert cell["granted"] is False


def test_list_permissions_requires_admin() -> None:
    with TestClient(_app("user")) as client:
        r = client.get("/roles/permissions", headers=_HEADERS)
    assert r.status_code == 403


def test_list_permissions_503_when_backend_unwired() -> None:
    with TestClient(_app(wire=False)) as client:
        r = client.get("/roles/permissions", headers=_HEADERS)
    assert r.status_code == 503
