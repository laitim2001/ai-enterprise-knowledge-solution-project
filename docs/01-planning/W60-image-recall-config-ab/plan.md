---
phase: W60
name: image-recall-config-ab
status: active       # draft | active | closed
created: 2026-06-11
owner: "Claude (AI) — 技術 Lead Chris 審閱"
gap: "§4.5 未盡之一 — per-config A/B 對比(DD-4 前後對 image-recall 的影響)"
adr: null            # 純 eval 跑數 + 分析,零 code/schema/default 改動 = §5.1「加 test」例外,預期無 ADR
spec_refs:
  - docs/01-planning/CONFIG_PLATFORM_W43-W58_ROLLUP.md §4.5  # 緣起 + 未盡部分
  - docs/01-planning/W59-image-recall-metric/                # harness + GT + baseline 來源
  - docs/eval-set-image-recall-ar.yaml                       # 現成 AR 9-query GT
  - docs/adr/0052-chat-rag-quality-flag-production-default-flip.md  # DD-4 = A/B 對比軸
---

# W60 — 圖片召回 per-config A/B(DD-4 前後)

> **緣起**:W59 建立 image-recall 指標 + AR 圖密手冊 9-query baseline(mean recall 0.5715 /
> precision 0.9824),但只跑 **single config**(且當時是 **pre-DD-4** default,2026-06-10)。
> rollup §4.5 末「未盡部分」之一 = **per-config A/B 對比**,把「DD-4 flip 對圖片召回有無 side-effect」
> 由推測變實數。
>
> **用戶決策(2026-06-11)**:① 先做 A/B(prose 型第二份 GT 延後,需用戶提供文件 + 親自標注);
> ② A/B 軸 = **DD-4 前後**(W59 baseline 剛好 pre-DD-4 = 天然 A 臂)。
>
> **方法論核實(本 session,防掛錯 path)**:
> - `ConfigTestResult`(`/config-test`)response **只有圖數 counters**(`figure_count_raw/dedup`),
>   **無圖片 checksum 集** → 無法算 recall(需 set intersection)。
> - `/query` response 有 `citations[].embedded_images[].checksum_sha256` → **唯一可算 recall 的 path**
>   (W59 baseline 同 path)。
> - DD-4 三旋鈕含 `enable_parent_doc_retrieval`(檢索入口),per ADR-0050 **不在** per-doc/per-query
>   override → 只能由 **global default** 控制 → 用 **process 環境變數**(非 `.env` file,守 H5)toggle。
> - → **A/B = 兩次重啟 backend(同 `/query` path、同 KB、同 timeout),只變 DD-4 三旋鈕**;
>   driver `run_image_recall.py` **零 code 改動**。

## 1. 範圍(Scope)

用**現有 AR 9-query GT** 跑 controlled A/B,量化 DD-4 flip(ADR-0052)對 image-recall 的影響:

- **B 臂(post-DD-4,現 production default)**:`enable_parent_doc_retrieval=True` /
  `citation_expansion_max_aux=10` / `citation_expansion_section_path_prefix_depth=1`(settings.py 新 default)。
- **A 臂(pre-DD-4)**:process env override 三旋鈕回舊值(`False` / `2` / `0`)。
- 兩臂**唯一變數 = DD-4 三旋鈕**;同 `/query` path、同 KB(`drive-images-1`)、同
  `SYNTHESIZER_REQUEST_TIMEOUT_S=180`(確保 mega query timeout **非** confounding)、同
  `HYBRID_USE_SEMANTIC_RANKER=false`(繞 Free-tier 402)。
- A 臂應 **≈ 重現 W59 baseline 0.5715**(sanity:證明 controlled 重現 + DD-4 是唯一變數)。

## 2. 交付物(Deliverables)

