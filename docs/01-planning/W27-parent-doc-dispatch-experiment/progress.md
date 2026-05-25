---
phase: W27-parent-doc-dispatch-experiment
plan_ref: ./plan.md
checklist_ref: ./checklist.md
status: in-progress
---

# Phase W27 — Progress

> Daily progress + 結尾 retro。
> 每 commit 必須對應一個 Day-N entry mention(R2 binding rule per PROCESS.md §5)。

---

## Day 0 — 2026-05-25:Kickoff

**Action**:Phase W27 kickoff post W26 PARTIAL closeout
- Templates copied from `_templates/phase/` + W26 closed-phase conventions referenced(per CLAUDE.md §10.2「起草新 plan/checklist 必先讀『最近一個 closed phase』樣板」)
- `plan.md` drafted with 7-section structure + frontmatter `status: draft` + §2 F0-F3 deliverables + §3 G1-G6 + §4 R1-R5 + §5 D0-D3 + §6 W26 carry-overs + §7 Changelog
- `checklist.md` derived from plan §2 deliverables(atomic items;F0 kickoff partially ticked + F1-F3 pending)
- `progress.md` Day 0 entry(本 entry)
- Chris 3-question AskUserQuestion approval pick(2026-05-25):
  - Q1 phase 命名 = `W27-parent-doc-dispatch-experiment`(Recommended)
  - Q2 Setting 設計 = Enum `parent_doc_dispatch_mode` "replace"|"append"(Recommended)
  - Q3 G eval baseline = Both(F1 W26 D1 no-parent-doc + W26 F2 G replace mode)(Recommended)
- Trigger memo:W26 closeout retro `Next phase candidates` 候選 (a) Dispatch chain append-vs-replace 實驗 — R-W26-1 — 最直接解 RAGAs judge mismatch

**F0 R6 Pre-Active-Flip 5-Step Recursive Grep Verification**(per CLAUDE.md §10 R6):

執行重點:`prompt_builder.py` dispatch chain 同 ADR-0037 §229 wording 對齊 verified,W22 D9 plan-text-contamination 防範。

| R6 step | Action | Finding |
|---|---|---|
| Step 1 | Read plan literal acceptance criteria | F1 acceptance §A-§E + render strategy ambiguity surfaced |
| Step 2 | Grep code base for referenced files / functions / patterns | `backend/generation/prompt_builder.py:55-59` `or` chain — `chunk.fields.get("parent_section_text") or chunk.fields.get("expanded_text") or chunk.fields.get("chunk_text", "")` confirmed replace semantics(top-priority-wins);ADR-0037 §229 wording「dispatch chain `parent_section_text > expanded_text > chunk_text`」consistent |
| Step 3 | Surface mismatches via Karpathy §1.1 think-before-coding upfront | 2 NEW findings:(a) 規模 estimate ~50 LOC adjust upward ~80-120 LOC reflecting conditional rendering + ≥ 3 NEW unit tests + optional observability emit;(b) render strategy ambiguity F1 D1 R6 sub-verify before active flip(Option (i) single chunk header + delimiter sub-section vs Option (ii) 2 chunk entries)|
| Step 4 | Document deviations in plan §7 changelog at plan kickoff | `plan.md` §7 Plan Changelog Day 0 entry 2026-05-25 documented 2 findings + Option (i) Karpathy §1.2 simplicity defaulting |
| Step 5 | Adjust acceptance criteria per actual reality | F1 §B.2 acceptance 加 R6 sub-verify pre-active-flip + Option (i) defaulting;F1 §C.1-§C.4 ≥ 3 NEW unit tests + (optional) 4th citation invariant test(對應 規模 estimate) |

**R6 result**:0 historical surface contamination(per W22 D9 anti-pattern prevention);experiment-scoped wording grounded in W26 retro empirical finding;regime alignment confirmed。

**Carry-over from W26 retro**:
- R-W26-1 Dispatch chain append-vs-replace experiment(本 phase 直接 address)
- R-W26-2 RAGAs faithfulness judge orchestrator-aware tune(本 phase F2 G result FAIL → W28+ candidate (c) elevated)
- W26 F1 baseline `baseline-metrics-W26-D1.md` + W26 F2 G replace `parent-doc-metrics-W26-D5.md` 作 F2 G baseline references
- W26 F2 existing 7 dispatch tests `test_prompt_builder_dispatch.py`(F1 regression-guard)
- ADR-0037 §229 dispatch chain wording + `prompt_builder.py:55-59` 實作對齊(F0 R6 verified)

**Commit**:`5a6aab5` — `docs(planning): kickoff W27-parent-doc-dispatch-experiment`(4 files / +541 / -1 — plan.md + checklist.md + progress.md + session-start.md §10 timeline row append)

---

## Day 1 — 2026-05-25(planned)

### Done

- (pending — F1 implementation:Setting + prompt_builder branch + ≥ 3 unit tests)

### Decisions / OQ Resolved

- (pending)

### Blockers

- (pending — R8 prerequisite check at F2 D2 may surface here if Azure/Cohere key env not available)

### Actual vs Planned Effort

| Deliverable | Planned (h) | Actual (h) | Variance |
|---|---|---|---|

### Commits

- (pending)

---

## Day 2 — 2026-05-25(planned)

### Done

- (pending — F2 G RAGAs eval delta vs F1 + W26 F2 G baselines;R8 prerequisite gate)

### Decisions / OQ Resolved

- (pending)

### Blockers

- (pending — R8 partial → STOP and ask Chris per W25 F4 / W26 F1 precedent)

### Actual vs Planned Effort

| Deliverable | Planned (h) | Actual (h) | Variance |
|---|---|---|---|

### Commits

- (pending)

---

## Day 3 — 2026-05-25(planned)

### Done

- (pending — F3 closeout + ADR amendment OR ADR-0038 + cross-doc sync)

### Decisions / OQ Resolved

- (pending)

### Blockers

- (pending)

### Actual vs Planned Effort

| Deliverable | Planned (h) | Actual (h) | Variance |
|---|---|---|---|

### Commits

- (pending)

---

## Retro(填於 phase 結束)

### What worked

- (pending)

### What didn't work / unexpected friction

- (pending)

### Surprises / discoveries

- (pending)

### Carry-overs to W28+

- (pending)

### ADR triggers

- (pending — ADR-0037 amendment OR ADR-0038 new ship per G result)

### Phase Gate result

- G1:(pending — append mode aggregate faithfulness vs F1 baseline ±2pp)
- G2:(pending — append mode aggregate correctness vs F1 baseline ±2pp)
- G3:(pending — Q-W25-I07 faithfulness > 0.5)
- G4:(pending — Q-W25-I01 控制組不再 regression)
- G5:(pending — pytest delta + code gates green)
- G6:(automatic — measurement-experiment-fail-policy applied per Q4)

### Phase status

- Closeout commit:(pending)
- Frontmatter status flipped to:(pending — `closed` 若 PASS / `closed_partial` 若 FAIL)
- Phase W28+ kickoff trigger:(pending — depends on G result + Chris pick on next candidate)

---

**End of W27 progress**
