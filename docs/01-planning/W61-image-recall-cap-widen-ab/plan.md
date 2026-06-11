---
phase: W61
name: image-recall-cap-widen-ab
status: closed       # draft | active | closed
created: 2026-06-11
owner: "Claude (AI) — 技術 Lead Chris 審閱"
gap: "§4.5 未盡之一 — cap 放寬軸 A/B(W59/W60 確認 cap 天花板是圖片召回真瓶頸的候選,本 phase 實證)"
adr: null            # 純 per-KB config toggle + eval 跑數 + 分析,零 code/schema/settings.py-default 改動 = §5.1「加 test」例外,預期無 ADR
spec_refs:
  - docs/01-planning/CONFIG_PLATFORM_W43-W58_ROLLUP.md §4.5  # 緣起 + 未盡部分(cap 放寬軸)
  - docs/01-planning/W59-image-recall-metric/                # harness + GT + baseline 來源
  - docs/01-planning/W60-image-recall-config-ab/             # DD-4 軸 A/B(本 phase 的姊妹軸)+ per-KB toggle 血淚教訓
  - docs/eval-set-image-recall-ar.yaml                       # 現成 AR 9-query GT
---

# W61 — 圖片召回 cap 放寬軸 A/B(max_images_per_answer 20→40→60)

> **緣起**:W59 baseline(mean recall 0.5715)失敗分類指認 **A. cap 天花板**(5 條 cap-bound query:
> Q001/Q036/Q043/Q003/Q038,returned 卡 ~18–20 vs 預期 37–73)= 「per-doc config 放寬 cap 直接槓桿」。
> W60 DD-4 軸 A/B 進一步證實 DD-4 三旋鈕對圖片召回**中性偏負**,並把「圖片召回真瓶頸 = cap 天花板」
> 列為下一槓桿。本 phase 把「放寬 cap 能否提升 cap-bound query 召回」由推測變實數。
>
> **用戶決策(2026-06-11)**:本輪做 **cap 放寬軸**(prose 型第二份 GT 延後,需用戶提供文件 + 親自標注)。
>
> **⚠️ 核心方法論(W60 血淚教訓,務必遵守 — memory `project_config_ab_per_kb_resolve_trap`)**:
> - `max_images_per_answer` **在 per-KB KbConfig 裡**(`GET /kb/drive-images-1` 確認現值 = 20),且
>   `/query` route 經 ADR-0040 `_resolve` 讀 **per-KB config**(query.py:492 `cap_images_per_answer(citations,
>   effective.max_images_per_answer)`)→ **正確 toggle = 改 per-KB config**(`PATCH /kb/{id}/settings`),
>   **絕不可用 process env override**(W60 第一次踩此坑,env 被 per-KB 鎖死 → 兩臂 identical → variance 誤判)。
> - `PATCH /kb/{kb_id}/settings` = **full KbConfig replacement**(omitted fields reset to default)→ 必須先
>   `GET /kb/{id}` 取現 config、**只改 `max_images_per_answer` 單一 field**、再 PATCH 整個 object back。
> - cap 在 **query time** apply(非 ingestion)→ 改 cap **即時生效,不需 reindex / 重啟**。
> - **跑完務必把 cap 改回原值 20**(GET readback 確認)。
> - **真 sanity gate = GET readback 確認 cap 已變**(非「重現 baseline」;後者可能來自 config 沒變 = 假 gate)。

## 1. 範圍(Scope)

用**現有 AR 9-query GT**(`docs/eval-set-image-recall-ar.yaml`)跑 controlled A/B,量化把
`drive-images-1` per-KB `max_images_per_answer` 由 20 放寬到 40 / 60 對 image-recall 的影響,
**且實證「cap 是否真 binding constraint」**:

- **A 臂(baseline)**:`max_images_per_answer=20`(現值;W59/W60 已 4× corroborate ~0.572)。
- **B 臂**:`max_images_per_answer=40`。
- **C 臂**:`max_images_per_answer=60`。
- 三臂**唯一變數 = `max_images_per_answer`**;同 `/query` path、同 KB(`drive-images-1`)、同
  `SYNTHESIZER_REQUEST_TIMEOUT_S=180`(mega query Q001/Q036 timeout 非 confounding)、同
  `HYBRID_USE_SEMANTIC_RANKER=false`(繞 Free-tier 402)、同 driver `run_image_recall.py`(零 code 改動)。

