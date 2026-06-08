---
change_id: CH-009
title: "Chat image relevance + quality — decorative filter + cap strategy + query-relevance ordering"
status: approved       # draft | approved | done
adr_ref: ../../../adr/0046-chat-image-relevance-decorative-dims.md
affects_components: [C01, C03, C05, C10]   # C01 Ingestion (dims probe + decorative flag) · C03 Indexing (ImageRef schema populate) · C05 Generation (image ordering) · C10 Chat UI (cap wiring + ordering)
spec_refs:
  - architecture.md §3.3 / §3.5 (ingestion / ChunkRecord ImageRef)
  - architecture.md §3.6 (index schema)
  - ADR-0034 (neighbour image attach) · BUG-026 (image dedup + source_section) · BUG-027 (section-aware attach) · BUG-031 (INLINE_IMAGE_CAP)
---

# CH-009 — Chat image relevance + quality

> **接 BUG-034 問題1 圖片維度**(CH-008 文字 rerank 已修復 + merged 2026-06-08;文字 13/13 citation 全部錨 GL03)。本 CH 處理 chat 答案**圖片**側嘅三個質素問題。**Status draft — code GATED on user approve + ADR Accept(H1/H4 涉及)。**

## 1. Problem(2026-06-08 live 診斷,drive-images-1 GL「post a journal entry」)

三個獨立子問題(全部圖 `source_section` 正確喺 GL03 §3.1.x — **非 recall 錯章節**;係圖片**質素 + presentation**):

1. **裝飾 icon surface 成 figure**:手冊嘅「Tip/Note/idea」燈泡 icon 被 surface 成 figure 4。Root:`ScreenshotExtractor.extract` 抽晒所有 embedded image(含裝飾 icon),`ScreenshotRecord.width/height` 從來冇 populate(`/query` 實測所有圖 `0x0`)→ 無 size 信號可 filter。`InlineImageCard` 亦無 onError fallback(確認燈泡係真實 render 嘅圖,非 broken placeholder)。
2. **完整性 / cap 截斷**:`INLINE_IMAGE_CAP=8`(frontend 常數,BUG-031 user-approved 2026-06-01)。去重後 30+ unique GL03 圖按 `section_path` 字串排序(Finding D)後 slice 頭 8 → 後段 figure 入「View all in Image Library」。用戶感知「跳/漏」。
3. **無 query-相關性排圖**:圖只按 section/chunk 次序 dump(Finding D 文件次序),冇按 query 相關性。手冊每 step 有大量相似截圖 → 攞到嘅 8 張偏隨機。

## 2. Scope(三項 + 設計選項)

### I-A — 裝飾 icon 過濾(#1)
- **Probe dims**:`ScreenshotExtractor.extract` 時解 PNG IHDR header 拎 width/height(**stdlib `struct`,零新 dep,避 H2**;非 PNG 走 best-effort / skip)→ populate `ScreenshotRecord.width/height` → 落 `ChunkRecord` ImageRef + index `embedded_images_json`。
- **Decorative filter**:`min(width,height) < THRESHOLD`(建議 64px)或 area < THRESHOLD² 視為裝飾 icon。**過濾位置決策**(見 §5 OD-1):ingest 時 drop vs 存 `decorative` flag + 查詢/display 時 filter(建議後者 — 保留資料、可調、可 audit)。
- **Re-index**:要 re-ingest `drive-images-1` 先 populate dims(in-place,同 CH-008 V2)。

### I-B — cap 策略(#2)
- `max_images_per_answer` config 欄位**已存在**(`KbConfig`,drive-images-1 = null = 全域 default)。Wire frontend `INLINE_IMAGE_CAP` → 讀 per-KB `max_images_per_answer`(經 `/query` response 或 KB config),null fallback 8。
- **決策**(OD-2):default cap 值 + per-KB 可配 vs 純調大常數。

### I-C — query-相關性排圖(#3)
- **H4 邊界硬規**:**只用文字 chunk 信號**(owning citation 嘅 `relevance_score` / section 匹配 top citations),**嚴禁 image embedding / multimodal**(純圖片搜索 = Tier 2,H4 禁)。
- **Approach**:圖片按 owning citation `relevance_score` 排序(最相關 chunk 嘅圖先)→ cap 揀最相關 N 張。
- **Tension(OD-3)**:同 Finding D「按文件次序排圖」(BUG-026/034 user-pick)衝突。Resolution 選項:(a) relevance 決定**邊幾張入 cap**、document-order 決定 cap 內**顯示次序**;(b) per-KB toggle relevance vs document order;(c) 全改 relevance。建議 (a)。

