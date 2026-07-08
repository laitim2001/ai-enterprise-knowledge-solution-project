"""Citation post-process — attach neighbour-chunk images per W25 F5 D1 + ADR-0034.

When the LLM cites a chunk that itself has no embedded images (eg. the §8
"Integration scenarios" intro chunk), but nearby chunks in the same document
DO carry relevant images (eg. §8.1-8.5 scenario walkthroughs with diagrams),
this module attaches those neighbour images to the citation's
`embedded_images` field so the chat UI surfaces them.

Per W25 plan §2 F5 D1 acceptance criteria:
- Look up neighbours by `doc_order` ±N range (default N=3) in the same doc
- Cap at `max_aux_per_citation = 2` neighbour images per citation (avoid 圖洪水)
- Dedup against citation's own embedded_images via `checksum_sha256`
- Returns NEW Citation list (Pydantic immutable model_copy pattern)

Per Karpathy §1.2 simplicity-first: the first cut matched only `chunk_index ±N`
range (covers the immediate neighbour case). BUG-027 (W42 follow-up) adds the
predicted section-aware mode: when `section_path_prefix_depth > 0`, section
membership (`section_path[:depth]`) REPLACES window proximity, so a §8 intro
citation surfaces ALL §8.* scenario figures (chunk 45/47/49/51/53) instead of
only the two inside ±window. Gated off by default (depth=0) — production flip
is a separate user decision (see settings.citation_neighbour_section_path
_prefix_depth).

Per ADR-0034 §Implementation Mapping: this module complements the F3 D4
query expansion path (which improves chunk retrieval recall) — D1 ensures
that even when retrieval surfaces only meta/intro chunks, the answer's
citation can still carry the relevant scenario-specific images that
neighbour chunks own.
"""

from __future__ import annotations

import asyncio
from collections import Counter

import structlog

from api.schemas.query import Citation, ImageRef
from generation.citation_enrichment import parse_embedded_images
from retrieval.retrieval_engine import RetrievalEngine

logger = structlog.get_logger(__name__)


async def attach_neighbour_images(
    citations: list[Citation],
    kb_id: str,
    engine: RetrievalEngine,
    *,
    max_aux_per_citation: int = 2,
    neighbour_window: int = 3,
    section_path_prefix_depth: int = 0,
    user_principals: list[str] | None = None,
) -> list[Citation]:
    """For each citation, attach embedded_images from neighbour chunks in the
    same document (matched by chunk_index ±neighbour_window range).

    Returns a NEW list of Citation instances; original citations passed
    through unchanged when no neighbour images found. Each citation's
    `embedded_images` field is extended (not replaced) — existing direct
    images preserved + appended with up to `max_aux_per_citation` distinct
    neighbour images, deduped against the citation's own images by
    `checksum_sha256`.

    BUG-041 — `user_principals` threads ACL security trimming into the neighbour
    chunk fetch, matching the other four retrieval surfaces (search / context
    expander / parent-doc / citation expansion). Without it the neighbour-image
    path is a confused-deputy leak: a user hitting a visible chunk could pull
    images off adjacent chunks that document-level ACL would trim. admin
    (`user_principals=None`) = no filter (ADR-0066 G4 intent).

    Per F5 D1 acceptance criteria + ADR-0034 §Implementation Mapping.
    """
    if not citations:
        return citations

    # Group by unique doc_id; one chunk-list fetch per doc rather than per
    # citation (citations from same doc share the doc's chunk universe).
    doc_ids: list[str] = sorted({c.doc_id for c in citations if c.doc_id})
    if not doc_ids:
        return citations

    # Parallel fetch chunk lists (independent IO-bound Azure Search calls).
    # BUG-041 — thread user_principals so the neighbour fetch is ACL-trimmed.
    fetched_chunks = await asyncio.gather(
        *(engine.list_chunks(kb_id, did, user_principals=user_principals) for did in doc_ids),
        return_exceptions=True,
    )

    chunks_by_doc: dict[str, list[dict]] = {}
    fetch_errors: list[str] = []
    for did, result in zip(doc_ids, fetched_chunks, strict=True):
        if isinstance(result, BaseException):
            fetch_errors.append(f"{did}: {type(result).__name__}: {result}")
            chunks_by_doc[did] = []
            continue
        chunks_by_doc[did] = result  # type: ignore[assignment]

    if fetch_errors:
        # Graceful degradation: per-doc fetch failures don't break the citation
        # list — that doc's neighbour-image augmentation is skipped (citation
        # falls back to direct embedded_images only). Log for trace + diagnosis.
        logger.warning(
            "neighbour_images_doc_chunk_fetch_failed",
            errors=fetch_errors,
        )

    augmented_citations: list[Citation] = []
    augmented_count = 0
    images_added = 0

    for citation in citations:
        doc_chunks = chunks_by_doc.get(citation.doc_id, [])
        if not doc_chunks:
            augmented_citations.append(citation)
            continue

        new_images = _find_neighbour_images(
            citation=citation,
            doc_chunks=doc_chunks,
            max_aux=max_aux_per_citation,
            window=neighbour_window,
            section_path_prefix_depth=section_path_prefix_depth,
        )

        if new_images:
            merged = list(citation.embedded_images) + new_images
            augmented_citations.append(
                citation.model_copy(update={"embedded_images": merged}),
            )
            augmented_count += 1
            images_added += len(new_images)
        else:
            augmented_citations.append(citation)

    logger.info(
        "neighbour_images_attached",
        kb_id=kb_id,
        citation_count=len(citations),
        docs_fetched=len(doc_ids),
        citations_augmented=augmented_count,
        images_added=images_added,
        max_aux_per_citation=max_aux_per_citation,
        neighbour_window=neighbour_window,
    )

    return augmented_citations


