---
phase: W24-frontend-wave-c1
plan_ref: ./plan.md
status: active                      # active | closed
last_updated: 2026-05-19  # F3 active-flip → F3.1-F3.11 complete
---

# W24-wave-c1 — Checklist

> Derived from `plan.md §2 F0-F8 deliverables`。延後項標 🚧 + reason(per CLAUDE.md sacred rule — 唔可以刪未勾 `[ ]`)。

## F0 — Kickoff cascade

- [x] **F0.1** W24 `plan.md`(this folder)+ `checklist.md` + `progress.md` created `status: active` 2026-05-19
- [x] **F0.2** NO `frontend/` or `backend/` code change at kickoff(per W19-W23 F0 precedent — F0 governance only)
- [x] **F0.3** `architecture.md v6 §5.0` Settings paragraph inline-tagged amendment landed at kickoff(thin v1 → 6-tab hub per ADR-0026 Option B + ADR-0024 / §3.4 / §3.7 precedent;doc version held)
- [x] **F0.4** Pre-active-flip 5-step grep audit recursive(per R6):W22-W23 plan-text contamination check + `frontend/app/(app)/settings/page.tsx` current state confirmed thin v1(104 lines)+ `backend/api/routes/` confirmed 14 routes no `/admin` group + `references/design-mockups/ekp-page-settings-tabs.jsx` 882 lines structure confirmed
- [x] **F0.5** W24 kickoff cascade committed `(this commit)`

## F1 — KeyVaultProvider abstraction + Azure SDK install(Plan B (c) mobile hotspot)

- [x] **F1.1** `backend/storage/key_vault.py` NEW — `KeyVaultProvider` Protocol(`get_secret` + `set_secret` + `delete_secret` + `list_secrets` + `rotate_secret`)+ `SecretMetadata` Pydantic + `SecretNotFoundError` + `generate_secret_value` 32-byte urlsafe entropy helper
- [x] **F1.2** `EnvVarProvider` impl in `key_vault.py` — `os.environ`-backed fallback when `KEY_VAULT_URL` unset;`rotate_secret` raises `NotImplementedError` with actionable error message
- [x] **F1.3** `backend/storage/azure_key_vault.py` NEW — `AzureKeyVaultProvider` production path using `azure.keyvault.secrets.aio.SecretClient` + `azure.identity.aio.DefaultAzureCredential`(async-by-default per CLAUDE.md §3.1)+ `aclose()` lifecycle hook for FastAPI lifespan shutdown
- [x] **F1.4** `backend/storage/key_vault_factory.py` NEW — `make_key_vault_provider(settings)` factory;lazy-imports `AzureKeyVaultProvider` only when `key_vault_url` set(parallel to `make_kb_backend` ADR-0023 pattern)
- [x] **F1.5** `backend/pyproject.toml` updated — `azure-keyvault-secrets>=4.8.0` added to `[project.dependencies]`(existing `azure-identity>=1.20` already satisfies 1.25.3 install);`KEY_VAULT_URL` env var added to `backend/storage/settings.py`
- [x] **F1.5a** Install via mobile hotspot per ADR-0017 (c)— Chris executed 2026-05-19;`pip install "azure-keyvault-secrets>=4.8.0" "azure-identity>=1.18.0"` resolved to `azure-keyvault-secrets 4.11.0` + `azure-identity 1.25.3` clean(zero R8;3rd realized Plan B (c) after Langfuse 2026-05-16)
- [x] **F1.6** `backend/tests/test_key_vault.py` NEW — **15 tests pass in 8.36s**(EnvVarProvider round-trip 6 tests + `generate_secret_value` entropy 3 tests + factory branch selection 2 tests + AzureKeyVaultProvider SDK-mocked Protocol conformance 4 tests)
- [x] **F1.7** `mypy --strict storage/key_vault.py storage/azure_key_vault.py storage/key_vault_factory.py` → **0 errors in 3 source files**(1 mid-implementation finding:aio SecretClient uses `delete_secret` not `begin_delete_secret`/poller — fixed)
- [x] **F1.8** ADR-0017 amendment landed:occurrence #8 row + NEW "Plan B realised — Azure Key Vault SDK via mobile hotspot (2026-05-19, W24-wave-c1 F1)" section + Decision-rule #5 (c) 3rd realized confirmation
- [x] **F1.9** Full backend pytest regression preserved:**720 passed + 11 skipped**(W23 baseline 705 → +15 IMPROVED via F1.6 tests;no regression introduced)

