"""C11 — FastAPI Depends single switching point (W7 F1.3 + W13 D5 F5.6 + W17 F2).

W7 baseline:

    auth_dependency = get_current_user_mock if settings.feature_auth_mock
                       else get_current_user_msal

W13 F5.6 (per ADR-0014 hybrid auth) — session-token branch sits in front of the
mock/MSAL fork: self-register users present a session bearer issued by
`POST /auth/login`, resolved via `users_repo.resolve_session` → returned as the
same `AuthenticatedUser` shape so downstream code stays provider-agnostic.

W17 F2 (per ADR-0022 auth-transport hardening) — the session token's primary
transport is now the httpOnly `ekp_session` cookie. Resolution order:
  1. `ekp_session` cookie (the SPA's self-register session). On a state-changing
     request (POST/PUT/PATCH/DELETE) the CSRF double-submit is enforced:
     `X-CSRF-Token` header must equal the `ekp_csrf` cookie, else 403.
  2. `Authorization: Bearer` — a session bearer (legacy / API clients), else the
     mock dev-token (`feature_auth_mock`), else real MSAL JWT. Bearer-authenticated
     requests are CSRF-exempt (a Bearer is never auto-attached by a browser).
A present-but-invalid cookie falls through to (2) so the mock + API-client paths
stay intact.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from storage.settings import Settings, get_settings

from . import users_repo
from .cookies import (
    CSRF_COOKIE,
    CSRF_HEADER,
    SESSION_COOKIE,
    STATE_CHANGING_METHODS,
    csrf_token_ok,
)
from .mock_msal import authenticate_mock
from .models import AuthenticatedUser
from .msal_provider import authenticate_msal

_bearer = HTTPBearer(auto_error=False)

BearerDep = Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_current_user(
    request: Request,
    credentials: BearerDep,
    settings: SettingsDep,
) -> AuthenticatedUser:
    """Single switching point — cookie session → bearer session → mock → MSAL.

    Tests can override `feature_auth_mock` per-case AND seed the sessions repo
    via `users_repo.create_session(...)`; the cookie path is exercised by
    sending the session token in an `ekp_session` cookie (+ a matching
    `ekp_csrf` cookie / `X-CSRF-Token` header on non-GET).
    """

    # 1. Cookie path — the SPA's self-register session (takes precedence).
    session_cookie = request.cookies.get(SESSION_COOKIE)
    if session_cookie:
        session_user = users_repo.resolve_session(session_cookie)
        if session_user is not None:
            if request.method in STATE_CHANGING_METHODS and not csrf_token_ok(
                request.headers.get(CSRF_HEADER), request.cookies.get(CSRF_COOKIE)
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="CSRF token missing or invalid",
                )
            return session_user
        # Cookie present but invalid/expired → fall through to the bearer paths.

    # 2. Bearer path — session bearer (legacy / API clients) → mock → MSAL.
    if credentials is not None and credentials.scheme.lower() == "bearer":
        session_user = users_repo.resolve_session(credentials.credentials)
        if session_user is not None:
            return session_user

    if settings.feature_auth_mock:
        return authenticate_mock(credentials, settings)
    return authenticate_msal(credentials, settings)
