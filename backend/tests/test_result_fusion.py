"""Reciprocal Rank Fusion unit tests (W25 F3.5 per ADR-0034; CLAUDE.md §5.6 H6).

Coverage:
- fused_retrieve(empty variants) → empty result, no engine call
- fused_retrieve(single variant) = identity ordering = engine.retrieve baseline
- fused_retrieve(N variants) parallel via asyncio.gather (single longest-tail latency)
- RRF formula correctness:known rank inputs → expected fused order
- Top-K cap:returns at most top_k chunks even if union > top_k
- Dedup by chunk_id:same chunk in N variants accumulates rrf_score sum
- Stable tie-break by chunk_id when RRF scores equal
- Skips malformed chunks (empty chunk_id)
- as_retrieval_result shape adapter: chunks preserved, timings adapted
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from retrieval.result_fusion import (
    RRF_K_DEFAULT,
    FusedRetrievalResult,
    fused_retrieve,
)
from retrieval.retrieval_engine import RetrievalResult, RetrievedChunk


# ---------- helpers ----------------------------------------------------------


def _chunk(chunk_id: str, score: float = 0.8) -> RetrievedChunk:
    return RetrievedChunk(
        score=score,
        fields={
            "chunk_id": chunk_id,
            "chunk_title": f"title-{chunk_id}",
            "chunk_text": f"body-{chunk_id}",
        },
    )


def _retrieval_result(*chunk_ids: str, latency_ms: int = 100, reranked: bool = True) -> RetrievalResult:
    return RetrievalResult(
        chunks=[_chunk(cid) for cid in chunk_ids],
        embed_latency_ms=10,
        search_latency_ms=80,
        rerank_latency_ms=10 if reranked else 0,
        total_latency_ms=latency_ms,
        reranked=reranked,
    )


def _engine_with_per_variant_results(*per_variant_chunk_ids: list[str]) -> MagicMock:
    """Build a MagicMock RetrievalEngine where each call to retrieve() returns the
    next queued RetrievalResult — one list[str] per expected variant."""
    engine = MagicMock()
    results = [_retrieval_result(*cids) for cids in per_variant_chunk_ids]
    engine.retrieve = AsyncMock(side_effect=results)
    return engine


# ---------- edge cases -------------------------------------------------------


@pytest.mark.asyncio
async def test_fused_retrieve_empty_variants_returns_empty() -> None:
    engine = _engine_with_per_variant_results()  # no variants → no engine calls
    result = await fused_retrieve(
        variants=[],
        kb_id="kb1",
        top_k=5,
        engine=engine,
    )
    assert result.chunks == []
    assert result.variant_count == 0
    assert result.fused_top_k == 5
    engine.retrieve.assert_not_called()


@pytest.mark.asyncio
async def test_fused_retrieve_single_variant_identity_ordering() -> None:
    # Single variant retrieving 3 chunks → RRF over 1 list = ranking preserved
    engine = _engine_with_per_variant_results(["a", "b", "c"])
    result = await fused_retrieve(
        variants=["query A"],
        kb_id="kb1",
        top_k=3,
        engine=engine,
    )
    assert [c.fields["chunk_id"] for c in result.chunks] == ["a", "b", "c"]
    assert result.variant_count == 1
    engine.retrieve.assert_called_once()


# ---------- RRF formula correctness ------------------------------------------


@pytest.mark.asyncio
async def test_fused_retrieve_rrf_formula_three_variants() -> None:
    """RRF score = sum over variants of 1/(60 + rank). With 3 variants ranking:
    variant 1: a@1, b@2, c@3
    variant 2: b@1, a@2, d@3
    variant 3: c@1, d@2, a@3

    Expected RRF scores (k=60):
    a = 1/61 + 1/62 + 1/63 ≈ 0.04830
    b = 1/62 + 1/61          ≈ 0.03253
    c = 1/63 + 1/61          ≈ 0.03227
    d = 1/63 + 1/62          ≈ 0.03200

    Expected fused order: a, b, c, d.
    """
    engine = _engine_with_per_variant_results(
        ["a", "b", "c"],
        ["b", "a", "d"],
        ["c", "d", "a"],
    )
    result = await fused_retrieve(
        variants=["v1", "v2", "v3"],
        kb_id="kb1",
        top_k=4,
        engine=engine,
    )

    chunk_ids = [c.fields["chunk_id"] for c in result.chunks]
    assert chunk_ids == ["a", "b", "c", "d"]
    assert result.variant_count == 3
    assert engine.retrieve.call_count == 3


@pytest.mark.asyncio
async def test_fused_retrieve_top_k_caps_result() -> None:
    engine = _engine_with_per_variant_results(
        ["a", "b", "c"],
        ["d", "e", "f"],
    )
    result = await fused_retrieve(
        variants=["v1", "v2"],
        kb_id="kb1",
        top_k=2,
        engine=engine,
    )
    # Despite union {a,b,c,d,e,f}, only top 2 returned
    assert len(result.chunks) == 2


@pytest.mark.asyncio
async def test_fused_retrieve_dedup_same_chunk_across_variants() -> None:
    # All 3 variants surface the same single chunk → result has 1 chunk
    engine = _engine_with_per_variant_results(
        ["a"],
        ["a"],
        ["a"],
    )
    result = await fused_retrieve(
        variants=["v1", "v2", "v3"],
        kb_id="kb1",
        top_k=3,
        engine=engine,
    )
    assert len(result.chunks) == 1
    assert result.chunks[0].fields["chunk_id"] == "a"
    # RRF score for chunk 'a' = 3/(60+1) — score field of result.chunks[0]
    assert result.chunks[0].score == pytest.approx(3 / 61, rel=1e-6)


@pytest.mark.asyncio
async def test_fused_retrieve_tie_break_by_chunk_id_alphabetical() -> None:
    # Both chunks rank #1 in their own variant → identical RRF score → stable
    # tie-break by chunk_id ASC (z comes after a alphabetically)
    engine = _engine_with_per_variant_results(
        ["alpha"],
        ["zulu"],
    )
    result = await fused_retrieve(
        variants=["v1", "v2"],
        kb_id="kb1",
        top_k=2,
        engine=engine,
    )
    assert [c.fields["chunk_id"] for c in result.chunks] == ["alpha", "zulu"]


@pytest.mark.asyncio
async def test_fused_retrieve_skips_chunks_with_empty_chunk_id() -> None:
    # Variant returns chunks with empty chunk_id → those must be skipped
    bad_chunk = RetrievedChunk(score=0.9, fields={"chunk_id": "", "chunk_text": "garbage"})
    good_chunk = _chunk("good")
    engine = MagicMock()
    engine.retrieve = AsyncMock(return_value=RetrievalResult(
        chunks=[bad_chunk, good_chunk],
        embed_latency_ms=0,
        search_latency_ms=0,
        rerank_latency_ms=0,
        total_latency_ms=0,
        reranked=False,
    ))
    result = await fused_retrieve(
        variants=["v1"],
        kb_id="kb1",
        top_k=5,
        engine=engine,
    )
    assert [c.fields["chunk_id"] for c in result.chunks] == ["good"]


# ---------- parallel fan-out -------------------------------------------------


@pytest.mark.asyncio
async def test_fused_retrieve_kicks_off_variants_concurrently() -> None:
    """Total wall-clock latency ≈ max(per-variant) not sum — fan-out parallel."""
    call_count = 0
    barrier_event = asyncio.Event()

    async def _slow_retrieve(*_: object, **__: object) -> RetrievalResult:
        nonlocal call_count
        call_count += 1
        # Each call waits for the barrier; if execution is parallel, all 3
        # calls arrive at the wait point before any can resume.
        if call_count == 3:
            barrier_event.set()
        await barrier_event.wait()
        return _retrieval_result("a", "b")

    engine = MagicMock()
    engine.retrieve = AsyncMock(side_effect=_slow_retrieve)

    # If gather is serial, the first call blocks forever (event never sets).
    # With parallel gather, all 3 reach wait → call #3 sets event → all unblock.
    result = await asyncio.wait_for(
        fused_retrieve(
            variants=["v1", "v2", "v3"],
            kb_id="kb1",
            top_k=5,
            engine=engine,
        ),
        timeout=2.0,
    )
    assert result.variant_count == 3
    assert call_count == 3


# ---------- per_variant_overfetch --------------------------------------------


@pytest.mark.asyncio
async def test_fused_retrieve_per_variant_overfetch_default_2x() -> None:
    """Per-variant fetch_k = per_variant_overfetch * top_k (default 2× the
    final top_k cap)."""
    engine = _engine_with_per_variant_results(["a", "b"])
    await fused_retrieve(
        variants=["v1"],
        kb_id="kb1",
        top_k=5,
        engine=engine,
    )
    # First positional kwargs: engine.retrieve(query=..., kb_id=..., top_k=...)
    call_kwargs = engine.retrieve.call_args.kwargs
    assert call_kwargs["top_k"] == 10  # 5 × default 2 overfetch


@pytest.mark.asyncio
async def test_fused_retrieve_per_variant_overfetch_configurable() -> None:
    engine = _engine_with_per_variant_results(["a"])
    await fused_retrieve(
        variants=["v1"],
        kb_id="kb1",
        top_k=5,
        engine=engine,
        per_variant_overfetch=3,
    )
    assert engine.retrieve.call_args.kwargs["top_k"] == 15


# ---------- FusedRetrievalResult shape adapter -------------------------------


@pytest.mark.asyncio
async def test_as_retrieval_result_preserves_chunks_and_total_latency() -> None:
    engine = _engine_with_per_variant_results(["a", "b"], ["c", "d"])
    fused = await fused_retrieve(
        variants=["v1", "v2"],
        kb_id="kb1",
        top_k=3,
        engine=engine,
    )
    adapted = fused.as_retrieval_result()

    assert adapted.chunks == fused.chunks
    assert adapted.reranked is True
    # adapted.search_latency_ms folds the per-variant sums; total_latency_ms
    # preserved from fused result
    assert adapted.total_latency_ms == fused.total_latency_ms


# ---------- defaults ---------------------------------------------------------


def test_rrf_k_default_is_60_per_cormack_2009() -> None:
    """Cormack et al. 2009 canonical RRF rank-floor — sanity check we did not
    accidentally change away from the paper's default."""
    assert RRF_K_DEFAULT == 60
