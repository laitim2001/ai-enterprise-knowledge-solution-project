---
phase: W57
name: per-doc-config-backend
status: active        # draft | active | closed
created: 2026-06-09
owner: "Claude (AI) — 技術 Lead Chris 審閱"
gap: "Gap A / P2a (per-document config platform — backend layer)"
adr: ADR-0050
spec_refs:
  - docs/02-architecture/per-document-config-platform-design.md §3.1 (Layer A)
  - ADR-0040  # per-KB tunable retrieval config scope (本 phase 延伸至 per-DOC)
  - architecture.md §3.6 / §3.7  # config 模型 / citation expansion
---

# W57 — Per-Document 配置平台(後端層 P2a)

> **緣起**:用戶 2026-06-01 foundational vision「不同 KB 嘅文件可以運用不同度身訂做配置,喺平台
> 試跑驗證後持久化到該文件」(memory `project_per_kb_tunable_config_vision`)。Gap C(圖片位置 +
> 完整性)已喺 CH-011/CH-012 完成;本 phase 起 **Gap A — per-document 粒度配置**,係 vision 核心。
> 平台藍圖:`docs/02-architecture/per-document-config-platform-design.md` §3.1 Layer A。

## 1. 範圍(Scope)

**P2a = 後端 per-doc 配置層**(UI 拆 P2b,per 2026-06-09 用戶決策 Q2)。本 phase **唔掂 frontend**
(per-doc 配置 UI 喺 mockup 無對應 surface = H7,UI 待 P2b mockup 決定後做)。

配置粒度由現有 **per-KB** 落到 **per-document**,執行期按**被引 chunk 嘅主導 doc**(dominant doc)
resolve 該文件 profile,插入解析鏈中間:

```
per-query override  >  per-DOC profile  >  per-KB KbConfig  >  global Settings
```

**解析語意(2026-06-09 用戶決策 Q1 = 主導 doc + 後處理旋鈕)**:

| 旋鈕類別 | 旋鈕 | pipeline 消耗點 | per-doc? |
|---|---|---|---|
| 檢索入口 | `default_top_k` / `default_rerank_k` / `parent_doc_*` | retrieve / parent-doc(synth 前)| ❌ 維持 per-KB(引文未知前已消耗;雞同蛋)|
| 合成 | `answer_detail` | synth | ✅ dominant doc |
| 引文後處理 | `citation_expansion_*` / `citation_neighbour_*` / `max_images_per_answer` / `enable_chapter_overview_pin` | citations / images(retrieval 後)| ✅ dominant doc |

**Dominant doc** = reranked chunk set 入面**出現 chunk 數最多**嘅 `doc_id`(tie → 最高 rank chunk 嘅
doc)。單文件 query(Drive 手冊主用例)→ dominant doc = 唯一 doc → 效果 = 100% per-doc。Multi-doc
query → 用主導 doc 嘅 profile(簡單合理 default)。

## 2. 交付物(Deliverables)

| # | 交付 | Component | 檔案(預估)|
|---|---|---|---|
| **F1** | `DocConfig` schema + per-doc 配置 store(Postgres 表 + in-memory fallback + factory)| C02 | `backend/api/schemas/doc_config.py`(新)/ `backend/kb_management/doc_config_store.py`(新)/ `factory.py` |
| **F2** | `resolve_effective_config` 加 per-DOC layer(post-retrieval 旋鈕)| C05 | `backend/generation/effective_config.py` |
| **F3** | Pipeline dominant-doc 注入(`/query` + `/query/stream` retrieve 後重 resolve 後處理旋鈕)| C04/C05 | `backend/api/routes/query.py` |
| **F4** | per-doc config CRUD API(`GET/PUT/DELETE /kb/{kb_id}/docs/{doc_id}/config`)| C09 | `backend/api/routes/doc_config.py`(新)+ `api/server.py` router wire |
| **F5** | config-test doc-scope(`ConfigTestRequest.doc_id` → 試跑針對單一文件 profile)| C05/C06 | `backend/api/schemas/config_test.py` + `backend/api/routes/config_test.py` |
| **F6** | Test(H6 — C02/C05/C06 同步)| C06/test | `backend/tests/test_doc_config_*.py`(新)+ effective_config / query route regression |
| **ADR** | ADR-0050 per-doc config scope + dominant-doc 解析策略 | doc | `docs/adr/0050-*.md` + README index |

