"""Post-hoc citation expansion per W31 F1.2 — (B'.c) cite-confidence threshold relax.

Synthesizer 出完 cite 之後 backend 自動 inspect ±N neighbor chunks(same doc,within
score threshold + §X.M title pattern)→ auto-insert `[chunk-{neighbor_id}]` markers
after existing citations。Goal:即使 LLM cite-decision biased toward intro chunks,
backend 自動 expand 補 specific walkthrough chunks。

Per W31 plan §1 axis 3:operates on top-K reranked chunks(no additional Azure Search
fetch — surgical scope per Karpathy §1.2 simplicity);parallel pattern to W25 F5 D1
`citation_image_neighbors.py`(images),but targets citation chunks not images。

Per W31 plan §3 G6 Q4 measurement-experiment-fail-policy:default `enable_citation_
post_hoc_expansion=True` for measurement(per Karpathy §1.4 goal-driven「make it
pass」requires axis enabled);F4 closeout will decide preserve / revert。

Algorithm:
1. For each existing `[chunk-{id}]` marker in answer_text:
   - Look up cited chunk in `chunks` (top-K reranked set,already retrieved)
   - Find ±window chunk_index neighbors in same doc within `chunks` list
   - Filter:NOT already cited + rerank score ≥ threshold + title regex ``§\\d+\\.\\d+``
   - Pick top `max_aux` by absolute chunk_index distance
2. Group additions by after_id;build replacement string `[chunk-A][chunk-N1][chunk-N2]`
3. Apply single str.replace(marker, new_marker, 1) per after_id(only first occurrence)
4. Re-extract citation_ids from expanded text to return ordered final list
"""

from __future__ import annotations

import re

import structlog

from retrieval.retrieval_engine import RetrievedChunk
from storage.settings import Settings

logger = structlog.get_logger(__name__)

_CITATION_PATTERN = re.compile(r"\[chunk-([^\]\s]+)\]")
_SECTION_NUMBER_PATTERN = re.compile(r"§\d+\.\d+")


def _extract_citation_ids(answer_text: str) -> list[str]:
    """Return ordered unique chunk_ids from `[chunk-{id}]` markers."""
    seen: list[str] = []
    for m in _CITATION_PATTERN.finditer(answer_text):
        cid = m.group(1).strip()
        if cid and cid not in seen:
            seen.append(cid)
    return seen


def expand_citations(
    answer_text: str,
    citation_ids: list[str],
    chunks: list[RetrievedChunk],
    *,
    settings: Settings,
) -> tuple[str, list[str]]:
    """Auto-add neighbor chunk citations to answer_text per W31 (B'.c) post-hoc expansion.

    Returns (expanded_answer_text, expanded_citation_ids). When
    `settings.enable_citation_post_hoc_expansion=False`,returns inputs unchanged
    (backward-compat preserved per W31 plan §2 F1.4.c).

    Pure function:no IO,no async,testable in isolation。

    Per W31 plan §2 F1.2 algorithm:
    - Top-K reranked chunks already in `chunks` list (no engine fetch)
    - ±window chunk_index in same doc
    - Filter:rerank score ≥ threshold + title regex `§\\d+\\.\\d+`
    - Cap `max_aux` per existing citation
    """
    if not settings.enable_citation_post_hoc_expansion:
        return answer_text, citation_ids

    if not citation_ids or not chunks:
        return answer_text, citation_ids

    # Build chunk lookup by chunk_id for O(1) access
    chunk_by_id: dict[str, RetrievedChunk] = {}
    for chunk in chunks:
        cid = str(chunk.fields.get("chunk_id", ""))
        if cid:
            chunk_by_id[cid] = chunk

    # additions_by_after: cited_id → ordered list of neighbor_ids to insert after it
    additions_by_after: dict[str, list[str]] = {}
    added_ids: set[str] = set(citation_ids)

    for cited_id in citation_ids:
        cited_chunk = chunk_by_id.get(cited_id)
        if cited_chunk is None:
            # Defensive:LLM cited a chunk_id not in retrieved set (rare,but
            # possible if synthesizer hallucinated despite Rule 5 — skip silently)
            continue

        cited_doc_id = str(cited_chunk.fields.get("doc_id", ""))
        if not cited_doc_id:
            continue

        cited_idx_raw = cited_chunk.fields.get("chunk_index", 0)
        try:
            cited_idx = int(cited_idx_raw) if cited_idx_raw is not None else 0
        except (TypeError, ValueError):
            continue

        # Find neighbor candidates in chunks list (same top-K reranked set)
        neighbor_candidates: list[tuple[int, str]] = []  # (abs_distance, neighbor_id)
        for candidate in chunks:
            cand_id = str(candidate.fields.get("chunk_id", ""))
            if not cand_id or cand_id in added_ids:
                continue
            cand_doc_id = str(candidate.fields.get("doc_id", ""))
            if cand_doc_id != cited_doc_id:
                continue

            cand_idx_raw = candidate.fields.get("chunk_index", 0)
            try:
                cand_idx = int(cand_idx_raw) if cand_idx_raw is not None else 0
            except (TypeError, ValueError):
                continue

            distance = abs(cand_idx - cited_idx)
            if distance == 0 or distance > settings.citation_expansion_window:
                continue

            if candidate.score < settings.citation_expansion_score_threshold:
                continue

            cand_title = str(candidate.fields.get("chunk_title", "") or "")
            if not _SECTION_NUMBER_PATTERN.search(cand_title):
                continue

            neighbor_candidates.append((distance, cand_id))

        # Sort by absolute distance ascending,take top max_aux
        neighbor_candidates.sort(key=lambda pair: pair[0])
        chosen = [
            neighbor_id
            for _, neighbor_id in neighbor_candidates[: settings.citation_expansion_max_aux]
        ]

        if chosen:
            additions_by_after[cited_id] = chosen
            added_ids.update(chosen)

    # Apply text insertions:after each `[chunk-{cited_id}]` marker
    expanded_text = answer_text
    for after_id, new_ids in additions_by_after.items():
        marker = f"[chunk-{after_id}]"
        new_marker = marker + "".join(f"[chunk-{nid}]" for nid in new_ids)
        # Replace only first occurrence to avoid double-expansion if cited_id appears
        # multiple times in answer_text (e.g. repeated supporting cite)
        expanded_text = expanded_text.replace(marker, new_marker, 1)

    # Re-extract ordered citation_ids from expanded text
    expanded_citation_ids = _extract_citation_ids(expanded_text)

    logger.info(
        "citation_expansion_applied",
        original_citation_count=len(citation_ids),
        expanded_citation_count=len(expanded_citation_ids),
        added_count=len(expanded_citation_ids) - len(citation_ids),
        cited_chunks_expanded=len(additions_by_after),
        window=settings.citation_expansion_window,
        score_threshold=settings.citation_expansion_score_threshold,
        max_aux=settings.citation_expansion_max_aux,
    )

    return expanded_text, expanded_citation_ids
