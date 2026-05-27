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
            await s.search("paper jam", [0.1] * 1024, kb_id="drive_user_manuals", top_k=50)

    payload = json.loads(instance.post.await_args.kwargs["content"])
    assert payload["search"] == "paper jam"
    assert payload["top"] == 50
    assert payload["queryType"] == "semantic"
    assert payload["semanticConfiguration"] == "ekp-semantic-config"
    # ADR-0018 multi-KB invariant: kb_id eq prepended to default filter
    # ADR-0035 W25 F5 D2: low_value_flag eq false removed from server-side
    # filter; client-side post-filter handles low_value chunks
    assert (
        payload["filter"]
        == "kb_id eq 'drive_user_manuals' and enabled eq true"
    )
    assert payload["vectorQueries"][0]["fields"] == "content_vector"
    assert payload["vectorQueries"][0]["k"] == 50
    assert len(payload["vectorQueries"][0]["vector"]) == 1024
    # hybrid is the default mode — payload identical whether mode omitted or "hybrid".


@pytest.mark.asyncio
async def test_hybrid_search_mode_vector_payload_shape() -> None:
    """ADR-0021: mode='vector' → search='*' + vectorQueries; no semantic config."""
    with patch("retrieval.hybrid.httpx.AsyncClient") as MockClient:
        instance = MockClient.return_value
        instance.post = AsyncMock(return_value=_mock_response(200, {"value": []}))
        instance.aclose = AsyncMock()

        async with HybridSearcher("https://x", "k", "idx") as s:
            await s.search(
                "paper jam", [0.2] * 1024, kb_id="drive_user_manuals",
                top_k=10, mode="vector",
            )

    payload = json.loads(instance.post.await_args.kwargs["content"])
    assert payload["search"] == "*"
    assert payload["top"] == 10
    assert "queryType" not in payload
    assert "semanticConfiguration" not in payload
    assert payload["vectorQueries"][0]["fields"] == "content_vector"
    assert len(payload["vectorQueries"][0]["vector"]) == 1024


@pytest.mark.asyncio
async def test_hybrid_search_mode_fulltext_payload_shape() -> None:
    """ADR-0021: mode='fulltext' → BM25-only (queryType='simple'); no vectorQueries."""
    with patch("retrieval.hybrid.httpx.AsyncClient") as MockClient:
        instance = MockClient.return_value
        instance.post = AsyncMock(return_value=_mock_response(200, {"value": []}))
        instance.aclose = AsyncMock()

        async with HybridSearcher("https://x", "k", "idx") as s:
            await s.search(
                "paper jam", [], kb_id="drive_user_manuals",
                top_k=15, mode="fulltext",
            )

    payload = json.loads(instance.post.await_args.kwargs["content"])
    assert payload["search"] == "paper jam"
    assert payload["top"] == 15
    assert payload["queryType"] == "simple"
    assert "vectorQueries" not in payload
    assert "semanticConfiguration" not in payload


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
            hits = await s.search("query", [0.0] * 1024, kb_id="drive_user_manuals", top_k=2)

    assert len(hits) == 2
    assert hits[0].score == 0.91
    assert hits[0].fields["chunk_id"] == "kb-drive_doc-A_chunk-0007"
    assert "@search.score" not in hits[0].fields  # stripped


@pytest.mark.asyncio
async def test_hybrid_search_custom_filter_clause_prepends_kb_id() -> None:
    """ADR-0018: caller-supplied filter is conjuncted with mandatory kb_id eq clause."""
    with patch("retrieval.hybrid.httpx.AsyncClient") as MockClient:
        instance = MockClient.return_value
        instance.post = AsyncMock(return_value=_mock_response(200, {"value": []}))
        instance.aclose = AsyncMock()

        async with HybridSearcher("https://x", "k", "idx") as s:
            await s.search(
                "q",
                [0.0] * 1024,
                kb_id="finance_dept",
                filter_clause="enabled eq true",
            )

    payload = json.loads(instance.post.await_args.kwargs["content"])
    assert payload["filter"] == "kb_id eq 'finance_dept' and enabled eq true"


