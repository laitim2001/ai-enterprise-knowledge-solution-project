"""W8 D5 F5.2 + F5.4 + F4.4 — observability dashboard + admin auth coverage.

Per W08-beta-deploy-sprint2 plan §2 acceptance:
  - F5.2 /observability/cost-summary returns structured projection rows
  - F5.4 /observability/alerts returns the 6-rule Beta-phase ruleset
  - F4.4 admin routers (documents/chunks/eval/screenshots/debug/observability)
    now refuse unauthenticated requests (401), wired through the same
    `get_current_user` Depends chain as /query + /kb
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from api.server import app
from observability import langfuse_tracer
from observability.alerts import beta_alert_rules
from observability.cost_estimator import (
    projected_daily_rows,
    total_projected_daily_usd,
    total_projected_monthly_usd,
)


@pytest.fixture(autouse=True)
def _isolate_app_state() -> None:
    """Reset Langfuse singleton between tests。

    W9 D5 C11 cleanup:upstream `test_api_skeleton.py` no longer leaks
    `get_current_user` dependency_override at module load(now autouse-fixture
    scoped),so the previous defensive `app.dependency_overrides.pop()`
    workaround here is redundant — only Langfuse singleton reset remains。
    """
    langfuse_tracer._set_langfuse_client_for_tests(None)
    yield
    langfuse_tracer._set_langfuse_client_for_tests(None)


def _bearer() -> dict[str, str]:
    return {"Authorization": "Bearer dev-token"}


# ---------------------------------------------------------------------------
# F5.2 cost-summary
# ---------------------------------------------------------------------------


def test_cost_summary_returns_static_projection_with_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FEATURE_AUTH_MOCK", "true")
    from storage.settings import get_settings

    get_settings.cache_clear()

    client = TestClient(app)
    resp = client.get("/observability/cost-summary", headers=_bearer())

    assert resp.status_code == 200, resp.text
    body = resp.json()

    expected_rows = projected_daily_rows()
    assert len(body["rows"]) == len(expected_rows)
    assert {r["service"] for r in body["rows"]} == {r.service for r in expected_rows}

    assert body["total_projected_daily_usd"] == total_projected_daily_usd()
    assert body["total_projected_monthly_usd"] == total_projected_monthly_usd()
    # No Langfuse client wired in this test
    assert body["langfuse_status"] == "not_configured"
    assert "architecture.md §9" in body["note"]


def test_cost_summary_reports_wired_when_langfuse_present(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("FEATURE_AUTH_MOCK", "true")
    from storage.settings import get_settings

    get_settings.cache_clear()
    langfuse_tracer._set_langfuse_client_for_tests(MagicMock())

    client = TestClient(app)
    resp = client.get("/observability/cost-summary", headers=_bearer())

    assert resp.status_code == 200
    assert resp.json()["langfuse_status"] == "wired"


# ---------------------------------------------------------------------------
# F5.2 W10 D3 — realtime usage hybrid response
# ---------------------------------------------------------------------------


def test_cost_summary_realtime_no_client_when_langfuse_absent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No Langfuse client → realtime fields present but empty + status=no_client。"""
    monkeypatch.setenv("FEATURE_AUTH_MOCK", "true")
    from storage.settings import get_settings

    get_settings.cache_clear()

    client = TestClient(app)
    resp = client.get("/observability/cost-summary", headers=_bearer())

    assert resp.status_code == 200
    body = resp.json()
    assert body["realtime_status"] == "no_client"
    assert body["realtime_usage"] == []
    assert body["realtime_total_usd"] == 0.0
    assert body["realtime_window_hours"] == 24
    assert "placeholder" in body["pricing_baseline"]


