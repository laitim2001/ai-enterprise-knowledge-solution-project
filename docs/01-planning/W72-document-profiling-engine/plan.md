---
phase: W72
name: document-profiling-engine
status: active       # draft | active | closed
created: 2026-06-13
owner: "Claude (AI) — 技術 Lead Chris 審閱"
gap: "ADR-0056 層 A 落地第一段 — rule-based 文件畫像分類引擎(六類 profile + 信心度),由真 ParserResult 抽結構信號 + PDF pypdfium2 pre-OCR 探測,33+7 sample accuracy 驗收 ≥90%。standalone 新 module,零侵入(唔接 orchestrator、唔改 ParserResult / parser / chunker / pipeline)。routing / UI / LLM 保險 / D8 PDF picture / 方案 A 全部留後續段。"
adr: "ADR-0056(Accepted 2026-06-13)— 本 phase 只實作 D1 taxonomy + D2 rule v3 信號抽取 + 信心度 + D7 低信心 fallback label(分類層);D3 routing(profile→preset 套 config)/ D4 三層 UI / D5 LLM tie-break / D8 PDF picture ingestion / 方案 A section 錨定 = 後續段,不在本 phase scope"
spec_refs:
  - docs/adr/0056-document-profiling-adaptive-recall.md            # D1 taxonomy + D2 信號 + D7 fallback
  - backend/ingestion/parsers/base.py                             # ParserResult 契約(信號來源)
  - backend/ingestion/chunker/strategies.py                       # chunk_strategy=auto rule-based 純函數 precedent
  - scripts/explore_doc_profiling_v2.py                           # classify_v2 + 手標 ground truth(productionize 來源,90%)
  - scripts/explore_scan_pdf.py                                   # P4 pre-OCR text-layer 探測(7/7 驗證)
---

# W72 — 文件畫像引擎(rule-based profiler,分類層)

> **緣起**:用戶 2026-06-13 拍板「同意 ADR-0056,開始執行」+ AskUserQuestion 揀「Profiler engine 先」。
> ADR-0056 層 A 內部拆三段(Profiler engine → render-side → 三層 UI),本 phase = 第一段,
> 由最基礎、無 blocker、可獨立驗收嘅分類引擎起。
>
> **R6 核實(plan-text grounding,2026-06-13 kickoff 當日)**:
> - **`ParserResult`**(`backend/ingestion/parsers/base.py:72`)已有 `paragraphs`(每個
>   `kind: heading|text|list_item` + `heading_level`)/ `embedded_images` / `tables` +
>   `@property raw_text|heading_tree|paragraphs_total` → v2 全部信號(paras / headings 數 /
>   max depth / list_item 數 / images 數 / tables 數 + 衍生密度)**可由現有欄位抽,零契約改動**。
> - **缺口 1**:D2「每頁文字密度」需 page metadata,ParserResult 冇 → **唔改契約**,改由
>   profiler 對 PDF 自行做 `pypdfium2` pre-OCR per-page pass 順帶計(見下「設計決策」)。
> - **缺口 2(已坐實)**:PDF `embedded_images` 永遠 0(Docling PDF 唔抽 embedded image)→
>   PDF profile **唔可以靠 img_density**(v2 已 per-format 處理:PDF 靠 text-layer + page density)。
> - **`select_chunker._resolve_auto`**(`strategies.py:49`)= 現成 per-format rule-based 純函數
>   dispatch precedent → profiler classify 跟同一 deterministic 風格(無 LLM、可單元測試)。
> - **`classify_v2`**(`scripts/explore_doc_profiling_v2.py:89`)= productionize 起點,但勘查
>   script reuse v1 hardcoded SIGNALS;productionize 必須改由真 `ParserResult` 抽信號(R2 風險)。
> - **P4 pre-OCR 鎖定**:`explore_scan_pdf.py` 證 7/7 scan text-layer 空比例 1.0,且 Docling
>   OCR 後信號失效(`embedded_images`=0 + heading 誤判)→ P4 偵測**必須 pre-OCR**,唔可以靠
>   parse 後 ParserResult。

## 1. 行為設計

- **新 module `backend/ingestion/profiler.py`**(C01 ingestion component)。**Standalone**:
  本 phase **唔接入** `orchestrator.py`(接入點 = profile→preset routing,屬段 ②);phase 1
  只 build + verify profiler 本身,production ingestion 行為 **bit-identical 不變**。
