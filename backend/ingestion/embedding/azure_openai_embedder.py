"""Azure OpenAI text-embedding-3-large async embedder (per architecture.md §3.2 + components/C01-ingestion.md §1).

Uses openai SDK AsyncAzureOpenAI (R8 mitigated W2 D0 2026-05-03 — pip install
unblocked via home network). MRL truncate via `dimensions` parameter natively
supported by text-embedding-3-large; 1024d default per Settings.embedding_dimension
matches Azure AI Search index `content_vector` field config (architecture.md §3.6).

Cost log fields (structlog event "embedding_call"):
- input_tokens: Azure-billed token count
- output_dim:   1024 (per Q19 W2 D3 decision)
- batch_size:   number of input strings in this call
- latency_ms:   wall time
- deployment:   AZURE_OPENAI_DEPLOYMENT_EMBEDDING name (per .env)

Retry strategy (tenacity):
- RateLimitError + APITimeoutError → exponential backoff up to 3 attempts.
- Other errors propagate immediately (caller decides FailureRecord vs abort).
"""

from __future__ import annotations

import time

import structlog
from openai import APITimeoutError, AsyncAzureOpenAI, RateLimitError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from ingestion.embedding.base import EmbeddingResult

logger = structlog.get_logger(__name__)


class AzureOpenAIEmbedder:
    """Async embedder using Azure OpenAI text-embedding-3-large + MRL truncate."""

    def __init__(
        self,
        endpoint: str,
        api_key: str,
        api_version: str,
        deployment: str,
        dimensions: int = 1024,
    ) -> None:
        self.deployment = deployment
        self.embedding_dimension = dimensions
        self._client = AsyncAzureOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version=api_version,
        )

    async def aclose(self) -> None:
        await self._client.close()

    async def __aenter__(self) -> AzureOpenAIEmbedder:
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        await self.aclose()

    @retry(
        retry=retry_if_exception_type((RateLimitError, APITimeoutError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def _embed_raw(self, texts: list[str]) -> tuple[list[list[float]], int]:
        """Single Azure call returning (vectors, input_tokens). Retries on rate limit."""
        response = await self._client.embeddings.create(
            input=texts,
            model=self.deployment,
            dimensions=self.embedding_dimension,
        )
        vectors = [item.embedding for item in response.data]
        input_tokens = response.usage.prompt_tokens or 0
        return vectors, input_tokens

    async def embed(self, text: str) -> EmbeddingResult:
        results = await self.embed_batch([text])
        return results[0]

    async def embed_batch(self, texts: list[str]) -> list[EmbeddingResult]:
        if not texts:
            return []
        start = time.perf_counter()
        vectors, total_tokens = await self._embed_raw(texts)
        latency_ms = int((time.perf_counter() - start) * 1000)

        # Azure does not break down per-input tokens; we approximate by
        # pro-rating total over batch. For exact per-chunk billing, callers
        # should embed individually (much slower) or trust the batch-aggregate.
        per_input_tokens = total_tokens // len(texts) if texts else 0

        logger.info(
            "embedding_call",
            batch_size=len(texts),
            input_tokens=total_tokens,
            output_dim=self.embedding_dimension,
            latency_ms=latency_ms,
            deployment=self.deployment,
        )

        return [
            EmbeddingResult(vector=vec, input_tokens=per_input_tokens)
            for vec in vectors
        ]
