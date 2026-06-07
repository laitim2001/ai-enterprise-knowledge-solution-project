---
change_id: CH-007
spec_ref: ./spec.md
checklist_ref: ./checklist.md
status: closed          # in-progress | closed
---

# CH-007 — Progress

> Day-N entries + closeout。每 commit 對應 Day-N mention(R2)。

---

## Day 1 — 2026-06-07

### Context
CH-006 期間發現:KB Settings 嘅 `default_rerank_k`(+ `default_top_k`)set+save 後 **chat 完全忽略**(chat payload 只送 `{query, kb_id}`;`execute_query_pipeline` 讀 `payload.top_k_rerank` 而非 `EffectiveConfig`;`top_k_retrieval` overfetch 喺 query 路徑完全 dead)。CH-006 §2.3 已 deferred 本 CH。spec draft→approved(Chris chat「批准 — 兩個都接入」);scope = `default_rerank_k` + `default_top_k` 一併接入。

### Done
- (kickoff)spec.md status draft → **approved**(Chris)+ §2.4 scope 抉擇記錄 + §7 changelog + checklist + progress committed(R1.change 滿足)。
- **Backend I1-I7 完成**:`QueryRequest` top_k → Optional;`EffectiveConfig`/`PerQueryOverrides` 加 `default_top_k`/`default_rerank_k` + resolver 三層次序;`RetrievalEngine.retrieve` + `fused_retrieve` 加 additive `overfetch` kwarg;`query.py` 入口砌 `PerQueryOverrides`、pipeline 三處(fused/retrieve/stream)改讀 `effective.default_rerank_k` + `overfetch=effective.default_top_k`。
- **Tests T1-T6 完成**:`test_effective_config.py` +3 CH-007 resolve test + global-inherit assert;`test_query_per_kb_config.py` +4 route test(`/query` ×3 + `/query/stream` ×1,`_RecordingEngine` record top_k/overfetch);`test_retrieval.py` +1 engine overfetch test。
- **V1-V2 verified**:**113 passed / 0 fail**;ruff clean;mypy 改動檔 clean。
- **V3 Live 驗 PASS**:w56-drive-ab-1 無 top_k → retrieved_chunks=11(=KB default,舊 5);`top_k_rerank=3` → 3(override)。詳見 closeout。

### CH-006 incomplete-landing 恢復(deviation,per spec §7)
跑 query-pipeline test suite 揭 **CH-006「done」其實漏咗 4 個 route-test 檔 + 一個 schema type bug**,兩層互相遮蔽:
1. CH-006 query route 無條件傳 `synthesize(..., detail_level=)`,但 `test_query_per_kb_config` / `test_config_test_route` / `test_observe_query_route` / `test_e1_e5_e12_smoke` 4 個 mock synthesize 漏改 → 502 TypeError。
2. 修 mock 後 unmask 第二層:`ConfigTestResult.resolved_config: dict[str,int|bool|None]` 容唔落 CH-006 加入 EffectiveConfig 嘅 `answer_detail: str`(`asdict` 入 resolved_config)→ 9 個 config_test ValidationError。
- 第 1 層 TypeError(502 早於 `return ConfigTestResult`)一直遮蔽第 2 層,所以 CH-006 V1「80 passed」從未跑到呢 4 檔、兩個 bug 都漏網。
- **修**:4 檔 mock 加 `detail_level: str = "concise"`(對齊 ship 的真簽名)+ `resolved_config` type 放寬至含 `str`。CH-007 改 `execute_query_pipeline` + 為 EffectiveConfig 加欄位(亦流入 resolved_config),呢條 suite 必須綠先驗到 CH-007 → 屬 blast-radius 內最小恢復,全透明。建議用戶考慮補一條 CH-006 retro note。

### Decisions
- **Backend 單一真相源**:pipeline 改後**只**從 `effective` 讀 top_k,`payload.top_k_*` 只喺入口折入 `effective`(經 `PerQueryOverrides`)→ 徹底消除 payload/effective 雙源 ambiguity;`config_test` 經 `execute_query_pipeline` 自動正確。
- **消歧義必須改 schema**:`top_k_rerank=5` 同「未設定」今日無法區分 → 必須改 `int | None = None`。
- **`default_top_k` 接入** = engine `retrieve`/`fused_retrieve` 加 additive `overfetch` kwarg(`None`=既有行為,向後相容)。
- **Frontend 唔使改**:控件 + 持久化已存在 → 無 H7 觸發。
- **`/retrieval-test`(V4)+ eval harness** 用獨立 path → 不接入(維持明確 top_k)。

