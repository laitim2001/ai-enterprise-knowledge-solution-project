# ADR-0026: Settings v1 thin → 6-tab hub + Connections backend(**option set — Chris pick at W19 F6**)

**Date**: 2026-05-16
**Status**: **Accepted + Wave C1+C2 implemented** — W19 F6 Chris pick 2026-05-16 + W24-wave-c1 closed 2026-05-19 + W24b-wave-c2 closed 2026-05-20。Chris selected Option B over Option C hybrid(W19 F2 §6 recommendation)和 Option A read-only。**Implications**:~22 NEW backend endpoints + Key Vault SDK new dependency(H2 trigger;R8 corp-proxy risk per ADR-0017 mitigation pattern noted)+ Wave C combined with ADR-0027 Option A = ~42 backend days **MUST split Wave C into C1+C2 sub-phases** per F4 §3.6 trigger + CLAUDE.md §10 rolling JIT。**Wave C1 + C2 implementation** — see the two Implementation Status sections below(C1 ships fully-editable backend + read-mostly frontend;C2 promotes the frontend to inline-editable depth)。
**Approver**: Chris(Tech Lead + stakeholder)

## Context

`architecture.md v6 §5.0`(per ADR-0024)spec `/settings` v1 = **thin**:profile display + theme toggle + sign-out。`references/design-mockups/ekp-page-settings-tabs.jsx PageSettingsRich`(per W19 F1 audit) implements **6 tabs**:Profile / Appearance / **Connections** / **Identity & Auth** / **API Keys & Quotas** / Account。

The Connections + Identity & Auth + API Keys tabs are the H1 weight:

- **Connections tab** — 5 categories × 9 providers(Azure OpenAI w/ 4 deployments + Cohere + Azure AI Search + Blob + Postgres + Azurite + Langfuse + structlog + ACS Email + Container Apps + Key Vault),each with `ServiceCard` expandable + field inputs(`ApiKeyInput` reveal/hide/copy/rotate)+ meta table + deployments table with TPM/RPM bars
- **Identity & Auth tab** — Entra tenant + App registration(client ID/secret/redirect URIs/scopes/sign-in audience)+ MSAL config(token cache mem/Redis-Tier-2 + TTL + refresh rotation + CSRF rotation)+ Role mapping(3 + 1 Tier 2 Power User disabled)+ Sign-in policy(allowed domains + MFA toggles + auto-disable)
- **API Keys & Quotas tab** — 4-stat usage strip + Outgoing API quotas per provider(TPM + RPM bars)+ Incoming API keys table(Tier 2 disabled — "Tier 1 access via web UI only")

Per W19 F2 §3.4:**massive backend scope** — currently all 9 providers' credentials are `.env`-driven;promoting to UI-managed needs Key Vault SDK wire + provider CRUD + test connection + secret rotation endpoint group。Settings 6-tab Tier 1 ship represents significant operational maturity for the Beta launch operator(replaces `.env` rotation rituals + Azure Portal trips with self-service UI)。

Per CLAUDE.md §5.1 H1 — `architecture.md v6 §5.0` v1 = "profile display + theme + sign-out only";6-tab hub with management-grade tabs = architectural addition → requires ADR。Per CLAUDE.md §5.2 H2 — Key Vault SDK is **new dependency**(if Option B chosen)→ ADR + stop-and-ask。

## Decision

Adopt the **6-tab Settings hub** layout per the prototype。Amend `architecture.md v6 §5.0` with the 6-tab structure。Tab implementation scope is the strategic call:

### Option A — Read-only(Tier 1 ship,minimum scope)

