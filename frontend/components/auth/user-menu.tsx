'use client';

/**
 * C09/C10 app-shell user menu — W22 F1-pivot direct-copy from mockup
 * `references/design-mockups/ekp-shell.jsx` UserMenu function (per
 * CLAUDE.md §5.7 H7 strict fidelity 2026-05-17 user directive — direct
 * copy mockup JSX + adapt for project architecture).
 *
 * Structure mirrors mockup `<PopMenu width=260>`:
 *   - Header: avatar (large) + display name + email + "Workspace Admin" badge
 *   - Body: 5 nav items (Profile / Settings / API keys & quotas / Identity & Auth)
 *           + `<div className="hr" />` divider + Sign out (destructive color)
 *   - Footer: "MSAL · httpOnly cookie · 7d TTL" muted-mono caption
 *
 * shadcn `<DropdownMenu>` Radix wrapper preserved for accessibility (keyboard
 * trap + focus return + portal positioning). Inner content uses mockup CSS
 * classes (`.avatar.avatar-lg` / `.badge.badge-accent` / `.nav-item` / `.hr`
 * / `.text-xs.muted` / `.mono`) — NO Tailwind utility classes.
 *
 * Wraps existing `useAuthStore` + `useCurrentUser` hooks for the real auth
 * data;routes Profile / API keys / Identity & Auth all link to /settings until
 * W22 F8 settings cluster wires the 6-tab Settings page per ADR-0026 Wave C2.
 */

import { ChevronDown, Key, LogOut, Settings as SettingsIcon, Shield, User as UserIcon } from 'lucide-react';
import Link from 'next/link';

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { RoleBadge } from '@/components/users/role-badge';
import { useRole } from '@/lib/hooks/use-role';
import { useAuthStore, useCurrentUser } from '@/lib/providers/auth-provider';

function getInitials(username: string): string {
  const localPart = username.split('@')[0] || username;
  const tokens = localPart.split(/[._-]/).filter(Boolean);
  return tokens
    .map((t) => t[0]?.toUpperCase() ?? '')
    .join('')
    .slice(0, 2);
}

export function UserMenu() {
  const user = useCurrentUser();
  const role = useRole();
  const signOut = useAuthStore((s) => s.signOut);

  if (!user) {
    return (
      <div className="text-xs text-muted-foreground">Signing in…</div>
    );
  }

  const initials = getInitials(user.preferredUsername);
  // Mockup TopBar shows the local-part of the email (e.g. "chris.lai") next to
  // the avatar — keeps the visual chrome tight at the 360w search constraint.
  const displayName = user.preferredUsername.split('@')[0] || user.preferredUsername;

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button
          type="button"
          aria-label="Open user menu"
          title="Account"
          className="btn btn-ghost btn-sm"
          style={{ paddingLeft: 4, paddingRight: 8, gap: 8 }}
        >
          <span className="avatar avatar-sm" aria-hidden="true">
            {initials || 'U'}
          </span>
          <span style={{ fontSize: 13 }}>{displayName}</span>
          <ChevronDown size={13} />
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent
        align="end"
        sideOffset={4}
        className="topbar-popmenu p-0"
        style={{ width: 260 }}
      >
        {/* Header — direct copy mockup ekp-shell.jsx UserMenu lines 202-211 */}
        <div
          style={{
            padding: '12px 14px',
            borderBottom: '1px solid oklch(var(--border))',
            display: 'flex',
            gap: 10,
            alignItems: 'center',
          }}
        >
          <div className="avatar avatar-lg">{initials || 'U'}</div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontSize: 13.5, fontWeight: 600 }}>{displayName}</div>
            <div
              className="text-xs muted"
              style={{
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
              }}
            >
              {user.preferredUsername}
              {user.isMock ? ' [mock]' : ''}
            </div>
            <div style={{ display: 'flex', gap: 4, marginTop: 4 }}>
              {/* W88 P0 F3 — real RBAC role chip (was hard-coded "Workspace
                  Admin"). RoleBadge = the mockup-grounded four-tier role visual
                  (ekp-page-users.jsx); hidden while /auth/me is in flight. */}
              {role && <RoleBadge role={role} />}
            </div>
          </div>
        </div>

        {/* Body — 4 nav items + divider + Sign out;direct copy mockup lines 212-227 */}
        <div style={{ padding: 6 }}>
          <Link href="/settings" className="nav-item" style={{ padding: '7px 10px' }}>
            <UserIcon className="icon" size={14} />
            <span>Profile</span>
          </Link>
          <Link href="/settings" className="nav-item" style={{ padding: '7px 10px' }}>
            <SettingsIcon className="icon" size={14} />
            <span>Settings</span>
          </Link>
          <Link href="/settings" className="nav-item" style={{ padding: '7px 10px' }}>
            <Key className="icon" size={14} />
            <span>API keys &amp; quotas</span>
          </Link>
          <Link href="/settings" className="nav-item" style={{ padding: '7px 10px' }}>
            <Shield className="icon" size={14} />
            <span>Identity &amp; Auth</span>
          </Link>
          <div className="hr" />
          <button
            type="button"
            onClick={() => void signOut()}
            className="nav-item"
            style={{
              padding: '7px 10px',
              color: 'oklch(var(--destructive))',
              width: '100%',
              textAlign: 'left',
            }}
          >
            <LogOut size={14} />
            <span>Sign out</span>
          </button>
        </div>

        {/* Footer — direct copy mockup lines 228-230 */}
        <div
          style={{
            padding: '8px 14px',
            borderTop: '1px solid oklch(var(--border))',
            background: 'oklch(var(--muted) / 0.3)',
          }}
        >
          <div className="text-xs muted mono">MSAL · httpOnly cookie · 7d TTL</div>
        </div>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
