---
component: C06
name: Eval Framework
catalog_ref: ../COMPONENT_CATALOG.md#c06--eval-framework
spec_refs: [eval-methodology.md, architecture.md §6.3, architecture.md §8.1, eval-set-v0.yaml]
status: v0-draft
last_updated: 2026-05-01
---

# C06 — Eval Framework Design Note

> **Status**:`v0-draft`(W1 D1 validator + 30 條 synthetic eval set scaffold ✅;RAGAs runner + LLM judge + gate logic 仍 forward-looking W2-W4)
>
> **Owner**:AI(framework)+ Chris(SME labeler per Q14 self-assigned)

---

## 1. Internal Architecture

```
scripts/
└── validate_eval_set.py        ← Schema validator (stdlib + pyyaml,no pydantic)✅ W1 D1

docs/
└── eval-set-v0.yaml            ← 30 條 synthetic ground truth scaffold ✅ W1 D1
   (W4: → eval-set-v1.yaml after SME validation + 20 real query)

backend/eval/                   ← W2+ runtime
├── __init__.py
├── runner.py                   ← (W2) RAGAs invoker + result aggregator
├── judge.py                    ← (W3) LLM judge wrapper (GPT-5.4-mini)
├── gates.py                    ← (W2) Gate 1 / Gate 2 decision logic
├── shootout.py                 ← (W4) 4-way reranker shootout harness
└── reports/                    ← Generated YAML / JSON reports
   (gitignored,reports/ root level)
```

**Pipeline flow**:

```
Eval Set YAML
    │
    ▼
validate_eval_set.py  ← schema check (W1 ✅)
    │
    ▼
runner.py             ← for each query: invoke C04 + C05 to get response + retrieved chunks
    │
    ├─ RAGAs metric calc (4 metrics) ── faithfulness / answer-relevancy / context-precision / context-recall
    └─ judge.py LLM judge ──── GPT-5.4-mini scores each response on factual / refusal / citation accuracy
    │
    ▼
gates.py              ← decision logic
    │
    ├─ Gate 1 (W2 D5): R@5 ≥ 80% on hybrid retrieval baseline → pass to W3
    └─ Gate 2 (W4 D5): 4 metrics within ±5pp of target → pass to W5
    │
    ▼
reports/eval_run_YYYY-MM-DD_HHmm.yaml  ← per-run snapshot

shootout.py (W4)      ← run same eval set against 4 rerankers → comparison report
```

---

## 2. Key Interfaces

### Inputs
- `docs/eval-set-v{n}.yaml` — ground truth set(30+ queries)
- C04 `RetrievalEngine.retrieve(query, kb_id, top_k)` — get retrieved chunks
- C05 `GenerationPipeline.generate(query, chunks)` — get synthesized response with citations
- C12 Azure OpenAI `gpt-5.4-mini` deployment(judge)

### Outputs
- `reports/eval_run_*.yaml` — per-run metric snapshot
- Gate decision:`{"gate": "G1" | "G2", "passed": bool, "details": {...}}`
- Reranker shootout: `reports/reranker_shootout_*.yaml`(W4)

### Side effects
- Azure OpenAI judge API calls(~1 call per query for judge,30+ per run)
- C04 / C05 invocation traces written to Langfuse(C07)

---

## 3. Critical Design Decisions

| Decision | Rationale |
|---|---|
| **Validator stdlib only(`zipfile` + `xml.etree` + `pyyaml`),no pydantic dep** | Per W1 D1 reality:pydantic install supply uncertain;validator should run on bare Python 3.12 install。`pyyaml` 細 pure-Python wheel,low install risk |
| **Eval set YAML(non-JSON)** | Human-readable for SME labeler edit;multiline `expected_answer` 易讀;pyyaml round-trip preserves structure |
| **30 條 synthetic baseline W1 + 20 條 real query W3-W4** | W1 baseline 唔 block W4 evaluation 上前(per `§8.1` R2 mitigation)。Real query W3 user signal capture |
| **RAGAs 4 metrics(non-custom)** | Industry standard;auditable;easier stakeholder communication 比 custom metric |
| **GPT-5.4-mini judge**(non GPT-5.5)| Cost-quality tradeoff:5.4-mini ~10× cheaper than 5.5;judge consistency 對 answer quality 影響 minor;5.5-pro reserved if budget allow W4 |
| **Gate decision logic explicit(non implicit)** | Per `§6.3`:Gate 1 W2 末 R@5 ≥ 80% pass;Gate 2 W4 末 4-metric ±5pp。Pre-set thresholds 避免 sunk-cost continuation |
| **Reranker shootout W4 4-way**(Cohere baseline + Voyage + ZeroEntropy + Azure built-in)| Per `decision-form Q21` resolution path |
| **LLM judge first pass + Chris verify fallback**(per `§8.1` R2)| Q14 ground truth labeling Chris self-assigned;efficiency through LLM judge first cut,Chris verify edge cases |

---

