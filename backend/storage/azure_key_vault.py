"""AzureKeyVaultProvider — production `KeyVaultProvider` impl (W24-wave-c1 F1).

Lazy-imported by `storage.key_vault_factory.make_key_vault_provider`. Unset
`KEY_VAULT_URL` never touches `azure-keyvault-secrets`, mirroring the
`kb_management.postgres_backend` lazy-import shape (ADR-0023) so local dev
works without the SDK installed.

Install notes:
- `azure-keyvault-secrets>=4.8.0` + `azure-identity>=1.18.0` installed
  2026-05-19 via Plan B (c) mobile-hotspot per ADR-0017 occurrence #8 (Langfuse
  SDK 2026-05-16 precedent). Re-install on a clean checkout requires either a
  PyPI-reachable network (corp proxy may block the 600KB+ binary wheel — R8) or
  the same mobile-hotspot workflow.

Authentication:
- Uses `DefaultAzureCredential` from `azure.identity.aio` — tries Azure CLI →
  Managed Identity → environment variables → VS Code in that order. In Container
  Apps production (per ADR-0024 + Q11 operational), Managed Identity is the
  expected resolved credential; local dev expects `az login` ahead of time.

Threading + lifecycle:
- The aio `SecretClient` holds an HTTP session that must be closed. We keep one
  long-lived client per provider instance and rely on FastAPI's `lifespan` to
  call `aclose()` at shutdown (factory wires the cleanup). Per-call short-lived
  clients would add a TLS handshake per request — unacceptable for the
  `/admin/connections/{id}/test` interactive flow.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from storage.key_vault import (
    KeyVaultProvider,
    SecretMetadata,
    SecretNotFoundError,
    generate_secret_value,
)

if TYPE_CHECKING:
    # Only imported during type-checking so unset KEY_VAULT_URL paths don't pay
    # the SDK import cost (matches the kb_management/postgres_backend.py pattern).
    from azure.identity.aio import DefaultAzureCredential
    from azure.keyvault.secrets.aio import SecretClient


class AzureKeyVaultProvider:
    """`KeyVaultProvider` backed by Azure Key Vault Secrets.

    Construct with the vault URL (e.g. `https://ekp-prod-kv.vault.azure.net`).
    Credential resolution defers to `DefaultAzureCredential` so production
    (Managed Identity) and local dev (`az login`) work without code changes.
    """

    def __init__(self, vault_url: str) -> None:
        # Local imports avoid hitting `azure-keyvault-secrets` when callers
        # import this module only for type hints. The factory does the same
        # lazy-import dance one level up so unset KEY_VAULT_URL skips this
        # whole file.
        from azure.identity.aio import DefaultAzureCredential
        from azure.keyvault.secrets.aio import SecretClient

        self._vault_url = vault_url
        self._credential: DefaultAzureCredential = DefaultAzureCredential()
        self._client: SecretClient = SecretClient(
            vault_url=vault_url,
            credential=self._credential,
        )

    async def get_secret(self, name: str) -> str:
        from azure.core.exceptions import ResourceNotFoundError

        try:
            secret = await self._client.get_secret(name)
        except ResourceNotFoundError as e:
            raise SecretNotFoundError(f"key vault secret {name!r} not found") from e
        if secret.value is None:
            # KV returns None for deleted-but-recoverable secrets; treat as not-found
            # so callers don't have to disambiguate (UI rotate-secret flow would
            # have surfaced a different control if soft-delete was relevant).
            raise SecretNotFoundError(f"key vault secret {name!r} has no value")
        return secret.value

    async def set_secret(self, name: str, value: str) -> SecretMetadata:
        secret = await self._client.set_secret(name, value)
        return SecretMetadata(
            name=secret.name or name,
            enabled=secret.properties.enabled if secret.properties.enabled is not None else True,
            updated_at=secret.properties.updated_on or datetime.now(UTC),
        )

    async def delete_secret(self, name: str) -> None:
        from azure.core.exceptions import ResourceNotFoundError

        try:
            # The aio SecretClient's `delete_secret` (unlike the sync client's
            # `begin_delete_secret` LROPoller) returns once the soft-delete is
            # accepted by Azure — sufficient for the rotation flow (audit_log
            # row writes the deletion event before returning to the caller).
            await self._client.delete_secret(name)
        except ResourceNotFoundError as e:
            raise SecretNotFoundError(f"key vault secret {name!r} not found") from e

    async def list_secrets(self) -> list[SecretMetadata]:
        results: list[SecretMetadata] = []
        async for prop in self._client.list_properties_of_secrets():
            results.append(
                SecretMetadata(
                    name=prop.name or "",
                    enabled=prop.enabled if prop.enabled is not None else True,
                    updated_at=prop.updated_on,
                )
            )
        return results

    async def rotate_secret(self, name: str) -> str:
        # New random value, then set as a new version. KV preserves the old
        # version implicitly (Soft delete + versioning on the vault); the new
        # value becomes the active one. Caller writes audit_log row with the
        # previous + new version IDs if needed.
        new_value = generate_secret_value()
        await self.set_secret(name, new_value)
        return new_value

    async def aclose(self) -> None:
        """Release the underlying HTTP session + credential token cache.

        Wire from FastAPI `lifespan` shutdown (factory will register this hook
        when the provider is created in the app startup sequence).
        """
        await self._client.close()
        await self._credential.close()


# Re-export Protocol so the factory + admin routes can import a single symbol.
__all__ = ["AzureKeyVaultProvider", "KeyVaultProvider"]
