/**
 * Unit tests — Eval Console page (`/eval`) — CH-002 F3 + W22 F7.1 rebuild
 * re-aligned at W23 F1.1.
 *
 * Covers: the page renders the W22 mockup-faithful 6-section layout (page-title
 * 「Eval Console」+ subtitle empty-state「No eval runs yet — click <b>Run eval suite</b>
 * to start.」+ page-actions 3 buttons);clicking「Run eval suite」calls `evalApi.run`
 * with eval_set_id + enable_crag + max_main_queries (W22 D7 hardcoded
 * EVAL_SET_ID const) and renders the 4 MetricCard labels (Recall@5 / Faithfulness /
 * Correctness / Image Association — W22 D9.d backend-wins labels, full text not
 * short-codes) + Failed queries card with q.query row from `EvalReport.failed_queries`;
 * an eval-run error surfaces toast.error('Eval run failed', { description }). The
 * mutation goes through a real `QueryClientProvider`;`evalApi` / `sonner` /
 * `next/link` / `lucide-react` icons are mocked.
 */

import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('next/link', () => ({
  __esModule: true,
  default: ({ href, children, ...rest }: { href: string; children: React.ReactNode }) => (
    <a href={typeof href === 'string' ? href : '#'} {...rest}>
      {children}
    </a>
  ),
}));
vi.mock('sonner', () => ({
  toast: { success: vi.fn(), error: vi.fn(), info: vi.fn() },
}));
vi.mock('@/lib/api/eval', () => ({ evalApi: { run: vi.fn(), shootout: vi.fn() } }));

import { toast } from 'sonner';

import { evalApi } from '@/lib/api/eval';
import EvalConsolePage from '../../app/(app)/eval/page';

const FAKE_REPORT = {
  recall_at_5: 0.92,
  faithfulness: 0.88,
  correctness: 0.81,
  image_association: 0.0,
  p95_latency_ms: 1200,
  failed_queries: [
    {
      query_id: 'q-001',
      query: 'how do refunds work',
      expected: '>= 0.7',
      got: 'answer_relevancy=0.30',
      metric_failed: ['answer_relevancy'],
    },
  ],
  crag_trigger_rate: 0.1,
  avg_cost_per_query_usd: 0.002,
};

function renderEval() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <EvalConsolePage />
    </QueryClientProvider>,
  );
}

describe('Eval Console page (CH-002 F3 + W22 F7.1 rebuild) — re-aligned W23 F1.1', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the W22 mockup-faithful header + empty subtitle without stale W4-stub copy', () => {
    renderEval();
    // Page heading is "Eval Console" (W22 F7.1 mockup PageEval line ~131 page-title).
    expect(
      screen.getByRole('heading', { name: 'Eval Console', level: 1 }),
    ).toBeInTheDocument();
    // Empty-state subtitle text "No eval runs yet" + click hint preserved.
    expect(screen.getByText(/no eval runs yet/i)).toBeInTheDocument();
    // Stale pre-rebuild stub copy gone.
    expect(screen.queryByText(/W4 stub/i)).toBeNull();
    expect(screen.queryByText(/pending implementation/i)).toBeNull();
  });

  it('running an eval renders the 4 MetricCard labels + Failed queries card from the report', async () => {
    vi.mocked(evalApi.run).mockResolvedValue(FAKE_REPORT);
    renderEval();

    // Run button label is "Run eval suite" (W22 F7.1 mockup PageEval line ~155).
    await userEvent.click(screen.getByRole('button', { name: /run eval suite/i }));

    // MetricCard renders `labels.full` (Recall@5 / Faithfulness / Correctness /
    // Image Association) per W22 F7.1 METRIC_LABELS. The eval-run scenario does
    // NOT trigger the Shootout `<table>` (shootoutReport stays null → empty-state
    // card with no `<th>` headers) — so no header collision on these label names.
    for (const label of ['Recall@5', 'Faithfulness', 'Correctness', 'Image Association']) {
      expect(await screen.findByText(label)).toBeInTheDocument();
    }
    // recall_at_5 = 0.92 → MetricCard `pct.toFixed(1)` = "92.0" (W22 line ~264).
    expect(screen.getByText('92.0')).toBeInTheDocument();
    // Failed queries card heading + the FAKE_REPORT q.query row text (W22 line ~745).
    expect(screen.getByRole('heading', { name: /failed queries/i, level: 3 })).toBeInTheDocument();
    expect(screen.getByText('how do refunds work')).toBeInTheDocument();

    // evalApi.run called with the hardcoded EVAL_SET_ID + enable_crag + a numeric
    // max_main_queries cap (W22 D7: hardcoded const, not reactive picker).
    expect(evalApi.run).toHaveBeenCalledWith(
      expect.objectContaining({
        eval_set_id: 'eval-set-v0',
        enable_crag: true,
        max_main_queries: expect.any(Number),
      }),
    );
  });

  it('surfaces a toast on eval-run failure', async () => {
    vi.mocked(evalApi.run).mockRejectedValue(new Error('eval orchestrator down'));
    renderEval();

    await userEvent.click(screen.getByRole('button', { name: /run eval suite/i }));

    // W22 F7.1 onError → toast.error('Eval run failed', { description: err.message }).
    await waitFor(() => expect(toast.error).toHaveBeenCalled());
  });
});
