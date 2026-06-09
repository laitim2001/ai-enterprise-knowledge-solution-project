/**
 * Per-document config API (W58 / ADR-0051; consumes the W57 / ADR-0050 backend).
 *
 * The per-DOCUMENT config overlay (post-retrieval knobs only) keyed by
 * (kb_id, doc_id). Mirrors `backend/api/schemas/doc_config.py` `DocConfig`
 * field-for-field. Every field Optional — `null`/absent = inherit the per-KB
 * value (then global), resolved server-side per ADR-0050
 * (per-query > per-DOC > per-KB > global).
 */

import { ApiClient } from '../api-client';

const client = new ApiClient();

/**
 * Per-document config — the post-retrieval knobs ADR-0050 resolves per document
 * via the dominant cited doc. Retrieval-entry knobs (top_k / rerank / parent_doc)
 * are deliberately ABSENT (they stay per-KB). `null` = inherit per-KB.
 */
export interface DocConfig {
  answer_detail?: 'concise' | 'detailed' | null;
  enable_citation_post_hoc_expansion?: boolean | null;
  citation_expansion_max_aux?: number | null;
  citation_expansion_window?: number | null;
  citation_expansion_section_path_prefix_depth?: number | null;
  enable_citation_neighbour_images?: boolean | null;
  citation_neighbour_max_aux_images?: number | null;
  citation_neighbour_section_path_prefix_depth?: number | null;
  max_images_per_answer?: number | null;
  enable_chapter_overview_pin?: boolean | null;
}

export const docConfigApi = {
  // GET — stored per-doc config, or an all-null DocConfig (= inherit per-KB).
  get: (kbId: string, docId: string): Promise<DocConfig> =>
    client.get<DocConfig>(`/kb/${kbId}/docs/${encodeURIComponent(docId)}/config`),

  // PUT — upsert the per-doc config; returns the stored config.
  put: (kbId: string, docId: string, config: DocConfig): Promise<DocConfig> =>
    client.put<DocConfig>(`/kb/${kbId}/docs/${encodeURIComponent(docId)}/config`, config),

  // DELETE — clear the per-doc config (204; idempotent → inherits per-KB again).
  delete: (kbId: string, docId: string): Promise<void> =>
    client.delete(`/kb/${kbId}/docs/${encodeURIComponent(docId)}/config`),

  // GET — {doc_id: DocConfig} for every per-doc config under the KB.
  list: (kbId: string): Promise<Record<string, DocConfig>> =>
    client.get<Record<string, DocConfig>>(`/kb/${kbId}/doc-configs`),
};
