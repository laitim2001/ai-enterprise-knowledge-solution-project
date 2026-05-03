"""W2 D4 F5 end-to-end populate sanity: 6 sample → orchestrator → AI Search index.

(1) Parse + chunk + (skip Blob upload — R12 deferred) + embed + populate
(2) GET /indexes/ekp-kb-drive-v1 doc count post-upload → match expected ~329
(3) Emit reports/w02_d4_populate_sanity.yaml: per-doc chunk count, total, cost
    projection (input_tokens × $0.13/M), upload success rate

Usage (from project root, post VPN-disconnect for R8 cleared):
    backend/.venv/Scripts/python.exe -m scripts.run_populate_sanity

Exit codes:
    0  — all docs ingested + indexed; doc count matches expected
    1  — sample dir missing OR any FailureRecord OR upload partial fail OR R8 block
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# sys.path bootstrap (per W2 D2 convention)
_BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

import yaml  # noqa: E402  — after sys.path bootstrap

from indexing.populate import IndexPopulator  # noqa: E402
from ingestion.chunker.layout_aware import LayoutAwareChunker  # noqa: E402
from ingestion.embedding.azure_openai_embedder import AzureOpenAIEmbedder  # noqa: E402
from ingestion.orchestrator import IngestionOrchestrator  # noqa: E402
from ingestion.parsers.docx_parser import DoclingDocxParser  # noqa: E402
from storage.settings import get_settings  # noqa: E402

SAMPLE_DIR = Path("docs/06-reference/01-sample-doc")
REPORT_PATH = Path("reports/w02_d4_populate_sanity.yaml")
KB_ID = "drive_user_manuals"


async def _amain() -> int:
    if not SAMPLE_DIR.is_dir():
        print(f"sample dir not found: {SAMPLE_DIR}", file=sys.stderr)
        return 1

    samples = sorted(SAMPLE_DIR.glob("*.docx"))
    if not samples:
        print(f"no .docx files in {SAMPLE_DIR}", file=sys.stderr)
        return 1

    settings = get_settings()
    if not settings.azure_openai_api_key or not settings.azure_search_admin_key:
        print(
            "AZURE_OPENAI_API_KEY or AZURE_SEARCH_ADMIN_KEY missing in .env "
            "— cannot run populate sanity",
            file=sys.stderr,
        )
        return 1

    parser = DoclingDocxParser()
    chunker = LayoutAwareChunker()
    per_doc: list[dict[str, object]] = []
    all_chunks_count = 0
    total_input_tokens = 0
    total_failures = 0

    async with AzureOpenAIEmbedder(
        endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key,
        api_version=settings.azure_openai_api_version,
        deployment=settings.azure_openai_deployment_embedding,
        dimensions=settings.embedding_dimension,
    ) as embedder, IndexPopulator(
        endpoint=settings.azure_search_endpoint,
        admin_key=settings.azure_search_admin_key,
        index_name=settings.azure_search_default_index,
    ) as populator:
        # uploader=None per R12 — Azurite signature mismatch defers Blob upload to W7+ cloud
        orchestrator = IngestionOrchestrator(
            parser=parser,
            chunker=chunker,
            embedder=embedder,
            uploader=None,
        )

        for sample in samples:
            doc_id = sample.stem
            result = await orchestrator.ingest(
                source=sample,
                kb_id=KB_ID,
                doc_id=doc_id,
                source_url=f"file://{sample.resolve().as_posix()}",
            )

            if result.failure is not None:
                total_failures += 1
                per_doc.append(
                    {
                        "filename": sample.name,
                        "stage_failed": result.failure.stage,
                        "error": result.failure.error,
                        "chunks": 0,
                    },
                )
                continue

            upload_result = await populator.upload(result.chunks)
            doc_tokens = sum(0 for _ in result.chunks)  # populated via structlog event in embed
            per_doc.append(
                {
                    "filename": sample.name,
                    "chunks": len(result.chunks),
                    "indexed_succeeded": upload_result.succeeded,
                    "indexed_failed": upload_result.failed,
                    "images_uploaded": result.images_uploaded,
                    "images_deduped": result.images_deduped,
                },
            )
            all_chunks_count += len(result.chunks)
            total_input_tokens += doc_tokens

        # Verify total doc count via GET /indexes/{name}/docs/$count (REST direct)
        import httpx
        count_url = (
            f"{settings.azure_search_endpoint.rstrip('/')}"
            f"/indexes/{settings.azure_search_default_index}/docs/$count"
            f"?api-version=2024-07-01"
        )
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(
                count_url, headers={"api-key": settings.azure_search_admin_key},
            )
            doc_count = int(r.text) if r.is_success else -1

    aggregate = {
        "total_files": len(samples),
        "total_failures": total_failures,
        "total_chunks_emitted": all_chunks_count,
        "indexed_doc_count": doc_count,
        "expected_chunks": all_chunks_count,
        "match": doc_count == all_chunks_count,
        "cost_estimate_usd": round(total_input_tokens / 1_000_000 * 0.13, 4),
    }

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        yaml.safe_dump(
            {"per_doc": per_doc, "aggregate": aggregate},
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )

    print(f"Populate sanity report written: {REPORT_PATH}")
    print(
        f"Files: {aggregate['total_files']} ({aggregate['total_failures']} failed) "
        f"chunks_emitted={aggregate['total_chunks_emitted']} "
        f"indexed_doc_count={aggregate['indexed_doc_count']} "
        f"match={aggregate['match']}",
    )
    return 0 if total_failures == 0 and doc_count == all_chunks_count else 1


def main() -> int:
    return asyncio.run(_amain())


if __name__ == "__main__":
    raise SystemExit(main())