@pytest.mark.asyncio
async def test_hybrid_search_kb_id_only_filter_when_none_passed() -> None:
    """ADR-0018: filter_clause=None still applies kb_id eq scoping (multi-KB invariant)."""
    with patch("retrieval.hybrid.httpx.AsyncClient") as MockClient:
        instance = MockClient.return_value
        instance.post = AsyncMock(return_value=_mock_response(200, {"value": []}))
        instance.aclose = AsyncMock()

        async with HybridSearcher("https://x", "k", "idx") as s:
            await s.search("q", [0.0] * 1024, kb_id="rapo_internal", filter_clause=None)

    payload = json.loads(instance.post.await_args.kwargs["content"])
    assert payload["filter"] == "kb_id eq 'rapo_internal'"


@pytest.mark.asyncio
async def test_hybrid_search_dynamic_index_name_for_new_kb() -> None:
    """ADR-0018: kb_id != legacy → URL uses ekp-kb-{kb_id}-v1 per ADR-0005 convention."""
    with patch("retrieval.hybrid.httpx.AsyncClient") as MockClient:
        instance = MockClient.return_value
        instance.post = AsyncMock(return_value=_mock_response(200, {"value": []}))
        instance.aclose = AsyncMock()

        async with HybridSearcher("https://x", "k", "ekp-kb-drive-v1") as s:
            await s.search("q", [0.0] * 1024, kb_id="finance_dept")

    url_called = instance.post.await_args.args[0]
    assert "/indexes/ekp-kb-finance_dept-v1/" in url_called


@pytest.mark.asyncio
async def test_hybrid_search_legacy_alias_preserves_deployed_index() -> None:
    """ADR-0018: kb_id='drive_user_manuals' uses self.index_name (Tier 1 legacy alias)."""
    with patch("retrieval.hybrid.httpx.AsyncClient") as MockClient:
        instance = MockClient.return_value
        instance.post = AsyncMock(return_value=_mock_response(200, {"value": []}))
        instance.aclose = AsyncMock()

        async with HybridSearcher("https://x", "k", "ekp-kb-drive-v1") as s:
            await s.search("q", [0.0] * 1024, kb_id="drive_user_manuals")

    url_called = instance.post.await_args.args[0]
    assert "/indexes/ekp-kb-drive-v1/" in url_called


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
            hits = await s.search("q", [0.0] * 1024, kb_id="drive_user_manuals")

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
    result = await engine.retrieve(query="   ", kb_id="drive_user_manuals", top_k=10)

    assert isinstance(result, RetrievalResult)
    assert result.chunks == []
    searcher.search.assert_not_called()


@pytest.mark.asyncio
async def test_retrieval_engine_calls_embedder_then_searcher_with_kb_id() -> None:
    embedder = _FakeEmbedder()
    searcher = MagicMock()
    searcher.search = AsyncMock(
        return_value=[
            HybridSearchHit(score=0.9, fields={"chunk_id": "c1", "chunk_text": "t1"}),
            HybridSearchHit(score=0.5, fields={"chunk_id": "c2", "chunk_text": "t2"}),
        ],
    )

    engine = RetrievalEngine(embedder=embedder, searcher=searcher)
    result = await engine.retrieve(query="how to recover", kb_id="drive_user_manuals", top_k=5)

    assert len(result.chunks) == 2
    assert result.chunks[0].score == 0.9
    assert result.chunks[0].fields["chunk_id"] == "c1"
    searcher.search.assert_awaited_once()
    call_kwargs = searcher.search.await_args.kwargs
    assert call_kwargs["query_text"] == "how to recover"
    assert call_kwargs["kb_id"] == "drive_user_manuals"  # ADR-0018 propagation
    assert len(call_kwargs["query_vector"]) == 1024
    assert call_kwargs["top_k"] == 5


@pytest.mark.asyncio
async def test_retrieval_engine_default_filter_clause_applied() -> None:
    embedder = _FakeEmbedder()
    searcher = MagicMock()
    searcher.search = AsyncMock(return_value=[])

    engine = RetrievalEngine(embedder=embedder, searcher=searcher)
    await engine.retrieve(query="q", kb_id="drive_user_manuals")

    call_kwargs = searcher.search.await_args.kwargs
    # ADR-0035 W25 F5 D2: engine baseline filter no longer includes
    # low_value_flag eq false (moved to client-side post-filter)
    assert call_kwargs["filter_clause"] == "enabled eq true"


