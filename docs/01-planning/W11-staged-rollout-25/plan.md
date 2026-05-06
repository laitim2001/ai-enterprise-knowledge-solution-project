---
phase: W11-staged-rollout-25
name: "Staged Rollout 25% — Track A LIVE deploy cascade trigger window + cohort expansion + W12 production launch readiness"
sprint_week: W11
start_date: 2026-06-09           # tentative — assumes W10 closed 2026-06-06 + Track A IT cred event fires W10/W11 boundary
end_date: 2026-06-13             # 5 working days
status: active                   # `active` 自 W11 D1(2026-06-09)— Chris W10 closeout sign-off authorization + Track B IT-cred-independent items 即時 start;Track A 仍等 IT cred populate event(real-calendar 2026-06-08 re-escalation deadline 1-day buffer)
spec_refs:
  - architecture.md §6.1 W11 row             # Staged rollout 25% → 50% trigger
  - architecture.md §6.2 Beta + Rollout      # W7-W12 timeline
  - architecture.md §7.4 Day-2 Readiness     # Runbook real-incident exercise + cost dashboard real-time + alert routing
  - architecture.md §8 Risk Register         # R-B1 closure verification + R5 Azure quota post-LIVE-deploy
  - components/C07-observability.md          # Live Langfuse generations API plumb post real cohort traffic
  - components/C11-identity.md               # Q11 final operational Resolved trigger event
  - components/C12-devops.md                 # Track A LIVE deploy cascade trigger
prior_phase: W10-beta-iteration
related_artifacts:
  - docs/03-implementation/beta-plan-v1.md       # W7-W12 phase breakdown
  - docs/03-implementation/w11-staged-rollout-25-prep-deck.md  # Stakeholder Go/No-Go prep deck(W10 D4)
  - docs/03-implementation/runbook-tabletop-W10-d5.md  # AF1-AF4 runbook in-place edits to land before live exercise
  - docs/01-planning/W10-beta-iteration/progress.md  # Retro § Carry-overs
  - docs/01-planning/RISK_REGISTER.md            # R14 R-B1 closure trigger
---

# Phase W11 — Staged Rollout 25%(Track A trigger window + cohort 25% rollout + W12 production launch readiness final review)

> **Plan version**:1.0(draft 2026-06-06 W10 D5 末 closeout cascade — rolling JIT per CLAUDE.md §10 R1)
> **Owner**:Chris(Tech Lead + Stakeholder coordination + IT engagement follow-through + Beta cohort onboarding lead)+ AI(implementation polish + W12 production launch prep)
> **Approved by**:_(pending Chris W10 closeout sign-off + Stakeholder W11 prep deck approve cycle)_

## 1. Scope(rolling-JIT W10 D5 末 draft;refined post-Stakeholder W11 prep deck approve cycle)

W11 = **Track A LIVE deploy cascade trigger window + 25% staged rollout phase**(W7-W12)。**Two parallel tracks**:
- **Track A**:**LIVE deploy cascade execution** — IT cred populate event(R-B1 closure trigger)→ F2.1-F2.7 + F3 LIVE smoke + F4 cohort onboarding cascade in single multi-stakeholder coordination cycle(W10 carry-over per W11 prep deck §4 GC1)
- **Track B**:**25% staged rollout + W12 production launch readiness** — once Track A complete:25% rollout activation(~62-125 users from full 250-500 base per Q7 cohort roster final)+ daily 4-metric monitor + 50% EoW conditional gate + Q15 first weekly signal review(W11 EoW)+ runbook live exercise replacing W10 D5 tabletop substitute

**6 deliverables F1-F6**:
- F1 Track A IT cred populate event + R-B1 closure verification(W10 carry-over;trigger window any time W11 D1-D5)
- F2 25% staged rollout activation(~62-125 users)+ cohort access provisioning + onboarding doc final-fill(IT helpdesk contact + Slack auto-join)
- F3 Daily metric monitor(4-metric + cost real-time per F5.2 + user satisfaction)+ 50% EoW conditional gate evaluation
- F4 Runbook live exercise replacing W10 D5 tabletop substitute(AF1-AF4 in-place edits land first)
- F5 Q15 first weekly signal report W11 EoW(`weekly_signal_report.py --week 2026-W24` real cohort traffic)+ Q4 deployment pricing rate confirmation(W11 prep deck §6.1 GC2)
- F6 Phase Gate closeout + W11 retro + W12-production-launch phase folder kickoff per rolling JIT

