// C11 — frontend single switching point analogous to backend Depends pattern.
//
// authMode is tri-state (CH-013), resolved from env at module load:
//   NEXT_PUBLIC_AUTH_MOCK=true       → "mock"   (W7 dev — auto dev-user, mock_msal.ts)
//   else NEXT_PUBLIC_AUTH_SSO=true   → "msal"   (Entra ID SSO — msal_provider.ts; Track A cred)
//   else                             → "cookie" (email/password self-register — cookie_session.ts)
//
// The "cookie" default (mock off + SSO off) avoids landing on the un-configured
// MSAL path: with no NEXT_PUBLIC_AZURE_* env, getMsalInstance() throws and the
// app would be stuck on an error splash. Cookie mode is the local self-register
// flow per ADR-0014/0022.
//
// W17 F2 (per ADR-0022): the self-register session is carried in the httpOnly
// `ekp_session` cookie the browser attaches automatically (api-client.ts uses
// `credentials:'include'`). So `getBearer()` returns a real bearer only in mock
// (dev-token) / msal (JWT) modes; cookie mode has no bearer (getCookieBearer
// throws → api-client falls back to `{}` and the cookie does the work).
//
// Consumers (api-client.ts, providers/auth-provider.tsx) import from this
// barrel only — keeps the swap to a single env-var flip.

import {
  getCookieBearer,
  getCookieUser,
  loginCookie,
  logoutCookie,
  refreshCookie,
} from "./cookie_session";
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

const isMockMode = process.env.NEXT_PUBLIC_AUTH_MOCK === "true";
const isSsoMode = process.env.NEXT_PUBLIC_AUTH_SSO === "true";

export const authMode: "mock" | "cookie" | "msal" = isMockMode
  ? "mock"
  : isSsoMode
    ? "msal"
    : "cookie";

export function getBearer(): AuthBearer {
  if (authMode === "mock") return getMockBearer();
  if (authMode === "msal") return getMsalBearer();
  return getCookieBearer();
}

export function getCurrentUser(): AuthenticatedUser {
  if (authMode === "mock") return getMockUser();
  if (authMode === "msal") return getMsalUser();
  return getCookieUser();
}

export async function login(): Promise<AuthenticatedUser> {
  if (authMode === "mock") return loginMock();
  if (authMode === "msal") return loginMsal();
  return loginCookie();
}

export async function logout(): Promise<void> {
  if (authMode === "mock") return logoutMock();
  if (authMode === "msal") return logoutMsal();
  return logoutCookie();
}

export async function refresh(): Promise<{
  accessToken: string;
  expiresIn: number;
}> {
  if (authMode === "mock") return refreshMock();
  if (authMode === "msal") return refreshMsal();
  return refreshCookie();
}
