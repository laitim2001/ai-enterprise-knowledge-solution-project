---
bug_id: BUG-036
report_ref: ./report.md
checklist_ref: ./checklist.md
status: investigating     # investigating | closed
---

# BUG-036 — Progress

> Day-N entries + closeout。Sev2 → postmortem mandatory。

---

## Day 1 — 2026-06-08

### Done
- 用戶 chat 測試揭文字答案 regression（CH-011 re-index 後）→ triage Sev2 → 開 BUG-036
- 診斷捕捉（report §6）：唯一變數 = re-index 首次套 CH-008 contextual embedding；13 cites = 4 reranked + 9 expansion；detailed synthesizer 列整段 → synthetic 重編號 + 重複行
- repro 確認（API 2 run 穩定 CAR×2）

### Decisions
- 用戶揀「開 Bug-fix 正式診斷+修」（over 即時 config 緩解 / contextual toggle+re-index）
- Sev2（核心 chat surface 品質 regression + 明確 defect + 用戶 flag 嚴重）→ postmortem mandatory
- branch `fix/chat-reindex-text-answer-regression`（off main）

- I4 **root cause = source-inherent 冗餘 heading**（讀 §3.1.4 chunk 原文確認）+ `_RULE_3_DETAILED` 「do NOT merge」令 LLM 忠實列
- I5 用戶揀 **A（synthesis dedup prompt）**
- **Fix**：改 `_RULE_3_DETAILED`（distinct-step dedup + summary-table fold，移除 "merge"）+ regression test；40 prompt test + 新 test 綠;ruff/format clean
- **Verify（backend，新 prompt）**：§GL03-2「Confirm Approval Request ×3 / Approve General Journal ×2」→ **每 step 一次**；完整性保留；CH-011 圖片不受影響;答案 leaner
- Postmortem 寫好（Sev2 mandatory）

### Blockers
- 無（fix backend-verified；待 V3 用戶 live 驗 + postmortem sign-off）

### Commits
| Hash | Subject |
|---|---|
| `f...`（triage）| docs(bug): BUG-036 triage Sev2 |
| _(this commit)_ | fix(generation): BUG-036 detailed-synth dedup repeated source headings |

---

## Closeout（填於 status=closed）
_(待)_

---

**End of BUG-036 progress**
