---
phase: W10-beta-iteration
plan_ref: ./plan.md
checklist_ref: ./checklist.md
status: active   # `draft → active` flipped 2026-06-02 W10 D1 Track B kickoff(per plan §7 changelog)
---

# Phase W10 — Progress

> Daily progress + 結尾 retro。
> 每 commit 必須對應一個 Day-N entry mention(R2 binding rule per PROCESS.md §5)。
> Status:`active` flipped 2026-06-02 W10 D1 Track B kickoff。

---

## Day 0 — 2026-05-30: Kickoff prep(W9 D5 末 closeout cascade same-session)

**Action**:Phase W10 kickoff prep(per PROCESS.md §2.3 rolling-JIT lifecycle;W9 D5 closeout cascade per CLAUDE.md §10 R5)

- Folder `docs/01-planning/W10-beta-iteration/` created
- `plan.md` filled with status=`draft`(6 deliverables F1-F6 split into Track A LIVE deploy cascade + Track B implementation polish — IT cred timing唔 block Track B per W9 D1 三方 outcome cascade)
- `checklist.md` derived from plan deliverables(~28 atomic items)
- `progress.md` Day 0 entry initialized(this file)
- **Carry-over candidates from W09-beta-internal-testing**(per W9 retro § Carry-overs):
  - IT cred populate trigger(F1.1)— Track A activation event;target early June real-calendar
  - Chris infra/IT/DNS apply cascade(F2)— Track A
  - LIVE smoke verification(F3.1-F3.4)— Track A
  - Beta cohort onboarding(F3.5-F3.6)— Track A;onboarding doc W9 D4 ready,Chris finalise contact info
  - observe_streaming decorator(F4.1)— Track B(W9 D4 deferred for SSE flow capture variant)
  - Live query collection plumbing(F5.2)— Track B(W9 D3 query_collector scaffolding ready,plumb to audit_log / Langfuse generations API)
  - Runbook real-incident exercise(F5.1)— Track B(W9 D2 runbook authored,exercise post-deploy)
  - Q15 manual update frequency signal(F4.3)— Track B
  - F5.5 Pixel diff snapshots(W7 carry-over)— Track B polish window
- **W10 critical path**:
  - **Track A trigger**:IT cred populate event — fires F1.2 → F2.1-F2.7 → F3.1-F3.6 cascade in single multi-stakeholder coordination cycle
  - **Track B continuous**:F4 + F5 implementation polish + W11 staged rollout prep regardless of Track A timing
- **W11 staged rollout phase entry**:W10 closes Beta iteration / IT cred-bridge phase;W11 = staged rollout 25%(per architecture.md §6.1 W11 row + beta-plan-v1.md §3);W12 = 100% rollout post Stakeholder go/no-go gate

### Decisions / OQ summary

- W9 closeout PARTIAL PASS verdict landed(F5 + F4.2 + F6 closeout completed without IT cred per W9 D1 三方 outcome cascade)
- Q11 status:`decision-level Resolved + operational committed early June 2026 real`(unchanged from W9 D1 三方 outcome until IT cred populate event Track A activation)
- Q6 + Q15 + Q21 deferred to W10-W11 real-cohort signal(per architecture.md §6.1 + Beta plan deviation log W9 plan §7)
- W9 commits = 5 daily batches(W9 D1 + D1 cont + D2 + D3 + D4 + D5;each `feat` + `docs(planning)` backfill pair)

### Open / blocked

- ⏸ W10 D1 implementation start awaiting Chris W9 closeout sign-off + Track A IT cred populate trigger event(target early June real)
- ⏸ W10 plan/checklist status `draft → active` flip W10 D1 trigger
- ⏸ Track A cascade fires per IT cred timing(could W10 D1 / D2 / D3 OR slip to W11)
- ⏸ Track B continues unblocked W10 D1+

### Commit reference

- W9 D5 closeout commit `8e78fd7`(W10 phase folder included in W9 closeout batch per F6.3 acceptance)

---

