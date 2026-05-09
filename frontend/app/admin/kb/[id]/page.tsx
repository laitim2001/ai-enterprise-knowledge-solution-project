'use client';

/**
 * V4 KB Detail (`/admin/kb/[id]`) — per architecture.md v6 §5.5 view 4.
 *
 * W14 D3 F3 refactor — 5-tab nav (Documents / Chunks / Pipeline / Retrieval
 * Testing / Settings) per ui-design-reference-v6.md §2.4 wireframe. Tab state
 * lives in Next.js searchParams (`?tab=documents`) so URLs are bookmark-friendly.
 *
 * Plan §7 changelog (D3) deviations:
 * - F3.2 Documents tab: backend GET /kb/{id}/documents returns 501 (W2 stub) —
 *   surface count + failed_documents list + Upload CTA + TODO note.
 * - F3.3 Chunks tab: backend GET /kb/{id}/documents/{id}/chunks returns 501 —
 *   surface placeholder + TODO note.
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
  Settings as SettingsIcon,
  SlidersHorizontal,
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ApiError } from '@/lib/api-client';
import {
  kbApi,
  type FailureRecord,
  type KbConfig,
  type KbStatus,
} from '@/lib/api/kb';
import { streamQuery, type Citation } from '@/lib/api/query';

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

      <BackendStubNote stub="GET /kb/{id}/documents" issue="W2 listing implementation" />

      {kb.failed_documents.length > 0 && (
        <FailuresSection rows={kb.failed_documents} />
      )}

      <div className="rounded-md border border-dashed border-border bg-muted/30 p-6 text-center">
        <Upload className="mx-auto h-8 w-8 text-muted-foreground" />
        <p className="mt-3 text-sm font-medium">Add a document</p>
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

interface RetrievalResult {
  citations: Citation[];
  answer: string;
  refused: boolean;
  rerankerUsed: string;
  errorText: string | null;
}

const EMPTY_RESULT: RetrievalResult = {
  citations: [],
  answer: '',
  refused: false,
  rerankerUsed: '',
  errorText: null,
};

function RetrievalTab({ kb }: { kb: KbStatus }) {
  const [queryText, setQueryText] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [result, setResult] = useState<RetrievalResult>(EMPTY_RESULT);
  const abortRef = useRef<AbortController | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = queryText.trim();
    if (!trimmed || isStreaming) return;
    setResult({ ...EMPTY_RESULT });
    setIsStreaming(true);
    const ac = new AbortController();
    abortRef.current = ac;
    try {
      for await (const evt of streamQuery(
        { query: trimmed, kb_id: kb.kb_id },
        ac.signal,
      )) {
        if (evt.type === 'text-delta') {
          setResult((prev) => ({ ...prev, answer: prev.answer + evt.content }));
        } else if (evt.type === 'citation') {
          setResult((prev) => ({
            ...prev,
            citations: [...prev.citations, evt.citation],
          }));
        } else if (evt.type === 'done') {
          setResult((prev) => ({
            ...prev,
            refused: evt.refused,
            rerankerUsed: evt.reranker_used,
          }));
        }
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      setResult((prev) => ({ ...prev, errorText: msg }));
      if (err instanceof ApiError) {
        toast.error('Query failed', { description: err.message });
      }
    } finally {
      setIsStreaming(false);
      abortRef.current = null;
    }
  }

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Run a test query</CardTitle>
          <CardDescription>
            POST /query against{' '}
            <span className="font-mono text-foreground">{kb.kb_id}</span>;
            inspect retrieved chunks + relevance scores + reranker outcome.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-3">
            <div className="space-y-1.5">
              <Label htmlFor="retrieval-query">Test query</Label>
              <textarea
                id="retrieval-query"
                value={queryText}
                onChange={(e) => setQueryText(e.target.value)}
                rows={3}
                placeholder="Ask a question — e.g. How do I reconcile AR invoices?"
                disabled={isStreaming}
                className="w-full resize-none rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm transition-colors placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
              />
            </div>
            <Button type="submit" disabled={!queryText.trim() || isStreaming}>
              {isStreaming ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Running…
                </>
              ) : (
                <>
                  <FlaskConical className="mr-2 h-4 w-4" />
                  Run query
                </>
              )}
            </Button>
          </form>
        </CardContent>
      </Card>

      {result.errorText && (
        <div className="rounded-md border border-destructive bg-destructive/10 p-3 text-sm">
          Stream error: {result.errorText}
        </div>
      )}

      {result.refused && (
        <div className="rounded-md border border-warning bg-warning/10 p-3 text-sm">
          Refused — answer not found in available documentation.
        </div>
      )}

      {result.answer && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center justify-between text-base">
              Synthesized answer
              {result.rerankerUsed && (
                <Badge variant="outline" className="text-xs">
                  reranker: {result.rerankerUsed}
                </Badge>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="whitespace-pre-wrap text-sm">
              {result.answer}
              {isStreaming && <span className="ml-1 animate-pulse">▍</span>}
            </p>
          </CardContent>
        </Card>
      )}

      {result.citations.length > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">
              Retrieved chunks ({result.citations.length})
            </CardTitle>
            <CardDescription>
              Sorted by relevance score(reranked when reranker enabled).
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ul className="space-y-3">
              {result.citations.map((c, idx) => (
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
                    <Badge variant="outline" className="text-xs">
                      score {c.relevance_score.toFixed(3)}
                    </Badge>
                  </div>
                  <div className="mt-2 font-mono text-[10px] text-muted-foreground">
                    {c.chunk_id}
                  </div>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}
    </div>
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
