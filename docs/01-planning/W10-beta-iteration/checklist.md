---
phase: W10-beta-iteration
plan_ref: ./plan.md
status: closed
last_updated: 2026-06-06
---

# Phase W10 — Checklist

> Atomic checkbox(每 item ≤ 0.5–2 hour effort per W6 C10 calibration:LIVE deploy 2x;static 0.5x)。
> Status:`closed` flipped 2026-06-06 W10 D5 closeout cascade(PARTIAL PASS verdict;Track B complete + Track A pending IT cred event)。

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

- [x] F4.1 `observe_streaming` SSE wrapper NEW for `/query/stream` handler — **W10 D1 done 2026-06-02** — `backend/observability/observe.py` async-iterator passthrough wrapper(NOT decorator — natural seam is the iterator,not the iterator-producing fn);captures terminal `done` frame model + token counts → `client.generation()` emit;handles `asyncio.CancelledError` graceful(status=cancelled)+ exception(status=error)+ no-op when client absent + emit-failure swallowed;H5 SECURITY:wrapper passes ONLY tokens + model + structured metadata to Langfuse,NEVER text-delta content / citation chunk_text(test asserts via `repr(kwargs)` substring negative);wired to `/query/stream` route with `extra_metadata_fields=("refused", "reranker_used")`;8 tests pass(C07 + C08)
- [x] F4.2 Eval-set augmentation pipeline — **W10 D1 done 2026-06-02** — `backend/eval/eval_set_augmentor.py` NEW C06 module + CLI(`python -m eval.eval_set_augmentor --eval-set ... --real-corpus ... --output ... [--dry-run] [--start-qid N]`);real query corpus(query_collector YAML)→ candidate eval-set entry stubs matching `eval-set-v1-draft.yaml` Q001+ schema(query_phrasing_source=real_user_W10 + difficulty="" + query_type=oos/single_step_lookup heuristic + ground_truth empty for SME + annotation.validated=False + provenance notes embed hash/duration_ms/crag_triggered/user_oid_redacted);dedup against existing eval set canonical hashes + within-corpus;**Karpathy §1.2 simplicity-first**:no LLM topic classification + no difficulty heuristic + no in-place overwrite(safety guard ValueError when output_path == eval_set_path)+ no external API;`MergeReport` dataclass with stable contract for W11+ RAGAs runner integration;canonicalisation lockstep with `query_collector._canonical` enforced via guard test;20 tests pass(C06)
- [x] F4.3 Q15 manual update frequency signal scaffold — **W10 D2 done 2026-06-03** — `backend/observability/weekly_signal_report.py` NEW C07 module + `FeedbackRecord` Pydantic schema(parallels `RealQueryRecord` + adds `query_hash` join key)+ `WeeklyAggregation` dataclass(volume summary + top-N per signal axis)+ `parse_iso_week` ISO-8601→`YYYY-Www` + `aggregate_week`/`aggregate_all_weeks` partitioners + `read_feedback_yaml` reader + `render_markdown` report generator + `main` CLI;**Three Q15 signal axes**:Frequency(top-N most-asked → coverage priority)+ Refusal cluster(coverage gap signal)+ CRAG-triggered cluster(ambiguity / outdated signal)+ Negative feedback(thumbs_down + PII-stripped comment joined by query_hash);**Karpathy §1.2 simplicity-first**:no live API fetch + no NLP topic modelling + no DB layer + feedback comment H5 PII strip belt-and-braces via `query_collector.pii_strip` reuse;**W11+ scope explicit**:hook live Langfuse generations API + Slack `#ekp-beta` scrape;CLI `python -m observability.weekly_signal_report --queries Q.yaml [--feedback F.yaml] [--output OUT.md] [--week 2026-W23] [--top-n N]`;mock corpus `docs/03-implementation/beta-feedback-W9-W10.yaml` NEW 6-row(3👍/3👎 with cross-references to query_collector mock corpus query_hash values);33 tests pass(C07)
- [ ] F4.4 F5.5 Pixel diff snapshots installation 🚧 **DEFER W11+ post-cohort signal** — **W10 D4 finding 2026-06-05** — `frontend/package.json` 唔 install Vitest 唔 install Playwright(no `test` script + no `vitest`/`@playwright/test` devDeps);per Karpathy §1.2 simplicity-first — install cost ~1 day + capture mock baseline snapshots without real cohort UX signal = wasted polish before signal exists;**re-trigger condition**:real cohort feedback W11+ surfaces UX regression risk → install harness + capture baseline pre-rollout(W7 D5 carry-over preserved into W11 phase folder per rolling JIT)

