---
bug_id: BUG-024
report_ref: ./report.md
checklist_ref: ./checklist.md
status: done
last_updated: 2026-05-24
---

# BUG-024 — Progress

> Sev3 surgical idx alignment per Karpathy §1.3。Postmortem NOT required per PROCESS.md §4.5。

## Day 1 — 2026-05-24

### Investigation

User-eye verify post BUG-021 amendment + BUG-022 chat 頁面 reference screenshot click 反映 outside badge `1` vs modal header idx `2` 不一致。Source inspection 確認:
- ImageGallery thumbnail badge(`frontend/app/(app)/chat/page.tsx` line 1828)用 `{i + 1}` over **imageCitations subset** position
- ScreenshotModal idx(line 522-526)用 `latestAssistantCitations.findIndex+1` over **full citations** array position
- 兩個 base 唔同 → mismatch when image-bearing chunk 唔係 full citations 第 1 個

### Decisions

- **D1.1** — Sev3 classification:visual inconsistency only,no data loss / no workflow break;Karpathy §1.2 simplicity = idx alignment fix not 1-cell rendering correctness。
- **D1.2** — Fix direction = align ImageGallery badge to CitationPill convention(full citations findIndex+1)not flip ScreenshotModal to use subset position。Reason:CitationPill / SourcesStrip / PanelSourceCard 全部 reference full citations idx → numbering convention canonical = full citations position。
- **D1.3** — `allCitations` prop pass-through over context / global state — over-engineered for 2 levels of component tree;callsite + ImageGallery 同 file,prop pass-through 最 surgical。

### Code changes

| 檔案 | 改動 |
|---|---|
| `frontend/app/(app)/chat/page.tsx` | `ImageGallery` 加 `allCitations: Citation[]` prop;thumbnail badge computed via `allCitations.findIndex` + 8-line inline comment cite BUG-024;callsite pass `allCitations={message.citations}` |

### Verify gates

- Reproduce step:thumbnail badge `N` = ScreenshotModal header `N` for same chunk_id ✅(post-fix verify)
- `tsc --noEmit` exit 0
- `next lint` clean
- `pnpm test:unit` chat-meta-row 7/7 preserve

### Commits

(pending — 1 commit:`fix(chat): align ImageGallery thumbnail badge with full citations idx — BUG-024`)

### Retro

- **Subset vs full-set indexing convention**:當有 sub-set view rendering(ImageGallery imageCitations vs full latestAssistantCitations / SourcesStrip 全集),要 surface 一個 stable idx,必須 align to canonical numbering source(per mockup,= full citations position)。Sub-set position 唔可以做 idx — 會破 cross-surface reference。
- **Latent inherited bug**:呢個 mismatch 自 BUG-019 ImageGallery restore + BUG-021 `>=1` unification inherit;之前 imageCitations subset 同 full citations 順序通常 align(image-bearing chunks 多排前),所以表面冇問題 — 直到呢次 query response shape 令 position 0 vs 1 露白。**Lesson**:cascade fix(BUG-019-022)visually 解決 surface,但仍可能掩埋 sub-pattern bug latent inheritance — user-eye verify 嘅階段範圍要 extend to「numbering / counts / labels cross-surface consistency」,唔單只 visual layout。
