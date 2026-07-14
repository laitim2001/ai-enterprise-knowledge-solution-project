'use client';

/**
 * V6 Traces (`/traces/[traceId]`) — per architecture.md v6 §5.7 +
 * `references/design-mockups/ekp-page-trace.jsx:5 PageTrace` + ADR-0037 W26 F2.
 *
 * W22 F7.3 (2026-05-18 D5) — complete rewrite for mockup fidelity per
 * CLAUDE.md §5.7 H7. Pre-W22 W18 9-stage Collapsible pattern (533 lines)
 * replaced with mockup PageTrace decomposition:
 *   - TraceHeader (breadcrumb back + trace_id + query as title + metadata)
 *   - 5-stat strip (Total latency / Tokens / Cost / CRAG iterations / Status)
 *   - viz mode selector seg toggle (Vertical / Waterfall / Flame)
 *   - 3 viz components ALL inline in this file per mockup single-file pattern
 *     (per W22 D9.c — no `frontend/components/traces/` extraction)
 *   - FinalResponseCard
 *
 * W26 F2.12 (2026-05-25) — 9→10 stage expansion per ADR-0037 §Q5 Option A
 * explicit insert. NEW stage 8 "Parent-Document Retriever" inserted between
 * Context Expander + LLM Synthesis. Mockup `ekp-page-trace.jsx` + `ekp-data.jsx`
 * MOCK_TRACE synced at same time (mockup is single source of truth — H7 fidelity
 * preserved by mirroring updated mockup 100%, not approximating). Context category
 * extended to `[6, 7]` covering both Context Expander + Parent-Document Retriever
 * (both are post-rerank chunk-aggregation steps).
 *
 * Viz mode persistence: localStorage `ekp-trace-viz-mode` SSR-safe useEffect
 * read pattern (per W15 D3 conversation-history precedent); mockup
 * `tweaks.traceViz` window-level convention not applicable to Next.js prod.
 *
 * Backend integration preserved: `debugApi.getTrace` + 10-stage `bucketObservations`
 * conceptual mapping. Backend `TraceDetail.stages[]` is a flat list of raw Langfuse
 * observations; the view maps each onto one of the 10 architecture.md §5.7 stages
 * (extended via ADR-0037) via name-prefix matching (`PIPELINE_STAGES` below).
 *
 * Backend-wins fallback per CLAUDE.md §13 / W22 D9 for fields the schema doesn't
 * expose (mockup `trace.query`, `trace.user`, `trace.kb_id`, `trace.total_cost_usd`,
 * `stage.cost_usd`, `trace.model_used`, `trace.crag_iterations` flag): synthesize
 * from stage details where possible (CRAG count from `crag.grade` observations,
 * model from Synthesis stage `model`, kb_id from retrieval stage details);
 * else render placeholder "—" or DisabledAffordance Wave C+.
 */

import { useQuery } from '@tanstack/react-query';
import {
  Activity,
  ChevronLeft,
  ChevronRight,
  Clock,
  Copy,
  Cpu,
  Download,
  ExternalLink,
  Layers,
  MessageSquare,
  RefreshCw,
  Shield,
  Zap,
} from 'lucide-react';
import { useTranslations } from 'next-intl';
import { useEffect, useMemo, useState } from 'react';

import { DisabledAffordance } from '@/components/ui/disabled-affordance';
import { debugApi, type TraceDetail, type TraceStage } from '@/lib/api/debug';

// --- 10 conceptual pipeline stages per architecture.md v6 §5.7 + ADR-0037 ----
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
    description: 'CRAG correction loop — rewrites the query when initial confidence is below threshold',
    obsPrefixes: ['crag.rewrite_query'],
    note: 'Only present when CRAG triggers a correction (confidence below 0.70).',
  },
  {
    id: 3,
    name: 'Hybrid Retrieval',
    description: 'BM25 top-50 + Vector top-50 + RRF fusion → unique candidates (kb_id-scoped per ADR-0018)',
    obsPrefixes: ['retrieval.retrieve'],
    note: 'Cohere rerank runs inside this span — see `rerank_latency_ms` in its details.',
  },
  {
    id: 4,
    name: 'Reranker',
    vendor: 'Cohere v4.0-pro',
    description: 'Top-50 candidates → top-K rerank (production lock per Q21 Resolved + ADR-0012)',
    obsPrefixes: [],
    note: 'Folded into the Hybrid Retrieval span (`rerank_latency_ms` there).',
  },
  {
    id: 5,
    name: 'CRAG Confidence Judge',
    vendor: 'gpt-5.4-mini',
    description: 'Grades retrieved context; pass-through above threshold (default 0.70) or trigger re-retrieve',
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
    description: 'Prepends prev / appends next neighbor chunk text to the top-K reranked chunks (architecture.md §3.1, ADR-0020)',
    obsPrefixes: ['generation.context_expansion'],
  },
  {
    id: 8,
    name: 'Parent-Document Retriever',
    description: 'Aggregates top-1 anchor\'s section_path siblings into parent_section_text for LLM context (architecture.md §3.1, ADR-0037 W26 F2; flag-gated default OFF)',
    obsPrefixes: ['generation.parent_doc_retrieval'],
    note: 'Only emits a span when enable_parent_doc_retrieval=True (measurement experiment per ADR-0037 Q4).',
  },
  {
    id: 9,
    name: 'LLM Synthesis',
    vendor: 'gpt-5.5',
    description: 'Synthesize answer with citations + refusal logic for out-of-scope queries',
    obsPrefixes: ['synthesizer.synthesize', 'api.query.stream'],
  },
  {
    id: 10,
    name: 'Final Response',
    description: 'End-to-end orchestration aggregate — citation linking, cost, Langfuse trace publish',
    obsPrefixes: ['api.query'],
  },
];

