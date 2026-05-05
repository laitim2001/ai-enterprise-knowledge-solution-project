/**
 * Admin layout (per architecture.md §5.3 sidebar pattern; layout reference
 * Dify Image 4 — code NOT copied, EKP design tokens only per CLAUDE.md §7).
 *
 * Provides shared sidebar navigation across /admin/* routes + TanStack Query
 * client provider for KB API queries.
 */

import { QueryProvider } from '@/lib/providers/query-provider';
import { AuthProvider } from '@/lib/providers/auth-provider';
import { AdminShell } from '@/components/nav/admin-shell';

/**
 * Admin layout (per architecture.md §5.3 sidebar pattern; layout reference
 * Dify Image 4 — code NOT copied, EKP design tokens only per CLAUDE.md §7).
 *
 * W7 D4 F5.2: shell extracted into client component `<AdminShell>` so the
 * hamburger nav state can live alongside the rest of the admin layout. This
 * server component keeps the providers (Auth + Query) where they belong.
 */
export default function AdminLayout({ children }: { children: React.ReactNode }) {
  return (
    <AuthProvider>
      <QueryProvider>
        <AdminShell>{children}</AdminShell>
      </QueryProvider>
    </AuthProvider>
  );
}
