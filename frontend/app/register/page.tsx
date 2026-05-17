'use client';

/**
 * V9 Register page (`/register`) — W22 F2 direct-copy from mockup
 * `references/design-mockups/ekp-page-auth.jsx:68-175` PageRegister
 * (per CLAUDE.md §5.7 H7 strict fidelity 2026-05-18 — visual rebuild).
 *
 * 3-step structure (PRESERVED from W17 F2 + W20 F7.2 — backend wins per
 * CLAUDE.md §4 authority + §13 "Mockup vs backend contract 衝突 → backend
 * wins per §4"):
 *   1. Account info (full name / email / password / terms)
 *   2. Email verify (6-digit code, NOT mockup's email-link — backend
 *      contract per ADR-0014 + architecture.md v6 §3.7)
 *   3. Welcome (post-verify success state)
 *
 * Mockup PageRegister is 2-step (form + click-email-link landing) because
 * its design assumed Magic Link verification. EKP backend ships 6-digit
 * code verification → Step 2 keeps W20 6-digit boxes + auto-advance focus
 * + paste distribution UX. Step 2 visual treatment (IcInbox + "Check your
 * inbox" + ACS footer) lifted from mockup; the 6-digit input replaces
 * mockup's "click the link" copy + Resend button.
 *
 * Visual rebuild (per H7):
 *   - <AuthFrame> wrapper (shared with /login)
 *   - All Tailwind utility / shadcn primitives replaced by mockup CSS
 *     classes (`.btn .input .label .field .hint .badge`)
 *   - Mockup inline styles preserved 1:1
 *
 * Preserved auth flow (per CLAUDE.md §4):
 *   - authApi.register / authApi.verifyEmail / authApi.resendVerification
 *   - ApiError.code → toast variant mapping
 *   - 60s resend cooldown
 *   - Password strength heuristic (passwordStrength)
 *   - validateAccountInfo + EMAIL_PATTERN
 *
 * Renders OUTSIDE `app/(app)/` — no AppShell.
 */

import { ArrowLeft, Inbox, Loader2, PartyPopper, RefreshCw } from 'lucide-react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import {
  useEffect,
  useRef,
  useState,
  type ChangeEvent,
  type ClipboardEvent,
  type FormEvent,
  type KeyboardEvent,
} from 'react';
import { toast } from 'sonner';

import { AuthFrame } from '@/components/auth/auth-frame';
import { ApiError } from '@/lib/api-client';
import { AuthErrorCodes, authApi } from '@/lib/api/auth';

const RESEND_COOLDOWN_SEC = 60;
const CODE_LENGTH = 6;

type Step = 1 | 2 | 3;

interface AccountInfo {
  email: string;
  password: string;
  confirmPassword: string;
  displayName: string;
  acceptedTerms: boolean;
}

const EMPTY_INFO: AccountInfo = {
  email: '',
  password: '',
  confirmPassword: '',
  displayName: '',
  acceptedTerms: false,
};

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export default function RegisterPage() {
  const router = useRouter();
  const [step, setStep] = useState<Step>(1);
  const [info, setInfo] = useState<AccountInfo>(EMPTY_INFO);
  const [code, setCode] = useState<string[]>(() => Array(CODE_LENGTH).fill(''));
  const [isPending, setIsPending] = useState(false);
  const [resendCooldown, setResendCooldown] = useState(0);

  const errors = validateAccountInfo(info);

  useEffect(() => {
    if (resendCooldown <= 0) return;
    const id = setTimeout(() => setResendCooldown((prev) => prev - 1), 1000);
    return () => clearTimeout(id);
  }, [resendCooldown]);

  async function handleStep1Submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (Object.keys(errors).length > 0) return;
    setIsPending(true);
    try {
      await authApi.register({
        email: info.email,
        password: info.password,
        display_name: info.displayName,
      });
      toast.success('Verification email sent — check your inbox.');
      setStep(2);
      setResendCooldown(RESEND_COOLDOWN_SEC);
    } catch (err) {
      handleRegisterError(err);
    } finally {
      setIsPending(false);
    }
  }

  async function handleStep2Submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (code.some((c) => !c)) {
      toast.error('Enter all 6 digits.');
      return;
    }
    setIsPending(true);
    try {
      await authApi.verifyEmail({
        email: info.email,
        code: code.join(''),
      });
      toast.success('Email verified!');
      setStep(3);
    } catch (err) {
      handleVerifyError(err);
    } finally {
      setIsPending(false);
    }
  }

  async function handleResend() {
    if (resendCooldown > 0) return;
    try {
      await authApi.resendVerification({ email: info.email });
      setResendCooldown(RESEND_COOLDOWN_SEC);
      toast.info('Verification email resent.');
    } catch (err) {
      handleResendError(err);
    }
  }

  function handleGoToDashboard() {
    router.push('/dashboard');
  }

  return (
    <AuthFrame>
      {step === 1 && (
        <Step1
          info={info}
          errors={errors}
          isPending={isPending}
          onChange={setInfo}
          onSubmit={handleStep1Submit}
        />
      )}
      {step === 2 && (
        <Step2
          email={info.email}
          code={code}
          isPending={isPending}
          resendCooldown={resendCooldown}
          onCodeChange={setCode}
          onResend={handleResend}
          onSubmit={handleStep2Submit}
          onBack={() => setStep(1)}
        />
      )}
      {step === 3 && (
        <Step3 displayName={info.displayName} onContinue={handleGoToDashboard} />
      )}
    </AuthFrame>
  );
}

