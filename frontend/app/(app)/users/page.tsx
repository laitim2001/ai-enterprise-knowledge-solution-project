'use client';

/**
 * `/users` — Users & access (W24c F9.2 per ADR-0027 Option A).
 *
 * Canonical visual spec: mockup `references/design-mockups/ekp-page-users.jsx`
 * lines 62-191 (`PageUsers` shell + `UsersTab` Members tab).
 *
 * F9.2 ships the route shell + the Members tab. The Roles / Groups / Audit log
 * tab bodies land with F9.3 / F9.4 — until then they render a transient
 * `<TabPlaceholder>`. The `useRole()` role-gated rendering is F9.4 scope.
 *
 * **Pre-active-flip R6 audit** (per CLAUDE.md §10 R6 — plan §7 Day 10):
 *   - Tab pattern follows `settings/page.tsx`: `<button role="tab">` + `?tab=`
 *     deep-link via `useSearchParams` (Suspense-boundary required). The mockup's
 *     plain `useState` is a prototype URL-state simplification — non-H7 deviation.
 *   - `GET /users` is a backend subset (F4 D4.1 — `UserSummary` has no
 *     `source` / `group` / `queries_7d` / `kbs_owned` / `last_login`). All 10
 *     table columns + all 4 stat cards are kept (visual fidelity per §13);
 *     the 5 missing-data cells + 2 unavailable stats render `—` per the W22
 *     B-i placeholder policy (`kb/page.tsx` precedent).
 *   - The mockup's "Export CSV" / "Invite member" / per-row "More" buttons are
 *     presentational (no onClick / modal / menu in the click-through prototype)
 *     — reproduced inert. Functional invite / role-change UI is not in the
 *     mockup, so it is not built (Karpathy §1.2).
 */

import {
  Activity,
  AlertTriangle,
  Download,
  Filter,
  Layers,
  MoreHorizontal,
  Plus,
  Search,
  Shield,
  Users,
} from 'lucide-react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Suspense, useCallback, useMemo, useState, type ReactNode } from 'react';
import { useQuery } from '@tanstack/react-query';

import { ErrorBoundary } from '@/components/error/error-boundary';
import { TabErrorState } from '@/components/settings/tab-error-state';
import { RoleBadge } from '@/components/users/role-badge';
import { usersApi, type UserListResponse, type UserSummary } from '@/lib/api/users';

const TABS = [
  { id: 'members', label: 'Members', icon: Users },
  { id: 'roles', label: 'Roles & permissions', icon: Shield },
  { id: 'groups', label: 'Groups', icon: Layers },
  { id: 'audit', label: 'Audit log', icon: Activity },
] as const;

type TabId = (typeof TABS)[number]['id'];

const VALID_TABS = new Set<TabId>(TABS.map((t) => t.id));

/** Members-tab seg filter — `admin` / `editor` / `user` map to `UserSummary.role`. */
type MemberFilter = 'all' | 'admin' | 'editor' | 'user' | 'pending';

const SEG_FILTERS: { id: MemberFilter; label: string }[] = [
  { id: 'all', label: 'All' },
  { id: 'admin', label: 'Admin' },
  { id: 'editor', label: 'Editor' },
  { id: 'user', label: 'User' },
  { id: 'pending', label: 'Pending' },
];

/** 2-char avatar initials from `display_name`, falling back to the email local-part. */
function initials(name: string, email: string): string {
  const src = name.trim() || (email.split('@')[0] ?? '');
  const parts = src.split(/[\s.\-_+]/).filter(Boolean);
  if (parts.length >= 2 && parts[0] && parts[1]) {
    return (parts[0][0]! + parts[1][0]!).toUpperCase();
  }
  return src.slice(0, 2).toUpperCase() || '??';
}

/** Wraps a tab body in an error boundary scoped to that tab (mirrors settings). */
function TabBoundary({
  tabName,
  children,
}: {
  tabName: string;
  children: ReactNode;
}) {
  return (
    <ErrorBoundary
      fallback={(reset) => <TabErrorState tabName={tabName} onRetry={reset} />}
    >
      {children}
    </ErrorBoundary>
  );
}

// ============================================================================
// Page shell — mockup `PageUsers` lines 62-113
// ============================================================================

export default function UsersPage() {
  return (
    <Suspense
      fallback={
        <div className="content">
          <div className="content-wide">
            <div className="page-header">
              <h1 className="page-title">Users &amp; access</h1>
            </div>
          </div>
        </div>
      }
    >
      <UsersPageInner />
    </Suspense>
  );
}

