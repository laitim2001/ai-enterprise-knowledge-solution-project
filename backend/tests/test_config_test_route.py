"""W43 F2.5 — config-test harness route (ADR-0040 §Decision 3).

Asserts the harness (a) runs N times, (b) aggregates presentation counters with a
variance band, (c) honours the DRAFT config through the shared execute_query_pipeline
(image cap), (d) supports draft-vs-saved A/B, (e) 404s an unknown KB. A mock synth
returns fixed citation_ids over image-bearing chunks so counts are deterministic.
"""

from __future__ import annotations

import asyncio
import json
import threading
from dataclasses import dataclass, field
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routes import config_test as ct_route
from api.routes import query as query_route
from api.schemas.kb import KbConfig, KbCreate
from kb_management.service import KBService, get_kb_service
from kb_management.storage import InMemoryKBBackend


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
    refused: bool
    latency_ms: int
    deployment: str
    expanded_neighbor_chunks: list = field(default_factory=list)


def _imgs_json(n: int, prefix: str) -> str:
    return json.dumps([
        {
            "blob_url": f"blob://{prefix}-{i}", "alt_text": "",
            "checksum_sha256": f"sha-{prefix}-{i}", "width": 10, "height": 10,
            "source_section": [],
        }
        for i in range(n)
    ])


def _chunks() -> list[_Chunk]:
    return [
        _Chunk(0.9, {
            "chunk_id": "chunk-a", "chunk_title": "A", "chunk_text": "x",
            "doc_id": "d", "doc_title": "D", "doc_format": "docx", "chunk_index": 1,
            "section_path": ["Doc", "A"], "embedded_images_json": _imgs_json(3, "a"),
        }),
        _Chunk(0.8, {
            "chunk_id": "chunk-b", "chunk_title": "B", "chunk_text": "y",
            "doc_id": "d", "doc_title": "D", "doc_format": "docx", "chunk_index": 2,
            "section_path": ["Doc", "B"], "embedded_images_json": _imgs_json(2, "b"),
        }),
    ]


class _Engine:
    def __init__(self, chunks: list[_Chunk]) -> None:
        self._c = chunks

    async def retrieve(self, *, query: str, kb_id: str, top_k: int, **_kw: object) -> _RR:
        return _RR(self._c, True, 10)

    async def expand_context_for_chunks(
        self, chunks: list[_Chunk], *, kb_id: str,
    ) -> tuple[list[_Chunk], dict]:
        return chunks, {}


class _MockSynth:
    async def synthesize(
        self, query: str, chunks: list[_Chunk], *,
        engine: object = None, kb_id: str | None = None, effective_config: object = None,
        detail_level: str = "concise",  # CH-006 — route passes this; mock must accept it
    ) -> _Synth:
        return _Synth(
            answer="ans [chunk-a][chunk-b]", citation_ids=["chunk-a", "chunk-b"],
            refused=False, latency_ms=5, deployment="gpt-5.5-mock",
        )


def _service(kb_id: str, cfg: KbConfig) -> KBService:
    s = KBService(InMemoryKBBackend())
    asyncio.run(s.create(KbCreate(kb_id=kb_id, name="t", config=cfg)))
    return s


def _app(service: KBService) -> FastAPI:
    app = FastAPI()
    app.state.retrieval_engine = _Engine(_chunks())
    app.state.synthesizer = _MockSynth()
    app.state.crag_loop = None
    app.dependency_overrides[get_kb_service] = lambda: service
    app.include_router(query_route.router)
    app.include_router(ct_route.router)
    return app


@pytest.fixture(autouse=True)
def _no_judge(monkeypatch: pytest.MonkeyPatch) -> None:
    """W48 — default: NO faithfulness judge in tests (deterministic, no network).

    `eval_faithfulness` defaults True, and the route resolves `get_settings()` (real
    .env, which may carry an Azure key), so without this patch the presentation-counter
    tests below would fire a live judge call. The faithfulness tests override this.
    """
    monkeypatch.setattr(ct_route, "make_faithfulness_evaluator", lambda settings: None)


# Draft that disables the expansion side-paths so the mock engine needs no
# list_chunks / aggregate methods — isolates the counts to build_citations + cap.
_ISOLATE = {"enable_parent_doc_retrieval": False, "enable_citation_neighbour_images": False}


