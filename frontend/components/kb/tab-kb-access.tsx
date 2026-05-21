'use client';

/**
 * `<TabKbAccess>` — the KB Detail "Access" tab (W24c F10 per ADR-0025 + ADR-0027).
 *
 * Canonical visual spec: mockup `references/design-mockups/ekp-page-users.jsx`
 * lines 390-519 (`TabKbAccess`). Surfaces the F8 `kb_acl` backend
 * (`GET /kb/{id}/acl`).
 *
 * **Pre-active-flip R6 audit** (per CLAUDE.md §10 R6 — plan §7 Day 13):
 *   - `GET /kb/{id}/acl` returns explicit grants only (F8 D8.3). This tab adds
 *     the synthetic "Workspace Admins (auto)" system row — truthful, it mirrors
 *     the `require_kb_acl` admin-always-pass rule. Group-inherited rows need
 *     group-member data (F6 D6.5 deferred) — skipped.
 *   - The Visibility card has no Tier 1 backend (F8 D8.4 deferred KB Visibility)
 *     — rendered read-only (radios disabled) per the W22 B-i placeholder policy.
 *   - The mockup's CRUD affordances (Add member / Add Entra group / per-row KB
 *     role select / row More) are presentational — reproduced inert. Only the
 *     footer "Manage all → /users" nav is functional in the mockup.
 *   - Member / Group display names + workspace roles are a client-side join
 *     onto `/users` + `/groups`; the tab only blocks on the `kb_acl` fetch.
 */

import {
  Globe,
  Layers,
  Link,
  MoreHorizontal,
  Plus,
  Shield,
  Users,
} from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';

import { RoleBadge } from '@/components/users/role-badge';
import type { EkpRoleKey } from '@/lib/api/admin';
import {
  kbApi,
  type KbAclListResponse,
  type KbAclRole,
} from '@/lib/api/kb';
import {
  usersApi,
  type GroupListResponse,
  type UserListResponse,
} from '@/lib/api/users';

const VISIBILITY_ROWS = [
  {
    id: 'private',
    icon: Shield,
    label: 'Private',
    desc: "Only explicit members + Workspace Admins · others can't see this KB",
    tier2: false,
  },
  {
    id: 'workspace',
    icon: Users,
    label: 'Workspace',
    desc: 'Any member of Ricoh · RAPO can find + query this KB',
    tier2: false,
  },
  {
    id: 'public',
    icon: Globe,
    label: 'Public (Tier 2)',
    desc: 'Listed in public KB catalog · queryable via anonymous API key',
    tier2: true,
  },
] as const;

