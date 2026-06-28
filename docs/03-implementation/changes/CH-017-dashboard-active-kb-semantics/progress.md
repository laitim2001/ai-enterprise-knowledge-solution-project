---
change_id: CH-017
spec_ref: ./spec.md
checklist_ref: ./checklist.md
status: closed     # in-progress | closed
---

# CH-017 — Progress

## Day 1 — 2026-06-28

### Done
- 診斷：stat「8 active」= `kbs.length`（含 archived）但 label「active」→ 語義 bug
- 對照 mockup：`ekp-page-dashboard.jsx:39` 也是 `{kbs.length} active`，但 MOCK_KBS（`ekp-data.jsx:7`）用 status 無 archived 概念 → mockup demo length = active count，真實系統引入 archived 後失效
- 建立 CH-017 三件套（spec approved / checklist / progress）
- 實作：activeKbs filter；KB count + Documents + chunks + storage 改基於 activeKbs；2 處文案去 jargon
- tsc exit 0 / eslint clean / dashboard.test 5 passed
- 受控驗證（Chrome MCP，admin）：stat strip 8→**2** active / 18→**12** docs / 1365→**738** chunks；文案 → "Cost tracking is not enabled yet" + "No queries recorded yet — query logging is not enabled."；KB 表格仍 8 列含 ARCHIVED；sidebar badge 仍 2（一致）

### Decisions
- stat strip 全部基於 active（非 archived）KB：KB count + Documents + chunks + storage，避免「2 active 卻 18 docs」新矛盾
- KB 表格（KbSummaryCard）不動：仍列全部含 archived（完整清單 vs strip 概覽分工）
- placeholder 文案：移除 user-facing 內部 jargon（Q6 / Beta cohort），保留已清楚的（run from /eval / no baseline）
- 不建後端 endpoint（用戶未選「接後端」）

### Blockers
- 無

### Commits
| Hash | Subject |
|---|---|
| (本次) | feat(frontend): dashboard stat strip active-KB semantics + honest placeholders (C09, CH-017) |

---

## Closeout

### Acceptance verification
§3 全 ✅：stat = active（2，與 sidebar 一致）；Documents/chunks 基於 active（12 / 738）；KB 表格仍 8 列含 archived；jargon (Q6 / Beta cohort) 移除；tsc + eslint clean + dashboard.test 5 passed。

### Lessons
- mockup demo 缺少真實系統維度（archived 軟刪除）時，照抄的計數運算式（`kbs.length`）在真實資料下語義漂移。修一個 stat（KB count）必須連帶檢查同 strip 的相依加總（docs/chunks），否則製造「2 active 卻 18 docs」新矛盾。
- 「誠實標示」最小化解讀 = 移除漏到 user-facing UI 的內部 jargon（OQ 編號 Q6 / Beta cohort），不重寫已清楚 + 有 actionable 引導的 placeholder（run from /eval）。

### Component design note status updates
- C09：dashboard stat strip 語義 = active（非 archived）KB 概覽（CH-017），與 sidebar badge（CH-016）一致；KB 表格維持全清單。
