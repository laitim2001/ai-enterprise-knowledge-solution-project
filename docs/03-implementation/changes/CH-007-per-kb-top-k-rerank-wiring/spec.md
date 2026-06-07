---
change_id: CH-007
title: "Per-KB default_top_k / default_rerank_k wiring into chat/query pipeline"
status: done             # draft | proposed | approved | active | done | cancelled
created: 2026-06-07
target_completion: 2026-06-08
affects_components: [C04, C02]      # C04 Retrieval (engine + query pipeline) + C02 KB Manager (KbConfig/EffectiveConfig)
spec_refs:
  - architecture.md §3.2 §3.5 (Hybrid retrieval / rerank depth)
  - architecture.md §4.4 §4.5 (Query endpoints / QueryRequest schema)
  - ADR-0040 (per-KB tunable config resolution → EffectiveConfig)
  - backend/api/routes/query.py execute_query_pipeline
  - backend/generation/effective_config.py
  - CH-006 spec §2.3 (此 wiring gap 明確 deferred 另案)
---

# CH-007 — Per-KB default_top_k / default_rerank_k 接入 chat/query pipeline

> **Spec version**:1.0(initial)
> **Owner**:AI(實作)/ Chris(approve)
> **Approved by**:Chris(2026-06-07 — chat「批准 — 兩個都接入」)

## 1. Context (Why)

CH-006 實作期間(2026-06-07)發現:KB Detail → Settings → Retrieval 配置面板嘅 **`default_rerank_k`**(同 `default_top_k`)設定 + save 之後**對 chat 答案完全冇影響**,因為 chat 路徑根本冇將 top_k 傳落 backend,而 backend 又冇從 KB config 讀返。

**證據鏈**:

- **Frontend 送出 payload 缺 top_k**:`frontend/lib/api/query.ts` `streamQuery()` POST 落 `/query/stream` 嘅 body 只有 `{ query, kb_id }`(呼叫點 `frontend/app/(app)/chat/page.tsx` ~L386:`streamQuery({ query: trimmed, kb_id: kbId }, ...)`),冇 `top_k_retrieval` / `top_k_rerank`。
- **Backend schema 用 int 預設**:`backend/api/schemas/query.py` `QueryRequest.top_k_rerank` 預設 `5`、`top_k_retrieval` 預設 `50`。
- **Pipeline 讀 payload、唔讀 KB config**:`backend/api/routes/query.py` `execute_query_pipeline`(L165 / L183)+ `query_stream`(L380)用 `payload.top_k_rerank` 做 `engine.retrieve(top_k=...)`(= rerank 深度);**完全冇讀** 已 resolve 嘅 `EffectiveConfig` 內任何 top_k / rerank_k。
- **`EffectiveConfig` 現時唔帶 top_k**:`backend/generation/effective_config.py` 已經 per-KB resolve parent-doc / citation 等旋鈕,**但無 `default_top_k` / `default_rerank_k`**。
- **`top_k_retrieval`(overfetch)喺 query 路徑係完全 dead**:全 backend 只有 schema 定義引用,無任何 reader。Overfetch 實際由 engine 建構時 `settings.hybrid_top_k_retrieval=50` 固定(`RetrievalEngine._hybrid_overfetch`),非 per-request。所以 `default_top_k` 目前**無任何** wiring path。

**淨結果**:UI 設定 `default_rerank_k`(或 `default_top_k`)會持久化(經 PATCH `/kb/{id}/settings`,frontend state 已綁 `kb.config.default_top_k` / `default_rerank_k`),但 `/query` + `/query/stream` 完全忽略佢。用戶合理預期「set + save → chat 採用」落空 = 一個 dead control bug。

**根因 = wiring,非 retrieval/synthesis 質素**:KB config 持久化 OK、UI OK、resolver 架構(ADR-0040 `EffectiveConfig`)已在,差嘅只係 top_k/rerank_k 未 thread 入 resolver + pipeline 未讀 effective 值。

**Cross-ref**:CH-006 spec §2.3 明確將「`default_rerank_k` → chat 嘅 wiring gap」列為 out of scope、另開 CH/Bug 處理 — 即本 CH-007。

