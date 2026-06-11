# W61 — progress(cap 放寬軸 A/B)

> Daily progress + decisions + commits + 結尾 retro。對應 plan.md / checklist.md。

## Day 1（2026-06-11）— kickoff + grounding

### 開場 grounding（落手前核實,防 W60 假設陷阱）
- Session start + pre-flight 全綠:Docker daemon up / ekp-postgres healthy + `SELECT 1` / Langfuse
  `/api/public/health` 200（container flag unhealthy = timing artifact,以 endpoint 為準）/ backend
  `/health` 200。**azurite 起初 down**（port 10000 無 LISTEN）→ native Plan B 起返（PID 23256）。
- 用戶選 **cap 放寬軸 A/B**（prose 第二份 GT 延後）。
- `GET /kb/drive-images-1` 確認 per-KB config:`max_images_per_answer=20` + DD-4 三旋鈕
  `enable_parent_doc_retrieval=false / citation_expansion_max_aux=10 /
  citation_expansion_section_path_prefix_depth=1`（W60 已改回,**非** null）。另留意
  `citation_neighbour_max_aux_images=18`（per-citation aux 上限,非 total binding cap）。
- **cap 鏈核實**（防 W60 env-override 踩坑）:`/query` route query.py:492
  `cap_images_per_answer(citations, effective.max_images_per_answer)` 讀 **per-KB** config（ADR-0040
  `_resolve` per-KB 贏）→ 正確 toggle = `PATCH /kb/{id}/settings`,**非** process env。
  `cap_images_per_answer`（citation_enrichment.py:111）= 簡單 cumulative budget truncation（closer-to-top
  citation 的 images 先保留,budget 用完後面 empty）→ 放寬 cap 直接抬高天花板。
- `PATCH /kb/{id}/settings` 核實 = **full KbConfig replacement**（kb.py:218,omitted fields reset）→ 必須
  GET→只改單一 field→PATCH 整個 object back。cap 在 query time apply → 即時生效,**不需 reindex/重啟**。
- GT 預期數核實（`docs/eval-set-image-recall-ar.yaml`）:Q001/Q036=67 / Q043=73 / Q003/Q038=37（= 5 條
  cap-bound,焦點）;Q002=18 / Q004=12 / Q006=8（≤cap,對照,recall 必持平）;Q005=32（W59 歸 section-miss
  stochastic,returned 卡 9 ≪ cap,放寬無反應）。

### 關鍵設計決策
- **三臂 20/40/60**:A=20（baseline,W59/W60 已 4× corroborate ~0.572）/ B=40 ×2 / C=60 ×2 = 共 5 runs。
- **量 returned_count 判 cap-binding**:W59「cap 是瓶頸」本身是**假設**。放寬 cap 後若 returned 升向新 cap →
  cap 確 binding;若持平 ~20 → upstream 候選供給才是真 binding,**反證 W59**（亦是有效進展）。
- **真 sanity gate = GET readback 確認 cap 已變**（非「重現 baseline」= 假 gate,W60 教訓）。
- **跑完務必復原 cap=20**（F4 獨立 deliverable + AC5 gate）。

### Plan / checklist / progress 三件套 committed（R1 gate 滿足）
- 待 commit:`docs(planning): W61 cap-widen image-recall A/B kickoff`

### F1 — backend 重啟 + baseline（cap=20）✅ AC1 通過
- Running backend 查得單一 venv dual-process（PID 46912 venv parent + 32376 system child listening 8000），
  **無 multi-session collision**。env 未知（synth timeout / semantic ranker）→ 為保證 5-run A/B 已知良好條件,
  殺兩 PID（port 8000 釋放）+ 起 fresh backend（`SYNTHESIZER_REQUEST_TIMEOUT_S=180` /
  `HYBRID_USE_SEMANTIC_RANKER=false`）→ ~60s healthy。
