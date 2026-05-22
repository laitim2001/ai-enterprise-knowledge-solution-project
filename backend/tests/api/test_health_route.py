"""W20 F2.2 — `GET /health` per-component payload tests (per W19 F2 §3.1 item 1).

Covers `backend/api/routes/health.py`:
- All-green path (every singleton wired) → top-level `ok`
- Partial degraded (one component singleton missing) → top-level `degraded`
- not_configured branches (Cohere optional / no DATABASE_URL) → still top-level `ok`
- Langfuse client state branches (configured vs not)

The route is config-state-only (Wave A scope) — no real I/O pings, so tests are
deterministic by swapping `app.state.*` attributes + monkeypatching
`get_langfuse_client` / `get_settings`. Acceptance ref: W20 plan F2 + CLAUDE.md §3.1 H6.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routes import health as health_routes


def _build_app(
    *,
    retrieval_engine: Any | None = None,
    embedder: Any | None = None,
) -> FastAPI:
    """Build a minimal FastAPI instance with the health router + the singletons
    we want to expose via `app.state` (the real lifespan is bypassed)."""
    app = FastAPI()
    app.include_router(health_routes.router)
    app.state.retrieval_engine = retrieval_engine
    app.state.embedder = embedder
    return app


@pytest.fixture(autouse=True)
def _clean_settings_cache() -> Iterator[None]:
    """`get_settings()` is `@lru_cache`d — clear between tests so monkeypatched
    `database_url` doesn't leak across cases."""
    from storage.settings import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


# --------------------------------------------------------------------------- #
# All-green path
# --------------------------------------------------------------------------- #


def test_health_all_green(monkeypatch: pytest.MonkeyPatch) -> None:
    """Every singleton wired + Postgres configured + Cohere wired + Langfuse client = top-level `ok`."""
    engine = MagicMock(name="RetrievalEngine")
    engine.reranker = MagicMock(name="CohereReranker")
    embedder = MagicMock(name="AzureOpenAIEmbedder")

    monkeypatch.setattr(
        health_routes,
        "get_langfuse_client",
        lambda: MagicMock(name="LangfuseClient"),
    )
    monkeypatch.setenv("DATABASE_URL", "postgresql://test/test")

    app = _build_app(retrieval_engine=engine, embedder=embedder)
    client = TestClient(app)

    resp = client.get("/health")
    assert resp.status_code == 200

    body = resp.json()
    assert body["status"] == "ok"
    assert body["components"]["azure_search"]["status"] == "ok"
    assert body["components"]["azure_openai"]["status"] == "ok"
    assert body["components"]["cohere"]["status"] == "ok"
    assert body["components"]["langfuse"]["status"] == "ok"
    assert body["components"]["postgres"]["status"] == "ok"

    # Wave A scope — latency_ms always None (no real I/O ping yet)
    for comp in body["components"].values():
        assert comp["latency_ms"] is None


# --------------------------------------------------------------------------- #
# Configured-but-degraded branches (singleton init failed at lifespan startup)
# --------------------------------------------------------------------------- #


def test_health_degraded_when_retrieval_engine_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`retrieval_engine` is None → azure_search + cohere both `degraded` → top-level `degraded`."""
    monkeypatch.setattr(health_routes, "get_langfuse_client", lambda: None)

    app = _build_app(
        retrieval_engine=None,
        embedder=MagicMock(name="AzureOpenAIEmbedder"),
    )
    client = TestClient(app)

    resp = client.get("/health")
    assert resp.status_code == 200

    body = resp.json()
    assert body["status"] == "degraded"
    assert body["components"]["azure_search"]["status"] == "degraded"
    # Cohere also flips to degraded because the engine wrapping it is gone
    assert body["components"]["cohere"]["status"] == "degraded"
    # azure_openai still ok (embedder wired)
    assert body["components"]["azure_openai"]["status"] == "ok"


def test_health_degraded_when_embedder_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`embedder` is None → azure_openai `degraded` → top-level `degraded`."""
    engine = MagicMock(name="RetrievalEngine")
    engine.reranker = MagicMock(name="CohereReranker")
    monkeypatch.setattr(
        health_routes, "get_langfuse_client", lambda: MagicMock()
    )

    app = _build_app(retrieval_engine=engine, embedder=None)
    client = TestClient(app)

    body = client.get("/health").json()
    assert body["status"] == "degraded"
    assert body["components"]["azure_openai"]["status"] == "degraded"
    assert body["components"]["azure_search"]["status"] == "ok"


