'use client';

/**
 * C09/C10 app-shell user menu — W12 D4 build with shadcn DropdownMenu;
 * W18 F5: + a "Settings" link → /settings (per ADR-0024 §5.0 top-bar user menu);
 * W22 F1: trigger button rewritten per mockup `ekp-shell.jsx` `UserMenu` —
 *   avatar (initials, small) + username text + chev-down (replaces W18 baseline
 *   icon-only avatar). Dropdown internals preserved per Karpathy §1.3 surgical;
 *   richer item set (Profile / API keys / Identity & Auth) is W22 F8 settings
 *   cluster scope, not F1.
 *
 * Wraps existing `useAuthStore` + `useCurrentUser` hooks.
 */

import { ChevronDown, LogOut, Settings } from 'lucide-react';
import Link from 'next/link';

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { useAuthStore, useCurrentUser } from '@/lib/providers/auth-provider';
import { cn } from '@/lib/utils';

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
          className={cn(
            'flex h-8 items-center gap-2 rounded-sm pl-1 pr-2 text-[13px] transition-colors hover:bg-muted',
          )}
        >
          <span
            aria-hidden="true"
            className="flex h-[22px] w-[22px] shrink-0 items-center justify-center rounded-full border border-border bg-muted font-mono text-[10px] font-semibold"
          >
            {initials || 'U'}
          </span>
          <span className="hidden truncate sm:inline-block">{displayName}</span>
          <ChevronDown className="h-3.5 w-3.5 shrink-0 text-muted-foreground" aria-hidden="true" />
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-56">
        <DropdownMenuLabel>
          <div className="flex flex-col">
            <span className="truncate text-sm font-medium">
              {user.preferredUsername}
            </span>
            {user.isMock ? (
              <span className="text-xs text-muted-foreground">[mock]</span>
            ) : null}
          </div>
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem asChild>
          <Link href="/settings">
            <Settings className="mr-2 h-4 w-4" />
            Settings
          </Link>
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem onSelect={() => void signOut()}>
          <LogOut className="mr-2 h-4 w-4" />
          Sign out
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