// ──────────────────────────────────────────────────────────────────────────
// Step 1 — Account info (direct-copy mockup PageRegister lines 133-174)
// ──────────────────────────────────────────────────────────────────────────

function Step1({
  info,
  errors,
  isPending,
  onChange,
  onSubmit,
}: {
  info: AccountInfo;
  errors: Record<string, string>;
  isPending: boolean;
  onChange: (next: AccountInfo) => void;
  onSubmit: (e: FormEvent<HTMLFormElement>) => void;
}) {
  const isFormValid = Object.keys(errors).length === 0;

  return (
    <form onSubmit={onSubmit}>
      {/* Heading — mockup lines 135-140 */}
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
          Create your account
        </h1>
        <p
          style={{
            fontSize: 14,
            color: 'oklch(var(--muted-foreground))',
            margin: 0,
          }}
        >
          Self-register with email · SSO via{' '}
          <Link
            href="/login"
            style={{ color: 'oklch(var(--foreground))', fontWeight: 500, textDecoration: 'none' }}
          >
            Sign in
          </Link>{' '}
          if you have Entra ID.
        </p>
      </div>

      {/* Full name — mockup lines 142-145 */}
      <div className="field">
        <label className="label" htmlFor="reg-display-name">
          Full name
        </label>
        <input
          id="reg-display-name"
          className="input"
          type="text"
          autoComplete="name"
          placeholder="Chris Lai"
          value={info.displayName}
          onChange={(e) => onChange({ ...info, displayName: e.target.value })}
          disabled={isPending}
          required
        />
        {errors.displayName && (
          <div
            className="hint"
            style={{ color: 'oklch(var(--destructive))' }}
            role="alert"
          >
            {errors.displayName}
          </div>
        )}
      </div>

      {/* Email — mockup lines 147-151 */}
      <div className="field">
        <label className="label" htmlFor="reg-email">
          Work email
        </label>
        <input
          id="reg-email"
          className="input"
          type="email"
          autoComplete="email"
          placeholder="you@ricoh.com"
          value={info.email}
          onChange={(e) => onChange({ ...info, email: e.target.value })}
          disabled={isPending}
          required
        />
        <div className="hint">
          We&apos;ll send a 6-digit verification code · Beta cohort restricted to{' '}
          <span className="mono">@ricoh.com</span>
        </div>
        {errors.email && (
          <div
            className="hint"
            style={{ color: 'oklch(var(--destructive))' }}
            role="alert"
          >
            {errors.email}
          </div>
        )}
      </div>

      {/* Password — mockup lines 153-157 */}
      <div className="field">
        <label className="label" htmlFor="reg-password">
          Password
        </label>
        <input
          id="reg-password"
          className="input"
          type="password"
          autoComplete="new-password"
          placeholder="At least 8 characters"
          value={info.password}
          onChange={(e) => onChange({ ...info, password: e.target.value })}
          disabled={isPending}
          required
        />
        <div className="hint">
          Scrypt-hashed via ADR-0022 · 8+ chars, 1 uppercase, 1 digit or symbol
        </div>
        {errors.password && (
          <div
            className="hint"
            style={{ color: 'oklch(var(--destructive))' }}
            role="alert"
          >
            {errors.password}
          </div>
        )}
      </div>

      {/* Confirm password — preserved per W20 F7.2 */}
      <div className="field">
        <label className="label" htmlFor="reg-confirm-password">
          Confirm password
        </label>
        <input
          id="reg-confirm-password"
          className="input"
          type="password"
          autoComplete="new-password"
          value={info.confirmPassword}
          onChange={(e) =>
            onChange({ ...info, confirmPassword: e.target.value })
          }
          disabled={isPending}
          required
        />
        {errors.confirmPassword && (
          <div
            className="hint"
            style={{ color: 'oklch(var(--destructive))' }}
            role="alert"
          >
            {errors.confirmPassword}
          </div>
        )}
      </div>

      {/* Terms checkbox — mockup lines 159-164 */}
      <div
        className="row"
        style={{ marginBottom: 16, alignItems: 'flex-start', gap: 8, display: 'flex' }}
      >
        <input
          type="checkbox"
          checked={info.acceptedTerms}
          onChange={(e) =>
            onChange({ ...info, acceptedTerms: e.target.checked })
          }
          disabled={isPending}
          style={{ marginTop: 3 }}
          aria-describedby="terms-description"
        />
        <span
          id="terms-description"
          style={{
            fontSize: 12.5,
            lineHeight: 1.5,
            color: 'oklch(var(--muted-foreground))',
          }}
        >
          I agree to the{' '}
          <a
            href="#"
            style={{ color: 'oklch(var(--accent))' }}
            onClick={(e) => e.preventDefault()}
          >
            Terms of Use
          </a>{' '}
          and{' '}
          <a
            href="#"
            style={{ color: 'oklch(var(--accent))' }}
            onClick={(e) => e.preventDefault()}
          >
            Privacy Policy
          </a>{' '}
          · I understand my queries are logged for evaluation (Langfuse) and
          visible only to me.
        </span>
      </div>
      {errors.acceptedTerms && (
        <div
          className="hint"
          style={{
            color: 'oklch(var(--destructive))',
            marginTop: -10,
            marginBottom: 12,
          }}
          role="alert"
        >
          {errors.acceptedTerms}
        </div>
      )}

      {/* Submit — mockup lines 166-168 */}
      <button
        type="submit"
        className="btn btn-accent btn-lg"
        style={{ width: '100%', justifyContent: 'center' }}
        disabled={!isFormValid || isPending}
      >
        {isPending ? (
          <>
            <Loader2 className="animate-spin" size={14} />
            Creating account…
          </>
        ) : (
          'Create account →'
        )}
      </button>

      {/* Sign-in link — mockup lines 170-172 */}
      <div
        style={{
          textAlign: 'center',
          marginTop: 18,
          fontSize: 13,
          color: 'oklch(var(--muted-foreground))',
        }}
      >
        Already have an account?{' '}
        <Link
          href="/login"
          style={{
            color: 'oklch(var(--accent))',
            fontWeight: 500,
            textDecoration: 'none',
          }}
        >
          Sign in
        </Link>
      </div>
    </form>
  );
}

