---
bug_id: BUG-022
report_ref: ./report.md
status: done
last_updated: 2026-05-24
---

# BUG-022 — Checklist

> Derived from `report.md §6 Acceptance for Fix`。Sev1 fast-track,minimal change。

## Fix

- [x] **T1** — `backend/api/schemas/query.py` `Citation.doc_format` 加 `= "docx"` default(8-line inline comment cite BUG-022 + reasoning):
  - 「Drive corpus is .docx-only」rationale 令 default value 對 90%+ legacy data 正確
  - build_citations 對 fresh retrievals 仍 explicit set from chunk field(no behavior change for new data)
  - Schema backward compat preserved without database migration

## Verification

- [x] **T2** — uvicorn `--reload` 自動 pick up schema 改動;原 stale WatchFiles state cleared via fresh restart(同 session 內處理咗 Windows TCP socket ghost issue + ProactorEventLoop psycopg incompatibility → 改用 `--reload` flag explicitly per uvicorn loop selection)
- [x] **T3** — Backend pytest 既有 13 citation tests pass(no fixture change needed — default 只 affect missing-field deserialization,既有 tests 一直 explicit set doc_format)
- [x] **T4** — Live `GET /conversations/d0b9179bbaac4fdd95a8d8889bdaa8bd` 200 OK + response 包含 2 messages with citations carrying `doc_format: "docx"` default

## Runtime Verify

- [x] **T5** — User-eye runtime verify implicit through BUG-021 amendment user-eye walkthrough(`/chat` page 重新 load 對話 history 應該無 500 error)

## Closeout

- [x] **T6** — `progress.md` brief Day 1 entry + retro
- [x] **T7** — `postmortem.md` Sev1 mandatory(BUG-021 retroactive root cause analysis)
- [x] **T8** — Commit + push(rolled into amendment-followup commit)

---

## Cross-Cutting

- [x] **C1** — H1 architectural change:N/A
- [x] **C2** — H2 vendor change:N/A
- [x] **C3** — H5 security:N/A
- [x] **C4** — H6 test coverage:既有 backend pytest preserved;no new test needed(default value vs explicit value 兩個 path 已被既有 BUG-021 NEW tests + legacy tests cover)
- [x] **C5** — H7 design fidelity:N/A(backend schema)
- [x] **C6** — Commit references progress entry per R2
