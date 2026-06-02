---
phase: W43-per-kb-tunable-retrieval-config
name: "Per-KB Tunable Retrieval / Citation Config + On-Platform Test Loop (MVP — runtime-only)"
sprint_week: W43
start_date: 2026-06-01
end_date: 2026-06-12          # planned MVP window, may slip with §7 changelog
status: active               # draft | active | closed — 0.5 gate PASS 2026-06-01 (ADR-0040 Accepted + scope signed); F3 GATED on F2.6
component_scope: KbConfig (C02 KB Manager schema + storage) + C04 Retrieval Engine (parent_doc wire) + C06/C07 Generation (citation_expansion + neighbour-image wire) + C08 API Gateway (query route refactor + NEW config-test endpoint) + frontend KB Settings tab
adr_refs:
  - ADR-0040 (NEW DRAFT Proposed) — Per-KB config-scope resolution model (global default → per-KB override → per-query override); F0 起草,F1 之前需 user confirm H1 boundary + Accept + stakeholder scope (0.2)
  - ADR-0028 — KbConfig +4 multimodal fields (additive-field + migration-default back-compat precedent;本 phase reuse)
  - ADR-0035 / ADR-0037 — 兩者皆曾把「per-KB config」列為被 defer 嘅 alternative → 本 phase 正式 formalize 為 first-class config-scope model
  - architecture.md §3.1 (RAG core retrieval — parent_doc) + §3.7 (query orchestration — citation_expansion)
  - architecture.md §5.5 (KB Detail tabs — Settings tab home per ADR-0025)
related_carry_overs:
  - 證偽實驗 2026-06-01 (AR KB test-kb-20260531-v1) — Fork A 確認 / Fork B 未獲證實 / 圖洪水 ingestion-bound / 試跑 variance ~20%
  - memory project_per_kb_tunable_config_vision — 用戶 foundational vision + 證偽結果
  - memory project_chat_demo_rag_quality_followups — 全域 expansion 設定 content-coupled 根因
  - memory project_v4_retrieve_only_vs_query_pipeline — V4 retrieve-only ≠ full pipeline(本 phase F2 test-harness 要擴 V4 至 full pipeline)
  - BUG-031 (commit 508f979, 2026-06-01) — chat image flood + citation marker run-together 顯示層止血(前端 INLINE_IMAGE_CAP=8 + pill grouping);本 phase F1.6 `max_images_per_answer` 為其後端 per-KB 可配置版,須對齊(plan §2 F1.6)
---

# W43 — Per-KB Tunable Retrieval / Citation Config + On-Platform Test Loop

> **Plan version**:1.1(initial draft + 2026-06-01 review amendments — eval-blindness keystone / G2 對稱 / BUG-031 對齊 / F2.6 harness-trust gate / KB id drift fix)
> **Owner**:Chris(Tech Lead)
> **Approved by**:_(stakeholder name when status flips draft → active — 見 0.2 scope gate)_

## §1 目標 + 範疇

**單一主要目標**:把目前**全域**(`get_settings()`)嘅 retrieval / citation / image 擴張旋鈕,降到 **per-KB 作用域**(擴充既有 `KbConfig`),建立「**per-KB 配置 → 平台試跑 → 驗證 → 持久化到該 KB**」嘅閉環,令**不同內容格式嘅文件可以各用度身訂做配置而互不干擾**。本 phase 為 **MVP — runtime-only**:**唔掂 chunker / ingestion**(圖洪水深層修 defer 至 W44+ ADR-0041)。

**Why this is critical(per 證偽實驗 2026-06-01)**:
- 全域單一配置同**內容格式耦合**:為 DCE 文件(prose + §8 五子情境)調嘅激進 expansion,換到 AR 圖密步驟手冊(`test-kb-20260531-v1`)即 citation 數洪水(11)+ 圖洪水(31)。
- 證偽實驗實證:**Fork A(per-document/per-KB 配置)成立** —— AR 文件兩條 query 都係保守 config 較佳,而 DCE-調嘅激進 config 反而令 AR 兩條都變差。同一全域配置服侍唔到兩類文件。
- 即「不同文件需不同配置」唔係臆測,係實證 → 配置作用域必須由全域降到 per-KB。

