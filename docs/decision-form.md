# EKP Tier 1 — Stakeholder Decision Form

> **目的**:本文件將 EKP 規格 v5 嘅 21 條 Open Question 整理為**可填寫嘅 decision form**,
> 用嚟 collect stakeholder + 領域專家 + 技術 owner 嘅正式答覆,確保 W1 Day 1 啟動時冇 ambiguity。
>
> **使用方式**:Stakeholder 喺**「Decision」**欄位填 answer,**「Decided By」**填 owner,**「Date」**填日期,**「Status」**改成 `Resolved`。
> 任何已填寫嘅 decision **必須 commit** 入 repo,等 Claude Code 同團隊以 latest version 為準。

---

## 0. Executive Summary(畀 stakeholder 5 分鐘讀完)

### What this is

EKP(Enterprise Knowledge Platform)Tier 1 嘅 12 週 implementation 喺等 21 條 decision resolve 之後就可以 W1 Day 1 啟動。**6 條屬 critical path,W1 Day 1 必須有答案**;其餘 15 條可以喺 W1–W4 內陸續 resolve。

### Decision Volume

| Owner | 條數 | 預期 turnaround |
|---|---|---|
| Stakeholder(Project Sponsor / Lead) | **13 條** | 1 sit-down meeting,~45 分鐘 |
| 領域專家(Subject Matter Expert) | 3 條 | Sync with stakeholder 同一 meeting |
| 技術(Tech Lead / W1 自行 confirm) | 5 條 | W1 Day 1–W4 dev hands-on |

### 6 條 W1 Day 1 Critical(必先 resolve)

| Q# | 簡述 | Owner |
|---|---|---|
| **Q1** | Document format ratio(Word / PDF / PPT %) | Stakeholder + SME |
| **Q2** | 100 manuals access path(SharePoint / Drive / share folder URL) | Stakeholder |
| **Q3** | Azure AI Search resource provisioned 未?Resource name? | Stakeholder + IT |
| **Q4** | Azure OpenAI GPT-5.5 deployment ready 未?Deployment name? | Stakeholder + IT |
| **Q13** | Ground truth labeling resource allocation(stakeholder side) | Stakeholder |
| **Q14** | Specific SME owner for ground truth labeling | Domain Expert |

呢 6 條 unresolve 嘅話,**W1 整個 sprint 都會 block**(architecture.md §6.1 嘅 Day 1 Foundation Setup 做唔到)。

### Default Behavior(若 stakeholder 未答)

每條 OQ 都列咗 default,**unresolve 嘅情況下 Claude Code 會用 default 繼續做**,但會喺 commit message 標 `Note: depends on OQ-Q<N> default`。**Default 用得多 = risk 累積**,所以仍應盡早 resolve。

### Sign-off

填好之後喺 §5 簽名 + commit。**Stakeholder sign-off 前 W1 唔啟動**(避免 sunk cost retrofit)。

---

## 1. Stakeholder Decisions(13 條)

呢部分需要 **Project Sponsor / Project Lead** 簽核。建議一次 sit-down meeting 攪掂。

### Q1 — Document Format Ratio 🔴 CRITICAL

| Field | Content |
|---|---|
| **Question** | 100 份 Drive Project manual 喺 .docx / .pdf / .pptx 嘅實際比例係? |
| **Why it matters** | W1 priority:邊個 parser 做先(Docling .docx 先做,定 PDF 先做)。比例極不均(e.g. 95% Word)會 simplify W1–W2 work。 |
| **Default if unanswered** | 假設 ~80% Word + 15% PDF + 5% PPT,W1 主力做 Docling .docx parser |
| **Decision** | **40% Word + 30% PPT + 30% PDF**。Implication:W1 主力 Docling `.docx` parser(最大 single format),但 W2 PDF + PPT 同等 priority,**唔可以推到 W3**(PPT + PDF 合 60%,delay 即 60% corpus 唔 indexable)。 |
| **Decided By** | Chris(acting as Stakeholder per 2026-04-30 session) |
| **Date** | 2026-04-30 |
| **Status** | `Resolved` |

---

### Q2 — Document Source Access Path 🔴 CRITICAL