def test_cost_summary_realtime_sdk_method_missing_when_old_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Langfuse client lacks fetch_observations → status=sdk_method_missing。"""
    monkeypatch.setenv("FEATURE_AUTH_MOCK", "true")
    from storage.settings import get_settings

    get_settings.cache_clear()
    # MagicMock spec=["score"] — fetch_observations attribute absent
    legacy_client = MagicMock(spec=["score"])
    langfuse_tracer._set_langfuse_client_for_tests(legacy_client)

    client = TestClient(app)
    resp = client.get("/observability/cost-summary", headers=_bearer())

    assert resp.status_code == 200
    body = resp.json()
    assert body["langfuse_status"] == "wired"
    assert body["realtime_status"] == "sdk_method_missing"
    assert body["realtime_usage"] == []


def test_cost_summary_realtime_fetch_failed_returns_200_with_status(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """fetch_observations raises → endpoint still 200,status=fetch_failed。"""
    monkeypatch.setenv("FEATURE_AUTH_MOCK", "true")
    from storage.settings import get_settings

    get_settings.cache_clear()
    flaky_client = MagicMock()
    flaky_client.fetch_observations.side_effect = RuntimeError("network down")
    langfuse_tracer._set_langfuse_client_for_tests(flaky_client)

    client = TestClient(app)
    resp = client.get("/observability/cost-summary", headers=_bearer())

    assert resp.status_code == 200
    body = resp.json()
    assert body["realtime_status"] == "fetch_failed"
    assert body["realtime_usage"] == []


def test_cost_summary_realtime_ok_returns_aggregated_rows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Langfuse client returns generations → endpoint embeds aggregated rows。"""
    monkeypatch.setenv("FEATURE_AUTH_MOCK", "true")
    from storage.settings import get_settings

    get_settings.cache_clear()
    happy_client = MagicMock()
    happy_client.fetch_observations.return_value = [
        {"model": "gpt-5-5", "usage": {"input": 1000, "output": 500}},
        {"model": "gpt-5-5", "usage": {"input": 2000, "output": 250}},
        {"model": "cohere-rerank-v3.5", "usage": {"input": 0, "output": 0}},
    ]
    langfuse_tracer._set_langfuse_client_for_tests(happy_client)

    client = TestClient(app)
    resp = client.get("/observability/cost-summary", headers=_bearer())

    assert resp.status_code == 200
    body = resp.json()
    assert body["realtime_status"] == "ok"
    assert len(body["realtime_usage"]) == 2
    deployments = {r["deployment"] for r in body["realtime_usage"]}
    assert deployments == {"gpt-5-5", "cohere-rerank-v3.5"}
    assert body["realtime_total_usd"] > 0
    # gpt-5-5 row: 3000 input × $0.005/1k + 750 output × $0.015/1k = 0.015 + 0.01125
    gpt = next(r for r in body["realtime_usage"] if r["deployment"] == "gpt-5-5")
    assert gpt["call_count"] == 2
    assert gpt["input_tokens"] == 3000
    assert gpt["output_tokens"] == 750
    assert gpt["estimated_usd"] == pytest.approx(0.02625, abs=1e-4)


def test_cost_summary_realtime_window_hours_query_param_propagates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`?window_hours=72` flows through to fetch + appears in response。"""
    monkeypatch.setenv("FEATURE_AUTH_MOCK", "true")
    from storage.settings import get_settings

    get_settings.cache_clear()
    happy_client = MagicMock()
    happy_client.fetch_observations.return_value = []
    langfuse_tracer._set_langfuse_client_for_tests(happy_client)

    client = TestClient(app)
    resp = client.get(
        "/observability/cost-summary?window_hours=72",
        headers=_bearer(),
    )

    assert resp.status_code == 200
    assert resp.json()["realtime_window_hours"] == 72


def test_cost_summary_realtime_window_hours_clamps_to_valid_range(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Out-of-range `window_hours` → 422 from Pydantic validation。"""
    monkeypatch.setenv("FEATURE_AUTH_MOCK", "true")
    from storage.settings import get_settings

    get_settings.cache_clear()

    client = TestClient(app)
    resp = client.get(
        "/observability/cost-summary?window_hours=0",
        headers=_bearer(),
    )
    assert resp.status_code == 422

    resp = client.get(
        "/observability/cost-summary?window_hours=99999",
        headers=_bearer(),
    )
    assert resp.status_code == 422


