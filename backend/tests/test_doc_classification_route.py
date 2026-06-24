"""W90 P2.3 / ADR-0066 — admin classification tag endpoint tests (per CLAUDE.md §5.6 H6).

Covers `PATCH /kb/{kb_id}/docs/{doc_id}/classification`:
- 200 happy path — tags restricted → persists to store + merge-restamps the live index;
  response carries the new classification + chunks_restamped count.
- revert restricted → internal round-trips.
- 403 non-admin (require_role("admin") guard — classification is a security control).
- 422 invalid classification value (Literal-rejected at the API boundary).
- 404 when the doc has no chunks in the KB.
- 503 when the classification store isn't wired.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.auth.dependency import get_current_user
from api.auth.models import AuthenticatedUser
from api.routes import documents as documents_routes
from api.schemas.kb import KbConfig, KbCreate
from kb_management import KBService, get_kb_service
from kb_management.doc_classification_store import InMemoryDocClassificationStore
from kb_management.storage import InMemoryKBBackend

# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #


class _MockEngine:
    """Minimal RetrievalEngine stand-in — only `list_documents` (for _doc_exists_in_kb)."""

    def __init__(self, docs: list[dict[str, Any]]) -> None:
        self._docs = docs

    async def list_documents(self, kb_id: str, max_chunks: int = 1000) -> list[dict[str, Any]]:
        return self._docs


class _MockPopulator:
    """Records `update_doc_classification` calls + returns a fixed restamp count."""

    def __init__(self, restamped: int = 5) -> None:
        self._restamped = restamped
        self.calls: list[tuple[str, str, str]] = []

    async def update_doc_classification(
        self, kb_id: str, doc_id: str, classification: str
    ) -> int:
        self.calls.append((kb_id, doc_id, classification))
        return self._restamped


async def _kb_service(*, archived: bool = False) -> KBService:
    service = KBService(InMemoryKBBackend())
    await service.create(KbCreate(kb_id="kb1", name="KB One", description="", config=KbConfig()))
    if archived:
        await service.archive("kb1")
    return service


def _doc_row(doc_id: str) -> dict[str, Any]:
    return {"doc_id": doc_id, "doc_title": doc_id.upper(), "total_chunks": 5}


def _build_app(
    *,
    kb_service: KBService,
    store: InMemoryDocClassificationStore | None,
    engine: _MockEngine | None = None,
    populator: _MockPopulator | None = None,
    role: str = "admin",
    with_ingestion: bool = True,
) -> FastAPI:
    app = FastAPI()
    app.include_router(documents_routes.router)
    app.dependency_overrides[get_kb_service] = lambda: kb_service
    app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(
        oid="u-1", tid="t-1", preferred_username="u@test.local", role=role
    )
    # embedder + chunker exist only to satisfy `_ingestion_deps_or_503`; never called.
    if with_ingestion:
        app.state.embedder = MagicMock(name="Embedder")
        app.state.ingestion_chunker = MagicMock(name="Chunker")
        app.state.index_populator = populator
    else:
        app.state.embedder = None
        app.state.ingestion_chunker = None
        app.state.index_populator = None
    app.state.retrieval_engine = engine
    if store is not None:
        app.state.doc_classification_store = store
    return app


# --------------------------------------------------------------------------- #
# happy path
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_tag_restricted_persists_and_restamps() -> None:
    service = await _kb_service()
    store = InMemoryDocClassificationStore()
    populator = _MockPopulator(restamped=7)
    engine = _MockEngine(docs=[_doc_row("doc-A")])
    app = _build_app(kb_service=service, store=store, engine=engine, populator=populator)

    resp = TestClient(app).patch(
        "/kb/kb1/docs/doc-A/classification", json={"classification": "restricted"}
    )
    assert resp.status_code == 200, resp.text
    assert resp.json() == {
        "kb_id": "kb1",
        "doc_id": "doc-A",
        "classification": "restricted",
        "chunks_restamped": 7,
    }
    # 1. persisted (so re-ingest preserves).
    assert await store.get("kb1", "doc-A") == "restricted"
    # 2. live index restamped with the right args.
    assert populator.calls == [("kb1", "doc-A", "restricted")]


@pytest.mark.asyncio
async def test_revert_to_internal_round_trips() -> None:
    service = await _kb_service()
    store = InMemoryDocClassificationStore()
    await store.upsert("kb1", "doc-A", "restricted")  # already restricted
    populator = _MockPopulator()
    engine = _MockEngine(docs=[_doc_row("doc-A")])
    app = _build_app(kb_service=service, store=store, engine=engine, populator=populator)

    resp = TestClient(app).patch(
        "/kb/kb1/docs/doc-A/classification", json={"classification": "internal"}
    )
    assert resp.status_code == 200, resp.text
    assert await store.get("kb1", "doc-A") == "internal"
    assert populator.calls[-1] == ("kb1", "doc-A", "internal")


# --------------------------------------------------------------------------- #
# guards / errors
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_non_admin_forbidden() -> None:
    service = await _kb_service()
    store = InMemoryDocClassificationStore()
    engine = _MockEngine(docs=[_doc_row("doc-A")])
    app = _build_app(
        kb_service=service, store=store, engine=engine, populator=_MockPopulator(), role="editor"
    )
    resp = TestClient(app).patch(
        "/kb/kb1/docs/doc-A/classification", json={"classification": "restricted"}
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_invalid_classification_value_422() -> None:
    service = await _kb_service()
    store = InMemoryDocClassificationStore()
    engine = _MockEngine(docs=[_doc_row("doc-A")])
    app = _build_app(
        kb_service=service, store=store, engine=engine, populator=_MockPopulator()
    )
    resp = TestClient(app).patch(
        "/kb/kb1/docs/doc-A/classification", json={"classification": "secret"}
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_doc_not_found_404() -> None:
    service = await _kb_service()
    store = InMemoryDocClassificationStore()
    engine = _MockEngine(docs=[])  # no chunks for any doc
    app = _build_app(
        kb_service=service, store=store, engine=engine, populator=_MockPopulator()
    )
    resp = TestClient(app).patch(
        "/kb/kb1/docs/doc-X/classification", json={"classification": "restricted"}
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_unknown_kb_404() -> None:
    service = await _kb_service()
    store = InMemoryDocClassificationStore()
    app = _build_app(
        kb_service=service, store=store, engine=_MockEngine([]), populator=_MockPopulator()
    )
    resp = TestClient(app).patch(
        "/kb/nope/docs/doc-A/classification", json={"classification": "restricted"}
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_archived_kb_forbidden() -> None:
    service = await _kb_service(archived=True)
    store = InMemoryDocClassificationStore()
    engine = _MockEngine(docs=[_doc_row("doc-A")])
    app = _build_app(
        kb_service=service, store=store, engine=engine, populator=_MockPopulator()
    )
    resp = TestClient(app).patch(
        "/kb/kb1/docs/doc-A/classification", json={"classification": "restricted"}
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_503_when_no_store_wired() -> None:
    service = await _kb_service()
    # ingestion services present (embedder/populator/chunker) but NO classification store.
    app = _build_app(
        kb_service=service, store=None, engine=_MockEngine([_doc_row("doc-A")]),
        populator=_MockPopulator(),
    )
    resp = TestClient(app).patch(
        "/kb/kb1/docs/doc-A/classification", json={"classification": "restricted"}
    )
    assert resp.status_code == 503