| Field | Content |
|---|---|
| **Question** | 100 份 manual 嘅實際 access path?(SharePoint URL? Google Drive folder? OneDrive? Network share? 個別下載?) |
| **Why it matters** | Ingestion pipeline Day 1 要 connect 到 source。手動 download zip 同 SharePoint API connector 係 2 種不同 effort。 |
| **Default if unanswered** | 假設 Chris 提供 zip / folder 包 100 份 manual,W1 用 manual upload。 |
| **Decision** | Stakeholder 提供文件原檔。Upload path **三選一**:(1) 直接上傳(POC default、Admin Console drag-drop)、(2) 共享 folder(network share pickup)、(3) SharePoint site。POC 階段 **(1) manual upload 即可**;**(3) SharePoint connector 屬 Tier 2 auto-sync trigger**(spec §11)。 |
| **Decided By** | Chris(acting as Stakeholder per 2026-04-30 session) |
| **Date** | 2026-04-30 |
| **Status** | `Resolved` |

---

### Q3 — Azure AI Search Resource 🔴 CRITICAL

| Field | Content |
|---|---|
| **Question** | 公司 Azure tenant 已有 Azure AI Search resource 未?如有,resource name + region + tier 係?如冇,邊個 owner 負責 provision? |
| **Why it matters** | Standard S1 base price ~USD 75/月。需 Service quota 同 RBAC 配置,新 provision 通常 1–3 工作日。 |
| **Default if unanswered** | 假設要新 provision,W1 Day 1 dev 自己用 `az search service create` 跑 setup.md §3.2 |
| **Decision** | **Azure AI Search service 已 provisioned**(POC stage)。**W1 D2 (2026-05-01) implementation detail delivered**:endpoint = `https://azureaisearchtesting.search.windows.net`(service name `azureaisearchtesting`),admin key 由 plaintext markdown 遷移至 root `.env`(gitignored,H5 remediation commit `09138d4`)。**W1 D5 (2026-05-02) full Resolution**:**tier = Standard S1**(per architecture.md §3.2 spec default,confirmed by Chris W1 D5 closeout session);**region = eastus2**(confirmed by Chris W1 D5 closeout session,matches endpoint hostname inference);F9 index `ekp-kb-drive-v1` already created HTTP 201 W1 D4 (commit `349c33e`). |
| **Decided By** | Chris(acting as Stakeholder per 2026-04-30 session;detail delivered 2026-05-01;tier+region full resolution 2026-05-02) |
| **Date** | 2026-04-30(initial)/ 2026-05-01(detail)/ 2026-05-02(tier+region) |
| **Status** | `Resolved` (full) |

---

### Q4 — Azure OpenAI GPT-5.5 Deployment 🔴 CRITICAL

| Field | Content |
|---|---|
| **Question** | 公司 Azure OpenAI resource 有 GPT-5.5 deployment 未?Deployment name 係咩(e.g. `gpt-5-5`)?Quota 配置?<br>同樣問:`text-embedding-3-large` 同 `gpt-5.4-mini`(CRAG judge) deployment 名? |
| **Why it matters** | W3 critical path:LLM synthesis 唔 deploy = 答案生成做唔到。Deployment quota 太細(< 50 TPM)Beta 階段會 rate limit。 |
| **Default if unanswered** | 假設 dev 自行 deploy(setup.md §3.3)。Deployment name 用 `gpt-5-5`、`text-embedding-3-large`、`gpt-5-4-mini`。Quota 50–100 TPM。 |
| **Decision** | **Azure OpenAI 完整 deployment 已 ready**。**W1 D2 (2026-05-01) implementation detail delivered**:endpoint = `https://chris-mj48nnoz-eastus2.cognitiveservices.azure.com/`,region = `eastus2`,api version = `2024-12-01-preview`,6 deployments(`gpt-5.5` / `gpt-5.4` / `gpt-5.4-mini` / `gpt-5.4-nano` / `text-embedding-3-small` / `text-embedding-3-large`,exact name 用 dot 而非 dash),api key 由 plaintext markdown 遷移至 root `.env`(H5 remediation commit `09138d4`)。**Note**:`gpt-5.5-pro`(per CLAUDE.md §5.2 H2 alternative eval judge)未 deploy POC stage,eval judge default 用 `gpt-5.4-mini`(spec-compliant)。**Outstanding minor**:per-deployment quota TPM(operational planning only,non-blocking)。 |
| **Decided By** | Chris(acting as Stakeholder per 2026-04-30 session;detail delivered 2026-05-01) |
| **Date** | 2026-04-30(initial)/ 2026-05-01(detail) |
| **Status** | `Resolved` (full) |

