"""BUG-037 — eval harness kb_id threading (per CLAUDE.md §5.6 H6 — C06 eval).

Two surfaces were unable to target a non-default KB:
- `/eval/run` + `/eval/shootout` hardcoded `kb_id="drive_user_manuals"` (no request
  field) → could not eval CH-011 / per-doc config against another KB.
- CLI `scripts/run_ragas_eval.py` called `engine.retrieve(query=, top_k=)` WITHOUT
  `kb_id`, which RetrievalEngine.retrieve has required since ADR-0018 → TypeError.

These tests pin: (a) the API threads `payload.kb_id` (and defaults to the Tier 1
baseline), (b) the CLI passes `--kb-id` into `engine.retrieve(..., kb_id=...)`.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routes import eval as eval_routes
from api.schemas.eval import EvalReport

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))


def _build_app(engine: object | None = None) -> FastAPI:
    app = FastAPI()
    app.include_router(eval_routes.router)
    app.state.retrieval_engine = engine
    return app


def _mock_eval_report() -> EvalReport:
    return EvalReport(
        recall_at_5=0.9,
        faithfulness=0.0,
        correctness=None,
        image_association=0.0,
        p95_latency_ms=100,
        failed_queries=[],
        crag_trigger_rate=0.0,
        avg_cost_per_query_usd=0.0,
    )


# --------------------------------------------------------------------------- #
# API — /eval/run + /eval/shootout thread payload.kb_id (was hardcoded)
# --------------------------------------------------------------------------- #


def test_run_eval_threads_explicit_kb_id() -> None:
    app = _build_app(engine=object())
    client = TestClient(app)
    pipeline = AsyncMock(return_value=_mock_eval_report())

    with patch("api.routes.eval.run_eval_pipeline", new=pipeline):
        resp = client.post(
            "/eval/run", json={"eval_set_id": "eval-set-v0", "kb_id": "drive-images-1"}
        )

    assert resp.status_code == 200, resp.text
    assert pipeline.await_args.kwargs["kb_id"] == "drive-images-1"


def test_run_eval_defaults_to_tier1_baseline_kb_id() -> None:
    """Omitting kb_id preserves the production single-KB baseline."""
    app = _build_app(engine=object())
    client = TestClient(app)
    pipeline = AsyncMock(return_value=_mock_eval_report())

    with patch("api.routes.eval.run_eval_pipeline", new=pipeline):
        resp = client.post("/eval/run", json={"eval_set_id": "eval-set-v0"})

    assert resp.status_code == 200, resp.text
    assert pipeline.await_args.kwargs["kb_id"] == "drive_user_manuals"


def test_shootout_threads_explicit_kb_id() -> None:
    app = _build_app(engine=object())
    client = TestClient(app)
    pipeline = AsyncMock(return_value=_mock_eval_report())

    with patch("api.routes.eval.run_eval_pipeline", new=pipeline):
        resp = client.post(
            "/eval/shootout",
            json={"eval_set_id": "eval-set-v0", "kb_id": "drive-images-1", "rerankers": ["off"]},
        )

    assert resp.status_code == 200, resp.text
    assert pipeline.await_args.kwargs["kb_id"] == "drive-images-1"


# --------------------------------------------------------------------------- #
# CLI — --kb-id wiring + threaded into engine.retrieve (the TypeError regression)
# --------------------------------------------------------------------------- #


def test_cli_parse_args_kb_id_default_and_override(monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts.run_ragas_eval import DEFAULT_KB_ID, _parse_args

    monkeypatch.setattr(sys, "argv", ["run_ragas_eval"])
    assert _parse_args().kb_id == DEFAULT_KB_ID  # default = Tier 1 baseline

    monkeypatch.setattr(sys, "argv", ["run_ragas_eval", "--kb-id", "drive-images-1"])
    assert _parse_args().kb_id == "drive-images-1"


class _AsyncCM:
    """Minimal async context manager stub for embedder / searcher / synthesizer."""

    async def __aenter__(self) -> _AsyncCM:
        return self

    async def __aexit__(self, *exc: object) -> bool:
        return False


@pytest.mark.asyncio
async def test_cli_build_samples_threads_kb_id_into_retrieve() -> None:
    """The pre-fix bug: engine.retrieve() called without the ADR-0018-required
    kb_id → TypeError. Assert kb_id now reaches retrieve."""
    from scripts import run_ragas_eval as cli

    sample = SimpleNamespace(question="how do I post a journal?", contexts=[], answer="")

    engine_fake = SimpleNamespace(retrieve=AsyncMock(return_value=SimpleNamespace(chunks=[])))
    synth_cm = _AsyncCM()
    synth_cm.synthesize = AsyncMock(return_value=SimpleNamespace(answer="ans"))  # type: ignore[attr-defined]

    with (
        patch.object(cli, "get_settings", return_value=MagicMock()),
        patch.object(cli, "load_samples_from_eval_set", return_value=[sample]),
        patch.object(cli, "AzureOpenAIEmbedder", return_value=_AsyncCM()),
        patch.object(cli, "HybridSearcher", return_value=_AsyncCM()),
        patch.object(cli, "make_reranker", return_value=None),
        patch.object(cli, "Synthesizer", return_value=synth_cm),
        patch.object(cli, "RetrievalEngine", return_value=engine_fake),
    ):
        await cli._build_samples_via_pipeline(Path("docs/eval-set-v0.yaml"), 1, "drive-images-1")

    engine_fake.retrieve.assert_awaited_once()
    assert engine_fake.retrieve.await_args.kwargs["kb_id"] == "drive-images-1"
