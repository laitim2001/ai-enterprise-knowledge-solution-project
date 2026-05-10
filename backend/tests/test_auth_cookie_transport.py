"""W17 F2 — auth-transport hardening (httpOnly cookie + CSRF + /auth/refresh) tests.

Covers ADR-0022:
- `POST /auth/login` + `POST /auth/verify-email` (verified-transition) set the
  httpOnly `ekp_session` cookie + the readable `ekp_csrf` double-submit cookie;
  the token is still in the JSON body for API/CLI clients.
- `get_current_user` dual-path: cookie takes precedence; a present-but-invalid
  cookie falls through to Bearer / mock; Bearer is CSRF-exempt.
- CSRF double-submit enforced on cookie-authenticated state-changing requests
  (POST/PUT/PATCH/DELETE) — missing/mismatched `X-CSRF-Token` → 403; GET exempt.
- `POST /auth/refresh` rotates the session token + both cookies (revokes the old
  one); mock dev mode keeps returning the fixed dev-token (no cookie).
- `POST /auth/logout` revokes the session + clears both cookies.

Fresh FastAPI sub-app per fixture (parallel to test_auth_self_register.py) so
module-level dependency overrides don't leak across files.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from api.auth import users_repo
from api.auth.cookies import CSRF_COOKIE, SESSION_COOKIE
from api.auth.dependency import get_current_user
from api.auth.email_provider import get_email_provider
from api.auth.models import AuthenticatedUser
from api.error_handlers import register_error_handlers
from api.routes.auth import router as auth_router
from storage.settings import Settings, get_settings

_VALID_PASSWORD = "Aa1secret!"


class _CapturingEmailProvider:
    def __init__(self) -> None:
        self.sent: list[dict[str, str]] = []

    async def send_verification(self, *, to_email: str, code: str, display_name: str) -> None:
        self.sent.append({"to_email": to_email, "code": code, "display_name": display_name})

    @property
    def last_code(self) -> str:
        assert self.sent, "no verification email sent"
        return self.sent[-1]["code"]


@pytest.fixture
def email_capture() -> _CapturingEmailProvider:
    return _CapturingEmailProvider()


@pytest.fixture
def app(email_capture: _CapturingEmailProvider) -> Iterator[FastAPI]:
    users_repo.reset_repo()
    instance = FastAPI()
    register_error_handlers(instance)
    # feature_auth_mock=True so the cookie-fallthrough + mock-refresh paths work;
    # the cookie path is independent of the mock flag (real cookie always wins).
    settings = Settings(feature_auth_mock=True)
    instance.dependency_overrides[get_settings] = lambda: settings
    instance.dependency_overrides[get_email_provider] = lambda: email_capture
    instance.include_router(auth_router)

    @instance.get("/protected")
    def _protected(user: AuthenticatedUser = Depends(get_current_user)) -> dict[str, Any]:  # noqa: B008
        return {"oid": user.oid, "tid": user.tid, "is_mock": user.is_mock}

    @instance.post("/mutate")
    def _mutate(user: AuthenticatedUser = Depends(get_current_user)) -> dict[str, Any]:  # noqa: B008
        return {"oid": user.oid, "tid": user.tid, "is_mock": user.is_mock}

    yield instance
    users_repo.reset_repo()


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    return TestClient(app)


def _register_verified(client: TestClient, email_capture: _CapturingEmailProvider, email: str = "alice@example.com") -> dict[str, Any]:
    """Register + verify (auto-login). Returns the verify-email JSON body. The
    TestClient cookie jar now carries ekp_session + ekp_csrf."""
    client.post("/auth/register", json={"email": email, "password": _VALID_PASSWORD, "display_name": "Alice"})
    resp = client.post("/auth/verify-email", json={"email": email, "code": email_capture.last_code})
    assert resp.status_code == 200
    return resp.json()


# --- Set-Cookie on auth success ----------------------------------------------


def test_login_sets_session_and_csrf_cookies(client: TestClient, email_capture: _CapturingEmailProvider) -> None:
    email = "bob@example.com"
    client.post("/auth/register", json={"email": email, "password": _VALID_PASSWORD, "display_name": "Bob"})
    client.post("/auth/verify-email", json={"email": email, "code": email_capture.last_code})
    # verify-email already set cookies (auto-login); clear them to isolate login.
    client.cookies.clear()
    resp = client.post("/auth/login", json={"email": email, "password": _VALID_PASSWORD})
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["access_token"]) >= 40
    set_cookie_blob = ", ".join(resp.headers.get_list("set-cookie"))
    assert "ekp_session=" in set_cookie_blob
    assert "httponly" in set_cookie_blob.lower()
    assert "ekp_csrf=" in set_cookie_blob
    assert "samesite=lax" in set_cookie_blob.lower()
    # local env (default) → no Secure flag so HTTP dev works.
    assert "secure" not in set_cookie_blob.lower()
    # Token in the body matches the session cookie value (Bearer transport parity).
    assert client.cookies.get(SESSION_COOKIE) == body["access_token"]
    assert client.cookies.get(CSRF_COOKIE) is not None


def test_verify_email_auto_login_sets_cookies_and_token(client: TestClient, email_capture: _CapturingEmailProvider) -> None:
    body = _register_verified(client, email_capture)
    assert body["user"]["verified"] is True
    assert body["access_token"] is not None
    assert body["expires_in"] is not None
    assert client.cookies.get(SESSION_COOKIE) == body["access_token"]
    assert client.cookies.get(CSRF_COOKIE) is not None


def test_verify_email_idempotent_already_verified_no_new_session(client: TestClient, email_capture: _CapturingEmailProvider) -> None:
    first = _register_verified(client, email_capture)
    # Re-submit the same code — already verified → no new session, no access_token.
    resp = client.post("/auth/verify-email", json={"email": "alice@example.com", "code": email_capture.last_code})
    assert resp.status_code == 200
    body = resp.json()
    assert body["user"]["verified"] is True
    assert body["access_token"] is None
    # Original session still valid (not rotated).
    assert client.cookies.get(SESSION_COOKIE) == first["access_token"]


# --- Cookie auth + CSRF on state-changing requests ---------------------------


def test_cookie_auth_get_works_without_csrf(client: TestClient, email_capture: _CapturingEmailProvider) -> None:
    body = _register_verified(client, email_capture)
    resp = client.get("/protected")  # cookie auto-sent; no Authorization header
    assert resp.status_code == 200
    assert resp.json()["oid"] == body["user"]["oid"]
    assert resp.json()["is_mock"] is False


def test_cookie_auth_post_without_csrf_header_is_403(client: TestClient, email_capture: _CapturingEmailProvider) -> None:
    _register_verified(client, email_capture)
    resp = client.post("/mutate")  # cookie present, no X-CSRF-Token
    assert resp.status_code == 403


def test_cookie_auth_post_with_matching_csrf_header_ok(client: TestClient, email_capture: _CapturingEmailProvider) -> None:
    body = _register_verified(client, email_capture)
    csrf = client.cookies.get(CSRF_COOKIE)
    assert csrf is not None
    resp = client.post("/mutate", headers={"X-CSRF-Token": csrf})
    assert resp.status_code == 200
    assert resp.json()["oid"] == body["user"]["oid"]


def test_cookie_auth_post_with_mismatched_csrf_header_is_403(client: TestClient, email_capture: _CapturingEmailProvider) -> None:
    _register_verified(client, email_capture)
    resp = client.post("/mutate", headers={"X-CSRF-Token": "not-the-cookie-value"})
    assert resp.status_code == 403


def test_bearer_auth_post_is_csrf_exempt(client: TestClient, email_capture: _CapturingEmailProvider) -> None:
    body = _register_verified(client, email_capture)
    token = body["access_token"]
    # Drop the cookies so only the Bearer is in play.
    client.cookies.clear()
    resp = client.post("/mutate", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["oid"] == body["user"]["oid"]


def test_mock_bearer_post_is_csrf_exempt(client: TestClient) -> None:
    # No cookie, mock dev-token bearer → mock path, no CSRF check.
    resp = client.post("/mutate", headers={"Authorization": "Bearer dev-token"})
    assert resp.status_code == 200
    assert resp.json()["is_mock"] is True


def test_invalid_session_cookie_falls_through_to_mock(client: TestClient) -> None:
    client.cookies.set(SESSION_COOKIE, "stale-or-forged-token")
    # GET so no CSRF concern; cookie doesn't resolve → mock dev-token bearer wins.
    resp = client.get("/protected", headers={"Authorization": "Bearer dev-token"})
    assert resp.status_code == 200
    assert resp.json()["is_mock"] is True


# --- /auth/refresh rotation --------------------------------------------------


def test_refresh_rotates_session_and_cookies(client: TestClient, email_capture: _CapturingEmailProvider) -> None:
    body = _register_verified(client, email_capture)
    old_token = body["access_token"]
    csrf = client.cookies.get(CSRF_COOKIE)
    assert csrf is not None
    resp = client.post("/auth/refresh", headers={"X-CSRF-Token": csrf})
    assert resp.status_code == 200
    new_token = resp.json()["access_token"]
    assert resp.json()["is_mock"] is False
    assert new_token != old_token
    # Cookies rotated to the new token.
    assert client.cookies.get(SESSION_COOKIE) == new_token
    # Old token revoked, new token resolves.
    assert users_repo.resolve_session(old_token) is None
    assert users_repo.resolve_session(new_token) is not None


def test_refresh_without_credentials_is_401(client: TestClient) -> None:
    resp = client.post("/auth/refresh")  # no cookie, no bearer
    assert resp.status_code == 401


def test_refresh_mock_mode_returns_dev_token_no_cookie(client: TestClient) -> None:
    resp = client.post("/auth/refresh", headers={"Authorization": "Bearer dev-token"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["is_mock"] is True
    assert body["access_token"] == "dev-token"
    assert "ekp_session" not in ", ".join(resp.headers.get_list("set-cookie"))


# --- /auth/logout cookie clear -----------------------------------------------


def test_logout_clears_cookies_and_revokes_session(client: TestClient, email_capture: _CapturingEmailProvider) -> None:
    body = _register_verified(client, email_capture)
    token = body["access_token"]
    csrf = client.cookies.get(CSRF_COOKIE)
    assert csrf is not None
    resp = client.post("/auth/logout", headers={"X-CSRF-Token": csrf})
    assert resp.status_code == 200
    set_cookie_blob = ", ".join(resp.headers.get_list("set-cookie")).lower()
    assert "ekp_session=" in set_cookie_blob  # cleared (Max-Age=0)
    assert "ekp_csrf=" in set_cookie_blob
    # TestClient applied the expiry → cookies gone, session revoked.
    assert client.cookies.get(SESSION_COOKIE) is None
    assert users_repo.resolve_session(token) is None