### Blockers
- 無。

### architecture.md §4.5 drift note(X5 — frozen §1-14 不動,只記)
spec §4.5 illustrative schema 仍寫 `top_k_retrieval: int = 50` / `top_k_rerank: int = 5`;實作改為 `int | None = None`。行為層向後相容(omitted/None = 今日 KB/全域預設;explicit int = override)。屬 frozen-doc content lock 範圍 → 不編輯 architecture.md,僅此記錄 drift;下次 stakeholder-approved version increment 時同步。

### Effort
- Planned:~0.5 day;Actual:~半日(single session,含恢復 CH-006 4 檔)；Variance:約持平。

---

## Closeout — 2026-06-07

### Acceptance verification(spec.md §3)
- ✅ `QueryRequest.top_k_*` → `int | None = None`(omitted/None/明確值 round-trip)
- ✅ `EffectiveConfig`/`PerQueryOverrides` 帶 `default_top_k`/`default_rerank_k`;resolve = per-query > per-KB > 全域(`hybrid_top_k_retrieval`/`rerank_top_k`)
- ✅ chat(`/query/stream`,無 top_k)→ retrieve 採 KB `default_rerank_k`;`/query` 同(route test 斷言 `{top_k:20, overfetch:80}`)
- ✅ retrieve overfetch 採 KB `default_top_k`(`overfetch=None` 零行為改變,engine test 證 80 vs 50)
- ✅ Non-regression:explicit top_k 壓過 KB default;default KB(50/5)bit-identical;`test_multi_kb_routing` 不破
- ✅ `config_test` 經 `execute_query_pipeline` 自動採 KB saved `default_rerank_k`(無回歸)
- ✅ pytest **113 passed / 0 fail**;ruff clean;mypy 改動檔 clean
- ✅ **V3 Live 驗 PASS**(2026-06-07):backend restart 載入新 code;KB `w56-drive-ab-1`(415 chunks,`default_rerank_k=11`,mode=vector,enable_crag=false,零 KB mutation)。**Test A** 無 top_k(chat 路徑)→ `retrieved_chunks=11` = KB default(舊 code 硬寫 5 → 證 per-KB 生效);**Test B** `top_k_rerank=3` → `retrieved_chunks=3`(證 explicit override 壓過);reranker=cohere-v4.0-pro。Live 環境只有 2 個 Azure index 存在(`w54-live-ab-1` / `w56-drive-ab-1`),其餘 9 個 KB metadata 的 index 已不在 `azureaisearchtesting` resource(orphaned metadata,非 CH-007 問題)。

### Lessons
- **做得好**:backend 單一真相源(pipeline 只讀 `effective`,payload 入口折入)徹底消除 top_k 雙源 ambiguity;additive `overfetch` kwarg 令 `default_top_k` 由 dead control 變生效兼零行為改變;route test 用 recording-engine 直接斷言傳入值。
- **意外**:跑 query-pipeline suite 揭 CH-006「done」漏咗 4 檔 route-test mock(`detail_level`)+ `resolved_config` type bug,兩層互相遮蔽(mock 502 早於 ConfigTestResult build)→ CH-006 V1 從未跑到呢 4 檔。CH-007 blast-radius 內最小恢復 + 透明記錄。
- **carry-over**:(1) 建議補 CH-006 retro note(test-mock + resolved_config gap);(2) 未來可考慮 `DraftRetrievalConfig` 加 top_k/rerank_k 旋鈕令 config-test 草稿層 A/B(本 CH out of scope);(3) live 環境只有 2 個 Azure index 存在(orphaned KB metadata × 9)— 若日後要對其他 KB live 驗需 re-ingest。

### Component design note status updates
- C04 Retrieval:amendment + last_updated 2026-06-07(per-KB `default_rerank_k` rerank 深度 + `default_top_k` overfetch via `retrieve(overfetch=)`)
- C02 KB Manager:amendment + last_updated 2026-06-07(`default_top_k`/`default_rerank_k` 經 EffectiveConfig 生效於 query 路徑)

### Commits
| Hash | Subject |
|---|---|
| _(待 user go)_ | docs(change): CH-007 kickoff(spec approved + checklist + progress) |
| _(待 user go)_ | feat(retrieval): CH-007 — per-KB default_top_k/default_rerank_k wiring + tests(C04+C02)|
| _(待 user go)_ | closeout |

---

**End of CH-007 progress**
