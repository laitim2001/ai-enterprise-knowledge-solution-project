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
### P2.2b 重建索引 + eval(🔴 north-star §15 硬閘,待執行)
- [ ] 即時重建 drive-images-1 索引(schema PUT 加 2 欄位 + W46 reindex re-ingest stamp,用戶拍板「即時重建」)
- [ ] **eval 驗 W43-85 問答品質 + 圖文還原不退(north-star §15 硬閘)** — fail-open + drive-images-1 無 grant → 預期 bit-identical(證 filter no-op);任何退化 = STOP
- [ ] 真端到端 trimming live smoke(有 grant 真 chunk:有權見、無權被 Azure 剔除)

## P2.3 classification clearance(DG1)
- [ ] `classification` clearance 比對(internal/restricted)
- [ ] restricted 文件只 restricted clearance 用戶可見 + internal 用戶被擋(測試)

## Phase Gate(收尾)
- [ ] G-P2.0 ~ G-P2.3 逐項驗
- [ ] RBAC / retrieval pytest 全綠 + ruff + mypy
- [ ] **eval 問答品質 + 圖文還原不退(north-star §15)**
- [ ] 端到端 smoke + 更新 TRACKER / FINDINGS
