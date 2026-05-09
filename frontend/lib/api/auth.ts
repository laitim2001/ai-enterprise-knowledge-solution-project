/**
 * Self-register hybrid auth API client (W13 D5 cont CO_F5d frontend wire batch).
 *
 * Wraps backend POST /auth/register + /auth/verify-email + /auth/login +
 * /auth/resend-verification with typed responses. Reuses `apiClient.post`
 * which auto-injects bearer header — backend treats these endpoints as public
 * (no Depends auth), so the bearer is harmless when present.
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

export const SESSION_TOKEN_STORAGE_KEY = 'ekp_session_token';

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
