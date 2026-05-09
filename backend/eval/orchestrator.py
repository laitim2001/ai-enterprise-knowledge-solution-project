"""Eval orchestrator for /eval/run + /eval/shootout endpoints (W16 F5.4 CO_W15_F1).

Wires existing W2 EvalRunner (Recall@5) into api/schemas/eval.py EvalReport
schema. Per Decision C.1 (Both endpoints full implementation):
- /eval/run consumes this orchestrator with current app.state.retrieval_engine
- /eval/shootout iterates rerankers by reconstructing engines per reranker

Tier 1 baseline scope (W17+ RAGAs full integration deferred per cost + latency
analysis — Beta cohort ~50 queries × ~5 RAGAs LLM calls each = ~250 judge
LLM calls per /eval/run; synchronous endpoint with multi-minute response =
bad UX). RAGAs full 4-metric integration via background job (FastAPI
BackgroundTasks) deferred to W17+ housekeeping per W16 plan §3 PARTIAL PASS
allowance.

For W17+ RAGAs integration, see existing modules:
- backend/eval/ragas_runner.py — RagasRunner with judge LLM
- scripts/run_ragas_eval.py — CLI entry point pattern to copy

Tier 1 baseline returns:
- recall_at_5 — from EvalRunner (real)
- faithfulness / correctness / image_association — 0.0 placeholders with
  failed_queries note documenting deferral to W17+ RAGAs background job
- p95_latency_ms — from per-query embed+search timing
- failed_queries — actual EvalRunner errored queries + RAGAs deferral note
- crag_trigger_rate — 0.0 (CRAG correlation requires Synthesizer wiring;
  W17+ when synthesizer reachable in eval orchestrator)
- avg_cost_per_query_usd — 0.0 placeholder (cost tracking via
  realtime_cost.py independent of eval orchestrator)
"""

from __future__ import annotations

from pathlib import Path

import structlog

from api.schemas.eval import EvalReport, FailedQueryDetail
from eval.runner import EvalRunner
from retrieval.retrieval_engine import RetrievalEngine

logger = structlog.get_logger(__name__)

_RAGAS_DEFERRAL_NOTE = (
    "RAGAs 4-metric (faithfulness / answer_relevancy / context_precision / "
    "context_recall) deferred to W17+ background job — Tier 1 baseline returns "
    "Recall@5 only per W16 plan §3 PARTIAL PASS allowance."
)


async def run_eval_pipeline(
    eval_set_path: Path,
    engine: RetrievalEngine,
    kb_id: str = "drive_user_manuals",
    max_main_queries: int | None = None,
) -> EvalReport:
    """Run EvalRunner against engine; return EvalReport with Recall@5 + placeholders.

    Tier 1 baseline (W17+ RAGAs integration deferred per orchestrator docstring).
    """
    runner = EvalRunner(engine=engine, top_k=5, kb_id=kb_id)
    runner_report = await runner.run(eval_set_path, max_main_queries=max_main_queries)

    failed: list[FailedQueryDetail] = []

    # Surface real EvalRunner errored queries to consumer
    for r in runner_report.per_query:
        if r.error is not None:
            failed.append(FailedQueryDetail(
                query_id=r.query_id,
                query=r.query_text,
                expected="(see eval-set ground_truth)",
                got=f"error: {r.error}",
                metric_failed=["recall_at_5"],
            ))

    # Compute p95 latency from per-query timing (W17+ may extend with synth latency)
    embed_lat = sorted(
        (r.embed_latency_ms + r.search_latency_ms)
        for r in runner_report.per_query if r.error is None
    )
    p95_idx = int(0.95 * (len(embed_lat) - 1)) if embed_lat else 0
    p95_latency_ms = embed_lat[p95_idx] if embed_lat else 0

    # W17+ deferral transparency via failed_queries note (avoids mutating schema)
    failed.append(FailedQueryDetail(
        query_id="_w17_ragas_deferral_note",
        query="(orchestrator note)",
        expected="(see W16 plan §3 PARTIAL PASS allowance)",
        got=_RAGAS_DEFERRAL_NOTE,
        metric_failed=["faithfulness", "correctness", "image_association"],
    ))

    logger.info(
        "eval_orchestrator_complete",
        eval_set=runner_report.eval_set,
        recall_at_5=runner_report.aggregate_recall_at_5,
        evaluated=runner_report.queries_evaluated,
        errored=runner_report.queries_errored,
        p95_latency_ms=p95_latency_ms,
    )

    return EvalReport(
        recall_at_5=runner_report.aggregate_recall_at_5,
        faithfulness=0.0,  # W17+ RAGAs deferral
        correctness=None,  # W17+ RAGAs deferral
        image_association=0.0,  # W17+ image-text correlation deferral
        p95_latency_ms=p95_latency_ms,
        failed_queries=failed,
        crag_trigger_rate=0.0,  # W17+ when synthesizer reachable in orchestrator
        avg_cost_per_query_usd=0.0,  # cost tracking via realtime_cost.py independent
    )
