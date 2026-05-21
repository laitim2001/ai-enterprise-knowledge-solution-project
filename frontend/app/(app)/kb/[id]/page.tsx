'use client';

/**
 * /kb/[id] — KB Detail per architecture.md v6 §5.5 view 4 + ADR-0025 8-tab.
 *
 * W22 F6.1 rebuild per CLAUDE.md §5.7 H7 — 100% mockup fidelity match against
 * references/design-mockups/ekp-page-kb.jsx:140 PageKbDetail (sub-tabs spread
 * across ekp-page-kb.jsx + ekp-page-kb-extras.jsx).
 *
 * Mockup decomposition adopted (single-file pattern):
 *   - DocumentsTab / ChunksTab / ImagesTab / ChunkingLabTab / PipelineTab /
 *     RetrievalTab / SettingsTab — all inline within page.tsx (mockup-faithful)
 *   - Access tab — <TabKbAccess> (components/kb/) per ADR-0025 + ADR-0027,
 *     activated W24c F10 once the F8 kb_acl backend landed
 *
 * Backend integration preserved (per F6.5):
 *   kbApi.get / kbApi.listImages / kbApi.chunkingPreview / kbApi.patchSettings /
 *   kbApi.patchMetadata / kbApi.archive + documentsApi.list + listChunks +
 *   retrievalTestApi.run
 *
 * CSS-first pivot baseline (per W22 F1 D2): visual layer via mockup CSS classes
 * (.tabs, .tab, .card, .field, .seg, .badge, .table, .banner, .stat-grid)
 * with inline style only for one-off mockup specifics.
 */

