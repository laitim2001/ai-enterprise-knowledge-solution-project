'use client';

/**
 * Chat (`/chat`) — W22 F4 direct-copy from mockup
 * `references/design-mockups/ekp-page-chat.jsx` PageChat
 * (per CLAUDE.md §5.7 H7 strict fidelity 2026-05-18, AskUserQuestion picked
 * "Preserve W20 Tier 2 work + add mockup visual layer (Recommended)").
 *
 * 3-pane grid layout (mockup `gridTemplateColumns: "260px 1fr 400px"`,
 * `height: calc(100vh - var(--topbar-h))`, `overflow: hidden`) — replaces
 * the W20 `flex` layout that depended on AppShell `.content` wrapper.
 *
 * Preserved from W20 (per W22 plan §0 "preserve backend integration / state
 * mgmt"):
 *   - `streamQuery` SSE flow from `/lib/api/query`
 *   - `conversationsApi` CRUD (server-side Conversation History per
 *     ADR-0031 Option B → C10 §7 Tier 2 → Tier 1 promotion preserved)
 *   - localStorage keys (`ekp-chat-history-collapsed`, `ekp-chat-sources-collapsed`)
 *   - `?q=` deep-link from `<GlobalSearch>` (W18 F6)
 *   - Per-turn persistence (user prompt + assistant reply POST to
 *     `/conversations/{id}/messages` after `done` event;best-effort tail)
 *   - citationMode state machine + `inline`/`footnote`/`sidebar` placement
 *     consumers (MessageRow / SourcesStrip / CitationPanel)
 *
 * F4 fidelity correction 2026-05-18 — ChatHeader right-side rebuilt to mockup
 * direct-copy: CRAG switch + Show images switch + Focus eye + Sources book.
 * The W20-era 3-mode citation seg-toggle was removed (mockup never had it).
 * citationMode is fixed at `sidebar` per mockup (ekp-page-chat.jsx:79) — the
 * BookOpen header toggle + right CitationPanel render in that mode. It is not
 * persisted nor user-switchable: BUG-007 reverted a W22 F4 default flip, and
 * the BUG-007 amendment dropped the `ekp-citation-mode` localStorage hydration
 * (a stale W20-era value still overrode the default and hid the toggle).
 * The inline/footnote placement machinery stays dormant for future ADR use.
 *
 * Visual rebuild (mockup-direct per memory rule #1 + rule #2):
 *   - Inline ConversationHistoryPanel (260px aside, mockup lines 134-219)
 *   - Inline ChatHeader (KB chip + CRAG/images switches + focus/sources icons, mockup 257-298)
 *   - Inline ChatThread + MessageRow (user/assistant variants, mockup 301-373)
 *   - Inline FeedbackBar (mockup 377-440)
 *   - Inline SourcesStrip + SourceDocCard (footnote/inline mode footer, mockup 667-778)
 *   - Inline CitationPanel + PanelSourceCard (sidebar mode, mockup 799-869)
 *   - Inline ScreenshotModal (mockup 871-1009 estimate — pared back to
 *     practical viewer since real images come from blob_url, not synthetic)
 *   - Inline ChatComposer (textarea + submit)
 *
 * Obsolete W20 separate components are deleted alongside (ConversationHistory,
 * FeedbackBar, CragStrip) — they were custom abstractions not matching mockup
 * component breakdown. (ImageGallery — mockup ekp-page-chat.jsx:621-664 — was
 * wrongly dropped here in W22 F4 and restored by BUG-007. InlineImageCard —
 * mockup ekp-page-chat.jsx:470-498 usage + 581-617 definition — was wrongly
 * dropped here in W22 F4 and restored by BUG-019: mockup intent = inline image
 * card per imageCitation in answer body, ImageGallery is the collective
 * fallback, not a replacement. CitationPill hover popover — mockup
 * ekp-page-chat.jsx:515-578 — was wrongly dropped here in W22 F4 and the
 * surviving numeric-badge `InlineCitationPills` was gated
 * `citationMode === 'inline'` while mode is fixed at 'sidebar' so it never
 * rendered; restored by BUG-020 as unconditional CitationPillsRow at end of
 * each assistant message, then BUG-021 added inline marker→pill replacement
 * inside the answer body so verbose `[chunk-{id}]` markers from the LLM are
 * rendered as inline numeric pills instead of raw text. SingleScreenshotStrip
 * — added by BUG-020 as a custom 1-image-citation mini-section, removed by
 * BUG-021 in favour of lowering the ImageGallery gate to `>=1` so all
 * image-bearing answers share the canonical "Referenced screenshots" layout
 * (label / count badge / View-all-in-Image-Library link / numeric badge
 * top-left on each thumbnail). AnswerBodyMarkdown — BUG-021 + ADR-0036
 * (react-markdown H2 dep) — backend synthesiser emits markdown (numbered
 * list / bold / inline code), now rendered formatted instead of plain
 * `whiteSpace: 'pre-wrap'`. doc_format ext-sniff via `fileTypeFromDocId` is
 * replaced everywhere by `citation.doc_format` from the schema (BUG-021)
 * since user-supplied doc_id often lacks a file extension and fell back to
 * the muted "Unknown" FileTypeChip in citation popovers.)
 *
 * Real Citation schema lacks mockup's `idx` / `preview` / `file_type` /
 * `page` fields → graceful defaults: idx = array index + 1, preview = empty,
 * file_type derived from doc_id suffix, page omitted from display.
 */

import {
  ArrowDown,
  ArrowUp,
  BookOpen,
  ChevronRight,
  Copy,
  Eye,
  FileText,
  Inbox,
  Layers,
  Link as LinkIcon,
  Plus,
  RefreshCw,
  Search,
  Send,
  Shield,
  Square,
  Star,
  X as XIcon,
} from 'lucide-react';
import Link from 'next/link';
import {
  Children,
  useEffect,
  useMemo,
  useRef,
  useState,
  type FormEvent,
  type ReactNode,
} from 'react';
import ReactMarkdown from 'react-markdown';
import { useQuery, useQueryClient } from '@tanstack/react-query';

import { conversationsApi, type Conversation } from '@/lib/api/conversations';
import { kbApi, type KbStatus } from '@/lib/api/kb';
import { streamQuery, type Citation, type ImageRef, type SseEvent } from '@/lib/api/query';
import {
  dedupeCitationImages,
  formatRelevance,
  imageSectionPath,
  imageTitle,
  type DedupedCitationImage,
} from '@/lib/chat/citation-images';

// ──────────────────────────────────────────────────────────────────────────
// Local types + state
// ──────────────────────────────────────────────────────────────────────────

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  citations: Citation[];
  isStreaming: boolean;
  refused: boolean;
  /** Synthesis deployment name (e.g. "gpt-5.5") — populated on `done`. */
  model: string;
  rerankerUsed: string;
  errorText: string | null;
  cragTriggered: boolean;
  cragIterations: number;
  /** Wall-clock for display ("2:32 PM"). */
  at: number;
  /** Latency — populated on `done`. */
  latencyMs: number | null;
  /** USD synthesis cost — populated on `done`; null when no pricing row. */
  costUsd: number | null;
}

type CitationMode = 'inline' | 'footnote' | 'sidebar';

const HISTORY_COLLAPSED_KEY = 'ekp-chat-history-collapsed';
const SOURCES_COLLAPSED_KEY = 'ekp-chat-sources-collapsed';

function formatTime(ms: number): string {
  return new Date(ms).toLocaleTimeString([], {
    hour: 'numeric',
    minute: '2-digit',
  });
}

// `fileTypeFromDocId` removed by BUG-021 — the doc_id ext-sniff was orphaned
// once every consumer switched to `citation.doc_format` (server-side
// authoritative Literal). FILE_TYPE_COLORS kept for FileTypeChip styling; the
// `unknown` entry is dead today (Literal excludes it) but retained as a
// defensive fallback should the schema ever broaden.
const FILE_TYPE_COLORS: Record<string, { fg: string; bg: string; border: string }> = {
  docx: {
    fg: 'oklch(0.55 0.13 240)',
    bg: 'oklch(0.55 0.13 240 / 0.12)',
    border: 'oklch(0.55 0.13 240 / 0.25)',
  },
  pdf: {
    fg: 'oklch(0.58 0.18 25)',
    bg: 'oklch(0.58 0.18 25 / 0.12)',
    border: 'oklch(0.58 0.18 25 / 0.25)',
  },
  pptx: {
    fg: 'oklch(0.55 0.16 25)',
    bg: 'oklch(0.55 0.16 25 / 0.12)',
    border: 'oklch(0.55 0.16 25 / 0.25)',
  },
  unknown: {
    fg: 'oklch(var(--muted-foreground))',
    bg: 'oklch(var(--muted))',
    border: 'oklch(var(--border))',
  },
};

