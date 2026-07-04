---
artifact: security-governance-review-framework
version: 0.2 (draft — EKP 現狀 claim 已 code-verified 2026-07-01)
status: draft
created: 2026-07-01
codebase_verified: 2026-07-01(§2/§3/§4 EKP 現狀逐條讀 code 核對,證據見 §11 驗證註記)
owner: Chris(技術 Lead)
purpose: 為 EKP 交付 corporate Security team + Risk & Governance team 審查做準備 — 統一整合層(ADR-0070)接入公司內容後嘅企業級安全 + APAC 合規檢查框架
research_basis: 2 輪 deep-research(2026-07-01)+ 現有 RISK_REGISTER / enterprise-rbac FINDINGS 對照
evidence_tags:
  - "✅ 已核實 = 兩輪 deep-research primary-source 3-0 verified"
  - "📚 據知識 = 業界well-established,兩輪未 verify,標『待確認』"
  - "⚖️ 需法務 = data-protection 法律解釋,必須 Ricoh 法務/DPO 拍板,不可由 AI fabricate"
---

# EKP 安全與治理檢查框架(Security & Governance Review Framework)

> **定調**:呢次檢查**唔係「由零證明系統安全」**,而係 **「把已做嘅(檢索層 security trimming P2/P3)整理成可交證據 + 補殘餘(SSO / 撤權 / 治理 / secrets / 跨境)+ 對照權威框架」**。EKP 已經有紮實地基(enterprise RBAC 160+ 測試、檢索層文件級 ACL、整合層零侵入 ingestion 核心),呢份 framework 係把佢地圖化,對接 security + risk & governance 團隊嘅語言。

---

## 0. 範圍與前提

| 項目 | 定案 |
|---|---|
| 觸發 | 統一整合層(ADR-0070)接入公司 SharePoint 內容 → 系統開始代表用戶讀公司既有權限內容,風險面質變 → 需 security + risk & governance 審查後先可 production |
| 合規管轄 | **APAC 為主**(Singapore PDPA / Japan APPI / HK PDPO)+ 業界 AI 安全標準;EU AI Act / GDPR 非主軸 |
| 對照框架 | **業界標準基線** — OWASP LLM Top 10 + NIST AI RMF + ISO 42001/27001/27017/27018 + Microsoft baselines |
| 部署形態 | **Hybrid / on-prem 元件** — 檢查同時涵蓋 cloud shared-responsibility 控制 **同** 自管基礎設施控制(host hardening / patching / 網絡隔離 / secrets-at-rest / 實體+邏輯存取) |
| 現有資產 | `RISK_REGISTER.md`(R1-R15,operational + RAG 品質為主,**無 security cluster**)、`enterprise-rbac/FINDINGS.md`(P2/P3 檢索層 ACL 已落地)、`docs/09-analysis/` 整合層研究 + live runbook |

---

## 1. 適用權威框架基線

> 逐個框架標明**管咩** + **對 EKP 意涵** + **引用狀態**。交俾審查團隊要標明出處版本,呢個表就係 citation index。

