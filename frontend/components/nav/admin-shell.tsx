'use client';

/**
 * C09 — W7 D4 F5.2 mobile-aware admin shell.
 *
 * Sidebar collapses on `sm` (< 640px) into an off-canvas drawer toggled by a
 * hamburger button in the header. `md` and up keeps the sticky 224px sidebar
 * (W2 D5 baseline preserved for desktop).
 *
 * Touch-friendly: nav links 40px tap target, header bar 48px tall on mobile.
 */

import Link from 'next/link';
import { useState } from 'react';

import { UserMenu } from '@/components/auth/user-menu';

const NAV_ITEMS = [
  { href: '/admin', label: 'Overview' },
  { href: '/admin/kb', label: 'Knowledge Bases' },
  { href: '/eval', label: 'Eval Console' },
];

interface AdminShellProps {
  children: React.ReactNode;
}

export function AdminShell({ children }: AdminShellProps) {
  const [navOpen, setNavOpen] = useState(false);
  const closeNav = () => setNavOpen(false);

  return (
    <div className="flex min-h-screen flex-col md:flex-row">
      <header className="flex items-center justify-between border-b border-[oklch(0.92_0_0)] bg-[oklch(0.99_0_0)] px-4 py-2 md:hidden">
        <button
          type="button"
          onClick={() => setNavOpen((v) => !v)}
          className="flex h-10 w-10 items-center justify-center rounded hover:bg-[oklch(0.94_0_0)]"
          aria-label={navOpen ? 'Close navigation' : 'Open navigation'}
          aria-expanded={navOpen}
        >
          {/* Inline hamburger icon — avoids extra dep; lucide-react already
              installed but keeping markup-only for snapshot stability. */}
          <span className="block h-0.5 w-5 bg-current shadow-[0_-6px_0_currentColor,0_6px_0_currentColor]" />
        </button>
        <Link href="/admin" className="text-base font-semibold">
          EKP Admin
        </Link>
        <UserMenu />
      </header>

      {navOpen ? (
        <button
          type="button"
          aria-label="Close navigation overlay"
          onClick={closeNav}
          className="fixed inset-0 z-30 bg-[oklch(0_0_0/0.4)] md:hidden"
        />
      ) : null}

      <aside
        className={`${
          navOpen ? 'translate-x-0' : '-translate-x-full'
        } fixed inset-y-0 left-0 z-40 w-64 transform border-r border-[oklch(0.92_0_0)] bg-[oklch(0.98_0_0)] p-4 transition-transform duration-200 md:static md:w-56 md:translate-x-0 md:transition-none`}
      >
        <Link
          href="/admin"
          onClick={closeNav}
          className="mb-6 block text-lg font-semibold"
        >
          EKP Admin
        </Link>
        <nav className="flex flex-col gap-1">
          {NAV_ITEMS.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              onClick={closeNav}
              className="flex min-h-[40px] items-center rounded px-3 py-2 text-sm hover:bg-[oklch(0.94_0_0)]"
            >
              {item.label}
            </Link>
          ))}
        </nav>
      </aside>

      <main className="flex min-w-0 flex-1 flex-col">
        <header className="hidden items-center justify-end border-b border-[oklch(0.92_0_0)] bg-[oklch(0.99_0_0)] px-8 py-3 md:flex">
          <UserMenu />
        </header>
        <div className="flex-1 p-4 md:p-8">{children}</div>
      </main>
    </div>
  );
}
