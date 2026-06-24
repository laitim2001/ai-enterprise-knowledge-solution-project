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
  Check,
  Cpu,
  Download,
  Filter,
  Layers,
  Link,
  MoreHorizontal,
  Pencil,
  Plus,
  RefreshCw,
  Search,
  Shield,
  ShieldAlert,
  Users,
  type LucideIcon,
} from 'lucide-react';
import { useRouter, useSearchParams } from 'next/navigation';
import {
  Fragment,
  Suspense,
  useCallback,
  useMemo,
  useState,
  type CSSProperties,
  type ReactNode,
} from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { ErrorBoundary } from '@/components/error/error-boundary';
import { TabErrorState } from '@/components/settings/tab-error-state';
import { RoleBadge } from '@/components/users/role-badge';
import {
  adminApi,
  EKP_ROLE_LABELS,
  type AuditLogPage,
  type EkpRoleKey,
  type IdentityConfig,
} from '@/lib/api/admin';
import {
  usersApi,
  type GroupListResponse,
  type PermissionMatrixResponse,
  type RoleListResponse,
  type RolePermission,
  type UserListResponse,
  type UserSummary,
} from '@/lib/api/users';
import { useRole } from '@/lib/hooks/use-role';

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
  const role = useRole();
  const searchParams = useSearchParams();
  const router = useRouter();
  const initialTab = searchParams.get('tab') as TabId | null;
  const [tab, setTab] = useState<TabId>(
    initialTab && VALID_TABS.has(initialTab) ? initialTab : 'members',
  );
  const [inviteOpen, setInviteOpen] = useState(false); // F4 — invite member dialog

  // `/users` is Workspace-Admin-only (ADR-0027 permissions matrix —
  // `cfg.manage_users`). Skip the admin-gated `GET /users` fetch for
  // non-admins so they never trip a 403.
  const query = useQuery<UserListResponse>({
    queryKey: ['users', 'list'],
    queryFn: usersApi.listUsers,
    enabled: role === 'admin',
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

  // Role gate — `useRole()` is null while `/auth/me` is in flight.
  if (role === null) {
    return (
      <div className="content">
        <div className="content-wide">
          <div className="page-header">
            <h1 className="page-title">Users &amp; access</h1>
          </div>
          <div
            className="text-xs muted"
            style={{ padding: '48px 18px', textAlign: 'center' }}
          >
            Loading…
          </div>
        </div>
      </div>
    );
  }
  if (role !== 'admin') {
    return (
      <div className="content">
        <div className="content-wide">
          <div className="page-header">
            <h1 className="page-title">Users &amp; access</h1>
          </div>
          <div
            className="banner banner-warning"
            role="alert"
            style={{ alignItems: 'center' }}
          >
            <ShieldAlert size={14} aria-hidden="true" />
            <div style={{ flex: 1, lineHeight: 1.55 }}>
              <div style={{ fontSize: 13, fontWeight: 500 }}>
                Admin access required
              </div>
              <div className="text-xs muted">
                Managing workspace members, roles, and per-KB access needs the
                Workspace Admin role.
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

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
            <button
              type="button"
              className="btn btn-primary btn-sm"
              onClick={() => setInviteOpen(true)}
            >
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
            <RolesTab />
          </TabBoundary>
        )}
        {tab === 'groups' && (
          <TabBoundary tabName="Groups">
            <GroupsTab />
          </TabBoundary>
        )}
        {tab === 'audit' && (
          <TabBoundary tabName="Audit log">
            <AuditTab />
          </TabBoundary>
        )}
      </div>
      {/* F4 — invite member dialog */}
      {inviteOpen && <InviteDialog onClose={() => setInviteOpen(false)} />}
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
  // F4 — which row's ⋯ menu is open + the suspend-confirm target
  const [menuOpenId, setMenuOpenId] = useState<string | null>(null);
  const [suspendUser, setSuspendUser] = useState<UserSummary | null>(null);

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
                  <td className="col-shrink" style={{ position: 'relative' }}>
                    <button
                      type="button"
                      className="btn btn-ghost btn-icon btn-xs"
                      aria-label="Row actions"
                      aria-haspopup="menu"
                      aria-expanded={menuOpenId === u.oid}
                      onClick={() =>
                        setMenuOpenId(menuOpenId === u.oid ? null : u.oid)
                      }
                    >
                      <MoreHorizontal size={13} aria-hidden="true" />
                    </button>
                    {menuOpenId === u.oid && (
                      <>
                        {/* transparent backdrop — click-outside closes the menu */}
                        <div
                          style={{ position: 'fixed', inset: 0, zIndex: 25 }}
                          onClick={() => setMenuOpenId(null)}
                          aria-hidden="true"
                        />
                        <RowActionMenu
                          user={u}
                          onClose={() => setMenuOpenId(null)}
                          onSuspend={() => {
                            setMenuOpenId(null);
                            setSuspendUser(u);
                          }}
                        />
                      </>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {/* F4 — suspend confirm dialog */}
      {suspendUser && (
        <SuspendDialog user={suspendUser} onClose={() => setSuspendUser(null)} />
      )}
    </div>
  );
}

// ============================================================================
// F4 — /users write interactions (invite / role change / suspend)
// Canonical visual spec: mockup `ekp-page-users.jsx` InviteModal / RowActionMenu
// / SuspendModal (W88 P0 F4). Backend: usersApi.inviteUser / changeUserRole /
// suspendUser. shadcn Dialog (Radix a11y) + mockup .field / .btn classes for
// fidelity; row menu is row-anchored inline-style (NOT the topbar PopMenu §4.1).
// ============================================================================

function InviteDialog({ onClose }: { onClose: () => void }) {
  const queryClient = useQueryClient();
  const [email, setEmail] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [roleValue, setRoleValue] = useState<EkpRoleKey>('user');

  const inviteMutation = useMutation({
    mutationFn: () =>
      usersApi.inviteUser({
        email: email.trim(),
        role: roleValue,
        display_name: displayName.trim() || null,
      }),
    onSuccess: (u) => {
      toast.success(`Invited ${u.email}`);
      void queryClient.invalidateQueries({ queryKey: ['users', 'list'] });
      onClose();
    },
    onError: (e) =>
      toast.error(e instanceof Error ? e.message : 'Invite failed'),
  });

  return (
    <Dialog open onOpenChange={(o) => (!o ? onClose() : undefined)}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Invite member</DialogTitle>
          <DialogDescription>
            Pre-authorise an email + workspace role. An invite record is created
            (status = invited) and a verification email is sent.
          </DialogDescription>
        </DialogHeader>
        <div className="field">
          <label className="label" htmlFor="invite-email">
            Email address{' '}
            <span style={{ color: 'oklch(var(--destructive))' }}>*</span>
          </label>
          <input
            id="invite-email"
            className="input"
            type="email"
            placeholder="name@ricoh.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>
        <div className="field">
          <label className="label" htmlFor="invite-name">
            Display name
          </label>
          <input
            id="invite-name"
            className="input"
            placeholder="Optional — derived from email if left blank"
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
          />
        </div>
        <div className="field">
          <label className="label" htmlFor="invite-role">
            Workspace role
          </label>
          <select
            id="invite-role"
            className="select"
            value={roleValue}
            onChange={(e) => setRoleValue(e.target.value as EkpRoleKey)}
          >
            <option value="admin">Workspace Admin</option>
            <option value="editor">Knowledge Editor</option>
            <option value="user">End User</option>
            <option value="power" disabled>
              Power User · Tier 2
            </option>
          </select>
          <div className="hint">
            Power User is a Tier 2 role — not assignable in Tier 1.
          </div>
        </div>
        <DialogFooter>
          <button
            type="button"
            className="btn btn-ghost btn-sm"
            onClick={onClose}
          >
            Cancel
          </button>
          <button
            type="button"
            className="btn btn-primary btn-sm"
            disabled={!email.trim() || inviteMutation.isPending}
            onClick={() => inviteMutation.mutate()}
          >
            <Plus size={13} aria-hidden="true" /> Send invite
          </button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function RowActionMenu({
  user,
  onClose,
  onSuspend,
}: {
  user: UserSummary;
  onClose: () => void;
  onSuspend: () => void;
}) {
  const queryClient = useQueryClient();
  const tier1Roles: EkpRoleKey[] = ['admin', 'editor', 'user'];
  const itemStyle: CSSProperties = {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    width: '100%',
    padding: '7px 12px',
    fontSize: 12.5,
    textAlign: 'left',
    background: 'transparent',
    border: 0,
    cursor: 'pointer',
  };

  const roleMutation = useMutation({
    mutationFn: (role: EkpRoleKey) => usersApi.changeUserRole(user.oid, role),
    onSuccess: (u) => {
      toast.success(`${u.display_name} is now ${EKP_ROLE_LABELS[u.role]}`);
      void queryClient.invalidateQueries({ queryKey: ['users', 'list'] });
      onClose();
    },
    onError: (e) =>
      toast.error(e instanceof Error ? e.message : 'Role change failed'),
  });

  return (
    <div
      role="menu"
      style={{
        position: 'absolute',
        right: 8,
        top: '100%',
        marginTop: 4,
        width: 210,
        background: 'oklch(var(--popover))',
        border: '1px solid oklch(var(--border))',
        borderRadius: 'var(--radius-md)',
        boxShadow: 'var(--shadow-lg)',
        zIndex: 30,
        overflow: 'hidden',
        animation: 'pop-in 0.14s var(--ease)',
      }}
    >
      <div
        style={{
          padding: '8px 12px 4px',
          fontSize: 10.5,
          fontWeight: 700,
          letterSpacing: '0.04em',
          textTransform: 'uppercase',
          color: 'oklch(var(--muted-foreground))',
        }}
      >
        Change role
      </div>
      {tier1Roles.map((rk) => (
        <button
          key={rk}
          type="button"
          role="menuitem"
          style={{ ...itemStyle, color: 'oklch(var(--foreground))' }}
          disabled={roleMutation.isPending}
          onClick={() => (user.role === rk ? onClose() : roleMutation.mutate(rk))}
        >
          <span style={{ width: 14, display: 'inline-flex', flexShrink: 0 }}>
            {user.role === rk && (
              <Check size={12} style={{ color: 'oklch(var(--accent))' }} />
            )}
          </span>
          {EKP_ROLE_LABELS[rk]}
        </button>
      ))}
      <div
        style={{
          height: 1,
          background: 'oklch(var(--border))',
          margin: '4px 0',
        }}
      />
      <button
        type="button"
        role="menuitem"
        style={{ ...itemStyle, color: 'oklch(var(--destructive))' }}
        onClick={onSuspend}
      >
        <span style={{ width: 14, display: 'inline-flex', flexShrink: 0 }}>
          <Shield size={12} />
        </span>
        Suspend member
      </button>
    </div>
  );
}

function SuspendDialog({
  user,
  onClose,
}: {
  user: UserSummary;
  onClose: () => void;
}) {
  const queryClient = useQueryClient();
  const suspendMutation = useMutation({
    mutationFn: () => usersApi.suspendUser(user.oid),
    onSuccess: () => {
      toast.success(`Suspended ${user.display_name}`);
      void queryClient.invalidateQueries({ queryKey: ['users', 'list'] });
      onClose();
    },
    onError: (e) =>
      toast.error(e instanceof Error ? e.message : 'Suspend failed'),
  });

  return (
    <Dialog open onOpenChange={(o) => (!o ? onClose() : undefined)}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Suspend member?</DialogTitle>
          <DialogDescription>
            <b>{user.display_name}</b> ({user.email}) will lose access to all KBs
            and can no longer sign in. Re-invite to restore access.
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <button
            type="button"
            className="btn btn-ghost btn-sm"
            onClick={onClose}
          >
            Cancel
          </button>
          <button
            type="button"
            className="btn btn-sm"
            style={{ background: 'oklch(var(--destructive))', color: '#fff' }}
            disabled={suspendMutation.isPending}
            onClick={() => suspendMutation.mutate()}
          >
            Suspend member
          </button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// ============================================================================
// Roles & permissions tab — mockup `RolesTab` lines 209-286
// ============================================================================

/** Role-column order — matches the backend `_ROLE_ORDER` + the mockup matrix. */
const MATRIX_ROLES: EkpRoleKey[] = ['admin', 'editor', 'user', 'power'];

/** One area of the pivoted permissions matrix. */
interface MatrixArea {
  area: string;
  perms: {
    permissionKey: string;
    label: string;
    grants: Record<EkpRoleKey, boolean>;
  }[];
}

/**
 * Pivot the flat `RolePermission[]` (`GET /roles/permissions` — 92 rows ordered
 * area → permission → role per the backend `permission_matrix_rows()`) into the
 * area-grouped per-permission matrix the mockup renders. First-seen order is
 * kept — the backend already returns rows in the mockup's `PERMISSIONS_MATRIX`
 * order (F5 D5.4), so no explicit ordering constant is needed.
 */
function pivotMatrix(rows: RolePermission[]): MatrixArea[] {
  const areas: MatrixArea[] = [];
  const areaByName = new Map<string, MatrixArea>();
  const permById = new Map<string, MatrixArea['perms'][number]>();
  for (const row of rows) {
    let area = areaByName.get(row.area);
    if (!area) {
      area = { area: row.area, perms: [] };
      areaByName.set(row.area, area);
      areas.push(area);
    }
    const permId = `${row.area}::${row.permission_key}`;
    let perm = permById.get(permId);
    if (!perm) {
      perm = {
        permissionKey: row.permission_key,
        label: row.label,
        grants: { admin: false, editor: false, user: false, power: false },
      };
      permById.set(permId, perm);
      area.perms.push(perm);
    }
    perm.grants[row.role_key] = row.granted;
  }
  return areas;
}

function RolesTab() {
  const rolesQ = useQuery<RoleListResponse>({
    queryKey: ['roles', 'list'],
    queryFn: usersApi.listRoles,
  });
  const permsQ = useQuery<PermissionMatrixResponse>({
    queryKey: ['roles', 'permissions'],
    queryFn: usersApi.listPermissions,
  });
  // Shares the `['users', 'list']` cache entry with the page shell — TanStack
  // dedupes to a single request. Role-card member counts are client-side
  // (F5 D5.3 — `Role` carries no `member_count`).
  const usersQ = useQuery<UserListResponse>({
    queryKey: ['users', 'list'],
    queryFn: usersApi.listUsers,
  });

  const matrix = useMemo(
    () => pivotMatrix(permsQ.data?.permissions ?? []),
    [permsQ.data],
  );

  if (rolesQ.isLoading || permsQ.isLoading || usersQ.isLoading) {
    return (
      <div
        className="text-xs muted"
        style={{ padding: '48px 18px', textAlign: 'center' }}
      >
        Loading roles &amp; permissions…
      </div>
    );
  }
  if (rolesQ.isError || permsQ.isError || usersQ.isError) {
    return (
      <div
        className="banner banner-destructive"
        role="alert"
        style={{ alignItems: 'center' }}
      >
        <AlertTriangle size={14} aria-hidden="true" />
        <div style={{ flex: 1, lineHeight: 1.55 }}>
          <div style={{ fontSize: 13, fontWeight: 500 }}>
            Couldn&apos;t load roles
          </div>
          <div className="text-xs">
            A roles / permissions request failed. Reload the page to retry.
          </div>
        </div>
      </div>
    );
  }

  const roles = rolesQ.data?.roles ?? [];
  const users = usersQ.data?.users ?? [];

  return (
    <div className="col" style={{ gap: 16 }}>
      {/* RBAC banner — mockup lines 212-220 */}
      <div className="banner banner-info">
        <Shield
          size={14}
          aria-hidden="true"
          style={{ color: 'oklch(var(--info))' }}
        />
        <div style={{ flex: 1, lineHeight: 1.55 }}>
          <div style={{ fontSize: 13, fontWeight: 500 }}>
            Role-based access control (RBAC)
          </div>
          <div className="text-xs muted">
            Tier 1: Admin / Editor / End User — view-gating enforced
            server-side per audit log. Tier 2: Power User adds advanced
            retrieval tuning. Permissions are not editable per ADR-0024
            (predefined roles); custom roles are Tier 2.
          </div>
        </div>
      </div>

      {/* Role cards — mockup lines 223-241 */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(2, 1fr)',
          gap: 12,
        }}
      >
        {roles.map((role) => {
          const count = users.filter((u) => u.role === role.role_key).length;
          const isTier2 = role.tier >= 2;
          return (
            <div
              key={role.role_key}
              className="card"
              style={{ opacity: isTier2 ? 0.6 : 1 }}
            >
              <div className="card-body">
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                    marginBottom: 8,
                  }}
                >
                  <RoleBadge role={role.role_key} />
                  {isTier2 && (
                    <span className="badge badge-muted">TIER 2</span>
                  )}
                  <div className="spacer" />
                  <span className="mono text-xs muted">
                    {count} member{count !== 1 ? 's' : ''}
                  </span>
                </div>
                <div className="text-sm" style={{ lineHeight: 1.55 }}>
                  {role.description}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Permissions matrix — mockup lines 244-283 */}
      <div className="card">
        <div className="card-header">
          <div>
            <h3 className="card-title">Permissions matrix</h3>
            <div className="card-desc">
              What each role can do · ✓ = allowed · — = denied
            </div>
          </div>
          <button type="button" className="btn btn-ghost btn-sm">
            <Download size={13} aria-hidden="true" /> Export
          </button>
        </div>
        <div className="card-body card-body-tight">
          <table className="table" style={{ tableLayout: 'fixed' }}>
            <thead>
              <tr>
                <th style={{ width: '44%' }}>Permission</th>
                <th style={{ textAlign: 'center' }}>Admin</th>
                <th style={{ textAlign: 'center' }}>Editor</th>
                <th style={{ textAlign: 'center' }}>User</th>
                <th style={{ textAlign: 'center', opacity: 0.6 }}>
                  Power{' '}
                  <span className="badge badge-muted" style={{ fontSize: 9 }}>
                    T2
                  </span>
                </th>
              </tr>
            </thead>
            <tbody>
              {matrix.map((area) => (
                <Fragment key={area.area}>
                  <tr style={{ background: 'oklch(var(--muted) / 0.3)' }}>
                    <td
                      colSpan={5}
                      className="text-xs muted mono"
                      style={{
                        padding: '8px 16px',
                        letterSpacing: '0.04em',
                        textTransform: 'uppercase',
                        fontWeight: 700,
                      }}
                    >
                      {area.area}
                    </td>
                  </tr>
                  {area.perms.map((perm) => (
                    <tr key={perm.permissionKey}>
                      <td>{perm.label}</td>
                      {MATRIX_ROLES.map((rk) => (
                        <td
                          key={rk}
                          style={{
                            textAlign: 'center',
                            ...(rk === 'power' ? { opacity: 0.6 } : {}),
                          }}
                        >
                          {perm.grants[rk] ? (
                            <Check
                              size={13}
                              aria-label="Allowed"
                              style={{ color: 'oklch(var(--success))' }}
                            />
                          ) : (
                            <span className="muted" aria-label="Denied">
                              —
                            </span>
                          )}
                        </td>
                      ))}
                    </tr>
                  ))}
                </Fragment>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// Groups tab — mockup `GroupsTab` lines 288-322
// ============================================================================

/** Relative-time format for the group `synced_at` column. */
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

/** Compact a long Entra object id (GUID) to `first4…last4` per the mockup. */
function truncateOid(oid: string | null): string {
  if (!oid) return '—';
  return oid.length > 12 ? `${oid.slice(0, 4)}…${oid.slice(-4)}` : oid;
}

function GroupsTab() {
  const groupsQ = useQuery<GroupListResponse>({
    queryKey: ['groups', 'list'],
    queryFn: usersApi.listGroups,
  });
  // `GET /groups` carries no role mapping (F6 D6.3) — the group → EKP role
  // join is client-side off the Settings → Identity & Auth role mappings.
  const identityQ = useQuery<IdentityConfig>({
    queryKey: ['admin', 'identity'],
    queryFn: adminApi.getIdentity,
  });

  const roleByGroupId = useMemo(() => {
    const map = new Map<string, EkpRoleKey>();
    for (const m of identityQ.data?.roles.mappings ?? []) {
      map.set(m.entra_group_id, m.ekp_role);
    }
    return map;
  }, [identityQ.data]);

  if (groupsQ.isLoading || identityQ.isLoading) {
    return (
      <div
        className="text-xs muted"
        style={{ padding: '48px 18px', textAlign: 'center' }}
      >
        Loading groups…
      </div>
    );
  }
  if (groupsQ.isError || identityQ.isError) {
    return (
      <div
        className="banner banner-destructive"
        role="alert"
        style={{ alignItems: 'center' }}
      >
        <AlertTriangle size={14} aria-hidden="true" />
        <div style={{ flex: 1, lineHeight: 1.55 }}>
          <div style={{ fontSize: 13, fontWeight: 500 }}>
            Couldn&apos;t load groups
          </div>
          <div className="text-xs">
            The <span className="mono">/groups</span> request failed. Reload
            the page to retry.
          </div>
        </div>
      </div>
    );
  }

  const groups = groupsQ.data?.groups ?? [];
  const tenantDomain = identityQ.data?.tenant.tenant_domain ?? '—';

  return (
    <div className="card">
      <div className="card-header">
        <div>
          <h3 className="card-title">Entra ID groups</h3>
          <div className="card-desc">
            Synced from <span className="mono">{tenantDomain}</span> tenant ·
            group → role mapping in Settings → Identity &amp; Auth
          </div>
        </div>
        <button type="button" className="btn btn-secondary btn-sm">
          <RefreshCw size={13} aria-hidden="true" /> Sync from Entra
        </button>
      </div>
      <div className="card-body card-body-tight">
        {groups.length === 0 ? (
          <div
            className="text-xs muted"
            style={{ padding: '48px 18px', textAlign: 'center' }}
          >
            No Entra ID groups synced yet.
          </div>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Group name</th>
                <th>Object ID</th>
                <th>EKP role</th>
                <th className="col-num">Members</th>
                <th className="col-num">Synced</th>
                <th className="col-shrink" aria-label="Row actions" />
              </tr>
            </thead>
            <tbody>
              {groups.map((g) => {
                const mappedRole = g.entra_object_id
                  ? roleByGroupId.get(g.entra_object_id)
                  : undefined;
                return (
                  <tr key={g.group_key}>
                    <td className="col-mono">{g.name}</td>
                    <td className="col-mono text-xs">
                      {truncateOid(g.entra_object_id)}
                    </td>
                    <td>
                      {mappedRole ? (
                        <RoleBadge role={mappedRole} />
                      ) : (
                        <span className="text-xs muted">Not mapped</span>
                      )}
                    </td>
                    <td className="col-num">{g.member_count}</td>
                    <td className="col-num text-xs">
                      {formatRelative(g.synced_at)}
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
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

// ============================================================================
// Audit log tab — mockup `AuditTab` lines 324-377
// ============================================================================

/** Action → feed icon, prefix-matched per the mockup `actionIcon` (lines 333-339). */
function auditActionIcon(action: string): LucideIcon {
  if (action.startsWith('role')) return Shield;
  if (action.startsWith('user')) return Users;
  if (action.startsWith('kb.access')) return Link;
  if (action.startsWith('provider')) return Cpu;
  if (action.startsWith('kb.config')) return Pencil;
  return Activity;
}

/**
 * Synthesize the feed's 3rd line from the entry `payload` — the backend has no
 * human `note` field, so scalar payload entries render as `k: v · k: v`
 * (nested / null values skipped; the backend guarantees no secrets in payload).
 */
function payloadNote(payload: Record<string, unknown> | null): string {
  if (!payload) return '';
  const parts: string[] = [];
  for (const [k, v] of Object.entries(payload)) {
    if (v === null || typeof v === 'object') continue;
    parts.push(`${k}: ${String(v)}`);
  }
  return parts.join(' · ');
}

function AuditTab() {
  const auditQ = useQuery<AuditLogPage>({
    queryKey: ['admin', 'audit-log'],
    queryFn: () => adminApi.listAuditLog(),
  });

  if (auditQ.isLoading) {
    return (
      <div
        className="text-xs muted"
        style={{ padding: '48px 18px', textAlign: 'center' }}
      >
        Loading audit log…
      </div>
    );
  }
  if (auditQ.isError) {
    return (
      <div
        className="banner banner-destructive"
        role="alert"
        style={{ alignItems: 'center' }}
      >
        <AlertTriangle size={14} aria-hidden="true" />
        <div style={{ flex: 1, lineHeight: 1.55 }}>
          <div style={{ fontSize: 13, fontWeight: 500 }}>
            Couldn&apos;t load the audit log
          </div>
          <div className="text-xs">
            The <span className="mono">/admin/audit-log</span> request failed.
            Reload the page to retry.
          </div>
        </div>
      </div>
    );
  }

  const events = auditQ.data?.entries ?? [];

  return (
    <div className="card">
      <div className="card-header">
        <div>
          <h3 className="card-title">Workspace audit log</h3>
          <div className="card-desc">
            Every role / access / config change is logged with actor + target
            + timestamp · 90d retention
          </div>
        </div>
        <div className="row">
          <button type="button" className="btn btn-secondary btn-sm">
            <Filter size={13} aria-hidden="true" /> Filter
          </button>
          <button type="button" className="btn btn-secondary btn-sm">
            <Download size={13} aria-hidden="true" /> Export
          </button>
        </div>
      </div>
      <div className="card-body card-body-tight">
        {events.length === 0 ? (
          <div
            className="text-xs muted"
            style={{ padding: '48px 18px', textAlign: 'center' }}
          >
            No audit events yet.
          </div>
        ) : (
          events.map((e, i, arr) => {
            const Icon = auditActionIcon(e.action);
            const note = payloadNote(e.payload);
            return (
              <div
                key={e.id ?? i}
                style={{
                  display: 'flex',
                  gap: 12,
                  padding: '12px 18px',
                  borderBottom:
                    i < arr.length - 1
                      ? '1px solid oklch(var(--border))'
                      : 'none',
                }}
              >
                <div
                  style={{
                    width: 26,
                    height: 26,
                    borderRadius: 'var(--radius-sm)',
                    background: 'oklch(var(--muted))',
                    display: 'grid',
                    placeItems: 'center',
                    flexShrink: 0,
                  }}
                >
                  <Icon size={13} className="muted" aria-hidden="true" />
                </div>
                <div style={{ flex: 1 }}>
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 8,
                      marginBottom: 2,
                    }}
                  >
                    <span
                      className="mono text-xs"
                      style={{
                        background: 'oklch(var(--muted))',
                        padding: '1px 5px',
                        borderRadius: 3,
                        fontWeight: 600,
                      }}
                    >
                      {e.action}
                    </span>
                    <span className="text-xs muted">by</span>
                    <span className="mono text-xs">{e.actor ?? 'system'}</span>
                  </div>
                  <div style={{ fontSize: 12.5, lineHeight: 1.45 }}>
                    {e.resource}
                  </div>
                  {note && (
                    <div className="text-xs muted" style={{ marginTop: 2 }}>
                      {note}
                    </div>
                  )}
                </div>
                <span className="text-xs muted mono" style={{ flexShrink: 0 }}>
                  {formatRelative(e.created_at)}
                </span>
              </div>
            );
          })
        )}
      </div>
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
