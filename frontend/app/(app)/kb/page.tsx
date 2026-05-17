'use client';

/**
 * V3 KB List (`/kb`) — W22 F5 direct-copy from mockup
 * `references/design-mockups/ekp-page-kb.jsx:5-137` PageKbList + KbCard +
 * KbTable (per CLAUDE.md §5.7 H7 strict fidelity 2026-05-18).
 *
 * Mockup layout:
 *   - `.page-header` greeting + subtitle (ADR-0018 namespace note) + view toggle
 *     `<seg>` + Export btn + New KB btn
 *   - Filter bar — search wrap + status/tag chips + right-aligned count meta
 *   - `.kb-grid` cards OR `<KbTable>` based on view state
 *
 * Preserved from W20 F4.3 (per W22 plan §0):
 *   - `useQuery(kbApi.list)` for data
 *   - `localStorage['ekp-kb-list-view']` for grid/table preference
 *   - Status filter (indexed / empty / degraded / all) + search + sort
 *
 * Real KbStatus schema lacks mockup fields (status / indexing_progress /
 * recall_at_5 / tags / owner) → graceful defaults: derive `status` from
 * data shape (archived / empty / has-docs) ;recall@5 / tags / owner shown
 * as "—" placeholders until backend ships those fields.
 */

import {
  Database,
  Download,
  FileText,
  Filter,
  Layers,
  Plus,
  Search,
  Tag,
  Zap,
} from 'lucide-react';
import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';

import { kbApi, type KbStatus } from '@/lib/api/kb';

type SortKind = 'name' | 'last_indexed' | 'documents';
type StatusKind = 'indexed' | 'empty' | 'archived';
type StatusFilter = StatusKind | 'all';
type ViewKind = 'grid' | 'table';

const SORT_LABEL: Record<SortKind, string> = {
  name: 'Name (A→Z)',
  last_indexed: 'Last indexed (recent)',
  documents: 'Documents (most)',
};

const STATUS_FILTER_LABEL: Record<StatusFilter, string> = {
  all: 'Status: All',
  indexed: 'Status: Indexed',
  empty: 'Status: Empty',
  archived: 'Status: Archived',
};

const VIEW_KEY = 'ekp-kb-list-view';

function deriveStatus(kb: KbStatus): StatusKind {
  if (kb.archived) return 'archived';
  if (kb.total_documents === 0) return 'empty';
  return 'indexed';
}

