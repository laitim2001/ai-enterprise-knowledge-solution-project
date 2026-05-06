---
phase: W10-beta-iteration
plan_ref: ./plan.md
status: active
last_updated: 2026-06-02
---

# Phase W10 — Checklist

> Atomic checkbox(每 item ≤ 0.5–2 hour effort per W6 C10 calibration:LIVE deploy 2x;static 0.5x)。
> Status:`active` flipped 2026-06-02 W10 D1 Track B kickoff(Track A still blocked on IT cred populate event)。

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
- [ ] F4.4 F5.5 Pixel diff snapshots installation(if Vitest/Playwright harness available;non-Beta-blocking)

## F5 — W11 staged rollout readiness(Track B)

- [ ] F5.1 Runbook real-incident exercise(walk through §1 Document parse failure + §2 API quota exhaustion against staged ACA env)
- [x] F5.2 Cost dashboard real-time wire — **W10 D3 done 2026-06-04** — `backend/observability/realtime_cost.py` NEW C07 module(`_PRICING_TABLE` per-1k-token + per-call rates for gpt-5-5/gpt-5-4-mini/text-embedding-3-large/Cohere v3.5/v4-pro;`_rate_for` case-insensitive + prefix-tolerant lookup;`aggregate_generations` group-by-deployment with **unknown bucket preserved as zero-USD signal** + known-rows-first ordering;`fetch_realtime_usage` graceful 4-status wrapper [`no_client`/`sdk_method_missing`/`fetch_failed`/`ok`] with **test-injectable fetcher** + production `_default_fetcher` duck-types Langfuse 2.x SDK shapes for envelope + usage field + object/dict access variants);`backend/api/schemas/observability.py` C08 extended NEW `RealtimeUsageRow` + `CostSummary` realtime fields(backward-compatible defaults);`backend/api/routes/observability.py` C08 upgrade `/observability/cost-summary?window_hours=N`(Pydantic ge=1, le=720)hybrid response **static projection preserved + realtime usage embedded side-by-side**(no double-count);**always 200** even on fetch failure(observability never blocks dashboard render per Karpathy §1.2 + H6);**Karpathy §1.2 simplicity-first** — no live LLM API roundtrip required(fetcher injection)+ no DB layer + pricing table explicitly labelled `placeholder_publicly_quoted_rates_2026-Q2`(F5.4 stakeholder spend gate review flag);37 tests pass(30 realtime_cost + 7 endpoint;C07 + C08)
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
