# W84 plan — P4 掃描件 ingest 預檢 guard + force override（ADR-0065）

**Status**: active（kickoff 2026-06-16）
**Kickoff**: 2026-06-16
**Phase 類型**: full-stack feature（backend ingest guard + frontend force UI；H1 ingest 流程 +
H7 design-stage expansion upload 警告；ADR-0065 Accepted）
**ADR**: ADR-0065（P4 scan pre-parse guard + force override — 預檢警告 + 「仍要繼續」）

---

## §1 Context / 緣起

用戶擱置層 C（DD-12 defer）後評估層 A scan / 層 B（DD-10），揀**做層 A P4 預檢 guard**（= production
會開放 PDF 上傳）。DD-9 探索結論：scan robustness + 分類已 OK，剩餘 OCR 慢（8–9.5 分鐘 = Tier 2 本質）+
零 production scan KB。**真實壞體驗風險** = ingest 同步（Tier 1 no background job），scan PDF → Docling
OCR 同步 hang request 8–9.5 分鐘。guard 防此 hang。用戶揀 guard 行為 = **預檢警告 + force override**
（非硬 reject，保留自調，呼應 vision）。

**落點 grounding（plan kickoff,R6）**：
- `backend/ingestion/profiler.py` — `_probe_pdf_text_layer`（pypdfium2 pre-OCR，秒級，不 OCR）+
  `_classify_pdf_preocr` P4 threshold（`pdf_empty_ratio >= 0.5` 或 `pdf_avg_chars < 200`）。抽 standalone
  `is_scan_pdf(path)` helper，profiler 復用（零行為改變）。
- `backend/api/routes/documents.py`：
  - `_run_ingest_pipeline`（701）— tmpfile 寫好（744）後、`select_parser`（759）/ `orchestrator`（774，OCR）
    之前插 guard。
  - `upload_document`（1258，POST `/kb/{kb_id}/documents`，同步 202）+ reindex endpoint — 加 `force_scan`
    query 參數，傳落 `_run_ingest_pipeline`。
- `frontend/lib/api/kb.ts` — `uploadDoc(kbId, file)`（230）目前 422 throw generic Error（242）→ 改成能
  區分 `scan_requires_confirm` + 加 `forceScan?` 參數（`?force_scan=`）。
- `frontend/app/(app)/kb/[id]/upload/page.tsx` — 既有 `banner banner-info` / `banner-error` primitive
  + error 處理（status failed → error.message）→ 加 scan 警告 banner（`banner-warning`）+ 「仍要繼續」按鈕。

---

## §2 Scope / Deliverables

### F1 — Backend `is_scan_pdf` helper + ingest guard + force flag
- **F1.1** `profiler.py` 抽 module-level `is_scan_pdf(source_path) -> bool`（復用 `_probe_pdf_text_layer`
  + P4 threshold；profiler `_extract_signals` / `_classify_pdf_preocr` 改為復用，零行為改變）。
- **F1.2** `_run_ingest_pipeline` 加 `force_scan: bool = False` 參數 + guard：`ext == ".pdf"` 且
  `is_scan_pdf(tmp_path)` 且非 `force_scan` → raise 422 `ingest.scan_requires_confirm`（actionable hint
  指 force 重試）。插 tmpfile 寫好後、`select_parser` 之前。
- **F1.3** `upload_document` + reindex endpoint 加 `force_scan: bool = False` query 參數 → 傳落
  `_run_ingest_pipeline`。
- **acceptance**：pytest 蓋 scan PDF 無 force → 422 `scan_requires_confirm` / scan + force → 跳 guard /
  born-digital PDF → 照常（production-preserve）/ docx → 跳 probe；`is_scan_pdf` unit test（scan / born-digital
  / 非 PDF）；mypy strict + ruff clean。

### F2 — Frontend force UI
- **F2.1** `kb.ts` `uploadDoc(kbId, file, forceScan = false)` 加 `?force_scan=` + 422 解析：`scan_requires_confirm`
  → throw 帶 code 的 typed error（或回特殊 sentinel）讓 upload page 區分。
- **F2.2** `upload/page.tsx` 接 `scan_requires_confirm` → 警告 banner（`banner-warning`，**復用既有 primitive
  視覺零發明**：掃描件 + OCR ~8–9.5 分鐘）+ 「仍要繼續」按鈕 → `uploadDoc(..., true)` 重試。
- **acceptance**：type-check 0 + lint 零新 warning + build ✓；警告 UI 全用既有 banner primitive（H7 視覺零發明）。

