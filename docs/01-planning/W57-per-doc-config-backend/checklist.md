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
- [ ] F1.1 — `DocConfig` Pydantic schema(`backend/api/schemas/doc_config.py`):只含 post-retrieval Optional 旋鈕(`answer_detail` / `citation_expansion_*` / `citation_neighbour_*` / `max_images_per_answer` / `enable_chapter_overview_pin`);全 `None` = 繼承上層
- [ ] F1.2 — `DocConfigStore` Protocol + `InMemoryDocConfigStore`(`backend/kb_management/doc_config_store.py`):`get(kb_id, doc_id)` / `upsert(kb_id, doc_id, config)` / `delete(kb_id, doc_id)` / `list_for_kb(kb_id)`
- [ ] F1.3 — `PostgresDocConfigStore`:表 `document_configs(kb_id TEXT, doc_id TEXT, config JSONB, PK(kb_id,doc_id))`;`CREATE TABLE IF NOT EXISTS` on connect(同 PostgresKBBackend pattern)
- [ ] F1.4 — `make_doc_config_store(settings)` factory(`DATABASE_URL` set → Postgres,else in-memory;lazy psycopg import)+ wire app.state

## F2 — EffectiveConfig per-DOC layer(C05)
- [ ] F2.1 — `resolve_effective_config` 加 `doc_config: DocConfig | None = None` 參數;post-retrieval 旋鈕解析鏈插 doc layer(`per-query > per-DOC > per-KB > global`);retrieval-entry 旋鈕不受影響
- [ ] F2.2 — `doc_config=None` early path = bit-identical(production-preserve)

## F3 — Pipeline dominant-doc 注入(C04/C05)
- [ ] F3.1 — `_dominant_doc_id(chunks)` helper:reranked chunk set 出現最多嘅 doc_id(tie → 最高 rank)
- [ ] F3.2 — `execute_query_pipeline`(`/query`):retrieve 後、expand/synth 前,load dominant doc config → 重 resolve effective(後處理旋鈕);無 config 跳過
- [ ] F3.3 — `query_stream`(`/query/stream`):同上,retrieve 後重賦值 `effective`(callback closure 讀新值)
- [ ] F3.4 — doc config store 經 app.state / Depends 注入 route

## F4 — per-doc config CRUD API(C09)
- [ ] F4.1 — `backend/api/routes/doc_config.py`:`GET /kb/{kb_id}/docs/{doc_id}/config`(無 → 200 空 DocConfig)/ `PUT`(upsert)/ `DELETE`(204);KB 不存在 → 404
- [ ] F4.2 — router wire 入 `api/server.py`;mock auth dep

## F5 — config-test doc-scope(C05/C06)
- [ ] F5.1 — `ConfigTestRequest` 加 `doc_id: str | None = None`
- [ ] F5.2 — config-test route:有 `doc_id` → load 該 doc config 插解析鏈(draft > per-DOC > per-KB > global);`None` = 現有行為 bit-identical

## F6 — Test(H6)
- [ ] F6.1 — `test_doc_config_store.py`:in-memory + (skip-if-no-DB)Postgres upsert/get/delete/list round-trip
- [ ] F6.2 — `test_effective_config.py` 加 per-DOC layer test:doc layer 蓋 per-KB(post-retrieval 旋鈕)/ retrieval-entry 旋鈕不受影響 / `doc_config=None` bit-identical
- [ ] F6.3 — `_dominant_doc_id` unit test(單 doc / 多 doc / tie)
- [ ] F6.4 — doc_config CRUD API route test
- [ ] F6.5 — config-test doc-scope route test(doc_id 透傳 + None bit-identical)
- [ ] F6.6 — production-preserve regression：既有 `test_effective_config` / `test_query_per_kb_config` / `test_config_test_*` 全綠

## Verify
- [ ] V1 — pytest 全綠(新 + 既有);ruff format clean;新 code 零新 ruff error
- [ ] V2 —(可選)live /query drive-images-1 + per-doc config upsert,確認 dominant-doc 解析生效
- [ ] V3 — 用戶 review

## Closeout
- [ ] C1 — plan/checklist/progress status → closed;progress retro
- [ ] C2 — ff-merge → main(用戶確認);platform design doc §7 P2 標 done + §0 TL;DR phasing 更新