- **`ProfileResult`**(dataclass,跟 `ParserResult` 風格 — internal type,非 API boundary):
  `profile: Literal[...]`(D1 taxonomy:`P1_sop_imgdense` / `P1_sop_text` / `P2_prose` /
  `P3_slide_imgdense` / `P3_slide_text` / `P4_scan_imgdense` / `P5_form` + utility
  `too_small` / `unknown`)+ `confidence: float`(0–1)+ `signals: dict`(透明展示用,
  後續 UI 段 L3 直接消費)+ `fallback_applied: bool`。
- **`DocumentProfiler.profile(parser_result, source_path) → ProfileResult`**:
  1. **信號抽取**(由 `ParserResult` 現有欄位 + 衍生密度):paras / headings 數 / max heading
     depth / list_item 數 / embedded_images 數 / tables 數 → img_density / head_density /
     list_ratio。
  2. **tick-box / Q-marker 密度**(scan `raw_text`:`□` `★` `Qn` `Your answer:`)→ 救 P5_form。
  3. **PDF 專屬 pre-OCR 信號**(`source_path` 經 `pypdfium2`,Docling 自帶零新 dep):per-page
     text-layer 空比例(高 → P4,short-circuit **唔行 Docling OCR**)+ 每頁字數密度(低 → PDF
     簡報 P3 / 高 → procedure P1_sop_text)。
  4. **classify v3**(productionize `classify_v2` + ADR D2 四項 v3 修正):per-format(pptx →
     P3 細分、PDF 靠 text-layer/page-density 唔靠 img_density)+ `too_small` 門檻 25→20 +
     tick-box 救 form + P1 拆 imgdense/text 兩支。
  5. **信心度 + D7 低信心 fallback**:多重強信號零矛盾 → 高;單弱條件 / 接近 threshold /
     信號矛盾 → 低 + flag;`unknown`(無 rule 命中)→ **fallback 到最保守 `P2_prose`**
     (`fallback_applied=True`,per D7「分錯寧保守,不激進」)。
- **knob / config 不動**:本 phase 純 build profiler,**唔寫任何 per-doc / per-KB config**
  (套 preset = routing 段)。

### 設計決策(記錄 — 偏離 ADR D2 字面,屬 implementation,非 architectural)

ADR D2 寫「每頁文字密度需 parser 出 page metadata(ParserResult 要加)」。本 phase 改為
**profiler 自行對 PDF 做 `pypdfium2` pre-OCR pass** 計每頁字數,**唔改 `ParserResult` 契約**。
理由(Karpathy §1.3 surgical):① P4 偵測本來就要 pre-OCR pypdfium2 pass,每頁字數同一 pass
順帶攞,零額外成本;② 改 ParserResult page metadata 會擴散到所有 parser + downstream
consumer,影響面遠大過需求;③ page metadata 目前**只有 profiler 一個 consumer** → YAGNI,
future 真有第二 consumer 先抽上契約。**此決定喺本 changelog + progress Day-1 記錄(R3)**。

## 2. 交付物 + Gate

| # | 交付 | Gate |
|---|---|---|
| **F1** | `profiler.py` 核心:`ProfileResult` schema + `DocumentProfiler` 信號抽取(ParserResult 衍生 + tick-box scan)+ classify v3 + 信心度 + D7 fallback | mypy --strict 0 / ruff 0;單元測試覆蓋 classify 各分支 |
| **F2** | PDF pre-OCR 信號:`pypdfium2` per-page text-layer 空比例 + 每頁字數密度,接入 profiler PDF 分支(P4 short-circuit + P3/P1 分流) | scan short-circuit 唔觸發 Docling OCR;born-digital PDF text-layer 非空判正確 |
| **F3** | accuracy harness + H6 test:真 parse 33 sample(docx/pptx Docling + PDF pre-OCR)+ 7 scan → accuracy ≥90% / 7 scan 全 P4;profiler unit test(邊界 / 信心度 / 退化 / deterministic) | accuracy ≥90% gate PASS;pytest 綠;coverage 達 ingestion 標準 |
| **F4** | 收爐:memory 更新(profiler 落地)+ closeout retro + ADR-0056 D8 段交棒記錄 | — |

## 3. Acceptance Criteria

- **AC1(分類 accuracy)**:33 sample(扣 SMALL 噪音後真實內容文件)rule v3 命中 **≥90%**
  (ADR v3 預估 ~95%);7 份 scan 發票 **全部判 `P4_scan_imgdense`**。
- **AC2(deterministic)**:同一文件多次 profile 結果 bit-identical(純 rule,無 LLM stochastic;
  per H4)。
- **AC3(信心度 + fallback)**:信號矛盾 / 邊界 case flag 低信心;`unknown` 一律 fallback 到
  `P2_prose`(`fallback_applied=True`),**永不**自動套激進 imgdense profile(D7)。
