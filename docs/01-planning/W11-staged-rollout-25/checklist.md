---
phase: W11-staged-rollout-25
plan_ref: ./plan.md
status: active
last_updated: 2026-06-09
---

# Phase W11 — Checklist

> Atomic checkbox(每 item ≤ 0.5–2 hour effort per W6 C10 calibration:LIVE deploy 2x;static 0.5x)。
> Status:`draft` 自 2026-06-06 W10 D5 closeout cascade。
> 全 unchecked 至 W11 D1 implementation start。

## F1 — Track A IT cred populate event + R-B1 closure(W10 carry-over)

- [ ] F1.1 IT cred delivered(`AZURE_TENANT_ID` + `AZURE_CLIENT_ID` per Pattern A)— real-calendar trigger event
- [ ] F1.2 Cred populated to Key Vault per `infrastructure/keyvault/README.md`(6 secrets)+ Managed Identity grant `Key Vault Secrets User`
- [ ] F1.3 ACA networking apply(Private Endpoint + DNS zone link;disable Search public access)+ Entra ID app registration apply(Pattern A 8-step)+ SWA custom domain apply(`ekp-beta.ricoh.com`)
- [ ] F1.4 LIVE switch:`Settings.feature_auth_mock=False` env override + ACA revision restart;`NEXT_PUBLIC_AUTH_MOCK=false` GHA env update + SWA re-deploy
- [ ] F1.5 LIVE smoke verification(F1.5 + F1.7 + F3.5 + F4.5 from W10 plan carry-over):dev tenant Entra ID end-to-end login flow + audit chain + graceful UX cases
- [ ] F1.6 R-B1 status 🟡 → 🟢 **Mitigated** + Q11 status `Resolved` operational + decision-form sync

## F2 — 25% staged rollout activation + cohort onboarding final-fill

- [ ] F2.1 25% rollout activation(~62-125 users from full 250-500 base per Q7 final roster;phased onboard RAPO 內部 ≥ 3 first if W11 prep deck §5 fallback active)
- [ ] F2.2 Onboarding doc final-fill:Chris IT helpdesk contact populate + Slack `#ekp-beta` channel auto-join confirmation(`docs/03-implementation/beta-cohort-onboarding-W11-W12.md` per W10 D5 carry-over)
- [ ] F2.3 First-cohort kick-off ping + feedback intake established + Slack `#ekp-beta` active monitoring shift
- [ ] F2.4 Day-1 metric baseline capture(p95 latency + cost real-time per F5.2 + Langfuse generation event volume)

## F3 — Daily metric monitor + 50% EoW conditional gate

- [ ] F3.1 Daily 4-metric monitor automation(retrieval recall + answer relevancy + faithfulness + latency p95)— `backend/eval/runner.py` against real query subset
- [ ] F3.2 Cost dashboard daily review(`/observability/cost-summary?window_hours=24` per F5.2;flag spend > projected × 1.2 alert)
- [ ] F3.3 User satisfaction tracking(👍/👎 ratio + Slack `#ekp-beta` issue volume)
- [ ] F3.4 50% rollout EoW conditional gate evaluation(no Sev1/Sev2 incident + 4-metric within ±3pp baseline + cost ≤ projected × 1.2)
- [ ] F3.5 50% rollout activation if gate passes(125-250 users)— Stakeholder go/no-go re-cycle

## F4 — Runbook live exercise replacing W10 D5 tabletop substitute

