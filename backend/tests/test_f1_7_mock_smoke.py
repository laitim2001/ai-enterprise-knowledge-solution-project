"""W7 D5 F1.7-mock end-to-end smoke (W7 closeout substitute).

Reconstructs the production `api.server.app` wiring (auth Depends + rate
limiter middleware + audit log middleware + error handlers + auth routes)
against a *fresh* Settings(feature_auth_mock=True) so the test is hermetic
from the local `.env` state.

Verifies the full F1.3 + F1.4 + F1.5 + F2 + F3 + F4.1 chain end-to-end:
1. dev-token bearer → 200 + `_DEV_USER` identity reaches the route body
2. invalid bearer → 401 + ApiError envelope (F4.1) + WWW-Authenticate header
3. F2 rate-key uses mock `oid` (per-user budget enforced; per-IP fallback
   only when caller has no bearer)
4. F3 audit tag emits `user_id=mock_oid` + `tenant_id=mock_tid` +
   `audit_action="<METHOD> <path>"` + `request_id` round-trip
5. Burst exceed → 429 + ApiError envelope (F4.1) + Retry-After header

This is the W7 closeout F1.7-mock substitute per plan §2 F1 a-revised
2026-05-05; LIVE F1.7 (real Entra ID) lands W8 D4 post-IT cred delivery.
"""

from __future__ import annotations

import logging

import pytest
import structlog
from fastapi import APIRouter, Depends, FastAPI
from fastapi.testclient import TestClient

from api.auth import get_current_user
from api.auth.models import AuthenticatedUser
from api.error_handlers import register_error_handlers
from api.middleware import (
    REQUEST_ID_HEADER,
    AuditLogMiddleware,
    RateLimitMiddleware,
    reset_rate_limiter,
)
from api.routes.auth import router as auth_router
from storage.settings import Settings, get_settings


def _build_smoke_app(settings: Settings) -> FastAPI:
    """Mirror api/server.py wiring against an isolated Settings."""
    app = FastAPI()
    register_error_handlers(app)

    app.add_middleware(
        RateLimitMiddleware,
        settings=settings,
        protected_prefixes=("/echo", "/auth"),
    )
    app.add_middleware(
        AuditLogMiddleware,
        settings=settings,
        protected_prefixes=("/echo", "/auth"),
    )

    # Override get_settings so /auth/refresh + /auth/logout (which call
    # get_settings via their own Depends) see the test settings.
    app.dependency_overrides[get_settings] = lambda: settings

    # Mirror /query identity surface without the heavy retrieval pipeline:
    # one router with auth Depends so the F1.3 contract is exercised.
    echo_router = APIRouter(prefix="/echo", dependencies=[Depends(get_current_user)])

    @echo_router.get("/whoami")
    def whoami(user: AuthenticatedUser = Depends(get_current_user)) -> dict[str, str | bool]:  # noqa: B008
        return {
            "oid": user.oid,
            "tid": user.tid,
            "preferred_username": user.preferred_username,
            "is_mock": user.is_mock,
        }

    app.include_router(echo_router)
    app.include_router(auth_router)

    return app


@pytest.fixture
def smoke_settings() -> Settings:
    return Settings(
        feature_auth_mock=True,
        rate_limit_enabled=True,
        rate_limit_per_minute=3,
        rate_limit_concurrent=5,
    )


@pytest.fixture
def smoke_client(smoke_settings: Settings) -> TestClient:
    reset_rate_limiter()
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
    )
    app = _build_smoke_app(smoke_settings)
    return TestClient(app, raise_server_exceptions=False)


def _bearer(settings: Settings) -> dict[str, str]:
    return {"Authorization": f"Bearer {settings.auth_mock_bearer_token}"}


# ---------------------------------------------------------------------------
# 1. dev-token bearer → 200 + _DEV_USER identity reaches route body
# ---------------------------------------------------------------------------


def test_smoke_1_dev_token_returns_dev_user(
    smoke_client: TestClient, smoke_settings: Settings
) -> None:
    response = smoke_client.get("/echo/whoami", headers=_bearer(smoke_settings))

    assert response.status_code == 200
    body = response.json()
    assert body["oid"] == smoke_settings.auth_mock_oid
    assert body["tid"] == smoke_settings.auth_mock_tid
    assert body["preferred_username"] == smoke_settings.auth_mock_preferred_username
    assert body["is_mock"] is True


# ---------------------------------------------------------------------------
# 2. invalid bearer → 401 + ApiError envelope (F4.1) + WWW-Authenticate
# ---------------------------------------------------------------------------


