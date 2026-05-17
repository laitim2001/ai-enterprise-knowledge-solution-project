"""Listing schemas for KB documents + chunks (per architecture.md §4.4 #9-10 + §3.5).

W16 F5.1 CO_F3a closure — replace 501 stubs in `routes/documents.py` +
`routes/chunks.py` via Azure AI Search index aggregation. Schemas surface
Beta-relevant fields only (chunk_text + embedded_images excluded — Beta
client doesn't need bulk text in listing endpoints; use /query for text).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class DocumentSummary(BaseModel):
    """Doc-level metadata aggregated from chunks per kb_id (per F5.1.1)."""

    doc_id: str
    doc_title: str
    doc_format: str
    total_chunks: int
    last_indexed_at: str  # ISO datetime; max(ingested_at) across observed chunks
    source_url: str | None = None
    tags: list[str] = []


class ChunkSummary(BaseModel):
    """Chunk-level metadata for doc detail view (per F5.1.2; chunk_text excluded)."""

    chunk_id: str
    chunk_index: int
    chunk_total: int
    chunk_title: str
    section_path: list[str] = []
    enabled: bool = True
    low_value_flag: bool = False


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
