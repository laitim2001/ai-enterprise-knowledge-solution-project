"""W75 / ADR-0056 段②d — inject_section_anchored_markers tests(方案 A).

Covers F3.1 (same-section anchoring) / F3.2 (no same-section anchor → untouched) /
F3.3 (doc_order ordering + no-op cases). The marker body == checksum_sha256[:8], so
each fixture checksum is its sha8 padded to a 64-hex string.
"""

from __future__ import annotations

from api.schemas.query import Citation, ImageRef
from generation.section_anchor_markers import inject_section_anchored_markers

# sha8 (marker body) == checksum_sha256[:8]; pad to a realistic 64-hex checksum.
SHA_A = "aaaaaaaa" + "1" * 56
SHA_B = "bbbbbbbb" + "1" * 56
SHA_C = "cccccccc" + "1" * 56
SHA_D = "dddddddd" + "1" * 56


def _img(sha: str, *, section: list[str] | None = None, doc_order: int = 0) -> ImageRef:
    return ImageRef(
        blob_url=f"blob/{sha[:8]}",
        alt_text="",
        checksum_sha256=sha,
        width=800,
        height=600,
        source_section=section if section is not None else [],
        doc_order=doc_order,
    )


def _citation(images: list[ImageRef], *, section: list[str] | None = None) -> Citation:
    return Citation(
        chunk_id="chunk-1",
        doc_id="doc-1",
        doc_title="Manual",
        chunk_title="t",
        chunk_index=0,
        section_path=section if section is not None else [],
        relevance_score=1.0,
        embedded_images=images,
    )


def test_same_section_aux_image_injected_after_anchor() -> None:
    """F3.1 — an un-anchored aux image in the same chapter as an anchored marker
    gets its marker injected right after that anchor."""
    answer = "Step one [IMG#aaaaaaaa] then step two."
    citations = [
        _citation(
            [
                _img(SHA_A, section=["3"]),  # anchored (its marker is in the answer)
                _img(SHA_B, section=["3"]),  # un-anchored aux, same chapter
            ],
        ),
    ]
    out = inject_section_anchored_markers(answer, citations)
    assert out == "Step one [IMG#aaaaaaaa][IMG#bbbbbbbb] then step two."


def test_no_same_section_anchor_left_untouched() -> None:
    """F3.2 — an un-anchored image whose chapter has NO anchored marker is not
    injected (stays in the trailing pile); the answer is unchanged."""
    answer = "Step one [IMG#aaaaaaaa] then."
    citations = [
        _citation(
            [
                _img(SHA_A, section=["3"]),  # anchored, chapter 3
                _img(SHA_C, section=["5"]),  # un-anchored, chapter 5 — no anchor there
            ],
        ),
    ]
    out = inject_section_anchored_markers(answer, citations)
    assert out == answer


def test_aux_images_injected_in_doc_order() -> None:
    """F3.3 — same-chapter un-anchored images are injected in doc_order, not
    citation order."""
    answer = "Intro [IMG#aaaaaaaa] end."
    citations = [
        _citation(
            [
                _img(SHA_A, section=["3"], doc_order=1),  # anchored
                _img(SHA_B, section=["3"], doc_order=20),  # un-anchored, later
                _img(SHA_C, section=["3"], doc_order=10),  # un-anchored, earlier
            ],
        ),
    ]
    out = inject_section_anchored_markers(answer, citations)
    # C (doc_order 10) before B (doc_order 20)
    assert out == "Intro [IMG#aaaaaaaa][IMG#cccccccc][IMG#bbbbbbbb] end."


def test_multiple_chapters_each_anchored_independently() -> None:
    """Each chapter's aux images go after THAT chapter's anchor; back-to-front
    splice keeps earlier offsets valid."""
    answer = "Ch3 [IMG#aaaaaaaa] mid Ch5 [IMG#cccccccc] end."
    citations = [
        _citation(
            [
                _img(SHA_A, section=["3"]),  # anchored ch3
                _img(SHA_C, section=["5"]),  # anchored ch5
                _img(SHA_B, section=["3"]),  # un-anchored ch3
                _img(SHA_D, section=["5"]),  # un-anchored ch5
            ],
        ),
    ]
    out = inject_section_anchored_markers(answer, citations)
    assert out == "Ch3 [IMG#aaaaaaaa][IMG#bbbbbbbb] mid Ch5 [IMG#cccccccc][IMG#dddddddd] end."


