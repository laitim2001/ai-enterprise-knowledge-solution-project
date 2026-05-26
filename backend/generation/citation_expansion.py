"""Engine-fetch post-hoc citation expansion per W32 (h') single-axis ship.

Per W31 retro HIGHEST candidate (h') — escapes W31 F2 v3 R6 catch (3) `window=3`
architectural constraint by fetching FULL doc chunks via async `engine.list_chunks`
instead of operating on top-K reranked subset。Goal:expansion CAN fire regardless
of reformulator stochasticity surfacing §X.M walkthroughs in top-K reranked set。

Per W32 plan §1 sequential ship strategy locked — single-axis (h') ship,no concurrent
prompt change(Rule 7 v2 + Rule 8 reverted per W31 F4)。Attribution clean。

Mirror W25 F5 D1 `citation_image_neighbors.py` `attach_neighbour_images` pattern:
- async signature accepting `engine: RetrievalEngine + kb_id: str`
- group cited chunks by doc_id + parallel `asyncio.gather` per-doc fetch
- graceful per-doc failure(other docs continue;log warning)
- pure `_find_neighbour_chunks` private helper(no IO,no async)testable in isolation
- dedupe against existing citation_ids + max_aux cap closer-preferred

Algorithm:
1. For each `[chunk-{id}]` marker in answer_text → look up cited chunk in `chunks`
   (top-K reranked,for `doc_id` + `chunk_index` lookup ONLY)
2. Group cited chunks by unique `doc_id`
3. Parallel `asyncio.gather` `engine.list_chunks(kb_id, doc_id)` per unique doc
4. For each cited chunk + its doc's full chunk list:
   - Find chunks within ±window of cited chunk_index(EXCLUDING self + already cited)
   - Filter to chunks with title regex `\\b\\d+\\.\\d+\\b`(corpus-validated bare +
     §-prefix pattern per W31 PC-W31-1 lesson)
   - Sort by absolute distance + take top `max_aux`
5. Group additions by `after_id`;build replacement string `[chunk-A][chunk-N1][chunk-N2]`
6. Apply single `str.replace(marker, new_marker, 1)` per `after_id`(first occurrence only)
7. Re-extract `citation_ids` from expanded text → ordered final list

Per W31 PC-W31-2 lesson:NO `score_threshold` field — `engine.list_chunks` returns
raw Azure Search chunks without rerank score(filter not applicable)。
"""

from __future__ import annotations

import asyncio
import re
from typing import Any

import structlog

from retrieval.retrieval_engine import RetrievalEngine, RetrievedChunk
from storage.settings import Settings

logger = structlog.get_logger(__name__)

_CITATION_PATTERN = re.compile(r"\[chunk-([^\]\s]+)\]")
_SECTION_NUMBER_PATTERN = re.compile(r"\b\d+\.\d+\b")


def _extract_citation_ids(answer_text: str) -> list[str]:
    """Return ordered unique chunk_ids from `[chunk-{id}]` markers."""
    seen: list[str] = []
    for m in _CITATION_PATTERN.finditer(answer_text):
        cid = m.group(1).strip()
        if cid and cid not in seen:
            seen.append(cid)
    return seen


def _find_neighbour_chunks(
    cited_chunk_index: int,
    cited_doc_id: str,
    doc_chunks: list[dict[str, Any]],
    *,
    already_cited: set[str],
    window: int,
    max_aux: int,
) -> list[str]:
    """Walk full doc chunks within chunk_index ±window of cited,filter §X.M title,cap max_aux。

    Pure function;no IO,no async;testable in isolation without engine。Parallel to
    W25 F5 D1 `_find_neighbour_images` line 135-186 pattern。

    Returns ordered list of neighbor chunk_ids sorted by absolute distance ascending
    (closer chunks preferred when max_aux cap binds)。
    """
    if max_aux <= 0 or window <= 0:
        return []

    candidates: list[tuple[int, str]] = []  # (absolute_distance, chunk_id)
    for chunk in doc_chunks:
        cand_id = str(chunk.get("chunk_id", ""))
        if not cand_id or cand_id in already_cited:
            continue

        chunk_idx_raw = chunk.get("chunk_index", 0)
        try:
            chunk_idx = int(chunk_idx_raw) if chunk_idx_raw is not None else 0
        except (TypeError, ValueError):
            continue

        distance = abs(chunk_idx - cited_chunk_index)
        if distance == 0 or distance > window:
            continue

        cand_title = str(chunk.get("chunk_title", "") or "")
        if not _SECTION_NUMBER_PATTERN.search(cand_title):
            continue

        candidates.append((distance, cand_id))

    # Sort by absolute distance ascending,take top max_aux
    candidates.sort(key=lambda pair: pair[0])
    return [cand_id for _, cand_id in candidates[:max_aux]]


