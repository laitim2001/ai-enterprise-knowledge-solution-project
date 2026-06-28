# SharePoint / OneDrive 連接 + 權限映射(Document-Level Security Trimming)— 外部市場 / 官方文件實證調查(2026-06-28)

**Date**: 2026-06-28
**Status**: Research brief — 外部證據彙整,**未決策、未開 phase、未寫 ADR**(交俾 Chris 定方向)。EKP-specific 比對 / 裁決見 §5 + §8。
**Scope**: 企業級 RAG / 知識庫連接 Microsoft SharePoint / OneDrive 作為 KB 來源 + 將來源權限映射到檢索層做 document-level security trimming 嘅 2025-2026 最新實證 + 業界實踐。Microsoft / Azure 先行(公司環境主力)。
**讀者**: Chris(技術 Lead)+ Claude Code(本 repo AI 助手)
**研究方法**: 兩階段 —— (1) 2026-06-27 web-search 初探(4 路);(2) **2026-06-28 deep-research harness** — 6 路 fan-out web search → 23 sources fetched → 108 falsifiable claims → 三票對抗式驗證 top 25(需 2/3 反證才剔除)→ **20 confirmed / 5 killed / 11 after synthesis**(106 agent calls)。
**動機**: 用戶 2026-06-27/28 提出長遠方向 —— EKP 要喺企業內部推廣,需要連接 Microsoft / Google / AWS 文件來源(Microsoft 先行)。本調查為將來 ADR(來源抽象 H1 + Microsoft Graph SDK H2)做引用依據。

> **遵守 CLAUDE.md 硬約束**:本調查嘅可行性裁決全部以 EKP locked stack(Azure AI Search + Azure OpenAI + Cohere + 自家 Docling ingestion)+ 文件級 RBAC track(`allowed_principals`)+ Tier 邊界為框架。任何方向落地仍需 ADR + Chris approve(H1/H2/H4)。

---

## 1. 一句話結論

**主路線(push-model 自家 ingestion + 自己注入權限 metadata 入 Azure AI Search + 映射到 `allowed_principals`)獲微軟官方明文背書、技術可行;但 deep-research 嘅最大價值係推翻咗初探兩個樂觀假設**:(1)「push 入去嘅權限欄會被當 Entra 認證自動 token-trim」**被 0-3 反證** —— 正式版(GA)路徑就係**純字串比對**,而字串比對啱啱對應我哋已經喺度做嘅 `allowed_principals`,所以**唔使押注 preview**;(2)「delta query = 可靠即時 ACL 同步」**被反證** —— Graph delta query 結構性無法可靠捕捉 library/folder 層權限變更。**stale permission 係官方承認嘅結構性有界延遲,無方案做到即時撤權。**

---

## 2. 三個 meta 結論(直接打中 EKP)

| # | 發現 | 對 EKP 意義 | 可信度 |
|---|---|---|---|
| 1 | **GA 正解 = 字串比對 security filters,正好等於我哋現有 `allowed_principals` 做法** — 四種 document-level access control 只有 string-match security filters 係 GA;Entra-native 自動 token-trim(POSIX-like ACL / Purview labels / SharePoint M365 ACLs)全部 PREVIEW(`2026-05-01-preview`,無 SLA) | **我哋方向正確,且唔需要 preview** — 現有字串 ACL 做法就係 GA 穩妥版;唔好為咗「server 自動展 group」嘅便利押注 preview | 高(3-0 + 3-0 + 2-1) |
| 2 | **push-model 獲官方明文支援,但展 nested group 嘅責任喺我哋一側** — 自跑 ingestion + push `userIds`/`groupIds`/`rbacScope` 得到同 indexer 一樣嘅 enforcement,但 push 路徑要自己把 nested group 展成 flat principal set | **push-model 同 locked stack 三者全相容**(Azure AI Search + 自家 Docling + 文件級 RBAC),代價 = 自己做 group 展開(`transitiveMembers` 端點) | 高(2-1 + 3-0) |
| 3 | **stale permission 係結構性限制,無方案即時撤權** — 官方技術文件親口承認「timing lag」唔畀秒數;delta query 無法可靠捕捉 library 層撤權;competitor Glean 自報「webhook 即時撤權」被反證 | **撤權延遲要當設計考量**(排程 full re-ingest + 接受有界延遲),唔好假設有即時方案 | 高(3-0 + 2-1) |

---

## 3. 逐子題發現(標票數 + 來源 + EKP 可用性)

