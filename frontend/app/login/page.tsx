'use client';

/**
 * V8 Login page (`/login`) — W22 F2 direct-copy from mockup
 * `references/design-mockups/ekp-page-auth.jsx:5-65` PageLogin
 * (per CLAUDE.md §5.7 H7 strict fidelity 2026-05-18 — supersedes W17 F2 +
 * W18 F7 + W20 F7.1 strict-fidelity refactor;those used shadcn primitives +
 * Tailwind utilities;F2 rebuild uses mockup CSS classes directly).
 *
 * Structure mirrors mockup PageLogin:
 *   - Header: h1 "Welcome back" + subtitle (SSO + email)
 *   - Primary: SSO `<button class="btn btn-primary btn-lg">` full-width
 *   - Divider "OR continue with email" via shared <AuthDivider />
 *   - Email `<input class="input">` inside `<div class="field">`
 *   - Password `<input>` with right-aligned "Forgot password?" Tier 2 chip
 *   - Submit `<button class="btn btn-accent btn-lg">` full-width
 *   - "Don't have an account? Create one" link
 *   - Auth-modes mono dashed block (Tier 1 hybrid auth surface)
 *
 * Preserved from W17 F2 + W20 F7 (per CLAUDE.md §4 authority: backend wins):
 *   - useAuthStore.signIn for SSO (mock-auth bridge / real MSAL Beta+)
 *   - authApi.login for self-register (POST /auth/login → httpOnly cookie
 *     + CSRF double-submit per ADR-0022)
 *   - ApiError.code → toast variant mapping (INVALID_CREDENTIALS /
 *     EMAIL_NOT_VERIFIED / fallthrough)
 *   - router.push('/dashboard') on success
 *
 * Renders OUTSIDE `app/(app)/` — no AppShell (per ADR-0024 + W18 F7).
 */

import { Loader2 } from 'lucide-react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useState, type FormEvent } from 'react';
import { toast } from 'sonner';

import { AuthDivider, AuthFrame, MicrosoftIcon } from '@/components/auth/auth-frame';
import { ApiError } from '@/lib/api-client';
import { AuthErrorCodes, authApi } from '@/lib/api/auth';
import { useAuthStore } from '@/lib/providers/auth-provider';

