"""W75 / ADR-0056 段②d — section-anchored aux image marker injection(方案 A).

The image-recall arc (W59-W68, cap=80 / ``citation_neighbour_max_aux_images``=40)
drives ``attach_neighbour_images`` (``citation_image_neighbors.py``) to撈 a large pool
of neighbour / aux images onto the citations POST-synthesis. The synthesiser prompt
never sees those images, so the answer text carries no ``[IMG#<sha8>]`` marker for
them → the frontend ``planAnchoredImages`` drops every one into the trailing
"Referenced screenshots" pile (per ADR-0055 §結構性限制). For a P1 image-dense SOP
that meant 22-55% of the surfaced figures sat at the end with no anchoring text
(measured 2026-06-14, drive-images-1).

This module is the方案 A render-side fix: post-synthesis, for each un-anchored aux
image, INJECT an ``[IMG#<sha8>]`` marker into the answer text right after the
SAME-SECTION anchored marker the synthesiser already wrote. The frontend's existing
``parseInlineImageMarkers`` / ``planAnchoredImages`` then renders the image inline at
that position — no frontend change (H7 untouched); the trailing pile shrinks to only
the genuinely un-anchorable residue.

Anchoring is章節-level (``section_prefix_depth=1``): an un-anchored image is matched
to an anchored marker whose image shares its ``source_section[:depth]``. The measured
章節-level可錨率 is 100% on drive-images-1 (every un-anchored aux image's chapter has
at least one anchored marker), while full-leaf matching wavers 2-82% — so chapter
level is the matching granularity. WITHIN a chapter, the ``nearest`` option (W98)
picks the doc_order-closest anchor instead of the chapter's last, spreading the aux
across the chapter's cited steps (offline diagnostic: clump 37→16, +110 aux placed,
worse=0 over 18 captures); ``nearest=False`` keeps the W75 chapter-last behaviour.

Gated OFF by default via ``Settings.enable_section_anchored_aux_images`` (ADR-0040
four-layer); profile-routed ON for ``P1_sop_imgdense`` (W73 PROFILE_PRESETS). ADR-0056
條件式 principle: structured SOP only — prose / slide stay OFF to avoid misplacement.

Text / section signal only — no image embedding, no multimodal retrieval (H4).
Pure function, no IO; testable in isolation without mocks.
"""

from __future__ import annotations

import re
from collections import defaultdict

from api.schemas.query import Citation, ImageRef

# Same lenient body match as the strip / parse paths (inline_image_markers.py /
# inline-image-markers.ts) so injected + synthesiser markers share one grammar.
_MARKER_RE = re.compile(r"\[IMG#([^\]\s]*)\]")