- Profile / Appearance / Account tabs:fully functional Tier 1(profile read from session + theme via next-themes + sign-out via existing `/auth/logout`)
- Connections / Identity & Auth / API Keys tabs:**display current state + "Edit coming Tier 2" affordance** on all input fields
- Backend scope:`GET /admin/connections/list` + `GET /admin/identity/state` + `GET /admin/api-keys/list` + `GET /admin/usage-stats` ~= **3-4 NEW endpoints,~3 backend days**
- Beta operators continue rotating secrets via `.env` + Azure Portal + Key Vault Portal;UI provides discovery + status visibility
- Trade-off:operational maturity unchanged from current state — but Settings hub provides centralized visibility

### Option B — Fully editable(Tier 1 ship,maximum scope)

- All 6 tabs fully editable Tier 1
- Backend scope:`GET/PATCH /admin/connections/{id}` + `POST /admin/connections/{id}/test` + `POST /admin/connections/{id}/rotate-secret`(× 9 providers)+ `GET/PATCH /admin/identity/{tenant|app|msal|roles|policy}`(× 5 sub-resources)+ API Keys full CRUD ~= **~22 NEW endpoints,~7 backend days**
- **Key Vault SDK new dependency**(per H2 stop-and-ask — `azure-keyvault-secrets` ~600KB,R8 corp-proxy concern + ADR-0017 mitigation pattern)
- Beta operators full self-service rotation;Azure Portal trips eliminated for routine ops

### Option C — Hybrid(**RECOMMENDED — per W19 F2 §6**)

