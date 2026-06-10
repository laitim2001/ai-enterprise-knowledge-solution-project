# W59 — image-recall-metric progress

## Day 1 — 2026-06-10

### 做咗
- Plan kickoff(`plan.md` draft → active)。緣起 = rollup §4.5 圖片召回指標缺口;用戶選定為下一開發焦點。
- **核實前置**(防掛錯路徑):三條 eval 路徑核實 —— `runner.py` = retrieve-only(無圖);
  `orchestrator.py` RAGAs path 用 `synthesize()` 不經揀圖鏈(`image_association=0.0` placeholder);
  `config_test.py` 經 `execute_query_pipeline` = 唯一有最終圖片的路徑 → **指標必須復用此路**。
- **F1 done**:`scripts/dump_doc_images.py`(對齊 `discover_chunk_ids.py` 風格;`HybridSearcher.list_documents`
  / `list_chunks` + `parse_embedded_images`;checksum dedup + doc_order sort)。ruff clean。live 跑通。

### 發現 / 決策
- **Live service 只有 3 個 index**:`drive-images-1` / `w54-live-ab-1` / `w56-drive-ab-1`。
  舊測試 KB(test-kb-2026053x)+ `drive_user_manuals`(`ekp-kb-drive-v1`)已不在(404)。
- **Pilot KB = `drive-images-1`** = 圖密 Drive 財務手冊 6 模組(AR 90 / AP 83 / FA 78 / GL 74 / CB 28 / BM 16 chunks)。
- **AR 模組 dump 結果**:90 chunks → **222 distinct images**(252 instances)→ 極度圖密。
  catalog: `reports/image_catalog_drive-images-1_drive-user-manual-0601-ar-fna-ar-management-v0-03.yaml`。
- **資料品質**:checksum ✅ / doc_order ✅ 非 0(已 re-index)/ source_section ✅ 有層級 / alt_text ❌ 全空。
- **對 F2 的含意**:222 圖逐張標不現實 → 傾向 **section-range 標注介面**(標注者指定預期 section,
  helper 展開成該 section 全圖 checksum;checksum 仍是底層 match key)。修正第一輪「逐張 by checksum」設想。

### 決策(2026-06-10 用戶拍板)
- **Pilot doc = AR 模組(0601)**(`drive-user-manual-0601-ar-fna-ar-management-v0-03`,222 圖)。
- **標注粒度 = section-range 展開**(標 section,helper 展開成全圖 checksum;checksum 仍底層 match key)。

### Query 來源確認(F2 前提已備)
- **`docs/eval-set-v1-draft.yaml`**(55 條,Chris 2026-06-04 SME-validated,content-based GT)= AR/AP/FA/CB/GL/BM
  六模組財務手冊 query,領域對上 `drive-images-1`。`ground_truth` 已有 `expected_screenshot_chunks`(空 seam)
  → 加 `expected_images` 順理成章。AR query 在其中(Q001 payment collection / AR01…)。
- ⚠️ 兩點待 F2 處理:(1) eval set `created_by` 基於舊 `ekp-kb-drive-v1`(已 404),query 為領域性、對 AR 文件仍適用,
  但需設 `kb_id=drive-images-1`;(2) query 無模組標記 → 需從 keyword(AR01…)/ 內容篩出 AR 子集。

### F2 tooling done(2026-06-10)
- `scripts/image_recall_gt.py`(`worksheet` / `expand` 兩子命令,純檔案操作無 Azure)。ruff clean。
- **worksheet 產出**:`reports/image_recall_worksheet_AR.yaml` — 30 section index(AR01→AR10,各 overview + 步驟圖,
  含 image_count / doc_order_range / checksums)+ 9 條 AR query(Q001-006 + Q036/038/043)+ 空 `expected_sections`。
- **AR 篩選**:keyword `AR0x` heuristic(非 OOS)→ 9 條。注:Q051(customer payment journal field)keyword 無 AR code 未入,
  如需可手動補。
- **expand smoke 驗證**:Q001=[S03,S04,S05,S06] → `expected_images`=65 圖(1+44+9+11 無跨 section 重複)+ provenance
  + kb_id/doc_id 正確。temp 檔已清。
- **schema**:image-recall eval set `ground_truth.{expected_images(checksum match key), expected_image_sections(provenance)}`
  + per-query kb_id/doc_id;輸出獨立檔(不污染 v1-draft 註解)。
- **資料觀察**:S04(AR01 步驟)44 圖、S11(AR03)23 圖、S22(AR07)20 圖 = 圖洪水 section(真實結構);
  S29/S30 section_path 只有編號無標題(`['11','11.1.3']`)= parser heading 抽取限制,標注可斟酌。

### F2 HTML 標注頁(2026-06-10 — 應用戶「YAML 手填不便」)
- `image_recall_gt.py` 加 `html` 子命令:worksheet → self-contained HTML(每 query 30 section checkbox + 該 section
  縮圖,建議預勾,一鍵匯出填好 JSON 餵 expand)。產出 `reports/image_recall_worksheet_AR.html`(454KB;270 checkbox /
  33 預勾 / 1998 縮圖 ref / wsdata 嵌入)。圖靠 azurite blob_url 渲染。**dev tooling 非 EKP 產品前端 → 不涉 H7**。
- 建議起點已預填 9 query(`prefill_note` 標明請覆核)。
- 注:Windows console cp1252 印中文會 UnicodeEncodeError → script print 一律英文(HTML 檔本身 utf-8 寫,無礙)。

### azurite 看圖修復(2026-06-10 — 用戶 report HTML 圖看不到)
- 診斷:azurite 之前沒跑 → native 啟動(loaded machine ~75s 才 listen 10000)→ blob anonymous GET **403**
  (container 預設拒 anonymous,**非** azurite 故障;chat UI 經 backend/SAS 故能顯示)→ 設
  `ekp-kb-drive-images-1-screenshots` container public(`set_container_access_policy public_access=blob`,
  via `UseDevelopmentStorage=true`)→ 200。
- playwright(file:// 被阻 → 起 http.server serve reports/)截圖確認圖**實際渲染**(Q001 S01-S05 縮圖全顯示)。
- 記 memory [[project_azurite_anonymous_blob_public]]。

### F2 完成(2026-06-10)
- 用戶喺 HTML 標注頁(含 lightbox)覆核 9 條 AR query 勾選 → 匯出 `docs/06-reference/image_recall_worksheet_filled.json`
  → 跑 `expand` → **GT 落地 `docs/eval-set-image-recall-ar.yaml`**(9/9 labeled)。
- 每 query expected_images 數:Q001/Q036=65、Q002=18、Q003/Q038=37、Q004=12、Q005=32、Q006=8、Q043=73
  (對應 section 圖數加總正確;sum=347,文件 distinct=222 圖,跨 query 有重疊屬正常)。
- 用戶採用建議起點(9 條全填,與預填一致)。

### 待 / 下一步(F3)
- 寫 `backend/eval/image_recall.py` — 復用 `execute_query_pipeline`(full pipeline)跑 GT 9 query,
  提取 `resp.citations[].embedded_images` checksum 集,對照 `expected_images` 算 image-recall / image-precision。
- 需 backend 起 + azurite + Free-tier semantic 用 `HYBRID_USE_SEMANTIC_RANKER=false` 繞。
