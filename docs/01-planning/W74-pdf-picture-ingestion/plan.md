---
phase: W74
name: pdf-picture-ingestion
status: closed       # draft | active | closed(2026-06-14 — F1-F3 done;23 pass + 7 skip;per-KB thread extract_embedded_images;production-preserve)
created: 2026-06-14
owner: "Claude (AI) — 技術 Lead Chris 審閱"
gap: "ADR-0057(段 ②c)— per-KB generate_picture_images:thread 現有 `KbConfig.extract_embedded_images` 落 PDF parser,令 born-digital PDF embedded picture 入庫。解 ADR-0056 層 A 嘅 PDF 圖類 profile preset(W73)+ ADR-0055 inline marker 對 PDF 空轉。re-index 按需(W46 機制,唔強制)。production-preserve(`extract_embedded_images=False` bit-identical)。"
adr: "ADR-0057(Accepted 2026-06-14)— per-KB generate_picture_images + 按需 re-index。scan P4 OCR / 方案 A 不在 scope。"
spec_refs:
  - docs/adr/0057-pdf-picture-ingestion-per-kb.md
  - backend/ingestion/parsers/pdf_parser.py                       # :54 DocumentConverter() 預設
  - backend/ingestion/parsers/__init__.py                        # :23 select_parser
  - backend/api/schemas/kb.py                                    # :41 extract_embedded_images
  - backend/api/routes/documents.py                             # :604 select_parser call + kb_config 讀
  - scripts/explore_pdf_picture_flag.py                          # 0→10/10 + +19% 實測
---

# W74 — PDF picture ingestion(段 ②c,ADR-0057)

> **緣起**:用戶開段②c → STOP(H1)→ AskUserQuestion 揀「per-KB(thread extract_embedded_images)」+「按需 re-index」→ ADR-0057 Accepted。本段兌現。
>
> **R6 核實**(已喺 ADR-0057 grounding 做齊):
> - `select_parser(source)`(`__init__.py:23`)只食 path → `DoclingPdfParser()`,無 kb_config。
> - `pdf_parser.py:54` `self._converter = DocumentConverter()`(預設 generate_picture_images=False)。
> - `KbConfig.extract_embedded_images`(預設 False,`kb.py:41`)= 現有 per-KB image toggle。
> - `_run_ingest_pipeline`(`documents.py:604`)`parser = select_parser(tmp_path)`;**kb_config 喺
>   line ~610 先讀**(select_parser 之後)→ 要把 kb_config 讀**移前**至 select_parser 之前。
> - Docling 自訂 converter:`PdfPipelineOptions().generate_picture_images = True` +
>   `DocumentConverter(format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=opts)})`
>   (per `explore_pdf_picture_flag.py`,Docling 自帶零新 dep)。

## 1. 行為設計

### D1 — parser 層接受 generate_picture_images
- `DoclingPdfParser.__init__(generate_picture_images: bool = False)` — 預設 False(production-preserve);
  True → 用自訂 `PdfPipelineOptions(generate_picture_images=True)` converter,否則維持預設
  `DocumentConverter()`(bit-identical)。

### D2 — select_parser thread flag
- `select_parser(source, *, extract_images: bool = False)` — `.pdf` 分支傳
  `DoclingPdfParser(generate_picture_images=extract_images)`;`.docx`/`.pptx` 不變(keyword-only,
  default False → 現有 caller 零 churn)。

### D3 — _run_ingest_pipeline wire
- kb_config 讀**移前**至 `select_parser` 之前(現時喺其後)。
- `parser = select_parser(tmp_path, extract_images=bool(kb_config and kb_config.extract_embedded_images))`。
- 語意統一:`extract_embedded_images=True` → parser 抽 PDF 圖 + orchestrator `ScreenshotExtractor`
  extract / upload(現有);兩層一致。

### D4 — re-index 按需(零本段改動)
- 新 PDF ingest 即有圖;現有 PDF doc 用戶按需 W46 `POST /kb/{kb_id}/reindex` 補圖。本段**唔自動 /
  唔強制** re-index 任何 KB(零強制成本)。reindex 路徑 reuse `_run_ingest_pipeline`(W46 / ADR-0043)
  → 自動繼承本段 thread(reindex 都 per-KB 抽圖)。

## 2. 交付物 + Gate