| 框架 | 版本 / 日期 | 管轄 | 對 EKP 意涵 | 狀態 |
|---|---|---|---|---|
| **OWASP Top 10 for LLM Applications** | 2025(2024-11-17,現行) | LLM 應用威脅榜 | LLM01 Prompt Injection + **LLM08 Vector and Embedding Weaknesses(RAG 專屬)** | ✅ |
| **OWASP RAG Security Cheat Sheet** | ~2026-05 新增(無 on-page 版本戳,version-volatile) | RAG 具體控制 | retrieval-時強制存取控制 + 每 chunk ACL metadata + cascading deletion + 權限變更 cache invalidation + retrieved content 當 data-only + cap 3-5 chunks | ✅ |
| **NIST AI RMF 1.0** | 2023-01-26 | AI 風險治理(Govern/Map/Measure/Manage) | 治理骨架,map 到 12 類 GenAI 風險 | ✅ |
| **NIST GenAI Profile(AI 600-1)** | 2024-07-26 | GenAI 12 類風險 | Data Privacy / Information Security(收 indirect prompt injection)/ Information Integrity / Value Chain 最貼 RAG | ✅ |
| **MITRE ATLAS** | v5.1.0(2025-11) | AI/ML 對抗式 TTP | threat model 用,把威脅 map 到具名技術 | ✅ |
| **ISO/IEC 27017** | 2015(revision 進行中,2015 仍現行) | 雲端安全(37 個 27002 控制 + 7 個 CLD.* 雲端專屬) | shared-responsibility 導向,對 hybrid 責任分割直接相關 | ✅ |
| **ISO/IEC 27018** | 2025(3rd ed,retitled) | 公有雲 PII processor 保護 | Azure OpenAI / Azure AI Search 作為 Ricoh 文件嘅 PII processor;**要確認 Azure OpenAI 是否在 27018 attestation scope 內** | ✅ |
| **ISO/IEC 42001** | 2023(AIMS) | AI 管理系統 | governance 團隊好可能揸呢個做認證基準;Annex A ~38 控制,對應 NIST RMF | 📚 待向認證方確認 |
| **ISO/IEC 27001** | 2022(ISMS) | 資訊安全管理系統 | 93 Annex A 控制(4 主題);EKP 基礎資安對照 | 📚 待確認 |
| **Microsoft Responsible AI Standard** | v2(2022-06,living doc) | 負責任 AI 6 原則 + **Impact Assessment 強制範本** | **Impact Assessment 範本可直接當 DPIA / AI-impact 交付物** | ✅ |
| **Azure OpenAI security baseline** | Microsoft Cloud Security Benchmark v1.0 | Azure OpenAI 控制 | Private Link / CMK / managed identity **全部非 default,要自己開** | ✅ |
| **Azure AI Search security** | GA(security filter)/ preview(built-in ACL) | 檢索層安全 | **GA security filter = 你哋 `allowed_principals` 設計,官方 recommended** | ✅ |
| **Singapore PDPA** | Advisory Guidelines on AI(2024-03-01) | 個資保護(全 AI 生命週期) | 資料最小化 / 去識別化 / DPIA / **dev 環境標準 = production** | ✅(advisory) |
| **Japan APPI** | 最新修訂 | 個資 + 跨境傳輸 | ingest 含個資公司文件 + 跨境 | ⚖️ 需法務 |
| **Hong Kong PDPO** | 6 DPPs + s.33 + PCPD AI 指引 | 個資保護 | 6 大保護原則 + 跨境(s.33 狀態)+ PCPD 2024-06 AI 個資框架 | ⚖️ 需法務 |

---

## 2. RAG 專屬威脅目錄(映射框架 + EKP 現狀)

> 呢個係 threat model 嘅種子。每個威脅標:框架映射 / EKP 現狀 / 殘餘風險 / 對應控制。

