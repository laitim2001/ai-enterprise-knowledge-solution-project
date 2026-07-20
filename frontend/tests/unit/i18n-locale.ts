/**
 * 測試用 locale 開關 — W103 F7.3。
 *
 * `setup.ts` 把 `next-intl` 的 `useTranslations` / `useLocale` 換成讀本模組的
 * 狀態,令 unit test 唔使逐個包 `<NextIntlClientProvider>` 都 render 得到
 * (W103 externalize 之後,幾乎每個組件都依賴 i18n context)。
 *
 * 預設 `en` —— 既有測試的英文斷言因此照舊有效。要驗 zh 態或切換行為,喺
 * test 內 `setTestLocale('zh')`;`setup.ts` 會喺每個 test 之後自動 reset 返
 * `en`,避免跨 test 污染。
 */

export type TestLocale = 'en' | 'zh';

export const testLocaleState: { locale: TestLocale } = { locale: 'en' };

export function setTestLocale(locale: TestLocale): void {
  testLocaleState.locale = locale;
}

export function resetTestLocale(): void {
  testLocaleState.locale = 'en';
}