function formatRelative(iso: string | null | undefined): string {
  if (!iso) return '—';
  const ts = new Date(iso).getTime();
  if (Number.isNaN(ts)) return '—';
  const mins = Math.floor((Date.now() - ts) / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  if (mins < 60 * 24) return `${Math.floor(mins / 60)}h ago`;
  return `${Math.floor(mins / 60 / 24)}d ago`;
}

function makeComparator(sort: SortKind): (a: KbStatus, b: KbStatus) => number {
  if (sort === 'name') {
    return (a, b) => (a.name || a.kb_id).localeCompare(b.name || b.kb_id);
  }
  if (sort === 'documents') {
    return (a, b) => (b.total_documents ?? 0) - (a.total_documents ?? 0);
  }
  return (a, b) => {
    const av = a.last_indexed_at ?? '';
    const bv = b.last_indexed_at ?? '';
    return bv.localeCompare(av);
  };
}

export default function KbListPage() {
  const query = useQuery<KbStatus[]>({
    queryKey: ['kb', 'list'],
    queryFn: kbApi.list,
  });

  const [search, setSearch] = useState('');
  const [sort, setSort] = useState<SortKind>('last_indexed');
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');
  const [view, setView] = useState<ViewKind>('grid');

  useEffect(() => {
    const stored = window.localStorage.getItem(VIEW_KEY);
    if (stored === 'grid' || stored === 'table') setView(stored);
  }, []);

  function pickView(next: ViewKind) {
    setView(next);
    window.localStorage.setItem(VIEW_KEY, next);
  }

  const visible = useMemo(() => {
    const rows = query.data ?? [];
    const term = search.trim().toLowerCase();
    const filteredBySearch = term
      ? rows.filter((kb) =>
          [kb.name, kb.kb_id, kb.description]
            .filter(Boolean)
            .some((field) => field.toLowerCase().includes(term)),
        )
      : rows;
    const filteredByStatus =
      statusFilter === 'all'
        ? filteredBySearch
        : filteredBySearch.filter((kb) => deriveStatus(kb) === statusFilter);
    return [...filteredByStatus].sort(makeComparator(sort));
  }, [query.data, search, sort, statusFilter]);

  const totalDocs = (query.data ?? []).reduce(
    (s, k) => s + k.total_documents,
    0,
  );

  return (
    <div className="content">
      <div className="content-wide">
        {/* Page header — mockup lines 12-31 */}
        <div className="page-header">
          <div>
            <h1 className="page-title">Knowledge bases</h1>
            <p className="page-subtitle">
              Each KB is provisioned with its own Azure AI Search index (
              <span className="mono">ekp-kb-&lt;kb_id&gt;-v1</span>, 1024d HNSW)
              per ADR-0018.
            </p>
          </div>
          <div className="page-actions">
            <div className="seg">
              <button
                type="button"
                className="seg-btn"
                data-active={view === 'grid'}
                onClick={() => pickView('grid')}
              >
                <Layers size={13} /> Grid
              </button>
              <button
                type="button"
                className="seg-btn"
                data-active={view === 'table'}
                onClick={() => pickView('table')}
              >
                <Filter size={13} /> Table
              </button>
            </div>
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              disabled
              title="Export — Tier 2 (post-Beta)"
              style={{ opacity: 0.5, cursor: 'default' }}
            >
              <Download size={13} /> Export
            </button>
            <Link href="/kb/new" className="btn btn-primary btn-sm">
              <Plus size={13} /> New KB
            </Link>
          </div>
        </div>

        {/* Filter bar — mockup lines 34-43 */}
        <div
          style={{
            display: 'flex',
            gap: 8,
            marginBottom: 16,
            alignItems: 'center',
          }}
        >
          <div className="input-search-wrap" style={{ flex: 1, maxWidth: 320 }}>
            <span className="icon-leading">
              <Search size={14} />
            </span>
            <input
              className="input"
              placeholder="Filter by name, id, description…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>

          {/* Status filter — cycle through options on click (replaces shadcn Select) */}
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={() => {
              const order: StatusFilter[] = ['all', 'indexed', 'empty', 'archived'];
              const idx = order.indexOf(statusFilter);
              setStatusFilter(order[(idx + 1) % order.length]!);
            }}
            title="Click to cycle status filter"
          >
            <Filter size={13} /> {STATUS_FILTER_LABEL[statusFilter]}
          </button>

          {/* Sort cycle */}
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={() => {
              const order: SortKind[] = ['last_indexed', 'name', 'documents'];
              const idx = order.indexOf(sort);
              setSort(order[(idx + 1) % order.length]!);
            }}
            title="Click to cycle sort"
          >
            <Tag size={13} /> {SORT_LABEL[sort]}
          </button>

          <div className="spacer" style={{ flex: 1 }} />
          <div className="text-xs muted mono">
            {visible.length} of {(query.data ?? []).length} KBs · {totalDocs} docs total
          </div>
        </div>

        {/* Body — grid or table */}
        {query.isLoading ? (
          <div
            className="text-xs muted"
            style={{ padding: '48px 18px', textAlign: 'center' }}
          >
            Loading knowledge bases…
          </div>
        ) : visible.length === 0 ? (
          <KbEmpty
            hasFilter={
              search.trim().length > 0 || statusFilter !== 'all'
            }
          />
        ) : view === 'grid' ? (
          <div className="kb-grid">
            {visible.map((kb) => (
              <KbCard key={kb.kb_id} kb={kb} />
            ))}
          </div>
        ) : (
          <KbTable rows={visible} />
        )}
      </div>
    </div>
  );
}

// ──────────────────────────────────────────────────────────────────────────
// KbCard — mockup lines 57-86
// ──────────────────────────────────────────────────────────────────────────

function KbCard({ kb }: { kb: KbStatus }) {
  const status = deriveStatus(kb);
  return (
    <Link
      href={`/kb/${kb.kb_id}`}
      className="kb-card"
      style={{ textDecoration: 'none', color: 'inherit', display: 'flex', flexDirection: 'column' }}
    >
      <div className="kb-card-head">
        <div className="kb-icon">
          <Database size={18} />
        </div>
        {status === 'archived' ? (
          <span className="badge badge-muted">
            <span className="badge-dot" /> ARCHIVED
          </span>
        ) : status === 'empty' ? (
          <span className="badge badge-info">
            <span className="badge-dot" /> EMPTY
          </span>
        ) : (
          <span className="badge badge-success">
            <span className="badge-dot" /> READY
          </span>
        )}
      </div>
      <div>
        <div className="kb-title">{kb.name || kb.kb_id}</div>
        <div className="kb-desc">{kb.description || '—'}</div>
      </div>
      <div className="kb-meta">
        <span>
          <FileText size={11} /> {kb.total_documents}
        </span>
        <span>
          <Layers size={11} /> {kb.total_chunks.toLocaleString()}
        </span>
        <span>
          <Zap size={11} /> {kb.storage_size_mb.toFixed(1)} MB
        </span>
        <span style={{ marginLeft: 'auto' }}>
          {formatRelative(kb.last_indexed_at)}
        </span>
      </div>
    </Link>
  );
}

// ──────────────────────────────────────────────────────────────────────────
// KbTable — mockup lines 88-137
// ──────────────────────────────────────────────────────────────────────────

function KbTable({ rows }: { rows: KbStatus[] }) {
  return (
    <div className="table-wrap">
      <table className="table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Status</th>
            <th className="col-num">Docs</th>
            <th className="col-num">Chunks</th>
            <th className="col-num">Screenshots</th>
            <th className="col-num">Storage</th>
            <th className="col-num">Last indexed</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((kb) => {
            const status = deriveStatus(kb);
            return (
              <tr key={kb.kb_id}>
                <td>
                  <Link
                    href={`/kb/${kb.kb_id}`}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 10,
                      textDecoration: 'none',
                      color: 'inherit',
                    }}
                  >
                    <div className="kb-icon" style={{ width: 26, height: 26 }}>
                      <Database size={13} />
                    </div>
                    <div>
                      <div className="table-row-link">{kb.name || kb.kb_id}</div>
                      <div className="text-xs muted mono">
                        ekp-kb-{kb.kb_id}-v1
                      </div>
                    </div>
                  </Link>
                </td>
                <td>
                  {status === 'archived' ? (
                    <span className="badge badge-muted">
                      <span className="badge-dot" /> ARCHIVED
                    </span>
                  ) : status === 'empty' ? (
                    <span className="badge badge-info">
                      <span className="badge-dot" /> EMPTY
                    </span>
                  ) : (
                    <span className="badge badge-success">
                      <span className="badge-dot" /> READY
                    </span>
                  )}
                </td>
                <td className="col-num">{kb.total_documents}</td>
                <td className="col-num">{kb.total_chunks.toLocaleString()}</td>
                <td className="col-num">{kb.total_screenshots}</td>
                <td className="col-num">{kb.storage_size_mb.toFixed(1)} MB</td>
                <td className="col-num text-xs">
                  {formatRelative(kb.last_indexed_at)}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function KbEmpty({ hasFilter }: { hasFilter: boolean }) {
  return (
    <div
      style={{
        padding: '48px 24px',
        textAlign: 'center',
        border: '1px dashed oklch(var(--border))',
        borderRadius: 'var(--radius-md)',
        background: 'oklch(var(--muted) / 0.2)',
      }}
    >
      <div
        style={{
          width: 56,
          height: 56,
          borderRadius: '50%',
          background: 'oklch(var(--muted))',
          color: 'oklch(var(--muted-foreground))',
          display: 'grid',
          placeItems: 'center',
          margin: '0 auto 16px',
        }}
      >
        <Database size={22} />
      </div>
      <div
        style={{
          fontSize: 15,
          fontWeight: 600,
          marginBottom: 6,
          color: 'oklch(var(--foreground))',
        }}
      >
        {hasFilter ? 'No knowledge bases match' : 'No knowledge bases yet'}
      </div>
      <div className="text-xs muted" style={{ marginBottom: 16 }}>
        {hasFilter
          ? 'Adjust your search / status filter.'
          : 'Create your first KB to start ingesting documents.'}
      </div>
      {!hasFilter && (
        <Link href="/kb/new" className="btn btn-primary btn-sm">
          <Plus size={13} /> Create knowledge base
        </Link>
      )}
    </div>
  );
}
