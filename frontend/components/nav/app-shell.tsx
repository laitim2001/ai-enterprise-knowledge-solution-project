'use client';

/**
 * C09 unified application shell — W22 F1-pivot CSS-first rebuild per
 * CLAUDE.md §5.7 H7 (2026-05-17 user directive after the hand-translation
 * approach was rejected for typography + spacing drift).
 *
 * **Visual layer = mockup CSS direct adoption** (`references/design-mockups/
 * styles.css` → `frontend/app/styles-mockup.css`). This TSX file only owns:
 *   - React structure (App Router integration / state)
 *   - Data hooks (auth user, pathname → active route + breadcrumbs)
 *   - Behaviour (collapse toggle, Cmd/Ctrl+K binding, mobile drawer)
 *   - Class-name mapping to mockup CSS rules
 *
 * Class names mirror `references/design-mockups/ekp-shell.jsx` 1:1:
 *   .app .sidebar .sidebar-brand .brand-mark .brand-name .brand-tag
 *   .workspace-switcher .ws-avatar .ws-info
 *   .nav .nav-section-label .nav-item (data-active) .nav-tail
 *   .sidebar-footer .user-chip .user-chip-info .avatar
 *   .topbar .breadcrumbs .topbar-search .kbd .topbar-actions .topbar-divider
 *   .btn .btn-ghost .btn-icon .btn-sm
 *
 * Preserve (per W22 plan §0):
 *   - File path `frontend/components/nav/app-shell.tsx` + AppShellProps API
 *   - localStorage key 'ekp-sidebar-collapsed'
 *   - Cmd/Ctrl+K → <GlobalSearch> binding
 *   - Mobile <Sheet> drawer pattern (shadcn Radix-wrapped; BUG-002 test still holds)
 *   - <UserMenu> / <ThemeToggle> / <NotificationsMenu> / <GlobalSearch> integration
 *   - <DisabledAffordance> wraps every Tier 2 surface (W19 F5 27-affordance catalog)
 */

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Activity,
  ChevronDown,
  ChevronRight,
  Cpu,
  Database,
  Globe,
  Home,
  Layers,
  Link2,
  type LucideIcon,
  Menu,
  MessageCircle,
  MoreHorizontal,
  PanelLeft,
  Search,
  Send,
  Settings,
  Shield,
  Sparkles,
  Star,
  Users as UsersIcon,
  Zap,
} from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { useTranslations } from 'next-intl';

import { UserMenu } from '@/components/auth/user-menu';
import { GlobalSearch } from '@/components/nav/global-search';
import { LanguageToggle } from '@/components/nav/language-toggle';
import { NotificationsMenu } from '@/components/nav/notifications-menu';
import { ThemeToggle } from '@/components/nav/theme-toggle';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet';
import { RoleBadge } from '@/components/users/role-badge';
import { kbApi } from '@/lib/api/kb';
import { useRole } from '@/lib/hooks/use-role';
import { useCurrentUser } from '@/lib/providers/auth-provider';

const SIDEBAR_COLLAPSED_KEY = 'ekp-sidebar-collapsed';
const WORKSPACE_LABEL = 'Ricoh · RAPO';
const WORKSPACE_HOST = 'ekp-beta.ricoh.com';

interface NavLink {
  href: string;
  /** i18n key under the `Nav` message namespace (W103 F4 externalize) —
   *  resolved via `t(label)` in `SidebarLink` / breadcrumb render. */
  label: string;
  Icon: LucideIcon;
  /** Right-aligned tail label (e.g. KB count, "Cmd↵" shortcut). The Knowledge
   *  item's count is injected live in `SidebarNav` (CH-016), not stored here. */
  tail?: string;
}

/**
 * Icon mapping per mockup `references/design-mockups/ekp-data.jsx` NAV_ITEMS + manual
 * `IcX` → closest lucide-react equivalent (mechanical, NOT semantic guess):
 *   IcHome (house shape `M3 11 12 3l9 8`) → lucide `Home` (matches house outline)
 *   IcChat (round speech bubble w/ tail) → lucide `MessageCircle` (matches round bubble)
 *   IcDatabase (cylinder ellipses) → lucide `Database` (same shape)
 *   IcActivity (zigzag line) → lucide `Activity` (same shape)
 *   IcLayers (stacked diamonds) → lucide `Layers` (same shape)
 */
