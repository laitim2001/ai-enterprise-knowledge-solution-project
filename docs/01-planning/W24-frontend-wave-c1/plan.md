---
phase: W24-frontend-wave-c1
name: "Settings 6-tab Hub + Connections + Identity & Auth + API Keys & Quotas — ADR-0026 Option B fully editable + Key Vault SDK (Plan B (c) mobile hotspot first)"
sprint_week: W24
start_date: 2026-05-19              # real-calendar — Chris directive 2026-05-19 「start W24-wave-c1 kickoff」 post BUG-003 + BUG-004 closure
end_date: 2026-05-24                # ~3-5 day window per backend-heavy 22 NEW endpoints + Key Vault SDK install + 6-tab frontend rebuild;real-calendar collapse 1.5-12× pattern applies — actual likely ~2-4 days per W19-W23 trajectory;frontmatter is a window, not a commitment
status: active                      # active from kickoff 2026-05-19
spec_refs:
  - CLAUDE.md §10 R1-R6             # rolling JIT + plan-before-code (multi-day Phase work) + R6 pre-active-flip recursive (plan-text grep audit)
  - CLAUDE.md §5.1 H1               # architecture.md §5.0 amendment (Settings v1 thin → 6-tab hub)
  - CLAUDE.md §5.2 H2               # Key Vault SDK NEW dependency (azure-keyvault-secrets + azure-identity)
  - CLAUDE.md §5.7 H7               # frontend mockup fidelity (ekp-page-settings-tabs.jsx PageSettingsRich 100% reproduction)
  - architecture.md v6 §5.0         # Settings page spec (v1 thin per ADR-0024 → 6-tab hub per ADR-0026 W24 amendment)
  - architecture.md v6 §3.7         # Application architecture (identity & auth — interplay with Settings Identity tab)
  - ADR-0026                        # Settings 6-tab + Connections backend (Option B fully editable)
  - ADR-0017                        # R8 corp-proxy mitigation pattern (Plan B (c) mobile hotspot for Key Vault SDK)
  - ADR-0022                        # auth-transport hardening (Identity & Auth tab MSAL config basis)
  - ADR-0023                        # Postgres persistent backing (Settings persists provider config via Postgres + Key Vault)
prior_phase: W23-frontend-test-cleanup  # closed 2026-05-19 PASS WITH F2 PARTIAL CAVEAT + BUG-003/004 same-session
related_artifacts:
  - docs/adr/0026-settings-6-tab-hub-and-connections-backend.md  # primary ADR — Option B Accepted
  - docs/adr/0017-r8-corp-proxy-mitigation-pattern.md             # Plan B sequencing reference
  - references/design-mockups/ekp-page-settings-tabs.jsx          # 882 lines, PageSettingsRich + 6 SubComponents
  - references/design-mockups/DESIGN_SYSTEM.md                    # §0 quick reference + §2 13-primitive + §4 composite patterns
  - frontend/app/(app)/settings/page.tsx                          # W22 F8.1 thin v1 (104 lines, 3 cards) — TARGET for 6-tab rebuild
  - frontend/lib/api/                                             # apiClient module — add `apiClient.admin.*` group
  - backend/api/routes/                                           # NEW `/admin/*` route group (currently no admin routes)
  - backend/storage/                                              # NEW `key_vault.py` Protocol + EnvVarProvider + AzureKeyVaultProvider
  - .env.example                                                  # NEW KEY_VAULT_URL env var
---

# Phase W24-wave-c1 — Settings 6-tab Hub + Connections + Identity & Auth + API Keys & Quotas Plan

> **Authorization**:Chris explicit directive 2026-05-19(post BUG-003 + BUG-004 closeout pushed to remote):
>
> 「**start W24-wave-c1 kickoff**」
>
> 2 AskUserQuestion confirmations 2026-05-19:
> 1. **Wave C1 scope** = Settings 6-tab Option B 唯一(Access tab + /users defer Wave C2 per ADR-0025 RBAC dep)
> 2. **Key Vault SDK Plan B sequencing** = (c) mobile hotspot 首輪(reuse Langfuse SDK 2026-05-16 Plan B (c) precedent;skip PyPI binary CDN R8 risk)
>
> Wave C1 = **Beta-readiness milestone**:Settings 6-tab Hub 提供 centralized visibility for 9 external services + identity config + API quotas;**Connections + Identity + API Keys** = Beta operator self-service rotation 取代 `.env` rotation rituals + Azure Portal trips。

---

## §0 Phase identity

**Trigger**:Chris W23 closeout decision 2026-05-19 → W24-wave-c1 kickoff per W19 F4 §3.6 Wave C split trigger + CLAUDE.md §10 R1 rolling JIT。

**Decision authority**:Chris W19 F6 ADR-0026 Accepted Option B(fully editable;over Option C hybrid recommended)+ ADR-0017 Plan B (c) mobile hotspot pick W24 kickoff(over PyPI 首輪 + defer)。