## Day 1 — 2026-06-02: Track B kickoff(F4.1 observe_streaming + F4.2 eval-set augmentation pipeline)

**Action**:Track B implementation polish kickoff per W9 D5 closeout cascade — IT-cred-independent batch closes W9 D4 SSE flow capture carry-over + W9 D3 query_collector plumbing carry-over;Track A still blocked on IT cred populate event(real-calendar target ~2026-06-02 to 2026-06-07,not yet fired)

- W10 plan/checklist/progress 三 file frontmatter `draft → active` flipped(per R1 implementation start gate;changelog entry 2026-06-02 in plan §7 records Chris W9 closeout sign-off + Track B kickoff trigger)
- **F4.1 ✅ done — `observe_streaming` SSE wrapper(closes W9 D4 carry-over)**
  - `backend/observability/observe.py`:NEW async-iterator passthrough wrapper `observe_streaming(stream, *, name, done_event_type, model_field, input_tokens_field, output_tokens_field, extra_metadata_fields)`(C07)
  - **Surgical decoration design**:helper-function shape(NOT decorator)matches the natural seam in SSE handler — `compose_query_stream(...)` returns an async iterator,wrapper passes events through unchanged so Vercel AI SDK frame ordering preserved exactly(text-delta* citation* done)
  - **Cancellation-graceful**:`asyncio.CancelledError` caught + re-raised + `client.generation()` emitted with `status=cancelled`(client disconnect mid-stream still books partial-spend cost attribution truthfully)
  - **Exception-graceful**:mid-stream exception → `status=error` + `error_type` captured + `stream_terminated` log + propagate(observability never blocks the request path,per Karpathy §1.2 + H5)
  - **H5 SECURITY enforced**:wrapper passes ONLY token counts + model + structured metadata to Langfuse;`text-delta` content + `citation` payloads NEVER captured into trace metadata(test `test_observe_streaming_h5_no_text_delta_content_in_metadata` asserts the negative directly via `repr(kwargs)` substring check)
  - `backend/api/routes/query.py`:`/query/stream` route's `event_serializer` wraps `compose_query_stream(...)` with `observe_streaming(name="api.query.stream", extra_metadata_fields=("refused", "reranker_used"))`(C08)
  - **Tests**:`backend/tests/test_observe.py` +8 cases(done frame capture / no-done-frame graceful / no-op when client absent / cancellation status / exception status / emit failure swallowed / H5 negative assertion / extra_metadata only from done event)
- **F4.2 ✅ done — Eval-set augmentation pipeline(closes W9 D3 query_collector plumbing carry-over)**
  - `backend/eval/eval_set_augmentor.py`:NEW C06 module + CLI(`python -m eval.eval_set_augmentor --eval-set ... --real-corpus ... --output ... [--dry-run] [--start-qid N]`)
  - **Pipeline**:real query corpus(query_collector YAML)→ candidate eval-set entry stubs(SME-validation schema)→ dedup against existing eval set canonical hashes + within-corpus → emit augmented YAML(NEW file,never overwrite source SME-validated eval set)
  - **Karpathy §1.2 simplicity-first**:no LLM-driven topic classification(`query_type` heuristic = `oos` if refused,else `single_step_lookup`;SME refines)+ no difficulty heuristic(empty for SME)+ no in-place overwrite(safety guard via `ValueError` when `output_path == eval_set_path`)+ no external API
  - **Schema match**:candidate stubs match `eval-set-v1-draft.yaml` Q001+ entry shape(`query_id` / `query_text` / `query_phrasing_source=real_user_W10` / `difficulty=""` / `query_type` / `ground_truth.{primary,acceptable,screenshot}_chunk_ids=[]` / `expected_answer_keywords=[]` / `expected_refusal` mirrors record / `annotation.validated=False` + notes embed corpus provenance fields hash + duration_ms + crag_triggered + user_oid_redacted)
  - **Canonicalisation alignment**:`_canonical()` deliberately duplicates `query_collector._canonical()` rule + guard test `test_canonical_matches_query_collector` enforces lockstep(both must move together if dedup behaviour evolves)
  - **MergeReport dataclass**:per-record `CandidateOutcome`(query_text + canonical_hash + accepted + reason ∈ {added/duplicate_of_existing/duplicate_within_corpus} + assigned_qid)+ aggregate stats(existing_count + candidate_count + added_count + duplicate_against_existing + duplicate_within_corpus + next_qid + dry_run flag)— stable contract for downstream tooling(CLI report formatter + W11+ RAGAs runner integration)
  - **Tests**:`backend/tests/test_eval_set_augmentor.py` NEW +20 cases(canonical alignment guard / `existing_query_hashes` / `next_query_id` default + non-Qxxx skip / candidate schema match v1-draft + refused→oos + ground_truth fields / dedup against existing / dedup within corpus via raw YAML bypass `write_yaml` dedup / dry-run skips write + reports `output_path=None` truthfully / writes augmented YAML + augmentation header round-trip / refuses overwrite source / dry-run no `--output` required / no candidates → no write + `output_path=None` / start-qid override / preserves existing queries verbatim / outcomes one-per-record / CLI dry-run exit 0 / CLI missing --output without --dry-run = exit 2 / CLI full-run writes file / MergeReport field set contract)