const WORKSPACE_NAV: NavLink[] = [
  { href: '/dashboard', label: 'dashboard', Icon: Home },
  { href: '/chat', label: 'chat', Icon: MessageCircle, tail: 'Cmd↵' },
  // tail = live active-KB count, injected in SidebarNav (CH-016). mockup
  // `ekp-data.jsx:233` ships a hard-coded `tail: "5"` placeholder (= its
  // MOCK_KBS length); we wire it to the real `kbApi.list()` count instead.
  { href: '/kb', label: 'knowledge', Icon: Database },
  // Integrations — top-level source-integration module (ADR-0071). Sits after
  // Knowledge in Workspace (mockup integration-import/10-integrations-landing.html
  // sidebar). Icon: chain-link SVG → lucide `Link2` (mechanical match).
  { href: '/integrations', label: 'integrations', Icon: Link2 },
  { href: '/eval', label: 'eval', Icon: Activity },
  { href: '/traces', label: 'traces', Icon: Layers },
];

const TOOLS_NAV: NavLink[] = [
  { href: '/settings', label: 'settings', Icon: Settings },
  { href: '/users', label: 'users', Icon: UsersIcon },
];

interface LabsItem {
  label: string;
  Icon: LucideIcon;
  reason: string;
  trigger: string;
}

/** Labs · Tier 2 — 8 items rendered visible-disabled per W19 F5 27-affordance
 * catalog + F5.4 Option C (prototype-only;`/labs/*` routes never ship). Each
 * wraps in `<DisabledAffordance>` so AT users hear the disabled state + the
 * Tier 2 boundary (CC10 H4) is held. */
const LABS_NAV: LabsItem[] = [
  { label: 'GraphRAG', Icon: Layers, reason: 'Knowledge-graph retrieval — Tier 2', trigger: 'graph-rag retrieval' },
  { label: 'Multi-Agent', Icon: Cpu, reason: 'Multi-agent orchestration — Tier 2', trigger: 'agent-orchestration' },
  { label: 'Multi-Language', Icon: Globe, reason: 'Multi-language (JP / ZH) — Tier 2', trigger: 'i18n machinery' },
  { label: 'Voice I/O', Icon: Send, reason: 'Voice input / output — Tier 2', trigger: 'voice-io machinery' },
  { label: 'Fine-Tune', Icon: Sparkles, reason: 'Custom LLM fine-tuning — Tier 2', trigger: 'fine-tuning pipeline' },
  { label: 'Workflow Builder', Icon: Zap, reason: 'No-code workflow builder — Tier 2', trigger: 'workflow plugin builder' },
  { label: 'Personalization', Icon: Star, reason: 'User-level personalization — Tier 2', trigger: 'personalization pipeline' },
  { label: 'Multi-Tenancy', Icon: Shield, reason: 'Multi-workspace tenancy — Tier 2', trigger: 'multi-tenancy' },
];

function isActiveRoute(pathname: string, href: string): boolean {
  return pathname === href || pathname.startsWith(`${href}/`);
}

/**
 * Map App Router pathname → breadcrumb labels. Dynamic segments (`/kb/[id]`,
 * `/traces/[traceId]`) surface a generic last-crumb until the per-page rebuild
 * wires the real name via context (F6 / F7 cluster scope).
 */
/**
 * Returns i18n keys under the `Breadcrumb` message namespace (W103 F4
 * externalize) — resolved via `t(key)` in `TopBar`. The unknown-route fallback
 * returns the capitalised raw segment (not a key); `TopBar` guards with
 * `t.has()` so it renders verbatim.
 */
function computeBreadcrumbs(pathname: string): string[] {
  const segments = pathname.split('/').filter(Boolean);
  if (segments.length === 0) return ['dashboard'];

  const [root, ...rest] = segments;

  if (root === 'dashboard') return ['dashboard'];
  if (root === 'chat') return ['chat'];
  if (root === 'eval') return ['eval'];
  if (root === 'settings') return ['settings'];
  if (root === 'users') return ['users'];

  if (root === 'kb') {
    if (rest.length === 0) return ['knowledge'];
    if (rest[0] === 'new') return ['knowledge', 'newKb'];
    const trail = ['knowledge', 'knowledgeBase'];
    if (rest[1] === 'upload') trail.push('upload');
    else if (rest[1] === 'docs') trail.push('document');
    return trail;
  }

  if (root === 'traces') {
    if (rest.length === 0) return ['traces'];
    return ['traces', 'traceDetail'];
  }

  if (root === 'integrations') {
    // /integrations → landing; /integrations/sharepoint/import → import wizard.
    if (rest[0] === 'sharepoint') return ['integrations', 'importFromSharePoint'];
    return ['integrations'];
  }

  return [root.charAt(0).toUpperCase() + root.slice(1)];
}

