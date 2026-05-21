'use client';

/**
 * `<SettingsIdentity>` tab (W24-wave-c1 F5 per ADR-0026 + mockup line
 * 528-723 SettingsIdentity decomposition).
 *
 * 5 cards mapped 1:1 onto F3 backend sub-resources:
 *  - Entra ID tenant (tenant_id + tenant_domain + cloud_instance + derived authority_url)
 *  - App registration (client_id + client_secret via <ApiKeyInput> + redirect URIs + scopes + audience)
 *  - MSAL & session (token cache + TTL + refresh + CSRF + cookie preview read-only)
 *  - Role mapping (3 active EKP roles + Power User Tier 2 disabled affordance per ADR-0027 fallback)
 *  - Sign-in policy (allowed domains + MFA toggle + auto-disable days)
 *
 * W24b-wave-c2 F5 — inline edit activation: 4 cards (Tenant / App registration /
 * MSAL / Sign-in policy) become editable forms — react-hook-form + zod
 * (`@/lib/schemas/admin/identity`) + a `useMutation` per card that PATCHes its
 * sub-resource and re-baselines the form on success. The Role mapping card
 * stays read-only display: the mockup edits roles via a per-row "⋯" menu +
 * "Add mapping" (individual CRUD), which plan F5.5 defers to Wave C+.
 *
 * Tier 2 boundary preserved: the multi-tenant / distributed-cache `<option>`s
 * stay disabled and the Power User role row stays disabled — the backend
 * rejects those values 422, and a 422 surfaces inline via the card's mutation
 * error.
 */

import { zodResolver } from '@hookform/resolvers/zod';
import { useMutation } from '@tanstack/react-query';
import { Loader2, Plus, ShieldCheck, X } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';

import { ApiKeyInput } from '@/components/ui/api-key-input';
import { DisabledAffordance } from '@/components/ui/disabled-affordance';
import {
  adminApi,
  EKP_ROLE_LABELS,
  type AppRegistrationConfig,
  type EntraTenantConfig,
  type IdentityConfig,
  type MsalConfig,
  type RoleMapping,
  type SignInPolicyConfig,
} from '@/lib/api/admin';
import {
  appRegistrationConfigSchema,
  entraTenantConfigSchema,
  msalConfigSchema,
  signInPolicyConfigSchema,
  type AppRegistrationInput,
  type EntraTenantInput,
  type MsalInput,
  type SignInPolicyInput,
} from '@/lib/schemas/admin/identity';

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
            rotation per ADR-0022. Changes are audit-logged.
          </div>
        </div>
      </div>

      <TenantCard initial={config.tenant} />
      <AppRegistrationCard initial={config.app_registration} />
      <MsalCard initial={config.msal} />
      <RoleMappingCard mappings={config.roles.mappings} />
      <SignInPolicyCard initial={config.policy} />
    </div>
  );
}

// ============================================================================
// Shared bits
// ============================================================================

/** Inline destructive hint shown under an input that failed zod validation. */
function FieldError({ message }: { message?: string }) {
  if (!message) return null;
  return (
    <div className="hint" style={{ color: 'oklch(var(--destructive))' }}>
      {message}
    </div>
  );
}

/**
 * Card footer — Save button + mutation feedback. `type="submit"` triggers the
 * enclosing `<form className="card">`'s onSubmit.
 */
function CardSaveRow({
  isDirty,
  pending,
  error,
  justSaved,
}: {
  isDirty: boolean;
  pending: boolean;
  error: Error | null;
  justSaved: boolean;
}) {
  return (
    <div
      style={{
        padding: '12px 18px',
        borderTop: '1px solid oklch(var(--border))',
        display: 'flex',
        alignItems: 'center',
        gap: 8,
      }}
    >
      <button
        type="submit"
        className="btn btn-secondary btn-sm"
        disabled={!isDirty || pending}
      >
        {pending ? (
          <Loader2 size={12} className="animate-spin" aria-hidden="true" />
        ) : null}{' '}
        Save changes
      </button>
      {error ? (
        <span
          className="text-xs"
          style={{ color: 'oklch(var(--destructive))' }}
        >
          {error.message}
        </span>
      ) : null}
      {justSaved && !isDirty ? (
        <span className="text-xs muted">Saved</span>
      ) : null}
    </div>
  );
}

