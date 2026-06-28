# 統一整合層(Unified Integration Layer / Connector Framework)— 架構分析 + 設計骨架(2026-06-28)

**Date**: 2026-06-28
**Status**: Design proposal — **未決策、未開 phase、未寫 ADR**(交俾 Chris 定方向)。本 doc 係 future ADR 嘅前置設計骨架。
**Scope**: 把「連接外部文件來源做 KB」由「針對 SharePoint 嘅單一 connector」升級為「**統一整合層**:一個可支援多個 service provider / 第三方系統嘅來源抽象框架」。Microsoft 先行,但設計 generalize 到 Google / AWS / Box / Confluence 等。
**讀者**: Chris(技術 Lead)+ Claude Code(本 repo AI 助手)
**依據**: 用戶 2026-06-28 vision(企業推廣需要統一整合層,非只 SharePoint)+ `sharepoint_connector_permission_mapping_external_research_20260628.md`(SharePoint 作為第一個 concrete connector 嘅深度)
**錨點**: CLAUDE.md §5.1 H1(架構變更)/ §5.2 H2(vendor SDK)/ §5.4 H4(Tier 2 auto-sync)/ architecture.md「modular, extensible, MCP-ready」要求

> **本 doc 唔係 architecture spec(architecture.md frozen)**,係一份設計 proposal。任何落地仍需 ADR + Chris approve。

---

## 1. 一句話 vision + 結論

**Vision**:本項目要喺企業內部推廣,需要一個**統一整合層** —— 一個框架,可以接駁唔同來源(SharePoint / OneDrive / Google Drive / S3 / Confluence …),統一咁:連接 → 認證 → 瀏覽 → 選取 → 抓文件 + 抓權限 → 交俾我哋自家 ingestion 入 KB。

**結論**:技術上完全可行,而且**唔影響我哋核心競爭力** —— 因為有一條設計鐵律(§5):**connector 只負責「來源 → 標準化文件 + 權限 + metadata」,絕對唔掂 ingestion 核心**。即係換來源 = 換 adapter,Docling / 圖文還原 / profile / 可調配置全部不變。**但統一整合層本質係 Tier 2 級 vision**,要分階段(§8):Tier 1 先落抽象 interface + 一個 concrete connector(SharePoint 按需匯入),多來源 + 自動同步留 Tier 2。

---

## 2. 問題陳述 / 動機

| 現狀 | 企業推廣需要 |
|---|---|
| KB 內容只能**人手上傳文件** | 直接連企業現有文件庫(SharePoint / OneDrive / Google Drive …),自動拉入 KB |
| 單一上傳來源 | 多 service provider / 第三方系統,統一管理 |
| 無來源權限概念 | 尊重來源原生權限(security trimming,唔可以「冇權限嘅人透過 RAG 睇到」) |

用戶以 Microsoft Copilot Studio 作為概念例子:佢就係「一個框架接多來源入 KB」,只不過偏自家生態。我哋要做嘅係**同一概念但 provider-agnostic** 嘅統一層。

---

## 3. 核心概念:Source Abstraction Layer(來源抽象層)

```
                    ┌─────────────────────────────────────┐
   外部來源          │       統一整合層 (Integration Layer)   │      EKP 核心(不變)
   ──────           │  ┌────────────┐                       │      ──────────
   SharePoint ──┐   │  │ SharePoint │                       │
   OneDrive   ──┼──→│  │  adapter   │─┐                     │
   Google Drive─┼──→│  ├────────────┤ │  標準化           │   ┌──────────────┐
   S3         ──┼──→│  │  Google    │ ├─→ 文件 + 權限 ────→│──→│  Docling     │
   Confluence ──┘   │  │  adapter   │ │   + metadata       │   │  ingestion   │
                    │  ├────────────┤ │                     │   │  (圖文/profile│
                    │  │  …adapter  │─┘                     │   │   /可調配置)  │
                    │  └────────────┘                       │   └──────┬───────┘
                    │   (provider-specific,可插拔)          │          │
                    └─────────────────────────────────────┘          ▼
                                                              Azure AI Search
                                                              (chunks + allowed_principals)
```

**關鍵**:左邊(adapter)provider-specific、可插拔;右邊(ingestion 核心)provider-agnostic、永不變。

---

## 4. 架構分解:7 個正交關注點

每個 provider 各自實作頭 5 個;第 6-7 個係統一層共用邏輯。

