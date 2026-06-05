/**
 * Unit tests — W46 F3 — KB Detail Settings tab unlock (chunk_strategy + per-KB
 * image cap) + Re-indexing card (button → confirm modal → POST /kb/{id}/reindex
 * → summary), per ADR-0042 + ADR-0043.
 *
 * Same harness as kb-settings-tuning.test.tsx (real QueryClientProvider; mocked
 * next/navigation + sonner + api modules). Asserts:
 *   1. chunk_strategy seg is now EDITABLE (not disabled) + "Max images / chunk"
 *      field renders — the W46 unlock;
 *   2. Save sends the FULL KbConfig body INCLUDING chunk_strategy +
 *      chunker_max_images_per_chunk (full-replacement semantics);
 *   3. the Re-indexing card opens a confirm modal, and confirming calls
 *      kbApi.reindex and renders the per-doc summary banner.
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
vi.mock('@/lib/api/config-test', () => ({ configTestApi: { run: vi.fn() } }));
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
    // W45 — image cap unset → inherits the global default (8). Renders as ''.
    chunker_max_images_per_chunk: null,
  },
  total_documents: 1,
  total_chunks: 2,
  total_screenshots: 0,
  failed_documents: [],
  last_indexed_at: '2026-05-12T00:00:00Z',
  storage_size_mb: 0.0,
  archived: false,
};

const FAKE_REINDEX_SUMMARY = {
  status: 'reindexed',
  kb_id: 'test-kb',
  documents_total: 1,
  documents_reindexed: 1,
  reindexed: ['doc-1'],
  skipped_no_source: [],
  failed: [],
  chunks_total: 2,
};

vi.mock('@/lib/api/kb', () => ({
  kbApi: {
    get: vi.fn(async () => FAKE_KB),
    patchSettings: vi.fn(async () => FAKE_KB.config),
    patchMetadata: vi.fn(async () => FAKE_KB),
    archive: vi.fn(async () => FAKE_KB),
    reindex: vi.fn(async () => FAKE_REINDEX_SUMMARY),
    listImages: vi.fn(async () => ({ items: [], total: 0, limit: 50, offset: 0 })),
    chunkingPreview: vi.fn(async () => ({ items: [] })),
  },
}));
vi.mock('@/lib/api/documents', () => ({
  documentsApi: { list: vi.fn(async () => []), listChunks: vi.fn(async () => []) },
}));

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

describe('W46 F3.2 — chunk_strategy unlock + image cap field', () => {
  beforeEach(() => vi.clearAllMocks());

  it('renders an editable chunk_strategy seg + a Max images / chunk field', async () => {
    renderSettings();

    // chunk_strategy seg buttons are now interactive (W46 unlock) — not disabled.
    const layoutBtn = await screen.findByRole('button', { name: 'layout_aware' });
    expect(layoutBtn).not.toBeDisabled();
    // The new per-KB image cap field (placeholder = inherit-global affordance).
    expect(screen.getByText('Max images / chunk')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('繼承全域 (8)')).toBeInTheDocument();
  });
});

describe('W46 F3.2 — Save includes chunk_strategy + image cap', () => {
  beforeEach(() => vi.clearAllMocks());

  it('PATCHes the full config with the changed chunk_strategy + image cap', async () => {
    renderSettings();

    await userEvent.click(await screen.findByRole('button', { name: 'layout_aware' }));
    const capInput = screen.getByPlaceholderText('繼承全域 (8)');
    await userEvent.clear(capInput);
    await userEvent.type(capInput, '5');
    await userEvent.click(screen.getByRole('button', { name: 'Save changes' }));

    await waitFor(() =>
      expect(kbApi.patchSettings).toHaveBeenCalledWith(
        'test-kb',
        expect.objectContaining({
          chunk_strategy: 'layout_aware',
          chunker_max_images_per_chunk: 5,
          // base fields preserved on full-replacement
          embedding_model: 'text-embedding-3-large',
          default_top_k: 50,
        }),
      ),
    );
  });
});

describe('W46 F3.3 — Re-indexing card → confirm modal → summary', () => {
  beforeEach(() => vi.clearAllMocks());

  it('opens the confirm modal, calls kbApi.reindex, and shows the summary', async () => {
    renderSettings();

    // open modal from the Re-indexing card footer button
    await userEvent.click(
      await screen.findByRole('button', { name: /Trigger re-index now/i }),
    );
    expect(
      await screen.findByRole('heading', { name: /Re-index this knowledge base/i }),
    ).toBeInTheDocument();

    // confirm → POST /kb/{id}/reindex
    await userEvent.click(
      screen.getByRole('button', { name: /Re-index 1 documents/i }),
    );
    await waitFor(() => expect(kbApi.reindex).toHaveBeenCalledWith('test-kb'));

    // success → per-doc summary banner rendered on the card
    expect(
      await screen.findByText(/Re-indexed 1 \/ 1 documents/i),
    ).toBeInTheDocument();
  });
});
