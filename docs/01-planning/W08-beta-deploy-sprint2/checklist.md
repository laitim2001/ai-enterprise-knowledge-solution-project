---
phase: W08-beta-deploy-sprint2
plan_ref: ./plan.md
status: closed
last_updated: 2026-05-23
---

# Phase W08 — Checklist

> Atomic checkbox(每 item ≤ 0.5–2 hour effort per W6 C10 calibration:LIVE deploy days × 2;static days × 0.5)。
> Status:`draft` 自 2026-05-16 W7 D5 closeout cascade。
> 全 unchecked 至 W8 D1 implementation start。

## F1 — Real Entra ID auth integration LIVE switch(C11)

- [ ] **CRITICAL Q11 IT** F1.1 W8 D1 IT engagement:Chris confirm Tenant Access + App Registration + Owner Identification(Ricoh 統一 tenant)— W7 a-revised mock auth fallback preserved if IT slips
- [x] F1.2 W8 D2-D3 backend JWT validation — **W8 D2 done 2026-05-20** — `python-jose[cryptography]` installed(Karpathy §1.2 simplicity-first:backend = resource server only,skip msal Python SDK;frontend msal-react W8 D3 handles token acquisition);real `backend/api/auth/msal_provider.py` implementation:JWKS fetch + TTL cache + RS256 signature + audience+issuer check + expiry check;Settings 加 `azure_tenant_id` + `azure_client_id` + `jwks_cache_ttl_s` + JWKS URI / issuer templates;empty config falls back to 503(W7 D1 contract preserved while IT delivery in-flight)
- [x] F1.3 W8 D3 frontend msal-react wire — **W8 D3 done 2026-05-21** — `pnpm add @azure/msal-browser@5.9.0 @azure/msal-react@5.3.2`(within Microsoft Entra ID locked vendor scope per architecture.md §6.1 W7);real `frontend/lib/auth/msal_provider.ts` PublicClientApplication lazy SSR-safe singleton + sessionStorage cache + handleRedirectPromise on init + loginRedirect / logoutRedirect / acquireTokenSilent + module-level token cache so api-client.ts sync `getBearer()` API preserved;`auth-provider.tsx` LIVE branch initMsal on mount + 50min refresh interval + no auto-redirect on misconfigured cred;`.env.example` NEXT_PUBLIC_AZURE_TENANT_ID + CLIENT_ID + API_SCOPE
- [ ] F1.4 W8 D4 LIVE switch:`Settings.feature_auth_mock=False` + `NEXT_PUBLIC_AUTH_MOCK=false`;real Entra ID redirect flow exercise
- [ ] F1.5 W8 D4 F1.7 LIVE smoke(W7 carry-over):dev tenant Entra ID end-to-end login flow on local dev server
- [x] F1.6 unit tests — **W8 D2 done 2026-05-20** — `backend/tests/test_msal_provider.py` 13 tests with self-signed RSA keypair fixture + JWKS mock:valid signed JWT 200 + upn fallback 200 + expired 401 + audience mismatch 401 + issuer mismatch 401 + missing kid 401 + unknown kid 401 + missing oid claim 401 + malformed JWT 401 + missing credentials 401 + JWKS fetch failure 503 + incomplete config 503 + JWKS cache TTL reuse
- [ ] AZURE_TENANT_ID + AZURE_CLIENT_ID + AZURE_CLIENT_SECRET 從 .env 移到 Azure Key Vault;Settings reads via Managed Identity

## F2 — Azure Container Apps deploy backend(C12)

