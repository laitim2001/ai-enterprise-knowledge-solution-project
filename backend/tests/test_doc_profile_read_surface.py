"""W76 / ADR-0056 層 A 段③ 前置 — profile read surface tests (per CLAUDE.md §5.6 H6).

Coverage:
- `InMemoryDocProfileStore` round-trip (get / upsert / delete / list_for_kb) + kb isolation.
- `make_doc_profile_store` factory selection (in-memory / Postgres without connecting).
- `DocProfileInfo.from_result` — ProfileResult → read schema (13-signal mirror + pdf None
  default + fallback flag).
- API join: list_documents (DocumentSummary.profile + profile_confidence) + doc_detail
  (DocumentDetail.profile full signals); profile present → surfaced, absent → null,
  no store wired → null (graceful degrade — the persist path is advisory).
"""

from __future__ import annotations

import asyncio
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routes import documents as documents_routes
from api.schemas.doc_profile import DocProfileInfo
from api.schemas.kb import KbConfig, KbCreate
from ingestion.profiler import ProfileResult, ProfileSignals
from kb_management import KBService, get_kb_service
from kb_management.doc_profile_store import (
    InMemoryDocProfileStore,
    PostgresDocProfileStore,
    make_doc_profile_store,
)
from kb_management.storage import InMemoryKBBackend
from storage.settings import Settings

# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #


def _signals(**over: float) -> ProfileSignals:
    base: dict[str, Any] = dict(
        paragraphs=100,
        headings=10,
        max_depth=4,
        list_items=55,
        images=30,
        tables=2,
        img_density=0.3,
        head_density=0.1,
        list_ratio=0.55,
        tickbox_density=0.0,
    )
    base.update(over)
    return ProfileSignals(**base)


def _info(profile: str = "P1_sop_imgdense", confidence: float = 0.9) -> DocProfileInfo:
    return DocProfileInfo.from_result(
        ProfileResult(profile=profile, confidence=confidence, signals=_signals()),  # type: ignore[arg-type]
        profiled_at="2026-06-15T00:00:00+00:00",
    )


# --------------------------------------------------------------------------- #
# InMemoryDocProfileStore round-trip
# --------------------------------------------------------------------------- #


def test_inmemory_get_absent_returns_none() -> None:
    store = InMemoryDocProfileStore()
    assert asyncio.run(store.get("kb1", "docX")) is None


def test_inmemory_upsert_then_get_round_trips() -> None:
    store = InMemoryDocProfileStore()
    info = _info()
    asyncio.run(store.upsert("kb1", "docA", info))
    got = asyncio.run(store.get("kb1", "docA"))
    assert got == info
    assert got is not None
    assert got.profile == "P1_sop_imgdense"
    assert got.signals.img_density == 0.3


def test_inmemory_upsert_replaces() -> None:
    store = InMemoryDocProfileStore()
    asyncio.run(store.upsert("kb1", "docA", _info(profile="P2_prose")))
    asyncio.run(store.upsert("kb1", "docA", _info(profile="P1_sop_text")))
    got = asyncio.run(store.get("kb1", "docA"))
    assert got is not None
    assert got.profile == "P1_sop_text"


def test_inmemory_delete_idempotent() -> None:
    store = InMemoryDocProfileStore()
    asyncio.run(store.upsert("kb1", "docA", _info()))
    assert asyncio.run(store.delete("kb1", "docA")) is True
    assert asyncio.run(store.delete("kb1", "docA")) is False  # already gone
    assert asyncio.run(store.get("kb1", "docA")) is None


def test_inmemory_list_for_kb_isolated_per_kb() -> None:
    store = InMemoryDocProfileStore()
    asyncio.run(store.upsert("kb1", "docA", _info()))
    asyncio.run(store.upsert("kb1", "docB", _info(profile="P2_prose")))
    asyncio.run(store.upsert("kb2", "docC", _info()))
    listed = asyncio.run(store.list_for_kb("kb1"))
    assert set(listed) == {"docA", "docB"}
    assert listed["docB"].profile == "P2_prose"
    assert asyncio.run(store.list_for_kb("kb2")).keys() == {"docC"}
    assert asyncio.run(store.list_for_kb("nope")) == {}


def test_inmemory_list_copy_does_not_mutate_store() -> None:
    store = InMemoryDocProfileStore()
    asyncio.run(store.upsert("kb1", "docA", _info()))
    listed = asyncio.run(store.list_for_kb("kb1"))
    listed["docZ"] = _info()  # mutate the returned dict
    assert "docZ" not in asyncio.run(store.list_for_kb("kb1"))  # live store unaffected


# --------------------------------------------------------------------------- #
# factory selection
# --------------------------------------------------------------------------- #


def test_factory_no_database_url_returns_inmemory() -> None:
    store = make_doc_profile_store(Settings(_env_file=None, database_url=""))  # type: ignore[call-arg]
    assert isinstance(store, InMemoryDocProfileStore)


def test_factory_database_url_returns_postgres_without_connecting() -> None:
    # Construction must not open a connection (lazy psycopg import inside _connect).
    store = make_doc_profile_store(
        Settings(_env_file=None, database_url="postgresql://u:p@localhost:5432/x"),  # type: ignore[call-arg]
    )
    assert isinstance(store, PostgresDocProfileStore)


# --------------------------------------------------------------------------- #
# DocProfileInfo.from_result (schema mapping)
# --------------------------------------------------------------------------- #


