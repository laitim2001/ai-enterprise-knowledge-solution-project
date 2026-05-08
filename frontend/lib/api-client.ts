/**
 * Backend API client (per architecture.md §4.4 — 18 endpoints).
 *
 * Browser fetches hit `/api/backend/*` and are server-side proxied by
 * Next.js (next.config.mjs rewrite → ${NEXT_PUBLIC_API_URL}/*). This:
 *   1. Bypasses CORS (no backend middleware needed; same-origin from
 *      browser perspective).
 *   2. Delegates TLS chain verification to Node.js OpenSSL bundle, avoiding
 *      browser truststore issues with corp proxy R8 (W11 D2 discovery —
 *      schannel CRYPT_E_NO_REVOCATION_CHECK on direct browser fetch).
 * `NEXT_PUBLIC_API_URL` is consumed only by next.config.mjs at server
 * start; do not read it from client-side code.
 *
 * W7 D2 F1.4: every request injects an Authorization Bearer header from
 * `lib/auth/index.ts` so /query/** + /kb/** + /feedback land authenticated.
 * Mock vs real MSAL is a `NEXT_PUBLIC_AUTH_MOCK` env-var flip — same single
 * switching point as backend `Settings.feature_auth_mock`.
 *
 * URL hygiene rule (W11 D2 discovery 2026-06-10): URL paths passed to
 * ApiClient methods MUST NOT have trailing slashes. FastAPI auto-redirects
 * `/path/` → `/path` with HTTP 307; the redirect hop CAN strip the
 * Authorization header (Python httpx strips by default as cross-origin
 * credential-leak prevention; native fetch behavior on 307+Auth is
 * implementation-defined and fragile). Path canonicalization at source
 * eliminates the redirect hop entirely.
 *
 * Verified compliant 2026-06-10: lib/api/kb.ts (/kb, /kb/${id},
 * /kb/${id}/settings, /kb/${id}/documents), lib/api/query.ts (/query/stream).
 *
 * Reference: docs/01-planning/W11-staged-rollout-25/progress.md Day 2 §3
 * governance finding #3 + W11 D5 retro carry-over #4.
 */

import { getBearer } from './auth';

const API_PREFIX = '/api/backend';

function buildAuthHeader(): Record<string, string> {
  try {
    const bearer = getBearer();
    return { Authorization: `${bearer.scheme} ${bearer.token}` };
  } catch {
    // msal_provider skeleton throws until W8 D2-D3. Caller will see the 401
    // from backend rather than a hard frontend crash.
    return {};
  }
}

/**
 * Backend ApiError envelope (F4.1 contract). Frontend boundary (F4.2)
 * inspects `code` for branching and shows `message` + `actionable_hint`.
 */
export interface ApiErrorEnvelope {
  error: {
    code: string;
    message: string;
    actionable_hint?: string | null;
  };
}

export class ApiError extends Error {
  public readonly code: string;
  public readonly actionableHint: string | null;

  constructor(
    public readonly status: number,
    public readonly body: string,
    parsed?: ApiErrorEnvelope,
  ) {
    super(parsed?.error.message ?? `API error ${status}: ${body}`);
    this.code = parsed?.error.code ?? `http.${status}`;
    this.actionableHint = parsed?.error.actionable_hint ?? null;
  }
}

async function buildApiError(response: Response): Promise<ApiError> {
  const body = await response.text();
  try {
    const parsed = JSON.parse(body) as ApiErrorEnvelope;
    if (parsed?.error?.code && parsed?.error?.message) {
      return new ApiError(response.status, body, parsed);
    }
  } catch {
    // Body wasn't the F4.1 envelope; fall through to generic ApiError.
  }
  return new ApiError(response.status, body);
}

export class ApiClient {
  constructor(private readonly baseUrl: string = API_PREFIX) {}

  async get<T>(path: string): Promise<T> {
    const response = await fetch(`${this.baseUrl}${path}`, {
      headers: { ...buildAuthHeader() },
    });
    if (!response.ok) {
      throw await buildApiError(response);
    }
    return response.json() as Promise<T>;
  }

  async post<T>(path: string, body: unknown): Promise<T> {
    const response = await fetch(`${this.baseUrl}${path}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...buildAuthHeader(),
      },
      body: JSON.stringify(body),
    });
    if (!response.ok) {
      throw await buildApiError(response);
    }
    return response.json() as Promise<T>;
  }

  async patch<T>(path: string, body: unknown): Promise<T> {
    const response = await fetch(`${this.baseUrl}${path}`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        ...buildAuthHeader(),
      },
      body: JSON.stringify(body),
    });
    if (!response.ok) {
      throw await buildApiError(response);
    }
    return response.json() as Promise<T>;
  }
}

export const apiClient = new ApiClient();
