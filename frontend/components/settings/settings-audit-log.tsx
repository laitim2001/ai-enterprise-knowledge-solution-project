'use client';

/**
 * `<SettingsAuditLog>` sub-card (W24-wave-c1 F5 — Account tab extension;
 * W24b-wave-c2 F6 — action_type filter + since picker + cursor pagination).
 *
 * Reads audit_log rows via `adminApi.listAuditLog`. F6 delivers the filter +
 * "Load more" pagination the W24-c1 surface pre-committed to. Local-state
 * pattern (useEffect + useState) per the Wave C2 settings-cluster convention
 * — no TanStack here (D3.1 precedent). Has no mockup counterpart: the audit
 * surface is a functional retention promote, not a mockup visual element.
 */

import { Activity, Loader2 } from 'lucide-react';
import { useTranslations } from 'next-intl';
import { useCallback, useEffect, useState } from 'react';

import { adminApi, type AuditAction, type AuditLogEntry } from '@/lib/api/admin';

const PAGE_SIZE = 10;

// action_type options — 'all' clears the filter. Labels mirror the badge
// rendering ('_' → space) so the dropdown reads like the table column.
const ACTION_OPTIONS: { value: AuditAction | 'all'; label: string }[] = [
  { value: 'all', label: 'All actions' },
  { value: 'connection_patch', label: 'connection patch' },
  { value: 'connection_test', label: 'connection test' },
  { value: 'connection_rotate_secret', label: 'connection rotate secret' },
  { value: 'identity_patch', label: 'identity patch' },
  {
    value: 'api_keys_alert_threshold_patch',
    label: 'api keys alert threshold patch',
  },
];

function errMessage(err: unknown, fallback: string): string {
  return err instanceof Error ? err.message : fallback;
}

export function SettingsAuditLog() {
  const t = useTranslations('SettingsAudit');
  const [entries, setEntries] = useState<AuditLogEntry[] | null>(null);
  const [nextCursor, setNextCursor] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loadingMore, setLoadingMore] = useState(false);

  const [actionFilter, setActionFilter] = useState<AuditAction | 'all'>('all');
  const [since, setSince] = useState('');

  const isFiltered = actionFilter !== 'all' || since !== '';

  // Fresh fetch whenever a filter changes — resets the accumulator.
  useEffect(() => {
    let cancelled = false;
    setEntries(null);
    setError(null);
    void adminApi
      .listAuditLog({
        limit: PAGE_SIZE,
        action_type: actionFilter === 'all' ? undefined : actionFilter,
        since: since || undefined,
      })
      .then((page) => {
        if (cancelled) return;
        setEntries(page.entries);
        setNextCursor(page.next_cursor);
      })
      .catch((err: unknown) => {
        if (!cancelled) setError(errMessage(err, t('errFallbackLoad')));
      });
    return () => {
      cancelled = true;
    };
    // `t` 只用於 error fallback 文案,不入 deps —— 否則 translator identity 變動
    // 會觸發整份 audit log 重新抓取。
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [actionFilter, since]);

  const loadMore = useCallback(() => {
    if (nextCursor == null || loadingMore) return;
    setLoadingMore(true);
    void adminApi
      .listAuditLog({
        limit: PAGE_SIZE,
        action_type: actionFilter === 'all' ? undefined : actionFilter,
        since: since || undefined,
        cursor: nextCursor,
      })
      .then((page) => {
        setEntries((prev) => [...(prev ?? []), ...page.entries]);
        setNextCursor(page.next_cursor);
      })
      .catch((err: unknown) => {
        setError(errMessage(err, t('errFallbackLoadMore')));
      })
      .finally(() => setLoadingMore(false));
    // `t` 同上 —— 只用於 error fallback,不入 deps。
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [nextCursor, loadingMore, actionFilter, since]);

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
            {t('title')}
          </h3>
          <div className="card-desc">{t('desc')}</div>
        </div>
      </div>
      <div className="card-body card-body-tight">
        <div
          style={{
            display: 'flex',
            gap: 12,
            padding: '10px 16px',
            alignItems: 'flex-end',
            flexWrap: 'wrap',
            borderBottom: '1px solid oklch(var(--border))',
          }}
        >
          <div className="field" style={{ marginBottom: 0 }}>
            <label className="label" htmlFor="audit-action">
              {t('filterAction')}
            </label>
            <select
              id="audit-action"
              className="select"
              value={actionFilter}
              onChange={(e) =>
                setActionFilter(e.target.value as AuditAction | 'all')
              }
            >
              {ACTION_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.value === 'all' ? t('actionAll') : o.label}
                </option>
              ))}
            </select>
          </div>
          <div className="field" style={{ marginBottom: 0 }}>
            <label className="label" htmlFor="audit-since">
              {t('filterSince')}
            </label>
            <input
              id="audit-since"
              type="date"
              className="input"
              value={since}
              onChange={(e) => setSince(e.target.value)}
            />
          </div>
        </div>

        {error ? (
          <div
            className="text-xs"
            style={{ padding: '12px 16px', color: 'oklch(var(--destructive))' }}
          >
            {t('loadFailed')} <span className="mono">{error}</span>
          </div>
        ) : !entries ? (
          <div
            className="text-xs muted"
            style={{
              padding: '12px 16px',
              display: 'flex',
              alignItems: 'center',
              gap: 6,
            }}
          >
            <Loader2 size={12} className="animate-spin" aria-hidden="true" />
            {t('loading')}
          </div>
        ) : entries.length === 0 ? (
          <div
            className="text-xs muted"
            style={{ padding: '12px 16px', lineHeight: 1.5 }}
          >
            {isFiltered ? t('emptyFiltered') : t('empty')}
          </div>
        ) : (
          <>
            <table className="table">
              <thead>
                <tr>
                  <th>{t('colWhen')}</th>
                  <th>{t('colActor')}</th>
                  <th>{t('colAction')}</th>
                  <th>{t('colResource')}</th>
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
            {nextCursor != null && (
              <div
                style={{
                  padding: '10px 16px',
                  display: 'flex',
                  justifyContent: 'center',
                }}
              >
                <button
                  type="button"
                  className="btn btn-secondary btn-sm"
                  onClick={loadMore}
                  disabled={loadingMore}
                >
                  {loadingMore ? (
                    <>
                      <Loader2
                        size={12}
                        className="animate-spin"
                        aria-hidden="true"
                      />
                      {t('loadingMore')}
                    </>
                  ) : (
                    t('loadMore')
                  )}
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
