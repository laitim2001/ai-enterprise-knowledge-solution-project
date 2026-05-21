"""Entra ID Graph API client — managed-REST group sync (W24c F6 per ADR-0027).

C16 Users Service group-sync transport. Lives alongside the C11 identity
providers (`msal_provider` / `email_provider`) since Entra is identity
infrastructure; consumed by `api/routes/groups.py`.

F1 D1 decision — managed-REST over `msgraph-sdk`: `azure-identity` (already
installed for Key Vault, W24-c1 F1) acquires an app token, `httpx` (already a
core dep) calls `GET graph.microsoft.com/v1.0/groups`. Zero new dependency,
zero H2, zero R8 — per ADR-0017 "managed-REST > heavy SDK".

`DefaultAzureCredential` resolves Managed Identity in Container Apps / `az
login` locally — the same credential chain as `storage/azure_key_vault.py`.
The caller (`routes/groups.py`) short-circuits before reaching here when
`azure_tenant_id` is unset, so mock-auth dev never touches `azure-identity`.

The live call path is exercised pre-Beta with real Track A IT credentials
(W24c plan §3 PARTIAL PASS + R-W24c-6); the route test mocks `fetch_entra_groups`.
"""

from __future__ import annotations

from dataclasses import dataclass

import httpx

_GRAPH_BASE = "https://graph.microsoft.com/v1.0"
_GRAPH_SCOPE = "https://graph.microsoft.com/.default"
_TIMEOUT = httpx.Timeout(20.0)


@dataclass(frozen=True)
class EntraGroup:
    """A group as returned by Microsoft Graph `GET /groups`."""

    object_id: str
    display_name: str
    description: str | None


async def fetch_entra_groups() -> list[EntraGroup]:
    """Fetch every group from Microsoft Graph, following `@odata.nextLink`.

    Acquires an app token via `DefaultAzureCredential`. Raises on credential
    failure or a non-2xx Graph response — the caller turns that into a 502.
    """
    from azure.identity.aio import DefaultAzureCredential

    credential = DefaultAzureCredential()
    groups: list[EntraGroup] = []
    try:
        token = await credential.get_token(_GRAPH_SCOPE)
        headers = {"Authorization": f"Bearer {token.token}"}
        url: str | None = f"{_GRAPH_BASE}/groups?$select=id,displayName,description"
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            while url:
                resp = await client.get(url, headers=headers)
                resp.raise_for_status()
                data = resp.json()
                for grp in data.get("value", []):
                    groups.append(
                        EntraGroup(
                            object_id=grp["id"],
                            display_name=grp.get("displayName") or "",
                            description=grp.get("description"),
                        )
                    )
                url = data.get("@odata.nextLink")
    finally:
        await credential.close()
    return groups