| # | 威脅 | 框架映射 | EKP 現狀 | 殘餘風險 / 要補 |
|---|---|---|---|---|
| T1 | **間接 / 儲存式 prompt injection**(惡意指令藏入被 ingest 文件,含白底白字隱藏文字) | OWASP LLM01:2025 + NIST Information Security + ATLAS | ⚠️ 整合層由 SharePoint 拉文件 = **新注入面**;現無 ingest-時內容驗證 / 隱藏文字偵測(2026-07-01 grep 確認無) | 🔴 高:ingest 前驗證 + 偵測隱藏內容;retrieved content 當 data-only(delimiter);考慮 Azure AI Content Safety(shared-responsibility 明列係 EKP 責任) |
| T2 | **檢索層 confused deputy / cross-context 洩漏** | OWASP LLM08:2025 | ✅ **大致已堵**:P2 `allowed_principals` security trimming(`hybrid.py`)+ `classification` 欄位 + `/query` KB 守衛(G1)+ P3a doc_acl(G6)+ P3b 群組繼承(G7) | ⚠️ **fail-OPEN**(空 `allowed_principals` 當 public)+ admin bypass → review 要確認呢兩個係 intended;要交檢索層 access-control test 證據 |
| T3 | **權限映射保真度**(source ACL → index) | OWASP RAG Cheat Sheet §4 | 整合層 `get_principals` flatten 到 group 級(ADR-0070) | 要驗證映射正確性 + 邊界情況(org/public/external_group principal 端到端未驗) |
| T4 | **Stale permission / 無即時撤權** | OWASP RAG Cheat Sheet §4/§11 + Azure(customer 責任) | 🔴 push-model `allowed_principals` ingest 時固化,無 live ACL 查詢 | **最高優先殘餘**:定義 **re-sync / 撤權 SLA** + cascading deletion(刪 source 連帶清 chunk/embedding/cache)+ 權限變更 cache invalidation |
| T5 | **敏感資料經 retrieval + 合成外洩** | NIST Data Privacy + Singapore PDPA | ✅ 2-level classification(internal/restricted)wired 落檢索 filter + restamp endpoint;default internal | 分類 tagging 覆蓋率 + 必要時 DPIA + PII 掃描 |
| T6 | **Citation / source 洩漏** | OWASP LLM08 | citation 用 anchor chunk_id(architecture.md §3.5) | 確認 citation 唔洩露無權 source metadata |
| T7 | **Secrets 管理** | ISO 27001 + Azure baseline(IM) | ✅ Key Vault provider 抽象 + IaC(`backend.bicep` 6 secret KV ref + managed identity);dev 跑 `.env` fallback,未 apply(R-B1) | activate KV + 確認全 secret 經 provider + rotation 政策 |
| T8 | **Model DoS / cost abuse** | OWASP LLM10 + NIST | ✅ rate limiting 已實作(`middleware/rate_limit.py`,IaC 50/min + 5 concurrent);quota(R5 Open) | quota alert + 壓測驗證 |
| T9 | **供應鏈 / vendor 風險** | NIST Value Chain + ISO 27017 | Azure / Cohere / Langfuse | 第三方 AI 服務 security due-diligence + Azure ISO attestation 證據 |

---

## 3. EKP 現狀 vs 控制對照(Gap Analysis 雛形)

### 3.1 ✅ 已符合 / 已實作(可直接交證據 — 2026-07-01 code-verified,詳見 §11)
- **檢索層文件級 security trimming**(P2/P3)= Azure AI Search **GA security filter recommended pattern**(`hybrid.py` `allowed_principals/any(p: search.in(...))`)。⚠️ **fail-OPEN**:空 `allowed_principals` 當 public(向後兼容);admin → 見全部。
- `/query` KB 守衛(G1,`query.py`)+ 群組繼承(G7,`principals_for_user` = `[oid] ∪ group keys`)。
- **2-level classification**(internal/restricted)wired 落檢索 filter + `PATCH .../classification` chunk restamp。
- **Audit log middleware**(每 request + H5 redaction)+ Postgres 持久化 + admin 查詢端點。
- **Rate limiting** 已實作(`middleware/rate_limit.py`,IaC 50/min + 5 concurrent)。
- **Secrets:Key Vault provider 抽象 + IaC**(`key_vault_factory.py` + `backend.bicep` 6 secret 走 KV reference + user-assigned managed identity)。
- **Entra ID SSO JWT 驗證器 code 完整**(`msal_provider.py`,`feature_auth_mock` default False)。
- Enterprise RBAC 地基:5 表 + 4 級角色 + 92 權限 + 160+ pytest(`enterprise-rbac/FINDINGS.md`,2026-06-23 實測)。
- 整合層零侵入 ingestion 核心(ADR-0070)+ `get_principals` group-level flatten(`transitiveMembers`)。