export default function LoginPage() {
  const router = useRouter();
  const ssoSignIn = useAuthStore((s) => s.signIn);

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isFormPending, setIsFormPending] = useState(false);
  const [isSsoPending, setIsSsoPending] = useState(false);

  async function handleSelfSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!email || !password) {
      toast.error('Email and password required');
      return;
    }
    setIsFormPending(true);
    try {
      const response = await authApi.login({ email, password });
      toast.success(`Welcome back, ${response.user.display_name}!`);
      router.push('/dashboard');
    } catch (err) {
      handleAuthError(err, 'Sign in failed.');
    } finally {
      setIsFormPending(false);
    }
  }

  async function handleSsoClick() {
    setIsSsoPending(true);
    try {
      await ssoSignIn();
      toast.success('Signed in with Microsoft.');
      router.push('/dashboard');
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      toast.error('Microsoft sign-in failed.', { description: message });
    } finally {
      setIsSsoPending(false);
    }
  }

  const anyPending = isFormPending || isSsoPending;

  return (
    <AuthFrame>
      <form onSubmit={handleSelfSubmit}>
        {/* Heading — mockup lines 8-13 */}
        <div style={{ marginBottom: 18 }}>
          <h1
            style={{
              fontSize: 24,
              fontWeight: 600,
              letterSpacing: '-0.02em',
              margin: 0,
              marginBottom: 6,
            }}
          >
            Welcome back
          </h1>
          <p
            style={{
              fontSize: 14,
              color: 'oklch(var(--muted-foreground))',
              margin: 0,
            }}
          >
            Sign in with your Ricoh corporate account or with email.
          </p>
        </div>

        {/* Primary: Entra ID SSO — mockup lines 15-19 */}
        <button
          type="button"
          className="btn btn-primary btn-lg"
          style={{
            width: '100%',
            marginBottom: 14,
            justifyContent: 'center',
            gap: 10,
          }}
          onClick={handleSsoClick}
          disabled={anyPending}
        >
          {isSsoPending ? (
            <>
              <Loader2 className="animate-spin" size={14} />
              Redirecting…
            </>
          ) : (
            <>
              <MicrosoftIcon />
              Sign in with Microsoft
            </>
          )}
        </button>

        <AuthDivider label="OR continue with email" />

        {/* Email — mockup lines 23-26 */}
        <div className="field">
          <label className="label" htmlFor="login-email">
            Work email
          </label>
          <input
            id="login-email"
            className="input"
            type="email"
            autoComplete="email"
            placeholder="you@ricoh.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            disabled={anyPending}
            required
          />
        </div>

        {/* Password — mockup lines 28-37 */}
        <div className="field">
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <label
              className="label"
              htmlFor="login-password"
              style={{ flex: 1, marginBottom: 0 }}
            >
              Password
            </label>
            <button
              type="button"
              disabled
              aria-disabled="true"
              className="btn btn-ghost btn-xs btn-ghost-muted"
              title="Forgot password — Tier 2 (post-Beta)"
            >
              Forgot password?{' '}
              <span
                className="badge badge-muted"
                style={{ marginLeft: 4, fontSize: 9.5 }}
              >
                Tier 2
              </span>
            </button>
          </div>
          <input
            id="login-password"
            className="input"
            type="password"
            autoComplete="current-password"
            placeholder="••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            disabled={anyPending}
            required
            style={{ marginTop: 6 }}
          />
        </div>

        {/* Submit — mockup lines 39-41 */}
        <button
          type="submit"
          className="btn btn-accent btn-lg"
          style={{ width: '100%', marginTop: 8, justifyContent: 'center' }}
          disabled={anyPending}
        >
          {isFormPending ? (
            <>
              <Loader2 className="animate-spin" size={14} />
              Signing in…
            </>
          ) : (
            'Sign in →'
          )}
        </button>

        {/* Sign-up link — mockup lines 43-45 */}
        <div
          style={{
            textAlign: 'center',
            marginTop: 18,
            fontSize: 13,
            color: 'oklch(var(--muted-foreground))',
          }}
        >
          Don&apos;t have an account?{' '}
          <Link
            href="/register"
            style={{
              color: 'oklch(var(--accent))',
              fontWeight: 500,
              textDecoration: 'none',
            }}
          >
            Create one
          </Link>
        </div>

        {/* Auth modes (Tier 1) mono dashed block — mockup lines 48-62 */}
        <div
          style={{
            marginTop: 24,
            padding: '10px 12px',
            border: '1px dashed oklch(var(--border-strong))',
            borderRadius: 'var(--radius-sm)',
            fontSize: 11.5,
            color: 'oklch(var(--muted-foreground))',
            lineHeight: 1.6,
            fontFamily: 'var(--font-mono)',
          }}
          aria-label="Auth modes — Tier 1"
        >
          <b style={{ color: 'oklch(var(--foreground))' }}>Auth modes (Tier 1)</b>
          <br />· Hybrid: Entra ID SSO primary + email self-register fallback (ADR-0022)
          <br />· httpOnly cookie + CSRF double-submit + /auth/refresh
          <br />· Mock-auth default in dev (Track A IT cred populate W16+)
        </div>
      </form>
    </AuthFrame>
  );
}

function handleAuthError(err: unknown, fallbackMessage: string): void {
  if (err instanceof ApiError) {
    const code = err.code;
    if (code === AuthErrorCodes.INVALID_CREDENTIALS) {
      toast.error('Email or password is incorrect.', {
        description: 'Check your credentials and try again.',
      });
    } else if (code === AuthErrorCodes.EMAIL_NOT_VERIFIED) {
      toast.error('Verify your email first.', {
        description: err.actionableHint ?? 'Check your inbox or resend the code.',
      });
    } else {
      toast.error(err.message, {
        description: err.actionableHint ?? undefined,
      });
    }
    return;
  }
  const message = err instanceof Error ? err.message : String(err);
  toast.error(fallbackMessage, { description: message });
}
