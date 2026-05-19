'use client';

/**
 * `<ServiceCard>` primitive (W24-wave-c1 F5 per ADR-0026 + mockup line 96-355
 * SettingsConnections decomposition).
 *
 * Renders a per-provider card with header (status badge + region + endpoint)
 * + collapsible body slot. Default-collapsed: clicking the header expands
 * into the configuration fields slot (any children).
 *
 * **Status badge variants** mirror the backend `TestStatus` literal
 * (`ok` / `degraded` / `error` / `not_tested`) — uses CSS-first `.badge`
 * classes per `references/design-mockups/styles-mockup.css`.
 */

import { ChevronDown, ChevronRight, ExternalLink } from 'lucide-react';
import { useState, type ReactNode } from 'react';

import type { TestStatus } from '@/lib/api/admin';

interface ServiceCardProps {
  displayName: string;
  /** Short description shown below the title, e.g. "LLM + Embedding + Judge". */
  role?: string;
  endpoint?: string | null;
  region?: string | null;
  status: TestStatus;
  /** Body content shown only when expanded. */
  children: ReactNode;
  /** When provided, header shows an "Open in Azure Portal" link button. */
  externalUrl?: string;
  /** Optional defaultExpanded override (default false). */
  defaultExpanded?: boolean;
}

const STATUS_LABEL: Record<TestStatus, string> = {
  ok: 'HEALTHY',
  degraded: 'DEGRADED',
  error: 'ERROR',
  not_tested: 'NOT TESTED',
};

const STATUS_BADGE_CLASS: Record<TestStatus, string> = {
  ok: 'badge badge-success',
  degraded: 'badge badge-warning',
  error: 'badge badge-destructive',
  not_tested: 'badge badge-muted',
};

export function ServiceCard({
  displayName,
  role,
  endpoint,
  region,
  status,
  children,
  externalUrl,
  defaultExpanded = false,
}: ServiceCardProps) {
  const [expanded, setExpanded] = useState(defaultExpanded);

  return (
    <div className="card" style={{ marginBottom: 12 }}>
      <button
        type="button"
        className="card-header"
        onClick={() => setExpanded(!expanded)}
        aria-expanded={expanded}
        style={{
          width: '100%',
          background: 'transparent',
          border: 0,
          cursor: 'pointer',
          textAlign: 'left',
          padding: 'var(--card-header-padding, 14px 18px)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flex: 1 }}>
          {expanded ? (
            <ChevronDown size={14} aria-hidden="true" />
          ) : (
            <ChevronRight size={14} aria-hidden="true" />
          )}
          <div style={{ flex: 1, minWidth: 0 }}>
            <h3 className="card-title" style={{ marginBottom: 2 }}>
              {displayName}
            </h3>
            {role ? <div className="card-desc">{role}</div> : null}
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {region ? <span className="text-xs muted">{region}</span> : null}
          <span className={STATUS_BADGE_CLASS[status]}>
            <span className="badge-dot" /> {STATUS_LABEL[status]}
          </span>
        </div>
      </button>
      {expanded ? (
        <div className="card-body">
          {endpoint ? (
            <div
              className="row"
              style={{
                marginBottom: 12,
                padding: '6px 0',
                borderBottom: '1px dashed oklch(var(--border))',
              }}
            >
              <span className="text-xs muted mono" style={{ flex: 1 }}>
                {endpoint}
              </span>
              {externalUrl ? (
                <a
                  className="btn btn-ghost btn-sm"
                  href={externalUrl}
                  target="_blank"
                  rel="noreferrer"
                >
                  <ExternalLink size={12} aria-hidden="true" /> Azure Portal
                </a>
              ) : null}
            </div>
          ) : null}
          {children}
        </div>
      ) : null}
    </div>
  );
}
