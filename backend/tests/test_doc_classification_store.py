"""Per-document classification store tests (W90 P2.3 / ADR-0066, per CLAUDE.md §5.6 H6).

Covers `InMemoryDocClassificationStore` round-trip (upsert / get / delete / list_for_kb,
incl. idempotent delete + kb-isolation + empty-bucket cleanup) + `make_doc_classification_store`
factory selection (in-memory when no DATABASE_URL; Postgres type when set — without connecting).
"""

from __future__ import annotations

import asyncio

from kb_management.doc_classification_store import (
    InMemoryDocClassificationStore,
    PostgresDocClassificationStore,
    make_doc_classification_store,
)
from storage.settings import Settings

# --------------------------------------------------------------------------- #
# InMemoryDocClassificationStore round-trip
# --------------------------------------------------------------------------- #


def test_inmemory_get_absent_returns_none() -> None:
    # No row = default internal — the caller materialises the default, not the store.
    store = InMemoryDocClassificationStore()
    assert asyncio.run(store.get("kb1", "docX")) is None


def test_inmemory_upsert_then_get_round_trips() -> None:
    store = InMemoryDocClassificationStore()
    asyncio.run(store.upsert("kb1", "docA", "restricted"))
    assert asyncio.run(store.get("kb1", "docA")) == "restricted"


def test_inmemory_upsert_replaces() -> None:
    store = InMemoryDocClassificationStore()
    asyncio.run(store.upsert("kb1", "docA", "restricted"))
    asyncio.run(store.upsert("kb1", "docA", "internal"))  # reverted
    assert asyncio.run(store.get("kb1", "docA")) == "internal"


def test_inmemory_delete_idempotent() -> None:
    store = InMemoryDocClassificationStore()
    asyncio.run(store.upsert("kb1", "docA", "restricted"))
    assert asyncio.run(store.delete("kb1", "docA")) is True
    assert asyncio.run(store.delete("kb1", "docA")) is False  # already gone
    assert asyncio.run(store.get("kb1", "docA")) is None


def test_inmemory_delete_drops_empty_kb_bucket() -> None:
    store = InMemoryDocClassificationStore()
    asyncio.run(store.upsert("kb1", "docA", "restricted"))
    asyncio.run(store.delete("kb1", "docA"))
    # bucket cleaned up — list_for_kb returns empty, no orphan kb key.
    assert asyncio.run(store.list_for_kb("kb1")) == {}


def test_inmemory_list_for_kb_isolated_per_kb() -> None:
    store = InMemoryDocClassificationStore()
    asyncio.run(store.upsert("kb1", "docA", "restricted"))
    asyncio.run(store.upsert("kb1", "docB", "internal"))
    asyncio.run(store.upsert("kb2", "docC", "restricted"))
    assert asyncio.run(store.list_for_kb("kb1")) == {"docA": "restricted", "docB": "internal"}
    assert asyncio.run(store.list_for_kb("kb2")) == {"docC": "restricted"}
    assert asyncio.run(store.list_for_kb("kb3")) == {}


def test_inmemory_list_for_kb_returns_copy() -> None:
    # Callers can't mutate the live store via the returned dict.
    store = InMemoryDocClassificationStore()
    asyncio.run(store.upsert("kb1", "docA", "restricted"))
    snapshot = asyncio.run(store.list_for_kb("kb1"))
    snapshot["docA"] = "internal"
    assert asyncio.run(store.get("kb1", "docA")) == "restricted"


# --------------------------------------------------------------------------- #
# Factory selection
# --------------------------------------------------------------------------- #


def test_factory_inmemory_when_no_database_url() -> None:
    store = make_doc_classification_store(Settings(_env_file=None, database_url=""))
    assert isinstance(store, InMemoryDocClassificationStore)


def test_factory_postgres_type_when_database_url_set() -> None:
    # Selects the Postgres impl WITHOUT connecting (construction is lazy).
    store = make_doc_classification_store(
        Settings(_env_file=None, database_url="postgresql://u:p@localhost:5432/x")
    )
    assert isinstance(store, PostgresDocClassificationStore)
