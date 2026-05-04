"""Reranker unit tests (W3 D1 F1 — Cohere REST client + factory).

Live procurement deferred (Chris W3 D1-D2 Marketplace deploy in progress);
mocked transport here pins the contract per CLAUDE.md §5.6 H6 (retrieval
critical pipeline).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from retrieval.hybrid import HybridSearchHit
from retrieval.reranker.cohere import CohereReranker
from retrieval.reranker.factory import make_reranker
from storage.settings import Settings


def _mock_response(status_code: int, body: dict) -> MagicMock:
    response = MagicMock(spec=httpx.Response)
    response.status_code = status_code
    response.json = MagicMock(return_value=body)
    response.raise_for_status = MagicMock()
    return response


def _hits(*texts: str) -> list[HybridSearchHit]:
    return [
        HybridSearchHit(score=0.5, fields={"chunk_id": f"c{i}", "chunk_text": t})
        for i, t in enumerate(texts)
    ]


@pytest.mark.asyncio
async def test_rerank_empty_candidates_returns_empty_no_call() -> None:
    with patch("retrieval.reranker.cohere.httpx.AsyncClient") as MockClient:
        instance = MockClient.return_value
        instance.post = AsyncMock()
        instance.aclose = AsyncMock()

        async with CohereReranker(endpoint="https://x", api_key="k") as r:
            result = await r.rerank("q", [], top_k=5)

        assert result == []
        instance.post.assert_not_awaited()


@pytest.mark.asyncio
async def test_rerank_orders_by_relevance_score_desc() -> None:
    body = {
        "results": [
            {"index": 2, "relevance_score": 0.95},
            {"index": 0, "relevance_score": 0.71},
            {"index": 1, "relevance_score": 0.30},
        ]
    }

    with patch("retrieval.reranker.cohere.httpx.AsyncClient") as MockClient:
        instance = MockClient.return_value
        instance.post = AsyncMock(return_value=_mock_response(200, body))
        instance.aclose = AsyncMock()

        async with CohereReranker(endpoint="https://x", api_key="k") as r:
            out = await r.rerank("query", _hits("a", "b", "c"), top_k=5)

    scores = [c.rerank_score for c in out]
    assert scores == sorted(scores, reverse=True)
    assert out[0].fields["chunk_id"] == "c2"
    assert out[0].original_index == 2
    assert out[0].hybrid_score == 0.5


@pytest.mark.asyncio
async def test_rerank_payload_shape() -> None:
    body = {"results": [{"index": 0, "relevance_score": 1.0}]}

    captured: dict = {}

    async def _capture(url, content):
        captured["url"] = url
        captured["content"] = content
        return _mock_response(200, body)

    with patch("retrieval.reranker.cohere.httpx.AsyncClient") as MockClient:
        instance = MockClient.return_value
        instance.post = AsyncMock(side_effect=_capture)
        instance.aclose = AsyncMock()

        async with CohereReranker(
            endpoint="https://m.example.com", api_key="key", model="rerank-v3.5"
        ) as r:
            await r.rerank("hello", _hits("doc-a"), top_k=3)

    assert captured["url"] == "https://m.example.com/v2/rerank"
    import json

    payload = json.loads(captured["content"])
    assert payload["model"] == "rerank-v3.5"
    assert payload["query"] == "hello"
    assert payload["documents"] == ["doc-a"]
    assert payload["top_n"] == 1  # min(top_k=3, len=1)


@pytest.mark.asyncio
async def test_rerank_top_n_clamped_to_candidate_count() -> None:
    body = {"results": [{"index": 0, "relevance_score": 0.9}]}
    captured: dict = {}

    async def _capture(url, content):
        captured["content"] = content
        return _mock_response(200, body)

    with patch("retrieval.reranker.cohere.httpx.AsyncClient") as MockClient:
        instance = MockClient.return_value
        instance.post = AsyncMock(side_effect=_capture)
        instance.aclose = AsyncMock()

        async with CohereReranker(endpoint="https://x", api_key="k") as r:
            await r.rerank("q", _hits("only"), top_k=10)

    import json

    assert json.loads(captured["content"])["top_n"] == 1


@pytest.mark.asyncio
async def test_rerank_invalid_index_in_response_skipped() -> None:
    body = {
        "results": [
            {"index": 0, "relevance_score": 0.9},
            {"index": 99, "relevance_score": 0.8},  # out-of-range; should skip
        ]
    }

    with patch("retrieval.reranker.cohere.httpx.AsyncClient") as MockClient:
        instance = MockClient.return_value
        instance.post = AsyncMock(return_value=_mock_response(200, body))
        instance.aclose = AsyncMock()

        async with CohereReranker(endpoint="https://x", api_key="k") as r:
            out = await r.rerank("q", _hits("a", "b"), top_k=5)

    assert len(out) == 1
    assert out[0].original_index == 0


def test_factory_returns_none_when_endpoint_unset() -> None:
    settings = Settings(cohere_endpoint="", cohere_api_key="")
    assert make_reranker(settings) is None


def test_factory_returns_none_when_key_unset() -> None:
    settings = Settings(cohere_endpoint="https://x", cohere_api_key="")
    assert make_reranker(settings) is None


def test_factory_returns_cohere_when_both_set() -> None:
    settings = Settings(
        cohere_endpoint="https://m.example.com",
        cohere_api_key="key",
        cohere_procurement_path="A",
    )
    r = make_reranker(settings)
    assert isinstance(r, CohereReranker)
    assert r.endpoint == "https://m.example.com"
    assert r.path == "A"
