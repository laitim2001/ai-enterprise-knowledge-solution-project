# CLAUDE.md — EKP Project Standing Instructions

> **Claude Code:呢份文件係你嘅 standing instructions。每次 session 開始必須先讀,然後再做任何嘢。**
> **本 instruction 採用 Strict Mode**:架構決定一旦 lock 就唔可以單方面改,凡涉及 architectural change 必須 stop and confirm。

---

## 0. Quick Identity Check(每 session 開始 30 秒讀)

| 項目 | Value |
|---|---|
| Project | **Enterprise Knowledge Platform (EKP)** — Tier 1 Foundation |
| First Use Case | Drive Project — Ricoh internal user manuals |
| Primary Spec | `docs/architecture.md`(v5 frozen as of 2026-04-27) |
| Phase | Tier 1 / 12-week sprint(POC 6w → Beta 4w → Rollout 2w) |
| Strict Mode | **ON** — see §5 Hard Constraints |
| Behavioral Baseline | **§1(Karpathy guidelines)** — universal coding mindset,適用於所有 code change |
| Decision Owner(architecture) | Chris(技術 Lead) |
| Decision Owner(scope / business) | Stakeholder(via decision-form.md) |

---

## 1. Behavioral Baseline(Karpathy Guidelines — universal)

> **Source**: `andrej-karpathy-skills` plugin(`karpathy-guidelines`,`alwaysApply: true`)
> **適用範圍**:**所有** code change、review、refactor —— 與 §2–§14 嘅 project-specific rule 並行,優先級僅次於 §5 Hard Constraints。
> **Tradeoff**:呢套 guideline bias toward caution over speed。Trivial task 可以用 judgment,但 non-trivial task 必須跟。

### 1.1 Think Before Coding —— 思考先,寫 code 後

**核心**:Don't assume. Don't hide confusion. Surface tradeoffs.

開始實作之前:
- 把 assumption **明確講出嚟**;唔肯定就問,唔好估
- 如果有多種詮釋,**全部 present**,唔好默默揀一個
- 如果有更簡單做法,**講出嚟**;有需要就 push back
- 唔清楚就 stop,**講明邊度唔清楚**,然後問

呢條同 §13 "When in doubt → ask, don't guess" 互相強化。

### 1.2 Simplicity First —— 最少嘅 code 解決問題

**核心**:Minimum code that solves the problem. Nothing speculative.

- 唔加未要求嘅 feature
- 唔為 single-use code 做 abstraction
- 唔加未 request 嘅 "flexibility" / "configurability"
- 唔處理冇可能發生嘅 error scenario
- 寫咗 200 行但其實 50 行夠 → **重寫**

自我檢查:「senior engineer 會話呢段 over-engineered 嗎?」答 yes 就簡化。

對 EKP 嘅意義:Tier 1 階段 simplicity wins(已喺 §13 寫明,呢條係執行細則)。

### 1.3 Surgical Changes —— 精準改動,只清自己嘅 mess

**核心**:Touch only what you must. Clean up only your own mess.

改 existing code 時:
- **唔好**「順手」改 adjacent code、comment、formatting
- **唔好** refactor 冇 break 嘅嘢
- **Match existing style**,即使你會 prefer 另一種寫法
- 見到無關嘅 dead code → **mention,but 唔好刪**

改動製造嘅 orphan(import / variable / function 因你嘅改動而 unused):
- **要刪**(你製造嘅 mess 自己清)
- **唔好** 刪 pre-existing dead code,除非用戶要求

驗證標準:**每一行改動都要可以 trace 返用戶嘅 request**。

對 EKP 嘅意義:強化 §4.3 "One feature per PR" + §4.4 "Files Claude Code 絕不 touch" —— 呢條係 mindset,§4 係硬規則。

### 1.4 Goal-Driven Execution —— 定義成功標準,loop 到 verify 為止

**核心**:Define success criteria. Loop until verified.

把 task 轉做 verifiable goal:
- "Add validation" → "寫 test for invalid input,然後 make them pass"
- "Fix the bug" → "寫 test reproduce 個 bug,然後 make it pass"
- "Refactor X" → "Refactor 前後 test 都 pass"

Multi-step task 要先講 plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

**Strong success criteria** 等你可以獨立 loop;**weak criteria**(如「make it work」)會逼用戶不斷 clarify。

