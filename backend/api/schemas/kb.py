"""KB Pydantic schemas (per architecture.md §4.5; W20 F4.1 — Multimodal Tier 1 fields per ADR-0028)."""

import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


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

    # W43 F1.1 — per-KB tunable retrieval / citation runtime knobs (per ADR-0040).
    # These mirror the global `Settings` defaults that currently drive parent-doc
    # retrieval (§3.1), post-hoc citation expansion (§3.7), and neighbour-image
    # attach (ADR-0034). Every field is `Optional` with a `None` default meaning
    # "inherit the global Settings value" — so an existing KB persisted before W43
    # (whose JSONB config lacks these keys) reconstructs with all `None` and behaves
    # bit-identical to today (zero breaking change, ADR-0028 migration-default
    # precedent). `EffectiveConfig` (generation/effective_config.py) resolves the
    # live value at request entry as per-query override > per-KB (this) > global.
    #
    # Image flood mitigation note (per ADR-0040 + BUG-031): `max_images_per_answer`
    # is the BACKEND per-KB version of the BUG-031 frontend `INLINE_IMAGE_CAP=8`.
    # `None` = no backend cap (frontend display cap handles flood); set a value to
    # cap the total images returned across an answer's citations at the payload
    # level. The two live in different layers — backend per-KB cap takes precedence,
    # frontend cap is the fallback when this is `None`.
    enable_parent_doc_retrieval: bool | None = None
    parent_doc_section_depth_offset: int | None = None
    parent_doc_top_k: int | None = None
    parent_doc_max_tokens_per_parent: int | None = None
    enable_citation_post_hoc_expansion: bool | None = None
    citation_expansion_max_aux: int | None = None
    citation_expansion_window: int | None = None
    citation_expansion_section_path_prefix_depth: int | None = None
    enable_citation_neighbour_images: bool | None = None
    citation_neighbour_max_aux_images: int | None = None
    citation_neighbour_section_path_prefix_depth: int | None = None
    max_images_per_answer: int | None = None
    # CH-010 / ADR-0047 — pin the dominant chapter's §X.1 "Overview" figures to the
    # front of the lead citation (before the image cap) so a procedural answer leads
    # with the chapter overview/flow diagram. `None` = inherit global Settings
    # (default False). Per-KB opt-in for image-heavy procedural manuals.
    enable_chapter_overview_pin: bool | None = None

    # W45 — per-KB ingest-time chunker image cap (per ADR-0042; extends the
    # ADR-0040 config-scope model from query-time to INGEST-time). Mirrors the
    # global `Settings.chunker_max_images_per_chunk` (W44 / ADR-0041, default 8)
    # that drives the LayoutAwareChunker force-split. Semantics differ from the
    # W43 retrieval knobs by ONE deliberate choice (Chris pick 2026-06-04):
    #   * None        → inherit the global `Settings` cap (default 8).
    #   * positive int→ this KB's per-chunk image cap (force-split at N).
    # A per-KB KB CANNOT express "no cap" (the pre-W44 whole-section pile-on):
    # `None` is the inherit sentinel here, but the chunker's own
    # `max_images_per_chunk=None` already means "no cap" — the two `None`s
    # collide, so the no-cap escape stays GLOBAL-only (`CHUNKER_MAX_IMAGES_PER_CHUNK=null`).
    # Resolved at INGEST time in `documents.py:_run_ingest_pipeline` (NOT via the
    # query-time `EffectiveConfig`); `None` reuses the global chunker singleton so
    # an existing KB persisted before W45 reconstructs bit-identical (G7
    # production-preserve, ADR-0028/0040 migration-default precedent). Re-index
    # required for a change to take effect (cap is consumed at chunk time).
    chunker_max_images_per_chunk: int | None = None

    # CH-006 — per-KB synthesis answer detail level (extends ADR-0040 config-scope
    # to the GENERATION stage). `None` = inherit global `Settings.synthesis_answer_detail`
    # (default "concise" = W2 baseline prompt_builder Rule 3 150-word cap → zero
    # behaviour change for existing KBs). "detailed" = relaxed Rule 3 (no word cap,
    # enumerate every sub-step) so a procedural-manual KB reproduces the full source
    # procedure instead of a summary. Resolved query-time via `EffectiveConfig`
    # (NOT a re-index knob — synthesis is read at /query + /query/stream).
    answer_detail: Literal["concise", "detailed"] | None = None

    # W70 (ADR-0055) — per-KB inline image markers gate. `None` = inherit global
    # `Settings.enable_inline_image_markers` (default False = clean-text prompts,
    # zero behaviour change). True = this KB's synthesis prompts consume the
    # `chunk_text_marked` variant ([IMG#sha8] markers) + system rule, so answers
    # carry position markers for the W70 strip / W71 interleaved render. Query-time
    # knob (no re-index needed to flip — the marked field is written at ingest
    # unconditionally, but the KB's index must HAVE the field populated for ON to
    # surface markers; un-re-indexed KBs degrade gracefully to clean text).
    enable_inline_image_markers: bool | None = None

    # W75 (ADR-0056 段②d) — per-KB section-anchored aux images gate. `None` = inherit
    # global `Settings.enable_section_anchored_aux_images` (default False = trailing pile
    # unchanged). True = this KB's un-anchored neighbour / aux images get a marker injected
    # at their same-section anchored marker post-synthesis, so the frontend renders them
    # interleaved (方案 A). Query-time knob (no re-index). Profile-routed ON for
    # P1_sop_imgdense (W73 PROFILE_PRESETS).
    enable_section_anchored_aux_images: bool | None = None

    # W75 F5 (ADR-0056 段②d) — per-KB per-anchor injection cap. `None` = inherit global
    # `Settings.section_anchor_max_per_anchor` (default 0 = no cap). N > 0 caps the
    # per-chapter injection at N (doc_order first N) to bound clump.
    section_anchor_max_per_anchor: int | None = None


