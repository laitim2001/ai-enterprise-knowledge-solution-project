"""Admin identity & auth config storage — Protocol + InMemory impl + 5 sub-resource seed.

W24-wave-c1 F3 per ADR-0026 Option B. Mirrors the `admin_provider_storage`
3-file Protocol + lazy-import shape (F2 precedent):

- `AdminIdentityConfigBackend` Protocol lives here
- `InMemoryAdminIdentityBackend` lives here (install-free, restart-wipes)
- `PostgresAdminIdentityBackend` in `admin_identity_postgres.py` (lazy-imported)

The 5 seeded sub-resources map onto the Identity & Auth tab mockup cards:
tenant + app_registration + msal + roles + policy.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol, runtime_checkable

from api.schemas.admin_identity import (
    AppRegistrationConfig,
    EntraTenantConfig,
    IdentityConfig,
    MsalConfig,
    RoleMapping,
    RoleMappingConfig,
    SignInPolicyConfig,
)


class IdentitySubResourceNotFoundError(Exception):
    """Raised when a sub_resource key is unknown (outside the 5-element enum)."""


# Tier 1 sub-resource keys — single source of truth for routes + storage.
SUB_RESOURCES = ("tenant", "app_registration", "msal", "roles", "policy")


def _now() -> datetime:
    return datetime.now(UTC)


# ---------- Default seed ----------------------------------------------------


def default_tenant() -> EntraTenantConfig:
    return EntraTenantConfig(
        tenant_id="00000000-0000-0000-0000-000000000000",
        tenant_domain="ricoh.onmicrosoft.com",
        cloud_instance="azure_public",
    )


def default_app_registration() -> AppRegistrationConfig:
    return AppRegistrationConfig(
        client_id="00000000-0000-0000-0000-000000000000",
        client_secret_kv_ref="ekp-entra-client-secret",
        redirect_uris=[
            "https://ekp-beta.ricoh.com/auth/callback",
            "http://localhost:3001/auth/callback",
        ],
        scopes=["User.Read", "openid", "profile", "email", "offline_access"],
        sign_in_audience="single",
    )


def default_msal() -> MsalConfig:
    return MsalConfig()


def default_roles() -> RoleMappingConfig:
    return RoleMappingConfig(
        mappings=[
            RoleMapping(
                ekp_role="admin",
                entra_group_name="grp-ekp-admins",
                entra_group_id="00000000-0000-0000-0000-000000000001",
            ),
            RoleMapping(
                ekp_role="editor",
                entra_group_name="grp-ekp-editors",
                entra_group_id="00000000-0000-0000-0000-000000000002",
            ),
            RoleMapping(
                ekp_role="user",
                entra_group_name="grp-ekp-users",
                entra_group_id="00000000-0000-0000-0000-000000000003",
            ),
            RoleMapping(
                ekp_role="power",
                entra_group_name="",
                entra_group_id="",
                is_tier2_disabled=True,
                tier2_reason=(
                    "Power User role available post-W12 (advanced retrieval tuning "
                    "+ model picker per ADR-0024 future evolution)"
                ),
            ),
        ]
    )


def default_policy() -> SignInPolicyConfig:
    return SignInPolicyConfig(
        allowed_email_domains=["@ricoh.com", "@ricoh.co.jp"],
        require_mfa_workspace_admin=True,
        auto_disable_after_days=90,
    )


def default_identity_config() -> IdentityConfig:
    """Return the 5-sub-resource seed (used by InMemory init + Postgres idempotent seed)."""
    return IdentityConfig(
        tenant=default_tenant(),
        app_registration=default_app_registration(),
        msal=default_msal(),
        roles=default_roles(),
        policy=default_policy(),
        updated_at=_now(),
    )


# ---------- Protocol --------------------------------------------------------


@runtime_checkable
class AdminIdentityConfigBackend(Protocol):
    """Admin identity config CRUD. Sub-resource granularity for PATCH."""

    async def get_all(self) -> IdentityConfig: ...

    async def update_tenant(self, value: EntraTenantConfig) -> EntraTenantConfig: ...

    async def update_app_registration(
        self, value: AppRegistrationConfig
    ) -> AppRegistrationConfig: ...

    async def update_msal(self, value: MsalConfig) -> MsalConfig: ...

    async def update_roles(self, value: RoleMappingConfig) -> RoleMappingConfig: ...

    async def update_policy(self, value: SignInPolicyConfig) -> SignInPolicyConfig: ...


# ---------- InMemory impl ---------------------------------------------------


class InMemoryAdminIdentityBackend:
    """Process-local identity config store seeded with the 5 defaults."""

    def __init__(self) -> None:
        self._cfg: IdentityConfig = default_identity_config()

    async def get_all(self) -> IdentityConfig:
        # Re-derive `authority_url` on every GET — it's never persisted (per F3 schema docstring).
        tenant = self._cfg.tenant.model_copy(
            update={"authority_url": _derive_authority_url(self._cfg.tenant)}
        )
        return self._cfg.model_copy(update={"tenant": tenant})

    async def update_tenant(self, value: EntraTenantConfig) -> EntraTenantConfig:
        # Strip any client-supplied authority_url — server derives it.
        clean = value.model_copy(update={"authority_url": None})
        self._cfg = self._cfg.model_copy(update={"tenant": clean, "updated_at": _now()})
        return self._cfg.tenant.model_copy(update={"authority_url": _derive_authority_url(clean)})

    async def update_app_registration(
        self, value: AppRegistrationConfig
    ) -> AppRegistrationConfig:
        self._cfg = self._cfg.model_copy(update={"app_registration": value, "updated_at": _now()})
        return self._cfg.app_registration

    async def update_msal(self, value: MsalConfig) -> MsalConfig:
        self._cfg = self._cfg.model_copy(update={"msal": value, "updated_at": _now()})
        return self._cfg.msal

    async def update_roles(self, value: RoleMappingConfig) -> RoleMappingConfig:
        self._cfg = self._cfg.model_copy(update={"roles": value, "updated_at": _now()})
        return self._cfg.roles

    async def update_policy(self, value: SignInPolicyConfig) -> SignInPolicyConfig:
        self._cfg = self._cfg.model_copy(update={"policy": value, "updated_at": _now()})
        return self._cfg.policy


def _derive_authority_url(tenant: EntraTenantConfig) -> str:
    """Build the public Entra authority URL from cloud instance + tenant_id."""
    base = {
        "azure_public": "https://login.microsoftonline.com",
        "azure_government": "https://login.microsoftonline.us",
        "azure_china_21vianet": "https://login.partner.microsoftonline.cn",
    }[tenant.cloud_instance]
    return f"{base}/{tenant.tenant_id}"
