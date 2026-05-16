'use client';

/**
 * V3 KB List (`/kb`) — per architecture.md v6 §5.4 view 3.
 *
 * W14 D2 F2 refactor: plain-table → card grid per ui-design-reference-v6.md
 * §2.3 wireframe + design ref §3 cross-view rules.
 *
 * W20 F4.3 polish (per ADR-0028 + architecture.md v6 §5.4 inline-tagged
 * amendment):
 *   - Status filter dropdown alongside the existing search + sort
 *     (indexed / empty / degraded / all)
 *   - Grid (default) ⇄ Table view toggle persisted to
 *     `localStorage['ekp-kb-list-view']`
 *   - The Card path renders unchanged (Karpathy §1.3 surgical — additive only);
 *     the Table path is a new render branch hitting the same `visible` list
 *
 * Layout reference Dify Image 4 dataset-grid pattern (no code copy per ADR-0010);
 * EKP design tokens only — 100% via tokens.ts, no hardcoded oklch.
 */

import { useQuery } from '@tanstack/react-query';
import {
  ArrowDownAZ,
  CheckCircle2,
  Clock,
  Database,
  FileText,
  FileWarning,
  LayoutGrid,
  List,
  Plus,
  Search,
} from 'lucide-react';
import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';

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
type StatusKind = 'indexed' | 'empty' | 'degraded';
type StatusFilter = StatusKind | 'all';
type ViewKind = 'grid' | 'table';

const SORT_LABEL: Record<SortKind, string> = {
  name: 'Name (A→Z)',
  last_indexed: 'Last indexed (recent)',
  documents: 'Documents (most)',
};

const STATUS_FILTER_LABEL: Record<StatusFilter, string> = {
  all: 'All statuses',
  indexed: 'Indexed only',
  empty: 'Empty only',
  degraded: 'Degraded only',
};

const VIEW_KEY = 'ekp-kb-list-view';

