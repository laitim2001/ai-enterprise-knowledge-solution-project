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
level is the build target; leaf-level precision is left to the frontend ``doc_order``
sort (CH-011) and a possible future refinement.

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
) -> str:
    """Inject ``[IMG#<sha8>]`` markers for un-anchored aux images at their
    same-section anchored marker.

    For each image in ``citations.embedded_images`` (deduped by sha8, first
    occurrence) that has NO marker in ``answer`` (an un-anchored aux image), find the
    anchored marker whose image shares its ``source_section[:section_prefix_depth]``
    and inject the un-anchored image's marker right after the LAST such anchored
    marker in the answer. Same-section un-anchored images are ordered by ``doc_order``
    so they read in document flow. Un-anchored images with no same-section anchored
    marker are left untouched (they stay in the frontend trailing pile — the
    章節-level可錨率 < 100% residue; we never force a wrong-section anchor).

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
    # already-anchored set (→ their section becomes an anchor target) and the
    # un-anchored set (→ to be injected). Images whose section_path is shallower than
    # the requested depth don't participate (no reliable chapter to match on).
    seen: set[str] = set()
    anchored_section: dict[str, tuple[str, ...]] = {}
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
                anchored_section[sha8] = section
            else:
                un_anchored.append((img, section))

    if not un_anchored:
        return answer

    # Per chapter → the END offset of the LAST anchored marker in that chapter
    # (finditer order means a later match overwrites = the last position wins).
    last_anchor_end: dict[tuple[str, ...], int] = {}
    for match in anchored_matches:
        anchor_section = anchored_section.get(match.group(1))
        if anchor_section is None:
            continue  # marker sha8 not in citations (capped / hallucinated) — not an anchor
        last_anchor_end[anchor_section] = match.end()

    # Group un-anchored images by chapter, keeping only those WITH a same-section
    # anchor (the rest stay in the trailing pile).
    by_section: dict[tuple[str, ...], list[ImageRef]] = defaultdict(list)
    for img, section in un_anchored:
        if section in last_anchor_end:
            by_section[section].append(img)

    if not by_section:
        return answer

    # One insertion per chapter: its un-anchored images (doc_order sorted) as a marker
    # run, placed after that chapter's last anchored marker.
    insertions: list[tuple[int, str]] = []
    for section, imgs in by_section.items():
        imgs_sorted = sorted(imgs, key=lambda im: im.doc_order)
        marker_run = "".join(f"[IMG#{im.checksum_sha256[:8]}]" for im in imgs_sorted)
        insertions.append((last_anchor_end[section], marker_run))

    # Apply back-to-front so earlier offsets stay valid as we splice.
    insertions.sort(key=lambda pair: pair[0], reverse=True)
    out = answer
    for pos, text in insertions:
        out = out[:pos] + text + out[pos:]
    return out
