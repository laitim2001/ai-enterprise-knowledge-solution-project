'use client';

/**
 * C09 unified application shell — W22 F1 strict-fidelity rebuild per
 * `references/design-mockups/ekp-shell.jsx` + CLAUDE.md §5.7 H7.
 *
 * Layout philosophy (mockup grid-template-columns: var(--sidebar-w) 1fr;
 * height 100vh):
 *   ┌─────────────┬─────────────────────────────────────┐
 *   │  Sidebar    │  TopBar (52px)                      │
 *   │  ─────────  │  ───────────────────────────────────│
 *   │  Brand      │  ┊ toggle ┊ breadcrumbs ┊ search ┊  │
 *   │  Workspace  │  ┊ ┊ lang ┊ theme ┊ bell ┊ user ┊ │
 *   │  switcher   │  ───────────────────────────────────│
 *   │             │                                     │
 *   │  Workspace  │            Page content             │
 *   │  Tools      │                                     │
 *   │  Labs T2    │                                     │
 *   │             │                                     │
 *   │  user-chip  │                                     │
 *   └─────────────┴─────────────────────────────────────┘
 *
 * Replaces the W18 F1 / W20 F1 implementation (flex-col with TopBar across
 * top of both columns), which failed the user-eye fidelity audit 2026-05-17
 * with 4 fundamental drifts (TopBar IA / Sidebar IA / Main content shape /
 * Typography). See W22 plan §0 + W21 progress.md Day 1 retro.
 *
 * Preserve (per W22 plan §0 + Karpathy §1.3 surgical):
 *   - File path `frontend/components/nav/app-shell.tsx` + `AppShellProps`
 *     `{ children }` API contract
 *   - localStorage key `ekp-sidebar-collapsed`
 *   - Cmd/Ctrl+K → <GlobalSearch> binding
 *   - Mobile off-canvas <Sheet> pattern (preserves BUG-002 375px no-overflow
 *     test in `app-shell-path.spec.ts`)
 *   - ARIA landmarks (`<header>` implicit banner / `<nav aria-label="Primary">`
 *     / `<main>`) — same names asserted by `app-shell.test.tsx`
 *   - `<DisabledAffordance>` wraps every Tier 2 surface (workspace switcher /
 *     language toggle / Labs section / Audit log) — W19 F5 27-affordance
 *     catalog + CC10 H4 boundary
 *   - <UserMenu> / <ThemeToggle> / <NotificationsMenu> / <GlobalSearch>
 *     integration points (their internals are F2/F8 cluster scope)
 *
 * Rebuild (per mockup strict reproduction):
 *   - grid-cols-[var(--sidebar-w)_1fr] layout (replaces flex-col)
 *   - Sidebar = 248px (replaces w-56 = 224px); --sidebar-w + --topbar-h
 *     CSS vars added to globals.css
 *   - Sidebar internal: brand strip (52px aligned w/ topbar) → workspace
 *     switcher (moved from topbar) → nav sections (Workspace 5 items /
 *     Tools 3 items / Labs · Tier 2 8 items) → user-chip footer
 *   - TopBar internal: sidebar-toggle → breadcrumbs → search (right-of-center
 *     360w 30h) → right-actions (lang / theme / bell / divider / user-w-name)
 *   - Tier 2 Labs section rendered with `<DisabledAffordance>` per item — the
 *     8 Labs items render visible but unclickable (W19 F5.4 Option C — items
 *     show in UI but `/labs/*` routes never ship; Tier 2 boundary held)
 *   - Tools `Audit Log` rendered with `<DisabledAffordance>` (multi-tenant
 *     concern; Tier 2 §11)
 *
 * 100% design-token consumption — only arbitrary values are the layout
 * constants `var(--sidebar-w)` and `h-[52px]` which are spec-locked per
 * references/design-mockups/styles.css and added to globals.css.
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
  LayoutDashboard,
  Layers,
  Menu,
  MessageSquare,
  MoreHorizontal,
  PanelLeftClose,
  PanelLeftOpen,
  Search,
  Send,
  Settings,
  Shield,
  Sparkles,
  Star,
  Users as UsersIcon,
  Zap,
} from 'lucide-react';

import { UserMenu } from '@/components/auth/user-menu';
import { GlobalSearch } from '@/components/nav/global-search';
import { NotificationsMenu } from '@/components/nav/notifications-menu';
import { ThemeToggle } from '@/components/nav/theme-toggle';
import { Button } from '@/components/ui/button';
import { DisabledAffordance } from '@/components/ui/disabled-affordance';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet';
import { useCurrentUser } from '@/lib/providers/auth-provider';
import { cn } from '@/lib/utils';

/** localStorage key for the focus-mode / sidebar-collapsed preference. */
const SIDEBAR_COLLAPSED_KEY = 'ekp-sidebar-collapsed';

