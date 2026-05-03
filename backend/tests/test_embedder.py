"""Azure OpenAI embedder unit tests (per CLAUDE.md §5.6 H6 — embedding pipeline is critical).

Live Azure smoke deferred per R8 active VPN reactivation (W2 D3 carry-over);
mock-based unit tests guarantee request shape + response handling correctness.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from openai import RateLimitError

from ingestion.embedding.azure_openai_embedder import AzureOpenAIEmbedder
from ingestion.embedding.base import EmbeddingResult


def _mock_response(vectors: list[list[float]], total_tokens: int) -> MagicMock:
    response = MagicMock()
    response.data = [MagicMock(embedding=vec) for vec in vectors]
    response.usage = MagicMock(prompt_tokens=total_tokens)
    return response


@pytest.mark.asyncio
async def test_embed_single_returns_1024d_vector() -> None:
    expected_vec = [0.1] * 1024

    with patch("ingestion.embedding.azure_openai_embedder.AsyncAzureOpenAI") as MockClient:
        instance = MockClient.return_value
        instance.embeddings.create = AsyncMock(
            return_value=_mock_response([expected_vec], total_tokens=10),
        )
        instance.close = AsyncMock()

        async with AzureOpenAIEmbedder(
            endpoint="https://x.openai.azure.com",
            api_key="key",
            api_version="2025-04-01-preview",
            deployment="text-embedding-3-large",
            dimensions=1024,
        ) as embedder:
            result = await embedder.embed("hello world")

    assert isinstance(result, EmbeddingResult)
    assert len(result.vector) == 1024
    assert result.input_tokens == 10  # full batch (1 text)


@pytest.mark.asyncio
async def test_embed_batch_calls_azure_with_dimensions_1024() -> None:
    """Verify SDK request includes dimensions=1024 (MRL truncate)."""
    vec = [0.0] * 1024
    with patch("ingestion.embedding.azure_openai_embedder.AsyncAzureOpenAI") as MockClient:
        instance = MockClient.return_value
        instance.embeddings.create = AsyncMock(
            return_value=_mock_response([vec, vec, vec], total_tokens=30),
        )
        instance.close = AsyncMock()

        async with AzureOpenAIEmbedder(
            endpoint="https://x.openai.azure.com",
            api_key="key",
            api_version="2025-04-01-preview",
            deployment="text-embedding-3-large",
            dimensions=1024,
        ) as embedder:
            results = await embedder.embed_batch(["a", "b", "c"])

    assert len(results) == 3
    assert all(len(r.vector) == 1024 for r in results)
    instance.embeddings.create.assert_awaited_once_with(
        input=["a", "b", "c"],
        model="text-embedding-3-large",
        dimensions=1024,
    )


@pytest.mark.asyncio
async def test_embed_batch_empty_returns_empty_no_call() -> None:
    """Empty input must not consume an Azure API call (cost guard)."""
    with patch("ingestion.embedding.azure_openai_embedder.AsyncAzureOpenAI") as MockClient:
        instance = MockClient.return_value
        instance.embeddings.create = AsyncMock()
        instance.close = AsyncMock()

        async with AzureOpenAIEmbedder(
            endpoint="https://x.openai.azure.com",
            api_key="key",
            api_version="v",
            deployment="text-embedding-3-large",
        ) as embedder:
            results = await embedder.embed_batch([])

    assert results == []
    instance.embeddings.create.assert_not_called()


@pytest.mark.asyncio
async def test_embed_batch_pro_rates_tokens_across_inputs() -> None:
    """Per-input token approximation = total // batch_size (Azure batch billing)."""
    vec = [0.0] * 1024
    with patch("ingestion.embedding.azure_openai_embedder.AsyncAzureOpenAI") as MockClient:
        instance = MockClient.return_value
        instance.embeddings.create = AsyncMock(
            return_value=_mock_response([vec, vec, vec, vec], total_tokens=100),
        )
        instance.close = AsyncMock()

        async with AzureOpenAIEmbedder(
            endpoint="https://x.openai.azure.com",
            api_key="k",
            api_version="v",
            deployment="d",
        ) as embedder:
            results = await embedder.embed_batch(["a", "b", "c", "d"])

    assert all(r.input_tokens == 25 for r in results)  # 100 // 4


@pytest.mark.asyncio
async def test_embed_retries_on_rate_limit_then_succeeds() -> None:
    """tenacity retry on RateLimitError; 3rd attempt succeeds."""
    vec = [0.0] * 1024

    rate_limit_error = RateLimitError(
        message="rate limit",
        response=MagicMock(status_code=429),
        body=None,
    )

    with patch("ingestion.embedding.azure_openai_embedder.AsyncAzureOpenAI") as MockClient:
        instance = MockClient.return_value
        instance.embeddings.create = AsyncMock(
            side_effect=[
                rate_limit_error,
                rate_limit_error,
                _mock_response([vec], total_tokens=5),
            ],
        )
        instance.close = AsyncMock()

        async with AzureOpenAIEmbedder(
            endpoint="https://x.openai.azure.com",
            api_key="k",
            api_version="v",
            deployment="d",
        ) as embedder:
            result = await embedder.embed("hello")

    assert len(result.vector) == 1024
    assert instance.embeddings.create.await_count == 3


@pytest.mark.asyncio
async def test_embed_propagates_non_retryable_error() -> None:
    """Errors outside retry list (e.g. ValueError) propagate immediately."""
    with patch("ingestion.embedding.azure_openai_embedder.AsyncAzureOpenAI") as MockClient:
        instance = MockClient.return_value
        instance.embeddings.create = AsyncMock(side_effect=ValueError("bad input"))
        instance.close = AsyncMock()

        async with AzureOpenAIEmbedder(
            endpoint="https://x.openai.azure.com",
            api_key="k",
            api_version="v",
            deployment="d",
        ) as embedder:
            with pytest.raises(ValueError, match="bad input"):
                await embedder.embed("x")


@pytest.mark.asyncio
async def test_embedder_implements_embedder_protocol() -> None:
    """Static-style runtime check: AzureOpenAIEmbedder must satisfy Embedder Protocol."""
    from ingestion.embedding.base import Embedder

    with patch("ingestion.embedding.azure_openai_embedder.AsyncAzureOpenAI") as MockClient:
        MockClient.return_value.close = AsyncMock()
        embedder = AzureOpenAIEmbedder(
            endpoint="https://x.openai.azure.com",
            api_key="k",
            api_version="v",
            deployment="d",
        )
        assert isinstance(embedder, Embedder)
        await embedder.aclose()