對 EKP 嘅意義:同 §12 Self-Verification checklist 互補 —— §12 係 task done 嘅 gate,§1.4 係 task start 嘅 framing。

---

**呢套 guideline 生效嘅 signal**:
- Diff 入面 unnecessary change 變少
- 因 over-engineering 而要重寫嘅情況變少
- Clarifying question 出現喺 implementation **之前**,而唔係 mistake 之後

---

## 2. Document Routing(when to read what)

**呢份 CLAUDE.md 唔重複任何 spec 內容**。當你需要做嘢,跟以下 routing 去搵 source of truth:

| 情況 | 必讀文件 | 補充 |
|---|---|---|
| **Multi-day phase / sprint work**(任何超 single session implementation) | [`docs/01-planning/PROCESS.md §2`](./docs/01-planning/PROCESS.md) + active phase folder | Per phase plan / checklist / progress — 詳見 §10 |
| **Change to existing feature**(modify behavior, < 3 days) | [`docs/01-planning/PROCESS.md §3`](./docs/01-planning/PROCESS.md) + new instance `docs/03-implementation/changes/CH-{NNN}-{kebab}/` | Pre-doc:**spec.md**(approved by user)→ derive checklist + progress;AI auto-classify per PROCESS.md §1 |
| **Bug-fix**(fix incorrect / broken / regressed behavior) | [`docs/01-planning/PROCESS.md §4`](./docs/01-planning/PROCESS.md) + new instance `docs/03-implementation/bugs/BUG-{NNN}-{kebab}/` | Pre-doc:**report.md**(severity Sev1-Sev4)→ derive checklist + progress;Sev1/Sev2 mandatory postmortem |
| **改 / 新加 component**(明確涉及 EKP 12 modules 之一)| [`docs/02-architecture/COMPONENT_CATALOG.md`](./docs/02-architecture/COMPONENT_CATALOG.md) + 對應 `components/Cn-{kebab}.md`(若已存在)| 識別 component → spec ref + dep + tech + status,再跳去 architecture.md 對應 section 落實作 |
| **Risk-related decision / mitigation update** | [`docs/01-planning/RISK_REGISTER.md`](./docs/01-planning/RISK_REGISTER.md)(living)+ `docs/architecture.md §8`(frozen baseline)| 新 risk / status update 入 living register,§8 不動 |
| Setup local dev environment | `docs/setup.md` | 包括 Azurite、Langfuse、docker-compose、env vars |
| 寫 / 改 backend feature | `docs/architecture.md` §3 + §4 | RAG core + application architecture |
| 寫 / 改 frontend feature | `docs/architecture.md` §5 + Dify ref(see §7) | UI specifications + visual identity policy |
| 加 / 改 API endpoint | `docs/api-contract.md`(W2 末 ready) | 在此之前用 `docs/architecture.md` §4.4 + §4.5 |
| 加 vendor / 換 component | **STOP** — 必須先確認(see §5.2 Hard Constraint H2) | 寫 ADR `docs/adr/`(W2 末 framework ready) |
| 改架構 / 違反 §3 / §4 設計 | **STOP** — 必須先確認(see §5.1 Hard Constraint H1) | 同 |
| 處理 Tango.us / 多 format ingestion | `docs/architecture.md` §3.3 | 注:source 係 Word/PDF/PPT,**不是** Tango |
| Chunking 邏輯 | `docs/architecture.md` §3.3 + §3.5 | layout-aware,not character-based |
| 寫 eval / test | `docs/eval-methodology.md` + `docs/eval-set-v0.yaml`(W1 ready) | RAGAs + 30–50 條 ground truth |
| 涉及 Dify reference | `references/REFERENCE_USAGE.md`(W1 Day 1 setup) | 嚴禁 copy-paste,只可 layout 借鑒 |
| Stakeholder-facing 變動 | `docs/decision-form.md`(W1 ready) | 確認 21 條 OQ status |
| 評估 GraphRAG / multi-agent / multi-tenancy | **STOP** — 呢啲係 Tier 2,Tier 1 唔做 | See `docs/architecture.md` §11 trigger matrix |

**Default behavior**:如果你唔確定一個 task 屬邊個 doc 範圍,**ask before guessing**。

---

## 3. Coding Conventions

### 3.1 Backend(Python)

