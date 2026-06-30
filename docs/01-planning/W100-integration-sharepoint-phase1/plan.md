# W100 — 統一整合層階段 1:SharePoint 按需匯入(backend 實作)

| 項目 | 值 |
|---|---|
| Phase | W100-integration-sharepoint-phase1(ADR-0070 / C17 Source Abstraction Framework 第一個 concrete connector)|
| Status | **proposed — 待用戶 approve**(per [[feedback_change_spec_approval_gate]];plan committed 但 **F1 code 未開**,等用戶 go)|
| Tier | Tier 1.5(NET NEW backend module `backend/integration/`,已喺 architecture.md §3.3/§4.1 + COMPONENT_CATALOG C17 登記 = ADR-0070 Accepted 授權範圍;非新架構決定)|
| 依賴 | **已清**:① H2 無新 dep(`azure-identity>=1.20` + `httpx>=0.27` 已喺 `pyproject.toml`,藍圖 §2.5 managed-REST 路線)② B1 前置(`allowed_principals` index 欄 + ingest stamp + query filter)已 ship(W90 P2.1 / ADR-0066,grep 證 `orchestrator.ingest()` line 139/331 已收 + stamp)|
| 錨點 | 方案藍圖 `docs/09-analysis/integration_layer_phase1_sharepoint_solution.md`(§0–10 + 附錄)· ADR-0070(Accepted)· 2 份 deep-research · COMPONENT_CATALOG C17 · UI design-stage mockup `references/design-mockups/integration-import/` · BACKLOG B-01 |
| 粗估 | 中-大(6 deliverable;F1-F4 純 backend connector + mock 測試;F5 ingestion 薄銜接;F6 API route + Gate)|

> **H1 / H2 gating**:本 phase **唔加新架構決定、唔加新 vendor**。
> - **H1**:C17 已喺 architecture.md §3.3/§4.1 + COMPONENT_CATALOG 登記(`884b149`,ADR-0070 Accepted),建 `backend/integration/` 係**實作呢個已批 component**,非新架構決定 → H1 唔 trigger。
> - **H2**:藍圖 §2.5 / §4.2 揀 `azure-identity` + `httpx` managed-REST(對齊 C16「managed-REST > heavy SDK」),避開 `msgraph-sdk`。兩個 dep 已喺 stack(`pyproject.toml` line 17/23)→ **無新 dependency**,H2 唔 trigger。§9.3 逐項確認 = 完成(無 dep 要批)。
> - **D4 reframe**:SharePoint / Graph live 驗證要真 tenant + `Sites.Selected` per-site grant,**本機造唔到** → 本 phase 落「connector code + mock Graph 回應單元測試」;**對住真 tenant 嘅 live 驗證留藍圖 §10 階段 D runbook 畀公司執行**,本 phase 唔假裝 live-test。

## §1 目標(Why)

令 EKP 唔再只靠人手上傳,而係可以接 SharePoint:揀 site / library / folder → 把文件 **+ 原生權限** 拉入 KB → 經自家 Docling ingestion(圖文還原 / profile / 可調配置**全保留**)→ 檢索時尊重來源權限(冇權限嘅人查唔到)。

**設計鐵律(藍圖 §0.4)**:connector 只負責「來源 → 標準化文件 + 權限 + metadata」,**絕對唔掂 ingestion 核心**。換來源 = 換 adapter,Docling pipeline 零改動。

**北極星(§15)**:connector-sourced 文件行**同一條** Docling pipeline,圖文還原度應同人手上傳一致(對 W43–85 baseline;此項屬 live 驗證 D1,留 runbook)。

## §2 Deliverables(F1–F6)

