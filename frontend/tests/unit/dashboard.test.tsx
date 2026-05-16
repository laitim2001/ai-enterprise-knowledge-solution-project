/**
 * Unit tests — Dashboard page (`/dashboard`) render + payload-consumption smoke
 * (W18 F8.4 baseline + W20 F2.6 extension).
 *
 * W18 baseline (2 tests):
 *   - renders `<h1>` + 5 overview card headings
 *   - renders 4 quick-action links with right hrefs
 *
 * W20 F2.6 extension (per ADR-0030 absorbed scope):
 *   - renders the 4-stat strip (KBs / Documents / Chunks / Storage)
 *   - renders 5 per-component dots in the System health card
 *   - top-5 KB list renders the kbApi.list items
 *
 * Both `useQuery` calls are mocked so the assertions run synchronously.
 * Deep data-state coverage (degraded statuses → dot colour assertions) is Tier 2.
 */

import { render, screen, within } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, expect, it, vi } from 'vitest';

vi.mock('next/navigation', () => ({ useRouter: () => ({ push: vi.fn() }) }));
vi.mock('next/link', () => ({
  __esModule: true,
  default: ({ href, children, ...rest }: { href: string | { pathname?: string }; children: React.ReactNode }) => (
    <a href={typeof href === 'string' ? href : (href?.pathname ?? '#')} {...rest}>
      {children}
    </a>
  ),
}));

// W20 F2 — kbApi.list returns a small fixture so the 4-stat strip + top-5 list both render.
vi.mock('@/lib/api/kb', () => ({
  kbApi: {
    list: vi.fn(async () => [
      {
        kb_id: 'drive-manuals',
        name: 'Drive Project — Manuals',
        total_documents: 12,
        total_chunks: 240,
        storage_size_mb: 3.4,
      },
      {
        kb_id: 'ricoh-onboarding',
        name: 'Ricoh Onboarding',
        total_documents: 5,
        total_chunks: 80,
        storage_size_mb: 1.1,
      },
    ]),
  },
}));

// W20 F2.1 — /health now returns the per-component payload; the dashboard card
// renders 5 dots from this fixture.
vi.mock('@/lib/api-client', () => ({
  apiClient: {
    get: vi.fn(async () => ({
      status: 'ok',
      components: {
        azure_search: { status: 'ok', latency_ms: null, detail: null },
        azure_openai: { status: 'ok', latency_ms: null, detail: null },
        cohere: { status: 'not_configured', latency_ms: null, detail: 'optional' },
        langfuse: { status: 'ok', latency_ms: null, detail: null },
        postgres: { status: 'not_configured', latency_ms: null, detail: 'in-memory fallback' },
      },
    })),
  },
}));

import DashboardPage from '../../app/(app)/dashboard/page';

function renderDashboard() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <DashboardPage />
    </QueryClientProvider>,
  );
}

describe('Dashboard page', () => {
  it('renders the page heading and the 5 overview card headings', async () => {
    renderDashboard();
    expect(await screen.findByRole('heading', { name: 'Quick actions', level: 2 })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: /^dashboard$/i, level: 1 })).toBeInTheDocument();
    for (const title of ['Knowledge bases', 'Recent queries', 'Latest evaluation', 'System health']) {
      expect(screen.getByRole('heading', { name: title, level: 2 })).toBeInTheDocument();
    }
  });

  it('renders the 4 quick-action links with the right hrefs', async () => {
    renderDashboard();
    await screen.findByRole('heading', { name: 'Quick actions', level: 2 });
    expect(screen.getByRole('link', { name: /new kb/i })).toHaveAttribute('href', '/kb/new');
    expect(screen.getByRole('link', { name: /upload doc/i })).toHaveAttribute('href', '/kb');
    expect(screen.getByRole('link', { name: /run eval/i })).toHaveAttribute('href', '/eval');
    expect(screen.getByRole('link', { name: /open chat/i })).toHaveAttribute('href', '/chat');
  });

  it('renders the 4-stat strip with aggregate KB values', async () => {
    renderDashboard();
    // findByText waits for the kbApi.list mock to resolve.
    expect(await screen.findByText('Documents')).toBeInTheDocument();
    expect(screen.getByText('Chunks')).toBeInTheDocument();
    expect(screen.getByText('Storage')).toBeInTheDocument();
    // 2 KBs in the fixture → KB count = "2"
    expect(screen.getByText('2')).toBeInTheDocument();
    // Σdocs = 12 + 5 = 17; Σchunks = 240 + 80 = 320; Σstorage = 3.4 + 1.1 = 4.5 MB
    expect(screen.getByText('17')).toBeInTheDocument();
    expect(screen.getByText('320')).toBeInTheDocument();
    expect(screen.getByText('4.5 MB')).toBeInTheDocument();
  });

  it('renders 5 per-component dots in the System health card', async () => {
    renderDashboard();
    // The component list lives under aria-label="Component connectivity".
    const healthList = await screen.findByRole('list', { name: 'Component connectivity' });
    const items = within(healthList).getAllByRole('listitem');
    expect(items).toHaveLength(5);
    // Each row has the human-readable component name.
    for (const label of [
      'Azure AI Search',
      'Azure OpenAI',
      'Cohere Reranker',
      'Langfuse',
      'Postgres',
    ]) {
      expect(within(healthList).getByText(label)).toBeInTheDocument();
    }
    // The mocked payload has cohere + postgres at not_configured (rendered "Not configured").
    expect(within(healthList).getAllByText('Not configured')).toHaveLength(2);
    expect(within(healthList).getAllByText('OK')).toHaveLength(3);
  });

  it('renders the top-5 KB list with names + link to /kb', async () => {
    renderDashboard();
    // findByRole on the KB-specific link waits for kbQuery to actually resolve
    // (the structural "View all →" link renders even in the empty-state branch,
    // so finding it doesn't prove data has landed yet).
    const driveLink = await screen.findByRole('link', { name: 'Drive Project — Manuals' });
    expect(driveLink).toHaveAttribute('href', '/kb/drive-manuals');
    expect(screen.getByRole('link', { name: 'Ricoh Onboarding' })).toHaveAttribute(
      'href',
      '/kb/ricoh-onboarding',
    );
    // The "View all knowledge bases →" link still renders.
    expect(screen.getByRole('link', { name: /view all knowledge bases/i })).toHaveAttribute(
      'href',
      '/kb',
    );
  });
});
