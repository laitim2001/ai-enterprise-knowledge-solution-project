---
change_id: CH-014
title: "chat KB 選擇器對齊 mockup — 移除載入對話時的 KB 還原（selector 獨立語義）"
status: approved         # draft | proposed | approved | active | done | cancelled
created: 2026-06-28
target_completion: 2026-06-28
affects_components: [C10]      # C10 Chat（前端 chat 互動）
spec_refs:
  - references/design-mockups/ekp-page-chat.jsx (line 73 / 99 / 250 — KB selector 獨立 state；切換對話不改 kbId；對話各自顯示 kb_name)
  - architecture.md §5 (chat UI)
  - BUG-033（reverse — 載入還原當初過度實作，偏離 mockup）
  - frontend/app/(app)/chat/page.tsx loadConversation
---

# CH-014 — chat KB 選擇器對齊 mockup（移除載入對話時的 KB 還原）

> **Spec version**：1.0（initial）
> **Owner**：AI（實作）/ Chris（approve）
> **Approved by**：Chris（2026-06-28 — chat AskUserQuestion 選「對齊 mockup（推薦）」）

## 1. Context (Why)

使用者回報 chat 的 KB 選擇器「點選歷史對話時停留/飄移、感覺誤導」。**受控測試（2026-06-28，playwright）已決定性證明現行綁定 + 還原功能正確**：new chat 選非 default KB（`drive-user-manual-kb-20260618`）→ 送出 → DB 對話 `kb_id` 綁定正確 → reload 點該對話 → selector 還原正確。所以這**不是功能 bug**。

真正問題是**語義不一致 + 偏離 mockup**：

- **Mockup 設計**（`ekp-page-chat.jsx`）：KB selector 是獨立 state（line 73 `useState("drive-manuals")`），**切換對話時不改變它**（line 99 `onSelect={setActiveConv}` 不碰 kbId）；每個歷史對話在左側列表各自顯示自己的 `kb_name`（line 250）。即 selector = 「我現在要用哪個 KB 問」。
- **現行 code 多做了一步**：`loadConversation`（`chat/page.tsx:315`，BUG-033）載入對話時把 selector 還原成「那個對話的 KB」。於是 selector 一下代表「當前要用的」、一下代表「這個對話的」，兩種語義混合 → 使用者感覺「飄/誤導」。這是**偏離 mockup 的過度實作**。

依 CLAUDE.md §13「mockup wins」+ §5.7 H7（mockup 為前端 canonical spec），對齊 mockup 把 selector 還原成單一語義。**移除還原 = 把 implementation 拉回 mockup 行為 = 修正 interaction drift**（per §5.7「修正 drift 把 implementation 更貼近 mockup（reverse direction）」不屬 H7 trigger）。

連帶背景：通電（CH-013）後對話 user-scoped（ADR-0031），舊 mock dev-user 的髒對話已隔離 + 清理（2026-06-28 刪 30 筆），所以本 change 純粹是語義對齊。

## 2. Scope (What)

### 2.1 Behavior Change

- **Before**：點選歷史對話 → `loadConversation` 把 KB selector 還原成該對話的 `kb_id`（selector 隨對話切換而變）。
- **After**：點選歷史對話 → selector **維持當前選擇不變**（對齊 mockup）。selector = 「當前要用哪個 KB 問」。歷史對話各自的 KB 仍在左側列表 tag 顯示（既有，無需改）。

### 2.2 In Scope

- **移除 `loadConversation` 的 KB 還原**（`chat/page.tsx:315` `if (detail.conversation.kb_id) setKbId(...)` + BUG-033 註解）。`loadConversation` 只 `setActiveConvId` + hydrate messages。
- 更新註解說明對齊 mockup（selector 獨立語義）。

### 2.3 Out of Scope（explicit）

- ❌ **BUG-034 re-bind 保留**（`chat/page.tsx:408` reuse 既有對話送新訊息時 `update kb_id`）：保留讓左側 tag 始終反映該對話訊息**實際**用的 KB（selector 獨立 + tag 準確，兩者分工一致）。
- ❌ **handleStartNewChat 不重置 kbId 保留**（`:343`）：mockup new chat 也不重置（line 99 不碰 kbId）→ 維持對齊。
- ❌ **useEffect firstActive default 保留**（`:227-235`）：處理 kbId 初始 `''` / 指向已刪 KB 的 fallback，對齊 mockup「default 一個 KB」。
- ❌ **後端 / schema / conversations 持久化**：完全不動（kb_id 持久化正確，受控測試已驗）。
- ❌ **任何 visual / layout 改動**：純移除一個 state 副作用，視覺輸出不變。

## 3. Acceptance Criteria

- [ ] 點選歷史對話 → KB selector 值**不變**（維持點之前的選擇）。
- [ ] 左側對話列表每筆仍正確顯示自己的 KB tag（不受影響）。
- [ ] new chat → selector = 當前/firstActive default（行為與今日一致）。
- [ ] 送出查詢仍用 selector 當前 KB（`streamQuery` kb_id = kbId）；新對話 create 綁該 KB（受控測試重跑驗）。
- [ ] reuse 既有對話送新訊息 → re-bind 仍把對話 kb_id 更新為當前 selector（tag 反映實際用的 KB）。
- [ ] `tsc --noEmit` + `eslint`（chat/page.tsx）clean。
- [ ] 受控測試（playwright）：選 KB-B → 送 → reload → 點該對話 → **selector 維持當前值（不再自動跳成對話的 KB）**；sidebar tag 顯示對話 KB。

## 4. Risks

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | 移除還原後「打開舊對話繼續問」用的是 selector 當前 KB 而非對話原 KB（語義變化）| Med | Low | 這正是 mockup 設計（selector = 當前要用的）；re-bind 保留讓 tag 跟上實際 KB；acceptance 明列 |
| R2 | 使用者習慣了 BUG-033 還原行為，覺得 selector「不跟對話」奇怪 | Low | Low | 對齊 mockup 為 single source of truth（H7）；用戶已 approve 此方向；sidebar tag 提供對話 KB 資訊 |
| R3 | 反轉 BUG-033 造成其表面回歸（loadConversation stuck on kbs[0]）| Low | Low | 移除後 selector = 當前 kbId（非 kbs[0]）；useEffect firstActive 確保 kbId 永遠有效；受控測試驗 |

## 5. Effort Estimate

~0.5–1 小時（移除一行 + 註解；tsc/eslint；受控測試一輪）。

## 6. Dependencies

- 無外部 / OQ 阻塞。後端不動。
- **非 H1**：無 architecture component / vendor / storage / multi-KB / 8-view layout philosophy 改動；無 Tier 2。純前端互動副作用移除。→ 無 ADR。
- **H7**：移除還原 = 把 chat 互動拉回 mockup（`ekp-page-chat.jsx` selector 獨立語義）= 修正 interaction drift（reverse direction，per §5.7 非 trigger）。無 visual / layout 改動。
- **H6**：前端，非後端 pipeline 強制覆蓋；受控測試（playwright）替代。

## 7. Spec Changelog（deviation log）

| Date | Change | Reason | Approver |
|---|---|---|---|
| 2026-06-28 | Initial draft + approved | 受控測試證明功能正確；對齊 mockup 移除 BUG-033 過度實作的載入還原；用戶 AskUserQuestion 選「對齊 mockup」 | Chris |

---

**Lifecycle reminder**：呢份 spec locked after status=approved。重大 deviation → §7 changelog。
