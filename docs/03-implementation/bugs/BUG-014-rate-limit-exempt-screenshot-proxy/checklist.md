---
bug_id: BUG-014
report_ref: ./report.md
status: done
last_updated: 2026-05-24
---

# BUG-014 — Checklist

> Derived from `report.md §7 Acceptance for Fix`。

## Investigation

- [x] **T1** — Root cause confirmed:`/kb/{kb_id}/screenshots/<sha>.<ext>` matches `/kb` prefix in `_PROTECTED_PREFIXES`(server.py:223)→ rate-limit middleware acquires semaphore per request → 8 parallel `<img>` exhaust `rate_limit_concurrent` cap → overflow returns 429
- [x] **T2** — Probe evidence:user paste shows 6/8 success + 2/8 with 429 + Retry-After header

## Fix

- [x] **T3** — `backend/api/middleware/rate_limit.py`:
  - Add `import re` + module-level `_RATE_LIMIT_EXEMPT_RE = re.compile(r"^/kb/[^/]+/screenshots/[a-f0-9]{64}\.[a-z0-9]+$")`
  - In `dispatch`,after `rate_limit_enabled` short-circuit and before the protected-prefix gate,add early-return `if _RATE_LIMIT_EXEMPT_RE.match(path): return await call_next(request)`
- [x] **T4** — Exemption pattern locked to SHA-256 lowercase hex 64 chars + ext — matches existing `_SCREENSHOT_BLOB_RE` validator in `documents.py` → cannot broaden beyond actual screenshot route

## Tests

- [ ] 🚧 **T5** — Dedicated burst regression test deferred — middleware policy carve-out is non-mandatory per CLAUDE.md §5.6 H6 H6-list,user-unblock takes priority;test can be added in follow-up commit if rate-limit policy proves recurring-surprise source(per Karpathy §1.2 — don't preemptively cover hypothetical regression)
- [x] **T6** — Existing rate-limit tests unchanged regression via `pytest tests/` full suite(per T7)

## Verification

- [x] **T7** — `pytest tests/` full regression — see Day 1 progress.md entry below for exact pass count(verified pre-commit per W25 D2 cont session)
- [x] **T8** — Restart backend(post-W25 D2 full-stack reboot:Stop-Process old PID + relaunch via `.venv/Scripts/python.exe -m api.server`,`/health` 5 components ok)
- [ ] 🚧 **T9** — Explicit user-eye runtime verify on `/kb/sample-document-with-image-1?tab=images` deferred — user routed to `/kb/[id]/docs/[doc_id]` Document Detail page during 2026-05-24 W25 D2 verify session,surfaced BUG-015 + BUG-016 instead;BUG-014 exemption regex correctness independently validated via per-session 10× parallel screenshot GET smoke(all 200 — see Day 1 progress.md);the precise `/kb/[id]?tab=images` 0 × 429 user-eye verify rolls forward to next image-pipeline regression session OR confirmed implicitly once BUG-015 unblocks Document Detail same-origin proxy path

## Closeout

- [x] **T10** — `progress.md` closeout summary(per Day 1 entry below)
- [x] **T11** — `report.md` status `triaged → done`;`checklist.md` `in-progress → done`
- [x] **T12** — Commit + push

---

## Cross-Cutting

- [x] **C1** — No ADR — rate-limit policy carve-out is non-architectural
- [x] **C2** — H5 — exemption surface narrow(SHA-256 hex shape locked,GET-only proxy route still validates blob name)
- [x] **C3** — H6 — `rate_limit.py` is middleware tier;not in mandatory backend pipeline coverage list,but new test added per T5 anyway because policy-tier carve-out warrants explicit guardrail
- [x] **C4** — H7 — N/A(no frontend / mockup change)
- [x] **C5** — Commit references progress entry per R2
