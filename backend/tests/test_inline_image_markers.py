"""W71 F3 (ADR-0055 / DD-8) — backend inline image marker strip unit tests.

`strip_inline_image_markers` is the symmetric counterpart of the frontend strip;
it cleans `[IMG#sha8]` markers out of any answer text before it is JUDGED or
EXPORTED (e.g. the RAGAs faithfulness / answer-relevancy intake), so the markers
never read as unsupported answer content.
"""

from __future__ import annotations

from generation.inline_image_markers import strip_inline_image_markers


def test_strips_a_single_marker() -> None:
    assert strip_inline_image_markers("Click Save. [IMG#a1b2c3d4] Then close.") == (
        "Click Save.  Then close."
    )


def test_strips_multiple_including_standalone() -> None:
    text = "Step 1. [IMG#a1b2c3d4]\n\n[IMG#b2c3d4e5]\n\nStep 2. [IMG#c3d4e5f6]"
    out = strip_inline_image_markers(text)
    assert "[IMG#" not in out
    assert "Step 1." in out
    assert "Step 2." in out


def test_strips_malformed_marker_body() -> None:
    # lenient body — a marker the LLM mangles is still removed (never judged as text)
    assert strip_inline_image_markers("x [IMG#zz-not-hex!] y") == "x  y"


def test_leaves_citation_markers_and_brackets_untouched() -> None:
    text = "Fact one. [chunk-kb-a_doc-b_chunk-0001] See [a link](url)."
    assert strip_inline_image_markers(text) == text


def test_fast_path_returns_marker_less_text_unchanged() -> None:
    assert strip_inline_image_markers("no markers here") == "no markers here"


def test_empty_string() -> None:
    assert strip_inline_image_markers("") == ""


def test_answer_reduced_to_whitespace_when_only_a_marker() -> None:
    # a hypothetical marker-only fragment strips to whitespace — the RAGAs
    # config-test `_eval` treats that as empty (no meaningful faithfulness score)
    assert strip_inline_image_markers("[IMG#a1b2c3d4]").strip() == ""