**Scope**:
- F0 Kickoff cascade(plan + checklist + progress + architecture.md v6 §5.0 inline-tagged amendment)
- F1 Backend `KeyVaultProvider` abstraction + `AzureKeyVaultProvider`(install azure-keyvault-secrets + azure-identity via mobile hotspot per ADR-0017 (c))
- F2 Backend `/admin/connections/*` endpoint group(× 9 providers list/get/patch + test connection + rotate secret)~10 endpoints
- F3 Backend `/admin/identity/*` endpoint group(tenant / app registration / msal config / role mapping / sign-in policy)~8 endpoints
- F4 Backend `/admin/api-keys/*` + `/admin/usage-stats` endpoint group + audit_log row writes(table additive — Tier 2 expansion path)~4 endpoints
- F5 Frontend `/settings` 6-tab `PageSettingsRich` rebuild(per CLAUDE.md §5.7 H7 + mockup `ekp-page-settings-tabs.jsx` 100% fidelity)+ 4 NEW sub-components(SettingsConnections + SettingsIdentity + SettingsApiKeys + SettingsAccount enhancements)+ 3 NEW primitives(ServiceCard + ApiKeyInput + DeploymentsTable)
- F6 Frontend `apiClient.admin.*` wiring(react-query / TanStack Query mutation hooks + optimistic UI + ErrorBoundary integration + form validation per provider schema)
- F7 Tests(Vitest 6-tab navigation + Connections test-connection flow + Identity & Auth save flow + Playwright E2E render-smoke + visual baseline capture)
- F8 Closeout(Gate verdict + retro + session-start sync + ADR-0026 Implementation Status section append + COMPONENT_CATALOG C09 + C08 status notes + PAGE_INVENTORY /settings 6-tab status flip)

**Out of scope**:
- ADR-0027 /users Tier 1.5 RBAC — Wave C2 deferred(6 NEW Postgres tables + Entra Graph SDK + ACL middleware)
- ADR-0025 Access tab activation — Wave C2 deferred(`kb_acl` table dep on RBAC backend)
- Real-MSAL feature flag concurrent ship — Wave C2 user 岔口 2(Wave C1 仍 mock-auth default per W18+ pattern)
- W16 F1-F4 Track A IT cred — parallel external-blocked track
- CO17 R8 umbrella(F1.5b psycopg / F3.5b RAGAs live-verify)— external-blocked
- New eval / new model / new vendor outside of Key Vault SDK + azure-identity(scope locked per ADR-0026 + ADR-0017)

**Authorities**:
- **CLAUDE.md §10 R1-R6** — rolling JIT + plan-before-code(Phase-class work)+ R6 pre-active-flip 5-step grep audit recursive(plan-text + code-at-active-flip per W22 D1+D8+D9 evidence)
- **CLAUDE.md §5.1 H1** — `architecture.md v6 §5.0` v1 thin spec → 6-tab hub = architectural addition(ADR-0026 Accepted + Wave C1 implementation)
- **CLAUDE.md §5.2 H2** — Key Vault SDK NEW dep(per ADR-0026 Option B + ADR-0017 Plan B (c) mitigation)
- **CLAUDE.md §5.7 H7** — frontend mockup fidelity(`PageSettingsRich` 100% reproduction;per-tab H7 self-verify gate;NO「smoke-user-deferred」 for fidelity itself per W21+W22+W23 retro consistency)
- **ADR-0026** Status Accepted(Chris W19 F6 pick Option B over recommended Option C)
- **ADR-0017** Plan B (c) sequencing(Chris W24 kickoff pick over PyPI 首輪)

---

## §1 Authorization + spec refs

| F-deliverable | Authorization | Spec ref |
|---|---|---|
| F0 Kickoff | this plan + Chris kickoff directive | CLAUDE.md §10 R1 + R5 + §1 + ADR-0026 §References |
| F1 KeyVaultProvider abstraction + Azure SDK install | ADR-0026 §Decision Option B + ADR-0017 Plan B (c) | `backend/storage/key_vault.py` NEW + `requirements.txt` add `azure-keyvault-secrets>=4.8.0 azure-identity>=1.18.0` + ADR-0017 §Decision-rule #5 |
| F2 `/admin/connections/*` | ADR-0026 §Decision Option B + W19 F2 §3.4 items 11-13 | `backend/api/routes/admin/connections.py` NEW + mockup `ekp-page-settings-tabs.jsx:96-355 SettingsConnections` |
| F3 `/admin/identity/*` | ADR-0026 §Decision Option B + ADR-0014/0022 interplay | `backend/api/routes/admin/identity.py` NEW + mockup `ekp-page-settings-tabs.jsx:528-723 SettingsIdentity` |
| F4 `/admin/api-keys/*` + `/admin/usage-stats` | ADR-0026 §Decision Option B + audit_log preview Wave C2 dep | `backend/api/routes/admin/api_keys.py` NEW + mockup `ekp-page-settings-tabs.jsx:744-823 SettingsApiKeys` |
| F5 Frontend 6-tab PageSettingsRich | CLAUDE.md §5.7 H7 + mockup ekp-page-settings-tabs.jsx 100% fidelity | `frontend/app/(app)/settings/page.tsx` rewrite + 4 NEW sub-components + 3 NEW primitives |
| F6 apiClient.admin wiring | ADR-0026 §Decision Option B integration | `frontend/lib/api/admin.ts` NEW + TanStack Query mutation hooks |
| F7 Tests | CLAUDE.md §5.6 H6 + W23 Playwright pattern(render-smoke 3-state OR)| `frontend/tests/unit/settings-6tab.test.tsx` + `frontend/tests/e2e/app-shell-path.spec.ts` 加 /settings 6-tab assertions |
| F8 Closeout | CLAUDE.md §10 R3 + W19-W23 closeout pattern | this plan §3 Gate criteria + ADR-0026 Implementation Status section append |

---

## §2 F0-F8 deliverables

**Rolling JIT discipline**:F0 + F1 detailed kickoff time;F2-F8 sketched;detail refines per-deliverable at kickoff time per W12-W23 pattern。Per CLAUDE.md §10 R6 — pre-active-flip 5-step grep audit applied **recursively** to plan-text **and** code-at-active-flip-time(W22 D1+D8+D9 evidence)。

