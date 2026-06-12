"""Context Expander unit tests (ADR-0020 W16+ Phase 3 P0.3; per CLAUDE.md §5.6 H6).

Per ADR-0020 closure of audit-W15-d5-vs-spec.md §1.5 C05 Major drift #3 + §CC-3:
- prev_chunk_id + next_chunk_id populated in ChunkRecord (orchestrator + index) but
  never consumed pre-W16. Phase 3 deliver wires Context Expander step per §3.1.

Test coverage:
- expand_context: happy path (mid-doc chunk with both prev + next available)
- Edge cases: first chunk (no prev) / last chunk (no next) / cross-doc boundary /
  lookup miss / empty top-K / fetch error graceful degradation
- ExpandedChunk: no_expansion classmethod for feature-flag-disabled / fallback
- ExpansionStats: requested_count / expanded_count / boundary_skip_count tracking
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from generation.context_expander import (
    ExpandedChunk,
    ExpansionStats,
    expand_context,
)
from retrieval.retrieval_engine import RetrievedChunk


def _chunk(
    chunk_id: str,
    text: str = "",
    prev_id: str | None = None,
    next_id: str | None = None,
    score: float = 0.9,
) -> RetrievedChunk:
    """Test helper: construct RetrievedChunk with chunk_id format kb-X_doc-Y_chunk-NNNN."""
    return RetrievedChunk(
        score=score,
        fields={
            "chunk_id": chunk_id,
            "chunk_text": text,
            "prev_chunk_id": prev_id,
            "next_chunk_id": next_id,
        },
    )


# ExpandedChunk.no_expansion


def test_expanded_chunk_no_expansion_preserves_original_fields() -> None:
    """ADR-0020: no_expansion classmethod produces ExpandedChunk that prompt_builder treats
    as raw chunk (no expanded_text key in fields → falls back to chunk_text)."""
    rc = _chunk("kb-x_doc-A_chunk-0001", text="hello")
    expanded = ExpandedChunk.no_expansion(rc)

    assert expanded.score == 0.9
    assert expanded.fields == rc.fields
    assert "expanded_text" not in expanded.fields
    assert expanded.prev_chunk_text is None
    assert expanded.next_chunk_text is None
    assert expanded.expansion_applied is False


# expand_context: happy path


@pytest.mark.asyncio
async def test_expand_context_mid_doc_chunk_merges_prev_and_next() -> None:
    """ADR-0020 happy path: mid-doc chunk with prev_chunk_id + next_chunk_id from same doc
    receives expanded_text = prev + original + next."""
    chunks = [_chunk(
        "kb-x_doc-A_chunk-0042",
        text="Step 3: Click Confirm to post.",
        prev_id="kb-x_doc-A_chunk-0041",
        next_id="kb-x_doc-A_chunk-0043",
    )]

    searcher = MagicMock()
    searcher.fetch_by_chunk_ids = AsyncMock(return_value={
        "kb-x_doc-A_chunk-0041": {"chunk_text": "Step 2: Verify customer credit."},
        "kb-x_doc-A_chunk-0043": {"chunk_text": "Step 4: Inspect inventory if posting fails."},
    })

    expanded, stats = await expand_context(chunks, kb_id="x", searcher=searcher)

    assert len(expanded) == 1
    e = expanded[0]
    assert e.expansion_applied is True
    assert e.prev_chunk_text == "Step 2: Verify customer credit."
    assert e.next_chunk_text == "Step 4: Inspect inventory if posting fails."
    # expanded_text composed in order prev → original → next
    assert e.fields["expanded_text"] == (
        "Step 2: Verify customer credit.\n\n"
        "Step 3: Click Confirm to post.\n\n"
        "Step 4: Inspect inventory if posting fails."
    )
    assert stats.requested_count == 1
    assert stats.expanded_count == 1
    assert stats.boundary_skip_count == 0


@pytest.mark.asyncio
async def test_expand_context_first_chunk_no_prev_only_next_merged() -> None:
    """Edge case: first chunk in document (prev_chunk_id None) → only next merged."""
    chunks = [_chunk(
        "kb-x_doc-A_chunk-0000",
        text="Introduction.",
        prev_id=None,
        next_id="kb-x_doc-A_chunk-0001",
    )]

    searcher = MagicMock()
    searcher.fetch_by_chunk_ids = AsyncMock(return_value={
        "kb-x_doc-A_chunk-0001": {"chunk_text": "First section content."},
    })

    expanded, stats = await expand_context(chunks, kb_id="x", searcher=searcher)

    e = expanded[0]
    assert e.expansion_applied is True
    assert e.prev_chunk_text is None
    assert e.next_chunk_text == "First section content."
    assert e.fields["expanded_text"] == "Introduction.\n\nFirst section content."
    assert stats.expanded_count == 1
    assert stats.boundary_skip_count == 1  # first chunk had no prev


@pytest.mark.asyncio
async def test_expand_context_last_chunk_no_next_only_prev_merged() -> None:
    """Edge case: last chunk in document (next_chunk_id None) → only prev merged."""
    chunks = [_chunk(
        "kb-x_doc-A_chunk-9999",
        text="Conclusion.",
        prev_id="kb-x_doc-A_chunk-9998",
        next_id=None,
    )]

    searcher = MagicMock()
    searcher.fetch_by_chunk_ids = AsyncMock(return_value={
        "kb-x_doc-A_chunk-9998": {"chunk_text": "Final section content."},
    })

    expanded, stats = await expand_context(chunks, kb_id="x", searcher=searcher)

    e = expanded[0]
    assert e.expansion_applied is True
    assert e.prev_chunk_text == "Final section content."
    assert e.next_chunk_text is None
    assert e.fields["expanded_text"] == "Final section content.\n\nConclusion."
    assert stats.boundary_skip_count == 1  # last chunk had no next


@pytest.mark.asyncio
async def test_expand_context_cross_doc_boundary_skipped() -> None:
    """Edge case: prev/next chunk_id has different doc → cross-doc boundary skipped."""
    chunks = [_chunk(
        "kb-x_doc-A_chunk-0042",
        text="Mid doc A chunk.",
        prev_id="kb-x_doc-B_chunk-0099",  # cross-doc — should skip
        next_id="kb-x_doc-A_chunk-0043",  # same doc — should merge
    )]

    searcher = MagicMock()
    # Searcher should NOT be asked for cross-doc neighbor; only same-doc next
    searcher.fetch_by_chunk_ids = AsyncMock(return_value={
        "kb-x_doc-A_chunk-0043": {"chunk_text": "Next section in doc A."},
    })

    expanded, stats = await expand_context(chunks, kb_id="x", searcher=searcher)

    e = expanded[0]
    assert e.expansion_applied is True
    assert e.prev_chunk_text is None  # cross-doc skipped
    assert e.next_chunk_text == "Next section in doc A."
    # fetch_by_chunk_ids was called with only the same-doc next id
    call_args = searcher.fetch_by_chunk_ids.await_args.args[0]
    assert "kb-x_doc-A_chunk-0043" in call_args
    assert "kb-x_doc-B_chunk-0099" not in call_args


@pytest.mark.asyncio
async def test_expand_context_lookup_miss_returns_no_expansion() -> None:
    """Edge case: prev/next chunk_id requested but not in index → no expansion applied."""
    chunks = [_chunk(
        "kb-x_doc-A_chunk-0042",
        text="Original.",
        prev_id="kb-x_doc-A_chunk-orphan",
        next_id="kb-x_doc-A_chunk-orphan2",
    )]

    searcher = MagicMock()
    searcher.fetch_by_chunk_ids = AsyncMock(return_value={})  # both lookups miss

    expanded, stats = await expand_context(chunks, kb_id="x", searcher=searcher)

    e = expanded[0]
    assert e.expansion_applied is False
    assert e.prev_chunk_text is None
    assert e.next_chunk_text is None
    assert "expanded_text" not in e.fields  # falls back to chunk_text in prompt_builder
    assert stats.expanded_count == 0


@pytest.mark.asyncio
async def test_expand_context_empty_top_k_no_api_call() -> None:
    """Cost guard: empty top-K → no fetch call, return empty list + zero stats."""
    searcher = MagicMock()
    searcher.fetch_by_chunk_ids = AsyncMock()

    expanded, stats = await expand_context([], kb_id="x", searcher=searcher)

    assert expanded == []
    assert stats.requested_count == 0
    assert stats.expanded_count == 0
    searcher.fetch_by_chunk_ids.assert_not_called()


@pytest.mark.asyncio
async def test_expand_context_fetch_failure_graceful_degradation() -> None:
    """ADR-0020 graceful degradation: searcher fetch raises → all chunks return no_expansion."""
    chunks = [_chunk(
        "kb-x_doc-A_chunk-0042",
        text="Original.",
        prev_id="kb-x_doc-A_chunk-0041",
        next_id="kb-x_doc-A_chunk-0043",
    )]

    searcher = MagicMock()
    searcher.fetch_by_chunk_ids = AsyncMock(side_effect=ConnectionError("network down"))

    expanded, stats = await expand_context(chunks, kb_id="x", searcher=searcher)

    # No exception propagated; all chunks degrade to no_expansion
    e = expanded[0]
    assert e.expansion_applied is False
    assert e.prev_chunk_text is None
    assert e.next_chunk_text is None
    assert stats.expanded_count == 0


@pytest.mark.asyncio
async def test_expand_context_batches_neighbors_in_single_call() -> None:
    """ADR-0020 perf: K chunks * 2 neighbors = 1 batch call (not 2K calls)."""
    chunks = [
        _chunk(f"kb-x_doc-A_chunk-{i:04d}",
               text=f"chunk {i}",
               prev_id=f"kb-x_doc-A_chunk-{i - 1:04d}",
               next_id=f"kb-x_doc-A_chunk-{i + 1:04d}")
        for i in range(1, 6)  # 5 mid-doc chunks
    ]

    searcher = MagicMock()
    searcher.fetch_by_chunk_ids = AsyncMock(return_value={})

    await expand_context(chunks, kb_id="x", searcher=searcher)

    # Must be called exactly once with 6 unique neighbor ids (chunks 0..6 minus chunks 1..5,
    # plus dedup overlap — 6 distinct neighbors total)
    assert searcher.fetch_by_chunk_ids.await_count == 1
    requested = searcher.fetch_by_chunk_ids.await_args.args[0]
    assert isinstance(requested, list)


@pytest.mark.asyncio
async def test_expand_context_propagates_kb_id_to_searcher() -> None:
    """ADR-0018 cross-ref: kb_id must be forwarded to searcher.fetch_by_chunk_ids."""
    chunks = [_chunk(
        "kb-x_doc-A_chunk-0042",
        prev_id="kb-x_doc-A_chunk-0041",
        next_id=None,
    )]

    searcher = MagicMock()
    searcher.fetch_by_chunk_ids = AsyncMock(return_value={})

    await expand_context(chunks, kb_id="finance_dept", searcher=searcher)

    assert searcher.fetch_by_chunk_ids.await_args.kwargs["kb_id"] == "finance_dept"


@pytest.mark.asyncio
async def test_expand_context_stats_latency_recorded() -> None:
    """ExpansionStats.fetch_latency_ms tracked for V6 Debug View per ADR-0020 observability."""
    chunks = [_chunk(
        "kb-x_doc-A_chunk-0042",
        prev_id="kb-x_doc-A_chunk-0041",
        next_id=None,
    )]

    searcher = MagicMock()
    searcher.fetch_by_chunk_ids = AsyncMock(return_value={
        "kb-x_doc-A_chunk-0041": {"chunk_text": "prev"},
    })

    _expanded, stats = await expand_context(chunks, kb_id="x", searcher=searcher)

    assert isinstance(stats, ExpansionStats)
    assert stats.fetch_latency_ms >= 0  # non-negative


# W70 / ADR-0055 - marked-variant assembly (use_marked threading)


@pytest.mark.asyncio
async def test_w70_use_marked_assembles_expanded_text_from_marked_variants() -> None:
    """use_marked=True - expanded_text built from chunk_text_marked (anchor +
    neighbours), falling back per chunk to clean text when the marked field is
    empty/absent. fields["chunk_text"] stays clean (citation invariant)."""
    chunks = [
        RetrievedChunk(
            score=0.9,
            fields={
                "chunk_id": "kb-x_doc-A_chunk-0042",
                "chunk_text": "Step 3 clean.",
                "chunk_text_marked": "Step 3 marked. [IMG#aaaa1111]",
                "prev_chunk_id": "kb-x_doc-A_chunk-0041",
                "next_chunk_id": "kb-x_doc-A_chunk-0043",
            },
        ),
    ]
    searcher = MagicMock()
    searcher.fetch_by_chunk_ids = AsyncMock(
        return_value={
            "kb-x_doc-A_chunk-0041": {
                "chunk_text": "Step 2 clean.",
                "chunk_text_marked": "Step 2 marked. [IMG#bbbb2222]",
            },
            # next neighbour has NO marked field -> falls back to clean text
            "kb-x_doc-A_chunk-0043": {"chunk_text": "Step 4 clean."},
        }
    )

    expanded, _ = await expand_context(
        chunks,
        kb_id="x",
        searcher=searcher,
        use_marked=True,
    )

    assert expanded[0].fields["expanded_text"] == (
        "Step 2 marked. [IMG#bbbb2222]\n\nStep 3 marked. [IMG#aaaa1111]\n\nStep 4 clean."
    )
    assert expanded[0].fields["chunk_text"] == "Step 3 clean."  # citation invariant


@pytest.mark.asyncio
async def test_w70_use_marked_false_keeps_pre_w70_clean_assembly() -> None:
    """Default use_marked=False - expanded_text built from clean text even when
    marked fields are present (G3 zero-regression)."""
    chunks = [
        RetrievedChunk(
            score=0.9,
            fields={
                "chunk_id": "kb-x_doc-A_chunk-0042",
                "chunk_text": "Step 3 clean.",
                "chunk_text_marked": "Step 3 marked. [IMG#aaaa1111]",
                "prev_chunk_id": "kb-x_doc-A_chunk-0041",
                "next_chunk_id": None,
            },
        ),
    ]
    searcher = MagicMock()
    searcher.fetch_by_chunk_ids = AsyncMock(
        return_value={
            "kb-x_doc-A_chunk-0041": {
                "chunk_text": "Step 2 clean.",
                "chunk_text_marked": "Step 2 marked. [IMG#bbbb2222]",
            },
        }
    )

    expanded, _ = await expand_context(chunks, kb_id="x", searcher=searcher)

    assert expanded[0].fields["expanded_text"] == "Step 2 clean.\n\nStep 3 clean."
    assert "[IMG#" not in expanded[0].fields["expanded_text"]
