"""F6 — SharePoint import route + production ingest adapter (W100 / ADR-0070).

RBAC gating, not-configured handling, request validation, summary serialization,
and the adapter's doc-ACL-then-pipeline structure (mocked — the live path needs a
real tenant + Azure, D4, runbook §10).
"""

from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routes import integration as integration_routes
from integration.import_service import ImportSummary
from integration.models import SourceContainer, SourceDocumentRef
from kb_management import KBService, get_kb_service
from kb_management.doc_acl_store import InMemoryDocAclStore
from kb_management.storage import InMemoryKBBackend
from storage.rbac_storage import InMemoryRbacBackend
from storage.settings import Settings, get_settings

_HEADERS = {"Authorization": "Bearer dev-token"}
_KB = "kb-1"


def _app(
    mock_role: str = "admin",
    *,
    oid: str = "caller-oid",
    rbac: InMemoryRbacBackend | None = None,
    settings: Settings | None = None,
) -> FastAPI:
    app = FastAPI()
    app.include_router(integration_routes.router)
    app.dependency_overrides[get_kb_service] = lambda: KBService(InMemoryKBBackend())
    # Non-None ingestion deps so `_ingestion_deps_or_503` passes (the happy path
    # monkeypatches the connector/import so these sentinels are never invoked).
    app.state.embedder = object()
    app.state.index_populator = object()
    app.state.ingestion_chunker = object()
    app.state.doc_acl_store = InMemoryDocAclStore()
    app.state.rbac_backend = rbac if rbac is not None else InMemoryRbacBackend()
    app.dependency_overrides[get_settings] = lambda: settings or Settings(
        feature_auth_mock=True, auth_mock_role=mock_role, auth_mock_oid=oid
    )
    return app


def _grant(rbac: InMemoryRbacBackend, oid: str, access_role: str) -> None:
    asyncio.run(
        rbac.add_kb_acl(
            kb_id=_KB,
            principal_type="user",
            principal_id=oid,
            access_role=access_role,
            granted_by="admin",
        )
    )


def _body() -> dict:
    return {"kb_id": _KB, "container_ids": ["drive::D1"]}


# ---- RBAC ------------------------------------------------------------------


def test_import_user_role_forbidden() -> None:
    with TestClient(_app("user")) as client:
        r = client.post("/integration/sharepoint/import", json=_body(), headers=_HEADERS)
    assert r.status_code == 403  # require_role("admin","editor")


def test_import_401_without_credentials() -> None:
    with TestClient(_app("admin")) as client:
        r = client.post("/integration/sharepoint/import", json=_body())
    assert r.status_code == 401


def test_import_editor_without_kb_grant_forbidden() -> None:
    with TestClient(_app("editor", oid="editor-oid")) as client:
        r = client.post("/integration/sharepoint/import", json=_body(), headers=_HEADERS)
    assert r.status_code == 403  # passes require_role, fails per-KB assert_kb_access("edit")


def test_import_not_configured_503() -> None:
    # admin clears both guards; SharePoint creds empty → 503 not-configured.
    with TestClient(_app("admin")) as client:
        r = client.post("/integration/sharepoint/import", json=_body(), headers=_HEADERS)
    assert r.status_code == 503
    assert "not configured" in r.json()["detail"]


def test_import_validation_error_on_missing_fields() -> None:
    # Neither container_ids nor documents → 422 (in-route guard, #1 / D-3 — both fields
    # now optional but at least one must be non-empty).
    with TestClient(_app("admin")) as client:
        r = client.post("/integration/sharepoint/import", json={"kb_id": _KB}, headers=_HEADERS)
    assert r.status_code == 422


# ---- happy path (mocked connector + real import_documents) ------------------


class _FakeHandle:
    async def token(self) -> str:
        return "tok"

    async def aclose(self) -> None:
        return None


