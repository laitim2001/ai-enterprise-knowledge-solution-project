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
import { useTheme } from 'next-themes';

export function ThemeToggle() {
  const { setTheme, resolvedTheme } = useTheme();
  const isDark = resolvedTheme === 'dark';

  return (
    <button
      type="button"
      className="btn btn-ghost btn-icon btn-sm"
      aria-label="Toggle theme"
      title={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
      onClick={() => setTheme(isDark ? 'light' : 'dark')}
    >
      {isDark ? <Sparkles size={15} /> : <Layers size={15} />}
    </button>
  );
}