### F0 — Kickoff cascade(landed at phase open — `(this commit)`)

- **Component(s)**:governance(no Cn touched at F0)
- **Spec ref**:CLAUDE.md §10 R1 + this plan §0
- **OQ deps**:none
- **Acceptance criteria**:
  - F0.1 W24 `plan.md`(this file)+ `checklist.md` + `progress.md` created `status: active` 2026-05-19
  - F0.2 NO `frontend/` or `backend/` code change at kickoff(per W19-W23 F0 precedent — F0 governance only)
  - F0.3 `architecture.md v6 §5.0` Settings paragraph inline-tagged amendment landed at kickoff(thin v1 → 6-tab hub per ADR-0026 Accepted Option B + ADR-0024 / §3.4 / §3.7 inline-tag precedent;doc version held)
  - F0.4 Pre-active-flip 5-step grep audit recursive(per R6):W22-W23 plan-text contamination check + `frontend/app/(app)/settings/page.tsx` current state confirmed thin v1 + `backend/api/routes/` confirmed 14 routes no `/admin` group + `references/design-mockups/ekp-page-settings-tabs.jsx` 882 lines structure confirmed
  - F0.5 W24 kickoff cascade committed `(this commit)`
- **Effort estimate**:0.25 day(this commit)

### F1 — KeyVaultProvider abstraction + Azure SDK install(Plan B (c) mobile hotspot)

- **Component(s)**:**C08** API Gateway(storage layer extension)+ **C12** DevOps & Infra(SDK install + env var)
- **Spec ref**:
  - ADR-0026 §Decision Option B
  - ADR-0017 §Decision-rule #5 Plan B sequencing (c) mobile hotspot
  - Langfuse SDK 2026-05-16 Plan B (c) precedent(`backend/observability/observe.py` v2/v4 adapter shim)
- **OQ deps**:none(Q5 Cohere Path A 已 Resolved 不影響 azure-keyvault-secrets install path)
- **Acceptance criteria**:
  - F1.1 `backend/storage/key_vault.py` NEW — `KeyVaultProvider` Protocol(`get_secret(name) -> str | None` + `set_secret(name, value) -> bool` + `delete_secret(name) -> bool` + `list_secrets() -> list[SecretMetadata]` + `rotate_secret(name) -> str`)
  - F1.2 `EnvVarProvider` impl — fallback when `KEY_VAULT_URL` unset(reads from `.env` / `os.environ`;rotate_secret raises `NotImplementedError` since env-var rotation needs process restart)
  - F1.3 `AzureKeyVaultProvider` impl — production path;依賴 `azure-keyvault-secrets>=4.8.0` + `azure-identity>=1.18.0`(DefaultAzureCredential / ManagedIdentityCredential)
  - F1.4 `make_key_vault_provider() -> KeyVaultProvider` factory — `KEY_VAULT_URL` env var presence decides AzureKeyVaultProvider vs EnvVarProvider fallback(parallel pattern to `make_kb_backend` / `make_users_store` per ADR-0023)
  - F1.5 `requirements.txt` adds `azure-keyvault-secrets>=4.8.0` + `azure-identity>=1.18.0`(if not transitively present)
  - F1.5a Install via mobile hotspot per ADR-0017 (c) — same precedent as Langfuse 2026-05-16 `dffe19a`(switch to mobile hotspot → `pip install azure-keyvault-secrets azure-identity` → switch back)
  - F1.6 Tests:`backend/tests/storage/test_key_vault.py` NEW — EnvVarProvider 完整 round-trip + AzureKeyVaultProvider 用 `unittest.mock` patch(real Azure call **NOT** in unit test;integration smoke 在 W24+/CO17 R8 umbrella per Track A IT cred trigger)
  - F1.7 `mypy --strict backend/storage/key_vault.py` clean
  - F1.8 ADR-0017 amendment landed:occurrence #8 row(Key Vault SDK install via mobile hotspot Plan B (c) — 3rd realized occurrence after Langfuse 2026-05-16)
- **Effort estimate**:1 backend day(0.5 abstraction + 0.25 SDK install + 0.25 tests + ADR amendment)

### F2 — `/admin/connections/*` endpoint group(× 9 providers)

- **Component(s)**:**C08** API Gateway(NEW `/admin/*` route group)+ **C02** KB Manager(若 Provider state 入 Postgres + Key Vault hybrid)
- **Spec ref**:
  - ADR-0026 §Decision Option B
  - mockup `ekp-page-settings-tabs.jsx:96-355 SettingsConnections`(5 categories × 9 providers)
  - W19 F2 §3.4 items 11(Azure OpenAI 4 deployments + TPM/RPM bars)
