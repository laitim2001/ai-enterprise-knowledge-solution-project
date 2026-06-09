---
change_id: CH-012
spec_ref: ./spec.md
checklist_ref: ./checklist.md
status: implementing     # implementing | closed
---

# CH-012 — Progress

> Day-N entries + closeout retro。

---

## Day 1 — 2026-06-09

### Done
- 用戶揀 kickoff Gap C C-2(圖片完整性)→ 調查現有揀圖 logic(CH-011 已做 document-order span）
- **實測根因診斷**(/query drive-images-1):20 圖**全堆 §3.1.1 lead citation**,citations[1-12] 零圖;20 張只涵蓋 §3.1.1+§3.1.3,**§3.1.4/3.1.5 零圖**。兩重 front-loading cap(section-attach max_aux=18 doc-order truncate + cap_images_per_answer=20 greedy)疊加 + decorative filter 20→15
- 用戶揀**方向 A(section-fair 分配)**over B(純升 cap）/ C(A+升 cap）
- spec.md 寫 + approved;ADR-0049 寫 + Accepted + README index

### Decisions
- Change CH-012(改既有揀圖分配行為,非 bug;< 3 days)
- ADR-0049 延伸 ADR-0048「揀圖模式」(section-fair distribution）
- 主修 = section-attach round-robin;次修(cap section-fair)= conditional,視主修實測(Karpathy §1.2 唔投機）
- 維持 cap=20(唔升,守圖洪水紀律);無 re-index/schema/frontend 改

### Blockers
- 無

### Commits
| Hash | Subject |
|---|---|
| _(pending)_ | docs CH-012 spec + ADR-0049 kickoff |
| _(pending)_ | feat(generation): CH-012 section-fair neighbour-image distribution |

---

## Closeout（填於 status=closed）
_(待)_

---

**End of CH-012 progress**
