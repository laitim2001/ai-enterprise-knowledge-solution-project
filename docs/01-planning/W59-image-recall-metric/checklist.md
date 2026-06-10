# W59 — image-recall-metric checklist

> 對應 `plan.md` F1–F5。daily tick。

## F1 — 標注 tooling
- [x] `scripts/dump_doc_images.py`(`list_documents` / `list_chunks` → image catalog,checksum dedup + doc_order sort)
- [x] ruff lint + format clean
- [x] live 跑通:列 service index → 列 KB 文件 → dump 圖清單
- [x] 確認 pilot KB = `drive-images-1`(6 模組圖密 Drive 財務手冊)
- [x] 資料品質驗證:checksum / doc_order(已 re-index,非 0)/ source_section(有層級)齊;alt_text 空
- [x] **用戶確認 pilot doc = AR 模組(0601)**(2026-06-10)

## F2 — ground truth schema + 標注
- [x] eval-set `ground_truth.expected_images` schema 定(checksum match key + `expected_image_sections` provenance;獨立檔不污染 v1-draft)
- [x] 標注粒度 = section-range 展開(用戶 2026-06-10 決定;222 圖驅動)
- [x] section→checksum 展開 helper(`scripts/image_recall_gt.py` expand;smoke 驗證 Q001=65 圖)
- [x] AR query 子集篩選(`worksheet` 子命令;keyword `AR0x` heuristic → 9 條)
- [x] 標注 guideline(worksheet `metadata.instructions` inline)
- [x] worksheet 產出:`reports/image_recall_worksheet_AR.yaml`(30 section + 9 AR query)
- [x] 建議起點預填(9 query `expected_sections`;檔內 `prefill_note` 標明「請覆核」)
- [x] HTML 視覺標注頁(`html` 子命令;`reports/image_recall_worksheet_AR.html` — 270 checkbox / 33 預勾 / section 縮圖;解 YAML 手填不便)
- [x] **用戶**喺 HTML 頁覆核勾選 → 匯出 `image_recall_worksheet_filled.json` → 跑 `expand`(2026-06-10)
- [x] GT 落地:`docs/eval-set-image-recall-ar.yaml`(9 query,expected_images checksum + section provenance)

**F2 完成** ✅

**F3 完成** ✅

## F3 — 指標 harness
- [x] `backend/eval/image_recall.py`(純邏輯:compute_metrics / extract_returned_checksums / aggregate / report_to_dict;match key = checksum,blob_url fallback)
- [x] `scripts/run_image_recall.py`(driver:POST 真實 `/query` full pipeline,抽 `citations[].embedded_images` checksum 對照 GT)
- [x] image-recall / image-precision 計算(per-query + aggregate;沒標 query 排除 — production-preserve)
- [x] ruff lint clean

## F4 — 跑 pilot 出實數
- [x] baseline 報告(現 production default config)→ `reports/image_recall_ar_baseline.yaml`(gitignored per §6.1;結果寫入 progress.md)
- [x] 9/9 scored:mean image-recall=0.5715 / mean image-precision=0.9824
- [x] Q001/Q036 mega-section synth(預期 65 圖)— `SYNTHESIZER_REQUEST_TIMEOUT_S=180` 解 30s timeout
- [x] 失敗案例分類(cap 天花板 / Q005 section miss / mega-section synth 負擔)→ progress.md

## F5 — 測試
- [x] 指標計算 unit test(空預期 / 空返回 / 部分命中邊界;11 test 全 PASS)
