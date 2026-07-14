'use client';

/**
 * C09 global search command palette — W18 F6 (per ADR-0024 D6 + architecture.md v6 §5.0).
 *
 * Cmd/Ctrl+K (or the top-bar search trigger) opens a quick-jump palette. **Tier 1 scope =
 * navigation quick-jump only** — NOT semantic search-as-you-type across chunks (that's a
 * Tier 2 candidate per CLAUDE.md §5.4 H4). Result types, in order:
 *   1. Pages          — the 5 sidebar modules + Settings (static; filtered by label/keywords)
 *   2. Knowledge bases — names off the cached `GET /kb` list (`kbApi.list`) → /kb/[id]
 *   3. "Ask in chat: …" — always present when there's a query → /chat?q=<encoded> (the chat
 *                         page reads `?q=` on mount and pre-fills the input — W18 F6.5)
 *
 * Built on the shadcn `Dialog` primitive (Radix) — no new dependency. The Dialog gives
 * role="dialog" + aria-modal + focus trap + Escape-to-close for free; arrow-key result
 * navigation + `aria-activedescendant` are wired here on the search input (combobox/listbox
 * pattern). Controlled by `<AppShell>` (`open` / `onOpenChange`).
 *
 * 100% design-token classes — no hardcoded colour arbitrary-values (W15 milestone preserved).
 */

import { useRouter } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { useEffect, useMemo, useState, type KeyboardEvent } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Activity,
  ArrowRight,
  Database,
  FlaskConical,
  LayoutDashboard,
  MessageSquare,
  Search,
  Settings as SettingsIcon,
} from 'lucide-react';

import {
  Dialog,
  DialogContent,
  DialogTitle,
} from '@/components/ui/dialog';
import { kbApi } from '@/lib/api/kb';
import { cn } from '@/lib/utils';

type ResultIcon = typeof LayoutDashboard;

interface PageResult {
  kind: 'page';
  id: string;
  label: string;
  href: string;
  Icon: ResultIcon;
  keywords?: string;
}
interface KbResult {
  kind: 'kb';
  id: string;
  label: string;
  href: string;
  kbId: string;
}
interface AskResult {
  kind: 'ask';
  id: 'ask';
  label: string;
  href: string;
}
type SearchResult = PageResult | KbResult | AskResult;

/** The static destinations — the 5 sidebar modules + Settings. `labelKey`
 *  resolves against the `GlobalSearch` messages namespace at render time. */
const PAGE_RESULTS: {
  id: string;
  labelKey: string;
  href: string;
  Icon: ResultIcon;
  keywords?: string;
}[] = [
  { id: 'page-dashboard', labelKey: 'pageDashboard', href: '/dashboard', Icon: LayoutDashboard, keywords: 'home overview' },
  { id: 'page-chat', labelKey: 'pageChat', href: '/chat', Icon: MessageSquare, keywords: 'ask question' },
  { id: 'page-kb', labelKey: 'pageKnowledgeBases', href: '/kb', Icon: Database, keywords: 'kb documents upload' },
  { id: 'page-eval', labelKey: 'pageEvalConsole', href: '/eval', Icon: FlaskConical, keywords: 'evaluation ragas metrics' },
  { id: 'page-traces', labelKey: 'pageTraces', href: '/traces', Icon: Activity, keywords: 'debug langfuse pipeline' },
  { id: 'page-settings', labelKey: 'pageSettings', href: '/settings', Icon: SettingsIcon, keywords: 'profile theme account' },
];

interface GlobalSearchProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function GlobalSearch({ open, onOpenChange }: GlobalSearchProps) {
  const router = useRouter();
  const t = useTranslations('GlobalSearch');
  const [query, setQuery] = useState('');
  const [activeIndex, setActiveIndex] = useState(0);

  // The KB list — shares the dashboard's query cache (same key); only fetched while open.
  const { data: kbs } = useQuery({
    queryKey: ['kb', 'list'],
    queryFn: () => kbApi.list(),
    enabled: open,
    staleTime: 60_000,
  });

  // Reset on each open.
  useEffect(() => {
    if (open) {
      setQuery('');
      setActiveIndex(0);
    }
  }, [open]);

