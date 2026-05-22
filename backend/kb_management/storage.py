"""KB storage backends — Protocol + W1 in-memory impl.

W2 D1 will add an Azure AI Search-backed implementation that satisfies
the same Protocol; FastAPI dependency override swaps it in without
touching call sites (per architecture.md §3.4).

CH-001 (2026-05-12) — added `update_metrics` for post-ingest counter sync
(closes CO_F3a / AC10): documents_delta + chunks_delta signed-int updates,
last_indexed_at overwrite, append_failure for ingest failure recording.
Scope intentionally minimal: total_screenshots + storage_size_mb drift is
documented as a known future-tier follow-up (no per-doc size tracking yet).
"""

from datetime import datetime
from typing import Protocol

from api.schemas.kb import FailureRecord, KbConfig, KbStatus


class KBNotFoundError(Exception):
    """Raised when a kb_id does not exist in the backend."""


class KBAlreadyExistsError(Exception):
    """Raised when create() targets a kb_id that already exists."""


class KBStorageBackend(Protocol):
    """KB CRUD interface. Implementations must be async-safe."""

    async def create(self, kb: KbStatus) -> KbStatus: ...

    async def list_all(self) -> list[KbStatus]: ...

    async def get(self, kb_id: str) -> KbStatus: ...

    async def delete(self, kb_id: str) -> None: ...

    async def update_config(self, kb_id: str, config: KbConfig) -> KbStatus: ...

    async def update_metadata(
        self, kb_id: str, name: str | None = None, description: str | None = None,
    ) -> KbStatus: ...  # W16 F5.2 CO_F3b — partial PATCH name+description

    async def update_metrics(
        self,
        kb_id: str,
        *,
        documents_delta: int = 0,
        chunks_delta: int = 0,
        screenshots_delta: int = 0,
        last_indexed_at: datetime | None = None,
        append_failure: FailureRecord | None = None,
    ) -> KbStatus: ...  # CH-001 — post-ingest counter sync (closes AC10)

    async def set_archived(self, kb_id: str, archived: bool) -> KbStatus: ...
    """W20 F5.1 — flip the `archived` flag for soft-archive semantics per ADR-0025."""


class InMemoryKBBackend:
    """Process-local KB store. W1 development only — not durable across restart."""

    def __init__(self) -> None:
        self._kbs: dict[str, KbStatus] = {}

    async def create(self, kb: KbStatus) -> KbStatus:
        if kb.kb_id in self._kbs:
            raise KBAlreadyExistsError(f"KB '{kb.kb_id}' already exists")
        self._kbs[kb.kb_id] = kb
        return kb

    async def list_all(self) -> list[KbStatus]:
        return list(self._kbs.values())

    async def get(self, kb_id: str) -> KbStatus:
        kb = self._kbs.get(kb_id)
        if kb is None:
            raise KBNotFoundError(f"KB '{kb_id}' not found")
        return kb

    async def delete(self, kb_id: str) -> None:
        if kb_id not in self._kbs:
            raise KBNotFoundError(f"KB '{kb_id}' not found")
        del self._kbs[kb_id]

    async def update_config(self, kb_id: str, config: KbConfig) -> KbStatus:
        kb = await self.get(kb_id)
        updated = kb.model_copy(update={"config": config})
        self._kbs[kb_id] = updated
        return updated

    async def update_metadata(
        self, kb_id: str, name: str | None = None, description: str | None = None,
    ) -> KbStatus:
        """W16 F5.2 CO_F3b — partial PATCH of name + description fields only.

        Omitted fields (None) preserve existing values. Per Decision A.1
        separation of concern — config update goes through update_config.
        """
        kb = await self.get(kb_id)
        updates: dict = {}
        if name is not None:
            updates["name"] = name
        if description is not None:
            updates["description"] = description
        if not updates:  # both None — no-op (still return current state)
            return kb
        updated = kb.model_copy(update=updates)
        self._kbs[kb_id] = updated
        return updated

    async def update_metrics(
        self,
        kb_id: str,
        *,
        documents_delta: int = 0,
        chunks_delta: int = 0,
        screenshots_delta: int = 0,
        last_indexed_at: datetime | None = None,
        append_failure: FailureRecord | None = None,
    ) -> KbStatus:
        """CH-001 — post-ingest counter sync. Read-modify-write on the cached KB.

        documents_delta / chunks_delta / screenshots_delta: signed integers
        (positive on upload-success, negative on delete). Floors at 0 to
        prevent underflow drift if a delete touches a counter we forgot to
        increment on a prior upload failure.

        BUG-010 — `screenshots_delta` carries `IngestionResult.images_uploaded`
        on ingest success so the Images-tab counter reflects reality. Delete /
        reindex screenshot decrement stays a documented future-tier follow-up
        (dedup makes screenshots shared across docs — needs ref-counting).
        """
        kb = await self.get(kb_id)
        new_documents = max(0, kb.total_documents + documents_delta)
        new_chunks = max(0, kb.total_chunks + chunks_delta)
        new_screenshots = max(0, kb.total_screenshots + screenshots_delta)
        new_indexed_at = last_indexed_at if last_indexed_at is not None else kb.last_indexed_at
        new_failures = list(kb.failed_documents)
        if append_failure is not None:
            new_failures.append(append_failure)
        updated = kb.model_copy(update={
            "total_documents": new_documents,
            "total_chunks": new_chunks,
            "total_screenshots": new_screenshots,
            "last_indexed_at": new_indexed_at,
            "failed_documents": new_failures,
        })
        self._kbs[kb_id] = updated
        return updated

    async def set_archived(self, kb_id: str, archived: bool) -> KbStatus:
        """W20 F5.1 — soft-archive flag flip. Idempotent (flipping to current value
        returns the unchanged record). Per ADR-0025 the search index + screenshot
        blobs are preserved — only `documents.py` write paths refuse new ingest."""
        kb = await self.get(kb_id)
        if kb.archived == archived:
            return kb
        updated = kb.model_copy(update={"archived": archived})
        self._kbs[kb_id] = updated
        return updated