**Pre-condition for W11 promotion**(等 Chris W10 closeout sign-off + Stakeholder W11 prep deck approve cycle):
- W10 closeout PARTIAL PASS landed(per W9 D1 三方 outcome cascade pattern;Track B complete + Track A pending IT cred event)
- W11 prep deck Stakeholder Go/No-Go approve cycle complete(`docs/03-implementation/w11-staged-rollout-25-prep-deck.md` 8 sections sign-off)
- 3 open gate items(R-B1 closure / Q4 pricing rate confirm / cohort roster final)resolved per Stakeholder approve outcome
- IT cred populate event window(real-calendar 2026-06-08 re-escalation deadline if not yet fired;W10 D5 == 2026-06-06 — 2-day buffer remains)

## 2. Deliverables(F1-F6)

### F1 — Track A IT cred populate event + R-B1 closure(W10 carry-over)

- **Component(s)**:**C11** Identity & Access(primary)+ **C12** DevOps(infra cascade)+ governance
- **Spec ref**:`infrastructure/keyvault/README.md` 6 secrets + `infrastructure/aca/networking.bicep` PE + `infrastructure/entra-id/README.md` Pattern A 8-step + `infrastructure/swa/README.md` 5-step DNS
- **OQ deps**:Q11 final operational pending IT cred event
- **Acceptance criteria**:
  - F1.1 IT cred delivered(`AZURE_TENANT_ID` + `AZURE_CLIENT_ID` per Pattern A;real-calendar trigger event)
  - F1.2 Cred populated to Key Vault per `infrastructure/keyvault/README.md` 6-secrets cascade + Managed Identity grant `Key Vault Secrets User`
  - F1.3 ACA networking apply + Entra ID app registration apply + SWA custom domain apply(`ekp-beta.ricoh.com`)
  - F1.4 LIVE switch:`Settings.feature_auth_mock=False` + `NEXT_PUBLIC_AUTH_MOCK=false` GHA env update + ACA + SWA re-deploy
  - F1.5 LIVE smoke verification(F1.5 + F1.7 + F3.5 + F4.5 from W10 plan)+ Beta cohort first-cohort access provisioning
  - F1.6 R-B1 status 🟡 → 🟢 **Mitigated** + Q11 status `Resolved` operational + decision-form sync
- **Effort estimate**:2 days(W6 C10 calibration LIVE deploy 2x;multi-stakeholder coordination cycle)
- **Owner**:Chris(infra apply + IT engagement)+ AI(GHA verification + smoke test automation + governance docs sync)
- **Cost expected**:~$15-25(ACA + SWA + KV ops + first-week steady-state)

### F2 — 25% staged rollout activation + cohort onboarding final-fill

- **Component(s)**:**C09** Admin Console + **C10** Chat UI + **C11** + governance
- **Spec ref**:Beta plan v1 §2 W11 + `docs/03-implementation/beta-cohort-onboarding-W11-W12.md`(W10 D5 carry-over)+ Q7 cohort roster
- **OQ deps**:F1 complete + Q7 cohort roster final
- **Acceptance criteria**:
  - F2.1 25% rollout activation(~62-125 users from full 250-500 base per Q7 final roster;phased onboard RAPO 內部 ≥ 3 first if W11 prep deck §5 fallback active)
  - F2.2 Onboarding doc final-fill:Chris IT helpdesk contact populate + Slack `#ekp-beta` channel auto-join confirmation(W10 D5 carry-over per onboarding doc Update history 2026-06-06 entry)
  - F2.3 First-cohort kick-off ping + feedback intake established + Slack `#ekp-beta` active monitoring shift
  - F2.4 Day-1 metric baseline capture(p95 latency + cost real-time per F5.2 + Langfuse generation event volume)
