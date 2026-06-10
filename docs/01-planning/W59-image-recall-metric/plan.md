---
phase: W59
name: image-recall-metric
status: closed       # draft | active | closed
created: 2026-06-10
owner: "Claude (AI) — 技術 Lead Chris 審閱"
gap: "新缺口(藍圖 3-gap 以外)— 圖片側召回指標(CONFIG_PLATFORM_W43-W58_ROLLUP.md §4.5)"
adr: null            # 加 eval/指標 = §5.1「加 test」例外,不觸 H1 → 預期無 ADR(§6 核對)
spec_refs:
  - docs/01-planning/CONFIG_PLATFORM_W43-W58_ROLLUP.md §4.5  # 緣起 + 提議
  - docs/eval-methodology.md                                  # eval 方法學(指標定義對齊)
  - docs/eval-set-v0.yaml                                     # ground truth 擴展對象(現有 expected_screenshot_chunks seam)
  - backend/api/routes/config_test.py                        # full-pipeline harness 復用範本(execute_query_pipeline)
  - backend/eval/orchestrator.py                             # image_association placeholder seam(L80-85)
---

# W59 — 圖片召回指標(image-recall / image-precision)

> **緣起**:文字側可系統性收斂(R@5 / faithfulness / `distinct_sections`),但**圖片側的「成功」
> 至今全靠肉眼在 UI 驗證** —— eval set 沒標「每條 query 預期返回哪幾張圖」,因此「文字 + 相關圖片齊腳」
> 這個產品核心目標**無法量度、無法系統性改善**(rollup §4.5)。本 phase 令它首次可量度。
>
> **用戶決策(2026-06-10)**:① 先一份 pilot 圖密手冊;② AI 建標注 tooling、用戶填 ground truth
> (「哪幾張圖相關」需領域判斷)。
>
> **核實前置(本 session,防掛錯路徑)**:三條 eval 路徑核實 ——
> - `runner.py`(`EvalRunner`)= **retrieve-only**,只算 R@5,不碰圖片。
> - `orchestrator.py`(`run_eval_pipeline`)RAGAs path 用 `synthesizer.synthesize()` 拿純文字答案,
>   **不經揀圖鏈**;圖片是 `image_association=0.0` 明文 placeholder(L80-85)。
> - `config_test.py`(`execute_query_pipeline`)= **唯一跑 full pipeline + 已提取最終圖片**
>   (`_figure_counts`)的路徑,但單 query、無 eval set、無 ground truth。
>
> → **圖片召回指標必須復用 `execute_query_pipeline` 跑 eval set,不可掛 orchestrator 的 RAGAs path**
> (否則量到的不是用戶真正看到的圖片集 — 同 memory `project_v4_retrieve_only_vs_query_pipeline` 陷阱)。

## 1. 範圍(Scope)

為**一份 pilot 圖密步驟手冊**建立圖片召回量度能力:

1. **標注 tooling**:script dump 出該文件所有圖的穩定 identity(`doc_order` + `checksum_sha256` +
   `source_section` + `blob_url`),供用戶對照文件填 ground truth。
2. **Ground truth schema**:eval set 每條 query 加 `expected_images`(image-level,checksum 為 match key、
   `doc_order` 為人類可讀錨)。production-preserve:沒標的 query 不參與圖片指標。
3. **指標 harness**:復用 `execute_query_pipeline`(full pipeline)跑 eval set,提取最終返回圖片,
   對照 ground truth 算 **圖片召回率(image-recall)** + **圖片精確率(image-precision)**,per-query + aggregate。
4. **跑 pilot 出實數**:現 production default config 的圖片召回率 baseline(可選 A/B vs DD-4 config)。

**Pilot 文件**:一份圖密步驟手冊;候選 = AR KB(`test-kb-20260531-v1`)主文件,F1 dump 後與用戶確認最終 `doc_id`。

## 2. 交付物(Deliverables)

| # | 交付 | 檔案 / 位置 | Gate |
|---|---|---|---|
| **F1** | 標注 tooling:`scripts/dump_doc_images.py`(或 `backend/eval/` 內)— 輸入 `kb_id` + `doc_id`,dump 該文件全圖清單(`doc_order` / `checksum_sha256` / `source_section` / `blob_url`)成 yaml/csv。**並與用戶確認 pilot `doc_id`** | C06 / scripts | 跑得出清單 + 用戶確認 doc |
| **F2** | Ground truth schema + 範本:eval set `ground_truth.expected_images`(list of checksum,可選 `(doc_id, doc_order)`)+ 標注 guideline(「相關」定義 + section-range fallback)。**用戶據 F1 清單填** | docs/eval-* | schema 定 + 範本給用戶 |
| **F3** | 指標 harness:`backend/eval/image_recall.py` — 復用 `execute_query_pipeline` 跑標注 query,提取 `resp.citations[].embedded_images` checksum 集,對照 `expected_images` 算 image-recall / image-precision(per-query + aggregate)| C06 | **gated on F2 ground truth** |
| **F4** | 跑 pilot 出實數報告:現 default baseline(+ 可選 A/B vs DD-4 config)→ 報告「pilot 文件圖片召回率 = X%,失敗案例分類」 | reports/ | gated on F3 + 標注完成 |
| **F5** | 指標計算 unit test(recall/precision 純函數 + 邊界:空預期 / 空返回 / 部分命中) | test | gated on F3 |

