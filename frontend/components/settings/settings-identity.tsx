'use client';

/**
 * `<SettingsIdentity>` tab (W24-wave-c1 F5 per ADR-0026 + mockup line
 * 528-723 SettingsIdentity decomposition).
 *
 * 5 cards mapped 1:1 onto F3 backend sub-resources:
 *  - Entra ID tenant (tenant_id + tenant_domain + cloud_instance + derived authority_url)
 *  - App registration (client_id + client_secret_kv_ref via <ApiKeyInput> + redirect URIs + scopes + audience)
 *  - MSAL & session (token cache + TTL + refresh + CSRF + cookie preview read-only)
 *  - Role mapping (3 active EKP roles + Power User Tier 2 disabled affordance per ADR-0027 fallback)
 *  - Sign-in policy (allowed domains + MFA toggle + auto-disable days)
 *
 * Wave C1 is **read-mostly**: PATCH endpoints exist but the UI ships display-only
 * with the structural primitives in place for Wave C2 promotion to inline edit.
 */

import { Loader2, ShieldCheck } from 'lucide-react';
import { useEffect, useState } from 'react';

import { ApiKeyInput } from '@/components/ui/api-key-input';
import { DisabledAffordance } from '@/components/ui/disabled-affordance';
import { adminApi, type IdentityConfig } from '@/lib/api/admin';

