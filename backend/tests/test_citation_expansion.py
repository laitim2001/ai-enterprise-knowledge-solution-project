"""Engine-fetch citation expansion tests (W32 F1.2.d; CLAUDE.md §5.6 H6).

Per W32 plan §1 single-axis ship per W31 multi-axis trap lesson — (h') ONLY,
no concurrent prompt change。Mirror W25 F5 D1 `test_citation_image_neighbors.py`
async testing pattern with mocked `engine.list_chunks`。

Coverage:
- expand_citations(disabled flag) → returns inputs unchanged
- expand_citations(empty citation_ids OR empty chunks) → returns inputs unchanged
- happy path:cited intro + 2 §X.M doc-neighbors via mocked list_chunks
- corpus bare X.M pattern(no §-prefix)
- §-prefix backward compat(both bare AND §-prefix match `\\b\\d+\\.\\d+\\b`)
- window boundary inclusive/exclusive
- max_aux cap
- closer neighbor preferred over further within max_aux cap
- dedupe against existing citation_ids
- same doc constraint(cited from doc-A,fetched chunks doc-A only)
- multiple cited chunks from different docs each expanded independently
- cited chunk not in `chunks` list defensive skip(LLM hallucinated chunk_id)
- per-doc fetch exception graceful degradation(other docs continue)
- `_find_neighbour_chunks` pure unit(no engine,no async)
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from generation.citation_expansion import (
    _extract_citation_ids,
    _find_neighbour_chunks,
    expand_citations,
)
from retrieval.retrieval_engine import RetrievedChunk
from storage.settings import Settings

# ---------- helpers ----------------------------------------------------------


def _chunk(
    chunk_id: str,
    *,
    doc_id: str = "doc-A",
    chunk_index: int = 0,
    chunk_title: str = "",
) -> RetrievedChunk:
    return RetrievedChunk(
        score=0.5,
        fields={
            "chunk_id": chunk_id,
            "doc_id": doc_id,
            "chunk_index": chunk_index,
            "chunk_title": chunk_title,
        },
    )


def _doc_chunk(
    chunk_id: str,
    chunk_index: int,
    chunk_title: str,
) -> dict:
    """Build a dict matching `engine.list_chunks` return shape (raw Azure Search row)."""
    return {
        "chunk_id": chunk_id,
        "chunk_index": chunk_index,
        "chunk_title": chunk_title,
        "section_path": [],
        "enabled": True,
    }


def _settings(
    *,
    enabled: bool = True,
    window: int = 10,
    max_aux: int = 2,
) -> Settings:
    s = Settings()
    s.enable_citation_post_hoc_expansion = enabled
    s.citation_expansion_window = window
    s.citation_expansion_max_aux = max_aux
    return s


def _mock_engine(list_chunks_return=None, list_chunks_side_effect=None):
    """Build mock engine with `list_chunks` async method."""
    engine = AsyncMock()
    if list_chunks_side_effect is not None:
        engine.list_chunks = AsyncMock(side_effect=list_chunks_side_effect)
    else:
        engine.list_chunks = AsyncMock(return_value=list_chunks_return or [])
    return engine


# ---------- _extract_citation_ids unit tests --------------------------------


def test_extract_citation_ids_empty_text() -> None:
    assert _extract_citation_ids("") == []


def test_extract_citation_ids_ordered_unique() -> None:
    text = "First [chunk-A]. Second [chunk-B]. Third [chunk-A] (dup). Fourth [chunk-C]."
    assert _extract_citation_ids(text) == ["A", "B", "C"]


# ---------- _find_neighbour_chunks pure unit (no IO, no async) --------------


def test_find_neighbour_chunks_happy_path_corpus_bare_x_m_pattern() -> None:
    """Corpus uses bare「8.4 Scenario D」not「§8.4」(W31 F2 v2 evidence per PC-W31-1)。"""
    doc_chunks = [
        _doc_chunk("0044", 44, "8. Integration scenarios (intro)"),
        _doc_chunk("0046", 46, "8.1 Scenario A walkthrough"),
        _doc_chunk("0048", 48, "8.2 Scenario B walkthrough"),
        _doc_chunk("0051", 51, "8.4 Scenario D walkthrough"),
    ]
    result = _find_neighbour_chunks(
        cited_chunk_index=44,
        cited_doc_id="doc-A",
        doc_chunks=doc_chunks,
        already_cited={"0044"},
        window=10,
        max_aux=2,
    )
    # Distance 2 (0046) + Distance 4 (0048) closer than Distance 7 (0051)
    assert result == ["0046", "0048"]


def test_find_neighbour_chunks_section_prefix_also_matches() -> None:
    """§X.M still matches `\\b\\d+\\.\\d+\\b` pattern (covers both bare + §-prefix)。"""
    doc_chunks = [
        _doc_chunk("0046", 46, "§8.1 Scenario A walkthrough"),
        _doc_chunk("0048", 48, "§8.2 Scenario B walkthrough"),
    ]
    result = _find_neighbour_chunks(
        cited_chunk_index=44,
        cited_doc_id="doc-A",
        doc_chunks=doc_chunks,
        already_cited={"0044"},
        window=10,
        max_aux=2,
    )
    assert result == ["0046", "0048"]


def test_find_neighbour_chunks_section_pattern_filter_excludes_intro_or_overview() -> None:
    """「8. Integration scenarios」(no second-level digit) MUST be excluded。"""
    doc_chunks = [
        _doc_chunk("0044", 44, "8. Integration scenarios (intro)"),
        _doc_chunk("0046", 46, "8.1 Walkthrough"),
        _doc_chunk("0050", 50, "Overview of platform"),  # no numbering
    ]
    result = _find_neighbour_chunks(
        cited_chunk_index=44,
        cited_doc_id="doc-A",
        doc_chunks=doc_chunks,
        already_cited={"0044"},
        window=10,
        max_aux=5,
    )
    assert result == ["0046"]  # Only valid X.M pattern with chunks distance 2


def test_find_neighbour_chunks_window_boundary_inclusive() -> None:
    doc_chunks = [
        _doc_chunk("0047", 47, "8.1 Edge"),  # distance 3 = window=3 edge inclusive
        _doc_chunk("0048", 48, "8.2 Past"),  # distance 4 > window=3 exclusive
    ]
    result = _find_neighbour_chunks(
        cited_chunk_index=44,
        cited_doc_id="doc-A",
        doc_chunks=doc_chunks,
        already_cited={"0044"},
        window=3,
        max_aux=5,
    )
    assert result == ["0047"]


def test_find_neighbour_chunks_max_aux_cap_closer_preferred() -> None:
    doc_chunks = [
        _doc_chunk("0046", 46, "8.1 Close"),  # distance 2
        _doc_chunk("0050", 50, "8.3 Far"),  # distance 6
        _doc_chunk("0048", 48, "8.2 Mid"),  # distance 4
    ]
    result = _find_neighbour_chunks(
        cited_chunk_index=44,
        cited_doc_id="doc-A",
        doc_chunks=doc_chunks,
        already_cited={"0044"},
        window=10,
        max_aux=2,
    )
    assert result == ["0046", "0048"]


def test_find_neighbour_chunks_dedupe_skips_already_cited() -> None:
    doc_chunks = [
        _doc_chunk("0046", 46, "8.1 Already cited"),
        _doc_chunk("0048", 48, "8.2 Not cited"),
    ]
    result = _find_neighbour_chunks(
        cited_chunk_index=44,
        cited_doc_id="doc-A",
        doc_chunks=doc_chunks,
        already_cited={"0044", "0046"},  # 0046 already cited
        window=10,
        max_aux=5,
    )
    assert result == ["0048"]


def test_find_neighbour_chunks_distance_0_excluded_self() -> None:
    doc_chunks = [
        _doc_chunk("0044b", 44, "8. Same idx self"),  # distance 0 → excluded
        _doc_chunk("0046", 46, "8.1 Distance 2"),
    ]
    result = _find_neighbour_chunks(
        cited_chunk_index=44,
        cited_doc_id="doc-A",
        doc_chunks=doc_chunks,
        already_cited={"0044"},
        window=10,
        max_aux=5,
    )
    assert result == ["0046"]


def test_find_neighbour_chunks_zero_window_or_max_aux_returns_empty() -> None:
    doc_chunks = [_doc_chunk("0046", 46, "8.1 Walkthrough")]
    assert _find_neighbour_chunks(
        cited_chunk_index=44, cited_doc_id="doc-A", doc_chunks=doc_chunks,
        already_cited={"0044"}, window=0, max_aux=5,
    ) == []
    assert _find_neighbour_chunks(
        cited_chunk_index=44, cited_doc_id="doc-A", doc_chunks=doc_chunks,
        already_cited={"0044"}, window=10, max_aux=0,
    ) == []


# ---------- expand_citations async behavior tests ---------------------------


@pytest.mark.asyncio
async def test_disabled_flag_returns_inputs_unchanged() -> None:
    settings = _settings(enabled=False)
    answer = "Intro [chunk-0044]. More content."
    citation_ids = ["0044"]
    chunks = [_chunk("0044", chunk_index=44, chunk_title="8. Integration")]
    engine = _mock_engine(list_chunks_return=[_doc_chunk("0046", 46, "8.1 Walk")])
    expanded_text, expanded_ids = await expand_citations(
        answer, citation_ids, chunks, engine=engine, kb_id="kb1", settings=settings,
    )
    assert expanded_text == answer
    assert expanded_ids == citation_ids
    # When disabled, engine.list_chunks should NOT be called (short-circuit before fetch)
    engine.list_chunks.assert_not_called()


@pytest.mark.asyncio
async def test_empty_citation_ids_returns_inputs_unchanged() -> None:
    settings = _settings()
    chunks = [_chunk("0051", chunk_index=51, chunk_title="8.4 Walk")]
    engine = _mock_engine()
    text, ids = await expand_citations(
        "text only", [], chunks, engine=engine, kb_id="kb1", settings=settings,
    )
    assert text == "text only"
    assert ids == []
    engine.list_chunks.assert_not_called()


@pytest.mark.asyncio
async def test_empty_chunks_returns_inputs_unchanged() -> None:
    settings = _settings()
    engine = _mock_engine()
    text, ids = await expand_citations(
        "Intro [chunk-0044].", ["0044"], [], engine=engine, kb_id="kb1", settings=settings,
    )
    assert text == "Intro [chunk-0044]."
    assert ids == ["0044"]
    engine.list_chunks.assert_not_called()


@pytest.mark.asyncio
async def test_happy_path_engine_fetch_finds_section_neighbors() -> None:
    """W32 (h') primary scenario — top-5 reranked chunks不含 §X.M walkthroughs,
    but engine.list_chunks fetches full doc which DOES contain §X.M neighbors。"""
    settings = _settings(window=10, max_aux=2)
    answer = "Integration scenarios [chunk-0044]. End."
    # top-K reranked subset: only intro chunk (NO walkthroughs surfaced — W31 v2/v3 pattern)
    chunks = [_chunk("0044", chunk_index=44, chunk_title="8. Integration scenarios")]
    # Full doc chunks (via engine.list_chunks) DOES contain §X.M walkthroughs
    full_doc_chunks = [
        _doc_chunk("0044", 44, "8. Integration scenarios"),
        _doc_chunk("0046", 46, "8.1 Scenario A walkthrough"),
        _doc_chunk("0048", 48, "8.2 Scenario B walkthrough"),
        _doc_chunk("0051", 51, "8.4 Scenario D walkthrough"),
    ]
    engine = _mock_engine(list_chunks_return=full_doc_chunks)

    expanded_text, expanded_ids = await expand_citations(
        answer, ["0044"], chunks, engine=engine, kb_id="kb1", settings=settings,
    )
    # Closer 2 walkthrough neighbors by distance (0046 dist 2 + 0048 dist 4) inserted
    assert "[chunk-0044][chunk-0046][chunk-0048]" in expanded_text
    assert expanded_ids == ["0044", "0046", "0048"]
    engine.list_chunks.assert_called_once_with("kb1", "doc-A")


@pytest.mark.asyncio
async def test_multiple_cited_chunks_from_different_docs_independent_expansion() -> None:
    """Each cited doc fetched + expanded independently (parallel asyncio.gather pattern)。"""
    settings = _settings(window=3, max_aux=1)
    answer = "Doc A topic [chunk-0010]. Doc B topic [chunk-0020]."
    chunks = [
        _chunk("0010", doc_id="doc-A", chunk_index=10, chunk_title="1. Doc A intro"),
        _chunk("0020", doc_id="doc-B", chunk_index=20, chunk_title="2. Doc B intro"),
    ]

    async def _list_chunks(kb_id: str, doc_id: str) -> list[dict]:
        if doc_id == "doc-A":
            return [_doc_chunk("0011", 11, "1.1 Doc A detail")]
        if doc_id == "doc-B":
            return [_doc_chunk("0021", 21, "2.1 Doc B detail")]
        return []

    engine = _mock_engine(list_chunks_side_effect=_list_chunks)

    expanded_text, expanded_ids = await expand_citations(
        answer, ["0010", "0020"], chunks, engine=engine, kb_id="kb1", settings=settings,
    )
    assert "[chunk-0010][chunk-0011]" in expanded_text
    assert "[chunk-0020][chunk-0021]" in expanded_text
    assert expanded_ids == ["0010", "0011", "0020", "0021"]
    # 2 calls to list_chunks (one per unique doc — sorted to (doc-A, doc-B))
    assert engine.list_chunks.call_count == 2


@pytest.mark.asyncio
async def test_cited_chunk_not_in_chunks_list_skip_silently() -> None:
    """LLM hallucinated chunk_id not in retrieved set (Rule 5 violation) → skip silently。"""
    settings = _settings()
    answer = "Hallucinated [chunk-9999]."
    chunks = [_chunk("0044", chunk_index=44, chunk_title="8.1 Walk")]
    engine = _mock_engine()

    expanded_text, expanded_ids = await expand_citations(
        answer, ["9999"], chunks, engine=engine, kb_id="kb1", settings=settings,
    )
    # No fetch attempted (cited_id not in chunks → no doc_id to fetch)
    assert expanded_text == answer
    assert expanded_ids == ["9999"]
    engine.list_chunks.assert_not_called()


@pytest.mark.asyncio
async def test_per_doc_fetch_exception_graceful_degradation() -> None:
    """One doc's list_chunks 500'd → that doc's expansion skipped,others continue。"""
    settings = _settings(window=3, max_aux=1)
    answer = "[chunk-0010] and [chunk-0020]."
    chunks = [
        _chunk("0010", doc_id="doc-A", chunk_index=10, chunk_title="1. A intro"),
        _chunk("0020", doc_id="doc-B", chunk_index=20, chunk_title="2. B intro"),
    ]

    async def _list_chunks(kb_id: str, doc_id: str) -> list[dict]:
        if doc_id == "doc-A":
            raise RuntimeError("Azure Search 500")
        if doc_id == "doc-B":
            return [_doc_chunk("0021", 21, "2.1 B detail")]
        return []

    engine = _mock_engine(list_chunks_side_effect=_list_chunks)

    expanded_text, expanded_ids = await expand_citations(
        answer, ["0010", "0020"], chunks, engine=engine, kb_id="kb1", settings=settings,
    )
    # doc-A's expansion skipped (fetch failed),doc-B's expansion succeeded
    assert "[chunk-0011]" not in expanded_text  # doc-A neighbor would have been 0011 but skipped
    assert "[chunk-0020][chunk-0021]" in expanded_text  # doc-B expansion succeeded
    assert expanded_ids == ["0010", "0020", "0021"]


@pytest.mark.asyncio
async def test_no_walkthrough_neighbors_in_doc_returns_unchanged() -> None:
    """When full doc has no §X.M chunks within window,answer unchanged。"""
    settings = _settings(window=10, max_aux=2)
    answer = "Intro [chunk-0044]."
    chunks = [_chunk("0044", chunk_index=44, chunk_title="8. Intro")]
    # Full doc has only chunks WITHOUT §X.M numbering
    full_doc_chunks = [
        _doc_chunk("0044", 44, "8. Intro"),
        _doc_chunk("0045", 45, "Overview (no numbering)"),
        _doc_chunk("0046", 46, "Notes"),
    ]
    engine = _mock_engine(list_chunks_return=full_doc_chunks)

    expanded_text, expanded_ids = await expand_citations(
        answer, ["0044"], chunks, engine=engine, kb_id="kb1", settings=settings,
    )
    assert expanded_text == answer
    assert expanded_ids == ["0044"]
