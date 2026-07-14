'use client';

/**
 * C09 + C10 — W7 D4 F4.2 UI error boundary.
 *
 * Renders a user-friendly error card with retry + report CTAs. Surfaces the
 * backend ApiError envelope (F4.1) when available — `code` / `message` /
 * `actionable_hint` map to title / body / hint respectively. Generic
 * fallback shown when the error lacks the envelope (e.g. network failure).
 *
 * W15 D3 F3.4 token cleanup — replaced 6 hardcoded oklch values with Tailwind
 * tokens (border-destructive/30, bg-destructive/10, text-destructive,
 * text-muted-foreground) per W12 D2 strict baseline + CO_W14_F4_error_boundary
 * carry-over from W14 retro deferred to W15 polish phase (Karpathy §1.3
 * surgical scope expansion warranted — broader token cleanup natural-fit for
 * W15 polish phase per W14 F4.3 audit deferral). Native `<button>` + `<a>`
 * replaced with shadcn Button + Button asChild for visual consistency with
 * admin UI + automatic dark mode + focus-visible ring (a11y).
 */

import { useTranslations } from 'next-intl';
import { Component, type ReactNode } from 'react';

import { Button } from '@/components/ui/button';
import { ApiError } from '@/lib/api-client';

export interface ErrorBoundaryViewProps {
  error: Error & { digest?: string };
  reset?: () => void;
  scope?: string;
}

// W8: replace with EKP support channel post Track A IT cred
const REPORT_URL = 'https://github.com/anthropics/claude-code/issues';

export function ErrorBoundaryView({
  error,
  reset,
  scope,
}: ErrorBoundaryViewProps) {
  const t = useTranslations('ErrorBoundary');
  const isApiError = error instanceof ApiError;
  const code = isApiError ? error.code : 'frontend.unhandled';
  const message = error.message || t('unexpectedError');
  const hint = isApiError ? error.actionableHint : null;
  const status = isApiError ? error.status : null;

  return (
    <div
      role="alert"
      className="mx-auto my-12 max-w-xl rounded-lg border border-destructive/30 bg-destructive/10 p-6 text-sm"
    >
      <div className="mb-2 flex items-baseline justify-between gap-3">
        <h2 className="text-base font-semibold text-destructive">
          {scope ? `${scope} — ` : ''}{t('somethingWentWrong')}
        </h2>
        <code className="font-mono text-xs text-muted-foreground">
          {code}
          {status ? ` (${status})` : ''}
        </code>
      </div>
      <p className="mb-3 text-foreground">{message}</p>
      {hint ? (
        <p className="mb-4 text-muted-foreground">
          <strong className="font-medium text-foreground">{t('nextStep')}</strong>{' '}
          {hint}
        </p>
      ) : null}
      <div className="flex flex-wrap gap-2">
        {reset ? (
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => reset()}
            className="border-destructive text-destructive hover:bg-destructive/10"
          >
            {t('retry')}
          </Button>
        ) : null}
        <Button asChild variant="outline" size="sm">
          <a href={REPORT_URL} target="_blank" rel="noopener noreferrer">
            {t('report')}
          </a>
        </Button>
      </div>
    </div>
  );
}

// ============================================================================
// ErrorBoundary — React error boundary class (W24b-wave-c2 F4)
// ============================================================================

interface ErrorBoundaryProps {
  children: ReactNode;
  /**
   * Renders the fallback UI. `reset` clears the caught error so `children`
   * re-mount — e.g. re-running a fetch that failed the first time.
   */
  fallback: (reset: () => void) => ReactNode;
}

interface ErrorBoundaryState {
  error: Error | null;
}

/**
 * Catches render-time errors in `children` and shows `fallback` instead of
 * letting them bubble to the route-level `error.tsx`. React offers no hook
 * equivalent — an error boundary must be a class component.
 *
 * Used by `/settings` to scope a thrown tab to that tab (W24b F4): one bad
 * tab shows a recoverable error state, the other five keep working.
 */
export class ErrorBoundary extends Component<
  ErrorBoundaryProps,
  ErrorBoundaryState
> {
  state: ErrorBoundaryState = { error: null };

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { error };
  }

  componentDidCatch(error: Error): void {
    // Console only — backend owns Langfuse trace correlation.
    console.error('[ErrorBoundary]', error);
  }

  private readonly reset = (): void => this.setState({ error: null });

  render(): ReactNode {
    if (this.state.error) return this.props.fallback(this.reset);
    return this.props.children;
  }
}
