# W100 — checklist(integration-sharepoint-phase1)

> 每項對應 plan.md §2 deliverable。**F1 未開 — 全部待 approve 後逐項 tick。**

## F1 — `SourceConnector` interface + capability model + 資料模型

- [ ] F1.1 `backend/integration/__init__.py` 建包
- [ ] F1.2 `connector.py`:`ConnectorCapabilities`(auth_kind / supports_browse / supports_acl / supports_delta / acl_granularity)
- [ ] F1.3 `connector.py`:`SourceConnector` Protocol(connect / browse / list_documents / fetch_document / get_principals / delta)+ `ConnectionHandle` 抽象
- [ ] F1.4 `models.py`:`SourceContainer` / `SourceDocumentRef`(etag/version/last_modified/size)/ `SourceDocument` / `Principal`(kind+entra_guid)/ `DeltaResult`
- [ ] F1.5 `pyproject.toml` `[tool.setuptools.packages.find]` include 加 `integration*`
- [ ] F1.6 `tests/integration/test_capabilities.py`:capability 退化規則(§3.4)
- [ ] F1.7 驗:`mypy --strict` clean + ruff clean + provider-agnostic(connector/models 零 SharePoint import)

## F2 — Graph REST client(認證 + 分頁 + token refresh)

- [ ] F2.1 `backend/integration/sharepoint/__init__.py` 建包
- [ ] F2.2 `graph_client.py`:app-only token(`azure-identity` ClientSecret/Certificate credential)
- [ ] F2.3 `graph_client.py`:`httpx.AsyncClient` GET/POST 封裝 + 429/5xx retry(`tenacity`)
- [ ] F2.4 `graph_client.py`:`@odata.nextLink` 分頁 async generator
- [ ] F2.5 `ConnectionHandle` 封裝 token refresh(過期自動續,呼叫方唔理)
- [ ] F2.6 `tests/integration/test_graph_client.py`:`httpx.MockTransport` 分頁 + token refresh + retry(無新 dep)
- [ ] F2.7 驗:credential 絕不 log(H5)+ 測試綠

## F3 — SharePoint connector:connect / browse / list / fetch

- [ ] F3.1 `connector.py`:`SharePointConnector` capability 宣告(§4.1 acl_granularity=document / supports_delta=False)
- [ ] F3.2 `connect`(app-only token + ConnectionHandle)
- [ ] F3.3 `browse`(site→drive→folder,分頁 AsyncIterator,§4.3)
- [ ] F3.4 `list_documents`(driveItem + eTag/cTag/lastModified/size 映射 SourceDocumentRef,§4.4)
- [ ] F3.5 `fetch_document`(stream 落 temp file + 抓完即清,§4.5)
- [ ] F3.6 `tests/integration/test_sharepoint_connector.py`:mock browse 樹 / list 分頁 / fetch-to-temp
- [ ] F3.7 驗:分頁 + temp 清理 + change-detection 欄 + 測試綠

## F4 — `get_principals` 權限映射(ACL → allowed_principals)

- [ ] F4.1 `permissions.py`:`/permissions` 抽 grantedToIdentitiesV2(user)+ group identity
- [ ] F4.2 `transitiveMembers` 展平 nested group **到 group 級**(§5.3,唔展 user 級)
- [ ] F4.3 特殊 principal 規則(§5.4:Anyone=drop default / Org-link / 非 Entra group)
- [ ] F4.4 防爆量 cap < 2,049 / file(§5.5,超額 log warning + truncate / 退化)
- [ ] F4.5 抽唔到 ACL **唔默默 fail-open public**(記 per-doc 失敗或退化 KB 層 — §6 risk)
- [ ] F4.6 `tests/integration/test_sharepoint_permissions.py`:每個特殊 case + nested flatten + over-limit + 抽唔到 ACL
- [ ] F4.7 驗:回 group 級 set + Anyone drop + 測試綠

## F5 — import service(ingestion 薄銜接 + per-doc 錯誤模型 + summary)

- [ ] F5.1 `import_service.py`:browse-selection → list → per-doc fetch
- [ ] F5.2 per-doc:fetch → **既有 ingestion 入口**(orchestrator `ingest()` 帶 `allowed_principals` + `classification`)→ 收集 result
- [ ] F5.3 fatal(auth / per-site 無權)停 batch;per-doc(單文件 fetch/parse/ACL 失敗)skip + 記(§8.1)
- [ ] F5.4 per-doc summary `{doc_id, name, status, error?}`(§8.2 對齊 ADR-0043)
- [ ] F5.5 `tests/integration/test_import_service.py`:per-doc 失敗唔 abort + allowed_principals 端到端 + fatal 停 batch
- [ ] F5.6 驗:**ingestion 核心 git diff = 零**(§7.2 鐵律)+ 測試綠

## F6 — thin API route + Phase Gate

- [ ] F6.1 `api/routes/integration.py`:`POST /integration/sharepoint/import`(+ browse/list 如需)wire import_service
- [ ] F6.2 RBAC 守衛 `require_role(admin, editor)`(對齊 W88 寫端點)
- [ ] F6.3 register router(`api/server.py` 或 router aggregator)
- [ ] F6.4 `tests/integration/test_integration_route.py`:route + RBAC 守衛(mock import_service)
- [ ] F6.5 **G-W100 Gate**:full pytest 綠 + ruff clean + `mypy --strict` clean + ingestion diff=零 + H6 coverage 新 module
- [ ] F6.6 doc-sync:progress retro + BACKLOG B-01 → `完成`(backend 部分)+ memory append + PROGRESS tracker
