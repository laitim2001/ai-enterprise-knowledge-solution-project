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


# ─── W33 F1.2.a + W35 F1.7 — Rule 7 v2 + Rule 8 Option C re-tighten + Rule 6 non-regression ───
# Sequential ship on W32 (h') baseline established (engine-fetch citation expansion):
# Rule 7 v2 = specificity preference (§X.M numbering > overview/coverage-summary chunks).
# Rule 8   = cite chunks that support each fact (W35 Option C re-tighten — F1.7 contingency from
#            Option B per F1.4 correctness -5pp regression; Option C minimal change wording:
#            soft cap「typically 1-2 per fact」 + explicit anti-pattern「avoid citing multiple
#            overlapping chunks that convey the same information」).
# Rule 7 v2 preserved verbatim from W31 commit 16b9b3d (reverted W31 → restored W33 → preserved W35).
# Rule 8 W33 source = W31 commit 16b9b3d verbatim → W35 F1.0 Option B first divergence (regressed
#         correctness -5pp) → W35 F1.7 Option C re-tighten preserves multi-cite freedom.


def test_system_prompt_includes_rule_7_v2_specificity_preference() -> None:
    """W33 F1.2.a — Rule 7 v2 wording present in SYSTEM_PROMPT.

    Restored verbatim from W31 commit 16b9b3d. Key phrases per W31 plan §F1.1.a +
    F2 v1 corpus-realistic refinement (bare X.M + §X.M coverage + Scenario A walkthrough
    + Step 3.2 examples + intro-chunk-insufficient framing per F2 v1 Run 1 evidence).
    """
    from generation.prompt_builder import SYSTEM_PROMPT

    # Core specificity-preference framing
    assert "§X.M" in SYSTEM_PROMPT
    assert "individually-numbered chunks" in SYSTEM_PROMPT
    assert "coverage-summary chunks" in SYSTEM_PROMPT
    # Intro chunk insufficient framing (per W31 F2 v1 Run 5 §8.6 mis-interpretation evidence)
    assert "intro chunk" in SYSTEM_PROMPT
    assert "lists scenario names is insufficient" in SYSTEM_PROMPT
    # Examples include both §-prefix and Scenario A/Step 3.2 corpus-realistic patterns
    assert "§8.1" in SYSTEM_PROMPT
    assert "Scenario A walkthrough" in SYSTEM_PROMPT
    assert "Step 3.2" in SYSTEM_PROMPT


def test_system_prompt_includes_rule_8_cite_sufficient() -> None:
    """W35 F1.7 — Rule 8 wording Option C re-tighten present in SYSTEM_PROMPT.

    Option C locked after F1.4 Option B outcome surprise (G1 faith preserve OK +
    runtime -25% ⭐ but correctness -5pp regression — W34 0.7669 → W35 Opt B
    0.7169 = W26 baseline 0.7416 -2.47pp BELOW). Option C minimal change wording:
    soft cap「typically 1-2 per fact」 + explicit anti-pattern「avoid citing
    multiple overlapping chunks that convey the same information」 — preserves
    multi-cite freedom without over-abstract「different angle」 framing that
    caused Option B over-conservative cite + sparse answer.
    """
    from generation.prompt_builder import SYSTEM_PROMPT

    # Core cite-chunks-that-support framing (W35 Option C)
    assert "cite the chunks that support each fact" in SYSTEM_PROMPT
    assert "partial information" in SYSTEM_PROMPT  # lead-in preserved
    assert "typically 1-2 per fact" in SYSTEM_PROMPT  # soft cap
    # Anti-redundancy explicit (replaces Option B「non-redundant detail」 abstract)
    assert "avoid citing multiple overlapping chunks" in SYSTEM_PROMPT
    assert "convey the same information" in SYSTEM_PROMPT