- **OQ deps**:Q5 Cohere Path A(Resolved)
- **Acceptance criteria**:
  - F2.1 `backend/api/routes/admin/__init__.py` + `backend/api/routes/admin/connections.py` NEW
  - F2.2 9 providers schema(Pydantic v2)— Azure OpenAI(4 deployments)+ Cohere + Azure AI Search + Azure Blob + Postgres + Azurite + Langfuse + structlog + ACS Email + Container Apps + Key Vault — `ProviderConfig` + `ProviderDeployment` + `ProviderUsageStats` Pydantic models
  - F2.3 `GET /admin/connections` → list[ProviderSummary](9 entries with status / category / last_test_at)
  - F2.4 `GET /admin/connections/{provider_id}` → ProviderConfig full(secret values masked;deployments + meta)
  - F2.5 `PATCH /admin/connections/{provider_id}` → update non-secret fields(endpoint URL / region / deployment name);writes to Postgres `admin_provider_configs` table(NEW)+ audit_log row(Wave C2 expansion)
  - F2.6 `POST /admin/connections/{provider_id}/test` → lightweight connection probe(per provider;Azure OpenAI = `models.list()` call / Cohere = `models` endpoint / Azure AI Search = `get_service_statistics()` / Postgres = `SELECT 1` / etc.)→ `{status, latency_ms, detail}` shape(reuse `/health` `ComponentHealth` Pydantic per W20 F2.1)
  - F2.7 `POST /admin/connections/{provider_id}/rotate-secret` → calls `KeyVaultProvider.rotate_secret(provider_id.secret_name)` + Postgres `admin_provider_configs.last_rotated_at` update + audit_log row
  - F2.8 NEW Postgres table `admin_provider_configs`(per ADR-0023 base):`provider_id` PK + `category` + `endpoint_url` + `region` + `deployments_json` + `last_test_at` + `last_test_status` + `last_test_detail` + `last_rotated_at` + `secret_kv_ref`(Key Vault secret name reference)+ `created_at` + `updated_at`;idempotent `ALTER TABLE ADD COLUMN IF NOT EXISTS` migration per W17 F1 pattern
  - F2.9 Tests `backend/tests/api/admin/test_connections.py` NEW — 9 provider list + per-provider get + patch round-trip + test-connection mock(per provider)+ rotate-secret with `MockKeyVaultProvider` fixture(~30+ pytest cases)
  - F2.10 mypy strict + pytest pass
- **Effort estimate**:2.5 backend days(0.5 schema + 1 endpoints + 0.5 Postgres + 0.5 tests)

### F3 — `/admin/identity/*` endpoint group(MSAL + Entra config + Role mapping)

- **Component(s)**:**C08** API Gateway(`/admin/*` extension)+ **C11** Identity & Access(config persistence)
- **Spec ref**:
  - ADR-0026 §Decision Option B
  - ADR-0014 hybrid auth basis
  - ADR-0022 auth-transport hardening
  - mockup `ekp-page-settings-tabs.jsx:528-723 SettingsIdentity`(Entra tenant + App registration + MSAL config + Role mapping + Sign-in policy)
- **OQ deps**:Q11 operational(committed early June 2026 — mock auth bridge preserved Wave C1)
- **Acceptance criteria**:
  - F3.1 `backend/api/routes/admin/identity.py` NEW — 5 sub-resources(tenant / app_registration / msal / roles / policy)
  - F3.2 Pydantic schemas — `EntraTenantConfig` + `AppRegistrationConfig` + `MsalConfig` + `RoleMappingConfig` + `SignInPolicyConfig`
  - F3.3 `GET /admin/identity` → consolidated state(all 5 sub-resources;client_secret masked)
  - F3.4 `PATCH /admin/identity/tenant` → update tenant_id + display_name + verified_domains(verified_domains read-only — Entra-controlled,Tier 2 sync per ADR-0027 Wave C2)
  - F3.5 `PATCH /admin/identity/app_registration` → update redirect URIs + scopes + sign-in audience(client_secret rotation via KeyVaultProvider per F1)
  - F3.6 `PATCH /admin/identity/msal` → update token cache strategy(memory / Redis-Tier-2 disabled affordance)+ TTL + refresh rotation enabled + CSRF rotation enabled(persists to Postgres `admin_identity_config` table NEW)
  - F3.7 `PATCH /admin/identity/roles` → update Entra group → EKP role mapping(3 active roles + Power User Tier 2 disabled affordance per ADR-0027 Option B fallback)
  - F3.8 `PATCH /admin/identity/policy` → update allowed sign-in domains + MFA toggles + auto-disable thresholds
  - F3.9 NEW Postgres table `admin_identity_config`(per ADR-0023 base):single-row config(sub_resource_key PK + config_json + updated_at + updated_by)
  - F3.10 Tests `backend/tests/api/admin/test_identity.py` NEW — 5 sub-resource get/patch round-trip + audit_log row write verify(~15 pytest cases)
  - F3.11 mypy strict + pytest pass
- **Effort estimate**:2 backend days(0.5 schemas + 1 endpoints + 0.5 tests)

### F4 — `/admin/api-keys/*` + `/admin/usage-stats` endpoint group

- **Component(s)**:**C08** API Gateway(`/admin/*` extension)+ **C07** Observability Stack(usage stats consume real-time cost tracker per W10 D3)
- **Spec ref**:
  - ADR-0026 §Decision Option B
  - mockup `ekp-page-settings-tabs.jsx:744-823 SettingsApiKeys`(4-stat usage strip + per-provider TPM/RPM quotas + Incoming API keys table Tier 2 disabled)
  - W10 D3 `backend/observability/realtime_cost.py` 重用
