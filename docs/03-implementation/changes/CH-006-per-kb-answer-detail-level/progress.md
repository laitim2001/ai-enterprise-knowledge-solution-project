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
- **Backend I1-I6 + T1-T3 完成**:Settings 全域預設 + KbConfig.answer_detail + EffectiveConfig resolve + prompt_builder concise/detailed 雙變體(`.replace()` 派生)+ synthesizer detail_level + query.py 兩路 + CRAG re-synth wiring。**14 個 CH-006 test 全綠**;52 個相關 test 通過。
- (pending I7-I8 frontend / T4 / V1-V3)

### Decisions
- 預設 `concise` = 現行 prompt 逐字不變 → **零 regression**;`detailed` opt-in per-KB。
- **prompt_builder 重構策略**:rename 變數(body 不郁)+ `.replace()` 派生 detailed(只換 Rule 3)→ 零 rule 重複、零 drift、concise 保證 byte-identical(Karpathy §1.3 最 surgical)。
- 保留 `SYSTEM_PROMPT` 別名 = concise → 唔破現有 import/test(CH-005 substring 斷言全過)。
- I2 scope 收窄:config_test DraftRetrievalConfig **不加** answer_detail（synthesis knob 非 retrieval;config-test panel 仍用 KB saved/global = concise）。
- CRAG re-synth 一併 thread detail_level(一致性)。
- `default_rerank_k` → chat wiring gap **明確另案**(唔混入本 CH)。

### Notes (pre-existing, 非 CH-006)
- `test_synthesizer.py::test_synthesize_invokes_engine_fetch_expansion...` 喺 **clean checkout(git stash 驗)一樣 fail** → pre-existing citation-expansion 失敗,**唔關 CH-006**;按 Karpathy §1.3 唔喺本 CH 修(另案)。
- `effective_config.py` 喺 HEAD 已 format-dirty(`max_images_per_answer` block)→ pre-existing debt,唔郁(我加嘅 block 已 format-clean)。
- mypy:我改 3 檔零 error;6 個 error 喺其他模組(langfuse/observe/retrieval_engine)= pre-existing baseline。

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
