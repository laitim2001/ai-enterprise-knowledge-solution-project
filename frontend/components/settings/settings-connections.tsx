'use client';

/**
 * `<SettingsConnections>` tab (W24-wave-c1 F5 per ADR-0026 + mockup line
 * 96-355 SettingsConnections decomposition).
 *
 * Lists the 9 F2-seeded providers grouped by `ProviderCategory` (5 categories),
 * each rendered as a collapsible `<ServiceCard>`. Inside an expanded card:
 *  - endpoint + region + last test status header (`<ServiceCard>` slot)
 *  - secret_kv_ref + masked preview surface via `<ApiKeyInput>`
 *  - per-deployment table via `<DeploymentsTable>` (where applicable)
 *  - Test connection + Rotate secret mutation buttons
 *
 * Mockup labels live in `CATEGORY_LABEL` — backend `ProviderCategory` literal
 * values (`llm` / `retrieval` / `storage` / `observability` / `identity`)
 * map onto the mockup category headers.
 *
 * **Data-bound**: real `apiClient.admin.listConnections` + `getConnection`
 * round-trip on mount. No mock data.
 *
 * W24b-wave-c2 F3: each expanded ProviderRow gains an inline edit form
 * (endpoint / region / display name — react-hook-form + zod) with an
 * optimistic PATCH; Test connection + Rotate secret moved to `useMutation`.
 */

import { zodResolver } from '@hookform/resolvers/zod';
import { useMutation } from '@tanstack/react-query';
import { CheckCircle2, Loader2, PlugZap } from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';

import { ApiKeyInput } from '@/components/ui/api-key-input';
import { DeploymentsTable } from '@/components/ui/deployments-table';
import { ServiceCard } from '@/components/ui/service-card';
import {
  adminApi,
  type ProviderCategory,
  type ProviderConfig,
  type ProviderSummary,
  type TestStatus,
} from '@/lib/api/admin';
import {
  providerPatchSchema,
  type ProviderPatchInput,
} from '@/lib/schemas/admin/connections';

const CATEGORY_ORDER: ProviderCategory[] = [
  'llm',
  'retrieval',
  'storage',
  'observability',
  'identity',
];

const CATEGORY_LABEL: Record<ProviderCategory, string> = {
  llm: 'LLM & Embedding',
  retrieval: 'Retrieval',
  storage: 'Search & Storage',
  observability: 'Observability',
  identity: 'Identity & Email',
};

