"""F5 — import orchestration: per-doc error model, ACL flow, temp cleanup, no fail-open.

Mostly driven by a controllable fake connector; one end-to-end case wires the real
SharePointConnector (MockTransport) so allowed_principals flow connector→ingest.
"""

from __future__ import annotations

import tempfile
from collections.abc import AsyncIterator
from pathlib import Path

import httpx

from integration.connector import ConnectorCapabilities
from integration.import_service import import_documents, import_selected_documents
from integration.models import Principal, SourceContainer, SourceDocument, SourceDocumentRef
from integration.sharepoint.connector import SharePointConnector, _drive_cid
from integration.sharepoint.graph_client import SharePointCredentials

_CAPS = ConnectorCapabilities(
    auth_kind="app_registration",
    supports_browse=True,
    supports_acl=True,
    supports_delta=False,
    acl_granularity="document",
)


def _ref(item_id: str, name: str, container: str = "drive::D1") -> SourceDocumentRef:
    return SourceDocumentRef(id=item_id, name=name, path=f"/{name}", container_id=container)


class _FakeConnector:
    capabilities = _CAPS

    def __init__(
        self,
        *,
        docs: dict[str, list[SourceDocumentRef]],
        principals: dict[str, list[Principal]],
        fetch_fail: set[str] = frozenset(),  # type: ignore[assignment]
        list_fail: set[str] = frozenset(),  # type: ignore[assignment]
    ) -> None:
        self._docs = docs
        self._principals = principals
        self._fetch_fail = fetch_fail
        self._list_fail = list_fail
        self.created_paths: list[Path] = []

    async def connect(self):  # noqa: ANN201
        return None

    async def browse(  # noqa: D102
        self, handle, container_id=None  # noqa: ANN001
    ) -> AsyncIterator[SourceContainer]:
        return
        yield  # pragma: no cover — makes this an async generator

    async def list_documents(  # noqa: D102
        self, handle, container_id  # noqa: ANN001
    ) -> AsyncIterator[SourceDocumentRef]:
        if container_id in self._list_fail:
            raise RuntimeError("403 no per-site grant")
        for ref in self._docs.get(container_id, []):
            yield ref

    async def fetch_document(self, handle, ref) -> SourceDocument:  # noqa: ANN001
        if ref.id in self._fetch_fail:
            raise RuntimeError("content fetch 500")
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(ref.name).suffix) as tmp:
            tmp.write(b"bytes")
            path = Path(tmp.name)
        self.created_paths.append(path)
        return SourceDocument(ref=ref, content_path=path)

    async def get_principals(self, handle, ref) -> list[Principal]:  # noqa: ANN001
        return self._principals.get(ref.id, [])

    async def delta(self, handle, container_id, token):  # noqa: ANN001, ANN201
        return None


class _RecordingIngest:
    def __init__(self, fail_doc_ids: set[str] = frozenset()) -> None:  # type: ignore[assignment]
        self.calls: list[dict] = []
        self.seen_paths: list[Path] = []
        self._fail = fail_doc_ids

    async def __call__(  # noqa: D102
        self, *, content_path, name, kb_id, doc_id, allowed_principals, source_url  # noqa: ANN001
    ) -> None:
        self.seen_paths.append(content_path)
        if doc_id in self._fail:
            raise RuntimeError("ingest boom")
        self.calls.append(
            {"doc_id": doc_id, "name": name, "allowed": allowed_principals, "url": source_url}
        )


async def test_happy_path_two_docs_ingest_with_principals() -> None:
    conn = _FakeConnector(
        docs={"drive::D1": [_ref("I1", "a.pdf"), _ref("I2", "b.docx")]},
        principals={"I1": [Principal("group", "G1")], "I2": [Principal("user", "U1")]},
    )
    ingest = _RecordingIngest()
    summary = await import_documents(
        conn, None, kb_id="kb1", container_ids=["drive::D1"], ingest=ingest  # type: ignore[arg-type]
    )

    assert summary.total == 2 and summary.succeeded == 2 and summary.failed == 0
    assert {c["doc_id"] for c in ingest.calls} == {"sp-I1", "sp-I2"}
    assert ingest.calls[0]["allowed"] == ["G1"]  # SharePoint ACL flows to the stamp
    # temp files cleaned up after ingest (§8.5)
    assert all(not p.exists() for p in conn.created_paths)


async def test_empty_acl_refused_not_indexed_as_public() -> None:
    conn = _FakeConnector(
        docs={"drive::D1": [_ref("I1", "secret.pdf")]},
        principals={"I1": []},  # no resolvable principal (e.g. Anyone-link dropped)
    )
    ingest = _RecordingIngest()
    summary = await import_documents(
        conn, None, kb_id="kb1", container_ids=["drive::D1"], ingest=ingest  # type: ignore[arg-type]
    )

    assert summary.failed == 1 and summary.succeeded == 0
    assert "acl_empty" in (summary.results[0].error or "")
    assert ingest.calls == []  # never ingested — no fail-open to public (§6)