- **Python 3.12+** required
- **Type hints required everywhere**(`mypy --strict` clean)
- **Async by default**(FastAPI、httpx、Azure SDK 全部用 async client)
- **Pydantic v2** for all schemas(see `backend/api/schemas/`)
- **Logging via structlog**(JSON output for Langfuse correlation)
- **Imports**:absolute imports only,no relative imports across modules
- **Function length**:soft cap 50 行,超過要拆
- **Test framework**:pytest + pytest-asyncio
- **Coverage target**:critical pipeline modules ≥ 80%(`backend/pipeline/`、`backend/retrieval/`、`backend/ingestion/`)
- **Linter**:ruff(config in `pyproject.toml`)
- **Formatter**:ruff format

### 3.2 Frontend(TypeScript / Next.js 14)

- **TypeScript strict mode**(no `any`,no `@ts-ignore` 除非有 comment 解釋)
- **App Router only**,no Pages Router
- **Server Components by default**;Client Components 必須有 `"use client"` directive + 解釋 comment
- **shadcn/ui** components only — no Material UI、Ant Design、Chakra
- **Tailwind utility classes**;custom CSS 限 `frontend/styles/` 全局
- **Design tokens via `frontend/lib/theming/tokens.ts`** — 絕對唔可以 hardcode 顏色 / spacing
- **State management**:React state for local;Zustand for cross-component;**no Redux**
- **Data fetching**:Vercel AI SDK 嘅 `useChat` for streaming;TanStack Query for non-streaming
- **Test framework**:Vitest + React Testing Library
- **Linter**:ESLint(Next.js default + Tailwind plugin)
- **Formatter**:Prettier

### 3.3 共通

- **Naming**:
  - Files:`snake_case.py`、`kebab-case.tsx`
  - Variables / functions:`snake_case`(Python)、`camelCase`(TS)
  - Classes / Components:`PascalCase`
  - Constants:`UPPER_SNAKE`
  - Database / Azure Search field:`snake_case`(全小寫)
- **Comments**:解釋 **why**,唔係 **what**(code 自己應該講 what)
- **TODO comments format**:`# TODO(<owner>): <description> [<issue-id>]`
- **絕不 commit**:secret、API key、PII、`.env` 內容、`references/dify/` 任何 file

---

## 4. Git & Workflow Conventions

### 4.1 Branch naming

```
main                          ← protected, 永遠 deployable
feat/<area>-<short-desc>      ← e.g. feat/ingestion-docx-parser
fix/<area>-<short-desc>       ← e.g. fix/retrieval-rrf-edge-case
chore/<short-desc>            ← e.g. chore/update-deps
docs/<short-desc>             ← e.g. docs/api-contract-v1
adr/<adr-number>-<short>      ← e.g. adr/0012-langgraph-deferred
```

### 4.2 Commit message(Conventional Commits)

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

Types:`feat` / `fix` / `chore` / `docs` / `refactor` / `test` / `perf` / `style`
Scope:`ingestion` / `retrieval` / `generation` / `pipeline` / `kb` / `eval` / `api` / `frontend` / `infra`

Example:
```
feat(retrieval): add Cohere Rerank v3.5 client

Wire Cohere via Azure Marketplace billing.
Fallback to Azure built-in semantic ranker on outage.

Refs: docs/architecture.md §3.2
```

### 4.3 PR Rules

- **One feature per PR**,no kitchen-sink PRs
- **PR description 必須**:link to spec section、list test scenario、include screenshots(frontend)
- **Reference Dify**(若有):必須在 PR comment 標 `Reference: dify/<path>`(see §7)
- **Pre-merge checklist**:tests pass、coverage 不降、no linter warning、ADR updated(若 architecture change)

### 4.4 Files & folders Claude Code **絕不** touch

- `.git/`
- `references/dify/`(read-only,license risk)
- `.env`、`.env.local`、any file with credentials
- `infrastructure/secrets/`(若存在)
- `docs/architecture.md` 嘅 §1–§14(content lock,只有 stakeholder approve 後 increment version)

---

## 5. Hard Constraints(Strict Mode)

呢啲 constraint **violate 即係 broken project**。Claude Code 遇到以下情況**必須 STOP and ask**:

### 5.1 H1 — Architectural Change Constraint

**「Architectural change」嘅定義**:任何符合以下其一嘅變動 ——

