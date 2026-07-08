---
id: BUG-044
title: PDF parser 對 born-digital PDF 白行 Docling OCR → parse 慢 ~3x(+~60s,零文字得着),上傳似 hang
severity: Sev2          # 核心 ingest UX:圖多 PDF 上傳 ~87s + stale backend 下凍全 backend,表面 hang
status: done            # 2026-07-08 用戶 approve → do_ocr=False fix landed + 3 新 test 綠(87s→27s 離線實測)
reported: 2026-07-08
reporter: 頁面測試(用戶新建 KB 上傳 born-digital brochure PDF「一直 loading」)
backlog: B-21
related: ADR-0019(PDF parser Tier 1 scope = text-extractable only,OCR defer Tier 2)/ ADR-0065(is_scan_pdf scan guard + force_scan)/ BUG-040(ingest offload event loop — 決定 stale backend 表現為全凍)
---

# BUG-044 — born-digital PDF 白行 OCR,parse 慢 ~3x

## 1. 現象(頁面 + 離線實測)

新建 KB 後上傳一份 **3 頁 born-digital PDF**(`docs/06-reference/01-sample-doc/IMC320F_MC320FW_PC375_Brochure_102 (5).pdf`,Adobe InDesign 19.5 製作,3.28 MB,有完整文字層),前端**一直 loading**。

離線用 venv python 實測同一份檔:

| Parse 方式 | 耗時 | text 項 | 圖(PICTURE) | 表 |
|---|---|---|---|---|
| 預設 `DocumentConverter()`(OCR on) | **87.1s** | 42 | 13 | 1 |
| `PdfPipelineOptions.do_ocr=False` | **27.0s** | 42 | 13 | 1 |

OCR 多花 **~60s 但零得着**:text 項兩邊完全相同(42),因 born-digital PDF 本身有文字層,RapidOCR 抽唔到新嘢。`is_scan_pdf` 對此檔回 `False`(0.35s,正確 — 非掃描件),故不觸 ADR-0065 的 422 guard,直落 parse。

## 2. 根因(對 code first-hand 核對)

**A(本 BUG 主因,代碼):** `backend/ingestion/parsers/pdf_parser.py:55-69` — `DoclingPdfParser.__init__` 用 Docling **預設 converter**(`DocumentConverter()`),而 Docling 預設 `do_ocr=True` → 每份 PDF 都跑 RapidOCR(torch CPU)。這**違反 parser 自己寫明的 Tier 1 scope**(`pdf_parser.py:49`「text-extractable PDF only. Scanned (OCR) … defer Tier 2」,ADR-0019),亦與 `documents.py:866-867` scan guard 註解「Docling OCR blocks the SYNCHRONOUS ingest」的避 OCR 意圖矛盾 —— scan guard 只擋「空文字層」的全掃描件,對有文字層但圖多的 born-digital PDF 無效,OCR 照跑。

**B(令現象放大為「全凍」的運行狀態,非本 code bug):** 現行 running backend(PID 7188)於 **2026-07-07 11:03** 啟動,早於 BUG-040(`asyncio.to_thread` offload,commit 於 **14:18**);`reload=False` → 未 pick up。故 87s 同步 parse **阻塞整個 uvicorn event loop**,upload 期間全 backend 凍住 → 前端表現為 hang。**重啟 backend 即修 B**(現行 main 已含 BUG-040 offload);但即使非阻塞,單份仍 ~87s,故 A 才是 UX 主因。

## 3. 建議修法(等 approve)

1. **`DoclingPdfParser` 加 `do_ocr: bool = False` 參數**;統一走 `PdfPipelineOptions`,設 `opts.do_ocr = do_ocr`(同時保留 `generate_picture_images` 分支)。預設 `False` → 一般 PDF parse 87s→27s。
2. **`parsers/__init__.py` `select_parser` 加 `do_ocr` 參數**透傳到 `DoclingPdfParser`。
3. **`documents.py` 兩個 select_parser 呼叫點(:893 主 ingest、:1298 reindex/backfill)傳 `do_ocr=force_scan`** —— 一般 PDF `force_scan=False` → `do_ocr=False`(快);用戶確認的掃描件路 `force_scan=True` → `do_ocr=True`(保留 OCR 抽掃描件文字,ADR-0065 意圖不變)。
4. **運行:** 修完**重啟 backend**,一次過生效 BUG-040 offload(修 B)+ 本 OCR fix(修 A)。

