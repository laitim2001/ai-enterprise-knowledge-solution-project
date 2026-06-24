"""KB management route RBAC guard tests (W88 P0 F5 per ADR-0027 Option A).

Covers F5 — every *write* endpoint in `api/routes/kb.py` is now gated, mirroring
the canonical workspace permission matrix (`storage/rbac_storage.py`):
- POST /kb                          → require_role("admin","editor")   (kb.create)
- PATCH /kb/{id} + /settings        → require_kb_acl("edit")           (kb.edit_config)
- POST /kb/{id}/reindex + backfill  → require_kb_acl("edit")           (kb.trigger_reindex)
- DELETE /kb/{id} + archive         → require_kb_acl("manage")         (kb.delete)

A non-admin with no `kb_acl` grant is rejected (403); a workspace admin passes
unconditionally (admins clear `require_kb_acl` before the backend is read); an
editor with a sufficient grant passes. Read endpoints (GET /kb, GET /kb/{id})
stay ungated — list / retrieval-layer trimming is P2 (out of P0 scope).

Mock-auth drives the caller's role + oid; a fresh KB + RBAC backend per app.
"""

from __future__ import annotations

import asyncio

from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routes import documents as documents_routes
from api.routes import kb as kb_routes
from api.schemas.kb import KbConfig, KbCreate
from kb_management import KBService, get_kb_service
from kb_management.storage import InMemoryKBBackend
from storage.rbac_storage import InMemoryRbacBackend
from storage.settings import Settings, get_settings

_HEADERS = {"Authorization": "Bearer dev-token"}
_EXISTING_KB = "kb-1"


def _build_kb_service() -> KBService:
    service = KBService(InMemoryKBBackend())
    asyncio.run(
        service.create(
            KbCreate(kb_id=_EXISTING_KB, name="KB One", description="", config=KbConfig())
        )
    )
    return service


def _app(
    mock_role: str = "admin",
    *,
    oid: str = "caller-oid",
    rbac: InMemoryRbacBackend | None = None,
) -> FastAPI:
    """KB router app with mock-auth + a fresh KB/RBAC backend.

    `documents` router is included too so the reindex route's local import of
    `run_kb_reindex` resolves; the guard fires before any handler body, so the
    Azure-less app never reaches ingestion for the 403 cases.
    """
    app = FastAPI()
    app.include_router(kb_routes.router)
    app.include_router(documents_routes.router)
    app.dependency_overrides[get_kb_service] = lambda: _build_kb_service()
    app.state.rbac_backend = rbac if rbac is not None else InMemoryRbacBackend()
    # No index_populator → POST/DELETE /kb fail-soft (W16 F5.3 Decision B.1).
    app.state.index_populator = None
    app.dependency_overrides[get_settings] = lambda: Settings(
        feature_auth_mock=True, auth_mock_role=mock_role, auth_mock_oid=oid
    )
    return app


def _grant(rbac: InMemoryRbacBackend, oid: str, access_role: str) -> None:
    asyncio.run(
        rbac.add_kb_acl(
            kb_id=_EXISTING_KB,
            principal_type="user",
            principal_id=oid,
            access_role=access_role,
            granted_by="admin",
        )
    )


# ---- POST /kb — require_role("admin","editor") -----------------------------


def test_create_kb_admin_allowed() -> None:
    with TestClient(_app("admin")) as client:
        r = client.post(
            "/kb",
            json={"kb_id": "new-kb", "name": "New", "description": "", "config": {}},
            headers=_HEADERS,
        )
    assert r.status_code == 201, r.text


def test_create_kb_editor_allowed() -> None:
    """kb.create is granted to editor too (matrix: admin+editor)."""
    with TestClient(_app("editor")) as client:
        r = client.post(
            "/kb",
            json={"kb_id": "new-kb", "name": "New", "description": "", "config": {}},
            headers=_HEADERS,
        )
    assert r.status_code == 201, r.text


def test_create_kb_user_forbidden() -> None:
    """An end user cannot create a KB (matrix: kb.create = admin+editor only)."""
    with TestClient(_app("user")) as client:
        r = client.post(
            "/kb",
            json={"kb_id": "new-kb", "name": "New", "description": "", "config": {}},
            headers=_HEADERS,
        )
    assert r.status_code == 403


def test_create_kb_401_without_credentials() -> None:
    with TestClient(_app("admin")) as client:
        r = client.post(
            "/kb",
            json={"kb_id": "new-kb", "name": "New", "description": "", "config": {}},
        )
    assert r.status_code == 401


# ---- DELETE /kb/{id} + archive — require_kb_acl("manage") -------------------


def test_delete_kb_admin_allowed() -> None:
    with TestClient(_app("admin")) as client:
        r = client.delete(f"/kb/{_EXISTING_KB}", headers=_HEADERS)
    assert r.status_code == 204, r.text


def test_delete_kb_editor_without_grant_forbidden() -> None:
    with TestClient(_app("editor")) as client:
        r = client.delete(f"/kb/{_EXISTING_KB}", headers=_HEADERS)
    assert r.status_code == 403


