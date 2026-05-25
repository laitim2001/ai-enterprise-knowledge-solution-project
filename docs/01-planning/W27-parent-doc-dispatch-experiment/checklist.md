---
phase: W27-parent-doc-dispatch-experiment
plan_ref: ./plan.md
status: in-progress
last_updated: 2026-05-25
---

# Phase W27 — Checklist

> Atomic checkbox(每 item ≤ 1–2 hour effort)。
> AI tick 完成嘅 item;唔可以 tick 嘅 item 喺 progress Day-N entry 寫原因 + 標 🚧 reason。

## F0 — Kickoff(plan + checklist + progress + R6 grep verify)

- [x] Create `docs/01-planning/W27-parent-doc-dispatch-experiment/` folder
- [x] R6 pre-active-flip recursive grep verify(per CLAUDE.md §10 R6)— ADR-0037 §229 wording vs `backend/generation/prompt_builder.py:55-59` 對齊 verified;5 R6 findings 記 `plan.md` §7 Plan Changelog Day 0 entry
- [x] Draft `plan.md` per W26 closed-phase template — 7-section structure + frontmatter + §2 F0-F3 deliverables + §3 G1-G6 + §4 R1-R5 + §5 D0-D3 + §6 W26 carry-overs + §7 Changelog
- [x] Draft `checklist.md` per W26 closed-phase template — atomic items derived from plan §2 deliverables
- [x] Draft `progress.md` Day 0 entry — kickoff action + commit hash placeholder
- [x] Commit `docs(planning): kickoff W27-parent-doc-dispatch-experiment` per CLAUDE.md §10 R1 binding before any code(commit `5a6aab5`)
- [x] session-start.md §10 timeline row update — W27 active status entry append + W28+ rolling JIT row
- [N/A] session-start.md §11 W27 active context section append — per W26 active precedent §11 是 CLOSED block 累積區,active state 唔 prepend 新 block(等 W27 closeout 才 prepend per session-start.md §11 pattern)

## F1 — Implementation:Setting + prompt_builder branch + unit tests

### A. Setting addition

- [ ] `backend/storage/settings.py` NEW field `parent_doc_dispatch_mode: Literal["replace", "append"] = "replace"` — default preserves W26 F2 G semantics per Q4 measurement-experiment-fail-policy

### B. Prompt builder dispatch branching

- [ ] F1 D1 R6 sub-verify before active flip — render strategy ambiguity resolution(Option (i) single chunk header + `Parent section context:` delimiter sub-section per Karpathy §1.2 simplicity defaulting vs Option (ii) 2 chunk entries — read existing 7 W26 dispatch tests + lock pick)
- [ ] `backend/generation/prompt_builder.py` `_format_chunk` 函數 branch on `Settings.parent_doc_dispatch_mode`:
  - `"replace"` branch — preserve current line 55-59 `or` chain semantics(W26 F2 G behavioral parity / regression-guard)
  - `"append"` branch — render 2-segment format(anchor `chunk_text` 主段 + delimiter + parent section context 段)
- [ ] Citation invariant preservation verified — `Citation.chunk_text = original_chunk.chunk_text` 兩 branch 都 unchanged per architecture.md §3.5

### C. Tests

- [ ] `backend/tests/test_prompt_builder_dispatch.py` NEW unit test 1:`test_format_chunk_dispatch_replace_mode_preserves_w26_semantics`(replace branch = current behavior;regression-guard against W26 F2 G existing 7 dispatch tests)
- [ ] `backend/tests/test_prompt_builder_dispatch.py` NEW unit test 2:`test_format_chunk_dispatch_append_mode_includes_both_segments`(LLM input contains BOTH `chunk_text` raw + parent section context delimiter)
- [ ] `backend/tests/test_prompt_builder_dispatch.py` NEW unit test 3:`test_format_chunk_dispatch_append_mode_no_parent_section_falls_back_to_replace_chain`(append + 無 `parent_section_text` field → behave as replace chain `expanded_text > chunk_text`)
- [ ] (Optional)`backend/tests/test_prompt_builder_dispatch.py` NEW unit test 4:`test_format_chunk_dispatch_append_mode_citation_chunk_id_preserved`(citation invariant explicit verification)
- [ ] Existing 7 W26 F2 dispatch tests `test_prompt_builder_dispatch.py` 全部 pass(regression-guard,W26 baseline preservation)

### D. Code quality gates

- [ ] mypy strict delta 0 — touched files only(W26 baseline 13 errors pre-existing `CO_W25_mypy_strict_debt` 維持)
- [ ] ruff check + ruff format clean delta 0
- [ ] backend pytest full run regression 0 — W26 baseline 1056 → ≥ 1059 W27 F1(3 NEW tests minimum)

### E. Observability(optional minor)

- [ ] (Optional)`backend/observability/observe.py` `generation.parent_doc_retrieval` stage emit + `dispatch_mode` field(append / replace)— skip 若 W26 F2 stage 已存在 evidence

### F. Commit

- [ ] Commit F1 implementation `feat(generation): W27 F1 dispatch mode enum + append branch + N NEW unit tests per ADR-0037 amendment candidate`

## F2 — G RAGAs delta vs F1(W26 D1)+ W26 F2 G(replace)baselines

### A. R8 prerequisite gate

- [ ] R8 prerequisite check — Azure OpenAI judge key + Cohere v4.0-pro reranker key available in dev / personal Azure tier per ADR-0017 Plan B (c)
- [ ] STOP and ask Chris 若 blocked(per W25 F4 / W26 F1 deferred precedent pattern)— F2/F3 deferred caveat trigger PARTIAL closeout

