"""F3 — SharePoint connector: connect / browse / list_documents / fetch_document.

MockTransport fakes Graph; a fake handle supplies the bearer (azure-identity never
touched, D4). Asserts tree navigation, file/folder split, change-detection fields,
and streamed fetch.
"""

from __future__ import annotations

from pathlib import Path

import httpx

from integration.models import SourceDocumentRef
from integration.sharepoint.connector import SharePointConnector, _drive_cid, _folder_cid
from integration.sharepoint.graph_client import SharePointCredentials

_FILE = {
    "id": "I1",
    "name": "guide.pdf",
    "file": {"mimeType": "application/pdf"},
    "webUrl": "https://contoso.sharepoint.com/.../guide.pdf",
    "eTag": "etag-1",
    "cTag": "ctag-1",
    "size": 2048,
    "lastModifiedDateTime": "2026-06-01T09:30:00Z",
}
_FOLDER = {"id": "F1", "name": "Manuals", "folder": {"childCount": 3}}


class _FakeHandle:
    async def token(self) -> str:
        return "tok"

    async def aclose(self) -> None:
        return None


def _connector(handler) -> SharePointConnector:  # noqa: ANN001
    http = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return SharePointConnector(
        SharePointCredentials(tenant_id="t", client_id="c", client_secret="s"),
        http=http,
    )


def test_sharepoint_capabilities() -> None:
    # §4.1 declaration. Full SourceConnector Protocol conformance (incl. get_principals)
    # is asserted in F4's test once permission mapping lands.
    c = _connector(lambda request: httpx.Response(200, json={}))
    assert c.capabilities.auth_kind == "app_registration"
    assert c.capabilities.acl_granularity == "document"
    assert c.capabilities.supports_delta is False
    assert c.capabilities.supports_browse is True


async def test_browse_top_level_lists_sites() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1.0/sites"
        return httpx.Response(200, json={"value": [{"id": "S1", "displayName": "Eng"}]})

    c = _connector(handler)
    sites = [s async for s in c.browse(_FakeHandle())]
    assert len(sites) == 1
    assert sites[0].type == "site"
    assert sites[0].id == "site::S1"


async def test_browse_site_lists_libraries() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1.0/sites/S1/drives"
        return httpx.Response(200, json={"value": [{"id": "D1", "name": "Documents"}]})

    c = _connector(handler)
    libs = [x async for x in c.browse(_FakeHandle(), "site::S1")]
    assert libs[0].type == "library"
    assert libs[0].id == "drive::D1"
    assert libs[0].parent_id == "site::S1"


async def test_browse_drive_yields_folders_only() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"value": [_FOLDER, _FILE]})

    c = _connector(handler)
    children = [x async for x in c.browse(_FakeHandle(), "drive::D1")]
    assert len(children) == 1  # the file is excluded from browse
    assert children[0].type == "folder"
    assert children[0].id == "folder::D1::F1"


async def test_list_documents_yields_files_with_change_detection() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1.0/drives/D1/root/children"
        return httpx.Response(200, json={"value": [_FOLDER, _FILE]})

    c = _connector(handler)
    docs = [d async for d in c.list_documents(_FakeHandle(), "drive::D1")]
    assert len(docs) == 1  # folder skipped
    ref = docs[0]
    assert ref.id == "I1"
    assert ref.name == "guide.pdf"
    assert ref.etag == "etag-1" and ref.version == "ctag-1" and ref.size == 2048
    assert ref.last_modified is not None and ref.last_modified.year == 2026
    assert ref.container_id == "drive::D1"


async def test_list_documents_in_folder() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1.0/drives/D1/items/F1/children"
        return httpx.Response(200, json={"value": [_FILE]})

    c = _connector(handler)
    docs = [d async for d in c.list_documents(_FakeHandle(), _folder_cid("D1", "F1"))]
    assert len(docs) == 1 and docs[0].id == "I1"


async def test_fetch_document_streams_to_temp(tmp_path: Path) -> None:
    payload = b"%PDF-1.7 content" * 50

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1.0/drives/D1/items/I1/content"
        return httpx.Response(200, content=payload)

    c = _connector(handler)
    ref = SourceDocumentRef(
        id="I1", name="guide.pdf", path="/guide.pdf", container_id=_drive_cid("D1")
    )
    doc = await c.fetch_document(_FakeHandle(), ref)
    try:
        assert doc.content_path.exists()
        assert doc.content_path.read_bytes() == payload
        assert doc.content_path.suffix == ".pdf"
        assert doc.metadata["source"] == "sharepoint"
    finally:
        doc.content_path.unlink(missing_ok=True)  # caller cleans up (§7.2)


async def test_resolve_site_by_url() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.startswith("/v1.0/sites/contoso.sharepoint.com:")
        return httpx.Response(200, json={"id": "S9", "displayName": "Engineering"})

    c = _connector(handler)
    site = await c.resolve_site(
        _FakeHandle(), "contoso.sharepoint.com", "sites/Engineering"
    )
    assert site.id == "site::S9" and site.type == "site"


async def test_delta_signals_resync() -> None:
    c = _connector(lambda request: httpx.Response(200, json={}))
    result = await c.delta(_FakeHandle(), "drive::D1", None)
    assert result.resync_required is True and result.changes == []
