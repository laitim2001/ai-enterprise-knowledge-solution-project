"""F3 4-way reranker shootout unit tests (W4 D3; per CLAUDE.md §5.6 H6).

Live procurement deferred — Voyage + ZeroEntropy keys Chris async per W4
plan §F3 owner row. Mocked transport pins each reranker's REST contract
(URL / payload / response parse / error skip / score normalisation).

Coverage per reranker:
- empty candidates → empty result + no API call (parity with Cohere)
- desc by relevance_score / preserves original_index + hybrid_score
- payload shape (URL / model / query / documents / top-N field name)
- top-N clamped to candidate count
- invalid index in response skipped

Coverage for factory (`make_reranker`):
- reranker_kind="off" returns None regardless of populated keys
- reranker_kind="voyage" returns None when voyage_api_key unset, else VoyageReranker
- reranker_kind="zeroentropy" returns None when zeroentropy_api_key unset, else ZeroEntropyReranker
- reranker_kind="azure" returns None when Azure Search keys unset, else AzureSemanticReranker
- reranker_kind="cohere" parity with W3 D1 tests preserved
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from retrieval.hybrid import HybridSearchHit
from retrieval.reranker.azure_semantic import AzureSemanticReranker
from retrieval.reranker.cohere import CohereReranker
from retrieval.reranker.factory import make_reranker
from retrieval.reranker.voyage import VoyageReranker
from retrieval.reranker.zeroentropy import ZeroEntropyReranker
from storage.settings import Settings


def _mock_response(status_code: int, body: dict) -> MagicMock:
    response = MagicMock(spec=httpx.Response)
    response.status_code = status_code
    response.json = MagicMock(return_value=body)
    response.raise_for_status = MagicMock()
    return response


def _hits(*texts: str) -> list[HybridSearchHit]:
    return [
        HybridSearchHit(
            score=0.5,
            fields={"chunk_id": f"c{i}", "chunk_text": t},
        )
        for i, t in enumerate(texts)
    ]


# ---------- VoyageReranker ---------------------------------------------------


@pytest.mark.asyncio
async def test_voyage_empty_candidates_returns_empty_no_call() -> None:
    with patch("retrieval.reranker.voyage.httpx.AsyncClient") as MockClient:
        instance = MockClient.return_value
        instance.post = AsyncMock()
        instance.aclose = AsyncMock()

        async with VoyageReranker(api_key="k") as r:
            result = await r.rerank("q", [], top_k=5)

        assert result == []
        instance.post.assert_not_awaited()


@pytest.mark.asyncio
async def test_voyage_orders_by_relevance_score_desc() -> None:
    body = {
        "data": [
            {"index": 2, "relevance_score": 0.95},
            {"index": 0, "relevance_score": 0.71},
            {"index": 1, "relevance_score": 0.30},
        ],
    }
    with patch("retrieval.reranker.voyage.httpx.AsyncClient") as MockClient:
        instance = MockClient.return_value
        instance.post = AsyncMock(return_value=_mock_response(200, body))
        instance.aclose = AsyncMock()

        async with VoyageReranker(api_key="k") as r:
            out = await r.rerank("query", _hits("a", "b", "c"), top_k=5)

    scores = [c.rerank_score for c in out]
    assert scores == sorted(scores, reverse=True)
    assert out[0].fields["chunk_id"] == "c2"
    assert out[0].original_index == 2
    assert out[0].hybrid_score == 0.5


@pytest.mark.asyncio
async def test_voyage_payload_shape() -> None:
    body = {"data": [{"index": 0, "relevance_score": 1.0}]}
    captured: dict = {}

    async def _capture(url, content):
        captured["url"] = url
        captured["content"] = content
        return _mock_response(200, body)

    with patch("retrieval.reranker.voyage.httpx.AsyncClient") as MockClient:
        instance = MockClient.return_value
        instance.post = AsyncMock(side_effect=_capture)
        instance.aclose = AsyncMock()

        async with VoyageReranker(api_key="key", model="voyage-rerank-2.5") as r:
            await r.rerank("hello", _hits("doc-a"), top_k=3)

    assert captured["url"] == "https://api.voyageai.com/v1/rerank"
    payload = json.loads(captured["content"])
    assert payload["model"] == "voyage-rerank-2.5"
    assert payload["query"] == "hello"
    assert payload["documents"] == ["doc-a"]
    assert payload["top_k"] == 1  # min(top_k=3, len=1)
    assert payload["return_documents"] is False


@pytest.mark.asyncio
async def test_voyage_top_k_clamped() -> None:
    body = {"data": [{"index": 0, "relevance_score": 0.9}]}
    captured: dict = {}

    async def _capture(url, content):
        captured["content"] = content
        return _mock_response(200, body)

    with patch("retrieval.reranker.voyage.httpx.AsyncClient") as MockClient:
        instance = MockClient.return_value
        instance.post = AsyncMock(side_effect=_capture)
        instance.aclose = AsyncMock()

        async with VoyageReranker(api_key="k") as r:
            await r.rerank("q", _hits("only"), top_k=10)

    assert json.loads(captured["content"])["top_k"] == 1


@pytest.mark.asyncio
async def test_voyage_invalid_index_skipped() -> None:
    body = {
        "data": [
            {"index": 0, "relevance_score": 0.9},
            {"index": 99, "relevance_score": 0.8},  # out-of-range
        ],
    }
    with patch("retrieval.reranker.voyage.httpx.AsyncClient") as MockClient:
        instance = MockClient.return_value
        instance.post = AsyncMock(return_value=_mock_response(200, body))
        instance.aclose = AsyncMock()

        async with VoyageReranker(api_key="k") as r:
            out = await r.rerank("q", _hits("a", "b"), top_k=5)

    assert len(out) == 1
    assert out[0].original_index == 0


# ---------- ZeroEntropyReranker ----------------------------------------------


@pytest.mark.asyncio
async def test_zeroentropy_empty_candidates_returns_empty_no_call() -> None:
    with patch("retrieval.reranker.zeroentropy.httpx.AsyncClient") as MockClient:
        instance = MockClient.return_value
        instance.post = AsyncMock()
        instance.aclose = AsyncMock()

        async with ZeroEntropyReranker(api_key="k") as r:
            result = await r.rerank("q", [], top_k=5)

        assert result == []
        instance.post.assert_not_awaited()


@pytest.mark.asyncio
async def test_zeroentropy_orders_by_relevance_score_desc() -> None:
    body = {
        "results": [
            {"index": 1, "relevance_score": 0.91},
            {"index": 0, "relevance_score": 0.42},
        ],
    }
    with patch("retrieval.reranker.zeroentropy.httpx.AsyncClient") as MockClient:
        instance = MockClient.return_value
        instance.post = AsyncMock(return_value=_mock_response(200, body))
        instance.aclose = AsyncMock()

        async with ZeroEntropyReranker(api_key="k") as r:
            out = await r.rerank("q", _hits("a", "b"), top_k=5)

    assert out[0].fields["chunk_id"] == "c1"
    assert out[0].original_index == 1
    assert out[0].rerank_score == pytest.approx(0.91)


@pytest.mark.asyncio
async def test_zeroentropy_payload_shape() -> None:
    body = {"results": [{"index": 0, "relevance_score": 1.0}]}
    captured: dict = {}

    async def _capture(url, content):
        captured["url"] = url
        captured["content"] = content
        return _mock_response(200, body)

    with patch("retrieval.reranker.zeroentropy.httpx.AsyncClient") as MockClient:
        instance = MockClient.return_value
        instance.post = AsyncMock(side_effect=_capture)
        instance.aclose = AsyncMock()

        async with ZeroEntropyReranker(api_key="key", model="zerank-1") as r:
            await r.rerank("hi", _hits("doc"), top_k=2)

    assert captured["url"] == "https://api.zeroentropy.dev/v1/rerank"
    payload = json.loads(captured["content"])
    assert payload["model"] == "zerank-1"
    assert payload["query"] == "hi"
    assert payload["documents"] == ["doc"]
    assert payload["top_n"] == 1


@pytest.mark.asyncio
async def test_zeroentropy_invalid_index_skipped() -> None:
    body = {
        "results": [
            {"index": 0, "relevance_score": 0.6},
            {"index": -1, "relevance_score": 0.5},
        ],
    }
    with patch("retrieval.reranker.zeroentropy.httpx.AsyncClient") as MockClient:
        instance = MockClient.return_value
        instance.post = AsyncMock(return_value=_mock_response(200, body))
        instance.aclose = AsyncMock()

        async with ZeroEntropyReranker(api_key="k") as r:
            out = await r.rerank("q", _hits("a"), top_k=5)

    assert len(out) == 1
    assert out[0].original_index == 0


# ---------- AzureSemanticReranker -------------------------------------------


@pytest.mark.asyncio
async def test_azure_semantic_empty_candidates_returns_empty_no_call() -> None:
    with patch("retrieval.reranker.azure_semantic.httpx.AsyncClient") as MockClient:
        instance = MockClient.return_value
        instance.post = AsyncMock()
        instance.aclose = AsyncMock()

        async with AzureSemanticReranker(
            endpoint="https://x.search.windows.net",
            admin_key="k",
            index_name="ekp-kb-drive-v1",
        ) as r:
            result = await r.rerank("q", [], top_k=5)

        assert result == []
        instance.post.assert_not_awaited()


@pytest.mark.asyncio
async def test_azure_semantic_normalises_0_4_score_to_0_1() -> None:
    body = {
        "value": [
            {"chunk_id": "c0", "@search.rerankerScore": 4.0},   # → 1.0
            {"chunk_id": "c1", "@search.rerankerScore": 2.0},   # → 0.5
        ],
    }
    with patch("retrieval.reranker.azure_semantic.httpx.AsyncClient") as MockClient:
        instance = MockClient.return_value
        instance.post = AsyncMock(return_value=_mock_response(200, body))
        instance.aclose = AsyncMock()

        async with AzureSemanticReranker(
            endpoint="https://x.search.windows.net",
            admin_key="k",
            index_name="ekp-kb-drive-v1",
        ) as r:
            out = await r.rerank("q", _hits("a", "b"), top_k=5)

    assert {c.fields["chunk_id"]: c.rerank_score for c in out} == {
        "c0": pytest.approx(1.0),
        "c1": pytest.approx(0.5),
    }


@pytest.mark.asyncio
async def test_azure_semantic_payload_shape() -> None:
    body = {"value": [{"chunk_id": "c0", "@search.rerankerScore": 3.0}]}
    captured: dict = {}

    async def _capture(url, content):
        captured["url"] = url
        captured["content"] = content
        return _mock_response(200, body)

    with patch("retrieval.reranker.azure_semantic.httpx.AsyncClient") as MockClient:
        instance = MockClient.return_value
        instance.post = AsyncMock(side_effect=_capture)
        instance.aclose = AsyncMock()

        async with AzureSemanticReranker(
            endpoint="https://x.search.windows.net",
            admin_key="k",
            index_name="ekp-kb-drive-v1",
            semantic_config="ekp-semantic-config",
        ) as r:
            await r.rerank("hi", _hits("a", "b"), top_k=5)

    assert (
        captured["url"]
        == "https://x.search.windows.net/indexes/ekp-kb-drive-v1/docs/search?api-version=2024-07-01"
    )
    payload = json.loads(captured["content"])
    assert payload["queryType"] == "semantic"
    assert payload["semanticConfiguration"] == "ekp-semantic-config"
    assert "search.in(chunk_id" in payload["filter"]
    assert "c0" in payload["filter"] and "c1" in payload["filter"]
    assert payload["top"] == 2
    assert payload["select"] == "chunk_id"


@pytest.mark.asyncio
async def test_azure_semantic_ignores_unknown_chunk_ids_in_response() -> None:
    body = {
        "value": [
            {"chunk_id": "c0", "@search.rerankerScore": 3.0},
            {"chunk_id": "stray-id", "@search.rerankerScore": 4.0},  # not in our candidate set
        ],
    }
    with patch("retrieval.reranker.azure_semantic.httpx.AsyncClient") as MockClient:
        instance = MockClient.return_value
        instance.post = AsyncMock(return_value=_mock_response(200, body))
        instance.aclose = AsyncMock()

        async with AzureSemanticReranker(
            endpoint="https://x.search.windows.net",
            admin_key="k",
            index_name="ekp-kb-drive-v1",
        ) as r:
            out = await r.rerank("q", _hits("a"), top_k=5)

    assert len(out) == 1
    assert out[0].fields["chunk_id"] == "c0"


# ---------- factory dispatch -------------------------------------------------


def test_factory_off_returns_none_even_when_keys_set() -> None:
    settings = Settings(
        reranker_kind="off",
        cohere_endpoint="https://m.example.com",
        cohere_api_key="key",
        voyage_api_key="vk",
        zeroentropy_api_key="zk",
    )
    assert make_reranker(settings) is None


def test_factory_cohere_parity_w3_d1() -> None:
    settings = Settings(
        reranker_kind="cohere",
        cohere_endpoint="https://m.example.com",
        cohere_api_key="key",
        cohere_procurement_path="A",
        # CH-020 / ADR-0074 — isolate the W3 D1 cohere-dispatch parity from the new
        # hot-fallback wrap (which would return FallbackReranker when Azure creds are
        # present in .env). FallbackReranker dispatch is covered in test_reranker_fallback.
        reranker_fallback_enabled=False,
    )
    r = make_reranker(settings)
    assert isinstance(r, CohereReranker)


def test_factory_voyage_returns_none_when_key_unset() -> None:
    settings = Settings(reranker_kind="voyage", voyage_api_key="")
    assert make_reranker(settings) is None


def test_factory_voyage_returns_voyage_when_key_set() -> None:
    settings = Settings(reranker_kind="voyage", voyage_api_key="vk")
    r = make_reranker(settings)
    assert isinstance(r, VoyageReranker)
    assert r.api_key == "vk"


def test_factory_zeroentropy_returns_none_when_key_unset() -> None:
    settings = Settings(reranker_kind="zeroentropy", zeroentropy_api_key="")
    assert make_reranker(settings) is None


def test_factory_zeroentropy_returns_zeroentropy_when_key_set() -> None:
    settings = Settings(reranker_kind="zeroentropy", zeroentropy_api_key="zk")
    r = make_reranker(settings)
    assert isinstance(r, ZeroEntropyReranker)


def test_factory_azure_returns_azure_when_search_keys_set() -> None:
    settings = Settings(
        reranker_kind="azure",
        azure_search_endpoint="https://x.search.windows.net",
        azure_search_admin_key="ak",
        azure_search_default_index="ekp-kb-drive-v1",
        azure_semantic_config_name="ekp-semantic-config",
    )
    r = make_reranker(settings)
    assert isinstance(r, AzureSemanticReranker)
    assert r.semantic_config == "ekp-semantic-config"


def test_factory_azure_returns_none_when_search_admin_key_unset() -> None:
    settings = Settings(
        reranker_kind="azure",
        azure_search_endpoint="https://x.search.windows.net",
        azure_search_admin_key="",
    )
    assert make_reranker(settings) is None
