# Observability — F5.1 + F5.2 + F5.4 SOP(W8 D5)

> Per W08-beta-deploy-sprint2 plan §2 F5 + components/C07-observability.md + architecture.md §7.4 Day-2 Readiness。
> **Owner**:Chris(Langfuse cloud account + Azure Monitor + on-call rotation)+ AI(SDK wire + alert rules authoring)。
> **Status**:SDK + cost dashboard + alert rules **landed W8 D5**;Langfuse cloud cred populate + Azure Monitor alert sync + on-call paging integration **deferred W9+** post-cred + on-call rotation staffed。

## Scope

W8 D5 ships the observability **plumbing**:
- F5.1 Real Langfuse SDK initialised in `backend/observability/langfuse_tracer.py`
- F5.2 Cost projection dashboard endpoint `GET /observability/cost-summary`
- F5.3 User feedback `/feedback` forwards to Langfuse `score()` API
- F5.4 Alert rule spec module `backend/observability/alerts.py` + endpoint `GET /observability/alerts`

W9+ wires the **runtime side**:
- Langfuse cloud account populated with `LANGFUSE_PUBLIC_KEY` + `LANGFUSE_SECRET_KEY` (Key Vault per `infrastructure/keyvault/README.md`)
- Per-stage `@observe` decoration on `query.py` + `synthesizer.py` + `crag.py` so trace events flow
- Azure Monitor alert rules synced from `beta_alert_rules()` ruleset
- On-call paging integration (Slack / PagerDuty / Teams) per beta-plan-v1.md §3 W9

## Langfuse SDK lifecycle(F5.1)

`langfuse_tracer.py` is the single integration point。Service code reads
`get_langfuse_client()` and branches on `is not None`:

```python
from observability.langfuse_tracer import get_langfuse_client

client = get_langfuse_client()
if client is not None:
    client.score(trace_id=tid, name="user_feedback", value=1, comment=...)
```

Lifecycle:
- `init_tracer(settings)` runs in FastAPI `lifespan` startup(`api/server.py`):
  - Configures structlog JSON renderer **unconditionally**(audit middleware needs it)
  - Initialises Langfuse client **only when** both `langfuse_public_key` + `langfuse_secret_key` populated
  - Import / init failure → singleton stays `None`(structured warning logged;never raises)
- `flush_tracer()` runs in FastAPI `lifespan` shutdown finally block — drains queued events before process exit so short-lived tasks(CI / one-shot scripts)don't lose traces

## Cost dashboard(F5.2)

`GET /observability/cost-summary` returns the projected daily spend dashboard:

```json
{
  "rows": [
    {
      "service": "Azure AI Search Standard S1",
      "component": "C03 Indexing Service",
      "projected_daily_usd": 2.5,
      "projected_monthly_usd": 75.0,
      "source": "architecture.md §9 row 1 (S1 multi-KB ready)"
    },
    ...
  ],
  "total_projected_daily_usd": 9.6,
  "total_projected_monthly_usd": 288.0,
  "langfuse_status": "wired",
  "note": "Projected figures from architecture.md §9 Beta column..."
}
```

W8 D5 baseline = static projection from architecture.md §9。**Real-time LLM token attribution requires Langfuse generations API + per-stage `@observe` decoration** — W9+ progressive instrumentation。

## User feedback(F5.3)

`POST /feedback` accepts thumbs_up / thumbs_down + optional comment + trace_id:

- Maps `thumbs_up` → Langfuse score `value=1`
- Maps `thumbs_down` → Langfuse score `value=-1`
- When Langfuse client is `None` → still 202 accepted(audit-logged via structlog)
- When `score()` raises → still 202 accepted(warning logged;never 5xx)

Karpathy §1.2 simplicity-first:**feedback is never silently dropped**。Local dev / CI / cred-pending-deploy 路徑全部保留 feedback 入 audit log,等 Langfuse cloud 接通後 backfill optional。

## Alerts(F5.4)

`GET /observability/alerts` returns the Beta-phase ruleset:

| Rule | Threshold | Severity | Spec ref |
|---|---|---|---|
| api_latency_p95 | > 30000 ms | p2 | architecture.md §7.4 + §7.1 G1 |
| api_error_rate | > 5% | p1 | architecture.md §7.4 + RISK_REGISTER R5 |
| cost_spike | > 1.5x rolling 7-day avg | p2 | architecture.md §7.4 + §9 |
| crag_trigger_rate | > 50% | p3 | architecture.md §7.4 + §3.7 CRAG |
| rate_limit_saturation | > 10% over 10 min | p3 | architecture.md §8.1 R5 |
| langfuse_export_lag | > 10 min | p2 | architecture.md §3.1 + §7.4 |

W8 D5 baseline = rules **declared**(authoritative source for admin UI rendering + W9+ Azure Monitor sync)。**Paging integration(Slack / PagerDuty)deferred W9+** post on-call rotation staffed。

### Wire-up sequence(W9+ Chris)

1. **Azure Monitor metric queries**:translate `api_latency_p95` + `api_error_rate` into Log Analytics KQL queries against ACA App Insights export
2. **Langfuse alerts**:configure `crag_trigger_rate` + `langfuse_export_lag` via Langfuse cloud alert UI
3. **Routing**:wire to Slack channel `#ekp-oncall`(or PagerDuty service if procurement landed)
4. **Runbook**:per `architecture.md §7.4` runbook checklist — document parse failures + API quota exhaustion + index corruption + reranker outage + CRAG loop bug

## Local dev / CI behaviour

When `LANGFUSE_PUBLIC_KEY` + `LANGFUSE_SECRET_KEY` are empty(default `.env.example`):

- `init_tracer` logs `langfuse_sdk_status="not_configured"` and returns
- `get_langfuse_client()` returns `None` everywhere
- `/observability/cost-summary` returns rows with `langfuse_status="not_configured"`
- `/feedback` accepts payloads + emits `forwarded_to_langfuse=false` audit row
- `/observability/alerts` returns the same ruleset(rules are static spec)

This keeps local dev + CI **zero-cred**;Beta+ deploy populates cred via Key Vault Managed Identity per `infrastructure/keyvault/README.md`。

## Cross-component dependencies

| Component | Wired |
|---|---|
| **C07 Observability** | `langfuse_tracer.py` + `cost_estimator.py` + `alerts.py` modules |
| **C08 API Gateway** | `/feedback` + `/observability/cost-summary` + `/observability/alerts` routers behind `Depends(get_current_user)` |
| **C12 DevOps** | Key Vault `langfuse-public-key` + `langfuse-secret-key` secrets(W9+ populate) |

## Tier 2(out-of-scope)

- Custom dashboard UI(Grafana / Datadog) — Tier 2 advanced visualisation
- Trace sampling tuning — Tier 2 cost-of-observability optimisation
- Multi-region Langfuse failover — Tier 2 production geo-redundancy
- Auto-anomaly detection ML — Tier 2 advanced alerting

## Update history

| Date | Change | Reason |
|---|---|---|
| 2026-05-23 | Initial SOP(W8 D5 F5.1-F5.4)| W7 D5 retro § Carry-over C10 Real Langfuse SDK wire + W8 D5 cost dashboard + alert rules cascade |
