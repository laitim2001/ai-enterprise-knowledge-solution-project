"""Microsoft Graph REST client (managed-REST: azure-identity + httpx, 方案藍圖 §2.5).

Thin async wrapper the SharePoint connector (§4) sits on. Responsibilities:
- app-only token acquisition (Entra app registration `Sites.Selected`, §1.2 / §2.2)
  via azure-identity aio credentials (same pattern as `api/auth/entra_graph.py`),
- bearer injection + retry on 429 / 5xx (`tenacity`, already a dep),
- `@odata.nextLink` pagination (②) as an async generator,
- streamed download to a temp file (④ — large scans never sit fully in memory).

No `msgraph-sdk` (H2 — zero new dependency; ADR-0017 "managed-REST > heavy SDK").
Credentials / tokens are NEVER logged (H5).

Testability: `GraphClient` depends only on a `ConnectionHandle` (token provider)
+ an `httpx.AsyncClient`, so unit tests inject a fake handle + `httpx.MockTransport`
— azure-identity is never touched off a real tenant (D4). `build_credential` /
`GraphConnectionHandle` wrap azure-identity and are exercised live per runbook §10.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, cast

import httpx
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from integration.connector import ConnectionHandle

GRAPH_BASE = "https://graph.microsoft.com/v1.0"
GRAPH_SCOPE = "https://graph.microsoft.com/.default"
_DEFAULT_TIMEOUT = httpx.Timeout(60.0)


class GraphTransientError(Exception):
    """A retryable Graph response (429 throttling / 5xx). Non-transient 4xx (e.g. 403
    = per-site grant missing, §1.3) surface as `httpx.HTTPStatusError` and propagate
    as fatal (§8.1)."""


def _auth_headers(token: str) -> dict[str, str]:
    # H5: this dict is never logged.
    return {"Authorization": f"Bearer {token}", "Accept": "application/json"}


# --------------------------------------------------------------------------- #
# Credentials + connection handle (azure-identity wrappers — live path)
# --------------------------------------------------------------------------- #


@dataclass(slots=True, frozen=True)
class SharePointCredentials:
    """Entra app-registration credentials for app-only Graph access (§1.2 / §2.2).

    Provide exactly one of `client_secret` / `certificate_path` (certificate
    preferred for production, §1.2). NEVER logged / committed (H5).
    """

    tenant_id: str
    client_id: str
    client_secret: str | None = None
    certificate_path: str | None = None


class _AccessToken(Protocol):
    token: str


class _AsyncTokenCredential(Protocol):
    """Structural view of the azure-identity aio credentials we use (decouples the
    module from azure's exact stub signature across versions)."""

    async def get_token(self, *scopes: str, **kwargs: Any) -> _AccessToken: ...
    async def close(self) -> None: ...


def build_credential(creds: SharePointCredentials) -> _AsyncTokenCredential:
    """Construct an azure-identity aio credential for app-only Graph.

    Lazy import (matches `entra_graph.py` / `azure_key_vault.py`) — keeps module
    import light + avoids touching azure-identity on the in-memory / mock path.
    """
    from azure.identity.aio import CertificateCredential, ClientSecretCredential

    # cast: azure's get_token declares extra keyword-only params (claims / tenant_id /
    # enable_cae), so the concrete credential isn't *structurally* our minimal
    # _AsyncTokenCredential — but it has get_token + close at runtime, and decoupling
    # from azure's exact signature keeps us robust across azure-identity versions.
    if creds.certificate_path:
        return cast(
            _AsyncTokenCredential,
            CertificateCredential(
                tenant_id=creds.tenant_id,
                client_id=creds.client_id,
                certificate_path=creds.certificate_path,
            ),
        )
    if creds.client_secret:
        return cast(
            _AsyncTokenCredential,
            ClientSecretCredential(
                tenant_id=creds.tenant_id,
                client_id=creds.client_id,
                client_secret=creds.client_secret,
            ),
        )
    raise ValueError("SharePointCredentials requires client_secret or certificate_path")


class GraphConnectionHandle:
    """`ConnectionHandle` for Microsoft Graph. Holds an azure-identity aio credential;
    `token()` delegates to it (azure-identity caches + refreshes near expiry, ⑥).
    `aclose()` releases the credential's transport (mirrors entra_graph finally-close)."""

    def __init__(
        self, credential: _AsyncTokenCredential, *, scope: str = GRAPH_SCOPE
    ) -> None:
        self._credential = credential
        self._scope = scope

    async def token(self) -> str:
        access = await self._credential.get_token(self._scope)
        return access.token

    async def aclose(self) -> None:
        await self._credential.close()


# --------------------------------------------------------------------------- #
# Graph REST client (testable — depends only on ConnectionHandle + httpx)
# --------------------------------------------------------------------------- #


class GraphClient:
    """Async Microsoft Graph REST client. `handle` provides bearer tokens; `http` is
    a shared `httpx.AsyncClient`. Retry tuning is injectable so tests run with zero
    backoff."""

    def __init__(
        self,
        handle: ConnectionHandle,
        http: httpx.AsyncClient,
        *,
        base_url: str = GRAPH_BASE,
        max_attempts: int = 5,
        backoff_base: float = 0.5,
    ) -> None:
        self._handle = handle
        self._http = http
        self._base_url = base_url
        self._max_attempts = max_attempts
        self._backoff_base = backoff_base

    def _abs(self, path_or_url: str) -> str:
        if path_or_url.startswith("http"):
            return path_or_url  # already absolute (e.g. an @odata.nextLink)
        return f"{self._base_url}{path_or_url}"

    async def _request(
        self, method: str, url: str, *, params: dict[str, str] | None = None
    ) -> httpx.Response:
        async for attempt in AsyncRetrying(
            retry=retry_if_exception_type(GraphTransientError),
            stop=stop_after_attempt(self._max_attempts),
            wait=wait_exponential(multiplier=self._backoff_base, max=20.0),
            reraise=True,
        ):
            with attempt:
                token = await self._handle.token()
                resp = await self._http.request(
                    method, url, params=params, headers=_auth_headers(token)
                )
                if resp.status_code == 429 or resp.status_code >= 500:
                    raise GraphTransientError(
                        f"graph transient {resp.status_code}: {method} {url}"
                    )
                resp.raise_for_status()  # non-429 4xx → fatal HTTPStatusError
                return resp
        raise AssertionError("unreachable")  # pragma: no cover

    async def get_json(
        self, path_or_url: str, *, params: dict[str, str] | None = None
    ) -> dict[str, Any]:
        resp = await self._request("GET", self._abs(path_or_url), params=params)
        data: dict[str, Any] = resp.json()
        return data

    async def paged(
        self, path_or_url: str, *, params: dict[str, str] | None = None
    ) -> AsyncIterator[dict[str, Any]]:
        """Yield each element of `value` across `@odata.nextLink` pages (②). Params
        ride only the first request — the nextLink already encodes the query."""
        url: str | None = self._abs(path_or_url)
        page_params = params
        while url:
            resp = await self._request("GET", url, params=page_params)
            data: dict[str, Any] = resp.json()
            for item in data.get("value", []):
                yield item
            url = data.get("@odata.nextLink")
            page_params = None

    async def stream_to_file(self, path_or_url: str, dest: Path) -> None:
        """Stream a document's content to `dest` (④). No retry mid-stream — a failed
        fetch is recorded per-doc by the import service (§8.1)."""
        token = await self._handle.token()
        async with self._http.stream(
            "GET", self._abs(path_or_url), headers=_auth_headers(token)
        ) as resp:
            resp.raise_for_status()
            with dest.open("wb") as fh:
                async for chunk in resp.aiter_bytes():
                    fh.write(chunk)
