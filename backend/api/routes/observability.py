"""Observability dashboard endpoints (W8 D5 F5.2 + F5.4 + W10 D3 F5.2 realtime).

Two read-only admin endpoints:
  - GET /observability/cost-summary — projected daily spend + realtime usage
  - GET /observability/alerts       — declared alert ruleset

Both are protected by the standard auth Depends chain wired in
`api.server` (router-level `dependencies=[Depends(get_current_user)]`),
matching the F4.4 W8 D5 admin-routes auth wire.

W10 D3 F5.2 upgrade — `cost-summary` now returns hybrid response:
  - Static projection rows(W8 D5 baseline preserved per architecture.md §9)
  - Realtime usage rows(W10 D3 NEW — Langfuse generations API plumbed via
    `observability.realtime_cost.fetch_realtime_usage`;empty list with
    descriptive `realtime_status` when client absent / fetch fails)
"""

from __future__ import annotations

from fastapi import APIRouter, Query

from api.schemas.observability import (
    AlertRule as AlertRuleSchema,
)
from api.schemas.observability import (
    AlertsConfig,
    CostRow,
    CostSummary,
    RealtimeUsageRow,
)
from observability.alerts import beta_alert_rules, routing_summary
from observability.cost_estimator import (
    projected_daily_rows,
    total_projected_daily_usd,
    total_projected_monthly_usd,
)
from observability.langfuse_tracer import get_langfuse_client
from observability.realtime_cost import (
    fetch_realtime_usage,
    total_realtime_usd,
)

router = APIRouter()


@router.get("/observability/cost-summary", response_model=CostSummary)
async def get_cost_summary(
    window_hours: int = Query(24, ge=1, le=720, description="Realtime window in hours (1-720)"),
) -> CostSummary:
    """Return projected daily spend + realtime per-deployment USD attribution.

    W8 D5 baseline = static projection from architecture.md §9 cost rows.
    W10 D3 F5.2 upgrade = additionally fetch Langfuse generations API for
    realtime per-deployment USD attribution(closes W9 D3 carry-over「Live
    query collection plumbing」)。

    Static + realtime are reported side-by-side(no double-count — static
    is monthly projection,realtime is rolling N-hour actuals)so the
    admin UI can sanity-check projection vs realised spend per F5.4
    Stakeholder go/no-go review prep deck pattern。

    Realtime fetch is always best-effort:
      - No client wired → `realtime_status="no_client"` + empty rows
      - SDK method missing → `realtime_status="sdk_method_missing"` + empty
      - Fetch raises → `realtime_status="fetch_failed"` + empty
      - Fetch ok → `realtime_status="ok"` + rows(possibly empty if window
        has no events)
    Endpoint always returns 200;observability fetch error never blocks
    dashboard render。
    """
    rows = [CostRow(**row.to_dict()) for row in projected_daily_rows()]
    client = get_langfuse_client()
    langfuse_status = "wired" if client is not None else "not_configured"

    outcome = fetch_realtime_usage(client, window_hours=window_hours)
    realtime_rows = [
        RealtimeUsageRow(
            deployment=r.deployment,
            component=r.component,
            call_count=r.call_count,
            input_tokens=r.input_tokens,
            output_tokens=r.output_tokens,
            estimated_usd=r.estimated_usd,
            rate_note=r.rate_note,
        )
        for r in outcome.rows
    ]

    note = (
        "Static projected figures from architecture.md §9 Beta column. "
        "Realtime usage from Langfuse generations API — pricing baseline = "
        f"{outcome.pricing_baseline} (Q4 deployment rate confirm pending "
        "before Beta cohort spend gate per W10 plan §2 F5.4)."
    )
    return CostSummary(
        rows=rows,
        total_projected_daily_usd=total_projected_daily_usd(),
        total_projected_monthly_usd=total_projected_monthly_usd(),
        langfuse_status=langfuse_status,
        realtime_usage=realtime_rows,
        realtime_total_usd=total_realtime_usd(outcome.rows),
        realtime_status=outcome.status,
        realtime_window_hours=outcome.window_hours,
        pricing_baseline=outcome.pricing_baseline,
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
