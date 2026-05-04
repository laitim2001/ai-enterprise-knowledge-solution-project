"""W4 D3 F3 — 4-way reranker shootout driver.

Runs the same eval-set against each available reranker backend and emits a
per-reranker comparison table:

    reranker     R@5     latency_ms (avg)    candidates_evaluated
    -----------  ------  -------------------  --------------------
    cohere       0.815   142                  20
    voyage       0.840   118                  20
    zeroentropy  0.795   128                  20
    azure        0.770   165                  20
    hybrid-only  0.700   45                   20

For each reranker, the driver:
1. Builds a fresh RetrievalEngine wired with that reranker (via make_reranker
   override on a copy of Settings with reranker_kind set).
2. Runs the eval-set through EvalRunner (W2 baseline R@5 metric).
3. Records aggregate R@5 + avg latency.

Procurement awareness (per W4 plan §4 R1+R2):
- Each reranker is skipped (with a `(SKIPPED — key/endpoint unset)` note in
  the comparison table) when its required env keys are missing. The shootout
  STILL emits the table for whatever rerankers ARE configured + the
  hybrid-only baseline. This lets W4 D3 land structurally even if Voyage /
  ZeroEntropy keys are still pending.

Usage (from project root, post Azure OpenAI / AI Search live):
    backend/.venv/Scripts/python.exe -m scripts.run_reranker_shootout
    backend/.venv/Scripts/python.exe -m scripts.run_reranker_shootout \
        --eval-set docs/eval-set-v1-draft.yaml \
        --output reports/reranker-shootout.json \
        --subset 20

Exit codes:
    0 — shootout ran end-to-end, JSON written; ≥1 reranker evaluated
    1 — env missing OR no reranker evaluable OR runtime exception
"""

from __future__ import annotations

# Use OS trust store (Windows Cert Store) for TLS verification so Ricoh corp
# proxy SSL inspection is honoured. Must run before any ssl/urllib3/httpx import.
import truststore

truststore.inject_into_ssl()

import argparse
import asyncio
import json
import sys
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path

_BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from eval.runner import EvalRunner  # noqa: E402
from ingestion.embedding.azure_openai_embedder import AzureOpenAIEmbedder  # noqa: E402
from retrieval.hybrid import HybridSearcher  # noqa: E402
from retrieval.reranker.factory import make_reranker  # noqa: E402
from retrieval.retrieval_engine import RetrievalEngine  # noqa: E402
from storage.settings import Settings, get_settings  # noqa: E402

DEFAULT_EVAL_SET = Path("docs/eval-set-v1-draft.yaml")
DEFAULT_OUTPUT = Path("reports/reranker-shootout.json")
SHOOTOUT_KINDS = ("hybrid-only", "cohere", "voyage", "zeroentropy", "azure")


@dataclass(slots=True)
class RerankerRunSummary:
    kind: str
    skipped: bool
    skip_reason: str
    aggregate_recall_at_5: float
    queries_evaluated: int
    queries_errored: int
    avg_embed_latency_ms: float
    avg_search_latency_ms: float


@dataclass(slots=True)
class ShootoutReport:
    eval_set: str
    subset: int
    started_at: str
    finished_at: str
    runs: list[RerankerRunSummary] = field(default_factory=list)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="W4 D3 F3 4-way reranker shootout")
    parser.add_argument(
        "--eval-set", type=Path, default=DEFAULT_EVAL_SET,
        help=f"YAML eval-set path (default: {DEFAULT_EVAL_SET})",
    )
    parser.add_argument(
        "--output", type=Path, default=DEFAULT_OUTPUT,
        help=f"Output JSON path (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--subset", type=int, default=0,
        help="Subset to first N eval-set queries (0 = all; cost containment per W4 plan §4 R4)",
    )
    return parser.parse_args()


def _settings_for_kind(base: Settings, kind: str) -> Settings:
    """Return a Settings copy with reranker_kind overridden."""
    if kind == "hybrid-only":
        # `off` produces None reranker → hybrid-only fallback per factory contract
        return base.model_copy(update={"reranker_kind": "off"})
    return base.model_copy(update={"reranker_kind": kind})


def _skip_reason(kind: str, settings: Settings) -> str:
    """Return non-empty reason if `kind` cannot run with current Settings."""
    if kind == "hybrid-only":
        return ""
    if kind == "cohere" and not (settings.cohere_endpoint and settings.cohere_api_key):
        return "cohere_endpoint or cohere_api_key unset (.env Q5 procurement pending)"
    if kind == "voyage" and not settings.voyage_api_key:
        return "voyage_api_key unset (.env Chris procurement pending per W4 plan §F3)"
    if kind == "zeroentropy" and not settings.zeroentropy_api_key:
        return "zeroentropy_api_key unset (.env Chris procurement pending per W4 plan §F3)"
    if kind == "azure" and not (settings.azure_search_endpoint and settings.azure_search_admin_key):
        return "azure_search_endpoint or admin_key unset"
    return ""


