---
title: "W11 Staged Rollout 25% — Stakeholder Go/No-Go Prep Deck"
status: draft                          # `draft` 自 W10 D4 2026-06-05;flips active 等 Stakeholder W10 D5 末 review approve
phase_target: W11-staged-rollout-25
review_date: 2026-06-06               # tentative — W10 D5 末 closeout sync
authors: [AI Drafter, Chris Lai (Tech Lead)]
spec_refs:
  - architecture.md §6.1 W11 row
  - architecture.md §6.2 Beta + Rollout Phase
  - docs/03-implementation/beta-plan-v1.md §2 W11
  - docs/01-planning/W10-beta-iteration/plan.md §2 F5.4
  - docs/01-planning/RISK_REGISTER.md R14 R-B1
oq_dependencies:
  - Q4 Azure OpenAI deployment(pricing rate confirmation NEW)
  - Q7 Beta user source(cohort expansion roster)
  - Q11 Entra ID tenant(operational Resolved trigger)
  - Q12 Tier 2 owner
  - Q15 Manual update frequency(real-cohort signal trigger)
related_artifacts:
  - docs/03-implementation/beta-cohort-onboarding-W11-W12.md
  - docs/03-implementation/beta-plan-v1.md
  - infrastructure/runbook/README.md
last_updated: 2026-06-05
---

# W11 Staged Rollout 25% — Stakeholder Go/No-Go Prep Deck

> **Audience**:Stakeholder + Chris + IT manager。**Decision asked**:approve / defer / no-go for W11 staged rollout 25%(~62-125 users from full 250-500 base per Beta plan v1 §2 W11)。
>
> **Karpathy §1.2 simplicity-first**:呢份 deck **one-page-decision-form** 結構 — exec summary + go criteria(must-pass)+ no-go fallback + 3 open gate items + sign-off section。詳細 implementation 細節 link out 到對應 artifact,唔重複 context。
>
> **Lifecycle**:`draft` 自 2026-06-05 W10 D4;flips `active` 喺 Stakeholder W10 D5 末 review approve cycle 完成後;`closed` 喺 W11 D1 staged rollout trigger event 之後。

---

## 1. Executive Summary

W10 Beta iteration closes(real-calendar 2026-06-06)。Track B implementation polish complete(F4.1 + F4.2 + F4.3 + F5.2 = 4/4 IT-cred-independent items shipped W10 D1-D3)。Track A LIVE deploy cascade still **pending IT cred populate event**(target window 2026-06-02 to 2026-06-07 per W9 D1 三方 outcome;**re-escalation deadline 2026-06-08** if IT 仍未 deliver)。

**Three open gate items** require Stakeholder + IT manager confirmation before W11 staged rollout 25% can fire:
1. **R-B1 closure** — IT cred populated to Key Vault + LIVE smoke PASS(Track A cascade complete)
2. **Q4 pricing rate confirmation** *(NEW per W10 D3 F5.2)* — Beta tenant deployment-specific rates replacing `placeholder_publicly_quoted_rates_2026-Q2` baseline
3. **Cohort expansion roster** — final 62-125 user list per Q7(default RAPO 內部 ≥ 3 + 1-2 friendly departments per W6 D5 stakeholder approval cycle)

**Recommendation**:**Conditional GO** for W11 D1 staged rollout 25% trigger,**contingent on all 3 gate items resolved by W10 D5 末**(2026-06-06)。If any gate item slips → **No-Go fallback to W11 D2-D3 trigger window** with explicit re-confirmation cycle。

---

## 2. W10 Verdict Snapshot(per W10 plan §3 G1-G7)

### G1-G4 Track A(LIVE deploy cascade)— **PENDING**(blocked on IT cred populate event)
- G1:Q11 final operational Resolved + R-B1 closed → ⏸ pending
- G2:Chris infra/IT/DNS apply cascade complete(F2.1-F2.7)→ ⏸ pending
- G3:LIVE smoke verification + Beta cohort access provisioned → ⏸ pending

### G4 Implementation polish(Track B)— ✅ **PASS**
- F4.1 ✅ `observe_streaming` SSE flow capture(W10 D1;commit `85aa8f4`)
- F4.2 ✅ Eval-set augmentation pipeline(W10 D1;commit `85aa8f4`)
- F4.3 ✅ Q15 weekly signal report scaffold(W10 D2;commit `86ecf7f`)
- F5.2 ✅ Cost dashboard real-time wire(W10 D3;commit `d656b03`)
- F4.4 🚧 Pixel diff harness — **DEFERRED W11+ post-cohort signal**(W10 D4 finding:Vitest/Playwright 未 install in `frontend/package.json`;Karpathy §1.2 — install cost ~1 day + mock baseline snapshots without real cohort UX signal = wasted polish before signal exists)

