'use client';

/**
 * V4 KB Detail (`/kb/[id]`) — per architecture.md v6 §5.5 view 4.
 *
 * W14 D3 F3 refactor — 5-tab nav (Documents / Chunks / Pipeline / Retrieval
 * Testing / Settings) per ui-design-reference-v6.md §2.4 wireframe. Tab state
 * lives in Next.js searchParams (`?tab=documents`) so URLs are bookmark-friendly.
 *
 * Plan §7 changelog (D3) deviations:
 * - F3.2 Documents tab: (W14 D3 — backend stub) → W17 F4.1: now wired to the
 *   real GET /kb/{id}/documents (W16 F5.1.1 / CO_F3a — Azure AI Search chunk
 *   aggregation by doc_id); renders a doc table; empty index → Upload prompt.
 * - F3.3 Chunks tab: CH-002 F7 (2026-05-12) — wired to the real
 *   GET /kb/{id}/documents/{doc_id}/chunks (W16 F5.1.2); doc picker (from the
 *   doc listing, honours ?doc=<doc_id>) + ChunkSummary table (index / title /
 *   section path / flags / chunk_id). Was a 501-stub placeholder. Chunk body
 *   text is not bulk-listed (use Retrieval Testing / /query for that).
 * - F3.4 Pipeline tab: read-only config visualization Tier 1 (no PATCH inline).
 * - F3.6 Settings: CH-002 F10 (2026-05-12) — name + description are now
 *   editable, saved via PATCH /kb/{id} (W16 F5.2 / CO_F3b — partial update);
 *   KbConfig settings stay in PATCH /kb/{id}/settings. Was display-only.
 * - F3.8 Stepper rule-of-3 NOT triggered: Pipeline tab read-only display, not
 *   wizard state machine; inline retention preserved per W13 D4 decision.
 *
 * Layout reference Dify Image 1+2+4+5+6 (no code copy per ADR-0010).
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  AlertTriangle,
  Archive,
  ArrowLeft,
  Database,
  FileText,
  FlaskConical,
  Image as ImageIcon,
  Loader2,
  Lock,
  Scissors,
  Search,
  Settings as SettingsIcon,
  SlidersHorizontal,
  Sparkles,
  Upload,
} from 'lucide-react';
import Link from 'next/link';
import { useParams, useRouter, useSearchParams } from 'next/navigation';
import {
  useEffect,
  useRef,
  useState,
  type FormEvent,
} from 'react';
import { toast } from 'sonner';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { DisabledAffordance } from '@/components/ui/disabled-affordance';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Slider } from '@/components/ui/slider';
import { Switch } from '@/components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ApiError } from '@/lib/api-client';
import {
  documentsApi,
  type ChunkSummary,
  type DocumentSummary,
} from '@/lib/api/documents';
import {
  kbApi,
  type FailureRecord,
  type KbConfig,
  type KbStatus,
} from '@/lib/api/kb';
import { streamQuery, type Citation, type QueryRequest } from '@/lib/api/query';
import {
  retrievalTestApi,
  type RetrievalMode,
  type RetrievalTestResult,
} from '@/lib/api/retrieval-test';

// W20 F5.4 — 7-tab refactor per ADR-0025 (`-Access` Wave A scope; Access tab
// is rendered as a disabled affordance, not in VALID_TABS routing so it can't
// be ?tab=access-targeted).
const VALID_TABS = [
  'documents',
  'chunks',
  'images',
  'chunking-lab',
  'pipeline',
  'retrieval',
  'settings',
] as const;
type TabKey = (typeof VALID_TABS)[number];

const TAB_LABEL: Record<TabKey, string> = {
  documents: 'Documents',
  chunks: 'Chunks',
  images: 'Images',
  'chunking-lab': 'Chunking Lab',
  pipeline: 'Pipeline',
  retrieval: 'Retrieval Testing',
  settings: 'Settings',
};

export default function KbDetailPage() {
  const params = useParams<{ id: string }>();
  const kbId = params.id;
  const router = useRouter();
  const searchParams = useSearchParams();

  const tabParam = searchParams.get('tab');
  const activeTab: TabKey = VALID_TABS.includes(tabParam as TabKey)
    ? (tabParam as TabKey)
    : 'documents';

  const query = useQuery<KbStatus>({
    queryKey: ['kb', kbId],
    queryFn: () => kbApi.get(kbId),
    enabled: !!kbId,
  });

  function handleTabChange(next: string) {
    const params = new URLSearchParams(searchParams.toString());
    params.set('tab', next);
    router.push(`/kb/${kbId}?${params.toString()}`, { scroll: false });
  }

  if (query.isLoading) {
    return (
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Loader2 className="h-4 w-4 animate-spin" />
        Loading KB…
      </div>
    );
  }
  if (query.isError) {
    return (
      <div className="rounded-md border border-destructive bg-destructive/10 p-3 text-sm">
        Failed to load KB {kbId}:{' '}
        {String((query.error as Error)?.message ?? 'unknown')}
      </div>
    );
  }
  if (!query.data) return null;

  const kb = query.data;

  return (
    <div className="space-y-6">
      <div>
        <Link
          href="/kb"
          className="inline-flex items-center gap-1 text-xs text-muted-foreground transition-colors hover:text-foreground"
        >
          <ArrowLeft className="h-3 w-3" />
          Back to KBs
        </Link>
      </div>

      <header className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="space-y-1">
          <h1 className="text-2xl font-semibold tracking-tight">
            {kb.name || kb.kb_id}
          </h1>
          <p className="font-mono text-xs text-muted-foreground">{kb.kb_id}</p>
          {kb.description && (
            <p className="max-w-2xl text-sm text-muted-foreground">
              {kb.description}
            </p>
          )}
        </div>
        <Button asChild>
          <Link href={`/kb/${kbId}/upload`}>
            <Upload className="mr-2 h-4 w-4" />
            Upload Document
          </Link>
        </Button>
      </header>

      <Tabs value={activeTab} onValueChange={handleTabChange} className="w-full">
        <div className="overflow-x-auto">
          <TabsList>
            <TabsTrigger value="documents">
              <FileText className="mr-1.5 h-3.5 w-3.5" />
              {TAB_LABEL.documents}
            </TabsTrigger>
            <TabsTrigger value="chunks">
              <Database className="mr-1.5 h-3.5 w-3.5" />
              {TAB_LABEL.chunks}
            </TabsTrigger>
            <TabsTrigger value="images">
              <ImageIcon className="mr-1.5 h-3.5 w-3.5" />
              {TAB_LABEL.images}
            </TabsTrigger>
            <TabsTrigger value="chunking-lab">
              <Scissors className="mr-1.5 h-3.5 w-3.5" />
              {TAB_LABEL['chunking-lab']}
            </TabsTrigger>
            <TabsTrigger value="pipeline">
              <SlidersHorizontal className="mr-1.5 h-3.5 w-3.5" />
              {TAB_LABEL.pipeline}
            </TabsTrigger>
            <TabsTrigger value="retrieval">
              <FlaskConical className="mr-1.5 h-3.5 w-3.5" />
              {TAB_LABEL.retrieval}
            </TabsTrigger>
            <TabsTrigger value="settings">
              <SettingsIcon className="mr-1.5 h-3.5 w-3.5" />
              {TAB_LABEL.settings}
            </TabsTrigger>
            {/* W20 F5.8 — Access tab disabled affordance (Tier 1.5;Wave C1
                activates per ADR-0027 Option A RBAC backend). Render the tab
                visibly but block ?tab=access routing + click via TabsTrigger
                disabled + wrap in <DisabledAffordance>. */}
            <DisabledAffordance
              variant="p1-strict"
              reason="RBAC pending Wave C1 per ADR-0027 Option A backend"
              tier2Trigger="RBAC + audit log + group membership"
              className="inline-flex"
            >
              <TabsTrigger value="access" disabled aria-disabled="true">
                <Lock className="mr-1.5 h-3.5 w-3.5" />
                Access
              </TabsTrigger>
            </DisabledAffordance>
          </TabsList>
        </div>

        <TabsContent value="documents" className="mt-6">
          <DocumentsTab kb={kb} />
        </TabsContent>
        <TabsContent value="chunks" className="mt-6">
          <ChunksTab kb={kb} />
        </TabsContent>
        <TabsContent value="images" className="mt-6">
          <ImagesTab kb={kb} />
        </TabsContent>
        <TabsContent value="chunking-lab" className="mt-6">
          <ChunkingLabTab kb={kb} />
        </TabsContent>
        <TabsContent value="pipeline" className="mt-6">
          <PipelineTab kb={kb} />
        </TabsContent>
        <TabsContent value="retrieval" className="mt-6">
          <RetrievalTab kb={kb} />
        </TabsContent>
        <TabsContent value="settings" className="mt-6">
          <SettingsTab kb={kb} />
        </TabsContent>
      </Tabs>
    </div>
  );
}

