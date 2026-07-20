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
import { afterEach, vi } from 'vitest';

import { resetTestLocale } from './i18n-locale';

/**
 * i18n — W103 F7.3。externalize 之後幾乎每個組件都會 `useTranslations()`,但
 * unit test 直接 render 組件、冇 `<NextIntlClientProvider>` 包住 → context 缺失
 * 即 throw(修之前 24 檔 / 95 test 就係咁掛)。
 *
 * 這裡**唔**手寫假 translator,而是用 next-intl 官方的 `createTranslator` —— 同
 * hook 版同一實作,`t()` / `t.rich()` / `t.has()` 同 ICU 格式化行為完全一致,唔會
 * 出現「測試過但真實 render 爆」的假綠。字典按 `testLocaleState` 選 en / zh
 * (預設 en,故既有英文斷言零改動仍然有效)。
 */
vi.mock('next-intl', async (importOriginal) => {
  const actual = await importOriginal<typeof import('next-intl')>();
  const [{ default: enMessages }, { default: zhMessages }, { testLocaleState }] = await Promise.all([
    import('../../messages/en.json'),
    import('../../messages/zh.json'),
    import('./i18n-locale'),
  ]);
  const dict = { en: enMessages, zh: zhMessages };
  // Translator 無狀態,可按 (locale, namespace) 快取重用 —— 每次 render 重建會
  // 令 ICU 初始化開銷疊加(實測慢 15 倍,chat-meta-row 908ms → 13.5s)。
  type HookTranslator = ReturnType<typeof actual.useTranslations>;
  // `createTranslator` 的 messages / namespace 參數型別是由字典**推導**出來的
  // literal union,但 mock 層只拿到執行期字串(值一模一樣,只是型別來源不同)。
  // 收窄成一個 loose 簽名,令 cast 集中喺這一點而唔散落各處。
  const createTranslator = actual.createTranslator as unknown as (opts: {
    locale: string;
    messages: unknown;
    namespace?: string;
  }) => HookTranslator;
  const cache = new Map<string, HookTranslator>();

  return {
    ...actual,
    useLocale: () => testLocaleState.locale,
    useTranslations: (namespace?: string) => {
      const { locale } = testLocaleState;
      const key = `${locale}:${namespace ?? ''}`;
      let translator = cache.get(key);
      if (!translator) {
        translator = createTranslator({ locale, messages: dict[locale], namespace });
        cache.set(key, translator);
      }
      return translator;
    },
  };
});

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
  resetTestLocale();
});
