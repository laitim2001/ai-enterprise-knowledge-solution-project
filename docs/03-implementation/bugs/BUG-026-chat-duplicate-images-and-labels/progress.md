---
bug_id: BUG-026
report_ref: ./report.md
checklist_ref: ./checklist.md
status: in-progress
---

# BUG-026 — Progress

> Investigation → fix → verify timeline。
> 每 commit 必須對應一個 Day-N entry mention(R2 binding rule per PROCESS.md §5)。

---

## Day 1 — 2026-05-30

### Done
- 由 W42 post-closeout UI demo follow-up（memory `project_chat_demo_rag_quality_followups`）開 bug task
- Code-trace 3 個 root cause finding(無 live repro —— demo KB `dce-integration-demo-1` 已喺 demo 清理刪除)
- 寫 `report.md`(Sev3,3-finding 診斷)+ `checklist.md`
- **Finding A fix 實作**:
  - NEW pure helper `frontend/lib/chat/citation-images.ts::dedupeCitationImages`(key `checksum_sha256` fallback `blob_url`,首現 citation attribute,full-citations `citationIdx`)
  - `chat/page.tsx`:import helper + `dedupedImages = dedupeCitationImages(message.citations)`;inline cards + ImageGallery + FeedbackBar count 全部改由 deduped 列表 drive;ImageGallery 簽名 `citations`/`allCitations` → `images: DedupedCitationImage[]`(label 保持 mockup-faithful `chunk_title`+`doc_title` per Finding B)
  - `imageCitations` 保留(meta row「N with screenshots」= citations 數,語意正確)
- **NEW test** `tests/unit/citation-images.test.ts`(6 cases)
- **驗證全綠**:Vitest 13 passed(6 新 + 7 既有 `chat-meta-row` 無 regression)/ ESLint clean(唯一 pre-existing `<img>` warning)/ `tsc --noEmit` exit 0 / `npm run build` exit 0(✓ Compiled,15 頁)/ Prettier clean

### Diagnosis update
- **Finding A**(dedup,真 bug):`attach_neighbour_images`（`citation_image_neighbors.py`）跨 citation 無 dedup → 同 `checksum_sha256` 圖落多個 citation;frontend `chat/page.tsx` inline cards(1228-1245)+ gallery(1796)兩處 flat render 無 dedup
- **Finding B**(gallery label = `chunk_title`):code-trace 對 mockup `ekp-page-chat.jsx:653-656` —— **mockup 本身就用 chunk_title + doc_title**(source attribution),所以唔係 bug,改成 alt_text = H7 violation → 不動
- **Finding C**(per-image 真 caption):`alt_text` = ingest Docling caption(`docx_parser.py:117`);有 caption 時 inline title 已正確,無 caption fallback chunk_title;真 fix 屬 ingest 層 + overlap BUG-017 + 需 re-ingest + live 驗 alt_text → 待 user 決策

### Decisions
- Finding A dedup 位置 = **frontend display dedup**(report §8 Alt 1)—— presentation 層問題喺 presentation 層解;保留 backend citation↔image data 完整;contained 喺 chat page
- Finding B 保持 mockup-faithful(§13 mockup wins)
- Finding C 唔自行做 ingest 深度工作(較大 + 需 re-ingest + 需 live 驗證)→ STOP+ask user 方向

### Blockers
- Manual UI verify 需 demo KB 重新 ingest(blobs 已隨 demo 清理刪除)—— code + Vitest 層先驗,UI 層 user-deferred

### Effort
- Planned:0.5h(dedup fix);Actual:_(進行中)_;Variance:_

### Commits
| Hash | Subject |
|---|---|
| _(pending)_ | fix(frontend): BUG-026 dedup cross-citation duplicate images in chat (C10) |

---

## Closeout(填於 status=closed)

_(待 Finding A fix + verify 完成)_
