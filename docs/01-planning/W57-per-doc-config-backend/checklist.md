---
phase: W57
plan_ref: ./plan.md
status: active     # active | closed
last_updated: 2026-06-09
---

# W57 — Checklist

> 逐項 atomic;done → `[x]`,未做標 🚧 + 理由。Plan locked 2026-06-09(Q1 dominant-doc + post-retrieval / Q2 UI 拆 P2b)。

## Setup
- [x] S1 — ADR-0050 寫 + Accepted(Chris)+ README index
- [x] S2 — plan / checklist / progress committed(kickoff commit)

## F1 — DocConfig schema + per-doc store(C02)
- [x] F1.1 — `DocConfig` Pydantic schema(`backend/api/schemas/doc_config.py`):只含 post-retrieval Optional 旋鈕(`answer_detail` / `citation_expansion_*` / `citation_neighbour_*` / `max_images_per_answer` / `enable_chapter_overview_pin`);全 `None` = 繼承上層
- [x] F1.2 — `DocConfigStore` Protocol + `InMemoryDocConfigStore`(`backend/kb_management/doc_config_store.py`):`get(kb_id, doc_id)` / `upsert(kb_id, doc_id, config)` / `delete(kb_id, doc_id)` / `list_for_kb(kb_id)`
- [x] F1.3 — `PostgresDocConfigStore`:表 `document_configs(kb_id TEXT, doc_id TEXT, config JSONB, PK(kb_id,doc_id))`;`CREATE TABLE IF NOT EXISTS` on connect(同 PostgresKBBackend pattern;`DictRow`-typed = 0 新 mypy error,改善 postgres_backend pattern)
- [x] F1.4 — `make_doc_config_store(settings)` factory(`DATABASE_URL` set → Postgres,else in-memory;lazy psycopg import)+ wire app.state(`server.py`)

## F2 — EffectiveConfig per-DOC layer(C05)
- [x] F2.1 — `resolve_effective_config` 加 `doc_config: DocConfig | None = None` 參數;post-retrieval 旋鈕解析鏈插 doc layer(用 `_layer()` helper folding doc-over-kb 入既有 `_resolve` 鏈,`per-query > per-DOC > per-KB > global`);retrieval-entry 旋鈕行 untouched
- [x] F2.2 — `doc_config=None` / `DocConfig()` early path = bit-identical(production-preserve;test 證實)

## F3 — Pipeline dominant-doc 注入(C04/C05)
- [x] F3.1 — `_dominant_doc_id(chunks)` helper:reranked chunk set 出現最多嘅 doc_id(tie → 最高 rank,dict insertion order + max first-key)
- [x] F3.2 — `execute_query_pipeline`(`/query`):retrieve 後即注入 overlay callback → 重 resolve effective(後處理旋鈕);無 config / 無 store 跳過
- [x] F3.3 — `query_stream`(`/query/stream`):retrieve 後重賦值 `effective`(callback closure + synth_stream 讀新值)
- [x] F3.4 — doc config store 經 `app.state.doc_config_store` 注入(`_doc_config_store(request)` + `_make_doc_overlay`)

## F4 — per-doc config CRUD API(C09)
- [x] F4.1 — `backend/api/routes/doc_config.py`:`GET /kb/{kb_id}/docs/{doc_id}/config`(無 → 200 空 DocConfig)/ `PUT`(upsert)/ `DELETE`(204 idempotent)/ `GET /kb/{kb_id}/doc-configs`(list,避開 `/docs/{doc_id}` 撞名);KB 不存在 → 404
- [x] F4.2 — router wire 入 `api/server.py`(`dependencies=_auth`)

## F5 — config-test doc-scope(C05/C06)
- [x] F5.1 — `ConfigTestRequest` 加 `doc_id: str | None = None`
- [x] F5.2 — config-test route:有 `doc_id` → load 該 doc stored config 插解析鏈(draft > per-DOC > per-KB > global,draft+saved 兩側皆插);`None` / 無 store = 現有行為 bit-identical

## F6 — Test(H6)
- [x] F6.1 — `test_doc_config_store.py`:in-memory upsert/get/delete(idempotent)/list/kb-isolation round-trip + factory 選型(in-memory vs Postgres type,不連線)。**註**:live Postgres round-trip 未寫(需 live DB),以 factory-選型 + Protocol 共形覆蓋(deviate from plan「skip-if-no-DB」措辭)
- [x] F6.2 — `test_effective_config.py` 加 6 個 per-DOC layer test:doc 蓋 per-KB(多 post-retrieval 旋鈕)/ partial 落 per-KB / retrieval-entry 旋鈕不受影響 / per-query 勝 per-DOC / doc False 勝 KB True / `None`+`DocConfig()` bit-identical
- [x] F6.3 — `_dominant_doc_id` unit test(單 doc / 最多引用勝 / tie 取最高 rank / 空+無 doc_id → None)
- [x] F6.4 — `test_doc_config_routes.py`:GET 空默認 / PUT round-trip / PUT replace / DELETE idempotent / list / 404 全動詞
- [x] F6.5 — `test_config_test_route.py` 加 3 test:doc-scope 套用 stored doc config / 無 doc_id 忽略 store / draft 勝 doc-scope
- [x] F6.6 — production-preserve regression：`test_effective_config`(既有全綠)/ `test_query_per_kb_config`(全綠)/ `test_config_test_route`(既有全綠);+ `test_query_doc_config_overlay.py` 端到端(`/query`+`/query/stream` overlay 套用 / 無 config / 非主導 doc 不漏 / 無 store back-compat）

## Verify
- [x] V1 — pytest **62 passed**(W57 + regression);ruff format clean(12 檔);ruff check 專案預設**全綠**(server.py 30 E402 = pre-existing truststore pattern,我加 import 已 noqa);mypy `--explicit-package-bases` 新 file **零新 error**(剩 7 全在 pre-existing postgres_backend.py)
- [ ] V2 —(可選)live /query drive-images-1 + per-doc config upsert,確認 dominant-doc 解析生效
- [ ] V3 — 用戶 review

## Closeout
- [ ] C1 — plan/checklist/progress status → closed;progress retro
- [ ] C2 — ff-merge → main(用戶確認);platform design doc §7 P2 標 done + §0 TL;DR phasing 更新
