'use client';

/**
 * Dashboard (`/dashboard`) — the post-login home overview (architecture.md v6 §5.3, per ADR-0024 D4 + ADR-0030 absorbed scope).
 *
 * W18 F4 shipped the first cut (5 cards, backend liveness off the W1 `{status: "ok"}` payload).
 * W20 F2 rewrites it for the richer payload + 4-stat strip per ADR-0030 absorbed:
 *   - 4-stat strip       : Total KBs / Total Documents / Total Chunks / Total Storage MB
 *                          (aggregate off kbApi.list)
 *   - Knowledge bases    : top-5 KB list (off kbApi.list) + link → /kb
 *   - Recent queries     : empty-state CTA → /chat (Q6 real-query collection still Open)
 *   - Latest evaluation  : empty-state CTA → /eval (no cached-eval-run endpoint yet)
 *   - System health      : **per-component dots** (Azure Search / OpenAI / Cohere / Langfuse /
 *                          Postgres) off the W20 F2.1 extended `GET /health` payload — semantic
 *                          tokens drive the colour (success / muted / destructive / accent)
 *   - Quick actions      : New KB / Upload doc / Run eval / Open chat
 *
 * No new backend beyond F2.1's `/health` extension; Recent-queries + Latest-eval remain
 * empty-state CTAs per the W18 F4 acceptance (Q6 Open + no eval-cache endpoint).
 *
 * Renders inside <AppShell> (the sidebar shows "Dashboard" active). 100% design-token classes;
 * Zero hardcoded `oklch()` colour arbitrary-values across frontend/ (W15/W18/W20 F1 milestone preserved).
 */

import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import {
  Database,
  FileText,
  FlaskConical,
  HardDrive,
  Layers,
  MessageSquare,
  Plus,
  Upload,
  type LucideIcon,
} from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { apiClient } from '@/lib/api-client';
import { kbApi } from '@/lib/api/kb';

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

// Semantic-token dot colours per component status (no hardcoded oklch).
function statusDotClass(status: ComponentStatus): string {
  switch (status) {
    case 'ok':
      return 'bg-success';
    case 'not_configured':
      return 'bg-muted-foreground/40';
    case 'degraded':
      return 'bg-accent';
    case 'error':
      return 'bg-destructive';
  }
}

function statusLabel(status: ComponentStatus): string {
  switch (status) {
    case 'ok':
      return 'OK';
    case 'not_configured':
      return 'Not configured';
    case 'degraded':
      return 'Degraded';
    case 'error':
      return 'Error';
  }
}

// ---------------------------------------------------------------------------
// 4-stat strip
// ---------------------------------------------------------------------------

interface StatCardProps {
  label: string;
  value: string;
  icon: LucideIcon;
}

function StatCard({ label, value, icon: Icon }: StatCardProps) {
  return (
    <Card>
      <CardContent className="flex items-center gap-3 p-4">
        <Icon className="h-5 w-5 shrink-0 text-muted-foreground" aria-hidden="true" />
        <div className="min-w-0">
          <div className="truncate text-xs text-muted-foreground">{label}</div>
          <div className="truncate text-xl font-semibold tracking-tight">{value}</div>
        </div>
      </CardContent>
    </Card>
  );
}