@pytest.mark.asyncio
async def test_retrieval_engine_custom_filter_clause_passes_through() -> None:
    embedder = _FakeEmbedder()
    searcher = MagicMock()
    searcher.search = AsyncMock(return_value=[])

    engine = RetrievalEngine(embedder=embedder, searcher=searcher)
    await engine.retrieve(query="q", kb_id="finance_dept", filter_clause="tags/any(t: t eq 'public')")

    call_kwargs = searcher.search.await_args.kwargs
    assert call_kwargs["filter_clause"] == "tags/any(t: t eq 'public')"


@pytest.mark.asyncio
async def test_retrieval_engine_kb_id_propagates_to_searcher() -> None:
    """ADR-0018 multi-KB invariant: kb_id explicitly forwarded to HybridSearcher.search()."""
    embedder = _FakeEmbedder()
    searcher = MagicMock()
    searcher.search = AsyncMock(return_value=[])

    engine = RetrievalEngine(embedder=embedder, searcher=searcher)
    await engine.retrieve(query="q", kb_id="rapo_internal", top_k=5)

    call_kwargs = searcher.search.await_args.kwargs
    assert call_kwargs["kb_id"] == "rapo_internal"


@pytest.mark.asyncio
async def test_retrieval_engine_records_latencies() -> None:
    embedder = _FakeEmbedder()
    searcher = MagicMock()
    searcher.search = AsyncMock(return_value=[])

    engine = RetrievalEngine(embedder=embedder, searcher=searcher)
    result = await engine.retrieve(query="q", kb_id="drive_user_manuals", top_k=10)

    assert result.embed_latency_ms >= 0
    assert result.search_latency_ms >= 0
    assert result.total_latency_ms >= max(result.embed_latency_ms, result.search_latency_ms)
    assert result.reranked is False
    assert result.rerank_latency_ms == 0


@pytest.mark.asyncio
async def test_retrieval_engine_overfetches_when_reranker_present() -> None:
    """With reranker configured, hybrid fetch_k = max(top_k, hybrid_overfetch)."""
    from retrieval.reranker.base import RerankedChunk

    embedder = _FakeEmbedder()
    searcher = MagicMock()
    searcher.search = AsyncMock(return_value=[
        HybridSearchHit(score=0.5, fields={"chunk_id": f"c{i}", "chunk_text": "x"})
        for i in range(50)
    ])
    reranker = MagicMock()
    reranker.rerank = AsyncMock(return_value=[
        RerankedChunk(fields={"chunk_id": "c0"}, rerank_score=0.99, hybrid_score=0.5, original_index=0),
    ])

    engine = RetrievalEngine(
        embedder=embedder, searcher=searcher, reranker=reranker, hybrid_overfetch_for_rerank=50
    )
    result = await engine.retrieve(query="q", kb_id="drive_user_manuals", top_k=5)

    assert searcher.search.await_args.kwargs["top_k"] == 50
    assert reranker.rerank.await_count == 1
    assert result.reranked is True
    assert len(result.chunks) == 1
    assert result.chunks[0].score == 0.99  # rerank_score replaces hybrid score


@pytest.mark.asyncio
async def test_retrieval_engine_no_rerank_call_when_hits_empty() -> None:
    embedder = _FakeEmbedder()
    searcher = MagicMock()
    searcher.search = AsyncMock(return_value=[])
    reranker = MagicMock()
    reranker.rerank = AsyncMock()

    engine = RetrievalEngine(embedder=embedder, searcher=searcher, reranker=reranker)
    result = await engine.retrieve(query="q", kb_id="drive_user_manuals", top_k=5)

    reranker.rerank.assert_not_awaited()
    assert result.reranked is False
    assert result.chunks == []


# ---------- W38 reranker cross-section deboost tests ----------
# Per ADR-0035 W25 F5 D2 symmetric pattern reference;non-architectural per H1
# (post-rerank client-side score multiply,Cohere v4.0-pro contract unchanged)。


from retrieval.reranker.base import RerankedChunk  # noqa: E402


def _reranked(chunk_id: str, score: float, section_path: list[str] | None = None,
              extra: dict | None = None, *, original_index: int = 0,
              hybrid_score: float | None = None) -> RerankedChunk:
    """Build a RerankedChunk mock with explicit section_path for deboost testing.

    RerankedChunk is frozen=True (slots=True) with required fields:
    fields + rerank_score + hybrid_score + original_index.
    """
    fields = {"chunk_id": chunk_id, "chunk_text": chunk_id}
    if section_path is not None:
        fields["section_path"] = section_path
    if extra:
        fields.update(extra)
    return RerankedChunk(
        fields=fields,
        rerank_score=score,
        hybrid_score=hybrid_score if hybrid_score is not None else score,
        original_index=original_index,
    )