## 4. Edge Cases & Error Handling

| Edge case | Handling |
|---|---|
| Eval set schema invalid(missing required field)| Validator exit 1 with field-level error message |
| Duplicate `query_id` in eval set | Validator catches |
| `oos` (out-of-scope) query without `expected_refusal: true` | Validator catches |
| Non-oos query without `primary_chunk_ids` | Validator catches |
| RAGAs metric throws(LLM judge unavailable)| Retry 3× with exponential backoff(via tenacity);若 final fail,mark metric as `null`,report `partial_pass` |
| Azure OpenAI judge rate limit | tenacity retry with backoff;若 rate limit persistent,fall back to `gpt-5.4-nano` for that query |
| Real chunk_id not found in eval set(stale ground truth)| Mark query as `skipped`,log warning,exclude from aggregate metric |
| Time-out 1 query > 30s | Cancel,mark as `timed_out`,exclude from metric;count toward error rate |

---

## 5. Performance Characteristics

| Operation | Cost / Time | Notes |
|---|---|---|
| Validate eval set | < 1s | Stdlib YAML parse + rule check |
| Single query eval | ~10-30s | C04 retrieval(~1s)+ C05 generation(~5-15s)+ judge(~3-5s)+ RAGAs metrics(~3-5s)|
| Full eval run(30 queries)| ~5-15 min | Sequential;may parallelize W4 if needed |
| Full eval run(50 queries W4)| ~10-25 min | |
| Reranker shootout W4(4 rerankers × 30 queries)| ~30-45 min | Reuse retrieval result,only rerank step varies |
| Cost per eval run(LLM)| ~$1-3 USD | 30 queries × ~3 LLM calls(synthesis + judge + metric) |
| Cost W4 shootout | ~$10-15 USD | 4× judge cost increase |

---

## 6. Test Strategy

| Test type | Scope | Status |
|---|---|---|
| **Validator self-test**(invalid eval set fixture)| validator catches all 4 rule types | W1 D2(deferred R8 pytest) |
| **Mock LLM eval**(judge stubbed)| runner end-to-end with mock C04 / C05 / judge | W2 D5 |
| **Real eval(small set)**(5 query smoke run)| Real Azure OpenAI + Azure AI Search(post Q3+Q4 wired)| W2 末 |
| **Gate decision unit test** | Gate logic with synthetic metric tuples → expected pass/fail | W2 D5 |
| **Shootout harness test** | Mock 4 reranker → comparison report shape correct | W4 D2 |
| **Real eval(full set)** | 30 query → metric report → Gate 1 decision | **W2 D5 Gate 1 prep** |
| **Coverage target** | ≥ 80% for `backend/eval/` per CLAUDE.md H6 | W4 |

---

## 7. Future Evolution / Tier 2 Hooks

| Tier 2 feature | C06 evolution |
|---|---|
| **Continuous eval**(Beta+)| Schedule daily eval run via Azure Container Apps Jobs(C12);trend dashboard via C09 admin UI |
| **Real query auto-collection**(Beta+)| Capture user queries from `/query` endpoint(C08)→ flag for SME review → optional add to eval set |
| **Adversarial eval set**(Tier 2 GraphRAG)| Add jailbreak / prompt injection test cases;measure refusal rate |
| **Multi-language eval**(Tier 2 JP / ZH)| Per-language eval subset;per-language judge with language-aware prompting |
| **Pairwise judge**(human preference learning)| Replace single-LLM scoring with pairwise comparison;Chatbot Arena style |
| **Cost / latency tracking per eval run** | Aggregate Langfuse traces from C07,append to eval report |

---

## 8. Open Items / TODO

- [ ] **F11 ground truth fill**(30 → 30 SME-validated)— blocked Q2 sample for chunk_id discovery(R10)
- [ ] **W2 D5 runner.py impl** — RAGAs invocation
- [ ] **W2 D5 gates.py impl** — Gate 1 logic
- [ ] **W3 D2 judge.py impl** — GPT-5.4-mini wrapper
- [ ] **W4 D2 shootout.py impl** — 4-way reranker harness
- [ ] **W4 add 20 real query** to eval-set-v1.yaml(per Q6 resolution)
- [ ] **W4 5 table-heavy query** for R4(LLM hallucination on tables)regression
- [ ] **Cost log integration with C07** — per-eval-run cost summary to Langfuse

---

**Cross-refs**:
- Catalog: [`../COMPONENT_CATALOG.md#c06--eval-framework`](../COMPONENT_CATALOG.md#c06--eval-framework)
- Spec: [`../../eval-methodology.md`](../../eval-methodology.md)(eval design全)+ `architecture.md §6.3`(W2 + W4 explicit gates)+ `§8.1` R2 risk
- Validator commit: `cc0b90b`(W1 D1)
- Eval set scaffold: [`../../eval-set-v0.yaml`](../../eval-set-v0.yaml)
- Risks: R2(ground truth slip — Resolved via Q14)、R10(Q2 sample delay)
