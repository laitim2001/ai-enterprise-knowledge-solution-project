/**
 * Typed Retrieval Testing API (ADR-0021 — V4 Retrieval Testing tab §5.5.4).
 *
 * POST /kb/{kb_id}/retrieval-test — pure retrieval (no CRAG, no LLM synthesis):
 * compare Vector / Full-Text / Hybrid modes, tune Top-K / score threshold,
 * toggle rerank → ranked chunks + relevance scores + per-stage timings.
 */

import { ApiClient } from '../api-client';

const client = new ApiClient();

export type RetrievalMode = 'hybrid' | 'vector' | 'fulltext';

export interface RetrievalTestRequest {
  query: string;
  mode?: RetrievalMode;
  top_k?: number;
  rerank?: boolean;
  /** 0–1 similarity threshold for vector/hybrid scores; ignored for fulltext (BM25 unbounded). */
  score_threshold?: number;
}

export interface RetrievalTestChunk {
  rank: number;
  chunk_id: string;
  doc_id: string;
  doc_title: string;
  chunk_title: string;
  chunk_index: number;
  section_path: string[];
  score: number;
  chunk_text_preview: string;
}

export interface RetrievalTestResult {
  kb_id: string;
  query: string;
  mode: string;
  reranked: boolean;
  reranker: string; // "cohere-v4.0-pro" when reranked, else "none"
  embed_latency_ms: number;
  search_latency_ms: number;
  rerank_latency_ms: number;
  total_latency_ms: number;
  total_hits: number; // before the score_threshold filter
  chunks: RetrievalTestChunk[];
}

export const retrievalTestApi = {
  run: (kbId: string, body: RetrievalTestRequest): Promise<RetrievalTestResult> =>
    client.post<RetrievalTestResult>(
      `/kb/${encodeURIComponent(kbId)}/retrieval-test`,
      body,
    ),
};
