/**
 * Vitest config — frontend unit-test harness (W17 F6; closes CO_W15_F4_vitest_baseline_gap).
 *
 * Scope: component-level unit tests under `tests/unit/` (jsdom + React Testing
 * Library + jest-dom matchers). Playwright E2E (`tests/e2e/`, `playwright.config.ts`,
 * `test:e2e` script) stays the golden-path layer and is excluded here — the two
 * runners don't overlap. Path alias `@/*` mirrors `tsconfig.json`.
 */

import react from '@vitejs/plugin-react';
import { resolve } from 'node:path';
import { defineConfig } from 'vitest/config';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': resolve(__dirname, '.'),
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./tests/unit/setup.ts'],
    include: ['tests/unit/**/*.test.{ts,tsx}'],
    exclude: ['node_modules', '.next', 'tests/e2e/**'],
  },
});
