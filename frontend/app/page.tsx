/**
 * Root route (`/`) — redirect only (W18 F7, per ADR-0024 + architecture.md v6 §5.9;
 * CH-013 §2.4 adds the authenticated shortcut).
 *
 * The V7 marketing-style Landing page was REMOVED per ADR-0024 (EKP is an internal
 * tool — there's no public funnel; the old hero / feature cards / how-it-works /
 * footer were deleted, not preserved). `/` is now a pure redirect.
 *
 * CH-013 §2.4 — route by session presence: if the httpOnly `ekp_session` cookie
 * (ADR-0022 self-register session) is present, send the user to /dashboard;
 * otherwise to /login. We only check presence, not validity — an expired/invalid
 * cookie still lands on /dashboard, where the login-gate + GET /auth/me hydration
 * handle the resulting 401. This replaces the old unconditional `/ → /login` so a
 * signed-in user re-visiting localhost:3001 is no longer bounced back to login.
 * `brand-panel.tsx` (the auth-page brand splash) is kept; nothing else imported
 * the deleted Landing markup.
 */

import { cookies } from 'next/headers';
import { redirect } from 'next/navigation';

export default function RootPage() {
  const hasSession = cookies().get('ekp_session') != null;
  redirect(hasSession ? '/dashboard' : '/login');
}
