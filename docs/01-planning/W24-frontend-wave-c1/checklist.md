---
phase: W24-frontend-wave-c1
plan_ref: ./plan.md
status: active                      # active | closed
last_updated: 2026-05-19
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

- [ ] **F2.1** `backend/api/routes/admin/__init__.py` + `backend/api/routes/admin/connections.py` NEW
- [ ] **F2.2** 9-provider Pydantic schemas(`ProviderConfig` + `ProviderDeployment` + `ProviderUsageStats`)
- [ ] **F2.3** `GET /admin/connections` → list[ProviderSummary]
- [ ] **F2.4** `GET /admin/connections/{provider_id}` → ProviderConfig full(secret masked)
- [ ] **F2.5** `PATCH /admin/connections/{provider_id}` → update non-secret fields + Postgres write + audit_log row
- [ ] **F2.6** `POST /admin/connections/{provider_id}/test` → per-provider lightweight connection probe → `{status, latency_ms, detail}`
- [ ] **F2.7** `POST /admin/connections/{provider_id}/rotate-secret` → KeyVaultProvider.rotate_secret + last_rotated_at update + audit_log row
- [ ] **F2.8** NEW Postgres table `admin_provider_configs` + idempotent ALTER migration
- [ ] **F2.9** Tests `backend/tests/api/admin/test_connections.py` NEW(~30+ pytest cases)
- [ ] **F2.10** mypy strict + pytest pass

## F3 — `/admin/identity/*` endpoint group

- [ ] **F3.1** `backend/api/routes/admin/identity.py` NEW(5 sub-resources)
- [ ] **F3.2** Pydantic schemas — Entra / App / MSAL / Roles / Policy
- [ ] **F3.3** `GET /admin/identity` → consolidated state(secret masked)
- [ ] **F3.4** `PATCH /admin/identity/tenant`
- [ ] **F3.5** `PATCH /admin/identity/app_registration`(client_secret rotation via KeyVaultProvider)
- [ ] **F3.6** `PATCH /admin/identity/msal` → Postgres `admin_identity_config` write
- [ ] **F3.7** `PATCH /admin/identity/roles`(3 active + Power User disabled affordance fallback)
- [ ] **F3.8** `PATCH /admin/identity/policy`
- [ ] **F3.9** NEW Postgres table `admin_identity_config`
- [ ] **F3.10** Tests `backend/tests/api/admin/test_identity.py` NEW(~15 pytest cases)
- [ ] **F3.11** mypy strict + pytest pass

## F4 — `/admin/api-keys/*` + `/admin/usage-stats` endpoint group

- [ ] **F4.1** `backend/api/routes/admin/api_keys.py` + `usage_stats.py` NEW
- [ ] **F4.2** `GET /admin/usage-stats` → 4-stat strip + per-provider TPM/RPM(reads realtime_cost.py)
- [ ] **F4.3** `GET /admin/api-keys/outgoing` → list of per-provider quotas
- [ ] **F4.4** `PATCH /admin/api-keys/outgoing/{provider_id}` → quota config update
- [ ] **F4.5** `GET /admin/api-keys/incoming` → 永遠 `{enabled: false}` disabled affordance shape
- [ ] **F4.6** Tests NEW(~12 pytest cases)
- [ ] **F4.7** mypy strict + pytest pass
- [ ] **F4.8** `audit_log` row writes preview(Postgres table NEW additive — Tier 2 expansion via ADR-0027 Wave C2)

## F5 — Frontend `/settings` 6-tab `PageSettingsRich` rebuild

- [ ] **F5.1** `frontend/app/(app)/settings/page.tsx` rewrite — replace thin v1 with 6-tab PageSettingsRich(preserve W18 LoginGate + (app)/ + AppShell)
- [ ] **F5.2** 6-tab navigation .tabs CSS class + `?tab=` deep link
- [ ] **F5.3** `<SettingsProfile>` extend W22 F8.1 thin(Display name PATCH + Email read-only + Locale Tier 2 disabled)
- [ ] **F5.4** `<SettingsAppearance>` preserve W22 F8.1 + add Density toggle(Tier 2 disabled)
- [ ] **F5.5** `<SettingsConnections>` NEW — 5 categories × 9 providers + 3 NEW primitives(ServiceCard + ApiKeyInput + DeploymentsTable)+ Test connection mutation per provider
- [ ] **F5.6** `<SettingsIdentity>` NEW — Entra tenant + App registration + MSAL + Role mapping(3+1 Tier 2 disabled)+ Sign-in policy
- [ ] **F5.7** `<SettingsApiKeys>` NEW — 4-stat usage strip + outgoing quotas + incoming disabled affordance
- [ ] **F5.8** `<SettingsAccount>` extend W22 F8.1 + Audit log preview surface + DangerZone(Delete account Tier 2 disabled)
- [ ] **F5.9** H7 per-tab verification gate(6 tabs × 7-item self-verify + user-eye verify)— NO「smoke-user-deferred」for fidelity
- [ ] **F5.10** `tsc --noEmit` exit 0 + `next lint` clean + `Grep '\[oklch'` = 0 preserved

## F6 — Frontend `apiClient.admin.*` wiring + form integration

- [ ] **F6.1** `frontend/lib/api/admin.ts` NEW — connections / identity / apiKeys / usageStats / auditLog methods
- [ ] **F6.2** TanStack Query mutation hooks per CRUD endpoint
- [ ] **F6.3** Form validation per provider schema(react-hook-form + zod per W20 F4 pattern)
- [ ] **F6.4** Optimistic UI per PATCH(rollback on error per TanStack Query pattern)
- [ ] **F6.5** ErrorBoundary integration per tab(per W14 CO_F4 pattern)
- [ ] **F6.6** `tsc --noEmit` exit 0 + `next lint` clean

## F7 — Tests(Vitest + Playwright)

- [ ] **F7.1** `frontend/tests/unit/settings-6tab.test.tsx` NEW(6-tab nav + Connections test + Identity save + ApiKeyInput interactions)
- [ ] **F7.2** `frontend/tests/e2e/app-shell-path.spec.ts` 加 `/settings` 6-tab assertions(per W23 F2 pattern)
- [ ] **F7.3** `frontend/tests/e2e/visual-baseline.spec.ts` 加 `/settings?tab=connections` baseline(first capture per W23 F2.3)
- [ ] **F7.4** Vitest stats `pnpm test:unit` ≥ 32 pass(W23 baseline 28 → +4 IMPROVED)
- [ ] **F7.5** Playwright stats ≥ 24/24 pass(W23 baseline 22/22 → +2 IMPROVED)
- [ ] **F7.6** Backend pytest:全 regression preserved + F2/F3/F4 new ~60+ = ~765+ pass

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
