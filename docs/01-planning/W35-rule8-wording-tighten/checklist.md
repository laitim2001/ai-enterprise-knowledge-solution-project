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
- [x] F0.6 Commit kickoff `b2f4ca3` — `docs(planning): kickoff W35-rule8-wording-tighten + R6 Day 0 catch Rule 8 verbatim wording + test assertions lock + 3 wording options surface`
- [x] F0.7 session-start.md §10 W35 row append `🟡 active 2026-05-26`(commit `b2f4ca3`)+ W34 row 4 commits backfilled `aa1c24e`+`448cb3b`+`0087092`+`6734161` + W36+ rolling JIT row preserved(commit `8c08557`)

## F1 — Rule 8 wording tighten + LIVE RAGAs eval(~2-3h)

### F1.0 Surgical edit(`backend/generation/prompt_builder.py:30`)

- [x] F1.0.a Option B locked initially per user pick 2026-05-26
- [x] F1.0.b Edit Rule 8 line wording Option B applied
- [x] F1.0.c Attribution comment updated per Option B
- [x] F1.0.d ruff `All checks passed!` ✅

### F1.1 Test assertions sync(`backend/tests/test_prompt_builder_dispatch.py:207-221`)

- [x] F1.1.a Function renamed `_cite_breadth` → `_cite_sufficient` + 5 Option B assertions
- [x] F1.1.b Test docstring updated W33→W35 trajectory
- [x] F1.1.c Rule 7 v2 + Rule 6 non-regression assertions unchanged
- [x] F1.1.d Function rename decision = `_cite_sufficient`(umbrella concept across A/B/C options)

### F1.2 pytest baseline preserve

- [x] F1.2.a Scoped pytest test_prompt_builder_dispatch.py = **14 passed** ✅
- [x] F1.2.b Full pytest suite = **1084 passed + 25 skipped + 0 failed in 384.38s** ✅(W34 closeout exact preserve)

### F1.3 Backend explicit kill+restart(per PC-W32-1 + PC-W33-1 + PC-W34-1)

- [x] F1.3.a Postgres `SELECT 1` = 1 ready_for_query ✅(PC-W33-1)
- [x] F1.3.b Langfuse `/api/public/health` 200 OK ✅(PC-W34-1,需 30s timeout cover post-restart warmup);Docker UI 一度卡住 user 重啟 Docker
- [x] F1.3.c 冇 existing backend on :8000 → 直接 start fresh `python -m api.server` → 5/5 /health components OK

### F1.4 Invoke /eval/run + capture EvalReport(Option B initial)

- [x] F1.4.a `backend/w35-f1-ragas-runner.py` created(adapt W34 runner + W34 F1 baseline 0.9836 / 0.7669 / 0.8936 / 1331ms reference + W34 -2pp envelope 0.9637)
- [x] F1.4.b Raw JSON `w35-f1-option-b-raw.json`(renamed F1.7 audit trail);Option C result `w35-f1-option-c-raw.json`
- [x] F1.4.c **runtime Option B 478s + Option C 475s** vs W34 642s = **-25% / -26%** ⭐

### F1.5 Aggregate vs W34 F1 baseline

- [x] F1.5.a 4-metric mean comparison table(Option B + Option C / W34 F1 / delta pp)— inline progress.md Day 1
- [x] F1.5.b failed_queries detail Option B 11 / Option C 10(I07 came back vs Option B)
- [x] F1.5.c Per-query metric breakdown documented
- [x] F1.5.d Decision tree branch verdict per plan §3 G1 — **G1 preserve Option B / G1 IMPROVED Option C ⭐**

### F1.6 Decision tree application

- [x] F1.6.a Outcome branch Option B = preserve;Option C = IMPROVED(beyond preserve)
- [x] F1.6.b F1.7 contingency triggered per Option B correctness -5pp side effect(user lock path (β))
- [x] F1.6.c W36+ priority queue update — DEMOTE Option A more aggressive;PRESERVE PC-W34-1/2 housekeeping(documented progress.md Day 1)

### F1.7 Contingency Option B → Option C re-tighten(per user lock path (β) 2026-05-26)

- [x] F1.7.a NOT applicable(G1 preserved,no "break")
- [x] F1.7.b Option C re-tighten — plan §7 changelog amendment R3 + prompt_builder.py:30 B→C + test_prompt_builder_dispatch.py 5 assertions B→C + pytest 14 PASS + ruff PASS + raw JSON rename + backend kill PID 32632 + restart → 5/5 OK + F1.4 re-run Option C 475s → G1 IMPROVED 0.9876 + p95 -17% + correctness -1.90pp from W26 baseline

### F1.8 Commit + progress.md Day 1

- [ ] F1.8.a Commit `feat(generation): W35 F1 Rule 8 wording tighten Option C re-tighten + LIVE RAGAs eval evidence — G1 IMPROVED 0.9876 + p95 -17% + runtime -26%`(combined Option B initial ship + F1.7 Option C contingency lifecycle)
- [x] F1.8.b progress.md Day 1 entry — F1.0 + F1.1 + F1.2 + F1.3 + F1.4 Option B + F1.5+F1.6 decision verdict Option B + F1.7 contingency Option C + Option C final verdict + W36+ priority queue update + carry-overs

## F2 — Latency re-verify(A.2,~1h)

### F2.1 5-run latency measurement

