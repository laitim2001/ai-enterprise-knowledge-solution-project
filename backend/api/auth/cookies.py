"""C11 — session cookie + CSRF helpers (W17 F2 / ADR-0022).

httpOnly `ekp_session` carries the self-register session token (XSS-unreadable);
non-httpOnly `ekp_csrf` carries a double-submit CSRF token the SPA reads from
`document.cookie` and echoes back via the `X-CSRF-Token` header on non-GET
requests. `dependency.get_current_user` enforces the match on cookie-authenticated
state-changing requests (Bearer-authenticated requests are CSRF-exempt — a Bearer
is never auto-attached by a browser).

`Secure` is env-gated (`settings.environment != "local"`) so local HTTP dev
works. `SameSite=Lax` survives the SSO top-level-redirect round-trip per ADR-0022
(`Strict` would drop the cookie coming back from `login.microsoftonline.com`).
"""

from __future__ import annotations

import secrets

from fastapi import Response

from api.auth.security import SESSION_TOKEN_TTL_SEC
from storage.settings import Settings

SESSION_COOKIE = "ekp_session"
CSRF_COOKIE = "ekp_csrf"
CSRF_HEADER = "X-CSRF-Token"

_CSRF_TOKEN_BYTES = 32
# Browser-auto-attached methods that mutate state → require the CSRF double-submit.
STATE_CHANGING_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})


def generate_csrf_token() -> str:
    """URL-safe 256-bit random double-submit CSRF token."""
    return secrets.token_urlsafe(_CSRF_TOKEN_BYTES)


def set_session_cookies(
    response: Response, settings: Settings, session_token: str
) -> str:
    """Set `ekp_session` (httpOnly) + `ekp_csrf` (readable) on `response`.

    Returns the freshly minted CSRF token so the caller can also surface it in
    the JSON body if a client wants it (the SPA reads it from the cookie, so
    this is optional convenience).
    """
    csrf = generate_csrf_token()
    secure = settings.environment != "local"
    response.set_cookie(
        SESSION_COOKIE,
        session_token,
        max_age=SESSION_TOKEN_TTL_SEC,
        path="/",
        samesite="lax",
        secure=secure,
        httponly=True,
    )
    response.set_cookie(
        CSRF_COOKIE,
        csrf,
        max_age=SESSION_TOKEN_TTL_SEC,
        path="/",
        samesite="lax",
        secure=secure,
        httponly=False,
    )
    return csrf


def clear_session_cookies(response: Response) -> None:
    """Expire both auth cookies (logout)."""
    response.delete_cookie(SESSION_COOKIE, path="/")
    response.delete_cookie(CSRF_COOKIE, path="/")


def csrf_token_ok(header_token: str | None, cookie_token: str | None) -> bool:
    """Constant-time double-submit check — both present and equal."""
    if not header_token or not cookie_token:
        return False
    return secrets.compare_digest(header_token, cookie_token)
