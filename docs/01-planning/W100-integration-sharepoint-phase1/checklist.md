# W100 — checklist(integration-sharepoint-phase1)

> 每項對應 plan.md §2 deliverable。**F1 未開 — 全部待 approve 後逐項 tick。**

## F1 — `SourceConnector` interface + capability model + 資料模型

- [x] F1.1 `backend/integration/__init__.py` 建包
- [x] F1.2 `connector.py`:`ConnectorCapabilities`(auth_kind / supports_browse / supports_acl / supports_delta / acl_granularity)
- [x] F1.3 `connector.py`:`SourceConnector` Protocol(connect / browse / list_documents / fetch_document / get_principals / delta)+ `ConnectionHandle` 抽象
- [x] F1.4 `models.py`:`SourceContainer` / `SourceDocumentRef`(etag/version/last_modified/size)/ `SourceDocument` / `Principal`(kind+id)/ `DeltaResult`
- [x] F1.5 `pyproject.toml` `[tool.setuptools.packages.find]` include 加 `integration*`
- [x] F1.6 `tests/integration/test_capabilities.py`:capability 退化規則(§3.4)+ models + Protocol runtime-check(7 test)
- [x] F1.7 驗:`mypy --strict -p integration` clean + ruff clean + provider-agnostic(connector/models 零 SharePoint import)+ 7 passed

## F2 — Graph REST client(認證 + 分頁 + token refresh)

- [x] F2.1 `backend/integration/sharepoint/__init__.py` 建包
- [x] F2.2 `graph_client.py`:`build_credential`(`azure-identity` aio ClientSecret/Certificate,lazy import 對齊 entra_graph)+ `SharePointCredentials`(secret/cert 二擇一)
- [x] F2.3 `graph_client.py`:`GraphClient._request` `httpx.AsyncClient` + `tenacity` 429/5xx retry(4xx 非 429 propagate fatal)
- [x] F2.4 `graph_client.py`:`paged` `@odata.nextLink` async generator(params 只第一頁)+ `stream_to_file`(④)
- [x] F2.5 `GraphConnectionHandle` token refresh(委派 azure-identity 快取/續期,⑥)+ `aclose()`(加入 ConnectionHandle Protocol)
- [x] F2.6 `tests/integration/test_graph_client.py`:`httpx.MockTransport` 7 test(bearer 注入 / 分頁 / 429 retry / 5xx 耗盡 / 403 fatal / stream / cred 驗證)
- [x] F2.7 驗:credential / token 絕不 log(H5)+ ruff/mypy --strict/14 passed(7+7)

## F3 — SharePoint connector:connect / browse / list / fetch

- [x] F3.1 `connector.py`:`SharePointConnector` capability 宣告(§4.1 acl_granularity=document / supports_delta=False)
- [x] F3.2 `connect`(`build_credential` → `GraphConnectionHandle`)+ `aclose`(close owned http)+ `resolve_site`(UI step1 URL→site container)
- [x] F3.3 `browse`(container-id 前綴編碼 site→drive→folder,分頁 AsyncIterator,folder-only;§4.3)
- [x] F3.4 `list_documents`(driveItem file-only + eTag/cTag/lastModified/size 映射 SourceDocumentRef,§4.4)
- [x] F3.5 `fetch_document`(`stream_to_file` 落 NamedTemporaryFile + suffix;抓完即清 = caller 責任 §7.2)
- [x] F3.6 `tests/integration/test_sharepoint_connector.py` 9 test:browse 三層 / list file-only / fetch-to-temp / resolve_site / delta-resync / capabilities
- [x] F3.7 驗:分頁 + folder/file 分流 + change-detection 欄 + ruff/mypy/23 passed(完整 SourceConnector conformance 留 F4 — get_principals 後)

## F4 — `get_principals` 權限映射(ACL → allowed_principals)

- [x] F4.1 `permissions.py`:`resolve_principals` 抽 grantedToV2 + grantedToIdentitiesV2(user/group/siteGroup)+ link facet
- [x] F4.2 `_expand_group_to_group_level`:`transitiveMembers` 展平 nested group **到 group 級**(§5.3,`@odata.type` endswith group;skip user)
- [x] F4.3 特殊 principal(§5.4:Anyone anonymous=drop default(D-2)/ public sentinel / reject · organization→`org::{tenant}` · siteGroup→external_group · specific-people→identities)
- [x] F4.4 防爆量 cap `MAX_PRINCIPALS_PER_FILE=2049`(§5.5,超額 log `acl_principal_cap_hit` + truncate)
- [x] F4.5 抽唔到 ACL **唔 fail-open**:permission fetch 失敗 → `AclResolutionError`(propagate);空集 = 「無可解析 principal」非 public(docstring + F5 enforce)
- [x] F4.6 `tests/integration/test_sharepoint_permissions.py` 12 test(user/group-nested/anyone drop·reject·public/org/siteGroup/specific-people/cap/fetch-fail/full conformance/connector get_principals)
- [x] F4.7 驗:group 級 set + Anyone drop + 完整 SourceConnector conformance(靜態 `_assert_conforms` + runtime isinstance)+ ruff/mypy/35 passed

## F5 — import service(ingestion 薄銜接 + per-doc 錯誤模型 + summary)

- [x] F5.1 `import_service.py`:`import_documents` per-container `list_documents` → per-doc `_import_one`(provider-agnostic,零 SharePoint import)
- [x] F5.2 per-doc:`get_principals` → `fetch_document` → **注入式 `IngestCallable` seam**(production F6 adapter 寫 doc ACL → 既有 `_run_ingest_pipeline` 經 5.2 override pick up,核心零改動)
- [x] F5.3 fatal(connect/auth)喺 `connect()` 前置 propagate;per-container list 失敗記 + 續;per-doc fetch/ACL/ingest 失敗 skip + 記(§8.1 ⑦)
- [x] F5.4 per-doc summary `DocImportResult{doc_id,name,status,error?}` + `ImportSummary` total/succeeded/failed(§8.2 ADR-0043)
- [x] F5.5 `tests/integration/test_import_service.py` 6 test(happy 2-doc+ACL flow / 空 ACL 拒 / fetch 失敗 per-doc / ingest 失敗+temp 清 / container 失敗 per-container / 真 connector 端到端 G1+G2)
- [x] F5.6 驗:**ingestion 核心 git diff = 零**(全程未碰 `backend/ingestion/`)+ temp 抓完即清(§8.5)+ 空集≠public(F4.5 enforce)+ ruff/mypy/41 passed

## F6 — thin API route + Phase Gate

- [ ] F6.1 `api/routes/integration.py`:`POST /integration/sharepoint/import`(+ browse/list 如需)wire import_service
- [ ] F6.2 RBAC 守衛 `require_role(admin, editor)`(對齊 W88 寫端點)
- [ ] F6.3 register router(`api/server.py` 或 router aggregator)
- [ ] F6.4 `tests/integration/test_integration_route.py`:route + RBAC 守衛(mock import_service)
- [ ] F6.5 **G-W100 Gate**:full pytest 綠 + ruff clean + `mypy --strict` clean + ingestion diff=零 + H6 coverage 新 module
- [ ] F6.6 doc-sync:progress retro + BACKLOG B-01 → `完成`(backend 部分)+ memory append + PROGRESS tracker
