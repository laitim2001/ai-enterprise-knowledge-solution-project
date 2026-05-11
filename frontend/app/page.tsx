/**
 * Root route (`/`) — redirect only (W18 F7, per ADR-0024 + architecture.md v6 §5.9).
 *
 * The V7 marketing-style Landing page was REMOVED per ADR-0024 (EKP is an internal
 * tool — there's no public funnel; the old hero / feature cards / how-it-works /
 * footer were deleted, not preserved). `/` now just sends you to `/login`.
 *
 * Server Component — a plain `redirect('/login')`. The "already-authenticated →
 * /dashboard" shortcut isn't done here on purpose: in mock-auth dev there's no
 * server-readable session, and in real MSAL the `(app)/` login-gate + MSAL's own
 * session handling re-route you once you reach any `/app` route — so `/ → /login`
 * is the honest Tier 1 behaviour. `brand-panel.tsx` (the auth-page brand splash)
 * is kept; nothing else imported the deleted Landing markup.
 */

import { redirect } from 'next/navigation';

export default function RootPage() {
  redirect('/login');
}