// ──────────────────────────────────────────────────────────────────────────
// Step 2 — Email verify (6-digit code, backend wins per CLAUDE.md §13)
// Mockup visual treatment lifted from `ekp-page-auth.jsx:72-130`; the
// "click the link" copy is REPLACED by the 6-digit code form.
// ──────────────────────────────────────────────────────────────────────────

function Step2({
  email,
  code,
  isPending,
  resendCooldown,
  onCodeChange,
  onResend,
  onSubmit,
  onBack,
}: {
  email: string;
  code: string[];
  isPending: boolean;
  resendCooldown: number;
  onCodeChange: (next: string[]) => void;
  onResend: () => void;
  onSubmit: (e: FormEvent<HTMLFormElement>) => void;
  onBack: () => void;
}) {
  const inputsRef = useRef<Array<HTMLInputElement | null>>([]);

  useEffect(() => {
    inputsRef.current[0]?.focus();
  }, []);

  function handleBoxChange(idx: number, e: ChangeEvent<HTMLInputElement>) {
    const raw = e.target.value;
    const digit = raw.replace(/\D/g, '').slice(-1);
    if (!digit && raw) return;
    const next = [...code];
    next[idx] = digit;
    onCodeChange(next);
    if (digit && idx < CODE_LENGTH - 1) {
      inputsRef.current[idx + 1]?.focus();
    }
  }

  function handleBoxKeyDown(idx: number, e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Backspace' && !code[idx] && idx > 0) {
      inputsRef.current[idx - 1]?.focus();
    } else if (e.key === 'ArrowLeft' && idx > 0) {
      inputsRef.current[idx - 1]?.focus();
    } else if (e.key === 'ArrowRight' && idx < CODE_LENGTH - 1) {
      inputsRef.current[idx + 1]?.focus();
    }
  }

  function handlePaste(e: ClipboardEvent<HTMLInputElement>) {
    const pasted = e.clipboardData.getData('text').replace(/\D/g, '');
    if (pasted.length === 0) return;
    e.preventDefault();
    const next = Array(CODE_LENGTH).fill('');
    for (let i = 0; i < Math.min(pasted.length, CODE_LENGTH); i += 1) {
      next[i] = pasted[i];
    }
    onCodeChange(next);
    const lastFilledIdx = Math.min(pasted.length, CODE_LENGTH) - 1;
    inputsRef.current[lastFilledIdx]?.focus();
  }

  const isCodeComplete = code.every((c) => c.length === 1);

  return (
    <form onSubmit={onSubmit}>
      {/* Centred icon + heading — mockup lines 75-91 */}
      <div style={{ textAlign: 'center', padding: '12px 0 24px' }}>
        <div
          style={{
            width: 56,
            height: 56,
            borderRadius: '50%',
            background: 'oklch(var(--accent) / 0.12)',
            color: 'oklch(var(--accent))',
            display: 'grid',
            placeItems: 'center',
            margin: '0 auto 16px',
          }}
        >
          <Inbox size={26} />
        </div>
        <h1
          style={{
            fontSize: 22,
            fontWeight: 600,
            letterSpacing: '-0.018em',
            margin: 0,
            marginBottom: 8,
          }}
        >
          Check your inbox
        </h1>
        <p
          style={{
            fontSize: 14,
            color: 'oklch(var(--muted-foreground))',
            lineHeight: 1.55,
            margin: 0,
            maxWidth: 320,
            marginLeft: 'auto',
            marginRight: 'auto',
          }}
        >
          We sent a 6-digit code to{' '}
          <b style={{ color: 'oklch(var(--foreground))' }}>{email}</b>. Enter
          it below to activate your account.
        </p>
      </div>

      {/* 6-digit code input — EKP backend wins (replaces mockup's "click the link" copy) */}
      <div className="field" style={{ alignItems: 'center' }}>
        <label
          className="label"
          style={{ textAlign: 'center', width: '100%' }}
        >
          Verification code
        </label>
        <div
          style={{
            display: 'flex',
            justifyContent: 'center',
            gap: 8,
            marginTop: 4,
          }}
        >
          {code.map((digit, idx) => (
            <input
              key={idx}
              ref={(el) => {
                inputsRef.current[idx] = el;
              }}
              className="input"
              type="text"
              inputMode="numeric"
              autoComplete="one-time-code"
              maxLength={1}
              value={digit}
              onChange={(e) => handleBoxChange(idx, e)}
              onKeyDown={(e) => handleBoxKeyDown(idx, e)}
              onPaste={idx === 0 ? handlePaste : undefined}
              disabled={isPending}
              aria-label={`Digit ${idx + 1}`}
              style={{
                width: 44,
                height: 48,
                textAlign: 'center',
                fontFamily: 'var(--font-mono)',
                fontSize: 18,
                padding: 0,
              }}
            />
          ))}
        </div>
      </div>

      {/* What happens next mono block — mockup lines 93-108, adapted for 6-digit flow */}
      <div
        style={{
          padding: '12px 14px',
          background: 'oklch(var(--muted) / 0.4)',
          border: '1px solid oklch(var(--border))',
          borderRadius: 'var(--radius-sm)',
          marginBottom: 16,
        }}
      >
        <div
          className="text-xs muted mono"
          style={{
            marginBottom: 4,
            letterSpacing: '0.04em',
            textTransform: 'uppercase',
          }}
        >
          What happens next
        </div>
        <ol
          style={{
            margin: 0,
            paddingLeft: 18,
            fontSize: 12.5,
            lineHeight: 1.7,
            color: 'oklch(var(--foreground))',
          }}
        >
          <li>Enter the 6-digit code (expires in 24h)</li>
          <li>
            You&apos;ll be auto-signed in and routed to{' '}
            <span className="mono">/dashboard</span>
          </li>
          <li>
            Your workspace is <b>Ricoh · RAPO</b> (Beta cohort)
          </li>
        </ol>
      </div>

      {/* Verify submit */}
      <button
        type="submit"
        className="btn btn-accent btn-lg"
        style={{ width: '100%', justifyContent: 'center', marginBottom: 8 }}
        disabled={!isCodeComplete || isPending}
      >
        {isPending ? (
          <>
            <Loader2 className="animate-spin" size={14} />
            Verifying…
          </>
        ) : (
          'Verify email →'
        )}
      </button>

      {/* Resend — mockup lines 110-112 */}
      <button
        type="button"
        className="btn btn-secondary"
        style={{ width: '100%', justifyContent: 'center', marginBottom: 8, gap: 6 }}
        onClick={onResend}
        disabled={resendCooldown > 0 || isPending}
      >
        <RefreshCw size={13} />
        {resendCooldown > 0
          ? `Resend in ${resendCooldown}s`
          : 'Resend verification code'}
      </button>

      {/* Back — mockup lines 113-115 */}
      <button
        type="button"
        className="btn btn-ghost btn-sm"
        style={{ width: '100%', justifyContent: 'center', gap: 6 }}
        onClick={onBack}
        disabled={isPending}
      >
        <ArrowLeft size={13} /> Change email
      </button>

      {/* ACS footer block — mockup lines 117-128 */}
      <div
        style={{
          marginTop: 18,
          padding: '10px 12px',
          border: '1px dashed oklch(var(--border-strong))',
          borderRadius: 'var(--radius-sm)',
          fontSize: 11,
          color: 'oklch(var(--muted-foreground))',
          lineHeight: 1.55,
          fontFamily: 'var(--font-mono)',
        }}
      >
        Powered by{' '}
        <b style={{ color: 'oklch(var(--foreground))' }}>
          Azure Communication Services
        </b>{' '}
        (C13 Email Verification Service · architecture.md v6 §3.7). Dev mode
        falls back to <span className="mono">ConsoleEmailProvider</span>.
      </div>
    </form>
  );
}