**焦點 vs 對照**:
- **焦點 = 5 條 cap-bound query**(Q001/Q036 預期 67,Q043 預期 73,Q003/Q038 預期 37;cap=20 下 recall
  上限 0.30–0.54)。
- **對照 = 4 條 non-cap-bound query**(Q002 預期 18 / Q004 預期 12 / Q006 預期 8 全 ≤20 → cap 永不 binding,
  recall **必須持平**;Q005 預期 32 但 W59 歸 section-miss 型 stochastic,returned 卡 9 ≪ cap → 放寬 cap 預期
  **無反應**)。對照臂若有移動 = 純 variance / noise baseline 證據。

## 2. 交付物(Deliverables)

| # | 交付 | 檔案 / 位置 | Gate |
|---|---|---|---|
| **F1** | pre-flight(azurite + index `drive-images-1` + Langfuse/Postgres health)+ 確保 backend 於 documented env(180s timeout,有需要重啟,查 multi-session collision)+ 跑 A 臂 baseline(cap=20)| `reports/image_recall_ar_cap20.yaml` | 9/9 scored + Q001/Q036 mega-query 無 error + mean ≈ 0.572 |
| **F2** | `PATCH cap=40` → `GET readback=40`(真 sanity gate)→ 跑 ×2 | `reports/image_recall_ar_cap40_r{1,2}.yaml` | readback 確認 40 + 各 9/9 scored |
| **F3** | `PATCH cap=60` → `GET readback=60`(真 sanity gate)→ 跑 ×2 | `reports/image_recall_ar_cap60_r{1,2}.yaml` | readback 確認 60 + 各 9/9 scored |
| **F4** | `PATCH restore cap=20` → `GET readback=20`(復原) | (per-KB config) | readback 確認 20 |
| **F5** | A/B 分析:per-query recall / precision / **returned_count** 跨 20/40/60 三臂對比 → cap-binding 判決(returned 有無升向新 cap)+ recall 提升幅度 + precision 是否退 + 對照臂是否持平 → progress.md;結論落 rollup §4.5 | progress.md + rollup §4.5 | 對比表 + 判決 |

## 3. Acceptance Criteria

- **AC1**(F1):A 臂 baseline 9/9 出數,Q001/Q036 mega-query 無 timeout error,mean recall **≈ 0.572 ±
  合理 variance**(重現 W59/W60 baseline → 證明本 session machine/backend 條件正常;若大幅偏離 → STOP 查
  confounding)。
- **AC2**(F2/F3):每次 PATCH 後 **GET readback 確認 cap = 目標值**(真 sanity gate,非靠 eval 輸出);
  B/C 臂各 9/9 出數。
- **AC3**(F5 — cap-binding 判決):指認放寬 cap 後 cap-bound query 的 **returned_count 有無升向新 cap**:
  - **升向 cap**(e.g. cap=40 時 returned→~40)→ **cap 確為 binding**,放寬 cap 是 cap-bound query 的有效槓桿。
  - **持平 ~20**(放寬無反應)→ **cap 非真 binding**;真 binding = upstream 候選圖供給(retrieval / neighbour
    attachment)→ **反證 W59「cap 是瓶頸」**,§4.6 結構路線需重評。
- **AC4**(F5 — recall/precision 判決):量化 5 條 cap-bound query 的 recall 提升(20→40→60)+ precision 是否
  因 surface 非 GT 圖而退(precision tradeoff);**對照 4 條 non-cap-bound 是否持平**(持平 = 乾淨;移動 =
  variance baseline)。
- **AC5**(F4 復原 + H 核對):跑完 cap 改回 20 並 GET readback 確認;純 per-KB config toggle + 跑數 + 分析,
  **零 code/schema/settings.py-default 改動** → 不觸 H1;match signal 仍 checksum(無 image embedding,守 H4);
  不碰 .env file(H5)。

## 4. 風險

- **R1 🟡 假 binding 反證**:放寬 cap 後 returned 持平 ~20 → cap 非真瓶頸。緩解:AC3 把此情況明文為**有效**
  結論(反證 W59 假設亦是進展,非失敗),不硬說 cap 有益。
