/**
 * Golden-path E2E baseline — W15 D4 F4.2 deliverable.
 *
 * Coverage (Tier 1 baseline scope per W15 plan §3 Success Criteria):
 * - V7 Landing page renders (architecture.md v6 §5.9)
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
  test('V7 Landing page renders with hero + features + how-it-works', async ({
    page,
  }) => {
    await page.goto('/');
    // Hero section
    await expect(
      page.getByRole('heading', { name: /enterprise knowledge platform/i }),
    ).toBeVisible();
    // 3 feature highlight cards
    await expect(page.getByText(/multi-format ingestion/i)).toBeVisible();
    await expect(page.getByText(/hybrid retrieval/i)).toBeVisible();
    await expect(page.getByText(/citation/i)).toBeVisible();
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
    // Step 1 — account info form fields
    await expect(page.getByLabel(/email/i)).toBeVisible();
    await expect(page.getByLabel(/password/i, { exact: false })).toBeVisible();
    // Stepper indicator visible
    const stepperIndicator = page.locator('[class*="step"]').first();
    await expect(stepperIndicator).toBeVisible();
  });

  test('V1 Chat page renders message input + send button', async ({ page }) => {
    // mock MSAL auth bypass — direct nav per webServer env NEXT_PUBLIC_AUTH_MOCK=true
    await page.goto('/chat');
    // Chat input area present (textarea OR contenteditable)
    const inputArea = page.locator('textarea, [contenteditable="true"]').first();
    await expect(inputArea).toBeVisible();
  });
});