### 3.1 子題 A — push-model vs turnkey indexer + chunk-level ACL 傳播

| 發現 | 票 | 成本 / re-index | EKP 可用性 |
|---|---|---|---|
| **微軟官方明文支援 push-model**:自跑 ingestion logic,經 REST/SDK push 文件夾帶 `userIds`/`groupIds`/`rbacScope` 三欄 + index 設 `permissionFilterOption=enabled` → 得到與內建 indexer **完全相同**嘅 server-side enforcement | 2-1 + 3-0 佐證 | 需 re-index(schema 改 `permissionFilter` 屬性)+ 小幅架構改 | ✅ **主路線獲背書** — 但只有想要 server-side token-trim 先要改 schema 成 `permissionFilter`(preview);若用 GA 字串比對則沿用現有 `allowed_principals` 即可 |
| **chunk-level ACL 傳播**:文件切細時,permission metadata 從 indexer field mapping 移去 index projection;每 chunk 要帶完整 ACL | 證據缺口 | — | ⚠️ **子題 A 核心未有 production case** — 文件切多 chunk 每 chunk 是否重複完整 `allowed_principals`?index 膨脹 + query 效能?**列入未答缺口(§7)** |

### 3.2 子題 B — stale permission + delta query 可靠度(出現重要反證)

| 發現 | 票 | EKP 可用性 |
|---|---|---|
| **stale permission 官方承認結構性有界延遲** — source 端撤權要等下次 indexer run / push 更新 / Purview refresh 先反映,用「timing lag」字眼**唔畀秒數**;pull 同 push 都受 | 3-0 + 2-1 | **無法靠 Azure AI Search 本身做到即時撤權**;緩解 = 排程 re-ingest / webhook / 接受有界延遲 |
| **【反證】delta query 無法可靠捕捉 library/folder 層權限變更** — 連同三個 Prefer header(`deltashowremovedasdeleted` / `deltatraversepermissiongaps` / `deltashowsharingchanges`)都唔得;folder/library 層加減 user/group 會令 delta token 失效(`resyncRequired`),屬架構性限制。微軟員工親口確認「current Graph APIs 無 straightforward 方法 track permission changes」 | 2-1 + 3-0 | ⚠️ **推翻初探假設** — 若用 delta query 做增量 ACL re-sync,library 層撤權捕捉唔到 → 要 full re-ingest 或其他機制補 |
| **競品量化(Glean,vendor 自報)** — 無 `Sites.FullControl.All` 高權限,permission-only 變更只能**每 24 小時**增量爬一次 | 3-0 | 佐證性外部數字(量化已知 stale 延遲類);**非新方向** |

### 3.3 子題 C — SharePoint ACL → 自家 ACL 映射難點

| 發現 | 票 | EKP 可用性 |
|---|---|---|
| **特殊 principal**:「Specific people」分享連結帶可解析 `grantedToIdentitiesV2` Entra user.id(可映射);「**Anyone**」連結**無可解析 Entra object ID**(permission 物件只有 link facet);「People in your organization」連結不令內容出現喺 search/Copilot | 3-0 + 2-1 | ⚠️ **映射時必須處理 Anyone link 特殊情況**(drop / 當 public / 拒絕索引);ISE blog 確認 ingestion-time 只抽 user/group,Anyone link 無嘢可抽 |
| **nested group 展開**:push 下要自己用 Graph `transitiveMembers` 端點(返回 flat nested members 列表,application 最小 = `GroupMember.Read.All`)。**`transitiveMemberOf`「v1.0 GA 跨所有 group type」claim 被 0-3 反證** → 唔好當定論 | 3-0(但相鄰 claim refute) | ✅ 可做,但係 push-model 把責任移到自己一側嘅具體工作量(indexer 自動做) |
| **規模硬上限**:單一用戶 group membership < 2,049(超過結果不可預測)、> 10,000 query 直接 400;ACL entry 上限 SharePoint 1000/file、ADLS Gen2 32/file | 3-0 | **自家展 group 亦要防爆量**(group → flat principal 展開要設上限保護) |
| **M365 Copilot connector external-groups 模型**(參考設計,非主路線):非 Entra group 構造(SharePoint groups / Salesforce Profiles 等)建議模型化為 external groups,支援 nested membership | 3-0 ×3 | 📖 **參考模型** — 唔直接適用我哋 push-model,但係「點處理非 Entra group + nested group」嘅成熟設計參考 |

