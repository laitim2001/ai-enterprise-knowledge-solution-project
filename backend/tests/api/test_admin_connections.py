"""`/admin/connections/*` route tests (W24-wave-c1 F2 per ADR-0026 Option B).

5 endpoints × 9 providers, plus the storage Protocol seed shape. Uses the
`_build_app` minimal-FastAPI pattern from `test_health_route.py` (bypasses
the real `lifespan`, attaches our InMemory backend + a `MagicMock`-shaped
KeyVaultProvider directly to `app.state`).

Mocked test-connection logic is the Wave A config-state-only contract (per
W20 F2.1 `/health` pattern); Wave B+ would replace the `_probe_*` helpers
with real provider pings.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routes.admin import connections as admin_connections
from storage.admin_provider_storage import (
    InMemoryAdminProviderBackend,
    default_providers,
)
from storage.key_vault import (
    EnvVarProvider,
    KeyVaultProvider,
    SecretMetadata,
)


def _build_app(
    *,
    backend: Any | None = None,
    key_vault: Any | None = None,
) -> FastAPI:
    """Minimal FastAPI with the admin connections router + state injected."""
    app = FastAPI()
    app.include_router(admin_connections.router)
    app.state.admin_provider_backend = backend
    app.state.key_vault_provider = key_vault
    return app


@pytest.fixture(autouse=True)
def _clean_settings_cache() -> Iterator[None]:
    """`get_settings()` is `@lru_cache`d — clear between tests so env state stays isolated."""
    from storage.settings import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


# --------------------------------------------------------------------------- #
# Storage Protocol seed
# --------------------------------------------------------------------------- #


def test_default_providers_returns_ten_entries() -> None:
    """Seed must contain exactly the 10 providers spec'd in ADR-0026 + ADR-0072 (sharepoint)."""
    providers = default_providers()
    assert len(providers) == 10
    ids = {p.provider_id for p in providers}
    assert ids == {
        "azure_openai",
        "cohere",
        "azure_search",
        "azure_blob",
        "postgres",
        "langfuse",
        "acs_email",
        "key_vault",
        "structlog",
        "sharepoint",
    }


def test_default_providers_categories_match_spec() -> None:
    """Each provider lands in a documented category — UI groups by category."""
    by_id = {p.provider_id: p for p in default_providers()}
    assert by_id["azure_openai"].category == "llm"
    assert by_id["cohere"].category == "retrieval"
    assert by_id["azure_search"].category == "retrieval"
    assert by_id["azure_blob"].category == "storage"
    assert by_id["postgres"].category == "storage"
    assert by_id["langfuse"].category == "observability"
    assert by_id["structlog"].category == "observability"
    assert by_id["acs_email"].category == "identity"
    assert by_id["key_vault"].category == "identity"
    assert by_id["sharepoint"].category == "integration"


def test_default_azure_openai_has_four_deployments() -> None:
    """Azure OpenAI seed exposes the 4 deployments the Tier 1 stack uses."""
    by_id = {p.provider_id: p for p in default_providers()}
    azure = by_id["azure_openai"]
    deployment_ids = {d.deployment_id for d in azure.deployments}
    assert deployment_ids == {"embedding", "llm_primary", "llm_judge", "llm_eval_judge"}


@pytest.mark.asyncio
async def test_in_memory_backend_seeds_ten_on_construct() -> None:
    backend = InMemoryAdminProviderBackend()
    configs = await backend.list_all()
    assert len(configs) == 10


@pytest.mark.asyncio
async def test_in_memory_backend_update_persists_in_process() -> None:
    from api.schemas.admin import ProviderPatch

    backend = InMemoryAdminProviderBackend()
    updated = await backend.update(
        "cohere",
        ProviderPatch(display_name="Cohere (custom display name)"),
    )
    assert updated.display_name == "Cohere (custom display name)"
    # Re-fetch — same backend instance preserves the patch.
    refetched = await backend.get("cohere")
    assert refetched.display_name == "Cohere (custom display name)"


# --------------------------------------------------------------------------- #
# GET /admin/connections
# --------------------------------------------------------------------------- #


def test_list_connections_returns_ten_summaries() -> None:
    app = _build_app(backend=InMemoryAdminProviderBackend(), key_vault=EnvVarProvider())
    client = TestClient(app)
    response = client.get("/admin/connections")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 10
    assert {row["provider_id"] for row in body} == {
        "azure_openai",
        "cohere",
        "azure_search",
        "azure_blob",
        "postgres",
        "langfuse",
        "acs_email",
        "key_vault",
        "structlog",
        "sharepoint",
    }


def test_list_connections_503_when_backend_not_initialized() -> None:
    """A request that hits before the lifespan wired the backend returns 503."""
    app = _build_app(backend=None, key_vault=EnvVarProvider())
    client = TestClient(app)
    response = client.get("/admin/connections")
    assert response.status_code == 503