# --------------------------------------------------------------------------- #
# `not_configured` branches — optional components (don't trip `degraded`)
# --------------------------------------------------------------------------- #


def test_health_cohere_not_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    """Cohere reranker is optional per Q5 — `engine.reranker is None` → cohere `not_configured`
    and top-level stays `ok`."""
    engine = MagicMock(name="RetrievalEngine")
    engine.reranker = None
    embedder = MagicMock(name="AzureOpenAIEmbedder")
    monkeypatch.setattr(
        health_routes, "get_langfuse_client", lambda: MagicMock()
    )
    monkeypatch.setenv("DATABASE_URL", "postgresql://test/test")

    app = _build_app(retrieval_engine=engine, embedder=embedder)
    client = TestClient(app)

    body = client.get("/health").json()
    # not_configured shouldn't trip the top-level roll-up to `degraded`
    assert body["status"] == "ok"
    assert body["components"]["cohere"]["status"] == "not_configured"


def test_health_postgres_not_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    """No DATABASE_URL → in-memory fallback per ADR-0023 → postgres `not_configured` (not `degraded`)."""
    engine = MagicMock(name="RetrievalEngine")
    engine.reranker = MagicMock(name="CohereReranker")
    embedder = MagicMock(name="AzureOpenAIEmbedder")
    monkeypatch.setattr(
        health_routes, "get_langfuse_client", lambda: MagicMock()
    )
    # Empty (not delete) — the dev `.env` may carry DATABASE_URL; an empty env
    # var overrides the `.env` file value, `delenv` would expose it. BUG-008.
    monkeypatch.setenv("DATABASE_URL", "")

    app = _build_app(retrieval_engine=engine, embedder=embedder)
    client = TestClient(app)

    body = client.get("/health").json()
    assert body["status"] == "ok"
    assert body["components"]["postgres"]["status"] == "not_configured"
    assert (
        body["components"]["postgres"]["detail"]
        and "in-memory" in body["components"]["postgres"]["detail"].lower()
    )


def test_health_langfuse_not_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`get_langfuse_client()` returns None when LANGFUSE keys aren't set → langfuse `not_configured`."""
    engine = MagicMock(name="RetrievalEngine")
    engine.reranker = MagicMock(name="CohereReranker")
    embedder = MagicMock(name="AzureOpenAIEmbedder")
    monkeypatch.setattr(health_routes, "get_langfuse_client", lambda: None)
    monkeypatch.setenv("DATABASE_URL", "postgresql://test/test")

    app = _build_app(retrieval_engine=engine, embedder=embedder)
    client = TestClient(app)

    body = client.get("/health").json()
    assert body["status"] == "ok"
    assert body["components"]["langfuse"]["status"] == "not_configured"


# --------------------------------------------------------------------------- #
# Response schema shape — the dashboard relies on the keys being stable
# --------------------------------------------------------------------------- #


def test_health_response_schema(monkeypatch: pytest.MonkeyPatch) -> None:
    """The 5-component key set + the `{status, latency_ms, detail}` shape is the contract
    the `/dashboard` System health card depends on (W20 F2 ADR-0030 absorbed scope)."""
    monkeypatch.setattr(health_routes, "get_langfuse_client", lambda: None)
    # Empty (not delete) — the dev `.env` may carry DATABASE_URL; an empty env
    # var overrides the `.env` file value, `delenv` would expose it. BUG-008.
    monkeypatch.setenv("DATABASE_URL", "")

    app = _build_app(retrieval_engine=None, embedder=None)
    client = TestClient(app)

    body = client.get("/health").json()
    assert set(body.keys()) == {"status", "components"}
    assert set(body["components"].keys()) == {
        "azure_search",
        "azure_openai",
        "cohere",
        "langfuse",
        "postgres",
    }
    for comp in body["components"].values():
        assert set(comp.keys()) == {"status", "latency_ms", "detail"}