export function SettingsIdentity() {
  const [config, setConfig] = useState<IdentityConfig | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    void adminApi
      .getIdentity()
      .then((c) => {
        if (!cancelled) setConfig(c);
      })
      .catch((err) => {
        if (!cancelled) setError(err.message ?? 'Failed to load identity config');
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (error) {
    return (
      <div className="banner banner-destructive">
        Failed to load identity config: <span className="mono">{error}</span>
      </div>
    );
  }
  if (!config) {
    return (
      <div
        className="banner banner-info"
        style={{ display: 'flex', alignItems: 'center', gap: 8 }}
      >
        <Loader2 size={14} className="animate-spin" aria-hidden="true" />
        Loading identity configuration…
      </div>
    );
  }

  return (
    <div className="col" style={{ gap: 14 }}>
      <div className="banner banner-info">
        <ShieldCheck size={14} aria-hidden="true" />
        <div style={{ flex: 1, lineHeight: 1.55 }}>
          <div style={{ fontSize: 13, fontWeight: 500 }}>
            Entra ID + MSAL configuration
          </div>
          <div className="text-xs muted">
            Hybrid auth per ADR-0014: Entra ID SSO + self-register fallback.
            Transport: httpOnly cookie + CSRF double-submit + /auth/refresh
            rotation per ADR-0022. Wave C1 ships read-mostly — inline edit
            promotes via Wave C2.
          </div>
        </div>
      </div>

      {/* Tenant */}
      <div className="card">
        <div className="card-header">
          <h3 className="card-title">Entra ID tenant</h3>
          <span className="badge badge-success">
            <span className="badge-dot" /> CONFIGURED
          </span>
        </div>
        <div
          className="card-body"
          style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}
        >
          <div className="field" style={{ marginBottom: 0 }}>
            <label className="label">Tenant ID</label>
            <input
              className="input mono"
              readOnly
              value={config.tenant.tenant_id}
              style={{ fontSize: 12 }}
            />
            <div className="hint">Ricoh corporate Entra tenant</div>
          </div>
          <div className="field" style={{ marginBottom: 0 }}>
            <label className="label">Tenant domain</label>
            <input
              className="input mono"
              readOnly
              value={config.tenant.tenant_domain}
              style={{ fontSize: 12 }}
            />
          </div>
          <div className="field" style={{ marginBottom: 0 }}>
            <label className="label">Authority URL</label>
            <input
              className="input mono"
              readOnly
              disabled
              value={config.tenant.authority_url ?? ''}
              style={{ fontSize: 12 }}
            />
            <div className="hint">Derived from tenant + cloud instance</div>
          </div>
          <div className="field" style={{ marginBottom: 0 }}>
            <label className="label">Cloud instance</label>
            <select
              className="select"
              value={config.tenant.cloud_instance}
              disabled
            >
              <option value="azure_public">Azure Public Cloud</option>
              <option value="azure_government">Azure Government</option>
              <option value="azure_china_21vianet">
                Azure China 21Vianet
              </option>
            </select>
          </div>
        </div>
      </div>

      {/* App registration */}
      <div className="card">
        <div className="card-header">
          <div>
            <h3 className="card-title">App registration</h3>
            <div className="card-desc">
              <span className="mono">{config.app_registration.client_id}</span>
              {' · enterprise application in Entra ID'}
            </div>
          </div>
        </div>
        <div className="card-body">
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr',
              gap: 12,
              marginBottom: 12,
            }}
          >
            <div className="field" style={{ marginBottom: 0 }}>
              <label className="label">Application (client) ID</label>
              <input
                className="input mono"
                readOnly
                value={config.app_registration.client_id}
                style={{ fontSize: 12 }}
              />
            </div>
            <div className="field" style={{ marginBottom: 0 }}>
              <label className="label">Client secret</label>
              <ApiKeyInput
                value={config.app_registration.client_secret_masked_preview}
                rotateDisabled
                rotateDisabledReason="Wave C2 — rotation requires Entra Graph SDK"
                ariaLabel="Entra app client secret"
              />
              <div className="hint">
                {config.app_registration.client_secret_kv_ref
                  ? `Stored in Key Vault as ${config.app_registration.client_secret_kv_ref}`
                  : 'Not provisioned'}
              </div>
            </div>
          </div>
          <div className="field" style={{ marginBottom: 12 }}>
            <label className="label">Redirect URIs (web)</label>
            <div className="col" style={{ gap: 4 }}>
              {config.app_registration.redirect_uris.map((u) => (
                <input
                  key={u}
                  className="input mono"
                  readOnly
                  value={u}
                  style={{ fontSize: 11.5, height: 28 }}
                />
              ))}
            </div>
          </div>
          <div
            style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}
          >
            <div className="field" style={{ marginBottom: 0 }}>
              <label className="label">API permissions (scopes)</label>
              <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                {config.app_registration.scopes.map((s) => (
                  <span key={s} className="badge badge-muted">
                    {s}
                  </span>
                ))}
              </div>
            </div>
            <div className="field" style={{ marginBottom: 0 }}>
              <label className="label">Sign-in audience</label>
              <select
                className="select"
                value={config.app_registration.sign_in_audience}
                disabled
              >
                <option value="single">
                  Single tenant (this Entra org only)
                </option>
                <option value="multi_disabled" disabled>
                  Multi-tenant (Tier 2)
                </option>
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* MSAL */}
      <div className="card">
        <div className="card-header">
          <h3 className="card-title">MSAL &amp; session</h3>
          <div className="card-desc">httpOnly cookie + CSRF · per ADR-0022</div>
        </div>
        <div
          className="card-body"
          style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}
        >
          <div className="field" style={{ marginBottom: 0 }}>
            <label className="label">Token cache strategy</label>
            <select
              className="select"
              value={config.msal.token_cache_strategy}
              disabled
            >
              <option value="memory">In-memory (per-replica)</option>
              <option value="distributed_disabled" disabled>
                Distributed (Redis · Tier 2)
              </option>
            </select>
          </div>
          <div className="field" style={{ marginBottom: 0 }}>
            <label className="label">Session TTL</label>
            <input
              className="input mono"
              readOnly
              value={config.msal.session_ttl}
              style={{ fontSize: 12 }}
            />
          </div>
          <div className="field" style={{ marginBottom: 0 }}>
            <label className="label">Refresh token rotation</label>
            <input
              className="input mono"
              readOnly
              value={config.msal.refresh_token_rotation}
              style={{ fontSize: 12 }}
            />
          </div>
          <div className="field" style={{ marginBottom: 0 }}>
            <label className="label">CSRF token rotation</label>
            <input
              className="input mono"
              readOnly
              value={config.msal.csrf_token_rotation}
              style={{ fontSize: 12 }}
            />
          </div>
          <div
            className="field"
            style={{ gridColumn: '1 / -1', marginBottom: 0 }}
          >
            <label className="label">Cookie settings</label>
            <div
              style={{
                padding: '8px 10px',
                background: 'oklch(var(--muted) / 0.4)',
                borderRadius: 'var(--radius-sm)',
                fontFamily: 'var(--font-mono)',
                fontSize: 11.5,
                color: 'oklch(var(--foreground) / 0.85)',
                lineHeight: 1.6,
              }}
            >
              {config.msal.cookie_settings_preview}
            </div>
          </div>
        </div>
      </div>

      {/* Role mapping */}
      <div className="card">
        <div className="card-header">
          <div>
            <h3 className="card-title">Role mapping</h3>
            <div className="card-desc">
              Map Entra security groups → EKP roles · Tier 1 has 3 active roles
              · Power User is Tier 2 (ADR-0027 fallback)
            </div>
          </div>
        </div>
        <div className="card-body card-body-tight">
          <table className="table">
            <thead>
              <tr>
                <th>EKP role</th>
                <th>Entra group</th>
                <th>Group ID</th>
                <th className="col-num">Members</th>
              </tr>
            </thead>
            <tbody>
              {config.roles.mappings.map((m) => (
                <tr key={m.ekp_role} style={m.is_tier2_disabled ? { opacity: 0.5 } : {}}>
                  <td>
                    <span
                      className={
                        m.is_tier2_disabled
                          ? 'badge badge-muted'
                          : m.ekp_role === 'workspace_admin'
                            ? 'badge badge-accent'
                            : m.ekp_role === 'knowledge_editor'
                              ? 'badge badge-info'
                              : 'badge badge-muted'
                      }
                    >
                      {m.ekp_role.replace('_', ' ')}
                    </span>
                    {m.is_tier2_disabled ? (
                      <span
                        className="badge badge-muted"
                        style={{ marginLeft: 4 }}
                      >
                        Tier 2
                      </span>
                    ) : null}
                  </td>
                  <td>
                    <span className="mono text-xs">
                      {m.entra_group_name || '—'}
                    </span>
                  </td>
                  <td>
                    <span className="mono text-xs muted">
                      {m.entra_group_id || '—'}
                    </span>
                  </td>
                  <td className="col-num">
                    {m.member_count ?? '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Sign-in policy */}
      <div className="card">
        <div className="card-header">
          <h3 className="card-title">Sign-in policy</h3>
        </div>
        <div className="card-body">
          <div className="field">
            <label className="label">
              Allowed email domains for self-register
            </label>
            <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
              {config.policy.allowed_email_domains.map((d) => (
                <span key={d} className="badge badge-accent">
                  {d}
                </span>
              ))}
            </div>
            <div className="hint">
              Self-register requires matching email domain · email
              verification mandatory
            </div>
          </div>
          <div className="row" style={{ marginBottom: 10 }}>
            <span
              className="switch"
              data-on={config.policy.require_mfa_workspace_admin}
            />
            <span className="text-xs" style={{ flex: 1 }}>
              Require MFA for Workspace Admin role
            </span>
          </div>
          <DisabledAffordance
            variant="p1-strict"
            reason="Wave D+ — full-tenant MFA enforcement is Tier 2 scope"
            tier2Trigger="Tier 2 — post-Beta governance"
          >
            <div className="row" style={{ marginBottom: 10 }}>
              <span className="switch" data-on={false} />
              <span className="text-xs" style={{ flex: 1 }}>
                Require MFA for all roles (Tier 2)
              </span>
            </div>
          </DisabledAffordance>
          <div className="row">
            <span className="switch" data-on={config.policy.auto_disable_after_days > 0} />
            <span className="text-xs" style={{ flex: 1 }}>
              Auto-disable accounts after{' '}
              <span className="mono">
                {config.policy.auto_disable_after_days}d
              </span>{' '}
              inactivity
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