@pytest.mark.asyncio
async def test_w38_reranker_deboost_disabled_default_no_op() -> None:
    """deboost=1.0 (default) → reranked order untouched (W37 baseline preserve)."""
    embedder = _FakeEmbedder()
    searcher = MagicMock()
    searcher.search = AsyncMock(
        return_value=[HybridSearchHit(score=0.9, fields={"chunk_id": "c1"})],
    )
    reranker = MagicMock()
    # Cross-section candidates — but deboost=1.0 = no-op
    reranker.rerank = AsyncMock(
        return_value=[
            _reranked("a", 0.9, section_path=["Doc", "§8"]),
            _reranked("b", 0.8, section_path=["Doc", "§11"]),  # cross-section,但 deboost disabled
            _reranked("c", 0.7, section_path=["Doc", "§8", "§8.4"]),
        ],
    )

    engine = RetrievalEngine(
        embedder=embedder, searcher=searcher, reranker=reranker,
        reranker_cross_section_deboost=1.0,  # disabled
    )
    result = await engine.retrieve(query="q", kb_id="drive_user_manuals", top_k=3)

    # Order unchanged — `b` keeps original rerank_score 0.8
    assert [c.fields["chunk_id"] for c in result.chunks] == ["a", "b", "c"]
    assert result.chunks[1].score == 0.8


@pytest.mark.asyncio
async def test_w38_reranker_deboost_cross_section_score_reduced() -> None:
    """anchor §8 + 候選 §11 → rerank_score *= 0.85;re-sort 後 cross-section 排尾。"""
    embedder = _FakeEmbedder()
    searcher = MagicMock()
    searcher.search = AsyncMock(return_value=[HybridSearchHit(score=0.9, fields={})])
    reranker = MagicMock()
    reranker.rerank = AsyncMock(
        return_value=[
            _reranked("a", 0.90, section_path=["Doc", "§8"]),                         # anchor
            _reranked("b", 0.88, section_path=["Doc", "§11", "§11.2 Phase 1"]),       # cross → × 0.85 = 0.748
            _reranked("c", 0.80, section_path=["Doc", "§8", "§8.4 Scenario D"]),      # same-section preserved
        ],
    )

    engine = RetrievalEngine(
        embedder=embedder, searcher=searcher, reranker=reranker,
        reranker_cross_section_deboost=0.85,
        reranker_section_path_prefix_depth=2,
    )
    result = await engine.retrieve(query="q", kb_id="drive_user_manuals", top_k=3)

    # Post-deboost order:a (0.90) > c (0.80) > b (0.748 deboosted)
    assert [c.fields["chunk_id"] for c in result.chunks] == ["a", "c", "b"]
    # b's score reduced by deboost factor
    assert result.chunks[2].score == pytest.approx(0.88 * 0.85, abs=1e-6)


@pytest.mark.asyncio
async def test_w38_reranker_deboost_same_section_hierarchical_zoom_preserved() -> None:
    """anchor §8 + 候選 §8.4 (hierarchical zoom-in) → score preserved,NOT deboosted。"""
    embedder = _FakeEmbedder()
    searcher = MagicMock()
    searcher.search = AsyncMock(return_value=[HybridSearchHit(score=0.9, fields={})])
    reranker = MagicMock()
    reranker.rerank = AsyncMock(
        return_value=[
            _reranked("anchor", 0.90, section_path=["Doc", "§8"]),                    # anchor depth=1
            _reranked("sub_a", 0.85, section_path=["Doc", "§8", "§8.4"]),             # depth=2,prefix[:2]=["Doc","§8"] match anchor[:2]=["Doc","§8"]
            _reranked("sub_b", 0.80, section_path=["Doc", "§8", "§8.5"]),
        ],
    )

    engine = RetrievalEngine(
        embedder=embedder, searcher=searcher, reranker=reranker,
        reranker_cross_section_deboost=0.85,
        reranker_section_path_prefix_depth=2,
    )
    result = await engine.retrieve(query="q", kb_id="drive_user_manuals", top_k=3)

    # 全部 preserve(anchor prefix [:2] = ["Doc","§8"] partial,sub_a+sub_b [:2] = ["Doc","§8"] match)
    # Note:anchor sp 只有 1 級「Doc","§8"」,prefix[:2] = ["Doc","§8"]
    # sub_a sp 有 3 級,prefix[:2] = ["Doc","§8"] = anchor 同 → preserved
    assert all(c.score == orig for c, orig in zip(
        result.chunks, [0.90, 0.85, 0.80], strict=True,
    ))


