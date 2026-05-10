'use client';

/**
 * V3 KB List (`/kb`) — per architecture.md v6 §5.4 view 3.
 *
 * W14 D2 F2 refactor — plain-table → card grid per ui-design-reference-v6.md
 * §2.3 wireframe + design ref §3 cross-view rules. Each Card surfaces kb_id /
 * name / description / doc_count / chunks_count / last_indexed_at / derived
 * status badge so admins can sweep operational state at a glance.
 *
 * Layout reference Dify Image 4 dataset-grid pattern (no code copy per ADR-0010);
 * EKP design tokens only.
 *
 * Search + sort are client-side over the in-memory list — Tier 1 cohort scale
 * (small KB count) doesn't justify backend pagination yet (W11 retro CO18 →
 * Beta hardening when persistent backing migrates to Postgres / Cosmos DB).
 */

import { useQuery } from '@tanstack/react-query';
import {
  ArrowDownAZ,
  CheckCircle2,
  Clock,
  Database,
  FileText,
  FileWarning,
  Plus,
  Search,
} from 'lucide-react';
import Link from 'next/link';
import { useMemo, useState } from 'react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Skeleton } from '@/components/ui/skeleton';
import { kbApi, type KbStatus } from '@/lib/api/kb';
import { cn } from '@/lib/utils';

type SortKind = 'name' | 'last_indexed' | 'documents';

const SORT_LABEL: Record<SortKind, string> = {
  name: 'Name (A→Z)',
  last_indexed: 'Last indexed (recent)',
  documents: 'Documents (most)',
};

