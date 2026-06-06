"""W53 live driver: chunk-strategy self-supervised recall comparison.

For each --strategy: set `kb_config.chunk_strategy` → reindex the KB in place →
regenerate synthetic QA from its own chunks → W52 self-supervised Recall@K. Reports
per-strategy recall + chunk count + best (highest self-retrievability).

兩者合一下半截: W52 recall 基建 → W53 跨 chunk_strategy 比較 (heading_aware vs layout_aware
per ADR-0044). Reuses eval/synthetic_qa.run_synthetic_recall (zero new recall math).

NOTE (methodology honesty): per-config question sets DIFFER (regenerated from each
strategy's own chunks) → recall delta is confounded → this is *self-retrievability*,
NOT a controlled A/B; and it rests on W52 synthetic recall (NOT human ground truth).
Read `best` as a relative signal, not an absolute verdict.

SMOKE-DEFERRED: needs Azure judge cred + indexed KB + stored original sources
(W46 `-sources` container) + Free-tier 402 workaround. The core orchestration
(`backend/eval/strategy_comparison.py`) is unit-tested with stubs. Sequential in-place
reindex leaves the KB in the LAST strategy's state.

Usage (from project root):
    backend/.venv/Scripts/python.exe -m scripts.run_strategy_recall_comparison \\
        --kb-id drive_user_manuals --strategies layout_aware heading_aware \\
        --sample 30 --seed 0 --top-k 5

Exit codes: 0 ran end-to-end; 1 env / judge / engine init / runtime error.
"""

from __future__ import annotations

import truststore

truststore.inject_into_ssl()

import argparse  # noqa: E402
import asyncio  # noqa: E402
import sys  # noqa: E402
from pathlib import Path  # noqa: E402
from types import SimpleNamespace  # noqa: E402

_BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from api.routes.documents import run_kb_reindex  # noqa: E402
from api.server import app, lifespan  # noqa: E402
from eval.runner import EvalReport  # noqa: E402
from eval.strategy_comparison import run_strategy_recall_comparison  # noqa: E402
from eval.synthetic_qa import make_qa_generator, run_synthetic_recall  # noqa: E402
from kb_management import get_kb_service  # noqa: E402
from storage.settings import get_settings  # noqa: E402


async def _amain(args: argparse.Namespace) -> int:
    settings = get_settings()
    if not (settings.azure_openai_api_key and settings.azure_search_admin_key):
        print("ERROR: AZURE_OPENAI_API_KEY / AZURE_SEARCH_ADMIN_KEY missing", file=sys.stderr)
        return 1
    generate_fn = make_qa_generator(settings)
    if generate_fn is None:
        print(
            "ERROR: no Azure OpenAI judge credential — synthetic-QA generator unavailable",
            file=sys.stderr,
        )
        return 1

    args.output_dir.mkdir(parents=True, exist_ok=True)
    current = {"strategy": "init"}

    # Bootstrap the real app lifespan so app.state (engine + ingestion deps) is wired
    # identically to production; run_kb_reindex only reads request.app.state.
    async with lifespan(app):
        engine = app.state.retrieval_engine
        if engine is None:
            print("ERROR: retrieval_engine not initialized (check Azure .env)", file=sys.stderr)
            return 1
        service = get_kb_service()
        request_shim = SimpleNamespace(app=app)

        async def reindex_with_strategy(strategy: str) -> int:
            current["strategy"] = strategy
            status = await service.get(args.kb_id)
            new_config = status.config.model_copy(update={"chunk_strategy": strategy})
            await service.update_config(args.kb_id, new_config)
            await run_kb_reindex(kb_id=args.kb_id, request=request_shim, service=service)  # type: ignore[arg-type]
            docs = await engine.list_documents(args.kb_id)
            return sum(int(d.get("total_chunks") or 0) for d in docs)

        async def recall() -> EvalReport:
            out = args.output_dir / f"synthetic-{current['strategy']}.yaml"
            return await run_synthetic_recall(
                engine,
                args.kb_id,
                generate_fn=generate_fn,
                output_path=out,
                sample_size=args.sample,
                seed=args.seed,
                top_k=args.top_k,
            )

        comparison = await run_strategy_recall_comparison(
            args.kb_id,
            args.strategies,
            reindex_with_strategy_fn=reindex_with_strategy,
            recall_fn=recall,
            top_k=args.top_k,
        )

    print(f"\n{'=' * 64}")
    print("W53 chunk-strategy self-supervised recall comparison")
    print(
        f"  KB: {comparison.kb_id}   sample/seed: {args.sample}/{args.seed}   top-k: {comparison.top_k}"
    )
    print(f"  {'strategy':<16}{'recall@k':>10}{'chunks':>9}{'sample':>8}{'errored':>9}")
    for r in comparison.results:
        print(
            f"  {r.strategy:<16}{r.recall_at_k:>10.4f}{r.chunk_count:>9}{r.sample_size:>8}{r.errored:>9}"
        )
    print(f"  best (self-retrievability): {comparison.best_strategy}")
    print("  NOTE: self-retrievability (confounded per-config question sets), NOT a")
    print("        controlled A/B; rests on synthetic (non-human-ground-truth) recall.")
    print(f"{'=' * 64}\n")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kb-id", required=True, help="KB id (drives per-KB index)")
    parser.add_argument(
        "--strategies",
        nargs="+",
        default=["layout_aware", "heading_aware"],
        help="chunk_strategy values to compare (default: layout_aware heading_aware)",
    )
    parser.add_argument("--sample", type=int, default=30, help="chunks to sample per strategy")
    parser.add_argument("--seed", type=int, default=0, help="sampling seed (default 0)")
    parser.add_argument("--top-k", type=int, default=5, help="retrieval top-K for recall")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("reports"),
        help="dir for per-strategy synthetic eval-set YAMLs",
    )
    args = parser.parse_args()
    # Windows: psycopg (lifespan audit-log prune) needs a SelectorEventLoop, not the
    # default ProactorEventLoop — mirror api/server.py's __main__ guard + the W55
    # run_controlled_ab_comparison fix. W53 shares the identical lifespan/psycopg path;
    # confirmed live in W56 (this CLI was smoke-deferred → never exercised before).
    if sys.platform == "win32":
        return asyncio.run(_amain(args), loop_factory=asyncio.SelectorEventLoop)
    return asyncio.run(_amain(args))


if __name__ == "__main__":
    raise SystemExit(main())