@pytest.mark.asyncio
async def test_w38_reranker_deboost_re_sort_invariant() -> None:
    """Deboost 觸發後 rerank_score 必須 descending sorted。"""
    embedder = _FakeEmbedder()
    searcher = MagicMock()
    searcher.search = AsyncMock(return_value=[HybridSearchHit(score=0.9, fields={})])
    reranker = MagicMock()
    # Set up case where deboost shuffles ordering:
    # original [a 0.90, b 0.88, c 0.80] → after deboost [a 0.90, b 0.528, c 0.80]
    # → re-sort [a 0.90, c 0.80, b 0.528]
    reranker.rerank = AsyncMock(
        return_value=[
            _reranked("a", 0.90, section_path=["Doc", "§8"]),
            _reranked("b", 0.88, section_path=["Doc", "§11"]),
            _reranked("c", 0.80, section_path=["Doc", "§8"]),
        ],
    )

    engine = RetrievalEngine(
        embedder=embedder, searcher=searcher, reranker=reranker,
        reranker_cross_section_deboost=0.6,  # aggressive: 0.88 * 0.6 = 0.528 < 0.80
        reranker_section_path_prefix_depth=2,
    )
    result = await engine.retrieve(query="q", kb_id="drive_user_manuals", top_k=3)

    scores = [c.score for c in result.chunks]
    assert scores == sorted(scores, reverse=True), f"Not descending: {scores}"


@pytest.mark.asyncio
async def test_w38_reranker_deboost_malformed_section_path_defensive_skip() -> None:
    """候選 section_path 不是 list (None / str / missing) → 跳過 deboost preserve rank。"""
    embedder = _FakeEmbedder()
    searcher = MagicMock()
    searcher.search = AsyncMock(return_value=[HybridSearchHit(score=0.9, fields={})])
    reranker = MagicMock()
    reranker.rerank = AsyncMock(
        return_value=[
            _reranked("anchor", 0.90, section_path=["Doc", "§8"]),
            # malformed cases — defensive skip,score preserved
            RerankedChunk(fields={"chunk_id": "missing_sp"}, rerank_score=0.85, hybrid_score=0.85, original_index=1),
            RerankedChunk(fields={"chunk_id": "str_sp", "section_path": "Doc/§11"}, rerank_score=0.80, hybrid_score=0.80, original_index=2),
            # well-formed cross-section — gets deboosted
            _reranked("xs_well_formed", 0.75, section_path=["Doc", "§11"]),
        ],
    )

    engine = RetrievalEngine(
        embedder=embedder, searcher=searcher, reranker=reranker,
        reranker_cross_section_deboost=0.5,
        reranker_section_path_prefix_depth=2,
    )
    result = await engine.retrieve(query="q", kb_id="drive_user_manuals", top_k=4)

    by_id = {c.fields["chunk_id"]: c.score for c in result.chunks}
    # malformed candidates preserve original score (defensive skip)
    assert by_id["missing_sp"] == 0.85
    assert by_id["str_sp"] == 0.80
    # well-formed cross-section deboosted
    assert by_id["xs_well_formed"] == pytest.approx(0.75 * 0.5, abs=1e-6)
    # anchor preserved (no self-deboost)
    assert by_id["anchor"] == 0.90


# ---------- W40 F1 anchor-prefix length-mismatch fix tests ----------
# Per W39 insight 2 (architectural surface via Path A LIVE evidence).
# Bug:當 anchor_sp 短於 depth (corpus chapter intro chunk shape),
# `anchor_sp[:depth]` silent truncates,然後 cand_sp[:depth] 可能 longer →
# 必然 not-equal → over-deboost zoom-ins。Fix:effective_depth = min(depth, len(anchor_sp))


