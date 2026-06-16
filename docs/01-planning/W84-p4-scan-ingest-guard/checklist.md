# W84 checklist — P4 掃描件 ingest 預檢 guard + force override（ADR-0065）

> Atomic items per deliverable。每日 tick。Source of truth = `plan.md`。

## F1 — Backend `is_scan_pdf` helper + ingest guard + force flag
- [ ] F1.1 `profiler.py` 抽 module-level `is_scan_pdf(source_path) -> bool`（復用 `_probe_pdf_text_layer` + P4 threshold）+ profiler 自身復用（零行為改變）
- [ ] F1.2 `_run_ingest_pipeline` 加 `force_scan` 參數 + guard（`.pdf` + `is_scan_pdf` + 非 force → 422 `ingest.scan_requires_confirm`，插 tmpfile 後 / select_parser 前）
- [ ] F1.3 `upload_document` + reindex endpoint 加 `force_scan: bool = False` query 參數 → 傳落 pipeline
- [ ] F1.4 pytest：scan 無 force → 422 / scan + force → 跳 guard / born-digital PDF → 照常 / docx → 跳 probe；`is_scan_pdf` unit test（scan / born-digital / 非 PDF）
- [ ] F1.5 回歸：profiler 既有 test 全綠（helper 復用零行為改變）
- [ ] F1 gate：mypy strict + ruff clean + pytest 綠

## F2 — Frontend force UI
- [ ] F2.1 `kb.ts` `uploadDoc(kbId, file, forceScan = false)` + `?force_scan=` + 422 解析 `scan_requires_confirm` → typed error / sentinel
- [ ] F2.2 `upload/page.tsx` 接 `scan_requires_confirm` → 警告 banner（`banner-warning` 復用視覺零發明）+ 「仍要繼續」按鈕 → `uploadDoc(..., true)` 重試
- [ ] F2 gate：type-check 0 + lint 零新 warning + build ✓

## F3 — Browser 驗（playwright）
- [ ] F3.1 upload scan PDF（`scanned_pdf_sample/`）→ reject 路徑秒級判 P4 → 警告 banner + 「仍要繼續」按鈕出現
- [ ] F3.2 born-digital PDF / docx upload → 無警告正常（production-preserve 視覺驗）
- [ ] F3 gate：scan reject 路徑警告 render PASS；force OCR 路徑 backend test 覆蓋（browser 不跑足 8-9.5 分鐘）

## F4 — closeout
- [ ] F4.1 backend test + type-check/lint/build + browser 全綠
- [ ] F4.2 plan closed + progress retro
- [ ] F4.3 ADR-0065 README index
- [ ] F4.4 DEFERRED_REGISTER DD-9 更新（收窄至只剩 OCR 慢 Tier 2）
- [ ] F4.5 memory 更新（W84 段 + DD-9 收窄）
