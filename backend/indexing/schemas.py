"""ChunkRecord + ImageRef Pydantic schemas (per architecture.md §3.5 + §3.6).

ChunkRecord is the unified emit format from C01 ingestion pipeline (orchestrator)
to C03 indexing (populate). Field set is 1:1 with architecture.md §3.5 JSON
literal — Azure AI Search index `ekp-kb-drive-v1` schema is the same set
serialized via index field config (architecture.md §3.6).

Why Pydantic (not @dataclass like ChunkSpec):
- This IS the API/storage boundary — validation matters.
- Azure AI Search REST API consumes the JSON shape directly, so Pydantic's
  model_dump_json output IS what we POST to /docs/index.
- Per CLAUDE.md §3.1 — Pydantic v2 for all schemas.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ImageRef(BaseModel):
    """Resolved embedded image reference (post F3 Blob upload)."""

    blob_url: str
    alt_text: str = ""
    checksum_sha256: str
    width: int = 0
    height: int = 0


def make_chunk_id(kb_id: str, doc_id: str, chunk_index: int) -> str:
    """Stable chunk_id factory per architecture.md §3.5 example.

    Format: kb-{kb_id}_doc-{doc_id}_chunk-{idx:04d}
    Reserved characters in kb_id/doc_id (e.g. underscore in kb_id) preserved.
    """
    return f"kb-{kb_id}_doc-{doc_id}_chunk-{chunk_index:04d}"


class ChunkRecord(BaseModel):
    """Final emit per architecture.md §3.5. Direct serialize to AI Search index doc."""

    chunk_id: str
    kb_id: str
    doc_id: str
    doc_title: str
    doc_format: Literal["docx", "pdf", "pptx"]
    chunk_index: int
    chunk_total: int
    chunk_title: str
    chunk_text: str
    chunk_token_count: int
    section_path: list[str] = Field(default_factory=list)
    embedded_images: list[ImageRef] = Field(default_factory=list)
    prev_chunk_id: str | None = None
    next_chunk_id: str | None = None
    tags: list[str] = Field(default_factory=list)
    low_value_flag: bool = False
    enabled: bool = True
    source_url: str = ""
    ingested_at: datetime
    embedding: list[float] = Field(..., min_length=1)

    def to_search_doc(self) -> dict:
        """Serialize to Azure AI Search /docs/index payload shape.

        Two adjustments vs raw model_dump:
        - `embedded_images` flattened to `embedded_images_json` per §3.6 schema
          (Edm.String retrievable; we serialize image list as JSON string).
        - `embedding` field renamed to `content_vector` per §3.6 vector field name.
        - `ingested_at` ISO 8601 string (Azure AI Search Edm.DateTimeOffset).
        """
        import json as _json

        data = self.model_dump(mode="json")
        data["embedded_images_json"] = _json.dumps(
            data.pop("embedded_images"), ensure_ascii=False,
        )
        data["content_vector"] = data.pop("embedding")
        return data