@pytest.mark.asyncio
async def test_w40_f1_anchor_shorter_than_depth_hierarchical_zoom_preserved() -> None:
    """W40 F1 — anchor sp length < depth (corpus chapter intro shape from W39 evidence)。

    Real corpus shape per W39 F2 Path A 5+5 LIVE runner output:
    - anchor `['8. Integration scenarios (end-to-end walkthroughs)']` length 1
    - cand_a same-chapter zoom-in `['8. Integration scenarios...', '8.1 Scenario A...']` length 2
    - cand_b cross-chapter `['7. Integration patterns by system', '7.9 Docuware']` length 2

    Pre-W40 F1 bug (depth=2 silent truncate):
    - anchor_prefix = anchor_sp[:2] = `['8. Integration scenarios...']` length 1
    - cand_a_prefix = cand_a[:2] = full list length 2
    - cand_a_prefix != anchor_prefix → over-DEBOOST (錯誤 — 明明 same-chapter zoom-in)

    Post-W40 F1 fix (effective_depth = min(2, 1) = 1):
    - anchor_prefix = `['8. Integration scenarios...']`
    - cand_a_prefix = cand_a[:1] = `['8. Integration scenarios...']` = anchor → preserved ✓
    - cand_b_prefix = cand_b[:1] = `['7. Integration patterns by system']` != anchor → DEBOOSTED ✓
    """
    embedder = _FakeEmbedder()
    searcher = MagicMock()
    searcher.search = AsyncMock(return_value=[HybridSearchHit(score=0.9, fields={})])
    reranker = MagicMock()
    reranker.rerank = AsyncMock(
        return_value=[
            _reranked("anchor", 0.90,
                      section_path=["8. Integration scenarios (end-to-end walkthroughs)"]),
            _reranked("cand_a_zoom_in", 0.85,
                      section_path=["8. Integration scenarios (end-to-end walkthroughs)",
                                    "8.1 Scenario A — Customer service request submission"]),
            _reranked("cand_b_cross_chapter", 0.80,
                      section_path=["7. Integration patterns by system", "7.9 Docuware"]),
        ],
    )

    engine = RetrievalEngine(
        embedder=embedder, searcher=searcher, reranker=reranker,
        reranker_cross_section_deboost=0.85,
        reranker_section_path_prefix_depth=2,
    )
    result = await engine.retrieve(query="q", kb_id="drive_user_manuals", top_k=3)

    by_id = {c.fields["chunk_id"]: c.score for c in result.chunks}
    # Anchor preserved (always)
    assert by_id["anchor"] == 0.90
    # Same-chapter zoom-in PRESERVED (W40 F1 fix — pre-fix would deboost to 0.85 * 0.85 = 0.7225)
    assert by_id["cand_a_zoom_in"] == 0.85
    # Cross-chapter DEBOOSTED (still correct behavior)
    assert by_id["cand_b_cross_chapter"] == pytest.approx(0.80 * 0.85, abs=1e-6)


@pytest.mark.asyncio
async def test_w40_f1_anchor_empty_section_path_no_deboost_defensive() -> None:
    """W40 F1 — anchor section_path empty (defensive: 不能 classify cross-section)。

    When anchor has empty section_path (effective_depth=0), no deboost should
    apply — we can't compute cross-section relationship without anchor reference.
    All candidates preserved at original scores. Defensive symmetric to W38
    malformed-cand-skip behavior.
    """
    embedder = _FakeEmbedder()
    searcher = MagicMock()
    searcher.search = AsyncMock(return_value=[HybridSearchHit(score=0.9, fields={})])
    reranker = MagicMock()
    reranker.rerank = AsyncMock(
        return_value=[
            _reranked("anchor", 0.90, section_path=[]),  # empty anchor
            _reranked("cand_a", 0.85, section_path=["§8", "§8.1"]),
            _reranked("cand_b", 0.80, section_path=["§7", "§7.9"]),
        ],
    )

    engine = RetrievalEngine(
        embedder=embedder, searcher=searcher, reranker=reranker,
        reranker_cross_section_deboost=0.85,
        reranker_section_path_prefix_depth=2,
    )
    result = await engine.retrieve(query="q", kb_id="drive_user_manuals", top_k=3)

    by_id = {c.fields["chunk_id"]: c.score for c in result.chunks}
    # All preserved — empty anchor → effective_depth=0 → no deboost applies
    assert by_id["anchor"] == 0.90
    assert by_id["cand_a"] == 0.85
    assert by_id["cand_b"] == 0.80
