# ADR-0070: Source Abstraction Framework — 外部文件來源統一整合層(Unified Integration Layer)

**Date**: 2026-06-28
**Status**: Accepted(Chris 2026-06-28 — 用戶 session 行使 decision owner 拍板 3 個 scope decision DG-INT-1/2/3 resolved + 採納 5 點 interface 修正;H1 + H2 + H4)
**Approver**: Chris(2026-06-28)

> 企業推廣方向 ADR。整體來源抽象架構 + 階段 1 scope 拍板。觸 **H1**(來源抽象新 component + ingestion upstream)+ **H2**(Microsoft Graph SDK)+ **H4**(auto-sync = Tier 2 邊界)。
> 技術基礎:[`../09-analysis/unified_integration_layer_architecture_20260628.md`](../09-analysis/unified_integration_layer_architecture_20260628.md)(設計骨架)+ [`../09-analysis/sharepoint_connector_permission_mapping_external_research_20260628.md`](../09-analysis/sharepoint_connector_permission_mapping_external_research_20260628.md)(第一 connector 深度 + deep-research 實證)。

## Context

EKP 要喺企業內部推廣,KB 內容唔可以只靠**人手上傳文件** —— 企業文件住喺 SharePoint / OneDrive / Google Drive / S3 / Confluence 等系統。用戶 2026-06-28 明確確立方向:要嘅係**企業級統一整合層**(provider-agnostic connector framework),**唔係針對性嘅單一 SharePoint connector**。概念類 Microsoft Copilot Studio(一個框架接多來源入 KB),但 provider-agnostic。Microsoft 先行(公司環境 Azure 為主)。

兩階段研究奠定基礎:

- **機制確認**:像 Copilot Studio 嘅工具背後唔係 real-time,係「指定來源 → 拉文件 → 預處理建索引 → 排程刷新」。本質係「換一個上傳來源」,RAG 必然預處理。
- **deep-research(2026-06-28,106 agent / 20 confirmed / 5 killed)主路線裁決**:push-model(自跑 ingestion + 自己注入權限 metadata)獲微軟官方明文背書,同 EKP locked stack 全相容。但推翻兩個樂觀假設 ——
  - **① push 嘅權限字串欄唔會自動獲 Entra token-trim**(0-3 反證):正式版(GA)路徑就係**純字串比對 security filters**,而字串比對啱啱對應 EKP 現有 `allowed_principals` 做法;Entra-native 自動 token-trim 全部仍 PREVIEW(`2026-05-01-preview`,無 SLA)。
  - **② Graph delta query 無法可靠捕捉 SharePoint library/folder 層權限變更**(結構性,微軟員工親口確認)→ 撤權唔可以靠 delta。
- **stale permission**:微軟官方技術文件親口承認結構性有界延遲(用「timing lag」唔畀秒數),pull/push 都受,**無方案即時撤權**。

**核心張力**:Azure AI Search 有 turnkey SharePoint indexer(pull model,自己 crawl+parse+chunk),但會**繞過 EKP 整個 ingestion 核心**(Docling layout-aware chunking / 圖文還原 / per-doc profile / per-KB 可調配置)—— 嗰啲先係 EKP 價值所在。故主路線必須 push-model。

**Tier 邊界**:統一整合層本質係 Tier 2 級 vision(多來源框架 + auto-sync,後者係 H4 明確 Tier 2)。但可分階段做到 Tier 1-friendly。

## Decision

採來源抽象架構(設計骨架見前置 doc),拍板以下:

1. **`SourceConnector` 抽象 + capability model**(H1):provider-agnostic Protocol(跟 EKP 既有 `ConversationStore` / `KBStorageBackend` async Protocol convention)。**interface 草案(per DG-INT-3 修正,5 點)**:

   ```python
   class SourceConnector(Protocol):
       capabilities: ConnectorCapabilities
       async def connect(self, credentials) -> ConnectionHandle: ...
       async def browse(self, handle, container_id=None) -> AsyncIterator[SourceContainer]: ...        # ② 分頁
       async def list_documents(self, handle, container_id) -> AsyncIterator[SourceDocumentRef]: ...   # ②③ ref 帶 etag/version
       async def fetch_document(self, handle, doc_ref) -> SourceDocument: ...                           # ④ stream / temp path
       async def get_principals(self, handle, doc_ref) -> list[Principal]: ...                          # ① flatten 到 group 級
       async def delta(self, handle, container_id, token) -> DeltaResult: ...                           # ⑤ 保留唔實作
   ```

   - **① `get_principals` 展平到 group 級,非 user 級**:展 nested group → 直接 group id + 直接 user id 即止(**唔展到每個 member user**)。query-time string-match 比對嘅係用戶 token 帶嘅 group membership,故 index 存 group id + 直接 user id;加 user 入某 group **即時生效、零 re-ingest**(展到 user 級會 index 爆炸 + 改 membership 要 re-stamp 全部文件)。`transitiveMembers` 防爆量(< 2,049/file)仍喺 connector 內做,但目標係 flatten **nested groups**,唔係 flatten to users。**同 ADR-0067 P4 群組繼承洞察一致**(chunk 存 group key 非 member oid → group member 改動零 re-stamp,query 側 `principals_for_user` 展開)。
   - **② `browse` / `list_documents` 分頁**:返 `AsyncIterator`(或帶 continuation token),大 library 上萬文件唔可以一次 `list[...]`(爆 memory + 超 Graph 分頁上限)。
   - **③ `SourceDocumentRef` 帶 change-detection 欄位**(`etag` / `version` / `last_modified` / `size`):即使階段 1 手動匯入,re-import 時只 re-ingest changed 文件慳成本;Graph driveItem 原生有 `eTag`/`cTag`,前瞻平宜。
   - **④ `fetch_document` 用 stream / temp file path**,唔好全 bytes-in-memory(大掃描件 PDF 頂唔順);交俾現有 ingestion 入口(現食 multipart upload)。
   - **⑤ `delta` 保留但階段 1 唔實作**:`supports_delta=false` capability-gate;對齊「一次設計 Tier 2-friendly、實作分階段」,將來加 auto-sync 唔使改 Protocol。

   `ConnectorCapabilities` 宣告 `auth_kind` / `supports_browse` / `supports_acl` / `supports_delta` / `acl_granularity`;UI + lifecycle 按 capability 退化(無 delta → 隱藏自動同步;`acl_granularity=none` → 退化 KB 層權限)。

2. **設計鐵律 — connector 唔掂 ingestion 核心**:connector 只負責「來源 → 標準化文件 + 權限 + metadata」;之後 Docling pipeline / 圖文還原 / profile / 可調配置**全部不變**,無論文件由邊個來源嚟。換來源 = 換 adapter(第 1-5 步),核心零風險。把 push-model 邊界 generalize 成框架鐵律。

3. **權限統一收斂到 `allowed_principals`**(複用 ADR-0066 RBAC track):每個 connector 嘅權限映射,最終都係填同一個文件級 `allowed_principals` 欄;query-time security trimming 邏輯**只寫一次、全 provider 共用**。**用 GA 字串比對 security filters**(非 preview Entra-native token-trim)→ 主路線唔押注 preview。整合層同 RBAC track 係**同一條路嘅兩段**。

4. **認證分工**(Microsoft Graph,H2):ingestion 服務帳號用 **application `Sites.Selected`**(least-privilege,逐 site 授權,security review 可辯護);query-time 用 **delegated / on-behalf-of**(per-user token)。EKP 既有 Entra ID(W7-W8 mock bridge)可重用。

5. **權限展平到 group 級(非 user 級)+ 防爆量**:connector 用 Graph `transitiveMembers`(**非**被反證嘅 `transitiveMemberOf`)展 **nested group → flat group id set + 直接 user id**(**唔展到 member user**,per DG-INT-3 ①)→ 填 `allowed_principals`;query 側用用戶 token group membership 比對(同 ADR-0067 `principals_for_user` 一致),加 user 入 group 零 re-ingest。展開設上限(< 2,049 / file,避免 group 爆量)。特殊 principal(Anyone link 無可解析 GUID)按明確規則處理(drop / 當 public / 拒絕索引)。

6. **撤權策略**:stale permission 結構性,**用排程 full re-ingest** 補(delta 對 library 層唔可靠);撤權延遲產品上明示為有界延遲,**唔承諾即時撤權**。

7. **分階段 Tier 定位**:
   - **階段 1(Tier 1.5)**:落 `SourceConnector` 抽象 interface + **一個** concrete connector(SharePoint **按需手動匯入**,push-model + GA 字串比對 ACL)。**唔做** auto-sync / 多 provider。
   - **階段 2(Tier 2)**:加多 provider(Google Drive / Box / Confluence)+ 統一管理 UI。
   - **階段 3(Tier 2)**:自動同步(delta / 排程 / webhook 撤權)= H4 明確 Tier 2。
   - **架構一次過設計成 Tier 2-friendly,實作分階段**(符合 architecture spec「extensible / MCP-ready」)。

8. **Accept 後落地**:Accept 後 amend `architecture.md §3.3`(ingestion upstream 加來源層)+ §4(application architecture)+ COMPONENT_CATALOG.md(新 component 或 extend ingestion component),再按 rolling JIT 開階段 1 implementation phase。**唔喺定方向階段寫 code。**

