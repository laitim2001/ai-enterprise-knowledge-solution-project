"""W2 Gate 1 live eval driver: eval-set-v0.yaml → RetrievalEngine → R@5 verdict.

Usage (from project root, post populate sanity success):
    backend/.venv/Scripts/python.exe -m scripts.run_gate1_eval

Exit codes:
    0 — eval ran end-to-end, report written; verdict (pass/fail) printed
    1 — env missing OR retrieval engine init failed OR runtime exception
"""

from __future__ import annotations

# Use OS trust store (Windows Cert Store) for TLS verification so Ricoh corp
# proxy SSL inspection is honoured. Must run before any ssl/urllib3/httpx import.
import truststore

truststore.inject_into_ssl()

import asyncio
import sys
from pathlib import Path

_BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from eval.runner import EvalRunner, report_to_yaml  # noqa: E402
from ingestion.embedding.azure_openai_embedder import AzureOpenAIEmbedder  # noqa: E402
from retrieval.hybrid import HybridSearcher  # noqa: E402
from retrieval.retrieval_engine import RetrievalEngine  # noqa: E402
from storage.settings import get_settings  # noqa: E402

EVAL_SET = Path("docs/eval-set-v0.yaml")
INDEX_NAME = "ekp-kb-drive-v1"
GATE1_THRESHOLD = 0.80
REPORT_PATH = Path("reports/gate1_w2.yaml")


async def _amain() -> int:
    settings = get_settings()
    if not (settings.azure_openai_api_key and settings.azure_search_admin_key):
        print("ERROR: AZURE_OPENAI_API_KEY / AZURE_SEARCH_ADMIN_KEY missing", file=sys.stderr)
        return 1

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
        index_name=INDEX_NAME,
    )

    async with embedder, searcher:
        engine = RetrievalEngine(embedder=embedder, searcher=searcher)
        runner = EvalRunner(engine=engine, top_k=5)
        report = await runner.run(EVAL_SET)

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report_to_yaml(report), encoding="utf-8")

    verdict = "PASS" if report.aggregate_recall_at_5 >= GATE1_THRESHOLD else "FAIL"
    print(f"\n{'=' * 60}")
    print(f"W2 Gate 1 verdict: {verdict}")
    print(f"  R@5 (aggregate, main queries):  {report.aggregate_recall_at_5:.4f}")
    print(f"  Threshold:                       {GATE1_THRESHOLD:.2f}")
    print(f"  Total queries:                   {report.total_queries}")
    print(f"  Main (non-OOS) queries:          {report.main_queries}")
    print(f"  OOS queries:                     {report.oos_queries}")
    print(f"  Evaluated (no error):            {report.queries_evaluated}")
    print(f"  Errored:                         {report.queries_errored}")
    print(f"  Mode breakdown:                  {report.mode_breakdown}")
    print(f"  Avg embed latency (ms):          {report.avg_embed_latency_ms}")
    print(f"  Avg search latency (ms):         {report.avg_search_latency_ms}")
    print(f"  Report path:                     {REPORT_PATH}")
    print(f"{'=' * 60}\n")
    return 0


def main() -> int:
    return asyncio.run(_amain())


if __name__ == "__main__":
    raise SystemExit(main())
