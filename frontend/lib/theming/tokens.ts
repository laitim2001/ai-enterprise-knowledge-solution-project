/**
 * EKP design tokens — visual identity layer (per architecture.md v6 §5.1).
 *
 * Decision lineage:
 * - OQ-Q10 W6 D5 Resolved (default neutral tokens; designer pass post-Beta optional)
 * - W12 D2 ratification 2026-06-10 — Option C "Warm Charcoal + Coral Accent"
 *   (Notion-leaning editorial direction; User-as-Stakeholder approve cycle 1)
 * - Dark mode parallel implement (W12 D4 override per User explicit decision
 *   2026-06-10; supersedes spec defer-W15 default)
 *
 * Constraints (per CLAUDE.md §3.2 + architecture.md v6 §5.1 + §7):
 * - 100% custom oklch values, NEVER copied from Dify (per H3 + ADR-0010)
 * - Layout patterns can borrow from Dify; visual identity must be distinctly EKP
 * - NEVER hardcode color/spacing in components — always reference tokens here
 * - radius / fontFamily are spec-locked per architecture.md v6 §5.1
 */

export const ekpTokens = {
  /**
   * Light mode color palette — Option C "Warm Charcoal + Coral Accent".
   *
   * Primary = warm charcoal (used for nav text, primary CTA backgrounds).
   * Accent = warm coral (used for citation links, highlights, action emphasis).
   * Background = pure white. Foreground = near-black neutral.
   */
  colorsLight: {
    primary: 'oklch(0.20 0.01 285)',
    'primary-foreground': 'oklch(0.98 0 0)',
    accent: 'oklch(0.65 0.18 25)',
    'accent-foreground': 'oklch(0.98 0 0)',
    background: 'oklch(1 0 0)',
    foreground: 'oklch(0.15 0 0)',
    muted: 'oklch(0.96 0 0)',
    'muted-foreground': 'oklch(0.45 0 0)',
    border: 'oklch(0.92 0 0)',
    input: 'oklch(0.92 0 0)',
    ring: 'oklch(0.65 0.18 25)',
    success: 'oklch(0.65 0.16 145)',
    'success-foreground': 'oklch(0.98 0 0)',
    warning: 'oklch(0.78 0.16 80)',
    'warning-foreground': 'oklch(0.15 0 0)',
    destructive: 'oklch(0.57 0.22 25)',
    'destructive-foreground': 'oklch(0.98 0 0)',
  },

  /**
   * Dark mode color palette — inverted-button pattern (Notion-leaning).
   *
   * Primary inverts to light warm-neutral (buttons become light bg in dark mode).
   * Accent coral lifts L from 0.65 → 0.68 for better contrast on dark surfaces.
   * Background = warm-neutral dark (NOT pure black; subtle warm undertone matches
   * primary hue 285 to maintain editorial cohesion).
   */
  colorsDark: {
    primary: 'oklch(0.95 0.005 285)',
    'primary-foreground': 'oklch(0.18 0.005 285)',
    accent: 'oklch(0.68 0.16 25)',
    'accent-foreground': 'oklch(0.15 0 0)',
    background: 'oklch(0.18 0.005 285)',
    foreground: 'oklch(0.95 0 0)',
    muted: 'oklch(0.25 0.005 285)',
    'muted-foreground': 'oklch(0.65 0 0)',
    border: 'oklch(0.30 0.005 285)',
    input: 'oklch(0.30 0.005 285)',
    ring: 'oklch(0.68 0.16 25)',
    success: 'oklch(0.70 0.18 145)',
    'success-foreground': 'oklch(0.15 0 0)',
    warning: 'oklch(0.80 0.18 80)',
    'warning-foreground': 'oklch(0.15 0 0)',
    destructive: 'oklch(0.62 0.24 25)',
    'destructive-foreground': 'oklch(0.98 0 0)',
  },

  /**
   * Border radius — spec-locked per architecture.md v6 §5.1
   * ("更銳利感 vs Dify default" — sharper feel via smaller scale).
   */
  radius: {
    sm: '0.25rem',
    md: '0.5rem',
    lg: '0.75rem',
  },

  /**
   * Font families — spec-locked per architecture.md v6 §5.1
   * (Inter sans + JetBrains Mono — distinct from Dify SF Pro).
   */
  fontFamily: {
    sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
    mono: ['JetBrains Mono', 'ui-monospace', 'monospace'],
  },

  /**
   * Spacing — Tailwind default reference (no duplicate values; consume via
   * Tailwind utility classes per CLAUDE.md §3.2 "tokens consumption verified").
   */
  spacing: {
    // Tailwind default scale: 0 / 0.5 / 1 / 1.5 / 2 / 2.5 / 3 / 3.5 / 4 / 5 / 6 ...
    // Reference only — components consume via class="p-4 m-2 gap-3" etc.
  },

  /**
   * Shadow tokens — shadcn/ui v0 default scale.
   */
  shadow: {
    sm: '0 1px 2px 0 rgb(0 0 0 / 0.05)',
    DEFAULT: '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)',
    md: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
    lg: '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)',
  },

  /**
   * Motion tokens — durations + ease curve per shadcn/ui v0 default.
   * Use for transition / animation timing across components.
   */
  motion: {
    durationFast: '150ms',
    durationBase: '200ms',
    durationSlow: '300ms',
    easeDefault: 'cubic-bezier(0.4, 0, 0.2, 1)',
  },
} as const;

export type EkpTokens = typeof ekpTokens;
