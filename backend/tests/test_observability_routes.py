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

from api.auth import get_current_user
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
    """Reset Langfuse singleton + clear dependency_overrides leaked from
    other test modules (test_api_skeleton.py installs a module-level
    `get_current_user` override that would mask 401 expectations here).
    """
    langfuse_tracer._set_langfuse_client_for_tests(None)
    saved_override = app.dependency_overrides.pop(get_current_user, None)
    yield
    langfuse_tracer._set_langfuse_client_for_tests(None)
    if saved_override is not None:
        app.dependency_overrides[get_current_user] = saved_override


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
