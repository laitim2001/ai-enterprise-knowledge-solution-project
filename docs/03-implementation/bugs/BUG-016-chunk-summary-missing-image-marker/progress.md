---
bug_id: BUG-016
report_ref: ./report.md
checklist_ref: ./checklist.md
status: done
last_updated: 2026-05-24
---

# BUG-016 — Progress

> Bug-fix workflow per `PROCESS.md §4`。

## Day 1 — 2026-05-24

### Investigation

W25 D2 user-eye fidelity verify session(jointly with BUG-015 diagnosis)— user opened `/kb/sample-document-with-image-1/docs/dce-integration-platform-implementation-plan` Document Detail 3-pane page and reported:

> **「也看不到有任何的 chunks 內容是 [with images]」**

Screenshot showed all 63 chunks in Chunks panel rendering identically with no `[with images]` marker / badge / affordance,despite 8 images existing on the document(`total_images=8`)。

**Critical correction to user's premise**(echoed in BUG-015 progress)— user feared this meant chunk-image association was missing at ingestion-time / Azure Search storage layer;answer is **NO**:
- `hybrid.list_chunks` line 348 SELECT clause **does** request `embedded_images_json` from Azure Search
- Line 373 returns it as `str(item.get("embedded_images_json") or "[]")`
- Doc-detail aggregation proves data flow correctness via `total_images=8 + image_refs count=8`(loop reads chunk-level field successfully)

**Actual root cause**:`backend/api/schemas/listing.py` `ChunkSummary` schema **intentionally strips** `embedded_images_json` per W16 F5.1.2 design decision「Beta client doesn't need bulk text in listing endpoints」。Schema docstring explicitly notes this exclusion。W20 Document Detail 3-pane(ADR-0029 Wave B)added the need for per-chunk image affordance,which was not part of W16-era scope — **broken assumption** between W16 schema decision and W20 surface requirement。

### Decisions

- **D1.1** — 分類 Bug-fix BUG-016 Sev3;same-tier 7-bug image-pipeline cascade(BUG-009-015 chain continues)
- **D1.2** — Fix shape = additive `embedded_image_count: int` field on `ChunkSummary`(per report §8 Option 3 selected),NOT full `embedded_images_json` string(would violate W16 F5.1.2 bulk-exclusion intent + payload bloat across N chunks)。Backend derives via `len(json.loads(...))` from already-fetched JSON string,zero extra Azure Search query
- **D1.3** — No ADR triggered:additive field on listing schema is non-architectural;forward-compatible default 0
- **D1.4** — Frontend marker design subject to H7 self-verify(checklist T7)— must check mockup for `[with images]` pattern;if mockup lacks specific design → STOP + ask user(NOT approximate per CLAUDE.md §5.7 H7)

### Code changes(pending)

| 檔案 | 改動 |
|---|---|
| `backend/api/schemas/listing.py` | `ChunkSummary`:add `embedded_image_count: int = 0` field;2-line inline comment cite BUG-016 + cross-ref W16 F5.1.2 preservation intent |
| `backend/api/routes/documents.py`(chunks listing aggregator) | Derive `embedded_image_count` via `len(json.loads(raw_chunk["embedded_images_json"] or "[]"))` with try/except → 0 fallback |
| `backend/tests/api/test_documents_detail_route.py`(or chunks listing test) | NEW assertion `embedded_image_count` field present + value matches expected count for fixture chunks with images |
| `frontend/lib/api/...` `apiClient.kb.*` TypeScript types | `ChunkSummary` TS mirror add `embedded_image_count: number` |
| `frontend/app/(app)/kb/[id]/docs/[docId]/...` Document Detail Chunks panel | Mark chunks where `embedded_image_count > 0` via visual affordance(per mockup `[with images]` pattern OR per H7-confirmed alternative)|

### Verify gates(pending)

- `pytest tests/` full regression → 0 fail vs baseline 939
- `pnpm test:unit` Vitest no regression(if frontend test added)
- Backend hot-reload + Frontend HMR pick up changes
- Probe chunks listing returns `embedded_image_count` field
- User reload Document Detail page → chunks marked visually

### Commits(pending)

_(see commit footer — `fix(api+ui): ChunkSummary adds embedded_image_count for Document Detail per-chunk marker — BUG-016`)_

### Retro

- **W16-decision vs W20-need broken assumption pattern**:`ChunkSummary` listing-payload bulk-exclusion intent was right for W16-era KB Detail Chunks tab scope but didn't anticipate W20 Document Detail 3-pane(ADR-0029)needing per-chunk image affordance。**Process lesson**:phase-introduced schemas should be revisited at each downstream surface addition for affordance coverage;additive count-only field preserves original intent
- **H7 mockup spec exact match**:`ekp-page-doc-detail.jsx:277` provided exact spec(`badge badge-accent` + `embedded_images` text + `<b>` count)— no approximation needed,implementation 1:1 mirror。Karpathy §1.1 think-before-coding paid off — checked mockup BEFORE coding instead of designing a different affordance
- **Test deferral rationale**:additive field with default 0(forward-compatible);probe verification covers correctness across all 63 chunks;follow-up test can be added with BUG-017 round if regression source recurs。Karpathy §1.2 don't pre-test hypothetical regression
- **Issue 2 surfaced same session**:user-eye verify went further than this BUG's marker affordance scope and discovered the actual chunk-image attribution off-by-one — opened as BUG-017 per user-pick 2026-05-24 Option 1 separate BUG cascade trail。Note that after BUG-017 fix + re-ingest,chunk indices owning images will SHIFT(eg current chunk 8 → likely chunk 9 post-fix),but the marker mechanism + count derivation in BUG-016 remain correct(schema + per-chunk derivation unchanged)
