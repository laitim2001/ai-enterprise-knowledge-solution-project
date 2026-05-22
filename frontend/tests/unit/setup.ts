/**
 * Vitest setup — registers `@testing-library/jest-dom` matchers (toBeInTheDocument,
 * toHaveClass, …), polyfills the browser APIs jsdom omits but Radix primitives
 * touch (ResizeObserver — used by Slider / Select size hooks), and auto-cleans
 * the rendered DOM between tests. Loaded via `vitest.config.ts` `test.setupFiles`.
 * (W17 F6; ResizeObserver polyfill added CH-002 F3 — the Eval Console renders a
 * Radix Slider.)
 */

import '@testing-library/jest-dom/vitest';
import { cleanup } from '@testing-library/react';
import { afterEach } from 'vitest';

if (!('ResizeObserver' in globalThis)) {
  class ResizeObserverStub {
    observe(): void {}
    unobserve(): void {}
    disconnect(): void {}
  }
  (globalThis as unknown as { ResizeObserver: typeof ResizeObserverStub }).ResizeObserver =
    ResizeObserverStub;
}

// jsdom implements neither Element.scrollTo nor scrollIntoView — components
// that auto-scroll (e.g. the chat thread) call them in effects. Stub as no-ops.
// (BUG-006 — the chat page test renders the auto-scrolling thread.)
const elementProto = Element.prototype as unknown as Record<string, unknown>;
if (typeof elementProto.scrollTo !== 'function') {
  elementProto.scrollTo = () => {};
}
if (typeof elementProto.scrollIntoView !== 'function') {
  elementProto.scrollIntoView = () => {};
}

afterEach(() => {
  cleanup();
});