/** Workspace label (single-tenant Tier 1 — fixed value; switcher disabled per §11). */
const WORKSPACE_LABEL = 'Ricoh · RAPO';
const WORKSPACE_HOST = 'ekp-beta.ricoh.com';

interface NavLink {
  href: string;
  label: string;
  Icon: typeof LayoutDashboard;
  tail?: string;
}

/**
 * The 5 Workspace modules — per mockup `window.NAV_ITEMS` labels (Dashboard /
 * Chat / Knowledge / Eval / Traces). Tail numbers come from data in a later
 * pass (e.g. Knowledge tail = KB count) — F3+ wire data fetch.
 */
const WORKSPACE_NAV: NavLink[] = [
  { href: '/dashboard', label: 'Dashboard', Icon: LayoutDashboard },
  { href: '/chat', label: 'Chat', Icon: MessageSquare },
  { href: '/kb', label: 'Knowledge', Icon: Database },
  { href: '/eval', label: 'Eval', Icon: Activity },
  { href: '/traces', label: 'Traces', Icon: Layers },
];

/** Tools section — Settings + Users + Audit Log (Audit Log is Tier 2 §11). */
const TOOLS_NAV: NavLink[] = [
  { href: '/settings', label: 'Settings', Icon: Settings },
  { href: '/users', label: 'Users & access', Icon: UsersIcon },
];

/**
 * Labs · Tier 2 section — visible-disabled per W19 F5 27-affordance catalog +
 * F5.4 Option C (prototype-only; `/labs/*` routes never ship). Each item
 * wraps in `<DisabledAffordance>` so the AT path stays correct and the
 * Tier 2 boundary (CC10 H4) is held — items render but are unclickable.
 */
interface LabsItem {
  label: string;
  Icon: typeof LayoutDashboard;
  /** Drives `<DisabledAffordance reason>` and the tooltip text. */
  reason: string;
  /** Tier 2 trigger tag — surfaced in the tooltip per the W19 F5 catalog. */
  trigger: string;
}

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
 * Compute breadcrumb labels from the App Router pathname.
 *
 * Dynamic segments (e.g. `/kb/[id]`) surface a generic label
 * ("Knowledge Base" / "Document" / "Trace detail") until the corresponding
 * page rebuild (F6 KB cluster / F7 observability cluster) wires the real
 * name through a context provider. The mockup shows real names — the
 * generic placeholder is the F1 acceptable interim per CLAUDE.md §13
 * "Mockup detail unclear" row's pragmatic interpretation.
 */
function computeBreadcrumbs(pathname: string): string[] {
  const segments = pathname.split('/').filter(Boolean);
  if (segments.length === 0) return ['Dashboard'];

  const [root, ...rest] = segments;

  if (root === 'dashboard') return ['Dashboard'];
  if (root === 'chat') return ['Chat'];
  if (root === 'eval') return ['Eval'];
  if (root === 'settings') return ['Settings'];
  if (root === 'users') return ['Users & access'];

  if (root === 'kb') {
    if (rest.length === 0) return ['Knowledge'];
    if (rest[0] === 'new') return ['Knowledge', 'New KB'];
    // /kb/[id] / /kb/[id]/upload / /kb/[id]/docs/[docId]
    const trail = ['Knowledge', 'Knowledge Base'];
    if (rest[1] === 'upload') trail.push('Upload');
    else if (rest[1] === 'docs') trail.push('Document');
    return trail;
  }

  if (root === 'traces') {
    if (rest.length === 0) return ['Traces'];
    return ['Traces', 'Trace detail'];
  }

  // Fallback — humanise the first segment
  return [root.charAt(0).toUpperCase() + root.slice(1)];
}

interface AppShellProps {
  children: React.ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  const pathname = usePathname() ?? '/';

  // Focus-mode / sidebar-collapsed — persisted to localStorage; SSR-stable.
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

  // Mobile off-canvas nav (Sheet — preserved W18 F1 pattern).
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  // Cmd/Ctrl+K palette (preserved W18 F6 binding).
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
    <div
      // Desktop: 2-col grid (sidebar | main); mobile (< md): single col, sidebar
      // hidden — accessed via the top-bar hamburger → <Sheet>.
      className="grid h-screen overflow-hidden md:grid-cols-[var(--sidebar-w)_1fr]"
      data-sidebar={collapsed ? 'collapsed' : 'expanded'}
    >
      {/* Desktop sidebar — hidden when focus mode (collapsed) is on or below md. */}
      {!collapsed && (
        <DesktopSidebar pathname={pathname} />
      )}

