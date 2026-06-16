/**
 * Typed KB API methods (per architecture.md §4.4 #4-#11 + §4.5 KbConfig schema).
 *
 * W3 D5 F8: + create method for Pipeline wizard sequence
 * (POST /kb → POST /kb/{id}/documents).
 */

import { ApiClient, buildAuthHeader, getCsrfHeaders } from '../api-client';

const client = new ApiClient();

// W84 (ADR-0065) — backend P4 scan pre-parse guard. A scanned PDF needs Docling
// OCR which blocks the SYNCHRONOUS ingest 8–9.5 min/file. The backend 422s with
// envelope `{"error":{"code":"ingest.scan_requires_confirm",...}}` BEFORE the slow
// parse; `uploadDoc` surfaces it as this typed error so the upload page can show a
// force-confirm banner and retry with forceScan=true.
export const SCAN_REQUIRES_CONFIRM_CODE = 'ingest.scan_requires_confirm';

export class ScanRequiresConfirmError extends Error {
  readonly code = SCAN_REQUIRES_CONFIRM_CODE;
  constructor(message: string) {
    super(message);
    this.name = 'ScanRequiresConfirmError';
  }
}

export interface KbConfig {
  embedding_model: string;
  embedding_dimension: number;
  chunk_strategy: 'heading_aware' | 'layout_aware' | 'slide_based' | 'auto';
  default_top_k: number;
  default_rerank_k: number;
  // W20 F4.1 — Multimodal Tier 1 fields (per ADR-0028 + architecture.md v6 §5.5.3).
  // Surfaced by the /kb/new Step-4 wizard.
  extract_embedded_images: boolean;
  slide_screenshots: boolean;
  dedup_strategy: 'sha256' | 'none';
  return_images_in_chat: boolean;
  // W43 F1 — 12 per-KB tunable retrieval/citation/image knobs (per ADR-0040).
  // All Optional: `null`/absent = inherit the global Settings default. Surfaced by
  // the KB Detail Settings tab "Advanced retrieval tuning" card (F3.2). Resolved
  // per-query > per-KB (these) > global by the backend EffectiveConfig resolver.
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
  // W45 F1 — per-KB ingest-time chunker image cap (per ADR-0042; extends the
  // ADR-0040 config-scope model from query-time to INGEST-time). `null`/absent =
  // inherit the global Settings cap (default 8); a positive int caps images per
  // chunk (force-split). A per-KB KB cannot express "no cap" — that escape stays
  // global-only. Consumed at INGEST time, so a change only takes effect on
  // re-index (KB Detail Settings → Re-indexing card, F3).
  chunker_max_images_per_chunk?: number | null;
  // CH-006 — per-KB synthesis answer detail level. `null`/absent = inherit the global
  // default ("concise" = 150-word cap). "detailed" relaxes the synthesis prompt so
  // procedural answers reproduce every sub-step. Query-time knob (no re-index needed).
  answer_detail?: 'concise' | 'detailed' | null;
  // W70 (ADR-0055) — per-KB inline image markers gate. `null`/absent = inherit the
  // global default (False = clean-text prompts). True = answers carry [IMG#sha8]
  // position markers (stripped by the chat display until the W71 interleaved
  // render lands). Query-time knob; the KB's index must be re-indexed with the
  // marked field populated for markers to actually surface.
  enable_inline_image_markers?: boolean | null;
}

export const DEFAULT_KB_CONFIG: KbConfig = {
  embedding_model: 'text-embedding-3-large',
  embedding_dimension: 1024,
  chunk_strategy: 'auto',
  default_top_k: 50,
  default_rerank_k: 5,
  extract_embedded_images: false,
  slide_screenshots: true,
  dedup_strategy: 'sha256',
  return_images_in_chat: false,
};

export interface KbCreatePayload {
  kb_id: string;
  name: string;
  description?: string;
  config?: KbConfig;
}

export interface FailureRecord {
  doc_id: string;
  stage: string;
  error: string;
}

export interface KbStatus {
  kb_id: string;
  name: string;
  description: string;
  config: KbConfig;
  total_documents: number;
  total_chunks: number;
  total_screenshots: number;
  failed_documents: FailureRecord[];
  last_indexed_at: string;
  storage_size_mb: number;
  // W20 F5.1 — soft-archive flag per ADR-0025 KB Detail Settings Danger zone.
  archived: boolean;
}

// W20 F5.2 — KB images aggregation (KB Detail Tab 3 Images NEW).
export interface KbImageItem {
  id: string;
  url: string;
  doc_id: string;
  doc_name: string;
  page_num: number | null;
  ocr_text: string;
  screenshot_type: string | null;
  created_at: string | null;
}

export interface KbImagesResponse {
  items: KbImageItem[];
  total: number;
  limit: number;
  offset: number;
}

// W20 F5.3 — chunking preview (KB Detail Tab 4 Chunking Lab NEW).
export interface ChunkingPreviewRequest {
  kb_id?: string;
  sample_doc_id?: string;
  sample_text: string;
  strategy: 'heading_aware' | 'layout_aware' | 'slide_based' | 'auto';
  chunk_size: number;
  overlap: number;
}

export interface ChunkingPreviewItem {
  chunk_index: number;
  chunk_title: string;
  chunk_text: string;
  chunk_token_count: number;
  section_path: string[];
  low_value_flag: boolean;
}

export interface ChunkingPreviewResponse {
  items: ChunkingPreviewItem[];
  total: number;
  strategy: string;
  chunk_size: number;
  overlap: number;
  note: string | null;
}

