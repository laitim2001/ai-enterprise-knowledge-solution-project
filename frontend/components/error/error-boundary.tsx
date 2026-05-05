'use client';

/**
 * C09 + C10 — W7 D4 F4.2 UI error boundary.
 *
 * Renders a user-friendly error card with retry + report CTAs. Surfaces the
 * backend ApiError envelope (F4.1) when available — `code` / `message` /
 * `actionable_hint` map to title / body / hint respectively. Generic
 * fallback shown when the error lacks the envelope (e.g. network failure).
 */

import { ApiError } from '@/lib/api-client';

export interface ErrorBoundaryViewProps {
  error: Error & { digest?: string };
  reset?: () => void;
  scope?: string;
}

const REPORT_URL = 'https://github.com/anthropics/claude-code/issues'; // W8: replace with EKP support channel

export function ErrorBoundaryView({
  error,
  reset,
  scope,
}: ErrorBoundaryViewProps) {
  const isApiError = error instanceof ApiError;
  const code = isApiError ? error.code : 'frontend.unhandled';
  const message = error.message || 'An unexpected error occurred.';
  const hint = isApiError ? error.actionableHint : null;
  const status = isApiError ? error.status : null;

  return (
    <div
      role="alert"
      className="mx-auto my-12 max-w-xl rounded-lg border border-[oklch(0.88_0.04_25)] bg-[oklch(0.98_0.02_25)] p-6 text-sm"
    >
      <div className="mb-2 flex items-baseline justify-between">
        <h2 className="text-base font-semibold text-[oklch(0.45_0.18_25)]">
          {scope ? `${scope} — ` : ''}Something went wrong
        </h2>
        <code className="text-xs text-[oklch(0.55_0_0)]">
          {code}
          {status ? ` (${status})` : ''}
        </code>
      </div>
      <p className="mb-3">{message}</p>
      {hint ? (
        <p className="mb-4 text-[oklch(0.45_0_0)]">
          <strong>Next step:</strong> {hint}
        </p>
      ) : null}
      <div className="flex flex-wrap gap-2">
        {reset ? (
          <button
            type="button"
            onClick={() => reset()}
            className="rounded border border-[oklch(0.45_0.18_25)] bg-[oklch(0.98_0_0)] px-4 py-1.5 text-xs hover:bg-[oklch(0.94_0_0)]"
          >
            Retry
          </button>
        ) : null}
        <a
          href={REPORT_URL}
          target="_blank"
          rel="noopener noreferrer"
          className="rounded border border-[oklch(0.92_0_0)] px-4 py-1.5 text-xs hover:bg-[oklch(0.94_0_0)]"
        >
          Report
        </a>
      </div>
    </div>
  );
}
