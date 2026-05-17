'use client';

/**
 * Settings (`/settings`) — small profile + preferences view (W18 F5, per ADR-0024 D5).
 *
 * Tier 1 scope = exactly: profile display (the AuthenticatedUser claims — preferredUsername /
 * oid / tid + a mock badge in dev), a theme preference toggle (reuses <ThemeToggle> — Light /
 * Dark / System via next-themes), and a sign-out button (reuses the same useAuthStore.signOut
 * the <UserMenu> uses). Deeper settings (notifications / API tokens / org) are a later-tier
 * concern. Reached from the <UserMenu> "Settings" item. Renders inside <AppShell>.
 */

import { LogOut } from 'lucide-react';

import { ThemeToggle } from '@/components/nav/theme-toggle';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useAuthStore, useCurrentUser } from '@/lib/providers/auth-provider';

export default function SettingsPage() {
  const user = useCurrentUser();
  const signOut = useAuthStore((s) => s.signOut);

  // F1-pivot per CLAUDE.md §5.7 H7 (2026-05-18): page-level self-wrap per mockup
  // `ekp-page-settings-tabs.jsx:19-20` (`.content` + `.content-narrow`). Inner preserved
  // until F8 settings rebuild (Wave C2 6-tab scope per ADR-0026).
  return (
    <div className="content"><div className="content-narrow">
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Settings</h1>
        <p className="mt-1 text-sm text-muted-foreground">Your profile and preferences.</p>
      </div>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle role="heading" aria-level={2} className="text-base">Profile</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          {user ? (
            <>
              <ProfileRow label="Username" value={user.preferredUsername} mono />
              <ProfileRow label="User ID (oid)" value={user.oid} mono />
              <ProfileRow label="Tenant (tid)" value={user.tid} mono />
              {user.isMock && (
                <div className="pt-1">
                  <Badge variant="outline">mock auth — dev mode</Badge>
                </div>
              )}
            </>
          ) : (
            <p className="text-muted-foreground">Signing in…</p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle role="heading" aria-level={2} className="text-base">Preferences</CardTitle>
        </CardHeader>
        <CardContent className="flex items-center justify-between">
          <div>
            <div className="text-sm font-medium">Theme</div>
            <div className="text-xs text-muted-foreground">Light / Dark / System</div>
          </div>
          <ThemeToggle />
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle role="heading" aria-level={2} className="text-base">Session</CardTitle>
        </CardHeader>
        <CardContent>
          <Button variant="outline" onClick={() => void signOut()}>
            <LogOut className="mr-2 h-4 w-4" aria-hidden="true" />
            Sign out
          </Button>
        </CardContent>
      </Card>
    </div>
    </div></div>
  );
}

function ProfileRow({
  label,
  value,
  mono,
}: {
  label: string;
  value: string;
  mono?: boolean;
}) {
  return (
    <div className="flex items-center justify-between gap-4 border-b border-border py-1.5 last:border-0">
      <span className="shrink-0 text-muted-foreground">{label}</span>
      <span className={mono ? 'truncate font-mono text-xs' : 'truncate'} title={value}>
        {value}
      </span>
    </div>
  );
}
