"""W82 F1 / ADR-0063 — global profile→preset override store + `resolve_preset`.

Covers:
- `InMemoryPresetOverrideStore` round-trip (get / upsert / delete / list_all), incl.
  idempotent delete + returned-dict isolation.
- `make_preset_override_store` factory selection (in-memory when no DATABASE_URL;
  Postgres type when set — without connecting).
- `resolve_preset` overlay semantics: no override → bit-identical to `preset_for`
  (production-preserve), override → uses override, result is a fresh copy.
"""

from __future__ import annotations

import asyncio

from api.schemas.doc_config import DocConfig
from ingestion.profile_presets import preset_for, resolve_preset
from kb_management.preset_override_store import (
    InMemoryPresetOverrideStore,
    PostgresPresetOverrideStore,
    make_preset_override_store,
)
from storage.settings import Settings

# --------------------------------------------------------------------------- #
# InMemoryPresetOverrideStore round-trip
# --------------------------------------------------------------------------- #


def test_inmemory_get_absent_returns_none() -> None:
    store = InMemoryPresetOverrideStore()
    assert asyncio.run(store.get("P2_prose")) is None


def test_inmemory_upsert_then_get_round_trips() -> None:
    store = InMemoryPresetOverrideStore()
    cfg = DocConfig(answer_detail="concise", max_images_per_answer=15)
    asyncio.run(store.upsert("P2_prose", cfg))
    got = asyncio.run(store.get("P2_prose"))
    assert got == cfg
    assert got.answer_detail == "concise"
    assert got.max_images_per_answer == 15


def test_inmemory_upsert_replaces() -> None:
    store = InMemoryPresetOverrideStore()
    asyncio.run(store.upsert("P2_prose", DocConfig(max_images_per_answer=10)))
    asyncio.run(store.upsert("P2_prose", DocConfig(max_images_per_answer=20)))
    got = asyncio.run(store.get("P2_prose"))
    assert got is not None
    assert got.max_images_per_answer == 20


def test_inmemory_delete_idempotent() -> None:
    store = InMemoryPresetOverrideStore()
    asyncio.run(store.upsert("P2_prose", DocConfig()))
    assert asyncio.run(store.delete("P2_prose")) is True
    assert asyncio.run(store.delete("P2_prose")) is False  # already gone (還原預設)
    assert asyncio.run(store.get("P2_prose")) is None


def test_inmemory_list_all_returns_every_override() -> None:
    store = InMemoryPresetOverrideStore()
    asyncio.run(store.upsert("P2_prose", DocConfig(max_images_per_answer=1)))
    asyncio.run(store.upsert("P5_form", DocConfig(max_images_per_answer=2)))
    listed = asyncio.run(store.list_all())
    assert set(listed) == {"P2_prose", "P5_form"}
    assert listed["P2_prose"].max_images_per_answer == 1


def test_inmemory_list_copy_does_not_mutate_store() -> None:
    store = InMemoryPresetOverrideStore()
    asyncio.run(store.upsert("P2_prose", DocConfig()))
    listed = asyncio.run(store.list_all())
    listed["P9_fake"] = DocConfig()  # mutate the returned dict
    assert "P9_fake" not in asyncio.run(store.list_all())  # live store unaffected


# --------------------------------------------------------------------------- #
# factory selection
# --------------------------------------------------------------------------- #


def test_factory_no_database_url_returns_inmemory() -> None:
    store = make_preset_override_store(Settings(_env_file=None, database_url=""))
    assert isinstance(store, InMemoryPresetOverrideStore)


def test_factory_database_url_returns_postgres_without_connecting() -> None:
    # Construction must not open a connection (lazy psycopg import inside _connect).
    store = make_preset_override_store(
        Settings(_env_file=None, database_url="postgresql://u:p@localhost:5432/x"),
    )
    assert isinstance(store, PostgresPresetOverrideStore)


# --------------------------------------------------------------------------- #
# resolve_preset — overlay semantics (ADR-0063)
# --------------------------------------------------------------------------- #


def test_resolve_no_override_is_bit_identical_to_factory() -> None:
    # production-preserve: empty store → resolve == preset_for for every profile.
    store = InMemoryPresetOverrideStore()
    for profile in ("P1_sop_imgdense", "P2_prose", "P5_form"):
        assert asyncio.run(resolve_preset(profile, store)) == preset_for(profile)


def test_resolve_no_override_none_profiles_stay_none() -> None:
    # too_small / unknown have no factory preset → resolve stays None (inherit).
    store = InMemoryPresetOverrideStore()
    assert asyncio.run(resolve_preset("too_small", store)) is None
    assert asyncio.run(resolve_preset("unknown", store)) is None


def test_resolve_none_store_falls_back_to_factory() -> None:
    # W82 F2 — an unwired store (None) degrades to the factory preset (production-
    # preserve for call sites whose preset_override_store isn't wired, e.g. some tests).
    for profile in ("P1_sop_imgdense", "P2_prose"):
        assert asyncio.run(resolve_preset(profile, None)) == preset_for(profile)
    assert asyncio.run(resolve_preset("too_small", None)) is None


def test_resolve_override_wins_over_factory() -> None:
    store = InMemoryPresetOverrideStore()
    custom = DocConfig(max_images_per_answer=999, answer_detail="concise")
    asyncio.run(store.upsert("P1_sop_imgdense", custom))
    resolved = asyncio.run(resolve_preset("P1_sop_imgdense", store))
    assert resolved == custom
    assert resolved != preset_for("P1_sop_imgdense")  # factory cap=80, not 999


def test_resolve_override_can_route_a_none_profile() -> None:
    # An admin override gives a routable preset to an otherwise-None profile.
    store = InMemoryPresetOverrideStore()
    custom = DocConfig(max_images_per_answer=5)
    asyncio.run(store.upsert("too_small", custom))
    assert asyncio.run(resolve_preset("too_small", store)) == custom


def test_resolve_returns_fresh_copy_not_store_instance() -> None:
    # Mutating the resolved config must not corrupt the stored override.
    store = InMemoryPresetOverrideStore()
    asyncio.run(store.upsert("P2_prose", DocConfig(max_images_per_answer=5)))
    resolved = asyncio.run(resolve_preset("P2_prose", store))
    assert resolved is not None
    resolved.max_images_per_answer = 111  # mutate the copy
    again = asyncio.run(store.get("P2_prose"))
    assert again is not None
    assert again.max_images_per_answer == 5  # store untouched


def test_resolve_factory_copy_is_independent() -> None:
    # No override → returns a copy of the factory preset; mutating it must not
    # corrupt the module-level PROFILE_PRESETS (shared across the process).
    store = InMemoryPresetOverrideStore()
    resolved = asyncio.run(resolve_preset("P1_sop_imgdense", store))
    assert resolved is not None
    resolved.max_images_per_answer = 7
    assert preset_for("P1_sop_imgdense").max_images_per_answer == 80  # factory intact
