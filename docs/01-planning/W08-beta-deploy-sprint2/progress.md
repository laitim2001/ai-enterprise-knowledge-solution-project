---
phase: W08-beta-deploy-sprint2
plan_ref: ./plan.md
checklist_ref: ./checklist.md
status: active    # flipped draft→active 2026-05-19 W8 D1 kickoff
---

# Phase W08 — Progress

> Daily progress + 結尾 retro。
> 每 commit 必須對應一個 Day-N entry mention(R2 binding rule per PROCESS.md §5)。
> Status:`draft` 自 2026-05-16 W7 D5 closeout cascade。

---

## Day 0 — 2026-05-16: Kickoff prep(W7 D5 末 closeout cascade same-session)

**Action**:Phase W08 kickoff prep(per PROCESS.md §2.3 rolling-JIT lifecycle;W7 D5 closeout cascade per CLAUDE.md §10 R5)

- Folder `docs/01-planning/W08-beta-deploy-sprint2/` created
- `plan.md` filled with status=`draft`(6 deliverables F1-F6:Real Entra ID auth integration LIVE switch + Azure Container Apps deploy backend + Azure Static Web Apps deploy frontend + LIVE smoke cascade(F1.7 + F3.5 + F4.5 W7 carry-overs)+ Cost monitoring + user feedback dashboard + Phase Gate closeout + W9 kickoff prep)
- `checklist.md` derived from plan deliverables(~31 atomic items)
- `progress.md` Day 0 entry initialized(this file)
- **Carry-over candidates from W07-beta-deploy**(per W7 retro § Carry-overs C1-C10):
  - C1 W8 D1 Q11 IT operational cascade trigger(F1.1 — Beta-blocking if W8 D5 仍未 confirm)
  - C2 W8 D2-D3 real msal_provider wire(F1.2 + F1.3 — H2 vendor ask-and-approve cycle 預期 direct approve since msal SDK within Tier 1 vendor scope per architecture.md §3.2)
  - C3 W8 D4 LIVE switch + F1.7 LIVE smoke(F1.4 + F1.5)
  - C4 W8 cost dashboard data source(F5.1 + F5.2)
  - C5 F3.5 + F4.5 LIVE smoke deferred from W7(F4.1 + F4.2)
  - C6 F5.3 Citation card mobile UX 仍 deferred(C10 not yet built)
  - C7 F5.5 Pixel diff snapshots W8 polish window install
  - C8 Documents/chunks/eval/screenshots/debug routes auth wire(F4.4)
  - C9 Plan estimate calibration applied
  - C10 Real Langfuse SDK wire(F5.1)
- **W8 critical path identification**:**Q11 IT operational confirm cascade trigger W8 D1**;F1.1 IT engagement = F1.2-F1.5 cascade gate;若 W8 D5 仍未 confirm → R-B1 escalation Stakeholder + IT manager 三方
- **Beta deploy phase entry**:W7 closes Tier 1 12-week sprint Beta hardening Sprint 1;W8 = Beta deploy Sprint 2(Azure deploy + real Entra ID + LIVE smoke cascade);W9-W10 = Beta internal testing;W11-W12 = staged rollout 25% → 100% production launch per architecture.md §6.1 timeline

### Decisions / OQ summary

- W7 closeout PASS verdict landed(G1'-G7 全 PASS — 8 G's verified;W7 retro 7 sections complete;F1.1 + F1.7 + F3.5 + F4.5 + F5.3 + F5.5 properly deferred with rationale)
- Q11 unchanged decision-level Resolved 2026-05-05(W6 D5 stakeholder approval cycle);W8 D1 IT operational cascade trigger 是 W8 D1 critical path
- W7 commits = 10(W7 D1+D2+D3+D4+D5 progressive batches each `feat` + `docs(planning) backfill` pair)

### Open / blocked

- ⏸ W8 D1 implementation start awaiting Chris W7 closeout sign-off + W8 D1 kickoff approval + Q11 IT operational confirm
- ⏸ W8 plan/checklist status `draft → active` flip W8 D1 trigger

### Commit reference

- W7 D5 closeout commit `_(pending)_`(W08 phase folder included in W7 closeout batch per F6.3 acceptance)

---

## Day 1 — 2026-05-19: W8 phase active flip + F2.1 Dockerfile finalize + F2.2 ACA Bicep spec

