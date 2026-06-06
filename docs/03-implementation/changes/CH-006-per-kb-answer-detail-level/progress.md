---
change_id: CH-006
spec_ref: ./spec.md
checklist_ref: ./checklist.md
status: in-progress     # in-progress | closed
---

# CH-006 — Progress

> Day-N entries + closeout。每 commit 對應 Day-N mention(R2)。

---

## Day 1 — 2026-06-06

### Context
W56 後續 live 診斷(KB `w56-drive-ab-1`):procedural 問題(GL03 post journal)recall 已完整(parent_doc → 14/14 chunks),但 chat 答案仍係 6 步摘要。Scratch 證實根因 = synthesis prompt Rule 3「target <= 150 words」cap;放寬 → gpt-5.5 即吐完整逐 sub-step。用戶揀 per-KB「答案詳細度」config 路線。spec draft→approved(Chris chat「Approve」)。

### Done
- (kickoff)spec.md status draft → **approved**(Chris)+ checklist + progress committed(R1.change 滿足)。
- (pending implementation I1-I8 / T1-T4 / V1-V3)

### Decisions
- 預設 `concise` = 現行 prompt 逐字不變 → **零 regression**;`detailed` opt-in per-KB。
- 保留 `SYSTEM_PROMPT` 別名 = concise variant → 唔破現有 import/test。
- `default_rerank_k` → chat wiring gap **明確另案**(唔混入本 CH)。

### Blockers
- 無。

### Effort
- Planned:~0.5–1 day;Actual:_(填)_;Variance:_

### Commits
| Hash | Subject |
|---|---|
| _(待)_ | docs(change): CH-006 kickoff |

---

## Closeout（填於 status=closed）

_(待實作完成填)_

---

**End of CH-006 progress**
