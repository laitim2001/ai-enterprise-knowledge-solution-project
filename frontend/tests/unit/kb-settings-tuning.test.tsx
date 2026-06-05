/**
 * Unit tests — W43 F3.2/F3.3/F3.4 — KB Detail Settings tab "Advanced retrieval
 * tuning" (12 per-KB knobs) + "試跑 (config-test)" panel, per ADR-0040.
 *
 * Renders `/kb/[id]` with `?tab=settings` through a real QueryClientProvider;
 * next/navigation + sonner + the api modules are mocked (same shape as
 * kb-detail.test.tsx). Asserts:
 *   1. the tuning card renders 3 groups + a knob in the 已覆寫 (overridden) state;
 *   2. Save sends the FULL KbConfig body (base + top_k + 12 knobs) — F3.4
 *      full-replacement semantics, not a partial PATCH;
 *   3. 試跑 calls configTestApi.run with the draft + A/B and renders both result
 *      cards + the per-citation breakdown.
 */

import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('next/navigation', () => ({
  useParams: () => ({ id: 'test-kb' }),
  useRouter: () => ({ push: vi.fn() }),
  useSearchParams: () => new URLSearchParams('tab=settings'),
}));
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
vi.mock('@/lib/api-client', () => ({ ApiError: class ApiError extends Error {} }));
vi.mock('@/lib/api/query', () => ({ streamQuery: vi.fn() }));
vi.mock('@/lib/api/retrieval-test', () => ({ retrievalTestApi: {} }));
vi.mock('@/components/kb/tab-kb-access', () => ({ TabKbAccess: () => null }));

const FAKE_KB = {
  kb_id: 'test-kb',
  name: 'Test KB',
  description: 'A test KB.',
  config: {
    embedding_model: 'text-embedding-3-large',
    embedding_dimension: 1024,
    chunk_strategy: 'auto' as const,
    default_top_k: 50,
    default_rerank_k: 5,
    extract_embedded_images: false,
    slide_screenshots: true,
    dedup_strategy: 'sha256' as const,
    return_images_in_chat: false,
    // overridden: a bool group toggle + a numeric knob — the rest inherit (absent).
    enable_parent_doc_retrieval: true,
    max_images_per_answer: 8,
  },
  total_documents: 1,
  total_chunks: 2,
  total_screenshots: 0,
  failed_documents: [],
  last_indexed_at: '2026-05-12T00:00:00Z',
  storage_size_mb: 0.0,
  archived: false,
};

const band = (v: number) => ({ min: v, max: v, mean: v, band: 0 });
const FAKE_RESULT = {
  kb_id: 'test-kb',
  query: 'How do I configure the address book sync?',
  runs: 3,
  resolved_config: { max_images_per_answer: 8 },
  draft: {
    runs: [
      { run: 1, citation_count: 1, figure_count_raw: 6, figure_count_dedup: 6, latency_ms: 4100, answer_chars: 612, refused: false },
    ],
    citation_count: band(1),
    figure_count_raw: band(6),
    figure_count_dedup: band(6),
    latency_ms: band(4100),
    per_citation: [{ chunk_id: 'chunk-42', section_path: ['Address Book', 'Sync'], image_count: 6 }],
    faithfulness: 0.97, // W48 dual-axis quality
  },
  saved: {
    runs: [
      { run: 1, citation_count: 11, figure_count_raw: 36, figure_count_dedup: 29, latency_ms: 5800, answer_chars: 1840, refused: false },
    ],
    citation_count: band(11),
    figure_count_raw: band(36),
    figure_count_dedup: band(29),
    latency_ms: band(5800),
    per_citation: [],
    faithfulness: 0.94, // W48 dual-axis quality
  },
};

vi.mock('@/lib/api/kb', () => ({
  kbApi: {
    get: vi.fn(async () => FAKE_KB),
    patchSettings: vi.fn(async () => FAKE_KB.config),
    patchMetadata: vi.fn(async () => FAKE_KB),
    archive: vi.fn(async () => FAKE_KB),
    listImages: vi.fn(async () => ({ items: [], total: 0, limit: 50, offset: 0 })),
    chunkingPreview: vi.fn(async () => ({ items: [] })),
  },
}));
vi.mock('@/lib/api/documents', () => ({
  documentsApi: { list: vi.fn(async () => []), listChunks: vi.fn(async () => []) },
}));
vi.mock('@/lib/api/config-test', () => ({
  configTestApi: { run: vi.fn(async () => FAKE_RESULT) },
}));

