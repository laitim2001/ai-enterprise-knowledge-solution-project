# ADR-0034: Query expansion + RAG-Fusion — multi-variant retrieval with Reciprocal Rank Fusion

**Date**: 2026-05-24
**Status**: Accepted
**Approver**: Chris(chat 2026-05-24「可以開始執行 ADR-0034」)
**Phase context**: `W25-image-association-deep-fix` F3 deliverable
**Related**:
- ADR-0033 chunker low-value tuning(F1 deliverable — chunker fix is prerequisite to F3 lift quantification)
- ADR-0023 KB Manager persistent backing(if `enable_query_expansion` lands on `KbConfig`,Postgres backend gains the field — F3 D1 decision point)
- ADR-0017 R8 corp-proxy mitigation pattern(reformulator using existing Azure OpenAI SDK avoids R8 trigger — pre-empts dependency-add risk)
- Investigation memo `docs/03-implementation/image-chunk-retrieval-investigation-2026-05-23.md`
- W25 progress.md Day 3 entry — user real-world observation Q-W25-I07「show me all the Integration scenarios」returns 2/5 + 0 images,validates D4 necessity empirically

---

## Context

### Trigger

W25 plan §1 explicit framing(per user chat 2026-05-23「我需要的是完整地解決圖片和文字內容的關聯問題」+ AskUserQuestion Path III phase-level full optimization):**D3 chunker fix alone is insufficient for image-text association completion**。

W25 Day 3 user real-world observation crystallizes the gap:

> 用戶 2026-05-24 chat: `Show me all the Integration scenarios`
> Backend retrieval returns **2 citations**(covering Scenarios A + B summary chunk)+ **0 images**
> LLM answer reuses footnote 1/2 across 5 scenario mentions(C/D/E only paraphrased,no distinct chunk citation)
> Expected document content: A-E scenarios each with embedded image diagram

**Root cause**(per W25 plan §1.1 H2 sub-thesis):**single-hop hybrid retrieve cannot expand vocabulary**:
- Original query「Integration scenarios」lexically overlaps the §X-summary chunk(「five end-to-end scenarios covering...」)well
- A-E individual chunks use scenario-specific vocabulary(「Customer service request submission」/「Saga-style multi-system orchestration」/「Inbound event-driven flow」/「Batch ETL data movement」)
- BM25 + vector similarity both score `summary chunk + A or A+B` higher than `C/D/E chunks` for the literal query phrasing
- Top-K hybrid retrieve returns only summary + 1-2 scenario chunks → LLM sees 2 distinct chunks → cannot cite C/D/E individually

This pattern generalizes:**any query asking for「all instances of category X」across multi-section docs is at risk** when section vocabulary diverges from query vocabulary。Image association compounds the gap — if A-E chunks were retrieved,F5 D1 citation post-process could attach their embedded images;current single-retrieve path prevents this entirely。

### Spec baseline(`architecture.md §3.7` query orchestration)

> "Query orchestration:GPT-5.5 synthesizes from top-K hybrid-retrieved chunks(Azure AI Search BM25 + vector + Cohere Rerank);CRAG L2 loop for low-confidence retrieval"

CRAG L2 loop **does not** do query reformulation — it issues NEW queries based on retrieval-grade self-assessment(loop-back if low-score),not multi-variant fan-out per call。

### Code locus(per pre-active-flip R6 recursive grep verification)

```python
# backend/pipeline/query_pipeline.py — current single-query path
async def query_pipeline_run(query: str, kb_id: str, ...) -> QueryResponse:
    # 1. Hybrid retrieve (single query → top-K)
    chunks = await hybrid_searcher.search(query, kb_id, k=settings.retrieval_k)
    # 2. Cohere rerank
    reranked = await cohere_reranker.rerank(query, chunks)
    # 3. CRAG L2 loop (if low-confidence, re-issue)
    # 4. Synthesize answer
    answer = await synthesizer.synthesize(query, reranked, ...)
    return answer
```

**W25 F3 D4 = insert reformulator + fusion BEFORE step 1**:
- Reformulator generates `max_variants - 1` query variants
- Each variant runs step 1 (hybrid retrieve) independently
- Results fused via Reciprocal Rank Fusion → unified top-K
- Step 2 (Cohere rerank) + step 3 (CRAG) + step 4 (synthesize) unchanged
- Backward compatible:`enable_query_expansion=false` → original path preserved bit-identical

