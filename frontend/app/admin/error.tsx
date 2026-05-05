'use client';

/**
 * /admin segment error UI — W7 D4 F4.2 scoped boundary for C09 Admin views.
 * Catches errors inside KB list / KB detail / Eval Console without
 * tearing down the parent admin shell or auth state.
 */

import { ErrorBoundaryView } from '@/components/error/error-boundary';

export default function AdminError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return <ErrorBoundaryView error={error} reset={reset} scope="Admin" />;
}
