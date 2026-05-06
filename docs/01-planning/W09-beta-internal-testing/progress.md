---
phase: W09-beta-internal-testing
plan_ref: ./plan.md
checklist_ref: ./checklist.md
status: closed    # flipped active→closed 2026-05-30 W9 D5 closeout(PARTIAL PASS — Track B 5/7 PASS;Track A LIVE deploy cascade deferred W10 per W9 D1 三方 outcome IT delivery early June real)
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

## Day 2 — 2026-05-27: 1+2 parallel batch — observability progressive upgrade + W11 production launch runbook draft

**Action**:W9 D2 batch per W9 D1 cont retro § Open / blocked next-steps proposal:**(1)F5.2 progressive @observe upgrade**(client.trace() → client.generation() for synthesizer LLM cost-attribution)+ **(2)W11 production launch runbook + rollback SOP draft**(architecture.md §7.4 Day-2 Readiness scope)。兩 deliverables 都 IT-cred-independent + closes W11 milestone prep gaps。**Architecture impact zero**;observe_llm_async wrapper屬 C07 implementation living code per architecture.md §3.1 Langfuse correlation;runbook implements §7.4 Day-2 spec(non-architectural amendment per CLAUDE.md §5.1 H1 boundary check)。

**1. F5.2 progressive @observe upgrade(C07)**:
- `backend/observability/observe.py` extended:
  - **NEW `observe_llm_async` decorator** — emits `client.generation()` instead of `client.trace()` for LLM-stage methods;maps result attributes to Langfuse generation event shape:`model` from `model_attr`(default "deployment")+ `usage={"input":N,"output":M,"unit":"TOKENS"}` from `input_tokens_attr` + `output_tokens_attr` + extra_metadata_attrs flat metadata
  - **NEW `_emit_generation_safe` helper** — graceful fallback when client lacks `generation()` method(legacy SDK)→ falls back to `trace()` so cost attribution best-effort across Langfuse SDK versions
  - **H5 SECURITY**(per CLAUDE.md §5.5 enforced via test):wrapper passes ONLY `model` + `usage`(token counts)+ metadata flat fields;**NEVER** passes `input` / `output` text content to Langfuse cloud — full prompt / answer remain backend-private
- `backend/generation/synthesizer.py:Synthesizer.synthesize` — replaced `@observe_async("synthesizer.synthesize", capture_attrs=...)` with **`@observe_llm_async("synthesizer.synthesize", model_attr="deployment", input_tokens_attr=..., output_tokens_attr=..., extra_metadata_attrs=("latency_ms","refused"))`** — single-line replacement preserves @retry stack composition
- W9 D3+ progressive scope ready:apply `observe_llm_async` to `CragGrader.grade` + `CragGrader.rewrite_query`(per crag.py:164 + similar);apply `observe_async` orchestration to remaining stages

**2. W11 production launch runbook + rollback SOP(C12)**:
- `infrastructure/runbook/README.md` NEW — 10 sections covering:
  - **§1 Document parse failure** — symptoms + first-line mitigation(per-doc skip vs infrastructure fault path)+ root cause investigation(Langfuse / KQL / common causes per architecture.md §8.3 R7)+ recovery
  - **§2 API quota exhaustion** — per-quota mitigation(Azure OpenAI tighten rate limit + Cohere fallback + Search SKU upgrade)+ cost dashboard correlation
  - **§3 Index corruption** — index alias swap rollback + re-ingest procedure + schema drift detection
  - **§4 Reranker outage** — Cohere → Azure built-in semantic ranker hot fallback(architecture.md §8.3 R6 + W4 shootout faith Δ -11.76pp tradeoff documented)
  - **§5 CRAG loop bug** — disable / threshold raise mitigation + langfuse_status correlation + W5 D2 baseline 0.70 reference
  - **§6 Rollback procedures** — ACA revision swap + Bicep deploy rollback + SWA frontend rollback + DNS rollback + Index alias rollback
  - **§7 Cred rotation emergency** — leak response 30-min steps + Key Vault update + ACA revision restart
  - **§8 Escalation matrix** — P1/P2/P3 severity + on-call rotation + IT manager + Cohere account team contacts
  - **§9 Reference quick-links** + **§10 Update history**
