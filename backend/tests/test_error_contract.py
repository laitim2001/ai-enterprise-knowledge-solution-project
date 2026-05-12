"""W7 D4 F4.4 — uniform ApiError envelope contract tests.

Verifies F4.1 every endpoint returns `{"error": {"code", "message",
"actionable_hint"}}` shape across 4xx + 5xx + ValidationError + unhandled
Exception. NO raw stack trace leaks to client.
"""

from __future__ import annotations

from typing import Literal

import pytest
from fastapi import FastAPI, HTTPException, status
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field

from api.error_handlers import register_error_handlers
from api.schemas.errors import ErrorCodes


class _Body(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)


class _FeedbackLike(BaseModel):
    """Mirrors the real `/feedback` `rating` field (a Literal) — used by the
    CH-002 F8 test that checks the 422 envelope names the field + allowed values
    without echoing the bad input. Module-level so `get_type_hints` can resolve
    the `from __future__ import annotations` forward ref."""

    rating: Literal["thumbs_up", "thumbs_down"]


@pytest.fixture
def app() -> FastAPI:
    app = FastAPI()
    register_error_handlers(app)

    @app.get("/raise-401")
    def _raise_401() -> None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )

    @app.get("/raise-404")
    def _raise_404() -> None:
        raise HTTPException(status_code=404, detail="KB not found")

    @app.get("/raise-409")
    def _raise_409() -> None:
        raise HTTPException(status_code=409, detail="KB already exists")

    @app.get("/raise-502")
    def _raise_502() -> None:
        raise HTTPException(status_code=502, detail="retrieval failure: NetworkError")

    @app.get("/raise-503")
    def _raise_503() -> None:
        raise HTTPException(status_code=503, detail="Synthesizer not initialized")

    @app.get("/raise-504")
    def _raise_504() -> None:
        raise HTTPException(status_code=504, detail="LLM call exceeded 30s deadline")

    @app.get("/raise-unhandled")
    def _raise_unhandled() -> None:
        raise RuntimeError("internal database driver crashed: secret_password=foo")

    @app.post("/validate")
    def _validate(body: _Body) -> dict[str, str]:
        return {"echo": body.query}

    @app.post("/feedback-like")
    def _feedback_like(body: _FeedbackLike) -> dict[str, str]:
        return {"rating": body.rating}

    return app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    return TestClient(app, raise_server_exceptions=False)


def _assert_envelope(payload: dict, expected_code: str) -> None:
    assert "error" in payload, payload
    err = payload["error"]
    assert err["code"] == expected_code
    assert isinstance(err["message"], str)
    assert err["message"]
    assert "actionable_hint" in err  # may be None but key present


def test_401_returns_envelope_with_auth_unauthorized_code(client: TestClient) -> None:
    response = client.get("/raise-401")
    assert response.status_code == 401
    _assert_envelope(response.json(), ErrorCodes.AUTH_UNAUTHORIZED)
    assert response.json()["error"]["message"] == "Token expired"
    assert response.headers.get("WWW-Authenticate") == "Bearer"


def test_404_returns_envelope_with_resource_not_found_code(client: TestClient) -> None:
    response = client.get("/raise-404")
    assert response.status_code == 404
    _assert_envelope(response.json(), ErrorCodes.RESOURCE_NOT_FOUND)


def test_409_returns_envelope_with_resource_conflict_code(client: TestClient) -> None:
    response = client.get("/raise-409")
    assert response.status_code == 409
    _assert_envelope(response.json(), ErrorCodes.RESOURCE_CONFLICT)


def test_502_returns_envelope_with_retrieval_failed_code(client: TestClient) -> None:
    response = client.get("/raise-502")
    assert response.status_code == 502
    _assert_envelope(response.json(), ErrorCodes.PIPELINE_RETRIEVAL_FAILED)


def test_503_envelope_for_synthesis_unavailable(client: TestClient) -> None:
    response = client.get("/raise-503")
    assert response.status_code == 503
    _assert_envelope(response.json(), ErrorCodes.PIPELINE_SYNTHESIS_FAILED)


def test_504_envelope_for_llm_timeout_E5(client: TestClient) -> None:
    """E5 architecture.md §7.3 — LLM API timeout."""
    response = client.get("/raise-504")
    assert response.status_code == 504
    _assert_envelope(response.json(), ErrorCodes.PIPELINE_LLM_TIMEOUT)


def test_unhandled_exception_envelope_redacts_internals(client: TestClient) -> None:
    """F4.1 + CLAUDE.md §5.5 H5 — never leak stack trace / internal detail to client."""
    response = client.get("/raise-unhandled")
    assert response.status_code == 500
    payload = response.json()
    _assert_envelope(payload, ErrorCodes.INTERNAL_SERVER_ERROR)
    body_text = response.text
    # Internal details must NOT appear in the response body.
    assert "RuntimeError" not in body_text
    assert "secret_password" not in body_text
    assert "internal database driver crashed" not in body_text


def test_validation_error_envelope_E6_query_too_long(client: TestClient) -> None:
    """E6 architecture.md §7.3 — query > 2000 chars."""
    response = client.post("/validate", json={"query": "a" * 2001})
    assert response.status_code == 422
    _assert_envelope(response.json(), ErrorCodes.VALIDATION_QUERY_TOO_LONG)


def test_validation_error_envelope_generic_invalid_payload(client: TestClient) -> None:
    response = client.post("/validate", json={"query": ""})
    assert response.status_code == 422
    _assert_envelope(response.json(), ErrorCodes.VALIDATION_INVALID_PAYLOAD)


def test_envelope_includes_actionable_hint_when_known(client: TestClient) -> None:
    response = client.get("/raise-401")
    hint = response.json()["error"]["actionable_hint"]
    assert hint is not None
    assert "Sign in" in hint or "refresh" in hint.lower()


# --------------------------------------------------------------------------- #
# CH-002 F8 — 422 envelope names the failing field + constraint, never the
# raw input value (H5 redaction preserved).
# --------------------------------------------------------------------------- #


def test_ch002_f8_validation_envelope_names_field_without_leaking_input(client: TestClient) -> None:
    """CH-002 F8 — a Pydantic Literal mismatch (mirrors the real `/feedback`
    `rating` field) surfaces the field path + the allowed values in the message,
    but the bad input value is NOT echoed back (CLAUDE.md §5.5 H5)."""
    resp = client.post("/feedback-like", json={"rating": "BANANA_SENTINEL"})
    assert resp.status_code == 422
    _assert_envelope(resp.json(), ErrorCodes.VALIDATION_INVALID_PAYLOAD)
    message = resp.json()["error"]["message"]
    assert "body.rating" in message            # the failing field is named
    assert "thumbs_up" in message and "thumbs_down" in message  # allowed values surfaced
    assert "BANANA_SENTINEL" not in resp.text  # the bad input value is NOT echoed (H5)


def test_ch002_f8_validation_envelope_redacts_structured_input_value(client: TestClient) -> None:
    """CH-002 F8 / R5 — a type error whose `input` is a structured value still
    must not leak that value into the response body; the field path is named."""
    resp = client.post("/validate", json={"query": {"nested": "LEAKME_SENTINEL_xyz"}})
    assert resp.status_code == 422
    _assert_envelope(resp.json(), ErrorCodes.VALIDATION_INVALID_PAYLOAD)
    assert "body.query" in resp.json()["error"]["message"]
    assert "LEAKME_SENTINEL_xyz" not in resp.text
