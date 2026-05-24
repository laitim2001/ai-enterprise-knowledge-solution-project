---
bug_id: BUG-013
report_ref: ./report.md
status: done
last_updated: 2026-05-24
---

# BUG-013 — Checklist

> Derived from `report.md §7 Acceptance for Fix`。

## Investigation

- [x] **T1** — Root cause confirmed via 3-layer diagnostic chain:mock_msal.ts hardcodes Bearer + never `/auth/login` → no `ekp_session` cookie → apiClient explicit Bearer makes fetch work but `<img>` can't add custom header → 401
- [x] **T2** — Probe evidence:`/api/backend/.../screenshots/<sha>.png` returns 401 (no auth) vs 200 (with Bearer)

## Fix

- [x] **T3** — `frontend/app/api/backend/[...path]/route.ts`:add `if (isDev && !headers['authorization'])` Bearer injection after HOP_HEADERS filter,using `process.env.NEXT_PUBLIC_AUTH_MOCK_BEARER ?? 'dev-token'`
- [x] **T4** — Docstring update cite BUG-013 + production isDev=false carve-out documented

## Verification

- [x] **T5** — Next.js dev server HMR auto pick up file change — confirmed via post-edit probe(/screenshots/... no-auth GET 200 = was 401 pre-fix)
- [ ] 🚧 **T6** — Explicit user-eye runtime verify on `/kb/sample-document-with-image-1?tab=images` deferred — user routed to `/kb/[id]/docs/[doc_id]` Document Detail page during 2026-05-24 W25 D2 verify session,surfaced BUG-015 + BUG-016 instead;BUG-013 fix correctness independently validated via T5 post-edit probe(401 → 200 transition);the precise `/kb/[id]?tab=images` user-eye verify rolls forward to next image-pipeline regression session OR confirmed implicitly once BUG-015 unblocks Document Detail same-origin proxy path
- [x] **T7** — Smoke /images endpoint with Bearer header — 200 preserved(injection is conditional `!headers['authorization']`,apiClient explicit Bearer not overwritten)

## Closeout

- [x] **T8** — `progress.md` closeout summary(per Day 1 entry below)
- [x] **T9** — `report.md` status `triaged → done`;`checklist.md` `in-progress → done`
- [x] **T10** — Commit + push BUG-013 fix

---

## Cross-Cutting

- [x] **C1** — No ADR — H1 / H2 untouched(dev-only proxy auth flow tweak)
- [x] **C2** — H5 — N/A(dev mode only;production isDev=false bypass — no production security regression)
- [x] **C3** — H6 — N/A(Next.js catch-all proxy route file has no unit test infra historically;integration via dev server smoke)
- [x] **C4** — H7 — N/A(no frontend visual / mockup change)
- [x] **C5** — Commit references progress entry per R2
- [x] **C6** — Frontend dev server HMR confirms updated route
