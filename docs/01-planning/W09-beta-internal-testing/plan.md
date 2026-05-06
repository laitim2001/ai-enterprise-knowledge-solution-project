---
phase: W09-beta-internal-testing
name: "Beta Internal Testing — Chris IT/infra/DNS apply cascade + LIVE deploy + real query log collection"
sprint_week: W9
start_date: 2026-05-26          # tentative — assumes W8 closed 2026-05-23
end_date: 2026-05-30            # 5 working days
status: active                  # flipped draft→active 2026-05-26 W9 D1 kickoff(W8 D5 closeout PARTIAL PASS cascade;A+B parallel deliverable batch — alignment memo + observe wrapper landed before 三方 session per Karpathy §1.1 prep-while-blocked)
spec_refs:
  - architecture.md §6.1 W9 row             # Beta internal testing + real query log collection + UX iteration
  - architecture.md §6.2 Beta + Rollout     # W7-W12 timeline
  - architecture.md §7.4 Day-2 Readiness    # Cost dashboard + alerts + runbook
  - architecture.md §8 Risk Register        # R-B1 Entra ID delay + R5 Azure quota
  - components/C11-identity.md              # Real msal SDK + JWKS + redirect flow
  - components/C12-devops.md                # Azure deploy + ACA + SWA + Key Vault
  - components/C07-observability.md         # Langfuse SDK + cost dashboard + alerts
  - components/C09-admin-console.md         # Admin Console UI iteration
prior_phase: W08-beta-deploy-sprint2
related_artifacts:
  - docs/03-implementation/beta-plan-v1.md  # W7-W12 phase breakdown
  - docs/01-planning/W08-beta-deploy-sprint2/progress.md  # Retro § Carry-overs C1-C11
  - docs/01-planning/RISK_REGISTER.md       # R14 R-B1 🔴 Active escalation 2026-05-23
---

# Phase W09 — Beta Internal Testing(Chris IT/infra/DNS apply cascade + LIVE deploy + real query log collection)

> **Plan version**:1.0(draft 2026-05-23 W8 D5 末 closeout cascade — rolling JIT per CLAUDE.md §10 R1)
> **Owner**:Chris(Tech Lead + IT engagement + infra apply + DNS apply)+ Stakeholder(W9 D1 三方 alignment session for R-B1 escalation)+ AI(LIVE smoke verification + UX iteration support)
> **Approved by**:_(pending Chris W8 closeout sign-off + W9 D1 三方 alignment outcome + Q11 final operational Resolved)_

## 1. Scope

W09 = **Tier 1 Beta internal testing phase entry**(W7-W12)。**Beta deploy LIVE cascade + internal user onboarding** 焦點:Chris IT engagement(Q11 final operational confirm)+ Chris infra session(F2.3 ACA deploy + F2.4 Key Vault populate + F2.5 ACA networking apply)+ Chris DNS session(F3.2 SWA custom domain apply)+ F1.4 LIVE switch + F1.5 + F1.7 LIVE smoke verification + W7 D5 deferred LIVE smoke cascade(F3.5 + F4.5)+ W9 D3 onset Beta internal user onboarding(per Q7 RAPO 內部 + 1-2 友好部門)+ real query log collection scaffolding(per Q6 owner trigger)+ UX iteration based on first-cohort feedback。

**6 deliverables F1-F6**:
- F1 R-B1 escalation alignment + Q11 final operational Resolved(W9 D1 三方 session)
- F2 Chris infra/IT/DNS apply cascade — F1.4 LIVE switch + F2.3 ACA deploy + F2.4 KV populate + F2.5 networking + F3.2 DNS + F3.3 Entra ID portal apply
- F3 LIVE smoke verification — F1.5 + F1.7 + F3.5 + F4.5(per W7 + W8 carry-overs C2 + C3 + C5)
- F4 Beta internal user onboarding — Q7 user roster + onboarding doc + first-cohort access provisioning
- F5 Real query log collection scaffolding(per Q6 owner trigger)+ progressive `@observe` decoration(F5.1 SDK accessor adopted by query/synthesizer/crag stages)
- F6 Phase Gate closeout + W9 retro + W10 kickoff prep

