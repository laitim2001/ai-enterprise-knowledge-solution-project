# W90 P2 — Checklist

> 對應 [`plan.md`](./plan.md) §2 P2.0-P2.3 + §3 Phase Gate。完成 → `[x]` + progress Day-N 記錄。
> 未完項**不可刪**(per CLAUDE.md §10 sacred rule),只 `→ [x]` 或標 🚧 + 理由。
> **約束**:索引結構 / filter / ACL 來源以 ADR-0066(Accepted)Decision 為準。

## P2.0 query 端點補 KB 層守衛(G1,最低風險先做)
- [x] `/query` + `/query/stream` 加守衛 → **`assert_kb_access("query")`**(body-aware;kb_id 在 `QueryRequest` body 非 path → `require_kb_acl` path-based 不適用,acl.py 加 helper + refactor `_guard` 復用 DRY)
- [x] 無 KB query grant 帳號 query/stream → **403**(`test_query_route_acl.py` 4 測試)
- [x] admin / query-grant 用戶通過 → admin pass-guard(4 整合測試 pipeline 跑通)+ `assert_kb_access` 單元測試 grant pass(`test_acl_middleware` 4 新測試)
- [x] 受影響 query 整合測試 wire admin(test_query_per_kb_config / _doc_config_overlay 加 override;_observe / _smoke user 加 role=admin)+ signature 斷言同步(`current_user` 透過 @observe_async chain 暴露)
- [x] 零 regression(67 passed + signature fix)

## P2.1 索引 schema + ingestion stamp(G3)
- [x] `schema.json` 加 `allowed_principals: Collection(Edm.String)`(filterable)+ `classification: Edm.String`(filterable, facetable);`to_search_doc` drift guard `test_w70_search_doc_fields_align_with_schema_json` 自動驗對齊
- [x] `ChunkRecord`(`indexing/schemas.py`)加 2 欄位(`allowed_principals` default `[]`、`classification` default `internal`;`to_search_doc` 經 model_dump 自動帶,無 rename)
- [x] ingestion stamp(5.1 KB 繼承):`resolve_kb_principals(rbac_backend, kb_id)` helper(acl.py,讀 `list_kb_acl` 全 grant principal,role rank 只 gate 寫)→ `_run_ingest_pipeline` 經 `deps.rbac_backend` resolve → `orchestrator.ingest(allowed_principals=...)` stamp 每 chunk(per-chunk list copy 不共享);`classification` 預設 internal(P2.3 先分);orchestrator 零 rbac 依賴(關注點分離)
- [x] **production-preserve 拍板:過渡期 fail-open**(plan §6 changelog 2026-06-24):空 `allowed_principals` = 公開;rbac None / 無 grant → `[]`(fail-soft);穩態(P2.2 重建後)收斂等價。理由 = north-star §15(P2.1→P2.2 過渡期 fail-closed 會擋光現有 KB chunk → 圖文還原爆)
- [x] 單元測試:`test_populate`(ChunkRecord ACL default + to_search_doc 帶 2 欄位)/ `test_orchestrator`(stamp 每 chunk + list 不共享 + BC fail-open default)/ `test_acl_middleware`(resolve None→[] / 空 KB→[] / 全 grant + 跨 KB 不洩漏)= 7 新測試;71 + 67 passed + ruff + mypy(自身 0 error)

