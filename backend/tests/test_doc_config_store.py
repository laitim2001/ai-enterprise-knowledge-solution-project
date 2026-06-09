"""W57 F6.1 / F6.3 — per-document config store + dominant-doc helper (ADR-0050).

Covers:
- `InMemoryDocConfigStore` round-trip (upsert / get / delete / list_for_kb), incl.
  idempotent delete + kb-isolation.
- `make_doc_config_store` factory selection (in-memory when no DATABASE_URL;
  Postgres type when set — without connecting).
- `_dominant_doc_id` (query pipeline) — single doc / multi doc / tie / empty.
"""

from __future__ import annotations

import asyncio
from types import SimpleNamespace

from api.routes.query import _dominant_doc_id
from api.schemas.doc_config import DocConfig
from kb_management.doc_config_store import (
    InMemoryDocConfigStore,
    PostgresDocConfigStore,
    make_doc_config_store,
)
from storage.settings import Settings

# --------------------------------------------------------------------------- #
# InMemoryDocConfigStore round-trip
# --------------------------------------------------------------------------- #


def test_inmemory_get_absent_returns_none() -> None:
    store = InMemoryDocConfigStore()
    assert asyncio.run(store.get("kb1", "docX")) is None


def test_inmemory_upsert_then_get_round_trips() -> None:
    store = InMemoryDocConfigStore()
    cfg = DocConfig(answer_detail="detailed", max_images_per_answer=30)
    asyncio.run(store.upsert("kb1", "docA", cfg))
    got = asyncio.run(store.get("kb1", "docA"))
    assert got == cfg
    assert got.answer_detail == "detailed"
    assert got.max_images_per_answer == 30


def test_inmemory_upsert_replaces() -> None:
    store = InMemoryDocConfigStore()
    asyncio.run(store.upsert("kb1", "docA", DocConfig(max_images_per_answer=10)))
    asyncio.run(store.upsert("kb1", "docA", DocConfig(max_images_per_answer=20)))
    got = asyncio.run(store.get("kb1", "docA"))
    assert got is not None
    assert got.max_images_per_answer == 20


def test_inmemory_delete_idempotent() -> None:
    store = InMemoryDocConfigStore()
    asyncio.run(store.upsert("kb1", "docA", DocConfig()))
    assert asyncio.run(store.delete("kb1", "docA")) is True
    assert asyncio.run(store.delete("kb1", "docA")) is False  # already gone
    assert asyncio.run(store.get("kb1", "docA")) is None


def test_inmemory_list_for_kb_is_isolated_per_kb() -> None:
    store = InMemoryDocConfigStore()
    asyncio.run(store.upsert("kb1", "docA", DocConfig(max_images_per_answer=1)))
    asyncio.run(store.upsert("kb1", "docB", DocConfig(max_images_per_answer=2)))
    asyncio.run(store.upsert("kb2", "docC", DocConfig(max_images_per_answer=3)))
    listed = asyncio.run(store.list_for_kb("kb1"))
    assert set(listed) == {"docA", "docB"}
    assert listed["docA"].max_images_per_answer == 1
    assert asyncio.run(store.list_for_kb("kb2")).keys() == {"docC"}
    assert asyncio.run(store.list_for_kb("nope")) == {}


def test_inmemory_list_copy_does_not_mutate_store() -> None:
    store = InMemoryDocConfigStore()
    asyncio.run(store.upsert("kb1", "docA", DocConfig()))
    listed = asyncio.run(store.list_for_kb("kb1"))
    listed["docZ"] = DocConfig()  # mutate the returned dict
    assert "docZ" not in asyncio.run(store.list_for_kb("kb1"))  # live store unaffected


# --------------------------------------------------------------------------- #
# factory selection
# --------------------------------------------------------------------------- #


def test_factory_no_database_url_returns_inmemory() -> None:
    store = make_doc_config_store(Settings(_env_file=None, database_url=""))
    assert isinstance(store, InMemoryDocConfigStore)


def test_factory_database_url_returns_postgres_without_connecting() -> None:
    # Construction must not open a connection (lazy psycopg import inside _connect).
    store = make_doc_config_store(
        Settings(_env_file=None, database_url="postgresql://u:p@localhost:5432/x"),
    )
    assert isinstance(store, PostgresDocConfigStore)


# --------------------------------------------------------------------------- #
# _dominant_doc_id (ADR-0050)
# --------------------------------------------------------------------------- #


def _chunk(doc_id: str) -> SimpleNamespace:
    return SimpleNamespace(fields={"doc_id": doc_id})


def test_dominant_doc_single() -> None:
    chunks = [_chunk("dA"), _chunk("dA"), _chunk("dA")]
    assert _dominant_doc_id(chunks) == "dA"


def test_dominant_doc_most_cited_wins() -> None:
    chunks = [_chunk("dA"), _chunk("dB"), _chunk("dB"), _chunk("dB"), _chunk("dA")]
    assert _dominant_doc_id(chunks) == "dB"


def test_dominant_doc_tie_resolves_to_highest_rank() -> None:
    # dA and dB tie at 2 each; dA's first chunk is highest-ranked (index 0) → dA wins.
    chunks = [_chunk("dA"), _chunk("dB"), _chunk("dB"), _chunk("dA")]
    assert _dominant_doc_id(chunks) == "dA"


def test_dominant_doc_empty_or_no_doc_id_is_none() -> None:
    assert _dominant_doc_id([]) is None
    assert _dominant_doc_id([SimpleNamespace(fields={})]) is None
    assert _dominant_doc_id([SimpleNamespace(fields={"doc_id": ""})]) is None
    assert _dominant_doc_id([SimpleNamespace(other="x")]) is None  # no .fields dict