def test_import_happy_path_returns_summary(monkeypatch: pytest.MonkeyPatch) -> None:
    configured = Settings(
        feature_auth_mock=True,
        auth_mock_role="admin",
        sharepoint_tenant_id="T1",
        sharepoint_client_id="C1",
        sharepoint_client_secret="S1",
    )

    # Fake connector: connect/aclose only — import_documents is stubbed to a canned
    # summary so neither Graph nor ingestion is touched (D4).
    class _FakeConnector:
        def __init__(self, *args: object, **kwargs: object) -> None:
            pass

        async def connect(self) -> _FakeHandle:
            return _FakeHandle()

        async def aclose(self) -> None:
            return None

    async def _fake_import(connector, handle, *, kb_id, container_ids, ingest):  # noqa: ANN001
        return ImportSummary(results=[])

    monkeypatch.setattr(integration_routes, "SharePointConnector", _FakeConnector)
    monkeypatch.setattr(integration_routes, "import_documents", _fake_import)

    with TestClient(_app("admin", settings=configured)) as client:
        r = client.post("/integration/sharepoint/import", json=_body(), headers=_HEADERS)
    assert r.status_code == 200, r.text
    payload = r.json()
    assert payload == {"total": 0, "succeeded": 0, "failed": 0, "results": []}


# ---- production ingest adapter ---------------------------------------------


def test_adapter_writes_doc_acl_then_calls_pipeline(monkeypatch: pytest.MonkeyPatch) -> None:
    from api.routes.documents import _IngestionDeps

    acl = InMemoryDocAclStore()
    deps = _IngestionDeps(
        embedder=object(),  # type: ignore[arg-type]
        populator=object(),  # type: ignore[arg-type]
        chunker=object(),  # type: ignore[arg-type]
        doc_acl_store=acl,
    )
    calls: list[dict] = []

    async def _fake_pipeline(*, upload_file, kb_id, doc_id, deps, service, force_scan=False):  # noqa: ANN001
        calls.append({"kb_id": kb_id, "doc_id": doc_id, "filename": upload_file.filename})
        return {}

    monkeypatch.setattr(integration_routes, "_run_ingest_pipeline", _fake_pipeline)

    ingest = integration_routes.make_pipeline_ingest(deps, KBService(InMemoryKBBackend()))
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(b"bytes")
        path = Path(tmp.name)
    try:
        asyncio.run(
            ingest(
                content_path=path,
                name="guide.pdf",
                kb_id=_KB,
                doc_id="sp-I1",
                allowed_principals=["G1", "G2"],
                source_url="/guide.pdf",
            )
        )
    finally:
        path.unlink(missing_ok=True)

    rows = asyncio.run(acl.list_for_doc(_KB, "sp-I1"))
    assert {row.principal_id for row in rows} == {"G1", "G2"}  # source ACL persisted
    assert len(calls) == 1 and calls[0]["doc_id"] == "sp-I1"  # pipeline invoked


def test_adapter_refuses_without_doc_acl_store() -> None:
    from api.routes.documents import _IngestionDeps

    deps = _IngestionDeps(
        embedder=object(),  # type: ignore[arg-type]
        populator=object(),  # type: ignore[arg-type]
        chunker=object(),  # type: ignore[arg-type]
        doc_acl_store=None,
    )
    ingest = integration_routes.make_pipeline_ingest(deps, KBService(InMemoryKBBackend()))
    with pytest.raises(RuntimeError, match="doc_acl_store unwired"):
        asyncio.run(
            ingest(
                content_path=Path("/nonexistent"),
                name="x.pdf",
                kb_id=_KB,
                doc_id="d",
                allowed_principals=["G1"],
                source_url="/x",
            )
        )


# ---- browse / list / resolve endpoints (F1 — mocked connector) --------------


def _configured(role: str = "admin") -> Settings:
    return Settings(
        feature_auth_mock=True,
        auth_mock_role=role,
        sharepoint_tenant_id="T1",
        sharepoint_client_id="C1",
        sharepoint_client_secret="S1",
    )


