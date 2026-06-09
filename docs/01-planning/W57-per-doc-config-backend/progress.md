---
phase: W57
plan_ref: ./plan.md
checklist_ref: ./checklist.md
status: active     # active | closed
---

# W57 — Progress

> Day-N entries + closeout retro。

---

## Day 1 — 2026-06-09

### Done
- Gap C(CH-011/CH-012)收尾後,用戶 trigger Gap A / P2(per-doc 配置平台 + UI,vision 核心)。
- 讀平台藍圖 §3.1 Layer A + ground 現有 config 解析鏈(`EffectiveConfig` `per-query > per-KB > global`,
  request 入口 resolve 一次)+ 儲存層(`KBStorageBackend` Protocol + Postgres/InMemory + factory)+
  pipeline(`/query` `execute_query_pipeline` + `/query/stream` `query_stream`,retrieve 後拎到 reranked chunks)。
- **H7 發現**:per-doc 配置 UI 喺 mockup **無對應 surface**(`ekp-page-doc-detail.jsx` 純唯讀 chunk
  inspector;config UI 只喺 KB 層 `ekp-page-kb.jsx` SettingsTab)→ 唔可以自行 approximate。
- **2 個架構決策(AskUserQuestion)**:
  - **Q1 解析語意 = 主導 doc + 後處理旋鈕**:per-doc 只蓋 post-retrieval 旋鈕(answer_detail /
    citation_expansion / neighbour_images / max_images / overview_pin),用 dominant doc resolve;
    retrieval-entry(top_k/rerank/parent_doc)維持 per-KB。單文件 query → 等同全 per-doc。
  - **Q2 UI 拆 P2b**:今個 phase = P2a 後端層;UI 待 mockup 決定。

### Decisions
- Phase W57 = P2a 後端 per-doc 配置層(不掂 frontend = 守 H7)。
- ADR-0050 延伸 ADR-0040 config-scope(per-KB → per-DOC + dominant-doc 解析)。
- 儲存用獨立 `DocConfigStore`(新表 `document_configs`)平行 `make_kb_backend` pattern,唔污染 KB CRUD。
- doc_id free-form key(無 documents 持久表;MVP 不強制 FK,記 OQ)。

### 實作 + Verify(Day 1 cont)
- **F1 store**:`DocConfig` schema(10 個 post-retrieval 旋鈕,全 Optional)+ `DocConfigStore` Protocol + `InMemoryDocConfigStore` + `PostgresDocConfigStore`(表 `document_configs`,`DictRow`-typed = 0 新 mypy error)+ `make_doc_config_store` factory + wire `app.state.doc_config_store`(`server.py`)。
- **F2 解析**:`resolve_effective_config` 加 `doc_config` 參數;新增 `_layer()` helper 把 doc-over-kb fold 入既有 `_resolve` 鏈(只改 post-retrieval 旋鈕行,retrieval-entry 行 untouched = surgical)。
- **F3 dominant-doc**:`_dominant_doc_id`(最多引用 doc,tie 取最高 rank)+ `_make_doc_overlay` callback(route 層 close over resolution inputs)+ `execute_query_pipeline` / `query_stream` retrieve 後單點注入(downstream `effective.*` 不變)。
- **F4 CRUD API**:`doc_config.py` 4 endpoint(GET/PUT/DELETE `/config` + list `/doc-configs`,避開 `/docs/{doc_id}` 撞名)+ wire `server.py` `_auth`。
- **F5 config-test doc-scope**:`ConfigTestRequest.doc_id` + route load stored doc config 插 draft+saved 兩側解析鏈。
- **F6 test**:5 個新 test 檔/section,**62 passed**(test_doc_config_store / test_doc_config_routes / test_query_doc_config_overlay 新 + test_effective_config 6 新 + test_config_test_route 3 新 + 既有 regression 全綠)。
- **V1 PASS**:pytest 62 綠;ruff format clean(12 檔);ruff check 專案預設全綠(server.py 30 E402 = pre-existing truststore,我 import 已 noqa);mypy `--explicit-package-bases` 新 file 零新 error(剩 7 全在 pre-existing postgres_backend.py)。

### Decisions(cont)
- 儲存層 `_connect` 用 `psycopg.AsyncConnection[DictRow]` typed(改善 postgres_backend.py 同 pattern 嘅 mypy 缺口)→ 新 file 零新 mypy error,守 §3.1 mypy-clean 目標,但**不** retro-fix postgres_backend(非我 mess,Karpathy §1.3)。
- list endpoint 路徑 `/kb/{kb_id}/doc-configs`(非 `/docs/configs`)避開 documents route `/kb/{kb_id}/docs/{doc_id}` 以 `doc_id="configs"` 搶 match。

### Blockers
- 無(待 V2 可選 live 驗 + V3 用戶 review)。

### Commits
| Hash | Subject |
|---|---|
| `2d98de1` | docs(planning): W57 kickoff — plan + ADR-0050 |
| _(pending)_ | feat(generation): W57 per-doc config backend layer(F1-F6) |

---

**End of W57 progress(Day 1)**