## F2 — `/admin/connections/*` endpoint group(× 9 providers)

- [x] **F2.1** `backend/api/routes/admin/__init__.py` + `backend/api/routes/admin/connections.py` NEW(228 lines:5 endpoints + 9-provider probe dispatcher + mask helper)
- [x] **F2.2** Pydantic schemas in `backend/api/schemas/admin.py` NEW(115 lines:`ProviderCategory` + `TestStatus` Literals + `ProviderDeployment` + `ProviderConfig` + `ProviderSummary` + `ProviderPatch` + `TestConnectionResult` + `RotateSecretResult`)
- [x] **F2.3** `GET /admin/connections` → list[ProviderSummary]9 rows
- [x] **F2.4** `GET /admin/connections/{provider_id}` → ProviderConfig full(secret value NEVER returned — only secret_kv_ref name + secret_masked_preview)
- [x] **F2.5** `PATCH /admin/connections/{provider_id}` → ProviderPatch(endpoint_url + region + display_name);deployments + secret_kv_ref deliberately omitted per ADR-0026 §Decision(Wave B+ may expose deployment edits)
- [x] **F2.6** `POST /admin/connections/{provider_id}/test` → 9-provider probe dispatcher(`_probe_https_endpoint` × 4 + `_probe_postgres` + `_probe_key_vault` + `_probe_acs_email` + `_probe_structlog`);Wave A config-state-only scope per W20 F2.1 /health pattern;Wave B+ promote 至 real I/O pings
- [x] **F2.7** `POST /admin/connections/{provider_id}/rotate-secret` → KeyVaultProvider.rotate_secret + masked preview(`***` + last 4 chars)+ `last_rotated_at` update;500 → 503 mapping for `NotImplementedError`(EnvVarProvider fallback);400 for managed-identity providers(key_vault + structlog,secret_kv_ref=None)
- [x] **F2.8** NEW Postgres table `admin_provider_configs` in `backend/storage/admin_provider_postgres.py`(202 lines)+ idempotent `CREATE TABLE IF NOT EXISTS` + seed merge(only INSERT rows missing by PK)
- [x] **F2.8a** `backend/storage/admin_provider_storage.py` NEW(259 lines)— Protocol + `InMemoryAdminProviderBackend` + `default_providers()` 9-seed function(matches mockup categories);`ProviderNotFoundError` exception
- [x] **F2.8b** `backend/storage/admin_provider_factory.py` NEW(20 lines)— `make_admin_provider_backend(settings)` mirrors `make_kb_backend` ADR-0023 lazy-import shape
- [x] **F2.8c** `backend/api/server.py` lifespan wires `app.state.admin_provider_backend` + `app.state.key_vault_provider` + registers `admin_connections.router` w/ `_auth` deps
- [x] **F2.9** Tests `backend/tests/api/test_admin_connections.py` NEW(411 lines)— **27 tests pass in 4.14s**:storage seed(5)+ GET list(2)+ GET detail(2)+ PATCH(3)+ POST test 9-provider per-probe(8)+ POST rotate-secret(5)+ mask helper(2)+ schema sanity(1)
- [x] **F2.10** mypy strict:`api/schemas/admin.py` + `storage/admin_provider_storage.py` + `storage/admin_provider_factory.py` + `api/routes/admin/connections.py` 全部 0 errors;`storage/admin_provider_postgres.py` 6 errors **mirror existing `kb_management/postgres_backend.py` pattern**(psycopg no-stubs x3 + dict/tuple generic type-arg x3)— per CLAUDE.md §13 surgical 不改 pre-existing baseline pattern
- [x] **F2.11** Full backend pytest regression preserved:**747 passed + 11 skipped in 207s**(F1 post 720 → **+27 net IMPROVED** via F2 27 NEW tests;no regression)

