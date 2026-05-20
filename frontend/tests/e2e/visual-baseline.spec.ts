/**
 * Visual baseline pixel diff harness — W15 D4 F4.4 deliverable; W18 F7 updated;
 * W20 F8.5 extended; W22 rebuilt 15 routes; **W23 F2.3 baseline RE-CAPTURE**.
 *
 * Captures baseline screenshots for representative views per Tier 1 scope:
 * - V8 Login (`/login`) — W22 F2.1 rebuild
 * - V9 Register Step 1 (`/register`) — W22 F2.2 rebuild
 * - Dashboard (`/dashboard`) — W22 F3 rebuild
 * - V5 Eval Console (`/eval`) — W22 F7.1 rebuild
 * - /kb/new wizard Step 1 (Identity) — W22 F5.2 rebuild
 * - Chat advanced surfaces (`/chat`) — W22 F4 rebuild
 *
 * V7 Landing's `/` baseline was dropped — Landing page REMOVED per ADR-0024.
 *
 * V1 Chat / V3 KB List / V4 KB Detail / V6 Traces = covered by golden-path +
 * app-shell-path E2E render assertions (interactive flow tests). Pixel diff is
 * gated to stable layout views — empty state baselines avoid dynamic content
 * jitter.
 *
 * First run captures baseline:
 *   PW_CHANNEL=chrome pnpm test:e2e:update-snapshots
 * Subsequent runs diff against baseline (1% maxDiffPixelRatio per
 * playwright.config.ts):
 *   PW_CHANNEL=chrome pnpm test:e2e
 *
 * Baseline screenshots stored next to this file under:
 *   tests/e2e/visual-baseline.spec.ts-snapshots/
 *
 * W23 F2.3 baseline re-capture: pre-W22 baselines stale across 15 W22 rebuilt
 * routes (TopBar / Sidebar / typography / spacing all changed at CSS-first
 * pivot baseline). All 6 baselines below re-capture with new W22 mockup-faithful
 * DOM. Selectors re-aligned per W22 F2/F3/F5/F7 rebuild commits.
 */

import { test, expect } from '@playwright/test';

test.describe('Visual baseline — pixel diff harness (W23 F2.3 W22-aligned)', () => {
  test('V8 Login baseline (W22 F2.1)', async ({ page }) => {
    await page.goto('/login');
    // W22 F2.1 page-title「Welcome back」 + work email label preserved.
    await expect(page.getByLabel(/work email/i)).toBeVisible();
    await expect(page).toHaveScreenshot('v8-login.png', {
      fullPage: true,
    });
  });

  test('V9 Register Step 1 baseline (W22 F2.2)', async ({ page }) => {
    await page.goto('/register');
    // W22 F2.2 page-title「Create your account」 + full name field first.
    await expect(page.getByLabel(/full name/i)).toBeVisible();
    await expect(page).toHaveScreenshot('v9-register-step1.png', {
      fullPage: true,
    });
  });

  test('Dashboard baseline (W22 F3 rebuild)', async ({ page }) => {
    await page.goto('/dashboard');
    // W22 F3 page-title「Welcome back, {displayName}」(not pre-W22「Dashboard」).
    await expect(
      page.getByRole('heading', { name: /welcome back/i, level: 1 }),
    ).toBeVisible();
    // F3 cards' data loads async (GET /kb + GET /health); mask dynamic content
    // (mono-font ids / timestamps) so the baseline doesn't jitter on counts/uptime.
    await expect(page).toHaveScreenshot('dashboard.png', {
      fullPage: true,
      mask: [page.locator('time'), page.locator('.mono')],
    });
  });

  test('V5 Eval Console baseline (W22 F7.1 empty state)', async ({ page }) => {
    await page.goto('/eval');
    // W22 F7.1 page-title「Eval Console」 (not pre-W22「Evaluation Console」).
    await expect(
      page.getByRole('heading', { name: 'Eval Console', level: 1 }),
    ).toBeVisible();
    // Empty 4-metric state — captured before any Run click.
    await expect(page.getByText(/no eval runs yet/i)).toBeVisible();
    await expect(page).toHaveScreenshot('v5-eval-console.png', {
      fullPage: true,
    });
  });

  test('/kb/new wizard Step 1 baseline (W22 F5.2 — 5-step Identity)', async ({ page }) => {
    await page.goto('/kb/new');
    // W22 F5.2 Step 1 card heading「KB identity」(h3 level, not pre-W22「Source」h2).
    await expect(
      page.getByRole('heading', { name: /kb identity/i, level: 3 }),
    ).toBeVisible();
    await expect(page).toHaveScreenshot('kb-new-wizard-step1.png', {
      fullPage: true,
    });
  });

  test('Chat advanced surfaces baseline (W22 F4 — Conversations + ChatHeader)', async ({
    page,
  }) => {
    await page.goto('/chat');
    // W22 F4 Conversations sidebar — span element not heading (line 577).
    await expect(page.getByText(/^conversations$/i).first()).toBeVisible();
    // Mask dynamic timestamps + mono spans (KB IDs / chunk counts).
    await expect(page).toHaveScreenshot('chat-w20-f3b.png', {
      fullPage: true,
      mask: [page.locator('time'), page.locator('.mono')],
    });
  });

  test('Settings ?tab=connections baseline (W24 F5 — 6-tab PageSettingsRich)', async ({
    page,
  }) => {
    await page.goto('/settings?tab=connections');
    // W24 F5 page-title preserved + deep-link tab selection.
    await expect(
      page.getByRole('heading', { name: /^settings$/i, level: 1 }),
    ).toBeVisible();
    // Connections tab content: lazy-fetch detail expands per row; wait for the
    // category headers to land (banner OR LLM-category header).
    const banner = page.getByText(/loading connections/i);
    const llmHeader = page.getByText(/llm & embedding/i);
    await expect(banner.or(llmHeader).first()).toBeVisible({ timeout: 10000 });
    // Mask dynamic mono content (provider endpoints / kv_ref names vary per env).
    await expect(page).toHaveScreenshot('settings-connections.png', {
      fullPage: true,
      mask: [page.locator('.mono')],
    });
  });

  test('Settings ?tab=identity baseline (W24b F7.4 — Identity inline-edit forms)', async ({
    page,
  }) => {
    await page.goto('/settings?tab=identity');
    // W24 F5 page-title preserved + deep-link tab selection.
    await expect(
      page.getByRole('heading', { name: /^settings$/i, level: 1 }),
    ).toBeVisible();
    // Identity tab: 4 editable cards (Tenant / App registration / MSAL /
    // Sign-in policy) load async — wait for the loading banner OR the resolved
    // tenant card before the pixel capture.
    const banner = page.getByText(/loading identity configuration/i);
    const tenantCard = page.getByText(/entra id tenant/i);
    await expect(banner.or(tenantCard).first()).toBeVisible({ timeout: 10000 });
    // Mask dynamic mono content (tenant / client GUIDs + kv_ref names + the
    // derived authority URL vary per env).
    await expect(page).toHaveScreenshot('settings-identity.png', {
      fullPage: true,
      mask: [page.locator('.mono')],
    });
  });
});
