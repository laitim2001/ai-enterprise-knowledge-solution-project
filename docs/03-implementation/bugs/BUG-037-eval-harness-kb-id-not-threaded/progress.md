---
bug_id: BUG-037
report_ref: ./report.md
checklist_ref: ./checklist.md
status: closed     # fixing | closed
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
| `5a2c3ae` | fix(eval): BUG-037 thread kb_id through eval CLI + /eval API |

---

## Closeout — 2026-06-09

**判決**:✅ RESOLVED(14 test 綠;CLI crash + API hardcode 兩處 kb_id 已 thread 通）

- Fix:`EvalRunRequest`/`EvalShootoutRequest` 加 `kb_id` field + route 用 `payload.kb_id`;CLI 加 `--kb-id` + `engine.retrieve(kb_id=)`。預設保持 `drive_user_manuals`(production-preserve）。
- Test:`test_eval_kb_id_bug037.py` 6 個(API 透傳 ×3 + CLI arg + CLI retrieve-kb_id regression guard)+ 既有 eval endpoint 8 = 14 passed。
- Tooling:backend ruff/format clean;scripts/ 唔喺 ruff/mypy gate(pre-existing E402/F401 + 手寫風格);mypy --strict 31 pre-existing error 零個喺改行(詳見 checklist V1）。
- **Unblock**:CH-011 AC6 圖片順序/完整性 eval + 未來 per-doc config-test eval 可指定 KB(task_ecd4f8bd 可關）。
- ff-merge fix branch → main。

**Sev3 → 無 mandatory postmortem。**

---

**End of BUG-037 progress**