interface AppShellProps {
  children: React.ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  const t = useTranslations('Shell');
  const pathname = usePathname() ?? '/';

  // Sidebar collapsed state — persisted to localStorage; SSR-stable.
  const [collapsed, setCollapsed] = useState(false);
  useEffect(() => {
    if (window.localStorage.getItem(SIDEBAR_COLLAPSED_KEY) === '1') {
      setCollapsed(true);
    }
  }, []);
  const toggleCollapsed = useCallback(() => {
    setCollapsed((prev) => {
      const next = !prev;
      window.localStorage.setItem(SIDEBAR_COLLAPSED_KEY, next ? '1' : '0');
      return next;
    });
  }, []);

  // Mobile off-canvas drawer
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  // Cmd/Ctrl+K palette
  const [searchOpen, setSearchOpen] = useState(false);
  const handleOpenSearch = useCallback(() => setSearchOpen(true), []);
  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        handleOpenSearch();
      }
    }
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [handleOpenSearch]);

  const breadcrumbs = useMemo(() => computeBreadcrumbs(pathname), [pathname]);

  return (
    <div className="app" data-sidebar={collapsed ? 'collapsed' : 'expanded'}>
      <DesktopSidebar pathname={pathname} collapsed={collapsed} />
      <div className="main">
        <TopBar
          breadcrumbs={breadcrumbs}
          onToggleSidebar={toggleCollapsed}
          onOpenMobileNav={() => setMobileNavOpen(true)}
          onOpenSearch={handleOpenSearch}
        />
        {/* Per mockup pattern: each PageX self-wraps its content with
            `<div className="content"><div className="content-{wide|narrow}">`
            (per `references/design-mockups/ekp-page-*.jsx`). PageChat is the
            deliberate exception — full-bleed 3-pane grid filling
            `calc(100vh - var(--topbar-h))` per `ekp-page-chat.jsx:88-94`.
            AppShell stays layout-agnostic so each route can express its own
            content-box shape (H7 fidelity per CLAUDE.md §5.7). */}
        {children}
      </div>

      {/* Mobile off-canvas sidebar (< md) — shadcn Sheet pattern preserved.
          When the Sheet renders, the `<aside class="sidebar">` from mockup
          CSS is reused inside the Sheet body for IA consistency. */}
      <Sheet open={mobileNavOpen} onOpenChange={setMobileNavOpen}>
        <SheetContent side="left" className="w-[248px] p-0">
          <SheetHeader className="sr-only">
            <SheetTitle>{t('navigation')}</SheetTitle>
          </SheetHeader>
          <MobileSidebar pathname={pathname} onNavigate={() => setMobileNavOpen(false)} />
        </SheetContent>
      </Sheet>

      <GlobalSearch open={searchOpen} onOpenChange={setSearchOpen} />
    </div>
  );
}

// ── TopBar ─────────────────────────────────────────────────────────────────

interface TopBarProps {
  breadcrumbs: string[];
  onToggleSidebar: () => void;
  onOpenMobileNav: () => void;
  onOpenSearch: () => void;
}