def _find_neighbour_images(
    citation: Citation,
    doc_chunks: list[dict],
    *,
    max_aux: int,
    window: int,
    section_path_prefix_depth: int = 0,
) -> list[ImageRef]:
    """Walk doc_chunks within chunk_index ±window of citation, extract distinct
    new images (deduped against citation's own + each other), cap at max_aux.

    BUG-027 — when `section_path_prefix_depth > 0` (and the citation carries a
    section_path), section membership REPLACES window proximity: same-section
    sibling figures attach regardless of chunk distance (nearest-first, still
    capped at max_aux), so a §8 intro citation surfaces ALL §8.* scenario
    figures, not just the two inside ±window. depth=0 (default) keeps the
    window±N first-cut behavior bit-identical. See `_find_section_neighbour_images`.

    Pure function; no IO; testable in isolation without mocks.
    """
    if max_aux <= 0:
        return []
    if section_path_prefix_depth > 0 and citation.section_path:
        return _find_section_neighbour_images(
            citation,
            doc_chunks,
            max_aux=max_aux,
            section_path_prefix_depth=section_path_prefix_depth,
        )
    if window <= 0:
        return []

    # Dedup checksums — start with citation's own images
    own_checksums: set[str] = {
        img.checksum_sha256 for img in citation.embedded_images if img.checksum_sha256
    }

    new_images: list[ImageRef] = []
    for chunk in doc_chunks:
        chunk_idx_raw = chunk.get("chunk_index", 0)
        try:
            chunk_idx = int(chunk_idx_raw) if chunk_idx_raw is not None else 0
        except (TypeError, ValueError):
            continue

        # Skip self + out-of-window
        if chunk_idx == citation.chunk_index:
            continue
        if abs(chunk_idx - citation.chunk_index) > window:
            continue

        # Parse this chunk's images
        images = parse_embedded_images(
            str(chunk.get("embedded_images_json", "") or ""),
        )
        for img in images:
            # Skip empty checksum (defensive — pre-BUG-009 chunks may lack it)
            if not img.checksum_sha256:
                continue
            if img.checksum_sha256 in own_checksums:
                continue
            own_checksums.add(img.checksum_sha256)
            new_images.append(img)
            if len(new_images) >= max_aux:
                return new_images

    return new_images


