"""F4 — SharePoint ACL → allowed_principals mapping (§5).

Covers each special-principal case, nested-group flatten (group level only),
防爆量 cap, fetch-failure (no fail-open), and full SourceConnector conformance.
"""

from __future__ import annotations

import httpx
import pytest

from integration.connector import SourceConnector
from integration.models import SourceDocumentRef
from integration.sharepoint.connector import SharePointConnector, _drive_cid
from integration.sharepoint.graph_client import GraphClient, SharePointCredentials
from integration.sharepoint.permissions import (
    PUBLIC_PRINCIPAL,
    AclResolutionError,
    resolve_principals,
)


class _FakeHandle:
    async def token(self) -> str:
        return "tok"

    async def aclose(self) -> None:
        return None


def _graph(handler) -> GraphClient:  # noqa: ANN001
    http = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return GraphClient(_FakeHandle(), http, max_attempts=2, backoff_base=0.0)


def _perms_handler(perms: list[dict], members: dict[str, list[dict]] | None = None):  # noqa: ANN001, ANN202
    members = members or {}

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path.endswith("/permissions"):
            return httpx.Response(200, json={"value": perms})
        if "/groups/" in path and path.endswith("/transitiveMembers"):
            gid = path.split("/groups/")[1].split("/")[0]
            return httpx.Response(200, json={"value": members.get(gid, [])})
        return httpx.Response(404, json={"error": "unexpected"})

    return handler


async def _resolve(handler, **kw) -> list:  # noqa: ANN001, ANN003
    return await resolve_principals(_graph(handler), "D1", "I1", tenant_id="T1", **kw)


async def test_direct_user_grant() -> None:
    perms = [{"roles": ["read"], "grantedToV2": {"user": {"id": "U1", "displayName": "Ann"}}}]
    principals = await _resolve(_perms_handler(perms))
    assert [(p.kind, p.id) for p in principals] == [("user", "U1")]


async def test_group_grant_flattens_nested_groups_not_users() -> None:
    perms = [{"roles": ["read"], "grantedToV2": {"group": {"id": "G1", "displayName": "Eng"}}}]
    members = {
        "G1": [
            {"@odata.type": "#microsoft.graph.group", "id": "G2", "displayName": "Backend"},
            {"@odata.type": "#microsoft.graph.user", "id": "U9", "displayName": "Bob"},
        ]
    }
    principals = await _resolve(_perms_handler(perms, members))
    ids = {p.id for p in principals}
    assert ids == {"G1", "G2"}  # the granted group + nested group; the user is NOT expanded
    assert all(p.kind == "group" for p in principals)


async def test_anyone_link_dropped_by_default() -> None:
    perms = [{"roles": ["read"], "link": {"scope": "anonymous", "type": "view"}}]
    principals = await _resolve(_perms_handler(perms))  # default anyone_policy="drop"
    assert principals == []  # nothing indexed; F5 must refuse to treat [] as public


async def test_anyone_link_reject_raises() -> None:
    perms = [{"roles": ["read"], "link": {"scope": "anonymous", "type": "view"}}]
    with pytest.raises(AclResolutionError, match="policy=reject"):
        await _resolve(_perms_handler(perms), anyone_policy="reject")


async def test_anyone_link_public_emits_sentinel() -> None:
    perms = [{"roles": ["read"], "link": {"scope": "anonymous", "type": "view"}}]
    principals = await _resolve(_perms_handler(perms), anyone_policy="public")
    assert [p.id for p in principals] == [PUBLIC_PRINCIPAL]


async def test_organization_link_maps_to_org_principal() -> None:
    perms = [{"roles": ["read"], "link": {"scope": "organization", "type": "view"}}]
    principals = await _resolve(_perms_handler(perms))
    assert [(p.kind, p.id) for p in principals] == [("org", "org::T1")]


async def test_sharepoint_local_group_is_external_group() -> None:
    perms = [
        {"roles": ["read"], "grantedToV2": {"siteGroup": {"id": "SG1", "displayName": "Owners"}}}
    ]
    principals = await _resolve(_perms_handler(perms))
    assert [(p.kind, p.id) for p in principals] == [("external_group", "SG1")]


async def test_specific_people_link_resolves_identities() -> None:
    perms = [
        {
            "roles": ["read"],
            "link": {"scope": "users", "type": "view"},
            "grantedToIdentitiesV2": [
                {"user": {"id": "U3", "displayName": "Cy"}},
                {"user": {"id": "U4", "displayName": "Di"}},
            ],
        }
    ]
    principals = await _resolve(_perms_handler(perms))
    assert {p.id for p in principals} == {"U3", "U4"}


async def test_cap_truncates_principal_set() -> None:
    # One group whose transitiveMembers explode past the cap → result is capped.
    perms = [{"roles": ["read"], "grantedToV2": {"group": {"id": "G1", "displayName": "Big"}}}]
    big = [
        {"@odata.type": "#microsoft.graph.group", "id": f"G{i}"} for i in range(50)
    ]
    principals = await _resolve(_perms_handler(perms, {"G1": big}), max_principals=10)
    assert len(principals) == 10  # capped (G1 + 9 nested before the bound)


async def test_permission_fetch_failure_raises_not_fail_open() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, json={"error": "no per-site grant"})

    with pytest.raises(AclResolutionError, match="permission fetch failed"):
        await _resolve(handler)


async def test_full_sourceconnector_conformance() -> None:
    # get_principals now present → SharePointConnector satisfies the Protocol
    # (runtime_checkable checks all 6 methods; static check lives in connector.py).
    http = httpx.AsyncClient(transport=httpx.MockTransport(lambda r: httpx.Response(200, json={})))
    c: SourceConnector = SharePointConnector(
        SharePointCredentials(tenant_id="T1", client_id="c", client_secret="s"), http=http
    )
    assert isinstance(c, SourceConnector)


async def test_connector_get_principals_uses_anyone_policy() -> None:
    # End-to-end through the connector: drop policy on an Anyone link → empty.
    perms = [{"roles": ["read"], "link": {"scope": "anonymous"}}]
    http = httpx.AsyncClient(transport=httpx.MockTransport(_perms_handler(perms)))
    c = SharePointConnector(
        SharePointCredentials(tenant_id="T1", client_id="c", client_secret="s"), http=http
    )
    ref = SourceDocumentRef(id="I1", name="g.pdf", path="/g.pdf", container_id=_drive_cid("D1"))
    assert await c.get_principals(_FakeHandle(), ref) == []