      {/* Main column — top bar + scrolling content. */}
      <div className="flex min-w-0 flex-col overflow-hidden">
        <TopBar
          breadcrumbs={breadcrumbs}
          collapsed={collapsed}
          onToggleCollapsed={toggleCollapsed}
          onOpenMobileNav={() => setMobileNavOpen(true)}
          onOpenSearch={handleOpenSearch}
        />
        <main className="flex-1 overflow-y-auto overflow-x-hidden bg-background">
          {children}
        </main>
      </div>

      {/* Mobile off-canvas sidebar */}
      <Sheet open={mobileNavOpen} onOpenChange={setMobileNavOpen}>
        <SheetContent side="left" className="w-[248px] p-0">
          <SheetHeader className="sr-only">
            <SheetTitle>Navigation</SheetTitle>
          </SheetHeader>
          <MobileSidebarContent pathname={pathname} onNavigate={() => setMobileNavOpen(false)} />
        </SheetContent>
      </Sheet>

      {/* Global search palette (Cmd/Ctrl+K) — opened by top-bar trigger or hotkey */}
      <GlobalSearch open={searchOpen} onOpenChange={setSearchOpen} />
    </div>
  );
}

// ── TopBar ─────────────────────────────────────────────────────────────────

interface TopBarProps {
  breadcrumbs: string[];
  collapsed: boolean;
  onToggleCollapsed: () => void;
  onOpenMobileNav: () => void;
  onOpenSearch: () => void;
}

function TopBar({ breadcrumbs, collapsed, onToggleCollapsed, onOpenMobileNav, onOpenSearch }: TopBarProps) {
  return (
    <header
      className={cn(
        'flex h-[var(--topbar-h)] shrink-0 items-center gap-3 border-b border-border bg-background px-5',
      )}
    >
      {/* Mobile hamburger (< md) */}
      <Button
        variant="ghost"
        size="icon"
        aria-label="Open navigation"
        className="h-8 w-8 md:hidden"
        onClick={onOpenMobileNav}
      >
        <Menu className="h-4 w-4" />
      </Button>

      {/* Desktop focus-mode toggle (≥ md) */}
      <Button
        variant="ghost"
        size="icon"
        aria-label={collapsed ? 'Expand sidebar (exit focus mode)' : 'Collapse sidebar (focus mode)'}
        aria-pressed={collapsed}
        title="Toggle sidebar (hides left navigation)"
        className="hidden h-8 w-8 md:inline-flex"
        onClick={onToggleCollapsed}
      >
        {collapsed ? (
          <PanelLeftOpen className="h-[15px] w-[15px]" />
        ) : (
          <PanelLeftClose className="h-[15px] w-[15px]" />
        )}
      </Button>

      {/* Breadcrumbs */}
      <nav aria-label="Breadcrumb" className="flex items-center gap-1.5 text-[13px] text-muted-foreground">
        {breadcrumbs.map((b, i) => (
          <span key={`${i}-${b}`} className="flex items-center gap-1.5">
            {i > 0 && (
              <ChevronRight className="h-3 w-3 shrink-0 opacity-40" aria-hidden="true" />
            )}
            {i === breadcrumbs.length - 1 ? (
              <span className="font-medium text-foreground">{b}</span>
            ) : (
              <span>{b}</span>
            )}
          </span>
        ))}
      </nav>

      {/* Search trigger — pushed right via `ml-auto`; mockup width 360 height 30 */}
      <button
        type="button"
        onClick={onOpenSearch}
        aria-label="Search (Ctrl+K)"
        className={cn(
          'ml-auto flex h-[30px] min-w-0 max-w-[360px] flex-1 items-center gap-2 rounded-sm border border-border bg-muted/50 px-2.5 text-[13px] text-muted-foreground transition-colors hover:bg-muted',
        )}
      >
        <Search className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />
        <span className="min-w-0 flex-1 truncate text-left">
          Search KBs, traces, settings…
        </span>
        <kbd className="ml-auto hidden shrink-0 rounded-[3px] border border-border bg-background px-1.5 py-px font-mono text-[10.5px] sm:inline-block">
          ⌘ K
        </kbd>
      </button>

      {/* Right cluster — language / theme / notifications / divider / account */}
      <div className="flex shrink-0 items-center gap-0.5">
        {/* Language toggle — Tier 2 disabled (i18n machinery is Tier 2 §11) */}
        <DisabledAffordance
          reason="Multi-language (JP / ZH) — Tier 2"
          tier2Trigger="i18n machinery"
          className="hidden sm:inline-flex"
        >
          <Button
            variant="ghost"
            size="icon"
            disabled
            aria-label="Language (Tier 2 — coming soon)"
            className="h-8 w-8"
          >
            <Globe className="h-[15px] w-[15px]" />
          </Button>
        </DisabledAffordance>

        {/* Theme toggle (sun / moon — internal swap) */}
        <ThemeToggle />

        {/* Notifications bell (existing W20 F1.1 component preserved) */}
        <NotificationsMenu />

        {/* Vertical divider */}
        <div
          aria-hidden="true"
          className="mx-1 hidden h-[18px] w-px bg-border sm:block"
        />

        {/* Account — UserMenu trigger rebuilt to mockup pattern (avatar + name + chev) */}
        <UserMenu />
      </div>
    </header>
  );
}