def _find_section_neighbour_images(
    citation: Citation,
    doc_chunks: list[dict],
    *,
    max_aux: int,
    section_path_prefix_depth: int,
) -> list[ImageRef]:
    """BUG-027 / CH-011 / CH-012 — section-aware variant of `_find_neighbour_images`.

    Attaches images from chunks in the SAME section as the citation (matched by
    `section_path[:section_path_prefix_depth]`), ignoring chunk-index window
    proximity — so a §3 intro citation surfaces figures across the whole procedure,
    not only the two inside ±window.

    CH-012 / ADR-0049 — section-FAIR distribution. Candidate figures are grouped by
    the finer SUB-section (`section_path[:section_path_prefix_depth + 1]`, e.g.
    §3.1.1 / §3.1.3 / §3.1.4 / §3.1.5) and the `max_aux` budget is taken ROUND-ROBIN
    across those sub-sections (sub-sections ordered by document position; document
    order within each). This stops the earliest sub-sections (§3.1.1-§3.1.3) from
    saturating `max_aux` and starving the procedure's tail steps (Approve/Reject
    §3.1.4, Post §3.1.5) — pre-CH-012, candidates were one document-ordered list
    truncated at `max_aux`, leaving tail steps with zero figures. With no finer
    sub-section to split on (single group), the round-robin degenerates to the prior
    document-ordered take (bit-identical). Images are deduped against the citation's
    own images + each other (first occurrence wins across sub-sections); capped at
    max_aux. The frontend's CH-011 `doc_order` sort still governs the final render
    order — this only governs WHICH figures survive `max_aux`. Returns [] when the
    citation's section_path is shorter than the requested prefix depth.

    Pure function; no IO; testable in isolation without mocks.
    """
    cited_prefix = list(citation.section_path[:section_path_prefix_depth])
    if len(cited_prefix) < section_path_prefix_depth:
        return []

    own_checksums: set[str] = {
        img.checksum_sha256 for img in citation.embedded_images if img.checksum_sha256
    }

    # CH-012 / ADR-0049 — collect same-section candidates, grouped by the finer
    # SUB-section (one level deeper than the match depth) so the max_aux budget can
    # spread round-robin across sub-sections instead of front-loading the earliest.
    # Sub-section groups are ordered by their first document position; chunks within
    # a group stay in document order.
    sub_depth = section_path_prefix_depth + 1
    groups: dict[tuple[str, ...], list[tuple[int, dict]]] = {}
    group_first_idx: dict[tuple[str, ...], int] = {}
    for chunk in doc_chunks:
        chunk_idx_raw = chunk.get("chunk_index", 0)
        try:
            chunk_idx = int(chunk_idx_raw) if chunk_idx_raw is not None else 0
        except (TypeError, ValueError):
            continue
        if chunk_idx == citation.chunk_index:
            continue
        cand_section_path = chunk.get("section_path")
        if not isinstance(cand_section_path, list):
            continue
        if list(cand_section_path[:section_path_prefix_depth]) != cited_prefix:
            continue
        sub_key = tuple(str(p) for p in cand_section_path[:sub_depth])
        groups.setdefault(sub_key, []).append((chunk_idx, chunk))
        prev = group_first_idx.get(sub_key)
        if prev is None or chunk_idx < prev:
            group_first_idx[sub_key] = chunk_idx

    if not groups:
        return []

    # Per sub-section, extract candidate images in document order (own-dedup only;
    # cross-group dedup happens during the round-robin via `seen`).
    ordered_keys = sorted(groups, key=lambda k: group_first_idx[k])
    per_group: list[list[ImageRef]] = []
    for key in ordered_keys:
        imgs: list[ImageRef] = []
        for _idx, chunk in sorted(groups[key], key=lambda pair: pair[0]):
            for img in parse_embedded_images(str(chunk.get("embedded_images_json", "") or "")):
                if not img.checksum_sha256 or img.checksum_sha256 in own_checksums:
                    continue
                imgs.append(img)
        per_group.append(imgs)

    # Round-robin across sub-sections: one image per group per pass, in document
    # order of sub-sections, until max_aux or all groups exhausted. `seen` enforces
    # global dedup (a figure shared across sub-sections counts once; first wins).
    new_images: list[ImageRef] = []
    seen: set[str] = set(own_checksums)
    cursors = [0] * len(per_group)
    progressed = True
    while len(new_images) < max_aux and progressed:
        progressed = False
        for gi, imgs in enumerate(per_group):
            if len(new_images) >= max_aux:
                break
            i = cursors[gi]
            while i < len(imgs) and imgs[i].checksum_sha256 in seen:
                i += 1
            cursors[gi] = i
            if i < len(imgs):
                img = imgs[i]
                seen.add(img.checksum_sha256)
                new_images.append(img)
                cursors[gi] = i + 1
                progressed = True

    return new_images


