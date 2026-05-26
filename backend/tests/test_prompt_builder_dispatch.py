"""Prompt builder dispatch chain test per ADR-0037 W26 F2.

Verifies the chunk-text priority chain in `_format_chunk`:
    parent_section_text > expanded_text > chunk_text

Extends ADR-0020 Context Expander baseline (expanded_text > chunk_text) with the
ADR-0037 parent-document layer. Critical invariant — `prompt_builder.build_prompt`
must read the highest-priority key available so the LLM sees parent section
context when Parent-Document Retriever has aggregated siblings.
"""

from __future__ import annotations

from generation.prompt_builder import build_prompt
from retrieval.retrieval_engine import RetrievedChunk


def _chunk_with_fields(**overrides: object) -> RetrievedChunk:
    base: dict[str, object] = {
        "chunk_id": "kb-test_doc-A_chunk-0001",
        "chunk_title": "Test Title",
        "chunk_text": "raw chunk text fallback",
        "section_path": ["Doc", "§1"],
    }
    base.update(overrides)
    return RetrievedChunk(score=0.9, fields=base)


def test_dispatch_picks_chunk_text_when_no_expansion() -> None:
    """Baseline — neither parent_section_text nor expanded_text → use chunk_text."""
    chunk = _chunk_with_fields()
    msgs = build_prompt("test query", [chunk])
    user_msg = msgs.messages[1]["content"]
    assert "raw chunk text fallback" in user_msg


def test_dispatch_picks_expanded_text_over_chunk_text() -> None:
    """ADR-0020 — when Context Expander applied, expanded_text supersedes chunk_text."""
    chunk = _chunk_with_fields(expanded_text="prev\n\nraw chunk text\n\nnext")
    msgs = build_prompt("test query", [chunk])
    user_msg = msgs.messages[1]["content"]
    assert "prev\n\nraw chunk text\n\nnext" in user_msg
    assert "raw chunk text fallback" not in user_msg  # original NOT used


def test_dispatch_picks_parent_section_text_over_expanded_text() -> None:
    """ADR-0037 W26 F2 — parent_section_text supersedes expanded_text when both present."""
    chunk = _chunk_with_fields(
        expanded_text="prev\n\nraw chunk text\n\nnext",
        parent_section_text="Sibling 1\n\nSibling 2\n\nSibling 3\n\nSibling 4\n\nSibling 5",
    )
    msgs = build_prompt("test query", [chunk])
    user_msg = msgs.messages[1]["content"]
    assert "Sibling 1" in user_msg
    assert "Sibling 5" in user_msg
    assert "raw chunk text fallback" not in user_msg
    assert "prev\n\nraw chunk text\n\nnext" not in user_msg  # expanded NOT used


def test_dispatch_picks_parent_section_text_over_chunk_text_when_no_expanded() -> None:
    """ADR-0037 — parent_section_text supersedes chunk_text even when expanded_text absent."""
    chunk = _chunk_with_fields(
        parent_section_text="Parent section content with siblings A, B, C",
    )
    msgs = build_prompt("test query", [chunk])
    user_msg = msgs.messages[1]["content"]
    assert "Parent section content with siblings A, B, C" in user_msg
    assert "raw chunk text fallback" not in user_msg


def test_dispatch_chunk_id_preserved_for_citation_invariant() -> None:
    """Citation invariant — chunk_id reference remains anchor's id regardless of dispatch."""
    chunk = _chunk_with_fields(
        chunk_id="kb-test_doc-X_chunk-0042",
        parent_section_text="full parent section text replaces anchor's own text",
    )
    msgs = build_prompt("test query", [chunk])
    user_msg = msgs.messages[1]["content"]
    # The chunk-{id} marker uses anchor's chunk_id regardless of which text is displayed
    assert "[chunk-kb-test_doc-X_chunk-0042]" in user_msg


def test_dispatch_falls_back_to_chunk_text_when_parent_section_text_is_empty_string() -> None:
    """Falsy parent_section_text (empty string) → fall through to expanded_text / chunk_text."""
    chunk = _chunk_with_fields(
        parent_section_text="",
        expanded_text="expanded result",
    )
    msgs = build_prompt("test query", [chunk])
    user_msg = msgs.messages[1]["content"]
    assert "expanded result" in user_msg


def test_dispatch_handles_missing_parent_section_text_key() -> None:
    """Missing key (no parent_section_text at all) → identical to no-expansion baseline."""
    chunk = _chunk_with_fields(expanded_text="expanded only")
    msgs = build_prompt("test query", [chunk])
    user_msg = msgs.messages[1]["content"]
    assert "expanded only" in user_msg


# ─── W27 F1 — dispatch_mode enum branching tests per ADR-0037 amendment candidate ───
# R-W26-1 hypothesis test:append mode renders BOTH anchor chunk_text + parent
# section context (2 segments) instead of replace mode's top-priority-wins `or`
# chain — preserves citation invariant against RAGAs faithfulness judge mismatch.


def test_format_chunk_dispatch_replace_mode_preserves_w26_semantics() -> None:
    """W27 F1 — `dispatch_mode="replace"` explicit 同 backward-compat default 行為一致。

    Regression-guard against W26 F2 G existing 7 dispatch tests:replace branch
    必須 top-priority-wins (`parent_section_text > expanded_text > chunk_text`)。
    """
    chunk = _chunk_with_fields(
        expanded_text="expanded fallback",
        parent_section_text="parent section wins on replace",
    )
    msgs = build_prompt("test query", [chunk], dispatch_mode="replace")
    user_msg = msgs.messages[1]["content"]
    assert "parent section wins on replace" in user_msg
    assert "expanded fallback" not in user_msg  # replace branch — expanded NOT rendered
    assert "raw chunk text fallback" not in user_msg  # replace branch — chunk_text NOT rendered


