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
) -> list[Citation]:
    """For each citation, attach embedded_images from neighbour chunks in the
    same document (matched by chunk_index ±neighbour_window range).

    Returns a NEW list of Citation instances; original citations passed
    through unchanged when no neighbour images found. Each citation's
    `embedded_images` field is extended (not replaced) — existing direct
    images preserved + appended with up to `max_aux_per_citation` distinct
    neighbour images, deduped against the citation's own images by
    `checksum_sha256`.

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
    fetched_chunks = await asyncio.gather(
        *(engine.list_chunks(kb_id, did) for did in doc_ids),
        return_exceptions=True,
    )

    chunks_by_doc: dict[str, list[dict]] = {}
    fetch_errors: list[str] = []
    for did, result in zip(doc_ids, fetched_chunks):
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
        img.checksum_sha256
        for img in citation.embedded_images
        if img.checksum_sha256
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
    """BUG-027 — section-aware variant of `_find_neighbour_images`.

    Attaches images from chunks in the SAME section as the citation (matched by
    `section_path[:section_path_prefix_depth]`), ignoring chunk-index window
    proximity — so ALL §8.* scenario figures surface under a §8 intro citation,
    not only the two inside ±window. Candidates are ordered nearest-first by
    chunk-index distance for a deterministic cap (closest siblings win when
    capped); images are deduped against the citation's own images + each other;
    capped at max_aux. Returns [] when the citation's section_path is shorter
    than the requested prefix depth (no stable section key to match on).

    Pure function; no IO; testable in isolation without mocks.
    """
    cited_prefix = list(citation.section_path[:section_path_prefix_depth])
    if len(cited_prefix) < section_path_prefix_depth:
        return []

    own_checksums: set[str] = {
        img.checksum_sha256
        for img in citation.embedded_images
        if img.checksum_sha256
    }

    # Collect same-section candidates with chunk-index distance so the cap takes
    # the nearest sibling figures first (deterministic ordering, no IO).
    candidates: list[tuple[int, dict]] = []
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
        candidates.append((abs(chunk_idx - citation.chunk_index), chunk))

    candidates.sort(key=lambda pair: pair[0])

    new_images: list[ImageRef] = []
    for _distance, chunk in candidates:
        images = parse_embedded_images(
            str(chunk.get("embedded_images_json", "") or ""),
        )
        for img in images:
            if not img.checksum_sha256:
                continue
            if img.checksum_sha256 in own_checksums:
                continue
            own_checksums.add(img.checksum_sha256)
            new_images.append(img)
            if len(new_images) >= max_aux:
                return new_images

    return new_images
