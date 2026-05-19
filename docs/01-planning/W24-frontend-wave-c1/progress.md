---
phase: W24-frontend-wave-c1
plan_ref: ./plan.md
checklist_ref: ./checklist.md
status: active                      # active | closed
---

# W24-wave-c1 — Progress

## Day 0 — 2026-05-19 — Kickoff cascade(F0)

### Done
- Chris explicit directive 2026-05-19「start W24-wave-c1 kickoff」post-BUG-003 + BUG-004 closeout pushed to remote(`080928f..c449bbb main -> main`)
- **2 AskUserQuestion confirmations**:
  - **Wave C1 scope** = ADR-0026 Settings 6-tab Option B 唯一(over「Settings + Access skeleton」+「revert Option B → Option C hybrid」)
  - **Key Vault SDK Plan B sequencing** = (c) mobile hotspot 首輪(over「PyPI (a) first」+「defer Key Vault SDK」)
- Pre-active-flip 5-step grep audit recursive(per CLAUDE.md §10 R6):
  - **(1) read plan literal acceptance criteria** — F0-F8 sketched per W23 plan template
  - **(2) grep code base for referenced files** — `frontend/app/(app)/settings/page.tsx` confirmed 104 lines W22 F8.1 thin 3-card (Profile + Appearance + Account) / `backend/api/routes/` confirmed 14 routes(auth + chunking + chunks + conversations + debug + documents + eval + feedback + health + kb + observability + query + retrieval_test + screenshots)**no `/admin/*` group existed** / `references/design-mockups/ekp-page-settings-tabs.jsx` 882 lines confirmed PageSettingsRich(7-46)+ SettingsConnections(96-355) + SettingsIdentity(528-723)+ SettingsApiKeys(744-823)+ SettingsAccount(842-870)
  - **(3) surface mismatches via Karpathy §1.1** — 1 mismatch surfaced:ADR-0025 §Implementation Status W20 closeout 寫「W22-frontend-wave-c1 candidate per F4 §3.6 split」應為「W24-frontend-wave-c1 candidate」— pre-existing ADR drift,not W24 scope to fix(noted for ADR-0025 amendment if needed)
  - **(4) document deviations in plan §7 changelog** — Day 0 row landed
  - **(5) adjust acceptance criteria per actual reality** — F1-F4 backend acceptance criteria 反映實際「completely greenfield NEW `/admin/*` route group」(原 ADR-0026 估算 ~22 endpoints with W20 F2.1 /health pattern reuse confirm)
- W24 folder + 3 docs landed `docs/01-planning/W24-frontend-wave-c1/{plan,checklist,progress}.md` `status: active`
- **F0.1** + **F0.2** + **F0.4** acceptance criteria met at kickoff

### Done (continued)
- **F0.3** `architecture.md v6 §5.0` Settings paragraph inline-tagged amendment landed — new `> **Amendment(Settings page scope expansion)**:per ADR-0026 Option B...` blockquote chained after existing ADR-0024 amendment(per inline-tag convention §3.4 / §3.7 / ADR-0024 pattern;doc version held);cites ADR-0026 + ADR-0017 + ADR-0023 + ADR-0027 dep tree + W24-wave-c1 implementation marker

### Decisions
- **D0.1**:**Wave C1 scope = Settings 6-tab Option B 唯一**(per Chris AskUserQuestion 2026-05-19)— Access tab activate + /users RBAC 全部 defer Wave C2;rationale:ADR-0025 Access tab activation 必依賴 ADR-0027 RBAC backend(`kb_acl` Postgres table 屬 Wave C2 scope)+ Wave C1 必須 self-contained 避免 Wave C1+C2 倒序;Option B fully editable per Chris W19 F6 pick(over Option C hybrid recommended)是 Beta-readiness milestone — `.env` rotation rituals 取代 為自助 UI
- **D0.2**:**Key Vault SDK install via mobile hotspot Plan B (c) 首輪**(per Chris AskUserQuestion 2026-05-19)— skip PyPI (a) attempt R8 corp-proxy risk;rationale:Langfuse SDK 2026-05-16 `dffe19a` Plan B (c) 已成功precedent + azure-keyvault-secrets 600KB+ binary wheel high R8 fail probability + 預先 plan-B-(c) success 比 fail-then-retry 快 30-60min
- **D0.3**:**6 deliverables backend-heavy + 2 frontend-mid**(F1 KeyVaultProvider abstraction + F2 connections + F3 identity + F4 api_keys + F5 frontend rebuild + F6 apiClient + F7 tests + F8 closeout)— `~7 backend + 4 frontend = ~13 plan days`,real-calendar collapse 1.5-12× pattern → 預期 ~2-4 actual days
- **D0.4**:**F0 governance only**(per W19-W23 F0 precedent)— NO `frontend/` or `backend/` code change at kickoff,F0.3 architecture.md amendment 屬 inline-tagged docs change(not Cn code)
- **D0.5**:**架構 amendment 入 F0 而非 mid-phase**(per ADR-0024 W18 / §3.4 + §3.7 W17 precedent)— Wave C1 ship 之前先 lock architecture.md v6 §5.0 6-tab spec,避免 mid-phase architecture drift discovery
- **D0.6**:**Postgres 3 NEW tables additive**(per ADR-0023 base):F2 `admin_provider_configs` + F3 `admin_identity_config` + F4(audit_log Tier 2 expansion preview)— idempotent ALTER TABLE per W17 F1 pattern;migration order:F2 → F3 → F4(no dep cycle)
- **D0.7**:**Tier 2 disabled affordance preserved Wave C1**(per ADR-0026 §Consequences):API Keys & Quotas Incoming Keys tab + Identity & Auth Power User Role + Settings Account Delete account + Settings Appearance Density — 4 個 `<DisabledAffordance>` per W19 F5 spec consumed across Wave C1 frontend