**明確不做:** 不引入新 OCR 引擎 / 不改 scan guard 邏輯 / 不做 per-KB OCR 開關(Tier 1 無此需求,YAGNI)。

## 4. 驗收標準(等 approve 後據此驗)

- 同一份 brochure PDF:一般 ingest parse ~27s(非 87s),text/圖/表數量不變(42 / 13 / 1),答案品質不退。
- `force_scan=True` 路仍 `do_ocr=True`(掃描件仍 OCR;可用 monkeypatch 驗 pipeline_options.do_ocr 依 force_scan 切換)。
- `.docx` / `.pptx` 路不受影響。
- `test_pdf_parser.py` 補 test:預設 parser `do_ocr=False`、`do_ocr=True` 時 opts 生效。
- ruff / mypy clean(新增 code)。

## 5. 風險與注意

- **低**:born-digital PDF(Tier 1 scope)本有文字層,關 OCR 零文字損失(實測 42=42)。真掃描件早被 `is_scan_pdf` 422 擋,force_scan 路保留 OCR。
- **邊界**:born-digital PDF 內若有「圖中文字」(如圖表標籤),OCR 本可抽到,關咗會失 —— 但此屬 Tier 2 multimodal scope(architecture.md §11),Tier 1 不承諾,可接受。
- 修法純加參數 + 預設值,不改控制流;現有 born-digital 測試結果應 bit-identical(除 OCR 產生的雜訊文字,反而更乾淨)。

## 6. Fix landed

- `backend/ingestion/parsers/pdf_parser.py` — `DoclingPdfParser.__init__` 加 `do_ocr: bool = False` 參數;統一走 `PdfPipelineOptions`(顯式 `opts.do_ocr` + `opts.generate_picture_images`),取代原本「`generate_picture_images` True→建 opts / False→裸 `DocumentConverter()`(Docling 預設 OCR on)」分支。預設 `do_ocr=False` → born-digital PDF 唔再白行 OCR。
- `backend/ingestion/parsers/__init__.py` — `select_parser` 加 `do_ocr: bool = False` 透傳到 `DoclingPdfParser`(.docx / .pptx 無 OCR path,不受影響)。
- `backend/api/routes/documents.py` — 主 ingest 呼叫點(`_run_ingest_pipeline`:893)`select_parser(..., do_ocr=force_scan)`:一般 born-digital PDF `force_scan=False` → `do_ocr=False`(快);用戶確認掃描件路 `force_scan=True` → `do_ocr=True`(保留 OCR 抽掃描件文字,ADR-0065 意圖不變)。profile backfill 呼叫點(:1298)沿用 `do_ocr=False` 預設(profiling 一致 + 屬既有 doc,無 force_scan)。
- `backend/tests/test_pdf_parser.py` — 補 3 結構式 test:預設 `do_ocr=False` / `do_ocr=True` opt-in / `select_parser` 透傳。
- **驗證**:`test_pdf_parser.py` **8 passed(5 舊 + 3 新)+ 7 skipped**(deferred real-PDF)/ `ruff check` All passed / 新增 code `ruff format` clean(整檔 `format --check` fail = pre-existing 長 `@pytest.mark.skip` 行,屬 B-20,surgical 不碰)/ mypy 新增 code 零 error(既有 9 error = `NodeItem` attr + `doc_format` Literal mismatch,pre-existing;`docx_parser.py`〔未觸〕同類為證,屬 B-20)。
- **行為實測(離線 venv,非 server)**:同一份 3 頁 born-digital brochure,OCR on **87.1s** vs `do_ocr=False` **27.0s**,text/圖/表數量相同(42 / 13 / 1)→ OCR 白行零得着,關咗省 ~60s。
- **生效需重啟 backend**(`reload=False`);running backend 亦要重啟先 pick up 已 merge 的 BUG-040 offload。

## 7. Changelog

| 日期 | 動作 | 決定人 |
|---|---|---|
| 2026-07-08 | 頁面測試發現 born-digital PDF 上傳似 hang → 離線實測定位(OCR 白行 +60s / stale backend 阻塞)→ 立案 BUG-044,`status: proposed`,未動 code | 頁面測試 / 待用戶 approve |
| 2026-07-08 | 用戶 approve → fix landed(`do_ocr` 參數預設 False + `select_parser` 透傳 + 主 ingest `do_ocr=force_scan`)+ 3 新 test 綠 + ruff/mypy(新增 clean,pre-existing 屬 B-20)→ `status: done` | 用戶 approve / Claude |
