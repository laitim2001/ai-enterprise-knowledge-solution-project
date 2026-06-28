---
change_id: CH-014
spec_ref: ./spec.md
checklist_ref: ./checklist.md
status: closed     # in-progress | closed
---

# CH-014 — Progress

## Day 1 — 2026-06-28

### Done
- 受控測試（playwright + ekptest 暫設 admin）決定性證明現行綁定 + 還原**功能正確**（非 bug）
- 清理：刪 30 筆 mock dev-user 髒對話（cascade messages），剩 admin 1 + ekptest 1
- mockup 分析（ekp-page-chat.jsx）→ 確認 current 多做了載入還原（BUG-033），偏離 mockup selector 獨立語義
- spec approved（用戶 AskUserQuestion 選「對齊 mockup」）
- I1 移除 `loadConversation` line 315 KB 還原 + 對齊 mockup 註解

### Decisions
- 對齊 mockup = selector 獨立於對話切換（移除 BUG-033 還原）；re-bind（BUG-034）保留讓 sidebar tag 反映實際用的 KB；new chat 不重置（mockup 一致）
- H7：移除還原 = 修正 interaction drift（reverse direction，非 trigger）

### Blockers
- （無）

### Commits
| Hash | Subject |
|---|---|

---

### Commits
| Hash | Subject |
|---|---|
| (待 commit) | feat(frontend): align chat KB selector to mockup (C10) |

---

## Closeout

### Acceptance verification
§3 全部 ✅：tsc exit 0 + eslint exit 0（唯一 warning = 既有 `<img>`）；受控測試（playwright）驗 default=drive-images-1 → 點對話（drive-user-manual-kb-20260618）→ selector 維持 drive-images-1 不跳 = 對齊 mockup selector 獨立語義；對話正常打開；sidebar tag 不受影響。

### Lessons
- 「感覺像 bug」未必是 bug：受控測試先證明功能正確（綁定+還原都對），再發現真問題是**語義偏離 mockup**（BUG-033 載入還原過度實作），對的修法是移除而非再加
- mockup 是 single source of truth：對照 ekp-page-chat.jsx 才看出 current 多做了還原；改動 = 把 implementation 拉回 mockup（reverse drift）
- 改動極小（移除一行 + 註解），但需先用受控測試 + mockup 分析建立信心才動

### Component design note status updates
- C10：chat KB selector 語義由「混合（當前+對話還原）」→「獨立（當前要用的 KB）」對齊 mockup