// ============================================================================
// TenantCard
// ============================================================================

function TenantCard({ initial }: { initial: EntraTenantConfig }) {
  const {
    register,
    handleSubmit,
    reset,
    watch,
    formState: { errors, isDirty },
  } = useForm<EntraTenantInput>({
    resolver: zodResolver(entraTenantConfigSchema),
    defaultValues: initial,
  });

  const mutation = useMutation({
    mutationFn: (data: EntraTenantInput) =>
      // authority_url is server-derived — send null, the backend re-derives it.
      adminApi.patchTenant({
        tenant_id: data.tenant_id,
        tenant_domain: data.tenant_domain,
        cloud_instance: data.cloud_instance,
        authority_url: null,
      }),
    onSuccess: (saved) => reset(saved),
  });

  const onSubmit = handleSubmit((data) => mutation.mutate(data));

  return (
    <form className="card" onSubmit={onSubmit}>
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
          <label className="label" htmlFor="tenant-id">
            Tenant ID
          </label>
          <input
            id="tenant-id"
            className="input mono"
            style={{ fontSize: 12 }}
            aria-invalid={errors.tenant_id ? 'true' : undefined}
            {...register('tenant_id')}
          />
          {errors.tenant_id ? (
            <FieldError message={errors.tenant_id.message} />
          ) : (
            <div className="hint">Ricoh corporate Entra tenant</div>
          )}
        </div>
        <div className="field" style={{ marginBottom: 0 }}>
          <label className="label" htmlFor="tenant-domain">
            Tenant domain
          </label>
          <input
            id="tenant-domain"
            className="input mono"
            style={{ fontSize: 12 }}
            aria-invalid={errors.tenant_domain ? 'true' : undefined}
            {...register('tenant_domain')}
          />
          <FieldError message={errors.tenant_domain?.message} />
        </div>
        <div className="field" style={{ marginBottom: 0 }}>
          <label className="label" htmlFor="tenant-authority">
            Authority URL
          </label>
          <input
            id="tenant-authority"
            className="input mono"
            style={{ fontSize: 12 }}
            readOnly
            disabled
            value={watch('authority_url') ?? ''}
          />
          <div className="hint">Derived from tenant + cloud instance</div>
        </div>
        <div className="field" style={{ marginBottom: 0 }}>
          <label className="label" htmlFor="tenant-cloud">
            Cloud instance
          </label>
          <select
            id="tenant-cloud"
            className="select"
            {...register('cloud_instance')}
          >
            <option value="azure_public">Azure Public Cloud</option>
            <option value="azure_government">Azure Government</option>
            <option value="azure_china_21vianet">Azure China 21Vianet</option>
          </select>
        </div>
      </div>
      <CardSaveRow
        isDirty={isDirty}
        pending={mutation.isPending}
        error={mutation.isError ? mutation.error : null}
        justSaved={mutation.isSuccess}
      />
    </form>
  );
}

// ============================================================================
// AppRegistrationCard
// ============================================================================