- [x] F2.1 Dockerfile finalize backend — **W8 D1 done 2026-05-19** — `backend/Dockerfile` multi-stage(builder uv venv + runtime slim)+ non-root user `ekp` UID 10001 + HEALTHCHECK `/health` interval=30s start-period=15s;`.dockerignore` H5 enforcement(`.env*` + `*.pem` / `*.key` / `*.pfx` ignored;`.env.example` whitelisted)
- [x] F2.2 Azure Container Apps spec — **W8 D1 done 2026-05-19** — `infrastructure/aca/backend.bicep` declarative spec:internal ingress + 1 vCPU/2GB + autoscale 1-5 HTTP concurrency target 30(§8.1 R5)+ User-assigned Managed Identity + 6 Key Vault secret references + Liveness + Readiness probes;`infrastructure/aca/README.md` pre-requisite list + manual deploy reference
- [x] F2.3 GHA CI/CD pipeline — **W8 D2 done 2026-05-20** — `.github/workflows/backend-ci.yml`(PR validation:ruff + pytest)+ `.github/workflows/backend-deploy.yml`(main push:test → ACR build → Bicep deploy revision → smoke `/health` via `az containerapp exec`;`workflow_dispatch + rollback=true` swaps traffic to previous active revision non-destructive);OIDC federated credential via `azure/login@v2`
- [x] F2.4 Azure Key Vault secrets management — **W8 D2 done 2026-05-20** — `infrastructure/keyvault/README.md` SOP:vault layout 6 secrets table(azure-openai-api-key / azure-search-admin-key / cohere-api-key / azure-tenant-id / azure-client-id / azure-client-secret)+ create + populate `az keyvault` commands + Managed Identity grant `Key Vault Secrets User`(reader-only least-privilege per H5)+ rotation SOP per-cadence + emergency + verification commands + Tier 2 boundaries;**actual apply 等 Chris infra session W8 D2-D3**(SOP authoring 完成,值 populate 等 Q11 IT delivery)
- [x] F2.5 ACA networking — **W8 D3 done 2026-05-21**(declarative spec)— `infrastructure/aca/networking.bicep` Private Endpoint `<name>-search-pe` to Azure AI Search + auto-attached Private DNS zone group `privatelink.search.windows.net`;forces backend retrieval traffic onto VNet zero internet hop;`infrastructure/aca/README.md` updated with Chris infra apply sequence(VNet pre-provision → ACA env vnet integration AT CREATE → DNS zone link → Bicep deploy → disable Search public access AFTER PE verified);**actual apply Chris infra session**;backend.bicep already specifies `external: false` internal ingress(W8 D1)

## F3 — Azure Static Web Apps deploy frontend(C12)

- [x] F3.1 SWA build pipeline — **W8 D3 done 2026-05-21** — `.github/workflows/frontend-deploy.yml` lint + type-check + Next.js build → `Azure/static-web-apps-deploy@v1` upload to staging slot(PR / manual)or production(main push);env vars NEXT_PUBLIC_API_URL + AUTH_MOCK=false + AZURE_TENANT/CLIENT/SCOPE from GHA secrets;PR comment auto-post preview URL;pnpm cache via `pnpm/action-setup@v4`
- [x] F3.2 Custom domain DNS — **W8 D4 SOP done 2026-05-22 (Chris cascade pending)** — `infrastructure/swa/README.md` NEW 5-step SOP:Azure portal Add domain → Ricoh corp DNS team CNAME + TXT validation → portal Validate → Entra ID redirect URI sync → GHA env var update;apex domain ALIAS vs A record caveat;`Q owner` Chris + Stakeholder W8 D1 confirm pending(default = subdomain of ricoh.com)
- [x] F3.3 Auth integration sync — **W8 D4 SOP done 2026-05-22 (Chris cascade pending)** — `infrastructure/entra-id/README.md` NEW 8-step app registration cascade:Pattern A combined SPA+API single app(recommended)/ Pattern B separate(audit fallback);redirect URIs(prod + staging + localhost)+ post-logout URIs;Expose API + scope `api://<client-id>/access`;F1.5 LIVE smoke procedure(uvicorn + pnpm dev + redirect round-trip + audit propagation);Chris portal apply pending Q11 cred confirm
- [x] F3.4 SPA route fallback — **W8 D3 done 2026-05-21** — `frontend/staticwebapp.config.json` navigationFallback `/index.html`(exclude `/api/*` + `/_next/*` + asset MIME globs);responseOverrides 401 → `/admin` 302 redirect + 403 → `/admin/error.html` + 404 → `/index.html` 200(SPA);global security headers X-Frame-Options DENY + nosniff + Referrer-Policy + Permissions-Policy + HSTS