- 加 / 改 / 刪 `docs/architecture.md` §3(RAG Core)或 §4(Application Architecture)入面提到嘅 component
- 改 vendor / service(e.g. Azure AI Search → Pinecone、Cohere → Voyage 不在 W4 shootout 範圍)
- 改 storage layout(e.g. blob path convention、search index schema)
- 改 multi-KB architecture(e.g. KB-id namespacing rule)
- 改 8 個視 view 嘅其中任何一個嘅 layout philosophy(可以 polish,但唔可以 redesign)
- 加 Tier 2 feature(GraphRAG、multi-agent、multi-tenancy、workflow)入 Tier 1 codebase

**Required behavior**:
1. **STOP** 寫 code
2. 喺 chat 講明:
   - 你想做咩 architectural change
   - 為何 v5 spec 唔啱
   - Proposed 替代方案
3. 等 user 回應「approved + write ADR」先繼續
4. 寫新 ADR 入 `docs/adr/`(format see §6)

**唔屬於 architectural change**(可以自行做):
- Bug fix
- Refactor 內部實作而冇改 interface
- 加 internal helper function
- UI polish(spacing、typography、micro-interaction)
- 加 test
- 加 logging / observability

### 5.2 H2 — Vendor / Dependency Constraint

**Tier 1 嘅 vendor list 已 lock**(see `docs/architecture.md` §3.2 + §14):

| Layer | 已 lock vendor |
|---|---|
| Vector + BM25 | Azure AI Search Standard S1 |
| Embedding | Azure OpenAI text-embedding-3-large |
| Reranker(baseline) | Cohere Rerank v3.5(W4 shootout 後可換 Voyage / ZeroEntropy / Azure built-in) |
| LLM(synthesis) | Azure OpenAI GPT-5.5 |
| LLM(judge) | Azure OpenAI GPT-5.4-mini / GPT-5.5 Pro |
| Document parsing | Docling + python-pptx |
| Image storage | Azure Blob(local: Azurite) |
| Observability | Langfuse |
| Eval | RAGAs |
| Frontend | Next.js 14 + shadcn/ui + Tailwind |
| Backend | FastAPI + uvicorn |

**加新 dependency 嘅唯一合法路徑**:
1. STOP and ask
2. 解釋為何現有 stack 唔夠
3. 等 approval
4. 寫 ADR documenting decision

**例外**(可以自行加):
- Pure utility library(e.g. `tenacity` for retry,`structlog` for logging)
- Type stub package(`types-*`)
- Dev dependency(test、linter、formatter)

### 5.3 H3 — Dify Reference Constraint

`references/dify/` 係 **read-only reference**,唔係 dependency。

**絕對唔可以做**:
- Copy-paste 任何 Dify code 入 EKP codebase
- Import / require 任何 Dify package
- Fork Dify 或 vendor 一個 Dify instance
- Replicate Dify branding(logo、primary color、marketing copy)

**可以做**:
- Read Dify source 學 layout、interaction、component composition
- Reference Dify API design 作為 endpoint pattern inspiration
- 喺 PR comment 標 `Reference: dify/web/app/components/datasets/...`

詳見 `references/REFERENCE_USAGE.md`(W1 Day 1 setup)。

### 5.4 H4 — Tier Boundary Constraint

**Tier 1 implementation 唔可以包含 Tier 2 feature**,即使你覺得「順手做埋」。

Tier 2 list(`docs/architecture.md` §11):
- GraphRAG / Knowledge Graph
- L4+ multi-agent orchestration
- Workflow / plugin builder
- Multi-tenancy
- Multi-modal retrieval(B 類純圖片搜索)
- Multi-language(JP / ZH)
- Auto-sync from external source
- Custom LLM fine-tuning

**「Tier 2 friendly」係要求**:Tier 1 architecture 必須 modular、extensible、MCP-ready,等 Tier 2 將來可以加。但**任何 Tier 2 feature 嘅 implementation 都係 out of Tier 1 scope**。

### 5.5 H5 — Security & Privacy Constraint

