'use client';

/**
 * C11 — login-gate for the app/(app)/ route group (W18 F2, per ADR-0024 + architecture.md v6 §5.0).
 *
 * Wraps every authenticated view. Behaviour by auth mode:
 *  - mock dev (NEXT_PUBLIC_AUTH_MOCK / FEATURE_AUTH_MOCK): AuthProvider auto-signs-in on
 *    mount, so the gate never gates — it passes its children straight through. The visible
 *    "未登入 → /login" only appears in real MSAL / production builds (documented in ADR-0024).
 *  - real MSAL: while auth is resolving (idle / loading) → a minimal splash; on error →
 *    the error + a /login link; once authenticated → children. We do NOT auto-redirect
 *    to /login — matching the existing AuthProvider design that avoids an infinite loop if
 *    cred wiring is broken (the user clicks the sign-in CTA; /login is outside (app)/, so it
 *    is not behind this gate).
 *  - cookie session (CH-013, mock off + SSO off): AuthProvider hydrates identity from the
 *    httpOnly ekp_session cookie via GET /auth/me on mount. Same gate UI as real MSAL —
 *    splash while loading, splash + sign-in link when unauthenticated (a 401 resolves to
 *    `idle`, not `error`). The root `/` redirect (CH-013 §2.4) routes authenticated users
 *    to /dashboard and others to /login, so this in-(app) splash is only briefly seen on a
 *    direct deep-link before login.
 *    // TODO(W16): once MSAL cred wiring is live (Q11 Track A), tighten this to a
 *    // router.replace('/login') on the definitively-unauthenticated state.
 */

import { useTranslations } from 'next-intl';
import Link from 'next/link';
import { Loader2 } from 'lucide-react';

import { authMode, useAuthHydrated, useAuthStatus } from '@/lib/providers/auth-provider';

export function LoginGate({ children }: { children: React.ReactNode }) {
  const status = useAuthStatus();
  const hydrated = useAuthHydrated();
  const t = useTranslations('LoginGate');

  // Mock dev mode auto-signs-in → never gate. Authenticated → pass through.
  if (authMode === 'mock' || status === 'authenticated') {
    return <>{children}</>;
  }

  // Still resolving identity (cookie hydration via GET /auth/me, or MSAL init).
  // The user may well be signed in — show a neutral spinner WITHOUT the sign-in
  // CTA so we never flash "Sign in to continue" at an already-authenticated user
  // (BUG-038). BUG-039: the store STARTS at `idle` before the hydration effect
  // runs, so `!hydrated` gets the same neutral spinner — the CTA below is only
  // for the post-hydration, definitively-unauthenticated states.
  if (!hydrated || status === 'loading') {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-4 p-6 text-center">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" aria-hidden="true" />
      </div>
    );
  }

  // Definitively unauthenticated (idle after a 401) or sign-in error — splash + a
  // sign-in link (no auto-redirect; see docstring).
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4 p-6 text-center">
      {status === 'error' ? (
        <p className="text-sm text-destructive">{t('signInFailed')}</p>
      ) : (
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" aria-hidden="true" />
      )}
      <Link
        href="/login"
        className="text-sm font-medium underline-offset-4 hover:underline"
      >
        {t('signInToContinue')}
      </Link>
    </div>
  );
}