**Pre-condition for W9 promotion**(等 W8 D5 closeout sign-off):
- W8 D5 closeout PARTIAL PASS landed(G1'+G4 substitute+G5+G6 PASS;G1+G2+G3+G7 deferred W9 acknowledged)
- Chris W8 closeout sign-off
- **Q11 final operational confirm cascade trigger W9 D1**(per W8 D5 escalation R-B1 — 三方 Stakeholder + IT manager + Chris alignment session)
- Chris dev server availability for LIVE smoke window

## 2. Deliverables(F1-F6)

### F1 — R-B1 escalation alignment + Q11 final operational Resolved

- **Component(s)**:cross-cutting governance(impacts **C11** + **C12** + **C09** + **C10**)
- **Spec ref**:`RISK_REGISTER.md R14 R-B1` 🔴 Active escalation 2026-05-23,`W08 retro § Carry-overs C1`,`beta-plan-v1.md §2 W8.F1`
- **OQ deps**:Q11 final operational Resolved(this phase trigger)
- **Acceptance criteria**:
  - F1.1 W9 D1 三方 alignment session:Stakeholder + IT manager + Chris — IT delivery commitment date confirmed;若仍 push → escalation Stakeholder cycle re-engage
  - F1.2 IT cred delivery:`AZURE_TENANT_ID` + `AZURE_CLIENT_ID` + (optional Pattern B `AZURE_CLIENT_SECRET`)populated to Key Vault per `infrastructure/keyvault/README.md`
  - F1.3 Q11 status update:`Resolved` operational(replace W8 D5 deferred-pending state);decision-form.md sync
  - F1.4 R-B1 status update:🔴 Active escalation → 🟢 Mitigated post-IT delivery(or 🔴 Open if escalation cycle slips)
- **Effort estimate**:0.5 day(三方 session typically half-day);若 escalation cycle 多輪 → spread W9 D1-D3
- **Owner**:Chris + Stakeholder + IT manager(Chris coordinates)
- **Cost expected**:~$0(governance work)
- **Blocking**:F1.2 IT cred is F2 LIVE deploy + F3 LIVE smoke gate

### F2 — Chris infra/IT/DNS apply cascade

- **Component(s)**:**C12** DevOps & Infra(primary)+ **C11** Identity & Access
- **Spec ref**:`infrastructure/aca/README.md`,`infrastructure/keyvault/README.md`,`infrastructure/swa/README.md`,`infrastructure/entra-id/README.md`,`W08 retro § Carry-overs C2-C4`
- **OQ deps**:F1.2 IT cred delivery
- **Acceptance criteria**:
  - F2.1 Backend ACA deploy via `.github/workflows/backend-deploy.yml`(W8 D2 spec ready)— main push triggers ACR build + Bicep deploy revision + smoke `/health` via `az containerapp exec`;rollback path verified
  - F2.2 Key Vault populate:6 secrets(azure-openai-api-key + azure-search-admin-key + cohere-api-key + azure-tenant-id + azure-client-id + azure-client-secret)per `infrastructure/keyvault/README.md`;Managed Identity grant `Key Vault Secrets User`
  - F2.3 ACA networking apply:`infrastructure/aca/networking.bicep` Private Endpoint to Azure AI Search + Private DNS zone group attach(per W8 D3 declarative spec);disable Search public access AFTER PE verified
  - F2.4 Entra ID app registration apply:Pattern A 8-step per `infrastructure/entra-id/README.md`(redirect URIs + post-logout URIs + Expose API scope + admin consent)
  - F2.5 SWA custom domain apply:`ekp-beta.ricoh.com`(or stakeholder-confirmed name)per `infrastructure/swa/README.md`(Azure portal Add → Ricoh corp DNS team CNAME + TXT → Validate → cert provisioned)
  - F2.6 SWA deploy via `.github/workflows/frontend-deploy.yml`(W8 D3 spec ready)
- **Effort estimate**:2 days(W6 C10 calibration LIVE deploy 2x;multi-stakeholder coordination cycle)
- **Owner**:Chris(infra apply)+ AI(GHA verification + smoke test)
- **Cost expected**:~$15-25 W9(ACA 1-5 replicas + SWA Standard + KV ops + first-week steady-state)

### F3 — LIVE smoke verification(W7 + W8 carry-overs)

- **Component(s)**:**C07 + C08 + C11 + C09 + C10**
- **Spec ref**:`W08 retro § Carry-overs C2 + C3 + C5`,`error-cases-E1-E14.md §4 F4.5 LIVE smoke plan`,`audit-log-schema.md §7 F3.5 LIVE smoke verification`
- **OQ deps**:F2 deploy + Chris dev server availability
- **Acceptance criteria**:
  - F3.1 F1.5 LIVE smoke:dev tenant Entra ID end-to-end login flow(uvicorn + pnpm dev or staged ACA + SWA)→ `/auth/refresh` + `/auth/logout` + `/query` Bearer real-JWT cascade per `infrastructure/entra-id/README.md` step 8
  - F3.2 F1.7 LIVE smoke acceptance(W7 plan §3 G1):full redirect round-trip + `/query` 200 with real identity propagated through audit pipeline(Langfuse trace tag `user_id=<real oid>`)
  - F3.3 F3.5 LIVE smoke(W7 carry-over):5 query through dev / staged server → Langfuse trace 顯示 audit tags + request_id traceable
  - F3.4 F4.5 LIVE smoke(W7 carry-over):trigger E1(OOS query 拒答)+ E5(LLM timeout retry)+ E12(KB delete during query / chunk_id collision)→ verify graceful UX
  - F3.5 W4/W5 LIVE smoke remainder(W6 C3):PPT E2E + GPT-5.5 latency baseline + Chat UI screenshots
- **Effort estimate**:1 day
- **Owner**:AI + Chris(dev server / staged env)
- **Cost expected**:~$10-15(LIVE LLM spend × 10-15 queries)

### F4 — Beta internal user onboarding

- **Component(s)**:**C09 + C10 + C11**(adoption surface)+ governance
- **Spec ref**:`architecture.md §6.1 W9-10`,`beta-plan-v1.md §3 W9-W10`,Q7 Resolved(RAPO 內部 + 1-2 友好部門 + Chris pre-identify W7-W8)
- **OQ deps**:F2 deploy + F3 LIVE smoke pass + Q7 final user roster
- **Acceptance criteria**:
  - F4.1 Final user roster confirm with Chris(per Q7;~5-10 first-cohort)
  - F4.2 Onboarding doc:1-page how-to-use(login + query example + feedback button + reporting bug channel)
  - F4.3 Entra ID app access provision:add users to app registration(or assign role if Pattern B)
  - F4.4 First-cohort kick-off ping(Slack / email)+ feedback intake channel
- **Effort estimate**:0.5 day
- **Owner**:Chris(user coordination)+ AI(onboarding doc draft)
- **Cost expected**:~$0(communication work)

### F5 — Real query log collection scaffolding + progressive @observe decoration

- **Component(s)**:**C07** Observability + **C04 + C05** stages
- **Spec ref**:`architecture.md §3.1`,`components/C07-observability.md`,Q6 Real query collection owner trigger,`W08 retro § Carry-overs C8`
- **OQ deps**:Q6 Real query collection owner(W9 trigger per architecture.md §6.1 W9 row)
- **Acceptance criteria**:
  - F5.1 Q6 owner identification:Chris confirm with Stakeholder W9 D1 — typically Chris self-assign(per Q14 ground truth pattern)or Beta cohort lead
  - F5.2 Progressive `@observe` decoration on query/synthesizer/crag stages:wire Langfuse SDK accessor(W8 D5 F5.1 ready)to per-stage trace capture so `/observability/cost-summary` 升 from static projection to real-time attribution
  - F5.3 Real query log scaffolding:audit_log → query corpus(deduplicated;PII-stripped per H5)— stored to `docs/03-implementation/beta-real-queries-W9-W10.yaml`(or DB)
  - F5.4 Daily query distribution review(W9 D2-D5 + W10 daily):surface frequent-query patterns + failed queries → feeds Q15 manual update frequency + Q21 reranker alternative consideration
- **Effort estimate**:1 day
- **Owner**:AI(@observe wire + scaffolding script)+ Chris(daily review)
- **Cost expected**:~$0 W9(infrastructure-only)

### F6 — Phase Gate closeout + W9 retro + W10 kickoff prep

- **Component(s)**:cross-cutting governance
- **Spec ref**:`PROCESS.md §2.3 closeout`,`beta-plan-v1.md §2 W10 staged rollout preview`
- **OQ deps**:F1-F5 verdict outcomes
- **Acceptance criteria**:
  - F6.1 W9 phase Gate verdict landed
  - F6.2 W09 progress.md retro 7 sections complete
  - F6.3 W10 phase folder kickoff:`docs/01-planning/W10-beta-iteration/{plan,checklist,progress}.md` draft(W10 = UX iteration + bug fix + W11 staged rollout 25% prep)
  - F6.4 W09 progress.md frontmatter status flipped to `closed`
  - F6.5 R-B1 closure(if Q11 + LIVE smoke landed)or status update(if escalation cycle ongoing)
  - F6.6 OQ Q11 final operational Resolved + Q6 Real query collection owner Resolved sync to `decision-form.md`
- **Effort estimate**:0.5 day
- **Owner**:AI(draft)+ Chris(approve)

## 3. Success Criteria(Phase Gate to W10)

| # | Criterion | Target | Measure | Block W10?|
|---|---|---|---|---|
| G1 | F1 R-B1 escalation resolved + Q11 final operational Resolved | `Resolved` operational | decision-form.md | Yes |
| G2 | F2 Chris infra/IT/DNS apply cascade complete | All 6 sub-gates landed | F2.1-F2.6 verification | Yes |
| G3 | F3 LIVE smoke verification(F1.5 + F1.7 + F3.5 + F4.5)pass | All cases verified | F3.1-F3.5 | Yes |
| G4 | F4 Beta internal user onboarding 5-10 first cohort access provisioned | Cohort active | F4.1-F4.4 | No(can defer to W10 if F2/F3 slips)|
| G5 | F5 Real query log scaffolding + first batch collected(W9 D5)| ≥ 50 queries logged | `beta-real-queries-W9-W10.yaml` row count | No |
| G6 | Backend ruff + frontend lint + type-check 0 errors | All clean | local + CI | Yes |
| G7 | Q6 Real query collection owner Resolved | `Resolved` | decision-form.md | No(can carry W10) |

## 4. Risks(Phase-Specific)

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | R-B1 escalation cycle 多輪 — Q11 final operational delay 過 W9 | Medium | High | W9 D1 三方 alignment session — IT delivery commitment date 必須 explicit;若仍 push → Stakeholder cycle re-engage(W11-W12 production launch milestone risk transparency surface)|
| R2 | Azure infra apply first time friction(networking + KV + Managed Identity binding)| Medium | Medium | W8 D1-D3 declarative Bicep spec complete;ACA deploy 走 staging revision 先 catch issue;rollback path GHA workflow ready |
| R3 | F1.7 LIVE smoke 失敗 — real Entra ID tenant config drift from SOP | Low | High | `infrastructure/entra-id/README.md` step 8 explicit verification commands + audit propagation check;F1.6 13 unit tests catch contract mismatch early;mock-substitute fallback if LIVE 走 not work |
| R4 | Q7 user roster 縮水 — Beta first cohort access slow | Medium | Low | Default = RAPO 內部 + Chris pre-identify(W7-W8 carry-over);若 friendly department slow → first cohort still ≥ 3 RAPO users;W10 expand cohort cycle |
| R5 | Real query log collection low volume(< 50 queries W9 D5)| Medium | Medium | Onboarding doc emphasizes query examples + feedback loop;W10 expand if persistent low — signals adoption issue R1(architecture.md §8.1 R1 Shadow AI displacement)|
| R6 | LIVE LLM spend 超 budget — first cohort heavy queries | Low | Medium | architecture.md §8.1 R5 rate limit 50 req/min/user already wired W7;cost dashboard alert `cost_spike > 1.5x rolling 7-day avg` per W8 D5 F5.4 ruleset(though paging integration W9+ — manual daily review fallback)|

## 5. Day-by-Day Breakdown(rough)

| Day | Date | Focus | Deliverables targeted |
|---|---|---|---|
| D1 | 2026-05-26 | F1 三方 alignment session + Q11 cred IT delivery + F2.4 KV populate kickoff | F1, F2 |
| D2 | 2026-05-27 | F2 Chris infra apply cascade(ACA deploy + networking + Entra ID portal + SWA DNS)+ F5.1 Q6 owner | F2, F5 |
| D3 | 2026-05-28 | F3 LIVE smoke cascade(F1.5 + F1.7 + F3.5 + F4.5)+ F4 onboarding doc + first-cohort access | F3, F4 |
| D4 | 2026-05-29 | F4 first-cohort kick-off ping + F5.2 progressive @observe + F5.3 query log scaffolding | F4, F5 |
| D5 | 2026-05-30 | F5.4 daily query review + F6 closeout + W10 kickoff prep | F5, F6 |

## 6. Dependencies on Prior Phase

Carry-overs from `W08-beta-deploy-sprint2/progress.md` retro § Carry-overs C1-C11:
- **C1 Q11 IT operational confirm cascade**(F1)— W8 D5 escalation 觸發
- **C2 F1.4 LIVE switch + F1.5 + F1.7 LIVE smoke**(F3.1 + F3.2)
- **C3 F3.2 SWA DNS + F3.3 Entra ID portal apply**(F2.4 + F2.5)
- **C4 F2.4 Key Vault populate + F2.5 ACA networking Bicep apply**(F2.2 + F2.3)
- **C5 F4.3 W4/W5 LIVE smoke remainder + F3.5 + F4.5 LIVE smoke real dev server**(F3.3 + F3.4 + F3.5)
- **C6 F5.3 Admin Console feedback view UI** — 仍 deferred(C10 not yet built;rolling-JIT trigger when C10 lands)
- **C7 F5.5 Pixel diff snapshots installation** — W9+ if Vitest/Playwright harness installed(non-Beta-blocking)
- **C8 W9+ progressive `@observe` decoration on query/synthesizer/crag stages**(F5.2)
- **C9 Q6 Real query collection owner trigger**(F5.1)
- **C10 W9 Beta internal testing user roster**(F4.1)
- **C11 dependency_overrides cleanup pattern** — W9+ test infrastructure cleanup window(non-Beta-blocking)

## 7. Plan Changelog

| Date | Change | Reason | Approver |
|---|---|---|---|
| 2026-05-23 | Initial draft(W8 D5 末 closeout cascade)| Per PROCESS.md §2.3 rolling-JIT kickoff;status=draft pending Chris W8 closeout sign-off + W9 D1 三方 alignment outcome | Chris(pending approve to flip active) |
| 2026-05-26 | status `draft → active` | W9 D1 kickoff cascade — A+B parallel deliverables landed pre-session(R-B1 alignment memo for Chris + F5.2-kickoff observe wrapper + 3-stage decoration);F1.1 三方 session itself is human-coordinated external work | Chris implicit(W8 closeout sign-off cascade) |

---

**Lifecycle reminder**:呢份 plan `status=draft`(等 Chris W8 closeout sign-off + W9 D1 三方 alignment outcome + Q11 final operational confirm flip `active`)。重大 deviation 入第 7 節 changelog。
