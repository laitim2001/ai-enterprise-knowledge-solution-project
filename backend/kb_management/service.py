"""KB service — translates request payloads to backend calls.

Backend is injected (via `make_kb_backend`) so the storage layer can swap
between in-memory and Postgres (ADR-0023) without touching service or route.
"""

from datetime import UTC, datetime
from functools import lru_cache

from api.schemas.kb import FailureRecord, KbConfig, KbCreate, KbStatus
from storage.settings import get_settings

from .factory import make_kb_backend
from .storage import KBStorageBackend


class KBService:
    def __init__(self, backend: KBStorageBackend) -> None:
        self._backend = backend

    async def create(self, payload: KbCreate) -> KbStatus:
        now = datetime.now(UTC)
        kb = KbStatus(
            kb_id=payload.kb_id,
            name=payload.name,
            description=payload.description,
            config=payload.config,
            total_documents=0,
            total_chunks=0,
            total_screenshots=0,
            failed_documents=[],
            last_indexed_at=now,
            storage_size_mb=0.0,
        )
        return await self._backend.create(kb)

    async def list_all(self) -> list[KbStatus]:
        return await self._backend.list_all()

    async def get(self, kb_id: str) -> KbStatus:
        return await self._backend.get(kb_id)

    async def delete(self, kb_id: str) -> None:
        await self._backend.delete(kb_id)

    async def update_config(self, kb_id: str, config: KbConfig) -> KbStatus:
        return await self._backend.update_config(kb_id, config)

    async def update_metadata(
        self, kb_id: str, name: str | None = None, description: str | None = None,
    ) -> KbStatus:
        """W16 F5.2 CO_F3b — partial PATCH of name + description (Decision A.1)."""
        return await self._backend.update_metadata(kb_id, name=name, description=description)

    async def archive(self, kb_id: str, archived: bool = True) -> KbStatus:
        """W20 F5.1 — flip the soft-archive flag (default = True). Idempotent.
        Per ADR-0025 archived KBs survive in storage; upload/reindex routes refuse."""
        return await self._backend.set_archived(kb_id, archived)

    async def record_doc_event(
        self,
        kb_id: str,
        *,
        documents_delta: int = 0,
        chunks_delta: int = 0,
        last_indexed_at: datetime | None = None,
        append_failure: FailureRecord | None = None,
    ) -> KbStatus:
        """CH-001 — post-ingest counter sync (closes AC10).

        Wraps `KBStorageBackend.update_metrics`. Use:
        - On upload success → `documents_delta=+1, chunks_delta=+N, last_indexed_at=now`
        - On delete success → `documents_delta=-1, chunks_delta=-M, last_indexed_at=now`
        - On reindex success → `chunks_delta=(new_N - old_M), last_indexed_at=now`
        - On ingest failure → `append_failure=FailureRecord(...), last_indexed_at=now`
        """
        return await self._backend.update_metrics(
            kb_id,
            documents_delta=documents_delta,
            chunks_delta=chunks_delta,
            last_indexed_at=last_indexed_at,
            append_failure=append_failure,
        )


@lru_cache(maxsize=1)
def get_kb_service() -> KBService:
    """FastAPI dependency — process-singleton wired via `make_kb_backend`.

    Backend = Postgres when `DATABASE_URL` is set (ADR-0023), else in-memory
    (W1 behaviour — local dev / CI). Tests still swap a fresh in-memory service
    in via `app.dependency_overrides[get_kb_service]`.
    """
    return KBService(make_kb_backend(get_settings()))
