"""`/admin/api-keys/*` route tests (W24-wave-c1 F4 per ADR-0026 Option B).

3 endpoints:
  - GET   /admin/api-keys/outgoing (per-deployment quota + realtime usage rows)
  - PATCH /admin/api-keys/outgoing/{provider}/{deployment}/alert-threshold
  - GET   /admin/api-keys/incoming (Tier 2 disabled affordance)

Plus audit log write verification + threshold validation boundaries.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routes.admin import api_keys as admin_api_keys
from storage.admin_provider_storage import InMemoryAdminProviderBackend
from storage.audit_log_storage import InMemoryAuditLogBackend


def _build_app(
    *,
    provider_backend: Any | None = None,
    audit_log_backend: Any | None = None,
) -> FastAPI:
    app = FastAPI()
    app.include_router(admin_api_keys.router)
    app.state.admin_provider_backend = provider_backend
    app.state.audit_log_backend = audit_log_backend
    return app


@pytest.fixture(autouse=True)
def _clean_settings_cache() -> Iterator[None]:
    from storage.settings import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture(autouse=True)
def _stub_langfuse_client(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """All api-keys tests run without a real Langfuse — realtime status=no_client."""
    monkeypatch.setattr(
        "api.routes.admin.api_keys.get_langfuse_client", lambda: None
    )
    yield


# --------------------------------------------------------------------------- #
# GET /admin/api-keys/incoming — Tier 2 disabled affordance
# --------------------------------------------------------------------------- #


def test_get_incoming_returns_permanent_tier2_disabled() -> None:
    app = _build_app()
    with TestClient(app) as client:
        r = client.get("/admin/api-keys/incoming")
        assert r.status_code == 200
        body = r.json()
        assert body["enabled"] is False
        assert "Tier 2" in body["reason"]


# --------------------------------------------------------------------------- #
# GET /admin/api-keys/outgoing — per-deployment rows
# --------------------------------------------------------------------------- #


def test_get_outgoing_503_when_provider_backend_unwired() -> None:
    app = _build_app(provider_backend=None)
    with TestClient(app) as client:
        r = client.get("/admin/api-keys/outgoing")
        assert r.status_code == 503


def test_get_outgoing_returns_flattened_per_deployment_rows() -> None:
    app = _build_app(provider_backend=InMemoryAdminProviderBackend())
    with TestClient(app) as client:
        r = client.get("/admin/api-keys/outgoing")
        assert r.status_code == 200
        body = r.json()
        # 10 providers in seed, minus structlog + key_vault (skipped) = 8 providers
        # but azure_openai has 4 deployments → 4 rows from it
        # Total = 4 (azure_openai) + 1 each for cohere/azure_search/azure_blob/
        # postgres/langfuse/acs_email/sharepoint (W102/ADR-0072) = 11 rows
        assert len(body["rows"]) == 11


def test_get_outgoing_skips_structlog_and_key_vault() -> None:
    app = _build_app(provider_backend=InMemoryAdminProviderBackend())
    with TestClient(app) as client:
        r = client.get("/admin/api-keys/outgoing")
        provider_ids = {row["provider_id"] for row in r.json()["rows"]}
        assert "structlog" not in provider_ids
        assert "key_vault" not in provider_ids


def test_get_outgoing_azure_openai_emits_four_deployment_rows() -> None:
    app = _build_app(provider_backend=InMemoryAdminProviderBackend())
    with TestClient(app) as client:
        r = client.get("/admin/api-keys/outgoing")
        rows = [row for row in r.json()["rows"] if row["provider_id"] == "azure_openai"]
        assert len(rows) == 4
        deployment_ids = {row["deployment_id"] for row in rows}
        assert deployment_ids == {"embedding", "llm_primary", "llm_judge", "llm_eval_judge"}


def test_get_outgoing_acs_email_uses_emails_unit() -> None:
    app = _build_app(provider_backend=InMemoryAdminProviderBackend())
    with TestClient(app) as client:
        r = client.get("/admin/api-keys/outgoing")
        acs_rows = [row for row in r.json()["rows"] if row["provider_id"] == "acs_email"]
        assert len(acs_rows) == 1
        assert acs_rows[0]["quota_unit"] == "emails"


def test_get_outgoing_realtime_status_propagates() -> None:
    """Langfuse not wired → realtime_status='no_client' propagates to list response."""
    app = _build_app(provider_backend=InMemoryAdminProviderBackend())
    with TestClient(app) as client:
        r = client.get("/admin/api-keys/outgoing")
        assert r.json()["realtime_status"] == "no_client"


def test_get_outgoing_default_alert_threshold_80() -> None:
    """Fresh seed deployments default to 80% alert threshold per F4 schema."""
    app = _build_app(provider_backend=InMemoryAdminProviderBackend())
    with TestClient(app) as client:
        r = client.get("/admin/api-keys/outgoing")
        rows = r.json()["rows"]
        for row in rows:
            assert row["alert_threshold_pct"] == 80


# --------------------------------------------------------------------------- #
# PATCH /admin/api-keys/outgoing/{p}/{d}/alert-threshold
# --------------------------------------------------------------------------- #


def test_patch_alert_threshold_updates_value() -> None:
    backend = InMemoryAdminProviderBackend()
    app = _build_app(provider_backend=backend)
    with TestClient(app) as client:
        r = client.patch(
            "/admin/api-keys/outgoing/azure_openai/llm_primary/alert-threshold",
            json={"alert_threshold_pct": 90},
        )
        assert r.status_code == 200
        assert r.json()["alert_threshold_pct"] == 90


def test_patch_alert_threshold_persists_visible_on_next_get() -> None:
    backend = InMemoryAdminProviderBackend()
    app = _build_app(provider_backend=backend)
    with TestClient(app) as client:
        client.patch(
            "/admin/api-keys/outgoing/azure_openai/llm_primary/alert-threshold",
            json={"alert_threshold_pct": 65},
        )
        r = client.get("/admin/api-keys/outgoing")
        llm_primary_row = next(
            row for row in r.json()["rows"]
            if row["provider_id"] == "azure_openai" and row["deployment_id"] == "llm_primary"
        )
        assert llm_primary_row["alert_threshold_pct"] == 65


def test_patch_alert_threshold_rejects_below_50() -> None:
    app = _build_app(provider_backend=InMemoryAdminProviderBackend())
    with TestClient(app) as client:
        r = client.patch(
            "/admin/api-keys/outgoing/azure_openai/llm_primary/alert-threshold",
            json={"alert_threshold_pct": 49},
        )
        assert r.status_code == 422


def test_patch_alert_threshold_rejects_above_95() -> None:
    app = _build_app(provider_backend=InMemoryAdminProviderBackend())
    with TestClient(app) as client:
        r = client.patch(
            "/admin/api-keys/outgoing/azure_openai/llm_primary/alert-threshold",
            json={"alert_threshold_pct": 96},
        )
        assert r.status_code == 422


def test_patch_alert_threshold_404_when_unknown_provider() -> None:
    app = _build_app(provider_backend=InMemoryAdminProviderBackend())
    with TestClient(app) as client:
        r = client.patch(
            "/admin/api-keys/outgoing/unknown_provider/some_deployment/alert-threshold",
            json={"alert_threshold_pct": 80},
        )
        assert r.status_code == 404


def test_patch_alert_threshold_404_when_unknown_deployment() -> None:
    app = _build_app(provider_backend=InMemoryAdminProviderBackend())
    with TestClient(app) as client:
        r = client.patch(
            "/admin/api-keys/outgoing/azure_openai/nonexistent/alert-threshold",
            json={"alert_threshold_pct": 80},
        )
        assert r.status_code == 404


def test_patch_alert_threshold_writes_audit_log_when_backend_wired() -> None:
    provider_backend = InMemoryAdminProviderBackend()
    audit_backend = InMemoryAuditLogBackend()
    app = _build_app(provider_backend=provider_backend, audit_log_backend=audit_backend)
    with TestClient(app) as client:
        client.patch(
            "/admin/api-keys/outgoing/azure_openai/llm_primary/alert-threshold",
            json={"alert_threshold_pct": 75},
        )
    import asyncio

    rows = asyncio.run(audit_backend.list_recent())
    assert len(rows) == 1
    assert rows[0].action == "api_keys_alert_threshold_patch"
    assert rows[0].resource == "admin_provider_configs/azure_openai/llm_primary"
    assert rows[0].payload == {"alert_threshold_pct": 75}


def test_patch_alert_threshold_no_audit_log_when_backend_none() -> None:
    """Endpoint stays usable when audit_log_backend is None (F2/F3 test path)."""
    app = _build_app(
        provider_backend=InMemoryAdminProviderBackend(), audit_log_backend=None
    )
    with TestClient(app) as client:
        r = client.patch(
            "/admin/api-keys/outgoing/azure_openai/llm_primary/alert-threshold",
            json={"alert_threshold_pct": 70},
        )
        assert r.status_code == 200
