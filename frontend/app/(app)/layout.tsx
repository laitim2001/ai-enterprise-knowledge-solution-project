/**
 * Application-shell layout — the single layout for all authenticated views
 * (W18 F2, per ADR-0024 + architecture.md v6 §5.0).
 *
 * Every route physically under app/(app)/ — /dashboard, /chat, /kb/**, /eval,
 * /traces/**, /settings — renders inside this chain:
 *   AuthProvider → QueryProvider → LoginGate → AppShell → the page.
 * Replaces the W12-W15 per-section layouts (app/admin/layout.tsx,
 * app/eval/layout.tsx, app/debug/layout.tsx — folded here). Their removal +
 * the page moves into app/(app)/ land with W18 F3 (this F2 commit adds the new
 * layout + the login-gate; the layout is inert until F3 moves the pages in).
 * The root app/layout.tsx keeps only ThemeProvider + Toaster so the auth pages
 * (/login, /register, /verify) and the `/` redirect get no app chrome.
 *
 * Server component (like the layouts it replaces) — AuthProvider / QueryProvider /
 * LoginGate / AppShell are the client islands.
 */

import { AuthProvider } from '@/lib/providers/auth-provider';
import { QueryProvider } from '@/lib/providers/query-provider';
import { LoginGate } from '@/components/auth/login-gate';
import { AppShell } from '@/components/nav/app-shell';

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <AuthProvider>
      <QueryProvider>
        <LoginGate>
          <AppShell>{children}</AppShell>
        </LoginGate>
      </QueryProvider>
    </AuthProvider>
  );
}