**Sprint origin**:W42 closeout 後 rolling JIT(§9 W19+);trigger = 2026-06-01 AR 文件 smoke 揭全域配置 content-coupling + 用戶 foundational vision(per-KB user-tunable config)。

**⚠️ H1 BOUNDARY**:把配置解析由全域改成「per-query > per-KB > 全域 default」優先序鏈,觸及 `architecture.md §3.1 / §3.7` 嘅 config 解析方式 → **H1-adjacent**(§5 詳評)。ADR-0035 / ADR-0037 兩度將 per-KB config 列為被 reject 嘅 alternative;本 phase 正式 formalize → **需 ADR-0040 + stakeholder scope 確認(0.2)**。**F1 code 之前 STOP+ask**。

**Non-goals(本 phase 範疇外,defer W44+)**:
- **chunker / ingestion 改動**(圖洪水深層修 = `max_images_per_chunk` / 細分 / per-image metadata)→ H1 chunker change + re-ingest,屬 W44+ NEW ADR-0041。本 phase 對圖洪水只交付**鈍刀上限** `max_images_per_answer`(runtime cap,非根治)。
- **Fork B query-intent gate**(列舉 vs 具體)→ 證偽實驗顯示 AR 文件唔需要;defer 至遇上「缺 summary chunk」文件先觸發。
- **per-document scope**(配置由 per-KB 落到 per-doc)→ MVP 先 per-KB;mixed-format KB 場景 defer。
- **config version history / profile 自動建議 / 批量 sweep** → 操作性增強,defer。
- **per-query 旋鈕完整 expose**(MVP 只 reuse 既有 `top_k_*`;其餘 per-query override 留 seam)。

---

## §2 範疇 + 逐 F-phase

### F0 — 規劃 + ADR-0040 起草 + stakeholder scope gate(本 doc)
- 寫 `plan.md`(本文件)+ ADR-0040 DRAFT(Proposed)+ §5 H1 assessment + §4 R6 Day 0
- **0.2 stakeholder scope 確認** —— 呢個係 architecture 擴張(非 bugfix),需 owner 簽 scope
- **F1 GATE**:STOP+ask user confirm H1 boundary + ADR-0040 Accept + scope sign-off