def inject_section_anchored_markers(
    answer: str,
    citations: list[Citation],
    *,
    section_prefix_depth: int = 1,
    max_per_anchor: int = 0,
    nearest: bool = False,
) -> str:
    """Inject ``[IMG#<sha8>]`` markers for un-anchored aux images at their
    same-section anchored marker.

    For each image in ``citations.embedded_images`` (deduped by sha8, first
    occurrence) that has NO marker in ``answer`` (an un-anchored aux image), find an
    anchored marker whose image shares its ``source_section[:section_prefix_depth]``
    and inject the un-anchored image's marker right after it. Same-target un-anchored
    images are ordered by ``doc_order`` so they read in document flow. Un-anchored
    images with no same-section anchored marker are left untouched (they stay in the
    frontend trailing pile — the章節-level可錨率 < 100% residue; we never force a
    wrong-section anchor).

    Anchor selection (W98 / ADR-0056 段②d leaf 級):
    - ``nearest=False`` (default, W75) — the chapter's LAST anchored marker. All
      same-chapter aux clump after one step.
    - ``nearest=True`` — the same-chapter anchored marker whose image ``doc_order`` is
      CLOSEST to the aux's (tie → earliest text offset), spreading the chapter's aux
      across its distinct cited steps so each lands beside the step it illustrates.
      Structurally Pareto on clump: a single-anchor chapter is identical to
      ``nearest=False``; a multi-anchor chapter can only spread (never concentrate more).

    W75 F5 — when ``max_per_anchor`` > 0, each anchor injects at most N images
    (doc_order first N); the overflow stays un-injected (frontend trailing pile),
    which bounds the per-anchor clump (DD-1 measured maxRun=39). 0 = no cap (every
    same-section aux image injected — the F1-F4 behaviour).

    Returns the answer unchanged when there is no marker to anchor against, no
    un-anchored image, or nothing to inject. Pure function; no IO.
    """
    if not answer or "[IMG#" not in answer:
        return answer

    # The anchored markers the synthesiser already wrote (position + sha8, in order).
    anchored_matches = list(_MARKER_RE.finditer(answer))
    if not anchored_matches:
        return answer
    anchored_sha8 = {m.group(1) for m in anchored_matches}

    # Walk the citation images once: dedup by sha8 (first occurrence), split into the
    # already-anchored set (→ becomes an anchor target, carrying its chapter + doc_order)
    # and the un-anchored set (→ to be injected). Images whose section_path is shallower
    # than the requested depth don't participate (no reliable chapter to match on).
    seen: set[str] = set()
    anchored_meta: dict[str, tuple[tuple[str, ...], int]] = {}  # sha8 → (chapter, doc_order)
    un_anchored: list[tuple[ImageRef, tuple[str, ...]]] = []
    for citation in citations:
        for img in citation.embedded_images:
            sha = img.checksum_sha256
            if not sha:
                continue
            sha8 = sha[:8]
            if sha8 in seen:
                continue
            seen.add(sha8)
            section = tuple(str(p) for p in img.source_section[:section_prefix_depth])
            if len(section) < section_prefix_depth:
                continue  # too-shallow section — skip (no chapter to anchor on)
            if sha8 in anchored_sha8:
                anchored_meta[sha8] = (section, img.doc_order)
            else:
                un_anchored.append((img, section))

    if not un_anchored:
        return answer

    # Each anchored marker occurrence → (chapter, doc_order, END offset). A marker whose
    # sha8 is not in citations (capped / hallucinated) is not an anchor.
    anchors: list[tuple[tuple[str, ...], int, int]] = []
    for match in anchored_matches:
        meta = anchored_meta.get(match.group(1))
        if meta is None:
            continue
        anchors.append((meta[0], meta[1], match.end()))
    if not anchors:
        return answer

    # Per chapter → the END offset of the LAST anchored marker (the W75 default
    # placement; a later occurrence overwrites = last position wins).
    last_offset: dict[tuple[str, ...], int] = {}
    for chapter, _doc_order, end in anchors:
        last_offset[chapter] = end

    # Assign each un-anchored aux to a target insertion offset, grouped by that offset.
    # Default (W75) = its chapter's LAST anchor → all same-chapter aux clump there.
    # ``nearest`` (W98 / ADR-0056 段②d leaf 級) = the SAME-CHAPTER anchor whose image
    # doc_order is closest to the aux's (tie → earliest offset) so the aux lands beside
    # the step it illustrates, spreading the chapter's aux across its cited steps. Aux
    # with no same-chapter anchor stay in the frontend trailing pile (never wrong-section).
    by_offset: dict[int, list[ImageRef]] = defaultdict(list)
    for img, chapter in un_anchored:
        if chapter not in last_offset:
            continue
        if nearest:
            target = min(
                (a for a in anchors if a[0] == chapter),
                key=lambda a: (abs(a[1] - img.doc_order), a[2]),
            )[2]
        else:
            target = last_offset[chapter]
        by_offset[target].append(img)

    if not by_offset:
        return answer

    # One insertion per target offset: its aux images (doc_order sorted) as a marker run.
    # W75 F5 — ``max_per_anchor`` caps each anchor's run at N (doc_order first N); the
    # overflow stays un-injected (frontend trailing pile), bounding the per-anchor clump.
    insertions: list[tuple[int, str]] = []
    for offset, imgs in by_offset.items():
        imgs_sorted = sorted(imgs, key=lambda im: im.doc_order)
        if max_per_anchor > 0:
            imgs_sorted = imgs_sorted[:max_per_anchor]
        marker_run = "".join(f"[IMG#{im.checksum_sha256[:8]}]" for im in imgs_sorted)
        insertions.append((offset, marker_run))

    # Apply back-to-front so earlier offsets stay valid as we splice.
    insertions.sort(key=lambda pair: pair[0], reverse=True)
    out = answer
    for pos, text in insertions:
        out = out[:pos] + text + out[pos:]
    return out
