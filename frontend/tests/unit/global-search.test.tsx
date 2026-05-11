/**
 * Unit tests — `<GlobalSearch>` command palette (W18 F8.4).
 *
 * Covers: (1) opening renders the static Page results, (2) typing filters the
 * Page results + always appends an "Ask in chat: …" action, (3) selecting the
 * "Ask in chat" result navigates to `/chat?q=<encoded>` + closes the palette,
 * (4) ArrowDown + Enter activates + selects the next result. KB results come
 * off `useQuery` — mocked to `[]` here (no backend in jsdom); the Page-results
 * path is the testable core. Render/interaction smoke — deep coverage is Tier 2
 * (see `tests/unit/README.md`).
 */

import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const push = vi.fn();
vi.mock('next/navigation', () => ({
  useRouter: () => ({ push, replace: vi.fn(), prefetch: vi.fn(), back: vi.fn(), forward: vi.fn(), refresh: vi.fn() }),
}));
vi.mock('@/lib/api/kb', () => ({
  kbApi: { list: vi.fn(async () => []) },
}));

import { GlobalSearch } from '@/components/nav/global-search';

function renderPalette(open = true) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const onOpenChange = vi.fn();
  const utils = render(
    <QueryClientProvider client={client}>
      <GlobalSearch open={open} onOpenChange={onOpenChange} />
    </QueryClientProvider>,
  );
  return { ...utils, onOpenChange };
}

describe('GlobalSearch', () => {
  beforeEach(() => {
    push.mockClear();
  });

  it('renders the static page results when open with an empty query', () => {
    renderPalette();
    const options = screen.getAllByRole('option');
    // 6 static pages: Dashboard / Chat / Knowledge Bases / Eval Console / Traces / Settings
    expect(options).toHaveLength(6);
    expect(screen.getByRole('option', { name: /dashboard/i })).toBeInTheDocument();
    expect(screen.getByRole('option', { name: /eval console/i })).toBeInTheDocument();
    expect(screen.getByRole('option', { name: /settings/i })).toBeInTheDocument();
  });

  it('filters the page results and appends an "Ask in chat" action when typing', async () => {
    renderPalette();
    await userEvent.type(screen.getByRole('combobox', { name: /search/i }), 'eval');
    const names = screen.getAllByRole('option').map((o) => o.textContent ?? '');
    expect(names.some((n) => /eval console/i.test(n))).toBe(true);
    expect(names.some((n) => /ask in chat/i.test(n))).toBe(true);
    expect(names.some((n) => /^dashboard/i.test(n))).toBe(false);
  });

  it('navigates to /chat?q= and closes when the "Ask in chat" result is selected', async () => {
    const { onOpenChange } = renderPalette();
    await userEvent.type(screen.getByRole('combobox', { name: /search/i }), 'how do refunds work');
    await userEvent.click(screen.getByRole('option', { name: /ask in chat/i }));
    expect(push).toHaveBeenCalledWith('/chat?q=how%20do%20refunds%20work');
    expect(onOpenChange).toHaveBeenCalledWith(false);
  });

  it('ArrowDown + Enter selects the next result', async () => {
    renderPalette();
    const input = screen.getByRole('combobox', { name: /search/i });
    input.focus();
    // First result (Dashboard) is active by default → ArrowDown moves to Chat → Enter selects it.
    await userEvent.keyboard('{ArrowDown}{Enter}');
    expect(push).toHaveBeenCalledWith('/chat');
  });
});
