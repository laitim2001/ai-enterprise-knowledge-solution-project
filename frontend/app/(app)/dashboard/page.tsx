'use client';

/**
 * Dashboard (`/dashboard`) — the post-login home overview (architecture.md v6 §5.3, per ADR-0024 D4).
 *
 * W18 F4 — real overview cards, all off existing endpoints (no new backend):
 *   - Knowledge bases : count + total docs/chunks/storage (off GET /kb via kbApi.list)
 *   - Recent queries  : no backend source yet (Q6 real-query collection open) → "ask" CTA → /chat
 *   - Latest evaluation: no cached eval-run source → "run eval" CTA → /eval
 *   - System health   : backend liveness off GET /health (per-component connectivity needs a
 *                       richer /health endpoint — a later-tier concern, not W18 scope)
 *   - Quick actions   : New KB / Upload doc / Run eval / Open chat
 *
 * Renders inside <AppShell> (the sidebar shows "Dashboard" active). 100% design-token classes.
 */

import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { FlaskConical, MessageSquare, Plus, Upload } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { apiClient } from '@/lib/api-client';
import { kbApi } from '@/lib/api/kb';

function plural(n: number, word: string): string {
  return `${n} ${word}${n === 1 ? '' : 's'}`;
}

export default function DashboardPage() {
  const kbQuery = useQuery({ queryKey: ['kb', 'list'], queryFn: () => kbApi.list() });
  const healthQuery = useQuery({
    queryKey: ['health'],
    queryFn: () => apiClient.get<{ status: string }>('/health'),
    retry: 1,
  });

  const kbs = kbQuery.data ?? [];
  const totalDocs = kbs.reduce((s, k) => s + k.total_documents, 0);
  const totalChunks = kbs.reduce((s, k) => s + k.total_chunks, 0);
  const totalMb = kbs.reduce((s, k) => s + k.storage_size_mb, 0);

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Dashboard</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Overview of knowledge bases, queries, evaluations and system health.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {/* Knowledge bases */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle role="heading" aria-level={2} className="text-sm font-medium text-muted-foreground">Knowledge bases</CardTitle>
          </CardHeader>
          <CardContent>
            {kbQuery.isPending ? (
              <Skeleton className="h-16 w-full" />
            ) : kbQuery.isError ? (
              <p className="text-sm text-destructive">Couldn&apos;t load knowledge bases.</p>
            ) : (
              <>
                <div className="text-3xl font-semibold">{kbs.length}</div>
                <div className="mt-1 text-xs text-muted-foreground">
                  {plural(totalDocs, 'document')} · {plural(totalChunks, 'chunk')} · {totalMb.toFixed(1)} MB
                </div>
                <Button asChild variant="link" size="sm" className="mt-2 h-auto p-0">
                  <Link href="/kb">View knowledge bases →</Link>
                </Button>
              </>
            )}
          </CardContent>
        </Card>

        {/* Recent queries — no backend source yet (Q6) */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle role="heading" aria-level={2} className="text-sm font-medium text-muted-foreground">Recent queries</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Query history isn&apos;t collected yet (Q6).
            </p>
            <Button asChild variant="link" size="sm" className="mt-2 h-auto p-0">
              <Link href="/chat">Ask a question →</Link>
            </Button>
          </CardContent>
        </Card>

        {/* Latest evaluation — no cached run source */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle role="heading" aria-level={2} className="text-sm font-medium text-muted-foreground">Latest evaluation</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              No eval run cached. Run RAGAs to see Recall@5 / Faithfulness / Correctness.
            </p>
            <Button asChild variant="link" size="sm" className="mt-2 h-auto p-0">
              <Link href="/eval">Open Eval Console →</Link>
            </Button>
          </CardContent>
        </Card>

        {/* System health */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle role="heading" aria-level={2} className="text-sm font-medium text-muted-foreground">System health</CardTitle>
          </CardHeader>
          <CardContent>
            {healthQuery.isPending ? (
              <Skeleton className="h-5 w-36" />
            ) : healthQuery.isError ? (
              <div className="flex items-center gap-2 text-sm">
                <span className="h-2 w-2 rounded-full bg-destructive" aria-hidden="true" />
                <span>Backend unreachable</span>
              </div>
            ) : (
              <div className="flex items-center gap-2 text-sm">
                <span className="h-2 w-2 rounded-full bg-success" aria-hidden="true" />
                <span>Backend operational</span>
              </div>
            )}
            <p className="mt-2 text-xs text-muted-foreground">
              Per-component connectivity (Azure Search / OpenAI / Cohere / Langfuse) — coming with a richer /health endpoint.
            </p>
          </CardContent>
        </Card>

        {/* Quick actions */}
        <Card className="sm:col-span-2">
          <CardHeader className="pb-2">
            <CardTitle role="heading" aria-level={2} className="text-sm font-medium text-muted-foreground">Quick actions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
              <QuickAction href="/kb/new" icon={Plus} label="New KB" />
              <QuickAction href="/kb" icon={Upload} label="Upload doc" />
              <QuickAction href="/eval" icon={FlaskConical} label="Run eval" />
              <QuickAction href="/chat" icon={MessageSquare} label="Open chat" />
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function QuickAction({
  href,
  icon: Icon,
  label,
}: {
  href: string;
  icon: typeof Plus;
  label: string;
}) {
  return (
    <Button asChild variant="outline" className="h-auto flex-col gap-1.5 py-3">
      <Link href={href}>
        <Icon className="h-4 w-4" aria-hidden="true" />
        <span className="text-xs">{label}</span>
      </Link>
    </Button>
  );
}
