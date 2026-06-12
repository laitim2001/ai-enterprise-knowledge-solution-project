# ADR-0055: Inline image markers — B2 雙欄位 + per-KB 開關 + 交織顯示(逐字逐圖跟原文順序)

**Date**: 2026-06-12
**Status**: Accepted(雙 session 合併稿 — B2 機制 2026-06-12 口頭批;合併稿最終 Accept 2026-06-12)
**Approver**: Chris(技術 Lead)— 2026-06-12 拍板「Accept 但先只 commit 文件」;F2+ 實作留後續 session 開工

> **合併紀錄**:本 ADR 由兩個平行 session 嘅同題草稿合併(2026-06-12)。
> 機制骨幹(B2 雙欄位 + `[IMG#sha8]` 標記 + 驗證先行)承自 markers 稿;
> mockup reverse-drift 考證 + ADR-0054 cap 互動 + 顯示語意 + 結構限制精確化承自
> anchors 稿(該稿 `0055-inline-image-anchors-doc-order-interleaving.md` 已刪,
> 內容併入本檔)。

## Context

用戶 2026-06-12 方向指示:chat 答案要「無限接近地跟隨原文件內的文字和圖片的顯示
順序」— 而家係答案全文行先、所有 recall 圖片堆喺 message 末尾(inline 圖卡 cluster +
gallery),但 Drive 手冊原文係「每步驟後跟一張截圖」嘅閱讀流。

**Mockup 設計意圖本來就係 interleaved**(H7 reverse-drift):
`references/design-mockups/ekp-page-chat.jsx:443-500` 嘅 `AnswerBody` 把 `InlineImageCard`
手放喺引用佢嘅段落正下方(figure 1 跟住 step list、figure 2 跟住 checklist 段落),
末尾 gallery 只係總覽輔助。現行實作(`frontend/app/(app)/chat/page.tsx:1277-1287`
全部 inline card 集中喺答案末尾)係當時嘅近似 — 本 ADR 方向係行返埋 mockup 意圖。

**技術缺口**:答案文字係 GPT-5.5 合成,citation 標記 `[chunk-id]` 粒度係成個 chunk,
前端無從得知「答案邊一步對應原文邊張圖」。位置資料其實一早存在 — 每張圖有 parser
`doc_order`(ADR-0048),chunker 行 interleaved 事件流時(`layout_aware.py:193-202`)
知道每張圖喺邊段文字之後 — 但呢個 interleave 資訊喺 chunk 組裝時被丟棄(只留
side-list `embedded_image_positions`,`layout_aware.py:156`),synthesizer 對圖片
零感知(`prompt_builder.py` 無任何 image 指令)。

**三條 LLM 文字來源都要穿標記**(production 配置 per ADR-0052 parent_doc ON):
`prompt_builder._format_chunk` dispatch chain = `parent_section_text` > `expanded_text` >
`chunk_text`;sibling 聚合用 raw `chunk_text` 砌(`parent_doc_retriever.py:316`),
context expander 同樣。標記唔穿呢三條路 = production 下 LLM 根本見唔到。

