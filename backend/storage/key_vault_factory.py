"""Key Vault provider factory (W24-wave-c1 F1 per ADR-0026 Option B).

Picks `AzureKeyVaultProvider` when `settings.key_vault_url` is set, else the
process-local `EnvVarProvider` (W1 `.env` workflow preserved). Mirrors the
`kb_management.factory.make_kb_backend` + ADR-0023 lazy-import shape so unset
`KEY_VAULT_URL` never touches `azure-keyvault-secrets` — local dev / CI work
identically to W17-W23 even if the SDK install is missing or stale.
"""

from __future__ import annotations

from storage.key_vault import EnvVarProvider, KeyVaultProvider
from storage.settings import Settings


def make_key_vault_provider(settings: Settings) -> KeyVaultProvider:
    """Return an Azure-backed provider when `key_vault_url` is set, else env-var fallback."""
    if settings.key_vault_url:
        # Lazy import — same shape as `make_kb_backend` (ADR-0023). Keeps the
        # `azure-keyvault-secrets` SDK out of the import graph for callers that
        # only need the EnvVarProvider path (local dev / CI / R8-blocked installs).
        from storage.azure_key_vault import AzureKeyVaultProvider

        return AzureKeyVaultProvider(settings.key_vault_url)
    return EnvVarProvider()
