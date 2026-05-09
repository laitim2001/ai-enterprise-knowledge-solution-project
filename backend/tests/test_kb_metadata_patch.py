"""KB metadata PATCH endpoint tests (W16 F5.2 CO_F3b closure).

Per W16 plan F5.2 acceptance criteria + CLAUDE.md §5.6 H6 + Decision A.1
(NEW endpoint PATCH /kb/{kb_id};separate from PATCH /kb/{kb_id}/settings).

Coverage:
- Happy path: both name + description PATCH
- Partial PATCH: name only / description only (omitted fields preserve)
- Empty body: no-op (returns current state)
- KB not found: 404
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
    await service.create(KbCreate(
        kb_id="drive_user_manuals",
        name="Drive Project — User Manuals",
        description="D365 F&O ERP user manuals",
        config=KbConfig(),
    ))
    return service


@pytest.fixture
async def kb_service_empty() -> KBService:
    return KBService(InMemoryKBBackend())


@pytest.mark.asyncio
async def test_patch_kb_metadata_both_fields(kb_service_with_drive: KBService) -> None:
    """PATCH with both name + description → both updated."""
    app = _build_app(kb_service_with_drive)
    client = TestClient(app)

    resp = client.patch(
        "/kb/drive_user_manuals",
        json={"name": "Drive — Renamed", "description": "Updated desc"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["kb_id"] == "drive_user_manuals"
    assert body["name"] == "Drive — Renamed"
    assert body["description"] == "Updated desc"


@pytest.mark.asyncio
async def test_patch_kb_metadata_name_only(kb_service_with_drive: KBService) -> None:
    """PATCH with only name → description preserved (true partial semantics)."""
    app = _build_app(kb_service_with_drive)
    client = TestClient(app)

    resp = client.patch(
        "/kb/drive_user_manuals",
        json={"name": "Drive — New Name"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["name"] == "Drive — New Name"
    assert body["description"] == "D365 F&O ERP user manuals"  # preserved


@pytest.mark.asyncio
async def test_patch_kb_metadata_description_only(kb_service_with_drive: KBService) -> None:
    """PATCH with only description → name preserved."""
    app = _build_app(kb_service_with_drive)
    client = TestClient(app)

    resp = client.patch(
        "/kb/drive_user_manuals",
        json={"description": "Just description update"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["name"] == "Drive Project — User Manuals"  # preserved
    assert body["description"] == "Just description update"


@pytest.mark.asyncio
async def test_patch_kb_metadata_empty_body_is_noop(
    kb_service_with_drive: KBService,
) -> None:
    """PATCH with empty body {} → no-op, returns current state unchanged."""
    app = _build_app(kb_service_with_drive)
    client = TestClient(app)

    resp = client.patch("/kb/drive_user_manuals", json={})
    assert resp.status_code == 200
    body = resp.json()
    assert body["name"] == "Drive Project — User Manuals"
    assert body["description"] == "D365 F&O ERP user manuals"


@pytest.mark.asyncio
async def test_patch_kb_metadata_kb_not_found(kb_service_empty: KBService) -> None:
    """Unknown kb_id → 404."""
    app = _build_app(kb_service_empty)
    client = TestClient(app)

    resp = client.patch(
        "/kb/nonexistent_kb",
        json={"name": "x"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_patch_kb_settings_unchanged_by_metadata_patch(
    kb_service_with_drive: KBService,
) -> None:
    """Per Decision A.1 separation of concern: PATCH /kb/{id} does NOT touch
    KbConfig. /settings endpoint still works for config changes independently."""
    app = _build_app(kb_service_with_drive)
    client = TestClient(app)

    # First patch metadata
    resp = client.patch(
        "/kb/drive_user_manuals",
        json={"name": "X"},
    )
    assert resp.status_code == 200
    config_before = resp.json()["config"]

    # Then patch settings — config changes; metadata preserved
    new_config = {
        "embedding_model": "text-embedding-3-large",
        "embedding_dimension": 1024,
        "chunk_strategy": "layout_aware",
        "default_top_k": 100,
        "default_rerank_k": 10,
    }
    resp2 = client.patch("/kb/drive_user_manuals/settings", json=new_config)
    assert resp2.status_code == 200
    assert resp2.json()["default_top_k"] == 100  # config changed

    # Re-fetch full status — name preserved from metadata patch
    resp3 = client.get("/kb/drive_user_manuals")
    assert resp3.status_code == 200
    assert resp3.json()["name"] == "X"  # metadata preserved
    assert resp3.json()["config"]["default_top_k"] == 100  # settings changed
    assert config_before["default_top_k"] == 50  # default before settings patch