async def pin_chapter_overview_images(
    citations: list[Citation],
    kb_id: str,
    engine: RetrievalEngine,
    *,
    chapter_prefix_depth: int = 1,
    overview_section_keyword: str = "overview",
    user_principals: list[str] | None = None,
) -> list[Citation]:
    """CH-010 / ADR-0047 — pin the dominant chapter's §X.1 "Overview" figures to the
    FRONT of the lead citation's ``embedded_images``.

    Why this exists (root cause, verified 2026-06-08 on drive-images-1): for a
    narrow-step query the §X.1 Overview chunk (e.g. GL03 §3.1.1 with the High Level
    Process + Business Process Flow diagrams) is neither retrieved (rerank_k=5) nor
    reached by the nearest-first neighbour-attach (the abundant same-section step
    images saturate ``max_aux`` before the far overview chunk). Even when post-hoc
    expansion materialises the overview as a (low-relevance) citation, the
    citation-order ``cap_images_per_answer`` starves its images. Fetching the
    overview chunk's images and prepending them to ``citations[0]`` places them
    AHEAD of the cap (front-kept), so they survive; the frontend's document-order
    sort (§X.1 < §X.3) then makes them lead the procedure.

    Text / section signal only — no image embedding (H4). Returns a NEW citation
    list; the original is returned unchanged on no dominant chapter / no overview
    chunk / fetch error (graceful degradation per ADR-0034 §Consequences). Pure
    aside from the single ``engine.list_chunks`` fetch.

    BUG-041 — `user_principals` threads ACL security trimming into the overview
    chunk fetch (same confused-deputy fix as ``attach_neighbour_images``). admin
    (``user_principals=None``) = no filter.
    """
    if not citations:
        return citations

    # Dominant chapter = the most common section_path[:depth] across citations.
    prefixes = [
        tuple(c.section_path[:chapter_prefix_depth])
        for c in citations
        if len(c.section_path) >= chapter_prefix_depth and c.section_path[:chapter_prefix_depth]
    ]
    if not prefixes:
        return citations
    dominant_chapter = Counter(prefixes).most_common(1)[0][0]

    lead = citations[0]
    if not lead.doc_id:
        return citations

    try:
        # BUG-041 — thread user_principals so the overview fetch is ACL-trimmed.
        doc_chunks = await engine.list_chunks(kb_id, lead.doc_id, user_principals=user_principals)
    except Exception as exc:  # noqa: BLE001 — graceful degradation; keep original citations
        logger.warning(
            "chapter_overview_pin_fetch_failed",
            kb_id=kb_id,
            error=f"{type(exc).__name__}: {exc}",
        )
        return citations

    # Collect images from the dominant chapter's "Overview" chunk(s), deduped.
    keyword = overview_section_keyword.lower()
    overview_images: list[ImageRef] = []
    seen: set[str] = set()
    for chunk in doc_chunks:
        section_path = chunk.get("section_path")
        if not isinstance(section_path, list) or len(section_path) < chapter_prefix_depth:
            continue
        if tuple(section_path[:chapter_prefix_depth]) != dominant_chapter:
            continue
        leaf = str(section_path[-1]) if section_path else ""
        if keyword not in leaf.lower():
            continue
        for img in parse_embedded_images(str(chunk.get("embedded_images_json", "") or "")):
            if not img.checksum_sha256 or img.checksum_sha256 in seen:
                continue
            seen.add(img.checksum_sha256)
            overview_images.append(img)

    if not overview_images:
        return citations

    # MOVE the overview images to the FRONT of the lead citation. They must lead
    # AND survive the citation-order `cap_images_per_answer` (which keeps each
    # citation's FIRST N). It is NOT enough to skip when they are already present:
    # the neighbour-attach may have attached them at a LATE position on the lead,
    # where the cap then strips them. So strip any existing copies from the lead
    # and re-prepend — overview first, then the lead's other images.
    overview_checksums = {img.checksum_sha256 for img in overview_images}
    lead_rest = [
        img for img in lead.embedded_images if img.checksum_sha256 not in overview_checksums
    ]
    new_images = [*overview_images, *lead_rest]

    # No-op when the lead already leads with exactly these overview images in order
    # (avoids a needless model_copy + keeps the citation object identity stable).
    if [img.checksum_sha256 for img in lead.embedded_images] == [
        img.checksum_sha256 for img in new_images
    ]:
        return citations

    new_lead = lead.model_copy(update={"embedded_images": new_images})
    logger.info(
        "chapter_overview_pinned",
        kb_id=kb_id,
        chapter=list(dominant_chapter),
        overview_images=len(overview_images),
    )
    return [new_lead, *citations[1:]]
