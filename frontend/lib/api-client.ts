/**
 * Backend API client (per architecture.md §4.4 — 18 endpoints).
 *
 * Reads `NEXT_PUBLIC_API_URL` from env (.env.example).
 * W7 D2 F1.4: every request injects an Authorization Bearer header from
 * `lib/auth/index.ts` so /query/** + /kb/** + /feedback land authenticated.
 * Mock vs real MSAL is a `NEXT_PUBLIC_AUTH_MOCK` env-var flip — same single
 * switching point as backend `Settings.feature_auth_mock`.
 */

import { getBearer } from './auth';

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

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
  constructor(private readonly baseUrl: string = API_URL) {}

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
