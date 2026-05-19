"""Key Vault provider unit tests (W24-wave-c1 F1 per ADR-0026 Option B).

Covers `backend/storage/key_vault.py` + `key_vault_factory.py` per CLAUDE.md §5.6
H6 (Settings hub will run secret rotation through this Protocol — production
path can't have surprises). `AzureKeyVaultProvider` real-Azure interactions are
tested at the Protocol contract level via `unittest.mock`; the live Azure smoke
is W24+/CO17 R8-bounded territory and is wired in `tests/api/admin/*` against
the populated cloud once Track A IT cred lands.

Test taxonomy:
- EnvVarProvider — full round-trip against `os.environ` (set / get / delete /
  list / rotate-raises).
- generate_secret_value — entropy sanity (urlsafe alphabet + length distribution).
- make_key_vault_provider — branch selection by `settings.key_vault_url`.
- AzureKeyVaultProvider — instantiation contract (mocked SDK) so unset
  KEY_VAULT_URL paths still verify the lazy-import shape.
"""

from __future__ import annotations

import os
import string
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from storage.key_vault import (
    EnvVarProvider,
    KeyVaultProvider,
    SecretMetadata,
    SecretNotFoundError,
    generate_secret_value,
)
from storage.key_vault_factory import make_key_vault_provider
from storage.settings import Settings

# ----- EnvVarProvider round-trip -----


@pytest.mark.asyncio
async def test_env_var_provider_set_and_get_round_trip() -> None:
    provider = EnvVarProvider()
    await provider.set_secret("EKP_TEST_SECRET_SET_GET", "round-trip-value")
    assert await provider.get_secret("EKP_TEST_SECRET_SET_GET") == "round-trip-value"
    # Cleanup so the test doesn't leak into the rest of the suite.
    await provider.delete_secret("EKP_TEST_SECRET_SET_GET")


@pytest.mark.asyncio
async def test_env_var_provider_get_missing_raises() -> None:
    provider = EnvVarProvider()
    # Guarantee the env var is unset for the duration of this test.
    os.environ.pop("EKP_TEST_SECRET_DEFINITELY_UNSET", None)
    with pytest.raises(SecretNotFoundError):
        await provider.get_secret("EKP_TEST_SECRET_DEFINITELY_UNSET")


@pytest.mark.asyncio
async def test_env_var_provider_delete_missing_raises() -> None:
    provider = EnvVarProvider()
    os.environ.pop("EKP_TEST_SECRET_DELETE_MISSING", None)
    with pytest.raises(SecretNotFoundError):
        await provider.delete_secret("EKP_TEST_SECRET_DELETE_MISSING")


@pytest.mark.asyncio
async def test_env_var_provider_set_returns_metadata() -> None:
    provider = EnvVarProvider()
    meta = await provider.set_secret("EKP_TEST_SECRET_META", "value")
    assert isinstance(meta, SecretMetadata)
    assert meta.name == "EKP_TEST_SECRET_META"
    assert meta.enabled is True
    assert meta.updated_at is not None
    await provider.delete_secret("EKP_TEST_SECRET_META")


@pytest.mark.asyncio
async def test_env_var_provider_list_returns_empty_by_contract() -> None:
    # Listing every env var would dump PATH / system internals — the contract
    # returns an empty list and lets callers filter by name through get_secret.
    provider = EnvVarProvider()
    assert await provider.list_secrets() == []


@pytest.mark.asyncio
async def test_env_var_provider_rotate_raises_not_implemented() -> None:
    provider = EnvVarProvider()
    with pytest.raises(NotImplementedError) as exc:
        await provider.rotate_secret("EKP_TEST_SECRET_ROTATE")
    # The error message is the actionable signal the /admin/connections/*
    # surface relies on to render a <DisabledAffordance> reason — pin it.
    assert "KEY_VAULT_URL" in str(exc.value)


# ----- generate_secret_value entropy -----


def test_generate_secret_value_returns_urlsafe_string() -> None:
    value = generate_secret_value()
    # token_urlsafe base64-url alphabet: letters + digits + - + _
    allowed = set(string.ascii_letters + string.digits + "-_")
    assert set(value).issubset(allowed), f"non-urlsafe char in {value!r}"


def test_generate_secret_value_default_length_reasonable() -> None:
    # 32 input bytes → base64-url ~ 43 chars (4 * ceil(32/3) - padding stripped).
    # We don't pin exact length (Python's token_urlsafe doc says "approximately
    # 1.3x nbytes") — just sanity-check the rough range so a wholly different
    # default doesn't slip in without anyone noticing.
    value = generate_secret_value()
    assert 40 <= len(value) <= 50


