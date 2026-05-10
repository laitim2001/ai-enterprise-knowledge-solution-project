'use client';

/**
 * V4 KB Detail (`/admin/kb/[id]`) — per architecture.md v6 §5.5 view 4.
 *
 * W14 D3 F3 refactor — 5-tab nav (Documents / Chunks / Pipeline / Retrieval
 * Testing / Settings) per ui-design-reference-v6.md §2.4 wireframe. Tab state
 * lives in Next.js searchParams (`?tab=documents`) so URLs are bookmark-friendly.
 *
 * Plan §7 changelog (D3) deviations:
 * - F3.2 Documents tab: (W14 D3 — backend stub) → W17 F4.1: now wired to the
 *   real GET /kb/{id}/documents (W16 F5.1.1 / CO_F3a — Azure AI Search chunk
 *   aggregation by doc_id); renders a doc table; empty index → Upload prompt.
 * - F3.3 Chunks tab: backend GET /kb/{id}/documents/{id}/chunks returns 501 —
 *   surface placeholder + TODO note (still a stub — W2 ingestion + Track A).
 * - F3.4 Pipeline tab: read-only config visualization Tier 1 (no PATCH inline).
 * - F3.6 Settings: name + description display-only (kbApi.patchSettings only
 *   accepts Partial<KbConfig>; name/description backend endpoint not exposed).
 *   Config fields remain editable.
 * - F3.8 Stepper rule-of-3 NOT triggered: Pipeline tab read-only display, not
 *   wizard state machine; inline retention preserved per W13 D4 decision.
 *
 * Layout reference Dify Image 1+2+4+5+6 (no code copy per ADR-0010).
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  AlertTriangle,
  ArrowLeft,
  Database,
  FileText,
  FlaskConical,
  Loader2,
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
import { documentsApi, type DocumentSummary } from '@/lib/api/documents';
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

const VALID_TABS = [
  'documents',
  'chunks',
  'pipeline',
  'retrieval',
  'settings',
] as const;
type TabKey = (typeof VALID_TABS)[number];

const TAB_LABEL: Record<TabKey, string> = {
  documents: 'Documents',
  chunks: 'Chunks',
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
    router.push(`/admin/kb/${kbId}?${params.toString()}`, { scroll: false });
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
          href="/admin/kb"
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
          <Link href={`/admin/kb/${kbId}/upload`}>
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
          </TabsList>
        </div>

        <TabsContent value="documents" className="mt-6">
          <DocumentsTab kb={kb} />
        </TabsContent>
        <TabsContent value="chunks" className="mt-6">
          <ChunksTab kb={kb} />
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
              <Link href={`/admin/kb/${kb.kb_id}/upload`}>
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
  return (
    <div className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-2">
        <StatCard label="Total chunks" value={kb.total_chunks} />
        <StatCard label="Screenshots" value={kb.total_screenshots} />
      </div>

      <BackendStubNote
        stub="GET /kb/{id}/documents/{id}/chunks"
        issue="W2 chunk listing implementation"
      />

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Chunk inspection</CardTitle>
          <CardDescription>
            Per-chunk drill-down(`chunk_id` / `section_path` / token count /
            preview)+ click-to-expand modal — pending backend list endpoint.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-xs text-muted-foreground">
            Use the Retrieval Testing tab to inspect retrieved chunks for a
            specific query — citation cards surface the same{' '}
            <span className="font-mono">chunk_id</span> /{' '}
            <span className="font-mono">section_path</span> trace.
          </p>
        </CardContent>
      </Card>
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

  useEffect(() => {
    setConfig(kb.config);
  }, [kb.config]);

  const patchMutation = useMutation({
    mutationFn: (next: Partial<KbConfig>) =>
      kbApi.patchSettings(kb.kb_id, next),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['kb', kb.kb_id] });
      queryClient.invalidateQueries({ queryKey: ['kb', 'list'] });
      toast.success('Settings saved.');
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

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Identity</CardTitle>
          <CardDescription>
            Display fields are read-only Tier 1 — backend `name` /
            `description` PATCH lands W15+ per CO_W15 follow-up.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="space-y-1.5">
            <Label>KB ID</Label>
            <Input value={kb.kb_id} readOnly className="font-mono" />
          </div>
          <div className="space-y-1.5">
            <Label>Display name</Label>
            <Input value={kb.name} readOnly />
          </div>
          <div className="space-y-1.5">
            <Label>Description</Label>
            <Input value={kb.description} readOnly />
          </div>
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

      <DangerZone kbId={kb.kb_id} />
    </div>
  );
}

function DangerZone({ kbId }: { kbId: string }) {
  return (
    <Card className="border-destructive/30">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base text-destructive">
          <AlertTriangle className="h-4 w-4" />
          Danger zone
        </CardTitle>
        <CardDescription>
          Re-index sweeps every document(idempotent);Delete drops the KB +
          all its chunks + screenshots(non-recoverable).
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        <DangerAction
          label="Re-index KB"
          description="Re-run the ingestion pipeline against every document in this KB."
          confirmTitle="Re-index this KB?"
          confirmMessage="This will queue a re-ingestion job for every document. Existing chunks remain queryable until the job completes."
          confirmCta="Re-index"
          stub="POST /kb/{id}/reindex"
          issue="W2 stub — confirms UX wire only."
          kbId={kbId}
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
          kbId={kbId}
        />
      </CardContent>
    </Card>
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

function BackendStubNote({
  stub,
  issue,
}: {
  stub: string;
  issue: string;
}) {
  return (
    <div className="rounded-md border border-dashed border-border bg-muted/30 px-3 py-2 text-xs text-muted-foreground">
      <span className="font-medium text-foreground">Backend status:</span>{' '}
      <span className="font-mono">{stub}</span> — {issue} (501 stub).
    </div>
  );
}
