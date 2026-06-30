"""Provider-agnostic source-integration data models (C17, per ADR-0070 + 方案藍圖 §3.5).

These are the standardized types a `SourceConnector` emits — the boundary between
"some external source" and EKP's ingestion core. The connector's only job is to
turn a provider (SharePoint, …) into these; everything downstream (Docling
parsing / chunking / 圖文還原 / per-doc profile) stays provider-blind (設計鐵律 §0.4).

@dataclass (not Pydantic) — internal pipeline types, no API-boundary validation,
matching `ingestion/parsers/base.py`. frozen for the immutable descriptors;
SourceDocument is non-frozen (carries a temp path the caller cleans up).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Literal

PrincipalKind = Literal["user", "group", "external_group", "org"]
ContainerType = Literal["site", "library", "folder"]


@dataclass(slots=True, frozen=True)
class Principal:
    """A resolved access-control principal.

    `id` is the literal string written into a chunk's `allowed_principals` (Entra
    object GUID for user/group; a synthetic stable token for org-wide / external
    groups — the query-time security filter matches on the literal string, so any
    stable id works). `kind` is metadata for logging + degradation, not matching.
    """

    kind: PrincipalKind
    id: str
    display_name: str = ""


@dataclass(slots=True, frozen=True)
class SourceContainer:
    """A browsable container in the source tree (SharePoint: site / library / folder)."""

    id: str
    name: str
    type: ContainerType
    parent_id: str | None = None


@dataclass(slots=True, frozen=True)
class SourceDocumentRef:
    """A pointer to a source document + change-detection metadata (③ — `etag` /
    `version` / `last_modified` / `size`). Cheap to list in bulk; `fetch_document`
    turns one into a `SourceDocument`. Re-import compares `etag` to skip unchanged
    docs (§4.4)."""

    id: str
    name: str
    path: str
    container_id: str
    etag: str | None = None
    version: str | None = None
    last_modified: datetime | None = None
    size: int | None = None


@dataclass(slots=True)
class SourceDocument:
    """A fetched document: its ref + a local temp path the connector streamed the
    content to (④ — large scans must not sit fully in memory). The caller hands
    `content_path` to EKP's existing ingestion entry, then deletes the temp file.
    ACL is fetched separately via `get_principals` (single-responsibility — the ACL
    lives behind a distinct Graph endpoint)."""

    ref: SourceDocumentRef
    content_path: Path
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True, frozen=True)
class DeltaResult:
    """Incremental-sync result (⑤). Reserved; SharePoint declares
    `supports_delta=False` (delta is unreliable at the library/folder permission
    layer — §6.2). Kept so 階段 3 auto-sync needn't change the Protocol."""

    changes: list[SourceDocumentRef]
    new_token: str | None
    resync_required: bool = False
