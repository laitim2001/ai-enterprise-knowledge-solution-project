"""Debug trace endpoint tests (W16 F5.5 CO_W15_F2 closure).

Per W16 plan F5.5 acceptance criteria + CLAUDE.md §5.6 H6 + Decision D.2
(full Langfuse SDK integration). Coverage:
- Happy path: Langfuse client wired + trace exists → ok status + stages
- Trace not found: client returns None data → status="not_found"
- Langfuse not configured: client = None → status="langfuse_not_configured"
- SDK method missing: client lacks fetch_trace → status="sdk_method_missing"
- Fetch raises: client.fetch_trace exception → status="fetch_failed"
- trace_url pattern always returned (frontend deep-link CTA)
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routes import debug as debug_routes
from observability import langfuse_tracer


def _build_app() -> FastAPI:
    app = FastAPI()
    app.include_router(debug_routes.router)
    return app


def test_get_trace_happy_path_with_stages() -> None:
    """Langfuse client wired + trace has observations → ok + stages populated."""
    start = datetime.now(UTC)
    end = start + timedelta(milliseconds=150)

    fake_observations = [
        SimpleNamespace(
            name="retrieval.retrieve",
            type="SPAN",
            start_time=start,
            end_time=end,
            usage=None,
            model=None,
            level="DEFAULT",
            latency_ms=150,
        ),
        SimpleNamespace(
            name="api.query.synthesize",
            type="GENERATION",
            start_time=start,
            end_time=end + timedelta(milliseconds=2000),
            usage=SimpleNamespace(input=1500, output=350),
            model="gpt-5-5",
            level="DEFAULT",
            latency_ms=2000,
        ),
    ]
    fake_trace_data = SimpleNamespace(observations=fake_observations)
    fake_response = SimpleNamespace(data=fake_trace_data)

    fake_client = MagicMock()
    fake_client.fetch_trace = MagicMock(return_value=fake_response)
    langfuse_tracer._set_langfuse_client_for_tests(fake_client)

    try:
        app = _build_app()
        client = TestClient(app)
        resp = client.get("/debug/trace/trace-abc-123")
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["trace_id"] == "trace-abc-123"
        assert body["status"] == "ok"
        assert "trace/trace-abc-123" in body["trace_url"]
        assert len(body["stages"]) == 2
        assert body["stages"][0]["name"] == "retrieval.retrieve"
        assert body["stages"][1]["model"] == "gpt-5-5"
        assert body["stages"][1]["input_tokens"] == 1500
        assert body["stages"][1]["output_tokens"] == 350
        assert body["total_latency_ms"] == 150 + 2000
        assert body["total_input_tokens"] == 1500
        assert body["total_output_tokens"] == 350
    finally:
        langfuse_tracer._set_langfuse_client_for_tests(None)


def test_get_trace_not_found_status_when_data_none() -> None:
    """client.fetch_trace returns response with data=None → status='not_found'."""
    fake_response = SimpleNamespace(data=None)
    fake_client = MagicMock()
    fake_client.fetch_trace = MagicMock(return_value=fake_response)
    langfuse_tracer._set_langfuse_client_for_tests(fake_client)

    try:
        app = _build_app()
        client = TestClient(app)
        resp = client.get("/debug/trace/trace-missing")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "not_found"
        assert body["trace_id"] == "trace-missing"
        assert "trace/trace-missing" in body["trace_url"]
        assert body["stages"] == []
    finally:
        langfuse_tracer._set_langfuse_client_for_tests(None)


def test_get_trace_langfuse_not_configured() -> None:
    """No Langfuse client → status='langfuse_not_configured' + trace_url pattern only."""
    langfuse_tracer._set_langfuse_client_for_tests(None)
    app = _build_app()
    client = TestClient(app)
    resp = client.get("/debug/trace/trace-x")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "langfuse_not_configured"
    assert body["trace_id"] == "trace-x"
    assert "trace/trace-x" in body["trace_url"]
    assert body["stages"] == []
    assert "trace_url pattern returned" in body["note"]


def test_get_trace_sdk_method_missing() -> None:
    """Langfuse client lacks fetch_trace method → status='sdk_method_missing'."""
    fake_client = SimpleNamespace()  # no fetch_trace attribute
    langfuse_tracer._set_langfuse_client_for_tests(fake_client)

    try:
        app = _build_app()
        client = TestClient(app)
        resp = client.get("/debug/trace/trace-y")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "sdk_method_missing"
        assert "trace/trace-y" in body["trace_url"]
    finally:
        langfuse_tracer._set_langfuse_client_for_tests(None)


def test_get_trace_fetch_raises_returns_fetch_failed_status() -> None:
    """client.fetch_trace raises → status='fetch_failed' + error in note."""
    fake_client = MagicMock()
    fake_client.fetch_trace = MagicMock(side_effect=ConnectionError("Langfuse unreachable"))
    langfuse_tracer._set_langfuse_client_for_tests(fake_client)

    try:
        app = _build_app()
        client = TestClient(app)
        resp = client.get("/debug/trace/trace-err")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "fetch_failed"
        assert "ConnectionError" in body["note"]
        assert "trace/trace-err" in body["trace_url"]
    finally:
        langfuse_tracer._set_langfuse_client_for_tests(None)


def test_get_trace_error_level_observation_marked_error_status() -> None:
    """Observation with level='ERROR' → stage status='error' (others 'ok')."""
    start = datetime.now(UTC)
    end = start + timedelta(milliseconds=100)

    fake_observations = [
        SimpleNamespace(
            name="retrieval.retrieve",
            type="SPAN",
            start_time=start,
            end_time=end,
            usage=None,
            model=None,
            level="ERROR",  # → status='error'
            latency_ms=100,
        ),
    ]
    fake_response = SimpleNamespace(data=SimpleNamespace(observations=fake_observations))

    fake_client = MagicMock()
    fake_client.fetch_trace = MagicMock(return_value=fake_response)
    langfuse_tracer._set_langfuse_client_for_tests(fake_client)

    try:
        app = _build_app()
        client = TestClient(app)
        resp = client.get("/debug/trace/trace-with-err")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"  # trace fetch ok
        assert body["stages"][0]["status"] == "error"  # but stage flagged
    finally:
        langfuse_tracer._set_langfuse_client_for_tests(None)
