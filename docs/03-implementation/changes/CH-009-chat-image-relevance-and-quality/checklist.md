---
change_id: CH-009
spec_ref: ./spec.md
adr_ref: ../../../adr/0046-chat-image-relevance-decorative-dims.md
---

# CH-009 — Checklist

> 逐項 atomic;done → `→[x]`,未做標 🚧 + 理由(per CLAUDE.md sacred rule)。**Code GATED on ADR-0046 Accept(H1)。**

## I-A — Decorative filter + dims probe (OD-1)
- [x] A1 — `probe_png_dimensions`(extractor.py,stdlib `struct` IHDR;非 PNG / 截斷 / 0-dim → `None`);`ScreenshotExtractor.extract` populate `ScreenshotRecord.width/height`
- [x] A2 — dims 落 `ChunkRecord` ImageRef:orchestrator `sha_to_dims` → `ImageRef(width,height)`;serialize 經 `to_search_doc`(已自動)+ `parse_embedded_images` 已讀 width/height(無需改 parse)
- [x] A3 — `decorative` 判定 + filter 喺 **frontend display**(`citation-images.ts` `isDecorativeImage`,`min(w,h)<DECORATIVE_MIN_PX=64`,dims 已知先判;0×0 legacy 保留)+ `dedupeCitationImages` skip decorative
- [x] A7a — architecture.md §3.6 CH-009 amendment block(ImageRef dims + decorative filter + cap + relevance ordering + H4 邊界)
- [x] A7b — C01 design note bump(extractor probe + orchestrator dims);C03 schema 欄位 width/height 早存在(只 populate,無 schema 改)

## I-B — Per-KB cap wiring (OD-2)
- [x] B1 — `MessageRow` cap = `maxImagesPerAnswer ?? INLINE_IMAGE_CAP`;`ChatThread`/`MessageRow` thread `maxImagesPerAnswer`;chat page 讀 `activeKb.config.max_images_per_answer ?? null`
- [x] B2 — C10 design note bump(cap wiring + decorative + relevance,CH-009 block)

## I-C — Query-relevance ordering (OD-3)
- [x] C1 — ⚠️ **OD-3 REVERTED 2026-06-08**:原實作 relevance-select(`selectInlineImages` top-cap by relevanceScore)live 驗揭把低分 §3.1.1 概覽圖排出 cap → 改回 **`selectInlineImages = deduped.slice(0, cap)` 純 document-order**(Finding D),概覽圖 lead;移除 `relevanceScore` 追蹤 + relevance sort。vitest 21 + tsc clean
- [x] C2 — ~~H4 guard~~ N/A after revert(無 relevance 排序 = 無 image signal 問題);document-order 用 `source_section`(既有),零 H4 風險
- [x] C3 — C10 design note bump(relevance-select + document-display);C05 generation 無 code 改(`parse_embedded_images` 早讀 width/height;`cap_images_per_answer` payload ceiling 不變 — interaction 記 progress)

## Tests (H6)
- [x] T1 — `probe_png_dimensions` + extractor + orchestrator dims flow(`test_ch009_image_dims.py` 9 tests:valid/non-PNG/truncated/0-dim/missing-IHDR + extractor populate + orchestrator ImageRef dims)
- [x] T2 — decorative filter(`citation-images.test.ts`:<64 drop / 一維 thin drop / 0×0 keep / =64 keep)
- [x] T3 — `selectInlineImages` cap(<=cap full / cap<=0 empty)
- [x] T4 — relevance-select + document-display(over-cap 揀高 relevance + document order;max relevance across citations)

## Re-index + Verification
- [x] V1 — backend pytest(`test_ch009_image_dims` 9 + `test_orchestrator` 12 = 21 passed)+ frontend vitest 22 passed + tsc clean + ruff clean + mypy 改檔 0 新 error(16 pre-existing docling)(AC6)
- [x] V2 — `drive-images-1` in-place re-index DONE(6/6,369 chunks;CH-009 dims probe 生效)
- [x] V3 — `/query` GL「post a journal entry」**AC1+AC2 PASS**:40 unique images **0 個 dims=0**(probe 全中);**1 個 93×62(min 62<64)= 燈泡 icon → 前端 filter**;39 內容圖(min≥237)保留;64 閾值穩坐 62-vs-237 gap
- [x] V4 — **AC3+AC4**:cap per-KB(`maxImagesPerAnswer ?? 8`,drive-images-1 null→8)+ relevance-select(`selectInlineImages` top-cap by `relevance_score` + document-order)— T3/T4 unit + live relevance_score 數據背書
- [ ] 🚧 V5 — chat live 驗(**用戶動作**):chat 問 GL「post a journal entry」確認 ① 無裝飾燈泡 ② 8 張圖貼題(最相關)③ 文件次序 — 待用戶
- [x] V6 — 無 regression:decorative filter 只喺 dims 已知時觸發(0×0 legacy 保留)+ `selectInlineImages` ≤cap 時 return 原 document-order list;Finding D dedup + CH-008 文字 rerank 不受影響(orchestrator/citation-images 既有 test 全綠)(AC5)

## Closeout
- [ ] 🚧 C-1 — spec status → done;progress closeout retro — 待 V5
- [x] C-2 — ADR-0046 Proposed → Accepted(Chris 2026-06-08;README index 同步)
- [ ] 🚧 C-3 — commits 對應 Day-N(R2);ff-merge 入 main(用戶確認)— 待 V5 + merge go
