/**
 * Admin API client (W24-wave-c1 F5/F6 per ADR-0026 Option B).
 *
 * Wraps the F2 (`/admin/connections/*`) + F3 (`/admin/identity/*`) + F4
 * (`/admin/api-keys/*` + `/admin/usage-stats` + `/admin/audit-log`) endpoint
 * groups that surface the `/settings` 6-tab `PageSettingsRich` view per
 * mockup `ekp-page-settings-tabs.jsx`.
 *
 * **Security hygiene mirror per backend Pydantic models**:
 *  - F2 `ProviderConfig.secret_kv_ref` + `secret_masked_preview` — never the
 *    real secret value
 *  - F3 `AppRegistrationConfig.client_secret_kv_ref` + masked preview
 *  - F4 rotate-secret returns `{provider_id, last_rotated_at, masked}` only
 */

import { ApiClient } from '../api-client';

const client = new ApiClient();

// ---------- F2 — /admin/connections/* shared types ---------------------------

export type ProviderCategory =
  | 'llm'
  | 'retrieval'
  | 'storage'
  | 'observability'
  | 'identity';

export type TestStatus = 'ok' | 'degraded' | 'error' | 'not_tested';

export interface ProviderDeployment {
  deployment_id: string;
  deployment_name: string;
  model_family: string;
  tpm_limit: number | null;
  rpm_limit: number | null;
  alert_threshold_pct: number;
}

