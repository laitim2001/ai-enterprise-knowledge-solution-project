---
phase: W09-beta-internal-testing
plan_ref: ./plan.md
checklist_ref: ./checklist.md
status: active    # flipped draft→active 2026-05-26 W9 D1 kickoff(A+B parallel deliverable batch — alignment memo + observe wrapper)
---

# Phase W09 — Progress

> Daily progress + 結尾 retro。
> 每 commit 必須對應一個 Day-N entry mention(R2 binding rule per PROCESS.md §5)。
> Status:`draft` 自 2026-05-23 W8 D5 closeout cascade。

---

## Day 0 — 2026-05-23: Kickoff prep(W8 D5 末 closeout cascade same-session)

**Action**:Phase W09 kickoff prep(per PROCESS.md §2.3 rolling-JIT lifecycle;W8 D5 closeout cascade per CLAUDE.md §10 R5)

- Folder `docs/01-planning/W09-beta-internal-testing/` created
- `plan.md` filled with status=`draft`(6 deliverables F1-F6:R-B1 escalation alignment + Q11 final operational Resolved + Chris infra/IT/DNS apply cascade + LIVE smoke verification + Beta internal user onboarding + Real query log collection scaffolding + Progressive @observe decoration + Phase Gate closeout + W10 kickoff prep)
- `checklist.md` derived from plan deliverables(~31 atomic items)
- `progress.md` Day 0 entry initialized(this file)
- **Carry-over candidates from W08-beta-deploy-sprint2**(per W8 retro § Carry-overs C1-C11):
  - C1 Q11 IT operational confirm cascade(F1)— **W8 D5 escalation 觸發**;W9 D1 三方 alignment session needed
  - C2 F1.4 LIVE switch + F1.5 + F1.7 LIVE smoke(F3.1 + F3.2)
  - C3 F3.2 SWA DNS + F3.3 Entra ID portal apply(F2.4 + F2.5)
  - C4 F2.4 Key Vault populate + F2.5 ACA networking Bicep apply(F2.2 + F2.3)
  - C5 F4.3 W4/W5 LIVE smoke remainder + F3.5 + F4.5 LIVE smoke real dev server(F3.3 + F3.4 + F3.5)
  - C6 F5.3 Admin Console feedback view UI 仍 deferred(C10 not yet built)
  - C7 F5.5 Pixel diff snapshots installation 非 W9 scope(non-Beta-blocking)
  - C8 Progressive @observe decoration on query/synthesizer/crag(F5.2)
  - C9 Q6 Real query collection owner trigger(F5.1)
  - C10 Beta internal testing user roster(F4.1)
  - C11 dependency_overrides cleanup 非 W9 scope(non-Beta-blocking;W9+ test infrastructure cleanup window)
- **W9 critical path identification**:**R-B1 🔴 Active escalation 2026-05-23**;F1.1 三方 alignment session = W9 D1 critical path;若 IT delivery commit date 仍 push → escalation Stakeholder cycle re-engage(W11-W12 production launch milestone risk transparency surface)
- **Beta internal testing entry**:W7 closes Beta hardening Sprint 1;W8 closes Beta deploy Sprint 2(implementation spec-complete + observability cascade + LIVE deploy gates deferred);W9 = Beta internal testing(Chris IT/infra/DNS apply cascade + LIVE smoke + first-cohort onboarding + real query log scaffolding);W10 = Beta iteration / UX polish;W11-W12 = staged rollout 25% → 100% per architecture.md §6.1 timeline

### Decisions / OQ summary