**結構性限制**(預期校準):`citation_expansion`(W32 h')只插 `[chunk-{id}]` *marker*、
唔插文字(`citation_expansion.py:314-321`)— 呢條 post-hoc 路徑收割嘅 aux 圖,其原文
根本唔出現喺答案入面,**永遠冇得精準 anchor**,維持落 gallery。Parent / sibling 路徑
帶入嘅鄰居文字(連標記)則可以被 LLM 重現 → sibling 圖有機會 anchor 到。

## Decision

1. **B2 雙欄位**:`chunk_text` 保持 bit-identical;新增 index 欄位 `chunk_text_marked`
   (`searchable: false, retrievable: true`)— 圖片落點打 `[IMG#<checksum_sha256 前 8 hex>]`
   標記,只供 synthesis prompt 消費。檢索六消費者(BM25 `en.microsoft` / `content_vector`
   embedding / semantic ranker prioritized field / Cohere rerank / CRAG 評分 / RAGAs
   contexts)+ 第七個 `Citation.chunk_text` 前端顯示,全部唔見標記。

2. **標記語法 `[IMG#sha8]`(ingest 時寫死身份)**:chunker 以 `[IMG@<doc_order>]` 佔位
   (佢只知 position),orchestrator 用現有 `position_to_sha` 映射(`orchestrator.py:190-194`)
   改寫做 sha8;uploader 跳過嘅圖,標記同步剝走(同 `ImageRef` 落選條件一致)。
   sha8 跨 doc 全域唯一,直接對應前端 dedup key(`checksum_sha256`)— 查詢時零推斷、
   零歧義類別。

3. **per-KB 開關 `enable_inline_image_markers`**(global default `False`):行 ADR-0040 /
   ADR-0050 四層解析(per-query > per-DOC > per-KB > global)。Ingest 端**無條件**寫
   marked 欄位(純 data,無行為);開關只 gate 消費 — ON 時三條 prompt 文字路徑
   (parent_section_text / expanded_text / chunk_text)全部改用 marked 變體 + system
   prompt 附加「原位保留 `[IMG#...]` 標記,絕不自創」規則;OFF 時行為與現狀完全一致。

4. **現存 index PUT 遷移(re-ingest 前提)**:`to_search_doc()` 係 model_dump 全欄位
   上傳(`populate.py:209` + `schemas.py:89`)— 現存 index 冇新欄位會拒收任何 re-ingest。
   遷移 = 對現存 KB 重發 PUT(`create_index_for_kb` 同一 schema.json 路徑,additive
   field 合法);遷移前先 GET 現有 index 定義對照(防其他 drift 令 PUT 被拒);
   W70 只遷移 drive-images-1。

5. **驗證先行(兩段式)**:W70 只落基建 + 前端顯示層 strip(唔做交織 render);
   marker-placement 驗證集(九 query,四指標:validity / coverage / placement accuracy /
   dup rate)實測 LLM 錯位率,達標(自動評分錯位率 ≤ 3% 且人工抽查無誤導性錯配)
   先開 W71 前端交織 render。

6. **W71 交織 render 語意(已預鎖,2026-06-12 用戶確認)**:
   - marker 位 render mockup 現成 `InlineImageCard`(`ekp-page-chat.jsx:581-618`)—
     屬 **H7 reverse-drift**(mockup `AnswerBody` 本來就 inline 插圖),唔係 new-pattern
     proposal;實作仍受 H7 fidelity check 約束(元件 / class / spacing 照 mockup)。
   - 標記解析必須對 **post-attach / dedup / cap 嘅 surviving 圖集**(ADR-0054 預算結算
     之後)做 membership 驗證 — 圖被 cap 剪走 / sha8 無對應 → strip 標記,圖留 gallery,
     **永不 render 爛標記**。
   - **Anchored 圖唔再喺答案末尾 inline strip 重複出現;末尾 gallery 照舊全量總覽**
     (mockup 雙層設計)。LLM 漏標記 → 圖退回 gallery(= 今日行為,graceful)。

7. **實作排程**:W70 phase(`docs/01-planning/W70-inline-image-markers/`)= 基建 +
   strip + 驗證集;W71 = 交織 render(gated on 驗證達標)。Code GATED on 本 ADR
   最終 Accept per §5.1。Amends `architecture.md §3.3`(chunker 平行 marked 流)/
   `§3.5`(citation 合約 + 標記消費)/ `§3.6`(index schema 加欄位)/ `§3.7`(prompt rule)。

## Alternatives Considered

- **B1 單欄位(直接喺 `chunk_text` 打標記)** — Rejected:`chunk_text` 係單一欄位餵晒
  六個檢索消費者 + 前端顯示;標記污染令 R@5 0.9722 基線有不可事先證明嘅回退風險,
  token 計數改變會推移 chunk 切位(W44 chunker 校準作廢);rollback 要再 re-index 一次。
  B2 嘅旗標即關 rollback 強壓呢條路。
- **`[[img:doc_order]]` 標記留喺 index + post-synthesis doc-scope 解析**(anchors 稿
  原機制:答案合成後以「最近前置 citation 嘅 doc_id」推斷 doc-scope,解析 doc_order →
  checksum 再 rewrite)— Rejected:推斷喺多 doc 答案有歧義 failure class,而 sha8
  ingest 時寫死身份用現成 `position_to_sha` 成本近零、全域唯一、直接對應 dedup key;
  保留呢條路冇對應增益。
- **方案 A(段落級引用錨定,純前端)** — Not rejected,**降級為 fallback**:若 W70
  驗證集錯位率唔達標,W71 退守方案 A(零 LLM 依賴,確定性按 citation block 插圖,
  按 `doc_order` 排序)。粒度限制有實證:AR01-1 case 成個流程 = 單一 citation [21],
  全部 step 圖仍然 cluster,達唔到「逐字逐圖」— 所以只做 fallback 唔做終局。
  本 ADR 嘅 sha8 標記基建對方案 A 都有利(精確圖片身份映射)。
- **LLM 輸出側生成標記(唔改 ingest,prompt 俾圖片清單叫 LLM 自行決定落點)** —
  Rejected:LLM 唔知圖片喺原文嘅實際位置(alt_text 多數空),等於叫佢靠估;
  錯位率必然更高,且無 ground truth 可驗。
- **Vision / multimodal 圖文配對** — H4 Tier 2 禁區;reject。

## Consequences

- **Positive**:
  - 檢索層零影響 *by construction*(`chunk_text` / embedding / token 計數 bit-identical)
    — 唯一不可消除嘅殘餘風險收窄到「LLM 錯位標記」,且有驗證集量化 + 達標 gate。
  - 旗標即關 rollback(新欄位休眠,無需 re-index 回滾);未 re-index 嘅 KB 欄位為空 →
    自動 fallback 現有行為(graceful)。
  - Cited + parent/sibling 文字範圍內做到逐步逐圖 interleave;mockup `AnswerBody`
    設計意圖落地(H7 reverse-drift)。
- **Negative**:
  - **現存 index 必須 PUT 遷移加欄位**,否則任何 re-ingest 被拒收(Decision 4;
    W70 只遷移 drive-images-1)。
  - 開關 ON 時 prompt 實際 token 多過 `chunk_token_count` 記錄值(標記開銷,估每
    query 輸入 +500-1500 / 輸出 +100-200 tokens)— 已知偏差;對 ADR-0053 synthesizer
    timeout 120s 預算影響輕微,W70 實測覆核。
  - 答案文字含標記語法 → 顯示層要 strip(W70 含 streaming 半截標記 buffer);copy /
    export / RAGAs answer 評分嘅 strip 留 W71(DEFERRED_REGISTER 記 caveat;W71 RAGAs
    迴歸跑必須 strip-before-judge)。
  - 儲存層有圖 chunk 文字接近翻倍(369 chunks 規模,可忽略)。
  - Chunker 三條 flush / merge 路徑(`_flush_text_section` / `_add_paragraph` cap 內
    flush / `_force_flush_images`,加 `_merge_adjacent_shorts` 合併)要同步維護第二條
    文字流 — 實作面最大風險點,H6 測試 mandatory(chunker 屬必測 module)。
- **Neutral**:
  - aux / neighbour 圖兩類待遇唔同:parent / sibling 路徑帶到鄰居文字 → 有機會 anchor;
    post-hoc `citation_expansion` 收割嗰批(marker-only insertion)結構上永遠落 gallery
    — 限制非 regression。
  - 圖片預算語義(ADR-0054 dedup-before-cap)不受本 ADR 影響;標記解析只係喺結算後
    做 membership 驗證。

**驗收 gate**:
- **G1(W70)** placement 驗證集四指標;W71 go / no-go = 自動評分錯位率 ≤ 3% 且人工
  抽查無誤導性錯配。
- **G2(W70)** image-recall 九 query 重跑(knob ON),mean recall 相對 W68 基線(~1.00)
  跌幅 ≤ 0.02。
- **G3(W70)** 零回歸:knob OFF 下 prompt 內容 / `chunk_text` / token 計數 / embedding
  輸入 bit-identical;既有 test suite 全綠。
- **G4(W71)** RAGAs 4-metric(strip-before-judge)無迴歸 + H7 fidelity check 對
  mockup `AnswerBody` 逐項對齊。

## References

- Mockup(canonical):`references/design-mockups/ekp-page-chat.jsx:443-500`(`AnswerBody`
  inline placement)+ `:581-618`(`InlineImageCard`)
- Grounding:`backend/ingestion/chunker/layout_aware.py:153-167, 193-202`(image event /
  事件流)/ `backend/ingestion/orchestrator.py:190-194`(`position_to_sha`)/
  `backend/indexing/schemas.py:89` + `backend/indexing/populate.py:209, 253`
  (`to_search_doc` 全欄位 / `create_index_for_kb` PUT)/
  `backend/generation/prompt_builder.py:103-148`(dispatch chain)/
  `backend/generation/parent_doc_retriever.py:309-342`(sibling 聚合)/
  `backend/generation/citation_expansion.py:314-321`(marker-only insertion)
- ADR-0040 / ADR-0050(config-scope 四層解析)/ ADR-0041(切法 D image cap)/
  ADR-0048(per-image `doc_order`)/ ADR-0052(production default flip — parent 路徑
  必須支援 marked)/ ADR-0053(synthesizer timeout)/ ADR-0054(dedup-before-cap)
- `docs/01-planning/W70-inline-image-markers/plan.md`(實作切分 + AC + 驗證門檻)
- `architecture.md §3.3 / §3.5 / §3.6 / §3.7`(amends)
- 用戶方向指示 2026-06-12:「無限接近地跟隨原文件內的文字和圖片的顯示順序」+
  顯示語意確認(anchored 圖唔重複喺 strip;gallery 全量)