export interface ProviderConfig {
  provider_id: string;
  category: ProviderCategory;
  display_name: string;
  endpoint_url: string | null;
  region: string | null;
  deployments: ProviderDeployment[];
  secret_kv_ref: string | null;
  secret_masked_preview: string | null;
  last_test_at: string | null;
  last_test_status: TestStatus;
  last_test_detail: string | null;
  last_rotated_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface ProviderSummary {
  provider_id: string;
  category: ProviderCategory;
  display_name: string;
  last_test_at: string | null;
  last_test_status: TestStatus;
}

export interface ProviderPatch {
  endpoint_url?: string | null;
  region?: string | null;
  display_name?: string | null;
}

export interface TestConnectionResult {
  status: TestStatus;
  latency_ms: number | null;
  detail: string | null;
}

export interface RotateSecretResult {
  provider_id: string;
  last_rotated_at: string;
  secret_masked_preview: string;
}

// ---------- F3 — /admin/identity/* shared types ------------------------------

export type EkpRoleKey = 'admin' | 'editor' | 'user' | 'power';

/**
 * Display labels for the RBAC roles — mockup `ekp-page-users.jsx` ROLES +
 * `ekp-page-settings-tabs.jsx` lines 664-685 (W24c F3 vocabulary unification:
 * long-form `workspace_admin` etc. retired in favour of the RBAC-core short keys).
 */
export const EKP_ROLE_LABELS: Record<EkpRoleKey, string> = {
  admin: 'Workspace Admin',
  editor: 'Knowledge Editor',
  user: 'End User',
  power: 'Power User',
};

export type CloudInstance =
  | 'azure_public'
  | 'azure_government'
  | 'azure_china_21vianet';

export type SignInAudience = 'single' | 'multi_disabled';
export type TokenCacheStrategy = 'memory' | 'distributed_disabled';

export interface EntraTenantConfig {
  tenant_id: string;
  tenant_domain: string;
  cloud_instance: CloudInstance;
  authority_url: string | null; // derived server-side; null on PATCH
}

export interface AppRegistrationConfig {
  client_id: string;
  client_secret_kv_ref: string | null;
  client_secret_masked_preview: string | null;
  client_secret_expires_at: string | null;
  redirect_uris: string[];
  scopes: string[];
  sign_in_audience: SignInAudience;
}

export interface MsalConfig {
  token_cache_strategy: TokenCacheStrategy;
  session_ttl: string;
  refresh_token_rotation: string;
  csrf_token_rotation: string;
  cookie_settings_preview: string;
}

export interface RoleMapping {
  ekp_role: EkpRoleKey;
  entra_group_name: string;
  entra_group_id: string;
  member_count: number | null;
  is_tier2_disabled: boolean;
  tier2_reason: string | null;
}

export interface RoleMappingConfig {
  mappings: RoleMapping[];
}

export interface SignInPolicyConfig {
  allowed_email_domains: string[];
  require_mfa_workspace_admin: boolean;
  require_mfa_all_roles_tier2: false; // Literal[False] — Tier 2 boundary
  auto_disable_after_days: number;
}

export interface IdentityConfig {
  tenant: EntraTenantConfig;
  app_registration: AppRegistrationConfig;
  msal: MsalConfig;
  roles: RoleMappingConfig;
  policy: SignInPolicyConfig;
  updated_at: string;
}

// ---------- F4 — usage stats + api keys --------------------------------------

export type RealtimeStatus =
  | 'ok'
  | 'no_client'
  | 'sdk_method_missing'
  | 'fetch_failed';

export interface UsageStats4Stat {
  api_calls_24h: number;
  api_calls_delta_pct: number | null;
  spend_today_usd: number;
  spend_cap_daily_usd: number;
  spend_pct_used: number;
  token_throughput_tpm: number;
  token_throughput_p95_in_cap: boolean;
  rate_limit_hits_24h: number;
  realtime_status: RealtimeStatus;
}

export type QuotaStatus = 'within_limits' | 'warning' | 'over_limit';

export interface OutgoingQuotaRow {
  provider_id: string;
  deployment_id: string;
  display_name: string;
  used_tpm: number;
  cap_tpm: number | null;
  used_rpm: number;
  cap_rpm: number | null;
  alert_threshold_pct: number;
  quota_unit: 'tokens' | 'emails';
  status: QuotaStatus;
}

export interface OutgoingQuotaList {
  rows: OutgoingQuotaRow[];
  realtime_status: RealtimeStatus;
}

export interface IncomingKeysDisabled {
  enabled: false;
  reason: string;
  tier2_trigger: string;
}

export type AuditAction =
  | 'connection_patch'
  | 'connection_test'
  | 'connection_rotate_secret'
  | 'identity_patch'
  | 'api_keys_alert_threshold_patch';

export interface AuditLogEntry {
  id: number | null;
  actor: string | null;
  action: AuditAction;
  resource: string;
  payload: Record<string, unknown> | null;
  created_at: string;
}

export interface AuditLogPage {
  entries: AuditLogEntry[];
  next_cursor: number | null;
}

export interface AuditLogQuery {
  limit?: number;
  action_type?: AuditAction;
  /** ISO date (YYYY-MM-DD) or datetime — entries on/after this instant. */
  since?: string;
  /** `id` of the oldest row already shown — fetches the next older page. */
  cursor?: number;
}

// ---------- ApiClient surface ------------------------------------------------

export const adminApi = {
  // F2 — connections
  listConnections: (): Promise<ProviderSummary[]> =>
    client.get('/admin/connections'),
  getConnection: (providerId: string): Promise<ProviderConfig> =>
    client.get(`/admin/connections/${providerId}`),
  updateConnection: (
    providerId: string,
    patch: ProviderPatch,
  ): Promise<ProviderConfig> => client.patch(`/admin/connections/${providerId}`, patch),
  testConnection: (providerId: string): Promise<TestConnectionResult> =>
    client.post(`/admin/connections/${providerId}/test`, {}),
  rotateSecret: (providerId: string): Promise<RotateSecretResult> =>
    client.post(`/admin/connections/${providerId}/rotate-secret`, {}),

  // F3 — identity
  getIdentity: (): Promise<IdentityConfig> => client.get('/admin/identity'),
  patchTenant: (value: EntraTenantConfig): Promise<EntraTenantConfig> =>
    client.patch('/admin/identity/tenant', value),
  patchAppRegistration: (
    value: AppRegistrationConfig,
  ): Promise<AppRegistrationConfig> =>
    client.patch('/admin/identity/app_registration', value),
  patchMsal: (value: MsalConfig): Promise<MsalConfig> =>
    client.patch('/admin/identity/msal', value),
  patchRoles: (value: RoleMappingConfig): Promise<RoleMappingConfig> =>
    client.patch('/admin/identity/roles', value),
  patchPolicy: (value: SignInPolicyConfig): Promise<SignInPolicyConfig> =>
    client.patch('/admin/identity/policy', value),

  // F4 — usage + api-keys + audit-log
  getUsageStats: (): Promise<UsageStats4Stat> => client.get('/admin/usage-stats'),
  getOutgoingQuotas: (): Promise<OutgoingQuotaList> =>
    client.get('/admin/api-keys/outgoing'),
  patchAlertThreshold: (
    providerId: string,
    deploymentId: string,
    alertThresholdPct: number,
  ): Promise<OutgoingQuotaRow> =>
    client.patch(
      `/admin/api-keys/outgoing/${providerId}/${deploymentId}/alert-threshold`,
      { alert_threshold_pct: alertThresholdPct },
    ),
  getIncomingKeys: (): Promise<IncomingKeysDisabled> =>
    client.get('/admin/api-keys/incoming'),
  listAuditLog: (opts: AuditLogQuery = {}): Promise<AuditLogPage> => {
    const params = new URLSearchParams();
    params.set('limit', String(opts.limit ?? 10));
    if (opts.action_type) params.set('action_type', opts.action_type);
    if (opts.since) params.set('since', opts.since);
    if (opts.cursor != null) params.set('cursor', String(opts.cursor));
    return client.get(`/admin/audit-log?${params.toString()}`);
  },
};
