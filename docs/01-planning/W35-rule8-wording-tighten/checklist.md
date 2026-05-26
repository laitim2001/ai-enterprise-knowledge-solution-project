---
phase: W35-rule8-wording-tighten
plan_ref: ./plan.md
status: active   # F0 kickoff 2026-05-26
last_updated: 2026-05-26
---

# Phase W35 — Checklist

> Atomic checkbox(每 item ≤ 1-2 hour effort)。Rule 8 wording tighten + LIVE RAGAs re-verify + latency re-verify。Single-line prompt edit + test assertions sync + measurement-driven gate。

## F0 — Kickoff(plan + checklist + progress + R6 grep verify + session-start sync)

- [x] F0.1 Create `docs/01-planning/W35-rule8-wording-tighten/` folder
- [x] F0.2 R6 Day 0 recursive grep verify — **catch (1) `prompt_builder.py:30` Rule 8 verbatim 5 phrases**(`cite ALL of them` / `partial information` / `each fact ... backed by every chunk` / `two chunks describe the same scenario` / `both warrant a citation marker`);**catch (2) `test_prompt_builder_dispatch.py:207-221` 5 assertions lock**;**catch (3) W33 commit `16b9b3d` verbatim restoration source — W35 是 first divergence,test docstring 「Restored verbatim」 wording 需 update**
- [x] F0.3 Draft `plan.md` 7-section per W34 closed-phase template
- [x] F0.4 Draft `checklist.md` atomic items derived from plan §2 deliverables(this file)
- [x] F0.5 Draft `progress.md` Day 0 entry — kickoff action + R6 catch report + 3 wording options surface + W34 F1+F2 baseline reference + decision tree pre-implementation surface
- [ ] F0.6 Commit kickoff — `docs(planning): kickoff W35-rule8-wording-tighten + R6 Day 0 catch Rule 8 verbatim wording + test assertions lock + 3 wording options surface`
- [ ] F0.7 session-start.md §10 W35 row append `🟡 active 2026-05-26`(commit hash post-F0.6)+ W34 row 維持 closed PASS + W36+ rolling JIT row defer

## F1 — Rule 8 wording tighten + LIVE RAGAs eval(~2-3h)

### F1.0 Surgical edit(`backend/generation/prompt_builder.py:30`)

- [ ] F1.0.a Lock Option(default B,user override pick A/C 之前彈性)— surface 喺 progress.md Day 1 entry beginning + 加 chat 提示 user confirm
- [ ] F1.0.b Edit Rule 8 line wording from W33 verbatim → W35 tightened wording per locked Option(single-line edit prompt_builder.py:30)
- [ ] F1.0.c Update attribution comment trail — `(W33 F1.1.b ...)` → `(W35 F1.0 — Rule 8 wording tighten from W33 verbatim restoration per W34 G2 LLM emit dominant 92% verdict)`
- [ ] F1.0.d ruff `backend/generation/prompt_builder.py` clean

### F1.1 Test assertions sync(`backend/tests/test_prompt_builder_dispatch.py:207-221`)

- [ ] F1.1.a Update `test_system_prompt_includes_rule_8_cite_breadth` 5 assertions per locked Option wording phrases
- [ ] F1.1.b Update test docstring 「Restored verbatim from W31 commit 16b9b3d」 → 「Tightened W35 from W33 verbatim restoration per W34 G2 LLM emit dominant 92%」
- [ ] F1.1.c Rule 7 v2 + Rule 6 non-regression assertions unchanged
- [ ] F1.1.d Decide rename `test_system_prompt_includes_rule_8_cite_breadth` → `test_system_prompt_includes_rule_8_cite_sufficient` OR preserve original name(F1.0.a lock 同時決定)

### F1.2 pytest baseline preserve

- [ ] F1.2.a Run `python -m pytest tests/test_prompt_builder_dispatch.py -v` — expect 3 NEW Rule 7 v2 + Rule 8 + Rule 6 tests + pre-existing tests all pass
- [ ] F1.2.b Run full pytest suite — expect 1084(W34 closeout)→ 1084 pass + 25 skip + 0 fail

### F1.3 Backend explicit kill+restart(per PC-W32-1 + PC-W33-1 + PC-W34-1)

- [ ] F1.3.a Verify Langfuse :3000 + Postgres :5432 reachable(PC-W33-1)
- [ ] F1.3.b Verify Langfuse `/api/public/health` 200(PC-W34-1)+ Postgres `SELECT 1` ready_for_query handshake(PC-W34-1)
- [ ] F1.3.c Kill existing uvicorn + restart `python -m api.server` + bind :8000 wait ~5min lifespan

### F1.4 Invoke /eval/run + capture EvalReport

- [ ] F1.4.a `backend/w35-f1-ragas-runner.py`(adapt `w34-f1-ragas-runner.py`)POST /eval/run with Bearer dev-token + `{"eval_set_id": "eval-set-v0-w25-supplement"}` + capture full EvalReport JSON
- [ ] F1.4.b Raw JSON save `backend/w35-f1-ragas-eval-raw.json`
- [ ] F1.4.c Expected runtime ~10-12 min(W34 F1 reference 642s)

### F1.5 Aggregate vs W34 F1 baseline

- [ ] F1.5.a 4-metric mean comparison table(W35 / W34 F1 / W26 F1 / W34 -2pp envelope / delta pp)
- [ ] F1.5.b failed_queries detail
- [ ] F1.5.c Per-query metric breakdown(I07 + I01 specifically + other 11)
- [ ] F1.5.d Decision tree branch verdict per plan §3 G1

