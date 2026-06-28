---
change_id: CH-014
spec_ref: ./spec.md
status: done     # in-progress | done
last_updated: 2026-06-28
---

# CH-014 — Checklist

> Derived from spec.md §3 acceptance criteria.

## Implementation

- [x] I1 — 移除 `loadConversation` KB 還原（`chat/page.tsx:315`）+ 更新註解對齊 mockup
- [x] I2 — BUG-034 re-bind / handleStartNewChat / useEffect firstActive 保留不動（確認無誤改）

## Verification

- [x] V1 — `tsc --noEmit` exit 0 + `eslint`（chat/page.tsx）exit 0（唯一 warning = line 1884 既有 `<img>`，無關）
- [x] V2 — 受控測試（playwright）：default selector=drive-images-1 → 點對話（綁 drive-user-manual-kb-20260618）→ **selector 維持 drive-images-1（不再跳）**；對話正常打開；sidebar tag 仍顯示對話 KB
- [x] V3 — new chat selector = firstActive(drive-images-1)；送出用 selector KB（CH-013 受控測試已驗綁定）；re-bind 保留不動

## Cross-Cutting

- [x] 非 H1 → 無 ADR；H7 = 對齊 mockup（修正 interaction drift，非 trigger）；無 visual 改動
- [ ] commit references progress Day-N（R2）→ 待用戶確認 commit
- [x] progress closeout written
- [ ] progress status flipped to `closed` → 待 commit

---

**Lifecycle reminder**:checklist 隨 spec acceptance criteria 衍生。
