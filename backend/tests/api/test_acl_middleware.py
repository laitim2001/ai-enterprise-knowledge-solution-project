"""ACL middleware tests — require_role dependency (W24c F3 per ADR-0027 Option A).

Covers F3.1 (`require_role` factory) + F3.2/F3.3 (role claim through the mock +
MSAL paths) + F3.4 (403-on-unauthorized contract). Real-MSAL JWT validation
itself is not exercised here (no live Entra) — only the role-extraction helper.
"""

from __future__ import annotations

import asyncio
from typing import Annotated

import pytest
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.testclient import TestClient

from api.auth.mock_msal import authenticate_mock
from api.auth.models import AuthenticatedUser
from api.auth.msal_provider import _role_from_claims
from api.middleware.acl import require_kb_acl, require_role
from storage.rbac_storage import InMemoryRbacBackend
from storage.settings import Settings, get_settings


def _user(role: str) -> AuthenticatedUser:
    return AuthenticatedUser(
        oid="oid-1", tid="tid-1", preferred_username="dev@ricoh.com", role=role
    )


# ---- F3.1 — require_role factory (direct _guard invocation) ----------------


def test_require_role_admits_matching_role() -> None:
    guard = require_role("admin")
    admin = _user("admin")
    assert guard(admin) is admin


def test_require_role_rejects_other_role_with_403() -> None:
    guard = require_role("admin")
    with pytest.raises(HTTPException) as exc:
        guard(_user("editor"))
    assert exc.value.status_code == 403


def test_require_role_accepts_any_of_multiple_allowed() -> None:
    guard = require_role("admin", "editor")
    assert guard(_user("editor")).role == "editor"
    with pytest.raises(HTTPException) as exc:
        guard(_user("user"))
    assert exc.value.status_code == 403


# ---- F3.4 — 403/401 contract in a real request flow ------------------------


def _guarded_app(mock_role: str) -> FastAPI:
    """A one-endpoint app gated by `require_role('admin')`, mock-auth wired."""
    app = FastAPI()

    @app.get("/admin-only")
    def admin_only(
        actor: Annotated[AuthenticatedUser, Depends(require_role("admin"))],
    ) -> dict[str, str]:
        return {"role": actor.role}

    app.dependency_overrides[get_settings] = lambda: Settings(
        feature_auth_mock=True, auth_mock_role=mock_role
    )
    return app


def test_guarded_endpoint_admits_admin() -> None:
    with TestClient(_guarded_app("admin")) as client:
        r = client.get("/admin-only", headers={"Authorization": "Bearer dev-token"})
    assert r.status_code == 200
    assert r.json() == {"role": "admin"}


def test_guarded_endpoint_rejects_editor_with_403() -> None:
    with TestClient(_guarded_app("editor")) as client:
        r = client.get("/admin-only", headers={"Authorization": "Bearer dev-token"})
    assert r.status_code == 403


def test_guarded_endpoint_401_without_credentials() -> None:
    with TestClient(_guarded_app("admin")) as client:
        r = client.get("/admin-only")
    assert r.status_code == 401


# ---- F3.2/F3.3 — role claim through the auth paths -------------------------


def test_authenticated_user_role_defaults_to_user() -> None:
    user = AuthenticatedUser(oid="o", tid="t", preferred_username="x@ricoh.com")
    assert user.role == "user"


def test_authenticate_mock_carries_settings_role() -> None:
    settings = Settings(feature_auth_mock=True, auth_mock_role="editor")
    creds = HTTPAuthorizationCredentials(
        scheme="Bearer", credentials=settings.auth_mock_bearer_token
    )
    assert authenticate_mock(creds, settings).role == "editor"


def test_role_from_claims_picks_app_role() -> None:
    assert _role_from_claims({"roles": ["editor"]}) == "editor"


def test_role_from_claims_falls_back_to_user() -> None:
    assert _role_from_claims({}) == "user"
    assert _role_from_claims({"roles": []}) == "user"
    assert _role_from_claims({"roles": ["bogus"]}) == "user"


def test_role_from_claims_downgrades_tier2_power() -> None:
    # Power User is Tier 2 (CLAUDE.md H4) — a `power` claim must not grant it.
    assert _role_from_claims({"roles": ["power"]}) == "user"


# ---- F8 — require_kb_acl ----------------------------------------------------


def _kb_app(
    mock_role: str, *, wire: bool = True
) -> tuple[FastAPI, InMemoryRbacBackend | None]:
    """A one-endpoint app gated by require_kb_acl('edit') on /kb/{kb_id}/probe."""
    app = FastAPI()
    backend = InMemoryRbacBackend() if wire else None

    @app.get("/kb/{kb_id}/probe")
    def probe(
        actor: Annotated[AuthenticatedUser, Depends(require_kb_acl("edit"))],
    ) -> dict[str, str]:
        return {"oid": actor.oid}

    if backend is not None:
        app.state.rbac_backend = backend
    app.dependency_overrides[get_settings] = lambda: Settings(
        feature_auth_mock=True, auth_mock_role=mock_role, auth_mock_oid="kb-tester"
    )
    return app, backend


def test_require_kb_acl_admits_admin_without_grant() -> None:
    app, _ = _kb_app("admin")
    with TestClient(app) as client:
        r = client.get("/kb/kb-1/probe", headers={"Authorization": "Bearer dev-token"})
    assert r.status_code == 200


def test_require_kb_acl_admits_user_with_sufficient_grant() -> None:
    app, backend = _kb_app("editor")
    assert backend is not None
    asyncio.run(
        backend.add_kb_acl(
            kb_id="kb-1", principal_type="user", principal_id="kb-tester",
            access_role="manage", granted_by="admin",
        )
    )
    with TestClient(app) as client:
        r = client.get("/kb/kb-1/probe", headers={"Authorization": "Bearer dev-token"})
    assert r.status_code == 200


def test_require_kb_acl_rejects_user_without_grant() -> None:
    app, _ = _kb_app("editor")
    with TestClient(app) as client:
        r = client.get("/kb/kb-1/probe", headers={"Authorization": "Bearer dev-token"})
    assert r.status_code == 403


def test_require_kb_acl_rejects_insufficient_role() -> None:
    app, backend = _kb_app("editor")
    assert backend is not None
    # query < edit — a query grant does not satisfy require_kb_acl('edit').
    asyncio.run(
        backend.add_kb_acl(
            kb_id="kb-1", principal_type="user", principal_id="kb-tester",
            access_role="query", granted_by="admin",
        )
    )
    with TestClient(app) as client:
        r = client.get("/kb/kb-1/probe", headers={"Authorization": "Bearer dev-token"})
    assert r.status_code == 403


def test_require_kb_acl_503_when_backend_unwired() -> None:
    app, _ = _kb_app("editor", wire=False)
    with TestClient(app) as client:
        r = client.get("/kb/kb-1/probe", headers={"Authorization": "Bearer dev-token"})
    assert r.status_code == 503
