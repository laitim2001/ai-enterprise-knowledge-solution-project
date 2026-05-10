/**
 * Dashboard (`/dashboard`) — the post-login home overview (architecture.md v6 §5.3, per ADR-0024).
 *
 * W18 F3 placeholder — the real overview cards (KB summary / recent queries / latest eval /
 * system health / quick actions, all off existing endpoints) land in W18 F4. This stub keeps
 * the AppShell app-name link + the sidebar "Dashboard" item from 404-ing in the meantime.
 */

import Link from 'next/link';

export default function DashboardPage() {
  return (
    <div className="mx-auto max-w-5xl space-y-4">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Dashboard</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Overview of knowledge bases, recent queries, eval status and system health.
        </p>
      </div>
      <div className="rounded-md border border-dashed border-border p-6 text-sm text-muted-foreground">
        Overview cards land in W18 F4. For now, jump to{' '}
        <Link href="/chat" className="font-medium text-foreground underline-offset-4 hover:underline">
          Chat
        </Link>
        ,{' '}
        <Link href="/kb" className="font-medium text-foreground underline-offset-4 hover:underline">
          Knowledge Bases
        </Link>
        ,{' '}
        <Link href="/eval" className="font-medium text-foreground underline-offset-4 hover:underline">
          Eval Console
        </Link>{' '}
        or{' '}
        <Link href="/traces" className="font-medium text-foreground underline-offset-4 hover:underline">
          Traces
        </Link>
        .
      </div>
    </div>
  );
}
