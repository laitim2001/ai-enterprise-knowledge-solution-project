/**
 * Unit test — chat assistant meta row + ImageGallery (BUG-007).
 *
 * BUG-007 restored 3 mockup-spec'd surfaces the W22 F4 rebuild dropped:
 *   - the assistant meta row shows the synthesis model name + USD cost
 *   - the "Referenced screenshots" ImageGallery renders below the answer
 *     when 2+ cited chunks carry embedded images
 *
 * Each test drives a full streamQuery (text-delta + citation* + done) and
 * asserts the rendered assistant turn. Pre-fix the meta row had no model /
 * cost and ImageGallery did not exist.
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
  total_screenshots: 2,
  failed_documents: [],
  last_indexed_at: '2026-05-22T00:00:00Z',
  storage_size_mb: 0,
  archived: false,
};

function imageRef(name: string) {
  return {
    blob_url: `https://blob.example/${name}.png`,
    alt_text: `${name} screenshot`,
    checksum_sha256: name,
    width: 800,
    height: 480,
  };
}

function citation(idx: number, withImage: boolean) {
  return {
    chunk_id: `chunk-${idx}`,
    doc_id: `doc-${idx}.docx`,
    doc_title: `Document ${idx}`,
    doc_format: 'docx' as const,  // BUG-021 — mirror backend Literal schema
    chunk_title: `Section ${idx}`,
    chunk_index: idx,
    section_path: ['A', 'B'],
    relevance_score: 0.9,
    embedded_images: withImage ? [imageRef(`shot-${idx}`)] : [],
  };
}

function renderChat() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <ChatPage />
    </QueryClientProvider>,
  );
}

async function sendQuery() {
  await screen.findByRole('option', { name: /drive-user-manual-1/i });
  const composer = screen.getByPlaceholderText(/ask about ricoh/i);
  await userEvent.type(composer, 'what is in the document');
  fireEvent.submit(composer.closest('form')!);
}

describe('Chat assistant meta row + ImageGallery (BUG-007)', () => {
  beforeEach(() => {
    streamQuery.mockReset();
    kbList.mockReset();
    convCreate.mockReset();
    kbList.mockResolvedValue([FAKE_KB]);
    convCreate.mockResolvedValue({ id: 'conv-1', kb_id: 'drive-user-manual-1' });
  });

  it('renders the synthesis model name and USD cost in the meta row', async () => {
    streamQuery.mockImplementation(() =>
      (async function* () {
        yield { type: 'text-delta', content: 'Answer body.' };
        yield {
          type: 'done',
          model: 'gpt-5.5',
          input_tokens: 2000,
          output_tokens: 500,
          cost: 0.029,
          latency_ms: 4130,
          refused: false,
          reranker_used: 'cohere-v4.0-pro',
        };
      })(),
    );

    renderChat();
    await sendQuery();

    // Meta row span text: "gpt-5.5 · cohere-v4.0-pro · 0 citations"
    await waitFor(() =>
      expect(screen.getByText(/gpt-5\.5/)).toBeInTheDocument(),
    );
    // Latency span text: "4.13s · $0.029"
    expect(screen.getByText(/\$0\.029/)).toBeInTheDocument();
  });

  it('renders the "Referenced screenshots" gallery for 2+ image citations', async () => {
    streamQuery.mockImplementation(() =>
      (async function* () {
        yield { type: 'text-delta', content: 'Answer with images.' };
        yield { type: 'citation', citation: citation(1, true) };
        yield { type: 'citation', citation: citation(2, true) };
        yield { type: 'citation', citation: citation(3, false) };
        yield {
          type: 'done',
          model: 'gpt-5.5',
          input_tokens: 1,
          output_tokens: 1,
          cost: 0.001,
          latency_ms: 2000,
          refused: false,
          reranker_used: 'cohere-v4.0-pro',
        };
      })(),
    );

    renderChat();
    await sendQuery();

    await waitFor(() =>
      expect(screen.getByText('Referenced screenshots')).toBeInTheDocument(),
    );
    // Two image-bearing citations → two InlineImageCard renders (per BUG-019,
    // mockup ekp-page-chat.jsx:470-498 — each image-bearing citation gets an
    // inline card in the answer body) + two ImageGallery thumbnails (collective
    // fallback per mockup line 354-357 `>=2` gate). 2 inline + 2 gallery = 4.
    expect(screen.getAllByRole('img')).toHaveLength(4);
  });

  it('renders the "Referenced screenshots" gallery for exactly 1 image citation (BUG-021 reversal — ImageGallery `>=1` unifies 1- and 2+-image cases)', async () => {
    streamQuery.mockImplementation(() =>
      (async function* () {
        yield { type: 'text-delta', content: 'Answer with one image.' };
        yield { type: 'citation', citation: citation(1, true) };
        yield { type: 'citation', citation: citation(2, false) };
        yield {
          type: 'done',
          model: 'gpt-5.5',
          input_tokens: 1,
          output_tokens: 1,
          cost: 0.001,
          latency_ms: 2000,
          refused: false,
          reranker_used: 'cohere-v4.0-pro',
        };
      })(),
    );

    renderChat();
    await sendQuery();

    // BUG-021 — same canonical ImageGallery surfaces for 1-image case post-gate
    // lowering. SingleScreenshotStrip dropped (was BUG-020 hybrid). "Single
    // screenshot" label must NOT appear; "Referenced screenshots" must.
    await waitFor(() =>
      expect(screen.getByText('Referenced screenshots')).toBeInTheDocument(),
    );
    expect(screen.queryByText('Single screenshot')).not.toBeInTheDocument();
    // 1 InlineImageCard (BUG-019 inline render) + 1 ImageGallery thumbnail = 2 imgs.
    expect(screen.getAllByRole('img')).toHaveLength(2);
  });

  it('renders citation pills unconditionally after answer body (BUG-020 — removes citationMode === "inline" gate)', async () => {
    streamQuery.mockImplementation(() =>
      (async function* () {
        yield { type: 'text-delta', content: 'Answer text.' };
        yield { type: 'citation', citation: citation(1, false) };
        yield { type: 'citation', citation: citation(2, false) };
        yield { type: 'citation', citation: citation(3, false) };
        yield {
          type: 'done',
          model: 'gpt-5.5',
          input_tokens: 1,
          output_tokens: 1,
          cost: 0.001,
          latency_ms: 1000,
          refused: false,
          reranker_used: 'cohere-v4.0-pro',
        };
      })(),
    );

    renderChat();
    await sendQuery();

    // CitationPill row renders 1, 2, 3 numeric pills unconditionally (citationMode
    // defaults to 'sidebar' so the W22 gate would have hidden them). PanelSourceCard
    // in the right Sources panel also surfaces each citation as an idx circle, so
    // each digit appears at least twice in the DOM — assert that count to verify
    // both the pill row AND the panel render the citations.
    await waitFor(() => expect(screen.getByText('Answer text.')).toBeInTheDocument());
    expect(screen.getAllByText('1').length).toBeGreaterThanOrEqual(2);
    expect(screen.getAllByText('2').length).toBeGreaterThanOrEqual(2);
    expect(screen.getAllByText('3').length).toBeGreaterThanOrEqual(2);
  });

  it('renders markdown formatting in the answer body (BUG-021 + ADR-0036 react-markdown dep)', async () => {
    streamQuery.mockImplementation(() =>
      (async function* () {
        yield {
          type: 'text-delta',
          content:
            'Lead **bold** intro.\n\n1. First step here\n2. Second step here',
        };
        yield { type: 'citation', citation: citation(1, false) };
        yield {
          type: 'done',
          model: 'gpt-5.5',
          input_tokens: 1,
          output_tokens: 1,
          cost: 0.001,
          latency_ms: 1000,
          refused: false,
          reranker_used: 'cohere-v4.0-pro',
        };
      })(),
    );

    renderChat();
    await sendQuery();

    // <strong> rendered for **bold** + numbered list <ol><li> for `1. ... 2. ...`
    await waitFor(() => expect(screen.getByText('bold')).toBeInTheDocument());
    const strong = screen.getByText('bold');
    expect(strong.tagName).toBe('STRONG');
    expect(screen.getByText('First step here').closest('li')).not.toBeNull();
    expect(screen.getByText('Second step here').closest('li')).not.toBeNull();
  });

  it('replaces verbose [chunk-{id}] markers with inline numeric pills (BUG-021)', async () => {
    streamQuery.mockImplementation(() =>
      (async function* () {
        yield {
          type: 'text-delta',
          content:
            'Architecture overview [chunk-chunk-1] with platform components [chunk-chunk-2].',
        };
        yield { type: 'citation', citation: citation(1, false) };
        yield { type: 'citation', citation: citation(2, false) };
        yield {
          type: 'done',
          model: 'gpt-5.5',
          input_tokens: 1,
          output_tokens: 1,
          cost: 0.001,
          latency_ms: 1000,
          refused: false,
          reranker_used: 'cohere-v4.0-pro',
        };
      })(),
    );

    renderChat();
    await sendQuery();

    // Verbose marker text must not appear inline (regex match — surrounding
    // text split into [text, pill, text, pill, text] children so getByText
    // exact-match would miss). Numeric pills replace markers inline.
    await waitFor(() =>
      expect(
        screen.getByText(/Architecture overview/),
      ).toBeInTheDocument(),
    );
    expect(
      screen.queryByText(/\[chunk-chunk-1\]/),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByText(/\[chunk-chunk-2\]/),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByText(/⟦CIT/),
    ).not.toBeInTheDocument();
  });

  it('renders the sources-panel toggle in the header', async () => {
    // ChatHeader shows the BookOpen sources-panel toggle in sidebar mode (the
    // mockup default). BUG-007 amendment — a stale `ekp-citation-mode`
    // localStorage value used to flip citationMode to `inline` and hide it.
    renderChat();
    await screen.findByRole('option', { name: /drive-user-manual-1/i });
    expect(
      screen.getByRole('button', { name: /sources panel/i }),
    ).toBeInTheDocument();
  });
});