- **OQ deps**:none
- **Acceptance criteria**:
  - F4.1 `backend/api/routes/admin/api_keys.py` NEW + `backend/api/routes/admin/usage_stats.py` NEW
  - F4.2 `GET /admin/usage-stats` → consolidated 4-stat strip(total_requests_7d + total_tokens_7d + total_cost_7d_usd + total_errors_7d)+ per-provider TPM/RPM consumption + per-provider quota limits(reads from `realtime_cost.py` aggregator)
  - F4.3 `GET /admin/api-keys/outgoing` → list of per-provider TPM/RPM quota config(read from `admin_provider_configs.deployments_json` or NEW dedicated table — F2 + F4 schema interplay decision at F4 active-flip time per R6)
  - F4.4 `PATCH /admin/api-keys/outgoing/{provider_id}` → update quota config(TPM cap + RPM cap + cost alert threshold)
  - F4.5 `GET /admin/api-keys/incoming` → 永遠返 `{enabled: false, reason: "Tier 2 — Tier 1 access via web UI only"}` 嘅 disabled affordance shape(per ADR-0026 §Consequences)
  - F4.6 Tests `backend/tests/api/admin/test_api_keys.py` + `test_usage_stats.py` NEW(~12 pytest cases)
  - F4.7 mypy strict + pytest pass
  - F4.8 `audit_log` row writes preview(F2-F4 endpoint writes structured rows;`audit_log` Postgres table NEW additive — Tier 2 expansion via ADR-0027 Wave C2 just adds UI;Tier 1 starts writing rows for forward-compat retention)
- **Effort estimate**:1.5 backend days

### F5 — Frontend `/settings` 6-tab `PageSettingsRich` rebuild(per CLAUDE.md §5.7 H7)

- **Component(s)**:**C09** Admin Console UI(`/settings` page-level rebuild)
- **Spec ref**:
  - CLAUDE.md §5.7 H7 mockup fidelity
  - mockup `ekp-page-settings-tabs.jsx:7-46 PageSettingsRich`(6 tabs + tab navigation)
  - mockup `ekp-page-settings-tabs.jsx:50-94 SettingsProfile`(extend W22 F8.1 thin profile)
  - mockup `ekp-page-settings-tabs.jsx:96-355 SettingsConnections`(massive 9-provider surface)
  - mockup `ekp-page-settings-tabs.jsx:528-723 SettingsIdentity`(Entra + MSAL + role + policy)
  - mockup `ekp-page-settings-tabs.jsx:744-823 SettingsApiKeys`(usage strip + quotas table)
  - mockup `ekp-page-settings-tabs.jsx:842-870 SettingsAccount`(extend W22 F8.1 thin account + Connections audit log integration)
  - `references/design-mockups/DESIGN_SYSTEM.md` §0 quick reference + §2 13-primitive + §4 composite patterns(ServiceCard / ApiKeyInput / DeploymentsTable / OptionRow / DisabledAffordance)
- **OQ deps**:none
- **Acceptance criteria**:
  - F5.1 `frontend/app/(app)/settings/page.tsx` rewrite — replace thin v1 3-card structure with 6-tab `PageSettingsRich`;preserve W18 `<LoginGate>` + `(app)/` route group + AppShell integration
  - F5.2 6 tab navigation(.tabs CSS class per DESIGN_SYSTEM.md §2)+ `?tab=` deep link(per W18 F3 URL pattern;default = `profile`)
  - F5.3 `<SettingsProfile>` component — extend W22 F8.1 thin Profile card with Display name PATCH + Email read-only(Q11 Entra-controlled)+ Locale select(en disabled affordance per i18n Tier 2)
  - F5.4 `<SettingsAppearance>` component — preserve W22 F8.1 thin Appearance theme toggle + add Density toggle(Compact / Comfortable;Tier 2 disabled affordance per Wave C2 promote)
  - F5.5 `<SettingsConnections>` NEW — 5 categories × 9 providers,each card uses NEW `<ServiceCard>` primitive(expandable);secret fields use NEW `<ApiKeyInput>` primitive(reveal/hide/copy/rotate);deployments table uses NEW `<DeploymentsTable>` primitive(TPM/RPM consumption bars);per provider "Test connection" button consumes `apiClient.admin.testConnection(provider_id)` mutation
  - F5.6 `<SettingsIdentity>` NEW — Entra tenant card + App registration card + MSAL config card + Role mapping card(3 active + Power User disabled affordance per ADR-0027 Option B fallback)+ Sign-in policy card
  - F5.7 `<SettingsApiKeys>` NEW — 4-stat usage strip(reuse W22 F3 `.stat-grid` pattern)+ Outgoing API quotas table(per provider TPM/RPM bars)+ Incoming API keys table wrapped in `<DisabledAffordance variant="p2-tier2" reason="Tier 2 — Tier 1 access via web UI only">`
  - F5.8 `<SettingsAccount>` NEW — extend W22 F8.1 thin Account card(sign-out preserved)with Audit log preview surface(reads `audit_log` last-10 rows via `GET /admin/audit-log?limit=10`)+ DangerZone(Delete account = Tier 2 disabled affordance)
  - F5.9 H7 per-tab verification gate(per W22 F1-F7 precedent):每個 tab acceptance 包含 H7 7-item self-verify + user-eye side-by-side verify against mockup;NO「smoke-user-deferred」 for fidelity itself per W21+W22+W23 retro consistency
  - F5.10 `tsc --noEmit` exit 0 + `next lint` clean + `Grep '\[oklch'` across `frontend/` = 0 preserved
- **Effort estimate**:3 frontend days(1 PageSettingsRich shell + tab nav + 2 sub-components / 1.5 Connections + Identity sub-components + 3 primitives / 0.5 ApiKeys + Account)

### F6 — Frontend `apiClient.admin.*` wiring + form integration

- **Component(s)**:**C09** Admin Console UI(API client extension)
- **Spec ref**:
  - F2 + F3 + F4 backend endpoints
  - W17 F4 frontend hardening bundle precedent
  - W20 F3 advanced surfaces TanStack Query mutation hooks precedent
