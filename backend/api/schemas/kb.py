"""KB Pydantic schemas (per architecture.md §4.5)."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class KbConfig(BaseModel):
    embedding_model: str = "text-embedding-3-large"
    embedding_dimension: int = 1024
    chunk_strategy: Literal["heading_aware", "layout_aware", "slide_based", "auto"] = "auto"
    default_top_k: int = 50
    default_rerank_k: int = 5


class KbCreate(BaseModel):
    """POST /kb input (per architecture.md §4.4 #5).

    `kb_id` is client-supplied; per §3.4 it forms the AI Search index name
    `ekp-kb-{kb_id}-v{version}`, so callers must keep it index-name-safe
    (lowercase, hyphen/underscore only).
    """

    kb_id: str
    name: str
    description: str = ""
    config: KbConfig = Field(default_factory=KbConfig)


class FailureRecord(BaseModel):
    doc_id: str
    error: str
    failed_at: datetime


class KbStatus(BaseModel):
    kb_id: str
    name: str
    description: str
    config: KbConfig
    total_documents: int
    total_chunks: int
    total_screenshots: int
    failed_documents: list[FailureRecord]
    last_indexed_at: datetime
    storage_size_mb: float
