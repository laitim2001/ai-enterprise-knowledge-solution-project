/**
 * Typed Debug Trace API methods (per architecture.md §4.4 #17 + §5.7 V6 Debug View).
 *
 * W15 D2 F2: V6 Debug View trace fetcher (forward-looking stub contract).
 * ADR-0020 Session 2: contract synced to the live backend `GET /debug/trace/{trace_id}`
 * (`api/schemas/observability.py` `TraceDetail` / `TraceStage`), shipped W16 F5.5
 * with full Langfuse SDK integration (Decision D.2).
 *
 * The endpoint always returns HTTP 200 — `status` communicates the outcome
 * ("ok" | "not_found" | "langfuse_not_configured" | "sdk_method_missing" |
 * "fetch_failed"); the frontend branches on `status` rather than HTTP code.
 * `trace_url` is always populated so the "Open in Langfuse" deep-link CTA works
 * even when stage extraction is unavailable.
 *
 * `stages` is a flat list of raw Langfuse observations (e.g. "retrieval.retrieve",
 * "api.query.synthesize", "crag.refine", "generation.context_expansion"). The V6
 * Debug View maps each observation onto the 9 conceptual pipeline stages per
 * architecture.md §5.7 via name-prefix matching.
 */

import { ApiClient } from '../api-client';

const client = new ApiClient();

/** One Langfuse observation within a trace (backend `TraceStage`). */
export interface TraceStage {
  name: string;
  type: string; // "SPAN" | "GENERATION" | "EVENT"
  latency_ms: number;
  model?: string | null; // populated for GENERATION observations
  input_tokens: number;
  output_tokens: number;
  status: string; // "ok" | "error" | "cancelled"
  // Stage-specific metadata surfaced from the observation's `metadata` dict
  // (minus the always-present `duration_ms`). Carries e.g. Context Expander
  // `expanded_count` / `boundary_skip_count` / `requested_count`, or CRAG
  // `triggered` / `iterations`. Null when the observation had no extra metadata.
  details?: Record<string, unknown> | null;
}

/** Trace detail response (backend `TraceDetail`). */
export interface TraceDetail {
  trace_id: string;
  trace_url: string; // {langfuse_host}/trace/{trace_id}
  status: string; // "ok" | "not_found" | "langfuse_not_configured" | "sdk_method_missing" | "fetch_failed"
  total_latency_ms: number;
  total_input_tokens: number;
  total_output_tokens: number;
  stages: TraceStage[];
  note: string;
}

export const debugApi = {
  getTrace: (traceId: string): Promise<TraceDetail> =>
    client.get<TraceDetail>(`/debug/trace/${encodeURIComponent(traceId)}`),
};