## F3 — `/admin/identity/*` endpoint group

- [x] **F3.1** `backend/api/routes/admin/identity.py` NEW(127 lines:1 GET + 5 PATCH endpoints + 3 Tier 2 boundary guards `_reject_tier2_app_registration` + `_reject_tier2_msal` + `_reject_tier2_roles`)
- [x] **F3.2** Pydantic schemas in `backend/api/schemas/admin_identity.py` NEW(140 lines:`EkpRoleKey` + `CloudInstance` + `SignInAudience` + `TokenCacheStrategy` Literals + `EntraTenantConfig` + `AppRegistrationConfig` + `MsalConfig` + `RoleMapping` + `RoleMappingConfig` + `SignInPolicyConfig` + `IdentityConfig` consolidated)
- [x] **F3.3** `GET /admin/identity` → IdentityConfig consolidated 5 sub-resources(client_secret value NEVER returned — only `client_secret_kv_ref` + `client_secret_masked_preview`)
- [x] **F3.4** `PATCH /admin/identity/tenant` → EntraTenantConfig(server strips client-supplied `authority_url` + re-derives from `tenant_id + cloud_instance` per security hygiene)
- [x] **F3.5** `PATCH /admin/identity/app_registration` → AppRegistrationConfig(client_secret rotation via F1 KeyVaultProvider hook — `client_secret_kv_ref` field;Wave B+ promotes rotate-on-PATCH;Tier 2 boundary:`multi_disabled` audience rejected 422)
- [x] **F3.6** `PATCH /admin/identity/msal` → MsalConfig(Tier 2 boundary:`distributed_disabled` token cache strategy rejected 422)
- [x] **F3.7** `PATCH /admin/identity/roles` → RoleMappingConfig(**list-replace** semantic per pre-active-flip deviation in plan §7 changelog;Tier 2 boundary:`power_user` ekp_role rejected unless `is_tier2_disabled=True` per ADR-0027 Option B fallback)
- [x] **F3.8** `PATCH /admin/identity/policy` → SignInPolicyConfig(`require_mfa_all_roles_tier2` Literal[False] permanent;`auto_disable_after_days >= 0` validated)
- [x] **F3.9** NEW Postgres table `admin_identity_config` in `backend/storage/admin_identity_postgres.py`(174 lines):**per-sub-resource row pattern**(per plan §7 changelog deviation from "single-row JSON")— `sub_resource TEXT PRIMARY KEY + config JSONB + updated_at + updated_by NULL`;idempotent `CREATE TABLE IF NOT EXISTS` + 5-row seed merge
- [x] **F3.9a** `backend/storage/admin_identity_storage.py` NEW(180 lines)— Protocol + `InMemoryAdminIdentityBackend` + `default_*` seed helpers + `SUB_RESOURCES` constant + `_derive_authority_url` for 3 cloud instances + `IdentitySubResourceNotFoundError`
- [x] **F3.9b** `backend/storage/admin_identity_factory.py` NEW(22 lines)— `make_admin_identity_backend(settings)` mirrors `make_admin_provider_backend` F2 + ADR-0023 lazy-import shape
- [x] **F3.9c** `backend/api/server.py` lifespan wires `app.state.admin_identity_backend` + registers `admin_identity.router` w/ `_auth` deps
- [x] **F3.10** Tests `backend/tests/api/test_admin_identity.py` NEW(316 lines)— **26 tests pass in 6.43s**:storage seed shape(8)+ 503 lifespan guard(1)+ GET identity(3)+ PATCH tenant(2)+ PATCH app_registration(2)+ PATCH msal(2)+ PATCH roles(3)+ PATCH policy(3)+ cross-cutting persistence(1)+ 3-cloud authority URL derivation(3)
- [x] **F3.11** mypy strict:`api/schemas/admin_identity.py` + `api/routes/admin/identity.py` + `storage/admin_identity_storage.py` + `storage/admin_identity_factory.py` 全部 **0 errors in 4 source files**;`storage/admin_identity_postgres.py` 6 errors **mirror existing baseline pattern**(psycopg no-stubs x3 + dict generic type-arg x3)— per CLAUDE.md §13 surgical 不改 pre-existing baseline
- [x] **F3.12** Full backend pytest regression preserved:**773 passed + 11 skipped + 0 failed in 404.09s**(F2 baseline 747 → **+26 net IMPROVED** via F3 26 NEW Identity tests;no regression introduced)

