# 統一整合層階段 1 — SharePoint 按需匯入 · 方案藍圖(Solution Blueprint)

**Date**: 2026-06-29(起)
**Status**: 方案藍圖 — 逐節寫,**交付給用戶喺公司真實環境執行**(非 local repo implement)。
**對應**: ADR-0070(Accepted 2026-06-28)/ BACKLOG B-01 / COMPONENT_CATALOG C17 / progress tracker `integration_layer_phase1_sharepoint_solution_PROGRESS.md`
**前置 deep-research**: `unified_integration_layer_architecture_20260628.md`(設計骨架)+ `sharepoint_connector_permission_mapping_external_research_20260628.md`(權限實證)
**讀者**: Chris(技術 Lead)+ 公司 IT + Claude Code

> **本檔性質**:呢份係**你帶去公司真實環境執行嗰份方案書** —— 由前置條件、認證、interface、SharePoint 連接、權限映射、撤權、到公司執行 checklist。技術決定全部 ground 喺上述 ADR + 兩份 deep-research(對抗式查證,20 confirmed / 5 killed)。**唔喺 local repo 假裝 implement**(SharePoint / Microsoft Graph 要真 tenant + `Sites.Selected` per-site grant,本機造唔到)。
>
> **寫作進度**:§0–§2 已寫;**§3–§10 + 附錄待續**(逐節寫,見 progress tracker §2 大綱)。

---

## §0 總覽

### 0.1 目標

令 EKP 嘅 KB 內容**唔再只靠人手上傳文件**,而係可以**直接連接公司 SharePoint**,揀指定 site / library / 資料夾 → 把文件 + **原生權限** 拉入 KB,經 EKP 自家 Docling ingestion 建索引,並喺檢索時**尊重來源權限**(冇權限嘅人唔會透過 RAG 睇到內容)。

### 0.2 階段 1 鎖死範圍(per DG-INT-2,守 H4)

| 階段 1 **做** | 階段 1 **唔做**(留 Tier 2) |
|---|---|
| 落 `SourceConnector` 抽象 interface(provider-agnostic) | 多 provider(Google Drive / Box / Confluence)→ 階段 2 |
| **一個** concrete connector = SharePoint | 自動同步(delta / 排程 / webhook 撤權)→ 階段 3(H4 明確 Tier 2) |
| **按需手動匯入**(用戶揀範圍,觸發一次匯入) | turnkey indexer(會繞過 Docling 核心)|
| push-model + GA 字串比對 ACL `allowed_principals` | preview Entra-native 自動 token-trim(無 SLA) |

階段 1 定位 = **Tier 1.5**。架構**一次過設計成 Tier 2-friendly**(interface + capability model 一步到位),但**實作分階段**,將來加 provider / auto-sync 唔使重構。

### 0.3 主路線一句(per deep-research 裁決)

```
Graph(Sites.Selected, application 服務帳號)拉 SharePoint 文件 + /permissions ACL
  → 自家 Docling ingestion(圖文還原 / profile / 可調配置全保留)
  → 用 Graph transitiveMembers 把 nested group 展成 flat principal set(group 級)
  → push chunks + allowed_principals(Entra GUID 字串)入 Azure AI Search
  → query-time:GA 字串比對 security filter 按用戶 principal set trim
撤權:排程 full re-ingest(delta 對 library 層唔可靠)+ 接受有界延遲
```

### 0.4 設計鐵律(保護核心競爭力)

> **Connector 只負責「來源 → 標準化文件 + 權限 + metadata」,絕對唔掂 ingestion 核心。**

換來源 = 換 adapter;Docling layout-aware parsing / 圖文還原 / per-doc profile / per-KB 可調配置 **全部零改動**,無論文件由邊個來源嚟。

### 0.5 交付 ↔ 執行分工(reframe,per D4)

| 角色 | 負責 |
|---|---|
| **本方案書(AI 交付)** | 架構 / interface / 認證 / 權限映射 / 撤權策略 / 公司執行 runbook |
| **你 + 公司 IT(真實環境執行)** | Entra app registration、`Sites.Selected` per-site grant、credential、真實 tenant 上跑匯入 + 驗證 |

### 0.6 本檔導航

§0 總覽 · **§1 前置條件(IT / tenant)** · **§2 認證架構** · §3 `SourceConnector` interface + capability model · §4 SharePoint connector 實作 · §5 權限映射(ACL → `allowed_principals`) · §6 撤權 / stale permission · §7 與 EKP 核心銜接 · §8 錯誤模型 + 生命週期 · §9 範圍邊界 + 未答缺口 · §10 公司執行 checklist · 附錄(Graph endpoints / scopes / 來源)。

---

## §1 前置條件(IT / tenant)

> 呢節係**公司 IT 喺真實環境要先 set 好嘅嘢**;缺一階段 1 匯入就行唔到。每項標明由邊個角色做。

### 1.1 前置清單(總覽)

| # | 前置 | 角色 | 備註 |
|---|---|---|---|
| P1 | SharePoint / Microsoft 365 tenant + 目標 site / library | 公司既有 | 確認要匯入邊個 site/library |
| P2 | Entra app registration(ingestion 服務帳號)| IT / Entra admin | 建 app + client credential |
| P3 | 授予 `Sites.Selected`(**application** permission)+ admin consent | Entra admin | **consent ≠ 有權**(見 1.3)|
| P4 | **per-site 顯式授權**(逐個 site grant app 讀權限)| SharePoint / site admin | 三步缺一即拒(見 1.3)|
| P5 | credential 安全儲存 | IT | 階段 1 配置 / `.env`;Beta+ Azure Key Vault(H5)|
| P6 | (query-time)delegated / OBO 認證可用 | IT | 重用 EKP 既有 Entra ID(W7–W8 bridge)|

