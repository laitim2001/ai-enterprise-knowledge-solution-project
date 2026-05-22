/**
 * Unit test — chat page KB-selection sync (BUG-006).
 *
 * The chat page kept a `kbId` state that defaulted to a W3-POC legacy alias
 * (`drive_user_manuals`) and was never synced to the loaded KB list. The KB
 * dropdown DISPLAYED the right KB (via the derived `activeKb`), masking the
 * stale state — but `streamQuery` / `conversationsApi.create` were handed the
 * raw `kbId`, so every retrieval hit a non-existent legacy index and 502'd.
 *
 * This test loads a real KB, sends a query, and asserts the backend calls
 * carry the loaded kb_id — not the stale default. Pre-fix it fails (kb_id
 * would be `drive_user_manuals`); post-fix the sync `useEffect` corrects it.
 */

import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { ReactNode } from 'react';

// `vi.hoisted` so the spies exist before the hoisted `vi.mock` factories run.
const { streamQuery, kbList, convCreate } = vi.hoisted(() => ({
  streamQuery: vi.fn(),
  kbList: vi.fn(),
  convCreate: vi.fn(),
}));

vi.mock('next/link', () => ({
  __esModule: true,
  default: ({ href, children, ...rest }: { href: string; children: ReactNode }) => (
    <a href={typeof href === 'string' ? href : '#'} {...rest}>
      {children}
    </a>
  ),
}));
vi.mock('@/lib/api/kb', () => ({ kbApi: { list: kbList } }));
vi.mock('@/lib/api/query', () => ({ streamQuery }));
vi.mock('@/lib/api/conversations', () => ({
  conversationsApi: {
    create: convCreate,
    list: vi.fn(async () => ({ items: [], total: 0, limit: 50, offset: 0 })),
    get: vi.fn(async () => ({ messages: [] })),
    appendMessage: vi.fn(async () => ({})),
  },
}));

import ChatPage from '@/app/(app)/chat/page';

const FAKE_KB = {
  kb_id: 'drive-user-manual-1',
  name: 'drive-user-manual-1',
  description: 'drive-user-manual-1',
  config: {
    embedding_model: 'text-embedding-3-large',
    embedding_dimension: 1024,
    chunk_strategy: 'auto' as const,
    default_top_k: 50,
    default_rerank_k: 5,
  },
  total_documents: 1,
  total_chunks: 121,
  total_screenshots: 0,
  failed_documents: [],
  last_indexed_at: '2026-05-22T00:00:00Z',
  storage_size_mb: 0,
  archived: false,
};

function renderChat() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <ChatPage />
    </QueryClientProvider>,
  );
}

describe('Chat KB-selection sync (BUG-006)', () => {
  beforeEach(() => {
    streamQuery.mockReset();
    kbList.mockReset();
    convCreate.mockReset();
    kbList.mockResolvedValue([FAKE_KB]);
    convCreate.mockResolvedValue({ id: 'conv-1', kb_id: 'drive-user-manual-1' });
    // streamQuery yields nothing — the page's `for await` loop ends at once;
    // the test only cares about the kb_id it was called with.
    streamQuery.mockImplementation(() => (async function* () {})());
  });

  it('sends the loaded KB id to the backend, not the stale POC default', async () => {
    renderChat();

    // Wait for the KB list to load — the option renders + the sync useEffect
    // flushes kbId by the time this resolves.
    await screen.findByRole('option', { name: /drive-user-manual-1/i });

    const composer = screen.getByPlaceholderText(/ask about ricoh/i);
    await userEvent.type(composer, 'what is in the document');
    fireEvent.submit(composer.closest('form')!);

    await waitFor(() => expect(streamQuery).toHaveBeenCalled());
    expect(streamQuery.mock.calls[0]![0]).toMatchObject({
      kb_id: 'drive-user-manual-1',
    });
    // The conversation is created against the same real KB.
    expect(convCreate).toHaveBeenCalledWith({ kb_id: 'drive-user-manual-1' });
  });
});
