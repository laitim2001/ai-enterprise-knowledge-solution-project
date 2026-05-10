'use client';

/**
 * V5 Eval Console (`/eval`) — per architecture.md v6 §5.6 view 5 + design ref
 * §2.5 wireframe.
 *
 * W15 D1 F1 implementation — NEW build replacing W1 skeleton placeholder.
 * Layout: top filter bar + 2-column (Run config card + main panel with
 * 4-metric cards + Failed queries table + W4 Reranker Shootout table).
 *
 * F1 deviations logged plan §7 changelog 2026-06-10 (D1):
 * 1. Plan F1.1 "rebuild from W12 F4.5 baseline" — actual baseline = W1
 *    skeleton 15-line placeholder; effective NEW implementation per Karpathy
 *    §1.1 think-before-coding upfront verification.
 * 2. Plan F1.3 "Context Relevancy / Answer Relevancy" — schema + design ref
 *    §2.5 wireframe agree on Correctness / Image Association; align with
 *    spec (4 metrics: R@5 / FFul / CRct / IAss).
 * 3. Plan F1.3 4-metric data display — backend /eval/run returns 501 stub →
 *    stub mitigation pattern (empty state + Run CTA + ApiError 501 →
 *    toast.info) per W14 BackendStubNote pattern.
 * 4. Plan F1.5 "static JSON file" — no `reranker_shootout*` artifact exists;
 *    inline RERANKER_SHOOTOUT const populated from W6 demo-prep.md §107-114
 *    Q-A2 stakeholder Q&A actual W6 D1 LIVE Azure 2-way comparison data.
 * 5. Plan F1.5 "4-way comparison" — W4 Karpathy §1.2 simplicity drop made it
 *    effective 2-way (Cohere vs Azure built-in); Voyage + ZeroEntropy DROPPED
 *    Tier 1 per W4 retro. Table shows 2 active + 2 dropped rows w/ rationale.
 */

import { useMutation } from '@tanstack/react-query';
import {
  AlertCircle,
  CheckCircle2,
  ExternalLink,
  Play,
  PlayCircle,
} from 'lucide-react';
import Link from 'next/link';
import { useState } from 'react';
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
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Skeleton } from '@/components/ui/skeleton';
import { Slider } from '@/components/ui/slider';
import { ApiError } from '@/lib/api-client';
import {
  evalApi,
  type EvalReport,
  type EvalRunRequest,
} from '@/lib/api/eval';
import { cn } from '@/lib/utils';

// 4-metric thresholds (Tier 1 strict acceptance per architecture.md §6.3 +
// W6 retro). Recall@5 ≥ 0.80 = Gate 1 W2 末; others ≥ 0.85 = Tier 1 strict
// per W6 retro "rel 0.803 still below 0.85 Tier 1 strict-acceptance".
const METRIC_THRESHOLDS = {
  recall_at_5: 0.8,
  faithfulness: 0.85,
  correctness: 0.85,
  image_association: 0.85,
} as const;

const METRIC_LABELS = {
  recall_at_5: { full: 'Recall@5', short: 'R@5' },
  faithfulness: { full: 'Faithfulness', short: 'FFul' },
  correctness: { full: 'Correctness', short: 'CRct' },
  image_association: { full: 'Image Association', short: 'IAss' },
} as const;

type MetricKey = keyof typeof METRIC_THRESHOLDS;

const METRIC_ORDER: MetricKey[] = [
  'recall_at_5',
  'faithfulness',
  'correctness',
  'image_association',
];

interface RerankerRow {
  vendor: string;
  faithfulness: number | null;
  answer_relevancy: number | null;
  recommendation: string;
  status: 'recommended' | 'fallback' | 'dropped';
}

