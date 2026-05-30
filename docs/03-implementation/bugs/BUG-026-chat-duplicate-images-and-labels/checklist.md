---
bug_id: BUG-026
report_ref: ./report.md
status: in-progress
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
- [ ] 🚧 (user-facing)Manual UI verify —— **deferred**:需 demo KB 重新 ingest(blobs 隨 demo 清理已刪);code + Vitest + build 層已驗,UI 層待有 live KB 時 user 確認

## Finding B / C(非主修)

- [x] Finding B documented 為 mockup-faithful(gallery `chunk_title` 不動,改 = H7 violation)
- [ ] 🚧 Finding C(per-image caption ingest 深度)待 user 決策 (a)/(b)/(c) per `report.md §6`

## Closeout

- [ ] `progress.md` closeout summary(timeline + root cause + lessons)
- [ ] (Sev3 → postmortem 非強制,pattern recurring 先寫)
- [ ] `report.md` status 翻 `done`
- [ ] `progress.md` status 翻 `closed`

---

## Cross-Cutting

- [ ] 每 commit 對應 `progress.md` Day-N entry(R2)
- [ ] Commit message component tag `fix(frontend): … (C10)`(CC-1)
- [ ] (非 architectural fix → 無 ADR)
- [ ] (無 OQ 依賴)
