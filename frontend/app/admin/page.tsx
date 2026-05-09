'use client';

/**
 * V2 Admin Dashboard (`/admin`) — per architecture.md v6 §5.3 view 2.
 *
 * W14 D1 F1 refactor — 4-card stats row + failed documents section + 3-button
 * quick actions row per ui-design-reference-v6.md §2.2 wireframe + design ref
 * §3 cross-view consistency rules. Layout reference Dify Image 4 dashboard
 * pattern (no code copy per ADR-0010).
 *
 * Data flows through TanStack Query against `kbApi.list` so KB stats + failed
 * documents derive from a single GET; system status badge reflects the same
 * query state (success → green / loading → muted / error → destructive). No
 * new backend endpoints required for the V2 refactor.
 */

import { useQuery } from '@tanstack/react-query';
import { CheckCircle2, FileWarning, FlaskConical, MessageSquare, Plus } from 'lucide-react';
import Link from 'next/link';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { kbApi, type FailureRecord, type KbStatus } from '@/lib/api/kb';
import { cn } from '@/lib/utils';

interface FailureRow extends FailureRecord {
  kb_id: string;
}

export default function AdminOverviewPage() {
  const query = useQuery<KbStatus[]>({
    queryKey: ['kb', 'list'],
    queryFn: kbApi.list,
  });

  const totalKbs = query.data?.length ?? 0;
  const totalDocs =
    query.data?.reduce((acc, kb) => acc + (kb.total_documents ?? 0), 0) ?? 0;
  const totalChunks =
    query.data?.reduce((acc, kb) => acc + (kb.total_chunks ?? 0), 0) ?? 0;

  const failures: FailureRow[] = (query.data ?? []).flatMap((kb) =>
    (kb.failed_documents ?? []).map((failure) => ({
      ...failure,
      kb_id: kb.kb_id,
    })),
  );

  const status = computeStatus(query.isLoading, query.isError, failures.length);

  return (
    <div className="space-y-8">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Overview</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Aggregate stats across all Knowledge Bases.
        </p>
      </header>

      {query.isError && (
        <div className="rounded-md border border-destructive bg-destructive/10 p-3 text-sm">
          Failed to load — backend unreachable. R8 reactivation? Disconnect VPN +
          retry. Error: {String((query.error as Error)?.message ?? 'unknown')}
        </div>
      )}

      <section>
        <div className="grid gap-4 sm:grid-cols-2 md:grid-cols-4">
          <StatCard
            label="Knowledge Bases"
            value={totalKbs}
            loading={query.isLoading}
          />
          <StatCard
            label="Documents"
            value={totalDocs}
            loading={query.isLoading}
          />
          <StatCard
            label="Chunks"
            value={totalChunks}
            loading={query.isLoading}
          />
          <SystemStatusCard status={status} failureCount={failures.length} />
        </div>
      </section>

      <section>
        <header className="mb-3 flex items-baseline justify-between">
          <h2 className="text-lg font-semibold tracking-tight">
            Failed ingestion
          </h2>
          <span className="text-xs text-muted-foreground">
            {failures.length === 0 ? 'No failures' : `${failures.length} failed document${failures.length === 1 ? '' : 's'}`}
          </span>
        </header>
        {query.isLoading ? (
          <FailuresSkeleton />
        ) : failures.length === 0 ? (
          <FailuresEmpty />
        ) : (
          <FailuresTable rows={failures} />
        )}
      </section>

      <section>
        <h2 className="mb-3 text-lg font-semibold tracking-tight">Quick actions</h2>
        <div className="grid gap-3 sm:grid-cols-3">
          <ActionButton
            href="/admin/kb/new"
            icon={<Plus className="h-4 w-4" />}
            label="Create KB"
            description="Upload + ingest a new manual"
          />
          <ActionButton
            href="/chat"
            icon={<MessageSquare className="h-4 w-4" />}
            label="Test query"
            description="Ask a question against an indexed KB"
          />
          <ActionButton
            href="/eval"
            icon={<FlaskConical className="h-4 w-4" />}
            label="View eval"
            description="Reranker shootout + RAGAs metrics"
          />
        </div>
      </section>
    </div>
  );
}

type StatusKind = 'ok' | 'loading' | 'warn' | 'error';

function computeStatus(
  isLoading: boolean,
  isError: boolean,
  failureCount: number,
): StatusKind {
  if (isLoading) return 'loading';
  if (isError) return 'error';
  if (failureCount > 0) return 'warn';
  return 'ok';
}

