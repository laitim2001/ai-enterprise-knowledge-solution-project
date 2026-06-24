"""Parent-Document Retriever tests per ADR-0037 W26 F2.

Covers `aggregate_parent_sections` algorithm + `ParentSectionChunk` /
`ParentDocStats` dataclasses + edge cases enumerated in plan.md checklist
F2.13 (a-k):

- a: Happy path (1 anchor → 1 parent → siblings aggregated)
- b: Multi-anchor dedupe (top-2 anchors share parent → fetch once)
- c: Section depth fallback (shallow section_path → doc-level fallback)
- d: Token budget truncation (parent > max_tokens → tail-drop preserving order)
- e: Cross-doc boundary respect (via searcher API doc_id arg)
- f: Empty input (reranked_chunks=[] → empty result + zero stats)
- g: Lookup miss (Azure Search returns 0 → graceful empty parent)
- h: Network error (graceful degradation, log + pass through anchors unchanged)
- j: Coexist with Context Expander (Q6 Both on — `expanded_text` preserved
  on non-anchor chunks; passthrough)
- k: Citation invariant — Citation.chunk_text references anchor's original
  chunk_text (parent_section_text is LLM-input-only)
- (i): Feature flag off scenario covered at pipeline integration layer, not
  here — the retriever assumes caller has checked the flag

Per CLAUDE.md §5.6 H6 — generation/retrieval critical pipeline test coverage.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from generation.parent_doc_retriever import (
    ParentDocStats,
    ParentSectionChunk,
    aggregate_parent_sections,
)

# ---------------------------------------------------------------------------
# Test fixtures — minimal RetrievedChunk + HybridSearchHit duck-typed shapes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _Chunk:
    """Duck-typed RetrievedChunk / ExpandedChunk for test input."""

    score: float
    fields: dict[str, Any]


def _make_chunk(
    *,
    chunk_id: str,
    doc_id: str,
    section_path: list[str],
    chunk_text: str,
    chunk_index: int = 0,
    score: float = 0.9,
    extra_fields: dict[str, Any] | None = None,
) -> _Chunk:
    fields: dict[str, Any] = {
        "chunk_id": chunk_id,
        "doc_id": doc_id,
        "section_path": section_path,
        "chunk_text": chunk_text,
        "chunk_index": chunk_index,
        **(extra_fields or {}),
    }
    return _Chunk(score=score, fields=fields)


def _make_sibling_hit(
    *,
    chunk_id: str,
    chunk_text: str,
    chunk_index: int = 0,
) -> object:
    """Duck-typed HybridSearchHit (score + fields)."""
    return _Chunk(
        score=1.0,
        fields={
            "chunk_id": chunk_id,
            "chunk_text": chunk_text,
            "chunk_index": chunk_index,
        },
    )


def _searcher_with_fetch(
    siblings_by_parent: dict[tuple[str, tuple[str, ...]], list[object]] | None = None,
    *,
    side_effect: Exception | None = None,
) -> tuple[MagicMock, AsyncMock]:
    """Build a mock HybridSearcher returning siblings keyed by (doc_id, parent_path).

    `side_effect` raises the given exception from fetch instead of returning normally.
    """
    searcher = MagicMock()

    async def _fetch(
        parent_path: list[str],
        doc_id: str,
        kb_id: str,
        *,
        max_chunks: int = 50,
        user_principals: list[str] | None = None,
    ) -> list[object]:
        if side_effect is not None:
            raise side_effect
        return (siblings_by_parent or {}).get((doc_id, tuple(parent_path)), [])

    fetch_mock = AsyncMock(side_effect=_fetch)
    searcher.fetch_chunks_by_section_path = fetch_mock
    return searcher, fetch_mock


# ---------------------------------------------------------------------------
# F2.13f — Empty input
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_empty_input_returns_empty_result_and_zero_stats() -> None:
    """reranked_chunks=[] → no fetch, empty list, ParentDocStats all zero."""
    searcher, fetch_mock = _searcher_with_fetch({})

    result, stats = await aggregate_parent_sections(
        reranked_chunks=[],
        kb_id="drive_user_manuals",
        searcher=searcher,
    )

    assert result == []
    assert isinstance(stats, ParentDocStats)
    assert stats.requested_anchors == 0
    assert stats.parents_fetched == 0
    assert stats.siblings_aggregated == 0
    assert stats.skipped_shallow_count == 0
    assert stats.truncated_count == 0
    fetch_mock.assert_not_awaited()


# ---------------------------------------------------------------------------
# F2.13a — Happy path
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_happy_path_single_anchor_aggregates_parent_siblings() -> None:
    """1 anchor at ["Doc", "§8", "Scenario A"] → parent ["Doc", "§8"] → 5 siblings concat."""
    anchor = _make_chunk(
        chunk_id="kb-drive_doc-DCE_chunk-0044",
        doc_id="DCE_Integration_Platform",
        section_path=["DCE Document", "§8: Integration Scenarios", "Scenario A"],
        chunk_text="Scenario A: ERP↔CRM data sync",
        chunk_index=44,
        score=0.97,
    )
    siblings = [
        _make_sibling_hit(chunk_id="c44", chunk_text="§8 intro paragraph", chunk_index=43),
        _make_sibling_hit(chunk_id="c45", chunk_text="Scenario A: ERP↔CRM data sync", chunk_index=44),
        _make_sibling_hit(chunk_id="c46", chunk_text="Scenario B: Order fulfillment relay", chunk_index=45),
        _make_sibling_hit(chunk_id="c47", chunk_text="Scenario C: Inventory reconciliation", chunk_index=46),
        _make_sibling_hit(chunk_id="c48", chunk_text="Scenario D: Customer master sync", chunk_index=47),
        _make_sibling_hit(chunk_id="c49", chunk_text="Scenario E: Financial close handoff", chunk_index=48),
    ]
    parent_key = ("DCE_Integration_Platform", ("DCE Document", "§8: Integration Scenarios"))
    searcher, fetch_mock = _searcher_with_fetch({parent_key: siblings})

    result, stats = await aggregate_parent_sections(
        reranked_chunks=[anchor],
        kb_id="drive_user_manuals",
        searcher=searcher,
    )

    fetch_mock.assert_awaited_once()
    assert len(result) == 1
    chunk = result[0]
    assert isinstance(chunk, ParentSectionChunk)
    assert chunk.score == pytest.approx(0.97)  # anchor score preserved
    assert chunk.sibling_count == 6
    assert chunk.parent_section_text is not None
    assert "Scenario A" in chunk.parent_section_text
    assert "Scenario E" in chunk.parent_section_text  # all 5 + intro joined
    assert chunk.truncated is False
    # New key added to fields dict; original keys preserved
    assert chunk.fields["parent_section_text"] == chunk.parent_section_text
    assert chunk.fields["chunk_id"] == "kb-drive_doc-DCE_chunk-0044"  # anchor's chunk_id intact
    assert stats.requested_anchors == 1
    assert stats.parents_fetched == 1
    assert stats.siblings_aggregated == 6


# ---------------------------------------------------------------------------
# F2.13b — Multi-anchor dedupe
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_multi_anchor_dedupe_fetches_shared_parent_once() -> None:
    """top_k=2 anchors at sibling positions → 1 batched fetch + 2 anchored result rows."""
    anchor_a = _make_chunk(
        chunk_id="c-A",
        doc_id="DCE",
        section_path=["Doc", "§8", "Scenario A"],
        chunk_text="A",
    )
    anchor_b = _make_chunk(
        chunk_id="c-B",
        doc_id="DCE",
        section_path=["Doc", "§8", "Scenario B"],
        chunk_text="B",
    )
    siblings = [
        _make_sibling_hit(chunk_id="x", chunk_text="content", chunk_index=1)
    ]
    searcher, fetch_mock = _searcher_with_fetch({("DCE", ("Doc", "§8")): siblings})

    result, stats = await aggregate_parent_sections(
        reranked_chunks=[anchor_a, anchor_b],
        kb_id="drive_user_manuals",
        searcher=searcher,
        parent_doc_top_k=2,
    )

    assert fetch_mock.await_count == 1  # dedupe worked
    assert len(result) == 2  # both anchors got parent_section_text
    assert result[0].parent_section_text == "content"
    assert result[1].parent_section_text == "content"
    assert stats.parents_fetched == 1  # 1 unique parent
    assert stats.siblings_aggregated == 2  # 1 sibling × 2 anchors


# ---------------------------------------------------------------------------
# F2.13c — Section depth fallback
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_shallow_section_path_falls_back_to_top_segment_with_flag_on() -> None:
    """Anchor in `["DocOnly"]` with offset=1 + fallback=True → parent_path=["DocOnly"]."""
    anchor = _make_chunk(
        chunk_id="c-shallow",
        doc_id="DocOnly_doc",
        section_path=["DocOnly"],
        chunk_text="shallow chunk",
    )
    siblings = [_make_sibling_hit(chunk_id="x", chunk_text="content", chunk_index=1)]
    searcher, fetch_mock = _searcher_with_fetch({("DocOnly_doc", ("DocOnly",)): siblings})

    result, stats = await aggregate_parent_sections(
        reranked_chunks=[anchor],
        kb_id="drive_user_manuals",
        searcher=searcher,
        fallback_to_doc_on_shallow=True,
    )

    fetch_mock.assert_awaited_once()
    assert result[0].parent_section_text == "content"
    assert result[0].parent_path == ["DocOnly"]
    assert stats.skipped_shallow_count == 0


@pytest.mark.asyncio
async def test_shallow_section_path_skipped_with_flag_off() -> None:
    """Anchor `["DocOnly"]` with offset=1 + fallback=False → skipped (no fetch)."""
    anchor = _make_chunk(
        chunk_id="c-shallow",
        doc_id="DocOnly_doc",
        section_path=["DocOnly"],
        chunk_text="shallow chunk",
    )
    searcher, fetch_mock = _searcher_with_fetch({})

    result, stats = await aggregate_parent_sections(
        reranked_chunks=[anchor],
        kb_id="drive_user_manuals",
        searcher=searcher,
        fallback_to_doc_on_shallow=False,
    )

    fetch_mock.assert_not_awaited()
    assert result[0].parent_section_text is None  # pass through unchanged
    assert result[0].fields["chunk_id"] == "c-shallow"
    assert stats.skipped_shallow_count == 1


# ---------------------------------------------------------------------------
# F2.13d — Token budget truncation (tail-drop preserving narrative order)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_token_budget_truncates_with_tail_drop() -> None:
    """max_tokens=20 + 4 siblings × ~10 tokens each → first 2 in, last 2 tail-dropped, truncated=True."""
    anchor = _make_chunk(
        chunk_id="c-anchor",
        doc_id="D",
        section_path=["Doc", "§8", "Scenario A"],
        chunk_text="anchor text",
    )
    # ~10 token (~40 char) per sibling via 4-char-per-token heuristic
    long_text = "x" * 40
    siblings = [
        _make_sibling_hit(chunk_id=f"s{i}", chunk_text=long_text, chunk_index=i)
        for i in range(4)
    ]
    searcher, _ = _searcher_with_fetch({("D", ("Doc", "§8")): siblings})

    result, stats = await aggregate_parent_sections(
        reranked_chunks=[anchor],
        kb_id="drive_user_manuals",
        searcher=searcher,
        max_tokens_per_parent=20,  # ~80 chars; 2 siblings would exceed
    )

    assert result[0].truncated is True
    assert result[0].sibling_count < 4  # tail-dropped
    # Narrative start preserved (first siblings present)
    assert result[0].parent_section_text is not None
    assert result[0].parent_section_text.startswith(long_text)
    assert stats.truncated_count == 1


@pytest.mark.asyncio
async def test_token_budget_includes_first_sibling_even_if_over_budget() -> None:
    """Degenerate single-large-sibling-chunk doc → include 1 + flag truncated."""
    anchor = _make_chunk(
        chunk_id="c-anchor",
        doc_id="D",
        section_path=["Doc", "§"],
        chunk_text="anchor",
    )
    huge_text = "y" * 10_000  # ~2500 tokens
    siblings = [_make_sibling_hit(chunk_id="huge", chunk_text=huge_text, chunk_index=0)]
    searcher, _ = _searcher_with_fetch({("D", ("Doc",)): siblings})

    result, _ = await aggregate_parent_sections(
        reranked_chunks=[anchor],
        kb_id="drive_user_manuals",
        searcher=searcher,
        max_tokens_per_parent=100,  # smaller than huge_text alone
    )

    # First sibling always included so a degenerate doc still gets context
    assert result[0].sibling_count == 1
    assert result[0].parent_section_text == huge_text


# ---------------------------------------------------------------------------
# F2.13g — Lookup miss
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_lookup_miss_returns_anchor_unchanged() -> None:
    """Azure Search returns 0 hits (section_path mismatch) → pass anchor unchanged + flag stats."""
    anchor = _make_chunk(
        chunk_id="c-anchor",
        doc_id="D",
        section_path=["Doc", "§8", "Scenario A"],
        chunk_text="anchor text",
    )
    # Empty siblings list for the queried parent
    searcher, _ = _searcher_with_fetch({("D", ("Doc", "§8")): []})

    result, stats = await aggregate_parent_sections(
        reranked_chunks=[anchor],
        kb_id="drive_user_manuals",
        searcher=searcher,
    )

    assert result[0].parent_section_text is None
    assert result[0].sibling_count == 0
    assert result[0].fields["chunk_id"] == "c-anchor"  # anchor data intact
    assert stats.parents_fetched == 0


# ---------------------------------------------------------------------------
# F2.13h — Network error graceful degradation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_network_error_falls_back_gracefully() -> None:
    """fetch raises → log warning + return anchors unchanged (no exception bubbled up)."""
    anchor = _make_chunk(
        chunk_id="c-anchor",
        doc_id="D",
        section_path=["Doc", "§8", "Scenario A"],
        chunk_text="anchor text",
    )
    searcher, _ = _searcher_with_fetch({}, side_effect=RuntimeError("Azure 503"))

    # Should NOT raise — graceful degradation
    result, stats = await aggregate_parent_sections(
        reranked_chunks=[anchor],
        kb_id="drive_user_manuals",
        searcher=searcher,
    )

    assert result[0].parent_section_text is None  # no parent due to error
    assert result[0].fields["chunk_id"] == "c-anchor"  # anchor preserved
    assert stats.parents_fetched == 0


# ---------------------------------------------------------------------------
# F2.13j — Coexist with Context Expander (passthrough non-anchors)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_non_anchor_chunks_passthrough_with_expanded_text_preserved() -> None:
    """Q6 Both on — top_k=1 anchor expanded; top-2..top-K chunks pass through (incl. expanded_text)."""
    anchor = _make_chunk(
        chunk_id="c-anchor",
        doc_id="D",
        section_path=["Doc", "§8", "Scenario A"],
        chunk_text="A",
        extra_fields={"expanded_text": "prev\n\nA\n\nnext"},
    )
    # Non-anchor chunk with ADR-0020 Context Expander prev/next already merged
    passthrough_chunk = _make_chunk(
        chunk_id="c-other",
        doc_id="OtherDoc",
        section_path=["X", "Y"],
        chunk_text="other text",
        extra_fields={"expanded_text": "prev other\n\nother text\n\nnext other"},
    )
    siblings = [_make_sibling_hit(chunk_id="s", chunk_text="sibling", chunk_index=0)]
    searcher, _ = _searcher_with_fetch({("D", ("Doc", "§8")): siblings})

    result, _ = await aggregate_parent_sections(
        reranked_chunks=[anchor, passthrough_chunk],
        kb_id="drive_user_manuals",
        searcher=searcher,
        parent_doc_top_k=1,  # only anchor gets parent expansion
    )

    assert len(result) == 2
    # Anchor: parent_section_text overrides
    assert result[0].parent_section_text == "sibling"
    # Passthrough: expanded_text preserved in fields (prompt_builder dispatch chain
    # parent_section_text > expanded_text > chunk_text — falls through to expanded_text)
    assert result[1].parent_section_text is None
    assert result[1].fields["expanded_text"] == "prev other\n\nother text\n\nnext other"


# ---------------------------------------------------------------------------
# F2.13k — Citation invariant (anchor chunk_id + chunk_text preserved)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_citation_invariant_anchor_chunk_id_and_text_preserved() -> None:
    """LLM sees parent_section_text but Citation rendering uses anchor's chunk_id + chunk_text."""
    anchor = _make_chunk(
        chunk_id="anchor-citation-id",
        doc_id="D",
        section_path=["Doc", "§8", "Scenario A"],
        chunk_text="Original anchor text — this is what Citation.chunk_text renders",
        chunk_index=44,
    )
    siblings = [
        _make_sibling_hit(chunk_id="sib-1", chunk_text="sibling content one"),
        _make_sibling_hit(chunk_id="sib-2", chunk_text="sibling content two"),
    ]
    searcher, _ = _searcher_with_fetch({("D", ("Doc", "§8")): siblings})

    result, _ = await aggregate_parent_sections(
        reranked_chunks=[anchor],
        kb_id="drive_user_manuals",
        searcher=searcher,
    )

    # Anchor's chunk_id + chunk_text preserved in fields (Citation rendering source)
    assert result[0].fields["chunk_id"] == "anchor-citation-id"
    assert (
        result[0].fields["chunk_text"]
        == "Original anchor text — this is what Citation.chunk_text renders"
    )
    # New parent_section_text added for prompt_builder dispatch chain
    assert (
        result[0].fields["parent_section_text"]
        == "sibling content one\n\nsibling content two"
    )