### F3 — Browser 驗（playwright）
- 起 infra → upload 頁 upload 一份 scan PDF（`docs/06-reference/01-sample-doc/scanned_pdf_sample/`）→ 驗
  **reject 路徑**（秒級判 P4 → 警告 banner + 「仍要繼續」按鈕出現）；born-digital PDF / docx upload → 無警告
  正常。**force 路徑 OCR 慢（8–9.5 分鐘）由 F1 backend test 覆蓋**，browser 不跑足 OCR（或 skip）。
- **acceptance**：scan reject 路徑警告 banner render PASS；console 僅 pre-existing 404。

### F4 — closeout
- backend test + type-check/lint/build + browser；plan closed + retro + ADR-0065 README index +
  DEFERRED DD-9 更新（收窄至只剩 OCR 慢 Tier 2）+ memory 更新。

---

## §3 設計原則（ADR-0065）

1. **pre-parse 攔截** — 必須喺 Docling OCR 之前判 P4（pypdfium2 pre-OCR probe 秒級），否則 defeats purpose。
2. **預檢警告 + force（非硬 reject）** — 保留用戶自調（vision）；force 路徑同步等待係用戶知情取捨。
3. **production-preserve** — 只對 `.pdf` 跑 probe；born-digital PDF 判非 P4 照常；docx/pptx 跳過；零 scan KB
   現狀零影響。
4. **視覺零發明** — upload 警告復用既有 `banner-warning` primitive（H7 方案，同 W81/W82 precedent）。
5. **helper 復用** — `is_scan_pdf` 抽自 profiler 既有 probe，profiler 自身零行為改變。

---

## §4 Non-goals（明確唔做）

- **async background ingest** — 根治 hang 但大架構改動（Tier 2-ish），超 scope；force 路徑同步等待。
- **解 OCR 慢本身** — Tier 2 本質（ADR-0019），不做。
- **改 profiler P4 threshold** — 復用現有判定，不調。
- **改 mockup** — upload 警告復用既有 primitive；mockup 補 scan 警告設計走獨立 design sync。
- **scan PDF 完整 OCR ingest 驗** — F3 只驗 reject 路徑（秒級）；force OCR 路徑 backend test 覆蓋。

---

## §5 Risks

- **R1 H7 design-stage expansion**（upload scan 警告 mockup 之外）— 緩解：復用既有 `banner-warning` primitive
  視覺零發明 + 用戶選項 1 已批准方向 + 記 ADR-0065；mockup 補設計獨立 design sync。
- **R2 `is_scan_pdf` 誤判 born-digital PDF 為 scan** → 誤擋正常 PDF — 緩解：復用已驗 P4 threshold（7/7 真 scan
  + born-digital 區分準）+ force override 兜底（誤判都可繞）+ F1 test 蓋 born-digital。
- **R3 profiler 復用 helper 後行為改變** — 緩解：F1.1 抽 helper 後 profiler 既有 test 全綠（零行為改變回歸）。
- **R4 force_scan query 參數 reindex 漏接** — 緩解：F1.3 兩 endpoint 都加 + test。

---

## §6 紀律自檢（kickoff）

- **H1** ⚠️→✅ ingest 流程加 guard（§3.3）— ADR-0065 Accepted（用戶連續 AskUserQuestion 揀做 P4 guard + 預檢警告
  + force）；不改 vendor / parser / index schema。
- **H2** ✅ 零新 dep（pypdfium2 已係 Docling 自帶 dep，profiler 已用）。
- **H4** ✅ profiler 純文字 text-layer 信號，無 image embedding。
- **H6** ✅ backend guard + helper 寫 test（ingest pipeline module）。
- **H7** ⚠️→✅ upload 警告 design-stage expansion — 復用既有 banner primitive 視覺零發明（用戶批准方向），記 ADR-0065。
- **Karpathy** ✅ think（評估三候選 + DD-9 數據背書揀 grounded 的 guard）、simple（helper 復用 + 秒級 probe +
  既有 primitive）、surgical（pre-parse 插一點 + production-preserve）、surface（H1/H7 + guard 行為畀用戶揀）。

---

## §7 Changelog

- 2026-06-16 kickoff — plan active,F1-F4 scope locked;ADR-0065 Accepted（用戶揀做 P4 guard + 預檢警告 + force
  override）;落點 ground（`is_scan_pdf` 抽自 profiler probe / `_run_ingest_pipeline` parse 前插 guard /
  `force_scan` query 參數 / frontend `uploadDoc` + `banner-warning` primitive 復用）。
