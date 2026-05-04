'use client';

/**
 * End User Chat (`/`) — per architecture.md §5.2 + components/C10-chat-ui.md.
 *
 * W3 D4 baseline plain HTML/Tailwind (shadcn upgrade deferred to W3 D5 F8 polish
 * window per Karpathy §1.2 simplicity-first; matches W2 D5 admin-views pattern).
 *
 * SSE consumed via `streamQuery` async generator (lib/api/query.ts). Per-event
 * React state updates render token-by-token streaming + citation cards as they
 * arrive. Click thumbnail → ScreenshotModal full-image overlay (ESC closes).
 *
 * Layout reference Dify Image 5 chat + citation card (no code copy per CLAUDE.md §7);
 * EKP design tokens only via `oklch(...)` from `lib/theming/tokens.ts`.
 */

import { useEffect, useRef, useState, type FormEvent } from 'react';
import {
  streamQuery,
  type Citation,
  type ImageRef,
  type SseEvent,
} from '@/lib/api/query';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  citations: Citation[];
  isStreaming: boolean;
  refused: boolean;
  rerankerUsed: string;
  errorText: string | null;
}

const KB_ID = 'drive_user_manuals'; // W3 single-KB POC; multi-KB selector W7+ Beta

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [modalImage, setModalImage] = useState<ImageRef | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') setModalImage(null);
    }
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  function patchAssistant(id: string, mut: (m: Message) => Message) {
    setMessages((prev) =>
      prev.map((m) => (m.id === id && m.role === 'assistant' ? mut(m) : m)),
    );
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || isStreaming) return;

    const now = Date.now();
    const userMsg: Message = {
      id: `u-${now}`,
      role: 'user',
      content: trimmed,
      citations: [],
      isStreaming: false,
      refused: false,
      rerankerUsed: '',
      errorText: null,
    };
    const assistantId = `a-${now}`;
    const assistantMsg: Message = {
      id: assistantId,
      role: 'assistant',
      content: '',
      citations: [],
      isStreaming: true,
      refused: false,
      rerankerUsed: '',
      errorText: null,
    };
    setMessages((prev) => [...prev, userMsg, assistantMsg]);
    setInput('');
    setIsStreaming(true);

    const ac = new AbortController();
    abortRef.current = ac;

    try {
      const stream: AsyncIterable<SseEvent> = streamQuery(
        { query: trimmed, kb_id: KB_ID },
        ac.signal,
      );
      for await (const evt of stream) {
        if (evt.type === 'text-delta') {
          patchAssistant(assistantId, (m) => ({ ...m, content: m.content + evt.content }));
        } else if (evt.type === 'citation') {
          patchAssistant(assistantId, (m) => ({ ...m, citations: [...m.citations, evt.citation] }));
        } else if (evt.type === 'done') {
          patchAssistant(assistantId, (m) => ({
            ...m,
            isStreaming: false,
            refused: evt.refused,
            rerankerUsed: evt.reranker_used,
          }));
        }
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      patchAssistant(assistantId, (m) => ({
        ...m,
        isStreaming: false,
        errorText: msg,
      }));
    } finally {
      setIsStreaming(false);
      abortRef.current = null;
    }
  }

  function handleStop() {
    abortRef.current?.abort();
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-3xl flex-col px-4 py-8">
      <header className="mb-6 border-b border-[oklch(0.92_0_0)] pb-4">
        <h1 className="text-2xl font-semibold">EKP — Knowledge Chat</h1>
        <p className="mt-1 text-xs text-[oklch(0.45_0_0)]">
          KB: <span className="font-mono">{KB_ID}</span>
        </p>
      </header>

      <section className="flex-1 space-y-4">
        {messages.length === 0 && (
          <div className="rounded border border-dashed border-[oklch(0.92_0_0)] p-6 text-center text-sm text-[oklch(0.45_0_0)]">
            Ask about Ricoh financial software (AR / AP / FA / CB / GL / BM).
          </div>
        )}
        {messages.map((m) => (
          <MessageBubble key={m.id} message={m} onThumbnailClick={setModalImage} />
        ))}
      </section>

      <form
        onSubmit={handleSubmit}
        className="sticky bottom-0 mt-6 border-t border-[oklch(0.92_0_0)] bg-[oklch(1_0_0)] py-4"
      >
        <div className="flex gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question…"
            rows={2}
            className="flex-1 resize-none rounded border border-[oklch(0.92_0_0)] px-3 py-2 text-sm focus:border-[oklch(0.42_0.04_260)] focus:outline-none"
            disabled={isStreaming}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                e.currentTarget.form?.requestSubmit();
              }
            }}
          />
          {isStreaming ? (
            <button
              type="button"
              onClick={handleStop}
              className="rounded bg-[oklch(0.57_0.22_25)] px-4 py-2 text-sm font-medium text-white hover:bg-[oklch(0.50_0.22_25)]"
            >
              Stop
            </button>
          ) : (
            <button
              type="submit"
              disabled={!input.trim()}
              className="rounded bg-[oklch(0.42_0.04_260)] px-4 py-2 text-sm font-medium text-white hover:bg-[oklch(0.36_0.04_260)] disabled:opacity-50"
            >
              Send
            </button>
          )}
        </div>
      </form>

      {modalImage && <ScreenshotModal image={modalImage} onClose={() => setModalImage(null)} />}
    </main>
  );
}

