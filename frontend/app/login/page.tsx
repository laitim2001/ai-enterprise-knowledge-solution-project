'use client';

/**
 * V8 Login page (`/login`) — public entry per architecture.md v6 §5.10 + ADR-0014.
 *
 * Layout per ui-design-reference-v6.md §2.8 wireframe: brand panel left + form
 * area right (split layout). Brand panel collapses < md per F3.8 responsive
 * acceptance.
 *
 * W13 D5 cont CO_F5d: auth wire deferral resolved — F5 backend cascade landed.
 * W17 F2 (per ADR-0022): self-register path POSTs `/auth/login`; the backend
 * sets the httpOnly `ekp_session` cookie + `ekp_csrf` cookie on the response
 * (the browser / `/api/backend` proxy carry it), so the page no longer
 * persists the token in localStorage. SSO path delegates to existing
 * useAuthStore (mock_msal in dev / real MSAL Beta+ via Q11 IT cred).
 * Error.code from the ApiError envelope drives toast variants per F3.7.
 *
 * W18 F7 (per ADR-0024): successful sign-in now routes to `/dashboard` (the new
 * post-login home) instead of `/chat`. Stays OUTSIDE the `app/(app)/` shell —
 * the login page gets no app chrome (the BrandPanel split layout is its own).
 */

import { Building2, Loader2 } from 'lucide-react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useState, type FormEvent } from 'react';
import { toast } from 'sonner';

import { BrandPanel } from '@/components/auth/brand-panel';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
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
      // W17 F2 (ADR-0022): the `ekp_session` httpOnly cookie is set by the
      // response — no client-side token persistence. Subsequent protected
      // calls carry it automatically (api-client `credentials:'include'`).
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
    <div className="flex min-h-screen flex-col md:flex-row">
      <BrandPanel />
      <main className="flex flex-1 items-center justify-center bg-background px-6 py-12">
        <div className="w-full max-w-sm">
          <h1 className="text-2xl font-semibold tracking-tight">Sign in</h1>
          <p className="mt-2 text-sm text-muted-foreground">
            Welcome back. Use your Ricoh account or sign in with email.
          </p>

          <form onSubmit={handleSelfSubmit} className="mt-8 space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                autoComplete="email"
                placeholder="you@ricoh.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                disabled={anyPending}
                required
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={anyPending}
                required
              />
            </div>
            <Button type="submit" className="w-full" disabled={anyPending}>
              {isFormPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Signing in…
                </>
              ) : (
                'Sign in'
              )}
            </Button>
          </form>

          <div className="my-6 flex items-center gap-3">
            <Separator className="flex-1" />
            <span className="text-xs uppercase tracking-wide text-muted-foreground">
              or
            </span>
            <Separator className="flex-1" />
          </div>

          <Button
            variant="outline"
            className="w-full"
            onClick={handleSsoClick}
            disabled={anyPending}
          >
            {isSsoPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Redirecting…
              </>
            ) : (
              <>
                <Building2 className="mr-2 h-4 w-4" />
                Sign in with Microsoft
              </>
            )}
          </Button>

          <div className="mt-6 flex items-center justify-between text-xs">
            <span
              className="cursor-not-allowed text-muted-foreground opacity-60"
              title="Forgot password — Tier 2 (post-Beta) per ADR-0014"
            >
              Forgot password?
            </span>
            <Link
              href="/register"
              className="text-foreground transition-colors hover:text-accent"
            >
              Don&apos;t have an account?{' '}
              <span className="font-medium underline-offset-4 hover:underline">
                Register
              </span>
            </Link>
          </div>
        </div>
      </main>
    </div>
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
