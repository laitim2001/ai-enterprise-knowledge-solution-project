"""W2 D3 F4 Azure OpenAI embedder smoke + parallel batch benchmark.

(1) Single embed: 1 short text → assert vector dimension == 1024 (MRL truncate)
(2) Parallel batch: 100 chunk texts from W2 D2 chunker output → assert wall <5s
    (per components/C01-ingestion.md §5 design target)
(3) Cost projection: total tokens × $0.13/M baseline

Usage (from project root):
    backend/.venv/Scripts/python.exe -m scripts.run_embedder_smoke

Exit codes:
    0  — smoke + benchmark pass
    1  — single embed dimension mismatch OR wall time > 5s OR API error
"""

from __future__ import annotations

import asyncio
import sys
import time
from pathlib import Path

# sys.path bootstrap (per W2 D2 convention)
_BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from ingestion.chunker.layout_aware import LayoutAwareChunker  # noqa: E402
from ingestion.embedding.azure_openai_embedder import AzureOpenAIEmbedder  # noqa: E402
from ingestion.parsers.docx_parser import DoclingDocxParser  # noqa: E402
from storage.settings import get_settings  # noqa: E402


async def _single_smoke(embedder: AzureOpenAIEmbedder) -> bool:
    text = "Press the lever on the right side to release the paper jam."
    result = await embedder.embed(text)
    ok = len(result.vector) == embedder.embedding_dimension and result.input_tokens > 0
    print(
        f"  single_embed: dim={len(result.vector)} (expected {embedder.embedding_dimension}) "
        f"tokens={result.input_tokens} OK={ok}",
    )
    return ok


def _gather_chunk_texts(target_count: int = 100) -> list[str]:
    """Parse + chunk samples until reach target chunk count for benchmark."""
    sample_dir = Path("docs/06-reference/01-sample-doc")
    parser = DoclingDocxParser()
    chunker = LayoutAwareChunker()
    texts: list[str] = []
    for sample in sorted(sample_dir.glob("*.docx")):
        result = parser.parse(sample)
        for spec in chunker.chunk(result):
            if not spec.low_value_flag and spec.chunk_text:
                texts.append(spec.chunk_text)
            if len(texts) >= target_count:
                return texts
    return texts


async def _batch_benchmark(embedder: AzureOpenAIEmbedder, texts: list[str]) -> bool:
    if len(texts) < 5:
        print(f"  batch: only {len(texts)} chunks gathered (skipping benchmark)")
        return True
    start = time.perf_counter()
    results = await embedder.embed_batch(texts)
    wall = time.perf_counter() - start
    dims = {len(r.vector) for r in results}
    total_tokens = sum(r.input_tokens for r in results) * len(texts)  # pro-rated
    cost_usd = total_tokens / 1_000_000 * 0.13  # text-embedding-3-large pricing baseline
    print(
        f"  batch_embed: count={len(texts)} dims={dims} wall={wall:.2f}s "
        f"throughput={len(texts) / wall:.1f}/s",
    )
    print(f"  cost_estimate: total_tokens={total_tokens} cost_usd~={cost_usd:.4f}")
    benchmark_target_seconds = 5.0
    return wall < benchmark_target_seconds * (len(texts) / 100)


async def _amain() -> int:
    settings = get_settings()
    print(
        f"endpoint={settings.azure_openai_endpoint} "
        f"deployment={settings.azure_openai_deployment_embedding} "
        f"dim={settings.embedding_dimension}",
    )
    if not settings.azure_openai_api_key:
        print("AZURE_OPENAI_API_KEY missing in .env — cannot run smoke", file=sys.stderr)
        return 1

    async with AzureOpenAIEmbedder(
        endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key,
        api_version=settings.azure_openai_api_version,
        deployment=settings.azure_openai_deployment_embedding,
        dimensions=settings.embedding_dimension,
    ) as embedder:
        single_ok = await _single_smoke(embedder)
        if not single_ok:
            return 1

        texts = _gather_chunk_texts(target_count=100)
        print(f"  gathered {len(texts)} non-low-value chunks for batch benchmark")
        batch_ok = await _batch_benchmark(embedder, texts)
        if not batch_ok:
            print("  batch benchmark exceeded target; investigate", file=sys.stderr)
            return 1

    return 0


def main() -> int:
    return asyncio.run(_amain())


if __name__ == "__main__":
    raise SystemExit(main())