## 3. Acceptance Criteria(draft — 待設計鎖定後 finalize)
- AC1 — `drive-images-1` re-index 後 ImageRef 帶真實 width/height(非 0)。
- AC2 — 裝飾 icon(燈泡 < threshold)唔再 surface 成 figure(GL query 圖片無燈泡)。
- AC3 — cap 可經 per-KB `max_images_per_answer` 控制(null fallback 現行 8)。
- AC4 — GL query inline cap 內圖片 = 首 N 張(document-order,Finding D)→ §3.1.1 章節概覽圖(High Level Process)lead,照手冊流程 start→end(OD-3 reverted:非 relevance order)。
- AC5 — 無 regression:text-only KB / 無圖 KB 行為不變;Finding D dedup 仍 work;CH-008 文字 rerank 不受影響。
- AC6 — backend pytest(ingestion + generation)+ frontend lint/test pass + ruff + mypy 改檔 0 新 error。

## 4. H1 / H4 / ADR flags
- **H1**:ingestion dims probe + decorative filter(§3.3/§3.5)+ ImageRef populate(§3.6)+ image ordering(C05 pipeline)= 改 documented behavior → **需 ADR**(暫定 ADR-0046)。
- **H4**:#3 相關性排序**只准文字信號**;image embedding/multimodal = Tier 2 禁區。ADR 明文記呢條邊界。
- **H7**:#1 #2 #3 改 chat 圖片呈現,涉 frontend → mockup fidelity 對齊;cap/裝飾過濾若偏離 mockup 需 H7 surface(BUG-031 cap 本身已係 H7-deviation user-approved 先例)。

## 5. Locked Decisions(Chris 2026-06-08)
- **OD-1 ✅**(#1 過濾位置):**存 `decorative` flag + display filter**。ingest probe PNG 尺寸 + 標 `decorative`(`min(width,height) < 64px`)→ 圖照存 index → chat display 時 filter 走。保留資料 / threshold 可調 / 可 audit / 可 per-KB override。要 re-index drive-images-1 populate dims。
- **OD-2 ✅**(#2 cap):**Wire per-KB `max_images_per_answer`**。frontend cap 讀 per-KB config,`null` fallback 維持 8。
- **OD-3 ⚠️ REVERTED 2026-06-08**(#3 排序):原鎖定「relevance 揀圖 + 文件次序顯示」,但 live 驗揭 **relevance-select 把低 rerank 分數嘅 §3.1.1 章節概覽圖(High Level Process,score 0 expansion neighbour)排出 cap**,令 lead 變成高分嘅 mid-procedure step 圖(§3.1.4)。用戶反饋:程序手冊應由概覽圖(page 20)行先。**改回純 document-order(Finding D)+ cap** —— `selectInlineImages = deduped.slice(0, cap)`,概覽圖照文件次序 lead。relevance-select code(`relevanceScore` 追蹤 + relevance sort)移除。decorative filter(OD-1)+ per-KB cap(OD-2)保留。

## 6. Risks
- **R1**:re-index `drive-images-1` 期間短暫不可查(同 CH-008 V2,in-place)。
- **R2**:decorative threshold 太鬆/太緊 → 誤殺真圖 / 漏放 icon;靠 live 驗 + threshold 可調緩解。
- **R3**:relevance 排序改動 image presentation → 對齊 H7 mockup;BUG-031 cap deviation 先例可循。
- **R4**:dims probe 對非 PNG / 損壞圖 → best-effort,失敗 fallback None(不阻 ingest)。

## 7. Changelog
| Date | Change | Reason |
|---|---|---|
| 2026-06-08 | spec draft 建立 | Chris 揀「一個 CH 三項一齊」處理 BUG-034 問題1 圖片維度(CH-008 文字已 merged);待 OD-1/2/3 鎖定 + ADR |
| 2026-06-08 | draft → approved;OD-1/2/3 鎖定 | Chris 鎖定:OD-1 decorative flag + display filter(64px)/ OD-2 wire per-KB max_images_per_answer / OD-3 relevance 揀圖 + 文件次序顯示。ADR-0046 Proposed 待 Accept(H1 code gate) |
| 2026-06-08 | 實作 + V2/V3 PASS | I-A dims probe + decorative filter + I-B per-KB cap + I-C(OD-3)落地;re-index drive-images-1;V3 `/query` 40 unique 0 dims-miss、93×62 燈泡判 decorative |
| 2026-06-08 | **OD-3 REVERTED → 純 document-order**(Chris 確認) | live 驗:OD-3 relevance-select 把低分(score 0)§3.1.1 章節概覽圖排出 cap,lead 變 §3.1.4 step;用戶要概覽圖(page 20)行先。`selectInlineImages` 改 `slice(0,cap)`;移除 relevanceScore + relevance sort;decorative(OD-1)+ cap(OD-2)保留。vitest 21 + tsc clean。**同時開 BUG-035 修 conversation kb_id 綁定**(揀 DRIVE reopen 變 DCE) |
