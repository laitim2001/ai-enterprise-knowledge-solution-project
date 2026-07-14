'use client';

import { Globe } from 'lucide-react';
import { useLocale, useTranslations } from 'next-intl';
import { useRouter } from 'next/navigation';
import { useTransition } from 'react';

/**
 * Language toggle — W103 F4 **臨時驗證版** (temporary end-to-end verification).
 *
 * Minimal en↔zh cycle: click writes the `NEXT_LOCALE` cookie + refreshes the
 * router so the server re-reads the locale (cookie-based, D-2 甲 per i18n/
 * request.ts). Keeps the mockup Globe-icon button visual (`.btn .btn-ghost
 * .btn-icon .btn-sm`) — only flips it from the disabled coming-soon affordance
 * to a functional control.
 *
 * ⚠️ 正式 toggle UI 形態 (Globe cycle vs dropdown 選單) + H7 mockup 對齊 = F6.
 * mockup 只有 disabled Globe,冇 enabled 互動設計 → F6 STOP+ask 決定形態
 * (per CLAUDE.md §5.7 H7). This interim button unblocks F4 batch verification.
 */
export function LanguageToggle() {
  const locale = useLocale();
  const t = useTranslations('LanguageToggle');
  const router = useRouter();
  const [pending, startTransition] = useTransition();

  const next = locale === 'en' ? 'zh' : 'en';
  const nextLabel = next === 'zh' ? t('chinese') : t('english');

  function switchLocale() {
    // 1-year cookie, root path — mirrors next-intl cookie-based default.
    document.cookie = `NEXT_LOCALE=${next}; path=/; max-age=31536000; samesite=lax`;
    startTransition(() => router.refresh());
  }

  return (
    <button
      type="button"
      onClick={switchLocale}
      disabled={pending}
      aria-label={t('ariaLabel')}
      title={`${t('label')} · ${nextLabel}`}
      className="btn btn-ghost btn-icon btn-sm hidden sm:inline-flex"
    >
      <Globe size={15} />
    </button>
  );
}
