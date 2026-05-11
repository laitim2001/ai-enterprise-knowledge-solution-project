/**
 * Visual baseline pixel diff harness — W15 D4 F4.4 deliverable; W18 F7 updated.
 *
 * Captures baseline screenshots for the representative views per Tier 1 scope:
 * - V8 Login (`/login`)
 * - V9 Register Step 1 (`/register`)
 * - Dashboard (`/dashboard` — real overview cards landed W18 F4; re-baseline on visual approval)
 * - V5 Eval Console (`/eval`)
 *
 * (V7 Landing's `/` baseline was dropped — the Landing page was REMOVED per
 * ADR-0024 W18 F7; `/` now just redirects to `/login`, already covered above.)
 *
 * V1 Chat / V3 KB List / V4 KB Detail / V6 Traces = covered by golden-path +
 * app-shell-path E2E render assertions (interactive flow tests). Pixel diff is
 * gated to stable layout views — empty state baselines avoid dynamic content
 * jitter (KB IDs / timestamps / failed_documents arrays would mask out).
 *
 * First run captures baseline:
 *   pnpm test:e2e:update-snapshots
 * Subsequent runs diff against baseline (1% maxDiffPixelRatio per
 * playwright.config.ts):
 *   pnpm test:e2e
 *
 * Baseline screenshots stored next to this file under:
 *   tests/e2e/visual-baseline.spec.ts-snapshots/
 * Per Playwright convention (Karpathy §1.2 simplicity — follow tool defaults
 * vs custom path; plan F4.4 literal "frontend/tests/e2e/screenshots/baseline/"
 * deviation noted in §7 changelog (D4) — Playwright auto-organizes snapshots
 * next to test file).
 */

import { test, expect } from '@playwright/test';

test.describe('Visual baseline — pixel diff harness', () => {
  test('V8 Login baseline', async ({ page }) => {
    await page.goto('/login');
    await expect(page.getByLabel(/email/i)).toBeVisible();
    await expect(page).toHaveScreenshot('v8-login.png', {
      fullPage: true,
    });
  });

  test('V9 Register Step 1 baseline', async ({ page }) => {
    await page.goto('/register');
    await expect(page.getByLabel(/email/i)).toBeVisible();
    await expect(page).toHaveScreenshot('v9-register-step1.png', {
      fullPage: true,
    });
  });

  test('Dashboard baseline (W18 F3 placeholder)', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(
      page.getByRole('heading', { name: /dashboard/i }),
    ).toBeVisible();
    // W18 F3 placeholder — re-capture this baseline once the W18 F4 overview cards land.
    // Mask any dynamic content (timestamps / mono-font ids appear after data load in F4).
    await expect(page).toHaveScreenshot('dashboard.png', {
      fullPage: true,
      mask: [page.locator('time'), page.locator('.font-mono')],
    });
  });

  test('V5 Eval Console baseline (empty state)', async ({ page }) => {
    await page.goto('/eval');
    await expect(
      page.getByRole('heading', { name: /evaluation console/i }),
    ).toBeVisible();
    // Empty 4-metric state (no eval runs yet — backend /eval/run is W4 stub)
    await expect(page.getByText(/no eval runs yet/i)).toBeVisible();
    await expect(page).toHaveScreenshot('v5-eval-console.png', {
      fullPage: true,
    });
  });
});