### B. Both-baseline eval execution

- [ ] Settings runtime override `parent_doc_dispatch_mode="append"` + `enable_parent_doc_retrieval=true`
- [ ] Append mode run `eval-set-v0-w25-supplement.yaml` 13 queries via `/eval/run`
- [ ] Per-query 4-metric output:faithfulness / answer_relevancy / context_precision / context_recall
- [ ] Aggregated mean computation

### C. Hard gate G1-G4 evaluation

- [ ] G1 evaluation:append mode aggregate faithfulness 回升至 F1 baseline ±2pp(0.9651 ≤ x ≤ 1.0)
- [ ] G2 evaluation:append mode aggregate correctness 回升至 F1 baseline ±2pp(0.7216 ≤ x ≤ 0.7616)
- [ ] G3 evaluation:Q-W25-I07 faithfulness > 0.5(W26 F2 G replace 0.00 → append > 0.5 minimum bar)
- [ ] G4 evaluation:Q-W25-I01 控制組 answer_relevancy ≥ F1 baseline ± 0.05

### D. Documentation

- [ ] `docs/01-planning/W27-parent-doc-dispatch-experiment/append-mode-metrics-W27-D{N}.md` — per-query 4-metric + aggregated table + plain-text interpretation三方對比(F1 baseline vs W26 F2 G replace vs W27 F2 append)
- [ ] `docs/01-planning/W27-parent-doc-dispatch-experiment/append-mode-metrics-W27-D{N}-raw.json` — raw eval payload per W26 D5 precedent

### E. Commit

- [ ] Commit F2 G eval `docs(eval): W27 F2 G RAGAs append mode delta vs F1 + W26 F2 G baselines`

## F3 — Closeout — ADR amendment OR ADR-0038 + cross-doc sync

### A. ADR governance per G result

- [ ] G result determination — G3 + G4 雙 PASS OR 任一 FAIL?
- [ ] **若 PASS** → ADR-0037 amendment per ADR-0017 5-amendment precedent:
  - [ ] Status「Accepted」→「Accepted; amended 2026-05-25 W27 F3 per dispatch chain append-vs-replace experiment」
  - [ ] NEW "Amendment 2026-05-25 W27 F3 — append dispatch chain" section
  - [ ] §6.4 Q-NEW append-vs-replace decision documented
  - [ ] `parent_doc_dispatch_mode` default flip "replace" → "append" — Settings 改值 + tests update
- [ ] **若 FAIL** → NEW ADR-0038 ship:
  - [ ] `docs/adr/0038-parent-doc-dispatch-append-mode-no-improvement.md` — Accepted status documents finding + W27+ candidates (b) Setting sweep + (c) RAGAs orchestrator-aware tune elevated as W28+ priority
  - [ ] `docs/adr/README.md` index sync(row + footer next-NNNN 0038→0039)

### B. Cross-doc sync per CLAUDE.md §10 R3 + R5 + R6

- [ ] plan.md frontmatter `status: draft → closed`(若 PASS)OR `closed_partial`(若 FAIL — measurement-experiment-fail-policy applicable per W26 PARTIAL precedent)
- [ ] checklist.md cross-cutting 全 tick + 標明 deferred items per 🚧 reason
- [ ] progress.md retro 7-section + Phase Gate G1-G6 result + What worked / What didn't / Surprises / Carry-overs to W28+ / ADR triggers
- [ ] session-start.md §10 timeline row update(W27 closed / closed_partial status)
- [ ] session-start.md §11 W27 CLOSED block prepend(若 PASS)OR W27 PARTIAL closed_partial block prepend(若 FAIL — per W26 PARTIAL precedent)
- [ ] RISK_REGISTER R-W26-1 update — status flip per result(Mitigated 若 PASS / Confirmed-hypothesis-rejected 若 FAIL — W27+ candidates (b) + (c) elevated)
- [ ] COMPONENT_CATALOG.md C05 status note 1-line append:「W27 F3 dispatch_mode `replace|append` enum landed;default per G result」

### C. Measurement-experiment-fail-policy applicable per Q4

- [ ] 若 G result FAIL → Settings default preserve "replace" + `enable_parent_doc_retrieval=False` 唔觸 revert per Karpathy §1.3 surgical(同 W26 F2 G FAIL precedent)
- [ ] 若 G result PASS → Settings default flip "replace" → "append" via ADR-0037 amendment per ADR-0017 5-amendment precedent

### D. Commit

- [ ] Commit F3 closeout `docs(planning): W27 closeout {PASS|PARTIAL} — F2 G append mode {success|failure} + ADR-0037 {amendment|0038 supersede} + cross-doc sync`

---

## Cross-Cutting

- [ ] All deliverables committed to git
- [ ] All OQ status changes reflected in `docs/decision-form.md`(若 任何 OQ resolved this phase — 預期無)
- [ ] All architectural-adjacent decisions documented as ADR(per CLAUDE.md §5.1 H1)— ADR-0037 amendment OR ADR-0038
- [ ] `progress.md` retro section written
- [ ] `progress.md` frontmatter status flipped to `closed` OR `closed_partial`
- [ ] Phase W28+ kickoff trigger noted in retro

---

**Lifecycle reminder**:呢份 checklist 隨 plan deliverables 衍生。新加 deliverable 必須先入 plan + changelog,然後再加 checklist item。
