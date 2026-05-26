---
phase: W35-rule8-wording-tighten
status: active   # F0 kickoff 2026-05-26 per W34 retro HIGHEST OPTIONAL candidate
last_updated: 2026-05-26
component_scope: C05 Generation Pipeline (prompt_builder.py Rule 8 wording) + C06 Eval Framework (RAGAs LIVE re-verify) + C07 Observability (latency re-verify)
adr_refs:
  - ADR-0034 (W25 F3 D4 query expansion + RAG-Fusion — W35 preserves W29 .env tune)
  - ADR-0037 (W26 F2 parent-doc — preserved per W28 best combo + Q4 default OFF)
  - ADR-0038 (W27 dispatch_mode — preserved "replace")
  - W17 F3 RAGAs 4-metric integration
  - W26 F1 baseline RAGAs report (`baseline-metrics-W26-D1-raw.json`) — historical reference faith 0.9851
  - W32 F1 (h') engine-fetch citation expansion (preserved)
  - W33 F1 Rule 7 v2 + Rule 8 prompt layer (Rule 8 wording is W35 tighten target)
  - W34 F1 RAGAs LIVE eval baseline (faith 0.9836 / correctness 0.7669 / recall@5 0.8936 / p95 1331ms)
  - W34 F2 latency profile baseline (synth_overall 16974ms / synth_llm_completion 15665ms 92% / synth_expand_citations 1308ms 8% / synth_prompt_build 0ms / I07 avg_cit 6 / I01 avg_cit 10.2)
related_carry_overs:
  - W34 retro W35+ HIGHEST OPTIONAL — Rule 8 wording tighten「cite SUFFICIENT chunks」(F2 LLM emit dominant 92% ROI clear)
  - W34 PC-W34-1 (session-start protocol amend Langfuse `/api/public/health` + Postgres `SELECT 1` handshake) — preserved W35+
  - W34 PC-W34-2 (RAGAs judge robustness — gpt-5.4-mini complex multi-step parse failure) — preserved W35+
  - W33 verbatim restoration source `16b9b3d` — W35 是 first divergence from verbatim
---

# W35 — Rule 8 Wording Tighten「cite SUFFICIENT chunks」

## §1 Goal + Scope

**Single primary goal**:Tighten Rule 8 wording 從 W33 「cite ALL of them」 → 「cite SUFFICIENT chunks」 以 bound 過度 cite + reduce LLM `output_tokens` emit cost,同時 preserve W34 G1 baseline faithfulness 0.9836(W34 envelope -2pp = ≥ 0.9637)+ preserve W33 cross-section breadth value 喺 「different angles」 specific multi-cite scenarios。

**Key framing**:
- W34 measurement evidence-driven:F1 G1 preserve(faith 0.9836)+ F2 G2 LLM emit dominant 92% → 確定 ROI 喺 reduce output_tokens emit。
- W35 = first divergence from W33 verbatim restoration(`16b9b3d`)— 之前 W30→W34 都 preserve verbatim Rule 7 v2 + Rule 8。
- **Surgical scope** — 只改 `prompt_builder.py:30` 一條 Rule 8 line + 同步 3 個 W33 NEW test assertions wording。No new feature, no Settings flip, no eval-set author。
- **Measurement-driven gate** — G1 faith ≥ 0.9637 hard threshold;G2 measurable citation count drop;G3 measurable LLM emit latency drop。任一 fail = F1.5 contingency revert OR re-tighten。

**3 候選 wording**(F1.0 implementation lock 之前 §7 changelog surface,user pick):

| Option | Wording | 緊度 + 預測 |
|---|---|---|
| **A 激進** | `cite the most relevant chunks (typically 1-2 per fact) — additional overlapping chunks only if they add non-redundant detail` | 強 bound;可能傷 G1 cross-section breadth |
| **B 中等** ⭐ working candidate | `cite SUFFICIENT chunks to support each fact (typically 1-2 chunks) — additional overlapping chunks warrant citation only when they add non-redundant detail (different angle, complementary evidence)` | 保留 W33 multi-angle intent + soft cap |
| **C 保守** | `cite the chunks that support each fact (typically 1-2 per fact) — avoid citing multiple overlapping chunks that convey the same information` | 最 minimal change |

**Working assumption**:Option B(中等)是 F1.0 implementation default 候選,基於:
- 保留 W33 「different angle, complementary evidence」 cross-section breadth(W34 correctness +2.53pp 證實 W33 + (h') stack 有 measurable contribution)
- 「typically 1-2 chunks」 soft cap explicit reduce LLM emit pressure
- 「SUFFICIENT」 wording match W34 retro F2 verdict — ROI direction reduce output_tokens

User explicit lock 之前 implementation 可彈性。

**Non-goals**(out of W35 scope):
- Rule 7 v2 wording compact(W34 F2 prompt token 0ms 已 DEMOTED LOW)
- Engine-fetch async pool(W34 F2 engine-fetch 8% 已 DEMOTED LOW)
- PC-W34-1 session-start protocol amend(preserve W36+ housekeeping)
- PC-W34-2 RAGAs judge robustness(preserve W36+)
- (j') section_path filter / (B'.a) / (ii) / (k) — preserved
- New eval-set(use existing `eval-set-v0-w25-supplement.yaml` 13 queries)
- Settings flip / Production behavior shift beyond prompt wording

**Component scope**:**C05 Generation Pipeline**(`backend/generation/prompt_builder.py:30` 1-line Rule 8 wording tighten — no behavior shift beyond LLM-prompt-driven citation strategy)+ **C06 Eval Framework**(re-run /eval/run with same eval-set — no orchestrator change)+ **C07 Observability**(re-use W34 F2 structlog stage timing — no new instrumentation)。**No** C01-C04 / C08-C13 changes。

---

## §2 Deliverables F0-F3

### F0 — Kickoff(this session 2026-05-26)

- F0.1 Create `docs/01-planning/W35-rule8-wording-tighten/` folder
- F0.2 R6 Day 0 recursive grep verify(plan-text + code base contamination check per CLAUDE.md §10 R6):
  - **catch (1)** `prompt_builder.py:30` Rule 8 verbatim wording captured(5 key phrases:`cite ALL of them` / `partial information` / `each fact ... backed by every chunk` / `two chunks describe the same scenario` / `both warrant a citation marker`)
  - **catch (2)** `test_prompt_builder_dispatch.py:207-221` 5 assertions 鎖住 Rule 8 verbatim wording — F1.1 test wording sync 必須同步
  - **catch (3)** W33 verbatim restoration source `16b9b3d` — F1.1 test docstring 「Restored verbatim from W31 commit 16b9b3d」 wording 需要 update 至「Tightened W35 from W33 verbatim restoration」
- F0.3 Draft `plan.md` 7-section per W34 closed-phase template(this file)
- F0.4 Draft `checklist.md` atomic items per plan §2 deliverables
- F0.5 Draft `progress.md` Day 0 entry — kickoff + R6 catch report + 3 wording options surface + W34 baseline reference + decision tree pre-implementation
- F0.6 Commit kickoff `docs(planning): kickoff W35-rule8-wording-tighten + R6 Day 0 catch Rule 8 verbatim wording + test assertions lock + 3 wording options surface`
- F0.7 session-start.md §10 W35 row append `🟡 active 2026-05-26` + W34 row 維持 closed PASS

### F1 — Rule 8 wording tighten + LIVE RAGAs eval(~2-3h)

**F1.0 Surgical edit**(`backend/generation/prompt_builder.py:30`)
- F1.0.a Lock Option(default B,user override pick A/C 之前彈性)— surface 喺 progress.md Day 1 entry beginning
- F1.0.b Edit Rule 8 line wording from W33 verbatim → W35 tightened wording per locked Option
- F1.0.c Preserve W33 attribution comment trail format — update `(W33 F1.1.b ...)` → `(W35 F1.0 — Rule 8 wording tighten from W33 verbatim restoration per W34 G2 LLM emit dominant 92% verdict)`
- F1.0.d ruff `backend/generation/prompt_builder.py` clean

**F1.1 Test assertions sync**(`backend/tests/test_prompt_builder_dispatch.py:207-221`)
- F1.1.a Update `test_system_prompt_includes_rule_8_cite_breadth` 5 assertions per locked Option wording phrases(retain assertion structure,replace inner phrases)
- F1.1.b Update test docstring 「Restored verbatim from W31 commit 16b9b3d」 → 「Tightened W35 from W33 verbatim restoration per W34 G2 LLM emit dominant 92%」
- F1.1.c Rule 7 v2 + Rule 6 non-regression assertions unchanged
- F1.1.d Rename test function name from `test_system_prompt_includes_rule_8_cite_breadth` → `test_system_prompt_includes_rule_8_cite_sufficient`(reflect tighten intent)OR preserve original name with updated assertions(decide F1.0.a lock with user)

**F1.2 pytest baseline preserve**
- F1.2.a Run `python -m pytest tests/test_prompt_builder_dispatch.py -v` — expect 3 NEW Rule 7 v2 + Rule 8 + Rule 6 tests + pre-existing tests all pass
- F1.2.b Run full pytest suite — expect 1084(W34 closeout)→ 1084(no new test added)pass + 25 skip + 0 fail

**F1.3 Backend explicit kill+restart**(per PC-W32-1 + PC-W33-1 + PC-W34-1)
- F1.3.a Verify Langfuse :3000 + Postgres :5432 reachable(PC-W33-1)
- F1.3.b Verify Langfuse `/api/public/health` 200(PC-W34-1)+ Postgres `SELECT 1` ready_for_query handshake(PC-W34-1)
- F1.3.c Kill existing uvicorn + restart `python -m api.server` + bind :8000 wait ~5min lifespan

**F1.4 Invoke /eval/run + capture EvalReport**(re-use W34 F1 eval-set)
- F1.4.a `backend/w35-f1-ragas-runner.py`(adapt `w34-f1-ragas-runner.py`)POST /eval/run with Bearer dev-token + `{"eval_set_id": "eval-set-v0-w25-supplement"}` + capture full EvalReport JSON
- F1.4.b Raw JSON save `backend/w35-f1-ragas-eval-raw.json`
- F1.4.c Expected runtime ~10-12 min(W34 F1 reference 642s)

**F1.5 Aggregate vs W34 F1 baseline**
- F1.5.a 4-metric mean comparison table(W35 / W34 F1 / W26 F1 / W34 -2pp envelope / delta pp)
- F1.5.b failed_queries detail
- F1.5.c Per-query metric breakdown(I07 + I01 specifically + other 11)
- F1.5.d Decision tree branch verdict per §3 G1

**F1.6 Decision tree application**
- F1.6.a Outcome branch — preserve / flag / break per §3 G1 thresholds
- F1.6.b If F1.5 contingency triggered → execute and add comparison
- F1.6.c Document W36+ candidate priority queue update per outcome

**F1.7 Contingency:revert OR re-tighten**(only if F1.6.a outcome = "break" OR "flag")
- F1.7.a If "break":revert prompt_builder.py:30 Rule 8 wording back to W33 verbatim restoration + revert test assertions + git commit revert(no merge to main 之前 user lock)
- F1.7.b If "flag":evaluate Option A / B / C re-tighten OR partial revert per user decision

**F1.8 Commit + progress.md Day 1**
- F1.8.a Commit `feat(generation): W35 F1 Rule 8 wording tighten「cite SUFFICIENT chunks」 + test assertions sync + LIVE RAGAs eval evidence`
- F1.8.b progress.md Day 1 entry — F1.0 wording lock + F1.1 test sync + F1.4 eval result + decision branch + (F1.7 contingency if triggered)

### F2 — Latency re-verify(A.2,~1h validation)

**F2.1 5-run latency measurement**(re-use W34 F2 structlog stage timing — no new instrumentation)
- F2.1.a `backend/w35-f2-runner.py`(adapt `w34-f2-runner.py`)Q-W25-I07 5 runs + Q-W25-I01 5 runs back-to-back
- F2.1.b Backend stderr log capture structlog JSON events `uvicorn-restart-w35.log.err`
- F2.1.c Aggregate 10-run mean — I07 + I01 avg total + synth_overall + synth_llm_completion + synth_expand_citations + synth_prompt_build

**F2.2 Aggregate citation count + latency DROP determination**
- F2.2.a Per-query avg citation count table(W35 / W34 F2 / delta abs + delta %)
- F2.2.b Per-stage latency table(W35 / W34 F2 / delta ms + delta %)
- F2.2.c G2 measurable citation count DROP — target -20% to -40% per I07 / I01(W34 baseline I07 6 cit / I01 10.2 cit)
- G2.2.d G3 measurable LLM emit latency DROP — target -10% to -30% synth_llm_completion(W34 baseline 15665ms)

**F2.3 Commit + progress.md Day 2**
- F2.3.a Commit `feat(observability): W35 F2 latency re-verify + citation count DROP measurement vs W34 F2 baseline`
- F2.3.b progress.md Day 2 entry — 10-run latency table + citation count delta + tighten effect verdict

### F3 — Decision tree analysis + closeout

**A. Combined decision tree(F1 outcome × F2 outcome)**
- A.1 RAGAs branch:G1 preserve / flag / break per §3
- A.2 Citation count branch:G2 measurable drop / inconclusive / null
- A.3 LLM emit latency branch:G3 measurable drop / inconclusive / null
- A.4 Intersect → W36+ priority queue update:
  - G1 preserve + G2 + G3 drop → W35 tighten production-ready ship → preserve in main
  - G1 preserve + G2 drop + G3 null → tighten effective on emit but not on latency(judge gpt-5.5 may dominate)→ preserve ship + lower priority W36+ revisit
  - G1 preserve + G2 null → tighten ineffective(wording change insufficient)→ preserve ship + W36+ Option A more aggressive
  - G1 flag → defer ship + W36+ Option C more conservative OR partial revert
  - G1 break → trigger F1.7 contingency revert + W36+ revisit Rule 7 v2 + Rule 8 entirely

**B. Cross-doc sync per CLAUDE.md §10 R3 + R5 + R6**
- B.1 plan.md frontmatter `status: active → closed`(measurement-driven PASS OR closed_partial verdict)
- B.2 checklist.md cross-cutting tick + N/A reason
- B.3 progress.md retro 7-section(What Worked + What Didn't / Surprises + Carry-overs + ADR Triggers + Phase Gate Result + W36+ Priority Queue Locked + Actual vs Planned Effort)
- B.4 session-start.md §10 W35 row `🟡 active` → `✅ closed` + §11 W35 CLOSED block prepend
- B.5 RISK_REGISTER NEW R candidate(if F1.6 verdict = break OR flag)
- B.6 ADR README — no NEW ADR expected(F1.0 Rule 8 wording tighten = non-architectural prompt content per H1)

**C. `.env` cleanup + W36+ priority queue evaluation**
- C.1 `.env` cleanup — W29 env override preserved unchanged
- C.2 W36+ candidate prioritization update per F1.6 + F2.2 outcome intersect

**D. Commit + push**
- D.1 F3 closeout commit — combined with F1 + F2 evidence(per W31-W34 closeout pattern atomic)
- D.2 Push origin/main(per W33-W34 user-instruction precedent)

---

## §3 Acceptance Criteria(G1-G6 — measurement-driven thresholds)

### G1 PRIMARY — Faithfulness LIVE RAGAs eval vs W34 F1 baseline 0.9836

| Gate | Threshold | Decision branch |
|---|---|---|
| **G1 preserve** | faith ≥ 0.9637(W34 -2pp envelope)| W35 tighten BENIGN faithfulness → preserve production ship |
| **G1 flag** | 0.9337 ≤ faith < 0.9637(W34 -5pp to -2pp)| W35 tighten breaks faithfulness mildly → defer ship,F1.7 evaluate Option A/C |
| **G1 break** | faith < 0.9337(W34 -5pp 以下)| W35 tighten BREAKS faithfulness → trigger F1.7 contingency revert |

### G2 SECONDARY — Citation count measurable DROP vs W34 F2 baseline

| Gate | Criterion | Decision branch |
|---|---|---|
| **G2 drop** | I07 avg_cit ≤ 5 AND I01 avg_cit ≤ 8(W34 baseline 6 / 10.2)| Tighten effective on citation strategy |
| **G2 inconclusive** | Single query drops OR drop < 10% | Partial tighten effect — preserve ship + lower priority W36+ revisit |
| **G2 null** | Both queries unchanged OR INCREASE | Tighten wording ineffective — W36+ Option A more aggressive |

### G3 SECONDARY — LLM emit latency DROP vs W34 F2 baseline 15665ms

| Gate | Criterion | Decision branch |
|---|---|---|
| **G3 drop** | synth_llm_completion ≤ 14098ms(-10% W34 baseline)| Tighten effective on emit latency |
| **G3 inconclusive** | drop < 10% | Tighten weak — judge gpt-5.5 may dominate emit cost |
| **G3 null** | unchanged OR INCREASE | Tighten ineffective on latency — W36+ revisit |

### G4 backend pytest baseline preserved

1084(W34 closeout)→ expected 1084(no new test added,F1.1 in-place assertion update)。No existing test regression。

### G5 ruff PASS + mypy strict module-path quirk preserved

新 touch files clean;pre-existing 13 errors per CO_W25_mypy_strict_debt unchanged。

### G6 R6 catch verify

- F0.2 R6 catch (1) + (2) + (3) 全部 surfaced in progress.md Day 0
- F1.0.c attribution comment trail updated
- F1.1.b test docstring updated

---

## §4 R1-R6 Sprint Rules(per CLAUDE.md §10 binding)

- **R1** plan.md committed before F1 code(F0.6 commit kickoff this session)
- **R2** daily commits correspond to progress.md Day-N entries(F0.6 D0 + F1.8 D1 + F2.3 D2 + F3 closeout)
- **R3** plan deviation logged in §7 changelog(no silent drift)
- **R4** OQ resolved → decision-form.md + progress.md Day-N sync(none expected — wording tighten phase)
- **R5** ADR if architectural decision(per H1)— F1.0 Rule 8 wording tighten = non-architectural prompt content change(no §3 / §4 component schema / vendor / storage layout impact);**no NEW ADR expected**
- **R6** Day 0 recursive grep verify(F0.2)— **catch (1) Rule 8 verbatim wording 5 phrases**(`cite ALL of them` / `partial information` / `each fact ... backed by every chunk` / `two chunks describe the same scenario` / `both warrant a citation marker`);**catch (2) test_prompt_builder_dispatch.py:207-221 assertions lock**;**catch (3) W33 commit `16b9b3d` verbatim source — W35 是 first divergence,docstring 需 update**

---

## §5 D0-D1-D2 Day Breakdown Estimate

| Day | Deliverables | Effort | Verify |
|---|---|---|---|
| **D0(this session 2026-05-26)** | F0.1-F0.7 kickoff | ~1h | plan/checklist/progress committed + R6 verify |
| **D1** | F1.0 wording lock(~10min)+ F1.1 test sync(~20min)+ F1.2 pytest(~5min)+ F1.3 backend restart(~10min)+ F1.4 RAGAs eval(~10-12min runtime)+ F1.5-F1.6 aggregate + decision(~30min)+ F1.7 contingency if triggered(~30-60min extra)+ F1.8 commit | ~2-3h | EvalReport JSON + decision tree branch + commit |
| **D2** | F2.1 5-run measurement(~10min runtime)+ F2.2 aggregate(~20min)+ F2.3 commit + F3 closeout(~1h)= ~1.5-2h | ~1.5-2h | latency + citation count table + commit + push |

**Total**:~4-6h actual work spread across 2 calendar days(F1.7 contingency adds 30-60min if triggered)。Real-calendar collapse pattern continues per W22-W34(typical 1-3× collapse,W35 likely 1-2× given measurement re-verify scope smaller than W34's instrumentation-init scope)。

---

## §6 W34 Carry-overs + Dependencies

### Preserved baseline(W26-W34 inheritance)

- **W29 `.env` env override**:`QUERY_EXPANSION_PER_VARIANT_OVERFETCH=8` + `QUERY_EXPANSION_RRF_K=30`(retrieval-side +40pp,W30→W35 inherits)
- **W28 `Settings.py` defaults**:`parent_doc_max_tokens_per_parent=2000` + `parent_doc_top_k=2` + `parent_doc_dispatch_mode="replace"`(W28 best combo,W35 inherits)
- **W26 `Settings.py` Q4**:`enable_parent_doc_retrieval=False`(W35 NOT toggle)
- **W32 (h') Settings**:`enable_citation_post_hoc_expansion=True` + `citation_expansion_window=10` + `citation_expansion_max_aux=2`(production-default,W35 inherits)
- **W33 prompt layer Rule 7 v2**:preserved verbatim(W35 only tightens Rule 8)
- **W34 F2 structlog stage timing**:preserved(W35 re-uses for F2 re-verify)

### Dependencies on prior infrastructure

- **W17 F3 RAGAs integration**:`make_ragas_evaluator(settings)` + `orchestrator.build_ragas_samples` + `RagasRunner` + POST /eval/run endpoint(W34 F1.0 surgical patch applied — kwargs propagation production-parity)
- **W34 F2 structlog stage timing**:`synth_overall_latency_ms` / `synth_prompt_build_latency_ms` / `synth_llm_completion_latency_ms` / `synth_expand_citations_latency_ms` / `expand_citations_list_chunks_batch` event — re-used for W35 F2 re-verify
- **`eval-set-v0-w25-supplement.yaml`** 13-query eval set against `sample-document-with-image-1` KB
- **W34 F1 baseline** `backend/w34-f1-ragas-eval-raw.json`:faith 0.9836 / correctness 0.7669 / recall@5 0.8936 / p95_latency 1331ms — measurement baseline
- **W34 F2 baseline** `backend/w34-f2-aggregate.json`:I07 avg 62.2s / I01 avg 53.4s / synth_overall 16974ms / synth_llm_completion 15665ms 92% / synth_expand_citations 1308ms 8% / synth_prompt_build 0ms / I07 avg_cit 6 / I01 avg_cit 10.2 — measurement baseline

### W26-W34 preventive controls applied

- **PC-W31-1/2/3** corpus-realistic regex / Settings calibrated / window-based locality — N/A this phase
- **PC-W32-1** backend explicit kill+restart — F1.3 verify backend reload
- **PC-W32-2** citation enrichment integration pattern — N/A(W34 F1.0 already realized + preserved)
- **PC-W33-1** session-start protocol amend(Langfuse + Postgres pre-flight)— F1.3 verify
- **PC-W34-1** session-start protocol amend extend(Langfuse `/api/public/health` 200 + Postgres `SELECT 1` ready_for_query handshake)— F1.3 verify
- **PC-W34-2** RAGAs judge robustness — preserved W36+(not blocking W35)

### Out of W35 scope(W36+ candidates)

- W36+ ship decisions driven by F3 decision tree intersect(see §3 G1+G2+G3)
- **PC-W34-1** session-start protocol amend explicit — preserve W36+ housekeeping
- **PC-W34-2** RAGAs judge robustness(gpt-5.4-mini → gpt-5.5 OR robust JSON parsing OR exclude complex queries from RAGAs eval-set per Q14 SME-validate)— preserve W36+
- **(j') section_path prefix filter** — preserve W36+
- **PC-W33-1** session-start protocol amend explicit baseline — preserve W36+ housekeeping
- **(g')** 20-run sample methodology — saturated low priority
- **(i')** reformulator deterministic temp=0 — saturated low priority
- **(B'.a)** Settings parameter chunk-score threshold — preserve W36+
- **(ii)** CRAG threshold trial — preserved low priority
- **(k)** wire reformulator into eval/orchestrator.py — preserve W36+
- (c)(e)(f) / BUG-026+027 / W22 D8 / W16 F1-F4 Track A — long-term carry-over

---

## §7 Changelog

| Date | Section | Change | Reason |
|---|---|---|---|
| 2026-05-26 | initial | Plan drafted F0 D0 kickoff | W34 retro HIGHEST OPTIONAL candidate Rule 8 wording tighten per user explicit pick 2026-05-26 same-day post-W34 closeout |
| 2026-05-26 | §1 + §3 | Tighten scope locked + 3-option wording surface(Option B default candidate)+ 3-axis decision tree(G1 faith / G2 cit count / G3 LLM emit latency)| Per W34 F2 G2 LLM emit dominant 92% verdict + W34 F1 G1 preserve + Karpathy §1.4 verifiable success criteria |
| 2026-05-26 | §6 R6 catch | Rule 8 verbatim 5 phrases + test assertions lock + W33 verbatim restoration source `16b9b3d` first divergence | R6 Day 0 recursive grep verify — surface contamination check before F1.0 wording lock |
