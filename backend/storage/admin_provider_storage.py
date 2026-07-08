"""Admin provider config storage — Protocol + InMemory impl + provider seed.

W102 / ADR-0072 added `sharepoint` (category `integration`) as the 10th provider,
carrying non-secret config (tenant_id / client_id) in the generic `settings` dict.

W24-wave-c1 F2 per ADR-0026 Option B. Mirrors the `kb_management.storage`
Protocol + lazy-import shape (ADR-0023):

- `AdminProviderConfigBackend` Protocol lives here
- `InMemoryAdminProviderBackend` lives here (install-free)
- `PostgresAdminProviderBackend` in `admin_provider_postgres.py` (lazy-imported
  by `admin_provider_factory.py`)

The 9 seeded providers map onto the Connections tab mockup categories. The seed
runs idempotently on first `list_all` / `get` — Tier 1 doesn't have a separate
provisioning step. PATCH-able fields update in place; the secret_kv_ref name is
seeded but not the value (value lives in the configured Key Vault, owned by the
operator via Azure portal / `az keyvault secret set`).
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol, runtime_checkable

from api.schemas.admin import (
    ProviderConfig,
    ProviderDeployment,
    ProviderPatch,
    TestStatus,
)


class ProviderNotFoundError(Exception):
    """Raised when a provider_id is not in the backend (after seeding)."""


# ---------- 9-provider default seed -----------------------------------------

# These rows match the Settings Connections tab mockup categories. They are the
# Tier 1 source-of-truth shape — Wave B+ may add providers (e.g. Speech / Vision
# for multimodal) but the existing 9 stay stable. `secret_kv_ref` names follow
# the `ekp-<provider>-<purpose>` convention so an operator can predict the Key
# Vault layout without consulting code.

_AZURE_OPENAI_DEPLOYMENTS = [
    ProviderDeployment(
        deployment_id="embedding",
        deployment_name="text-embedding-3-large",
        model_family="embedding",
        tpm_limit=350_000,
        rpm_limit=2_000,
    ),
    ProviderDeployment(
        deployment_id="llm_primary",
        deployment_name="gpt-5-5",
        model_family="chat",
        tpm_limit=200_000,
        rpm_limit=600,
    ),
    ProviderDeployment(
        deployment_id="llm_judge",
        deployment_name="gpt-5-4-mini",
        model_family="chat",
        tpm_limit=200_000,
        rpm_limit=1_200,
    ),
    ProviderDeployment(
        deployment_id="llm_eval_judge",
        deployment_name="gpt-5-5-pro",
        model_family="chat",
        tpm_limit=100_000,
        rpm_limit=300,
    ),
]


def _now() -> datetime:
    return datetime.now(UTC)


def default_providers() -> list[ProviderConfig]:
    """Return the 9-provider seed (idempotent — InMemory backend constructs once)."""
    now = _now()
    return [
        ProviderConfig(
            provider_id="azure_openai",
            category="llm",
            display_name="Azure OpenAI",
            endpoint_url="https://ekp-openai-poc.openai.azure.com",
            region="eastus2",
            deployments=_AZURE_OPENAI_DEPLOYMENTS,
            secret_kv_ref="ekp-azure-openai-api-key",
            secret_masked_preview=None,
            created_at=now,
            updated_at=now,
        ),
        ProviderConfig(
            provider_id="cohere",
            category="retrieval",
            display_name="Cohere Rerank (Azure Marketplace)",
            endpoint_url="https://Cohere-rerank-v4-0-poc.eastus2.models.ai.azure.com",
            region="eastus2",
            secret_kv_ref="ekp-cohere-api-key",
            secret_masked_preview=None,
            created_at=now,
            updated_at=now,
        ),
        ProviderConfig(
            provider_id="azure_search",
            category="retrieval",
            display_name="Azure AI Search",
            endpoint_url="https://ekp-search-poc.search.windows.net",
            region="eastus2",
            secret_kv_ref="ekp-azure-search-admin-key",
            secret_masked_preview=None,
            created_at=now,
            updated_at=now,
        ),
        ProviderConfig(
            provider_id="azure_blob",
            category="storage",
            display_name="Azure Blob Storage (Azurite local)",
            endpoint_url="http://127.0.0.1:10000",
            region="local",
            secret_kv_ref="ekp-azure-blob-connection-string",
            secret_masked_preview=None,
            created_at=now,
            updated_at=now,
        ),
        ProviderConfig(
            provider_id="postgres",
            category="storage",
            display_name="Postgres (KB + auth + conversations + admin)",
            endpoint_url="localhost:5432",
            region="local",
            secret_kv_ref="ekp-postgres-password",
            secret_masked_preview=None,
            created_at=now,
            updated_at=now,
        ),
        ProviderConfig(
            provider_id="langfuse",
            category="observability",
            display_name="Langfuse",
            endpoint_url="http://localhost:3000",
            region="local",
            secret_kv_ref="ekp-langfuse-secret-key",
            secret_masked_preview=None,
            created_at=now,
            updated_at=now,
        ),
        ProviderConfig(
            provider_id="acs_email",
            category="identity",
            display_name="Azure Communication Services Email",
            endpoint_url=None,
            region="eastus2",
            secret_kv_ref="ekp-acs-connection-string",
            secret_masked_preview=None,
            created_at=now,
            updated_at=now,
        ),
        ProviderConfig(
            provider_id="key_vault",
            category="identity",
            display_name="Azure Key Vault",
            endpoint_url=None,  # set per environment via KEY_VAULT_URL
            region="eastus2",
            secret_kv_ref=None,  # managed identity — no secret to rotate from here
            secret_masked_preview=None,
            created_at=now,
            updated_at=now,
        ),
        ProviderConfig(
            provider_id="structlog",
            category="observability",
            display_name="structlog (JSON log shipping)",
            endpoint_url=None,
            region=None,
            secret_kv_ref=None,
            secret_masked_preview=None,
            created_at=now,
            updated_at=now,
        ),
        # ADR-0072 — SharePoint source integration (managed connection). tenant_id /
        # client_id / credential_type are admin-set via UI (PATCH settings); the
        # client secret / cert lives in Key Vault under secret_kv_ref (set-secret).
        # Empty settings = "not configured" → integration route falls back to .env.
        ProviderConfig(
            provider_id="sharepoint",
            category="integration",
            display_name="SharePoint (Sites.Selected import)",
            endpoint_url=None,
            region=None,
            settings={"tenant_id": "", "client_id": "", "credential_type": "client_secret"},
            secret_kv_ref="ekp-sharepoint-client-secret",
            secret_masked_preview=None,
            created_at=now,
            updated_at=now,
        ),
    ]


# ---------- Protocol --------------------------------------------------------


@runtime_checkable
class AdminProviderConfigBackend(Protocol):
    """Admin provider CRUD interface. Implementations must be async-safe."""

    async def list_all(self) -> list[ProviderConfig]: ...

    async def get(self, provider_id: str) -> ProviderConfig: ...

    async def update(self, provider_id: str, patch: ProviderPatch) -> ProviderConfig: ...

    async def update_test_result(
        self,
        provider_id: str,
        *,
        status: TestStatus,
        detail: str | None,
        tested_at: datetime,
    ) -> ProviderConfig: ...

    async def update_rotation_timestamp(
        self,
        provider_id: str,
        *,
        rotated_at: datetime,
        secret_masked_preview: str,
    ) -> ProviderConfig: ...

    async def update_deployment_alert_threshold(
        self,
        provider_id: str,
        deployment_id: str,
        *,
        alert_threshold_pct: int,
    ) -> ProviderConfig: ...


# ---------- InMemory impl ---------------------------------------------------


class InMemoryAdminProviderBackend:
    """Process-local provider config store seeded with the 9 defaults.

    Tier 1 dev / CI baseline — restart-wipes (matches `InMemoryKBBackend`'s
    W17-era shape). PATCH mutations stay in memory; Postgres path persists.
    """

    def __init__(self) -> None:
        self._configs: dict[str, ProviderConfig] = {p.provider_id: p for p in default_providers()}

    async def list_all(self) -> list[ProviderConfig]:
        return list(self._configs.values())

    async def get(self, provider_id: str) -> ProviderConfig:
        if provider_id not in self._configs:
            raise ProviderNotFoundError(f"provider {provider_id!r} not found")
        return self._configs[provider_id]

    async def update(self, provider_id: str, patch: ProviderPatch) -> ProviderConfig:
        current = await self.get(provider_id)
        updated = current.model_copy(
            update={
                **{k: v for k, v in patch.model_dump(exclude_unset=True).items() if v is not None},
                "updated_at": _now(),
            }
        )
        self._configs[provider_id] = updated
        return updated

    async def update_test_result(
        self,
        provider_id: str,
        *,
        status: TestStatus,
        detail: str | None,
        tested_at: datetime,
    ) -> ProviderConfig:
        current = await self.get(provider_id)
        updated = current.model_copy(
            update={
                "last_test_status": status,
                "last_test_detail": detail,
                "last_test_at": tested_at,
                "updated_at": _now(),
            }
        )
        self._configs[provider_id] = updated
        return updated

    async def update_rotation_timestamp(
        self,
        provider_id: str,
        *,
        rotated_at: datetime,
        secret_masked_preview: str,
    ) -> ProviderConfig:
        current = await self.get(provider_id)
        updated = current.model_copy(
            update={
                "last_rotated_at": rotated_at,
                "secret_masked_preview": secret_masked_preview,
                "updated_at": _now(),
            }
        )
        self._configs[provider_id] = updated
        return updated

    async def update_deployment_alert_threshold(
        self,
        provider_id: str,
        deployment_id: str,
        *,
        alert_threshold_pct: int,
    ) -> ProviderConfig:
        current = await self.get(provider_id)
        new_deployments = []
        found = False
        for d in current.deployments:
            if d.deployment_id == deployment_id:
                new_deployments.append(d.model_copy(update={"alert_threshold_pct": alert_threshold_pct}))
                found = True
            else:
                new_deployments.append(d)
        if not found:
            raise ProviderNotFoundError(
                f"deployment {deployment_id!r} not found in provider {provider_id!r}"
            )
        updated = current.model_copy(update={"deployments": new_deployments, "updated_at": _now()})
        self._configs[provider_id] = updated
        return updated