def test_generate_secret_value_two_calls_differ() -> None:
    # 32-byte entropy collision probability is ~ 2^-256 — if these match,
    # the RNG is broken, not the test flaky.
    assert generate_secret_value() != generate_secret_value()


# ----- Factory branch selection -----


def test_factory_returns_env_var_provider_when_unset() -> None:
    settings = Settings(key_vault_url="")
    provider = make_key_vault_provider(settings)
    assert isinstance(provider, EnvVarProvider)


def test_factory_returns_azure_provider_when_url_set() -> None:
    # The factory's lazy import only fires when key_vault_url is truthy — patch
    # the AzureKeyVaultProvider class so we don't construct a real SDK client
    # (which would try to instantiate DefaultAzureCredential).
    settings = Settings(key_vault_url="https://ekp-test.vault.azure.net")
    with patch("storage.azure_key_vault.AzureKeyVaultProvider") as mock_class:
        mock_instance = MagicMock(spec=KeyVaultProvider)
        mock_class.return_value = mock_instance
        provider = make_key_vault_provider(settings)
        mock_class.assert_called_once_with("https://ekp-test.vault.azure.net")
        assert provider is mock_instance


# ----- AzureKeyVaultProvider Protocol conformance (SDK mocked) -----


@pytest.mark.asyncio
async def test_azure_key_vault_provider_get_secret_returns_value() -> None:
    # Build the provider with the SDK constructors patched so no real network
    # / credential resolution happens. The aio SecretClient.get_secret returns
    # an object with `.value` — mirror that shape.
    with patch("azure.keyvault.secrets.aio.SecretClient") as mock_client_class, patch(
        "azure.identity.aio.DefaultAzureCredential"
    ):
        mock_secret = MagicMock()
        mock_secret.value = "the-real-secret-value"
        mock_client = MagicMock()
        mock_client.get_secret = AsyncMock(return_value=mock_secret)
        mock_client_class.return_value = mock_client

        from storage.azure_key_vault import AzureKeyVaultProvider

        provider = AzureKeyVaultProvider("https://ekp-test.vault.azure.net")
        value = await provider.get_secret("client-secret")
        assert value == "the-real-secret-value"
        mock_client.get_secret.assert_awaited_once_with("client-secret")


@pytest.mark.asyncio
async def test_azure_key_vault_provider_get_secret_raises_on_not_found() -> None:
    from azure.core.exceptions import ResourceNotFoundError

    with patch("azure.keyvault.secrets.aio.SecretClient") as mock_client_class, patch(
        "azure.identity.aio.DefaultAzureCredential"
    ):
        mock_client = MagicMock()
        mock_client.get_secret = AsyncMock(
            side_effect=ResourceNotFoundError("secret not found")
        )
        mock_client_class.return_value = mock_client

        from storage.azure_key_vault import AzureKeyVaultProvider

        provider = AzureKeyVaultProvider("https://ekp-test.vault.azure.net")
        with pytest.raises(SecretNotFoundError):
            await provider.get_secret("missing-secret")


@pytest.mark.asyncio
async def test_azure_key_vault_provider_rotate_secret_returns_new_value() -> None:
    # rotate_secret = generate + set_secret. We patch set_secret directly on
    # the instance to confirm the new value flows back to the caller (the
    # /admin/connections/*/rotate-secret endpoint relies on this round-trip).
    with patch("azure.keyvault.secrets.aio.SecretClient") as mock_client_class, patch(
        "azure.identity.aio.DefaultAzureCredential"
    ):
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        from storage.azure_key_vault import AzureKeyVaultProvider

        provider = AzureKeyVaultProvider("https://ekp-test.vault.azure.net")
        # Patch set_secret on the instance to capture what rotate generated.
        captured: list[str] = []

        async def fake_set(name: str, value: str) -> SecretMetadata:
            captured.append(value)
            return SecretMetadata(name=name)

        provider.set_secret = fake_set  # type: ignore[method-assign]
        new_value = await provider.rotate_secret("client-secret")
        assert new_value == captured[0]
        assert len(new_value) > 0


@pytest.mark.asyncio
async def test_azure_key_vault_provider_aclose_releases_resources() -> None:
    with patch("azure.keyvault.secrets.aio.SecretClient") as mock_client_class, patch(
        "azure.identity.aio.DefaultAzureCredential"
    ) as mock_cred_class:
        mock_client = MagicMock()
        mock_client.close = AsyncMock()
        mock_client_class.return_value = mock_client
        mock_cred = MagicMock()
        mock_cred.close = AsyncMock()
        mock_cred_class.return_value = mock_cred

        from storage.azure_key_vault import AzureKeyVaultProvider

        provider = AzureKeyVaultProvider("https://ekp-test.vault.azure.net")
        await provider.aclose()
        mock_client.close.assert_awaited_once()
        mock_cred.close.assert_awaited_once()