async def test_fetch_failure_is_per_doc_not_fatal() -> None:
    conn = _FakeConnector(
        docs={"drive::D1": [_ref("I1", "ok.pdf"), _ref("I2", "bad.pdf")]},
        principals={"I1": [Principal("group", "G1")], "I2": [Principal("group", "G2")]},
        fetch_fail={"I2"},
    )
    ingest = _RecordingIngest()
    summary = await import_documents(
        conn, None, kb_id="kb1", container_ids=["drive::D1"], ingest=ingest  # type: ignore[arg-type]
    )

    assert summary.succeeded == 1 and summary.failed == 1
    assert {c["doc_id"] for c in ingest.calls} == {"sp-I1"}  # good doc still imported


async def test_ingest_failure_records_and_cleans_temp() -> None:
    conn = _FakeConnector(
        docs={"drive::D1": [_ref("I1", "a.pdf")]},
        principals={"I1": [Principal("group", "G1")]},
    )
    ingest = _RecordingIngest(fail_doc_ids={"sp-I1"})
    summary = await import_documents(
        conn, None, kb_id="kb1", container_ids=["drive::D1"], ingest=ingest  # type: ignore[arg-type]
    )

    assert summary.failed == 1 and "ingest boom" in (summary.results[0].error or "")
    assert all(not p.exists() for p in conn.created_paths)  # temp cleaned even on failure


async def test_container_listing_failure_is_per_container() -> None:
    conn = _FakeConnector(
        docs={"drive::OK": [_ref("I1", "a.pdf", "drive::OK")]},
        principals={"I1": [Principal("group", "G1")]},
        list_fail={"drive::BAD"},
    )
    ingest = _RecordingIngest()
    summary = await import_documents(
        conn,
        None,  # type: ignore[arg-type]
        kb_id="kb1",
        container_ids=["drive::BAD", "drive::OK"],
        ingest=ingest,
    )

    assert summary.succeeded == 1  # drive::OK still processed
    assert any("list_failed" in (r.error or "") for r in summary.results)


async def test_end_to_end_real_connector_acl_flow() -> None:
    # Real SharePointConnector + MockTransport: list → permissions (group + nested) →
    # content, all the way to the ingest stamp.
    file_item = {"id": "I1", "name": "guide.pdf", "file": {}, "size": 9}

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path.endswith("/children"):
            return httpx.Response(200, json={"value": [file_item]})
        if path.endswith("/permissions"):
            return httpx.Response(
                200,
                json={"value": [{"grantedToV2": {"group": {"id": "G1", "displayName": "Eng"}}}]},
            )
        if "/groups/G1/transitiveMembers" in path:
            return httpx.Response(
                200, json={"value": [{"@odata.type": "#microsoft.graph.group", "id": "G2"}]}
            )
        if path.endswith("/content"):
            return httpx.Response(200, content=b"%PDF-1.7 ...")
        return httpx.Response(404, json={})

    http = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    connector = SharePointConnector(
        SharePointCredentials(tenant_id="T1", client_id="c", client_secret="s"), http=http
    )

    class _Handle:
        async def token(self) -> str:
            return "tok"

        async def aclose(self) -> None:
            return None

    ingest = _RecordingIngest()
    summary = await import_documents(
        connector,
        _Handle(),
        kb_id="kb1",
        container_ids=[_drive_cid("D1")],
        ingest=ingest,
    )

    assert summary.succeeded == 1
    assert set(ingest.calls[0]["allowed"]) == {"G1", "G2"}  # group + nested, end to end


async def test_import_selected_documents_by_ref() -> None:
    # Individual-file path (#1 / D-3): refs imported directly, list_documents bypassed.
    conn = _FakeConnector(
        docs={},  # unused — import_selected_documents does not list containers
        principals={"I1": [Principal("group", "G1")], "I2": [Principal("group", "G2")]},
    )
    ingest = _RecordingIngest()
    summary = await import_selected_documents(
        conn,  # type: ignore[arg-type]
        None,  # type: ignore[arg-type]
        kb_id="kb1",
        refs=[_ref("I1", "a.pdf"), _ref("I2", "b.docx")],
        ingest=ingest,
    )

    assert summary.total == 2 and summary.succeeded == 2 and summary.failed == 0
    assert {c["doc_id"] for c in ingest.calls} == {"sp-I1", "sp-I2"}
    assert all(not p.exists() for p in conn.created_paths)  # temp cleaned (§8.5)


async def test_import_selected_empty_acl_refused() -> None:
    # Same no-fail-open guard as the container path (§6): empty ACL → not indexed.
    conn = _FakeConnector(docs={}, principals={"I1": []})
    ingest = _RecordingIngest()
    summary = await import_selected_documents(
        conn,  # type: ignore[arg-type]
        None,  # type: ignore[arg-type]
        kb_id="kb1",
        refs=[_ref("I1", "secret.pdf")],
        ingest=ingest,
    )

    assert summary.failed == 1 and ingest.calls == []