---

### Q5 — Cohere via Azure Marketplace Procurement

| Field | Content |
|---|---|
| **Question** | Cohere via Azure Marketplace 嘅 procurement / billing 流程確認 path?(POC 階段先用 direct API + corporate card,定即刻 initiate Marketplace?)Estimated procurement timeline? |
| **Why it matters** | W3 critical:Cohere reranker 唔 ready 影響 retrieval quality。Marketplace 一般 7–14 工作日 turnaround,direct API 即時可用。 |
| **Default if unanswered** | POC 用 Path A(direct API + corporate card),W3 並行 initiate Path B(Marketplace),W7 Beta 切到 Marketplace。 |
| **Decision** | 🟡 To be filled by stakeholder |
| **Decided By** | _(name)_ |
| **Date** | _(YYYY-MM-DD)_ |
| **Status** | `Open` |

---

### Q6 — Real User Query Collection Owner

| Field | Content |
|---|---|
| **Question** | W4 計劃加 20 條 real user query 入 eval set,**邊個 owner** 負責收集?**收集渠道**(Slack support channel? Email tickets? 訪談 5–10 個 power user? Tango.us usage log?)? |
| **Why it matters** | Eval set quality 直接影響 W4 Decision Gate。純 synthetic query 同真實用戶用詞會有 vocabulary mismatch,W4 metric 數字會偏樂觀。 |
| **Default if unanswered** | 假設 Chris W3 內向 5–10 個 internal user 訪談收集。 |
| **Decision** | 🟡 To be filled by stakeholder |
| **Decided By** | _(name)_ |
| **Date** | _(YYYY-MM-DD)_ |
| **Status** | `Open` |

---

### Q7 — Beta 50 Internal User 來源

| Field | Content |
|---|---|
| **Question** | W9 Beta 階段嘅 50 internal user 由邊度黎?(RAPO 內部 team 成員?其他 BU 友好部門?願意 hands-on testing 嘅 power user?) |
| **Why it matters** | Beta phase 嘅 real query log 係 production deployment 前最後一道 validation。Sample 唔 representative(e.g. 全部 dev 同事)= production 撞 user behavior gap。 |
| **Default if unanswered** | 假設 RAPO 內部 + 1–2 個友好部門。 |
| **Decision** | 🟡 To be filled by stakeholder |
| **Decided By** | _(name)_ |
| **Date** | _(YYYY-MM-DD)_ |
| **Status** | `Open` |

---

### Q8 — 4-Metric Replacement Confirmation

| Field | Content |
|---|---|
| **Question** | Stakeholder 正式接受用 4 個分指標(Recall@5 ≥ 90% / Faithfulness ≥ 95% / Correctness ≥ 80% / Image Association ≥ 85%)取代原本嘅「90% 準確率」? |
| **Why it matters** | POC W6 demo 嘅 success / fail 判定根據呢套 metric。Stakeholder 後期質疑「點解唔係 90% accuracy」會令 POC 結論 dispute。 |
| **Default if unanswered** | Yes,沿用 v5 spec §1.6。但 unresolved 會留 demo 質疑風險。 |
| **Decision** | 🟡 To be filled by stakeholder |
| **Decided By** | _(name)_ |
| **Date** | _(YYYY-MM-DD)_ |
| **Status** | `Open` |

---

### Q9 — Document Sensitivity / CMK Need