| # | Deliverable | 檔案(新建) | Acceptance |
|---|---|---|---|
| **F1** | `SourceConnector` interface + capability model + 資料模型(provider-agnostic 抽象層)| `backend/integration/__init__.py` · `connector.py`(`SourceConnector` Protocol 6 method + `ConnectorCapabilities` + `ConnectionHandle`)· `models.py`(`SourceContainer` / `SourceDocumentRef` 帶 etag/version/last_modified/size · `SourceDocument` · `Principal` · `DeltaResult`)· `pyproject.toml` 加 `integration*` package | `mypy --strict` clean;`connector.py`/`models.py` **零 SharePoint import**(provider-agnostic);capability 退化規則(§3.4)單元測試;ruff clean |
| **F2** | Graph REST client(認證 + 分頁 + token refresh)| `backend/integration/sharepoint/__init__.py` · `graph_client.py`(app-only token via `azure-identity` `ClientSecretCredential`/`CertificateCredential` · `httpx.AsyncClient` · `@odata.nextLink` 分頁 async generator · `ConnectionHandle` 封裝 token refresh · 429/5xx retry via `tenacity`)| 分頁跨頁 yield;token 過期自動續;mock via `httpx.MockTransport`(**無新 dep**)測試綠;credential 絕不 log(H5)|
| **F3** | SharePoint connector:`connect`/`browse`/`list_documents`/`fetch_document` | `backend/integration/sharepoint/connector.py`(`SharePointConnector(SourceConnector)`:capability 宣告 §4.1 · browse site→drive→folder §4.3 · list_documents driveItem + eTag/cTag/size §4.4 · fetch_document stream 落 temp §4.5)| browse/list 分頁;fetch stream 落 temp + 抓完即清;ref 帶 change-detection 欄;mock Graph 測試綠 |
| **F4** | `get_principals` 權限映射(ACL → `allowed_principals`)| `backend/integration/sharepoint/permissions.py`(`/permissions` 抽 grantedToIdentitiesV2 + group · `transitiveMembers` 展平**到 group 級** §5.3 · 特殊 principal §5.4 · 防爆量 cap §5.5)| 回 group 級 principal set(**唔展 user 級**);Anyone-link default **drop**;over-limit log warning + cap <2049;每個特殊 principal case 單元測試 |
| **F5** | import service(ingestion 薄銜接 + per-doc 錯誤模型 + summary)| `backend/integration/import_service.py`(browse-selection → list → per-doc fetch → **既有 ingestion 入口**(orchestrator `ingest()` 已收 `allowed_principals`)→ 收集 result · fatal vs per-doc §8.1 · per-doc summary §8.2 對齊 ADR-0043)| per-doc 失敗唔 abort batch;`allowed_principals` 端到端入 ChunkRecord;fatal(auth)停 batch;**ingestion 核心零改動**(§7.2 鐵律)驗證;測試綠 |
| **F6** | thin API route + Phase Gate | `backend/api/routes/integration.py`(`POST /integration/sharepoint/import` 等,wire import_service,RBAC 守衛 `require_role(admin,editor)` 對齊 W88 寫端點)+ register router | route callable + RBAC 守衛;full pytest + ruff + `mypy --strict` clean;新 module H6 coverage |

## §3 Phase Gate

- **G-W100**:F1–F6 全完成 + **full pytest 綠**(含新 mock 測試)+ ruff clean + `mypy --strict` clean + 新 connector/permission/import module H6 coverage + ingestion 核心 diff = 零(鐵律 §7.2,git diff `backend/ingestion/` 驗證,只 `orchestrator.ingest()` 既有 `allowed_principals` 參數,無新改)。
- **Live 驗證(D1–D4,藍圖 §10 階段 D)= 留 runbook 畀公司真 tenant 執行**,**唔計入 G-W100**(D4 reframe)。Gate 只認 mock 測試 + 靜態檢查 + 鐵律 diff。

## §4 §9.3 實作決定(proposed default,待 approve 時確認 / 覆寫)

| # | 決定 | proposed default | 理由 |
|---|---|---|---|
| D-1 | `SourceConnector` 正式型別簽名 | F1 設計(跟 `ConversationStore`/`KBStorageBackend` Protocol convention)| 工程決定,非用戶決定 |
| D-2 | **Anyone-link 政策** | **drop**(唔索引該 grant;可 config 改 public / 拒索引)| 最保守 — 映射唔到 Entra principal 嘅 grant 預設唔放入(H5 安全傾向);**security-relevant → 向用戶 surface 確認** |
| D-3 | credential 儲存 | 階段 1 `.env`(gitignored)/ Beta+ Key Vault(C12 已落)| 跟藍圖 §1.4 + 既有 pattern,無新嘢 |
| D-4 | chunk-level ACL 傳播(缺口②)| **每 chunk 重複 `allowed_principals`** | 對齊 `orchestrator.py:331` 既有 stamp;Tier 1.5 規模(按需匯入)無膨脹壓力;文件級 ACL 表 join 留 production case 觸發 |
| D-5 | 防爆量超額策略 | `transitiveMembers` 展開 cap **< 2,049 / file**,超額 log warning + truncate(可退化 KB 層)| 藍圖 §5.5 硬上限;safe default |
| D-6 | Graph 存取 dep | `azure-identity` + `httpx`(**已存在,無新 dep**)| H2 逐項確認完成 |

