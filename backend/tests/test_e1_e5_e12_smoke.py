"""W8 D4 F4 smoke substitute — E1 + E5 + E12 graceful UX coverage.

Per W08-beta-deploy-sprint2 plan §2 F4(LIVE smoke cascade)acceptance:

  - E1: OOS query 拒答 → 200 + refused=true + UI refusal message
  - E5: LLM API timeout → 502/503/504 envelope + retry hint
  - E12: chunk_id collision across KBs → namespace isolation preserved

This is the W8 D4 substitute — full middleware chain exercised against
an in-memory FastAPI app(`api.server.app`)with retrieval / synthesis
mocked. Differs from F1.7-mock(W7 D5)by exercising the actual
`/query` route + routing engine + crag loop wiring against deterministic
mocks instead of a synthetic `/echo/whoami`.

F4.5 LIVE smoke against a real dev server with Azure cred remains a
W8 carry-over per W7 D5 retro § Carry-overs C5 — pending Chris dev
server availability。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.auth import get_current_user
from api.auth.models import AuthenticatedUser
from api.error_handlers import register_error_handlers
from api.middleware import AuditLogMiddleware, RateLimitMiddleware, reset_rate_limiter
from api.routes import query as query_route
from storage.settings import Settings

# ---------------------------------------------------------------------------
# Lightweight mocks of the retrieval + synthesis surface the /query route
# touches. Only the attributes /query actually reads are populated.
# ---------------------------------------------------------------------------


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
    def __init__(self, *, answer: str, refused: bool, raise_exc: Exception | None = None):
        self._answer = answer
        self._refused = refused
        self._raise = raise_exc

    async def synthesize(
        self,
        query: str,
        chunks: list[_Chunk],
        *,
        engine: object = None,  # W32 F1.1.a mock signature accept new kwargs (unused)
        kb_id: str | None = None,
    ) -> _SynthOutcome:
        if self._raise is not None:
            raise self._raise
        return _SynthOutcome(
            answer=self._answer,
            citation_ids=[],
            deployment="gpt-5.5-mock",
            latency_ms=84,
            refused=self._refused,
        )


def _build_smoke_app(
    *,
    chunks: list[_Chunk],
    synth: _MockSynth | None,
    rate_limit_per_minute: int = 100,
) -> FastAPI:
    """Reconstruct production wiring with mocked engine + synthesizer."""
    settings = Settings(
        feature_auth_mock=True,
        rate_limit_enabled=True,
        rate_limit_per_minute=rate_limit_per_minute,
        rate_limit_concurrent=5,
    )
    reset_rate_limiter()

    app = FastAPI()
    register_error_handlers(app)
    app.add_middleware(
        RateLimitMiddleware,
        settings=settings,
        protected_prefixes=("/query", "/kb"),
    )
    app.add_middleware(
        AuditLogMiddleware,
        settings=settings,
        protected_prefixes=("/query", "/kb"),
    )

    # Override auth Depends with a fixed mock user — keeps test focused on
    # E1/E5/E12 rather than re-litigating mock_msal.
    app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(
        oid="smoke-user-001",
        tid="smoke-tenant",
        preferred_username="smoke@ekp.local",
        is_mock=True,
    )

    app.state.retrieval_engine = _MockEngine(chunks)
    app.state.synthesizer = synth
    app.state.crag_loop = None  # F4 smoke focuses on first-pass; CRAG covered W4

    app.include_router(query_route.router, dependencies=[])
    return app


def _bearer() -> dict[str, str]:
    # Auth Depends is overridden; bearer token still required by middleware
    # identity resolution for rate-key + audit-tag.
    return {"Authorization": "Bearer dev-token"}


def _request_payload(query: str) -> dict[str, Any]:
    return {"query": query, "kb_id": "drive_user_manuals"}


# ---------------------------------------------------------------------------
# E1 — Out-of-scope query → grounded refusal, status 200 + refused=true
# ---------------------------------------------------------------------------


def test_e1_oos_query_returns_grounded_refusal_with_200() -> None:
    chunks = [
        _Chunk(
            score=0.32,  # below typical relevance threshold
            fields={
                "chunk_id": "irrelevant_001",
                "chunk_title": "Unrelated topic",
                "chunk_text": "This text has nothing to do with the query.",
            },
        ),
    ]
    synth = _MockSynth(
        answer="I cannot answer that question with the available documents.",
        refused=True,
    )
    app = _build_smoke_app(chunks=chunks, synth=synth)
    client = TestClient(app)

    response = client.post(
        "/query",
        headers=_bearer(),
        json=_request_payload("What is the airspeed velocity of an unladen swallow?"),
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["refused"] is True
    assert "cannot answer" in body["answer"].lower()
    # E1 acceptance: NO ApiError envelope on grounded refusal — refusal is a
    # non-error path per error-cases-E1-E14.md §2.
    assert "error" not in body


# ---------------------------------------------------------------------------
# E5 — LLM API timeout / synthesis failure → ApiError envelope
# ---------------------------------------------------------------------------


def test_e5_llm_timeout_returns_envelope_502() -> None:
    chunks = [
        _Chunk(
            score=0.85,
            fields={
                "chunk_id": "doc_a__intro_001",
                "chunk_title": "Introduction",
                "chunk_text": "Real EKP content.",
            },
        ),
    ]

    class _Timeout(Exception):
        pass

    synth = _MockSynth(answer="", refused=False, raise_exc=_Timeout("LLM call exceeded 30s"))
    app = _build_smoke_app(chunks=chunks, synth=synth)
    client = TestClient(app)

    response = client.post("/query", headers=_bearer(), json=_request_payload("How do I X?"))

    assert response.status_code == 502
    body = response.json()
    # F4.1 envelope contract preserved end-to-end.
    assert body["error"]["code"] == "pipeline.retrieval_failed"
    assert body["error"]["actionable_hint"] is not None
    # No traceback / file path leaked (type name is acceptable per W2/W3
    # query.py design — surfaces the exception class for ops debugging).
    assert "Traceback" not in response.text
    assert "site-packages" not in response.text


def test_e5_synthesizer_unavailable_returns_envelope_with_safe_message() -> None:
    """Synthesizer init failure path — server.state.synthesizer = None falls
    back to retrieval-only response (W2 baseline behavior preserved).
    """
    chunks = [
        _Chunk(
            score=0.9,
            fields={
                "chunk_id": "doc_a__chunk_001",
                "chunk_title": "Real",
                "chunk_text": "Content.",
            },
        ),
    ]
    app = _build_smoke_app(chunks=chunks, synth=None)
    client = TestClient(app)

    response = client.post("/query", headers=_bearer(), json=_request_payload("Hello?"))

    # 200 retrieval-only fallback, NOT an error — graceful degradation.
    assert response.status_code == 200
    body = response.json()
    assert body["model_used"] == "(retrieval-only)"
    assert "[W2 baseline" in body["answer"]


# ---------------------------------------------------------------------------
# E12 — chunk_id collision across KBs → namespaced retrieval correctness
# ---------------------------------------------------------------------------


def test_e12_chunk_id_collision_resolves_via_kb_namespace() -> None:
    """Two chunks with identical raw chunk_id but different docs/KBs are
    surfaced through the API as distinct entries — the kb_id + doc_id
    namespace prefix in retrieval results prevents the answer from
    accidentally citing the wrong source.
    """
    # Both chunks share raw chunk_id "intro_001" but are namespaced via the
    # `kb_id__doc_id__chunk_id` convention enforced at ingestion (W2 D2 F2).
    chunks = [
        _Chunk(
            score=0.95,
            fields={
                "chunk_id": "drive_user_manuals__doc_a__intro_001",
                "chunk_title": "Doc A intro",
                "chunk_text": "Doc A intro text.",
            },
        ),
        _Chunk(
            score=0.92,
            fields={
                "chunk_id": "drive_user_manuals__doc_b__intro_001",
                "chunk_title": "Doc B intro",
                "chunk_text": "Doc B intro text.",
            },
        ),
    ]
    synth = _MockSynth(
        answer="Doc A intro [drive_user_manuals__doc_a__intro_001].",
        refused=False,
    )
    app = _build_smoke_app(chunks=chunks, synth=synth)
    client = TestClient(app)

    response = client.post("/query", headers=_bearer(), json=_request_payload("intro"))

    assert response.status_code == 200
    body = response.json()
    chunk_ids = [c["chunk_id"] for c in body["retrieved_chunks"]]
    # Both namespaced ids surfaced — no collision merged into a single entry.
    assert "drive_user_manuals__doc_a__intro_001" in chunk_ids
    assert "drive_user_manuals__doc_b__intro_001" in chunk_ids
    assert len(set(chunk_ids)) == 2


# ---------------------------------------------------------------------------
# F3.5 audit smoke — full chain emits identity+request_id under load
# ---------------------------------------------------------------------------


def test_f3_5_audit_chain_under_burst(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """5-query burst exercises auth → rate-limit → audit → /query → response;
    each query produces an audit_log row tagged with the mock identity.
    """
    import logging

    import structlog

    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
    )
    caplog.set_level(logging.INFO, logger="ekp.audit")

    chunks = [
        _Chunk(
            score=0.88,
            fields={"chunk_id": "x", "chunk_title": "T", "chunk_text": "C"},
        ),
    ]
    synth = _MockSynth(answer="ans", refused=False)
    app = _build_smoke_app(chunks=chunks, synth=synth, rate_limit_per_minute=10)
    client = TestClient(app)

    for i in range(5):
        client.post(
            "/query",
            headers={**_bearer(), "X-Request-ID": f"smoke-{i:03d}"},
            json=_request_payload("seed"),
        )

    audit_lines = [r.getMessage() for r in caplog.records if r.name == "ekp.audit"]
    blob = "\n".join(audit_lines)
    # Audit middleware re-runs `authenticate_mock` against the bearer token
    # — which always resolves to Settings.auth_mock_* defaults regardless of
    # the route-level Depends override. This is correct production behaviour:
    # audit identity comes from the validated token, not from a per-request
    # override. The Settings default oid + tid surface here.
    settings = Settings()
    assert settings.auth_mock_oid in blob
    assert settings.auth_mock_tid in blob
    assert "POST /query" in blob
    # All 5 request_ids round-tripped.
    for i in range(5):
        assert f"smoke-{i:03d}" in blob
