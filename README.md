# Enterprise Knowledge Platform (EKP)

> Self-built enterprise knowledge platform with multi-format document ingestion,
> hybrid retrieval, and L2 agentic RAG. First use case: **Drive Project** — Ricoh
> internal user manuals.

📐 **[互動架構總覽(Artifact)](https://claude.ai/code/artifact/b9c0b7f6-23d3-44bf-b0b5-e4b696e3d375)** — 給工程師 / 新開發者的最佳起點:RAG pipeline、stack 選型理由、13 components、資料流、部署、目前狀態一頁睇晒。

| | |
|---|---|
| **Status** | Tier 1 foundation — 功能近乎完成,pre-launch hardening;原 12-week → 實際 rolling JIT(最近進展:統一整合層 W100-101 + CH-023 UI 語言統一,2026-07-09) |
| **Phase** | W1–W18 base(POC → Beta → Rollout → UI sprint cycle → app shell IA)+ W19+ rolling JIT;最新狀況見 [`docs/01-planning/BACKLOG.md`](./docs/01-planning/BACKLOG.md);timeline 見 [`docs/12-ai-assistant/01-prompts/01-session-start.md`](./docs/12-ai-assistant/01-prompts/01-session-start.md) §10 |
| **Spec Version** | v6(frozen;v5 → v5.1 → v6 amendment per ADR-0014/0015/0024) |
| **Tech Lead** | Chris |
| **Strict Mode** | ON — see [`CLAUDE.md`](./CLAUDE.md) |

---

## What this is

EKP 係 RAPO 自建嘅 enterprise knowledge platform foundation。Tier 1 用 Drive Project(100 份 Ricoh user manuals)做 first use case,驗證:

- Multi-format document ingestion(Word + PDF + PPT)
- Layout-aware chunking(取代 Dify-style character chunking)
- Hybrid retrieval(BM25 + dense + Cohere rerank)
- L2 agentic RAG(CRAG self-correction loop)
- Multi-Knowledge-Base 架構(Tier 1 即支援多 KB,first KB = Drive)
- 自託 screenshot pipeline(local: Azurite,cloud: Azure Blob)

**唔係 Tier 1 嘅 scope**(Tier 2 roadmap):GraphRAG、multi-agent、multi-tenancy、workflow builder、multimodal retrieval。

---

## Quickstart

### Prerequisites

- Docker Desktop(Azurite + Langfuse local emulator)
- Python 3.12+(backend)
- Node.js 20+(frontend)
- Azure subscription with:
  - Azure AI Search Standard S1
  - Azure OpenAI(`text-embedding-3-large` + `gpt-5.5` + `gpt-5.4-mini` deployment)
  - Azure Blob Storage account
- Cohere API access(direct or via Azure Marketplace)
- Access to Ricoh internal document source(SharePoint / Drive / share folder — see Q2 in [`docs/decision-form.md`](./docs/decision-form.md))

### Setup(5 分鐘)

```bash
# 1. Clone repo
git clone <repo-url> ekp && cd ekp

# 2. Setup Dify reference(read-only)
mkdir -p references && cd references
git clone --depth 1 https://github.com/langgenius/dify.git
cd ..

# 3. Configure environment
cp .env.example .env
# Edit .env 填入 Azure / Cohere credentials —— 詳見 docs/setup.md

# 4. Start local services(Azurite + Langfuse + Postgres)
docker compose -f infrastructure/docker-compose.yml up -d

# 5. Backend
cd backend
uv sync                                  # or `pip install -e .`
uv run alembic upgrade head              # if applicable
uv run uvicorn api.server:app --reload   # http://localhost:8000

# 6. Frontend(another terminal)
cd frontend
pnpm install
pnpm dev                                 # http://localhost:3001
```

**完整 setup guide**(troubleshooting、Azure resource provisioning checklist、credential management):
→ **[`docs/setup.md`](./docs/setup.md)**

---

## Repository Structure

```
ekp/
├── README.md                  ← 你而家睇緊
├── CLAUDE.md                  ← Claude Code standing instructions(strict mode)
├── docs/
│   ├── architecture.md        ← Spec v6(frozen,single source of truth)
│   ├── setup.md               ← Local dev + Azure resource setup
│   ├── api-contract.md        ← API 契約(~58 endpoints implemented across routers)
│   ├── eval-methodology.md    ← (W1 ready)RAGAs + 4 metric framework
│   ├── eval-set-v0.yaml       ← (W1 ready)30 條 ground truth eval set
│   ├── decision-form.md       ← 22 條 Open Question stakeholder review(17 Resolved / 5 Open)
│   └── adr/                   ← (W2 ready)Architecture Decision Records
├── references/
│   ├── design-mockups/        ← EKP 自有 high-fidelity prototype(前端 canonical visual spec)
│   ├── dify/                  ← Third-party read-only reference(gitignored,license-isolated)
│   └── REFERENCE_USAGE.md     ← Reference usage policy
├── backend/                   ← FastAPI + Pydantic + Python 3.12
│   ├── ingestion/
│   ├── retrieval/
│   ├── generation/
│   ├── pipeline/
│   ├── kb_management/
│   ├── integration/           ← C17 source connectors(SharePoint 等,upstream of ingestion)
│   ├── eval/
│   ├── observability/
│   ├── storage/
│   └── api/
├── frontend/                  ← Next.js 14 + shadcn/ui + Tailwind
│   ├── app/                   ← App Router
│   ├── components/
│   ├── lib/
│   └── styles/
├── infrastructure/
│   ├── docker-compose.yml     ← Local dev stack
│   ├── azurite.config.json
│   └── containerapp.bicep     ← Azure deployment
├── eval_data/
│   ├── eval_set_v1.yaml
│   └── ground_truth/
└── tests/
```

---

## Tech Stack(at a glance)

| Layer | Tool |
|---|---|
| Document parser | Docling(.docx + .pdf)+ python-pptx |
| Image storage | Azure Blob(Local: Azurite emulator) |
| Embedding | Azure OpenAI `text-embedding-3-large`(1024d MRL) |
| Vector + BM25 | Azure AI Search Standard S1(multi-KB) |
| Reranker | Cohere Rerank v4.0-pro(W6 production lock per ADR-0012;v3.5 W3 baseline → v4.0-pro same-vendor upgrade;W4 shootout outcome Voyage / ZeroEntropy DROPPED Tier 1) |
| LLM(synthesis) | Azure OpenAI `gpt-5.5` |
| LLM(judge) | Azure OpenAI `gpt-5.4-mini` / `gpt-5.5-pro` |
| Agentic | L2 CRAG;W5 stretch L3 routing |
| Eval | RAGAs + custom LLM-as-judge |
| Observability | Langfuse(self-host) |
| Backend | FastAPI + uvicorn |
| Frontend | Next.js 14 + shadcn/ui + Tailwind + Vercel AI SDK |
| Persistent store | Postgres 16(psycopg 3;KB metadata + users/sessions;in-memory fallback) |
| Auth | Microsoft Entra ID(SSO)+ self-service email register(Beta+) |
| Deployment | Azure Container Apps(backend)+ Azure Static Web Apps(frontend Beta+) |
| Reference | Dify(read-only,clone to `references/dify/`) |

完整選型 rationale 見 [`docs/architecture.md` §3.2 + §13](./docs/architecture.md)。

---

## Working with Claude Code

呢個 project 用 **Claude Code 作為主要 dev agent**。Claude Code 嘅 standing instructions 喺 [`CLAUDE.md`](./CLAUDE.md),包括:

- Strict Mode hard constraints(H1–H7)
- Document routing logic(咩情況讀邊份 doc)
- Coding / git / testing conventions
- Sprint awareness(W1–W18 base + W19+ rolling JIT)
- Self-verification checklist

**Onboarding new dev**:讀完 README.md → 讀 CLAUDE.md → 讀 [`docs/architecture.md`](./docs/architecture.md) → 讀 [`docs/setup.md`](./docs/setup.md) 跑 setup → 開工。

---

## Sprint Timeline

> **註**:以下為**原 12-week plan**。實際 trajectory 已 rolling JIT 到 W101+(image-recall 弧 / per-KB config / enterprise RBAC / 統一整合層 / CH-023)。最新狀況見 [`docs/01-planning/BACKLOG.md`](./docs/01-planning/BACKLOG.md);逐 phase timeline 見 [`session-start.md §10`](./docs/12-ai-assistant/01-prompts/01-session-start.md)。

| Phase | Week | Milestone |
|---|---|---|
| POC | W1 | Foundation + Eval set v0 |
| POC | W2 | **Gate 1** — Hybrid retrieval Recall@5 ≥ 80% |
| POC | W3 | Cohere rerank + GPT-5.5 + Citation + Streaming |
| POC | W4 | **Gate 2** — CRAG + RAGAs + Reranker shootout(4 metric within 5pp) |
| POC | W5 | Optimization + W5 stretch L3 routing(conditional) |
| POC | W6 | Final eval + Demo + Beta plan |
| Beta | W7 | Microsoft Entra ID + Hardening sprint 1 |
| Beta | W8 | Beta deploy + Hardening sprint 2 |
| Beta | W9 | 50 internal users testing |
| Beta | W10 | Beta refinement |
| Rollout | W11 | Staged 25% → 50% |
| Rollout | W12 | Full launch(250–500 users) |

Decision Gates 詳情見 [`docs/architecture.md` §6.3](./docs/architecture.md)。

---

## Success Metrics

### Technical(POC W6 gate)

| Metric | Target |
|---|---|
| Retrieval Recall@5 | ≥ 90% |
| Answer Faithfulness | ≥ 95% |
| Answer Correctness(human) | ≥ 80% |
| Image Association Accuracy | ≥ 85% |
| p95 Latency | ≤ 30s |

### Business(Beta+ measurement)

| Metric | Target |
|---|---|
| Time-to-answer reduction | ≥ 50% |
| Shadow AI displacement | ≥ 40% |
| User satisfaction(thumbs ratio) | ≥ 70% positive |

詳情見 [`docs/architecture.md` §1.6 + §1.7](./docs/architecture.md)。

---

## Status & Open Questions

**目前 status**:Tier 1 spec **v6** frozen;功能近乎完成,pre-launch hardening 階段。RAG core、統一 web shell、self-service + SSO auth、RBAC 均已落地並過 gate。W1 critical OQ 早已 resolve(17/22 Resolved,其餘 non-blocking)。

**目前主要 pending(多 blocked on 外部)**:production launch(卡 Track A IT credential)、整合層 live 驗證(卡真 tenant + `Sites.Selected`)、prose human ground-truth 標註(卡 SME)。完整 backlog 見 [`docs/01-planning/BACKLOG.md`](./docs/01-planning/BACKLOG.md);22 條 OQ 見 [`docs/decision-form.md`](./docs/decision-form.md)。

---

## Strict Mode 提醒(critical)

呢個 project 採用 **Strict Mode**:

- 架構決定一旦 lock(spec v6)就唔可以單方面改
- 加 vendor / 改 component → 必須先 ask + 寫 ADR
- Dify 係 **read-only reference**,絕對唔可以 copy code
- Tier 2 features(GraphRAG、multi-agent etc)唔可以「順手做埋」入 Tier 1

詳細 rules 同 escalation flow 見 [`CLAUDE.md` §4 Hard Constraints](./CLAUDE.md)。

---

## License & Internal Use

Internal Ricoh Asia Pacific Operations(RAPO)project。
External distribution / open-sourcing 需 RAPO management approval。

`references/dify/` 係 third-party open source(Dify modified Apache 2.0),
**唔係 EKP codebase 一部分**,使用見 [`references/REFERENCE_USAGE.md`](./references/REFERENCE_USAGE.md)。

---

## Contact

- **Tech Lead**:Chris
- **Decision Owner**(architecture):Chris
- **Decision Owner**(scope / business):Stakeholder(see decision-form.md)

---

**Last updated**:2026-07-10
**README version**:1.2