class _FakeBrowseConnector:
    """connect/resolve/browse/list only — no Graph, no ingestion (D4)."""

    def __init__(self, *args: object, **kwargs: object) -> None:
        pass

    async def connect(self) -> _FakeHandle:
        return _FakeHandle()

    async def aclose(self) -> None:
        return None

    async def resolve_site(self, handle: object, hostname: str, site_path: str) -> SourceContainer:
        return SourceContainer(id="site::S1", name="Manuals", type="site")

    async def browse(self, handle: object, container_id: str | None = None):  # noqa: ANN201
        yield SourceContainer(
            id="drive::D1", name="Documents", type="library", parent_id=container_id
        )

    async def list_documents(self, handle: object, container_id: str):  # noqa: ANN201
        yield SourceDocumentRef(id="I1", name="a.pdf", path="/a.pdf", container_id=container_id)


def test_resolve_site_happy(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(integration_routes, "SharePointConnector", _FakeBrowseConnector)
    with TestClient(_app("admin", settings=_configured())) as client:
        r = client.post(
            "/integration/sharepoint/resolve-site",
            json={"site_url": "https://contoso.sharepoint.com/sites/manuals"},
            headers=_HEADERS,
        )
    assert r.status_code == 200, r.text
    assert r.json() == {"id": "site::S1", "name": "Manuals", "type": "site", "parent_id": None}


def test_resolve_site_invalid_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(integration_routes, "SharePointConnector", _FakeBrowseConnector)
    with TestClient(_app("admin", settings=_configured())) as client:
        r = client.post(
            "/integration/sharepoint/resolve-site",
            json={"site_url": "https://contoso.sharepoint.com"},  # no /sites/<name>
            headers=_HEADERS,
        )
    assert r.status_code == 422


def test_resolve_site_user_forbidden() -> None:
    with TestClient(_app("user")) as client:
        r = client.post(
            "/integration/sharepoint/resolve-site",
            json={"site_url": "https://c.sharepoint.com/sites/m"},
            headers=_HEADERS,
        )
    assert r.status_code == 403


def test_browse_happy(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(integration_routes, "SharePointConnector", _FakeBrowseConnector)
    with TestClient(_app("admin", settings=_configured())) as client:
        r = client.get(
            "/integration/sharepoint/browse",
            params={"container_id": "site::S1"},
            headers=_HEADERS,
        )
    assert r.status_code == 200, r.text
    assert r.json()["containers"][0]["id"] == "drive::D1"


def test_browse_user_forbidden() -> None:
    with TestClient(_app("user")) as client:
        r = client.get("/integration/sharepoint/browse", headers=_HEADERS)
    assert r.status_code == 403


def test_documents_happy(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(integration_routes, "SharePointConnector", _FakeBrowseConnector)
    with TestClient(_app("admin", settings=_configured())) as client:
        r = client.get(
            "/integration/sharepoint/documents",
            params={"container_id": "drive::D1"},
            headers=_HEADERS,
        )
    assert r.status_code == 200, r.text
    docs = r.json()["documents"]
    assert len(docs) == 1
    assert docs[0]["id"] == "I1" and docs[0]["container_id"] == "drive::D1"


def test_documents_requires_container_id() -> None:
    with TestClient(_app("admin", settings=_configured())) as client:
        r = client.get("/integration/sharepoint/documents", headers=_HEADERS)
    assert r.status_code == 422  # container_id is a required query param


def test_import_individual_documents_path(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(integration_routes, "SharePointConnector", _FakeBrowseConnector)
    captured: dict = {}

    async def _fake_selected(connector, handle, *, kb_id, refs, ingest):  # noqa: ANN001
        captured["kb_id"] = kb_id
        captured["refs"] = refs
        return ImportSummary(results=[])

    monkeypatch.setattr(integration_routes, "import_selected_documents", _fake_selected)
    body = {
        "kb_id": _KB,
        "documents": [{"id": "I1", "name": "a.pdf", "path": "/a.pdf", "container_id": "drive::D1"}],
    }
    with TestClient(_app("admin", settings=_configured())) as client:
        r = client.post("/integration/sharepoint/import", json=body, headers=_HEADERS)
    assert r.status_code == 200, r.text
    assert captured["kb_id"] == _KB
    assert len(captured["refs"]) == 1 and captured["refs"][0].id == "I1"
