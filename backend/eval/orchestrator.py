"""Eval orchestrator for /eval/run + /eval/shootout endpoints.

W16 F5.4 (CO_W15_F1) wired the W2 `EvalRunner` (Recall@5) into the
`api/schemas/eval.py::EvalReport` schema; RAGAs 4-metric was deferred (cost +
latency — ~50 queries × ~5 judge LLM calls each = synchronous multi-minute).

W17 F3 closes that: `run_eval_pipeline` now takes an optional `synthesizer` +
`ragas_evaluator`. When **both** are supplied (the `/eval/*` route passes
`app.state.synthesizer` + `eval.ragas_evaluator.make_ragas_evaluator(settings)`,
which itself returns `None` without an Azure judge key), the orchestrator:
  1. runs the RAG pipeline per main query (retrieve via the engine → synthesize)
     to build `RagasQuerySample`s,
  2. hands them to `RagasRunner` with the Azure-judge evaluator,
  3. maps `faithfulness` mean → `EvalReport.faithfulness`, `answer_relevancy`
     mean → `EvalReport.correctness` ("Answer-Correctness" is approximated by
     RAGAs answer-relevancy in Tier 1 — real `answer_correctness` needs SME
     reference answers per Q14, which the eval-set doesn't carry yet), and
  4. surfaces per-query RAGAs failures (and below-threshold scorers) into
     `EvalReport.failed_queries`.

When `synthesizer`/`ragas_evaluator` are `None` (local dev / CI — no Azure key)
it falls back to the Recall@5-only report with a documented note in
`failed_queries` (so the V5 Eval Console still renders something coherent).

Still placeholders (out of F3 scope): `image_association` (a custom image-text
correlation metric — not a RAGAs metric; needs screenshot/citation correlation
wiring), `crag_trigger_rate` (CRAG correlation requires CragLoop in the eval
loop), `avg_cost_per_query_usd` (cost tracking lives in `realtime_cost.py`).
Long synchronous runs are bounded via `max_main_queries` (W4 plan §4 R4 cap).
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import structlog

from api.schemas.eval import EvalReport, FailedQueryDetail
from eval.ragas_runner import RagasQuerySample, RagasRunner
from eval.runner import EvalRunner
from retrieval.retrieval_engine import RetrievalEngine

logger = structlog.get_logger(__name__)

# Below this RAGAs faithfulness OR answer_relevancy score a query is surfaced in
# failed_queries for reviewer attention (matches the eval-methodology §"borderline
# cluster" attention threshold; not a hard gate).
_RAGAS_ATTENTION_THRESHOLD = 0.70

_RECALL_ONLY_NOTE = (
    "RAGAs 4-metric not run — no Azure OpenAI judge credential configured "
    "(AZURE_OPENAI_API_KEY empty) AND/OR app.state.synthesizer unavailable. "
    "EvalReport.faithfulness / correctness are 0.0 / None placeholders; "
    "Recall@5 is real. Configure .env (Q3 + Q4) for the full RAGAs run."
)

_IMAGE_ASSOCIATION_NOTE = (
    "image_association is a custom image-text correlation metric (not a RAGAs "
    "metric) — not yet wired into the eval orchestrator; stays 0.0. "
    "crag_trigger_rate / avg_cost_per_query_usd similarly deferred (CRAG loop / "
    "realtime_cost.py integration)."
)


async def build_ragas_samples(
    eval_set_path: Path,
    engine: RetrievalEngine,
    synthesizer: object,
    kb_id: str,
    max_main_queries: int | None = None,
) -> list[RagasQuerySample]:
    """Run the RAG pipeline (retrieve → synthesize) per main (non-OOS) query and
    assemble `RagasQuerySample`s. OOS queries are skipped (refusal accuracy is
    evaluated separately). `synthesizer` must expose `async synthesize(query, chunks)
    -> .answer`. Bounded by `max_main_queries` for cost containment."""
    import yaml  # noqa: PLC0415

    eval_set = yaml.safe_load(eval_set_path.read_text(encoding="utf-8"))
    queries = eval_set.get("queries", [])

    samples: list[RagasQuerySample] = []
    built = 0
    for q in queries:
        if q.get("ground_truth", {}).get("expected_refusal", False):
            continue  # OOS — evaluated separately for refusal accuracy
        if max_main_queries is not None and built >= max_main_queries:
            break
        query_id = str(q.get("query_id", ""))
        question = str(q.get("query_text", ""))
        q_kb_id = str(q.get("kb_id") or kb_id)  # ADR-0018 per-query override
        try:
            retrieval = await engine.retrieve(query=question, kb_id=q_kb_id, top_k=5)
            contexts = [str(c.fields.get("chunk_text", "")) for c in retrieval.chunks]
            synth = await synthesizer.synthesize(question, retrieval.chunks)  # type: ignore[attr-defined]
            answer = str(getattr(synth, "answer", ""))
        except Exception as exc:  # noqa: BLE001 — surface as an empty sample; RagasRunner errors it
            logger.warning("ragas_sample_build_failed", query_id=query_id, error=str(exc))
            contexts, answer = [], ""
        samples.append(
            RagasQuerySample(
                query_id=query_id,
                question=question,
                contexts=contexts,
                answer=answer,
                reference=str(q.get("ground_truth", {}).get("reference_answer", "") or ""),
                expected_keywords=[
                    str(k) for k in (q.get("ground_truth", {}).get("expected_answer_keywords") or [])
                ],
            ),
        )
        built += 1
    return samples


async def run_eval_pipeline(
    eval_set_path: Path,
    engine: RetrievalEngine,
    kb_id: str = "drive_user_manuals",
    max_main_queries: int | None = None,
    synthesizer: object | None = None,
    ragas_evaluator: Callable[[RagasQuerySample], dict] | None = None,
    judge_deployment: str = "",
) -> EvalReport:
    """Run `EvalRunner` (Recall@5) + — when `synthesizer` AND `ragas_evaluator`
    are both supplied — the RAGAs 4-metric judge pass; return a populated
    `EvalReport`. Without those, returns the Recall@5-only report (CI / local)."""
    runner = EvalRunner(engine=engine, top_k=5, kb_id=kb_id)
    runner_report = await runner.run(eval_set_path, max_main_queries=max_main_queries)

    failed: list[FailedQueryDetail] = []
    for r in runner_report.per_query:
        if r.error is not None:
            failed.append(FailedQueryDetail(
                query_id=r.query_id,
                query=r.query_text,
                expected="(see eval-set ground_truth)",
                got=f"error: {r.error}",
                metric_failed=["recall_at_5"],
            ))

    embed_lat = sorted(
        (r.embed_latency_ms + r.search_latency_ms)
        for r in runner_report.per_query if r.error is None
    )
    p95_idx = int(0.95 * (len(embed_lat) - 1)) if embed_lat else 0
    p95_latency_ms = embed_lat[p95_idx] if embed_lat else 0

    faithfulness = 0.0
    correctness: float | None = None
    if synthesizer is not None and ragas_evaluator is not None:
        samples = await build_ragas_samples(
            eval_set_path, engine, synthesizer, kb_id, max_main_queries=max_main_queries,
        )
        ragas_report = RagasRunner(
            judge_deployment=judge_deployment, evaluator=ragas_evaluator,
        ).evaluate(
            samples,
            eval_set_name=eval_set_path.name,
            eval_set_version=runner_report.eval_set_version,
        )
        faithfulness = ragas_report.aggregates["faithfulness"].mean
        correctness = ragas_report.aggregates["answer_relevancy"].mean
        for qr in ragas_report.per_query:
            if qr.error is not None:
                failed.append(FailedQueryDetail(
                    query_id=qr.query_id,
                    query="(RAGAs judge error)",
                    expected="(4-metric score)",
                    got=f"error: {qr.error}",
                    metric_failed=["faithfulness", "answer_relevancy", "context_precision", "context_recall"],
                ))
            else:
                low = [
                    m for m in ("faithfulness", "answer_relevancy", "context_precision", "context_recall")
                    if getattr(qr, m) < _RAGAS_ATTENTION_THRESHOLD
                ]
                if low:
                    failed.append(FailedQueryDetail(
                        query_id=qr.query_id,
                        query="(below attention threshold)",
                        expected=f">= {_RAGAS_ATTENTION_THRESHOLD}",
                        got=", ".join(f"{m}={getattr(qr, m):.2f}" for m in low),
                        metric_failed=low,
                    ))
    else:
        failed.append(FailedQueryDetail(
            query_id="_ragas_not_run",
            query="(orchestrator note)",
            expected="(faithfulness / correctness)",
            got=_RECALL_ONLY_NOTE,
            metric_failed=["faithfulness", "correctness"],
        ))

    failed.append(FailedQueryDetail(
        query_id="_metrics_deferred_note",
        query="(orchestrator note)",
        expected="(image_association / crag_trigger_rate / avg_cost_per_query_usd)",
        got=_IMAGE_ASSOCIATION_NOTE,
        metric_failed=["image_association", "crag_trigger_rate", "avg_cost_per_query_usd"],
    ))

    logger.info(
        "eval_orchestrator_complete",
        eval_set=runner_report.eval_set,
        recall_at_5=runner_report.aggregate_recall_at_5,
        faithfulness=round(faithfulness, 4),
        correctness=(round(correctness, 4) if correctness is not None else None),
        evaluated=runner_report.queries_evaluated,
        errored=runner_report.queries_errored,
        p95_latency_ms=p95_latency_ms,
        ragas_run=(synthesizer is not None and ragas_evaluator is not None),
    )

    return EvalReport(
        recall_at_5=runner_report.aggregate_recall_at_5,
        faithfulness=round(faithfulness, 4),
        correctness=(round(correctness, 4) if correctness is not None else None),
        image_association=0.0,
        p95_latency_ms=p95_latency_ms,
        failed_queries=failed,
        crag_trigger_rate=0.0,
        avg_cost_per_query_usd=0.0,
    )
