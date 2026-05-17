'use client';

/**
 * V8 + V9 shared auth-page frame — direct-copy from mockup
 * `references/design-mockups/ekp-page-auth.jsx:178-287` AuthFrame
 * (per CLAUDE.md §5.7 H7 strict fidelity 2026-05-18 user directive —
 * W22 F2 rebuild;supersedes W17 F2 BrandPanel + W20 F7 strict-fidelity
 * refactor which used Tailwind + shadcn primitives).
 *
 * 2-column grid (mockup `gridTemplateColumns: "1fr 1fr"`):
 *   - Left brand panel (primary bg + decorative dot pattern + logo +
 *     workspace name + tagline + 3 metric badges + build footer)
 *   - Right form pane (top toggle row + centred form + bottom mono footer)
 *
 * `mode="login" | "register"` switches the form-pane bottom footer copy
 * (login = "MSAL session · httpOnly cookie · scrypt password · CSRF protected";
 * register inherits same line per mockup).
 *
 * Auth pages render OUTSIDE `app/(app)/` so no AppShell — this is its own
 * full-viewport layout (per ADR-0024 + W18 F7 login-page-no-app-chrome rule).
 *
 * Mockup CSS classes directly consumed: `.btn .btn-ghost .btn-icon .btn-sm`.
 * Mockup decorative SVG dot pattern preserved 1:1.
 */

import { Globe, Layers, Sparkles } from 'lucide-react';
import { useTheme } from 'next-themes';

interface AuthFrameProps {
  children: React.ReactNode;
}