- **Tests**:**358 → 386**(+28,zero regression — full backend pytest sweep `pytest -q` exit 0 in 58.07s)
- **Lint**:`ruff check --fix` cleaned 2 import-grouping issues in F4.2 module + tests(I001;same auto-fix pattern as W9 D5 C11 cleanup)

### Track A status(unchanged W10 D1)

- ⏸ IT cred populate event NOT yet fired(real-calendar target early June 2026 ~2026-06-02 to 2026-06-07 per W9 D1 三方 outcome — Chris IT engagement cascade pending);**target W10 D2-D5 OR W11 trigger window**
- 🟡 R-B1 status preserved:Active monitor with confirmed deadline(re-escalation trigger if real 2026-06-08 仍未 deliver)
- F1 / F2 / F3 / F3.5-F3.6 cascade ALL waiting on event;W7-W12 production launch milestone window remains comfortable

### Track B progress

- F4.1 ✅(observe_streaming SSE flow capture variant — closes W9 D4 deferred carry-over)
- F4.2 ✅(eval-set augmentation pipeline — closes W9 D3 query_collector plumbing carry-over)
- F4.3 ⏳ Q15 manual update frequency signal scaffold(W10 D3 target — weekly Langfuse + Slack aggregation)
- F4.4 ⏳ F5.5 Pixel diff snapshots installation(non-Beta-blocking;W10 D4-D5 polish window candidate)
- F5.1-F5.4 ⏳ W11 staged rollout readiness(W10 D4-D5 — runbook real-incident exercise + cost dashboard real-time wire + onboarding doc final + Stakeholder go/no-go prep deck)

### Decisions / OQ summary

- No architectural change(observe_streaming = additive C07 helper extending observe.py family;eval_set_augmentor = additive C06 tool — both within architecture.md v5.1 §3 + §6.3 spec scope)
- No ADR triggered(spec implementation per Karpathy §1.3 surgical;ADR-0012 still reserved for W10 Track A IT cred populate trigger)
- No OQ status change(Q11 Resolved decision-level + operational committed early June real preserved;Q6 + Q15 still 🔴 Open await real-cohort signal)
- No R-B1 status change(🟡 Active monitor with confirmed deadline preserved per W9 D1 三方 outcome)

### Open / blocked

- ⏸ Track A cascade(F1.2 + F2.1-F2.7 + F3.1-F3.6)blocked on IT cred populate event;Track B continues unblocked
- ⏸ F4.3 Q15 weekly aggregation scaffold(W10 D2-D3)
- ⏸ F4.4 Pixel diff harness installation check(W10 D4-D5)
- ⏸ F5 W11 readiness items(W10 D4-D5;F5.1 runbook exercise depends on staged ACA env per Track A)

### Commit reference

