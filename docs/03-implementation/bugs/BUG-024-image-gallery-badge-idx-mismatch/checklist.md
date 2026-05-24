---
bug_id: BUG-024
report_ref: ./report.md
status: done
last_updated: 2026-05-24
---

# BUG-024 — Checklist

> Derived from `report.md §6 Acceptance for Fix`。Sev3 surgical idx alignment per Karpathy §1.3。

## Fix

- [x] **T1** — `frontend/app/(app)/chat/page.tsx` `ImageGallery` 函數 signature 加 `allCitations: Citation[]` prop + 8-line inline comment cite BUG-024 + numbering convention rationale
- [x] **T2** — Thumbnail badge `<span>{i + 1}</span>` → `<span>{badge}</span>` where `badge = fullIdx >= 0 ? fullIdx + 1 : '?'` + defensive fallback comment
- [x] **T3** — Callsite(MessageRow inside)pass `allCitations={message.citations}`

## Verification

- [x] **T4** — `tsc --noEmit` exit 0(已 verify post-fix)
- [x] **T5** — `next lint` clean(只有 pre-existing `<img>` warning,不關 BUG-024 fix 事)
- [x] **T6** — `pnpm test:unit` chat-meta-row 7/7 pass(no regression)
- [ ] **T7** — User-eye reproduce verify:thumbnail badge `N` = ScreenshotModal header `N`(same chunk_id consistent;pending user refresh + re-query test)

## Closeout

- [x] **T8** — `progress.md` Day 1 entry + retro
- [ ] **T9** — Commit:`fix(chat): align ImageGallery thumbnail badge with full citations idx — BUG-024`

---

## Cross-Cutting

- [x] **C1** — H1 architectural change:N/A
- [x] **C2** — H2 vendor change:N/A
- [x] **C3** — H5 security:N/A
- [x] **C4** — H6 test coverage:既有 Vitest 7/7 preserved;skip new test per Sev3 Karpathy §1.2 simplicity(idx alignment 屬 1-cell rendering;hard to assert via RTL without elaborate citations fixture)
- [x] **C5** — H7 design fidelity:post-fix numbering consistent with mockup convention(CitationPill / SourcesStrip / ImageGallery / ScreenshotModal / PanelSourceCard 全部 reference 同一 latestAssistantCitations position+1)
- [x] **C6** — Commit references progress entry per CLAUDE.md §10 R2(will tag on commit)