/** 2-char avatar initials from a display name. */
function initials(name: string): string {
  const parts = name.trim().split(/[\s.\-_+]/).filter(Boolean);
  if (parts.length >= 2 && parts[0] && parts[1]) {
    return (parts[0][0]! + parts[1][0]!).toUpperCase();
  }
  return name.trim().slice(0, 2).toUpperCase() || '??';
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

/** One rendered Members-table row — a synthetic system row or a `kb_acl` grant. */
interface AccessRow {
  key: string;
  kind: 'user' | 'group';
  name: string;
  sub: string;
  avatar?: string;
  workspaceRole: EkpRoleKey | null;
  kbRole: KbAclRole;
  grantedBy: string;
  granted: string;
  locked: boolean;
}

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

export function TabKbAccess({ kbId }: { kbId: string }) {
  const router = useRouter();

  const aclQ = useQuery<KbAclListResponse>({
    queryKey: ['kb', kbId, 'acl'],
    queryFn: () => kbApi.listAcl(kbId),
  });
  // Best-effort joins — display names + workspace roles. The tab blocks only
  // on the `kb_acl` fetch; if these fail, rows fall back to the principal id.
  const usersQ = useQuery<UserListResponse>({
    queryKey: ['users', 'list'],
    queryFn: usersApi.listUsers,
  });
  const groupsQ = useQuery<GroupListResponse>({
    queryKey: ['groups', 'list'],
    queryFn: usersApi.listGroups,
  });

  const entries = useMemo(() => aclQ.data?.entries ?? [], [aclQ.data]);

  const rows = useMemo<AccessRow[]>(() => {
    const usersById = new Map(
      (usersQ.data?.users ?? []).map((u) => [u.oid, u]),
    );
    const groupsByKey = new Map(
      (groupsQ.data?.groups ?? []).map((g) => [g.group_key, g]),
    );
    // Synthetic system row — workspace admins always have manage access
    // (the `require_kb_acl` admin-always-pass rule; F8 D8.3).
    const out: AccessRow[] = [
      {
        key: 'system-admins',
        kind: 'group',
        name: 'Workspace Admins',
        sub: 'Workspace Admins · auto',
        workspaceRole: 'admin',
        kbRole: 'manage',
        grantedBy: 'system',
        granted: '—',
        locked: true,
      },
    ];
    for (const e of entries) {
      if (e.principal_type === 'user') {
        const u = usersById.get(e.principal_id);
        const name = u?.display_name ?? e.principal_id;
        out.push({
          key: `acl-${e.id}`,
          kind: 'user',
          name,
          sub: u?.email ?? e.principal_id,
          avatar: initials(name),
          workspaceRole: u?.role ?? null,
          kbRole: e.access_role,
          grantedBy: e.granted_by ?? 'system',
          granted: formatRelative(e.created_at),
          locked: false,
        });
      } else {
        const g = groupsByKey.get(e.principal_id);
        out.push({
          key: `acl-${e.id}`,
          kind: 'group',
          name: g?.name ?? e.principal_id,
          // Group → workspace role mapping lives in Settings → Identity & Auth
          // (F6 D6.3) — not joined here; the column falls back to "—".
          sub: g?.description ?? '(group)',
          workspaceRole: null,
          kbRole: e.access_role,
          grantedBy: e.granted_by ?? 'system',
          granted: formatRelative(e.created_at),
          locked: false,
        });
      }
    }
    return out;
  }, [entries, usersQ.data, groupsQ.data]);

  if (aclQ.isLoading) {
    return (
      <div
        className="text-xs muted"
        style={{ padding: '48px 18px', textAlign: 'center' }}
      >
        Loading access list…
      </div>
    );
  }
  if (aclQ.isError) {
    return (
      <div
        className="banner banner-destructive"
        role="alert"
        style={{ alignItems: 'center' }}
      >
        <Shield size={14} aria-hidden="true" />
        <div style={{ flex: 1, lineHeight: 1.55 }}>
          <div style={{ fontSize: 13, fontWeight: 500 }}>
            Couldn&apos;t load the access list
          </div>
          <div className="text-xs">
            Managing a KB&apos;s access list requires the <span className="mono">manage</span>{' '}
            role on this KB.
          </div>
        </div>
      </div>
    );
  }

  const byRole = { manage: 0, edit: 0, query: 0 };
  for (const e of entries) byRole[e.access_role] += 1;

  return (
    <div>
      {/* Banner — mockup lines 393-401 */}
      <div className="banner banner-info" style={{ marginBottom: 16 }}>
        <Shield
          size={14}
          aria-hidden="true"
          style={{ color: 'oklch(var(--info))' }}
        />
        <div style={{ flex: 1, lineHeight: 1.55 }}>
          <div style={{ fontSize: 13, fontWeight: 500 }}>
            Per-KB access control
          </div>
          <div className="text-xs muted">
            Members listed here can query / edit / manage <b>this</b> KB
            regardless of their workspace role. Workspace Admins always have
            full access.
          </div>
        </div>
      </div>

      {/* Stat grid — mockup lines 403-408 */}
      <div
        className="stat-grid"
        style={{ gridTemplateColumns: 'repeat(4, 1fr)', marginBottom: 16 }}
      >
        {/* KB Visibility is not a Tier 1 backend field (F8 D8.4) — W22 B-i. */}
        <StatCard label="Visibility" value="—" sub="—" />
        <StatCard
          label="Members with access"
          value={String(entries.length)}
          sub={`${byRole.manage} manage · ${byRole.edit} edit · ${byRole.query} query`}
        />
        <StatCard label="Pending invites" value="—" sub="—" />
        <StatCard label="Default new member access" value="—" sub="—" />
      </div>

      {/* Visibility card — mockup lines 410-439. No Tier 1 backend (F8 D8.4) —
          rendered read-only: the radios are disabled, "Workspace" preselected. */}
      <div className="card" style={{ marginBottom: 16 }}>
        <div className="card-header">
          <div>
            <h3 className="card-title">Visibility</h3>
            <div className="card-desc">Who can see this KB exists at all</div>
          </div>
        </div>
        <div className="card-body card-body-tight">
          {VISIBILITY_ROWS.map((v, i, arr) => {
            const Icon = v.icon;
            return (
              <div
                key={v.id}
                style={{
                  display: 'flex',
                  gap: 12,
                  padding: '12px 18px',
                  borderBottom:
                    i < arr.length - 1
                      ? '1px solid oklch(var(--border))'
                      : 'none',
                  opacity: v.tier2 ? 0.5 : 1,
                }}
              >
                <input
                  type="radio"
                  name="kb-visibility"
                  aria-label={v.label}
                  defaultChecked={v.id === 'workspace'}
                  disabled
                  style={{ marginTop: 3, flexShrink: 0 }}
                />
                <Icon
                  size={14}
                  className="muted"
                  aria-hidden="true"
                  style={{ marginTop: 3, flexShrink: 0 }}
                />
                <div style={{ flex: 1 }}>
                  <div
                    style={{ display: 'flex', alignItems: 'center', gap: 6 }}
                  >
                    <span style={{ fontWeight: 500, fontSize: 13.5 }}>
                      {v.label}
                    </span>
                    {v.tier2 && (
                      <span className="badge badge-muted">Tier 2</span>
                    )}
                  </div>
                  <div
                    className="text-xs muted"
                    style={{ marginTop: 2, lineHeight: 1.5 }}
                  >
                    {v.desc}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Members & permissions — mockup lines 441-512 */}
      <div className="card">
        <div className="card-header">
          <div>
            <h3 className="card-title">Members &amp; permissions</h3>
            <div className="card-desc">
              Per-KB role overrides workspace role · &ldquo;Manager&rdquo; can
              edit access list itself
            </div>
          </div>
          <div className="row">
            <button type="button" className="btn btn-secondary btn-sm">
              <Link size={13} aria-hidden="true" /> Add Entra group
            </button>
            <button type="button" className="btn btn-primary btn-sm">
              <Plus size={13} aria-hidden="true" /> Add member
            </button>
          </div>
        </div>
        <div className="card-body card-body-tight">
          <table className="table">
            <thead>
              <tr>
                <th>Member / Group</th>
                <th>Workspace role</th>
                <th>KB role</th>
                <th>Granted by</th>
                <th className="col-num">Granted</th>
                <th className="col-shrink" aria-label="Row actions" />
              </tr>
            </thead>
            <tbody>
              {rows.map((m) => (
                <tr key={m.key}>
                  <td>
                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 10,
                      }}
                    >
                      {m.kind === 'user' ? (
                        <div className="avatar avatar-sm" aria-hidden="true">
                          {m.avatar}
                        </div>
                      ) : (
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
                          <Layers size={12} className="muted" aria-hidden="true" />
                        </div>
                      )}
                      <div>
                        <div className="table-row-link">
                          {m.kind === 'user' ? (
                            m.name
                          ) : (
                            <span className="mono">{m.name}</span>
                          )}
                        </div>
                        <div className="text-xs muted mono">{m.sub}</div>
                      </div>
                    </div>
                  </td>
                  <td>
                    {m.workspaceRole ? (
                      <RoleBadge role={m.workspaceRole} />
                    ) : (
                      <span className="text-xs muted">—</span>
                    )}
                  </td>
                  <td>
                    <select
                      className="select"
                      aria-label="KB role"
                      defaultValue={m.kbRole}
                      disabled={m.locked}
                      style={{ height: 26, fontSize: 12 }}
                    >
                      <option value="manage">Manager (full)</option>
                      <option value="edit">Editor (upload + tune)</option>
                      <option value="query">Query only</option>
                    </select>
                  </td>
                  <td className="col-mono text-xs">{m.grantedBy}</td>
                  <td className="col-num text-xs">{m.granted}</td>
                  <td className="col-shrink">
                    {m.locked ? (
                      <span className="badge badge-muted">
                        <Shield size={9} aria-hidden="true" /> AUTO
                      </span>
                    ) : (
                      <button
                        type="button"
                        className="btn btn-ghost btn-icon btn-xs"
                        aria-label="Row actions"
                      >
                        <MoreHorizontal size={13} aria-hidden="true" />
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <button
        type="button"
        className="btn btn-ghost btn-xs"
        style={{ marginTop: 12 }}
        onClick={() => router.push('/users')}
      >
        Manage all workspace members → /users
      </button>
    </div>
  );
}