export function AuthFrame({ children }: AuthFrameProps) {
  const { resolvedTheme, setTheme } = useTheme();
  const isDark = resolvedTheme === 'dark';

  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: '1fr 1fr',
        height: '100vh',
        background: 'oklch(var(--background))',
      }}
    >
      {/* Brand panel (left) — direct copy mockup `AuthFrame` lines 187-255 */}
      <div
        style={{
          background: 'oklch(var(--primary))',
          color: 'oklch(var(--primary-foreground))',
          padding: '40px 48px',
          display: 'flex',
          flexDirection: 'column',
          position: 'relative',
          overflow: 'hidden',
        }}
      >
        {/* Decorative accent dots — mockup lines 197-204 */}
        <svg
          viewBox="0 0 400 400"
          style={{ position: 'absolute', inset: 0, opacity: 0.15 }}
          aria-hidden="true"
        >
          <defs>
            <pattern id="auth-dots" width="20" height="20" patternUnits="userSpaceOnUse">
              <circle cx="2" cy="2" r="1" fill="oklch(var(--primary-foreground))" />
            </pattern>
          </defs>
          <rect width="400" height="400" fill="url(#auth-dots)" />
        </svg>

        {/* Logo block — mockup lines 206-219 */}
        <div
          style={{
            position: 'relative',
            zIndex: 1,
            display: 'flex',
            alignItems: 'center',
            gap: 12,
          }}
        >
          <div
            style={{
              width: 36,
              height: 36,
              borderRadius: 'var(--radius-sm)',
              background: 'oklch(var(--accent))',
              color: 'oklch(var(--accent-foreground))',
              display: 'grid',
              placeItems: 'center',
              fontFamily: 'var(--font-mono)',
              fontWeight: 700,
              fontSize: 14,
            }}
          >
            EKP
          </div>
          <div>
            <div style={{ fontWeight: 600, fontSize: 15 }}>
              Enterprise Knowledge Platform
            </div>
            <div
              style={{
                fontSize: 12,
                opacity: 0.7,
                fontFamily: 'var(--font-mono)',
              }}
            >
              ekp-beta.ricoh.com
            </div>
          </div>
        </div>

        {/* Tagline + metric badges — mockup lines 221-250 */}
        <div
          style={{
            position: 'relative',
            zIndex: 1,
            marginTop: 'auto',
            marginBottom: 'auto',
          }}
        >
          <div
            style={{
              fontSize: 28,
              fontWeight: 600,
              lineHeight: 1.25,
              letterSpacing: '-0.022em',
              marginBottom: 14,
              textWrap: 'balance',
            }}
          >
            Knowledge retrieval, grounded in your real documents.
          </div>
          <div
            style={{
              fontSize: 14,
              lineHeight: 1.6,
              opacity: 0.8,
              maxWidth: 380,
            }}
          >
            Hybrid retrieval · Cohere v4.0-pro rerank · CRAG self-correction · 9-stage trace · Image-grounded citations.
          </div>

          <div
            style={{
              marginTop: 28,
              display: 'flex',
              flexDirection: 'column',
              gap: 10,
              fontSize: 12.5,
            }}
          >
            {(
              [
                ['R@5 = 97.2%', 'Drive Manuals · D365 F&O ERP corpus'],
                ['P95 latency 4.2s', '9-stage Langfuse trace per query'],
                ['100% oklch tokens', 'Light + dark, no Dify dependency'],
              ] as const
            ).map(([metric, sub]) => (
              <div
                key={metric}
                style={{ display: 'flex', gap: 12, alignItems: 'center' }}
              >
                <span
                  style={{
                    fontFamily: 'var(--font-mono)',
                    fontWeight: 600,
                    width: 130,
                    background: 'oklch(var(--accent) / 0.2)',
                    border: '1px solid oklch(var(--accent) / 0.4)',
                    color: 'oklch(var(--accent))',
                    padding: '3px 8px',
                    borderRadius: 3,
                    textAlign: 'center',
                  }}
                >
                  {metric}
                </span>
                <span style={{ opacity: 0.75 }}>{sub}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Build footer — mockup lines 252-254 */}
        <div
          style={{
            position: 'relative',
            zIndex: 1,
            fontSize: 11.5,
            opacity: 0.6,
            fontFamily: 'var(--font-mono)',
          }}
        >
          © Ricoh · RAPO · v0.18.0-beta · Build 2026-05-15
        </div>
      </div>

      {/* Form panel (right) — direct copy mockup lines 258-284 */}
      <div
        style={{
          padding: '40px 48px',
          display: 'flex',
          flexDirection: 'column',
          overflowY: 'auto',
          position: 'relative',
        }}
      >
        {/* Top toggle row */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <div className="spacer" />
          <button
            type="button"
            className="btn btn-ghost btn-icon btn-sm"
            title={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
            onClick={() => setTheme(isDark ? 'light' : 'dark')}
            aria-label="Toggle theme"
          >
            {isDark ? <Sparkles size={14} /> : <Layers size={14} />}
          </button>
          {/* Language toggle — Tier 2 disabled per W19 F5 catalog */}
          <button
            type="button"
            disabled
            aria-disabled="true"
            className="btn btn-ghost btn-icon btn-sm"
            title="Language (Tier 2 — coming soon)"
            aria-label="Language (Tier 2)"
            style={{ opacity: 0.5, cursor: 'default' }}
          >
            <Globe size={14} />
          </button>
        </div>

        {/* Centred form area */}
        <div
          style={{
            flex: 1,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <div style={{ width: '100%', maxWidth: 380 }}>{children}</div>
        </div>

        {/* Form-pane bottom footer */}
        <div
          style={{
            textAlign: 'center',
            fontSize: 11.5,
            color: 'oklch(var(--muted-foreground))',
            fontFamily: 'var(--font-mono)',
          }}
        >
          MSAL session · httpOnly cookie · scrypt password · CSRF protected
        </div>
      </div>
    </div>
  );
}

/** Shared horizontal divider with center label — mockup `Divider` lines 289-297. */
export function AuthDivider({ label }: { label: string }) {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 10,
        margin: '16px 0',
        color: 'oklch(var(--muted-foreground))',
        fontSize: 11.5,
      }}
    >
      <div style={{ flex: 1, height: 1, background: 'oklch(var(--border))' }} />
      <span>{label}</span>
      <div style={{ flex: 1, height: 1, background: 'oklch(var(--border))' }} />
    </div>
  );
}

/** Microsoft 4-square brand mark — direct copy mockup `MicrosoftIcon` lines 299-308. */
export function MicrosoftIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" style={{ flexShrink: 0 }} aria-hidden="true">
      <rect x="2" y="2" width="9.5" height="9.5" fill="#F25022" />
      <rect x="12.5" y="2" width="9.5" height="9.5" fill="#7FBA00" />
      <rect x="2" y="12.5" width="9.5" height="9.5" fill="#00A4EF" />
      <rect x="12.5" y="12.5" width="9.5" height="9.5" fill="#FFB900" />
    </svg>
  );
}
