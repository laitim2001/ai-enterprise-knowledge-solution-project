---
change_id: CH-016
spec_ref: ./spec.md
status: done     # in-progress | done
last_updated: 2026-06-28
---

# CH-016 — Checklist

## Implementation
- [x] I1 — `SidebarNav` 加 `useQuery({ queryKey: ['kb','list'], queryFn: kbApi.list })`（共用 `/kb` cache）
- [x] I2 — 算 `activeKbCount = data.filter(kb => !kb.archived).length`；render 時 `/kb` 項 tail 動態 override（未 ready → 省略 tail）
- [x] I3 — 移除 `WORKSPACE_NAV` 的寫死 `tail: '5'` + 註解說明對齊 mockup `tail = KB count`

## Verification
- [x] V1 — `tsc --noEmit` exit 0
- [x] V2 — `eslint`（app-shell.tsx）clean
- [x] V3 — 受控測試（Chrome MCP browser）：admin 登入 sidebar badge 顯示 `2` = DB 真實非 archived KB 數（8 KB 中 2 個 READY、6 archived）；其他 nav tail（Cmd↵ / T2 / Soon）不變

## Cross-Cutting
- [x] 非 H1 / 非 H6 / 非 H7（badge 視覺不變，placeholder → 真實數據 = reverse drift）
- [x] commit references progress（R2）
- [x] progress closeout + lessons written
