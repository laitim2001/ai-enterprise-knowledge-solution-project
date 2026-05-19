"""`/admin/connections/*` — 9-provider config CRUD + test + rotate (W24-wave-c1 F2).

5 endpoints per ADR-0026 Option B fully editable Settings:

- `GET /admin/connections` → 9 ProviderSummary rows
- `GET /admin/connections/{provider_id}` → ProviderConfig (secret masked)
- `PATCH /admin/connections/{provider_id}` → update non-secret fields
- `POST /admin/connections/{provider_id}/test` → config-state probe
- `POST /admin/connections/{provider_id}/rotate-secret` → KeyVault rotation

**Test-connection probes are config-state checks** (Wave A scope, mirrors W20
F2.1 `/health` pattern):they verify required env / endpoint settings without
issuing real I/O. Real provider pings (Azure OpenAI `models.list()`, Postgres
`SELECT 1`, etc.) are Wave B+ promotion — they trade flap risk + Azure-key
binding for marginal signal until Beta cohort traffic surfaces actual outages.

**Rotation flow**:`KeyVaultProvider.rotate_secret` generates a fresh
`secrets.token_urlsafe(32)` value via Azure Key Vault, then the backend records
a masked preview (`***` + last 4 chars) and a timestamp. UI never sees the
real value — secret hygiene per ADR-0026 §Consequences.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request, status

from api.schemas.admin import (
    ProviderConfig,
    ProviderPatch,
    ProviderSummary,
    RotateSecretResult,
    TestConnectionResult,
    TestStatus,
)
from storage.admin_provider_storage import (
    AdminProviderConfigBackend,
    ProviderNotFoundError,
)
from storage.key_vault import KeyVaultProvider, SecretNotFoundError
from storage.settings import Settings, get_settings

router = APIRouter(prefix="/admin/connections")


def _get_backend(request: Request) -> AdminProviderConfigBackend:
    backend = getattr(request.app.state, "admin_provider_backend", None)
    if backend is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="admin_provider_backend not initialized — check lifespan logs",
        )
    return backend  # type: ignore[no-any-return]


def _get_key_vault(request: Request) -> KeyVaultProvider:
    provider = getattr(request.app.state, "key_vault_provider", None)
    if provider is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="key_vault_provider not initialized — check lifespan logs",
        )
    return provider  # type: ignore[no-any-return]


def _mask_secret(value: str) -> str:
    """Return a UI-safe preview: '***' + last 4 chars (or '***' for short values)."""
    if len(value) <= 4:
        return "***"
    return f"***{value[-4:]}"


# ---------- Config-state probes (Wave A scope; Wave B+ → real I/O) -----------


def _probe_https_endpoint(
    cfg: ProviderConfig, allow_http_local: bool = False
) -> TestConnectionResult:
    """Generic HTTPS endpoint config check for cloud providers."""
    if not cfg.endpoint_url:
        return TestConnectionResult(
            status="error", latency_ms=0, detail="endpoint_url not configured"
        )
    if cfg.endpoint_url.startswith("https://"):
        return TestConnectionResult(status="ok", latency_ms=0, detail="config OK")
    if allow_http_local and cfg.endpoint_url.startswith("http://"):
        return TestConnectionResult(
            status="ok",
            latency_ms=0,
            detail="config OK (local HTTP — production should use HTTPS)",
        )
    return TestConnectionResult(
        status="degraded", latency_ms=0, detail="endpoint_url should be HTTPS"
    )


def _probe_postgres(cfg: ProviderConfig, settings: Settings) -> TestConnectionResult:
    if not settings.database_url:
        return TestConnectionResult(
            status="not_tested",
            latency_ms=0,
            detail="DATABASE_URL unset — in-memory fallback (ADR-0023)",
        )
    return TestConnectionResult(
        status="ok", latency_ms=0, detail="DATABASE_URL configured (Wave B+ adds SELECT 1 ping)"
    )


def _probe_key_vault(cfg: ProviderConfig, settings: Settings) -> TestConnectionResult:
    if not settings.key_vault_url:
        return TestConnectionResult(
            status="not_tested",
            latency_ms=0,
            detail="KEY_VAULT_URL unset — EnvVarProvider fallback (ADR-0026)",
        )
    if not settings.key_vault_url.startswith("https://"):
        return TestConnectionResult(
            status="degraded", latency_ms=0, detail="KEY_VAULT_URL should be HTTPS"
        )
    return TestConnectionResult(
        status="ok",
        latency_ms=0,
        detail="KEY_VAULT_URL configured (Wave B+ adds list-secrets ping)",
    )


def _probe_acs_email(cfg: ProviderConfig, settings: Settings) -> TestConnectionResult:
    # ACS doesn't have an endpoint_url — secret_kv_ref points at the connection string.
    if not cfg.secret_kv_ref:
        return TestConnectionResult(
            status="not_tested",
            latency_ms=0,
            detail="ACS connection string not configured (feature_email_mock=true fallback)",
        )
    return TestConnectionResult(
        status="ok",
        latency_ms=0,
        detail="ACS connection string ref configured (Wave B+ adds ACS health ping)",
    )


def _probe_structlog(cfg: ProviderConfig) -> TestConnectionResult:
    # structlog is config-only — JSON shipping is always on, no probe needed.
    return TestConnectionResult(
        status="ok", latency_ms=0, detail="structlog JSON shipping always on"
    )


def _run_probe(
    cfg: ProviderConfig, settings: Settings
) -> TestConnectionResult:
    """Dispatch by provider_id. Times the probe so the UI shows latency_ms."""
    start = time.monotonic()
    if cfg.provider_id == "azure_openai":
        result = _probe_https_endpoint(cfg)
    elif cfg.provider_id == "cohere":
        result = _probe_https_endpoint(cfg)
    elif cfg.provider_id == "azure_search":
        result = _probe_https_endpoint(cfg)
    elif cfg.provider_id == "azure_blob":
        result = _probe_https_endpoint(cfg, allow_http_local=True)
    elif cfg.provider_id == "postgres":
        result = _probe_postgres(cfg, settings)
    elif cfg.provider_id == "langfuse":
        result = _probe_https_endpoint(cfg, allow_http_local=True)
    elif cfg.provider_id == "acs_email":
        result = _probe_acs_email(cfg, settings)
    elif cfg.provider_id == "key_vault":
        result = _probe_key_vault(cfg, settings)
    elif cfg.provider_id == "structlog":
        result = _probe_structlog(cfg)
    else:
        result = TestConnectionResult(
            status="error",
            latency_ms=0,
            detail=f"no probe registered for provider {cfg.provider_id!r}",
        )
    elapsed_ms = int((time.monotonic() - start) * 1000)
    # Preserve any internal latency the probe recorded; otherwise use the elapsed dispatch time.
    if result.latency_ms is None or result.latency_ms == 0:
        result = result.model_copy(update={"latency_ms": elapsed_ms})
    return result


# ---------- Endpoints --------------------------------------------------------


@router.get("", response_model=list[ProviderSummary])
async def list_connections(request: Request) -> list[ProviderSummary]:
    backend = _get_backend(request)
    configs = await backend.list_all()
    return [
        ProviderSummary(
            provider_id=c.provider_id,
            category=c.category,
            display_name=c.display_name,
            last_test_at=c.last_test_at,
            last_test_status=c.last_test_status,
        )
        for c in configs
    ]


@router.get("/{provider_id}", response_model=ProviderConfig)
async def get_connection(provider_id: str, request: Request) -> ProviderConfig:
    backend = _get_backend(request)
    try:
        return await backend.get(provider_id)
    except ProviderNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.patch("/{provider_id}", response_model=ProviderConfig)
async def update_connection(
    provider_id: str, patch: ProviderPatch, request: Request
) -> ProviderConfig:
    backend = _get_backend(request)
    try:
        return await backend.update(provider_id, patch)
    except ProviderNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post("/{provider_id}/test", response_model=TestConnectionResult)
async def test_connection(provider_id: str, request: Request) -> TestConnectionResult:
    backend = _get_backend(request)
    settings = get_settings()
    try:
        cfg = await backend.get(provider_id)
    except ProviderNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    result = _run_probe(cfg, settings)
    # Cast to satisfy mypy on the Literal["ok","degraded","error","not_tested"] arg.
    test_status: TestStatus = result.status
    await backend.update_test_result(
        provider_id,
        status=test_status,
        detail=result.detail,
        tested_at=datetime.now(timezone.utc),
    )
    return result


@router.post("/{provider_id}/rotate-secret", response_model=RotateSecretResult)
async def rotate_secret(provider_id: str, request: Request) -> RotateSecretResult:
    backend = _get_backend(request)
    kv = _get_key_vault(request)
    try:
        cfg = await backend.get(provider_id)
    except ProviderNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    if cfg.secret_kv_ref is None:
        # Managed-identity providers (key_vault, container_apps) + structlog have
        # no rotatable secret. UI surfaces a <DisabledAffordance> on the Rotate
        # button — this is the server-side guard for direct API hits.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"provider {provider_id!r} has no rotatable secret "
                "(managed-identity or config-only)"
            ),
        )
    try:
        new_value = await kv.rotate_secret(cfg.secret_kv_ref)
    except NotImplementedError as e:
        # EnvVarProvider hit — surface the actionable reason to the UI.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        ) from e
    except SecretNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    rotated_at = datetime.now(timezone.utc)
    masked = _mask_secret(new_value)
    await backend.update_rotation_timestamp(
        provider_id, rotated_at=rotated_at, secret_masked_preview=masked
    )
    return RotateSecretResult(
        provider_id=provider_id,
        last_rotated_at=rotated_at,
        secret_masked_preview=masked,
    )
