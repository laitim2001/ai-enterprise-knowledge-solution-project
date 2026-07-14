'use client';

/**
 * C09 topbar notifications menu — W22 F1-pivot direct-copy from mockup
 * `references/design-mockups/ekp-shell.jsx:86-189` PopMenu + NotificationsMenu
 * (per CLAUDE.md §5.7 H7 strict fidelity 2026-05-18 user audit).
 *
 * Implementation note — Radix DropdownMenu replaced with mockup-faithful
 * portal pattern (2026-05-18 fidelity fix #2). The original Radix wrapper
 * applied Floating UI positioning via transform on an ancestor wrapper,
 * which made `position: fixed` inside the popover anchor to that
 * transformed ancestor instead of the viewport — defeating the mockup's
 * `right: 66` viewport-anchored gutter pattern. Mockup `ekp-shell.jsx:14-22`
 * uses a plain `document.addEventListener('click', ...)` + `.closest()`
 * exclusion check on `[data-popmenu-trigger]` for click-outside; we mirror
 * that exact pattern so the popover's `position: fixed; right: 66` resolves
 * against the actual viewport.
 *
 * Structure mirrors mockup `<PopMenu width={380} right={66}>`:
 *   - Header: "Notifications" + "X unread" subtitle + "Mark all read" right
 *   - Body: 5 notification rows; per-row 26x26 icon box (kind-coloured) +
 *           title + body + mono timestamp + 6x6 unread accent dot; unread
 *           rows tint with `oklch(var(--accent) / 0.04)` background
 *   - Footer: "Alert rules in Dashboard → System health" left +
 *             "Notification settings →" right
 *
 * Backend `GET /notifications` is OPTIONAL per W19 F2 item 21 — Wave A ships
 * with `MOCK_NOTIFICATIONS` fallback; when the endpoint 404s the mock data
 * stays visible so the topbar surface is consistent across dev / Beta states.
 *
 * Icon mapping per memory rule #3 (mechanical SVG-path match):
 *   IcCheck (`m5 12 5 5L20 7`)          → lucide `Check`
 *   IcZap (`M13 2 4 14h7l-1 8 9-12h-7z`) → lucide `Zap`
 *   IcAlert (triangle + bang)            → lucide `AlertTriangle`
 *   IcX (`M18 6 6 18M6 6l12 12`)         → lucide `X`
 *   IcActivity (pulse line)              → lucide `Activity`
 */

import { useQuery } from '@tanstack/react-query';
import {
  Activity,
  AlertTriangle,
  Bell,
  Check,
  X as XIcon,
  Zap,
  type LucideIcon,
} from 'lucide-react';
import { useTranslations } from 'next-intl';
import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import { createPortal } from 'react-dom';

import { apiClient } from '@/lib/api-client';

type NotificationKind =
  | 'indexing-complete'
  | 'eval-pass'
  | 'crag-spike'
  | 'indexing-failed'
  | 'shootout';

export interface NotificationItem {
  id: string;
  kind: NotificationKind;
  title: string;
  body: string;
  /** Human-readable relative time (mockup data shape — keep as-is until real backend lands). */
  at: string;
  unread: boolean;
  /** Where the row navigates on click. */
  href: string;
}

interface NotificationsResponse {
  items: NotificationItem[];
}

/** Static fallback shown when `GET /notifications` 404s (Wave A — endpoint optional).
 *  Data mirrors mockup `ekp-shell.jsx:137-143` 5 sample notifications. */
const MOCK_NOTIFICATIONS: NotificationItem[] = [
  {
    id: 'mock-1',
    kind: 'indexing-complete',
    title: 'Customer Service SOP indexing finished',
    body: '62% → 100% in 14 min · 87 docs · 2,104 chunks',
    at: '2 min ago',
    unread: true,
    href: '/kb/customer-service-sop',
  },
  {
    id: 'mock-2',
    kind: 'eval-pass',
    title: 'Nightly eval pass · R@5 +2.4pp',
    body: 'Drive Manuals · 184-q eval set · all 4 metrics above target',
    at: '1h ago',
    unread: true,
    href: '/eval',
  },
  {
    id: 'mock-3',
    kind: 'crag-spike',
    title: 'CRAG trigger rate climbed to 28%',
    body: 'Last 60 min · approaching 30% alert threshold',
    at: '3h ago',
    unread: false,
    href: '/traces',
  },
  {
    id: 'mock-4',
    kind: 'indexing-failed',
    title: '2 documents failed to parse',
    body: 'Advanced Reporting (PPTX) + Legacy Vendor Contracts (scanned PDF)',
    at: 'Today 08:22',
    unread: false,
    href: '/kb/drive-manuals',
  },
  {
    id: 'mock-5',
    kind: 'shootout',
    title: 'Reranker shootout completed',
    body: 'Cohere v4.0-pro retained · v3.5 Δ faith −11.76pp',
    at: 'Yesterday',
    unread: false,
    href: '/eval',
  },
];

