---
phase: W34-faithfulness-eval-latency-profile
status: active
last_updated: 2026-05-26
component_scope: C05 Generation Pipeline (latency profile) + C06 Eval Framework (RAGAs eval)
adr_refs:
  - ADR-0034 (W25 F3 D4 query expansion + RAG-Fusion — W34 preserves W29 .env tune)
  - ADR-0037 (W26 F2 parent-doc — Settings preserved per W28 best combo + Q4 default OFF)
  - ADR-0038 (W27 dispatch_mode — preserved "replace" per W28 reaffirmation)
  - W17 F3 RAGAs 4-metric integration (`make_ragas_evaluator` + `orchestrator.build_ragas_samples`)
  - W26 F1 baseline RAGAs report (`baseline-metrics-W26-D1-raw.json`) — faithfulness 0.9851 / correctness 0.7416 historical reference
  - W32 F1 (h') engine-fetch citation expansion (production baseline 100/100/5.4)
  - W33 F1 Rule 7 v2 + Rule 8 prompt layer (production +22% citation breadth + +143% I01 over-citation)
related_carry_overs:
  - W33 retro W34+ HIGHEST candidate — Faithfulness LIVE RAGAs eval(measure if I01 +143% over-citation breaks faithfulness OR benign coverage breadth)
  - W33 retro W34+ #2 candidate — Latency profile breakdown(determine LLM emit cost vs prompt token cost vs engine-fetch IO cost dominant)
  - W32 PC-W32-2 citation enrichment integration pattern documented — W34 F0 R6 catch realized:`build_ragas_samples` callsite missing W32 (h') wiring
  - W33 PC-W33-1 candidate(session-start protocol amend)— W34 inherits + may produce additional pre-flight verify pattern
---

# W34 — Faithfulness LIVE RAGAs Eval + Latency Profile(measurement-only phase)

## §1 Goal + Scope

**Single primary goal**:Measure W33 production state(W32 (h') + Rule 7 v2 + Rule 8)against W26 F1 baseline RAGAs reference + isolate latency cost dominant factor。**Measurement-only phase** — no production behavior shift,no Settings flip,no Rule wording change。W35+ ship decision driven by W34 evidence。

**Key framing differences vs W31-W33**:
- W31-W33 都係 ship 候選 features 然後 measure
- **W34 ship NOTHING** — pure measurement + observability instrumentation
- F1 surgical patch(`build_ragas_samples` engine + kb_id propagation)= **production-parity restoration**(eval path 之前 missing W32 (h') backbone),技術上係 bug-fix-adjacent 而非 NEW feature
- F2 structlog stage timing = pure observability,no production behavior impact

**2-axis measurement scope**:

**Axis 1 — Faithfulness LIVE RAGAs eval**(A.1,~2-3h)
- F1.0 R6 Day 0 catch surgical fix:`backend/eval/orchestrator.py:95` `build_ragas_samples` propagate `engine=engine, kb_id=q_kb_id` kwargs into `synthesizer.synthesize` call。W32 (h') engine-fetch + W33 Rule 7 v2 + Rule 8 prompt 層 兩個 都要 fire 才 production-parity。
- F1.1 Use existing `docs/eval-set-v0-w25-supplement.yaml`(13 queries including Q-W25-I07 + Q-W25-I01 + 11 other corpus-matched queries against `sample-document-with-image-1`)
- F1.2 Invoke POST /eval/run with `{eval_set_id: "eval-set-v0-w25-supplement"}` + capture EvalReport JSON
- F1.3 Aggregate vs W26 F1 baseline(faith 0.9851 / correctness 0.7416)+ failed_queries detail
- F1.4 Decision tree(per plan §3):
  - faith ≥ 0.9651(within W26 F1 -2pp)→ W33 over-citation BENIGN → preserve production
  - faith ∈ [0.9351, 0.9651)(within W26 F1 -5pp to -2pp)→ Rule 8 over-citation FLAG → defer ship decision pending W35+ Rule 8 wording tighten test
  - faith < 0.9351(W26 F1 -5pp 以下)→ W33 BREAKS faithfulness → trigger W32 (h')-only isolation eval to attribute(see F1.5 contingency)
- F1.5 **Contingency only if F1.4 faith < 0.9351**:temporarily revert prompt_builder.py Rule 7 + Rule 8(local-only,no commit)→ re-run /eval/run → measure W32 (h')-only RAGAs → attribute Rule 7 v2 + Rule 8 effect:
  - W32-only faith ≥ 0.9651 → Rule 7 v2 + Rule 8 caused regression → W35+ revert OR tighten
  - W32-only faith < 0.9651 → (h') itself caused regression → re-think W32 ship governance

**Axis 2 — Latency profile structlog stage timing**(A.2,~1-2h)
- F2.1 Add `structlog.bind(stage=X, latency_ms=Y)` stage timing in 4 key locations:
  - `synthesizer.synthesize` overall(query → return SynthesisResult)
  - `synthesizer.synthesize` prompt-build sub-stage(`build_prompt` invocation)
  - `synthesizer.synthesize` LLM chat completion sub-stage(`client.chat.completions.create`)
  - `citation_expansion.expand_citations` overall + per-doc `engine.list_chunks` parallel batch sub-stage
- F2.2 5-run Q-W25-I07 + Q-W25-I01 via `backend/w34-f2-runner.py`(adapted from `w33-f2-runner.py`)+ structlog JSON output capture
- F2.3 Aggregate per-stage avg latency across 10 runs:
  - prompt build cost(W33 SYSTEM_PROMPT 2230 chars vs W32 1730 chars +29%)
  - LLM chat completion cost(prompt processing + response emit;W33 avg_cit 6.6 vs W32 5.4 emit cost)
  - engine.list_chunks parallel IO cost(Azure Search round-trip per doc + RAGAs pre-W34-fix missing)
- F2.4 Decision tree(per plan §3):
  - LLM emit cost dominant(>50% of slowdown)→ W35+ candidate:Rule 8 wording tighten「cite SUFFICIENT chunks」
  - Prompt token cost dominant(>50%)→ W35+ candidate:Rule 7 v2 wording compact(去 examples 但 keep §X.M signal)
  - Engine-fetch IO cost dominant(>50%)→ W35+ candidate:async parallelism 改善(`asyncio.gather` 已有 batch level,但可加 connection pool)
  - Mixed(no single dominant)→ W35+ candidate:multi-axis tightening(combine wording tighten + token compact)

**Non-goals**(out of W34 scope):
- Any production code change beyond F1.0 surgical kwargs propagation(non-architectural per H1)+ F2.1 observability instrumentation(no behavior shift)
- Rule 8 wording tighten — defer W35+ pending W34 evidence
- Prompt token reduction — defer W35+
- (j') section_path filter — defer W35+
- (g')/(i')/(B'.a)/(ii)/(k) — preserved per W33 retro
- New eval-set yaml(use existing `eval-set-v0-w25-supplement.yaml`)

**Component scope**:**C06 Eval Framework**(`backend/eval/orchestrator.py` surgical kwargs propagation + 1 NEW unit test)+ **C05 Generation Pipeline**(`backend/generation/synthesizer.py` + `citation_expansion.py` structlog stage timing — no behavior change)+ **C07 Observability**(structlog stage timing JSON output via existing logging infrastructure)。**No** C04 Retrieval Engine / C03 Indexing / C01 Ingestion / C08 API Gateway / C09-C13 frontend / mockup changes。

---

## §2 Deliverables F0-F3

### F0 — Kickoff(this session 2026-05-26)

- F0.1 Create `docs/01-planning/W34-faithfulness-eval-latency-profile/` folder
- F0.2 R6 Day 0 recursive grep verify(plan-text + code base contamination check per CLAUDE.md §10 R6)— **R6 catch (1)** documented:`build_ragas_samples` line 95 missing W32 (h') kwargs(PC-W32-2 realized);`make_ragas_evaluator` Azure key check verified ✅
- F0.3 Draft `plan.md` 7-section per W33 closed-phase template
- F0.4 Draft `checklist.md` atomic items per plan deliverables
- F0.5 Draft `progress.md` Day 0 entry — kickoff + R6 catch report + W26 F1 baseline reference + decision tree pre-implementation surface
- F0.6 Commit kickoff `docs(planning): kickoff W34-faithfulness-eval-latency-profile + R6 Day 0 catch build_ragas_samples missing W32 (h') wiring + measurement-only phase scope`
- F0.7 session-start.md §10 W34 row append `🟡 active 2026-05-26` + W35+ rolling JIT row defer + W33 row 維持 closed PASS

### F1 — Faithfulness LIVE RAGAs eval(A.1,~2-3h)

**F1.0 R6 catch surgical patch**(`backend/eval/orchestrator.py:91-96`)
- F1.0.a `build_ragas_samples` line 95 `synth = await synthesizer.synthesize(question, retrieval.chunks)` → `synth = await synthesizer.synthesize(question, retrieval.chunks, engine=engine, kb_id=q_kb_id)`(propagate W32 F1.1.a kwargs)
- F1.0.b Existing test `test_orchestrator.py` 或 RAGAs test 加 1 NEW assertion validating engine + kb_id propagation(if test infrastructure exists);if not exists 跳過(non-blocking,production parity restoration suffices)
- F1.0.c Verify pytest baseline 1084(W33 closeout)→ expected 1084 OR 1085(+1 NEW assertion if test added);no regression

**F1.1 Eval-set selection**(use existing yaml)
- F1.1.a Use `docs/eval-set-v0-w25-supplement.yaml`(13 queries — T01-T06 + I01-I07 — all kb_id `sample-document-with-image-1`)
- F1.1.b Verify Q-W25-I07 + Q-W25-I01 included(per yaml lines 178-194 I01 + 296-315 I07)— no NEW eval-set authoring needed

**F1.2 Invoke /eval/run + capture EvalReport**
- F1.2.a curl POST /eval/run with `Authorization: Bearer dev-token` + `{"eval_set_id": "eval-set-v0-w25-supplement"}` + capture full EvalReport JSON
- F1.2.b Expected runtime ~8-12 minutes(W26 F2.20 reference 492s for 13 queries with RAGAs;W33 prompt + W32 (h') may add overhead per F2 latency findings)
- F1.2.c Save raw JSON `backend/w34-f1-ragas-eval-raw.json` + summary table inline progress.md F1

**F1.3 Aggregate vs W26 F1 baseline**
- F1.3.a 4-metric mean comparison table(W34 production / W26 F1 baseline / delta pp)
- F1.3.b failed_queries detail(query_id + metric_failed + got value)
- F1.3.c Per-query metric breakdown(I07 + I01 specifically + other 11 queries)
- F1.3.d Decision tree branch verdict(per plan §3 F1.4 thresholds)

**F1.4 Decision tree application**
- F1.4.a Determine outcome branch — preserve / flag / break per W34 plan §3
- F1.4.b If F1.5 contingency triggered → execute and add comparison
- F1.4.c Document W35+ candidate priority queue update per outcome

**F1.5 Contingency:W32 (h')-only isolation eval**(only if F1.4.a outcome = "break")
- F1.5.a Temporarily revert `prompt_builder.py:28-30` Rule 7 + Rule 8 lines(local edit,no commit yet)
- F1.5.b Restart backend per PC-W32-1 + PC-W33-1(Langfuse + Postgres pre-flight verify)
- F1.5.c Re-run /eval/run + capture `backend/w34-f1-ragas-w32-only-raw.json`
- F1.5.d Restore Rule 7 v2 + Rule 8 after measurement
- F1.5.e Attribute regression source per plan §3 F1.5 outcome decision

**F1.6 Commit + progress.md Day 1**
- F1.6.a Commit `feat(eval): W34 F1 build_ragas_samples engine + kb_id propagation per W32 (h') parity + LIVE RAGAs eval evidence`
- F1.6.b progress.md Day 1 entry — F1.0 surgical patch + F1.1-F1.4 eval result + decision branch + (F1.5 if contingency triggered)

### F2 — Latency profile structlog stage timing(A.2,~1-2h)

**F2.1 Structlog stage timing instrumentation**(`backend/generation/synthesizer.py` + `backend/generation/citation_expansion.py`)
- F2.1.a `synthesizer.synthesize` overall — log `synth_overall_latency_ms` at return
- F2.1.b prompt-build sub-stage — wrap `build_prompt(query, chunks, ...)` with timer + log `synth_prompt_build_latency_ms`
- F2.1.c LLM chat completion sub-stage — wrap `client.chat.completions.create(...)` with timer + log `synth_llm_completion_latency_ms` + `prompt_tokens` + `completion_tokens`(from response.usage)
- F2.1.d `citation_expansion.expand_citations` overall — log `expand_citations_overall_latency_ms` at return
- F2.1.e `engine.list_chunks` parallel batch sub-stage — wrap `asyncio.gather` with timer + log `expand_list_chunks_batch_latency_ms` + `unique_docs_count`
- F2.1.f Same log binding pattern as existing W22 observability per Karpathy §1.3 surgical(no new logger,no new field convention)

**F2.2 5-run latency measurement**(`backend/w34-f2-runner.py` adapted from `w33-f2-runner.py`)
- F2.2.a Q-W25-I07 5 runs back-to-back + Q-W25-I01 5 runs back-to-back
- F2.2.b Capture per-run JSON + structlog JSON output(structlog defaults to stderr;capture via `2>backend/w34-f2-structlog.log`)
- F2.2.c Aggregate per-stage mean latency across 10 runs:
  - synth_overall vs prompt_build + LLM_completion + expand_citations sum
  - LLM_completion vs prompt_tokens/completion_tokens count
  - expand_citations vs list_chunks_batch + unique_docs_count

**F2.3 Aggregate dominant cost determination**
- F2.3.a Per-stage breakdown table:LLM emit / prompt token / engine-fetch / other
- F2.3.b Identify dominant cost(>50% of W33 +57-91% latency vs W32 baseline)
- F2.3.c Document W35+ candidate priority queue update per F2 outcome
- F2.3.d Decision branch:LLM emit dominant / prompt token dominant / engine-fetch dominant / mixed

**F2.4 Commit + progress.md Day 2**
- F2.4.a Commit `feat(observability): W34 F2 structlog stage timing + 10-run latency profile`
- F2.4.b progress.md Day 2 entry — instrumentation summary + 10-run latency table + dominant cost verdict

### F3 — Decision tree analysis + closeout

**A. Combined decision tree(F1 outcome × F2 outcome)**
- A.1 RAGAs branch:preserve / flag / break
- A.2 Latency branch:LLM emit / prompt token / engine-fetch / mixed
- A.3 Intersect → W35+ ship recommendation:
  - faith preserve + LLM emit dominant → W35+ Rule 8 wording tighten OPTIONAL(no urgent priority)
  - faith preserve + prompt token dominant → W35+ Rule 7 v2 wording compact OPTIONAL
  - faith preserve + engine-fetch dominant → W35+ async parallelism enhancement OPTIONAL
  - faith flag + any latency → W35+ Rule 8 wording tighten REQUIRED + revisit faithfulness
  - faith break + any latency → W35+ partial OR full revert Rule 7 v2 + Rule 8 REQUIRED

**B. Cross-doc sync per CLAUDE.md §10 R3 + R5 + R6**
- B.1 plan.md frontmatter status flip
- B.2 checklist.md cross-cutting tick + N/A reason
- B.3 progress.md retro 7-section
- B.4 session-start.md §10 W34 row `🟡 active` → `✅ closed` + §11 W34 CLOSED block prepend
- B.5 RISK_REGISTER NEW R candidate(if F1.4 verdict = break or flag)
- B.6 ADR README — no NEW ADR expected(F1.0 surgical kwargs propagation + F2.1 observability instrumentation both non-architectural per plan §1 + §4 R5)

**C. `.env` cleanup + W35+ priority queue evaluation**
- C.1 `.env` cleanup — W29 env override preserved unchanged
- C.2 W35+ candidate prioritization update per F1.4 + F2.4 outcome intersect

**D. Commit + push**
- D.1 F3 closeout commit — combined with F1 + F2 evidence(per W31-W33 closeout pattern atomic)
- D.2 Push origin/main(per W33 user-instruction precedent)

---

## §3 Acceptance Criteria(G1-G6 — measurement-driven thresholds)

### G1 PRIMARY — Faithfulness LIVE RAGAs eval vs W26 F1 baseline 0.9851

| Gate | Threshold | Decision branch |
|---|---|---|
| **G1 preserve** | faith ≥ 0.9651(W26 -2pp envelope)| W33 over-citation BENIGN → preserve Rule 7 v2 + Rule 8 production ship |
| **G1 flag** | 0.9351 ≤ faith < 0.9651(W26 -5pp to -2pp)| Rule 8 over-citation FLAG → defer ship decision pending W35+ Rule 8 wording tighten test |
| **G1 break** | faith < 0.9351(W26 -5pp 以下)| W33 BREAKS faithfulness → trigger F1.5 contingency W32 (h')-only isolation eval |

### G2 SECONDARY — Latency profile dominant cost identification

| Gate | Criterion | Decision branch |
|---|---|---|
| **G2 LLM emit** | LLM completion latency > 50% of W33-W32 slowdown | W35+ Rule 8 wording tighten 「cite SUFFICIENT」 |
| **G2 prompt token** | Prompt build / chat completion prefill latency > 50% of W33-W32 slowdown | W35+ Rule 7 v2 wording compact 去 examples |
| **G2 engine-fetch** | `engine.list_chunks` batch latency > 50% of W33-W32 slowdown | W35+ async connection pool / parallelism enhancement |
| **G2 mixed** | No single source > 50% | W35+ multi-axis combined tighten + compact |

### G3 backend pytest baseline preserved

1084(W33 closeout)→ expected 1084 OR 1085 post-W34 F1(+1 NEW assertion if test added)。No existing test regression。

### G4 ruff PASS + mypy strict module-path quirk preserved

新 touch files clean;pre-existing 13 errors per CO_W25_mypy_strict_debt unchanged。

### G5 R6 catch (1) `build_ragas_samples` W32 (h') wiring surgical patch verified

- F1.0.a 代碼 grep confirm propagate `engine=engine, kb_id=q_kb_id` 入 line 95 synth.synthesize() call
- F1.0.c pytest no regression

### G6 Q4 measurement-experiment-fail-policy

**N/A for W34** — measurement-only phase,no production behavior shift。F3 outcome drives W35+ ship governance not W34 itself。

---

## §4 R1-R6 Sprint Rules(per CLAUDE.md §10 binding)

- **R1** plan.md committed before F1 code(F0.6 commit kickoff this session)
- **R2** daily commits correspond to progress.md Day-N entries(F0.6 D0 + F1.6 D1 + F2.4 D2 + F3 closeout)
- **R3** plan deviation logged in §7 changelog(no silent drift)
- **R4** OQ resolved → decision-form.md + progress.md Day-N sync(none expected — measurement-only phase)
- **R5** ADR if architectural decision(per H1)— F1.0 kwargs propagation = production parity restoration(non-architectural)/ F2.1 structlog timing = observability instrumentation(non-architectural);**no NEW ADR expected**
- **R6** Day 0 recursive grep verify(F0.2)— **catch (1) `build_ragas_samples` missing W32 (h') wiring**(PC-W32-2 realized — exact integration gap W32 lesson 已警告);**catch (2) confirmed `make_ragas_evaluator` Azure key dependency satisfied via .env AZURE_OPENAI_API_KEY**

---

## §5 D0-D1-D2 Day Breakdown Estimate

| Day | Deliverables | Effort | Verify |
|---|---|---|---|
| **D0(this session 2026-05-26)** | F0.1-F0.7 kickoff | ~1h | plan/checklist/progress committed + R6 verify |
| **D1** | F1.0 surgical patch(~20min)+ F1.1-F1.4 RAGAs LIVE eval(~2-3h including ~8-12min runtime)+ F1.5 contingency if triggered(~2-3h extra)+ F1.6 commit | full D1 | EvalReport JSON + decision tree branch + commit |
| **D2** | F2.1 structlog instrumentation(~30-60min)+ F2.2 5-run measurement(~10min runtime + setup)+ F2.3 aggregate(~30min)+ F2.4 commit + F3 closeout(~1h)= ~3-4h | full D2 | latency table + dominant cost verdict + commit + push |

**Total**:~5-9h actual work spread across 2-3 calendar days(F1.5 contingency adds 2-3h if triggered)。Real-calendar collapse pattern continues per W22-W33(typical 1-5× collapse,W34 likely 1-3× given measurement-only scope vs W33's ship + 5-run scope)。

---

## §6 W33 Carry-overs + Dependencies

### Preserved baseline(W26-W33 inheritance)

- **W29 `.env` env override**:`QUERY_EXPANSION_PER_VARIANT_OVERFETCH=8` + `QUERY_EXPANSION_RRF_K=30`(retrieval-side +40pp,W30→W34 inherits)
- **W28 `Settings.py` defaults**:`parent_doc_max_tokens_per_parent=2000` + `parent_doc_top_k=2` + `parent_doc_dispatch_mode="replace"`(W28 best combo,W34 inherits)
- **W26 `Settings.py` Q4**:`enable_parent_doc_retrieval=False`(W34 NOT toggle)
- **W32 (h') Settings**:`enable_citation_post_hoc_expansion=True` + `citation_expansion_window=10` + `citation_expansion_max_aux=2`(production-default,W34 inherits)
- **W33 prompt layer**:Rule 7 v2 + Rule 8 in SYSTEM_PROMPT(production-default,W34 inherits — F1.5 contingency may temporarily revert local-only no commit)

### Dependencies on prior infrastructure

- **W17 F3 RAGAs integration**:`make_ragas_evaluator(settings)` + `orchestrator.build_ragas_samples` + `RagasRunner` + POST /eval/run endpoint — all wired,production-ready when Azure key + judge LLM available
- **W32 F1.1.a synthesizer wire**:`Synthesizer.synthesize/_stream(..., *, engine=None, kb_id=None)` kwargs — F1.0 surgical patch propagates to RAGAs eval callsite
- **W32 F1.8 `SynthesisResult.expanded_neighbor_chunks`** field — RAGAs eval samples NOT directly using citations,but build_ragas_samples uses `synth.answer` answer text which is enriched per W33 + (h') stack
- **`eval-set-v0-w25-supplement.yaml`** 13-query eval set against `sample-document-with-image-1` KB
- **W26 F1 baseline** `baseline-metrics-W26-D1-raw.json`:faith 0.9851 / correctness 0.7416 / recall@5 0.8744 / p95_latency 1001ms — historical reference

### W26-W33 preventive controls applied

- **PC-W31-1**(corpus-realistic regex)— N/A this phase(no regex change)
- **PC-W31-2**(Settings calibrated against LIVE corpus)— N/A(no NEW Settings)
- **PC-W31-3**(window-based locality empirical validation)— N/A(no window change)
- **PC-W32-1**(backend explicit kill+restart for code reload)— F1.5 contingency + F2.2 verify backend reload mode
- **PC-W32-2**(citation enrichment integration pattern)— **REALIZED W34 F0 R6 catch (1)** — `build_ragas_samples` callsite was the integration gap PC-W32-2 warned about
- **PC-W33-1**(session-start protocol amend — Langfuse + Postgres pre-flight)— F1 + F2 inherits + may extend with `make_ragas_evaluator` Azure key check pattern

### Out of W34 scope(W35+ candidates)

- W35+ ship decisions driven by F3 decision tree intersect:
  - Rule 8 wording tighten「cite SUFFICIENT」 — IF faith flag OR LLM emit dominant
  - Rule 7 v2 wording compact 去 examples — IF prompt token dominant
  - Engine-fetch async connection pool — IF engine-fetch dominant
  - Partial OR full revert Rule 7 v2 + Rule 8 — IF faith break
  - Multi-axis combined tighten + compact — IF mixed
- **(j') section_path prefix filter** — preserve W35+
- **PC-W33-1** session-start protocol amend explicit — preserve W35+ housekeeping
- **(g')** 20-run sample methodology — lower priority(saturated post-W32-W33)
- **(i')** reformulator deterministic temp=0 — lower priority(saturated)
- **(B'.a)** Settings parameter chunk-score threshold — preserve W35+
- **(ii)** CRAG threshold trial — preserved low priority
- **(k)** wire reformulator into eval/orchestrator.py — preserve W35+
- (c)(e)(f)/BUG-026+027 / W22 D8 / W16 F1-F4 Track A preserved

---

## §7 Changelog

| Date | Section | Change | Reason |
|---|---|---|---|
| 2026-05-26 | initial | Plan drafted F0 D0 kickoff | W33 retro carry-over W34+ HIGHEST candidate Faithfulness LIVE RAGAs eval + #2 Latency profile per user explicit pick 2026-05-26 same-day post-W33 closeout |
| 2026-05-26 | §1 + §3 | 2-axis measurement-only phase scope locked + 3-branch decision tree per axis | Per W33 retro decision matrix + Karpathy §1.4 goal-driven verifiable success criteria |
| 2026-05-26 | §6 R6 catch | `build_ragas_samples` line 95 missing W32 (h') kwargs surgical patch needed for production-parity eval | R6 Day 0 recursive grep verify — PC-W32-2 integration gap warning realized at RAGAs eval callsite |
