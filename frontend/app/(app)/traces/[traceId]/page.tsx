'use client';

/**
 * V6 Traces (`/traces/[traceId]`) — per architecture.md v6 §5.7 view 6 +
 * design ref §2.6 wireframe.
 *
 * W18 F3 (per ADR-0024): renamed "Debug View" → "Traces" + relocated
 * /debug/[traceId] → app/(app)/traces/[traceId] (now rendered inside <AppShell>).
 * The backend endpoint stays `GET /debug/trace/{trace_id}` (unchanged) — only
 * the frontend route + the sidebar label changed; `lib/api/debug.ts` keeps its
 * name (it talks to that backend endpoint).
 *
 * W15 D2 F2: initial implementation (6-stage interim wireframe scaffold + 501
 * stub mitigation, per W15 D2 plan §7 changelog).
 * ADR-0020 Session 2 (W16): expanded to the 9-stage spec (architecture.md §5.7)
 * and wired to the live backend `GET /debug/trace/{trace_id}` (shipped W16 F5.5,
 * Decision D.2 full Langfuse SDK integration). The backend returns a flat list
 * of raw Langfuse observations; this view maps each onto one of the 9 conceptual
 * pipeline stages via name-prefix matching. Stages without a matched observation
 * render a "not traced this query" note (e.g. Query Rewriter / Re-retrieve only
 * appear when CRAG triggers a correction).
 *
 * The endpoint always returns HTTP 200 — the `status` field communicates the
 * outcome, so this view branches on `status` (ok / langfuse_not_configured /
 * not_found / sdk_method_missing / fetch_failed) rather than HTTP code. The
 * "Open in Langfuse" deep-link CTA uses the backend-provided `trace_url` (which
 * is always populated) and falls back to `NEXT_PUBLIC_LANGFUSE_URL`.
 *
 * Layout primitive: custom Collapsible (useState + ChevronDown rotation) per
 * the W15 D2 decision — no shadcn Accordion dependency (H2 vendor lock).
 */

import { useQuery } from '@tanstack/react-query';
import {
  AlertCircle,
  ChevronDown,
  ChevronLeft,
  ExternalLink,
  Hash,
  Timer,
} from 'lucide-react';
import Link from 'next/link';
import { useState } from 'react';

import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { debugApi, type TraceDetail, type TraceStage } from '@/lib/api/debug';
import { cn } from '@/lib/utils';

// --- 9 conceptual pipeline stages per architecture.md v6 §5.7 ----------------
// `obsPrefixes` matches raw Langfuse observation names emitted by the backend
// (`@observe_async` / `@observe_llm_async` / `observe_streaming` /
// `emit_stage_metadata`). A given observation is claimed by the FIRST stage (in
// this order) whose prefix it matches, so there's no double-counting when e.g.
// `retrieval.retrieve` appears twice (initial + CRAG re-retrieval). Stages with
// no prefix aren't separately traced in Tier 1; `note` explains why.

interface PipelineStage {
  id: number;
  name: string;
  vendor?: string;
  description: string;
  obsPrefixes: string[];
  note?: string;
}