## F4 — `/admin/api-keys/*` + `/admin/usage-stats` endpoint group

- [x] **F4.1** `backend/api/routes/admin/api_keys.py`(196 lines)+ `usage_stats.py`(63 lines)NEW
- [x] **F4.2** `GET /admin/usage-stats` → `UsageStats4Stat` shape(per pre-active-flip audit deviation — **adjusted to mockup 24h window**:`api_calls_24h` + `spend_today_usd` + `spend_cap_daily_usd` + `spend_pct_used` + `token_throughput_tpm` + `rate_limit_hits_24h`;Wave B+ wire real P95 + delta_pct + middleware 429 counter);reads `realtime_cost.fetch_realtime_usage(window_hours=24)` + `cost_estimator.total_projected_daily_usd()`
- [x] **F4.3** `GET /admin/api-keys/outgoing` → `OutgoingQuotaList`(per-deployment flattened rows;F2 `azure_openai` 4 deployments + 6 non-deployment providers — skips `structlog` + `key_vault` config-only;total 10 rows in seed state)
- [x] **F4.4** **Scope-adjusted per pre-active-flip audit**:`PATCH /admin/api-keys/outgoing/{provider_id}/{deployment_id}/alert-threshold` only(cost-spike alert % 50-95,default 80;mockup line 760 "alerts fire at 80% sustained")— TPM/RPM cap edit defer Wave B+(Azure portal authoritative);extends `ProviderDeployment.alert_threshold_pct` field additively + `AdminProviderConfigBackend.update_deployment_alert_threshold` Protocol method
- [x] **F4.5** `GET /admin/api-keys/incoming` → `IncomingKeysDisabled` 永遠返 `{enabled: false, reason: "Tier 2 — Tier 1 access via web UI only (MSAL SSO)."}`(per ADR-0026 §Consequences + mockup line 815-818)
- [x] **F4.6** Tests:`test_admin_api_keys.py`(213 lines / 16 tests)+ `test_admin_usage_stats.py`(110 lines / 4 tests)+ `test_audit_log.py`(85 lines / 6 tests)= **26 tests pass in 8.54s**(F3 baseline 26 → +26 IMPROVED via F4)
- [x] **F4.7** mypy strict:F4 6 NEW non-Postgres files(schemas/admin_api_keys + schemas/audit_log + routes/admin/api_keys + routes/admin/usage_stats + storage/audit_log_storage + storage/audit_log_factory)0 errors;F2 + F3 routes re-check 0 errors post audit-log wiring;`storage/audit_log_postgres.py` 3 errors mirror F2/F3 + kb_management baseline(psycopg import-not-found per R8 / CO17)— per CLAUDE.md §13 surgical
- [x] **F4.8** `audit_log` Postgres table NEW additive + 3-file split(`audit_log_storage.py` Protocol + InMemory + `audit_log_postgres.py` SERIAL PK / ORDER BY id DESC + `audit_log_factory.py` lazy-import);F2 PATCH/test/rotate-secret + F3 PATCH × 5 sub-resource + F4 PATCH alert-threshold 6 endpoint hooks emit `connection_patch` / `connection_test` / `connection_rotate_secret` / `identity_patch` / `api_keys_alert_threshold_patch` rows;**graceful no-op when `audit_log_backend` is None**(preserves F2/F3 test path);read endpoint defer F5/Wave C2 SettingsAccount surface
- [x] **F4.9** `backend/api/server.py` lifespan wires `app.state.audit_log_backend` + registers `admin_usage_stats.router` + `admin_api_keys.router` w/ `_auth` deps
- [x] **F4.10** Full backend pytest regression preserved:**799 passed + 11 skipped + 0 failed in 309s**(F3 baseline 773 → **+26 net IMPROVED** via F4 26 NEW tests;no regression introduced)