### F1.6 Decision tree application

- [ ] F1.6.a Determine outcome branch — preserve / flag / break per plan §3 G1 thresholds
- [ ] F1.6.b If F1.7 contingency triggered → execute and add comparison
- [ ] F1.6.c Document W36+ candidate priority queue update per outcome

### F1.7 Contingency(only if F1.6.a outcome = "break" OR "flag")

- [ ] F1.7.a If "break":revert prompt_builder.py:30 Rule 8 wording back to W33 verbatim + revert test assertions + git commit revert(no merge to main 之前 user lock)
- [ ] F1.7.b If "flag":evaluate Option A / B / C re-tighten OR partial revert per user decision

### F1.8 Commit + progress.md Day 1

- [ ] F1.8.a Commit `feat(generation): W35 F1 Rule 8 wording tighten「cite SUFFICIENT chunks」 + test assertions sync + LIVE RAGAs eval evidence`
- [ ] F1.8.b progress.md Day 1 entry — F1.0 wording lock + F1.1 test sync + F1.4 eval result + decision branch + (F1.7 contingency if triggered)+ actual vs planned effort

## F2 — Latency re-verify(A.2,~1h)

### F2.1 5-run latency measurement

- [ ] F2.1.a `backend/w35-f2-runner.py`(adapt `w34-f2-runner.py`)Q-W25-I07 5 runs + Q-W25-I01 5 runs back-to-back
- [ ] F2.1.b Backend stderr log capture structlog JSON events `uvicorn-restart-w35.log.err`
- [ ] F2.1.c Aggregate 10-run mean — I07 + I01 avg total + synth_overall + synth_llm_completion + synth_expand_citations + synth_prompt_build

### F2.2 Aggregate citation count + latency DROP determination

- [ ] F2.2.a Per-query avg citation count table(W35 / W34 F2 / delta abs + delta %)
- [ ] F2.2.b Per-stage latency table(W35 / W34 F2 / delta ms + delta %)
- [ ] F2.2.c G2 measurable citation count DROP — target I07 ≤ 5 AND I01 ≤ 8(W34 baseline 6 / 10.2)
- [ ] F2.2.d G3 measurable LLM emit latency DROP — target synth_llm_completion ≤ 14098ms(-10% W34 baseline 15665ms)

### F2.3 Commit + progress.md Day 2

- [ ] F2.3.a Commit `feat(observability): W35 F2 latency re-verify + citation count DROP measurement vs W34 F2 baseline`
- [ ] F2.3.b progress.md Day 2 entry — 10-run latency table + citation count delta + tighten effect verdict

## F3 — Decision tree analysis + closeout

### A. Combined decision tree(F1 outcome × F2 outcome)

- [ ] A.1 RAGAs branch determined — G1 preserve / flag / break per plan §3
- [ ] A.2 Citation count branch determined — G2 drop / inconclusive / null
- [ ] A.3 LLM emit latency branch determined — G3 drop / inconclusive / null
- [ ] A.4 Intersect → W36+ priority queue update per plan §F3 A.4 matrix

### B. Cross-doc sync per CLAUDE.md §10 R3 + R5 + R6

- [ ] plan.md frontmatter `status: active → closed`(measurement-driven PASS OR closed_partial verdict)
- [ ] checklist.md cross-cutting tick + N/A reason(this file)
- [ ] progress.md retro 7-section(What Worked + What Didn't / Surprises + Carry-overs + ADR Triggers + Phase Gate Result + W36+ Priority Queue Locked + Actual vs Planned Effort)
- [ ] session-start.md §10 W35 row `🟡 active` → `✅ closed` + §11 W35 CLOSED block prepend
- [ ] 🚧 RISK_REGISTER NEW R candidate — DEFERRED W36+ default(G1 preserve outcome expected;若 F1.6 break/flag 則 promote NEW R)
- [ ] ADR README — no NEW ADR(F1.0 Rule 8 wording tighten = non-architectural prompt content per H1)

### C. `.env` cleanup + W36+ priority queue evaluation

- [ ] `.env` cleanup — W29 env override preserved unchanged
- [ ] W36+ candidate prioritization update per F3 decision tree intersect — PC-W34-1 + PC-W34-2 + (j') + PC-W33-1 + lower priority preserved 候選 + long-term carry-over(documented retro §W36+ Priority Queue Locked)

### D. Commit + push

- [ ] F3 closeout commit — `feat(generation): W35 F2 latency re-verify + W35 closeout {PASS|PARTIAL} — decision tree intersect verdict`
- [ ] Push origin/main(per W33-W34 user-instruction precedent)

---

## Cross-Cutting

- [ ] All deliverables committed to git(F0.6 kickoff + F1.8 F1 + F2.3 F2 + F3 closeout)
- [ ] All OQ status changes reflected in `docs/decision-form.md` — no OQ resolved expected
- [ ] All architectural-adjacent decisions documented as ADR — N/A F1.0 Rule 8 wording tighten + F2.1 latency re-verify(re-use W34 instrumentation)both non-architectural per plan §1 + §4 R5
- [ ] `progress.md` retro section written — 7-section per closeout commit
- [ ] `progress.md` frontmatter status flipped to `closed` OR `closed_partial` per outcome
- [ ] Phase W36+ kickoff trigger noted in retro — candidates list update per F1.6 + F2.2 intersect

---

**Lifecycle reminder**:呢份 checklist 隨 plan deliverables 衍生。新加 deliverable 必須先入 plan + changelog,然後再加 checklist item。