## 3. Acceptance Criteria

- **AC1**(F1 storage):per-doc `DocConfig`(只含 post-retrieval Optional 旋鈕)可 upsert / get / delete /
  list-by-kb;Postgres 表 `document_configs(kb_id, doc_id, config JSONB, PK(kb_id,doc_id))`;
  `DATABASE_URL` unset → in-memory fallback(同 `make_kb_backend` pattern)。
- **AC2**(F2 解析):`resolve_effective_config(settings, kb_config, per_query, doc_config=...)` 對
  post-retrieval 旋鈕行 `per-query > per-DOC > per-KB > global`;retrieval-entry 旋鈕**不受** doc layer
  影響(`DocConfig` 無嗰啲 field)。
- **AC3**(production-preserve / G7):`doc_config=None`(無 per-doc 配置)→ resolve 結果 **bit-identical**
  現有行為;既有 `test_effective_config` / `test_query_per_kb_config` 全綠。
- **AC4**(F3 dominant-doc):`/query` + `/query/stream` retrieve 後,若 dominant doc 有 per-doc 配置 →
  後處理旋鈕用該 profile;無 → 維持 per-KB(無 regression)。單文件 query → 等同全 per-doc。
- **AC5**(F4 API):per-doc config CRUD endpoint 透傳 store;mock auth `Bearer dev-token`;404 when KB 不存在。
- **AC6**(F5 config-test):`ConfigTestRequest` 加 `doc_id`(optional)→ 試跑解析鏈插 doc layer;`None` =
  現有 per-KB 行為(bit-identical)。
- **AC7**(H4):per-doc config 喺單一 KB 內,**非** multi-tenancy(租戶隔離)= Tier 1-friendly。
- **AC8**(H6):每個 F1/F2/F3/F4/F5 同步 unit test;production-preserve regression 全綠;ruff format clean。

## 4. 風險

- **R1 🟡 Pipeline 雙重 resolve 複雜度**:dominant-doc 注入要喺 retrieve 後重 resolve 一次 effective。
  緩解:單點注入(retrieve 後、synth 前),downstream 讀 `effective.*` 不變;`doc_config=None` 早 return
  保持 bit-identical。
- **R2 🟡 doc_id free-form**(無 documents 持久表)→ per-doc config 用 free-form key,可能指向已刪文件。
  緩解:MVP store 唔強制 FK;list-by-kb + UI(P2b)負責 surface 孤兒。記入 OQ。
- **R3 🟢 production-preserve**:所有新 path `doc_config=None`/store 空 → bit-identical(沿 ADR-0028/0040
  migration-default precedent)。
- **R4 🟡 stream 路徑**:`/query/stream` 用 `compose_query_stream` callback;dominant-doc 重 resolve 要喺
  retrieve 後、synth_stream 開始前完成(`effective` 變數重新賦值,callback closure 讀新值)。

## 5. 非目標(Non-goals)

- ❌ Frontend per-doc 配置 UI(= P2b,待 mockup 決定)。
- ❌ 檢索入口旋鈕 per-doc(top_k/rerank/parent_doc 維持 per-KB,per Q1 決策)。
- ❌ Per-citation owning-doc 解析(用 dominant doc;per Q1 決策 reject Option B)。
- ❌ Gap B query 意圖 gate(= P3,必要性未證實)。
- ❌ documents 持久表 / FK 驗證(MVP free-form doc_id key)。

## 6. ADR 觸發(H1)

擴 config 解析模型由 per-KB 到 per-DOC + 新持久層 + pipeline 解析點 = ADR-0040 後續 → **ADR-0050**
(per-doc config scope + dominant-doc 解析策略)。用戶 2026-06-09 已 approve 方向(Q1 = Option A 主導 doc +
後處理旋鈕;Q2 = 後端先行 P2a)→ ADR Accepted。

## 7. Changelog

| Date | Change | Reason |
|---|---|---|
| 2026-06-09 | Initial plan(P2a 後端層;Q1 dominant-doc + post-retrieval 旋鈕 / Q2 UI 拆 P2b)| 用戶 trigger Gap A;2 決策已拍板 |
