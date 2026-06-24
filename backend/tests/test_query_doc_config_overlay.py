"""W57 F3 — /query + /query/stream apply the per-document config overlay (ADR-0050).

End-to-end proof of the dominant-doc overlay: after retrieval the pipeline finds the
dominant cited doc, loads its `DocConfig` from the store, re-resolves the
post-retrieval knobs, and the synthesizer sees the doc's value. Observed via
`answer_detail` (the route passes `detail_level=effective.answer_detail` to synth),
which a recording synth captures.

- doc has a per-doc config → synth sees the doc's value (overlay applied)
- doc has NO per-doc config → synth sees the per-KB value (production-preserve)
- no store wired → per-KB value (back-compat)
- /query/stream parity
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.auth.dependency import get_current_user
from api.auth.models import AuthenticatedUser
from api.routes import query as query_route
from api.schemas.doc_config import DocConfig
from api.schemas.kb import KbConfig, KbCreate
from kb_management.doc_config_store import InMemoryDocConfigStore
from kb_management.service import KBService, get_kb_service
from kb_management.storage import InMemoryKBBackend
from storage.settings import Settings


@dataclass
class _Chunk:
    score: float
    fields: dict[str, Any]


@dataclass
class _RR:
    chunks: list[_Chunk]
    reranked: bool
    total_latency_ms: int


@dataclass
class _Synth:
    answer: str
    citation_ids: list[str]
    deployment: str
    latency_ms: int
    refused: bool
    expanded_neighbor_chunks: list = field(default_factory=list)


class _Engine:
    def __init__(self, chunks: list[_Chunk]) -> None:
        self._chunks = chunks

    async def retrieve(self, *, query: str, kb_id: str, top_k: int, **_kw: object) -> _RR:
        return _RR(self._chunks, True, 10)

    async def expand_context_for_chunks(
        self,
        chunks: list[_Chunk],
        *,
        kb_id: str,
    ) -> tuple[list[_Chunk], dict]:
        return chunks, {}


class _RecordingSynth:
    """Captures the `detail_level` (== effective.answer_detail) the route passes."""

    def __init__(self) -> None:
        self.detail_levels: list[str] = []

    async def synthesize(
        self,
        query: str,
        chunks: list[_Chunk],
        *,
        engine: object = None,
        kb_id: str | None = None,
        effective_config: object = None,
        detail_level: str = "concise",
    ) -> _Synth:
        self.detail_levels.append(detail_level)
        return _Synth(
            answer="ok",
            citation_ids=[],
            deployment="gpt-5.5-mock",
            latency_ms=1,
            refused=False,
        )

    async def synthesize_stream(
        self,
        query: str,
        chunks: list[_Chunk],
        *,
        engine: object = None,
        kb_id: str | None = None,
        effective_config: object = None,
        detail_level: str = "concise",
    ):
        self.detail_levels.append(detail_level)
        yield {"type": "text-delta", "content": "ok"}
        yield {
            "type": "result",
            "citation_ids": [],
            "deployment": "gpt-5.5-mock",
            "answer": "ok",
            "input_tokens": 1,
            "output_tokens": 1,
            "latency_ms": 1,
            "refused": False,
        }


def _chunks(dominant: str) -> list[_Chunk]:
    # 2 chunks of the dominant doc + 1 of another → dominant wins.
    return [
        _Chunk(0.9, {"chunk_id": "c1", "chunk_title": "T", "chunk_text": "x", "doc_id": dominant}),
        _Chunk(0.8, {"chunk_id": "c2", "chunk_title": "T", "chunk_text": "y", "doc_id": dominant}),
        _Chunk(0.7, {"chunk_id": "c3", "chunk_title": "T", "chunk_text": "z", "doc_id": "other"}),
    ]


def _app(
    *,
    kb_config: KbConfig,
    dominant: str = "dom",
    doc_config: DocConfig | None = None,
    doc_id: str = "dom",
    wire_store: bool = True,
) -> tuple[FastAPI, _RecordingSynth]:
    service = KBService(InMemoryKBBackend())
    asyncio.run(service.create(KbCreate(kb_id="kb", name="t", config=kb_config)))
    synth = _RecordingSynth()
    app = FastAPI()
    app.state.retrieval_engine = _Engine(_chunks(dominant))
    app.state.synthesizer = synth
    app.state.crag_loop = None
    if wire_store:
        store = InMemoryDocConfigStore()
        if doc_config is not None:
            asyncio.run(store.upsert("kb", doc_id, doc_config))
        app.state.doc_config_store = store
    app.dependency_overrides[get_kb_service] = lambda: service
    # W90 P2.0 — /query + /query/stream now assert_kb_access("query")-guarded;
    # admin clears it without a wired rbac_backend.
    app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(
        oid="test-admin", tid="test-tid", preferred_username="admin@test.local", role="admin"
    )
    app.include_router(query_route.router)
    return app, synth


def _no_neighbour_kb(**kw: object) -> KbConfig:
    # neighbour-image attach off so the mock engine needs no list_chunks path.
    return KbConfig(enable_citation_neighbour_images=False, **kw)


def test_query_applies_per_doc_answer_detail(monkeypatch) -> None:
    monkeypatch.setattr(query_route, "get_settings", lambda: Settings(_env_file=None))
    app, synth = _app(
        kb_config=_no_neighbour_kb(answer_detail="concise"),
        doc_config=DocConfig(answer_detail="detailed"),
    )
    resp = TestClient(app).post("/query", json={"query": "how?", "kb_id": "kb"})
    assert resp.status_code == 200, resp.text
    # dominant doc 'dom' has answer_detail=detailed → overlay wins over per-KB concise
    assert synth.detail_levels == ["detailed"]


def test_query_no_doc_config_keeps_per_kb(monkeypatch) -> None:
    monkeypatch.setattr(query_route, "get_settings", lambda: Settings(_env_file=None))
    app, synth = _app(
        kb_config=_no_neighbour_kb(answer_detail="detailed"),
        doc_config=None,  # store wired but empty
    )
    resp = TestClient(app).post("/query", json={"query": "how?", "kb_id": "kb"})
    assert resp.status_code == 200, resp.text
    # no per-doc config for the dominant doc → per-KB value (detailed) unchanged
    assert synth.detail_levels == ["detailed"]


def test_query_config_only_for_other_doc_not_applied(monkeypatch) -> None:
    """A per-doc config keyed to a NON-dominant doc must not leak into the answer."""
    monkeypatch.setattr(query_route, "get_settings", lambda: Settings(_env_file=None))
    app, synth = _app(
        kb_config=_no_neighbour_kb(answer_detail="concise"),
        doc_config=DocConfig(answer_detail="detailed"),
        doc_id="other",  # config stored for the minority doc, not the dominant 'dom'
    )
    resp = TestClient(app).post("/query", json={"query": "how?", "kb_id": "kb"})
    assert resp.status_code == 200, resp.text
    assert synth.detail_levels == ["concise"]  # dominant 'dom' has no config


def test_query_no_store_wired_is_back_compat(monkeypatch) -> None:
    monkeypatch.setattr(query_route, "get_settings", lambda: Settings(_env_file=None))
    app, synth = _app(
        kb_config=_no_neighbour_kb(answer_detail="concise"),
        wire_store=False,  # app.state has no doc_config_store → no overlay
    )
    resp = TestClient(app).post("/query", json={"query": "how?", "kb_id": "kb"})
    assert resp.status_code == 200, resp.text
    assert synth.detail_levels == ["concise"]


def test_query_stream_applies_per_doc_answer_detail(monkeypatch) -> None:
    monkeypatch.setattr(query_route, "get_settings", lambda: Settings(_env_file=None))
    app, synth = _app(
        kb_config=_no_neighbour_kb(answer_detail="concise"),
        doc_config=DocConfig(answer_detail="detailed"),
    )
    resp = TestClient(app).post("/query/stream", json={"query": "how?", "kb_id": "kb"})
    assert resp.status_code == 200, resp.text
    assert synth.detail_levels == ["detailed"]  # stream parity with /query
