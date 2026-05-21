'use client';

/**
 * `useRole()` — the authenticated caller's RBAC role (W24c F9 per ADR-0027).
 *
 * Fetches `GET /auth/me`, where the backend resolves the role server-side
 * (W24c F3 — three paths: self-register / mock / real-MSAL app-role claim).
 * Returns `null` while loading or when unauthenticated. The `/users` page
 * uses this for role-gated view rendering.
 */

import { useQuery } from '@tanstack/react-query';

import type { EkpRoleKey } from '@/lib/api/admin';
import { usersApi } from '@/lib/api/users';

/** The caller's RBAC role, or `null` while the `/auth/me` fetch is in flight. */
export function useRole(): EkpRoleKey | null {
  const query = useQuery({
    queryKey: ['auth', 'me'],
    queryFn: () => usersApi.getMe(),
    staleTime: 5 * 60 * 1000,
  });
  return query.data?.role ?? null;
}
