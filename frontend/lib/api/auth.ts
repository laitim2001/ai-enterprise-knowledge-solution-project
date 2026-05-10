/**
 * Self-register hybrid auth API client (W13 D5 cont CO_F5d frontend wire batch;
 * W17 F2 cookie transport per ADR-0022).
 *
 * Wraps backend POST /auth/register + /auth/verify-email + /auth/login +
 * /auth/resend-verification with typed responses. Reuses `apiClient.post` —
 * backend treats these as public (no Depends auth), so the auto-injected
 * Bearer is harmless when present. `login` + `verify-email` success sets the
 * httpOnly `ekp_session` cookie + `ekp_csrf` cookie (handled by the browser /
 * the `/api/backend` proxy) — callers don't persist the token themselves.
 *
 * Errors flow through the W7 ApiError envelope (`error.code` discriminator);
 * callers branch via the constants exported below to surface variant-specific
 * toast messages per V8/V9 plan acceptance criteria F3.7 + F4.7.
 */

import { apiClient } from '../api-client';

export interface UserPublic {
  oid: string;
  email: string;
  display_name: string;
  verified: boolean;
  is_mock: boolean;
}

export interface RegisterPayload {
  email: string;
  password: string;
  display_name: string;
}

export interface VerifyEmailPayload {
  email: string;
  code: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface ResendPayload {
  email: string;
}

export interface RegisterResponse {
  user: UserPublic;
  message: string;
}

export interface VerifyEmailResponse {
  user: UserPublic;
  message: string;
  // Set on the verified-transition (auto-login, per ADR-0022); null if the
  // user was already verified. The session cookie is the actual credential —
  // these are informational for any client that wants the Bearer too.
  access_token: string | null;
  expires_in: number | null;
}

export interface LoginResponse {
  access_token: string;
  token_type: 'Bearer';
  expires_in: number;
  user: UserPublic;
}

export interface ResendVerificationResponse {
  message: string;
  cooldown_seconds: number;
}

export const AuthErrorCodes = {
  EMAIL_ALREADY_EXISTS: 'auth.email_already_exists',
  INVALID_CREDENTIALS: 'auth.invalid_credentials',
  EMAIL_NOT_VERIFIED: 'auth.email_not_verified',
  VERIFICATION_FAILED: 'auth.verification_failed',
  VERIFICATION_EXPIRED: 'auth.verification_expired',
  RESEND_RATE_LIMITED: 'auth.resend_rate_limited',
  INVALID_EMAIL: 'validation.invalid_email',
  WEAK_PASSWORD: 'validation.weak_password',
} as const;

export const authApi = {
  register: (payload: RegisterPayload) =>
    apiClient.post<RegisterResponse>('/auth/register', payload),

  verifyEmail: (payload: VerifyEmailPayload) =>
    apiClient.post<VerifyEmailResponse>('/auth/verify-email', payload),

  login: (payload: LoginPayload) =>
    apiClient.post<LoginResponse>('/auth/login', payload),

  resendVerification: (payload: ResendPayload) =>
    apiClient.post<ResendVerificationResponse>('/auth/resend-verification', payload),
};