- **絕不 log**:full LLM prompts containing user query payload to plaintext file(只 log to Langfuse,encrypted at rest)
- **絕不 commit**:Azure connection string、API key、Cohere key、Microsoft Entra ID secret
- **絕不 hard-code**:tenant ID、subscription ID、resource name(都 from env var)
- **Secrets management**:POC 用 `.env`(gitignored);Beta+ 用 Azure Key Vault
- **PII handling**:Drive Project 假設無 PII;若 future KB 含 PII,trigger Tier 2 review

### 5.6 H6 — Test Coverage Constraint

以下 module 寫 code **必須同步寫 test**:
- `backend/ingestion/parsers/`
- `backend/ingestion/chunker/`
- `backend/retrieval/`
- `backend/pipeline/query_pipeline.py`
- `backend/pipeline/crag_loop.py`
- `backend/api/routes/query.py`
- `backend/eval/`

UI component test 為 nice-to-have(視 sprint 進度),其他 backend 鼓勵但唔強制。

---

## 6. Architecture Decision Record (ADR) Format

任何違反 H1 / H2 嘅變動,approval 後必須寫 ADR。Format:

```markdown
# ADR-NNNN: <Title>

**Date**: YYYY-MM-DD
**Status**: Proposed | Accepted | Superseded by ADR-MMMM
**Approver**: <Name>

## Context
咩 trigger 呢個決定?咩 constraint?

## Decision
具體做咩?

## Alternatives Considered
睇過咩其他選擇?點解 reject?

## Consequences
- Positive: ...
- Negative: ...
- Neutral: ...

## References
- spec section
- external link
- previous ADR(若 supersede)
```

ADR 文件位置:`docs/adr/NNNN-short-title.md`,NNNN 係 4-digit zero-padded sequential。Index 喺 `docs/adr/README.md`。

頭 11 個 ADR(0001-0011)由 v5 §13.0-§13.11 Decision Log promote 而來,**W2 D5 cont 2026-05-04 batch 創建完成**(§13.10 "Other v3 inherits" 屬 meta-rollup,不單獨 promote)。**新 ADR 由 NNNN=0012 開始**。

---

## 7. Dify Reference Workflow(critical 重複強調)

**Setup**(W1 Day 1):
```bash
mkdir -p references && cd references
git clone --depth 1 https://github.com/langgenius/dify.git
cd dify && git log -1 > ../DIFY_PINNED_COMMIT.txt
```

`.gitignore` 要 include:
```
references/dify/
references/DIFY_PINNED_COMMIT.txt
```

**Daily usage**:
- 寫一個 EKP component 之前,**可以**去 `references/dify/web/` 搵類似 component 學 layout
- **必須**用 EKP 自己嘅 design tokens(`frontend/lib/theming/tokens.ts`),唔可以抄 Dify 顏色
- 喺 PR comment 標明 reference path:`Reference: dify/web/app/components/datasets/documents/list.tsx (layout pattern only)`
- **絕對唔可以**:`cp references/dify/...` to EKP codebase

詳細 policy 見 `references/REFERENCE_USAGE.md`。

---

## 8. Open Questions(影響 Claude Code 決策)

呢 21 條 OQ(`docs/architecture.md` §10、`docs/decision-form.md`)嘅 status 影響你嘅 default behavior:

- 任何 OQ status = **「Open」** → 用 spec 入面標明嘅 default value 繼續做,但**喺 commit message 標**:`Note: depends on OQ-Q<N> default`
- 任何 OQ status = **「Resolved」** → 直接用 resolved value,唔需要 note
- 任何 OQ status = **「Blocked」** → STOP 對應 work item,ask user

**最 critical 嘅 W1 必 resolve OQ**:Q1(format ratio)、Q2(document source access)、Q3(Azure AI Search resource)、Q4(GPT-5.5 deployment)、Q13(ground truth labeler)。其他 OQ 用 default 繼續。

---

## 9. Sprint Awareness

| Week | 你嘅 default focus(若無其他 instruction) | Hard cutoff |
|---|---|---|
| W1 | Foundation:FastAPI skeleton、Next.js skeleton、Docling .docx parser、KB CRUD、Eval set v0、Azurite local | W1 末 Gate 1 prep |
| W2 | Multi-format ingestion 完成、Hybrid retrieval baseline、Admin Console layout | **Gate 1 Decision(Recall@5 ≥ 80%)** |
| W3 | Cohere Rerank、GPT-5.5 synthesis、Citation、Chat UI streaming、PPT parser | — |
| W4 | CRAG L2、RAGAs eval automation、Reranker shootout(4-way)、加 20 條 real query | **Gate 2 Decision(4 metric within 5pp)** |
| W5 | Optimization;**conditional** L3 routing(only if Gate 2 全 pass) | — |
| W6 | Final eval、Demo prep、Beta plan | POC 結束 |
| W7-8 | Microsoft Entra ID、rate limiting、React polish、Beta deploy | — |
| W9-10 | Beta internal testing、UX iteration | — |
| W11-12 | Staged rollout 25% → 100% | Production launch |

