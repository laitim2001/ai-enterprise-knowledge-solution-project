"""C07 Observability — Alert rule definitions (W8 D5 F5.4).

Per architecture.md §7.4 Day-2 Readiness alerting requirements:
  - p95 latency > 30s
  - API error rate > 5%
  - Cost spike (daily aggregate > 1.5x rolling 7-day avg)
  - CRAG trigger rate > 50% (signals retrieval insufficient)

This module ships the rule *spec* — the canonical source of truth that the
admin UI surfaces and that future Azure Monitor / Langfuse alert wiring
consumes. Actual paging integration (Slack / PagerDuty / Teams) is deferred
to W9+ once on-call rotation is staffed (per beta-plan-v1.md §3 W9).

Karpathy §1.2 simplicity-first: rules are declarative dataclasses. No
runtime evaluation engine here — the thresholds are evaluated externally
by Azure Monitor Log Analytics queries / Langfuse alert rules wired off
the same `audit_log` + Langfuse trace stream.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AlertRule:
    name: str
    condition: str
    threshold: str
    severity: str  # "p1" critical / "p2" warning / "p3" info
    spec_ref: str  # architecture.md / RISK_REGISTER section that mandates this rule


_BETA_ALERT_RULES: tuple[AlertRule, ...] = (
    AlertRule(
        name="api_latency_p95",
        condition="POST /query duration_ms p95 over a 5-minute window",
        threshold="> 30000 ms",
        severity="p2",
        spec_ref="architecture.md §7.4 + §7.1 G1 (R@5 < 30s answer time SLO)",
    ),
    AlertRule(
        name="api_error_rate",
        condition="audit_log status_code >= 500 ratio over a 5-minute window",
        threshold="> 5%",
        severity="p1",
        spec_ref="architecture.md §7.4 + RISK_REGISTER R5 (Azure quota exhaust)",
    ),
    AlertRule(
        name="cost_spike",
        condition="cost-aggregator daily total vs rolling 7-day average",
        threshold="> 1.5x rolling avg",
        severity="p2",
        spec_ref="architecture.md §7.4 (cost dashboard alert) + §9 (Beta budget)",
    ),
    AlertRule(
        name="crag_trigger_rate",
        condition="CragLoop reformulation rate over a 1-hour window",
        threshold="> 50%",
        severity="p3",
        spec_ref="architecture.md §7.4 (signals retrieval insufficient) + §3.7 CRAG",
    ),
    AlertRule(
        name="rate_limit_saturation",
        condition="rate_limit_exceeded count vs total /query requests",
        threshold="> 10% over 10 minutes",
        severity="p3",
        spec_ref="architecture.md §8.1 R5 (rate limit 50 req/min/user) + W7 D2 F2",
    ),
    AlertRule(
        name="langfuse_export_lag",
        condition="time since last successful Langfuse trace flush",
        threshold="> 10 minutes",
        severity="p2",
        spec_ref="architecture.md §3.1 + §7.4 (observability availability)",
    ),
)


def beta_alert_rules() -> list[AlertRule]:
    """Return the alert ruleset planned for Beta phase (W8-W12).

    Stable order matches the priority sequence used by the admin UI panel.
    Future revision = ADR + plan changelog (per CLAUDE.md §5.1 H1 boundary —
    alerting policy 屬 Day-2 Readiness implementation, non-architectural).
    """
    return list(_BETA_ALERT_RULES)


def routing_summary() -> str:
    """One-line description of where alerts fire to.

    W8 baseline: Azure Monitor + Langfuse alerts (definition only — paging
    integration W9+). On-call rotation staff trigger documented in
    `infrastructure/observability/README.md`.
    """
    return "Azure Monitor (latency/error/cost) + Langfuse alerts (CRAG/feedback) — paging W9+ pending on-call rotation"
