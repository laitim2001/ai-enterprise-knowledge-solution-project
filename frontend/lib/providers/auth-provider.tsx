'use client';

/**
 * C11 — auth state context (W7 D2 F1.4 login flow UI).
 *
 * Zustand store wrapping `lib/auth/index.ts` single switching point. Mock
 * mode (W7) auto-logs-in on mount; real MSAL (W8 D4 onwards) waits for the
 * user to click the login button which redirects to the Entra ID hosted page.
 */

import { create } from 'zustand';
import { useEffect } from 'react';

import { authMode, getCurrentUser, login, logout, refresh } from '@/lib/auth';
import type { AuthenticatedUser } from '@/lib/auth';
import { initMsal, getMsalUser } from '@/lib/auth/msal_provider';

type AuthState = {
  user: AuthenticatedUser | null;
  status: 'idle' | 'loading' | 'authenticated' | 'error';
  error: string | null;
  signIn: () => Promise<void>;
  signOut: () => Promise<void>;
  setUserFromCache: (user: AuthenticatedUser) => void;
};

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  status: 'idle',
  error: null,

  signIn: async () => {
    set({ status: 'loading', error: null });
    try {
      const user = await login();
      set({ user, status: 'authenticated', error: null });
    } catch (e) {
      set({
        status: 'error',
        error: e instanceof Error ? e.message : String(e),
      });
    }
  },

  signOut: async () => {
    await logout();
    set({ user: null, status: 'idle', error: null });
  },

  setUserFromCache: (user: AuthenticatedUser) =>
    set({ user, status: 'authenticated', error: null }),
}));

// Refresh slightly before Microsoft default 1-hour expiry so the cached
// bearer never goes stale mid-request. 50min = 3000s.
const REFRESH_INTERVAL_MS = 50 * 60 * 1000;

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const { signIn, setUserFromCache, status } = useAuthStore();

  useEffect(() => {
    if (authMode === 'mock') {
      if (status === 'idle') {
        // W7 mock mode: auto-sign-in so dev sessions don't have to click a
        // button before each Admin / Chat view loads.
        void signIn();
      }
      return;
    }

    // W8 D3 LIVE msal-react path. handleRedirectPromise + active-account
    // restore from sessionStorage cache; no auto-redirect to Entra ID hosted
    // login — user must click sign-in CTA so we never get into an infinite
    // loop on startup if cred wiring is broken.
    let cancelled = false;
    void (async () => {
      try {
        await initMsal();
        if (cancelled) return;
        try {
          const user = getMsalUser();
          setUserFromCache(user);
        } catch {
          // Not authenticated yet — UserMenu shows sign-in CTA.
        }
      } catch (e) {
        if (!cancelled) {
          // initMsal failure (config missing / network) surfaces via store
          // error state so ErrorBoundary can pick it up downstream.
          useAuthStore.setState({
            status: 'error',
            error: e instanceof Error ? e.message : String(e),
          });
        }
      }
    })();

    // Periodic silent refresh while the tab is open — acquireTokenSilent
    // uses the refresh token kept in sessionStorage cache. Failure is
    // recovered by next request triggering 401 → frontend redirects to
    // login (handled at api-client.ts ApiError boundary).
    const interval = setInterval(() => {
      void refresh().catch(() => {
        // Silent — recoverable on next user action.
      });
    }, REFRESH_INTERVAL_MS);

    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [signIn, setUserFromCache, status]);

  // Surface the current user via the store directly; consumers select what
  // they need rather than reading from an extra Context layer.
  return <>{children}</>;
}

export function useCurrentUser(): AuthenticatedUser | null {
  return useAuthStore((s) => s.user);
}

export function useAuthStatus(): AuthState['status'] {
  return useAuthStore((s) => s.status);
}

export { authMode, getCurrentUser };