function AppRegistrationCard({
  initial,
}: {
  initial: AppRegistrationConfig;
}) {
  const {
    register,
    handleSubmit,
    reset,
    watch,
    setValue,
    formState: { errors, isDirty },
  } = useForm<AppRegistrationInput>({
    resolver: zodResolver(appRegistrationConfigSchema),
    defaultValues: initial,
  });

  const mutation = useMutation({
    mutationFn: (data: AppRegistrationInput) =>
      adminApi.patchAppRegistration({
        client_id: data.client_id,
        // Secret fields + scopes are not edited here — pass the loaded values
        // through. Secret rotation is Wave C2 (needs the Entra Graph SDK).
        client_secret_kv_ref: initial.client_secret_kv_ref,
        client_secret_masked_preview: initial.client_secret_masked_preview,
        client_secret_expires_at: initial.client_secret_expires_at,
        redirect_uris: data.redirect_uris ?? [],
        scopes: initial.scopes,
        sign_in_audience: data.sign_in_audience,
      }),
    onSuccess: (saved) => reset(saved),
  });

  const onSubmit = handleSubmit((data) => mutation.mutate(data));
  const uris = watch('redirect_uris') ?? [];

  return (
    <form className="card" onSubmit={onSubmit}>
      <div className="card-header">
        <div>
          <h3 className="card-title">App registration</h3>
          <div className="card-desc">
            <span className="mono">{initial.client_id}</span>
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
            <label className="label" htmlFor="app-client-id">
              Application (client) ID
            </label>
            <input
              id="app-client-id"
              className="input mono"
              style={{ fontSize: 12 }}
              aria-invalid={errors.client_id ? 'true' : undefined}
              {...register('client_id')}
            />
            <FieldError message={errors.client_id?.message} />
          </div>
          <div className="field" style={{ marginBottom: 0 }}>
            <label className="label">Client secret</label>
            <ApiKeyInput
              value={initial.client_secret_masked_preview}
              rotateDisabled
              rotateDisabledReason="Wave C2 — rotation requires Entra Graph SDK"
              ariaLabel="Entra app client secret"
            />
            <div className="hint">
              {initial.client_secret_kv_ref
                ? `Stored in Key Vault as ${initial.client_secret_kv_ref}`
                : 'Not provisioned'}
            </div>
          </div>
        </div>

        {/* Redirect URIs — editable list. */}
        <div className="field" style={{ marginBottom: 12 }}>
          <label className="label">Redirect URIs (web)</label>
          <div className="col" style={{ gap: 4 }}>
            {uris.map((_, i) => (
              <div
                key={i}
                style={{ display: 'flex', alignItems: 'center', gap: 6 }}
              >
                <input
                  className="input mono"
                  style={{ fontSize: 11.5, height: 28 }}
                  aria-label={`Redirect URI ${i + 1}`}
                  aria-invalid={errors.redirect_uris?.[i] ? 'true' : undefined}
                  {...register(`redirect_uris.${i}`)}
                />
                <button
                  type="button"
                  className="btn btn-ghost btn-icon btn-xs"
                  aria-label={`Remove redirect URI ${i + 1}`}
                  onClick={() =>
                    setValue(
                      'redirect_uris',
                      uris.filter((__, idx) => idx !== i),
                      { shouldDirty: true },
                    )
                  }
                >
                  <X size={11} aria-hidden="true" />
                </button>
              </div>
            ))}
            <button
              type="button"
              className="btn btn-ghost btn-xs"
              style={{ width: 'fit-content' }}
              onClick={() =>
                setValue('redirect_uris', [...uris, ''], { shouldDirty: true })
              }
            >
              <Plus size={11} aria-hidden="true" /> Add redirect URI
            </button>
          </div>
          <FieldError
            message={
              Array.isArray(errors.redirect_uris)
                ? undefined
                : errors.redirect_uris?.message
            }
          />
        </div>

        <div
          style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}
        >
          <div className="field" style={{ marginBottom: 0 }}>
            <label className="label">API permissions (scopes)</label>
            <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
              {initial.scopes.map((s) => (
                <span key={s} className="badge badge-muted">
                  {s}
                </span>
              ))}
            </div>
          </div>
          <div className="field" style={{ marginBottom: 0 }}>
            <label className="label" htmlFor="app-audience">
              Sign-in audience
            </label>
            <select
              id="app-audience"
              className="select"
              {...register('sign_in_audience')}
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
      <CardSaveRow
        isDirty={isDirty}
        pending={mutation.isPending}
        error={mutation.isError ? mutation.error : null}
        justSaved={mutation.isSuccess}
      />
    </form>
  );
}

// ============================================================================
// MsalCard
// ============================================================================