// --- Documents tab -----------------------------------------------------------

function DocumentsTab({ kb }: { kb: KbStatus }) {
  // W17 F4.1 — wire the real GET /kb/{id}/documents (backend impl per W16 F5.1.1
  // CO_F3a: Azure AI Search chunk aggregation by doc_id). Empty index → empty
  // list (kb exists but no chunks ingested yet) → show the upload prompt.
  const docs = useQuery<DocumentSummary[]>({
    queryKey: ['kb', kb.kb_id, 'documents'],
    queryFn: () => documentsApi.list(kb.kb_id),
  });

  return (
    <div className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-3">
        <StatCard label="Total documents" value={kb.total_documents} />
        <StatCard label="Total chunks" value={kb.total_chunks} />
        <StatCard
          label="Storage"
          value={`${kb.storage_size_mb.toFixed(1)} MB`}
        />
      </div>

      {kb.failed_documents.length > 0 && (
        <FailuresSection rows={kb.failed_documents} />
      )}

      <section className="space-y-3">
        <header className="flex items-baseline justify-between">
          <h2 className="text-base font-semibold tracking-tight">Documents</h2>
          <span className="text-xs text-muted-foreground">
            {docs.isLoading
              ? 'Loading…'
              : docs.isError
                ? '—'
                : `${docs.data?.length ?? 0} document${(docs.data?.length ?? 0) === 1 ? '' : 's'} indexed`}
          </span>
        </header>

        {docs.isLoading ? (
          <DocumentsSkeleton />
        ) : docs.isError ? (
          <div className="rounded-md border border-destructive bg-destructive/10 p-3 text-sm">
            Failed to load documents — backend unreachable or Azure AI Search not
            configured. Error:{' '}
            {String((docs.error as Error)?.message ?? 'unknown')}
          </div>
        ) : (docs.data?.length ?? 0) === 0 ? (
          <div className="rounded-md border border-dashed border-border bg-muted/30 p-6 text-center">
            <Upload className="mx-auto h-8 w-8 text-muted-foreground" />
            <p className="mt-3 text-sm font-medium">No documents yet</p>
            <p className="mt-1 text-xs text-muted-foreground">
              Word, PDF, or PowerPoint — ingestion pipeline parses + chunks + embeds
            </p>
            <Button asChild className="mt-4">
              <Link href={`/kb/${kb.kb_id}/upload`}>
                <Upload className="mr-2 h-4 w-4" />
                Upload Document
              </Link>
            </Button>
          </div>
        ) : (
          <DocumentsTable rows={docs.data ?? []} />
        )}
      </section>
    </div>
  );
}