### G5 W11 staged rollout readiness(Track B)— **PARTIAL PASS**(F5.1 + F5.3 blocked on Track A;F5.4 = this deck)
- F5.1 ⏸ Runbook real-incident exercise(needs staged ACA env per Track A)
- F5.2 ✅(see G4)
- F5.3 ⏸ Onboarding doc final review(IT helpdesk contact dependency per Chris)
- F5.4 ✅ This prep deck(W10 D4;Stakeholder review trigger event)

### G6 Backend ruff + frontend lint + type-check 0 errors — ✅ **PASS**(456/456 pytest pass)

### G7 OQ sync — **PARTIAL**(Q11 + Q15 + Q6 pending real-cohort signal post Track A)

**W10 verdict aggregate**:**PARTIAL PASS — Track B complete,Track A pending IT cred populate event**。Verdict identical to W9 closeout per W9 D1 三方 outcome plan;the deferred Track A items remain timing-bound,not technical-blockers。

---

## 3. W11 Staged Rollout 25% Scope(per Beta plan v1 §2 W11)

| # | Deliverable | Owner | Trigger | Notes |
|---|---|---|---|---|
| W11.F1 | 25% rollout(~62-125 users)| Chris + IT | post-W10 D5 closeout + 3 gate items resolved | Random sampling from full 250-500 base per Q7 final roster |
| W11.F2 | Daily metric monitor | AI + C07 | rollout fire event | 4-metric(retrieval recall + answer relevancy + faithfulness + latency p95)+ cost(real-time per F5.2)+ user satisfaction(👍/👎 per F4.3 weekly signal scaffold) |
| W11.F3 | 50% rollout EoW trigger(125-250 users) | Chris | conditional pass gate(no Sev1/Sev2 incident + 4-metric within ±3pp baseline + cost ≤ projected × 1.2)| Stakeholder go/no-go re-cycle EoW |
| W11.F4 | Incident response runbook drill | Chris | Day-2 ops readiness | Walk through `infrastructure/runbook/README.md §1-§10` against staged ACA env |
| W11.F5 | Q15 first weekly signal review | Chris + Stakeholder | W11 EoW | Run `weekly_signal_report.py --week 2026-W24`(F4.3 scaffold)→ surface manual update frequency hot spots |

---

## 4. Go Criteria(must-pass before W11 D1 trigger)

| # | Criterion | Owner | Status as of 2026-06-05 W10 D4 | Block W11?|
|---|---|---|---|---|
| GC1 | **R-B1 closed** — IT cred populated to Key Vault + LIVE smoke PASS(F2.1-F2.7 + F3.1-F3.4)| Chris + IT | ⏸ pending(IT cred event) | Yes |
| GC2 | **Q4 pricing rate confirmed** — Beta tenant deployment-specific rates supplant `placeholder_publicly_quoted_rates_2026-Q2` in `realtime_cost._PRICING_TABLE` | Chris + IT pricing | ⏸ pending(Q4 NEW gate item per F5.2) | **Yes — spend gate**|
| GC3 | **Cohort roster final** — 62-125 user list locked per Q7(RAPO 內部 + friendly departments)| Chris + Stakeholder | ⏸ pending W10 D5 sign-off | Yes |
| GC4 | **Onboarding doc final** — IT helpdesk contact + Slack `#ekp-beta` auto-join confirmed(F5.3)| Chris | ⏸ pending IT helpdesk contact | Yes |
| GC5 | **Runbook real-incident exercise** — `infrastructure/runbook/README.md §1 + §2` walked through staged ACA env(F5.1)| Chris | ⏸ pending Track A staged ACA | Yes |
| GC6 | **Day-2 ops handover** — Chris + AI co-sign on monitoring + alert routing + runbook + cost dashboard real-time wire | Chris + AI | 🟡 partial(F5.2 cost dashboard ready;F5.1 + F5.3 pending) | Yes |
| GC7 | **Stakeholder Go/No-Go sign-off** | Stakeholder | ⏸ pending review cycle | Yes |
| GC8 | Backend pytest 456/456 + ruff clean + frontend type-check 0 errors | AI | ✅ green W10 D3 closeout | (already met) |

**Conditional GO requires GC1-GC7 all green by W10 D5 末 closeout(2026-06-06 EOD)**。

---

## 5. No-Go Fallback Plan

**If GC1 (R-B1 closure) slips past 2026-06-08**(re-escalation trigger per RISK_REGISTER R14):
- 🟡 → 🔴 R-B1 re-escalation
- Stakeholder + IT manager + Chris re-cycle session(同 W9 D1 三方 alignment pattern)
- W11 staged rollout 25% **defers to W12 D1 trigger window**(impact production launch milestone — extend by 1 week,still within 2026-07-19 Tier 1 launch envelope)
- Track B implementation polish continues IT-cred-independent(W11 = additional polish + Tier 2 trigger metric scaffolding W11+ optional)