def test_smoke_2_invalid_bearer_returns_envelope_401(smoke_client: TestClient) -> None:
    response = smoke_client.get(
        "/echo/whoami", headers={"Authorization": "Bearer not-the-token"}
    )

    assert response.status_code == 401
    body = response.json()
    assert body["error"]["code"] == "auth.unauthorized"
    assert body["error"]["actionable_hint"] is not None
    assert response.headers.get("WWW-Authenticate") == "Bearer"


def test_smoke_2b_no_bearer_returns_envelope_401(smoke_client: TestClient) -> None:
    response = smoke_client.get("/echo/whoami")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "auth.unauthorized"


# ---------------------------------------------------------------------------
# 3. F2 rate-key uses mock oid (per-user) + 5. burst → 429 envelope
# ---------------------------------------------------------------------------


def test_smoke_3_burst_exceed_returns_envelope_429_with_retry_after(
    smoke_client: TestClient, smoke_settings: Settings
) -> None:
    # rate_limit_per_minute=3 → 3 calls allowed, 4th exceeds.
    statuses = [
        smoke_client.get("/echo/whoami", headers=_bearer(smoke_settings)).status_code
        for _ in range(5)
    ]
    assert statuses[:3] == [200, 200, 200]
    assert 429 in statuses[3:]

    # Verify the 429 carries the F4.1 envelope shape.
    response = smoke_client.get("/echo/whoami", headers=_bearer(smoke_settings))
    assert response.status_code == 429
    body = response.json()
    assert body["error"]["code"] == "rate_limit.exceeded"
    assert body["error"]["actionable_hint"] is not None
    assert "Retry-After" in response.headers


def test_smoke_3b_per_user_isolation(
    smoke_client: TestClient, smoke_settings: Settings
) -> None:
    """Two distinct mock oids must not share a rate budget.

    Achieved here by exhausting the dev-token bucket then verifying an
    *unauthenticated* call (IP fallback, distinct key) is independent.
    """
    for _ in range(3):
        smoke_client.get("/echo/whoami", headers=_bearer(smoke_settings))
    # 4th dev-token call exceeds.
    over = smoke_client.get("/echo/whoami", headers=_bearer(smoke_settings))
    assert over.status_code == 429
    # Unauth call resolves to IP key — independent budget — first 3 succeed
    # at the 401 layer (auth Depends rejects), proving rate-limiter did NOT
    # consume the dev-token bucket for unauth callers.
    unauth = smoke_client.get("/echo/whoami")
    assert unauth.status_code == 401


# ---------------------------------------------------------------------------
# 4. F3 audit tag emits user_id=mock_oid + tenant_id=mock_tid + request_id
# ---------------------------------------------------------------------------


def test_smoke_4_audit_emits_mock_identity(
    smoke_client: TestClient,
    smoke_settings: Settings,
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO, logger="ekp.audit")

    response = smoke_client.get(
        "/echo/whoami",
        headers={**_bearer(smoke_settings), REQUEST_ID_HEADER: "smoke-trace-001"},
    )
    assert response.status_code == 200
    assert response.headers.get(REQUEST_ID_HEADER) == "smoke-trace-001"

    audit_lines = [r.getMessage() for r in caplog.records if r.name == "ekp.audit"]
    assert audit_lines, "no audit_log event captured"
    blob = "\n".join(audit_lines)
    assert smoke_settings.auth_mock_oid in blob
    assert smoke_settings.auth_mock_tid in blob
    assert "GET /echo/whoami" in blob
    assert "smoke-trace-001" in blob


def test_smoke_4b_audit_captures_429_on_rate_limit(
    smoke_client: TestClient,
    smoke_settings: Settings,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Audit middleware sits OUTERMOST so 429 from rate limiter is still audited."""
    caplog.set_level(logging.INFO, logger="ekp.audit")

    for _ in range(4):
        smoke_client.get("/echo/whoami", headers=_bearer(smoke_settings))

    audit_lines = [r.getMessage() for r in caplog.records if r.name == "ekp.audit"]
    blob = "\n".join(audit_lines)
    # At least one entry should record status_code=429.
    assert "429" in blob


# ---------------------------------------------------------------------------
# 6. /auth/refresh + /auth/logout end-to-end (F1.5 integration)
# ---------------------------------------------------------------------------


def test_smoke_5_auth_refresh_round_trip(
    smoke_client: TestClient, smoke_settings: Settings
) -> None:
    response = smoke_client.post("/auth/refresh", headers=_bearer(smoke_settings))
    assert response.status_code == 200
    body = response.json()
    assert body["access_token"] == smoke_settings.auth_mock_bearer_token
    assert body["is_mock"] is True


def test_smoke_5b_auth_logout_round_trip(
    smoke_client: TestClient, smoke_settings: Settings
) -> None:
    response = smoke_client.post("/auth/logout", headers=_bearer(smoke_settings))
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