def test_config_test_multi_run_counts_and_band() -> None:
    client = TestClient(_app(_service("kb-ct", KbConfig())))
    resp = client.post("/kb/kb-ct/config-test", json={
        "query": "how?", "runs": 3, "draft_config": _ISOLATE,
    })
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["runs"] == 3
    assert len(body["draft"]["runs"]) == 3
    # 2 citations, 3+2 = 5 images, all distinct checksums
    r0 = body["draft"]["runs"][0]
    assert r0["citation_count"] == 2
    assert r0["figure_count_raw"] == 5
    assert r0["figure_count_dedup"] == 5
    # deterministic mock → zero variance band
    assert body["draft"]["figure_count_raw"]["band"] == 0
    assert body["draft"]["citation_count"]["mean"] == 2
    # W51 — distinct cited sections (coverage proxy): chunk-a [Doc,A] + chunk-b [Doc,B] = 2
    assert r0["distinct_sections"] == 2
    assert body["draft"]["distinct_sections"]["mean"] == 2
    assert body["draft"]["distinct_sections"]["band"] == 0
    # per-citation breakdown from the last run
    assert {c["chunk_id"] for c in body["draft"]["per_citation"]} == {"chunk-a", "chunk-b"}


def test_config_test_max_images_cap_applies() -> None:
    client = TestClient(_app(_service("kb-cap", KbConfig())))
    resp = client.post("/kb/kb-cap/config-test", json={
        "query": "how?", "runs": 1,
        "draft_config": {**_ISOLATE, "max_images_per_answer": 2},
    })
    assert resp.status_code == 200, resp.text
    body = resp.json()
    # cap=2 trims cumulative images 5 -> 2; citations still 2 (cap never drops citations)
    assert body["draft"]["runs"][0]["figure_count_raw"] == 2
    assert body["draft"]["runs"][0]["citation_count"] == 2
    assert body["resolved_config"]["max_images_per_answer"] == 2


def test_config_test_compare_to_saved() -> None:
    client = TestClient(_app(_service("kb-ab", KbConfig())))
    resp = client.post("/kb/kb-ab/config-test", json={
        "query": "how?", "runs": 1, "draft_config": _ISOLATE, "compare_to_saved": True,
    })
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["saved"] is not None
    assert len(body["saved"]["runs"]) == 1


def test_config_test_unknown_kb_404() -> None:
    client = TestClient(_app(_service("kb-real", KbConfig())))
    resp = client.post("/kb/kb-missing/config-test", json={"query": "how?", "runs": 1})
    assert resp.status_code == 404


# ── W48 — faithfulness quality axis (ADR-0040 dual-axis) ─────────────────────


def test_config_test_faithfulness_computed(monkeypatch: pytest.MonkeyPatch) -> None:
    """eval_faithfulness (default True) → faithfulness MetricBand on the summary, fed
    each run's answer + retrieved-chunk contexts (W49 — judged per run, not once)."""
    captured: dict[str, object] = {}

    def fake_factory(settings: object):  # noqa: ANN202, ARG001
        def _ev(question: str, answer: str, contexts: list[str]) -> float:
            captured["question"] = question
            captured["answer"] = answer
            captured["contexts"] = contexts
            return 0.95

        return _ev

    monkeypatch.setattr(ct_route, "make_faithfulness_evaluator", fake_factory)
    client = TestClient(_app(_service("kb-faith", KbConfig())))
    resp = client.post("/kb/kb-faith/config-test", json={
        "query": "how?", "runs": 2, "draft_config": _ISOLATE,
    })
    assert resp.status_code == 200, resp.text
    body = resp.json()
    # W49 — faithfulness is now an N-run MetricBand; identical per-run score → band=0.
    faith = body["draft"]["faithfulness"]
    assert faith["mean"] == 0.95
    assert faith["band"] == 0
    # fed the mock synth's answer + the retrieved chunk texts (contexts) of each run
    assert captured["answer"] == "ans [chunk-a][chunk-b]"
    assert captured["contexts"] == ["x", "y"]
    assert captured["question"] == "how?"


