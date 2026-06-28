---
change_id: CH-015
spec_ref: ./spec.md
status: done     # in-progress | done
last_updated: 2026-06-28
---

# CH-015 — Checklist

## Implementation
- [x] I1 — 恢復 `loadConversation` KB 還原（`chat/page.tsx`：`if (detail.conversation.kb_id) setKbId(...)`）+ source-fidelity / CH-014-revert 註解

## Verification
- [x] V1 — `tsc --noEmit` exit 0
- [x] V2 — 受控測試（playwright）：選 drive-user-manual → 送 → reload chat → 點對話 → 選擇器顯示 drive-user-manual-kb-20260618（非 default）
- [x] V3 — default new chat 仍 firstActive；建立綁定 / re-bind 不受影響（未動）

## Cross-Cutting
- [x] 非 H1 / 非 H6；H7 = 真實需求(§15)wins over mockup 靜態 demo（§13）
- [x] supersedes CH-014（CH-014 spec status → superseded）
- [ ] commit references progress（R2）→ 本次 commit
- [x] progress closeout + lessons written
