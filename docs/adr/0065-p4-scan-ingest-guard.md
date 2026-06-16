# ADR-0065: P4 掃描件 ingest 預檢 guard + force override

**Date**: 2026-06-16
**Status**: Accepted
**Approver**: Chris

## Context

層 A scan robustness（DD-9）2026-06-15 兩次實證重跑收斂：**robustness 已 OK**（`std::bad_alloc`
Docling per-page graceful degrade，兩次各 3/3 scan 零 crash）+ **分類已準**（兩次各 3/3 全
`P4_scan_imgdense` 0.95）。真正剩餘缺口 = **OCR 慢**（~490–568s/檔，8–9.5 分鐘 = Tier 2 本質，
ADR-0019 defer）+ **零 production scan KB**（現有全 docx）。

關鍵壞體驗風險：ingest 係**同步**的（`upload_document` docstring：「the ingest is synchronous in
Tier 1, no background job」）。一旦 production 開放 PDF 上傳，用戶上載一份 scan PDF → Docling OCR
同步 hang request **8–9.5 分鐘** → request timeout / 用戶以為系統壞咗。

用戶 2026-06-16（連續 AskUserQuestion：擱置層 C → 評估層 A scan / 層 B → 揀做層 A P4 guard →
揀「預檢警告 + force override」）確認推進此 guard，且 guard 行為 = **預檢警告 + 「仍要繼續」force
覆寫**（非硬 reject，保留用戶自調，呼應 per-KB tunable config vision）。

此 guard 改 ingest 流程（§3.3）→ 觸 **H1**；upload 警告 UI 係 mockup 之外 → 觸 **H7**。

## Decision

ingest 前加一個**秒級 pre-parse P4 probe**，攔截 scan PDF 防同步 OCR hang，並提供 force override：

1. **`is_scan_pdf(path)` standalone helper**（`ingestion/profiler.py`）— 抽出 profiler 既有的
   `_probe_pdf_text_layer` pypdfium2 **pre-OCR** 邏輯（秒級，**唔觸發 OCR**）：text-layer 空頁比例
   ≥ 0.5 **或** 平均 chars/頁 < 200 → True（對齊 `_classify_pdf_preocr` 的 P4 判定 threshold）。
   profiler 自身改為復用此 helper（零行為改變）。

2. **`_run_ingest_pipeline` guard** — tmpfile 寫好後、`select_parser` / `orchestrator`（OCR）之前：
   `ext == ".pdf"` 且 `is_scan_pdf(tmp_path)` 且 **無 `force_scan`** → raise **422
   `ingest.scan_requires_confirm`**（「掃描件 OCR 需 ~8–9.5 分鐘，確認後 force 重試」）。
   `force_scan=True` → 跳過 guard 照常 ingest（用戶知情接受同步等待）。

3. **`force_scan: bool = False` 參數** — POST `/kb/{kb_id}/documents` + POST `.../reindex` 加 query
   參數，傳落 `_run_ingest_pipeline`。

4. **frontend** — `kbApi.uploadDoc(kbId, file, forceScan?)` 帶 `?force_scan=`；upload 接 422
   `scan_requires_confirm` → 警告 banner（**復用既有 `banner-warning` primitive，視覺零發明**）+
   「仍要繼續（約 8–9.5 分鐘）」按鈕 → `force_scan=true` 重試。

**production-preserve**：guard 只對 `.pdf` 跑秒級 probe；born-digital PDF 判非 P4 → 照常 ingest
（零行為改變）；docx / pptx 完全跳過。

## Alternatives Considered

- **純硬 reject**（判 P4 一律拒絕）— 最簡單但擋死 scan（用戶即使願等也不能 ingest），違 vision 自調。Reject。
- **warn-only 不擋**（標記但照常 ingest）— 唔解 hang（仍同步卡 8–9.5 分鐘）。Reject。
- **async background ingest**（job queue 防 hang）— 根治 hang 但係大架構改動（背景 job + 狀態輪詢），
  Tier 2-ish，遠超 P4 guard scope。Reject 本期（force 路徑同步等待係用戶知情接受的取捨）。
- **用 `profiler.profile` 完整跑判 P4** — 需先 `parser.parse()`（= OCR），defeats the purpose。
  Reject — 必須用 pre-parse pypdfium2 probe。

## Consequences

- **Positive**：防 scan PDF 同步 ingest hang 8–9.5 分鐘（production 開放 PDF 上傳時的真實壞體驗）；
  保留用戶自調（force override 呼應 vision）；秒級 probe overhead；production-preserve（born-digital
  PDF + docx/pptx 零影響）；DD-9 由「結構性 defer」收窄至只剩 OCR 慢（Tier 2 本質）。
- **Negative**：H7 design-stage expansion（upload 警告 UI mockup 之外，復用既有 banner primitive 緩解）；
  force 路徑仍同步 hang（用戶知情接受，async 留 future）。
- **Neutral**：唔解 OCR 慢本質（Tier 2 ADR-0019）；profiler 分類行為不變（helper 復用零改變）。

## References

- DD-9（scan robustness 探索結論）/ ADR-0056（層 A document profiling 母 ADR）/ ADR-0057（PDF picture）/
  ADR-0019（PDF parser Tier 1 — scanned/encrypted defer Tier 2）
- `ingestion/profiler.py`（`_probe_pdf_text_layer` + `_classify_pdf_preocr` P4 threshold）/
  `api/routes/documents.py`（`_run_ingest_pipeline` + `upload_document`）/ `frontend/lib/api/kb.ts`（`uploadDoc`）
- architecture.md §3.3（ingestion）；H1（ingest 流程改動）/ H4（profiler 純文字信號）/ H7（design-stage expansion）
- 母 vision：`project_per_kb_tunable_config_vision`（per-KB/per-document 可調配置 + UI 自調）