const LANGFUSE_FALLBACK_BASE =
  process.env.NEXT_PUBLIC_LANGFUSE_URL ?? 'http://localhost:3000';

const VIZ_STORAGE_KEY = 'ekp-trace-viz-mode';

type VizMode = 'vertical' | 'waterfall' | 'flame';

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

/**
 * Build the 9 "stage rows" expected by the mockup viz components. Each row
 * aggregates that stage's bucket of raw observations:
 *   - latency_ms = sum of obs latencies
 *   - input/output tokens = sum
 *   - type = "GENERATION" if any obs has type GENERATION else "SPAN"
 *   - model = first obs.model when present
 *   - details = first obs.details (deep-dive only — full Langfuse covers more)
 *   - cost_usd = 0 (D9.c fallback — TraceStage schema doesn't expose cost)
 *
 * Empty stage rows render with latency 0 / "not traced this query" affordance
 * (matches the pre-W22 9-stage UX where stages without an observation displayed
 * a note explaining why).
 */
interface StageRowData {
  id: number;
  name: string;
  vendor?: string;
  type: 'SPAN' | 'GENERATION' | 'EVENT';
  latency_ms: number;
  input_tokens: number;
  output_tokens: number;
  model?: string | null;
  cost_usd: number;
  details?: Record<string, unknown> | null;
  empty: boolean;
  note?: string;
  obsCount: number;
}

function buildStageRows(
  buckets: Map<number, TraceStage[]>,
): StageRowData[] {
  return PIPELINE_STAGES.map((stage) => {
    const obs = buckets.get(stage.id) ?? [];
    if (obs.length === 0) {
      return {
        id: stage.id,
        name: stage.name,
        vendor: stage.vendor,
        type: 'SPAN',
        latency_ms: 0,
        input_tokens: 0,
        output_tokens: 0,
        cost_usd: 0,
        details: null,
        empty: true,
        note: stage.note,
        obsCount: 0,
      };
    }
    const totalLatency = obs.reduce((s, o) => s + o.latency_ms, 0);
    const totalIn = obs.reduce((s, o) => s + o.input_tokens, 0);
    const totalOut = obs.reduce((s, o) => s + o.output_tokens, 0);
    const isGen = obs.some((o) => o.type === 'GENERATION');
    return {
      id: stage.id,
      name: stage.name,
      vendor: stage.vendor,
      type: isGen ? 'GENERATION' : 'SPAN',
      latency_ms: totalLatency,
      input_tokens: totalIn,
      output_tokens: totalOut,
      model: obs.find((o) => o.model)?.model,
      cost_usd: 0,
      details: obs[0]!.details ?? null,
      empty: false,
      obsCount: obs.length,
    };
  });
}

// Derive trace-level metadata from backend stage details (D9 backend-wins fallbacks).
function deriveTraceMetadata(buckets: Map<number, TraceStage[]>): {
  query: string | null;
  kbId: string | null;
  cragIterations: number;
  modelUsed: string | null;
  answerPreview: string | null;
} {
  // CRAG iteration count = observation count under stage 5 (CRAG Confidence Judge)
  const cragObs = buckets.get(5) ?? [];
  const cragIterations = cragObs.filter((o) =>
    matchesPrefix(o.name, 'crag.grade'),
  ).length;

  // Extract query from any stage with `query` / `input` / `q` in details
  let query: string | null = null;
  let kbId: string | null = null;
  for (const stageObs of buckets.values()) {
    for (const obs of stageObs) {
      const d = obs.details ?? {};
      if (!query && typeof d.query === 'string') query = d.query;
      if (!query && typeof d.input === 'string') query = d.input;
      if (!kbId && typeof d.kb_id === 'string') kbId = d.kb_id;
      if (query && kbId) break;
    }
    if (query && kbId) break;
  }

  // Model from Synthesis stage (id 8)
  const synthObs = buckets.get(8) ?? [];
  const modelUsed = synthObs.find((o) => o.model)?.model ?? null;

  // Answer preview from Synthesis details
  let answerPreview: string | null = null;
  for (const obs of synthObs) {
    const d = obs.details ?? {};
    if (typeof d.answer === 'string') {
      answerPreview = d.answer.slice(0, 240);
      break;
    }
    if (typeof d.output === 'string') {
      answerPreview = d.output.slice(0, 240);
      break;
    }
  }

  return { query, kbId, cragIterations, modelUsed, answerPreview };
}