function DocumentsSkeleton() {
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

function DocumentsTable({ rows }: { rows: DocumentSummary[] }) {
  return (
    <div className="overflow-hidden rounded-md border border-border">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-muted/50 text-xs uppercase tracking-wide text-muted-foreground">
            <tr>
              <th scope="col" className="px-3 py-2 text-left font-medium">Title</th>
              <th scope="col" className="px-3 py-2 text-left font-medium">Format</th>
              <th scope="col" className="px-3 py-2 text-right font-medium">Chunks</th>
              <th scope="col" className="px-3 py-2 text-left font-medium">Last indexed</th>
              <th scope="col" className="px-3 py-2 text-left font-medium">Doc id</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {rows.map((doc) => (
              <tr key={doc.doc_id} className="bg-background">
                <td className="px-3 py-2">
                  <span className="font-medium">{doc.doc_title || doc.doc_id}</span>
                  {doc.tags.length > 0 && (
                    <span className="ml-2 inline-flex gap-1">
                      {doc.tags.slice(0, 3).map((t) => (
                        <Badge key={t} variant="outline" className="text-[10px]">
                          {t}
                        </Badge>
                      ))}
                    </span>
                  )}
                </td>
                <td className="px-3 py-2">
                  <Badge variant="outline" className="text-xs uppercase">
                    {doc.doc_format || '—'}
                  </Badge>
                </td>
                <td className="px-3 py-2 text-right tabular-nums">
                  {doc.total_chunks.toLocaleString()}
                </td>
                <td className="px-3 py-2 text-xs text-muted-foreground">
                  {doc.last_indexed_at ? doc.last_indexed_at.slice(0, 10) : '—'}
                </td>
                <td className="px-3 py-2 font-mono text-xs text-muted-foreground">
                  {doc.doc_id}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function FailuresSection({ rows }: { rows: FailureRecord[] }) {
  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-base">
          <AlertTriangle className="h-4 w-4 text-warning-foreground" />
          Failed documents
        </CardTitle>
        <CardDescription>
          {rows.length} document{rows.length === 1 ? '' : 's'} failed during
          ingestion.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ul className="space-y-2 text-sm">
          {rows.map((failure) => (
            <li
              key={failure.doc_id}
              className="rounded-md border border-border p-3"
            >
              <div className="flex items-center justify-between gap-2">
                <span className="font-mono text-xs text-muted-foreground">
                  {failure.doc_id}
                </span>
                <Badge variant="outline" className="text-xs">
                  {failure.stage}
                </Badge>
              </div>
              <p className="mt-2 text-xs">{failure.error}</p>
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  );
}

// --- Chunks tab --------------------------------------------------------------

function ChunksTab({ kb }: { kb: KbStatus }) {
  // CH-002 F7 — wired to the real GET /kb/{id}/documents/{doc_id}/chunks
  // (W16 F5.1.2). Needs a doc_id, so: a doc picker from the doc listing
  // (already-wired GET /kb/{id}/documents, W17 F4.1), honouring ?doc=<doc_id>.
  const searchParams = useSearchParams();
  const docs = useQuery<DocumentSummary[]>({
    queryKey: ['kb', kb.kb_id, 'documents'],
    queryFn: () => documentsApi.list(kb.kb_id),
  });

  const docList = docs.data ?? [];
  const docParam = searchParams.get('doc');
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null);
  const effectiveDocId =
    selectedDocId ??
    (docParam && docList.some((d) => d.doc_id === docParam)
      ? docParam
      : (docList[0]?.doc_id ?? null));

  const chunks = useQuery<ChunkSummary[]>({
    queryKey: ['kb', kb.kb_id, 'chunks', effectiveDocId],
    queryFn: () => documentsApi.listChunks(kb.kb_id, effectiveDocId as string),
    enabled: !!effectiveDocId,
  });

  return (
    <div className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-2">
        <StatCard label="Total chunks" value={kb.total_chunks} />
        <StatCard label="Screenshots" value={kb.total_screenshots} />
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Chunk inspection</CardTitle>
          <CardDescription>
            Per-chunk metadata(<span className="font-mono">chunk_id</span> /{' '}
            <span className="font-mono">section_path</span> / index / flags)for a
            document. Chunk body text is not bulk-listed — use the Retrieval
            Testing tab(or <span className="font-mono">/query</span>)to see the
            text of a retrieved chunk.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {docs.isLoading ? (
            <DocumentsSkeleton />
          ) : docs.isError ? (
            <div className="rounded-md border border-destructive bg-destructive/10 p-3 text-sm">
              Failed to load documents — backend unreachable or Azure AI Search
              not configured. Error:{' '}
              {String((docs.error as Error)?.message ?? 'unknown')}
            </div>
          ) : docList.length === 0 ? (
            <div className="rounded-md border border-dashed border-border bg-muted/30 p-6 text-center text-sm text-muted-foreground">
              No documents in this KB yet — upload one to inspect its chunks.
            </div>
          ) : (
            <>
              <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
                <Label
                  htmlFor="chunks-doc"
                  className="text-xs text-muted-foreground sm:w-24 sm:shrink-0"
                >
                  Document
                </Label>
                <Select
                  value={effectiveDocId ?? undefined}
                  onValueChange={setSelectedDocId}
                >
                  <SelectTrigger id="chunks-doc" className="w-full sm:w-96">
                    <SelectValue placeholder="Select a document" />
                  </SelectTrigger>
                  <SelectContent>
                    {docList.map((d) => (
                      <SelectItem key={d.doc_id} value={d.doc_id}>
                        {d.doc_title || d.doc_id}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {chunks.isLoading ? (
                <DocumentsSkeleton />
              ) : chunks.isError ? (
                <div className="rounded-md border border-destructive bg-destructive/10 p-3 text-sm">
                  Failed to load chunks. Error:{' '}
                  {String((chunks.error as Error)?.message ?? 'unknown')}
                </div>
              ) : (chunks.data?.length ?? 0) === 0 ? (
                <div className="rounded-md border border-dashed border-border bg-muted/30 p-6 text-center text-sm text-muted-foreground">
                  No chunks for this document.
                </div>
              ) : (
                <ChunksTable rows={chunks.data ?? []} />
              )}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function ChunksTable({ rows }: { rows: ChunkSummary[] }) {
  return (
    <div className="overflow-hidden rounded-md border border-border">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-muted/50 text-xs uppercase tracking-wide text-muted-foreground">
            <tr>
              <th scope="col" className="px-3 py-2 text-left font-medium">#</th>
              <th scope="col" className="px-3 py-2 text-left font-medium">Title</th>
              <th scope="col" className="px-3 py-2 text-left font-medium">Section path</th>
              <th scope="col" className="px-3 py-2 text-left font-medium">Flags</th>
              <th scope="col" className="px-3 py-2 text-left font-medium">Chunk id</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {rows.map((c) => (
              <tr key={c.chunk_id} className="bg-background">
                <td className="px-3 py-2 tabular-nums text-xs text-muted-foreground">
                  {c.chunk_index + 1}/{c.chunk_total}
                </td>
                <td className="px-3 py-2 font-medium">{c.chunk_title || '—'}</td>
                <td className="px-3 py-2 text-xs text-muted-foreground">
                  {c.section_path.length > 0 ? c.section_path.join(' › ') : '—'}
                </td>
                <td className="px-3 py-2">
                  <div className="flex flex-wrap gap-1">
                    {!c.enabled && (
                      <Badge variant="outline" className="text-[10px]">
                        disabled
                      </Badge>
                    )}
                    {c.low_value_flag && (
                      <Badge
                        variant="outline"
                        className="bg-warning/15 text-warning-foreground border-transparent text-[10px]"
                      >
                        low-value
                      </Badge>
                    )}
                    {c.enabled && !c.low_value_flag && (
                      <span className="text-[10px] text-muted-foreground">—</span>
                    )}
                  </div>
                </td>
                <td className="px-3 py-2 font-mono text-xs text-muted-foreground">
                  {c.chunk_id}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// --- Images tab (W20 F5.5 per ADR-0025) --------------------------------------

function ImagesTab({ kb }: { kb: KbStatus }) {
  const images = useQuery({
    queryKey: ['kb', kb.kb_id, 'images'],
    queryFn: () => kbApi.listImages(kb.kb_id, 200, 0),
  });
  const [selected, setSelected] = useState<string | null>(null);

  const items = images.data?.items ?? [];
  const selectedItem = items.find((i) => i.id === selected) ?? null;

  return (
    <div className="space-y-4">
      <header className="flex items-baseline justify-between">
        <div>
          <h2 className="text-base font-semibold tracking-tight">Cited screenshots</h2>
          <p className="text-xs text-muted-foreground">
            Images surfaced during ingest, aggregated across all chunks (deduplicated by SHA-256).
          </p>
        </div>
        <span className="text-xs text-muted-foreground">
          {images.isLoading ? 'Loading…' : `${items.length} image${items.length === 1 ? '' : 's'}`}
        </span>
      </header>

      {images.isError && (
        <div className="rounded-md border border-destructive bg-destructive/10 p-3 text-sm">
          Failed to load images:{' '}
          {String((images.error as Error)?.message ?? 'unknown')}
        </div>
      )}

      {!images.isLoading && !images.isError && items.length === 0 && (
        <div className="rounded-md border border-dashed border-border bg-muted/30 p-8 text-center">
          <ImageIcon className="mx-auto h-10 w-10 text-muted-foreground" />
          <p className="mt-3 text-sm font-medium">No images yet</p>
          <p className="mt-1 text-xs text-muted-foreground">
            Images surface after the screenshot pipeline runs end-to-end (R12 — Azure Blob
            switch pending Track A IT cred). Upload Word, PDF, or PowerPoint docs to populate.
          </p>
        </div>
      )}

      {items.length > 0 && (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4">
          {items.map((img) => (
            <button
              key={img.id}
              type="button"
              onClick={() => setSelected(img.id)}
              className="overflow-hidden rounded-md border border-border text-left transition-colors hover:border-accent focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
              aria-label={`Open image from ${img.doc_name}`}
            >
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={img.url}
                alt={img.ocr_text || `Image from ${img.doc_name}`}
                className="h-32 w-full object-cover"
              />
              <div className="border-t border-border bg-background p-2">
                <div className="line-clamp-1 text-xs font-medium">{img.doc_name}</div>
                {img.ocr_text && (
                  <div className="mt-0.5 line-clamp-2 text-[11px] text-muted-foreground">
                    {img.ocr_text}
                  </div>
                )}
              </div>
            </button>
          ))}
        </div>
      )}

      <Dialog open={selectedItem !== null} onOpenChange={(open) => !open && setSelected(null)}>
        <DialogContent className="max-w-3xl">
          <DialogHeader>
            <DialogTitle className="line-clamp-1">
              {selectedItem?.doc_name ?? 'Image preview'}
            </DialogTitle>
          </DialogHeader>
          {selectedItem && (
            <div className="space-y-2">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={selectedItem.url}
                alt={selectedItem.ocr_text || selectedItem.doc_name}
                className="max-h-[60vh] w-full rounded-md border border-border object-contain"
              />
              {selectedItem.ocr_text && (
                <div className="rounded-md border border-border bg-muted/40 p-3 text-xs">
                  <div className="font-semibold uppercase tracking-wide text-muted-foreground">
                    OCR / alt text
                  </div>
                  <p className="mt-1 whitespace-pre-wrap">{selectedItem.ocr_text}</p>
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}

// --- Chunking Lab tab (W20 F5.6 per ADR-0025) --------------------------------

function ChunkingLabTab({ kb }: { kb: KbStatus }) {
  const [sampleText, setSampleText] = useState(
    '## Example heading\n\nPaste sample content here to preview how the chunker will split it.\n\nAdd more paragraphs separated by blank lines.',
  );
  const [strategy, setStrategy] = useState<KbConfig['chunk_strategy']>(kb.config.chunk_strategy);
  const [chunkSize, setChunkSize] = useState(700);

  const preview = useMutation({
    mutationFn: () =>
      kbApi.chunkingPreview({
        kb_id: kb.kb_id,
        sample_text: sampleText,
        strategy,
        chunk_size: chunkSize,
        overlap: 0,
      }),
  });

  return (
    <div className="space-y-4">
      <header>
        <h2 className="text-base font-semibold tracking-tight">Chunking Lab</h2>
        <p className="text-xs text-muted-foreground">
          Preview how the current chunker will split sample text — no persistence, no
          Azure index writes. Apply changes via Settings → Chunk strategy.
        </p>
      </header>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Inputs</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="space-y-1.5">
            <Label htmlFor="lab-text">Sample text</Label>
            <textarea
              id="lab-text"
              value={sampleText}
              onChange={(e) => setSampleText(e.target.value)}
              rows={6}
              className="block w-full rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label htmlFor="lab-strategy">Strategy</Label>
              <Select
                value={strategy}
                onValueChange={(v) => setStrategy(v as KbConfig['chunk_strategy'])}
              >
                <SelectTrigger id="lab-strategy">
                  <SelectValue placeholder="Strategy" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="auto">auto</SelectItem>
                  <SelectItem value="layout_aware">layout_aware</SelectItem>
                  <SelectItem value="heading_aware">heading_aware</SelectItem>
                  <SelectItem value="slide_based">slide_based</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="lab-size">Chunk size (tokens)</Label>
              <Input
                id="lab-size"
                type="number"
                min={50}
                max={4000}
                value={chunkSize}
                onChange={(e) => setChunkSize(Number(e.target.value))}
              />
            </div>
          </div>
          <div className="flex items-center justify-between gap-2 pt-1">
            <Button type="button" onClick={() => preview.mutate()} disabled={preview.isPending}>
              {preview.isPending ? 'Previewing…' : 'Preview'}
            </Button>
            {/* Apply is a Tier 2 affordance — Wave B+ re-chunking pipeline. */}
            <DisabledAffordance
              variant="p3-preview"
              reason="Re-chunking requires re-ingest of every doc — arrives in a later tier"
              tier2Trigger="re-chunking pipeline"
              showBadge
            >
              <Button type="button" variant="outline" disabled>
                Apply
              </Button>
            </DisabledAffordance>
          </div>
        </CardContent>
      </Card>

      {preview.isError && (
        <div className="rounded-md border border-destructive bg-destructive/10 p-3 text-sm">
          Preview failed: {String((preview.error as Error)?.message ?? 'unknown')}
        </div>
      )}

      {preview.data && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">
              Preview ({preview.data.total} chunk{preview.data.total === 1 ? '' : 's'})
            </CardTitle>
            {preview.data.note && (
              <CardDescription className="text-xs">{preview.data.note}</CardDescription>
            )}
          </CardHeader>
          <CardContent className="space-y-2">
            {preview.data.items.length === 0 && (
              <p className="text-xs text-muted-foreground">No chunks emitted from the sample.</p>
            )}
            {preview.data.items.map((item) => (
              <details
                key={item.chunk_index}
                className="rounded-md border border-border bg-muted/30 p-2 text-xs"
              >
                <summary className="cursor-pointer">
                  <span className="font-medium">#{item.chunk_index}</span>{' '}
                  {item.chunk_title || '(untitled section)'}
                  <span className="ml-2 text-muted-foreground">
                    · {item.chunk_token_count} tokens
                  </span>
                </summary>
                <div className="mt-2 space-y-1">
                  {item.section_path.length > 0 && (
                    <div className="font-mono text-[10px] text-muted-foreground">
                      {item.section_path.join(' › ')}
                    </div>
                  )}
                  <pre className="whitespace-pre-wrap rounded bg-background p-2 font-mono text-[11px]">
                    {item.chunk_text}
                  </pre>
                </div>
              </details>
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// --- Pipeline tab ------------------------------------------------------------

function PipelineTab({ kb }: { kb: KbStatus }) {
  const { config } = kb;
  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Indexing</CardTitle>
          <CardDescription>
            Read-only Tier 1 view. Inline tuning lands W15+ per design ref §6
            sequencing.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <ConfigRow label="Embedding model" value={config.embedding_model} />
          <ConfigRow
            label="Embedding dimension"
            value={String(config.embedding_dimension)}
          />
          <ConfigRow label="Chunk strategy" value={config.chunk_strategy} />
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Retrieval</CardTitle>
          <CardDescription>
            Defaults applied to every query against this KB unless overridden.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <ConfigRow
            label="Default top_k retrieval"
            value={String(config.default_top_k)}
          />
          <ConfigRow
            label="Default rerank_k"
            value={String(config.default_rerank_k)}
          />
        </CardContent>
      </Card>
    </div>
  );
}

function ConfigRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between border-b border-border pb-2 last:border-0 last:pb-0">
      <span className="text-xs uppercase tracking-wide text-muted-foreground">
        {label}
      </span>
      <span className="font-mono text-sm">{value}</span>
    </div>
  );
}

// --- Retrieval Testing tab ---------------------------------------------------
// Per architecture.md §5.5.4 (ADR-0021): Vector / Full-Text / Hybrid mode
// selector + Top K + Score Threshold + Rerank toggle → ranked result preview
// (pure retrieval); plus the EKP-specific CRAG toggle + LLM selector on the
// end-to-end synthesis sub-panel.

const RETRIEVAL_MODES: { value: RetrievalMode; label: string; hint: string }[] = [
  {
    value: 'hybrid',
    label: 'Hybrid (BM25 + vector RRF)',
    hint: 'Default — keyword + semantic fused, with semantic rerank.',
  },
  {
    value: 'vector',
    label: 'Vector only',
    hint: 'Pure embedding similarity; no keyword scoring.',
  },
  {
    value: 'fulltext',
    label: 'Full-Text only (BM25)',
    hint: 'Keyword scoring only; no vector, no semantic rerank.',
  },
];

function RetrievalTab({ kb }: { kb: KbStatus }) {
  return (
    <div className="space-y-6">
      <RetrievalTestPanel kb={kb} />
      <EndToEndQueryPanel kb={kb} />
    </div>
  );
}

function RetrievalTestPanel({ kb }: { kb: KbStatus }) {
  const [query, setQuery] = useState('');
  const [mode, setMode] = useState<RetrievalMode>('hybrid');
  const [topK, setTopK] = useState(5);
  const [rerank, setRerank] = useState(true);
  const [scoreThreshold, setScoreThreshold] = useState(0);

  const thresholdApplies = mode !== 'fulltext';

  const mutation = useMutation({
    mutationFn: () =>
      retrievalTestApi.run(kb.kb_id, {
        query: query.trim(),
        mode,
        top_k: topK,
        rerank,
        score_threshold: thresholdApplies ? scoreThreshold : 0,
      }),
    onError: (err) => {
      if (err instanceof ApiError) {
        toast.error('Retrieval test failed', { description: err.message });
      }
    },
  });
  const result: RetrievalTestResult | null = mutation.data ?? null;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <Search className="h-4 w-4" />
          Retrieval test
        </CardTitle>
        <CardDescription>
          Pure retrieval against{' '}
          <span className="font-mono text-foreground">{kb.kb_id}</span> — compare
          Vector / Full-Text / Hybrid modes, tune Top-K + score threshold + rerank.
          No CRAG, no LLM synthesis (per architecture.md §5.5.4).
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-1.5">
          <Label htmlFor="rt-query">Test query</Label>
          <Input
            id="rt-query"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="e.g. how do I reconcile AR invoices?"
            disabled={mutation.isPending}
          />
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-1.5">
            <Label htmlFor="rt-mode">Search mode</Label>
            <Select value={mode} onValueChange={(v) => setMode(v as RetrievalMode)}>
              <SelectTrigger id="rt-mode">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {RETRIEVAL_MODES.map((m) => (
                  <SelectItem key={m.value} value={m.value}>
                    {m.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <p className="text-xs text-muted-foreground">
              {RETRIEVAL_MODES.find((m) => m.value === mode)?.hint}
            </p>
          </div>

          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <Label>Top K</Label>
              <span className="font-mono text-sm text-muted-foreground">{topK}</span>
            </div>
            <Slider
              aria-label="Top K"
              value={[topK]}
              onValueChange={(v) => setTopK(v[0] ?? 5)}
              min={1}
              max={50}
              step={1}
            />
            <p className="text-xs text-muted-foreground">
              Final chunk count{rerank ? ' (after rerank)' : ''}.
            </p>
          </div>

          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <Label>Score threshold</Label>
              <span className="font-mono text-sm text-muted-foreground">
                {thresholdApplies ? scoreThreshold.toFixed(2) : 'n/a'}
              </span>
            </div>
            <Slider
              aria-label="Score threshold"
              value={[scoreThreshold]}
              onValueChange={(v) => setScoreThreshold(v[0] ?? 0)}
              min={0}
              max={1}
              step={0.01}
              disabled={!thresholdApplies}
            />
            <p className="text-xs text-muted-foreground">
              {thresholdApplies
                ? 'Drop chunks below this similarity score (0 = keep all).'
                : 'Full-Text BM25 scores have no 0–1 range — threshold disabled.'}
            </p>
          </div>

          <div className="space-y-1.5">
            <div className="flex items-center justify-between gap-3">
              <Label htmlFor="rt-rerank">Rerank model</Label>
              <Switch id="rt-rerank" checked={rerank} onCheckedChange={setRerank} />
            </div>
            <p className="text-xs text-muted-foreground">
              {rerank
                ? 'Cohere v4.0-pro (Tier 1 locked — ADR-0012 / Q21).'
                : 'No reranker — raw mode-native ordering.'}
            </p>
          </div>
        </div>

        <Button
          onClick={() => mutation.mutate()}
          disabled={!query.trim() || mutation.isPending}
        >
          {mutation.isPending ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Running…
            </>
          ) : (
            <>
              <Search className="mr-2 h-4 w-4" />
              Test retrieval
            </>
          )}
        </Button>

        {mutation.isError && (
          <div className="rounded-md border border-destructive bg-destructive/10 p-3 text-sm">
            Retrieval failed:{' '}
            {String((mutation.error as Error)?.message ?? 'unknown error')}
          </div>
        )}

        {result && (
          <div className="space-y-3">
            <div className="flex flex-wrap items-center gap-x-4 gap-y-1 rounded-md bg-muted/40 p-2 font-mono text-xs text-muted-foreground">
              <span>mode: {result.mode}</span>
              <span>reranker: {result.reranker}</span>
              <span>
                hits: {result.chunks.length} / {result.total_hits}
              </span>
              <span>embed {result.embed_latency_ms}ms</span>
              <span>search {result.search_latency_ms}ms</span>
              {result.reranked && <span>rerank {result.rerank_latency_ms}ms</span>}
              <span>total {result.total_latency_ms}ms</span>
            </div>
            {result.chunks.length === 0 ? (
              <div className="rounded-md border border-dashed border-border p-3 text-sm text-muted-foreground">
                No chunks{' '}
                {result.total_hits > 0
                  ? `above the score threshold (${result.total_hits} retrieved before filter)`
                  : 'retrieved for this query'}
                .
              </div>
            ) : (
              <ul className="space-y-2">
                {result.chunks.map((c) => (
                  <li
                    key={c.chunk_id}
                    className="rounded-md border border-border p-3"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0 flex-1 space-y-1">
                        <div className="text-sm font-semibold">
                          {c.rank}. {c.chunk_title || '(untitled chunk)'}
                        </div>
                        <div className="text-xs text-muted-foreground">
                          {c.doc_title}
                        </div>
                        <div className="truncate font-mono text-[11px] text-muted-foreground">
                          {c.section_path.join(' > ') || '—'}
                        </div>
                      </div>
                      <Badge variant="outline" className="shrink-0 text-xs">
                        score {c.score.toFixed(4)}
                      </Badge>
                    </div>
                    <p className="mt-2 line-clamp-2 text-xs text-muted-foreground">
                      {c.chunk_text_preview}
                    </p>
                    <div className="mt-1 font-mono text-[10px] text-muted-foreground">
                      {c.chunk_id}
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function EndToEndQueryPanel({ kb }: { kb: KbStatus }) {
  const [query, setQuery] = useState('');
  const [enableCrag, setEnableCrag] = useState(true);
  const [llmModel, setLlmModel] = useState<'gpt-5.5' | 'gpt-5.4-mini'>('gpt-5.5');
  const [isStreaming, setIsStreaming] = useState(false);
  const [answer, setAnswer] = useState('');
  const [citations, setCitations] = useState<Citation[]>([]);
  const [refused, setRefused] = useState(false);
  const [rerankerUsed, setRerankerUsed] = useState('');
  const [errorText, setErrorText] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = query.trim();
    if (!trimmed || isStreaming) return;
    setAnswer('');
    setCitations([]);
    setRefused(false);
    setRerankerUsed('');
    setErrorText(null);
    setIsStreaming(true);
    const ac = new AbortController();
    abortRef.current = ac;
    const req: QueryRequest = {
      query: trimmed,
      kb_id: kb.kb_id,
      llm_model: llmModel,
      enable_crag: enableCrag,
    };
    try {
      for await (const evt of streamQuery(req, ac.signal)) {
        if (evt.type === 'text-delta') {
          setAnswer((prev) => prev + evt.content);
        } else if (evt.type === 'citation') {
          setCitations((prev) => [...prev, evt.citation]);
        } else if (evt.type === 'done') {
          setRefused(evt.refused);
          setRerankerUsed(evt.reranker_used);
        }
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      setErrorText(msg);
      if (err instanceof ApiError) {
        toast.error('Query failed', { description: err.message });
      }
    } finally {
      setIsStreaming(false);
      abortRef.current = null;
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <Sparkles className="h-4 w-4" />
          End-to-end query (synthesis)
        </CardTitle>
        <CardDescription>
          Full RAG against{' '}
          <span className="font-mono text-foreground">{kb.kb_id}</span> — hybrid
          retrieval → Cohere rerank → optional CRAG → LLM synthesis with citations.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-3">
          <div className="space-y-1.5">
            <Label htmlFor="e2e-query">Query</Label>
            <textarea
              id="e2e-query"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              rows={3}
              placeholder="Ask a question — e.g. How do I reconcile AR invoices?"
              disabled={isStreaming}
              className="w-full resize-none rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm transition-colors placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
            />
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="flex items-center justify-between gap-3">
              <Label htmlFor="e2e-crag">CRAG correction loop</Label>
              <Switch
                id="e2e-crag"
                checked={enableCrag}
                onCheckedChange={setEnableCrag}
                disabled={isStreaming}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="e2e-llm">LLM model</Label>
              <Select
                value={llmModel}
                onValueChange={(v) => setLlmModel(v as 'gpt-5.5' | 'gpt-5.4-mini')}
                disabled={isStreaming}
              >
                <SelectTrigger id="e2e-llm">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="gpt-5.5">gpt-5.5 (synthesis default)</SelectItem>
                  <SelectItem value="gpt-5.4-mini">gpt-5.4-mini</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <Button type="submit" disabled={!query.trim() || isStreaming}>
            {isStreaming ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Running…
              </>
            ) : (
              <>
                <FlaskConical className="mr-2 h-4 w-4" />
                Run end-to-end
              </>
            )}
          </Button>
        </form>

        {errorText && (
          <div className="mt-4 rounded-md border border-destructive bg-destructive/10 p-3 text-sm">
            Stream error: {errorText}
          </div>
        )}

        {refused && (
          <div className="mt-4 rounded-md border border-warning bg-warning/10 p-3 text-sm">
            Refused — answer not found in available documentation.
          </div>
        )}

        {answer && (
          <div className="mt-4 space-y-1.5">
            <div className="flex items-center justify-between">
              <Label>Synthesized answer</Label>
              {rerankerUsed && (
                <Badge variant="outline" className="text-xs">
                  reranker: {rerankerUsed}
                </Badge>
              )}
            </div>
            <p className="whitespace-pre-wrap rounded-md border border-border p-3 text-sm">
              {answer}
              {isStreaming && <span className="ml-1 animate-pulse">▍</span>}
            </p>
          </div>
        )}

        {citations.length > 0 && (
          <div className="mt-4 space-y-2">
            <Label>Citations ({citations.length})</Label>
            <ul className="space-y-2">
              {citations.map((c, idx) => (
                <li
                  key={c.chunk_id}
                  className="rounded-md border border-border p-3"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0 flex-1 space-y-1">
                      <div className="text-sm font-semibold">
                        {idx + 1}. {c.chunk_title || '(untitled chunk)'}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {c.doc_title}
                      </div>
                      <div className="truncate font-mono text-[11px] text-muted-foreground">
                        {c.section_path.join(' > ') || '—'}
                      </div>
                    </div>
                    <Badge variant="outline" className="shrink-0 text-xs">
                      score {c.relevance_score.toFixed(3)}
                    </Badge>
                  </div>
                  <div className="mt-1 font-mono text-[10px] text-muted-foreground">
                    {c.chunk_id}
                  </div>
                </li>
              ))}
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// --- Settings tab ------------------------------------------------------------

function SettingsTab({ kb }: { kb: KbStatus }) {
  const queryClient = useQueryClient();
  const [config, setConfig] = useState<KbConfig>(kb.config);
  const [name, setName] = useState(kb.name);
  const [description, setDescription] = useState(kb.description);

  useEffect(() => {
    setConfig(kb.config);
    setName(kb.name);
    setDescription(kb.description);
  }, [kb.config, kb.name, kb.description]);

  function invalidateKb() {
    queryClient.invalidateQueries({ queryKey: ['kb', kb.kb_id] });
    queryClient.invalidateQueries({ queryKey: ['kb', 'list'] });
  }

  const patchMutation = useMutation({
    mutationFn: (next: Partial<KbConfig>) =>
      kbApi.patchSettings(kb.kb_id, next),
    onSuccess: () => {
      invalidateKb();
      toast.success('Settings saved.');
    },
    onError: (err) => {
      toast.error('Save failed.', {
        description: err instanceof Error ? err.message : String(err),
      });
    },
  });

  // CH-002 F10 — name + description are editable now; partial PATCH /kb/{id}
  // (W16 F5.2 / CO_F3b). KbConfig stays in patchSettings.
  const metadataMutation = useMutation({
    mutationFn: (patch: { name?: string; description?: string }) =>
      kbApi.patchMetadata(kb.kb_id, patch),
    onSuccess: () => {
      invalidateKb();
      toast.success('Identity saved.');
    },
    onError: (err) => {
      toast.error('Save failed.', {
        description: err instanceof Error ? err.message : String(err),
      });
    },
  });

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    patchMutation.mutate(config);
  }

  function handleIdentitySubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    // True partial PATCH — only send the fields that actually changed.
    const patch: { name?: string; description?: string } = {};
    if (name !== kb.name) patch.name = name;
    if (description !== kb.description) patch.description = description;
    if (Object.keys(patch).length === 0) {
      toast.info('No changes to save.');
      return;
    }
    metadataMutation.mutate(patch);
  }

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Identity</CardTitle>
          <CardDescription>
            Display name + description — saved via PATCH /kb/&#123;id&#125;
            (partial update; the KB id is immutable). Indexing config is below.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleIdentitySubmit} className="space-y-3">
            <div className="space-y-1.5">
              <Label htmlFor="kb-id">KB ID</Label>
              <Input id="kb-id" value={kb.kb_id} readOnly className="font-mono" />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="kb-name">Display name</Label>
              <Input
                id="kb-name"
                value={name}
                onChange={(e) => setName(e.target.value)}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="kb-description">Description</Label>
              <Input
                id="kb-description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
              />
            </div>
            <div className="pt-2">
              <Button type="submit" disabled={metadataMutation.isPending}>
                {metadataMutation.isPending ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Saving…
                  </>
                ) : (
                  'Save identity'
                )}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Indexing config</CardTitle>
          <CardDescription>
            Editable. Save persists to backend via PATCH /kb/&#123;id&#125;/settings.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-3">
            <div className="space-y-1.5">
              <Label htmlFor="kb-embedding-model">Embedding model</Label>
              <Input
                id="kb-embedding-model"
                value={config.embedding_model}
                onChange={(e) =>
                  setConfig({ ...config, embedding_model: e.target.value })
                }
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="kb-embedding-dim">Embedding dimension</Label>
              <Input
                id="kb-embedding-dim"
                type="number"
                value={config.embedding_dimension}
                onChange={(e) =>
                  setConfig({
                    ...config,
                    embedding_dimension: Number(e.target.value),
                  })
                }
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="kb-chunk-strategy">Chunk strategy</Label>
              <Select
                value={config.chunk_strategy}
                onValueChange={(v) =>
                  setConfig({
                    ...config,
                    chunk_strategy: v as KbConfig['chunk_strategy'],
                  })
                }
              >
                <SelectTrigger id="kb-chunk-strategy">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="auto">auto (per format)</SelectItem>
                  <SelectItem value="layout_aware">layout_aware (Word/PDF)</SelectItem>
                  <SelectItem value="heading_aware">heading_aware</SelectItem>
                  <SelectItem value="slide_based">slide_based (PPT)</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <Label htmlFor="kb-top-k">Default top_k retrieval</Label>
                <Input
                  id="kb-top-k"
                  type="number"
                  value={config.default_top_k}
                  onChange={(e) =>
                    setConfig({
                      ...config,
                      default_top_k: Number(e.target.value),
                    })
                  }
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="kb-rerank-k">Default rerank_k</Label>
                <Input
                  id="kb-rerank-k"
                  type="number"
                  value={config.default_rerank_k}
                  onChange={(e) =>
                    setConfig({
                      ...config,
                      default_rerank_k: Number(e.target.value),
                    })
                  }
                />
              </div>
            </div>
            <div className="pt-2">
              <Button type="submit" disabled={patchMutation.isPending}>
                {patchMutation.isPending ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Saving…
                  </>
                ) : (
                  'Save settings'
                )}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      <DangerZone kb={kb} />
    </div>
  );
}

function DangerZone({ kb }: { kb: KbStatus }) {
  return (
    <Card className="border-destructive/30">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base text-destructive">
          <AlertTriangle className="h-4 w-4" />
          Danger zone
        </CardTitle>
        <CardDescription>
          Archive freezes new ingest but keeps the index + screenshots queryable;
          Re-index sweeps every document(idempotent);Delete drops the KB +
          all its chunks + screenshots(non-recoverable).
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {/* W20 F5.7 — Archive action lands real backend (POST /kb/{id}/archive). */}
        <ArchiveAction kb={kb} />
        <DangerAction
          label="Re-index KB"
          description="Re-run the ingestion pipeline against every document in this KB."
          confirmTitle="Re-index this KB?"
          confirmMessage="This will queue a re-ingestion job for every document. Existing chunks remain queryable until the job completes."
          confirmCta="Re-index"
          stub="POST /kb/{id}/reindex"
          issue="W2 stub — confirms UX wire only."
          kbId={kb.kb_id}
        />
        <DangerAction
          label="Delete KB"
          description="Permanently delete this KB, its chunks, and screenshots."
          confirmTitle="Delete this KB?"
          confirmMessage="This action is non-recoverable. Type the KB id to confirm in a future iteration; for now the action is gated to a UI confirm only."
          confirmCta="Delete KB"
          stub="DELETE /kb/{id}"
          issue="Stub — UI wire only."
          variant="destructive"
          kbId={kb.kb_id}
        />
      </CardContent>
    </Card>
  );
}

// W20 F5.7 — Archive action with real backend wire (POST /kb/{id}/archive).
function ArchiveAction({ kb }: { kb: KbStatus }) {
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);

  const mutation = useMutation({
    mutationFn: () => kbApi.archive(kb.kb_id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['kb', kb.kb_id] });
      queryClient.invalidateQueries({ queryKey: ['kb', 'list'] });
      toast.success(`KB '${kb.kb_id}' archived.`);
      setOpen(false);
    },
    onError: (err) => {
      toast.error('Archive failed.', {
        description: err instanceof Error ? err.message : String(err),
      });
    },
  });

  return (
    <div className="flex items-start justify-between gap-3 rounded-md border border-border p-3">
      <div className="flex-1">
        <div className="flex items-center gap-2 text-sm font-medium">
          <Archive className="h-3.5 w-3.5" />
          Archive KB
          {kb.archived && (
            <Badge variant="outline" className="bg-muted text-xs text-muted-foreground">
              Already archived
            </Badge>
          )}
        </div>
        <p className="text-xs text-muted-foreground">
          Freeze new ingest. The Azure search index + screenshot blobs are preserved so
          the chat surface keeps citing past content.
        </p>
      </div>
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogTrigger asChild>
          <Button variant="outline" disabled={kb.archived || mutation.isPending}>
            {kb.archived ? 'Archived' : 'Archive'}
          </Button>
        </DialogTrigger>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Archive this KB?</DialogTitle>
            <DialogDescription>
              <span className="font-mono">{kb.kb_id}</span> will reject new uploads + reindex
              requests. Existing chunks remain queryable from the chat surface.
              Re-create the KB to resume ingest.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setOpen(false)} disabled={mutation.isPending}>
              Cancel
            </Button>
            <Button onClick={() => mutation.mutate()} disabled={mutation.isPending}>
              {mutation.isPending ? 'Archiving…' : 'Archive KB'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

function DangerAction({
  label,
  description,
  confirmTitle,
  confirmMessage,
  confirmCta,
  stub,
  issue,
  variant = 'outline',
  kbId,
}: {
  label: string;
  description: string;
  confirmTitle: string;
  confirmMessage: string;
  confirmCta: string;
  stub: string;
  issue: string;
  variant?: 'outline' | 'destructive';
  kbId: string;
}) {
  const [open, setOpen] = useState(false);
  return (
    <div className="flex flex-col gap-2 rounded-md border border-border p-3 sm:flex-row sm:items-start sm:justify-between">
      <div className="min-w-0 flex-1">
        <p className="text-sm font-medium">{label}</p>
        <p className="text-xs text-muted-foreground">{description}</p>
      </div>
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogTrigger asChild>
          <Button variant={variant} size="sm" className="shrink-0">
            {label}
          </Button>
        </DialogTrigger>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{confirmTitle}</DialogTitle>
            <DialogDescription>{confirmMessage}</DialogDescription>
          </DialogHeader>
          <div className="space-y-2 rounded-md border border-dashed border-border bg-muted/40 p-3 text-xs">
            <p className="font-medium">Backend status</p>
            <p className="text-muted-foreground">
              <span className="font-mono">{stub}</span> — {issue}
            </p>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setOpen(false)}>
              Cancel
            </Button>
            <Button
              variant={variant === 'destructive' ? 'destructive' : 'default'}
              onClick={() => {
                setOpen(false);
                toast.info(`${label} pending backend (${stub})`, {
                  description: `KB: ${kbId}`,
                });
              }}
            >
              {confirmCta}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

// --- Shared helpers ----------------------------------------------------------

function StatCard({
  label,
  value,
}: {
  label: string;
  value: number | string;
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
          {typeof value === 'number' ? value.toLocaleString() : value}
        </div>
      </CardContent>
    </Card>
  );
}