This change touches `architecture.md §3.7` query orchestration mechanism → triggers CLAUDE.md §5.1 H1(architectural component change)→ MUST write ADR。

---

## Decision

**Two-component module addition + integration + config flag**:

### (a) NEW module `backend/pipeline/query_reformulator.py`

```python
async def reformulate(
    query: str,
    max_variants: int = 4,            # original + 3 reformulations default
    llm_client: AzureOpenAIClient,    # reuses existing GPT-5.5-mini deployment
    latency_cap_seconds: float = 3.0,  # internal cap for reformulation alone (leaves budget for retrieval)
) -> list[str]:
    """
    Generate up to `max_variants - 1` reformulated query variants alongside
    the original query. Returns list of length [1, max_variants]:
    - [original] if reformulation fails / times out (graceful fallback per R3)
    - [original, variant_1, variant_2, ...] on success

    Hard cap: returns within `latency_cap_seconds` wall-clock; on timeout
    returns [original] only. Per W25 plan §8 Q4 hard P95 < 5s budget for
    full pipeline.

    Prompt: GPT-5.5-mini one-shot system + user prompt produces JSON array
    of variants. Prompt template lives inline (single source of truth, no
    external prompt file per Karpathy §1.2 simplicity).
    """
```

**Vendor choice**:**GPT-5.5-mini via existing Azure OpenAI SDK + chat completion endpoint**(per CLAUDE.md §5.2 H2 vendor lock table — Azure OpenAI is the locked synthesizer + judge vendor;mini variant for reformulation is cheap-LLM use case within same vendor;**zero new dependency** → no R8 trigger per ADR-0017 Decision-rule #5)。

**Prompt template**(inline,illustrative):

```text
SYSTEM: You are a query reformulation assistant. Given a user search query,
generate {N} alternative phrasings that explore distinct semantic angles
of the same information need. Variants should:
- Use synonyms or domain-specific vocabulary likely to appear in source documents
- Decompose multi-part questions into focused sub-queries
- NOT change the user's intent or scope
- Be self-contained search queries (not conversational replies)

Return JSON: {"variants": ["variant 1", "variant 2", ...]}

USER: Reformulate this query into {N} alternative phrasings: "{original_query}"
```

### (b) NEW module `backend/retrieval/result_fusion.py`

```python
async def fused_retrieve(
    queries: list[str],
    kb_id: str,
    k: int,
    searcher: HybridSearcher,
) -> list[ChunkRecord]:
    """
    Run hybrid retrieve once per query, then merge results via Reciprocal
    Rank Fusion (RRF) per the canonical formula:

        rrf_score(chunk) = sum over queries of 1 / (60 + rank_in_query)

    where rank_in_query is 1-indexed position of chunk in that query's
    top-k hybrid results (chunks not in a query's top-k contribute 0).

    Returns top-k chunks by descending RRF score, deduplicated by chunk_id.

    Parallel: hybrid retrieves issue concurrently via asyncio.gather (each
    query is independent IO-bound work — Azure Search + Azure OpenAI
    embedder calls).
    """
```

**RRF rank-floor constant `60`**:per Cormack et al. 2009 canonical paper(industry-standard RRF parameter,not tuned per kb/query — empirical observation that RRF is robust to floor choice in [40, 100] range)。

### (c) Integration in `backend/pipeline/query_pipeline.py`

```python
async def query_pipeline_run(...) -> QueryResponse:
    expand = settings.enable_query_expansion  # OR kb_config.enable_query_expansion (D1 decision)
    if expand:
        variants = await reformulate(query, ...)              # NEW step 0a
        chunks = await fused_retrieve(variants, kb_id, k, hybrid_searcher)  # NEW step 0b (replaces step 1)
    else:
        chunks = await hybrid_searcher.search(query, kb_id, k)  # original step 1 preserved bit-identical
    # ... existing step 2 (Cohere rerank), step 3 (CRAG), step 4 (synthesize) UNCHANGED
```

### (d) Config flag location — **`Settings` global default**(D1 decision per Karpathy §1.2 simplicity)

- **`settings.enable_query_expansion: bool = False`** in `backend/storage/settings.py`
- **NOT** `KbConfig.enable_query_expansion`(rejected — see Alternatives §3)
- Override via `.env` `ENABLE_QUERY_EXPANSION=true` for staging/Beta toggle
- Future:if per-KB tuning needed(eg. some KBs benefit,others regress),promote to `KbConfig` field per ADR-0023 KbConfig extension pattern(future-tier change,不喺本 ADR scope)

---

## Alternatives Considered

### Rejected: CRAG L4+ multi-agent retrieval / agentic re-issue

**Description**:Use L4+ multi-agent loop to issue follow-up queries based on retrieval-grade self-assessment(eg. retrieved Scenario A but missing C/D/E → issue「Scenario C details」「Scenario D details」)。

**Why rejected**:
- Out of Tier 1 scope per CLAUDE.md §5.4 H4(L4+ multi-agent orchestration is explicit Tier 2)
- Higher latency(serial loop vs parallel fan-out)+ harder to budget P95
- More LLM calls per query(non-trivial cost)
- Complexity not justified by W25 use case empirical evidence

### Rejected: Multi-query embedding retrieval(LangChain `MultiQueryRetriever` style)without RRF

**Description**:Generate variants,run each retrieval,concat results without rank-aware fusion。

**Why rejected**:
- Naive concat doesn't deduplicate or weight chunks by ranking across variants
- Same chunk surfaced in multiple variant top-K should rank higher than chunk surfaced in only one — RRF handles this correctly,plain concat does not
- RRF formula is trivially cheap(O(n × k) per query, k typically ≤ 20)— complexity cost is negligible vs accuracy benefit

### Rejected: HyDE(Hypothetical Document Embedding)— generate fake answer first then retrieve via answer embedding

**Description**:LLM drafts hypothetical answer to query → embed answer → retrieve chunks similar to embedding。

**Why rejected**:
- Doesn't address vocabulary expansion across multi-section coverage problem(eg. user wants「all Integration scenarios」— HyDE generates ONE hypothetical answer about Integration scenarios,still single retrieve)
- HyDE is more aligned with single-correct-answer queries(eg.「what is X?」),not「list all X」queries
- Adds one LLM call without solving the per-variant fan-out need
- May be additive future enhancement(orthogonal to D4)

### Rejected: `KbConfig.enable_query_expansion` per-KB flag instead of global `Settings`

**Description**:Promote `enable_query_expansion` to `KbConfig` field so each KB sets its own toggle。

**Why rejected**(for THIS ADR — may revisit if F4/F6 verify shows KB-specific regression):
- Premature configuration per Karpathy §1.2 — W25 has 1 active dev KB + 2 archived test KBs;no empirical signal that per-KB tuning is needed
- KbConfig field add triggers ADR-0023 Postgres schema migration(`ALTER TABLE knowledge_bases ADD COLUMN enable_query_expansion BOOLEAN DEFAULT FALSE`)+ KbConfig schema update + 5+ Pydantic call sites
- Global Settings flag is simpler bootstrap for Tier 1;promote to KbConfig later if F4/F6 shows per-KB regression
- Safety net:if per-KB regression surfaces,`Settings.enable_query_expansion=False` global disable acts as immediate rollback while we promote to KbConfig

### Rejected: Reformulate via locally-running open-source LLM(eg. Qwen / Llama via Ollama)

**Description**:Use local LLM(no Azure OpenAI call cost / latency)for reformulation。

**Why rejected**:
- Violates CLAUDE.md §5.2 H2 vendor lock(Azure OpenAI is the locked LLM vendor)
- New runtime dependency(Ollama server / GGUF model file download)triggers R8 corp-proxy risk per ADR-0017
- Cost of GPT-5.5-mini reformulation calls is negligible(~50 tokens output × $0.0X / 1K tokens × X queries/day << total Azure budget)
- Latency:GPT-5.5-mini network call ~300-500ms vs local Ollama may be slower on dev hardware

### Rejected: Skip D4 entirely,rely on F1 chunker + F5 D2/D1 alone

**Description**:Don't implement D4;rely on F1 chunker fix lifting recall + F5 D2 image-low-value-relax + D1 citation post-process to deliver image association without query expansion。

**Why rejected**:
- Day 3 user real-world Q-W25-I07 evidence explicitly shows F1-alone fails on multi-section「list all X」queries(2/5 returned + 0 images post F1 re-ingest)
- F5 D1 citation post-process attaches NEIGHBOUR images to retrieved chunks — but if A-E chunks themselves aren't retrieved,no neighbour images can be attached for unretrieved chunks
- D4 is the load-bearing component for vocabulary expansion;skipping it = W25 phase goal G1 unachievable

---

## Consequences

### Positive

- **Recall lift across vocabulary-divergent multi-section queries**:RRF fusion of N variants surfaces chunks each variant ranks high,union → broader chunk coverage than single retrieve
- **Image association rate lift**:more A-E chunks retrieved → F5 D1 citation post-process can attach more neighbour images → W25 phase goal G1(≥ 5/8 image hit rate)achievable in combination with F5
- **Vendor lock preserved**:reuses GPT-5.5-mini via existing Azure OpenAI SDK — zero new deps,no R8 trigger
- **Backward compatible**:`enable_query_expansion=false` default → original path bit-identical;safe rollback via env var flip
- **General retrieval improvement** beyond image use case:any vocabulary-divergent query benefits(non-image queries gain recall too)

### Negative

- **Latency P95 envelope shrinks**:reformulation adds ~300-500ms + N parallel hybrid retrieves(parallel via `asyncio.gather` — single longest-tail dominates not sum,but worst-case still ≥ single hybrid latency);per W25 plan §8 Q4 hard P95 < 5s budget,F4 verify will measure + fall back if exceeded
- **Cost increase per query**:N variants → N hybrid retrieves(Azure Search + embedder calls)+ 1 GPT-5.5-mini reformulation call;rough budget calc ~$0.0X / query vs pre-D4 ~$0.00X — Tier 1 dev/Beta scale(low query volume)cost negligible,monitor at scale
- **Reformulation quality variance**:GPT-5.5-mini may generate poor variants(off-topic / over-narrow / over-broad)→ RRF can introduce noise;F4 verify catches via Faithfulness drop measurement;back-out option = `Settings.enable_query_expansion=False` default
- **Test surface expansion**:new modules `query_reformulator.py` + `result_fusion.py` need unit tests + integration coverage(per plan F3.5);+~10-15 NEW tests added to backend pytest baseline

### Neutral

- **`KbConfig` extension deferred**:future per-KB tuning capability postponed until empirical evidence(non-blocking)
- **RRF k=60 floor constant**:industry standard,not tuned;documented for future amendment if F4/F6 shows alternate floor outperforms
- **Reformulator prompt template inline**:single source of truth in `query_reformulator.py` module — if prompts grow / need versioning,future extraction to template file is straightforward refactor

---

## Implementation Mapping

| ADR section | Plan F3 acceptance criterion |
|---|---|
| Decision (a) reformulator module | F3.2 `backend/pipeline/query_reformulator.py` |
| Decision (b) RRF fusion module | F3.3 `backend/retrieval/result_fusion.py` |
| Decision (c) query_pipeline integration | F3.4 `backend/pipeline/query_pipeline.py` integration |
| Decision (d) Settings flag | F3.D1 pre-decide D1 — answered: Settings global default |
| Latency cap | F3.2 `latency_cap_seconds=3.0` + F4 verify P95<5s hard cap |
| Unit + integration tests | F3.5 `test_query_reformulator.py` + `test_result_fusion.py` + e2e integration |

---

## References

- W25 plan §2 F3 acceptance criteria
- Investigation memo `docs/03-implementation/image-chunk-retrieval-investigation-2026-05-23.md`
- W25 progress.md Day 3 entry — user Q-W25-I07 empirical evidence
- ADR-0033 chunker low-value tuning(F1 — prerequisite to F3 lift measurement)
- ADR-0017 R8 corp-proxy mitigation pattern(reformulator vendor choice rationale)
- Cormack, G. V., Clarke, C. L., & Buettcher, S. (2009). Reciprocal rank fusion outperforms condorcet and individual rank learning methods. SIGIR.(RRF canonical paper — k=60 floor source)
- CLAUDE.md §5.1 H1 architectural change(this ADR addresses §3.7 query orchestration)
- CLAUDE.md §5.2 H2 vendor lock(Azure OpenAI reuse — no vendor decision change)
- CLAUDE.md §5.4 H4 Tier 1 boundary(L4+ multi-agent retrieval rejected as Tier 2)
