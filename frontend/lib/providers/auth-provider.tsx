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

import { authMode, getCurrentUser, login, logout } from '@/lib/auth';
import type { AuthenticatedUser } from '@/lib/auth';

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

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const { signIn, status } = useAuthStore();

  useEffect(() => {
    if (authMode !== 'mock' || status !== 'idle') return;
    // W7 mock mode: auto-sign-in so dev sessions don't have to click a button
    // before each Admin / Chat view loads. W8 D4 LIVE switch: this branch is
    // dead because authMode === 'msal' and the user must click signIn.
    void signIn();
  }, [signIn, status]);

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
