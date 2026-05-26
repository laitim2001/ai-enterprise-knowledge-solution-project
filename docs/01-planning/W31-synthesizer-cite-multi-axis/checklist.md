---
phase: W31-synthesizer-cite-multi-axis
plan_ref: ./plan.md
status: active
last_updated: 2026-05-26
---

# Phase W31 — Checklist

> Atomic checkbox(每 item ≤ 1-2 hour effort)。

## F0 — Kickoff(plan + checklist + progress + R6 grep verify + session-start sync)

- [x] F0.1 Create `docs/01-planning/W31-synthesizer-cite-multi-axis/` folder
- [x] F0.2 R6 Day 0 recursive grep verify — `prompt_builder.py:28` SYSTEM_PROMPT current state confirmed only Rule 1-6 present(W30 Rule 7 REVERTED per `e192464`)+ `Settings.py` L198-243 parent-doc + dispatch knobs current state confirmed + `synthesizer.py` synthesize+synthesize_stream call sites confirmed no existing post-hoc citation expansion logic + `citation_image_neighbors.py` W25 F5 D1 pattern confirmed as parallel reference for B'.c → **no shipped-pattern conflict for B'.b / B'.c / Rule 7 v2**(W31 multi-axis subset all 3 axes 新 work,not redundant)
- [x] F0.3 Draft `plan.md` 7-section per W30 closed-phase template
- [x] F0.4 Draft `checklist.md` atomic items derived from plan §2 deliverables(this file)
- [x] F0.5 Draft `progress.md` Day 0 entry — kickoff action + R6 catch report + (B'.b + B'.c + Rule 7 v2) multi-axis subset user pick rationale
- [x] F0.6 Commit kickoff `3a838b5` — `docs(planning): kickoff W31-synthesizer-cite-multi-axis + R6 Day 0 no-shipped-pattern confirm + (B'.b + B'.c + Rule 7 v2) multi-axis subset pick`
- [ ] F0.7 session-start.md §10 W31 row append `🟡 active 2026-05-26` + W32+ rolling JIT row defer + W30 row 維持 closed_partial

## F1 — Implementation(D1 estimate)

### F1.1 Prompt layer edit(`backend/generation/prompt_builder.py:28` SYSTEM_PROMPT)

- [x] F1.1.a NEW Rule 7 v2 `prompt_builder.py:28-30` —「§X.M numbering pattern」+ reference examples(§8.1/§8.2/§8.3, Scenario A walkthrough, Step 3.2)+ intro chunk insufficiency framing
- [x] F1.1.b NEW Rule 8 `prompt_builder.py:30-31` —「cite ALL of them」+「each fact backed by every chunk」+ two-chunks-same-scenario reference example
- [x] F1.1.c Rule 6 CH-005 preserved unchanged(non-regression test `test_system_prompt_rule_6_ch005_preserved_non_regression` PASS)

### F1.2 Backend layer NEW module(`backend/generation/citation_expansion.py`)

- [x] F1.2.a `expand_citations(answer_text, citation_ids, chunks, *, settings) → (expanded_text, expanded_citation_ids)` pure function signature
- [x] F1.2.b Neighbor inspection logic — same doc constraint + ±window chunk_index + score ≥ threshold + title regex `§\\d+\\.\\d+` filter(keyword overlap deferred Karpathy §1.2 simplicity — title pattern sufficient first cut)
- [x] F1.2.c Auto-insert `[chunk-{neighbor_id}]` markers + max_aux cap + dedupe against existing citation_ids + sort-by-distance prefer-closer
- [x] F1.2.d `backend/tests/test_citation_expansion.py` **15 unit tests** PASS — happy path / disabled flag / empty inputs / §X.M filter / score threshold / window boundary / same doc / dedupe / max_aux cap / closer-neighbor-preferred / cited-not-in-chunks defensive / multiple cited / self-at-distance-0 exclude / extract_citation_ids ordering

### F1.3 Settings NEW knobs(`backend/storage/settings.py:245-272`)

