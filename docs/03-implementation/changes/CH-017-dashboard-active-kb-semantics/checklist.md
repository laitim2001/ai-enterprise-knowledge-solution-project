---
change_id: CH-017
spec_ref: ./spec.md
status: done     # in-progress | done
last_updated: 2026-06-28
---

# CH-017 — Checklist

## Implementation
- [x] I1 — `dashboard/page.tsx` 加 `activeKbs = kbs.filter(k => !k.archived)`；`totalDocs`/`totalChunks`/`totalStorageMb` 改基於 `activeKbs`
- [x] I2 — KB stat value `{kbs.length}` → `{activeKbs.length}`（active = 非 archived）+ 註解說明 mockup 無 archived 概念
- [x] I3 — 文案：Recent queries 移除「(Q6)」+ Today's spend meta 移除「Beta cohort」→ 清楚「尚未啟用」英文

## Verification
- [x] V1 — `tsc --noEmit` exit 0
- [x] V2 — `eslint`（dashboard/page.tsx）clean
- [x] V3 — 受控測試（Chrome MCP）：stat 顯示 2 active / 12 docs / 738 chunks；KB 表格仍 8 列；文案無 (Q6)/Beta cohort；既有 dashboard.test 5 passed

## Cross-Cutting
- [x] 非 H1 / 非 H6 / 非 H7（stat 數字 = reverse drift；placeholder 文案 = EKP 自有 empty-state）
- [x] commit references progress（R2）
- [x] progress closeout + lessons written