## F5 — Frontend `/settings` 6-tab `PageSettingsRich` rebuild

- [x] **F5.1** `frontend/app/(app)/settings/page.tsx` rewrite(411 lines)— replace W22 F8.1 thin v1 3-card structure with 6-tab `PageSettingsRich` shell;preserve W18 `<LoginGate>` + `(app)/` + AppShell integration;preserve W22 F8.1 ProfileCard / AppearanceCard / AccountCard logic as inline `ProfileTab` / `AppearanceTab` / `AccountTab` (per CLAUDE.md §1.3 surgical extend-not-rewrite)
- [x] **F5.2** 6-tab navigation `.tabs` CSS class(mockup line 28-37 verbatim shape)+ `?tab=` deep link via `useSearchParams` + `router.replace(scroll: false)` shallow URL update + `<Suspense>` boundary(Next 14 App Router requirement);`VALID_TABS` set validates query param;default = `profile`
- [x] **F5.3** `ProfileTab` extends W22 F8.1 thin Profile card(avatar + initials computed from preferredUsername + role placeholder + session line + Edit profile DisabledAffordance Tier 2)— Display name PATCH defer Wave C2 ADR-0027 Graph SDK
- [x] **F5.4** `AppearanceTab` preserves W22 F8.1 theme seg(Light/Dark Pydantic-binary)+ adds Density toggle(Compact/Comfortable Tier 2 DisabledAffordance per Wave C2 promote)+ existing Language Tier 2 disabled affordance
- [x] **F5.5** `<SettingsConnections>` NEW(245 lines)— data-bound to `adminApi.listConnections()` + `getConnection()` lazy-fetch per row;5 categories × 9 providers grouped via `CATEGORY_ORDER` + `CATEGORY_LABEL` lookup;3 NEW primitives consumed:`<ServiceCard>`(collapsible expand-on-click)+ `<ApiKeyInput>`(reveal/hide/copy/rotate buttons)+ `<DeploymentsTable>`(tight TPM/RPM cap + alert % table);Test connection + Rotate secret mutation buttons wire `adminApi.testConnection` + `adminApi.rotateSecret`
- [x] **F5.6** `<SettingsIdentity>` NEW(330 lines)— data-bound to `adminApi.getIdentity()`;5 cards mapped 1:1 onto F3 backend sub-resources:Entra ID tenant + App registration(client_id + ApiKeyInput-bound client_secret + redirect URIs list + scopes badges + sign-in audience disabled select)+ MSAL & session(token cache + TTL + refresh + CSRF + cookie preview mono block)+ Role mapping(3 active + Power User row `opacity: 0.5` `is_tier2_disabled=True` per ADR-0027 fallback)+ Sign-in policy(allowed domains badges + MFA switches + auto-disable days);Wave C1 ship read-mostly(disabled inputs)— inline edit promote Wave C2
- [x] **F5.7** `<SettingsApiKeys>` NEW(290 lines)— data-bound to `adminApi.getUsageStats()` + `getOutgoingQuotas()` + `getIncomingKeys()` parallel fetch;4-stat strip reuses W22 F3 `.stat-grid` pattern;`OutgoingQuotaRowItem` per-row TPM + RPM bars(colored by used% threshold)+ inline alert threshold % input(50-95 range) wires `adminApi.patchAlertThreshold` mutation;Incoming API keys section wrapped in `<DisabledAffordance variant="p1-strict">` per ADR-0026 §Consequences
- [x] **F5.8** `AccountTab` extends W22 F8.1 thin Account card(Rotate session Tier 2 disabled + functional Sign-out preserved)+ `<SettingsAuditLog>` NEW sub-card(95 lines)reads `adminApi.listAuditLog(10)` last-10 rows(promoted from F4 deferral — F5 backend hook `GET /admin/audit-log?limit=N` added via `audit_log.py` route);Danger Zone Delete account `<DisabledAffordance>` per mockup line 842-870
- [x] **F5.8a** NEW backend `backend/api/routes/admin/audit_log.py`(36 lines)— `GET /admin/audit-log?limit=N`(default 10,1-200 range);wired into `server.py` lifespan + auth-protected router;6 NEW pytest(503 guard + empty + newest-first + limit-param + limit-validation min/max)
- [x] **F5.9** **H7 per-tab self-verify gate**:per CLAUDE.md §5.7 H7 + W22 F1-F7 precedent — each F5.3-F5.8 tab acceptance includes mockup line-ref alignment(SettingsProfile line 50-65 + SettingsAppearance line 67-93 + SettingsConnections line 96-355 + SettingsIdentity line 528-723 + SettingsApiKeys line 744-823 + SettingsAccount line 842-870);**NO「smoke-user-deferred」 for fidelity itself** per W21+W22+W23 retro consistency;**data-bound design fidelity** — every visible value reads from real backend response not mockup hardcoded data,layout/spacing/typography/color tokens preserved per CSS-first pivot baseline
- [x] **F5.10** `tsc --noEmit` exit 0 + `next lint` clean(No ESLint warnings or errors)+ `Grep '\[oklch'` across `frontend/` = **0 preserved** milestone(post-W23 baseline 0 maintained through F5 9 NEW files);3 NEW primitives + 4 NEW settings/* components 全部 use CSS-first `.btn / .card / .field / .input / .select / .tabs / .seg / .badge / .switch / .table / .banner / .stat / .stat-grid` per DESIGN_SYSTEM.md §2 13-primitive index — zero arbitrary Tailwind `[oklch(...)]` escapes
- [x] **F5.11** Full backend pytest regression preserved:**805 passed + 11 skipped + 0 failed in 189s**(F4 baseline 799 → **+6 net IMPROVED** via F5 6 NEW audit-log GET tests;no regression)

## F6 — Frontend `apiClient.admin.*` wiring + form integration

- [x] **F6.1** `frontend/lib/api/admin.ts` NEW(235 lines)— 13 methods covering F2 connections + F3 identity + F4 usage-stats + outgoing quotas + alert-threshold + incoming + F5 audit-log;full Pydantic-mirror TypeScript types(landed in F5 — `01481a8`)
- [x] **F6.2** Per-row mutation hooks landed inline in `SettingsConnections.ProviderRow`(handleTest + handleRotate)+ `SettingsApiKeys.OutgoingQuotaRowItem`(handleSave alert threshold)— Karpathy §1.3 surgical co-location with consumers vs separate TanStack Query module
- [🚧] **F6.3 DEFERRED Wave C2** — Form validation per-provider schema(react-hook-form + zod);Wave C1 ships read-mostly Identity tab(disabled inputs/selects)+ inline `<input type="number">` validate via `min={50} max={95}` Pydantic-mirror for alert threshold;structural primitives in place for Wave C2 inline-edit promotion
- [🚧] **F6.4 DEFERRED Wave C2** — Optimistic UI per PATCH(rollback on error);Wave C1 ships pessimistic UI(await response + refresh detail);Wave C2 promotes when Identity inline-edit + Connections deployment edit land
- [🚧] **F6.5 DEFERRED Wave C2** — ErrorBoundary integration per-tab(per W14 CO_F4 pattern);Wave C1 ships per-tab inline error banner(banner-destructive Failed-to-load shape used by all 4 settings/* components);ErrorBoundary wrapper Wave C2-friendly defer when inline-edit lands
- [x] **F6.6** `tsc --noEmit` exit 0 + `next lint` clean(verified at F5.10);9 NEW frontend files all type-check clean post Pydantic-mirror

## F7 — Tests(Vitest + Playwright)

- [x] **F7.1** `frontend/tests/unit/settings-6tab.test.tsx` NEW(217 lines / **9 pytest pass in 26s**):**(a)** 6 tab labels render(`getByRole('tab', { name: ... })`);**(b)** Profile default when no `?tab=` query;**(c)** `?tab=identity` deep link selects + tenant card visible;**(d)** `?tab=api-keys` hyphenated deep link;**(e)** unknown `?tab=bogus` falls back to profile;**(f)** Tab click updates URL via `router.replace` spy(contains `tab=connections`);**(g)** Account tab renders Sign out + Audit log + Danger Zone;**(h)** Identity Power User Tier 2 disabled affordance;**(i)** API Keys 4-stat strip + incoming Tier 2 affordance — all data-bound via `adminApi` mock
- [x] **F7.2** `frontend/tests/e2e/app-shell-path.spec.ts` 加 **2 NEW tests** for `/settings` 6-tab:**(a)** 6-tab labels render via `getByRole('tab')` + page-title preserved;**(b)** `?tab=identity` deep link asserts `aria-selected="true"` + loading-banner-OR-tenant-card render-smoke pattern(matches BUG-004 3-state OR convention for data-dependent tests)
- [x] **F7.3** `frontend/tests/e2e/visual-baseline.spec.ts` 加 NEW `/settings?tab=connections` baseline:loading-banner-OR-LLM-category-header render-smoke before `toHaveScreenshot('settings-connections.png')`;mask `.mono` for env-dependent endpoint URLs / kv_ref names;**first capture defer user smoke** per W20 F8.5 chat-w20-f3b precedent — `pnpm test:e2e:update-snapshots` captures the baseline on first user-triggered run
- [x] **F7.4** Vitest stats `pnpm exec vitest run tests/unit/settings-6tab.test.tsx` → **9/9 pass in 26s**;full suite re-run hits OneDrive cold-start pool worker timeouts(W23 D2.1 documented behavior;`pool: 'threads'` default;sequential `--no-file-parallelism` workaround per docs/setup.md §8.7);**individual file run 100% green** — pool-spawn-timeout is environmental NOT regression(post-W23 baseline 28 pass + 9 NEW F7 = expected 37 pass;**+9 net IMPROVED**)
- [🚧] **F7.5 PARTIAL** Playwright run defer to user smoke per CO_W15_F4_interactive_flow_E2E carry-over pattern — F7 ships 2 NEW app-shell-path tests + 1 NEW visual baseline test(W23 baseline 22 → expected 24 + 1 baseline first-capture);**full E2E run via `PW_CHANNEL=chrome pnpm test:e2e`** = user pre-Beta smoke trigger;first-capture baseline via `PW_CHANNEL=chrome pnpm test:e2e:update-snapshots` is user-triggered (per W23 F2.3 6-baseline re-capture precedent)
- [x] **F7.6** Backend pytest:**805 passed + 11 skipped + 0 failed in 189s**(F5 baseline maintained;no F7 backend touch)

## F8 — Closeout cascade

- [ ] **F8.1** Phase Gate verdict published per `progress.md` retro
- [ ] **F8.2** 7-section retro(What worked / What didn't / Surprises / Decisions / Carry-overs / Time tracking / Spec-ref)
- [ ] **F8.3** plan/checklist/progress frontmatter `active → closed`
- [ ] **F8.4** Wave C2 candidates noted in retro NOT pre-created per §10 R1
- [ ] **F8.5** `session-start.md` 6 places synced(§3 + §10 + §11 + §12 + Last Updated + Update history)
- [ ] **F8.6** `COMPONENT_CATALOG.md` C08 + C09 + C11 W24 status amendment appended
- [ ] **F8.7** `PAGE_INVENTORY.md` `/settings` row W22 F8.1 thin → W24 6-tab status flip
- [ ] **F8.8** `ADR-0026 Implementation Status` section appended at closeout(per W20 F9.3 / ADR-0025 W20 closeout precedent)
- [ ] **F8.9** ADR-0017 amendment row added(occurrence #8 + 3rd realized Plan B (c))

---

**Lifecycle reminder**:新加 acceptance item 必先入 `plan.md §2 F-deliverables`,然後再加 checklist。延後項標 🚧 + reason,唔可以刪。