## 2. Scope (What)

### 2.1 Behavior Change

- **Before**:chat(`/query/stream`)同 `/query` 一律用 schema 預設 `top_k_rerank=5` 做 rerank 深度,**無視** KB 設定嘅 `default_rerank_k`;`default_top_k` 對 retrieval overfetch 完全冇作用(overfetch 固定全域 50)。
- **After**:當呼叫方**冇明確傳** per-query top_k(chat 路徑),pipeline 採用該 KB 嘅 `default_rerank_k`(rerank 深度)同 `default_top_k`(retrieval overfetch);當呼叫方**有明確傳**(eval / 測試 / 未來 per-query override),per-query 值優先。零行為改變嘅 KB = 用預設 50/5 嘅 KB(同今日一致)。

### 2.2 In Scope

採用 **backend-first 單一真相源** 做法(per 用戶指引 + ADR-0040 既有 resolver 模型),frontend **唔使改**(控件 + 持久化已存在):

- **C02 schema(消歧義)**:`QueryRequest.top_k_retrieval` / `top_k_rerank` 由 `int`(50 / 5)改為 `int | None = None`。
  - 理由:今日 `top_k_rerank=5` 同「未設定」無法區分(都係 5),令 KB default 永遠無法生效。`None` = 「用 KB / 全域預設」;明確 int = per-query override。此為消除 ambiguity 嘅必要改動(用戶於 task brief 已點出)。
- **C02 `PerQueryOverrides` + `EffectiveConfig`**(`effective_config.py`):各加 `default_top_k` / `default_rerank_k`。
- **C02 resolver**(`resolve_effective_config`):新增兩旋鈕 resolve,次序 = **per-query override > per-KB `KbConfig.default_*` > 全域 `Settings`**。全域 fallback:`default_top_k → settings.hybrid_top_k_retrieval`(50)、`default_rerank_k → settings.rerank_top_k`(5)。註:`KbConfig.default_top_k/default_rerank_k` 係 concrete int(非 Optional,沿用 W2 baseline),故已註冊 KB 必有值、per-KB 一定壓過全域;未註冊 KB(`kb_config=None`)跌全域 — 與既有 KbConfig 語義一致。
- **query.py wiring**:
  - `_resolve_effective_config(...)` 新增 `per_query: PerQueryOverrides | None = None` 參數,傳落 `resolve_effective_config`。
  - `query()` + `query_stream()` 由 `payload.top_k_retrieval` / `payload.top_k_rerank` 砌 `PerQueryOverrides(default_top_k=..., default_rerank_k=...)`,resolve 入 `effective`。
  - `execute_query_pipeline`(L165 / L183)+ `query_stream`(L380)三處 retrieve 改讀 **`effective.default_rerank_k`**(取代 `payload.top_k_rerank`)。改後 pipeline **只**從 `effective` 讀 top_k,`payload.top_k_*` 只在入口被折入 `effective` → 徹底消除 payload/effective 雙源 ambiguity,亦令 `config_test`(經 `execute_query_pipeline`)自動採用 KB saved `default_rerank_k`。
- **C04 engine(接入 `default_top_k` overfetch — 見 §2.4 scope 抉擇)**:`RetrievalEngine.retrieve` + `retrieval.result_fusion.fused_retrieve` 新增 additive `overfetch: int | None = None` kwarg(`None` = 沿用 `self._hybrid_overfetch`,零行為改變);pipeline 傳 `effective.default_top_k`。`fetch_k = max(top_k, overfetch if overfetch is not None else self._hybrid_overfetch)`。
- **Tests(H6 — `backend/api/routes/query.py` 屬 H6 強制覆蓋清單)**:
  - `QueryRequest` top_k 欄位 Optional round-trip(None 預設 / 明確值)。
  - `EffectiveConfig` 帶 `default_top_k` / `default_rerank_k` + resolve 次序(per-query > per-KB > 全域)。
  - `execute_query_pipeline` 用 `effective.default_rerank_k`(mock `engine.retrieve`,assert 傳入 `top_k` = KB 值)。
  - `/query` + `/query/stream` 兩路皆生效。
  - Non-regression:payload 明確 top_k 仍壓過 KB default(`test_multi_kb_routing` 既有 explicit 5 路徑不破)。
  - (若採 §2.4 推薦)engine `overfetch` kwarg:`None` = 既有行為、明確值 = 改 `fetch_k`。

