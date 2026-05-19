"""Key Vault provider — Protocol + EnvVar fallback (W24-wave-c1 F1 per ADR-0026 Option B).

Wave C1 promotes `/settings` from thin v1 (W22 F8.1 — 3 cards) to a 6-tab hub
with **Connections** + **Identity & Auth** + **API Keys & Quotas** tabs that
manage credentials for 9 external services. UI-driven secret rotation needs an
abstraction over the underlying secret store:

- **Production** — Azure Key Vault via `azure-keyvault-secrets` (Plan B (c)
  mobile-hotspot install 2026-05-19 per ADR-0017 occurrence #8; impl lives in
  `backend/storage/azure_key_vault.py` and is lazy-imported by the factory so
  unset `KEY_VAULT_URL` never touches `azure-keyvault-secrets`).
- **Local dev / CI / test** — `EnvVarProvider` reading from `os.environ` (the
  W1 `.env`-driven pattern preserved). `rotate_secret` raises `NotImplementedError`
  since env-var rotation requires a process restart that the runtime can't do
  on demand.

Mirrors the `kb_management.factory.make_kb_backend` + ADR-0023 graceful-degrade
shape: Protocol in this file, lazy production impl in a sibling file, factory
elsewhere. The pattern keeps `EnvVarProvider` install-free so local dev works
identically to W17-W23 behaviour.
"""

from __future__ import annotations

import os
import secrets as _secrets_token_module
from datetime import datetime, timezone
from typing import Protocol, runtime_checkable

from pydantic import BaseModel, Field


class SecretNotFoundError(Exception):
    """Raised when `get_secret` / `delete_secret` / `rotate_secret` targets a missing name."""


class SecretMetadata(BaseModel):
    """Lightweight secret descriptor returned by `list_secrets`.

    `value` is intentionally excluded — listing should never fan out the full
    secret payload. Use `get_secret(name)` to fetch a specific value when needed.
    """

    name: str
    enabled: bool = True
    updated_at: datetime | None = Field(
        default=None,
        description="Last-modified timestamp (Azure Key Vault `updated_on` or env-var sentinel).",
    )


@runtime_checkable
class KeyVaultProvider(Protocol):
    """Secret-store interface used by `/admin/connections/*/rotate-secret` etc.

    All methods are async to match the FastAPI / Azure SDK aio convention
    (CLAUDE.md §3.1). `EnvVarProvider` wraps sync `os.environ` access in
    `async def` no-ops; `AzureKeyVaultProvider` calls the real `aio` SDK.
    """

    async def get_secret(self, name: str) -> str: ...

    async def set_secret(self, name: str, value: str) -> SecretMetadata: ...

    async def delete_secret(self, name: str) -> None: ...

    async def list_secrets(self) -> list[SecretMetadata]: ...

    async def rotate_secret(self, name: str) -> str: ...
    """Generate a new random secret value, persist it, and return the new value."""


class EnvVarProvider:
    """`os.environ`-backed fallback for local dev / CI / test.

    Secret names map 1:1 onto env-var names (no namespacing). `set_secret` writes
    to `os.environ` for the current process only — restarts wipe the change,
    which is exactly the W1 `.env` behaviour callers expect. `rotate_secret`
    is *not* supported because env-var rotation requires a process restart that
    the runtime can't issue from inside a request handler (UI would have to
    surface a `<DisabledAffordance>` reason "Provider not configured for rotation
    — set KEY_VAULT_URL to enable").
    """

    async def get_secret(self, name: str) -> str:
        value = os.environ.get(name)
        if value is None:
            raise SecretNotFoundError(f"env var {name!r} not set")
        return value

    async def set_secret(self, name: str, value: str) -> SecretMetadata:
        os.environ[name] = value
        return SecretMetadata(
            name=name,
            enabled=True,
            updated_at=datetime.now(timezone.utc),
        )

    async def delete_secret(self, name: str) -> None:
        if name not in os.environ:
            raise SecretNotFoundError(f"env var {name!r} not set")
        del os.environ[name]

    async def list_secrets(self) -> list[SecretMetadata]:
        # Returning every env var would dump PATH / OS internals; callers that
        # need a curated list of "secret-shaped" env vars (Azure / Cohere / etc.)
        # filter at their layer. Returning an empty list here keeps the contract
        # honest: "EnvVarProvider doesn't enumerate, it dereferences by name."
        return []

    async def rotate_secret(self, name: str) -> str:
        raise NotImplementedError(
            "EnvVarProvider doesn't support rotation. Set KEY_VAULT_URL "
            "to switch to AzureKeyVaultProvider, which can rotate in place."
        )


def generate_secret_value(num_bytes: int = 32) -> str:
    """URL-safe 32-byte token suitable for client_secret / API key rotation.

    Used by `AzureKeyVaultProvider.rotate_secret` (and any provider that wants
    to share the same entropy source). Same `secrets.token_urlsafe` pattern as
    the verify-email token generator (`api/auth/email_provider.py`).
    """
    return _secrets_token_module.token_urlsafe(num_bytes)