- **R2 🟡 precision 崩**:放寬 cap surface 大量低排名非 GT 圖 → precision 由 0.98 大跌。緩解:AC4 同步量
  precision;若 recall↑precision↓ = tradeoff,如實記錄(放寬 cap 非無代價)。
- **R3 🟡 mega query timeout**:Q001/Q036(含 S04 44-image mega-section)synth 慢。緩解:backend 用
  `SYNTHESIZER_REQUEST_TIMEOUT_S=180`(per W59 DD-7);driver client timeout 300s。
- **R4 🟡 single-run variance**:cap-bound query 雖非 borderline(大 GT),但 retrieval 排名有 run-to-run 抖動。
  緩解:B/C 臂各跑 2 次取 band;Q005 已知 stochastic(returned 0↔9),不據單次判。
- **R5 🟢 忘記復原 cap**:緩解:F4 為獨立 deliverable + AC5 GET readback gate;progress.md 結尾複查。
- **R6 🟢 backend 自死 / venv dual-process / multi-session collision**:緩解:長 A/B 用自己起、可監控的 backend;
  清殘留以 port 8000 LISTEN PID 為準,勿殺 system-path child;重啟前查有無另一 session 在動(memory
  `project_backend_venv_dual_process` + `project_multi_session_restart_collision`)。

## 5. 非目標(Non-goals)

- ❌ **prose 型第二份 GT**(§4.5 未盡之二)— 延後,需用戶提供 prose 文件 + 親自標注 GT。
- ❌ **DD-4 軸**(W60 已做,結論中性偏負)。
- ❌ **改 settings.py global default / 改揀圖排序 / 改 pipeline**(本 phase 只 per-KB toggle + 跑數,跑完復原)。
- ❌ **把 cap 放寬寫成 drive-images-1 production 持久配置**(本 phase 只實證槓桿效力;是否持久化由用戶按實數決定)。
- ❌ **把圖片指標 wire 進 production eval gate**(W59 已列 non-goal,不變)。

## 6. ADR / Hard Constraint 核對(H1–H7)

- **H1**:零 code/schema/vendor/storage/settings.py-default 改動;cap toggle 是 **per-KB config 暫時改動**
  (跑完復原 20,非改 default)→ **不觸 H1,預期無 ADR**。
- **H4**:match signal 限 `checksum_sha256` → 無 image embedding / 視覺檢索(守 Tier 1 紅線)。
- **H5**:**不讀不改 .env file**;per-KB config 經 API PATCH + mock auth `Bearer dev-token`。
- **H6**:零新 code(重用 W59 `backend/eval/image_recall.py` + `scripts/run_image_recall.py`,已有 11 test)。
- **H7**:無前端改動 → 不觸發。

## 7. Changelog

| Date | Change | Reason |
|---|---|---|
| 2026-06-11 | Initial plan(active)| rollup §4.5 未盡之一;用戶選「cap 放寬軸」;方法論核實 = per-KB config toggle(`PATCH /kb/{id}/settings` full replacement)+ GET readback 真 sanity gate + returned_count 量 cap-binding(W60 env-override 踩坑教訓);三臂 20/40/60,焦點 5 條 cap-bound,對照 4 條 non-cap-bound |
| 2026-06-11 | **Phase closed**(F1–F5 全 done)| controlled A/B 5 runs:**cap=20 確 binding 但真天花板 = upstream 候選供給 ~26–33(非 cap)**;cap-bound returned 20→26–35(cap=40)但 40→60 零增長(plateau 26–33,2 runs 穩定);recall cap=20→40 partial gain +0.09~+0.17 / precision 維持 0.95–1.00(額外圖 GT-correct)/ 對照 3 條完美持平;**mega-query(GT 65–73)即使 cap 無限 recall 上限 ~0.40–0.51 → cap 放寬單獨不足以填缺口,真瓶頸 = 供給側(§4.6)**。AC1–AC5 全達(baseline 重現 0.574 / 每臂 GET readback gate / cap-binding 決定性判決 / 復原 cap=20)。零 code 改動(重用 W59 harness)→ 無 ADR(§5.1 加 test 例外)。Q005 高度 stochastic 跨 5 runs 印證;cap=60 首 run Azure transient 502 單次重試恢復。🚧 prose 第二份 GT 仍欠(硬依賴用戶) |