def test_config_test_faithfulness_band_over_runs(monkeypatch: pytest.MonkeyPatch) -> None:
    """W49 — faithfulness is judged on EVERY run and aggregated into a band, so the
    quality axis exposes its run-to-run noise (the whole point of 決策 7)."""
    scores = iter([0.9, 0.5, 0.7])
    lock = threading.Lock()  # judge calls run concurrently via asyncio.to_thread

    def fake_factory(settings: object):  # noqa: ANN202, ARG001
        def _ev(question: str, answer: str, contexts: list[str]) -> float:
            with lock:
                return next(scores)

        return _ev

    monkeypatch.setattr(ct_route, "make_faithfulness_evaluator", fake_factory)
    client = TestClient(_app(_service("kb-band", KbConfig())))
    resp = client.post("/kb/kb-band/config-test", json={
        "query": "how?", "runs": 3, "draft_config": _ISOLATE,
    })
    assert resp.status_code == 200, resp.text
    faith = resp.json()["draft"]["faithfulness"]
    # band is order-independent (concurrent runs) — min/max/band over {0.9, 0.5, 0.7}
    assert faith["min"] == 0.5
    assert faith["max"] == 0.9
    assert faith["band"] == pytest.approx(0.4)
    assert faith["mean"] == pytest.approx(0.7)


def test_config_test_faithfulness_n1_band_zero(monkeypatch: pytest.MonkeyPatch) -> None:
    """runs=1 → single judge → band=0 (the frontend then shows a single-shot warning)."""
    monkeypatch.setattr(
        ct_route, "make_faithfulness_evaluator", lambda settings: (lambda q, a, c: 0.8)
    )
    client = TestClient(_app(_service("kb-n1", KbConfig())))
    resp = client.post("/kb/kb-n1/config-test", json={
        "query": "how?", "runs": 1, "draft_config": _ISOLATE,
    })
    assert resp.status_code == 200, resp.text
    faith = resp.json()["draft"]["faithfulness"]
    assert faith == {"min": 0.8, "max": 0.8, "mean": 0.8, "band": 0}


def test_config_test_faithfulness_partial_none(monkeypatch: pytest.MonkeyPatch) -> None:
    """A judge error on some runs (per-call None) → band over the runs that succeeded;
    None only when EVERY run errored."""
    scores = iter([0.9, None, 0.5])
    lock = threading.Lock()

    def fake_factory(settings: object):  # noqa: ANN202, ARG001
        def _ev(question: str, answer: str, contexts: list[str]) -> float | None:
            with lock:
                return next(scores)

        return _ev

    monkeypatch.setattr(ct_route, "make_faithfulness_evaluator", fake_factory)
    client = TestClient(_app(_service("kb-partial", KbConfig())))
    resp = client.post("/kb/kb-partial/config-test", json={
        "query": "how?", "runs": 3, "draft_config": _ISOLATE,
    })
    assert resp.status_code == 200, resp.text
    faith = resp.json()["draft"]["faithfulness"]
    # band over {0.9, 0.5} (the None run dropped)
    assert faith["min"] == 0.5
    assert faith["max"] == 0.9
    assert faith["band"] == pytest.approx(0.4)


def test_config_test_faithfulness_disabled() -> None:
    """eval_faithfulness=False → the judge is never built; faithfulness stays None."""
    client = TestClient(_app(_service("kb-nofaith", KbConfig())))
    resp = client.post("/kb/kb-nofaith/config-test", json={
        "query": "how?", "runs": 1, "draft_config": _ISOLATE, "eval_faithfulness": False,
    })
    assert resp.status_code == 200, resp.text
    assert resp.json()["draft"]["faithfulness"] is None


def test_config_test_faithfulness_graceful_when_evaluator_returns_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An evaluator that yields None (no judge / per-call error contract) → the
    config-test still returns 200 with faithfulness=None (graceful degradation)."""
    monkeypatch.setattr(
        ct_route, "make_faithfulness_evaluator", lambda settings: (lambda q, a, c: None)
    )
    client = TestClient(_app(_service("kb-graceful", KbConfig())))
    resp = client.post("/kb/kb-graceful/config-test", json={
        "query": "how?", "runs": 1, "draft_config": _ISOLATE, "compare_to_saved": True,
    })
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["draft"]["faithfulness"] is None
    assert body["saved"]["faithfulness"] is None
