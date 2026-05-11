'use client';

/**
 * C09/C10 unified application shell — W18 F1 (per ADR-0024 + architecture.md v6 §5.0).
 *
 * Generalizes the W12-W15 `<AdminShell>` into the single chrome that wraps
 * **all authenticated views** (Dashboard / Chat / Knowledge Bases / Eval / Traces):
 *   - persistent top bar  : app name → /dashboard + global-search trigger (Cmd/Ctrl+K)
 *                           + disabled language toggle (i18n is Tier 2 §11) + ThemeToggle + UserMenu
 *   - collapsible left sidebar : the 5 functional modules; a "focus mode" toggle hides it
 *                                (persisted to localStorage) for chat-immersive use
 *   - main content slot
 *   - responsive : the sidebar collapses to an off-canvas Sheet < md
 *
 * Wired into `app/(app)/layout.tsx` by W18 F2. W18 F6 mounted `<GlobalSearch>` here —
 * the top-bar search trigger + the Cmd/Ctrl+K listener both open the quick-jump palette.
 *
 * 100% design-token consumption (Tailwind classes wired to globals.css :root/.dark) —
 * no hardcoded `oklch()` colour arbitrary-values (W15 milestone preserved).
 */

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useCallback, useEffect, useState } from 'react';
import {
  Activity,
  Database,
  FlaskConical,
  Languages,
  LayoutDashboard,
  Menu,
  MessageSquare,
  PanelLeftClose,
  PanelLeftOpen,
  Search,
} from 'lucide-react';

import { UserMenu } from '@/components/auth/user-menu';
import { GlobalSearch } from '@/components/nav/global-search';
import { ThemeToggle } from '@/components/nav/theme-toggle';
import { Button } from '@/components/ui/button';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet';
import { cn } from '@/lib/utils';

const APP_NAME = 'EKP';

/** localStorage key for the "focus mode" / sidebar-collapsed preference. */
const SIDEBAR_COLLAPSED_KEY = 'ekp-sidebar-collapsed';

interface NavItem {
  href: string;
  label: string;
  Icon: typeof LayoutDashboard;
}

/** The 5 functional modules — flat list (sectioned headers are an optional W18 polish detail). */
const NAV_ITEMS: NavItem[] = [
  { href: '/dashboard', label: 'Dashboard', Icon: LayoutDashboard },
  { href: '/chat', label: 'Chat', Icon: MessageSquare },
  { href: '/kb', label: 'Knowledge Bases', Icon: Database },
  { href: '/eval', label: 'Eval Console', Icon: FlaskConical },
  { href: '/traces', label: 'Traces', Icon: Activity },
];

function isActiveRoute(pathname: string, href: string): boolean {
  return pathname === href || pathname.startsWith(`${href}/`);
}

interface AppShellProps {
  children: React.ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  const pathname = usePathname() ?? '/';

  // "Focus mode" — collapses the desktop sidebar; persisted to localStorage.
  // Initialised to `false` for SSR-stable hydration; the stored value is read on mount.
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

  // Mobile off-canvas nav (controlled — the trigger lives in the top bar, outside <SheetTrigger>).
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  // Global search command palette (W18 F6) — opened by the top-bar trigger and by Cmd/Ctrl+K.
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

