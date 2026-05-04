"""W5 D3 F2.1 — CRAG grader confidence distribution smoke (per W4 plan §F2 + W4 R6).

Runs CragGrader on first N main(non-OOS)eval-set queries to capture the LIVE
grader confidence distribution。Used for empirical CRAG threshold calibration:

- W4 D1 baseline: `Settings.crag_confidence_threshold = 0.70`(plan-draft 0.6
  bumped to 0.70 since 0.6 too lenient triggers correction rarely on healthy
  retrievals)。Both values pre-LIVE — no real distribution data behind choice。
- W5 D2 Phase 1 RAGAs subset=20: faithfulness 0.944 / answer_relevancy 0.795 /
  context_precision 0.986 / context_recall 1.000 → Cohere v4.0-pro pipeline
  retrieval quality is high and most queries should be CONFIDENT(grader output
  closer to 1.0 than 0.5)。
- This driver answers:**given the same 20-query sample**,what's the empirical
  grader confidence distribution? Which threshold ∈ {0.65, 0.70, 0.75} would
  trigger correction for the right queries(the ones that ALSO had low RAGAs
  faithfulness/relevancy)without false-correcting healthy retrievals?

Cost-shape: per-query call = 1 embedding + 1 search + 1 cohere rerank +
1 grader chat completion(GPT-5.4-mini judge)。Skips synthesize + RAGAs to
contain cost(~$1 USD for 20 queries vs F1.7 RAGAs subset=20 ~$15-25)。

Usage(from project root):
    backend/.venv/Scripts/python.exe -m scripts.run_crag_grade_smoke
    backend/.venv/Scripts/python.exe -m scripts.run_crag_grade_smoke --subset 20

Output:`reports/crag-grade-smoke.json` per-query confidence + aggregate stats
(mean / median / p25 / p75 / p95)+ threshold-trigger counts at 0.65 / 0.70 /
0.75 / 0.80 candidates。
"""

from __future__ import annotations

import truststore

truststore.inject_into_ssl()

import argparse
import asyncio
import json
import statistics
import sys
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path

import yaml

_BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from generation.crag import CragGrader  # noqa: E402
from ingestion.embedding.azure_openai_embedder import AzureOpenAIEmbedder  # noqa: E402
from retrieval.hybrid import HybridSearcher  # noqa: E402
from retrieval.reranker.factory import make_reranker  # noqa: E402
from retrieval.retrieval_engine import RetrievalEngine  # noqa: E402
from storage.settings import get_settings  # noqa: E402

DEFAULT_EVAL_SET = Path("docs/eval-set-v1-draft.yaml")
DEFAULT_OUTPUT = Path("reports/crag-grade-smoke.json")
THRESHOLD_CANDIDATES = (0.65, 0.70, 0.75, 0.80)


@dataclass(slots=True)
class PerQueryGrade:
    query_id: str
    query_text: str
    confidence: float
    raw_text: str
    chunks_in: int
    grader_input_tokens: int
    grader_output_tokens: int
    grader_latency_ms: int
    error: str | None = None


@dataclass(slots=True)
class GradeSummary:
    eval_set: str
    subset: int
    started_at: str
    finished_at: str
    queries_evaluated: int
    queries_errored: int
    mean: float
    median: float
    p25: float
    p75: float
    p95: float
    threshold_triggers: dict[str, int] = field(default_factory=dict)
    per_query: list[PerQueryGrade] = field(default_factory=list)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="W5 D3 F2.1 CRAG grader confidence distribution")
    parser.add_argument("--eval-set", type=Path, default=DEFAULT_EVAL_SET)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--subset", type=int, default=20)
    return parser.parse_args()


def _load_main_queries(eval_set_path: Path, subset: int) -> list[dict]:
    eval_set = yaml.safe_load(eval_set_path.read_text(encoding="utf-8"))
    queries = eval_set.get("queries", [])
    main = [q for q in queries if not q.get("ground_truth", {}).get("expected_refusal", False)]
    if subset > 0:
        main = main[:subset]
    return main


def _percentile(sorted_values: list[float], pct: int) -> float:
    if not sorted_values:
        return 0.0
    k = (len(sorted_values) - 1) * (pct / 100)
    lo = int(k)
    hi = min(lo + 1, len(sorted_values) - 1)
    frac = k - lo
    return sorted_values[lo] * (1 - frac) + sorted_values[hi] * frac