// W24c F10 — per-KB ACL (mirrors backend `routes/kb_acl.py` + `rbac.py`
// KbAcl* schemas per ADR-0027). Read-only here: the mockup `TabKbAccess` CRUD
// affordances are presentational, so the POST/PATCH/DELETE client lands when
// the kb_acl mutation UI is built.
export type KbAclRole = 'manage' | 'edit' | 'query';
export type KbPrincipalType = 'user' | 'group';

export interface KbAclEntry {
  id: number;
  kb_id: string;
  principal_type: KbPrincipalType;
  principal_id: string;
  access_role: KbAclRole;
  granted_by: string | null;
  created_at: string;
}

export interface KbAclListResponse {
  entries: KbAclEntry[];
  total: number;
}

// W46 F2 — real KB-level reindex summary (per ADR-0043; backend
// `documents.py:run_kb_reindex`). Synchronous in-place per-doc delete+reingest
// from each document's stored original source. Docs ingested before W46 (no
// stored source) land in `skipped_no_source`; mid-pipeline failures in `failed`.
export interface KbReindexFailure {
  doc_id: string;
  error: string;
}

export interface KbReindexSummary {
  status: string; // "reindexed"
  kb_id: string;
  documents_total: number;
  documents_reindexed: number;
  reindexed: string[]; // doc_ids successfully rebuilt
  skipped_no_source: string[]; // doc_ids with no stored source — re-upload to fix
  failed: KbReindexFailure[];
  chunks_total: number;
}

export const kbApi = {
  list: (): Promise<KbStatus[]> => client.get<KbStatus[]>('/kb'),

  get: (kbId: string): Promise<KbStatus> => client.get<KbStatus>(`/kb/${kbId}`),

  create: (payload: KbCreatePayload): Promise<KbStatus> =>
    client.post<KbStatus>('/kb', payload),

  patchSettings: (kbId: string, config: Partial<KbConfig>): Promise<KbStatus> =>
    client.patch<KbStatus>(`/kb/${kbId}/settings`, config),

  // PATCH /kb/{id} — W16 F5.2 / CO_F3b: partial update of KB metadata
  // (name + description only; KbConfig stays in patchSettings). Omitted fields
  // preserve the existing value (true partial-PATCH semantics).
  patchMetadata: (
    kbId: string,
    patch: { name?: string; description?: string },
  ): Promise<KbStatus> => client.patch<KbStatus>(`/kb/${kbId}`, patch),

  // W20 F5.1 — archive a KB (soft delete; index + blobs preserved per ADR-0025).
  archive: (kbId: string): Promise<KbStatus> =>
    client.post<KbStatus>(`/kb/${kbId}/archive`, {}),

  // W46 F2 — real KB-level reindex (ADR-0043). Synchronous; returns a summary of
  // per-doc outcomes. 403 if the KB is archived; 503 if Azure deps unconfigured.
  reindex: (kbId: string): Promise<KbReindexSummary> =>
    client.post<KbReindexSummary>(`/kb/${kbId}/reindex`, {}),

  // W20 F5.2 — KB images aggregation (Tab 3 Images).
  listImages: (kbId: string, limit = 50, offset = 0): Promise<KbImagesResponse> =>
    client.get<KbImagesResponse>(
      `/kb/${kbId}/images?limit=${limit}&offset=${offset}`,
    ),

  // W20 F5.3 — chunking preview (Tab 4 Chunking Lab).
  chunkingPreview: (body: ChunkingPreviewRequest): Promise<ChunkingPreviewResponse> =>
    client.post<ChunkingPreviewResponse>('/chunking-preview', body),

  // W24c F10 — per-KB ACL grants (KB Detail Access tab; backend F8 kb_acl).
  listAcl: (kbId: string): Promise<KbAclListResponse> =>
    client.get<KbAclListResponse>(`/kb/${kbId}/acl`),

  uploadDoc: async (
    kbId: string,
    file: File,
    forceScan = false,
  ): Promise<{ doc_id: string }> => {
    const form = new FormData();
    form.append('file', file);
    // Browser fetch goes through Next.js server-side rewrite (per api-client.ts
    // top docstring). NEXT_PUBLIC_API_URL is server-side only.
    // W84 (ADR-0065) — forceScan=true bypasses the backend P4 scan guard after the
    // user confirms via the upload UI's "仍要繼續" button (OCR is slow but accepted).
    const qs = forceScan ? '?force_scan=true' : '';
    const response = await fetch(`/api/backend/kb/${kbId}/documents${qs}`, {
      method: 'POST',
      credentials: 'include',
      headers: { ...buildAuthHeader(), ...getCsrfHeaders() },
      body: form,
    });
    if (!response.ok) {
      const body = await response.text();
      if (response.status === 422) {
        // W84 (ADR-0065) — the P4 scan guard 422s with code
        // `ingest.scan_requires_confirm`; surface it as a typed error so the
        // upload page shows a force-confirm banner instead of a generic failure.
        let code: string | undefined;
        let message: string | undefined;
        try {
          const parsed = JSON.parse(body) as {
            error?: { code?: string; message?: string };
          };
          code = parsed.error?.code;
          message = parsed.error?.message;
        } catch {
          // body wasn't JSON — fall through to the generic error below
        }
        if (code === SCAN_REQUIRES_CONFIRM_CODE) {
          throw new ScanRequiresConfirmError(
            message ?? 'This looks like a scanned PDF — OCR will take several minutes.',
          );
        }
      }
      throw new Error(`upload failed: ${response.status} ${body}`);
    }
    return response.json() as Promise<{ doc_id: string }>;
  },
};
