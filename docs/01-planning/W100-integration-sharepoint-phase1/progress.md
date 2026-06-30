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

**Commits**:見下方 F3 commit hash。

---

<!-- Day N entries append below as F-items land -->

