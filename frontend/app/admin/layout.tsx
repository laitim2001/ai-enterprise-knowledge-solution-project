/**
 * Admin layout (per architecture.md §5.3 sidebar pattern; layout reference
 * Dify Image 4 — code NOT copied, EKP design tokens only per CLAUDE.md §7).
 *
 * Provides shared sidebar navigation across /admin/* routes + TanStack Query
 * client provider for KB API queries.
 */

import Link from 'next/link';
import { QueryProvider } from '@/lib/providers/query-provider';
import { AuthProvider } from '@/lib/providers/auth-provider';
import { UserMenu } from '@/components/auth/user-menu';

const NAV_ITEMS = [
  { href: '/admin', label: 'Overview' },
  { href: '/admin/kb', label: 'Knowledge Bases' },
  { href: '/eval', label: 'Eval Console' },
];

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  return (
    <AuthProvider>
      <QueryProvider>
        <div className="flex min-h-screen">
          <aside className="w-56 border-r border-[oklch(0.92_0_0)] bg-[oklch(0.98_0_0)] p-4">
            <Link href="/admin" className="mb-6 block text-lg font-semibold">
              EKP Admin
            </Link>
            <nav className="flex flex-col gap-1">
              {NAV_ITEMS.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className="rounded px-3 py-2 text-sm hover:bg-[oklch(0.94_0_0)]"
                >
                  {item.label}
                </Link>
              ))}
            </nav>
          </aside>
          <main className="flex flex-1 flex-col">
            <header className="flex items-center justify-end border-b border-[oklch(0.92_0_0)] bg-[oklch(0.99_0_0)] px-8 py-3">
              <UserMenu />
            </header>
            <div className="flex-1 p-8">{children}</div>
          </main>
        </div>
      </QueryProvider>
    </AuthProvider>
  );
}