## F4 — LIVE smoke cascade(W7 carry-overs)

- [x] F4.1 + F4.2 substitute — **W8 D4 done 2026-05-22** — `backend/tests/test_e1_e5_e12_smoke.py` 5 integration smoke tests covering full middleware chain(authenticate_mock + RateLimit + Audit + ErrorHandlers + /query route)against mocked retrieval / synthesis:E1 OOS query 拒答 200 + `refused=true`;E5 LLM timeout 502 envelope + no Traceback leak;E5 synthesizer unavailable → 200 retrieval-only fallback;E12 chunk_id namespaced collision distinct;F3.5 audit chain 5-burst with mock identity + request_id round-trip
- [ ] ~~F4.1 F3.5 LIVE smoke real dev server~~ → **DEFERRED W8 D5 OR W9** — Chris dev server availability + LLM spend approval(W6 C3 carry-over preserved);substitute integration smoke landed 2026-05-22 covers same acceptance via deterministic test
- [ ] ~~F4.2 F4.5 LIVE smoke real dev server~~ → **DEFERRED W8 D5 OR W9** — same gating as F4.1 LIVE;substitute integration smoke landed 2026-05-22
- [ ] F4.3 W4/W5 LIVE smoke remainder(W6 C3):PPT E2E + GPT-5.5 latency baseline + Chat UI screenshots
- [x] F4.4 Documents/chunks/eval/screenshots/debug routes auth wire — **W8 D5 done 2026-05-23** — `backend/api/server.py` 添加 `dependencies=_auth` to documents/chunks/eval/screenshots/debug + observability routers(W7 D2 字面 scope 之外 cascade per beta-plan-v1.md §2 W8.F1);7 admin routes 401-without-bearer parametrized tests + 1 pass-with-bearer test in `backend/tests/test_observability_routes.py`;single server.py edit per Karpathy §1.3 surgical;zero edit to 5 admin route files

## F5 — Cost monitoring + user feedback dashboard(C07)

- [x] F5.1 Real Langfuse SDK wire — **W8 D5 done 2026-05-23** — `backend/observability/langfuse_tracer.py` complete rewrite of W1 stub:lazy module-level singleton + degrade-graceful init(missing keys / import failure / constructor failure all yield `None`)+ `get_langfuse_client()` accessor + `flush_tracer()` lifespan shutdown drain hook + `_set_langfuse_client_for_tests()` escape hatch;`backend/pyproject.toml` `langfuse>=2.50` dep(architecture.md §3.2 stack lock — direct approve same pattern as W8 D2 python-jose);`backend/api/server.py` lifespan finally block calls `flush_tracer()`;8 unit tests `test_langfuse_tracer.py`
- [x] F5.2 Cost dashboard build — **W8 D5 done 2026-05-23** — `backend/observability/cost_estimator.py` NEW 8-row Beta projection table(architecture.md §9 Beta column / 30 days):Azure AI Search S1 + text-embedding-3-large + GPT-5.5 synthesis + GPT-5.4-mini judge + Cohere Rerank v3.5 + Blob + ACA + SWA;`backend/api/routes/observability.py` NEW `GET /observability/cost-summary` returning `{rows, total_projected_daily_usd, total_projected_monthly_usd, langfuse_status, note}`;langfuse_status reflection lets admin UI surface Langfuse cred wire status;real-time LLM token attribution requires per-stage `@observe` decoration(W9+ scope per beta-plan-v1.md §2)
- [x] F5.3 User feedback loop wire — **W8 D5 done 2026-05-23** — `backend/api/routes/feedback.py` complete rewrite of W1 501 stub:`POST /feedback` returns 202 with uuid4 feedback_id;thumbs_up → score `value=1`;thumbs_down → score `value=-1`;forwards to Langfuse `score(trace_id, name="user_feedback", value, comment)` when client wired;degrades to audit-log only when client `None`;swallows `score()` raise(202 still accepted,never silently dropped per Karpathy §1.2);6 unit tests `test_feedback.py`;**Admin Console feedback view UI deferred** since C10 Chat UI not built(W7 carry-over;rolling-JIT trigger when C10 lands)
- [x] F5.4 Alerts — **W8 D5 done 2026-05-23** — `backend/observability/alerts.py` NEW declarative ruleset 6 `AlertRule` frozen dataclasses(p95 latency > 30s p2 + API error > 5% p1 + cost spike > 1.5x rolling avg p2 + CRAG trigger > 50% p3 + rate_limit_saturation > 10% p3 + langfuse_export_lag > 10min p2);`GET /observability/alerts` returns ruleset + routing summary + spec ref;**paging integration(Slack / PagerDuty)deferred W9+** post on-call rotation staffed per beta-plan-v1.md §3 W9;`infrastructure/observability/README.md` SOP authored