- Profile + Appearance + Account tabs:fully editable Tier 1(low scope,reuse existing endpoints)
- Connections + Identity & Auth + API Keys tabs:**read-only Tier 1**(per Option A)+ each field has "Edit coming Tier 2" affordance + each provider has "Test connection" button(`POST /admin/connections/{id}/test` lightweight)
- Backend scope:Option A(~3 endpoints)+ Test connection endpoints(× 9 providers ~= 9 more)+ minor profile patch from existing auth ~= **~10 NEW endpoints,~5 backend days**
- **Key Vault SDK deferred Tier 2**(read-only doesn't need to rotate)
- Beta operators rotate secrets via `.env` + Azure Portal,UI shows status + test-connection capability。Trade-off:slightly less self-service than Option B,but **fits single Wave C phase**(per F2 §4)+ no new dep + Tier 2 path clear

**Recommended pick**:**Option C hybrid**。Rationale:Beta cohort scope is internal Ricoh(per Q7),operators familiar with `.env` workflow;test-connection capability(Option C addition over A)is the immediate diagnostic value;Tier 2 promotes to full editing post-Beta governance(Q12 trigger,when scale demands self-service)。Cost:5 backend days fits single Wave C phase alongside ADR-0027 minimal RBAC(also ~5 days)— total ~10 backend days for Wave C。

## Alternatives Considered

1. **Keep v1 thin Settings**(stakeholder approved 2026-05-10 W18 closeout per ADR-0024)— rejected。Operator pain in production(`.env` rotation rituals)+ prototype 已 design 嘅 surface lost。A "Settings just shows profile" is a regression from Beta-readiness perspective。
2. **Split into multi-page**(`/admin/connections` + `/admin/identity` + `/admin/api-keys` separate routes) — rejected。Settings is the natural hub per ADR-0024 unified shell + multi-page proliferation defeats the IA simplicity established W18。
3. **Option B fully editable Wave C** — rejected per W19 F2 §6 recommendation。+22 backend days exceeds single Wave C phase budget,must split Wave C into C1+C2(violates rolling JIT — over-commit before W22 kickoff)+ H2 new dep concern(Key Vault SDK R8 risk)。
4. **Option A read-only**(simpler than Option C)— rejected。No "Test connection" diagnostic value — Beta operator UI provides only "what is configured" but not "is it working?",which is the high-frequency operator question。Option C adds 9 endpoints(per provider)but covers the immediate ops need。

## Consequences

**Per Option C(recommended)**:

**Positive**:
- 6-tab Settings hub provides centralized visibility for 9 external services + identity config + API quotas(operational maturity step for Beta)
- "Test connection" button per provider is immediate diagnostic value — replaces `curl https://...` ad-hoc verification
- Backend scope ~5 days fits single Wave C phase + no new dependency(Key Vault SDK deferred Tier 2)
- Tier 2 promotion path clear(when scale demands self-service,promote Connections + Identity edits — already-built read view becomes editable + add rotation endpoints)
- Identity & Auth tab role mapping(Workspace Admin / Knowledge Editor / End User Entra group → EKP role)is critical for Wave C ADR-0027 RBAC ship — Settings hub is the natural home

**Negative**:
- Beta operators still rotate secrets manually(`.env` for dev + Azure Portal + Key Vault Portal for prod)— no self-service rotation UI;trade-off accepted per Beta cohort small scale
- API Keys & Quotas Incoming Keys tab = disabled affordance("Tier 2 — Tier 1 access via web UI only")— external integration scope post-Beta governance
- Identity & Auth tab Power User mapping = disabled affordance(per ADR-0027 Option B minimal RBAC)— Tier 2 expansion
- 6-tab tab navigation density:design preserves W18 unified shell flow;tab content fits within `<AppShell>` main content area;no IA risk

**Neutral**:
- `architecture.md v6 §5.0` Settings paragraph amendment(thin v1 → 6-tab hub)inline-tagged at W22-frontend-wave-c kickoff
- `COMPONENT_CATALOG.md` C09 Settings row gets「6-tab per ADR-0026 Option C」status note + new endpoint group documented under C08 / C12 scope
- Legacy `PageSettings` in `ekp-page-misc.jsx`(thin v1)is SUPERSEDED — `frontend/` ships `PageSettingsRich`

## Implementation Status — W24-wave-c1 closeout(2026-05-19)

**Implemented by `W24-frontend-wave-c1` phase**(closed 2026-05-19,Gate **PASS WITH WAVE-C2-PROMOTE-DEFERS CAVEAT**)— Wave C1 ships **Option B fully editable Settings 6-tab hub backend + read-mostly frontend + audit_log write-mostly retention**。

### Backend(F1-F4)

- [x] **F1** `KeyVaultProvider` abstraction(`backend/storage/key_vault.py` Protocol + `EnvVarProvider` fallback + `azure_key_vault.py` async `AzureKeyVaultProvider` via `azure-keyvault-secrets>=4.8.0` + `azure-identity>=1.18.0`)+ `make_key_vault_provider` factory(lazy-import per ADR-0023 pattern;unset `KEY_VAULT_URL` never touches the SDK)— Azure SDK install via mobile hotspot Plan B (c)per ADR-0017 occurrence #8(15/15 pytest)
- [x] **F2** `/admin/connections/*`(5 endpoints × 9 providers seed):`GET` list + detail / `PATCH` non-secret fields / `POST /test` config-state probe(Wave A scope per W20 F2.1 `/health` pattern)/ `POST /rotate-secret` Key Vault rotation hook with masked preview;**`admin_provider_configs` Postgres table NEW** + 3-file split storage / postgres / factory(27 pytest)
- [x] **F3** `/admin/identity/*`(5 endpoints / 5 sub-resources):consolidated `GET` + 5 `PATCH` per tenant + app_registration + msal + roles + policy;**3 Tier 2 boundary guards** rejected via 422(`multi_disabled` audience / `distributed_disabled` token cache / active `power_user` ekp_role unless `is_tier2_disabled=True`)+ server-side `authority_url` derivation from `tenant_id × cloud_instance` per 3-cloud map(Azure Public / Government / China);**`admin_identity_config` Postgres table NEW per-sub-resource row pattern**(26 pytest)
- [x] **F4** `/admin/api-keys/*` + `/admin/usage-stats`(5 endpoints):4-stat strip(24h window per mockup line 749-752)+ per-deployment flatten `OutgoingQuotaList`(F2 azure_openai 4 deployments + 6 non-deployment providers = 10 rows seed)+ `PATCH /alert-threshold`(50-95 range,cost-spike rule consume)+ permanent `IncomingKeysDisabled.enabled: Literal[False]` Tier 2 affordance;**`audit_log` Postgres table NEW** + write hooks from F2 PATCH/test/rotate + F3 PATCH × 5 sub-resource + F4 PATCH(26 pytest)
- [x] **F5 backend hook** `GET /admin/audit-log?limit=N`(promoted from F4 deferral;default 10,1-200 range — 6 pytest)
- [x] **Per-sub-resource Postgres pattern** for `admin_identity_config`(vs single-row JSON blob plan-text)— audit_log per-row writes simpler at Wave C2 + 5 rows seeded idempotently
- [x] **Security hygiene**:secret values NEVER returned in any GET — only `secret_kv_ref` name + `secret_masked_preview`(`***last4`);client-supplied `authority_url` 喺 PATCH 被 strip + re-derived(prevents redirect injection)

### Frontend(F5)

- [x] **F5.1** `frontend/app/(app)/settings/page.tsx` 6-tab `PageSettingsRich` shell + `?tab=` deep link via `useSearchParams` + `<Suspense>` boundary + W22 F8.1 ProfileTab/AppearanceTab/AccountTab preserved inline(per Karpathy §1.3 surgical extend-not-rewrite)
- [x] **F5.2-F5.4** Profile + Appearance + Account tabs preserved from W22 F8.1 logic;Density toggle Tier 2 disabled affordance added per Wave C2 promote
- [x] **F5.5** `<SettingsConnections>` data-bound to `adminApi.listConnections()` + lazy-fetch `getConnection()` per row;**3 NEW primitives**:`<ApiKeyInput>`(reveal/hide/copy/rotate)+ `<ServiceCard>`(collapsible expand-on-click with TestStatus badge variants)+ `<DeploymentsTable>`(tight TPM/RPM cap + alert % table);Test connection + Rotate secret mutation buttons wire `adminApi.testConnection` + `adminApi.rotateSecret`
- [x] **F5.6** `<SettingsIdentity>` 5 cards 1:1 onto F3 sub-resources(Entra tenant + App reg + MSAL + Role mapping 3 active + Power User Tier 2 disabled affordance per ADR-0027 fallback + Sign-in policy);Wave C1 ship **read-mostly**(inline edit Wave C2 promote)
- [x] **F5.7** `<SettingsApiKeys>` 4-stat strip(spend_pct>=80 warn amber + rate_limit_hits>0 warn amber)+ `OutgoingQuotaRowItem` per-row TPM + RPM bars + inline alert threshold `<input type="number" min={50} max={95}>` editable + `<IncomingKeysDisabled>` Tier 2 affordance with permanent `enabled: false` Literal
- [x] **F5.8** `AccountTab` extends W22 F8.1 + NEW `<SettingsAuditLog>` sub-card reads `adminApi.listAuditLog(10)` + Danger Zone Delete account `<DisabledAffordance>` per mockup line 842-870
- [x] **`apiClient.admin.*`** wrapper(`frontend/lib/api/admin.ts` 235 LOC,13 methods)— full Pydantic-mirror TypeScript types for F2 + F3 + F4 + F5 audit-log endpoints
- [x] **H7 per-tab fidelity gate ALL passed** — mockup line-ref alignment for all 6 tabs(50-65 / 67-93 / 96-355 / 528-723 / 744-823 / 842-870)— **NO smoke-user-deferred for fidelity itself** per W21+W22+W23 retro consistency

### Tests + Verify gates

- [x] **F7 Vitest**:`tests/unit/settings-6tab.test.tsx` 217 LOC / **9 tests pass in 26s**(6 tab labels + 3 deep-link variations + tab-click router.replace spy + Account/Identity/ApiKeys data-bound assertions)
- [x] **F7 Playwright +2 NEW** app-shell-path tests(6-tab labels + `?tab=identity` deep link 2-state OR render-smoke)+ **+1 NEW** visual baseline test `settings-connections.png`(first-capture user-deferred per W20 F8.5 + W23 F2.3 precedent)
- [x] **Full backend pytest regression**:**805 passed + 11 skipped + 0 failed in 189s**(W23 baseline 705 → +100 net IMPROVED through W24 backend phase)
- [x] **Verify gates**:`tsc --noEmit` exit 0 + `next lint` clean + `Grep '[oklch'` across `frontend/` = **0 preserved**(post-W23 milestone maintained through 9 NEW frontend files)
- [x] **`architecture.md v6 §5.0`** inline-tagged amendment landed at F0 kickoff(thin v1 → 6-tab hub per ADR-0024 / §3.4 / §3.7 precedent;doc version held)

### Wave C2 promote items(NOT W24-wave-c1 scope)

- F6.3 Form validation per-provider schema(react-hook-form + zod)— Wave C1 ships HTML5 `min`/`max` Pydantic-mirror validation only
- F6.4 Optimistic UI per PATCH(rollback on error per TanStack Query pattern)— Wave C1 ships pessimistic await + refresh
- F6.5 ErrorBoundary integration per tab — Wave C1 ships inline `banner-destructive` per-component error surface
- Identity inline edit(Tenant + App reg + MSAL + Policy)— Wave C1 ships read-mostly with `readOnly` / `disabled` props;structural primitives in place
- `<SettingsConnections>` deployment cap edit(TPM/RPM)— Wave B+ scope per F4 plan(Azure portal authoritative for caps);alert_threshold % is the Wave C1 editable knob
- Audit log filter + pagination — Wave C2 promotes when SettingsAccount audit log surface lands properly
- Real-MSAL feature flag concurrent ship — Wave C2 per user 岔口 2(Wave C1 仍 mock-auth default per W18+ pattern)

## Implementation Status — W24b-wave-c2 closeout(2026-05-20)

**Implemented by `W24b-frontend-wave-c2-settings-depth` phase**(closed 2026-05-20,Gate **PASS WITH SMOKE-USER-DEFERRED CAVEAT**)— Wave C2 promotes the 6-tab Settings hub from Wave C1 read-mostly 到 **inline-editable depth**。The 6 "Wave C2 promote items" listed above are now landed(Connections deployment cap edit + real-MSAL feature flag remain out of scope per the lean-scope R6 decision — see below):

- [x] **F1** react-hook-form + zod + @hookform/resolvers — 3 NEW frontend deps via Plan B (a) `pnpm add` clean install,zero R8(npm-registry metadata non-binary per W17 F6 Vitest precedent;**no ADR-0017 amendment needed** — Plan B fallback never triggered)
- [x] **F2** Form validation — 3 zod schema files(`frontend/lib/schemas/admin/{identity,api_keys,connections}.ts`)mirror backend Pydantic models(GUID / duration / domain regex intentionally stricter than backend `str` — form-layer意義,wire contract unchanged);ApiKeys alert-threshold `OutgoingQuotaRowItem` upgraded to react-hook-form + `zodResolver`
- [x] **F3** Optimistic UI — `<SettingsConnections>` ProviderRow inline edit form + `useMutation` local-state optimistic(`onMutate` snapshot `detail` + `onError` rollback + `onSuccess` server-truth);test / rotate-secret retrofitted from `useState` to `useMutation`
- [x] **F4** ErrorBoundary per tab — NEW `ErrorBoundary` class component(`frontend/components/error/error-boundary.tsx`,first-party — no `react-error-boundary` dep)+ `<TabErrorState>` fallback;`settings/page.tsx` wraps all 6 tab bodies via a `TabBoundary` helper
- [x] **F5** Identity inline edit — `<SettingsIdentity>` rewritten from read-only display to **4 editable form cards**(Tenant / App registration / MSAL / Sign-in policy)each react-hook-form + `zodResolver` + per-card `useMutation` PATCH + `onSuccess reset(saved)` re-baseline + `onError` keep-edits;Role mapping card stays read-only display(individual mapping CRUD = mockup「⋯」menu /「Add mapping」deferred Wave C+);3 Tier 2 boundary guards preserved(`multi_disabled` / `distributed_disabled` disabled `<option>` + Power User row)
- [x] **F6** Audit log filter + pagination — `GET /admin/audit-log` gains additive `action_type` + `since` + `cursor` query params + NEW `AuditLogPage` wrapper response `{entries, next_cursor}`(over-fetch `limit+1` to derive `next_cursor`);`AuditLogBackend.list_recent` Protocol + InMemory + Postgres impls gain keyword-only filter params;`<SettingsAuditLog>` gains action filter `.select` + since date picker + cursor「Load more」button
- [x] **F7** Tests — `settings-identity-form.test.tsx` NEW(4 RHF+zod TenantCard cases)+ `settings-audit-log.test.tsx`(5 cases:F6 3 + F7.2 +2)+ Playwright `app-shell-path` / `visual-baseline` spec changes;Vitest settings-area 41/41 deterministic batch;backend pytest **816 passed**(W24-c1 805 → +11)

**Verify gates**:`tsc --noEmit` exit 0 + `next lint` clean + `Grep '[oklch'` across `frontend/` = **0 preserved** + mypy strict on the audit_log route/schema/storage clean。**No `architecture.md v6` amendment** — Wave C2 is depth promotion within the existing ADR-0026 6-tab spec(no Cn structural change)。

**Out of Wave C2 scope**(→ W24c+,per R6 lean-scope decision at kickoff):Connections deployment cap edit(Wave B+ — Azure portal authoritative for TPM/RPM caps)· real-MSAL feature flag verification(W16 Track A IT cred parallel track,Q11 operational early June 2026)· `client_secret` rotation full wire(needs Entra Graph SDK)· ADR-0027 Option A `/users` Tier 1.5 RBAC + ADR-0025 `/kb/[id]` Access tab activation。

**Caveat**:F7.6 Playwright `PW_CHANNEL=chrome` execution + `settings-identity.png` visual baseline first-capture = user pre-Beta smoke(spec file changes landed + tsc/lint verified)— same smoke-user-deferred pattern as W18 / W20 / W24-wave-c1。

## References

- `architecture.md v6 §5.0` Settings paragraph(v1 thin spec per ADR-0024)
- `references/design-mockups/ekp-page-settings-tabs.jsx`(`PageSettingsRich` lines 7-46;tabs definition lines 9-16;SettingsConnections lines 96-355;SettingsIdentity lines 528-723;SettingsApiKeys lines 744-823;SettingsAccount lines 842-870)
- `references/design-mockups/ekp-page-misc.jsx`(`PageSettings` thin v1 legacy lines 307-373 — SUPERSEDED)
- W19 F1 audit §2.1 D2(massive H1 weight surface)
- W19 F2 backend gap map §3.4 items 11-13(Option A/B/C effort estimates)+ §6 Option C recommendation
- ADR-0014 hybrid auth model(Identity & Auth tab content basis)
- ADR-0022 auth-transport hardening(MSAL config tab basis — cookie + CSRF + /auth/refresh)
- ADR-0023 Postgres persistent backing(users + sessions tables already exist via psycopg)
- ADR-0017 R8 corp-proxy mitigation(rationale for deferring Key Vault SDK to Tier 2 if Option C picked)
- Q11 operational Resolved(Entra ID tenant ricoh.onmicrosoft.com per W9 D1 alignment)
- ADR-0027 /users Tier 1.5 RBAC(Identity & Auth tab Role mapping interplay)