function MessageBubble({
  message,
  onThumbnailClick,
}: {
  message: Message;
  onThumbnailClick: (img: ImageRef) => void;
}) {
  const isUser = message.role === 'user';
  return (
    <div className={isUser ? 'flex justify-end' : 'flex justify-start'}>
      <div
        className={[
          'max-w-[88%] rounded p-3 text-sm',
          isUser
            ? 'bg-[oklch(0.42_0.04_260)] text-white'
            : 'border border-[oklch(0.92_0_0)] bg-[oklch(0.98_0_0)]',
        ].join(' ')}
      >
        <div className="whitespace-pre-wrap">
          {message.content}
          {message.isStreaming && <span className="ml-1 animate-pulse">▍</span>}
        </div>

        {message.refused && (
          <div className="mt-2 rounded bg-[oklch(0.96_0.04_80)] px-2 py-1 text-xs text-[oklch(0.40_0.10_60)]">
            Refused — answer not found in available documentation.
          </div>
        )}

        {message.errorText && (
          <div className="mt-2 rounded border border-[oklch(0.57_0.22_25)] bg-[oklch(0.96_0.02_25)] p-2 text-xs">
            Stream error: {message.errorText}
          </div>
        )}

        {message.citations.length > 0 && (
          <div className="mt-3">
            <div className="text-xs font-medium uppercase tracking-wide text-[oklch(0.45_0_0)]">
              Citations ({message.citations.length})
            </div>
            <div className="mt-2 grid gap-2 sm:grid-cols-2">
              {message.citations.map((c) => (
                <CitationCard key={c.chunk_id} citation={c} onThumbnailClick={onThumbnailClick} />
              ))}
            </div>
          </div>
        )}

        {!isUser && !message.isStreaming && message.rerankerUsed && (
          <div className="mt-2 text-[10px] uppercase tracking-wide text-[oklch(0.55_0_0)]">
            reranker: {message.rerankerUsed}
          </div>
        )}
      </div>
    </div>
  );
}

function CitationCard({
  citation,
  onThumbnailClick,
}: {
  citation: Citation;
  onThumbnailClick: (img: ImageRef) => void;
}) {
  const sectionLabel = citation.section_path.length > 0 ? citation.section_path.join(' > ') : '—';
  const thumbnail = citation.embedded_images[0];
  return (
    <div className="rounded border border-[oklch(0.92_0_0)] bg-white p-2">
      <div className="text-xs font-semibold">{citation.chunk_title || '(untitled chunk)'}</div>
      <div className="mt-0.5 text-[11px] text-[oklch(0.45_0_0)]">{citation.doc_title}</div>
      <div className="mt-0.5 truncate font-mono text-[10px] text-[oklch(0.55_0_0)]" title={sectionLabel}>
        {sectionLabel}
      </div>
      {thumbnail && thumbnail.blob_url && (
        <button
          type="button"
          onClick={() => onThumbnailClick(thumbnail)}
          className="mt-2 block w-full overflow-hidden rounded border border-[oklch(0.92_0_0)] hover:border-[oklch(0.42_0.04_260)]"
        >
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={thumbnail.blob_url}
            alt={thumbnail.alt_text || 'screenshot thumbnail'}
            className="h-24 w-full object-cover"
          />
        </button>
      )}
      <div className="mt-1 text-[10px] text-[oklch(0.55_0_0)]">
        score: {citation.relevance_score.toFixed(3)}
      </div>
    </div>
  );
}

function ScreenshotModal({
  image,
  onClose,
}: {
  image: ImageRef;
  onClose: () => void;
}) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4"
      role="dialog"
      aria-modal="true"
      onClick={onClose}
    >
      <div
        className="relative max-h-full max-w-4xl overflow-hidden rounded bg-white"
        onClick={(e) => e.stopPropagation()}
      >
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={image.blob_url}
          alt={image.alt_text || 'screenshot full view'}
          className="max-h-[85vh] w-auto"
        />
        <button
          type="button"
          onClick={onClose}
          className="absolute right-2 top-2 rounded bg-black/60 px-3 py-1 text-xs text-white hover:bg-black/80"
        >
          Close (Esc)
        </button>
      </div>
    </div>
  );
}
