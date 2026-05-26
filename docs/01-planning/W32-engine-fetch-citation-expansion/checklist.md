---
phase: W32-engine-fetch-citation-expansion
plan_ref: ./plan.md
status: active
last_updated: 2026-05-26
---

# Phase W32 — Checklist

> Atomic checkbox(每 item ≤ 1-2 hour effort)。

## F0 — Kickoff(plan + checklist + progress + R6 grep verify + session-start sync)

- [x] F0.1 Create `docs/01-planning/W32-engine-fetch-citation-expansion/` folder
- [x] F0.2 R6 Day 0 recursive grep verify — `prompt_builder.py` Rule 1-6 only(W31 Rule 7+8 REVERTED per `09805d6`)+ `synthesizer.py` NO expand_citations import/wire(W31 reverted)+ `Settings.py` NO citation_expansion_* fields(W31 reverted)+ `citation_image_neighbors.py` W25 F5 D1 attach_neighbour_images reference pattern verified at line 41-132 + `retrieval_engine.py:258` `list_chunks(kb_id, doc_id, top=1000)` API verified → **no shipped-pattern conflict for engine-fetch B'.c path 3**
- [x] F0.3 Draft `plan.md` 7-section per W30+W31 closed-phase template
- [x] F0.4 Draft `checklist.md` atomic items derived from plan §2 deliverables(this file)
- [x] F0.5 Draft `progress.md` Day 0 entry — kickoff action + R6 catch report + W31 lessons applied(PC-W31-1/2/3)
- [x] F0.6 Commit kickoff `8628fbb` — `docs(planning): kickoff W32-engine-fetch-citation-expansion + (h') single-axis ship per W31 multi-axis lesson + R6 Day 0 net 0 contamination`
- [ ] F0.7 session-start.md §10 W32 row append `🟡 active 2026-05-26` + W33+ rolling JIT row defer + W31 row 維持 closed_partial

## F1 — Implementation(D1 estimate)

### F1.1 Synthesizer wire signature change(`backend/generation/synthesizer.py`)

- [ ] F1.1.a `Synthesizer.synthesize(query, chunks)` → `Synthesizer.synthesize(query, chunks, *, engine=None, kb_id=None)` keyword-only optional params
- [ ] F1.1.b `Synthesizer.synthesize_stream(query, chunks)` → same kwarg additions
- [ ] F1.1.c Caller site update — `backend/api/routes/query.py`(or `pipeline/query_pipeline.py`)passes `engine + kb_id` from existing pipeline state
- [ ] F1.1.d Backward compat:if `engine is None or kb_id is None` → skip expansion(W25 F5 D1 attach_neighbour_images pattern at line 61-62 same defensive return)

### F1.2 Backend layer NEW async module(`backend/generation/citation_expansion.py`)

- [ ] F1.2.a `async def expand_citations(answer_text, citation_ids, chunks, *, engine, kb_id, settings) → (expanded_text, expanded_citation_ids)` async signature
- [ ] F1.2.b Algorithm:group cited chunks by doc_id → parallel `asyncio.gather` `engine.list_chunks(kb_id, doc_id)` → per-doc find ±window neighbors with §X.M title regex + max_aux cap closer-preferred
- [ ] F1.2.c Auto-insert `[chunk-{neighbor_id}]` markers after existing(preserve W31 F1.2.c pattern)+ dedupe + per-doc batch fetch
- [ ] F1.2.d Defensive:per-doc fetch exception → log warning + skip that doc's expansion(W25 F5 D1 line 86-92 graceful degradation pattern)
- [ ] F1.2.e `_find_neighbour_chunks` private pure helper testable without engine(parallel W25 F5 D1 `_find_neighbour_images`)

### F1.3 Settings NEW knobs(`backend/storage/settings.py`)

- [ ] F1.3.a `enable_citation_post_hoc_expansion: bool = True` — W32 default ON per Karpathy §1.4 goal-driven measurement
- [ ] F1.3.b `citation_expansion_window: int = 10` — W31 F2 v3 evidence corpus §X.1-§X.5 within ±10 of intro idx 44(escapes W31 window=3 constraint)
- [ ] F1.3.c `citation_expansion_max_aux: int = 2` — parallel W25 F5 D1 + W31 reverted convention
- [ ] F1.3.d **NO** `citation_expansion_score_threshold` — `list_chunks` returns raw chunks without rerank score per W31 PC-W31-2 lesson

### F1.4 Caller wire update(`backend/api/routes/query.py` OR `pipeline/query_pipeline.py`)

- [ ] F1.4.a Locate Synthesizer caller — pass `engine + kb_id` through pipeline state(already available since `RetrievalEngine.retrieve(kb_id=...)` called earlier)
- [ ] F1.4.b Backward compat:legacy callers / tests without engine → expand_citations no-op gracefully

### F1.5 Unit tests + non-regression coverage

