"""W2 baseline eval runner — load eval-set YAML, invoke RetrievalEngine, compute Recall@5.

Two recall modes (auto-selected per query):
- **strict**:    when query.annotation.validated == True AND ground_truth.acceptable_chunk_ids
                 contains real chunk_ids → measure |retrieved ∩ acceptable| / |acceptable|
- **keyword**:   fallback when chunk_ids are placeholder (validated=False)
                 → 1.0 if ALL expected_answer_keywords found in top-5 chunk_text (case-insensitive),
                   else fraction = |found keywords| / |expected keywords|

OOS queries (expected_refusal=True) are tracked separately (W3 generation will measure
refusal accuracy; W2 baseline excludes from Recall@5 aggregate).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

import structlog
import yaml

from retrieval.retrieval_engine import RetrievalEngine

logger = structlog.get_logger(__name__)

RecallMode = Literal["strict", "keyword"]


@dataclass(slots=True)
class QueryEvalResult:
    """One query's evaluation outcome."""

    query_id: str
    query_text: str
    mode: RecallMode  # which scoring mode applied
    recall_at_5: float
    is_oos: bool
    retrieved_chunk_ids: list[str]
    expected_chunk_ids: list[str]  # acceptable_chunk_ids (strict) or [] (keyword mode)
    expected_keywords: list[str]   # for keyword mode (always populated for traceability)
    matched_keywords: list[str]    # subset that appeared in top-5
    embed_latency_ms: int
    search_latency_ms: int
    error: str | None = None


@dataclass(slots=True)
class EvalReport:
    """Aggregate eval report → serialized as reports/gate1_w2.yaml."""

    eval_set: str
    eval_set_version: str
    started_at: str
    finished_at: str
    total_queries: int
    main_queries: int  # non-OOS
    oos_queries: int
    queries_evaluated: int
    queries_errored: int
    aggregate_recall_at_5: float  # over main_queries (non-OOS, no errors)
    mode_breakdown: dict[str, int]  # {"strict": N, "keyword": M}
    avg_embed_latency_ms: float
    avg_search_latency_ms: float
    per_query: list[QueryEvalResult] = field(default_factory=list)


class EvalRunner:
    """Run a YAML eval set against a RetrievalEngine, emit EvalReport.

    W16+ ADR-0018 multi-KB invariant: kb_id parameter required by RetrievalEngine.
    EvalRunner defaults to "drive_user_manuals" (Tier 1 single-KB Q7 Resolved baseline);
    individual queries can override via `q.get("kb_id")` in eval-set YAML for multi-KB
    eval sets (W16+ deliverable per `eval_set_augmentor.py` extension).
    """

    def __init__(
        self,
        engine: RetrievalEngine,
        top_k: int = 5,
        kb_id: str = "drive_user_manuals",
    ) -> None:
        self._engine = engine
        self._top_k = top_k
        self._kb_id = kb_id

    async def run(
        self,
        eval_set_path: Path,
        max_main_queries: int | None = None,
    ) -> EvalReport:
        """Run eval-set against engine, optionally capped at first N main(non-OOS)queries.

        max_main_queries=None(default)→ run all queries(W2 baseline behaviour preserved).
        max_main_queries=N → run first N non-OOS queries + ALL OOS queries(OOS not counted
        toward N since they're tracked separately for refusal accuracy per `is_oos` flag).
        Cost-containment knob for partial-eval cost discovery(W4 plan §4 R4)— W5 D1 fixed
        prior driver-side bug where `--subset` only capped final aggregation but actual API
        calls still ran the full eval-set.
        """
        eval_set = yaml.safe_load(eval_set_path.read_text(encoding="utf-8"))
        version = str(eval_set.get("metadata", {}).get("version", "unknown"))
        queries = eval_set.get("queries", [])

        started_at = datetime.now(UTC).isoformat()
        per_query: list[QueryEvalResult] = []

        main_evaluated = 0
        for q in queries:
            is_oos = bool(q.get("ground_truth", {}).get("expected_refusal", False))
            if max_main_queries is not None and not is_oos and main_evaluated >= max_main_queries:
                continue  # cap reached on main queries; skip remaining (OOS still pass-through)
            result = await self._evaluate_query(q)
            per_query.append(result)
            if not is_oos:
                main_evaluated += 1

        finished_at = datetime.now(UTC).isoformat()
        return _aggregate(eval_set_path.name, version, started_at, finished_at, per_query)

    async def _evaluate_query(self, q: dict) -> QueryEvalResult:
        query_id = str(q.get("query_id", ""))
        query_text = str(q.get("query_text", ""))
        ground_truth = q.get("ground_truth", {})
        is_oos = bool(ground_truth.get("expected_refusal", False))
        validated = bool(q.get("annotation", {}).get("validated", False))

        # ADR-0018 multi-KB invariant: per-query kb_id override OR runner default.
        kb_id = str(q.get("kb_id") or self._kb_id)
        try:
            retrieval = await self._engine.retrieve(
                query=query_text, kb_id=kb_id, top_k=self._top_k,
            )
        except Exception as exc:  # noqa: BLE001 — surface error per query
            return QueryEvalResult(
                query_id=query_id,
                query_text=query_text,
                mode="strict",
                recall_at_5=0.0,
                is_oos=is_oos,
                retrieved_chunk_ids=[],
                expected_chunk_ids=[],
                expected_keywords=[],
                matched_keywords=[],
                embed_latency_ms=0,
                search_latency_ms=0,
                error=f"{type(exc).__name__}: {exc}",
            )

        retrieved_ids = [
            str(c.fields.get("chunk_id", "")) for c in retrieval.chunks
        ]
        retrieved_text_lower = "\n".join(
            str(c.fields.get("chunk_text", "")).lower() for c in retrieval.chunks
        )

        acceptable_ids = list(ground_truth.get("acceptable_chunk_ids") or [])
        expected_keywords = [str(k) for k in (ground_truth.get("expected_answer_keywords") or [])]

        # Mode selection: strict if validated AND acceptable_ids look like real ids
        # (placeholder ids start with "kb-drive_doc-M" per eval-set-v0 convention)
        use_strict = validated and acceptable_ids and not any(
            ch.startswith("kb-drive_doc-M0") for ch in acceptable_ids
        )

        if use_strict:
            matched = set(retrieved_ids) & set(acceptable_ids)
            recall = len(matched) / max(1, len(acceptable_ids))
            mode: RecallMode = "strict"
            matched_kws: list[str] = []
        else:
            matched_kws = [
                k for k in expected_keywords if k.lower() in retrieved_text_lower
            ]
            recall = (
                len(matched_kws) / max(1, len(expected_keywords))
                if expected_keywords
                else 0.0
            )
            mode = "keyword"

        return QueryEvalResult(
            query_id=query_id,
            query_text=query_text,
            mode=mode,
            recall_at_5=recall,
            is_oos=is_oos,
            retrieved_chunk_ids=retrieved_ids,
            expected_chunk_ids=acceptable_ids if use_strict else [],
            expected_keywords=expected_keywords,
            matched_keywords=matched_kws,
            embed_latency_ms=retrieval.embed_latency_ms,
            search_latency_ms=retrieval.search_latency_ms,
        )


