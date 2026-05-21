"""C11 — W7 F1.2.1 mock MSAL dev-only middleware.

Returns a fixed `_DEV_USER` identity matching the real MSAL JWT claim shape so
downstream F2 rate-key + F3 audit-tag exercise the same code path whether dev
or LIVE. Activated by `Settings.feature_auth_mock=True` (default False).

Karpathy §1.3 surgical: zero impact on production code path — when
`feature_auth_mock=False` (default + W8 D4 onwards) this module is never imported
by the auth dependency. C11 component design intent preserved.
"""

from __future__ import annotations

from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials

from storage.settings import Settings

from .models import AuthenticatedUser


def authenticate_mock(
    credentials: HTTPAuthorizationCredentials | None,
    settings: Settings,
) -> AuthenticatedUser:
    """Validate the dev bearer token and return the fixed _DEV_USER.

    Accept rule: `Authorization: Bearer <settings.auth_mock_bearer_token>`.
    Anything else → 401 with the same error contract real MSAL will use, so the
    F1.6 unit tests stay valid after W8 D4 LIVE switch.
    """

    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or malformed Authorization header (expected 'Bearer <token>')",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if credentials.credentials != settings.auth_mock_bearer_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid bearer token (mock mode expects Settings.auth_mock_bearer_token)",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return AuthenticatedUser(
        oid=settings.auth_mock_oid,
        tid=settings.auth_mock_tid,
        preferred_username=settings.auth_mock_preferred_username,
        role=settings.auth_mock_role,
        is_mock=True,
    )
