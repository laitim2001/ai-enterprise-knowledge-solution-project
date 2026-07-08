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
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Request, status

from api.schemas.admin import (
    ProviderConfig,
    ProviderPatch,
    ProviderSummary,
    RotateSecretResult,
    SetSecretRequest,
    SetSecretResult,
    TestConnectionResult,
    TestStatus,
)
from storage.admin_provider_storage import (
    AdminProviderConfigBackend,
    ProviderNotFoundError,
)
from storage.audit_log_storage import AuditLogBackend
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


def _get_audit_log(request: Request) -> AuditLogBackend | None:
    """Audit log is optional — endpoint stays usable when unwired (F2 tests pass)."""
    return getattr(request.app.state, "audit_log_backend", None)


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


def _probe_sharepoint(cfg: ProviderConfig) -> TestConnectionResult:
    """SharePoint config-state probe (ADR-0072, Wave A). tenant_id / client_id live
    in settings; the secret is set iff a masked preview exists. Real Graph
    resolve-site verification is the wizard's Test connection (Wave B+ here)."""
    tenant = cfg.settings.get("tenant_id", "")
    client = cfg.settings.get("client_id", "")
    if not tenant or not client:
        return TestConnectionResult(
            status="not_tested",
            latency_ms=0,
            detail="tenant_id / client_id not configured (.env fallback may still apply)",
        )
    if not cfg.secret_masked_preview:
        return TestConnectionResult(
            status="degraded",
            latency_ms=0,
            detail="tenant / client set; client secret not stored — use set-secret",
        )
    return TestConnectionResult(
        status="ok",
        latency_ms=0,
        detail="config OK (tenant / client / secret set; Wave B+ adds Graph resolve-site ping)",
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
    elif cfg.provider_id == "sharepoint":
        result = _probe_sharepoint(cfg)
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
        updated = await backend.update(provider_id, patch)
    except ProviderNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    audit = _get_audit_log(request)
    if audit is not None:
        await audit.append(
            actor=None,
            action="connection_patch",
            resource=f"admin_provider_configs/{provider_id}",
            payload=patch.model_dump(exclude_unset=True),
        )
    return updated


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
        tested_at=datetime.now(UTC),
    )
    audit = _get_audit_log(request)
    if audit is not None:
        await audit.append(
            actor=None,
            action="connection_test",
            resource=f"admin_provider_configs/{provider_id}",
            payload={"status": test_status, "detail": result.detail},
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
    rotated_at = datetime.now(UTC)
    masked = _mask_secret(new_value)
    await backend.update_rotation_timestamp(
        provider_id, rotated_at=rotated_at, secret_masked_preview=masked
    )
    audit = _get_audit_log(request)
    if audit is not None:
        await audit.append(
            actor=None,
            action="connection_rotate_secret",
            resource=f"admin_provider_configs/{provider_id}",
            payload={"kv_ref": cfg.secret_kv_ref, "masked_preview": masked},
        )
    return RotateSecretResult(
        provider_id=provider_id,
        last_rotated_at=rotated_at,
        secret_masked_preview=masked,
    )


@router.post("/{provider_id}/set-secret", response_model=SetSecretResult)
async def set_secret(
    provider_id: str, body: SetSecretRequest, request: Request
) -> SetSecretResult:
    """Store a USER-supplied secret in Key Vault (ADR-0072).

    Unlike `rotate-secret` (which mints a value server-side), `set-secret` stores a
    value the admin provides — e.g. the SharePoint client secret Azure AD issued,
    which the app cannot generate. **H5**: `body.value` is written straight to Key
    Vault and is NEVER logged, returned, or persisted in plaintext; only the masked
    preview is recorded + returned. Errors deliberately omit the value + suppress
    the exception chain so no secret leaks via a traceback.
    """
    backend = _get_backend(request)
    kv = _get_key_vault(request)
    try:
        cfg = await backend.get(provider_id)
    except ProviderNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    if cfg.secret_kv_ref is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"provider {provider_id!r} has no secret slot (secret_kv_ref unset)",
        )
    try:
        await kv.set_secret(cfg.secret_kv_ref, body.value)
    except Exception as e:  # noqa: BLE001 — H5: never surface the value; drop the chain
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"failed to store secret for {provider_id!r} in Key Vault ({type(e).__name__})",
        ) from None
    updated_at = datetime.now(UTC)
    masked = _mask_secret(body.value)
    await backend.update_rotation_timestamp(
        provider_id, rotated_at=updated_at, secret_masked_preview=masked
    )
    audit = _get_audit_log(request)
    if audit is not None:
        await audit.append(
            actor=None,
            action="connection_set_secret",
            resource=f"admin_provider_configs/{provider_id}",
            payload={"kv_ref": cfg.secret_kv_ref, "masked_preview": masked},  # never the value (H5)
        )
    return SetSecretResult(
        provider_id=provider_id,
        secret_masked_preview=masked,
        updated_at=updated_at,
    )