### 3.2 🟡 已建但未 activate / 未驗證(要 flip + 出證據)
- **Key Vault** — 抽象 + IaC 已建,但 dev 跑 `.env` fallback(`key_vault_url` 未設),部署 IaC 因 R-B1 IT cred 未 apply → 未實際驗證。要:activate + 確認**所有** secret 都經 provider + rotation。
- **真實 SSO 端到端** — 驗證器 code 有,但從未接真實 Entra ID tenant 做端到端登入(卡 R-B1 IT cred);dev 跑 `feature_auth_mock=true`。SCIM 自動群組同步未做。
- **Classification 覆蓋率** — 功能有,但 default 全 `internal`,要驗證實際有幾多 restricted doc 已 tag + 2 級夠唔夠對應 PDPA 敏感度。
- **Audit / observability** — 功能有,交付物 D6 = 整理成審查證據(導出樣本 + 對應存取事件)。

### 3.3 🔴 真缺口(由零要做,review 前處理或明列)
- **Stale-permission / 撤權 SLA** — 未定義(T4,最高優先)。
- **Ingest-時 prompt injection 防線** — 確認無(T1,grep 全 false-positive)。
- **Application-side content safety** — 確認無(Azure AI Content Safety 未整合);shared-responsibility 明列係 EKP 責任。
- **P5 治理層**(auditor 職責分立 + 存取覆核)— 設計咗 ADR-0068,**impl 暫緩等真實審計 driver → 呢次 review 本身就係 driver,值得重啟**。
- **Private Link 到 PaaS + CMK** — 未設(見 §4.2)。
- **On-prem 自管控制** — host hardening / patch / 網絡隔離 / backup-DR 未系統化(見 §4.3)。
- **正式交付物**(DPIA / threat model / data-flow / control matrix)— 未產出(見 §5)。

---

## 4. Azure 責任分擔 + 部署控制(hybrid / on-prem)

### 4.1 Shared responsibility(✅ 已核實)
- Customer **永遠**擁有:data / endpoints / accounts / access management(不論部署類型)。
- RAG grounding(persistence layer / semantic index / plugins)= **AI application layer** → **EKP 自己要起 application safety system**(prompt-injection 防護 + content safety),唔係 Microsoft 包。
- Prompt security + prompt-injection mitigation = customer 責任。

### 4.2 Azure PaaS baseline(✅ baseline 已核實;EKP 現狀已 code/IaC 核對)
> ⚠️ 部署 IaC(`infrastructure/aca/backend.bicep`)已宣告部分控制,但因 R-B1 IT cred 未 populate,**實際 deploy 未 apply → 屬「已設計於 IaC,未實際部署驗證」**。
| 控制 | baseline ref | EKP 現狀 |
|---|---|---|
| Managed identity + KV secret refs | IM-1 / IM-3 / PA-7 | ✅ IaC 已宣告(user-assigned MI + 6 secret 走 KV reference,H5 compliant);未 apply |
| Internal ingress(唔對公網) | NS-2(部分) | ✅ IaC `external: false`(Front Door + auth gate upstream);未 apply |
| Private Link 到 Azure OpenAI / AI Search PaaS | NS-2 | ❌ IaC 未宣告 → 要做(container internal ≠ PaaS private endpoint) |
| CMK 加密 at rest | DP-5 | ❌ 未設 → 現用 platform key(default);要決定是否 CMK + decision record |
| Azure AI Search security filter | GA pattern | ✅ 已對齊 `allowed_principals`(`hybrid.py` `search.in`);filterable/retrievable 設定見 §11 |