def test_uses_last_anchor_in_chapter() -> None:
    """When a chapter has several anchored markers, the aux image is injected after
    the LAST one in the answer."""
    answer = "[IMG#aaaaaaaa] text [IMG#bbbbbbbb] more."
    citations = [
        _citation(
            [
                _img(SHA_A, section=["3"]),  # anchored, earlier
                _img(SHA_B, section=["3"]),  # anchored, later
                _img(SHA_C, section=["3"]),  # un-anchored → after the LATER anchor
            ],
        ),
    ]
    out = inject_section_anchored_markers(answer, citations)
    assert out == "[IMG#aaaaaaaa] text [IMG#bbbbbbbb][IMG#cccccccc] more."


def test_too_shallow_section_skipped() -> None:
    """An un-anchored image with no source_section (shallower than the prefix depth)
    can't be chapter-matched and is left untouched."""
    answer = "[IMG#aaaaaaaa] x."
    citations = [
        _citation(
            [
                _img(SHA_A, section=["3"]),  # anchored
                _img(SHA_B, section=[]),  # un-anchored, no section → skip
            ],
        ),
    ]
    out = inject_section_anchored_markers(answer, citations)
    assert out == answer


def test_no_marker_in_answer_is_noop() -> None:
    """No anchored marker to anchor against → answer returned unchanged."""
    answer = "Plain answer, no images."
    citations = [_citation([_img(SHA_A, section=["3"])])]
    assert inject_section_anchored_markers(answer, citations) == answer


def test_all_images_already_anchored_is_noop() -> None:
    """Every citation image already has a marker → nothing to inject."""
    answer = "Step [IMG#aaaaaaaa] done."
    citations = [_citation([_img(SHA_A, section=["3"])])]
    assert inject_section_anchored_markers(answer, citations) == answer


def test_empty_citations_is_noop() -> None:
    answer = "Step [IMG#aaaaaaaa] done."
    assert inject_section_anchored_markers(answer, []) == answer


def test_aux_image_deduped_by_sha8_across_citations() -> None:
    """The same un-anchored image appearing under two citations is injected once."""
    answer = "Intro [IMG#aaaaaaaa] end."
    citations = [
        _citation([_img(SHA_A, section=["3"]), _img(SHA_B, section=["3"])]),
        _citation([_img(SHA_B, section=["3"])]),  # SHA_B repeats — first occurrence wins
    ]
    out = inject_section_anchored_markers(answer, citations)
    assert out == "Intro [IMG#aaaaaaaa][IMG#bbbbbbbb] end."


def test_max_per_anchor_caps_injection_per_chapter() -> None:
    """W75 F5 — max_per_anchor caps each chapter's injection at N (doc_order first N);
    the overflow stays un-injected (frontend trailing pile)."""
    answer = "Intro [IMG#aaaaaaaa] end."
    citations = [
        _citation([
            _img(SHA_A, section=["3"], doc_order=1),   # anchored
            _img(SHA_B, section=["3"], doc_order=10),  # un-anchored
            _img(SHA_C, section=["3"], doc_order=20),  # un-anchored
            _img(SHA_D, section=["3"], doc_order=30),  # un-anchored — overflow at cap=2
        ]),
    ]
    out = inject_section_anchored_markers(answer, citations, max_per_anchor=2)
    # only B + C (first 2 by doc_order); D overflow stays out
    assert out == "Intro [IMG#aaaaaaaa][IMG#bbbbbbbb][IMG#cccccccc] end."


def test_max_per_anchor_zero_is_no_cap() -> None:
    """W75 F5 — max_per_anchor=0 (default) = no cap = F1-F4 behaviour (bit-identical)."""
    answer = "Intro [IMG#aaaaaaaa] end."
    citations = [
        _citation([
            _img(SHA_A, section=["3"], doc_order=1),
            _img(SHA_B, section=["3"], doc_order=10),
            _img(SHA_C, section=["3"], doc_order=20),
        ]),
    ]
    out_zero = inject_section_anchored_markers(answer, citations, max_per_anchor=0)
    out_default = inject_section_anchored_markers(answer, citations)
    assert out_zero == out_default == "Intro [IMG#aaaaaaaa][IMG#bbbbbbbb][IMG#cccccccc] end."
