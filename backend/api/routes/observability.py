"""Observability dashboard endpoints (W8 D5 F5.2 + F5.4).

Two read-only admin endpoints:
  - GET /observability/cost-summary — projected daily spend per service
  - GET /observability/alerts       — declared alert ruleset

Both are protected by the standard auth Depends chain wired in
`api.server` (router-level `dependencies=[Depends(get_current_user)]`),
matching the F4.4 W8 D5 admin-routes auth wire.
"""

from __future__ import annotations

from fastapi import APIRouter

from api.schemas.observability import (
    AlertRule as AlertRuleSchema,
)
from api.schemas.observability import (
    AlertsConfig,
    CostRow,
    CostSummary,
)
from observability.alerts import beta_alert_rules, routing_summary
from observability.cost_estimator import (
    projected_daily_rows,
    total_projected_daily_usd,
    total_projected_monthly_usd,
)
from observability.langfuse_tracer import get_langfuse_client

router = APIRouter()


@router.get("/observability/cost-summary", response_model=CostSummary)
async def get_cost_summary() -> CostSummary:
    """Return the projected daily spend dashboard data.

    W8 D5 baseline = static projection from architecture.md §9 cost rows.
    Actual usage attribution lands W9+ when Langfuse generations API is
    queryable + per-stage @observe instrumentation flows.
    """
    rows = [CostRow(**row.to_dict()) for row in projected_daily_rows()]
    langfuse_status = "wired" if get_langfuse_client() is not None else "not_configured"
    note = (
        "Projected figures from architecture.md §9 Beta column. Real-time LLM "
        "token attribution requires Langfuse generations API — W9+ scope "
        "(per beta-plan-v1.md §2 W8.F5)."
    )
    return CostSummary(
        rows=rows,
        total_projected_daily_usd=total_projected_daily_usd(),
        total_projected_monthly_usd=total_projected_monthly_usd(),
        langfuse_status=langfuse_status,
        note=note,
    )


@router.get("/observability/alerts", response_model=AlertsConfig)
async def get_alert_rules() -> AlertsConfig:
    """Return the Beta-phase alert ruleset declared in observability/alerts.py.

    Surface for admin UI rendering + W9+ Azure Monitor / Langfuse alert
    sync (manual SOP — `infrastructure/observability/README.md`).
    """
    rules = [
        AlertRuleSchema(
            name=rule.name,
            condition=rule.condition,
            threshold=rule.threshold,
            severity=rule.severity,
            spec_ref=rule.spec_ref,
        )
        for rule in beta_alert_rules()
    ]
    return AlertsConfig(
        rules=rules,
        routing=routing_summary(),
        spec_ref="architecture.md §7.4 Day-2 Readiness Checklist",
    )