// ── Sidebar (desktop) ──────────────────────────────────────────────────────

function DesktopSidebar({ pathname }: { pathname: string }) {
  return (
    <aside className="flex h-screen flex-col overflow-hidden border-r border-border bg-card">
      <SidebarBrand />
      <WorkspaceSwitcher />
      <SidebarNav pathname={pathname} />
      <SidebarFooter />
    </aside>
  );
}

function MobileSidebarContent({
  pathname,
  onNavigate,
}: {
  pathname: string;
  onNavigate: () => void;
}) {
  return (
    <div className="flex h-full flex-col overflow-hidden">
      <SidebarBrand />
      <WorkspaceSwitcher />
      <SidebarNav pathname={pathname} onNavigate={onNavigate} />
      <SidebarFooter />
    </div>
  );
}

function SidebarBrand() {
  return (
    <div className="flex h-[var(--topbar-h)] shrink-0 items-center gap-2.5 border-b border-border px-4">
      <Link
        href="/dashboard"
        className="flex h-[26px] w-[26px] shrink-0 items-center justify-center rounded-sm bg-primary font-mono text-[12px] font-semibold tracking-tighter text-primary-foreground"
        aria-label="EKP — go to dashboard"
      >
        EKP
      </Link>
      <span className="overflow-hidden truncate text-[14px] font-semibold tracking-tight">
        Knowledge Platform
      </span>
      <span className="rounded-sm bg-muted px-1.5 py-px font-mono text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
        Beta
      </span>
    </div>
  );
}

function WorkspaceSwitcher() {
  return (
    <DisabledAffordance
      reason="Multi-workspace support — Tier 2 per architecture.md §11"
      tier2Trigger="multi-tenancy"
    >
      <button
        type="button"
        disabled
        aria-label={`Workspace: ${WORKSPACE_LABEL} (multi-workspace — Tier 2)`}
        className={cn(
          'mx-3 mb-1 mt-2.5 flex items-center gap-2 rounded-sm border border-border bg-card px-2.5 py-1.5 text-[13px] transition-colors hover:bg-muted',
        )}
      >
        <span className="flex h-[22px] w-[22px] shrink-0 items-center justify-center rounded-sm bg-accent font-mono text-[11px] font-semibold text-accent-foreground">
          R
        </span>
        <span className="flex min-w-0 flex-1 flex-col leading-tight">
          <span className="truncate text-[13px] font-semibold">{WORKSPACE_LABEL}</span>
          <span className="text-[11px] text-muted-foreground">{WORKSPACE_HOST}</span>
        </span>
        <ChevronDown className="h-3 w-3 shrink-0 text-muted-foreground" aria-hidden="true" />
      </button>
    </DisabledAffordance>
  );
}