def test_format_chunk_dispatch_append_mode_includes_both_segments() -> None:
    """W27 F1 — append mode render BOTH anchor chunk_text + parent section context。

    Core hypothesis test:LLM input contains anchor's raw chunk_text 主段 + delimiter
    + parent section context 段;preserves citation invariant against judge mismatch.
    """
    chunk = _chunk_with_fields(
        chunk_text="anchor chunk raw text here",
        parent_section_text="Sibling A\n\nSibling B\n\nSibling C",
    )
    msgs = build_prompt("test query", [chunk], dispatch_mode="append")
    user_msg = msgs.messages[1]["content"]
    # 主段 — anchor chunk_text raw
    assert "anchor chunk raw text here" in user_msg
    # delimiter — explicit "Parent section context:" sub-section
    assert "Parent section context:" in user_msg
    # parent section context segment
    assert "Sibling A" in user_msg
    assert "Sibling C" in user_msg


def test_format_chunk_dispatch_append_mode_no_parent_section_falls_back_to_replace_chain() -> None:
    """W27 F1 — append mode + 無 parent_section_text → 退回 replace chain (expanded > chunk)。

    Falsy parent_section_text → no 2-segment render;Test-deterministic equivalence
    with replace branch when parent-doc retriever returns empty (flag off OR no anchor)。
    """
    chunk = _chunk_with_fields(expanded_text="expanded result without parent")
    msgs = build_prompt("test query", [chunk], dispatch_mode="append")
    user_msg = msgs.messages[1]["content"]
    assert "expanded result without parent" in user_msg
    assert "Parent section context:" not in user_msg  # 無 parent → 無 delimiter


def test_format_chunk_dispatch_append_mode_citation_chunk_id_preserved() -> None:
    """W27 F1 — append mode citation invariant explicit verification。

    Per architecture.md §3.5 Citation contract:LLM cites anchor chunk_id 即使
    parent_section_text 已 render — append branch 唔改 citation surface。
    """
    chunk = _chunk_with_fields(
        chunk_id="kb-test_doc-X_chunk-0042",
        parent_section_text="full parent section text appended after anchor",
    )
    msgs = build_prompt("test query", [chunk], dispatch_mode="append")
    user_msg = msgs.messages[1]["content"]
    # Citation marker uses anchor's chunk_id regardless of dispatch mode
    assert "[chunk-kb-test_doc-X_chunk-0042]" in user_msg
    # Both segments rendered (sanity check)
    assert "raw chunk text fallback" in user_msg  # anchor chunk_text
    assert "full parent section text appended" in user_msg  # parent context


# ---------- W31 F1.5.a SYSTEM_PROMPT Rule 7 v2 + Rule 8 assertions ----------


def test_system_prompt_includes_rule_7_v2_section_numbering_pattern() -> None:
    """W31 F1.1.a — Rule 7 v2 wording target「§X.M numbering pattern」explicit。

    Replaces W30 Rule 7「specific subsection」abstract wording per Run 5 §8.6
    Coverage summary mis-interpretation evidence。Must include literal「§X.M」
    pattern + reference examples + intro chunk insufficiency framing。
    """
    from generation.prompt_builder import SYSTEM_PROMPT

    # §X.M numbering pattern explicit
    assert "§X.M" in SYSTEM_PROMPT
    # Reference examples present (§8.1 / §8.2 / §8.3 or similar)
    assert "§8.1" in SYSTEM_PROMPT
    # Prefer specific over overview framing
    assert "prefer citing" in SYSTEM_PROMPT.lower()
    assert "individually-numbered chunks" in SYSTEM_PROMPT
    # Intro chunk insufficiency framing
    assert "insufficient" in SYSTEM_PROMPT.lower()


def test_system_prompt_includes_rule_8_cite_all_overlap() -> None:
    """W31 F1.1.b — Rule 8 B'.b prompt instruction layer for cite-confidence threshold relax。

    Must include「cite ALL of them」directive + multi-chunk-partial-info framing。
    """
    from generation.prompt_builder import SYSTEM_PROMPT

    assert "cite ALL of them" in SYSTEM_PROMPT
    assert "not just the most representative" in SYSTEM_PROMPT
    # multi-chunk partial information framing
    assert "partial information" in SYSTEM_PROMPT
    # every chunk that supports
    assert "every chunk that supports" in SYSTEM_PROMPT


def test_system_prompt_rule_6_ch005_preserved_non_regression() -> None:
    """W31 F1.1.c non-regression — Rule 6 CH-005 R14 mitigation preserved unchanged。

    W30→W31 transition must NOT break CH-005 Rule 6 framing per W25.5 BUG-025 +
    W26 R14 mitigation context (overview / aggregate queries synthesize what IS
    available rather than refusing entirely)。
    """
    from generation.prompt_builder import SYSTEM_PROMPT

    assert "overview / aggregate queries" in SYSTEM_PROMPT
    assert "synthesize what IS available" in SYSTEM_PROMPT
    assert "Based on available documentation:" in SYSTEM_PROMPT
    assert "CH-005" in SYSTEM_PROMPT
    # All 8 rules present (1-8)
    for n in range(1, 9):
        assert f"\n{n}." in SYSTEM_PROMPT, f"Rule {n} missing from SYSTEM_PROMPT"