### 4.3 On-prem 自管控制(📚 據實務標準,GAP 4 未 verify 但 shared-responsibility 已界定範圍)
- **Host hardening** — CIS Benchmarks 對 OS / container。
- **Patch management** — 定 cadence(critical CVE SLA)。
- **Network segmentation** — zero-trust / 分區(DB / backend / frontend 隔離)。
- **Secrets-at-rest** — vault + rotation(T7)。
- **邏輯 + 實體存取控制** — 最小權限 + 審計。
- **Backup / DR** — RPO / RTO 定義。

---

## 5. 交付物清單(Evidence Package — 交俾審查團隊嘅嘢)

> 📚 據實務標準(OWASP LLM Cybersecurity & Governance Checklist + Microsoft AI security guidance + 一般 security review 慣例)。呢個係 review 團隊會問你攞嘅嘢。

| # | 交付物 | 內容 | 來源 / 範本 |
|---|---|---|---|
| D1 | **Data-flow diagram** | 由 SharePoint source → 整合層 → ingestion → index → retrieval → LLM 合成 → 答案,標明 trust boundary + 個資流向 | 自製 |
| D2 | **Threat model** | STRIDE + MITRE ATLAS + OWASP LLM Top 10 映射(用 §2 威脅目錄做種子) | 自製 |
| D3 | **DPIA / PIA** | 個資影響評估 | **可採用 Microsoft Responsible AI Impact Assessment 範本** + Singapore PDPA §7 要求 |
| D4 | **Control-mapping matrix** | 控制 ↔ 框架(OWASP / NIST / ISO / Azure baseline)逐項對照 + 狀態 | 自製(用 §1 + §3) |
| D5 | **檢索層 access-control 證據** | security trimming test 結果(有權/無權用戶 query 對照)+ north-star §15 圖文還原不退證明 | P2/P3 測試 + 新測 |
| D6 | **Logging & audit 證據** | `audit_log` + Langfuse trace,證明可追溯存取 + 操作 | 現有 + 整理 |
| D7 | **Model & data governance 文件** | KB 分類政策 / 資料保留 / 模型版本 / per-KB config lifecycle | 現有 doc 整理 |
| D8 | **Vendor / third-party assessment** | Azure(ISO 27017/27018 attestation)/ Cohere / Langfuse 嘅 security due-diligence | Azure compliance docs + 確認 attestation scope |
| D9 | **Secrets management attestation** | Key Vault 遷移 + rotation + 無 hardcoded secret 證明 | 遷移後產出 |

---

## 6. 分階段檢查計劃(Phased Review Plan)

> 最高風險優先(prompt injection T1 / 檢索繞過 T2 / 撤權 T4 打頭)。

| Phase | 內容 | 驗證 | 狀態 |
|---|---|---|---|
| **Phase 0** | 框架基線(本 doc)— 適用標準 + 威脅目錄 + EKP 對照 | 本 doc committed | ✅ 進行中 |
| **Phase 1** | 資產 + 資料流盤點 + threat model(D1 + D2)— 擴充 enterprise-rbac P1 威脅模型,唔重做 | data-flow + threat model draft | 待 |
| **Phase 2** | Gap analysis + control matrix(D4)— 逐控制項標已符合/部分/缺口,**高風險 T1/T2/T4 先** | control matrix + gap 清單入 RISK_REGISTER(新 security cluster) | 待 |
| **Phase 3** | Remediation backlog — 缺口排優先序入 BACKLOG;架構級走 ADR(H1) | backlog entries + ADR(如需) | 待 |
| **Phase 4** | Evidence package 整理(D3/D5/D6/D7/D8/D9)+ **法務/DPO 審 §7** | evidence package 齊 + 法務 sign-off | 待 |
| **Phase 5** | 提交 security + risk & governance 團隊審查 | 審查通過 → production gate | 待 |

---

## 7. 需法務 / DPO 確認事項(⚖️ 不可由 AI fabricate)

> data-protection 法律解釋**必須**行 Ricoh 法務 / DPO。以下係 orientation,唔係法律意見。

