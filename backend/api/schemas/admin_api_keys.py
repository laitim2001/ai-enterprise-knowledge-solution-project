"""Admin API keys + usage stats schemas (W24-wave-c1 F4 per ADR-0026 Option B).

Surfaces the `/settings` API Keys & Quotas tab (per
`references/design-mockups/ekp-page-settings-tabs.jsx:744-823 SettingsApiKeys`):

- 4-stat strip — API calls 24h, Spend today, Token throughput TPM, Rate limit hits 24h
- Outgoing API quotas — per-deployment TPM/RPM utilization + cap + cost alert %
- Incoming API keys — Tier 2 disabled affordance (per ADR-0026 §Consequences)

Quota cap edit is intentionally deferred Wave B+ (Azure portal is authoritative
for deployment-level TPM/RPM caps; Wave C1 ships read-only). The PATCH-able
knob is `alert_threshold_pct` consumed by `observability/alerts.py` cost-spike
rule (mockup line 760 "alerts fire at 80% sustained").
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

# ---------- GET /admin/usage-stats ------------------------------------------


class UsageStats4Stat(BaseModel):
    """The 4-stat strip at the top of the API Keys & Quotas tab (mockup line 748-753)."""

    api_calls_24h: int = Field(..., ge=0, description="Generation events in last 24h.")
    api_calls_delta_pct: float | None = Field(
        default=None,
        description="% change vs prior 24h. None when prior window has no data.",
    )
    spend_today_usd: float = Field(..., ge=0, description="Realtime USD attributed via Langfuse fetch.")
    spend_cap_daily_usd: float = Field(
        ..., ge=0, description="Daily spend cap; used to derive spend_pct_used."
    )
    spend_pct_used: float = Field(
        ..., ge=0, le=200, description="(spend_today_usd / spend_cap_daily_usd) * 100; >100 = over-cap."
    )
    token_throughput_tpm: int = Field(
        ..., ge=0, description="Rolling tokens-per-minute (input + output) over last 60min."
    )
    token_throughput_p95_in_cap: bool = Field(
        default=True, description="True when current throughput within cap (mockup line 751)."
    )
    rate_limit_hits_24h: int = Field(
        ..., ge=0, description="429 responses returned by RateLimitMiddleware in last 24h."
    )
    realtime_status: Literal["ok", "no_client", "sdk_method_missing", "fetch_failed"] = "ok"


# ---------- GET /admin/api-keys/outgoing -------------------------------------


class OutgoingQuotaRow(BaseModel):
    """One per-deployment quota row (mockup line 765-768 hard-coded 4-row pattern)."""

    provider_id: str = Field(..., description="F2 provider key, e.g. 'azure_openai'.")
    deployment_id: str = Field(
        ..., description="F2 deployment key, e.g. 'llm_primary'. Falls back to provider_id for non-deployment providers."
    )
    display_name: str = Field(..., description="Composed UI label, e.g. 'Azure OpenAI · gpt-5.5'.")
    used_tpm: int = Field(..., ge=0, description="Realtime TPM consumed (from realtime_cost aggregation).")
    cap_tpm: int | None = Field(default=None, description="TPM cap from F2 ProviderDeployment. None when unbounded.")
    used_rpm: int = Field(..., ge=0, description="Realtime RPM consumed.")
    cap_rpm: int | None = Field(default=None, description="RPM cap from F2 ProviderDeployment.")
    alert_threshold_pct: int = Field(
        default=80, ge=50, le=95, description="Cost-spike alert fires when used% >= this. PATCH-able."
    )
    quota_unit: Literal["tokens", "emails"] = Field(
        default="tokens", description="ACS Email shows 'EMAILS / min' not TPM (mockup line 779)."
    )
    status: Literal["within_limits", "warning", "over_limit"] = "within_limits"


class OutgoingQuotaList(BaseModel):
    """`GET /admin/api-keys/outgoing` response — list of per-deployment rows."""

    rows: list[OutgoingQuotaRow] = Field(default_factory=list)
    realtime_status: Literal["ok", "no_client", "sdk_method_missing", "fetch_failed"] = "ok"


class AlertThresholdPatch(BaseModel):
    """`PATCH /admin/api-keys/outgoing/{provider_id}/{deployment_id}/alert-threshold` payload."""

    alert_threshold_pct: int = Field(
        ..., ge=50, le=95, description="Cost-spike alert threshold percentage."
    )


# ---------- GET /admin/api-keys/incoming -------------------------------------


class IncomingKeysDisabled(BaseModel):
    """`GET /admin/api-keys/incoming` — always returns Tier 2 disabled affordance.

    Per ADR-0026 §Consequences + mockup line 792-818: Tier 1 access is via
    web UI only (MSAL SSO). Wave D Tier 2 promotes — until then this endpoint
    documents the boundary for any client that probes.
    """

    enabled: Literal[False] = False
    reason: str = Field(
        default="Tier 2 — Tier 1 access via web UI only (MSAL SSO).",
        description="Surfaced in the UI banner (mockup line 815-818).",
    )
    tier2_trigger: str = Field(
        default="post-W12 Tier 2 governance (Q12 owner = Chris)",
        description="When this surface unlocks.",
    )