function StatCard({
  label,
  value,
  loading,
}: {
  label: string;
  value: number;
  loading: boolean;
}) {
  return (
    <Card>
      <CardHeader className="space-y-1 pb-2">
        <CardDescription className="text-xs uppercase tracking-wide">
          {label}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-semibold">
          {loading ? '—' : value.toLocaleString()}
        </div>
      </CardContent>
    </Card>
  );
}

const STATUS_LABEL: Record<StatusKind, string> = {
  ok: 'Operational',
  loading: 'Loading…',
  warn: 'Degraded',
  error: 'Backend unreachable',
};

const STATUS_BADGE_CLASS: Record<StatusKind, string> = {
  ok: 'bg-success/15 text-success border-transparent',
  loading: 'bg-muted text-muted-foreground border-transparent',
  warn: 'bg-warning/15 text-warning-foreground border-transparent',
  error: 'bg-destructive/15 text-destructive border-transparent',
};

function SystemStatusCard({
  status,
  failureCount,
}: {
  status: StatusKind;
  failureCount: number;
}) {
  const subtext =
    status === 'warn'
      ? `${failureCount} failed ingestion${failureCount === 1 ? '' : 's'}`
      : status === 'error'
        ? 'Retry after VPN check'
        : status === 'loading'
          ? 'Querying backend…'
          : 'All systems green';
  return (
    <Card>
      <CardHeader className="space-y-1 pb-2">
        <CardDescription className="text-xs uppercase tracking-wide">
          System status
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-2">
        <Badge className={cn('text-xs', STATUS_BADGE_CLASS[status])} variant="outline">
          {STATUS_LABEL[status]}
        </Badge>
        <p className="text-xs text-muted-foreground">{subtext}</p>
      </CardContent>
    </Card>
  );
}

function FailuresEmpty() {
  return (
    <div className="flex flex-col items-center gap-2 rounded-md border border-dashed border-border bg-muted/30 p-8 text-center">
      <CheckCircle2 className="h-8 w-8 text-success" />
      <p className="text-sm font-medium">No failed ingestion</p>
      <p className="text-xs text-muted-foreground">
        Last ingestion runs across all KBs landed clean.
      </p>
    </div>
  );
}

function FailuresSkeleton() {
  return (
    <div className="space-y-2">
      {Array.from({ length: 3 }).map((_, i) => (
        <div
          key={i}
          className="h-12 animate-pulse rounded-md border border-border bg-muted/30"
        />
      ))}
    </div>
  );
}

function FailuresTable({ rows }: { rows: FailureRow[] }) {
  return (
    <div className="overflow-hidden rounded-md border border-border">
      <table className="w-full text-sm">
        <thead className="bg-muted/50 text-xs uppercase tracking-wide text-muted-foreground">
          <tr>
            <th className="px-3 py-2 text-left font-medium">KB</th>
            <th className="px-3 py-2 text-left font-medium">Doc id</th>
            <th className="px-3 py-2 text-left font-medium">Stage</th>
            <th className="px-3 py-2 text-left font-medium">Error</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {rows.slice(0, 10).map((row, idx) => (
            <tr key={`${row.kb_id}-${row.doc_id}-${idx}`} className="bg-background">
              <td className="px-3 py-2 font-mono text-xs">{row.kb_id}</td>
              <td className="px-3 py-2 font-mono text-xs">{row.doc_id}</td>
              <td className="px-3 py-2">
                <Badge variant="outline" className="text-xs">
                  <FileWarning className="mr-1 h-3 w-3" />
                  {row.stage}
                </Badge>
              </td>
              <td className="px-3 py-2 text-xs text-muted-foreground">
                {row.error}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {rows.length > 10 && (
        <div className="border-t border-border bg-muted/30 px-3 py-2 text-xs text-muted-foreground">
          Showing first 10 of {rows.length} failures.
        </div>
      )}
    </div>
  );
}

function ActionButton({
  href,
  icon,
  label,
  description,
}: {
  href: string;
  icon: React.ReactNode;
  label: string;
  description: string;
}) {
  return (
    <Button
      asChild
      variant="outline"
      className="h-auto justify-start gap-3 p-4 text-left"
    >
      <Link href={href}>
        <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-accent/10 text-accent">
          {icon}
        </span>
        <span className="flex flex-col items-start gap-0.5">
          <span className="text-sm font-medium">{label}</span>
          <span className="text-xs font-normal text-muted-foreground">
            {description}
          </span>
        </span>
      </Link>
    </Button>
  );
}
