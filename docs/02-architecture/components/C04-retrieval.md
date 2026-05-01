---
component: C04
name: Retrieval Engine
catalog_ref: ../COMPONENT_CATALOG.md#c04--retrieval-engine
spec_refs: [architecture.md §3.1, architecture.md §3.2, eval-methodology.md §7]
status: v0-draft
last_updated: 2026-05-01
---

# C04 — Retrieval Engine Design Note

> **Status**:`v0-draft`(W2 D5 first-touch:hybrid baseline for Gate 1 R@5 ≥ 80%;W3 Cohere wired;W4 4-way reranker shootout)
>
> **Owner**:AI

---

## 1. Internal Architecture

```
backend/retrieval/                ← W2 D5 create
├── __init__.py
├── hybrid.py                     ← Hybrid search via Azure AI Search built-in RRF
├── reranker/
│   ├── __init__.py
│   ├── base.py                   ← Reranker Protocol
│   ├── cohere.py                 ← Cohere Rerank v3.5(W3 baseline)
│   ├── voyage.py                 ← Voyage rerank(W4 shootout)
│   ├── zeroentropy.py            ← ZeroEntropy(W4 shootout)
│   ├── azure_semantic.py         ← Azure built-in semantic ranker(R6 fallback)
│   └── factory.py                ← config-flag based selection
├── retrieval_engine.py           ← Public API:retrieve(query, kb_id, top_k) → list[ChunkRecord]
└── (optional) query_preprocess.py  ← (W3+) query expansion / detection
```

### Retrieval flow

```
Query string + kb_id + top_k(typical 50)
    │
    ▼
┌──────────────────────────────────────────────────────────────┐
│ 1. Hybrid search (Azure AI Search built-in)                  │
│    POST /indexes/ekp-kb-{kb_id}-v{n}/docs/search             │
│    {                                                           │
│      "search": "...query...",                                 │
│      "vectorQueries": [{"vector": [embed(query)],            │
│                          "k": 50,                              │
│                          "fields": "embedding"}],             │
│      "queryType": "semantic",   ← uses semantic config        │
│      "top": 50                                                 │
│    }                                                           │
│    → Built-in RRF fusion (BM25 + vector)                     │
│    → Returns top-50 chunks with @search.score                │
└─────────────────────────────┬────────────────────────────────┘
                              │
                              ▼ (filter: enabled=true via search filter clause)
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│ 2. Rerank (W3+)                                              │
│    reranker.rerank(query, chunks, top_k=5) → re-ordered      │
│    Cohere baseline:                                          │
│      POST cohere /v1/rerank                                  │
│      → return top-5 with rerank_score                       │
└─────────────────────────────┬────────────────────────────────┘
                              │
                              ▼
Output: list[ChunkRecord] (top-5,passed to C05 generation)
```

---

## 2. Key Interfaces

### Inputs
- `query: str`(user natural language)
- `kb_id: str`(routes to per-KB index)
- `top_k: int`(default from `KbConfig.default_top_k`,typical 50 for retrieval,5 for rerank)
- (W3+) `KbConfig.default_rerank_k`

### Outputs
- `list[ChunkRecord]`(top-K reranked chunks per `§3.5` schema)
- Each chunk includes score(`@search.score` for hybrid,`rerank_score` for reranker)
- Trace info(retrieved chunk count, RRF latency, rerank latency)→ Langfuse via C07

### Side effects
- Azure AI Search query API call(C03 dependency for index existence)
- Cohere Rerank API call(W3+)
- Azure OpenAI embedding API call for query embedding(per query)
- Langfuse @observe trace per stage

### Reranker Protocol

```python
class Reranker(Protocol):
    async def rerank(
        self,
        query: str,
        candidates: list[ChunkRecord],
        top_k: int,
    ) -> list[ChunkRecord]: ...  # ordered by rerank_score desc
```

---

## 3. Critical Design Decisions

| Decision | Rationale |
|---|---|
| **Azure AI Search built-in RRF**(non custom RRF impl) | Built-in 已 optimized;reduce custom code;BM25 + vector fusion 一次 API call |
| **Embedding query at retrieval time**(non pre-computed)| Query embedding cost ~50ms,small;allows query expansion / preprocessing without re-index |
| **Hybrid retrieval `top=50`,rerank `top=5`** | Common pattern;50 candidates give reranker enough variety;5 final fits LLM context budget(~1500 token × 5 = 7500 token < GPT-5.5 limit) |
| **Reranker behind Protocol abstraction**(W4 shootout swap) | Plug-and-play 4 rerankers;config flag切 without code change(R6 hot fallback to Azure semantic) |
| **Cohere Rerank v3.5 baseline**(spec §3.2 H2) | Industry standard,well-documented,low-latency |
| **W4 reranker shootout**:Cohere / Voyage / ZeroEntropy / Azure semantic | Per `eval-methodology.md §7` + spec §6.3 Gate 2;data-driven Q21 resolution |
| **Filter `enabled=true`**(via Azure Search filter clause) | Honor admin-toggled disabled chunks(per `§3.5` enabled field)without re-index |
| **No query rewriting / expansion W2-W3**(reserve W4 if Gate 1 R@5 fails)| YAGNI;hybrid baseline 通常 sufficient for clear queries;reformulation 留 CRAG(C05) |
| **Per-KB reranker config**(KbConfig.reranker)| Future per-KB tuning;W1-W4 全 KB 用 default Cohere |