export function SettingsConnections() {
  const [summaries, setSummaries] = useState<ProviderSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    void adminApi
      .listConnections()
      .then((rows) => {
        if (!cancelled) setSummaries(rows);
      })
      .catch((err) => {
        if (!cancelled) setError(err.message ?? 'Failed to load connections');
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (error) {
    return (
      <div className="banner banner-destructive">
        Failed to load connections: <span className="mono">{error}</span>
      </div>
    );
  }
  if (!summaries) {
    return (
      <div
        className="banner banner-info"
        style={{ display: 'flex', alignItems: 'center', gap: 8 }}
      >
        <Loader2 size={14} className="animate-spin" aria-hidden="true" />
        Loading connections…
      </div>
    );
  }

  // Group by category preserving the canonical order.
  const grouped = CATEGORY_ORDER.map((cat) => ({
    category: cat,
    label: CATEGORY_LABEL[cat],
    rows: summaries.filter((s) => s.category === cat),
  })).filter((g) => g.rows.length > 0);

  return (
    <div className="col" style={{ gap: 16 }}>
      <div className="banner banner-info">
        <PlugZap size={14} aria-hidden="true" />
        <div style={{ flex: 1, lineHeight: 1.55 }}>
          <div style={{ fontSize: 13, fontWeight: 500 }}>
            External service connections
          </div>
          <div className="text-xs muted">
            Every endpoint, secret, and connection string is managed here
            (persisted in Azure Key Vault when configured; `.env` fallback
            in dev). Secret values are never shown — only masked previews.
          </div>
        </div>
      </div>

      {grouped.map((g) => (
        <div key={g.category}>
          <h2
            style={{
              fontSize: 12,
              fontWeight: 600,
              textTransform: 'uppercase',
              letterSpacing: '0.06em',
              color: 'oklch(var(--muted-foreground))',
              marginBottom: 8,
            }}
          >
            {g.label}
          </h2>
          {g.rows.map((row) => (
            <ProviderRow key={row.provider_id} summary={row} />
          ))}
        </div>
      ))}
    </div>
  );
}

// ============================================================================
// ProviderRow — collapsible card with on-demand detail fetch
// ============================================================================

/**
 * What the inline edit form submits — narrower than `ProviderPatch`: the form
 * always sends a concrete `display_name`, so `{ ...detail, ...patch }` in the
 * optimistic merge type-checks against `ProviderConfig` (whose `display_name`
 * is non-null).
 */
type ConnectionEdit = {
  endpoint_url: string | null;
  region: string | null;
  display_name: string;
};

function ProviderRow({ summary }: { summary: ProviderSummary }) {
  const [detail, setDetail] = useState<ProviderConfig | null>(null);
  const [loading, setLoading] = useState(false);
  const [lastTestDetail, setLastTestDetail] = useState<string | null>(null);

  const ensureDetail = useCallback(async (): Promise<void> => {
    if (detail) return;
    setLoading(true);
    try {
      setDetail(await adminApi.getConnection(summary.provider_id));
    } finally {
      setLoading(false);
    }
  }, [detail, summary.provider_id]);

  // Edit form — the 3 ProviderPatch fields. `values` keeps the form synced
  // with `detail`, which loads after mount and is mutated optimistically.
  const {
    register,
    handleSubmit,
    formState: { errors, isDirty },
  } = useForm<ProviderPatchInput>({
    resolver: zodResolver(providerPatchSchema),
    values: {
      endpoint_url: detail?.endpoint_url ?? '',
      region: detail?.region ?? '',
      display_name: detail?.display_name ?? '',
    },
  });

  // Optimistic PATCH — snapshot `detail`, apply the patch locally, roll back
  // on error, replace with the server truth on success.
  const patchMutation = useMutation({
    mutationFn: (patch: ConnectionEdit) =>
      adminApi.updateConnection(summary.provider_id, patch),
    onMutate: (patch) => {
      const snapshot = detail;
      if (detail) setDetail({ ...detail, ...patch });
      return { snapshot };
    },
    onError: (_error, _patch, context) => {
      if (context) setDetail(context.snapshot);
    },
    onSuccess: (updated) => setDetail(updated),
  });

  const testMutation = useMutation({
    mutationFn: () => adminApi.testConnection(summary.provider_id),
    onSuccess: (result) => {
      setLastTestDetail(result.detail);
      setDetail((d) =>
        d
          ? {
              ...d,
              last_test_status: result.status,
              last_test_detail: result.detail,
            }
          : d,
      );
    },
  });

  const rotateMutation = useMutation({
    mutationFn: () => adminApi.rotateSecret(summary.provider_id),
    onSuccess: (result) => {
      setDetail((d) =>
        d
          ? {
              ...d,
              last_rotated_at: result.last_rotated_at,
              secret_masked_preview: result.secret_masked_preview,
            }
          : d,
      );
    },
  });

  const onSubmit = handleSubmit((data) => {
    patchMutation.mutate({
      // Empty endpoint / region collapse to null — backend models them as
      // `str | None`, so a cleared field means "unset" not "stored ''".
      endpoint_url: data.endpoint_url ? data.endpoint_url : null,
      region: data.region ? data.region : null,
      display_name: data.display_name ?? '',
    });
  });

  // The card's status badge reads from the detail (if loaded) or the summary.
  const status: TestStatus = detail?.last_test_status ?? summary.last_test_status;
  const idBase = summary.provider_id;

  return (
    <ServiceCard
      displayName={summary.display_name}
      region={detail?.region ?? null}
      status={status}
    >
      {/* Lazy-fetch detail on first expand. */}
      {!detail ? (
        <div
          className="text-xs muted"
          style={{ padding: '8px 0', display: 'flex', alignItems: 'center', gap: 6 }}
        >
          {loading ? (
            <>
              <Loader2 size={12} className="animate-spin" aria-hidden="true" />
              Loading provider config…
            </>
          ) : (
            <button
              type="button"
              className="btn btn-ghost btn-sm"
              onClick={() => void ensureDetail()}
            >
              Load configuration
            </button>
          )}
        </div>
      ) : (
        <>
          {/* Inline edit form — endpoint / region / display name. */}
          <form onSubmit={onSubmit} style={{ marginBottom: 14 }}>
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: '1fr 1fr',
                gap: 12,
                marginBottom: 10,
              }}
            >
              <div className="field" style={{ marginBottom: 0 }}>
                <label className="label" htmlFor={`dn-${idBase}`}>
                  Display name
                </label>
                <input
                  id={`dn-${idBase}`}
                  className="input"
                  aria-invalid={errors.display_name ? 'true' : undefined}
                  {...register('display_name')}
                />
                {errors.display_name ? (
                  <div
                    className="hint"
                    style={{ color: 'oklch(var(--destructive))' }}
                  >
                    {errors.display_name.message}
                  </div>
                ) : null}
              </div>
              <div className="field" style={{ marginBottom: 0 }}>
                <label className="label" htmlFor={`rg-${idBase}`}>
                  Region
                </label>
                <input
                  id={`rg-${idBase}`}
                  className="input"
                  {...register('region')}
                />
              </div>
              <div
                className="field"
                style={{ gridColumn: '1 / -1', marginBottom: 0 }}
              >
                <label className="label" htmlFor={`ep-${idBase}`}>
                  Endpoint URL
                </label>
                <input
                  id={`ep-${idBase}`}
                  className="input mono"
                  aria-invalid={errors.endpoint_url ? 'true' : undefined}
                  {...register('endpoint_url')}
                  style={{ fontSize: 12 }}
                />
                {errors.endpoint_url ? (
                  <div
                    className="hint"
                    style={{ color: 'oklch(var(--destructive))' }}
                  >
                    {errors.endpoint_url.message}
                  </div>
                ) : null}
              </div>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <button
                type="submit"
                className="btn btn-secondary btn-sm"
                disabled={!isDirty || patchMutation.isPending}
              >
                {patchMutation.isPending ? (
                  <Loader2 size={12} className="animate-spin" aria-hidden="true" />
                ) : null}{' '}
                Save changes
              </button>
              {patchMutation.isError ? (
                <span
                  className="text-xs"
                  style={{ color: 'oklch(var(--destructive))' }}
                >
                  {patchMutation.error?.message ?? 'Update failed'}
                </span>
              ) : null}
            </div>
          </form>

          {/* Secret row (only when secret_kv_ref present). */}
          {detail.secret_kv_ref ? (
            <div className="field" style={{ marginBottom: 12 }}>
              <label className="label">
                Secret · <span className="mono text-xs">{detail.secret_kv_ref}</span>
              </label>
              <ApiKeyInput
                value={detail.secret_masked_preview}
                onRotate={() => rotateMutation.mutate()}
                rotateDisabled={rotateMutation.isPending}
                ariaLabel={`Secret for ${detail.display_name}`}
              />
              {detail.last_rotated_at ? (
                <div className="hint">
                  Last rotated{' '}
                  <span className="mono">{detail.last_rotated_at}</span>
                </div>
              ) : (
                <div className="hint">
                  Not rotated yet — click the refresh icon to mint a new value
                  in Key Vault.
                </div>
              )}
            </div>
          ) : (
            <div className="hint" style={{ marginBottom: 12 }}>
              Managed-identity provider — no rotatable secret.
            </div>
          )}

          {/* Deployments table (LLM providers). */}
          {detail.deployments.length > 0 ? (
            <div style={{ marginBottom: 12 }}>
              <div className="label" style={{ marginBottom: 6 }}>
                Deployments
              </div>
              <DeploymentsTable deployments={detail.deployments} />
            </div>
          ) : null}

          {/* Actions */}
          <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={() => testMutation.mutate()}
              disabled={testMutation.isPending}
            >
              {testMutation.isPending ? (
                <Loader2 size={12} className="animate-spin" aria-hidden="true" />
              ) : (
                <CheckCircle2 size={12} aria-hidden="true" />
              )}{' '}
              Test connection
            </button>
            {lastTestDetail ? (
              <span className="text-xs muted">{lastTestDetail}</span>
            ) : null}
          </div>
        </>
      )}
    </ServiceCard>
  );
}
