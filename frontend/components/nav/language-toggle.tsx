'use client';

import { Check, Globe } from 'lucide-react';
import { useLocale, useTranslations } from 'next-intl';
import { useRouter } from 'next/navigation';
import { useEffect, useState, useTransition } from 'react';
import { createPortal } from 'react-dom';

/**
 * C09 topbar language toggle — W103 F6.2 正式版(mockup `ekp-shell.jsx:104-134`
 * LanguageMenu PopMenu 忠實移植;portal pattern 同 `notifications-menu.tsx`
 * 一致 — Radix DropdownMenu 係 anti-pattern per DESIGN_SYSTEM.md §4)。
 *
 * Mockup `<PopMenu width={260} right={138}>` 結構:
 *   - Header: "Display language" + Tier 邊界副題
 *   - Body: en / zh / ja 三行(.nav-item;mono code 欄 + label + active 剔號
 *     + disabled 行 opacity .5 + Tier 2 badge)
 *   - Footer: muted bar
 *
 * 對 mockup 嘅 design-stage 內容修正(2026-07-21 用戶拍板,per ADR-0075):
 *   - zh label「简体中文」→「繁體中文」(promote 嘅係繁體 UI chrome)
 *   - en active + ja/zh 皆 disabled → en/zh enabled(剔號隨 locale),ja 保持
 *     Tier 2 disabled
 *   - header 副題「Per ADR-0024 · JP/ZH disabled in Tier 1」stale → ADR-0075
 *   - footer「Preview JP / ZH support (Labs) →」導向 prototype-only route →
 *     改 disabled 提示文字(JP Tier 2)
 *
 * 揀語言寫 `NEXT_LOCALE` cookie + router.refresh(cookie-based,D-2 甲 per
 * i18n/request.ts)。登入頁(auth-frame)複用本組件,經 menuTop / menuRight
 * 調 popover 錨點(登入頁冇 .topbar,--topbar-h 錨唔啱)。
 */

interface LanguageOption {
  code: 'en' | 'zh' | 'ja';
  /** Native name 慣例 — 語言名以其自身語言顯示,en / zh 字典同值。 */
  label: string;
  enabled: boolean;
}

const LANGUAGES: LanguageOption[] = [
  { code: 'en', label: 'English', enabled: true },
  { code: 'zh', label: '繁體中文', enabled: true },
  { code: 'ja', label: '日本語', enabled: false },
];

export function LanguageToggle({
  menuTop = 'calc(var(--topbar-h) - 4px)',
  menuRight = 138,
}: {
  menuTop?: string;
  menuRight?: number;
} = {}) {
  const locale = useLocale();
  const t = useTranslations('LanguageToggle');
  const router = useRouter();
  const [, startTransition] = useTransition();
  const [open, setOpen] = useState(false);
  const [mounted, setMounted] = useState(false);

  // Portal hydration guard — 同 notifications-menu pattern。
  useEffect(() => {
    setMounted(true);
  }, []);

  // Click-outside + Escape — mockup `ekp-shell.jsx:14-22` pattern。
  useEffect(() => {
    if (!open) return;
    function handleClick(e: MouseEvent) {
      const target = e.target as Element | null;
      if (!target) return;
      if (
        !target.closest('.topbar-popmenu') &&
        !target.closest('[data-popmenu-trigger="language"]')
      ) {
        setOpen(false);
      }
    }
    function handleKey(e: KeyboardEvent) {
      if (e.key === 'Escape') setOpen(false);
    }
    document.addEventListener('click', handleClick);
    document.addEventListener('keydown', handleKey);
    return () => {
      document.removeEventListener('click', handleClick);
      document.removeEventListener('keydown', handleKey);
    };
  }, [open]);

  function selectLocale(code: string) {
    setOpen(false);
    if (code === locale) return;
    // 1-year cookie, root path — mirrors next-intl cookie-based default.
    document.cookie = `NEXT_LOCALE=${code}; path=/; max-age=31536000; samesite=lax`;
    startTransition(() => router.refresh());
  }

  const popover = (
    <div
      className="topbar-popmenu"
      role="menu"
      aria-label={t('menuTitle')}
      style={{
        position: 'fixed',
        top: menuTop,
        right: menuRight,
        width: 260,
        background: 'oklch(var(--popover))',
        border: '1px solid oklch(var(--border))',
        borderRadius: 'var(--radius-md)',
        boxShadow: 'var(--shadow-lg)',
        zIndex: 50,
        overflow: 'hidden',
        animation: 'pop-in 0.14s var(--ease)',
      }}
    >
      {/* Header — mockup ekp-shell.jsx:107-110 */}
      <div style={{ padding: '10px 14px', borderBottom: '1px solid oklch(var(--border))' }}>
        <div style={{ fontSize: 12.5, fontWeight: 600 }}>{t('menuTitle')}</div>
        <div className="text-xs muted">{t('menuSubtitle')}</div>
      </div>

      {/* Body — mockup ekp-shell.jsx:111-126 */}
      <div style={{ padding: 6 }}>
        {LANGUAGES.map((l) => (
          <div
            key={l.code}
            className="nav-item"
            role="menuitemradio"
            aria-checked={l.code === locale}
            aria-disabled={!l.enabled}
            style={{
              opacity: l.enabled ? 1 : 0.5,
              padding: '7px 10px',
              cursor: l.enabled ? 'pointer' : 'default',
            }}
            onClick={() => l.enabled && selectLocale(l.code)}
          >
            <span className="mono text-xs" style={{ width: 26 }}>
              {l.code}
            </span>
            <span style={{ flex: 1 }}>{l.label}</span>
            {l.code === locale && (
              <Check size={13} style={{ color: 'oklch(var(--accent))' }} />
            )}
            {!l.enabled && <span className="badge badge-muted">{t('tier2Badge')}</span>}
          </div>
        ))}
      </div>

      {/* Footer — mockup ekp-shell.jsx:127-131 結構;內容改 disabled 提示
          (原「Preview JP / ZH support (Labs) →」導向 prototype-only route)。 */}
      <div
        style={{
          padding: '8px 14px',
          borderTop: '1px solid oklch(var(--border))',
          background: 'oklch(var(--muted) / 0.3)',
        }}
      >
        <span className="text-xs muted" aria-disabled="true">
          {t('footerJapanese')}
        </span>
      </div>
    </div>
  );

  return (
    <>
      <button
        type="button"
        className="btn btn-ghost btn-icon btn-sm hidden sm:inline-flex"
        data-popmenu-trigger="language"
        aria-label={t('ariaLabel')}
        aria-haspopup="menu"
        aria-expanded={open}
        title={t('label')}
        onClick={() => setOpen((o) => !o)}
      >
        <Globe size={15} />
      </button>
      {mounted && open && createPortal(popover, document.body)}
    </>
  );
}
