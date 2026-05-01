---
component: C05
name: Generation Pipeline
catalog_ref: ../COMPONENT_CATALOG.md#c05--generation-pipeline
spec_refs: [architecture.md §3.1, architecture.md §3.2, architecture.md §13.11 (custom CRAG vs LangGraph ADR)]
status: v0-draft
last_updated: 2026-05-01
---

# C05 — Generation Pipeline Design Note

> **Status**:`v0-draft`(W3 D1 first-touch:basic synthesis + citation skeleton;W4 D1 CRAG L2 loop for Gate 2;W5 stretch L3 routing if Gate 2 全 pass)
>
> **Owner**:AI

---

## 1. Internal Architecture

```
backend/generation/                  ← W3 D1 create
├── __init__.py
├── azure_openai_client.py           ← async LLM client(streaming + non-streaming)
├── prompts/
│   ├── synthesis.txt                ← citation-required synthesis system prompt
│   ├── confidence_judge.txt         ← CRAG confidence scoring prompt
│   └── reformulate.txt              ← CRAG query reformulation prompt
├── synthesis.py                     ← orchestrator:context pack → LLM → cite extract
├── crag_loop.py                     ← CRAG L2 agentic loop(W4 D1)
├── citation/
│   ├── __init__.py
│   ├── extractor.py                 ← parse `[chunk_id]` markers from LLM response
│   └── validator.py                 ← assert cited chunk_ids 屬 retrieved set
└── (W5 stretch) routing.py          ← L3 query type routing
```

### Generation flow

```
Input: query + retrieved chunks (from C04 top-5)
    │
    ▼
┌──────────────────────────────────────────────────────────────┐
│ 1. Context pack                                               │
│    Build LLM prompt:                                          │
│      [SYSTEM: synthesis.txt — citation required]              │
│      [CONTEXT chunks formatted as:                           │
│         <chunk id="kb-drive_doc-M042_chunk-0007">             │
│         {chunk_text}                                          │
│         </chunk>]                                             │
│      [USER: {query}]                                          │
└─────────────────────────────┬────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│ 2. LLM streaming synthesis                                    │
│    Azure OpenAI gpt-5.5 streaming API                        │
│    → SSE token chunks                                         │
│    → response includes inline `[chunk_id]` citations         │
└─────────────────────────────┬────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│ 3. Citation extract + validate                               │
│    Post-stream parse `[chunk_id]` markers                    │
│    Validate each cited id ∈ retrieved.chunk_ids             │
│    Convert to citation objects with source_url + screenshot │
│    (If validation fail → flag hallucinated citation)        │
└─────────────────────────────┬────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│ 4. (W4) CRAG confidence check + reformulate loop             │
│    Judge LLM scores response confidence(0-1)                 │
│    If confidence < threshold(0.70 default):                 │
│      Reformulate query → C04 retrieve again → goto step 1   │
│      Max 1 reformulation per spec(R5 cost cap)              │
│    If still low → emit refusal "信心不足,請聯絡 Admin"       │
└──────────────────────────────────────────────────────────────┘
Output: streamed response + citations + trace_id
```

---

## 2. Key Interfaces

### Inputs
- `query: str`
- `chunks: list[ChunkRecord]`(top-K from C04)
- `kb_id: str`(for trace context)
- `streaming: bool = True`(C10 chat default;`/eval` non-streaming)

### Outputs(streaming)
- SSE stream of:
  - `{"type": "token", "text": "..."}` — incremental token
  - `{"type": "citation", "marker": "[1]", "chunk_id": "...", "source_url": "...", "screenshot_url": "..." | null}` — cited chunk emitted as encountered
  - `{"type": "done", "trace_id": "..."}` — final flush

### Outputs(non-streaming)
- `GenerationResult`:
  - `response_text: str`
  - `citations: list[Citation]`
  - `confidence: float`(W4+)
  - `crag_iterations: int`(W4+,0 if no reformulation)
  - `trace_id: str`