# kb_id forms BOTH the AI Search index name (`ekp-kb-{kb_id}-v1`) AND the Azure
# Blob container names (`ekp-kb-{kb_id}-screenshots` / `-sources`). Blob container
# naming is the stricter of the two: lowercase alphanumerics separated by SINGLE
# dashes only — no leading/trailing/consecutive dashes, no underscores. A kb_id
# violating this (e.g. "a---b" from a "A - B" name) indexes chunks fine but 500s
# (InvalidResourceName) at the first screenshot/source blob op during ingest or
# reindex. Validated at create time so the failure is an actionable 422 up front.
_KB_ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

# ADR-0018 legacy alias: kb_id="drive_user_manuals" maps to FIXED legacy container
# names (ekp-kb-drive-screenshots), NOT the derived ekp-kb-{kb_id}-* pattern, so its
# underscore is Blob-safe. The sole id exempt from _KB_ID_RE. Mirrors
# storage.kb_naming._LEGACY_KB_ID.
_LEGACY_KB_ID = "drive_user_manuals"


class KbCreate(BaseModel):
    """POST /kb input (per architecture.md §4.4 #5).

    `kb_id` is client-supplied; it forms the AI Search index name
    `ekp-kb-{kb_id}-v1` AND the Azure Blob container names
    `ekp-kb-{kb_id}-screenshots` / `-sources`. Must be Blob-container-safe:
    lowercase a-z / 0-9 separated by single dashes (no leading, trailing, or
    consecutive dashes, and no underscores).
    """

    kb_id: str
    name: str
    description: str = ""
    config: KbConfig = Field(default_factory=KbConfig)

    @field_validator("kb_id")
    @classmethod
    def _validate_kb_id(cls, v: str) -> str:
        if v == _LEGACY_KB_ID:
            return v  # ADR-0018 legacy alias — fixed legacy containers, Blob-safe
        if not 2 <= len(v) <= 40:
            raise ValueError("kb_id must be 2-40 characters long")
        if not _KB_ID_RE.fullmatch(v):
            raise ValueError(
                "kb_id must be lowercase a-z / 0-9 separated by single dashes "
                "(no leading, trailing, or consecutive dashes, and no underscores) - "
                "it becomes the Azure Blob container name ekp-kb-{kb_id}-screenshots"
            )
        return v


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
    # W20 F5.1 — archive soft-state per ADR-0025. Archived KBs survive in storage
    # (search index + screenshot blobs preserved) but `documents.py` upload/reindex
    # routes return 403 so the KB freezes from the user's perspective. Default
    # False keeps every existing record + every existing test path unchanged.
    archived: bool = False
