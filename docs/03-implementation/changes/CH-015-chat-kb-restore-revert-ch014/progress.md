---
change_id: CH-015
spec_ref: ./spec.md
checklist_ref: ./checklist.md
status: closed     # in-progress | closed
---

# CH-015 — Progress

## Day 1 — 2026-06-28

### Done
- 用戶實測 CH-014 後回報「選 drive-user-manual，點對話回到 Drive Manuals」→ 確認 CH-014 方向誤判
- 查 DB 確認用戶對話 `3644b17a` kb_id=drive-user-manual-kb-20260618（綁定一直正確）
- revert：恢復 `loadConversation` KB 還原 + source-fidelity 註解
- tsc exit 0；受控測試（playwright，完整重現用戶場景）驗證點對話顯示正確 KB
- CH-014 spec 標 superseded

### Decisions
- mockup 靜態 demo 未涵蓋「載入對話顯示其 KB」→ 真實需求(§15 north-star)+ 用戶明確 wins over mockup（§13）
- 只動 loadConversation 還原一行；建立/re-bind/new-chat/firstActive 全不動（一直正確）

### Blockers
- 服務在 session 邊界被 teardown（run_in_background 進程綁 session）→ 改用 `Start-Process` detached 重啟（backend pid 20572 / frontend pid 92064）以撐過 session 邊界

### Commits
| Hash | Subject |
|---|---|
| (本次) | revert(frontend): restore chat KB load on conversation open (C10, CH-015) |

---

## Closeout

### Acceptance verification
§3 全 ✅：受控測試驗證點對話顯示對話真正 KB（drive-user-manual）；tsc clean。

### Lessons
見 spec §8：mockup 靜態 demo ≠ 全行為 spec；勿用單一框架（「對齊 mockup」）框死方向（呼應 memory feedback_ui_compare_mockup_first）；改既有正確行為前先確認它為何存在。CH-014 受控測試其實已證明還原正確，卻因 framing 仍去移除——這是核心教訓。

### Component design note status updates
- C10：chat KB selector 載入還原 = 恢復（CH-013-era 行為），對話忠實顯示其 KB
