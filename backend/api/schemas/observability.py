"""Observability dashboard schemas (W8 D5 F5.2 + F5.4 + W10 D3 F5.2 realtime)."""

from __future__ import annotations

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
