---
bug_id: BUG-015
report_ref: ./report.md
status: done
last_updated: 2026-05-24
---

# BUG-015 — Checklist

> Derived from `report.md §7 Acceptance for Fix`。

## Investigation

- [x] **T1** — Root cause confirmed:`image_refs[].blob_url` returns raw Azurite URL stored at ingestion time(orchestrator `sha_to_url` writes raw Azurite URL into `ChunkRecord.embedded_images`)vs `/kb/{id}/images` aggregator post-BUG-012 correctly re-derives via `screenshot_proxy_url`
- [x] **T2** — Probe evidence:`curl /kb/sample-document-with-image-1/docs/dce-integration-platform-implementation-plan` returns `"blob_url": "http://127.0.0.1:10000/devstoreaccount1/..."`(raw Azurite),vs `curl /kb/sample-document-with-image-1/images` returns `"url": "/api/backend/kb/.../screenshots/<sha>.png"`(proxy)

## Fix

- [x] **T3** — `backend/api/routes/documents.py` doc-detail aggregator(`get_doc_detail`):import `screenshot_proxy_url` helper(or rely on module-local accessibility);override `ImageRef.blob_url = screenshot_proxy_url(kb_id, f"{sha}.png")` in the seen_images dedup loop
- [x] **T4** — Cite BUG-015 + cross-reference BUG-012 in inline comment(2-line) explaining why we don't trust ingestion-time `blob_url`
- [x] **T4b** — **Issue 1 frontend wire**(H7 deviation Option B user-authorized 2026-05-24)— `frontend/app/(app)/kb/[id]/docs/[docId]/page.tsx` `ImageThumb` 加 real `<img src={img.blob_url}>` + onError fallback to gradient + Layers icon(mirrors BUG-011 pattern from `app/(app)/kb/[id]/page.tsx` `ImageCard`)。Backend fix T3 alone insufficient because mockup ImageThumb was pure gradient placeholder

## Tests

- [ ] 🚧 **T5** — `backend/tests/api/test_documents_detail_route.py` dedicated assertion deferred — backend fix is single-line URL re-derive sharing infrastructure with BUG-012 `/kb/{id}/images` aggregator(which has test coverage);probe verification(T8)proves correctness;follow-up test can be added with BUG-017 round if regression source recurs

## Verification

- [x] **T6** — `pytest tests/` full regression → **939 passed + 25 skipped + 0 failed** in 166.35s(vs baseline 939 — zero regression)
- [x] **T7** — Backend hot-reload via Stop-Process old PID 16720 + relaunch `.venv/Scripts/python.exe -m api.server`(no `--reload` per setup.md §4.3 BUG-008)
- [x] **T8** — Probe verified:`curl /kb/sample-document-with-image-1/docs/dce-integration-platform-implementation-plan` → `image_refs[0].blob_url` = `/api/backend/kb/sample-document-with-image-1/screenshots/<sha>.png`(proxy URL ✅,was raw Azurite URL pre-fix)
- [ ] 🚧 **T9** — Explicit user-eye runtime verify on `/kb/[id]/docs/[doc_id]` 8/8 thumbnails render deferred — Issue 1 frontend wire(T4b)applied + `tsc` exit 0 + Doc Detail HMR recompile HTTP 200 in 0.94s;**Issue 2 image-section attribution off-by-one(parser/chunker bug)opened as separate BUG-017** during 2026-05-24 W25 D2 verify session;3 fixes(BUG-015 + BUG-016 + BUG-017)consolidated into single user-eye walkthrough post BUG-017 commit per user-pick path

## Closeout

- [x] **T10** — `progress.md` closeout summary(per Day 1 entry below)
- [x] **T11** — `report.md` status `triaged → done`;`checklist.md` `in-progress → done`
- [x] **T12** — Commit + push

---

## Cross-Cutting

- [x] **C1** — No ADR — URL derivation in aggregator only,non-architectural
- [x] **C2** — H5 — exemption surface narrow(proxy URL goes through existing rate-limit-exempt + auth-injected path BUG-013/014 already mitigated)
- [x] **C3** — H6 — `documents.py` doc-detail route already in test coverage(`test_documents_detail_route.py`),follow-up assertion deferred per T5 🚧
- [x] **C4** — H7 — **deviation Option B user-authorized 2026-05-24** for Issue 1 frontend `ImageThumb` real `<img>` render(mockup pure gradient was static-prototype limitation,not design choice — same rationale as BUG-011 H7 deviation Option A 2026-05-23)
- [x] **C5** — Commit references progress entry per R2
