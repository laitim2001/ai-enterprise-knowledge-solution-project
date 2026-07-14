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

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
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
  Eye,
  FileText,
  Image as ImageIcon,
  Layers,
  Link2,
  MoreHorizontal,
  RefreshCw,
  Search,
  Settings as SettingsIcon,
  Shield,
  Sparkles,
  Tag,
  Trash2,
  Upload,
  Zap,
  type LucideIcon,
} from 'lucide-react';
import { useTranslations } from 'next-intl';
import { useParams, useRouter, useSearchParams } from 'next/navigation';
import { useMemo, useState, type FormEvent, type ReactNode } from 'react';
import { toast } from 'sonner';

import { TabKbAccess } from '@/components/kb/tab-kb-access';
import {
  configTestApi,
  type ConfigRunSummary,
  type ConfigTestResult,
  type DraftRetrievalConfig,
} from '@/lib/api/config-test';
import { ApiError } from '@/lib/api-client';
import { documentsApi, type ChunkSummary, type DocumentSummary } from '@/lib/api/documents';
import {
  IMAGE_DENSE_PRESET,
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

const TAB_DEFS: { id: TabKey; labelKey: string; icon: LucideIcon }[] = [
  { id: 'documents', labelKey: 'tabDocuments', icon: FileText },
  { id: 'chunks', labelKey: 'tabChunks', icon: Layers },
  { id: 'images', labelKey: 'tabImages', icon: ImageIcon },
  { id: 'chunking-lab', labelKey: 'tabChunkingLab', icon: Zap },
  { id: 'pipeline', labelKey: 'tabPipeline', icon: Zap },
  { id: 'retrieval', labelKey: 'tabRetrievalTesting', icon: Search },
  { id: 'settings', labelKey: 'tabSettings', icon: SettingsIcon },
  { id: 'access', labelKey: 'tabAccess', icon: Shield },
];

function formatRelative(
  iso: string | null | undefined,
  t: ReturnType<typeof useTranslations>,
): string {
  if (!iso) return '—';
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return '—';
  const diff = Date.now() - then;
  const minutes = Math.round(diff / 60_000);
  if (minutes < 1) return t('relativeJustNow');
  if (minutes < 60) return t('relativeMinutes', { minutes });
  const hours = Math.round(minutes / 60);
  if (hours < 24) return t('relativeHours', { hours });
  const days = Math.round(hours / 24);
  if (days < 30) return t('relativeDays', { days });
  return new Date(iso).toLocaleDateString();
}

// W77 / ADR-0056 層 A 段③ — 文件畫像 badge(L2 文件列表)per mockup ekp-page-kb.jsx:139-159.
// profile = W72 profiler 分類;低信心 → badge-warning 黃旗 + 信心度;未分析(profile=null,
// ingest 未成功 / 未 re-index)→ muted「未分析」。
const PROFILE_LABELS: Record<string, string> = {
  P1_sop_imgdense: 'P1 Image-dense SOP',
  P1_sop_text: 'P1 Text SOP',
  P2_prose: 'P2 Prose',
  P3_slide_imgdense: 'P3 Image-dense slides',
  P3_slide_text: 'P3 Text slides',
  P4_scan_imgdense: 'P4 Scan',
  P5_form: 'P5 Form',
};

function ProfileBadge({
  profile,
  confidence,
}: {
  profile?: string | null;
  confidence?: number | null;
}) {
  const t = useTranslations('KbDetail');
  if (!profile) {
    return (
      <span className="badge badge-muted" style={{ opacity: 0.65 }}>
        {t('profileNotAnalyzed')}
      </span>
    );
  }
  // L2 輕量 summary 無 fallback_applied 欄;低信心用 confidence < 0.7 判(per W78 plan §4-1，
  // 視覺零差 — fallback doc confidence 必 < 0.7)。完整 fallback 判斷喺 L3 文件畫像。
  const low = confidence != null && confidence < 0.7;
  const label = PROFILE_LABELS[profile] ?? profile;
  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 5 }}>
      <span
        className={`badge ${low ? 'badge-warning' : 'badge-muted'}`}
        title={low ? t('profileLowConfTitle') : t('profileDetectedTitle')}
      >
        <span className="badge-dot" /> {label}
      </span>
      {confidence != null && (
        <span className="text-xs muted mono">{Math.round(confidence * 100)}%</span>
      )}
    </span>
  );
}

