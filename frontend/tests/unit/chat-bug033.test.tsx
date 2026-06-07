/**
 * Unit tests — BUG-033 (chat page).
 *
 * Finding A: loadConversation never synced kbId → the KB selector stayed on
 *   kbs[0] regardless of which conversation was opened. Fix sets kbId from
 *   detail.conversation.kb_id. Test: open a conversation bound to the SECOND KB
 *   and assert the selector switches to it (not the default first KB).
 *
 * Finding B: AnswerBodyMarkdown's `ol`/`ul` renderers lacked `list-style-type`,
 *   so Tailwind's preflight `list-style:none` hid numbered/bulleted markers even
 *   though the LLM markdown was correct. Fix adds listStyleType. Test: an
 *   assistant message with a markdown numbered list renders an <ol> whose inline
 *   style carries list-style-type: decimal.
 */

import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { ReactNode } from 'react';

const { streamQuery, kbList, convList, convGet } = vi.hoisted(() => ({
  streamQuery: vi.fn(),
  kbList: vi.fn(),
  convList: vi.fn(),
  convGet: vi.fn(),
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
    list: convList,
    get: convGet,
    create: vi.fn(async () => ({ id: 'c-new', kb_id: 'kb-a' })),
    appendMessage: vi.fn(async () => ({})),
    remove: vi.fn(async () => ({})),
  },
}));

import ChatPage from '@/app/(app)/chat/page';

function kb(id: string, name: string) {
  return {
    kb_id: id,
    name,
    description: name,
    config: {
      embedding_model: 'text-embedding-3-large',
      embedding_dimension: 1024,
      chunk_strategy: 'auto' as const,
      default_top_k: 50,
      default_rerank_k: 5,
    },
    total_documents: 1,
    total_chunks: 10,
    total_screenshots: 0,
    failed_documents: [],
    last_indexed_at: '2026-06-01T00:00:00Z',
    storage_size_mb: 0,
    archived: false,
  };
}

const CONV = {
  id: 'conv-b',
  user_id: 'u1',
  title: 'GL thread',
  kb_id: 'kb-b',
  created_at: '2026-06-07T00:00:00Z',
  updated_at: '2026-06-07T00:00:00Z',
  message_count: 1,
};

function renderChat() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <ChatPage />
    </QueryClientProvider>,
  );
}

describe('BUG-033 — chat KB restore + list markers', () => {
  beforeEach(() => {
    streamQuery.mockReset();
    kbList.mockReset();
    convList.mockReset();
    convGet.mockReset();
    // kb-a is FIRST → the selector defaults to it; the conversation is bound to kb-b.
    kbList.mockResolvedValue([kb('kb-a', 'KB Alpha'), kb('kb-b', 'KB Bravo')]);
    convList.mockResolvedValue({ items: [CONV], total: 1, limit: 50, offset: 0 });
    streamQuery.mockImplementation(() => (async function* () {})());
  });

  it('Finding A — restores the conversation KB on open (not kbs[0])', async () => {
    convGet.mockResolvedValue({ conversation: CONV, messages: [] });
    renderChat();

    // selector defaults to the first KB once the async KB list loads + the sync
    // useEffect flushes kbId (initial render value is '' before that resolves).
    const select = (await screen.findByRole('combobox')) as HTMLSelectElement;
    await waitFor(() => expect(select.value).toBe('kb-a'));

    // open the conversation bound to kb-b
    await userEvent.click(await screen.findByText('GL thread'));

    await waitFor(() => expect(select.value).toBe('kb-b'));
  });

  it('Finding B — numbered list renders an <ol> with list-style-type: decimal', async () => {
    convGet.mockResolvedValue({
      conversation: CONV,
      messages: [
        {
          id: 'm1',
          conversation_id: 'conv-b',
          role: 'assistant',
          content: '1. First step\n2. Second step\n3. Third step',
          citations: [],
          created_at: '2026-06-07T00:00:01Z',
        },
      ],
    });
    const { container } = renderChat();

    await userEvent.click(await screen.findByText('GL thread'));

    await waitFor(() => expect(container.querySelector('ol')).not.toBeNull());
    const ol = container.querySelector('ol') as HTMLOListElement;
    expect(ol.style.listStyleType).toBe('decimal');
  });
});
