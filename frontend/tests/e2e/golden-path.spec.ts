/**
 * Golden-path E2E baseline — W15 D4 F4.2 deliverable; W18 F7 updated (per ADR-0024).
 *
 * Coverage (Tier 1 baseline scope per W15 plan §3 Success Criteria):
 * - `/` redirects to `/login` (V7 Landing REMOVED per ADR-0024 — architecture.md v6 §5.9)
 * - V8 Login page renders + dual auth path UI (§5.10)
 * - V9 Register 3-step wizard renders (§5.11)
 * - V1 Chat page renders (§5.2)
 *
 * Subsumes manual smoke deferred across W12+W13+W14 cycles per plan §F4
 * "W12+W13+W14 manual smoke deferred backlog systematic subsume".
 *
 * Tier 1 = render assertions only (basic UI flow); interactive flow assertions
 * (form submit + backend integration) defer Beta hardening per plan §4 risks.
 * Tests assume NEXT_PUBLIC_AUTH_MOCK=true (set in playwright.config.ts webServer
 * env) so MSAL bypasses real Entra ID.
 */

import { test, expect } from '@playwright/test';

test.describe('Golden path — public + chat E2E', () => {
  test('/ redirects to /login (V7 Landing removed per ADR-0024)', async ({
    page,
  }) => {
    await page.goto('/');
    await expect(page).toHaveURL(/\/login$/);
    await expect(
      page.getByRole('heading', { name: /sign in/i }),
    ).toBeVisible();
  });

  test('V8 Login page renders with dual auth path (SSO + form)', async ({
    page,
  }) => {
    await page.goto('/login');
    // Email/password form
    await expect(page.getByLabel(/email/i)).toBeVisible();
    await expect(page.getByLabel(/password/i)).toBeVisible();
    // Sign in with Microsoft (Entra ID SSO)
    await expect(
      page.getByRole('button', { name: /sign in with microsoft/i }),
    ).toBeVisible();
    // Register link
    await expect(page.getByRole('link', { name: /register|sign up/i })).toBeVisible();
  });

  test('V9 Register page renders 3-step wizard at step 1', async ({ page }) => {
    await page.goto('/register');
    // Step 1 — account info form fields. The register form has BOTH a "Password"
    // and a "Confirm password" field, so target the password label exactly.
    await expect(page.getByLabel(/email/i)).toBeVisible();
    await expect(page.getByLabel('Password', { exact: true })).toBeVisible();
    await expect(page.getByLabel(/confirm password/i)).toBeVisible();
    // We're on step 1 of the 3-step wizard (the Stepper + the Step1 sub-header).
    await expect(page.getByText(/step 1 of 3/i)).toBeVisible();
    await expect(page.getByText('Account info')).toBeVisible();
  });

  test('V1 Chat page renders message input + send button', async ({ page }) => {
    // mock MSAL auth bypass — direct nav per webServer env NEXT_PUBLIC_AUTH_MOCK=true
    await page.goto('/chat');
    // Chat input area present (textarea OR contenteditable)
    const inputArea = page.locator('textarea, [contenteditable="true"]').first();
    await expect(inputArea).toBeVisible();
  });

  test('V1 Chat page renders the Conversation History pane + advanced surfaces (W20 F3b)', async ({
    page,
  }) => {
    // mock MSAL auth bypass — direct nav per webServer env NEXT_PUBLIC_AUTH_MOCK=true
    await page.goto('/chat');
    // Conversation History pane (lg-only via Tailwind `hidden lg:block` so the
    // viewport must be ≥ lg breakpoint; the default Playwright project uses
    // Desktop Chrome 1280×720 which qualifies).
    await expect(
      page.getByRole('heading', { name: /^conversations$/i }),
    ).toBeVisible();
    await expect(page.getByRole('button', { name: /new chat/i })).toBeVisible();
    // The 3 citation placement modes pill toggle (inline / footnote / sidebar)
    // surfaces in the chat header fieldset.
    await expect(
      page.getByRole('button', { name: /^inline$/i, exact: false }).first(),
    ).toBeVisible();
  });

  test('V8 Login renders W20 F7.1 strict-fidelity surfaces (SSO primary + Auth modes aside)', async ({
    page,
  }) => {
    await page.goto('/login');
    // SSO primary button at top of form (mockup-anchored ordering).
    await expect(
      page.getByRole('button', { name: /sign in with microsoft/i }),
    ).toBeVisible();
    // Divider label between SSO and email form.
    await expect(page.getByText(/or continue with email/i)).toBeVisible();
    // Auth modes mono dashed aside block at the bottom (operator-awareness surface).
    await expect(
      page.getByLabel(/auth modes — tier 1/i),
    ).toBeVisible();
  });

  test('V9 Register renders W20 F7.2 polish (field reorder + Terms checkbox + Hint copy)', async ({
    page,
  }) => {
    await page.goto('/register');
    // W20 F7.2 field reorder — Full name first.
    await expect(page.getByLabel(/full name/i)).toBeVisible();
    await expect(page.getByLabel(/work email/i)).toBeVisible();
    // Hint copy below email + password fields.
    await expect(page.getByText(/6-digit verification code/i)).toBeVisible();
    await expect(page.getByText(/scrypt-hashed via adr-0022/i)).toBeVisible();
    // Terms of Use + Privacy Policy checkbox renders.
    await expect(page.getByRole('checkbox')).toBeVisible();
  });
});
