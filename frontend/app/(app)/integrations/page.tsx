'use client';

import type { CSSProperties } from 'react';

import Link from 'next/link';

/**
 * Integrations landing — top-level source-integration module (ADR-0071).
 *
 * H7 reproduction of `references/design-mockups/integration-import/
 * 10-integrations-landing.html`: a SharePoint connector card (→ import wizard) +
 * a disabled "connect another source" affordance (Tier 2, H4 boundary). The
 * connection state is static ("Not connected") in 階段 1b — live probing needs a
 * configured tenant (D4, runbook).
 */

// One-off card layout matching the mockup's inline-styled `.conn-card` (same
// inline-style approach as the kb/new stepper). Values copied verbatim from the
// mockup so the visual is pixel-faithful (H7).
const connCard: CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: 16,
  padding: '16px 18px',
  marginBottom: 12,
};
const connLogo: CSSProperties = {
  width: 42,
  height: 42,
  borderRadius: 'var(--radius-sm)',
  display: 'grid',
  placeItems: 'center',
  flexShrink: 0,
  background: 'oklch(var(--muted))',
  color: 'oklch(var(--foreground))',
};
const connLogoSvg: CSSProperties = {
  width: 22,
  height: 22,
  stroke: 'currentColor',
  fill: 'none',
  strokeWidth: 1.5,
};
const connDesc: CSSProperties = {
  fontSize: 12.5,
  color: 'oklch(var(--muted-foreground))',
  lineHeight: 1.5,
  marginTop: 2,
};
const connActions: CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: 12,
  flexShrink: 0,
};
const mono: CSSProperties = { fontFamily: 'var(--font-mono)' };

export default function IntegrationsPage() {
  return (
    <div className="content">
      <div className="content-wide">
        <div className="page-header">
          <div>
            <h1 className="page-title">Integrations</h1>
            <p className="page-subtitle">
              Connect external content sources and import their documents into your
              knowledge bases.
            </p>
          </div>
        </div>

        <div className="banner banner-info" style={{ marginBottom: 20 }}>
          <div style={{ flex: 1, fontSize: 12.5, lineHeight: 1.55 }}>
            Imported documents run through the same Docling pipeline, profiles and
            per-KB config as local uploads. Source permissions are mapped to{' '}
            <span style={mono}>allowed_principals</span> (per ADR-0070 / ADR-0066).
          </div>
        </div>

        <div className="nav-section-label" style={{ padding: '0 2px 10px' }}>
          Available sources
        </div>
        <div className="card" style={connCard}>
          <div style={connLogo}>
            <svg viewBox="0 0 16 16" style={connLogoSvg}>
              <circle cx="4" cy="8" r="1.8" />
              <circle cx="12" cy="4" r="1.8" />
              <circle cx="12" cy="12" r="1.8" />
              <path d="M5.6 7.1l4.8-2.4M5.6 8.9l4.8 2.4" />
            </svg>
          </div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontSize: 14, fontWeight: 600 }}>SharePoint</div>
            <div style={connDesc}>
              Import documents from a SharePoint site granted{' '}
              <span style={mono}>Sites.Selected</span> access.
            </div>
          </div>
          <div style={connActions}>
            <span className="badge badge-muted">
              <span className="badge-dot" /> Not connected
            </span>
            <Link
              className="btn btn-primary btn-sm"
              href="/integrations/sharepoint/import"
            >
              Import documents &rarr;
            </Link>
          </div>
        </div>

        <div className="nav-section-label" style={{ padding: '14px 2px 10px' }}>
          More sources
        </div>
        <div className="card" style={{ ...connCard, opacity: 0.6 }}>
          <div style={{ ...connLogo, color: 'oklch(var(--muted-foreground))' }}>
            <svg viewBox="0 0 16 16" style={connLogoSvg}>
              <path d="M8 3.5v9M3.5 8h9" />
            </svg>
          </div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontSize: 14, fontWeight: 600 }}>Connect another source</div>
            <div style={connDesc}>
              Google Drive, Box, Confluence and more — planned for a later release.
            </div>
          </div>
          <div style={connActions}>
            <span className="badge badge-muted">Tier 2</span>
          </div>
        </div>
      </div>
    </div>
  );
}
