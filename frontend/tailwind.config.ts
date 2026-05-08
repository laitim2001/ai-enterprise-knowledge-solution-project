import type { Config } from 'tailwindcss';

import { ekpTokens } from './lib/theming/tokens';

const config: Config = {
  darkMode: ['class'],
  content: [
    './app/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './lib/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      // Color utility classes wired via CSS custom properties for theme toggle.
      // Bare oklch component values (L C H) defined in app/globals.css
      // (:root for light / .dark for dark). Sync with tokens.ts colorsLight/Dark.
      colors: {
        primary: 'oklch(var(--primary))',
        'primary-foreground': 'oklch(var(--primary-foreground))',
        accent: 'oklch(var(--accent))',
        'accent-foreground': 'oklch(var(--accent-foreground))',
        background: 'oklch(var(--background))',
        foreground: 'oklch(var(--foreground))',
        muted: 'oklch(var(--muted))',
        'muted-foreground': 'oklch(var(--muted-foreground))',
        border: 'oklch(var(--border))',
        input: 'oklch(var(--input))',
        ring: 'oklch(var(--ring))',
        success: 'oklch(var(--success))',
        'success-foreground': 'oklch(var(--success-foreground))',
        warning: 'oklch(var(--warning))',
        'warning-foreground': 'oklch(var(--warning-foreground))',
        destructive: 'oklch(var(--destructive))',
        'destructive-foreground': 'oklch(var(--destructive-foreground))',
      },
      borderRadius: ekpTokens.radius,
      fontFamily: ekpTokens.fontFamily,
      boxShadow: ekpTokens.shadow,
      transitionDuration: {
        fast: '150',
        DEFAULT: '200',
        slow: '300',
      },
      transitionTimingFunction: {
        DEFAULT: ekpTokens.motion.easeDefault,
      },
    },
  },
  plugins: [],
};

export default config;