**Action**:W8 D1 implementation kickoff — W8 frontmatter `draft → active`(W7 D5 closeout PASS G1'-G7 verdict landed);F2.1 multi-stage Dockerfile + non-root user + HEALTHCHECK;F2.2 ACA backend.bicep declarative spec(no actual deploy this session per Chris infra ownership)。**F1.1 Q11 IT engagement** — external Chris dependency in-progress;non-blocking for F2/F3/F4/F5 dev work per W7 a-revised mock auth strategy preserved。

**Backend(C12)**:
- `backend/Dockerfile` — multi-stage rewrite:
  - Stage 1 `builder` — Python 3.12-slim + uv installs deps into `/opt/venv`;dep manifests copied first for layer cache reuse across code-only changes
  - Stage 2 `runtime` — slim image,non-root `ekp` user UID 10001 / GID 10001(off host typical [1000, 9999] range to avoid bind-mount UID clash);minimal system pkg(`curl` only for HEALTHCHECK probe)
  - HEALTHCHECK `curl -fsS http://127.0.0.1:8000/health` interval=30s timeout=5s start-period=15s retries=3(allows lifespan Azure SDK warm-up)
  - PATH + PYTHONPATH baked;UID-aware COPY chown
  - CLAUDE.md §5.5 H5 — secret bake-in 防止 via .dockerignore + Settings runtime read
- `backend/.dockerignore` — extended with `.env*` + `*.pem` / `*.key` / `*.pfx` H5 enforcement(`.env.example` 留 whitelist)

**Infra(C12)**:
- `infrastructure/aca/backend.bicep` NEW — Container App declarative spec:
  - Internal ingress `external: false`(Front Door + Auth gate upstream)+ targetPort 8000
  - User-assigned Managed Identity for Key Vault Secrets User role
  - 6 secrets via `keyVaultUrl:` references(NEVER plain-text):AZURE_OPENAI_API_KEY / AZURE_SEARCH_ADMIN_KEY / COHERE_API_KEY + 3 Entra ID(TENANT_ID / CLIENT_ID / CLIENT_SECRET)
  - Resources 1 vCPU + 2 GiB(architecture.md §9 cost row)
  - Liveness + Readiness probes both `/health`,separate so slow lifespan 唔 kill replica
  - Autoscale 1-5 replicas;HTTP concurrency target 30(architecture.md §8.1 R5 paired app-level `rate_limit_concurrent=5/user`)
  - `FEATURE_AUTH_MOCK=false` env var(W8 D4 LIVE switch ready;mock dev mode `.env`-only past W8)
- `infrastructure/aca/README.md` NEW — pre-requisite list(Chris infra setup outside W8 D1 AI scope):resource group + ACA managed environment + ACR + Key Vault + Managed Identity + 6 secrets;manual `az deployment group create` reference(production via W8 D2 GHA F2.3)

**Verification**:
- 269/269 backend pytest pass(W7 closeout baseline preserved;Dockerfile changes 屬 build-time,zero runtime regression)
- Bicep spec `az bicep build` syntax-check pending Chris infra session(declarative spec;no `az` CLI invocation this session)
- `.dockerignore` H5 audit:`.env*` + secrets gitignored AND dockerignored;`.env.example` whitelisted

**Karpathy §1 alignment**:
- §1.1 think-before-coding:Dockerfile multi-stage saves runtime image size(builder + uv stripped);non-root UID 10001 chosen to avoid host UID range clash;HEALTHCHECK start-period=15s based on lifespan AzureOpenAIEmbedder + HybridSearcher + Synthesizer + CragGrader concurrent `__aenter__` warm-up time(empirical W4 D1)
- §1.2 simplicity-first:single Bicep file 一個 backend Container App spec(non multi-resource template);declarative-only,no `az deploy` automation this session(W8 D2 F2.3 GHA pipeline cascade);.dockerignore positive-list extension matches root .gitignore §5.5 H5 H1 alignment
- §1.3 surgical:Dockerfile rewrite zero impact to backend code paths(runtime entrypoint identical `uvicorn api.server:app` per W1 baseline);ACA spec lives in dedicated `infrastructure/aca/` folder — not mixed with code
- §1.4 goal-driven:Dockerfile + Bicep both verifiable independently(docker build + az bicep build syntax check);no untestable speculation

**Hard constraints check**:
- H1 architecture lock — ✅ no §3 / §4 component change;Bicep spec implements §6.1 W8 deploy + §8.1 R5 autoscale spec
- H2 vendor lock — ✅ Azure Container Apps + Azure Container Registry + Azure Key Vault + Managed Identity 全屬 architecture.md §3.2 stack(zero new vendor)
- H3 Dify reference — ✅ untouched
- H4 Tier 1 boundary — ✅ no Tier 2 滲入
- H5 security & privacy — ✅ Bicep secrets 全 Key Vault references;Dockerfile + .dockerignore enforced no `.env` bake-in;non-root user runtime
- H6 test coverage — ✅ Dockerfile changes 屬 build-time;backend test suite 269 unaffected

### Decisions / OQ summary
- No OQ change(Q11 unchanged decision-level Resolved 2026-05-05;operational IT engagement F1.1 in-progress external)
- No ADR triggered(Bicep spec + Dockerfile rewrite 屬 architecture.md §6.1 W8 deploy implementation;non-architectural amendment per CLAUDE.md §5.1 H1 boundary)

### Open / blocked
- ⏸ **F1.1 W8 D1 Q11 IT operational confirm cascade trigger** — Chris IT engagement in-progress(Tenant Access + App Registration + Owner Identification per `beta-plan-v1.md §2 W8.F1`);若 W8 D5 仍未 confirm → R-B1 escalation per RISK_REGISTER R14 Stakeholder + IT manager 三方
- ⏸ F1.2 + F1.3 backend / frontend real msal SDK wire — W8 D2-D3 trigger(可以開始 W8 D2 即使 F1.1 仍 pending — msal SDK install + JWT validation skeleton implementation 不需要 real cred;real test 推 F1.5 W8 D4)
- ⏸ F2.3 GHA CI/CD pipeline — W8 D2 trigger
- ⏸ F2.4 Azure Key Vault secrets management — W8 D2-D3 trigger(Chris infra setup pre-requisite per `infrastructure/aca/README.md`)
- ⏸ F2.5 ACA networking + Private Endpoint — W8 D2-D3 trigger
- ⏸ F3 SWA frontend deploy — W8 D3-D4
- ⏸ F4 LIVE smoke cascade — W8 D4
- ⏸ F5 cost dashboard + Langfuse SDK wire — W8 D5
- ⏸ F6 closeout — W8 D5

### Commit reference
- W8 D1 commit `de316e4`(7 files changed,+362 / -14;2 new files + 5 modified;Dockerfile multi-stage + non-root + HEALTHCHECK + .dockerignore H5 + ACA backend.bicep + README + W8 frontmatter active flip)

---

---

## Day 2 — 2026-05-20: F1.2 real msal_provider + F1.6 + F2.3 + F2.4

**Action**:W8 D2 — backend real Microsoft Entra ID JWT validator landed(F1.2 + F1.6),GHA CI/CD pipeline draft(F2.3),Key Vault secrets management SOP(F2.4)。**F1.1 Q11 IT engagement** — Chris external in-progress;tenant_id + client_id 仍 pending — F1.2 implementation 不 block(empty config falls back to 503;Settings populate W8 D2-D3 cascade once IT delivers)。

**Backend(C11)**:
- `backend/pyproject.toml` — `python-jose[cryptography]>=3.3` added(Karpathy §1.2 simplicity-first:backend = resource server only,validates JWT;skip msal Python SDK since frontend msal-react W8 D3 handles token acquisition;single new dep within architecture.md §3.2 Microsoft Entra ID vendor scope per W8 plan §2 F1.2)
- `backend/storage/settings.py` — `azure_tenant_id` + `azure_client_id` + `jwks_cache_ttl_s=3600` + `azure_jwt_issuer_template` + `azure_jwks_uri_template` 新 Settings(populated via Key Vault refs in ACA per `infrastructure/aca/backend.bicep`)
- `backend/api/auth/msal_provider.py` — **real implementation replaces W7 D1 503 skeleton**:
  - JWKS fetch via httpx with module-level TTL cache(`reset_jwks_cache()` test hook)
  - `_select_signing_key` matches JWT header `kid` against JWKS keys
  - `jwt.decode` enforces RS256 + audience=`azure_client_id` + issuer per tenant
  - Failure paths:expired → 401 token expired;audience/issuer mismatch → 401 token claims invalid;malformed → 401;missing kid / oid / tid → 401;JWKS fetch fail → 503
  - Identity build:`oid` + `tid` required;`preferred_username` falls back to `upn` then `email` then `oid`(B2B / guest tolerance)
  - All failures emit safe message — never leak inner JOSE error to client(CLAUDE.md §5.5 H5)
  - Server-side structlog `jwt_decode_failed` / `jwks_fetch_failed` / `jwt_claims_invalid` for ops debugging

**Tests(F1.6)**:
- `backend/tests/test_msal_provider.py` NEW — 13 unit tests with self-signed RSA keypair fixture + JWKS mock:valid signed JWT 200 + upn fallback 200 + expired 401 + audience mismatch 401 + issuer mismatch 401 + missing kid 401 + unknown kid 401 + missing oid claim 401 + malformed JWT 401 + missing credentials 401 + JWKS fetch failure 503 + incomplete config 503 + JWKS cache TTL reuse(2 calls → 1 fetch)
- W7 D1-D5 baseline preserved:`test_mock_msal.py` 7 + `test_auth_routes.py` 7(monkeypatched authenticate_msal still exercises the contract)+ `test_auth_endpoints.py` 5 + `test_f1_7_mock_smoke.py` 9 — all 28 unchanged because real msal_provider with empty `azure_tenant_id` falls back to 503 same as old skeleton

**Infra(C12)**:
- `.github/workflows/backend-ci.yml` NEW(F2.3 PR validation)— ruff + pytest on every PR / push to main affecting `backend/**`;15-min timeout;uv venv install
- `.github/workflows/backend-deploy.yml` NEW(F2.3 deploy)— main push triggers test → ACR build + push → resolve ACA env + MI IDs → Bicep deploy → smoke `/health` via `az containerapp exec`(internal ingress per backend.bicep);workflow_dispatch with `rollback=true` swaps traffic to previous active revision(non-destructive;previous revision stays warm)
- OIDC federated credential via `azure/login@v2`(GHA secrets `AZURE_CLIENT_ID` / `AZURE_TENANT_ID` / `AZURE_SUBSCRIPTION_ID` 走 SP non plain-text)
- `infrastructure/keyvault/README.md` NEW(F2.4 SOP)— vault layout 6 secrets + create/populate commands + Managed Identity grant(`Key Vault Secrets User` reader role per least-privilege CLAUDE.md §5.5 H5)+ rotation SOP(per-cadence + emergency)+ verification + Tier 2 boundaries(CMK / cross-region replication out)

**Verification**:
- `pytest -q` → **282 passed in 143.57s**(W7 closeout baseline 269 + F1.6 +13 = 282;zero regression)
- `ruff check api/auth/msal_provider.py tests/test_msal_provider.py storage/settings.py` → All checks passed
- W7 baseline 28 auth/rate/audit tests verified pass with real msal_provider in-place

**Karpathy §1 alignment**:
- §1.1 think-before-coding:backend = resource server,frontend handles token acquisition → backend doesn't need msal Python SDK,only python-jose for JWT validation;single dep instead of two;empty `azure_tenant_id` 503 fail-closed preserves W7 D1 contract while W8 D2-D3 IT delivery in-flight
- §1.2 simplicity-first:python-jose[cryptography] single dep covers all needs(httpx already available for JWKS fetch);no in-memory key parsing libraries;TTL cache simple dict instead of cachetools;module-level singleton with test reset hook
- §1.3 surgical:msal_provider.py rewrite scope-isolated(no edit to mock_msal.py / dependency.py / models.py / test_mock_msal.py);GHA workflows in dedicated `.github/workflows/`;Key Vault SOP in dedicated `infrastructure/keyvault/`
- §1.4 goal-driven:13 acceptance criteria(W8 plan §2 F1.6 + extras: kid missing/unknown,oid missing,JWKS cache reuse)→ 13 named tests → all 13 PASS;closed loop

**Hard constraints check**:
- H1 architecture lock — ✅ no §3 / §4 component change;real msal_provider implements C11 design intent per architecture.md §6.1 W7 + §6.2 Beta;non-architectural amendment
- H2 vendor lock — ✅ python-jose[cryptography] within architecture.md §6.1 W7 Microsoft Entra ID scope;NO new vendor introduced(Microsoft Entra ID 已 locked vendor;python-jose 是 implementation library for that vendor's protocol per W8 plan §2 F1.2 ask-and-approve direct approve cycle pre-confirmed)
- H3 Dify reference — ✅ untouched
- H4 Tier 1 boundary — ✅ single-tenant;multi-tenant aggregation queries explicit Tier 2
- H5 security & privacy — ✅ all JWT validation failures emit safe message(client never sees JOSE error / signature detail);Key Vault SOP enforces no plain-text bake-in;Managed Identity reader role least-privilege;GHA OIDC federated credential 唔 plain-text SP secret in workflow logs
- H6 test coverage — ✅ 13 new tests for critical C11 module;test_msal_provider.py covers W8 plan §2 F1.6 acceptance matrix + edge cases

### Decisions / OQ summary
- No OQ change(Q11 unchanged decision-level Resolved;operational IT engagement F1.1 in-progress external)
- No ADR triggered(python-jose dep within architecture.md §6.1 Microsoft Entra ID vendor scope;non-architectural amendment per CLAUDE.md §5.1 H1 boundary check + §5.2 H2 ask-and-approve direct approve cycle pre-confirmed in W8 plan §2 F1.2)

### Open / blocked
- ⏸ **F1.1 W8 D1 Q11 IT operational confirm cascade** — Chris external in-progress;tenant_id + client_id + client_secret 走 Key Vault populate W8 D2-D3 cascade per `infrastructure/keyvault/README.md`;若 W8 D5 仍未 confirm → R-B1 escalation per RISK_REGISTER R14
- ⏸ F1.3 frontend msal-react real wire — W8 D3 trigger
- ⏸ F1.4 W8 D4 LIVE switch + F1.5 LIVE smoke — W8 D4
- ⏸ F2.5 ACA networking + Private Endpoint — W8 D2-D3 trigger(Chris infra)
- ⏸ F3 SWA frontend deploy — W8 D3-D4
- ⏸ F4 LIVE smoke cascade — W8 D4
- ⏸ F5 cost dashboard + Langfuse SDK wire — W8 D5
- ⏸ F6 closeout — W8 D5

### Commit reference
- W8 D2 commit `9504a6b`(9 files changed,+910 / -28;4 new files + 5 modified;real msal_provider + 13 F1.6 tests + 2 GHA workflows + Key Vault SOP + python-jose[cryptography] dep)

---

---

## Day 3 — 2026-05-21: F1.3 frontend msal-react + F3.1 + F3.4 + F2.5

**Action**:W8 D3 — frontend real msal-react wire(F1.3),Azure SWA build pipeline GHA(F3.1)+ SWA route fallback config(F3.4),ACA networking Bicep Private Endpoint to Azure AI Search(F2.5 declarative spec)。**F1.1 Q11 IT engagement** — Chris external in-progress;NEXT_PUBLIC_AZURE_TENANT_ID + CLIENT_ID 仍 pending → `.env.example` populated 等 IT delivery W8 D3-D4。

**Frontend(C11)**:
- `frontend/package.json` — `@azure/msal-browser@5.9.0` + `@azure/msal-react@5.3.2`(Microsoft official Entra ID SDK,within architecture.md §6.1 W7 vendor scope per W8 plan §2 F1.3 ask-and-approve direct approve cycle pre-confirmed);installed via pnpm
- `frontend/lib/auth/msal_provider.ts` — **real implementation replaces W7 D1 throw skeleton**:
  - `PublicClientApplication` lazy singleton(SSR-safe,gated `typeof window !== 'undefined'`)+ sessionStorage cache
  - `initMsal()` idempotent + handleRedirectPromise on landing-back from Entra ID hosted login + active-account restore from session cache
  - `loginMsal()` → `loginRedirect`(production-grade vs popup avoiding popup-blocker / iframe sandbox issues)
  - `logoutMsal()` → `logoutRedirect`
  - `refreshMsal()` → `acquireTokenSilent` + cache update
  - `getMsalBearer()` / `getMsalUser()` sync — returns module-level cached access_token / account(populated after login + refresh)
  - `_resetMsalForTests()` test escape hatch(future Vitest harness install)
- `frontend/lib/providers/auth-provider.tsx` — `AuthProvider` LIVE msal-react path branch:
  - `initMsal()` on mount + `handleRedirectPromise` + active-account restore;**no auto-redirect to Entra ID hosted login**(prevents infinite-loop on misconfigured cred)
  - 50-min `setInterval` calls `refresh()` silent token refresh while tab open(Microsoft default 1h expiry buffer)
  - Failure surfaces `useAuthStore.setState({ status: 'error' })` for ErrorBoundary downstream
  - Mock mode branch unchanged(W7 dev auto-sign-in preserved)
- `.env.example` — NEW NEXT_PUBLIC_AZURE_TENANT_ID + NEXT_PUBLIC_AZURE_CLIENT_ID + NEXT_PUBLIC_AZURE_API_SCOPE(populated W8 D3-D4 after Q11 IT delivery;mirror backend AZURE_TENANT_ID / AZURE_CLIENT_ID from Key Vault)

**Infra(C12 — F3 frontend deploy)**:
- `.github/workflows/frontend-deploy.yml` NEW(F3.1)— SWA build pipeline:lint + type-check + Next.js build → `Azure/static-web-apps-deploy@v1` upload to staging slot(PR / manual)or production(main push);env vars:NEXT_PUBLIC_API_URL + AUTH_MOCK=false + AZURE_TENANT/CLIENT/SCOPE from GHA secrets;PR comment auto-post preview URL;pnpm cache via `pnpm/action-setup@v4` + `actions/setup-node@v4`
- `frontend/staticwebapp.config.json` NEW(F3.4)— SPA navigation fallback to `/index.html` for Next.js App Router client routes(exclude `/api/*` + `/_next/*` + asset MIME globs);responseOverrides:401 → `/admin` 302 redirect(re-auth flow)+ 403 → `/admin/error.html` 403 + 404 → `/index.html` 200(SPA route);global security headers:X-Frame-Options DENY + X-Content-Type-Options nosniff + Referrer-Policy + Permissions-Policy + HSTS

**Infra(C12 — F2.5 ACA networking)**:
- `infrastructure/aca/networking.bicep` NEW(declarative spec only;Chris infra apply)— Private Endpoint `<name>-search-pe` to Azure AI Search service:`searchService` group id;auto-attached Private DNS zone group `privatelink.search.windows.net` so backend's `azure_search_endpoint` resolves to private IP from inside ACA VNet;outputs `searchPrivateEndpointId` + `searchPrivateEndpointName` for backend.bicep PE verification
- `infrastructure/aca/README.md` updated — W8 D3 cascade section(Chris apply sequence:VNet pre-provision → ACA env vnet integration AT CREATE non-mutable post-create → DNS zone link → Bicep deploy → disable Search public access AFTER PE verified)

**Verification**:
- `tsc --noEmit`(frontend)→ exit 0(after CacheOptions.storeAuthStateInCookie removed — msal-browser 5.x dropped this option)
- `eslint --max-warnings=0 lib/auth lib/providers/auth-provider.tsx` → exit 0
- `pytest -q`(backend)→ **282 passed in 144.31s**(W8 D2 baseline preserved;zero regression — frontend-only changes)
- pnpm install msal deps `+ @azure/msal-browser 5.9.0 + @azure/msal-react 5.3.2 done in 33.4s`

**Karpathy §1 alignment**:
- §1.1 think-before-coding:msal-browser is browser-only → `typeof window !== 'undefined'` guard at every entry point + lazy singleton init prevents SSR build crash;`loginRedirect` over `loginPopup` for production reliability(corp networks);silent refresh interval 50min slightly before 1h Microsoft default expiry
- §1.2 simplicity-first:module-level cache pattern preserves W7 D2 sync `getBearer()` API → no api-client.ts refactor needed(post-login + refresh both populate cache);`PublicClientApplication` direct usage over `MsalProvider` Context — avoids splitting auth state between Zustand store + MSAL Context double-source;F2.5 Bicep declarative-only(non auto-deploy this session per Chris infra ownership)
- §1.3 surgical:msal_provider.ts complete rewrite preserves all 5 exported function signatures from W7 D1 skeleton(getMsalBearer / getMsalUser / loginMsal / logoutMsal / refreshMsal — same TS types);auth-provider.tsx adds LIVE branch w/o touching mock mode path;.env.example append-only;F3.1 + F3.4 + F2.5 全部 NEW files in dedicated paths
- §1.4 goal-driven:F1.3 verifiable goal "frontend tsc + eslint clean + msal-react can be initialized + bearer pre-populated in cache" — TS strict mode caught CacheOptions issue early;F3.1 + F3.4 + F2.5 declarative — verifiable on Chris infra apply(W8 D3-D4 cascade)

**Hard constraints check**:
- H1 architecture lock — ✅ no §3 / §4 component change;real msal-react wire implements C11 design intent per architecture.md §6.1 W7 + §6.2 Beta;non-architectural amendment
- H2 vendor lock — ✅ @azure/msal-browser + @azure/msal-react 屬 Microsoft Entra ID locked vendor implementation libraries(同 W8 D2 backend python-jose pattern);ask-and-approve direct approve cycle pre-confirmed in W8 plan §2 F1.3
- H3 Dify reference — ✅ untouched(layout.tsx Dify Image 4 注釋 preserved as reference-only)
- H4 Tier 1 boundary — ✅ single-tenant only(loginRedirect uses tenant-specific authority not /common /organizations);multi-tenant Tier 2
- H5 security & privacy — ✅ token cache `sessionStorage`(safer than localStorage — cleared on tab close;not accessible via XSS to other tabs);`storeAuthStateInCookie: false`(default;cookie store deprecated in msal-browser 5.x);global security headers in staticwebapp.config.json;FRONTEND_CLIENT_ID + AZURE_API_SCOPE 走 GHA secrets non plain-text in workflow logs
- H6 test coverage — ✅ frontend test harness deferred per W7 D4 F4.4 / F5.5(no Vitest installed;adding = scope creep);`_resetMsalForTests` escape hatch authored ready for future install

### Decisions / OQ summary
- No OQ change(Q11 unchanged decision-level Resolved 2026-05-05;F1.1 IT engagement in-progress)
- No ADR triggered(@azure/msal-* + python-jose 都屬 Microsoft Entra ID locked vendor implementation libraries;non-new vendor;same boundary check pattern as W8 D2 F1.2)

### Open / blocked
- ⏸ **F1.1 W8 D1 Q11 IT operational confirm** — Chris external in-progress;cred populate 等 IT delivery W8 D3-D4(both backend Settings + frontend NEXT_PUBLIC_*)
- ⏸ F1.4 W8 D4 LIVE switch + F1.5 LIVE smoke — W8 D4 trigger(等 cred populate + dev tenant Entra ID redirect flow exercise)
- ⏸ F2.5 networking Bicep apply — Chris infra session(VNet pre-provision + ACA env vnet integration + DNS zone link + PE deploy + disable Search public access)
- ⏸ F3.2 SWA custom domain DNS — Chris W8 D3-D4(`ekp.ricoh.com` 或 staging subdomain)
- ⏸ F3.3 Auth integration sync — register msal-react redirect URI + post-logout URI in Entra ID app registration(blocked on F1.1)
- ⏸ F4 LIVE smoke cascade — W8 D4
- ⏸ F5 cost dashboard + Langfuse SDK — W8 D5
- ⏸ F6 closeout — W8 D5

### Commit reference
- W8 D3 commit `cbd36b3`(11 files changed,+621 / -41;3 new files + 8 modified;real msal-react wire + SWA pipeline + SWA config + ACA PE Bicep + 2 deps installed + .env.example expanded)

---

---

## Day 4 — 2026-05-22: F4 smoke substitute + F1.1/F3.2/F3.3 SOPs;F1.4+F1.5 LIVE deferred

**Action**:W8 D4 — F4 LIVE smoke cascade substitute(E1+E5+E12+F3.5 audit chain via TestClient + mocked Azure responses,deterministic + zero LLM cost);Chris-cascade SOPs landed for F3.3 Entra ID app registration + F3.2 SWA custom domain。**F1.4 LIVE switch + F1.5 LIVE smoke 仍 DEFERRED** — Q11 IT cred 仍未 deliver(Chris external in-progress per W8 D1+);F1.7 LIVE smoke 推 W8 D5 OR W9 cascade post-IT engagement。**Architecture impact zero**;all W8 D4 work within existing Microsoft Entra ID locked vendor scope。

**Backend tests(F4 substitute)**:
- `backend/tests/test_e1_e5_e12_smoke.py` NEW — 5 integration smoke tests covering full middleware chain(authenticate_mock + RateLimitMiddleware + AuditLogMiddleware + register_error_handlers + `/query` route)against mocked retrieval / synthesis:
  - **E1** OOS query 拒答:_MockSynth `refused=True` + grounded refusal message → 200 + `refused=true` + NO ApiError envelope(per error-cases-E1-E14.md §2 non-error path)
  - **E5** LLM API timeout:`_Timeout` Exception in synth → 502 envelope `code=pipeline.retrieval_failed` + actionable_hint;NO Traceback / site-packages leak
  - **E5** Synthesizer unavailable:`app.state.synthesizer = None` → 200 retrieval-only fallback per W2 baseline
  - **E12** chunk_id collision across docs:dual `kb_id__doc_id__chunk_id` namespaced ids returned from `/query` distinctly(no collision merge)— architecture.md §7.3 E12 namespace enforcement verified
  - **F3.5** audit chain under burst:5 sequential `/query` calls → audit middleware emits 5 `audit_log` rows with mock `oid` + `tid` + `audit_action="POST /query"` + `request_id` round-trip(X-Request-ID header echoed)
- **F4.5 LIVE smoke vs substitute distinction**:LIVE smoke against real dev server with Azure cred remains W8 D5 / W9 carry-over(Chris dev server availability + W7 D5 retro § Carry-overs C5);substitute provides equivalent acceptance via deterministic test 而 zero LLM spend

**Doc(F3.3 + F3.2 Chris cascade SOPs)**:
- `infrastructure/entra-id/README.md` NEW(F3.3 SOP)— 8-step Entra ID app registration cascade for Chris:Pattern A combined SPA+API single app(recommended)/ Pattern B separate apps(audit fallback);step 1-7 cred populate to Key Vault + GHA secrets;step 8 F1.5 LIVE smoke procedure(uvicorn + pnpm dev + redirect round-trip + audit propagation verification);Tier 2 boundaries(multi-tenant dispatcher / Conditional Access / B2B / claims mapping all out)
- `infrastructure/swa/README.md` NEW(F3.2 SOP)— 5-step SWA custom domain cascade for Chris:Azure portal Add domain → Ricoh corp DNS team CNAME + TXT validation → portal Validate → Entra ID redirect URI sync → GHA env var update;apex domain caveat(ALIAS vs A record);post-validation security headers verification via `curl -I`;rollback procedures

**F1.4 + F1.5 LIVE SWITCH STATUS**:
- F1.4 `Settings.feature_auth_mock=False` flip:**NOT executed** — empty `azure_tenant_id` + `azure_client_id` would cause msal_provider 503 fail-closed across all protected routes(W7 D1 contract);Karpathy §1.1 think-before-coding — flipping without cred = breaking system not implementing
- F1.5 LIVE smoke real Entra ID redirect flow:**deferred** — requires Chris IT cred delivery(Tenant Access + App Registration + Owner Identification per W8 plan §2 F1.1)+ dev server boot
- F1.7 LIVE smoke acceptance(W7 plan §3 G1):W8 D5 OR W9 trigger post-cred(per `infrastructure/entra-id/README.md` step 8)

**Verification**:
- `pytest -q` → **287 passed in 90.53s**(W8 D3 baseline 282 + F4 substitute +5 = 287;zero regression)
- `ruff check tests/test_e1_e5_e12_smoke.py` → All checks passed(after import order auto-fix)
- frontend tsc + eslint unchanged from W8 D3(no frontend code changes)

**Karpathy §1 alignment**:
- §1.1 think-before-coding:**explicitly surfaced F1.4 LIVE switch deferral**(blocking on cred);**explicitly surfaced F4.5 LIVE smoke deferral**(LLM cost + dev server availability);proposed substitute integration smoke achieves same acceptance criteria deterministically;chose Pattern A app registration default for SOP simplicity unless audit pushes Pattern B
- §1.2 simplicity-first:F4 substitute uses TestClient + mocked retrieval / synthesis — zero LLM cost(W6 cycle ~$5-10 / 5 queries avoided);Chris SOPs in dedicated `infrastructure/entra-id/` + `infrastructure/swa/` folders alongside `infrastructure/aca/` + `infrastructure/keyvault/`(consistent topology)
- §1.3 surgical:F4 smoke test 唔 edit `query.py`(W2 design preserved — exception type name in 502 detail accepted as ops-friendly,not stack-trace leak);SOP files NEW only — zero edit to existing infra Bicep / GHA workflows
- §1.4 goal-driven:F4 substitute 5 verifiable cases mapped to acceptance criteria(E1 / E5 / E5 fallback / E12 / F3.5 audit chain);Chris SOPs verifiable via portal apply gate(step-by-step + verification commands + rollback)

**Hard constraints check**:
- H1 architecture lock — ✅ no §3 / §4 component change;F4 substitute exercises wired pipeline;SOPs implementation living docs
- H2 vendor lock — ✅ zero new dep;all SOPs reference already-locked Microsoft Entra ID + Azure SWA stack(architecture.md §6.1 W7 + W8)
- H3 Dify reference — ✅ untouched
- H4 Tier 1 boundary — ✅ Entra ID single-tenant Pattern A documented;multi-tenant + B2B explicit Tier 2 in SOP §Tier 2
- H5 security — ✅ F4 smoke test verifies no Traceback / site-packages leak in error response;SOPs enforce Key Vault for client_secret;Entra ID implicit grant **OFF** documented(msal-react Authorization Code with PKCE only)
- H6 test coverage — ✅ +5 tests for critical C08(error_handlers + middleware)+ C11(auth chain through query route)

### Decisions / OQ summary
- No OQ change(Q11 unchanged decision-level Resolved 2026-05-05;F1.1 IT operational still in-progress external)
- No ADR triggered W8 D4(全 work within architecture.md §6.1 W7+W8 + §6.2 Beta scope)

### Open / blocked
- ⏸ **F1.1 W8 D1+ Q11 IT operational confirm cascade** — Chris external in-progress;cred delivery cascades F1.4 + F1.5 + F3.3 application of SOP
- ⏸ **F1.4 LIVE switch + F1.5 F1.7 LIVE smoke** — W8 D5 OR W9 cascade post-cred per `infrastructure/entra-id/README.md` step 8
- ⏸ **F3.2 SWA custom domain DNS** — Chris infra session + Ricoh corp DNS team;SOP authoring complete pending DNS authority + apply
- ⏸ **F3.3 Entra ID app registration apply** — Chris IT session + portal apply pending Q11 cred confirm
- ⏸ **F3.5 + F4.5 LIVE smoke against real dev server** — W8 D5 OR W9 cascade(Chris dev server availability + LLM spend approval)
- ⏸ F4.4 Documents/chunks/eval/screenshots/debug routes auth wire(W7 D2 字面 scope 之外)— W8 D5 OR W9 cascade
- ⏸ F5 cost dashboard + Langfuse SDK wire — W8 D5
- ⏸ F6 closeout — W8 D5

### Commit reference
- _(W8 D4 commit pending — references progress.md Day 4 + checklist F4 substitute + F3.2 SOP + F3.3 SOP ticked + F1.4 + F1.5 + F4.5 LIVE deferred 標明)_

---

---

## Day 5 — _(pending)_

---

## Retro(填於 W8 D5 末)

### What worked
_(W8 D5 末 fill)_

### What didn't work / unexpected friction
_(W8 D5 末)_

### Surprises / discoveries
_(W8 D5 末)_

### Carry-overs to W09-beta-internal-testing
_(W8 D5 末)_

### ADR triggers
_(W8 D5 末 — ADR-0013 reservation candidate:msal SDK ask-and-approve outcome OR ACA networking topology decision OR Tier 2 trigger)_

### Phase Gate result(per plan.md §3 + architecture.md §7 acceptance)
- G1-G7:_(W8 D5 末)_
- **W8 Beta deploy verdict**:_(W8 D5 末)_ → ready for W9 Beta internal testing / require additional polish

### Phase status
- Closeout commit:_(W8 D5 末)_
- Frontmatter status flipped to `closed`:_(W8 D5 末)_
- Phase W09 kickoff trigger:_(W8 D5 末 — W9 plan = real query log collection + UX iteration + Q6 Real query collection owner trigger per architecture.md §6.1 W9 row)_

---