const PIPELINE_STAGES: PipelineStage[] = [
  {
    id: 1,
    name: 'Query Preprocessor',
    description: 'Tokenize, normalize, optional intent classification',
    obsPrefixes: [],
    note: 'Lightweight in-process step — not emitted as a separate Langfuse span.',
  },
  {
    id: 2,
    name: 'Query Rewriter',
    vendor: 'gpt-5.4-mini',
    description:
      'CRAG correction loop — rewrites the query when initial confidence is below threshold',
    obsPrefixes: ['crag.rewrite_query'],
    note: 'Only present when CRAG triggers a correction (confidence below 0.70).',
  },
  {
    id: 3,
    name: 'Hybrid Retrieval',
    description:
      'BM25 top-50 + Vector top-50 + RRF fusion → unique candidates (kb_id-scoped per ADR-0018)',
    obsPrefixes: ['retrieval.retrieve'],
    note: 'Cohere rerank runs inside this span — see `rerank_latency_ms` in its details.',
  },
  {
    id: 4,
    name: 'Reranker',
    vendor: 'Cohere v4.0-pro',
    description:
      'Top-50 candidates → top-K rerank (production lock per Q21 Resolved + ADR-0012)',
    obsPrefixes: [],
    note: 'Folded into the Hybrid Retrieval span (`rerank_latency_ms` there).',
  },
  {
    id: 5,
    name: 'CRAG Confidence Judge',
    vendor: 'gpt-5.4-mini',
    description:
      'Grades retrieved context; pass-through above threshold (default 0.70) or trigger re-retrieve',
    obsPrefixes: ['crag.grade', 'crag.refine'],
  },
  {
    id: 6,
    name: 'Re-retrieve',
    description: 'CRAG correction loop — re-runs retrieval with the rewritten query',
    obsPrefixes: [],
    note: 'Reuses the `retrieval.retrieve` span name — a second occurrence appears under Hybrid Retrieval when CRAG corrects.',
  },
  {
    id: 7,
    name: 'Context Expander',
    description:
      'Prepends prev / appends next neighbor chunk text to the top-K reranked chunks (architecture.md §3.1, ADR-0020)',
    obsPrefixes: ['generation.context_expansion'],
  },
  {
    id: 8,
    name: 'LLM Synthesis',
    vendor: 'gpt-5.5',
    description: 'Synthesize answer with citations + refusal logic for out-of-scope queries',
    obsPrefixes: ['synthesizer.synthesize', 'api.query.stream'],
  },
  {
    id: 9,
    name: 'Final Response',
    description: 'End-to-end orchestration aggregate — citation linking, cost, Langfuse trace publish',
    obsPrefixes: ['api.query'],
  },
];

const LANGFUSE_FALLBACK_BASE =
  process.env.NEXT_PUBLIC_LANGFUSE_URL ?? 'http://localhost:3000';

function matchesPrefix(name: string, prefix: string): boolean {
  return name === prefix || name.startsWith(`${prefix}.`);
}

/** Distribute observations across the 9 conceptual stages (first-match wins). */
function bucketObservations(stages: TraceStage[]): Map<number, TraceStage[]> {
  const buckets = new Map<number, TraceStage[]>();
  for (const stage of PIPELINE_STAGES) {
    buckets.set(stage.id, []);
  }
  for (const obs of stages) {
    const owner = PIPELINE_STAGES.find((s) =>
      s.obsPrefixes.some((p) => matchesPrefix(obs.name, p)),
    );
    if (owner) {
      buckets.get(owner.id)!.push(obs);
    }
  }
  return buckets;
}

type LoadState = 'loading' | 'error' | 'ready';

export default function DebugTracePage({
  params,
}: {
  params: { traceId: string };
}) {
  const traceId = params.traceId;

  const query = useQuery<TraceDetail>({
    queryKey: ['debug', 'trace', traceId],
    queryFn: () => debugApi.getTrace(traceId),
    retry: false,
  });

  const loadState: LoadState = query.isLoading
    ? 'loading'
    : query.isError
      ? 'error'
      : 'ready';

  const data = query.data;
  const langfuseHref =
    data?.trace_url ??
    `${LANGFUSE_FALLBACK_BASE}/trace/${encodeURIComponent(traceId)}`;

  const buckets = data ? bucketObservations(data.stages) : null;

  return (
    <div className="space-y-6">
      <header className="space-y-3">
        <div className="flex items-center gap-3 text-sm text-muted-foreground">
          <Button asChild variant="ghost" size="sm">
            <Link href="/eval">
              <ChevronLeft className="mr-1 h-4 w-4" />
              Back to Eval Console
            </Link>
          </Button>
        </div>
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="min-w-0">
            <h1 className="text-2xl font-semibold tracking-tight">Trace inspection</h1>
            <p className="mt-1 truncate font-mono text-sm text-muted-foreground">
              {traceId}
            </p>
          </div>
          <Button asChild variant="outline">
            <a href={langfuseHref} target="_blank" rel="noopener noreferrer">
              <ExternalLink className="mr-2 h-4 w-4" />
              Open in Langfuse
            </a>
          </Button>
        </div>
      </header>

      <StatusBanner loadState={loadState} data={data} error={query.error} />

      <SummaryCard loadState={loadState} data={data} />

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Pipeline timeline (9 stages)</CardTitle>
          <CardDescription>
            Per-stage Langfuse observations per architecture.md v6 §5.7 (ADR-0020).
            Stages with no observation this query are noted inline.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-2">
          {PIPELINE_STAGES.map((stage) => (
            <PipelineStageCollapsible
              key={stage.id}
              stage={stage}
              observations={buckets?.get(stage.id) ?? []}
              loadState={loadState}
              traceStatus={data?.status}
            />
          ))}
        </CardContent>
      </Card>
    </div>
  );
}

