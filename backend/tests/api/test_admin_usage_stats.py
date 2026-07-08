"""`GET /admin/usage-stats` route tests (W24-wave-c1 F4 per ADR-0026 Option B).

4-stat strip derived from `observability.realtime_cost.fetch_realtime_usage`
+ `cost_estimator.total_projected_daily_usd`. Tests inject the Langfuse client
via monkeypatch on `get_langfuse_client` so no real Langfuse server required.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routes.admin import usage_stats as admin_usage_stats


def _build_app() -> FastAPI:
    app = FastAPI()
    app.include_router(admin_usage_stats.router)
    return app


@pytest.fixture(autouse=True)
def _clean_settings_cache() -> Iterator[None]:
    from storage.settings import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_usage_stats_returns_4stat_shape_when_no_client(monkeypatch: pytest.MonkeyPatch) -> None:
    """Langfuse not wired → empty rows, realtime_status='no_client', 4-stat all zero."""
    monkeypatch.setattr(
        "api.routes.admin.usage_stats.get_langfuse_client", lambda: None
    )
    app = _build_app()
    with TestClient(app) as client:
        r = client.get("/admin/usage-stats")
        assert r.status_code == 200
        body = r.json()
        assert body["api_calls_24h"] == 0
        assert body["spend_today_usd"] == 0.0
        assert body["spend_pct_used"] == 0.0
        assert body["token_throughput_tpm"] == 0
        assert body["rate_limit_hits_24h"] == 0
        assert body["realtime_status"] == "no_client"


def test_usage_stats_aggregates_from_realtime_fetch(monkeypatch: pytest.MonkeyPatch) -> None:
    """Inject a fake client + fetcher returning 2 generation events."""
    from observability import realtime_cost

    fake_client = object()
    monkeypatch.setattr(
        "api.routes.admin.usage_stats.get_langfuse_client", lambda: fake_client
    )

    def fake_fetcher(_client: object, _window: int) -> list[dict[str, Any]]:
        return [
            {"model": "gpt-5-5", "input_tokens": 2000, "output_tokens": 500},
            {"model": "gpt-5-5", "input_tokens": 1500, "output_tokens": 400},
        ]

    monkeypatch.setattr(realtime_cost, "_default_fetcher", fake_fetcher)

    app = _build_app()
    with TestClient(app) as client:
        r = client.get("/admin/usage-stats")
        assert r.status_code == 200
        body = r.json()
        assert body["api_calls_24h"] == 2
        # Tokens summed: 2000+500+1500+400 = 4400 → 4400 // (24*60=1440) = 3 TPM
        assert body["token_throughput_tpm"] == 3
        assert body["spend_today_usd"] > 0  # gpt-5-5 has a non-zero rate
        assert body["realtime_status"] == "ok"


def test_usage_stats_spend_pct_clamps_at_200() -> None:
    """Pydantic Field(le=200) ceiling protects UI from over-cap blow-up."""
    from api.schemas.admin_api_keys import UsageStats4Stat

    stat = UsageStats4Stat(
        api_calls_24h=0,
        spend_today_usd=0,
        spend_cap_daily_usd=10.0,
        spend_pct_used=200.0,  # Exactly the ceiling.
        token_throughput_tpm=0,
        rate_limit_hits_24h=0,
    )
    assert stat.spend_pct_used == 200.0

    with pytest.raises(ValueError):  # Pydantic ValidationError is a ValueError subclass
        UsageStats4Stat(
            api_calls_24h=0,
            spend_today_usd=0,
            spend_cap_daily_usd=10.0,
            spend_pct_used=201.0,  # Above ceiling.
            token_throughput_tpm=0,
            rate_limit_hits_24h=0,
        )


def test_usage_stats_realtime_status_propagates_fetch_failed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """SDK raises → realtime_status='fetch_failed', endpoint still returns 200."""
    from observability import realtime_cost

    fake_client = object()
    monkeypatch.setattr(
        "api.routes.admin.usage_stats.get_langfuse_client", lambda: fake_client
    )

    def failing_fetcher(_c: object, _w: int) -> list[dict[str, Any]]:
        raise RuntimeError("Langfuse 503")

    monkeypatch.setattr(realtime_cost, "_default_fetcher", failing_fetcher)

    app = _build_app()
    with TestClient(app) as client:
        r = client.get("/admin/usage-stats")
        assert r.status_code == 200
        assert r.json()["realtime_status"] == "fetch_failed"
