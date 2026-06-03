/**
 * Hydration-integrity regression harness — BUG-032 follow-up (2026-06-03).
 *
 * Asserts that directly full-loading the SSR-rendered routes produces ZERO React
 * hydration errors in the browser console. This is the automated net for BUG-032
 * (and the same class as BUG-023): a `next-themes`-driven theme-toggle icon read
 * `resolvedTheme` during render without a mounted guard, so the server rendered
 * `<Layers>` while a dark-mode client hydrated `<Sparkles>` → SVG path mismatch →
 * React discarded the whole server tree (11 console errors on /login). The fix
 * added a mounted guard so the first client render matches the server HTML.
 *
 * Why `colorScheme: 'dark'` (test.use below): the root layout is
 * `defaultTheme="system" enableSystem` (app/layout.tsx), so the client only
 * resolves a theme that DIFFERS from the SSR default (`undefined` → light icon)
 * when the emulated system preference is dark. Under light there is no mismatch
 * to detect — so emulating dark is what makes this test able to FAIL before the
 * fix (verified by temporarily reverting the guard: 2/3 routes errored) and PASS
 * after it. `<html suppressHydrationWarning>` only silences the html-attribute
 * diff next-themes injects; it does NOT cover deep component icon mismatches,
 * which is exactly what BUG-032 was.
 *
 * Routes cover both changed files:
 *   - /login + /register  → components/auth/auth-frame.tsx (shared AuthFrame)
 *   - /dashboard          → components/nav/theme-toggle.tsx (AppShell)
 *
 * Run (per tests/e2e/README.md): `PW_CHANNEL=chrome pnpm test:e2e`. Mock MSAL is
 * enabled via playwright.config.ts webServer env so /dashboard renders without a
 * real Entra ID round-trip; backend-unreachable network errors are filtered out
 * (only hydration-signature messages are asserted on).
 */

import { test, expect, type ConsoleMessage, type Page } from '@playwright/test';

// Narrow signatures of React/Next hydration failures. Deliberately specific so
// unrelated dev-console noise (fast-refresh notices, backend-unreachable fetch
// errors when uvicorn is down) never produces a false positive.
const HYDRATION_ERROR_PATTERNS: RegExp[] = [
  /hydration failed/i,
  /did not match/i, // "Prop `d` did not match" — BUG-032 signature
  /error while hydrating/i,
  /text content does not match/i,
  /cannot be a descendant of/i, // "<div> cannot be a descendant of <p>" — BUG-023 class
];

function isHydrationError(text: string): boolean {
  return HYDRATION_ERROR_PATTERNS.some((re) => re.test(text));
}

/**
 * Attach console + pageerror listeners BEFORE navigation so the first hydration
 * pass — which runs immediately after the initial server HTML loads — is
 * captured. Returns the mutable sink the test asserts on.
 */
function captureHydrationErrors(page: Page): string[] {
  const errors: string[] = [];
  page.on('console', (msg: ConsoleMessage) => {
    if (msg.type() === 'error' && isHydrationError(msg.text())) {
      errors.push(msg.text());
    }
  });
  page.on('pageerror', (err) => {
    if (isHydrationError(err.message)) errors.push(err.message);
  });
  return errors;
}

const SSR_ROUTES = [
  { path: '/login', surface: 'auth-frame theme toggle' },
  { path: '/register', surface: 'auth-frame theme toggle (shared AuthFrame)' },
  { path: '/dashboard', surface: 'AppShell nav/theme-toggle' },
] as const;

test.describe('Hydration integrity — SSR routes emit zero hydration errors (BUG-032)', () => {
  // Emulate a dark system preference so the client resolves a theme that differs
  // from the SSR default — the only condition under which the BUG-032 mismatch
  // surfaces (see file header).
  test.use({ colorScheme: 'dark' });

  for (const { path, surface } of SSR_ROUTES) {
    test(`${path} full-load has no hydration mismatch — ${surface}`, async ({
      page,
    }) => {
      const hydrationErrors = captureHydrationErrors(page);
      // Direct full-load (not client-side nav) so the SSR → client hydration
      // pass actually runs. Default waitUntil:'load' (not networkidle) so a
      // down backend doesn't stall the wait — we filter network errors anyway.
      await page.goto(path);
      // Hydration + the post-mount theme re-render flush just after first paint;
      // give React a beat before asserting.
      await page.waitForTimeout(800);

      expect(
        hydrationErrors,
        `Unexpected hydration errors on ${path}:\n${
          hydrationErrors.join('\n---\n') || '(none)'
        }`,
      ).toEqual([]);
    });
  }
});
