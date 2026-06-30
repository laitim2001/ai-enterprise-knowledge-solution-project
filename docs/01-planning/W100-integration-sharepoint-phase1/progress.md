# W100 — progress(integration-sharepoint-phase1)

> Daily progress + decisions + commits + 結尾 retro。Plan: [`plan.md`](./plan.md) · Checklist: [`checklist.md`](./checklist.md)

---

## Day 0 — 2026-06-30(kickoff proposal,F1 code 未開)

**Context**:用戶 2026-06-30 講「可以開始 ADR-0070 階段 1 落 code」。依 §10 R1(無 plan 唔可以 implement)+ [[feedback_change_spec_approval_gate]](先 propose spec/plan,STOP 等 approve,先 code)→ 先寫 plan 三件套,**proposed 狀態,未落 code**。

**Gate 評估(開工前查證,Karpathy §1.1)**:
1. **H2 新 dependency** → 藍圖 §2.5 揀 `azure-identity` + `httpx` managed-REST(避 `msgraph-sdk`)。核 `backend/pyproject.toml`:`httpx>=0.27`(L17)+ `azure-identity>=1.20`(L23)**已存在** → **無新 dep,H2 唔 trigger**。§9.3 dep 逐項確認完成。
2. **B1 前置**(`allowed_principals` index 欄 + ingest stamp + query filter)→ grep 證 16 檔已 wire:`indexing/schema.json` + `schemas.py` 有欄、`orchestrator.ingest()` L139/331 已收 + 逐 chunk stamp(W90 P2.1 / ADR-0066)、`retrieval/hybrid.py` + `api/middleware/acl.py` query filter。→ **B1 已 ship**,connector 只需「填內容」。
3. **H1** → C17 已喺 architecture.md §3.3/§4.1 + COMPONENT_CATALOG 登記(`884b149`,ADR-0070 Accepted)→ 建 `backend/integration/` = 實作已批 component,**非新架構決定,H1 唔 trigger**。
4. **D4 reframe** → SharePoint/Graph live 要真 tenant + `Sites.Selected`,本機造唔到 → 本 phase 落 connector code + **mock Graph 回應**單元測試;live 驗證(藍圖 §10 階段 D)留 runbook 畀公司執行,**唔計入 G-W100**。

**產出(Day 0)**:`plan.md` + `checklist.md` + `progress.md`(本檔)三件套,status = proposed。

**待用戶決定(STOP gate)**:
- (a) approve plan(F1–F6 scope + G-W100 = mock 測試 + 靜態檢查,不含 live)
- (b) 確認 §4 D-2 **Anyone-link 政策 = drop**(security-relevant default)
- (c) frontend wizard(H7 重現 `integration-import/` 4 surface)時機 — F6 後即做 / 抑或留階段 1b(plan §5 建議留 1b,因 API 對唔到真 tenant 前屬 speculative)

**Next**:approve 後 → F1.1(`backend/integration/__init__.py` + Protocol + capability model + 資料模型)。**未 approve 前唔開 code。**

**Commits**:_(Day 0 plan 三件套 = `docs(planning):` housekeeping,R2 例外)_

---

## Day 1 — 2026-06-30(approve + F1 落地)

**用戶 approve(AskUserQuestion)**:D-2 Anyone-link = **drop**(推薦)· frontend wizard 留 **階段 1b**(backend 先)。→ plan status proposed→active,§9.3 default 鎖好。

**F1 — `SourceConnector` interface + capability model + 資料模型 → 完成,G 綠**:
- `backend/integration/__init__.py`(C17 包說明)
- `backend/integration/models.py`:`Principal`(kind+id,id=allowed_principals 字串)/ `SourceContainer` / `SourceDocumentRef`(③ etag/version/last_modified/size)/ `SourceDocument`(④ content_path temp)/ `DeltaResult`(⑤ 保留)
- `backend/integration/connector.py`:`ConnectorCapabilities` + `ConnectionHandle` Protocol(⑥ token refresh)+ `SourceConnector` Protocol 6 method + `resolve_behaviour`(§3.4 退化:manual/auto · kb_fallback/document_trimming · tree/manual_id)
- `pyproject.toml` packages.find 加 `integration*`
- `tests/integration/test_capabilities.py` 7 test(退化規則 4 case + models + Protocol runtime-check)

