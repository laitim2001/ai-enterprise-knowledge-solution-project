/**
 * Unit tests — Dashboard page (`/dashboard`) render smoke (W18 F8.4).
 *
 * Covers: the page renders its `<h1>` + the 5 overview card headings + the 4
 * quick-action links (with the right hrefs). The two `useQuery` calls (GET /kb,
 * GET /health) are mocked to resolve to empty/ok — the card *titles* and the
 * quick-action links render synchronously regardless of data state, so this is
 * a structure smoke. Deep data-state coverage is Tier 2.
 */

import { render, screen } from '@testing-library/react';
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
vi.mock('@/lib/api/kb', () => ({ kbApi: { list: vi.fn(async () => []) } }));
vi.mock('@/lib/api-client', () => ({ apiClient: { get: vi.fn(async () => ({ status: 'ok' })) } }));

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
  it('renders the page heading and the overview card headings', async () => {
    renderDashboard();
    // findBy lets the (mocked) useQuery resolutions settle inside act before we assert.
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
});
