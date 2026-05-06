---
phase: W10-beta-iteration
plan_ref: ./plan.md
status: draft
last_updated: 2026-05-30
---

# Phase W10 — Checklist

> Atomic checkbox(每 item ≤ 0.5–2 hour effort per W6 C10 calibration:LIVE deploy 2x;static 0.5x)。
> Status:`draft` 自 2026-05-30 W9 D5 closeout cascade。

## F1 — Q11 final operational Resolved + R-B1 closure(Track A — IT cred trigger)

- [ ] F1.1 IT cred delivered(`AZURE_TENANT_ID` + `AZURE_CLIENT_ID` per Pattern A)— trigger event
- [ ] F1.2 Cred populated to Key Vault per `infrastructure/keyvault/README.md`
- [ ] F1.3 `decision-form.md` Q11 status `decision-level Resolved + operational committed early June real` → `Resolved` operational(final)
- [ ] F1.4 `RISK_REGISTER.md` R14 R-B1 status 🟡 Active monitor → 🟢 Mitigated

## F2 — Chris infra/IT/DNS apply cascade execution + F1.4 LIVE switch(Track A)

- [ ] F2.1 ACA backend deploy via `.github/workflows/backend-deploy.yml`
- [ ] F2.2 Key Vault populate 6 secrets + Managed Identity grant
- [ ] F2.3 ACA networking apply(Private Endpoint + DNS zone link;disable Search public access)
- [ ] F2.4 Entra ID app registration apply(Pattern A 8-step per `infrastructure/entra-id/README.md`)
- [ ] F2.5 SWA custom domain apply(`ekp-beta.ricoh.com` per Ricoh corp DNS team)
- [ ] F2.6 SWA frontend deploy via `.github/workflows/frontend-deploy.yml`
- [ ] F2.7 F1.4 LIVE switch:`Settings.feature_auth_mock=False` env override + ACA revision restart;`NEXT_PUBLIC_AUTH_MOCK=false` GHA env update + SWA re-deploy

## F3 — LIVE smoke verification + Beta cohort onboarding(Track A)

- [ ] F3.1 F1.5 LIVE smoke + F1.7 LIVE smoke per `infrastructure/entra-id/README.md` step 8
- [ ] F3.2 F3.5 LIVE smoke audit chain through dev / staged server
- [ ] F3.3 F4.5 LIVE smoke E1 + E5 + E12 graceful UX
- [ ] F3.4 W4/W5 LIVE smoke remainder(PPT E2E + GPT-5.5 latency baseline + Chat UI screenshots)
- [ ] F3.5 Beta cohort first-cohort access provisioning(Entra ID role assignment + onboarding doc final IT helpdesk contact populate + Slack `#ekp-beta` auto-join)
- [ ] F3.6 First-cohort kick-off ping + feedback intake established

## F4 — Implementation polish(Track B — IT-cred-independent)

- [ ] F4.1 `observe_streaming` decorator NEW for `/query/stream` SSE handler(W9 D4 deferred)
- [ ] F4.2 Eval-set augmentation pipeline(`query_collector.py` real query corpus → eval set merge tool)
- [ ] F4.3 Q15 manual update frequency signal scaffold(weekly cohort feedback aggregation report from Langfuse + Slack)
- [ ] F4.4 F5.5 Pixel diff snapshots installation(if Vitest/Playwright harness available;non-Beta-blocking)

## F5 — W11 staged rollout readiness(Track B)

- [ ] F5.1 Runbook real-incident exercise(walk through §1 Document parse failure + §2 API quota exhaustion against staged ACA env)
- [ ] F5.2 Cost dashboard real-time wire(plumb query_collector → audit_log stream OR Langfuse generations API for `/observability/cost-summary` upgrade)
- [ ] F5.3 Onboarding doc final review(Chris populate IT helpdesk contact + Slack auto-join + Q7 cohort signup process)
- [ ] F5.4 W11 staged rollout 25% phase prep:Stakeholder go/no-go review prep deck + cohort expansion roster

## F6 — Phase Gate closeout + W10 retro + W11 staged rollout phase folder kickoff

- [ ] F6.1 W10 phase Gate verdict landed
- [ ] F6.2 W10 progress.md retro 7 sections complete
- [ ] F6.3 W11-staged-rollout-25 phase folder kickoff(`docs/01-planning/W11-staged-rollout-25/{plan,checklist,progress}.md` draft)
- [ ] F6.4 W10 progress.md frontmatter status flipped to `closed`
- [ ] F6.5 R-B1 closure verification + R5 Azure quota status update post-LIVE-deploy real signal
- [ ] F6.6 OQ Q11 + Q15 + Q6 sync to decision-form.md per outcome

---

## Cross-Cutting

- [ ] Each commit references `progress.md` Day-N entry(R2)
- [ ] Component tag in commit message per CC-1
- [ ] OQ status sync to `decision-form.md`(R4)— Q11 final operational + Q15 + Q6 W10 critical
- [ ] Risk register update if R-B1 status changes(close on F1.4 verdict;re-escalation if W10 D5 仍未 IT deliver)
- [ ] CLAUDE.md §5.5 H5 security check:no secret commit;real query log PII-stripped before commit
- [ ] Track A vs Track B work split preserved — IT cred timing唔 block Track B implementation polish

---

**Lifecycle reminder**:呢份 checklist 衍生自 `plan.md` deliverables。新加 deliverable 必須先入 plan + changelog,然後再加 checklist item。