**驗證**:ruff `All checks passed` · `mypy --strict -p integration` `Success: no issues found in 3 source files`(註:path mode 撞 `backend.integration` 雙名 → 用 `-p` module mode)· pytest `7 passed`。

**決定 / 偏離藍圖草案(R3)**:
- D-1:credentials 入 concrete connector `__init__`,**非** `connect()` 參數 — 避 Protocol method-param contravariance 破壞 structural conformance + 對齊 EKP store 構造 pattern(cheap sync 構造 / async network connect)。
- `browse`/`list_documents` = async generator → 宣告 `def -> AsyncIterator[...]`(非 `async def`)。
- `SourceDocument` 唔 carry `allowed_principals`:ACL 由 `get_principals` 單一職責方法出(解藍圖 §3.2 method vs §3.5 欄位草案不一致)。
- provider-agnostic 守住:`connector.py` / `models.py` **零 SharePoint / Graph import**。

**Next**:F2 — Graph REST client(`azure-identity` app-only token + `httpx` + `@odata.nextLink` 分頁 + `ConnectionHandle` token refresh + `tenacity` 429/5xx retry),mock via `httpx.MockTransport`。

**Commits**:`67f4f14` feat(integration): F1 SourceConnector interface + capability model。

---

## Day 1(續)— 2026-06-30(F2 Graph REST client)

**先例確認**:`backend/api/auth/entra_graph.py` 已記「F1 D1 — managed-REST over `msgraph-sdk`:azure-identity + httpx,zero new dep / H2 / R8(ADR-0017)」+ `azure.identity.aio` `get_token(_GRAPH_SCOPE)` + `@odata.nextLink` loop + `credential.close()` → 印證 H2 分析 + 對齊既有可行 pattern。

**F2 — Graph REST client → 完成,綠**:
- `backend/integration/sharepoint/__init__.py`(包說明)
- `backend/integration/sharepoint/graph_client.py`:`SharePointCredentials`(secret/cert)+ `build_credential`(lazy `azure.identity.aio`,cast 解耦 azure get_token 簽名)+ `GraphConnectionHandle`(token 委派 azure 快取/續期 ⑥ + `aclose`)+ `GraphClient`(`_request` tenacity 429/5xx retry · `get_json` · `paged` `@odata.nextLink` async generator · `stream_to_file` ④)+ `GRAPH_BASE/SCOPE` 常數
- `integration/connector.py`:`ConnectionHandle` Protocol 加 `aclose()`(handle = network resource,caller batch 完 close)
- `tests/integration/test_graph_client.py` 7 test(`httpx.MockTransport` + fake handle)

**驗證**:ruff `All checks passed` · `mypy --strict -p integration` `Success: 5 source files` · pytest `14 passed`(7 F1 + 7 F2)。

**決定**:
- testable seam — `GraphClient` 只依賴 `ConnectionHandle` + `httpx.AsyncClient` → 測試注入 fake handle + MockTransport,**azure-identity 永不喺 mock 測試觸及**(D4);`build_credential`/`GraphConnectionHandle` 留 runbook live 行。
- retry seam injectable(`max_attempts`/`backoff_base`)→ 測試零 backoff 快跑;429+5xx retry,非 429 4xx(如 403 缺 per-site grant §1.3)即 propagate fatal(§8.1)。
- H5:`_auth_headers` 明註不 log;無 token/secret 落 log。

**Next**:F3 — `SharePointConnector`(capability 宣告 §4.1 + connect/browse/list_documents/fetch_document),sit 喺 GraphClient 上。

**Commits**:`abfaf1e` feat(integration): F2 Microsoft Graph REST client。

---

## Day 1(續)— 2026-06-30(F3 SharePoint connect/browse/list/fetch)

**F3 — `SharePointConnector` → 完成,綠**:
- `backend/integration/sharepoint/connector.py`:capability §4.1 + `connect`(build_credential→GraphConnectionHandle)+ `aclose` + `resolve_site`(UI step1 URL→site)+ `browse`(container-id 前綴 `site::`/`drive::`/`folder::` 一個 method 行全樹,folder-only)+ `list_documents`(file-only,ref 帶 ③ eTag/cTag/lastModified/size)+ `fetch_document`(stream 落 NamedTemporaryFile)+ `delta`(resync_required)
- `tests/integration/test_sharepoint_connector.py` 9 test

**驗證**:ruff clean · `mypy --strict -p integration` 6 files clean · pytest `23 passed`(7+7+9)。