| # | 交付 | Gate |
|---|---|---|
| **F1** | `DoclingPdfParser.__init__(generate_picture_images)` + `select_parser(extract_images)` + `_run_ingest_pipeline` kb_config 移前 + wire | mypy 0 + ruff 0;現有 parser_factory / documents / reindex test 全綠 |
| **F2** | test:`select_parser(extract_images=True)` → parser generate_picture_images;default False bit-identical;真 PDF 抽圖(skipif sample) | pytest 綠(H6)|
| **F3** | 收爐:memory + closeout + 段②d/③ 交棒 + plan closed | — |

## 3. Acceptance Criteria

- **AC1(per-KB 抽圖)**:`select_parser(path, extract_images=True)` 對 `.pdf` → `DoclingPdfParser`
  帶 generate_picture_images=True;真 born-digital PDF(skipif sample)ingest → embedded_images 非空。
- **AC2(production-preserve)**:`select_parser(path)`(default)/ `extract_images=False` →
  generate_picture_images=False,parse 結果 bit-identical 現狀(PDF 圖唔抽)。
- **AC3(語意統一)**:`_run_ingest_pipeline` thread `kb_config.extract_embedded_images` →
  圖類 KB(True)PDF 抽圖 + extract;text KB(False / None)零成本。
- **AC4(零 churn)**:`select_parser` keyword-only `extract_images` default False → 現有 caller
  (parser_factory test / populate)不變;`.docx`/`.pptx` 路徑 bit-identical。
- **AC5(H6)**:parser + select_parser thread 有 test。

## 4. 風險

- **R1 🟡 scan PDF `std::bad_alloc`**:ADR-0056 D8 標(Docling layout 階段)。本段唔解(non-goal);
  parser 已有 try/except → `parse_failed=True`(orchestrator 記 FailureRecord,唔 crash batch)。
- **R2 🟢 +19% parse 成本**:只 `extract_embedded_images=True` 的 PDF KB 付(per-KB 控制)。
- **R3 🟢 reindex 繼承**:reindex reuse `_run_ingest_pipeline` → 自動 per-KB 抽圖(無額外改動);
  W46 前 PDF 冇 source → `skipped_no_source`(已有行為)。

## 5. 非目標

- ❌ **scan PDF(P4)OCR / page-raster gallery** — ADR-0019 Tier 2 + ADR-0057 scope 外。
- ❌ **方案 A section 級錨定**(段②d)— `P1_sop_imgdense` 完整 render,net-new。
- ❌ **強制 / 自動 re-index** 現有 PDF KB — 按需(D4)。
- ❌ **全局 generate_picture_images** — per-KB(ADR-0057 D1,reject 全局)。
- ❌ **`std::bad_alloc` robustness 修** — 上游 ingestion 另議(ADR-0056 D8)。
- ❌ **三層 UI**(段③)— 卡 H7 OQ-B。

## 6. H 核對

- **H1**:改 PDF parse behavior(抽圖)+ storage(PDF screenshot blobs)— **ADR-0057 Accepted cover**。
- **H2**:`pypdfium2` / Docling 自帶,零新 dep(自訂 converter 用 Docling 既有 API)。
- **H3**:不觸。
- **H4**:embedded image 入庫 = Tier 1 image pipeline(citation render),**非** multimodal retrieval /
  image embedding(Tier 2 禁)— 不觸。
- **H5**:不觸。
- **H6**:`pdf_parser` + `select_parser` thread 有 test。
- **H7**:本段無 UI / frontend,不觸。

## 7. Changelog

| Date | Change | Reason |
|---|---|---|
| 2026-06-14 | Initial plan(active)| 用戶開段②c → STOP(H1)→ AskUserQuestion 揀 per-KB(thread extract_embedded_images)+ 按需 re-index → ADR-0057 Accepted。R6 grounding 已喺 ADR 做齊;關鍵 implement 點:kb_config 讀要移前至 select_parser 之前(現時喺其後);select_parser keyword-only extract_images default False 保零 churn |
| 2026-06-14 | Closeout(closed,PASS)| F1-F3 全成,23 pass + 7 skip + mypy/ruff clean(7 errors 全 pre-existing docling stub + Protocol doc_format)。實作對齊 plan(parser flag + select_parser thread + kb_config 移前 wire)。real-PDF integration 由 explore_pdf_picture_flag.py 背書代替(EKP convention real-PDF deferred skip)。無 deviation,無 deferred `[ ]` |
