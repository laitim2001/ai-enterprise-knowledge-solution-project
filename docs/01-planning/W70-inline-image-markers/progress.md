# W70 — progress(inline-image-markers)

## Day 1 — 2026-06-12

### 緣起 + 拍板
- 用戶提出 chat 顯示要「無限接近原文文字+圖片順序」(而家全文後先一批圖卡)。
- 評估兩級方案(A 段落級引用錨定 / B 逐步級標記交織)+ B 嘅兩個變體(B1 單欄位 /
  B2 雙欄位)後,用戶拍板:**B2 + per-KB 開關 + marker-placement 驗證集先行**。
- 風險評估關鍵結論:B1 會令標記污染檢索六消費者(BM25 / vector / semantic / rerank /
  CRAG / RAGAs),R@5 基線有不可預證嘅回退風險 → reject;B2 令唯一不可消除風險收窄
  到「LLM 錯位標記」,用驗證集量化先決定 W71 去向。

### R6 grounding(kickoff 當日,記入 plan 頭注)
- chunker `_SectionAccumulator` 冇 interleaved flow(paragraphs / image_positions 兩條
  獨立 list)— marked text 要加 ordered flow,三個 flush 點 + `_merge_adjacent_shorts`
  都要跟。
- `to_search_doc()` model_dump 全欄位 → **現存 index 唔加欄位會拒收 upload**;
  `create_index_for_kb` 係 PUT 全量 schema → 遷移 = 重發 PUT(additive 合法)。
- prompt 文字三條路徑(parent_section_text / expanded_text / chunk_text)都要 marked
  變體 — production default parent_doc ON(ADR-0052),漏咗 parent 路徑標記就唔會出現。
- 標記語法定為 `[IMG#sha8]`(orchestrator 用 `position_to_sha` 改寫 chunker 嘅
  `[IMG@doc_order]` 佔位)— 跨 doc 全域唯一,直接對應前端 dedup key。

### F1 — ADR-0055 ✅(雙 session 合併稿,見 commit)
- 兩個平行 session 同題草稿合併:機制骨幹維持 B2 + `[IMG#sha8]` + 驗證先行兩段式;
  anchors 稿三項併入 — (1) W71 交織 render 定性 = **mockup reverse-drift**
  (`ekp-page-chat.jsx:443-500` `AnswerBody` 本來就 inline 插圖);(2) 標記解析必須對
  ADR-0054 dedup/cap 後 surviving 圖集做 membership 驗證,爛標記 strip;(3) 顯示語意
  預鎖(用戶確認):anchored 圖唔重複喺末尾 strip,gallery 全量。anchors 稿檔案已刪併入。
- 合併稿三項 load-bearing 主張二次核實全部成立(`to_search_doc` 全欄位上傳 /
  `create_index_for_kb` PUT additive / `position_to_sha` 現成)。
- 標記機制裁決:採 **sha8-at-ingest**(棄 anchors 稿嘅 doc_order + post-synthesis
  doc-scope 推斷)— ingest 寫死身份零推斷歧義,理據記 ADR Alternatives。
- **Chris 拍板(2026-06-12):「Accept 但先只 commit 文件」— ADR + README + W70 plan
  套件 commit;F2+ code 下個 session 開工。**
