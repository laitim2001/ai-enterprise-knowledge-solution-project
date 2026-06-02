"""Config-test harness schemas (W43 F2, ADR-0040 §Decision 3).

The on-platform试跑 harness: preview a DRAFT (unsaved) per-KB retrieval/citation
config by running the full `/query` pipeline N times and aggregating presentation
counters (citation / figure raw+dedup) + latency with a variance band — so the KB
owner sees the config's effect before persisting it (and can A/B vs the saved one).
"""

from typing import Literal

from pydantic import BaseModel, Field


class DraftRetrievalConfig(BaseModel):
    """The 12 W43 per-KB knobs under test (draft, unsaved). Mirrors the `KbConfig`
    Optional knobs + `EffectiveConfig` / `PerQueryOverrides` field shape. Every field
    is Optional — `None` = fall through to the KB's saved config / global default in
    the resolver (so a draft only overrides the knobs it sets)."""

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


class ConfigTestRequest(BaseModel):
    """POST /kb/{kb_id}/config-test input."""

    query: str = Field(..., min_length=1, max_length=2000)
    # N runs for the variance band — 證偽實驗④ saw ~20% figure swing run-to-run, so a
    # single run can't decide a config. Capped at 5 (each run = a full synth, ~10-40s).
    runs: int = Field(default=3, ge=1, le=5)
    draft_config: DraftRetrievalConfig = Field(default_factory=DraftRetrievalConfig)
    mode: Literal["hybrid", "vector", "fulltext"] = "hybrid"
    # Default CRAG off for a clean per-config signal (CRAG re-synth adds its own variance).
    enable_crag: bool = False
    # F2.4 — also run N with the SAVED config (all-draft knobs cleared) for an A/B.
    compare_to_saved: bool = False


class CitationBreakdown(BaseModel):
    """Per-citation section + image count (F2.3 — 每 citation section+圖數)."""

    chunk_id: str
    section_path: list[str]
    image_count: int


class RunMetrics(BaseModel):
    """Presentation counters + latency for one run."""

    run: int
    citation_count: int
    figure_count_raw: int  # total embedded_images across citations (cross-citation dups kept)
    figure_count_dedup: int  # unique by checksum_sha256 (matches the frontend display dedup)
    latency_ms: int
    answer_chars: int
    refused: bool


class MetricBand(BaseModel):
    """Aggregate of one metric across runs. `band` = max - min = the variance band
    (per 證偽發現④ — if the band swamps a draft-vs-saved difference, the signal is
    noise; F2.6 trust gate checks exactly this)."""

    min: float
    max: float
    mean: float
    band: float


class ConfigRunSummary(BaseModel):
    """N-run aggregate for one config (draft or saved)."""

    runs: list[RunMetrics]
    citation_count: MetricBand
    figure_count_raw: MetricBand
    figure_count_dedup: MetricBand
    latency_ms: MetricBand
    per_citation: list[CitationBreakdown]  # from the last run (representative)


class ConfigTestResult(BaseModel):
    """POST /kb/{kb_id}/config-test output."""

    kb_id: str
    query: str
    runs: int
    # The resolved EffectiveConfig actually applied (draft > saved KbConfig > global)
    # — lets the caller confirm what was tested.
    resolved_config: dict[str, int | bool | None]
    draft: ConfigRunSummary
    saved: ConfigRunSummary | None = None  # populated when compare_to_saved=True