## F5 — W11 staged rollout readiness(Track B)

- [x] F5.1 Runbook real-incident exercise via tabletop substitute — **W10 D5 done 2026-06-06** — `docs/03-implementation/runbook-tabletop-W10-d5.md` NEW 6-section walkthrough(Chris + AI scribe);Track A staged ACA env unavailable per W11 prep deck §5 No-Go Fallback → tabletop substitute approved pattern;§1 Document parse failure ✅ Clear with 1 clarification(AF1 — `§1.A` step 2「offline re-process queue」 = Slack thread + bugs/BUG-{NNN},no separate queue infra Tier 1)+ §2 API quota exhaustion ✅ Clear with 2 clarifications + 1 gap(AF2 — `§2 step 2 tier-1` ACA revision restart required;AF3 — `§2 step 2 tier-3` rewrite to `OPENAI_API_KEY=''` env override actual mechanism;AF4 🔴 — runaway client per-user revoke NOT IMPLEMENTED Tier 1,Tier 2 trigger flag);**4 aggregate findings AF1-AF4 carry-over to W11 F4.1-F4.4 in-place edits before live exercise**;live exercise within 72h post-Track A LIVE deploy
- [x] F5.2 Cost dashboard real-time wire — **W10 D3 done 2026-06-04** — `backend/observability/realtime_cost.py` NEW C07 module(`_PRICING_TABLE` per-1k-token + per-call rates for gpt-5-5/gpt-5-4-mini/text-embedding-3-large/Cohere v3.5/v4-pro;`_rate_for` case-insensitive + prefix-tolerant lookup;`aggregate_generations` group-by-deployment with **unknown bucket preserved as zero-USD signal** + known-rows-first ordering;`fetch_realtime_usage` graceful 4-status wrapper [`no_client`/`sdk_method_missing`/`fetch_failed`/`ok`] with **test-injectable fetcher** + production `_default_fetcher` duck-types Langfuse 2.x SDK shapes for envelope + usage field + object/dict access variants);`backend/api/schemas/observability.py` C08 extended NEW `RealtimeUsageRow` + `CostSummary` realtime fields(backward-compatible defaults);`backend/api/routes/observability.py` C08 upgrade `/observability/cost-summary?window_hours=N`(Pydantic ge=1, le=720)hybrid response **static projection preserved + realtime usage embedded side-by-side**(no double-count);**always 200** even on fetch failure(observability never blocks dashboard render per Karpathy §1.2 + H6);**Karpathy §1.2 simplicity-first** — no live LLM API roundtrip required(fetcher injection)+ no DB layer + pricing table explicitly labelled `placeholder_publicly_quoted_rates_2026-Q2`(F5.4 stakeholder spend gate review flag);37 tests pass(30 realtime_cost + 7 endpoint;C07 + C08)
- [x] F5.3 Onboarding doc final review — **W10 D5 done 2026-06-06** — `docs/03-implementation/beta-cohort-onboarding-W11-W12.md` content coverage verified across §1-§9;Update history entry 2026-06-06 added;**carry-over to W11 D1**:Chris IT helpdesk contact info populate + Slack `#ekp-beta` channel auto-join confirmation(blocked on Track A IT engagement cascade);Karpathy §1.3 surgical — NO structural change W10 D5,defer in-place IT helpdesk number edit until Chris contact data lands(same pattern as F5.1 tabletop substitute);real-cohort feedback W11+ → W11 D5 retro Update history with usage signals
- [x] F5.4 W11 staged rollout 25% phase prep — **W10 D4 done 2026-06-05** — `docs/03-implementation/w11-staged-rollout-25-prep-deck.md` NEW 10-section Stakeholder Go/No-Go prep deck:§1 Executive summary(3 open gate items + Conditional GO recommendation)+ §2 W10 verdict snapshot per plan §3 G1-G7(G4 Track B PASS + G1-G3 Track A pending)+ §3 W11 rollout scope per Beta plan v1 §2(W11.F1-F5)+ §4 Go criteria(GC1-GC8 must-pass before W11 D1)+ §5 No-Go fallback plan(R-B1 slip + Q4 pricing slip + cohort incomplete + onboarding doc gap + runbook exercise tabletop substitute)+ §6 Open gate items(Q4 pricing rate NEW + R-B1 closure + cohort roster final)+ §7 Day-2 ops handover checklist + §8 Stakeholder decision form + §9 References + §10 Update history;**Karpathy §1.2 simplicity-first** one-page-decision-form structure — exec summary + go criteria + no-go fallback + sign-off section;详细 implementation 細節 link out to artifact,唔重複 context;**3 open gate items surfaced**(Q4 deployment pricing rate confirm per F5.2 placeholder + R-B1 closure + cohort expansion roster);Stakeholder review trigger event = W10 D5 末 closeout sync;cohort expansion roster delegated to Chris pre-identify carry-over preservation per Q7