function UsersPageInner() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const initialTab = searchParams.get('tab') as TabId | null;
  const [tab, setTab] = useState<TabId>(
    initialTab && VALID_TABS.has(initialTab) ? initialTab : 'members',
  );

  const query = useQuery<UserListResponse>({
    queryKey: ['users', 'list'],
    queryFn: usersApi.listUsers,
  });
  const users = useMemo(() => query.data?.users ?? [], [query.data]);
  const loaded = query.isSuccess;

  const counts = useMemo<Record<MemberFilter, number>>(
    () => ({
      all: users.length,
      admin: users.filter((u) => u.role === 'admin').length,
      editor: users.filter((u) => u.role === 'editor').length,
      user: users.filter((u) => u.role === 'user').length,
      pending: users.filter(
        (u) => u.status === 'pending' || u.status === 'invited',
      ).length,
    }),
    [users],
  );

  const handleTabChange = useCallback(
    (next: TabId) => {
      setTab(next);
      // Shallow URL update — preserves deep-link sharing without full navigation.
      const url = new URL(window.location.href);
      url.searchParams.set('tab', next);
      router.replace(url.pathname + url.search, { scroll: false });
    },
    [router],
  );

  return (
    <div className="content">
      <div className="content-wide">
        {/* Page header — mockup lines 81-90 */}
        <div className="page-header">
          <div>
            <h1 className="page-title">Users &amp; access</h1>
            <p className="page-subtitle">
              Workspace members · role assignment · per-KB access. Roles are
              mapped via Entra ID groups; assignments here update both Postgres{' '}
              <span className="mono">users</span> table and Entra group
              membership.
            </p>
          </div>
          <div className="page-actions">
            <button type="button" className="btn btn-secondary btn-sm">
              <Download size={13} aria-hidden="true" /> Export CSV
            </button>
            <button type="button" className="btn btn-primary btn-sm">
              <Plus size={13} aria-hidden="true" /> Invite member
            </button>
          </div>
        </div>

        {/* Stat grid — mockup lines 92-97 */}
        <div
          className="stat-grid"
          style={{ gridTemplateColumns: 'repeat(4, 1fr)', marginBottom: 16 }}
        >
          <StatCard
            label="Total members"
            value={loaded ? String(users.length) : '—'}
            sub={
              loaded
                ? `${counts.admin} Admin · ${counts.editor} Editor · ${counts.user} User`
                : '—'
            }
          />
          {/* Session tracking is not a Tier 1 backend surface — W22 B-i placeholder. */}
          <StatCard label="Active sessions" value="—" sub="—" />
          <StatCard
            label="Pending invites"
            value={loaded ? String(counts.pending) : '—'}
            sub="Email verification pending"
          />
          {/* Per-user query volume needs the query log (Q6 open) — W22 B-i placeholder. */}
          <StatCard label="Avg queries / user" value="—" sub="—" />
        </div>

        {/* Tab navigation — mockup lines 99-104 */}
        <div className="tabs" role="tablist" aria-label="User management sections">
          {TABS.map((t) => {
            const Icon = t.icon;
            const active = tab === t.id;
            return (
              <button
                key={t.id}
                type="button"
                role="tab"
                aria-selected={active}
                className="tab"
                data-active={active}
                onClick={() => handleTabChange(t.id)}
              >
                <Icon size={14} aria-hidden="true" /> {t.label}
                {t.id === 'members' && (
                  <span className="count">{loaded ? users.length : '—'}</span>
                )}
              </button>
            );
          })}
        </div>

        {/* Tab body — F9.2 ships Members; F9.3 / F9.4 replace the placeholders. */}
        {tab === 'members' && (
          <TabBoundary tabName="Members">
            <UsersTab
              users={users}
              counts={counts}
              isLoading={query.isLoading}
              isError={query.isError}
            />
          </TabBoundary>
        )}
        {tab === 'roles' && (
          <TabBoundary tabName="Roles & permissions">
            <TabPlaceholder label="Roles & permissions" />
          </TabBoundary>
        )}
        {tab === 'groups' && (
          <TabBoundary tabName="Groups">
            <TabPlaceholder label="Groups" />
          </TabBoundary>
        )}
        {tab === 'audit' && (
          <TabBoundary tabName="Audit log">
            <TabPlaceholder label="Audit log" />
          </TabBoundary>
        )}
      </div>
    </div>
  );
}

// ============================================================================
// Members tab — mockup `UsersTab` lines 115-191
// ============================================================================