def test_system_prompt_rule_6_ch005_preserved_non_regression() -> None:
    """W33 F1.2.a — Rule 6 CH-005 R14 mitigation wording 未被 Rule 7/8 邊緣編輯破壞。

    Non-regression guard against accidental Rule 6 wording shift during multi-rule edit。
    CH-005 R14 mitigation key phrases preserved per W25 D4 + W25.5 BUG-025 fix scope。
    """
    from generation.prompt_builder import REFUSAL_PHRASE, SYSTEM_PROMPT

    # CH-005 partial-coverage framing
    assert "Based on available documentation:" in SYSTEM_PROMPT
    # COMPLETELY off-topic condition for refusal (Rule 2 reference)
    assert "COMPLETELY off-topic" in SYSTEM_PROMPT
    # Refusal phrase still reachable via REFUSAL_PHRASE constant interpolation
    assert REFUSAL_PHRASE in SYSTEM_PROMPT
    # CH-005 attribution preserved
    assert "(CH-005 — R14 mitigation" in SYSTEM_PROMPT


# --- W70 / ADR-0055 - inline image markers (knob-gated marked dispatch + rule) ---


def test_w70_off_ignores_marked_field_and_omits_rule() -> None:
    """G3 zero-regression - default OFF: prompt uses clean chunk_text even when
    the marked field is present, and the system prompt stays byte-identical."""
    from generation.prompt_builder import SYSTEM_PROMPT

    chunk = _chunk_with_fields(chunk_text_marked="marked text [IMG#aabbccdd]")
    msgs = build_prompt("test query", [chunk])
    assert "raw chunk text fallback" in msgs.messages[1]["content"]
    assert "[IMG#" not in msgs.messages[1]["content"]
    assert msgs.messages[0]["content"] == SYSTEM_PROMPT


def test_w70_on_raw_path_uses_marked_and_appends_rule() -> None:
    """ON - raw-text path switches to chunk_text_marked; keep-markers rule is
    appended AFTER the unchanged base system prompt."""
    from generation.prompt_builder import SYSTEM_PROMPT

    chunk = _chunk_with_fields(chunk_text_marked="marked text [IMG#aabbccdd]")
    msgs = build_prompt("test query", [chunk], inline_image_markers=True)
    user_msg = msgs.messages[1]["content"]
    assert "marked text [IMG#aabbccdd]" in user_msg
    assert "raw chunk text fallback" not in user_msg
    system = msgs.messages[0]["content"]
    assert system.startswith(SYSTEM_PROMPT)
    assert "[IMG#" in system  # the appended keep-markers rule


def test_w70_on_falls_back_to_clean_text_when_marked_empty() -> None:
    """ON + marker-less chunk ("" marked field / pre-W70 index) -> clean text."""
    chunk = _chunk_with_fields(chunk_text_marked="")
    msgs = build_prompt("test query", [chunk], inline_image_markers=True)
    assert "raw chunk text fallback" in msgs.messages[1]["content"]


def test_w70_on_parent_section_text_takes_priority_unchanged() -> None:
    """ON - dispatch priority unchanged: parent_section_text (assembled marked
    upstream) still supersedes the raw path."""
    chunk = _chunk_with_fields(
        chunk_text_marked="anchor marked [IMG#11223344]",
        parent_section_text="parent marked sibling [IMG#55667788]",
    )
    msgs = build_prompt("test query", [chunk], inline_image_markers=True)
    user_msg = msgs.messages[1]["content"]
    assert "parent marked sibling [IMG#55667788]" in user_msg
    assert "anchor marked [IMG#11223344]" not in user_msg  # replace branch


def test_w70_on_append_mode_main_segment_uses_marked() -> None:
    """ON + append dispatch - the anchor main segment uses the marked variant."""
    chunk = _chunk_with_fields(
        chunk_text_marked="anchor marked [IMG#11223344]",
        parent_section_text="parent siblings text",
    )
    msgs = build_prompt(
        "test query",
        [chunk],
        dispatch_mode="append",
        inline_image_markers=True,
    )
    user_msg = msgs.messages[1]["content"]
    assert "anchor marked [IMG#11223344]" in user_msg
    assert "parent siblings text" in user_msg
