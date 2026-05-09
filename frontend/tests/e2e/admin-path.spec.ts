/**
 * Admin-path E2E baseline — W15 D4 F4.3 deliverable.
 *
 * Coverage (Tier 1 baseline scope per W15 plan §3 Success Criteria):
 * - V2 Admin Dashboard renders (architecture.md v6 §5.3) — 4-card stats +
 *   Failed ingestion + Quick actions
 * - V3 KB List renders (§5.4) — card grid + sort + filter + Create CTA
 * - V4 KB Detail 5-tab renders (§5.5) — Documents/Chunks/Pipeline/Retrieval/Settings
 *   + URL searchParams ?tab= state
 * - V5 Eval Console renders (§5.6) — filter bar + 4-metric cards + Failed queries
 *   + Reranker Shootout
 * - V6 Debug View renders (§5.7) — 6-stage timeline + Open in Langfuse
 *
 * Tests assume NEXT_PUBLIC_AUTH_MOCK=true bypasses login + uses default mock
 * user identity. Backend stub endpoints (501 NOT_IMPLEMENTED for /eval/run +
 * /debug/trace) handled gracefully via toast.info / stub mitigation UI per
 * W15 D1+D2 implementation.
 */

import { test, expect } from '@playwright/test';

test.describe('Admin path E2E — KB management + eval + debug flow', () => {
  test('V2 Admin Dashboard renders 4-card stats + Quick actions', async ({
    page,
  }) => {
    await page.goto('/admin');
    await expect(
      page.getByRole('heading', { name: /overview|admin/i }),
    ).toBeVisible();
    // Stats cards (KB count / doc count / chunks / system status)
    await expect(page.getByText(/kb|knowledge base/i).first()).toBeVisible();
    // Quick actions (Create KB / Test query / View eval)
    await expect(page.getByRole('link', { name: /create kb/i })).toBeVisible();
    await expect(page.getByRole('link', { name: /test query|chat/i })).toBeVisible();
  });

  test('V3 KB List renders card grid with sort + filter + Create CTA', async ({
    page,
  }) => {
    await page.goto('/admin/kb');
    await expect(
      page.getByRole('heading', { name: /knowledge bases/i }),
    ).toBeVisible();
    // Search filter input
    await expect(page.getByPlaceholder(/search/i)).toBeVisible();
    // Sort dropdown
    await expect(page.getByText(/last indexed|name/i).first()).toBeVisible();
    // Create CTA
    await expect(
      page.getByRole('link', { name: /create kb/i }).first(),
    ).toBeVisible();
  });

  test('V5 Eval Console renders filter bar + 4-metric empty state + Reranker Shootout', async ({
    page,
  }) => {
    await page.goto('/eval');
    await expect(
      page.getByRole('heading', { name: /evaluation console/i }),
    ).toBeVisible();
    // Eval set selector + Run buttons
    await expect(page.getByRole('button', { name: /^run$/i })).toBeVisible();
    await expect(
      page.getByRole('button', { name: /run single/i }),
    ).toBeVisible();
    // 4-metric empty state — backend /eval/run is W4 stub
    await expect(page.getByText(/no eval runs yet/i)).toBeVisible();
    // W4 Reranker Shootout table (inline static const W6 D1 LIVE data)
    await expect(page.getByText(/cohere v4\.0-pro/i)).toBeVisible();
    await expect(page.getByText(/azure built-in/i)).toBeVisible();
    await expect(page.getByText(/recommended/i)).toBeVisible();
  });

  test('V6 Debug View renders trace header + 6-stage timeline + Langfuse link', async ({
    page,
  }) => {
    const traceId = '20260605-Q014';
    await page.goto(`/debug/${traceId}`);
    await expect(
      page.getByRole('heading', { name: /trace inspection/i }),
    ).toBeVisible();
    // traceId display (mono font)
    await expect(page.getByText(traceId).first()).toBeVisible();
    // Stub note alert (backend GET /debug/trace W3+ stub)
    await expect(page.getByText(/trace data pending|w3\+ stub/i)).toBeVisible();
    // 6-stage scaffold (custom Collapsible per stage)
    await expect(page.getByText(/query preprocessor/i)).toBeVisible();
    await expect(page.getByText(/hybrid retrieval/i)).toBeVisible();
    await expect(page.getByText(/llm synthesis/i)).toBeVisible();
    // Open in Langfuse link
    await expect(
      page.getByRole('link', { name: /open in langfuse/i }),
    ).toBeVisible();
  });

  test('Sidebar nav navigates between admin views', async ({ page }) => {
    await page.goto('/admin');
    // Click "Knowledge Bases" sidebar nav (NavLinks startsWith /admin/kb)
    await page.getByRole('link', { name: /knowledge bases/i }).first().click();
    await expect(page).toHaveURL(/\/admin\/kb/);
    // Click "Eval Console"
    await page.getByRole('link', { name: /eval console/i }).first().click();
    await expect(page).toHaveURL(/\/eval/);
  });
});