### 3.4 子題 D — Microsoft Graph 認證最小權限(結論清晰)

| 發現 | 票 | EKP 可用性 |
|---|---|---|
| **`Sites.Selected` = 「同意都唔等於有權」最小權限** — consent 後仍需顯式 per-resource 授權(POST permissions + role);授 per-site 需三獨立步驟,缺一即拒;撤權有兩控制點 | 3-0 + 3-0 | ✅ **ingestion 服務帳號用 `Sites.Selected` 逐 site least-privilege,security review 可辯護**,優於 indexer 需要嘅 `Sites.FullControl.All` |
| **Selected scopes 支援 application + delegated 雙模式** — delegated 因「app 永不超過用戶權限」(app 權限 ∩ user 權限)更安全,微軟建議優先 | 3-0 | ✅ **架構分工**:ingestion 用 application `Sites.Selected`(superset 服務帳號);query-time trimming 用 delegated / on-behalf-of(per-user token)。caveat:delegated `Sites.Selected` 僅 Graph API 實作(對 Graph-based RAG 無影響) |

### 3.5 子題 E — 競品 / 框架成熟度(分層可信度)

| 框架 | permission-aware 做法 | 成熟度 | 可信度 |
|---|---|---|---|
| **Azure AI Search**(我哋 stack) | string-match security filters(GA)+ Entra-native token-trim(preview) | string filter GA;ACL token-trim preview | 高(官方 doc) |
| **M365 Copilot connectors** | external-items ACL 模型 + external groups | GA(Graph 構造) | 高(官方 doc) |
| **Glean** | Graph crawl + 24h 增量;real-time 需 `Files.ReadWrite.All` + `Sites.FullControl.All` 高權限 | 商用 GA | 中(vendor 自報,「即時撤權」claim 被反證 1-2) |
| **LlamaCloud / LlamaParse** | 抽 SharePoint 權限做 chunk-level metadata(`allowed_siteUser_ids`)+ retrieval metadata filter | 商用 | 中(vendor blog) |
| **Microsoft Foundry IQ** | SharePoint knowledge source | 新 | 中(個人 blog) |

### 3.6 子題 F — 分階段策略(證據缺口)

「先 pull-on-demand 手動匯入,後 auto-sync」分階段策略喺業界是否 common pattern + incremental migration 經驗 —— **本輪存活 claim 未直接覆蓋,列入未答缺口(§7)**。

---

## 4. 被反證 kill list(5 個 — 寫 ADR 前唔好當定論)

> deep-research 嘅對抗式查證最實用一部分 —— 以下 claim 被多數反證,**唔可採信**:

1. **「push 嘅 permission filter metadata 被當 Entra 認證(而非純字串比對),自動 token-trim」** ❌(0-3)— **最重要**:GA 路徑就係純字串比對。唔好假設 push 嘅 `allowed_principals` 字串欄自動獲 Entra-token 驗證。要 server-side token-trim 就要食 preview。
2. **「`GET /groups/{id}/transitiveMemberOf` 係 v1.0 GA 跨所有 group type 展開」** ❌(0-3)— 應以 `transitiveMembers` 端點為可靠依據;nested group 展開在 scale 下有 quirk。
3. **「Glean 用 webhook 即時反映撤權」** ❌(1-2)— vendor 自報未獨立 benchmark,gated on `Sites.FullControl.All`;唔採信即時撤權。
4. **「Glean 用 `Member.Read.Hidden` 補捉 hidden group membership」** ❌(1-2)— vendor 自報未獨立佐證。
5. **「微軟員工確認 Graph 唔支援 track library permissions,只建議提 feature request」** ❌(0-3)— 過度簡化原 thread,唔可當官方結論(但「library 層 delta 唔可靠」本身由另一 claim 3-0 確認)。

---

## 5. 主路線可行性裁決

**裁決:可行,採用「修正版本」。**

```
最穩妥版本(全 GA,毋須 preview):
  Graph (Sites.Selected, application) 拉 SharePoint/OneDrive 文件 + /permissions ACL
    → 自家 Docling ingestion pipeline(圖文還原 / profile / 可調配置全保留)
    → 自己用 Graph transitiveMembers 把 nested group 展成 flat principal set
    → push chunks + allowed_principals(Entra GUID 字串)入 Azure AI Search
    → query-time:string-match security filter(GA)按用戶 principal set trim
  撤權:排程 full re-ingest(delta 對 library 層唔可靠)+ 接受有界延遲
```

