"""`GET /admin/audit-log` route tests (W24-wave-c1 F5 backend hook).

Endpoint promoted from F4 deferral so `<SettingsAccount>` can surface the
last-10 audit rows. Hooks into existing `InMemoryAuditLogBackend`.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routes.admin import audit_log as admin_audit_log
from storage.audit_log_storage import InMemoryAuditLogBackend


def _build_app(*, backend: Any | None = None) -> FastAPI:
    app = FastAPI()
    app.include_router(admin_audit_log.router)
    app.state.audit_log_backend = backend
    return app


@pytest.fixture(autouse=True)
def _clean_settings_cache() -> Iterator[None]:
    from storage.settings import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_audit_log_503_when_backend_unwired() -> None:
    app = _build_app(backend=None)
    with TestClient(app) as client:
        r = client.get("/admin/audit-log")
        assert r.status_code == 503


def test_audit_log_returns_empty_list_when_no_writes() -> None:
    app = _build_app(backend=InMemoryAuditLogBackend())
    with TestClient(app) as client:
        r = client.get("/admin/audit-log")
        assert r.status_code == 200
        assert r.json() == []


def test_audit_log_returns_newest_first() -> None:
    import asyncio

    backend = InMemoryAuditLogBackend()
    for i in range(3):
        asyncio.run(
            backend.append(
                actor=None,
                action="connection_patch",
                resource=f"admin_provider_configs/p_{i}",
                payload={"i": i},
            )
        )
    app = _build_app(backend=backend)
    with TestClient(app) as client:
        r = client.get("/admin/audit-log")
        rows = r.json()
        assert len(rows) == 3
        assert rows[0]["resource"] == "admin_provider_configs/p_2"
        assert rows[-1]["resource"] == "admin_provider_configs/p_0"


def test_audit_log_respects_limit_query_param() -> None:
    import asyncio

    backend = InMemoryAuditLogBackend()
    for i in range(10):
        asyncio.run(
            backend.append(
                actor=None,
                action="identity_patch",
                resource=f"admin_identity_config/r_{i}",
                payload=None,
            )
        )
    app = _build_app(backend=backend)
    with TestClient(app) as client:
        r = client.get("/admin/audit-log?limit=3")
        assert r.status_code == 200
        assert len(r.json()) == 3


def test_audit_log_limit_validation_rejects_zero() -> None:
    app = _build_app(backend=InMemoryAuditLogBackend())
    with TestClient(app) as client:
        r = client.get("/admin/audit-log?limit=0")
        assert r.status_code == 422  # Query Field(ge=1)


def test_audit_log_limit_validation_rejects_above_200() -> None:
    app = _build_app(backend=InMemoryAuditLogBackend())
    with TestClient(app) as client:
        r = client.get("/admin/audit-log?limit=201")
        assert r.status_code == 422
