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
