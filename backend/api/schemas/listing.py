"""Listing schemas for KB documents + chunks (per architecture.md §4.4 #9-10 + §3.5).

W16 F5.1 CO_F3a closure — replace 501 stubs in `routes/documents.py` +
`routes/chunks.py` via Azure AI Search index aggregation. Schemas surface
Beta-relevant fields only (chunk_text + embedded_images excluded — Beta
client doesn't need bulk text in listing endpoints; use /query for text).
"""

from __future__ import annotations

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
