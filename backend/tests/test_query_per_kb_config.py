"""W43 F1.8 — /query route honours the per-KB EffectiveConfig (ADR-0040).

Proves the F1.3 wire: a per-KB `KbConfig` knob flows through `EffectiveConfig` to
the parent-doc aggregation gate, overriding the global default in BOTH directions:
- per-KB True + custom value over a global-OFF default (the value reaches the engine)
- per-KB False over a global-ON default (the aggressive global is suppressed — the
  AR-conservative scenario that ADR-0040 G2 needs)

A `_RecordingEngine` captures whether / how `aggregate_parent_sections_for_chunks`
fires. `get_settings` is monkeypatched per test so the global baseline is
deterministic regardless of any repo-root `.env`.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routes import query as query_route
from api.schemas.kb import KbConfig, KbCreate
from kb_management.service import KBService, get_kb_service
from kb_management.storage import InMemoryKBBackend
from storage.settings import Settings


@dataclass
class _Chunk:
    score: float
    fields: dict[str, Any]


@dataclass
class _RetrievalResult:
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


class _RecordingEngine:
    """Records parent-doc aggregation calls; passthrough for everything else."""

    def __init__(self, chunks: list[_Chunk]) -> None:
        self._chunks = chunks
        self.aggregate_calls: list[dict[str, Any]] = []
        # CH-007 — capture the top_k (rerank depth) + overfetch (candidate pool) the
        # route passes, so a test can prove the per-KB default_rerank_k / default_top_k
        # reached the engine.
        self.retrieve_calls: list[dict[str, Any]] = []

    async def retrieve(
        self, *, query: str, kb_id: str, top_k: int,
        overfetch: int | None = None, **_kw: object,
    ) -> _RetrievalResult:
        self.retrieve_calls.append({"top_k": top_k, "overfetch": overfetch})
        return _RetrievalResult(chunks=self._chunks, reranked=True, total_latency_ms=10)

    async def expand_context_for_chunks(
        self, chunks: list[_Chunk], *, kb_id: str,
    ) -> tuple[list[_Chunk], dict]:
        return chunks, {}

    async def aggregate_parent_sections_for_chunks(
        self,
        chunks: list[_Chunk],
        *,
        kb_id: str,
        section_depth_offset: int,
        parent_doc_top_k: int,
        max_tokens_per_parent: int,
        max_chunks_per_parent: int,
        fallback_to_doc_on_shallow: bool,
    ) -> tuple[list[_Chunk], dict]:
        self.aggregate_calls.append(
            {"section_depth_offset": section_depth_offset, "parent_doc_top_k": parent_doc_top_k},
        )
        return chunks, {}


class _MockSynth:
    async def synthesize(
        self, query: str, chunks: list[_Chunk], *,
        engine: object = None, kb_id: str | None = None, effective_config: object = None,
        detail_level: str = "concise",  # CH-006 — route passes this; mock must accept it
    ) -> _Synth:
        return _Synth(
            answer="ok", citation_ids=[], deployment="gpt-5.5-mock",
            latency_ms=1, refused=False,
        )

    async def synthesize_stream(
        self, query: str, chunks: list[_Chunk], *,
        engine: object = None, kb_id: str | None = None, effective_config: object = None,
        detail_level: str = "concise",
    ):
        """Minimal Synthesizer.synthesize_stream protocol: text-delta* then a terminal
        `result` event (per stream_composer.compose_query_stream)."""
        yield {"type": "text-delta", "content": "ok"}
        yield {
            "type": "result", "citation_ids": [], "deployment": "gpt-5.5-mock",
            "answer": "ok", "input_tokens": 1, "output_tokens": 1,
            "latency_ms": 1, "refused": False,
        }


def _kb_service_with(kb_id: str, config: KbConfig) -> KBService:
    service = KBService(InMemoryKBBackend())
    asyncio.run(service.create(KbCreate(kb_id=kb_id, name="t", config=config)))
    return service


def _build_app(engine: _RecordingEngine, service: KBService) -> FastAPI:
    app = FastAPI()
    app.state.retrieval_engine = engine
    app.state.synthesizer = _MockSynth()
    app.state.crag_loop = None
    app.dependency_overrides[get_kb_service] = lambda: service
    app.include_router(query_route.router)
    return app


def _good_chunk() -> _Chunk:
    return _Chunk(score=0.9, fields={"chunk_id": "c1", "chunk_title": "T", "chunk_text": "x"})


def test_per_kb_enables_parent_doc_over_global_off(monkeypatch) -> None:
    """per-KB enable_parent_doc_retrieval=True + offset=3 reaches the engine even
    though the global default is OFF."""
    monkeypatch.setattr(
        query_route, "get_settings",
        lambda: Settings(_env_file=None, enable_parent_doc_retrieval=False),
    )
    engine = _RecordingEngine([_good_chunk()])
    kb = KbConfig(
        enable_parent_doc_retrieval=True,
        parent_doc_section_depth_offset=3,
        enable_citation_neighbour_images=False,  # avoid the neighbour-image fetch path
    )
    client = TestClient(_build_app(engine, _kb_service_with("kb-pd", kb)))

    resp = client.post("/query", json={"query": "how?", "kb_id": "kb-pd"})

    assert resp.status_code == 200, resp.text
    assert len(engine.aggregate_calls) == 1
    # per-KB value (3) reached the engine, not the global default (1)
    assert engine.aggregate_calls[0]["section_depth_offset"] == 3


def test_per_kb_disables_parent_doc_over_global_on(monkeypatch) -> None:
    """per-KB enable_parent_doc_retrieval=False suppresses an aggressive global ON
    (the AR-conservative scenario per ADR-0040 G2)."""
    monkeypatch.setattr(
        query_route, "get_settings",
        lambda: Settings(_env_file=None, enable_parent_doc_retrieval=True),
    )
    engine = _RecordingEngine([_good_chunk()])
    kb = KbConfig(
        enable_parent_doc_retrieval=False,
        enable_citation_neighbour_images=False,
    )
    client = TestClient(_build_app(engine, _kb_service_with("kb-nopd", kb)))

    resp = client.post("/query", json={"query": "how?", "kb_id": "kb-nopd"})

    assert resp.status_code == 200, resp.text
    assert engine.aggregate_calls == []  # per-KB False wins over global True


# --------------------------------------------------------------------------- #
# CH-007 — /query + /query/stream honour per-KB default_top_k / default_rerank_k
# --------------------------------------------------------------------------- #


def _settings_default(monkeypatch) -> None:
    """Pin the global retrieval defaults (50 / 5) regardless of any repo-root .env."""
    monkeypatch.setattr(query_route, "get_settings", lambda: Settings(_env_file=None))


def test_ch007_query_uses_per_kb_rerank_k_and_overfetch(monkeypatch) -> None:
    """The chat payload sends no top_k → the KB's default_rerank_k (rerank depth) and
    default_top_k (overfetch) reach engine.retrieve."""
    _settings_default(monkeypatch)
    engine = _RecordingEngine([_good_chunk()])
    kb = KbConfig(default_top_k=80, default_rerank_k=20, enable_citation_neighbour_images=False)
    client = TestClient(_build_app(engine, _kb_service_with("kb-tk", kb)))

    resp = client.post("/query", json={"query": "how?", "kb_id": "kb-tk"})

    assert resp.status_code == 200, resp.text
    assert engine.retrieve_calls == [{"top_k": 20, "overfetch": 80}]


def test_ch007_explicit_per_query_top_k_overrides_per_kb(monkeypatch) -> None:
    """An explicit per-query top_k (eval harness / tests) beats the KB default."""
    _settings_default(monkeypatch)
    engine = _RecordingEngine([_good_chunk()])
    kb = KbConfig(default_top_k=80, default_rerank_k=20, enable_citation_neighbour_images=False)
    client = TestClient(_build_app(engine, _kb_service_with("kb-tk2", kb)))

    resp = client.post(
        "/query",
        json={"query": "how?", "kb_id": "kb-tk2", "top_k_retrieval": 12, "top_k_rerank": 3},
    )

    assert resp.status_code == 200, resp.text
    assert engine.retrieve_calls == [{"top_k": 3, "overfetch": 12}]


def test_ch007_default_kb_is_non_regression(monkeypatch) -> None:
    """A KB at the W2 baseline (50 / 5) reaches the engine with the unchanged defaults."""
    _settings_default(monkeypatch)
    engine = _RecordingEngine([_good_chunk()])
    kb = KbConfig(enable_citation_neighbour_images=False)  # default_top_k=50, default_rerank_k=5
    client = TestClient(_build_app(engine, _kb_service_with("kb-base", kb)))

    resp = client.post("/query", json={"query": "how?", "kb_id": "kb-base"})

    assert resp.status_code == 200, resp.text
    assert engine.retrieve_calls == [{"top_k": 5, "overfetch": 50}]


def test_ch007_query_stream_uses_per_kb_rerank_k_and_overfetch(monkeypatch) -> None:
    """The stream route resolves the SAME EffectiveConfig and passes the per-KB
    rerank depth + overfetch to engine.retrieve (parity with /query)."""
    _settings_default(monkeypatch)
    engine = _RecordingEngine([_good_chunk()])
    kb = KbConfig(default_top_k=80, default_rerank_k=20, enable_citation_neighbour_images=False)
    client = TestClient(_build_app(engine, _kb_service_with("kb-stream", kb)))

    resp = client.post("/query/stream", json={"query": "how?", "kb_id": "kb-stream"})

    assert resp.status_code == 200, resp.text
    assert engine.retrieve_calls == [{"top_k": 20, "overfetch": 80}]
