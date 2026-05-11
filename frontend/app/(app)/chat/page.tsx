'use client';

/**
 * End User Chat (`/chat`) — per architecture.md v6 §5.2 + components/C10-chat-ui.md.
 *
 * W13 D1 F1.1 routing restructure: moved from `/` to `/chat` so root path
 * (`/`) becomes V7 Landing public marketing-style entry per ADR-0015 UI Tier 1
 * expansion. Functional logic preserved exactly — only file path changed.
 *
 * W18 F3 (per ADR-0024): relocated into the app/(app)/ route group (URL
 * unchanged — /chat); now rendered inside <AppShell>, so the page's own <main>
 * + min-h-screen became a <div> + h-full and the title row slimmed (the "EKP"
 * wordmark + chrome live in the AppShell top bar / sidebar now). SSE-chat logic
 * unchanged.
 *
 * W18 F6: reads the `?q=` deep-link on first mount (the global-search palette's
 * "Ask in chat: …" action navigates here with the query in the URL) → pre-fills
 * the input + focuses it; the user hits Enter to send. Pre-fill only — the chat
 * input / streaming logic is otherwise untouched.
 *
 * W12 D4 F4.4 tokens migration:hardcoded inline color Tailwind arbitrary values
 * replaced with token-referenced classes(`bg-primary` / `border-border` / etc)
 * wired via Tailwind config to CSS custom properties(globals.css :root + .dark)。
 *
 * Send + Stop buttons upgraded to shadcn Button(default + destructive variants)
 * per F3.5 head-start pattern;remaining inline elements still plain HTML w/
 * token classes(full shadcn form refactor defer W13-W14 view-level work)。
 *
 * SSE consumed via `streamQuery` async generator(lib/api/query.ts)。Per-event
 * React state updates render token-by-token streaming + citation cards as they
 * arrive。Click thumbnail → ScreenshotModal full-image overlay(ESC closes)。
 *
 * Layout reference Dify Image 5 chat + citation card(no code copy per ADR-0010);
 * EKP visual identity via tokens.ts Option C "Warm Charcoal + Coral Accent"。
 */

import { useEffect, useRef, useState, type FormEvent } from 'react';

import { Button } from '@/components/ui/button';
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
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') setModalImage(null);
    }
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  // Deep-link from the global-search "Ask in chat: …" action (W18 F6) — pre-fill on first mount.
  useEffect(() => {
    const q = new URLSearchParams(window.location.search).get('q');
    if (q && q.trim()) {
      setInput(q);
      textareaRef.current?.focus();
    }
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
    <div className="mx-auto flex h-full max-w-3xl flex-col">
      <div className="mb-4 flex items-baseline justify-between border-b border-border pb-3">
        <h1 className="text-lg font-semibold">Chat</h1>
        <span className="text-xs text-muted-foreground">
          KB: <span className="font-mono">{KB_ID}</span>
        </span>
      </div>

      <section className="flex-1 space-y-4">
        {messages.length === 0 && (
          <div className="rounded-md border border-dashed border-border p-6 text-center text-sm text-muted-foreground">
            Ask about Ricoh financial software (AR / AP / FA / CB / GL / BM).
          </div>
        )}
        {messages.map((m) => (
          <MessageBubble key={m.id} message={m} onThumbnailClick={setModalImage} />
        ))}
      </section>

      <form
        onSubmit={handleSubmit}
        className="sticky bottom-0 mt-6 border-t border-border bg-background py-4"
      >
        <div className="flex gap-2">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question…"
            rows={2}
            className="flex-1 resize-none rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm transition-colors placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
            disabled={isStreaming}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                e.currentTarget.form?.requestSubmit();
              }
            }}
          />
          {isStreaming ? (
            <Button type="button" variant="destructive" onClick={handleStop}>
              Stop
            </Button>
          ) : (
            <Button type="submit" disabled={!input.trim()}>
              Send
            </Button>
          )}
        </div>
      </form>

      {modalImage && <ScreenshotModal image={modalImage} onClose={() => setModalImage(null)} />}
    </div>
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
          'max-w-[88%] rounded-md p-3 text-sm',
          isUser
            ? 'bg-primary text-primary-foreground'
            : 'border border-border bg-muted/50',
        ].join(' ')}
      >
        <div className="whitespace-pre-wrap">
          {message.content}
          {message.isStreaming && <span className="ml-1 animate-pulse">▍</span>}
        </div>

        {message.refused && (
          <div className="mt-2 rounded-sm bg-warning/20 px-2 py-1 text-xs text-warning-foreground">
            Refused — answer not found in available documentation.
          </div>
        )}

        {message.errorText && (
          <div className="mt-2 rounded-sm border border-destructive bg-destructive/10 p-2 text-xs">
            Stream error: {message.errorText}
          </div>
        )}

        {message.citations.length > 0 && (
          <div className="mt-3">
            <div className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
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
          <div className="mt-2 text-[10px] uppercase tracking-wide text-muted-foreground">
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
    <div className="rounded-md border border-border bg-card p-2">
      <div className="text-xs font-semibold">{citation.chunk_title || '(untitled chunk)'}</div>
      <div className="mt-0.5 text-[11px] text-muted-foreground">{citation.doc_title}</div>
      <div
        className="mt-0.5 truncate font-mono text-[10px] text-muted-foreground"
        title={sectionLabel}
      >
        {sectionLabel}
      </div>
      {thumbnail && thumbnail.blob_url && (
        <button
          type="button"
          onClick={() => onThumbnailClick(thumbnail)}
          className="mt-2 block w-full overflow-hidden rounded-sm border border-border transition-colors hover:border-accent"
        >
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={thumbnail.blob_url}
            alt={thumbnail.alt_text || 'screenshot thumbnail'}
            className="h-24 w-full object-cover"
          />
        </button>
      )}
      <div className="mt-1 text-[10px] text-muted-foreground">
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
        className="relative max-h-full max-w-4xl overflow-hidden rounded-md bg-card"
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
          className="absolute right-2 top-2 rounded-sm bg-black/60 px-3 py-1 text-xs text-white transition-colors hover:bg-black/80"
        >
          Close (Esc)
        </button>
      </div>
    </div>
  );
}
