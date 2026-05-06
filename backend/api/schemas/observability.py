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