async def expand_citations(
    answer_text: str,
    citation_ids: list[str],
    chunks: list[RetrievedChunk],
    *,
    engine: RetrievalEngine,
    kb_id: str,
    settings: Settings,
) -> tuple[str, list[str]]:
    """Auto-add neighbor chunk citations to answer_text via engine.list_chunks full-doc fetch。

    Returns (expanded_answer_text, expanded_citation_ids). When
    `settings.enable_citation_post_hoc_expansion=False` OR `engine is None` OR
    `kb_id is None` OR empty inputs,returns inputs unchanged(backward compat
    preserved per W32 plan §2 F1.1.d + F1.4.b)。

    Async — fetches full doc chunks via `engine.list_chunks(kb_id, doc_id)` per
    unique cited doc;parallel `asyncio.gather` per-doc fetch with graceful
    per-doc failure(W25 F5 D1 line 71-92 pattern)。

    Per W32 plan §2 F1.2 algorithm — escapes W31 window=3 constraint by fetching
    FROM FULL DOC not top-K reranked subset。Reformulator stochasticity surfacing
    different sections in top-K no longer limits expansion candidates。
    """
    if not settings.enable_citation_post_hoc_expansion:
        return answer_text, citation_ids

    if not citation_ids or not chunks:
        return answer_text, citation_ids

    # Build chunk lookup by chunk_id for O(1) doc_id + chunk_index access
    chunk_by_id: dict[str, RetrievedChunk] = {}
    for chunk in chunks:
        cid = str(chunk.fields.get("chunk_id", ""))
        if cid:
            chunk_by_id[cid] = chunk

    # Group cited chunks by unique doc_id (one fetch per doc covers all cited chunks
    # from same doc — parallel pattern to W25 F5 D1 line 65-66)
    cited_by_doc: dict[str, list[tuple[str, int]]] = {}  # doc_id → [(cited_id, cited_idx)]
    for cited_id in citation_ids:
        cited_chunk = chunk_by_id.get(cited_id)
        if cited_chunk is None:
            # LLM hallucinated chunk_id not in retrieved set (Rule 5 violation) — skip
            continue

        cited_doc_id = str(cited_chunk.fields.get("doc_id", ""))
        if not cited_doc_id:
            continue

        cited_idx_raw = cited_chunk.fields.get("chunk_index", 0)
        try:
            cited_idx = int(cited_idx_raw) if cited_idx_raw is not None else 0
        except (TypeError, ValueError):
            continue

        cited_by_doc.setdefault(cited_doc_id, []).append((cited_id, cited_idx))

    if not cited_by_doc:
        return answer_text, citation_ids

    # Parallel fetch full doc chunk lists per unique doc — W25 F5 D1 line 71-74 pattern
    doc_ids = sorted(cited_by_doc.keys())
    fetched_chunks = await asyncio.gather(
        *(engine.list_chunks(kb_id, did) for did in doc_ids),
        return_exceptions=True,
    )

    chunks_by_doc: dict[str, list[dict[str, Any]]] = {}
    fetch_errors: list[str] = []
    for did, result in zip(doc_ids, fetched_chunks, strict=True):
        if isinstance(result, BaseException):
            fetch_errors.append(f"{did}: {type(result).__name__}: {result}")
            chunks_by_doc[did] = []
            continue
        chunks_by_doc[did] = result

    if fetch_errors:
        # Graceful degradation per W25 F5 D1 line 86-92 pattern — log + skip that doc's
        # expansion (don't fail entire request because one doc list_chunks 500'd)
        logger.warning(
            "citation_expansion_doc_chunk_fetch_failed",
            errors=fetch_errors,
        )

    # additions_by_after: cited_id → ordered list of neighbor_ids to insert after it
    additions_by_after: dict[str, list[str]] = {}
    added_ids: set[str] = set(citation_ids)

    for doc_id, cited_pairs in cited_by_doc.items():
        doc_chunks = chunks_by_doc.get(doc_id, [])
        if not doc_chunks:
            continue

        for cited_id, cited_idx in cited_pairs:
            chosen = _find_neighbour_chunks(
                cited_chunk_index=cited_idx,
                cited_doc_id=doc_id,
                doc_chunks=doc_chunks,
                already_cited=added_ids,
                window=settings.citation_expansion_window,
                max_aux=settings.citation_expansion_max_aux,
            )

            if chosen:
                additions_by_after[cited_id] = chosen
                added_ids.update(chosen)

    # Apply text insertions:after each `[chunk-{cited_id}]` marker
    expanded_text = answer_text
    for after_id, new_ids in additions_by_after.items():
        marker = f"[chunk-{after_id}]"
        new_marker = marker + "".join(f"[chunk-{nid}]" for nid in new_ids)
        # Replace only first occurrence to avoid double-expansion if cited_id appears
        # multiple times in answer_text
        expanded_text = expanded_text.replace(marker, new_marker, 1)

    # Re-extract ordered citation_ids from expanded text
    expanded_citation_ids = _extract_citation_ids(expanded_text)

    logger.info(
        "citation_expansion_applied",
        kb_id=kb_id,
        original_citation_count=len(citation_ids),
        expanded_citation_count=len(expanded_citation_ids),
        added_count=len(expanded_citation_ids) - len(citation_ids),
        cited_chunks_expanded=len(additions_by_after),
        docs_fetched=len(doc_ids),
        fetch_errors=len(fetch_errors),
        window=settings.citation_expansion_window,
        max_aux=settings.citation_expansion_max_aux,
    )

    return expanded_text, expanded_citation_ids
