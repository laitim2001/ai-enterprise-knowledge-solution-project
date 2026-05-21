"""/kb/{kb_id}/acl per-KB ACL route tests (W24c F8 per ADR-0027 Option A).

Covers F8.1 (kb_acl CRUD — grant / list / role-change / revoke + upsert +
cross-KB entry scoping + the kb.access.granted audit write) + F8.2 (the
router-level require_kb_acl('manage') gate). Mock-auth drives the caller's
role; a fresh RBAC backend is wired on app.state per test.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routes import kb_acl
from storage.audit_log_storage import InMemoryAuditLogBackend
from storage.rbac_storage import InMemoryRbacBackend
from storage.settings import Settings, get_settings

_HEADERS = {"Authorization": "Bearer dev-token"}
_GRANT = {"principal_type": "user", "principal_id": "u-99", "access_role": "edit"}


def _app(
    mock_role: str = "admin",
    *,
    wire: bool = True,
    audit: InMemoryAuditLogBackend | None = None,
) -> FastAPI:
    app = FastAPI()
    app.include_router(kb_acl.router)
    if wire:
        app.state.rbac_backend = InMemoryRbacBackend()
    if audit is not None:
        app.state.audit_log_backend = audit
    app.dependency_overrides[get_settings] = lambda: Settings(
        feature_auth_mock=True, auth_mock_role=mock_role
    )
    return app


# ---- F8.1 — GET / POST -----------------------------------------------------


def test_list_kb_acl_empty() -> None:
    with TestClient(_app()) as client:
        r = client.get("/kb/kb-1/acl", headers=_HEADERS)
    assert r.status_code == 200
    assert r.json() == {"entries": [], "total": 0}


def test_grant_kb_access() -> None:
    with TestClient(_app()) as client:
        r = client.post("/kb/kb-1/acl", json=_GRANT, headers=_HEADERS)
    assert r.status_code == 201
    body = r.json()
    assert body["principal_id"] == "u-99"
    assert body["access_role"] == "edit"
    assert body["granted_by"] is not None


def test_grant_then_list() -> None:
    with TestClient(_app()) as client:
        client.post("/kb/kb-1/acl", json=_GRANT, headers=_HEADERS)
        r = client.get("/kb/kb-1/acl", headers=_HEADERS)
    assert r.json()["total"] == 1


def test_grant_upserts_same_principal() -> None:
    with TestClient(_app()) as client:
        client.post("/kb/kb-1/acl", json=_GRANT, headers=_HEADERS)
        client.post(
            "/kb/kb-1/acl",
            json={**_GRANT, "access_role": "manage"},
            headers=_HEADERS,
        )
        r = client.get("/kb/kb-1/acl", headers=_HEADERS)
    body = r.json()
    assert body["total"] == 1  # upserted, not duplicated
    assert body["entries"][0]["access_role"] == "manage"


def test_grant_writes_audit() -> None:
    audit = InMemoryAuditLogBackend()
    with TestClient(_app(audit=audit)) as client:
        client.post("/kb/kb-1/acl", json=_GRANT, headers=_HEADERS)
    assert len(audit._rows) == 1
    assert audit._rows[0].action == "kb.access.granted"
    assert audit._rows[0].resource == "kb/kb-1"


def test_grant_rejects_bad_role_422() -> None:
    with TestClient(_app()) as client:
        r = client.post(
            "/kb/kb-1/acl",
            json={**_GRANT, "access_role": "owner"},
            headers=_HEADERS,
        )
    assert r.status_code == 422


# ---- F8.1 — PATCH / DELETE -------------------------------------------------


def test_change_kb_acl_role() -> None:
    with TestClient(_app()) as client:
        created = client.post("/kb/kb-1/acl", json=_GRANT, headers=_HEADERS).json()
        r = client.patch(
            f"/kb/kb-1/acl/{created['id']}",
            json={"access_role": "manage"},
            headers=_HEADERS,
        )
    assert r.status_code == 200
    assert r.json()["access_role"] == "manage"


def test_change_unknown_entry_404() -> None:
    with TestClient(_app()) as client:
        r = client.patch(
            "/kb/kb-1/acl/999", json={"access_role": "edit"}, headers=_HEADERS
        )
    assert r.status_code == 404


def test_change_wrong_kb_404() -> None:
    """A grant created on kb-1 cannot be edited via a kb-2 path."""
    with TestClient(_app()) as client:
        created = client.post("/kb/kb-1/acl", json=_GRANT, headers=_HEADERS).json()
        r = client.patch(
            f"/kb/kb-2/acl/{created['id']}",
            json={"access_role": "manage"},
            headers=_HEADERS,
        )
    assert r.status_code == 404


def test_revoke_kb_access() -> None:
    with TestClient(_app()) as client:
        created = client.post("/kb/kb-1/acl", json=_GRANT, headers=_HEADERS).json()
        r = client.delete(f"/kb/kb-1/acl/{created['id']}", headers=_HEADERS)
        listed = client.get("/kb/kb-1/acl", headers=_HEADERS)
    assert r.status_code == 204
    assert listed.json()["total"] == 0


def test_revoke_unknown_entry_404() -> None:
    with TestClient(_app()) as client:
        r = client.delete("/kb/kb-1/acl/999", headers=_HEADERS)
    assert r.status_code == 404


# ---- F8.2 — require_kb_acl('manage') gate ----------------------------------


def test_kb_acl_requires_manage_access() -> None:
    """A non-admin with no kb_acl grant is rejected by require_kb_acl."""
    with TestClient(_app("editor")) as client:
        r = client.get("/kb/kb-1/acl", headers=_HEADERS)
    assert r.status_code == 403


def test_kb_acl_401_without_credentials() -> None:
    with TestClient(_app()) as client:
        r = client.get("/kb/kb-1/acl")
    assert r.status_code == 401


def test_kb_acl_503_when_backend_unwired() -> None:
    with TestClient(_app(wire=False)) as client:
        r = client.get("/kb/kb-1/acl", headers=_HEADERS)
    assert r.status_code == 503
