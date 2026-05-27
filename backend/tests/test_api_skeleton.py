"""API skeleton smoke tests (per CLAUDE.md §5.6 H6 — query.py is critical module).

W1 scope: verify route registration + 501 stub response + schema validation.
W3+ replaces individual tests with real implementation tests.

W9 D5 C11 cleanup: refactored module-level `app.dependency_overrides` set
into autouse fixture-scoped pattern with proper teardown — prevents leak
into downstream test modules (test_observability_routes.py F4.4 401 assertions
were previously masked by this leak per W8 D5 retro § What didn't work).
"""

import pytest
from fastapi.testclient import TestClient

from api.auth import AuthenticatedUser, get_current_user
from api.server import app


@pytest.fixture(autouse=True)
def _mock_auth_override():
    """Install fixed test-user override on `get_current_user` for the duration
    of each test, then pop it on teardown.

    W7 D2 F1.3 — auth Depends wraps /query/** + /kb/** + /feedback. Pre-W7
    tests authenticated implicitly; preserve that behavior here. Real
    auth reject/allow paths are covered separately in test_mock_msal.py +
    test_auth_routes.py.
    """
    app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(
        oid="test-oid",
        tid="test-tid",
        preferred_username="test@ekp.local",
        is_mock=True,
    )
    yield
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_health_returns_ok(client: TestClient) -> None:
    # W20 F2.1 (550111e) extended /health from W1 `{status: "ok"}` to per-component
    # HealthResponse{status, components} — 5 backends reported individually.
    # TestClient(app) doesn't trigger the lifespan startup, so app.state.* singletons
    # stay None and the roll-up here is always "degraded"; this is a shape contract
    # check, not a strict-equality smoke against a populated app.
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] in {"ok", "degraded"}
    assert set(payload["components"].keys()) == {
        "azure_search",
        "azure_openai",
        "cohere",
        "langfuse",
        "postgres",
    }


def test_query_route_returns_502_when_retrieval_fails_due_to_network(
    client: TestClient,
) -> None:
    """W2 D4 F6: /query wired to RetrievalEngine. With .env configured, lifespan
    initializes engine; live retrieval fails (R8 reactivated VPN cert) → 502.
    R8 cleared environment would return 200 with chunks."""
    response = client.post(
        "/query",
        json={"query": "test", "kb_id": "drive_user_manuals"},
    )
    # Either 200 (engine works, e.g. post-VPN-disconnect) or 502 (live retrieval
    # blocked by R8 / network), but no longer 501. /query is no longer a stub.
    assert response.status_code in (200, 502, 503)
    if response.status_code == 200:
        body = response.json()
        assert "retrieved_chunks" in body
        assert "answer" in body


def test_query_stream_route_registered_returns_2xx_or_5xx(
    client: TestClient,
) -> None:
    """W3 D3 F4 (commit pending) wired SSE; route returns 503 when synthesizer
    not initialized (TestClient lifespan provides no Azure OpenAI keys),
    502 if retrieval fails downstream, or 200 with text/event-stream when
    fully wired. 501 no longer expected."""
    response = client.post(
        "/query/stream",
        json={"query": "test", "kb_id": "drive_user_manuals"},
    )
    assert response.status_code in (200, 502, 503)


def test_kb_list_route_returns_empty_in_memory(client: TestClient) -> None:
    """W1 D2 F7 (commit c6ca6e3) replaced 501 stub with in-memory KB CRUD.

    GET /kb returns 200 with empty list when no KBs created. W2 D1 swap to
    Azure-backed backend per W02 plan F1 dependency.
    """
    response = client.get("/kb")
    assert response.status_code == 200
    assert response.json() == []


def test_eval_run_route_registered_returns_503_when_engine_absent(client: TestClient) -> None:
    """W16 F5.4 closure (commit 4046b24): /eval/run no longer 501 stub.

    With no app.state.retrieval_engine wired (W1 skeleton fixture), endpoint
    returns 503 SERVICE_UNAVAILABLE per orchestrator pre-check guard. Real
    eval execution validated in tests/test_eval_endpoints.py.
    """
    response = client.post(
        "/eval/run",
        json={"eval_set_id": "eval-set-v0"},
    )
    assert response.status_code == 503


def test_screenshots_redirect_route_registered_returns_501(
    client: TestClient,
) -> None:
    response = client.get("/screenshots/drive/M042/img_007.png")
    assert response.status_code == 501


def test_query_request_schema_rejects_too_long_query(client: TestClient) -> None:
    """Per architecture.md §4.5: query max_length=2000."""
    too_long = "a" * 2001
    response = client.post(
        "/query",
        json={"query": too_long, "kb_id": "drive"},
    )
    assert response.status_code == 422


def test_query_request_schema_rejects_empty_query(client: TestClient) -> None:
    """Per architecture.md §4.5: query min_length=1."""
    response = client.post(
        "/query",
        json={"query": "", "kb_id": "drive"},
    )
    assert response.status_code == 422


def test_w39_query_request_mode_field_default_hybrid() -> None:
    """W39 F2 Path A — QueryRequest.mode defaults to 'hybrid' (backward-compat)."""
    from api.schemas.query import QueryRequest
    payload = QueryRequest(query="test query", kb_id="drive")
    assert payload.mode == "hybrid"


def test_w39_query_request_mode_field_accepts_vector_and_fulltext() -> None:
    """W39 F2 Path A — QueryRequest.mode accepts hybrid/vector/fulltext per ADR-0021."""
    from api.schemas.query import QueryRequest
    for mode in ("hybrid", "vector", "fulltext"):
        payload = QueryRequest(query="q", kb_id="drive", mode=mode)
        assert payload.mode == mode


def test_w39_query_request_mode_field_rejects_invalid_value() -> None:
    """W39 F2 Path A — Literal["hybrid", "vector", "fulltext"] rejects others."""
    import pytest
    from pydantic import ValidationError

    from api.schemas.query import QueryRequest
    with pytest.raises(ValidationError):
        QueryRequest(query="q", kb_id="drive", mode="semantic")  # type: ignore[arg-type]