# --------------------------------------------------------------------------- #
# GET /admin/connections/{provider_id}
# --------------------------------------------------------------------------- #


def test_get_connection_returns_full_config() -> None:
    app = _build_app(backend=InMemoryAdminProviderBackend(), key_vault=EnvVarProvider())
    client = TestClient(app)
    response = client.get("/admin/connections/azure_openai")
    assert response.status_code == 200
    body = response.json()
    assert body["provider_id"] == "azure_openai"
    assert body["category"] == "llm"
    assert len(body["deployments"]) == 4
    # Secret value is NEVER exposed — only the KV ref name.
    assert body["secret_kv_ref"] == "ekp-azure-openai-api-key"
    assert "api_key" not in body
    assert "client_secret" not in body


def test_get_connection_unknown_provider_returns_404() -> None:
    app = _build_app(backend=InMemoryAdminProviderBackend(), key_vault=EnvVarProvider())
    client = TestClient(app)
    response = client.get("/admin/connections/no_such_provider")
    assert response.status_code == 404


# --------------------------------------------------------------------------- #
# PATCH /admin/connections/{provider_id}
# --------------------------------------------------------------------------- #


def test_patch_connection_updates_display_name() -> None:
    backend = InMemoryAdminProviderBackend()
    app = _build_app(backend=backend, key_vault=EnvVarProvider())
    client = TestClient(app)
    response = client.patch(
        "/admin/connections/cohere",
        json={"display_name": "Cohere v4.0-pro (production)"},
    )
    assert response.status_code == 200
    assert response.json()["display_name"] == "Cohere v4.0-pro (production)"


def test_patch_connection_unknown_provider_returns_404() -> None:
    app = _build_app(backend=InMemoryAdminProviderBackend(), key_vault=EnvVarProvider())
    client = TestClient(app)
    response = client.patch(
        "/admin/connections/no_such", json={"display_name": "X"}
    )
    assert response.status_code == 404


def test_patch_connection_no_fields_is_idempotent_get() -> None:
    """Empty PATCH body returns the current row unchanged (idempotent contract)."""
    app = _build_app(backend=InMemoryAdminProviderBackend(), key_vault=EnvVarProvider())
    client = TestClient(app)
    response = client.patch("/admin/connections/azure_search", json={})
    assert response.status_code == 200
    assert response.json()["provider_id"] == "azure_search"


# --------------------------------------------------------------------------- #
# POST /admin/connections/{provider_id}/test
# --------------------------------------------------------------------------- #


def test_test_connection_azure_openai_https_endpoint_returns_ok() -> None:
    """Seed config has an HTTPS endpoint — config-state probe says OK."""
    app = _build_app(backend=InMemoryAdminProviderBackend(), key_vault=EnvVarProvider())
    client = TestClient(app)
    response = client.post("/admin/connections/azure_openai/test")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"


def test_test_connection_azure_blob_local_http_returns_ok() -> None:
    """Azurite endpoint is HTTP — the azure_blob probe allows local HTTP."""
    app = _build_app(backend=InMemoryAdminProviderBackend(), key_vault=EnvVarProvider())
    client = TestClient(app)
    response = client.post("/admin/connections/azure_blob/test")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    # The detail copy hints at local HTTP (operator confirmation that this is Azurite).
    assert "local HTTP" in (body["detail"] or "")


def test_test_connection_postgres_not_configured_when_database_url_unset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Empty (not delete) — the dev `.env` may carry DATABASE_URL; an empty env
    # var overrides the `.env` file value, `delenv` would expose it. BUG-008.
    monkeypatch.setenv("DATABASE_URL", "")
    app = _build_app(backend=InMemoryAdminProviderBackend(), key_vault=EnvVarProvider())
    client = TestClient(app)
    response = client.post("/admin/connections/postgres/test")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "not_tested"
    assert "DATABASE_URL" in (body["detail"] or "")


def test_test_connection_key_vault_not_configured_when_url_unset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("KEY_VAULT_URL", raising=False)
    app = _build_app(backend=InMemoryAdminProviderBackend(), key_vault=EnvVarProvider())
    client = TestClient(app)
    response = client.post("/admin/connections/key_vault/test")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "not_tested"


def test_test_connection_structlog_always_ok() -> None:
    """structlog is config-only — probe always returns ok."""
    app = _build_app(backend=InMemoryAdminProviderBackend(), key_vault=EnvVarProvider())
    client = TestClient(app)
    response = client.post("/admin/connections/structlog/test")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_test_connection_persists_last_test_status() -> None:
    """A successful test writes last_test_at + last_test_status back to the backend."""
    backend = InMemoryAdminProviderBackend()
    app = _build_app(backend=backend, key_vault=EnvVarProvider())
    client = TestClient(app)
    client.post("/admin/connections/azure_openai/test")
    response = client.get("/admin/connections/azure_openai")
    body = response.json()
    assert body["last_test_status"] == "ok"
    assert body["last_test_at"] is not None


