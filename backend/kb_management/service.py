"""KB service — translates request payloads to backend calls.

Backend is injected (via `make_kb_backend`) so the storage layer can swap
between in-memory and Postgres (ADR-0023) without touching service or route.
"""

from datetime import UTC, datetime
from functools import lru_cache

from api.schemas.kb import KbConfig, KbCreate, KbStatus
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


@lru_cache(maxsize=1)
def get_kb_service() -> KBService:
    """FastAPI dependency — process-singleton wired via `make_kb_backend`.

    Backend = Postgres when `DATABASE_URL` is set (ADR-0023), else in-memory
    (W1 behaviour — local dev / CI). Tests still swap a fresh in-memory service
    in via `app.dependency_overrides[get_kb_service]`.
    """
    return KBService(make_kb_backend(get_settings()))
