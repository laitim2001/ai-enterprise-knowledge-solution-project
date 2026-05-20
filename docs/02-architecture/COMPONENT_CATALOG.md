---
artifact: component-catalog
version: 1.0
status: active
last_updated: 2026-05-01
spec_anchor: docs/architecture.md (v5 frozen 2026-04-27)
process_anchor: docs/01-planning/PROCESS.md (v1.0)
---

# EKP Component Catalog

> **Purpose**:source of truth for **EKP module decomposition**。
>
> 三層 doc 分工:
> - **`docs/architecture.md`** — `WHAT` + `WHY`,full system spec(frozen v5)
> - **`docs/01-planning/PROCESS.md`** — `HOW we work`,phase lifecycle framework
> - **THIS file** — `STRUCTURE`,12 component spine + dependency + phase mapping
>
> 每個 component 有:stable identity(`Cn` ID + name + scope)、citation 返 spec 不重複、tracked dependency / OQ / risk / phase plan / owner / status。
>
> Per-component **design note** 喺 `docs/02-architecture/components/Cn-{kebab}.md`,**rolling JIT**(first heavy-touch phase 寫,implementation 過程 enrich)。

---

## 1. Catalog Index(at-a-glance)

| ID | Component | Spec ref | Tech (locked H2) | First touch | Status (2026-05-01) |
|---|---|---|---|---|---|
| **[C01](#c01--ingestion-pipeline)** | Ingestion Pipeline | `§3.3` `§3.5` | Docling + python-pptx + Azure OpenAI embedding | W2 | 🚫 Pending Q2 sample |
| **[C02](#c02--knowledge-base-manager)** | Knowledge Base Manager | `§3.4` `§4.4 #4-8` | FastAPI + Pydantic + Storage Protocol | W1 D2 | ✅ Implemented (Postgres-backed per ADR-0023; in-memory fallback when `DATABASE_URL` unset) |
| **[C03](#c03--indexing-service)** | Indexing Service | `§3.6` `§3.4` | Azure AI Search Standard S1 + HNSW | W2 D1 | 🟡 Pending tier+region confirm |
| **[C04](#c04--retrieval-engine)** | Retrieval Engine | `§3.1` `§3.2` | Hybrid BM25+vector + Cohere Rerank v3.5 | W2 D5 | 🟢 v2-stable(hybrid + Cohere wired W3 D1-D2;4-way shootout surface ready W4)|
| **[C05](#c05--generation-pipeline)** | Generation Pipeline | `§3.1` `§3.2` | Azure OpenAI GPT-5.5 + custom CRAG (non-LangGraph) | W3 D1 | 🟢 v1-active(Synthesizer + SSE + CRAG L2 W3-W4 D1)|
| **[C06](#c06--eval-framework)** | Eval Framework | `eval-methodology.md` | RAGAs + GPT-5.4-mini judge + custom gate | W1 D1 | 🟢 Validator + scaffold ✅ |
| **[C07](#c07--observability-stack)** | Observability Stack | `§3.2` `§4.3` | Langfuse v2 self-host + structlog | W1 D1 | 🟢 Init ✅ |
| **[C08](#c08--api-gateway)** | API Gateway | `§4.1` `§4.4` `§4.5` | FastAPI + uvicorn + Pydantic v2 | W1 D1 | 🟢 v2-stable(18 stubs + KB CRUD + /query full RAG + /query/stream SSE W3-W4)|
| **[C09](#c09--admin-console-ui)** | Admin Console UI | `§5.1-§5.7` | Next.js 14 + shadcn/ui + Tailwind + TanStack Query | W1 D1 | 🟢 v1-active(6 routes + admin views W2 + wizard W3 D5)|
| **[C10](#c10--chat-interface-ui)** | Chat Interface UI | `§5` | Next.js + native fetch SSE | W3 D2 | 🟢 v1-active(streaming chat + citation card + screenshot modal W3 D4)|
| **[C11](#c11--identity--access)** | Identity & Access (Beta+) | `§9` | MSAL middleware + Entra ID | W7 D1 | ⏳ Beta+ scope |
| **[C12](#c12--devops--infra)** | DevOps & Infra | `§4.3` `§9` | Docker + Azurite + Azure Container Apps + GitHub Actions | W1 D1 | 🟢 Local stack ✅ |

**Legend**:🟢 active progressing | 🟡 partially blocked | 🚫 hard blocked | ⏳ not started (planned) | ⚪ deferred to Tier 2

---

## 2. Dependency Graph

```
                                ┌──────────────────────────────┐
                                │  C12  DevOps & Infra        │ ← foundational
                                │  (Docker / Azurite / Azure  │
                                │   CA / GitHub Actions)      │
                                └────────────┬─────────────────┘
              ┌──────────────────┬──────────┼──────────┬─────────────┐
              ▼                  ▼          ▼          ▼             ▼
       ┌──────────────┐  ┌──────────────┐ ┌──────┐ ┌──────────┐ ┌────────────┐
       │ C03 Indexing │  │ C07 Observ-  │ │ C01  │ │ C12 Blob │ │ C11 Entra  │
       │ Service      │  │ ability      │ │ Ing- │ │ Container│ │ (Beta+)    │
       │ (per-KB AI   │  │ (Langfuse +  │ │ est- │ │ per KB   │ │            │
       │  Search idx) │  │  Postgres)   │ │ ion  │ │          │ │            │
       └──────┬───────┘  └──────┬───────┘ └──┬───┘ └────┬─────┘ └──────┬─────┘
              │                 │            │          │              │
              ▼                 │            ▼          │              │
       ┌──────────────┐         │     [C03 index ◀──────┘              │
       │ C04 Retr-    │         │      schema as            (depends    │
       │ ieval Engine │         │      sink target)          C12 cfg)   │
       │ (Hybrid +    │         │                                       │
       │  Cohere)     │         │                                       │
       └──────┬───────┘         │                                       │
              │                 │                                       │
              ▼                 │                                       │
       ┌──────────────┐         │                                       │
       │ C05 Gener-   │         │                                       │
       │ ation Pipe-  │ ◀────── (C07 traces every stage)                │
       │ line (CRAG)  │         │                                       │
       └──────┬───────┘         │                                       │
              │                 │                                       │
              ▼                 ▼                                       │
       ┌──────────────────────────────┐                                 │
       │ C06 Eval Framework           │                                 │
       │ (consumes C04+C05 output,    │                                 │
       │  reads C07 traces for ctx)   │                                 │
       └──────────────────────────────┘                                 │
                       │                                                │
                       │ ┌──────────────────────────────────────────────┘
                       ▼ ▼
       ┌──────────────────────────────────────────┐
       │ C08 API Gateway (FastAPI)                │ ← wraps C02 + C04 + C05 + C06
       │ - 18 endpoints across 8 routers          │   exposes them as REST
       │ - Pydantic schemas + error mapping       │
       └──────┬─────────────────────────────┬─────┘
              │                             │
              ▼                             ▼
       ┌──────────────┐              ┌──────────────┐
       │ C09 Admin    │              │ C10 Chat     │
       │ Console UI   │              │ Interface UI │
       │ (8 views)    │              │ (streaming)  │
       └──────────────┘              └──────────────┘

Cross-cutting: C12 underpins all; C07 traces all server-side stages.
              C02 (KB Manager) consumed by C03 (provisions per-KB index),
              C12 (per-KB Blob container), and exposed via C08.
```

### Dependency Matrix(machine-readable)

| Component | Hard depends on | Soft depends on / consumes |
|---|---|---|
| **C01** Ingestion | C03 (index schema target), C12 (Azure OpenAI for embedding) | C07 (cost telemetry on embedding calls) |
| **C02** KB Manager | C03 (per-KB index provision), C12 (per-KB Blob container) | C08 (exposes via REST) |
| **C03** Indexing | C12 (Azure AI Search service) | C07 (index ops trace) |
| **C04** Retrieval | C03 (querying index) | C07 (latency trace) |
| **C05** Generation | C04 (consumes retrieval results) | C07 (token / cost trace) |
| **C06** Eval | C04 + C05 (evaluates), C12 (Azure OpenAI judge) | C07 (reads traces for ctx) |
| **C07** Observability | C12 (Postgres for Langfuse) | — |
| **C08** API Gateway | C02 + C04 + C05 + C06 (wires) | C07 (request logging) |
| **C09** Admin UI | C08 (API client) | — |
| **C10** Chat UI | C08 (streaming endpoint) | C09 (shared design tokens) |
| **C11** Identity (Beta+) | C08 (gates middleware), C12 (Entra config) | — |
| **C12** DevOps & Infra | — (foundational) | — |

---

## 3. Phase × Component Heatmap

> Show 12 weeks × 12 components grid。**X = heavy work / new build**;**x = touch / refine**;**✓ = init done**;空白 = not active。

```
                        W1   W2   W3   W4   W5   W6   W7   W8   W9   W10  W11  W12
                        Fnd  Ing  Chat CRAG Opt  Final Beta Beta Beta Beta Roll Roll
                                  Retr Eval      Demo Hard Depl Test Refin 25%  100%
─────────────────────────────────────────────────────────────────────────────────────
C01 Ingestion                X    X    x                                            
C02 KB Manager          ✓    X    x                                                 
C03 Indexing                 X         X    x                                       
C04 Retrieval                x    X    X    x                                       
C05 Generation                    X    X    x                                       
C06 Eval                ✓    X    x    X         X                                  
C07 Observability       ✓    x    X    x    x                                       
C08 API Gateway         ✓    X    X    X    x                                       
C09 Admin UI            ✓    X    X    X                                            
C10 Chat UI                       X    X    x                                       
C11 Identity (Beta+)                                  X    X    x                    
C12 DevOps & Infra      ✓    x         x         x    X    X    x    x    X    X    
─────────────────────────────────────────────────────────────────────────────────────
Phase Gates             prep G1        G2   stretch  POC  Beta deploy testing 25→100%
                              (R@5    (4-metric                                       
                               ≥80%)   ±5pp)
```

**Interpretation tips**:
- **W2 column** 7 components 同步活躍 — 最 intensive 一週
- **C12 (DevOps)** 喺 W1 / W7 / W11-12 三波 heavy(local stack → cloud deploy → rollout)
- **C11 (Identity)** 完全 Beta+ scope,W1-W6 zero touch
- **C06 (Eval)** 喺 W1 + W2 + W4 + W6 四個 critical gate,連續 active

---

## 4. Per-Component Detail

> 每 entry 結構:**Scope** / **Spec ref** / **Tech** / **Depends on** / **Phase plan** / **OQ** / **Risks** / **Owner** / **Status** / **Interface**(input / output / side effects)。
>
> Per-component design note(`components/Cn-{kebab}.md`)留空白,first heavy-touch phase 寫。

---

### C01 — Ingestion Pipeline

| Field | Value |
|---|---|
| **Scope** | 由 raw file(.docx / .pdf / .pptx)→ heading-aware section split → layout-aware chunk → embedded image extract + Blob upload → embedding generation → ChunkRecord ready for C03 indexing |
| **Spec ref** | `architecture.md §3.3`(multi-format ingestion)+ `§3.5`(ChunkRecord schema) |
| **Tech (H2 locked)** | Docling(.docx + .pdf parser)+ python-pptx(.pptx)+ Azure OpenAI text-embedding-3-large(MRL truncate to 1024d) |
| **Depends on** | C03(知 index schema target),C12(Azure OpenAI deployment for embedding) |
| **Phase plan** | W2 D2-D3 F8 Docling .docx parser PoC on 5 sample → W2-W3 multi-format coverage → W4 chunk strategy refinement based on Gate 1 finding |
| **Critical OQ** | Q1(format ratio,resolved 40W/30P/30P)、Q2(sample access — pending)、Q17(heading style coverage)、Q18(image format inventory)、Q19(MRL truncate 1024 vs 3072) |
| **Risks** | R1(Q2 sample delay → W2 start delay)、R4(Docling install pull blocked by corp proxy,workaround = Docling Python lib direct,no Docker image) |
| **Owner** | AI(impl)、Chris(Q2 source delivery) |
| **Status** | 🚫 Hard-blocked on Q2 sample manual delivery → **W20 F4.2 amendment**:`ingest()` accepts optional `kb_config: KbConfig` (defaulting to `None` for back-compat);when `kb_config.extract_embedded_images=False` short-circuits `ScreenshotExtractor.extract` to an empty list (uploader never called for that doc). 3 forward-compat flags (`slide_screenshots` / `dedup_strategy` / `return_images_in_chat`) documented as Wave B+ seams. Backward-compat preserves all existing W2 baseline tests + adds 2 new orchestrator pytests (13/13 pass). |
| **Interface** | **Input**:Path(.docx / .pdf / .pptx)or bytes → **Output**:`list[ChunkRecord]`(per `§3.5` schema)→ **Side effect**:Blob PUT to `ekp-kb-{kb_id}-screenshots/` per image,Azure OpenAI embedding API call per chunk text |

---

### C02 — Knowledge Base Manager

| Field | Value |
|---|---|
| **Scope** | KB CRUD lifecycle、per-KB config(embedding model / chunk strategy / top-K / rerank-K)、multi-KB isolation(每 KB 獨立 index + Blob container + storage backend) |
| **Spec ref** | `architecture.md §3.4`(multi-KB)+ `§4.4 #4-8`(API endpoints) |
| **Tech (H2 locked)** | FastAPI router + Pydantic v2 schemas + `KBStorageBackend` Protocol(`InMemoryKBBackend` ↔ `PostgresKBBackend` via `make_kb_backend(settings)` — Postgres added W17 F1 per ADR-0023;H2 dep `psycopg[binary]`)|
| **Depends on** | C03(provision per-KB index when KB created),C12(per-KB Blob container provision + docker-compose `postgres` `ekp` DB) |
| **Phase plan** | W1 D2 F7 in-memory CRUD ✅ → W17 F1 Postgres-backed persistent path(`make_kb_backend` picks `PostgresKBBackend` when `DATABASE_URL` set,else in-memory — zero call-site change,Protocol contract holds;closes CO18)→ stable / soak |
| **Critical OQ** | Indirect via Q3(C03 dependency) |
| **Risks** | (None direct;inherits C03 risks;W17 `psycopg` local install hit R8 corp proxy → Postgres-path verification deferred per ADR-0017 — code shippable via lazy import + in-memory fallback)|
| **Owner** | AI |
| **Status** | 🟢 W1 in-memory impl committed `c6ca6e3`(2026-05-01)→ W17 F1 `PostgresKBBackend` + `make_kb_backend` factory + tests added(per ADR-0023);Protocol-based,backend swap zero-touch on call sites → **W20 F5.1 amendment**:`KbStatus.archived: bool = False` (Pydantic default backfills existing rows) + `KBStorageBackend.set_archived` Protocol method + InMemory + Postgres impl (idempotent `ALTER TABLE ADD COLUMN IF NOT EXISTS archived BOOLEAN` on every connect — Alembic-free migration consistent with W17 F1) + `KBService.archive(kb_id, archived=True)` flips the flag (soft-archive, reversible). **W20 F4.1 amendment**:`KbConfig` +4 multimodal Tier 1 fields (`extract_embedded_images` / `slide_screenshots` / `dedup_strategy` / `return_images_in_chat`) — active end-to-end + forward-compat seams documented. |
| **Interface** | **Input**:`KbCreate`(kb_id + name + description + KbConfig)/ kb_id path param → **Output**:`KbStatus` / 204 / 404 / 409 → **Side effect**:KB metadata row in Postgres `knowledge_bases` table(or process-local dict when `DATABASE_URL` unset);per-KB Azure AI Search index + Blob container create/drop handled via C03 / C12 |

---

### C03 — Indexing Service

| Field | Value |
|---|---|
| **Scope** | Azure AI Search index lifecycle(create / populate / version / retire)、index naming convention `ekp-kb-{kb_id}-v{version}`、HNSW vectorSearch profile 配置、semantic config |
| **Spec ref** | `architecture.md §3.6`(index schema JSON)+ `§3.4`(per-KB index naming) |
| **Tech (H2 locked)** | Azure AI Search Standard S1 + HNSW(m=4 efConstruction=400 efSearch=500 cosine)+ semantic config `ekp-semantic-config` |
| **Depends on** | C12(Azure AI Search service must exist + provisioned) |
| **Phase plan** | W2 D1 F9 first index `ekp-kb-drive-v1` 創建 → W2-W3 populate via C01 → W4 potentially v2 if chunk strategy refined → W5+ stable |
| **Critical OQ** | Q3(resource availability — Resolved partial:endpoint+key delivered W1 D2 → root `.env`;tier+region confirm pending W2 D1) |
| **Risks** | R3(Ricoh corp DNS intercept on MCR — Azure AI Search SDK calls 可能受影響,W2 D1 verify) |
| **Owner** | AI(SDK script)、Chris(Q3 tier+region confirmation) |
| **Status** | ✅ Implemented(`ekp-kb-drive-v1` 1024d HNSW W2 D1;**CH-001 2026-05-12** added multi-KB lifecycle:`IndexPopulator.create_index_for_kb(kb_id)` PUT-create from `backend/indexing/schema.json` + `delete_index(kb_id)` DELETE fail-soft-on-404 + `delete_doc(kb_id, doc_id)` filter-then-batch-delete + `upload(records, kb_id=None)` BC sig ext for per-KB index routing;closes ADR-0018 Phase 3 upload-side) → **W20 F5.2 amendment**:`HybridSearcher.list_chunks` select clause additively extended with `embedded_images_json` field so the new `GET /kb/{kb_id}/images` aggregation can walk chunks → images without re-fetching parsed docs (W17 F4.1 callers unaffected — Pydantic `ChunkSummary` silently drops the new field). |
| **Interface** | **Input**:`KbConfig` from C02 → **Output**:Azure AI Search index ready for indexing,index handle for C04 retrieval → **Side effect**:Azure AI Search service API calls(create / delete index + per-doc chunk batch ops) |

---

### C04 — Retrieval Engine

| Field | Value |
|---|---|
| **Scope** | Hybrid retrieval(BM25 + vector via RRF fusion)、reranking(W3 Cohere baseline → W4 4-way shootout: Cohere / Voyage / ZeroEntropy / Azure built-in)、top-K configuration |
| **Spec ref** | `architecture.md §3.1`(pipeline flow)+ `§3.2`(stack table) |
| **Tech (H2 locked)** | Azure AI Search hybrid search(built-in RRF)+ Cohere Rerank v3.5(W3 baseline,W4 shootout 後可換) |
| **Depends on** | C03(query against index),C07(latency / RRF score telemetry) |
| **Phase plan** | W2 D5 hybrid baseline(RRF only,no rerank)for Gate 1(R@5 ≥ 80%)→ W3 Cohere wired → W4 reranker shootout(Q21 resolution)→ W5 stable |
| **Critical OQ** | Q21(reranker pick after W4 shootout)、Q5(Cohere procurement Path A direct API vs Path B Azure Marketplace)、Q8(4-metric replacement if not target) |
| **Risks** | R2(mocked retrieval test 同 prod divergence)、W4 shootout eval design 需在 C06 配合 |
| **Owner** | AI |
| **Status** | ⏳ Not started(pending C03 W2 D1) |
| **Interface** | **Input**:query string + kb_id + top-K → **Output**:`list[ChunkRecord]` ranked → **Side effect**:Azure AI Search query API + Cohere Rerank API calls,Langfuse trace |

---

### C05 — Generation Pipeline

| Field | Value |
|---|---|
| **Scope** | Query reformulation(CRAG L2 confidence-based)→ context packing → LLM synthesis → citation extraction → optional re-attempt loop |
| **Spec ref** | `architecture.md §3.1`(pipeline flow + CRAG diagram)+ `§3.2`(stack)+ `§13.11`(custom CRAG vs LangGraph deferred decision) |
| **Tech (H2 locked)** | Azure OpenAI GPT-5.5(synthesis)+ custom CRAG implementation(non-LangGraph per ADR 13.11)+ optional Pro variant for eval-judge |
| **Depends on** | C04(retrieval results in),C07(token / cost / loop iteration trace) |
| **Phase plan** | W3 D1 basic synthesis + citation skeleton → W3 streaming response wire → W4 CRAG L2 loop(confidence threshold + 1-reformulation max for Gate 2)→ W5 stretch L3 routing if Gate 2 全 pass |
| **Critical OQ** | Q4(deployment names — Resolved full W1 D2)、Q20(LLM pick alternative — open) |
| **Risks** | GPT-5.5 cost over-run(per-query cost monitoring critical W4)、hallucination control without ground-truth refusal mechanism |
| **Owner** | AI |
| **Status** | ⏳ Not started(W3 D1 first touch) → **W20 F3b amendment**(frontend-only wire — no backend change):existing `EvalReport.crag_triggered: bool` + `crag_iterations: int` fields(W4 CRAG L2 baseline)now surfaced via NEW `<CragStrip>` frontend component(`<Sparkles>` icon + "CRAG triggered — N iteration(s)" chip in chat header);wiring stays in place for Wave B+ L3 enable;`crag_reasoning` field deliberately NOT added(Wave B+ candidate per Karpathy §1.2 simplicity — rendering "CRAG triggered — N iterations" without reasoning tooltip until usage demands more). |
| **Interface** | **Input**:query + retrieved chunks(from C04) → **Output**:streamed response with citation markers → **Side effect**:Azure OpenAI API streaming call,Langfuse trace per CRAG iteration |

---

### C06 — Eval Framework

| Field | Value |
|---|---|
| **Scope** | Eval set v0/v1(ground truth)、RAGAs 4 metrics(faithfulness / answer-relevancy / context-precision / context-recall)、LLM judge(GPT-5.4-mini)、phase gate decision logic(Gate 1 W2,Gate 2 W4)、reranker shootout harness W4 |
| **Spec ref** | `eval-methodology.md`(全)+ `architecture.md §6.3`(W2 + W4 explicit gates)+ `§8` R2 risk |
| **Tech (H2 locked)** | RAGAs(eval lib)+ Azure OpenAI GPT-5.4-mini judge + custom gate Python logic + YAML eval set |
| **Depends on** | C04 + C05(evaluates their output),C12(Azure OpenAI judge endpoint) |
| **Phase plan** | W1 D1 F5 schema validator + F11 ground truth scaffold ✅ → W2 D5 Gate 1 prep(R@5 baseline)→ W4 Gate 2 + reranker shootout → W6 final eval → Beta+ continuous eval |
| **Critical OQ** | Q13(SME allocation — Resolved)、Q14(specific labeler = Chris Lai self-assigned,Resolved full W1 D2)、Q8(4-metric replacement)、Q6(real query collection W3+) |
| **Risks** | R2(LLM judge inconsistency,fallback Chris verify)、Q14 SME bandwidth(Chris 自身 multi-role) |
| **Owner** | AI(framework)、Chris + SME(ground truth labeling) |
| **Status** | 🟢 W1 D1 validator ✅,30 條 synthetic eval set scaffold;ground truth fill 仍 spread W1-W4 |
| **Interface** | **Input**:eval-set-v{n}.yaml + C04/C05 actual output → **Output**:metric scores + gate decision pass/fail → **Side effect**:Azure OpenAI judge API call per query,reports/ output |

---

### C07 — Observability Stack

| Field | Value |
|---|---|
| **Scope** | Langfuse trace(per-query session,linked to retrieval / generation / CRAG iterations)、structlog JSON logging(stdout + file)、cost telemetry(per-API-call tracking)、latency monitoring(P50/P95/P99 per stage)、token usage |
| **Spec ref** | `architecture.md §3.2`(Langfuse in stack)+ `§4.3`(local stack topology) |
| **Tech (H2 locked)** | Langfuse v2 self-host(Docker-compose Postgres-backed)+ structlog Python lib |
| **Depends on** | C12(Postgres for Langfuse persistence) |
| **Phase plan** | W1 D1 init stub ✅ → W3 per-pipeline-stage tracing(retrieval, generation, CRAG iter)→ W4-W6 cost / latency analysis dashboards in Langfuse → Beta+ alerting |
| **Critical OQ** | — |
| **Risks** | Langfuse self-host scaling at Beta+ load(may need cluster mode)、trace volume cost at Beta+ |
| **Owner** | AI |
| **Status** | 🟢 W1 D1 Langfuse v2 healthy at `/api/public/health`,structlog JSON config init → **W20 F2.1 amendment**:`/health` extracted from inline `server.py` into NEW `backend/api/routes/health.py` + extended payload from `{status: "ok"}` to `{status, components: {azure_search, azure_openai, cohere, langfuse, postgres}: {status, latency_ms, detail}}` (5 ComponentStatus values:ok / not_configured / degraded / error);config-state-only check Wave A scope per Karpathy §1.2 simplicity;real-I/O pings deferred Wave B+ (`latency_ms` schema field preserved). 7/7 pytest pass on the new route. |
| **Interface** | **Input**:any Python module emit `structlog.get_logger().info(...)` + Langfuse `@observe` decorator → **Output**:Langfuse UI trace + stdout JSON log → **Side effect**:Langfuse Postgres write per trace |

---

### C08 — API Gateway

| Field | Value |
|---|---|
| **Scope** | FastAPI app + 18 RESTful endpoints across 8 routers + Pydantic v2 schemas + error mapping(HTTPException 4xx/5xx)+ Beta+ rate limit + Beta+ auth gating |
| **Spec ref** | `architecture.md §4.1`(stack)+ `§4.4`(18 endpoints table)+ `§4.5`(schema definitions) |
| **Tech (H2 locked)** | FastAPI 0.115+ + uvicorn 0.32+ + Pydantic v2.9+ + Pydantic Settings 2.6+ |
| **Depends on** | C02 + C04 + C05 + C06(wires them as endpoints),C07(request logging) |
| **Phase plan** | W1 D1 F2 18-endpoint scaffold(501 stubs) ✅ → W2-W4 wire each Cn as it lands(KB ✅,documents,query,eval,debug)→ W7+ MSAL middleware + rate limit |
| **Critical OQ** | — |
| **Risks** | H6 hard constraint:`api/routes/query.py` 必須 test coverage ≥ 80% |
| **Owner** | AI |
| **Status** | ✅ Implemented(18 endpoints;`/query`+`/chat` SSE + `/auth/*` hybrid auth + W17 F2 httpOnly cookie+CSRF+`/auth/refresh` per ADR-0022 + admin auth;stub closure cascade DONE — `debug/trace/{id}` + KB doc listing W16 F5 + `eval/run`+`eval/shootout` real RAGAs W17 F3;**CH-001 2026-05-12** wired the 3 document routes — POST `/kb/{kb_id}/documents` (multipart → tempfile → orchestrator → IndexPopulator.upload(kb_id=)) + DELETE `/kb/{kb_id}/documents/{doc_id}` (IndexPopulator.delete_doc → 204/404/502) + POST `.../{doc_id}/reindex` (Decision A=(ii) replace-in-place: doc-exists 404 + doc_id-match 422 + atomic delete-then-ingest + 502 partial_failure) + POST `/kb` auto-provisions per-KB Azure index + DELETE `/kb` drops it (close CO_F3a + ADR-0018 Phase 3 upload-side; 24 backend tests in `tests/api/test_documents_route.py`);**CH-002 2026-05-12** error-envelope + ingest fixes — `documents.py` `_api_error` detail key `"actionable_hint"`→`"hint"` (the key `error_handlers.http_exception_handler` actually reads — was silently dropping route hints so `actionable_hint` came back null on `document.duplicate` / `validation.unsupported_format` / `document.not_found` / `reindex.doc_id_mismatch`; F5) + `error_handlers.validation_exception_handler` 422 `message` now names the failing field path + constraint via `_redacted_loc_path` (str/int `loc` elements only — never the raw `input` value, H5; F8) + `_run_ingest_pipeline` writes the tempfile under `mkdtemp()/<original-basename>` so the parser's `doc_title = source.stem` is the real stem, not `tmpXXXX` (traversal-safe; F2);+10 backend test cases → **W20 Wave A amendment**:**+10 NEW endpoints**(6 `/conversations` CRUD per ADR-0031 Option B + `POST /kb/{id}/archive` per ADR-0025 + `GET /kb/{id}/images` per ADR-0025 + `POST /chunking-preview` per ADR-0025 + `GET /health` extracted/extended per ADR-0030 absorbed)— total endpoint count now 28. **`_refuse_if_archived` helper** guards upload + reindex paths (403 `kb.archived`);read paths intentionally allow archived KBs so chat keeps citing. **59/59 backend pytests pass** through Wave A (archive 5 + images 4 + chunking-preview 5 + documents 32 + orchestrator 13). → **W24-wave-c1 amendment**(per ADR-0026 Option B Settings 6-tab fully editable):**+17 NEW endpoints across 4 NEW routers**(`/admin/connections/*` × 5 endpoints per F2 + `/admin/identity/*` × 5 endpoints + `/admin/api-keys/*` × 3 endpoints + `/admin/usage-stats` × 1 endpoint + `/admin/audit-log` × 1 endpoint per F5 backend hook)— **total endpoint count now 45**;**3 NEW Postgres tables**(`admin_provider_configs` + `admin_identity_config` per-sub-resource row pattern + `audit_log` SERIAL PK write-mostly)+ **3 Tier 2 boundary guards** at PATCH layer(F3 `multi_disabled` + `distributed_disabled` + active `power_user` rejected 422);**Security hygiene**:secret values NEVER returned in any GET — only `secret_kv_ref` name + `secret_masked_preview`(`***last4`)+ client-supplied `authority_url` 喺 PATCH 被 strip + re-derived server-side(prevents redirect injection)。**805 passed + 11 skipped + 0 failed** through W24 backend phase。 → **W24b-wave-c2 F6 amendment**(per ADR-0026 Wave C2 promote):`GET /admin/audit-log` promoted from W24-c1 read-only last-10 to **filter + cursor pagination** — additive `action_type`(AuditAction Literal)+ `since`(datetime,UTC-normalized)+ `cursor`(ge=1)query params + NEW `AuditLogPage` wrapper response `{entries, next_cursor}`(over-fetch `limit+1` to derive `next_cursor`);`AuditLogBackend.list_recent` Protocol + InMemory(in-pass filter loop)+ Postgres(parameterized `WHERE` predicates)impls gain keyword-only filter params;endpoint count unchanged at **45**(F6 additive params,no new route)。**816 passed + 11 skipped + 0 failed**(W24-c1 805 → +11 net:7 NEW endpoint + 4 NEW storage filter tests)。 |
| **Interface** | **Input**:HTTP requests → **Output**:JSON responses per Pydantic schema → **Side effect**:downstream Cn calls,structlog request log,Langfuse trace |

---

### C09 — Admin Console UI

| Field | Value |
|---|---|
| **Scope** | 8 admin views(`/admin` overview,`/admin/kb` KB list,`/admin/kb/[id]` KB detail / config / docs,`/admin/kb/[id]/upload` doc upload,`/admin/kb/[id]/chunks/[doc_id]` chunk inspector,`/eval` eval dashboard,`/debug/[traceId]` Langfuse trace viewer,`/admin/settings`) |
| **Spec ref** | `architecture.md §5.1-§5.7`(UI specifications + 8 views breakdown) |
| **Tech (H2 locked)** | Next.js 14 App Router + TypeScript strict + shadcn/ui + Tailwind 3.4 + TanStack Query(non-streaming data fetch) |
| **Depends on** | C08(API client target via `lib/api-client.ts`) |
| **Phase plan** | W1 D1 F3 6 routes scaffold ✅ → W2-W3 wire KB list / detail / doc upload → W3 chunk inspector → W4 eval dashboard + debug trace viewer → W5 settings + polish |
| **Critical OQ** | Q10(visual identity — Open,using neutral tokens default until W4 designer pass) |
| **Risks** | H3 hard constraint:Dify reference 只可學 layout,絕不可 copy code 或 brand color |
| **Owner** | AI |
| **Status** | 🟢 W1 D1 6 routes scaffold + custom design tokens(non-Dify)+ pnpm install + lint + type-check 全 clean → W12-W15 UI Tier 1 expansion 9 views(per ADR-0015)→ **W18(per ADR-0024)**:all authenticated views re-parented under a single `<AppShell>`(persistent top bar + collapsible left sidebar + main content);URLs flattened — `/admin/*` → `/kb/*`,`/debug/[traceId]` → `/traces/[traceId]`,`/admin` → a real `/dashboard` overview(KB summary / recent-query CTA / latest-eval CTA / backend health / quick actions);`/settings` added(profile + theme + sign-out);V7 marketing Landing removed(`/` → redirect `/login`);login/register success → `/dashboard`;`<GlobalSearch>` Cmd/Ctrl+K quick-jump palette(Pages + KB names + "Ask in chat"). `architecture.md v6 §5` is inline-tagged with the amendment(§5.0 Application Shell + §5.3 Dashboard + §5.7 Traces + §5.9 Landing-removed + the flattened routing — doc version held);this catalog row mirrors it. `[oklch(...)]`=0 milestone preserved through the restructure。**CH-002 2026-05-12** caught 3 views up to the W16-F5 + CH-001 backend reality — `/eval` Eval Console:dead 501-stub error branch removed + empty-state copy fixed("eval-set-v0 is a W1 placeholder")+ `max_main_queries` cap input added(it was already wired to `evalApi.run`);KB-detail Chunks tab:`<BackendStubNote>` placeholder → real `ChunkSummary` table(doc picker honouring `?doc=`, GET `/kb/{id}/documents/{doc_id}/chunks`);KB-detail Settings→Identity:name/description now editable + Save → PATCH `/kb/{id}`(partial via `kbApi.patchMetadata`). Vitest 4 files/13 tests → 6 files/18 tests(+`eval-page`+`kb-detail`;`tests/unit/setup.ts` += ResizeObserver polyfill) → **W20 Wave A amendment**(per ADR-0025/0028/0031 + ADR-0030/0032 absorbed scope):**F1** `<AppShell>` topbar polish + `<NotificationsMenu>` + Workspace switcher Tier 2 disabled + Sidebar Tools sub-section + Labs hidden + shared `<DisabledAffordance>` component(W19 F5 spec) · **F2** `/dashboard` real cards(4-stat strip + 5 cards w/ per-component health dots) · **F3b** `/chat` advanced surfaces — server-side Conversation History(localStorage-collapsed pane) + 3 citation placement modes(inline/footnote/sidebar) + image gallery + CitationPill hover-popover + feedback bar w/ tag dropdown + CRAG strip(Wave B+ wired-but-dormant) · **F4** `/kb` list grid+table view toggle + status filter + `/kb/new` 5-step wizard(Source / Parsing / Chunking / Multimodal Tier 1 + Tier 2 affordances / Review) · **F5** `/kb/[id]` 7-tab `-Access` refactor(Documents + Chunks + Images NEW + Chunking Lab NEW + Pipeline + Retrieval + Settings;Access tab disabled affordance Tier 1.5 — Wave C1 activates) + Settings Danger zone Archive action · **F6** `/kb/[id]/upload` single-step → 3-step re-ingestion wizard skeleton(read-only Multimodal display per KB config + link to Settings) · **F7** `/login` strict-fidelity refactor(SSO primary + Divider + email secondary + Forgot password inline disabled affordance + Auth modes mono block per `references/design-mockups/ekp-page-auth.jsx`)+ `/register` polish(field reorder + Terms checkbox + Hint copy + Step 3 KB selector via shared `<DisabledAffordance>`). **Rule-of-3 wizard primitive promotion trigger NOW hit**(4th wizard usage — F4 + W13 Register + W18 F5 Pipeline + W20 F6)— extract to shared `frontend/components/ui/stepper.tsx` is **Wave B+ candidate**. `[oklch(...)]`=0 milestone preserved through Wave A. Vitest 6 files/21 tests preserved(F8.4 scaffold batch deferred 8 NEW test files). → **W22 amendment**(per CLAUDE.md §5.7 H7 promoted Hard Constraint 2026-05-17 + W21 partial-close H7-enforcement audit trigger):**strict-fidelity rebuild of 15 Tier 1 routes**(F1 AppShell cross-cutting / F2 auth pair / F3 dashboard / F4 chat / F5a+F5b KB list+wizard / F6 cluster 3 sub-pages / F7 observability cluster 3 sub-pages / F8.1 settings baseline)100% mockup-faithful per `references/design-mockups/ekp-page-*.jsx`;CSS-first pivot baseline(mockup `styles.css` 1073 lines verbatim adopted as `styles-mockup.css`;mockup CSS classes drive visual layer + shadcn primitives where Radix a11y benefits + Tailwind utility for one-off layout);**`[oklch(...)]`=0 milestone preserved through W22 rebuild**;**5 cumulative empirical-finding anti-patterns**(D1/D6/D7/D8/D9)logged to `feedback_design_fidelity.md` memory — pre-active-flip 5-step recursive audit pattern formalized;**Vitest 9 passed + 3 skipped(12 files,26 pass + 6 skipped vs pre-W22 14 pass)**— 4 complex test files DEFERRED W23+ via `describe.skip` per F8.7 closeout discipline;**Playwright pixel baseline recaptured** for all 15 rebuilt routes(F8.8 — `PW_CHANNEL=chrome pnpm test:e2e:update-snapshots`)。Wave C boundaries preserved:`/users` Wave C1 RBAC + `/settings` 6-tab fully-editable Wave C2 per ADR-0026/0027。 → **W24-wave-c1 F5 amendment**(per ADR-0026 Option B):**`/settings` 6-tab `PageSettingsRich` rebuild** — 6 tabs(Profile / Appearance / Connections / Identity & Auth / API Keys & Quotas / Account)with `?tab=` deep link via `useSearchParams` + `<Suspense>` boundary + W22 F8.1 ProfileTab/AppearanceTab/AccountTab logic preserved inline per Karpathy §1.3 surgical;**3 NEW primitives**:`<ApiKeyInput>`(reveal/hide/copy/rotate + masked-preview-as-value)+ `<ServiceCard>`(collapsible expand-on-click with TestStatus badge variants)+ `<DeploymentsTable>`(TPM/RPM cap + alert%);**4 NEW settings/* components data-bound to `adminApi`** — `<SettingsConnections>`(9 providers × 5 categories with lazy-fetch + Test connection + Rotate secret)+ `<SettingsIdentity>`(5 cards 1:1 onto F3 sub-resources + Power User Tier 2 disabled affordance)+ `<SettingsApiKeys>`(4-stat strip 24h + per-deployment quota bars + inline alert threshold edit + permanent IncomingKeysDisabled affordance)+ `<SettingsAuditLog>`(last-10 rows read endpoint promoted F4→F5);**`apiClient.admin.*`** 235 LOC with full Pydantic-mirror TypeScript types for 17 admin endpoints。**`[oklch(...)]`=0 milestone preserved through 9 NEW frontend files**(CSS-first per DESIGN_SYSTEM.md §2 13-primitive index);Vitest 9/9 settings-6tab tests pass + Playwright +2 NEW app-shell-path tests + 1 NEW visual baseline first-capture user-deferred per W20 F8.5 + W23 F2.3 precedent。**Wave C2 promote items**:F6.3 form validation react-hook-form+zod + F6.4 optimistic UI + F6.5 ErrorBoundary wrapper + Identity inline edit + Connections deployment cap edit + Audit log filter/pagination + real-MSAL feature flag concurrent ship per user 岔口 2。 → **W24b-wave-c2 amendment**(per ADR-0026 Wave C2 promote — Settings 6-tab Hub read-mostly → inline-editable depth):**F1** react-hook-form + zod + @hookform/resolvers 3 NEW deps(Plan B (a) `pnpm add` clean,zero R8 — npm-registry non-binary per W17 F6 precedent)+ NEW `lib/schemas/admin/` zod schema collection;**F2** 3 zod schema files(`identity.ts` + `api_keys.ts` + `connections.ts`)mirror backend Pydantic + ApiKeys alert-threshold `OutgoingQuotaRowItem` RHF+zod 硬化;**F3** `<SettingsConnections>` ProviderRow inline edit form + local-state optimistic `useMutation`(`onMutate`/`onError` rollback);**F4** NEW `ErrorBoundary` class(`components/error/error-boundary.tsx`)+ `<TabErrorState>` fallback + 6-tab `TabBoundary` wrap;**F5** `<SettingsIdentity>` read-only display → 4 editable form cards(Tenant / App registration / MSAL / Sign-in policy)各 useForm + zodResolver + per-card `useMutation` PATCH;role card stays display(individual mapping CRUD Wave C+);**F6** `<SettingsAuditLog>` 加 action_type filter `.select` + since date picker + cursor「Load more」pagination(local-state extend);**`[oklch(...)]`=0 milestone preserved** through Wave C2;Vitest settings-area 41/41 deterministic batch;Playwright `app-shell-path` + `visual-baseline` spec 改動 landed,`PW_CHANNEL=chrome` execution + `settings-identity.png` PNG first-capture user-deferred per W24-c1 precedent。 |
| **Interface** | **Input**:user browser interaction → **Output**:rendered React component tree → **Side effect**:fetch to C08 API |

---

### C10 — Chat Interface UI

| Field | Value |
|---|---|
| **Scope** | Streaming chat interface(end-user view)、citation render(inline + sidebar)、optional query history(Beta+ defer to `/history` route) |
| **Spec ref** | `architecture.md §5`(chat-related views,first use case = Drive Project end-users) |
| **Tech (H2 locked)** | Next.js + Vercel AI SDK `useChat` hook(SSE streaming)+ shadcn/ui components(shared with C09 design tokens) |
| **Depends on** | C08(streaming `/query` endpoint),C09(shared design tokens / common components) |
| **Phase plan** | W3 D2 chat UI scaffold + connect to C05 streaming → W3-W4 citation render(inline 句末 [^1] + sidebar source list with screenshot preview)→ W5 polish |
| **Critical OQ** | — |
| **Risks** | SSE streaming on Ricoh corp network(可能 buffer 唔流暢)、citation render edge cases(citation 落 hallucinated source) |
| **Owner** | AI |
| **Status** | 🟢 W3 D2 chat UI + SSE streaming + citation cards + screenshot modal → W13 routing restructure(`/` → `/chat`)+ theme provider / dark mode → W15 token cleanup → **W18(per ADR-0024)**:the chat view now renders inside `<AppShell>`(its own `<main>`+`min-h-screen` became a `<div>`+`h-full`;the focus-mode toggle replaces the full-bleed chrome-less surface;in-page header slimmed — the "EKP" wordmark is in the shell top bar now);reads `?q=` on mount(the global-search "Ask in chat" deep-link pre-fills the input + focuses it). Route `/chat` unchanged;SSE/streaming logic untouched → **W20 F3b amendment**(per ADR-0031 Option B server-side Conversation History — promotes C10 §7 Tier 2 → Tier 1):left **Conversation History pane**(collapsible via `localStorage['ekp-chat-history-collapsed']` — deviation from "AppShell focus-mode")with `useQuery(['conversations', 'list'])` 30s staleTime + lazy `POST /conversations` on first user send + double-click inline rename + delete `<Dialog>` confirmation;**SSE persistence shim** — user prompt + assistant turn POSTed with `.catch(() => {})` best-effort so a transient persistence blip doesn't block the active-session render;**3 citation placement modes**(inline / footnote / sidebar) toggle in `<ChatHeader>` fieldset + persisted to `localStorage['ekp-citation-mode']`;**conversation-wide image gallery** below stream(aggregates `citations.embedded_images[0]` across all messages);**`<CitationPill>`** vanilla popover w/ 100ms hover-grace + keyboard a11y(no shadcn Popover primitive — Karpathy §1.2 add-on-2nd-use-site);**`<FeedbackBar>`** thumbs-up one-shot + thumbs-down inline disclosure w/ `<select>` tag dropdown(inaccurate / incomplete / off-topic / other)+ textarea — tag prefixed into existing W8 `POST /feedback` `comment` field as `[tag] text…`(no backend schema change);**`<CragStrip>`** wired-but-dormant in Tier 1 SSE path(`crag_triggered` + `crag_iterations` rendered;`crag_reasoning` Wave B+ candidate). → **W22 F4 amendment**(per CLAUDE.md §5.7 H7 strict-fidelity rebuild 2026-05-18):`/chat` complete presentation rebuild per mockup `ekp-page-chat.jsx:72 PageChat` actual decomposition(`ConversationHistoryPanel` + `ChatHeader` + `ChatThread` + `MessageRow` + `SourcesStrip` + `SourceDocCard` + `CitationPanel` + `PanelSourceCard` + `ScreenshotModal` + `ChatComposer`)— all inline per mockup single-file pattern;**D1 anti-pattern surfaced**:initial F4 inherited W20-era「Citations seg-toggle」in ChatHeader → mockup actually has CRAG switch + Show images switch + Focus Eye + Sources BookOpen → fixed `fee7836` post user-eye audit;**Obsolete W20 components deleted**(per Karpathy §1.3 surgical):`conversation-history.tsx` / `inline-image-card.tsx` / `image-gallery.tsx` / `citation-pill.tsx` / `feedback-bar.tsx` / `crag-strip.tsx`;**citationMode state machine preserved at PageChat level**(localStorage reader preserved + writer removed — default `inline`;future ADR can re-introduce explicit toggle UI per ADR-0031 Citation modes spec);SSE wiring + Conversation History persistence + `/feedback` tag-prefix integration **all preserved unchanged**(Wave A backend per CC6)。 |
| **Interface** | **Input**:user typed query → **Output**:streamed response render with citation markers → **Side effect**:SSE long-poll to C08 |

---

### C11 — Identity & Access(Beta+)

| Field | Value |
|---|---|
| **Scope** | Microsoft Entra ID auth(SSO)、role-based access(Admin / End-user,Beta+ 加 Power-user 如需)、token validation middleware on C08 |
| **Spec ref** | `architecture.md §9`(Beta plan)+ `CLAUDE.md §5.2 H2` H4 Tier boundary(stays in Tier 1 Beta+,not Tier 2) |
| **Tech (H2 locked)** | MSAL middleware(FastAPI-MSAL or custom)+ Entra ID app registration + role claims in token |
| **Depends on** | C08(gates middleware),C12(Entra tenant config + app registration) |
| **Phase plan** | W7 D1-D3 MSAL middleware + role schema → W7 D4-D5 protect API + UI auth flow → W8 admin role separation → W9-W12 soak |
| **Critical OQ** | Q11(Entra tenant + app registration — Open,W6 末 resolve before W7 start) |
| **Risks** | Corp Entra tenant access timeline(IT request lead time)、role assignment governance |
| **Owner** | AI(impl)、Chris + IT(tenant + app registration) |
| **Status** | ⏳ Not started(Beta+ scope,W7 first touch) → **W24-wave-c1 F3 amendment**(per ADR-0026 Option B + ADR-0014/0022 interplay):**5 NEW `/admin/identity/*` endpoints**(consolidated `GET` + 5 `PATCH` per tenant + app_registration + msal + roles + policy)+ NEW `admin_identity_config` Postgres table(per-sub-resource row pattern: `sub_resource TEXT PK + config JSONB + updated_at + updated_by NULL`,5 rows seeded idempotently);**Server-side `authority_url` derivation** from `tenant_id × cloud_instance` per 3-cloud map(Azure Public / Government / China 21Vianet)— client-supplied `authority_url` 喺 PATCH 被 strip + re-derived(prevents redirect injection);**3 Tier 2 boundary guards** rejected via 422 per CLAUDE.md H4:`multi_disabled` audience(app_registration)+ `distributed_disabled` token cache strategy(msal)+ active `power_user` ekp_role rejected unless `is_tier2_disabled=True`(roles list-replace semantic per ADR-0027 Option B fallback);**Power User row** ships permanent disabled affordance with `tier2_reason`("post-W12 governance per ADR-0024 future evolution");26 NEW F3 pytest pass。**`<SettingsIdentity>`** frontend tab(F5.6)data-bound to `adminApi.getIdentity()` with read-mostly inputs(`readOnly` / `disabled` per Wave C1 scope — Wave C2 promotes inline edit when ADR-0027 Graph SDK lands)。 → **W24b-wave-c2 F5 amendment**:`<SettingsIdentity>` 由 read-mostly 提升至 **inline-editable** — 4 editable form cards(Tenant / App registration / MSAL / Sign-in policy)各 react-hook-form + `zodResolver` + per-card `useMutation` PATCH(`patchTenant` / `patchAppRegistration` / `patchMsal` / `patchPolicy`)+ `onSuccess reset(saved)` re-baseline + `onError` keep-edits(form-based,非 onMutate-rollback — rollback 會棄用戶輸入);**3 Tier 2 boundary guards preserved** — `multi_disabled` / `distributed_disabled` `<option disabled>` + Power User row read-only display(individual mapping CRUD = mockup「⋯」menu deferred Wave C+);server-derived `authority_url` 保持 read-only watch-controlled。無新 endpoint(Wave C1 嘅 5 PATCH endpoints 已 shipped);client_secret rotation `ApiKeyInput rotateDisabled`「Wave C2 — rotation requires Entra Graph SDK」。 |
| **Interface** | **Input**:HTTP Authorization header(Bearer token) → **Output**:authenticated user context attached to request → **Side effect**:token validation API call(MSAL)、403 on unauthorized |

---

### C12 — DevOps & Infra

| Field | Value |
|---|---|
| **Scope** | Local dev stack(docker-compose Postgres + Langfuse + Azurite)、Azurite emulator fallback(npm-based when Docker MCR blocked)、Azure Container Apps cloud deploy(W7+)、CI/CD GitHub Actions(W7+)、IaC scripts |
| **Spec ref** | `architecture.md §4.3`(local stack)+ `§9`(Beta+ deploy) |
| **Tech (H2 locked)** | Docker + docker-compose + Azurite(npm + Docker dual)+ Azure Container Apps + GitHub Actions + Bicep(IaC TBD) |
| **Depends on** | (None — foundational) |
| **Phase plan** | W1 D1 local stack 3/3 services up ✅(Postgres + Langfuse Docker + Azurite npm fallback)→ W7 cloud Bicep + Azure CA deploy → W8 CI/CD GitHub Actions → W9-W12 staged rollout 25→50→100% |
| **Critical OQ** | — |
| **Risks** | R3 Ricoh corp DNS intercept on MCR(workaround:npm Azurite + docker.io direct path);**known follow-up**:IT whitelist or VPN long-term;**新撞**:Ricoh corp proxy 對 PyPI 大檔(>500KB wheel)connection-broken,影響任何 pip install,W1 D2 confirmed pattern |
| **Owner** | AI(scripts)、Chris(Azure tenant + corp IT escalation) |
| **Status** | 🟢 Local stack ✅;corp proxy mitigation pending P1(VPN/hotspot ops window)or P2(IT whitelist long-term) → **W24-wave-c1 F1 amendment**:**Azure Key Vault SDK install via mobile-hotspot Plan B (c)**(per ADR-0017 occurrence #8 — `azure-keyvault-secrets>=4.8.0` + `azure-identity>=1.18.0` installed via personal mobile hotspot 2026-05-19;`pyproject.toml` updated;15/15 `test_key_vault.py` pass);**3rd realized Plan B (c)** after Langfuse SDK 2026-05-16 + Playwright 2026-05-13 — confirms mobile-hotspot pattern is the standing fallback for PyPI binary-wheel installs that the corp proxy throttles deterministically inside bad R8 windows。NEW `KEY_VAULT_URL` env var in `backend/storage/settings.py`(empty default → `EnvVarProvider` `.env` fallback;set → `AzureKeyVaultProvider` async SDK via `azure.keyvault.secrets.aio.SecretClient` + `azure.identity.aio.DefaultAzureCredential`)— **lazy-import per ADR-0023 pattern**;unset `KEY_VAULT_URL` never touches `azure-keyvault-secrets`,so local dev / CI / R8-blocked re-installs keep working via stdlib `EnvVarProvider`。 |
| **Interface** | **Input**:docker-compose.yml + .env + Bicep templates → **Output**:running services(local + cloud) → **Side effect**:Docker image pull,Azure resource provisioning |

---

## 5. Cross-Cutting Conventions(binding)

呢套規則喺 catalog 寫低,所有 future doc / commit / artifact 必跟:

| ID | Rule | Enforcement |
|---|---|---|
| **CC-1** | 每個 phase plan deliverable(Fn)**必須 tag** affected component(s)`Cn`,e.g. `F7 → C2 (KB Manager)` | Reviewer 喺 phase plan 審 |
| **CC-2** | 每個 ADR **必須 tag** affected component(s) | ADR template 加 `Affects:` field |
| **CC-3** | `decision-form.md` 21 OQ **必須 tag** affected component(s),作為 OQ resolution 加速 routing | Decision-form 加 column |
| **CC-4** | `architecture.md §8` Risk Register entries 入 catalog 之 component-tagged living version `docs/01-planning/RISK_REGISTER.md`(`§8` frozen 不動)| Per-component status field link |
| **CC-5** ✱ | 每 component design note(`components/Cn-{kebab}.md`)係 **design-first with v0-draft marker** —— W1 D3-D5 batch 寫齊 11 個 v0-draft note(C11 Beta+ defer 到 W6 末 / W7 kickoff),作為 implementation 嘅 reference contract。Implementation 過程中發現 design 偏差 → update note + bump status `v0-draft → v1-active → v2-stable`。每 note `status` field 必標 | Per-component status field track v-stage |
| **CC-5 status semantics** | `v0-draft` = pre-implementation,may evolve;`v1-active` = implementation in progress,design 已驗 part;`v2-stable` = implementation 完成,design final | Note frontmatter `status` |
| **CC-6** | Catalog 嘅 Tech 列必對齊 `architecture.md §3.2` 嘅 H2 vendor lock。任何 catalog tech 改動 = H2 violation = STOP + ADR | CLAUDE.md §5.2 enforce |
| **CC-7** | Catalog 自身 versioned via frontmatter `version` field;structural change(加 / 刪 component,改 dependency)需 ADR | This file `version: 1.0` |

---

## 6. Tier 2 Future Slots(architectural readiness)

Tier 2 features per `architecture.md §11`,plug 入 existing component slots:

> **Component-ID note**(housekeeping 2026-05-13):Tier 1 嘅 13 components 係 **C01–C13**,當中 **C13 = Email Verification Service**(Azure Communication Services,per architecture.md v6 §3.7 + ADR-0014 — authoritative)。早期版本呢個表把 hypothetical "Workflow Engine" 標做 "C13",同 Tier 1 C13 撞 ID — 已更正:任何 Tier 2 新 component 由 **C14** 起順排(下表 Training Pipeline = C14、Workflow Engine = C15)。

| Tier 2 Feature | Plug into | How |
|---|---|---|
| **GraphRAG / Knowledge Graph** | C04 Retrieval(alternative engine)+ C01 Ingestion(extra graph extraction step) | Retrieval 加 graph traversal mode,ingestion 加 entity / relation extraction 後寫 separate graph store |
| **L4+ Multi-Agent Orchestration** | C05 Generation(orchestration layer 取代 single CRAG loop) | Custom CRAG → multi-agent system(LangGraph 或 custom),C05 internal change,interface 不變 |
| **Custom LLM Fine-Tuning** | C05 Generation(replace base model)+ new **C14 Training Pipeline** | 加 new component C14(training data prep + fine-tune job)→ output model deployed,C05 swap deployment name |
| **Workflow / Plugin Builder** | C09 Admin UI(new view) + new **C15 Workflow Engine** | 加 new component C15(workflow runtime)+ C09 加 builder UI。**注:唔係 C13** — C13 喺 Tier 1 已係 Email Verification Service |
| **Multi-Tenancy** | C02 KB Manager(tenant_id column)+ C03 Indexing(tenant prefix in index name)+ C11 Identity(tenant claim) | 三個 component 各自加 tenant dimension,C08 加 tenant context middleware |
| **Multi-Modal Retrieval(B 類純圖搜)** | C04 Retrieval(image embedding mode)+ C01 Ingestion(image embedding) | 加 image embedding model 入 C01,C04 加 image-only query path |
| **Multi-Language(JP / ZH)** | C01 Ingestion(per-language analyzer)+ C04 Retrieval(per-language semantic config) | Language detection in C01,per-language index variants in C03 |
| **Auto-Sync from External Source** | C01 Ingestion(scheduler trigger)+ C12 DevOps(scheduler infra) | 加 scheduled job runner(Azure Functions 或 Container Apps Jobs)→ trigger C01 ingestion |

**架構 readiness invariant**:Tier 2 features **不應該** 需要 Tier 1 component 嘅 interface change(只係 internal evolve)。任何 Tier 2 feature plan 若需要 Tier 1 interface 改動 → STOP + ADR + re-evaluate decomposition。

---

## 7. Catalog Maintenance

- **Update trigger**:component status change(✅ / 🟡 / 🚫 / ⏳ flip)、phase plan 寫 Fn 落地觸發 status update、OQ resolution affecting component、ADR landing
- **Update authority**:catalog frontmatter `version` 1.0 起,minor change(status / OQ / risk update)= patch 1.0 → 1.0(no version bump);structural change(加/刪 component / 改 dependency / 改 spec_anchor)= minor bump 1.0 → 1.1 + ADR
- **Update commit type**:`docs(catalog): <change>` 或 `docs(planning): catalog <change>`
- **Reference protocol**:future doc reference 必標 `(per COMPONENT_CATALOG.md C{NN})`;avoid drift via single-source rule

---

## Appendix A — Quick Reference Card(印 stick on monitor)

```
EKP Component Catalog — 12 Modules
  │
  ├─ Foundational
  │   └─ C12 DevOps & Infra
  │
  ├─ Data layer (pipeline order)
  │   ├─ C01 Ingestion ──→ C03 Indexing ──→ C04 Retrieval ──→ C05 Generation
  │   └─ C02 KB Manager (cross-cuts data layer)
  │
  ├─ Cross-cutting
  │   ├─ C06 Eval Framework
  │   └─ C07 Observability Stack
  │
  ├─ API surface
  │   └─ C08 API Gateway (wraps C02 + C04 + C05 + C06)
  │
  ├─ UI surface
  │   ├─ C09 Admin Console UI
  │   └─ C10 Chat Interface UI
  │
  └─ Beta+ scope
      └─ C11 Identity & Access

Phase × Component:see Section 3 heatmap
Conventions:see Section 5 CC-1 … CC-7
```

---

**End of COMPONENT_CATALOG.md v1.0**
**Effective**:from W1 D3(2026-05-01)
**Owner**:Chris(技術 Lead)
