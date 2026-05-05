"""W7 D2 F2.4 — token-bucket rate limiter unit tests.

Covers per-key token-bucket behaviour + concurrent cap + middleware 429.
"""

from __future__ import annotations

import asyncio

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.middleware.rate_limit import (
    RateLimiter,
    RateLimitMiddleware,
    reset_rate_limiter,
)
from storage.settings import Settings


@pytest.fixture(autouse=True)
def _reset_limiter() -> None:
    reset_rate_limiter()


@pytest.mark.asyncio
async def test_acquire_within_budget_allowed() -> None:
    limiter = RateLimiter(per_minute=5, concurrent=5)
    for _ in range(5):
        allowed, _ = await limiter.acquire("oid:user-a")
        assert allowed is True
        await limiter.release("oid:user-a")


@pytest.mark.asyncio
async def test_burst_exceed_returns_not_allowed_with_retry_after() -> None:
    limiter = RateLimiter(per_minute=2, concurrent=5)
    for _ in range(2):
        allowed, _ = await limiter.acquire("oid:user-a")
        assert allowed is True
        await limiter.release("oid:user-a")

    allowed, retry_after = await limiter.acquire("oid:user-a")
    assert allowed is False
    assert retry_after >= 1.0


@pytest.mark.asyncio
async def test_concurrent_cap_enforced() -> None:
    limiter = RateLimiter(per_minute=100, concurrent=2)

    a, _ = await limiter.acquire("oid:user-a")
    b, _ = await limiter.acquire("oid:user-a")
    c, retry_after = await limiter.acquire("oid:user-a")

    assert (a, b) == (True, True)
    assert c is False
    assert retry_after >= 1.0

    await limiter.release("oid:user-a")
    d, _ = await limiter.acquire("oid:user-a")
    assert d is True


@pytest.mark.asyncio
async def test_per_key_isolation() -> None:
    limiter = RateLimiter(per_minute=1, concurrent=5)

    a, _ = await limiter.acquire("oid:user-a")
    assert a is True

    b, _ = await limiter.acquire("oid:user-b")
    assert b is True


def _build_app(settings: Settings) -> FastAPI:
    app = FastAPI()
    app.add_middleware(
        RateLimitMiddleware,
        settings=settings,
        protected_prefixes=("/protected",),
    )

    @app.get("/protected")
    def protected_route() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/public")
    def public_route() -> dict[str, str]:
        return {"status": "ok"}

    return app


def test_middleware_allows_within_budget() -> None:
    settings = Settings(
        feature_auth_mock=True,
        rate_limit_per_minute=10,
        rate_limit_concurrent=5,
    )
    app = _build_app(settings)
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {settings.auth_mock_bearer_token}"}

    for _ in range(5):
        response = client.get("/protected", headers=headers)
        assert response.status_code == 200


def test_middleware_returns_429_on_burst_exceed() -> None:
    reset_rate_limiter()
    settings = Settings(
        feature_auth_mock=True,
        rate_limit_per_minute=3,
        rate_limit_concurrent=5,
    )
    app = _build_app(settings)
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {settings.auth_mock_bearer_token}"}

    statuses = [client.get("/protected", headers=headers).status_code for _ in range(5)]
    assert statuses[:3] == [200, 200, 200]
    assert 429 in statuses[3:]

    rate_limited = next(
        client.get("/protected", headers=headers)
        for _ in range(1)
        if True
    )
    if rate_limited.status_code == 429:
        assert "Retry-After" in rate_limited.headers


def test_middleware_skips_unprotected_paths() -> None:
    reset_rate_limiter()
    settings = Settings(
        feature_auth_mock=True,
        rate_limit_per_minute=1,
        rate_limit_concurrent=5,
    )
    app = _build_app(settings)
    client = TestClient(app)

    for _ in range(10):
        response = client.get("/public")
        assert response.status_code == 200


def test_middleware_disabled_when_flag_false() -> None:
    reset_rate_limiter()
    settings = Settings(
        feature_auth_mock=True,
        rate_limit_enabled=False,
        rate_limit_per_minute=1,
        rate_limit_concurrent=5,
    )
    app = _build_app(settings)
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {settings.auth_mock_bearer_token}"}

    for _ in range(5):
        response = client.get("/protected", headers=headers)
        assert response.status_code == 200


def test_middleware_falls_back_to_ip_when_no_bearer() -> None:
    """Unauthenticated request hits IP bucket (auth Depends rejects 401 separately)."""
    reset_rate_limiter()
    settings = Settings(
        feature_auth_mock=True,
        rate_limit_per_minute=2,
        rate_limit_concurrent=5,
    )
    app = _build_app(settings)
    client = TestClient(app)

    statuses = [client.get("/protected").status_code for _ in range(4)]
    # First 2 ok via IP bucket, then 429 (4 calls > 2 per_minute).
    assert statuses.count(200) == 2
    assert statuses.count(429) == 2


def test_release_resets_concurrent() -> None:
    """Synchronous wrapper to verify release decrements counter via direct API."""

    async def _scenario() -> int:
        limiter = RateLimiter(per_minute=100, concurrent=1)
        await limiter.acquire("oid:x")
        denied, _ = await limiter.acquire("oid:x")
        assert denied is False
        await limiter.release("oid:x")
        allowed, _ = await limiter.acquire("oid:x")
        return 1 if allowed else 0

    assert asyncio.run(_scenario()) == 1