**決定 / 教訓**:
- container-id 前綴編碼(`<kind>::<native-id>[::<item>]`)令單一 `browse` walk 全樹;`SourceDocumentRef.container_id` 保留 → `fetch_document` 由此 recover drive_id,零額外 state。
- `browse` folder-only / `list_documents` file-only(driveItem `folder`/`file` facet 分流)。
- **教訓**:F3 test 原本斷言 `isinstance(c, SourceConnector)` runtime 失敗(`get_principals` 未做,F4 先有)→ 正確訊號。`mypy -p integration` 唔檢 `tests/`(唔同 package)所以冇 catch;**完整 SourceConnector conformance 斷言移去 F4**,F3 只驗 capabilities。
- http lifecycle:connector 自有 AsyncClient(injected = caller-owned 不 close;自建 = `aclose` 關)。

**Next**:F4 — `get_principals` 權限映射(`permissions.py`:`/permissions` → transitiveMembers 展 group 級 + Anyone-link drop(D-2)+ 防爆量 cap)+ 補完 SourceConnector conformance。

**Commits**:`bfa1d34` feat(integration): F3 SharePoint connect/browse/list/fetch。

---

## Day 1(續)— 2026-06-30(F4 ACL → allowed_principals 權限映射)

**F4 — `get_principals` 權限映射 → 完成,綠(security-critical)**:
- `backend/integration/sharepoint/permissions.py`:`resolve_principals`(`/permissions` 分頁 → 各 grant)+ `_identity_set_principals`(user/group/siteGroup)+ `_expand_group_to_group_level`(`transitiveMembers` 展 nested group **到 group 級** ①,skip user)+ `AnyonePolicy` Literal(drop/public/reject)+ `MAX_PRINCIPALS_PER_FILE=2049` 防爆量(§5.5)+ `AclResolutionError`(fetch 失敗 / reject → 拋,**唔 fail-open** §6)
- `connector.py`:`get_principals` wire `resolve_principals`(`anyone_policy` 入 `__init__`,default drop D-2)+ `TYPE_CHECKING` `_assert_conforms` 靜態 SourceConnector conformance
- `tests/integration/test_sharepoint_permissions.py` 12 test

**驗證**:ruff clean · `mypy --strict -p integration` 7 files clean · pytest `35 passed`(7+7+9+12)。

**決定 / 教訓**:
- **D-2 Anyone-link=drop**:anonymous link 預設唔索引(映射唔到 Entra principal);policy=public 出 `PUBLIC_PRINCIPAL` sentinel(註:真 grant everyone 需 query 側注入,follow-up,default drop 唔行此路);policy=reject 拋 `AclResolutionError`。
- **group 級展開**(①):`transitiveMembers` 只收 `@odata.type` endswith `group`(nested group),**skip user members** → 零 re-ingest on membership 變,同 ADR-0067 一致。
- **空集 ≠ public**(§6 risk F4.5):fetch 失敗拋 `AclResolutionError`;成功但全 drop → 回 `[]`,F5 必須拒當 public(下一步 enforce)。
- **conformance**:`get_principals` 補齊 → SharePointConnector 完整 6 method;靜態(`_assert_conforms` TYPE_CHECKING)+ runtime(`isinstance`)雙重鎖。

**Next**:F5 — `import_service`(browse-selection → list → per-doc fetch → 既有 ingestion 入口帶 `allowed_principals` → per-doc summary;空 ACL 拒 fail-open;fatal vs per-doc §8.1)。**ingestion 核心零改動驗證**(§7.2 鐵律)。

**Commits**:`0499f2d` feat(integration): F4 SharePoint ACL -> allowed_principals mapping。

---

## Day 1(續)— 2026-06-30(F5 import service)

**先查**:既有單檔 ingestion 入口 = `api/routes/documents.py:_run_ingest_pipeline`(收 `UploadFile` + 內部自行 `resolve_doc_principals` 解 allowed_principals,**唔收外部值**)。

**F5 — `import_service` → 完成,綠**:
- `backend/integration/import_service.py`:`import_documents`(per-container `list_documents` → per-doc `_import_one`)+ `DocImportResult` / `ImportSummary`(§8.2)+ `IngestCallable` Protocol(注入式 ingestion seam)+ `default_doc_id`(`sp-{item}` 穩定 id → re-import replace-in-place §8.3)
- `tests/integration/test_import_service.py` 6 test(fake connector 可控 + 真 SharePointConnector 端到端 ACL flow)

