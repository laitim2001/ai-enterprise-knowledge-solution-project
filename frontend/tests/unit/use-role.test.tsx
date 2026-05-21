/**
 * Unit tests — `useRole()` hook (W24c F9.1 per ADR-0027; F11 dedicated coverage).
 *
 * The `/users` page gates whole-page rendering on this hook, so its contract
 * matters: it must return `null` while the `GET /auth/me` fetch is in flight
 * (the gate shows a loading state, never a flash of access-denied) and `null`
 * again when the fetch fails (unauthenticated), and the resolved `EkpRoleKey`
 * once `/auth/me` lands. The `/users` page tests (`users-page.test.tsx`)
 * exercise the hook indirectly via role-gating; this file isolates the hook's
 * three-state contract directly via `renderHook`.
 */

import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { ReactNode } from 'react';

// `useRole()` reads `usersApi.getMe()` — a controllable spy drives each state.
// `vi.hoisted` so the spy exists before the hoisted `vi.mock` factory runs.
const { getMe } = vi.hoisted(() => ({ getMe: vi.fn() }));

vi.mock('@/lib/api/users', () => ({
  usersApi: { getMe },
}));

import { useRole } from '@/lib/hooks/use-role';

function wrapper({ children }: { children: ReactNode }) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}

describe('useRole() — RBAC role hook (W24c F11)', () => {
  beforeEach(() => {
    getMe.mockReset();
  });

  it('returns null while the /auth/me fetch is in flight', () => {
    // A never-resolving promise keeps the query pending across the assertion.
    getMe.mockReturnValue(new Promise(() => {}));
    const { result } = renderHook(() => useRole(), { wrapper });
    expect(result.current).toBeNull();
  });

  it('returns the resolved role once /auth/me lands', async () => {
    getMe.mockResolvedValue({
      oid: 'o1',
      tid: 't1',
      preferred_username: 'chris.lai@ricoh.com',
      role: 'admin',
      is_mock: true,
    });
    const { result } = renderHook(() => useRole(), { wrapper });
    expect(result.current).toBeNull(); // still loading on first render
    await waitFor(() => expect(result.current).toBe('admin'));
  });

  it('returns null when /auth/me fails (unauthenticated)', async () => {
    getMe.mockRejectedValue(new Error('401 Unauthorized'));
    const { result } = renderHook(() => useRole(), { wrapper });
    await waitFor(() => expect(getMe).toHaveBeenCalledTimes(1));
    // A failed fetch never populates `data` — the hook stays null, no throw.
    expect(result.current).toBeNull();
  });
});