### Side effects
- Azure OpenAI synthesis API call(streaming)
- (W4+)Azure OpenAI judge API call(confidence scoring)
- (W4+)C04 re-invocation(reformulated query)
- Langfuse @observe trace per CRAG iteration

---

## 3. Critical Design Decisions

| Decision | Rationale |
|---|---|
| **Custom CRAG implementation**(non LangGraph,per ADR 13.11) | LangGraph adds complexity for Tier 1 single-loop CRAG;custom Python control flow更 transparent;LangGraph re-evaluate Tier 2 multi-agent |
| **Citation-required prompt**(per spec §8.2 R4 mitigation) | Force LLM 喺 response 入面 quote `[chunk_id]`;extractor + validator catches hallucinated cites |
| **Streaming via SSE**(non WebSocket) | Compatible Vercel AI SDK(C10);simpler infra |
| **Citation extract post-stream**(non per-token) | Streaming token rate ~10-50/sec;post-stream parse 100ms post-completion vs per-token regex (perf concerns) |
| **Citation validation against retrieved set** | Prevent LLM hallucination injecting fake chunk_ids;flag mismatched as `unverified` to UX |
| **CRAG confidence threshold 0.70**(default,tunable per env) | Per spec §3.1;balance over-cautious(refuse too often)vs under-cautious(let bad answer through) |
| **CRAG max 1 reformulation**(per spec §3.1)| Cost cap(2× LLM call max);W5 stretch L3 routing if needed |
| **Refusal message standard**:"信心不足,請聯絡 Admin"(per UX guideline) | Consistent UX;encourage user to escalate rather than discard;tracks via C07 for product learning |
| **Judge model = gpt-5.4-mini**(non gpt-5.5)| Cost saving 10×;judge accuracy on confidence scoring high enough |
| **Synthesis model = gpt-5.5**(per spec §3.2 H2 lock) | Best quality for primary user-facing answer |
| **No model swap mid-stream**(W1-W6) | Keep simple;Tier 2 fine-tune model swap可考慮 routing.py |

---

## 4. Edge Cases & Error Handling

| Edge case | Handling |
|---|---|
| **No retrieved chunks**(C04 returns empty) | Refusal:"未搵到相關資料。請 rephrase 或檢查 KB";don't invoke LLM(cost saving)|
| **LLM timeout**(> 60s) | Cancel stream;emit error event;Langfuse trace `aborted`;C10 chat shows "響應超時,請重試" |
| **LLM rate limit**(R5 Azure quota) | tenacity retry exponential backoff;若 final fail → 503 to caller;Langfuse alert |
| **Hallucinated citation**(`[chunk_id]` 唔屬 retrieved set) | Validator flags;render in UI as "⚠ unverified citation";record in eval set as quality signal |
| **Refusal triggered too often**(quality issue) | Track refusal rate as eval metric(C06);if > 20% → confidence threshold tune required |
| **CRAG infinite loop**(reformulation 都 low confidence)| Cap at 1 reformulation per spec;若 still low → forced refusal(per spec) |
| **Streaming connection drop mid-response** | Server-side cleanup of in-flight resources;Langfuse trace marks `aborted` partial response |
| **LLM emits response without citation marker**(忘 cite) | Validator catches;retry once with explicit instruction;若 still no cite → emit response with warning "未檢測到 citation,謹慎使用" |
| **Cost runaway**(10K-token response) | Set max_tokens cap(e.g. 2000);若 hit cap → truncate + warning |

---

## 5. Performance Characteristics

| Operation | Latency target | Notes |
|---|---|---|
| LLM synthesis TTFT | < 2s P95 | Azure OpenAI streaming first token |
| LLM full response | ~10-20s typical;< 30s P95 | Depends on response length |
| CRAG judge call | ~1-2s P95 | gpt-5.4-mini fast |
| CRAG reformulation + re-retrieve + re-synthesize | +5-10s if triggered | Roughly 2× base latency |
| Citation extract post-process | < 100ms | Pure Python regex + dict lookup |
| Citation validation | < 50ms | Set membership check |
| **End-to-end /query**(no CRAG iter) | < 12s P95 | C04 retrieve(~1.5s)+ C05 synthesis(~10s) |
| **End-to-end /query**(with 1 CRAG iter) | < 25s P95 | + judge + reformulate + re-synthesize |
| **Cost per query**(synthesis only) | ~$0.005-0.02 | gpt-5.5 input + output tokens |
| **Cost per query**(with CRAG iter) | ~$0.01-0.04 | + judge + 2nd synthesis |