## 3. Acceptance Criteria

- **AC1**(F1 tooling):dump 出 pilot 文件**完整**圖清單,每張有 `doc_order` + `checksum_sha256` +
  `source_section` + `blob_url`,人可對照文件辨認「第幾張圖」並填 ground truth。
- **AC2**(F2 schema):eval set 支援 image-level `expected_images`;**production-preserve** —— 沒標
  `expected_images` 的 query **不參與**圖片指標(不影響現有 R@5 / RAGAs 流程)。
- **AC3**(F3 落點):harness 經 **`execute_query_pipeline`(full pipeline)** 取最終圖片,**非**
  orchestrator RAGAs path;match key = `checksum_sha256`(內容雜湊,re-index 穩定)。
- **AC4**(F3 指標):image-recall = |返回 ∩ 預期| / |預期|;image-precision = |返回 ∩ 預期| / |返回|;
  per-query + aggregate;沒標的 query 排除於 aggregate。
- **AC5**(F4 實數):跑 pilot 得出 baseline 實數 + 失敗案例分類(例:跨頁圖 / 未被 cite 的 section),
  令「真的可行嗎」由哲學問題變實證問題(rollup §4.1)。
- **AC6**(F5 test):recall/precision 計算 unit-tested(含邊界)。
- **AC7**(H1/H4 核對):純加 eval/指標 + additive schema field;不動 index schema、不動揀圖行為、
  不動 pipeline;match signal 只用 `checksum` / `doc_order` / `source_section`,**無 image embedding**。

## 4. 風險

- **R1 🟡 「相關」主觀**:ground truth「哪幾張圖相關」是領域判斷。緩解:F2 標注 guideline 寫清楚 +
  提供 **section-range fallback 定義**(預期 section 內整段步驟圖算齊),令標注可收斂、不逐張糾結。
- **R2 🟡 harness 整合**:`execute_query_pipeline(qreq, request, effective, settings)` 依賴 `request`
  拿 `app.state`(config_test 在 route handler 內滿足)。F3 需決定:做成 route(`POST /eval/image-recall`,
  有 request)或建 offline harness 注入 `app.state`。傾向**沿 config_test route-based 模式**(最小驚訝)。
- **R3 🟡 Free-tier semantic 402**:圖密 KB hybrid 撞 Free-tier semantic cap → 用
  `HYBRID_USE_SEMANTIC_RANKER=false` 繞(per memory)。
- **R4 🟢 標注規模**:pilot 控制在該文件 ~13–30 條 query,單份成本可控。
- **R5 🟢 checksum 穩定性**:`checksum_sha256` = 圖內容雜湊,re-index 不變 → 作 match key 穩定
  (優於 `doc_order`,後者跨 re-index 理論上可變)。

## 5. 非目標(Non-goals)

- ❌ **改揀圖 / 排序行為** —— 本 phase **只量度,不改 pipeline**(改善留後續 phase,由實數驅動)。
- ❌ **caption 文字化 / 多模態檢索**(rollup §4.6 結構性路線 = H1 / Tier 2,須先有實數再議)。
- ❌ **一次標多份文件**(pilot only;驗證 pipeline 通了再擴)。
- ❌ **把圖片指標 wire 進 production eval gate**(先出數;gate 整合是後續決定)。
- ❌ **Gap B query 意圖 gate**(本指標出數後才有判據)。

## 6. ADR / Hard Constraint 核對(H1–H7)

- **H1**:加 eval/指標 = §5.1 明文例外(「加 test」);additive schema field(`expected_images` /
  指標 field)production-preserve,不改 vendor / storage layout / component interface 本質 → **不觸 H1,預期無 ADR**。
  (若 F3 發現必須改 `execute_query_pipeline` signature 或 index schema = STOP+ask,可能要 ADR。)
- **H4**:match/score signal 限 `checksum` / `doc_order` / `source_section`(文字 / 位置);**無 image
  embedding / 視覺檢索** → 守 Tier 1 邊界(藍圖 §3.3 紅線)。
- **H6**:F3 指標計算屬 `backend/eval/` → F5 unit test(對齊 H6 eval 模組要求)。
- **H7**:無前端改動 → 不觸發。
- **H5**:dump tooling 只輸出 `blob_url`(已是 SAS-less 內部引用)+ checksum,無 secret/PII。

## 7. Changelog

| Date | Change | Reason |
|---|---|---|
| 2026-06-10 | Initial plan(draft)| rollup §4.5 + 用戶選定「圖片召回指標」為下一開發焦點 + scope(pilot 一份圖密手冊 / AI 建 tooling + 用戶填)|
| 2026-06-10 | **Phase closed**(F1–F5 全 done)| baseline 9/9 出數:mean image-recall=0.5715 / image-precision=0.9824;失敗分類 = A.cap 天花板 5 條 + B.≤cap 全召回 3 條 + C.section miss(Q005)1 條;AC1–AC7 達成;Q001/Q036 mega-section synth 用 `SYNTHESIZER_REQUEST_TIMEOUT_S=180` 解 30s timeout;無 ADR(§5.1「加 test」例外確認)|