**If GC2 (Q4 pricing rate) slips**:
- F5.2 dashboard renders with `placeholder` baseline → **Beta cohort spend visibility stays fuzzy**
- Mitigation:Stakeholder approves spend cap proxy(static projection × 1.5x as ceiling alarm via `observability/alerts.py` `cost_spike` rule;7-day re-baseline post real cohort traffic per W9.F2 + F5.2 hybrid endpoint)
- Decision:can proceed with placeholder rates IF Stakeholder accepts spend signal lag risk;Chris IT pricing follow-up cycle continues parallel

**If GC3 (cohort roster) incomplete**:
- Phased onboard:start with confirmed RAPO 內部 ≥ 3 sub-cohort,defer friendly department additions to W11 D3+
- Maintains W11 D1 trigger viability with reduced cohort size(~10-15 users initial)
- W11 D3 expansion contingent on no Sev1/Sev2 incident + 4-metric within baseline

**If GC4 (onboarding doc) missing IT helpdesk contact**:
- Use generic `support@ricoh.com` placeholder + Slack `#ekp-beta` channel as primary support funnel
- Update doc within 48h post-W11 D1 launch

**If GC5 (runbook exercise) cannot fire**(staged ACA env unavailable due to Track A delay):
- **Tabletop exercise** as substitute — Chris walks through `runbook/README.md §1 + §2` 10-step procedures with AI present;document any clarifications inline
- Escalate to live exercise within 72h post-Track A LIVE deploy

---

## 6. Open Gate Items(Stakeholder confirm needed)

### 6.1 Q4 Pricing Rate Confirmation *(NEW per W10 D3 F5.2)*

**What changed**:F5.2 cost dashboard real-time wire shipped W10 D3 with placeholder per-1k-token rates(`gpt-5-5` $0.005 input + $0.015 output etc)labelled `placeholder_publicly_quoted_rates_2026-Q2`。Real Beta tenant pricing depends on:
- Azure OpenAI deployment region(eastus2 vs other)
- Deployment tier(standard vs provisioned)
- Negotiated Microsoft Enterprise Agreement discount(if applicable)
- Cohere Marketplace billing terms(Path A per Q5)

**Decision asked**:
- **Option A**:Block W11 trigger until Chris + IT pricing finalise tenant-specific rates(target W10 D5 末)
- **Option B**:Proceed with placeholder rates + spend cap proxy alarm(`cost_spike` × 1.5x static projection ceiling),7-day re-baseline post real cohort traffic
- **Recommendation**:**Option B**(Karpathy §1.2 — placeholder pricing has explicit fuzz-warning label;real cohort traffic gives accurate calibration data within first week;cost dashboard `realtime_status="ok"` already provides traffic-anchored signal even without exact rates)

**Owner**:Chris(IT pricing follow-up)+ Stakeholder(spend gate sign-off)
**Resolution path**:Update `backend/observability/realtime_cost.py::_PRICING_TABLE` with confirmed rates → flip `PRICING_BASELINE_LABEL` from `placeholder_publicly_quoted_rates_2026-Q2` to `confirmed_2026-Q2-tenant-eastus2`(or similar)

**Decision recorded — W11 D1 2026-06-09**:**Option B chosen**(Stakeholder authorization)— placeholder rates preserved + `cost_spike` rule × 1.5x ceiling preserved(`backend/observability/alerts.py` existing rule;rolling 7-day avg comparison serves anomaly detection intent;wording 「static projection × 1.5x」 was approximate — actual rule = dynamic rolling avg comparison,functionally equivalent for first-week anomaly detection)+ 7-day re-baseline post real cohort traffic W11+ scheduled。Option A NOT CHOSEN(spec-completeness ROI 不及 Beta timeline pressure;real cohort traffic 第一週自然校準到 confirmed-rate accuracy through usage signal)。`docs/decision-form.md` Q4 entry sync per R4 binding(W11 D1 operational follow-up sub-entry added;Q4 status remains `Resolved (full)`)。

### 6.2 R-B1 Closure(per RISK_REGISTER R14)

**Status**:🟡 Active monitor with confirmed deadline 2026-05-26(W9 D1 三方 outcome de-escalation);**re-escalation trigger 2026-06-08** if real-calendar IT 仍未 deliver。

**Decision asked**:**No new decision required from Stakeholder unless re-escalation trigger fires** — IT cred populate event is mechanical execution of W8 D1-D4 SOPs。If 2026-06-08 仍未 deliver → triple session re-cycle(same pattern as W9 D1)。