// ──────────────────────────────────────────────────────────────────────────
// Page orchestrator
// ──────────────────────────────────────────────────────────────────────────

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [activeConvId, setActiveConvId] = useState<string | null>(null);
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [modalImage, setModalImage] = useState<{
    citation: Citation;
    image: ImageRef;
  } | null>(null);
  // Fixed `sidebar` per mockup ekp-page-chat.jsx:79 — surfaces the BookOpen
  // header toggle + right CitationPanel. Not persisted / not user-switchable;
  // the inline/footnote modes are dormant W20 machinery (BUG-007 amendment).
  const [citationMode] = useState<CitationMode>('sidebar');
  const [historyCollapsed, setHistoryCollapsed] = useState(false);
  const [sourcesCollapsed, setSourcesCollapsed] = useState(false);
  const [kbId, setKbId] = useState<string>('');
  const abortRef = useRef<AbortController | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);
  const queryClient = useQueryClient();

  const kbsQuery = useQuery({
    queryKey: ['kb', 'list'],
    queryFn: () => kbApi.list(),
  });
  const kbs = useMemo<KbStatus[]>(() => kbsQuery.data ?? [], [kbsQuery.data]);
  const activeKb = kbs.find((k) => k.kb_id === kbId) ?? kbs[0];

  // Sync the selected KB to a real one once the list loads. `kbId` starts
  // empty and a stale value (e.g. a since-deleted KB, or an old single-KB-POC
  // default) must never reach the backend — it would resolve to a wrong or
  // non-existent Azure index. BUG-006.
  useEffect(() => {
    if (kbs.length > 0 && !kbs.some((k) => k.kb_id === kbId)) {
      setKbId(kbs[0].kb_id);
    }
  }, [kbs, kbId]);

  // Hydrate persisted preferences (SSR-stable). citationMode is intentionally
  // NOT hydrated — it stays at the mockup default `sidebar`. A stale W20-era
  // `ekp-citation-mode` localStorage value used to override it here and hide
  // the sources-panel toggle (BUG-007 amendment).
  useEffect(() => {
    if (window.localStorage.getItem(HISTORY_COLLAPSED_KEY) === '1') {
      setHistoryCollapsed(true);
    }
    if (window.localStorage.getItem(SOURCES_COLLAPSED_KEY) === '1') {
      setSourcesCollapsed(true);
    }
  }, []);

  // Esc closes screenshot modal.
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') setModalImage(null);
    }
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  // ?q= deep-link from <GlobalSearch> (W18 F6).
  useEffect(() => {
    const q = new URLSearchParams(window.location.search).get('q');
    if (q && q.trim()) {
      setInput(q);
      textareaRef.current?.focus();
    }
  }, []);

  function patchAssistant(id: string, mut: (m: Message) => Message) {
    setMessages((prev) => prev.map((m) => (m.id === id && m.role === 'assistant' ? mut(m) : m)));
  }

  function persist(key: string, value: string) {
    window.localStorage.setItem(key, value);
  }

  function toggleHistory() {
    setHistoryCollapsed((prev) => {
      const next = !prev;
      persist(HISTORY_COLLAPSED_KEY, next ? '1' : '0');
      return next;
    });
  }

  function toggleSources() {
    setSourcesCollapsed((prev) => {
      const next = !prev;
      persist(SOURCES_COLLAPSED_KEY, next ? '1' : '0');
      return next;
    });
  }

  async function ensureConversation(): Promise<string | null> {
    if (activeConvId) return activeConvId;
    try {
      const conv = await conversationsApi.create({ kb_id: kbId });
      setActiveConvId(conv.id);
      return conv.id;
    } catch {
      return null;
    }
  }

  async function loadConversation(conversationId: string) {
    setActiveConvId(conversationId);
    try {
      const detail = await conversationsApi.get(conversationId);
      // BUG-033 Finding A — restore the conversation's bound KB so the selector
      // reflects the loaded thread (was stuck on kbs[0] because loadConversation
      // never synced kbId). kb_id lives on detail.conversation; null → leave the
      // current selection.
      if (detail.conversation.kb_id) setKbId(detail.conversation.kb_id);
      const hydrated: Message[] = detail.messages.map((m) => ({
        id: m.id,
        role: m.role,
        content: m.content,
        citations: m.citations ?? [],
        isStreaming: false,
        refused: false,
        model: '',
        rerankerUsed: '',
        errorText: null,
        cragTriggered: false,
        cragIterations: 0,
        at: new Date(m.created_at).getTime(),
        latencyMs: null,
        costUsd: null,
      }));
      setMessages(hydrated);
    } catch {
      setMessages([]);
    }
  }

  function handleConversationCreate(conv: Conversation) {
    setActiveConvId(conv.id);
    setMessages([]);
  }

  function handleActiveDeleted() {
    setActiveConvId(null);
    setMessages([]);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || isStreaming) return;

    // BUG-034 Finding A — a freshly-created conversation captures the current
    // kbId correctly; a REUSED one (created earlier, possibly before the user
    // switched the KB selector) keeps its stale kb_id. Track whether we are
    // reusing so we can re-bind it to the KB we actually query below.
    const reusedConversation = activeConvId != null;
    const conversationId = await ensureConversation();
    const now = Date.now();

    const userMsg: Message = {
      id: `u-${now}`,
      role: 'user',
      content: trimmed,
      citations: [],
      isStreaming: false,
      refused: false,
      model: '',
      rerankerUsed: '',
      errorText: null,
      cragTriggered: false,
      cragIterations: 0,
      at: now,
      latencyMs: null,
      costUsd: null,
    };
    const assistantId = `a-${now}`;
    const assistantMsg: Message = {
      id: assistantId,
      role: 'assistant',
      content: '',
      citations: [],
      isStreaming: true,
      refused: false,
      model: '',
      rerankerUsed: '',
      errorText: null,
      cragTriggered: false,
      cragIterations: 0,
      at: now,
      latencyMs: null,
      costUsd: null,
    };
    setMessages((prev) => [...prev, userMsg, assistantMsg]);
    setInput('');
    setIsStreaming(true);

    if (conversationId) {
      // BUG-034 Finding A — keep the persisted kb_id aligned with the KB this
      // turn actually queries (kbId). Only needed when reusing an existing
      // conversation whose kb_id may be stale; invalidate the list so the
      // sidebar label reflects the corrected binding.
      if (reusedConversation && kbId) {
        conversationsApi
          .update(conversationId, { kb_id: kbId })
          .then(() => queryClient.invalidateQueries({ queryKey: ['conversations'] }))
          .catch(() => {});
      }
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
        { query: trimmed, kb_id: kbId },
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
          // BUG-028 ② — replace the streamed raw text with the post-hoc-expanded
          // answer. citation_expansion adds the extra `[chunk-N]` markers AFTER
          // the text-delta frames already streamed the LLM's original cites, so
          // the streamed content under-cites vs the Sources panel; swapping to
          // the expanded answer on done restores answer↔source parity (matches
          // non-stream /query). Falls back to streamed content when the backend
          // omits `answer` (pre-BUG-028).
          if (evt.answer) finalContent = evt.answer;
          patchAssistant(assistantId, (m) => ({
            ...m,
            content: evt.answer || m.content,
            isStreaming: false,
            refused: evt.refused,
            model: evt.model,
            rerankerUsed: evt.reranker_used,
            latencyMs: evt.latency_ms,
            // Normalize at the SSE boundary — a pre-BUG-007 backend omits
            // `cost` entirely, so guard the meta-row `costUsd !== null` check.
            costUsd: evt.cost ?? null,
          }));
        }
      }

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

  // Latest assistant turn citations — for sidebar mode + sources strip.
  const latestAssistantCitations: Citation[] =
    [...messages].reverse().find((m) => m.role === 'assistant')?.citations ?? [];

  // 3-pane grid columns
  const cols = [
    !historyCollapsed ? '260px' : null,
    '1fr',
    citationMode === 'sidebar' && !sourcesCollapsed && latestAssistantCitations.length > 0
      ? '400px'
      : null,
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: cols,
        height: 'calc(100vh - var(--topbar-h))',
        overflow: 'hidden',
      }}
    >
      {!historyCollapsed && (
        <ConversationHistoryPanel
          activeConvId={activeConvId}
          kbId={kbId}
          onSelect={(id) => void loadConversation(id)}
          onCreate={handleConversationCreate}
          onActiveDeleted={handleActiveDeleted}
          onClose={() => toggleHistory()}
        />
      )}

      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
          borderRight:
            citationMode === 'sidebar' && !sourcesCollapsed && latestAssistantCitations.length > 0
              ? '1px solid oklch(var(--border))'
              : 'none',
        }}
      >
        <ChatHeader
          kbs={kbs}
          activeKb={activeKb}
          onKbChange={setKbId}
          citationMode={citationMode}
          historyCollapsed={historyCollapsed}
          onToggleHistory={toggleHistory}
          sourcesCollapsed={sourcesCollapsed}
          onToggleSources={toggleSources}
        />

        <ChatThread
          messages={messages}
          citationMode={citationMode}
          kbId={kbId || activeKb?.kb_id || ''}
          onOpenScreenshot={(citation, image) => setModalImage({ citation, image })}
        />

        <ChatComposer
          input={input}
          onInputChange={setInput}
          isStreaming={isStreaming}
          onSubmit={handleSubmit}
          onStop={handleStop}
          textareaRef={textareaRef}
        />
      </div>

      {citationMode === 'sidebar' && !sourcesCollapsed && latestAssistantCitations.length > 0 && (
        <CitationPanel
          citations={latestAssistantCitations}
          onClose={() => toggleSources()}
          onOpenScreenshot={(c, img) => setModalImage({ citation: c, image: img })}
        />
      )}

      {modalImage && (
        <ScreenshotModal
          citation={modalImage.citation}
          image={modalImage.image}
          idx={
            // Resolve numeric idx from the latest assistant's citations so
            // the modal header matches CitationPill / PanelSourceCard.
            // Fallback to chunk_index + 1 if citation not in latest list.
            (() => {
              const found = latestAssistantCitations.findIndex(
                (c) => c.chunk_id === modalImage.citation.chunk_id,
              );
              return found >= 0 ? found + 1 : modalImage.citation.chunk_index + 1;
            })()
          }
          kbId={kbId || activeKb?.kb_id || ''}
          onClose={() => setModalImage(null)}
        />
      )}
    </div>
  );
}

// ──────────────────────────────────────────────────────────────────────────
// ConversationHistoryPanel — mockup ekp-page-chat.jsx:134-219
// ──────────────────────────────────────────────────────────────────────────

