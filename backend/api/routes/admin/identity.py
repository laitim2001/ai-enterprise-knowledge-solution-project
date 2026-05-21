"""`/admin/identity/*` — 5 sub-resource CRUD (W24-wave-c1 F3 per ADR-0026 Option B).

5 endpoints surfaceable by the `/settings` Identity & Auth tab (per
`references/design-mockups/ekp-page-settings-tabs.jsx:528-723 SettingsIdentity`):

- `GET    /admin/identity`                     → IdentityConfig (5 sub-resources)
- `PATCH  /admin/identity/tenant`              → EntraTenantConfig
- `PATCH  /admin/identity/app_registration`    → AppRegistrationConfig
- `PATCH  /admin/identity/msal`                → MsalConfig
- `PATCH  /admin/identity/roles`               → RoleMappingConfig (list-replace)
- `PATCH  /admin/identity/policy`              → SignInPolicyConfig

**Roles PATCH semantic** = full list replace (`RoleMappingConfig.mappings`).
Individual mapping CRUD is Wave C2 + ADR-0027 RBAC infra; Tier 1 ships
read-mostly with 3 active + 1 Tier 2 disabled affordance (Power User).

**Tier 2 boundary enforcement** at PATCH:

- `tenant.cloud_instance` — Literal validates against 3 enums (no Tier 2 expand)
- `app_registration.sign_in_audience` — `"multi_disabled"` rejected via 422
- `msal.token_cache_strategy` — `"distributed_disabled"` rejected via 422
- `roles.mappings[*].ekp_role == "power"` — rejected unless `is_tier2_disabled=True`
- `policy.require_mfa_all_roles_tier2` — Literal[False] permanent

**Authority URL** is derived server-side from `tenant_id + cloud_instance`;
client-supplied values are silently stripped (`authority_url` is None on PATCH +
re-computed on GET).
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, status

from api.schemas.admin_identity import (
    AppRegistrationConfig,
    EntraTenantConfig,
    IdentityConfig,
    MsalConfig,
    RoleMappingConfig,
    SignInPolicyConfig,
)
from storage.admin_identity_storage import AdminIdentityConfigBackend
from storage.audit_log_storage import AuditLogBackend

router = APIRouter(prefix="/admin/identity")


def _get_backend(request: Request) -> AdminIdentityConfigBackend:
    backend = getattr(request.app.state, "admin_identity_backend", None)
    if backend is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="admin_identity_backend not initialized — check lifespan logs",
        )
    return backend  # type: ignore[no-any-return]


def _get_audit_log(request: Request) -> AuditLogBackend | None:
    """Audit log is optional — endpoint stays usable when unwired (F3 tests pass)."""
    return getattr(request.app.state, "audit_log_backend", None)


async def _audit_identity_patch(
    request: Request, sub_resource: str, payload: dict[str, object]
) -> None:
    audit = _get_audit_log(request)
    if audit is None:
        return
    await audit.append(
        actor=None,
        action="identity_patch",
        resource=f"admin_identity_config/{sub_resource}",
        payload=payload,
    )


# ---------- Tier 2 boundary guards (per CLAUDE.md H4) ----------------------


def _reject_tier2_app_registration(value: AppRegistrationConfig) -> None:
    if value.sign_in_audience == "multi_disabled":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="multi-tenant sign-in audience is Tier 2 (per CLAUDE.md H4)",
        )


def _reject_tier2_msal(value: MsalConfig) -> None:
    if value.token_cache_strategy == "distributed_disabled":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="distributed Redis token cache is Tier 2 (per CLAUDE.md H4)",
        )


def _reject_tier2_roles(value: RoleMappingConfig) -> None:
    for row in value.mappings:
        if row.ekp_role == "power" and not row.is_tier2_disabled:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    "power role must have is_tier2_disabled=True "
                    "(Power User is Tier 2 per CLAUDE.md H4)"
                ),
            )


# ---------- Endpoints --------------------------------------------------------


@router.get("", response_model=IdentityConfig)
async def get_identity(request: Request) -> IdentityConfig:
    backend = _get_backend(request)
    return await backend.get_all()


@router.patch("/tenant", response_model=EntraTenantConfig)
async def patch_tenant(value: EntraTenantConfig, request: Request) -> EntraTenantConfig:
    backend = _get_backend(request)
    result = await backend.update_tenant(value)
    await _audit_identity_patch(
        request, "tenant", value.model_dump(mode="json", exclude={"authority_url"})
    )
    return result


@router.patch("/app_registration", response_model=AppRegistrationConfig)
async def patch_app_registration(
    value: AppRegistrationConfig, request: Request
) -> AppRegistrationConfig:
    _reject_tier2_app_registration(value)
    backend = _get_backend(request)
    result = await backend.update_app_registration(value)
    # `client_secret_masked_preview` is the only secret-adjacent field — never log
    # the kv_ref value itself (only the name).
    await _audit_identity_patch(request, "app_registration", value.model_dump(mode="json"))
    return result


@router.patch("/msal", response_model=MsalConfig)
async def patch_msal(value: MsalConfig, request: Request) -> MsalConfig:
    _reject_tier2_msal(value)
    backend = _get_backend(request)
    result = await backend.update_msal(value)
    await _audit_identity_patch(request, "msal", value.model_dump(mode="json"))
    return result


@router.patch("/roles", response_model=RoleMappingConfig)
async def patch_roles(value: RoleMappingConfig, request: Request) -> RoleMappingConfig:
    _reject_tier2_roles(value)
    backend = _get_backend(request)
    result = await backend.update_roles(value)
    await _audit_identity_patch(request, "roles", value.model_dump(mode="json"))
    return result


@router.patch("/policy", response_model=SignInPolicyConfig)
async def patch_policy(value: SignInPolicyConfig, request: Request) -> SignInPolicyConfig:
    backend = _get_backend(request)
    result = await backend.update_policy(value)
    await _audit_identity_patch(request, "policy", value.model_dump(mode="json"))
    return result
