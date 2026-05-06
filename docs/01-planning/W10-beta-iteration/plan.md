---
phase: W10-beta-iteration
name: "Beta Iteration — IT cred-bridge polish + LIVE deploy cascade trigger window + W11 staged rollout prep"
sprint_week: W10
start_date: 2026-06-02            # tentative — assumes W9 closed 2026-05-30 + IT cred target early June real
end_date: 2026-06-06              # 5 working days
status: closed                    # `active → closed` flipped 2026-06-06 W10 D5 closeout cascade(PARTIAL PASS verdict — Track B complete + Track A pending IT cred populate event per W9 D1 三方 outcome cascade pattern)
spec_refs:
  - architecture.md §6.1 W10 row             # UX iteration + W11 staged rollout prep
  - architecture.md §6.2 Beta + Rollout      # W7-W12 timeline
  - architecture.md §7.4 Day-2 Readiness     # Cost dashboard + alerts + runbook real-incident exercise
  - architecture.md §8 Risk Register         # R-B1 closure trigger
  - components/C07-observability.md          # Progressive observe upgrade + real query log live plumbing
  - components/C08-api-gateway.md            # Streaming observe variant
  - components/C11-identity.md               # Q11 final operational Resolved
  - components/C12-devops.md                 # F2 LIVE deploy + F3 LIVE smoke trigger
prior_phase: W09-beta-internal-testing
related_artifacts:
  - docs/03-implementation/beta-plan-v1.md   # W7-W12 phase breakdown
  - docs/01-planning/W09-beta-internal-testing/progress.md  # Retro § Carry-overs
  - docs/01-planning/RISK_REGISTER.md        # R14 R-B1 closure trigger
---

# Phase W10 — Beta Iteration(IT cred-bridge polish + LIVE deploy trigger window + W11 staged rollout prep)

> **Plan version**:1.0(draft 2026-05-30 W9 D5 末 closeout cascade — rolling JIT per CLAUDE.md §10 R1)
> **Owner**:Chris(Tech Lead + IT engagement follow-through + Beta cohort onboarding lead)+ AI(implementation polish + W11 prep)
> **Approved by**:_(pending Chris W9 closeout sign-off + IT cred populate trigger early June real)_

## 1. Scope(rolling-JIT W9 D5 末 draft;refined post-IT-cred populate)

W10 = **IT cred-bridge transition phase**(W7-W12)。**Two parallel tracks**:
- **Track A**:**LIVE deploy cascade trigger window** — IT cred 預期 early June real-calendar deliver(per W9 D1 三方 outcome);once cred populated → F1.2 + F2.1-F2.6 + F3 LIVE smoke + F4 cohort onboarding cascade in single multi-stakeholder coordination cycle
- **Track B**:**Implementation polish + W11 staged rollout prep**(IT-cred-independent work continues regardless of Track A timing):progressive observe wire on remaining stages + real query log live plumbing scaffold + runbook real-incident exercise prep + eval-set augmentation pipeline + onboarding doc final review

**6 deliverables F1-F6**:
- F1 Q11 final operational Resolved post IT cred populate(Track A — early June trigger)
- F2 Chris infra/IT/DNS apply cascade execution + F1.4 LIVE switch(Track A)
- F3 LIVE smoke verification + F4 Beta cohort onboarding(Track A)
- F4 Implementation polish(progressive observe wire + streaming variant + eval-set augmentation prep)— Track B
- F5 W11 staged rollout readiness(runbook real-incident exercise + cost dashboard real-time wire + onboarding doc final review)— Track B
- F6 Phase Gate closeout + W10 retro + W11 staged rollout phase folder kickoff

**Pre-condition for W10 promotion**(等 W9 D5 closeout sign-off):
- W9 D5 closeout PARTIAL PASS landed(F5 + F4.2 + F6 closeout completed without IT cred per W9 D1 三方 outcome cascade)
- Chris W9 closeout sign-off
- **IT cred populate trigger event**(Track A activation)— could fire any time W10 D1-D5 OR slip to W11 if IT delivery further delays
- Beta cohort access list final per Q7(Chris with Stakeholder)

## 2. Deliverables(F1-F6)

### F1 — Q11 final operational Resolved + R-B1 closure(Track A)