// W4-W6 Reranker Shootout — historical W6 D1 LIVE Azure 2-way comparison.
// Per W6 demo-prep.md §107-114 (Q-A2 stakeholder Q&A). Voyage + ZeroEntropy
// DROPPED Tier 1 per W4 Karpathy §1.2 simplicity drop (W4 retro).
// Cohere v4.0-pro production lock per Q21 Resolved (ADR-0012 reservation).
const RERANKER_SHOOTOUT: RerankerRow[] = [
  {
    vendor: 'Cohere v4.0-pro',
    faithfulness: 1.0,
    answer_relevancy: 0.841,
    recommendation:
      'Production lock per Q21 Resolved (Azure Marketplace billing Path A)',
    status: 'recommended',
  },
  {
    vendor: 'Azure built-in semantic',
    faithfulness: 0.882,
    answer_relevancy: 0.743,
    recommendation:
      'Hot fallback for Cohere outage (Settings.reranker_kind=azure flag)',
    status: 'fallback',
  },
  {
    vendor: 'Voyage Rerank',
    faithfulness: null,
    answer_relevancy: null,
    recommendation: 'DROPPED Tier 1 per W4 Karpathy §1.2 simplicity drop',
    status: 'dropped',
  },
  {
    vendor: 'ZeroEntropy',
    faithfulness: null,
    answer_relevancy: null,
    recommendation: 'DROPPED Tier 1 per W4 Karpathy §1.2 simplicity drop',
    status: 'dropped',
  },
];

interface RunConfig {
  llm_model: string;
  reranker: string;
  top_k: number;
  crag_threshold: number;
  intent_type: string;
}

const DEFAULT_CONFIG: RunConfig = {
  llm_model: 'gpt-5.5',
  reranker: 'cohere-v4.0-pro',
  top_k: 5,
  crag_threshold: 0.7,
  intent_type: 'auto',
};

export default function EvalConsolePage() {
  const [evalSetId, setEvalSetId] = useState('eval-set-v0');
  const [config, setConfig] = useState<RunConfig>(DEFAULT_CONFIG);
  const [report, setReport] = useState<EvalReport | null>(null);

  const runMutation = useMutation<EvalReport, Error, EvalRunRequest>({
    mutationFn: (payload) => evalApi.run(payload),
    onSuccess: (data) => {
      setReport(data);
      toast.success('Eval run complete');
    },
    onError: (err) => {
      if (err instanceof ApiError && err.status === 501) {
        toast.info('Eval run pending W4 backend implementation', {
          description: 'docs/eval-methodology.md',
        });
        return;
      }
      toast.error('Eval run failed', {
        description: err.message,
      });
    },
  });

  const handleRun = () => {
    runMutation.mutate({
      eval_set_id: evalSetId,
      llm_model: config.llm_model,
      reranker: config.reranker,
      enable_crag: true,
    });
  };

  const handleRunSingle = () => {
    toast.info('Run Single — pending V6 Debug View integration', {
      description: 'W15 D2 F2 deliverable',
    });
  };

  return (
    <div className="space-y-6">
      <header className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">
            Evaluation Console
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Run RAGAs eval over the chosen eval set + reranker config (per
            architecture.md v6 §5.6).
          </p>
        </div>
      </header>

      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <div className="flex-1 sm:flex-initial">
          <Label htmlFor="eval-set" className="sr-only">
            Eval set
          </Label>
          <Select value={evalSetId} onValueChange={setEvalSetId}>
            <SelectTrigger id="eval-set" className="w-full sm:w-72">
              <SelectValue placeholder="Eval set" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="eval-set-v0">
                eval-set-v0 (W2 baseline 30 queries)
              </SelectItem>
              <SelectItem value="eval-set-v1">
                eval-set-v1 (W4+W5 +20 real-query 50 queries)
              </SelectItem>
            </SelectContent>
          </Select>
        </div>
        <Button onClick={handleRun} disabled={runMutation.isPending}>
          <Play className="mr-2 h-4 w-4" />
          {runMutation.isPending ? 'Running…' : 'Run'}
        </Button>
        <Button variant="outline" onClick={handleRunSingle}>
          <PlayCircle className="mr-2 h-4 w-4" />
          Run Single
        </Button>
      </div>

      <div className="grid gap-6 md:grid-cols-[280px_1fr]">
        <RunConfigCard config={config} onChange={setConfig} />
        <div className="min-w-0 space-y-6">
          <MetricCardsGrid report={report} loading={runMutation.isPending} />
          <FailedQueriesCard failures={report?.failed_queries ?? []} />
          <RerankerShootoutCard />
        </div>
      </div>
    </div>
  );
}

