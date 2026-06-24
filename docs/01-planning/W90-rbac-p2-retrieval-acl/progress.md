# W90 P2 — Progress

> 每日進展 + 決策 + commits + 結尾 retro。對應 [`checklist.md`](./checklist.md)。

## Day 1 — 2026-06-24(P2 kickoff + P2.0)

### 開工背景
- P1 完全完成(ADR-0066 **Accepted** 2026-06-24,用戶 decision owner 拍板;M2 達成)→ 次序鐵律 5 satisfied,P2 implementation 解鎖。
- 用戶「即 kickoff W90 P2」→ rolling JIT 建 W90 三件套(R1)。
- P2 = implementation phase(改 code/schema/檢索),H1 由 ADR-0066 Accepted 涵蓋;H6(retrieval/pipeline test)適用。

### P2 scope(per ADR-0066 Decision)
- P2.0 query 守衛(G1)→ P2.1 schema+stamp(G3)→ P2.2 filter+重建索引(G2/G4,高風險)→ P2.3 classification(DG1)。
- **north-star §15 硬閘**:P2.2 動檢索主路徑,必須 eval 驗 W43-85 圖文還原 + 問答品質不退。
- 文件 ACL 來源 = 5.1 KB 繼承(P2);5.2 文件級表留 P3。

### P2.0 query 端點 KB 層守衛(2026-06-24 ✅ 完成)
- **實作**:`/query` + `/query/stream` handler 加 `current_user` + `await assert_kb_access(request, payload.kb_id, current_user, "query")`。`acl.py` 加 `assert_kb_access` body-aware helper + refactor `require_kb_acl._guard` 復用(DRY)。
- **deviation(R3,見 plan changelog)**:守衛用 `assert_kb_access` 非 `require_kb_acl`(後者 path-based,不適用 body kb_id)。policy 相同,ADR-0066 G1 意圖達成。
- **測試**:`test_query_route_acl.py` 4(403×2 query+stream / 401×2);`test_acl_middleware` 加 4 `assert_kb_access` 單元(admin pass / 無 grant 403 / grant pass / backend None 503);4 受影響 query 整合 wire admin(per_kb / overlay 加 `get_current_user` override;observe / smoke user 加 `role=admin`)+ signature 斷言加 `current_user`(驗證透過 @observe_async chain 暴露)。
- **驗證**:67 passed + signature fix;ruff clean。

### P2.1 索引 schema + ingestion stamp(2026-06-24 ✅ 完成)
- **production-preserve 拍板:過渡期 fail-open**(plan §6 changelog)。理由:P2.1 只 stamp 新 ingest,P2.2 先重建現有索引;過渡期所有現有 chunk 未 stamp,fail-closed 會即刻擋光現有 KB 全部 chunk → W43-85 圖文還原 + 問答品質爆,撞 north-star §15。fail-open 係唯一唔破壞 north-star 嘅選擇;穩態(P2.2 重建後)所有 chunk 都 stamp → fail-open 與 fail-closed 收斂等價,洩漏面僅限過渡窗。
- **6 處 code(資料層 → stamp 層 → wire 層)**:
  1. `ChunkRecord`(`indexing/schemas.py`)加 `allowed_principals: list[str] = []` + `classification: str = "internal"`(fail-open default;`to_search_doc` 經 model_dump 自動帶)。
  2. `schema.json` 加 `allowed_principals: Collection(Edm.String)`(filterable)+ `classification: Edm.String`(filterable, facetable)。
  3. `acl.py` 加 `resolve_kb_principals(rbac_backend, kb_id)`(rbac None → `[]` fail-soft;讀 `list_kb_acl` 全 grant principal — query/edit/manage 都可讀,role rank 只 gate 寫)。
  4. `orchestrator.ingest()` 加 `allowed_principals` + `classification` 2 param → stamp 每 chunk(per-chunk list copy 不共享);orchestrator 零 rbac 依賴(關注點分離,Karpathy §1.3)。
  5. `documents.py`:`_IngestionDeps` 加 `rbac_backend` optional DI field + `_ingestion_deps_or_503` getattr(對齊既有 doc_config_store optional pattern)。
  6. `_run_ingest_pipeline` 經 `deps.rbac_backend` resolve principals → 傳落 `orchestrator.ingest`(3 caller upload/reindex/doc-reindex 全經此統一入口,零改 caller)。