function MsalCard({ initial }: { initial: MsalConfig }) {
  const {
    register,
    handleSubmit,
    reset,
    watch,
    formState: { errors, isDirty },
  } = useForm<MsalInput>({
    resolver: zodResolver(msalConfigSchema),
    defaultValues: initial,
  });

  const mutation = useMutation({
    mutationFn: (data: MsalInput) =>
      adminApi.patchMsal({
        token_cache_strategy: data.token_cache_strategy,
        session_ttl: data.session_ttl,
        refresh_token_rotation: data.refresh_token_rotation,
        csrf_token_rotation: data.csrf_token_rotation,
        // Server-computed read-only preview — pass the loaded value through.
        cookie_settings_preview: initial.cookie_settings_preview,
      }),
    onSuccess: (saved) => reset(saved),
  });

  const onSubmit = handleSubmit((data) => mutation.mutate(data));

  return (
    <form className="card" onSubmit={onSubmit}>
      <div className="card-header">
        <h3 className="card-title">MSAL &amp; session</h3>
        <div className="card-desc">httpOnly cookie + CSRF · per ADR-0022</div>
      </div>
      <div
        className="card-body"
        style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}
      >
        <div className="field" style={{ marginBottom: 0 }}>
          <label className="label" htmlFor="msal-cache">
            Token cache strategy
          </label>
          <select
            id="msal-cache"
            className="select"
            {...register('token_cache_strategy')}
          >
            <option value="memory">In-memory (per-replica)</option>
            <option value="distributed_disabled" disabled>
              Distributed (Redis · Tier 2)
            </option>
          </select>
        </div>
        <div className="field" style={{ marginBottom: 0 }}>
          <label className="label" htmlFor="msal-ttl">
            Session TTL
          </label>
          <input
            id="msal-ttl"
            className="input mono"
            style={{ fontSize: 12 }}
            aria-invalid={errors.session_ttl ? 'true' : undefined}
            {...register('session_ttl')}
          />
          <FieldError message={errors.session_ttl?.message} />
        </div>
        <div className="field" style={{ marginBottom: 0 }}>
          <label className="label" htmlFor="msal-refresh">
            Refresh token rotation
          </label>
          <input
            id="msal-refresh"
            className="input mono"
            style={{ fontSize: 12 }}
            aria-invalid={errors.refresh_token_rotation ? 'true' : undefined}
            {...register('refresh_token_rotation')}
          />
          <FieldError message={errors.refresh_token_rotation?.message} />
        </div>
        <div className="field" style={{ marginBottom: 0 }}>
          <label className="label" htmlFor="msal-csrf">
            CSRF token rotation
          </label>
          <input
            id="msal-csrf"
            className="input mono"
            style={{ fontSize: 12 }}
            aria-invalid={errors.csrf_token_rotation ? 'true' : undefined}
            {...register('csrf_token_rotation')}
          />
          <FieldError message={errors.csrf_token_rotation?.message} />
        </div>
        <div className="field" style={{ gridColumn: '1 / -1', marginBottom: 0 }}>
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
            {watch('cookie_settings_preview')}
          </div>
        </div>
      </div>
      <CardSaveRow
        isDirty={isDirty}
        pending={mutation.isPending}
        error={mutation.isError ? mutation.error : null}
        justSaved={mutation.isSuccess}
      />
    </form>
  );
}

// ============================================================================
// RoleMappingCard — read-only display (individual mapping CRUD = Wave C+)
// ============================================================================

