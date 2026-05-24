---
bug_id: BUG-023
report_ref: ./report.md
status: done
last_updated: 2026-05-24
---

# BUG-023 — Checklist

> Derived from `report.md §6 Acceptance for Fix`。Sev2 surgical fix per Karpathy §1.3。

## Fix

- [x] **T1** — `frontend/app/(app)/chat/page.tsx` CitationPill popover 3 `<div>` → `<span>` + appropriate `style.display` set:
  - Line 1525 FileTypeChip + doc_title + score header row → `<span style={{display: 'flex', ...}}>` 保留 flex layout
  - Line 1552 section_path container → `<span style={{display: 'block', ...}}>` className `section-path text-xs` 保留
  - Line 1562 chunk_title preview → `<span style={{display: 'block', ...}}>` 其他 styles 保留
  - 8-line block comment cite BUG-023 + Karpathy §1.3 rationale

## Verification

- [x] **T2** — `tsc --noEmit` exit 0(已 verify post-fix)
- [x] **T3** — `next lint` clean(只有 pre-existing line 1673 `<img>` warning,不關 BUG-023 fix 事)
- [x] **T4** — Vitest `chat-meta-row.test.tsx` 7/7 pass(no regression)
- [ ] **T5** — User-eye hover popover console **零** `<div> cannot be a descendant of <p>` warning(pending user refresh + DevTools verify)

## Closeout

- [x] **T6** — `progress.md` Day 1 entry + retro
- [ ] **T7** — Commit:`fix(chat): CitationPill popover div→span:block — BUG-023 hydration warning`

---

## Cross-Cutting

- [x] **C1** — H1 architectural change:N/A
- [x] **C2** — H2 vendor change:N/A
- [x] **C3** — H5 security:N/A
- [x] **C4** — H6 test coverage:既有 Vitest 7/7 preserved;no new test added(visual + structural change only;hover popover sub-DOM 非既有 chat-meta-row test scope)
- [x] **C5** — H7 design fidelity:visual identical(`<span style={{display: 'block'/'flex'}}>` 同 `<div>` 視覺等效;structural-only fix)
- [x] **C6** — Commit references progress entry per CLAUDE.md §10 R2(will tag on commit)
