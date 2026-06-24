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

## Day 1 cont — 2026-06-24(P2.2b 重建 + eval + live trimming,north-star §15 PASS)

### 用戶 2 決策(AskUserQuestion)
- **即時重建 drive-images-1** + **現在 push** `5fca451`(已 push,`9284403..5fca451`)。

### 執行前 blocker 全解(無需 restart,零撞 session)
- pre-flight 全綠(Langfuse 200 / backend 200 全 component ok / Postgres 1 row)。
- mock auth dev-token = **role admin** → `assert_kb_access` 過(無 403)+ `principals_for_user(admin)=None` → filter trivial bypass → eval 測 rebuild 效果(filter 正確性 + 非 admin trimming 已由測試證)。
- **stale backend 洞察**:running backend 係 P2.1(9284403),但 filter 對 drive-images-1 證實 no-op(無 grant + fail-open),故 P1 backend eval-after-rebuild 足夠驗 north-star §15,無需 restart 到 P2.2。

### 重建序列(全成功)
1. `scripts/put_index_schema.py --kb-id drive-images-1`:複用 `create_index_for_kb` PUT additive 加 2 欄位(既有 doc 保留,reindex 前該欄位 null)。**坑**:Windows console cp1252 唔食 `→`(改 ASCII + `PYTHONIOENCODING=utf-8`)。
2. `POST /kb/drive-images-1/reindex`(202):6 docs / 369 chunks / **0 fail / 0 skip**,stamp `allowed_principals=[]`。

### eval 比對(north-star §15)
| 指標 | before | after | |
|---|---|---|---|
| mean image-recall | 1.000 | **1.000** | **完全保留** ✅ |
| mean image-precision | 0.988 | 0.954 | -0.034 |
- **recall 全 query 1.00 = 全圖召回(ADR-0054 成功定義)零退化**。precision delta = re-ingest 多抓 1-7 張 section 圖(Q004/Q005/Q006/Q043),**良性(多圖非少圖,recall 無損),源自 re-ingest 非 filter**(eval admin bypass 證 filter 完全唔參與檢索)。**用戶判決 PASS**。

### live trimming smoke(Azure 真 drop 驗證)
- `scripts/acl_trimming_live_smoke.py`(self-cleaning):upload 合成 restrictive chunk `allowed_principals=['alice-oid']` → alice(列入)見=**1** / bob(未列入)**被 Azure 剔除=0** / bob fail-open 見 369 空-ACL chunk 全放行 → 刪除合成 chunk。**PASS** —— Azure server-side `any()`/`search.in` 真 drop + fail-open 雙驗。**坑**:Azure document key 唔可 leading underscore(`__x__` → 400 InvalidName)。

### P2.2 完整收束
- P2.0(query 守衛)+ P2.1(索引 schema+stamp)+ P2.2a(filter+11 層 threading)+ P2.2c(端到端 wiring fixture)+ P2.2b(重建+eval+live drop)**全部 ✅**。north-star §15 PASS。檢索層文件級 security trimming 上線就緒(DG4 Tier 1 上線先決達成)。
- **下一步 P2.3**:classification clearance(internal/restricted 比對 + restricted 文件流程,DG1)。

### Commits
- (kickoff)docs(planning): kickoff W90 P2 phase artifacts
- feat(api): P2.0 query endpoint KB-level guard
- feat(api): P2.1 index ACL schema + ingestion stamp
- feat(retrieval): P2.2a retrieval-layer ACL filter + threading + P2.2c trimming fixture
- (本 entry)chore(ops): P2.2b rebuild ops scripts + eval reports(north-star §15 PASS)

## Day 1 cont — 2026-06-24(P2.3 classification clearance,DG1)

### 用戶 2 決策(AskUserQuestion)
- **clearance 來源 = 由 workspace role 推導**(admin = restricted-cleared / 非 admin = internal)。
- **文件標記 = 完整閉環 admin-only `PATCH .../classification`**(merge-restamp 索引 + 持久化,無 re-ingest)。

### think-before-coding 關鍵 simplification(Karpathy §1.1/§1.2,plan changelog)
- clearance 由 role 推導且只有 admin = restricted-cleared,而 `principals_for_user(admin)` 已返 `None`(完全 bypass)→ **「principals 是 None」⟺「admin」⟺「restricted-cleared」**。classification clause **唔需要再 threading 第二個 `user_clearance` param 落 11 層** —— filter 側改動完全 self-contained(零 re-threading,surgical §1.3)。隱式 coupling 失敗模式 = over-restriction(fail-safe)非洩漏 → 可接受 + 強 docstring 標 P3 per-user clearance 須改 explicit。

### 實作(讀側 + 寫側)
- **讀側**:`_build_acl_filter` 非 None list append `(classification eq 'internal' or classification eq null)`;None 不加。`null` disjunct = production-preserve fail-open(未重建 KB classification null → internal 可見,對稱 `allowed_principals` 空集)。**零 11 層 re-threading**。
- **寫側(完整閉環)**:
  1. `kb_management/doc_classification_store.py`(新,Protocol + InMemory + Postgres `document_classifications` 表 + factory,mirror `doc_profile_store`,存單一 `str`,只記 exception = restricted)。
  2. `api/schemas/doc_classification.py`(`ClassificationUpdateRequest` Literal[internal/restricted] + `DocClassificationInfo`)。
  3. `IndexPopulator.update_doc_classification`(C03,mirror `delete_doc` search-then-merge,第二步 `@search.action: merge` 只更新 classification 欄位,無 re-ingest)。
  4. `PATCH /kb/{kb_id}/docs/{doc_id}/classification`(documents.py,`require_role("admin")` — security 控制 admin-only,P3 可放寬 KB manage)→ 持久化先(防 re-ingest race)→ merge-restamp 索引。
  5. `_run_ingest_pipeline` 讀持久化 classification → 傳 `orchestrator.ingest(classification=...)`:**restricted 文件 re-ingest/reindex/backfill 不退回 internal**(安全屬性)。
  6. server.py lifespan wire `app.state.doc_classification_store`。

### 測試 + 驗證
- 新測試:`test_doc_classification_store.py`(9 CRUD + factory)/ `test_doc_classification_route.py`(9:200 標記持久化+restamp / revert / 403 非 admin / 422 invalid / 404 doc / 404 KB / 403 archived / 503 無 store)/ `test_populate.py` 加 3(restamp merge / 0-match / index-missing fail-soft)/ `test_retrieval_acl_filter.py` 加 P2.3 clause 斷言 / `test_documents_route.py` 加 re-ingest 保留 restricted / `test_query_route_acl_trimming.py` 加 route 層 clearance 斷言。
- **針對性 pytest 96 passed**;**全套待綠**;ruff clean(我嘅檔全過;server.py 30 E402 = pre-existing 缺 noqa,非我引入,Karpathy §1.3 唔掂);mypy 改動 production 檔自身 0 error(transitive debt pre-existing)。

### Commits
- (本 entry)feat(api): P2.3 classification clearance filter + admin tag endpoint + persist
