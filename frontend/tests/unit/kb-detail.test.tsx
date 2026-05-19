/**
 * Unit tests — KB Detail page (`/kb/[id]`) — CH-002 F7 (Chunks tab wired) +
 * F10 (Settings → name/description PATCH) re-aligned at W23 F1.2 to W22 F6.1
 * 7-tab rebuild DOM (mockup `ekp-page-kb.jsx:140 PageKbDetail` inline pattern,
 * 1776→1339 lines).
 *
 * The page is rendered through a real `QueryClientProvider`;`next/navigation`
 * (`useParams` / `useRouter` / `useSearchParams` — active tab from `?tab=`),
 * `next/link`, `sonner`, and the api modules are mocked. Active tab content
 * is conditional on `activeTab === <key>` (W22 inline render, not Radix Tabs),
 * so each describe block flips `mocks.tab` before render.
 */

import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const mocks = vi.hoisted(() => ({ tab: 'documents' as string }));

vi.mock('next/navigation', () => ({
  useParams: () => ({ id: 'test-kb' }),
  useRouter: () => ({ push: vi.fn() }),
  useSearchParams: () => new URLSearchParams(`tab=${mocks.tab}`),
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
  },
  total_documents: 1,
  total_chunks: 2,
  total_screenshots: 0,
  failed_documents: [],
  last_indexed_at: '2026-05-12T00:00:00Z',
  storage_size_mb: 0.0,
  archived: false,
};
const FAKE_DOCS = [
  {
    doc_id: 'doc-1',
    doc_title: 'Vendor Manual',
    doc_format: 'docx',
    total_chunks: 2,
    last_indexed_at: '2026-05-12T00:00:00Z',
    source_url: null,
    tags: [],
  },
];
const FAKE_CHUNKS = [
  {
    chunk_id: 'kb-test-kb_doc-doc-1_chunk-0000',
    chunk_index: 0,
    chunk_total: 2,
    chunk_title: 'Section 1',
    section_path: ['Vendor Manual', 'Section 1'],
    enabled: true,
    low_value_flag: false,
  },
  {
    chunk_id: 'kb-test-kb_doc-doc-1_chunk-0001',
    chunk_index: 1,
    chunk_total: 2,
    chunk_title: 'Section 2',
    section_path: ['Vendor Manual', 'Section 2'],
    enabled: true,
    low_value_flag: true,
  },
];

vi.mock('@/lib/api/kb', () => ({
  kbApi: {
    get: vi.fn(async () => FAKE_KB),
    patchSettings: vi.fn(async () => FAKE_KB),
    patchMetadata: vi.fn(async () => FAKE_KB),
    archive: vi.fn(async () => FAKE_KB),
    listImages: vi.fn(async () => []),
    chunkingPreview: vi.fn(async () => ({ chunks: [] })),
  },
}));
vi.mock('@/lib/api/documents', () => ({
  documentsApi: {
    list: vi.fn(async () => FAKE_DOCS),
    listChunks: vi.fn(async () => FAKE_CHUNKS),
  },
}));

import { kbApi } from '@/lib/api/kb';
import KbDetailPage from '../../app/(app)/kb/[id]/page';

function renderKbDetail() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <KbDetailPage />
    </QueryClientProvider>,
  );
}

describe('KB Detail — Chunks tab (CH-002 F7 + W22 F6.1 rebuild) — re-aligned W23 F1.2', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.tab = 'chunks';
  });

  it("lists a document's chunks (no stale 501-stub copy)", async () => {
    renderKbDetail();

    // W22 F6.1 ChunksTab renders chunk_id with `#` prefix in browse list
    // (mockup `ekp-page-kb.jsx` sub-tab convention;line ~650). Allow extra
    // time when whole suite runs (jsdom + OneDrive can be slow with chained
    // KB-get → docs-list → chunks-list async resolutions).
    expect(
      await screen.findByText(
        '#kb-test-kb_doc-doc-1_chunk-0000',
        {},
        { timeout: 5000 },
      ),
    ).toBeInTheDocument();
    expect(screen.getByText('#kb-test-kb_doc-doc-1_chunk-0001')).toBeInTheDocument();

    // chunk_title rendered as 13px row body text (line ~653). Note: `Section 1`
    // also appears in section_path span within both the browse row and the
    // active-chunk preview card (line ~656 + ~732), so use `getAllByText`.
    expect(screen.getAllByText('Section 1').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Section 2').length).toBeGreaterThan(0);

    // W22 ChunksTab Browse + Chunk preview cards both render — heading copy
    // confirms tab rendered correctly.
    expect(
      screen.getByRole('heading', { name: /browse chunks/i, level: 3 }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole('heading', { name: /chunk preview/i, level: 3 }),
    ).toBeInTheDocument();

    // Stale W2-era stub copy gone (W22 rebuild + W17 stub cascade closed).
    expect(screen.queryByText(/501 stub/i)).toBeNull();
    expect(screen.queryByText(/pending backend list endpoint/i)).toBeNull();
    expect(screen.queryByText(/W2 chunk listing/i)).toBeNull();
  });
});

describe('KB Detail — Settings tab (CH-002 F10 + W22 F6.1 rebuild) — re-aligned W23 F1.2', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.tab = 'settings';
  });

  it('renders editable Name + Description inputs (kb_id is locked) and PATCHes on Save changes', async () => {
    renderKbDetail();

    // W22 F6.1 SettingsTab uses label「Name」/「Description」/「kb_id」(lowercase
    // + Shield icon) but the labels and their inputs are siblings WITHOUT
    // `htmlFor`/`id` linkage (line ~1832-1869), so `getByLabelText` cannot
    // match. Query by display value instead — each input has a distinct value
    // ("Test KB" / "A test KB." / "test-kb"). Pre-W22 also used HTML `readonly`
    // for KB ID input;W22 switched to `disabled` (line ~1863).
    const nameInput = await screen.findByDisplayValue('Test KB');
    expect(nameInput).not.toBeDisabled();

    const descriptionInput = screen.getByDisplayValue('A test KB.');
    expect(descriptionInput).not.toBeDisabled();

    const kbIdInput = screen.getByDisplayValue('test-kb');
    expect(kbIdInput).toBeDisabled();

    // Stale pre-rebuild copy gone.
    expect(screen.queryByText(/PATCH lands W15/i)).toBeNull();
    expect(screen.queryByText(/read-only Tier 1/i)).toBeNull();

    // Save flow — W22 SettingsTab combined-form「Save changes」button (line ~2013)
    // calls metaMutation.mutate() when name/description dirty;mutation calls
    // kbApi.patchMetadata(kbId, { name?: ..., description?: ... }) conditional
    // on field change (line ~1781-1786).
    await userEvent.clear(nameInput);
    await userEvent.type(nameInput, 'Renamed KB');
    await userEvent.click(screen.getByRole('button', { name: /save changes/i }));

    await waitFor(() =>
      expect(kbApi.patchMetadata).toHaveBeenCalledWith(
        'test-kb',
        expect.objectContaining({ name: 'Renamed KB' }),
      ),
    );
  });
});