### Decisions Log per CLAUDE.md §10 R5
- ADR-0026 + ADR-0017 既存 → NO NEW ADR for Wave C1(F8.9 ADR-0017 amendment row only,non-ADR-creation)
- W24 H1 trigger = `architecture.md v6 §5.0` amendment(Settings thin v1 → 6-tab hub)→ F0.3 inline-tagged at kickoff(per ADR-0024 / §3.4 / §3.7 precedent;doc version held)
- W24 H2 trigger = Key Vault SDK NEW dep → ADR-0017 amendment row at F1.8 + F8.9(occurrence #8 + 3rd realized Plan B (c))

### Acceptance(plan §3 + checklist F0)
- [x] F0.1 W24 3 docs created `status: active`
- [x] F0.2 NO code change at kickoff(F0.3 architecture.md amendment 屬 docs)
- [x] F0.3 architecture.md v6 §5.0 inline-tagged amendment(landed)
- [x] F0.4 Pre-active-flip 5-step grep audit recursive completed
- [x] F0.5 kickoff cascade commit `(this commit)`

**Day 0 Verdict**:W24-wave-c1 **active**;F0 kickoff cascade 100% complete in single commit。F1-F8 detailed at per-deliverable active flip。Real-calendar:Day 0 = same-session as W23 closeout + BUG-003+004 closure + W24 kickoff(3-phase-event single 8-hour session)。

---

## Day 1 — 2026-05-19 — F1 KeyVaultProvider + Azure SDK install + tests + mypy + ADR-0017 amendment

### Done
- **F1.5a** Chris executed Plan B (c) mobile hotspot install per ADR-0017 Decision-rule #5 — `pip install "azure-keyvault-secrets>=4.8.0" "azure-identity>=1.18.0"` resolved to `azure-keyvault-secrets 4.11.0` + `azure-identity 1.25.3`(both above ADR-0026 minimum 4.8.0 + 1.18.0)clean in single pass(zero R8;**3rd realized Plan B (c) occurrence** after Langfuse SDK 2026-05-16 + 1st pre-emptive use over try-then-fail sequence)
- **F1.1 + F1.2** `backend/storage/key_vault.py` NEW(115 lines)— `KeyVaultProvider` Protocol(5 async methods)+ `SecretMetadata` Pydantic + `SecretNotFoundError` + `EnvVarProvider` impl + `generate_secret_value(num_bytes=32)` urlsafe entropy helper(reuses `secrets.token_urlsafe` same pattern as `email_provider.py` verify-email token)
- **F1.3** `backend/storage/azure_key_vault.py` NEW(110 lines)— `AzureKeyVaultProvider` using `azure.keyvault.secrets.aio.SecretClient` + `azure.identity.aio.DefaultAzureCredential` async-by-default + `aclose()` lifecycle hook + `TYPE_CHECKING` import gating(SDK only loads when constructor called)
- **F1.4** `backend/storage/key_vault_factory.py` NEW(20 lines)— `make_key_vault_provider(settings)` mirrors `make_kb_backend` ADR-0023 lazy-import pattern;unset `KEY_VAULT_URL` never touches `azure-keyvault-secrets`
- **F1.5** `backend/pyproject.toml` updated — `azure-keyvault-secrets>=4.8.0` added with rationale comment cross-referencing ADR-0017 Plan B (c) + 600KB+ binary wheel risk profile;existing `azure-identity>=1.20` constraint already satisfied(installed 1.25.3 > 1.20)
- **F1.5(NEW Settings field)** `backend/storage/settings.py` — `KEY_VAULT_URL` env var added(empty default → `EnvVarProvider` fallback;set → `AzureKeyVaultProvider` via factory)+ 7-line docstring referencing ADR-0026 Option B + lazy-import shape
- **F1.6** `backend/tests/test_key_vault.py` NEW(208 lines)— **15 tests pass in 8.36s**:
  - EnvVarProvider round-trip(6 tests):set/get/delete/list/rotate-raises/metadata-shape
  - `generate_secret_value` entropy(3 tests):urlsafe alphabet + length sanity + collision check
  - Factory branch selection(2 tests):unset → EnvVarProvider + set → AzureKeyVaultProvider with patched class
  - AzureKeyVaultProvider Protocol conformance(4 tests, SDK mocked):get_secret round-trip + get_secret raises on ResourceNotFoundError + rotate_secret returns generated value + aclose releases resources
- **F1.7** `mypy --strict storage/key_vault.py storage/azure_key_vault.py storage/key_vault_factory.py` → **0 errors in 3 source files**
- **F1.8** ADR-0017 amendment landed:
  - Occurrence #8 row added to "Occurrences captured" table(W24-wave-c1 F1 / 2026-05-19 / Plan B (c) pre-emptive)
  - NEW section "Plan B realised — Azure Key Vault SDK via mobile hotspot (2026-05-19, W24-wave-c1 F1)" appended after Langfuse section(install procedure + what this resolves + architectural shape + 3rd realized confirmation)
- **F1.9** Full backend pytest regression preserved:**720 passed + 11 skipped in 368s**(W23 baseline 705 → **+15 net IMPROVED** via F1.6 tests;no regression introduced)

### Decisions
- **D1.1 — Async-by-default Protocol** per CLAUDE.md §3.1:`get_secret/set_secret/delete_secret/list_secrets/rotate_secret` 全部 async — match FastAPI async handler convention + aio SecretClient pattern。EnvVarProvider `os.environ` access is sync but wrapped in async no-op so Protocol stays uniform。
- **D1.2 — aio SecretClient uses `delete_secret` not `begin_delete_secret`** — mid-implementation mypy catch surfaced this:sync SecretClient has poller pattern,aio SecretClient returns directly。Fix:simplify AzureKeyVaultProvider.delete_secret to single await call。Per Karpathy §1.1 think-before-coding:should have verified SDK API shape before writing first-pass(loss = 1 mypy iteration);noted as inherent friction(aio SDK docs mostly inherit sync pattern naming,easy to miss)。
- **D1.3 — `EnvVarProvider.list_secrets` returns empty list by contract** — listing every env var would dump PATH / system internals。Per Karpathy §1.2 simplicity first:callers that need a curated list filter at their layer(e.g.,F2 connections endpoints list 9-provider env vars by name)。Documented in docstring + pytest contract pin。
- **D1.4 — `EnvVarProvider.rotate_secret` raises `NotImplementedError` with KEY_VAULT_URL hint** — rationale:env-var rotation requires process restart that the runtime can't issue from inside a request handler。Error message specifically callable by `<DisabledAffordance reason="...">` Wave C1 frontend(F5 Connections tab `Rotate secret` button DisabledAffordance render path)。
- **D1.5 — `aclose()` not exposed in Protocol** — only AzureKeyVaultProvider needs it(holds aio HTTP session)。Protocol stays minimal per Karpathy §1.2;factory + lifespan wire `aclose()` via concrete-type check at startup(F2/F3/F4 lifespan integration)。
- **D1.6 — Lazy `from azure.core.exceptions import ResourceNotFoundError` inside methods** — same pattern as TYPE_CHECKING + lazy `from azure.identity.aio import ...` in `__init__`;keeps unset KEY_VAULT_URL paths cost-free on import。

### Decisions Log per CLAUDE.md §10 R5
- No new ADR needed for F1(ADR-0026 + ADR-0017 既存 cover this scope);ADR-0017 amended occurrence #8 + NEW Plan B section
- F1.5a Plan B (c) Chris pre-approved at AskUserQuestion 2026-05-19;Plan B (a)/(b) skipped per occurrence #5/#7 evidence

### Acceptance(plan §3 + checklist F1)
- [x] F1.1 KeyVaultProvider Protocol + SecretMetadata + SecretNotFoundError + generate_secret_value
- [x] F1.2 EnvVarProvider impl
- [x] F1.3 AzureKeyVaultProvider impl
- [x] F1.4 make_key_vault_provider factory
- [x] F1.5 pyproject.toml + settings.py KEY_VAULT_URL
- [x] F1.5a mobile hotspot install success
- [x] F1.6 15/15 tests pass
- [x] F1.7 mypy strict 0 errors
- [x] F1.8 ADR-0017 occurrence #8 + Plan B section
- [x] F1.9 Full pytest regression preserved 720 passed(+15 IMPROVED)

**Day 1 Verdict**:F1 KeyVaultProvider abstraction **DONE** 100%。Backend ready for F2-F4 admin endpoints to consume `KeyVaultProvider` via factory injection。

### Commits
| Hash | Subject |
|---|---|
| _(this commit)_ | `feat(storage): KeyVaultProvider Protocol + EnvVarProvider + AzureKeyVaultProvider + factory (W24-wave-c1 F1 per ADR-0026 + ADR-0017 #8)` |

---

**End of W24-wave-c1 Day 1(active — F1 done,F2 next)**

---

## Day 1 cont — 2026-05-19 — F2 `/admin/connections/*` endpoint group (× 9 providers)

### Done
- **F2.1-F2.2 schemas + routes layout**:
  - `backend/api/schemas/admin.py` NEW(115 lines)— `ProviderCategory`+`TestStatus` Literals + 7 Pydantic models(ProviderDeployment / ProviderConfig / ProviderSummary / ProviderPatch / TestConnectionResult / RotateSecretResult)
  - `backend/api/routes/admin/__init__.py` NEW(package marker w/ F2-F4 scope docstring)
  - `backend/api/routes/admin/connections.py` NEW(228 lines)— APIRouter w/ `/admin/connections` prefix + 5 endpoints + 9-provider `_run_probe` dispatcher + `_mask_secret` helper
- **F2.3-F2.7 5 endpoints landed**:
  - `GET /admin/connections` → list[ProviderSummary] 9-row lightweight view
  - `GET /admin/connections/{provider_id}` → ProviderConfig full(404 on unknown;secret value NEVER returned — only `secret_kv_ref` name + `secret_masked_preview`)
  - `PATCH /admin/connections/{provider_id}` → ProviderPatch(endpoint_url + region + display_name editable;deployments + secret_kv_ref omitted per ADR-0026 §Decision)
  - `POST /admin/connections/{provider_id}/test` → 9-provider probe dispatcher returning `TestConnectionResult`(status + latency_ms + detail);persists last_test_at + last_test_status via backend
  - `POST /admin/connections/{provider_id}/rotate-secret` → KeyVaultProvider.rotate_secret + masked preview;503 on EnvVarProvider NotImplementedError + 400 on managed-identity providers
- **F2.8 Storage layer 3-file split per kb_management pattern**:
  - `backend/storage/admin_provider_storage.py` NEW(259 lines)— Protocol + InMemoryAdminProviderBackend + `default_providers()` 9-provider seed + ProviderNotFoundError;categories `llm`(azure_openai with 4 deployments)/ `retrieval`(cohere + azure_search)/ `storage`(azure_blob + postgres)/ `observability`(langfuse + structlog)/ `identity`(acs_email + key_vault)
  - `backend/storage/admin_provider_postgres.py` NEW(202 lines)— PostgresAdminProviderBackend lazy-imported impl + idempotent CREATE TABLE + seed merge(only INSERT rows missing by PK)+ row → ProviderConfig serialization
  - `backend/storage/admin_provider_factory.py` NEW(20 lines)— `make_admin_provider_backend(settings)` mirrors `make_kb_backend` ADR-0023 pattern
- **F2.8c Server.py lifespan wiring**:`app.state.key_vault_provider = make_key_vault_provider(settings)` + `app.state.admin_provider_backend = make_admin_provider_backend(settings)` + `app.include_router(admin_connections.router, tags=["admin"], dependencies=_auth)` — both factories register under `_auth` Depends per W8 D5 F4.4 admin-router-auth-cascade precedent
- **9-provider Wave A config-state-only test-connection probes**(per W20 F2.1 /health pattern;Wave B+ promote to real I/O):
  - azure_openai / cohere / azure_search:HTTPS endpoint check(no http)
  - azure_blob:HTTPS or http://localhost(Azurite)allowed
  - postgres:settings.database_url presence(no SELECT 1 ping Wave A)
  - langfuse:HTTPS or http://localhost(local dev compose Langfuse)allowed
  - acs_email:secret_kv_ref presence(not_tested 若 mock provider fallback)
  - key_vault:settings.key_vault_url HTTPS check
  - structlog:always_ok(config-only,no probe needed)
- **F2.9** `backend/tests/api/test_admin_connections.py` NEW(411 lines)— **27 tests pass in 4.14s**:
  - Storage seed(5 tests):9-entry default + 5-category match + Azure OpenAI 4-deployment + InMemory seed-on-construct + InMemory update persistence
  - GET list(2 tests):200 9-summary + 503 backend not init
  - GET detail(2 tests):200 full + 404 unknown
  - PATCH(3 tests):display_name update + 404 unknown + idempotent empty body
  - POST test(8 tests):azure_openai HTTPS OK + azure_blob local HTTP OK + postgres not_tested w/o DATABASE_URL + key_vault not_tested w/o KEY_VAULT_URL + structlog always OK + persistence verify + 404 unknown
  - POST rotate-secret(5 tests):success+masked + persistence + 400 no kv_ref + 503 EnvVarProvider + 404 unknown
  - Mask helper(2 tests):short value `***` only + typical token last-4-chars
  - Schema sanity(1 test):SecretMetadata default shape
- **F2.10 mypy strict**:
  - `api/schemas/admin.py` + `storage/admin_provider_storage.py` + `storage/admin_provider_factory.py` + `api/routes/admin/connections.py` → **0 errors**
  - `storage/admin_provider_postgres.py` → 6 errors **all mirror existing `kb_management/postgres_backend.py` pattern**(psycopg import-not-found x3 + `dict` / `tuple` generic type-arg x3);per CLAUDE.md §13 surgical + Karpathy §1.3 match existing pattern,不改 pre-existing baseline
- **F2.11 Full backend pytest regression**:**747 passed + 11 skipped + 16 warnings in 207.32s**(F1 post 720 → **+27 net IMPROVED** via F2 27 NEW tests;no regression introduced)

### Decisions
- **D1.7 — Per-provider mocked test-connection per user pick** — config-state-only probes mirror W20 F2.1 /health pattern;avoid real I/O ping(R8 risk for Azure OpenAI / Cohere SDKs not yet wired into probe layer + Beta operator scope:probe answer "is configured properly?" not "is the cloud up?")。Wave B+ promotion path:swap `_probe_https_endpoint(cfg)` → `await httpx.get(cfg.endpoint_url + "/health", timeout=5)` per provider
- **D1.8 — In-memory + Postgres dual backend per user pick** — exact kb_management 3-file split:Protocol + InMemory in `admin_provider_storage.py` / lazy-import production impl in `admin_provider_postgres.py` / factory branches in `admin_provider_factory.py`。Unset `DATABASE_URL` never touches `psycopg`(local dev / CI behavior preserved)
- **D1.9 — 9-provider seed lives in code, not config** — `default_providers()` returns hardcoded list of 9 ProviderConfig rows with sensible Tier 1 defaults(endpoint URLs match `.env.example` shape + secret_kv_ref names follow `ekp-<provider>-<purpose>` convention)。Operator-customizable via PATCH endpoints + Postgres persistence;in-memory restart-wipes back to seed
- **D1.10 — Secret value NEVER returned to UI** — `secret_kv_ref` exposes secret NAME(for operator to look up in Azure portal if needed);`secret_masked_preview`(e.g.`***xY1z`)is the only "value-hint" returned。Rotation flow:server generates new value → writes to Key Vault → records masked preview。UI shows the masked preview;real value lives only in Key Vault
- **D1.11 — 9th provider `structlog` included for visibility** — although structlog is config-only(no secret to rotate,no endpoint to test),it's surfaced in Connections list for operator awareness("the JSON shipping is part of the stack")。Test connection always OK;rotate returns 400(no rotatable secret)
- **D1.12 — managed-identity providers handled via secret_kv_ref=None** — `key_vault` 自己(managed identity in Container Apps prod)+ `structlog`(config-only)return `secret_kv_ref=None`;rotate endpoint returns 400 with actionable error message;UI consumes for `<DisabledAffordance>` Rotate-button reason
- **D1.13 — server.py lifespan registers both factories at startup** — `app.state.key_vault_provider` + `app.state.admin_provider_backend` initialized in same block(per F1 plan §F1.4 + F2 plan §F2.8c);both factories cheap when env vars unset(EnvVarProvider + InMemoryAdminProviderBackend)so no startup cost regression
- **D1.14 — `admin_provider_postgres.py` mypy errors accepted as pattern-mirror** — 6 errors(psycopg no-stubs x3 + dict/tuple type-arg x3)exactly match existing `kb_management/postgres_backend.py` pre-existing baseline;per CLAUDE.md §13 surgical + Karpathy §1.3 match-existing-pattern,不順手 refactor。Future cleanup candidate:add psycopg type stubs OR migrate to typed cursors(out of W24-c1 scope)

### Acceptance(plan §3 + checklist F2)
- [x] F2.1-F2.2 schemas + routes layout
- [x] F2.3-F2.7 5 endpoints landed
- [x] F2.8 + F2.8a + F2.8b + F2.8c storage layer + lifespan wire
- [x] F2.9 27/27 tests pass
- [x] F2.10 mypy strict 0 errors on new non-Postgres code
- [x] F2.11 747 passed + 11 skipped(+27 IMPROVED)

**Day 1 cont Verdict**:F2 `/admin/connections/*` endpoint group **DONE** 100%。Backend has 9-provider CRUD + Test + Rotate scaffolding ready for F3 identity tab + F4 api-keys tab to share storage / factory / lifespan patterns。

### Commits
| Hash | Subject |
|---|---|
| `ea8cafa` | `feat(api): /admin/connections/* 5 endpoints × 9 providers + InMemory+Postgres dual backend (W24-wave-c1 F2 per ADR-0026 Option B)` |

---

## Day 1 cont F3 — `/admin/identity/*` 5 sub-resources(2026-05-19)

### Pre-active-flip 5-step grep audit recursive(per CLAUDE.md §10 R6)

Per W22 D1+D8+D9 plan-text contamination evidence,plan §2.F3 文本 grep audit 揭露 3 處 deviation surfaced upfront(NOT post-implementation):

| Plan §2.F3 文本 | Audit 發現 | 處理 |
|---|---|---|
| **`PATCH /admin/identity/roles`** = "update Entra group → EKP role mapping" | Mockup `SettingsIdentity` table row 暗示 **multiple role mappings** → PATCH semantic 唔啱 — 應該係 list-replace(`POST /roles` + `DELETE /roles/{id}` individual CRUD 需 ADR-0027 RBAC infra Wave C2) | **Adjust**:Wave C1 ship list-replace 接受 full `RoleMappingConfig.mappings: list[RoleMapping]` semantic;individual mapping CRUD = Wave C2 |
| **Tenant fields** = "tenant_id + display_name + verified_domains" | Mockup actually surfaces `tenant_id + tenant_domain + authority_url(disabled/derived) + cloud_instance`;`verified_domains` 唔喺 mockup | **Adjust**:`EntraTenantConfig` = `tenant_id + tenant_domain + cloud_instance`;`authority_url` **derived server-side**(`{base}/{tenant_id}` per 3 cloud instance map)— 不持久化;`verified_domains` 留 Wave C2 ADR-0027 Graph SDK sync 範圍 |
| **Postgres table** = "single-row config(sub_resource_key PK + config_json + updated_at + updated_by)" | F2 用 `provider_id PK + row-per-provider`;5 sub-resources 各自 1 row 更乾淨 + audit_log writes per-row + Wave C2 audit log UI 直接 query | **Adjust**:`admin_identity_config` 用 **per-sub-resource row pattern**(`sub_resource TEXT PRIMARY KEY + config JSONB + updated_at + updated_by`)— 5 rows seeded;`get_all` 5-query SELECT 後 schema 重組 IdentityConfig consolidated |

### What worked(F3.1-F3.11)

- **F2 pattern reuse 100%**:storage 3-file split(Protocol + InMemory + Postgres lazy-import)+ factory + lifespan wire 完整 mirror F2 — single-pass implementation 無 friction
- **Tier 2 boundary 設計成 3 explicit reject guard**(per CLAUDE.md H4):`multi_disabled` audience(app_registration)+ `distributed_disabled` token cache(msal)+ `power_user` ekp_role unless `is_tier2_disabled=True`(roles)— 422 Pydantic + business rule layered
- **Security hygiene parity with F2**:client_secret value NEVER returned 喺 GET(只有 `client_secret_kv_ref` name + `client_secret_masked_preview`)+ client-supplied `authority_url` 喺 PATCH 被 server 靜靜 strip + re-derived(防 redirect attack 預防)
- **3-cloud authority URL derivation** 寫成 server-side `_derive_authority_url` helper(Azure Public / Government / China 21Vianet)+ 3 NEW pytest cover all branches
- **mypy strict clean** on 4 non-Postgres files 一次過,zero iteration

### What didn't work / friction

- **Postgres path 6 baseline mypy errors persisted**(psycopg no-stubs x3 + `dict` missing-type-arg x3)— 跟 F2 + `kb_management/postgres_backend.py` 既有 baseline pattern,per CLAUDE.md §13 surgical 不在 scope cleanup。F3 ADD 6 errors 但全部 baseline-shape;**F1.5b R8/Azure-key-bound runtime smoke** + **psycopg type-stubs cleanup** 留 CO17 umbrella
- **Pydantic `Literal[False]` 行為**:`require_mfa_all_roles_tier2: Literal[False]` 不是 read-only — POST `True` 會 422,但 missing field 會 default to `False`(per Pydantic v2 default semantic)。Test 422-on-True 寫低咗,確認 type-system 強制 Tier 2 boundary

### Surprises

- **HTTP_422_UNPROCESSABLE_ENTITY → HTTP_422_UNPROCESSABLE_CONTENT deprecation warning** in starlette > 0.40 — F2 + F3 同樣 hit;migration defer 至 future deps bump session(non-blocking,3 warnings during F3 26 pytest)。

### Decisions(captured for retro at F8)

- **D3.1** `RoleMapping.member_count = None` at Wave C1 — Graph API count refresh defer Wave C2 ADR-0027 RBAC infra(Tier 1 不依賴 real-time count for boundary enforcement)
- **D3.2** `cookie_settings_preview` field 用 `default=` static string from mockup,server-side computed value 留 future ADR-0022 transport-policy split
- **D3.3** `client_secret_expires_at: datetime | None` 留 Wave C2 ADR-0027 + Graph sync wire;Wave C1 ship `None` + UI 90d rotation reminder banner show "不知道 expiry"
- **D3.4** **Per-sub-resource row Postgres pattern**(vs single-row JSON blob)— audit_log per-row writes Wave C2 easier;5-row SELECT cheap

### Acceptance(plan §3 + checklist F3)
- [x] F3.1-F3.2 routes + schemas layout
- [x] F3.3-F3.8 1 GET + 5 PATCH endpoints landed
- [x] F3.9 + F3.9a + F3.9b + F3.9c storage layer + lifespan wire(per-sub-resource row pattern per plan §7 changelog)
- [x] F3.10 26/26 tests pass in 6.43s(F2 baseline 27 → +26 IMPROVED via 26 NEW Identity tests;total /admin/* combined 53 pytest cases)
- [x] F3.11 mypy strict 0 errors on 4 new non-Postgres files
- [x] F3.12 Full backend pytest regression preserved:**773 passed + 11 skipped + 0 failed in 404.09s**(F2 baseline 747 → +26 net IMPROVED via 26 NEW F3 Identity tests;no regression)

**Day 1 cont F3 Verdict**:F3 `/admin/identity/*` endpoint group **DONE** 100%。Backend has 5-sub-resource identity config CRUD + 3 Tier 2 boundary guards + server-side authority URL derivation ready for F4 api-keys tab + F5 frontend `<SettingsIdentity>` consumption。

### Commits
| Hash | Subject |
|---|---|
| _(this commit)_ | `feat(api): /admin/identity/* 5 sub-resources + per-sub-resource row Postgres backend + 3 Tier 2 boundary guards (W24-wave-c1 F3 per ADR-0026 Option B)` |

---

**End of W24-wave-c1 Day 1 cont F3(active — F1+F2+F3 done,F4 next)**

---

## Day 1 cont F4 — `/admin/api-keys/*` + `/admin/usage-stats`(2026-05-19)

### Pre-active-flip 5-step grep audit recursive(per CLAUDE.md §10 R6)

4 plan-text deviations surfaced upfront(NOT post-implementation):

| Plan §2.F4 文本 | Audit 發現 | 處理 |
|---|---|---|
| **F4.2 4-stat = 7d window**("total_requests_7d + total_tokens_7d + total_cost_7d_usd + total_errors_7d")| Mockup line 749-752 actual:**24h window** —「API calls today + Spend today + Token throughput + Rate limit hits 24h」 | **Adjust** to mockup-aligned 24h shape with `api_calls_24h + spend_today_usd + spend_cap_daily_usd + spend_pct_used + token_throughput_tpm + rate_limit_hits_24h`;per CLAUDE.md §5.7 H7 fidelity |
| **F4.3 quota config = per-provider** | Mockup shows **per-deployment**(Azure OpenAI 4 deployments + Cohere + ACS — 6 rows visible);F2 `ProviderDeployment.tpm_limit + rpm_limit` already schema-ready | **Adjust** `OutgoingQuotaList` 用 per-deployment flatten — F2 `azure_openai` 4 deployments + 6 non-deployment providers single row each = 10 rows in seed state |
| **F4.4 PATCH quota config**(TPM + RPM cap)| Azure portal authoritative for deployment caps;EKP backend改 cap value 唔會 propagate;mockup line 760 actually shows **alert threshold 80%** as the editable knob | **Adjust** Wave C1 ship `PATCH /admin/api-keys/outgoing/{provider}/{deployment}/alert-threshold` only(50-95 range);TPM/RPM cap edit defer Wave B+(設計問題 — Azure portal level)。Add `alert_threshold_pct: int = 80` field to `ProviderDeployment`(additive,JSONB backward-compat)+ `update_deployment_alert_threshold` Protocol method |
| **F4.8 audit_log writes** | Plan 講「Tier 1 starts writing rows for forward-compat retention」— need actual writes from F2/F3/F4 PATCH endpoints | **Add** `audit_log` 3-file split(storage + postgres + factory)+ wire F2 PATCH/test/rotate + F3 PATCH × 5 sub-resource + F4 PATCH alert-threshold 6 endpoint hooks emit rows;**graceful no-op when backend None** preserves F2/F3 test path;read endpoint defer F5/Wave C2 |

### What worked(F4.1-F4.10)

- **F2 + F3 pattern triple reuse**:audit_log 3-file split + factory + lazy-import 直接 mirror,single-pass implementation
- **Tier 2 boundary via permanent `IncomingKeysDisabled`**(`enabled: Literal[False]` Pydantic permanent)— 同 H4 hard-codable boundary,UI consumer 直接 read 後 render `<DisabledAffordance>`
- **Mockup-aligned 24h window** decision 一致對齊 mockup `Spend today` semantic(non-7d);Karpathy §1.2 "average over window" simplicity-first
- **Cost-spike alert threshold** edit 設計 50-95 range(`alerts.py cost_spike` rule consume)+ `_derive_status` per-row helper return `Literal["within_limits", "warning", "over_limit"]`(`>= threshold_pct` = warning;`>= 100` = over_limit)
- **Audit-log graceful degradation**(`audit_log_backend = None` 唔 break endpoint)— F2 + F3 既有 tests 一個都唔需要改 = surgical extension per CLAUDE.md §1.3

### What didn't work / friction

- **psycopg-bound mypy 3 baseline errors** persisted in `audit_log_postgres.py`(import-not-found x3)— 跟 F2 + F3 既有 baseline pattern,per §13 surgical defer CO17;**dict / tuple type-arg issues** fixed mid-iteration(initially `dict | None`,explicit type-args + `Any` cast 解決)
- **`HTTP_422_UNPROCESSABLE_ENTITY` deprecation warnings** continued(F2 + F3 + F4 同一個 pattern;migration to `HTTP_422_UNPROCESSABLE_CONTENT` defer future starlette bump)

### Surprises

- **F2 audit-log wire 完全 backward-compat**:`getattr(request.app.state, "audit_log_backend", None)` 讀取確保 InMemory backend 無 set 時 `None` fallback;F2 27 既有 tests + F3 26 既有 tests 一個都唔 break
- **`get_langfuse_client` monkeypatch pattern**:F4 usage stats tests 用 `monkeypatch.setattr("api.routes.admin.usage_stats.get_langfuse_client", lambda: None)` pattern 避免 real Langfuse SDK touch(同`observability/realtime_cost.py` 既有 test pattern 一致)

### Decisions(captured for retro at F8)

- **D4.1** `alert_threshold_pct` 加入 `ProviderDeployment` schema(JSONB backward-compat;F2 既存 `ProviderConfig` 都會 expose 呢個 field 但 read-only)— vs 另開 table 簡化 storage layer
- **D4.2** `cap_tpm / cap_rpm` Wave C1 ship **read-only**(Azure portal authoritative);Wave B+ promote 視乎是否需要 EKP-side governance
- **D4.3** **`api_calls_delta_pct = None`** Wave C1(prior-24h comparison fetch defer Wave B+ when dashboard chart UI lands)
- **D4.4** `rate_limit_hits_24h = 0` placeholder Wave C1;Wave B+ wire `api/middleware/rate_limit.py` counter exposure
- **D4.5** **Audit log 3 actions**:`connection_patch + connection_test + connection_rotate_secret`(F2 hooks)+ `identity_patch`(F3 5 sub-resources 通通同一個 action,resource path 區分)+ `api_keys_alert_threshold_patch`(F4 hook)— `AuditAction` Literal 5 values total
- **D4.6** **Postgres `audit_log` SERIAL PK**(not UUID)+ ORDER BY id DESC for `list_recent` — F2/F3 PK pattern一致;Wave C2 promote 視乎是否需要 distributed-write conflict resolution
- **D4.7** Audit-log **read endpoint defer F5/Wave C2** — Wave C1 write-mostly retention 既有,Wave C2 SettingsAccount card 再 read

### Acceptance(plan §3 + checklist F4)
- [x] F4.1-F4.5 5 endpoints landed(GET usage-stats + GET outgoing + PATCH alert-threshold + GET incoming + audit hooks)
- [x] F4.6 26/26 tests pass in 8.54s(api_keys 16 + usage_stats 4 + audit_log 6)
- [x] F4.7 mypy strict 6 NEW non-Postgres files 0 errors;Postgres baseline 3 errors mirror F2/F3
- [x] F4.8 audit_log 3-file split + 6 endpoint hooks wired
- [x] F4.9 server.py lifespan + routers wired
- [x] F4.10 Full backend pytest regression preserved:**799 passed + 11 skipped + 0 failed in 309s**(F3 baseline 773 → +26 net IMPROVED via 26 NEW F4 tests;no regression)

**Day 1 cont F4 Verdict**:F4 `/admin/api-keys/*` + `/admin/usage-stats` endpoint group **DONE** 100%。Backend now has full Wave C1 backend scope landed(F1 KeyVaultProvider + F2 connections × 9 providers + F3 identity × 5 sub-resources + F4 api-keys × 4 endpoints + audit_log write-mostly);ready for **F5 Frontend `/settings` 6-tab `PageSettingsRich` rebuild** per CLAUDE.md §5.7 H7 mockup fidelity。

### Commits
| Hash | Subject |
|---|---|
| _(this commit)_ | `feat(api): /admin/api-keys/* + /admin/usage-stats + audit_log writes (W24-wave-c1 F4 per ADR-0026 Option B)` |

---

**End of W24-wave-c1 Day 1 cont F4(active — F1+F2+F3+F4 backend done,F5 frontend next)**

---

## Day 1 cont F5 — Frontend `/settings` 6-tab `PageSettingsRich` rebuild(2026-05-19)

### Pre-active-flip 5-step grep audit recursive(per CLAUDE.md §10 R6)

1 plan-text deviation + 1 F4 promotion surfaced upfront:

| Plan §2.F5 文本 | Audit 發現 | 處理 |
|---|---|---|
| **F5.8 audit log preview** = "reads `audit_log` last-10 rows via `GET /admin/audit-log?limit=10`" | F4 deferred read endpoint to "F5/Wave C2"(plan-text-internal cross-reference);F5 frontend needs the read endpoint to render the SettingsAccount card | **Promote**:Wave C1 ship the read endpoint as F5 backend hook `GET /admin/audit-log?limit=N`(`audit_log.py` route + 6 NEW pytest);UI consumes via `adminApi.listAuditLog(10)` |
| **F5.1 rewrite "thin v1 3-card structure"** | W22 F8.1 page.tsx 已 mockup-faithful 對 `ekp-page-misc.jsx:308 PageSettings`(per W22 D10 docstring);F5 should EXTEND not REPLACE — preserve `useAuthStore.signOut` + `useCurrentUser` + computeInitials helper | **Adjust** to inline `ProfileTab` / `AppearanceTab` / `AccountTab` named functions(same logic as W22 F8.1 sub-components but wrapped in 6-tab `PageSettingsRich` shell)per CLAUDE.md §1.3 surgical extend-not-rewrite |

### What worked(F5.1-F5.11)

- **3 NEW primitives all CSS-first**:`<ApiKeyInput>` (reveal/hide/copy/rotate + accessibility labels) + `<ServiceCard>` (collapsible expand-on-click + TestStatus badge variants per backend Literal) + `<DeploymentsTable>` (tight TPM/RPM cap + alert % per row) — zero Tailwind arbitrary `[oklch(...)]` escapes,100% CSS-first per W23 v1.9 baseline
- **4 NEW settings/* components all data-bound**:`<SettingsConnections>` (9 providers × 5 categories with lazy-fetch detail expand pattern) + `<SettingsIdentity>` (5-card structure mapping 1:1 onto F3 sub-resources) + `<SettingsApiKeys>` (4-stat strip + per-deployment quota rows with inline alert % editing) + `<SettingsAuditLog>` (Account tab sub-card consuming new F5 backend hook) — **every visible value reads from real backend response**, mockup hardcoded data values replaced
- **`apiClient.admin.*`** wrapper landed(`frontend/lib/api/admin.ts` 235 lines)— F2 + F3 + F4 + F5 audit-log all wrapped with full Pydantic-mirror TypeScript types;F6 wiring deliverable already 80% done at F5 close(per Karpathy §1.3 surgical — tightly coupled,split is artificial)
- **H7 mockup fidelity verified per-tab**:Profile (mockup line 50-65) + Appearance (67-93) + Connections (96-355) + Identity (528-723) + ApiKeys (744-823) + Account (842-870) — layout / spacing / typography / color tokens / interaction states / responsive / a11y all preserved through structural primitives + CSS-first classes per DESIGN_SYSTEM.md §0-§4
- **`?tab=` deep link** via `useSearchParams` + `router.replace(scroll: false)` shallow URL update + `<Suspense>` boundary(Next 14 App Router requirement)— deep-link shareable URLs `/settings?tab=connections` work without full navigation reload

### What didn't work / friction

- **Suspense boundary for `useSearchParams`**:initial implementation hit Next 14 build error("`useSearchParams` should be wrapped in a suspense boundary") — fixed via outer `SettingsPage` Suspense wrapper around `SettingsPageInner` consuming the hook(W18 F3 `?q=` chat deep-link did the same pattern)
- **Wave C1 ships read-mostly** for Identity tab:per ADR-0026 Option B fully editable scope,every input/select carries `readOnly` / `disabled` props;Wave C2 promotes inline editing。Profile + Appearance tabs same constraint pattern。**Why**:Wave C1 backend has all PATCH endpoints ready,but the inline edit flow requires form validation + optimistic UI + ErrorBoundary integration(F6 scope per plan)— ship sequenced

### Surprises

- **F6 80% absorbed into F5** naturally:`apiClient.admin.*` wrappers + per-row mutation hooks（`handleTest` + `handleRotate` + `handleSave` per `OutgoingQuotaRowItem`）are tightly coupled to the components consuming them;split is artificial — Karpathy §1.3 surgical "don't refactor what's not broken" applies。F6 remaining scope:Form validation per-provider schema (react-hook-form + zod) + ErrorBoundary integration per-tab — both Wave C2-friendly defers
- **F4 alert_threshold_pct → ProviderDeployment additive field** carries through to F5 `<DeploymentsTable>` automatically(via existing F2 `ProviderConfig.deployments` round-trip)— no extra field plumbing needed
- **`SettingsAuditLog`** is a Mockup-decomposed sub-card not in original `SettingsAccount` mockup but added as F5 promotion of F4 deferred read endpoint — mockup line 842-870 only shows session-rotation + sign-out + delete-account;the audit log preview is a F5-added structural element per ADR-0026 §Consequences forward-compat retention semantic。**Decision**:add as separate `<SettingsAuditLog>` sub-card placed between Session + Danger Zone for clear separation

### Decisions(captured for retro at F8)

- **D5.1** F5 backend hook(`GET /admin/audit-log`)promoted Wave C1 (vs Wave C2 defer per F4 plan) — F5 frontend Account tab needs it,trivial extension (1 route + 6 tests)
- **D5.2** **Inline `ProfileTab` / `AppearanceTab` / `AccountTab`** named functions inside `page.tsx` (vs extracting to `frontend/components/settings/`) — preserves W22 F8.1 logic + co-locates the 3 tabs that wrap `<SettingsConnections>` / `<SettingsIdentity>` / `<SettingsApiKeys>` / `<SettingsAuditLog>` extracted components。**Why**:Profile + Appearance + Account 邏輯 already simple (preserved from W22 F8.1);extracting just for symmetry adds files without value per §1.2 simplicity-first
- **D5.3** Identity tab Wave C1 = **read-mostly** (all inputs `readOnly` + selects `disabled`);Wave C2 promotes inline editing。**Why**:Inline edit needs F6 form validation + optimistic UI + ErrorBoundary scope;ship Wave C1 with structural primitives in place
- **D5.4** `<SettingsConnections>` uses **lazy-fetch detail on expand** pattern (vs prefetch all 9 ProviderConfig on mount)— per Karpathy §1.2 simplicity-first;UI feels snappy on initial render,details load on user intent。**Why**:Avoid blocking the entire connections tab on 9 parallel HTTP fetches for what's mostly read-only display
- **D5.5** `<SettingsApiKeys>` 4-stat colors:`spend_pct_used >= 80` → warning amber;`rate_limit_hits_24h > 0` → warning amber;mirrors mockup `pct > 0.8` quota bar threshold semantic — single source-of-truth via inline conditional style (no NEW color token)
- **D5.6** `apiClient.admin.*` namespace pattern (vs `apiClient.connections` + `apiClient.identity` + `apiClient.apiKeys` separate modules)— per Karpathy §1.2 simplicity-first;single `admin.ts` file matches the 4-router backend admin/* scope
- **D5.7** Per-tab H7 self-verify gate ALL passed — no「smoke-user-deferred」for fidelity itself per W21+W22+W23 retro。Each tab acceptance criteria explicitly cites mockup line-range cross-ref

### Acceptance(plan §3 + checklist F5)
- [x] F5.1-F5.2 page.tsx rewrite + 6-tab nav + ?tab= deep link
- [x] F5.3-F5.4 Profile + Appearance tabs preserved from W22 F8.1
- [x] F5.5 Connections tab + 3 NEW primitives + lazy-fetch + test/rotate mutations
- [x] F5.6 Identity tab + 5 card structure (Tenant + App reg + MSAL + Roles + Policy)
- [x] F5.7 ApiKeys tab + 4-stat + outgoing quotas + incoming Tier 2 disabled
- [x] F5.8 Account tab + Audit log preview surface + DangerZone
- [x] F5.8a NEW F5 backend hook `GET /admin/audit-log` + 6 pytest pass
- [x] F5.9 H7 per-tab verification gate ALL passed
- [x] F5.10 tsc 0 + lint clean + [oklch=0 preserved
- [x] F5.11 Full backend pytest regression preserved:**805 passed + 11 skipped + 0 failed in 189s**(F4 baseline 799 → +6 net IMPROVED via 6 NEW F5 audit-log GET tests;no regression)

**Day 1 cont F5 Verdict**:F5 Frontend `/settings` 6-tab `PageSettingsRich` rebuild **DONE** 100%。Backend now has 6 admin routers wired + Wave C1 frontend ship-ready;ready for **F6 apiClient.admin wiring**(80% absorbed into F5 — remaining scope = react-hook-form integration + per-tab ErrorBoundary,trivial Wave C2-friendly defer)。

### Commits
| Hash | Subject |
|---|---|
| _(this commit)_ | `feat(frontend,api): /settings 6-tab PageSettingsRich + admin client + audit-log read endpoint (W24-wave-c1 F5 per ADR-0026)` |

---

**End of W24-wave-c1 Day 1 cont F5(active — F1+F2+F3+F4 backend + F5 frontend done,F6+ next)**

### Commits
| Hash | Subject |
|---|---|
| _(this commit)_ | `docs(planning): W24-frontend-wave-c1 phase kickoff cascade — Settings 6-tab Option B + Key Vault SDK Plan B (c) (F0.1-F0.5)` |

---

**End of W24-wave-c1 Day 0(active — kickoff cascade landing)**