function ConversationHistoryPanel({
  activeConvId,
  kbId,
  onSelect,
  onCreate,
  onActiveDeleted,
  onClose,
}: {
  activeConvId: string | null;
  kbId: string;
  onSelect: (id: string) => void;
  onCreate: (conv: Conversation) => void;
  onActiveDeleted: () => void;
  onClose: () => void;
}) {
  const [search, setSearch] = useState('');
  const listQuery = useQuery({
    queryKey: ['conversations'],
    queryFn: () => conversationsApi.list(50, 0),
  });
  const conversations = useMemo(() => listQuery.data?.items ?? [], [listQuery.data]);

  async function handleNewChat() {
    try {
      const conv = await conversationsApi.create({ kb_id: kbId });
      onCreate(conv);
      listQuery.refetch();
    } catch {
      /* swallow */
    }
  }

  const filtered = useMemo(() => {
    const term = search.trim().toLowerCase();
    if (!term) return conversations;
    return conversations.filter((c) => c.title.toLowerCase().includes(term));
  }, [conversations, search]);

  // Group by relative day buckets (mockup pattern Today / Yesterday / This week / Older)
  const groups = useMemo(() => {
    const now = Date.now();
    const todayCut = now - 24 * 60 * 60 * 1000;
    const yesterdayCut = now - 2 * 24 * 60 * 60 * 1000;
    const weekCut = now - 7 * 24 * 60 * 60 * 1000;

    const today: Conversation[] = [];
    const yesterday: Conversation[] = [];
    const thisWeek: Conversation[] = [];
    const older: Conversation[] = [];

    for (const c of filtered) {
      const ts = new Date(c.updated_at).getTime();
      if (ts >= todayCut) today.push(c);
      else if (ts >= yesterdayCut) yesterday.push(c);
      else if (ts >= weekCut) thisWeek.push(c);
      else older.push(c);
    }
    return [
      { id: 'today', label: 'Today', items: today },
      { id: 'yesterday', label: 'Yesterday', items: yesterday },
      { id: 'this-week', label: 'This week', items: thisWeek },
      { id: 'older', label: 'Older', items: older },
    ];
  }, [filtered]);

  return (
    <aside
      style={{
        display: 'flex',
        flexDirection: 'column',
        background: 'oklch(var(--card))',
        borderRight: '1px solid oklch(var(--border))',
        overflow: 'hidden',
      }}
    >
      {/* Header — mockup lines 152-166 */}
      <div
        style={{
          padding: '10px 12px',
          borderBottom: '1px solid oklch(var(--border))',
          flexShrink: 0,
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            marginBottom: 8,
          }}
        >
          <span style={{ fontSize: 13, fontWeight: 600 }}>Conversations</span>
          <span className="badge badge-accent" style={{ fontSize: 10, fontWeight: 600 }}>
            BETA+
          </span>
          <div className="spacer" />
          <button
            type="button"
            className="btn btn-ghost btn-icon btn-xs"
            title="Close history"
            onClick={onClose}
          >
            <XIcon size={12} />
          </button>
        </div>
        <button
          type="button"
          className="btn btn-secondary btn-sm"
          style={{ width: '100%', justifyContent: 'flex-start', gap: 8 }}
          onClick={handleNewChat}
        >
          <Plus size={13} /> New chat
        </button>
        <div className="input-search-wrap" style={{ marginTop: 8 }}>
          <span className="icon-leading">
            <Search size={13} />
          </span>
          <input
            className="input"
            placeholder="Search conversations…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ height: 28, fontSize: 12.5 }}
          />
        </div>
      </div>

      {/* Privacy notice — mockup lines 169-184 */}
      <div
        style={{
          padding: '8px 12px',
          background: 'oklch(var(--muted) / 0.5)',
          borderBottom: '1px solid oklch(var(--border))',
          fontSize: 11,
          color: 'oklch(var(--muted-foreground))',
          display: 'flex',
          alignItems: 'center',
          gap: 6,
          flexShrink: 0,
        }}
      >
        <Shield size={11} />
        <span>Server-side per ADR-0031 · scoped to user · Postgres backing</span>
      </div>

      {/* List */}
      <div style={{ flex: 1, overflowY: 'auto', padding: 6 }}>
        {listQuery.isPending ? (
          <div className="muted text-xs" style={{ padding: '24px 8px', textAlign: 'center' }}>
            Loading…
          </div>
        ) : conversations.length === 0 ? (
          <div className="muted text-xs" style={{ padding: '24px 8px', textAlign: 'center' }}>
            No conversations yet.
          </div>
        ) : (
          groups.map((g) => {
            if (g.items.length === 0) return null;
            return (
              <div key={g.id}>
                <div className="nav-section-label" style={{ padding: '10px 8px 4px' }}>
                  {g.label}
                </div>
                {g.items.map((c) => (
                  <ConversationItem
                    key={c.id}
                    conv={c}
                    active={c.id === activeConvId}
                    onClick={() => onSelect(c.id)}
                    onDelete={async () => {
                      try {
                        await conversationsApi.remove(c.id);
                        if (c.id === activeConvId) onActiveDeleted();
                        listQuery.refetch();
                      } catch {
                        /* swallow */
                      }
                    }}
                  />
                ))}
              </div>
            );
          })
        )}
      </div>

      {/* Footer — mockup lines 203-217 */}
      <div
        style={{
          padding: '8px 12px',
          borderTop: '1px solid oklch(var(--border))',
          flexShrink: 0,
          fontSize: 11,
          color: 'oklch(var(--muted-foreground))',
          display: 'flex',
          alignItems: 'center',
          gap: 6,
        }}
      >
        <Inbox size={11} />
        <span>
          {conversations.length} conversation{conversations.length === 1 ? '' : 's'}
        </span>
      </div>
    </aside>
  );
}

function ConversationItem({
  conv,
  active,
  onClick,
  onDelete,
}: {
  conv: Conversation;
  active: boolean;
  onClick: () => void;
  onDelete: () => void;
}) {
  const [hover, setHover] = useState(false);
  return (
    <div
      onClick={onClick}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{
        padding: '8px 10px',
        borderRadius: 'var(--radius-sm)',
        cursor: 'default',
        background: active
          ? 'oklch(var(--muted))'
          : hover
            ? 'oklch(var(--muted) / 0.5)'
            : 'transparent',
        borderLeft: active ? '2px solid oklch(var(--accent))' : '2px solid transparent',
        transition: 'background var(--duration-fast)',
        marginBottom: 1,
        position: 'relative',
      }}
    >
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 6,
          marginBottom: 2,
        }}
      >
        <span
          style={{
            fontSize: 12.5,
            fontWeight: active ? 600 : 500,
            flex: 1,
            minWidth: 0,
            whiteSpace: 'nowrap',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            lineHeight: 1.35,
          }}
        >
          {conv.title || 'Untitled'}
        </span>
        {hover && (
          <button
            type="button"
            className="btn btn-ghost btn-icon btn-xs"
            title="Delete conversation"
            onClick={(e) => {
              e.stopPropagation();
              onDelete();
            }}
          >
            <XIcon size={11} />
          </button>
        )}
      </div>
      <div
        style={{
          display: 'flex',
          gap: 6,
          alignItems: 'center',
          fontSize: 10.5,
          color: 'oklch(var(--muted-foreground))',
        }}
      >
        {conv.kb_id && (
          <span
            className="mono"
            style={{
              background: 'oklch(var(--muted))',
              padding: '0 4px',
              borderRadius: 2,
              fontSize: 9.5,
            }}
          >
            {conv.kb_id}
          </span>
        )}
        <span
          style={{
            marginLeft: 'auto',
            fontFamily: 'var(--font-mono)',
          }}
        >
          {conv.message_count}m
        </span>
      </div>
    </div>
  );
}

// ──────────────────────────────────────────────────────────────────────────
// ChatHeader — mockup ekp-page-chat.jsx:257-298
// ──────────────────────────────────────────────────────────────────────────

function ChatHeader({
  kbs,
  activeKb,
  onKbChange,
  citationMode,
  historyCollapsed,
  onToggleHistory,
  sourcesCollapsed,
  onToggleSources,
}: {
  kbs: KbStatus[];
  activeKb: KbStatus | undefined;
  onKbChange: (id: string) => void;
  citationMode: CitationMode;
  historyCollapsed: boolean;
  onToggleHistory: () => void;
  sourcesCollapsed: boolean;
  onToggleSources: () => void;
}) {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 12,
        padding: '10px 20px',
        borderBottom: '1px solid oklch(var(--border))',
        flexShrink: 0,
        background: 'oklch(var(--background))',
      }}
    >
      {historyCollapsed && (
        <button
          type="button"
          className="btn btn-ghost btn-icon btn-sm"
          title="Show conversation history"
          onClick={onToggleHistory}
        >
          <Inbox size={14} />
        </button>
      )}
      <div className="row">
        <span className="muted mono text-xs">KB</span>
        <select
          className="select"
          value={activeKb?.kb_id ?? ''}
          onChange={(e) => onKbChange(e.target.value)}
          style={{ height: 28 }}
        >
          {kbs.length === 0 ? (
            <option value="">No knowledge bases yet</option>
          ) : (
            kbs.map((k) => (
              <option key={k.kb_id} value={k.kb_id}>
                {k.name || k.kb_id}
              </option>
            ))
          )}
        </select>
        {activeKb && (
          <>
            <span className="muted text-xs">·</span>
            <span className="muted mono text-xs">
              {activeKb.total_chunks.toLocaleString()} chunks · {activeKb.total_screenshots}{' '}
              screenshots
            </span>
          </>
        )}
      </div>
      <div className="spacer" />
      <div className="row">
        <span className="muted text-xs">CRAG</span>
        <span className="switch" data-on="true" />
        <span className="muted text-xs" style={{ marginLeft: 12 }}>
          Show images
        </span>
        <span className="switch" data-on="true" />
      </div>
      <div className="row" style={{ marginLeft: 4 }}>
        <button
          type="button"
          className="btn btn-ghost btn-icon btn-sm"
          title="Focus mode (hide all panels)"
        >
          <Eye size={14} />
        </button>
        {citationMode === 'sidebar' && (
          <button
            type="button"
            className="btn btn-ghost btn-icon btn-sm"
            title={sourcesCollapsed ? 'Show sources panel' : 'Hide sources panel'}
            onClick={onToggleSources}
            style={{
              background: !sourcesCollapsed ? 'oklch(var(--muted))' : 'transparent',
            }}
          >
            <BookOpen size={14} />
          </button>
        )}
      </div>
    </div>
  );
}

// ──────────────────────────────────────────────────────────────────────────
// ChatThread + MessageRow — mockup ekp-page-chat.jsx:301-373
// ──────────────────────────────────────────────────────────────────────────

function ChatThread({
  messages,
  citationMode,
  kbId,
  onOpenScreenshot,
}: {
  messages: Message[];
  citationMode: CitationMode;
  kbId: string;
  onOpenScreenshot: (citation: Citation, image: ImageRef) => void;
}) {
  const threadRef = useRef<HTMLDivElement | null>(null);

  // Auto-scroll on new messages.
  useEffect(() => {
    threadRef.current?.scrollTo({
      top: threadRef.current.scrollHeight,
      behavior: 'smooth',
    });
  }, [messages]);

  return (
    <div ref={threadRef} style={{ flex: 1, overflowY: 'auto', padding: '20px 32px 32px' }}>
      <div style={{ maxWidth: 860, margin: '0 auto' }}>
        {messages.length === 0 ? (
          <EmptyState />
        ) : (
          messages.map((m) => (
            <MessageRow
              key={m.id}
              message={m}
              citationMode={citationMode}
              kbId={kbId}
              onOpenScreenshot={onOpenScreenshot}
            />
          ))
        )}
      </div>
    </div>
  );
}

