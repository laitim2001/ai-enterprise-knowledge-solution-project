# SITUATION EKP — Session Start Prompt(每個新 session 必用)

> **用法**:每個新 session 開始時,整份 copy 入對話框送出,**只需更新最後一節「今天的任務」一行**。其他段落係常駐 onboarding context,唔需要每次改。
>
> **適用範圍**:Tier 1 12-week sprint(W1–W12,2026-04-27 → 2026-07-19 約)。Tier 1 收尾後再決定是否退役 / 改寫 V2 prompt。

---

## 第一部分:你正在加入嘅項目

你好。本項目係 **Enterprise Knowledge Platform (EKP) — Tier 1 Foundation**,目前處於 **12-week sprint POC + Beta + Rollout 階段**(W1 = 2026-04-27 啟動)。

### EKP 為何存在(Why)

Ricoh internal user manual(Word + PPT + PDF 混合 format)散落 SharePoint / Drive,員工搵唔到、引用唔啱,客戶服務同 onboarding 受影響。EKP Tier 1 提供**單一 RAG 入口**,首個 use case 係 **Drive Project — Ricoh internal user manuals**。

### EKP Tier 1 唔係咩(避免常見誤解)

- ❌ **唔係 SaaS / 多租戶平台** — Tier 1 single tenant,Beta+ 加 Microsoft Entra ID
- ❌ **唔係 GraphRAG / multi-agent** — 呢啲 explicit 屬 Tier 2(`architecture.md §11`)
- ❌ **唔係 Dify fork / 修改版** — Dify 純 read-only reference(`references/dify/`,license risk),禁止 copy code
- ❌ **唔係「Tango.us 抽 manual」** — source 係 Word / PDF / PPT 文件,非 Tango 平台
- ❌ **唔係 character-based chunker** — chunking 係 layout-aware(`§3.3 + §3.5`)

---

## 第二部分:最高指導原則(不可違反 — Strict Mode)

### 原則 1 — Behavioral Baseline(§1 Karpathy guidelines)
- **Think before coding**:assumption 明示,唔肯定就 ask,有更簡單做法就 push back
- **Simplicity first**:最少 code 解決問題,唔加未要求嘅 abstraction / flexibility / future-proofing
- **Surgical changes**:只改 user request 涉及嘅 code,唔順手 refactor / format adjacent code
- **Goal-driven execution**:task 一開始定 verifiable success criteria(寫 test for invalid input,然後 make pass)

### 原則 2 — Spec 凍結(`architecture.md` v6)
- v6 係 frozen baseline(v5 → v5.1 → v6 amendment landed W11 D2 cont 2026-05-09 per ADR-0014/0015 — UI Tier 1 expansion 9 views + hybrid auth model;§3.4 KB-metadata-persistence note + §3.7 auth-transport note added W17 per ADR-0022/0023, doc version not bumped — ADR is the record),**§3 + §4 任何 component 改動**就係 architectural change(H1)
- §3.2 vendor table 已 lock(H2):Azure AI Search S1 / Azure OpenAI text-embedding-3-large / Cohere Rerank v4.0-pro(W6 production lock per ADR-0012 + Q21 Resolved)/ GPT-5.5 / Docling + python-pptx / Langfuse / RAGAs / Next.js + shadcn/ui / FastAPI / Azure Communication Services(Email Verification per ADR-0014 + Q22)/ Postgres via `psycopg`(KB-metadata + users/sessions persistent backing per ADR-0023;in-memory fallback when `DATABASE_URL` unset)

### 原則 3 — Tier 1 only(H4)
- **Tier 1 implementation 唔可以包含 Tier 2 feature**,即使「順手做埋」:
  - GraphRAG / Knowledge Graph
  - L4+ multi-agent orchestration
  - Workflow / plugin builder
  - Multi-tenancy / Multi-language(JP/ZH)/ Multi-modal(B 類純圖片搜索)
  - Auto-sync / Custom LLM fine-tuning
- **「Tier 2 friendly」唔等於做**:Tier 1 必須 modular + extensible + MCP-ready,但實作留畀 Tier 2

完整 6 條 Hard Constraints(H1–H6)詳見 [`CLAUDE.md §5`](../../../CLAUDE.md)。

---

## 第三部分:EKP 13 Components(架構骨架)

EKP 嚴格按以下 13 component 組織代碼,**禁止跨 component 雜湊**:

