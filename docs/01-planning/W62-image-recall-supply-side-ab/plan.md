---
phase: W62
name: image-recall-supply-side-ab
status: closed       # draft | active | closed
created: 2026-06-12
owner: "Claude (AI) — 技術 Lead Chris 審閱"
gap: "W61 判決指向嘅供給側軸 — upstream 候選供給 ~26–33 係真天花板,量化供給側旋鈕可推幾遠"
adr: null            # 純 per-KB/env toggle A/B + 跑數,零 code/schema/default 改動 = §5.1「加 test」例外,預期無 ADR
spec_refs:
  - docs/01-planning/CONFIG_PLATFORM_W43-W58_ROLLUP.md §4.5-§4.6  # 指標 + 結構路線判據
  - docs/01-planning/W61-image-recall-cap-widen-ab/               # cap 軸判決(供給 ~26–33 = 真天花板)
  - docs/eval-set-image-recall-ar.yaml                            # AR 9-query GT(不變)
---

# W62 — 圖片召回供給側 A/B(rerank_k / neighbour window / neighbour max_aux)

> **緣起**:W61 cap 放寬軸判決 — cap=20 確 binding,但 cap=40→60 零增長,真天花板 = upstream
> 候選供給 ~26–33 張(mega-query GT 65–73 即使 cap 無限 recall 上限 ~0.40–0.51)。
> 供給側旋鈕(`default_rerank_k` / `citation_neighbour_window` / `citation_neighbour_max_aux_images`)
> 係 W61 明文指出嘅下一槓桿。用戶 2026-06-12 拍板:先補完定義無關差距,供給側 A/B 行第一。
>
> **產品框架更新(2026-06-12 討論)**:mega-query 唔係怪問題 — Q001「How do I record a payment
> collection」係普通問題撞圖極密文件(程序 65 張截圖)。本 phase 出「供給可推幾遠」實數,
> 餵俾將來「成功定義」決策(全圖召回 vs section 覆蓋)— 本 phase 唔拍呢個板。
>
> **R6 plan-text 核實(2026-06-12,落手前 grep)**:
> - `default_rerank_k` **per-KB 可控**:`/query` 讀 `effective.default_rerank_k`
>   (`backend/api/routes/query.py:293/313/556`)→ PATCH toggle,無 W60 env 陷阱。
> - `citation_neighbour_max_aux_images` **per-KB 可控**(`effective_config.py:239` resolve 鏈)。
> - `citation_neighbour_window` **global-only pass-through**(`effective_config.py:101/255`,
>   default 3,`settings.py:209`);KbConfig **無此欄位** → env override 唔會被 per-KB 鎖死,
>   係安全控制路徑,但需重啟 backend。Env 映射 = UPPER_SNAKE 無 prefix(settings.py docstring
>   `case_sensitive=False`)→ `CITATION_NEIGHBOUR_WINDOW=8`。
> - W61 cap=60 reports 仍在 disk(`reports/image_recall_ar_cap60_r1.yaml` / `_r2.yaml`)→
>   **直接複用做 baseline 臂**(同 KB 同 GT 同 cap=60 同 env 條件),慳 2 runs。
> - 供給機制(`settings.py:203-210`):neighbour 補圖 = cited chunk ±`window` chunk_index 內、
>   每 citation ≤`max_aux` 張、受 section prefix depth 箝制;chunker per-chunk cap=8(ADR-0041)
>   → window=3 覆蓋 ±3 chunks ≈ 上限 ~56 張,max_aux=18 可 binding;window 係 reach 半徑。

## 1. 範圍(Scope)

全程 **cap=60**(unbind cap,令供給變化可量度 — W61 證 cap=60 不 binding),AR 9-query GT 不變,
KB = `drive-images-1`,同 W61 env(`SYNTHESIZER_REQUEST_TIMEOUT_S=180` + `HYBRID_USE_SEMANTIC_RANKER=false`)。