| Field | Content |
|---|---|
| **Question** | 100 份 manual 嘅 sensitivity classification?(Public / Internal / Confidential / Restricted?) 需唔需要 Customer-Managed Keys(CMK)? 有冇 PII / 客戶資料? |
| **Why it matters** | 影響 Azure AI Search、Blob、Key Vault 嘅 security 配置。CMK setup 多 ~3 工作日 IT 工。如有 PII,部分 logging 要 mask。 |
| **Default if unanswered** | 假設 `Internal` 級別,無 PII,唔需 CMK。 |
| **Decision** | 🟡 To be filled by stakeholder |
| **Decided By** | _(name)_ |
| **Date** | _(YYYY-MM-DD)_ |
| **Status** | `Open` |

---

### Q10 — EKP Visual Identity / Brand Guidelines

| Field | Content |
|---|---|
| **Question** | EKP 有冇 designated designer 出 brand guidelines(primary color、typography、logo)?如冇,W1 dev 用中性 design tokens(neutral grayscale + 一個 accent color),W4 由 designer pass。 |
| **Why it matters** | Frontend 質素 = stakeholder demo 第一印象。中性 token 可以 ship,但 W6 demo 之前唔上 designer 過 = 視覺 polish 達唔到 70–80% Dify quality target(spec §1.3)。 |
| **Default if unanswered** | W1 用 neutral tokens,W4 提醒 stakeholder 要 designer。 |
| **Decision** | 🟡 To be filled by stakeholder |
| **Decided By** | _(name)_ |
| **Date** | _(YYYY-MM-DD)_ |
| **Status** | `Open` |

---

### Q11 — Microsoft Entra ID Tenant Access(Beta+)

| Field | Content |
|---|---|
| **Question** | Beta(W7+)階段加 SSO,用咩 Microsoft Entra ID tenant?Ricoh 有統一 tenant?用 RAPO 子 tenant?新開 application registration?Owner of app registration? |
| **Why it matters** | W7 critical:auth 唔 ready 撞 Beta 50 user onboarding。App registration 通常 IT approve 3–7 工作日。 |
| **Default if unanswered** | 假設用 Ricoh 統一 tenant,W6 末由 IT initiate app registration。 |
| **Decision** | 🟡 To be filled by stakeholder |
| **Decided By** | _(name)_ |
| **Date** | _(YYYY-MM-DD)_ |
| **Status** | `Open` |

---

### Q12 — Tier 2 GraphRAG Decision Owner

| Field | Content |
|---|---|
| **Question** | Confirm Chris 為 Tier 2 GraphRAG / Knowledge Graph 嘅 decision owner(架構規格 §11.2 trigger matrix 滿 3 條 + Chris approve = trigger Tier 2)? |
| **Why it matters** | 防止 stakeholder 喺 production 階段「不如試下 GraphRAG」打亂 Tier 1 backlog。Decision owner 明確 = governance clear。 |
| **Default if unanswered** | Yes(沿用 v5 spec §11.2)。 |
| **Decision** | 🟡 To be filled by stakeholder |
| **Decided By** | _(name)_ |
| **Date** | _(YYYY-MM-DD)_ |
| **Status** | `Open` |

---

### Q13 — Ground Truth Labeling Resource Allocation 🔴 CRITICAL

| Field | Content |
|---|---|
| **Question** | Stakeholder 同意 dedicate 一個 SME 負責 W1–W4 嘅 eval set ground truth 標註?Estimated 2–3 工作日 effort across 4 週。 |
| **Why it matters** | 無 ground truth = 無 4 metric measurement = POC W4 / W6 Gate 數字唔可信 = POC 結論 disputable。R2 risk(architecture.md §8.1)直接 cover 呢點。 |
| **Default if unanswered** | 假設 yes,W1 Day 2 confirm 具體 SME(Q14)。 |
| **Decision** | **Yes** — stakeholder 同意 dedicate SME 負責 W1–W4 ground truth 標註(estimated 2–3 工作日 across 4 週)。Specific labeler 詳見 Q14。 |
| **Decided By** | Chris(acting as Stakeholder per 2026-04-30 session) |
| **Date** | 2026-04-30 |
| **Status** | `Resolved` |

---

## 2. Domain Expert Decisions(3 條)

呢部分需要**領域專家 / 業務 SME** 答。理想喺 stakeholder meeting 同步問。