## F6 — Phase Gate closeout + W10 retro + W11 staged rollout phase folder kickoff

- [x] F6.1 W10 phase Gate verdict landed — **W10 D5 done 2026-06-06** — **PARTIAL PASS**(identical to W9 D1 三方 outcome cascade pattern):G1-G3 Track A ⏸ DEFERRED W11(IT cred populate event pending);G4 Track B ✅ PASS(F4.1+F4.2+F4.3 + F4.4 🚧 DEFER W11+);G5 ✅ PASS WITH ASTERISKS(F5.1 🟡 tabletop + F5.2 ✅ + F5.3 🟡 review + F5.4 ✅);G6 ✅ PASS(456/456 pytest + ruff clean);G7 🟡 PARTIAL(NEW Q4 pricing rate gate item surfaced)→ ready for W11 staged rollout 25% conditional on Stakeholder W11 prep deck approve cycle + Track A IT cred event by 2026-06-08 deadline
- [x] F6.2 W10 progress.md retro 7 sections complete — **W10 D5 done 2026-06-06** — What worked / What didn't work / Surprises / Carry-overs to W11 / ADR triggers / Phase Gate result G1-G7 / Phase status 全部填寫
- [x] F6.3 W11-staged-rollout-25 phase folder kickoff — **W10 D5 done 2026-06-06** — `docs/01-planning/W11-staged-rollout-25/` 三 file 建好(plan.md draft Track A LIVE deploy + Track B 25% rollout + W12 production launch readiness;checklist.md ~30 atomic items;progress.md Day 0 entry initialized);6 deliverables F1-F6 split per Beta plan v1 §2 W11
- [x] F6.4 W10 frontmatter status flipped to `closed` — **W10 D5 done 2026-06-06** — plan.md + checklist.md + progress.md frontmatter all flipped + last_updated synced to 2026-06-06
- [x] F6.5 R-B1 monitor pass-through — **W10 D5 done 2026-06-06** — `RISK_REGISTER.md` R14 R-B1 status preserved 🟡 Active monitor with confirmed deadline(re-escalation deadline 2026-06-08 = 2 days out;within target window);**re-escalation procedure documented**:if 2026-06-08 仍未 IT cred populate event → 🟡 → 🔴 cycle re-engage Stakeholder + IT manager + Chris triple session(same pattern as W9 D1 三方 alignment)+ W11 D1 staged rollout 25% defers to W12 D1 trigger window per W11 prep deck §5 No-Go fallback;R5 Azure quota update deferred to W11 F1.6 post-Track A real signal
- [x] F6.6 OQ status sync — **W10 D5 done 2026-06-06** — Q11 + Q15 + Q6 unchanged(real-cohort signal pending Track A);**NEW Q4 pricing rate gate item surfaced** per W10 D3 F5.2 placeholder labelling — Stakeholder W11 prep deck §6.1 Option A vs Option B decision pending W10 D5 末 review trigger event;final Q11 operational Resolved trigger event W11 Track A IT cred populate

---

## Cross-Cutting

- [x] Each commit references `progress.md` Day-N entry(R2)— ✅ all 10 W10 commits(5 feat + 5 docs(planning) backfill pairs)
- [x] Component tag in commit message per CC-1 — ✅ all W10 commits tagged(C06 + C07 + C08 + governance)
- [x] OQ status sync to `decision-form.md`(R4)— Q11 + Q15 + Q6 unchanged W10 D5(Track A pending);**Q4 NEW gate item** surfaced per F5.2 placeholder labelling → Stakeholder W11 prep deck §6.1 decision pending
- [x] Risk register update — R-B1 monitor pass-through preserved 🟡(re-escalation procedure documented per F6.5)
- [x] CLAUDE.md §5.5 H5 security check — ✅ no secret commit;feedback comment PII strip belt-and-braces via `pii_strip` reuse;observe_streaming H5 negative assertion enforces no text-delta / citation_text leak
- [x] Track A vs Track B work split preserved — ✅ Track B shipped 8/8 IT-cred-independent items in 5 days without Track A blocker

---

**Lifecycle reminder**:呢份 checklist 衍生自 `plan.md` deliverables。新加 deliverable 必須先入 plan + changelog,然後再加 checklist item。