import { configTestApi } from '@/lib/api/config-test';
import { kbApi } from '@/lib/api/kb';
import KbDetailPage from '../../app/(app)/kb/[id]/page';

function renderSettings() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <KbDetailPage />
    </QueryClientProvider>,
  );
}

describe('W43 F3.2 — Advanced retrieval tuning card', () => {
  beforeEach(() => vi.clearAllMocks());

  it('renders the 3 knob groups + an 已覆寫 (overridden) state', async () => {
    renderSettings();

    expect(
      await screen.findByRole('heading', { name: /advanced retrieval tuning/i, level: 3 }),
    ).toBeInTheDocument();
    // 3 groups
    expect(screen.getByText('Parent-document retrieval')).toBeInTheDocument();
    expect(screen.getByText('Citation post-hoc expansion')).toBeInTheDocument();
    expect(screen.getByText(/Citation neighbour images/)).toBeInTheDocument();
    // enable_parent_doc_retrieval=true → its group is 已覆寫; the rest 繼承全域.
    expect(screen.getAllByText('已覆寫').length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText('繼承全域').length).toBeGreaterThanOrEqual(1);
    // config-test panel present (collapsed, empty state)
    expect(
      screen.getByRole('heading', { name: /試跑/, level: 3 }),
    ).toBeInTheDocument();
  });
});

describe('W43 F3.4 — Save sends the full KbConfig body', () => {
  beforeEach(() => vi.clearAllMocks());

  it('PATCHes the complete config (base + top_k + 12 knobs), not a partial', async () => {
    renderSettings();

    // change default_top_k 50 → 40 to make config dirty, then save via the
    // Advanced card "儲存到此 KB" (exact name avoids the test-panel save button).
    const topKInput = await screen.findByDisplayValue('50');
    await userEvent.clear(topKInput);
    await userEvent.type(topKInput, '40');
    await userEvent.click(screen.getByRole('button', { name: '儲存到此 KB' }));

    await waitFor(() =>
      expect(kbApi.patchSettings).toHaveBeenCalledWith(
        'test-kb',
        expect.objectContaining({
          default_top_k: 40,
          // 12 knobs preserved in the full body (full-replacement safety)
          enable_parent_doc_retrieval: true,
          max_images_per_answer: 8,
          // inherited knob serialised as null (not dropped)
          parent_doc_top_k: null,
          // base fields preserved (would otherwise reset on full-replacement)
          embedding_model: 'text-embedding-3-large',
          chunk_strategy: 'auto',
        }),
      ),
    );
  });
});

describe('W43 F3.3 — config-test 試跑 panel', () => {
  beforeEach(() => vi.clearAllMocks());

  it('runs the draft + A/B and renders both result cards + breakdown', async () => {
    renderSettings();

    await screen.findByRole('heading', { name: /試跑/, level: 3 });
    await userEvent.click(screen.getByRole('button', { name: /試跑/ }));

    await waitFor(() =>
      expect(configTestApi.run).toHaveBeenCalledWith(
        'test-kb',
        expect.objectContaining({
          query: expect.any(String),
          runs: 3,
          compare_to_saved: true,
          draft_config: expect.objectContaining({ max_images_per_answer: 8 }),
        }),
      ),
    );

    // A/B result cards
    expect(await screen.findByText('草稿配置(DRAFT)')).toBeInTheDocument();
    expect(screen.getByText('已存配置(SAVED)')).toBeInTheDocument();
    // per-citation breakdown from the draft's last run
    expect(screen.getByText('chunk-42')).toBeInTheDocument();
    // W48 dual-axis — faithfulness quality axis renders on both A/B cards
    expect(screen.getAllByText(/忠實度/).length).toBeGreaterThanOrEqual(2);
    expect(screen.getByText('0.97')).toBeInTheDocument();
    expect(screen.getByText('0.94')).toBeInTheDocument();
  });
});
