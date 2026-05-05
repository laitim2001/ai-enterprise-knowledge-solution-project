'use client';

/**
 * App Router root error UI (Next.js 14 convention) — W7 D4 F4.2.
 * Catches client-side rendering errors and unhandled API failures bubbled up
 * past the route segment. NO browser default error page reached.
 */

import { ErrorBoundaryView } from '@/components/error/error-boundary';

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return <ErrorBoundaryView error={error} reset={reset} scope="EKP" />;
}
