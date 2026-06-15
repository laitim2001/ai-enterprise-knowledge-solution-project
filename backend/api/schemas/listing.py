"""Listing schemas for KB documents + chunks (per architecture.md §4.4 #9-10 + §3.5).

W16 F5.1 CO_F3a closure — replace 501 stubs in `routes/documents.py` +
`routes/chunks.py` via Azure AI Search index aggregation. Schemas surface
Beta-relevant fields only (chunk_text + embedded_images excluded — Beta
client doesn't need bulk text in listing endpoints; use /query for text).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from api.schemas.doc_profile import DocProfileInfo
from api.schemas.query import ImageRef


class DocumentSummary(BaseModel):
    """Doc-level metadata aggregated from chunks per kb_id (per F5.1.1)."""

    doc_id: str
    doc_title: str
    doc_format: str
    total_chunks: int
    last_indexed_at: str  # ISO datetime; max(ingested_at) across observed chunks
    source_url: str | None = None
    tags: list[str] = []
    # W76 / ADR-0056 層 A 段③ 前置 — lightweight profile surface for the L2 doc-list
    # badge. Full signals live on DocumentDetail.profile; here only label + confidence
    # (avoid倒 the 13-field signal bundle into a list payload). None = not profiled.
    profile: str | None = None  # DocProfile label (e.g. "P1_sop_imgdense")
    profile_confidence: float | None = None  # 0–1


class ChunkSummary(BaseModel):
    """Chunk-level metadata for doc detail view (per F5.1.2; chunk_text excluded).

    BUG-016 (W25 D2) — adds `embedded_image_count` count-only field so the W20
    Document Detail 3-pane (ADR-0029) Chunks panel can mark `[with images]`
    affordance per chunk. Bulk `embedded_images_json` JSON string remains
    excluded per W16 F5.1.2 listing-payload bulk-exclusion intent — count is
    backend-cheap (derived from already-fetched JSON length), frontend-actionable
    (non-zero → render marker).
    """

    chunk_id: str
    chunk_index: int
    chunk_total: int
    chunk_title: str
    section_path: list[str] = []
    enabled: bool = True
    low_value_flag: bool = False
    embedded_image_count: int = 0  # BUG-016 — non-zero → frontend marks [with images]


# --------------------------------------------------------------------------- #
# W20 F5.2 — `/kb/{kb_id}/images` aggregation surface (per ADR-0025 +
# architecture.md v6 §5.5 KB Detail Tab 3 Images NEW).
# --------------------------------------------------------------------------- #


class KbImageItem(BaseModel):
    """One image as surfaced by `/kb/{kb_id}/images`.

    Aggregated from chunk-level `embedded_images_json` across the KB,
    deduplicated by `id` (= the SHA-256 checksum from the W2 F3 screenshot
    pipeline). Tier 1 doesn't yet carry `page_num` / `screenshot_type` (forward
    -compat seams — null today); `ocr_text` falls back to `alt_text` which the
    W2 F3 pipeline already populates with the image caption / surrounding text.
    """

    id: str            # checksum_sha256 (image identity)
    url: str           # blob_url
    doc_id: str
    doc_name: str      # doc_title from the host chunk
    page_num: int | None = None        # Tier 1: null — forward-compat seam
    ocr_text: str = ""                 # alt_text from ImageRef (W2 F3 capture)
    screenshot_type: str | None = None # Tier 1: null — forward-compat seam
    created_at: str | None = None      # Tier 1: null — host chunk's ingested_at not yet exposed via list_chunks


class KbImagesResponse(BaseModel):
    """Paginated list of `/kb/{kb_id}/images`."""

    items: list[KbImageItem]
    total: int
    limit: int
    offset: int


# --------------------------------------------------------------------------- #
# W21 F1 — `GET /kb/{kb_id}/docs/{doc_id}` enriched (per ADR-0029 Option C +
# architecture.md v6 §5.5.2a Document Detail page).
#
# Powers the 3-pane Doc Detail view (outline left + chunks center + inspector
# right). Schemas surface doc-level metadata + outline reconstruction from the
# layout-aware chunker's `section_path` field + image_refs aggregated from
# `embedded_images_json` (the W20 F5.2 + W17 F4.1 select-clause extension).
#
# Forward-compat seams (Tier 1 `None` per Karpathy §1.2 — wired when source data
# lands): `parse_duration_ms` + `embed_duration_ms` (F1.3 — ingestion result
# persistence Wave C+) / `size_kb` + `pages` + `language` / `total_tokens`
# (list_chunks doesn't surface chunk_token_count yet).
# --------------------------------------------------------------------------- #


class OutlineNode(BaseModel):
    """One heading in the doc outline reconstructed from chunk `section_path[]`.

    `level` = `len(section_path)` (1-indexed depth). `title` = `section_path[-1]`.
    `chunk_count` = number of chunks whose section_path matches this exact path.
    `page` is None for Tier 1 (page-number tracking is a forward-compat seam —
    the layout-aware chunker emits chunks without per-section page anchors today).
    """

    level: int
    title: str
    chunk_count: int
    page: int | None = None


class DocumentDetail(BaseModel):
    """`GET /kb/{kb_id}/docs/{doc_id}` enriched response per ADR-0029.

    Composed from `RetrievalEngine.list_documents(kb_id)` (doc-level row) +
    `RetrievalEngine.list_chunks(kb_id, doc_id)` (chunk-level aggregation for
    outline + image_refs + low_value count) + `KBService.get(kb_id)` (chunk_strategy
    from KbConfig).

    The 8 forward-compat seam fields (`source` / `size_kb` / `pages` / `language`
    / `total_tokens` / `parse_duration_ms` / `embed_duration_ms` + `page` on
    OutlineNode) carry `None` for Tier 1 — UI renders "—" + tooltip "Stage timing
    — Wave C+ instrumentation" (per ADR-0029 §3 + plan §2 F3.6 contract).
    """

    doc_id: str
    title: str                              # from list_documents `doc_title`
    source: str | None = None               # forward-compat seam — Wave C+
    source_url: str | None = None           # from list_documents row when ingestion captured it
    file_type: str                          # from list_documents `doc_format` (e.g. "docx", "pdf", "pptx")
    size_kb: int | None = None              # forward-compat seam — Wave C+
    pages: int | None = None                # forward-compat seam — Wave C+ (chunker doesn't track page totals)
    language: str | None = None             # forward-compat seam — Wave C+
    chunk_strategy: str | None = None       # from KbConfig.chunk_strategy when KB resolvable
    total_chunks: int                       # doc-level total from list_documents `total_chunks`
    total_images: int                       # unique image count post-SHA256 dedup
    total_tokens: int | None = None         # forward-compat seam — list_chunks doesn't surface chunk_token_count yet
    low_value_chunks: int                   # count of chunks with low_value_flag=True
    parse_duration_ms: int | None = None    # F1.3 forward-compat seam — ingestion result persistence Wave C+
    embed_duration_ms: int | None = None    # F1.3 forward-compat seam — ingestion result persistence Wave C+
    indexed_at: str                         # from list_documents `last_indexed_at` (ISO-8601 string)
    outline: list[OutlineNode]              # reconstructed from chunks' section_path[] (sorted)
    image_refs: list[ImageRef]              # aggregated from chunks' embedded_images_json (SHA256-deduped)
    # W76 / ADR-0056 層 A 段③ 前置 — full profile + signals for the L3「文件畫像」
    # section (transparent signal展示 + override). None = not profiled (re-index to populate).
    profile: DocProfileInfo | None = None


# --------------------------------------------------------------------------- #
# W20 F5.3 — POST `/chunking-preview` (per ADR-0025 KB Detail Tab 4 Chunking Lab).
# --------------------------------------------------------------------------- #


class ChunkingPreviewRequest(BaseModel):
    """`POST /chunking-preview` payload — preview chunks for a candidate config
    without persisting anything. Used by the KB Detail Tab 4 Chunking Lab.

    The Wave A implementation only consumes `sample_text` + `target_tokens`. The
    `sample_doc_id` field is accepted for forward-compat (Wave B+ wires a
    sample-doc re-parse path);when passed today the route returns a
    501-like 200 response with `note` explaining the limitation."""

    kb_id: str | None = None  # forward-compat — Wave A uses sample_text only
    sample_doc_id: str | None = None  # forward-compat — Wave A uses sample_text only
    sample_text: str = ""  # required for the Wave A path
    strategy: Literal["heading_aware", "layout_aware", "slide_based", "auto"] = "layout_aware"
    chunk_size: int = 700  # target_tokens for LayoutAwareChunker
    overlap: int = 0  # accepted for forward-compat — heading-bounded chunker is overlap-less


class ChunkingPreviewItem(BaseModel):
    """One preview chunk — same shape as the W2 ChunkSpec minus the embedding."""

    chunk_index: int
    chunk_title: str
    chunk_text: str
    chunk_token_count: int
    section_path: list[str] = []
    low_value_flag: bool = False


class ChunkingPreviewResponse(BaseModel):
    """`POST /chunking-preview` response — preview chunks + the config that
    produced them so the UI can echo the active settings back to the user."""

    items: list[ChunkingPreviewItem]
    total: int
    strategy: str
    chunk_size: int
    overlap: int
    note: str | None = None  # populated when the request landed in a forward-compat seam