### 2.3 Out of Scope(explicit)

- ❌ **Frontend 任何改動** — 控件 + 持久化已存在;純 backend wiring,無 H7 design fidelity 觸發。
- ❌ **`/retrieval-test`(RetrievalTab V4)** — 用獨立 `RetrievalTestRequest.top_k`(自帶 slider 預設 5),診斷專用 surface(per memory `project_v4_retrieve_only_vs_query_pipeline`),不接入 KB default(維持明確 top_k 行為)。
- ❌ **eval harness**(`scripts/run_ragas_eval.py`)— 自建 engine、直接 `retrieve(top_k=5)`,不經 `/query`;明確 top_k 維持。
- ❌ **`DraftRetrievalConfig`(config-test 草稿)加 top_k/rerank_k 旋鈕** — config-test 改後會採用 KB saved 值(正確);讓 config-test **草稿層** A/B 不同 rerank_k 屬未來增強,本 CH 不做。
- ❌ **改 `docs/architecture.md` §4.5 frozen schema**(content lock §1-14)— 只記 drift note,不動 frozen doc。
- ❌ **改 retrieval/rerank 演算法本身** — 純 wiring,演算法不動。

### 2.4 Scope 抉擇(需 approve 時確認)— `default_top_k` 是否一併接入

`default_rerank_k`(rerank 深度)接入 = 乾淨直接、正正係所報 bug 核心。`default_top_k`(retrieval overfetch)目前 100% dead(§1),接入需要 §2.2 嘅 engine `overfetch` kwarg(additive、小、向後相容)。

- **推薦 = 兩個都接入**:否則 `default_top_k` 會繼續係「設咗 + save 但被忽略」嘅同類 dead control bug,且改動細小(一個 kwarg + 一行 `fetch_k`)。單一真相源更完整。
- **替代 = 只接 `default_rerank_k`**:更 surgical;`default_top_k` 留另案(但 UI 控件繼續 dead,需向用戶交代)。

> **Approve 抉擇**:☑ 兩個都接(推薦,Chris 2026-06-07)/ ☐ 只接 `default_rerank_k`。

## 3. Acceptance Criteria

- [ ] `QueryRequest.top_k_retrieval` / `top_k_rerank` 改 `int | None = None`;omitted / None / 明確 int 三種輸入皆正常(schema round-trip)。
- [ ] `EffectiveConfig` + `PerQueryOverrides` 有 `default_top_k` / `default_rerank_k`;`resolve_effective_config` 次序 = per-query > per-KB > 全域(`hybrid_top_k_retrieval` / `rerank_top_k`)。
- [ ] chat(`/query/stream`,payload 無 top_k)→ retrieve 採用 KB `default_rerank_k`;`/query` 同。
- [ ] (若揀兩個都接)retrieve overfetch 採用 KB `default_top_k`(`overfetch=None` 時零行為改變)。
- [ ] **Non-regression**:payload 明確傳 top_k(eval / `test_multi_kb_routing` 既有 explicit 5)→ per-query 值壓過 KB default;`default_top_k=50` / `default_rerank_k=5` 嘅 KB 行為 bit-identical 今日。
- [ ] `config_test` 經 `execute_query_pipeline` 自動採用 KB saved `default_rerank_k`(無回歸)。
- [ ] H6 tests 全綠:`backend/.venv/Scripts/python.exe -m pytest backend/tests/test_effective_config.py backend/tests/test_query*.py backend/tests/test_multi_kb_routing.py -q`(+ 相關新 test)。
- [ ] `ruff` / `mypy --strict`(改動檔)clean。
- [ ] 手動 live 驗:某 KB 設 `default_rerank_k` 由 5 → 20 + save → chat 問同一問題,觀察 retrieve top_k / citation 數隨之變(對照 5)。

