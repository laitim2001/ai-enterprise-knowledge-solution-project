'use client';

/**
 * C09 admin shell theme toggle — W22 F1-pivot direct-copy from mockup
 * `references/design-mockups/ekp-shell.jsx` line 53-55 (per CLAUDE.md
 * §5.7 H7 strict fidelity 2026-05-17 user directive).
 *
 * Mockup pattern: SIMPLE onClick → toggle theme. No dropdown menu.
 *   IcSparkles (when dark mode active, click to go light) /
 *   IcLayers (when light mode active, click to go dark).
 *
 * `next-themes` `setTheme(dark/light)` is the toggle target — bypasses the
 * "system" tri-state option that the prior shadcn DropdownMenu offered
 * (users can still pick system via /settings page if Wave C2 surfaces it).
 */

import { Layers, Sparkles } from 'lucide-react';
import { useTranslations } from 'next-intl';
import { useTheme } from 'next-themes';
import { useEffect, useState } from 'react';

export function ThemeToggle() {
  const t = useTranslations('ThemeToggle');
  const { setTheme, resolvedTheme } = useTheme();
  // `resolvedTheme` is undefined during SSR (next-themes resolves it client-side
  // from localStorage / system pref), so gate the icon on a mounted flag to keep
  // the first client render identical to the server HTML. Same hydration guard
  // as auth-frame.tsx (BUG-032) and notifications-menu.tsx.
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);
  const isDark = mounted && resolvedTheme === 'dark';

  return (
    <button
      type="button"
      className="btn btn-ghost btn-icon btn-sm"
      aria-label={t('toggleTheme')}
      title={isDark ? t('switchToLight') : t('switchToDark')}
      onClick={() => setTheme(isDark ? 'light' : 'dark')}
    >
      {isDark ? <Sparkles size={15} /> : <Layers size={15} />}
    </button>
  );
}
