---
phase: W70
name: inline-image-markers
status: active       # draft | active | closed
created: 2026-06-12
owner: "Claude (AI) — 技術 Lead Chris 審閱"
gap: "chat 答案文字同圖片分離(全文後先一批圖卡 + gallery),唔跟原文「步驟後跟截圖」嘅閱讀流;要起「答案文字 ↔ 原文圖片位置」嘅映射基建,先可以做 W71 交織顯示"
adr: "ADR-0055(B2 雙欄位 inline image markers + per-KB 開關)— H1 觸發:index schema 加欄位 + ingest 內容衍生欄位"
spec_refs:
  - docs/adr/0055-inline-image-markers-b2-dual-field.md
  - docs/adr/0048-per-image-doc-order-and-document-span-selection.md   # doc_order 基建
  - docs/adr/0040-per-kb-tunable-retrieval-config-scope.md             # per-KB knob 機制
  - docs/adr/0054-dedup-before-cap-image-budget.md                     # 圖片預算語義(不受本 phase 影響)
---

# W70 — inline image markers(B2 雙欄位)+ per-KB 開關 + marker-placement 驗證集

> **緣起**:用戶 2026-06-12 提出 chat 顯示要「無限接近原文文字+圖片順序」。評估後拍板
> 方案 B 變體 B2:`chunk_text` 保持 byte-identical(檢索層零污染),另加 `chunk_text_marked`
> 欄位(圖片落點打 `[IMG#<sha8>]` 標記)只供 synthesizer prompt 用;per-KB 開關 gate;
> 先起 marker-placement 驗證集實測 LLM 錯位率,達標先去 W71 前端交織 render。
>
> **R6 核實(plan-text grounding,2026-06-12 kickoff 當日)**:
> - chunker 文字組裝 = `backend/ingestion/chunker/layout_aware.py` `_SectionAccumulator`
>   (paragraphs + image_positions 兩條獨立 list,**冇** interleaved flow — 要加 ordered
>   `flow` 記錄;flush 點有三:`_flush_text_section` / `_add_paragraph` token-cap 內 flush /
>   `_force_flush_images` 切法 D;`_merge_adjacent_shorts` 合併時 marked text 要跟住併)
> - `img@<doc_order>` → sha 映射喺 orchestrator `position_to_sha`(orchestrator.py:190-216)
>   — 標記改寫(`[IMG@n]` → `[IMG#sha8]`)喺 orchestrator 做,chunker 唔知 sha
> - `to_search_doc()` 係 model_dump 全欄位 → **現存 index 冇新欄位會拒收 upload**;
>   `create_index_for_kb` 係 PUT(populate.py:253,schema.json 全量定義)→ 遷移 =
>   對現存 KB 重發 PUT(additive field 合法)
> - prompt 文字有三條路徑:`parent_section_text`(parent_doc_retriever.py,production
>   default ON per ADR-0052)/ `expanded_text`(context_expander.py)/ raw `chunk_text`
>   (prompt_builder.py `_format_chunk` dispatch chain)— **三條都要支援 marked 變體**,
>   否則 production 路徑見唔到標記
> - per-KB knob 加點:`backend/api/schemas/kb.py`(12 knobs 區)+ `effective_config.py`
>   (`PerQueryOverrides` / `EffectiveConfig` / `resolve_effective_config`)+
>   `backend/storage/settings.py` global default + 前端 `kb/[id]/page.tsx` `TuneKnobKey`
> - 驗證 harness 樣板 = `scripts/run_image_recall.py` + `docs/eval-set-image-recall-ar.yaml`
>   (drive-images-1 九 query GT,procedural 型啱用)

## 1. 行為設計

- **標記語法**:`[IMG#<checksum_sha256 前 8 hex>]` — 全域唯一(跨 doc 無 doc_order 碰撞),
  同前端現有 dedup key(`checksum_sha256`)直接對應。chunker 先以 `[IMG@<doc_order>]`
  佔位(佢只知 position),orchestrator 用 `position_to_sha` 改寫做 sha8;uploader 跳過
  嘅圖(sha 缺)標記同步剝走 — 同 `ImageRef` list 嘅落選條件一致。
