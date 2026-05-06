---
phase: W09-beta-internal-testing
plan_ref: ./plan.md
status: active
last_updated: 2026-05-26 cont
---

# Phase W09 — Checklist

> Atomic checkbox(每 item ≤ 0.5–2 hour effort per W6 C10 calibration:LIVE deploy 2x;static 0.5x)。
> Status:`draft` 自 2026-05-23 W8 D5 closeout cascade。
> 全 unchecked 至 W9 D1 implementation start。

## F1 — R-B1 escalation alignment + Q11 final operational Resolved

- [x] **CRITICAL R-B1** F1.1 W9 D1 三方 alignment session — **W9 D1 done 2026-05-26** — Stakeholder + IT manager + Chris session outcome:**Option B-extended**(IT 預期 early June 2026 real-calendar deliver ~2026-06-02 to 2026-06-07)+ **Pattern A combined SPA+API confirmed**(NO Pattern B compliance push)+ **domain `ekp-beta.ricoh.com` confirmed**;mock auth bridge continues until IT cred populate;real-calendar context = implementation front-runs real ~3-4 週,IT 4-week wait fits production launch milestone window naturally
- [ ] F1.2 IT cred delivery — **DEFER project W11**(post real-early-June IT cred populate per Chris infra session):`AZURE_TENANT_ID` + `AZURE_CLIENT_ID` populated to Key Vault per `infrastructure/keyvault/README.md`(Pattern A — NO `AZURE_CLIENT_SECRET` needed)
- [x] F1.3 Q11 status update partial — **W9 D1 done 2026-05-26** — `decision-form.md` Q11 updated:`Resolved` decision-level + **operational committed early June 2026 real**(was "operational pending W9");final `Resolved` operational trigger 等 IT cred populate(post real-early-June)
- [x] F1.4 R-B1 status update — **W9 D1 done 2026-05-26** — `RISK_REGISTER.md` R14 R-B1 🔴 **Active escalation 2026-05-23 → 🟡 Active monitor with confirmed deadline 2026-05-26**(W9 D1 三方 outcome de-escalation);re-escalation trigger 若 real 2026-06-08 仍未 deliver

## F2 — Chris infra/IT/DNS apply cascade

- [ ] F2.1 Backend ACA deploy via `.github/workflows/backend-deploy.yml`(W8 D2 spec ready)+ rollback path verified
- [ ] F2.2 Key Vault populate 6 secrets(azure-openai-api-key + azure-search-admin-key + cohere-api-key + azure-tenant-id + azure-client-id + azure-client-secret)+ Managed Identity grant `Key Vault Secrets User`
- [ ] F2.3 ACA networking apply:`infrastructure/aca/networking.bicep` Private Endpoint + DNS zone group attach;disable Search public access AFTER PE verified
- [ ] F2.4 Entra ID app registration apply:Pattern A 8-step per `infrastructure/entra-id/README.md`(redirect URIs + post-logout URIs + Expose API scope + admin consent)
- [ ] F2.5 SWA custom domain apply:`ekp-beta.ricoh.com` per `infrastructure/swa/README.md`(Azure portal Add → Ricoh corp DNS CNAME + TXT → Validate → cert provisioned)
- [ ] F2.6 SWA deploy via `.github/workflows/frontend-deploy.yml`(W8 D3 spec ready)

## F3 — LIVE smoke verification(W7 + W8 carry-overs)

- [ ] F3.1 F1.5 LIVE smoke:dev tenant Entra ID end-to-end login flow(uvicorn + pnpm dev or staged ACA + SWA)per `infrastructure/entra-id/README.md` step 8
- [ ] F3.2 F1.7 LIVE smoke acceptance(W7 plan §3 G1):full redirect round-trip + `/query` 200 with real identity propagated through audit pipeline
- [ ] F3.3 F3.5 LIVE smoke(W7 carry-over):5 query through dev / staged server → Langfuse trace audit tags + request_id traceable
- [ ] F3.4 F4.5 LIVE smoke(W7 carry-over):trigger E1 + E5 + E12 graceful UX cases verified
- [ ] F3.5 W4/W5 LIVE smoke remainder(W6 C3):PPT E2E + GPT-5.5 latency baseline + Chat UI screenshots

## F4 — Beta internal user onboarding

- [ ] F4.1 Final user roster confirm with Chris(per Q7;~5-10 first-cohort)
- [ ] F4.2 Onboarding doc 1-page:login + query example + feedback button + bug reporting channel
- [ ] F4.3 Entra ID app access provision:add users to app registration(or assign role if Pattern B)
- [ ] F4.4 First-cohort kick-off ping(Slack / email)+ feedback intake channel established

## F5 — Real query log collection scaffolding + progressive @observe decoration

- [ ] F5.1 Q6 owner identification:Chris confirm with Stakeholder W9 D1
- [x] F5.2 Progressive `@observe` decoration on query/synthesizer/crag stages — **W9 D1 done 2026-05-26** — `backend/observability/observe.py` NEW thin wrapper(`observe_async` decorator + `_emit_trace_safe` helper);3-stage decoration:`Synthesizer.synthesize`(capture `input_tokens` + `output_tokens` + `latency_ms` + `refused`)+ `RetrievalEngine.retrieve`(capture embed/search/rerank/total latency + reranked flag)+ `CragLoop.refine`(capture triggered + iterations + confidence_before/after + fallback_used);`backend/tests/test_observe.py` 10 unit tests(happy paths + Langfuse emit failure swallowed + tenacity retry compose + signature preservation);wrapper degrade-graceful when Langfuse client absent(local dev / CI no-op);**W9 D2+ progressive scope = upgrade `client.trace()` → `client.generation()` for LLM-stage so cost-attribution dashboard flows real-time USD per query**(seam ready);322/322 pytest pass
- [ ] F5.3 Real query log scaffolding:audit_log → `docs/03-implementation/beta-real-queries-W9-W10.yaml`(deduplicated;PII-stripped per H5)
- [ ] F5.4 Daily query distribution review(W9 D2-D5 + W10 daily):surface frequent-query patterns + failed queries

## F6 — Phase Gate closeout + W9 retro + W10 kickoff prep

- [ ] F6.1 W9 phase Gate verdict landed
- [ ] F6.2 W09 progress.md retro 7 sections complete
- [ ] F6.3 W10 phase folder kickoff:`docs/01-planning/W10-beta-iteration/{plan,checklist,progress}.md` draft
- [ ] F6.4 W09 progress.md frontmatter status flipped to `closed`
- [ ] F6.5 R-B1 closure(if Q11 + LIVE smoke landed)or status update(if escalation cycle ongoing)
- [ ] F6.6 OQ Q11 final operational Resolved + Q6 Real query collection owner Resolved sync to `decision-form.md`

---

## Cross-Cutting

- [ ] Each commit references `progress.md` Day-N entry(R2)
- [ ] Component tag in commit message per CC-1
- [ ] OQ status sync to `decision-form.md`(R4)— Q11 final operational + Q6 owner W9 critical
- [ ] Risk register update if R-B1 status changes(close on F1.4 verdict)
- [ ] CLAUDE.md §5.5 H5 security check:no secret commit;real query log PII-stripped before commit
- [ ] Each LIVE smoke run logs LLM spend to cost dashboard for daily review

---

**Lifecycle reminder**:呢份 checklist 衍生自 `plan.md` deliverables。新加 deliverable 必須先入 plan + changelog,然後再加 checklist item。
