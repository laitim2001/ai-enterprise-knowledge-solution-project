/**
 * Unit tests — `<AppShell>` unified application chrome (W18 F8.4 + W22 F1).
 *
 * Covers: (1) the 5 sidebar nav modules render under `<nav aria-label="Primary">`,
 * (2) the active route gets `aria-current="page"`, (3) the focus-mode toggle
 * hides the desktop sidebar (and flips its label), (4) the top-bar global-search
 * trigger is present. `<UserMenu>` shows "Signing in…" with no AuthProvider
 * mounted (fine — that path is exercised); `<ThemeToggle>` + `<GlobalSearch open=false>`
 * render inertly. Render/interaction smoke — deep coverage is Tier 2.
 *
 * W22 F1 label updates per CLAUDE.md §5.7 H7 strict mockup fidelity —
 * "Knowledge Bases" → "Knowledge", "Eval Console" → "Eval" (matches
 * `references/design-mockups/ekp-data.jsx` `window.NAV_ITEMS` shape).
 */

import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, expect, it, vi } from 'vitest';

vi.mock('next/navigation', () => ({
  usePathname: () => '/dashboard',
  useRouter: () => ({ push: vi.fn(), replace: vi.fn(), prefetch: vi.fn(), back: vi.fn(), forward: vi.fn(), refresh: vi.fn() }),
}));
vi.mock('next/link', () => ({
  __esModule: true,
  default: ({ href, children, ...rest }: { href: string | { pathname?: string }; children: React.ReactNode }) => (
    <a href={typeof href === 'string' ? href : (href?.pathname ?? '#')} {...rest}>
      {children}
    </a>
  ),
}));
vi.mock('@/lib/api/kb', () => ({ kbApi: { list: vi.fn(async () => []) } }));

import { AppShell } from '@/components/nav/app-shell';

function renderShell() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <AppShell>
        <div>page body</div>
      </AppShell>
    </QueryClientProvider>,
  );
}

describe('AppShell', () => {
  it('renders the 5 sidebar nav modules', () => {
    renderShell();
    expect(screen.getByRole('navigation', { name: /primary/i })).toBeInTheDocument();
    for (const label of ['Dashboard', 'Chat', 'Knowledge', 'Eval', 'Traces']) {
      expect(screen.getByRole('link', { name: label })).toBeInTheDocument();
    }
  });

  it('marks the active route with aria-current="page"', () => {
    renderShell();
    expect(screen.getByRole('link', { name: 'Dashboard' })).toHaveAttribute('aria-current', 'page');
    expect(screen.getByRole('link', { name: 'Chat' })).not.toHaveAttribute('aria-current');
  });

  it('the focus-mode toggle hides the desktop sidebar and flips its label', async () => {
    renderShell();
    expect(screen.getByRole('navigation', { name: /primary/i })).toBeInTheDocument();
    await userEvent.click(screen.getByRole('button', { name: /collapse sidebar/i }));
    expect(screen.queryByRole('navigation', { name: /primary/i })).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: /expand sidebar/i })).toBeInTheDocument();
  });

  it('renders the top-bar global-search trigger', () => {
    renderShell();
    expect(screen.getByRole('button', { name: /search/i })).toBeInTheDocument();
  });
});