### Q14 — Ground Truth Labeling Specific Owner 🔴 CRITICAL

| Field | Content |
|---|---|
| **Question** | Q13 已 confirm by stakeholder,**具體邊位 SME** 做標註?Email + 工時可用度? |
| **Why it matters** | Ownership clear 後 W1 Day 2 即啟動標註 workflow,避免 W4 Gate 撞死線。 |
| **Default if unanswered** | Block W1 Day 2 後 deliverable(eval set v0)。 |
| **Decision** | **Yes** — domain expert allocation confirmed by Chris。**W1 D2 (2026-05-01) specific labeler delivered**:Chris Lai(`chris.lai@rapo.com.hk`)親自擔任 SME labeler。中期 fallback unchanged:LLM-judge first pass + Chris verify(R2 risk mitigation per architecture.md §8.1)。**工時可用度**:Chris 自決,W1–W4 spread。 |
| **Decided By** | Chris(acting as Stakeholder per 2026-04-30 session;specific labeler self-assigned 2026-05-01) |
| **Date** | 2026-04-30(initial)/ 2026-05-01(labeler) |
| **Status** | `Resolved` (full) |

---

### Q15 — Manual Update Frequency

| Field | Content |
|---|---|
| **Question** | 100 份 manual 嘅典型更新頻率?(每月 batch update? 每 quarter? 罕見更新?) |
| **Why it matters** | 影響 re-index 策略 同 Day-2 ops runbook。罕見更新 = 手動觸發 OK;頻繁 = 要設計 auto-sync(Tier 2)。 |
| **Default if unanswered** | 假設 quarterly batch update。 |
| **Decision** | 🟡 To be filled by domain expert |
| **Decided By** | _(name)_ |
| **Date** | _(YYYY-MM-DD)_ |
| **Status** | `Open` |

---

### Q16 — Status Quo Baseline(用戶平日點搵呢啲資料)

| Field | Content |
|---|---|
| **Question** | 用戶現時點搵呢類 manual 內容?(Tango.us 直接搜? SharePoint 全文搜? 問同事? ChatGPT?) 平均花幾耐? |
| **Why it matters** | EKP 嘅 Time-to-answer reduction 50% target(spec §1.7)需要呢個 baseline 比較。冇 baseline = business impact metric 無法 measure。 |
| **Default if unanswered** | 假設 mix of 「自己搜 SharePoint 5–10 分鐘」+「問同事 即時–半日」。Beta phase 設計 5 個 task 做 stopwatch session。 |
| **Decision** | 🟡 To be filled by domain expert |
| **Decided By** | _(name)_ |
| **Date** | _(YYYY-MM-DD)_ |
| **Status** | `Open` |

---

## 3. Technical W1 Discovery(5 條,dev 自行 confirm)

呢部分**唔需要 stakeholder 答**。W1 Day 1–2 dev hands-on sample manual 同 cloud resource,自然會出答案。記錄喺度方便 audit。

### Q17 — Sample Manual Structure(W1 Day 1)

| Field | Content |
|---|---|
| **Question** | 5 份 sample manual 嘅 structure 一致?(Heading style 用 Word default H1/H2/H3?Image 數量 + 格式?Table 多寡?) |
| **Why it matters** | Docling parser 行為依賴 OOXML structure consistency。如果每份 manual heading 用 hardcoded font size 而唔係 style,parser 推斷 section 失效。 |
| **Resolution method** | W1 Day 1 拎 5 份 sample,跑 `python -m scripts.inspect_docx_structure`,人工 review report。 |
| **Decision / Finding** | _(W1 Day 1 後填)_ |
| **Decided By** | Dev(self) |
| **Date** | _(W1 Day 1)_ |
| **Status** | `Open` |

---

### Q18 — Embedded Image Format Coverage(W1 Day 1)

