'use client';

/**
 * `<SettingsApiKeys>` tab (W24-wave-c1 F5 per ADR-0026 + mockup line
 * 744-823 SettingsApiKeys decomposition).
 *
 * 3 sections per F4 backend:
 *  - 4-stat strip (api_calls_24h / spend_today / token_throughput_tpm / rate_limit_hits)
 *  - Outgoing API quotas — per-deployment TPM/RPM bars + alert threshold % editable
 *  - Incoming API keys — Tier 2 disabled affordance (mockup line 792-818)
 *
 * Per F4 plan deviation: alert_threshold_pct is the editable knob (cap edit
 * deferred Wave B+ — Azure portal authoritative).
 *
 * W24b-wave-c2 F2: the alert-threshold edit is react-hook-form + zod
 * (`alertThresholdSchema`) — surfaces a 50-95 range error inline.
 */

import { zodResolver } from '@hookform/resolvers/zod';
import { KeyRound, Loader2 } from 'lucide-react';
import { useTranslations } from 'next-intl';
import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';

import { DisabledAffordance } from '@/components/ui/disabled-affordance';
import {
  adminApi,
  type IncomingKeysDisabled,
  type OutgoingQuotaList,
  type OutgoingQuotaRow,
  type UsageStats4Stat,
} from '@/lib/api/admin';
import {
  alertThresholdSchema,
  type AlertThresholdInput,
} from '@/lib/schemas/admin/api_keys';

