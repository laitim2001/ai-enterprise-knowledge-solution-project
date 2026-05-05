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

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly body: string,
  ) {
    super(`API error ${status}: ${body}`);
  }
}

export class ApiClient {
  constructor(private readonly baseUrl: string = API_URL) {}

  async get<T>(path: string): Promise<T> {
    const response = await fetch(`${this.baseUrl}${path}`, {
      headers: { ...buildAuthHeader() },
    });
    if (!response.ok) {
      throw new ApiError(response.status, await response.text());
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
      throw new ApiError(response.status, await response.text());
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
      throw new ApiError(response.status, await response.text());
    }
    return response.json() as Promise<T>;
  }
}

export const apiClient = new ApiClient();