- [x] F2.1.a `backend/w35-f2-runner.py` adapted from W34 + G2/G3 verdict logic inline
- [x] F2.1.b Backend stderr UTF-16 LE log `w35-uvicorn-restart-optc.log` captured 10 structlog events 14:46-14:49Z
- [x] F2.1.c Aggregate 10-run mean — I07 avg 25.15s / I01 16.70s / synth_overall 12597ms / synth_llm_completion 11483.8ms / synth_expand_citations 1112.6ms / synth_prompt_build 0ms

### F2.2 Aggregate citation count + latency DROP determination

- [x] F2.2.a Per-query avg citation count table — I07 6.0→4.8(-1.2 / -20%);I01 10.2→5.4(-4.8 / -47%)
- [x] F2.2.b Per-stage latency table — synth_overall -25.8%;synth_llm_completion -26.7%;synth_expand_citations -14.9%;synth_prompt_build 0;output_tokens -10.6%;citations_count -32%
- [x] F2.2.c **G2 PASS with margin** ✅ — I07 4.8 ≤ 5 AND I01 5.4 ≤ 8
- [x] F2.2.d **G3 PASS with margin** ⭐⭐ — synth_llm_completion 11483.8ms ≤ 14098ms threshold = -26.7% vs -10% threshold

### F2.3 Commit + progress.md Day 2

- [x] F2.3.a Commit pending F3 closeout combined per W34 atomic pattern
- [x] F2.3.b progress.md Day 2 entry — F2.1 runner + F2.2 Q-level + F2.3 stage timing + G2 G3 verdict

## F3 — Decision tree analysis + closeout

### A. Combined decision tree(F1 outcome × F2 outcome)

- [x] A.1 RAGAs branch = **G1 IMPROVED** ⭐(0.9876 ≥ 0.9637 envelope + actually beats W34 baseline 0.9836)
- [x] A.2 Citation count branch = **G2 drop with margin** ⭐(I07 4.8 / I01 5.4)
- [x] A.3 LLM emit latency branch = **G3 drop with margin** ⭐⭐(11483.8ms / -26.7%)
- [x] A.4 Intersect → **W35 Option C ship production-ready** + W36+ priority queue locked HIGHEST PC-W34-1/2

### B. Cross-doc sync per CLAUDE.md §10 R3 + R5 + R6

- [x] plan.md frontmatter `status: active → closed`(F3 commit time;PASS WITH G1-IMPROVED CAVEAT)
- [x] checklist.md cross-cutting tick + N/A reason(this file)
- [x] progress.md retro 7-section(What Worked + What Didn't / Surprises + Carry-overs + ADR Triggers + Phase Gate Result + W36+ Priority Queue Locked + Actual vs Planned Effort)
- [x] session-start.md §10 W35 row `🟡 active` → `✅ closed PASS WITH G1-IMPROVED CAVEAT`(F3 commit time)
- [x] 🚧 RISK_REGISTER NEW R candidate — DEFERRED W36+ default(G1 IMPROVED no NEW risk material)
- [x] ADR README — no NEW ADR(F1.0/F1.7 Rule 8 wording tighten + F2 re-use W34 instrumentation both non-architectural per plan §1 + §4 R5)

### C. `.env` cleanup + W36+ priority queue evaluation

- [x] `.env` cleanup — W29 env override preserved unchanged
- [x] W36+ candidate prioritization update — HIGHEST PC-W34-1 + PC-W34-2(W35 F1.3 evidence reinforced)+ NEW PC-W35-1(F2 runner cp1252 print encoding bug)+ MEDIUM (j')+ LOW PC-W33-1+PC-W32-1/2 housekeeping + DEMOTED Option A/prompt token/engine-fetch async per F2 evidence + LOWER (g')(i')(B'.a)(ii)(k)+ LONG-TERM (c)(e)(f)/BUG-026+027/W22 D8/W16 F1-F4 Track A IT cred(documented retro §W36+ Priority Queue Locked)

### D. Commit + push

- [x] F3 closeout commit `bf1bee4` — `feat(generation): W35 F2 latency re-verify + W35 closeout PASS WITH G1-IMPROVED CAVEAT — G1 0.9876 +0.40pp / G2 cit -32% / G3 LLM emit -26.7%`(combined F2 + F3 atomic per W31-W34 pattern;19 files / 2009 insertions / 33 deletions)
- [x] Push origin/main `6734161..bf1bee4` ✅(per W33-W34 user-instruction precedent)

---

## Cross-Cutting

- [x] All deliverables committed to git(F0.6 kickoff `b2f4ca3` + F0.7 session-start `8c08557` + F0.7 housekeeping `0d19e47` + F1.8 F1 `c590a86` + F2 + F3 closeout pending combined commit)
- [x] All OQ status changes reflected in `docs/decision-form.md` — no OQ resolved
- [x] All architectural-adjacent decisions documented as ADR — N/A F1.0/F1.7 Rule 8 wording tighten + F2 re-use W34 instrumentation both non-architectural per plan §1 + §4 R5
- [x] `progress.md` retro section written — 7-section per F3 closeout
- [x] `progress.md` frontmatter status flipped to `closed`(F3 commit `bf1bee4`)
- [x] Phase W36+ kickoff trigger noted in retro — candidates list update per F1.6 + F2.2 intersect (HIGHEST PC-W34-1/2 + NEW PC-W35-1)

---

**Lifecycle reminder**:呢份 checklist 隨 plan deliverables 衍生。新加 deliverable 必須先入 plan + changelog,然後再加 checklist item。