export default function KbListPage() {
  const query = useQuery<KbStatus[]>({
    queryKey: ['kb', 'list'],
    queryFn: kbApi.list,
  });

  const [search, setSearch] = useState('');
  const [sort, setSort] = useState<SortKind>('last_indexed');
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');
  const [view, setView] = useState<ViewKind>('grid');

  // SSR-stable hydration: read the persisted view after mount.
  useEffect(() => {
    const stored = window.localStorage.getItem(VIEW_KEY);
    if (stored === 'grid' || stored === 'table') setView(stored);
  }, []);

  function pickView(next: ViewKind) {
    setView(next);
    window.localStorage.setItem(VIEW_KEY, next);
  }

  const visible = useMemo(() => {
    const rows = query.data ?? [];
    const term = search.trim().toLowerCase();
    const filteredBySearch = term
      ? rows.filter((kb) =>
          [kb.name, kb.kb_id, kb.description]
            .filter(Boolean)
            .some((field) => field.toLowerCase().includes(term)),
        )
      : rows;
    const filteredByStatus =
      statusFilter === 'all'
        ? filteredBySearch
        : filteredBySearch.filter((kb) => deriveStatus(kb) === statusFilter);
    return [...filteredByStatus].sort(makeComparator(sort));
  }, [query.data, search, sort, statusFilter]);

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

      <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center">
        <div className="relative min-w-0 flex-1 sm:max-w-md">
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
        <Select value={statusFilter} onValueChange={(v) => setStatusFilter(v as StatusFilter)}>
          <SelectTrigger className="w-full sm:w-44">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            {(['all', 'indexed', 'empty', 'degraded'] as StatusFilter[]).map((kind) => (
              <SelectItem key={kind} value={kind}>
                {STATUS_FILTER_LABEL[kind]}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
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

        <div
          role="group"
          aria-label="View mode"
          className="flex shrink-0 rounded-md border border-border p-0.5"
        >
          <Button
            type="button"
            variant="ghost"
            size="sm"
            aria-pressed={view === 'grid'}
            aria-label="Grid view"
            onClick={() => pickView('grid')}
            className={cn(
              'h-7 w-7 p-0',
              view === 'grid' && 'bg-accent/15 text-accent',
            )}
          >
            <LayoutGrid className="h-4 w-4" />
          </Button>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            aria-pressed={view === 'table'}
            aria-label="Table view"
            onClick={() => pickView('table')}
            className={cn(
              'h-7 w-7 p-0',
              view === 'table' && 'bg-accent/15 text-accent',
            )}
          >
            <List className="h-4 w-4" />
          </Button>
        </div>

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
        view === 'grid' ? <KbGridSkeleton /> : <KbTableSkeleton />
      ) : visible.length === 0 ? (
        <KbEmpty hasSearch={search.trim().length > 0 || statusFilter !== 'all'} />
      ) : view === 'grid' ? (
        <ul className="grid gap-4 sm:grid-cols-2 md:grid-cols-3">
          {visible.map((kb) => (
            <li key={kb.kb_id}>
              <KbCard kb={kb} />
            </li>
          ))}
        </ul>
      ) : (
        <KbTable rows={visible} />
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
  return (a, b) => {
    const av = a.last_indexed_at ?? '';
    const bv = b.last_indexed_at ?? '';
    if (!av && !bv) return 0;
    if (!av) return 1;
    if (!bv) return -1;
    return bv.localeCompare(av);
  };
}

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

function KbTable({ rows }: { rows: KbStatus[] }) {
  return (
    <div className="overflow-x-auto rounded-md border border-border">
      <table className="w-full text-sm">
        <thead className="bg-muted/40 text-xs uppercase tracking-wide text-muted-foreground">
          <tr>
            <th scope="col" className="px-3 py-2 text-left font-medium">Name</th>
            <th scope="col" className="px-3 py-2 text-left font-medium">KB id</th>
            <th scope="col" className="px-3 py-2 text-left font-medium">Status</th>
            <th scope="col" className="px-3 py-2 text-right font-medium">Docs</th>
            <th scope="col" className="px-3 py-2 text-right font-medium">Chunks</th>
            <th scope="col" className="px-3 py-2 text-left font-medium">Last indexed</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((kb) => {
            const status = deriveStatus(kb);
            return (
              <tr
                key={kb.kb_id}
                className="border-t border-border transition-colors hover:bg-muted/40"
              >
                <td className="px-3 py-2">
                  <Link
                    href={`/kb/${kb.kb_id}`}
                    className="font-medium hover:text-accent hover:underline focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                  >
                    {kb.name || kb.kb_id}
                  </Link>
                  {kb.description && (
                    <div className="line-clamp-1 text-xs text-muted-foreground">
                      {kb.description}
                    </div>
                  )}
                </td>
                <td className="px-3 py-2 font-mono text-xs text-muted-foreground">
                  {kb.kb_id}
                </td>
                <td className="px-3 py-2">
                  <Badge
                    variant="outline"
                    className={cn('text-xs', STATUS_BADGE_CLASS[status])}
                  >
                    {STATUS_LABEL[status]}
                  </Badge>
                </td>
                <td className="px-3 py-2 text-right tabular-nums">
                  {(kb.total_documents ?? 0).toLocaleString()}
                </td>
                <td className="px-3 py-2 text-right tabular-nums">
                  {(kb.total_chunks ?? 0).toLocaleString()}
                </td>
                <td className="px-3 py-2 text-xs text-muted-foreground">
                  {kb.last_indexed_at?.slice(0, 10) ?? '—'}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
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

function KbTableSkeleton() {
  return (
    <div className="rounded-md border border-border p-3" aria-hidden="true">
      {Array.from({ length: 6 }).map((_, i) => (
        <Skeleton key={i} className="my-2 h-6 w-full" />
      ))}
    </div>
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
            Try a different search term, change the status filter, or clear it.
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
