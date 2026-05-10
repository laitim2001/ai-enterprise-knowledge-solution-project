/**
 * App-shell-path E2E baseline — W18 F3 (per ADR-0024; renamed from admin-path.spec.ts).
 *
 * Coverage (Tier 1 baseline scope):
 * - /dashboard renders (architecture.md v6 §5.3) — W18 F3 PLACEHOLDER (the real overview
 *   cards land in W18 F4; this test is a heading + nav-link smoke for now — see the TODO)
 * - /kb KB List renders (§5.4) — card grid + sort + filter + Create CTA (re-routed from /admin/kb)
 * - /eval Eval Console renders (§5.6) — filter bar + 4-metric cards + Failed queries + Reranker Shootout
 * - /traces/[traceId] Traces detail renders (§5.7 — formerly "Debug View" /debug/[traceId]) —
 *   trace header + stage timeline + Open in Langfuse
 * - AppShell sidebar nav navigates between the modules
 *
 * Tests assume NEXT_PUBLIC_AUTH_MOCK=true bypasses login + uses the default mock user.
 * The actual run needs `npx playwright install chromium` which is R8-corp-proxy-blocked
 * (CO_W15_F4_browser_binaries / ADR-0017) — this spec's W18 F3 deliverable is the updated
 * route references + a tsc compile-check + this review; the run stays the pre-Beta smoke.
 */

import { test, expect } from '@playwright/test';

test.describe('App-shell path E2E — dashboard + KB + eval + traces flow', () => {
  test('/dashboard placeholder renders heading + module links', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(
      page.getByRole('heading', { name: /dashboard/i }),
    ).toBeVisible();
    // F3 placeholder surfaces module links (Chat / Knowledge Bases / Eval Console / Traces).
    await expect(page.getByRole('link', { name: /^chat$/i }).first()).toBeVisible();
    // TODO(W18 F4): assert the real overview cards (KB summary / recent queries /
    // latest eval / system health / quick actions) once the F4 dashboard lands.
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
});
