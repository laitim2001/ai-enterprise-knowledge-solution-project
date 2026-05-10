"""C11 — W7 F1.2.1 mock MSAL middleware unit tests (F1.6 partial).

Covers the dev-only path; real MSAL JWT validation tests land W8 D2-D3 once
`msal_provider.py` is wired beyond the fail-closed skeleton.
"""

from __future__ import annotations

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from starlette.requests import Request

from api.auth.dependency import get_current_user
from api.auth.mock_msal import authenticate_mock
from api.auth.models import AuthenticatedUser
from api.auth.msal_provider import authenticate_msal
from storage.settings import Settings


def _settings(*, mock: bool = True) -> Settings:
    return Settings(feature_auth_mock=mock)


def _bare_request() -> Request:
    """Minimal ASGI Request — GET, no cookies (W17 F2 `get_current_user` takes one)."""
    return Request({"type": "http", "method": "GET", "headers": []})


def test_authenticate_mock_accepts_dev_token_and_returns_dev_user() -> None:
    settings = _settings()
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="dev-token")

    user = authenticate_mock(creds, settings)

    assert isinstance(user, AuthenticatedUser)
    assert user.is_mock is True
    assert user.oid == settings.auth_mock_oid
    assert user.tid == settings.auth_mock_tid
    assert user.preferred_username == settings.auth_mock_preferred_username


def test_authenticate_mock_rejects_missing_credentials() -> None:
    with pytest.raises(HTTPException) as exc:
        authenticate_mock(None, _settings())
    assert exc.value.status_code == 401
    assert exc.value.headers == {"WWW-Authenticate": "Bearer"}


def test_authenticate_mock_rejects_wrong_scheme() -> None:
    creds = HTTPAuthorizationCredentials(scheme="Basic", credentials="dev-token")
    with pytest.raises(HTTPException) as exc:
        authenticate_mock(creds, _settings())
    assert exc.value.status_code == 401


def test_authenticate_mock_rejects_invalid_token() -> None:
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="not-the-token")
    with pytest.raises(HTTPException) as exc:
        authenticate_mock(creds, _settings())
    assert exc.value.status_code == 401


def test_authenticate_msal_skeleton_fails_closed_until_w8() -> None:
    """W7 D1 skeleton must reject so dev never silently bypasses real auth."""
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="any")
    with pytest.raises(HTTPException) as exc:
        authenticate_msal(creds, _settings(mock=False))
    assert exc.value.status_code == 503


def test_dependency_routes_to_mock_when_flag_true() -> None:
    settings = _settings(mock=True)
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="dev-token")

    user = get_current_user(_bare_request(), credentials=creds, settings=settings)

    assert user.is_mock is True


def test_dependency_routes_to_msal_when_flag_false_and_fails_closed() -> None:
    settings = _settings(mock=False)
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="dev-token")
    with pytest.raises(HTTPException) as exc:
        get_current_user(_bare_request(), credentials=creds, settings=settings)
    assert exc.value.status_code == 503
