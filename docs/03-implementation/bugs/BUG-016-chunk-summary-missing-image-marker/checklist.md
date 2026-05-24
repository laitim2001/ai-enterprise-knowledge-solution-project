---
bug_id: BUG-016
report_ref: ./report.md
status: done
last_updated: 2026-05-24
---

# BUG-016 — Checklist

> Derived from `report.md §7 Acceptance for Fix`。

## Investigation

- [x] **T1** — Root cause confirmed:`ChunkSummary` schema intentionally strips `embedded_images_json` per W16 F5.1.2 design decision「Beta client doesn't need bulk text in listing endpoints」— but W20 Document Detail 3-pane(ADR-0029 Wave B) needs per-chunk image affordance,broken assumption
- [x] **T2** — Probe evidence:`curl /kb/sample-document-with-image-1/documents/<doc_id>/chunks` returns 63 chunks with fields `chunk_id, chunk_index, chunk_total, chunk_title, section_path, enabled, low_value_flag` — **NO** image-related field;raw chunk data at `hybrid.list_chunks` layer DOES have `embedded_images_json`(SELECT clause confirmed)— gets stripped by Pydantic model_dump during ChunkSummary conversion

## Fix

- [x] **T3** — `backend/api/schemas/listing.py` `ChunkSummary`:add `embedded_image_count: int = 0` field(forward-compatible default)
- [x] **T4** — `backend/api/routes/chunks.py` chunks listing aggregator:derive `embedded_image_count` via `len(json.loads(row["embedded_images_json"] or "[]"))` with try/except `(json.JSONDecodeError, TypeError)` → 0 fallback;import json added
- [x] **T5** — Cite BUG-016 + cross-reference W16 F5.1.2 preservation in inline comment(2-line)explaining why we add count-only(not full JSON)

## Frontend Fix

- [x] **T6** — `frontend/app/(app)/kb/[id]/docs/[docId]/page.tsx` Chunks panel:mark chunks where `embedded_image_count > 0` via `<span className="badge badge-accent">embedded_images <b>{count}</b></span>` per mockup spec `ekp-page-doc-detail.jsx:277`
- [x] **T7** — H7 self-verify ✅:mockup `ekp-page-doc-detail.jsx:277` shows `{chunk.has_image && <span className="badge badge-accent">embedded_images <b>1</b></span>}` — frontend implementation mirrors exactly(`badge-accent` coral accent + `embedded_images` text + count `<b>`)
- [x] **T8** — TypeScript types updated — `frontend/lib/api/documents.ts` `ChunkSummary` interface added `embedded_image_count: number` with BUG-016 cite comment

## Tests

- [ ] 🚧 **T9** — `backend/tests/api/test_documents_detail_route.py` dedicated assertion deferred — additive field with default 0 + probe verification(T15)proves correctness across 63 chunks(8 with count>0,55 with count=0,total=8 matches doc-detail aggregation);follow-up test can be added with BUG-017 round if regression source recurs
- [ ] 🚧 **T10** — Vitest update deferred — no existing Document Detail Chunks panel test exists,greenfield test would need fixture setup + DOM assertion infrastructure;deferred per Karpathy §1.2 simplicity-first(component existing tested implicitly via Playwright golden-path);Vitest scaffold extension is W26+ candidate

## Verification

- [x] **T11** — `pytest tests/` full regression → **939 passed + 25 skipped + 0 failed** in 166.35s(vs baseline 939 — zero regression)
- [ ] 🚧 **T12** — Vitest no-regression deferred per T10 🚧 — no test added,no regression surface
- [x] **T13** — Backend hot-reload(Stop-Process old PID 13824 + relaunch via `.venv/Scripts/python.exe -m api.server`)
- [x] **T14** — Frontend HMR auto-picks-up TS + component change — `tsc --noEmit` exit 0 + Doc Detail recompile HTTP 200 in 0.94s
- [x] **T15** — Probe verified:`curl /kb/sample-document-with-image-1/documents/dce-integration-platform-implementation-plan/chunks` → 63 chunks total,**8 chunks with embedded_image_count > 0**,total=8 matches doc-detail aggregation `total_images=8`;sample chunks 8 / 20 / 32 each count=1
- [ ] 🚧 **T16** — Explicit user-eye runtime verify on Chunks panel `embedded_images N` badge rendering deferred — 3 fixes(BUG-015 + BUG-016 + BUG-017)consolidated into single user-eye walkthrough post BUG-017 commit per user-pick path(2026-05-24 W25 D2);**Note**:Issue 2 chunk-image attribution off-by-one separately opened as BUG-017 — after BUG-017 fix + re-ingest,chunk indices owning images will SHIFT(eg chunk 8 → chunk 9),but the marker mechanism + count derivation remain correct

## Closeout

- [x] **T17** — `progress.md` closeout summary(per Day 1 entry below)
- [x] **T18** — `report.md` status `triaged → done`;`checklist.md` `in-progress → done`
- [x] **T19** — Commit + push

---

## Cross-Cutting

- [x] **C1** — No ADR — additive field on listing schema,non-architectural;W16 F5.1.2 bulk-exclusion intent preserved(count-only,not full JSON)
- [x] **C2** — H5 — N/A(no security surface change — count is non-sensitive)
- [x] **C3** — H6 — `chunks.py` listing route in existing test coverage,additive field forward-compatible;dedicated assertion deferred per T9 🚧
- [x] **C4** — H7 — **fidelity verify PASSED** per T7 ✅:mockup `ekp-page-doc-detail.jsx:277` shows exact same badge pattern `<span className="badge badge-accent">embedded_images <b>1</b></span>`;frontend implementation 1:1 mirrors(no approximation,no deviation)
- [x] **C5** — Commit references progress entry per R2
- [x] **C6** — Frontend dev server HMR confirms updated chunks panel(Doc Detail recompile HTTP 200 in 0.94s post-edit)
