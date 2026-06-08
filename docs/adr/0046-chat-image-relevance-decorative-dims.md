# ADR-0046: Chat image relevance — decorative filter + dims probe + query-relevance ordering

**Date**: 2026-06-08
**Status**: Accepted
**Approver**: Chris

> **Amendment 2026-06-08(post-Accept,Chris)**:**Decision #3(query-relevance ordering)REVERTED → 純 document-order**。Live 驗揭 relevance-select 把低 rerank 分數(score 0,expansion neighbour)嘅 §3.1.1 章節概覽圖(High Level Process)排出 cap,令 chat lead 變成高分 mid-procedure step 圖(§3.1.4)。程序手冊嘅正確 image 流程 = 照 document order(概覽 → step),概覽圖必須 lead。`selectInlineImages` 改為 `deduped.slice(0, cap)`(純 document-order + per-KB cap),移除 relevance sort。**Decision #1(decorative filter)+ #2(per-KB cap)維持**。教訓:relevance-select 對「最相關片段」有用,但對「程序流程圖」係錯方向(document-order 先啱)。

## Context

BUG-034 問題1 嘅**圖片維度**(CH-008 已修復文字 rerank — chat 答案 13/13 citation 全部錨 GL03;merged 2026-06-08 `34c5d7c`)。Live 診斷(drive-images-1,GL「post a journal entry」,`/query` 重現)揭三個**圖片質素 / presentation** 問題(全部圖 `source_section` 正確喺 GL03 §3.1.x — **非 retrieval recall 錯**):

1. **裝飾 icon surface 成 figure**:手冊「Tip/Note/idea」燈泡 icon 被 surface 成 figure。Root:`ScreenshotExtractor.extract` 抽晒所有 embedded image(含裝飾 icon);`ScreenshotRecord.width/height` 從來冇 populate(`/query` 實測所有圖 `0x0`)→ 無 size 信號可 filter。`InlineImageCard` 無 onError fallback(確認係真實裝飾圖,非 broken placeholder)。
2. **cap 截斷**:`INLINE_IMAGE_CAP=8`(frontend 常數,BUG-031 user-approved)。30+ unique GL03 圖按 `section_path` 排序(Finding D)後 slice 頭 8 → 後段入 Image Library。
3. **無 query-相關性排圖**:圖只按 section/chunk 次序 dump(Finding D 文件次序),冇按 query 相關性 → 手冊每 step 大量相似截圖令攞到嘅 8 張偏隨機。

呢三項改 ingestion(dims probe + decorative flag,§3.3/§3.5)+ index ImageRef populate(§3.6)+ image ordering pipeline(C05)→ 觸發 **H1**。#3 相關性排序觸及 **H4 邊界**(multimodal / 純圖片搜索 = Tier 2)→ 必須明文約束。

## Decision

三項改動,**全部用現有 Tier 1 stack + 文字信號**,零新 vendor / 零 multimodal:

1. **Dims probe + decorative filter(OD-1)**
   - `ScreenshotExtractor.extract` 解 PNG IHDR header(**stdlib `struct`,零新 dep**;非 PNG / 損壞圖 → best-effort `None`,不阻 ingest)→ populate `ScreenshotRecord.width/height` → 落 `ChunkRecord` ImageRef + index `embedded_images_json`。
   - 標 `decorative` flag:`min(width,height) < 64px`(可調 / per-KB override 預留)。
   - 圖**照存**(保留資料 + audit);**chat display 時** filter 走 decorative → 燈泡唔再 surface。
   - 要 re-index 受影響 KB(本期 `drive-images-1`,in-place)populate dims。

2. **Per-KB cap wiring(OD-2)**
   - frontend `INLINE_IMAGE_CAP` 改讀 per-KB `KbConfig.max_images_per_answer`(欄位已存在;`null` fallback 維持 8)。每 KB 可自調圖片密度。

3. **Query-relevance image ordering(OD-3)**
   - 圖片按 **owning citation `relevance_score`**(Cohere 文字 rerank 分數)決定**邊幾張入 cap**(最相關 chunk 嘅圖先);cap 內按 **document-order(Finding D / `section_path`)顯示**。
   - **H4 硬邊界**:相關性**只用文字 chunk rerank 信號**,**嚴禁 image embedding / 純圖片 multimodal 檢索**(= Tier 2,H4 禁)。

## Alternatives Considered

- **#1 ingest 時直接 drop decorative**:慳空間但不可逆、threshold 改要 re-ingest、無 audit。Reject — 揀 flag + display filter(可調、可逆)。
- **#2 純調大 INLINE_IMAGE_CAP 常數**:全域一刀切,唔對齊 per-KB tunable config 方向。Reject — wire 已存在嘅 per-KB `max_images_per_answer`。
- **#3 全改 relevance order**:放棄 Finding D 文件次序(BUG-026/034 user-pick)。Reject — relevance 揀圖 + document-order 顯示兩者並存(OD-3 a)。
- **#3 image embedding / multimodal rerank**:技術上可按圖片內容排序,但 = Tier 2 純圖片搜索(H4 禁)+ 需新 vendor(H2)。Reject — Tier 1 只用文字信號。
- **改 chunker / OCR 圖內文字**:重 + 唔解 presentation 層。Reject。

## Consequences

- **Positive**:裝飾 icon 唔再污染 figure;圖片密度 per-KB 可控;最相關 step 圖優先入 cap → 用戶見到嘅圖更貼題;全部 Tier 1 文字信號 + 零新 dep / vendor。
- **Negative**:要 re-index 受影響 KB populate dims(Free-tier 3-slot,本期只 drive-images-1);decorative threshold 需 live 校(太鬆漏 icon / 太緊誤殺真圖);改 image presentation 需對齊 H7 mockup。
- **Neutral**:stored 圖片 + Finding D dedup 不變(decorative 只喺 display filter);CH-008 文字 rerank / citation 不受影響;`max_images_per_answer` null fallback 保現行 8 → 未配 KB 零行為改變。

## References

- BUG-034 問題1(圖片維度;CH-008 解文字層)/ CH-009 spec(本 ADR 實作 change)
- ADR-0034(neighbour image attach)/ BUG-026(image dedup + source_section)/ BUG-027(section-aware attach)/ BUG-031(INLINE_IMAGE_CAP user-approved cap)
- ADR-0040(per-KB tunable config — `max_images_per_answer` 屬其一)
- architecture.md §3.3 / §3.5(ingestion / ChunkRecord ImageRef)/ §3.6(index schema)
- H4(Tier 2 multimodal 邊界)/ H1(image pipeline documented behavior change)