- **Effort estimate**:1 day(LIVE smoke ~0.5 day + cohort onboarding ~0.5 day per W10 plan calibration)
- **Owner**:Chris(cohort coordination + onboarding doc final-fill)+ AI(smoke test automation + day-1 metric baseline capture)
- **Cost expected**:~$10-15(LIVE LLM spend × cohort kick-off queries × 25% × 5 q/day)

### F3 — Daily metric monitor + 50% EoW conditional gate

- **Component(s)**:cross-cutting **C06** + **C07** + governance
- **Spec ref**:Beta plan v1 §2 W11.F2-F3 + architecture.md §7.4 Day-2 Readiness + W11 prep deck §3
- **OQ deps**:F2 complete
- **Acceptance criteria**:
  - F3.1 Daily 4-metric monitor automation(retrieval recall + answer relevancy + faithfulness + latency p95)— `backend/eval/runner.py` against real query subset W11+
  - F3.2 Cost dashboard daily review(`/observability/cost-summary?window_hours=24` per F5.2;flag spend > projected × 1.2 alert)
  - F3.3 User satisfaction tracking(👍/👎 ratio + Slack `#ekp-beta` issue volume)
  - F3.4 50% rollout EoW conditional gate evaluation(no Sev1/Sev2 incident + 4-metric within ±3pp baseline + cost ≤ projected × 1.2)
  - F3.5 50% rollout activation if gate passes(125-250 users)— Stakeholder go/no-go re-cycle
- **Effort estimate**:1 day(daily 0.2 day × 5 days)
- **Owner**:AI(monitor automation + daily report)+ Chris(50% gate evaluation)+ Stakeholder(50% sign-off)
- **Cost expected**:~$15-25(LIVE LLM spend × 25% cohort × 5 q/day × 5 days)

### F4 — Runbook live exercise replacing W10 D5 tabletop substitute

- **Component(s)**:**C07** + **C12** + governance(oncall readiness)
- **Spec ref**:`infrastructure/runbook/README.md` + `docs/03-implementation/runbook-tabletop-W10-d5.md`(AF1-AF4 in-place edits to land first)
- **OQ deps**:F1 LIVE deploy complete(staged ACA env required for live exercise)
- **Acceptance criteria**:
  - F4.1 Runbook AF1-AF4 in-place edits land(per W10 D5 tabletop substitute aggregate findings):AF1 §1.A queue clarification + AF2 §2 ACA revision restart note + AF3 §2 tier-3 OPENAI_API_KEY rewrite + AF4 §2 per-user revoke gap acknowledged
  - F4.2 Runbook live exercise — Chris + AI walk through `runbook/README.md §1 + §2` against live ACA env within 72h post-Track A LIVE deploy
  - F4.3 Update `runbook/README.md` Update history with live exercise outcome
- **Effort estimate**:0.5 day(AF1-AF4 edits ~1h + live exercise ~3h)
- **Owner**:Chris(walkthrough + Update history)+ AI(AF1-AF4 in-place edits + scribe)
- **Cost expected**:~$0(no production LLM spend)

### F5 — Q15 first weekly signal report + Q4 deployment pricing rate confirm

- **Component(s)**:**C07** + governance
- **Spec ref**:F4.3 W10 D2 `weekly_signal_report.py` scaffold + W11 prep deck §6.1 Q4 pricing rate gate + F5.2 placeholder labelling
- **OQ deps**:F2 complete + 1 week real cohort traffic
- **Acceptance criteria**:
  - F5.1 Q15 first weekly signal report W11 EoW:`python -m observability.weekly_signal_report --queries <real-cohort-corpus> --feedback <real-feedback-corpus> --week 2026-W24 --output reports/weekly-signal-W24.md`(real cohort traffic feeds the scaffold)
  - F5.2 Q4 deployment pricing rate confirmation(per W11 prep deck §6.1 Option A vs Option B Stakeholder decision):
    - **Option A path**:Update `backend/observability/realtime_cost.py::_PRICING_TABLE` with confirmed Beta tenant rates → flip `PRICING_BASELINE_LABEL` from `placeholder_publicly_quoted_rates_2026-Q2` to `confirmed_2026-Q2-tenant-eastus2`(or similar)
    - **Option B path**(Karpathy §1.2 favoured):placeholder rates preserved + spend cap proxy alarm via `observability/alerts.py::cost_spike` rule(static projection × 1.5x ceiling)+ 7-day re-baseline post real cohort traffic
  - F5.3 Tier 2 trigger metric review(per W11 prep deck §3 W11.F5)— signal-driven decision on GraphRAG / multi-agent / multi-modal trigger gates(per architecture.md §11)
