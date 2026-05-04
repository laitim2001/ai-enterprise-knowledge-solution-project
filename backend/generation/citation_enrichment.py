"""Citation enrichment per architecture.md §4.5 + §3.5 (W3 D2 F3).

Maps Synthesizer-emitted chunk_ids to full Citation records sourced from the
retrieved chunks. Pulls embedded_images list (parsed from the index field
`embedded_images_json`, an architecture.md §3.6 Edm.String JSON-encoded array).

W2 D3 R12 deferral note:
- F3 Blob upload is deferred to W7+ cloud Azure Blob, so embedded_images_json
  is currently `[]` for every populated chunk. parse_embedded_images() handles
  empty list gracefully — Citation.embedded_images = [].
- When real Blob URLs land post W7+, no F3 changes needed (already shape-correct).
"""

from __future__ import annotations

import json

import structlog

from api.schemas.query import Citation, ImageRef
from retrieval.retrieval_engine import RetrievedChunk

logger = structlog.get_logger(__name__)


def parse_embedded_images(json_str: str) -> list[ImageRef]:
    """Parse the index field `embedded_images_json` into ImageRef list.

    Returns [] for empty / null / malformed JSON (logged at warning level).
    """
    if not json_str:
        return []
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError:
        logger.warning("embedded_images_json_decode_failed", value=json_str[:120])
        return []
    if not isinstance(data, list):
        return []
    images: list[ImageRef] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        try:
            images.append(
                ImageRef(
                    blob_url=str(item.get("blob_url", "")),
                    alt_text=str(item.get("alt_text", "") or ""),
                    checksum_sha256=str(item.get("checksum_sha256", "") or ""),
                    width=int(item.get("width", 0) or 0),
                    height=int(item.get("height", 0) or 0),
                )
            )
        except (TypeError, ValueError):
            continue
    return images


def build_citations(
    citation_ids: list[str],
    retrieved_chunks: list[RetrievedChunk],
) -> list[Citation]:
    """Translate ordered citation_ids → Citation list using retrieved chunks.

    Citation order matches `citation_ids` (Synthesizer emit order = appearance
    in answer). chunk_ids cited but not in retrieved set are skipped — that
    indicates a hallucinated citation, logged for observability.
    """
    chunks_by_id: dict[str, RetrievedChunk] = {
        str(c.fields.get("chunk_id", "")): c for c in retrieved_chunks
    }
    citations: list[Citation] = []
    hallucinated_ids: list[str] = []
    for cid in citation_ids:
        chunk = chunks_by_id.get(cid)
        if chunk is None:
            hallucinated_ids.append(cid)
            continue
        f = chunk.fields
        citations.append(
            Citation(
                chunk_id=cid,
                doc_id=str(f.get("doc_id", "")),
                doc_title=str(f.get("doc_title", "")),
                chunk_title=str(f.get("chunk_title", "")),
                chunk_index=int(f.get("chunk_index", 0) or 0),
                section_path=list(f.get("section_path") or []),
                relevance_score=float(chunk.score),
                embedded_images=parse_embedded_images(
                    str(f.get("embedded_images_json", "") or "")
                ),
            )
        )
    if hallucinated_ids:
        logger.warning("citation_hallucinated_ids", ids=hallucinated_ids)
    return citations
