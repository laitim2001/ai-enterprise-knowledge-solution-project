"""Admin identity & auth configuration schemas (W24-wave-c1 F3 per ADR-0026 Option B).

5 sub-resources surfaceable by the `/settings` Identity & Auth tab (per
`references/design-mockups/ekp-page-settings-tabs.jsx:528-723 SettingsIdentity`):

  tenant            — Entra ID tenant + tenant domain + cloud instance
  app_registration  — Entra app reg: client_id + secret rotation hook +
                      redirect URIs + scopes + sign-in audience
  msal              — Session strategy: token cache + TTL + refresh + CSRF
  roles             — Entra security group → EKP role mapping (list)
  policy            — Self-register allowed domains + MFA + auto-disable

Persistence shape (per F3.9):

    admin_identity_config(
        sub_resource TEXT PK,  -- one of: tenant / app_registration / msal / roles / policy
        config       JSONB,
        updated_at   TIMESTAMPTZ,
        updated_by   TEXT NULL  -- audit_log preview; Wave C2 promotes ADR-0027
    )

`PATCH /admin/identity/roles` semantics = **list-replace** (full RoleMappingConfig
replacement); individual mapping CRUD is Wave C2 + ADR-0027 RBAC infra. Power
User row is permanently `is_tier2_disabled=True` (mockup line 684-687 `opacity:
0.5` precedent).
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from api.schemas.rbac import RoleKey

# Cloud instance enum (matches mockup line 562-564 select options).
CloudInstance = Literal["azure_public", "azure_government", "azure_china_21vianet"]

# Sign-in audience — multi-tenant Tier 2 boundary per CLAUDE.md H4.
SignInAudience = Literal["single", "multi_disabled"]

# MSAL token cache strategy — distributed Redis Tier 2 boundary.
TokenCacheStrategy = Literal["memory", "distributed_disabled"]

# ---------- Sub-resource configs --------------------------------------------


class EntraTenantConfig(BaseModel):
    """Entra ID tenant. `authority_url` is derived server-side from `tenant_id`."""

    tenant_id: str = Field(..., description="Entra tenant GUID, e.g. 'f8b1...2056'.")
    tenant_domain: str = Field(..., description="E.g. 'ricoh.onmicrosoft.com'.")
    cloud_instance: CloudInstance = "azure_public"
    authority_url: str | None = Field(
        default=None,
        description="Derived from tenant_id at GET — never persisted; ignored on PATCH.",
    )


class AppRegistrationConfig(BaseModel):
    """Entra enterprise app registration. `client_secret_kv_ref` rotates via F1 KeyVaultProvider."""

    client_id: str = Field(..., description="App (client) ID GUID.")
    client_secret_kv_ref: str | None = Field(
        default=None,
        description="Key Vault secret name (NOT the value). None = secret not yet provisioned.",
    )
    client_secret_masked_preview: str | None = Field(
        default=None, description="Masked preview hint, e.g. '***xY1z' — never the real value."
    )
    client_secret_expires_at: datetime | None = Field(
        default=None, description="Tracked for 90d rotation reminder UI (mockup line 585)."
    )
    redirect_uris: list[str] = Field(
        default_factory=list, description="OAuth callback URIs (web platform)."
    )
    scopes: list[str] = Field(
        default_factory=list,
        description="API permissions, e.g. ['User.Read','openid','profile','email','offline_access'].",
    )
    sign_in_audience: SignInAudience = "single"


class MsalConfig(BaseModel):
    """MSAL session + cookie settings per ADR-0022 auth-transport hardening."""

    token_cache_strategy: TokenCacheStrategy = "memory"
    session_ttl: str = Field(default="7d", description="Pretty-printed duration, e.g. '7d' or '24h'.")
    refresh_token_rotation: str = Field(default="24h")
    csrf_token_rotation: str = Field(default="1h")
    cookie_settings_preview: str = Field(
        default=(
            "Set-Cookie: ekp_session=…; HttpOnly; Secure; SameSite=Lax; "
            "Path=/; Max-Age=604800"
        ),
        description="Read-only server-computed preview (mockup line 643-645).",
    )


class RoleMapping(BaseModel):
    """Single Entra group → EKP role mapping row.

    `ekp_role` uses the RBAC core `RoleKey` vocabulary (W24c F3 — unified from
    the pre-RBAC long-form `EkpRoleKey`; mockup `ekp-page-users.jsx` is canonical).
    """

    ekp_role: RoleKey
    entra_group_name: str = Field(..., description="E.g. 'grp-ekp-admins'.")
    entra_group_id: str = Field(..., description="Entra security group GUID.")
    member_count: int | None = Field(
        default=None,
        description="Snapshot count; refreshed via Graph API in Wave C2 (None at Wave C1).",
    )
    is_tier2_disabled: bool = Field(
        default=False, description="True for the power role (mockup line 684-687 disabled affordance)."
    )
    tier2_reason: str | None = Field(
        default=None,
        description="Surfaced in UI when is_tier2_disabled=True. Per ADR-0027 Option B fallback.",
    )


class RoleMappingConfig(BaseModel):
    """List of RoleMapping rows. PATCH semantics = full list replace."""

    mappings: list[RoleMapping] = Field(default_factory=list)


class SignInPolicyConfig(BaseModel):
    """Self-register policy + MFA + auto-disable thresholds."""

    allowed_email_domains: list[str] = Field(
        default_factory=list, description="E.g. ['@ricoh.com', '@ricoh.co.jp']."
    )
    require_mfa_workspace_admin: bool = False
    require_mfa_all_roles_tier2: Literal[False] = Field(
        default=False, description="Permanent Tier 2 disabled affordance (mockup line 713-715)."
    )
    auto_disable_after_days: int = Field(default=90, ge=0, description="0 = never auto-disable.")


# ---------- Consolidated GET response --------------------------------------


class IdentityConfig(BaseModel):
    """`GET /admin/identity` consolidated response. client_secret value never present."""

    tenant: EntraTenantConfig
    app_registration: AppRegistrationConfig
    msal: MsalConfig
    roles: RoleMappingConfig
    policy: SignInPolicyConfig
    updated_at: datetime