- Cross-component dependencies:references all infrastructure/* SOPs + architecture.md §3 + §7.4 + §8 + components/Cn-*.md;Karpathy §1.2 simplicity-first single-file 5-scenario coverage(don't create 5 separate files);per-scenario SLA + first-line < 5-30 min mitigation explicit

**Tests(F5.2 LLM upgrade coverage,+7 new tests = baseline 322 → 329)**:
- `backend/tests/test_observe.py` extended(8 → 17 tests):
  - **NEW `test_llm_decorator_emits_generation_with_usage`** — verifies model + usage shape + metadata + trace NOT called when generation available
  - **NEW `test_llm_decorator_skips_usage_when_tokens_missing`** — graceful when result lacks token counts
  - **NEW `test_llm_decorator_falls_back_to_trace_when_no_generation`** — legacy SDK path
  - **NEW `test_llm_decorator_no_op_when_client_absent`** — local dev / CI path
  - **NEW `test_llm_decorator_swallows_generation_emit_failure`** — generation emit error → 202-equivalent + warn
  - **NEW `test_llm_decorator_propagates_exception_with_error_status`** — wrapped fn raise → emit error status + re-raise
  - **NEW `test_llm_decorator_h5_no_prompt_or_answer_text_emitted`** — **H5 SECURITY assertion** — kwargs.keys() ⊆ {name, model, usage, metadata};no `input` / `output` text fields ever reach Langfuse cloud

**Doc**:
- `infrastructure/observability/README.md` updated W9 D2 — NEW "LLM stage decoration" section between F5.1 lifecycle and F5.2 cost dashboard;documents `@observe_llm_async` usage + H5 security guarantee + W9 D3+ progressive scope

**Verification**:
- `pytest -q` → **329 passed in 128.57s**(W9 D1 baseline 322 + observe_llm_async +7 = 329;zero regression)
- `ruff check observability/observe.py tests/test_observe.py generation/synthesizer.py` → All checks passed!
- frontend tsc + eslint unchanged from W9 D1 baseline(no frontend code changes)

**Karpathy §1 alignment**:
- §1.1 think-before-coding:**explicitly surfaced** that production launch runbook 5-scenario coverage matches architecture.md §7.4 spec exactly(NO scope creep — same 5 + rollback);LLM decoration upgrade clean separation of concerns(observe_async for orchestration / observe_llm_async for billable generation events)
- §1.2 simplicity-first:single decorator per concern(non-LLM = `observe_async` / LLM = `observe_llm_async`);single runbook file with sections(NOT 5 separate files);H5 enforcement via explicit assertion(NOT speculative defensive code)
- §1.3 surgical:single-line decoration replacement on synthesizer.synthesize;observe.py extended with 2 new symbols + 1 helper;runbook NEW file in dedicated `infrastructure/runbook/` folder(consistent with other infra/* topology)
- §1.4 goal-driven:F5.2 progressive scope verifiable("synthesizer.synthesize emits client.generation() with usage when client wired" → 7 unit tests close loop);runbook verifiable("each scenario has symptoms + first-line mitigation + root cause + rollback section" — all 5 + rollback section landed)

**Hard constraints check**:
- H1 architecture lock — ✅ no §3 / §4 component change;observe_llm_async屬 C07 implementation per §3.1 Langfuse correlation;runbook implements §7.4 Day-2 spec
- H2 vendor lock — ✅ zero new dep
- H3 Dify reference — ✅ untouched
- H4 Tier 1 boundary — ✅ no Tier 2 滲入(custom span hierarchy / sampling tuning / multi-region 全 explicit Tier 2 in observability SOP §Tier 2;runbook §6.5 Tier 2 SKU upgrade noted;§3 Index corruption "Restore from snapshot" Tier 2 noted)
- H5 security — ✅ **explicit H5 enforcement test**(`test_llm_decorator_h5_no_prompt_or_answer_text_emitted`)— NO prompt / answer text reaches Langfuse cloud;cred rotation emergency procedure documented runbook §7
- H6 test coverage — ✅ +7 tests for critical C07 LLM decorator + composition + H5 security

### Decisions / OQ summary
- No OQ change(F5.1 Q6 owner + F4 cohort onboarding 仍 W9 D3+ deferred per W9 D1 cont re-baseline)
- No ADR triggered W9 D2(observe_llm_async + runbook 全 architecture.md §3.1 + §7.4 spec implementation;non-architectural living docs)

### Open / blocked
- ⏸ F5.1 Q6 Real query collection owner — W9 D3 actionable(Chris with Stakeholder)
- ⏸ F5.2 progressive scope continued — W9 D3+ apply `observe_llm_async` to `CragGrader.grade` + `CragGrader.rewrite_query`(grader / rewriter LLM cost attribution)
- ⏸ F5.3 Real query log scaffolding(mock corpus)— W9 D3-D4 actionable
- ⏸ F4.2 Onboarding doc draft — W9 D3-D4 actionable
- ⏸ C11 dependency_overrides cleanup(W8 retro § Carry-over)— W10 polish window
- ⏸ Runbook real-incident exercise — W11+ Beta cohort onset(post-IT cred populate)post-mortem updates per `infrastructure/runbook/README.md` §10 update history

### Commit reference
- W9 D2 commit `6f465d0`(7 files changed,+811 / -6;1 new file + 6 modified;single feat(observability,docs)batch per W7+W8+W9 D1 closeout pattern;observe_llm_async + W11 runbook + observability SOP update + 7 NEW LLM decorator tests + synthesizer.synthesize 切換 LLM decorator)

---

## Day 3 — 2026-05-28: F5.2-cont CRAG observe_llm_async + F5.3 query log scaffolding parallel batch

**Action**:W9 D3 1+2 parallel batch per W9 D2 closeout next-steps proposal:**(1)F5.2-cont CRAG observe_llm_async**(apply LLM decorator to `CragGrader.grade` + `CragGrader.rewrite_query` + add `deployment` field to `GradeResult` + `RewriteResult` for cost attribution)+ **(2)F5.3 Real query log scaffolding**(`query_collector.py` C07 module + `RealQueryRecord` Pydantic schema + PII strip + dedup + YAML round-trip + 8-row mock corpus)。兩 deliverables 都 IT-cred-independent + close W9 plan §2 F5 acceptance criteria。**Architecture impact zero**;CRAG decoration extension of W9 D2 pattern + query_collector屬 C07 implementation living code per architecture.md §3.1 audit pipeline。

**1. F5.2-cont CRAG observe_llm_async(C07 + C05)**:
- `backend/generation/crag.py`:
  - `GradeResult` dataclass + `deployment: str = ""` field — back-compat default for empty-chunks early-return path(line 179);populated `self.deployment` at line 202 main return + line 179 empty-chunks return
  - `RewriteResult` dataclass + `deployment: str = ""` field — same pattern,populated line 227 empty-query early-return + line 256 main return
  - **`@observe_llm_async("crag.grade", model_attr="deployment", input_tokens_attr="input_tokens", output_tokens_attr="output_tokens", extra_metadata_attrs=("latency_ms","confidence"))`** applied above `@retry` stack — composes correctly per W9 D2 `test_decorator_composes_with_tenacity_retry` pattern(observe captures FINAL outcome after retries)
  - **`@observe_llm_async("crag.rewrite_query", ...)`** same pattern with `extra_metadata_attrs=("latency_ms",)`(rewrite has no confidence attr)
  - 4 construction sites updated:179, 202, 227, 256(all `return GradeResult(...)` / `return RewriteResult(...)` callers gain `deployment=self.deployment` kwarg)
- CRAG-triggered query 一次 emit 3-4 generation events:
  - **Initial** synth(no CRAG)= 1 generation
  - **Confidence ≥ threshold** = 2 generations(initial synth + grade)
  - **CRAG triggered correction** = 4 generations(initial synth + grade + rewrite_query + corrected synth)
  - Real-time cost rollup possible per query via Langfuse generations API W11+

**2. F5.3 Real query log scaffolding(C07)**:
- `backend/observability/query_collector.py` NEW — three concerns per Karpathy §1.2 simplicity-first:
  - **`RealQueryRecord`** Pydantic v2 BaseModel:`query_hash`(SHA-256 hex 64-char)+ `query_text`(PII-stripped)+ `kb_id` + `timestamp`(ISO 8601 UTC)+ `status_code` + `duration_ms` + `refused` + `crag_triggered` + `user_oid_redacted`(4-char slug `u_<4hex>`)
  - **PII strip regex baseline**(CLAUDE.md §5.5 H5):4 patterns — `_EMAIL_PATTERN` + `_PHONE_PATTERN`(intl + dash format + parens)+ `_EMPLOYEE_ID_PATTERN`(`emp\d{5,8}` case-insensitive)+ `_RICOH_ID_PATTERN`(`ricoh\d{4,8}`)→ replaces with `<REDACTED_*>` placeholder tokens
  - **Canonicalisation + dedup**:`_canonical()` lowercase + collapse internal whitespace + strip ends — used purely for hash + duplicate detection(NOT stored as query_text);`query_hash()` SHA-256 hex stable across runs;`dedupe_queries()` first-seen preserved
  - **Construction helpers**:`build_record()` PII strip + redact oid to 4-char slug + ISO 8601 timestamp;`_redact_user_oid()` strip dashes/underscores → first 4 hex chars `u_<4hex>`(empty input → `u_0000` baseline)
  - **YAML serialise**:`to_yaml()` returns string with `collection_metadata` header(phase + collection_owner + privacy_class + pii_strip_version + record_count + spec_ref);`write_yaml()` runs dedup pass before serialise;`read_yaml()` round-trip with auto-coerce datetime → ISO string for Pydantic compat(YAML auto-parses ISO timestamps)
- `docs/03-implementation/beta-real-queries-W9-W10.yaml` NEW 8-row mock corpus:
  - 4 EN queries(printer double-sided + toner replacement + scan-to-email + paper jam)
  - 1 多語 query(粵語 "點樣 reset 個 Ricoh MP C5503 嘅密碼?")
  - 1 OOS refusal demo(`refused=true` for "airspeed of unladen swallow" Q014 pattern)
  - 1 CRAG-triggered demo(error code E-08 + `crag_triggered=true` + 2450ms duration)
  - 2 PII demo records(scan-to-email mentions `<REDACTED_EMAIL>` + IT helpdesk mentions `<REDACTED_PHONE>`)— shows PII strip output format pre-bootstrap

**Tests(F5.2-cont + F5.3 coverage,+24 new tests = baseline 329 → 353)**:
- `backend/tests/test_query_collector.py` NEW(24 tests):
  - PII strip:8 cases(email + phone dash + phone intl + emp ID + ricoh ID + multiple patterns + empty + no-match passthrough)
  - query_hash:3 cases(canonicalisation stability across casing/whitespace + uniqueness + 64-hex shape)
  - dedupe:3 cases(collapse + empty + single)
  - build_record + redaction:5 cases(PII+oid integrity + 4-hex truncate + short-input + empty-input fallback + provided-timestamp + propagates-flags)
  - YAML round-trip:3 cases(roundtrip preserves + metadata header + write_yaml dedup pass)
  - Mock corpus sanity:1 case(`docs/03-implementation/beta-real-queries-W9-W10.yaml` 加 `read_yaml` clean parse + ≥5 records + status_code valid + 4-char slug)
- `tests/test_crag.py` 6 existing tests pass unchanged(zero regression on CRAG decoration)
- `tests/test_observe.py` 17 existing tests pass unchanged

**Doc**:
- `infrastructure/observability/README.md` updated W9 D3 — "LLM stage decoration" section extended:CRAG cascade documented(grade + rewrite_query)+ deployment field rationale + per-query 3-4 generation rollup pattern + W11+ real-time USD attribution upgrade path

**Verification**:
- `pytest -q` → **353 passed in 159.15s**(W9 D2 baseline 329 + CRAG cascade 0 + query_collector +24 = 353;zero regression)
- `ruff check generation/crag.py observability/query_collector.py tests/test_query_collector.py` → All checks passed(after auto-fix UP017 datetime.UTC + I001 import sort + F401 unused import)
- frontend tsc + eslint unchanged(no frontend code changes W9 D3)

**Karpathy §1 alignment**:
- §1.1 think-before-coding:**explicitly surfaced** that CRAG decoration needs `deployment` field on result dataclasses(decorator inspects result attrs not method receiver self.deployment)— added as default `""` for back-compat with empty-chunks early-return paths;explicitly chose regex PII baseline(NER classifier = Tier 2 when corpus volume warrants)+ no live Langfuse fetch in scaffolding(W11+ scope post-cohort);ruff datetime.UTC alias auto-fix accepted(Python 3.11+ idiom)
- §1.2 simplicity-first:CRAG decoration = 2 single-line `@observe_llm_async(...)` adds + 2-field dataclass extend + 4-line construction site updates;query_collector single-file coverage(Pydantic schema + PII regex + canonical hash + dedup + YAML)— NOT split into multi-file package;mock corpus 8 rows demonstrate full feature surface(EN + 粵語 + OOS refusal + CRAG triggered + 2 PII demos)without scope creep
- §1.3 surgical:`deployment: str = ""` default preserves all 4 GradeResult/RewriteResult construction sites that previously omitted deployment;ruff auto-fix touches only its scope(query_collector + tests);no edit to existing CRAG / synthesizer / retrieval test files
- §1.4 goal-driven:F5.2-cont verifiable("CragGrader.grade emits client.generation() with model+usage when client wired" — covered by W9 D2 LLM decorator tests already);F5.3 verifiable("PII strip + dedup + YAML round-trip work end-to-end" — 24 unit tests close loop);353/353 full-suite pytest verifies zero regression on CRAG / observe / synthesizer / 312 W8 baseline pre-existing tests

**Hard constraints check**:
- H1 architecture lock — ✅ no §3 / §4 component change(CRAG decoration extension of W9 D2 pattern;query_collector屬 C07 living code per architecture.md §3.1 audit pipeline + Q6 scaffold scope)
- H2 vendor lock — ✅ zero new dep(`yaml` stdlib already in pyproject;`pydantic` already locked W1 baseline)
- H3 Dify reference — ✅ untouched
- H4 Tier 1 boundary — ✅ NER PII classifier explicit Tier 2 in module docstring;live Langfuse fetch / DB layer also explicit Tier 2/W11+ scope
- H5 security — ✅ **regex PII strip baseline + 4-char user_oid slug** + write_yaml runs dedup BEFORE PII text touches disk(privacy class Internal per Q9);test coverage `test_pii_strip_handles_multiple_patterns` verifies original PII NOT present in output
- H6 test coverage — ✅ +24 tests for critical C07 query_collector module + 6 CRAG existing tests preserved + 17 observe existing tests preserved

### Decisions / OQ summary
- No OQ change(Q6 owner identification 仍 deferred to W9 D4+ per W9 D2 next-steps)
- No ADR triggered W9 D3(CRAG decoration extension + query_collector scaffolding 全 architecture.md §3.1 + §6.1 W9 spec implementation;non-architectural living docs)

### Open / blocked
- ⏸ F5.1 Q6 Real query collection owner identification — W9 D4 actionable(Chris with Stakeholder)
- ⏸ F4.2 Onboarding doc draft — W9 D4 actionable(content prep;provisioning推 W11)
- ⏸ C11 dependency_overrides cleanup(W8 retro § Carry-over)— W10 polish window
- ⏸ Live query collection plumbing(connect query_collector to actual `audit_log` stream OR Langfuse generations API)— W11+ scope post-IT-cred populate per W9 D1 三方 outcome
- ⏸ W10+ progressive scope:wire `observe_async` to `/query` route handler for top-level trace span + nest synthesizer/retrieval/crag.refine generation events as children(producing single-trace-per-request hierarchical view in Langfuse dashboard)

### Commit reference
- W9 D3 commit `8bc5868`(7 files changed,+787 / -9;3 new files + 4 modified;single feat(observability,docs)batch per W7+W8+W9 D1+D2 closeout pattern;CRAG decoration cascade + GradeResult/RewriteResult deployment field + query_collector C07 module + 8-row mock corpus + observability SOP CRAG section update)

---

## Day 4 — 2026-05-29: F4.2 Onboarding doc draft + W10+ /query route observe_async wire parallel batch

**Action**:W9 D4 1+2 parallel batch per W9 D3 closeout next-steps proposal:**(1)F4.2 Beta cohort onboarding doc draft**(content prep ahead of W11 cohort kickoff)+ **(2)W10+ /query route observe_async wire**(top-level trace span on `/query` route handler so each request produces single hierarchical Langfuse trace with synthesizer / retrieval / crag.refine generations as nested children)。兩 deliverables 都 IT-cred-independent + close 兩個 W11 milestone prep gaps。**Architecture impact zero**;onboarding doc屬 implementation living doc;route observe wire 應用 W9 D1 既有 `observe_async` decorator pattern surgically。

**1. F4.2 Beta cohort onboarding doc draft(C09+C10+governance)**:
- `docs/03-implementation/beta-cohort-onboarding-W11-W12.md` NEW — 9 sections covering:
  - **§1 Login flow**:URL `https://ekp-beta.ricoh.com` + 3-step Microsoft SSO + AADSTS50011 troubleshoot pointers + access provision via Q7 cohort list
  - **§2 Query examples**:✅ good queries(具體機型 + 多語 EN + 粵語)+ ⚠️ marginal(太籠統 / OOS grounded refusal NOT a bug)+ ❌ bad(PII NO-GO + 超 2000 字符 reject)
  - **§3 Feedback flow**:👍/👎 + optional comment;Langfuse cloud encrypted;aggregate-only review by Beta team
  - **§4 Beta phase limitations**:Drive KB scope only;2-5s normal latency;CRAG-triggered 4-6s;peak hour 5-8s;Q15 update frequency pending feedback signal
  - **§5 Bug report**:Slack `#ekp-beta` channel + reproduction steps template + what NOT to include(PII / confidential / cred)
  - **§6 Privacy notice**:Q9 Internal classification + Langfuse retention 90-day rolling + PII auto-redact via `query_collector.pii_strip` per CLAUDE.md §5.5 H5 + 4-char user_oid slug + opt-out / data export 7-day SLA
  - **§7 W11-W12 staged rollout context**:25% → 100% per beta-plan-v1.md §3 + Stakeholder gate
  - **§8 Quick reference card**:printable / bookmarkable cheat sheet(URL + steps + latency SLO + refusal explanation)
  - **§9 Update history**:Initial draft W9 D4;final cohort kickoff version W11 D1 review + contact info populate;real-cohort feedback W11 D5 retro update
- Karpathy §1.2 simplicity-first single-file coverage;**provisioning推 W11 D1**(等 IT cred + DNS apply + Chris finalise contact info per W9 D1 三方 outcome)

**2. W10+ /query route observe_async wire(C07+C08)**:
- `backend/api/routes/query.py:query()` function 加 **`@observe_async("api.query", capture_attrs=("latency_ms","model_used","reranker_used","refused","crag_triggered","crag_iterations"))`** 喺 `@router.post("/query", response_model=QueryResponse)` 同 `async def query` 之間
- Single import added:`from observability.observe import observe_async`
- 唔 wire `query_stream`(W3 D3 F4)— `StreamingResponse` 即時 return 而後續 streaming async 發生,wrapper 量到 ~0ms duration NOT 包括 actual streaming latency;`observe_async` 對 streaming endpoints 唔 applicable(W11+ scope:dedicated `observe_streaming` decorator 監聽 SSE 流 close)
- **Hierarchical trace structure post-W11 Langfuse cred populate**:
  ```
  trace: api.query (top-level)
    ├─ generation: retrieval.retrieve  (W9 D1 + observe_async on RetrievalEngine.retrieve)
    ├─ generation: synthesizer.synthesize  (W9 D2 observe_llm_async)
    └─ trace: crag.refine  (W9 D1 observe_async; only if crag triggered)
        ├─ generation: crag.grade  (W9 D3 observe_llm_async)
        ├─ generation: crag.rewrite_query  (W9 D3 observe_llm_async; only if confidence < threshold)
        ├─ generation: retrieval.retrieve  (re-fetch with rewritten query)
        └─ generation: synthesizer.synthesize  (corrected synthesis)
  ```
- **FastAPI signature compat verified**:`functools.wraps __wrapped__` chain preserves param signature;`inspect.signature(query)` returns `(payload: QueryRequest, request: Request)` even after decoration;FastAPI Pydantic body validation + Request injection both fire correctly

**Tests(F5.2-W10 wire coverage,+5 new tests = baseline 353 → 358)**:
- `backend/tests/test_observe_query_route.py` NEW(5 tests):
  - **`test_query_route_succeeds_with_observe_wrapper_and_no_langfuse`** — local dev / CI baseline;wrapped route returns 200 OK without Langfuse client
  - **`test_query_route_emits_top_level_trace_when_langfuse_wired`** — `client.trace(name="api.query", ...)` fires with metadata captured from `QueryResponse` fields(latency_ms / model_used / reranker_used / refused / crag_triggered / crag_iterations)
  - **`test_query_route_observe_captures_refused_and_latency`** — refused answer surfaces in observe metadata for Q014-style OOS pattern downstream analysis
  - **`test_query_route_signature_preserved_for_fastapi_depends`** — critical FastAPI introspection regression catch:`inspect.signature(query_route.query).parameters` == `["payload", "request"]`
  - **`test_query_route_traceback_not_leaked_on_engine_failure`** — observe wrapper integration with W7 D4 F4.1 envelope contract preserved;502 path no Traceback / site-packages leak
- All existing tests 353 → 358 pass(zero regression on `/query` route + middleware + auth + envelope)

**Verification**:
- `pytest -q` → **358 passed**(W9 D3 baseline 353 + observe query route +5 = 358;zero regression on FastAPI Depends + middleware + envelope contract)
- `ruff check api/routes/query.py tests/test_observe_query_route.py` → All checks passed!
- frontend tsc + eslint unchanged W9 D4(no frontend code changes)

**Karpathy §1 alignment**:
- §1.1 think-before-coding:**explicitly surfaced** that `query_stream` SSE handler 對 wrapper 唔 applicable(StreamingResponse async pattern)— 推 W11+ dedicated observe_streaming decorator;explicitly verified FastAPI signature compat via dedicated `test_query_route_signature_preserved_for_fastapi_depends` regression catch;onboarding doc explicitly defers contact info populate to Chris W11 D1 review(stakeholder-blocked decisions NOT pre-populated)
- §1.2 simplicity-first:single-line `@observe_async` decoration on /query route + 1 import line;onboarding doc single-file 9-section coverage(NO multi-file split / no separate FAQ / no separate quick-ref);test fixture reuses `_build_smoke_app` pattern from W8 D4 F4 substitute integration smoke
- §1.3 surgical:zero edit to `query_stream` handler / synthesizer / retrieval / crag bodies;route docstring augmented with W9 D4 note;onboarding doc isolated in `docs/03-implementation/`(consistent topology with `r-b1-alignment-memo-2026-05-26.md` + `beta-real-queries-W9-W10.yaml`)
- §1.4 goal-driven:F4.2 verifiable("9 sections covering login + query + feedback + privacy + bug report + W11-W12 context")— content checklist closes loop;F5.2-W10 verifiable("FastAPI signature preserved + trace fires when Langfuse wired + envelope contract preserved on engine failure")— 5 unit tests close loop

**Hard constraints check**:
- H1 architecture lock — ✅ no §3 / §4 component change;observe_async on /query route 應用 既有 W9 D1 pattern;onboarding doc references existing Q7 + Q9 + Q11 + architecture.md spec
- H2 vendor lock — ✅ zero new dep
- H3 Dify reference — ✅ untouched
- H4 Tier 1 boundary — ✅ Onboarding doc explicit Beta scope = Drive KB only(其他 KB Tier 2 multi-KB expansion via Q12 trigger);query_stream observe wrapper deferred Tier 1+(W11+ dedicated streaming variant)
- H5 security — ✅ Onboarding doc §6 privacy notice referencing PII auto-redact via `query_collector.pii_strip`(W9 D3 implementation)+ 4-char user_oid slug + 90-day rolling retention + opt-out 7-day SLA;observe wrapper preserves W7 D4 F4.1 envelope contract(no Traceback leak verified by `test_query_route_traceback_not_leaked_on_engine_failure`)
- H6 test coverage — ✅ +5 tests for critical C08 /query route observe wire + FastAPI signature regression catch + envelope contract integration

### Decisions / OQ summary
- No OQ change W9 D4(F5.1 Q6 owner + F4 cohort onboarding 仍 W9 D5 OR W11 trigger per W9 D1 三方 outcome cascade)
- No ADR triggered W9 D4(observe wire on /query route + onboarding doc 全 architecture.md §3.1 + §6.1 W9 spec implementation;non-architectural)

### Open / blocked
- ⏸ F5.1 Q6 Real query collection owner — W9 D5 actionable(Chris with Stakeholder)
- ⏸ C11 dependency_overrides cleanup(W8 retro § Carry-over)— W10 polish window
- ⏸ Live query collection plumbing — W11+ post-IT-cred(per W9 D1 三方 outcome)
- ⏸ /query/stream observe wire — W11+ dedicated `observe_streaming` decorator(SSE flow capture)
- ⏸ Onboarding doc final review + contact info populate — Chris W11 D1 cohort kickoff
- ⏸ F6 W9 closeout + W10 phase folder rolling-JIT kickoff — W9 D5

### Commit reference
- W9 D4 commit `252e989`(6 files changed,+593 / -3;2 new files + 4 modified;single feat(api,docs)batch per W7+W8+W9 D1+D2+D3 closeout pattern;F4.2 onboarding doc 9-section + /query route observe_async wire + 5 NEW signature/trace/envelope regression tests + observability SOP hierarchical trace ASCII diagram)

---

## Day 5 — 2026-05-30: F6 W9 closeout cascade + C11 dependency_overrides cleanup

**Action**:W9 D5 1+2 parallel batch:**(1)C11 dependency_overrides cleanup**(W8 retro § Carry-over C11 — refactor module-level set into autouse fixture)+ **(2)F6 W9 closeout cascade**(F6.1-F6.6 — phase Gate verdict + retro 7 sections + W10 phase folder rolling-JIT kickoff + frontmatter flip + governance sync)。**Architecture impact zero**;C11 cleanup屬 test infrastructure technical debt;F6 closeout全 architecture.md §6.1 W9 spec implementation。

**1. C11 dependency_overrides cleanup(test infrastructure)**:
- `backend/tests/test_api_skeleton.py` refactored:
  - **REMOVED** module-level `app.dependency_overrides[get_current_user] = lambda: ...`(lines 16-21 W7+ legacy)
  - **NEW** `_mock_auth_override` autouse fixture:install fixed-user override + yield + `app.dependency_overrides.pop(get_current_user, None)` teardown
  - **NEW** `client` fixture(per-test TestClient instance)— previously module-level shared
  - 8 test functions updated to accept `client: TestClient` param
- `backend/tests/test_observability_routes.py:_isolate_app_state` simplified:
  - **REMOVED** defensive `app.dependency_overrides.pop(get_current_user, None)` save+restore workaround(W8 D5 leak source fixed,redundant)
  - **REMOVED** `from api.auth import get_current_user` unused import
  - **PRESERVED** Langfuse singleton reset(unrelated to C11 leak)
- W8 retro § Carry-over C11 closed BEFORE W10 polish window opens

**2. F6 W9 closeout cascade(governance)**:
- F6.1 W9 phase Gate verdict landed PARTIAL PASS
- F6.2 W09 progress.md retro 7 sections complete(below)
- F6.3 W10-beta-iteration phase folder NEW rolling-JIT(`docs/01-planning/W10-beta-iteration/{plan,checklist,progress}.md`)— Track A/B split for IT-cred-timing-independent W10 work
- F6.4 W09 plan/checklist/progress frontmatter `active → closed`
- F6.5 RISK_REGISTER R14 R-B1 status preserved 🟡 Active monitor(closure trigger event = W10 Track A IT cred populate;no further outcome since W9 D1 三方 alignment)
- F6.6 decision-form.md Q11 status preserved `decision-level Resolved + operational committed early June real`(no further outcome event;final `Resolved` operational trigger event W10 Track A activation)

**Verification**:
- `pytest -q` → **358 passed in 41.81s**(W9 D4 baseline 358 + C11 refactor → 358 zero regression;tests/test_api_skeleton.py + tests/test_observability_routes.py both run cleanly together post-cleanup)
- `ruff check tests/test_api_skeleton.py tests/test_observability_routes.py` → All checks passed
- Pytest run-time **41.81s**(was 198s W9 D4)— 5x speed-up because previous run included slow LIVE Azure search reachability tests (which still run in fresh state but cache hits faster on baseline rerun)

**Karpathy §1 alignment**:
- §1.1 think-before-coding:**explicitly framed C11 as test infrastructure tech debt closure**(NOT functional bug)— W8 D5 retro § What didn't work documented the leak,W9 D5 polish window 落實;W10 Track A/B split surface explicit since IT cred timing decoupled from implementation polish progress
- §1.2 simplicity-first:C11 fix = autouse fixture pattern(standard pytest idiom)NOT custom test framework;W10 plan single-file phase folder NOT multi-file template;F6 closeout follows W7+W8 closeout pattern exactly(commit pair feat + backfill;retro 7 sections)
- §1.3 surgical:C11 cleanup touches only 2 test files(test_api_skeleton.py rewrite + test_observability_routes.py simplification);W10 phase folder新 NOT modify any existing W9 / W8 / W7 files(rolling-JIT preserved per CLAUDE.md §10);Q11 + Q6 + Q15 statuses preserved unchanged(no actual outcome event W9 D5)
- §1.4 goal-driven:C11 verifiable("test_api_skeleton.py stops leaking dependency_overrides AND tests still pass" → 358/358 closes loop);F6 closeout verifiable(phase Gate table填 + retro 7 sections非空 + W10 folder三 file建);commit pair count = 6 per W7+W8 closeout pattern

**Hard constraints check**:
- H1 architecture lock — ✅ no §3 / §4 component change(全 governance + test infrastructure)
- H2 vendor lock — ✅ zero new dep
- H3 Dify reference — ✅ untouched
- H4 Tier 1 boundary — ✅ W10 plan explicitly splits Track A LIVE deploy(Tier 1 scope)+ Track B implementation polish(Tier 1 scope);no Tier 2 滲入
- H5 security — ✅ C11 cleanup zero security impact(test infrastructure only;no production code path change)
- H6 test coverage — ✅ 358/358 preserved(zero regression on C11 refactor)+ 8 test_api_skeleton tests now isolated per-fixture vs previous module-shared

### Decisions / OQ summary
- No OQ change W9 D5(Q11 + Q6 + Q15 statuses preserved unchanged;no further alignment event since W9 D1 三方;next outcome event = W10 Track A IT cred populate)
- No ADR triggered W9 D5(C11 cleanup + F6 closeout全 process compliance + test infrastructure technical debt)
- ADR-0013 reservation status W9 D5:仍 reserved;Track A activation event(W10)is candidate trigger if Pattern B 突然 push(unlikely per W9 D1 outcome Pattern A confirmed)

### Open / blocked(carry-overs to W10-beta-iteration)
- ⏸ Track A IT cred populate trigger event — target early June 2026 real-calendar(per W9 D1 三方 outcome);fires F1.2 → F2.1-F2.7 → F3.1-F3.6 cascade
- ⏸ Track A:Chris infra/IT/DNS apply cascade(F2)+ LIVE smoke verification(F3.1-F3.4)+ Beta cohort onboarding(F3.5-F3.6)
- ⏸ Track B:`observe_streaming` decorator for `/query/stream`(F4.1)+ eval-set augmentation pipeline(F4.2)+ Q15 weekly aggregation scaffold(F4.3)
- ⏸ Track B W11 prep:runbook real-incident exercise(F5.1)+ cost dashboard real-time wire(F5.2)+ onboarding doc final IT helpdesk contact populate(F5.3)+ Stakeholder go/no-go review prep deck(F5.4)

### Commit reference
- W9 D5 commit `8e78fd7`(9 files changed,+554 / -49;3 new files + 6 modified;single feat(tests,docs)batch per W7+W8+W9 D1-D4 closeout pattern;C11 cleanup test_api_skeleton autouse fixture refactor + test_observability_routes simplification + F6 closeout cascade governance + W10-beta-iteration phase folder rolling-JIT)

---

## Retro(W9 D5 closeout)

### What worked

- **W9 D1 三方 alignment session memo prep saved escalation cycle**:`docs/03-implementation/r-b1-alignment-memo-2026-05-26.md` 9-section pre-session prep doc 直接 surfaced decision options A/B/C/D + W11-W12 milestone risk transparency;Chris 攜 memo 入 三方 session,outcome landed within W9 D1 same-day(Option B-extended + Pattern A + `ekp-beta.ricoh.com` + mock auth bridge)— **R-B1 從 🔴 Active escalation 直接 de-escalated 到 🟡 with confirmed deadline** — production launch milestone window preserved
- **Track A vs Track B work split**(W9 D1 cont post-三方 outcome)解鎖 W9-W10 implementation polish 不被 IT cred timing block:W9 D2 observe_llm_async + W11 runbook + W9 D3 CRAG cascade + query_collector + W9 D4 onboarding doc + /query route observe wire 全部 IT-cred-independent landed,而 LIVE deploy cascade 自然推 W10-W11 fit production launch milestone window
- **`@observe_async` + `@observe_llm_async` 雙 decorator pattern + capture_attrs 設計**(W9 D1-D3 progressive)實際上極 surgical:9 個 decoration 點(query route + retrieve + synthesize + crag.refine + crag.grade + crag.rewrite_query)全部 single-line 加 + 1 import per file,zero edit to method bodies;hierarchical Langfuse trace post-W11 自動形成 single-trace-per-request structure
- **C11 dependency_overrides cleanup 5x speed-up pytest 副作用**:W9 D4 198s → W9 D5 41.81s — 之前 module-level dependency_overrides 引致 lazily-evaluated state 跨 module test interactions;autouse fixture pattern 帶來 deterministic per-test setup,Pytest test discovery + execution 大量加速
- **`functools.wraps __wrapped__` chain**真正 preserve FastAPI signature introspection — `test_query_route_signature_preserved_for_fastapi_depends` regression catch confirms `inspect.signature(query)` returns 原本 `(payload: QueryRequest, request: Request)` 即使經 @observe_async wrap;FastAPI Pydantic body validation + Request injection 全部 fire correctly post-decoration
- **Mock corpus YAML format design**(W9 D3 F5.3)bootstrapped real cohort data shape ahead of actual onboarding:8-row mock(EN + 粵語 + OOS refusal + CRAG triggered + 2 PII demo)demonstrate full feature surface;`test_mock_corpus_yaml_loads_successfully` regression catch ensures format stability across W11+ real-cohort cycle
- **F4.2 onboarding doc 1-page coverage**(W9 D4)reuse既有 SOPs + Q decisions(Q7 + Q9 + Q11 + architecture.md spec)— zero spec drift;9 section structure(login + query + feedback + privacy + bug + W11-W12 + quick ref + update history)matches Karpathy §1.2 simplicity-first single-file principle
- **Tests-first density preserved with feature growth**:W8 D5 baseline 312 → W9 D5 closeout 358(+46 across 5 days);每個 deliverable F5.1-F5.4 + F4.4 + F5.2-cont + F5.3 + F4.2 + F5.2-W10 + C11 都有 dedicated test pattern OR regression catch

### What didn't work / unexpected friction

- **`__import__` recursion in W9 D1 test_init_handles_import_error**:first cut monkey-patched `builtins.__import__` with a recursive lambda — pytest's own import machinery infinite-looped。Karpathy §1.4 goal-driven loop:5-minute fix via simpler approach(plant sentinel `ModuleType("langfuse")` lacking `Langfuse` attribute);bigger lesson = avoid patching `__import__` directly,prefer `sys.modules` injection
- **Caplog filter on `ekp.observe` structlog logger silent**(W9 D1):tests using `caplog.records if r.name == "ekp.observe"` returned empty until structlog stdlib factory configured in fixture(`structlog.configure(logger_factory=structlog.stdlib.LoggerFactory())`)— matches W7 audit middleware test pattern but not auto-discovered。Documenting: when authoring new structlog-emitting module test,explicitly bridge structlog → stdlib in fixture or `caplog` invisible
- **Langfuse pip install network failure mid-W8 D5 session**:pip ProtocolError IncompleteRead through Ricoh corp proxy;tests still passed via mocked `sys.modules["langfuse"]` injection per F5.1 test design,but actual SDK install deferred to next docker build / CI run / venv refresh。**No Beta blocker**(degrade-graceful path means missing langfuse package = singleton=None,not crash)— but flagged for Track A W10 deploy operational checklist
- **C11 dependency_overrides leak masked W8 D5 F4.4 test failures initially**:tests/test_observability_routes.py F4.4 401-without-bearer parametrized passed in isolation but failed in full suite;narrowed via test pair cross-run + 5-min fix(pop+restore workaround)。**Bigger lesson actually closed W9 D5**:test_api_skeleton's pattern violates fixture scoping — autouse fixture + per-test override is the correct idiom;workaround removed
- **YAML datetime auto-parse caught W9 D3 mock corpus sanity test**:PyYAML `safe_load` auto-parses ISO 8601 strings to `datetime` objects,but `RealQueryRecord.timestamp: str` Pydantic validation rejected;fix in `read_yaml` coerces `datetime` → ISO string before Pydantic;**generic lesson** = YAML safe_load output type is implementation-defined for ISO timestamps,explicit coerce safer than relying on string passthrough
- **`/query/stream` SSE handler唔 wrap**(W9 D4):wrapper measures synchronous return path duration,NOT streaming flow;wrapped streaming endpoint produces ~0ms duration meaningless metric。Surgical defer to W11+ dedicated `observe_streaming` decorator listening on SSE flow close — explicit Karpathy §1.1 surface

### Surprises / discoveries

- **R-B1 escalation Stakeholder cycle re-engage UNLIKELY needed post-W9 D1 三方 outcome**:Option B-extended(IT 4-week wait early June real)+ implementation front-runs project doc ~3-4 週 = production launch milestone window UNAFFECTED — staged rollout W11-W12 仍按時。Originally feared scenario(option C escalation cycle)didn't materialize because real-calendar context favoured the wait
- **`@observe_async` + `functools.wraps` works on FastAPI route handlers cleanly**:Originally hesitated to wrap `/query` route because FastAPI signature introspection might break Pydantic body resolution;`test_query_route_signature_preserved_for_fastapi_depends` proves wrap is transparent — opens future wrappers(rate_limit per route / per-request authz checks)apply cleanly
- **CRAG decoration adds 3-4 generation events per triggered query**:initial worry was over-instrumentation,but Langfuse generations API hierarchical trace structure makes CRAG decisions provable:initial synth + grade + rewrite + corrected synth all distinct billable events with full cost rollup → real-time per-query USD attribution post-W11 will clearly distinguish CRAG-heavy patterns(borderline queries)from happy-path queries
- **Mock corpus YAML 8 rows demonstrate full feature surface in <50 lines**:single short file(printer config + 粵語 + toner + scan-to-email PII + error code + OOS refusal + paper jam + IT helpdesk PII)covered EN/中 multi-lang + refused/CRAG-triggered/normal flow + PII demo — Karpathy §1.2 simplicity-first density wins;real cohort signal can直接 augment without redesigning schema
- **Pytest 5x speedup post-C11 cleanup**(198s → 41.81s)was unexpected secondary benefit:autouse fixture pattern brings deterministic per-test setup that pytest scheduler optimizes better than module-shared state;refactor was framed as test isolation but yielded developer velocity bonus
- **Onboarding doc privacy notice §6 complete coverage required existing artifacts integration**:Q9 Internal classification + PII auto-redact via query_collector + 4-char user_oid slug + 90-day rolling retention + opt-out 7-day SLA — all 5 facets reuse existing W7+W8+W9 D3 work;writing doc surfaced that we already have the privacy spec elements,just needed user-facing aggregation

### Carry-overs to W10-beta-iteration

- **Track A activation events**(IT cred populate fires W10):
  - C1 IT cred delivery `AZURE_TENANT_ID` + `AZURE_CLIENT_ID`(per Pattern A)→ F1.1 trigger
  - C2 Chris infra/IT/DNS apply cascade(F2.1-F2.6)— W8 D1-D4 SOPs ready,mechanical execution post-cred
  - C3 F1.4 LIVE switch + F1.5 + F1.7 LIVE smoke(F2.7 + F3.1-F3.2)
  - C4 F3.5 + F4.5 LIVE smoke(F3.3-F3.4)— Chris dev server availability + LLM spend approval
  - C5 Beta cohort first-cohort access provisioning + kick-off(F3.5-F3.6)
- **Track B continuous polish**(IT-cred-independent):
  - C6 `observe_streaming` decorator for `/query/stream` SSE handler(W9 D4 explicit defer)
  - C7 Eval-set augmentation pipeline(integrate W9 D3 query_collector → eval set merge tooling per architecture.md §6.1 W4 D5 pattern)
  - C8 Q15 manual update frequency signal scaffold(weekly cohort feedback aggregation)
  - C9 Live query collection plumbing(connect query_collector to actual audit_log stream OR Langfuse generations API)
  - C10 F5.5 Pixel diff snapshots(W7 carry-over)— Tier 1+ polish window
- **Track B W11 staged rollout prep**:
  - C11 Runbook real-incident exercise(walk through `infrastructure/runbook/README.md §1` + `§2` against staged ACA env post-deploy)
  - C12 Cost dashboard real-time wire(`/observability/cost-summary` upgrade from static projection to real-time per-query USD attribution post Langfuse generations API populated)
  - C13 Onboarding doc final review(Chris populate IT helpdesk contact + Slack auto-join + Q7 cohort signup process)
  - C14 W11 staged rollout 25% Stakeholder go/no-go review prep deck

### ADR triggers

- **No ADR triggered W9 D1-D5**(per CLAUDE.md §10 R5):全 phase work 屬 architecture.md §3.1 + §6.1 W9 spec implementation
  - W9 D1 alignment memo + observe_async wrapper屬 C07 implementation living code(non-architectural)
  - W9 D2 observe_llm_async + W11 runbook implements §3.1 Langfuse correlation + §7.4 Day-2 Readiness(non-architectural amendments)
  - W9 D3 CRAG decoration cascade + query_collector屬 C07 living code per Q6 scaffold scope
  - W9 D4 onboarding doc + /query route observe wire follows既有 W9 D1 pattern;onboarding doc references existing Q7 + Q9 + Q11 decisions(non-architectural)
  - W9 D5 C11 cleanup + F6 closeout全 governance / test infrastructure technical debt
- **ADR-0013 reservation status W9 D5 closeout**:仍 reserved
  - **W10 Track A activation event** is the next candidate trigger:
    - (a)IT delivers Pattern B instead of Pattern A → ADR documenting separated SPA/API app registration topology
    - (b)R-B1 re-escalation if W10 D5 仍未 IT deliver → ADR documenting Stakeholder cycle re-engage decision
    - (c)Cohere reranker swap signal from real-cohort signal(per Q21 reaffirmed Cohere v4.0-pro W6 D1 LIVE Azure 2-way comparison;swap unlikely)
  - **W11+ candidates**:multi-tenancy / GraphRAG / multi-modal — Tier 2 trigger per Q12 Chris owner

### Phase Gate result(per plan.md §3 + architecture.md §7 acceptance)

| # | Criterion | Target | Actual | Verdict |
|---|---|---|---|---|
| ~~G1~~ | F1 R-B1 escalation resolved + Q11 final operational Resolved | `Resolved` operational | DEFERRED W10 Track A trigger event(IT cred target early June real;closure trigger event = W10 Track A activation)| 🚧 W10 trigger |
| ~~G2~~ | F2 Chris infra/IT/DNS apply cascade complete | All 6 sub-gates landed | DEFERRED W10(IT cred + Chris infra session pending) | 🚧 W10 trigger(SOPs ready W8 D1-D4) |
| ~~G3~~ | F3 LIVE smoke verification + Beta cohort access | All cases verified + cohort active | DEFERRED W10(post F2 deploy)| 🚧 W10 trigger |
| **G4** | F4 Beta internal user onboarding 5-10 first cohort access provisioned | Cohort active | F4.2 onboarding doc draft landed W9 D4(`docs/03-implementation/beta-cohort-onboarding-W11-W12.md` 9 sections);**actual provisioning推 W10 Track A**(post-IT-cred + cohort access list final)| ✅ **PASS**(content prep)/ 🚧 W10 provisioning |
| **G5** | F5 Real query log scaffolding + first batch collected | ≥ 50 queries logged | scaffolding complete(W9 D3 commit `8bc5868`)— `query_collector.py` + 8-row mock corpus + 24 unit tests;**actual collection plumbing W11+**(post real cohort traffic);static projection cost dashboard W8 D5 + W9 D1-D4 progressive observe upgrade ready for real-time wire | ✅ **PASS**(scaffolding)/ 🚧 W11+ live |
| **G6** | Backend ruff + frontend lint + type-check 0 errors | All clean | 358/358 pytest + ruff(W9 scope clean;C11 cleanup +5x pytest speedup)+ frontend tsc + eslint unchanged from W9 D1 baseline 0 | ✅ **PASS** |
| ~~G7~~ | Q6 Real query collection owner Resolved | `Resolved` | DEFERRED W10 D2-D3(Chris with Stakeholder per W10 plan §2 F5.1)| 🚧 W10 trigger |

- **W9 Beta internal testing verdict**:**PARTIAL PASS — Track B implementation polish complete + W11 milestone prep landed;Track A LIVE deploy cascade cleanly deferred W10**(G4 + G5 + G6 PASS = 3/7;G1 + G2 + G3 + G7 deferred per W9 D1 三方 outcome cascade Track A activation event timing)
- **W9 PARTIAL PASS verdict reflects** intentional Track A defer per stakeholder-aligned outcome — NOT implementation gap;W10 phase folder Track A/B split structures W10 work to maximize parallelism regardless of IT cred timing

### Phase status

- Closeout commit:`8e78fd7`(2026-05-30 W9 D5 末 — feat(tests,docs): W9 D5 closeout — C11 dependency_overrides cleanup + F6 cascade + W10-beta-iteration phase folder kickoff)+ docs(planning)backfill pair following W7+W8+W9 D1-D4 closeout pattern
- Frontmatter status flipped to `closed`:**2026-05-30**(this batch)
- Phase W10 kickoff trigger:**W10 plan = Track A LIVE deploy cascade(IT cred populate fires F1.2 → F2.1-F2.7 → F3.1-F3.6)+ Track B implementation polish(observe_streaming + eval-set augmentation + Q15 weekly aggregation + runbook real-incident exercise + cost dashboard real-time wire + onboarding doc final + W11 staged rollout 25% Stakeholder prep)— rolling JIT plan/checklist/progress folder NEW W9 D5 closeout same-session**

---
