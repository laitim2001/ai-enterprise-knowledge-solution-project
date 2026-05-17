'use client';

/**
 * C09 topbar notifications menu — W22 F1-pivot direct-copy from mockup
 * `references/design-mockups/ekp-shell.jsx:136-189` NotificationsMenu
 * (per CLAUDE.md §5.7 H7 strict fidelity 2026-05-18 user audit — rebuild
 * not patch when fundamental drift).
 *
 * Structure mirrors mockup `<PopMenu width=380>`:
 *   - Header: "Notifications" + "X unread" subtitle + "Mark all read" right
 *   - Body: 5 notification rows; per-row 26x26 icon box (kind-coloured) +
 *           title + body + mono timestamp + 6x6 unread accent dot; unread
 *           rows tint with `oklch(var(--accent) / 0.04)` background
 *   - Footer: "Alert rules in Dashboard → System health" left +
 *             "Notification settings →" right
 *
 * shadcn `<DropdownMenu>` Radix wrapper preserved for accessibility (keyboard
 * trap + focus return + portal positioning). Inner content uses mockup CSS
 * classes + inline styles 1:1 (per memory `feedback_design_fidelity.md`
 * rule #2 — direct-copy mockup JSX inside shadcn shell shell).
 *
 * Backend `GET /notifications` is OPTIONAL per W19 F2 item 21 — Wave A ships
 * with `MOCK_NOTIFICATIONS` fallback; when the endpoint 404s the mock data
 * stays visible so the topbar surface is consistent across dev / Beta states.
 *
 * Icon mapping per memory rule #3 (mechanical SVG-path match, NOT semantic
 * guess; mockup `references/design-mockups/icons.jsx`):
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
import Link from 'next/link';
import { useMemo, useState } from 'react';

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
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

export function NotificationsMenu() {
  const [locallyReadIds, setLocallyReadIds] = useState<Set<string>>(new Set());
  const [open, setOpen] = useState(false);

  const query = useQuery<NotificationsResponse>({
    queryKey: ['notifications'],
    queryFn: () => apiClient.get<NotificationsResponse>('/notifications'),
    // Endpoint is OPTIONAL per W19 F2 item 21 — don't hammer it on failure.
    retry: false,
    // Light polling so the badge stays warm without being a websocket.
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

  return (
    <DropdownMenu open={open} onOpenChange={setOpen}>
      <DropdownMenuTrigger asChild>
        <button
          type="button"
          className="btn btn-ghost btn-icon btn-sm"
          aria-label={
            unreadCount > 0
              ? `Notifications — ${unreadCount} unread`
              : 'Notifications'
          }
          title="Notifications"
          style={{ position: 'relative' }}
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
      </DropdownMenuTrigger>
      <DropdownMenuContent
        align="end"
        sideOffset={4}
        className="topbar-popmenu p-0"
        style={{ width: 380 }}
      >
        {/* Header — direct copy mockup ekp-shell.jsx lines 153-160 */}
        <div
          style={{
            padding: '10px 14px',
            borderBottom: '1px solid oklch(var(--border))',
            display: 'flex',
            alignItems: 'center',
          }}
        >
          <div>
            <div style={{ fontSize: 13, fontWeight: 600 }}>Notifications</div>
            <div className="text-xs muted">
              {unreadCount === 0
                ? 'All caught up'
                : `${unreadCount} unread`}
            </div>
          </div>
          <div className="spacer" />
          <button
            type="button"
            className="btn btn-ghost btn-xs"
            onClick={handleMarkAllRead}
            disabled={unreadCount === 0}
          >
            Mark all read
          </button>
        </div>

        {/* Body — direct copy mockup ekp-shell.jsx lines 161-183 */}
        <div style={{ maxHeight: 420, overflowY: 'auto' }}>
          {items.length === 0 ? (
            <div className="text-xs muted" style={{ padding: '24px 14px', textAlign: 'center' }}>
              No notifications yet.
            </div>
          ) : (
            items.map((n) => {
              const isUnread = n.unread && !locallyReadIds.has(n.id);
              const { Icon, colorVar } = ICON_FOR[n.kind];
              return (
                <Link
                  key={n.id}
                  href={n.href}
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
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
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

        {/* Footer — direct copy mockup ekp-shell.jsx lines 184-188 */}
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
            Alert rules in Dashboard → System health
          </span>
          <div className="spacer" />
          <Link
            href="/settings"
            onClick={() => setOpen(false)}
            className="btn btn-ghost btn-xs"
          >
            Notification settings →
          </Link>
        </div>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
