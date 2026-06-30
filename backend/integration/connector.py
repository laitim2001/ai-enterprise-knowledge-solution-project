"""`SourceConnector` Protocol + capability model (C17, per ADR-0070 + 方案藍圖 §3).

provider-agnostic contract. SharePoint (`integration/sharepoint/`) is the first and
(階段 1) only concrete connector; the Protocol is shaped so 階段 2 providers
(Google Drive / Box / …) plug in without touching the framework — they just declare
a different `ConnectorCapabilities` (§3.1) and the degradation rules (§3.4) adapt.

Convention notes (lock-in refinements of the 方案藍圖 §3.2 concept sketch, plan D-1):
- async + Protocol, mirroring `conversations.store.ConversationStore`.
- Credentials live in the concrete connector's `__init__`, NOT in `connect()`: a
  per-provider credential param on `connect` would break structural conformance
  (method-parameter contravariance), so the Protocol keeps identical signatures
  across providers. Matches EKP's store pattern — cheap sync construction, async
  network `connect()`.
- `browse` / `list_documents` are async *generators* (paged via `@odata.nextLink`
  in the SharePoint impl, ② — a large library must not materialize as one list),
  so they are declared `def -> AsyncIterator[...]`, not `async def`.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Literal, Protocol, runtime_checkable

from integration.models import (
    DeltaResult,
    Principal,
    SourceContainer,
    SourceDocument,
    SourceDocumentRef,
)

AuthKind = Literal["oauth", "app_registration", "api_key"]
AclGranularity = Literal["none", "kb", "document"]


@dataclass(slots=True, frozen=True)
class ConnectorCapabilities:
    """What a connector can do. UI + lifecycle read this to decide behaviour (see
    `resolve_behaviour` / §3.4) — one framework, providers just declare capability."""

    auth_kind: AuthKind
    supports_browse: bool
    supports_acl: bool
    supports_delta: bool
    acl_granularity: AclGranularity


@runtime_checkable
class ConnectionHandle(Protocol):
    """Opaque authenticated context. Implementations encapsulate token refresh (⑥)
    so connector methods never see token expiry."""

    async def token(self) -> str:
        """A currently-valid access token, refreshed transparently if near expiry."""
        ...


@runtime_checkable
class SourceConnector(Protocol):
    """provider-agnostic source contract (§3.2). Concrete connectors take their
    credentials in `__init__` and implement these six methods."""

    capabilities: ConnectorCapabilities

    async def connect(self) -> ConnectionHandle:
        """Acquire an authenticated handle (network). Raises on auth failure — fatal,
        the caller aborts the batch (§8.1)."""
        ...

    def browse(
        self, handle: ConnectionHandle, container_id: str | None = None
    ) -> AsyncIterator[SourceContainer]:
        """List child containers (site → library → folder). Paged (②). `container_id`
        None = top level."""
        ...

    def list_documents(
        self, handle: ConnectionHandle, container_id: str
    ) -> AsyncIterator[SourceDocumentRef]:
        """List documents in a container. Paged (②); refs carry change-detection (③)."""
        ...

    async def fetch_document(
        self, handle: ConnectionHandle, ref: SourceDocumentRef
    ) -> SourceDocument:
        """Download one document's content to a temp file (④)."""
        ...

    async def get_principals(
        self, handle: ConnectionHandle, ref: SourceDocumentRef
    ) -> list[Principal]:
        """Resolve a document's ACL → principals (group-level, ①). An empty list means
        'no resolvable ACL' — the caller MUST NOT treat that as public (§6 risk)."""
        ...

    async def delta(
        self, handle: ConnectionHandle, container_id: str, token: str | None
    ) -> DeltaResult:
        """Incremental changes (⑤). Reserved; capability-gated (`supports_delta`)."""
        ...


# --------------------------------------------------------------------------- #
# Capability degradation (§3.4) — framework reads capabilities, picks behaviour.
# --------------------------------------------------------------------------- #

SyncMode = Literal["manual_only", "auto"]
AclMode = Literal["kb_fallback", "document_trimming"]
BrowseMode = Literal["tree", "manual_id"]


@dataclass(slots=True, frozen=True)
class CapabilityBehaviour:
    """Resolved behaviour the UI + import lifecycle follow for a given connector.
    One place to read instead of scattering `if caps.supports_*` checks."""

    sync_mode: SyncMode
    acl_mode: AclMode
    browse_mode: BrowseMode


def resolve_behaviour(caps: ConnectorCapabilities) -> CapabilityBehaviour:
    """Map capabilities → behaviour (§3.4 degradation rules).

    - no delta → manual full re-ingest only (hide 'auto-sync')
    - acl none / not supported → fall back to KB-layer ACL
    - acl document → document-level trimming (fill `allowed_principals`)
    - no browse → user hand-enters a container id (no tree)
    """
    return CapabilityBehaviour(
        sync_mode="auto" if caps.supports_delta else "manual_only",
        acl_mode=(
            "document_trimming"
            if caps.supports_acl and caps.acl_granularity == "document"
            else "kb_fallback"
        ),
        browse_mode="tree" if caps.supports_browse else "manual_id",
    )
