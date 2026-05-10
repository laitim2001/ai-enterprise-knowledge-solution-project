"""Tests for the KB storage backend factory (W17 F1 / ADR-0023).

These run unconditionally — the in-memory selection needs no DB; the Postgres
selection only constructs the object (no connect), and is skipped if `psycopg`
isn't installed (R8 corp-proxy block). The actual Postgres-path CRUD tests live
in `test_kb_postgres_backend.py` (gated on DATABASE_URL + psycopg).
"""

from __future__ import annotations

import pytest

from kb_management import InMemoryKBBackend, make_kb_backend
from storage.settings import Settings


def test_make_kb_backend_empty_database_url_returns_in_memory() -> None:
    backend = make_kb_backend(Settings(database_url=""))
    assert isinstance(backend, InMemoryKBBackend)


def test_make_kb_backend_with_database_url_returns_postgres() -> None:
    pytest.importorskip("psycopg")
    from kb_management.postgres_backend import PostgresKBBackend

    # Constructs only — PostgresKBBackend connects lazily per-op, so no DB needed.
    backend = make_kb_backend(
        Settings(database_url="postgresql://u:p@localhost:5432/ekp"),
    )
    assert isinstance(backend, PostgresKBBackend)