- **Effort estimate**:0.5 day
- **Owner**:Chris(Q4 pricing rate confirm + Stakeholder coord)+ AI(weekly signal report run + Tier 2 review draft)
- **Cost expected**:~$0(governance work)

### F6 — Phase Gate closeout + W11 retro + W12-production-launch phase folder kickoff

- **Component(s)**:cross-cutting governance
- **Spec ref**:`PROCESS.md §2.3 closeout` + `docs/03-implementation/beta-plan-v1.md §3 W12 production launch`
- **OQ deps**:F1-F5 verdict outcomes
- **Acceptance criteria**:
  - F6.1 W11 phase Gate verdict landed
  - F6.2 W11 progress.md retro 7 sections complete
  - F6.3 W12-production-launch phase folder kickoff:`docs/01-planning/W12-production-launch/{plan,checklist,progress}.md` draft(per architecture.md §6.1 W12 row + Beta plan v1 §3 W12)
  - F6.4 W11 progress.md frontmatter status flipped to `closed`
  - F6.5 R-B1 closure verification(if F1.6 landed)+ R5 Azure quota status update post-LIVE-deploy real signal
  - F6.6 OQ Q11 final operational Resolved sync + Q15 status update per real signal + Q6 Real query collection owner Resolved per F2.3 cohort onboarding outcome + Q4 pricing rate confirm sync
- **Effort estimate**:0.5 day
- **Owner**:AI(draft)+ Chris(approve)

## 3. Success Criteria(Phase Gate to W12)

| # | Criterion | Target | Measure | Block W12?|
|---|---|---|---|---|
| G1 | F1 R-B1 closed + Q11 final operational Resolved | 🟢 Mitigated + `Resolved` operational | RISK_REGISTER + decision-form | Yes |
| G2 | F2 25% rollout activated + Day-1 metric baseline captured | 62-125 users + p95 latency + cost real-time logged | F2.1-F2.4 verification | Yes |
| G3 | F3 4-metric within ±3pp baseline + no Sev1/Sev2 + cost ≤ projected × 1.2 | All daily reviews pass | F3.1-F3.4 daily reports | Yes(50% gate) |
| G4 | F3.5 50% rollout activation if conditional gate passes | 125-250 users(or held at 25% if gate fails) | Stakeholder sign-off | Yes(W12) |
| G5 | F4 Runbook live exercise replaces tabletop substitute | AF1-AF4 landed + live exercise complete + Update history entry | F4.1-F4.3 | No(but blocks W12 production launch readiness final review) |
| G6 | F5 Q15 first weekly signal report + Q4 pricing rate decision | Report rendered + Stakeholder Option A/B decision recorded | F5.1-F5.2 | No |
| G7 | Backend pytest 456+/456+ + ruff + frontend lint + type-check 0 errors | All clean | local + CI | Yes |
| G8 | OQ Q11 + Q15 + Q6 + Q4 pricing sync to decision-form.md per outcome | All 4 statuses updated | decision-form.md | No |