| # | 交付 | 檔案 / 位置 | Gate |
|---|---|---|---|
| **F1** | pre-flight(azurite + index `drive-images-1` populated + Langfuse/Postgres health)+ 重啟 backend(B 臂 env)+ 跑 B 臂 9/9 | `reports/image_recall_ar_postdd4.yaml` | 9/9 scored |
| **F2** | 重啟 backend(A 臂 env override DD-4 三旋鈕)+ 跑 A 臂 9/9 | `reports/image_recall_ar_predd4.yaml` | 9/9 scored + ≈ W59 0.5715 sanity |
| **F3** | A/B 對比分析:per-query recall/precision delta + mean delta + 失敗分類變化(cap 天花板 5 條 / B 類 / Q005 section miss 在 DD-4 前後點變)→ progress.md | progress.md | 對比表 + 結論 |
| **F4** | 結論落 rollup §4.5(DD-4 對 image-recall 實證)+ DEFERRED_REGISTER §4.5 未盡更新(A/B done,prose 仍欠)| rollup + DEFERRED_REGISTER | doc-sync |

## 3. Acceptance Criteria

- **AC1**(F1):B 臂(post-DD-4 現 default)9/9 出數,mean recall/precision 有實數。
- **AC2**(F2):A 臂(pre-DD-4 env override)9/9 出數,且 mean recall **≈ 0.5715 ± 合理 variance**
  (重現 W59 baseline → 證明 env toggle 生效 + DD-4 唯一變數;若大幅偏離 → STOP 查 confounding)。
- **AC3**(F3):per-query A/B delta 出齊;指認 DD-4 令**哪些 query** recall 改善 / 退化 / 不變,
  並對齊 W59 失敗分類(A.cap 天花板 / B.≤cap / C.Q005 section miss)。
- **AC4**(F4):結論「DD-4 對圖片召回的淨影響 = X」寫入 rollup §4.5;§4.5 未盡更新(A/B ✅ / prose 🚧)。
- **AC5**(H 核對):純跑數 + 分析,**零 code/schema/default 改動**(env override 是 process env,非 .env file)
  → 不觸 H1;match signal 仍 checksum(無 image embedding,守 H4);不碰 .env file(H5)。

## 4. 風險

- **R1 🟡 A 臂無法重現 baseline**:若 A 臂 ≠ 0.5715,代表有其他 confounding(KB re-index / chunk 變 /
  timeout)。緩解:AC2 設 sanity gate,偏離大 → STOP 查,不硬出對比。
- **R2 🟡 mega query timeout**:post-DD-4 context 更重,Q001/Q036 synth 更慢。緩解:兩臂都用
  `SYNTHESIZER_REQUEST_TIMEOUT_S=180`(timeout 非 confounding;DD-7 production 120s 不在本 A/B 範圍)。
- **R3 🟢 重啟成本**:兩次 backend 重啟(loaded machine 50-120s+)= 慢非 hang,只輪詢 /health
  (per memory `project_loaded_machine_startup_infra_recovery`)。
- **R4 🟢 venv dual-process**:重啟用 `backend\.venv\Scripts\python.exe`,清殘留以 port 8000 LISTEN PID
  為準,勿殺 system-path child(per memory `project_backend_venv_dual_process`)。

## 5. 非目標(Non-goals)

- ❌ **prose 型第二份 GT**(§4.5 未盡之二)— 延後,需用戶提供 prose 文件 + 親自標注 GT。
- ❌ **cap 放寬軸 A/B**(用戶本輪選 DD-4 前後一軸;cap 軸留候選)。
- ❌ **改揀圖 / 排序 / pipeline / default**(本 phase 只跑數對比,零行為改動)。
- ❌ **把圖片指標 wire 進 production eval gate**(W59 已列 non-goal,不變)。

## 6. ADR / Hard Constraint 核對(H1–H7)

- **H1**:零 code/schema/vendor/storage/default 改動;env override 是 **process 環境變數**(臨時,非
  持久 .env file,非 settings.py default 改)→ **不觸 H1,預期無 ADR**。
- **H4**:match signal 限 `checksum_sha256` → 無 image embedding / 視覺檢索(守 Tier 1 紅線)。
- **H5**:**不讀不改 .env file**;用 process env(`$env:...`)+ mock auth `Bearer dev-token`。
- **H6**:零新 code(重用 W59 `backend/eval/image_recall.py` + `scripts/run_image_recall.py`,已有 11 test)。
- **H7**:無前端改動 → 不觸發。

## 7. Changelog

| Date | Change | Reason |
|---|---|---|
| 2026-06-11 | Initial plan(active)| rollup §4.5 未盡之一;用戶選「先 A/B、軸 = DD-4 前後」;方法論核實 = /query path + process env toggle + 兩次重啟(config-test response 無 checksum)|