function RoleMappingCard({ mappings }: { mappings: RoleMapping[] }) {
  return (
    <div className="card">
      <div className="card-header">
        <div>
          <h3 className="card-title">Role mapping</h3>
          <div className="card-desc">
            Map Entra security groups → EKP roles · Tier 1 has 3 active roles ·
            Power User is Tier 2 (ADR-0027 fallback) · editing roles is Wave C+
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
            {mappings.map((m) => (
              <tr
                key={m.ekp_role}
                style={m.is_tier2_disabled ? { opacity: 0.5 } : {}}
              >
                <td>
                  <span
                    className={
                      m.is_tier2_disabled
                        ? 'badge badge-muted'
                        : m.ekp_role === 'admin'
                          ? 'badge badge-accent'
                          : m.ekp_role === 'editor'
                            ? 'badge badge-info'
                            : 'badge badge-muted'
                    }
                  >
                    {EKP_ROLE_LABELS[m.ekp_role]}
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
                <td className="col-num">{m.member_count ?? '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ============================================================================
// SignInPolicyCard
// ============================================================================

function SignInPolicyCard({ initial }: { initial: SignInPolicyConfig }) {
  const {
    register,
    handleSubmit,
    reset,
    watch,
    setValue,
    formState: { errors, isDirty },
  } = useForm<SignInPolicyInput>({
    resolver: zodResolver(signInPolicyConfigSchema),
    defaultValues: initial,
  });

  const mutation = useMutation({
    mutationFn: (data: SignInPolicyInput) =>
      adminApi.patchPolicy({
        allowed_email_domains: data.allowed_email_domains ?? [],
        require_mfa_workspace_admin: data.require_mfa_workspace_admin,
        // Permanent Tier 2 boundary — backend models this Literal[False].
        require_mfa_all_roles_tier2: false,
        auto_disable_after_days: data.auto_disable_after_days,
      }),
    onSuccess: (saved) => reset(saved),
  });

  const onSubmit = handleSubmit((data) => mutation.mutate(data));
  const domains = watch('allowed_email_domains') ?? [];
  const mfaAdmin = watch('require_mfa_workspace_admin');
  const autoDisableDays = watch('auto_disable_after_days');

  return (
    <form className="card" onSubmit={onSubmit}>
      <div className="card-header">
        <h3 className="card-title">Sign-in policy</h3>
      </div>
      <div className="card-body">
        {/* Allowed email domains — editable list. */}
        <div className="field">
          <label className="label">
            Allowed email domains for self-register
          </label>
          <div className="col" style={{ gap: 4 }}>
            {domains.map((_, i) => (
              <div
                key={i}
                style={{ display: 'flex', alignItems: 'center', gap: 6 }}
              >
                <input
                  className="input mono"
                  style={{ fontSize: 11.5, height: 28, maxWidth: 280 }}
                  aria-label={`Allowed domain ${i + 1}`}
                  aria-invalid={
                    errors.allowed_email_domains?.[i] ? 'true' : undefined
                  }
                  {...register(`allowed_email_domains.${i}`)}
                />
                <button
                  type="button"
                  className="btn btn-ghost btn-icon btn-xs"
                  aria-label={`Remove domain ${i + 1}`}
                  onClick={() =>
                    setValue(
                      'allowed_email_domains',
                      domains.filter((__, idx) => idx !== i),
                      { shouldDirty: true },
                    )
                  }
                >
                  <X size={11} aria-hidden="true" />
                </button>
              </div>
            ))}
            <button
              type="button"
              className="btn btn-ghost btn-xs"
              style={{ width: 'fit-content' }}
              onClick={() =>
                setValue('allowed_email_domains', [...domains, ''], {
                  shouldDirty: true,
                })
              }
            >
              <Plus size={11} aria-hidden="true" /> Add domain
            </button>
          </div>
          <div className="hint">
            Self-register requires matching email domain · email verification
            mandatory
          </div>
        </div>

        <div className="row" style={{ marginBottom: 10 }}>
          <button
            type="button"
            className="switch"
            data-on={mfaAdmin}
            aria-pressed={mfaAdmin}
            aria-label="Require MFA for Workspace Admin role"
            onClick={() =>
              setValue('require_mfa_workspace_admin', !mfaAdmin, {
                shouldDirty: true,
              })
            }
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
          <button
            type="button"
            className="switch"
            data-on={autoDisableDays > 0}
            aria-pressed={autoDisableDays > 0}
            aria-label="Auto-disable inactive accounts"
            onClick={() =>
              setValue(
                'auto_disable_after_days',
                autoDisableDays > 0 ? 0 : 90,
                { shouldDirty: true },
              )
            }
          />
          <span
            className="text-xs"
            style={{ flex: 1, display: 'flex', alignItems: 'center', gap: 6 }}
          >
            Auto-disable accounts after
            <input
              type="number"
              className="input mono"
              min={0}
              style={{ width: 64, height: 26, fontSize: 12 }}
              aria-label="Auto-disable after days"
              aria-invalid={errors.auto_disable_after_days ? 'true' : undefined}
              {...register('auto_disable_after_days', { valueAsNumber: true })}
            />
            days of inactivity (0 = never)
          </span>
        </div>
        <FieldError message={errors.auto_disable_after_days?.message} />
      </div>
      <CardSaveRow
        isDirty={isDirty}
        pending={mutation.isPending}
        error={mutation.isError ? mutation.error : null}
        justSaved={mutation.isSuccess}
      />
    </form>
  );
}
