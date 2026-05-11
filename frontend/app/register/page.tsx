'use client';

/**
 * V9 Register page (`/register`) — public entry per architecture.md v6 §5.11 + ADR-0014.
 *
 * 3-step wizard: Account info → Email verify → Welcome.
 *
 * W13 D5 cont CO_F5d: auth wire deferral resolved — F5 backend cascade landed
 * (commit 054679d). Step submit handlers POST to /auth/register +
 * /auth/verify-email; resend hits /auth/resend-verification. Error.code from
 * the ApiError envelope drives toast variants per F4.7 acceptance.
 *
 * Layout: V8 BrandPanel (shared) left + form area right (split via flex-col
 * md:flex-row). Stepper visual pattern parallel to W12 F4.9 Pipeline wizard
 * (active/done/pending state machine) — inlined per Karpathy §1.2 simplicity-
 * first; rule-of-3 pending if a 4th wizard usage emerges, extract to shared
 * `frontend/components/ui/stepper.tsx`.
 *
 * Step 2 6-digit verification code input: 6 separate boxes with auto-advance
 * focus + paste distribution (industry-standard verification UX per design ref
 * §2.9 wireframe).
 *
 * Step 3 first-KB selector disabled per Q7 default Tier 1 single-KB POC.
 *
 * W18 F7 (per ADR-0024): Step 3's CTA routes to `/dashboard` (the new post-login
 * home) instead of `/chat` — the verify-email auto-login (ADR-0022) means Step 3
 * lands authenticated, so /dashboard resolves inside <AppShell>. The register
 * page itself stays OUTSIDE `app/(app)/` (no app chrome — BrandPanel split layout).
 */

import {
  ArrowLeft,
  CheckCircle2,
  Loader2,
  MailCheck,
  PartyPopper,
} from 'lucide-react';
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

import { BrandPanel } from '@/components/auth/brand-panel';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { ApiError } from '@/lib/api-client';
import { AuthErrorCodes, authApi } from '@/lib/api/auth';
import { cn } from '@/lib/utils';

const RESEND_COOLDOWN_SEC = 60;
const CODE_LENGTH = 6;

type Step = 1 | 2 | 3;

interface AccountInfo {
  email: string;
  password: string;
  confirmPassword: string;
  displayName: string;
}

const EMPTY_INFO: AccountInfo = {
  email: '',
  password: '',
  confirmPassword: '',
  displayName: '',
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
    <div className="flex min-h-screen flex-col md:flex-row">
      <BrandPanel />
      <main className="flex flex-1 flex-col items-center justify-center bg-background px-6 py-12">
        <div className="w-full max-w-md">
          <Stepper current={step} />

          <div className="mt-8">
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
              <Step3
                displayName={info.displayName}
                onContinue={handleGoToDashboard}
              />
            )}
          </div>

          {step !== 3 && (
            <p className="mt-6 text-center text-xs text-muted-foreground">
              Already have an account?{' '}
              <Link
                href="/login"
                className="text-foreground transition-colors hover:text-accent hover:underline"
              >
                Sign in
              </Link>
            </p>
          )}
        </div>
      </main>
    </div>
  );
}

function validateAccountInfo(info: AccountInfo): Record<string, string> {
  const errors: Record<string, string> = {};
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

  if (!info.displayName.trim()) errors.displayName = 'Required.';

  return errors;
}