**主要風險**:
1. **stale permission**(結構性,無即時方案)→ 撤權延遲要產品上明示 + 排程補。
2. **chunk-level ACL 傳播**最佳實踐未有 production case(§7 缺口②)。
3. **nested group 展開 + 防爆量**係我哋一側工作量(push-model 代價)。
4. **Anyone link 等特殊 principal** 要明確處理規則。
5. 若日後想要 server-side 自動 token-trim 嘅便利 → 押注 preview(無 SLA),需 track GA 進度。

---

## 6. 誠實 caveats

- **時間敏感 / preview 成熟度**:Entra-native ACL token-trim 路徑截至 2026-06-11 文件全部 PREVIEW,狀態會變,寫 ADR 前要重新核對 GA 進度。唯一 GA = string-match security filters(= 我哋現有做法)。
- **best-case framing**:Glean「24 小時」係 vendor 自報 default cadence,非第三方 benchmark;任何 vendor capability claim 都當自報。
- **領域適用性**:多個高可信 claim(M365 Copilot semantic index 行為 / external groups / sharing link 對 search 影響)描述嘅係 M365 Copilot / Graph connectors surface,**同我哋自建 Azure AI Search push pipeline 係唔同 surface** —— 對我哋價值係「ACL 映射參考模型 + 特殊 principal 處理規則」,非直接規範我哋 indexer 行為。
- **數字證據**:延遲方面官方只給定性「timing lag」唔畀秒數;唯一具體數字(Glean 24h)係單一 vendor 自報。stale permission 無精確業界 SLA 數字。
- **安全事故**:本輪搵唔到具名「因 stale permission 出 production 安全事故」嘅帖,只有官方 + vendor 對風險嘅承認;此為證據缺口非反證。

---

## 7. 未答證據缺口(寫 ADR 前要補)

1. **GA 時間線** — Entra-native ACL/RBAC token-trim 路徑預計幾時 GA?決定主路線押注 GA 字串比對抑或等 preview token-trim GA。
2. **chunk-level ACL 傳播最佳實踐** — 文件切多 chunk,每 chunk 是否重複完整 `allowed_principals`?大文件 + 大 group set 下 index 膨脹與 query filter 效能?(子題 A 核心未答)
3. **library/folder 層撤權補機制** — delta 唔可靠,業界 push-model 實際用咩補(SharePoint webhook + full per-site re-crawl?排程 full re-ingest 頻率?)+ 實測延遲與成本?
4. **分階段策略業界實證**(子題 F)— 「先手動匯入後自動同步」是否 common pattern?有冇 incremental migration 經驗帖?

---

## 8. EKP-specific 比對 + 下一步

### 8.1 同上一輪(2026-06-27 web-search)比對

| 上一輪結論 | 本輪 deep-research 判決 |
|---|---|
| Azure AI Search 原生支援 SharePoint ACL,query 自動 trim = 好消息 | **修正**:自動 token-trim 係 PREVIEW;GA 只有字串比對(= 我哋現有 `allowed_principals`)→ 好消息變成「我哋已經做緊 GA 正解」 |
| 唔好用 turnkey indexer(繞過 ingestion 核心),行 push-model | **確認**:push-model 獲官方明文背書,同 locked stack 全相容 |
| 權限映射連到 RBAC track(`allowed_principals`) | **強化**:`allowed_principals` 字串 ACL 就係 GA 路徑;RBAC track 鋪嘅路啱啱就係 SharePoint 連接落地要用嘅地基 |
| stale permission = 業界共通難關,delta query 可緩解 | **部分推翻**:stale 確係結構性;但 **delta query 對 library 層唔可靠**,唔可當可靠即時同步 |

### 8.2 同 EKP 現有 RBAC track 嘅銜接

- 我哋 W88-W95 做緊嘅 **`allowed_principals` 文件級 ACL + query-time security trimming** 啱啱就係本研究確認嘅 **GA 主路線**。
- SharePoint 連接落地時:SharePoint ACL(Graph `/permissions`)→ 正規化 Entra GUID + 展 nested group → 填入我哋 `allowed_principals` → 沿用現有 query-time trimming。
- 即係 **enterprise RBAC track 同 SharePoint 連接係同一條路嘅兩段**,唔係兩件獨立工作。

### 8.3 下一步(全需 Chris approve / 寫 ADR,非本研究範圍)