function EmptyState() {
  return (
    <div
      style={{
        textAlign: 'center',
        padding: '64px 24px',
        color: 'oklch(var(--muted-foreground))',
      }}
    >
      <div
        style={{
          width: 56,
          height: 56,
          borderRadius: '50%',
          background: 'oklch(var(--accent) / 0.1)',
          color: 'oklch(var(--accent))',
          display: 'grid',
          placeItems: 'center',
          margin: '0 auto 16px',
        }}
      >
        <Send size={22} />
      </div>
      <div
        style={{
          fontSize: 16,
          fontWeight: 600,
          color: 'oklch(var(--foreground))',
          marginBottom: 6,
        }}
      >
        Ask about Ricoh financial software
      </div>
      <div style={{ fontSize: 13, lineHeight: 1.55, maxWidth: 380, margin: '0 auto' }}>
        AR / AP / FA / CB / GL / BM · D365 F&O ERP corpus · Cohere v4.0-pro rerank · Image-grounded
        citations.
      </div>
    </div>
  );
}

// BUG-031 (A) — max images rendered inline (answer-body cards + gallery grid) per
// assistant message. Overflow is reachable via "View all in Image Library →".
// H7-deviation cap (mockup renders all) — user-approved 2026-06-01.
const INLINE_IMAGE_CAP = 8;

function MessageRow({
  message,
  citationMode,
  kbId,
  onOpenScreenshot,
}: {
  message: Message;
  citationMode: CitationMode;
  kbId: string;
  onOpenScreenshot: (citation: Citation, image: ImageRef) => void;
}) {
  if (message.role === 'user') {
    return (
      <div style={{ display: 'flex', gap: 12, marginBottom: 24 }}>
        <div className="avatar avatar-sm">You</div>
        <div style={{ flex: 1 }}>
          <div className="muted mono text-xs" style={{ marginBottom: 4 }}>
            you · {formatTime(message.at)}
          </div>
          <div
            style={{
              fontSize: 14.5,
              lineHeight: 1.55,
              whiteSpace: 'pre-wrap',
            }}
          >
            {message.content}
          </div>
        </div>
      </div>
    );
  }

  // Assistant
  // BUG-026 Finding A — unique images across citations (deduped by checksum /
  // blob_url). Drives inline cards + gallery + the meta-row screenshot count so
  // the same image
  // (a §X.1 figure that's both the §X.1 chunk's direct image AND the §X intro
  // chunk's neighbour-attached image) renders once, not once per citation.
  const dedupedImages = dedupeCitationImages(message.citations);
  // BUG-031 (A) — H7-deviation display cap (user-approved 2026-06-01). Image-dense
  // mega-chunks (one §x.y.z chunk can own 20-57 figures) × aggressive
  // citation_expansion surface 20+ images for a NARROW query. The mockup
  // (ekp-page-chat.jsx:621) renders all — its demo had ≤5 imgs and never flooded.
  // Cap the inline answer-body cards + the gallery grid to the first N; the gallery
  // badge keeps the TRUE total and the existing "View all in Image Library →"
  // overflow button (wired to the KB images tab) carries images N+1.. .
  const cappedImages = dedupedImages.slice(0, INLINE_IMAGE_CAP);

  return (
    <div style={{ display: 'flex', gap: 12, marginBottom: 24 }}>
      <div
        className="avatar avatar-sm"
        style={{
          background: 'oklch(var(--accent))',
          color: 'oklch(var(--accent-foreground))',
          border: 0,
        }}
      >
        E
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        {/* Meta row */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            marginBottom: 8,
            flexWrap: 'wrap',
          }}
        >
          <span style={{ fontSize: 13, fontWeight: 600 }}>EKP</span>
          <span className="muted mono text-xs">
            {message.model && `${message.model} · `}
            {message.rerankerUsed || 'cohere-v4.0-pro'} · {message.citations.length} citation
            {message.citations.length === 1 ? '' : 's'}
            {dedupedImages.length > 0 &&
              ` · ${dedupedImages.length} with screenshot${dedupedImages.length === 1 ? '' : 's'}`}
          </span>
          <span className="spacer" style={{ flex: 1 }} />
          {message.latencyMs !== null && (
            <span className="muted mono text-xs">
              {(message.latencyMs / 1000).toFixed(2)}s
              {message.costUsd !== null && ` · $${message.costUsd.toFixed(3)}`}
            </span>
          )}
        </div>

        {/* CRAG strip (when triggered) — mockup lines 332-348 */}
        {message.cragTriggered && (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              padding: '7px 11px',
              background: 'oklch(var(--accent) / 0.06)',
              border: '1px solid oklch(var(--accent) / 0.22)',
              borderRadius: 'var(--radius-sm)',
              marginBottom: 14,
              fontSize: 12.5,
            }}
          >
            <RefreshCw size={12} style={{ color: 'oklch(var(--accent))', flexShrink: 0 }} />
            <span>
              <b>CRAG L2 re-retrieve</b> · {message.cragIterations} iteration
              {message.cragIterations === 1 ? '' : 's'}
            </span>
          </div>
        )}

        {/* Answer body */}
        {message.errorText ? (
          <div
            style={{
              padding: '12px 14px',
              border: '1px solid oklch(var(--destructive) / 0.3)',
              background: 'oklch(var(--destructive) / 0.06)',
              color: 'oklch(var(--destructive))',
              borderRadius: 'var(--radius-sm)',
              fontSize: 13,
            }}
          >
            {message.errorText}
          </div>
        ) : (
          <div
            className="chat-answer-body"
            style={{
              fontSize: 14,
              lineHeight: 1.7,
              color: 'oklch(var(--foreground))',
            }}
          >
            {message.content ? (
              <AnswerBodyMarkdown content={message.content} citations={message.citations} />
            ) : (
              <span className="muted">{message.isStreaming ? 'Thinking…' : '(no content)'}</span>
            )}
          </div>
        )}

        {/* Citation pills — mockup ekp-page-chat.jsx:515-578 (per-pill hover popover
            with file icon + doc title + section + chunk title + relevance score).
            Restored by BUG-020 — W22 F4 dropped CitationPill as a "custom abstraction"
            and the surviving InlineCitationPills row was gated on
            `citationMode === 'inline'` while mode is fixed at 'sidebar' → pills
            never rendered. Now unconditional when citations exist; hover popover
            replaces the old HTML `title` tooltip per mockup interaction state. */}
        {!message.isStreaming && message.citations.length > 0 && (
          <CitationPillsRow citations={message.citations} />
        )}

        {/* Footnote citation list */}
        {citationMode === 'footnote' && message.citations.length > 0 && (
          <FootnoteList citations={message.citations} onOpenScreenshot={onOpenScreenshot} />
        )}

        {/* Inline image cards — mockup ekp-page-chat.jsx:470-498 (per imageCitation
            inline rendering in answer body). Restored by BUG-019 — W22 F4 rebuild
            wrongly dropped these as "custom abstraction" but mockup line 581-617
            defines the InlineImageCard function and uses it inline in AnswerBody.
            BUG-026 Finding A — render the deduped unique-image list (one card per
            distinct image, not one per (citation, image) pair) so a neighbour-
            attached image shared by 2+ citations renders once. ImageGallery
            below draws from the same deduped list as the collective fallback. */}
        {!message.isStreaming &&
          cappedImages.map(({ citation, image, citationIdx }, flatIdx) => (
            <InlineImageCard
              key={`${citation.chunk_id}-${image.checksum_sha256 || image.blob_url}`}
              citation={citation}
              image={image}
              citationIdx={citationIdx}
              figureIdx={flatIdx + 1}
              onOpen={() => onOpenScreenshot(citation, image)}
            />
          ))}

        {/* Image gallery — mockup ekp-page-chat.jsx:621-664 ("Referenced
            screenshots" collective list). BUG-021 amendment: gate lowered from
            `>=2` to `>=1` per user-pick — earlier BUG-020 SingleScreenshotStrip
            hybrid attempt did not match the mockup gallery layout (label /
            count badge / view-all link / numeric badge top-left were missing),
            so the same ImageGallery now handles the 1-image case too. Mockup
            line 354-357 `>=2` gate intent (1-image = inline only) is the
            documented deviation per user UX expectation. */}
        {!message.isStreaming && dedupedImages.length >= 1 && (
          <ImageGallery
            images={cappedImages}
            totalCount={dedupedImages.length}
            kbId={kbId}
            onOpenScreenshot={onOpenScreenshot}
          />
        )}

        {/* Sources strip (default — non-sidebar modes show it inline) */}
        {citationMode !== 'sidebar' && !message.isStreaming && message.citations.length > 0 && (
          <SourcesStrip citations={message.citations} onOpenScreenshot={onOpenScreenshot} />
        )}

        {/* Feedback bar */}
        {!message.isStreaming && message.content && (
          <FeedbackBar
            traceId={message.id}
            citations={message.citations}
            imageCount={dedupedImages.length}
          />
        )}
      </div>
    </div>
  );
}

// ──────────────────────────────────────────────────────────────────────────
// AnswerBodyMarkdown — BUG-021 + BUG-021 amendment.
//
// Two layered transforms applied to LLM synthesiser output:
//   1. Pre-process step replaces verbose `[chunk-{chunk_id}]` markers with a
//      placeholder token `⟦CITn⟧` (1-indexed citation idx, U+27E6/U+27E7
//      brackets unlikely to appear in real LLM output).
//   2. The pre-processed content is fed to a SINGLE <ReactMarkdown> render so
//      the markdown block structure (paragraphs / lists / bold / code) stays
//      intact. Custom `components` override walks the rendered children for
//      each inline-host element (p / li / strong / em / code) and splits any
//      string child containing `⟦CITn⟧` placeholders into a mix of literal
//      text and inline <CitationPill> components — keeping pills inline with
//      the surrounding text without breaking the block flow.
//
// The original BUG-021 approach split the content into tokens and called
// ReactMarkdown per token, which wrapped every text fragment in its own
// <p> block (forcing pills onto their own line + losing the cross-fragment
// markdown context like numbered lists). This amendment fixes that.
// ──────────────────────────────────────────────────────────────────────────

const CITATION_PLACEHOLDER_PATTERN = /⟦CIT(\d+)⟧/g;

function preprocessAnswerContent(content: string, citations: Citation[]): string {
  return content.replace(/\[chunk-([^\]]+)\]/g, (raw, id) => {
    const idx = citations.findIndex((c) => c.chunk_id === id);
    // Hallucinated chunk_id → keep raw marker (defensive — backend already
    // warns via `citation_hallucinated_ids` log).
    return idx >= 0 ? `⟦CIT${idx + 1}⟧` : raw;
  });
}