function TopBar({ breadcrumbs, onToggleSidebar, onOpenMobileNav, onOpenSearch }: TopBarProps) {
  const t = useTranslations('TopBar');
  const tb = useTranslations('Breadcrumb');
  return (
    <header className="topbar">
      {/* Mobile hamburger (< md) — opens shadcn Sheet drawer. `!md:hidden` uses
          Tailwind's important variant so `display:none` wins specificity over
          `.btn { display: inline-flex }` from styles-mockup.css (which loads
          AFTER Tailwind base/utilities per layout.tsx import order). Same
          treatment for the desktop toggle's `!hidden md:!inline-flex` so the
          two buttons swap cleanly across the breakpoint without ever both
          appearing simultaneously (BUG-002 375px no-overflow stays held). */}
      <button
        className="btn btn-ghost btn-icon btn-sm md:!hidden"
        type="button"
        aria-label={t('openNav')}
        onClick={onOpenMobileNav}
      >
        <Menu size={15} />
      </button>

      {/* Desktop sidebar toggle (≥ md) — collapses to icon-only rail */}
      <button
        className="btn btn-ghost btn-icon btn-sm !hidden md:!inline-flex"
        type="button"
        aria-label={t('toggleSidebar')}
        title={t('toggleSidebar')}
        onClick={onToggleSidebar}
      >
        <PanelLeft size={15} />
      </button>

      <nav aria-label={tb('ariaLabel')} className="breadcrumbs">
        {breadcrumbs.map((b, i) => {
          const label = tb.has(b) ? tb(b) : b;
          return (
            <span key={`${i}-${b}`} className="contents">
              {i > 0 && (
                <span className="sep" aria-hidden="true">
                  <ChevronRight size={12} />
                </span>
              )}
              {i === breadcrumbs.length - 1 ? <b>{label}</b> : <span>{label}</span>}
            </span>
          );
        })}
      </nav>

      <button
        className="topbar-search"
        type="button"
        onClick={onOpenSearch}
        aria-label={t('searchAria')}
        title={t('searchTitle')}
      >
        <Search size={14} />
        <span style={{ flex: 1, textAlign: 'left' }}>{t('searchPlaceholder')}</span>
        <span className="kbd">⌘ K</span>
      </button>

      <div className="topbar-actions">
        {/* Language toggle — W103 F4 臨時通線 (was Tier 2 disabled affordance).
            正式 UI 形態 (Globe cycle vs dropdown) + H7 mockup 對齊 = F6. */}
        <LanguageToggle />

        <ThemeToggle />
        <NotificationsMenu />

        <div className="topbar-divider" aria-hidden="true" />

        <UserMenu />
      </div>
    </header>
  );
}

// ── Sidebar ────────────────────────────────────────────────────────────────

function DesktopSidebar({ pathname, collapsed }: { pathname: string; collapsed: boolean }) {
  return (
    <aside className="sidebar">
      <SidebarBrand collapsed={collapsed} />
      {!collapsed && <WorkspaceSwitcher />}
      <SidebarNav pathname={pathname} collapsed={collapsed} />
      <SidebarFooter collapsed={collapsed} />
    </aside>
  );
}

function MobileSidebar({ pathname, onNavigate }: { pathname: string; onNavigate: () => void }) {
  return (
    <aside className="sidebar">
      <SidebarBrand collapsed={false} />
      <WorkspaceSwitcher />
      <SidebarNav pathname={pathname} collapsed={false} onNavigate={onNavigate} />
      <SidebarFooter collapsed={false} />
    </aside>
  );
}

function SidebarBrand({ collapsed }: { collapsed: boolean }) {
  const t = useTranslations('Shell');
  return (
    <div className="sidebar-brand">
      <Link
        href="/dashboard"
        className="brand-mark"
        aria-label={t('brandAria')}
      >
        EKP
      </Link>
      {!collapsed && <span className="brand-name">{t('brandName')}</span>}
    </div>
  );
}

function WorkspaceSwitcher() {
  // Apply aria-disabled + title directly to the button so mockup `.workspace-switcher`
  // layout (margin 10px 12px 4px + flex full-width inside sidebar) is preserved.
  // Earlier wrap in <DisabledAffordance> broke the layout because its `<span
  // className="inline-flex">` wrapper collapsed the switcher to content-width.
  const t = useTranslations('Shell');
  const tier2Title = t('workspaceSwitcherTitle');
  return (
    <button
      type="button"
      disabled
      aria-disabled="true"
      aria-label={`${WORKSPACE_LABEL} — ${tier2Title}`}
      title={tier2Title}
      className="workspace-switcher"
      style={{ opacity: 0.7, cursor: 'default' }}
    >
      <span className="ws-avatar">R</span>
      <span className="ws-info">
        <b>{WORKSPACE_LABEL}</b>
        <span>{WORKSPACE_HOST}</span>
      </span>
      <ChevronDown size={13} className="muted" />
    </button>
  );
}

