"""Hybrid retrieval unit tests (per CLAUDE.md §5.6 H6 — retrieval is critical pipeline)."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from ingestion.embedding.base import EmbeddingResult
from retrieval.hybrid import HybridSearcher, HybridSearchHit
from retrieval.retrieval_engine import RetrievalEngine, RetrievalResult


def _mock_response(status_code: int, body: dict | None = None) -> MagicMock:
    response = MagicMock(spec=httpx.Response)
    response.status_code = status_code
    response.is_success = 200 <= status_code < 300
    response.json = MagicMock(return_value=body or {"value": []})
    response.raise_for_status = MagicMock()
    return response


@pytest.mark.asyncio
async def test_hybrid_search_payload_shape_matches_spec() -> None:
    """Per architecture.md §3.1: search + vectorQueries + queryType=semantic + filter."""
    with patch("retrieval.hybrid.httpx.AsyncClient") as MockClient:
        instance = MockClient.return_value
        instance.post = AsyncMock(return_value=_mock_response(200, {"value": []}))
        instance.aclose = AsyncMock()

        async with HybridSearcher("https://x", "k", "ekp-kb-drive-v1") as s:
            await s.search("paper jam", [0.1] * 1024, top_k=50)

    payload = json.loads(instance.post.await_args.kwargs["content"])
    assert payload["search"] == "paper jam"
    assert payload["top"] == 50
    assert payload["queryType"] == "semantic"
    assert payload["semanticConfiguration"] == "ekp-semantic-config"
    assert payload["filter"] == "enabled eq true and low_value_flag eq false"
    assert payload["vectorQueries"][0]["fields"] == "content_vector"
    assert payload["vectorQueries"][0]["k"] == 50
    assert len(payload["vectorQueries"][0]["vector"]) == 1024


@pytest.mark.asyncio
async def test_hybrid_search_maps_response_to_hits_with_score() -> None:
    body = {
        "value": [
            {
                "@search.score": 0.91,
                "chunk_id": "kb-drive_doc-A_chunk-0007",
                "chunk_title": "Open the rear cover",
                "chunk_text": "Press the lever...",
            },
            {
                "@search.score": 0.45,
                "chunk_id": "kb-drive_doc-B_chunk-0001",
                "chunk_title": "Intro",
                "chunk_text": "...",
            },
        ],
    }

    with patch("retrieval.hybrid.httpx.AsyncClient") as MockClient:
        instance = MockClient.return_value
        instance.post = AsyncMock(return_value=_mock_response(200, body))
        instance.aclose = AsyncMock()

        async with HybridSearcher("https://x", "k", "idx") as s:
            hits = await s.search("query", [0.0] * 1024, top_k=2)

    assert len(hits) == 2
    assert hits[0].score == 0.91
    assert hits[0].fields["chunk_id"] == "kb-drive_doc-A_chunk-0007"
    assert "@search.score" not in hits[0].fields  # stripped


@pytest.mark.asyncio
async def test_hybrid_search_custom_filter_clause_honored() -> None:
    with patch("retrieval.hybrid.httpx.AsyncClient") as MockClient:
        instance = MockClient.return_value
        instance.post = AsyncMock(return_value=_mock_response(200, {"value": []}))
        instance.aclose = AsyncMock()

        async with HybridSearcher("https://x", "k", "idx") as s:
            await s.search(
                "q", [0.0] * 1024, filter_clause="kb_id eq 'drive_user_manuals'",
            )

    payload = json.loads(instance.post.await_args.kwargs["content"])
    assert payload["filter"] == "kb_id eq 'drive_user_manuals'"


@pytest.mark.asyncio
async def test_hybrid_search_no_filter_when_none_passed() -> None:
    with patch("retrieval.hybrid.httpx.AsyncClient") as MockClient:
        instance = MockClient.return_value
        instance.post = AsyncMock(return_value=_mock_response(200, {"value": []}))
        instance.aclose = AsyncMock()

        async with HybridSearcher("https://x", "k", "idx") as s:
            await s.search("q", [0.0] * 1024, filter_clause=None)

    payload = json.loads(instance.post.await_args.kwargs["content"])
    assert "filter" not in payload


@pytest.mark.asyncio
async def test_hybrid_search_retries_on_5xx() -> None:
    error_response = MagicMock(spec=httpx.Response)
    error_response.status_code = 503
    error_response.raise_for_status = MagicMock(
        side_effect=httpx.HTTPStatusError(
            "503", request=MagicMock(), response=error_response,
        ),
    )
    success_response = _mock_response(200, {"value": []})

    with patch("retrieval.hybrid.httpx.AsyncClient") as MockClient:
        instance = MockClient.return_value
        instance.post = AsyncMock(side_effect=[error_response, success_response])
        instance.aclose = AsyncMock()

        async with HybridSearcher("https://x", "k", "idx") as s:
            hits = await s.search("q", [0.0] * 1024)

    assert hits == []
    assert instance.post.await_count == 2


# RetrievalEngine integration tests


class _FakeEmbedder:
    embedding_dimension = 1024

    async def embed(self, text: str) -> EmbeddingResult:  # noqa: ARG002
        return EmbeddingResult(vector=[0.5] * 1024, input_tokens=3)

    async def embed_batch(self, texts: list[str]) -> list[EmbeddingResult]:
        return [EmbeddingResult(vector=[0.5] * 1024, input_tokens=1) for _ in texts]


@pytest.mark.asyncio
async def test_retrieval_engine_empty_query_returns_empty_no_calls() -> None:
    """Empty query bypasses both embed + search (cost guard)."""
    embedder = _FakeEmbedder()
    searcher = MagicMock()
    searcher.search = AsyncMock()

    engine = RetrievalEngine(embedder=embedder, searcher=searcher)
    result = await engine.retrieve(query="   ", top_k=10)

    assert isinstance(result, RetrievalResult)
    assert result.chunks == []
    searcher.search.assert_not_called()


@pytest.mark.asyncio
async def test_retrieval_engine_calls_embedder_then_searcher() -> None:
    embedder = _FakeEmbedder()
    searcher = MagicMock()
    searcher.search = AsyncMock(
        return_value=[
            HybridSearchHit(score=0.9, fields={"chunk_id": "c1", "chunk_text": "t1"}),
            HybridSearchHit(score=0.5, fields={"chunk_id": "c2", "chunk_text": "t2"}),
        ],
    )

    engine = RetrievalEngine(embedder=embedder, searcher=searcher)
    result = await engine.retrieve(query="how to recover", top_k=5)

    assert len(result.chunks) == 2
    assert result.chunks[0].score == 0.9
    assert result.chunks[0].fields["chunk_id"] == "c1"
    searcher.search.assert_awaited_once()
    call_kwargs = searcher.search.await_args.kwargs
    assert call_kwargs["query_text"] == "how to recover"
    assert len(call_kwargs["query_vector"]) == 1024
    assert call_kwargs["top_k"] == 5


@pytest.mark.asyncio
async def test_retrieval_engine_default_filter_clause_applied() -> None:
    embedder = _FakeEmbedder()
    searcher = MagicMock()
    searcher.search = AsyncMock(return_value=[])

    engine = RetrievalEngine(embedder=embedder, searcher=searcher)
    await engine.retrieve(query="q")

    call_kwargs = searcher.search.await_args.kwargs
    assert call_kwargs["filter_clause"] == "enabled eq true and low_value_flag eq false"


@pytest.mark.asyncio
async def test_retrieval_engine_custom_filter_clause_passes_through() -> None:
    embedder = _FakeEmbedder()
    searcher = MagicMock()
    searcher.search = AsyncMock(return_value=[])

    engine = RetrievalEngine(embedder=embedder, searcher=searcher)
    await engine.retrieve(query="q", filter_clause="kb_id eq 'foo'")

    call_kwargs = searcher.search.await_args.kwargs
    assert call_kwargs["filter_clause"] == "kb_id eq 'foo'"


@pytest.mark.asyncio
async def test_retrieval_engine_records_latencies() -> None:
    embedder = _FakeEmbedder()
    searcher = MagicMock()
    searcher.search = AsyncMock(return_value=[])

    engine = RetrievalEngine(embedder=embedder, searcher=searcher)
    result = await engine.retrieve(query="q", top_k=10)

    assert result.embed_latency_ms >= 0
    assert result.search_latency_ms >= 0
    assert result.total_latency_ms >= max(result.embed_latency_ms, result.search_latency_ms)