export default function KbDetailPage() {
  const t = useTranslations('KbDetail');
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
            <div style={{ flex: 1 }}>{t('loadingKb')}</div>
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
              {t('errorLoadKb', {
                kbId,
                msg: String((query.error as Error)?.message ?? 'unknown'),
              })}
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
                <ChevronLeft size={12} /> {t('backKnowledge')}
              </button>
              <span className="muted mono text-xs">·</span>
              <span className="muted mono text-xs">ekp-kb-{kb.kb_id}-v1</span>
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
              <Search size={13} /> {t('btnRetrievalTest')}
            </button>
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={() => handleTabChange('settings')}
            >
              <RefreshCw size={13} /> {t('btnReindex')}
            </button>
            <button
              type="button"
              className="btn btn-primary btn-sm"
              onClick={() => router.push(`/kb/${kb.kb_id}/upload`)}
            >
              <Upload size={13} /> {t('btnUploadDocuments')}
            </button>
          </div>
        </div>

        {kb.failed_documents.length > 0 && (
          <div className="banner banner-warning">
            <AlertTriangle size={16} style={{ color: 'oklch(var(--warning))' }} />
            <div style={{ flex: 1 }}>
              <div style={{ fontWeight: 500 }}>
                {t('failedToIndex', { count: kb.failed_documents.length })}
              </div>
              <div className="muted text-xs">{t('failedBannerDesc')}</div>
            </div>
            <button
              type="button"
              className="btn btn-ghost btn-sm"
              onClick={() => handleTabChange('documents')}
            >
              {t('btnViewErrors')}
            </button>
          </div>
        )}

        {/* Tabs */}
        <div className="tabs" role="tablist" aria-label={t('tablistAria')}>
          {TAB_DEFS.map((tabDef) => {
            const Ic = tabDef.icon;
            const count = totalCounts[tabDef.id];
            return (
              <button
                key={tabDef.id}
                type="button"
                role="tab"
                aria-selected={activeTab === tabDef.id}
                className="tab"
                data-active={activeTab === tabDef.id}
                onClick={() => handleTabChange(tabDef.id)}
              >
                <Ic size={14} /> {t(tabDef.labelKey)}
                {count != null && <span className="count">{count.toLocaleString()}</span>}
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
  const t = useTranslations('KbDetail');
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
        <div style={{ flex: 1 }}>{t('loadingDocuments')}</div>
      </div>
    );
  }
  if (docs.isError) {
    return (
      <div className="banner banner-error">
        <AlertTriangle size={16} />
        <div style={{ flex: 1 }}>
          {t('errorLoadDocuments', {
            msg: String((docs.error as Error)?.message ?? 'unknown'),
          })}
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
        <div className="empty-title">{t('emptyDocsTitle')}</div>
        <div>{t('emptyDocsDesc')}</div>
        <button
          type="button"
          className="btn btn-primary btn-sm"
          style={{ marginTop: 12 }}
          onClick={() => router.push(`/kb/${kb.kb_id}/upload`)}
        >
          <Upload size={13} /> {t('btnUploadDocument')}
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
          <input className="input" placeholder={t('searchDocsPlaceholder')} />
        </div>
        <div className="seg">
          {(['all', 'indexed', 'indexing', 'failed', 'queued'] as DocStatusFilter[]).map((f) => (
            <button
              type="button"
              key={f}
              className="seg-btn"
              data-active={filter === f}
              onClick={() => setFilter(f)}
            >
              {t(`docFilter_${f}`)}
              <span className="mono text-xs" style={{ opacity: 0.6 }}>
                {filterCounts[f]}
              </span>
            </button>
          ))}
        </div>
        <div className="spacer" />
        <button type="button" className="btn btn-secondary btn-sm" disabled>
          <Download size={13} /> {t('btnExportCsv')}
        </button>
      </div>

      <div className="table-wrap">
        <table className="table">
          <thead>
            <tr>
              <th>{t('colDocument')}</th>
              <th>{t('colType')}</th>
              <th className="col-num">{t('colChunks')}</th>
              <th>{t('colTags')}</th>
              <th>{t('colProfile')}</th>
              <th>{t('colStatus')}</th>
              <th className="col-num">{t('colIndexed')}</th>
              <th className="col-shrink" aria-label={t('rowActions')} />
            </tr>
          </thead>
          <tbody>
            {filtered.map((d) => (
              <tr
                key={d.doc_id}
                onClick={() => router.push(`/kb/${kb.kb_id}/docs/${encodeURIComponent(d.doc_id)}`)}
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
                  <div className="muted mono text-xs">{d.doc_id}</div>
                </td>
                <td>
                  <span className="mono text-xs" style={{ textTransform: 'uppercase' }}>
                    {d.doc_format || '—'}
                  </span>
                </td>
                <td className="col-num">{d.total_chunks}</td>
                <td>
                  {d.tags.length > 0 ? (
                    <span style={{ display: 'inline-flex', gap: 4, flexWrap: 'wrap' }}>
                      {d.tags.slice(0, 3).map((t) => (
                        <span key={t} className="badge badge-muted">
                          {t}
                        </span>
                      ))}
                    </span>
                  ) : (
                    <span className="muted text-xs">—</span>
                  )}
                </td>
                <td>
                  <ProfileBadge profile={d.profile} confidence={d.profile_confidence} />
                </td>
                <td>
                  <span className="badge badge-success">
                    <span className="badge-dot" /> INDEXED
                  </span>
                </td>
                <td className="col-num text-xs">{formatRelative(d.last_indexed_at, t)}</td>
                <td className="col-shrink">
                  <button
                    type="button"
                    className="btn btn-ghost btn-icon btn-xs"
                    aria-label={t('moreActions')}
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
          {t('showingCount', { shown: filtered.length, total: all.length })}
        </div>
        <div className="row">
          <button
            type="button"
            className="btn btn-ghost btn-icon btn-xs"
            disabled
            aria-label={t('prevPage')}
          >
            <ChevronLeft size={13} />
          </button>
          <span className="mono text-xs">1 / 1</span>
          <button
            type="button"
            className="btn btn-ghost btn-icon btn-xs"
            disabled
            aria-label={t('nextPage')}
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
  const t = useTranslations('KbDetail');
  const router = useRouter();
  const searchParams = useSearchParams();
  const docs = useQuery<DocumentSummary[]>({
    queryKey: ['kb', kb.kb_id, 'documents'],
    queryFn: () => documentsApi.list(kb.kb_id),
  });

  const docList = docs.data ?? [];
  const docParam = searchParams.get('doc');
  const selectedDocId =
    docParam && docList.some((d) => d.doc_id === docParam) ? docParam : docList[0]?.doc_id;

  const chunks = useQuery<ChunkSummary[]>({
    queryKey: ['kb', kb.kb_id, 'chunks', selectedDocId],
    queryFn: () => documentsApi.listChunks(kb.kb_id, selectedDocId!),
    enabled: !!selectedDocId,
  });

  const [selectedChunkId, setSelectedChunkId] = useState<string | null>(null);
  const chunkList = chunks.data ?? [];
  const activeChunk = chunkList.find((c) => c.chunk_id === selectedChunkId) ?? chunkList[0];

  if (docs.isLoading) {
    return (
      <div className="banner banner-info">
        <span className="spinner" />
        <div style={{ flex: 1 }}>{t('loadingDocuments')}</div>
      </div>
    );
  }
  if (docList.length === 0) {
    return (
      <div className="empty">
        <div className="empty-icon">
          <Layers size={20} />
        </div>
        <div className="empty-title">{t('emptyChunksTitle')}</div>
        <div>{t('emptyChunksDesc')}</div>
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
          {t('labelDocument')}
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
              {d.doc_title || d.doc_id} ({t('optionChunks', { count: d.total_chunks })})
            </option>
          ))}
        </select>
      </div>

      <div className="split-2">
        <div className="card">
          <div className="card-header">
            <div>
              <h3 className="card-title">{t('browseChunksTitle')}</h3>
              <div className="card-desc">
                {t('chunksInSelectedDoc', { count: chunkList.length.toLocaleString() })}
              </div>
            </div>
          </div>
          <div className="card-body card-body-tight" style={{ maxHeight: 540, overflowY: 'auto' }}>
            {chunks.isLoading && (
              <div style={{ padding: 14 }} className="muted text-xs">
                {t('loadingChunks')}
              </div>
            )}
            {chunks.isError && (
              <div style={{ padding: 14 }} className="text-xs">
                {t('errorLoadChunks', { msg: String((chunks.error as Error)?.message) })}
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
                    borderLeft: active ? '2px solid oklch(var(--accent))' : '2px solid transparent',
                  }}
                >
                  <div className="mono muted text-xs" style={{ marginBottom: 2 }}>
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
              <h3 className="card-title">{t('chunkPreviewTitle')}</h3>
              <div className="card-desc">
                {activeChunk ? <span className="mono">{activeChunk.chunk_id}</span> : '—'}
              </div>
            </div>
            <div className="row">
              <button
                type="button"
                className="btn btn-ghost btn-icon btn-sm"
                aria-label={t('ariaEdit')}
                disabled
              >
                <Edit size={14} />
              </button>
              <button
                type="button"
                className="btn btn-ghost btn-icon btn-sm"
                aria-label={t('ariaCopy')}
                onClick={() => {
                  if (activeChunk) {
                    void navigator.clipboard
                      .writeText(activeChunk.chunk_id)
                      .then(() => toast.success(t('toastChunkIdCopied')))
                      .catch(() => toast.error(t('toastCopyFailed')));
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
                    {t('badgeOf')} <b style={{ marginLeft: 2 }}>{activeChunk.chunk_total}</b>
                  </span>
                  {activeChunk.low_value_flag && (
                    <span className="badge badge-warning">low_value</span>
                  )}
                  {!activeChunk.enabled && (
                    <span className="badge badge-error">{t('badgeDisabled')}</span>
                  )}
                </div>
                <div className="section-path text-sm" style={{ marginBottom: 14 }}>
                  {activeChunk.section_path.map((s, j) => (
                    <span key={j}>{s}</span>
                  ))}
                </div>
                <div className="muted text-xs">{t('chunkBodyNotListed')}</div>
              </>
            ) : (
              <div className="muted text-xs">{t('selectChunkToPreview')}</div>
            )}
          </div>
          {activeChunk && (
            <div className="card-footer">
              <div className="muted mono text-xs">
                embedding_model · {kb.config.embedding_model} · {kb.config.embedding_dimension}d MRL
              </div>
              <button type="button" className="btn btn-ghost btn-xs" disabled>
                {t('btnViewRawEmbedding')}
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
  const t = useTranslations('KbDetail');
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
            <Layers size={13} /> {t('statExtractedImages')}
          </div>
          <div className="stat-value">{kb.total_screenshots}</div>
          <div className="stat-meta">
            {t('statAcrossDocs', { count: kb.total_documents })}
          </div>
        </div>
        <div className="stat">
          <div className="stat-label">
            <Shield size={13} /> {t('statSha256Dedup')}
          </div>
          <div className="stat-value">
            {dedupSavings}
            <span className="stat-unit">{t('statUnitDeduped')}</span>
          </div>
          <div className="stat-meta">{t('statSha256Sub', { refs: totalRefs })}</div>
        </div>
        <div className="stat">
          <div className="stat-label">
            <Database size={13} /> {t('statBlobStorage')}
          </div>
          <div className="stat-value">
            {(totalSizeKb / 1024).toFixed(1)}
            <span className="stat-unit"> MB</span>
          </div>
          <div className="stat-meta mono">ekp-kb-{kb.kb_id}-screenshots</div>
        </div>
        <div className="stat">
          <div className="stat-label">
            <AlertTriangle size={13} /> {t('statLowValueFlagged')}
          </div>
          <div className="stat-value">0</div>
          <div className="stat-meta">{t('statLowValueSub')}</div>
        </div>
      </div>

      <div className="banner banner-info" style={{ marginBottom: 16 }}>
        <Sparkles size={15} style={{ color: 'oklch(var(--info))' }} />
        <div style={{ flex: 1, lineHeight: 1.5 }}>
          <div style={{ fontSize: 13, fontWeight: 500 }}>{t('howChunksRefImagesTitle')}</div>
          <div className="muted mono text-xs" style={{ marginTop: 2 }}>
            Parser extracts{' '}
            <b style={{ color: 'oklch(var(--foreground))' }}>
              EmbeddedImage{`{sha256, alt_text, doc_order}`}
            </b>{' '}
            → Extractor adds kb_id/doc_id → Uploader pushes blob with{' '}
            <b style={{ color: 'oklch(var(--foreground))' }}>{'{sha256}.{ext}'}</b> path (cross-doc
            dedup) → Chunker references via{' '}
            <b style={{ color: 'oklch(var(--foreground))' }}>embedded_image_positions</b> →
            Orchestrator resolves to{' '}
            <b style={{ color: 'oklch(var(--foreground))' }}>ImageRef.blob_url</b> in ChunkRecord.
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
          <input className="input" placeholder={t('searchImagesPlaceholder')} />
        </div>
        <div className="spacer" />
        <button type="button" className="btn btn-secondary btn-sm" disabled>
          <Download size={13} /> {t('btnExportManifest')}
        </button>
      </div>

      {images.isLoading ? (
        <div className="banner banner-info">
          <span className="spinner" />
          <div style={{ flex: 1 }}>{t('loadingImages')}</div>
        </div>
      ) : images.isError ? (
        <div className="banner banner-error">
          <AlertTriangle size={16} />
          <div style={{ flex: 1 }}>
            {t('errorLoadImages', { msg: String((images.error as Error)?.message ?? 'unknown') })}
          </div>
        </div>
      ) : items.length === 0 ? (
        <div className="empty">
          <div className="empty-icon">
            <ImageIcon size={20} />
          </div>
          <div className="empty-title">{t('emptyImagesTitle')}</div>
          <div>{t('emptyImagesDesc')}</div>
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
  const t = useTranslations('KbDetail');
  const colors = [
    'oklch(var(--accent))',
    'oklch(0.62 0.13 200)',
    'oklch(0.65 0.14 145)',
    'oklch(0.60 0.16 285)',
    'oklch(0.65 0.18 25)',
  ];
  const c = colors[idx % colors.length];
  // BUG-011: render real screenshot thumbnail via the BUG-010 proxy URL with
  // onError fallback to the mockup gradient + Layers placeholder. H7 deviation
  // Option A authorised 2026-05-23 — mockup placeholder is a static-prototype
  // limitation (no image server), not a design choice.
  const [imgError, setImgError] = useState(false);
  const showPlaceholder = !img.url || imgError;
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
          position: 'relative',
          ...(showPlaceholder
            ? {
                backgroundImage: `linear-gradient(135deg, ${c.replace(
                  ')',
                  ' / 0.2)',
                )}, ${c.replace(')', ' / 0.05)')})`,
                display: 'grid',
                placeItems: 'center',
                color: c,
              }
            : { background: 'oklch(var(--muted) / 0.4)' }),
        }}
      >
        {showPlaceholder ? (
          <Layers size={28} />
        ) : (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={img.url}
            alt={img.ocr_text || t('altScreenshotThumbnail')}
            loading="lazy"
            onError={() => setImgError(true)}
            style={{
              width: '100%',
              height: '100%',
              objectFit: 'cover',
              display: 'block',
            }}
          />
        )}
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
          {img.page_num != null ? t('pageAbbrev', { n: img.page_num }) : '—'}
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
          {img.ocr_text || <span className="muted">{t('noOcrText')}</span>}
        </div>
        <div
          className="muted mono text-xs"
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
            {img.screenshot_type || t('badgeScreenshot')}
          </span>
        </div>
      </div>
    </div>
  );
}

// ── Tab: Chunking Lab ───────────────────────────────────────────────────────
const CHUNK_STRATEGIES: {
  id: KbConfig['chunk_strategy'];
  labelKey: string;
  hintKey: string;
  supported: boolean;
  skipReasonKey?: string;
}[] = [
  {
    id: 'layout_aware',
    labelKey: 'stratLayoutAwareLabel',
    hintKey: 'stratLayoutAwareHint',
    supported: true,
  },
  {
    id: 'slide_based',
    labelKey: 'stratSlideBasedLabel',
    hintKey: 'stratSlideBasedHint',
    supported: true,
  },
  {
    id: 'heading_aware',
    labelKey: 'stratHeadingAwareLabel',
    hintKey: 'stratHeadingAwareHint',
    supported: false,
    skipReasonKey: 'stratHeadingAwareSkipReason',
  },
  {
    id: 'auto',
    labelKey: 'stratAutoLabel',
    hintKey: 'stratAutoHint',
    supported: true,
  },
];

function ChunkingLabTab({ kb }: { kb: KbStatus }) {
  const t = useTranslations('KbDetail');
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
      const msg = e instanceof Error ? e.message : t('previewFailedToast');
      toast.error(msg);
    },
  });

  return (
    <div>
      <div className="banner banner-info" style={{ marginBottom: 16 }}>
        <Sparkles size={15} style={{ color: 'oklch(var(--info))' }} />
        <div style={{ flex: 1, lineHeight: 1.5 }}>
          <div style={{ fontSize: 13, fontWeight: 500 }}>{t('previewChunkingTitle')}</div>
          <div className="muted text-xs" style={{ marginTop: 2 }}>
            {t.rich('chunkingLabExplainer', { mono: (c) => <span className="mono">{c}</span> })}
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
              <h3 className="card-title">{t('sampleTextTitle')}</h3>
              <div className="card-desc">{t('sampleTextDesc')}</div>
            </div>
          </div>
          <div className="card-body">
            <textarea
              className="input"
              rows={6}
              placeholder={t('sampleTextPlaceholder')}
              value={sampleText}
              onChange={(e) => setSampleText(e.target.value)}
            />
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h3 className="card-title">{t('chunkingParamsTitle')}</h3>
          </div>
          <div className="card-body">
            <div className="field" style={{ marginBottom: 12 }}>
              <label className="label">
                {t('labelChunkSize')}{' '}
                <span className="muted mono text-xs" style={{ marginLeft: 6 }}>
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
                {t('labelOverlap')}{' '}
                <span className="muted mono text-xs" style={{ marginLeft: 6 }}>
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
        {t('strategyComparisonTitle')}
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
                activeStrategy === s.id ? 'oklch(var(--accent))' : 'oklch(var(--border))'
              }`,
              background:
                activeStrategy === s.id ? 'oklch(var(--accent) / 0.05)' : 'oklch(var(--card))',
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
              <span style={{ fontWeight: 600, fontSize: 13.5 }}>{t(s.labelKey)}</span>
              {!s.supported && <span className="badge badge-muted">{t('badgeNa')}</span>}
            </div>
            <div className="muted text-xs" style={{ marginBottom: 10, lineHeight: 1.4 }}>
              {t(s.hintKey)}
            </div>
            {!s.supported && s.skipReasonKey && (
              <div className="muted text-xs" style={{ lineHeight: 1.5, padding: '8px 0' }}>
                <span
                  style={{
                    color: 'oklch(var(--destructive))',
                    fontWeight: 500,
                  }}
                >
                  {t('notAvailablePrefix')}
                </span>
                {t(s.skipReasonKey)}
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="card">
        <div className="card-header">
          <div>
            <h3 className="card-title">
              {t('outputPreview')} ·{' '}
              {t(
                CHUNK_STRATEGIES.find((s) => s.id === activeStrategy)?.labelKey ?? 'stratAutoLabel',
              )}
            </h3>
            <div className="card-desc">
              {t('outputPreviewDesc', { count: preview.data?.items.length ?? 0 })}
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
                <span className="spinner" /> {t('running')}
              </>
            ) : (
              <>
                <Zap size={13} /> {t('btnRunPreview')}
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
                    i < preview.data!.items.length - 1 ? '1px solid oklch(var(--border))' : 'none',
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
                  <span style={{ fontSize: 13, fontWeight: 500, flex: 1 }}>{c.chunk_title}</span>
                  {c.low_value_flag && <span className="badge badge-warning">low_value</span>}
                  <span className="mono muted text-xs">{c.chunk_token_count} tok</span>
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
                {preview.isError ? t('previewFailed') : t('noPreviewYet')}
              </div>
              <div>
                {preview.isError
                  ? String((preview.error as Error)?.message ?? 'unknown')
                  : t('pastePreviewHint')}
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
  const t = useTranslations('KbDetail');
  const stages = [
    {
      name: t('stage1Name'),
      desc: t('stage1Desc'),
      duration: '—',
    },
    {
      name: t('stage2Name'),
      desc: 'Docling (PDF + DOCX) · python-pptx (slide_based)',
      duration: 'avg 8s/doc',
    },
    {
      name: t('stage3Name'),
      desc: t('stage3Desc', { strategy: kb.config.chunk_strategy }),
      duration: 'avg 1s/doc',
    },
    {
      name: t('stage4Name'),
      desc: `Azure OpenAI ${kb.config.embedding_model} · ${kb.config.embedding_dimension}d MRL truncate`,
      duration: 'avg 0.4s/chunk',
    },
    {
      name: t('stage5Name'),
      desc: `ekp-kb-${kb.kb_id}-v1 · HNSW vector + BM25 lexical`,
      duration: 'avg 0.1s/chunk',
    },
    {
      name: t('stage6Name'),
      desc: 'RAGAs 4-metric · per W17 F3',
      duration: '—',
    },
  ];
  return (
    <div>
      <div className="banner banner-success" style={{ marginBottom: 16 }}>
        <Check size={15} style={{ color: 'oklch(var(--success))' }} />
        <div style={{ flex: 1 }}>
          <div style={{ fontWeight: 500 }}>{t('pipelineHealthy')}</div>
          <div className="muted text-xs">
            {t('pipelineHealthyDesc', { when: formatRelative(kb.last_indexed_at, t) })}
          </div>
        </div>
        <button type="button" className="btn btn-secondary btn-sm" disabled>
          {t('btnTriggerFullReindex')}
        </button>
      </div>

      <div className="card">
        <div className="card-header">
          <h3 className="card-title">{t('indexingPipelineTitle')}</h3>
        </div>
        <div className="card-body card-body-tight">
          {stages.map((s, i) => (
            <div
              key={s.name}
              style={{
                display: 'flex',
                gap: 16,
                padding: '16px 20px',
                borderBottom: i < stages.length - 1 ? '1px solid oklch(var(--border))' : 'none',
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
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span style={{ fontWeight: 500 }}>{s.name}</span>
                  <span className="badge badge-success">
                    <span className="badge-dot" /> OK
                  </span>
                </div>
                <div className="muted mono text-sm" style={{ marginTop: 2 }}>
                  {s.desc}
                </div>
              </div>
              <div className="muted mono text-xs">{s.duration}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ── Tab: Retrieval Testing ──────────────────────────────────────────────────
function RetrievalTab({ kb }: { kb: KbStatus }) {
  const t = useTranslations('KbDetail');
  const [query, setQuery] = useState('How do I configure multi-currency posting definitions?');
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
      const msg = e instanceof Error ? e.message : t('retrievalFailedToast');
      toast.error(msg);
    },
  });

  const result: RetrievalTestResult | undefined = mutation.data;

  return (
    <div className="split-2" style={{ gridTemplateColumns: '360px 1fr' }}>
      <div className="card">
        <div className="card-header">
          <div>
            <h3 className="card-title">{t('queryTitle')}</h3>
            <div className="card-desc">{t('queryDesc')}</div>
          </div>
        </div>
        <div className="card-body">
          <div className="field">
            <label className="label">{t('labelQuery')}</label>
            <textarea
              className="input"
              rows={4}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          </div>

          <div className="field">
            <label className="label">{t('labelRetrievalMode')}</label>
            <div className="seg" style={{ width: '100%' }}>
              {(
                [
                  { id: 'hybrid', label: t('modeHybridLabel'), hint: t('modeHybridHint') },
                  { id: 'vector', label: t('modeVectorLabel'), hint: t('modeVectorHint') },
                  { id: 'fulltext', label: t('modeFulltextLabel'), hint: t('modeFulltextHint') },
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
                  <span className="muted text-xs" style={{ fontSize: 10 }}>
                    {m.hint}
                  </span>
                </button>
              ))}
            </div>
          </div>

          <div className="field">
            <label className="label">
              Top-K <span className="muted mono text-xs">{t('topKHint')}</span>
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
              <span className="mono" style={{ width: 26, textAlign: 'right', fontSize: 13 }}>
                {topK}
              </span>
            </div>
          </div>

          <div className="field">
            <label className="label">
              {t('labelScoreThreshold')}{' '}
              <span className="muted mono text-xs" style={{ marginLeft: 6 }}>
                {mode === 'fulltext' ? t('scoreThresholdNa') : '0.0 – 1.0'}
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
              <span className="mono" style={{ width: 38, textAlign: 'right', fontSize: 13 }}>
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
            <span style={{ fontSize: 13 }}>{t('labelApplyRerank')}</span>
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
                <span className="spinner" /> {t('running')}
              </>
            ) : (
              <>
                <Zap size={14} /> {t('btnRunRetrieval')}
              </>
            )}
          </button>

          <div className="hr" />

          <div className="muted mono text-xs" style={{ lineHeight: 1.6 }}>
            POST{' '}
            <span style={{ color: 'oklch(var(--foreground))' }}>/kb/{kb.kb_id}/retrieval-test</span>
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
            <div className="empty-title">{t('noResultsYet')}</div>
            <div>{t('noResultsDesc')}</div>
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
                    { label: t('metricEmbed'), val: `${result.embed_latency_ms}ms` },
                    { label: t('metricSearch'), val: `${result.search_latency_ms}ms` },
                    {
                      label: t('metricRerank'),
                      val: result.reranked ? `${result.rerank_latency_ms}ms` : '—',
                    },
                    { label: t('metricTotal'), val: `${result.total_latency_ms}ms` },
                    { label: t('metricHits'), val: String(result.total_hits) },
                  ].map((m, i) => (
                    <div
                      key={m.label}
                      style={{
                        padding: '14px 18px',
                        borderRight: i < 4 ? '1px solid oklch(var(--border))' : 'none',
                      }}
                    >
                      <div className="muted text-xs" style={{ marginBottom: 4 }}>
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

            <div className="row" style={{ marginBottom: 12, alignItems: 'center' }}>
              <h3 className="card-title">
                {t('rankedChunksTitle')}{' '}
                <span className="muted mono text-xs" style={{ marginLeft: 8 }}>
                  {t('rankedChunksMeta', { shown: result.chunks.length, total: result.total_hits })}
                </span>
              </h3>
              <div className="spacer" />
              <span className="muted text-xs">{t('vizLabel')}</span>
              <div className="seg">
                <button
                  type="button"
                  className="seg-btn"
                  data-active={vizMode === 'list'}
                  onClick={() => setVizMode('list')}
                >
                  {t('vizList')}
                </button>
                <button
                  type="button"
                  className="seg-btn"
                  data-active={vizMode === 'bars'}
                  onClick={() => setVizMode('bars')}
                >
                  {t('vizBars')}
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

function ChunkResultRow({ chunk, viz }: { chunk: RetrievalTestChunk; viz: 'list' | 'bars' }) {
  return (
    <div className="chunk">
      <div className="chunk-head">
        <div className={`chunk-rank ${chunk.rank <= 3 ? 'chunk-rank-top' : ''}`}>#{chunk.rank}</div>
        <div className="chunk-source">
          <FileText size={13} />
          <span className="doc-title">{chunk.doc_title}</span>
        </div>
        <div className="chunk-score-wrap">
          {viz === 'bars' && (
            <div className="score-bar" title={`score ${chunk.score.toFixed(4)}`}>
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
          chunk_id <span style={{ color: 'oklch(var(--foreground))' }}>{chunk.chunk_id}</span>
        </span>
        <span>
          chunk_index{' '}
          <span style={{ color: 'oklch(var(--foreground))' }}>#{chunk.chunk_index}</span>
        </span>
      </div>
    </div>
  );
}

// ── W43 F3.2/F3.3 — per-KB advanced retrieval tuning + config-test (ADR-0040) ──
type TuneKnobKey =
  | 'enable_parent_doc_retrieval'
  | 'parent_doc_section_depth_offset'
  | 'parent_doc_top_k'
  | 'parent_doc_max_tokens_per_parent'
  | 'enable_citation_post_hoc_expansion'
  | 'citation_expansion_max_aux'
  | 'citation_expansion_window'
  | 'citation_expansion_section_path_prefix_depth'
  | 'enable_citation_neighbour_images'
  | 'citation_neighbour_max_aux_images'
  | 'citation_neighbour_section_path_prefix_depth'
  | 'max_images_per_answer'
  | 'enable_inline_image_markers';

type KnobState = Record<TuneKnobKey, number | boolean | null>;

const TUNE_GROUPS: {
  icon: LucideIcon;
  titleKey: string;
  descKey: string;
  enableKey: TuneKnobKey;
  knobs: { key: TuneKnobKey; labelKey: string }[];
}[] = [
  {
    icon: Layers,
    titleKey: 'tuneParentTitle',
    descKey: 'tuneParentDesc',
    enableKey: 'enable_parent_doc_retrieval',
    knobs: [
      { key: 'parent_doc_section_depth_offset', labelKey: 'knobSectionDepthOffset' },
      { key: 'parent_doc_top_k', labelKey: 'knobParentTopK' },
      { key: 'parent_doc_max_tokens_per_parent', labelKey: 'knobMaxTokensPerParent' },
    ],
  },
  {
    icon: Link2,
    titleKey: 'tuneCitationExpTitle',
    descKey: 'tuneCitationExpDesc',
    enableKey: 'enable_citation_post_hoc_expansion',
    knobs: [
      { key: 'citation_expansion_max_aux', labelKey: 'knobMaxAuxPerCitation' },
      { key: 'citation_expansion_window', labelKey: 'knobExpansionWindow' },
      { key: 'citation_expansion_section_path_prefix_depth', labelKey: 'knobSectionPathPrefixDepth' },
    ],
  },
  {
    icon: Eye,
    titleKey: 'tuneNeighbourImgTitle',
    descKey: 'tuneNeighbourImgDesc',
    enableKey: 'enable_citation_neighbour_images',
    knobs: [
      { key: 'citation_neighbour_max_aux_images', labelKey: 'knobNeighbourMaxAuxImages' },
      { key: 'citation_neighbour_section_path_prefix_depth', labelKey: 'knobNeighbourPrefixDepth' },
      { key: 'max_images_per_answer', labelKey: 'knobMaxImagesPerAnswer' },
    ],
  },
  // W70 (ADR-0055) — bool-only knob (no 進階 numeric grid; mockup ekp-page-kb.jsx
  // tuning card 第 4 行). ON = answers carry [IMG#sha8] position markers (display
  // strips them until the W71 interleaved render).
  {
    icon: Tag,
    titleKey: 'tuneInlineMarkersTitle',
    descKey: 'tuneInlineMarkersDesc',
    enableKey: 'enable_inline_image_markers',
    knobs: [],
  },
];

const TUNE_KNOB_KEYS: TuneKnobKey[] = TUNE_GROUPS.flatMap((g) => [
  g.enableKey,
  ...g.knobs.map((k) => k.key),
]);

// IMAGE_DENSE_PRESET moved to lib/api/kb.ts so the /kb/new wizard can apply the
// same W69 image-dense recall preset at create time (single source of truth).

// One number knob. null = inherit (empty input + 繼承全域 placeholder); a value =
// per-KB override (badge + ↺ 還原全域). The env-driven global default value isn't
// surfaced here (would need a settings fetch), so inherit shows "繼承全域" rather
// than a fabricated number — F3.2 progress note (analogous to BUG-011 placeholder).
function KbTuneKnob({
  label,
  value,
  onChange,
}: {
  label: string;
  value: number | null;
  onChange: (v: number | null) => void;
}) {
  const t = useTranslations('KbDetail');
  const overridden = value !== null;
  return (
    <div className="field" style={{ marginBottom: 0 }}>
      <label className="label" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
        {label}
        {overridden ? (
          <span className="badge badge-success" style={{ fontSize: 9 }}>
            <Edit size={9} /> {t('badgeOverridden')}
          </span>
        ) : (
          <span className="badge badge-muted" style={{ fontSize: 9 }}>
            {t('inheritGlobal')}
          </span>
        )}
      </label>
      <input
        type="number"
        className="input mono"
        value={value ?? ''}
        placeholder={t('inheritGlobal')}
        onChange={(e) => onChange(e.target.value === '' ? null : Number(e.target.value))}
      />
      <div className="hint" style={{ display: 'flex', justifyContent: 'space-between', gap: 8 }}>
        <span>{overridden ? t('overriddenForKb') : t('notOverriddenGlobal')}</span>
        {overridden && (
          <button
            type="button"
            onClick={() => onChange(null)}
            style={{
              display: 'inline-flex',
              gap: 3,
              alignItems: 'center',
              color: 'oklch(var(--muted-foreground))',
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              padding: 0,
              font: 'inherit',
            }}
          >
            <RefreshCw size={10} /> {t('resetToGlobal')}
          </button>
        )}
      </div>
    </div>
  );
}

// A toggle-led group: enable_* switch + title/desc + 繼承/覆寫 badge + collapsible
// 進階 numeric grid. Mirrors the OptionRow visual language (DESIGN_SYSTEM §4.3).
// W70 (ADR-0055) — children optional: a bool-only knob (inline image markers)
// renders the same row WITHOUT the 進階 button / grid (mockup parity).
function KbTuneGroup({
  icon: Ic,
  title,
  desc,
  enabled,
  onToggle,
  onReset,
  children,
}: {
  icon: LucideIcon;
  title: string;
  desc: string;
  enabled: boolean | null;
  onToggle: (v: boolean) => void;
  onReset: () => void;
  children?: ReactNode;
}) {
  const t = useTranslations('KbDetail');
  const [open, setOpen] = useState(false);
  const overridden = enabled !== null;
  return (
    <div
      style={{
        border: '1px solid oklch(var(--border))',
        borderRadius: 'var(--radius-sm)',
        overflow: 'hidden',
      }}
    >
      <div
        style={{
          display: 'flex',
          gap: 12,
          padding: '12px 14px',
          alignItems: 'flex-start',
          background: enabled === true ? 'oklch(var(--muted) / 0.4)' : 'transparent',
        }}
      >
        <span
          className="switch"
          data-on={enabled === true}
          role="switch"
          aria-checked={enabled === true}
          tabIndex={0}
          onClick={() => onToggle(!(enabled === true))}
          style={{ flexShrink: 0, marginTop: 2 }}
        />
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
            <Ic size={13} style={{ color: 'oklch(var(--muted-foreground))' }} />
            <span style={{ fontSize: 13, fontWeight: 500 }}>{title}</span>
            {overridden ? (
              <span className="badge badge-success" style={{ fontSize: 9 }}>
                {t('badgeOverridden')}
              </span>
            ) : (
              <span className="badge badge-muted" style={{ fontSize: 9 }}>
                {t('inheritGlobal')}
              </span>
            )}
            {overridden && (
              <button
                type="button"
                onClick={onReset}
                style={{
                  display: 'inline-flex',
                  gap: 3,
                  alignItems: 'center',
                  fontSize: 11,
                  color: 'oklch(var(--muted-foreground))',
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  padding: 0,
                }}
              >
                <RefreshCw size={10} /> {t('resetToGlobal')}
              </button>
            )}
          </div>
          <div className="muted text-xs" style={{ marginTop: 3, lineHeight: 1.5 }}>
            {desc}
          </div>
        </div>
        {children != null && (
          <button
            type="button"
            className="btn btn-ghost btn-sm"
            style={{ flexShrink: 0 }}
            onClick={() => setOpen(!open)}
            aria-expanded={open}
          >
            {t('btnAdvanced')}{' '}
            <ChevronRight size={11} style={{ transform: open ? 'rotate(90deg)' : 'none' }} />
          </button>
        )}
      </div>
      {open && children != null && (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr 1fr',
            gap: 14,
            padding: 14,
            borderTop: '1px solid oklch(var(--border))',
          }}
        >
          {children}
        </div>
      )}
    </div>
  );
}

// W43 F3.3 — config-test 試跑 panel. Runs the full pipeline N times with the
// current (unsaved) draft knobs, optionally A/B vs the saved config. POST-only —
// persists nothing (that's the separate "儲存到此 KB" save).
function ConfigTestPanel({
  kbId,
  draftConfig,
  onSaveDraft,
  saving,
  dirty,
}: {
  kbId: string;
  draftConfig: DraftRetrievalConfig;
  onSaveDraft: () => void;
  saving: boolean;
  dirty: boolean;
}) {
  const t = useTranslations('KbDetail');
  const [testQuery, setTestQuery] = useState('How do I configure the address book sync?');
  const [runs, setRuns] = useState(3);
  const [compare, setCompare] = useState(true);

  const mutation = useMutation<ConfigTestResult>({
    mutationFn: () =>
      configTestApi.run(kbId, {
        query: testQuery,
        runs,
        draft_config: draftConfig,
        compare_to_saved: compare,
      }),
    onError: (e) => toast.error(e instanceof Error ? e.message : t('toastConfigTestFailed')),
  });
  const result = mutation.data;

  return (
    <div className="card" style={{ gridColumn: '1 / -1' }}>
      <div className="card-header">
        <div>
          <h3 className="card-title">
            <Zap
              size={14}
              style={{ verticalAlign: '-2px', marginRight: 6, color: 'oklch(var(--accent))' }}
            />
            {t('configTestTitle')}
          </h3>
          <div className="card-desc">
            {t('configTestDesc')}{' '}
            <span className="mono">POST /kb/{kbId}/config-test</span>
          </div>
        </div>
      </div>
      <div className="card-body">
        <div
          style={{
            display: 'flex',
            gap: 12,
            alignItems: 'flex-end',
            flexWrap: 'wrap',
            marginBottom: 16,
          }}
        >
          <div className="field" style={{ flex: 1, minWidth: 240, marginBottom: 0 }}>
            <label className="label">{t('labelTestQuestion')}</label>
            <input
              className="input"
              value={testQuery}
              onChange={(e) => setTestQuery(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  if (testQuery.trim() && !mutation.isPending) mutation.mutate();
                }
              }}
            />
          </div>
          <div className="field" style={{ marginBottom: 0 }}>
            <label className="label">{t('labelReruns')}</label>
            <div className="seg">
              {[1, 2, 3, 4, 5].map((n) => (
                <button
                  type="button"
                  key={n}
                  className="seg-btn"
                  data-active={n === runs}
                  style={{ minWidth: 34 }}
                  onClick={() => setRuns(n)}
                >
                  {n}
                </button>
              ))}
            </div>
          </div>
          <label
            className="row"
            style={{
              gap: 6,
              fontSize: 12.5,
              alignItems: 'center',
              cursor: 'pointer',
              paddingBottom: 8,
            }}
          >
            <span
              className="switch"
              data-on={compare}
              role="switch"
              aria-checked={compare}
              tabIndex={0}
              onClick={() => setCompare(!compare)}
            />
            {t('labelCompareToSaved')}
          </label>
          <button
            type="button"
            className="btn btn-primary"
            disabled={mutation.isPending || !testQuery.trim()}
            onClick={() => mutation.mutate()}
          >
            {mutation.isPending ? (
              <>
                <span className="spinner" /> {t('running')}
              </>
            ) : (
              <>
                <Zap size={14} /> {t('btnTestRun')}
              </>
            )}
          </button>
        </div>

        {!result && !mutation.isPending && (
          <div className="empty">
            <div className="empty-icon">
              <Zap size={20} />
            </div>
            <div className="empty-title">{t('noTestRunYet')}</div>
            <div>{t('noTestRunDesc')}</div>
          </div>
        )}

        {result && (
          <>
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: result.saved ? '1fr 1fr' : '1fr',
                gap: 14,
              }}
            >
              <ConfigResultCard label={t('cardDraftConfig')} accent summary={result.draft} />
              {result.saved && (
                <ConfigResultCard label={t('cardSavedConfig')} summary={result.saved} />
              )}
            </div>

            {/* W50 (決策 7 option d) — length-bias caveat: RAGAs faithfulness penalises
                long/comprehensive answers, so a low score paired with high completeness
                signals is likely the bias, not a worse config. */}
            <div
              className="hint"
              style={{ marginTop: 10, display: 'flex', gap: 6, alignItems: 'flex-start' }}
            >
              <AlertTriangle
                size={13}
                style={{ color: 'oklch(var(--warning))', marginTop: 1, flexShrink: 0 }}
              />
              <span>
                {t.rich('lengthBiasCaveat', {
                  bWarn: (c) => <b style={{ color: 'oklch(var(--warning))' }}>{c}</b>,
                  b: (c) => <b>{c}</b>,
                })}
              </span>
            </div>

            {result.draft.per_citation.length > 0 && (
              <div style={{ marginTop: 16 }}>
                <div className="muted text-xs" style={{ marginBottom: 6 }}>
                  {t('perCitationTitle')}
                </div>
                <div className="table-wrap">
                  <table className="table" style={{ fontSize: 12 }}>
                    <thead>
                      <tr>
                        <th>{t('colCitedChunk')}</th>
                        <th>{t('colSection')}</th>
                        <th className="col-num">{t('colImages')}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.draft.per_citation.map((c) => (
                        <tr key={c.chunk_id}>
                          <td className="mono">{c.chunk_id}</td>
                          <td>
                            <span className="section-path">
                              {c.section_path.map((s, j) => (
                                <span key={j}>{s}</span>
                              ))}
                            </span>
                          </td>
                          <td className="col-num mono">{c.image_count}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </>
        )}
      </div>
      <div className="card-footer">
        <div className="muted text-xs">{t('configTestFooter')}</div>
        <button
          type="button"
          className="btn btn-secondary btn-sm"
          onClick={onSaveDraft}
          disabled={!dirty || saving}
        >
          <Download size={13} /> {t('btnSaveDraftConfig')}
        </button>
      </div>
    </div>
  );
}

function ConfigResultCard({
  label,
  accent,
  summary,
}: {
  label: string;
  accent?: boolean;
  summary: ConfigRunSummary;
}) {
  const t = useTranslations('KbDetail');
  const last = summary.runs[summary.runs.length - 1];
  const fmt = (b: { mean: number }) =>
    Number.isInteger(b.mean) ? String(b.mean) : b.mean.toFixed(1);
  return (
    <div
      style={{
        border: accent ? '1px solid oklch(var(--accent) / 0.4)' : '1px solid oklch(var(--border))',
        borderRadius: 'var(--radius-sm)',
        background: accent ? 'oklch(var(--accent) / 0.04)' : 'transparent',
        overflow: 'hidden',
      }}
    >
      <div
        style={{
          padding: '10px 14px',
          borderBottom: '1px solid oklch(var(--border))',
          fontSize: 12,
          fontWeight: 600,
        }}
      >
        {label}
      </div>
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: 1,
          background: 'oklch(var(--border))',
        }}
      >
        {/* W48 質素軸 headline — reference-free RAGAs faithfulness (ADR-0040 雙軸)
            W49 (決策 7) — mean + ±band over N runs; N=1 → single-shot warning */}
        <div
          style={{
            gridColumn: '1 / -1',
            background: 'oklch(var(--card))',
            padding: '10px 14px',
          }}
        >
          <div className="muted text-xs" title={t('faithfulnessTooltip')}>
            {t('faithfulnessLabel')}
          </div>
          <div
            className="mono"
            style={{
              fontSize: 18,
              fontWeight: 700,
              marginTop: 2,
              color:
                summary.faithfulness != null
                  ? 'oklch(var(--success))'
                  : 'oklch(var(--muted-foreground))',
            }}
          >
            {summary.faithfulness != null ? summary.faithfulness.mean.toFixed(2) : '—'}
            {summary.faithfulness != null && summary.runs.length >= 2 && (
              <span className="muted text-xs" style={{ fontWeight: 400, marginLeft: 6 }}>
                ±{summary.faithfulness.band.toFixed(2)}
              </span>
            )}
            {summary.faithfulness == null && (
              <span className="muted text-xs" style={{ fontWeight: 400, marginLeft: 6 }}>
                {t('notEvaluated')}
              </span>
            )}
          </div>
          {summary.faithfulness != null && summary.runs.length === 1 && (
            <div className="text-xs" style={{ marginTop: 3, color: 'oklch(var(--warning))' }}>
              {t('singleJudgeRun')}
            </div>
          )}
        </div>
        <ConfigMetric
          k={t('metricCitations')}
          v={fmt(summary.citation_count)}
          band={summary.citation_count.band}
        />
        {/* W51 (決策 7 option d) — completeness/coverage proxy (breadth, NOT recall) */}
        <ConfigMetric
          k={t('metricSectionsCovered')}
          v={fmt(summary.distinct_sections)}
          sub={t('subSectionsCovered')}
          band={summary.distinct_sections.band}
        />
        <ConfigMetric
          k={t('metricImagesDedup')}
          v={fmt(summary.figure_count_dedup)}
          sub={t('subRaw', { n: fmt(summary.figure_count_raw) })}
          band={summary.figure_count_dedup.band}
        />
        {/* W65 — image-axis coverage proxy (mirror of 涵蓋章節數; wide text + narrow image = b-1 risk) */}
        <ConfigMetric
          k={t('metricImageSections')}
          v={fmt(summary.image_section_count)}
          sub={t('subImageSections')}
          band={summary.image_section_count.band}
        />
        <ConfigMetric
          k={t('metricLatencyP50')}
          v={`${(summary.latency_ms.mean / 1000).toFixed(1)}s`}
        />
        <ConfigMetric k={t('metricAnswerChars')} v={String(last?.answer_chars ?? 0)} />
        <ConfigMetric k={t('metricRefused')} v={last?.refused ? t('valueYes') : t('valueNo')} />
        <ConfigMetric
          k={t('metricStability')}
          v={t('stabilityValue', {
            a: summary.citation_count.band,
            b: summary.figure_count_dedup.band,
          })}
        />
      </div>
    </div>
  );
}

function ConfigMetric({ k, v, sub, band }: { k: string; v: string; sub?: string; band?: number }) {
  return (
    <div style={{ background: 'oklch(var(--card))', padding: '10px 14px' }}>
      <div className="muted text-xs">{k}</div>
      <div className="mono" style={{ fontSize: 16, fontWeight: 600, marginTop: 2 }}>
        {v}
        {band != null && (
          <span className="muted text-xs" style={{ fontWeight: 400, marginLeft: 4 }}>
            ±{band}
          </span>
        )}
      </div>
      {sub && (
        <div className="muted mono text-xs" style={{ marginTop: 1 }}>
          {sub}
        </div>
      )}
    </div>
  );
}

// ── Tab: Settings ───────────────────────────────────────────────────────────
function SettingsTab({ kb }: { kb: KbStatus }) {
  const t = useTranslations('KbDetail');
  const queryClient = useQueryClient();
  const [name, setName] = useState(kb.name);
  const [description, setDescription] = useState(kb.description);
  const [topK, setTopK] = useState(kb.config.default_top_k);
  const [rerankK, setRerankK] = useState(kb.config.default_rerank_k);
  // CH-006 — per-KB synthesis answer detail (query-time, no re-index). null/absent
  // saved config = inherit global "concise"; the seg surfaces the effective value.
  const [answerDetail, setAnswerDetail] = useState<'concise' | 'detailed'>(
    kb.config.answer_detail ?? 'concise',
  );
  // W46 (ADR-0042 + ADR-0043) — chunk_strategy + per-KB image cap are now editable.
  // Both are INGEST-time params, so a change only takes effect after a re-index
  // (Re-indexing card below). embedding_model stays locked (re-embed is heavier).
  const [chunkStrategy, setChunkStrategy] = useState<KbConfig['chunk_strategy']>(
    kb.config.chunk_strategy,
  );
  // '' = inherit the global cap (8); a positive int = this KB's per-chunk cap.
  const [maxImages, setMaxImages] = useState<string>(
    kb.config.chunker_max_images_per_chunk == null
      ? ''
      : String(kb.config.chunker_max_images_per_chunk),
  );
  const maxImagesValue: number | null = maxImages.trim() === '' ? null : Number(maxImages);
  // W43 F3.2 — the 12 per-KB tuning knobs (null = inherit global). Seeded from the
  // saved config; the UI only writes a boolean to enable_* keys and a number to the
  // rest, so the loose Record value type is correct per-key at runtime.
  const [knobs, setKnobs] = useState<KnobState>(() => {
    const init = {} as KnobState;
    for (const k of TUNE_KNOB_KEYS) init[k] = kb.config[k] ?? null;
    return init;
  });

  const setKnob = (key: TuneKnobKey, value: number | boolean | null) =>
    setKnobs((prev) => ({ ...prev, [key]: value }));
  const resetAllKnobs = () => {
    const cleared = {} as KnobState;
    for (const k of TUNE_KNOB_KEYS) cleared[k] = null;
    setKnobs(cleared);
  };

  // W69 — preset 套用 = 填草稿(rerank_k 喺 General 區獨立 state,跨兩區寫);
  // 已套用 = 三欄草稿現值全等於配方值 → 按鈕轉 disabled「已套用」。
  const presetApplied =
    rerankK === IMAGE_DENSE_PRESET.default_rerank_k &&
    knobs.citation_neighbour_max_aux_images ===
      IMAGE_DENSE_PRESET.citation_neighbour_max_aux_images &&
    knobs.max_images_per_answer === IMAGE_DENSE_PRESET.max_images_per_answer;
  const applyImageDensePreset = () => {
    setRerankK(IMAGE_DENSE_PRESET.default_rerank_k);
    setKnob(
      'citation_neighbour_max_aux_images',
      IMAGE_DENSE_PRESET.citation_neighbour_max_aux_images,
    );
    setKnob('max_images_per_answer', IMAGE_DENSE_PRESET.max_images_per_answer);
  };

  const knobsDirty = useMemo(
    () => TUNE_KNOB_KEYS.some((k) => (knobs[k] ?? null) !== (kb.config[k] ?? null)),
    [knobs, kb],
  );

  // Everything that round-trips through PATCH /settings (KbConfig). Separated from
  // the metadata diff because name/description go via patchMetadata.
  const configDirty = useMemo(
    () =>
      topK !== kb.config.default_top_k ||
      rerankK !== kb.config.default_rerank_k ||
      chunkStrategy !== kb.config.chunk_strategy ||
      maxImagesValue !== (kb.config.chunker_max_images_per_chunk ?? null) ||
      answerDetail !== (kb.config.answer_detail ?? 'concise') ||
      knobsDirty,
    [topK, rerankK, chunkStrategy, maxImagesValue, answerDetail, knobsDirty, kb],
  );

  const dirty = useMemo(
    () => name !== kb.name || description !== kb.description || configDirty,
    [name, description, configDirty, kb],
  );

  // PATCH /kb/{id}/settings replaces the whole KbConfig (omitted fields reset to
  // defaults — see backend update_kb_settings), so we send the COMPLETE config:
  // saved values + the editable top_k/rerank_k + the 12 knobs (null = inherit). The
  // cast is safe because the UI writes the correct primitive per knob key.
  function buildConfigBody(): KbConfig {
    return {
      ...kb.config,
      chunk_strategy: chunkStrategy,
      chunker_max_images_per_chunk: maxImagesValue,
      default_top_k: topK,
      default_rerank_k: rerankK,
      answer_detail: answerDetail,
      ...(knobs as Partial<KbConfig>),
    };
  }

  const metaMutation = useMutation({
    mutationFn: () =>
      kbApi.patchMetadata(kb.kb_id, {
        name: name !== kb.name ? name : undefined,
        description: description !== kb.description ? description : undefined,
      }),
    onSuccess: (updated) => {
      queryClient.setQueryData(['kb', kb.kb_id], updated);
      toast.success(t('toastMetadataSaved'));
    },
    onError: (e) => toast.error(e instanceof Error ? e.message : t('toastSaveFailed')),
  });

  const configMutation = useMutation({
    mutationFn: () => kbApi.patchSettings(kb.kb_id, buildConfigBody()),
    // The settings endpoint returns a bare KbConfig (not KbStatus), so invalidate +
    // refetch the full KB rather than writing the response into the cache.
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['kb', kb.kb_id] });
      toast.success(t('toastConfigSaved'));
    },
    onError: (e) => toast.error(e instanceof Error ? e.message : t('toastSaveFailed')),
  });

  function handleSave(e: FormEvent) {
    e.preventDefault();
    if (name !== kb.name || description !== kb.description) {
      metaMutation.mutate();
    }
    if (configDirty) {
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
          <h3 className="card-title">{t('cardGeneral')}</h3>
          <span className="badge badge-success">
            <Edit size={10} /> {t('badgeEditable')}
          </span>
        </div>
        <div className="card-body">
          <div className="field">
            <label className="label">{t('labelName')}</label>
            <input className="input" value={name} onChange={(e) => setName(e.target.value)} />
            <div className="hint">PATCH /kb/{kb.kb_id} · KbMetadataPatch.name</div>
          </div>
          <div className="field">
            <label className="label">{t('labelDescription')}</label>
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
              {t.rich('generalKbIdHint', {
                kbId: kb.kb_id,
                b: (c) => <b style={{ color: 'oklch(var(--warning))' }}>{c}</b>,
                mono: (c) => <span className="mono">{c}</span>,
              })}
            </div>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <h3 className="card-title">{t('cardRetrievalConfig')}</h3>
          <span className="badge badge-warning">
            <Shield size={10} /> {t('badgeMixLockedEditable')}
          </span>
        </div>
        <div className="card-body">
          <div className="field">
            <label className="label">
              {t('labelEmbeddingModel')}{' '}
              <Shield
                size={11}
                style={{
                  verticalAlign: '-2px',
                  marginLeft: 4,
                  color: 'oklch(var(--warning))',
                }}
              />
            </label>
            <select className="select" defaultValue={kb.config.embedding_model} disabled>
              <option>{kb.config.embedding_model}</option>
            </select>
            <div className="hint">
              {t.rich('embeddingModelHint', {
                dim: kb.config.embedding_dimension,
                b: (c) => <b style={{ color: 'oklch(var(--warning))' }}>{c}</b>,
              })}
            </div>
          </div>
          <div className="field">
            <label className="label">
              {t('labelChunkStrategy')}{' '}
              <RefreshCw
                size={11}
                style={{
                  verticalAlign: '-2px',
                  marginLeft: 4,
                  color: 'oklch(var(--warning))',
                }}
              />
            </label>
            <div className="seg" style={{ width: '100%' }}>
              {(
                [
                  'heading_aware',
                  'layout_aware',
                  'slide_based',
                  'auto',
                ] as KbConfig['chunk_strategy'][]
              ).map((s) => (
                <button
                  type="button"
                  key={s}
                  className="seg-btn"
                  data-active={chunkStrategy === s}
                  onClick={() => setChunkStrategy(s)}
                  style={{ flex: 1, padding: '5px 6px', fontSize: 11.5 }}
                >
                  {s}
                </button>
              ))}
            </div>
            <div className="hint">
              {t.rich('chunkStrategyHint', {
                b: (c) => <b style={{ color: 'oklch(var(--warning))' }}>{c}</b>,
              })}
            </div>
          </div>
          <div className="field">
            <label className="label">
              {t('labelMaxImagesPerChunk')}{' '}
              <RefreshCw
                size={11}
                style={{
                  verticalAlign: '-2px',
                  marginLeft: 4,
                  color: 'oklch(var(--warning))',
                }}
              />
            </label>
            <input
              type="number"
              className="input mono"
              value={maxImages}
              min={1}
              placeholder={t('placeholderInheritGlobal8')}
              onChange={(e) => setMaxImages(e.target.value)}
            />
            <div className="hint">
              {t.rich('maxImagesHint', {
                b: (c) => <b style={{ color: 'oklch(var(--warning))' }}>{c}</b>,
              })}
            </div>
          </div>
          <div className="field">
            <label className="label">
              {t('labelDefaultTopK')}{' '}
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
            <div className="hint">{t('topKHint2')}</div>
          </div>
          <div className="field">
            <label className="label">
              {t('labelDefaultRerankK')}{' '}
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
          {/* CH-006 — per-KB synthesis answer detail (query-time, no re-index) */}
          <div className="field" style={{ marginBottom: 0 }}>
            <label className="label">
              {t('labelAnswerDetail')}{' '}
              <Edit
                size={10}
                style={{
                  verticalAlign: '-1px',
                  marginLeft: 4,
                  color: 'oklch(var(--success))',
                }}
              />
            </label>
            <div className="seg" style={{ width: '100%' }}>
              {(['concise', 'detailed'] as const).map((d) => (
                <button
                  type="button"
                  key={d}
                  className="seg-btn"
                  data-active={answerDetail === d}
                  onClick={() => setAnswerDetail(d)}
                  style={{ flex: 1, padding: '5px 6px', fontSize: 11.5 }}
                >
                  {d === 'concise' ? t('segConcise') : t('segDetailed')}
                </button>
              ))}
            </div>
            <div className="hint">
              {t.rich('answerDetailHint', { b: (c) => <b>{c}</b> })}
            </div>
          </div>
        </div>
      </div>

      {/* W43 F3.2 — Advanced retrieval tuning (12 per-KB runtime knobs, ADR-0040) */}
      <div className="card" style={{ gridColumn: '1 / -1' }}>
        <div className="card-header">
          <div>
            <h3 className="card-title">{t('advancedTuningTitle')}</h3>
            <div className="card-desc">
              {t.rich('advancedTuningDesc', { b: (c) => <b>{c}</b> })}
            </div>
          </div>
          <span className="badge badge-info" style={{ fontSize: 9.5 }}>
            <Edit size={10} /> {t('badgeRuntimeNoReindex')}
          </span>
        </div>
        <div className="card-body" style={{ display: 'grid', gap: 12 }}>
          {/* W69 — 實證配方 preset 一鍵套用(mockup ekp-page-kb.jsx tuning card preset row) */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              padding: '12px 14px',
              border: '1px solid oklch(var(--border))',
              borderRadius: 'var(--radius-sm)',
              background: 'oklch(var(--muted) / 0.3)',
            }}
          >
            <Zap size={15} style={{ color: 'oklch(var(--accent))', flexShrink: 0 }} />
            <div style={{ flex: 1 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
                <span style={{ fontSize: 13, fontWeight: 500 }}>{t('presetTitle')}</span>
                <span className="badge badge-success" style={{ fontSize: 9.5 }}>
                  {t('presetBadge')}
                </span>
              </div>
              <div className="muted text-xs" style={{ marginTop: 3, lineHeight: 1.5 }}>
                {t('presetDesc')}
              </div>
            </div>
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              style={{ whiteSpace: 'nowrap' }}
              onClick={applyImageDensePreset}
              disabled={presetApplied}
            >
              {presetApplied ? (
                <>
                  <Check size={13} /> {t('btnApplied')}
                </>
              ) : (
                t('btnApplyRecipe')
              )}
            </button>
          </div>

          {TUNE_GROUPS.map((g) => (
            <KbTuneGroup
              key={g.enableKey}
              icon={g.icon}
              title={t(g.titleKey)}
              desc={t(g.descKey)}
              enabled={knobs[g.enableKey] as boolean | null}
              onToggle={(v) => setKnob(g.enableKey, v)}
              onReset={() => setKnob(g.enableKey, null)}
            >
              {g.knobs.length > 0
                ? g.knobs.map((kn) => (
                    <KbTuneKnob
                      key={kn.key}
                      label={t(kn.labelKey)}
                      value={knobs[kn.key] as number | null}
                      onChange={(v) => setKnob(kn.key, v)}
                    />
                  ))
                : null}
            </KbTuneGroup>
          ))}
        </div>
        <div className="card-footer">
          <div className="muted text-xs">
            {t.rich('configScopeKb', { b: (c) => <b>{c}</b> })}
          </div>
          <div className="row">
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={resetAllKnobs}
              disabled={!TUNE_KNOB_KEYS.some((k) => knobs[k] !== null)}
            >
              <RefreshCw size={13} /> {t('btnResetAllGlobal')}
            </button>
            <button
              type="submit"
              className="btn btn-primary btn-sm"
              disabled={!dirty || metaMutation.isPending || configMutation.isPending}
            >
              {configMutation.isPending ? t('saving') : t('btnSaveToKb')}
            </button>
          </div>
        </div>
      </div>

      <ConfigTestPanel
        kbId={kb.kb_id}
        draftConfig={knobs as DraftRetrievalConfig}
        onSaveDraft={() => configMutation.mutate()}
        saving={configMutation.isPending}
        dirty={dirty}
      />

      <div className="card" style={{ gridColumn: '1 / -1' }}>
        <div className="card-footer">
          <div className="muted text-xs">
            {t('lastIndexedLabel')}{' '}
            <span className="mono">{formatRelative(kb.last_indexed_at, t)}</span>
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
                setChunkStrategy(kb.config.chunk_strategy);
                setMaxImages(
                  kb.config.chunker_max_images_per_chunk == null
                    ? ''
                    : String(kb.config.chunker_max_images_per_chunk),
                );
                const reset = {} as KnobState;
                for (const k of TUNE_KNOB_KEYS) reset[k] = kb.config[k] ?? null;
                setKnobs(reset);
              }}
              disabled={!dirty}
            >
              {t('cancel')}
            </button>
            <button
              type="submit"
              className="btn btn-primary btn-sm"
              disabled={!dirty || metaMutation.isPending || configMutation.isPending}
            >
              {metaMutation.isPending || configMutation.isPending ? t('saving') : t('btnSaveChanges')}
            </button>
          </div>
        </div>
      </div>

      <ReindexCard kb={kb} chunkStrategy={chunkStrategy} maxImages={maxImages} />

      <DangerZone kb={kb} />
    </form>
  );
}

// ── W46 — Re-indexing card + confirm modal (ADR-0043) ────────────────────────
// Triggers POST /kb/{id}/reindex: synchronous in-place per-doc delete+reingest
// from each doc's stored original source under the CURRENT config, so a saved
// chunk_strategy / image-cap change actually takes effect. 100% match to mockup
// `ekp-page-kb.jsx` TabKbSettings Re-indexing card + .modal-overlay confirm.
function ReindexCard({
  kb,
  chunkStrategy,
  maxImages,
}: {
  kb: KbStatus;
  chunkStrategy: KbConfig['chunk_strategy'];
  maxImages: string;
}) {
  const t = useTranslations('KbDetail');
  const queryClient = useQueryClient();
  const [showExplainer, setShowExplainer] = useState(false);
  const [showModal, setShowModal] = useState(false);

  const reindexMutation = useMutation({
    mutationFn: () => kbApi.reindex(kb.kb_id),
    onSuccess: (summary) => {
      void queryClient.invalidateQueries({ queryKey: ['kb', kb.kb_id] });
      setShowModal(false);
      const skipped = summary.skipped_no_source.length;
      const failed = summary.failed.length;
      toast.success(
        t('toastReindexed', {
          done: summary.documents_reindexed,
          total: summary.documents_total,
          chunks: summary.chunks_total.toLocaleString(),
        }) +
          (skipped ? t('toastReindexSkippedSuffix', { skipped }) : '') +
          (failed ? t('toastReindexFailedSuffix', { failed }) : ''),
      );
    },
    onError: (e) => toast.error(e instanceof Error ? e.message : t('toastReindexError')),
  });

  const summary = reindexMutation.data;

  return (
    <div className="card" style={{ gridColumn: '1 / -1' }}>
      <div className="card-header">
        <div>
          <h3 className="card-title">{t('reindexTitle')}</h3>
          <div className="card-desc">{t('reindexDesc')}</div>
        </div>
        <button
          type="button"
          className="btn btn-ghost btn-sm"
          onClick={() => setShowExplainer((v) => !v)}
        >
          {showExplainer ? t('btnHideDetails') : t('btnWhatIsThis')}{' '}
          <ChevronRight size={11} style={{ transform: showExplainer ? 'rotate(90deg)' : 'none' }} />
        </button>
      </div>
      {showExplainer && (
        <div style={{ padding: '0 18px 18px' }}>
          <div
            style={{
              padding: '14px 16px',
              background: 'oklch(var(--muted) / 0.4)',
              border: '1px solid oklch(var(--border))',
              borderRadius: 'var(--radius-sm)',
              fontSize: 13,
              lineHeight: 1.65,
            }}
          >
            <p style={{ marginTop: 0, marginBottom: 10 }}>
              <b>{t('explainerWhatHappens')}</b>
            </p>
            <ol style={{ paddingLeft: 22, marginBottom: 10, lineHeight: 1.8 }}>
              <li>{t('explainerStep1')}</li>
              <li>{t.rich('explainerStep2', { b: (c) => <b>{c}</b> })}</li>
              <li>
                {t.rich('explainerStep3', {
                  kbId: kb.kb_id,
                  mono: (c) => <span className="mono">{c}</span>,
                })}
              </li>
              <li>{t('explainerStep4')}</li>
            </ol>
            <p style={{ marginBottom: 8 }}>
              <b>{t('explainerWhenTitle')}</b>
              <span className="muted"> {t('explainerWhenList')}</span>
            </p>
            <p style={{ marginBottom: 0 }} className="muted text-xs">
              {t('explainerNote')}
            </p>
            <div
              style={{
                display: 'flex',
                gap: 14,
                marginTop: 14,
                fontSize: 12,
                color: 'oklch(var(--muted-foreground))',
                fontFamily: 'var(--font-mono)',
                padding: 10,
                background: 'oklch(var(--background))',
                borderRadius: 'var(--radius-sm)',
              }}
            >
              <div>
                <b style={{ color: 'oklch(var(--foreground))' }}>{kb.total_documents}</b>{' '}
                {t('statDocsToReparse')}
              </div>
              <div>
                <b style={{ color: 'oklch(var(--foreground))' }}>
                  {kb.total_chunks.toLocaleString()}
                </b>{' '}
                {t('statChunksToRebuild')}
              </div>
              <div>{t.rich('statInPlace', { b: (c) => <b style={{ color: 'oklch(var(--foreground))' }}>{c}</b> })}</div>
            </div>
          </div>
        </div>
      )}
      {summary && (
        <div style={{ padding: '0 18px 14px' }}>
          <div
            className={`banner ${summary.failed.length ? 'banner-warning' : 'banner-success'}`}
            style={{ marginBottom: 0 }}
          >
            {summary.failed.length ? (
              <AlertTriangle size={15} style={{ color: 'oklch(var(--warning))' }} />
            ) : (
              <Check size={15} style={{ color: 'oklch(var(--success))' }} />
            )}
            <div style={{ flex: 1 }}>
              <div style={{ fontWeight: 500 }}>
                {t('summaryReindexed', {
                  done: summary.documents_reindexed,
                  total: summary.documents_total,
                  chunks: summary.chunks_total.toLocaleString(),
                })}
              </div>
              <div className="muted mono text-xs">
                {t('summarySkippedFailed', {
                  skipped: summary.skipped_no_source.length,
                  failed: summary.failed.length,
                })}
              </div>
            </div>
          </div>
        </div>
      )}
      <div className="card-footer">
        <div className="muted text-xs">
          {t('lastReindexLabel')} <span className="mono">{formatRelative(kb.last_indexed_at, t)}</span>{' '}
          {t('currentVersionLabel')} <span className="mono">v1</span>
        </div>
        <div className="row">
          <button type="button" className="btn btn-secondary btn-sm" disabled>
            <Download size={13} /> {t('btnExportConfigYaml')}
          </button>
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={() => setShowModal(true)}
            disabled={kb.archived || reindexMutation.isPending}
          >
            <RefreshCw size={13} />{' '}
            {reindexMutation.isPending ? t('reindexing') : t('btnTriggerReindexNow')}
          </button>
        </div>
      </div>

      {showModal && (
        <div
          className="modal-overlay"
          onClick={(e) => {
            if (e.target === e.currentTarget) setShowModal(false);
          }}
        >
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2 className="modal-title">{t('modalReindexTitle')}</h2>
              <p className="modal-desc">{t('modalReindexDesc')}</p>
            </div>
            <div className="modal-body">
              <div className="banner banner-warning" style={{ marginBottom: 14 }}>
                <AlertTriangle size={15} style={{ color: 'oklch(var(--warning))' }} />
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 500 }}>{t('modalSaveFirstTitle')}</div>
                  <div className="muted text-xs">{t('modalSaveFirstDesc')}</div>
                </div>
              </div>
              <div
                style={{
                  display: 'flex',
                  gap: 14,
                  fontSize: 12.5,
                  color: 'oklch(var(--muted-foreground))',
                  fontFamily: 'var(--font-mono)',
                  padding: 12,
                  background: 'oklch(var(--muted) / 0.4)',
                  borderRadius: 'var(--radius-sm)',
                }}
              >
                <div>
                  <b style={{ color: 'oklch(var(--foreground))' }}>{kb.total_documents}</b>{' '}
                  {t('statDocs')}
                </div>
                <div>
                  <b style={{ color: 'oklch(var(--foreground))' }}>
                    {kb.total_chunks.toLocaleString()}
                  </b>{' '}
                  {t('statChunks')}
                </div>
                <div>
                  {t('statStrategy')}{' '}
                  <b style={{ color: 'oklch(var(--foreground))' }}>{chunkStrategy}</b>
                </div>
                <div>
                  {t('statMaxImg')}{' '}
                  <b style={{ color: 'oklch(var(--foreground))' }}>
                    {maxImages || t('fallback8Global')}
                  </b>
                </div>
              </div>
            </div>
            <div className="modal-footer">
              <button
                type="button"
                className="btn btn-ghost btn-sm"
                onClick={() => setShowModal(false)}
                disabled={reindexMutation.isPending}
              >
                {t('cancel')}
              </button>
              <button
                type="button"
                className="btn btn-primary btn-sm"
                onClick={() => reindexMutation.mutate()}
                disabled={reindexMutation.isPending}
              >
                <RefreshCw size={13} />{' '}
                {reindexMutation.isPending
                  ? t('reindexing')
                  : t('btnReindexNDocuments', { n: kb.total_documents })}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function DangerZone({ kb }: { kb: KbStatus }) {
  const t = useTranslations('KbDetail');
  const queryClient = useQueryClient();
  const router = useRouter();
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const archiveMutation = useMutation({
    mutationFn: () => kbApi.archive(kb.kb_id),
    onSuccess: (updated) => {
      queryClient.setQueryData(['kb', kb.kb_id], updated);
      void queryClient.invalidateQueries({ queryKey: ['kb'] });
      toast.success(t('toastKbArchived'));
      router.push('/kb');
    },
    onError: (e) => toast.error(e instanceof Error ? e.message : t('toastArchiveFailed')),
  });
  // W87 — hard-delete: drops Postgres record + Azure index (DELETE /kb/{id}).
  const deleteMutation = useMutation({
    mutationFn: () => kbApi.delete(kb.kb_id),
    onSuccess: () => {
      setShowDeleteModal(false);
      void queryClient.invalidateQueries({ queryKey: ['kb'] });
      toast.success(t('toastKbDeleted'));
      router.push('/kb');
    },
    onError: (e) => {
      // 502 = storage record gone but the Azure index drop failed (lingers).
      // Per kb.py the orphan index can be cleared via scripts/create_index.py.
      if (e instanceof ApiError && e.status === 502) {
        setShowDeleteModal(false);
        toast.error(t('toastDeletePartial'));
        return;
      }
      toast.error(e instanceof Error ? e.message : t('toastDeleteFailed'));
    },
  });

  return (
    <div
      className="card"
      style={{
        gridColumn: '1 / -1',
        borderColor: 'oklch(var(--destructive) / 0.3)',
      }}
    >
      <div className="card-header" style={{ background: 'oklch(var(--destructive) / 0.04)' }}>
        <div>
          <h3 className="card-title" style={{ color: 'oklch(var(--destructive))' }}>
            {t('dangerZoneTitle')}
          </h3>
          <div className="card-desc">{t('dangerZoneDesc')}</div>
        </div>
      </div>
      <div className="card-body" style={{ display: 'flex', gap: 8 }}>
        <button
          type="button"
          className="btn btn-secondary"
          onClick={() => archiveMutation.mutate()}
          disabled={kb.archived || archiveMutation.isPending}
        >
          <Archive size={14} />
          {kb.archived ? t('btnAlreadyArchived') : t('btnArchiveKb')}
        </button>
        <div className="spacer" />
        <button
          type="button"
          className="btn btn-destructive"
          onClick={() => setShowDeleteModal(true)}
          disabled={deleteMutation.isPending}
        >
          <Trash2 size={14} /> {t('btnDeleteKb')}
        </button>
      </div>

      {/* W87 — delete confirm modal (.modal-overlay + .modal per DESIGN_SYSTEM §4.5,
          復用同頁 re-index confirm modal pattern — 視覺零發明). */}
      {showDeleteModal && (
        <div
          className="modal-overlay"
          onClick={(e) => {
            if (e.target === e.currentTarget) setShowDeleteModal(false);
          }}
        >
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2 className="modal-title">{t('modalDeleteTitle')}</h2>
              <p className="modal-desc">
                {t.rich('modalDeleteDesc', {
                  kbId: kb.kb_id,
                  mono: (c) => <span style={{ fontFamily: 'var(--font-mono)' }}>{c}</span>,
                })}
              </p>
            </div>
            <div className="modal-body">
              <div className="banner banner-warning" style={{ marginBottom: 14 }}>
                <AlertTriangle size={15} style={{ color: 'oklch(var(--warning))' }} />
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 500 }}>{t('modalCannotUndo')}</div>
                  <div className="muted text-xs">{t('modalDeleteNote')}</div>
                </div>
              </div>
              <div
                style={{
                  display: 'flex',
                  gap: 14,
                  fontSize: 12.5,
                  color: 'oklch(var(--muted-foreground))',
                  fontFamily: 'var(--font-mono)',
                  padding: 12,
                  background: 'oklch(var(--muted) / 0.4)',
                  borderRadius: 'var(--radius-sm)',
                }}
              >
                <div>
                  <b style={{ color: 'oklch(var(--foreground))' }}>{kb.total_documents}</b>{' '}
                  {t('statDocs')}
                </div>
                <div>
                  <b style={{ color: 'oklch(var(--foreground))' }}>
                    {kb.total_chunks.toLocaleString()}
                  </b>{' '}
                  {t('statChunks')}
                </div>
              </div>
            </div>
            <div className="modal-footer">
              <button
                type="button"
                className="btn btn-ghost btn-sm"
                onClick={() => setShowDeleteModal(false)}
                disabled={deleteMutation.isPending}
              >
                {t('cancel')}
              </button>
              <button
                type="button"
                className="btn btn-destructive btn-sm"
                onClick={() => deleteMutation.mutate()}
                disabled={deleteMutation.isPending}
              >
                <Trash2 size={13} />{' '}
                {deleteMutation.isPending ? t('deleting') : t('btnDeletePermanently')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