- **OQ deps**:none
- **Acceptance criteria**:
  - F6.1 `frontend/lib/api/admin.ts` NEW — `apiClient.admin.connections.*` + `apiClient.admin.identity.*` + `apiClient.admin.apiKeys.*` + `apiClient.admin.usageStats.*` + `apiClient.admin.auditLog.*` methods
  - F6.2 TanStack Query mutation hooks per CRUD endpoint(`useConnectionList()` + `useConnectionDetail(id)` + `useUpdateConnection()` + `useTestConnection()` + `useRotateSecret()` etc.)
  - F6.3 Form validation per provider schema(use existing react-hook-form + zod schema pattern from W20 F4 5-step wizard)
  - F6.4 Optimistic UI per PATCH(immediate UI update + rollback on error per TanStack Query mutation pattern)
  - F6.5 ErrorBoundary integration per tab(per W14 CO_F4_error_boundary pattern;each tab wraps its sub-component in `<ErrorBoundary fallback={<TabErrorState />}>`)
  - F6.6 `tsc --noEmit` exit 0 + `next lint` clean
- **Effort estimate**:1.5 frontend days

### F7 — Tests(Vitest + Playwright)

- **Component(s)**:**C09** Admin Console UI(test layer)
- **Spec ref**:
  - CLAUDE.md §5.6 H6 test coverage constraint(C09 frontend nice-to-have but Wave C1 backend-heavy → H6 strict applies)
  - W23 F2 Playwright render-smoke pattern(3-state OR for data-dependent tests)
  - W22 F8.7 Vitest pattern(per-tab DOM coverage)
- **OQ deps**:none
- **Acceptance criteria**:
  - F7.1 `frontend/tests/unit/settings-6tab.test.tsx` NEW — Vitest 6-tab navigation(tab switch + ?tab= deep link + active state)+ Connections test-connection mutation mock(success + error paths)+ Identity & Auth save flow + ApiKeyInput reveal/hide/copy interactions
  - F7.2 `frontend/tests/e2e/app-shell-path.spec.ts` 加 `/settings` 6-tab assertions(per W23 F2 pattern):page-title「Settings」+ tab navigation 6-item visible + tab content render-smoke(per tab 一個 visible content marker)
  - F7.3 `frontend/tests/e2e/visual-baseline.spec.ts` 加 `/settings?tab=connections` baseline capture(first time;per W23 F2.3 first-capture pattern)
  - F7.4 Vitest stats `pnpm test:unit` ≥ 32 pass(W23 baseline 28 → +4 IMPROVED via 4 NEW Settings test cases)
  - F7.5 Playwright stats `PW_CHANNEL=chrome pnpm exec playwright test` ≥ 24/24 pass(W23 baseline 22/22 → +2 IMPROVED via 2 NEW Settings cases)
  - F7.6 Backend pytest:全 backend regression preserved(W24 不 touch existing code;`pytest tests/` ≥ 705 + F2/F3/F4 new tests ~60+ = ~765+ pass)
- **Effort estimate**:1 day(parallel Vitest + Playwright + backend tests written 同 F2-F6 同步)

### F8 — Closeout cascade