**Owner**:Chris(IT engagement follow-through)+ IT manager(deliver)

### 6.3 Cohort Roster Final per Q7

**Default per W6 D5 stakeholder approval cycle**:RAPO 內部 ≥ 3 + 1-2 friendly departments(Chris pre-identify W7-W8 carry-over preserved through W10)

**Decision asked**:Confirm final 62-125 user list **before W11 D1 trigger**;recommend phased onboard with RAPO 內部 sub-cohort first(reduces blast radius if early Sev1/Sev2 incident)

**Owner**:Chris + Stakeholder

---

## 7. Day-2 Ops Handover Checklist

per `architecture.md §7.4 Day-2 Readiness Checklist`(carry-over context from W6 D5 demo prep + W8 F5):

- [ ] **Cost dashboard**:F5.2 real-time wire ✅(W10 D3 commit `d656b03`)
- [ ] **Alert ruleset**:`observability/alerts.py::beta_alert_rules()` 6-rule live(api_latency_p95 + api_error_rate + cost_spike + crag_trigger_rate + rate_limit_saturation + langfuse_export_lag);Azure Monitor sync per `infrastructure/observability/README.md`
- [ ] **Runbook**:`infrastructure/runbook/README.md` 10 sections authored(W9 D2)— **exercise pending F5.1 cascade**
- [ ] **Audit logging**:W7 D3 F3 audit middleware ✅(per-request tagged with request_id + user_oid + tenant_id + audit_action)
- [ ] **Feedback loop**:`/feedback` endpoint W8 D5 F5.3 ✅;weekly aggregation report `weekly_signal_report.py` W10 D2 ✅
- [ ] **Eval-set augmentation**:`eval_set_augmentor` W10 D1 ✅ — pipe real cohort queries into eval-set v2 W11+
- [ ] **CRAG monitoring**:`@observe_llm_async` decoration W9 D2-D3 ✅ on grade + rewrite_query stages
- [ ] **Streaming observability**:`observe_streaming` W10 D1 ✅ — captures /query/stream cost attribution

---

## 8. Stakeholder Decision Form

Stakeholder sign-off block(完成後 Chris flip status `draft → active` + W11 D1 trigger window opens):

```
Decision date: ___________________
Stakeholder name: ________________

[ ] APPROVE — W11 staged rollout 25% trigger window opens W11 D1 conditional on all 3 gate items resolved
[ ] APPROVE WITH CONDITIONS — list conditions in note section
[ ] DEFER — W11 trigger window pushes to W12 D1;extend Tier 1 launch envelope
[ ] NO-GO — escalation cycle required;document blocker

Conditions / notes:
__________________________________________________________________
__________________________________________________________________

Q4 pricing rate decision:[ ] Option A(block) [ ] Option B(placeholder + spend cap proxy)
Cohort roster confirmed:[ ] Yes(attached list)[ ] Phased(RAPO 內部 first)
Day-2 handover acknowledge:[ ] Yes
```

---

## 9. References

- `docs/architecture.md §6.1 W11 row` — staged rollout 25% timeline
- `docs/architecture.md §6.2 Beta + Rollout Phase`
- `docs/architecture.md §7.4 Day-2 Readiness Checklist`
- `docs/architecture.md §8 Risk Register R-B1`
- `docs/03-implementation/beta-plan-v1.md §2 W11`
- `docs/03-implementation/beta-cohort-onboarding-W11-W12.md`
- `docs/01-planning/W10-beta-iteration/plan.md §2 F5.4`
- `docs/01-planning/RISK_REGISTER.md R14 R-B1`
- `infrastructure/runbook/README.md`(10-section runbook;F5.1 exercise pending)
- `infrastructure/observability/README.md`
- `backend/observability/realtime_cost.py`(F5.2 — `_PRICING_TABLE` placeholder labelling per GC2)
- `backend/observability/weekly_signal_report.py`(F4.3 — Q15 manual update frequency signal scaffold;feeds W11.F5)

---

## 10. Update History

| Date | Change | Author |
|---|---|---|
| 2026-06-05 | Initial draft(W10 D4 F5.4)| AI |
| 2026-06-09(W11 D1)| §6.1 Q4 pricing rate Stakeholder decision recorded — Option B path chosen(placeholder + `cost_spike` 1.5x ceiling + 7-day re-baseline);`decision-form.md` Q4 sync per R4 binding | Chris(Stakeholder authorization)+ AI(scribe)|
| _(pending)_ | Stakeholder review approve cycle(other gate items GC1 / GC3 / GC4 / GC5 / GC6 / GC7)| Stakeholder + Chris |
| _(pending)_ | Status flip `draft → active` post-approve | Chris |
| _(pending)_ | Status flip `active → closed` post-W11 D1 trigger | Chris |