def _aggregate(
    eval_set_name: str,
    version: str,
    started_at: str,
    finished_at: str,
    per_query: list[QueryEvalResult],
) -> EvalReport:
    main_results = [r for r in per_query if not r.is_oos]
    oos_count = sum(1 for r in per_query if r.is_oos)
    errored = [r for r in per_query if r.error is not None]
    main_evaluated = [r for r in main_results if r.error is None]

    aggregate_recall = (
        sum(r.recall_at_5 for r in main_evaluated) / len(main_evaluated)
        if main_evaluated
        else 0.0
    )

    mode_breakdown: dict[str, int] = {"strict": 0, "keyword": 0}
    for r in main_evaluated:
        mode_breakdown[r.mode] += 1

    avg_embed = (
        sum(r.embed_latency_ms for r in main_evaluated) / len(main_evaluated)
        if main_evaluated
        else 0.0
    )
    avg_search = (
        sum(r.search_latency_ms for r in main_evaluated) / len(main_evaluated)
        if main_evaluated
        else 0.0
    )

    logger.info(
        "eval_run_complete",
        total=len(per_query),
        main=len(main_results),
        oos=oos_count,
        evaluated=len(main_evaluated),
        errored=len(errored),
        recall_at_5=round(aggregate_recall, 3),
    )

    return EvalReport(
        eval_set=eval_set_name,
        eval_set_version=version,
        started_at=started_at,
        finished_at=finished_at,
        total_queries=len(per_query),
        main_queries=len(main_results),
        oos_queries=oos_count,
        queries_evaluated=len(main_evaluated),
        queries_errored=len(errored),
        aggregate_recall_at_5=round(aggregate_recall, 4),
        mode_breakdown=mode_breakdown,
        avg_embed_latency_ms=round(avg_embed, 1),
        avg_search_latency_ms=round(avg_search, 1),
        per_query=per_query,
    )


def report_to_yaml(report: EvalReport) -> str:
    """Serialize EvalReport to YAML string (round-trip via pyyaml)."""
    payload = {
        "metadata": {
            "eval_set": report.eval_set,
            "eval_set_version": report.eval_set_version,
            "started_at": report.started_at,
            "finished_at": report.finished_at,
        },
        "aggregate": {
            "total_queries": report.total_queries,
            "main_queries": report.main_queries,
            "oos_queries": report.oos_queries,
            "queries_evaluated": report.queries_evaluated,
            "queries_errored": report.queries_errored,
            "aggregate_recall_at_5": report.aggregate_recall_at_5,
            "mode_breakdown": report.mode_breakdown,
            "avg_embed_latency_ms": report.avg_embed_latency_ms,
            "avg_search_latency_ms": report.avg_search_latency_ms,
        },
        "per_query": [
            {
                "query_id": r.query_id,
                "query_text": r.query_text,
                "mode": r.mode,
                "recall_at_5": round(r.recall_at_5, 3),
                "is_oos": r.is_oos,
                "retrieved_chunk_ids": r.retrieved_chunk_ids,
                "expected_chunk_ids": r.expected_chunk_ids,
                "expected_keywords": r.expected_keywords,
                "matched_keywords": r.matched_keywords,
                "embed_latency_ms": r.embed_latency_ms,
                "search_latency_ms": r.search_latency_ms,
                "error": r.error,
            }
            for r in report.per_query
        ],
    }
    return yaml.safe_dump(payload, sort_keys=False, allow_unicode=True)
