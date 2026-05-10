"""KB management package (per architecture.md §3.4 multi-KB architecture).

W1: in-memory backend (process-local, not durable).
W17 F1 / ADR-0023: `PostgresKBBackend` added — `make_kb_backend(settings)`
picks it when `DATABASE_URL` is set, else `InMemoryKBBackend`. `KBStorageBackend`
Protocol stays stable; FastAPI dependency override still works for tests.
"""

from .factory import make_kb_backend
from .service import KBService, get_kb_service
from .storage import (
    InMemoryKBBackend,
    KBAlreadyExistsError,
    KBNotFoundError,
    KBStorageBackend,
)

__all__ = [
    "InMemoryKBBackend",
    "KBAlreadyExistsError",
    "KBNotFoundError",
    "KBService",
    "KBStorageBackend",
    "get_kb_service",
    "make_kb_backend",
]