async def _amain() -> int:
    args = _parse_args()
    settings = get_settings()
    if not (settings.azure_openai_api_key and settings.azure_search_admin_key):
        print("FAIL: AZURE_OPENAI_API_KEY or AZURE_SEARCH_ADMIN_KEY unset", file=sys.stderr)
        return 1

    queries = _load_main_queries(args.eval_set, args.subset)
    print(f"Loaded {len(queries)} main queries (subset={args.subset})")

    embedder = AzureOpenAIEmbedder(
        endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key,
        api_version=settings.azure_openai_api_version,
        deployment=settings.azure_openai_deployment_embedding,
        dimensions=settings.embedding_dimension,
    )
    searcher = HybridSearcher(
        endpoint=settings.azure_search_endpoint,
        admin_key=settings.azure_search_admin_key,
        index_name=settings.azure_search_default_index,
    )
    reranker = make_reranker(settings)
    grader = CragGrader(
        endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key,
        api_version=settings.azure_openai_api_version,
        deployment=settings.azure_openai_deployment_llm_judge,
    )

    started_at = datetime.now(UTC).isoformat()
    per_query: list[PerQueryGrade] = []

    async with embedder, searcher, grader:
        if reranker is not None:
            await reranker.__aenter__()  # type: ignore[attr-defined]
        try:
            engine = RetrievalEngine(
                embedder=embedder, searcher=searcher, reranker=reranker,
                hybrid_overfetch_for_rerank=settings.hybrid_top_k_retrieval,
            )
            for q in queries:
                qid = str(q.get("query_id", ""))
                qtext = str(q.get("query_text", ""))
                try:
                    retrieval = await engine.retrieve(query=qtext, top_k=settings.rerank_top_k)
                    grade = await grader.grade(qtext, retrieval.chunks)
                    per_query.append(PerQueryGrade(
                        query_id=qid, query_text=qtext,
                        confidence=grade.confidence, raw_text=grade.raw_text,
                        chunks_in=len(retrieval.chunks),
                        grader_input_tokens=grade.input_tokens,
                        grader_output_tokens=grade.output_tokens,
                        grader_latency_ms=grade.latency_ms,
                    ))
                    print(f"  {qid}: confidence={grade.confidence:.3f}  raw='{grade.raw_text[:30]}'")
                except Exception as exc:  # noqa: BLE001
                    per_query.append(PerQueryGrade(
                        query_id=qid, query_text=qtext,
                        confidence=0.0, raw_text="", chunks_in=0,
                        grader_input_tokens=0, grader_output_tokens=0, grader_latency_ms=0,
                        error=f"{type(exc).__name__}: {exc}",
                    ))
                    print(f"  {qid}: ERR {type(exc).__name__}", file=sys.stderr)
        finally:
            if reranker is not None:
                await reranker.__aexit__(None, None, None)  # type: ignore[attr-defined]

    finished_at = datetime.now(UTC).isoformat()

    confidences = [p.confidence for p in per_query if p.error is None]
    sorted_conf = sorted(confidences)
    summary = GradeSummary(
        eval_set=args.eval_set.name,
        subset=args.subset,
        started_at=started_at,
        finished_at=finished_at,
        queries_evaluated=len(confidences),
        queries_errored=sum(1 for p in per_query if p.error),
        mean=round(statistics.mean(confidences), 4) if confidences else 0.0,
        median=round(statistics.median(confidences), 4) if confidences else 0.0,
        p25=round(_percentile(sorted_conf, 25), 4),
        p75=round(_percentile(sorted_conf, 75), 4),
        p95=round(_percentile(sorted_conf, 95), 4),
        threshold_triggers={
            f"{t:.2f}": sum(1 for c in confidences if c < t)
            for t in THRESHOLD_CANDIDATES
        },
        per_query=per_query,
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(asdict(summary), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"\n[results] CRAG grader confidence distribution(n={summary.queries_evaluated}):")
    print(f"  mean={summary.mean:.3f}  median={summary.median:.3f}")
    print(f"  p25={summary.p25:.3f}  p75={summary.p75:.3f}  p95={summary.p95:.3f}")
    print("\n  Threshold trigger counts (queries with confidence < threshold):")
    for t, n in summary.threshold_triggers.items():
        pct = 100 * n / max(1, summary.queries_evaluated)
        print(f"    {t}: {n}/{summary.queries_evaluated} ({pct:.0f}% would trigger correction)")
    print(f"\n[output] Full JSON -> {args.output}")
    return 0


def main() -> int:
    try:
        return asyncio.run(_amain())
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else 1
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