| ID | Component | 首次接觸 | Status(2026-05-10 W17-beta-hardening closeout) |
|---|---|---|---|
| **C01** | Ingestion Pipeline(Docling + python-pptx + embedder + layout-aware chunker + screenshot pipeline)| W2 | ✅ Implemented(W2 F1-F5 + W3 D5 PPT parser)|
| **C02** | Knowledge Base Manager(FastAPI + swappable `KBStorageBackend` per ADR-0023)| W1 D2 | ✅ Implemented(W17 F1:Postgres-backed via `make_kb_backend`;in-memory fallback when `DATABASE_URL` unset;**CO18 CLOSED**;🚧 F1.5b Postgres-path runtime smoke deferred W18+/CO17 — `pip install psycopg` R8-blocked)|
| **C03** | Indexing Service(Azure AI Search S1)| W2 D1 | ✅ Implemented(`ekp-kb-drive-v1` 1024d HNSW;W2 Gate 1 PASS R@5=0.9722)|
| **C04** | Retrieval Engine(Hybrid + Cohere Rerank v4.0-pro)| W2 D5 | ✅ Implemented(W3 Cohere wired + W6 D1 Azure 2-way reaffirmed v4.0-pro production lock per Q21 Resolved + ADR-0012)|
| **C05** | Generation Pipeline(GPT-5.5 + custom CRAG L2)| W3 D1 | ✅ Implemented(W3 synthesis + citation + SSE streaming + W4 CRAG L2 + W5 threshold KEEP 0.70 NON-STICKY + W6 prompt tweak +0.85pp aggregate)|
| **C06** | Eval Framework(RAGAs + custom gate)| W1 D1 | ✅ Implemented(W1 validator + W2 F7 framework + W4 shootout 2-way + W5 Gate 2 PARTIAL PASS + W6 reaffirmed + **W17 F3 RAGAs 4-metric integrated into `/eval/run`+`/eval/shootout`**(`make_ragas_evaluator` + `orchestrator.build_ragas_samples`;faithfulness→`EvalReport.faithfulness`, answer_relevancy→`correctness` approx;CI-tested at LLM-judge boundary);🚧 F3.5b live-verify against Azure deferred W18+/CO17;**CO_W15_F1_eval_set_v1 OPEN** — `eval-set-v1.yaml` final doesn't exist(only `eval-set-v1-draft.yaml` WIP), needs Q14 SME reference-answer labels)|
| **C07** | Observability Stack(Langfuse + structlog + cost dashboard + alerts)| W1 D1 | ✅ Implemented(W1 init + BUG-001 closed + W8 Langfuse SDK + cost dashboard + feedback + alerts + W10 D3 real-time wire + W11 D1 pricing rate Option B placeholder)|
| **C08** | API Gateway(FastAPI + uvicorn + Pydantic v2)| W1 D1 | ✅ Implemented(18 endpoints;`/query`+`/chat` SSE + `/auth/*` hybrid auth + **httpOnly cookie + CSRF transport + `/auth/refresh` rotation per ADR-0022(W17 F2)** + admin auth;stub closure cascade DONE — `debug/trace/{id}` + KB document listing(W16 F5)+ `eval/run`+`eval/shootout` real RAGAs(W17 F3))|
| **C09** | Admin Console UI(Next.js + shadcn/ui)| W1 D1 | ✅ Implemented(W2 partial → **W12-W15 UI Tier 1 expansion 9 views per ADR-0015** — V1 Dashboard + V2-V4 KB tabs + V5 Eval Console + V6 Debug View + Pipeline wizard + responsive/a11y + **entire frontend `[oklch(...)]` = 0 milestone**)|
| **C10** | Chat Interface UI(Next.js + Vercel AI SDK)| W3 D2 | ✅ Implemented(W3 streaming + Citation + W13 routing restructure + theme provider + dark mode toggle + W15 token cleanup)|
| **C11** | Identity & Access(MSAL + Entra ID + hybrid auth per ADR-0014 + scrypt password hash per ADR-0016 + cookie/CSRF transport per ADR-0022)| W7 D1 | 🟡 Mostly Implemented(W7 mock auth bridge + W11 D2 cont hybrid auth model amendment + W13 register/verify/login backend + scrypt password hash + **W17 F2 httpOnly cookie + CSRF double-submit + `/auth/refresh` rotation + verify-email auto-login(CO_F5_refresh + CO_F5_cookie CLOSED, per ADR-0022)** + **W17 F1.5 `users_repo`/sessions Postgres-backed via `make_users_store`(per ADR-0023;in-memory fallback)**;**Track A IT cred consumption pending W16 F1** for operational `Resolved` Q11)|
| **C12** | DevOps & Infra(Docker + Azurite + ACA + GHA)| W1 D1 | ✅ Implemented(W1 local stack + W11 staged rollout 25% activation;Azure Blob persistent backing W16+ Track A)|
| **C13** | Email Verification Service(Azure Communication Services per Q22 + ADR-0014;NEW W12 D1 v6 amendment)| W12 D1 | ✅ Implemented(W13 D5 ACS Email Client wrapper + verification token sign `secrets.token_urlsafe(32)` + 24h expiry per architecture.md v6 §3.7;`backend/api/auth/email_provider.py`;**CO_F6a-c retry post R8 + BackgroundTasks + SPF/DKIM IT-side W16+**)|

完整 spec:[`docs/02-architecture/COMPONENT_CATALOG.md`](../../02-architecture/COMPONENT_CATALOG.md) + per-component design notes `docs/02-architecture/components/Cn-*.md`(rolling JIT;C11 + C13 design notes pending)。

> **Note**:`COMPONENT_CATALOG.md §11 Tier 2 trigger matrix` 仍引用 hypothetical "C13 Workflow Engine"(Tier 2 future);**Tier 1 actual C13 = Email Verification Service** per architecture.md v6 §3.7(authoritative)— catalog amendment 屬 W17+ housekeeping。

---

## 第四部分:權威排序(衝突時上位者勝)

```
docs/architecture.md v6 § 1-14 (content lock; v5→v5.1→v6 amendment W11 D2 cont per ADR-0014/0015)
  > 根目錄 CLAUDE.md (standing instructions)
  > docs/01-planning/PROCESS.md v2.0 (workflow lifecycle)
  > docs/02-architecture/COMPONENT_CATALOG.md + components/Cn-*.md
  > active phase plan.md / checklist.md / progress.md
  > docs/decision-form.md (OQ status)
  > docs/adr/ (when 出 ADR 後)
```

**任何衝突以上位者為準**。Stakeholder feedback 同 spec 衝突 → STOP,surface conflict,等 resolution(per CLAUDE.md §13)。

---

## 第五部分:必讀文件(每次 session 至少讀以下)

依序讀完先對齊上下文:

1. **本 prompt**(你正在讀)— 高層 onboarding
2. **`CLAUDE.md`**(專案根目錄,v1.3)— Standing instructions + §1 Karpathy baseline + §5 H1–H6 hard constraints + §10 Phase Workflow R1–R5
3. **`docs/01-planning/PROCESS.md`**(v2.0)— 3 task types(Phase / Change / Bug-fix)+ R1–R5 binding rules + AI auto-classification
4. **Active phase plan.md + checklist.md + progress.md**(當前 W{NN} folder)— Sprint scope + next un-checked item + last 3 Day-N entries
5. **`docs/architecture.md`**(frozen v5)— 涉及 §3 RAG core / §4 application / §5 UI / §6 sprint timeline 嗰陣按需讀對應 section

按需要再讀:
- `docs/02-architecture/COMPONENT_CATALOG.md` + 對應 `components/Cn-*.md`(改 / 新加 component 時)
- `docs/01-planning/RISK_REGISTER.md`(living)— risk-related decision
- `docs/decision-form.md`(21 條 OQ 狀態)
- `docs/eval-methodology.md` + `docs/eval-set-v0.yaml`(寫 / 改 eval 時)
- `references/REFERENCE_USAGE.md`(借用 Dify reference 之前)

---

## 第六部分:Rolling Phase Planning 紀律(EKP §10 R1–R5 核心)⭐

> **EKP 紀律核心,每次 session 都要記住**

EKP 採用 **rolling JIT phase planning**(per `CLAUDE.md §10` + `PROCESS.md §5`):

### ✅ 正確做法

- **每 phase 喺 kickoff 先建** `docs/01-planning/W{NN}-{kebab}/` folder(W01-foundation / W02-multi-format-ingestion / W03-chat-retrieval-citation 已建)
- **任何 multi-day implementation 之前必須有對應 phase plan.md committed**(R1)
- Daily commit 必須對應 progress.md Day-N entry(R2)— `docs(planning):` housekeeping commits 例外
- Plan deviation(scope change / new deliverable / cancelled deliverable)必須 log 入 plan.md changelog(R3)
- OQ resolved → 同步更新 decision-form.md AND progress.md Day-N mention(R4)
- Phase closeout 之前任何 architectural-adjacent decision(per H1)必須寫 ADR(R5)
- **起草新 plan/checklist 必先讀「最近一個 closed phase」樣板**:章節編號 / Day 數 / acceptance criteria 細節水平必須一致;scope 差異透過**內容**調整(更多 deliverables / files / tests),**唔係**透過結構

### ❌ 禁止做法

- **唔好**一次過建 W01–W12 所有 folder(rolling JIT,違反 = 過早決定 + 將來必返工)
- **唔好**跳過 plan.md 直接 code(R1 hard constraint)
- **唔好**刪除 checklist 入面未勾選嘅 `[ ]` 項(只可 `[ ]→[x]`,延後項標 🚧 + reason)
- **唔好**喺 retrospective.md 寫具體未來 sprint task(rolling = 下一 sprint kickoff 先寫)

### 為何 rolling

1. 實作 phase N 會學到嘢,直接影響 phase N+1 設計(W2 chunk-count revised vs plan estimate 就係例)
2. 一次預寫多 phase plan,第 1 個跑完通常要改後幾個
3. ROI 偏低 + 維護成本高
4. 業界標準

→ **每個新 session 開始,AI 要先確認 rolling planning 紀律仍在執行,沒有突然出現多個未來 phase folder**

---

## 第七部分:Task Type Classification(PROCESS.md v2.0 §1)

收到 task 之後,AI 要先分類:

| Signal in user request | Likely type | Required pre-doc |
|---|---|---|
| "implement F<n>" / matches active phase deliverable | Phase/Sprint | active phase plan.md F<n> 已 committed |
| "改 X 嘅 behavior" / "add Y option" / "modify Z" / "support W format" | Change | `docs/03-implementation/changes/CH-{NNN}-{kebab}/spec.md` |
| "X 唔 work" / "broken" / "fail" / "regression" / "錯咗" | Bug-fix | `docs/03-implementation/bugs/BUG-{NNN}-{kebab}/report.md` |
| "fix typo" / "rename variable" / "update comment"(< 30 min)| Trivial | 無需 doc folder,直接 commit |

**Protocol**:
1. AI **classify** based on signals
2. **Propose to user** explicitly:「我判斷呢個係 [Phase / Change / Bug-fix / Trivial],建議走 X workflow,先準備 [plan.md / spec.md / report.md]。OK?」
3. **Wait for user confirm**(or override)
4. **Open corresponding doc**(per R1 binding)before any code

---

## 第八部分:當前進度(AI 自查,唔需用戶手動更新)

新 session 開始,AI 用以下指令自查當前進度:

```bash
# 1. 看現在喺邊個 branch
git branch --show-current

# 2. 看 main 最近 commits(過去 sprint 痕跡)
git log main --oneline -20

# 3. 看當前 branch commits(若喺 feature branch)
git log $(git branch --show-current) --oneline --not main

# 4. 看 working tree 是否乾淨
git status --short

# 5. 看 active phase folders(R1 紀律檢查 — 應該只有「過去 closed」+「當前 active」+「下一個 draft」)
ls docs/01-planning/W*-*/

# 6. 讀當前 active phase 嘅 progress.md 最新 Day-N entry
# 路徑:docs/01-planning/W{NN}-{name}/progress.md

# 7. 讀最近 closed phase retro(open items + lessons)
# 路徑:docs/01-planning/W{NN-1}-{name}/progress.md (Retro section)

# 8. 看 daily development log
ls docs/10-development-log/01-daily/ | tail -3
```

**讀完上述後**,AI 應該能夠回答:
- 目前喺邊個 sprint week?Day N?
- 上一個 closed phase 邊個?有咩 carry-over items?
- 累計完成多少 sprint?距離 Gate 1 / Gate 2 / W12 production launch 仲有幾遠?

---

## 第九部分:22 條 OQ 狀態(W15 D5 closeout snapshot — 2026-05-09)

> **每次 phase 結束按需要 sync 此節,但唔係必更新**;權威 source = `docs/decision-form.md §4 Decision Status Dashboard`
> **Note**:OQ 總數由 21 → 22 — Q22(Email Verification Service vendor)NEW W12 D1 per ADR-0014 hybrid auth model architecture v5.1 → v6 amendment

### ✅ Resolved(17 條)
- **Q1**(format ratio,2026-04-30)
- **Q2**(source access,2026-04-30)
- **Q3**(Azure AI Search S1 + eastus2 + index `ekp-kb-drive-v1`,2026-05-02)
- **Q4**(Azure OpenAI deployment full,2026-05-01;W11 D1 pricing rate operational follow-up via Option B placeholder + spend cap proxy non-blocking)
- **Q5**(Cohere procurement Path A Azure Marketplace + v3.5 → v4.0-pro spec drift accept;W6 D1 LIVE Azure 2-way reaffirm,2026-05-04 + 2026-05-05)
- **Q7**(Beta user source — default RAPO 內部 + 1-2 友好部門 + Chris pre-identify W7-W8;W6 D5 stakeholder approval cycle,2026-05-05)
- **Q9**(Sensitivity / CMK — default Internal + Azure-managed key;CMK trigger post-Beta if requires;W6 D5 stakeholder approval cycle,2026-05-05)
- **Q10**(Visual identity — default neutral tokens approved;designer pass post-Beta optional;W6 D5 stakeholder approval cycle,2026-05-05)
- **Q11**(Entra ID tenant — Ricoh 統一 tenant via Entra ID;**decision-level Resolved 2026-05-05 + operational committed early June 2026 real-calendar**(W9 D1 三方 alignment outcome 2026-05-26 — Pattern A combined SPA+API + `ekp-beta.ricoh.com` Beta domain confirmed);mock auth bridge preserved until IT cred populate event;**final operational `Resolved` trigger pending W16 F1 IT cred consumption**)
- **Q12**(Tier 2 owner — Chris as Tier 2 GraphRAG + multi-agent + multi-tenancy decision owner;post-W12 production launch governance trigger;W6 D5 stakeholder approval cycle,2026-05-05)
- **Q13**(ground truth allocation,2026-04-30)
- **Q14**(specific labeler = Chris Lai,2026-05-01;W11 D2 corpus scope clarification — Drive corpus actual content = D365 F&O ERP user manuals NOT MFP product manuals,labeler unchanged + Q14 status preserved per memo `docs/03-implementation/drive-corpus-scope-clarification-W11-d2.md`)
- **Q17**(Sample structure — 6 sample W2 used + W2 D5 cont,2026-05-04)
- **Q18**(Image format — PNG/JPEG dominant per W2 D3 actual data,2026-05-04)
- **Q19**(embedding dim = 1024d MRL truncate baseline,2026-05-05 W2 D3)
- **Q21**(Reranker final pick = Cohere v4.0-pro;W6 D1 LIVE Azure 2-way reaffirm via faith Δ -11.76pp + rel Δ -9.81pp WORSE;ADR-0012 formal record,2026-05-05)
- **Q22**(Email Verification Service vendor — default **Azure Communication Services** activated per ADR-0014 hybrid auth;Tier 2 reconsideration trigger if Beta cohort scale > 100/day OR feature gap surface;W12 D1 evening,2026-05-09)

### 🔴 Open(5 條)— 影響將來 phase
- **Q6** Real query collection owner → W16+ Beta cohort real query log collection trigger(non-blocking until W16+ rollout active)
- **Q8** 4-metric replacement → defer Tier 2(Gate 2 PARTIAL PASS confirmed,not FAIL — replacement 4-metric NOT triggered)
- **Q15** Manual update frequency → **W16 F3 first weekly signal report trigger**(Beta phase real query log signal baseline measurement)
- **Q16** Status quo baseline → defer W12+ production launch trigger
- **Q20** LLM synthesis final pick → defer Tier 2(GPT-5.5 spec lock per architecture.md §3.2 H2;Tier 2 may revisit if real query distribution requires alternative)

**Default behavior for Open OQ**:用 spec default value 繼續,**喺 commit message 標**:`Note: depends on OQ-Q<N> default`(per CLAUDE.md §8)。

---

## 第十部分:Sprint Awareness(W1 → W16+ timeline,extended via W12-W15 UI sprint cycle pivot)

per [`CLAUDE.md §9`](../../../CLAUDE.md):

| Week | Default focus | Hard cutoff |
|---|---|---|
| W1 | Foundation:FastAPI/Next.js skeleton + Docling docx parser PoC + KB CRUD + eval-set v0 + Azurite local | ✅ **closed 2026-05-02** |
| W2 | Multi-format ingestion + hybrid retrieval baseline + Admin Console layout + Gate 1 R@5 ≥ 80% | ✅ **closed 2026-05-04**(Gate 1 PASS R@5=0.9722 LIVE post-truststore mitigation)|
| W3 | Cohere Rerank + GPT-5.5 synthesis + Citation + Chat UI streaming + PPT parser | ✅ **closed 2026-05-04** |
| W4 | CRAG L2 + RAGAs eval automation + Reranker shootout(4-way → 2-way per Karpathy §1.2 simplicity drop)+ 加 20 條 real query | ✅ **closed 2026-05-04**(Gate 2 PARTIAL PASS DEFERRED → W5 D2 land)|
| W5 | Optimization;**conditional** L3 routing(only if Gate 2 全 pass)| ✅ **closed 2026-05-04**(Gate 2 PARTIAL PASS landed W5 D2 — L3 routing defer per strict reading;CRAG threshold KEEP 0.70;NON-STICKY reranker decision)|
| W6 | Final eval + demo prep + Beta plan + Azure 2-way verify(Gate 2 STRONG PASS upgrade attempt)| ✅ **closed 2026-05-05**(Gate 2 PARTIAL PASS confirmed NOT upgraded;Cohere v4.0-pro reaffirmed final;Q21 Resolved;F3 prompt tweak landed +0.85pp aggregate lift)|
| W7 | Microsoft Entra ID auth + rate limiting + audit logging + error handling polish + mobile responsive | ✅ **closed 2026-05-06**(F1.7-mock smoke + F5.4 viewport + F6 Phase Gate PASS)|
| W8 | Langfuse SDK + cost dashboard + feedback + alerts + admin auth(C07+C08+C12)| ✅ **closed 2026-05-06**(F5 Langfuse SDK + cost dashboard + feedback + alerts + F4.4 admin auth + F6 W08 closeout cascade)|
| W9 | Beta internal testing prep + C11 dependency_overrides cleanup + 三方 alignment(Q11 operational commit early June 2026 real)| ✅ **closed 2026-05-06**(C11 dependency_overrides cleanup + F6 cascade + W10-beta-iteration kickoff)|
| W10 | Beta iteration + tabletop exercise + cost dashboard real-time wire + W11 governance prep | ✅ **closed 2026-05-06**(F5.1 tabletop + F5.3 review + F6 + W11 phase folder kickoff)|
| W11 | Staged rollout 25% activation + Mode B local dev unblock + UI sprint pivot governance prep | ✅ **closed 2026-05-08 early**(PARTIAL PASS verdict;**UI sprint pivot triggered** — W11 D2 cont architecture.md v5.1 → v6 amendment + ADR-0014 hybrid auth + ADR-0015 UI Tier 1 expansion 9 views sister ADRs)|
| W12 | UI foundation discovery(Phase 1 of 4 UI sprint cycle)+ Q22 email vendor + C13 component card | ✅ **closed 2026-05-09**(PASS WITH F4.13 USER-DEFERRED CAVEAT)|
| W13 | User-facing views(Phase 2 of 4)+ routing restructure + theme provider + dark mode toggle + ADR-0016 scrypt password hash | ✅ **closed 2026-05-09**(PASS WITH SMOKE-USER-DEFERRED CAVEAT)|
| W14 | Admin views refactor(Phase 3 of 4)+ V2 Admin Dashboard refactor + cross-cutting verification | ✅ **closed 2026-05-09**(PASS WITH SMOKE-USER-DEFERRED CAVEAT)|
| W15 | Polish closeout(Phase 4 of 4 UI sprint cycle FINAL)+ V5 Eval Console + V6 Debug View + responsive/a11y/oklch=0 milestone + Playwright E2E baseline harness | ✅ **closed 2026-05-09**(PASS WITH SMOKE-USER-DEFERRED CAVEAT;**Tier 1 UI sprint cycle FINAL marker landed** — 9 views × 6+ components × hybrid auth × ACS email × responsive/a11y/E2E/pixel diff baseline)|
| **W16** | **Beta deploy resume**:Track A IT cred consumption + R-B1 closure + 25% Beta cohort rollout + daily metric monitor + Q15 weekly signal report + user smoke + backend stub closure cascade | **W16 status: draft**(F5 backend stub closure cascade **DONE** — `debug/trace/{id}` + KB doc listing + `84d030e` CORS audit-tail;**F1-F4 still Track-A-blocked** pending IT cred populate event + R-B1 closure — parallel-track to W17 which ran the AI-controllable Beta-hardening backlog)|
| **W17** | **Beta hardening**(AI-controllable backlog, parallel to W16):Postgres persistent backing(ADR-0023)+ auth-transport cookie+CSRF+`/auth/refresh`(ADR-0022)+ RAGAs 4-metric integration + frontend hardening bundle + a11y/dark-mode verify + Vitest/RTL scaffold + ADR-0017(R8 mitigation pattern) | ✅ **closed 2026-05-10**(phase Gate **PASS**;🚧 F1.5b Postgres-path runtime smoke + F3.5b RAGAs live-verify R8/Azure-key-bound → deferred W18+/CO17)|
| W18+ | _not pre-created_ — rolling JIT per CLAUDE.md §10 R1 | (kickoff post-W17-closeout;candidates = W16 F1-F4 if Track A cred lands / Tier 2 prep governance Q12 / user local-dev-setup task — `scripts/seed_dev_kb.py` or one-liner)|

**Critical gates**:
- **Gate 1(W2 末 R@5 ≥ 80%)** — ✅ **PASS** R@5=0.9722 W2 D5 LIVE eval post-truststore
- **Gate 2(W4-W6 4 metric within 5pp 互換)** — ✅ **PARTIAL PASS confirmed**(Cohere v4.0-pro baseline robust;W6 D1 Azure 2-way LIVE reaffirm — within-5pp on prec+recall only,faith+rel ≥ 5pp Cohere ahead)→ L2 CRAG NOT dropped(drop-L2 trigger 未觸發);production lock landed
- **Gate 3(W6 末 demo ready)** — ✅ **READY**(`docs/01-planning/W06-final-eval-demo/artifacts/demo-prep.md` Part 1 + 2 + 3 + `docs/03-implementation/beta-plan-v1.md` ready)
- **Tier 1 UI sprint cycle FINAL gate(W15 末)** — ✅ **PASS WITH SMOKE-USER-DEFERRED CAVEAT**(architecture.md v6 §13.12 amendment fully implemented;9 views × 6+ components × hybrid auth × ACS email × responsive/a11y/E2E/pixel diff baseline;user smoke deferred to W16 F4 first run)
- **Production launch gate(W16+ Beta deploy resume)** — ⏳ **pending Track A IT cred populate event trigger + R-B1 closure**

如果 session 唔清楚邊個 week,**ask user "What week / day are we in?"** 之後再做 default focus 對應。

---

## 第十一部分:常駐 Open Items / Carry-overs(每 phase 結束更新)

> **此節要每 phase 收尾時更新**:把 retro 嘅 carry-overs + ADR triggers 精煉成下方一句話列表

### 已知未解(at session start time = 2026-05-10 W17-beta-hardening closeout)

> **CLOSED by W17-beta-hardening**(2026-05-10):**CO18** KB Manager + `users_repo` persistent backing(→ Postgres via `psycopg` per ADR-0023;in-memory fallback when `DATABASE_URL` unset)· **CO_F5_refresh** + **CO_F5_cookie**(→ W17 F2 httpOnly cookie + CSRF + `/auth/refresh` rotation per ADR-0022)· **CO_W15_F1_backend**(→ W17 F3 RAGAs 4-metric integrated into `/eval/run`+`/eval/shootout`)· **CO_W15_F2_langfuse_url**(→ already in `.env.example` W16, verified W17 F4)· **CO_W15_F2_backend**(→ `debug/trace/{id}` done W16 F5)· **CO_F3a/b/c**(→ KB doc-listing wired W16 F5 + frontend W17 F4.1;per-doc upload/reindex/delete stays 501 stub — W2 ingestion + Track A)· **CO_W15_F4_vitest_baseline_gap**(→ W17 F6 Vitest+RTL scaffold)· **CO_W14_process_grep_verify**(applied again W17 D0 — `GET /kb/{id}/documents` already-impl + `NEXT_PUBLIC_LANGFUSE_URL` already-present surfaced upfront).
> **Partially closed by W17**:**CO_W15_F3_dark_mode_visual_verify**(W17 F5 — mechanism + `[oklch`=0 grep + V7/V8 browser-verified;interactive 9-view walkthrough = user pre-Beta smoke).
> **NEW 🚧 deferred(W18+/CO17 — R8/Azure-key-bound runtime checks under the "personal Azure dev tier / non-proxy env" umbrella)**:**F1.5b** `pip install psycopg[binary]` + manual `docker compose up` Postgres-path CRUD/session smoke + `mypy postgres_*`(R8-blocked)· **F3.5b** RAGAs live-verify against a populated `ekp-kb-drive-v1` Azure index + judge(needs Azure OpenAI keys).
> **Still OPEN**:**CO_W15_F1_eval_set_v1** — `docs/eval-set-v1.yaml` final doesn't exist(only `eval-set-v1-draft.yaml` WIP);needs Chris's SME reference-answer labels per Q14;no ground truth fabricated.

#### Immediate W16 D1 priority(post Track A IT cred populate event trigger + R-B1 closure)
- ⏸ **CO16 / Track A IT cred consumption** — `.env.production` + Azure subscription IDs + Cohere Marketplace billing wiring per W6 demo-prep.md beta-plan-v1 → **W16 F1**
- ⏸ **R-B1 closure verification** — risk register live update;blocked W11+ status flip → **W16 F1**
- ⏸ **W12+W13+W14+W15 user smoke 3-step workflow first execution** — `npx playwright install chromium` + `pnpm test:e2e:update-snapshots` + `pnpm test:e2e`(systematic subsume of cumulative 4-sprint manual smoke deferred backlog)→ **W16 F4**

#### W16 Beta cohort rollout activation(per W6 demo-prep.md beta-plan-v1 + W11 plan F1+F2+F3)
- ⏸ **F2.1-F2.4** 25% rollout activation cascade — beta-plan-v1 cohort definitions(internal RAPO + 1-2 友好部門 per Q7 Resolved)
- ⏸ **F3.1-F3.5** Daily metric monitor(R@5 + Faithfulness + Correctness + Image Association threshold tracking)
- ⏸ **F5.1** Q15 first weekly signal report(manual update frequency baseline measurement)

#### Backend follow-ups immediate Beta hardening
- ⏸ **CO_F3a/b/c**(W14)— backend `GET /kb/{id}/documents` + listing chunks + name/description PATCH + reindex/delete → **W16 F5.1-F5.3**
- ⏸ **CO_W15_F1_backend** Backend `POST /eval/run` + `POST /eval/shootout` W4 implementation → **W16 F5.4**
- ⏸ **CO_W15_F1_eval_set_v1** `eval-set-v1`(W4+W5 +20 real-query 50 queries)file existence verify → **W16 F5.x**
- ⏸ **CO_W15_F2_backend** Backend `GET /debug/trace/{trace_id}` W3+ Langfuse correlation → **W16 F5.5**
- ⏸ **CO_W15_F2_langfuse_url** `NEXT_PUBLIC_LANGFUSE_URL` Beta production endpoint env var → **W16 F5.x**

#### Polish + a11y + test backlog Beta hardening(W16 F4 / W17+ candidates)
- ⏸ **CO_W15_F3_aria_full_audit** Full ARIA + screen reader audit(NVDA/JAWS/VoiceOver)— W17+ candidate
- ⏸ **CO_W15_F3_dark_mode_visual_verify** Dark mode visual verify post-tokens.ts colorsDark — W17+ candidate
- 🚨 **CO_W15_F4_browser_binaries** `npx playwright install chromium` — **R8 corp proxy CDN block CONFIRMED 2026-05-09**(ECONNRESET at 0% of 179.4 MiB);**ADR-0017 reservation candidate strengthened** — mitigation paths:(A)personal Azure dev tier per W11 retro CO17 / (B)skip-binary `PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1` + system Chrome `channel: 'chrome'` workaround / (C)defer to W16 F4 PARTIAL PASS literal acceptance
- ⏸ **CO_W15_F4_baseline_capture** Pixel diff baseline first capture user smoke → **W16 F4.2**
- ⏸ **CO_W15_F4_vitest_baseline_gap** Vitest + RTL infrastructure formalize beyond Playwright E2E layer — W17+ candidate
- ⏸ **CO_W15_F4_interactive_flow_E2E** Full register/login + KB upload + Pipeline wizard interactive E2E — W17+ candidate

#### Process improvement formalization(W16+ pre-active flip checklist)
- ⏸ **CO_W14_process_grep_verify FORMALIZED** — Plan author "spec ref grep verification" 5-step pre-R1 active flip(9 cumulative occurrences W13+W14+W15 empirical signal):(1)Read plan literal acceptance criteria;(2)Grep code base for referenced files / functions / patterns;(3)Surface mismatches via Karpathy §1.1 think-before-coding upfront;(4)Document deviations in plan §7 changelog at plan kickoff;(5)Adjust acceptance criteria per actual reality

#### W13 backend follow-ups inherited unchanged
- ⏸ **CO_F5_refresh** `/auth/refresh` self-register session rotation
- ⏸ **CO_F5_cookie** httpOnly cookie hardening
- ⏸ **CO_F6a** `pip install azure-communication-email` retry post R8 proxy
- ⏸ **CO_F6b** Background-task email send via FastAPI BackgroundTasks
- ⏸ **CO_F6c** Sender domain SPF/DKIM IT-side post Track A

#### W11+ inherited unchanged(numbered governance carry-overs)
- ⏸ **CO16** Track A IT cred populate event + R-B1 closure(W16 F1)
- ⏸ **CO17** AF3 code fix Option A(**ADR-0013 reserved**)+ **Personal Azure dev tier / non-proxy env** — now the umbrella for the W17 deferred runtime checks:🚧 **F1.5b**(`pip install psycopg[binary]` + `docker compose up` Postgres-path smoke + `mypy postgres_*`)+ 🚧 **F3.5b**(RAGAs live-verify against a populated Azure index + judge)+ `npx playwright install chromium`(CO_W15_F4_browser_binaries)— all R8-corp-proxy / Azure-key-bound, deferred there
- ✅ **CO18** KB Manager + `users_repo` persistent backing — **CLOSED W17 F1**(Postgres via `psycopg` per ADR-0023;`PostgresKBBackend`/`PostgresUsersStore` + `make_kb_backend`/`make_users_store` factories;in-memory fallback when `DATABASE_URL` unset)— only 🚧 F1.5b runtime smoke remains(under CO17 above)
- ⏸ **CO19** F2.1-F2.4 25% rollout activation cascade(W16 F2)

#### Cross-phase / governance
- ⏸ **R8** Ricoh corp proxy — **5 cumulative occurrences**(Cohere W3 Marketplace + argon2-cffi W13 ADR-0016 stdlib switch + ACS SDK W13 lazy import + Playwright browser CDN W15 D5 ECONNRESET + psycopg W17 F1 IncompleteRead);**ADR-0017 landed 2026-05-10 W17 F0b** formalizing the mitigation pattern + vendor-decision-pivot trigger met. **Converse confirmed W17 F6**:`pnpm add -D` of npm-registry deps(Vitest/RTL etc.)goes through fine — **R8 blocks binary-CDN downloads, not the npm/PyPI registry**(the `.npmrc` `NODE_TLS_REJECT_UNAUTHORIZED=0` + hoisted-linker handle the corp-MITM-cert + OneDrive cases). Residual 🚧:`pip install psycopg[binary]`(F1.5b)+ `npx playwright install chromium`(CO_W15_F4_browser_binaries)— both binary-CDN, deferred personal-Azure-dev-tier/non-proxy env
- ⏸ **R12** Azurite SDK signature mismatch — `RISK_REGISTER` 🔴 Open;permanent fix = cloud Azure Blob W16+ Track A
- ⏸ **R-B1** Beta deploy launch readiness blocker(closure verification W16 F1 deliverable)
- ⏸ **R11** Langfuse degradation — closed via BUG-001(commits `10be96d` + `78e9ece`)

#### ADR status(2026-05-10 W17-beta-hardening closeout)
- **22 ADR landed**(0001-0012 + 0014-0023;**ADR-0013 reserved** for AF3 lifespan gate split fix per W11 D5 retro carry-over #1 — the only reserved slot left)— **next available NNNN = 0024**
- **ADR-0014**(Hybrid auth SSO + self-register)+ **ADR-0015**(UI Tier 1 expansion 9 views Dify-leaning)— sister ADRs landed W11 D2 cont stakeholder approval cycle 2026-05-09(architecture.md v5.1 → v6 amendment)
- **ADR-0016**(argon2-cffi → hashlib.scrypt stdlib)— W13 D5 F5 2026-05-09 R8 `pip install argon2-cffi` blocker;H2 vendor-decision-change ADR
- **ADR-0017**(R8 corp-proxy mitigation pattern — dependency-add discipline:stdlib > managed-REST > lazy-imported optional dep + graceful fallback;declare-but-defer-install for binary-heavy assets;stop-and-ask when unavoidable)— **landed 2026-05-10 W17 F0b** at the 5th cumulative R8 occurrence(Cohere W3 + argon2-cffi W13 + ACS SDK W13 + Playwright browser CDN W15 + psycopg W17 F1)+ vendor-decision pivot point;reservation cleared
- **ADR-0018**(Multi-KB `kb_id` propagation)+ **ADR-0019**(PDF parser)+ **ADR-0020**(Context Expander + frontend Langfuse-URL fallback)— P0 batch from `audit-W15-d5-vs-spec.md §6`, landed 2026-05-10
- **ADR-0021**(V4 Retrieval Testing tab §5.5.4 + `HybridSearcher` search-mode param)— audit drift #5 / §7 P2.1, landed 2026-05-10 — **all 5 audit major drifts now closed**
- **ADR-0022**(auth-transport hardening — httpOnly cookie + CSRF double-submit + `/auth/refresh` rotation;amends ADR-0014's transport layer)+ **ADR-0023**(KB Manager + `users_repo` persistent backing — Postgres via `psycopg`;`PostgresKBBackend`/`PostgresUsersStore` satisfy the storage Protocols;in-memory fallback)— **landed 2026-05-10 W17 F0**(the two `audit-W15-d5-vs-spec.md §7` future-ADR candidates now consumed);H1 storage-layout + H2 new-dependency, user-approved via AskUserQuestion
- 任何 H1 / H2 violation approval 後必須寫 ADR(format per CLAUDE.md §6)

> **AI 任務**:每個新 phase 開始,先看本 prompt §11 + 上 phase progress.md retro 「Carry-overs」,向用戶確認哪些 follow-up 要喺呢個 phase 處理,哪些繼續延後

---

## 第十二部分:常駐 milestones(累計完成)

> **每 phase 收尾更新一行**

| Phase | 完成日期 | 主要 commits | 主要成果 |
|---|---|---|---|
| **W01-foundation** | 2026-05-02 | `dc7e37f`(retro)+ `740de4c`(R8 mitigation)+ `c38710f`/`0a2673d`(F2 carryover)| FastAPI 18 stubs + Next.js 6 routes + KB CRUD in-memory + eval validator + Docling PoC stub + Azurite local + R8 / Q3 / Q4 / Q14 resolved |
| **W02-multi-format-ingestion** | 2026-05-04 | `f30f13a` D1 / `170e3db` D2 / `28341b8` D3 / `2b4bb7e` D4 / `072b95b` D5 | F1 Docling parser PoC + F2 layout-aware chunker + F3 screenshot pipeline + F4 embedder + F5 orchestrator + F6 hybrid retrieval + F7 eval framework + F8 chunk_id discovery + F9 Admin UI partial + index `ekp-kb-drive-v1` 1024d HNSW + **Gate 1 PASS R@5=0.9722** + Q19 resolved |
| **W03-chat-retrieval-citation** | 2026-05-04 | _(see W3 retro)_ | Cohere Rerank v3.5 + GPT-5.5 synthesis + Citation + SSE streaming + Chat UI + PPT parser + Pipeline wizard;Q5 Resolved Path A Marketplace |
| **W04-crag-eval-shootout** | 2026-05-04 | _(see W4 retro)_ | CRAG L2 loop + RAGAs eval automation + Reranker shootout 4-way → 2-way per Karpathy §1.2 simplicity drop(Voyage + ZeroEntropy DROPPED Tier 1)+ 加 20 條 real query placeholder + Gate 2 verdict DEFERRED → W5 |
| **W05-optimization** | 2026-05-04 | `99f9b36` + `163703f` + `7d97cf5` + `69b4577` | F1 Gate 2 LIVE PARTIAL PASS landed(Cohere v4.0-pro baseline robust;answer_relevancy 邊緣 follow-up;Azure 2-way carry-over W6) + F2 CRAG threshold KEEP 0.70 empirical fine-tune + F4 NON-STICKY reranker decision + Bug I max_completion_tokens floor 4096 fix + Q014 refusal investigation |
| **W06-final-eval-demo** | 2026-05-05 | `4cc5986` + `db35c4e` + `36f2c83` + `04e8afc` + `b161b9a` | F1 Cohere v4.0-pro reaffirmed final via W6 D1 LIVE Azure 2-way negative comparison(faith Δ -11.76pp + rel Δ -9.81pp WORSE)+ F3 prompt tweak landed(W6 D2 first-10 +1.92pp / W6 D5 subset=20 +0.85pp aggregate confirmed at scale) + F5 demo prep + Beta plan v1 + F6 W6 retro + W07 phase folder rolling JIT kickoff;**Gate 2 PARTIAL PASS confirmed** NOT upgraded;Q21 Resolved Cohere v4.0-pro production lock |
| **W07-beta-deploy** | 2026-05-06 | `247bb49` + `2222758` | F1.7-mock smoke + F5.4 viewport + F6 Phase Gate PASS — Microsoft Entra ID auth scaffold + mock auth bridge + rate limiting + audit logging + error handling polish + mobile responsive baseline |
| **W08-beta-deploy-sprint2** | 2026-05-06 | `ccdddf4` | F5 Langfuse SDK + cost dashboard + feedback + alerts + F4.4 admin auth + F6 W08 closeout cascade(C07 + C08 + C12)|
| **W09-beta-internal-testing** | 2026-05-06 | `8e78fd7` + `bac445a` | C11 dependency_overrides cleanup + F6 cascade + W10-beta-iteration phase folder kickoff;**W9 D1 三方 alignment outcome 2026-05-26**(Q11 operational committed early June 2026 real;Pattern A SPA+API + `ekp-beta.ricoh.com` confirmed)|
| **W10-beta-iteration** | 2026-05-06 | `7374dd4` + `a3d7c0e` | F5.1 tabletop + F5.3 review + F6 + W11 phase folder kickoff governance;cost dashboard real-time wire(`backend/observability/realtime_cost.py` + `alerts.py`);W11 D1 pricing rate Option B(placeholder + spend cap proxy) |
| **W11-staged-rollout-25** | 2026-05-08 | `4ec56d5` + `956d379` + `1431e73` + `49a634b` + `44a52cb` | **PARTIAL PASS verdict + UI sprint pivot triggered**;Mode B local dev unblock + W12 UI sprint pivot governance prep;**architecture.md v5.1 → v6 amendment landed**(UI Tier 1 expansion 9 views + hybrid auth model);ADR-0014(hybrid auth SSO + self-register)+ ADR-0015(UI Tier 1 expansion Dify-leaning)sister ADRs landed |
| **W12-ui-foundation-discovery** | 2026-05-09 | `dca5135` + `00a1dba` + `880099a` | UI sprint cycle Phase 1 of 4 — F1 Q22 email vendor default ACS + C13 component card + F4.13 USER-DEFERRED CAVEAT;**Q22 NEW Resolved** Email Verification Service vendor default ACS per ADR-0014 |
| **W13-user-facing-views** | 2026-05-09 | `a15182e` + `4f2c4cc` | UI sprint cycle Phase 2 of 4 — F1 routing restructure + theme provider + dark mode toggle + V1-V4 user-facing views(landing + register + verify + login + chat refactor);**ADR-0016 landed**(argon2-cffi → hashlib.scrypt stdlib R8 mitigation H2 ADR per strict reading)|
| **W14-admin-views** | 2026-05-09 | `641b328` + `a4213d0` + `9257993` + `4b202ce` + `dc68d46` | UI sprint cycle Phase 3 of 4 — V2 Admin Dashboard refactor + V3-V4 KB Detail tabs + cross-cutting verification(Stepper preserved + token audit pass + sidebar/UserMenu/Breadcrumb baseline preserved);CO_F5d-cont session-token mode + CO_F4_error_boundary W15 follow-up |
| **W15-polish-closeout** | 2026-05-09 | `bf01091` + `00b2262` + `60c812d` + `88320b9` + `40b4d34` + `0943ab1` | UI sprint cycle Phase 4 of 4 FINAL — F1 V5 Eval Console + F2 V6 Debug View(custom Collapsible 6-stage)+ F3 responsive/a11y + **MILESTONE entire frontend `[oklch(...)]` = 0 hits globally** + F4 Playwright E2E + pixel diff baseline harness(13 tests + 7 NEW files);**Tier 1 UI sprint cycle FINAL marker landed** — 9 views × 6+ components × hybrid auth × ACS email × responsive/a11y/E2E/pixel diff baseline |
| W16-beta-deploy | _draft 2026-05-09(rolling JIT thin skeleton)_ | `84d030e` + `3a509c4` + `adb89e5`(F5 cascade + audit-tail) | **F5 backend stub closure cascade DONE**(`debug/trace/{id}` + KB doc listing + CORS audit-tail);**F1-F4 still Track-A-blocked** pending IT cred populate event + R-B1 closure(Azure DELETE cleanup / ACS pip install / `.env.production` / Cohere Marketplace billing / 25% rollout / daily metric monitor / Q15 weekly signal report)— parallel-track to W17 |
| **W17-beta-hardening** | 2026-05-10 | `86a4403` D0 / `6edd9ef` F0 ADRs / `9ee636c` F4 / `2453a50`+`5c5df92` F1 / `fb0253a` F0b ADR-0017 / `7cca23e` F2 / `7f446fb` F3 / `414a21e` F5 / `2d71b1e` F6 / `(F7 closeout)` | Beta hardening(AI-controllable backlog, parallel to W16)— **F1 Postgres persistent backing**(ADR-0023;`PostgresKBBackend`/`PostgresUsersStore` + `make_kb_backend`/`make_users_store` factories;in-memory fallback;**CO18 CLOSED**;🚧 F1.5b runtime smoke deferred)+ **F0b ADR-0017**(R8 mitigation pattern, 5th occurrence)+ **F2 auth-transport hardening**(httpOnly cookie + CSRF double-submit + `/auth/refresh` rotation + verify-email auto-login per ADR-0022;**CO_F5_refresh + CO_F5_cookie CLOSED**)+ **F3 RAGAs 4-metric integration**(→ `/eval/run`+`/eval/shootout`;CI-tested at LLM-judge boundary;🚧 F3.5b live-verify deferred;CO_W15_F1_eval_set_v1 OPEN)+ **F4 frontend hardening bundle**(Documents tab real wire + lint orphan + Cohere naming canon + CO_W15_F2_langfuse_url CLOSED)+ **F5 a11y + dark-mode verify**(`[oklch`=0 milestone preserved;V7/V8 browser-verified;`<th scope>` fix)+ **F6 Vitest+RTL scaffold**(CO_W15_F4_vitest_baseline_gap CLOSED);**phase Gate PASS**;🚧 F1.5b + F3.5b R8/Azure-key-bound runtime verifications deferred W18+/CO17 |
| W18+ | _not pre-created_ | _pending W17 closeout decision_ | (rolling JIT — W18+ phase folder NOT pre-create per CLAUDE.md §10 R1;candidates = W16 F1-F4 if Track A cred lands / Tier 2 prep governance Q12 / user local-dev-setup task)|

**累計**:**16 phase closed**(W1-W15 + W17;Tier 1 12-week sprint extended via W12-W15 UI sprint cycle pivot — architecture v5.1 → v6 amendment + 9 views — then W17 Beta-hardening parallel to W16);**W16 status:draft**(F5 backend stub closure cascade DONE;F1-F4 Track-A-blocked pending IT cred populate event + R-B1 closure — parallel-track to W17)— **W17-beta-hardening closure 2026-05-10**(phase Gate PASS;🚧 F1.5b Postgres-path runtime smoke + F3.5b RAGAs live-verify deferred W18+/CO17)

---

## 第十三部分:行為規範(畀 AI 助手)

每次 reply 之前,確保:

### 必做

- [ ] 對齊 §1 Karpathy baseline(think → simple → surgical → goal)
- [ ] 對齊 H1–H6 hard constraints(若觸發,**第一句就 STOP and explain**)
- [ ] 需要時可代為啟動 / 重啟本地服務(uvicorn / next dev / docker-compose / Azurite 等)協助開發 + 測試;優先用 background 模式(`run_in_background`)避免阻塞 session,完成後記得 stop;**destructive 服務操作**(刪 docker volume / `down -v` / kill 用戶自己嘅 process)仍需先確認
- [ ] 跨 component 修改前先讀對應 `components/Cn-*.md` design note
- [ ] 開始 code 前確認該 phase 已有 plan.md + checklist.md(R1)
- [ ] 起草新 phase plan/checklist 前先讀「最近 closed phase」樣板(章節 / Day 數 / 細節水平必須一致)
- [ ] commit message 用 Conventional Commits(`<type>(<scope>): <description>`)+ co-author per CLAUDE.md §4.2
- [ ] 每 commit 對應一個 checklist 項目 + progress.md Day-N entry mention(R2)
- [ ] OQ resolved 同步更新 decision-form.md AND progress.md Day-N(R4)
- [ ] Daily progress.md 維持「Actual vs Planned Effort」table(estimates vs actual variance)
- [ ] Phase 收尾寫 retro(What worked / What didn't work / Surprises / Carry-overs / ADR triggers / Phase Gate result)
- [ ] 用**繁體中文**回覆(team primary language per CLAUDE.md §11)

### EKP 紀律 9 項自檢(每 PR 前 + 每 commit 後)

per [`CLAUDE.md §12 self-verification`](../../../CLAUDE.md):

1. **Architecture lock(H1)**— `docs/architecture.md §3 + §4` 任何 component 改動 → ADR 寫咗未?
2. **Vendor lock(H2)**— 加新 dependency 之前 STOP and ask?(utility / type stub / dev dep 例外)
3. **Dify reference(H3)**— `references/dify/` 純 read,絕無 copy-paste / import / branding clone
4. **Tier 1 boundary(H4)**— GraphRAG / multi-agent / multi-tenancy / multi-modal / auto-sync / fine-tune 全部 out
5. **Security(H5)**— 無 hard-code tenant ID / subscription ID / connection string;`.env` gitignored
6. **Test coverage(H6)**— `backend/{ingestion,retrieval,pipeline,eval}/` + `api/routes/query.py` 寫 code 同步寫 test
7. **Component spine** — 每 file 明確歸屬 1 個 Cn(no cross-component scattering)
8. **PROCESS.md classification** — task → Phase / Change / Bug-fix / Trivial 之前 propose to user
9. **Rolling planning** — 無預寫多個未來 phase plan

### Coding conventions 速查

- **Python 3.12+** + `mypy --strict` clean + async by default + Pydantic v2 + structlog JSON
- **TypeScript strict** + Next.js App Router only + Server Components default + shadcn/ui only + design tokens via `frontend/lib/theming/tokens.ts`(無 hardcode 顏色 / spacing)
- Naming:`snake_case.py` / `kebab-case.tsx` / Python `snake_case` / TS `camelCase` / Class `PascalCase` / Const `UPPER_SNAKE` / DB+Search field `snake_case`
- Comments 解釋 **why**,唔係 **what**;TODO format `# TODO(<owner>): <description> [<issue-id>]`
- 絕不 commit:secret / API key / PII / `.env` / `references/dify/` 任何 file

### 唔做

- [ ] 唔預寫多個未來 phase plan(rolling planning!)
- [ ] 唔刪 V1 archive(冇 V1 archive — Tier 1 由 W1 D1 開始)
- [ ] 唔讓 AI 單方面決定不可逆操作(git tag push / git mv 大量檔案 / `git reset --hard`)— 必須先報告
- [ ] 唔執行 `--no-verify` / `--force` git 命令(除非用戶明確授權)
- [ ] 唔刪除未勾選 checklist `[ ]` 項目(只可 `→[x]` 或加 🚧 + reason)
- [ ] 唔喺 retrospective 寫具體未來 sprint task(rolling = 下 phase kickoff 先寫)

---

## 第十四部分:今天嘅任務(**唯一需要用戶填寫嘅部分**)

> 喺每個新 session 開始,把整份 prompt copy 之後,只改下方呢一節即可。

```
今天嘅任務:__________________

例:
- 「啟動 W3 Day 1 — F1 Cohere Rerank v3.5 integration」
  → AI 將先 verify W2 Gate 1 verdict pass + W3 plan.md status flip active,然後讀 W3 plan §F1 + components/C04 §3,write code

- 「繼續 W2 D5 — trigger Gate 1 live eval(VPN disconnected)」
  → AI 跑 `scripts/run_populate_sanity.py` + `backend/eval/runner.py`,collect R@5 verdict,update progress.md retro + commit `docs(planning): W02 Gate 1 verdict — R@5 = X.XX (pass/fail)`

- 「處理 BUG-002 — `/query` returns 502 on empty KB」
  → AI 判斷 Bug-fix workflow,propose `docs/03-implementation/bugs/BUG-002-{kebab}/report.md` draft,等 Chris confirm Sev + repro accuracy 先 investigate

- 「Review W2 retro + 同步準備 W3 plan active flip」
  → AI 讀 W2 progress.md retro + W3 draft,同 user 對齊 W3 範圍 + 確認 carry-overs C1-C8 處理時序

- 「加 Voyage Rerank 入 W4 shootout」
  → AI 識別 H2 vendor change,STOP and propose ADR,等 user approve 先 update W4 draft + write ADR
```

---

## 附錄:本 prompt 自身嘅維護

### 何時更新

| 觸發 | 更新位置 |
|---|---|
| Phase 收尾 | §11 Open Items(合併 retro carry-overs)+ §12 milestones(加一行)+ §9 OQ status(若有變)|
| 發現 spec / CLAUDE.md 修訂(§5 H1–H6 / §10 R1–R5 / §11 Tier 2 list)| §2 最高指導原則 + §4 權威排序 + §13 紀律自檢 9 項 |
| Phase 切換(W2 → W3 → W4)| §3 component status + §10 sprint awareness 對應行 + §12 milestones |
| 重大 OQ resolved(影響架構)| §9 OQ status + 對應 component status |

### 何時退役

- Tier 1 完成(W12 production launch 後)→ Tier 2 規劃啟動,本 prompt 變歷史紀念物,改用 Tier 2 對應 prompt(如有)
- 中途若 §3 13 component spine 大改,本 prompt §3 + §13 全部重寫

---

**Last Updated**:2026-05-10(W17-beta-hardening closeout housekeeping catch-up — §2 "v5 frozen"→v6 + Cohere v3.5→v4.0-pro + ACS/Postgres added to the locked-vendor list;§3 C02 in-memory→Postgres-backed(ADR-0023, CO18 CLOSED)+ C06 RAGAs integrated(W17 F3)+ C08 stub cascade DONE + Implemented + C11 cookie/CSRF transport(ADR-0022, CO_F5_* CLOSED)+ users_repo Postgres-backed;§4 authority-order header v5→v6;§10 W16 row note(F5 done, F1-F4 Track-A-blocked)+ W17 row added(closed, Gate PASS)+ W18+ not-pre-created;§11 carry-overs replaced W15 D5 → W17 closeout(W17 CLOSED block: CO18 + CO_F5_* + CO_W15_F1_backend + CO_W15_F2_* + CO_F3a-c + CO_W15_F4_vitest;partially-closed CO_W15_F3_dark_mode;NEW 🚧 F1.5b + F3.5b under CO17;OPEN CO_W15_F1_eval_set_v1)+ ADR status 15→22 landed + next-NNNN 0017→0024(ADR-0017 R8-pattern + 0018-0021 audit batch + 0022/0023 W17 F0)+ R8 4→5 occurrences(ADR-0017 landed)+ converse-confirmed(npm registry not blocked);§12 milestones W16 row updated + W17 row added;累計 15→16 phase closed;§9 OQ unchanged(no new OQ W17))
**Maintainer**:Chris(技術 Lead)+ AI 助手共同維護
**File location**:`docs/12-ai-assistant/01-prompts/01-session-start.md`
**Companion**:`02-compact-session.md`(每個 session `/compact` 之前用)

---

## Update history

| Date | Phase | Updates |
|---|---|---|
| 2026-05-04 | W02 D5 closeout | 初版(基於 sample-1 結構,EKP-specific 內容:12 components / H1-H6 / R1-R5 / 21 OQ snapshot / W1-W12 timeline)|
| 2026-05-05 | W06 D5 closeout housekeeping | §9 OQ status updated 7→11 Resolved + 14→10 Open(Q5 / Q17 / Q18 / Q21 closed cycle);§10 Sprint table all W1-W6 closed + Gates verdict landed(Gate 1 PASS R@5=0.9722 / Gate 2 PARTIAL PASS confirmed / Gate 3 READY);§11 W6 carry-overs C1-C10 replaces stale W2 carry-overs;§12 milestones W3-W6 rows added 累計 6/12;ADR status update(0001-0011 batch created W2 D5 cont 2026-05-04;ADR-0012 reservation status documented per W6 retro)|
| 2026-05-05 | W06 D5 stakeholder approval cycle cascade | §9 OQ status 11→16 Resolved + 10→5 Open(Q7+Q9+Q10+Q11+Q12 stakeholder approve 落地);§10 Sprint table W7-8 row updated active;§12 milestones W7 row updated active;Last Updated reflect amendment + ADR-0012 formal record + Beta plan v1 active + W7 active |
| 2026-05-09 | W15 D5 closeout housekeeping catch-up(Tier 1 UI sprint cycle FINAL)| §9 OQ status 16→17 Resolved + Q22 NEW added(total 21→22)+ Q11 W9 D1 三方 alignment + Q14 W11 D2 corpus scope clarification context;§10 Sprint table extended W7-W16+ rows + Tier 1 UI sprint cycle FINAL gate added + Production launch gate added;§11 carry-overs replaced W6 D5 → W15 D5 closeout(Track A IT cred + R-B1 closure + 4-sprint user smoke deferred backlog + W14/W15 CO_* + R8 4 occurrences cumulative + ADR-0017 reservation candidate + ADR-0013 reserved AF3);§12 milestones added 9 rows W7-W15 + W16 draft + W17+ rolling JIT discipline preserved;架構 v5.1 → v6 amendment + ADR-0014/0015/0016 landed;**W16 status:draft**(rolling JIT thin skeleton);累計 6→15 phase closed |
| 2026-05-09 | W15 D5 component status follow-up(post §9-§12 catch-up)| §3 component count 12 → 13 + C13 Email Verification Service NEW row added(ACS per Q22 + ADR-0014;W12 D1 v6 amendment + W13 D5 implementation);C04/C05/C06/C09/C10 status 🟢/🟡/⏳ → ✅ Implemented(post-W6/W3/W4/W12-W15/W3-W15 milestones);C08/C11 → 🟡 Mostly Implemented(C08 4-stub closure W16 F5 pending;C11 Track A IT cred consumption W16 F1 pending);Status header date 2026-05-04 W2 → 2026-05-09 W15 D5;§14 退役 line 12 → 13 component spine;Note added re COMPONENT_CATALOG.md §11 Tier 2 trigger matrix stale "C13 Workflow Engine"(catalog amendment W17+ housekeeping)|
| 2026-05-10 | W16 — dev-server policy amendment(user directive)| §13 行為規範:由「唔做」list 移除「唔啟動長期運行 server process」;改放「必做」list 作正面授權 — AI 可代為啟動 / 重啟本地服務(uvicorn / next dev / docker-compose / Azurite)協助開發 + 測試,優先 background 模式,destructive 服務操作(刪 volume / `down -v` / kill 用戶 process)仍需先確認。Rationale:實際開發需 AI 代執行服務操作以提升協作效率;`run_in_background` 已解決舊「同 Claude Code 衝突」顧慮 |
| 2026-05-10 | W17-beta-hardening closeout housekeeping catch-up | §2 v5→v6 + Cohere v3.5→v4.0-pro + ACS/Postgres added to locked-vendor list;§3 C02(in-memory→Postgres-backed per ADR-0023, CO18 CLOSED, 🚧 F1.5b)+ C06(RAGAs integrated W17 F3, CO_W15_F1_eval_set_v1 OPEN)+ C08(stub cascade DONE, →✅ Implemented, +cookie/CSRF transport)+ C11(+cookie/CSRF transport per ADR-0022 CO_F5_* CLOSED, +users_repo Postgres-backed);Status-header date W15 D5→W17;§4 authority-order header v5→v6;§10 W16 row note(F5 done, F1-F4 Track-A-blocked)+ NEW W17 row(closed, Gate PASS)+ W18+ not-pre-created;§11 "已知未解" header W15 D5→W17 + W17 CLOSED block(CO18 + CO_F5_refresh/cookie + CO_W15_F1_backend + CO_W15_F2_langfuse_url/backend + CO_F3a-c + CO_W15_F4_vitest_baseline_gap + CO_W14_process_grep_verify applied)+ partially-closed CO_W15_F3_dark_mode_visual_verify + NEW 🚧 F1.5b/F3.5b under CO17 + OPEN CO_W15_F1_eval_set_v1;ADR status block 15→22 landed + next-NNNN 0017→0024(ADR-0017 R8-pattern landed + 0018/0019/0020/0021 audit batch + 0022/0023 W17 F0)+ R8 4→5 occurrences + ADR-0017 landed + converse-confirmed(npm/PyPI registry not R8-blocked, only binary CDNs)+ CO16/CO17/CO18/CO19 status;§12 milestones W16 row updated(F5 done)+ NEW W17 row + W18+ not-pre-created + 累計 15→16 phase closed;§9 OQ unchanged(no new OQ W17 — Q8 4-metric note holds, Q14 SME labels = existing eval-set-v1 blocker);Last-Updated reflects all the above |
