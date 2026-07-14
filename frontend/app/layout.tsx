import type { Metadata } from 'next';
import { Inter, JetBrains_Mono } from 'next/font/google';
import { NextIntlClientProvider } from 'next-intl';
import { getLocale } from 'next-intl/server';

import { Toaster } from '@/components/ui/sonner';
import { ThemeProvider } from '@/lib/providers/theme-provider';

// CSS load order matters: globals.css first (color tokens + Tailwind preflight),
// then styles-mockup.css (mockup direct adoption — body / layout / component
// classes, per W22 F1-pivot CSS-first rebuild 2026-05-17).
import './globals.css';
import './styles-mockup.css';

/**
 * Inter sans + JetBrains Mono — per `references/design-mockups/EKP Platform.html`
 * Google Fonts preconnect spec. Loaded via `next/font/google` for zero-runtime
 * cost + automatic preload + FOUT prevention. CSS variable assignment lets
 * `styles-mockup.css` body rule consume via `var(--font-sans)` /
 * `var(--font-mono)` chain (defined in styles-mockup.css :root).
 *
 * Weights 400/450/500/600/700 + 500/600 mono match mockup HTML <link> request.
 * `display: 'swap'` matches default Google Fonts preconnect behaviour.
 */
const inter = Inter({
  subsets: ['latin'],
  weight: ['400', '500', '600', '700'],
  variable: '--font-inter',
  display: 'swap',
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ['latin'],
  weight: ['400', '500', '600'],
  variable: '--font-jetbrains-mono',
  display: 'swap',
});

export const metadata: Metadata = {
  title: 'EKP — Enterprise Knowledge Platform',
  description: 'Self-built knowledge platform — Drive Project user manuals',
};

export default async function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  // Cookie-based locale (W103 F3, D-2 甲) — read the locale resolved by
  // i18n/request.ts so <html lang> + the client provider stay in sync (SSR-safe).
  const locale = await getLocale();

  return (
    <html
      lang={locale}
      suppressHydrationWarning
      // Apply `next/font` CSS variable class names at <html> so `styles-mockup.css`
      // `:root` `--font-sans: var(--font-inter), ...` resolution works for the
      // entire app + during SSR hydration.
      className={`${inter.variable} ${jetbrainsMono.variable}`}
    >
      <body>
        <NextIntlClientProvider>
          <ThemeProvider
            attribute="class"
            defaultTheme="system"
            enableSystem
            disableTransitionOnChange
          >
            {children}
            <Toaster />
          </ThemeProvider>
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