| Field | Content |
|---|---|
| **Question** | Embedded image 格式 coverage:PNG / JPG 為主?有冇 WMF / EMF(Office vector)? SVG?HEIC? |
| **Why it matters** | WMF / EMF 係 Office legacy vector format,Docling default 唔處理,要 fallback convert。 |
| **Resolution method** | W1 Day 1 sample 內所有 image 列 format inventory。 |
| **Decision / Finding** | _(W1 Day 1 後填)_ |
| **Decided By** | Dev(self) |
| **Date** | _(W1 Day 1)_ |
| **Status** | `Open` |

---

### Q19 — Embedding Dimension Trade-off(W2)

| Field | Content |
|---|---|
| **Question** | Embedding 用 1024d(MRL truncate from 3072)、1536d、定 full 3072d 喺 EKP corpus 上嘅 Recall@5 差異?Storage cost trade-off? |
| **Why it matters** | 3072d storage 同 search latency 約係 1024d 嘅 3×。Quality 差距 1024 vs 3072 通常 < 2pp,但需 measure。 |
| **Resolution method** | W2 用同一 30 條 eval set 跑 3 個 dim baseline,出 comparison table。 |
| **Decision / Finding** | _(W2 末填)_ |
| **Decided By** | Dev(self) |
| **Date** | _(W2 末)_ |
| **Status** | `Open` |

---

### Q20 — LLM Synthesis Model Final Pick(W3)

| Field | Content |
|---|---|
| **Question** | GPT-5.5 vs GPT-5.4-mini 喺 synthesis 嘅 cost-quality trade-off?Production lock 邊個? |
| **Why it matters** | GPT-5.5($5/$30 per M tokens)vs GPT-5.4-mini(~$0.5/$2 per M)cost 差 ~10×。如果 mini 嘅 Faithfulness ≥ 95% 同 Correctness ≥ 80%,production cost 慳大錢。 |
| **Resolution method** | W3 用 30 條 eval set 跑 A/B,4 metric 對比。 |
| **Decision / Finding** | _(W3 末填)_ |
| **Decided By** | Dev(self) |
| **Date** | _(W3 末)_ |
| **Status** | `Open` |

---

### Q21 — Reranker Final Pick(W4 Mini-Shootout)

| Field | Content |
|---|---|
| **Question** | Cohere v3.5 / Voyage rerank-2.5 / ZeroEntropy zerank-1 / Azure built-in semantic ranker 邊個 production lock? |
| **Why it matters** | 直接影響 Recall@5 + retrieval cost。Azure built-in 慳一個 vendor 但 quality 可能 -5% 到 -10%。 |
| **Resolution method** | W4 mini-shootout(architecture.md §4.5),4-way 對比,出 recommendation。 |
| **Decision / Finding** | _(W4 末填)_ |
| **Decided By** | Dev(self) |
| **Date** | _(W4 末)_ |
| **Status** | `Open` |

---

## 4. Decision Status Dashboard

每次 update 同步維護呢個 table 嘅 status:

| Q# | 簡述 | Owner | Critical? | Component(s) | Status | Decided On |
|---|---|---|---|---|---|---|
| Q1 | Format ratio | Stakeholder + SME | 🔴 | C01 | `Resolved` | 2026-04-30 |
| Q2 | Source access | Stakeholder | 🔴 | C01 + C06 | `Resolved` | 2026-04-30 |
| Q3 | Azure AI Search | Stakeholder + IT | 🔴 | C03 | `Resolved` (full — Standard S1 + eastus2 + index ekp-kb-drive-v1 created) | 2026-05-02 |
| Q4 | Azure OpenAI deployment | Stakeholder + IT | 🔴 | C05 + C01 | `Resolved` (full) | 2026-05-01 |
| Q5 | Cohere procurement | Stakeholder | | C04 | Open | — |
| Q6 | Real query collection | Stakeholder | | C06 | Open | — |
| Q7 | Beta user source | Stakeholder | | C09 + C10 + C11 | Open | — |
| Q8 | 4-metric replacement | Stakeholder | | C06 | Open | — |
| Q9 | Sensitivity / CMK | Stakeholder | | C03 + C12 | Open | — |
| Q10 | Visual identity | Stakeholder | | C09 + C10 | Open (using default neutral tokens) | — |
| Q11 | Entra ID tenant | Stakeholder | | C11 | Open | — |
| Q12 | Tier 2 owner = Chris | Stakeholder | | (cross-cutting governance) | Open | — |
| Q13 | Ground truth allocation | Stakeholder | 🔴 | C06 | `Resolved` | 2026-04-30 |
| Q14 | Specific labeler | Domain Expert | 🔴 | C06 | `Resolved` (full — Chris Lai self-assigned) | 2026-05-01 |
| Q15 | Update frequency | Domain Expert | | C01 | Open | — |
| Q16 | Status quo baseline | Domain Expert | | C06 | Open | — |
| Q17 | Sample structure | Dev | | C01 | Open | W1D1 |
| Q18 | Image format | Dev | | C01 | Open | W1D1 |
| Q19 | Embedding dim | Dev | | C01 + C03 | Open | W2 |
| Q20 | LLM pick | Dev | | C05 | Open | W3 |
| Q21 | Reranker pick | Dev | | C04 | Open | W4 |

