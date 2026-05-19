'use client';

/**
 * `<DeploymentsTable>` primitive (W24-wave-c1 F5 per ADR-0026 + mockup line
 * 110-115 `deployments` array shape).
 *
 * Renders the per-provider deployment list as a tight table with model
 * family + capacity TPM + alert threshold % + status. Stylistically mirrors
 * the F4 OutgoingQuotaRow flatten but scoped to one provider (e.g. Azure
 * OpenAI with 4 deployments rendered as one DeploymentsTable inside one
 * ServiceCard).
 *
 * Wave C1 is **read-only**; cap edit defers Wave B+ (Azure portal level
 * authoritative per F4 plan).
 */

import type { ProviderDeployment } from '@/lib/api/admin';

interface DeploymentsTableProps {
  deployments: ProviderDeployment[];
  /** Empty-state copy when the provider has no deployments. */
  emptyMessage?: string;
}

function formatTpm(n: number | null): string {
  if (n == null) return '—';
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(0)}k`;
  return String(n);
}

export function DeploymentsTable({
  deployments,
  emptyMessage = 'No deployments configured for this provider.',
}: DeploymentsTableProps) {
  if (deployments.length === 0) {
    return (
      <div className="text-xs muted" style={{ padding: '8px 0' }}>
        {emptyMessage}
      </div>
    );
  }

  return (
    <table className="table">
      <thead>
        <tr>
          <th>Deployment</th>
          <th>Family</th>
          <th className="col-num">TPM cap</th>
          <th className="col-num">RPM cap</th>
          <th className="col-num">Alert %</th>
        </tr>
      </thead>
      <tbody>
        {deployments.map((d) => (
          <tr key={d.deployment_id}>
            <td>
              <span className="mono text-xs">{d.deployment_name}</span>
            </td>
            <td>
              <span className="badge badge-muted">{d.model_family}</span>
            </td>
            <td className="col-num mono text-xs">{formatTpm(d.tpm_limit)}</td>
            <td className="col-num mono text-xs">{formatTpm(d.rpm_limit)}</td>
            <td className="col-num mono text-xs">{d.alert_threshold_pct}%</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
