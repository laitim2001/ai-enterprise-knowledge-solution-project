/**
 * Typed KB API methods (per architecture.md §4.4 #4-#11 + §4.5 KbConfig schema).
 *
 * W3 D5 F8: + create method for Pipeline wizard sequence
 * (POST /kb → POST /kb/{id}/documents).
 */

import { ApiClient, buildAuthHeader, getCsrfHeaders } from '../api-client';

const client = new ApiClient();

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

  // W20 F5.2 — KB images aggregation (Tab 3 Images).
  listImages: (kbId: string, limit = 50, offset = 0): Promise<KbImagesResponse> =>
    client.get<KbImagesResponse>(
      `/kb/${kbId}/images?limit=${limit}&offset=${offset}`,
    ),

  // W20 F5.3 — chunking preview (Tab 4 Chunking Lab).
  chunkingPreview: (body: ChunkingPreviewRequest): Promise<ChunkingPreviewResponse> =>
    client.post<ChunkingPreviewResponse>('/chunking-preview', body),

  uploadDoc: async (kbId: string, file: File): Promise<{ doc_id: string }> => {
    const form = new FormData();
    form.append('file', file);
    // Browser fetch goes through Next.js server-side rewrite (per api-client.ts
    // top docstring). NEXT_PUBLIC_API_URL is server-side only.
    const response = await fetch(`/api/backend/kb/${kbId}/documents`, {
      method: 'POST',
      credentials: 'include',
      headers: { ...buildAuthHeader(), ...getCsrfHeaders() },
      body: form,
    });
    if (!response.ok) {
      throw new Error(`upload failed: ${response.status} ${await response.text()}`);
    }
    return response.json() as Promise<{ doc_id: string }>;
  },
};
