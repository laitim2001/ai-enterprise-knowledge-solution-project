"""C07 Observability — real-time cost attribution scaffold(W10 D3 F5.2).

Per W10 plan §2 F5.2 + architecture.md §7.4 Day-2 Readiness + §9 cost rows
+ W8 D5 baseline `cost_estimator.py`(static projection)。

**Pipeline**:
    Langfuse generations API(populated by `observe_llm_async` +
    `observe_streaming` events from W9 D2-D3 + W10 D1 progressive scope)
        → fetch within window(default 24h)
        → group by deployment + sum tokens / call counts
        → multiply by per-1k-token / per-call rate table
        → attach to `/observability/cost-summary` response as `realtime_usage`

**Karpathy §1.2 simplicity-first**:
  - **No live LLM API roundtrip required for tests** — fetch is a duck-typed
    accessor swappable via fixture(`fetch_realtime_usage(client_or_fetcher)`)
  - **No DB**:aggregation in-memory each request;cache-as-needed in W11+
    when real cohort traffic exposes per-request hot path latency
  - **Pricing table = placeholder**:per-1k-token / per-call rates documented
    as「pricing_baseline=placeholder_publicly_quoted_rates_2026-Q2」;real
    Q4 deployment rates land before Beta cohort spend gates per W10 plan
    §2 F5.4 stakeholder go/no-go review
  - **Graceful degradation**:absent client → empty list + status="no_client";
    SDK method missing → status="sdk_method_missing";fetch raises →
    status="fetch_failed"。Endpoint always returns 200,never blocks dashboard
    on observability fetch error(per H5 + H6 read-side baseline)
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import structlog

_logger = structlog.get_logger("ekp.realtime_cost")


# ---------------------------------------------------------------------------
# Pricing baseline — placeholder pending Q4 deployment rate confirmation
# ---------------------------------------------------------------------------
#
# Rates expressed as USD per 1000 tokens(Azure OpenAI)or per 1000 calls
# (Cohere)。Source = publicly quoted Azure OpenAI rates 2026-Q2 + Cohere
# Marketplace v3.5 catalog;**SUBJECT TO CHANGE** when Chris confirms Beta
# tenant deployment-specific rates W10 D4-D5 per F5.4 prep deck。
#
# Architecture.md §9 Beta column is the ANCHOR;these per-token rates are
# back-derived from monthly aggregates 加 Beta usage assumptions(50 user ×
# 5 q/day × ~2k input + ~500 output GPT-5.5 per query)。Real cohort traffic
# W11+ will calibrate(per F5.4 review cycle)。

@dataclass(frozen=True)
class _DeploymentRate:
    """Per-1k-token billing rate for one deployment(USD)。"""

    deployment: str
    component: str
    input_per_1k_usd: float | None  # None for non-token services(e.g. Cohere)
    output_per_1k_usd: float | None
    per_call_usd: float | None  # Cohere per-1k-call → here per-1-call expressed as flat
    note: str


_PRICING_TABLE: tuple[_DeploymentRate, ...] = (
    _DeploymentRate(
        deployment="gpt-5-5",
        component="C05 Generation Pipeline (synthesis)",
        input_per_1k_usd=0.005,
        output_per_1k_usd=0.015,
        per_call_usd=None,
        note="GPT-5.5 synthesis — Q4 confirm before Beta cohort spend gate",
    ),
    _DeploymentRate(
        deployment="gpt-5-4-mini",
        component="C05 Generation Pipeline (CRAG L2 grader)",
        input_per_1k_usd=0.00015,
        output_per_1k_usd=0.0006,
        per_call_usd=None,
        note="GPT-5.4-mini judge — Q4 confirm",
    ),
    _DeploymentRate(
        deployment="text-embedding-3-large",
        component="C01 Ingestion + C04 Retrieval",
        input_per_1k_usd=0.00013,
        output_per_1k_usd=0.0,  # embeddings have no output tokens
        per_call_usd=None,
        note="text-embedding-3-large 1024d MRL truncate",
    ),
    _DeploymentRate(
        deployment="cohere-rerank-v3.5",
        component="C04 Retrieval Engine",
        input_per_1k_usd=None,
        output_per_1k_usd=None,
        per_call_usd=0.001,  # ~$1.00 per 1k calls
        note="Cohere Rerank v3.5 Marketplace per Q5 Path A",
    ),
    _DeploymentRate(
        deployment="cohere-rerank-v4-pro",
        component="C04 Retrieval Engine",
        input_per_1k_usd=None,
        output_per_1k_usd=None,
        per_call_usd=0.00105,  # +5% bump per ADR-0012 reaffirm
        note="Cohere Rerank v4.0-pro production lock per Q21 + ADR-0012",
    ),
)

PRICING_BASELINE_LABEL = "placeholder_publicly_quoted_rates_2026-Q2"


def _rate_for(deployment: str) -> _DeploymentRate | None:
    """Lookup rate row by deployment label;case-insensitive,prefix-tolerant。

    Langfuse generation events emit `model` from `Synthesizer.deployment`
    field which can vary between deployments(`gpt-5-5` / `gpt-5-5-prod` /
    etc.);prefix match keeps the rate lookup robust without rebuilding
    the table per-tenant。
    """
    if not deployment:
        return None
    lowered = deployment.lower().strip()
    for row in _PRICING_TABLE:
        if lowered == row.deployment or lowered.startswith(row.deployment + "-"):
            return row
    return None


# ---------------------------------------------------------------------------
# Aggregation core
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class GenerationEvent:
    """One Langfuse generation event reduced to fields needed for cost。

    Mirrors the `client.generation()` payload emitted by `observe_llm_async`
    + `observe_streaming`(see `observe.py::_emit_generation_safe`)。
    """

    model: str
    input_tokens: int
    output_tokens: int
    timestamp: str | None = None  # ISO 8601;optional for aggregation purposes


@dataclass(slots=True)
class RealtimeUsageRow:
    """One per-deployment usage + USD attribution row。"""

    deployment: str
    component: str
    call_count: int
    input_tokens: int
    output_tokens: int
    estimated_usd: float
    rate_note: str


def aggregate_generations(
    events: list[GenerationEvent],
) -> list[RealtimeUsageRow]:
    """Group events by deployment + compute per-deployment USD。

    Unknown deployments(no row in `_PRICING_TABLE`)are folded into a
    synthetic `unknown` bucket with `estimated_usd=0.0` so the dashboard
    can flag「missing pricing entry」without dropping signal — Karpathy §1.2:
    surface anomalies,don't hide them。

    Output ordering = pricing table order(stable across runs)+ unknown
    bucket last when present。
    """
    by_deployment: dict[str, dict[str, int]] = {}
    for event in events:
        bucket = by_deployment.setdefault(
            event.model or "(unknown)",
            {"call_count": 0, "input_tokens": 0, "output_tokens": 0},
        )
        bucket["call_count"] += 1
        bucket["input_tokens"] += int(event.input_tokens or 0)
        bucket["output_tokens"] += int(event.output_tokens or 0)

    rows: list[RealtimeUsageRow] = []
    seen_known: set[str] = set()
    for rate_row in _PRICING_TABLE:
        # Match any deployment in by_deployment whose canonical lookup hits this rate row
        for deployment, totals in by_deployment.items():
            if _rate_for(deployment) is rate_row and deployment not in seen_known:
                seen_known.add(deployment)
                rows.append(
                    _build_usage_row(
                        deployment=deployment,
                        rate=rate_row,
                        totals=totals,
                    )
                )

    # Unknown / no-rate deployments — preserved for signal; estimated_usd=0
    for deployment, totals in by_deployment.items():
        if deployment in seen_known:
            continue
        rows.append(
            RealtimeUsageRow(
                deployment=deployment,
                component="(no pricing entry)",
                call_count=totals["call_count"],
                input_tokens=totals["input_tokens"],
                output_tokens=totals["output_tokens"],
                estimated_usd=0.0,
                rate_note="missing rate — add to _PRICING_TABLE before Beta cohort gate",
            )
        )

    return rows


def _build_usage_row(
    *,
    deployment: str,
    rate: _DeploymentRate,
    totals: dict[str, int],
) -> RealtimeUsageRow:
    """Compute USD per per-1k-token + per-call rates。"""
    usd = 0.0
    if rate.input_per_1k_usd is not None:
        usd += (totals["input_tokens"] / 1000.0) * rate.input_per_1k_usd
    if rate.output_per_1k_usd is not None:
        usd += (totals["output_tokens"] / 1000.0) * rate.output_per_1k_usd
    if rate.per_call_usd is not None:
        usd += totals["call_count"] * rate.per_call_usd
    return RealtimeUsageRow(
        deployment=deployment,
        component=rate.component,
        call_count=totals["call_count"],
        input_tokens=totals["input_tokens"],
        output_tokens=totals["output_tokens"],
        estimated_usd=round(usd, 4),
        rate_note=rate.note,
    )


# ---------------------------------------------------------------------------
# Fetcher abstraction — duck-typed Langfuse SDK access with graceful fallback
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FetchOutcome:
    """Aggregator + fetch status for the endpoint。"""

    rows: list[RealtimeUsageRow]
    status: str  # "ok" | "no_client" | "sdk_method_missing" | "fetch_failed"
    window_hours: int
    pricing_baseline: str = PRICING_BASELINE_LABEL


# Type alias for the fetch callable — production wires Langfuse SDK,tests
# inject a fake returning a list of dicts。Output should be a list of dicts
# with keys `model`/`input_tokens`/`output_tokens`(matches Langfuse 2.x)
# or any subset thereof。Missing fields default to 0 / "(unknown)"。
GenerationsFetcher = Callable[[object, int], list[dict[str, Any]]]


def _default_fetcher(client: object, window_hours: int) -> list[dict[str, Any]]:
    """Production fetcher — try `client.fetch_observations(type="GENERATION")`。

    Langfuse Python SDK 2.x exposes:
        client.fetch_observations(type="GENERATION", limit=N, from_timestamp=...)
    Returns paginated `data` list of `Observation` objects with `.model` +
    `.usage` fields。SDK version drift handled by duck-typing — any callable
    surface returning `[{model, input_tokens, output_tokens}, ...]`-shaped
    iterables works。

    Raises any underlying SDK exception so caller's try/except in
    `fetch_realtime_usage` can record `status=fetch_failed`。
    """
    fetch_fn = getattr(client, "fetch_observations", None)
    if not callable(fetch_fn):
        raise AttributeError("Langfuse client has no fetch_observations method")
    # Argument shape kept generic — only pass what the SDK reliably accepts。
    raw = fetch_fn(type="GENERATION", limit=1000)
    # SDK returns either `[obj, ...]` or `{"data": [obj, ...]}` shape
    items: list[Any] = raw.get("data", []) if isinstance(raw, dict) else list(raw)
    out: list[dict[str, Any]] = []
    for item in items:
        # `usage` may be `{"input": N, "output": M}` or `{"input_tokens": N, ...}`
        usage = getattr(item, "usage", None)
        if usage is None and isinstance(item, dict):
            usage = item.get("usage")
        usage_dict = usage if isinstance(usage, dict) else {}
        input_tokens = usage_dict.get("input") or usage_dict.get("input_tokens") or 0
        output_tokens = usage_dict.get("output") or usage_dict.get("output_tokens") or 0
        model = getattr(item, "model", None) or (
            item.get("model") if isinstance(item, dict) else None
        )
        out.append({
            "model": model or "(unknown)",
            "input_tokens": int(input_tokens or 0),
            "output_tokens": int(output_tokens or 0),
        })
    return out


def fetch_realtime_usage(
    client: object | None,
    *,
    window_hours: int = 24,
    fetcher: GenerationsFetcher | None = None,
) -> FetchOutcome:
    """Fetch realtime generation events + aggregate per deployment。

    Args:
        client: Langfuse SDK client(or None for local dev / CI no-op)。
        window_hours: Look-back window in hours for the aggregation。Default
            24h matches the projected_daily_usd granularity in
            `cost_estimator.py`。Endpoint allows query-param override
            for ad-hoc 7d / 30d analysis。
        fetcher: Test-injectable fetch function。Production leaves None
            so `_default_fetcher` runs against the supplied client。

    Returns:
        `FetchOutcome` with rows + status + window + pricing_baseline label。
        Never raises — degradation paths return empty rows with descriptive
        status string for the dashboard render layer。

    Status semantics:
        - "no_client":Langfuse not configured(local dev / CI)
        - "sdk_method_missing":client wired but `fetch_observations` absent
        - "fetch_failed":fetch raised(network / auth / quota etc.)
        - "ok":fetch returned;rows may still be empty if window has no events
    """
    if client is None:
        return FetchOutcome(rows=[], status="no_client", window_hours=window_hours)

    runner = fetcher or _default_fetcher
    try:
        raw_events = runner(client, window_hours)
    except AttributeError as exc:
        _logger.info(
            "realtime_cost_sdk_method_missing",
            error=str(exc),
            window_hours=window_hours,
        )
        return FetchOutcome(rows=[], status="sdk_method_missing", window_hours=window_hours)
    except Exception as exc:  # noqa: BLE001 — observability never blocks dashboard
        _logger.warning(
            "realtime_cost_fetch_failed",
            error_type=type(exc).__name__,
            error=str(exc),
            window_hours=window_hours,
        )
        return FetchOutcome(rows=[], status="fetch_failed", window_hours=window_hours)

    events = [
        GenerationEvent(
            model=str(raw.get("model") or "(unknown)"),
            input_tokens=int(raw.get("input_tokens") or 0),
            output_tokens=int(raw.get("output_tokens") or 0),
            timestamp=raw.get("timestamp"),
        )
        for raw in raw_events
    ]
    rows = aggregate_generations(events)
    return FetchOutcome(rows=rows, status="ok", window_hours=window_hours)


def total_realtime_usd(rows: list[RealtimeUsageRow]) -> float:
    """Sum estimated USD across rows;rounded to 4 decimal places。"""
    return round(sum(r.estimated_usd for r in rows), 4)