### F1 — 配置模型 + 解析(後端核心;GATED on F0 gate)
1. `api/schemas/kb.py` `KbConfig` 加 retrieval/citation runtime 旋鈕欄位(全部 `Optional`,`None` = inherit 全域 default):`enable_parent_doc_retrieval` / `parent_doc_section_depth_offset` / `parent_doc_top_k` / `parent_doc_max_tokens_per_parent` / `enable_citation_post_hoc_expansion` / `citation_expansion_max_aux` / `citation_expansion_window` / `citation_expansion_section_path_prefix_depth` / `enable_citation_neighbour_images` / `citation_neighbour_max_aux_images` / `citation_neighbour_section_path_prefix_depth` / **`max_images_per_answer`(NEW,鈍刀上限)**
2. NEW `EffectiveConfig` resolver:`per-query override > per-KB KbConfig(非 None 欄位)> 全域 Settings default`。喺 request 入口砌一個 effective-config 物件,串落 pipeline(取代散落各處嘅 `settings.*` 直讀)
3. `api/routes/query.py` `/query` 路徑改用 resolved config(parent_doc L188 + neighbour-images L258 wire point)
4. `api/routes/query.py` `/chat` SSE stream 路徑同樣改(stream_settings L340 / parent_doc L345 / neighbour L367)
5. `generation/synthesizer.py` `expand_citations`(L181 sync / L296 stream)收 resolved config 而非 raw `settings`(citation_expansion 喺 synthesizer wire,非 query.py — per R6 catch 2)
6. `max_images_per_answer` 上限 apply 點(citation build 後、return 前;raw + dedup 後計）。**⚠️ 必須同 BUG-031(commit `508f979`)對齊** —— BUG-031 已喺**前端** hardcode `INLINE_IMAGE_CAP=8`(後端回全部、frontend 只 render 8 + badge 真實總數 + "View all in Image Library" 接 KB images tab)。本欄位係**後端 per-KB 可配置版**,兩者喺**不同層**(前端顯示 cap vs 後端 payload cap)。落地決定:**後端 `max_images_per_answer`(per-KB,default `None`=不限,由前端顯示 cap 兜)為主**;前端 hardcode 8 改為「`max_images_per_answer` 有值時以後端為準,`None` 時 fallback 前端預設」—— 避免兩個 cap 打架。BUG-031 嘅 **pill-grouping 係正交渲染修正,不動**
7. storage 持久化新欄位(Postgres `KbConfig` backend + in-memory)+ **既有 KB migration-default**(per ADR-0028 precedent — `None` 欄位 = 沿用全域 default,零 breaking change)
8. tests(H6):resolver 優先序 / `/query` + `/chat` + synthesizer honor per-KB config / back-compat(無 config 嘅 KB = 今日行為 bit-identical)

### F2 — 平台 full-pipeline 試跑 harness(loop 心臟)
1. NEW config-test 端點(或擴 V4 §5.5.4 retrieval-test tab):用 **draft config**(未儲存)跑**全 pipeline**(retrieval → synth → citation → image)— per memory,V4 現只 retrieve-only,要擴
2. multi-run 支援:同 query × N(default 3-5)→ 聚合 citation / figure(raw+dedup)count + **variance band**(per 證偽發現④ — 單次試跑有 ~20% figure 波動,單次定生死唔安全)
3. metrics 輸出:answer / citation count / figure count(raw+dedup)/ latency / variance / 每 citation 之 section+圖數
4. (可選)draft config vs 已存 config A/B 對照 —— 即係把 2026-06-01 手動 A/B 內建化
5. tests
6. **F2.6 — harness 信號可信 mini-gate(F3 GATE;per §4 catch 7)**:喺起 F3 UI 之前,**先用 harness 實跑 aggressive vs conservative**(AR-KB),驗證 harness 出嘅信號真係可信 —— 判準:**(a) presentation counters(圖/citation/marker)清楚分得開兩個 config;(b) 純 RAGAs 分唔太開(親手印證盲點);(c) multi-run variance band 唔會大到蓋過 (a) 嘅差異(否則信號被 noise 淹冇)**。理由:F3 係喺 harness 信號之上起 UI,若信號本身唔可信,個自助 loop 會用「假綠燈」放過壞配置 → 必須先驗證量度,後 build UI

**▶ F3 GATED on F2.6 PASS** — F2.6 唔過(信號分唔開好壞 config / variance 蓋過差異)→ STOP,re-diagnose harness 而唔好住 build UI

### F3 — UI(前端;受 H7 約束;**GATED on F2.6**)
1. **mockup 確認**:KB Settings「檢索與呈現」配置 tab + 試跑面板 —— **若 design-mockups 未有對應 spec → STOP+ask per §5.7 H7**(加 primitive / 寫 vanilla / 改 mockup)
2. KB Settings 配置面:分組旋鈕(檢索 / 引用 / 圖片)+「進階」收合 + ingestion 階段欄位掛「需重新索引」badge
3. 試跑面板:query 輸入 + run(multi-run)+ metrics + variance band 顯示
4.「儲存到此 KB」persist
5. frontend tests

### F4 — 驗證 + 收尾
1. Pre-flight per §10.3 step 5b(Langfuse /health 200 + Postgres SELECT 1)
2. cross-doc eval no-regression(**雙軸,per §4 catch 7**):無配置 KB 之 RAGAs(faithfulness/recall)**AND** presentation counters(圖/citation/marker per answer)vs baseline within tolerance(類 W42 / W30 eval set,**但 eval set 必須加入窄 how-to query** —— 否則 30-query enumeration-focused set 結構上捉唔到 flood,重蹈 RAGAs 盲點)
3. **G2 decisive proof**:AR-KB set 保守 + DCE-KB set 激進,各跑一次 → AR 保守(≤3 cit **且 how-to 答案仍正確完整,faithfulness/correctness 不退**)+ DCE 完整性**同時成立而冇改全域**(證偽實驗推導出嚟嘅成功判準;**AR 側與 DCE 側判準對稱** —— 兩邊都要質素 + presentation 雙軸)
4. governance:邊個角色可改 config(admin / KB-owner)+ audit(reuse ADR-0027 audit_log)
5. cross-doc sync(plan/checklist/progress + session-start §10 W43 row)+ ADR-0040 final status + W44+ candidate(chunker 圖洪水深層修 ADR-0041)
6. commit + push

---

## §3 Acceptance Criteria(Phase Gate)

| Gate | Criterion | Target | Measure | Block closeout? |
|---|---|---|---|---|
| **G1** | `KbConfig` 擴 runtime 旋鈕 + `EffectiveConfig` resolver 優先序(per-query > per-KB > 全域)unit-tested | 全 PASS | `pytest` resolver suite | Yes |
| **G2** ⭐ | **per-KB 配置生效且互不干擾** | AR-KB 保守(≤3 cit **且 how-to 答案仍正確完整 —— faithfulness/correctness 不退**)+ DCE-KB 激進(完整)**同時**成立,**冇改全域**。〔註:AR 側與 DCE 側判準對稱 —— 兩邊都要「質素 + presentation」雙軸,唔可以淨數 citation 而忽略答案質素〕 | F4.3 live 2-KB 對照跑 | Yes |
| **G3** | full-pipeline 試跑 harness 行全程 + multi-run variance **+ 信號可信(F2.6 mini-gate)** | N=5 跑回 cit/fig/variance band；**且 aggressive vs conservative 跑出嘅 counters 分得開、RAGAs 分唔開(印證盲點)、variance 唔蓋過差異** —— F3 GATED on 此 | F2 端點實跑 + F2.6 | Yes |
| **G4** | UI 配置面 + 試跑面板 100% mockup-faithful(H7)或 gap surfaced + resolved | 逐項對齊 | §5.7 H7 self-verify | Yes |
| **G5** | cross-doc eval no-regression(**雙軸**)| RAGAs faithfulness/recall within tolerance vs baseline **AND** presentation counters(圖/citation/marker per answer)無 regression vs baseline；eval set **必須含窄 how-to query**(per §4 catch 7 — 純 RAGAs 對 flood 係盲嘅)| F4.2 eval run | Yes |
| **G6** | pytest + ruff + mypy clean;H6 coverage on touched modules | green | CI | Yes |
| **G7** | **production-preserve** | 無 explicit config 嘅 KB 行為 = 今日 bit-identical(`None` = inherit 全域) | back-compat test | Yes |

**Outcome decision matrix**:
- (a) G1–G7 全 PASS → **STRONG PASS**:per-KB tunable config loop 上線,AR/DCE 並存,圖洪水以 `max_images_per_answer` 鈍刀緩解 → W44+ chunker 深層修(ADR-0041)交付「啱嗰幾張圖」
- (b) G2 PASS 但 G5 eval regress → **PASS WITH EVAL CAVEAT**:resolver 正確但 default 值需重校;記錄並 W44 follow-up
- (c) G1 OR G2 FAIL → **re-diagnose**(resolver / wire 機制未如預期)

---

## §4 R6 Day 0 Recursive Verification(per CLAUDE.md §10 R6)

- **catch (1)** — `KbConfig` 喺 `backend/api/schemas/kb.py:9`(非 listing.py);已有 ADR-0028 +4 multimodal 欄位擴充先例 + architecture.md §709 documents it + migration-default back-compat 做法 → F1.1 additive-field 路徑成立,零 breaking change
- **catch (2)** — `citation_expansion`(`expand_citations`)喺 **`synthesizer.py:181`(sync)/ :296(stream)** wire,**唔係** query.py;query.py 只 wire parent_doc(L188)+ neighbour-images(L258)。∴ resolver 必須同時餵到 query.py + synthesizer → F1.2 effective-config 串落 pipeline 係正確 insertion(唔可以淨改 query.py)
- **catch (3)** — V4 retrieval-test tab(ADR-0021)係 **retrieve-only**,唔行 synthesizer / citation_expansion / neighbour-images(per memory project_v4_retrieve_only_vs_query_pipeline)→ F2 試跑 harness 要**擴成 full pipeline**,唔可以直接 reuse V4 surface 當 full-pipeline preview
- **catch (4)** — 全域旋鈕實際欄位名(`enable_parent_doc_retrieval` / `citation_expansion_max_aux` / `citation_expansion_section_path_prefix_depth` / `citation_neighbour_max_aux_images` / `citation_neighbour_section_path_prefix_depth` 等)已 confirmed 喺 `storage/settings.py` → F1.1 per-KB 欄位命名鏡像之,避免 drift
- **catch (5)** — 圖洪水 = **chunk-level**(chunk-0008 自帶 27 圖,證偽實驗兩個 config 都 ~23 圖)→ **本 phase runtime config 解唔到圖洪水根本**,只能鈍刀 cap;深層修經 ingestion(W44+ ADR-0041)。plan §1 Non-goals 必須明寫,避免 G 過度承諾
- **catch (6)** — 證偽實驗顯示 Fork B(query-intent)對 AR **未獲證實必要** → 本 plan 唔 build query-intent gate(避免 over-engineer per Karpathy §1.2);留 seam,缺-summary 文件出現先 trigger
- **catch (7)** ⭐ — **RAGAs 對「presentation 失敗」係盲嘅(keystone finding,2026-06-01 chat 討論)**:memory `project_chat_demo_rag_quality_followups` #1 紀錄,`drive_user_manuals` 30-query RAGAs eval 喺**激進配置(parent_doc on)**下 = recall 1.0 / faithfulness 0.989 / **zero regression → PASS**,但**同一套配置就係會爆 flood**。即 RAGAs 量嘅係**答案文字**質素(faithfulness / correctness / recall),量唔到**圖數 / citation 數 / marker 密度**呢啲 presentation 維度 —— 而本 phase 要解嘅問題全在 presentation 軸。∴ **可信質素信號 = RAGAs(文字軸)+ presentation counters(圖/citation/marker 軸),兩條正交,各自捉到對方睇唔到嘅失敗。** 含義:(i) F2 harness 必須兩軸都出(F2.3 已含 count,呢度補原則);(ii) **G5 no-regression 唔可以淨靠 RAGAs,要包 presentation-regression**;(iii) F4.2/G5 eval set **必須包含窄 how-to query**(30-query set 原本 enumeration-focused,結構上捉唔到 how-to flood,會重蹈盲點)

---

## §5 H1 Boundary 評估 + 範疇歸屬

**H1 determination:H1-adjacent,需 ADR-0040 + stakeholder scope**

| H1 trigger 條件 | W43 是否觸發? |
|---|---|
| 加/改/刪 §3 RAG core component | ⚠️ **部分** — 改 §3.1 / §3.7 config **解析方式**(全域 → per-KB 優先序);但**行為** default-preserve(`None` = inherit),production 不變 |
| 改 vendor / service | ❌ NO — Azure / Cohere / OpenAI 不變,無 new dependency(H2 safe) |
| 改 storage layout | ⚠️ **輕微** — `KbConfig` 加欄位(additive,非 index schema change;ADR-0028 同類先例已判 additive-OK) |
| 改 multi-KB architecture | ❌ NO — reaffirm per-KB namespacing,唔改 kb_id 規則 |
| 改 8-view layout philosophy | ❌ NO — KB Settings tab 內擴,non-redesign(F3 受 H7 約束) |
| 加 Tier 2 feature | ❌ NO(⚠️ R6:config「studio」易膨脹向 Tier 2 → MVP scope 守緊) |

**結論**:config 作用域由全域降到 per-KB + 優先序鏈 = **H1-adjacent**。ADR-0035 / ADR-0037 兩度 reject per-KB config 作 one-off alternative;本 phase 正式 formalize 為 config-scope model → 需 **ADR-0040** documenting 決定 + stakeholder scope(架構方向擴張,非 bugfix)。

**Required behavior(per §5.1 H1)**:
1. ✅ F0 起草 ADR-0040(Proposed)+ H1 assessment(本節)
2. ⏳ **F1 code 之前 STOP+ask** — chat 講明 change / why / proposed + 等 user confirm「approved + ADR-0040 Accept + scope 簽」
3. ⏳ confirm 後 ADR-0040 Proposed → Accepted + 開始 F1

**H1–H7 verify**:
- **H1**:H1-adjacent — ADR-0040 route(本節)
- **H2**:✅ 無 vendor swap / 無 new dependency
- **H3**:N/A
- **H4**:⚠️ config-studio 膨脹風險 → MVP Non-goals 守 Tier 1 邊界
- **H5**:config 非 PII/secret;governance(F4.4)管 who-can-edit
- **H6**:✅ F1.8 unit tests(C04 retrieval + C06 generation + query route critical modules)
- **H7**:⚠️ F3 UI → mockup fidelity gated(F3.1 STOP+ask if mockup 缺)

---

## §6 改動清單(F-phase checkbox — 詳細 tick 以 checklist.md 為準)

### F0 啟動(本 doc)
- [x] 0.1 `docs/01-planning/W43-per-kb-tunable-retrieval-config/plan.md`(本文件)
- [x] 0.3 `docs/adr/0040-per-kb-tunable-retrieval-config-scope.md` DRAFT(Proposed)
- [x] 0.4 `checklist.md` + `progress.md` Day 0
- [x] 0.2 **stakeholder scope 確認**(architecture 擴張 → Chris 簽 = MVP runtime-only)
- [x] **0.5 STOP+ask user confirm H1 boundary + ADR-0040 Accept + scope(F1 GATE)** ✅ PASS 2026-06-01

### F1 配置模型 + 解析 ✅(0.5 gate PASS)
- [x] F1.1 `KbConfig` 加 12 runtime 旋鈕 Optional 欄位
- [x] F1.2 `EffectiveConfig` resolver(per-query > per-KB > 全域;`generation/effective_config.py`)
- [x] F1.3 `/query` 路徑改用 resolved config(+ CRAG re-synth 一致 — 見 §7 v1.2)
- [x] F1.4 `/chat`(`/query/stream`)路徑改用 resolved config
- [x] F1.5 `synthesizer.py` `expand_citations` 收 resolved config(Protocol `ExpansionConfig`)
- [x] F1.6 `max_images_per_answer` cap apply(`cap_images_per_answer`;+ 同 BUG-031 `508f979` 前端 `INLINE_IMAGE_CAP=8` 對齊:後端 per-KB 為主、前端 fallback)
- [x] F1.7 storage 持久化 + 既有 KB migration-default(Postgres JSONB + in-memory 自動帶新欄位)
- [x] F1.8 tests(resolver / 三 wire point honor / back-compat)+ ruff + mypy

### F2 平台試跑 harness ✅
- [x] F2.1 full-pipeline config-test 端點(`POST /kb/{kb_id}/config-test`;`execute_query_pipeline` 抽取共用)
- [x] F2.2 multi-run + variance band 聚合
- [x] F2.3 metrics 輸出(雙軸 + 每 citation breakdown)
- [x] F2.4 draft vs saved A/B(`compare_to_saved`)
- [x] F2.5 tests(4 case)
- [x] **F2.6 harness 信號可信 mini-gate(F3 GATE)PASS 2026-06-02** — dogfood AR KB:(a) citation 11→1 / figure 36→6 分得開 ✅ (b) RAGAs 盲(memory #1 證據)✅ (c) band=0 不蓋過 ✅

### F3 UI(H7;**F2.6 PASS → UNLOCKED**)
- [ ] F3.1 mockup 確認 / STOP+ask if gap
- [ ] F3.2 KB Settings 配置面(分組 + 進階收合 + 需重索引 badge)
- [ ] F3.3 試跑面板(query + multi-run + metrics + variance)
- [ ] F3.4 儲存到此 KB
- [ ] F3.5 frontend tests

### F4 驗證 + 收尾
- [ ] F4.1 Pre-flight(§10.3 5b)
- [ ] F4.2 cross-doc eval no-regression
- [ ] F4.3 **G2 decisive proof**(AR 保守 + DCE 激進並存)
- [ ] F4.4 governance(who-can-edit + audit)
- [ ] F4.5 cross-doc sync + ADR-0040 final + W44+ candidate(chunker ADR-0041)
- [ ] F4.6 commit + push

---

## §7 Plan Changelog

| Date | Change | Trigger | Approver |
|---|---|---|---|
| 2026-06-01 | Plan v1.0 draft ship — F0 kickoff;MVP runtime-only scope(chunker / Fork B / per-doc / version history defer W44+);ADR-0040 起草 Proposed | 2026-06-01 AR 文件 smoke 揭全域配置 content-coupling + 證偽實驗(Fork A 確認 / 圖洪水 ingestion-bound)+ 用戶 foundational vision「per-KB user-tunable config + on-platform test-loop」 | _(pending Chris scope sign-off — 0.2)_ |
| 2026-06-01 | Plan v1.1 — pre-Accept review amendments(3 點,draft 階段非 deviation):**(1)** §4 加 catch (7) eval-blindness keystone(RAGAs 對 presentation 失敗係盲嘅;可信信號 = RAGAs 文字軸 + presentation counters 軸)+ G5/F4.2 改雙軸 + eval set 須含 how-to query;**(2)** G2/F4.3 補答案質素判準令 AR 側與 DCE 側對稱(唔淨數 citation);**(3)** F1.6 + checklist + frontmatter 加 BUG-031(`508f979`)對齊(`max_images_per_answer` = 其後端 per-KB 版);**(4)** §2 加 **F2.6 harness 信號可信 mini-gate**(F3 GATED on it — counters 分得開 / RAGAs 印證盲點 / variance 唔蓋過差異)+ G3 + checklist 同步;**(5)** 4 處 KB id drift `test-kb-20260531-1` → `test-kb-20260531-v1` fix | 2026-06-01 chat review(本 session 用「RAGAs PASS 咗 flooding config」實證 + BUG-031 已 ship 揭重疊 + 「先驗證量度後 build UI」原則 + R6 KB-id precision)| _(F0 gate input,未改 status)_ |
| 2026-06-01 | **0.5 gate PASS — status draft → active**;ADR-0040 Proposed → Accepted + README row + scope = MVP runtime-only(Chris「三項都 confirm,開 F1」)。F1 全做完(8 item)| Chris 三項 confirm(H1 boundary + ADR Accept + stakeholder scope)| Chris |
| 2026-06-02 | **F1 implementation — 1 處 scope refinement(非 scope change,implementation-detail deviation per R3)**:F1.3 wire 除咗 plan §2 列明嘅 `query.py /query`(parent_doc L188 / neighbour L258)+ `/query/stream` + `synthesizer.expand_citations` 之外,**同時 thread `effective_config` 落 `CragLoop.refine`**(`generation/crag.py` parent_doc 段 + re-synth)。理由:CRAG re-synth 屬 `/query` happy path 一部分,若留全域配置而其餘行 per-KB,AR 保守 G2 會被 CRAG re-synth 用全域激進配置反噬 → 必須一致。預設 `effective_config=None` 時 byte-identical 舊行為(legacy caller / 全部現有 CRAG test 用 `AsyncMock` 不受影響)。同步:`expand_citations` `settings` 參數由具體 `Settings` 改 structural Protocol `ExpansionConfig`(令 `Settings` + `EffectiveConfig` 都 satisfy,mypy-clean)| F1 implementation Karpathy §1.3 surgical-consistency 考量 | Chris(post-hoc,implementation detail)|

---

**Lifecycle reminder**:呢份 plan **draft** — F1 code GATED on 0.5 STOP+ask(H1 confirm + ADR-0040 Accept + scope 簽)。status flips active 後 locked,重大 deviation 入 §7 changelog。