如果 Claude Code session 邊個 week 唔清楚,**ask user "What week are we in?"** 之後再做 default focus 對應。

---

## 10. Phase Planning Workflow

> 配合 §9 Sprint Awareness:每個 sprint week 屬一個 phase,有 dedicated planning artifacts。
> Source of truth:[`docs/01-planning/PROCESS.md`](./docs/01-planning/PROCESS.md)(完整 lifecycle、template、anti-pattern)。

### 10.1 Per-Phase Artifacts(3 docs)

每 phase 喺 `docs/01-planning/W{NN}-{phase-name}/` folder 內建立:
- **`plan.md`** — Phase scope + deliverables + acceptance criteria + risks(kickoff 寫,locked,改要 changelog)
- **`checklist.md`** — Atomic checkbox items per deliverable(daily tick)
- **`progress.md`** — Daily progress + decisions + commits + 結尾 retro(v1.0 嘅 `journal.md` 已 rename per PROCESS.md v2.0)

### 10.2 Binding Rules(R1–R5,process-level constraint)

- **R1**:任何 multi-day implementation 之前必須有對應 phase `plan.md` committed。**無 plan 唔可以 implement → STOP and ask**
- **R2**:Daily commit 必須對應 `progress.md` Day-N entry(`docs(planning):` housekeeping commits 例外)
- **R3**:Plan deviation(scope change / new deliverable / 取消 deliverable)必須 log 入 `plan.md` changelog,**唔可以 silent drift**
- **R4**:OQ resolved → 同步更新 `decision-form.md` AND `progress.md` Day-N entry mention
- **R5**:Phase closeout 之前任何 architectural-adjacent decision(per §5.1 H1)必須寫 ADR

### 10.3 AI Session Start Protocol

每個 Claude session 開始(在 §0 quick identity check 之後),AI **必須順序執行以下 6 步**,先 reply 用戶第一句訊息:

1. 讀 `docs/12-ai-assistant/01-prompts/01-session-start.md`(SITUATION EKP — 12 components C01–C12 / 21 OQ snapshot / 紀律 9 項 / 權威排序 7-tier / W1–W12 timeline)
2. 讀 active phase 嘅 `plan.md`(知 scope + acceptance criteria)
3. 讀 active phase 嘅 `checklist.md`(知 next un-checked item;active phase = `git status` + 最新 W{NN}-{name} folder)
4. 讀 active phase 嘅 `progress.md` 最近 3 個 Day-N entries(知 context + blockers + carry-overs)
5. Run `git status --short` + `git log --oneline -5`(知 working tree state)
6. 唔清楚 / item acceptance criteria 模糊 → ask user(per §13 When in Doubt)

**Compact 後嘅特殊處理**:`/compact` 觸發後 context 重組,AI **必須 re-read 步驟 1–4**。原因:compact summary 對 active session work(commits / tests / files)retain ~95%,但對 standing instructions(§3 12 components / §9 OQ snapshot / §13 紀律 9 項 / 權威排序 7-tier)retention 只有 ~60%,容易令 AI 答出 generic correct 但缺 EKP-specific structure 嘅 reply。Re-read 後唔需主動 summarize(用戶問先講),但要確保下一個 reply 對齊 SITUATION + active phase。

### 10.4 Phase Folder Naming

`W{NN}-{phase-kebab-name}/` 對應 §9 Sprint Awareness 嘅 W{NN} sprint week。
Example:`W01-foundation/`、`W02-multi-format-ingestion/`、`W04-crag-eval-shootout/`。**Rolling JIT**:每 phase 喺 kickoff 先建,**唔可以一次過建 W01–W12**。

### 10.5 Reference