## 4. Risks(Phase-Specific)

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | IT cred slip past 2026-06-08 → R-B1 re-escalation 🟡 → 🔴 | Medium | High | W11 prep deck §5 No-Go fallback:W12 D1 staged rollout 25% defer(within Tier 1 launch envelope 2026-07-19);triple session re-cycle pattern same as W9 D1 三方 |
| R2 | Real cohort signals 4-metric regression > 3pp baseline | Medium | Medium | F3.3 daily review surfaces early;Stakeholder go/no-go re-cycle EoW;hold at 25% if 50% gate fails |
| R3 | Sev1/Sev2 incident in 25% rollout(parser failure / quota exhaustion / index corruption / reranker outage / CRAG bug)| Low | High | Runbook live exercise F4 + tabletop substitute AF1-AF4 prep mitigates;§6.1 ACA revision rollback path verified |
| R4 | Cost spend > projected × 1.5 ceiling | Low | Medium | `cost_spike` alert rule fires(architecture.md §7.4)+ F5.2 cost dashboard real-time signal;F5.2 Option A confirmed rate landing tightens accuracy;7-day re-baseline if Option B path active |
| R5 | Q4 deployment pricing rate confirmation slip(stakeholder decision delayed)| Medium | Low | Option B fallback per W11 prep deck §6.1 Karpathy §1.2 — placeholder + spend cap proxy preserved;real cohort traffic gives accurate calibration data within first week regardless |

## 5. Day-by-Day Breakdown(rough)

| Day | Date | Track A focus | Track B focus | Deliverables targeted |
|---|---|---|---|---|
| D1 | 2026-06-09 | F1.1-F1.4 IT cred populate + KV populate + ACA + SWA apply + LIVE switch | F4.1 Runbook AF1-AF4 in-place edits | F1, F4 |
| D2 | 2026-06-10 | F1.5-F1.6 LIVE smoke verification + R-B1 closure;F2.1 25% rollout activation;F2.2 onboarding doc final-fill | F4.2 Runbook live exercise post-LIVE-deploy | F1, F2, F4 |
| D3 | 2026-06-11 | F2.3 first-cohort kick-off ping;F2.4 Day-1 metric baseline | F3.1-F3.3 daily metric monitor cycle starts | F2, F3 |
| D4 | 2026-06-12 | F3.1-F3.3 daily metric monitor continue | F5.2 Q4 pricing rate confirm path execution | F3, F5 |
| D5 | 2026-06-13 | F3.4-F3.5 50% EoW conditional gate evaluation;Stakeholder go/no-go re-cycle | F5.1 Q15 first weekly signal report;F5.3 Tier 2 trigger metric review;F6 W11 closeout cascade + W12 phase folder kickoff | F3, F5, F6 |

**Day-by-day caveat**:Track A timing depends on real-calendar IT cred event;若 slip past 2026-06-08 → all Track A days shift + W12 D1 defer per W11 prep deck §5 No-Go fallback;Track B F4.1(runbook AF1-AF4 edits)+ F5.3(Tier 2 review)IT-cred-independent。

## 6. Dependencies on Prior Phase

Carry-overs from `W10-beta-iteration/progress.md` retro § Carry-overs(W10 D5 closeout):
- IT cred populate event(F1.1)— Track A trigger
- F2.1-F2.7 Chris infra/IT/DNS apply cascade(W9 + W10 carry-over)
- F3.1-F3.4 LIVE smoke verification
- F2.2 Onboarding doc final-fill(IT helpdesk contact carry-over per W10 D5 onboarding doc Update history)
- F4.1 Runbook AF1-AF4 in-place edits(per `runbook-tabletop-W10-d5.md` aggregate findings)
- F4.2 Runbook live exercise post-LIVE-deploy
- F5.2 Q4 deployment pricing rate confirmation(per W11 prep deck §6.1 Stakeholder Option A vs B decision)
- F5.3 Tier 2 trigger metric review(per W11 prep deck §3 W11.F5)
- W11 prep deck Stakeholder approve cycle outcome

## 7. Plan Changelog

| Date | Change | Reason | Approver |
|---|---|---|---|
| 2026-06-06 | Initial draft(W10 D5 末 closeout cascade)| Per PROCESS.md §2.3 rolling-JIT kickoff;status=draft pending Chris W10 closeout sign-off + Stakeholder W11 prep deck approve cycle | Chris(pending approve to flip active) |

---

**Lifecycle reminder**:呢份 plan `status=draft`(等 Chris W10 closeout sign-off + Stakeholder W11 prep deck approve cycle flip `active`)。重大 deviation 入第 7 節 changelog。Track A 仍係 IT cred event-triggered;Track B(runbook AF edits + Tier 2 review)IT-cred-independent W11 D1+。
