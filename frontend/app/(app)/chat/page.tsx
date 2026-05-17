'use client';

/**
 * End User Chat (`/chat`) — per architecture.md v6 §5.2 + ADR-0031 Option B
 * server-side Conversation History; C10 §7 Tier 2 → Tier 1 promoted.
 *
 * W20 F3.5-F3.12 — advanced chat surfaces landed on top of the W18 AppShell
 * mount (W13 routing) + W3 SSE streaming. The surface now ships:
 *   - Conversation History sidebar (`<ConversationHistory>`) — server-side
 *     persistence via /conversations CRUD; collapse persisted to localStorage
 *     so it survives reloads (matches the AppShell focus-mode pattern, but the
 *     control is local to this page — the AppShell sidebar is orthogonal).
 *   - Per-turn message persistence — after each SSE round-trip settles, the
 *     user prompt + the assistant reply are POSTed to
 *     /conversations/{id}/messages. The server auto-titles the conversation on
 *     the first user turn (50-char slice — Wave B+ may LLM-summarise).
 *   - 3 citation placement modes (`inline` / `footnote` / `sidebar`) toggled
 *     in the page header; the choice is persisted to localStorage.
 *   - InlineImageCard / ImageGallery / CitationPill hover popover — consume the
 *     existing Citation + ImageRef schema (no backend change).
 *   - FeedbackBar comment + tag dropdown — extends the W8 thumbs UI; writes to
 *     the existing POST /feedback (`comment` is prefixed with the chosen tag).
 *   - CRAG strip — dormant in the SSE path (stream is L3-only per §3.5), but
 *     the wiring is in place for Wave B+ L3 enable.
 *
 * SSE streaming logic (`streamQuery` from lib/api/query) is preserved exactly
 * — the W13 / W18 layout integration (renders inside `<AppShell>`, reads `?q=`
 * deep-link) is unchanged. The persistence layer is a thin async tail after
 * the `done` event — failures are swallowed (the user shouldn't lose a turn to
 * a transient DB blip; the on-page message state is the source of truth for
 * the active session).
 */

import { useEffect, useRef, useState, type FormEvent } from 'react';
import { PanelLeftClose, PanelLeftOpen } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { CitationPill } from '@/components/chat/citation-pill';
import { ConversationHistory } from '@/components/chat/conversation-history';
import { CragStrip } from '@/components/chat/crag-strip';
import { FeedbackBar } from '@/components/chat/feedback-bar';
import { ImageGallery } from '@/components/chat/image-gallery';
import { InlineImageCard } from '@/components/chat/inline-image-card';
import { conversationsApi, type Conversation } from '@/lib/api/conversations';
import {
  streamQuery,
  type Citation,
  type ImageRef,
  type SseEvent,
} from '@/lib/api/query';
import { cn } from '@/lib/utils';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  citations: Citation[];
  isStreaming: boolean;
  refused: boolean;
  rerankerUsed: string;
  errorText: string | null;
  cragTriggered: boolean;
  cragIterations: number;
}

type CitationMode = 'inline' | 'footnote' | 'sidebar';

const KB_ID = 'drive_user_manuals'; // W3 single-KB POC; multi-KB selector W7+ Beta
const CITATION_MODE_KEY = 'ekp-citation-mode';
const HISTORY_COLLAPSED_KEY = 'ekp-chat-history-collapsed';