- **stamp 真實生效**:server.py lifespan L153-155 已 wire `app.state.rbac_backend`(P2.0 F6b live smoke 驗過)→ production `_ingestion_deps_or_503` getattr 拿到真 backend。
- **測試**(7 新):`test_populate`(ChunkRecord ACL default + to_search_doc 帶 2 欄位)/ `test_orchestrator`(stamp 每 chunk + list 不共享 + BC fail-open default)/ `test_acl_middleware`(resolve None→[] / 空 KB→[] / 全 grant + 跨 KB 不洩漏)。
- **驗證**:71 passed(orchestrator/populate/acl/kb_reindex/query_route_acl)+ 67 passed(documents_route/contextual/ch009/doc_profile caller BC)+ ruff clean + mypy(acl/orchestrator 自身 0 error,17 全係既有 api/auth + ingestion/parsers transitive debt)。

## Day 1 cont — 2026-06-24(P2.2a filter 注入 + P2.2c 端到端 wiring)

### think-before-coding 三發現(Karpathy §1.1,記 plan changelog)
1. **洩漏面 4 個 hybrid 方法**(非 3):citation expansion 經 `list_chunks` 撈整 doc neighbor 餵答案,亦要 trim,否則 G4 confused deputy 從 expansion/parent-doc/citation 洩漏。
2. **fail-open 令現有 KB filter 注入係 no-op**:drive-images-1 無 ACL grant → 全 chunk `allowed_principals=[]` → fail-open filter 第一 disjunct `not any()` 放行 → 檢索 bit-identical。north-star §15 eval = 證 filter 正確(no-op),非擔心退化。
3. **重建 drive-images-1 亦 no-op**(無 grant → 重建後仍 `[]`)。真 trimming 驗證需有 grant KB。

### 用戶 2 決策(AskUserQuestion)
- **即時重建 drive-images-1**(非延後;承擔一次 re-ingest + eval 重驗 W43-85)。
- **造測試 fixture 端到端驗 trimming**(admin grant userA → userA 見、userB 剔除)。

### P2.2a filter 注入 + 11 層 threading(✅)
- `hybrid._build_acl_filter` fail-open OData:`None → None`(BC);`list → (not allowed_principals/any() or allowed_principals/any(p: search.in(p,'{principals}',',')))`。注入 4 方法(search / fetch_by_chunk_ids / fetch_chunks_by_section_path / list_chunks)。
- `user_principals: list[str] | None` **explicit threading**(非 contextvars,安全:漏層 type-check 暴露)經 11 函數:`principals_for_user`(admin → None bypass)→ query/query_stream → execute_query_pipeline(6 call)→ fused_retrieve / retrieval_engine(5 方法)/ context_expander / parent_doc_retriever / citation_expansion / synthesizer(2)/ crag.refine(4 call)→ 4 hybrid 終點。
- **新測試**:`test_retrieval_acl_filter.py`(12)+ `test_query_route_acl_trimming.py`(3,P2.2c)+ `test_acl_middleware` principals_for_user(2)。

### 測試修復(threading 影響既有 fake/assert)
- **17 fake 簽名/assert 更新**(全 test-fixture,非 production):fake `synthesize`/`expand_context_for_chunks`/`aggregate_parent_sections_for_chunks`/`_fetch`/`_list_chunks` 加 `user_principals` kwarg(test_query_per_kb_config / test_config_test_route / test_e1_e5_e12_smoke / test_observe_query_route / test_query_doc_config_overlay / test_parent_doc_retriever / test_citation_expansion);assert_*_with 加 `user_principals=None`(test_crag / test_synthesizer / test_citation_expansion)。
- **連帶發現 P0/P2.0 遺留 auth 缺口**(targeted run 未 catch,全套先暴露):`test_multi_kb_routing`(P2.0 /query auth)+ `test_doc_profile_backfill`(P0 F5 backfill `require_kb_acl`)嘅 `_build_app` 補 admin auth override。**非 P2.2 引入,但同批修復**。
- **驗證**:全套 **1547 passed**(原 1530 + 新 17)/ 25 skip / 0 fail + ruff clean。

### 下一步 → P2.2b(🔴 north-star §15 硬閘,待執行)
- 即時重建 drive-images-1(schema PUT + W46 reindex stamp)+ eval 驗 W43-85 不退 + 真端到端 trimming live smoke。
- **動檢索主路徑前先 surface eval 基準等用戶拍板**(需 running backend + Azure)。

### Commits
- (kickoff)docs(planning): kickoff W90 P2 phase artifacts
- feat(api): P2.0 query endpoint KB-level guard
- feat(api): P2.1 index ACL schema + ingestion stamp
- (本 entry)feat(retrieval): P2.2a retrieval-layer ACL filter + threading + P2.2c trimming fixture