  return (
    <div className="flex min-h-screen flex-col">
      {/* Persistent top bar */}
      <header className="sticky top-0 z-30 flex h-14 items-center gap-2 border-b border-border bg-background px-3 sm:px-4">
        {/* Mobile: hamburger → off-canvas sidebar */}
        <Button
          variant="ghost"
          size="icon"
          aria-label="Open navigation"
          aria-expanded={mobileNavOpen}
          className="h-9 w-9 md:hidden"
          onClick={() => setMobileNavOpen(true)}
        >
          <Menu className="h-5 w-5" />
        </Button>

        {/* Desktop: focus-mode (collapse sidebar) toggle */}
        <Button
          variant="ghost"
          size="icon"
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          aria-pressed={collapsed}
          className="hidden h-9 w-9 md:inline-flex"
          onClick={toggleCollapsed}
        >
          {collapsed ? (
            <PanelLeftOpen className="h-5 w-5" />
          ) : (
            <PanelLeftClose className="h-5 w-5" />
          )}
        </Button>

        {/* App name → /dashboard (no marketing tagline — internal tool) */}
        <Link
          href="/dashboard"
          className="shrink-0 text-base font-semibold tracking-tight"
        >
          {APP_NAME}
        </Link>

        {/* Global search trigger (centre). Opens <GlobalSearch> (W18 F6); Cmd/Ctrl+K bound above. */}
        <button
          type="button"
          onClick={handleOpenSearch}
          aria-label="Search (Ctrl+K)"
          className="mx-auto flex h-9 w-full max-w-md items-center gap-2 rounded-md border border-border bg-muted/40 px-3 text-sm text-muted-foreground transition-colors hover:bg-muted"
        >
          <Search className="h-4 w-4 shrink-0" />
          <span className="truncate">Search knowledge bases, traces…</span>
          <kbd className="ml-auto hidden shrink-0 rounded border border-border bg-background px-1.5 text-[10px] font-medium text-muted-foreground sm:inline-block">
            Ctrl K
          </kbd>
        </button>

        {/* Right cluster */}
        <div className="flex shrink-0 items-center gap-1">
          {/* Language toggle — disabled affordance; i18n (JP/ZH) is Tier 2 per architecture.md §11. */}
          <Button
            variant="ghost"
            size="icon"
            disabled
            aria-label="Language (multi-language coming soon)"
            title="Multi-language (JP / ZH) — coming in a later tier"
            className="hidden h-9 w-9 sm:inline-flex"
          >
            <Languages className="h-5 w-5" />
          </Button>
          <ThemeToggle />
          <UserMenu />
        </div>
      </header>

      <div className="flex flex-1">
        {/* Desktop sidebar — hidden when focus mode (collapsed) is on */}
        {!collapsed && (
          <aside className="sticky top-14 hidden h-[calc(100dvh-3.5rem)] w-56 shrink-0 overflow-y-auto border-r border-border bg-muted/40 p-3 md:block">
            <NavLinks pathname={pathname} />
          </aside>
        )}

        {/* Main content */}
        <main className="min-w-0 flex-1 overflow-x-hidden p-4 md:p-8">
          {children}
        </main>
      </div>

      {/* Mobile off-canvas sidebar */}
      <Sheet open={mobileNavOpen} onOpenChange={setMobileNavOpen}>
        <SheetContent side="left" className="w-64 p-4">
          <SheetHeader>
            <SheetTitle className="text-lg">{APP_NAME}</SheetTitle>
          </SheetHeader>
          <NavLinks
            pathname={pathname}
            className="mt-4"
            onNavigate={() => setMobileNavOpen(false)}
          />
        </SheetContent>
      </Sheet>

      {/* Global search command palette (Cmd/Ctrl+K) */}
      <GlobalSearch open={searchOpen} onOpenChange={setSearchOpen} />
    </div>
  );
}

function NavLinks({
  pathname,
  className,
  onNavigate,
}: {
  pathname: string;
  className?: string;
  onNavigate?: () => void;
}) {
  return (
    <nav className={cn('flex flex-col gap-1', className)} aria-label="Primary">
      {NAV_ITEMS.map(({ href, label, Icon }) => {
        const active = isActiveRoute(pathname, href);
        return (
          <Link
            key={href}
            href={href}
            aria-current={active ? 'page' : undefined}
            onClick={onNavigate}
            className={cn(
              'flex min-h-[40px] items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors',
              active
                ? 'bg-muted font-medium text-foreground'
                : 'text-muted-foreground hover:bg-muted hover:text-foreground',
            )}
          >
            <Icon className="h-4 w-4 shrink-0" aria-hidden="true" />
            <span className="truncate">{label}</span>
          </Link>
        );
      })}
    </nav>
  );
}