// --- Status banner -----------------------------------------------------------

const STATUS_COPY: Record<
  string,
  { title: string; tone: 'info' | 'warn' } | undefined
> = {
  langfuse_not_configured: {
    title: 'Langfuse not configured — stage data unavailable',
    tone: 'info',
  },
  sdk_method_missing: {
    title: 'Langfuse SDK too old — stage extraction unavailable',
    tone: 'warn',
  },
  not_found: { title: 'Trace not found in Langfuse', tone: 'warn' },
  fetch_failed: { title: 'Langfuse fetch failed', tone: 'warn' },
};

function StatusBanner({
  loadState,
  data,
  error,
}: {
  loadState: LoadState;
  data: TraceDetail | undefined;
  error: unknown;
}) {
  if (loadState === 'loading') {
    return null;
  }
  if (loadState === 'error') {
    return (
      <div className="rounded-md border border-destructive bg-destructive/10 p-3 text-sm">
        Failed to load trace: {String((error as Error)?.message ?? 'unknown error')}
      </div>
    );
  }
  if (!data || data.status === 'ok') {
    return null;
  }
  const copy = STATUS_COPY[data.status] ?? {
    title: `Trace status: ${data.status}`,
    tone: 'warn' as const,
  };
  return (
    <div
      className={cn(
        'flex items-start gap-3 rounded-md border p-4 text-sm',
        copy.tone === 'info'
          ? 'border-dashed border-border bg-muted/30'
          : 'border-amber-500/40 bg-amber-500/10',
      )}
    >
      <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
      <div>
        <p className="font-medium">{copy.title}</p>
        {data.note ? (
          <p className="mt-1 text-xs text-muted-foreground">{data.note}</p>
        ) : null}
        <p className="mt-1 text-xs text-muted-foreground">
          The 9-stage scaffold below shows the pipeline shape; per-stage
          observations populate once trace data is available. The Open in
          Langfuse link uses the trace ID and works independently.
        </p>
      </div>
    </div>
  );
}

// --- Summary card ------------------------------------------------------------

function SummaryCard({
  loadState,
  data,
}: {
  loadState: LoadState;
  data: TraceDetail | undefined;
}) {
  if (loadState === 'loading') {
    return (
      <div className="grid gap-4 sm:grid-cols-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <Card key={i}>
            <CardHeader className="pb-2">
              <Skeleton className="h-4 w-1/2" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-7 w-3/4" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }
  if (!data) {
    return null;
  }
  return (
    <div className="grid gap-4 sm:grid-cols-3">
      <SummaryTile
        label="Latency"
        title="Total duration"
        icon={<Timer className="h-5 w-5 text-muted-foreground" />}
        value={`${data.total_latency_ms.toLocaleString()} ms`}
      />
      <SummaryTile
        label="Tokens in"
        title="Input tokens"
        icon={<Hash className="h-5 w-5 text-muted-foreground" />}
        value={data.total_input_tokens.toLocaleString()}
      />
      <SummaryTile
        label="Tokens out"
        title="Output tokens"
        icon={<Hash className="h-5 w-5 text-muted-foreground" />}
        value={data.total_output_tokens.toLocaleString()}
      />
    </div>
  );
}

function SummaryTile({
  label,
  title,
  icon,
  value,
}: {
  label: string;
  title: string;
  icon: React.ReactNode;
  value: string;
}) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardDescription className="font-mono text-[10px] uppercase tracking-wide">
          {label}
        </CardDescription>
        <CardTitle className="text-sm">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex items-center gap-2 text-2xl font-semibold">
          {icon}
          {value}
        </div>
      </CardContent>
    </Card>
  );
}

// --- Per-stage collapsible ---------------------------------------------------

