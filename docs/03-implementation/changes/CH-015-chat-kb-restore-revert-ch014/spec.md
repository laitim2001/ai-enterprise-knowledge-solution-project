---
change_id: CH-015
title: "revert CH-014 — 恢復 chat KB 載入還原（對話忠實顯示其真正用的 KB）"
status: done         # draft | proposed | approved | active | done | cancelled
created: 2026-06-28
target_completion: 2026-06-28
affects_components: [C10]      # C10 Chat
spec_refs:
  - CH-014（superseded — 本 CH revert 之）
  - CLAUDE.md §15 North-Star（source fidelity — 忠實還原）
  - CLAUDE.md §13（mockup vs 真實需求衝突的判斷）
  - frontend/app/(app)/chat/page.tsx loadConversation
  - references/design-mockups/ekp-page-chat.jsx（mockup 為靜態 demo）
---

# CH-015 — revert CH-014（恢復 chat KB 載入還原）

> **Spec version**：1.0（initial）
> **Owner**：AI（實作）/ Chris（approve）
> **Approved by**：Chris（2026-06-28 — 實測 CH-014 後回報「選了 drive-user-manual 但點對話回到 Drive Manuals」，要求恢復「對話顯示其真正 KB」+ chat 確認 commit revert）

## 1. Context (Why)

CH-014 移除了 `loadConversation` 的 KB 還原（`chat/page.tsx:315`），理由是「對齊 mockup（selector 獨立於對話切換）」。**這個方向判斷是錯的。**

用戶實測後回報：建新對話明確選 `drive-user-manual-kb-20260618`，但重新回 chat 頁、點該記錄時 KB 選擇器**回到 default `drive-images-1`（Drive Manuals）**——正是 CH-014 移除還原造成的。用戶真正要的是「**點對話 → 選擇器忠實顯示該對話真正用的 KB**」。

**根因 = 用「對齊 mockup」框死方向**：
- mockup（`ekp-page-chat.jsx`）是**靜態 demo**，KB selector 是固定 state、不隨對話切換改變——但 mockup 從未考慮「載入歷史對話要顯示其 KB」這個真實需求（demo 沒有真實多對話 / 多 KB 持久化）。
- 真實需求（用戶明確 + CLAUDE.md §15 north-star「忠實還原原文/狀態」）= 對話載入時忠實顯示它綁定的 KB。
- 所以這是 mockup 靜態行為 vs 真實需求的衝突，**真實需求 wins**（§13）。CH-014 錯把 mockup 的靜態 demo 行為當成 spec，移除了正確的還原。

**證據**：
- 用戶對話 `3644b17a`「hello, what is Drive ?」DB `kb_id = drive-user-manual-kb-20260618`（綁定正確 — 建立邏輯一直正確）。
- 恢復還原後受控測試（playwright，2026-06-28）：選 drive-user-manual → 送 → reload chat → 點該對話 → 選擇器**正確顯示 `drive-user-manual-kb-20260618`**（不再跳回 Drive Manuals）。

## 2. Scope (What)

### 2.1 Behavior Change

- **Before（CH-014）**：點選歷史對話 → 選擇器維持當前選擇（不還原對話 KB）→ 顯示誤導性的 default。
- **After（本 CH，= CH-014 之前）**：點選歷史對話 → 選擇器還原成該對話綁定的 `kb_id`（忠實顯示對話真正用的 KB）。

### 2.2 In Scope

- 恢復 `loadConversation` 的 KB 還原：`if (detail.conversation.kb_id) setKbId(detail.conversation.kb_id)`（`chat/page.tsx`），加上說明此為 source fidelity（§15）+ CH-014 誤判已 revert 的註解。

### 2.3 Out of Scope（explicit）

- ❌ ensureConversation 建立綁定 / BUG-034 re-bind / handleStartNewChat / useEffect firstActive：全部不動（一直正確）。
- ❌ 後端 / schema / 持久化：不動。
- ❌ 任何 visual / layout 改動。

## 3. Acceptance Criteria

- [x] 點選歷史對話 → 選擇器顯示該對話的 `kb_id`（受控測試：drive-user-manual 對話 → 顯示 drive-user-manual）✅
- [x] `tsc --noEmit` exit 0 ✅
- [x] 受控測試（playwright）完整重現用戶場景：選 KB → 送 → reload → 點對話 → 選擇器還原正確 ✅

## 4. Risks

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | 還原與 useEffect(firstActive) race 導致還原被覆蓋 | Low | Med | 還原 setKbId(對話KB) 後，該 KB 在 kbs 內 → useEffect `!kbs.some` 為 false 不覆蓋；受控測試（reload 後點對話）已驗穩定 |
| R2 | 偏離 mockup 靜態行為（H7）| n/a | n/a | mockup 為靜態 demo 未涵蓋此需求；真實需求（§15 + 用戶明確）wins per §13；恢復既有行為（BUG-033）非新增 |

## 5. Effort Estimate

~0.5 小時（恢復一行 + 註解；tsc；受控測試；服務重啟）。

## 6. Dependencies

- 無外部阻塞。後端不動。
- **非 H1 / 非 H6**。**H7**：恢復對話 KB 還原 = 滿足真實需求（§15 忠實還原），mockup 靜態 demo 未涵蓋此情境 → 真實需求 wins（§13）；恢復既有行為非新 drift。
- supersedes CH-014。

## 7. Spec Changelog（deviation log）

| Date | Change | Reason | Approver |
|---|---|---|---|
| 2026-06-28 | Initial draft + done | CH-014 方向誤判（把 mockup 靜態 demo 當 spec，移除正確還原）；用戶實測回報 + 要求恢復；受控測試驗證還原正確 | Chris |

## 8. Lessons（方向誤判教訓）

- **mockup 是靜態 demo，不是所有行為的 spec**：mockup 未涵蓋的真實需求（多對話載入要顯示其 KB），不能用「mockup 沒這樣做」去否定。§15 north-star（忠實還原）+ 用戶明確需求 > mockup 靜態行為（§13）。
- **不要用單一框架（「對齊 mockup」）框死方向**：呼應 memory `feedback_ui_compare_mockup_first`（ADR-0061→0062→revert 寬度三輪反覆教訓）——從一句話推斷方向 + 用未驗證前提框死，會放大誤差。CH-014 受控測試其實已證明「還原正確」，卻仍因「對齊 mockup」framing 去移除它。
- **改既有正確行為前先確認它為何存在**：BUG-033 還原當初就是為了這需求；移除前應確認用戶不要它，而非假設 mockup wins。