  const results = useMemo<SearchResult[]>(() => {
    const q = query.trim().toLowerCase();

    const pages: PageResult[] = PAGE_RESULTS.map((p) => ({
      kind: 'page' as const,
      id: p.id,
      label: t(p.labelKey),
      href: p.href,
      Icon: p.Icon,
      keywords: p.keywords,
    })).filter(
      (p) => !q || p.label.toLowerCase().includes(q) || (p.keywords ?? '').includes(q),
    );

    const kbResults: KbResult[] = (kbs ?? [])
      .filter((kb) => !q || kb.name.toLowerCase().includes(q) || kb.kb_id.toLowerCase().includes(q))
      .map((kb) => ({
        kind: 'kb',
        id: `kb-${kb.kb_id}`,
        label: kb.name,
        href: `/kb/${kb.kb_id}`,
        kbId: kb.kb_id,
      }));

    const q0 = query.trim();
    const ask: AskResult[] = q0
      ? [{ kind: 'ask', id: 'ask', label: t('askInChat', { query: q0 }), href: `/chat?q=${encodeURIComponent(q0)}` }]
      : [];

    return [...pages, ...kbResults, ...ask];
  }, [query, kbs, t]);

  const safeActive = Math.min(activeIndex, Math.max(0, results.length - 1));

  function select(result: SearchResult) {
    onOpenChange(false);
    router.push(result.href);
  }

  function onInputKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setActiveIndex((i) => Math.min(i + 1, results.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActiveIndex((i) => Math.max(i - 1, 0));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      const result = results[safeActive];
      if (result) select(result);
    }
    // Escape — handled by Radix Dialog (onOpenChange(false)).
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        aria-describedby={undefined}
        className="top-[14%] max-w-xl translate-y-0 gap-0 overflow-hidden p-0"
      >
        <DialogTitle className="sr-only">{t('dialogTitle')}</DialogTitle>

        {/* Search input row (the Dialog's own close-X sits top-right; pr-10 keeps text clear of it) */}
        <div className="flex items-center gap-2 border-b border-border px-3">
          <Search className="h-4 w-4 shrink-0 text-muted-foreground" aria-hidden="true" />
          {/* eslint-disable-next-line jsx-a11y/no-autofocus -- a command palette focuses its input on open by design */}
          <input
            autoFocus
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setActiveIndex(0);
            }}
            onKeyDown={onInputKeyDown}
            placeholder={t('inputPlaceholder')}
            aria-label={t('inputAria')}
            role="combobox"
            aria-expanded
            aria-controls="global-search-results"
            aria-activedescendant={results[safeActive]?.id}
            className="h-12 w-full bg-transparent pr-10 text-sm text-foreground outline-none placeholder:text-muted-foreground"
          />
        </div>

        {/* Results */}
        <ul
          id="global-search-results"
          role="listbox"
          aria-label={t('resultsAria')}
          className="max-h-80 overflow-y-auto p-1"
        >
          {results.length === 0 ? (
            <li className="px-3 py-6 text-center text-sm text-muted-foreground">{t('noMatches')}</li>
          ) : (
            results.map((result, i) => (
              <li
                key={result.id}
                id={result.id}
                role="option"
                aria-selected={i === safeActive}
                onMouseMove={() => setActiveIndex(i)}
                onClick={() => select(result)}
                className={cn(
                  'flex cursor-pointer items-center gap-3 rounded-sm px-3 py-2 text-sm text-foreground',
                  i === safeActive && 'bg-muted',
                )}
              >
                {result.kind === 'page' ? (
                  <result.Icon className="h-4 w-4 shrink-0 text-muted-foreground" aria-hidden="true" />
                ) : result.kind === 'kb' ? (
                  <Database className="h-4 w-4 shrink-0 text-muted-foreground" aria-hidden="true" />
                ) : (
                  <MessageSquare className="h-4 w-4 shrink-0 text-muted-foreground" aria-hidden="true" />
                )}
                <span className="truncate">{result.label}</span>
                {result.kind === 'kb' && (
                  <span className="ml-auto truncate font-mono text-xs text-muted-foreground">
                    {result.kbId}
                  </span>
                )}
                {result.kind === 'page' && (
                  <span className="ml-auto text-[10px] uppercase tracking-wide text-muted-foreground">
                    {t('pageBadge')}
                  </span>
                )}
                {result.kind === 'ask' && (
                  <ArrowRight className="ml-auto h-4 w-4 shrink-0 text-muted-foreground" aria-hidden="true" />
                )}
              </li>
            ))
          )}
        </ul>

        <div className="border-t border-border px-3 py-1.5 text-[10px] text-muted-foreground">
          <kbd className="font-medium">↑↓</kbd> {t('hintNavigate')} · <kbd className="font-medium">↵</kbd> {t('hintSelect')} ·{' '}
          <kbd className="font-medium">esc</kbd> {t('hintClose')}
        </div>
      </DialogContent>
    </Dialog>
  );
}