def test_from_result_maps_all_signals() -> None:
    result = ProfileResult(
        profile="P1_sop_imgdense",
        confidence=0.87,
        signals=_signals(paragraphs=120, images=40, img_density=0.33),
        fallback_applied=False,
    )
    info = DocProfileInfo.from_result(result, profiled_at="2026-06-15T01:00:00+00:00")
    assert info.profile == "P1_sop_imgdense"
    assert info.confidence == 0.87
    assert info.fallback_applied is False
    assert info.profiled_at == "2026-06-15T01:00:00+00:00"
    assert info.signals.paragraphs == 120
    assert info.signals.images == 40
    assert info.signals.img_density == 0.33
    assert info.signals.pdf_pages is None  # docx → no pdf pre-OCR signals


def test_from_result_carries_pdf_signals_and_fallback() -> None:
    result = ProfileResult(
        profile="P4_scan_imgdense",
        confidence=0.5,
        signals=_signals(pdf_pages=7, pdf_empty_ratio=1.0, pdf_avg_chars=0.0),
        fallback_applied=True,
    )
    info = DocProfileInfo.from_result(result, profiled_at="2026-06-15T02:00:00+00:00")
    assert info.fallback_applied is True
    assert info.signals.pdf_pages == 7
    assert info.signals.pdf_empty_ratio == 1.0


# --------------------------------------------------------------------------- #
# API join — list_documents + doc_detail
# --------------------------------------------------------------------------- #


class _MockEngine:
    """Minimal RetrievalEngine stand-in for the read routes (list_documents + list_chunks)."""

    def __init__(self, docs: list[dict[str, Any]], chunks: list[dict[str, Any]] | None = None) -> None:
        self._docs = docs
        self._chunks = chunks or []

    async def list_documents(self, kb_id: str, max_chunks: int = 1000) -> list[dict[str, Any]]:
        return self._docs

    async def list_chunks(self, kb_id: str, doc_id: str) -> list[dict[str, Any]]:
        return self._chunks


async def _kb_service() -> KBService:
    service = KBService(InMemoryKBBackend())
    await service.create(KbCreate(kb_id="kb1", name="KB One", description="", config=KbConfig()))
    return service


def _build_app(
    engine: _MockEngine, store: InMemoryDocProfileStore | None, kb_service: KBService
) -> FastAPI:
    app = FastAPI()
    app.include_router(documents_routes.router)
    app.dependency_overrides[get_kb_service] = lambda: kb_service
    app.state.retrieval_engine = engine
    if store is not None:
        app.state.doc_profile_store = store
    return app


def _doc_row(doc_id: str) -> dict[str, Any]:
    return {
        "doc_id": doc_id,
        "doc_title": doc_id.upper(),
        "doc_format": "docx",
        "total_chunks": 5,
        "last_indexed_at": "2026-06-15T00:00:00Z",
        "source_url": None,
        "tags": [],
    }


@pytest.mark.asyncio
async def test_list_documents_joins_profile() -> None:
    service = await _kb_service()
    store = InMemoryDocProfileStore()
    await store.upsert("kb1", "doc-A", _info(profile="P1_sop_imgdense", confidence=0.9))
    engine = _MockEngine(docs=[_doc_row("doc-A"), _doc_row("doc-B")])  # doc-B unprofiled
    app = _build_app(engine, store, service)

    resp = TestClient(app).get("/kb/kb1/documents")
    assert resp.status_code == 200, resp.text
    body = {d["doc_id"]: d for d in resp.json()}
    assert body["doc-A"]["profile"] == "P1_sop_imgdense"
    assert body["doc-A"]["profile_confidence"] == 0.9
    assert body["doc-B"]["profile"] is None  # not profiled → null
    assert body["doc-B"]["profile_confidence"] is None


@pytest.mark.asyncio
async def test_list_documents_no_store_graceful_null() -> None:
    service = await _kb_service()
    engine = _MockEngine(docs=[_doc_row("doc-A")])
    app = _build_app(engine, None, service)  # no store wired

    resp = TestClient(app).get("/kb/kb1/documents")
    assert resp.status_code == 200
    assert resp.json()[0]["profile"] is None
    assert resp.json()[0]["profile_confidence"] is None


@pytest.mark.asyncio
async def test_doc_detail_joins_full_profile() -> None:
    service = await _kb_service()
    store = InMemoryDocProfileStore()
    await store.upsert("kb1", "doc-A", _info(profile="P1_sop_imgdense", confidence=0.88))
    engine = _MockEngine(docs=[_doc_row("doc-A")], chunks=[])
    app = _build_app(engine, store, service)

    resp = TestClient(app).get("/kb/kb1/docs/doc-A")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["profile"] is not None
    assert body["profile"]["profile"] == "P1_sop_imgdense"
    assert body["profile"]["confidence"] == 0.88
    assert body["profile"]["signals"]["img_density"] == 0.3  # full signals surfaced


@pytest.mark.asyncio
async def test_doc_detail_absent_profile_null() -> None:
    service = await _kb_service()
    store = InMemoryDocProfileStore()  # empty store
    engine = _MockEngine(docs=[_doc_row("doc-A")], chunks=[])
    app = _build_app(engine, store, service)

    resp = TestClient(app).get("/kb/kb1/docs/doc-A")
    assert resp.status_code == 200, resp.text
    assert resp.json()["profile"] is None
