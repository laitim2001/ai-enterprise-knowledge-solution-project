"""C08 — W7 D2 F2 token-bucket rate limiter (per architecture.md §8.1 R5).

Per-user (mock `oid` from F1.2.1, real Entra ID `oid` from W8 D4) rate
limiting with per-IP fallback when an unauthenticated/unidentified caller
slips through. 50 req/min + 5 concurrent active queries per architecture.md
§8.1 R5 spec.

In-process state store. Production multi-replica deploy (W8 ACA) will swap
the backing store to Redis or Azure Cache; the protocol here is intentionally
in-memory dict so W7 dev mode works without external dependency.

Karpathy §1.2 simplicity-first: token bucket implemented from scratch
(~50 lines) instead of importing slowapi/limits — zero new dep, deterministic
behaviour for unit tests.
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Awaitable, Callable, Iterable
from dataclasses import dataclass, field

from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware

from api.auth.mock_msal import authenticate_mock
from api.auth.msal_provider import authenticate_msal
from storage.settings import Settings


@dataclass
class _Bucket:
    """Single-key token bucket + concurrent counter."""

    refill_per_minute: int
    tokens: float = field(init=False)
    last_refill: float = field(init=False)
    concurrent: int = 0
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    def __post_init__(self) -> None:
        self.tokens = float(self.refill_per_minute)
        self.last_refill = time.monotonic()

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self.last_refill
        if elapsed <= 0:
            return
        rate_per_second = self.refill_per_minute / 60.0
        self.tokens = min(
            float(self.refill_per_minute),
            self.tokens + elapsed * rate_per_second,
        )
        self.last_refill = now

    async def try_acquire(self, *, concurrent_cap: int) -> tuple[bool, float]:
        """Return (allowed, retry_after_seconds). retry_after meaningful only when not allowed."""
        async with self._lock:
            self._refill()
            if self.concurrent >= concurrent_cap:
                return False, 1.0
            if self.tokens < 1.0:
                rate_per_second = self.refill_per_minute / 60.0
                retry_after = max(1.0, (1.0 - self.tokens) / rate_per_second)
                return False, retry_after
            self.tokens -= 1.0
            self.concurrent += 1
            return True, 0.0

    async def release(self) -> None:
        async with self._lock:
            if self.concurrent > 0:
                self.concurrent -= 1


class RateLimiter:
    """Per-key token bucket store. Key = `oid:<oid>` when authenticated, else `ip:<host>`."""

    def __init__(self, *, per_minute: int, concurrent: int) -> None:
        self._per_minute = per_minute
        self._concurrent = concurrent
        self._buckets: dict[str, _Bucket] = {}
        self._store_lock = asyncio.Lock()

    async def _get(self, key: str) -> _Bucket:
        async with self._store_lock:
            bucket = self._buckets.get(key)
            if bucket is None:
                bucket = _Bucket(refill_per_minute=self._per_minute)
                self._buckets[key] = bucket
            return bucket

    async def acquire(self, key: str) -> tuple[bool, float]:
        bucket = await self._get(key)
        return await bucket.try_acquire(concurrent_cap=self._concurrent)

    async def release(self, key: str) -> None:
        bucket = await self._get(key)
        await bucket.release()


_singleton: RateLimiter | None = None


def get_rate_limiter(settings: Settings) -> RateLimiter:
    """Process-wide singleton rate limiter (W7 in-memory; W8+ Redis-backed)."""
    global _singleton
    if _singleton is None:
        _singleton = RateLimiter(
            per_minute=settings.rate_limit_per_minute,
            concurrent=settings.rate_limit_concurrent,
        )
    return _singleton


def reset_rate_limiter() -> None:
    """Test-only — discard the singleton so each test starts with empty buckets."""
    global _singleton
    _singleton = None


def _parse_bearer(request: Request) -> str | None:
    auth = request.headers.get("Authorization")
    if not auth:
        return None
    scheme, _, token = auth.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None
    return token


def _identity_key(request: Request, settings: Settings) -> str:
    """Resolve rate-limit key — `oid:<oid>` when authenticated, else `ip:<host>`.

    Routes through the same authenticate_{mock,msal} validators so the
    rate-limit identity decision shares one source of truth with the auth
    Depends. Validation failure → IP fallback (auth Depends on the same
    request will surface the 401 cleanly).
    """
    from fastapi import HTTPException
    from fastapi.security import HTTPAuthorizationCredentials

    token = _parse_bearer(request)
    creds = (
        HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        if token
        else None
    )
    try:
        if settings.feature_auth_mock:
            user = authenticate_mock(creds, settings)
        else:
            user = authenticate_msal(creds, settings)
        return f"oid:{user.oid}"
    except HTTPException:
        client = request.client
        ip = client.host if client else "unknown"
        return f"ip:{ip}"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Acquire on request, release on response (success or exception).

    Path-prefix scoped via `protected_prefixes` so /health stays unmetered.
    """

    def __init__(
        self,
        app,
        *,
        settings: Settings,
        protected_prefixes: Iterable[str],
    ) -> None:
        super().__init__(app)
        self._settings = settings
        self._prefixes = tuple(protected_prefixes)

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        if not self._settings.rate_limit_enabled:
            return await call_next(request)

        path = request.url.path
        if not any(path == p or path.startswith(f"{p}/") or path == p for p in self._prefixes):
            return await call_next(request)
        # also match exact prefix without trailing slash (e.g. "/kb")
        if not any(path.startswith(p) for p in self._prefixes):
            return await call_next(request)

        limiter = get_rate_limiter(self._settings)
        key = _identity_key(request, self._settings)
        allowed, retry_after = await limiter.acquire(key)
        if not allowed:
            return Response(
                content='{"detail":"Rate limit exceeded — see Retry-After header"}',
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                media_type="application/json",
                headers={"Retry-After": str(max(1, int(retry_after)))},
            )

        try:
            response = await call_next(request)
        finally:
            await limiter.release(key)
        return response