async def _run_one_kind(
    kind: str,
    base_settings: Settings,
    eval_set: Path,
    subset: int,
) -> RerankerRunSummary:
    """Build a fresh RetrievalEngine for `kind` and run the eval-set."""
    skip = _skip_reason(kind, base_settings)
    if skip:
        return RerankerRunSummary(
            kind=kind, skipped=True, skip_reason=skip,
            aggregate_recall_at_5=0.0, queries_evaluated=0,
            queries_errored=0, avg_embed_latency_ms=0.0,
            avg_search_latency_ms=0.0,
        )

    settings = _settings_for_kind(base_settings, kind)
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

    async with embedder, searcher:
        if reranker is not None:
            await reranker.__aenter__()  # type: ignore[attr-defined]
        try:
            engine = RetrievalEngine(
                embedder=embedder, searcher=searcher, reranker=reranker,
                hybrid_overfetch_for_rerank=settings.hybrid_top_k_retrieval,
            )
            runner = EvalRunner(engine, top_k=settings.rerank_top_k)
            report = await runner.run(eval_set)
        finally:
            if reranker is not None:
                await reranker.__aexit__(None, None, None)  # type: ignore[attr-defined]

    if subset > 0:
        # When subset requested, scale aggregates to first-N main queries by
        # recomputing on the prefix (cheaper than re-running the eval).
        prefix = [r for r in report.per_query if not r.is_oos][:subset]
        if prefix:
            recall = sum(r.recall_at_5 for r in prefix if r.error is None) / max(
                1, len([r for r in prefix if r.error is None]),
            )
            avg_embed = sum(r.embed_latency_ms for r in prefix) / max(1, len(prefix))
            avg_search = sum(r.search_latency_ms for r in prefix) / max(1, len(prefix))
            return RerankerRunSummary(
                kind=kind, skipped=False, skip_reason="",
                aggregate_recall_at_5=round(recall, 4),
                queries_evaluated=len([r for r in prefix if r.error is None]),
                queries_errored=len([r for r in prefix if r.error is not None]),
                avg_embed_latency_ms=round(avg_embed, 1),
                avg_search_latency_ms=round(avg_search, 1),
            )

    return RerankerRunSummary(
        kind=kind, skipped=False, skip_reason="",
        aggregate_recall_at_5=report.aggregate_recall_at_5,
        queries_evaluated=report.queries_evaluated,
        queries_errored=report.queries_errored,
        avg_embed_latency_ms=report.avg_embed_latency_ms,
        avg_search_latency_ms=report.avg_search_latency_ms,
    )


async def _amain() -> int:
    args = _parse_args()
    eval_set: Path = args.eval_set
    output: Path = args.output
    subset: int = args.subset

    base_settings = get_settings()
    if not (base_settings.azure_openai_api_key and base_settings.azure_search_admin_key):
        print(
            "missing AZURE_OPENAI_API_KEY or AZURE_SEARCH_ADMIN_KEY — populate .env per Q3 + Q4",
            file=sys.stderr,
        )
        return 1

    started_at = datetime.now(UTC).isoformat()
    runs: list[RerankerRunSummary] = []
    for kind in SHOOTOUT_KINDS:
        print(f"\n=== Running {kind} ===")
        run = await _run_one_kind(kind, base_settings, eval_set, subset)
        if run.skipped:
            print(f"  SKIPPED — {run.skip_reason}")
        else:
            print(
                f"  R@5={run.aggregate_recall_at_5:.4f}  "
                f"avg_search_latency_ms={run.avg_search_latency_ms:.1f}  "
                f"evaluated={run.queries_evaluated}",
            )
        runs.append(run)
    finished_at = datetime.now(UTC).isoformat()

    report = ShootoutReport(
        eval_set=eval_set.name,
        subset=subset,
        started_at=started_at,
        finished_at=finished_at,
        runs=runs,
    )

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(asdict(report), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # Comparison table to stdout
    print("\n📊 Reranker shootout results:")
    print(f"  {'reranker':<14}{'R@5':>8}{'search_ms':>12}{'embed_ms':>12}  status")
    print("  " + "-" * 60)
    for r in runs:
        if r.skipped:
            print(f"  {r.kind:<14}{'-':>8}{'-':>12}{'-':>12}  SKIPPED ({r.skip_reason})")
        else:
            print(
                f"  {r.kind:<14}{r.aggregate_recall_at_5:>8.4f}"
                f"{r.avg_search_latency_ms:>12.1f}{r.avg_embed_latency_ms:>12.1f}"
                f"  evaluated={r.queries_evaluated}",
            )
    print(f"\n📁 Full JSON → {output}")

    if not any(not r.skipped for r in runs):
        print("\nFAIL: no reranker evaluable; check .env keys", file=sys.stderr)
        return 1
    return 0


def main() -> int:
    try:
        return asyncio.run(_amain())
    except SystemExit as exc:
        if isinstance(exc.code, int):
            return exc.code
        print(str(exc), file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001 — top-level driver swallows for exit code
        print(f"FAIL: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
