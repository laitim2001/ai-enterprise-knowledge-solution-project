/**
 * App-shell-path E2E baseline — W18 F3 (per ADR-0024; renamed from admin-path.spec.ts); F4 + F8 updated.
 *
 * Coverage (Tier 1 baseline scope):
 * - /dashboard renders the real overview cards + quick actions (architecture.md v6 §5.3 / W18 F4)
 * - /kb KB List renders (§5.4) — card grid + sort + filter + Create CTA (re-routed from /admin/kb)
 * - /eval Eval Console renders (§5.6) — filter bar + 4-metric cards + Failed queries + Reranker Shootout
 * - /traces/[traceId] Traces detail renders (§5.7 — formerly "Debug View" /debug/[traceId]) —
 *   trace header + stage timeline + Open in Langfuse
 * - AppShell sidebar nav navigates between the modules
 * - AppShell chrome (top bar + sidebar) is present on /dashboard /chat /kb /eval /traces, absent on
 *   /login /register (W18 F8.5)
 *
 * Tests assume NEXT_PUBLIC_AUTH_MOCK=true bypasses login + uses the default mock user.
 * The actual run needs `npx playwright install chromium` which is R8-corp-proxy-blocked
 * (CO_W15_F4_browser_binaries / ADR-0017) — this spec's deliverable is the updated route
 * references + a tsc compile-check + this review; the run stays the pre-Beta smoke.
 */

import { test, expect } from '@playwright/test';

test.describe('App-shell path E2E — dashboard + KB + eval + traces flow', () => {
  test('/dashboard renders the overview cards + quick actions (W18 F4)', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(
      page.getByRole('heading', { name: /^dashboard$/i, level: 1 }),
    ).toBeVisible();
    // The 5 overview card titles (CardTitle = role="heading" aria-level={2} per W18 F8.2).
    await expect(
      page.getByRole('heading', { name: /knowledge bases/i, level: 2 }),
    ).toBeVisible();
    await expect(
      page.getByRole('heading', { name: /system health/i, level: 2 }),
    ).toBeVisible();
    await expect(
      page.getByRole('heading', { name: /quick actions/i, level: 2 }),
    ).toBeVisible();
    // Quick-action links.
    await expect(page.getByRole('link', { name: /new kb/i })).toBeVisible();
    await expect(page.getByRole('link', { name: /open chat/i })).toBeVisible();
  });

  test('/kb KB List renders card grid with sort + filter + Create CTA', async ({
    page,
  }) => {
    await page.goto('/kb');
    await expect(
      page.getByRole('heading', { name: /knowledge bases/i }),
    ).toBeVisible();
    await expect(page.getByPlaceholder(/search/i)).toBeVisible();
    await expect(page.getByText(/last indexed|name/i).first()).toBeVisible();
    await expect(
      page.getByRole('link', { name: /create kb/i }).first(),
    ).toBeVisible();
  });

  test('/eval Eval Console renders filter bar + 4-metric empty state + Reranker Shootout', async ({
    page,
  }) => {
    await page.goto('/eval');
    await expect(
      page.getByRole('heading', { name: /evaluation console/i }),
    ).toBeVisible();
    await expect(page.getByRole('button', { name: /^run$/i })).toBeVisible();
    await expect(
      page.getByRole('button', { name: /run single/i }),
    ).toBeVisible();
    await expect(page.getByText(/no eval runs yet/i)).toBeVisible();
    await expect(page.getByText(/cohere v4\.0-pro/i)).toBeVisible();
    await expect(page.getByText(/recommended/i)).toBeVisible();
  });

  test('/traces/[traceId] Traces detail renders trace header + stage timeline + Langfuse link', async ({
    page,
  }) => {
    const traceId = '20260605-Q014';
    await page.goto(`/traces/${traceId}`);
    await expect(page.getByRole('heading', { name: /trace/i })).toBeVisible();
    await expect(page.getByText(traceId).first()).toBeVisible();
    // Pipeline stage names (the 9-stage scaffold; subset assertion).
    await expect(page.getByText(/query preprocessor/i)).toBeVisible();
    await expect(page.getByText(/hybrid retrieval/i)).toBeVisible();
    await expect(page.getByText(/llm synthesis/i)).toBeVisible();
    await expect(
      page.getByRole('link', { name: /open in langfuse/i }),
    ).toBeVisible();
  });

  test('AppShell sidebar nav navigates between modules', async ({ page }) => {
    await page.goto('/dashboard');
    // Click "Knowledge Bases" in the AppShell sidebar → /kb
    await page.getByRole('link', { name: /knowledge bases/i }).first().click();
    await expect(page).toHaveURL(/\/kb/);
    // Click "Eval Console" → /eval
    await page.getByRole('link', { name: /eval console/i }).first().click();
    await expect(page).toHaveURL(/\/eval/);
    // Click "Chat" → /chat
    await page.getByRole('link', { name: /^chat$/i }).first().click();
    await expect(page).toHaveURL(/\/chat/);
  });

  test('AppShell chrome is present on app routes and absent on the auth pages', async ({
    page,
  }) => {
    // Present (top bar global-search trigger + the "Primary" sidebar nav) on the module routes.
    for (const path of ['/dashboard', '/chat', '/kb', '/eval', '/traces/some-trace-id']) {
      await page.goto(path);
      await expect(page.getByRole('navigation', { name: /primary/i })).toBeVisible();
      await expect(page.getByRole('button', { name: /search \(ctrl/i })).toBeVisible();
    }
    // Absent on the auth pages — they keep the chrome-free root layout (BrandPanel split).
    for (const path of ['/login', '/register']) {
      await page.goto(path);
      await expect(page.getByRole('navigation', { name: /primary/i })).toHaveCount(0);
      await expect(page.getByRole('button', { name: /search \(ctrl/i })).toHaveCount(0);
    }
    // …and `/` redirects out to /login (no chrome there either — W18 F7).
    await page.goto('/');
    await expect(page).toHaveURL(/\/login$/);
    await expect(page.getByRole('navigation', { name: /primary/i })).toHaveCount(0);
  });
});