- **Component(s)**:**C11** Identity & Access(primary)+ governance
- **Spec ref**:`infrastructure/entra-id/README.md` step 1-7,`docs/decision-form.md` Q11,`RISK_REGISTER.md` R14
- **OQ deps**:Q11 final operational pending IT cred(W9 D1 三方 alignment outcome)
- **Acceptance criteria**:
  - F1.1 IT cred delivered(`AZURE_TENANT_ID` + `AZURE_CLIENT_ID` per Pattern A)— trigger event
  - F1.2 Cred populated to Key Vault per `infrastructure/keyvault/README.md`
  - F1.3 `decision-form.md` Q11 status `decision-level Resolved + operational committed early June real` → `Resolved` operational(final)
  - F1.4 `RISK_REGISTER.md` R14 R-B1 status 🟡 Active monitor → 🟢 **Mitigated**(closure)
- **Effort estimate**:0.5 day(post-IT-delivery cascade is mechanical per W8 D2-D4 SOPs ready)
- **Owner**:Chris(infra apply)+ AI(governance docs sync)
- **Cost expected**:~$0(governance work)

### F2 — Chris infra/IT/DNS apply cascade execution + F1.4 LIVE switch

- **Component(s)**:**C12** DevOps & Infra(primary)+ **C11**
- **Spec ref**:`infrastructure/aca/`,`infrastructure/keyvault/`,`infrastructure/swa/`,`infrastructure/entra-id/` SOPs(W8 D1-D4 authored ready)
- **OQ deps**:F1.1 IT cred delivery
- **Acceptance criteria**:
  - F2.1 ACA backend deploy via `.github/workflows/backend-deploy.yml`
  - F2.2 Key Vault populate 6 secrets + Managed Identity grant
  - F2.3 ACA networking apply(Private Endpoint to Azure AI Search;disable Search public access AFTER PE verified)
  - F2.4 Entra ID app registration apply(Pattern A 8-step)
  - F2.5 SWA custom domain apply(`ekp-beta.ricoh.com` per Ricoh corp DNS team CNAME + TXT)
  - F2.6 SWA frontend deploy via `.github/workflows/frontend-deploy.yml`
  - F2.7 F1.4 LIVE switch:`Settings.feature_auth_mock=False` env override + ACA revision restart;`NEXT_PUBLIC_AUTH_MOCK=false` GHA env update + SWA re-deploy
- **Effort estimate**:2 days(W6 C10 calibration LIVE deploy 2x;multi-stakeholder Chris infra session)
- **Owner**:Chris(infra apply)+ AI(GHA verification + smoke test)
- **Cost expected**:~$15-25(ACA 1-5 replicas + SWA + KV ops + first-week steady-state)

### F3 — LIVE smoke verification + F4 Beta cohort onboarding(Track A)

- **Component(s)**:**C07 + C08 + C11 + C09 + C10**
- **Spec ref**:W7+W8+W9 carry-overs C2 + C3 + C5,`docs/03-implementation/beta-cohort-onboarding-W11-W12.md`(W9 D4 onboarding doc)
- **OQ deps**:F2 deploy complete + F1.4 LIVE switch
- **Acceptance criteria**:
  - F3.1 F1.5 LIVE smoke + F1.7 LIVE smoke acceptance per `infrastructure/entra-id/README.md` step 8
  - F3.2 F3.5 LIVE smoke audit chain through dev / staged server
  - F3.3 F4.5 LIVE smoke E1 + E5 + E12 graceful UX cases
  - F3.4 W4/W5 LIVE smoke remainder(W6 C3):PPT E2E + GPT-5.5 latency baseline + Chat UI screenshots
  - F3.5 Beta cohort first-cohort access provisioning(Entra ID app role assignment per Q7;onboarding doc final review + IT helpdesk contact info populate;Slack `#ekp-beta` channel auto-join)
  - F3.6 First-cohort kick-off ping + feedback intake established
- **Effort estimate**:1 day(LIVE smoke ~0.5 day + cohort onboarding ~0.5 day)
- **Owner**:AI(LIVE smoke automation)+ Chris(cohort coordination)
- **Cost expected**:~$10-15(LIVE LLM spend × 10-15 cohort kick-off queries)

### F4 — Implementation polish(Track B,IT-cred-independent)

- **Component(s)**:**C07 + C08 + C06**
- **Spec ref**:W9 retro § Carry-overs,`infrastructure/observability/README.md` W9 D3+ progressive scope hint
- **OQ deps**:none
- **Acceptance criteria**:
  - F4.1 `observe_streaming` decorator NEW for `/query/stream` SSE handler(W9 D4 deferred — captures SSE flow close latency + token counts post-stream-end)
  - F4.2 Eval-set augmentation pipeline:integrate W9 D3 `query_collector.py` real query corpus → eval set merge tooling(per architecture.md §6.1 W4 D5 pattern of 加 20 條 real query into eval set)
  - F4.3 Q15 manual update frequency signal scaffold:weekly cohort feedback aggregation report from Langfuse + bug report Slack channel
  - F4.4 W7 D5 carry-over polish:F5.5 Pixel diff snapshots installation if Vitest/Playwright harness available(non-Beta-blocking)
