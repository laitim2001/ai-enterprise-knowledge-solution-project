// C11 — frontend single switching point analogous to backend Depends pattern.
//
// `NEXT_PUBLIC_AUTH_MOCK=true` (W7 dev) → mock_msal.ts.
// `NEXT_PUBLIC_AUTH_MOCK=false` or unset (W8 D4 onwards) → msal_provider.ts.
//
// W14 D1 F1.5 (CO_F5d-cont) extension — self-register session-token mode sits
// in front of the mock/MSAL switching: when localStorage carries the session
// token issued by `POST /auth/login` (W13 D5 F5 hybrid auth cascade), use it
// as the bearer so api-client lifts the right credential for protected calls.
// Parallel to backend `dependency.get_current_user` session branch architecture.
//
// Consumers (api-client.ts, providers/auth-provider.tsx) import from this
// barrel only — keeps the swap to a single env-var flip.

import {
  getMockBearer,
  getMockUser,
  loginMock,
  logoutMock,
  refreshMock,
} from "./mock_msal";
import {
  getMsalBearer,
  getMsalUser,
  loginMsal,
  logoutMsal,
  refreshMsal,
} from "./msal_provider";
import type { AuthBearer, AuthenticatedUser } from "./types";

export type { AuthBearer, AuthenticatedUser };

// Single source of truth for the localStorage key — `lib/api/auth.ts`
// re-exports this so the login form and getBearer never drift.
export const SESSION_TOKEN_STORAGE_KEY = "ekp_session_token";

const isMockMode = process.env.NEXT_PUBLIC_AUTH_MOCK === "true";

function readSessionBearer(): AuthBearer | null {
  if (typeof window === "undefined") return null;
  try {
    const token = window.localStorage.getItem(SESSION_TOKEN_STORAGE_KEY);
    if (!token) return null;
    return { scheme: "Bearer", token };
  } catch {
    // localStorage may throw in privacy / sandbox mode — fall through to
    // mock/MSAL path so the app stays functional.
    return null;
  }
}

export function getBearer(): AuthBearer {
  const session = readSessionBearer();
  if (session !== null) return session;
  return isMockMode ? getMockBearer() : getMsalBearer();
}

export function getCurrentUser(): AuthenticatedUser {
  return isMockMode ? getMockUser() : getMsalUser();
}

export async function login(): Promise<AuthenticatedUser> {
  return isMockMode ? loginMock() : loginMsal();
}

export async function logout(): Promise<void> {
  return isMockMode ? logoutMock() : logoutMsal();
}

export async function refresh(): Promise<{
  accessToken: string;
  expiresIn: number;
}> {
  return isMockMode ? refreshMock() : refreshMsal();
}

export const authMode: "mock" | "msal" = isMockMode ? "mock" : "msal";