function UsersTab({
  users,
  counts,
  isLoading,
  isError,
}: {
  users: UserSummary[];
  counts: Record<MemberFilter, number>;
  isLoading: boolean;
  isError: boolean;
}) {
  const [filter, setFilter] = useState<MemberFilter>('all');
  const [search, setSearch] = useState('');

  const visible = useMemo(() => {
    let rows = users;
    if (filter === 'pending') {
      rows = rows.filter(
        (u) => u.status === 'pending' || u.status === 'invited',
      );
    } else if (filter !== 'all') {
      rows = rows.filter((u) => u.role === filter);
    }
    const term = search.trim().toLowerCase();
    if (term) {
      rows = rows.filter(
        (u) =>
          u.display_name.toLowerCase().includes(term) ||
          u.email.toLowerCase().includes(term),
      );
    }
    return rows;
  }, [users, filter, search]);

  return (
    <div>
      {/* Toolbar — mockup lines 118-138 */}
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
            <Search size={14} aria-hidden="true" />
          </span>
          <input
            className="input"
            placeholder="Search by name, email, group…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <div className="seg">
          {SEG_FILTERS.map((f) => (
            <button
              key={f.id}
              type="button"
              className="seg-btn"
              data-active={filter === f.id}
              onClick={() => setFilter(f.id)}
            >
              {f.label}{' '}
              <span className="text-xs mono" style={{ opacity: 0.6 }}>
                {counts[f.id]}
              </span>
            </button>
          ))}
        </div>
        <div className="spacer" />
        <button type="button" className="btn btn-secondary btn-sm">
          <Filter size={13} aria-hidden="true" /> More filters
        </button>
      </div>

      {isLoading ? (
        <div
          className="text-xs muted"
          style={{ padding: '48px 18px', textAlign: 'center' }}
        >
          Loading members…
        </div>
      ) : isError ? (
        <div
          className="banner banner-destructive"
          role="alert"
          style={{ alignItems: 'center' }}
        >
          <AlertTriangle size={14} aria-hidden="true" />
          <div style={{ flex: 1, lineHeight: 1.55 }}>
            <div style={{ fontSize: 13, fontWeight: 500 }}>
              Couldn&apos;t load members
            </div>
            <div className="text-xs">
              The <span className="mono">/users</span> request failed. Reload
              the page to retry.
            </div>
          </div>
        </div>
      ) : visible.length === 0 ? (
        <div
          className="text-xs muted"
          style={{ padding: '48px 18px', textAlign: 'center' }}
        >
          No members match the current filter.
        </div>
      ) : (
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th style={{ width: 26 }}>
                  <span className="kbd" style={{ padding: '0 4px' }}>
                    ☐
                  </span>
                </th>
                <th>Member</th>
                <th>Role</th>
                <th>Auth source</th>
                <th>Entra group</th>
                <th className="col-num">Queries (7d)</th>
                <th className="col-num">KBs owned</th>
                <th className="col-num">Last login</th>
                <th>Status</th>
                <th className="col-shrink" aria-label="Row actions" />
              </tr>
            </thead>
            <tbody>
              {visible.map((u) => (
                <tr key={u.oid}>
                  <td>
                    <span className="kbd" style={{ padding: '0 4px' }}>
                      ☐
                    </span>
                  </td>
                  <td>
                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 10,
                      }}
                    >
                      <div className="avatar avatar-sm" aria-hidden="true">
                        {initials(u.display_name, u.email)}
                      </div>
                      <div>
                        <div className="table-row-link">{u.display_name}</div>
                        <div className="text-xs muted mono">{u.email}</div>
                      </div>
                    </div>
                  </td>
                  <td>
                    <RoleBadge role={u.role} />
                  </td>
                  {/* Auth source — not a Tier 1 `UserSummary` field (F4 D4.1). */}
                  <td>
                    <span className="text-xs muted">—</span>
                  </td>
                  {/* Entra group — not a Tier 1 `UserSummary` field (F4 D4.1). */}
                  <td className="col-mono">
                    <span className="muted">—</span>
                  </td>
                  {/* Queries (7d) — needs the query log (Q6 open). */}
                  <td className="col-num">
                    <span className="muted">—</span>
                  </td>
                  {/* KBs owned — needs a KB ownership model (not Tier 1). */}
                  <td className="col-num">
                    <span className="muted">—</span>
                  </td>
                  {/* Last login — not a Tier 1 `UserSummary` field (F4 D4.1). */}
                  <td className="col-num text-xs">
                    <span className="muted">—</span>
                  </td>
                  <td>
                    {u.status === 'active' && (
                      <span className="badge badge-success">
                        <span className="badge-dot" /> ACTIVE
                      </span>
                    )}
                    {u.status === 'pending' && (
                      <span className="badge badge-warning">
                        <span className="badge-dot" /> PENDING EMAIL
                      </span>
                    )}
                    {u.status === 'invited' && (
                      <span className="badge badge-info">
                        <span className="badge-dot" /> INVITED
                      </span>
                    )}
                    {u.status === 'suspended' && (
                      <span className="badge badge-error">
                        <span className="badge-dot" /> SUSPENDED
                      </span>
                    )}
                  </td>
                  <td className="col-shrink">
                    <button
                      type="button"
                      className="btn btn-ghost btn-icon btn-xs"
                      aria-label="Row actions"
                    >
                      <MoreHorizontal size={13} aria-hidden="true" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Shared helpers
// ============================================================================

/** Stat card — mockup `Stat` lines 379-387. */
function StatCard({
  label,
  value,
  sub,
}: {
  label: string;
  value: string;
  sub: string;
}) {
  return (
    <div className="stat">
      <div className="stat-label">{label}</div>
      <div className="stat-value">{value}</div>
      <div className="stat-meta">{sub}</div>
    </div>
  );
}

/** Transient body for the not-yet-built tabs — replaced by F9.3 / F9.4. */
function TabPlaceholder({ label }: { label: string }) {
  return (
    <div
      className="text-xs muted"
      style={{ padding: '48px 18px', textAlign: 'center' }}
    >
      {label} — under construction.
    </div>
  );
}