## §5 Out of scope(留後續 / 別滑入)

- 🚧 **前端匯入 wizard(H7 重現 `integration-import/` 4 surface)= 階段 1b**:設計 mockup 已備(`70e42df`),但 API 對唔到真 tenant 前 frontend 屬 speculative(Karpathy §1.2 — 唔建無得 verify 嘅嘢)。**建議等真 tenant 驗證將近、或用戶要 full vertical slice 先做**。target = W{NN}b 或 live 驗證前。**向用戶 surface 揀:F6 後即做 frontend / 抑或留 1b**。
- **Live tenant 驗證**(藍圖 §10 階段 D D1–D4)= runbook 畀公司執行(D4 reframe)。
- **auto-sync / delta**(`delta` method 保留 `supports_delta=False`,唔實作)= 階段 3(Tier 2,H4)。
- **多 provider**(Google Drive / Box / Confluence)= 階段 2(Tier 2);interface 已 Tier 2-friendly,唔使重構。
- **turnkey SharePoint indexer** = 永不(繞過 Docling 核心,§2.3)。
- **preview Entra-native token-trim**(`permissionFilterOption`)= 押 GA 字串比對(現做法),唔等 preview(kill list #1)。

> **🔴 Tier 邊界提醒**:統一框架易滑入 Tier 2 —— 嚴守「階段 1 = 抽象 interface + **一個** SharePoint connector + 按需手動匯入」。順手做多 provider / auto-sync → STOP per H4。

## §6 Risks

- 🟡 **Live 不可本機驗(D4)**:SharePoint/Graph 要真 tenant,本 phase 只 mock 測試。Mitigate:mock 測試鏡像藍圖 §10 階段 D 各 criteria(security trimming / per-doc 失敗 / change-detection),令公司 runbook 執行時行為可預期。
- 🟡 **Anyone-link 政策係 security default(D-2)**:預設 drop 最保守,但屬 KB 政策 → **向用戶 surface 確認**(approve plan 時)。
- 🟡 **connector-sourced 文件 query filter 語意**:依賴既有 P2 filter(`hybrid.py`);`allowed_principals` 空集 = public(`orchestrator.py:149` fail-open transition)——SharePoint 文件抽到 ACL 後**唔應**為空,F4/F5 要確保抽唔到 ACL 時**唔默默變 public**(應記 per-doc 失敗或退化 KB 層,非 fail-open)。F5 acceptance 涵蓋。
- 🟢 **H2 無新 vendor/dep** + **B1 前置已 ship**(W90)→ 開工依賴清。
- 🟢 **ingestion 核心零改動**(§7.2 鐵律,Gate diff 驗證)→ blast radius 限 `backend/integration/` 新 module + 1 個 thin API route。
- 🟢 **H6 coverage**:新 connector/permission/import module 屬 backend pipeline-adjacent,同步寫 test(mock Graph)。

## §7 Changelog

| 日期 | 變動 | 由 |
|---|---|---|
| 2026-06-30 | **Plan proposed(F1 code 未開)**:用戶 2026-06-30 講「可以開始 ADR-0070 階段 1 落 code」→ 依 R1 先寫 plan。Gate 評估發現 H2 無新 dep(`azure-identity`+`httpx` 已存在)+ B1 前置(`allowed_principals` plumbing)已 ship(W90 P2.1)→ 兩 gate 清。D4 reframe:本機落 connector code + mock 測試,live 驗證留 runbook。6 deliverable F1–F6(F1 interface → F2 Graph client → F3 connect/browse/list/fetch → F4 get_principals 權限映射 → F5 import service 薄銜接 → F6 API route + Gate)。frontend wizard 列 §5 階段 1b(向用戶 surface 揀時機)。§9.3 六項實作決定 proposed default(D-2 Anyone-link=drop security-relevant → 待確認)。**STOP — 等用戶 approve plan + 確認 D-2 + frontend 時機,先開 F1。** | proposed |