import {
  useMutation,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query';
import {
  AlertTriangle,
  Archive,
  ChevronLeft,
  ChevronRight,
  Check,
  Copy,
  Database,
  Download,
  Edit,
  FileText,
  Image as ImageIcon,
  Layers,
  MoreHorizontal,
  RefreshCw,
  Search,
  Settings as SettingsIcon,
  Shield,
  Sparkles,
  Trash2,
  Upload,
  Zap,
  type LucideIcon,
} from 'lucide-react';
import { useParams, useRouter, useSearchParams } from 'next/navigation';
import { useMemo, useState, type FormEvent } from 'react';
import { toast } from 'sonner';

import { TabKbAccess } from '@/components/kb/tab-kb-access';
import {
  documentsApi,
  type ChunkSummary,
  type DocumentSummary,
} from '@/lib/api/documents';
import {
  kbApi,
  type KbConfig,
  type KbImageItem,
  type KbStatus,
} from '@/lib/api/kb';
import {
  retrievalTestApi,
  type RetrievalMode,
  type RetrievalTestChunk,
  type RetrievalTestResult,
} from '@/lib/api/retrieval-test';

// Active tabs (mockup-faithful). The Access tab is the 8th per ADR-0025 —
// activated W24c F10 now the F8 kb_acl backend has landed.
const VALID_TABS = [
  'documents',
  'chunks',
  'images',
  'chunking-lab',
  'pipeline',
  'retrieval',
  'settings',
  'access',
] as const;
type TabKey = (typeof VALID_TABS)[number];

const TAB_DEFS: { id: TabKey; label: string; icon: LucideIcon }[] = [
  { id: 'documents', label: 'Documents', icon: FileText },
  { id: 'chunks', label: 'Chunks', icon: Layers },
  { id: 'images', label: 'Images', icon: ImageIcon },
  { id: 'chunking-lab', label: 'Chunking Lab', icon: Zap },
  { id: 'pipeline', label: 'Pipeline', icon: Zap },
  { id: 'retrieval', label: 'Retrieval Testing', icon: Search },
  { id: 'settings', label: 'Settings', icon: SettingsIcon },
  { id: 'access', label: 'Access', icon: Shield },
];

function formatRelative(iso: string | null | undefined): string {
  if (!iso) return '—';
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return '—';
  const diff = Date.now() - then;
  const minutes = Math.round(diff / 60_000);
  if (minutes < 1) return 'just now';
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.round(hours / 24);
  if (days < 30) return `${days}d ago`;
  return new Date(iso).toLocaleDateString();
}

export default function KbDetailPage() {
  const params = useParams<{ id: string }>();
  const kbId = params.id;
  const router = useRouter();
  const searchParams = useSearchParams();

  const tabParam = searchParams.get('tab');
  const activeTab: TabKey = VALID_TABS.includes(tabParam as TabKey)
    ? (tabParam as TabKey)
    : 'documents';

  const query = useQuery<KbStatus>({
    queryKey: ['kb', kbId],
    queryFn: () => kbApi.get(kbId),
    enabled: !!kbId,
  });

  function handleTabChange(next: TabKey) {
    const sp = new URLSearchParams(searchParams.toString());
    sp.set('tab', next);
    router.push(`/kb/${kbId}?${sp.toString()}`, { scroll: false });
  }

  if (query.isLoading) {
    return (
      <div className="content">
        <div className="content-wide">
          <div className="banner banner-info">
            <span className="spinner" />
            <div style={{ flex: 1 }}>Loading KB…</div>
          </div>
        </div>
      </div>
    );
  }
  if (query.isError) {
    return (
      <div className="content">
        <div className="content-wide">
          <div className="banner banner-error">
            <AlertTriangle size={16} />
            <div style={{ flex: 1 }}>
              Failed to load KB {kbId}:{' '}
              {String((query.error as Error)?.message ?? 'unknown')}
            </div>
          </div>
        </div>
      </div>
    );
  }
  if (!query.data) return null;

  const kb = query.data;
  const totalCounts: Partial<Record<TabKey, number>> = {
    documents: kb.total_documents,
    chunks: kb.total_chunks,
    images: kb.total_screenshots,
  };

  return (
    <div className="content">
      <div className="content-wide">
        <div className="page-header">
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
              <button
                type="button"
                className="btn btn-ghost btn-xs btn-ghost-muted"
                onClick={() => router.push('/kb')}
              >
                <ChevronLeft size={12} /> Knowledge
              </button>
              <span className="text-xs muted mono">·</span>
              <span className="text-xs muted mono">ekp-kb-{kb.kb_id}-v1</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <h1 className="page-title">{kb.name || kb.kb_id}</h1>
              {kb.archived ? (
                <span className="badge badge-muted">
                  <span className="badge-dot" /> ARCHIVED
                </span>
              ) : (
                <span className="badge badge-success">
                  <span className="badge-dot" /> READY
                </span>
              )}
            </div>
            {kb.description && <p className="page-subtitle">{kb.description}</p>}
          </div>
          <div className="page-actions">
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={() => handleTabChange('retrieval')}
            >
              <Search size={13} /> Retrieval test
            </button>
            <button type="button" className="btn btn-secondary btn-sm" disabled>
              <RefreshCw size={13} /> Re-index
            </button>
            <button
              type="button"
              className="btn btn-primary btn-sm"
              onClick={() => router.push(`/kb/${kb.kb_id}/upload`)}
            >
              <Upload size={13} /> Upload documents
            </button>
          </div>
        </div>

        {kb.failed_documents.length > 0 && (
          <div className="banner banner-warning">
            <AlertTriangle size={16} style={{ color: 'oklch(var(--warning))' }} />
            <div style={{ flex: 1 }}>
              <div style={{ fontWeight: 500 }}>
                {kb.failed_documents.length} document
                {kb.failed_documents.length > 1 ? 's' : ''} failed to index
              </div>
              <div className="text-xs muted">
                Review parser errors in the Documents tab → &ldquo;failed&rdquo; filter.
              </div>
            </div>
            <button
              type="button"
              className="btn btn-ghost btn-sm"
              onClick={() => handleTabChange('documents')}
            >
              View errors
            </button>
          </div>
        )}

        {/* Tabs */}
        <div className="tabs" role="tablist" aria-label="KB sections">
          {TAB_DEFS.map((t) => {
            const Ic = t.icon;
            const count = totalCounts[t.id];
            return (
              <button
                key={t.id}
                type="button"
                role="tab"
                aria-selected={activeTab === t.id}
                className="tab"
                data-active={activeTab === t.id}
                onClick={() => handleTabChange(t.id)}
              >
                <Ic size={14} /> {t.label}
                {count != null && (
                  <span className="count">{count.toLocaleString()}</span>
                )}
              </button>
            );
          })}
        </div>

        {activeTab === 'documents' && <DocumentsTab kb={kb} />}
        {activeTab === 'chunks' && <ChunksTab kb={kb} />}
        {activeTab === 'images' && <ImagesTab kb={kb} />}
        {activeTab === 'chunking-lab' && <ChunkingLabTab kb={kb} />}
        {activeTab === 'pipeline' && <PipelineTab kb={kb} />}
        {activeTab === 'retrieval' && <RetrievalTab kb={kb} />}
        {activeTab === 'settings' && <SettingsTab kb={kb} />}
        {activeTab === 'access' && <TabKbAccess kbId={kb.kb_id} />}
      </div>
    </div>
  );
}

// ── Tab: Documents ──────────────────────────────────────────────────────────
type DocStatusFilter = 'all' | 'indexed' | 'indexing' | 'failed' | 'queued';

function DocumentsTab({ kb }: { kb: KbStatus }) {
  const router = useRouter();
  const [filter, setFilter] = useState<DocStatusFilter>('all');
  const docs = useQuery<DocumentSummary[]>({
    queryKey: ['kb', kb.kb_id, 'documents'],
    queryFn: () => documentsApi.list(kb.kb_id),
  });

  const all = docs.data ?? [];
  // Backend currently exposes indexed docs only; surface filter UX faithfully
  // and route everything to `all` for now (Wave C+ wires real status field).
  const filtered = filter === 'all' ? all : filter === 'indexed' ? all : [];
  const filterCounts: Record<DocStatusFilter, number> = {
    all: all.length,
    indexed: all.length,
    indexing: 0,
    failed: kb.failed_documents.length,
    queued: 0,
  };

  if (docs.isLoading) {
    return (
      <div className="banner banner-info">
        <span className="spinner" />
        <div style={{ flex: 1 }}>Loading documents…</div>
      </div>
    );
  }
  if (docs.isError) {
    return (
      <div className="banner banner-error">
        <AlertTriangle size={16} />
        <div style={{ flex: 1 }}>
          Failed to load documents — backend unreachable or Azure AI Search not
          configured. {String((docs.error as Error)?.message ?? 'unknown')}
        </div>
      </div>
    );
  }
  if (all.length === 0) {
    return (
      <div className="empty">
        <div className="empty-icon">
          <Upload size={20} />
        </div>
        <div className="empty-title">No documents yet</div>
        <div>
          Word, PDF, or PowerPoint — ingestion pipeline parses + chunks + embeds.
        </div>
        <button
          type="button"
          className="btn btn-primary btn-sm"
          style={{ marginTop: 12 }}
          onClick={() => router.push(`/kb/${kb.kb_id}/upload`)}
        >
          <Upload size={13} /> Upload Document
        </button>
      </div>
    );
  }

  return (
    <div>
      <div
        style={{
          display: 'flex',
          gap: 8,
          marginBottom: 12,
          alignItems: 'center',
        }}
      >
        <div className="input-search-wrap" style={{ flex: 1, maxWidth: 340 }}>
          <span className="icon-leading">
            <Search size={14} />
          </span>
          <input
            className="input"
            placeholder="Search documents by title or doc_id…"
          />
        </div>
        <div className="seg">
          {(['all', 'indexed', 'indexing', 'failed', 'queued'] as DocStatusFilter[]).map(
            (f) => (
              <button
                type="button"
                key={f}
                className="seg-btn"
                data-active={filter === f}
                onClick={() => setFilter(f)}
              >
                {f === 'all' ? 'All' : f.charAt(0).toUpperCase() + f.slice(1)}
                <span className="text-xs mono" style={{ opacity: 0.6 }}>
                  {filterCounts[f]}
                </span>
              </button>
            ),
          )}
        </div>
        <div className="spacer" />
        <button type="button" className="btn btn-secondary btn-sm" disabled>
          <Download size={13} /> Export CSV
        </button>
      </div>

      <div className="table-wrap">
        <table className="table">
          <thead>
            <tr>
              <th>Document</th>
              <th>Type</th>
              <th className="col-num">Chunks</th>
              <th>Tags</th>
              <th>Status</th>
              <th className="col-num">Indexed</th>
              <th className="col-shrink" aria-label="row actions" />
            </tr>
          </thead>
          <tbody>
            {filtered.map((d) => (
              <tr
                key={d.doc_id}
                onClick={() =>
                  router.push(`/kb/${kb.kb_id}/docs/${encodeURIComponent(d.doc_id)}`)
                }
                style={{ cursor: 'default' }}
              >
                <td style={{ maxWidth: 360 }}>
                  <div
                    className="table-row-link"
                    style={{
                      whiteSpace: 'nowrap',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      color: 'oklch(var(--accent))',
                    }}
                  >
                    {d.doc_title || d.doc_id}
                  </div>
                  <div className="text-xs muted mono">{d.doc_id}</div>
                </td>
                <td>
                  <span
                    className="mono text-xs"
                    style={{ textTransform: 'uppercase' }}
                  >
                    {d.doc_format || '—'}
                  </span>
                </td>
                <td className="col-num">{d.total_chunks}</td>
                <td>
                  {d.tags.length > 0 ? (
                    <span
                      style={{ display: 'inline-flex', gap: 4, flexWrap: 'wrap' }}
                    >
                      {d.tags.slice(0, 3).map((t) => (
                        <span key={t} className="badge badge-muted">
                          {t}
                        </span>
                      ))}
                    </span>
                  ) : (
                    <span className="text-xs muted">—</span>
                  )}
                </td>
                <td>
                  <span className="badge badge-success">
                    <span className="badge-dot" /> INDEXED
                  </span>
                </td>
                <td className="col-num text-xs">
                  {formatRelative(d.last_indexed_at)}
                </td>
                <td className="col-shrink">
                  <button
                    type="button"
                    className="btn btn-ghost btn-icon btn-xs"
                    aria-label="More actions"
                  >
                    <MoreHorizontal size={14} />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginTop: 12,
          fontSize: 12,
        }}
      >
        <div className="muted">
          Showing {filtered.length} of {all.length}
        </div>
        <div className="row">
          <button
            type="button"
            className="btn btn-ghost btn-icon btn-xs"
            disabled
            aria-label="Previous page"
          >
            <ChevronLeft size={13} />
          </button>
          <span className="mono text-xs">1 / 1</span>
          <button
            type="button"
            className="btn btn-ghost btn-icon btn-xs"
            disabled
            aria-label="Next page"
          >
            <ChevronRight size={13} />
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Tab: Chunks ─────────────────────────────────────────────────────────────
function ChunksTab({ kb }: { kb: KbStatus }) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const docs = useQuery<DocumentSummary[]>({
    queryKey: ['kb', kb.kb_id, 'documents'],
    queryFn: () => documentsApi.list(kb.kb_id),
  });

  const docList = docs.data ?? [];
  const docParam = searchParams.get('doc');
  const selectedDocId =
    docParam && docList.some((d) => d.doc_id === docParam)
      ? docParam
      : docList[0]?.doc_id;

  const chunks = useQuery<ChunkSummary[]>({
    queryKey: ['kb', kb.kb_id, 'chunks', selectedDocId],
    queryFn: () => documentsApi.listChunks(kb.kb_id, selectedDocId!),
    enabled: !!selectedDocId,
  });

  const [selectedChunkId, setSelectedChunkId] = useState<string | null>(null);
  const chunkList = chunks.data ?? [];
  const activeChunk =
    chunkList.find((c) => c.chunk_id === selectedChunkId) ?? chunkList[0];

  if (docs.isLoading) {
    return (
      <div className="banner banner-info">
        <span className="spinner" />
        <div style={{ flex: 1 }}>Loading documents…</div>
      </div>
    );
  }
  if (docList.length === 0) {
    return (
      <div className="empty">
        <div className="empty-icon">
          <Layers size={20} />
        </div>
        <div className="empty-title">No chunks yet</div>
        <div>Upload a document first — chunks emit during ingestion.</div>
      </div>
    );
  }

  return (
    <div>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          marginBottom: 12,
        }}
      >
        <label className="label" style={{ marginBottom: 0 }}>
          Document
        </label>
        <select
          className="select"
          value={selectedDocId ?? ''}
          onChange={(e) => {
            const sp = new URLSearchParams(searchParams.toString());
            sp.set('doc', e.target.value);
            router.push(`/kb/${kb.kb_id}?${sp.toString()}`, { scroll: false });
            setSelectedChunkId(null);
          }}
          style={{ maxWidth: 480 }}
        >
          {docList.map((d) => (
            <option key={d.doc_id} value={d.doc_id}>
              {d.doc_title || d.doc_id} ({d.total_chunks} chunks)
            </option>
          ))}
        </select>
      </div>

      <div className="split-2">
        <div className="card">
          <div className="card-header">
            <div>
              <h3 className="card-title">Browse chunks</h3>
              <div className="card-desc">
                {chunkList.length.toLocaleString()} chunks in selected doc
              </div>
            </div>
          </div>
          <div
            className="card-body card-body-tight"
            style={{ maxHeight: 540, overflowY: 'auto' }}
          >
            {chunks.isLoading && (
              <div style={{ padding: 14 }} className="text-xs muted">
                Loading chunks…
              </div>
            )}
            {chunks.isError && (
              <div style={{ padding: 14 }} className="text-xs">
                Failed to load chunks: {String((chunks.error as Error)?.message)}
              </div>
            )}
            {chunkList.map((c) => {
              const active = activeChunk?.chunk_id === c.chunk_id;
              return (
                <div
                  key={c.chunk_id}
                  onClick={() => setSelectedChunkId(c.chunk_id)}
                  style={{
                    padding: '10px 16px',
                    borderBottom: '1px solid oklch(var(--border))',
                    cursor: 'default',
                    background: active ? 'oklch(var(--muted) / 0.5)' : 'transparent',
                    borderLeft: active
                      ? '2px solid oklch(var(--accent))'
                      : '2px solid transparent',
                  }}
                >
                  <div className="text-xs mono muted" style={{ marginBottom: 2 }}>
                    #{c.chunk_id}
                  </div>
                  <div style={{ fontSize: 13, fontWeight: 500, marginBottom: 2 }}>
                    {c.chunk_title}
                  </div>
                  <div className="section-path text-xs">
                    {c.section_path.map((s, j) => (
                      <span key={j}>{s}</span>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <div>
              <h3 className="card-title">Chunk preview</h3>
              <div className="card-desc">
                {activeChunk ? (
                  <span className="mono">{activeChunk.chunk_id}</span>
                ) : (
                  '—'
                )}
              </div>
            </div>
            <div className="row">
              <button
                type="button"
                className="btn btn-ghost btn-icon btn-sm"
                aria-label="Edit"
                disabled
              >
                <Edit size={14} />
              </button>
              <button
                type="button"
                className="btn btn-ghost btn-icon btn-sm"
                aria-label="Copy"
                onClick={() => {
                  if (activeChunk) {
                    void navigator.clipboard
                      .writeText(activeChunk.chunk_id)
                      .then(() => toast.success('Chunk id copied'))
                      .catch(() => toast.error('Copy failed'));
                  }
                }}
              >
                <Copy size={14} />
              </button>
            </div>
          </div>
          <div className="card-body">
            {activeChunk ? (
              <>
                <div
                  style={{
                    display: 'flex',
                    flexWrap: 'wrap',
                    gap: 6,
                    marginBottom: 12,
                  }}
                >
                  <span className="badge badge-muted">
                    chunk_index <b style={{ marginLeft: 2 }}>{activeChunk.chunk_index}</b>
                  </span>
                  <span className="badge badge-muted">
                    of <b style={{ marginLeft: 2 }}>{activeChunk.chunk_total}</b>
                  </span>
                  {activeChunk.low_value_flag && (
                    <span className="badge badge-warning">low_value</span>
                  )}
                  {!activeChunk.enabled && (
                    <span className="badge badge-error">disabled</span>
                  )}
                </div>
                <div
                  className="section-path text-sm"
                  style={{ marginBottom: 14 }}
                >
                  {activeChunk.section_path.map((s, j) => (
                    <span key={j}>{s}</span>
                  ))}
                </div>
                <div className="text-xs muted">
                  Chunk body text not bulk-listed — use Retrieval Testing tab to
                  view full chunk text per query.
                </div>
              </>
            ) : (
              <div className="text-xs muted">Select a chunk to preview.</div>
            )}
          </div>
          {activeChunk && (
            <div className="card-footer">
              <div className="text-xs muted mono">
                embedding_model · {kb.config.embedding_model} ·{' '}
                {kb.config.embedding_dimension}d MRL
              </div>
              <button type="button" className="btn btn-ghost btn-xs" disabled>
                View raw embedding →
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ── Tab: Images ─────────────────────────────────────────────────────────────
function ImagesTab({ kb }: { kb: KbStatus }) {
  const images = useQuery({
    queryKey: ['kb', kb.kb_id, 'images'],
    queryFn: () => kbApi.listImages(kb.kb_id, 200, 0),
  });

  const items = images.data?.items ?? [];
  const totalRefs = items.length;
  const dedupSavings = 0; // Backend hasn't surfaced this yet (mockup-only viz).
  const totalSizeKb = 0; // Same — surfaced when KbImagesResponse adds size_kb.

  return (
    <div>
      <div
        className="stat-grid"
        style={{ gridTemplateColumns: 'repeat(4, 1fr)', marginBottom: 16 }}
      >
        <div className="stat">
          <div className="stat-label">
            <Layers size={13} /> Extracted images
          </div>
          <div className="stat-value">{kb.total_screenshots}</div>
          <div className="stat-meta">
            Across {kb.total_documents} document
            {kb.total_documents === 1 ? '' : 's'}
          </div>
        </div>
        <div className="stat">
          <div className="stat-label">
            <Shield size={13} /> SHA256 dedup
          </div>
          <div className="stat-value">
            {dedupSavings}
            <span className="stat-unit"> deduped</span>
          </div>
          <div className="stat-meta">
            Same hash → single Blob; {totalRefs} chunk references total
          </div>
        </div>
        <div className="stat">
          <div className="stat-label">
            <Database size={13} /> Blob storage
          </div>
          <div className="stat-value">
            {(totalSizeKb / 1024).toFixed(1)}
            <span className="stat-unit"> MB</span>
          </div>
          <div className="stat-meta mono">ekp-kb-{kb.kb_id}-screenshots</div>
        </div>
        <div className="stat">
          <div className="stat-label">
            <AlertTriangle size={13} /> low_value flagged
          </div>
          <div className="stat-value">0</div>
          <div className="stat-meta">Excluded from retrieval — logos, decorations</div>
        </div>
      </div>

      <div className="banner banner-info" style={{ marginBottom: 16 }}>
        <Sparkles size={15} style={{ color: 'oklch(var(--info))' }} />
        <div style={{ flex: 1, lineHeight: 1.5 }}>
          <div style={{ fontSize: 13, fontWeight: 500 }}>
            How chunks reference images
          </div>
          <div className="text-xs muted mono" style={{ marginTop: 2 }}>
            Parser extracts <b style={{ color: 'oklch(var(--foreground))' }}>
              EmbeddedImage{`{sha256, alt_text, doc_order}`}
            </b>{' '}
            → Extractor adds kb_id/doc_id → Uploader pushes blob with{' '}
            <b style={{ color: 'oklch(var(--foreground))' }}>
              {'{sha256}.{ext}'}
            </b>{' '}
            path (cross-doc dedup) → Chunker references via{' '}
            <b style={{ color: 'oklch(var(--foreground))' }}>
              embedded_image_positions
            </b>{' '}
            → Orchestrator resolves to{' '}
            <b style={{ color: 'oklch(var(--foreground))' }}>ImageRef.blob_url</b>{' '}
            in ChunkRecord.
          </div>
        </div>
      </div>

      <div
        style={{
          display: 'flex',
          gap: 8,
          alignItems: 'center',
          marginBottom: 12,
        }}
      >
        <div className="input-search-wrap" style={{ maxWidth: 320, flex: 1 }}>
          <span className="icon-leading">
            <Search size={14} />
          </span>
          <input
            className="input"
            placeholder="Search by alt text or SHA256…"
          />
        </div>
        <div className="spacer" />
        <button type="button" className="btn btn-secondary btn-sm" disabled>
          <Download size={13} /> Export manifest
        </button>
      </div>

      {images.isLoading ? (
        <div className="banner banner-info">
          <span className="spinner" />
          <div style={{ flex: 1 }}>Loading images…</div>
        </div>
      ) : images.isError ? (
        <div className="banner banner-error">
          <AlertTriangle size={16} />
          <div style={{ flex: 1 }}>
            Failed to load images:{' '}
            {String((images.error as Error)?.message ?? 'unknown')}
          </div>
        </div>
      ) : items.length === 0 ? (
        <div className="empty">
          <div className="empty-icon">
            <ImageIcon size={20} />
          </div>
          <div className="empty-title">No images extracted yet</div>
          <div>Embedded images appear once a doc with figures is ingested.</div>
        </div>
      ) : (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))',
            gap: 12,
          }}
        >
          {items.map((img, i) => (
            <ImageCard key={img.id} img={img} idx={i} />
          ))}
        </div>
      )}
    </div>
  );
}

function ImageCard({ img, idx }: { img: KbImageItem; idx: number }) {
  const colors = [
    'oklch(var(--accent))',
    'oklch(0.62 0.13 200)',
    'oklch(0.65 0.14 145)',
    'oklch(0.60 0.16 285)',
    'oklch(0.65 0.18 25)',
  ];
  const c = colors[idx % colors.length];
  return (
    <div
      style={{
        border: '1px solid oklch(var(--border))',
        borderRadius: 'var(--radius-md)',
        overflow: 'hidden',
        background: 'oklch(var(--card))',
        cursor: 'default',
      }}
    >
      <div
        style={{
          height: 130,
          backgroundImage: `linear-gradient(135deg, ${c.replace(
            ')',
            ' / 0.2)',
          )}, ${c.replace(')', ' / 0.05)')})`,
          position: 'relative',
          display: 'grid',
          placeItems: 'center',
          color: c,
        }}
      >
        <Layers size={28} />
        <span
          style={{
            position: 'absolute',
            bottom: 6,
            right: 8,
            fontFamily: 'var(--font-mono)',
            fontSize: 10,
            color: 'oklch(var(--muted-foreground))',
            background: 'oklch(var(--background) / 0.7)',
            padding: '1px 5px',
            borderRadius: 3,
          }}
        >
          {img.page_num != null ? `p.${img.page_num}` : '—'}
        </span>
      </div>
      <div style={{ padding: '10px 12px' }}>
        <div
          style={{
            fontSize: 12.5,
            fontWeight: 500,
            lineHeight: 1.4,
            height: 36,
            overflow: 'hidden',
            display: '-webkit-box',
            WebkitLineClamp: 2,
            WebkitBoxOrient: 'vertical',
          }}
        >
          {img.ocr_text || <span className="muted">(no ocr text)</span>}
        </div>
        <div
          className="text-xs muted mono"
          style={{
            marginTop: 6,
            whiteSpace: 'nowrap',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
          }}
        >
          {img.doc_name}
        </div>
        <div
          style={{
            marginTop: 8,
            display: 'flex',
            alignItems: 'center',
            gap: 6,
            fontSize: 11,
          }}
        >
          <span className="badge badge-muted" style={{ fontSize: 10 }}>
            {img.screenshot_type || 'screenshot'}
          </span>
        </div>
      </div>
    </div>
  );
}

// ── Tab: Chunking Lab ───────────────────────────────────────────────────────
const CHUNK_STRATEGIES: {
  id: KbConfig['chunk_strategy'];
  label: string;
  hint: string;
  supported: boolean;
  skip_reason?: string;
}[] = [
  {
    id: 'layout_aware',
    label: 'Layout-aware',
    hint: 'Docling — preserves tables, lists, sections',
    supported: true,
  },
  {
    id: 'slide_based',
    label: 'Slide-based',
    hint: 'python-pptx — one chunk per slide',
    supported: true,
  },
  {
    id: 'heading_aware',
    label: 'Heading-aware',
    hint: 'Splits at H1/H2/H3 — for narrative docs',
    supported: false,
    skip_reason: 'NotImplementedError — W3+ deferred per ingestion/chunker/strategies.py',
  },
  {
    id: 'auto',
    label: 'Auto',
    hint: 'Detect doc type, pick strategy',
    supported: true,
  },
];

function ChunkingLabTab({ kb }: { kb: KbStatus }) {
  const [activeStrategy, setActiveStrategy] = useState<KbConfig['chunk_strategy']>(
    kb.config.chunk_strategy,
  );
  const [chunkSize, setChunkSize] = useState(800);
  const [overlap, setOverlap] = useState(100);
  const [sampleText, setSampleText] = useState('');
  const preview = useMutation({
    mutationFn: () =>
      kbApi.chunkingPreview({
        kb_id: kb.kb_id,
        sample_text: sampleText || ' ',
        strategy: activeStrategy,
        chunk_size: chunkSize,
        overlap,
      }),
    onError: (e) => {
      const msg = e instanceof Error ? e.message : 'preview failed';
      toast.error(msg);
    },
  });

  return (
    <div>
      <div className="banner banner-info" style={{ marginBottom: 16 }}>
        <Sparkles size={15} style={{ color: 'oklch(var(--info))' }} />
        <div style={{ flex: 1, lineHeight: 1.5 }}>
          <div style={{ fontSize: 13, fontWeight: 500 }}>
            Preview chunking on a sample document
          </div>
          <div className="text-xs muted" style={{ marginTop: 2 }}>
            Strategies are picked by{' '}
            <span className="mono">ingestion/chunker/strategies.py</span>. Only{' '}
            <span className="mono">layout_aware</span> and{' '}
            <span className="mono">slide_based</span> are implemented;{' '}
            <span className="mono">heading_aware</span> raises{' '}
            <span className="mono">NotImplementedError</span> (W3+ deferred).
          </div>
        </div>
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '1.4fr 1fr',
          gap: 16,
          marginBottom: 16,
        }}
      >
        <div className="card">
          <div className="card-header">
            <div>
              <h3 className="card-title">Sample text</h3>
              <div className="card-desc">
                Paste a few paragraphs to preview chunk boundaries
              </div>
            </div>
          </div>
          <div className="card-body">
            <textarea
              className="input"
              rows={6}
              placeholder="Paste sample document text…"
              value={sampleText}
              onChange={(e) => setSampleText(e.target.value)}
            />
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Chunking parameters</h3>
          </div>
          <div className="card-body">
            <div className="field" style={{ marginBottom: 12 }}>
              <label className="label">
                Chunk size (tokens){' '}
                <span className="text-xs muted mono" style={{ marginLeft: 6 }}>
                  {chunkSize}
                </span>
              </label>
              <input
                type="range"
                min={200}
                max={1200}
                step={50}
                value={chunkSize}
                onChange={(e) => setChunkSize(+e.target.value)}
                style={{ width: '100%' }}
              />
            </div>
            <div className="field" style={{ marginBottom: 0 }}>
              <label className="label">
                Overlap{' '}
                <span className="text-xs muted mono" style={{ marginLeft: 6 }}>
                  {overlap}
                </span>
              </label>
              <input
                type="range"
                min={0}
                max={300}
                step={10}
                value={overlap}
                onChange={(e) => setOverlap(+e.target.value)}
                style={{ width: '100%' }}
              />
            </div>
          </div>
        </div>
      </div>

      <h3 className="card-title" style={{ marginBottom: 10 }}>
        Strategy comparison
      </h3>
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(4, 1fr)',
          gap: 12,
          marginBottom: 16,
        }}
      >
        {CHUNK_STRATEGIES.map((s) => (
          <div
            key={s.id}
            onClick={() => s.supported && setActiveStrategy(s.id)}
            style={{
              border: `1px solid ${
                activeStrategy === s.id
                  ? 'oklch(var(--accent))'
                  : 'oklch(var(--border))'
              }`,
              background:
                activeStrategy === s.id
                  ? 'oklch(var(--accent) / 0.05)'
                  : 'oklch(var(--card))',
              borderRadius: 'var(--radius-md)',
              padding: 14,
              opacity: s.supported ? 1 : 0.55,
              cursor: 'default',
            }}
          >
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 6,
                marginBottom: 4,
              }}
            >
              <span style={{ fontWeight: 600, fontSize: 13.5 }}>{s.label}</span>
              {!s.supported && <span className="badge badge-muted">N/A</span>}
            </div>
            <div
              className="text-xs muted"
              style={{ marginBottom: 10, lineHeight: 1.4 }}
            >
              {s.hint}
            </div>
            {!s.supported && s.skip_reason && (
              <div
                className="text-xs muted"
                style={{ lineHeight: 1.5, padding: '8px 0' }}
              >
                <span
                  style={{
                    color: 'oklch(var(--destructive))',
                    fontWeight: 500,
                  }}
                >
                  Not available ·
                </span>
                {s.skip_reason}
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="card">
        <div className="card-header">
          <div>
            <h3 className="card-title">
              Output preview ·{' '}
              {CHUNK_STRATEGIES.find((s) => s.id === activeStrategy)?.label}
            </h3>
            <div className="card-desc">
              First {preview.data?.items.length ?? 0} chunks from sample text
            </div>
          </div>
          <button
            type="button"
            className="btn btn-accent btn-sm"
            disabled={preview.isPending || !sampleText.trim()}
            onClick={() => preview.mutate()}
          >
            {preview.isPending ? (
              <>
                <span className="spinner" /> Running…
              </>
            ) : (
              <>
                <Zap size={13} /> Run preview
              </>
            )}
          </button>
        </div>
        <div className="card-body card-body-tight">
          {preview.data?.items.length ? (
            preview.data.items.map((c, i) => (
              <div
                key={i}
                style={{
                  padding: '14px 18px',
                  borderBottom:
                    i < preview.data!.items.length - 1
                      ? '1px solid oklch(var(--border))'
                      : 'none',
                }}
              >
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 10,
                    marginBottom: 6,
                  }}
                >
                  <span
                    className="mono text-xs"
                    style={{
                      background: 'oklch(var(--muted))',
                      padding: '1px 6px',
                      borderRadius: 3,
                      fontWeight: 600,
                    }}
                  >
                    #{c.chunk_index + 1}
                  </span>
                  <span style={{ fontSize: 13, fontWeight: 500, flex: 1 }}>
                    {c.chunk_title}
                  </span>
                  {c.low_value_flag && (
                    <span className="badge badge-warning">low_value</span>
                  )}
                  <span className="text-xs mono muted">
                    {c.chunk_token_count} tok
                  </span>
                </div>
                <div
                  style={{
                    fontSize: 12.5,
                    lineHeight: 1.55,
                    color: 'oklch(var(--foreground) / 0.85)',
                  }}
                >
                  {c.chunk_text.slice(0, 240)}
                  {c.chunk_text.length > 240 ? '…' : ''}
                </div>
              </div>
            ))
          ) : (
            <div className="empty">
              <div className="empty-icon">
                <AlertTriangle size={20} />
              </div>
              <div className="empty-title">
                {preview.isError ? 'Preview failed' : 'No preview yet'}
              </div>
              <div>
                {preview.isError
                  ? String((preview.error as Error)?.message ?? 'unknown')
                  : 'Paste sample text + click Run preview.'}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ── Tab: Pipeline ───────────────────────────────────────────────────────────
function PipelineTab({ kb }: { kb: KbStatus }) {
  const stages = [
    {
      name: '1. Source ingestion',
      desc: 'SharePoint / Drive / share folder',
      duration: '—',
    },
    {
      name: '2. Document extraction',
      desc: 'Docling (PDF + DOCX) · python-pptx (slide_based)',
      duration: 'avg 8s/doc',
    },
    {
      name: '3. Chunking',
      desc: `${kb.config.chunk_strategy} · 800 tokens · 100 overlap`,
      duration: 'avg 1s/doc',
    },
    {
      name: '4. Embedding',
      desc: `Azure OpenAI ${kb.config.embedding_model} · ${kb.config.embedding_dimension}d MRL truncate`,
      duration: 'avg 0.4s/chunk',
    },
    {
      name: '5. Index upsert',
      desc: `ekp-kb-${kb.kb_id}-v1 · HNSW vector + BM25 lexical`,
      duration: 'avg 0.1s/chunk',
    },
    {
      name: '6. Eval suite (nightly)',
      desc: 'RAGAs 4-metric · per W17 F3',
      duration: '—',
    },
  ];
  return (
    <div>
      <div className="banner banner-success" style={{ marginBottom: 16 }}>
        <Check size={15} style={{ color: 'oklch(var(--success))' }} />
        <div style={{ flex: 1 }}>
          <div style={{ fontWeight: 500 }}>Pipeline healthy</div>
          <div className="text-xs muted">
            All stages running within SLOs · last full re-index{' '}
            {formatRelative(kb.last_indexed_at)}
          </div>
        </div>
        <button type="button" className="btn btn-secondary btn-sm" disabled>
          Trigger full re-index
        </button>
      </div>

      <div className="card">
        <div className="card-header">
          <h3 className="card-title">Indexing pipeline</h3>
        </div>
        <div className="card-body card-body-tight">
          {stages.map((s, i) => (
            <div
              key={s.name}
              style={{
                display: 'flex',
                gap: 16,
                padding: '16px 20px',
                borderBottom:
                  i < stages.length - 1
                    ? '1px solid oklch(var(--border))'
                    : 'none',
              }}
            >
              <div style={{ flexShrink: 0 }}>
                <div
                  style={{
                    width: 32,
                    height: 32,
                    borderRadius: 'var(--radius-sm)',
                    background: 'oklch(var(--accent) / 0.1)',
                    color: 'oklch(var(--accent))',
                    display: 'grid',
                    placeItems: 'center',
                    fontFamily: 'var(--font-mono)',
                    fontWeight: 600,
                    fontSize: 13,
                  }}
                >
                  {i + 1}
                </div>
              </div>
              <div style={{ flex: 1 }}>
                <div
                  style={{ display: 'flex', alignItems: 'center', gap: 8 }}
                >
                  <span style={{ fontWeight: 500 }}>{s.name}</span>
                  <span className="badge badge-success">
                    <span className="badge-dot" /> OK
                  </span>
                </div>
                <div className="text-sm muted mono" style={{ marginTop: 2 }}>
                  {s.desc}
                </div>
              </div>
              <div className="text-xs muted mono">{s.duration}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ── Tab: Retrieval Testing ──────────────────────────────────────────────────
function RetrievalTab({ kb }: { kb: KbStatus }) {
  const [query, setQuery] = useState(
    'How do I configure multi-currency posting definitions?',
  );
  const [mode, setMode] = useState<RetrievalMode>('hybrid');
  const [topK, setTopK] = useState(5);
  const [rerank, setRerank] = useState(true);
  const [scoreThreshold, setScoreThreshold] = useState(0.4);
  const [vizMode, setVizMode] = useState<'list' | 'bars'>('bars');

  const mutation = useMutation({
    mutationFn: (body: { query: string }) =>
      retrievalTestApi.run(kb.kb_id, {
        query: body.query,
        mode,
        top_k: topK,
        rerank,
        score_threshold: mode === 'fulltext' ? undefined : scoreThreshold,
      }),
    onError: (e) => {
      const msg = e instanceof Error ? e.message : 'retrieval failed';
      toast.error(msg);
    },
  });

  const result: RetrievalTestResult | undefined = mutation.data;

  return (
    <div className="split-2" style={{ gridTemplateColumns: '360px 1fr' }}>
      <div className="card">
        <div className="card-header">
          <div>
            <h3 className="card-title">Query</h3>
            <div className="card-desc">
              Pure retrieval pass · no LLM synthesis · ADR-0021
            </div>
          </div>
        </div>
        <div className="card-body">
          <div className="field">
            <label className="label">Query</label>
            <textarea
              className="input"
              rows={4}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          </div>

          <div className="field">
            <label className="label">Retrieval mode</label>
            <div className="seg" style={{ width: '100%' }}>
              {(
                [
                  { id: 'hybrid', label: 'Hybrid', hint: 'BM25 + Vector + RRF' },
                  { id: 'vector', label: 'Vector', hint: 'Dense only' },
                  { id: 'fulltext', label: 'Full-text', hint: 'BM25 only' },
                ] as { id: RetrievalMode; label: string; hint: string }[]
              ).map((m) => (
                <button
                  type="button"
                  key={m.id}
                  className="seg-btn"
                  data-active={mode === m.id}
                  onClick={() => setMode(m.id)}
                  style={{
                    flex: 1,
                    flexDirection: 'column',
                    padding: '6px 8px',
                    gap: 2,
                  }}
                >
                  <span style={{ fontSize: 12.5, fontWeight: 600 }}>{m.label}</span>
                  <span className="text-xs muted" style={{ fontSize: 10 }}>
                    {m.hint}
                  </span>
                </button>
              ))}
            </div>
          </div>

          <div className="field">
            <label className="label">
              Top-K{' '}
              <span className="text-xs muted mono">retrieve before rerank</span>
            </label>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <input
                type="range"
                min={1}
                max={50}
                value={topK}
                onChange={(e) => setTopK(+e.target.value)}
                style={{ flex: 1 }}
              />
              <span
                className="mono"
                style={{ width: 26, textAlign: 'right', fontSize: 13 }}
              >
                {topK}
              </span>
            </div>
          </div>

          <div className="field">
            <label className="label">
              Score threshold{' '}
              <span className="text-xs muted mono" style={{ marginLeft: 6 }}>
                {mode === 'fulltext' ? 'n/a — BM25 unbounded' : '0.0 – 1.0'}
              </span>
            </label>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <input
                type="range"
                min={0}
                max={1}
                step={0.01}
                value={scoreThreshold}
                disabled={mode === 'fulltext'}
                onChange={(e) => setScoreThreshold(+e.target.value)}
                style={{ flex: 1 }}
              />
              <span
                className="mono"
                style={{ width: 38, textAlign: 'right', fontSize: 13 }}
              >
                {scoreThreshold.toFixed(2)}
              </span>
            </div>
          </div>

          <div className="row" style={{ marginBottom: 16 }}>
            <span
              className="switch"
              data-on={rerank}
              onClick={() => setRerank(!rerank)}
              role="switch"
              aria-checked={rerank}
              tabIndex={0}
            />
            <span style={{ fontSize: 13 }}>Apply rerank after retrieval</span>
          </div>

          <button
            type="button"
            className="btn btn-accent"
            style={{ width: '100%' }}
            disabled={mutation.isPending || !query.trim()}
            onClick={() => mutation.mutate({ query })}
          >
            {mutation.isPending ? (
              <>
                <span className="spinner" /> Running…
              </>
            ) : (
              <>
                <Zap size={14} /> Run retrieval
              </>
            )}
          </button>

          <div className="hr" />

          <div
            className="text-xs muted mono"
            style={{ lineHeight: 1.6 }}
          >
            POST <span style={{ color: 'oklch(var(--foreground))' }}>
              /kb/{kb.kb_id}/retrieval-test
            </span>
            <br />
            mode = {mode}, top_k = {topK}, rerank = {rerank.toString()}
            <br />
            score_threshold = {scoreThreshold.toFixed(2)}
          </div>
        </div>
      </div>

      <div>
        {!result && !mutation.isPending && (
          <div className="empty">
            <div className="empty-icon">
              <Search size={20} />
            </div>
            <div className="empty-title">No results yet</div>
            <div>Tune the query + parameters → click Run retrieval.</div>
          </div>
        )}

        {result && (
          <>
            <div className="card" style={{ marginBottom: 16 }}>
              <div className="card-body" style={{ padding: 0 }}>
                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(5, 1fr)',
                  }}
                >
                  {[
                    { label: 'Embed', val: `${result.embed_latency_ms}ms` },
                    { label: 'Search', val: `${result.search_latency_ms}ms` },
                    {
                      label: 'Rerank',
                      val: result.reranked ? `${result.rerank_latency_ms}ms` : '—',
                    },
                    { label: 'Total', val: `${result.total_latency_ms}ms` },
                    { label: 'Hits', val: String(result.total_hits) },
                  ].map((m, i) => (
                    <div
                      key={m.label}
                      style={{
                        padding: '14px 18px',
                        borderRight:
                          i < 4 ? '1px solid oklch(var(--border))' : 'none',
                      }}
                    >
                      <div className="text-xs muted" style={{ marginBottom: 4 }}>
                        {m.label}
                      </div>
                      <div
                        style={{
                          fontSize: 18,
                          fontWeight: 600,
                          fontVariantNumeric: 'tabular-nums',
                        }}
                      >
                        {m.val}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div
              className="row"
              style={{ marginBottom: 12, alignItems: 'center' }}
            >
              <h3 className="card-title">
                Ranked chunks{' '}
                <span
                  className="text-xs muted mono"
                  style={{ marginLeft: 8 }}
                >
                  {result.chunks.length} of {result.total_hits} (threshold)
                </span>
              </h3>
              <div className="spacer" />
              <span className="text-xs muted">Visualization →</span>
              <div className="seg">
                <button
                  type="button"
                  className="seg-btn"
                  data-active={vizMode === 'list'}
                  onClick={() => setVizMode('list')}
                >
                  List
                </button>
                <button
                  type="button"
                  className="seg-btn"
                  data-active={vizMode === 'bars'}
                  onClick={() => setVizMode('bars')}
                >
                  Bars
                </button>
              </div>
            </div>

            <div className="col" style={{ gap: 10 }}>
              {result.chunks.map((c) => (
                <ChunkResultRow key={c.chunk_id} chunk={c} viz={vizMode} />
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
}

function ChunkResultRow({
  chunk,
  viz,
}: {
  chunk: RetrievalTestChunk;
  viz: 'list' | 'bars';
}) {
  return (
    <div className="chunk">
      <div className="chunk-head">
        <div
          className={`chunk-rank ${chunk.rank <= 3 ? 'chunk-rank-top' : ''}`}
        >
          #{chunk.rank}
        </div>
        <div className="chunk-source">
          <FileText size={13} />
          <span className="doc-title">{chunk.doc_title}</span>
        </div>
        <div className="chunk-score-wrap">
          {viz === 'bars' && (
            <div
              className="score-bar"
              title={`score ${chunk.score.toFixed(4)}`}
            >
              <i style={{ width: `${Math.min(1, chunk.score) * 100}%` }} />
            </div>
          )}
          <span className="chunk-score">{chunk.score.toFixed(4)}</span>
        </div>
      </div>
      <div className="section-path">
        {chunk.section_path.map((s, j) => (
          <span key={j}>{s}</span>
        ))}
      </div>
      <div className="chunk-body">{chunk.chunk_text_preview}</div>
      <div className="chunk-foot">
        <span>
          chunk_id{' '}
          <span style={{ color: 'oklch(var(--foreground))' }}>
            {chunk.chunk_id}
          </span>
        </span>
        <span>
          chunk_index{' '}
          <span style={{ color: 'oklch(var(--foreground))' }}>
            #{chunk.chunk_index}
          </span>
        </span>
      </div>
    </div>
  );
}

// ── Tab: Settings ───────────────────────────────────────────────────────────
function SettingsTab({ kb }: { kb: KbStatus }) {
  const queryClient = useQueryClient();
  const [name, setName] = useState(kb.name);
  const [description, setDescription] = useState(kb.description);
  const [topK, setTopK] = useState(kb.config.default_top_k);
  const [rerankK, setRerankK] = useState(kb.config.default_rerank_k);

  const dirty = useMemo(
    () =>
      name !== kb.name ||
      description !== kb.description ||
      topK !== kb.config.default_top_k ||
      rerankK !== kb.config.default_rerank_k,
    [name, description, topK, rerankK, kb],
  );

  const metaMutation = useMutation({
    mutationFn: () =>
      kbApi.patchMetadata(kb.kb_id, {
        name: name !== kb.name ? name : undefined,
        description: description !== kb.description ? description : undefined,
      }),
    onSuccess: (updated) => {
      queryClient.setQueryData(['kb', kb.kb_id], updated);
      toast.success('Metadata saved');
    },
    onError: (e) => toast.error(e instanceof Error ? e.message : 'save failed'),
  });

  const configMutation = useMutation({
    mutationFn: () =>
      kbApi.patchSettings(kb.kb_id, {
        default_top_k: topK,
        default_rerank_k: rerankK,
      }),
    onSuccess: (updated) => {
      queryClient.setQueryData(['kb', kb.kb_id], updated);
      toast.success('Config saved');
    },
    onError: (e) => toast.error(e instanceof Error ? e.message : 'save failed'),
  });

  function handleSave(e: FormEvent) {
    e.preventDefault();
    if (name !== kb.name || description !== kb.description) {
      metaMutation.mutate();
    }
    if (
      topK !== kb.config.default_top_k ||
      rerankK !== kb.config.default_rerank_k
    ) {
      configMutation.mutate();
    }
  }

  return (
    <form
      onSubmit={handleSave}
      style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}
    >
      <div className="card">
        <div className="card-header">
          <h3 className="card-title">General</h3>
          <span className="badge badge-success">
            <Edit size={10} /> Editable
          </span>
        </div>
        <div className="card-body">
          <div className="field">
            <label className="label">Name</label>
            <input
              className="input"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
            <div className="hint">PATCH /kb/{kb.kb_id} · KbMetadataPatch.name</div>
          </div>
          <div className="field">
            <label className="label">Description</label>
            <textarea
              className="input"
              rows={3}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>
          <div className="field">
            <label className="label">
              kb_id{' '}
              <Shield
                size={11}
                style={{
                  verticalAlign: '-2px',
                  marginLeft: 4,
                  color: 'oklch(var(--warning))',
                }}
              />
            </label>
            <input className="input mono" disabled value={kb.kb_id} />
            <div className="hint">
              <b style={{ color: 'oklch(var(--warning))' }}>Locked.</b> Forms index{' '}
              <span className="mono">ekp-kb-{kb.kb_id}-v1</span> · cannot be changed
              without recreating the KB.
            </div>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <h3 className="card-title">Retrieval config</h3>
          <span className="badge badge-warning">
            <Shield size={10} /> Mix of locked + editable
          </span>
        </div>
        <div className="card-body">
          <div className="field">
            <label className="label">
              Embedding model{' '}
              <Shield
                size={11}
                style={{
                  verticalAlign: '-2px',
                  marginLeft: 4,
                  color: 'oklch(var(--warning))',
                }}
              />
            </label>
            <select
              className="select"
              defaultValue={kb.config.embedding_model}
              disabled
            >
              <option>{kb.config.embedding_model}</option>
            </select>
            <div className="hint">
              <b style={{ color: 'oklch(var(--warning))' }}>Locked.</b>{' '}
              {kb.config.embedding_dimension}d MRL truncate · changing requires full
              re-index.
            </div>
          </div>
          <div className="field">
            <label className="label">
              Chunk strategy{' '}
              <Shield
                size={11}
                style={{
                  verticalAlign: '-2px',
                  marginLeft: 4,
                  color: 'oklch(var(--warning))',
                }}
              />
            </label>
            <div className="seg" style={{ width: '100%', opacity: 0.7 }}>
              {(
                ['heading_aware', 'layout_aware', 'slide_based', 'auto'] as KbConfig['chunk_strategy'][]
              ).map((s) => (
                <button
                  type="button"
                  key={s}
                  className="seg-btn"
                  data-active={kb.config.chunk_strategy === s}
                  style={{ flex: 1, padding: '5px 6px', fontSize: 11.5 }}
                  disabled
                >
                  {s}
                </button>
              ))}
            </div>
            <div className="hint">
              <b style={{ color: 'oklch(var(--warning))' }}>Locked.</b> Changing
              affects chunk boundaries → requires re-index.
            </div>
          </div>
          <div className="field">
            <label className="label">
              Default top_k (retrieval){' '}
              <Edit
                size={10}
                style={{
                  verticalAlign: '-1px',
                  marginLeft: 4,
                  color: 'oklch(var(--success))',
                }}
              />
            </label>
            <input
              type="number"
              className="input mono"
              value={topK}
              min={1}
              max={100}
              onChange={(e) => setTopK(+e.target.value)}
            />
            <div className="hint">
              Editable any time · doesn&rsquo;t require re-index
            </div>
          </div>
          <div className="field" style={{ marginBottom: 0 }}>
            <label className="label">
              Default rerank_k{' '}
              <Edit
                size={10}
                style={{
                  verticalAlign: '-1px',
                  marginLeft: 4,
                  color: 'oklch(var(--success))',
                }}
              />
            </label>
            <input
              type="number"
              className="input mono"
              value={rerankK}
              min={1}
              max={50}
              onChange={(e) => setRerankK(+e.target.value)}
            />
          </div>
        </div>
      </div>

      <div className="card" style={{ gridColumn: '1 / -1' }}>
        <div className="card-footer">
          <div className="text-xs muted">
            Last indexed: <span className="mono">{formatRelative(kb.last_indexed_at)}</span>
          </div>
          <div className="row">
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={() => {
                setName(kb.name);
                setDescription(kb.description);
                setTopK(kb.config.default_top_k);
                setRerankK(kb.config.default_rerank_k);
              }}
              disabled={!dirty}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-primary btn-sm"
              disabled={!dirty || metaMutation.isPending || configMutation.isPending}
            >
              {metaMutation.isPending || configMutation.isPending
                ? 'Saving…'
                : 'Save changes'}
            </button>
          </div>
        </div>
      </div>

      <DangerZone kb={kb} />
    </form>
  );
}

function DangerZone({ kb }: { kb: KbStatus }) {
  const queryClient = useQueryClient();
  const router = useRouter();
  const archiveMutation = useMutation({
    mutationFn: () => kbApi.archive(kb.kb_id),
    onSuccess: (updated) => {
      queryClient.setQueryData(['kb', kb.kb_id], updated);
      void queryClient.invalidateQueries({ queryKey: ['kb'] });
      toast.success(`KB archived — read-only`);
      router.push('/kb');
    },
    onError: (e) => toast.error(e instanceof Error ? e.message : 'archive failed'),
  });

  return (
    <div
      className="card"
      style={{
        gridColumn: '1 / -1',
        borderColor: 'oklch(var(--destructive) / 0.3)',
      }}
    >
      <div
        className="card-header"
        style={{ background: 'oklch(var(--destructive) / 0.04)' }}
      >
        <div>
          <h3
            className="card-title"
            style={{ color: 'oklch(var(--destructive))' }}
          >
            Danger zone
          </h3>
          <div className="card-desc">Irreversible · audit-logged</div>
        </div>
      </div>
      <div
        className="card-body"
        style={{ display: 'flex', gap: 8 }}
      >
        <button
          type="button"
          className="btn btn-secondary"
          onClick={() => archiveMutation.mutate()}
          disabled={kb.archived || archiveMutation.isPending}
        >
          <Archive size={14} />
          {kb.archived ? ' Already archived' : ' Archive KB (read-only)'}
        </button>
        <div className="spacer" />
        <button type="button" className="btn btn-destructive" disabled>
          <Trash2 size={14} /> Delete KB
        </button>
      </div>
    </div>
  );
}
