---
change_id: CH-018
spec_ref: ./spec.md
status: done     # in-progress | done
last_updated: 2026-06-28
---

# CH-018 — Checklist

## Implementation
- [x] I1 — `ChatHeader` 內算 `selectableKbs = kbs.filter(k => !k.archived)`；option 清單用之，archived activeKb edge case 補回末尾
- [x] I2 — archived option label 加 `(archived)` 後綴；空清單判斷改用 option 清單長度

## Verification
- [x] V1 — `tsc --noEmit` exit 0
- [x] V2 — `eslint`（chat/page.tsx）clean（唯一 warning = 既有 `:1896` `<img>`，與本次無關）
- [x] V3 — 受控測試（Chrome MCP）：下拉只列 2 active KB（drive-images-1 + drive-user-manual，不見 6 archived）；default = firstActive；chat-bug033.test 2 passed（CH-015 載入還原未回歸）

## Cross-Cutting
- [x] 非 H1 / 非 H6 / 非 H7（過濾 = reverse drift；archived 後綴 = edge case 誠實處理）
- [x] commit references progress（R2）
- [x] progress closeout + lessons written