| 臂 | 變數 | 控制路徑 | runs |
|---|---|---|---|
| **A baseline** | cap=60 + 現供給(rerank_k 原值 / window 3 / max_aux 18)| **複用 W61 cap60_r1/r2** | 0(已有 2)|
| **B rerank 軸** | `default_rerank_k` 原值→**10** | per-KB PATCH + GET readback | 2 |
| **C window 軸** | rerank 復原 + `CITATION_NEIGHBOUR_WINDOW=8` | env + 重啟(雙重 gate 見 §3 AC2)| 2 |
| **D combo 供給全開** | window=8 + rerank=10 + `citation_neighbour_max_aux_images`=**40** | env 持續 + per-KB PATCH | 2 |

判軸:**returned_count**(供給係咪由 26–33 推高)為主,recall 為次,**precision 必須監察**
(供給放寬 reach 更遠,撈非 GT 圖嘅風險係本軸獨有 — W61 cap 軸冇呢個風險)。

## 2. 交付物(Deliverables)

| # | 交付 | 檔案 / 位置 | Gate |
|---|---|---|---|
| **F1** | pre-flight + 重啟 backend(已知良好 env)+ `GET /kb/drive-images-1` 記錄**全份原值** + PATCH cap=60 readback | progress.md 記原值 | readback cap=60 + 原值記錄齊 |
| **F2** | B 臂:PATCH `default_rerank_k`=10 readback + 跑 ×2 | `reports/image_recall_ar_supply_rerank10_r{1,2}.yaml` | readback + 9/9 ×2 |
| **F3** | C 臂:rerank 復原 + env window=8 重啟(AC2 雙重 gate)+ 跑 ×2;D 臂:PATCH rerank=10 + max_aux=40 + 跑 ×2 | `reports/image_recall_ar_supply_win8_r{1,2}.yaml` / `..._combo_r{1,2}.yaml` | gate + 9/9 ×4 |
| **F4** | **完全復原**:PATCH 寫回 F1 記錄嘅原值(cap=20 / rerank 原值 / max_aux=18)+ readback + 重啟移除 window env | progress.md | readback 逐欄位 = 原值 |
| **F5** | A/B 分析(returned/recall/precision 三軸 × 4 臂)+ 判決 + rollup §4.5/§4.6 doc-sync + DEFERRED 檢視 | progress.md + rollup | 判決寫低 |

## 3. Acceptance Criteria

- **AC1**(F1):cap=60 readback PASS + drive-images-1 全份 per-KB config 原值記錄在 progress.md
  (F4 復原依據;W61 教訓 PATCH = full replacement)。
- **AC2**(F3 window 臂雙重 gate):env 路徑無 KB-API readback → ① offline 驗證
  `backend\.venv\Scripts\python.exe` 一句 `get_settings().citation_neighbour_window` 喺
  `CITATION_NEIGHBOUR_WINDOW=8` 環境下回 8(證 env 名→field 映射);② backend 喺同一 shell 同 env
  下啟動。兩步齊先算 gate PASS(W60 假 sanity gate 教訓:「重現 baseline」唔係 gate)。
- **AC3**(F5 判決主軸):cap-bound 5 條嘅 **returned_count** 在 B/C/D 臂 vs A 臂(26–33)有冇實質
  推高;邊個旋鈕(rerank / window / max_aux)係主貢獻。「零推高」都係有效判決(= 供給側旋鈕
  亦唔係瓶頸 → 指向 §4.6 結構層或重定義成功)。
- **AC4**(F5):recall gain 與 **precision 代價**同錄(per-query + mean band);對照 3 條
  (Q002/Q004/Q006)必須持平(供給放寬唔應該倒灌非 GT 圖落已完美 query);Q005 繼續唔可以
  單 run 判(stochastic,2 runs band)。
- **AC5**(F4):復原 readback 逐欄位 = F1 原值;**零 code/schema/default 改動** → 無 ADR
  (§5.1「加 test」例外)。

## 4. 風險

- **R1 🟡 precision 崩**:供給 reach 擴大撈非 GT 圖。緩解:AC4 強制三軸同錄;precision 大跌
  本身係「呢個旋鈕唔可以亂開」嘅有價值判決,唔係失敗。
