---
bug_id: BUG-037
report_ref: ./report.md
checklist_ref: ./checklist.md
status: fixing     # fixing | closed
---

# BUG-037 — Progress

> Day-N entries + closeout。Sev3 → 無 mandatory postmortem。

---

## Day 1 — 2026-06-09

### Done
- 用戶揀「先修 eval harness」(task_ecd4f8bd)作 per-doc config 平台 enabler
- 診斷:CLI `run_ragas_eval.py` 缺 required kb_id crash(ADR-0018 後簽名 mismatch)+ `/eval` API hardcode `drive_user_manuals`
- 確認 HybridSearcher 自動 resolve per-KB index → CLI 只需 thread kb_id
- 分類 Bug-fix Sev3,非 H1(無 ADR);branch `fix/eval-harness-kb-id`

### Decisions
- Bug-fix(CLI 真 crash)over Change;API hardcode 同根源一齊修
- 預設保持 `drive_user_manuals`(production-preserve)

### Blockers
- 無

### Commits
| Hash | Subject |
|---|---|
| _(pending)_ | fix(eval): BUG-037 thread kb_id through eval CLI + /eval API |

---

## Closeout（填於 status=closed）
_(待)_

---

**End of BUG-037 progress**