# ---------------------------------------------------------------------------
# Additional — missing doc_id / missing section_path
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_missing_doc_id_passes_through_with_skipped_count() -> None:
    """Anchor with empty doc_id → skipped + no fetch + pass through unchanged."""
    anchor = _make_chunk(
        chunk_id="c-anchor",
        doc_id="",
        section_path=["Doc", "§8", "Scenario A"],
        chunk_text="anchor",
    )
    searcher, fetch_mock = _searcher_with_fetch({})

    result, stats = await aggregate_parent_sections(
        reranked_chunks=[anchor],
        kb_id="drive_user_manuals",
        searcher=searcher,
    )

    fetch_mock.assert_not_awaited()
    assert result[0].parent_section_text is None
    assert result[0].fields["chunk_id"] == "c-anchor"
    assert stats.skipped_shallow_count == 1


@pytest.mark.asyncio
async def test_missing_section_path_passes_through_with_skipped_count() -> None:
    """Anchor with empty section_path → skipped + no fetch."""
    anchor = _make_chunk(
        chunk_id="c-anchor",
        doc_id="D",
        section_path=[],
        chunk_text="anchor",
    )
    searcher, fetch_mock = _searcher_with_fetch({})

    result, stats = await aggregate_parent_sections(
        reranked_chunks=[anchor],
        kb_id="drive_user_manuals",
        searcher=searcher,
    )

    fetch_mock.assert_not_awaited()
    assert stats.skipped_shallow_count == 1
    assert result[0].parent_section_text is None