| # | 關注點 | 做咩 | provider 差異例 |
|---|---|---|---|
| 1 | **連接 + 認證** | provider 自己嘅 auth | Microsoft = Entra app registration(`Sites.Selected`);Google = OAuth;S3 = IAM key |
| 2 | **瀏覽來源** | 列可連容器 | SharePoint site/library;Drive folder;S3 bucket;Confluence space |
| 3 | **選擇範圍** | UI 揀邊啲入 KB | 統一 UI,adapter 提供樹狀結構 |
| 4 | **抓取 + 同步** | full 初次 + 增量 | 有 delta(Graph,但 library 層唔可靠)/ 無 delta(純排程 full) |
| 5 | **權限映射** | 來源 ACL → `allowed_principals` | 有 ACL(SharePoint)/ 無 ACL(純 folder)→ fallback KB 層 |
| 6 | **交接 ingestion** | 文件交俾 Docling pipeline | **統一,零 provider 影響** |
| 7 | **生命週期** | re-sync / 撤權傳播 / 健康監控 / 錯誤處理 | 統一框架,按 capability 退化 |

---

## 5. 設計鐵律(保護核心競爭力)

> **Connector 只負責「來源 → 標準化文件 + 權限 + metadata」,絕對唔掂 ingestion 核心。**

- 第 6 步之後 —— Docling layout-aware parsing、圖文還原(image recall / inline markers / section anchoring)、per-doc profile、per-KB 可調配置 —— **全部不變**,無論文件由邊個來源嚟。
- 呢個就係 SharePoint research 確認嘅 **push-model 邊界**(自家 ingestion + 自己注入權限),**generalize 成統一層鐵律**。
- 結果:加新 provider = 寫一個新 adapter(第 1-5 步),核心零風險。亦避開 turnkey indexer 會繞過我哋 ingestion 嘅陷阱。

---

## 6. SourceConnector interface 草案(capability-driven)

跟 EKP backend convention(Protocol + async,參考 `ConversationStore` / `KBStorageBackend`):

```python
# 概念草案 — 非最終;正式設計入 ADR
class ConnectorCapabilities:
    auth_kind: Literal["oauth", "app_registration", "api_key"]
    supports_browse: bool      # 可唔可以列容器樹
    supports_acl: bool         # 有冇文件級權限可抽
    supports_delta: bool       # 有冇可靠增量同步
    acl_granularity: Literal["none", "kb", "document"]

class SourceConnector(Protocol):
    capabilities: ConnectorCapabilities

    async def connect(self, credentials) -> ConnectionHandle: ...
    async def browse(self, handle, container_id=None) -> list[SourceContainer]: ...
    async def list_documents(self, handle, container_id) -> list[SourceDocumentRef]: ...
    async def fetch_document(self, handle, doc_ref) -> SourceDocument: ...   # bytes + metadata
    async def get_principals(self, handle, doc_ref) -> list[Principal]: ...   # 已展平 nested group
    # 以下 gated by capability — 無 supports_delta 嘅 connector 唔實作:
    async def delta(self, handle, container_id, token) -> DeltaResult: ...
```

**Capability model 嘅重點**:framework **唔可以假設所有 provider 一樣**。UI + lifecycle 讀 `capabilities` 決定:
- 無 `supports_delta` → 隱藏「自動同步」選項,只提供排程 full re-ingest。
- `acl_granularity == "none"` → 退化到 KB 層權限(該來源所有文件 = KB 嘅 ACL)。
- `acl_granularity == "document"` → 行文件級 security trimming(填 `allowed_principals`)。

---

## 7. 權限 generalization(統一整合層最難一環)

把「有 ACL vs 冇 ACL」嘅來源**統一收斂到我哋 `allowed_principals`**:

| 來源類型 | 處理 |
|---|---|
| 有文件級 ACL(SharePoint) | Graph `/permissions` 抽 → 正規化 Entra GUID → 用 `transitiveMembers` 展平 nested group → 填 `allowed_principals` |
| 特殊 principal(Anyone link) | **無可解析 GUID** → 明確規則(drop / 當 public / 拒絕索引)— per SharePoint research §3.3 |
| 有 group 但跨系統(Confluence local group / Salesforce profile) | 模型化為 external group(參考 M365 Copilot connector 設計) |
| 無 ACL(純 share folder) | 退化:該來源 = KB 層 ACL,所有文件繼承 |

**統一收斂點 = `allowed_principals`(我哋 RBAC track 已有嘅文件級 ACL 欄)。** 即係每個 connector 嘅權限映射,最終都係「填同一個 `allowed_principals`」,query-time security trimming 邏輯**只寫一次、全 provider 共用**。

**繼承 SharePoint research 嘅已知限制**:展 group 要防爆量(< 2,049 / file);stale permission 結構性無即時撤權,要排程 re-ingest 補。

---

## 8. Tier 邊界 + 分階段路線