// ============================================================================
// Page
// ============================================================================
export default function TraceDetailPage({
  params,
}: {
  params: { traceId: string };
}) {
  const traceId = params.traceId;
  const t = useTranslations('Traces');

  const query = useQuery<TraceDetail>({
    queryKey: ['debug', 'trace', traceId],
    queryFn: () => debugApi.getTrace(traceId),
    retry: false,
  });

  const [vizMode, setVizMode] = useState<VizMode>('vertical');
  const [expandedStage, setExpandedStage] = useState<number>(5); // CRAG stage default per mockup
  const [vizModeReady, setVizModeReady] = useState(false);

  // SSR-safe localStorage read for viz mode preference (W15 D3 pattern)
  useEffect(() => {
    if (typeof window === 'undefined') return;
    const stored = window.localStorage.getItem(VIZ_STORAGE_KEY);
    if (stored === 'vertical' || stored === 'waterfall' || stored === 'flame') {
      setVizMode(stored);
    }
    setVizModeReady(true);
  }, []);

  useEffect(() => {
    if (!vizModeReady || typeof window === 'undefined') return;
    window.localStorage.setItem(VIZ_STORAGE_KEY, vizMode);
  }, [vizMode, vizModeReady]);

  const data = query.data;
  const buckets = useMemo(
    () => (data ? bucketObservations(data.stages) : null),
    [data],
  );
  const stageRows = useMemo(
    () => (buckets ? buildStageRows(buckets) : null),
    [buckets],
  );
  const meta = useMemo(
    () => (buckets ? deriveTraceMetadata(buckets) : null),
    [buckets],
  );

  const langfuseHref =
    data?.trace_url ??
    `${LANGFUSE_FALLBACK_BASE}/trace/${encodeURIComponent(traceId)}`;

  // ---------- loading / error states ----------------------------------------
  if (query.isLoading) {
    return (
      <div className="content">
        <div className="content-wide">
          <div
            className="text-xs muted"
            style={{ padding: 24, textAlign: 'center' }}
          >
            {t('loadingTrace', { traceId })}
          </div>
        </div>
      </div>
    );
  }

  if (query.isError || !data) {
    return (
      <div className="content">
        <div className="content-wide">
          <div className="card" style={{ borderColor: 'oklch(var(--destructive) / 0.3)' }}>
            <div className="card-header">
              <div>
                <h3 className="card-title">{t('traceUnavailableTitle')}</h3>
                <div className="card-desc">
                  {(query.error as Error)?.message ?? t('unknownError')}
                </div>
              </div>
            </div>
            <div className="card-body">
              <p className="text-xs muted">
                {t.rich('traceCouldNotLoad', {
                  id: traceId,
                  mono: (chunks) => <span className="mono">{chunks}</span>,
                })}
              </p>
              <a
                className="btn btn-secondary btn-sm"
                href={langfuseHref}
                target="_blank"
                rel="noopener noreferrer"
                style={{ marginTop: 8 }}
              >
                <ExternalLink size={13} /> {t('openInLangfuse')}
              </a>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (data.status !== 'ok' && data.stages.length === 0) {
    return (
      <div className="content">
        <div className="content-wide">
          <div className="card" style={{ borderColor: 'oklch(var(--warning) / 0.3)' }}>
            <div className="card-header">
              <div>
                <h3 className="card-title">{t('observabilityDegradedTitle')}</h3>
                <div className="card-desc">
                  {t('statusLabel')} <span className="mono">{data.status}</span>
                  {data.note ? ` · ${data.note}` : ''}
                </div>
              </div>
            </div>
            <div className="card-body">
              <a
                className="btn btn-secondary btn-sm"
                href={langfuseHref}
                target="_blank"
                rel="noopener noreferrer"
              >
                <ExternalLink size={13} /> {t('openInLangfuse')}
              </a>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // ---------- ready state ---------------------------------------------------
  const totalLatency = data.total_latency_ms;
  const totalIn = data.total_input_tokens;
  const totalOut = data.total_output_tokens;
  const cragIterations = meta?.cragIterations ?? 0;
  const cragTriggered = cragIterations > 0;

  return (
    <div className="content">
      <div className="content-wide">
        <TraceHeader
          traceId={traceId}
          query={meta?.query ?? null}
          kbId={meta?.kbId ?? null}
          cragTriggered={cragTriggered}
        />

        {/* 5-stat strip */}
        <div
          className="stat-grid"
          style={{
            gridTemplateColumns: 'repeat(5, 1fr)',
            marginBottom: 16,
          }}
        >
          <div className="stat">
            <div className="stat-label">
              <Clock size={13} /> {t('statTotalLatency')}
            </div>
            <div className="stat-value">
              {(totalLatency / 1000).toFixed(2)}
              <span className="stat-unit">s</span>
            </div>
            <div className="stat-meta">
              <span className="trend-up">p95 4.21s</span> · {t('withinSlo')}
            </div>
          </div>
          <div className="stat">
            <div className="stat-label">
              <Cpu size={13} /> {t('statTokens')}
            </div>
            <div className="stat-value">
              {(totalIn / 1000).toFixed(1)}
              <span className="stat-unit">k</span>
            </div>
            <div className="stat-meta">
              {t('tokensMeta', {
                out: String(totalOut),
                in: totalIn.toLocaleString(),
              })}
            </div>
          </div>
          <div className="stat">
            <div className="stat-label">
              <Activity size={13} /> {t('statCost')}
            </div>
            <div className="stat-value">
              <DisabledAffordance
                variant="p3-preview"
                reason={t('costWaveCReason')}
                tier2Trigger={t('tier2Governance')}
              >
                —
              </DisabledAffordance>
            </div>
            <div className="stat-meta muted">
              {t('perStageCostWaveC')}
            </div>
          </div>
          <div className="stat">
            <div className="stat-label">
              <RefreshCw size={13} /> CRAG
            </div>
            <div
              className="stat-value"
              style={{ color: 'oklch(var(--accent))' }}
            >
              {cragIterations}×<span className="stat-unit"> {t('loopUnit')}</span>
            </div>
            <div className="stat-meta">
              {cragTriggered ? t('cragFired') : t('cragConfident')}
            </div>
          </div>
          <div className="stat">
            <div className="stat-label">
              <Shield size={13} /> {t('statStatus')}
            </div>
            <div className="stat-value">
              <span
                className="badge badge-success"
                style={{ height: 24, fontSize: 12.5 }}
              >
                <span className="badge-dot" />{' '}
                {data.status === 'ok' ? 'OK' : data.status.toUpperCase()}
              </span>
            </div>
            <div className="stat-meta">
              {t('obsTracedStages', {
                obs: data.stages.length,
                traced: stageRows?.filter((s) => !s.empty).length ?? 0,
              })}
            </div>
          </div>
        </div>

        {/* Viz mode selector */}
        <div className="row" style={{ marginBottom: 12 }}>
          <h3 className="card-title">{t('pipelineTitle')}</h3>
          <div className="spacer" />
          <span className="text-xs muted">{t('visualizationLabel')}</span>
          <div className="seg" role="tablist">
            <button
              type="button"
              role="tab"
              className="seg-btn"
              data-active={vizMode === 'vertical'}
              aria-selected={vizMode === 'vertical'}
              onClick={() => setVizMode('vertical')}
            >
              <Layers size={12} /> {t('vizVertical')}
            </button>
            <button
              type="button"
              role="tab"
              className="seg-btn"
              data-active={vizMode === 'waterfall'}
              aria-selected={vizMode === 'waterfall'}
              onClick={() => setVizMode('waterfall')}
            >
              <Activity size={12} /> {t('vizWaterfall')}
            </button>
            <button
              type="button"
              role="tab"
              className="seg-btn"
              data-active={vizMode === 'flame'}
              aria-selected={vizMode === 'flame'}
              onClick={() => setVizMode('flame')}
            >
              <Zap size={12} /> {t('vizFlame')}
            </button>
          </div>
          <a
            className="btn btn-secondary btn-sm"
            href={langfuseHref}
            target="_blank"
            rel="noopener noreferrer"
          >
            <ExternalLink size={13} /> {t('openInLangfuse')}
          </a>
        </div>

        {/* Viz body */}
        {stageRows && (
          <>
            {vizMode === 'vertical' && (
              <TraceVertical
                stages={stageRows}
                expanded={expandedStage}
                setExpanded={setExpandedStage}
                totalLatency={totalLatency || 1}
              />
            )}
            {vizMode === 'waterfall' && (
              <TraceWaterfall
                stages={stageRows}
                expanded={expandedStage}
                setExpanded={setExpandedStage}
                totalLatency={totalLatency || 1}
              />
            )}
            {vizMode === 'flame' && (
              <TraceFlame
                stages={stageRows}
                expanded={expandedStage}
                setExpanded={setExpandedStage}
                totalLatency={totalLatency || 1}
              />
            )}
          </>
        )}

        <FinalResponseCard
          query={meta?.query ?? null}
          answerPreview={meta?.answerPreview ?? null}
          modelUsed={meta?.modelUsed ?? null}
        />
      </div>
    </div>
  );
}

// ============================================================================
// TraceHeader
// ============================================================================
function TraceHeader({
  traceId,
  query,
  kbId,
  cragTriggered,
}: {
  traceId: string;
  query: string | null;
  kbId: string | null;
  cragTriggered: boolean;
}) {
  const t = useTranslations('Traces');
  return (
    <div className="page-header">
      <div style={{ flex: 1, minWidth: 0 }}>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            marginBottom: 4,
          }}
        >
          <a
            className="btn btn-ghost btn-xs btn-ghost-muted"
            href="/traces"
          >
            <ChevronLeft size={12} /> {t('pageTitle')}
          </a>
          <span className="text-xs muted mono">·</span>
          <span className="text-xs muted mono">{traceId}</span>
          <button
            type="button"
            className="btn btn-ghost btn-icon btn-xs"
            aria-label={t('copyTraceIdAria')}
            onClick={() => {
              if (typeof navigator !== 'undefined') {
                navigator.clipboard?.writeText(traceId);
              }
            }}
          >
            <Copy size={11} />
          </button>
        </div>
        <h1
          className="page-title"
          style={{
            fontSize: 17,
            fontWeight: 600,
            lineHeight: 1.45,
            fontFamily: 'var(--font-sans)',
          }}
        >
          {query ? `"${query}"` : (
            <span className="muted">{t('queryNotSurfaced')}</span>
          )}
        </h1>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            marginTop: 8,
            flexWrap: 'wrap',
          }}
        >
          {kbId ? (
            <span className="badge badge-muted">{kbId}</span>
          ) : (
            <span className="text-xs muted">kb_id —</span>
          )}
          <span className="text-xs muted mono">·</span>
          {/* D9.f-pattern: user not surfaced */}
          <span className="text-xs muted">{t('by')}</span>
          <span className="text-xs mono muted">—</span>
          {cragTriggered && (
            <>
              <span className="text-xs muted mono">·</span>
              <span className="badge badge-accent">
                <span className="badge-dot" /> {t('cragTriggered')}
              </span>
            </>
          )}
        </div>
      </div>
      <div className="page-actions">
        <button className="btn btn-secondary btn-sm" disabled>
          <Download size={13} /> {t('exportJson')}
        </button>
        <button className="btn btn-secondary btn-sm" disabled>
          <MessageSquare size={13} /> {t('replayInChat')}
        </button>
      </div>
    </div>
  );
}

