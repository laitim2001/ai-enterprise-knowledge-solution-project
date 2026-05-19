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

### Commits
| Hash | Subject |
|---|---|
| _(this commit)_ | `docs(planning): W24-frontend-wave-c1 phase kickoff cascade — Settings 6-tab Option B + Key Vault SDK Plan B (c) (F0.1-F0.5)` |

---

**End of W24-wave-c1 Day 0(active — kickoff cascade landing)**
