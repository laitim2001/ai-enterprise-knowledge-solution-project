---
change_id: CH-018
spec_ref: ./spec.md
checklist_ref: ./checklist.md
status: closed     # in-progress | closed
---

# CH-018 — Progress

## Day 1 — 2026-06-28

### Done
- 診斷：ChatHeader `<select>` 用 `kbs.map` 列全部 KB（含 archived）；父層 `kbs` 同時供 activeKb find（需全集合）→ 只能在 ChatHeader 內過濾 option
- 建立 CH-018 三件套（spec approved / checklist / progress）
- 實作：ChatHeader 內 `selectableKbs` filter + archived activeKb edge-case 補回 + `(archived)` 後綴
- tsc exit 0 / eslint clean（唯一 warning 既有無關）/ chat-bug033.test 2 passed
- 受控驗證（Chrome MCP）：KB 下拉只列 2 active（drive-images-1 + drive-user-manual-kb-20260618），6 archived 全部不見；default selected = drive-images-1（firstActive）

### Decisions
- 只改 ChatHeader option 來源，父層 `kbs` 保持全部（activeKb find + firstActive 需 robustness）
- edge case：歷史對話綁 archived KB → 補回清單標 `(archived)`，select 不壞 + 忠實顯示（CH-015 精神）
- 延續 CH-016/017 非 archived 語義

### Blockers
- 無

### Commits
| Hash | Subject |
|---|---|
| (本次) | feat(frontend): chat KB selector lists active KBs only (C10, CH-018) |

---

## Closeout

### Acceptance verification
§3 主要項 ✅：下拉只列 active KB（受控驗證 2 個，不見 6 archived）；default firstActive；chat-bug033.test 未回歸；tsc + eslint clean。archived activeKb edge case 由 code review + 補回邏輯保障（無綁 archived KB 的對話可即時測）。

### Lessons
- 同一份 `kbApi.list()` 在一個 component 裡服務兩種需求（全集合：activeKb find / firstActive default；子集合：可選清單）時，過濾要落在「消費端」（ChatHeader option）而非「資料源」（父層 kbs），否則破壞依賴全集合的 robustness。
- 過濾 archived 的 selector 必須處理「當前值是 archived」的 edge case（歷史對話載入綁 archived KB），否則 `<select value>` 對不上 `<option>` 清單會顯示異常 → 補回 + 標記。

### Component design note status updates
- C10：chat KB selector = active（非 archived）KB only（CH-018），archived 僅在「該對話綁定它」時補回標記；延續 CH-016/017 非 archived 語義。