- **B2 雙欄位**:`chunk_text` / `chunk_token_count` / embedding 輸入 **bit-identical 不變**;
  新欄位 `chunk_text_marked`(index:`searchable: false, retrievable: true`)只供
  synthesis prompt 消費。檢索六消費者(BM25 / vector / semantic / rerank / CRAG / RAGAs
  contexts)全部唔見標記。
- **per-KB 開關**:`enable_inline_image_markers`(global default `False`)行 ADR-0040
  四層解析(per-query > per-DOC > per-KB > global)。OFF = prompt 路徑用乾淨文字,
  行為與現狀完全一致;ON = 三條 prompt 文字路徑改用 marked 變體 + system prompt 附加
  「保留 `[IMG#...]` 標記」規則。
- **W70 前端只做 strip**:答案顯示層剝走 `[IMG#...]`(含 streaming 半截標記 buffer),
  **唔做交織 render**(W71,驗證達標先做,mockup 先行 per H7)。
- **驗證先行**:marker-placement harness 用九 query GT 實跑,量四指標 —
  validity(標記對應實際附帶圖)/ coverage(被引用 chunk 自有圖被標記比例)/
  placement accuracy(標記前文 vs 原文標記前文嘅相似度自動評分 + 人工覆核)/
  dup rate。錯位率判決 W71 去向(達標 → 交織;唔達標 → 退守方案 A 段落級跟隨)。

## 2. 交付物 + Gate

| # | 交付 | Gate |
|---|---|---|
| **F1** | ADR-0055 + `docs/adr/README.md` index | ADR committed |
| **F2** | chunker:`_SectionAccumulator` ordered flow + `ChunkSpec.chunk_text_marked`(三個 flush 點 + `_merge_adjacent_shorts` 合併)| 既有 chunker tests 全綠(`chunk_text` bit-identical)+ 新 marked tests |
| **F3** | orchestrator sha8 改寫 + `ChunkRecord` 欄位 + `schema.json` 欄位 + 現存 index PUT 遷移步驟 | tests 綠;PUT 更新 drive-images-1 index 成功 |
| **F4** | config:settings default + KbConfig knob + effective_config 四層解析 | tests 綠;OFF 時 resolve 結果與現狀一致 |
| **F5** | prompt 路徑:`prompt_builder` dispatch + system rule(knob-gated)+ `parent_doc_retriever` + `context_expander` marked 組裝 | dispatch tests 全綠(OFF bit-identical;ON 三路徑都帶標記)|
| **F6** | 前端:tuning card 開關(mockup 先行)+ 答案顯示 marker strip(含 streaming buffer)| tsc 0 / eslint 0 / vitest 綠;H7 fidelity check |
| **F7** | re-index drive-images-1(pre-flight → index PUT → re-upload)| `chunk_text_marked` 喺 index 有值;chunk 數不變 |
| **F8** | `scripts/run_marker_placement.py` harness + 九 query 實跑 + 報告 + **image-recall 對照跑**(knob ON 之下 recall 不回退)| 報告產出;recall ≥ 基線 −0.02;placement 判決記錄 |
| **F9** | doc-sync(user-guide 03 新旋鈕 + memory + rollup)+ closeout | — |

## 3. Acceptance Criteria

- **AC1(零回歸)**:knob OFF(全域 default)→ prompt 內容、`chunk_text`、
  `chunk_token_count`、embedding 輸入全部與改動前 bit-identical;既有 test suite 全綠。
- **AC2(標記正確性)**:chunker 輸出 `chunk_text_marked` 嘅標記位置嚴格按 doc_order
  interleave;sha8 改寫只保留實際上傳成功嘅圖;`chunk_text` 唔含任何標記。
- **AC3(端到端)**:drive-images-1 re-index + knob ON 後,`/query` 答案含合法
  `[IMG#sha8]` 標記,且 chat UI 顯示無爛字(strip 生效,streaming 期間都無半截標記)。
- **AC4(驗證報告)**:harness 輸出四指標 + 人工覆核表;placement 判決(W71 go / no-go
  threshold:自動評分錯位率 ≤ 3% 且人工抽查無誤導性錯配)寫入 progress.md。
- **AC5(召回不回退)**:knob ON 之下 image-recall 九 query 重跑,mean recall 相對
  W68 基線(~1.00)跌幅 ≤ 0.02。
- **AC6(H6)**:chunker / orchestrator / effective_config / prompt_builder 新邏輯全部
  有 test;前端 strip + 開關有 vitest case。