function sumLatency(observations: TraceStage[]): number {
  return observations.reduce((acc, o) => acc + (o.latency_ms || 0), 0);
}

function PipelineStageCollapsible({
  stage,
  observations,
  loadState,
  traceStatus,
}: {
  stage: PipelineStage;
  observations: TraceStage[];
  loadState: LoadState;
  traceStatus: string | undefined;
}) {
  const [open, setOpen] = useState(false);
  const hasData = observations.length > 0;
  const traceOk = traceStatus === 'ok';

  const durationLabel = (() => {
    if (loadState === 'loading') return '…';
    if (!hasData) return '—';
    return `${sumLatency(observations).toLocaleString()} ms`;
  })();

  const anyError = observations.some((o) => o.status === 'error');

  return (
    <div className="rounded-md border border-border">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        aria-expanded={open}
        className="flex w-full items-center justify-between gap-3 rounded-md p-3 text-left transition-colors hover:bg-muted/50 focus-visible:bg-muted/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1"
      >
        <div className="flex min-w-0 items-center gap-3">
          <ChevronDown
            className={cn(
              'h-4 w-4 shrink-0 transition-transform duration-200',
              open && 'rotate-180',
            )}
          />
          <span className="truncate font-medium">
            Stage {stage.id} — {stage.name}
            {stage.vendor ? (
              <span className="ml-1 text-muted-foreground">({stage.vendor})</span>
            ) : null}
          </span>
          {anyError ? (
            <span className="rounded bg-destructive/15 px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wide text-destructive">
              error
            </span>
          ) : null}
        </div>
        <div className="flex shrink-0 items-center gap-3 font-mono text-xs text-muted-foreground">
          {hasData && observations.length > 1 ? (
            <span>{observations.length}×</span>
          ) : null}
          <span>{durationLabel}</span>
        </div>
      </button>
      {open ? (
        <div className="space-y-3 border-t border-border p-3">
          <p className="text-sm text-muted-foreground">{stage.description}</p>
          {hasData ? (
            observations.map((obs, i) => (
              <ObservationDetail key={`${obs.name}-${i}`} obs={obs} />
            ))
          ) : (
            <p className="text-xs text-muted-foreground">
              {traceOk
                ? (stage.note ??
                  'No Langfuse observation for this stage on this query.')
                : 'Stage observations populate once trace data is available.'}
              {traceOk && stage.note && stage.obsPrefixes.length > 0
                ? ' (Not all queries exercise every stage.)'
                : ''}
            </p>
          )}
        </div>
      ) : null}
    </div>
  );
}

function ObservationDetail({ obs }: { obs: TraceStage }) {
  const tokenLine =
    obs.input_tokens || obs.output_tokens
      ? `${obs.input_tokens.toLocaleString()} in / ${obs.output_tokens.toLocaleString()} out`
      : null;
  const detailEntries = obs.details ? Object.entries(obs.details) : [];

  return (
    <div className="rounded-md bg-muted/40 p-3 text-xs">
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1 font-mono">
        <span className="font-medium text-foreground">{obs.name}</span>
        <span className="text-muted-foreground">{obs.type}</span>
        <span className="text-muted-foreground">{obs.latency_ms.toLocaleString()} ms</span>
        {obs.model ? <span className="text-muted-foreground">{obs.model}</span> : null}
        {tokenLine ? <span className="text-muted-foreground">{tokenLine}</span> : null}
        <span
          className={cn(
            'rounded px-1.5 py-0.5 uppercase tracking-wide',
            obs.status === 'error'
              ? 'bg-destructive/15 text-destructive'
              : obs.status === 'cancelled'
                ? 'bg-amber-500/15 text-amber-600'
                : 'bg-muted text-muted-foreground',
          )}
        >
          {obs.status}
        </span>
      </div>
      {detailEntries.length > 0 ? (
        <dl className="mt-2 grid grid-cols-[max-content_1fr] gap-x-3 gap-y-0.5 font-mono">
          {detailEntries.map(([k, v]) => (
            <div key={k} className="contents">
              <dt className="text-muted-foreground">{k}</dt>
              <dd className="break-all text-foreground">{String(v)}</dd>
            </div>
          ))}
        </dl>
      ) : null}
    </div>
  );
}
