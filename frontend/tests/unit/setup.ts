/**
 * Vitest setup — registers `@testing-library/jest-dom` matchers (toBeInTheDocument,
 * toHaveClass, …) and auto-cleans the rendered DOM between tests. Loaded via
 * `vitest.config.ts` `test.setupFiles`. (W17 F6)
 */

import '@testing-library/jest-dom/vitest';
import { cleanup } from '@testing-library/react';
import { afterEach } from 'vitest';

afterEach(() => {
  cleanup();
});
