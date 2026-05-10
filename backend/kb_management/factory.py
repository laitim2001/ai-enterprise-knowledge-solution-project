"""KB storage backend factory (per ADR-0023).

Picks the Postgres-backed `PostgresKBBackend` when `settings.database_url` is
set, else the process-local `InMemoryKBBackend` (W1 behaviour — local dev / CI
unchanged). Mirrors the `retrieval.reranker.factory.make_reranker` pattern.

`PostgresKBBackend` (and therefore `psycopg`) is imported lazily inside the
branch so an unset `DATABASE_URL` never touches `psycopg` — same graceful-degrade
shape as the ACS lazy import (W13 F6); also keeps the in-memory path working if
`psycopg` install is blocked (R8 corp proxy).
"""

from __future__ import annotations

from kb_management.storage import InMemoryKBBackend, KBStorageBackend
from storage.settings import Settings


def make_kb_backend(settings: Settings) -> KBStorageBackend:
    """Return a Postgres-backed KB store when `database_url` is set, else in-memory."""
    if settings.database_url:
        from kb_management.postgres_backend import PostgresKBBackend

        return PostgresKBBackend(settings.database_url)
    return InMemoryKBBackend()
