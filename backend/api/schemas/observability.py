"""Observability dashboard schemas (W8 D5 F5.2 + F5.4)."""

from __future__ import annotations

from pydantic import BaseModel


class CostRow(BaseModel):
    service: str
    component: str
    projected_daily_usd: float
    projected_monthly_usd: float
    source: str


class CostSummary(BaseModel):
    rows: list[CostRow]
    total_projected_daily_usd: float
    total_projected_monthly_usd: float
    langfuse_status: str  # "wired" | "not_configured"
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
