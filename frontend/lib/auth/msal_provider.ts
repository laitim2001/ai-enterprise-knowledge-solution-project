// C11 — W8 D3 F1.3 real msal-react Entra ID provider.
//
// Browser-only client component dependency: PublicClientApplication mutates
// sessionStorage. Module-level singleton, lazily initialized to keep SSR
// (Next.js server component render) safe — no `new PublicClientApplication`
// during build/server render.
//
// Token caching: api-client.ts calls `getMsalBearer()` synchronously per
// request. After login (redirect or popup) we cache the access_token in a
// module-level slot and refresh it via `acquireTokenSilent` from
// `refreshMsal()` before it expires (auth-provider.tsx schedules refresh
// every ~50 minutes per Microsoft default 1h expiry).

import {
  AccountInfo,
  AuthenticationResult,
  PublicClientApplication,
  type Configuration,
} from "@azure/msal-browser";

import type { AuthBearer, AuthenticatedUser } from "./types";

const TENANT_ID = process.env.NEXT_PUBLIC_AZURE_TENANT_ID ?? "";
const CLIENT_ID = process.env.NEXT_PUBLIC_AZURE_CLIENT_ID ?? "";
// API scope = `api://<API_CLIENT_ID>/<scope_name>`. Backend audience
// (azure_client_id Settings) usually equals API_CLIENT_ID.
const API_SCOPE = process.env.NEXT_PUBLIC_AZURE_API_SCOPE ?? "";

let _msalInstance: PublicClientApplication | null = null;
let _initialized = false;
let _cachedAccessToken: string | null = null;
let _cachedAccount: AccountInfo | null = null;

function _msalConfig(): Configuration {
  return {
    auth: {
      clientId: CLIENT_ID,
      authority: `https://login.microsoftonline.com/${TENANT_ID}`,
      redirectUri:
        typeof window !== "undefined" ? window.location.origin : "/",
      postLogoutRedirectUri:
        typeof window !== "undefined" ? window.location.origin : "/",
    },
    cache: {
      cacheLocation: "sessionStorage", // safer vs localStorage for token state
    },
  };
}

/**
 * Lazy singleton — never call during SSR/build. Throws if browser globals
 * absent so consumers can fall back to a render-only error UI.
 */
export function getMsalInstance(): PublicClientApplication {
  if (typeof window === "undefined") {
    throw new Error("msal-browser is browser-only — guard call sites with typeof window check");
  }
  if (!CLIENT_ID || !TENANT_ID) {
    throw new Error(
      "MSAL not configured (NEXT_PUBLIC_AZURE_CLIENT_ID / NEXT_PUBLIC_AZURE_TENANT_ID missing)",
    );
  }
  if (_msalInstance === null) {
    _msalInstance = new PublicClientApplication(_msalConfig());
  }
  return _msalInstance;
}

/** Initialize once; safe to call repeatedly (no-op after first). */
export async function initMsal(): Promise<void> {
  if (_initialized) return;
  const msal = getMsalInstance();
  await msal.initialize();
  // handleRedirectPromise resolves to AuthenticationResult on landing-back
  // from Entra ID hosted login, else null on every other navigation.
  const result = await msal.handleRedirectPromise();
  if (result) {
    _absorb(result);
  } else {
    // Restore active account from cache if user previously logged in.
    const accounts = msal.getAllAccounts();
    if (accounts.length > 0) {
      msal.setActiveAccount(accounts[0]);
      _cachedAccount = accounts[0];
    }
  }
  _initialized = true;
}

function _absorb(result: AuthenticationResult): void {
  _cachedAccessToken = result.accessToken;
  _cachedAccount = result.account;
  if (result.account) {
    getMsalInstance().setActiveAccount(result.account);
  }
}

function _toUser(account: AccountInfo): AuthenticatedUser {
  // localAccountId == oid for AAD; preferences fall back to username then
  // homeAccountId for B2B / guest accounts that may lack `username`.
  return {
    oid: (account.idTokenClaims as Record<string, unknown> | undefined)?.oid as string
      ?? account.localAccountId,
    tid: (account.idTokenClaims as Record<string, unknown> | undefined)?.tid as string
      ?? account.tenantId,
    preferredUsername: account.username || account.homeAccountId,
    isMock: false,
  };
}

export function getMsalBearer(): AuthBearer {
  if (!_cachedAccessToken) {
    throw new Error(
      "MSAL not authenticated yet — call login() or wait for handleRedirectPromise",
    );
  }
  return { scheme: "Bearer", token: _cachedAccessToken };
}

export function getMsalUser(): AuthenticatedUser {
  if (!_cachedAccount) {
    throw new Error("MSAL not authenticated yet — call login() first");
  }
  return _toUser(_cachedAccount);
}

export async function loginMsal(): Promise<AuthenticatedUser> {
  await initMsal();
  const msal = getMsalInstance();
  // loginRedirect is preferred over popup for production (avoids popup
  // blockers + iframe sandbox issues on corporate networks).
  // Caller resolves AFTER navigation back via initMsal -> handleRedirectPromise;
  // the awaited Promise here resolves to never under normal redirect flow.
  await msal.loginRedirect({
    scopes: API_SCOPE ? [API_SCOPE] : ["openid", "profile", "offline_access"],
  });
  // Unreachable in browser due to redirect; satisfies TS return type.
  if (!_cachedAccount) {
    throw new Error("redirect_in_progress");
  }
  return _toUser(_cachedAccount);
}

export async function logoutMsal(): Promise<void> {
  await initMsal();
  const msal = getMsalInstance();
  _cachedAccessToken = null;
  _cachedAccount = null;
  await msal.logoutRedirect();
}

export async function refreshMsal(): Promise<{
  accessToken: string;
  expiresIn: number;
}> {
  await initMsal();
  const msal = getMsalInstance();
  const account = _cachedAccount ?? msal.getActiveAccount();
  if (!account) {
    throw new Error("no active account — call login() first");
  }
  const result = await msal.acquireTokenSilent({
    scopes: API_SCOPE ? [API_SCOPE] : ["openid", "profile", "offline_access"],
    account,
  });
  _absorb(result);
  const expiresInS = result.expiresOn
    ? Math.max(0, Math.floor((result.expiresOn.getTime() - Date.now()) / 1000))
    : 3600;
  return { accessToken: result.accessToken, expiresIn: expiresInS };
}

// Test-only escape hatch (W8 D3 leaves frontend test harness deferred per
// W7 D4 F4.4 / F5.5 — added here so a future Vitest install can drive the
// auth flow without browser globals).
export function _resetMsalForTests(): void {
  _msalInstance = null;
  _initialized = false;
  _cachedAccessToken = null;
  _cachedAccount = null;
}