- Workflow source of truth:[`docs/01-planning/PROCESS.md`](./docs/01-planning/PROCESS.md)
- Templates:[`docs/01-planning/_templates/`](./docs/01-planning/_templates/)
- W01 reference example:[`docs/01-planning/W01-foundation/`](./docs/01-planning/W01-foundation/)

---

## 11. Output / Communication Conventions

當你 reply 喺 chat 入面:

- 用**繁體中文**回覆(team primary language)
- **唔好過度 disclaimer**(避免「嗱呢個都係要視乎情況...」呢類 hedging)
- 重要決定要**明確 surface**,唔好 bury 喺長文最後
- Code change 要**說明 what + why**,唔需要重複 code 內容
- 引用 spec 要**標明 section**,e.g. `(per architecture.md §3.5)`
- 遇到 H1–H6 hard constraint trigger,**第一句就要 STOP and explain**

當你寫 code:

- Function / class docstring **必須**(public API)
- Inline comment 解釋 **why**,唔係 **what**
- Error message 要 actionable(「embedding API 5xx」< 「Azure OpenAI embedding endpoint returned 503,suggest retry with exponential backoff」)
- TODO 必須有 owner:`# TODO(chris): wire MSAL middleware after Q11 resolved`

---

## 12. Self-Verification Before Marking Task Done

完成一個 task 之前,**run through 以下 checklist**:

- [ ] 對應 spec 嘅哪個 section?(quote section number)
- [ ] 有冇 violate H1–H6?(若有,即係 task 未完)
- [ ] 有冇 violate §1 Behavioral Baseline?(每行改動 trace 返 user request 嗎?)
- [ ] Test 寫咗未?(若 critical module)
- [ ] Linter / formatter run 過?
- [ ] Commit message follow Conventional Commits?
- [ ] 任何 architectural-adjacent 改動 → ADR 寫咗未?
- [ ] 用咗 Dify reference?在 PR comment 標 source 未?
- [ ] OQ status check:呢個 task 依賴邊條 OQ?status 係咩?
- [ ] Phase checklist 對應 item tick'd?Journal Day-N entry 寫咗未?(per §10 R2)

---

## 13. When in Doubt(default behavior)

| 情況 | Default |
|---|---|
| Spec 同 your idea 衝突 | Spec wins,unless you explicitly raise + get approval |
| Spec 缺乏 detail | Ask user,don't guess |
| 兩種實作方式都 reasonable | 揀**更接近 v4/v5 既有 pattern** 嘅一個 |
| Stakeholder feedback 同 spec 衝突 | STOP — surface the conflict,等 resolution |
| Tier 1 / Tier 2 邊界模糊 | Default to Tier 2(out of scope),ask if uncertain |
| Performance vs simplicity trade-off | Tier 1 階段:simplicity wins(2K chunks 無 perf 壓力) |
| Quality vs delivery time trade-off | 4 metric target 唔可以 compromise;UI polish 可以後補 |

---

## 14. Update This File

**呢份 CLAUDE.md 會 evolve**。當以下情況發生,update 呢份 file:

- 加新 vendor / dependency(approved + ADR 寫咗)
- 改 sprint timeline
- 加 / 改 hard constraint
- New OQ resolved
- New convention adopted by team

**Update 規則**:
- 改動必須喺 commit message 標 `docs(claude-md): <change>`
- 重大 update(改 H1–H6 或 §1 Behavioral Baseline)需要 user explicit approve
- 微調(加 routing entry、update sprint week status)可以自行做

---

## Appendix A: Quick Reference Card(印出嚟 stick 喺 monitor)

```
EKP Tier 1 — Strict Mode
├─ Behavioral baseline: §1 Karpathy (think → simple → surgical → goal)
├─ Spec: docs/architecture.md (frozen v5)
├─ Stack: Azure AI Search + OpenAI + Cohere + Next.js + FastAPI
├─ Tier 1 only: NO GraphRAG, NO multi-agent, NO multi-tenancy
├─ Dify: read-only reference, never copy code
├─ Architectural change: STOP + ask + ADR
├─ New vendor: STOP + ask + ADR
└─ When in doubt: ask, don't guess
```

---

**End of CLAUDE.md**
**Version 1.3 — added §10 Phase Planning Workflow + R1–R5 binding rules; renumbered §11–§14; §2 routing table + §12 self-verification updated**
**Effective: from W1 Day 1**
**Owner: Chris(技術 Lead)**
