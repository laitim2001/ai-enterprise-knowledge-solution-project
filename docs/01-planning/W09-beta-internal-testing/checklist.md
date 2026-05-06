---
phase: W09-beta-internal-testing
plan_ref: ./plan.md
status: closed
last_updated: 2026-05-30
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
- [x] F4.2 Onboarding doc 1-page — **W9 D4 done 2026-05-29** — `docs/03-implementation/beta-cohort-onboarding-W11-W12.md` NEW 9-section guide:§1 login flow(3-step Entra ID SSO + AADSTS50011 troubleshoot)+ §2 query examples(good / marginal / bad — 多語 OK 粵語 + EN + OOS refusal explained;PII no-go)+ §3 feedback flow(👍/👎 + comment;Langfuse cloud encrypted;aggregate-only review)+ §4 known limitations(Drive KB scope + 2-5s normal latency + Q15 manual update frequency)+ §5 bug report template(Slack `#ekp-beta` + reproduction steps)+ §6 privacy notice(Q9 Internal classification + PII auto-redact + 90-day rolling + opt-out)+ §7 W11-W12 staged rollout context(25% → 100%)+ §8 quick-reference card(printable / bookmarkable)+ §9 update history;Karpathy §1.2 simplicity-first 1-page coverage;final cohort kickoff version W11 D1 post IT cred + DNS apply per W9 D1 三方 outcome
- [ ] F4.3 Entra ID app access provision:add users to app registration(or assign role if Pattern B)
- [ ] F4.4 First-cohort kick-off ping(Slack / email)+ feedback intake channel established

## F5 — Real query log collection scaffolding + progressive @observe decoration

- [ ] F5.1 Q6 owner identification:Chris confirm with Stakeholder W9 D1
- [x] F5.2 Progressive `@observe` decoration on query/synthesizer/crag stages — **W9 D1 done 2026-05-26 + W9 D2 LLM upgrade 2026-05-27 + W9 D3 CRAG cascade 2026-05-28** — W9 D1 baseline:`observe_async` 3-stage decoration(synthesizer / retrieval / crag.refine);10 tests。W9 D2:`observe_llm_async` decorator + `_emit_generation_safe` helper + H5 enforcement test;synthesizer.synthesize 切換 LLM decorator;7 tests。**W9 D3 CRAG cascade**:`@observe_llm_async` applied to `CragGrader.grade`(model_attr=deployment + extra=latency_ms+confidence)+ `CragGrader.rewrite_query`(model_attr=deployment + extra=latency_ms);`GradeResult` + `RewriteResult` dataclasses gained `deployment` field(default `""` for back-compat with empty-chunks early-return path);4 GradeResult/RewriteResult construction sites updated。CRAG-triggered queries now emit 3-4 generation events(initial synth + grader + optional rewriter + corrected synth)for full per-call cost rollup。`backend/tests/test_crag.py` 6 existing tests pass unchanged(zero regression)— CRAG decoration surgical-only。**W10+ progressive scope** = wire `observe_async` to query route handler for top-level trace + nest synthesizer/retrieval/crag.refine generations as children
- [x] F5.3 Real query log scaffolding — **W9 D3 done 2026-05-28** — `backend/observability/query_collector.py` NEW C07 module:`RealQueryRecord` Pydantic schema(query_hash + query_text + kb_id + timestamp + status_code + duration_ms + refused + crag_triggered + user_oid_redacted)+ `pii_strip()` regex baseline(email + phone + emp/ricoh ID → `<REDACTED_*>` placeholders per CLAUDE.md §5.5 H5)+ `dedupe_queries()` SHA-256 canonical hash collapse + `build_record()` helper assembles + redacts oid to 4-char slug + `to_yaml()` / `read_yaml()` / `write_yaml()` round-trip with collection_metadata header(phase + collection_owner + privacy_class + pii_strip_version + record_count + spec_ref);`docs/03-implementation/beta-real-queries-W9-W10.yaml` NEW 8-row mock corpus(printer config + RAPO 多語 query + toner + scan-to-email with PII demo + error code + OOS refusal demo + paper jam + IT helpdesk PII demo)bootstraps format ahead of real cohort;`backend/tests/test_query_collector.py` 24 unit tests cover PII strip 8 patterns + hash stability + dedup + redaction + YAML round-trip + mock corpus loads cleanly;**Karpathy §1.2 simplicity-first**:no live Langfuse fetch / no DB layer / regex PII baseline(NER classifier = Tier 2 trigger when corpus volume warrants);W11+ scope = plumb actual collection from Beta cohort traffic post-IT-cred populate(per W9 D1 三方 outcome)
- [ ] F5.4 Daily query distribution review(W9 D2-D5 + W10 daily):surface frequent-query patterns + failed queries

## F6 — Phase Gate closeout + W9 retro + W10 kickoff prep

- [x] F6.1 W9 phase Gate verdict landed — **W9 D5 done 2026-05-30** — PARTIAL PASS:Track A G1+G2+G3+G7(IT cred + LIVE deploy + LIVE smoke + Q11 final operational)deferred W10-W11 per W9 D1 三方 outcome IT delivery target early June real;Track B G4+G5+G6(F5 observability + F4.2 onboarding doc + W11 readiness scaffold)= 5/7 PASS
- [x] F6.2 W09 progress.md retro 7 sections complete — **W9 D5 done 2026-05-30** — What worked / What didn't work / Surprises / Carry-overs / ADR triggers / Phase Gate result / Phase status全部填寫
- [x] F6.3 W10 phase folder kickoff — **W9 D5 done 2026-05-30** — `docs/01-planning/W10-beta-iteration/` 三 file 建好(plan.md draft Track A LIVE deploy cascade + Track B implementation polish split + checklist.md ~28 items + progress.md Day 0 entry)
- [x] F6.4 W09 progress.md frontmatter status flipped to `closed` — **W9 D5 done 2026-05-30**(此 batch)
- [x] F6.5 R-B1 status update — **W9 D5 done 2026-05-30** — `RISK_REGISTER.md` R14 R-B1 timeline secured 🟡 Active monitor with confirmed deadline preserved(W9 D1 三方 outcome unchanged;closure trigger W10 Track A IT cred populate event)
- [x] F6.6 OQ Q11 status sync — **W9 D5 done 2026-05-30** — `decision-form.md` Q11 status `decision-level Resolved + operational committed early June 2026 real` preserved unchanged(no further outcome event since W9 D1 三方 alignment);final `Resolved` operational trigger event W10 Track A IT cred populate

## Cross-Cutting

- [x] **C11 dependency_overrides cleanup** — **W9 D5 done 2026-05-30** — refactored `test_api_skeleton.py:16-21` module-level `app.dependency_overrides[get_current_user]` set into `_mock_auth_override` autouse fixture-scoped pattern(install + yield + pop teardown);simplified `test_observability_routes.py:_isolate_app_state` defensive pop+restore workaround(leak source fixed,redundant);358/358 pytest pass — zero regression

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