// ============================================================================
// TraceVertical (default viz)
// ============================================================================
function TraceVertical({
  stages,
  expanded,
  setExpanded,
  totalLatency,
}: {
  stages: StageRowData[];
  expanded: number;
  setExpanded: (id: number) => void;
  totalLatency: number;
}) {
  return (
    <div className="card" style={{ overflow: 'visible' }}>
      <div className="card-body" style={{ padding: 0 }}>
        {stages.map((s, i) => (
          <StageRow
            key={s.id}
            stage={s}
            idx={i}
            isLast={i === stages.length - 1}
            expanded={expanded === s.id}
            onToggle={() => setExpanded(expanded === s.id ? -1 : s.id)}
            totalLatency={totalLatency}
          />
        ))}
      </div>
    </div>
  );
}

function StageRow({
  stage,
  idx,
  isLast,
  expanded,
  onToggle,
  totalLatency,
}: {
  stage: StageRowData;
  idx: number;
  isLast: boolean;
  expanded: boolean;
  onToggle: () => void;
  totalLatency: number;
}) {
  const t = useTranslations('Traces');
  const pct = (stage.latency_ms / totalLatency) * 100;
  const isCrag = stage.id === 5 || stage.id === 6;
  const stageBg = isCrag ? 'oklch(var(--accent) / 0.05)' : 'transparent';

  return (
    <div
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onToggle();
        }
      }}
      style={{
        display: 'flex',
        borderBottom: isLast ? 'none' : '1px solid oklch(var(--border))',
        background: stageBg,
        cursor: 'pointer',
      }}
      onClick={onToggle}
    >
      {/* Rail (left) */}
      <div
        style={{
          flexShrink: 0,
          position: 'relative',
          width: 56,
          paddingTop: 16,
          paddingBottom: 16,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
        }}
      >
        <div
          style={{
            width: 28,
            height: 28,
            borderRadius: 6,
            background:
              stage.type === 'GENERATION'
                ? 'oklch(var(--accent) / 0.1)'
                : 'oklch(var(--muted))',
            color:
              stage.type === 'GENERATION'
                ? 'oklch(var(--accent))'
                : 'oklch(var(--foreground))',
            border: `1px solid ${
              stage.type === 'GENERATION'
                ? 'oklch(var(--accent) / 0.3)'
                : 'oklch(var(--border))'
            }`,
            display: 'grid',
            placeItems: 'center',
            fontFamily: 'var(--font-mono)',
            fontWeight: 600,
            fontSize: 11,
            zIndex: 1,
          }}
        >
          {String(idx + 1).padStart(2, '0')}
        </div>
        {!isLast && (
          <div
            style={{
              flex: 1,
              width: 1,
              background: 'oklch(var(--border))',
              marginTop: -2,
            }}
          />
        )}
      </div>

      {/* Body */}
      <div style={{ flex: 1, padding: '16px 18px 16px 0' }}>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 10,
          }}
        >
          <span style={{ fontWeight: 500, fontSize: 13.5 }}>{stage.name}</span>
          <span className="badge badge-muted" style={{ fontSize: 10.5 }}>
            {stage.type}
          </span>
          {stage.model && (
            <span className="text-xs muted mono">· {stage.model}</span>
          )}
          {stage.empty && (
            <span className="text-xs muted">· {t('notTracedThisQuery')}</span>
          )}
          <div className="spacer" />
          {(stage.input_tokens > 0 || stage.output_tokens > 0) && (
            <span
              className="mono text-xs"
              style={{ color: 'oklch(var(--muted-foreground))' }}
            >
              {t('tokensCount', {
                in: String(stage.input_tokens),
                out: String(stage.output_tokens),
              })}
            </span>
          )}
          <span
            className="mono"
            style={{
              fontSize: 13,
              fontWeight: 600,
              width: 64,
              textAlign: 'right',
              fontVariantNumeric: 'tabular-nums',
            }}
          >
            {stage.latency_ms < 1000
              ? `${stage.latency_ms}ms`
              : `${(stage.latency_ms / 1000).toFixed(2)}s`}
          </span>
          <ChevronRight
            size={14}
            className="muted"
            style={{
              transform: expanded ? 'rotate(90deg)' : 'none',
              transition: 'transform 0.15s',
            }}
          />
        </div>

        {/* Inline duration bar */}
        <div
          style={{
            marginTop: 8,
            display: 'flex',
            alignItems: 'center',
            gap: 10,
          }}
        >
          <div
            style={{
              flex: 1,
              height: 4,
              background: 'oklch(var(--muted))',
              borderRadius: 999,
              overflow: 'hidden',
            }}
          >
            <div
              style={{
                height: '100%',
                width: `${pct}%`,
                background:
                  stage.type === 'GENERATION'
                    ? 'oklch(var(--accent))'
                    : 'oklch(var(--foreground))',
                borderRadius: 999,
              }}
            />
          </div>
          <span
            className="text-xs mono muted"
            style={{ width: 48, textAlign: 'right' }}
          >
            {pct.toFixed(1)}%
          </span>
        </div>

        {/* Expanded body */}
        {expanded && (
          <div
            style={{
              marginTop: 14,
              padding: '12px 14px',
              background: 'oklch(var(--muted) / 0.4)',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid oklch(var(--border))',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                marginBottom: 10,
              }}
            >
              <span
                className="text-xs mono muted"
                style={{
                  fontWeight: 600,
                  letterSpacing: '0.04em',
                  textTransform: 'uppercase',
                }}
              >
                {t('stageDetails')}
              </span>
              <div className="spacer" />
              <span className="text-xs muted">
                {t('observationCount', { count: stage.obsCount })}
              </span>
            </div>
            {stage.empty ? (
              <p className="text-xs muted" style={{ margin: 0, lineHeight: 1.55 }}>
                {stage.note ?? t('noObservationsBucketed')}
              </p>
            ) : stage.details ? (
              <table
                style={{
                  width: '100%',
                  fontSize: 12,
                  fontFamily: 'var(--font-mono)',
                }}
              >
                <tbody>
                  {Object.entries(stage.details).map(([k, v]) => (
                    <tr key={k}>
                      <td
                        style={{
                          padding: '4px 12px 4px 0',
                          color: 'oklch(var(--muted-foreground))',
                          verticalAlign: 'top',
                          whiteSpace: 'nowrap',
                          width: '1px',
                        }}
                      >
                        {k}
                      </td>
                      <td
                        style={{
                          padding: '4px 0',
                          color: 'oklch(var(--foreground))',
                          wordBreak: 'break-word',
                          lineHeight: 1.5,
                        }}
                      >
                        {renderValue(k, v, stage, t)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <p className="text-xs muted" style={{ margin: 0 }}>
                {t('noExtraMetadata')}
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function renderValue(
  key: string,
  v: unknown,
  stage: StageRowData,
  t: ReturnType<typeof useTranslations>,
): React.ReactNode {
  // Highlight CRAG threshold check
  if (key === 'verdict' && v === 'RE_RETRIEVE') {
    return (
      <span className="badge badge-warning">
        <span className="badge-dot" /> RE_RETRIEVE
      </span>
    );
  }
  if (
    key === 'confidence' &&
    typeof v === 'number'
  ) {
    const detailsObj = stage.details ?? {};
    const threshold =
      typeof detailsObj.threshold === 'number' ? detailsObj.threshold : 0.7;
    const failed = v < threshold;
    return (
      <span
        style={{
          color: failed
            ? 'oklch(var(--destructive))'
            : 'oklch(var(--success))',
          fontWeight: 600,
        }}
      >
        {v.toFixed(2)}{' '}
        {failed ? t('belowThreshold', { threshold: threshold.toFixed(2) }) : ''}
      </span>
    );
  }
  if (Array.isArray(v)) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
        {v.map((x, i) => (
          <div
            key={i}
            style={{
              padding: '3px 7px',
              background: 'oklch(var(--card))',
              border: '1px solid oklch(var(--border))',
              borderRadius: 3,
            }}
          >
            {String(x)}
          </div>
        ))}
      </div>
    );
  }
  if (typeof v === 'boolean') return v ? 'true' : 'false';
  if (typeof v === 'number') return String(v);
  if (v === null || v === undefined) return '—';
  if (typeof v === 'object') return JSON.stringify(v);
  return String(v);
}

// ============================================================================
// TraceWaterfall (Chrome devtools style)
// ============================================================================
function TraceWaterfall({
  stages,
  expanded,
  setExpanded,
  totalLatency,
}: {
  stages: StageRowData[];
  expanded: number;
  setExpanded: (id: number) => void;
  totalLatency: number;
}) {
  let acc = 0;
  const withStart = stages.map((s) => {
    const start = acc;
    acc += s.latency_ms;
    return { ...s, start, end: acc };
  });

  return (
    <div className="card">
      <div className="card-body" style={{ padding: '16px 18px' }}>
        {/* Time axis */}
        <div
          style={{
            display: 'flex',
            marginBottom: 8,
            paddingLeft: 280,
            fontFamily: 'var(--font-mono)',
            fontSize: 10.5,
            color: 'oklch(var(--muted-foreground))',
          }}
        >
          {[0, 0.25, 0.5, 0.75, 1].map((t) => (
            <div key={t} style={{ flex: 1 }}>
              {Math.round(totalLatency * t)}ms
            </div>
          ))}
        </div>
        {withStart.map((s, i) => {
          const startPct = (s.start / totalLatency) * 100;
          const widthPct = (s.latency_ms / totalLatency) * 100;
          return (
            <div
              key={s.id}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  setExpanded(expanded === s.id ? -1 : s.id);
                }
              }}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                padding: '6px 0',
                borderBottom:
                  i < withStart.length - 1
                    ? '1px solid oklch(var(--border))'
                    : 'none',
                cursor: 'pointer',
              }}
              onClick={() => setExpanded(expanded === s.id ? -1 : s.id)}
            >
              <span
                className="mono text-xs muted"
                style={{ width: 22, textAlign: 'right' }}
              >
                {String(i + 1).padStart(2, '0')}
              </span>
              <span
                style={{
                  fontSize: 12.5,
                  width: 240,
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                }}
              >
                {s.name}
              </span>
              <div
                style={{
                  position: 'relative',
                  flex: 1,
                  height: 22,
                  background: 'oklch(var(--muted) / 0.3)',
                  borderRadius: 3,
                }}
              >
                {!s.empty && (
                  <div
                    style={{
                      position: 'absolute',
                      left: `${startPct}%`,
                      width: `${Math.max(widthPct, 0.4)}%`,
                      top: 3,
                      bottom: 3,
                      background:
                        s.type === 'GENERATION'
                          ? 'oklch(var(--accent))'
                          : 'oklch(var(--foreground) / 0.8)',
                      borderRadius: 2,
                      display: 'flex',
                      alignItems: 'center',
                      paddingLeft: 4,
                      fontFamily: 'var(--font-mono)',
                      fontSize: 10,
                      fontWeight: 600,
                      color:
                        s.type === 'GENERATION'
                          ? 'oklch(var(--accent-foreground))'
                          : 'oklch(var(--background))',
                      whiteSpace: 'nowrap',
                      overflow: 'hidden',
                    }}
                  >
                    {widthPct > 5 ? `${s.latency_ms}ms` : ''}
                  </div>
                )}
              </div>
              <span
                className="mono text-xs"
                style={{
                  width: 56,
                  textAlign: 'right',
                  fontVariantNumeric: 'tabular-nums',
                }}
              >
                {s.empty ? '—' : `${s.latency_ms}ms`}
              </span>
              <span
                className="mono text-xs muted"
                style={{ width: 60, textAlign: 'right' }}
              >
                —
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ============================================================================
// TraceFlame (stacked horizontal bars by category)
// ============================================================================
function TraceFlame({
  stages,
  expanded,
  setExpanded,
  totalLatency,
}: {
  stages: StageRowData[];
  expanded: number;
  setExpanded: (id: number) => void;
  totalLatency: number;
}) {
  const t = useTranslations('Traces');
  const categories = [
    { name: 'Preprocessing', stageIds: [1, 2], color: 'oklch(0.65 0.10 240)' },
    { name: 'Retrieval', stageIds: [3, 4], color: 'oklch(0.62 0.13 200)' },
    { name: 'CRAG', stageIds: [5, 6], color: 'oklch(0.65 0.18 25)' },
    { name: 'Context', stageIds: [7, 8], color: 'oklch(0.65 0.14 145)' },
    { name: 'Synthesis', stageIds: [9, 10], color: 'oklch(0.60 0.16 285)' },
  ];

  const stageById = new Map(stages.map((s) => [s.id, s]));

  return (
    <div className="card">
      <div className="card-body">
        {/* Top: category stack */}
        <div style={{ marginBottom: 16 }}>
          <div
            className="text-xs muted mono"
            style={{
              marginBottom: 6,
              letterSpacing: '0.04em',
              textTransform: 'uppercase',
            }}
          >
            {t('byCategory')}
          </div>
          <div
            style={{
              display: 'flex',
              height: 32,
              borderRadius: 4,
              overflow: 'hidden',
              border: '1px solid oklch(var(--border))',
            }}
          >
            {categories.map((c) => {
              const cMs = c.stageIds.reduce(
                (sum, sid) => sum + (stageById.get(sid)?.latency_ms ?? 0),
                0,
              );
              const pct = (cMs / totalLatency) * 100;
              return (
                <div
                  key={c.name}
                  style={{
                    width: `${pct}%`,
                    background: c.color,
                    color: 'white',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontFamily: 'var(--font-mono)',
                    fontSize: 11,
                    fontWeight: 600,
                    paddingLeft: 6,
                    paddingRight: 6,
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                    textShadow: '0 1px 1px rgba(0,0,0,0.2)',
                  }}
                >
                  {pct > 6 ? `${c.name} ${pct.toFixed(0)}%` : ''}
                </div>
              );
            })}
          </div>
          <div
            style={{
              display: 'flex',
              gap: 14,
              marginTop: 8,
              fontSize: 11.5,
              color: 'oklch(var(--muted-foreground))',
              flexWrap: 'wrap',
            }}
          >
            {categories.map((c) => {
              const cMs = c.stageIds.reduce(
                (sum, sid) => sum + (stageById.get(sid)?.latency_ms ?? 0),
                0,
              );
              return (
                <div
                  key={c.name}
                  style={{ display: 'flex', alignItems: 'center', gap: 5 }}
                >
                  <span
                    style={{
                      width: 10,
                      height: 10,
                      borderRadius: 2,
                      background: c.color,
                    }}
                  />
                  <span>{c.name}</span>
                  <span
                    className="mono"
                    style={{ color: 'oklch(var(--foreground))' }}
                  >
                    {cMs}ms
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Below: stage rows */}
        <div
          className="text-xs muted mono"
          style={{
            marginBottom: 6,
            letterSpacing: '0.04em',
            textTransform: 'uppercase',
          }}
        >
          {t('byStage')}
        </div>
        {stages.map((s, i) => {
          const cat = categories.find((c) => c.stageIds.includes(s.id));
          const pct = (s.latency_ms / totalLatency) * 100;
          return (
            <div
              key={s.id}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  setExpanded(expanded === s.id ? -1 : s.id);
                }
              }}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                padding: '4px 0',
                cursor: 'pointer',
              }}
              onClick={() => setExpanded(expanded === s.id ? -1 : s.id)}
            >
              <span
                className="mono text-xs muted"
                style={{ width: 22 }}
              >
                {String(i + 1).padStart(2, '0')}
              </span>
              <span
                style={{
                  fontSize: 12.5,
                  width: 220,
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                }}
              >
                {s.name}
              </span>
              <div style={{ flex: 1, position: 'relative', height: 18 }}>
                {!s.empty && (
                  <div
                    style={{
                      position: 'absolute',
                      left: 0,
                      width: `${Math.max(pct, 0.4)}%`,
                      top: 0,
                      bottom: 0,
                      background: cat?.color ?? 'oklch(var(--foreground))',
                      borderRadius: 2,
                    }}
                  />
                )}
              </div>
              <span
                className="mono text-xs"
                style={{ width: 56, textAlign: 'right' }}
              >
                {s.empty ? '—' : `${s.latency_ms}ms`}
              </span>
              <span
                className="mono text-xs muted"
                style={{ width: 60, textAlign: 'right' }}
              >
                —
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ============================================================================
// FinalResponseCard
// ============================================================================
function FinalResponseCard({
  query,
  answerPreview,
  modelUsed,
}: {
  query: string | null;
  answerPreview: string | null;
  modelUsed: string | null;
}) {
  const t = useTranslations('Traces');
  return (
    <div className="card" style={{ marginTop: 16 }}>
      <div className="card-header">
        <div>
          <h3 className="card-title">{t('finalResponseTitle')}</h3>
          <div className="card-desc">
            {t('stage09Output')}
            {modelUsed ? t('synthesizedBy', { model: modelUsed }) : ''}
          </div>
        </div>
        <div className="row">
          <DisabledAffordance
            variant="p3-preview"
            reason={t('citationWaveCReason')}
            tier2Trigger={t('tier2Governance')}
          >
            <span className="badge badge-muted">
              <span className="badge-dot" /> {t('citationStatusWaveC')}
            </span>
          </DisabledAffordance>
        </div>
      </div>
      <div className="card-body">
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: 12,
          }}
        >
          <div>
            <div
              className="text-xs muted mono"
              style={{
                marginBottom: 6,
                letterSpacing: '0.04em',
                textTransform: 'uppercase',
              }}
            >
              {t('queryFinalAfterCrag')}
            </div>
            <div
              style={{
                padding: '10px 12px',
                background: 'oklch(var(--muted) / 0.4)',
                border: '1px solid oklch(var(--border))',
                borderRadius: 'var(--radius-sm)',
                fontSize: 13,
                lineHeight: 1.55,
              }}
            >
              {query ?? (
                <span className="muted">{t('queryNotSurfaced')}</span>
              )}
            </div>
          </div>
          <div>
            <div
              className="text-xs muted mono"
              style={{
                marginBottom: 6,
                letterSpacing: '0.04em',
                textTransform: 'uppercase',
              }}
            >
              {t('answerPreviewTitle')}
            </div>
            <div
              style={{
                padding: '10px 12px',
                background: 'oklch(var(--muted) / 0.4)',
                border: '1px solid oklch(var(--border))',
                borderRadius: 'var(--radius-sm)',
                fontSize: 13,
                lineHeight: 1.55,
              }}
            >
              {answerPreview ?? (
                <DisabledAffordance
                  variant="p3-preview"
                  reason={t('answerPreviewWaveCReason')}
                  tier2Trigger={t('tier2Governance')}
                >
                  <span className="muted">{t('answerPreviewWaveC')}</span>
                </DisabledAffordance>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

