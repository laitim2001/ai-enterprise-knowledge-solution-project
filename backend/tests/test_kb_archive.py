"""KB archive endpoint tests (W20 F5.1 — per ADR-0025 + plan checklist).

Coverage:
- Happy path: POST /kb/{id}/archive flips `archived=True`
- Idempotent: POST /kb/{id}/archive a second time still returns 200 + archived=True
- 404: POST /kb/{missing}/archive returns 404
- New KBs default to `archived=False`
- Service-level: `service.archive(kb_id, archived=False)` round-trip un-archives
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routes import kb as kb_routes
from api.schemas.kb import KbConfig, KbCreate
from kb_management import KBService, get_kb_service
from kb_management.storage import InMemoryKBBackend


def _build_app(kb_service: KBService) -> FastAPI:
    app = FastAPI()
    app.include_router(kb_routes.router)
    app.dependency_overrides[get_kb_service] = lambda: kb_service
    return app


@pytest.fixture
async def kb_service_with_drive() -> KBService:
    service = KBService(InMemoryKBBackend())
    await service.create(
        KbCreate(
            kb_id="drive_user_manuals",
            name="Drive Project — User Manuals",
            description="D365 F&O ERP user manuals",
            config=KbConfig(),
        ),
    )
    return service


@pytest.fixture
async def kb_service_empty() -> KBService:
    return KBService(InMemoryKBBackend())


@pytest.mark.asyncio
async def test_new_kb_defaults_to_not_archived(kb_service_with_drive: KBService) -> None:
    """New KBs land with `archived=False`."""
    app = _build_app(kb_service_with_drive)
    client = TestClient(app)

    resp = client.get("/kb/drive_user_manuals")
    assert resp.status_code == 200, resp.text
    assert resp.json()["archived"] is False


@pytest.mark.asyncio
async def test_archive_happy_path(kb_service_with_drive: KBService) -> None:
    """POST /kb/{id}/archive flips the flag and the GET reflects it."""
    app = _build_app(kb_service_with_drive)
    client = TestClient(app)

    archive_resp = client.post("/kb/drive_user_manuals/archive")
    assert archive_resp.status_code == 200, archive_resp.text
    body = archive_resp.json()
    assert body["archived"] is True
    assert body["kb_id"] == "drive_user_manuals"

    # GET reflects the change too.
    get_resp = client.get("/kb/drive_user_manuals")
    assert get_resp.json()["archived"] is True


@pytest.mark.asyncio
async def test_archive_idempotent(kb_service_with_drive: KBService) -> None:
    """POST /kb/{id}/archive twice in a row still 200 + archived=True (no error)."""
    app = _build_app(kb_service_with_drive)
    client = TestClient(app)

    first = client.post("/kb/drive_user_manuals/archive")
    second = client.post("/kb/drive_user_manuals/archive")
    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["archived"] is True


@pytest.mark.asyncio
async def test_archive_missing_kb_returns_404(kb_service_empty: KBService) -> None:
    """POST /kb/{missing}/archive → 404 with KBNotFoundError detail."""
    app = _build_app(kb_service_empty)
    client = TestClient(app)

    resp = client.post("/kb/does-not-exist/archive")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_service_archive_can_unarchive(kb_service_with_drive: KBService) -> None:
    """`service.archive(kb_id, archived=False)` is the un-archive path
    (route currently always archives;un-archive is a service-layer affordance
    for Wave B+ when a `PATCH /kb/{kb_id}` accepting `{archived: bool}` lands)."""
    archived = await kb_service_with_drive.archive("drive_user_manuals", archived=True)
    assert archived.archived is True

    unarchived = await kb_service_with_drive.archive("drive_user_manuals", archived=False)
    assert unarchived.archived is False