**驗證**:ruff clean · `mypy --strict -p integration` 8 files clean · pytest `41 passed`(35+6)· **`backend/ingestion/` git diff = 零**(§7.2 鐵律守住)。

**關鍵設計決定**:
- **零核心改動達成法**:import_service 用注入式 `IngestCallable`,**唔 import sharepoint / 唔改 ingestion**;production wiring(F6)再寫 doc-level ACL rows → 既有 `_run_ingest_pipeline` 經 `resolve_doc_principals`(5.2 doc override)自然 pick up SharePoint principals → ingestion 核心 + Docling pipeline 完全不動。
- **空集 ≠ public enforce(§6/F4.5)**:`acl_granularity=="document"` 且 principals 空 → 記 `acl_empty` failed,**唔 ingest**(防 empty stamp 經 P2.2 filter fail-open 變 public)。
- **per-doc 韌性(⑦)**:`_import_one` 永不拋;fetch/ACL/ingest 失敗各記 + 續;container list 失敗 per-container 記 + 續;temp 抓完 finally 即清(§8.5),ingest 失敗都清。
- **provider-agnostic**:只 import `integration.connector`/`integration.models`,零 SharePoint 耦合 → 階段 2 provider reuse。

**Next**:F6 — thin API route(`POST /integration/sharepoint/import`,RBAC `require_role(admin,editor)`)+ production ingest adapter(doc ACL write → `_run_ingest_pipeline`)+ **G-W100 Gate**(full pytest + ruff + mypy --strict + ingestion diff=零)。

**Commits**:`08ce773` feat(integration): F5 import service。

---

## Day 1(續)— 2026-06-30(F6 API route + production adapter + Gate)

**先查**:`acl.py` 確認 principal 字串格式一致(`resolve_doc_principals` / `principals_for_user` 都係 raw GUID 字串比對)→ connector stamp raw Entra GUID 同 query filter match,「同一條路兩段」成立。`doc_acl_store.add` + `_run_ingest_pipeline`(documents.py:820,讀 `deps.doc_acl_store`)= adapter 落點。

**F6 — API route + production adapter → 完成,綠**:
- `backend/api/routes/integration.py`:`POST /integration/sharepoint/import`(`SharePointImportRequest`/`ImportSummaryOut`)+ `require_role(admin,editor)` self-gated + body-aware `assert_kb_access(kb_id, edit)` + `_sharepoint_credentials_or_503` + **`make_pipeline_ingest` production adapter**(寫 doc ACL rows → wrap temp file 做 `UploadFile` → 既有 `_run_ingest_pipeline`,**ingestion 核心零改動**)
- `backend/storage/settings.py`:SharePoint 配置欄位(`sharepoint_tenant_id`/`_client_id`/`_client_secret`/`_certificate_path`/`_anyone_policy`,空 → route 503 not-configured)
- `backend/api/server.py`:import `integration` + `include_router`(self-gated 無 `_auth`)
- `tests/api/test_integration_route.py` 8 test

**驗證**:ruff clean(我嘅檔;server.py 36 E402 = pre-existing app-bootstrap,我 4 行 edit 零新增)· `mypy --strict -p integration` 8 files clean · route module mypy(`--follow-imports=silent`)· F6 route 8 passed · **`backend/ingestion/` git diff = 零**(§7.2 鐵律)。

**關鍵決定 / 教訓**:
- **settings 必須 `Depends(get_settings)` 注入**(非 route body 直接 `get_settings()`)否則 `dependency_overrides` 唔生效(happy-path test 一度 503 → 改 Depends 修)。
- **adapter doc-ACL-then-pipeline**:把 SharePoint principals 寫 `doc_acl_store` → 既有 pipeline 經 `resolve_doc_principals` 5.2 override stamp → 核心 + Docling 零改動;`doc_acl_store` 未 wire → adapter raise(防 fail-open 退化 KB 繼承)。
- **principal_type bookkeeping-only**:retrieval match 純 `principal_id` 字串(`resolve_doc_principals` 忽略 type)→ 統一寫 "group" 功能正確;user/group(Entra)端到端 work,external_group/org/public 屬 follow-up(query 側注入,default drop 唔行此路)。
- **D4**:live(真 SharePoint + ingestion + Azure index)本機驗唔到 → route/RBAC/schema/summary/adapter 結構用 mock 測;real path 留 runbook §10 階段 C/D。

