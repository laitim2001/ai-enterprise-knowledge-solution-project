"""W2 D5 F8 helper — discover real chunk_ids for eval-set placeholder queries.

Iterates eval-set-v0.yaml queries, runs retrieval against the populated index, and
emits a candidate chunk_id list per query for SME review (Chris). Output goes to
reports/w02_d5_chunk_id_candidates.yaml — Chris reviews, picks confirmed
acceptable_chunk_ids per query, then bumps eval-set-v0.yaml → eval-set-v1.yaml
with `annotation.validated: true`.

Live run prerequisites:
- R8 cleared (VPN disconnected) so query embedding + AI Search query work
- Index ekp-kb-drive-v1 populated via scripts.run_populate_sanity (W2 D5 prereq)

Usage (from project root, post VPN-disconnect + populate):
    backend/.venv/Scripts/python.exe -m scripts.discover_chunk_ids
"""

from __future__ import annotations

# Use OS trust store (Windows Cert Store) for TLS verification so Ricoh corp
# proxy SSL inspection is honoured. Must run before any ssl/urllib3/httpx import.
import truststore

truststore.inject_into_ssl()

import asyncio
import sys
from pathlib import Path

# sys.path bootstrap (per W2 D2 convention)
_BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

import yaml  # noqa: E402  — after sys.path bootstrap

from ingestion.embedding.azure_openai_embedder import AzureOpenAIEmbedder  # noqa: E402
from retrieval.hybrid import HybridSearcher  # noqa: E402
from retrieval.retrieval_engine import RetrievalEngine  # noqa: E402
from storage.settings import get_settings  # noqa: E402

EVAL_SET_PATH = Path("docs/eval-set-v0.yaml")
REPORT_PATH = Path("reports/w02_d5_chunk_id_candidates.yaml")
TOP_K = 8  # surface a few extras for SME selection


async def _amain() -> int:
    if not EVAL_SET_PATH.is_file():
        print(f"eval set not found: {EVAL_SET_PATH}", file=sys.stderr)
        return 1

    settings = get_settings()
    if not settings.azure_openai_api_key or not settings.azure_search_admin_key:
        print(
            "AZURE_OPENAI_API_KEY or AZURE_SEARCH_ADMIN_KEY missing in .env — "
            "cannot run chunk_id discovery",
            file=sys.stderr,
        )
        return 1

    eval_set = yaml.safe_load(EVAL_SET_PATH.read_text(encoding="utf-8"))
    queries = eval_set.get("queries", [])
    candidates: list[dict] = []

    async with AzureOpenAIEmbedder(
        endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key,
        api_version=settings.azure_openai_api_version,
        deployment=settings.azure_openai_deployment_embedding,
        dimensions=settings.embedding_dimension,
    ) as embedder, HybridSearcher(
        endpoint=settings.azure_search_endpoint,
        admin_key=settings.azure_search_admin_key,
        index_name=settings.azure_search_default_index,
    ) as searcher:
        engine = RetrievalEngine(embedder=embedder, searcher=searcher)
        for q in queries:
            query_id = q.get("query_id", "")
            query_text = q.get("query_text", "")
            is_oos = bool(q.get("ground_truth", {}).get("expected_refusal", False))
            if is_oos:
                continue  # OOS queries don't need chunk_id assignment
            try:
                result = await engine.retrieve(query=query_text, top_k=TOP_K)
                candidates.append(
                    {
                        "query_id": query_id,
                        "query_text": query_text,
                        "current_acceptable_placeholders": q.get("ground_truth", {})
                        .get("acceptable_chunk_ids", []),
                        "discovered_top_k": [
                            {
                                "chunk_id": c.fields.get("chunk_id"),
                                "doc_id": c.fields.get("doc_id"),
                                "section_path": c.fields.get("section_path"),
                                "chunk_title": c.fields.get("chunk_title"),
                                "score": round(c.score, 3),
                                "chunk_text_preview": str(
                                    c.fields.get("chunk_text", ""),
                                )[:200],
                            }
                            for c in result.chunks
                        ],
                    },
                )
            except Exception as exc:  # noqa: BLE001
                candidates.append({
                    "query_id": query_id,
                    "query_text": query_text,
                    "error": f"{type(exc).__name__}: {exc}",
                })

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        yaml.safe_dump(
            {
                "metadata": {
                    "source_eval_set": str(EVAL_SET_PATH),
                    "top_k_per_query": TOP_K,
                    "purpose": (
                        "SME review: pick acceptable_chunk_ids per query from "
                        "discovered_top_k, then update eval-set-v0.yaml → -v1.yaml "
                        "with annotation.validated: true"
                    ),
                },
                "candidates": candidates,
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )

    print(f"Chunk_id candidate report written: {REPORT_PATH}")
    print(f"Reviewed {len(candidates)} non-OOS queries, top-{TOP_K} per query.")
    print(
        "Next step: Chris reviews report, picks acceptable_chunk_ids, bumps "
        "eval-set-v0.yaml → eval-set-v1.yaml with annotation.validated: true",
    )
    return 0


def main() -> int:
    return asyncio.run(_amain())


if __name__ == "__main__":
    raise SystemExit(main())