## 4. 風險

- **R1 🟡 LLM 錯位標記**(本 phase 要量化嘅核心風險):緩解 = harness 自動相似度評分
  + 人工覆核;判決門檻 AC4;唔達標退守方案 A,基建(欄位 + 開關)唔嘥 — 方案 A 都
  受惠於 sha8 標記嘅精確映射。
- **R2 🟡 現存 index PUT 遷移**:schema.json 自 index 創建後若有其他 drift,PUT 可能
  被 Azure 拒(非 additive 改動非法)— 處理 = 遷移前先 GET 現有 index 定義對照;
  失敗 fallback = 只遷移 drive-images-1(驗證目標)其餘 KB 等 W71。
- **R3 🟢 streaming 半截標記**:strip 要 buffer 未完整 pattern — 前端有 isStreaming
  分支可掛;test cover。
- **R4 🟢 token 計數語義**:`chunk_token_count` 繼續以乾淨 `chunk_text` 計(切位邏輯
  不變,AC1);prompt 實際 token 比計數多(標記開銷)— 已知偏差,記入 ADR Consequences。
- **R5 🟢 多 doc 標記碰撞**:sha8 語法直接消除(設計層面已解)。

## 5. 非目標

- ❌ 前端交織 render(文字中間插圖卡)— W71,驗證達標 + mockup 先行(H7)。
- ❌ copy / export / RAGAs answer 評分嘅標記 strip — W71(W70 答案顯示層 strip 已
  cover 主要 UX 面;copy 含標記係已知過渡 caveat,記 DEFERRED_REGISTER)。
- ❌ 變體 B1(單欄位)— ADR-0055 已 reject。
- ❌ aux / neighbour 圖嘅 section 級錨定(方案 A 邏輯)— W71 同交織 render 一齊考慮。
- ❌ drive_user_manuals 等其他 KB 嘅 re-index — 驗證只需 drive-images-1。

## 6. H 核對

- **H1**:**觸發並已走流程** — index schema 加欄位 + ingest 衍生欄位;用戶 2026-06-12
  chat 拍板 B2 + per-KB 開關 + 驗證先行;ADR-0055(F1)記錄決定。
- **H7**:W70 前端面 = tuning card 加開關行(mockup 先行,W43/W69 precedent)+ 顯示
  strip(內部標記語法唔屬 mockup 視覺元素,strip 後視覺 == 現狀 == mockup)。
  **W71 交織 render = mockup reverse-drift**(合併稿考證:`ekp-page-chat.jsx:443-500`
  `AnswerBody` 本來就係 inline 插圖設計意圖,現行「全部圖卡堆末尾」先係近似)—
  唔係 new-pattern proposal,但實作仍受 H7 fidelity check 約束(`InlineImageCard`
  元件 / class / spacing 照 mockup `:581-618`)。
- **H2/H3/H4**:不觸(無新 vendor / 無 Dify / Tier 1 範圍內)。
- **H5**:不觸(標記只含圖片 checksum 前綴,無 secret / PII)。
- **H6**:F2-F5 全部 mandatory-test 模組,test 同步寫(AC6)。

## 7. Changelog

| Date | Change | Reason |
|---|---|---|
| 2026-06-12 | Initial plan(active)| 用戶拍板 B2 + per-KB 開關 + marker-placement 驗證集先行;R6 grounding 完成(chunker flow 缺 interleave / orchestrator sha 映射 / to_search_doc 全欄位 upload 遷移坑 / 三條 prompt 文字路徑 / knob 加點 / harness 樣板)|
| 2026-06-12 | **雙 session ADR 合併**:ADR-0055 改為合併稿(機制骨幹不變 = B2 + sha8 + 驗證先行);anchors 稿三項併入 — (1) W71 交織 render 定性改為 **mockup reverse-drift**(`AnswerBody` 考證,§6 H7 已修);(2) W71 標記解析必須對 ADR-0054 dedup/cap 後 surviving 圖集做 membership 驗證,爛標記 strip;(3) 顯示語意預鎖(用戶確認):anchored 圖唔重複喺末尾 inline strip,gallery 全量總覽。F2+ code 維持 GATED on 合併稿最終 Accept(per §5.1)| 用戶指示整合兩 session 草稿;anchors 稿已刪併入 |