function splitStringForPills(text: string, citations: Citation[], keyPrefix: string): ReactNode[] {
  const parts: ReactNode[] = [];
  let lastIdx = 0;
  let match: RegExpExecArray | null;
  // BUG-031 (B) — accumulate CONSECUTIVE pills (no text between them) into one
  // group, flushed as a single inline-flex wrapper with `gap:2` + `marginLeft:3`
  // (mockup ekp-page-chat.jsx:519 `CitationPill ids={[…]}`). Without this, the
  // bare per-pill spans render back-to-back with no separator, so
  // citation_expansion's run of markers reads as "1234567891011".
  let group: ReactNode[] = [];
  let groupStart = -1;
  const flushGroup = () => {
    if (group.length === 0) return;
    parts.push(
      <span
        key={`${keyPrefix}-grp-${groupStart}`}
        style={{ display: 'inline-flex', gap: 2, marginLeft: 3, position: 'relative' }}
      >
        {group}
      </span>,
    );
    group = [];
    groupStart = -1;
  };

  CITATION_PLACEHOLDER_PATTERN.lastIndex = 0;
  while ((match = CITATION_PLACEHOLDER_PATTERN.exec(text)) !== null) {
    if (match.index > lastIdx) {
      // literal text precedes this marker → the previous pill run ends here.
      flushGroup();
      parts.push(text.slice(lastIdx, match.index));
    }
    const citIdx = parseInt(match[1]!, 10) - 1;
    const citation = citations[citIdx];
    if (citation) {
      if (groupStart === -1) groupStart = match.index;
      group.push(
        <CitationPill key={`${keyPrefix}-${match.index}`} citation={citation} idx={citIdx + 1} />,
      );
    } else {
      // hallucinated id → keep the raw token as literal text (defensive).
      flushGroup();
      parts.push(match[0]);
    }
    lastIdx = match.index + match[0].length;
  }
  flushGroup();
  if (lastIdx < text.length) {
    parts.push(text.slice(lastIdx));
  }
  return parts;
}

function injectPillsIntoChildren(
  children: ReactNode,
  citations: Citation[],
  keyPrefix: string,
): ReactNode {
  // React-markdown passes children as a string for simple inline text,
  // an array when bold/em/code split the inline content. Walk the array,
  // splitting string children that contain `⟦CITn⟧` placeholders.
  if (typeof children === 'string') {
    if (!children.includes('⟦CIT')) return children;
    return splitStringForPills(children, citations, keyPrefix);
  }
  if (Array.isArray(children)) {
    return Children.map(children, (child, i) => {
      if (typeof child === 'string' && child.includes('⟦CIT')) {
        return splitStringForPills(child, citations, `${keyPrefix}-${i}`);
      }
      return child;
    });
  }
  return children;
}

function AnswerBodyMarkdown({ content, citations }: { content: string; citations: Citation[] }) {
  const processed = useMemo(
    () => preprocessAnswerContent(content, citations),
    [content, citations],
  );

  const components = useMemo(
    () => ({
      p: ({ children }: { children?: ReactNode }) => (
        <p style={{ margin: '0 0 10px 0' }}>{injectPillsIntoChildren(children, citations, 'p')}</p>
      ),
      // BUG-033 Finding B — Tailwind `@tailwind base` preflight resets `list-style:
      // none`, so these renderers must re-assert the marker type or numbered/bulleted
      // lists render markerless (LLM markdown is correct; this is the render fix).
      ol: ({ children }: { children?: ReactNode }) => (
        <ol style={{ paddingLeft: 22, margin: '0 0 10px 0', lineHeight: 1.7, listStyleType: 'decimal' }}>
          {children}
        </ol>
      ),
      ul: ({ children }: { children?: ReactNode }) => (
        <ul style={{ paddingLeft: 22, margin: '0 0 10px 0', lineHeight: 1.7, listStyleType: 'disc' }}>
          {children}
        </ul>
      ),
      li: ({ children }: { children?: ReactNode }) => (
        <li style={{ marginBottom: 2 }}>{injectPillsIntoChildren(children, citations, 'li')}</li>
      ),
      strong: ({ children }: { children?: ReactNode }) => (
        <strong style={{ fontWeight: 600 }}>
          {injectPillsIntoChildren(children, citations, 'strong')}
        </strong>
      ),
      em: ({ children }: { children?: ReactNode }) => (
        <em style={{ fontStyle: 'italic' }}>
          {injectPillsIntoChildren(children, citations, 'em')}
        </em>
      ),
      code: ({ children }: { children?: ReactNode }) => (
        <code
          style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 12.5,
            background: 'oklch(var(--muted) / 0.6)',
            border: '1px solid oklch(var(--border))',
            padding: '1px 5px',
            borderRadius: 3,
          }}
        >
          {injectPillsIntoChildren(children, citations, 'code')}
        </code>
      ),
    }),
    [citations],
  );

  return <ReactMarkdown components={components}>{processed}</ReactMarkdown>;
}

// ──────────────────────────────────────────────────────────────────────────
// CitationPillsRow — mockup ekp-page-chat.jsx:515-578. Per-pill hover popover
// shows file icon + doc title + section path + chunk title + relevance score.
// Restored by BUG-020 — W22 F4 dropped the popover behavior; the surviving
// numeric-badge row was gated `citationMode === 'inline'` while mode is fixed
// at 'sidebar' so it never rendered. Now unconditional.
// ──────────────────────────────────────────────────────────────────────────

function CitationPillsRow({ citations }: { citations: Citation[] }) {
  return (
    <div
      style={{
        display: 'flex',
        flexWrap: 'wrap',
        gap: 4,
        marginTop: 10,
        alignItems: 'center',
      }}
    >
      {citations.map((c, i) => (
        <CitationPill key={c.chunk_id} citation={c} idx={i + 1} />
      ))}
    </div>
  );
}

function CitationPill({ citation, idx }: { citation: Citation; idx: number }) {
  const [hovered, setHovered] = useState(false);
  // BUG-021 — use server-side authoritative doc_format from Citation schema
  // (Literal docx/pdf/pptx). Earlier doc_id ext-sniff fell back to 'unknown'
  // when doc_id was the user-supplied identifier without `.docx`/`.pdf`/`.pptx`.
  const fileType = citation.doc_format;
  return (
    <span
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        minWidth: 18,
        height: 18,
        padding: '0 5px',
        fontSize: 11,
        fontWeight: 600,
        background: hovered ? 'oklch(var(--accent) / 0.22)' : 'oklch(var(--accent) / 0.1)',
        color: 'oklch(var(--accent))',
        border: '1px solid oklch(var(--accent) / 0.28)',
        borderRadius: 4,
        fontFamily: 'var(--font-mono)',
        cursor: 'default',
        transition: 'background var(--duration-fast)',
        position: 'relative',
      }}
    >
      {idx}
      {hovered && (
        <span
          style={{
            position: 'absolute',
            bottom: 'calc(100% + 6px)',
            left: '50%',
            transform: 'translateX(-50%)',
            width: 320,
            padding: '10px 12px',
            background: 'oklch(var(--popover))',
            border: '1px solid oklch(var(--border))',
            borderRadius: 'var(--radius-sm)',
            boxShadow: 'var(--shadow-lg)',
            fontFamily: 'var(--font-sans)',
            fontWeight: 400,
            color: 'oklch(var(--foreground))',
            textAlign: 'left',
            zIndex: 10,
            whiteSpace: 'normal',
          }}
        >
          {/* BUG-023 — popover inner wrappers were <div> elements, which became
              descendants of react-markdown's <p> ancestor (via AnswerBodyMarkdown's
              single-ReactMarkdown render + injectPillsIntoChildren). HTML5 spec
              disallows <div> inside <p>, surfacing as `<div> cannot be a
              descendant of <p>` hydration warning on every hover. Span with
              inline style display:flex/block is layout-equivalent + HTML-valid
              as a <p> descendant (Karpathy §1.3 surgical — 3 tag swaps, zero
              visual / behavioral change). */}
          <span
            style={{
              display: 'flex',
              gap: 6,
              alignItems: 'center',
              marginBottom: 6,
            }}
          >
            <FileTypeChip type={fileType} />
            <span
              style={{
                fontSize: 12,
                fontWeight: 500,
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                flex: 1,
                minWidth: 0,
              }}
            >
              {citation.doc_title}
            </span>
            <span className="mono muted text-xs">{formatRelevance(citation.relevance_score)}</span>
          </span>
          {citation.section_path.length > 0 && (
            <span className="section-path text-xs" style={{ display: 'block', marginBottom: 6 }}>
              {citation.section_path.map((s, j) => (
                <span key={j}>{s}</span>
              ))}
            </span>
          )}
          {citation.chunk_title && (
            <span
              style={{
                display: 'block',
                fontSize: 12,
                lineHeight: 1.5,
                color: 'oklch(var(--foreground) / 0.85)',
              }}
            >
              {citation.chunk_title}
            </span>
          )}
        </span>
      )}
    </span>
  );
}

// SingleScreenshotStrip dropped by BUG-021 — ImageGallery now handles the
// 1-image case via the lowered `>=1` gate (user-pick reversal of BUG-020
// option 3 hybrid). Earlier hybrid did not match mockup ImageGallery layout
// (label / count badge / view-all link / numeric badge top-left), so the
// canonical ImageGallery is now the single render path.

function FootnoteList({
  citations,
  onOpenScreenshot,
}: {
  citations: Citation[];
  onOpenScreenshot: (citation: Citation, image: ImageRef) => void;
}) {
  return (
    <ol
      style={{
        marginTop: 16,
        paddingLeft: 22,
        fontSize: 12,
        lineHeight: 1.6,
        color: 'oklch(var(--muted-foreground))',
      }}
    >
      {citations.map((c) => (
        <li key={c.chunk_id} style={{ marginBottom: 4 }}>
          <span style={{ color: 'oklch(var(--foreground))', fontWeight: 500 }}>{c.doc_title}</span>
          {c.chunk_title && (
            <>
              {' — '}
              <span>{c.chunk_title}</span>
            </>
          )}
          {c.embedded_images.length > 0 && (
            <button
              type="button"
              className="btn btn-ghost btn-xs"
              onClick={() => onOpenScreenshot(c, c.embedded_images[0]!)}
              style={{ marginLeft: 6 }}
            >
              <Layers size={10} /> Screenshot
            </button>
          )}
        </li>
      ))}
    </ol>
  );
}