- [x] F4.1 Runbook AF1 — `infrastructure/runbook/README.md §1.A` step 2 queue clarification(append: `"queue" = Slack #ekp-beta thread + bugs/BUG-{NNN}` instance — no separate queue infra Tier 1) ✅ W11 D1
- [x] F4.2 Runbook AF2 — `§2 step 2 Azure OpenAI tier-1` append `"+ ACA revision restart required (Settings env-var bound;not hot-reload)"` ✅ W11 D1
- [x] F4.3 Runbook AF3 — `§2 step 2 Azure OpenAI tier-3` rewrite to use `OPENAI_API_KEY=''` env override(actual mechanism)instead of「set `app.state.synthesizer = None`」 ✅ W11 D1
- [x] F4.4 Runbook AF4 — `§2 root cause investigation` add explicit「per-user block IS NOT IMPLEMENTED Tier 1;path is Slack ask user pause + Entra ID role removal via IT helpdesk」+ Tier 2 trigger flag ✅ W11 D1
- [ ] F4.5 Runbook live exercise — Chris + AI walk through `runbook/README.md §1 + §2` against live ACA env within 72h post-Track A LIVE deploy
- [ ] F4.6 Update `runbook/README.md` Update history with live exercise outcome

## F5 — Q15 first weekly signal report + Q4 deployment pricing rate confirm

- [ ] F5.1 Q15 first weekly signal report W11 EoW:`python -m observability.weekly_signal_report --queries <real-cohort-corpus> --feedback <real-feedback-corpus> --week 2026-W24 --output reports/weekly-signal-W24.md`
- [x] F5.2 Q4 deployment pricing rate confirmation ✅ W11 D1 — **Option B path chosen**(Karpathy §1.2 favoured per W11 prep deck §6.1 + Stakeholder authorization 2026-06-09):placeholder rates preserved(`backend/observability/realtime_cost.py::_PRICING_TABLE` 不變;label `placeholder_publicly_quoted_rates_2026-Q2`)+ `cost_spike` rule × 1.5x ceiling preserved(`backend/observability/alerts.py` existing rule;rolling 7-day avg comparison serves anomaly detection intent)+ 7-day re-baseline post real cohort traffic W11+ scheduled。Option A NOT CHOSEN(spec-completeness ROI 不及 Beta timeline pressure;real cohort traffic 第一週自然校準)
- [x] F5.3 Tier 2 trigger metric review(per W11 prep deck §3 W11.F5)— signal-driven decision on GraphRAG / multi-agent / multi-modal trigger gates(per architecture.md §11)✅ W11 D1 — `docs/03-implementation/tier-2-trigger-review-W11.md` 7 sections + 3 risks;0/8 capability triggers fired + 0/5 GraphRAG triggers fired;decision frame for post-W12 monthly evaluation gate cycle

## F6 — Phase Gate closeout + W11 retro + W12-production-launch phase folder kickoff

- [ ] F6.1 W11 phase Gate verdict landed
- [ ] F6.2 W11 progress.md retro 7 sections complete
- [ ] F6.3 W12-production-launch phase folder kickoff(`docs/01-planning/W12-production-launch/{plan,checklist,progress}.md` draft per architecture.md §6.1 W12 row + Beta plan v1 §3 W12)
- [ ] F6.4 W11 progress.md frontmatter status flipped to `closed`
- [ ] F6.5 R-B1 closure verification(if F1.6 landed)+ R5 Azure quota status update post-LIVE-deploy real signal
- [ ] F6.6 OQ Q11 + Q15 + Q6 + Q4 pricing sync to decision-form.md per outcome

---

## Cross-Cutting

- [ ] Each commit references `progress.md` Day-N entry(R2)
- [ ] Component tag in commit message per CC-1
- [ ] OQ status sync to `decision-form.md`(R4)— Q11 + Q15 + Q6 + Q4 pricing W11 critical
- [ ] Risk register update if R-B1 status changes(close on F1.6 verdict;re-escalation if 2026-06-08 仍未 IT deliver)
- [ ] CLAUDE.md §5.5 H5 security check:no secret commit;real query log PII-stripped before commit
- [ ] Track A LIVE deploy → Track B 25% rollout → 50% conditional gate sequence preserved

---

**Lifecycle reminder**:呢份 checklist 衍生自 `plan.md` deliverables。新加 deliverable 必須先入 plan + changelog,然後再加 checklist item。
