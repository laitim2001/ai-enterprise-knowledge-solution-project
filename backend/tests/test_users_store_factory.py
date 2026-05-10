"""Tests for the users-store factory (W17 F1 / ADR-0023).

Runs unconditionally — the in-memory selection needs no DB; the Postgres
selection only constructs the object (connects lazily per-op), and is skipped
if `psycopg` isn't installed (R8 corp-proxy block). The actual Postgres-path
CRUD tests live in `test_auth_users_postgres_store.py` (gated on DATABASE_URL +
psycopg). Mirrors `test_kb_factory.py`.
"""

from __future__ import annotations

import pytest

from api.auth.users_store import InMemoryUsersStore, make_users_store
from storage.settings import Settings


def test_make_users_store_empty_database_url_returns_in_memory() -> None:
    store = make_users_store(Settings(database_url=""))
    assert isinstance(store, InMemoryUsersStore)


def test_make_users_store_with_database_url_returns_postgres() -> None:
    pytest.importorskip("psycopg")
    from api.auth.postgres_users_store import PostgresUsersStore

    # Constructs only — PostgresUsersStore connects lazily per-op, so no DB needed.
    store = make_users_store(Settings(database_url="postgresql://u:p@localhost:5432/ekp"))
    assert isinstance(store, PostgresUsersStore)