// ──────────────────────────────────────────────────────────────────────────
// InlineImageCard — mockup ekp-page-chat.jsx:581-617 (function definition) +
// 470-498 (usage inline in AnswerBody). Restored by BUG-019 after W22 F4 wrongly
// dropped it as a "custom abstraction".
// Mockup uses <SyntheticScreenshot> as a placeholder; real renders <img>
// against the same-origin proxy URL (Citation.embedded_images[].blob_url,
// already proxied per BUG-010 via backend query.py::_proxy_citation_images).
// ──────────────────────────────────────────────────────────────────────────

function InlineImageCard({
  citation,
  image,
  citationIdx,
  figureIdx,
  onOpen,
}: {
  citation: Citation;
  image: ImageRef;
  citationIdx: number;
  figureIdx: number;
  onOpen: () => void;
}) {
  const title = imageTitle(image, citation);
  // BUG-026 C-ii — attribute to the image's OWN section (source_section) so a
  // neighbour-attached image shows its true section, not the citing chunk's.
  const caption = `Citation [${citationIdx}] · ${imageSectionPath(image, citation).join(' › ')}`;
  return (
    <figure
      style={{
        margin: '18px 0',
        border: '1px solid oklch(var(--border))',
        borderRadius: 'var(--radius-md)',
        overflow: 'hidden',
        background: 'oklch(var(--card))',
      }}
    >
      <div style={{ position: 'relative' }}>
        <img
          src={image.blob_url}
          alt={image.alt_text || title}
          style={{
            display: 'block',
            width: '100%',
            height: 'auto',
            maxHeight: 360,
            objectFit: 'contain',
            background: 'oklch(var(--muted) / 0.4)',
          }}
        />
        <div
          style={{
            position: 'absolute',
            top: 10,
            right: 10,
            display: 'flex',
            gap: 4,
          }}
        >
          <button
            type="button"
            className="btn btn-secondary btn-xs"
            style={{ background: 'oklch(var(--background) / 0.9)' }}
            onClick={(e) => {
              e.stopPropagation();
              onOpen();
            }}
          >
            <Eye size={11} /> Full size
          </button>
        </div>
      </div>
      <figcaption
        style={{
          padding: '10px 14px',
          background: 'oklch(var(--muted) / 0.4)',
          borderTop: '1px solid oklch(var(--border))',
          fontSize: 12.5,
          display: 'flex',
          alignItems: 'center',
          gap: 10,
        }}
      >
        <span className="mono muted text-xs">figure {figureIdx}</span>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div
            style={{
              fontWeight: 500,
              color: 'oklch(var(--foreground))',
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
            }}
            title={title}
          >
            {title}
          </div>
          <div className="muted text-xs" style={{ marginTop: 1 }}>
            {caption}
          </div>
        </div>
      </figcaption>
    </figure>
  );
}

// ──────────────────────────────────────────────────────────────────────────
// ImageGallery — mockup ekp-page-chat.jsx:621-664 ("Referenced screenshots").
// Renders below the answer when 2+ cited chunks carry embedded images.
// Thumbnails use the real ImageRef.blob_url (mockup draws synthetic SVGs).
// ──────────────────────────────────────────────────────────────────────────

function ImageGallery({
  images,
  totalCount,
  kbId,
  onOpenScreenshot,
}: {
  // BUG-026 Finding A — render the deduped unique-image list (one thumbnail per
  // distinct image), not one-per-citation. Each entry carries its owning
  // citation + the full-citations badge index. The badge stays anchored on the
  // full-citations position (per BUG-024) — `dedupeCitationImages` computes
  // `citationIdx` as `idx+1` over `message.citations`, matching CitationPill /
  // SourcesStrip / ScreenshotModal numbering.
  // BUG-031 (A) — `images` is the CAPPED list (≤ INLINE_IMAGE_CAP); `totalCount`
  // is the true deduped total so the badge stays honest and "View all" surfaces
  // when capped.
  images: DedupedCitationImage[];
  totalCount: number;
  kbId: string;
  onOpenScreenshot: (citation: Citation, image: ImageRef) => void;
}) {
  return (
    <div style={{ marginTop: 18 }}>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          marginBottom: 8,
        }}
      >
        <span
          className="muted mono text-xs"
          style={{
            letterSpacing: '0.04em',
            textTransform: 'uppercase',
            fontWeight: 600,
          }}
        >
          Referenced screenshots
        </span>
        {/* BUG-031 (A) — badge shows TRUE total (e.g. 24) even when the grid is
            capped to INLINE_IMAGE_CAP, so the count stays honest. */}
        <span className="badge badge-muted">{totalCount}</span>
        <div className="spacer" style={{ flex: 1 }} />
        {/* BUG-031 (A) — wire the mockup's overflow affordance: when capped, link to
            the KB images tab (the "Image Library") so images N+1.. stay reachable.
            kbId may be '' before the KB list loads → fall back to a static button. */}
        {kbId ? (
          <Link href={`/kb/${kbId}?tab=images`} className="btn btn-ghost btn-xs">
            View all in Image Library →
          </Link>
        ) : (
          <button type="button" className="btn btn-ghost btn-xs">
            View all in Image Library →
          </button>
        )}
      </div>
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))',
          gap: 8,
        }}
      >
        {images.map(({ citation, image, citationIdx }) => (
          <button
            key={`${citation.chunk_id}-${image.checksum_sha256 || image.blob_url}`}
            type="button"
            onClick={() => onOpenScreenshot(citation, image)}
            className="btn btn-secondary"
            style={{
              padding: 0,
              height: 'auto',
              flexDirection: 'column',
              background: 'oklch(var(--card))',
              overflow: 'hidden',
              textAlign: 'left',
              borderColor: 'oklch(var(--border))',
            }}
          >
            <div
              style={{
                width: '100%',
                aspectRatio: '16/9',
                overflow: 'hidden',
                position: 'relative',
              }}
            >
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={image.blob_url}
                alt={image.alt_text}
                style={{
                  width: '100%',
                  height: '100%',
                  objectFit: 'cover',
                  display: 'block',
                }}
              />
              <span
                style={{
                  position: 'absolute',
                  top: 4,
                  left: 4,
                  background: 'oklch(var(--accent))',
                  color: 'oklch(var(--accent-foreground))',
                  padding: '1px 6px',
                  borderRadius: 4,
                  fontFamily: 'var(--font-mono)',
                  fontSize: 10,
                  fontWeight: 600,
                }}
              >
                {citationIdx}
              </span>
            </div>
            <div style={{ width: '100%', padding: '8px 10px' }}>
              <div
                style={{
                  fontSize: 11.5,
                  fontWeight: 500,
                  lineHeight: 1.3,
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                }}
              >
                {imageTitle(image, citation)}
              </div>
              <div
                className="muted mono text-xs"
                style={{
                  marginTop: 2,
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                }}
              >
                {citation.doc_title}
              </div>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}

// ──────────────────────────────────────────────────────────────────────────
// Sources strip — mockup ekp-page-chat.jsx:667-778 (footnote/inline mode footer)
// ──────────────────────────────────────────────────────────────────────────

function SourcesStrip({
  citations,
  onOpenScreenshot,
}: {
  citations: Citation[];
  onOpenScreenshot: (citation: Citation, image: ImageRef) => void;
}) {
  const docCount = new Set(citations.map((c) => c.doc_id)).size;
  return (
    <div
      style={{
        marginTop: 22,
        padding: 14,
        border: '1px solid oklch(var(--border))',
        borderRadius: 'var(--radius-md)',
        background: 'oklch(var(--muted) / 0.2)',
      }}
    >
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          marginBottom: 10,
        }}
      >
        <BookOpen size={13} className="muted" />
        <span
          className="mono text-xs"
          style={{
            letterSpacing: '0.04em',
            textTransform: 'uppercase',
            fontWeight: 600,
            color: 'oklch(var(--foreground))',
          }}
        >
          Sources
        </span>
        <span className="muted text-xs">
          · {citations.length} chunks across {docCount} document
          {docCount === 1 ? '' : 's'}
        </span>
      </div>
      {/* minmax(0,1fr) not 1fr — `1fr` = minmax(auto,1fr) lets a long unbroken
          doc_id/doc_title push the track wider than the container (BUG-007
          amendment: real-data overflow). Visually identical 2 equal columns. */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'minmax(0, 1fr) minmax(0, 1fr)',
          gap: 8,
        }}
      >
        {citations.map((c, i) => (
          <SourceDocCard
            key={c.chunk_id}
            citation={c}
            idx={i + 1}
            onOpenScreenshot={() =>
              c.embedded_images[0] && onOpenScreenshot(c, c.embedded_images[0])
            }
          />
        ))}
      </div>
    </div>
  );
}

function SourceDocCard({
  citation,
  idx,
  onOpenScreenshot,
}: {
  citation: Citation;
  idx: number;
  onOpenScreenshot: () => void;
}) {
  const hasImage = citation.embedded_images.length > 0;
  // BUG-021 — use server-side authoritative doc_format from Citation schema
  // (Literal docx/pdf/pptx). Earlier doc_id ext-sniff fell back to 'unknown'
  // when doc_id was the user-supplied identifier without `.docx`/`.pdf`/`.pptx`.
  const fileType = citation.doc_format;
  return (
    <div
      style={{
        padding: '10px 12px',
        background: 'oklch(var(--card))',
        border: '1px solid oklch(var(--border))',
        borderRadius: 'var(--radius-sm)',
        display: 'flex',
        gap: 10,
        transition: 'border-color var(--duration-fast)',
      }}
    >
      <div
        style={{
          flexShrink: 0,
          width: 22,
          height: 22,
          borderRadius: 4,
          background: 'oklch(var(--accent) / 0.12)',
          color: 'oklch(var(--accent))',
          display: 'grid',
          placeItems: 'center',
          fontFamily: 'var(--font-mono)',
          fontSize: 11,
          fontWeight: 700,
        }}
      >
        {idx}
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <FileTypeChip type={fileType} />
          <span
            style={{
              fontSize: 12.5,
              fontWeight: 500,
              flex: 1,
              minWidth: 0,
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
            }}
            title={citation.doc_title}
          >
            {citation.doc_title}
          </span>
        </div>
        {citation.section_path.length > 0 && (
          <div className="section-path text-xs" style={{ marginTop: 4 }}>
            {citation.section_path.map((s, j) => (
              <span key={j}>{s}</span>
            ))}
          </div>
        )}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            marginTop: 6,
          }}
        >
          <span className="mono muted text-xs">chunk #{citation.chunk_index}</span>
          <div
            style={{
              flex: 1,
              height: 3,
              background: 'oklch(var(--muted))',
              borderRadius: 999,
              overflow: 'hidden',
            }}
          >
            <div
              style={{
                width: `${citation.relevance_score * 100}%`,
                height: '100%',
                background: 'oklch(var(--accent))',
              }}
            />
          </div>
          <span
            className="mono text-xs"
            style={{
              fontVariantNumeric: 'tabular-nums',
              fontWeight: 600,
            }}
          >
            {formatRelevance(citation.relevance_score)}
          </span>
        </div>
        <div style={{ display: 'flex', gap: 4, marginTop: 6 }}>
          {hasImage && (
            <button type="button" className="btn btn-ghost btn-xs" onClick={onOpenScreenshot}>
              <Layers size={10} /> Screenshot
            </button>
          )}
          <Link
            href={`/kb/drive_user_manuals/docs/${citation.doc_id}`}
            className="btn btn-ghost btn-xs"
          >
            <LinkIcon size={10} /> Open doc
          </Link>
        </div>
      </div>
    </div>
  );
}

