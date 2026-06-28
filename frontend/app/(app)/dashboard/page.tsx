'use client';

/**
 * Dashboard (`/dashboard`) — W22 F3 direct-copy from mockup
 * `references/design-mockups/ekp-page-dashboard.jsx` PageDashboard
 * (per CLAUDE.md §5.7 H7 strict fidelity 2026-05-18).
 *
 * Visual structure mirrors mockup:
 *   - `.page-header` greeting + status pill + 2 action buttons
 *   - `.stat-grid` 4 stats (KBs / Documents / Recall@5 / Today's spend)
 *   - Main grid (1.4fr 1fr) — 5 cards across 2 columns:
 *       Left:  KB summary table + Recent queries
 *       Right: Latest eval + System health + Quick actions
 *
 * Preserved data integration (per CLAUDE.md §4 authority + W22 plan §0):
 *   - `useQuery(kbApi.list)` for KB summary + 4-stat strip aggregation
 *   - `useQuery(/health)` for per-component System health card
 *   - Defensive `?.components?.[key]` read (W22 F1-pivot — accommodates
 *     thin `{status:"ok"}` payload when backend hasn't been upgraded yet)
 *
 * Empty-state CTAs (no backend yet — preserves W18 F4 + W20 F2 pattern):
 *   - Recall@5 stat            — Q6 Open / no per-KB eval cache
 *   - Today's spend stat       — no cost-summary endpoint
 *   - Recent queries card      — Q6 Open
 *   - Latest eval card         — no cached-eval-run endpoint
 *
 * All Tailwind utility classes / shadcn primitives replaced by mockup CSS
 * classes (`.card .card-header .card-title .card-desc .card-body
 * .card-body-tight .card-footer .stat-grid .stat .stat-label .stat-value
 * .stat-meta .stat-unit .status-dot .trend-up .table .col-num .badge-* .kb-icon
 * .activity .activity-icon .activity-body .activity-time .table-row-link`).
 *
 * Renders inside <AppShell> (sidebar shows "Dashboard" active). Outer wrap
 * `.content + .content-wide` per mockup line 16-17 (page-level self-wrap;
 * AppShell layout-agnostic per W22 F1 H7 pivot).
 */

import {
  Activity,
  ChevronRight,
  Database,
  FileText,
  Key,
  MessageCircle,
  Plus,
  Search,
  Upload,
  Zap,
  type LucideIcon,
} from 'lucide-react';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';

import { apiClient } from '@/lib/api-client';
import { kbApi, type KbStatus } from '@/lib/api/kb';
import { useCurrentUser } from '@/lib/providers/auth-provider';

// ---------------------------------------------------------------------------
// Types — mirror backend/api/routes/health.py HealthResponse (W20 F2.1)
// ---------------------------------------------------------------------------

type ComponentStatus = 'ok' | 'not_configured' | 'degraded' | 'error';

interface ComponentHealth {
  status: ComponentStatus;
  latency_ms: number | null;
  detail: string | null;
}

interface HealthResponse {
  status: 'ok' | 'degraded';
  components: Record<string, ComponentHealth>;
}

const COMPONENT_LABELS: Record<string, string> = {
  azure_search: 'Azure AI Search',
  azure_openai: 'Azure OpenAI',
  cohere: 'Cohere Reranker',
  langfuse: 'Langfuse',
  postgres: 'Postgres',
};

const COMPONENT_ORDER = [
  'azure_search',
  'azure_openai',
  'cohere',
  'langfuse',
  'postgres',
] as const;

function statusDotClass(status: ComponentStatus): string {
  switch (status) {
    case 'ok':
      return 'ready';
    case 'not_configured':
      return 'queued';
    case 'degraded':
      return 'indexing';
    case 'error':
      return 'failed';
  }
}

function statusBadgeClass(status: ComponentStatus): string {
  switch (status) {
    case 'ok':
      return 'badge-success';
    case 'not_configured':
      return 'badge-muted';
    case 'degraded':
      return 'badge-info';
    case 'error':
      return 'badge';
  }
}

