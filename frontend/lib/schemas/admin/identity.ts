/**
 * Zod schemas for the Identity & Auth settings tab (W24b-wave-c2 F2).
 *
 * Runtime mirror of backend `api/schemas/admin_identity.py` Pydantic models —
 * the form-validation layer the Wave C2 Identity inline-edit (F5) consumes via
 * `zodResolver`. Enum members + numeric bounds match the backend `Literal`s and
 * `Field()` constraints exactly so a payload that passes here also passes
 * server-side validation.
 *
 * The GUID / duration / domain regexes are intentionally stricter than the
 * backend (which types these as plain `str`) — that strictness is the point of
 * a form-validation layer: catch a malformed tenant GUID before the request,
 * not after MSAL auth silently breaks. A value that passes the regex is still a
 * `str`, so the wire contract with the backend is unchanged.
 */

import { z } from 'zod';

/** Entra tenant / app client GUID — RFC 4122 UUID. */
const guidSchema = z.string().uuid('Must be a valid GUID');

/** Pretty-printed duration the backend stores as a display string, e.g. '7d'. */
const durationSchema = z
  .string()
  .regex(/^\d+[smhd]$/i, "Use a duration like '7d', '24h', or '30m'");

export const cloudInstanceSchema = z.enum([
  'azure_public',
  'azure_government',
  'azure_china_21vianet',
]);

export const signInAudienceSchema = z.enum(['single', 'multi_disabled']);

export const tokenCacheStrategySchema = z.enum([
  'memory',
  'distributed_disabled',
]);

export const ekpRoleKeySchema = z.enum(['admin', 'editor', 'user', 'power']);

export const entraTenantConfigSchema = z.object({
  tenant_id: guidSchema,
  tenant_domain: z
    .string()
    .min(1, 'Tenant domain is required')
    .regex(/^[a-z0-9.-]+$/i, 'Domain may contain only letters, digits, dots, hyphens'),
  cloud_instance: cloudInstanceSchema,
  // Derived server-side from tenant_id + cloud_instance — ignored on PATCH.
  authority_url: z.string().nullable().optional(),
});

export const appRegistrationConfigSchema = z.object({
  client_id: guidSchema,
  client_secret_kv_ref: z.string().nullable().optional(),
  client_secret_masked_preview: z.string().nullable().optional(),
  client_secret_expires_at: z.string().nullable().optional(),
  redirect_uris: z.array(z.string().url('Each redirect URI must be a valid URL')),
  scopes: z.array(z.string().min(1)),
  sign_in_audience: signInAudienceSchema,
});

export const msalConfigSchema = z.object({
  token_cache_strategy: tokenCacheStrategySchema,
  session_ttl: durationSchema,
  refresh_token_rotation: durationSchema,
  csrf_token_rotation: durationSchema,
  // Server-computed read-only preview — not operator-editable.
  cookie_settings_preview: z.string(),
});

export const roleMappingSchema = z.object({
  ekp_role: ekpRoleKeySchema,
  // entra_group_name / entra_group_id may be empty for an unmapped row
  // (the Power User row ships unmapped + Tier 2 disabled).
  entra_group_name: z.string(),
  entra_group_id: z.string(),
  member_count: z.number().int().nullable().optional(),
  is_tier2_disabled: z.boolean(),
  tier2_reason: z.string().nullable().optional(),
});

/** PATCH /admin/identity/roles — full list-replace semantic per ADR-0026. */
export const roleMappingConfigSchema = z.object({
  mappings: z.array(roleMappingSchema),
});

export const signInPolicyConfigSchema = z.object({
  allowed_email_domains: z.array(
    z
      .string()
      .regex(/^@[a-z0-9.-]+$/i, "Domain must start with '@', e.g. '@ricoh.com'"),
  ),
  require_mfa_workspace_admin: z.boolean(),
  // Permanent Tier 2 boundary — backend models this as Literal[False].
  require_mfa_all_roles_tier2: z.literal(false),
  auto_disable_after_days: z
    .number()
    .int('Must be a whole number of days')
    .min(0, '0 = never auto-disable'),
});

// Inferred form-value types — `useForm<T>` generics for the F5 inline-edit
// cards. Consumed by `settings-identity.tsx`.
export type EntraTenantInput = z.infer<typeof entraTenantConfigSchema>;
export type AppRegistrationInput = z.infer<typeof appRegistrationConfigSchema>;
export type MsalInput = z.infer<typeof msalConfigSchema>;
export type SignInPolicyInput = z.infer<typeof signInPolicyConfigSchema>;
