---
phase: W43-per-kb-tunable-retrieval-config
plan_ref: ./plan.md
checklist_ref: ./checklist.md
status: active      # draft | active | closed — flipped active 2026-06-01 (0.5 gate PASS)
---

# Phase W43 — Progress

> Daily progress + 結尾 retro。每 commit 對應一個 Day-N entry(R2;`docs(planning):` housekeeping commits 例外）。
> **本 phase 仍 draft** — F1+ GATED on F0 0.5 STOP+ask(H1 confirm + ADR-0040 Accept + stakeholder scope)。Day 0 之後嘅 Day-N 留待 gate PASS 後填。

---

## Day 0 — 2026-06-01: F0 Kickoff + draft + review amendments

**Origin**:W42 closeout 後 rolling JIT(§9 W19+)。Trigger = 2026-06-01 AR 文件(`test-kb-20260531-v1`)smoke 揭全域 retrieval 配置同**內容格式耦合** + 用戶 foundational vision(per-KB user-tunable config + on-platform test-loop)。

### Done(F0 — 規劃,非 code)
- `plan.md` v1.0 draft 起草(MVP runtime-only scope:chunker / Fork B / per-doc / version history defer W44+)
- `docs/adr/0040-per-kb-tunable-retrieval-config-scope.md` DRAFT(Proposed)+ ADR README index row
- §5 H1 assessment(config 解析由全域 → per-KB 優先序鏈 = **H1-adjacent**,需 ADR-0040 + stakeholder scope)
- §4 R6 Day 0 recursive verification 6 catch(後加第 7 catch — 見下）
- `checklist.md` + `progress.md`(本文件)Day 0 — **完成 0.4**

### Review amendments(2026-06-01 chat,plan v1.0 → v1.1,draft 階段非 active deviation)
本 session review 後加嘅 5 點(全記 plan §7 changelog):
1. **eval-blindness keystone(§4 catch 7)** — `drive_user_manuals` 30-query RAGAs eval 喺激進配置下 PASS,但同一配置爆 flood → RAGAs 量文字質素、量唔到 presentation(圖/citation/marker 數)。可信信號 = RAGAs + presentation counters 雙軸。G5/F4.2 改雙軸 + eval set 須含窄 how-to query。
2. **G2/F4.3 對稱** — AR 側補「how-to 答案仍正確完整(faithfulness/correctness 不退)」,唔淨數 citation。
3. **BUG-031(`508f979`)對齊** — `max_images_per_answer` = BUG-031 前端 `INLINE_IMAGE_CAP=8` 嘅後端 per-KB 版;後端為主、前端 fallback;pill-grouping 正交不動。
4. **F2.6 harness 信號可信 mini-gate** — F3 GATED on it:先驗證量度(counters 分得開 / RAGAs 印證盲點 / variance 唔蓋過差異)後 build UI。
5. **KB id drift fix** — `test-kb-20260531-1` → `test-kb-20260531-v1`(4 處)。

### Decisions / OQ
- 決定:MVP = runtime-only;圖洪水深層修(ingestion-bound,證偽實驗證)split out W44+ ADR-0041。
- 決定:Fork B(query-intent gate)defer — 證偽實驗顯示 AR 未證明需要(避免 over-engineer per Karpathy §1.2)。
- OQ:本 phase **無 OQ 變更**(decision-form.md 無需同步)。

### Blockers / Gates(open)
- ⛔ **0.5 F1 GATE** — F1 code 之前需 user STOP+ask confirm:H1 boundary + ADR-0040 Proposed → Accepted + stakeholder scope(0.2)簽。**未過 gate,F1+ 一律唔開工。**
- 0.2 stakeholder scope 確認 — pending(architecture 擴張需 owner 簽)。

### Commits
- `267a46c` — `docs(planning): W43 F0 draft (plan + ADR-0040) + 2026-06-01 review amendments`(plan v1.1 + ADR-0040 Proposed + README row + 5 點修訂)
- `<this commit>` — `docs(planning): W43 F0 0.4 — checklist + progress Day 0`

---

---

## Day 1 — 2026-06-01: 0.5 gate PASS + F1 配置模型 + 解析(全 8 item 完成）

**Gate**:Chris「三項都 confirm,開 F1」→ 0.5 F1 GATE **PASS**:
- ✅ H1 boundary confirm(config 解析由全域降到 per-KB 優先序鏈,default-preserve)
- ✅ ADR-0040 `Proposed → Accepted`(+ `docs/adr/README.md` row + scope = MVP runtime-only)
- ✅ stakeholder scope 簽(Chris,architecture 擴張)
- plan / checklist / progress frontmatter status `draft → active`

### Done(F1 — 全 8 item)
- **F1.1** `KbConfig`(`api/schemas/kb.py`)加 12 個 Optional runtime 旋鈕(`None` = inherit 全域;parent_doc ×4 + citation_expansion ×4 + neighbour ×3 + `max_images_per_answer`)
- **F1.2** NEW `generation/effective_config.py` — `EffectiveConfig`(frozen dataclass)+ `PerQueryOverrides`(per-query seam)+ `resolve_effective_config(settings, kb_config, per_query)`(優先序 per-query > per-KB 非 None > 全域;global-only pass-through:`parent_doc_max_chunks_per_parent` / `parent_doc_fallback_to_doc_on_shallow` / `citation_neighbour_window`)
- **F1.3** `query.py` `/query`:NEW `KbServiceDep` + `_resolve_effective_config`(graceful `KBNotFoundError` → 全域 default)+ parent_doc(L188)/ neighbour(L258)/ CRAG `refine` 全部改用 `effective.*`
- **F1.4** `query.py` `/query/stream`(= chat UI 行嘅 path):同樣 entry 砌 `effective` + parent_doc / neighbour callback / `synthesize_stream` 全用 `effective`(移除 `stream_settings = get_settings()`)
- **F1.5** `synthesizer.py` `synthesize` + `synthesize_stream` 加 `effective_config` kwarg → 餵 `expand_citations`(`None` fallback 全域);`citation_expansion.py` `settings` 參數由 `Settings` 改 structural Protocol `ExpansionConfig`(read-only `@property` → frozen `EffectiveConfig` + mutable `Settings` 都 satisfy)
- **F1.6** `citation_enrichment.py` NEW `cap_images_per_answer`(鈍刀;`None` = 不限,production-preserve;cumulative cap across citations)+ `/query` + `/query/stream` 兩路 apply;對齊 BUG-031 前端 `INLINE_IMAGE_CAP=8`
- **F1.7** 持久化 — 確認 Postgres backend 用 JSONB(`config.model_dump()` / `KbConfig(**row)`)→ 新欄位**自動序列化**、舊 row 缺 key **自動 fill None**(migration-default 自動,零 schema change);in-memory 整個 KbStatus 存 → 自動帶
- **F1.8** tests:NEW `tests/test_effective_config.py`(resolver 優先序 / back-compat bit-identical / legacy dict migration / cap 4 case)+ `tests/test_query_per_kb_config.py`(route 整合 — per-KB True/False 雙向覆蓋全域,monkeypatch 控全域)

### Decisions / OQ
- **R3 implementation refinement(非 scope change)**:F1.3 除 plan §2 列明 wire point 外,**thread `effective_config` 落 `CragLoop.refine`**(CRAG re-synth 屬 `/query` happy path,留全域配置會反噬 AR 保守 G2)→ 記 plan §7 v1.2 changelog。預設 `None` byte-identical,現有 CRAG test(`AsyncMock`)不受影響。
- OQ:本 phase **無 OQ 變更**。

### 測試 / 檢查
- targeted pytest:`test_effective_config` / `test_query_per_kb_config` / `test_observe_query_route` / `test_e1_e5_e12_smoke` / `test_crag` / `test_citation_expansion` / `test_synthesizer` / `test_citation_enrichment` → **92 passed**;query/kb/eval/api route 第二輪 → **111 passed, 10 skipped**
- ⚠️ **1 個 pre-existing env-coupled 失敗**:`test_synthesizer::test_synthesize_invokes_engine_fetch_expansion_*` 期望 `0046`,得 `0044`。根因 = 真實 `.env` 有 `CITATION_EXPANSION_SECTION_PATH_PREFIX_DEPTH=1`(demo 調校值,code 預設 0)→ prefix filter reject 測試 neighbour(log 證 `section_path_prefix_depth=1`)。`git stash` 喺 pristine main 重現 = **非 F1 引入**;我對 synthesizer 嘅改動喺 `effective_config=None` 時 byte-identical 等同舊 `get_settings()`。屬測試 env-coupling 設計問題(W43 正正係解呢類全域耦合),非本 phase 修復範圍(Karpathy §1.3)
- ruff:touched files **all passed**
- mypy --strict:我嘅新模組(`effective_config.py` / `cap_images_per_answer` / `ExpansionConfig`)**0 error**;修正 1 個自引入 error(`EffectiveConfig` 不 satisfy plain-attr Protocol → 改 read-only `@property`)。codebase 本身有 **61 pre-existing --strict errors**(openai SDK overload / `getattr` Any / bare-`dict` annotation / `event_serializer` untyped-def)散落 21 file — 全部喺我**未改嘅行**,屬 baseline,Karpathy §1.3 不掃

### Mini-checkpoint(F1 完成,F2 待開)
- F2 平台試跑 harness 為下一步;**F3 仍 GATED on F2.6**(harness 信號可信 mini-gate)

### Commits
- `6c0ec73` — `feat(api): W43 F1 per-KB tunable retrieval/citation config (ADR-0040)`(code + 3 新 test file + 2 mock 更新)
- `ef4bc3a` — `docs(planning): W43 0.5 gate PASS + F1 closeout (ADR-0040 Accepted)`(本文件 + plan + checklist + ADR-0040 Accept + README)

---

## Day 1 — addendum 2026-06-02: F1 live A/B 驗證(`test-kb-20260531-v1`)

F1 落 code 後做嘅 live 驗證(非 phase deliverable,屬 post-F1 manual confirm;記錄供 F2/F4 引用)。

### 過程
- 發現 running backend 係**系統 Python + F1 之前嘅舊 code**(`python -m api.server` 無 reload,F1 前已啟動)→ `PATCH /kb/{id}/settings` 嘅 `max_images_per_answer` 被舊 `KbConfig`(pydantic `extra=ignore`)靜靜 drop。**決定性 check = `GET /openapi.json` → `KbConfig.properties` 有冇 `max_images_per_answer`**。
- kill port-8000 python → 用 `backend\.venv\Scripts\python.exe -m api.server` 重啟(venv 冷啟動 ~51s)→ 12 個 W43 旋鈕入 schema,F1 code live。

### A/B 結果(`POST /query`,`enable_crag=false`,zero variance)
| per-KB config | citations | total images | 解讀 |
|---|---|---|---|
| 全 `None` → 全域激進 | 11 | 36 | 洪水基線 |
| `max_images_per_answer=6` | 11 | **6** | ✅ 圖洪水收斂(cap 只 trim 圖,citation 不變) |
| `enable_parent_doc_retrieval=false` | 11 | 36 | ⚪ 無變化 — 此 KB 洪水由 citation_expansion 來,非 parent_doc |
| `enable_citation_post_hoc_expansion=false` | **1** | 35 | citation 洪水收斂 11→1,但單 chunk 自帶 35 圖 = ingestion-bound |

### 結論(3 點)
1. **per-KB 配置確認生效** —— 3 個旋鈕都 honor per-KB 值並雙向覆蓋全域(同 F1.8 整合測試一致)。
2. **圖洪水 = 兩個獨立來源**:citation-數驅動(post-hoc 展開拉 10 鄰居 chunk)= runtime 控到;**單 mega-chunk 自帶 35 圖 = ingestion-bound,runtime 解唔到**(Test C 留 1 citation 仍 35 圖)→ 正是 W44+ ADR-0041,ADR-0040 R6 catch 5 命中。
3. runtime 層唯一能 cap 總圖數嘅 lever = **`max_images_per_answer`**;`enable_parent_doc_retrieval` 對此 KB 無效。
4. **背書 eval-blindness keystone**:「36 vs 6 圖」對答案文字 RAGAs 隱形 → presentation counters 係必須第二軸 → 直接支撐 F2.3 / F2.6 雙軸 harness 設計。

### 收尾
- `PATCH /kb/{id}/settings` 係**全量替換**(略去欄位 reset 為 default)→ A/B 時 GET 現有 config + 先 null 全部 12 W43 旋鈕隔離,再設一個。
- KB config 已**還原全 None**(Postgres 持久,故必須還原);`return_images_in_chat=True` 保留;backend 留喺 venv F1 code。
- memory `project_chat_demo_rag_quality_followups` Finding #8 已記。

### Commits
- `01a3ea6` — `docs(planning): W43 F1 live A/B verification addendum (per-KB config effective)`

---

## Day 2 — 2026-06-02: F2 平台 full-pipeline 試跑 harness(全 6 item + F2.6 gate PASS)

### Done(F2)
- **F2.1** 抽 `/query` sync pipeline core → module-level `execute_query_pipeline(payload, request, effective, settings)`(query.py);`query()` 變薄 wrapper。NEW `POST /kb/{kb_id}/config-test`(`api/routes/config_test.py` + `api/schemas/config_test.py`)—— **唔污染 V4 retrieve-only**(per memory 經常 confuse smoke test),draft config 經 `PerQueryOverrides` 注入 resolver(draft > saved KB > 全域);harness 行 **IDENTICAL** pipeline(F2.6 trust 前提)。`server.py` register router(`dependencies=_auth`)。
- **F2.2** multi-run(N=1-5,default 3)+ `MetricBand`(min/max/mean/**band=max-min**)聚合。
- **F2.3** 雙軸 metrics:per-run citation / figure raw+dedup / latency / answer_chars / refused + aggregate band + `CitationBreakdown`(每 citation section+圖數)。
- **F2.4** `compare_to_saved=true` → draft vs saved A/B(把 2026-06-01 手動 A/B 內建化)。
- **F2.5** `tests/test_config_test_route.py` 4 case(multi-run+band / max_images cap apply / compare / 404)。

### F2.6 — harness 信號可信 mini-gate **PASS**(F3 GATE 解鎖)
dogfood `test-kb-20260531-v1`,config-test `runs=3 compare_to_saved`(draft=保守 vs saved=全域激進):
| 信號 | SAVED 激進 | DRAFT 保守 | 判準 |
|---|---|---|---|
| citation | 11 (band 0) | 1 (band 0) | (a) ✅ |
| figure_raw | 36 (band 0) | 6 (band 0) | (a) ✅ |
| figure_dedup | 28.7 | 6 | (a) ✅ raw≠dedup 計數都 work |
- **(a)** presentation counters 清楚分得開(11→1 / 36→6)✅
- **(b)** RAGAs 盲 —— memory #1 已記同激進配置 30-query RAGAs PASS zero-regression(用既有 eval 證據,不重燒 Azure judge)✅
- **(c)** band=0 << 差距,variance 唔蓋過 ✅
→ harness 信號可信,**F3 UNLOCKED**(GATED-on-F2.6 解除)。

### Decisions / OQ
- `execute_query_pipeline` 抽取 = 內部 refactor,**非 H1**(§5.1 明列 refactor-no-interface-change 不觸發);query.py 行為 bit-identical(16 query-route + harness test PASS)。
- 新端點而非擴 V4:per memory `project_v4_retrieve_only_vs_query_pipeline` —— V4 narrow retrieve-only scope 保持,避免 smoke-test 混淆。
- F2.6 (b) 用既有 RAGAs 證據(memory #1)而非重跑 —— 結論已實證,慳 Azure judge 成本。OQ 無變更。

### 測試 / 檢查
- pytest:config-test + query route(extraction regression)→ **16 passed**;ruff 新檔 all pass;mypy --strict 新模組 + query.py **0 new error**(總 61 = F1 baseline,無新增)。
- backend kill+restart 載入 F2(venv,39s);config-test 端點入 schema 確認。

### Commits
- `08443fc` — `feat(api): W43 F2 on-platform config-test harness (ADR-0040)`(query.py extraction + config_test route/schema + server wire + 4 test)
- `<docs commit>` — `docs(planning): W43 F2 closeout + F2.6 gate PASS`(本文件 + checklist + plan）

### Mini-checkpoint
- F3(UI,受 H7)已解鎖;F4 驗證收尾待 F3 後。**F3 開工前 F3.1 必先確認 design-mockups 有冇對應 spec → 冇就 STOP+ask per §5.7 H7。**

---

**End of W43 progress(Day 2 — F2 done + F2.6 gate PASS,F3 next)**
