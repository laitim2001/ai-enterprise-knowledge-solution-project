---
phase: W08-beta-deploy-sprint2
name: "Beta Hardening Sprint 2 — Azure Container Apps + Static Web Apps + Real Entra ID + LIVE smoke cascade"
sprint_week: W8
start_date: 2026-05-19          # tentative — assumes W7 closed 2026-05-16
end_date: 2026-05-23            # 5 working days
status: draft                   # awaiting Chris W7 closeout sign-off + W8 D1 kickoff approval + Q11 IT operational confirm
spec_refs:
  - architecture.md §6.1 W8 row             # Azure Container Apps + Static Web Apps + cost monitoring + Beta smoke
  - architecture.md §6.2 Beta + Rollout     # W7-W12 timeline
  - architecture.md §7.4 Day-2 Readiness    # Cost dashboard + alerts + runbook
  - architecture.md §8 Risk Register        # R-B1 Entra ID delay + R5 Azure quota + R-B6 compliance
  - components/C11-identity.md              # Real msal SDK + JWKS + redirect flow
  - components/C12-devops.md                # Azure deploy scripts + GHA pipelines + Key Vault
  - components/C07-observability.md         # Langfuse SDK wire + cost dashboard
  - components/C08-api-gateway.md           # Auth router cascade + rate limit Redis-backed
prior_phase: W07-beta-deploy
related_artifacts:
  - docs/03-implementation/beta-plan-v1.md  # W7-W12 phase breakdown
  - docs/01-planning/W07-beta-deploy/progress.md  # Retro § Carry-overs C1-C10
---

# Phase W08 — Beta Hardening Sprint 2(Azure deploy + real Entra ID + LIVE smoke cascade)

> **Plan version**:1.0(draft 2026-05-16 W7 D5 末 closeout cascade — rolling JIT per CLAUDE.md §10 R1)
> **Owner**:Chris(Tech Lead)+ IT(Q11 Entra ID tenant 配合)
> **Approved by**:_(pending Chris W7 closeout sign-off + W8 D1 kickoff approval + Q11 IT operational confirm)_

## 1. Scope

W08 = **Tier 1 Beta deploy phase Sprint 2**(W7-W12)。**Beta hardening Sprint 2** 焦點:Azure Container Apps + Static Web Apps deploy + real Entra ID JWT validation wire + cost monitoring dashboard + LIVE smoke cascade(F1.7 + F3.5 + F4.5 carry-overs from W7)— 為 W9-W10 Beta internal testing 鋪路。

**6 deliverables F1-F6**:
- F1 Real Entra ID auth integration LIVE switch(C11)— W8 D1 IT engagement(Q11 operational confirm)→ D2-D3 msal SDK wire → D4 LIVE switch + F1.7 LIVE smoke
- F2 Azure Container Apps deploy backend(C12)— Dockerfile finalize + ACA spec + GHA CI/CD + Key Vault secrets management
- F3 Azure Static Web Apps deploy frontend(C12)— Next.js 14 SWA build + custom domain + auth integration sync
- F4 LIVE smoke cascade(C07 + C08 + C09 + C10)— F3.5 audit + F4.5 E1+E5+E12 graceful UX trigger on dev tenant
- F5 Cost monitoring + user feedback dashboard(C07)— Langfuse SDK real wire + cost dashboard build per F2.5 + F3 audit data sources
- F6 Phase Gate closeout + W8 retro + W9 kickoff prep