- **R2 🟡 mega-query synth 更慢**:供給多 → citations/images 更重。緩解:timeout 180s(同 W61);
  若仍 timeout,記低該臂該 query 為 capacity signal,唔重試硬湊。
- **R3 🟢 Azure AI Search transient 502**:W61 已遇,單次重試恢復(ADR-0017 R8-R9 territory)。
- **R4 🟢 重啟成本**:C 臂 1 次重啟 + F4 1 次(loaded machine 50–120s+ 慢非 hang,只輪詢 /health;
  venv dual-process 清理以 port 8000 LISTEN PID 為準;重啟前確認無另一 session 在動)。
- **R5 🟡 baseline 複用合法性**:A 臂複用 W61 cap60 runs 前提 = KB 無 re-index、GT 不變、env 同款。
  F1 確認 KB doc 數 / chunk 數無變(`GET /kb/drive-images-1`);有變 → A 臂重跑 ×2(+2 runs)。

## 5. 非目標(Non-goals)

- ❌ **成功定義拍板**(全圖召回 vs section 覆蓋)— 用戶 2026-06-12 明示補完差距後先評估。
- ❌ **§4.6 caption 結構路線** / **Gap B** — 等定義(2026-06-12 隊列決策)。
- ❌ **prose 型第二份 GT** — 卡用戶提供文件 + 標注。
- ❌ **持久化任何 default / per-KB 值改動** — 跑完全復原;persist 由用戶按實數另行決定。
- ❌ **圖片指標入 UI / faithfulness 決策 7** — 隊列後續項,唔混入本 phase。

## 6. ADR / Hard Constraint 核對(H1–H7)

- **H1**:零 code/schema/vendor/storage 改動;per-KB PATCH(跑完復原)+ process env(非 .env file)
  → 不觸 H1,預期無 ADR。
- **H4**:match signal 仍限 checksum(無 image embedding / 視覺檢索)。
- **H5**:不讀不改 .env file;process env only;mock auth `Bearer dev-token`。
- **H6**:零新 code(重用 W59 harness `backend/eval/image_recall.py` + `scripts/run_image_recall.py`)。
- **H7**:無前端改動 → 不觸發。

## 7. Changelog

| Date | Change | Reason |
|---|---|---|
| 2026-06-12 | Initial plan(active)| 用戶拍板差距執行隊列,供給側 A/B 行第一;R6 核實三旋鈕控制路徑(rerank/max_aux per-KB、window global-only env)+ W61 cap60 reports 複用做 A 臂 |
| 2026-06-12 | **R3 deviation:加 E 臂**(rerank=10 + max_aux=40 + window=**3 default**,×2)| D 臂突破(0.890/0.904)conflate 咗 window(global-only,今日無法 per-KB persist)同 per-KB 兩旋鈕嘅貢獻;E 臂直接回答「淨 per-KB 旋鈕可否保住突破」= persist 決策嘅關鍵實數;零 code、免重啟(F4 已除 window env)、跑完照 F4 再復原 |
| 2026-06-12 | **R3 deviation:加 F 臂**(max_aux=40 單開,rerank=5 + window=3,×2)| E 臂 ≈ D 臂(0.889)證 window 多餘,但仍 conflate rerank=10 必要性;F 臂完成 rerank × max_aux 2×2 矩陣 → preset 最簡配方(rerank=10 有 synth 延遲代價,若 F ≈ E 就唔需要)|
| 2026-06-12 | **Phase closed**(F1–F5 + E/F 臂全 done)| 判決:**`citation_neighbour_max_aux_images=18` 係供給 binding 項**(18→40 單旋鈕 = 突破:mean 0.574→0.889–0.904,GT37 全召回 1.00,mega 0.62–0.74,precision 零代價 0.976–0.988);**rerank_k=10 = section 覆蓋穩定性**(Q005 6/6 vs 擲毫,= 差距 ② 起點);**window 多餘**(E≈D);mega 新天花板 returned ~48(下一層箝制未驗);W61「cap≈40 已足」推翻 → preset cap ~50。KB 完全復原 + 零 code 改動 → 無 ADR。persist / preset 待用戶拍板 |