// ──────────────────────────────────────────────────────────────────────────
// Step 3 — Welcome (post-verify success;preserved W20 pattern)
// ──────────────────────────────────────────────────────────────────────────

function Step3({
  displayName,
  onContinue,
}: {
  displayName: string;
  onContinue: () => void;
}) {
  return (
    <div>
      <div style={{ textAlign: 'center', padding: '12px 0 24px' }}>
        <div
          style={{
            width: 56,
            height: 56,
            borderRadius: '50%',
            background: 'oklch(var(--success) / 0.15)',
            color: 'oklch(var(--success))',
            display: 'grid',
            placeItems: 'center',
            margin: '0 auto 16px',
          }}
        >
          <PartyPopper size={26} />
        </div>
        <h1
          style={{
            fontSize: 22,
            fontWeight: 600,
            letterSpacing: '-0.018em',
            margin: 0,
            marginBottom: 8,
          }}
        >
          Welcome, {displayName || 'friend'}!
        </h1>
        <p
          style={{
            fontSize: 14,
            color: 'oklch(var(--muted-foreground))',
            lineHeight: 1.55,
            margin: 0,
            maxWidth: 320,
            marginLeft: 'auto',
            marginRight: 'auto',
          }}
        >
          Your account is ready. Head to your dashboard to get started.
        </p>
      </div>

      <div
        style={{
          padding: '12px 14px',
          background: 'oklch(var(--muted) / 0.4)',
          border: '1px solid oklch(var(--border))',
          borderRadius: 'var(--radius-sm)',
          marginBottom: 16,
        }}
      >
        <div
          className="text-xs muted mono"
          style={{
            marginBottom: 6,
            letterSpacing: '0.04em',
            textTransform: 'uppercase',
          }}
        >
          Default knowledge base
        </div>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '8px 10px',
            background: 'oklch(var(--muted))',
            borderRadius: 'var(--radius-sm)',
            opacity: 0.7,
            cursor: 'default',
          }}
          aria-disabled="true"
          title="Multi-KB selector — Tier 1 ships with a single shared KB per Q7 default"
        >
          <span className="mono" style={{ fontSize: 13 }}>
            drive_user_manuals
          </span>
          <span
            className="badge badge-muted"
            style={{ fontSize: 9.5 }}
          >
            Tier 2
          </span>
        </div>
        <div
          style={{
            fontSize: 11.5,
            color: 'oklch(var(--muted-foreground))',
            marginTop: 8,
          }}
        >
          Multi-KB selection arrives later — Tier 1 ships with a single shared KB.
        </div>
      </div>

      <button
        type="button"
        className="btn btn-accent btn-lg"
        style={{ width: '100%', justifyContent: 'center' }}
        onClick={onContinue}
      >
        Go to your dashboard →
      </button>
    </div>
  );
}