- W8 closeout PARTIAL PASS verdict landed(G1' + G4 substitute + G5 + G6 PASS = 4/7;G1 + G2 + G3 + G7 deferred W9 per Chris IT/infra/DNS external dependency cascade)
- Q11 status `decision-level Resolved + operational pending W9`;decision-form.md updated W8 D5 closeout same-session;final operational Resolved trigger W9 D1
- Q6 Real query collection owner trigger W9 per architecture.md §6.1 W9 row;F5.1 acceptance criterion
- W8 commits = single F5+F4.4+F6 batch + backfill pair(per W7 closeout pattern)

### Open / blocked

- ⏸ W9 D1 implementation start awaiting Chris W8 closeout sign-off + W9 D1 三方 alignment session outcome + Q11 final operational confirm
- ⏸ W9 plan/checklist status `draft → active` flip W9 D1 trigger

### Commit reference

- W8 D5 closeout commit `ccdddf4`(W09 phase folder included in W8 closeout batch per F6.3 acceptance)

---

## Day 1 — 2026-05-26: A+B parallel pre-session deliverables(R-B1 alignment memo + F5.2-kickoff observe wrapper)

**Action**:W9 D1 kickoff — F1.1 三方 alignment session 本身屬人類協調工作(Stakeholder + IT manager + Chris meeting),AI 無法 conduct;F1.2-F1.4 全 Chris external action。Per Karpathy §1.1 think-before-coding,AI 並行交付兩件 pre-session-actionable deliverables:**A. R-B1 alignment memo for Chris(pre-session prep aid)**+ **B. F5.2-kickoff observe wrapper module + 3-stage decoration(W8 retro § Carry-over C8 closing)**。F5.1 Q6 owner identification + F2.4 KV populate 全 IT-cred-gated,defer post-session 自然 cascade。**Architecture impact zero**;observe wrapper屬 C07 implementation living code(non-architectural per CLAUDE.md §5.1 H1)。

**A. R-B1 alignment memo for Chris**:
- `docs/03-implementation/r-b1-alignment-memo-2026-05-26.md` NEW — pre-session prep doc:
  - §1 Executive summary 30-second read(implementation production-ready;唯一 missing piece = IT cred delivery;past escalation threshold)
  - §2 Background — W6 D5 stakeholder approval cycle Q11 decision-level Resolved + a-revised mock auth strategy revision
  - §3 Current state W7-W8 done(implementation spec-complete + Chris-cascade SOPs ready + 322/322 pytest)
  - §4 Current state W9 deferred(G1 + G2 + G3 + G7 blockers all external)
  - §5 The Ask — IT 5-step deliverables(Pattern A combined SPA+API recommended + Pattern B compliance fallback)
  - §6 Decision options A/B/C/D for the session(W9 D2-D3 commit / W9 D5 slip / escalation cycle / Pattern B pivot)
  - §7 Risk implications — W11-W12 production launch milestone compression rate per slip-day
  - §8 Pre-session suggested agenda(20 min)+ §9 post-session action items template + §10 reference quick-links
- Audience:Chris(primary)+ Stakeholder + IT manager;Chris consume + sanitize as needed for distribution

**B. F5.2-kickoff observe wrapper(C07 — W8 retro § Carry-over C8)**:
- `backend/observability/observe.py` NEW — `@observe_async` decorator with three design tenets:
  - **Degrade-graceful**:wrapper NEVER raises into wrapped fn path;Langfuse client absent / `trace()` raise / SDK API drift all become no-ops with structured warning logs
  - **Surgical decoration**:single decorator covers query / synthesizer / retrieval / crag stages without touching their bodies;`capture_attrs` extracts attributes from awaited result for per-stage cost attribution
  - **Always-emit structlog**:`stage_complete` / `stage_failed` JSON log line emitted unconditionally;audit pipeline + future log-based cost reconstruction both benefit
- `_emit_trace_safe()` helper — three Langfuse SDK API shape tolerance(2.x trace + legacy variants)+ swallow every failure mode
- W9 D2+ progressive scope seam ready:upgrade `client.trace()` → `client.generation()` for LLM-stage cost-attribution dashboard flow real-time USD per query

**3-stage decoration applied(Karpathy §1.3 surgical — single line decoration each)**:
- `backend/generation/synthesizer.py:Synthesizer.synthesize` — `@observe_async(name="synthesizer.synthesize", capture_attrs=("input_tokens","output_tokens","latency_ms","refused"))` composed with existing `@retry` stack(observe captures FINAL outcome after retries — verified via `test_decorator_composes_with_tenacity_retry`)
- `backend/retrieval/retrieval_engine.py:RetrievalEngine.retrieve` — `@observe_async(name="retrieval.retrieve", capture_attrs=("embed_latency_ms","search_latency_ms","rerank_latency_ms","total_latency_ms","reranked"))` — full timing breakdown surfaces in trace metadata
- `backend/generation/crag.py:CragLoop.refine` — `@observe_async(name="crag.refine", capture_attrs=("triggered","iterations","confidence_before","confidence_after","fallback_used"))` — CRAG decision provenance captured

**Tests(F5.2-kickoff coverage — +10 new tests = baseline 312 → 322)**:
- `backend/tests/test_observe.py` NEW(10 tests):
  - Happy paths:wrapper-without-client returns unchanged + stage_complete log emit + capture_attrs extracts + capture_attrs skips missing + default-name uses qualname
  - Failure paths:trace_emit_failure swallowed + client-without-trace-method noop + wrapped-exception propagates with stage_failed
  - Integration:signature preserved for FastAPI Depends introspection + decorator composes with tenacity @retry
- structlog stdlib factory bridge in fixture autouse(matches `test_audit_log.py` pattern;caplog captures `ekp.observe` events)

**Verification**:
- `pytest -q` → **322 passed in 99.11s**(W8 D5 baseline 312 + observe wrapper +10 = 322;zero regression on synthesizer / retrieval / crag downstream tests)
- `ruff check observability/observe.py tests/test_observe.py generation/synthesizer.py generation/crag.py retrieval/retrieval_engine.py` → All checks passed!(after auto-fix import sort on synthesizer.py)
- frontend tsc + eslint unchanged(no frontend code changes W9 D1)

**Karpathy §1 alignment**:
- §1.1 think-before-coding:**explicitly surfaced** that 三方 alignment session 屬人類協調工作 not AI work — proposed A+B prep-while-blocked pattern;memo gives Chris pre-session leverage(decision options A-D mapped + W11-W12 milestone risk transparency surface);observe wrapper degrade-graceful pattern survives Langfuse cred populate cycle independent of Q11 outcome
- §1.2 simplicity-first:`@observe_async` thin wrapper over `client.trace()`(NOT custom span/segment hierarchy);`capture_attrs` tuple extracts attributes from result without modifying SynthesisResult / RetrievalResult / CragOutcome bodies;structlog stdlib bridge in fixture matches existing `test_audit_log.py` pattern(consistent test infrastructure)
- §1.3 surgical:3-stage decoration = 3 single-line `@observe_async(...)` adds + 1 import per file;zero edit to method bodies;wrapper file isolated in `observability/` package(C07 component spine)
- §1.4 goal-driven:F5.2-kickoff verifiable goal "trace span emitted when client wired + structlog event emitted always + wrapper preserves signature for FastAPI" — 10 unit tests close loop;322/322 full-suite pytest verifies zero regression

**Hard constraints check**:
- H1 architecture lock — ✅ no §3 / §4 component change;observe wrapper屬 C07 implementation living code per architecture.md §3.1 Langfuse correlation
- H2 vendor lock — ✅ zero new dep(Langfuse SDK already locked W8 D5 F5.1)
- H3 Dify reference — ✅ untouched
- H4 Tier 1 boundary — ✅ no Tier 2 滲入(custom span hierarchy / sampling tuning / multi-region 全 explicit Tier 2 in `infrastructure/observability/README.md` §Tier 2)
- H5 security — ✅ wrapper does NOT log function arguments(only result attributes via explicit `capture_attrs`)— no PII / prompt content leak
- H6 test coverage — ✅ +10 tests for critical C07 wrapper module + integration smoke

### Decisions / OQ summary
- No OQ change(F1.1 三方 session 未 fire — outcome 待 W9 D1 session 後 sync)
- No ADR triggered W9 D1(observe wrapper屬 architecture.md §3.1 Langfuse correlation implementation;non-architectural amendment per CLAUDE.md §5.1 H1 boundary)

### Open / blocked
- ⏸ **F1.1 三方 alignment session** — W9 D1 human coordination work in-progress external;outcome 待 Chris sync(per `r-b1-alignment-memo-2026-05-26.md` §9 post-session action items template)
- ⏸ F1.2 IT cred delivery — Pattern A 5-step depends on session outcome
- ⏸ F1.3 + F1.4 Q11 + R-B1 status update — post-session
- ⏸ F2.1-F2.6 Chris infra apply cascade — IT cred + DNS session post-F1
- ⏸ F3.1-F3.5 LIVE smoke verification — F2 deploy + Chris dev server post-F1+F2
- ⏸ F4.1-F4.4 Beta cohort onboarding — F2 + F3 LIVE smoke pass post-F1+F2+F3
- ⏸ F5.1 Q6 owner identification — Chris confirm with Stakeholder W9 D1 session window OR follow-up
- ⏸ F5.3 Real query log scaffolding + F5.4 daily query review — F4 cohort onboarded post-F4

### Commit reference
- W9 D1 commit `579e336`(9 files changed,+706 / -7;3 new files + 6 modified;single feat(observability,docs) batch per W7+W8 closeout pattern;A R-B1 alignment memo + B F5.2-kickoff observe wrapper + 3-stage decoration synthesizer/retrieval/crag)

---

## Day 1 cont — 2026-05-26: 三方 session outcome briefing + governance cascade

**Action**:Chris 攜 `r-b1-alignment-memo-2026-05-26.md` 入三方 session;outcome briefing landed same-day W9 D1。AI cascade governance updates per memo §9 post-session action items template。

**Session outcome(per Chris briefing)**:
1. **Timeline**:**Option B-extended**(memo §6 framework)— IT manager committed delivery target **early June 2026 real-calendar(~2026-06-02 to 2026-06-07)**;maps to project doc calendar approximately W11 deploy window
2. **Topology**:**Pattern A combined SPA+API confirmed**(memo §5.1)— NO Pattern B compliance push from Stakeholder / IT manager
3. **Domain**:**`ekp-beta.ricoh.com`** confirmed for Beta SWA(memo Section 1 default)
4. **Bridge strategy**:**Mock auth dev mode continues** until IT cred populate;real-calendar context = today 2026-05-06,implementation front-runs project doc calendar ~3-4 週,IT 4-week wait fits production launch milestone window naturally(W11-W12 staged rollout phase per architecture.md §6.1)

**Governance cascade landed(per memo §9 template)**:
- `docs/decision-form.md` Q11 — `Resolved` decision-level + **operational committed early June 2026 real**(was "operational pending W9");final `Resolved` operational trigger等 IT cred populate
- `docs/01-planning/RISK_REGISTER.md` R14 R-B1 — 🔴 **Active escalation 2026-05-23 → 🟡 Active monitor with confirmed deadline 2026-05-26**(W9 D1 outcome de-escalation);re-escalation trigger 若 real 2026-06-08 仍未 deliver
- `docs/01-planning/W09-beta-internal-testing/plan.md` §1 scope re-baselined + §7 changelog 2026-05-26 deviation entry per R3 — F1.2-F1.4 + F2 + F3 + F4 LIVE deploy cascade defer to **project W11**;W9-W10 active focus = F5 observability progressive + Q6 owner trigger + W11 production launch readiness doc polish + C11 dependency_overrides cleanup
- `docs/01-planning/W09-beta-internal-testing/checklist.md` F1.1 ✅ ticked + F1.3 ✅ partial(decision update done;final Resolved post-IT)+ F1.4 ✅(R-B1 de-escalated)
- F1.2 IT cred populate **DEFER project W11**(checklist item updated with explicit defer marker per CLAUDE.md sacred rule for unchecked `[ ]` items)

**W9-W10 re-baselined active scope(post 三方 outcome)**:
- F5.1 Q6 Real query collection owner identification(non-IT-blocked;Chris with Stakeholder)
- F5.2 progressive @observe upgrade(W9 D1 baseline ready;W9 D2+ upgrade `client.trace()` → `client.generation()` for real-time LLM cost-attribution per W9 plan §2 F5.2)
- F5.3 Real query log scaffolding with mock data(synthetic corpus to validate scaffolding logic — exercises pipeline before real cohort onboarding)
- F4.2 Onboarding doc draft(content prep — actual provisioning推 W11)
- W11 production launch readiness doc polish(runbook + rollback SOP per architecture.md §7.4 Day-2 Readiness)
- C11 dependency_overrides cleanup(W8 retro § Carry-over)— test infrastructure technical debt
- F6 W9 closeout + W10 phase folder rolling-JIT kickoff

**Karpathy §1 alignment**:
- §1.1 think-before-coding:Chris briefing surfaced critical real-calendar context(implementation front-runs project doc ~3-4 週)which transforms IT 4-week wait from "Beta-blocking" to "natural milestone alignment";re-baselined scope without panic — production launch window preserved
- §1.2 simplicity-first:re-baseline via plan.md changelog + checklist updates,NOT via plan rewrite or W10 phase folder pre-build(rolling-JIT preserved per CLAUDE.md §10);W9-W10 scope concentrates on non-IT-blocked work — zero waste
- §1.3 surgical:governance cascade touches 4 files(decision-form + RISK_REGISTER + W9 plan §1+§7 + W9 checklist + W9 progress);zero spec drift;Pattern A confirmation closes Pattern B branch in `infrastructure/entra-id/README.md` 但 SOP 文 retain 全部(audit trail)
- §1.4 goal-driven:R3 plan deviation log entry verifiable;R-B1 de-escalation trigger conditions explicit;W9-W10 re-baselined deliverables each have unblocked acceptance path

**Hard constraints check**:
- H1 architecture lock — ✅ no §3 / §4 component change(governance update only)
- H2 vendor lock — ✅ Pattern A confirmation = locked Microsoft Entra ID single app registration(architecture.md §6.1 W7+ baseline)
- H3 Dify reference — ✅ untouched
- H4 Tier 1 boundary — ✅ Beta phase work re-baselined within Tier 1 scope
- H5 security — ✅ Pattern A NO client secret needed(simpler attack surface)
- H6 test coverage — ✅ no test changes needed for governance cascade

### Decisions / OQ summary
- **Q11 operational status update**:decision-level Resolved 2026-05-05 PRESERVED + operational committed early June 2026 real(was "pending W9")— sync to `decision-form.md`(R4 binding rule)
- No new OQ;F4 Beta cohort onboarding deferred → Q7 final user roster sync stays W11
- No ADR triggered(Pattern A confirmation = within architecture.md §6.1 default path;non-architectural)

### Open / blocked(W9-W10 re-baselined)
- ⏸ F1.2 IT cred populate to Key Vault — **DEFER project W11**(post real-early-June);Chris coordinates with IT
- ⏸ F2.1-F2.6 Chris infra apply cascade — **DEFER project W11**(post-IT cred)
- ⏸ F3.1-F3.5 LIVE smoke verification — **DEFER project W11**(post-F2)
- ⏸ F4.1 Final user roster + F4.3 Entra ID app access provision + F4.4 First-cohort kick-off — **DEFER project W11**(post-F3 LIVE smoke)
- ⏸ F4.2 Onboarding doc draft — **W9-W10 actionable**(content prep)
- ⏸ F5.1 Q6 Real query collection owner — **W9 D2 actionable**(Chris with Stakeholder)
- ⏸ F5.2 progressive @observe `client.generation()` upgrade — **W9 D2-D5 actionable**(F5.1 SDK seam ready)
- ⏸ F5.3 Real query log scaffolding(mock data corpus)— **W9 D2-D5 actionable**
- ⏸ W11 production launch readiness runbook + rollback SOP — **W9-W10 actionable**

### Commit reference
- W9 D1 cont commit `099c751`(5 files changed,+87 / -11;0 new files + 5 modified;decision-form Q11 + RISK_REGISTER R14 R-B1 de-escalation + W9 plan §1 scope re-baseline + §7 R3 deviation log + W9 checklist F1.1/F1.3/F1.4 ticked + W9 progress Day 1 cont entry)

---

## Day 2 — _(pending)_

---

## Retro(填於 W9 D5 末)

### What worked
_(W9 D5 末 fill)_

### What didn't work / unexpected friction
_(W9 D5 末)_

### Surprises / discoveries
_(W9 D5 末)_

### Carry-overs to W10-beta-iteration
_(W9 D5 末)_

### ADR triggers
_(W9 D5 末 — ADR-0013 reservation candidate:Q11 escalation cycle Stakeholder re-engage outcome OR Q6 owner identification + real query distribution signals OR Tier 2 trigger)_

### Phase Gate result(per plan.md §3 + architecture.md §7 acceptance)
- G1-G7:_(W9 D5 末)_
- **W9 Beta internal testing verdict**:_(W9 D5 末)_ → ready for W10 Beta iteration / require additional polish

### Phase status
- Closeout commit:_(W9 D5 末)_
- Frontmatter status flipped to `closed`:_(W9 D5 末)_
- Phase W10 kickoff trigger:_(W9 D5 末 — W10 plan = UX iteration + bug fix + W11 staged rollout 25% prep per architecture.md §6.1 W10 row)_

---
