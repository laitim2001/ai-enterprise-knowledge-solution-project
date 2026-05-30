---
bug_id: BUG-026
report_ref: ./report.md
status: done
last_updated: 2026-05-30
---

# BUG-026 — Checklist

> Atomic checkbox per investigation / fix / regression / verify stages。
> AI tick 完成嘅 item;唔可以 tick 嘅 item 喺 progress Day-N entry 寫原因。

## Investigation

- [x] Reproduce 路徑 per `report.md §2`(code-trace,demo KB 已刪無法 live repro)
- [x] Identify root cause —— 3 finding(A 跨 citation 無 dedup / B gallery label mockup-faithful / C per-image caption ingest 深度)
- [x] Confirm hypothesis —— code path 確認(`attach_neighbour_images` + `page.tsx:1228-1245` flat render + `:1796` gallery)
- [x] Update `report.md §6` 確認 root cause

## Fix(Finding A —— dedup,主修)

- [x] 新 pure helper `frontend/lib/chat/citation-images.ts::dedupeCitationImages`(key checksum_sha256 fallback blob_url,attribute 首現 citation)
- [x] `chat/page.tsx` inline image cards 改由 deduped 列表 drive
- [x] `chat/page.tsx` ImageGallery 改由 deduped 列表 drive(保留 mockup 結構 + chunk_title label per Finding B)
- [x] image count(FeedbackBar / gallery badge)改用 unique image count
- [x] 只 touch 必要 code(Karpathy §1.3 surgical)—— `imageCitations` 保留畀 meta row「N with screenshots」(citations 數,語意正確)

## Regression Test

- [x] Vitest unit test 證 `dedupeCitationImages` 把同 checksum 跨 citation 圖只保留一次(6 cases,fails before / passes after)—— `tests/unit/citation-images.test.ts`
- [x] Run Vitest 相關 subset 綠 —— 13 passed(6 新 dedup + 7 既有 `chat-meta-row` 無 regression)
- [x] `npm run lint` clean(唯一 warning = pre-existing `<img>` @1596 InlineImageCard,未改)+ `tsc --noEmit` exit 0 + `npm run build` exit 0(✓ Compiled,15 頁生成)+ Prettier clean

## Verification

- [x] Re-run `report.md §2` 邏輯 —— deduped 列表每張獨特圖一次(unit test 覆蓋跨 citation dedup + 首現 attribution + blob_url fallback + 無 identity skip)
- [x] 確認無 regression —— 既有 `chat-meta-row` 4-img / 2-img 斷言維持(測試資料每 citation 不同 checksum → dedup 不改其 count);badge `citationIdx` 仍 anchor full-citations position(BUG-024 不變)
- [x] (user-facing)Manual UI verify —— **DONE**(2026-05-30 live):fresh KB `bug026-cii-verify-1` re-ingest + chat UI render「REFERENCED SCREENSHOTS · 3」3 張獨特圖無重覆(dedup PASS)

## Finding B / C(非主修)

- [x] Finding B documented 為 mockup-faithful(gallery `chunk_title` 不動,改 = H7 violation)
- [x] Finding C 驗證(user pick (a))—— `diagnose_image_doc_order.py` 證 8/8 圖 `alt_text` **全空** + per-image section 8/8 正確(post-BUG-017);結果記 `report.md §6`
- [x] Finding C fix 方向 = **C-ii Propagate 圖 section 落 ImageRef**(user pick 2026-05-30)

## Fix(Finding C-ii —— propagate section)

- [x] Storage `indexing/schemas.py::ImageRef` 加 `source_section: list[str]`(default_factory list;自動入 `embedded_images_json` via `to_search_doc` model_dump)
- [x] `ingestion/orchestrator.py` ingest 填 `source_section=list(spec.section_path)`(owning chunk section = parser-correct post-BUG-017)
- [x] API `api/schemas/query.py::ImageRef` 加 `source_section: list[str]`
- [x] `generation/citation_enrichment.py::parse_embedded_images` parse `source_section`(defensive coerce 到 list[str])
- [x] Frontend `lib/api/query.ts::ImageRef` 加 optional `source_section?: string[]`(容忍 legacy)
- [x] Frontend `lib/chat/citation-images.ts` 加 `imageSectionPath` + `imageTitle` helpers(prefer 圖自己 section / alt_text > section leaf > chunk_title)
- [x] `chat/page.tsx` InlineImageCard title+caption + ImageGallery title 改用 helpers
- [x] H1 邊界:`embedded_images_json` 係現有 §3.6 index field,只係 JSON 內加 key,**非 index schema 改**;Pydantic additive field → 無 H1 trigger / 無 ADR

## Regression Test(C-ii)

- [x] Backend 4 NEW tests(`test_citation_enrichment.py`:parse source_section + default-empty + non-list-coerce + storage→query round-trip)—— pytest **48 passed**(含既有)
- [x] Backend 0 new mypy error(15 pre-existing 全部唔 reference 新 code)
- [x] Frontend 6 NEW tests(`citation-images.test.ts`:imageSectionPath ×3 + imageTitle ×3)—— Vitest **19 passed**(13 + 6)
- [x] Frontend `tsc --noEmit` 0 + `npm run build` 0 + Prettier clean

## Verification(C-ii)

- [x] Storage→query round-trip unit test 證 `source_section` 過 `embedded_images_json` JSON contract
- [x] **Live re-ingest + UI verify DONE**(2026-05-30):fresh KB ingest(88 chunks + 8 images）→ `/query` API 證 source_section=8.1/8.2(neighbour-attach 帶圖自己 section）→ chat UI inline card「8.2 Scenario B」「8.5 Scenario E」+ gallery 標 8.1/8.2/8.5(每圖自己 section,非 citing §8 intro);需 `HYBRID_USE_SEMANTIC_RANKER=false` 繞 Free-tier 402(完後 revert）

## Closeout

- [x] `progress.md` closeout summary(timeline + root cause + lessons)
- [x] (Sev3 → postmortem 非強制,pattern recurring 先寫 —— 無 postmortem)
- [x] `report.md` status 翻 `done`
- [x] `progress.md` status 翻 `closed`

---

## Cross-Cutting

- [ ] 每 commit 對應 `progress.md` Day-N entry(R2)
- [ ] Commit message component tag `fix(frontend): … (C10)`(CC-1)
- [ ] (非 architectural fix → 無 ADR)
- [ ] (無 OQ 依賴)
