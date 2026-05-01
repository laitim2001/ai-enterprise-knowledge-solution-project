"""KB storage backends — Protocol + W1 in-memory impl.

W2 D1 will add an Azure AI Search-backed implementation that satisfies
the same Protocol; FastAPI dependency override swaps it in without
touching call sites (per architecture.md §3.4).
"""

from typing import Protocol

from api.schemas.kb import KbConfig, KbStatus


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