## P2.2 檢索 filter + 重建索引(G2/G4,高風險)
### P2.2a filter 注入 + 11 層 principals threading(✅ 完成)
- [x] `hybrid.py` `_build_acl_filter` fail-open OData helper + **4 個檢索方法**注入(`search` / `fetch_by_chunk_ids` / `fetch_chunks_by_section_path` / `list_chunks` — citation expansion 經 `list_chunks` 撈整 doc neighbor,亦係洩漏面)
- [x] 11 層 `user_principals: list[str] | None` explicit threading:query 端點 `principals_for_user`(admin → None bypass / 非 admin → `[oid]`)→ `execute_query_pipeline`(6 call)+ query_stream(4 call)→ `result_fusion.fused_retrieve` / `retrieval_engine`(5 方法)/ `context_expander` / `parent_doc_retriever` / `citation_expansion` / `synthesizer`(synthesize + stream)/ `crag.refine`(4 call)
- [x] 單元測試:`test_retrieval_acl_filter.py`(12 — `_build_acl_filter` None/list/空/escape + 4 方法 payload 注入 + BC None 不注入)+ `test_acl_middleware` principals_for_user(admin None / 非 admin [oid])
- [x] BC 驗證:`user_principals=None` → filter byte-identical 無 ACL clause(既有 test/工具/V4 不受影響)
### P2.2c 端到端 trimming wiring(✅ 完成,真 Azure drop 留 P2.2b live)
- [x] `test_query_route_acl_trimming.py`(3):granted user principal 到達 search filter / 兩 user 各自 filter 無 cross-leakage / admin 無 ACL clause(route → rbac grant → search filter 端到端 wiring)
### P2.2b 重建索引 + eval(✅ 完成,north-star §15 PASS 用戶判決 2026-06-24)
- [x] 即時重建 drive-images-1 索引:`scripts/put_index_schema.py` schema PUT(additive 加 2 欄位,既有 doc 保留)→ `POST /kb/drive-images-1/reindex`(6 docs / 369 chunks / **0 fail**,stamp `allowed_principals=[]` + `classification=internal`)
- [x] **eval 驗圖文還原不退(north-star §15)**:before recall **1.000**/prec 0.988 → after recall **1.000(完全保留)**/prec 0.954;**recall = 全圖召回(ADR-0054 成功定義)零退化**;precision -0.034 = re-ingest 多抓 1-7 張 section 圖(良性,多圖非少圖,**非 filter 退化** —— eval admin bypass 證 filter no-op)。**用戶判決 PASS**
- [x] 真端到端 trimming live smoke:`scripts/acl_trimming_live_smoke.py`(self-cleaning 合成 restrictive chunk)→ alice(列入)見=1 / bob(未列入)**被 Azure 剔除=0** / bob fail-open 見 369 空-ACL chunk 全放行 → **Azure server-side 真 drop 驗證 PASS**

## P2.3 classification clearance(DG1)(✅ 完成 2026-06-24)
### 讀側 — filter clearance clause(零 re-threading)
- [x] `_build_acl_filter` 加 classification clause:非 None list(非 admin = internal clearance)append `(classification eq 'internal' or classification eq null)`;None(admin / 工具 / V4)乜都唔加 → **clearance 由 role 推導,principals 是 None ⟺ admin = restricted-cleared,無需 threading 第二個 param**(think-before simplification,plan changelog)
- [x] `null` disjunct = production-preserve fail-open(未重建 KB classification null → 視為 internal 可見,同 `allowed_principals` 空集 fail-open 對稱)
- [x] 單元測試:`test_retrieval_acl_filter.py` 加 P2.3(非 admin 限 internal + null / admin None 無 clause / 主 search path 含 clause)+ `test_query_route_acl_trimming.py` 加 route 層 clearance clause 斷言
### 寫側 — 完整閉環標記端點(用戶決策)
- [x] `PATCH /kb/{kb_id}/docs/{doc_id}/classification` admin-only(`require_role("admin")`)→ 持久化(`doc_classification_store`)先 + merge-restamp 索引(`IndexPopulator.update_doc_classification`,search-then-merge 只更新 classification 欄位,無 re-ingest)
- [x] 新 `kb_management/doc_classification_store.py`(Protocol + InMemory + Postgres + factory,mirror `doc_profile_store`)+ `api/schemas/doc_classification.py`(`ClassificationUpdateRequest` Literal + `DocClassificationInfo`)+ server.py lifespan wire `app.state.doc_classification_store`
- [x] `_run_ingest_pipeline` 讀持久化 classification → 傳 `orchestrator.ingest(classification=...)`:**restricted 文件 re-ingest/reindex/backfill 不退回 internal**(安全屬性)
- [x] restricted 文件只 restricted clearance(admin)可見 + internal 用戶被擋:`test_doc_classification_route.py`(7:200 標記+持久化+restamp / revert / 403 非 admin / 422 invalid / 404 doc / 404 KB / 403 archived / 503 無 store)+ `test_doc_classification_store.py`(9 CRUD)+ `test_populate.py`(3 restamp)+ `test_documents_route.py`(re-ingest 保留 restricted)

## Phase Gate(收尾)
- [ ] G-P2.0 ~ G-P2.3 逐項驗
- [ ] RBAC / retrieval pytest 全綠 + ruff + mypy
- [ ] **eval 問答品質 + 圖文還原不退(north-star §15)**
- [ ] 端到端 smoke + 更新 TRACKER / FINDINGS