- [x] F1.3.a `enable_citation_post_hoc_expansion: bool = True` — W31 measurement default ON per Karpathy §1.4 goal-driven「make it pass」requires axis enabled
- [x] F1.3.b `citation_expansion_window: int = 3` — parallel to W25 F5 D1 `citation_neighbour_window=3`
- [x] F1.3.c `citation_expansion_score_threshold: float = 0.5` — Cohere v4.0-pro reranked range [0.5, 1.0] per W26 F1 D1 empirical
- [x] F1.3.d `citation_expansion_max_aux: int = 2` — parallel to W25 F5 D1 `citation_neighbour_max_aux_images=2`

### F1.4 Wire citation expansion into synthesizer pipeline

- [x] F1.4.a `synthesizer.py:135-152` — `synthesize` method wires `expand_citations` after `extract_citation_ids` + `refused` detection,only when not refused;passes `get_settings()` for runtime Settings read
- [x] F1.4.b `synthesizer.py:233-241` — `synthesize_stream` applies expansion in `result` event payload after stream complete(text-delta partial frames yielded before expansion;final `result` carries expanded answer + citation_ids)
- [x] F1.4.c Backward compat verified — `enable_citation_post_hoc_expansion=False` short-circuit inside `expand_citations` first 3 lines returns inputs unchanged(test `test_disabled_flag_returns_inputs_unchanged` PASS)

### F1.5 Unit tests + non-regression coverage

- [x] F1.5.a `test_prompt_builder_dispatch.py` +3 NEW tests — Rule 7 v2 + Rule 8 + Rule 6 non-regression PASS
- [x] F1.5.b `test_citation_expansion.py` 15 NEW tests PASS(see F1.2.d)
- [x] F1.5.c `test_synthesizer.py` +2 NEW tests — citation expansion wire enabled when not refused + skipped when refused PASS
- [x] F1.5.d backend pytest **1080 passed + 25 skipped + 0 failed**(W30 baseline 1060 → **+20 NEW W31** = exact)+ no existing test regression
- [x] F1.5.e ruff PASS(2 errors auto-fixed via `--fix`:unused pytest import in test file + import organization);mypy strict module-path quirk pre-existing per CO_W25_mypy_strict_debt(13 errors in other modules,`citation_expansion.py` 自身 W31 NEW module clean per --follow-imports=silent isolated check)

### F1 commit + progress.md Day 1

- [ ] F1.6 Commit `feat(generation): W31 F1 multi-axis prompt + post-hoc citation expansion(B'.b + B'.c + Rule 7 v2) + 20 NEW unit tests` per CLAUDE.md R2 daily commit binding
- [ ] F1.7 progress.md Day 1 entry — implementation summary + test verdict + ruff/mypy state + commit hash backfill

## F2 — 5-run reproducibility verify Q-W25-I07 + Q-W25-I01 control(D2 estimate)

- [ ] F2.1 Backend reload via `touch backend/generation/prompt_builder.py` + WatchFiles trigger + /health=ok verify
- [ ] F2.2 curl POST /query Q-W25-I07「show me all the Integration scenarios」5 runs back-to-back — per-run JSON in `backend/w31-f2-i07-multi-run-{1-5}.json`
- [ ] F2.3 curl POST /query Q-W25-I01「what is the high level architecture」5 runs back-to-back(control)— per-run JSON `backend/w31-f2-i01-multi-run-{1-5}.json`
- [ ] F2.4 Aggregate report `f2-5run-multi-axis-W31-D2-raw.txt` — Q-I07 walkthrough cite rate / Q-I07 citations count / Q-I01 no regression check / G1-G6 verdict
- [ ] F2.5 progress.md Day 2 F2 entry — 5-run table + W30+W29 baseline comparison + G1 verdict draft

## F3 — Manual user-test 3-query cohort(D2 estimate;same-day as F2)