- Pipeline probe（Q002 單條）：6 citations + 20 images + checksum,無 402 → 端到端健康。
- **baseline cap=20**（`reports/image_recall_ar_cap20.yaml`,bg `bkp51g1r4`）：

  | Query | recall | precision | hit/exp | returned | 類別 |
  |---|---|---|---|---|---|
  | Q001 | 0.31 | 1.00 | 20/65 | 20 | cap-bound |
  | Q036 | 0.28 | 1.00 | 18/65 | 18 | cap-bound |
  | Q043 | 0.27 | 1.00 | 20/73 | 20 | cap-bound |
  | Q003 | 0.51 | 0.95 | 19/37 | 20 | cap-bound |
  | Q038 | 0.51 | 0.95 | 19/37 | 20 | cap-bound |
  | Q002 | 1.00 | 0.95 | 18/18 | 19 | 對照 |
  | Q004 | 1.00 | 1.00 | 12/12 | 12 | 對照 |
  | Q006 | 1.00 | 1.00 | 8/8 | 8 | 對照 |
  | Q005 | 0.28 | 1.00 | 9/32 | 9 | section-miss |

  **mean recall 0.574 / precision 0.983 / 9/9** → ✅ AC1（≈ W59/W60 0.572,mega 無 timeout）。
- **關鍵 observation**：5 條 cap-bound 中 4 條 returned 卡 20、Q036 卡 18,且 precision 0.95–1.00 = 返回圖幾乎
  全 GT → 放寬 cap 理想前提（surface 更多 GT,precision 不應崩),**除非 upstream 供給耗盡**（Q036 returned
  18 < cap 已暗示 plateau 風險,= AC3 cap-binding 判決核心）。對照 Q002 returned 19 略超 GT 18 → cap=20 連對照
  都接近 binding（非 GT 圖佔 budget),放寬 cap 對對照臂的影響亦待觀察。
- GT expected_count 校正：Q001/Q036=65（非 67,先前肉眼多算）/ Q043=73 / Q003/Q038=37。

### F2 — cap=40
- `PATCH /kb/drive-images-1/settings`（full replacement,只改 `max_images_per_answer` 20→40）→
  **GET readback = 40 + DD-4 仍 `false/10/1` → GATE PASS**（真 sanity gate,config readback 證 toggle 生效）。
- run 1 launched（bg `btpd5nf51`,`reports/image_recall_ar_cap40_r1.yaml`）。

### F2 — cap=40 ×2 完成
| Query | cap=20 | cap=40 r1 | cap=40 r2 | returned 20→(r1/r2) |
|---|---|---|---|---|
| Q001 | 0.31 | 0.40 | 0.40 | 20→26 / 26 |
| Q036 | 0.28 | 0.40 | 0.54 | 18→26 / 35 |
| Q043 | 0.27 | 0.36 | 0.36 | 20→26 / 26 |
| Q038 | 0.51 | 0.68 | 0.68 | 20→26 / 26 |
| Q003 | 0.51 | 0.51 | 0.51 | 20→20 / 20（死卡）|
| Q005 | 0.28 | 0.00(fluke) | 0.38 | 9→0 / 12 |
| 對照×3 | 1.00 | 1.00 | 1.00 | 持平 |