function RunConfigCard({
  config,
  onChange,
}: {
  config: RunConfig;
  onChange: (next: RunConfig) => void;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Run config</CardTitle>
        <CardDescription>Tune RAGAs evaluation parameters</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="llm-model">LLM</Label>
          <Select
            value={config.llm_model}
            onValueChange={(v) => onChange({ ...config, llm_model: v })}
          >
            <SelectTrigger id="llm-model">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="gpt-5.5">gpt-5.5</SelectItem>
              <SelectItem value="gpt-5.4-mini">
                gpt-5.4-mini (judge)
              </SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-2">
          <Label htmlFor="reranker">Reranker</Label>
          <Select
            value={config.reranker}
            onValueChange={(v) => onChange({ ...config, reranker: v })}
          >
            <SelectTrigger id="reranker">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="cohere-v4.0-pro">Cohere v4.0-pro</SelectItem>
              <SelectItem value="cohere-v3.5">Cohere v3.5</SelectItem>
              <SelectItem value="azure-builtin">Azure built-in</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-2">
          <Label htmlFor="top-k">Top K</Label>
          <Input
            id="top-k"
            type="number"
            min={1}
            max={50}
            value={config.top_k}
            onChange={(e) =>
              onChange({ ...config, top_k: Number(e.target.value) || 1 })
            }
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="crag">CRAG threshold</Label>
          <Slider
            id="crag"
            min={0}
            max={1}
            step={0.05}
            value={[config.crag_threshold]}
            onValueChange={(v) =>
              onChange({ ...config, crag_threshold: v[0] ?? 0 })
            }
          />
          <p className="text-xs text-muted-foreground">
            {config.crag_threshold.toFixed(2)} · re-retrieve below threshold
          </p>
        </div>
        <div className="space-y-2">
          <Label htmlFor="intent">Intent type</Label>
          <Select
            value={config.intent_type}
            onValueChange={(v) => onChange({ ...config, intent_type: v })}
          >
            <SelectTrigger id="intent">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="auto">Auto</SelectItem>
              <SelectItem value="how_to">How-to</SelectItem>
              <SelectItem value="conceptual">Conceptual</SelectItem>
              <SelectItem value="lookup">Lookup</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </CardContent>
    </Card>
  );
}

