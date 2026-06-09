"""W4 D2 F2 — RAGAs 4-metric eval automation driver.

Usage (from project root, post Azure OpenAI / AI Search live):
    backend/.venv/Scripts/python.exe -m scripts.run_ragas_eval
    backend/.venv/Scripts/python.exe -m scripts.run_ragas_eval \
        --eval-set docs/eval-set-v1-draft.yaml \
        --output reports/ragas-results.json \
        --subset 20

The driver:
1. Loads eval-set YAML (skips OOS queries — refusal accuracy evaluated separately).
2. Optionally subsets to N queries (cost containment per W4 plan §4 R4).
3. Runs the EKP RAG pipeline per query (retrieve via RetrievalEngine →
   synthesize via Synthesizer) and assembles RagasQuerySample list.
4. Hands samples to RagasRunner with the real ragas.metrics.collections judge
   (Azure OpenAI GPT-5.4-mini wrapped via Settings.azure_openai_deployment_llm_judge).
5. Writes RagasReport JSON to --output.

Exit codes:
    0 — eval ran end-to-end, JSON written
    1 — env missing OR pipeline init failed OR runtime exception
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
from pathlib import Path

_BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from eval.ragas_evaluator import make_ragas_evaluator, patch_for_gpt5  # noqa: E402
from eval.ragas_runner import (  # noqa: E402
    RagasQuerySample,
    RagasRunner,
    load_samples_from_eval_set,
    report_to_json,
)
from generation.synthesizer import Synthesizer  # noqa: E402

# Back-compat alias — `tests/test_run_ragas_eval_patch.py` imports this name.
# The implementation now lives in `backend/eval/ragas_evaluator.py` (W17 F3)
# so `/eval/run` + `/eval/shootout` can reuse it.
_patch_for_gpt5 = patch_for_gpt5
from ingestion.embedding.azure_openai_embedder import AzureOpenAIEmbedder  # noqa: E402
from retrieval.hybrid import HybridSearcher  # noqa: E402
from retrieval.reranker.factory import make_reranker  # noqa: E402
from retrieval.retrieval_engine import RetrievalEngine  # noqa: E402
from storage.settings import get_settings  # noqa: E402

DEFAULT_EVAL_SET = Path("docs/eval-set-v1-draft.yaml")
DEFAULT_OUTPUT = Path("reports/ragas-results.json")
DEFAULT_KB_ID = "drive_user_manuals"  # BUG-037 — Tier 1 single-KB baseline (Q7 Resolved)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="W4 D2 F2 RAGAs 4-metric eval driver")
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
        help="Subset to first N queries (0 = all main queries; cost containment per W4 plan §4 R4)",
    )
    parser.add_argument(
        "--kb-id", type=str, default=DEFAULT_KB_ID,
        help=f"Target KB id for retrieval (default: {DEFAULT_KB_ID}). BUG-037 — required by "
             "RetrievalEngine.retrieve per ADR-0018; per-query kb_id in the eval-set still "
             "overrides at the runner layer.",
    )
    parser.add_argument(
        "--pipeline-cache", type=Path, default=None,
        help="Reuse cached pipeline outputs JSON instead of re-running retrieve+synthesize",
    )
    parser.add_argument(
        "--skip-pipeline", action="store_true",
        help="Skip retrieve+synthesize (requires --pipeline-cache);"
             " useful for re-running ragas judge against same RAG outputs",
    )
    return parser.parse_args()


async def _build_samples_via_pipeline(
    eval_set_path: Path,
    subset: int,
    kb_id: str,
) -> list[RagasQuerySample]:
    """Run EKP RAG pipeline per query → assemble RagasQuerySample list.

    `kb_id` (BUG-037) is the target KB for retrieval — required by
    `RetrievalEngine.retrieve` since ADR-0018 (multi-KB invariant). HybridSearcher
    resolves the per-KB index dynamically (`kb_id_to_index_name`), so the searcher
    constructor's `index_name` is only the legacy default fallback.
    """
    settings = get_settings()
    if not (settings.azure_openai_api_key and settings.azure_search_admin_key):
        raise SystemExit(
            "missing AZURE_OPENAI_API_KEY or AZURE_SEARCH_ADMIN_KEY — "
            "populate .env per Q3 + Q4 dependencies",
        )

    samples = load_samples_from_eval_set(eval_set_path, pipeline_outputs_path=None)
    if subset > 0:
        samples = samples[:subset]

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
    synthesizer = Synthesizer(
        endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key,
        api_version=settings.azure_openai_api_version,
        deployment=settings.azure_openai_deployment_llm_primary,
    )

    async with embedder, searcher, synthesizer:
        if reranker is not None:
            await reranker.__aenter__()  # type: ignore[attr-defined]
        try:
            engine = RetrievalEngine(
                embedder=embedder, searcher=searcher, reranker=reranker,
                hybrid_overfetch_for_rerank=settings.hybrid_top_k_retrieval,
            )
            for sample in samples:
                retrieval = await engine.retrieve(query=sample.question, kb_id=kb_id, top_k=5)
                sample.contexts = [
                    str(c.fields.get("chunk_text", "")) for c in retrieval.chunks
                ]
                synth = await synthesizer.synthesize(sample.question, retrieval.chunks)
                sample.answer = synth.answer
        finally:
            if reranker is not None:
                await reranker.__aexit__(None, None, None)  # type: ignore[attr-defined]

    return samples


def _build_samples_via_cache(
    eval_set_path: Path,
    cache_path: Path,
    subset: int,
) -> list[RagasQuerySample]:
    samples = load_samples_from_eval_set(eval_set_path, pipeline_outputs_path=cache_path)
    if subset > 0:
        samples = samples[:subset]
    return samples


def _make_real_evaluator(judge_deployment: str):  # noqa: ARG001 — reads judge from settings
    """Build the Azure-judge-bound RAGAs evaluator (now lives in
    `backend/eval/ragas_evaluator.make_ragas_evaluator` so `/eval/*` shares it).
    Raises `SystemExit` if no Azure judge credential is configured."""
    evaluator = make_ragas_evaluator(get_settings())
    if evaluator is None:
        raise SystemExit(
            "missing AZURE_OPENAI_API_KEY — populate .env to run the RAGAs judge",
        )
    return evaluator


async def _amain() -> int:
    args = _parse_args()
    eval_set_path: Path = args.eval_set
    output_path: Path = args.output
    subset: int = args.subset
    kb_id: str = args.kb_id

    if args.skip_pipeline and args.pipeline_cache is None:
        print("--skip-pipeline requires --pipeline-cache PATH", file=sys.stderr)
        return 1

    if args.pipeline_cache is not None:
        samples = _build_samples_via_cache(eval_set_path, args.pipeline_cache, subset)
    elif args.skip_pipeline:
        samples = _build_samples_via_cache(eval_set_path, args.pipeline_cache, subset)  # type: ignore[arg-type]
    else:
        samples = await _build_samples_via_pipeline(eval_set_path, subset, kb_id)

    if not samples:
        print("no samples to evaluate (empty eval-set after subset/OOS filter)", file=sys.stderr)
        return 1

    settings = get_settings()
    runner = RagasRunner(
        judge_deployment=settings.azure_openai_deployment_llm_judge,
        evaluator=_make_real_evaluator(settings.azure_openai_deployment_llm_judge),
    )
    report = runner.evaluate(
        samples,
        eval_set_name=eval_set_path.name,
        eval_set_version=str(yaml_version(eval_set_path)),
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report_to_json(report), encoding="utf-8")
    print(f"\n[output] RAGAs report -> {output_path}")
    for metric in ("faithfulness", "answer_relevancy", "context_precision", "context_recall"):
        agg = report.aggregates[metric]
        print(f"  {metric}: mean={agg.mean:.3f}  p95={agg.p95:.3f}  n={agg.n}")
    print(
        f"\nJudge cost: input_tokens={report.total_input_tokens}  "
        f"output_tokens={report.total_output_tokens}  "
        f"latency_ms={report.total_latency_ms}",
    )
    return 0


def yaml_version(path: Path) -> str:
    """Read eval-set-version from YAML frontmatter without materialising full doc."""
    import yaml  # noqa: PLC0415

    eval_set = yaml.safe_load(path.read_text(encoding="utf-8"))
    return str(eval_set.get("metadata", {}).get("version", "unknown"))


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
