"""KB Pydantic schemas (per architecture.md §4.5; W20 F4.1 — Multimodal Tier 1 fields per ADR-0028)."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class KbConfig(BaseModel):
    """KB-level configuration. The W2 baseline (`embedding_*`, `chunk_strategy`,
    `default_top_k`, `default_rerank_k`) is augmented in W20 F4.1 with 4 Tier 1
    multimodal flags surfaced by the `/kb/new` Step-4 wizard (per ADR-0028 +
    architecture.md v6 §5.5.3):

    * `extract_embedded_images` — gate the W2 F3 screenshot-extraction step at
      ingest time. `True` reproduces the W2 default; `False` skips extraction
      entirely (no `ScreenshotExtractor.extract` call) so a text-only KB can
      ingest faster.
    * `slide_screenshots` — applies to PPT ingestion;`True` keeps slide-level
      screenshot generation (current default), `False` would skip. Wiring to
      the PPT parser is a forward-compat seam (R12 — uploader=None today, so
      this flag is a no-op until the screenshot pipeline ships full ingest).
    * `dedup_strategy` — image SHA-256 dedup behaviour. `"sha256"` matches the
      W2 baseline (uploader returns `deduped=True` for duplicate blobs);
      `"none"` would re-upload duplicates (forward-compat seam).
    * `return_images_in_chat` — a *query-time* read by the chat surface to
      decide whether to render `InlineImageCard` / `ImageGallery` for this KB.
      Persisted via this config; not used by the ingestion orchestrator.
    """

    embedding_model: str = "text-embedding-3-large"
    embedding_dimension: int = 1024
    chunk_strategy: Literal["heading_aware", "layout_aware", "slide_based", "auto"] = "auto"
    default_top_k: int = 50
    default_rerank_k: int = 5

    # W20 F4.1 — Multimodal Tier 1 fields (per ADR-0028 + architecture.md §5.5.3).
    # Defaults match the plan literal — `False` for the opt-in extraction so a
    # text-only KB doesn't pay the screenshot cost. The wizard surfaces these as
    # explicit toggles so the KB owner picks intent at creation.
    extract_embedded_images: bool = False
    slide_screenshots: bool = True
    dedup_strategy: Literal["sha256", "none"] = "sha256"
    return_images_in_chat: bool = False


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


class KbMetadataPatch(BaseModel):
    """PATCH /kb/{kb_id} input — KB metadata partial update (W16 F5.2 CO_F3b).

    Per Decision A.1 (separation of concern): metadata = name + description;
    config remains in PATCH /kb/{kb_id}/settings (KbConfig-only). All fields
    Optional for partial PATCH (omitted = preserve existing value).
    """

    name: str | None = None
    description: str | None = None


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