export default function KbListPage() {
  const query = useQuery<KbStatus[]>({
    queryKey: ['kb', 'list'],
    queryFn: kbApi.list,
  });

  const [search, setSearch] = useState('');
  const [sort, setSort] = useState<SortKind>('last_indexed');

  const visible = useMemo(() => {
    const rows = query.data ?? [];
    const term = search.trim().toLowerCase();
    const filtered = term
      ? rows.filter((kb) =>
          [kb.name, kb.kb_id, kb.description]
            .filter(Boolean)
            .some((field) => field.toLowerCase().includes(term)),
        )
      : rows;
    return [...filtered].sort(makeComparator(sort));
  }, [query.data, search, sort]);

  return (
    <div className="space-y-6">
      <header className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Knowledge Bases</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Manage ingested manuals across all KBs.
          </p>
        </div>
        <Button asChild>
          <Link href="/kb/new">
            <Plus className="mr-2 h-4 w-4" />
            Create KB
          </Link>
        </Button>
      </header>

      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <div className="relative flex-1">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            type="search"
            placeholder="Search by name, id, description…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
            aria-label="Search KBs"
          />
        </div>
        <Select value={sort} onValueChange={(v) => setSort(v as SortKind)}>
          <SelectTrigger className="w-full sm:w-56">
            <ArrowDownAZ className="mr-2 h-4 w-4 text-muted-foreground" />
            <SelectValue placeholder="Sort by" />
          </SelectTrigger>
          <SelectContent>
            {(['last_indexed', 'name', 'documents'] as SortKind[]).map((kind) => (
              <SelectItem key={kind} value={kind}>
                {SORT_LABEL[kind]}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <span className="text-xs text-muted-foreground sm:ml-2">
          {query.isLoading
            ? '…'
            : `${visible.length} of ${query.data?.length ?? 0}`}
        </span>
      </div>

      {query.isError && (
        <div className="rounded-md border border-destructive bg-destructive/10 p-3 text-sm">
          Failed to load KBs:{' '}
          {String((query.error as Error)?.message ?? 'unknown')}
        </div>
      )}

      {query.isLoading ? (
        <KbGridSkeleton />
      ) : visible.length === 0 ? (
        <KbEmpty hasSearch={search.trim().length > 0} />
      ) : (
        <ul className="grid gap-4 sm:grid-cols-2 md:grid-cols-3">
          {visible.map((kb) => (
            <li key={kb.kb_id}>
              <KbCard kb={kb} />
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function makeComparator(sort: SortKind): (a: KbStatus, b: KbStatus) => number {
  if (sort === 'name') {
    return (a, b) => (a.name || a.kb_id).localeCompare(b.name || b.kb_id);
  }
  if (sort === 'documents') {
    return (a, b) => (b.total_documents ?? 0) - (a.total_documents ?? 0);
  }
  // last_indexed: recent first; null/empty pushed to end.
  return (a, b) => {
    const av = a.last_indexed_at ?? '';
    const bv = b.last_indexed_at ?? '';
    if (!av && !bv) return 0;
    if (!av) return 1;
    if (!bv) return -1;
    return bv.localeCompare(av);
  };
}

type StatusKind = 'indexed' | 'empty' | 'degraded';

function deriveStatus(kb: KbStatus): StatusKind {
  if ((kb.failed_documents?.length ?? 0) > 0) return 'degraded';
  if ((kb.total_documents ?? 0) === 0) return 'empty';
  return 'indexed';
}

const STATUS_BADGE_CLASS: Record<StatusKind, string> = {
  indexed: 'bg-success/15 text-success border-transparent',
  empty: 'bg-muted text-muted-foreground border-transparent',
  degraded: 'bg-warning/15 text-warning-foreground border-transparent',
};

const STATUS_LABEL: Record<StatusKind, string> = {
  indexed: 'Indexed',
  empty: 'Empty',
  degraded: 'Degraded',
};

const STATUS_ICON: Record<StatusKind, React.ReactNode> = {
  indexed: <CheckCircle2 className="mr-1 h-3 w-3" />,
  empty: <Database className="mr-1 h-3 w-3" />,
  degraded: <FileWarning className="mr-1 h-3 w-3" />,
};

function KbCard({ kb }: { kb: KbStatus }) {
  const status = deriveStatus(kb);
  const lastIndexed = kb.last_indexed_at?.slice(0, 10) ?? '—';
  return (
    <Link
      href={`/kb/${kb.kb_id}`}
      className="group block h-full focus:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
    >
      <Card className="h-full transition-colors group-hover:border-accent/60">
        <CardHeader className="space-y-2">
          <div className="flex items-start justify-between gap-3">
            <CardTitle className="line-clamp-1 text-base">
              {kb.name || kb.kb_id}
            </CardTitle>
            <Badge
              variant="outline"
              className={cn('shrink-0 text-xs', STATUS_BADGE_CLASS[status])}
            >
              {STATUS_ICON[status]}
              {STATUS_LABEL[status]}
            </Badge>
          </div>
          <CardDescription className="line-clamp-2 min-h-[2.5rem]">
            {kb.description || (
              <span className="italic text-muted-foreground/70">
                No description
              </span>
            )}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-center gap-3 text-xs text-muted-foreground">
            <span className="inline-flex items-center gap-1">
              <FileText className="h-3 w-3" />
              {(kb.total_documents ?? 0).toLocaleString()} doc
              {kb.total_documents === 1 ? '' : 's'}
            </span>
            <span className="inline-flex items-center gap-1">
              <Database className="h-3 w-3" />
              {(kb.total_chunks ?? 0).toLocaleString()} chunks
            </span>
          </div>
          <div className="flex items-center justify-between gap-2 text-xs text-muted-foreground">
            <span className="inline-flex items-center gap-1">
              <Clock className="h-3 w-3" />
              {lastIndexed}
            </span>
            <span className="font-mono text-[10px] text-muted-foreground/80">
              {kb.kb_id}
            </span>
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}

function KbGridSkeleton() {
  return (
    <ul className="grid gap-4 sm:grid-cols-2 md:grid-cols-3" aria-hidden="true">
      {Array.from({ length: 6 }).map((_, i) => (
        <li key={i}>
          <Card>
            <CardHeader className="space-y-3">
              <Skeleton className="h-5 w-3/4" />
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-2/3" />
            </CardHeader>
            <CardContent className="space-y-2">
              <Skeleton className="h-3 w-1/2" />
              <Skeleton className="h-3 w-1/3" />
            </CardContent>
          </Card>
        </li>
      ))}
    </ul>
  );
}

function KbEmpty({ hasSearch }: { hasSearch: boolean }) {
  if (hasSearch) {
    return (
      <div className="flex flex-col items-center gap-3 rounded-md border border-dashed border-border bg-muted/30 p-12 text-center">
        <Search className="h-10 w-10 text-muted-foreground" />
        <div>
          <p className="text-base font-medium">No matching KBs</p>
          <p className="mt-1 text-sm text-muted-foreground">
            Try a different search term or clear the filter.
          </p>
        </div>
      </div>
    );
  }
  return (
    <div className="flex flex-col items-center gap-3 rounded-md border border-dashed border-border bg-muted/30 p-12 text-center">
      <Database className="h-12 w-12 text-muted-foreground" />
      <div>
        <p className="text-base font-medium">No Knowledge Bases yet</p>
        <p className="mt-1 text-sm text-muted-foreground">
          Create your first KB to start ingesting Word, PDF, or PowerPoint manuals.
        </p>
      </div>
      <Button asChild>
        <Link href="/kb/new">
          <Plus className="mr-2 h-4 w-4" />
          Create KB
        </Link>
      </Button>
    </div>
  );
}
