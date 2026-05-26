---
phase: W33-rule7-rule8-restoration
plan_ref: ./plan.md
status: active
last_updated: 2026-05-26
---

# Phase W33 — Checklist

> Atomic checkbox(每 item ≤ 1-2 hour effort)。Sequential ship on W32 (h') baseline。

## F0 — Kickoff(plan + checklist + progress + R6 grep verify + session-start sync)

- [x] F0.1 Create `docs/01-planning/W33-rule7-rule8-restoration/` folder
- [x] F0.2 R6 Day 0 recursive grep verify — `prompt_builder.py` Rule 1-6 only(0 matches Rule 7/8 — post-W31-revert state confirmed via `09805d6` history)+ `synthesizer.py` W32 wire intact(L31 expand_citations import + L57 expanded_neighbor_chunks field + L135-138 engine=None/kb_id=None kwargs + L161-197 synthesize integration + L272-301 stream integration)+ `citation_expansion.py` W32 module present + `Settings.py` W32 (h') knobs intact(L264 enable_citation_post_hoc_expansion=True + L270 citation_expansion_window=10 + L274 citation_expansion_max_aux=2)+ W31 commit `16b9b3d` Rule 7 v2 + Rule 8 wording verbatim source confirmed via `git show`
- [x] F0.3 Draft `plan.md` 7-section per W32 closed-phase template
- [x] F0.4 Draft `checklist.md` atomic items derived from plan §2 deliverables(this file)
- [x] F0.5 Draft `progress.md` Day 0 entry — kickoff action + R6 catch report + W32 sequential ship rationale + Karpathy §1.1 G1 redefinition surface
- [x] F0.6 Commit kickoff `c56afa0` — `docs(planning): kickoff W33-rule7-rule8-restoration + sequential ship on W32 (h') baseline + R6 Day 0 verify`
- [x] F0.7 session-start.md §10 W33 row append `🟡 active 2026-05-26` + W34+ rolling JIT row defer + W32 row 維持 closed PASS

## F1 — Implementation(D1 estimate — short single-axis ~1-2h)

### F1.1 Prompt layer edit(`backend/generation/prompt_builder.py:20-28` SYSTEM_PROMPT)

- [x] F1.1.a Append Rule 7 v2 verbatim from W31 commit `16b9b3d` after existing Rule 6 + trailing attribution comment `(W33 F1.1.a — Rule 7 v2 restored from W31 commit 16b9b3d per sequential ship on W32 (h') baseline)`
- [x] F1.1.b Append Rule 8 verbatim from W31 commit `16b9b3d` after Rule 7 v2 + trailing attribution comment `(W33 F1.1.b — Rule 8 restored from W31 commit 16b9b3d per sequential ship layered on W32 (h') backend)`
- [x] F1.1.c Preserve Rule 1-6 unchanged — no edit;non-regression guard via F1.2.a test `test_system_prompt_rule_6_ch005_preserved_non_regression`

### F1.2 Unit tests + non-regression coverage

- [x] F1.2.a `test_prompt_builder_dispatch.py` +3 NEW tests ALL PASS:
  - `test_system_prompt_includes_rule_7_v2_specificity_preference` ✅
  - `test_system_prompt_includes_rule_8_cite_breadth` ✅
  - `test_system_prompt_rule_6_ch005_preserved_non_regression` ✅
- [x] F1.2.b backend pytest baseline 1081 → **1084 passed + 25 skipped + 0 failed**(+3 NEW exact match;full run 760.29s ≈ 12min,no regression)
- [x] F1.2.c ruff PASS on touched files(`ruff check generation/prompt_builder.py tests/test_prompt_builder_dispatch.py` All checks passed!)
- [x] F1.2.d mypy strict module-path quirk preserved(pre-existing `Source file found twice` per CO_W25_mypy_strict_debt unchanged;prompt_builder.py 本身無 NEW mypy violation)

### F1.3 Commit + progress.md Day 1

- [ ] F1.3.a Commit `feat(generation): W33 F1 Rule 7 v2 + Rule 8 prompt restoration on W32 (h') baseline + 3 NEW unit tests` per CLAUDE.md R2 daily commit binding
- [x] F1.3.b progress.md Day 1 entry — implementation summary(verbatim restoration evidence)+ test verdict 1084/25/0 + ruff/mypy state + actual vs planned effort(-67% real-calendar collapse)

## F2 — 5-run reproducibility verify Q-W25-I07 + Q-W25-I01 control(D2 estimate)

- [ ] F2.1 Backend explicit kill+restart `python -m api.server` per PC-W32-1(WatchFiles NOT active;explicit verify code reload via /health=ok + ?route inspection sanity check)
- [ ] F2.2 curl POST /query Q-W25-I07「show me all the Integration scenarios」5 runs back-to-back — per-run JSON in `backend/w33-f2-i07-multi-run-{1-5}.json`
- [ ] F2.3 curl POST /query Q-W25-I01「what is the high level architecture」5 runs back-to-back(control)— per-run JSON `backend/w33-f2-i01-multi-run-{1-5}.json`
- [ ] F2.4 Aggregate report inline progress.md F2 — Q-I07 distinct walkthrough cite count vs W32 baseline 5.4 / Q-I01 G2 no regression / G1a/G1b/G2-G6 verdict draft
- [ ] F2.5 progress.md Day 2 F2 entry — 5-run table + cumulative baseline comparison(W31 reverted 20% → W32 (h') 100/100/5.4 → W33 ?)+ expansion fired count + G1 verdict draft

## F3 — Closeout — Phase Gate + cross-doc sync + commit + push

### A. Phase Gate G1a-G1b-G2-G3-G4-G5-G6 evaluation

- [ ] G1a MAINTAIN W32 baseline strict 5/5 + relaxed 5/5
  - G1a strict (≥ 2 distinct walkthrough cited in ≥ 1 run — MAINTAIN W32 100%)
  - G1a relaxed (≥ 1 walkthrough cited per run for ≥ 3/5 — MAINTAIN W32 100%)
- [ ] G1b ADDITIVE cite breadth vs W32 baseline 5.4
  - G1b mean (avg distinct walkthrough cited per run ≥ 5.4)
  - G1b coverage (non-(h') sourced walkthrough evidence — LLM cited §X.M not from engine-fetch expansion)
- [ ] G2 control Q-W25-I01 no regression(refusals 0/5 + avg_cit ≥ 3.5 + faithfulness within W32 baseline)
- [ ] G3 backend pytest baseline preserved 1081 → ~1084
- [ ] G4 ruff PASS;mypy strict module-path quirk pre-existing per CO_W25_mypy_strict_debt
- [ ] G5 NEW unit tests PASS — F1.2.a 3 NEW
- [ ] G6 measurement-experiment-fail-policy applied per Q4 — outcome-driven decision matrix per plan §3

### B. Cross-doc sync per CLAUDE.md §10 R3 + R5 + R6

- [ ] plan.md frontmatter `status: active → closed` OR `closed_partial` per G1 verdict
- [ ] checklist.md cross-cutting tick + N/A reason
- [ ] progress.md retro 7-section
- [ ] session-start.md §10 W33 row `🟡 active` → `✅ closed` OR `closed_partial`
- [ ] session-start.md §11 W33 CLOSED block prepend
- [ ] RISK_REGISTER NEW R candidate evaluate(prompt over-citation noise risk if Rule 8 引發 G2 regression)
- [ ] COMPONENT_CATALOG C05 status note update if (h') + Rule 7 v2 + Rule 8 combined ship
- [ ] ADR README — no NEW ADR expected per §2(prompt iteration within existing framework parallel to W30/W31 attempts;non-architectural)

### C. `.env` cleanup + W34+ priority queue evaluation

- [ ] `.env` cleanup — W29 Setting tune `overfetch=8 + rrf_k=30` env override PRESERVED unchanged
- [ ] W34+ candidate prioritization update per F3 outcome — (j') section_path filter / (B'.a) Settings parameter chunk-score / (g') 20-run methodology / (i') reformulator temp=0 / (ii) CRAG / (k) eval-wire / (c)/(e)/(f)/BUG-026+027 carry-overs

### D. Commit + push

- [ ] F3 closeout commit — combined with F2 evidence(per W31+W32 closeout pattern;prompt edit + tests + retro + cross-doc sync atomic)
- [ ] Push origin/main(per W32 user-instruction precedent)

---

## Cross-Cutting

- [ ] All deliverables committed to git(F0.6 kickoff commit + F1.3 F1 commit + F3 closeout commit)
- [ ] All OQ status changes reflected in `docs/decision-form.md` — no OQ resolved expected(pure C05 prompt iteration)
- [ ] All architectural-adjacent decisions documented as ADR — F1.1 prompt iteration within existing framework,non-architectural per plan §1 scope decl
- [ ] `progress.md` retro section written — 7-section per closeout commit
- [ ] `progress.md` frontmatter status flipped to `closed` OR `closed_partial`
- [ ] Phase W34+ kickoff trigger noted in retro — candidates list update per F3 outcome

---

**Lifecycle reminder**:呢份 checklist 隨 plan deliverables 衍生。新加 deliverable 必須先入 plan + changelog,然後再加 checklist item。