---

## 6. Test Strategy

| Test type | Scope | Status |
|---|---|---|
| **Synthesis happy path**(real LLM, deterministic seed) | Known query + chunks → assert response 非空 + citation extracted | W3 D1 |
| **Citation validation regression** | Inject fake `[chunk_id]` → assert flagged | W3 D2 |
| **Refusal trigger test** | Empty chunks → assert refusal,no LLM call | W3 D2 |
| **CRAG loop unit test**(mock judge) | Force low confidence → assert reformulate triggered | W4 D2 |
| **CRAG max iter cap** | Force 2 low confidence → assert stop after 1 iter + refusal | W4 D2 |
| **End-to-end via /query endpoint**(mock LLM in test, real LLM in smoke) | TestClient streaming | W3-W4 |
| **Hallucination regression**(R4) | 5 table-heavy query in eval set → assert citation accuracy | W4 末 |
| **Coverage target** | ≥ 80% per CLAUDE.md H6(`api/routes/query.py` critical) | W4 |

---

## 7. Future Evolution / Tier 2 Hooks

| Tier 2 feature | C05 evolution |
|---|---|
| **L4+ multi-agent orchestration** | Replace single CRAG loop with multi-agent system(retrieval agent, reflection agent, synthesis agent);LangGraph再 evaluate;C05 internal change,interface 不變 |
| **Custom LLM fine-tuning** | Replace gpt-5.5 with fine-tuned deployment;C14 Training Pipeline produces deployment, C05 swap deployment_name in env |
| **Multi-language**(JP / ZH) | Per-language synthesis prompt;language detection in query preprocess;language-aware refusal message |
| **Tool calling / function execution** | LLM emits tool call markers;C05 dispatches to MCP-style tool registry(prepare for Tier 2) |
| **Adaptive routing**(simple Q → cheap model,complex → expensive) | `routing.py` classifier;route to gpt-5.4-nano vs gpt-5.5 based on query complexity;cost optimization |
| **Provenance chain**(beyond chunk_id citation) | Chain of evidence:cited chunks → entities → relations → original doc paragraphs;Tier 2 GraphRAG enabler |
| **Conversational context**(Beta+ multi-turn)| Pass conversation history to synthesis prompt;limit context window |

---

## 8. Open Items / TODO

- [ ] **W3 D1 azure_openai_client.py** async streaming wrapper
- [ ] **W3 D1 synthesis.py** + synthesis.txt prompt
- [ ] **W3 D1 citation extractor + validator**
- [ ] **W3 D2 SSE wire to C08 /query streaming endpoint**(consume by C10)
- [ ] **W4 D1 CRAG L2 loop**(judge + reformulate)
- [ ] **W4 D5 5 table-heavy eval queries** for R4 regression
- [ ] **Q20 LLM pick alternative** open(default gpt-5.5,W3 evaluate)
- [ ] **W5 stretch L3 routing decision**(triggered if Gate 2 全 pass)
- [ ] **Cost per query telemetry** to C07 + C09 dashboard(W4)

---

**Cross-refs**:
- Catalog: [`../COMPONENT_CATALOG.md#c05--generation-pipeline`](../COMPONENT_CATALOG.md#c05--generation-pipeline)
- Spec: `architecture.md §3.1`(pipeline + CRAG diagram)+ `§3.2`(stack)+ `§13.11`(custom CRAG ADR)
- Risks: R4(LLM hallucination on tables — citation prompt mitigation),R5(Azure quota)
- Cross-component: depends on C04 retrieved chunks;produces stream consumed by C08 → C10;traced via C07;evaluated by C06