def test_cost_summary_static_projection_unchanged_by_realtime_addition(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Static projection rows + totals must not regress when realtime fields added。"""
    monkeypatch.setenv("FEATURE_AUTH_MOCK", "true")
    from storage.settings import get_settings

    get_settings.cache_clear()

    client = TestClient(app)
    resp = client.get("/observability/cost-summary", headers=_bearer())

    body = resp.json()
    expected_rows = projected_daily_rows()
    # Same row count + service set as before W10 D3 upgrade
    assert len(body["rows"]) == len(expected_rows)
    assert {r["service"] for r in body["rows"]} == {r.service for r in expected_rows}
    assert body["total_projected_daily_usd"] == total_projected_daily_usd()
    assert body["total_projected_monthly_usd"] == total_projected_monthly_usd()


# ---------------------------------------------------------------------------
# F5.4 alerts
# ---------------------------------------------------------------------------


def test_alerts_endpoint_returns_beta_ruleset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FEATURE_AUTH_MOCK", "true")
    from storage.settings import get_settings

    get_settings.cache_clear()

    client = TestClient(app)
    resp = client.get("/observability/alerts", headers=_bearer())

    assert resp.status_code == 200
    body = resp.json()

    expected_rules = beta_alert_rules()
    assert len(body["rules"]) == len(expected_rules)
    rule_names = {r["name"] for r in body["rules"]}
    # All 4 architecture.md §7.4 rules + 2 Beta-specific rules present.
    assert {
        "api_latency_p95",
        "api_error_rate",
        "cost_spike",
        "crag_trigger_rate",
        "rate_limit_saturation",
        "langfuse_export_lag",
    }.issubset(rule_names)
    assert "Azure Monitor" in body["routing"]
    assert body["spec_ref"] == "architecture.md §7.4 Day-2 Readiness Checklist"


# ---------------------------------------------------------------------------
# F4.4 admin auth wire — every admin router now 401 without bearer
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "method,path",
    [
        ("GET", "/observability/cost-summary"),
        ("GET", "/observability/alerts"),
        ("GET", "/kb/test-kb/documents"),
        ("GET", "/kb/test-kb/documents/d1/chunks"),
        ("POST", "/eval/run"),
        ("GET", "/screenshots/k/d/img"),
        ("GET", "/debug/trace/abc"),
    ],
)
def test_admin_routes_require_auth(
    method: str,
    path: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """W8 D5 F4.4 — every admin router rejects unauthenticated requests."""
    monkeypatch.setenv("FEATURE_AUTH_MOCK", "true")
    from storage.settings import get_settings

    get_settings.cache_clear()

    client = TestClient(app)
    if method == "POST":
        resp = client.post(path, json={"eval_set_id": "v0"})
    else:
        resp = client.get(path)

    # 401 from auth Depends (rate limit middleware does NOT cover these so the
    # auth Depends fires on bearer-absent — uniform ApiError envelope).
    assert resp.status_code == 401, f"{method} {path} → {resp.status_code} (expected 401)"
    body = resp.json()
    assert "error" in body, f"{method} {path} body missing 'error': {body}"


def test_admin_routes_pass_with_bearer_then_hit_route_logic(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """With a valid mock bearer, the auth Depends passes — routes that are
    still 501 stubs (W2 implementation pending) surface their stub status.
    Confirms F4.4 wires auth WITHOUT regressing existing route behavior.
    """
    monkeypatch.setenv("FEATURE_AUTH_MOCK", "true")
    from storage.settings import get_settings

    get_settings.cache_clear()

    client = TestClient(app)

    # /debug/trace/{id} is still a 501 stub — confirms auth passed THEN route fired.
    resp = client.get("/debug/trace/abc", headers=_bearer())
    assert resp.status_code == 501, resp.text

    # /observability/cost-summary is fully implemented — 200 expected.
    resp = client.get("/observability/cost-summary", headers=_bearer())
    assert resp.status_code == 200
