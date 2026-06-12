# W62 — progress(供給側 A/B)

> Daily progress + decisions + commits + 結尾 retro。對應 plan.md / checklist.md。

## Day 1(2026-06-12)— kickoff

### 背景 + 決策鏈
- 用戶 2026-06-12 拍板:「先補完定義無關差距,之後先評估成功定義」;AskUserQuestion 揀
  **W62 供給側 A/B 行第一**(隊列:① 供給側 → ② Q005 section-miss 診斷 → ③④⑤ faithfulness
  警告閘 / 指標入 UI / 圖密 preset;⛔ 等定義 = §4.6 caption / Gap B / 跨 KB agent)。
- 產品框架更新(本日討論):mega-query(GT 65–73)係**普通問題撞圖密文件**(Q001 = "How do I
  record a payment collection",程序本身 65 張截圖),唔係「攞晒全部」枚舉題 → 「成功定義」
  (全圖召回 vs section 覆蓋)係之後嘅產品決策,本 phase 只出供給實數。

### R6 plan-text 核實(落手前 grep,詳 plan.md 頭注)
- `default_rerank_k` per-KB 可控(query.py:293/313/556 讀 effective)✅
- `citation_neighbour_max_aux_images` per-KB 可控(effective_config.py:239)✅
- `citation_neighbour_window` **global-only**(effective_config.py:101/255;KbConfig 無此欄位
  → env 唔會被 per-KB 鎖死;映射 `CITATION_NEIGHBOUR_WINDOW`,settings.py case_sensitive=False)✅
- W61 cap60 reports 在 disk(`reports/image_recall_ar_cap60_r{1,2}.yaml`)→ A 臂複用 ✅

### 三件套 committed(R1 gate)
- `docs(planning): W62 supply-side image-recall A/B kickoff`(`976596d`)

### F1 — pre-flight + baseline 確立 ✅ AC1 通過
- Pre-flight 全綠:Langfuse 200(Docker flag unhealthy = artifact)/ Postgres `1 row` /
  backend 200(全 components ok)/ azurite TCP 10000 通。
- 殺 W61 遺留 backend dual-process(PID 32132 venv parent + 44344 system child,
  start=06-11 17:52 = 非另一 session)→ port 8000 釋放 → fresh backend
  (`SYNTHESIZER_REQUEST_TIMEOUT_S=180` + `HYBRID_USE_SEMANTIC_RANKER=false`,無 window env)
  → healthy。
- **`GET /kb/drive-images-1` 原值記錄(F4 復原依據)**:
  `default_rerank_k=5` / `citation_neighbour_max_aux_images=18` / `max_images_per_answer=20` /
  `default_top_k=50` / DD-4 三旋鈕 `false/10/1` / `enable_chapter_overview_pin=true` /
  `citation_neighbour_section_path_prefix_depth=1` / `answer_detail=detailed` /
  `chunk_strategy=auto` / `chunker_max_images_per_chunk=null`。
- **R5 複用合法性 ✅**:`last_indexed_at=2026-06-08`(W61 runs 之前)+ 6 docs / 369 chunks /
  827 screenshots → KB 無 re-index → A 臂直接複用 W61 `image_recall_ar_cap60_r{1,2}.yaml`。
- PATCH cap 20→60(full replacement)→ **readback cap=60 + 其餘欄位原封 → GATE PASS**。

### F2 — B 臂(rerank_k=10)
- PATCH `default_rerank_k` 5→10 → **readback rerank_k=10 + cap=60 → GATE PASS**。
- Q002 probe:200 OK,6 citations + **60 images(撞 cap)** — 早期信號:W61 baseline(rerank=5,
  cap=60)Q002 returned 19;rerank=10 令對照 query 供給飆到 60 → **precision 代價風險(R1)現形**,
  待全 run 量化。
- run 1 launched(bg `bm9pk5zfl`,`reports/image_recall_ar_supply_rerank10_r1.yaml`)。

### F2 — B 臂 run 1 結果(mean recall 0.733 / precision 0.986 / 9/9)
| Query | recall | precision | returned | vs A 臂(W61 cap60)|
|---|---|---|---|---|
| Q001 | 0.40 | 1.00 | 26 | 持平(26/26)|
| Q036 | 0.48 | 1.00 | 31 | 持平(31/33)|
| Q043 | 0.34 | 1.00 | 25 | 持平偏微降(26/33)|
| Q003 | 0.70 | 0.96 | 27 | 持平(26/26)|
| Q038 | 0.68 | 0.96 | 26 | 持平(26/26)|
| Q002/Q004/Q006 | 1.00 | 0.95–1.00 | 19/12/8 | 對照持平 ✅ |
| Q005 | 1.00 | 1.00 | 32 | stochastic(band 內)|

- **早期判讀:rerank_k 5→10 對供給幾乎零影響** — cap-bound returned 25–31 同 A 臂 plateau
  26–33 同範圍;probe 時 Q002=60 圖未喺正式 run 重現(synthesizer citing variance)。
  解讀候選:synthesizer 俾 10 個候選都係 cite ~5–6 條 → images 跟 citation 嚟,supply 唔升。
- run 2 launched(bg `boqgjy12h`)。

### F2 — B 臂 run 2 完成(mean 0.720 / precision 0.985 / 9/9)→ **B 臂判決:供給零推高**
- cap-bound returned r2:Q001=26 / Q036=26 / Q043=26 / Q003=25 / Q038=26 — 同 A 臂 plateau
  26–33 完全同範圍,兩 runs 穩定。**rerank_k 5→10 = 候選翻倍,供給零反應**。
- 機制解讀:synthesizer 俾 10 個候選仍只 cite ~5–6 條;images 跟 citation,所以唔升。
- **副發現(餵差距 ②)**:Q005 喺 B 臂兩 runs 都 1.00(returned 32),A 臂 cap60 係 0↔1.00 隨機
  擺 — rerank_k=10 **可能**令 borderline query 嘅 section 覆蓋更穩(候選多 → 相關 section 更大
  機會入 cite 池)。2 runs 對 Q005 呢隻 stochastic query 唔夠定論,留 Q005 診斷 phase 驗證。

### F3 — C 臂(window=8)gates
- PATCH `default_rerank_k` 10→5 復原 → readback rerank_k=5 + cap=60 → PASS。
- **AC2 gate ①**:offline `get_settings().citation_neighbour_window` 喺 `CITATION_NEIGHBOUR_WINDOW=8`
  env 下回 **8** → env 名→field 映射證實。
- **AC2 gate ②**:殺 F2 backend(PID 12124/30412)→ 同 shell 帶 window=8 env 重啟 → healthy。
- C 臂 run 1 launched(bg `b5gib3p4t`,`reports/image_recall_ar_supply_win8_r1.yaml`)。

### F3 — C 臂 run 1 結果(mean 0.736 / precision 0.985 / 9/9)
- **首個供給突破信號:Q036 returned 39**(超 A 臂 plateau 26–35 上界),recall 0.48→**0.60**,
  precision 1.00(新增圖全 GT-correct)。
- 但同程序唔同問法嘅 Q001 仍卡 26(recall 0.40)— per-phrasing 差異再現(同 W61 Q003 vs Q038
  pattern)。其餘 cap-bound 持平(Q043=26 / Q003=23 / Q038=26)。
- 對照 3 條持平(19/12/8,precision 0.95–1.00)→ window 擴大冇倒灌非 GT 圖落對照。
- Q005 = 1.00/32(連續第 3 個 run 1.00:B r1 / B r2 / C r1;W61 同 cap60 條件下曾 1.00→0 擺 —
  繼續觀察,未敢叫穩)。
- C 臂 run 2 launched(bg `bkrfvwu4l`)。

### F3 — C 臂 run 2 結果(7/9;Q005/Q006 撞 Azure transient 502 中段自恢復,R3 territory 不重跑)
- cap-bound:Q001=26(0.40)/ Q036=**25**(0.38,r1 嘅 39 冇重現)/ Q043=**33**(0.45,r2 突破)/
  Q003=23(0.59)/ Q038=26(0.68)。對照 Q002/Q004 持平。
- **C 臂判決:window=8 嘅供給提升係間歇性** — 每 run 隨機有一條 mega-query 越過 plateau
  (r1 Q036=39 / r2 Q043=33),但唔穩定、唔同條;多數 query 仍卡 23–26。precision 全程 0.95–1.00
  (擴 reach 撈到嘅新圖仍 GT-correct)。
- 7/9 run mean(0.644)不可同 9/9 比;F5 分析用 per-query 值。

### F3 — D 臂(combo:window=8 + rerank=10 + max_aux=40)
- health 200(transient 已恢復)→ PATCH rerank_k=10 + neighbour_max_aux=40 →
  **readback 10/40/cap=60 → GATE PASS**(window env 持續)。
- D 臂 run 1 launched(bg `b3qxjd0pg`,`reports/image_recall_ar_supply_combo_r1.yaml`)。

### F3 — D 臂 run 1 結果:**突破(mean 0.890 / precision 0.988 / 9/9)**
| Query | A 臂(cap60)| D 臂 r1 | returned 變化 |
|---|---|---|---|
| Q001 | 0.40 | **0.74** | 26→**48** |
| Q036 | 0.48–0.51 | 0.62 | 31→40 |
| Q043 | 0.36–0.45 | **0.66** | 26→**48** |
| Q003 | 0.68 | **1.00**(37/37 全召回)| 26→38 |
| Q038 | 0.68 | **1.00**(37/37 全召回)| 26→38 |
| Q005 | 0↔1.00 | 1.00 | 32 |
| 對照×3 | 1.00 | 1.00 | 19/12/8 持平 |

- **supply plateau 26–33 被打穿 → 38–48**;precision 0.95–1.00 **冇代價**(新增圖全 GT-correct)。
- **機制判讀:三旋鈕互補,單開無效** — B 臂(rerank 單開)零反應 + C 臂(window 單開,max_aux=18
  收割上限箝住)間歇 + D 臂(window 俾 reach × max_aux=40 俾收割容量 × rerank=10 俾收割起點)爆發。
  supply ≈ citations × min(reach 內圖數, max_aux)。
- run 2 launched(bg `bummi6f40`)驗穩定性。

### F3 — D 臂 run 2:**突破確認穩定(mean 0.904 / precision 0.976 / 9/9)**
- Q001 0.74/48(重現)/ Q036 **0.74/48**(仲高過 r1)/ Q043 0.66/48(重現)/ Q003+Q038 1.00(重現)。
- D 臂 band = **0.890–0.904**(vs A 臂 0.732 / cap20 baseline 0.574)。
- 暇疵:Q006 對照 r2 多 1 張非 GT 圖(returned 9,precision 0.89)— 單張幅度,唔構成 AC4 fail。
- **觀察:三條 mega-query returned 全部釘喺 48** — 一致得可疑,似有下一層箝制(cap=60 未 binding;
  假設候選:citations × chunker per-chunk 圖數?未驗證,留將來)。
- Q005 喺 W62 全部 scored runs(B×2 / C r1 / D×2)= **1.00**,vs W61 同 cap60 條件 0↔1.00 擺 —
  歸因未明(三款唔同 config 都穩),唔可以斷言邊個旋鈕,留 Q005 診斷 phase。

### F4 — 完全復原 ✅ RESTORE PASS
- PATCH 寫回原值 → readback 逐欄位對 F1 記錄:cap=20 / rerank_k=5 / max_aux=18 / top_k=50 /
  parent_doc=False / exp 10/1 / neighbour_depth=1 / pin=True / detail=detailed / strategy=auto /
  chunker_cap=null / return_images=True — **全對**。
- 殺 window-env backend(PID 49020/18132)→ 無 window env 重啟 → healthy。

### R3 deviation — 加 E 臂(per-KB-only combo)
- **動機**:D 臂 conflate window(global-only,**今日冇得 per-KB persist**;加 per-KB 欄位 = schema
  改動 = H1 ADR route;改 global default 影響所有 KB 亦要 ADR)同 rerank+max_aux(per-KB 即日可
  persist)。E 臂(rerank=10 + max_aux=40 + window=3 default)直接回答「淨 per-KB 旋鈕保唔保得住
  突破」= persist 決策關鍵。Plan changelog 已記(R3)。
- PATCH cap=60 + rerank=10 + max_aux=40 → readback PASS;run 1 launched(bg `blkyqyedv`,
  `reports/image_recall_ar_supply_perkb_r1.yaml`)。

### E 臂 run 1:**mean 0.889 / precision 0.986 — 同 D 臂基本相同 → window=8 喺 combo 多餘**
- Q001 0.74/48 / Q036 0.62/40 / Q043 0.64/47 / Q003+Q038 1.00 — 逐條對齊 D 臂 band。
- **判讀:突破完全嚟自 per-KB 兩旋鈕(rerank=10 + max_aux=40)** → persist 唔使碰 global
  window,零 code 零 ADR。
- 仍 conflate:rerank=10 必要性(max_aux=40 單開未測;B 臂只證 rerank 單開 + max_aux=18 無效)。
  → 加 F 臂(max_aux=40 單開,rerank=5)完成 rerank × max_aux 2×2 矩陣 = preset 最簡配方判據
  (rerank=10 有 synth context 變大延遲代價)。R3 changelog 補記。
- E run 2 launched(bg `bsere3jlo`)。

### E 臂 run 2:0.889 / 0.988 — 逐條同 run 1 一樣,band 鎖死 0.889 → per-KB pair 完全重現 D 臂

### F 臂(max_aux=40 單開,rerank=5)run 1 — **雙重判決**
- **cap-bound 五條同 E 臂逐條一樣**(Q001 0.74/48 / Q036 0.62/40 / Q043 0.66/48 / Q003+Q038 1.00/38)
  → **供給突破 = max_aux=40 一個旋鈕已足**,rerank=10 對供給零貢獻。
- **Q005 = 0.00/returned 0** — rerank 退回 5 即翻發 section-miss 擺動。跨 W61+W62 數據史:
  **rerank=10 全部 6 runs(B×2/D×2/E×2)Q005=1.00;rerank=5 runs(W61 cap60 ×2 + C r1 + F r1)
  = 1.00/0/1.00/0 五五擺** → 假設成形:**rerank_k=10 買嘅係 section 覆蓋穩定性**(Q005 係
  雙段 query「set up + generate」,候選多 → 第二段 section 更大機會入 cite 池)— 直接係差距 ②
  (Q005 section-miss 診斷)嘅答案候選。mean 0.779/0.877 被 Q005=0 拖低,cap-bound 軸不受影響。
- F run 2 launched(bg `bbittyacq`)。

### F 臂 run 2:cap-bound 逐條重現(Q036 47 / 其餘同 r1);**Q005 連續第二次 0.00** → rerank=5 擺動證實

### F4(最終)— 完全復原 ✅ RESTORE PASS(第二次,E/F 臂之後)
- PATCH cap=20 + max_aux=18(rerank 已 5)→ readback 逐欄位對 F1 原值**全對**
  (cap=20 / rerank_k=5 / max_aux=18 / top_k=50 / parent_doc=False / exp 10/1 / neighbour_depth=1 /
  pin=True / detail=detailed / return_images=True);backend 已係無 window env 條件。

### F5 — 總判決(6 臂 × 11 runs + A 臂複用 2 runs)

**完整矩陣(cap-bound 5 條,recall(returned)band)**:

| Query | GT | A cap60 | B rerank10 | C win8 | D 全開 | E rerank10+aux40 | F aux40 單開 |
|---|---|---|---|---|---|---|---|
| Q001 | 65 | 0.40(26)| 0.40(26)| 0.40(26)| **0.74(48)** | **0.74(48)** | **0.74(48)** |
| Q036 | 65 | 0.48–0.51(31–33)| 0.40–0.48(26–31)| 0.38–0.60(25–39)| 0.62–0.74(40–48)| 0.62(40)| 0.62–0.72(40–47)|
| Q043 | 73 | 0.36–0.45(26–33)| 0.34–0.36(25–26)| 0.36–0.45(26–33)| **0.66(48)** | 0.64(47)| **0.66(48)** |
| Q003 | 37 | 0.68(26)| 0.65–0.70(25–27)| 0.59(23)| **1.00(38)** | **1.00(38–39)** | **1.00(38)** |
| Q038 | 37 | 0.68(26)| 0.68(26)| 0.68(26)| **1.00(38)** | **1.00(38)** | **1.00(38)** |

mean 軌跡:cap20 **0.574** → cap60 **0.732** → 突破臂 **0.889–0.904**(D/E;F 0.779–0.791 被 Q005=0
拖,cap-bound 軸 F≈E);precision 全程 **0.976–0.988**。

**判決(AC3/AC4)**:

1. **「upstream 供給 ~26–33」(W61)唔係 retrieval 上限,係 `citation_neighbour_max_aux_images=18`
   收割上限嘅偽裝**。max_aux 18→40 單一旋鈕(F 臂)已完整重現突破:returned 38–48、GT37 兩條
   **全召回 1.00**、mega 0.62–0.74。B(rerank 單開)零反應、C(window 單開)間歇 — 因為收割上限
   箝住,reach/起點再多都收唔返。supply ≈ citations × **min(reach 內圖數, max_aux)**,binding 項
   一直係 max_aux。
2. **precision 零代價**:六臂全程 0.95–1.00(唯一暇疵 D r2 Q006 多 1 張,0.89 單點)。對照 3 條
   全程持平 → 位置繼承喺步驟手冊好可靠,新收割 20+ 張幾乎全 GT-correct。
3. **rerank_k=10 嘅真正價值 = section 覆蓋穩定性,非供給**:Q005(雙段 query)喺 rerank=10 嘅
   **6/6 runs = 1.00**;rerank=5 嘅 5 個 scored runs = 1.00/0/1.00/0/0 擲毫。假設:候選池大 →
   第二段 section 更大機會入 cite 池。**= 差距 ②(Q005 section-miss 診斷)嘅最強起點**(仍屬
   假設層:單一 query,後續 phase 驗證)。
4. **window=8 多餘**(E≈D 逐條)→ persist 唔使碰 global window,**零 code 零 ADR**。
5. **mega-query 新天花板 returned ~47–48**(三條全釘住,cap=60 未 binding)→ 有下一層箝制
   (假設候選:cited+neighbour 收割範圍內 GT 圖總量 / per-citation budget 互動;未驗證)。
   mega recall 上限由 0.40–0.51 推到 **0.62–0.74**。
6. **W61「cap≈40 已足」建議被推翻**(條件變咗):新供給去到 48 → 圖密 preset cap 應 ~50–60。

**建議 preset(圖密步驟手冊類 KB;per-KB 即日可設,未 persist,由用戶拍板)**:
`citation_neighbour_max_aux_images=40`(供給核心)+ `default_rerank_k=10`(section 覆蓋穩定)
+ `max_images_per_answer≈50`(蓋住 48 留 margin)。

**Caveats**:單一文件類型(AR 圖密手冊)9 query;synth latency 未量(rerank=10 context 較大;
實驗 timeout=180s,production default 120s per ADR-0053 — persist 前要 120s 條件 sanity run);
prose 型 GT 仍欠(供給結論對 prose 文件未驗)。

### Retro
- **達成**:AC1–AC5 全達;R3 兩次 deviation(E/F 臂)令 2×2 矩陣閉合,得出「max_aux 係供給
  binding 項 / rerank 係穩定性項 / window 多餘」嘅可執行拆解 — 比原 3 臂設計更有用。
- **方法論**:returned_count 軸再次係決勝(W61 同款);「一致得可疑嘅數」(48/48/48)= 下一層
  箝制信號;Q005 類 stochastic query 嘅 config 歸因要跨 phase 數據史先睇到 pattern。
- **零 code/schema/default 改動 + KB 完全復原** → 無 ADR(§5.1 加 test 例外)。
- reports/*.yaml gitignored(eval-methodology §6.1),結果落本檔。
- **下一步(隊列)**:② Q005 section-miss 診斷(起點 = rerank=10 穩定性假設)→ ③④⑤;
  persist / preset 決策待用戶。
