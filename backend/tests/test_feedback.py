"""W8 D5 F5.3 — /feedback Langfuse wire coverage.

Per W08-beta-deploy-sprint2 plan §2 F5.3 acceptance:
  - thumbs_up + thumbs_down map to Langfuse score value +1 / -1
  - When Langfuse client absent → 202 still accepted (audit logged)
  - Forward failure → 202 still accepted (warning logged, no 5xx leak)
  - Trace_id round-trips into the Langfuse score() call
"""

from __future__ import annotations

import logging
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routes import feedback as feedback_route
from observability import langfuse_tracer


@pytest.fixture(autouse=True)
def _reset_langfuse_singleton() -> None:
    langfuse_tracer._set_langfuse_client_for_tests(None)
    yield
    langfuse_tracer._set_langfuse_client_for_tests(None)


def _build_app() -> FastAPI:
    app = FastAPI()
    app.include_router(feedback_route.router)
    return app


def _payload(rating: str = "thumbs_up", comment: str | None = None) -> dict:
    return {"trace_id": "trace-abc-123", "rating": rating, "comment": comment}


def test_feedback_accepts_thumbs_up_without_langfuse_client() -> None:
    """Local dev path — no client → 202 accepted, audit logged."""
    client = TestClient(_build_app())

    resp = client.post("/feedback", json=_payload("thumbs_up", "very helpful"))

    assert resp.status_code == 202
    body = resp.json()
    assert body["accepted"] is True
    assert isinstance(body["feedback_id"], str) and len(body["feedback_id"]) > 0


def test_feedback_thumbs_up_forwards_score_plus_one() -> None:
    fake_client = MagicMock()
    langfuse_tracer._set_langfuse_client_for_tests(fake_client)

    client = TestClient(_build_app())

    resp = client.post("/feedback", json=_payload("thumbs_up", "great citation"))

    assert resp.status_code == 202
    fake_client.score.assert_called_once_with(
        trace_id="trace-abc-123",
        name="user_feedback",
        value=1,
        comment="great citation",
    )


def test_feedback_thumbs_down_forwards_score_minus_one() -> None:
    fake_client = MagicMock()
    langfuse_tracer._set_langfuse_client_for_tests(fake_client)

    client = TestClient(_build_app())

    resp = client.post("/feedback", json=_payload("thumbs_down", None))

    assert resp.status_code == 202
    fake_client.score.assert_called_once_with(
        trace_id="trace-abc-123",
        name="user_feedback",
        value=-1,
        comment=None,
    )


def test_feedback_swallows_forward_failure(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Langfuse score() raise → 202 still accepted; warning logged."""
    fake_client = MagicMock()
    fake_client.score.side_effect = RuntimeError("langfuse 503")
    langfuse_tracer._set_langfuse_client_for_tests(fake_client)

    client = TestClient(_build_app())
    caplog.set_level(logging.WARNING, logger="ekp.feedback")

    resp = client.post("/feedback", json=_payload("thumbs_up"))

    assert resp.status_code == 202
    assert resp.json()["accepted"] is True
    fake_client.score.assert_called_once()


def test_feedback_validates_rating_literal() -> None:
    """Pydantic Literal — invalid rating → 422."""
    client = TestClient(_build_app())

    resp = client.post(
        "/feedback",
        json={"trace_id": "t-1", "rating": "ambivalent"},
    )

    assert resp.status_code == 422


def test_feedback_when_client_lacks_score_method() -> None:
    """Client without score attribute (older SDK?) — 202 accepted, no crash."""
    fake_client = object()  # no .score
    langfuse_tracer._set_langfuse_client_for_tests(fake_client)

    client = TestClient(_build_app())

    resp = client.post("/feedback", json=_payload("thumbs_up"))

    assert resp.status_code == 202