- W10 D1 commit `85aa8f4`(feat — Track B F4.1 observe_streaming + F4.2 eval-set augmentor batch;C06 + C07 + C08)
- W10 D1 backfill commit `86c5b36`(docs(planning) — hash backfill to W10 D1 entry per R2)

---

## Day 2 — 2026-06-03: F4.3 Q15 weekly signal scaffold + Track A monitor

**Action**:Track B F4.3 Q15 manual update frequency signal scaffold lands(closes W10 plan §2 F4.3 acceptance)+ Track A trigger watching governance(R-B1 monitor pass-through;real-calendar still within IT delivery target window)。Single-day surgical batch — no Track A event signal received yet。

- **F4.3 ✅ done — `weekly_signal_report.py` Q15 scaffold(C07)**
  - `backend/observability/weekly_signal_report.py` NEW module:`FeedbackRecord` Pydantic schema(parallels `RealQueryRecord` shape;adds optional `query_hash` join key for cross-corpus correlation)+ `TopQuery` + `WeeklyAggregation` dataclasses(volume summary + top-N per signal axis)+ `parse_iso_week()` ISO-8601 → `YYYY-Www` label + `aggregate_week` / `aggregate_all_weeks` partitioners + `read_feedback_yaml()` reader + `render_markdown()` report generator + `main()` CLI
  - **Three signal axes per Q15 governance pattern**:(1)**Frequency** top-N most-asked queries(high-volume topics → manual coverage priority)+(2)**Refusal cluster** top-N OOS-refused queries(coverage gap signal)+(3)**CRAG-triggered cluster** top-N(rewrite needed = ambiguity / outdated content)+(4)**Negative feedback** thumbs_down with PII-stripped comment preview joined by `query_hash` to query corpus
  - **Karpathy §1.2 simplicity-first**:no live API fetch(offline YAML inputs match W9 D3 query_collector bootstrap precedent)+ no NLP topic modelling(top-N by raw frequency;SME spots patterns in report)+ no DB layer(Markdown-on-disk output)+ feedback comment H5 PII strip belt-and-braces via `query_collector.pii_strip` reuse(consistent across observability modules)
  - **W11+ scope explicit**:hook live Langfuse generations API for trace-id ↔ feedback correlation + Slack `#ekp-beta` channel scrape for "outdated" / "old version" mention frequency(currently scaffold,real cohort traffic plumbs post-IT-cred populate)
  - **CLI**:`python -m observability.weekly_signal_report --queries QUERIES.yaml [--feedback FEEDBACK.yaml] [--output OUT.md] [--week 2026-W23] [--top-n N]`(stdout default;file write optional;single-week filter optional)
  - **Mock feedback corpus**:`docs/03-implementation/beta-feedback-W9-W10.yaml` NEW 6-row mock(3 thumbs_up + 3 thumbs_down with PII-demo comment + cross-references to `beta-real-queries-W9-W10.yaml` query_hash values so the cross-join lights up in the scaffold's negative-feedback section)
  - **Tests**:`backend/tests/test_weekly_signal_report.py` NEW +33 cases(ISO-week parser:Z suffix / +00:00 offset / date-only / year-boundary / garbage rejection / current week well-formed;Aggregation:volume summary / top frequent ordering / refusal segregation from frequency / CRAG segregation / top-N cap / negative feedback join / unknown when no query_hash / PII strip belt-and-braces / empty inputs;Multi-week:partition by ISO week / week filter / empty corpora / skip unparseable timestamps;Feedback YAML:round-trip / datetime coercion;Markdown render:required sections / empty placeholder / per-section empty placeholder / long text truncation;CLI:stdout default / output file write / feedback corpus integration / week filter / missing input file = exit 2;Smoke:dataclass field-set contracts + mock corpus loads cleanly)
- **Tests**:**386 → 419**(+33 zero regression — full backend pytest sweep `pytest -q` exit 0 in 88.65s)
- **Lint**:`ruff check --fix` cleaned 1 import-grouping issue(I001;same pattern as W10 D1)

### Track A status(W10 D2 monitor pass-through)

- ⏸ IT cred populate event still NOT fired(real-calendar W10 D2 = 2026-06-03;target window 2026-06-02 to 2026-06-07 per W9 D1 三方 outcome;**4-day buffer remaining within target,no early-trigger signal yet**)
- 🟡 R-B1 status:**Active monitor preserved unchanged**(re-escalation deadline 2026-06-08 still 5 days out;within target window so 🟡 → 🔴 trigger NOT armed)
- Q11 status:`Resolved` decision-level + **operational committed early June real** unchanged(no operational trigger event since W9 D1 三方 alignment)
- W7-W12 production launch milestone window:**comfortable**(real-calendar 4-week IT wait fits naturally per W9 D1 outcome briefing — implementation front-runs project doc ~3-4 週,total real-calendar slack remains)

### Track B progress

- F4.1 ✅(observe_streaming;W10 D1)
- F4.2 ✅(eval-set augmentation pipeline;W10 D1)
- F4.3 ✅(weekly_signal_report Q15 scaffold;W10 D2 today)
- F4.4 ⏳ F5.5 Pixel diff snapshots installation(non-Beta-blocking;W10 D4-D5 polish window candidate)
- F5.1 ⏳ Runbook real-incident exercise(W10 D4-D5;blocked on staged ACA env per Track A)
- F5.2 ⏳ Cost dashboard real-time wire(W10 D3-D4 target — plumb Langfuse generations API delta into `/observability/cost-summary`;**partially unblocked** by F4.3 scaffold which proved YAML offline → Markdown report pipeline,same shape applies)
- F5.3 ⏳ Onboarding doc final review(W10 D4-D5;blocked on Chris IT helpdesk contact populate)
- F5.4 ⏳ W11 staged rollout 25% prep deck(W10 D4-D5)

### Decisions / OQ summary

- No architectural change(weekly_signal_report = additive C07 module extending observability suite — `query_collector` + `langfuse_tracer` + `audit_log` middleware family;within architecture.md v5.1 §3 + §7.4 Day-2 Readiness scope)
- No ADR triggered(spec implementation per Karpathy §1.3 surgical;ADR-0012 still reserved for W10 Track A IT cred populate trigger)
- No OQ status change(Q11 + Q15 + Q6 unchanged;Q15 scaffold ready BUT real-cohort signal still 🔴 Open until cohort traffic flows post-IT-cred populate W11+)
- No R-B1 status change(🟡 Active monitor preserved per real-calendar within-target-window context)

### Open / blocked

- ⏸ Track A cascade still blocked on IT cred populate event;Track B continues unblocked
- ⏸ F4.4 Pixel diff harness installation check(W10 D4-D5)
- ⏸ F5.1 Runbook real-incident exercise(staged ACA env dependency)
- ⏸ F5.2 Cost dashboard real-time wire(W10 D3-D4 candidate)
- ⏸ F5.3 Onboarding doc final review(IT helpdesk contact dependency)

### Commit reference

- W10 D2 commit:_(pending — will backfill after `feat` + `docs(planning)` pair)_

### What worked
_(W10 D5 末 fill)_

### What didn't work / unexpected friction
_(W10 D5 末)_

### Surprises / discoveries
_(W10 D5 末)_

### Carry-overs to W11-staged-rollout-25
_(W10 D5 末)_

### ADR triggers
_(W10 D5 末 — ADR-0013 reservation candidate per W10 outcome)_

### Phase Gate result(per plan.md §3 + architecture.md §7 acceptance)
- G1-G7:_(W10 D5 末)_
- **W10 Beta iteration verdict**:_(W10 D5 末)_ → ready for W11 staged rollout 25% / require additional polish

### Phase status
- Closeout commit:_(W10 D5 末)_
- Frontmatter status flipped to `closed`:_(W10 D5 末)_
- Phase W11 kickoff trigger:_(W10 D5 末 — W11 plan = staged rollout 25% + cohort expansion + production launch readiness final review per architecture.md §6.1 W11 row)_

---