function SidebarNav({
  pathname,
  collapsed,
  onNavigate,
}: {
  pathname: string;
  collapsed: boolean;
  onNavigate?: () => void;
}) {
  // CH-016 — Knowledge nav tail = live active-KB count. Shares the exact
  // queryKey `['kb','list']` with the /kb list page, so this rides its cache
  // (no extra request) and reflects the RBAC-trimmed set the current user sees.
  // `archived` KBs are soft-deleted → excluded. tail stays absent until data is
  // ready (don't show a stale/placeholder number).
  const t = useTranslations('Nav');
  const { data: kbs } = useQuery({ queryKey: ['kb', 'list'], queryFn: kbApi.list });
  const activeKbCount = kbs?.filter((kb) => !kb.archived).length;

  return (
    <nav className="nav" aria-label={t('primaryAria')}>
      {!collapsed && <div className="nav-section-label">{t('sectionWorkspace')}</div>}
      {WORKSPACE_NAV.map((item) => (
        <SidebarLink
          key={item.href}
          item={
            item.href === '/kb' && activeKbCount !== undefined
              ? { ...item, tail: String(activeKbCount) }
              : item
          }
          active={isActiveRoute(pathname, item.href)}
          collapsed={collapsed}
          onNavigate={onNavigate}
        />
      ))}

      {!collapsed && (
        <>
          <div className="nav-section-label">{t('sectionTools')}</div>
          {TOOLS_NAV.map((item) => (
            <SidebarLink
              key={item.href}
              item={item}
              active={isActiveRoute(pathname, item.href)}
              collapsed={false}
              onNavigate={onNavigate}
            />
          ))}
          {/* Audit Log — Tier 2 disabled, mockup pattern `style={{ opacity: 0.5 }}`
              applied directly per `references/design-mockups/ekp-shell.jsx` line 296-300.
              No <DisabledAffordance> wrapper (it would break `.nav-item` flex layout). */}
          <button
            type="button"
            disabled
            aria-disabled="true"
            className="nav-item muted"
            title={t('auditLogTitle')}
            aria-label={t('auditLogAria')}
            style={{ opacity: 0.5, cursor: 'default' }}
          >
            <Shield className="icon" size={16} />
            <span>{t('auditLog')}</span>
            <span className="nav-tail">{t('soon')}</span>
          </button>

          <div className="nav-section-label" style={{ color: 'oklch(var(--accent))' }}>
            Labs · Tier 2
          </div>
          {LABS_NAV.map((item) => (
            <button
              key={item.label}
              type="button"
              disabled
              aria-disabled="true"
              className="nav-item"
              title={`${item.reason} · ${item.trigger}`}
              aria-label={`${item.label} (${item.reason})`}
              style={{ cursor: 'default' }}
            >
              <item.Icon className="icon" size={16} />
              <span>{item.label}</span>
              <span className="nav-tail" style={{ color: 'oklch(var(--accent))' }}>
                T2
              </span>
            </button>
          ))}
        </>
      )}
    </nav>
  );
}

function SidebarLink({
  item,
  active,
  collapsed,
  onNavigate,
}: {
  item: NavLink;
  active: boolean;
  collapsed: boolean;
  onNavigate?: () => void;
}) {
  const t = useTranslations('Nav');
  const { href, label, Icon, tail } = item;
  const labelText = t(label);
  return (
    <Link
      href={href}
      aria-current={active ? 'page' : undefined}
      onClick={onNavigate}
      className="nav-item"
      data-active={active ? 'true' : 'false'}
      title={collapsed ? labelText : undefined}
    >
      <Icon className="icon" size={16} />
      {!collapsed && (
        <>
          <span>{labelText}</span>
          {tail && <span className="nav-tail">{tail}</span>}
        </>
      )}
    </Link>
  );
}

function SidebarFooter({ collapsed }: { collapsed: boolean }) {
  const t = useTranslations('Shell');
  const user = useCurrentUser();
  const role = useRole();
  const displayName = user?.preferredUsername ?? t('signingIn');
  const localPart = displayName.split('@')[0] ?? displayName;
  const initials = (
    localPart
      .split(/[._-]/)
      .filter(Boolean)
      .map((t) => t[0]?.toUpperCase() ?? '')
      .join('')
      .slice(0, 2) || 'U'
  );

  if (collapsed) {
    return (
      <div className="sidebar-footer">
        <div className="avatar" title={localPart}>
          <span>{initials}</span>
        </div>
      </div>
    );
  }

  return (
    <div className="sidebar-footer">
      <div className="user-chip">
        <div className="avatar">
          <span>{initials}</span>
        </div>
        <div className="user-chip-info">
          <b>{localPart}</b>
          {/* W88 P0 F3 — real RBAC role chip (was hard-coded). RoleBadge =
              mockup-grounded four-tier visual; hidden while /auth/me loads. */}
          {role && <RoleBadge role={role} />}
        </div>
      </div>
      <button
        type="button"
        className="btn btn-ghost btn-icon btn-sm"
        title={t('accountActions')}
        aria-label={t('moreAccountActions')}
      >
        <MoreHorizontal size={14} />
      </button>
    </div>
  );
}
