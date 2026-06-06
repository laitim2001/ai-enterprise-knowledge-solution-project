"""W54 live driver: controlled shared-question A/B chunk-strategy recall comparison.

Builds ONE frozen, text-anchored, keyword-mode question set from the current reference
index (section-anchored → strategy-invariant), then for each --strategy: set
`kb_config.chunk_strategy` → reindex the KB in place → score the SAME frozen set via
EvalRunner keyword-containment recall. Reports per-strategy recall + chunk count + best.

This is the W53 嚴謹版 (W53 plan §1 deferred「controlled A/B (shared text-anchored QA)」):
the question set is SHARED across strategies → the W53 per-config question-difficulty
confounding is removed. Reuses EvalRunner keyword mode (zero new recall math).

NOTE (methodology honesty): the shared set IS controlled, but it is STILL synthetic
(LLM-written question + LLM-extracted keywords, NOT human ground truth) and scored by
keyword containment — a LEXICAL proxy (a chunk holding a keyword is not proof it is the
answer-bearing chunk; a section-anchored question may be answerable from several chunks
→ recall runs lenient). Read `best` as a relative signal, not an absolute verdict.

SMOKE-DEFERRED: needs Azure judge cred + indexed KB + stored original sources
(W46 `-sources` container) + Free-tier 402 workaround. The core
(`backend/eval/controlled_comparison.py`) is unit-tested with stubs. Sequential in-place
reindex leaves the KB in the LAST strategy's state. The shared set is generated from the
reference index BEFORE the first reindex.

Usage (from project root):
    backend/.venv/Scripts/python.exe -m scripts.run_controlled_ab_comparison \\
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

import yaml  # noqa: E402

_BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from api.routes.documents import run_kb_reindex  # noqa: E402
from api.server import app, lifespan  # noqa: E402
from eval.controlled_comparison import (  # noqa: E402
    build_shared_eval_set,
    make_qa_keyword_generator,
    run_controlled_strategy_comparison,
)
from eval.runner import EvalReport, EvalRunner  # noqa: E402
from kb_management import get_kb_service  # noqa: E402
from storage.settings import get_settings  # noqa: E402


async def _amain(args: argparse.Namespace) -> int:
    settings = get_settings()
    if not (settings.azure_openai_api_key and settings.azure_search_admin_key):
        print(
            "ERROR: AZURE_OPENAI_API_KEY / AZURE_SEARCH_ADMIN_KEY missing",
            file=sys.stderr,
        )
        return 1
    generate_fn = make_qa_keyword_generator(settings)
    if generate_fn is None:
        print(
            "ERROR: no Azure OpenAI judge credential — controlled-QA generator unavailable",
            file=sys.stderr,
        )
        return 1

    args.output_dir.mkdir(parents=True, exist_ok=True)
    shared_path = args.output_dir / f"controlled-ab-shared-seed{args.seed}.yaml"

    # Bootstrap the real app lifespan so app.state (engine + ingestion deps) is wired
    # identically to production; run_kb_reindex only reads request.app.state.
    async with lifespan(app):
        engine = app.state.retrieval_engine
        if engine is None:
            print(
                "ERROR: retrieval_engine not initialized (check Azure .env)",
                file=sys.stderr,
            )
            return 1
        service = get_kb_service()
        request_shim = SimpleNamespace(app=app)

        # Build the ONE frozen shared question set from the reference index (before reindex).
        pair_count = await build_shared_eval_set(
            engine,
            args.kb_id,
            generate_fn=generate_fn,
            output_path=shared_path,
            sample_size=args.sample,
            seed=args.seed,
        )
        version = str(
            yaml.safe_load(shared_path.read_text(encoding="utf-8"))
            .get("metadata", {})
            .get("version", "unknown")
        )
        print(
            f"shared question set: {pair_count} pairs → {shared_path} (version={version})"
        )

        async def reindex_with_strategy(strategy: str) -> int:
            status = await service.get(args.kb_id)
            new_config = status.config.model_copy(update={"chunk_strategy": strategy})
            await service.update_config(args.kb_id, new_config)
            await run_kb_reindex(
                kb_id=args.kb_id,
                request=request_shim,  # type: ignore[arg-type]
                service=service,
            )
            docs = await engine.list_documents(args.kb_id)
            return sum(int(d.get("total_chunks") or 0) for d in docs)

        async def score() -> EvalReport:
            # Same frozen set every strategy → controlled. validated=False entries force
            # EvalRunner's keyword-containment path (chunk_id-agnostic).
            return await EvalRunner(engine, top_k=args.top_k, kb_id=args.kb_id).run(
                shared_path
            )

        comparison = await run_controlled_strategy_comparison(
            args.kb_id,
            args.strategies,
            eval_set_version=version,
            shared_sample_size=pair_count,
            reindex_with_strategy_fn=reindex_with_strategy,
            score_fn=score,
            top_k=args.top_k,
        )

    print(f"\n{'=' * 66}")
    print("W54 controlled shared-question A/B recall comparison")
    print(
        f"  KB: {comparison.kb_id}   shared Qs: {comparison.sample_size}   "
        f"seed: {args.seed}   top-k: {comparison.top_k}"
    )
    print(f"  eval-set: {comparison.eval_set_version}")
    print(f"  {'strategy':<16}{'recall@k':>10}{'chunks':>9}{'scored':>8}{'errored':>9}")
    for r in comparison.results:
        print(
            f"  {r.strategy:<16}{r.recall_at_k:>10.4f}{r.chunk_count:>9}{r.sample_size:>8}{r.errored:>9}"
        )
    print(f"  best (keyword-recall): {comparison.best_strategy}")
    print("  NOTE: controlled (shared frozen question set) — removes W53 per-config")
    print("        confounding; STILL synthetic (LLM Q+keywords) + keyword-containment")
    print("        LEXICAL proxy, NOT human-ground-truth recall. Relative signal only.")
    print(f"{'=' * 66}\n")
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
    parser.add_argument(
        "--sample",
        type=int,
        default=30,
        help="section passages to sample for the shared set",
    )
    parser.add_argument("--seed", type=int, default=0, help="sampling seed (default 0)")
    parser.add_argument(
        "--top-k", type=int, default=5, help="retrieval top-K for recall"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("reports"),
        help="dir for the frozen shared eval-set YAML",
    )
    return asyncio.run(_amain(parser.parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