### Scope decisions resolved(2026-06-28,用戶行使 decision owner)

| # | 問題 | 決議 |
|---|---|---|
| **DG-INT-1** | 第一個 concrete connector? | **SharePoint 先行試點**(公司主力) |
| **DG-INT-2** | 階段 1 範圍? | **鎖死** = SharePoint 按需手動匯入,排除 auto-sync + 多 provider(守 H4) |
| **DG-INT-3** | interface 定案? | **按修正後 interface** — Decision 1 五點 ①-⑤ 已採納;⑥⑦ 入階段 1 plan |

### 階段 1 plan 補充(per DG-INT-3 ⑥⑦,唔改 interface)

- **⑥ `ConnectionHandle` token refresh**:長 ingestion run token 會過期,handle 內部封裝 refresh;credential 儲存階段 1 用配置,Beta+ 用 Azure Key Vault(H5)。
- **⑦ 錯誤模型**:`fetch_document` 單一文件失敗**唔應該 abort 成 batch**;framework orchestrator 收集 per-doc 成功/失敗報告(同 ADR-0043 reindex per-doc summary pattern 一致)。

## Alternatives Considered

- **Turnkey SharePoint indexer(Azure AI Search pull model)**:索引 turnkey、Microsoft 託管,但**自己 crawl + parse + chunk → 繞過 EKP 整個 ingestion 核心**(放棄 Docling / 圖文還原 / profile / 可調配置 = 核心競爭力)→ **reject**。
- **Preview Entra-native ACL token-trim(server 自動驗 token + 展 group)**:免自寫 group 展開,但全部 PREVIEW(無 SLA,唔建議 production);GA 字串比對已足夠且對應現有 `allowed_principals` → **用 GA 字串比對,token-trim defer**(待 GA track)。
- **一次過全部 provider + auto-sync**:範圍爆炸 + 直接撞 H4 Tier 2;違反 Karpathy §1.2 simplicity → **reject;分階段**。
- **唔抽象,逐 provider 硬寫 connector**:短期快但唔 scalable,每加一個來源重複 ingestion handoff / 權限映射邏輯 → **reject;一次設計抽象層**。
- **delta query 做即時 ACL 同步**:deep-research 反證 library 層唔可靠 → **reject;用排程 full re-ingest**。

## Consequences

- **Positive**:一套抽象支援多來源,核心 ingestion 零風險(設計鐵律);權限統一收斂 `allowed_principals` 複用 RBAC track,security trimming 只寫一次;用 GA 字串比對唔押注 preview;分階段降風險 + 守 Tier 邊界;Microsoft 生態同源,階段 1 唔引入新雲廠商(Graph SDK 屬 H2 但 Azure 內)。
- **Negative**:Microsoft Graph SDK = 新 dependency(H2,需 R8 corp-proxy mitigation 評估 per ADR-0017);push-model 下 nested group 展平 + 防爆量 + 特殊 principal 處理係 EKP 自己工作量(indexer 自動做);stale permission 結構性無即時撤權(排程 re-ingest 補,撤權延遲要產品明示);chunk-level ACL 傳播最佳實踐未有 production case(階段 1 plan 要解)。
- **Neutral**:階段 1 = Tier 1.5(範圍受控,確認非 Tier 2);auto-sync / 多 provider 明確留 Tier 2(階段 2-3,各需 H4 + 各家 H2 review);credential 多 provider 安全儲存 Beta+ 用 Azure Key Vault(H5);component 歸屬入 COMPONENT_CATALOG.md。

## References

- [`unified_integration_layer_architecture_20260628.md`](../09-analysis/unified_integration_layer_architecture_20260628.md)(設計骨架:7 正交關注點 + 設計鐵律 + interface 草案 + capability model + 分階段)
- [`sharepoint_connector_permission_mapping_external_research_20260628.md`](../09-analysis/sharepoint_connector_permission_mapping_external_research_20260628.md)(deep-research 實證:push-model 裁決 + 權限映射 + preview/GA + stale permission + 認證最小權限)
- ADR-0066(檢索層文件級 ACL `allowed_principals` — 本 ADR 權限收斂點)
- ADR-0017(R8 corp-proxy dependency-add mitigation pattern — Graph SDK H2 適用)
- ADR-0014(Microsoft Entra ID auth — 認證可重用)
- CLAUDE.md §5.1 H1 / §5.2 H2 / §5.4 H4(architectural change / vendor / Tier 邊界)
- architecture.md §11(Tier 2 trigger matrix — auto-sync from external source)
