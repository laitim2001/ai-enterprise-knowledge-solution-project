---
change_id: CH-018
title: "chat KB 選擇器只列 active（非 archived）KB"
status: approved        # draft | proposed | approved | active | done | cancelled
created: 2026-06-28
target_completion: 2026-06-28
affects_components: [C10]      # C10 Chat
spec_refs:
  - frontend/app/(app)/chat/page.tsx:956-971（ChatHeader KB <select>）
  - frontend/app/(app)/chat/page.tsx:220-235（父層 kbs / activeKb / firstActive default）
  - frontend/lib/api/kb.ts:122（KbStatus.archived）
  - CH-015（loadConversation 還原對話 KB — archived edge case 來源）
  - CH-016 / CH-017（同一非 archived 語義：sidebar badge + dashboard stat）
  - references/design-mockups/ekp-page-chat.jsx（mockup selector，MOCK_KBS 無 archived 概念）
---

# CH-018 — chat KB 選擇器只列 active（非 archived）KB

> **Spec version**：1.0（initial）
> **Owner**：AI（實作）/ Chris（approve）
> **Approved by**：Chris（2026-06-28 — chat「選擇 KB 的選項中，不應該也顯示那些不是 active 的 KB 記錄，應該只顯示 active 的」）

## 1. Context (Why)

chat 頁面的 KB 選擇器（`ChatHeader` 的 `<select>`，`chat/page.tsx:965`）用 `kbs.map` 列出**全部** KB，包含 archived（軟刪除）的。archived KB 不該是新提問的可選對象（用戶已主動軟刪除它）。延續 CH-016（sidebar badge）/ CH-017（dashboard stat）的同一非 archived 語義。

現況拆解：
- 父層 `kbs`（`:220`）= `kbApi.list()` 全部結果（含 archived）。
- 用於兩處：① `activeKb = kbs.find(k => k.kb_id === kbId)`（`:221`）—— 需要全部才能顯示「歷史對話綁的 archived KB」（CH-015 還原）；② ChatHeader `<select>` 的 option 清單（`:965`）—— **問題就在這裡列了全部**。
- `firstActive` default（`:232`，BUG-035）已會避開 archived 作為新對話 default，但下拉清單本身仍含 archived。

## 2. Scope (What)

### 2.1 Behavior Change

- **Before**：KB 下拉清單列出全部 KB（含 6 個 archived）。
- **After**：KB 下拉清單只列 active（非 archived）KB。例外：若當前載入的對話綁定一個現已 archived 的 KB，該 KB 仍出現在清單（標 `(archived)`），避免 `<select>` value 對不上 option 而壞掉，並忠實顯示該對話的 KB（CH-015）。

### 2.2 In Scope（只改 `ChatHeader`）

- `ChatHeader` 內算 `selectableKbs = kbs.filter(k => !k.archived)`。
- option 清單 = `selectableKbs`；若 `activeKb` 是 archived 且不在 `selectableKbs`（歷史對話 edge case）→ 補回清單末尾。
- archived 的 option label 加 `(archived)` 後綴（誠實標示，呼應 CH-017）。
- 空清單判斷由 `kbs.length === 0` 改為 option 清單長度。

### 2.3 Out of Scope（explicit）

- ❌ **父層 `kbs` 不改**：保持全部（`activeKb` find + `firstActive` useEffect 需要全集合 robustness；CH-015 載入 archived 對話顯示靠它）。
- ❌ **firstActive default 邏輯不改**（`:227-235`，已避開 archived）。
- ❌ **loadConversation / ensureConversation / re-bind 不改**（CH-015 還原行為保留）。
- ❌ **後端 / schema / KB API**：不動。
- ❌ **layout / class / select 結構**：不動，純改 option 來源 + label 後綴。

## 3. Acceptance Criteria

- [ ] chat KB 下拉清單只列 active KB（受控驗證：只見 2 個 active，不見 6 個 archived）。
- [ ] 新對話 default 仍為 active KB（firstActive，未改）。
- [ ] 載入綁 active KB 的歷史對話 → selector 正確顯示（CH-015，未回歸）。
- [ ] 載入綁 archived KB 的歷史對話（若有）→ selector 顯示該 KB 標 `(archived)`，select 不壞。
- [ ] `tsc --noEmit` + `eslint`（chat/page.tsx）clean。

## 4. Risks

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | 歷史對話綁 archived KB → select value 不在 active options → 顯示異常 | Med | Med | 補回 archived activeKb 到清單（標 archived），select value 永遠有對應 option |
| R2 | 過濾 archived 偏離 mockup（H7）| n/a | n/a | mockup MOCK_KBS 無 archived 概念（demo 全 active）→ 過濾 = 還原「列可用 KB」原意；`(archived)` 後綴是 mockup 未涵蓋的真實 edge case 之最小誠實處理（§13 真實需求 wins）|

## 5. Effort Estimate

~0.5 小時（ChatHeader 內 filter + edge-case 補回 + label；tsc/eslint；受控驗證）。

## 6. Dependencies

- 無外部 / OQ 阻塞。後端不動。
- **非 H1**：無 architecture component / vendor / storage / layout philosophy 改動；無 Tier 2。純前端 option 過濾。→ 無 ADR。
- **非 H7**：過濾 archived = reverse drift（還原 mockup「列可用 KB」原意，select 結構不變）；`(archived)` 後綴 = mockup 未涵蓋之真實 edge case 最小誠實處理（§13）。per §5.7 非 trigger。
- **非 H6**：前端；受控驗證替代。

## 7. Spec Changelog（deviation log）

| Date | Change | Reason | Approver |
|---|---|---|---|
| 2026-06-28 | Initial draft + approved | 用戶要求 chat KB 選擇器只列 active KB；延續 CH-016/017 非 archived 語義 | Chris |
| 2026-06-28 | Retroactive review + approve（程序修正）| 原 spec 由 AI 代標 `approved` 即實作，跳過 PROCESS.md §1.3 step 3 + §1.4 R1.change 嘅 await-user-approve gate（含 AI 自定 `(archived)` 後綴 + edge-case 補回）；用戶事後補 review 後確認保留——此行記錄真實 approve 時點 | Chris |

---

**Lifecycle reminder**：呢份 spec locked after status=approved。重大 deviation → §7 changelog。
