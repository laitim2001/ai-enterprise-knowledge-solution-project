# ADR-0026: Settings v1 thin → 6-tab hub + Connections backend(**option set — Chris pick at W19 F6**)

**Date**: 2026-05-16
**Status**: **Accepted (Option B fully editable)** — W19 F6 Chris pick 2026-05-16。Chris selected Option B over Option C hybrid(W19 F2 §6 recommendation)和 Option A read-only。**Implications**:~22 NEW backend endpoints + Key Vault SDK new dependency(H2 trigger;R8 corp-proxy risk per ADR-0017 mitigation pattern noted)+ Wave C combined with ADR-0027 Option A = ~42 backend days **MUST split Wave C into C1+C2 sub-phases** per F4 §3.6 trigger + CLAUDE.md §10 rolling JIT
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