/** Mockup `iconFor` (lines 144-149): kind → lucide icon + colour token. */
const ICON_FOR: Record<NotificationKind, { Icon: LucideIcon; colorVar: string }> = {
  'indexing-complete': { Icon: Check, colorVar: 'oklch(var(--success))' },
  'eval-pass': { Icon: Zap, colorVar: 'oklch(var(--accent))' },
  'crag-spike': { Icon: AlertTriangle, colorVar: 'oklch(var(--warning))' },
  'indexing-failed': { Icon: XIcon, colorVar: 'oklch(var(--destructive))' },
  shootout: { Icon: Activity, colorVar: '' },
};

/** Fallback when a fetched notification carries an unknown `kind` — defensive
 *  against backend schema drift (W22 F8.7 fix per W22 D11 — pre-W20 F1 test mock
 *  uses `{id, title, read}` shape lacking `kind`, surfacing destructure crash). */
const ICON_FOR_FALLBACK = { Icon: Activity, colorVar: 'oklch(var(--muted-foreground))' };

export function NotificationsMenu() {
  const t = useTranslations('Notifications');
  const [locallyReadIds, setLocallyReadIds] = useState<Set<string>>(new Set());
  const [open, setOpen] = useState(false);
  const [mounted, setMounted] = useState(false);

  // Avoid portal hydration mismatch — only render after mount on the client.
  useEffect(() => {
    setMounted(true);
  }, []);

  // Click-outside + Escape close — mockup `ekp-shell.jsx:14-22` pattern.
  useEffect(() => {
    if (!open) return;
    function handleClick(e: MouseEvent) {
      const target = e.target as Element | null;
      if (!target) return;
      if (
        !target.closest('.topbar-popmenu') &&
        !target.closest('[data-popmenu-trigger="notifications"]')
      ) {
        setOpen(false);
      }
    }
    function handleKey(e: KeyboardEvent) {
      if (e.key === 'Escape') setOpen(false);
    }
    document.addEventListener('click', handleClick);
    document.addEventListener('keydown', handleKey);
    return () => {
      document.removeEventListener('click', handleClick);
      document.removeEventListener('keydown', handleKey);
    };
  }, [open]);

  const query = useQuery<NotificationsResponse>({
    queryKey: ['notifications'],
    queryFn: () => apiClient.get<NotificationsResponse>('/notifications'),
    retry: false,
    refetchInterval: 60_000,
  });

  const items = useMemo<NotificationItem[]>(() => {
    if (query.data?.items) return query.data.items;
    return MOCK_NOTIFICATIONS;
  }, [query.data]);

  const unreadCount = useMemo(
    () => items.filter((it) => it.unread && !locallyReadIds.has(it.id)).length,
    [items, locallyReadIds],
  );

  const handleMarkAllRead = () => {
    setLocallyReadIds(new Set(items.map((it) => it.id)));
  };

  const popover = (
    <div
      className="topbar-popmenu"
      role="menu"
      aria-label={t('title')}
      style={{
        // Mockup `ekp-shell.jsx:86-101` PopMenu — viewport-anchored absolute
        // positioning. With createPortal to document.body, `position: fixed`
        // resolves against viewport (no transformed ancestor).
        position: 'fixed',
        top: 'calc(var(--topbar-h) - 4px)',
        right: 66,
        width: 380,
        background: 'oklch(var(--popover))',
        border: '1px solid oklch(var(--border))',
        borderRadius: 'var(--radius-md)',
        boxShadow: 'var(--shadow-lg)',
        zIndex: 50,
        overflow: 'hidden',
        animation: 'pop-in 0.14s var(--ease)',
      }}
    >
      {/* Header — mockup ekp-shell.jsx lines 153-160 */}
      <div
        style={{
          padding: '10px 14px',
          borderBottom: '1px solid oklch(var(--border))',
          display: 'flex',
          alignItems: 'center',
        }}
      >
        <div>
          <div style={{ fontSize: 13, fontWeight: 600 }}>{t('title')}</div>
          <div className="text-xs muted">
            {unreadCount === 0 ? t('allCaughtUp') : t('unread', { count: unreadCount })}
          </div>
        </div>
        <div className="spacer" />
        <button
          type="button"
          className="btn btn-ghost btn-xs"
          onClick={handleMarkAllRead}
          disabled={unreadCount === 0}
        >
          {t('markAllRead')}
        </button>
      </div>

      {/* Body — mockup ekp-shell.jsx lines 161-183 */}
      <div style={{ maxHeight: 420, overflowY: 'auto' }}>
        {items.length === 0 ? (
          <div
            className="text-xs muted"
            style={{ padding: '24px 14px', textAlign: 'center' }}
          >
            {t('empty')}
          </div>
        ) : (
          items.map((n) => {
            const isUnread = n.unread && !locallyReadIds.has(n.id);
            const { Icon, colorVar } = ICON_FOR[n.kind] ?? ICON_FOR_FALLBACK;
            return (
              <Link
                key={n.id}
                href={n.href ?? '#'}
                onClick={() => setOpen(false)}
                style={{
                  display: 'flex',
                  gap: 10,
                  padding: '10px 14px',
                  borderBottom: '1px solid oklch(var(--border))',
                  background: isUnread
                    ? 'oklch(var(--accent) / 0.04)'
                    : 'transparent',
                  textDecoration: 'none',
                  color: 'inherit',
                }}
              >
                <div
                  style={{
                    width: 26,
                    height: 26,
                    borderRadius: 'var(--radius-sm)',
                    background: 'oklch(var(--muted))',
                    display: 'grid',
                    placeItems: 'center',
                    flexShrink: 0,
                  }}
                >
                  <Icon
                    size={13}
                    className={colorVar ? undefined : 'muted'}
                    style={colorVar ? { color: colorVar } : undefined}
                  />
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 6,
                    }}
                  >
                    <span
                      style={{
                        fontSize: 12.5,
                        fontWeight: 500,
                        flex: 1,
                        minWidth: 0,
                        lineHeight: 1.35,
                      }}
                    >
                      {n.title}
                    </span>
                    {isUnread && (
                      <span
                        aria-hidden="true"
                        style={{
                          width: 6,
                          height: 6,
                          borderRadius: '50%',
                          background: 'oklch(var(--accent))',
                          flexShrink: 0,
                        }}
                      />
                    )}
                  </div>
                  <div
                    className="text-xs muted"
                    style={{ marginTop: 2, lineHeight: 1.4 }}
                  >
                    {n.body}
                  </div>
                  <div
                    className="text-xs muted mono"
                    style={{ marginTop: 4 }}
                  >
                    {n.at}
                  </div>
                </div>
              </Link>
            );
          })
        )}
      </div>

      {/* Footer — mockup ekp-shell.jsx lines 184-188 */}
      <div
        style={{
          padding: '8px 14px',
          borderTop: '1px solid oklch(var(--border))',
          background: 'oklch(var(--muted) / 0.3)',
          display: 'flex',
          alignItems: 'center',
        }}
      >
        <span className="text-xs muted">
          {t('footerAlert')}
        </span>
        <div className="spacer" />
        <Link
          href="/settings"
          onClick={() => setOpen(false)}
          className="btn btn-ghost btn-xs"
        >
          {t('footerSettings')}
        </Link>
      </div>
    </div>
  );

  return (
    <>
      <button
        type="button"
        className="btn btn-ghost btn-icon btn-sm"
        data-popmenu-trigger="notifications"
        aria-label={
          unreadCount > 0
            ? t('triggerUnread', { count: unreadCount })
            : t('triggerLabel')
        }
        aria-haspopup="menu"
        aria-expanded={open}
        title={t('triggerLabel')}
        style={{ position: 'relative' }}
        onClick={() => setOpen((o) => !o)}
      >
        <Bell size={15} />
        {unreadCount > 0 && (
          <span
            aria-hidden="true"
            style={{
              position: 'absolute',
              top: 4,
              right: 4,
              width: 7,
              height: 7,
              borderRadius: '50%',
              background: 'oklch(var(--accent))',
              border: '1.5px solid oklch(var(--background))',
            }}
          />
        )}
      </button>
      {mounted && open && createPortal(popover, document.body)}
    </>
  );
}