**G-W100 Gate**:**PASS(附 full-suite-env caveat)**。
- ✅ 新測試全綠:integration package 41 + route 8 = **49 passed**;RBAC 鄰近回歸 `test_kb_route_acl` 21 passed(共 70 passed 24.5s)。
- ✅ ruff clean(我嘅檔全部;`server.py` 36 E402 = pre-existing app-bootstrap,我 4 行 edit 零新增)。
- ✅ `mypy --strict -p integration`(8 files)clean + route module `mypy --strict --follow-imports=silent -m api.routes.integration` `Success: no issues found in 1 source file`。
- ✅ `import api.server` OK,`/integration` route 註冊成功(1 條)。
- ✅ **`backend/ingestion/` git diff = 零**(§7.2 鐵律全 phase 守住)。
- ⚠️ **full repo pytest 跑唔完(caveat)**:背景全套跑到 ~12%(hang 前 ~216 test 全綠 dots)卡喺一個**網絡綁定測試**(reach 緊外部服務無 timeout,3060s wall / 49 CPU-s = idle hang)→ 殺咗。屬 EKP 既有 env 限制(R8 corp-proxy / CLOSE_WAIT,非本 phase 引入:hang 前全綠 + 本 phase 改動全屬新增 module + 1 settings 欄 + router 註冊,additive/局部)。`pytest-timeout` 未裝(裝撞 R8)→ 改針對性 Gate 已足夠覆蓋本 phase surface。同 EKP「smoke-user-deferred」caveat 同類。

**Live 驗證(D4)**:真 SharePoint + ingestion + Azure index 端到端留藍圖 §10 階段 C/D runbook 畀公司真 tenant 執行,**不計入 G-W100**。

**Commits**:見下方 F6 commit hash。

---

## Retrospective(W100 closeout 2026-06-30)

**達成**:ADR-0070 階段 1 backend 垂直切片完整落地 —— C17 `SourceConnector` 抽象層 + SharePoint concrete connector(connect/browse/list/fetch/get_principals)+ 權限映射(transitiveMembers group 級 + Anyone-drop + 防爆量)+ import service(per-doc 錯誤模型)+ thin API route(RBAC 守衛)+ production ingest adapter(doc ACL → 既有 pipeline,核心零改動)。**49 新測試**,ruff/mypy clean,ingestion 核心零改動。

**Gate 評估的價值**(Karpathy §1.1 think-before):開工前查證令兩個原以為會卡嘅 gate 清空 —— H2 無新 dep(`azure-identity`+`httpx` 已存在,對齊 `entra_graph.py` 先例)+ B1(`allowed_principals` plumbing)已 ship(W90 P2.1)。慳返大量 re-work。

**教訓**:
1. **Protocol 設計 lock-in**(D-1):credentials 入 `__init__` 而非 `connect()` 參數,避 method-param contravariance 破 structural conformance — 概念草案(藍圖 §3.2)落實作要修。
2. **mypy `-p` module mode**:repo 根 path 撞 `backend.X` vs `X` 雙名 → 用 `-p`/`-m` module mode,唔用 path mode。
3. **`Depends(get_settings)` 注入**:route body 直接 `get_settings()` 繞過 `dependency_overrides`,test override 唔生效。
4. **空集 ≠ public**(§6/F4.5):document-ACL connector 抽唔到 principal 唔可 fail-open 當 public,要記 per-doc 失敗。
5. **full-suite env hang**:EKP 全套測試有網絡綁定測試會 idle-hang(wall ≫ CPU 係診斷信號),針對性 Gate + caveat 係務實做法。

**carry-over**:
- **階段 1b**:前端匯入 wizard(H7 100% 重現 `references/design-mockups/integration-import/` 4 surface)— 等真 tenant 驗證將近或用戶 explicit kickoff。
- **Live 驗證**:藍圖 §10 階段 C/D runbook,公司真 tenant 執行。
- **follow-up**:org-link / Anyone-public / external_group principal 端到端(需 query 側 inject org/public token;default drop 唔行此路)。

**G-W100 PASS WITH FULL-SUITE-ENV + LIVE-DEFERRED CAVEAT。W100 closed 2026-06-30。**

---

<!-- Day N entries append below as F-items land -->