- mean recall 0.574 → 0.594(r1）/ 0.651(r2）;mean precision r1 0.873（Q005=0 artifact）/ r2 **0.984**（≈ baseline）。
- **cap=20 確 binding**（returned 20→26–35）;**plateau ~26–35 從未到 40** → upstream 候選供給才係真天花板。
- **Q003 phrasing 死卡 20**（兩 run 都唔升,即使 cap=40）vs 同 GT Q038 卡 26 = 穩定 per-phrasing 差異。
- **precision 唔崩**（額外圖 GT-correct,r2 0.984）;Q005=0 證實 fluke（r2 回 0.38）。

### F3 — cap=60
- `PATCH max_images_per_answer 40→60` → **GET readback = 60 + DD-4 仍 `false/10/1` → GATE PASS**。
- run 1（bg `bzz5c96ek`）**全 9 條 502 `pipeline.retrieval_failed: APIConnectionError`**（Azure AI Search
  連接 transient blip,與 cap 無關 = cap 在 retrieval 之後 apply）→ run 作廢。診斷：backend `/health` 200 +
  單條 probe 回 200 → transient 已恢復 + config 仍 cap=60 → **重跑 run 1**（bg `bwldkgnwq`,覆蓋壞 report）。
  屬 R3/ADR-0017 R8-R9 infra transient territory,單次重試。
- **決定性測試**：若 cap=60 returned 仍 plateau ~26–35（不升向 60）→ 確證 cap 在 ~26 以上唔再 binding,
  真瓶頸 = upstream 供給（AC3 判決核心）。

- **cap=60 run 1**（重跑成功,`reports/image_recall_ar_cap60_r1.yaml`）：

  | Query | cap=20 | cap=40(r1/r2) | cap=60 r1 | returned cap=60 |
  |---|---|---|---|---|
  | Q001 | 0.31 | 0.40/0.40 | 0.40 | 26（= cap=40）|
  | Q036 | 0.28 | 0.40/0.54 | 0.48 | 31 |
  | Q043 | 0.27 | 0.36/0.36 | 0.36 | 26（= cap=40）|
  | Q003 | 0.51 | 0.51/0.51 | 0.68 | 26 |
  | Q038 | 0.51 | 0.68/0.68 | 0.68 | 26（= cap=40）|
  | Q005 | 0.28 | 0/0.38 | 1.00 | 32（stochastic 0→9→12→32）|
  | 對照×3 | 1.00 | 1.00 | 1.00 | 持平 |

  mean recall **0.732**（Q005=1.00 stochastic 抬高）/ precision **0.986**。
- **🔑 AC3 決定性**：cap=60 cap-bound returned 全 **26–31,無一近 60**,與 cap=40 同範圍 → **40→60 零增長** →
  真天花板 = upstream 供給 ~26–31,**非 cap**。W59「cap 是瓶頸」**只對一半**（cap=20 是 binding,放寬到供給
  上限後真瓶頸 = retrieval recall + neighbour attachment 廣度,= §4.6 結構路線）。mega-query（GT 65–73）即使
  cap 無限 recall 上限 ~0.40–0.48;Q003/Q038（GT 37）~0.68–0.70。
- run 2 launched（bg `bicvqllol`）確認 plateau 穩定。

### F4 — 復原 cap=20 ✅
- `PATCH max_images_per_answer 60→20` → **GET readback = 20 + DD-4 仍 `false/10/1` + neighbour cap 18 +
  return_images True → RESTORE PASS**。drive-images-1 完全復原 W60 原態。

### F5 — A/B 分析 + 判決

**完整 returned_count 軌跡（cap-bound 5 條,跨 5 runs）**：

| Query | GT | cap=20 | cap=40 r1/r2 | cap=60 r1/r2 | 真天花板（upstream 供給）|
|---|---|---|---|---|---|
| Q001 | 65 | 20 | 26 / 26 | 26 / 26 | **~26**（穩定）|
| Q036 | 65 | 18 | 26 / 35 | 31 / 33 | **~26–35** |
| Q043 | 73 | 20 | 26 / 26 | 26 / 33 | **~26–33** |
| Q003 | 37 | 20 | 20 / 20 | 26 / 26 | **~20–26** |
| Q038 | 37 | 20 | 26 / 26 | 26 / 26 | **~26** |

**recall 軌跡（cap-bound）**：

| Query | cap=20 | cap=40 band | cap=60 band | gain（20→sweet spot）|
|---|---|---|---|---|
| Q001 | 0.31 | 0.40 | 0.40 | +0.09 |
| Q036 | 0.28 | 0.40–0.54 | 0.48–0.51 | +0.12–0.26 |
| Q043 | 0.27 | 0.36 | 0.36–0.45 | +0.09–0.18 |
| Q003 | 0.51 | 0.51 | 0.68 | 0 → +0.17（variance）|
| Q038 | 0.51 | 0.68 | 0.68 | +0.17 |

**判決**：

1. **AC3 — cap=20 確為 binding,但真天花板 = upstream 候選供給(~26–33),非 cap**。returned 由 cap=20 的
   18–20 升至 cap=40 的 20–35,但 **cap=40→60 零增長**（全 plateau 26–33,無一接近 40 或 60,2 runs 穩定）。
   → 放寬 cap 到供給上限以上 = 浪費 headroom。
2. **AC4 — recall partial gain,precision 不崩**。cap-bound recall cap=20→40 升 +0.09~+0.17（Q003/Q038
   GT37 升至 0.68;mega-query GT65–73 升至 0.40–0.51）；**precision 維持 0.95–1.00**（額外圖 GT-correct,
   mean precision 偶跌全係 Q005=0 stochastic artifact）。**對照 3 條（Q002/Q004/Q006）完美持平 1.00** = 乾淨
   baseline,零 variance noise。
3. **W59「cap 是瓶頸」只對一半**：cap=20 是 binding（放寬有 partial gain),但對 **mega-query**
   （Q001/Q036/Q043,GT 65–73）upstream 供給 ~26–33 ≪ GT → **即使 cap 無限,recall 上限 ~0.40–0.51**。
   **cap 放寬單獨無法填 mega-query 缺口**;真瓶頸 = retrieval recall + neighbour-image attachment 廣度（= §4.6
   結構路線 + `citation_neighbour_max_aux_images`/`rerank_top_k` 等供給側旋鈕,本 phase 範圍外）。
4. **建議**：AR 類圖密文件,per-doc/per-KB **cap≈40 已捕捉全部 upstream 供給**（40 vs 60 無分別,40 已足）；
   進一步提升 mega-query recall 需走供給側（§4.6 / neighbour breadth）,非單純抬 cap。**是否把 cap 設成
   drive-images-1 持久值由用戶按實數決定**（plan non-goal:本 phase 只實證槓桿效力,已復原 20）。

**方法論收穫**：
- **returned_count 軸係判 cap-binding 的關鍵**——單看 recall 會把「cap binding」與「upstream 供給不足」混淆;
  量 returned 才睇到 plateau。
- **per-KB PATCH toggle + GET readback 真 sanity gate 有效**（W60 env-override 坑無重蹈;readback 證 toggle 生效）。
- **Q005 高度 stochastic**（recall 跨 5 runs:0.28→0→0.38→1.00→0,returned 0↔32）——與 cap 完全無關（section
  覆蓋 stochastic),**不可單 run 判**;2 runs 取 band 必要。
- **Azure AI Search transient 502**（cap=60 首 run 全 9 條 `APIConnectionError`）= infra blip,非 config 問題,
  單次重試即恢復（R3/ADR-0017 R8-R9 territory）。

### Retro
- **達成**：AC1（baseline 重現 0.574）/ AC2（每臂 GET readback gate PASS）/ AC3（cap-binding 決定性判決）/
  AC4（recall gain + precision 不崩 + 對照持平）/ AC5（復原 cap=20 + 零 code 改動,無 ADR）全達。
- **核心結論**：cap 放寬 20→40 對 cap-bound query 有 modest 真 gain（+0.09~+0.17,precision 保持),但 **40→60
  無效**,真天花板係 upstream 供給 ~26–33。**對 mega-query（GT 65–73）cap 放寬單獨不足**,需 §4.6 供給側路線。
- **零 code/schema/default 改動**（純 per-KB toggle + 跑完復原）→ 無 ADR（§5.1 加 test 例外）。
- **🚧 §4.5 未盡之二（prose 型第二份 GT）仍欠**——硬依賴用戶提供 prose 文件 + 親自標注。
- reports/*.yaml gitignored（eval-methodology §6.1）,不 commit。
