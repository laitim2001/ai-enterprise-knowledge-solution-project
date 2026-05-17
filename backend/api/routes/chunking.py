"""POST `/chunking-preview` — preview-only chunking for the KB Detail Chunking
Lab (W20 F5.3 per ADR-0025 + architecture.md v6 §5.5).

Why a stand-alone route + module: the existing `documents.py` route file owns
the *real* ingest pipeline (parse → chunk → embed → push); chunking-preview is
a parallel concern that runs *only* the chunker layer over a synthetic parser
result built from raw sample text. Separation per Karpathy §1.3 surgical.

Wave A scope (per plan F5.3 literal):
- Input shape covers `kb_id` + `sample_doc_id` + `sample_text` + `strategy` +
  `chunk_size` + `overlap`. Only `sample_text` is implemented end-to-end.
- `sample_doc_id` is a forward-compat seam — passing it returns 200 with the
  `note` field explaining the limitation (the Wave A route doesn't re-parse
  the doc from blob storage; that path arrives with the Wave B+ Azure Blob
  switch when the doc bytes are addressable again).
- `overlap` is accepted for forward-compat — the LayoutAwareChunker is
  heading-bounded (per the W2 baseline) and doesn't currently honour an
  overlap window. The field is echoed in the response so the UI can show the
  active value but the actual chunker call ignores it.
- `chunk_size` maps to LayoutAwareChunker.target_tokens.

Returns the preview chunks (no persist, no Azure index write). 422 when both
`sample_text` and `sample_doc_id` are empty.
"""

from __future__ import annotations

import structlog
from fastapi import APIRouter, HTTPException, status

from api.schemas.listing import (
    ChunkingPreviewItem,
    ChunkingPreviewRequest,
    ChunkingPreviewResponse,
)
from ingestion.chunker.layout_aware import LayoutAwareChunker
from ingestion.parsers.base import ParagraphItem, ParserResult

router = APIRouter()
logger = structlog.get_logger(__name__)


def _build_synthetic_parser_result(sample_text: str) -> ParserResult:
    """Turn raw sample text into a synthetic ParserResult for the chunker.

    Splits the text on blank-line paragraph boundaries; lines starting with
    `# ` / `## ` / `### ` (Markdown-style) are detected as headings so the
    chunker still produces section-bounded chunks. This is a Tier 1 preview
    affordance — the real ingest path runs Docling, which is much smarter.
    """
    paragraphs: list[ParagraphItem] = []
    raw_paragraphs = [block.strip() for block in sample_text.split("\n\n") if block.strip()]
    doc_order = 0
    for block in raw_paragraphs:
        first_line = block.splitlines()[0] if block else ""
        if first_line.startswith("### "):
            paragraphs.append(
                ParagraphItem(text=first_line[4:].strip(), kind="heading",
                              doc_order=doc_order, heading_level=3),
            )
            doc_order += 1
            body = "\n".join(block.splitlines()[1:]).strip()
            if body:
                paragraphs.append(ParagraphItem(text=body, kind="text", doc_order=doc_order))
                doc_order += 1
        elif first_line.startswith("## "):
            paragraphs.append(
                ParagraphItem(text=first_line[3:].strip(), kind="heading",
                              doc_order=doc_order, heading_level=2),
            )
            doc_order += 1
            body = "\n".join(block.splitlines()[1:]).strip()
            if body:
                paragraphs.append(ParagraphItem(text=body, kind="text", doc_order=doc_order))
                doc_order += 1
        elif first_line.startswith("# "):
            paragraphs.append(
                ParagraphItem(text=first_line[2:].strip(), kind="heading",
                              doc_order=doc_order, heading_level=1),
            )
            doc_order += 1
            body = "\n".join(block.splitlines()[1:]).strip()
            if body:
                paragraphs.append(ParagraphItem(text=body, kind="text", doc_order=doc_order))
                doc_order += 1
        else:
            paragraphs.append(ParagraphItem(text=block, kind="text", doc_order=doc_order))
            doc_order += 1

    # The synthetic source_path doesn't need to exist on disk — the chunker
    # only reads paragraphs/images/tables off the ParserResult dataclass.
    from pathlib import Path as _Path
    return ParserResult(
        source_path=_Path("synthetic-preview.txt"),
        doc_format="docx",
        doc_title="Chunking preview",
        paragraphs=paragraphs,
    )


@router.post("/chunking-preview", response_model=ChunkingPreviewResponse)
async def chunking_preview(body: ChunkingPreviewRequest) -> ChunkingPreviewResponse:
    """Preview chunks for a candidate config — no persistence."""
    if not body.sample_text and not body.sample_doc_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="provide `sample_text` (Wave A) or `sample_doc_id` (Wave B+)",
        )

    note: str | None = None
    if body.sample_doc_id and not body.sample_text:
        # Forward-compat seam — return an empty preview + an explicit note so
        # the UI can render a friendly message rather than a hard error.
        return ChunkingPreviewResponse(
            items=[],
            total=0,
            strategy=body.strategy,
            chunk_size=body.chunk_size,
            overlap=body.overlap,
            note=(
                "Sample-doc-id preview is a Wave B+ seam — pass `sample_text` "
                "to preview from raw text in Tier 1."
            ),
        )

    chunk_size = max(50, min(body.chunk_size, 4000))  # clamp for sanity
    chunker = LayoutAwareChunker(target_tokens=chunk_size)
    parser_result = _build_synthetic_parser_result(body.sample_text)

    try:
        specs = chunker.chunk(parser_result)
    except Exception as exc:  # noqa: BLE001 — preview never crashes the route
        logger.warning("chunking_preview_failed", error=f"{type(exc).__name__}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"chunker failed on the sample: {type(exc).__name__}: {exc}",
        ) from exc

    items = [
        ChunkingPreviewItem(
            chunk_index=spec.chunk_index,
            chunk_title=spec.chunk_title,
            chunk_text=spec.chunk_text,
            chunk_token_count=spec.chunk_token_count,
            section_path=list(spec.section_path),
            low_value_flag=spec.low_value_flag,
        )
        for spec in specs
    ]

    if body.overlap > 0:
        note = (
            "`overlap` accepted but ignored — Tier 1 LayoutAwareChunker is "
            "heading-bounded (no overlap window). Overlap arrives in Wave B+."
        )

    return ChunkingPreviewResponse(
        items=items,
        total=len(items),
        strategy=body.strategy,
        chunk_size=chunk_size,
        overlap=body.overlap,
        note=note,
    )
