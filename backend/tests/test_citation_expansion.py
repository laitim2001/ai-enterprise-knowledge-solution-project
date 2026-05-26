"""Post-hoc citation expansion tests (W31 F1.2.d; CLAUDE.md §5.6 H6).

Coverage:
- expand_citations(disabled flag) → returns inputs unchanged
- expand_citations(empty citation_ids OR empty chunks) → returns inputs unchanged
- happy path: cited intro chunk + 2 §X.M neighbors → 2 expansions inserted after marker
- §X.M filter:neighbor without §X.M title pattern excluded
- score threshold:neighbor below threshold excluded
- window boundary:neighbor at exact ±window included;outside excluded
- same doc constraint:neighbor in different doc excluded
- max_aux cap:3 qualifying neighbors but max_aux=2 → only 2 added
- dedupe:neighbor already cited skipped
- cited chunk not in chunks list (defensive) → skip silently
- multiple cited chunks each expanded independently
- ordering preserved via sort-by-distance
- _extract_citation_ids returns ordered unique list
"""

from __future__ import annotations

from generation.citation_expansion import _extract_citation_ids, expand_citations
from retrieval.retrieval_engine import RetrievedChunk
from storage.settings import Settings

# ---------- helpers ----------------------------------------------------------


def _chunk(
    chunk_id: str,
    *,
    doc_id: str = "doc-A",
    chunk_index: int = 0,
    chunk_title: str = "",
    score: float = 0.9,
) -> RetrievedChunk:
    return RetrievedChunk(
        score=score,
        fields={
            "chunk_id": chunk_id,
            "doc_id": doc_id,
            "chunk_index": chunk_index,
            "chunk_title": chunk_title,
        },
    )


def _settings(
    *,
    enabled: bool = True,
    window: int = 3,
    score_threshold: float = 0.5,
    max_aux: int = 2,
) -> Settings:
    s = Settings()
    s.enable_citation_post_hoc_expansion = enabled
    s.citation_expansion_window = window
    s.citation_expansion_score_threshold = score_threshold
    s.citation_expansion_max_aux = max_aux
    return s


# ---------- _extract_citation_ids unit tests --------------------------------


def test_extract_citation_ids_empty_text() -> None:
    assert _extract_citation_ids("") == []


def test_extract_citation_ids_ordered_unique() -> None:
    text = "First [chunk-A]. Second [chunk-B]. Third [chunk-A] (dup). Fourth [chunk-C]."
    assert _extract_citation_ids(text) == ["A", "B", "C"]


# ---------- expand_citations behavior tests ---------------------------------


def test_disabled_flag_returns_inputs_unchanged() -> None:
    settings = _settings(enabled=False)
    answer = "Intro [chunk-0044]. More content."
    citation_ids = ["0044"]
    chunks = [
        _chunk("0044", chunk_index=44, chunk_title="§8 Integration scenarios"),
        _chunk("0051", chunk_index=51, chunk_title="§8.4 Scenario walkthrough"),
    ]
    expanded_text, expanded_ids = expand_citations(answer, citation_ids, chunks, settings=settings)
    assert expanded_text == answer
    assert expanded_ids == citation_ids


def test_empty_citation_ids_returns_inputs_unchanged() -> None:
    settings = _settings()
    chunks = [_chunk("0051", chunk_index=51, chunk_title="§8.4")]
    text, ids = expand_citations("text only", [], chunks, settings=settings)
    assert text == "text only"
    assert ids == []


def test_empty_chunks_returns_inputs_unchanged() -> None:
    settings = _settings()
    text, ids = expand_citations("Intro [chunk-0044].", ["0044"], [], settings=settings)
    assert text == "Intro [chunk-0044]."
    assert ids == ["0044"]


def test_happy_path_intro_chunk_expanded_with_2_section_neighbors() -> None:
    settings = _settings(window=10, score_threshold=0.5, max_aux=2)
    answer = "Integration scenarios are described [chunk-0044]. End."
    chunks = [
        _chunk("0044", chunk_index=44, chunk_title="§8 Integration scenarios"),
        _chunk("0046", chunk_index=46, chunk_title="§8.1 Scenario A walkthrough", score=0.85),
        _chunk("0048", chunk_index=48, chunk_title="§8.2 Scenario B walkthrough", score=0.78),
        _chunk("0050", chunk_index=50, chunk_title="§8.3 Scenario C walkthrough", score=0.72),
    ]
    expanded_text, expanded_ids = expand_citations(answer, ["0044"], chunks, settings=settings)
    # Closest 2 §X.M neighbors by chunk_index distance from 44 = 46 (dist 2) + 48 (dist 4)
    assert "[chunk-0044][chunk-0046][chunk-0048]" in expanded_text
    assert expanded_ids == ["0044", "0046", "0048"]
    # 3rd neighbor (50) excluded by max_aux=2 cap
    assert "[chunk-0050]" not in expanded_text


def test_section_pattern_filter_excludes_non_section_titles() -> None:
    settings = _settings(window=10, score_threshold=0.5)
    answer = "Intro [chunk-0044]."
    chunks = [
        _chunk("0044", chunk_index=44, chunk_title="§8 Integration scenarios"),
        # No §X.M numbering — should be excluded
        _chunk("0046", chunk_index=46, chunk_title="Overview of platform", score=0.85),
        _chunk("0048", chunk_index=48, chunk_title="Notes", score=0.78),
    ]
    expanded_text, expanded_ids = expand_citations(answer, ["0044"], chunks, settings=settings)
    assert expanded_text == answer
    assert expanded_ids == ["0044"]


