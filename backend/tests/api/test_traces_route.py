"""W21 F2.2/F2.3 — `GET /traces` index list route tests.

Per W21 plan F2.3 acceptance criteria + CLAUDE.md §5.6 H6 coverage gate.
Sibling to `backend/tests/test_debug_trace.py` (W16 F5.5 /debug/trace/{id});
shares the Langfuse client substitute pattern via
`langfuse_tracer._set_langfuse_client_for_tests`.

Coverage matrix:
  - Happy path (mixed statuses) — error / crag / ok rolled up correctly
  - filter=errors / filter=crag_triggered post-fetch filter behaviour
  - since= ISO 8601 lower-bound filter
  - kb_id= scope filter (metadata + input fallback)
  - Empty Langfuse window (data=[]) — returns 200 + status="ok" + items=[]
  - Pagination (limit + offset slicing + total reflects pre-page filtered count)
  - Graceful degrade — no_client / sdk_method_missing / fetch_failed
  - Field extraction defensiveness — `latency` seconds → ms / observations
    list length → stage_count / totalTokens fallback / cost from totalCost
  - status priority error > crag_triggered > ok
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routes import debug as debug_routes
from observability import langfuse_tracer


def _build_app() -> FastAPI:
    app = FastAPI()
    app.include_router(debug_routes.router)
    return app


def _trace(
    *,
    trace_id: str,
    timestamp: datetime,
    latency_s: float = 0.5,
    name: str = "api.query.run",
    input_payload: Any = None,
    metadata: dict[str, Any] | None = None,
    level: str = "DEFAULT",
    observations: list[str] | None = None,
    total_tokens: int = 0,
    total_cost: float = 0.0,
) -> SimpleNamespace:
    """Construct a Langfuse-shaped trace summary for fixture purposes."""
    return SimpleNamespace(
        id=trace_id,
        timestamp=timestamp,
        latency=latency_s,
        name=name,
        input=input_payload,
        metadata=metadata or {},
        level=level,
        observations=observations or [],
        totalTokens=total_tokens,
        totalCost=total_cost,
    )


def test_list_traces_happy_path_mixed_statuses() -> None:
    """Happy path — 3 traces (ok/error/crag) → all returned with correct rollup."""
    now = datetime.now(UTC)
    fake_traces = [
        _trace(
            trace_id="t-ok",
            timestamp=now - timedelta(minutes=10),
            latency_s=1.2,
            input_payload={"query": "how to set up MFA?", "kb_id": "kb-drive"},
            metadata={"kb_id": "kb-drive"},
            observations=["obs-1", "obs-2", "obs-3"],
            total_tokens=1500,
            total_cost=0.0234,
        ),
        _trace(
            trace_id="t-err",
            timestamp=now - timedelta(minutes=20),
            latency_s=0.3,
            input_payload={"query": "explain F&O ERP rollover"},
            metadata={"status": "error", "kb_id": "kb-drive"},
            level="ERROR",
            observations=["obs-1"],
        ),
        _trace(
            trace_id="t-crag",
            timestamp=now - timedelta(minutes=30),
            latency_s=2.5,
            input_payload={"query": "what is the OQ q14 owner"},
            metadata={"crag_iterations": 2, "kb_id": "kb-drive"},
            observations=["obs-1", "obs-2", "obs-3", "obs-4"],
            total_tokens=3200,
            total_cost=0.0512,
        ),
    ]
    fake_response = SimpleNamespace(data=fake_traces)
    fake_client = MagicMock()
    fake_client.fetch_traces = MagicMock(return_value=fake_response)
    langfuse_tracer._set_langfuse_client_for_tests(fake_client)

    try:
        resp = TestClient(_build_app()).get("/traces")
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["status"] == "ok"
        assert body["total"] == 3
        assert body["limit"] == 50
        assert body["offset"] == 0
        assert len(body["items"]) == 3

        by_id = {item["trace_id"]: item for item in body["items"]}
        assert by_id["t-ok"]["status"] == "ok"
        assert by_id["t-ok"]["duration_ms"] == 1200
        assert by_id["t-ok"]["stage_count"] == 3
        assert by_id["t-ok"]["query_preview"].startswith("how to set up MFA?")
        assert by_id["t-ok"]["total_tokens"] == 1500
        assert by_id["t-ok"]["cost_usd"] == 0.0234
        assert by_id["t-ok"]["kb_id"] == "kb-drive"

        assert by_id["t-err"]["status"] == "error"
        assert by_id["t-err"]["stage_count"] == 1
        assert by_id["t-err"]["crag_iterations"] is None

        assert by_id["t-crag"]["status"] == "crag_triggered"
        assert by_id["t-crag"]["crag_iterations"] == 2
        assert by_id["t-crag"]["stage_count"] == 4
    finally:
        langfuse_tracer._set_langfuse_client_for_tests(None)


def test_list_traces_filter_errors_only_returns_error_status() -> None:
    """filter=errors → only error-status traces survive the filter."""
    now = datetime.now(UTC)
    fake_traces = [
        _trace(trace_id="ok-1", timestamp=now, input_payload={"query": "q1"}),
        _trace(
            trace_id="err-1",
            timestamp=now,
            input_payload={"query": "q2"},
            metadata={"status": "error"},
            level="ERROR",
        ),
        _trace(
            trace_id="crag-1",
            timestamp=now,
            input_payload={"query": "q3"},
            metadata={"crag_iterations": 1},
        ),
    ]
    fake_client = MagicMock()
    fake_client.fetch_traces = MagicMock(return_value=SimpleNamespace(data=fake_traces))
    langfuse_tracer._set_langfuse_client_for_tests(fake_client)

    try:
        resp = TestClient(_build_app()).get("/traces?filter=errors")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 1
        assert len(body["items"]) == 1
        assert body["items"][0]["trace_id"] == "err-1"
        assert body["items"][0]["status"] == "error"
    finally:
        langfuse_tracer._set_langfuse_client_for_tests(None)


def test_list_traces_filter_crag_triggered_only() -> None:
    """filter=crag_triggered → only CRAG-triggered traces survive."""
    now = datetime.now(UTC)
    fake_traces = [
        _trace(trace_id="ok-1", timestamp=now, input_payload={"query": "q1"}),
        _trace(
            trace_id="crag-2",
            timestamp=now,
            input_payload={"query": "q2"},
            metadata={"crag_iterations": 3},
        ),
        _trace(
            trace_id="crag-flag-only",
            timestamp=now,
            input_payload={"query": "q3"},
            metadata={"crag_triggered": True},
        ),
    ]
    fake_client = MagicMock()
    fake_client.fetch_traces = MagicMock(return_value=SimpleNamespace(data=fake_traces))
    langfuse_tracer._set_langfuse_client_for_tests(fake_client)

    try:
        resp = TestClient(_build_app()).get("/traces?filter=crag_triggered")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 2
        ids = {item["trace_id"] for item in body["items"]}
        assert ids == {"crag-2", "crag-flag-only"}
        assert all(t["status"] == "crag_triggered" for t in body["items"])
    finally:
        langfuse_tracer._set_langfuse_client_for_tests(None)


def test_list_traces_empty_window_returns_200_with_empty_items() -> None:
    """Empty Langfuse window (data=[]) → 200 + status='ok' + total=0 + items=[]."""
    fake_client = MagicMock()
    fake_client.fetch_traces = MagicMock(return_value=SimpleNamespace(data=[]))
    langfuse_tracer._set_langfuse_client_for_tests(fake_client)

    try:
        resp = TestClient(_build_app()).get("/traces")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"
        assert body["total"] == 0
        assert body["items"] == []
    finally:
        langfuse_tracer._set_langfuse_client_for_tests(None)


def test_list_traces_pagination_offset_and_limit() -> None:
    """limit=2 + offset=1 → returns rows [1:3] of 5;total reflects full filtered count."""
    now = datetime.now(UTC)
    fake_traces = [
        _trace(trace_id=f"t-{i}", timestamp=now - timedelta(minutes=i), input_payload={"query": f"q{i}"})
        for i in range(5)
    ]
    fake_client = MagicMock()
    fake_client.fetch_traces = MagicMock(return_value=SimpleNamespace(data=fake_traces))
    langfuse_tracer._set_langfuse_client_for_tests(fake_client)

    try:
        resp = TestClient(_build_app()).get("/traces?limit=2&offset=1")
        assert resp.status_code == 200
        body = resp.json()
        assert body["limit"] == 2
        assert body["offset"] == 1
        assert body["total"] == 5
        assert [item["trace_id"] for item in body["items"]] == ["t-1", "t-2"]
    finally:
        langfuse_tracer._set_langfuse_client_for_tests(None)


def test_list_traces_no_langfuse_client_returns_no_client_status() -> None:
    """No Langfuse client → status='no_client' + empty items + 200."""
    langfuse_tracer._set_langfuse_client_for_tests(None)
    resp = TestClient(_build_app()).get("/traces")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "no_client"
    assert body["items"] == []
    assert body["total"] == 0
    assert "Langfuse client not initialized" in body["note"]


def test_list_traces_sdk_method_missing() -> None:
    """Langfuse client without fetch_traces → status='sdk_method_missing'."""
    fake_client = SimpleNamespace()  # no fetch_traces attribute
    langfuse_tracer._set_langfuse_client_for_tests(fake_client)

    try:
        resp = TestClient(_build_app()).get("/traces")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "sdk_method_missing"
        assert body["items"] == []
        assert "fetch_traces" in body["note"]
    finally:
        langfuse_tracer._set_langfuse_client_for_tests(None)


def test_list_traces_fetch_raises_returns_fetch_failed() -> None:
    """client.fetch_traces raises → status='fetch_failed' + error in note."""
    fake_client = MagicMock()
    fake_client.fetch_traces = MagicMock(side_effect=ConnectionError("Langfuse unreachable"))
    langfuse_tracer._set_langfuse_client_for_tests(fake_client)

    try:
        resp = TestClient(_build_app()).get("/traces")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "fetch_failed"
        assert "ConnectionError" in body["note"]
        assert body["items"] == []
    finally:
        langfuse_tracer._set_langfuse_client_for_tests(None)


def test_list_traces_since_filter_excludes_older_rows() -> None:
    """since=ISO → rows with timestamp < since are excluded."""
    base = datetime(2026, 5, 17, 12, 0, 0, tzinfo=UTC)
    fake_traces = [
        _trace(trace_id="old", timestamp=base - timedelta(hours=2), input_payload={"query": "q1"}),
        _trace(trace_id="recent", timestamp=base + timedelta(hours=1), input_payload={"query": "q2"}),
    ]
    fake_client = MagicMock()
    fake_client.fetch_traces = MagicMock(return_value=SimpleNamespace(data=fake_traces))
    langfuse_tracer._set_langfuse_client_for_tests(fake_client)

    try:
        cutoff = base.isoformat()  # 2026-05-17T12:00:00+00:00
        resp = TestClient(_build_app()).get(f"/traces?since={cutoff}")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 1
        assert body["items"][0]["trace_id"] == "recent"
    finally:
        langfuse_tracer._set_langfuse_client_for_tests(None)


def test_list_traces_kb_id_filter_scopes_to_one_kb() -> None:
    """kb_id= filter → only traces with matching metadata.kb_id (or input.kb_id) survive."""
    now = datetime.now(UTC)
    fake_traces = [
        _trace(
            trace_id="drive-1",
            timestamp=now,
            input_payload={"query": "q1"},
            metadata={"kb_id": "kb-drive"},
        ),
        _trace(
            trace_id="other-1",
            timestamp=now,
            input_payload={"query": "q2"},
            metadata={"kb_id": "kb-other"},
        ),
        _trace(
            trace_id="drive-2-input-only",
            timestamp=now,
            input_payload={"query": "q3", "kb_id": "kb-drive"},
        ),
    ]
    fake_client = MagicMock()
    fake_client.fetch_traces = MagicMock(return_value=SimpleNamespace(data=fake_traces))
    langfuse_tracer._set_langfuse_client_for_tests(fake_client)

    try:
        resp = TestClient(_build_app()).get("/traces?kb_id=kb-drive")
        assert resp.status_code == 200
        body = resp.json()
        ids = {item["trace_id"] for item in body["items"]}
        assert ids == {"drive-1", "drive-2-input-only"}
        assert body["total"] == 2
    finally:
        langfuse_tracer._set_langfuse_client_for_tests(None)


def test_list_traces_error_priority_over_crag_status() -> None:
    """Trace with BOTH crag_iterations + level=ERROR → status='error' (priority)."""
    now = datetime.now(UTC)
    fake_traces = [
        _trace(
            trace_id="dual",
            timestamp=now,
            input_payload={"query": "q"},
            metadata={"crag_iterations": 2, "status": "error"},
            level="ERROR",
        ),
    ]
    fake_client = MagicMock()
    fake_client.fetch_traces = MagicMock(return_value=SimpleNamespace(data=fake_traces))
    langfuse_tracer._set_langfuse_client_for_tests(fake_client)

    try:
        resp = TestClient(_build_app()).get("/traces")
        body = resp.json()
        assert body["items"][0]["status"] == "error"
        assert body["items"][0]["crag_iterations"] == 2
    finally:
        langfuse_tracer._set_langfuse_client_for_tests(None)


def test_list_traces_response_as_plain_list_duck_typed() -> None:
    """SDK returning plain list (not `{data: [...]}`) is duck-typed correctly."""
    now = datetime.now(UTC)
    fake_traces = [
        _trace(trace_id="plain-1", timestamp=now, input_payload={"query": "q"}),
    ]
    fake_client = MagicMock()
    fake_client.fetch_traces = MagicMock(return_value=fake_traces)  # plain list, no .data
    langfuse_tracer._set_langfuse_client_for_tests(fake_client)

    try:
        resp = TestClient(_build_app()).get("/traces")
        body = resp.json()
        assert body["status"] == "ok"
        assert body["total"] == 1
        assert body["items"][0]["trace_id"] == "plain-1"
    finally:
        langfuse_tracer._set_langfuse_client_for_tests(None)


def test_list_traces_query_preview_truncated_to_100_chars() -> None:
    """Long query strings → query_preview truncated to first 100 chars."""
    long_query = "x" * 250
    now = datetime.now(UTC)
    fake_traces = [
        _trace(trace_id="long", timestamp=now, input_payload={"query": long_query}),
    ]
    fake_client = MagicMock()
    fake_client.fetch_traces = MagicMock(return_value=SimpleNamespace(data=fake_traces))
    langfuse_tracer._set_langfuse_client_for_tests(fake_client)

    try:
        resp = TestClient(_build_app()).get("/traces")
        body = resp.json()
        assert len(body["items"][0]["query_preview"]) == 100
    finally:
        langfuse_tracer._set_langfuse_client_for_tests(None)


def test_list_traces_fallback_to_name_when_input_empty() -> None:
    """No input + has name → query_preview falls back to trace.name."""
    now = datetime.now(UTC)
    fake_traces = [
        _trace(trace_id="no-input", timestamp=now, input_payload=None, name="api.eval.shootout"),
    ]
    fake_client = MagicMock()
    fake_client.fetch_traces = MagicMock(return_value=SimpleNamespace(data=fake_traces))
    langfuse_tracer._set_langfuse_client_for_tests(fake_client)

    try:
        resp = TestClient(_build_app()).get("/traces")
        body = resp.json()
        assert body["items"][0]["query_preview"] == "api.eval.shootout"
    finally:
        langfuse_tracer._set_langfuse_client_for_tests(None)
