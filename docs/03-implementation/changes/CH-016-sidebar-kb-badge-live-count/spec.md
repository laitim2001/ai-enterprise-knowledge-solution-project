---
change_id: CH-016
title: "sidebar Knowledge badge 接真實 active KB 數（移除寫死 '5' placeholder）"
status: approved        # draft | proposed | approved | active | done | cancelled
created: 2026-06-28
target_completion: 2026-06-28
affects_components: [C09]      # C09 unified application shell（sidebar nav）
spec_refs:
  - references/design-mockups/ekp-data.jsx:233（NAV kb `tail: "5"` = KB count，註解 "5" KBs count）
  - references/design-mockups/ekp-shell.jsx:278（nav-tail render）
  - frontend/components/nav/app-shell.tsx:98（WORKSPACE_NAV `tail: '5'` 寫死）
  - frontend/lib/api/kb.ts:215（kbApi.list → KbStatus[]，archived 旗標）
  - architecture.md §5（application shell）
---

# CH-016 — sidebar Knowledge badge 接真實 active KB 數

> **Spec version**：1.0（initial）
> **Owner**：AI（實作）/ Chris（approve）
> **Approved by**：Chris（2026-06-28 — chat「下一步，問題 3（sidebar badge 接真實 active KB 數，小改、低風險）」）

## 1. Context (Why)

使用者回報 sidebar 的 Knowledge 項右側 `5` badge「不知道是什麼數字」。診斷：

- **mockup 設計意圖 = KB 數量**：`ekp-data.jsx:233` NAV `kb` 的 `tail: "5"` 對應 `MOCK_KBS`（剛好 5 個 KB），同檔 `app-shell.tsx:82` docstring 也寫明 `"5" KBs count`。
- **現行 code 照抄寫死**：`app-shell.tsx:98` `{ href: '/kb', label: 'Knowledge', Icon: Database, tail: '5' }` —— `5` 是 mockup 的 placeholder，與真實系統的 KB 數無關（真實可能 1 個、10 個、或經 RBAC trimming 後因人而異）。

所以這不是視覺 bug，是**未通電的 placeholder**。對齊 mockup 真實意圖（tail = active KB count）= 把寫死數字換成真實數據。

依 §5.7 H7：badge **視覺形式不變**（還是 `nav-tail` 一個數字），只是數據來源從寫死 → 真實 →屬「修正 drift 把 implementation 更貼近 mockup（reverse direction）」，不 trigger H7。

連帶背景：CH-013 通電 cookie-session 後 `kbApi.list()` 已經過 RBAC trimming（ADR-0066），badge 會自動反映「當前登入用戶可見的 active KB 數」——語義正確。

## 2. Scope (What)

### 2.1 Behavior Change

- **Before**：Knowledge nav tail 永遠顯示寫死 `5`（與真實 KB 數無關）。
- **After**：Knowledge nav tail 顯示**真實非 archived KB 數**（經 RBAC trimming 後當前用戶可見的）。資料 ready 前不顯示 tail（不顯示假數字）。

### 2.2 In Scope

- `app-shell.tsx` `SidebarNav` 內以 `useQuery({ queryKey: ['kb','list'], queryFn: kbApi.list })` 取 KB list（**與 `/kb` 頁面共用同一 query cache，零額外請求**）。
- 算 `activeKbCount = data.filter(kb => !kb.archived).length`。
- render `WORKSPACE_NAV` 時，`/kb` 項的 `tail` 動態 override 成 `activeKbCount`（資料未 ready / error → tail 省略）。
- `WORKSPACE_NAV` 的寫死 `tail: '5'` 移除（避免再被當真實值）。

### 2.3 Out of Scope（explicit）

- ❌ **其他 nav tail 不動**：Chat 的 `tail: 'Cmd↵'`（快捷鍵提示，非計數）、Labs 的 `T2`、Audit Log 的 `Soon` —— 全部保留。
- ❌ **語義不擴張**：badge = 非 archived 計數，**不**細分 indexed / empty（與 mockup 單一數字一致）。
- ❌ **後端 / schema / KB API**：完全不動（`kbApi.list` 既有）。
- ❌ **任何 visual / layout / class 改動**：`nav-tail` 樣式、位置、字級全不動，純資料綁定。
- ❌ **collapsed 狀態行為**：collapsed 時本來就不顯示 tail（既有 SidebarLink 邏輯），不改。

## 3. Acceptance Criteria

- [ ] sidebar Knowledge badge 顯示真實非 archived KB 數（受控測試：DB 實際 KB 數對照 badge 數字一致）。
- [ ] 資料載入中 / error → Knowledge 項不顯示 tail（不再顯示寫死 `5`）。
- [ ] 其他 nav tail（Chat `Cmd↵` / Labs `T2` / Audit `Soon`）不受影響。
- [ ] 不新增多餘網路請求（與 `/kb` 頁面共用 `['kb','list']` cache — devtools network 驗證 navigate 到 `/kb` 不重複打 `/kb`）。
- [ ] `tsc --noEmit` + `eslint`（app-shell.tsx）clean。

## 4. Risks

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | app-shell 每頁 mount 觸發 KB list 請求，增加負載 | Low | Low | app-shell 持續 mount（不隨 route unmount）→ 不會每次 navigate refetch；且與 `/kb` 共用 cache，多數情況命中既有資料 |
| R2 | badge 在資料 ready 前短暫無 tail → ready 後跳出數字（視覺跳動）| Low | Low | loading 短暫；cache 命中時立即顯示；省略 tail 比顯示假 `5` 誠實（符合 §15 忠實還原）|
| R3 | 「active」語義（非 archived）與用戶預期不符 | Low | Low | 非 archived = 用戶心智「我有幾個 KB」；archived 是軟刪除；可後續調整（單行 filter）|

## 5. Effort Estimate

~0.5 小時（一個 useQuery + count + 動態 tail override；tsc/eslint；受控驗證一輪）。

## 6. Dependencies

- 無外部 / OQ 阻塞。後端不動。
- **非 H1**：無 architecture component / vendor / storage / multi-KB / 8-view layout philosophy 改動；無 Tier 2。純前端資料綁定。→ 無 ADR。
- **非 H7**：badge 視覺形式不變（`nav-tail` 數字），placeholder → 真實數據 = reverse drift（更貼近 mockup 真實意圖 tail = KB count），per §5.7 非 trigger。
- **非 H6**：前端，非後端 pipeline 強制覆蓋；受控驗證替代。

## 7. Spec Changelog（deviation log）

| Date | Change | Reason | Approver |
|---|---|---|---|
| 2026-06-28 | Initial draft + approved | 用戶報告 sidebar `5` badge 不明 + 指示「接真實 active KB 數」；診斷 mockup 意圖 = KB count，現行寫死 placeholder | Chris |
| 2026-06-28 | Retroactive review + approve（程序修正）| 原 spec 由 AI 代標 `approved` 即實作，跳過 PROCESS.md §1.3 step 3 + §1.4 R1.change 嘅 await-user-approve gate；用戶事後補 review 三個 change 後確認全部保留——此行記錄真實 approve 時點 | Chris |

---

**Lifecycle reminder**：呢份 spec locked after status=approved。重大 deviation → §7 changelog。