- **邊個管轄實際適用** — 取決於 data subject 喺邊(Ricoh 喺 Singapore / Japan / HK / Australia 邊度營運 + 資料主體所在)。
- **Japan APPI** — 跨境傳輸個資嘅同意 / 保障要求(如涉日本員工資料)。
- **Hong Kong PDPO** — 6 大保護原則 + s.33 跨境條款狀態 + PCPD 2024-06 AI 個資保護框架指引。
- **Singapore PDPA** — 是否需要 DPIA(§7:去識別化不可行時用原始個資即需 DPIA)。
- **Azure region 資料落地決定** — 揀邊個 APAC region(Southeast Asia / Japan East / etc)+ Azure OpenAI data-processing / residency 承諾 + 跨境 data flow 是否符合上述法規。

---

## 8. 未決研究缺口(可選第三輪 targeted research)

- **ISO 42001 Annex A 逐項控制** + certification 對 governance 團隊意義(可 targeted research 或問認證方)。
- **ISO 27001:2022 最相關控制** 對 hybrid RAG。
- **Japan APPI / HK PDPO 具體條文**(research 可補 orientation,但最終仍需 §7 法務)。
- **Azure OpenAI 是否在 Azure ISO 27018 attestation scope 內**(查 Microsoft compliance docs)。

---

## 9. 來源(兩輪 deep-research)

**已核實 primary sources**:
- OWASP: genai.owasp.org(LLM Top 10 2025 / LLM01 / LLM08)、cheatsheetseries.owasp.org(RAG Security Cheat Sheet)
- NIST: nvlpubs.nist.gov(AI RMF 1.0 100-1 / GenAI Profile 600-1)、nist.gov/itl/ai-risk-management-framework
- MITRE: atlas.mitre.org
- ISO: iso.org(27018 std:88150 / 27017)、learn.microsoft.com/compliance(offering-iso-27017 / 27018)
- Azure: learn.microsoft.com(search-security-trimming / search-document-level-access-overview / search-query-access-control-rbac-enforcement / azure-openai-security-baseline / shared-responsibility-ai / shared-responsibility / azure-cognitive-search-security-baseline)
- Microsoft Responsible AI Standard v2 PDF(microsoftcorp CDN)
- Singapore PDPC: pdpc.gov.sg(Advisory Guidelines on AI 2024-03-01)

**已抓但未 synthesize(第三輪可用)**:pcpd.org.hk(HK AI 個資框架 2024-06-11 + 6 DPPs)、learn.microsoft.com/azure/foundry/responsible-ai/openai/data-privacy、azure.microsoft.com data-residency、isms.online(ISO 42001 Annex A / 27001 Annex A,secondary)、schellman.com(ISO 42001,secondary)

---

## 10. 版本敏感 / 可靠性註記

- **Azure AI Search 存取控制**:GA security filter(production-safe,對齊 `allowed_principals`)vs built-in ACL/RBAC(**preview 2026-05-01-preview,無 SLA,唔可 production**)— production 決定前要 re-verify。
- **OWASP RAG Cheat Sheet**:~2026-05 新增,無 on-page 版本戳,version-volatile,引用時記日期。
- **Azure OpenAI baseline** 頁面有 Microsoft banner「based on Cloud Security Benchmark v1.0,may contain outdated guidance」— 但 NS-2/DP/IM 控制事實仍 current。
- **Responsible AI Standard v2**(2022-06)係 Microsoft **內部**義務框架,對 Ricoh(external operator)係 benchmark 非法律 mandate;但 Impact Assessment 範本可直接採用。
- **NIST AI 600-1** 開發依據 EO 14110 已於 2025-01-20 撤銷,但 600-1 本身**未撤回**,仍可引用(flag policy churn)。
- **ISO 27017** revision 進行中,2015 仍現行。

---

## 11. EKP 現狀驗證註記(2026-07-01 code-verified)

