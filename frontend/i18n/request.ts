import { cookies } from 'next/headers';
import { getRequestConfig } from 'next-intl/server';

/**
 * Supported UI-chrome locales — `en` (source language per CH-023) + `zh`
 * (Traditional Chinese). JP + RAG/content translation stay Tier 2 (ADR-0075).
 */
export const locales = ['en', 'zh'] as const;
export type Locale = (typeof locales)[number];
export const defaultLocale: Locale = 'en';

/**
 * Cookie-based locale resolution (W103 F3, D-2 甲 — next-intl "without i18n
 * routing"). The active locale comes from the `NEXT_LOCALE` cookie so URLs stay
 * flat (aligns W18 URL flatten); falls back to `en` when the cookie is absent
 * or holds an unsupported value.
 */
export default getRequestConfig(async () => {
  const cookieLocale = cookies().get('NEXT_LOCALE')?.value;
  const locale: Locale =
    cookieLocale && locales.includes(cookieLocale as Locale)
      ? (cookieLocale as Locale)
      : defaultLocale;

  return {
    locale,
    messages: (await import(`../messages/${locale}.json`)).default,
  };
});