def test_delete_kb_editor_with_edit_grant_still_forbidden() -> None:
    """edit < manage — an edit grant does not satisfy DELETE's manage gate."""
    rbac = InMemoryRbacBackend()
    _grant(rbac, "editor-oid", "edit")
    with TestClient(_app("editor", oid="editor-oid", rbac=rbac)) as client:
        r = client.delete(f"/kb/{_EXISTING_KB}", headers=_HEADERS)
    assert r.status_code == 403


def test_delete_kb_editor_with_manage_grant_allowed() -> None:
    rbac = InMemoryRbacBackend()
    _grant(rbac, "editor-oid", "manage")
    with TestClient(_app("editor", oid="editor-oid", rbac=rbac)) as client:
        r = client.delete(f"/kb/{_EXISTING_KB}", headers=_HEADERS)
    assert r.status_code == 204, r.text


def test_archive_editor_without_grant_forbidden() -> None:
    with TestClient(_app("editor")) as client:
        r = client.post(f"/kb/{_EXISTING_KB}/archive", headers=_HEADERS)
    assert r.status_code == 403


# ---- PATCH /kb/{id} + /settings — require_kb_acl("edit") -------------------


def test_settings_patch_editor_without_grant_forbidden() -> None:
    with TestClient(_app("editor")) as client:
        r = client.patch(f"/kb/{_EXISTING_KB}/settings", json={}, headers=_HEADERS)
    assert r.status_code == 403


def test_settings_patch_editor_with_edit_grant_allowed() -> None:
    rbac = InMemoryRbacBackend()
    _grant(rbac, "editor-oid", "edit")
    with TestClient(_app("editor", oid="editor-oid", rbac=rbac)) as client:
        r = client.patch(f"/kb/{_EXISTING_KB}/settings", json={}, headers=_HEADERS)
    assert r.status_code == 200, r.text


def test_metadata_patch_editor_without_grant_forbidden() -> None:
    with TestClient(_app("editor")) as client:
        r = client.patch(f"/kb/{_EXISTING_KB}", json={}, headers=_HEADERS)
    assert r.status_code == 403


def test_metadata_patch_admin_allowed() -> None:
    with TestClient(_app("admin")) as client:
        r = client.patch(
            f"/kb/{_EXISTING_KB}", json={"name": "Renamed"}, headers=_HEADERS
        )
    assert r.status_code == 200, r.text


# ---- POST /kb/{id}/reindex + backfill — require_kb_acl("edit") --------------


def test_reindex_editor_without_grant_forbidden() -> None:
    with TestClient(_app("editor")) as client:
        r = client.post(f"/kb/{_EXISTING_KB}/reindex", headers=_HEADERS)
    assert r.status_code == 403


def test_backfill_editor_without_grant_forbidden() -> None:
    with TestClient(_app("editor")) as client:
        r = client.post(f"/kb/{_EXISTING_KB}/profiles/backfill", headers=_HEADERS)
    assert r.status_code == 403


# ---- documents.py write endpoints — require_kb_acl("edit") (W88 P0 F5b) -----


def test_upload_document_editor_without_grant_forbidden() -> None:
    with TestClient(_app("editor")) as client:
        r = client.post(
            f"/kb/{_EXISTING_KB}/documents",
            files={"file": ("t.docx", b"x", "application/octet-stream")},
            headers=_HEADERS,
        )
    assert r.status_code == 403


def test_delete_document_editor_without_grant_forbidden() -> None:
    with TestClient(_app("editor")) as client:
        r = client.delete(f"/kb/{_EXISTING_KB}/documents/doc-1", headers=_HEADERS)
    assert r.status_code == 403


def test_reindex_document_editor_without_grant_forbidden() -> None:
    with TestClient(_app("editor")) as client:
        r = client.post(
            f"/kb/{_EXISTING_KB}/documents/doc-1/reindex",
            files={"file": ("t.docx", b"x", "application/octet-stream")},
            headers=_HEADERS,
        )
    assert r.status_code == 403


def test_override_profile_editor_without_grant_forbidden() -> None:
    with TestClient(_app("editor")) as client:
        r = client.put(
            f"/kb/{_EXISTING_KB}/docs/doc-1/profile",
            json={"profile": "P1_sop_imgdense"},
            headers=_HEADERS,
        )
    assert r.status_code == 403


def test_document_write_editor_with_edit_grant_clears_guard() -> None:
    """An edit grant clears the guard — the handler then resolves on its own
    (404/503, never 403). Proves the guard, not the handler."""
    rbac = InMemoryRbacBackend()
    _grant(rbac, "editor-oid", "edit")
    with TestClient(_app("editor", oid="editor-oid", rbac=rbac)) as client:
        r = client.delete(f"/kb/{_EXISTING_KB}/documents/doc-1", headers=_HEADERS)
    assert r.status_code != 403  # guard passed


# ---- Read endpoints stay ungated (P2 trimming, out of P0 scope) ------------


def test_get_kb_list_ungated() -> None:
    """GET /kb is not guarded — a plain user can list (read-trimming is P2)."""
    with TestClient(_app("user")) as client:
        r = client.get("/kb", headers=_HEADERS)
    assert r.status_code == 200