**Pre-condition for W8 promotion**(等 W7 D5 closeout sign-off):
- W7 D5 closeout PASS(G1'-G7 全 PASS expected per W7 retro Phase Gate verdict)
- Chris W8 D1 sign-off
- **Q11 IT operational confirm cascade trigger W8 D1**(per W7 a-revised mock auth strategy 2026-05-05;Tenant Access + App Registration + Owner Identification 3 deliverables IT delivery)

## 2. Deliverables(F1-F6)

### F1 — Real Entra ID auth integration LIVE switch(C11)

- **Component(s)**:**C11** Identity & Access(real MSAL + Entra ID JWT)
- **Spec ref**:`architecture.md §6.1 W8`,`components/C11-identity.md`,`beta-plan-v1.md §2 W8.F1`,`W07 retro § Carry-overs C1-C3`
- **OQ deps**:Q11 operational IT cred cascade(W8 D1 trigger);Q9 Sensitivity / CMK already Resolved
- **Acceptance criteria**:
  - F1.1 W8 D1 IT engagement:Chris confirm Tenant Access + App Registration + Owner Identification(Ricoh 統一 tenant)
  - F1.2 W8 D2-D3 backend real msal_provider wire:`msal` Python SDK + `python-jose` JWT verification(JWKS fetch + signature + audience/issuer + expiry);新 dep ask-and-approve cycle(within Tier 1 vendor scope per architecture.md §3.2 — direct approve 預期);AZURE_TENANT_ID + AZURE_CLIENT_ID + AZURE_CLIENT_SECRET in Azure Key Vault
  - F1.3 W8 D2-D3 frontend real msal_provider wire:`@azure/msal-react` PublicClientApplication + MsalProvider + redirect flow on `frontend/lib/auth/msal_provider.ts`
  - F1.4 W8 D4 LIVE switch:`Settings.feature_auth_mock=False` + `NEXT_PUBLIC_AUTH_MOCK=false` flip;real Entra ID redirect flow exercise
  - F1.5 W8 D4 F1.7 LIVE smoke(carry-over from W7):dev tenant Entra ID end-to-end login flow on local dev server → `/auth/refresh` + `/auth/logout` + `/query` Bearer real-JWT 全 cascade
  - F1.6 W8 D4 unit tests for real MSAL path:JWKS mock + valid signed JWT 200 + expired JWT 401 + audience mismatch 401 + issuer mismatch 401
- **Effort estimate**:2 days(W6 C10 calibration LIVE deploy 2x;real auth wire +SDK install cycle)
- **Owner**:AI(scaffold + tests)+ Chris(W8 D1 IT engagement + W8 D4 LIVE smoke)
- **Cost expected**:~$0(Entra ID Free tier;mock cred dev-only)
- **Blocking**:F1.1 IT cred 是 F1.2-F1.6 cascade trigger;若 W8 D5 仍未 confirm → Beta-blocking R-B1 active monitor

### F2 — Azure Container Apps deploy backend(C12)

- **Component(s)**:**C12** DevOps & Infra(ACA + GHA CI/CD + Key Vault)
- **Spec ref**:`architecture.md §6.1 W8`,`components/C12-devops.md`,`beta-plan-v1.md §2 W8.F2`
- **OQ deps**:none(all infra Q resolved earlier phases)
- **Acceptance criteria**:
  - F2.1 Dockerfile finalize backend(`backend/Dockerfile` already W1 baseline → multi-stage + non-root user + health probe)
  - F2.2 Azure Container Apps spec:2 replicas + 1 vCPU/2GB RAM each + autoscale 1-5 + Managed Identity + Key Vault binding
  - F2.3 GHA CI/CD pipeline:test → ruff → docker build → ACR push → ACA deploy revision → smoke test;rollback via ACA revision swap
  - F2.4 Azure Key Vault secrets:AZURE_OPENAI_API_KEY + AZURE_SEARCH_ADMIN_KEY + COHERE_API_KEY + AZURE_TENANT_ID + AZURE_CLIENT_ID + AZURE_CLIENT_SECRET 從 .env 移到 Key Vault;Settings reads via Managed Identity
  - F2.5 ACA networking:internal ingress with Private Endpoint to Azure AI Search;public ingress for `/health` + auth endpoints only(rest of API behind Front Door + Auth gate)
- **Effort estimate**:1.5 days
- **Owner**:Chris(infra)+ AI(Dockerfile + GHA)
- **Cost expected**:~$45 W8(ACA 2 replicas)per architecture.md §9 cost row

### F3 — Azure Static Web Apps deploy frontend(C12)

- **Component(s)**:**C12** + **C09 + C10** UI
- **Spec ref**:`architecture.md §6.1 W8`,`beta-plan-v1.md §2 W8.F3`
- **OQ deps**:Q10 Visual identity(default neutral tokens W8 acceptable;designer pass post-Beta optional)
- **Acceptance criteria**:
  - F3.1 SWA build pipeline:GHA workflow `next build` → SWA deploy(staging slot)+ environment vars wire
  - F3.2 Custom domain:`ekp.ricoh.com` 或 staging subdomain(Q owner pending W8 D1)
  - F3.3 Auth integration sync:real msal-react redirect URI + post-logout URI register in Entra ID app registration(blocked on F1.1 IT engagement)
  - F3.4 SPA route fallback config(`staticwebapp.config.json`)for Next.js App Router
- **Effort estimate**:1 day
- **Owner**:Chris(custom domain DNS)+ AI(GHA + SWA config)
- **Cost expected**:~$10 W8(SWA Standard tier;Free tier insufficient for custom domain + auth)

### F4 — LIVE smoke cascade(W7 carry-overs)

- **Component(s)**:**C07 + C08 + C09 + C10**
- **Spec ref**:`W07 retro § Carry-overs C5`,`docs/02-architecture/error-cases-E1-E14.md §4 F4.5 LIVE smoke plan`,`docs/02-architecture/audit-log-schema.md §7 F3.5 LIVE smoke verification`
- **OQ deps**:Chris dev server availability + F2 deploy
- **Acceptance criteria**:
  - F4.1 F3.5 LIVE smoke(W7 carry-over):5 query through dev server → Langfuse trace 顯示 audit tags + request_id traceable
  - F4.2 F4.5 LIVE smoke(W7 carry-over):trigger E1(OOS query 拒答)+ E5(LLM timeout retry)+ E12(KB delete during query / chunk_id collision)→ verify graceful UX
  - F4.3 W4/W5 LIVE smoke remainder(W6 C3):PPT E2E + GPT-5.5 latency baseline + Chat UI screenshots
  - F4.4 Documents/chunks/eval/screenshots/debug routes auth wire(W7 D2 字面 scope 之外)cascade per beta-plan-v1.md §2 W8.F1
- **Effort estimate**:0.5 day
- **Owner**:AI + Chris(dev server)
- **Cost expected**:~$10-15(LIVE LLM spend × 5-10 queries)

### F5 — Cost monitoring + user feedback dashboard(C07)

- **Component(s)**:**C07** Observability
- **Spec ref**:`architecture.md §7.4 Day-2 Readiness`,`components/C07-observability.md`,`beta-plan-v1.md §2 W8.F5`,`W07 retro § Carry-overs C4 + C10`
- **OQ deps**:none
- **Acceptance criteria**:
  - F5.1 Real Langfuse SDK wire(W3+ original scope):replace `langfuse_tracer.py:4` W1 stub with actual SDK init + flush hooks per query/retrieval/LLM stage
  - F5.2 Cost dashboard build:Azure OpenAI + Cohere + Blob + AI Search daily spend aggregated(architecture.md §7.4 alert spec);data sources = F2.5 `rate_limit_exceeded` events + F3 `audit_log` events + Langfuse trace LLM cost field
  - F5.3 User feedback loop wire:`/feedback` endpoint(C08 W3 baseline)→ Langfuse comment field;Admin Console feedback view
  - F5.4 Alerts:p95 latency > 30s + API error > 5% + cost spike + CRAG trigger rate > 50%(architecture.md §7.4 spec)
- **Effort estimate**:1 day
- **Owner**:AI + Chris(Langfuse cloud account)
- **Cost expected**:~$0 W8(self-host;Langfuse cloud W11+)

### F6 — Phase Gate closeout + W8 retro + W9 kickoff prep

- **Component(s)**:cross-cutting governance
- **Spec ref**:`PROCESS.md §2.3 closeout`,`beta-plan-v1.md §2 W9 Beta internal testing preview`
- **OQ deps**:F1-F5 verdict outcomes
- **Acceptance criteria**:
  - F6.1 W8 phase Gate verdict landed
  - F6.2 W08 progress.md retro 7 sections complete
  - F6.3 W09 phase folder kickoff:`docs/01-planning/W09-beta-internal-testing/{plan,checklist,progress}.md` draft(W9 = real query log collection + UX iteration + Q6 owner trigger)
  - F6.4 W08 progress.md frontmatter status flipped to `closed`
  - F6.5 R-B1 risk status update:Entra ID delay → mitigated(F1 LIVE landed)or active(F1.1 IT engagement slipped)
  - F6.6 OQ Q11 final operational Resolved sync to `decision-form.md`
- **Effort estimate**:1 day
- **Owner**:AI(draft)+ Chris(approve)

## 3. Success Criteria(Phase Gate to W09)

| # | Criterion | Target | Measure | Block W9?|
|---|---|---|---|---|
| G1 | F1 Real Entra ID LIVE smoke pass on dev tenant | LIVE pass | F1.5 + F1.7 W8 D4 | Yes |
| G2 | F2 Backend deployed to ACA + smoke 200 OK | 200 OK on /health | F2.3 GHA smoke | Yes |
| G3 | F3 Frontend deployed to SWA + custom domain reachable | 200 OK | F3.1 GHA smoke | Yes |
| G4 | F4 LIVE smoke cascade(F3.5 + F4.5)pass | All 5+3 cases | F4.1 + F4.2 | No(some can defer W9)|
| G5 | F5 Cost dashboard live + user feedback wired | Dashboard reachable | F5.2 + F5.3 | No |
| G6 | Backend ruff + frontend lint + type-check 0 errors | All clean | local run | Yes |
| G7 | OQ Q11 final operational Resolved | `Resolved` operational | decision-form.md | Yes |

## 4. Risks(Phase-Specific)

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | Q11 IT operational delay W8 D1+ — F1.1 cred not delivered | Medium | High | W7 a-revised mock auth dev mode preserved as fallback for F1.2-F1.4 dev work;若 W8 D5 仍未 confirm → R-B1 escalation Stakeholder + IT manager |
| R2 | Azure Container Apps deploy first time friction(networking + Key Vault binding)| Medium | Medium | W2 D1 docker-compose baseline preserved as fallback;ACA deploy 走 staging slot 先 catch issue |
| R3 | Real msal SDK install + JWT validation friction | Medium | Medium | Microsoft sample code reference;F1.6 unit tests catch contract mismatch early |
| R4 | F4 LIVE smoke 失敗 — Chris dev server unavailable | Medium | Low | F1.7-mock substitute + F3.4 + F4.4 unit tests provide non-LIVE coverage(W7 D5 已 verify;F3.5 + F4.5 LIVE 為 final cascade)|
| R5 | Cost dashboard 數據源 sparse W8 first day post-deploy | Low | Low | Synthetic data populate + delay full dashboard validation to W9 Beta internal testing onset |

## 5. Day-by-Day Breakdown(rough)

| Day | Date | Focus | Deliverables targeted |
|---|---|---|---|
| D1 | 2026-05-19 | F1.1 Q11 IT engagement + F2.1 Dockerfile finalize + F2.2 ACA spec | F1, F2 |
| D2 | 2026-05-20 | F1.2 backend msal_provider real wire + F1.6 unit tests + F2.3 GHA CI/CD pipeline | F1, F2 |
| D3 | 2026-05-21 | F1.3 frontend msal-react real wire + F2.4 Key Vault + F3.1 SWA build pipeline | F1, F2, F3 |
| D4 | 2026-05-22 | F1.4 LIVE switch + F1.5 + F1.7 LIVE smoke + F3.2-F3.4 SWA deploy + F4 LIVE smoke cascade | F1, F3, F4 |
| D5 | 2026-05-23 | F5 cost dashboard + user feedback + F6 closeout + W09 kickoff prep | F5, F6 |

## 6. Dependencies on Prior Phase

Carry-overs from `W07-beta-deploy/progress.md` retro § Carry-overs C1-C10(全 10 items):
- **C1 W8 D1 Q11 IT operational cascade**(F1.1)
- **C2 W8 D2-D3 real msal_provider wire**(F1.2 + F1.3)
- **C3 W8 D4 LIVE switch + F1.7 LIVE smoke**(F1.4 + F1.5)
- **C4 W8 cost dashboard**(F5.1 + F5.2)
- **C5 F3.5 + F4.5 LIVE smoke**(F4.1 + F4.2)
- **C6 F5.3 Citation card mobile UX** — 仍 deferred(C10 not yet built;rolling-JIT trigger when C10 lands)
- **C7 F5.5 Pixel diff snapshots** — W8 polish window installation
- **C8 Documents/chunks/eval/screenshots/debug routes auth wire** — F4.4 cascade
- **C9 Plan estimate calibration W8** — applied to §2 effort estimates(LIVE deploy 2x)
- **C10 Real Langfuse SDK wire** — F5.1

## 7. Plan Changelog

| Date | Change | Reason | Approver |
|---|---|---|---|
| 2026-05-16 | Initial draft(W7 D5 末 closeout cascade)| Per PROCESS.md §2.3 rolling-JIT kickoff;status=draft pending Chris W7 closeout sign-off + W8 D1 kickoff approval + Q11 IT operational confirm | Chris(pending approve to flip active) |

---

**Lifecycle reminder**:呢份 plan `status=draft`(等 Chris W7 closeout sign-off + W8 D1 sign-off + Q11 IT confirm flip `active`)。重大 deviation 入第 7 節 changelog。