- [ ] F3.1 Q-W25-I07「show me all the Integration scenarios」— expected ≥ 2 distinct §8.x walkthrough cited(target G1)
- [ ] F3.2 Q-W25-I01「what is the high level architecture」— expected control no regression(faithfulness within F1 baseline 0.9851 ±2pp)
- [ ] F3.3 NEW Q-W31-I08 enumeration / aggregate variant query selected by user OR Chris OR phase author
- [ ] F3.4 Visual citation render check `<CitationPill>` no overflow when citations > 5
- [ ] F3.5 progress.md Day 2 F3 entry — user-test cohort verdict + Q-W31-I08 selection rationale + visual rendering check note

## F4 — Phase Gate G1-G6 evaluation + decision policy

### A. Phase Gate G1-G6 evaluation

- [ ] G1 PRIMARY 5-run walkthrough_cite_rate vs W29+W30 20% baseline
  - G1 strict (≥ 2 distinct walkthrough cited in ≥ 1 run)
  - G1 relaxed (≥ 1 walkthrough cited per run for ≥ 3/5)
  - G1 marginal (>40% improvement vs W29+W30 baseline,target 5-run ≥ 60%)
- [ ] G2 control Q-W25-I01 no regression(faithfulness within F1 baseline 0.9851 ±2pp)
- [ ] G3 backend pytest baseline preserved 1060 → ~1070-1075
- [ ] G4 ruff PASS;mypy strict module-path quirk pre-existing per CO_W25_mypy_strict_debt
- [ ] G5 NEW unit tests PASS — F1.5.a + F1.5.b + F1.5.c
- [ ] G6 measurement-experiment-fail-policy applied per Q4 — G1 fully FAIL → revert per Karpathy §1.3 + plan §3 G1 decision matrix

### B. Cross-doc sync per CLAUDE.md §10 R3 + R5 + R6

- [ ] plan.md frontmatter `status: active → closed` OR `closed_partial` per G1 verdict
- [ ] checklist.md cross-cutting tick + N/A reason
- [ ] progress.md retro 7-section
- [ ] session-start.md §10 W31 row `🟡 active` → `✅ closed` OR `closed_partial`
- [ ] session-start.md §11 W31 CLOSED block prepend
- [ ] RISK_REGISTER NEW R16 candidate evaluate(over-citation noise risk if multi-axis G1 PASS but G2 regression)
- [ ] COMPONENT_CATALOG C05 status note update if Settings default flipped
- [ ] ADR README — no NEW ADR expected per §2 F5.7

### C. `.env` cleanup + W32+ priority queue evaluation

- [ ] `.env` cleanup — W29 Setting tune `overfetch=8 + rrf_k=30` env override PRESERVED unchanged
- [ ] W32+ candidate prioritization update per F4 outcome — (B'.a) Settings threshold pre-pend / (ii) CRAG threshold trial / (k) wire reformulator into eval/orchestrator.py / NEW W32+ axis tune based on F2+F3 evidence

### D. Commit + push

- [ ] F5 closeout commit — combined with F4 evidence(per W30 closeout pattern)
- [ ] Push origin/main(per explicit user instruction)

---

## Cross-Cutting

- [ ] All deliverables committed to git(F0.6 kickoff commit + F1.6 F1 commit + F4+F5 closeout commit)
- [ ] All OQ status changes reflected in `docs/decision-form.md` — no OQ resolved expected(pure C05 prompt + module iteration)
- [ ] All architectural-adjacent decisions documented as ADR — F1.1 Rule 7 v2 + Rule 8 prompt iteration within framework + F1.2 citation_expansion module parallel pattern(non-architectural per plan §1 scope decl)
- [ ] `progress.md` retro section written — 7-section per closeout commit
- [ ] `progress.md` frontmatter status flipped to `closed` OR `closed_partial`
- [ ] Phase W32+ kickoff trigger noted in retro — candidates list update per F4 outcome

---

**Lifecycle reminder**:呢份 checklist 隨 plan deliverables 衍生。新加 deliverable 必須先入 plan + changelog,然後再加 checklist item。