function statusLabel(status: ComponentStatus): string {
  switch (status) {
    case 'ok':
      return 'OK';
    case 'not_configured':
      return 'NOT SET';
    case 'degraded':
      return 'DEGRADED';
    case 'error':
      return 'ERROR';
  }
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function DashboardPage() {
  const user = useCurrentUser();
  const displayName = user?.preferredUsername.split('@')[0] ?? 'there';

  const kbQuery = useQuery({
    queryKey: ['kb', 'list'],
    queryFn: () => kbApi.list(),
  });
  const healthQuery = useQuery({
    queryKey: ['health'],
    queryFn: () => apiClient.get<HealthResponse>('/health'),
    retry: 1,
    refetchInterval: 60_000,
  });

  const kbs = kbQuery.data ?? [];
  // CH-017 — the stat strip describes the ACTIVE knowledge bases. Mockup
  // `MOCK_KBS` had no `archived` concept, so mockup `{kbs.length} active` worked
  // (length == active count); the real `KbStatus` carries an `archived`
  // soft-delete flag, so we filter to keep the strip's "N active" + Documents /
  // chunks consistent with the sidebar badge (CH-016). The KB summary TABLE
  // below still lists ALL kbs (archived ones flagged) — table = full inventory,
  // strip = active overview.
  const activeKbs = kbs.filter((k) => !k.archived);
  const totalDocs = activeKbs.reduce((s, k) => s + k.total_documents, 0);
  const totalChunks = activeKbs.reduce((s, k) => s + k.total_chunks, 0);
  const totalStorageMb = activeKbs.reduce((s, k) => s + k.storage_size_mb, 0);
  // Mockup line 13:`kbs.filter(k => k.status === "indexing")`。Backend `KbStatus`
  // 暫未 expose `status === indexing` field(W22 B-i policy:default "All ready"
  // until backend ships indexing state)。`archived` flag 唔等於 indexing,
  // 故唔做 W20 substitution。
  const indexingKbCount = 0;

  // /health overall — drives the page-header status pill.
  const healthOk = healthQuery.data?.status === 'ok';
  const healthLabel = healthQuery.isPending
    ? 'Checking system health…'
    : healthQuery.isError
      ? 'Backend unreachable'
      : healthOk
        ? 'System healthy'
        : 'System degraded';
  const healthDotClass = healthQuery.isPending
    ? 'queued'
    : healthQuery.isError || !healthOk
      ? 'failed'
      : 'ready';

  return (
    <div className="content">
      <div className="content-wide">
        {/* Page header — mockup lines 18-33 */}
        <div className="page-header">
          <div>
            <h1 className="page-title">Welcome back, {displayName}</h1>
            <p className="page-subtitle">
              <span className={`status-dot ${healthDotClass}`} /> EKP Beta ·{' '}
              <span className="mono">ekp-beta.ricoh.com</span> · {healthLabel} ·
              {' '}Last eval pass <b>—</b>
            </p>
          </div>
          <div className="page-actions">
            <Link href="/eval" className="btn btn-secondary btn-sm">
              <Activity size={14} /> View latest eval
            </Link>
            <Link href="/chat" className="btn btn-primary btn-sm">
              <MessageCircle size={14} /> Ask the knowledge base
            </Link>
          </div>
        </div>

        {/* Stat strip — mockup lines 36-66 */}
        <div className="stat-grid">
          <div className="stat">
            <div className="stat-label">
              <Database size={13} /> Knowledge bases
            </div>
            <div className="stat-value">
              {activeKbs.length}
              <span className="stat-unit"> active</span>
            </div>
            <div className="stat-meta">
              {indexingKbCount > 0 ? (
                <>
                  <span className="status-dot indexing" /> {indexingKbCount} indexing
                </>
              ) : (
                <>
                  <span className="status-dot ready" /> All ready
                </>
              )}
            </div>
          </div>
          <div className="stat">
            <div className="stat-label">
              <FileText size={13} /> Documents
            </div>
            <div className="stat-value">{totalDocs.toLocaleString()}</div>
            <div className="stat-meta">
              <span>
                {totalChunks.toLocaleString()} chunks · {totalStorageMb.toFixed(0)} MB
              </span>
            </div>
          </div>
          <div className="stat">
            <div className="stat-label">
              <Zap size={13} /> Recall @ 5
            </div>
            <div className="stat-value">
              —<span className="stat-unit">%</span>
            </div>
            <div className="stat-meta muted">No cached eval · run from /eval</div>
          </div>
          <div className="stat">
            <div className="stat-label">
              <Activity size={13} /> Today&apos;s spend
            </div>
            <div className="stat-value">—</div>
            <div className="stat-meta muted">Cost tracking is not enabled yet</div>
          </div>
        </div>

        {/* Main grid — mockup lines 69-82 */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: '1.4fr 1fr',
            gap: 16,
            marginTop: 16,
          }}
        >
          {/* Left column */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <KbSummaryCard kbs={kbs} loading={kbQuery.isPending} />
            <RecentQueriesCard />
          </div>

          {/* Right column */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <LatestEvalCard />
            <SystemHealthCard healthQuery={healthQuery} />
            <QuickActionsCard />
          </div>
        </div>
      </div>
    </div>
  );
}

// ──────────────────────────────────────────────────────────────────────────
// KB summary — mockup KbSummaryCard lines 88-146
// ──────────────────────────────────────────────────────────────────────────

function KbSummaryCard({
  kbs,
  loading,
}: {
  kbs: KbStatus[];
  loading: boolean;
}) {
  return (
    <div className="card">
      <div className="card-header">
        <div>
          <h3 className="card-title">Knowledge bases</h3>
          <div className="card-desc">
            Per-KB index <span className="mono">ekp-kb-{'{kb_id}'}-v1</span> · ADR-0018 namespace
          </div>
        </div>
        <Link href="/kb" className="btn btn-secondary btn-sm">
          View all <ChevronRight size={13} />
        </Link>
      </div>
      <div className="card-body card-body-tight">
        {loading ? (
          <div className="text-xs muted" style={{ padding: '24px 18px', textAlign: 'center' }}>
            Loading knowledge bases…
          </div>
        ) : kbs.length === 0 ? (
          <div className="text-xs muted" style={{ padding: '24px 18px', textAlign: 'center' }}>
            No knowledge bases yet ·{' '}
            <Link href="/kb/new" style={{ color: 'oklch(var(--accent))', fontWeight: 500 }}>
              Create your first →
            </Link>
          </div>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Status</th>
                <th className="col-num">Docs</th>
                <th className="col-num">Chunks</th>
                <th className="col-num">R@5</th>
                <th className="col-num">Last indexed</th>
              </tr>
            </thead>
            <tbody>
              {kbs.map((kb) => (
                <KbRow key={kb.kb_id} kb={kb} />
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

function KbRow({ kb }: { kb: KbStatus }) {
  return (
    <tr>
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
            <div className="text-xs muted mono">ekp-kb-{kb.kb_id}-v1</div>
          </div>
        </Link>
      </td>
      <td>
        {kb.archived ? (
          <span className="badge badge-muted">
            <span className="badge-dot" /> ARCHIVED
          </span>
        ) : (
          <span className="badge badge-success">
            <span className="badge-dot" /> READY
          </span>
        )}
      </td>
      <td className="col-num">{kb.total_documents}</td>
      <td className="col-num">{kb.total_chunks.toLocaleString()}</td>
      {/* R@5 — W22 B-i placeholder until backend `recall_at_5` per-KB field */}
      <td className="col-num">—%</td>
      <td className="col-num text-xs">{formatRelative(kb.last_indexed_at)}</td>
    </tr>
  );
}

// ──────────────────────────────────────────────────────────────────────────
// Recent queries — mockup RecentQueriesCard lines 148-184 (empty-state for Q6)
// ──────────────────────────────────────────────────────────────────────────

function RecentQueriesCard() {
  // W22 B-i:mockup lines 148-184 renders `recent.map(activity)` activity rows;
  // backend query log NOT collected yet(Q6 Open)→ recent=[] → card-body
  // visually empty,matches mockup behavior when MOCK_RECENT_QUERIES=[]。
  // Single muted-text placeholder preserves the card-body slot per mockup
  // `.card-body.card-body-tight` padding without inventing a CTA mockup lacks。
  return (
    <div className="card">
      <div className="card-header">
        <div>
          <h3 className="card-title">Recent queries</h3>
          <div className="card-desc">
            Last 24h · CRAG-triggered queries marked with{' '}
            <span className="badge badge-accent" style={{ marginLeft: 2 }}>
              <span className="badge-dot" /> CRAG
            </span>
          </div>
        </div>
        <Link href="/traces" className="btn btn-ghost btn-sm">
          All traces <ChevronRight size={13} />
        </Link>
      </div>
      <div className="card-body card-body-tight">
        <div
          className="text-xs muted"
          style={{ padding: '32px 18px', textAlign: 'center' }}
        >
          No queries recorded yet — query logging is not enabled.
        </div>
      </div>
    </div>
  );
}

// ──────────────────────────────────────────────────────────────────────────
// Latest eval — mockup LatestEvalCard lines 186-223 (empty-state for cached-run)
// ──────────────────────────────────────────────────────────────────────────

function LatestEvalCard() {
  // W22 B-i:mockup lines 186-223 renders 2×2 metric grid + Shootout footer
  // button。Backend no cached-eval-run endpoint yet → 4 placeholder metric
  // boxes with "—%" preserve grid structure;delta-arrow omitted(no baseline
  // to compare against until 2 eval runs land)。
  const metrics = [
    { label: 'Recall@5' },
    { label: 'Faithfulness' },
    { label: 'Ans Relevancy' },
    { label: 'Ctx Precision' },
  ];
  return (
    <div className="card">
      <div className="card-header">
        <div>
          <h3 className="card-title">Latest eval</h3>
          <div className="card-desc">
            RAGAs · <span className="mono">eval-set-v1-draft</span> · — q
          </div>
        </div>
        <Link href="/eval" className="btn btn-ghost btn-icon btn-sm" aria-label="Open eval">
          <ChevronRight size={13} />
        </Link>
      </div>
      <div
        className="card-body"
        style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}
      >
        {metrics.map((m) => (
          <div
            key={m.label}
            style={{
              padding: '10px 12px',
              border: '1px solid oklch(var(--border))',
              borderRadius: 'var(--radius-sm)',
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
              —<span className="stat-unit" style={{ fontSize: 11 }}>%</span>
            </div>
            <div className="text-xs mono muted" style={{ marginTop: 2 }}>
              no baseline
            </div>
          </div>
        ))}
      </div>
      <div className="card-footer">
        <div className="text-xs muted mono">
          Reranker locked ·{' '}
          <b style={{ color: 'oklch(var(--foreground))' }}>cohere-v4.0-pro</b> · ADR-0012
        </div>
        <Link href="/eval" className="btn btn-ghost btn-xs">
          Shootout →
        </Link>
      </div>
    </div>
  );
}

// ──────────────────────────────────────────────────────────────────────────
// System health — mockup SystemHealthCard lines 225-254 (real /health data)
// ──────────────────────────────────────────────────────────────────────────

function SystemHealthCard({
  healthQuery,
}: {
  healthQuery: ReturnType<typeof useQuery<HealthResponse>>;
}) {
  const data = healthQuery.data;
  const components = data?.components;
  const overallOk = data?.status === 'ok';

  return (
    <div className="card">
      <div className="card-header">
        <div>
          <h3 className="card-title">System health</h3>
          <div className="card-desc">Live · per-component connectivity</div>
        </div>
        {healthQuery.isPending ? (
          <span className="badge badge-muted">
            <span className="badge-dot" /> CHECKING
          </span>
        ) : healthQuery.isError ? (
          <span className="badge">
            <span className="badge-dot" /> UNREACHABLE
          </span>
        ) : overallOk ? (
          <span className="badge badge-success">
            <span className="badge-dot" /> ALL OK
          </span>
        ) : (
          <span className="badge badge-info">
            <span className="badge-dot" /> DEGRADED
          </span>
        )}
      </div>
      <div className="card-body card-body-tight">
        {!components ? (
          <div className="text-xs muted" style={{ padding: '18px', textAlign: 'center' }}>
            {healthQuery.isPending
              ? 'Checking…'
              : healthQuery.isError
                ? 'Backend unreachable.'
                : '/health returned thin payload (pre-W20 build).'}
          </div>
        ) : (
          COMPONENT_ORDER.map((key) => {
            const comp = components[key];
            if (!comp) return null;
            const label = COMPONENT_LABELS[key] ?? key;
            return (
              <div
                key={key}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 12,
                  padding: '10px 18px',
                  borderBottom: '1px solid oklch(var(--border))',
                }}
                title={comp.detail ?? undefined}
              >
                <span className={`status-dot ${statusDotClass(comp.status)}`} />
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: 13, fontWeight: 500 }}>{label}</div>
                  {comp.detail && (
                    <div className="text-xs muted mono">{comp.detail}</div>
                  )}
                </div>
                {comp.latency_ms !== null && (
                  <div
                    className="mono"
                    style={{
                      fontSize: 12,
                      fontVariantNumeric: 'tabular-nums',
                      color: 'oklch(var(--muted-foreground))',
                    }}
                  >
                    {comp.latency_ms}ms
                  </div>
                )}
                <span className={`badge ${statusBadgeClass(comp.status)}`}>
                  {statusLabel(comp.status)}
                </span>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}

// ──────────────────────────────────────────────────────────────────────────
// Quick actions — mockup QuickActionsCard lines 256-286
// ──────────────────────────────────────────────────────────────────────────

function QuickActionsCard() {
  const actions: Array<{
    icon: LucideIcon;
    label: string;
    hint: string;
    href?: string;
    disabled?: boolean;
    disabledReason?: string;
  }> = [
    {
      icon: Upload,
      label: 'Upload documents',
      hint: '3-step pipeline wizard',
      href: '/kb',
    },
    {
      icon: Search,
      label: 'Retrieval testing',
      hint: 'Compare BM25 / Vector / Hybrid',
      href: '/kb',
    },
    {
      icon: Plus,
      label: 'New knowledge base',
      hint: 'Per-KB index',
      href: '/kb/new',
    },
    {
      icon: Key,
      label: 'API access',
      hint: 'Tier 2 — disabled',
      disabled: true,
      disabledReason: 'API access — Tier 2 post-Beta',
    },
  ];

  return (
    <div className="card">
      <div className="card-header">
        <h3 className="card-title">Quick actions</h3>
      </div>
      <div
        className="card-body"
        style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}
      >
        {actions.map((a, i) => {
          const Ic = a.icon;
          const inner = (
            <>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <Ic size={15} className={a.disabled ? 'muted' : undefined} />
                <span style={{ fontWeight: 500 }}>{a.label}</span>
              </div>
              <div className="text-xs muted" style={{ fontWeight: 400 }}>
                {a.hint}
              </div>
            </>
          );
          const buttonStyle: React.CSSProperties = {
            height: 'auto',
            padding: '12px 12px',
            justifyContent: 'flex-start',
            textAlign: 'left',
            flexDirection: 'column',
            alignItems: 'flex-start',
            gap: 4,
          };
          if (a.disabled) {
            return (
              <button
                key={i}
                type="button"
                disabled
                aria-disabled="true"
                className="btn btn-secondary"
                style={{ ...buttonStyle, opacity: 0.5, cursor: 'default' }}
                title={a.disabledReason}
              >
                {inner}
              </button>
            );
          }
          return (
            <Link
              key={i}
              href={a.href ?? '/'}
              className="btn btn-secondary"
              style={buttonStyle}
            >
              {inner}
            </Link>
          );
        })}
      </div>
    </div>
  );
}

// ──────────────────────────────────────────────────────────────────────────
// Helpers
// ──────────────────────────────────────────────────────────────────────────

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