# ---------------------------------------------------------------------------
# ParentSectionChunk.no_aggregation classmethod
# ---------------------------------------------------------------------------


def test_no_aggregation_classmethod_wraps_chunk_without_expansion() -> None:
    """Standalone helper for flag-off / passthrough paths."""
    source = _make_chunk(
        chunk_id="x",
        doc_id="y",
        section_path=["a", "b"],
        chunk_text="text",
        score=0.85,
    )
    wrapped = ParentSectionChunk.no_aggregation(source)
    assert wrapped.score == pytest.approx(0.85)
    assert wrapped.fields["chunk_id"] == "x"
    assert wrapped.parent_section_text is None
    assert wrapped.parent_path is None
    assert wrapped.sibling_count == 0
    assert wrapped.truncated is False


# W70 / ADR-0055 - marked-variant sibling assembly (use_marked threading)


@pytest.mark.asyncio
async def test_w70_use_marked_assembles_parent_section_from_marked_siblings() -> None:
    """use_marked=True - parent_section_text concatenates each sibling marked
    variant, falling back per sibling to clean text when the field is absent."""
    anchor = _make_chunk(
        chunk_id="kb-x_doc-A_chunk-0010",
        doc_id="A",
        section_path=["Doc", "Ch8", "8.1"],
        chunk_text="anchor text",
    )
    siblings = [
        _Chunk(
            score=1.0,
            fields={
                "chunk_id": "kb-x_doc-A_chunk-0010",
                "chunk_text": "sib one clean",
                "chunk_text_marked": "sib one marked [IMG#aaaa1111]",
                "chunk_index": 10,
            },
        ),
        _Chunk(  # no marked field -> clean fallback
            score=1.0,
            fields={
                "chunk_id": "kb-x_doc-A_chunk-0011",
                "chunk_text": "sib two clean",
                "chunk_index": 11,
            },
        ),
    ]
    searcher, _ = _searcher_with_fetch({("A", ("Doc", "Ch8")): siblings})

    result, stats = await aggregate_parent_sections(
        [anchor],
        kb_id="x",
        searcher=searcher,
        use_marked=True,
    )

    assert result[0].parent_section_text == ("sib one marked [IMG#aaaa1111]\n\nsib two clean")
    assert stats.siblings_aggregated == 2


@pytest.mark.asyncio
async def test_w70_use_marked_false_keeps_clean_sibling_assembly() -> None:
    """Default use_marked=False - clean text even when marked fields exist (G3)."""
    anchor = _make_chunk(
        chunk_id="kb-x_doc-A_chunk-0010",
        doc_id="A",
        section_path=["Doc", "Ch8", "8.1"],
        chunk_text="anchor text",
    )
    siblings = [
        _Chunk(
            score=1.0,
            fields={
                "chunk_id": "kb-x_doc-A_chunk-0010",
                "chunk_text": "sib one clean",
                "chunk_text_marked": "sib one marked [IMG#aaaa1111]",
                "chunk_index": 10,
            },
        ),
    ]
    searcher, _ = _searcher_with_fetch({("A", ("Doc", "Ch8")): siblings})

    result, _ = await aggregate_parent_sections([anchor], kb_id="x", searcher=searcher)

    assert result[0].parent_section_text == "sib one clean"
    assert "[IMG#" not in (result[0].parent_section_text or "")