function passwordStrength(password: string): { label: string; score: number } {
  let score = 0;
  if (password.length >= 8) score += 1;
  if (password.length >= 12) score += 1;
  if (/[A-Z]/.test(password)) score += 1;
  if (/\d/.test(password)) score += 1;
  if (/[!@#$%^&*]/.test(password)) score += 1;

  const labels = ['Too short', 'Weak', 'Fair', 'Good', 'Strong', 'Very strong'];
  return { label: labels[Math.min(score, labels.length - 1)] ?? 'Strong', score };
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

function Stepper({ current }: { current: Step }) {
  const steps = [
    { id: 1, label: 'Account info' },
    { id: 2, label: 'Email verify' },
    { id: 3, label: 'Welcome' },
  ] as const;

  return (
    <ol className="flex items-center gap-2 text-xs font-medium uppercase tracking-wide">
      {steps.map((s, idx) => {
        const isActive = s.id === current;
        const isDone = s.id < current;
        return (
          <li key={s.id} className="flex flex-1 items-center gap-2">
            <span
              className={cn(
                'flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-[11px]',
                isActive
                  ? 'bg-primary text-primary-foreground'
                  : isDone
                    ? 'bg-success text-success-foreground'
                    : 'border border-border text-muted-foreground',
              )}
            >
              {isDone ? '✓' : s.id}
            </span>
            <span
              className={cn(
                'hidden sm:inline',
                isActive ? 'text-foreground' : 'text-muted-foreground',
              )}
            >
              {s.label}
            </span>
            {idx < steps.length - 1 && (
              <span className="ml-2 flex-1 border-t border-dashed border-border" />
            )}
          </li>
        );
      })}
    </ol>
  );
}

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
  const strength = passwordStrength(info.password);
  const showStrength = info.password.length > 0;
  const isFormValid = Object.keys(errors).length === 0;

  return (
    <form onSubmit={onSubmit} className="space-y-4">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Create account</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Step 1 of 3 — set up your credentials.
        </p>
      </header>

      <Field label="Email" htmlFor="reg-email" error={errors.email}>
        <Input
          id="reg-email"
          type="email"
          autoComplete="email"
          placeholder="you@example.com"
          value={info.email}
          onChange={(e) => onChange({ ...info, email: e.target.value })}
          disabled={isPending}
          required
        />
      </Field>

      <Field label="Password" htmlFor="reg-password" error={errors.password}>
        <Input
          id="reg-password"
          type="password"
          autoComplete="new-password"
          value={info.password}
          onChange={(e) => onChange({ ...info, password: e.target.value })}
          disabled={isPending}
          required
        />
        {showStrength && (
          <div className="mt-2 space-y-1">
            <div className="flex h-1 gap-1">
              {Array.from({ length: 5 }).map((_, i) => (
                <span
                  key={i}
                  className={cn(
                    'flex-1 rounded-full',
                    i < strength.score ? 'bg-accent' : 'bg-muted',
                  )}
                />
              ))}
            </div>
            <p className="text-xs text-muted-foreground">
              Strength: <span className="text-foreground">{strength.label}</span>
            </p>
          </div>
        )}
      </Field>

      <Field
        label="Confirm password"
        htmlFor="reg-confirm-password"
        error={errors.confirmPassword}
      >
        <Input
          id="reg-confirm-password"
          type="password"
          autoComplete="new-password"
          value={info.confirmPassword}
          onChange={(e) =>
            onChange({ ...info, confirmPassword: e.target.value })
          }
          disabled={isPending}
          required
        />
      </Field>

      <Field
        label="Display name"
        htmlFor="reg-display-name"
        error={errors.displayName}
      >
        <Input
          id="reg-display-name"
          autoComplete="name"
          placeholder="Chris L."
          value={info.displayName}
          onChange={(e) => onChange({ ...info, displayName: e.target.value })}
          disabled={isPending}
          required
        />
      </Field>

      <Button
        type="submit"
        className="w-full"
        disabled={!isFormValid || isPending}
      >
        {isPending ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            Creating account…
          </>
        ) : (
          <>Continue →</>
        )}
      </Button>
    </form>
  );
}

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
    <form onSubmit={onSubmit} className="space-y-6">
      <header className="flex flex-col items-center text-center">
        <span className="flex h-12 w-12 items-center justify-center rounded-full bg-accent/10 text-accent">
          <MailCheck className="h-6 w-6" />
        </span>
        <h1 className="mt-3 text-2xl font-semibold tracking-tight">
          Check your inbox
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          We sent a 6-digit code to{' '}
          <span className="font-medium text-foreground">{email}</span>
        </p>
      </header>

      <div className="space-y-2">
        <Label className="block text-center">Verification code</Label>
        <div className="flex justify-center gap-2">
          {code.map((digit, idx) => (
            <Input
              key={idx}
              ref={(el) => {
                inputsRef.current[idx] = el;
              }}
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
              className="h-12 w-10 text-center font-mono text-lg"
            />
          ))}
        </div>
      </div>

      <div className="flex items-center justify-between text-xs text-muted-foreground">
        <button
          type="button"
          onClick={onResend}
          disabled={resendCooldown > 0 || isPending}
          className="text-foreground transition-colors hover:text-accent disabled:cursor-not-allowed disabled:text-muted-foreground disabled:no-underline"
        >
          {resendCooldown > 0 ? `Resend (${resendCooldown}s)` : 'Resend code'}
        </button>
        <span>Didn&apos;t receive it? Check spam folder.</span>
      </div>

      <Button
        type="submit"
        className="w-full"
        disabled={!isCodeComplete || isPending}
      >
        {isPending ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            Verifying…
          </>
        ) : (
          <>Verify email →</>
        )}
      </Button>

      <Button
        type="button"
        variant="ghost"
        onClick={onBack}
        disabled={isPending}
        className="w-full"
      >
        <ArrowLeft className="mr-2 h-4 w-4" />
        Back to step 1
      </Button>
    </form>
  );
}

function Step3({
  displayName,
  onContinue,
}: {
  displayName: string;
  onContinue: () => void;
}) {
  return (
    <div className="space-y-6 text-center">
      <header className="flex flex-col items-center">
        <span className="flex h-14 w-14 items-center justify-center rounded-full bg-success/15 text-success">
          <PartyPopper className="h-7 w-7" />
        </span>
        <h1 className="mt-3 text-2xl font-semibold tracking-tight">
          Welcome, {displayName || 'friend'}!
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Your account is ready. Head to your dashboard to get started.
        </p>
      </header>

      <div className="rounded-md border border-dashed border-border bg-muted/30 p-4 text-left">
        <Label className="text-muted-foreground">Default knowledge base</Label>
        <div
          className="mt-2 flex cursor-not-allowed items-center justify-between rounded-sm border border-border bg-muted/40 px-3 py-2 text-sm opacity-70"
          title="Single-KB POC per Q7 Tier 1 default — multi-KB selector W7+ Beta"
        >
          <span className="font-mono">drive_user_manuals</span>
          <CheckCircle2 className="h-4 w-4 text-success" />
        </div>
        <p className="mt-2 text-xs text-muted-foreground">
          Multi-KB selection arrives later — Tier 1 ships with a single shared KB.
        </p>
      </div>

      <Button onClick={onContinue} size="lg" className="w-full">
        Go to your dashboard →
      </Button>
    </div>
  );
}

function Field({
  label,
  htmlFor,
  error,
  children,
}: {
  label: string;
  htmlFor: string;
  error?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-1.5">
      <Label htmlFor={htmlFor}>{label}</Label>
      {children}
      {error && <p className="text-xs text-destructive">{error}</p>}
    </div>
  );
}
