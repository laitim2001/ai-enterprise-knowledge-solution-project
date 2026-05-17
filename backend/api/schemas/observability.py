"""Observability dashboard schemas (W8 D5 F5.2 + F5.4 + W10 D3 F5.2 realtime).

W21 F2.1 — add `TraceSummary` + `TraceListResponse` for `GET /traces` list view
per ADR-0030 absorbed scope (architecture.md v6 §5.7 Traces). Schema lives in
this existing module per Karpathy §1.2 (group by theme = Observability) — not
a new file.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel


class CostRow(BaseModel):
    service: str
    component: str
    projected_daily_usd: float
    projected_monthly_usd: float
    source: str


class RealtimeUsageRow(BaseModel):
    """W10 D3 F5.2 — per-deployment realtime usage + USD attribution.

    Populated from Langfuse generations API when client wired;empty list
    when client absent / fetch fails(see `realtime_status` field on
    `CostSummary` for which path fired)。
    """

    deployment: str
    component: str
    call_count: int
    input_tokens: int
    output_tokens: int
    estimated_usd: float
    rate_note: str


class CostSummary(BaseModel):
    rows: list[CostRow]
    total_projected_daily_usd: float
    total_projected_monthly_usd: float
    langfuse_status: str  # "wired" | "not_configured"
    # W10 D3 F5.2 — realtime fields(empty list + descriptive status when
    # Langfuse not wired or fetch fails;dashboard always renders gracefully)
    realtime_usage: list[RealtimeUsageRow] = []
    realtime_total_usd: float = 0.0
    realtime_status: str = "no_client"  # "ok" | "no_client" | "sdk_method_missing" | "fetch_failed"
    realtime_window_hours: int = 24
    pricing_baseline: str = "placeholder_publicly_quoted_rates_2026-Q2"
    note: str


class AlertRule(BaseModel):
    name: str
    condition: str
    threshold: str
    severity: str  # "p1" | "p2" | "p3"
    spec_ref: str


class AlertsConfig(BaseModel):
    rules: list[AlertRule]
    routing: str
    spec_ref: str


class TraceStage(BaseModel):
    """One stage of a Langfuse trace (W16 F5.5 CO_W15_F2 Decision D.2).

    Maps to Langfuse observation (SPAN / GENERATION / EVENT). Stage name
    aligns with V6 9-stage Debug View per ADR-0020 (retrieval / rerank /
    context_expansion / synthesis / crag / etc.).
    """

    name: str  # e.g. "retrieval.retrieve", "api.query.synthesizer", "crag.l2.grade"
    type: str  # "SPAN" | "GENERATION" | "EVENT"
    latency_ms: int
    model: str | None = None  # populated for GENERATION observations
    input_tokens: int = 0
    output_tokens: int = 0
    status: str = "ok"  # "ok" | "error" | "cancelled"
    # ADR-0020 Session 2 — stage-specific metadata surfaced from the Langfuse
    # observation's `metadata` dict (minus the always-present `duration_ms`,
    # already mapped to `latency_ms`). Carries e.g. Context Expander
    # `expanded_count` / `boundary_skip_count` / `fetch_latency_ms` for V6
    # Debug View per-stage display. None when the observation had no extra
    # metadata.
    details: dict[str, Any] | None = None


class TraceDetail(BaseModel):
    """W16 F5.5 trace detail response (Langfuse correlation per D.2).

    Returned by GET /debug/trace/{trace_id}. Tier 1 baseline surfaces stage
    breakdown for V6 Debug View consumer (ADR-0020 frontend Session 2).
    Graceful degrade when Langfuse client unavailable: returns trace_url
    pattern only with stages=[] + status="langfuse_not_configured".
    """

    trace_id: str
    trace_url: str  # {langfuse_host}/trace/{trace_id}
    status: str  # "ok" | "not_found" | "langfuse_not_configured" | "fetch_failed"
    total_latency_ms: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    stages: list[TraceStage] = []
    note: str = ""


# ---------------------------------------------------------------------------
# W21 F2.1 — Trace list view (`GET /traces`) per ADR-0030 absorbed
# ---------------------------------------------------------------------------
# architecture.md v6 §5.7 — Traces index list view. Status enum scope is
# trace-level (rolled up from per-observation level field) so a single trace
# row can carry the 3 high-level filter buckets the frontend renders.
# `crag_triggered` is a Tier 1 product-signal status (not an SDK status); it
# co-exists with `ok`/`error` per-row because a CRAG-triggered trace that
# also errored should still surface as `error` (priority: error > crag > ok).


class TraceSummary(BaseModel):
    """One row in the `/traces` index list (per ADR-0030 absorbed scope).

    Maps to one Langfuse trace; fields chosen to be cheap to extract from a
    Langfuse `fetch_traces` summary (no per-trace deep fetch) — `stage_count`
    comes from the observations-id list length, `total_tokens`/`cost_usd`
    come from server-computed aggregates when present, `crag_iterations`
    from upstream-stamped trace metadata (`metadata.crag_iterations`).

    Defaults are conservative (0 / None / "") so the dashboard can render
    rows even when Langfuse server omits derived fields (older self-hosted
    v2 deployments). Frontend distinguishes "missing data" from "zero" via
    the `status` field on the wrapping `TraceListResponse`.
    """

    trace_id: str
    timestamp: str  # ISO 8601
    duration_ms: int = 0
    status: Literal["ok", "error", "crag_triggered"] = "ok"
    kb_id: str | None = None
    query_preview: str = ""  # first 100 chars of input.query (or trace.name)
    total_tokens: int = 0
    cost_usd: float = 0.0
    crag_iterations: int | None = None  # None = not a CRAG trace
    stage_count: int = 0


class TraceListResponse(BaseModel):
    """`GET /traces` paginated response.

    `total` reflects the count AFTER `status_filter`/`since`/`kb_id` were
    applied, BEFORE `offset`/`limit` paging — so the frontend can render
    "Showing N of M" without an extra count fetch. `status` field carries
    the Langfuse fetch outcome (mirrors `CostSummary.realtime_status` /
    `TraceDetail.status` graceful-degrade pattern); the endpoint always
    returns 200, observability fetch error never blocks list render.
    """

    items: list[TraceSummary] = []
    total: int = 0
    limit: int = 50
    offset: int = 0
    status: str = "ok"  # "ok" | "no_client" | "sdk_method_missing" | "fetch_failed"
    note: str = ""