## 4. Risks

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | `QueryRequest` top_k 改 Optional 影響其他 caller | Low | Med | 全 backend 只有 query.py L165/183/380 讀 `payload.top_k_rerank`,`top_k_retrieval` 無 reader;改後 pipeline 只讀 `effective`;`config_test` 建 `QueryRequest` 不傳 top_k(None OK);tests 明確覆蓋 |
| R2 | resolve 次序錯 → per-query override 失效或 KB default 被全域蓋 | Low | Med | `KbConfig.default_*` 係 concrete int,per-KB 必壓全域;per-query 經 `PerQueryOverrides` 最高優先;test 三層次序逐一斷言 |
| R3 | rerank_k 調大 → latency / cost ↑(更多 chunk 入 synth)| Med | Low | per-KB opt-in;預設 5 不變;成本知情記 spec(同 CH-006 R3 性質)|
| R4 | engine `overfetch` kwarg 改動牽連既有 retrieve 測試 | Low | Low | additive kwarg 預設 `None` = 既有行為;`fused_retrieve` 同步;既有 test 不傳 = 不破 |
| R5 | architecture.md §4.5 frozen schema 顯示 int 預設,改 Optional 造成 doc drift | Med | Low | §1-14 content lock 不動;記 drift note,改動向後相容(行為層 omitted=今日預設)|
| R6 | 跨 `/query` + `/query/stream` 漏接一路 | Low | Med | acceptance 明列兩路;test 覆蓋 |

## 5. Effort Estimate

~0.5 day(backend schema + effective_config + resolver + query.py wiring + engine kwarg ~半日;tests 數小時;無 frontend;live 驗短)。

## 6. Dependencies

- 無外部 / OQ 阻塞。Vendor stack 不變(無新 dep)。
- 跨 component C04(retrieval engine + query pipeline)+ C02(KbConfig / EffectiveConfig)。
- **非 H1**:無加/刪 architecture.md §3/§4 component,無 vendor swap,無 storage layout 改動,無 multi-KB arch 改動,無 8-view layout 改動,無 Tier 2 feature。純內部 schema 消歧義 + 既有 ADR-0040 resolver 延伸 + pipeline 接線。→ 無 ADR。
- **非 H7**:無 frontend / mockup 改動。
- **H6**:`backend/api/routes/query.py` 屬強制覆蓋清單 → 必須同步 test(§2.2 已列)。

## 7. Spec Changelog(deviation log)

| Date | Change | Reason | Approver |
|---|---|---|---|
| 2026-06-07 | Initial draft | CH-006 期間揭 `default_rerank_k`(+ `default_top_k`)set+save 後 chat 忽略 = dead control;CH-006 §2.3 已 deferred 本 CH | (待 approve) |
| 2026-06-07 | status draft → approved;§2.4 scope = 兩個都接入(`default_rerank_k` + `default_top_k` via engine `overfetch` kwarg)| Chris chat「批准 — 兩個都接入」| Chris |
| 2026-06-07 | scope 擴充(deviation):順帶恢復 **CH-006 incomplete-landing**。CH-006 query route 無條件傳 `detail_level=` 但 4 個 route-test mock 漏改 + `ConfigTestResult.resolved_config: dict[str,int\|bool\|None]` 容唔落 CH-006 `answer_detail: str` — 兩層皆被 mock 嘅 TypeError 502 互相遮蔽,CH-006「80 passed」未覆蓋呢 4 檔。因 CH-007 改 `execute_query_pipeline` + 為 EffectiveConfig 加欄位(亦 asdict 入 resolved_config),呢條 test suite 必須綠先驗證到 CH-007。修:4 檔 mock 加 `detail_level` + `resolved_config` type 放寬至含 `str`。屬 CH-007 blast-radius 內最小恢復,全透明記錄 | AI |
| 2026-06-07 | status approved → done | §3 acceptance 全驗(113 backend test pass / ruff clean / mypy 改動檔 clean);非 H1 無 ADR;零新 regression。**V3 live 驗 PASS**:w56-drive-ab-1 無 top_k → retrieved_chunks=11(=KB default,舊 5)、`top_k_rerank=3` → 3(override),零 KB mutation | AI |

---

**Lifecycle reminder**:呢份 spec locked after status=approved。重大 deviation → §7 changelog。**未 approve 前不 implement(R1.change)。**
