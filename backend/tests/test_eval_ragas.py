"""W17 F3 — RAGAs integration into the eval orchestrator (mocked at the
LLM-judge boundary — no live Azure OpenAI in CI).

- `make_ragas_evaluator(settings)` returns `None` without an Azure judge key
  (the no-key path → orchestrator falls back to Recall@5-only).
- `run_eval_pipeline` with a fake engine + fake synthesizer + stub `ragas_evaluator`
  populates `EvalReport.faithfulness` / `correctness` and surfaces below-threshold
  + errored queries in `failed_queries`.
- Without `synthesizer` / `ragas_evaluator` → the Recall@5-only fallback report
  (faithfulness 0.0 / correctness None) + the `_ragas_not_run` note.

The stub `ragas_evaluator` IS the LLM-judge boundary — these tests pin the
score-plumbing + EvalReport shape, not the judge's actual scoring.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from eval.orchestrator import run_eval_pipeline
from eval.ragas_evaluator import make_faithfulness_evaluator, make_ragas_evaluator
from eval.ragas_runner import RagasQuerySample
from storage.settings import Settings

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_EVAL_SET_V0 = _PROJECT_ROOT / "docs" / "eval-set-v0.yaml"


class _FakeChunk:
    def __init__(self, chunk_id: str, text: str) -> None:
        self.score = 0.9
        self.fields = {"chunk_id": chunk_id, "chunk_text": text}


class _FakeRetrieval:
    def __init__(self) -> None:
        self.chunks = [_FakeChunk("kb-drive_doc-T_chunk-0001", "the paper jam recovery procedure step text")]
        self.embed_latency_ms = 12
        self.search_latency_ms = 34


class _FakeEngine:
    async def retrieve(self, *, query: str, kb_id: str, top_k: int) -> _FakeRetrieval:  # noqa: ARG002
        return _FakeRetrieval()


class _FakeSynthesizer:
    async def synthesize(self, query: str, chunks: list) -> SimpleNamespace:  # noqa: ARG002
        return SimpleNamespace(answer=f"synthesized answer for: {query[:40]}")


def _good_evaluator(sample: RagasQuerySample) -> dict:
    return {
        "faithfulness": 0.92,
        "answer_relevancy": 0.88,
        "context_precision": 0.81,
        "context_recall": 0.79,
        "input_tokens": 0,
        "output_tokens": 0,
    }


def _mixed_evaluator(sample: RagasQuerySample) -> dict:
    # First main query scores high, the rest dip below the 0.70 attention threshold.
    if sample.query_id.endswith("1") or sample.query_id.endswith("01"):
        return _good_evaluator(sample)
    return {
        "faithfulness": 0.55,
        "answer_relevancy": 0.62,
        "context_precision": 0.40,
        "context_recall": 0.66,
        "input_tokens": 0,
        "output_tokens": 0,
    }


def test_make_ragas_evaluator_returns_none_without_azure_key() -> None:
    assert make_ragas_evaluator(Settings(azure_openai_api_key="")) is None


def test_make_faithfulness_evaluator_returns_none_without_azure_key() -> None:
    # W48 — the config-test quality axis degrades to None (no quality column) when
    # no Azure judge credential is configured (local dev / CI), same as the 4-metric
    # path. The route then returns ConfigRunSummary.faithfulness=None.
    assert make_faithfulness_evaluator(Settings(azure_openai_api_key="")) is None


@pytest.mark.asyncio
async def test_run_eval_pipeline_recall_only_without_synth_or_evaluator() -> None:
    report = await run_eval_pipeline(
        eval_set_path=_EVAL_SET_V0,
        engine=_FakeEngine(),
        max_main_queries=2,
    )
    assert report.faithfulness == 0.0
    assert report.correctness is None
    assert 0.0 <= report.recall_at_5 <= 1.0
    note_ids = {f.query_id for f in report.failed_queries}
    assert "_ragas_not_run" in note_ids
    assert "_metrics_deferred_note" in note_ids


@pytest.mark.asyncio
async def test_run_eval_pipeline_populates_ragas_metrics() -> None:
    report = await run_eval_pipeline(
        eval_set_path=_EVAL_SET_V0,
        engine=_FakeEngine(),
        max_main_queries=2,
        synthesizer=_FakeSynthesizer(),
        ragas_evaluator=_good_evaluator,
        judge_deployment="gpt-5-4-mini",
    )
    assert report.faithfulness == pytest.approx(0.92)
    assert report.correctness == pytest.approx(0.88)
    # No below-threshold queries with the all-high evaluator → only the two
    # orchestrator notes in failed_queries (no per-query attention rows).
    note_ids = {f.query_id for f in report.failed_queries}
    assert "_ragas_not_run" not in note_ids
    assert "_metrics_deferred_note" in note_ids


@pytest.mark.asyncio
async def test_run_eval_pipeline_surfaces_below_threshold_queries() -> None:
    report = await run_eval_pipeline(
        eval_set_path=_EVAL_SET_V0,
        engine=_FakeEngine(),
        max_main_queries=3,
        synthesizer=_FakeSynthesizer(),
        ragas_evaluator=_mixed_evaluator,
        judge_deployment="gpt-5-4-mini",
    )
    # faithfulness mean is pulled down by the below-threshold queries.
    assert 0.0 < report.faithfulness < 0.92
    # At least one per-query "below attention threshold" row surfaced.
    attention_rows = [
        f for f in report.failed_queries if f.expected.startswith(">=")
    ]
    assert attention_rows
    assert any("faithfulness" in f.metric_failed for f in attention_rows)


def test_w36_ragas_attention_thresholds_per_metric_calibration() -> None:
    """W36 F2 (d) — verify per-metric attention thresholds dict locked.

    Pre-W36 was single `_RAGAS_ATTENTION_THRESHOLD = 0.70`. W36 calibration:
    - faithfulness / answer_relevancy / context_precision = 0.65(降低 surface
      borderline benign answer_relevancy 0.6X cluster per W35 evidence)
    - context_recall = 0.0(keyword-mode artifact 不 surface 至 Q14 SME-validate
      reference_answer cascade ships)
    """
    from eval.orchestrator import _RAGAS_ATTENTION_THRESHOLDS

    assert _RAGAS_ATTENTION_THRESHOLDS["faithfulness"] == 0.65
    assert _RAGAS_ATTENTION_THRESHOLDS["answer_relevancy"] == 0.65
    assert _RAGAS_ATTENTION_THRESHOLDS["context_precision"] == 0.65
    # context_recall threshold = 0.0 effectively skips keyword-mode artifact surface
    assert _RAGAS_ATTENTION_THRESHOLDS["context_recall"] == 0.0


@pytest.mark.asyncio
async def test_w36_context_recall_keyword_mode_artifact_not_surfaced() -> None:
    """W36 F2 (d.2) — context_recall=0.00 keyword-mode artifact 不 surface 至
    failed_queries(per ragas_evaluator.py:75-77 W17 F3 fallback known limitation,
    until Q14 SME reference_answer ships)。

    Builds an evaluator where context_recall=0.0(keyword-mode artifact)while
    faithfulness=0.95(high)+ other metrics 0.85 — only the high-confidence path
    matters here, so no metric should surface as below-threshold; especially
    context_recall=0.0 must NOT be in any metric_failed list per W36 calibration.
    """

    def _kw_mode_evaluator(sample: RagasQuerySample) -> dict:
        return {
            "faithfulness": 0.95,
            "answer_relevancy": 0.85,
            "context_precision": 0.80,
            "context_recall": 0.0,  # 模擬 keyword-mode artifact per W17 F3 fallback
            "input_tokens": 0,
            "output_tokens": 0,
        }

    report = await run_eval_pipeline(
        eval_set_path=_EVAL_SET_V0,
        engine=_FakeEngine(),
        max_main_queries=2,
        synthesizer=_FakeSynthesizer(),
        ragas_evaluator=_kw_mode_evaluator,
        judge_deployment="gpt-5-4-mini",
    )
    # context_recall=0.0 → 不 surface 因 W36 threshold = 0.0
    for f in report.failed_queries:
        if f.expected.startswith(">="):
            assert "context_recall" not in f.metric_failed, (
                f"W36 (d.2) regression: context_recall=0.0 keyword-mode artifact "
                f"surfaced 至 failed_queries:{f.metric_failed}"
            )