function FileTypeChip({ type }: { type: keyof typeof FILE_TYPE_COLORS }) {
  const colors = FILE_TYPE_COLORS[type] ?? FILE_TYPE_COLORS.unknown!;
  return (
    <span
      style={{
        padding: '1px 5px',
        fontSize: 10,
        fontFamily: 'var(--font-mono)',
        fontWeight: 700,
        letterSpacing: '0.04em',
        background: colors.bg,
        color: colors.fg,
        border: `1px solid ${colors.border}`,
        borderRadius: 3,
        textTransform: 'uppercase',
        lineHeight: 1.3,
      }}
    >
      {type}
    </span>
  );
}

// ──────────────────────────────────────────────────────────────────────────
// CitationPanel (sidebar mode) — mockup ekp-page-chat.jsx:799-869
// ──────────────────────────────────────────────────────────────────────────

function CitationPanel({
  citations,
  onClose,
  onOpenScreenshot,
}: {
  citations: Citation[];
  onClose: () => void;
  onOpenScreenshot: (c: Citation, img: ImageRef) => void;
}) {
  const imageCount = citations.filter((c) => c.embedded_images.length > 0).length;
  return (
    <aside
      style={{
        display: 'flex',
        flexDirection: 'column',
        background: 'oklch(var(--card))',
        overflow: 'hidden',
      }}
    >
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          padding: '11px 16px',
          borderBottom: '1px solid oklch(var(--border))',
          flexShrink: 0,
        }}
      >
        <div>
          <div style={{ fontSize: 13.5, fontWeight: 600 }}>Sources</div>
          <div className="muted text-xs">
            {citations.length} chunk{citations.length === 1 ? '' : 's'} · {imageCount} with
            screenshot{imageCount === 1 ? '' : 's'} · sorted by relevance
          </div>
        </div>
        <div className="spacer" style={{ flex: 1 }} />
        <button type="button" className="btn btn-ghost btn-icon btn-sm" onClick={onClose}>
          <XIcon size={14} />
        </button>
      </div>
      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: 12,
          display: 'flex',
          flexDirection: 'column',
          gap: 8,
        }}
      >
        {citations.map((c, i) => (
          <PanelSourceCard
            key={c.chunk_id}
            citation={c}
            idx={i + 1}
            onOpenScreenshot={() =>
              c.embedded_images[0] && onOpenScreenshot(c, c.embedded_images[0])
            }
          />
        ))}
      </div>
    </aside>
  );
}

function PanelSourceCard({
  citation,
  idx,
  onOpenScreenshot,
}: {
  citation: Citation;
  idx: number;
  onOpenScreenshot: () => void;
}) {
  const hasImage = citation.embedded_images.length > 0;
  // BUG-021 — use server-side authoritative doc_format from Citation schema
  // (Literal docx/pdf/pptx). Earlier doc_id ext-sniff fell back to 'unknown'
  // when doc_id was the user-supplied identifier without `.docx`/`.pdf`/`.pptx`.
  const fileType = citation.doc_format;
  return (
    <div
      style={{
        border: '1px solid oklch(var(--border))',
        borderRadius: 'var(--radius-sm)',
        padding: 12,
        background: 'oklch(var(--card))',
      }}
    >
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          marginBottom: 8,
        }}
      >
        <div
          style={{
            flexShrink: 0,
            width: 22,
            height: 22,
            background: 'oklch(var(--accent) / 0.12)',
            color: 'oklch(var(--accent))',
            borderRadius: 4,
            display: 'grid',
            placeItems: 'center',
            fontFamily: 'var(--font-mono)',
            fontWeight: 700,
            fontSize: 11,
          }}
        >
          {idx}
        </div>
        <FileTypeChip type={fileType} />
        <span
          className="mono text-xs"
          style={{
            fontWeight: 600,
            color: 'oklch(var(--foreground))',
            marginLeft: 'auto',
          }}
        >
          {formatRelevance(citation.relevance_score)}
        </span>
      </div>

      <div
        style={{
          fontSize: 12.5,
          fontWeight: 500,
          marginBottom: 4,
          lineHeight: 1.4,
        }}
        title={citation.doc_title}
      >
        {citation.doc_title}
      </div>
      {citation.section_path.length > 0 && (
        <div className="section-path text-xs" style={{ marginBottom: 6 }}>
          {citation.section_path.map((s, j) => (
            <span key={j}>{s}</span>
          ))}
        </div>
      )}
      {citation.chunk_title && (
        <div className="muted text-xs" style={{ marginBottom: 6, lineHeight: 1.45 }}>
          {citation.chunk_title}
        </div>
      )}

      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          marginTop: 6,
        }}
      >
        <span className="mono muted text-xs">chunk #{citation.chunk_index}</span>
        {hasImage && (
          <button type="button" className="btn btn-ghost btn-xs" onClick={onOpenScreenshot}>
            <Layers size={10} /> Screenshot
          </button>
        )}
        <div style={{ flex: 1 }} />
        <Link
          href={`/kb/drive_user_manuals/docs/${citation.doc_id}`}
          className="btn btn-ghost btn-xs"
        >
          Open →
        </Link>
      </div>
    </div>
  );
}

// ──────────────────────────────────────────────────────────────────────────
// FeedbackBar — mockup ekp-page-chat.jsx:377-440
// ──────────────────────────────────────────────────────────────────────────

function FeedbackBar({
  traceId,
  citations,
  imageCount,
}: {
  traceId: string;
  citations: Citation[];
  imageCount: number;
}) {
  const [rating, setRating] = useState<'thumbs_up' | 'thumbs_down' | null>(null);
  const [showCommentBox, setShowCommentBox] = useState(false);

  return (
    <>
      <div
        style={{
          display: 'flex',
          gap: 4,
          marginTop: 16,
          alignItems: 'center',
          flexWrap: 'wrap',
        }}
      >
        <button type="button" className="btn btn-ghost btn-icon btn-xs" title="Copy answer">
          <Copy size={12} />
        </button>
        <button type="button" className="btn btn-ghost btn-icon btn-xs" title="Regenerate">
          <RefreshCw size={12} />
        </button>
        <div
          style={{
            width: 1,
            height: 14,
            background: 'oklch(var(--border))',
            margin: '0 4px',
          }}
        />
        <span className="muted text-xs" style={{ marginRight: 2 }}>
          Was this helpful?
        </span>
        <button
          type="button"
          className="btn btn-ghost btn-xs"
          onClick={() => {
            setRating('thumbs_up');
            setShowCommentBox(true);
          }}
          style={
            rating === 'thumbs_up'
              ? {
                  background: 'oklch(var(--success) / 0.12)',
                  color: 'oklch(var(--success))',
                }
              : undefined
          }
        >
          <ArrowUp size={11} /> Yes
        </button>
        <button
          type="button"
          className="btn btn-ghost btn-xs"
          onClick={() => {
            setRating('thumbs_down');
            setShowCommentBox(true);
          }}
          style={
            rating === 'thumbs_down'
              ? {
                  background: 'oklch(var(--destructive) / 0.1)',
                  color: 'oklch(var(--destructive))',
                }
              : undefined
          }
        >
          <ArrowDown size={11} /> No
        </button>
        <span className="spacer" style={{ flex: 1 }} />
        <span
          className="muted mono text-xs"
          style={{ display: 'flex', alignItems: 'center', gap: 8 }}
        >
          <Layers size={10} /> {citations.length} citation
          {citations.length === 1 ? '' : 's'} · {imageCount} with screenshot
          {imageCount === 1 ? '' : 's'}
        </span>
      </div>

      {showCommentBox && (
        <div
          style={{
            marginTop: 10,
            padding: '10px 12px',
            background: 'oklch(var(--muted) / 0.4)',
            border: '1px solid oklch(var(--border))',
            borderRadius: 'var(--radius-sm)',
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              marginBottom: 6,
            }}
          >
            <span className="text-xs" style={{ fontWeight: 500 }}>
              {rating === 'thumbs_up'
                ? 'Glad it helped! Tell us more (optional)'
                : 'Sorry about that. What went wrong? (optional)'}
            </span>
            <div className="spacer" style={{ flex: 1 }} />
            <button
              type="button"
              className="btn btn-ghost btn-icon btn-xs"
              onClick={() => setShowCommentBox(false)}
            >
              <XIcon size={11} />
            </button>
          </div>
          <textarea
            className="input"
            rows={2}
            placeholder={
              rating === 'thumbs_up'
                ? 'What worked well?'
                : 'Missing info, wrong answer, refused incorrectly…'
            }
            style={{ minHeight: 50, fontSize: 12.5 }}
          />
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              marginTop: 6,
            }}
          >
            <span className="muted mono text-xs">
              ref <span style={{ color: 'oklch(var(--accent))' }}>{traceId.slice(-12)}</span>
            </span>
            <div className="spacer" style={{ flex: 1 }} />
            <button
              type="button"
              className="btn btn-ghost btn-xs"
              onClick={() => setShowCommentBox(false)}
            >
              Skip
            </button>
            <button type="button" className="btn btn-accent btn-xs">
              Submit feedback
            </button>
          </div>
        </div>
      )}
    </>
  );
}

// ──────────────────────────────────────────────────────────────────────────
// ScreenshotModal — pared back from mockup (real images come from blob_url,
// not synthetic). Centred dialog with image + caption + close.
// ──────────────────────────────────────────────────────────────────────────