- [ ] F1.5.a NEW `backend/tests/test_citation_expansion.py` async unit tests — disabled flag / empty inputs / happy path / corpus bare X.M pattern / window boundary / max_aux cap / dedupe / same doc constraint / cited-not-in-chunks defensive / per-doc fetch exception graceful / `_find_neighbour_chunks` pure unit;12+ NEW tests target
- [ ] F1.5.b `test_synthesizer.py` +2 NEW async tests — synthesize wires expand_citations with engine + kb_id / skips when refused
- [ ] F1.5.c backend pytest baseline 1060 → expected ~1072-1075 post-W32 F1
- [ ] F1.5.d ruff PASS on touched files
- [ ] F1.5.e mypy strict citation_expansion.py clean(pre-existing W26 baseline module-path quirk per CO_W25_mypy_strict_debt unchanged)

### F1 commit + progress.md Day 1

- [ ] F1.6 Commit `feat(generation): W32 F1 engine-fetch citation expansion + async list_chunks per W31 (h') candidate + 12+ NEW unit tests` per CLAUDE.md R2 daily commit binding
- [ ] F1.7 progress.md Day 1 entry — implementation summary + test verdict + ruff/mypy state + commit hash backfill

## F2 — 5-run reproducibility verify Q-W25-I07 + Q-W25-I01 control(D2 estimate)

- [ ] F2.1 Backend reload via `touch backend/generation/citation_expansion.py` + WatchFiles trigger + /health=ok verify
- [ ] F2.2 curl POST /query Q-W25-I07「show me all the Integration scenarios」5 runs back-to-back — per-run JSON in `backend/w32-f2-i07-multi-run-{1-5}.json`
- [ ] F2.3 curl POST /query Q-W25-I01「what is the high level architecture」5 runs back-to-back(control)— per-run JSON `backend/w32-f2-i01-multi-run-{1-5}.json`
- [ ] F2.4 Aggregate report inline progress.md F2 — Q-I07 walkthrough cite rate vs W29+W30+W31 baselines / Q-I01 G2 no regression check / G1-G6 verdict draft
- [ ] F2.5 progress.md Day 2 F2 entry — 5-run table + cumulative baseline comparison + expansion fired count + G1 verdict draft

## F3 — Closeout — Phase Gate + cross-doc sync + commit + push

### A. Phase Gate G1-G6 evaluation

- [ ] G1 PRIMARY 5-run walkthrough_cite_rate vs W31 v3 baseline 20%
  - G1 strict (≥ 2 distinct walkthrough cited in ≥ 1 run)
  - G1 relaxed (≥ 1 walkthrough cited per run for ≥ 3/5)
  - G1 marginal (>40pp improvement vs W31 v3 baseline,target 5-run ≥ 60%)
- [ ] G2 control Q-W25-I01 no regression(refusals 0/5 + avg_cit ≥ 1.5 + faithfulness within W31 v3 baseline)
- [ ] G3 backend pytest baseline preserved 1060 → ~1072-1075
- [ ] G4 ruff PASS;mypy strict module-path quirk pre-existing per CO_W25_mypy_strict_debt
- [ ] G5 NEW unit tests PASS — F1.5.a + F1.5.b
- [ ] G6 measurement-experiment-fail-policy applied per Q4 — G1 fully FAIL → revert per Karpathy §1.3 + W30+W31 precedent

### B. Cross-doc sync per CLAUDE.md §10 R3 + R5 + R6

- [ ] plan.md frontmatter `status: active → closed` OR `closed_partial` per G1 verdict
- [ ] checklist.md cross-cutting tick + N/A reason
- [ ] progress.md retro 7-section
- [ ] session-start.md §10 W32 row `🟡 active` → `✅ closed` OR `closed_partial`
- [ ] session-start.md §11 W32 CLOSED block prepend
- [ ] RISK_REGISTER NEW R candidate evaluate(over-citation noise risk if (h') G1 PASS but G2 regression)
- [ ] COMPONENT_CATALOG C05 status note update if Settings default ON ship
- [ ] ADR README — no NEW ADR expected per §2(parallel pattern to W25 F5 D1 non-architectural)

### C. `.env` cleanup + W33+ priority queue evaluation

- [ ] `.env` cleanup — W29 Setting tune `overfetch=8 + rrf_k=30` env override PRESERVED unchanged
- [ ] W33+ candidate prioritization update per F3 outcome — (g') 20-run sample methodology / (i') reformulator deterministic temp=0 / Rule 7 v2 + Rule 8 restoration / (B'.a) / (ii) CRAG / (k) eval-wire / etc.

### D. Commit + push

- [ ] F3 closeout commit — combined with F2 evidence(per W31 closeout pattern;module + Settings + wire + tests + retro + cross-doc sync atomic)
- [ ] Push origin/main(per explicit user instruction)

---

## Cross-Cutting

- [ ] All deliverables committed to git(F0.6 kickoff commit + F1.6 F1 commit + F3 closeout commit)
- [ ] All OQ status changes reflected in `docs/decision-form.md` — no OQ resolved expected(pure C05 backend module iteration)
- [ ] All architectural-adjacent decisions documented as ADR — F1.2 citation_expansion async module parallel pattern to W25 F5 D1(non-architectural per plan §1 scope decl)
- [ ] `progress.md` retro section written — 7-section per closeout commit
- [ ] `progress.md` frontmatter status flipped to `closed` OR `closed_partial`
- [ ] Phase W33+ kickoff trigger noted in retro — candidates list update per F3 outcome

---

**Lifecycle reminder**:呢份 checklist 隨 plan deliverables 衍生。新加 deliverable 必須先入 plan + changelog,然後再加 checklist item。