### 1.2 Entra app registration(P2)

ingestion 服務帳號用一個 Entra app registration(client credentials / app-only token):
- 註冊 app → 攞 `tenant_id` / `client_id`。
- 建 client secret 或 certificate(certificate 較安全,建議生產用 cert)。
- 呢個 app 之後**只**會被授予 `Sites.Selected`(least-privilege),唔授 `Sites.FullControl.All`。

### 1.3 `Sites.Selected` 三步授權(P3 + P4)— **最易踩中嘅位**

deep-research 確認:`Sites.Selected` 係**「同意都唔等於有權」**嘅最小權限模型。授一個 site 要**三個獨立步驟,缺一即拒**:

1. **App 層**:app registration 加 `Sites.Selected`(**application** permission)。
2. **Tenant consent**:Entra admin 對該 app 嘅 `Sites.Selected` 做 admin consent。
   - ⚠️ 做完 1+2,app **仍然對任何 site 零權限** —— 只係「**有資格**被逐 site 授權」。
3. **Per-site grant**:對**每一個**要匯入嘅 site,顯式授予該 app 角色(`read` 足夠 ingestion;唔需要 write)。逐 site 做,由 site / SharePoint admin 執行。
   - 具體 Graph 呼叫(POST 到該 site 嘅 permissions + role)放 §4 / 附錄。

**好處**:逐 site least-privilege,security review 可辯護(app 只能掂被明確授權嘅 site),優於 turnkey indexer 需要嘅 `Sites.FullControl.All`。
**撤權**:有兩個控制點(移除 per-site grant / 移除 app consent),撤其一即斷。

### 1.4 credential 儲存(P5)

- **階段 1**:配置 / `.env`(gitignored,per H5;絕不 commit secret)。
- **Beta+**:Azure Key Vault(EKP 已喺 C12 落 `azure-keyvault-secrets` SDK,`KEY_VAULT_URL` 設定即啟 `AzureKeyVaultProvider`)。
- certificate / secret 輪替:由 `ConnectionHandle` 處理 token refresh(見 §2.4)。

### 1.5 query-time 認證前置(P6)

檢索時要按**登入用戶**嘅 principal set 做 security trimming(§5 / §7),所以 query-time 需要 per-user token(delegated / on-behalf-of)。EKP W7–W8 已做過 Entra ID mock bridge,呢部分認證可重用(見 §2.2)。

---

## §2 認證架構

### 2.1 雙模式分工(核心決定)

| 用途 | 認證模式 | 權限 | 點解 |
|---|---|---|---|
| **Ingestion**(拉文件 + 抽 ACL) | **application** `Sites.Selected`(app-only token,client credentials)| 服務帳號 superset(被授權嘅 site 全讀)| 後台批次匯入,無互動用戶;least-privilege 逐 site |
| **Query-time**(security trimming)| **delegated / on-behalf-of**(per-user token)| app 權限 ∩ **用戶**權限 | 要知道「邊個用戶」先 trim;delegated「app 永不超過用戶權限」更安全(微軟建議優先)|

> **caveat(per deep-research §3.4)**:delegated `Sites.Selected` 僅 Microsoft Graph API 實作 —— 對我哋呢種 **Graph-based RAG 無影響**(我哋本身就行 Graph)。

### 2.2 query-time trimming 概念流(細節在 §5 / §7)

```
用戶登入(Entra ID,delegated / OBO token)
  → 取得用戶 principal set = {user GUID} ∪ {用戶所屬 group GUID(展開)}
  → 查詢 Azure AI Search 時加 GA 字串比對 security filter:
       allowed_principals/any(p: search.in(p, '<用戶 principal set>'))
  → 只返回用戶 principal set 命中 allowed_principals 嘅 chunk
```

呢個比對邏輯**只寫一次、全 provider 共用**(收斂點 = `allowed_principals`,複用 EKP RBAC track / ADR-0066/0067)。

### 2.3 為何唔用 `Sites.FullControl.All` / turnkey indexer

- turnkey SharePoint indexer 需要高權限 + 自己 crawl/parse/chunk → **繞過 Docling 核心**(放棄 EKP 競爭力)→ reject。
- 競品(Glean)real-time 撤權 gated on `Files.ReadWrite.All` + `Sites.FullControl.All`(高權限)且 claim 被反證 → 唔行高權限路線。
- 我哋 push-model + `Sites.Selected` = 低權限 + 保留核心 + GA 穩妥。

### 2.4 token refresh(interface ⑥)

長時間 ingestion run 期間 app token 會過期。`ConnectionHandle`(§3)**內部封裝 refresh** —— connector 各方法攞 handle 時自動確保 token 有效,呼叫方唔使理。credential 來源 = §1.4(階段 1 配置 / Beta+ Key Vault)。

### 2.5 認證相關 H2 注意

Microsoft Graph 存取(`azure-identity` + `httpx` managed-REST,傾向 over `msgraph-sdk`,對齊 C16 F1「managed-REST > heavy SDK」)屬**新 dependency = H2** → 階段 1 implementation plan 內逐項確認 + R8 corp-proxy mitigation(per ADR-0017)。本方案書唔喺定方向階段加 dep。

---

> **§3–§10 + 附錄 待續**。下一塊:§3 `SourceConnector` interface + capability model(5 點修正 interface)+ §4 SharePoint connector 實作。大綱見 progress tracker `integration_layer_phase1_sharepoint_solution_PROGRESS.md` §2。