// ScreenshotModal — mockup ekp-page-chat.jsx:1068-1121 2-column layout
// (image ~1.6fr left + side panel ~1fr right with section_path / chunk_id /
// chunk_title / Open in Document Detail + Open original buttons). BUG-021
// amendment: prior single-pane image-only viewer replaced. `idx` resolved
// at call site from latestAssistantCitations so the header carries the same
// numeric badge as CitationPill / PanelSourceCard. `kbId` is needed for the
// Document Detail deep-link (matches the AppShell `/kb/[id]/docs/[docId]`
// route per ADR-0029).
function ScreenshotModal({
  citation,
  image,
  idx,
  kbId,
  onClose,
}: {
  citation: Citation;
  image: ImageRef;
  idx: number;
  kbId: string;
  onClose: () => void;
}) {
  // CH-004 — click-image-to-zoom progressive enhancement on top of the
  // mockup-faithful 2-col layout (BUG-021 amendment baseline). The 2-col
  // grid compresses the image to ~62% of modal width; user opts in to a
  // full-viewport overlay (z-index 200 > modal z-index 100) when needing
  // to inspect detail. ESC handler is scoped to isZoomed=true mount so it
  // never collides with the (currently absent) modal-level ESC handler
  // and gets cleaned up on flip/unmount — no leaked listener.
  const [isZoomed, setIsZoomed] = useState(false);
  useEffect(() => {
    if (!isZoomed) return;
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') {
        e.stopPropagation();
        setIsZoomed(false);
      }
    }
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [isZoomed]);
  return (
    <>
      <div
        role="dialog"
        aria-modal="true"
        onClick={onClose}
        style={{
          position: 'fixed',
          inset: 0,
          background: 'oklch(var(--background) / 0.85)',
          backdropFilter: 'blur(4px)',
          zIndex: 100,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: 32,
        }}
      >
        <div
          onClick={(e) => e.stopPropagation()}
          style={{
            width: 1040,
            maxWidth: '92vw',
            maxHeight: '90vh',
            background: 'oklch(var(--card))',
            border: '1px solid oklch(var(--border))',
            borderRadius: 'var(--radius-md)',
            overflow: 'hidden',
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          {/* Header — idx badge + chunk_title + doc_title + relevance_score + close */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 10,
              padding: '12px 16px',
              borderBottom: '1px solid oklch(var(--border))',
            }}
          >
            <span
              style={{
                flexShrink: 0,
                width: 22,
                height: 22,
                background: 'oklch(var(--accent))',
                color: 'oklch(var(--accent-foreground))',
                borderRadius: 4,
                display: 'grid',
                placeItems: 'center',
                fontFamily: 'var(--font-mono)',
                fontWeight: 700,
                fontSize: 12,
              }}
            >
              {idx}
            </span>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontSize: 14.5, fontWeight: 600 }}>
                {citation.chunk_title || 'Screenshot'}
              </div>
              <div
                className="muted mono text-xs"
                style={{
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                }}
              >
                {citation.doc_title} · chunk #{citation.chunk_index}
              </div>
            </div>
            <span className="mono" style={{ fontSize: 13, fontWeight: 600 }}>
              {formatRelevance(citation.relevance_score)}
            </span>
            <button
              type="button"
              className="btn btn-ghost btn-icon btn-sm"
              onClick={onClose}
              aria-label="Close screenshot"
            >
              <XIcon size={14} />
            </button>
          </div>

          {/* Body — 2-column grid (image left ~1.6fr, side panel right ~1fr) */}
          <div
            style={{
              flex: 1,
              overflow: 'auto',
              display: 'grid',
              gridTemplateColumns: '1.6fr 1fr',
              gap: 16,
              padding: 16,
            }}
          >
            <div
              style={{
                border: '1px solid oklch(var(--border))',
                borderRadius: 'var(--radius-md)',
                overflow: 'hidden',
                background: 'oklch(var(--muted) / 0.2)',
                display: 'grid',
                placeItems: 'center',
                minHeight: 280,
              }}
            >
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={image.blob_url}
                alt={image.alt_text || citation.chunk_title || 'Screenshot'}
                onClick={(e) => {
                  // CH-004 — escalate to full-viewport zoom overlay; stop
                  // propagation so the click does not bubble to the dialog
                  // backdrop (which calls onClose).
                  e.stopPropagation();
                  setIsZoomed(true);
                }}
                style={{
                  maxWidth: '100%',
                  maxHeight: '70vh',
                  display: 'block',
                  objectFit: 'contain',
                  cursor: 'zoom-in',
                }}
              />
            </div>

            {/* Side panel — section_path / chunk_id / chunk_title preview / actions */}
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: 12,
                minWidth: 0,
              }}
            >
              <div>
                <div
                  className="muted mono text-xs"
                  style={{
                    marginBottom: 4,
                    letterSpacing: '0.04em',
                    textTransform: 'uppercase',
                  }}
                >
                  section_path
                </div>
                <div className="section-path text-xs">
                  {citation.section_path.length > 0 ? (
                    citation.section_path.map((s, j) => <span key={j}>{s}</span>)
                  ) : (
                    <span className="muted">(root)</span>
                  )}
                </div>
              </div>
              <div>
                <div
                  className="muted mono text-xs"
                  style={{
                    marginBottom: 4,
                    letterSpacing: '0.04em',
                    textTransform: 'uppercase',
                  }}
                >
                  chunk_id
                </div>
                <div
                  className="mono text-xs"
                  style={{
                    wordBreak: 'break-all',
                    color: 'oklch(var(--foreground))',
                  }}
                >
                  {citation.chunk_id}
                </div>
              </div>
              <div>
                <div
                  className="muted mono text-xs"
                  style={{
                    marginBottom: 4,
                    letterSpacing: '0.04em',
                    textTransform: 'uppercase',
                  }}
                >
                  Section preview
                </div>
                <div
                  style={{
                    padding: '10px 12px',
                    background: 'oklch(var(--muted) / 0.4)',
                    borderRadius: 'var(--radius-sm)',
                    fontSize: 12.5,
                    lineHeight: 1.55,
                    border: '1px solid oklch(var(--border))',
                  }}
                >
                  {citation.chunk_title || image.alt_text || '(no preview)'}
                </div>
              </div>
              <div className="spacer" style={{ flex: 1 }} />
              <Link
                href={`/kb/${kbId}/docs/${citation.doc_id}`}
                className="btn btn-accent"
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 6,
                  justifyContent: 'center',
                }}
                onClick={onClose}
              >
                <FileText size={14} /> Open in Document Detail
              </Link>
            </div>
          </div>
        </div>
      </div>
      {/* CH-004 — full-viewport zoom overlay layer (z-index 200 > modal 100).
        Conditional mount on isZoomed=true; dismissed via backdrop click,
        image click, or ESC (window-scoped via useEffect above). objectFit
        contain caps over-large images at viewport per spec §4.1 — strict
        1:1 pixel + scroll behaviour deferred per spec §2.2 out-of-scope. */}
      {isZoomed && (
        <div
          role="dialog"
          aria-modal="true"
          aria-label="Full-resolution screenshot"
          onClick={() => setIsZoomed(false)}
          style={{
            position: 'fixed',
            inset: 0,
            background: 'oklch(0 0 0 / 0.92)',
            zIndex: 200,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'zoom-out',
            padding: 16,
          }}
        >
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={image.blob_url}
            alt={image.alt_text || citation.chunk_title || 'Screenshot full-resolution'}
            onClick={(e) => {
              e.stopPropagation();
              setIsZoomed(false);
            }}
            style={{
              maxWidth: '100%',
              maxHeight: '100%',
              objectFit: 'contain',
              cursor: 'zoom-out',
              display: 'block',
            }}
          />
        </div>
      )}
    </>
  );
}

// ──────────────────────────────────────────────────────────────────────────
// ChatComposer — textarea + send/stop (replaces mockup textbox at thread bottom)
// ──────────────────────────────────────────────────────────────────────────

function ChatComposer({
  input,
  onInputChange,
  isStreaming,
  onSubmit,
  onStop,
  textareaRef,
}: {
  input: string;
  onInputChange: (value: string) => void;
  isStreaming: boolean;
  onSubmit: (e: FormEvent<HTMLFormElement>) => void;
  onStop: () => void;
  textareaRef: React.MutableRefObject<HTMLTextAreaElement | null>;
}) {
  function handleKey(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      const form = (e.currentTarget.form ?? null) as HTMLFormElement | null;
      form?.requestSubmit();
    }
  }

  return (
    <form
      onSubmit={onSubmit}
      style={{
        flexShrink: 0,
        padding: '12px 20px 18px',
        borderTop: '1px solid oklch(var(--border))',
        background: 'oklch(var(--background))',
      }}
    >
      <div
        style={{
          maxWidth: 860,
          margin: '0 auto',
          display: 'flex',
          gap: 8,
          alignItems: 'flex-end',
        }}
      >
        <textarea
          ref={textareaRef}
          className="input"
          rows={1}
          placeholder="Ask about Ricoh financial software… (Enter to send · Shift+Enter for newline)"
          value={input}
          onChange={(e) => onInputChange(e.target.value)}
          onKeyDown={handleKey}
          disabled={isStreaming}
          style={{
            flex: 1,
            minHeight: 40,
            maxHeight: 200,
            resize: 'vertical',
            fontSize: 14,
            lineHeight: 1.5,
            padding: '10px 12px',
          }}
        />
        {isStreaming ? (
          <button
            type="button"
            className="btn btn-secondary btn-lg"
            onClick={onStop}
            title="Stop streaming"
            style={{ justifyContent: 'center', gap: 6 }}
          >
            <Square size={14} /> Stop
          </button>
        ) : (
          <button
            type="submit"
            className="btn btn-accent btn-lg"
            disabled={!input.trim()}
            style={{ justifyContent: 'center', gap: 6 }}
          >
            <Send size={14} /> Send
          </button>
        )}
      </div>
      <div className="muted mono text-xs" style={{ marginTop: 8, textAlign: 'center' }}>
        Hybrid retrieval · Cohere v4.0-pro rerank · GPT-5.5 synthesis · CRAG L2 self-correction
      </div>
    </form>
  );
}

// Keep these imports referenced even when not directly rendered (some are used
// conditionally and TS isn't smart enough about useState mutations).
void Eye;
void FileText;
void Star;
void ChevronRight;