| 階段 | 範圍 | Tier | Hard constraint |
|---|---|---|---|
| **階段 0(現狀)** | 人手上傳 | Tier 1 | — |
| **階段 1** | 落 `SourceConnector` 抽象 interface + **一個** concrete connector(SharePoint **按需手動匯入**,push-model + GA 字串比對 ACL) | **Tier 1.5** | H1(來源抽象)+ H2(Graph SDK)→ ADR |
| **階段 2** | 加多 provider(Google Drive / Box / Confluence)+ 統一 UI 管理 | **Tier 2** | H4(多來源框架)+ 各家 H2 SDK |
| **階段 3** | 自動同步(delta / 排程 / webhook 撤權) | **Tier 2** | H4(auto-sync from external source — 明確 Tier 2) |

**建議**:架構**一次過設計成 Tier 2-friendly**(interface + capability model 一步到位),但**實作分階段**,Tier 1 只落抽象 + SharePoint 按需匯入。咁將來加 provider / auto-sync 唔使重構,符合 architecture spec「extensible, MCP-ready」要求。

---

## 9. 同 EKP 現有 component 嘅銜接

- **Ingestion(Docling pipeline)**:統一整合層 sit **upstream**,交標準化文件落去,ingestion 零改動。新增 component 或 extend 現有 ingestion component(入 COMPONENT_CATALOG.md 決定)。
- **KB management**:connector 連到某個 KB;一個 KB 可以有混合來源(上傳 + SharePoint)。
- **RBAC track(W88-W95)**:**直接複用** —— connector 權限映射填 `allowed_principals`,query-time trimming 已鋪緊。整合層同 RBAC track 係同一條路嘅兩段。
- **Auth(Entra ID)**:W7-W8 做過 Entra mock bridge,SharePoint connector 認證可重用。

---

## 10. 業界參考(分層)

| 框架 | connector 抽象 | 啟發 | 可信度 |
|---|---|---|---|
| **Microsoft Graph connectors** | external items + ACL model + external groups | 跨系統權限 generalization 參考 | 高(官方) |
| **LlamaIndex / LlamaHub** | 100+ connectors,統一 `BaseReader` | interface 設計範本 | 中(vendor) |
| **Unstructured** | source connectors framework | ingestion-oriented connector 模式 | 中(vendor) |
| **Airbyte / Fivetran** | connector SDK + capability spec + 增量同步框架 | capability 宣告 + delta 框架成熟設計 | 中(vendor) |
| **LangChain** | document loaders | 輕量 loader 抽象 | 中(vendor) |

> 各家 connector SDK 設計嘅**橫向深度對比**(capability negotiation / 跨來源權限 generalization 最新實踐)留待 future focused deep-research,當需要 validate 具體設計決策時先做(避免過早燒 token)。

---

## 11. 未決問題 + 風險

1. **Component 歸屬**:整合層係新 component 定 extend ingestion?(入 COMPONENT_CATALOG.md)
2. **Chunk-level ACL 傳播**:文件切多 chunk,每 chunk 重複 `allowed_principals`?index 膨脹 + query 效能?(SharePoint research 未答缺口②)
3. **撤權延遲**:stale permission 結構性,排程 full re-ingest 頻率 vs 成本?
4. **Credential 管理**:多 provider credential 安全儲存(H5;Beta+ 用 Azure Key Vault)。
5. **第一個 provider 揀邊個**:SharePoint(公司主力)定先做最簡單嘅(純 folder,無 ACL 複雜度)?
6. **🔴 Tier 邊界風險**:統一框架好易滑入 Tier 2;要嚴守「Tier 1 只落抽象 + 一個 connector」,唔好順手做多來源 / auto-sync(H4)。

---

## 12. 下一步(ADR 前置,需 Chris approve)

1. 用本 doc 骨架 + SharePoint research 起草 **ADR**(來源抽象 framework,H1 + H2)。要定嘅 scope decision:
   - 階段 1 範圍鎖死(SharePoint 按需匯入,唔做 auto-sync)。
   - `SourceConnector` interface + capability model 定案。
   - 第一個 concrete connector = SharePoint。
2. ADR Accept 後先開 implementation phase(rolling JIT plan)。
3. **唔好**喺定方向階段動手寫 code。

---

## 附錄:相關文件

- `sharepoint_connector_permission_mapping_external_research_20260628.md`(第一個 concrete connector 深度 + 權限映射實證)
- `docs/01-planning/enterprise-rbac/`(RBAC track,`allowed_principals` 文件級 ACL 地基)
- CLAUDE.md §5(H1 / H2 / H4 hard constraints)
- architecture.md §11(Tier 2 trigger matrix)