- **Effort estimate**:1 day(static work × 0.5x calibration)
- **Owner**:AI(progressive scope)+ Chris(weekly review process)
- **Cost expected**:~$0

### F5 — W11 staged rollout readiness(Track B)

- **Component(s)**:cross-cutting(C12 + C07 + governance)
- **Spec ref**:`infrastructure/runbook/README.md`(W9 D2 authored)+ `docs/03-implementation/beta-plan-v1.md §3 W11`
- **OQ deps**:F2 deploy complete(for runbook real-incident exercise);Q7 cohort roster final
- **Acceptance criteria**:
  - F5.1 Runbook real-incident exercise:walk through `§1 Document parse failure` + `§2 API quota exhaustion` against staged ACA env;document any SOP gaps in update history
  - F5.2 Cost dashboard real-time wire:plumb `query_collector` → audit_log JSON stream OR Langfuse generations API for `/observability/cost-summary` upgrade from static projection to real-time per-query USD attribution
  - F5.3 Onboarding doc final review:Chris populate IT helpdesk contact + Slack channel auto-join confirmation + final cohort signup process per Q7
  - F5.4 W11 staged rollout 25% phase prep:Stakeholder go/no-go review prep deck + cohort expansion roster
- **Effort estimate**:1 day
- **Owner**:Chris(runbook exercise + Stakeholder coord)+ AI(real-time wire scaffold)
- **Cost expected**:~$5-10(runbook exercise queries)

### F6 — Phase Gate closeout + W10 retro + W11 staged rollout phase folder kickoff

- **Component(s)**:cross-cutting governance
- **Spec ref**:`PROCESS.md §2.3 closeout`,`docs/03-implementation/beta-plan-v1.md §3 W11 staged rollout 25%`
- **OQ deps**:F1-F5 verdict outcomes
- **Acceptance criteria**:
  - F6.1 W10 phase Gate verdict landed
  - F6.2 W10 progress.md retro 7 sections complete
  - F6.3 W11-staged-rollout-25 phase folder kickoff:`docs/01-planning/W11-staged-rollout-25/{plan,checklist,progress}.md` draft(per architecture.md §6.1 W11 row)
  - F6.4 W10 progress.md frontmatter status flipped to `closed`
  - F6.5 R-B1 closure verification(if F1.4 landed Track A);R5 Azure quota status update post-LIVE-deploy real signal
  - F6.6 OQ Q11 final operational Resolved sync(if Track A landed)+ Q15 manual update frequency status update per real signal + Q6 Real query collection owner Resolved per F3.6 cohort onboarding outcome
- **Effort estimate**:0.5 day
- **Owner**:AI(draft)+ Chris(approve)

## 3. Success Criteria(Phase Gate to W11)

| # | Criterion | Target | Measure | Block W11?|
|---|---|---|---|---|
| G1 | F1 Q11 final operational Resolved + R-B1 closed | `Resolved` operational + 🟢 Mitigated | decision-form.md + RISK_REGISTER | Yes(Track A; if cred slip → W11 trigger)|
| G2 | F2 Chris infra/IT/DNS apply cascade complete | All 7 sub-gates landed | F2.1-F2.7 verification | Yes |
| G3 | F3 LIVE smoke verification(F1.5 + F1.7 + F3.5 + F4.5)pass + Beta cohort access provisioned | All cases verified + 5-10 cohort active | F3.1-F3.6 | Yes |
| G4 | F4 Implementation polish(observe_streaming + eval-set augmentation prep) | observe_streaming wired + eval-set merge tool ready | F4.1 + F4.2 | No |
| G5 | F5 W11 staged rollout readiness:runbook exercise + cost dashboard real-time + onboarding doc final | All 4 prep items landed | F5.1-F5.4 | Yes |
| G6 | Backend ruff + frontend lint + type-check 0 errors | All clean | local + CI | Yes |
| G7 | Q11 + Q6 + Q15 sync to decision-form.md per outcome | All 3 statuses updated | decision-form.md | No |