- **Component(s)**:governance(no Cn touched)
- **Spec ref**:CLAUDE.md §10 R3 changelog + R5 ADR-before-implement(W24 不 trigger NEW ADR — ADR-0026 + ADR-0017 既存)+ W19-W23 closeout pattern
- **OQ deps**:none
- **Acceptance criteria**:
  - F8.1 Phase Gate verdict published per `progress.md` retro
  - F8.2 7-section retro in `progress.md` Day N(What worked / What didn't & friction / Surprises / Decisions / Carry-overs to Wave C2 / Time tracking / Spec-ref alignment)
  - F8.3 plan/checklist/progress frontmatter `active → closed`
  - F8.4 Wave C2 candidates noted in retro **NOT pre-created** per CLAUDE.md §10 R1 rolling JIT
  - F8.5 `session-start.md` 6 places synced(§3 C08 + C09 + C11 W24 status notes + §10 W24 row closed + W24+ row update + §11 NEW W24 CLOSED block + §12 milestones W24 row + 累計 22→23 phase closed + Last Updated + Update history row)
  - F8.6 `COMPONENT_CATALOG.md` C08 + C09 + C11 W24 status amendment appended
  - F8.7 `PAGE_INVENTORY.md` `/settings` row W22 F8.1 thin → W24 6-tab status flip
  - F8.8 `ADR-0026 Implementation Status` section appended at closeout(per W20 F9.3 / ADR-0025 W20 closeout precedent)
  - F8.9 ADR-0017 amendment row added(occurrence #8 Key Vault SDK Plan B (c) realised)
- **Effort estimate**:0.5 day

---

## §3 Success criteria + Gate criteria

Phase Gate **PASS** requires:

1. **All F0-F8 `[x]` complete**(74+ atomic items;atomic items per F detailed at F kickoff time)
2. **Backend new endpoint scope landed**:F2 ~10 + F3 ~8 + F4 ~4 = ~22 NEW `/admin/*` endpoints + 60+ new pytest cases
3. **Frontend mockup-fidelity gate per H7**:6 tabs × per-tab H7 7-item self-verify ALL passed + per-tab user-eye side-by-side verify ALL passed(no「smoke-user-deferred」for fidelity itself per W21+W22+W23 retro consistency)
4. **Key Vault SDK install via mobile hotspot Plan B (c) success**(F1.5a)+ `MockKeyVaultProvider` test coverage(F1.6)
5. **No backend regression**:full pytest 705 pre-W24 + ~60 new = ~765+ pass(W23 baseline 705 + 11 skipped + 0 fail)
6. **Verify gates all green**:`tsc --noEmit` exit 0 + `next lint` clean + `Grep '\[oklch'` = 0 preserved + `mypy --strict backend/storage/key_vault.py backend/api/routes/admin/` clean(F1-F4 NEW code only;104 pre-existing baseline errors NOT in scope per CLAUDE.md §13 surgical)
7. **Vitest stats**:`pnpm test:unit` ≥ 32 pass(W23 baseline 28 → +4 IMPROVED)
8. **Playwright stats**:`PW_CHANNEL=chrome pnpm exec playwright test` ≥ 24/24 pass(W23 baseline 22/22 → +2 IMPROVED)
9. **architecture.md v6 §5.0 amendment landed at F0**(per ADR-0024 / §3.4 / §3.7 inline-tag precedent;doc version held)
10. **ADR-0026 Implementation Status section appended at F8.8**(per W20 F9.3 precedent)
11. **ADR-0017 amendment row added at F8.9**(occurrence #8 + 3rd realized Plan B (c))

**PARTIAL PASS allowance**:
- F1.5a mobile hotspot install fail → fallback to PyPI (a) attempt → 若仍 fail,PARTIAL PASS rationale 入 retro,F1 defer Wave C1.5 + use `EnvVarProvider` only for Wave C1(`/admin/connections/*/rotate-secret` returns 501 + Tier 2 message);scope cuts F1.3 + F1.4 partial
- F5.x per-tab user-eye verify fail spotted mid-phase → STOP per CLAUDE.md §5.7 H7 + propose 處理方案(per W22 D6 / D7 / D8 user-eye verify correction precedent;NEVER smoke-user-deferred for fidelity)

---

## §4 Risks

| Risk | Mitigation | Status |
|---|---|---|
| **R-W24-1** Key Vault SDK install via mobile hotspot fail | Fallback PyPI (a) attempt;若仍 fail → PARTIAL PASS per §3 + F1.5b deferred Wave C1.5 + EnvVarProvider-only fallback | 🟡 active(mitigation ready) |
| **R-W24-2** F2 9-provider schema design-time scope creep | Schema sketched 1 round per provider at F2 active-flip;若 1 provider schema explodes mid-implementation → split out to dedicated PR | 🟡 active |
| **R-W24-3** F5 mockup-fidelity drift inherited W22 anti-pattern | Per-tab H7 self-verify gate(no「smoke-user-deferred」for fidelity per W21+W22+W23 retro);CSS-first pivot per CLAUDE.md v1.9 §3.2;mockup HTTP server 8080 side-by-side workflow per W22 standard | 🟡 active |
| **R-W24-4** Postgres migration order brittle | `admin_provider_configs` + `admin_identity_config` + `audit_log` 3 NEW tables addative;idempotent `ALTER TABLE ADD COLUMN IF NOT EXISTS` per W17 F1 pattern;若有 dep cycle → migration order in F2/F3/F4 plan §7 changelog | 🟢 mitigated |
| **R-W24-5** ADR-0027 Wave C2 / ADR-0025 Access tab future activation 衝突 W24-c1 design | Per ADR-0026 §Consequences:Identity & Auth Role mapping interplay with ADR-0027;Wave C1 5-tab Settings Identity & Auth tab 預 hook(read 3-role only;Power User disabled affordance)+ Wave C2 ADR-0027 expand role-edit + `groups`/`audit_log` Postgres tables additive | 🟢 mitigated |
| **R8 corp-proxy** | Plan B (c) mobile hotspot 首輪 per Chris pick + ADR-0017 amended occurrence #8 | 🟢 mitigated |

---

## §5 Component-Catalog references

| Cn | Touch | Scope |
|---|---|---|
| **C08** API Gateway | NEW `/admin/*` route group | F2 connections.py + F3 identity.py + F4 api_keys.py + usage_stats.py + admin/__init__.py |
| **C09** Admin Console UI | `/settings` page-level rebuild | F5 PageSettingsRich + 4 NEW sub-components + 3 NEW primitives + F6 apiClient.admin wiring |
| **C11** Identity & Access | persistence config | F3 admin_identity_config table + Entra/MSAL config CRUD |
| **C12** DevOps & Infra | NEW Key Vault SDK | F1 azure-keyvault-secrets + azure-identity install via mobile hotspot Plan B (c) + KEY_VAULT_URL env var |
| **C02** KB Manager | _no touch_ — preserved unchanged |
| **C01** / **C03** / **C04** / **C05** / **C06** / **C07** / **C10** / **C13** | _no touch_ — preserved unchanged |

---

## §6 Carry-overs to Wave C2 / W24b

- **W24b Wave C2 candidates**(per W19 F4 §3.6 SPLIT trigger):
  - ADR-0027 /users Tier 1.5 RBAC Option A full(`/users` 4-tab NET NEW + 6 NEW Postgres tables + Entra Graph SDK + ACL middleware + audit_log writes)
  - ADR-0025 Access tab activation(`kb_acl` table + per-KB ACL CRUD;依賴 Wave C2 RBAC backend)
  - W24-c1 Settings Identity & Auth Role mapping editable expansion(Wave C1 ship read-only 3-role;Wave C2 promote editable + Power User Tier 2 promote)
  - Settings Connections audit_log UI integration(Wave C1 ship audit row writes only;Wave C2 ship Audit log surface)
- **W24-c1 closeout 後 W24b/W25+ NOT pre-created** per CLAUDE.md §10 R1 rolling JIT
- **W16 F1-F4 Track A IT cred** — continues parallel external-blocked track,mock-auth default through Wave C2
- **CO17 R8 umbrella** — F1.5b psycopg + F3.5b RAGAs live-verify 仍 external-blocked

---

## §7 Changelog

| Day | Change | Reason |
|---|---|---|
| Day 0 2026-05-19 | Plan kickoff cascade — frontmatter / §0-§7 全部 landed `status: active` + Chris kickoff directive + 2 AskUserQuestion(Wave C1 scope + Key Vault SDK Plan B (c))confirmations | per CLAUDE.md §10 R1 rolling JIT + R5 ADR-before-implement + ADR-0026 Accepted scope |
| Day 1 cont 2026-05-19 | **F5 pre-active-flip 5-step grep audit recursive** surfaced **1 plan-text deviation + 1 F4 promotion**(per CLAUDE.md §10 R6):**(1)** F5.8 audit log preview surface plan-text "reads via `GET /admin/audit-log?limit=10`" → F4 deferred read endpoint to "F5/Wave C2"(plan-text-internal cross-reference) → **Promote** Wave C1 ship the read endpoint as F5 backend hook `audit_log.py` route + 6 pytest;UI consumes via `adminApi.listAuditLog(10)`;**(2)** F5.1 plan-text "rewrite thin v1 3-card structure" → W22 F8.1 page.tsx 已 mockup-faithful 對 `ekp-page-misc.jsx:308 PageSettings`(W22 D10 docstring) → **Adjust** to inline `ProfileTab` / `AppearanceTab` / `AccountTab` named functions inside 6-tab `PageSettingsRich` shell(preserve W22 F8.1 logic + Karpathy §1.3 surgical extend-not-rewrite)| Karpathy §1.1 think-before-coding surfaced these upfront;F5 ship 9 NEW files(`apiClient.admin.*` + 3 primitives + 4 settings/* components + audit_log backend hook)+ rewrite page.tsx + 6 NEW pytest;tsc + lint clean + [oklch=0 preserved through 6-tab structural rebuild |
| Day 1 cont 2026-05-19 | **F4 pre-active-flip 5-step grep audit recursive** surfaced **4 plan-text deviations**(per CLAUDE.md §10 R6):**(1)** F4.2 4-stat plan-text "7d window" → mockup line 749-752 actual = **24h window** → **Adjust** `UsageStats4Stat` shape `api_calls_24h + spend_today + spend_cap + spend_pct_used + token_throughput_tpm + rate_limit_hits_24h` per CLAUDE.md §5.7 H7 fidelity;**(2)** F4.3 plan-text "per-provider quota" → mockup actual = **per-deployment**(Azure OpenAI 4 deployments + 5 non-deployment providers 各 1 row = 10 rows seed)→ **Adjust** `OutgoingQuotaList` flatten matrix;**(3)** F4.4 plan-text "PATCH TPM/RPM cap" → Azure portal authoritative,EKP-level cap edit semantic 模糊;mockup line 760 actually editable knob = **alert threshold %**(50-95) → **Adjust** Wave C1 ship `PATCH /admin/api-keys/outgoing/{p}/{d}/alert-threshold` only,TPM/RPM cap edit defer Wave B+;add `alert_threshold_pct: int = 80` to `ProviderDeployment` JSONB backward-compat additive + `update_deployment_alert_threshold` Protocol method;**(4)** F4.8 audit_log Wave C1 = **write-only** with 3-file split storage/postgres/factory mirror F2/F3 + 6 endpoint hook(F2 patch/test/rotate + F3 patch × 5 sub-resource + F4 patch alert-threshold);**graceful no-op when backend None** preserves F2/F3 test path;read endpoint defer F5/Wave C2 SettingsAccount surface | Karpathy §1.1 think-before-coding surfaced these mismatches upfront via mockup line 744-823 + R6 recursive grep audit;single-pass implementation no friction post-adjust |
| Day 1 cont 2026-05-19 | **F3 pre-active-flip 5-step grep audit recursive** surfaced **3 plan-text deviations**(per CLAUDE.md §10 R6 + W22 D1+D8+D9 anti-pattern catalog `feedback_design_fidelity.md`):**(1)** `PATCH /admin/identity/roles` plan-text "update Entra group → EKP role mapping" → mockup actually shows list-of-rows → **Adjust to list-replace semantic**(individual mapping CRUD defer Wave C2 ADR-0027 RBAC infra);**(2)** Tenant fields plan-text "tenant_id + display_name + verified_domains" → mockup actually surfaces `tenant_id + tenant_domain + cloud_instance + authority_url(disabled/derived)` → **Adjust schema** to drop `display_name + verified_domains`(`verified_domains` defer Wave C2 Graph SDK sync)+ derive `authority_url` server-side from `tenant_id + cloud_instance` per 3 cloud instance map;**(3)** Postgres table plan-text "single-row config(sub_resource_key PK + config_json + updated_at + updated_by)" → **Adjust to per-sub-resource row pattern** = 5 rows seeded(`sub_resource TEXT PK + config JSONB + updated_at + updated_by NULL`)— audit_log per-row writes simpler at Wave C2;F1.6 kept `updated_by NULL` for audit_log preview shape forward-compat | Karpathy §1.1 think-before-coding surfaced these mismatches upfront via mockup line 528-723 + R6 recursive grep audit before implementation;single-pass implementation no friction post-adjust |

---

**End of W24-wave-c1 plan(version 1.0 kickoff)**