function MetricCardsGrid({
  report,
  loading,
}: {
  report: EvalReport | null;
  loading: boolean;
}) {
  if (loading) {
    return (
      <div className="grid gap-4 sm:grid-cols-2 md:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Card key={i}>
            <CardHeader className="pb-2">
              <Skeleton className="h-4 w-1/2" />
              <Skeleton className="h-4 w-3/4" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-8 w-3/4" />
              <Skeleton className="mt-2 h-4 w-1/3" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  if (!report) {
    return (
      <div className="flex flex-col items-center gap-3 rounded-md border border-dashed border-border bg-muted/30 p-12 text-center">
        <AlertCircle className="h-10 w-10 text-muted-foreground" />
        <div>
          <p className="text-base font-medium">No eval runs yet</p>
          <p className="mt-1 text-sm text-muted-foreground">
            Click <span className="font-medium">Run</span> above to evaluate
            the chosen eval set against the run config.
          </p>
          <p className="mt-2 text-xs text-muted-foreground">
            Backend `/eval/run` is W4 stub — pending implementation per
            docs/eval-methodology.md
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="grid gap-4 sm:grid-cols-2 md:grid-cols-4">
      {METRIC_ORDER.map((key) => (
        <MetricCard key={key} metricKey={key} report={report} />
      ))}
    </div>
  );
}

function MetricCard({
  metricKey,
  report,
}: {
  metricKey: MetricKey;
  report: EvalReport;
}) {
  const value = report[metricKey];
  const threshold = METRIC_THRESHOLDS[metricKey];
  const labels = METRIC_LABELS[metricKey];
  const passed = value !== null && value >= threshold;

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardDescription className="font-mono text-[10px] uppercase tracking-wide">
          {labels.short}
        </CardDescription>
        <CardTitle className="text-sm">{labels.full}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-semibold">
          {value === null ? '—' : value.toFixed(3)}
        </div>
        <div className="mt-2 flex items-center gap-2">
          {value === null ? (
            <Badge
              variant="outline"
              className="bg-muted text-muted-foreground border-transparent"
            >
              N/A
            </Badge>
          ) : passed ? (
            <Badge
              variant="outline"
              className="bg-success/15 text-success border-transparent"
            >
              <CheckCircle2 className="mr-1 h-3 w-3" />
              PASS
            </Badge>
          ) : (
            <Badge
              variant="outline"
              className="bg-warning/15 text-warning-foreground border-transparent"
            >
              FAIL
            </Badge>
          )}
          <span className="text-xs text-muted-foreground">
            ≥ {threshold.toFixed(2)}
          </span>
        </div>
      </CardContent>
    </Card>
  );
}

function FailedQueriesCard({
  failures,
}: {
  failures: EvalReport['failed_queries'];
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">
          Failed queries ({failures.length})
        </CardTitle>
        <CardDescription>
          Queries below per-metric strict acceptance threshold
        </CardDescription>
      </CardHeader>
      <CardContent>
        {failures.length === 0 ? (
          <div className="flex items-center gap-2 rounded-md bg-muted/30 p-4 text-sm text-muted-foreground">
            <CheckCircle2 className="h-4 w-4 text-success" />
            No failed queries.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="text-left text-xs uppercase text-muted-foreground">
                <tr className="border-b border-border">
                  <th className="px-2 py-2">Query ID</th>
                  <th className="px-2 py-2">Query</th>
                  <th className="px-2 py-2">Failed metrics</th>
                  <th className="px-2 py-2 text-right">Inspect</th>
                </tr>
              </thead>
              <tbody>
                {failures.map((q) => (
                  <tr
                    key={q.query_id}
                    className="border-b border-border last:border-b-0"
                  >
                    <td className="px-2 py-2 font-mono text-xs">
                      {q.query_id}
                    </td>
                    <td className="line-clamp-2 max-w-[24rem] px-2 py-2">
                      {q.query}
                    </td>
                    <td className="px-2 py-2">
                      <div className="flex flex-wrap gap-1">
                        {q.metric_failed.map((m) => (
                          <Badge
                            key={m}
                            variant="outline"
                            className="bg-warning/15 text-warning-foreground border-transparent text-xs"
                          >
                            {m}
                          </Badge>
                        ))}
                      </div>
                    </td>
                    <td className="px-2 py-2 text-right">
                      <Button asChild variant="ghost" size="sm">
                        <Link href={`/traces/${q.query_id}`}>
                          <ExternalLink className="h-3 w-3" />
                        </Link>
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function RerankerShootoutCard() {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">W4 Reranker Shootout</CardTitle>
        <CardDescription>
          W6 D1 LIVE Azure 2-way comparison · Cohere v4.0-pro production lock
          per Q21 Resolved · Voyage + ZeroEntropy DROPPED Tier 1 per W4
          Karpathy §1.2 simplicity drop
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="text-left text-xs uppercase text-muted-foreground">
              <tr className="border-b border-border">
                <th className="px-2 py-2">Reranker</th>
                <th className="px-2 py-2 text-right">Faithfulness</th>
                <th className="px-2 py-2 text-right">Answer Rel</th>
                <th className="px-2 py-2">Notes</th>
              </tr>
            </thead>
            <tbody>
              {RERANKER_SHOOTOUT.map((row) => {
                const dropped = row.status === 'dropped';
                return (
                  <tr
                    key={row.vendor}
                    className={cn(
                      'border-b border-border last:border-b-0',
                      dropped && 'opacity-60',
                    )}
                  >
                    <td className="px-2 py-2 font-medium">
                      <div className="flex items-center gap-2">
                        {row.vendor}
                        {row.status === 'recommended' && (
                          <Badge
                            variant="outline"
                            className="bg-success/15 text-success border-transparent text-[10px]"
                          >
                            RECOMMENDED
                          </Badge>
                        )}
                        {row.status === 'fallback' && (
                          <Badge
                            variant="outline"
                            className="bg-muted text-muted-foreground border-transparent text-[10px]"
                          >
                            Fallback
                          </Badge>
                        )}
                        {dropped && (
                          <Badge
                            variant="outline"
                            className="bg-muted text-muted-foreground border-transparent text-[10px]"
                          >
                            Dropped
                          </Badge>
                        )}
                      </div>
                    </td>
                    <td className="px-2 py-2 text-right font-mono">
                      {row.faithfulness === null
                        ? '—'
                        : row.faithfulness.toFixed(3)}
                    </td>
                    <td className="px-2 py-2 text-right font-mono">
                      {row.answer_relevancy === null
                        ? '—'
                        : row.answer_relevancy.toFixed(3)}
                    </td>
                    <td className="px-2 py-2 text-xs text-muted-foreground">
                      {row.recommendation}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}
