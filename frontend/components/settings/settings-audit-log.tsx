'use client';

/**
 * `<SettingsAuditLog>` sub-card (W24-wave-c1 F5 — Account tab extension).
 *
 * Reads the 10 most-recent audit_log rows via `adminApi.listAuditLog(10)`.
 * Tier 1 surfaces a tight read-only table; Wave C2 adds filter + pagination.
 *
 * Hooked into `<SettingsAccount>` per plan §2 F5.8 acceptance criteria.
 */

import { Activity, Loader2 } from 'lucide-react';
import { useEffect, useState } from 'react';

import { adminApi, type AuditLogEntry } from '@/lib/api/admin';

export function SettingsAuditLog() {
  const [entries, setEntries] = useState<AuditLogEntry[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    void adminApi
      .listAuditLog(10)
      .then((rows) => {
        if (!cancelled) setEntries(rows);
      })
      .catch((err) => {
        if (!cancelled) setError(err.message ?? 'Failed to load audit log');
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="card" style={{ marginBottom: 16 }}>
      <div className="card-header">
        <div>
          <h3 className="card-title">
            <Activity
              size={14}
              aria-hidden="true"
              style={{ verticalAlign: '-2px', marginRight: 4 }}
            />
            Audit log (last 10)
          </h3>
          <div className="card-desc">
            Write-only retention from Wave C1 — read surface promoted from
            F4 deferral. Wave C2 adds filter + pagination.
          </div>
        </div>
      </div>
      <div className="card-body card-body-tight">
        {error ? (
          <div className="text-xs" style={{ padding: '12px 16px', color: 'oklch(var(--destructive))' }}>
            Failed to load: <span className="mono">{error}</span>
          </div>
        ) : !entries ? (
          <div
            className="text-xs muted"
            style={{ padding: '12px 16px', display: 'flex', alignItems: 'center', gap: 6 }}
          >
            <Loader2 size={12} className="animate-spin" aria-hidden="true" />
            Loading audit log…
          </div>
        ) : entries.length === 0 ? (
          <div
            className="text-xs muted"
            style={{ padding: '12px 16px', lineHeight: 1.5 }}
          >
            No audit entries yet. Mutating Settings (Connections / Identity /
            API Keys) PATCH endpoints will populate this log.
          </div>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>When</th>
                <th>Actor</th>
                <th>Action</th>
                <th>Resource</th>
              </tr>
            </thead>
            <tbody>
              {entries.map((e) => (
                <tr key={e.id ?? `${e.created_at}-${e.resource}`}>
                  <td className="mono text-xs muted">{e.created_at}</td>
                  <td className="text-xs">{e.actor ?? 'system'}</td>
                  <td>
                    <span className="badge badge-muted">
                      {e.action.replace(/_/g, ' ')}
                    </span>
                  </td>
                  <td className="mono text-xs">{e.resource}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
