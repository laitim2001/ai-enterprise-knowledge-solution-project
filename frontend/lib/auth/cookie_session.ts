// C11 — cookie-session auth provider (CH-013).
//
// The third auth mode alongside mock (mock_msal.ts) + real MSAL (msal_provider.ts).
// Backs the email/password self-register login: `POST /auth/login` (handled by
// the login page form) sets the httpOnly `ekp_session` + `ekp_csrf` cookies per
// ADR-0022; this provider then resolves *who* the cookie belongs to via
// `GET /auth/me` so the auth store can render the real identity.
//
// There is no bearer here — the session travels in the httpOnly cookie that the
// browser attaches automatically (api-client.ts `credentials:'include'`). So the
// synchronous `getCookieBearer()` / `getCookieUser()` intentionally throw: bearer
// has no value (api-client.ts buildAuthHeader() catches → falls back to {} → the
// cookie does the work), and identity is hydrated asynchronously by the
// auth-provider calling `loginCookie()` on mount.
//
// Circular-import note: `usersApi` / `apiClient` are imported *dynamically* inside
// the async functions, NOT at module top-level. The static chain api-client.ts →
// auth/index.ts → cookie_session.ts → api/users.ts → api-client.ts forms a cycle;
// a top-level value import makes SSR webpack evaluate `ApiClient` before it's
// initialized ("Cannot access 'ApiClient' before initialization"). Deferring to
// call time (api-client fully initialized by then) breaks the cycle. Top-level
// imports here are type-only (erased at build).

import type { MeResponse } from "../api/users";
import type { AuthBearer, AuthenticatedUser } from "./types";

/** Map the backend snake_case `/auth/me` shape onto the frontend claim type.
 * `role` is dropped here — the store user shape carries no role; `useRole()`
 * reads it separately via the same `/auth/me` query. */
function mapMe(me: MeResponse): AuthenticatedUser {
  return {
    oid: me.oid,
    tid: me.tid,
    preferredUsername: me.preferred_username,
    isMock: me.is_mock,
  };
}

export function getCookieBearer(): AuthBearer {
  throw new Error("cookie-session uses the httpOnly ekp_session cookie — no bearer");
}

export function getCookieUser(): AuthenticatedUser {
  throw new Error("cookie-session identity is hydrated async via loginCookie()/GET /auth/me");
}

/** Resolve the current identity from the existing session cookie. Throws (via
 * ApiError 401) when there is no valid session — the auth-provider treats that
 * as "not signed in". The actual credential exchange already happened in the
 * login page form (`authApi.login` → cookie); this only reads it back. */
export async function loginCookie(): Promise<AuthenticatedUser> {
  const { usersApi } = await import("../api/users");
  const me = await usersApi.getMe();
  return mapMe(me);
}

/** Revoke the session server-side + clear the auth cookies. Goes through
 * `apiClient.post` so `credentials:'include'` carries the cookie and the CSRF
 * double-submit header is attached (POST is a state-changing method). */
export async function logoutCookie(): Promise<void> {
  try {
    const { apiClient } = await import("../api-client");
    await apiClient.post("/auth/logout", {});
  } catch {
    // A network blip during dev should not block UI sign-out — the store clear
    // + redirect are the user-facing source of truth.
  }
}

export async function refreshCookie(): Promise<{
  accessToken: string;
  expiresIn: number;
}> {
  // No silent refresh in cookie mode — the session cookie has a 7d TTL (ADR-0022)
  // and the dev flow re-logs-in on expiry. Kept for the provider interface parity.
  return { accessToken: "", expiresIn: 0 };
}

export { mapMe as _mapMeForTests };