1. 寫**方向 / 可行性分析文件**或直接起草 **ADR**(來源抽象 H1 + Microsoft Graph SDK H2),骨架 = §5 修正版本 + §7 缺口先補。
2. **唔好**喺定方向階段動手寫 code / 開 implementation plan。
3. 分階段建議:按需手動匯入(Tier 1.5)先行 → 權限映射跟 RBAC track 合流 → 自動同步(Tier 2,H4)最後。

---

## 附錄:來源分層(可信度)

**高(微軟官方 Learn doc / primary)**:
- [Document-Level Access Control — Azure AI Search](https://learn.microsoft.com/en-us/azure/search/search-document-level-access-overview)
- [Index-level ACL & RBAC push API — Azure AI Search](https://learn.microsoft.com/en-us/azure/search/search-index-access-control-lists-and-rbac-push-api)
- [Query-time ACL & RBAC enforcement — Azure AI Search](https://learn.microsoft.com/en-us/azure/search/search-query-access-control-rbac-enforcement)
- [Security filters for trimming results — Azure AI Search](https://learn.microsoft.com/en-us/azure/search/search-security-trimming-for-azure-search)
- [SharePoint indexer ACL ingestion — Azure AI Search](https://learn.microsoft.com/en-us/azure/search/search-indexer-sharepoint-access-control-lists)
- [What's new — Azure AI Search](https://learn.microsoft.com/en-us/azure/search/whats-new)
- [`Sites.Selected` permissions overview — Microsoft Graph](https://learn.microsoft.com/en-us/graph/permissions-selected-overview)
- [External groups for connectors — Microsoft Graph](https://learn.microsoft.com/en-us/graph/connecting-external-content-external-groups)
- [`transitiveMembers` / `transitiveMemberOf` — Microsoft Graph](https://learn.microsoft.com/en-us/graph/api/group-list-transitivemembers?view=graph-rest-1.0)
- [Shareable links (Anyone / Specific people / Org) — SharePoint](https://learn.microsoft.com/en-us/sharepoint/shareable-links-anyone-specific-people-organization)
- [`driveItem: delta` — Microsoft Graph](https://learn.microsoft.com/en-us/graph/api/driveitem-delta)
- [Q&A: Unable to track Document Library permission change (微軟員工回覆)](https://learn.microsoft.com/en-us/answers/questions/2224718/unable-to-track-document-library-permission-change)

**中高(微軟工程 devblog / TechCommunity)**:
- [Announcing enterprise-grade Entra-based document-level security in Azure AI Search](https://techcommunity.microsoft.com/blog/azure-ai-foundry-blog/announcing-enterprise-grade-microsoft-entra-based-document-level-security-in-azu/4418584)
- [Sensitivity labels & SharePoint ACLs in Azure AI Search](https://techcommunity.microsoft.com/blog/azure-ai-foundry-blog/sensitivity-labels-preservation-and-sharepoint-acls-in-azure-ai-search/4471216)
- [Propagating SharePoint Document Permissions to AI Search and RAG Pipelines — ISE Developer Blog](https://devblogs.microsoft.com/ise/sharepoint-doc-level-access/)

**中(vendor / 框架 blog)**:
- [Glean SharePoint connector — permissions](https://docs.glean.com/connectors/native/sharepoint/security/permissions)
- [Glean — application vs delegated](https://docs.glean.com/connectors/native/sharepoint/security/app-vs-delegated)
- [Permissions-Aware SharePoint Retrieval — LlamaIndex](https://www.llamaindex.ai/blog/permissions-aware-content-retrieval-with-sharepoint-and-llamacloud)
- [Bring SharePoint data to agents with Foundry IQ — Medium](https://medium.com/@arnaud.tincelin/bring-your-sharepoint-data-to-your-agents-with-foundry-iq-c03bedc3320f)

**參考(社群 / 個人帖)**:
- [How to maintain document-level RBAC in enterprise RAG — Truto](https://truto.one/blog/how-to-maintain-document-level-rbac-in-enterprise-rag-pipelines/)
- [The Permission Layer Problem — ragaboutit](https://ragaboutit.com/the-permission-layer-problem-why-your-enterprise-rag-is-a-security-time-bomb/)
- [Graph webhook + delta query — Voitanos](https://www.voitanos.io/blog/microsoft-graph-webhook-delta-query/)

---

**研究 Run ID**: `wf_0757c70d-677`(deep-research harness,2026-06-28)
**統計**: 6 angles / 23 sources fetched / 108 claims extracted / 25 verified / 20 confirmed / 5 killed / 11 after synthesis / 106 agent calls
