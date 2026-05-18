/**
 * Typed Documents API (per architecture.md §4.4 #9-#12 + §3.5).
 *
 * GET /kb/{kb_id}/documents — W16 F5.1.1 / CO_F3a: aggregates the kb_id-scoped
 * Azure AI Search index chunks by doc_id, returns doc-level metadata (no bulk
 * chunk_text — use /query for retrieved-chunk text). Empty index → empty list.
 * GET /kb/{kb_id}/documents/{doc_id}/chunks — W16 F5.1.2: per-chunk metadata
 * (chunk_id / section_path / index / flags), ordered by chunk_index ascending.
 * POST upload / DELETE doc / POST reindex — wired by CH-001 (2026-05-12); the
 * upload path uses `kbApi.uploadDoc` (multipart) directly, not this client.
 */

import { ApiClient } from '../api-client';

const client = new ApiClient();

export interface DocumentSummary {
  doc_id: string;
  doc_title: string;
  doc_format: string;
  total_chunks: number;
  /** ISO datetime — max(ingested_at) across the observed chunks. */
  last_indexed_at: string;
  source_url: string | null;
  tags: string[];
}

/** Mirrors backend `api.schemas.listing.ChunkSummary` (Pydantic). */
export interface ChunkSummary {
  chunk_id: string;
  chunk_index: number;
  chunk_total: number;
  chunk_title: string;
  section_path: string[];
  enabled: boolean;
  low_value_flag: boolean;
}

// W21 F1 — `GET /kb/{kb_id}/docs/{doc_id}` enriched (per ADR-0029 Option C).
// Powers the 3-pane Doc Detail view (outline + chunks + inspector).
// Shipped backend `306dbe0`; frontend client added W22 F6.3 (this addition).
export interface OutlineNode {
  level: number;
  title: string;
  chunk_count: number;
  page: number | null;
}

export interface ImageRef {
  blob_url: string;
  alt_text: string;
  checksum_sha256: string;
  width: number;
  height: number;
}

export interface DocumentDetail {
  doc_id: string;
  title: string;
  source: string | null;
  source_url: string | null;
  file_type: string;
  size_kb: number | null;
  pages: number | null;
  language: string | null;
  chunk_strategy: string | null;
  total_chunks: number;
  total_images: number;
  total_tokens: number | null;
  low_value_chunks: number;
  parse_duration_ms: number | null;
  embed_duration_ms: number | null;
  indexed_at: string;
  outline: OutlineNode[];
  image_refs: ImageRef[];
}

export const documentsApi = {
  list: (kbId: string): Promise<DocumentSummary[]> =>
    client.get<DocumentSummary[]>(`/kb/${encodeURIComponent(kbId)}/documents`),

  listChunks: (kbId: string, docId: string): Promise<ChunkSummary[]> =>
    client.get<ChunkSummary[]>(
      `/kb/${encodeURIComponent(kbId)}/documents/${encodeURIComponent(docId)}/chunks`,
    ),

  // W21 F1 backend endpoint — different URL path from listChunks (per ADR-0029
  // `/kb/{kb_id}/docs/{doc_id}` vs existing `/documents/{doc_id}` legacy paths).
  getDocDetail: (kbId: string, docId: string): Promise<DocumentDetail> =>
    client.get<DocumentDetail>(
      `/kb/${encodeURIComponent(kbId)}/docs/${encodeURIComponent(docId)}`,
    ),
};
