"""Eval endpoints tests (W16 F5.4 CO_W15_F1 closure).

Per W16 plan F5.4 acceptance criteria + CLAUDE.md §5.6 H6 + Decision C.1
(Both endpoints full implementation;RAGAs 4-metric W17+ deferred per
orchestrator docstring).

Coverage:
- /eval/run happy path: orchestrator returns EvalReport with Recall@5 +
  W17+ deferral note in failed_queries
- /eval/run engine 503: app.state.retrieval_engine = None
- /eval/run eval-set 404: unknown eval_set_id
- /eval/run runtime 502: orchestrator raises
- /eval/shootout happy path: per-reranker entries + winner selected
- /eval/shootout skip: voyage/zeroentropy/azure point to CLI driver
- /eval/shootout default rerankers when payload empty
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routes import eval as eval_routes
from api.schemas.eval import EvalReport, FailedQueryDetail


def _build_app(engine: object | None = None) -> FastAPI:
    app = FastAPI()
    app.include_router(eval_routes.router)
    app.state.retrieval_engine = engine
    return app


def _mock_eval_report(recall: float = 0.85) -> EvalReport:
    return EvalReport(
        recall_at_5=recall,
        faithfulness=0.0,
        correctness=None,
        image_association=0.0,
        p95_latency_ms=180,
        failed_queries=[
            FailedQueryDetail(
                query_id="_w17_ragas_deferral_note",
                query="(orchestrator note)",
                expected="(see W16 plan §3 PARTIAL PASS allowance)",
                got="RAGAs 4-metric deferred to W17+ background job",
                metric_failed=["faithfulness", "correctness", "image_association"],
            ),
        ],
        crag_trigger_rate=0.0,
        avg_cost_per_query_usd=0.0,
    )


def test_run_eval_happy_path() -> None:
    """orchestrator returns EvalReport;route surfaces 200 + schema-valid body."""
    app = _build_app(engine=object())  # truthy stub (orchestrator is mocked anyway)
    client = TestClient(app)

    with patch(
        "api.routes.eval.run_eval_pipeline",
        new=AsyncMock(return_value=_mock_eval_report(recall=0.92)),
    ):
        resp = client.post("/eval/run", json={"eval_set_id": "eval-set-v0"})

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["recall_at_5"] == 0.92
    assert body["faithfulness"] == 0.0
    assert body["correctness"] is None
    # W17+ deferral note must surface in failed_queries
    assert any(
        f["query_id"] == "_w17_ragas_deferral_note" for f in body["failed_queries"]
    )


def test_run_eval_engine_not_initialized_returns_503() -> None:
    app = _build_app(engine=None)
    client = TestClient(app)

    resp = client.post("/eval/run", json={"eval_set_id": "eval-set-v0"})
    assert resp.status_code == 503


def test_run_eval_unknown_eval_set_returns_404() -> None:
    app = _build_app(engine=object())
    client = TestClient(app)

    resp = client.post("/eval/run", json={"eval_set_id": "nonexistent_eval_set"})
    assert resp.status_code == 404


def test_run_eval_orchestrator_raises_returns_502() -> None:
    app = _build_app(engine=object())
    client = TestClient(app)

    with patch(
        "api.routes.eval.run_eval_pipeline",
        new=AsyncMock(side_effect=ConnectionError("Azure unreachable")),
    ):
        resp = client.post("/eval/run", json={"eval_set_id": "eval-set-v0"})

    assert resp.status_code == 502


def test_shootout_happy_path_default_rerankers() -> None:
    """Empty payload rerankers → use default [cohere-v4.0-pro + off]."""
    app = _build_app(engine=object())
    client = TestClient(app)

    with patch(
        "api.routes.eval.run_eval_pipeline",
        new=AsyncMock(return_value=_mock_eval_report(recall=0.88)),
    ):
        resp = client.post("/eval/shootout", json={"eval_set_id": "eval-set-v0"})

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["eval_set_id"] == "eval-set-v0"
    assert len(body["rerankers"]) == 2
    labels = [e["reranker"] for e in body["rerankers"]]
    assert "cohere-v4.0-pro" in labels
    assert "off" in labels
    # All evaluated (mock returns same recall) → winner is one of them
    assert body["winner"] in labels


def test_shootout_voyage_zeroentropy_azure_skipped_with_cli_pointer() -> None:
    """Voyage / ZeroEntropy / Azure → skipped with CLI driver pointer
    (per Decision C.1 Tier 1 baseline limitation)."""
    app = _build_app(engine=object())
    client = TestClient(app)

    with patch(
        "api.routes.eval.run_eval_pipeline",
        new=AsyncMock(return_value=_mock_eval_report()),
    ):
        resp = client.post(
            "/eval/shootout",
            json={
                "eval_set_id": "eval-set-v0",
                "rerankers": ["voyage-rerank-2.5", "zeroentropy-zerank-1", "azure-semantic"],
            },
        )

    assert resp.status_code == 200
    body = resp.json()
    assert len(body["rerankers"]) == 3
    for entry in body["rerankers"]:
        assert entry["skipped"] is True
        assert "scripts/run_reranker_shootout.py" in entry["skip_reason"]
        assert entry["report"] is None
    assert body["winner"] is None  # all skipped → no winner


def test_shootout_unknown_reranker_label_skipped() -> None:
    app = _build_app(engine=object())
    client = TestClient(app)

    with patch(
        "api.routes.eval.run_eval_pipeline",
        new=AsyncMock(return_value=_mock_eval_report()),
    ):
        resp = client.post(
            "/eval/shootout",
            json={
                "eval_set_id": "eval-set-v0",
                "rerankers": ["my-future-reranker-2027"],
            },
        )

    assert resp.status_code == 200
    body = resp.json()
    assert len(body["rerankers"]) == 1
    assert body["rerankers"][0]["skipped"] is True
    assert "Unknown reranker label" in body["rerankers"][0]["skip_reason"]
    assert body["winner"] is None


def test_shootout_winner_selected_by_max_recall() -> None:
    """Different recall per reranker → winner = max recall reranker."""
    app = _build_app(engine=object())
    client = TestClient(app)

    # Mock returns different recall for sequential calls
    mock_calls = [
        _mock_eval_report(recall=0.95),  # cohere-v4.0-pro
        _mock_eval_report(recall=0.78),  # off (hybrid-only)
    ]

    async def mock_pipeline(*args, **kwargs):
        return mock_calls.pop(0)

    with patch("api.routes.eval.run_eval_pipeline", new=mock_pipeline):
        resp = client.post("/eval/shootout", json={"eval_set_id": "eval-set-v0"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["winner"] == "cohere-v4.0-pro"  # higher recall


def test_run_eval_engine_503_short_circuits_before_eval_set_resolution() -> None:
    """Engine 503 must fire BEFORE eval_set_id 404 lookup (engine guard first)."""
    app = _build_app(engine=None)
    client = TestClient(app)

    resp = client.post(
        "/eval/run",
        json={"eval_set_id": "nonexistent_too"},
    )
    # Engine guard fires first (503), not eval_set 404
    assert resp.status_code == 503