## 4. Risks(Phase-Specific)

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | IT cred slip past W10 D5 → Track A 推 W11 | Medium | High | Track B continues IT-cred-independent;若 W11 D1 仍未 deliver → R-B1 re-escalation per RISK_REGISTER R14 trigger |
| R2 | Azure infra apply first time friction(networking + KV + Managed Identity binding)| Medium | Medium | W8 D1-D3 declarative Bicep spec ready;ACA staging revision; rollback path in `infrastructure/runbook/README.md §6.1` |
| R3 | Beta cohort onboarding low engagement(Q7 user roster slip)| Medium | Low | Chris pre-identify W7-W8 carry-over preserved;default RAPO 內部 ≥ 3 cohort users;W11 expand with friendly department |
| R4 | LIVE smoke fails on real Entra ID tenant config drift | Low | High | F1.6 13 unit tests catch contract mismatch;mock-substitute fallback if LIVE-only issue |
| R5 | Cost dashboard real-time wire reveals projection inaccuracy | Low | Low | Static projection per architecture.md §9 baseline preserved as fallback;real-time delta captured in Langfuse generations API for re-baseline |

## 5. Day-by-Day Breakdown(rough)

| Day | Date | Track A focus | Track B focus | Deliverables targeted |
|---|---|---|---|---|
| D1 | 2026-06-02 | F1.1 IT cred follow-up;若 delivered → F1.2 KV populate | F4.1 observe_streaming scaffold | F1, F4 |
| D2 | 2026-06-03 | F2 Chris infra apply cascade(若 cred ready)| F4.2 eval-set augmentation pipeline | F2, F4 |
| D3 | 2026-06-04 | F2.7 F1.4 LIVE switch + F3.1 F1.5 LIVE smoke | F4.3 Q15 weekly aggregation scaffold | F2, F3, F4 |
| D4 | 2026-06-05 | F3.5 Beta cohort access provision + F3.6 kick-off ping | F5.1 Runbook real-incident exercise + F5.2 cost dashboard real-time wire | F3, F5 |
| D5 | 2026-06-06 | F3 LIVE smoke remainder + F4 cohort first-day support | F5.3 onboarding doc final + F5.4 W11 prep deck + F6 closeout | F3, F5, F6 |

**Day-by-day caveat**:Track A timing depends on real-calendar IT cred delivery date(target early June);若 slip → all Track A days shift;Track B continues unaffected。Real-calendar context = implementation front-runs project doc ~3-4 週 per W9 D1 三方 outcome briefing。

## 6. Dependencies on Prior Phase

Carry-overs from `W09-beta-internal-testing/progress.md` retro § Carry-overs(W9 D5 closeout):
- IT cred populate trigger(F1.1)
- Chris infra/IT/DNS apply cascade(F2)
- LIVE smoke verification(F3.1-F3.4)
- Beta cohort onboarding(F3.5-F3.6)
- observe_streaming decorator W11+ scope(F4.1)
- Live query collection plumbing(F5.2)
- Runbook real-incident exercise post-deploy(F5.1)
- Onboarding doc final review(F5.3)
- F5.5 Pixel diff snapshots(W7 D5 carry-over;W10 polish window if harness installed)

## 7. Plan Changelog

| Date | Change | Reason | Approver |
|---|---|---|---|
| 2026-05-30 | Initial draft(W9 D5 末 closeout cascade)| Per PROCESS.md §2.3 rolling-JIT kickoff;status=draft pending Chris W9 closeout sign-off + IT cred populate trigger | Chris(pending approve to flip active) |
| 2026-06-02 | `draft → active` flip — W10 D1 implementation start | Chris W9 closeout sign-off received;Track B kickoff IT-cred-independent per plan §1 split;Track A still blocked on IT cred populate event(target ~2026-06-02 to 2026-06-07) | Chris(W10 D1 sign-off) |
| 2026-06-06 | `active → closed` flip — W10 D5 closeout cascade | PARTIAL PASS verdict landed(Track B complete F4.1+F4.2+F4.3+F5.2+F5.4+F5.1 tabletop+F5.3 review;F4.4 deferred W11+ per Karpathy §1.2;Track A pending IT cred event per W9 D1 三方 outcome cascade pattern;W11 phase folder kickoff per rolling JIT)| Chris(W10 closeout sign-off) |

---

**Lifecycle reminder**:呢份 plan `status=draft`(等 Chris W9 closeout sign-off + IT cred populate trigger flip `active`)。重大 deviation 入第 7 節 changelog。Track A vs Track B split allows W10 progress regardless of IT cred timing。