- **AC4(H4 邊界)**:零 LLM call、零 image embedding / multimodal、純結構 + 文字 marker 信號。
- **AC5(零侵入)**:profiler 係 standalone 新 module — **唔接入** orchestrator、**唔改**
  `ParserResult` / parser / chunker / pipeline 任何現有行為;`git diff` 對現有 ingestion code
  零改動(只新增 `profiler.py` + test)。
- **AC6(H6)**:`profiler.py` 喺 `backend/ingestion/` → 必須有 unit test(classify 各分支 /
  信心度 / fallback / PDF pre-OCR / deterministic)。

## 4. 風險

- **R1 🟡 PDF pre-OCR 邊界**:7/7 scan 已驗 text-layer 空 1.0,但 born-digital PDF 與「部分
  text-layer + 部分 raster」混合 PDF 邊界未全驗 → harness 跑真 PDF sample 時記實際 text-layer
  比例分佈,定 P4 門檻(非硬 1.0,留 margin)。
- **R2 🟡 productionize 信號漂移**:勘查 v2 用 v1 hardcoded SIGNALS;真 `ParserResult` 重抽信號
  數值若同 hardcoded 有差(parser 版本 / heading 偵測差異)→ classify 結果可能變。F3 harness
  必須真 parse 對齊,miss 變化記 progress。
- **R3 🟡 sample 偏細**:33 + 7,真實命中率仍有不確定(ADR Consequences 已標)。本 phase 只
  驗呢個 sample;真實 KB 命中率待 routing 段落地後實測。
- **R4 🟢 pypdfium2 可用性**:Docling 自帶(零新 dep,H2 不觸);勘查 script 已實證可 import。

## 5. 非目標

- ❌ **routing**(profile→preset 自動套 per-doc config,ADR D3)— 段 ②;本 phase profiler 只
  output label,唔寫任何 config。
- ❌ **三層 UI**(D4:badge / 文件畫像 section / 分類規則設定)— 段 ③,⚠️ **卡 H7 OQ-B**
  (profiling UI 無 mockup,要先設計)。
- ❌ **LLM tie-break 保險**(D5 / OQ-C)— 後續段;本 phase 純 rule,unknown 走 D7 fallback 即可。
- ❌ **D8 PDF picture ingestion**(`generate_picture_images=True` + re-index)— render-side 段。
- ❌ **方案 A section 級錨定** — render-side 段(W71 §5 未實作 net-new)。
- ❌ **改 `ParserResult` 契約**(加 page metadata)— profiler self-contained,per 設計決策。
- ❌ **profiler 接入 orchestrator** — 接入屬 routing 段(接入要決定點消費 profile)。
- ❌ **xlsx parser**(ADR D8 future H2)+ parser robustness 修(OCR `std::bad_alloc` / Pillow)。

## 6. H 核對

- **H1**:profiler = 新 module **但 standalone 唔接 pipeline** → 本 phase 唔改 `architecture.md`
  §3/§4 任何現有 component behavior / interface。ADR-0056 已 cover profiling 方向(Accepted)。
  接入 ingestion flow(§3.3)= routing 段先觸,屆時在該段 plan 處理。
- **H2**:`pypdfium2` = Docling 自帶(零新 dep);不觸 vendor lock。
- **H3**:不觸(無 Dify reference)。
- **H4**:純 rule classify,零 LLM、零 image embedding / multimodal;LLM 保險(D5)留後續段。
- **H5**:不觸(無 secret / PII;profiling 純結構信號)。
- **H6**:`profiler.py` 喺 `backend/ingestion/` 強制 test(F3 unit test + accuracy harness)。
- **H7**:本 phase 無 UI / 無 frontend 改動,不觸;UI 段(③)先觸 H7 OQ-B。

## 7. Changelog

| Date | Change | Reason |
|---|---|---|
| 2026-06-13 | Initial plan(active)| 用戶拍板「同意 ADR-0056,開始執行」+ AskUserQuestion 揀「Profiler engine 先」。R6 grounding 完成 — 關鍵發現:(1) ParserResult 現有欄位足以抽 v2 全部信號零契約改動;(2) D2 每頁文字密度缺口改由 profiler PDF pypdfium2 pre-OCR pass 自含(唔改 ParserResult,Karpathy surgical,記設計決策);(3) P4 必須 pre-OCR(parse 後信號失效);(4) profiler standalone 唔接 orchestrator → 本 phase 零侵入。**設計決策偏離 ADR D2 字面**(page metadata 由 profiler 自抽非 parser 出)屬 implementation 非 architectural,已記 §1 + 本 changelog(R3)|