function isCitationMode(value: string | null): value is CitationMode {
  return value === 'inline' || value === 'footnote' || value === 'sidebar';
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [activeConvId, setActiveConvId] = useState<string | null>(null);
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [modalImage, setModalImage] = useState<ImageRef | null>(null);
  const [citationMode, setCitationMode] = useState<CitationMode>('inline');
  const [historyCollapsed, setHistoryCollapsed] = useState(false);
  const abortRef = useRef<AbortController | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  // Hydrate persisted preferences after mount (SSR-stable hydration).
  useEffect(() => {
    const stored = window.localStorage.getItem(CITATION_MODE_KEY);
    if (isCitationMode(stored)) setCitationMode(stored);
    if (window.localStorage.getItem(HISTORY_COLLAPSED_KEY) === '1') {
      setHistoryCollapsed(true);
    }
  }, []);

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

  function handleCitationMode(mode: CitationMode) {
    setCitationMode(mode);
    window.localStorage.setItem(CITATION_MODE_KEY, mode);
  }

  function toggleHistory() {
    setHistoryCollapsed((prev) => {
      const next = !prev;
      window.localStorage.setItem(HISTORY_COLLAPSED_KEY, next ? '1' : '0');
      return next;
    });
  }

  async function ensureConversation(): Promise<string | null> {
    if (activeConvId) return activeConvId;
    try {
      const conv = await conversationsApi.create({ kb_id: KB_ID });
      setActiveConvId(conv.id);
      return conv.id;
    } catch {
      // The user might not be authed yet — keep the chat usable without persistence.
      return null;
    }
  }

  async function loadConversation(conversationId: string) {
    setActiveConvId(conversationId);
    try {
      const detail = await conversationsApi.get(conversationId);
      const hydrated: Message[] = detail.messages.map((m) => ({
        id: m.id,
        role: m.role,
        content: m.content,
        citations: m.citations ?? [],
        isStreaming: false,
        refused: false,
        rerankerUsed: '',
        errorText: null,
        cragTriggered: false,
        cragIterations: 0,
      }));
      setMessages(hydrated);
    } catch {
      setMessages([]);
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || isStreaming) return;

    const conversationId = await ensureConversation();

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
      cragTriggered: false,
      cragIterations: 0,
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
      cragTriggered: false,
      cragIterations: 0,
    };
    setMessages((prev) => [...prev, userMsg, assistantMsg]);
    setInput('');
    setIsStreaming(true);

    // Persist the user turn before the assistant streams (best effort — a 401 /
    // network blip shouldn't block the SSE round-trip from rendering).
    if (conversationId) {
      conversationsApi
        .appendMessage(conversationId, { role: 'user', content: trimmed })
        .catch(() => {});
    }

    const ac = new AbortController();
    abortRef.current = ac;

    const collected: Citation[] = [];
    let finalContent = '';
    try {
      const stream: AsyncIterable<SseEvent> = streamQuery(
        { query: trimmed, kb_id: KB_ID },
        ac.signal,
      );
      for await (const evt of stream) {
        if (evt.type === 'text-delta') {
          finalContent += evt.content;
          patchAssistant(assistantId, (m) => ({
            ...m,
            content: m.content + evt.content,
          }));
        } else if (evt.type === 'citation') {
          collected.push(evt.citation);
          patchAssistant(assistantId, (m) => ({
            ...m,
            citations: [...m.citations, evt.citation],
          }));
        } else if (evt.type === 'done') {
          patchAssistant(assistantId, (m) => ({
            ...m,
            isStreaming: false,
            refused: evt.refused,
            rerankerUsed: evt.reranker_used,
          }));
        }
      }

      // Persist the assistant turn now that the stream has settled (best effort).
      if (conversationId && finalContent) {
        conversationsApi
          .appendMessage(conversationId, {
            role: 'assistant',
            content: finalContent,
            citations: collected.length > 0 ? collected : null,
          })
          .catch(() => {});
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

  function handleConversationCreate(conv: Conversation) {
    setActiveConvId(conv.id);
    setMessages([]);
  }

  function handleActiveDeleted() {
    setActiveConvId(null);
    setMessages([]);
  }

  // Aggregate all image refs across the conversation (W20 F3.9).
  const galleryImages: ImageRef[] = messages
    .flatMap((m) => m.citations.flatMap((c) => c.embedded_images))
    .filter((img): img is ImageRef => Boolean(img && img.blob_url));

  // Sidebar mode: aggregate the latest assistant turn's citations.
  const latestAssistantCitations: Citation[] =
    [...messages].reverse().find((m) => m.role === 'assistant')?.citations ?? [];

  // F1-pivot per CLAUDE.md §5.7 H7 (2026-05-18): /chat is full-bleed per mockup
  // `ekp-page-chat.jsx:88-94` (3-pane grid `calc(100vh - var(--topbar-h))`).
  // AppShell no longer injects `.content`. Transient `flex-1 min-h-0` outer makes
  // the W20 layout fill the remaining flex-column space inside `.main` until F4
  // chat rebuild adopts the mockup's grid + height calc.
  return (
    <div className="flex flex-1 h-full min-h-0 gap-0">
      {!historyCollapsed && (
        <div className="hidden w-56 shrink-0 md:block">
          <ConversationHistory
            activeConversationId={activeConvId}
            onSelect={(id) => {
              void loadConversation(id);
            }}
            onCreate={handleConversationCreate}
            onActiveDeleted={handleActiveDeleted}
          />
        </div>
      )}

      <div className="mx-auto flex h-full min-w-0 flex-1 flex-col">
        <ChatHeader
          citationMode={citationMode}
          onCitationModeChange={handleCitationMode}
          historyCollapsed={historyCollapsed}
          onToggleHistory={toggleHistory}
        />

        <div className={cn('flex flex-1 min-h-0 gap-4', 'overflow-hidden')}>
          <section className="flex-1 space-y-4 overflow-y-auto pr-1">
            {messages.length === 0 && (
              <div className="rounded-md border border-dashed border-border p-6 text-center text-sm text-muted-foreground">
                Ask about Ricoh financial software (AR / AP / FA / CB / GL / BM).
              </div>
            )}
            {messages.map((m) => (
              <MessageBubble
                key={m.id}
                message={m}
                citationMode={citationMode}
                onThumbnailClick={setModalImage}
              />
            ))}
            <ImageGallery images={galleryImages} onSelect={setModalImage} />
          </section>

          {citationMode === 'sidebar' && latestAssistantCitations.length > 0 && (
            <aside
              aria-label="Citations sidebar"
              className="hidden w-72 shrink-0 overflow-y-auto border-l border-border pl-3 lg:block"
            >
              <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Citations ({latestAssistantCitations.length})
              </h3>
              <div className="space-y-2">
                {latestAssistantCitations.map((c) => (
                  <CitationCard
                    key={c.chunk_id}
                    citation={c}
                    onThumbnailClick={setModalImage}
                  />
                ))}
              </div>
            </aside>
          )}
        </div>

        <form
          onSubmit={handleSubmit}
          className="mt-4 border-t border-border bg-background py-4"
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
      </div>

      {modalImage && <ScreenshotModal image={modalImage} onClose={() => setModalImage(null)} />}
    </div>
  );
}

// --------------------------------------------------------------------------- //
// Page header — citation mode toggle + history collapse toggle
// --------------------------------------------------------------------------- //

function ChatHeader({
  citationMode,
  onCitationModeChange,
  historyCollapsed,
  onToggleHistory,
}: {
  citationMode: CitationMode;
  onCitationModeChange: (mode: CitationMode) => void;
  historyCollapsed: boolean;
  onToggleHistory: () => void;
}) {
  return (
    <div className="mb-4 flex items-center justify-between gap-3 border-b border-border pb-3">
      <div className="flex items-center gap-2">
        <Button
          variant="ghost"
          size="icon"
          aria-label={historyCollapsed ? 'Show conversation history' : 'Hide conversation history'}
          aria-pressed={historyCollapsed}
          onClick={onToggleHistory}
          className="hidden h-8 w-8 md:inline-flex"
        >
          {historyCollapsed ? (
            <PanelLeftOpen className="h-4 w-4" />
          ) : (
            <PanelLeftClose className="h-4 w-4" />
          )}
        </Button>
        <h1 className="text-lg font-semibold">Chat</h1>
      </div>
      <div className="flex items-center gap-3">
        <span className="text-xs text-muted-foreground">
          KB: <span className="font-mono">{KB_ID}</span>
        </span>
        <fieldset
          className="hidden items-center gap-1 rounded-md border border-border p-0.5 text-[11px] sm:flex"
          aria-label="Citation placement"
        >
          <legend className="sr-only">Citation placement</legend>
          {(['inline', 'footnote', 'sidebar'] as const).map((m) => (
            <button
              key={m}
              type="button"
              onClick={() => onCitationModeChange(m)}
              aria-pressed={citationMode === m}
              className={cn(
                'rounded px-2 py-0.5 capitalize text-muted-foreground',
                citationMode === m && 'bg-accent/15 text-accent',
              )}
            >
              {m}
            </button>
          ))}
        </fieldset>
      </div>
    </div>
  );
}

// --------------------------------------------------------------------------- //
// Message bubble — branches on citation mode
// --------------------------------------------------------------------------- //

function MessageBubble({
  message,
  citationMode,
  onThumbnailClick,
}: {
  message: Message;
  citationMode: CitationMode;
  onThumbnailClick: (img: ImageRef) => void;
}) {
  const isUser = message.role === 'user';
  return (
    <div className={isUser ? 'flex justify-end' : 'flex justify-start'}>
      <div
        className={cn(
          'max-w-[88%] rounded-md p-3 text-sm',
          isUser
            ? 'bg-primary text-primary-foreground'
            : 'border border-border bg-muted/50',
        )}
      >
        {!isUser && (
          <CragStrip
            cragTriggered={message.cragTriggered}
            cragIterations={message.cragIterations}
          />
        )}

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

        {message.citations.length > 0 && citationMode === 'inline' && (
          <InlineCitations
            citations={message.citations}
            onThumbnailClick={onThumbnailClick}
          />
        )}

        {message.citations.length > 0 && citationMode === 'footnote' && (
          <FootnoteCitations citations={message.citations} />
        )}

        {/* `sidebar` mode renders nothing inside the bubble — citations live in the right pane. */}

        {!isUser && !message.isStreaming && message.rerankerUsed && (
          <div className="mt-2 text-[10px] uppercase tracking-wide text-muted-foreground">
            reranker: {message.rerankerUsed}
          </div>
        )}

        {!isUser && !message.isStreaming && <FeedbackBar traceId="" />}
      </div>
    </div>
  );
}

function InlineCitations({
  citations,
  onThumbnailClick,
}: {
  citations: Citation[];
  onThumbnailClick: (img: ImageRef) => void;
}) {
  return (
    <div className="mt-3">
      <div className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
        Citations ({citations.length})
      </div>
      <div className="mt-2 grid gap-2 sm:grid-cols-2">
        {citations.map((c) => (
          <CitationCard
            key={c.chunk_id}
            citation={c}
            onThumbnailClick={onThumbnailClick}
          />
        ))}
      </div>
    </div>
  );
}

function FootnoteCitations({ citations }: { citations: Citation[] }) {
  return (
    <ol className="mt-3 space-y-1 border-t border-border pt-2 text-[11px] text-muted-foreground">
      {citations.map((c, idx) => (
        <li key={c.chunk_id} className="flex items-start gap-2">
          <CitationPill citation={c} index={idx + 1} />
          <span className="flex-1">
            <span className="font-medium text-foreground">{c.doc_title}</span>
            {c.chunk_title ? ` — ${c.chunk_title}` : ''}
          </span>
        </li>
      ))}
    </ol>
  );
}

function CitationCard({
  citation,
  onThumbnailClick,
}: {
  citation: Citation;
  onThumbnailClick: (img: ImageRef) => void;
}) {
  const sectionLabel =
    citation.section_path.length > 0 ? citation.section_path.join(' > ') : '—';
  const thumbnail = citation.embedded_images[0];
  return (
    <div className="rounded-md border border-border bg-card p-2">
      <div className="text-xs font-semibold">
        {citation.chunk_title || '(untitled chunk)'}
      </div>
      <div className="mt-0.5 text-[11px] text-muted-foreground">{citation.doc_title}</div>
      <div
        className="mt-0.5 truncate font-mono text-[10px] text-muted-foreground"
        title={sectionLabel}
      >
        {sectionLabel}
      </div>
      {thumbnail && thumbnail.blob_url && (
        <InlineImageCard image={thumbnail} onClick={onThumbnailClick} />
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
      className="fixed inset-0 z-50 flex items-center justify-center bg-foreground/70 p-4"
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
        {image.alt_text && (
          <div className="border-t border-border bg-background px-3 py-2 text-xs text-muted-foreground">
            {image.alt_text}
          </div>
        )}
        <button
          type="button"
          onClick={onClose}
          className="absolute right-2 top-2 rounded-sm bg-foreground/60 px-3 py-1 text-xs text-background transition-colors hover:bg-foreground/80"
        >
          Close (Esc)
        </button>
      </div>
    </div>
  );
}
