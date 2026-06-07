"""W9 D4 F5.2 cont — `/query` route observe_async wire integration test.

Per W9 plan §2 F5.2 + W9 D2 next-steps proposal:wire `@observe_async` to the
`/query` route handler so each request produces a single hierarchical
Langfuse trace with synthesizer / retrieval / crag.refine generations as
nested children(rather than independent root-level traces)。

This test reuses the W8 D4 `_build_smoke_app` mocked-engine pattern from
`test_e1_e5_e12_smoke.py` but adds a fake Langfuse client to assert the
top-level `api.query` trace event fires with the expected metadata captured
from `QueryResponse` fields。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from unittest.mock import MagicMock

import pytest
import structlog
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.auth import get_current_user
from api.auth.models import AuthenticatedUser
from api.error_handlers import register_error_handlers
from api.middleware import AuditLogMiddleware, RateLimitMiddleware, reset_rate_limiter
from api.routes import query as query_route
from observability import langfuse_tracer
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
class _SynthOutcome:
    answer: str
    citation_ids: list[str]
    deployment: str
    latency_ms: int
    refused: bool
    # W32 F1.8 mock SynthesisResult.expanded_neighbor_chunks field (default empty list)
    expanded_neighbor_chunks: list = field(default_factory=list)


class _MockEngine:
    def __init__(self, chunks: list[_Chunk]):
        self._chunks = chunks

    async def retrieve(self, *, query: str, kb_id: str, top_k: int,
                       **_kwargs: object) -> _RetrievalResult:
        # **_kwargs swallows production retrieve() signature additions
        # (W39 F2 mode, filter_clause, rerank — propagated from /query route).
        return _RetrievalResult(chunks=self._chunks, reranked=True, total_latency_ms=42)


class _MockSynth:
    def __init__(self, *, answer: str, refused: bool):
        self._answer = answer
        self._refused = refused

    async def synthesize(
        self,
        query: str,
        chunks: list[_Chunk],
        *,
        engine: object = None,  # W32 F1.1.a mock signature accept new kwargs (unused)
        kb_id: str | None = None,
        effective_config: object = None,  # W43 F1.5 — per-KB resolved config (unused in mock)
        detail_level: str = "concise",  # CH-006 — route passes this; mock must accept it
    ) -> _SynthOutcome:
        return _SynthOutcome(
            answer=self._answer,
            citation_ids=[],
            deployment="gpt-5-5-mock",
            latency_ms=84,
            refused=self._refused,
        )


@pytest.fixture(autouse=True)
def _bridge_structlog_and_reset_singleton() -> None:
    """Bridge structlog → stdlib so caplog captures observe events,
    + reset Langfuse singleton between tests。
    """
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
    )
    langfuse_tracer._set_langfuse_client_for_tests(None)
    yield
    langfuse_tracer._set_langfuse_client_for_tests(None)


def _build_app(
    chunks: list[_Chunk],
    synth: _MockSynth | None,
) -> FastAPI:
    settings = Settings(feature_auth_mock=True, rate_limit_enabled=True)
    reset_rate_limiter()

    app = FastAPI()
    register_error_handlers(app)
    app.add_middleware(RateLimitMiddleware, settings=settings, protected_prefixes=("/query",))
    app.add_middleware(AuditLogMiddleware, settings=settings, protected_prefixes=("/query",))
    app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(
        oid="test-oid", tid="test-tid",
        preferred_username="t@ekp.local", is_mock=True,
    )
    app.state.retrieval_engine = _MockEngine(chunks)
    app.state.synthesizer = synth
    app.state.crag_loop = None
    app.include_router(query_route.router)
    return app


def _bearer() -> dict[str, str]:
    return {"Authorization": "Bearer dev-token"}


def _payload() -> dict[str, Any]:
    return {"query": "How do I configure double-sided printing?", "kb_id": "drive_user_manuals"}


def _good_chunks() -> list[_Chunk]:
    return [
        _Chunk(
            score=0.9,
            fields={"chunk_id": "doc_a__intro_001", "chunk_title": "Intro", "chunk_text": "Real."},
        )
    ]


def test_query_route_succeeds_with_observe_wrapper_and_no_langfuse() -> None:
    """FastAPI signature introspection compat — wrapped route returns 200 OK
    with no Langfuse client(local dev / CI baseline)."""
    app = _build_app(_good_chunks(), _MockSynth(answer="ok", refused=False))
    client = TestClient(app)

    resp = client.post("/query", headers=_bearer(), json=_payload())

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["answer"] == "ok"
    assert body["model_used"] == "gpt-5-5-mock"
    assert body["reranker_used"] == "cohere-v4.0-pro"  # ADR-0012 production lock
    assert body["refused"] is False


def test_query_route_emits_top_level_trace_when_langfuse_wired() -> None:
    """Wrapper fires `client.trace(name="api.query", ...)` with metadata
    captured from QueryResponse fields(latency_ms / model_used / reranker_used
    / refused / crag_triggered / crag_iterations)。"""
    fake_client = MagicMock()
    langfuse_tracer._set_langfuse_client_for_tests(fake_client)

    app = _build_app(_good_chunks(), _MockSynth(answer="ok", refused=False))
    client = TestClient(app)

    resp = client.post("/query", headers=_bearer(), json=_payload())
    assert resp.status_code == 200

    # Filter trace calls for the top-level api.query span
    api_query_calls = [
        c for c in fake_client.trace.call_args_list
        if c.kwargs.get("name") == "api.query"
    ]
    assert len(api_query_calls) == 1, fake_client.trace.call_args_list
    kwargs = api_query_calls[0].kwargs
    assert kwargs["output"] == {"status": "ok"}
    md = kwargs["metadata"]
    assert "duration_ms" in md
    assert md["model_used"] == "gpt-5-5-mock"
    assert md["reranker_used"] == "cohere-v4.0-pro"  # ADR-0012 production lock
    assert md["refused"] is False
    assert md["crag_triggered"] is False
    assert md["crag_iterations"] == 0


def test_query_route_observe_captures_refused_and_latency() -> None:
    """Refused answer surfaces in observe metadata for downstream Q014-style
    OOS pattern analysis。"""
    fake_client = MagicMock()
    langfuse_tracer._set_langfuse_client_for_tests(fake_client)

    chunks = [_Chunk(score=0.32, fields={"chunk_id": "x", "chunk_title": "T", "chunk_text": "C"})]
    synth = _MockSynth(answer="I cannot answer that", refused=True)
    app = _build_app(chunks, synth)
    client = TestClient(app)

    resp = client.post(
        "/query",
        headers=_bearer(),
        json={"query": "airspeed of unladen swallow", "kb_id": "drive"},
    )
    assert resp.status_code == 200

    api_query_calls = [
        c for c in fake_client.trace.call_args_list
        if c.kwargs.get("name") == "api.query"
    ]
    assert len(api_query_calls) == 1
    md = api_query_calls[0].kwargs["metadata"]
    assert md["refused"] is True


def test_query_route_signature_preserved_for_fastapi_depends() -> None:
    """Critical — FastAPI introspects endpoint signature via `inspect.signature`
    to wire Pydantic body / Request injection。`functools.wraps` __wrapped__
    chain must preserve param names so QueryRequest body validation fires。"""
    import inspect

    sig = inspect.signature(query_route.query)
    params = list(sig.parameters)
    # W43 F1.3 — signature gained `service: KbServiceDep` so the route can resolve
    # the per-KB EffectiveConfig (ADR-0040). FastAPI introspection must still see
    # all three params through the @observe_async __wrapped__ chain.
    assert params == ["payload", "request", "service"], f"signature drift: {sig}"


def test_query_route_traceback_not_leaked_on_engine_failure() -> None:
    """observe wrapper logs stage_failed but the existing 502 envelope path
    in query.py still fires(traceback redaction preserved per W7 D4 F4.1)."""
    fake_client = MagicMock()
    langfuse_tracer._set_langfuse_client_for_tests(fake_client)

    class _FailingEngine:
        async def retrieve(self, *, query: str, kb_id: str, top_k: int,
                           **_kwargs: object) -> Any:
            raise ConnectionError("upstream Azure Search down")

    app = _build_app([], None)
    app.state.retrieval_engine = _FailingEngine()
    client = TestClient(app)

    resp = client.post("/query", headers=_bearer(), json=_payload())
    # 502 envelope from query.py:_engine_or_503 / except path
    assert resp.status_code == 502
    assert "Traceback" not in resp.text
    assert "site-packages" not in resp.text

    # observe wrapper should ALSO have fired with error status — but the trace
    # call may NOT happen for HTTPException because FastAPI catches it before
    # observe's exception path. The test simply asserts no Traceback leak +
    # 502 envelope preserved (the wrapper's own stage_failed log line goes to
    # structlog regardless of FastAPI exception handling).
