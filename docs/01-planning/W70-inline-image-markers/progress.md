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

## Day 1(同日續,session 2)— 2026-06-12

### F2 — chunker marked-text 流 ✅
- `_SectionAccumulator` 加 `flow: list[tuple[str, str]]` — `("para", text)` /
  `("img", "[IMG@<doc_order>]")` 按 doc_order 入列,同 `paragraphs` /
  `image_positions` 平行鏡像;**乾淨 `chunk_text` 組裝路徑一行未郁**(diff 證:
  layout_aware.py 被改嘅 5 行全部係 `_build_text_chunk` call site 加 `flow` 參數)
  → G3 bit-identical by construction。
- `ChunkSpec.chunk_text_marked`(default `""`)— 無標記 chunk 留空,下游
  `marked or chunk_text` fallback,慳儲存 +「有值 = 有標記」語義清晰。
- 出 chunk 位共 **5 個**(plan 講三個 flush 點之外,實際多兩個)全部接 flow:
  (1) `_flush_text_section`(2) hard-cap pre-flush(3) soft-target flush
  (4) `_force_flush_images`(5) **oversized standalone 段落** — 第 5 個跟現有
  image snapshot 語義(袋走 acc 嘅 marker 但唔 reset,residual tail 會重複,
  同 `embedded_image_positions` double-attach 行為平行一致,pre-existing 唔郁)。
- flow 重置語義跟 `_reset_images_on_flush`:cap 設 → 全清;cap=None(pre-W44
  pile-on)→ 保留 img 事件,marker 喺後續 sub-chunk 重現,同 image list 鏡像。
- `_merge_adjacent_shorts`:marked 平行合併;marker-less 一側以乾淨 `chunk_text`
  fallback 拼入,merged marked 流保持完整;兩側都無標記 → `""`。
- Tests:9 條新(exact interleave 斷言 / chunk_text 永不含 marker + token 計數
  以乾淨文字計 / 無圖留空 / soft-target flush 重置 / hard-cap pre-flush 邊界 /
  切法 D batch 對應 `embedded_image_positions` / oversized snapshot / merge
  fallback / cap=None pile-on 鏡像)。chunker 48 全綠;連 ChunkSpec 消費者
  (test_orchestrator / test_ch009_image_dims / test_contextual_retrieval_ch008)
  共 **75 passed**。
- Lint:ruff check 全過;layout_aware.py format clean;test_chunker.py 只
  range-format 新增 W70 section(檔案其餘部分 pre-existing 唔 format-clean,
  per Karpathy §1.3 唔全檔 reformat);mypy --strict 新 code 零新 error
  (layout_aware.py:125/184 `ev` assignment + parsers docling typing 全部
  pre-existing)。
- 下一步:F3 orchestrator sha8 改寫 + `ChunkRecord` 欄位 + `schema.json` +
  drive-images-1 index PUT 遷移(記住先 GET 對照)。

### F3 — orchestrator sha8 改寫 + index schema + live 遷移 ✅
- orchestrator 新增 module function `_rewrite_image_markers`:`[IMG@<doc_order>]` →
  `[IMG#<sha8>]`(`position_to_sha` + `sha_to_url` 雙重 lookup,**剝走條件同
  `ImageRef` 落選條件完全一致** — marker 永遠對應 live 圖);剝走後空段收斂
  (`\n{3,}` → `\n\n`);無 marker 殘存 → 整欄退化 `""`(維持「有值 = 有標記」)。
  `extract_embedded_images=False` / `uploader=None` 時 `sha_to_url` 空 → marker
  全剝 → `""`,同無圖行為自然一致。
- `ChunkRecord.chunk_text_marked: str = ""` — `to_search_doc` model_dump 自動帶,
  零 serialization code 改動。
- `schema.json` 加 `chunk_text_marked`(`searchable: false, retrievable: true`
  per ADR-0055 — 檢索六消費者唔見標記)。
- **live 遷移(drive-images-1)**:臨時 script 先 GET `ekp-kb-drive-images-1-v1`
  定義對照 — 結構 drift **零**(首輪報嘅 4 項係假陽性:local schema.json 對
  Int32 / DateTimeOffset 冇明寫 `searchable`,Azure GET 回傳 explicit default
  `False`,PUT 同樣填 default 唔構成衝突);唯一 additive = 新欄位 → PUT 經
  production path `create_index_for_kb("drive-images-1")` 成功;post-GET 驗證
  欄位已落(searchable=False / retrievable=True)+ **doc count 369 → 369 不變**。
  其餘 KB 嘅 index 未遷移(per plan 非目標;re-ingest 前要先 PUT — 已知 gate)。
- 遷移 script 用 `truststore.inject_into_ssl()`(同 `api/server.py` 一致,
  corporate TLS interception 環境必須;系統 httpx 直連會 SSL 驗證失敗)。
- Tests:orchestrator 4 條新(sha8 改寫 / 缺 sha 剝走 + 收斂 / 無 marker 殘存
  退化 `""` / marker-less passthrough)+ populate 2 條新(`to_search_doc` keys ==
  schema.json field set **對齊 guard**(R2 drift 防護,以後加欄漏 schema 即紅)/
  marked 值 ride-through)。相關 suites 104 passed。
- 下一步:F4 config 開關(settings default + KbConfig knob + effective_config
  四層解析)。

### F4 — config 開關(四層解析)✅
- `Settings.enable_inline_image_markers: bool = False`(global default OFF —
  消費 gate only;ingest 端無條件寫 marked 欄位 per ADR-0055 Decision 3)。
- `KbConfig.enable_inline_image_markers: bool | None = None`(None = 繼承 global;
  query-time knob,flip 唔使 re-index,但該 KB index 要有 marked 數據先會出標記
  — 未 re-index KB 欄位空 → 自然 fallback 乾淨文字)。
- `DocConfig` 同步加(ADR-0055 Decision 3 寫明四層 per-query > per-DOC > per-KB
  > global;knob 屬 synthesis prompt 消費 = post-retrieval,符合 ADR-0050
  per-DOC 層「dominant cited doc 已知先消費」邊界)。
- `effective_config.py`:`PerQueryOverrides` + `EffectiveConfig`(concrete bool)+
  `resolve_effective_config` 行 `_resolve(pq, _layer(dc, kb), global)` 標準鏈。
- `DraftRetrievalConfig`(config-test 試跑 draft)**刻意唔加** — DD-5 precedent
  係按需加;harness 嘅 counter(citation / figure / latency)反映唔到 marker
  效果,W71 交織 render 落地先有意義。
- Tests 5 條新:global OFF 繼承(kb=None + 空 KbConfig 雙 case)/ per-KB ON 覆寫
  / per-DOC 蓋 per-KB / per-query 最優先 / 舊 config dict 缺 key → None → 繼承
  OFF(ADR-0028 migration-default precedent)。effective-config 28 + per-KB
  consumer + config-test 合計 73 passed;ruff 全過。
- 下一步:F5 三條 prompt 路徑(`prompt_builder._format_chunk` dispatch +
  `parent_doc_retriever` + `context_expander` marked 變體 + system prompt rule)。
