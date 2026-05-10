'use client';

/**
 * Error UI for the app/(app)/ route group (W7 D4 F4.2 boundary; relocated W18 F3 per ADR-0024).
 * Catches errors inside any authenticated view (Dashboard / Chat / Knowledge Bases / Eval /
 * Traces / Settings) without tearing down the parent <AppShell> or auth state.
 */

import { ErrorBoundaryView } from '@/components/error/error-boundary';

export default function AppError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return <ErrorBoundaryView error={error} reset={reset} scope="App" />;
}