// ──────────────────────────────────────────────────────────────────────────
// Validation + error handling (preserved from W20 F7.2)
// ──────────────────────────────────────────────────────────────────────────

function validateAccountInfo(info: AccountInfo): Record<string, string> {
  const errors: Record<string, string> = {};
  if (!info.displayName.trim()) errors.displayName = 'Required.';

  if (!info.email) errors.email = 'Required.';
  else if (!EMAIL_PATTERN.test(info.email))
    errors.email = 'Invalid email format.';

  if (!info.password) errors.password = 'Required.';
  else if (info.password.length < 8) errors.password = 'Min 8 characters.';
  else if (!/[A-Z]/.test(info.password))
    errors.password = 'Must include an uppercase letter.';
  else if (!/[\d!@#$%^&*]/.test(info.password))
    errors.password = 'Must include a digit or symbol.';

  if (!info.confirmPassword) errors.confirmPassword = 'Required.';
  else if (info.confirmPassword !== info.password)
    errors.confirmPassword = 'Passwords do not match.';

  if (!info.acceptedTerms)
    errors.acceptedTerms = 'Accept the Terms of Use and Privacy Policy to continue.';

  return errors;
}

function handleRegisterError(err: unknown): void {
  if (err instanceof ApiError) {
    if (err.code === AuthErrorCodes.EMAIL_ALREADY_EXISTS) {
      toast.error('An account with that email already exists.', {
        description: err.actionableHint ?? 'Sign in instead, or use a different email.',
      });
    } else if (err.code === AuthErrorCodes.INVALID_EMAIL) {
      toast.error('Email format is invalid.');
    } else if (err.code === AuthErrorCodes.WEAK_PASSWORD) {
      toast.error(err.message);
    } else {
      toast.error(err.message, { description: err.actionableHint ?? undefined });
    }
    return;
  }
  toast.error('Registration failed.', {
    description: err instanceof Error ? err.message : String(err),
  });
}

function handleVerifyError(err: unknown): void {
  if (err instanceof ApiError) {
    if (err.code === AuthErrorCodes.VERIFICATION_EXPIRED) {
      toast.error('Verification code has expired.', {
        description: err.actionableHint ?? 'Request a new code via Resend.',
      });
    } else if (err.code === AuthErrorCodes.VERIFICATION_FAILED) {
      toast.error('Verification code is incorrect.');
    } else {
      toast.error(err.message);
    }
    return;
  }
  toast.error('Verification failed.', {
    description: err instanceof Error ? err.message : String(err),
  });
}

function handleResendError(err: unknown): void {
  if (err instanceof ApiError && err.code === AuthErrorCodes.RESEND_RATE_LIMITED) {
    toast.error('Resend rate limit hit.', {
      description: err.actionableHint ?? 'Wait a bit before trying again.',
    });
    return;
  }
  toast.error('Resend failed.', {
    description: err instanceof Error ? err.message : String(err),
  });
}