function formatNum(n: number | null): string {
  if (n == null) return '—';
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}k`;
  return n.toLocaleString();
}

export function SettingsApiKeys() {
  const t = useTranslations('SettingsApiKeys');
  const [stats, setStats] = useState<UsageStats4Stat | null>(null);
  const [outgoing, setOutgoing] = useState<OutgoingQuotaList | null>(null);
  const [incoming, setIncoming] = useState<IncomingKeysDisabled | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    Promise.all([
      adminApi.getUsageStats(),
      adminApi.getOutgoingQuotas(),
      adminApi.getIncomingKeys(),
    ])
      .then(([s, o, i]) => {
        if (!cancelled) {
          setStats(s);
          setOutgoing(o);
          setIncoming(i);
        }
      })
      .catch((err) => {
        if (!cancelled) setError(err.message ?? 'Failed to load usage stats');
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (error) {
    return (
      <div className="banner banner-destructive">
        {t('loadFailed')} <span className="mono">{error}</span>
      </div>
    );
  }
  if (!stats || !outgoing || !incoming) {
    return (
      <div
        className="banner banner-info"
        style={{ display: 'flex', alignItems: 'center', gap: 8 }}
      >
        <Loader2 size={14} className="animate-spin" aria-hidden="true" />
        {t('loading')}
      </div>
    );
  }

  return (
    <div className="col" style={{ gap: 16 }}>
      {/* 4-stat strip */}
      <div
        className="stat-grid"
        style={{ gridTemplateColumns: 'repeat(4, 1fr)' }}
      >
        <Stat
          label={t('statApiCalls')}
          value={formatNum(stats.api_calls_24h)}
          sub={
            stats.realtime_status === 'no_client'
              ? t('subLangfuseNotWired')
              : stats.api_calls_delta_pct != null
                ? t('subVsPrior', {
                    arrow: stats.api_calls_delta_pct > 0 ? '↑' : '↓',
                    pct: Math.abs(stats.api_calls_delta_pct).toFixed(1),
                  })
                : t('subLast24h')
          }
        />
        <Stat
          label={t('statSpend')}
          value={`$${stats.spend_today_usd.toFixed(2)}`}
          sub={t('spendSub', {
            cap: stats.spend_cap_daily_usd.toFixed(0),
            pct: stats.spend_pct_used.toFixed(0),
          })}
          warn={stats.spend_pct_used >= 80}
        />
        <Stat
          label={t('statToken')}
          value={t('tokenPerMin', {
            value: formatNum(stats.token_throughput_tpm),
          })}
          sub={
            stats.token_throughput_p95_in_cap
              ? t('subP95InCap')
              : t('subP95OverCap')
          }
        />
        <Stat
          label={t('statRateLimit')}
          value={stats.rate_limit_hits_24h.toString()}
          sub={
            stats.rate_limit_hits_24h === 0
              ? t('subAllClear')
              : t('subInvestigate')
          }
          warn={stats.rate_limit_hits_24h > 0}
        />
      </div>

      {/* Outgoing API quotas */}
      <div className="card">
        <div className="card-header">
          <div>
            <h3 className="card-title">{t('outgoingTitle')}</h3>
            <div className="card-desc">{t('outgoingDesc')}</div>
          </div>
        </div>
        <div className="card-body card-body-tight">
          {outgoing.rows.map((row, idx) => (
            <OutgoingQuotaRowItem
              key={`${row.provider_id}/${row.deployment_id}`}
              row={row}
              isLast={idx === outgoing.rows.length - 1}
            />
          ))}
        </div>
      </div>

      {/* Incoming API keys — Tier 2 */}
      <div className="card">
        <div className="card-header">
          <div>
            <h3 className="card-title">
              {t('incomingTitle')}{' '}
              <span className="badge badge-muted" style={{ marginLeft: 4 }}>
                Tier 2
              </span>
            </h3>
            <div className="card-desc">{t('incomingDesc')}</div>
          </div>
          <DisabledAffordance
            variant="p1-strict"
            reason={incoming.reason}
            tier2Trigger={incoming.tier2_trigger}
          >
            <button className="btn btn-secondary btn-sm" disabled>
              <KeyRound size={13} aria-hidden="true" /> {t('generateKey')}
            </button>
          </DisabledAffordance>
        </div>
        <div className="card-body card-body-tight">
          <div
            style={{
              padding: '12px 16px',
              fontSize: 12,
              color: 'oklch(var(--muted-foreground))',
              lineHeight: 1.5,
            }}
          >
            {incoming.reason} {t('promotionTriggerLabel')}{' '}
            {incoming.tier2_trigger}.
          </div>
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// Sub-components
// ============================================================================

function Stat({
  label,
  value,
  sub,
  warn = false,
}: {
  label: string;
  value: string;
  sub: string;
  warn?: boolean;
}) {
  return (
    <div className="stat">
      <div className="stat-label">{label}</div>
      <div
        className="stat-value"
        style={warn ? { color: 'oklch(var(--warning))' } : {}}
      >
        {value}
      </div>
      <div className="stat-sub">{sub}</div>
    </div>
  );
}

function OutgoingQuotaRowItem({
  row,
  isLast,
}: {
  row: OutgoingQuotaRow;
  isLast: boolean;
}) {
  const t = useTranslations('SettingsApiKeys');
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isDirty, isSubmitting },
  } = useForm<AlertThresholdInput>({
    resolver: zodResolver(alertThresholdSchema),
    defaultValues: { alert_threshold_pct: row.alert_threshold_pct },
  });

  const onSubmit = handleSubmit(async (data) => {
    const updated = await adminApi.patchAlertThreshold(
      row.provider_id,
      row.deployment_id,
      data.alert_threshold_pct,
    );
    // Re-baseline the form so `isDirty` clears after a successful save.
    reset({ alert_threshold_pct: updated.alert_threshold_pct });
  });

  const tpmPct = row.cap_tpm ? row.used_tpm / row.cap_tpm : 0;
  const rpmPct = row.cap_rpm ? row.used_rpm / row.cap_rpm : 0;
  const unit = row.quota_unit === 'emails' ? 'EMAILS / min' : 'TPM';
  const badgeClass =
    row.status === 'over_limit'
      ? 'badge badge-destructive'
      : row.status === 'warning'
        ? 'badge badge-warning'
        : 'badge badge-success';
  const inputId = `th-${row.provider_id}-${row.deployment_id}`;

  return (
    <div
      style={{
        padding: '14px 18px',
        borderBottom: isLast ? 'none' : '1px solid oklch(var(--border))',
      }}
    >
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          marginBottom: 8,
        }}
      >
        <span style={{ fontSize: 13, fontWeight: 500, flex: 1 }}>
          {row.display_name}
        </span>
        <span className={badgeClass}>
          <span className="badge-dot" />{' '}
          {row.status.replace('_', ' ').toUpperCase()}
        </span>
      </div>
      <div
        style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}
      >
        <QuotaBar label={unit} used={row.used_tpm} cap={row.cap_tpm} pct={tpmPct} />
        <QuotaBar label="RPM" used={row.used_rpm} cap={row.cap_rpm} pct={rpmPct} />
      </div>
      <form onSubmit={onSubmit} style={{ marginTop: 10 }}>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            fontSize: 12,
          }}
        >
          <label htmlFor={inputId}>{t('alertThreshold')}</label>
          <input
            id={inputId}
            type="number"
            className="input mono"
            min={50}
            max={95}
            aria-invalid={errors.alert_threshold_pct ? 'true' : undefined}
            {...register('alert_threshold_pct', { valueAsNumber: true })}
            style={{ width: 72, height: 28, fontSize: 12 }}
          />
          <span>%</span>
          <button
            type="submit"
            className="btn btn-ghost btn-sm"
            disabled={!isDirty || isSubmitting}
          >
            {isSubmitting ? (
              <Loader2 size={12} className="animate-spin" aria-hidden="true" />
            ) : null}{' '}
            {t('save')}
          </button>
        </div>
        {errors.alert_threshold_pct ? (
          <div
            className="hint"
            style={{ color: 'oklch(var(--destructive))', marginTop: 4 }}
          >
            {errors.alert_threshold_pct.message}
          </div>
        ) : null}
      </form>
    </div>
  );
}

function QuotaBar({
  label,
  used,
  cap,
  pct,
}: {
  label: string;
  used: number;
  cap: number | null;
  pct: number;
}) {
  const color =
    pct > 0.8
      ? 'oklch(var(--destructive))'
      : pct > 0.5
        ? 'oklch(var(--warning))'
        : 'oklch(var(--success))';
  return (
    <div>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          marginBottom: 4,
        }}
      >
        <span
          className="text-xs muted mono"
          style={{ letterSpacing: '0.04em' }}
        >
          {label}
        </span>
        <span className="mono text-xs" style={{ fontWeight: 500 }}>
          {used.toLocaleString()} / {cap?.toLocaleString() ?? '∞'}{' '}
          <span className="muted">({(pct * 100).toFixed(0)}%)</span>
        </span>
      </div>
      <div
        style={{
          height: 5,
          background: 'oklch(var(--muted))',
          borderRadius: 999,
          overflow: 'hidden',
        }}
      >
        <div
          style={{
            width: `${Math.min(100, pct * 100)}%`,
            height: '100%',
            background: color,
            borderRadius: 999,
          }}
        />
      </div>
    </div>
  );
}
