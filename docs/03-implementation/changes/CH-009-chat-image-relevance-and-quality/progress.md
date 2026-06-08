---
change_id: CH-009
spec_ref: ./spec.md
checklist_ref: ./checklist.md
status: in-progress     # in-progress | closed
---

# CH-009 — Progress

> Day-N entries + closeout。每 commit 對應 Day-N mention(R2)。

---

## Day 1 — 2026-06-08

### Context
接 BUG-034 問題1 **圖片維度**(CH-008 文字 rerank 已 merged `34c5d7c` — chat 13/13 citation 錨 GL03)。Live 診斷(drive-images-1 GL「post a journal entry」`/query` 重現)揭三個圖片質素問題,全部圖 source_section 正確喺 GL03(非 recall 錯):① 裝飾燈泡 icon surface 成 figure(所有圖 `0x0` — dims 從來冇 populate)② `INLINE_IMAGE_CAP=8` 截斷 ③ 無 query-相關性排圖。Chris 揀「一個 CH 三項一齊」。

### Done(kickoff)
- ADR-0046 寫(Proposed → **Accepted** Chris 2026-06-08)+ 入 ADR index(next NNNN=0047)。
- CH-009 spec(approved;OD-1/2/3 鎖定)+ checklist + progress committed。

### Done(implementation,ADR Accept 後)
- **I-A 後端**:`extractor.py` `probe_png_dimensions`(stdlib `struct` IHDR,零新 dep)+ `extract` populate `ScreenshotRecord.width/height`;`orchestrator.py` `sha_to_dims` → `ImageRef(width,height)`。`parse_embedded_images` 早讀 width/height(無需改)。
- **I-A A3 + I-B + I-C 前端**(display 層):`citation-images.ts` `isDecorativeImage`(min<64,dims 已知先判)+ `dedupeCitationImages` skip decorative + track `relevanceScore`(max across citations)+ `selectInlineImages(deduped, cap)`(top-cap by relevance → document-order);`chat/page.tsx` cap = `maxImagesPerAnswer ?? INLINE_IMAGE_CAP`,`ChatThread`/`MessageRow` thread per-KB `max_images_per_answer`。
- **Tests**:`test_ch009_image_dims.py`(9)+ `citation-images.test.ts`(+8 → 22 total)。
- **I7 docs**:architecture.md §3.6 CH-009 amendment + C01 + C10 design note bump。
- **V1**:backend pytest 21 + frontend vitest 22 + tsc clean + ruff clean + mypy 改檔 0 新 error(16 pre-existing docling)。
- **V2**:`drive-images-1` re-index 6/6,369 chunks(dims probe 生效)。
- **V3 AC1+AC2 PASS**(`/query` live):40 unique images,**0 個 dims=0**;**1 個 93×62(min 62<64)= 燈泡 → 前端 filter**;39 內容圖(min≥237)保留;閾值 64 穩坐 62-vs-237 gap。
- **V4 AC3+AC4**:cap per-KB + relevance-select,由 T3/T4 + live relevance_score 背書。

### Decisions(Chris 2026-06-08 鎖定)
- **OD-1**:decorative flag + display filter(probe PNG IHDR 尺寸,stdlib 零新 dep;`min(w,h)<64px` 標 decorative;圖照存,display filter 走)。要 re-index drive-images-1。
- **OD-2**:wire per-KB `max_images_per_answer`(欄位已存在;null fallback 8)。
- **OD-3**:relevance 揀圖(owning citation `relevance_score`)+ document-order(Finding D)顯示。**H4 硬邊界:文字信號 only,無 image embedding**。

### Decisions / Notes(implementation)
- **A3 decorative filter 定位 = frontend display**(非 backend):圖照存 index(dims 落 `embedded_images_json`),display 時 filter → 符 OD-1「圖照存」+ 同 dedup/cap/relevance display 邏輯 co-locate。
- **Backend `cap_images_per_answer` interaction**:query.py 已有後端 per-KB payload cap(`effective.max_images_per_answer`)。drive-images-1 該值 = null → 後端 no-op → 前端攞完整 set → relevance-select 全效。**已知限制**:若某 KB 設 `max_images_per_answer`,後端會先 blunt citation-order trim,前端 relevance-select 只能喺 trim 後嘅 set 揀(degraded)。本期 test KB null 不觸發;若日後設值要 full relevance-select,後端 cap 需改 relevance-aware(留 follow-up,Karpathy §1.2 不提前 over-engineer)。

### OD-3 REVERT(2026-06-08,Chris 確認)
- 用戶 V5 揭兩問題:① conversation 揀 DRIVE reopen 變 DCE(→ 開 **BUG-035**)② chat 圖 lead 變 §3.1.4 step 而非 §3.1.1 章節概覽圖(High Level Process,page 20)。
- 根因 ②:**OD-3 relevance-select reverse 咗 Finding D** —— §3.1.1 概覽 chunk rerank score=0(expansion neighbour),relevance-select 把佢排出 cap。程序手冊正確 image 流程 = document order(概覽 → step)。
- **Fix**:`selectInlineImages` 改 `deduped.slice(0, cap)`(純 document-order);移除 `relevanceScore` + relevance sort + maxRelevance pass。decorative filter(OD-1)+ per-KB cap(OD-2)保留。vitest 21 passed + tsc clean。
- ADR-0046 加 post-Accept amendment(Decision #3 reverted);spec / architecture.md §3.6 / C10 同步。
- **教訓**:relevance-select 對「最相關片段」啱,但對「程序流程圖」錯(低分但 pedagogically-first 嘅概覽會被排走)→ document-order 先啱。

### Blockers / Carry-over
- 🚧 **V5 chat live 驗**(用戶):chat 問 GL 確認 ① 無燈泡 ② 概覽圖(§3.1.1 High Level Process)lead ③ 照文件次序。
- 🚧 **C-1 / C-3 closeout**:spec done + ff-merge,待 V5 + merge go。
- 🔵 **BUG-035**(NEW):conversation kb_id 綁定 —— `handleNewChat` eager-create 用 default kbId(kbs[0]=DCE archived),切 KB 後只靠 submit re-bind;robust fix = onKbChange 即時 re-bind active conv 或 defer 建立到首 submit。獨立 bug。

### Effort
- Planned ~1-1.5 day;Actual:_(填)_

### Commits
| Hash | Subject |
|---|---|
| _(待)_ | docs(adr+change): ADR-0046 + CH-009 kickoff — chat image relevance |

---

**End of CH-009 progress (Day 1 — kickoff;code gate pending ADR-0046 Accept)**
