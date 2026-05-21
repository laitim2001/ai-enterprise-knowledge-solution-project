"""C11 — W8 D2 F1.2 real Microsoft Entra ID JWT validator.

Backend = resource server: validates JWT issued by Entra ID v2.0 to client
apps (frontend msal-react W8 D3 F1.3). Token acquisition is NOT done here.

Validation chain (per Microsoft "Validate tokens" guidance):
  1. Parse JWT header → extract `kid`
  2. Fetch JWKS from `azure_jwks_uri_template` (with TTL cache; ~24h rotation)
  3. Locate signing key by `kid`; reject if missing
  4. Verify signature (RS256 only — Entra ID standard)
  5. Verify `iss` matches `azure_jwt_issuer_template`
  6. Verify `aud` matches `azure_client_id`
  7. Verify `exp` not in past + `nbf` not in future (jose handles)
  8. Build AuthenticatedUser from `oid` + `tid` + `preferred_username`

All failures collapse to HTTP 401 with safe message — never leak the
inner JWT/jose error to the client (CLAUDE.md §5.5 H5).

Karpathy §1.2 simplicity-first: backend doesn't need msal Python SDK
since frontend handles token acquisition; python-jose[cryptography] +
existing httpx (JWKS fetch) suffices. Single new dep, focused scope.
"""

from __future__ import annotations

import time
from typing import Any

import httpx
import structlog
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from jose import jwt
from jose.exceptions import ExpiredSignatureError, JOSEError, JWTClaimsError, JWTError

from storage.settings import Settings

from .models import AuthenticatedUser

_logger = structlog.get_logger("ekp.auth.msal")

# Module-level cache: { tenant_id: (fetched_at_monotonic, jwks_dict) }.
# Re-used across requests; reset_jwks_cache() exposed for tests.
_jwks_cache: dict[str, tuple[float, dict[str, Any]]] = {}


def reset_jwks_cache() -> None:
    """Test-only: drop cached JWKS so each test starts cold."""
    _jwks_cache.clear()


def _fetch_jwks(uri: str) -> dict[str, Any]:
    """Synchronous JWKS fetch — runs inside the request handler thread.

    httpx.Client (sync) chosen over AsyncClient because authenticate_msal is
    a sync function called from a sync FastAPI Depends. Cached aggressively
    so the actual network call only fires every `jwks_cache_ttl_s`.
    """
    with httpx.Client(timeout=5.0) as client:
        response = client.get(uri)
        response.raise_for_status()
        return response.json()


def _get_jwks(settings: Settings) -> dict[str, Any]:
    if not settings.azure_tenant_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="azure_tenant_id not configured — populate via Key Vault (W8 F2.4).",
        )

    cached = _jwks_cache.get(settings.azure_tenant_id)
    now = time.monotonic()
    if cached is not None:
        fetched_at, jwks = cached
        if now - fetched_at < settings.jwks_cache_ttl_s:
            return jwks

    uri = settings.azure_jwks_uri_template.format(tenant_id=settings.azure_tenant_id)
    try:
        jwks = _fetch_jwks(uri)
    except Exception as exc:
        # Server-side detail logged; client-facing 503 generic.
        _logger.error("jwks_fetch_failed", uri=uri, error=repr(exc))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Identity provider temporarily unavailable.",
        ) from exc

    _jwks_cache[settings.azure_tenant_id] = (now, jwks)
    return jwks


def _select_signing_key(jwks: dict[str, Any], kid: str | None) -> dict[str, Any]:
    if not kid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="JWT header missing 'kid'.",
            headers={"WWW-Authenticate": "Bearer error=invalid_token"},
        )
    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            return key
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No matching signing key for 'kid'.",
        headers={"WWW-Authenticate": "Bearer error=invalid_token"},
    )


# W24c F3 — RBAC roles a real Entra token may grant. Power User is Tier 2
# (CLAUDE.md H4), so a `power` claim is downgraded to least-privilege 'user'.
_TIER1_GRANTABLE_ROLES = frozenset({"admin", "editor", "user"})


def _role_from_claims(claims: dict[str, Any]) -> str:
    """Pick the EKP RBAC role from the Entra app-role claim.

    Entra app registration assigns security groups / users to app roles; the
    JWT carries them in the `roles` claim. The first recognised Tier 1 role
    wins; anything unrecognised — incl. a Tier 2 `power` claim — falls back to
    'user' (least privilege). Group-GUID-based resolution stays a
    config-of-record in `admin_identity.RoleMappingConfig` (per W24c progress D3).
    """
    raw_roles = claims.get("roles", [])
    if isinstance(raw_roles, list):
        for raw in raw_roles:
            if isinstance(raw, str) and raw in _TIER1_GRANTABLE_ROLES:
                return raw
    return "user"


def authenticate_msal(
    credentials: HTTPAuthorizationCredentials | None,
    settings: Settings,
) -> AuthenticatedUser:
    """Validate a real Entra ID JWT and return the authenticated user."""

    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or malformed Authorization header (expected 'Bearer <token>')",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = credentials.credentials

    if not settings.azure_tenant_id or not settings.azure_client_id:
        # Fail-closed when config incomplete — prevents silent bypass W7 D1
        # behaviour preserved while real wire is rolling out.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "MSAL validator config incomplete (azure_tenant_id / "
                "azure_client_id). Set Settings.feature_auth_mock=True for dev."
            ),
        )

    # 1-3. JWKS + kid → signing key.
    try:
        unverified_header = jwt.get_unverified_header(token)
    except JOSEError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed JWT.",
            headers={"WWW-Authenticate": "Bearer error=invalid_token"},
        ) from exc

    jwks = _get_jwks(settings)
    signing_key = _select_signing_key(jwks, unverified_header.get("kid"))

    # 4-7. Signature + iss + aud + exp/nbf.
    issuer = settings.azure_jwt_issuer_template.format(tenant_id=settings.azure_tenant_id)
    try:
        claims = jwt.decode(
            token,
            signing_key,
            algorithms=["RS256"],
            audience=settings.azure_client_id,
            issuer=issuer,
            options={"require_exp": True, "verify_at_hash": False},
        )
    except ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired.",
            headers={"WWW-Authenticate": "Bearer error=invalid_token"},
        ) from exc
    except JWTClaimsError as exc:
        # Audience or issuer mismatch — generic message, log specific server-side.
        _logger.warning("jwt_claims_invalid", error=repr(exc))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token claims invalid (audience/issuer).",
            headers={"WWW-Authenticate": "Bearer error=invalid_token"},
        ) from exc
    except JWTError as exc:
        _logger.warning("jwt_decode_failed", error=repr(exc))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token signature.",
            headers={"WWW-Authenticate": "Bearer error=invalid_token"},
        ) from exc

    # 8. Build identity. Entra ID v2.0 always provides `oid` + `tid`; some
    # token flavours surface `preferred_username` while others use `upn` —
    # fall back so guest accounts / B2B users still resolve.
    oid = claims.get("oid")
    tid = claims.get("tid")
    if not oid or not tid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing required claims (oid/tid).",
            headers={"WWW-Authenticate": "Bearer error=invalid_token"},
        )
    preferred_username = (
        claims.get("preferred_username") or claims.get("upn") or claims.get("email") or oid
    )

    return AuthenticatedUser(
        oid=oid,
        tid=tid,
        preferred_username=preferred_username,
        role=_role_from_claims(claims),
        is_mock=False,
    )