def test_score_threshold_filter_excludes_low_score_neighbors() -> None:
    settings = _settings(window=10, score_threshold=0.7, max_aux=2)
    answer = "Intro [chunk-0044]."
    chunks = [
        _chunk("0044", chunk_index=44, chunk_title="§8 Integration"),
        _chunk("0046", chunk_index=46, chunk_title="§8.1 Walkthrough", score=0.65),  # below 0.7
        _chunk("0048", chunk_index=48, chunk_title="§8.2 Walkthrough", score=0.75),  # passes
    ]
    expanded_text, expanded_ids = expand_citations(answer, ["0044"], chunks, settings=settings)
    assert "[chunk-0046]" not in expanded_text
    assert "[chunk-0048]" in expanded_text


def test_window_boundary_inclusive() -> None:
    settings = _settings(window=3, score_threshold=0.5, max_aux=5)
    answer = "Intro [chunk-0044]."
    chunks = [
        _chunk("0044", chunk_index=44, chunk_title="§8 Intro"),
        _chunk("0047", chunk_index=47, chunk_title="§8.1 At window edge"),  # dist 3 = window edge,included
        _chunk("0048", chunk_index=48, chunk_title="§8.2 Past window"),  # dist 4 > window,excluded
    ]
    expanded_text, expanded_ids = expand_citations(answer, ["0044"], chunks, settings=settings)
    assert "[chunk-0047]" in expanded_text
    assert "[chunk-0048]" not in expanded_text


def test_same_doc_constraint_excludes_other_doc_neighbors() -> None:
    settings = _settings(window=10, score_threshold=0.5)
    answer = "Intro [chunk-0044]."
    chunks = [
        _chunk("0044", doc_id="doc-A", chunk_index=44, chunk_title="§8 Intro"),
        _chunk("0045", doc_id="doc-B", chunk_index=45, chunk_title="§8.1 Other doc"),
    ]
    expanded_text, expanded_ids = expand_citations(answer, ["0044"], chunks, settings=settings)
    assert "[chunk-0045]" not in expanded_text


def test_dedupe_skips_already_cited_chunks() -> None:
    settings = _settings(window=10, score_threshold=0.5, max_aux=2)
    answer = "Intro [chunk-0044]. Specific [chunk-0046]."
    citation_ids = ["0044", "0046"]
    chunks = [
        _chunk("0044", chunk_index=44, chunk_title="§8 Intro"),
        _chunk("0046", chunk_index=46, chunk_title="§8.1 Walkthrough"),  # already cited
        _chunk("0048", chunk_index=48, chunk_title="§8.2 Walkthrough"),  # not cited
    ]
    expanded_text, expanded_ids = expand_citations(answer, citation_ids, chunks, settings=settings)
    # 0046 already cited so excluded from 0044's expansion candidates;
    # 0048 should be added to 0044 (dist 4) — distance 4 in window 10
    assert "[chunk-0044][chunk-0048]" in expanded_text


def test_cited_chunk_not_in_chunks_list_skip_silently() -> None:
    settings = _settings(window=10, score_threshold=0.5)
    answer = "Hallucinated [chunk-9999]."  # LLM hallucinated chunk_id not in retrieved set
    chunks = [
        _chunk("0044", chunk_index=44, chunk_title="§8.1 Walkthrough"),
    ]
    expanded_text, expanded_ids = expand_citations(answer, ["9999"], chunks, settings=settings)
    # Should not crash;return inputs unchanged when no expandable cited chunk
    assert expanded_text == answer
    assert expanded_ids == ["9999"]


def test_multiple_cited_chunks_each_expanded_independently() -> None:
    settings = _settings(window=2, score_threshold=0.5, max_aux=1)
    answer = "First topic [chunk-0010]. Second topic [chunk-0020]."
    chunks = [
        _chunk("0010", chunk_index=10, chunk_title="§1 Intro"),
        _chunk("0011", chunk_index=11, chunk_title="§1.1 Detail"),
        _chunk("0020", chunk_index=20, chunk_title="§2 Intro"),
        _chunk("0021", chunk_index=21, chunk_title="§2.1 Detail"),
    ]
    expanded_text, expanded_ids = expand_citations(
        answer, ["0010", "0020"], chunks, settings=settings,
    )
    assert "[chunk-0010][chunk-0011]" in expanded_text
    assert "[chunk-0020][chunk-0021]" in expanded_text
    assert expanded_ids == ["0010", "0011", "0020", "0021"]


def test_closer_neighbor_preferred_over_further_under_max_aux_cap() -> None:
    settings = _settings(window=10, score_threshold=0.5, max_aux=1)
    answer = "Intro [chunk-0044]."
    chunks = [
        _chunk("0044", chunk_index=44, chunk_title="§8 Intro"),
        _chunk("0050", chunk_index=50, chunk_title="§8.3 Further walkthrough"),  # dist 6
        _chunk("0046", chunk_index=46, chunk_title="§8.1 Closer walkthrough"),  # dist 2 — should win
    ]
    expanded_text, expanded_ids = expand_citations(answer, ["0044"], chunks, settings=settings)
    # max_aux=1,closest by distance wins (0046 dist 2 < 0050 dist 6)
    assert "[chunk-0046]" in expanded_text
    assert "[chunk-0050]" not in expanded_text


def test_chunk_at_distance_0_excluded_self() -> None:
    settings = _settings(window=3, score_threshold=0.5, max_aux=2)
    answer = "Intro [chunk-0044]."
    chunks = [
        _chunk("0044", chunk_index=44, chunk_title="§8.4 Intro"),
        # Duplicate chunk_index — defensive (shouldn't happen but check)
        _chunk("0044b", chunk_index=44, chunk_title="§8.4 Duplicate"),
    ]
    expanded_text, expanded_ids = expand_citations(answer, ["0044"], chunks, settings=settings)
    # Same chunk_index treated as distance=0 self → excluded
    assert "[chunk-0044b]" not in expanded_text
