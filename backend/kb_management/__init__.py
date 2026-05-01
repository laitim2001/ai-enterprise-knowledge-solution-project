"""KB management package (per architecture.md §3.4 multi-KB architecture).

W1: in-memory backend (process-local, not durable).
W2 D1: swap to Azure AI Search-backed implementation via FastAPI
dependency override; `KBStorageBackend` Protocol stays stable.
"""

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
]
