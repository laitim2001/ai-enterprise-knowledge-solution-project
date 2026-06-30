"""SharePoint `SourceConnector` implementation (§4) — connect / browse / list / fetch.

Maps the provider-agnostic Protocol onto SharePoint via `GraphClient` (managed-REST).
`get_principals` (ACL → allowed_principals) is the heaviest method and lives next to
the permission-mapping logic in `permissions.py` (F4), mixed in here.

Container navigation uses a prefix-encoded id so one `browse` walks the whole tree:
  site::<site-id>            — a SharePoint site
  drive::<drive-id>          — a document library (drive)
  folder::<drive-id>::<item> — a folder inside a drive
`list_documents` accepts drive:: / folder:: ; a `SourceDocumentRef` keeps its owning
`container_id` so `fetch_document` recovers the drive id without extra state.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

import httpx

from integration.connector import ConnectionHandle, ConnectorCapabilities
from integration.models import (
    DeltaResult,
    SourceContainer,
    SourceDocument,
    SourceDocumentRef,
)
from integration.sharepoint.graph_client import (
    GraphClient,
    GraphConnectionHandle,
    SharePointCredentials,
    build_credential,
)

_DEFAULT_TIMEOUT = httpx.Timeout(60.0)
_SEP = "::"


# --------------------------------------------------------------------------- #
# Container-id encode / decode
# --------------------------------------------------------------------------- #


def _site_cid(site_id: str) -> str:
    return f"site{_SEP}{site_id}"


def _drive_cid(drive_id: str) -> str:
    return f"drive{_SEP}{drive_id}"


def _folder_cid(drive_id: str, item_id: str) -> str:
    return f"folder{_SEP}{drive_id}{_SEP}{item_id}"


def _parse_cid(container_id: str) -> tuple[str, list[str]]:
    parts = container_id.split(_SEP)
    return parts[0], parts[1:]


def _drive_id_from_container(container_id: str) -> str:
    kind, parts = _parse_cid(container_id)
    if kind in ("drive", "folder") and parts:
        return parts[0]
    raise ValueError(f"container has no drive id: {container_id}")


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _ref_from_item(item: dict[str, Any], container_id: str) -> SourceDocumentRef:
    """driveItem → SourceDocumentRef, carrying change-detection (③ — eTag/cTag/
    lastModified/size). `id` is the bare item id; the drive id is recoverable from
    `container_id` (so re-import + fetch need no extra plumbing)."""
    return SourceDocumentRef(
        id=item["id"],
        name=item["name"],
        path=item.get("webUrl") or item["name"],
        container_id=container_id,
        etag=item.get("eTag"),
        version=item.get("cTag"),
        last_modified=_parse_dt(item.get("lastModifiedDateTime")),
        size=item.get("size"),
    )


# --------------------------------------------------------------------------- #
# Connector
# --------------------------------------------------------------------------- #


class SharePointConnector:
    """SourceConnector for SharePoint via Microsoft Graph (§4). Capability declaration
    per §4.1: app-registration auth, browsable, document-level ACL, no delta."""

    capabilities = ConnectorCapabilities(
        auth_kind="app_registration",
        supports_browse=True,
        supports_acl=True,
        supports_delta=False,
        acl_granularity="document",
    )

    def __init__(
        self,
        credentials: SharePointCredentials,
        *,
        http: httpx.AsyncClient | None = None,
    ) -> None:
        self._creds = credentials
        # Connector owns one AsyncClient for the import run (reused across calls).
        # An injected client (tests) is caller-owned and not closed here.
        self._http = http or httpx.AsyncClient(timeout=_DEFAULT_TIMEOUT)
        self._owns_http = http is None

    async def connect(self) -> GraphConnectionHandle:
        """Build an app-only Graph handle (§4.2). The credential is created here;
        the caller closes the handle (`aclose`) after the batch."""
        return GraphConnectionHandle(build_credential(self._creds))

    async def aclose(self) -> None:
        """Close the owned httpx client (no-op for an injected one)."""
        if self._owns_http:
            await self._http.aclose()

    def _graph(self, handle: ConnectionHandle) -> GraphClient:
        return GraphClient(handle, self._http)

    async def resolve_site(
        self, handle: ConnectionHandle, hostname: str, site_path: str
    ) -> SourceContainer:
        """Resolve a SharePoint site URL (UI step 1) → a site container. `site_path`
        is the server-relative path, e.g. "sites/Engineering"."""
        gc = self._graph(handle)
        site = await gc.get_json(f"/sites/{hostname}:/{site_path}")
        return SourceContainer(
            id=_site_cid(site["id"]),
            name=site.get("displayName") or site.get("name") or site["id"],
            type="site",
        )

    async def browse(
        self, handle: ConnectionHandle, container_id: str | None = None
    ) -> AsyncIterator[SourceContainer]:
        """List child containers (②). None → sites; site → libraries; drive/folder →
        sub-folders (files come from `list_documents`)."""
        gc = self._graph(handle)
        if container_id is None:
            async for site in gc.paged("/sites", params={"search": "*"}):
                yield SourceContainer(
                    id=_site_cid(site["id"]),
                    name=site.get("displayName") or site.get("name") or site["id"],
                    type="site",
                )
            return

        kind, parts = _parse_cid(container_id)
        if kind == "site":
            async for drive in gc.paged(f"/sites/{parts[0]}/drives"):
                yield SourceContainer(
                    id=_drive_cid(drive["id"]),
                    name=drive.get("name") or drive["id"],
                    type="library",
                    parent_id=container_id,
                )
            return
        if kind in ("drive", "folder"):
            drive_id = parts[0]
            path = (
                f"/drives/{drive_id}/root/children"
                if kind == "drive"
                else f"/drives/{drive_id}/items/{parts[1]}/children"
            )
            async for child in gc.paged(path):
                if "folder" in child:  # only containers here; files via list_documents
                    yield SourceContainer(
                        id=_folder_cid(drive_id, child["id"]),
                        name=child["name"],
                        type="folder",
                        parent_id=container_id,
                    )
            return
        raise ValueError(f"cannot browse container kind: {kind}")

    async def list_documents(
        self, handle: ConnectionHandle, container_id: str
    ) -> AsyncIterator[SourceDocumentRef]:
        """List file documents in a drive / folder (②③). Folders are skipped."""
        gc = self._graph(handle)
        kind, parts = _parse_cid(container_id)
        if kind == "drive":
            path = f"/drives/{parts[0]}/root/children"
        elif kind == "folder":
            path = f"/drives/{parts[0]}/items/{parts[1]}/children"
        else:
            raise ValueError(f"cannot list documents in container kind: {kind}")
        async for child in gc.paged(path):
            if "file" not in child:
                continue  # skip folders / non-file driveItems
            yield _ref_from_item(child, container_id)

    async def fetch_document(
        self, handle: ConnectionHandle, ref: SourceDocumentRef
    ) -> SourceDocument:
        """Stream a document's content to a temp file (④). The caller hands the path
        to EKP ingestion then deletes it (§7.2)."""
        drive_id = _drive_id_from_container(ref.container_id)
        gc = self._graph(handle)
        with NamedTemporaryFile(delete=False, suffix=Path(ref.name).suffix) as tmp:
            dest = Path(tmp.name)
        await gc.stream_to_file(f"/drives/{drive_id}/items/{ref.id}/content", dest)
        return SourceDocument(ref=ref, content_path=dest, metadata={"source": "sharepoint"})

    async def delta(
        self, handle: ConnectionHandle, container_id: str, token: str | None
    ) -> DeltaResult:
        """⑤ reserved — `supports_delta=False` (delta is unreliable at the library
        permission layer, §6.2). Always signals resync so a caller that ignores the
        capability still falls back to full re-ingest."""
        return DeltaResult(changes=[], new_token=None, resync_required=True)