---

## 4. Edge Cases & Error Handling

| Edge case | Handling |
|---|---|
| **Empty query / whitespace** | Return empty list with reason;C05 should not invoke retrieval for empty |
| **No results found**(query 很 niche) | Return empty list (NOT error);C05 handles refusal logic |
| **kb_id not found**(C02 dropped KB)| Propagate as `KBNotFoundError` from C03;C08 maps 404 |
| **Index empty**(no docs ingested yet)| Return empty list with `total_count: 0`;UX 顯示 "no docs" |
| **Reranker timeout**(R6 Cohere outage)| tenacity retry;若 final fail → fallback Azure built-in semantic(config flag);log warning to Langfuse |
| **Reranker rate limit**(R6) | Fall back to no-rerank(return hybrid top-K directly);trace metric `rerank_skipped: true` |
| **Embedding API timeout**(query embedding) | tenacity retry;若 fail → propagate to C05 → user-friendly error |
| **Azure AI Search 503** | tenacity retry;若 persistent → 503 to caller |
| **Filter clause syntax invalid** | Catch in test;runtime should not happen if KbConfig validated |
| **Chunks missing `enabled` field**(legacy)| Default `enabled=true` in retrieval mapping |

---

## 5. Performance Characteristics

| Operation | Latency target | Notes |
|---|---|---|
| Query embedding | ~50ms P95 | Azure OpenAI text-embedding-3-large |
| Hybrid search(top=50)| ~200-500ms P95 | Azure AI Search Standard S1 |
| Cohere Rerank(50 → 5) | ~300-800ms P95 | API call to Cohere |
| **Total retrieval(query → top-5)** | **< 1.5s P95** | Critical for `/query` TTFT < 2s budget |
| **Cost per query** | ~$0.0001 embedding + ~$0.001 Cohere | Per-month POC ~50k queries × $0.0011 = ~$55 |
| Throughput | ~30 QPS Standard S1 | Beta target ~10 QPS supportable |

---

## 6. Test Strategy

| Test type | Scope | Status |
|---|---|---|
| **Hybrid baseline integration**(Gate 1 prep) | Real Azure AI Search + 30 query eval set | **W2 D5 ★ Gate 1 critical** |
| **Reranker contract test**(each impl) | Mock query+candidates → assert ordered output | W3 D2 |
| **Cohere integration smoke** | Real Cohere API call | W3 D1 |
| **Reranker shootout harness**(W4) | Run 4 rerankers on same eval set → comparison report | W4 D2-D5 |
| **R6 fallback test** | Stop Cohere → assert fallback to Azure semantic happens | W4 D3 |
| **Empty result test** | Query for known-absent topic → assert empty list, no error | W2 D5 |
| **Disabled chunk filter** | Mark chunks `enabled=false` → assert excluded from results | W3 D2 |
| **Coverage target** | ≥ 80% per CLAUDE.md H6 | W4 |

---

## 7. Future Evolution / Tier 2 Hooks

| Tier 2 feature | C04 evolution |
|---|---|
| **GraphRAG**(graph traversal) | Add `mode: "hybrid" | "graph" | "hybrid_then_graph"` to retrieve();GraphRAG mode queries entity index per `C03 future evolution` + traverses via graph store |
| **Cross-KB retrieval** | `retrieve(query, kb_ids: list[str], top_k)` — issue parallel queries to multiple indexes,merge with weighted fusion |
| **Query expansion via LLM** | Pre-step:LLM generates 2-3 query variations;OR-search across them;dedup results |
| **HyDE(Hypothetical Document Embedding)** | LLM generates expected answer doc → embed it → retrieve similar to that synthetic doc(Tier 2 advanced)|
| **Per-user personalization**(Beta+ user history) | User profile embedding boost retrieval ranking |
| **Multi-modal**(image + text query) | Image embedding query alongside text;hybrid fusion image-vector + text-vector + BM25 |
| **Adaptive top_k based on query type** | Short factoid → top_k=3;exploratory → top_k=20;ML classifier or LLM-based gate |

---

## 8. Open Items / TODO

- [ ] **W2 D5 hybrid baseline impl** — Azure AI Search REST query
- [ ] **W2 D5 Gate 1 evaluation** — R@5 ≥ 80% target on synthetic eval set
- [ ] **W3 D1 Cohere wire** — `reranker/cohere.py`
- [ ] **Q5 Cohere procurement Path A vs B** decision before W3 D1
- [ ] **W4 D2-D5 shootout harness**(per eval-methodology.md §7)
- [ ] **W4 末 Q21 reranker pick** decision based on shootout data
- [ ] **R6 fallback config flag** wiring(`COHERE_FALLBACK_TO_SEMANTIC=true`)

---

**Cross-refs**:
- Catalog: [`../COMPONENT_CATALOG.md#c04--retrieval-engine`](../COMPONENT_CATALOG.md#c04--retrieval-engine)
- Spec: `architecture.md §3.1`(pipeline)+ `§3.2`(stack)+ `eval-methodology.md §7`(shootout)
- Risks: R3(Cohere procurement),R6(Cohere outage hot fallback)
- Cross-component: depends on C03 index ready;feeds C05;traced via C07;evaluated by C06