**Critical path summary**:🔴 6 條(Q1, Q2, Q3, Q4, Q13, Q14)— **全部 `Resolved` as of 2026-04-30**。W1 啟動 cleared。

**Pending implementation detail**(W1 D5 closeout 2026-05-02:全部 6 critical OQ full Resolved,zero outstanding minor):
- ~~Q3~~ — ✅ Fully resolved W1 D5(2026-05-02):tier Standard S1 + region eastus2 confirmed by Chris;endpoint + admin key root `.env`(H5 commit `09138d4`);F9 index `ekp-kb-drive-v1` HTTP 201 created W1 D4(commit `349c33e`)
- ~~Q4~~ — ✅ Fully resolved W1 D2:endpoint + API key + 6 deployment names + api version `2024-12-01-preview` → root `.env`
- ~~Q14~~ — ✅ Fully resolved W1 D2:Chris Lai(`chris.lai@rapo.com.hk`)self-assigned SME labeler

---

## 5. Sign-off

完成填寫後,以下 owner 簽名 + commit 文件至 repo,W1 啟動。

```
─────────────────────────────────────────────────
 Stakeholder(Project Sponsor / Lead)

 Name: ____________________
 Date: ____________________
 Signature: _______________

 我 confirm 已 review 上述 13 條 Stakeholder Decision,
 答案如各條對應 Field "Decision" 所列。EKP Tier 1
 12-week sprint approval grant,W1 啟動。
─────────────────────────────────────────────────

 Tech Lead

 Name: Chris
 Date: ____________________
 Signature: _______________

 我 confirm 已 review 全部 21 條 Open Question,
 stakeholder + 領域專家答案已收 receipts,
 W1 sprint 正式啟動。
─────────────────────────────────────────────────

 Domain Expert(Subject Matter Expert)

 Name: ____________________
 Date: ____________________
 Signature: _______________

 我 confirm 已 review Q14–Q16 領域問題,答案如
 各條對應 Field "Decision" 所列;Q14 ground truth
 標註 owner = me / 已 delegate to ____________。
─────────────────────────────────────────────────
```

---

## 6. Update Workflow

當任何 OQ 由 `Open` 變 `Resolved`:

1. **編輯本文件**:填好 Decision / Decided By / Date,Status 改成 `Resolved`
2. **同步 §4 dashboard table**
3. **Commit message**:`docs(decision-form): resolve OQ-Q<N> — <one-line summary>`
4. **若係 critical path 解鎖**:通知 dev team channel(unblock 對應 work item)
5. **若 decision 改變 architecture**:同時 trigger ADR 流程(see [`../CLAUDE.md` §5](../CLAUDE.md))

---

## 7. Reference

- 主架構規格:[`architecture.md` §10 Open Questions](./architecture.md)
- Sprint plan:[`architecture.md` §6](./architecture.md)
- Risk Register(部分 OQ 對應 risk):[`architecture.md` §8](./architecture.md)
- Claude Code OQ Awareness:[`../CLAUDE.md` §7](../CLAUDE.md)

---

**Decision form version**:1.0
**Created**:2026-04-27
**Owner**:Chris(Tech Lead)
**Effective until**:All Critical 🔴 OQ resolved → W1 Day 1 啟動