> §2/§3/§4 對 EKP 現狀嘅 claim **逐條讀 code 核對**(唔係搵到檔案就算),以下係證據 + 對 v0.1 草案嘅更正。

| 項目 | 判定 | 證據(file:line)| v0.1 更正 |
|---|---|---|---|
| 檢索層 `allowed_principals` security trimming | ✅ 真 wired | `retrieval/hybrid.py:100`(`allowed_principals/any(p: search.in(...))`)+ `indexing/schemas.py:102` | — |
| ⚠️ security trimming = **fail-OPEN** | 需標明 | `schemas.py:96-102`(空 `allowed_principals` 當 public)+ `hybrid.py:100`(`not allowed_principals/any()`) | v0.1 漏咗;review 必須知空 ACL chunk 全公開 |
| admin bypass | 需標明 | `query.py:253`(admin → None 見全部) | 補上 |
| `/query` KB 守衛(G1) | ✅ 真 | `query.py:237,569`(`assert_kb_access(...,"query")`) | — |
| 群組繼承(G7,P3b) | ✅ 真 | `query.py:256`(`principals_for_user` = `[oid] ∪ group keys`) | — |
| 2-level classification | ✅ 真 wired | `schemas/doc_classification.py:16`(`Literal["internal","restricted"]`)+ `PATCH .../classification` restamp + `schemas.py:106` | v0.1 標 🟡 過輕 → 已落地 |
| audit log | ✅ middleware | `api/middleware/audit_log.py`(每 request + H5 redaction)+ `storage/audit_log_postgres.py` | v0.1 講啱 |
| rate limiting | ✅ 實作 | `api/middleware/rate_limit.py` + `backend.bicep:113`(`RATE_LIMIT_PER_MINUTE=50`)| v0.1 標「W7+ 設計」→ 已實作 |
| Key Vault | ✅ 抽象 + IaC | `storage/key_vault_factory.py`(KV provider + `.env` fallback)+ `backend.bicep:61-94`(6 secret KV refs)| v0.1 標「遷移未做」→ 抽象+IaC 已建,dev 跑 `.env`,未 apply |
| managed identity | ✅ IaC | `backend.bicep:38-43`(user-assigned MI)| 補上 |
| Entra ID SSO 驗證器 | ✅ code 完整 | `api/auth/msal_provider.py`(JWKS + RS256 + iss/aud/exp 驗);`settings.py:454` `feature_auth_mock=False` default | v0.1 標「100% mock」不準 → code 有,未接真 tenant(R-B1) |
| 整合層 `get_principals` group-level | ✅ 真 | `integration/sharepoint/permissions.py:83`(`transitiveMembers`,group 級)| — |
| ingest-時 prompt injection 防線 | ❌ 無 | grep `injection` 全 false-positive(blob container injection)| v0.1 講啱(真缺口)|
| Azure AI Content Safety | ❌ 無 | grep `content.?safety` / `prompt.?shield` 0 files | v0.1 講啱 |
| Private Link 到 PaaS / CMK | ❌ 無 | `backend.bicep` 只 container internal ingress,無 PaaS private endpoint / 無 CMK | v0.1 大方向啱,細節見 §4.2 |

**淨結論**:EKP 已做嘅比 v0.1 草案講嘅**多**(classification / rate limit / audit / KV 抽象 + IaC / MSAL 驗證器 / managed identity 都已存在,只係部分未 activate / 未 apply)。真正由零要做:**ingest 注入防線 + content safety + 撤權 SLA + Private Link/CMK + 正式交付物**。**最需要 review 特別留意嘅安全 nuance = security trimming fail-OPEN(空 ACL = 公開)**。

---

**End of Security & Governance Review Framework v0.2(draft)**
**下一步**:用戶 review 本 framework → 決定是否正式開 `W{NN}-security-governance-review/` phase track(plan.md + checklist.md + progress.md)+ RISK_REGISTER 新增 security cluster + BACKLOG 加項(per §10 R7)。
