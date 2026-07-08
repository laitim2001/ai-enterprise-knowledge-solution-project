"""`/admin/api-keys/*` — outgoing quotas + incoming Tier 2 disabled (W24-wave-c1 F4).

3 endpoints per ADR-0026 Option B + mockup `ekp-page-settings-tabs.jsx:744-823
SettingsApiKeys`:

- `GET   /admin/api-keys/outgoing` → list of per-deployment quota + realtime usage rows
- `PATCH /admin/api-keys/outgoing/{provider_id}/{deployment_id}/alert-threshold` → cost-spike alert %
- `GET   /admin/api-keys/incoming` → permanent Tier 2 disabled affordance

**Outgoing quotas semantic** (per pre-active-flip audit):

Cap edit (TPM/RPM) is intentionally **read-only** at Wave C1 — Azure portal
remains authoritative for deployment-level caps. The PATCH-able knob is
`alert_threshold_pct` which feeds the `cost_spike` rule in `alerts.py`.

**Deployment flattening**: F2 stores 4 deployments under `azure_openai` +
non-deployment providers (cohere / acs_email / azure_search / etc.) as
single-row. F4 flattens the matrix into one row per (provider × deployment),
falling back to a single row with `deployment_id == provider_id` for the
non-deployment case (mockup line 767-768 Cohere / ACS pattern).
"""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, HTTPException, Request, status

from api.schemas.admin import ProviderDeployment
from api.schemas.admin_api_keys import (
    AlertThresholdPatch,
    IncomingKeysDisabled,
    OutgoingQuotaList,
    OutgoingQuotaRow,
)
from observability.langfuse_tracer import get_langfuse_client
from observability.realtime_cost import fetch_realtime_usage
from storage.admin_provider_storage import (
    AdminProviderConfigBackend,
    ProviderNotFoundError,
)
from storage.audit_log_storage import AuditLogBackend

QuotaStatus = Literal["within_limits", "warning", "over_limit"]

router = APIRouter(prefix="/admin/api-keys")


def _get_provider_backend(request: Request) -> AdminProviderConfigBackend:
    backend = getattr(request.app.state, "admin_provider_backend", None)
    if backend is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="admin_provider_backend not initialized — check lifespan logs",
        )
    return backend  # type: ignore[no-any-return]


def _get_audit_log(request: Request) -> AuditLogBackend | None:
    """Audit log is optional at Wave C1 — endpoint stays usable when unwired."""
    return getattr(request.app.state, "audit_log_backend", None)


def _flatten_to_quota_rows(
    *,
    provider_id: str,
    display_name: str,
    deployments: list[ProviderDeployment],
    realtime_by_model: dict[str, tuple[int, int]],
) -> list[OutgoingQuotaRow]:
    """Compose per-deployment rows; falls back to single row when deployments empty."""
    out: list[OutgoingQuotaRow] = []
    if deployments:
        for d in deployments:
            input_tokens, call_count = realtime_by_model.get(d.deployment_name, (0, 0))
            # Wave A: derive used_tpm from input_tokens / 60min over the 24h window.
            used_tpm = input_tokens // (24 * 60) if input_tokens > 0 else 0
            used_rpm = call_count // (24 * 60) if call_count > 0 else 0
            out.append(
                OutgoingQuotaRow(
                    provider_id=provider_id,
                    deployment_id=d.deployment_id,
                    display_name=f"{display_name} · {d.deployment_name}",
                    used_tpm=used_tpm,
                    cap_tpm=d.tpm_limit,
                    used_rpm=used_rpm,
                    cap_rpm=d.rpm_limit,
                    alert_threshold_pct=d.alert_threshold_pct,
                    quota_unit="tokens",
                    status=_derive_status(used_tpm, d.tpm_limit, d.alert_threshold_pct),
                )
            )
    else:
        # Non-deployment providers (cohere / acs_email / etc.) — single synthetic row.
        out.append(
            OutgoingQuotaRow(
                provider_id=provider_id,
                deployment_id=provider_id,
                display_name=display_name,
                used_tpm=0,
                cap_tpm=None,
                used_rpm=0,
                cap_rpm=None,
                alert_threshold_pct=80,
                quota_unit="emails" if provider_id == "acs_email" else "tokens",
                status="within_limits",
            )
        )
    return out


def _derive_status(
    used: int, cap: int | None, threshold_pct: int
) -> QuotaStatus:
    if cap is None or cap == 0:
        return "within_limits"
    pct = (used / cap) * 100
    if pct >= 100:
        return "over_limit"
    if pct >= threshold_pct:
        return "warning"
    return "within_limits"


# ---------- Endpoints --------------------------------------------------------


@router.get("/outgoing", response_model=OutgoingQuotaList)
async def get_outgoing_quotas(request: Request) -> OutgoingQuotaList:
    backend = _get_provider_backend(request)
    client = get_langfuse_client()
    outcome = fetch_realtime_usage(client, window_hours=24)
    # Build a lookup keyed by the Langfuse `model` field (matches deployment_name).
    realtime_by_model: dict[str, tuple[int, int]] = {
        r.deployment: (r.input_tokens + r.output_tokens, r.call_count) for r in outcome.rows
    }

    configs = await backend.list_all()
    rows: list[OutgoingQuotaRow] = []
    for cfg in configs:
        # structlog + key_vault are config-only providers (no quota surface).
        if cfg.provider_id in ("structlog", "key_vault"):
            continue
        rows.extend(
            _flatten_to_quota_rows(
                provider_id=cfg.provider_id,
                display_name=cfg.display_name,
                deployments=cfg.deployments,
                realtime_by_model=realtime_by_model,
            )
        )
    return OutgoingQuotaList(rows=rows, realtime_status=outcome.status)  # type: ignore[arg-type]


@router.patch(
    "/outgoing/{provider_id}/{deployment_id}/alert-threshold",
    response_model=OutgoingQuotaRow,
)
async def patch_alert_threshold(
    provider_id: str,
    deployment_id: str,
    patch: AlertThresholdPatch,
    request: Request,
) -> OutgoingQuotaRow:
    backend = _get_provider_backend(request)
    try:
        updated = await backend.update_deployment_alert_threshold(
            provider_id, deployment_id, alert_threshold_pct=patch.alert_threshold_pct
        )
    except ProviderNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e

    # Locate the patched deployment row to compose the response.
    deployment = next(d for d in updated.deployments if d.deployment_id == deployment_id)

    audit = _get_audit_log(request)
    if audit is not None:
        await audit.append(
            actor=None,  # Wave C2: extract from request.state.user when ADR-0027 wires middleware
            action="api_keys_alert_threshold_patch",
            resource=f"admin_provider_configs/{provider_id}/{deployment_id}",
            payload={"alert_threshold_pct": patch.alert_threshold_pct},
        )

    return OutgoingQuotaRow(
        provider_id=provider_id,
        deployment_id=deployment_id,
        display_name=f"{updated.display_name} · {deployment.deployment_name}",
        used_tpm=0,
        cap_tpm=deployment.tpm_limit,
        used_rpm=0,
        cap_rpm=deployment.rpm_limit,
        alert_threshold_pct=deployment.alert_threshold_pct,
        quota_unit="tokens",
        status="within_limits",
    )


@router.get("/incoming", response_model=IncomingKeysDisabled)
async def get_incoming_keys() -> IncomingKeysDisabled:
    """Permanent Tier 2 disabled affordance per ADR-0026 §Consequences."""
    return IncomingKeysDisabled()