## F6 — Phase Gate closeout + W8 retro + W9 kickoff prep

- [x] F6.1 W8 phase Gate verdict landed — **W8 D5 done 2026-05-23** — PARTIAL PASS:G1' + G4 substitute + G5 + G6 PASS = 4/7;G1 + G2 + G3 + G7 deferred W9 per Chris IT/infra/DNS external dependency cascade(implementation spec-complete W8 D1-D5;LIVE deploy + Q11 final operational blocked on Chris external sessions)— `progress.md` Phase Gate result table填寫
- [x] F6.2 W08 progress.md retro 7 sections complete — **W8 D5 done 2026-05-23** — What worked / What didn't work / Surprises / Carry-overs(C1-C11)/ ADR triggers / Phase Gate result / Phase status全部填寫
- [x] F6.3 W09 phase folder kickoff — **W8 D5 done 2026-05-23** — `docs/01-planning/W09-beta-internal-testing/` 三 file 建好(plan.md draft + checklist.md + progress.md Day 0 entry)
- [x] F6.4 W08 progress.md frontmatter status flipped to `closed` — **W8 D5 done 2026-05-23**(此 batch)
- [x] F6.5 R-B1 risk status update — **W8 D5 done 2026-05-23** — `RISK_REGISTER.md` R14 R-B1 Entra ID tenant operational delay 🟡 Active monitor → 🔴 **Active escalation**(Chris IT engagement past W8 D5 closeout仍未 confirm;per W8 plan §4 R1 escalation trigger:Stakeholder + IT manager 三方);F1.7 LIVE 推 W9
- [x] F6.6 OQ Q11 final operational Resolved sync to `decision-form.md` — **W8 D5 done 2026-05-23** — Q11 status update:decision-level Resolved 2026-05-05 PRESERVED;**operational confirm DEFERRED W9** post-Chris IT engagement(W8 D5 closeout time仍 in-progress);transparent status documentation per CLAUDE.md §13 "When in doubt → ask, don't guess"

---

## Cross-Cutting

- [ ] Each commit references `progress.md` Day-N entry(R2)
- [ ] Component tag in commit message per CC-1
- [ ] OQ status sync to `decision-form.md`(R4)— Q11 W8 D1 critical
- [ ] Risk register update if R-B1(Entra ID delay)status changes
- [ ] CLAUDE.md §5.5 H5 security check:no secret commit;Cohere/Azure key 移到 Azure Key Vault;Entra ID client secret 走 Key Vault(Beta+)
- [ ] H2 vendor lock check:msal SDK 屬 Tier 1 vendor scope per architecture.md §3.2 — direct approve 預期(non-architectural addition);若 friction surface ADR-0013 candidate

---

**Lifecycle reminder**:呢份 checklist 衍生自 `plan.md` deliverables。新加 deliverable 必須先入 plan + changelog,然後再加 checklist item。