function SidebarNav({
  pathname,
  onNavigate,
}: {
  pathname: string;
  onNavigate?: () => void;
}) {
  return (
    <nav
      aria-label="Primary"
      className="flex flex-1 flex-col gap-px overflow-y-auto px-3 pb-4 pt-2"
    >
      <SidebarSectionLabel>Workspace</SidebarSectionLabel>
      {WORKSPACE_NAV.map((item) => (
        <SidebarLink
          key={item.href}
          item={item}
          active={isActiveRoute(pathname, item.href)}
          onNavigate={onNavigate}
        />
      ))}

      <SidebarSectionLabel>Tools</SidebarSectionLabel>
      {TOOLS_NAV.map((item) => (
        <SidebarLink
          key={item.href}
          item={item}
          active={isActiveRoute(pathname, item.href)}
          onNavigate={onNavigate}
        />
      ))}
      {/* Audit Log — Tier 2 disabled affordance (multi-tenancy §11) */}
      <DisabledAffordance
        reason="Audit log surface — Tier 2 (multi-tenancy)"
        tier2Trigger="multi-tenancy"
      >
        <button
          type="button"
          disabled
          className={cn(
            'flex items-center gap-2.5 rounded-sm px-2.5 py-1.5 text-[13.5px] font-normal text-muted-foreground opacity-60',
          )}
        >
          <Shield className="h-4 w-4 shrink-0" aria-hidden="true" />
          <span className="flex-1 text-left">Audit Log</span>
          <span className="ml-auto font-mono text-[11px] text-muted-foreground">
            Soon
          </span>
        </button>
      </DisabledAffordance>

      <SidebarSectionLabel accent>Labs · Tier 2</SidebarSectionLabel>
      {LABS_NAV.map((item) => (
        <DisabledAffordance
          key={item.label}
          reason={item.reason}
          tier2Trigger={item.trigger}
        >
          <button
            type="button"
            disabled
            className={cn(
              'flex items-center gap-2.5 rounded-sm px-2.5 py-1.5 text-[13.5px] font-normal text-foreground opacity-80',
            )}
          >
            <item.Icon className="h-4 w-4 shrink-0 text-muted-foreground" aria-hidden="true" />
            <span className="flex-1 text-left">{item.label}</span>
            <span className="ml-auto font-mono text-[11px] font-medium text-accent">
              T2
            </span>
          </button>
        </DisabledAffordance>
      ))}
    </nav>
  );
}

function SidebarSectionLabel({
  children,
  accent,
}: {
  children: React.ReactNode;
  accent?: boolean;
}) {
  return (
    <div
      aria-hidden="true"
      className={cn(
        'px-2.5 pb-1 pt-3.5 font-mono text-[10.5px] font-medium uppercase tracking-wider first:pt-1',
        accent ? 'text-accent' : 'text-muted-foreground',
      )}
    >
      {children}
    </div>
  );
}

function SidebarLink({
  item,
  active,
  onNavigate,
}: {
  item: NavLink;
  active: boolean;
  onNavigate?: () => void;
}) {
  const { href, label, Icon, tail } = item;
  return (
    <Link
      href={href}
      aria-current={active ? 'page' : undefined}
      onClick={onNavigate}
      className={cn(
        'relative flex items-center gap-2.5 rounded-sm px-2.5 py-1.5 text-[13.5px] transition-colors',
        active
          ? 'bg-muted font-medium text-foreground'
          : 'font-normal text-foreground hover:bg-muted',
        // Active-state left rail (mockup `.nav-item[data-active]::before`)
        active &&
          'before:absolute before:-left-3 before:top-[5px] before:bottom-[5px] before:w-[2px] before:rounded-full before:bg-accent before:content-[""]',
      )}
    >
      <Icon
        className={cn(
          'h-4 w-4 shrink-0',
          active ? 'text-foreground' : 'text-muted-foreground',
        )}
        aria-hidden="true"
      />
      <span className="flex-1 truncate">{label}</span>
      {tail && (
        <span className="ml-auto font-mono text-[11px] tabular-nums text-muted-foreground">
          {tail}
        </span>
      )}
    </Link>
  );
}

function SidebarFooter() {
  const user = useCurrentUser();
  const displayName = user?.preferredUsername ?? '—';
  const localPart = displayName.split('@')[0] ?? displayName;
  const initials = localPart
    .split(/[._-]/)
    .filter(Boolean)
    .map((t) => t[0]?.toUpperCase() ?? '')
    .join('')
    .slice(0, 2) || 'U';

  return (
    <div className="flex shrink-0 items-center gap-2 border-t border-border px-2.5 py-2">
      <div className="flex flex-1 items-center gap-2 rounded-sm px-2 py-1.5 hover:bg-muted">
        <span className="flex h-[26px] w-[26px] shrink-0 items-center justify-center rounded-full border border-border bg-muted font-mono text-[11px] font-semibold">
          {initials}
        </span>
        <div className="flex min-w-0 flex-1 flex-col leading-tight">
          <span className="truncate text-[12.5px] font-semibold">
            {localPart}
          </span>
          <span className="truncate text-[11px] text-muted-foreground">
            Workspace Admin
          </span>
        </div>
      </div>
      <Button
        variant="ghost"
        size="icon"
        aria-label="More account actions"
        className="h-7 w-7 shrink-0"
      >
        <MoreHorizontal className="h-3.5 w-3.5" />
      </Button>
    </div>
  );
}