def test_test_connection_unknown_provider_returns_404() -> None:
    app = _build_app(backend=InMemoryAdminProviderBackend(), key_vault=EnvVarProvider())
    client = TestClient(app)
    response = client.post("/admin/connections/no_such/test")
    assert response.status_code == 404


# --------------------------------------------------------------------------- #
# POST /admin/connections/{provider_id}/rotate-secret
# --------------------------------------------------------------------------- #


def _make_mock_kv(new_value: str = "new-rotated-value-with-suffix-xY1z") -> MagicMock:
    """A KeyVaultProvider mock that rotates to a known value (so masking is testable)."""
    mock = MagicMock(spec=KeyVaultProvider)
    mock.rotate_secret = AsyncMock(return_value=new_value)
    return mock


def test_rotate_secret_succeeds_and_returns_masked_preview() -> None:
    backend = InMemoryAdminProviderBackend()
    kv = _make_mock_kv("new-rotated-value-with-suffix-xY1z")
    app = _build_app(backend=backend, key_vault=kv)
    client = TestClient(app)
    response = client.post("/admin/connections/cohere/rotate-secret")
    assert response.status_code == 200
    body = response.json()
    assert body["provider_id"] == "cohere"
    # Mask = "***" + last 4 chars.
    assert body["secret_masked_preview"] == "***xY1z"
    kv.rotate_secret.assert_awaited_once_with("ekp-cohere-api-key")


def test_rotate_secret_persists_last_rotated_at() -> None:
    backend = InMemoryAdminProviderBackend()
    kv = _make_mock_kv()
    app = _build_app(backend=backend, key_vault=kv)
    client = TestClient(app)
    client.post("/admin/connections/azure_search/rotate-secret")
    response = client.get("/admin/connections/azure_search")
    body = response.json()
    assert body["last_rotated_at"] is not None
    assert body["secret_masked_preview"] is not None


def test_rotate_secret_400_when_provider_has_no_kv_ref() -> None:
    """key_vault and structlog have no rotatable secret — UI shows DisabledAffordance,
    server returns 400 if hit directly."""
    backend = InMemoryAdminProviderBackend()
    kv = _make_mock_kv()
    app = _build_app(backend=backend, key_vault=kv)
    client = TestClient(app)
    response = client.post("/admin/connections/key_vault/rotate-secret")
    assert response.status_code == 400


def test_rotate_secret_503_when_env_var_provider_used() -> None:
    """EnvVarProvider.rotate_secret raises NotImplementedError — surfaced as 503."""
    backend = InMemoryAdminProviderBackend()
    # Real EnvVarProvider (NOT a mock) — its rotate_secret raises.
    app = _build_app(backend=backend, key_vault=EnvVarProvider())
    client = TestClient(app)
    response = client.post("/admin/connections/cohere/rotate-secret")
    assert response.status_code == 503
    # The error message hints at the fix (the UI consumes this for the Rotate-button DisabledAffordance reason).
    assert "KEY_VAULT_URL" in response.json()["detail"]


def test_rotate_secret_unknown_provider_returns_404() -> None:
    app = _build_app(backend=InMemoryAdminProviderBackend(), key_vault=_make_mock_kv())
    client = TestClient(app)
    response = client.post("/admin/connections/no_such/rotate-secret")
    assert response.status_code == 404


# --------------------------------------------------------------------------- #
# Cross-cutting — masking helper
# --------------------------------------------------------------------------- #


def test_mask_secret_short_value_returns_three_stars_only() -> None:
    from api.routes.admin.connections import _mask_secret

    assert _mask_secret("abc") == "***"
    assert _mask_secret("abcd") == "***"
    assert _mask_secret("abcde") == "***bcde"


def test_mask_secret_typical_token_keeps_last_four() -> None:
    from api.routes.admin.connections import _mask_secret

    masked = _mask_secret("sk-lf-1234567890abcdef")
    assert masked.startswith("***")
    assert masked.endswith("cdef")
    # Body of the secret is hidden — no characters from the middle leak.
    assert "1234567890ab" not in masked


# --------------------------------------------------------------------------- #
# Secret metadata round-trip (covered indirectly above; sanity pin here)
# --------------------------------------------------------------------------- #


def test_secret_metadata_shape() -> None:
    meta = SecretMetadata(name="ekp-cohere-api-key")
    assert meta.name == "ekp-cohere-api-key"
    assert meta.enabled is True
    assert meta.updated_at is None
