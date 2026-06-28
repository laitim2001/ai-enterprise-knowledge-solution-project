---
change_id: CH-016
spec_ref: ./spec.md
checklist_ref: ./checklist.md
status: closed     # in-progress | closed
---

# CH-016 — Progress

## Day 1 — 2026-06-28

### Done
- 診斷確認：sidebar Knowledge `5` badge = mockup placeholder（`ekp-data.jsx:233` NAV tail = KB count），現行 `app-shell.tsx:98` 寫死 `'5'`
- 確認資料源：`kbApi.list()` → `KbStatus[]`（archived 旗標）；`/kb` 頁面用 `useQuery(['kb','list'])` → 共用 cache 可行
- 建立 CH-016 三件套（spec approved / checklist / progress）
- 實作：app-shell.tsx `SidebarNav` 接 query + 算 count + 動態 override `/kb` tail；移除寫死 `'5'`
- tsc exit 0 / eslint clean
- 受控驗證（Chrome MCP）：admin 登入 → sidebar Knowledge badge = `2` = DB 真實非 archived（8 KB 中 2 READY / 6 archived），與 dashboard KB 表格一致；Chat `Cmd↵` / Labs `T2` / Audit `Soon` 不變

### Decisions
- badge 語義 = 非 archived KB 數（archived = 軟刪除不計入）
- 共用 `['kb','list']` query cache（零額外請求）
- 資料未 ready / error → 省略 tail（不顯示假 `5`，§15 忠實還原）

### Notes（out of scope，留給問題 2）
- dashboard 主區 stat「Knowledge bases **8** active」的 `8` 是 KB 總數（含 archived），標籤誤寫 `active` → 與 sidebar `2`（真 active）語義不一致。屬 dashboard placeholder 措辭問題，CH-016 不動。

### Blockers
- 無

### Commits
| Hash | Subject |
|---|---|
| (本次) | feat(frontend): wire sidebar Knowledge badge to live active-KB count (C09, CH-016) |

---

## Closeout

### Acceptance verification
§3 全 ✅：sidebar badge = 真實非 archived count（受控驗證 admin = 2）；loading/error 省略 tail；其他 tail 不變；共用 cache 零額外請求；tsc + eslint clean。

### Lessons
- mockup 寫死的計數 placeholder（`tail: "5"` = MOCK_KBS length）通電真實資料時，**共用既有頁面的 query cache（同 queryKey）** 是最省的接法 — 零額外請求 + 自動跟隨 RBAC trimming。
- 驗證踩坑：localhost:3000 是 Langfuse docker，EKP frontend Next.js dev 被擠到 **3001**（port 衝突 auto-increment）；驗證前先確認真實 port（`Get-NetTCPConnection`），勿假設 3000。

### Component design note status updates
- C09：sidebar Knowledge nav tail = live active-KB count（CH-016），取代 mockup 寫死 placeholder。
