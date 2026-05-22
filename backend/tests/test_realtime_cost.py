"""W10 D3 F5.2 — realtime cost attribution scaffold coverage.

Per W10 plan §2 F5.2 acceptance:
  - Aggregate by deployment + sum tokens/calls + apply pricing rate
  - Unknown deployments preserved as zero-USD rows(signal,not silent drop)
  - Fetch graceful when client absent / SDK method missing / fetch raises
  - Test-injectable fetcher to avoid SDK roundtrip in unit tests
  - Total USD rounding stable across runs
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from observability.realtime_cost import (
    PRICING_BASELINE_LABEL,
    FetchOutcome,
    GenerationEvent,
    RealtimeUsageRow,
    _default_fetcher,
    _rate_for,
    aggregate_generations,
    estimate_query_cost,
    fetch_realtime_usage,
    total_realtime_usd,
)

# ---------------------------------------------------------------------------
# Pricing table lookup
# ---------------------------------------------------------------------------


def test_rate_for_exact_match() -> None:
    rate = _rate_for("gpt-5-5")
    assert rate is not None
    assert rate.deployment == "gpt-5-5"
    assert rate.input_per_1k_usd == 0.005
    assert rate.output_per_1k_usd == 0.015


def test_rate_for_prefix_match() -> None:
    """Tenant deployments often append `-prod` / `-eastus2` suffixes — prefix
    match keeps the rate lookup robust without rebuilding the table。"""
    assert _rate_for("gpt-5-5-prod-eastus2") is not None
    assert _rate_for("cohere-rerank-v4-pro-east") is not None


def test_rate_for_case_insensitive() -> None:
    assert _rate_for("GPT-5-5") is not None
    assert _rate_for("Cohere-Rerank-v3.5") is not None


def test_rate_for_dot_form_deployment() -> None:
    """Azure deployment names use dots(`gpt-5.5`)while `_PRICING_TABLE` keys
    use dashes(`gpt-5-5`)— dot/dash normalization must resolve them
    (BUG-007 amendment — un-normalized lookup returned None → chat cost blank)。"""
    assert _rate_for("gpt-5.5") is _rate_for("gpt-5-5")
    assert _rate_for("gpt-5.5") is not None
    assert _rate_for("gpt-5.4-mini") is not None
    assert _rate_for("gpt-5.5-prod-eastus2") is not None  # dot + suffix


def test_rate_for_unknown_returns_none() -> None:
    assert _rate_for("claude-opus-4-7") is None
    assert _rate_for("") is None
    assert _rate_for("   ") is None


# ---------------------------------------------------------------------------
# Per-query cost estimate (BUG-007 — stream_composer done event)
# ---------------------------------------------------------------------------


def test_estimate_query_cost_known_deployment() -> None:
    """gpt-5-5: input $0.005/1k + output $0.015/1k → 1k + 1k = $0.02。"""
    assert estimate_query_cost("gpt-5-5", 1000, 1000) == pytest.approx(0.02)


def test_estimate_query_cost_prefix_tolerant() -> None:
    """Suffixed deployment names resolve via the same prefix-tolerant lookup。"""
    assert estimate_query_cost("gpt-5-5-prod", 2000, 500) == pytest.approx(
        2000 / 1000 * 0.005 + 500 / 1000 * 0.015
    )


def test_estimate_query_cost_dot_form_deployment() -> None:
    """`gpt-5.5`(Azure dot form,the real `AZURE_OPENAI_DEPLOYMENT_LLM_PRIMARY`)
    resolves to the `gpt-5-5` table row — the un-normalized lookup returned None
    so the chat meta row showed no cost(BUG-007 amendment)。"""
    assert estimate_query_cost("gpt-5.5", 1000, 1000) == pytest.approx(0.02)
    assert estimate_query_cost("gpt-5.5", 2000, 500) is not None


def test_estimate_query_cost_unknown_deployment_returns_none() -> None:
    """No pricing row → None(cost unavailable),never a misleading $0。"""
    assert estimate_query_cost("claude-opus-4-7", 1000, 500) is None
    assert estimate_query_cost("", 100, 50) is None


def test_estimate_query_cost_zero_tokens() -> None:
    assert estimate_query_cost("gpt-5-5", 0, 0) == 0.0


# ---------------------------------------------------------------------------
# Aggregation core
# ---------------------------------------------------------------------------


def test_aggregate_generations_groups_by_deployment_and_sums_tokens() -> None:
    events = [
        GenerationEvent(model="gpt-5-5", input_tokens=1000, output_tokens=500),
        GenerationEvent(model="gpt-5-5", input_tokens=2000, output_tokens=300),
        GenerationEvent(model="gpt-5-4-mini", input_tokens=500, output_tokens=100),
    ]
    rows = aggregate_generations(events)

    by_dep = {r.deployment: r for r in rows}
    assert by_dep["gpt-5-5"].call_count == 2
    assert by_dep["gpt-5-5"].input_tokens == 3000
    assert by_dep["gpt-5-5"].output_tokens == 800
    assert by_dep["gpt-5-4-mini"].call_count == 1


def test_aggregate_generations_computes_usd_per_token_rate() -> None:
    """gpt-5-5 input $0.005/1k + output $0.015/1k → 1k input + 1k output = $0.02。"""
    events = [GenerationEvent(model="gpt-5-5", input_tokens=1000, output_tokens=1000)]
    rows = aggregate_generations(events)
    assert len(rows) == 1
    assert rows[0].estimated_usd == pytest.approx(0.02, abs=1e-6)


def test_aggregate_generations_per_call_rate_for_cohere() -> None:
    """Cohere has per_call_usd($0.001/call)but no per-token rates。"""
    events = [
        GenerationEvent(model="cohere-rerank-v3.5", input_tokens=0, output_tokens=0),
        GenerationEvent(model="cohere-rerank-v3.5", input_tokens=0, output_tokens=0),
    ]
    rows = aggregate_generations(events)
    cohere = next(r for r in rows if r.deployment == "cohere-rerank-v3.5")
    assert cohere.call_count == 2
    assert cohere.estimated_usd == pytest.approx(0.002, abs=1e-6)


def test_aggregate_generations_unknown_deployment_zero_usd() -> None:
    """Unknown deployments preserved as zero-USD rows(signal,not drop)。"""
    events = [GenerationEvent(model="claude-opus-4-7", input_tokens=1000, output_tokens=500)]
    rows = aggregate_generations(events)
    assert len(rows) == 1
    assert rows[0].deployment == "claude-opus-4-7"
    assert rows[0].component == "(no pricing entry)"
    assert rows[0].estimated_usd == 0.0
    assert "missing rate" in rows[0].rate_note


def test_aggregate_generations_known_and_unknown_coexist() -> None:
    events = [
        GenerationEvent(model="gpt-5-5", input_tokens=100, output_tokens=50),
        GenerationEvent(model="claude-opus-4-7", input_tokens=100, output_tokens=50),
    ]
    rows = aggregate_generations(events)
    deployments = {r.deployment for r in rows}
    assert deployments == {"gpt-5-5", "claude-opus-4-7"}


def test_aggregate_generations_known_rows_appear_first() -> None:
    """Pricing-table order preserved for known deployments;unknown bucket last。"""
    events = [
        GenerationEvent(model="claude-opus-4-7", input_tokens=10, output_tokens=10),
        GenerationEvent(model="gpt-5-5", input_tokens=10, output_tokens=10),
    ]
    rows = aggregate_generations(events)
    # First row should be known (gpt-5-5 in pricing table); unknown comes last
    assert rows[0].deployment == "gpt-5-5"
    assert rows[-1].deployment == "claude-opus-4-7"


def test_aggregate_generations_empty_list() -> None:
    assert aggregate_generations([]) == []


def test_aggregate_generations_handles_zero_tokens() -> None:
    events = [GenerationEvent(model="gpt-5-5", input_tokens=0, output_tokens=0)]
    rows = aggregate_generations(events)
    assert rows[0].estimated_usd == 0.0
    assert rows[0].call_count == 1


def test_total_realtime_usd_sums_estimated_usd() -> None:
    rows = [
        RealtimeUsageRow(
            deployment="gpt-5-5",
            component="C05",
            call_count=1,
            input_tokens=1000,
            output_tokens=1000,
            estimated_usd=0.02,
            rate_note="x",
        ),
        RealtimeUsageRow(
            deployment="cohere-rerank-v3.5",
            component="C04",
            call_count=2,
            input_tokens=0,
            output_tokens=0,
            estimated_usd=0.002,
            rate_note="y",
        ),
    ]
    assert total_realtime_usd(rows) == pytest.approx(0.022, abs=1e-6)


def test_total_realtime_usd_empty_returns_zero() -> None:
    assert total_realtime_usd([]) == 0.0


# ---------------------------------------------------------------------------
# Fetch wrapper — graceful degradation paths
# ---------------------------------------------------------------------------


def test_fetch_realtime_usage_no_client_returns_no_client_status() -> None:
    outcome = fetch_realtime_usage(None)
    assert outcome.status == "no_client"
    assert outcome.rows == []
    assert outcome.window_hours == 24
    assert outcome.pricing_baseline == PRICING_BASELINE_LABEL


def test_fetch_realtime_usage_sdk_method_missing() -> None:
    """Older Langfuse SDK lacks `fetch_observations` — wrapper detects + degrades。"""
    client = MagicMock(spec=["score"])  # no fetch_observations attribute
    outcome = fetch_realtime_usage(client)
    assert outcome.status == "sdk_method_missing"
    assert outcome.rows == []


def test_fetch_realtime_usage_fetch_failed_caught(caplog: pytest.LogCaptureFixture) -> None:
    """`fetch_observations` raises → wrapper logs + returns fetch_failed status。"""
    def _raising_fetcher(client: object, window_hours: int) -> list:  # noqa: ARG001
        raise RuntimeError("network down")

    outcome = fetch_realtime_usage(MagicMock(), fetcher=_raising_fetcher)
    assert outcome.status == "fetch_failed"
    assert outcome.rows == []


def test_fetch_realtime_usage_ok_path_aggregates_rows() -> None:
    def _stub_fetcher(client: object, window_hours: int) -> list:  # noqa: ARG001
        return [
            {"model": "gpt-5-5", "input_tokens": 2000, "output_tokens": 500},
            {"model": "gpt-5-5", "input_tokens": 1000, "output_tokens": 250},
            {"model": "cohere-rerank-v3.5", "input_tokens": 0, "output_tokens": 0},
        ]

    outcome = fetch_realtime_usage(MagicMock(), fetcher=_stub_fetcher, window_hours=12)
    assert outcome.status == "ok"
    assert outcome.window_hours == 12
    assert len(outcome.rows) == 2
    deployments = {r.deployment for r in outcome.rows}
    assert deployments == {"gpt-5-5", "cohere-rerank-v3.5"}
    gpt = next(r for r in outcome.rows if r.deployment == "gpt-5-5")
    assert gpt.call_count == 2
    assert gpt.input_tokens == 3000
    assert gpt.output_tokens == 750


def test_fetch_realtime_usage_ok_with_zero_events_returns_empty_rows() -> None:
    def _empty_fetcher(client: object, window_hours: int) -> list:  # noqa: ARG001
        return []

    outcome = fetch_realtime_usage(MagicMock(), fetcher=_empty_fetcher)
    assert outcome.status == "ok"
    assert outcome.rows == []


def test_fetch_realtime_usage_window_hours_propagates_to_outcome() -> None:
    def _ok(client: object, window_hours: int) -> list:  # noqa: ARG001
        return []

    outcome = fetch_realtime_usage(MagicMock(), fetcher=_ok, window_hours=72)
    assert outcome.window_hours == 72


# ---------------------------------------------------------------------------
# Default fetcher — duck-typed Langfuse SDK shape
# ---------------------------------------------------------------------------


def test_default_fetcher_raises_when_method_absent() -> None:
    client = MagicMock(spec=["score"])
    with pytest.raises(AttributeError):
        _default_fetcher(client, window_hours=24)


def test_default_fetcher_handles_dict_data_shape() -> None:
    """Langfuse 2.x returns `{"data": [...]}` envelope → unwrap。"""
    client = MagicMock()
    client.fetch_observations.return_value = {
        "data": [
            {"model": "gpt-5-5", "usage": {"input": 100, "output": 50}},
        ]
    }
    out = _default_fetcher(client, window_hours=24)
    assert out == [
        {"model": "gpt-5-5", "input_tokens": 100, "output_tokens": 50},
    ]


def test_default_fetcher_handles_list_shape() -> None:
    """Older / alternate SDK shape returns bare list — also accepted。"""
    client = MagicMock()
    client.fetch_observations.return_value = [
        {"model": "gpt-5-4-mini", "usage": {"input": 50, "output": 25}},
    ]
    out = _default_fetcher(client, window_hours=24)
    assert out == [
        {"model": "gpt-5-4-mini", "input_tokens": 50, "output_tokens": 25},
    ]


def test_default_fetcher_handles_input_tokens_key_variant() -> None:
    """Some SDK shapes use `input_tokens`/`output_tokens` directly。"""
    client = MagicMock()
    client.fetch_observations.return_value = [
        {"model": "gpt-5-5", "usage": {"input_tokens": 200, "output_tokens": 100}},
    ]
    out = _default_fetcher(client, window_hours=24)
    assert out[0]["input_tokens"] == 200
    assert out[0]["output_tokens"] == 100


def test_default_fetcher_handles_object_attribute_shape() -> None:
    """SDK may return Observation objects with `.model` + `.usage` attributes。"""
    item = MagicMock()
    item.model = "gpt-5-5"
    item.usage = {"input": 300, "output": 150}
    client = MagicMock()
    client.fetch_observations.return_value = [item]
    out = _default_fetcher(client, window_hours=24)
    assert out[0]["model"] == "gpt-5-5"
    assert out[0]["input_tokens"] == 300


def test_default_fetcher_handles_missing_usage_field() -> None:
    """No `usage` field → tokens default to 0 instead of crashing。"""
    client = MagicMock()
    client.fetch_observations.return_value = [{"model": "gpt-5-5"}]
    out = _default_fetcher(client, window_hours=24)
    assert out[0]["input_tokens"] == 0
    assert out[0]["output_tokens"] == 0


def test_default_fetcher_handles_missing_model_field() -> None:
    client = MagicMock()
    client.fetch_observations.return_value = [{"usage": {"input": 10, "output": 5}}]
    out = _default_fetcher(client, window_hours=24)
    assert out[0]["model"] == "(unknown)"


# ---------------------------------------------------------------------------
# Smoke contracts
# ---------------------------------------------------------------------------


def test_fetch_outcome_field_set_stable() -> None:
    fields = {"rows", "status", "window_hours", "pricing_baseline"}
    assert fields == set(FetchOutcome.__dataclass_fields__.keys())


def test_realtime_usage_row_field_set_stable() -> None:
    fields = {
        "deployment",
        "component",
        "call_count",
        "input_tokens",
        "output_tokens",
        "estimated_usd",
        "rate_note",
    }
    assert fields == set(RealtimeUsageRow.__dataclass_fields__.keys())


def test_pricing_baseline_label_descriptive() -> None:
    """Label must communicate that rates are placeholder + tied to a date。"""
    assert "placeholder" in PRICING_BASELINE_LABEL
    assert "2026-Q2" in PRICING_BASELINE_LABEL
