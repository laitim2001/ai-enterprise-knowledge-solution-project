"""`/admin/identity/*` route tests (W24-wave-c1 F3 per ADR-0026 Option B).

5 endpoints (1 GET + 5 PATCH sub-resources) + storage Protocol seed shape +
Tier 2 boundary guards (per CLAUDE.md H4). Mirrors F2 `test_admin_connections`
TestClient + InMemory backend wiring pattern.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routes.admin import identity as admin_identity
from api.schemas.admin_identity import IdentityConfig
from storage.admin_identity_storage import (
    SUB_RESOURCES,
    InMemoryAdminIdentityBackend,
    _derive_authority_url,
    default_identity_config,
    default_tenant,
)


def _build_app(*, backend: Any | None = None) -> FastAPI:
    """Minimal FastAPI with the admin identity router + state injected."""
    app = FastAPI()
    app.include_router(admin_identity.router)
    app.state.admin_identity_backend = backend
    return app


@pytest.fixture(autouse=True)
def _clean_settings_cache() -> Iterator[None]:
    from storage.settings import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


# --------------------------------------------------------------------------- #
# Storage Protocol seed shape
# --------------------------------------------------------------------------- #


def test_default_identity_config_has_five_sub_resources() -> None:
    cfg = default_identity_config()
    # Pydantic field set check — 5 sub-resources + updated_at.
    fields = set(cfg.model_dump().keys())
    assert {"tenant", "app_registration", "msal", "roles", "policy"}.issubset(fields)


def test_sub_resources_constant_matches_schema_fields() -> None:
    assert SUB_RESOURCES == ("tenant", "app_registration", "msal", "roles", "policy")


def test_default_roles_has_three_active_plus_power_user_disabled() -> None:
    roles = default_identity_config().roles.mappings
    assert len(roles) == 4
    active = [r for r in roles if not r.is_tier2_disabled]
    disabled = [r for r in roles if r.is_tier2_disabled]
    assert len(active) == 3
    assert len(disabled) == 1
    assert disabled[0].ekp_role == "power"
    assert disabled[0].tier2_reason is not None


def test_default_policy_has_allowed_ricoh_domains() -> None:
    policy = default_identity_config().policy
    assert "@ricoh.com" in policy.allowed_email_domains
    assert "@ricoh.co.jp" in policy.allowed_email_domains


def test_derive_authority_url_public_cloud() -> None:
    tenant = default_tenant()
    url = _derive_authority_url(tenant)
    assert url.startswith("https://login.microsoftonline.com/")
    assert tenant.tenant_id in url


def test_derive_authority_url_government_cloud() -> None:
    from api.schemas.admin_identity import EntraTenantConfig

    tenant = EntraTenantConfig(
        tenant_id="abc-tenant",
        tenant_domain="x.onmicrosoft.us",
        cloud_instance="azure_government",
    )
    assert _derive_authority_url(tenant) == "https://login.microsoftonline.us/abc-tenant"


def test_derive_authority_url_china_cloud() -> None:
    from api.schemas.admin_identity import EntraTenantConfig

    tenant = EntraTenantConfig(
        tenant_id="cn-tenant",
        tenant_domain="x.partner.onmschina.cn",
        cloud_instance="azure_china_21vianet",
    )
    assert _derive_authority_url(tenant) == "https://login.partner.microsoftonline.cn/cn-tenant"


@pytest.mark.asyncio
async def test_in_memory_backend_get_all_returns_seeded() -> None:
    backend = InMemoryAdminIdentityBackend()
    cfg = await backend.get_all()
    assert cfg.tenant.tenant_domain == "ricoh.onmicrosoft.com"
    # authority_url is derived per GET (not persisted).
    assert cfg.tenant.authority_url is not None
    assert "login.microsoftonline.com" in cfg.tenant.authority_url


@pytest.mark.asyncio
async def test_in_memory_backend_update_tenant_strips_client_authority_url() -> None:
    from api.schemas.admin_identity import EntraTenantConfig

    backend = InMemoryAdminIdentityBackend()
    # Client tries to inject a malicious authority_url.
    payload = EntraTenantConfig(
        tenant_id="new-tenant",
        tenant_domain="new.onmicrosoft.com",
        cloud_instance="azure_public",
        authority_url="https://evil.example/oauth",
    )
    result = await backend.update_tenant(payload)
    # Server-derived URL replaces the injected one.
    assert result.authority_url == "https://login.microsoftonline.com/new-tenant"


# --------------------------------------------------------------------------- #
# 503 lifespan guard
# --------------------------------------------------------------------------- #


def test_get_identity_503_when_backend_not_initialized() -> None:
    app = _build_app(backend=None)
    with TestClient(app) as client:
        r = client.get("/admin/identity")
        assert r.status_code == 503
        assert "admin_identity_backend not initialized" in r.json()["detail"]


# --------------------------------------------------------------------------- #
# GET /admin/identity
# --------------------------------------------------------------------------- #


def test_get_identity_returns_full_config() -> None:
    app = _build_app(backend=InMemoryAdminIdentityBackend())
    with TestClient(app) as client:
        r = client.get("/admin/identity")
        assert r.status_code == 200
        body = IdentityConfig(**r.json())
        assert body.tenant.tenant_domain == "ricoh.onmicrosoft.com"
        assert body.app_registration.client_secret_kv_ref == "ekp-entra-client-secret"
        assert body.msal.token_cache_strategy == "memory"
        assert len(body.roles.mappings) == 4
        assert body.policy.auto_disable_after_days == 90


def test_get_identity_authority_url_derived_each_get() -> None:
    app = _build_app(backend=InMemoryAdminIdentityBackend())
    with TestClient(app) as client:
        r1 = client.get("/admin/identity")
        r2 = client.get("/admin/identity")
        assert r1.json()["tenant"]["authority_url"] == r2.json()["tenant"]["authority_url"]
        assert r1.json()["tenant"]["authority_url"].startswith("https://login.microsoftonline.com/")


def test_get_identity_client_secret_value_never_returned() -> None:
    app = _build_app(backend=InMemoryAdminIdentityBackend())
    with TestClient(app) as client:
        r = client.get("/admin/identity")
        body = r.json()
        # Only the kv_ref name + masked preview surface — never a `client_secret` value field.
        assert "client_secret" not in body["app_registration"]
        assert "client_secret_kv_ref" in body["app_registration"]


# --------------------------------------------------------------------------- #
# PATCH /admin/identity/tenant
# --------------------------------------------------------------------------- #


def test_patch_tenant_updates_domain_and_recomputes_authority() -> None:
    app = _build_app(backend=InMemoryAdminIdentityBackend())
    with TestClient(app) as client:
        r = client.patch(
            "/admin/identity/tenant",
            json={
                "tenant_id": "updated-tenant",
                "tenant_domain": "updated.onmicrosoft.com",
                "cloud_instance": "azure_public",
            },
        )
        assert r.status_code == 200
        assert r.json()["tenant_domain"] == "updated.onmicrosoft.com"
        assert r.json()["authority_url"] == "https://login.microsoftonline.com/updated-tenant"


def test_patch_tenant_rejects_unknown_cloud_instance() -> None:
    app = _build_app(backend=InMemoryAdminIdentityBackend())
    with TestClient(app) as client:
        r = client.patch(
            "/admin/identity/tenant",
            json={
                "tenant_id": "x",
                "tenant_domain": "x.com",
                "cloud_instance": "azure_unknown",
            },
        )
        assert r.status_code == 422  # Pydantic Literal violation.


# --------------------------------------------------------------------------- #
# PATCH /admin/identity/app_registration
# --------------------------------------------------------------------------- #


def test_patch_app_registration_updates_redirect_uris() -> None:
    app = _build_app(backend=InMemoryAdminIdentityBackend())
    with TestClient(app) as client:
        r = client.patch(
            "/admin/identity/app_registration",
            json={
                "client_id": "new-client",
                "client_secret_kv_ref": "ekp-entra-client-secret",
                "redirect_uris": ["https://prod.ekp.ricoh.com/auth/callback"],
                "scopes": ["User.Read", "openid"],
                "sign_in_audience": "single",
            },
        )
        assert r.status_code == 200
        assert r.json()["redirect_uris"] == ["https://prod.ekp.ricoh.com/auth/callback"]
        assert r.json()["scopes"] == ["User.Read", "openid"]


def test_patch_app_registration_rejects_multi_tenant_audience() -> None:
    app = _build_app(backend=InMemoryAdminIdentityBackend())
    with TestClient(app) as client:
        r = client.patch(
            "/admin/identity/app_registration",
            json={
                "client_id": "x",
                "redirect_uris": [],
                "scopes": [],
                "sign_in_audience": "multi_disabled",
            },
        )
        assert r.status_code == 422
        assert "multi-tenant" in r.json()["detail"]


# --------------------------------------------------------------------------- #
# PATCH /admin/identity/msal
# --------------------------------------------------------------------------- #


def test_patch_msal_updates_ttl_and_rotation() -> None:
    app = _build_app(backend=InMemoryAdminIdentityBackend())
    with TestClient(app) as client:
        r = client.patch(
            "/admin/identity/msal",
            json={
                "token_cache_strategy": "memory",
                "session_ttl": "14d",
                "refresh_token_rotation": "12h",
                "csrf_token_rotation": "30m",
            },
        )
        assert r.status_code == 200
        assert r.json()["session_ttl"] == "14d"
        assert r.json()["refresh_token_rotation"] == "12h"


def test_patch_msal_rejects_distributed_token_cache() -> None:
    app = _build_app(backend=InMemoryAdminIdentityBackend())
    with TestClient(app) as client:
        r = client.patch(
            "/admin/identity/msal",
            json={"token_cache_strategy": "distributed_disabled"},
        )
        assert r.status_code == 422
        assert "distributed Redis" in r.json()["detail"]


# --------------------------------------------------------------------------- #
# PATCH /admin/identity/roles
# --------------------------------------------------------------------------- #


def test_patch_roles_replaces_mappings_list() -> None:
    app = _build_app(backend=InMemoryAdminIdentityBackend())
    with TestClient(app) as client:
        r = client.patch(
            "/admin/identity/roles",
            json={
                "mappings": [
                    {
                        "ekp_role": "admin",
                        "entra_group_name": "new-admin-group",
                        "entra_group_id": "new-admin-gid",
                    },
                ]
            },
        )
        assert r.status_code == 200
        assert len(r.json()["mappings"]) == 1
        assert r.json()["mappings"][0]["entra_group_name"] == "new-admin-group"


def test_patch_roles_rejects_active_power_user() -> None:
    app = _build_app(backend=InMemoryAdminIdentityBackend())
    with TestClient(app) as client:
        r = client.patch(
            "/admin/identity/roles",
            json={
                "mappings": [
                    {
                        "ekp_role": "power",
                        "entra_group_name": "grp-power",
                        "entra_group_id": "power-gid",
                        # is_tier2_disabled deliberately False (default).
                    },
                ]
            },
        )
        assert r.status_code == 422
        assert "power" in r.json()["detail"]


def test_patch_roles_accepts_power_user_when_explicitly_disabled() -> None:
    app = _build_app(backend=InMemoryAdminIdentityBackend())
    with TestClient(app) as client:
        r = client.patch(
            "/admin/identity/roles",
            json={
                "mappings": [
                    {
                        "ekp_role": "power",
                        "entra_group_name": "",
                        "entra_group_id": "",
                        "is_tier2_disabled": True,
                        "tier2_reason": "post-W12",
                    },
                ]
            },
        )
        assert r.status_code == 200


# --------------------------------------------------------------------------- #
# PATCH /admin/identity/policy
# --------------------------------------------------------------------------- #


def test_patch_policy_updates_allowed_domains_and_mfa() -> None:
    app = _build_app(backend=InMemoryAdminIdentityBackend())
    with TestClient(app) as client:
        r = client.patch(
            "/admin/identity/policy",
            json={
                "allowed_email_domains": ["@ricoh.com"],
                "require_mfa_workspace_admin": False,
                "require_mfa_all_roles_tier2": False,
                "auto_disable_after_days": 60,
            },
        )
        assert r.status_code == 200
        assert r.json()["allowed_email_domains"] == ["@ricoh.com"]
        assert r.json()["require_mfa_workspace_admin"] is False
        assert r.json()["auto_disable_after_days"] == 60


def test_patch_policy_rejects_mfa_all_roles_true_via_literal() -> None:
    """`require_mfa_all_roles_tier2` is Literal[False] — True triggers 422."""
    app = _build_app(backend=InMemoryAdminIdentityBackend())
    with TestClient(app) as client:
        r = client.patch(
            "/admin/identity/policy",
            json={
                "allowed_email_domains": [],
                "require_mfa_workspace_admin": False,
                "require_mfa_all_roles_tier2": True,
                "auto_disable_after_days": 0,
            },
        )
        assert r.status_code == 422


def test_patch_policy_rejects_negative_auto_disable_days() -> None:
    app = _build_app(backend=InMemoryAdminIdentityBackend())
    with TestClient(app) as client:
        r = client.patch(
            "/admin/identity/policy",
            json={
                "allowed_email_domains": [],
                "require_mfa_workspace_admin": False,
                "require_mfa_all_roles_tier2": False,
                "auto_disable_after_days": -1,
            },
        )
        assert r.status_code == 422


# --------------------------------------------------------------------------- #
# Cross-cutting — PATCH persistence visible on next GET
# --------------------------------------------------------------------------- #


def test_patch_msal_visible_on_next_get_identity() -> None:
    app = _build_app(backend=InMemoryAdminIdentityBackend())
    with TestClient(app) as client:
        client.patch("/admin/identity/msal", json={"session_ttl": "30d"})
        r = client.get("/admin/identity")
        assert r.json()["msal"]["session_ttl"] == "30d"
