"""F2 — Graph REST client (pagination / retry / streaming / token delegation).

No real tenant (D4): a fake ConnectionHandle supplies the bearer + `httpx.MockTransport`
fakes Graph responses. azure-identity is never touched here.
"""

from __future__ import annotations

from pathlib import Path

import httpx
import pytest

from integration.sharepoint.graph_client import (
    GraphClient,
    GraphTransientError,
    SharePointCredentials,
    build_credential,
)


class _FakeHandle:
    """Fake ConnectionHandle — returns a fixed token, counts how often it's asked."""

    def __init__(self, token: str = "fake-token") -> None:
        self._token = token
        self.token_calls = 0
        self.closed = False

    async def token(self) -> str:
        self.token_calls += 1
        return self._token

    async def aclose(self) -> None:
        self.closed = True


def _client(handle: _FakeHandle, transport: httpx.MockTransport) -> GraphClient:
    http = httpx.AsyncClient(transport=transport)
    return GraphClient(handle, http, max_attempts=3, backoff_base=0.0)


async def test_get_json_injects_bearer_and_parses() -> None:
    seen: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["auth"] = request.headers.get("Authorization", "")
        return httpx.Response(200, json={"id": "site-1", "displayName": "Docs"})

    handle = _FakeHandle("tok-abc")
    gc = _client(handle, httpx.MockTransport(handler))
    data = await gc.get_json("/sites/site-1")

    assert data["displayName"] == "Docs"
    assert seen["auth"] == "Bearer tok-abc"  # bearer injected
    assert handle.token_calls == 1


async def test_paged_follows_odata_nextlink() -> None:
    page2_url = "https://graph.microsoft.com/v1.0/drives/d1/items/i1/children?$skiptoken=ABC"

    def handler(request: httpx.Request) -> httpx.Response:
        if "$skiptoken" in str(request.url):
            return httpx.Response(200, json={"value": [{"id": "c"}, {"id": "d"}]})
        return httpx.Response(
            200,
            json={"value": [{"id": "a"}, {"id": "b"}], "@odata.nextLink": page2_url},
        )

    handle = _FakeHandle()
    gc = _client(handle, httpx.MockTransport(handler))
    items = [item["id"] async for item in gc.paged("/drives/d1/items/i1/children")]

    assert items == ["a", "b", "c", "d"]  # across two pages
    assert handle.token_calls == 2  # one token fetch per page request (refresh seam)


async def test_retry_on_429_then_succeeds() -> None:
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(429, json={"error": "throttled"})
        return httpx.Response(200, json={"ok": True})

    gc = _client(_FakeHandle(), httpx.MockTransport(handler))
    data = await gc.get_json("/groups/g1/transitiveMembers")

    assert data["ok"] is True
    assert calls["n"] == 2  # retried once after 429


async def test_retry_exhausts_on_persistent_5xx() -> None:
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(503, json={"error": "unavailable"})

    gc = _client(_FakeHandle(), httpx.MockTransport(handler))
    with pytest.raises(GraphTransientError):
        await gc.get_json("/sites/s1")
    assert calls["n"] == 3  # max_attempts


async def test_non_429_4xx_is_fatal_not_retried() -> None:
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(403, json={"error": "no per-site grant"})

    gc = _client(_FakeHandle(), httpx.MockTransport(handler))
    with pytest.raises(httpx.HTTPStatusError):
        await gc.get_json("/sites/s1")
    assert calls["n"] == 1  # 403 (missing Sites.Selected grant) propagates immediately


async def test_stream_to_file_writes_content(tmp_path: Path) -> None:
    payload = b"%PDF-1.7 fake document bytes" * 100

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=payload)

    gc = _client(_FakeHandle(), httpx.MockTransport(handler))
    dest = tmp_path / "doc.pdf"
    await gc.stream_to_file("/drives/d1/items/i1/content", dest)

    assert dest.read_bytes() == payload


def test_build_credential_requires_secret_or_cert() -> None:
    with pytest.raises(ValueError, match="client_secret or certificate_path"):
        build_credential(SharePointCredentials(tenant_id="t", client_id="c"))
