/**
 * Playwright E2E + pixel diff baseline harness config — W15 D4 F4 deliverable
 * per architecture.md v6 §5.8 + design ref §6 W15 scope + CLAUDE.md §3.2
 * test framework "Vitest + React Testing Library baseline preserved; Playwright
 * additive" (per W15 plan §F4 deliverable spec ref).
 *
 * Tier 1 baseline scope per W15 plan §3 Success Criteria:
 * - Chromium-only (Desktop Chrome) — Karpathy §1.2 simplicity drop firefox/webkit
 * - Sequential test execution (fullyParallel: false) — avoid race conditions on
 *   shared in-memory KB state baseline
 * - Trace + screenshot + video retain-on-failure (debugging aid)
 * - webServer auto-starts `pnpm dev` (port 3001) with NEXT_PUBLIC_AUTH_MOCK=true
 *   so tests bypass real Entra ID via mock MSAL
 * - Backend uvicorn (port 8000) = user-driven separately per CLAUDE.md §13 dev
 *   server policy (Claude Code can't run long-lived servers)
 *
 * User smoke usage:
 *   1. `! cd backend && .venv/Scripts/python.exe -m uvicorn api.server:app --port 8000`
 *   2. `! cd frontend && npx playwright install chromium` (one-time browser binary)
 *   3. `! cd frontend && pnpm test:e2e` (auto-starts pnpm dev)
 *   4. `! cd frontend && pnpm test:e2e:update-snapshots` (capture pixel diff baseline)
 *
 * CI integration deferred to W16+ Beta hardening per plan §F4.5 PARTIAL PASS
 * acceptance "local-only baseline OK Tier 1".
 */

import { defineConfig, devices } from '@playwright/test';

const PORT = 3001;
const BASE_URL = `http://localhost:${PORT}`;

export default defineConfig({
  testDir: './tests/e2e',
  timeout: 30_000,
  expect: {
    timeout: 5_000,
    toHaveScreenshot: {
      // 1% diff tolerance for anti-aliasing / sub-pixel rendering jitter
      maxDiffPixelRatio: 0.01,
    },
  },
  // Tier 1: sequential to avoid in-memory KB state race conditions
  fullyParallel: false,
  forbidOnly: Boolean(process.env.CI),
  retries: 0,
  reporter: [['list'], ['html', { open: 'never' }]],
  use: {
    baseURL: BASE_URL,
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: {
    command: 'pnpm dev',
    url: BASE_URL,
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
    env: {
      NEXT_PUBLIC_AUTH_MOCK: 'true',
      NEXT_PUBLIC_API_URL: 'http://localhost:8000',
    },
  },
});
