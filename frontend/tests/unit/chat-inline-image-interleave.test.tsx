/**
 * Unit test — W71 (ADR-0055) — inline image marker INTERLEAVE render.
 *
 * Drives a full streamQuery whose answer carries `[IMG#<sha8>]` markers and
 * asserts the chat anchors an InlineImageCard at each marker position (figure
 * numbered), never leaks the raw marker text, strips a marker for a non-
 * surviving image, and keeps the "Referenced screenshots" gallery full. A
 * marker-less answer keeps the pre-W71 behaviour (all images in the trailing
 * pile).
 */

import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { ReactNode } from 'react';

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
  kb_id: 'drive-images-1',
  name: 'drive-images-1',
  description: 'drive-images-1',
  config: {
    embedding_model: 'text-embedding-3-large',
    embedding_dimension: 1024,
    chunk_strategy: 'auto' as const,
    default_top_k: 50,
    default_rerank_k: 10,
  },
  total_documents: 1,
  total_chunks: 369,
  total_screenshots: 2,
  failed_documents: [],
  last_indexed_at: '2026-06-12T00:00:00Z',
  storage_size_mb: 0,
  archived: false,
};

// checksum_sha256 whose first 8 hex are the marker sha8.
function citationWithImage(idx: number, checksum: string) {
  return {
    chunk_id: `chunk-${idx}`,
    doc_id: `doc-${idx}.docx`,
    doc_title: `Document ${idx}`,
    doc_format: 'docx' as const,
    chunk_title: `Section ${idx}`,
    chunk_index: idx,
    section_path: ['A', 'B'],
    relevance_score: 0.9,
    embedded_images: [
      {
        blob_url: `https://blob.example/${checksum}.png`,
        alt_text: `Payment step ${idx}`,
        checksum_sha256: checksum,
        width: 800,
        height: 480,
      },
    ],
  };
}

const DONE = {
  type: 'done' as const,
  model: 'gpt-5.5',
  input_tokens: 1,
  output_tokens: 1,
  cost: 0.001,
  latency_ms: 2000,
  refused: false,
  reranker_used: 'cohere-v4.0-pro',
};

function renderChat() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <ChatPage />
    </QueryClientProvider>,
  );
}

async function sendQuery() {
  await screen.findByRole('option', { name: /drive-images-1/i });
  const composer = screen.getByPlaceholderText(/ask about ricoh/i);
  await userEvent.type(composer, 'how do I record a payment');
  fireEvent.submit(composer.closest('form')!);
}

describe('W71 — inline image interleave render', () => {
  beforeEach(() => {
    streamQuery.mockReset();
    kbList.mockReset();
    convCreate.mockReset();
    kbList.mockResolvedValue([FAKE_KB]);
    convCreate.mockResolvedValue({ id: 'conv-1', kb_id: 'drive-images-1' });
  });

  it('anchors a figure-numbered card at each marker and never leaks the marker text', async () => {
    streamQuery.mockImplementation(() =>
      (async function* () {
        yield {
          type: 'text-delta',
          content: 'Open the journal. [IMG#a1b2c3d4]\n\nThen post it. [IMG#b2c3d4e5]',
        };
        yield { type: 'citation', citation: citationWithImage(1, 'a1b2c3d4ffff0000') };
        yield { type: 'citation', citation: citationWithImage(2, 'b2c3d4e5ffff0000') };
        yield DONE;
      })(),
    );

    const { container } = renderChat();
    await sendQuery();

    // Both markers anchored → both cards render in the answer flow, figure-numbered.
    await waitFor(() => expect(screen.getByText('figure 1')).toBeInTheDocument());
    expect(screen.getByText('figure 2')).toBeInTheDocument();
    // Raw marker text must never reach the DOM (W70 strip guarantee continues).
    expect(container.textContent).not.toContain('[IMG#');
    // The collective gallery still lists all referenced screenshots.
    expect(screen.getByText('Referenced screenshots')).toBeInTheDocument();
  });

  it('strips a marker whose image is not among the surviving set (no broken card)', async () => {
    streamQuery.mockImplementation(() =>
      (async function* () {
        yield {
          type: 'text-delta',
          content: 'Open the journal. [IMG#deadbeef] then continue.',
        };
        // the only real image has no marker → it goes to the trailing pile
        yield { type: 'citation', citation: citationWithImage(1, 'a1b2c3d4ffff0000') };
        yield DONE;
      })(),
    );

    const { container } = renderChat();
    await sendQuery();

    await waitFor(() => expect(screen.getByText('Referenced screenshots')).toBeInTheDocument());
    // the hallucinated marker is stripped, not rendered as text or a card
    expect(container.textContent).not.toContain('[IMG#deadbeef]');
    // the real image still shows as a trailing card (figure 1 — nothing anchored)
    expect(screen.getByText('figure 1')).toBeInTheDocument();
    expect(screen.queryByText('figure 2')).not.toBeInTheDocument();
  });

  it('renders a marker-less answer exactly as before (all images trail)', async () => {
    streamQuery.mockImplementation(() =>
      (async function* () {
        yield { type: 'text-delta', content: 'A plain answer with no markers.' };
        yield { type: 'citation', citation: citationWithImage(1, 'a1b2c3d4ffff0000') };
        yield { type: 'citation', citation: citationWithImage(2, 'b2c3d4e5ffff0000') };
        yield DONE;
      })(),
    );

    renderChat();
    await sendQuery();

    // Two trailing cards (figure 1 + 2) + the gallery — pre-W71 behaviour.
    await waitFor(() => expect(screen.getByText('figure 1')).toBeInTheDocument());
    expect(screen.getByText('figure 2')).toBeInTheDocument();
    expect(screen.getByText('Referenced screenshots')).toBeInTheDocument();
  });

  it('copies the answer with image AND citation markers stripped (DD-8)', async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, 'clipboard', {
      value: { writeText },
      configurable: true,
    });
    streamQuery.mockImplementation(() =>
      (async function* () {
        yield {
          type: 'text-delta',
          content: 'Open the journal. [IMG#a1b2c3d4] See [chunk-chunk-1] then post.',
        };
        yield { type: 'citation', citation: citationWithImage(1, 'a1b2c3d4ffff0000') };
        yield DONE;
      })(),
    );

    renderChat();
    await sendQuery();

    const copyButton = await screen.findByTitle('Copy answer');
    fireEvent.click(copyButton);

    await waitFor(() => expect(writeText).toHaveBeenCalledTimes(1));
    const copied = writeText.mock.calls[0]![0] as string;
    expect(copied).not.toContain('[IMG#');
    expect(copied).not.toContain('[chunk-');
    expect(copied).toContain('Open the journal.');
    expect(copied).toContain('then post.');
  });
});
