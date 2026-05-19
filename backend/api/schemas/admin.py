"""Admin provider configuration schemas (W24-wave-c1 F2 per ADR-0026 Option B).

9 providers across 5 categories, each surfaceable by the `/settings` Connections
tab (per `references/design-mockups/ekp-page-settings-tabs.jsx:96-355
SettingsConnections`):

  llm           — azure_openai (with 4 deployments: embedding / llm_primary /
                  llm_judge / llm_eval_judge)
  retrieval     — cohere, azure_search
  storage       — azure_blob (Azurite for local), postgres
  observability — langfuse
  identity      — acs_email, key_vault

`container_apps` is intentionally omitted from the writable Connections list
(managed-identity only — no rotatable secret;visibility surfaced under Identity
& Auth tab F3 instead). `structlog` is config-only (no provider).

Schemas mirror the W20 F2.1 `/health` ComponentHealth shape for the
TestConnectionResult so the Connections tab can reuse the same dot taxonomy
(`ok` / `degraded` / `error` / `not_tested`).
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

ProviderCategory = Literal["llm", "retrieval", "storage", "observability", "identity"]
TestStatus = Literal["ok", "degraded", "error", "not_tested"]


class ProviderDeployment(BaseModel):
    """A specific deployment under a provider (e.g., GPT-5.5 under Azure OpenAI).

    Tier 1 scope = read-only display. Wave B+ may add editable TPM/RPM limits.
    """

    deployment_id: str = Field(..., description="Stable ID, e.g. 'embedding'.")
    deployment_name: str = Field(..., description="Display name, e.g. 'text-embedding-3-large'.")
    model_family: str = Field(..., description="E.g. 'embedding' / 'chat' / 'rerank'.")
    tpm_limit: int | None = None
    rpm_limit: int | None = None


class ProviderConfig(BaseModel):
    """Full per-provider config. Secret values are NEVER returned — only `secret_kv_ref`
    (a Key Vault secret name) and `secret_masked_preview` (e.g. '***xY1z') are exposed.
    Use `POST /admin/connections/{id}/rotate-secret` to mint a new value (server-side).
    """

    provider_id: str = Field(..., description="Stable provider key, e.g. 'azure_openai'.")
    category: ProviderCategory
    display_name: str = Field(..., description="Human label for the UI.")
    endpoint_url: str | None = None
    region: str | None = None
    deployments: list[ProviderDeployment] = Field(default_factory=list)
    secret_kv_ref: str | None = Field(
        default=None,
        description="Name of the secret in the configured Key Vault (NOT the value).",
    )
    secret_masked_preview: str | None = Field(
        default=None,
        description="Masked preview hint for the UI (e.g. '***xY1z') — never the real value.",
    )
    last_test_at: datetime | None = None
    last_test_status: TestStatus = "not_tested"
    last_test_detail: str | None = None
    last_rotated_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class ProviderSummary(BaseModel):
    """Lightweight summary for `GET /admin/connections` list view."""

    provider_id: str
    category: ProviderCategory
    display_name: str
    last_test_at: datetime | None = None
    last_test_status: TestStatus = "not_tested"


class ProviderPatch(BaseModel):
    """PATCH-able non-secret fields. Secret rotation has its own endpoint."""

    endpoint_url: str | None = None
    region: str | None = None
    display_name: str | None = None
    # deployments + secret_kv_ref deliberately omitted — Wave B+ may expose
    # deployment edits (currently they mirror Azure portal config), and secret
    # rotation is server-side only (no client-side value PATCH).


class TestConnectionResult(BaseModel):
    """`POST /admin/connections/{id}/test` response.

    Wave A scope = config-state check (Tier 1 mirrors W20 F2.1 `/health` pattern);
    Wave B+ promotes to real I/O pings against each provider's documented
    health endpoint.
    """

    status: TestStatus
    latency_ms: int | None = None
    detail: str | None = None


class RotateSecretResult(BaseModel):
    """`POST /admin/connections/{id}/rotate-secret` response.

    Returns metadata only — the new secret value lives in Key Vault and is
    consumed server-side by the next call to the provider. UI never sees the
    raw value (audit trail + secret hygiene per ADR-0026 Consequences).
    """

    provider_id: str
    last_rotated_at: datetime
    secret_masked_preview: str