function StatCardSkeleton() {
  return (
    <Card>
      <CardContent className="flex items-center gap-3 p-4">
        <Skeleton className="h-5 w-5 shrink-0" />
        <div className="min-w-0 space-y-1">
          <Skeleton className="h-3 w-20" />
          <Skeleton className="h-5 w-16" />
        </div>
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function DashboardPage() {
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
  const totalDocs = kbs.reduce((s, k) => s + k.total_documents, 0);
  const totalChunks = kbs.reduce((s, k) => s + k.total_chunks, 0);
  const totalMb = kbs.reduce((s, k) => s + k.storage_size_mb, 0);

  // Top-5 KBs by document count for the Knowledge bases card.
  const topKbs = [...kbs]
    .sort((a, b) => b.total_documents - a.total_documents)
    .slice(0, 5);

  // F1-pivot per CLAUDE.md §5.7 H7 (2026-05-18): page-level self-wrap per mockup
  // `ekp-page-dashboard.jsx:16-17` (`.content` + `.content-wide`). AppShell no longer
  // injects `.content` so /chat can stay full-bleed per its mockup. Inner W20 layout
  // (`mx-auto max-w-5xl space-y-6`) preserved until F3 dashboard rebuild.
  return (
    <div className="content"><div className="content-wide">
    <div className="mx-auto max-w-5xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Dashboard</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Overview of knowledge bases, queries, evaluations and system health.
        </p>
      </div>

      {/* 4-stat strip */}
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        {kbQuery.isPending ? (
          <>
            <StatCardSkeleton />
            <StatCardSkeleton />
            <StatCardSkeleton />
            <StatCardSkeleton />
          </>
        ) : (
          <>
            <StatCard
              label="Knowledge bases"
              value={kbs.length.toLocaleString()}
              icon={Database}
            />
            <StatCard
              label="Documents"
              value={totalDocs.toLocaleString()}
              icon={FileText}
            />
            <StatCard
              label="Chunks"
              value={totalChunks.toLocaleString()}
              icon={Layers}
            />
            <StatCard
              label="Storage"
              value={`${totalMb.toFixed(1)} MB`}
              icon={HardDrive}
            />
          </>
        )}
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {/* Knowledge bases — top 5 list */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle
              role="heading"
              aria-level={2}
              className="text-sm font-medium text-muted-foreground"
            >
              Knowledge bases
            </CardTitle>
          </CardHeader>
          <CardContent>
            {kbQuery.isPending ? (
              <Skeleton className="h-24 w-full" />
            ) : kbQuery.isError ? (
              <p className="text-sm text-destructive">
                Couldn&apos;t load knowledge bases.
              </p>
            ) : kbs.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                No knowledge bases yet — create your first to get started.
              </p>
            ) : (
              <ul className="space-y-1.5 text-sm">
                {topKbs.map((kb) => (
                  <li key={kb.kb_id} className="flex items-center justify-between gap-2">
                    <Link
                      href={`/kb/${kb.kb_id}`}
                      className="min-w-0 truncate text-foreground hover:underline"
                    >
                      {kb.name}
                    </Link>
                    <span className="shrink-0 text-xs text-muted-foreground">
                      {kb.total_documents} docs
                    </span>
                  </li>
                ))}
              </ul>
            )}
            <Button asChild variant="link" size="sm" className="mt-2 h-auto p-0">
              <Link href="/kb">View all knowledge bases →</Link>
            </Button>
          </CardContent>
        </Card>

        {/* Recent queries — Q6 still Open → empty-state CTA */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle
              role="heading"
              aria-level={2}
              className="text-sm font-medium text-muted-foreground"
            >
              Recent queries
            </CardTitle>
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

        {/* Latest evaluation — no cached-run endpoint → empty-state CTA */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle
              role="heading"
              aria-level={2}
              className="text-sm font-medium text-muted-foreground"
            >
              Latest evaluation
            </CardTitle>
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

        {/* System health — per-component dots off the W20 F2.1 extended /health payload */}
        <Card className="sm:col-span-2">
          <CardHeader className="pb-2">
            <CardTitle
              role="heading"
              aria-level={2}
              className="text-sm font-medium text-muted-foreground"
            >
              System health
            </CardTitle>
          </CardHeader>
          <CardContent>
            {healthQuery.isPending ? (
              <div className="space-y-2">
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-3/4" />
              </div>
            ) : healthQuery.isError ? (
              <div className="flex items-center gap-2 text-sm">
                <span
                  className="h-2 w-2 rounded-full bg-destructive"
                  aria-hidden="true"
                />
                <span>Backend unreachable</span>
              </div>
            ) : (
              <ul
                className="grid grid-cols-1 gap-1.5 text-sm sm:grid-cols-2"
                aria-label="Component connectivity"
              >
                {COMPONENT_ORDER.map((key) => {
                  // W22 F1-pivot defensive read — backend /health response can be
                  // shape `{status, components: {...}}` (W20 F2.1 build) or thin
                  // `{status: "ok"}` (pre-W20 build / old running process). Don't
                  // crash AppShell verification when components field absent.
                  const comp = healthQuery.data?.components?.[key];
                  if (!comp) return null;
                  const label = COMPONENT_LABELS[key] ?? key;
                  return (
                    <li
                      key={key}
                      className="flex items-center gap-2"
                      title={comp.detail ?? undefined}
                    >
                      <span
                        className={`h-2 w-2 shrink-0 rounded-full ${statusDotClass(comp.status)}`}
                        aria-hidden="true"
                      />
                      <span className="min-w-0 truncate text-foreground">{label}</span>
                      <span className="ml-auto shrink-0 text-xs text-muted-foreground">
                        {statusLabel(comp.status)}
                      </span>
                    </li>
                  );
                })}
              </ul>
            )}
          </CardContent>
        </Card>

        {/* Quick actions */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle
              role="heading"
              aria-level={2}
              className="text-sm font-medium text-muted-foreground"
            >
              Quick actions
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-2">
              <QuickAction href="/kb/new" icon={Plus} label="New KB" />
              <QuickAction href="/kb" icon={Upload} label="Upload doc" />
              <QuickAction href="/eval" icon={FlaskConical} label="Run eval" />
              <QuickAction href="/chat" icon={MessageSquare} label="Open chat" />
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
    </div></div>
  );
}

function QuickAction({
  href,
  icon: Icon,
  label,
}: {
  href: string;
  icon: LucideIcon;
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
