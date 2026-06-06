/**
 * Config-test harness API (W43 F2/F3.3, per ADR-0040 §Decision 3).
 *
 * The on-platform 試跑 harness: preview a DRAFT (unsaved) per-KB retrieval/citation
 * config by running the full `/query` pipeline N times and aggregating presentation
 * counters (citation / figure raw+dedup) + latency with a variance band. Mirrors
 * `backend/api/schemas/config_test.py` field-for-field.
 */

import { ApiClient } from '../api-client';

const client = new ApiClient();

/**
 * The 12 W43 per-KB knobs under test (draft, unsaved). Every field Optional —
 * `null`/absent = fall through to the KB's saved config / global default in the
 * resolver (so a draft only overrides the knobs it sets). Mirrors `KbConfig`'s
 * Optional knobs + backend `DraftRetrievalConfig`.
 */
export interface DraftRetrievalConfig {
  enable_parent_doc_retrieval?: boolean | null;
  parent_doc_section_depth_offset?: number | null;
  parent_doc_top_k?: number | null;
  parent_doc_max_tokens_per_parent?: number | null;
  enable_citation_post_hoc_expansion?: boolean | null;
  citation_expansion_max_aux?: number | null;
  citation_expansion_window?: number | null;
  citation_expansion_section_path_prefix_depth?: number | null;
  enable_citation_neighbour_images?: boolean | null;
  citation_neighbour_max_aux_images?: number | null;
  citation_neighbour_section_path_prefix_depth?: number | null;
  max_images_per_answer?: number | null;
}

export interface ConfigTestRequest {
  query: string;
  /** N runs for the variance band (1–5, default 3). Each run is a full synth. */
  runs?: number;
  draft_config?: DraftRetrievalConfig;
  mode?: 'hybrid' | 'vector' | 'fulltext';
  /** Default false — CRAG re-synth adds its own variance to a per-config signal. */
  enable_crag?: boolean;
  /** Also run N with the SAVED config for an A/B (F2.4). */
  compare_to_saved?: boolean;
  /**
   * W48 (ADR-0040 dual-axis) — also compute the reference-free RAGAs faithfulness
   * quality axis (judge LLM). Default true server-side; set false for a fast
   * presentation-only run. Degrades to null when no judge credential is configured.
   */
  eval_faithfulness?: boolean;
}

/** Per-citation section + image count (one row of the breakdown). */
export interface CitationBreakdown {
  chunk_id: string;
  section_path: string[];
  image_count: number;
}

/** Presentation counters + latency for one run. */
export interface RunMetrics {
  run: number;
  citation_count: number;
  figure_count_raw: number;
  figure_count_dedup: number;
  latency_ms: number;
  answer_chars: number;
  refused: boolean;
}

/** Aggregate of one metric across runs. `band` = max − min = the variance band. */
export interface MetricBand {
  min: number;
  max: number;
  mean: number;
  band: number;
}

/** N-run aggregate for one config (draft or saved). */
export interface ConfigRunSummary {
  runs: RunMetrics[];
  citation_count: MetricBand;
  figure_count_raw: MetricBand;
  figure_count_dedup: MetricBand;
  latency_ms: MetricBand;
  per_citation: CitationBreakdown[];
  /**
   * W48 (ADR-0040 dual-axis) → W49 (決策 7) — reference-free RAGAs faithfulness for
   * this config, judged PER RUN and aggregated into a MetricBand (band = max − min)
   * so the quality axis exposes its run-to-run noise. N=1 → band=0 (the card then
   * shows a single-shot warning). null = quality axis skipped (eval_faithfulness=false)
   * or no judge / every run's judge errored.
   */
  faithfulness: MetricBand | null;
}

export interface ConfigTestResult {
  kb_id: string;
  query: string;
  runs: number;
  /** The resolved EffectiveConfig actually applied (draft > saved KbConfig > global). */
  resolved_config: Record<string, number | boolean | null>;
  draft: ConfigRunSummary;
  saved: ConfigRunSummary | null;
}

export const configTestApi = {
  // POST /kb/{kb_id}/config-test — runs the full pipeline N times against a draft
  // config (and optionally the saved config) without persisting anything.
  run: (kbId: string, body: ConfigTestRequest): Promise<ConfigTestResult> =>
    client.post<ConfigTestResult>(`/kb/${kbId}/config-test`, body),
};
