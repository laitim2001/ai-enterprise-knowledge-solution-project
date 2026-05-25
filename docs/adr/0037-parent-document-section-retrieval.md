# ADR-0037: Parent-Document / Section-Level Retrieval(Tier 1 ceiling for enumeration queries — small-to-big aggregation)

**Date**: 2026-05-25
**Status**: Accepted; amended 2026-05-26 W28 F4 per Setting sweep
**Approver**: Chris(技術 Lead)— AskUserQuestion approved 2026-05-25 D1 cont(Q4 Default OFF + Q1 top_k=1 + Q2 depth_offset=1 + Q6 Both on — all Recommended picks;Q3+Q5+Q7+Q8 proposed defaults batch-locked at same approval);**amendment 2026-05-26 W28 F4 Chris approved**(Full Settings flip per W28 best combo Run 3.A — Recommended pick)
**Trigger**: W26-eval-driven-retrieval-tuning F1 empirical refutation 2026-05-25 D1 — F1 RAGAs baseline(`recall_at_5=0.8744` + `faithfulness=0.9851` + 5/13 queries `context_recall=0.00` recall-dominant)+ threshold-probe(`backend/scripts/w26_threshold_probe.py` 25 Cohere v4.0-pro scores)distribution `P25=0.83 / P50=0.90 / P75=0.91 / min=0.67 / max=0.97` 加上 Q-W25-I01(PASSED control)min 0.67 同 Q-W25-I02(FAILED `context_recall=0`)min 0.88 highly overlapping → **Cohere score CANNOT differentiate failed vs passed queries for enumeration queries**;brief §3 方向 A 「排第 4/5 低分 chunk 照入 context → 唔相關內容」premise empirically refuted。Per brief §1 「NOT EKP-unique bug — Dify same query also fails」 + §6 step 4 escalation。Chris pivot pick 2026-05-25 D1 AskUserQuestion (C) parent-document retrieval ADR-0037 over Step 1 rerank threshold scope。

---

## Context

### Spec promise(authoritative,frozen v6)

**architecture.md §3.1 Query Pipeline**(lines 184-219):

```
[Query Preprocessor]
       ↓
[Hybrid Retrieval BM25 + vector RRF top 50]
       ↓
[Cohere Rerank → top 5]                     ← top-K rerank cuts
       ↓
[Context Expander](per ADR-0020,prev/next ±1 chunk window)
       ↓
[CRAG Confidence Judge]
       ↓
[GPT-5.5 Synthesis with Citation]
       ↓
[Final Response]
```

**architecture.md §3.5 ChunkRecord + §3.6 Index Schema**(lines 314-411):

- `section_path: list[str]` populated by `backend/ingestion/chunker/layout_aware.py`(per ADR-0004 layout-aware chunking;example `["Operation", "Recovery", "Paper Jam"]` 喺 §3.5 line 328)
- Azure AI Search index field:`{"name": "section_path", "type": "Collection(Edm.String)", "filterable": true, "facetable": true}`(§3.6 line 364)— **already indexed,no schema change required**
- `chunk_index` field `Edm.Int32` filterable + sortable — supports ordered aggregation
- `doc_id` field filterable — supports same-doc scoping(cross-doc boundary precedent per ADR-0020)

### W26 F1 empirical refutation evidence(2026-05-25 D1)

#### F1 RAGAs baseline `baseline-metrics-W26-D1.md`(13-query eval-set-v0-w25-supplement.yaml subset):

| Metric | Aggregate | Symptom |
|---|---|---|
| `recall_at_5` | **0.8744** | High — top-5 retrieves correct chunks most of the time |
| `faithfulness` | **0.9851** | Very high — synthesis stays grounded in retrieved chunks |
| `answer_relevancy` | ~0.85 | High — synthesis addresses query intent |
| `context_recall` | **5/13 queries = 0.00** | **Recall-dominant failure mode** — for these queries the ground-truth answer **cannot be reconstructed** from retrieved chunks even when faithfulness高 |
| `context_precision` | ~0.7 average | Moderate — irrelevant chunks present but not dominant noise |

**Pattern**:5/13 queries failure mode = retrieved chunks contain factually-grounded content(faithfulness 0.9851 holds)but the **scope is incomplete**(`context_recall=0.00` ground truth answer chunks NOT covered by top-5)。為 enumeration / aggregation-class queries 嘅 signature symptom。

#### Threshold-probe `threshold-probe-W26-D1.json`(5 priority queries × top-5 = 25 chunks):

```json
{
  "reranker_model": "rerank-v4.0-pro",
  "distribution": {
    "count": 25,
    "min": 0.67,
    "p25": 0.83,
    "p50_median": 0.90,
    "p75": 0.91,
    "max": 0.97,
    "mean": 0.886
  }
}
```

**Per-query score range comparison**:

| Query ID | Status | Top-5 Cohere score min | Top-5 max | Diagnostic |
|---|---|---|---|---|
| Q-W25-I01 | ✅ PASSED control | **0.67** | 0.93 | Low-score chunk in passed query |
| Q-W25-I02 | ❌ `context_recall=0.00` | **0.88** | 0.95 | All chunks above 0.85 in failed query |
| Q-W25-I03 | ❌ `context_recall=0.00` | 0.82 | 0.94 | High-score chunks ≠ correct chunks |
| Q-W25-I07 | ❌ refuse + partial | 0.90 | 0.97 | Highest baseline,still fails |
| Q-W25-T04 | ❌ precision=0 + recall=0 | 0.67 | 0.91 | Low-score chunk in failed query |

**Empirical conclusion**(per Q-W25-I01 PASSED min 0.67 = Q-W25-T04 FAILED min 0.67 — same score,opposite outcome;Q-W25-I02 FAILED min 0.88 > Q-W25-I07 PASSED partial min 0.90 inversion):

> **Threshold cutoff at any value cannot differentiate failed vs passed queries**。Cohere v4.0-pro confidently rates wrong chunks high(0.88+)for enumeration queries on layout-chunked content,同時 passed queries have legitimate low-score chunks(0.67)which a threshold would incorrectly drop。

→ **Brief §3 方向 A premise empirically refuted**:「排第 4/5 低分 chunk 照入 context → 唔相關內容」 — Cohere 排前 5 全 0.67-0.97 高分,問題唔係「低分 leak」。

### Architectural root cause(per brief §1 + §3 + W26 F1 evidence)

問題本質 = **「enumeration / aggregation query × top-K factoid-tuned retrieval × 定長 layout-aware chunking」嘅 architectural mismatch**:

1. **Query class mismatch**:Q-W25-I07「show me **all** the Integration scenarios」要求 high recall + cross-chunk aggregation(砌返成個 §8 五個 scenario)— 但 top-5 precision-oriented retrieval 本質做唔到窮舉
2. **Chunking artifact**:5 個 scenario(A/B/C/D/E)分佈喺 §8 多個獨立 chunks;top-5 retrieve 只 hit 其中 1-2 個 scenario chunks + 摻 §3.1 chunk #8(語義相近但 topically off)
3. **Reranker scope limitation**:Cohere v4.0-pro 嘅 cross-encoder 對 single-chunk relevance scoring 強,但 **唔知** 個 chunk 屬於邊個 logical section,亦 **冇** mechanism aggregate 跨 chunks(top-N selection 純粹基於 query↔chunk pairwise score)
4. **Not EKP-specific**:Dify 用同樣 Cohere v4.0-pro reranker + General(定長)chunking + Top K=3-4 on the same query → 答「I'm not sure about that」refuse(per brief §1)→ **唔係 implementation bug,係架構本質 mismatch**

### Tier 1 ceiling rationale(why parent-doc 係正確 escalation)

| 既有 mitigation | 處理層 | 對 enumeration query 嘅效用 |
|---|---|---|
| W25 ADR-0033 chunker low_value tuning | Ingestion | ✅ 解 image-association gap,**未** 解 enumeration |
| W25 ADR-0034 query expansion + RRF | Query preprocess | ⚠️ 增加 recall on vocab-divergent queries,**未必** cover enumeration scope |
| W25 ADR-0035 low_value soft-relax(+ BUG-025 symmetric deboost) | Retrieval scoring | ✅ 解 text-only silent-drop,**未** 解 enumeration |
| ADR-0020 Context Expander(prev/next ±1) | Post-rerank | 細範圍 expansion,**唔夠 cover** 跨多個 sibling chunks(§8 有 5 個 scenario × N chunks each) |
| **此 ADR-0037 parent-doc retrieval** | **Post-rerank** | **直接 cover 整個 logical section**(§8 全部 scenarios)— **唯一 architectural fit** |

**業界標準precedent**(per brief §5):
- LangChain `ParentDocumentRetriever`(small-to-big retrieval)— retrieve fine-grained child chunks for hit,return larger parent doc for context
- LlamaIndex `AutoMergingRetriever` — siblings auto-merge to common parent based on threshold
- Dify Parent-child chunking mode

EKP 已有嘅 `section_path` metadata = layout-aware chunking's natural parent indicator。**Tier 1 唔需要 re-chunk + re-embed**(structurally invasive);只需 retrieve-time aggregation pipeline。

### Tier 1 vs Tier 2 boundary

呢個 ADR **唔觸** Tier 2 list(`architecture.md §11`):
- ❌ GraphRAG / Knowledge Graph(out — `architecture.md §11` Tier 2)
- ❌ L4+ multi-agent orchestration(out)
- ❌ Workflow / plugin builder(out)
- ❌ Multi-tenancy(out)
- ❌ Multi-modal retrieval(out)
- ❌ Custom LLM fine-tuning(out)

ADR-0037 = **retrieval pipeline architectural enhancement**(同 ADR-0020 Context Expander 一致)— 屬 Tier 1 ceiling option per brief §6 step 4「若 W26 Step 2 仍唔解 enumeration query → 開 parent-document retrieval / query routing 嘅 ADR(H1)」。

### H1 trigger confirmation

呢個改動 触 CLAUDE.md §5.1 H1「architectural change」嘅 3 個 trigger:

1. ✅ **加 / 改 / 刪 `docs/architecture.md` §3(RAG Core)入面提到嘅 component** — pipeline step new addition between Context Expander + CRAG
2. ✅ **改 storage layout 嘅 retrieval-time usage**(`section_path` field semantic promotion — from「retrievable metadata」to「retrieval-time aggregation key」)
3. ⚠️ **Soft trigger** — multi-KB architecture invariant 維持(`doc_id` + `section_path` scoping per ADR-0018 + ADR-0020 precedent)

→ ADR-0037 必須 Accepted 先 implement(per CLAUDE.md §10 R5)。

---

## Decision

### 1. 加 Parent-Document Retrieval step 入 query pipeline

**架構位置**(per architecture.md §3.1 + ADR-0020 precedent):

```
[Cohere Rerank → top 5]
       ↓
[Context Expander]                              ← ADR-0020(unchanged)
       ↓
[Parent-Document Retriever]                     ← NEW per ADR-0037
       ↓
[CRAG Confidence Judge]
       ↓
[GPT-5.5 Synthesis with Citation]
```

**Decision rationale**:
- **After Context Expander**:siblings aggregation 係 prev/next ±1 嘅 superset;sequencing matters less if both flags on(see §6.1 Q6 below for interaction policy)
- **Before CRAG**:CRAG 嘅 grade 應對 **expanded context**(parent section)— 而 NOT raw top-5;parent-doc 提升 context coverage 後 CRAG 嘅 confidence judge 先 meaningful

### 2. Section-path based aggregation strategy

**Core algorithm**(per `backend/generation/parent_doc_retriever.py` — NEW module):

```python
async def aggregate_parent_sections(
    reranked_chunks: list[RetrievedChunk] | list[ExpandedChunk],
    kb_id: str,
    searcher: HybridSearcher,
    *,
    section_depth_offset: int = 1,        # parent = section_path[:-1]
    parent_doc_top_k: int = 1,            # apply to top-1 reranked chunk only
    max_tokens_per_parent: int = 4000,    # token budget cap
) -> tuple[list[ParentSectionChunk], ParentDocStats]:
    # 1. Pick top-K cited chunks (default K=1) — the highest-confidence anchor(s)
    # 2. For each anchor: compute parent_section_path = anchor.section_path[:-section_depth_offset]
    # 3. Deduplicate parent_section_paths (siblings share parent)
    # 4. Batch fetch all chunks with matching (kb_id, doc_id, section_path startswith parent_section_path)
    #    via Azure AI Search OData filter (single batched call per unique parent)
    # 5. Order siblings by chunk_index ASC (preserves document narrative order)
    # 6. Concat sibling chunk_text into parent_section_text up to max_tokens_per_parent budget
    # 7. Return ParentSectionChunk list (duck-typed RetrievedChunk-compatible for prompt_builder)
```

**Key design choices**:

#### 2.1 Anchor selection(`parent_doc_top_k`)

**Default**:`parent_doc_top_k=1`(apply parent-doc to **top-1 highest-confidence** reranked chunk only)

**Rationale**:
- Top-1 reranked chunk = strongest signal of「query 真正 hit 邊個 section」
- 加多 anchors = 增加 off-topic parent sections leak(per F1 evidence:Q-W25-I07 top-5 已有 §3.1 chunk #8 = topically off — 若用 top-5 anchor parent-doc 就會 aggregate §3 整個 section 入 context = 反效果)
- Setting allows `parent_doc_top_k=2/3` for queries needing multi-section coverage(eg「compare X and Y」)— W26 F2 measurement 可 sweep

**Trade-off**:
- ✅ Conservative — minimize off-topic leak
- ⚠️ Loses cross-section breadth for multi-topic queries(measurable via F2 RAGAs `context_recall` for multi-section eval queries — likely needs separate Setting probe)

#### 2.2 Parent depth(`section_depth_offset`)

**Default**:`section_depth_offset=1`(parent = `section_path[:-1]` — drop last level)

**Example**(per architecture.md §3.5 chunker section_path output):

| Anchor chunk `section_path` | `section_depth_offset` | Parent section path | Siblings retrieved |
|---|---|---|---|
| `["Doc", "§8: Integration Scenarios", "Scenario A"]` | 1 | `["Doc", "§8: Integration Scenarios"]` | All 5 scenarios A-E |
| `["Doc", "§8: Integration Scenarios", "Scenario A"]` | 2 | `["Doc"]` | Entire doc(too broad) |
| `["Doc", "§3.1: Architecture"]` | 1 | `["Doc"]` | Entire doc(2-level chunks fall through) |

**Edge case**:若 anchor `section_path` 唔夠深(`len < section_depth_offset + 1`)→ fallback to doc-level(filter by `doc_id` only;subject to `max_tokens_per_parent` cap)

#### 2.3 Token budget(`max_tokens_per_parent`)

**Default**:`max_tokens_per_parent=4000`(approximate per chunk avg 250-300 tokens × ~15 sibling chunks)

**Rationale**:
- GPT-5.5 context window 大(128K input)但 **latency + cost ∝ tokens**;ADR-0034 P95<5s hard cap precedent
- Section that exceeds budget = truncate by chunk_index order(preserve narrative start;tail-drop)
- 4000 tokens ≈ §8 enumeration parent(~15 chunks)— covers Q-W25-I07 use case

**Trade-off**:
- ✅ Bounded latency + cost
- ⚠️ Very long sections lose tail content(measurable via F2 RAGAs — if `faithfulness` drops on truncated tails,raise budget)

#### 2.4 Citation invariant preservation(per ADR-0020 precedent)

- `ParentSectionChunk` duck-typed compatible with `RetrievedChunk` + `ExpandedChunk`:
  - `score` = anchor chunk's rerank score(unchanged)
  - `fields` = anchor chunk's fields,with NEW `parent_section_text` key holding aggregated parent text
- `prompt_builder.build_prompt()` dispatch chain:`parent_section_text` > `expanded_text` > `chunk_text`(fallback chain)
- **Citation rendering uses original anchor chunk_id + chunk_text**(unchanged — Citation card display 唔受影響)
- LLM sees parent section context,but citations reference original anchor chunks
- Per architecture.md §3.5 Citation contract — `Citation.chunk_text = original_chunk.chunk_text`,preserved

### 3. Settings(`backend/storage/settings.py`)

NEW Settings(default values pending Chris approval at AskUserQuestion):

```python
# Parent-Document Retrieval per ADR-0037 W26 F2
enable_parent_doc_retrieval: bool = False              # default OFF — W26 F2 measurement experiment
parent_doc_section_depth_offset: int = 1               # parent = section_path[:-1]
parent_doc_top_k: int = 1                              # apply to top-1 reranked chunk
parent_doc_max_tokens_per_parent: int = 4000           # truncate budget per parent section
parent_doc_max_chunks_per_parent: int = 50             # hard cap on siblings fetched(防 pathological doc)
parent_doc_fallback_to_doc_on_shallow: bool = True     # shallow section_path → doc-level fallback
```

**Feature-flag default-off**(per ADR-0034 precedent + Chris W26 plan §8 Q5 lock「W26 = measurement experiment only,NOT default flip」):

- W26 F2 = flip via env var override OR test harness 度 measurement signal
- 若 measurable improvement → 後續 NEW Change/Phase 決定 default flip(separate scope)
- 若 no improvement → close W26 with rationale,leave flag default-off as opt-in capability

### 4. Pipeline integration locus

**File touch list**(complete enumeration):

| File | Change | Reason |
|---|---|---|
| `backend/generation/parent_doc_retriever.py` | NEW | Core aggregation module(~200-250 lines) |
| `backend/generation/prompt_builder.py` | Modified | Dispatch chain `parent_section_text > expanded_text > chunk_text` |
| `backend/generation/crag.py` | Modified | Wire parent-doc step between Context Expander + CRAG grade(若 flag on) |
| `backend/api/routes/query.py` | Modified | Happy path `/query` + `/query/stream` wire parent-doc step(若 flag on);2 sites mirror ADR-0020 precedent |
| `backend/retrieval/hybrid.py` | Modified | NEW method `fetch_chunks_by_section_path()` — OData filter `kb_id + doc_id + section_path` collection match |
| `backend/storage/settings.py` | Modified | 6 NEW Settings(see §3 above) |
| `backend/observability/observe.py` | Modified | NEW stage name `generation.parent_doc_retrieval` for Langfuse trace(per ADR-0020 precedent;V6 Debug View 9→10 stages OR fold under Context Expander)|
| `backend/tests/test_parent_doc_retriever.py` | NEW | Unit tests ~15 cases(happy path / dedupe / depth fallback / token truncation / cross-doc boundary / empty / lookup miss / network error graceful / interaction with Context Expander) |

**No schema change**:`section_path` already indexed `Collection(Edm.String)` filterable + facetable per architecture.md §3.6 line 364。

### 5. Azure Search OData filter syntax

**Filter clause for parent section retrieval**:

```python
# Per anchor chunk:
parent_path = anchor.section_path[:-section_depth_offset]
# OData filter (Azure Search Collection field equality match per all elements):
filter_parts = [
    f"kb_id eq '{kb_id}'",
    f"doc_id eq '{anchor.doc_id}'",
    f"enabled eq true",  # respect W25 ADR-0035 baseline (low_value still post-filtered client-side)
]
# For section_path: use all() to assert each element in collection
for i, segment in enumerate(parent_path):
    filter_parts.append(f"section_path/any(s: s eq '{escape_odata(segment)}')")
filter_clause = " and ".join(filter_parts)
```

**OData escaping**:`escape_odata()` doubles single quotes per Azure Search OData spec(eg `Scenario A's intro` → `Scenario A''s intro`)

**Alternative considered**(rejected):use `search.in(section_path, '...')` — Azure Search `search.in` does NOT work for `Collection(Edm.String)` field elementwise check;`any()` operator is the correct primitive。

### 6. Interaction policy

#### 6.1 Q6 — Coexist with Context Expander(ADR-0020)?

**Decision**:**Both run when both flags on**;parent-doc consumes Context Expander output(`list[ExpandedChunk]` → `list[ParentSectionChunk]`)

**Rationale**:
- Context Expander = prev/next ±1 chunk(narrow local window;non-section boundary aware)
- Parent-doc = section-bounded aggregation(broader,topically coherent)
- 兩者 information surface 唔同 — both useful in principle
- **Composition**:Context Expander 先跑(per existing pipeline,wraps top-5 chunks with prev/next),Parent-doc retriever 再 pick anchor(top-1 by default)+ aggregate parent section
- Parent section already contains anchor's prev/next siblings(by construction — section spans multiple chunks)→ Context Expander's prev/next 對 anchor chunk **functionally redundant** when parent-doc on
- But for top-2..top-5 chunks(NOT anchors)— Context Expander's prev/next remains useful(parent-doc only expands anchors)
- **Net result**:parent-doc complements not replaces Context Expander;prompt_builder dispatch chain handles fallback

**Alternative considered**(rejected):mode-switch — `enable_parent_doc_retrieval=True` 時 disable Context Expander。Rejected because top-2..top-5 lose prev/next benefit。

#### 6.2 Q7 — Interaction with CRAG L2 confidence judge

**Decision**:CRAG grade applies to **parent-section-expanded context**(not raw top-5)

**Rationale**:
- CRAG L2 threshold 0.70(per W4-W5 empirical lock)was tuned on raw top-5 + Context Expander prev/next context
- Parent-doc 提升 context coverage 後,CRAG confidence 應該 **upward shift**(更 confident on enumeration queries)
- **No CRAG threshold change in W26**(per Chris W26 plan scope — out of scope)
- F2 measurement should observe:`crag_triggered` rate drop(more queries pass first grade);若 not observed → 需 W27+ NEW Change re-tune

**Edge case**:if parent section truncated(`max_tokens_per_parent` cap)→ CRAG may falsely upgrade confidence。Mitigation:include `parent_doc_truncated: bool` flag in `ParentSectionChunk.fields` → CRAG can deweight truncated context(deferred — W27+ if measurable issue)。

#### 6.3 Q8 — Interaction with citation_image_neighbors(CH-003 attach_neighbour_images)

**Decision**:**unchanged**(parent-doc operates on chunk_text aggregation;image attach unaffected)

**Rationale**:
- `citation_image_neighbors` runs **post-synthesis citation extract**(per W25 CH-003 wiring via `stream_composer.citation_post_process`)
- Cited chunks(determined by LLM emitting `[chunk-...]` tokens)still reference original anchor `chunk_id` — citation_image_neighbors continues to attach images by anchor's `chunk_index ±3` window
- No interaction loop;orthogonal layers

### 7. Observability

NEW Langfuse trace stage `generation.parent_doc_retrieval`(per ADR-0020 emit pattern):

```python
emit_stage_metadata(
    "generation.parent_doc_retrieval",
    duration_ms=batch_fetch_latency_ms,
    requested_anchors=len(anchor_chunks),
    parents_fetched=len(unique_parent_sections),
    siblings_aggregated=sum(len(p.siblings) for p in parents),
    truncated_count=sum(1 for p in parents if p.truncated),
    skipped_shallow_count=skipped_shallow_count,
)
```

**V6 Debug View update**(`frontend/app/debug/[traceId]/page.tsx` per ADR-0020 9-stage scaffold):

- **Option A**(recommended):**Insert NEW「Parent-Document Retriever」stage** between Context Expander + CRAG → 9→10 stage(spec §5.7 alignment update via subsequent doc-update — minor inline-tagged amendment)
- **Option B**:Fold parent-doc metadata under existing Context Expander stage(simpler;spec stays 9-stage but stage semantic broadens to「Context expansion(prev/next + parent-section)」)
- **Decision**:**Option A**(explicit transparency for new step);frontend touch ~30 LOC(observation-name prefix in `STAGE_DEFS` + key/value render in stage card)

**Tradeoff**:V6 Playwright pixel-diff baseline re-capture trigger(per ADR-0020 precedent W16 F4 carry-over);user-deferred per W22-W25 pattern

---

## Alternatives Considered

### Option B — Query intent routing(enumeration detector → dynamic top_k + relaxed cutoff)

**Action**:
- NEW classifier `backend/pipeline/query_intent.py`:detect enumeration intent via heuristic(keywords `all` / `list` / `every` / `each` 全部 / 列出)or small LLM call
- Enumeration intent → `top_k_rerank=20`(↑ from 5)+ skip rerank threshold(if any)
- Factoid intent → existing pipeline unchanged

**Pros**:
- Smaller code surface(no new aggregation module — reuse existing top-K wider retrieval)
- Preserves factoid query latency(only enumeration queries pay the cost)

**Cons**:
- ❌ **Cohere top-N already exhibits high-confidence wrong chunks**(per F1 evidence — Q-W25-I02 min 0.88 > Q-W25-I07 PASSED partial min 0.90)→ widening top_k 加多 noise,**唔解** root cause(architectural mismatch,not top-K narrowness)
- Classifier accuracy risk — query intent detection 自身可 fail / cost LLM round-trip
- LLM input grows linearly with top_k → token cost ↑ without targeted aggregation
- **Doesn't address chunk #8(§3.1)leak** — wider top_k = more off-topic chunks
- Brief §3 方向 F 標 🟡 H1 — same constraint level as Option A,not simpler

**Rejected because**:F1 empirical evidence shows wider top_k won't help — Cohere ranks wrong chunks high;parent-doc directly aggregates correct logical scope。Intent routing is a complementary concept(可作 W27+ optimization)but NOT a substitute for section-level retrieval。

### Option C — Re-chunk with parent_chunk_id metadata(Dify Parent-child mode at ingestion)

**Action**:
- Modify `backend/ingestion/chunker/layout_aware.py` to also emit「parent chunk」records(coarse chunks at section level)alongside fine chunks
- Index schema add `parent_chunk_id` field
- Retrieval-time:hit fine chunk → fetch parent chunk's combined text

**Pros**:
- Dify's mature pattern — proven at scale
- Single-fetch at retrieval-time(parent chunk pre-aggregated)
- Lower retrieval latency than runtime aggregation

**Cons**:
- ❌ **Requires re-chunk + re-embed all existing KBs**(structurally invasive — touches C01 + C03)
- ❌ Index schema change(architecture.md §3.6 amendment;new `parent_chunk_id` field)— H1 trigger more severe
- ❌ Doubles storage(每 doc 都有 fine + parent records)
- ❌ Less flexible — parent boundaries baked at ingestion time;cannot retune `section_depth_offset` without re-ingestion
- Beta launch implications:already-ingested `sample-document-with-image-1` + production future KBs all require re-ingest

**Rejected because**:Karpathy §1.2 simplicity-first — runtime aggregation reuses existing index schema + section_path metadata(zero re-ingestion cost);flexibility advantage(retune `section_depth_offset` via Settings without re-chunk)substantial。Dify pattern useful but EKP 嘅 layout-aware section_path already provides equivalent metadata without separate parent records。

### Option D — GraphRAG / community detection(Microsoft GraphRAG global aggregation)

**Action**:
- Build knowledge graph during ingestion(entity + relation extraction)
- Query-time:LLM identifies relevant communities → aggregate community summaries
- Replaces or supplements chunk-level retrieval entirely

**Pros**:
- Best-in-class for global aggregation queries
- Naturally handles「show me all」 + 「summarize」 + cross-document synthesis

**Cons**:
- ❌ **Tier 2 territory explicitly**(per `architecture.md §11` GraphRAG / Knowledge Graph row)
- ❌ NEW dependencies(graph DB / NetworkX + community detection algorithms)→ H2 trigger
- ❌ Ingestion pipeline rewrite(entity extraction LLM calls × millions of chunks → cost + latency explosion)
- ❌ EKP scale(Drive corpus ~thousands of docs)doesn't justify graph cost

**Rejected because**:CLAUDE.md §5.4 H4 hard boundary — Tier 1 唔做 GraphRAG / multi-agent。Parent-doc retrieval = simpler architectural escalation 直接 fits Tier 1。GraphRAG 屬 post-Tier-1 production launch governance question(per OQ-Q12 Tier 2 owner)。

### Option E — Multi-query expansion further hardening(rely on ADR-0034 RAG-Fusion alone)

**Action**:
- Skip parent-doc retrieval scope
- Enhance ADR-0034 query expansion:generate 5-10 reformulations(currently 3)to widen retrieval surface
- Trust RRF fusion + Cohere rerank to handle aggregation

**Pros**:
- Reuses existing framework(zero new code structure)
- ADR-0034 already opt-in via flag — could just flip default to True

**Cons**:
- ❌ **W26 F1 ran on baseline + ADR-0034 default off** — query expansion未 measured against current failure mode;may not address it
- ❌ Even with expansion,each variant queries top-5 then RRF fuses — final context window still bounded by top-K post-fusion;**doesn't address single-section aggregation requirement**
- Brief §3 step 4 explicitly notes if step 2(query expansion)doesn't fully resolve enumeration → escalate parent-doc
- Adds reformulator LLM calls(latency budget pressure — ADR-0034 P95<5s hard cap)

**Rejected because**:W26 plan §1.2 explicitly orders Step 2 query expansion AFTER threshold(originally,now AFTER parent-doc per pivot)— **Step 2 屬 F3 measurement experiment downstream**,not substitute for parent-doc。Architectural mismatch root cause(per brief §1 「NOT EKP-unique」)not addressable purely via query-side。

### Option F — Manual section index(curated parent index outside main Azure Search)

**Action**:
- NEW Postgres `kb_sections` table(per ADR-0023 backing)— `kb_id`,`doc_id`,`section_path`,`section_summary_text`,`chunk_ids[]`
- Pre-compute section summaries during ingestion(LLM call per section)
- Retrieval-time:lookup section by anchor → return pre-baked summary

**Pros**:
- Lowest runtime latency(pre-computed)
- Section summary can be LLM-condensed → fits LLM input cleanly

**Cons**:
- ❌ Heavyweight ingestion pipeline addition(per-section LLM call × thousands of sections)
- ❌ NEW Postgres table + storage layout change(H1 trigger more severe than ADR-0037 runtime aggregation)
- ❌ Summaries stale if doc updated — needs re-ingestion cascade
- ❌ Lose chunk granularity(LLM sees summary,not original — citation precision drops;each section becomes opaque to citation)

**Rejected because**:violates citation contract(architecture.md §3.5 Citation contract — `Citation.chunk_text = original_chunk.chunk_text`)— LLM-summarized section text 唔可作 citation;loses verbatim grounding。Runtime aggregation preserves chunk-level citation invariant。

---

## Consequences

### Positive

- **Direct architectural fit for enumeration queries**:section_path-based aggregation 直接解 brief §1「enumeration query × top-K factoid retrieval mismatch」root cause
- **Zero schema change**:`section_path` already `Collection(Edm.String)` filterable indexed per architecture.md §3.6 — no re-ingest required
- **Layered with existing pipeline**:complements ADR-0020 Context Expander + ADR-0034 query expansion + ADR-0035 low_value soft-relax(non-conflicting layers)
- **Citation invariant preserved**:LLM sees parent section,Citation card displays original chunk(per ADR-0020 precedent)
- **Feature-flag default-off**:matches ADR-0034 precedent — W26 F2 measurement experiment,no production behavior change until default-flip decision
- **Tier 2 friendly**:parent-doc retrieval primitive extensible to query intent routing(Option B Tier 2 candidate)+ multi-section parent aggregation(W27+ candidate)
- **Settings-tunable**:`section_depth_offset` + `parent_doc_top_k` + `max_tokens_per_parent` 全部 measurement-tunable without re-deploy

### Negative

- **NEW code = NEW risk surface**:~250 LOC core module + ~15 test cases + integration points across 8 files
- **Per-query latency**:1 additional Azure Search batched call(~50-100ms per F2 measurement;within ADR-0034 P95<5s budget)
- **LLM input token growth**:up to `max_tokens_per_parent=4000`(default)added per query when flag on → ~30-40% input token growth typical for enumeration queries → ~$0.001-0.002 incremental cost per query(GPT-5.5 input rate)
- **V6 Debug View 9→10 stage** requires frontend update + Playwright pixel-diff baseline re-capture trigger(carry-over with ADR-0020 precedent)
- **Setting tuning iteration**:`section_depth_offset` + `parent_doc_top_k` defaults likely need post-F2 RAGAs measurement adjust;multi-iteration possible(per W26 plan R3 risk — capped at 3 iterations)
- **CRAG threshold may need retune**(W27+ if measured)— parent-doc may upward-shift confidence judge;current 0.70 threshold tuned pre-parent-doc

### Neutral

- **No vendor change**(H2 unaffected)— uses existing Cohere + Azure Search + GPT-5.5
- **No multi-tenancy implication**(kb_id scoping per ADR-0018 preserved)
- **No security implication**(retrieval-time aggregation operates on already-indexed authorized chunks)
- **Component impact**:C04 Retrieval Engine + C05 Generation(adjacent)— design notes refresh trigger但 deferable per ADR-0020 design-note refresh pattern
- **Backward compat**:flag default-off → existing pipeline behavior unchanged;rollback = flip flag off(no schema rollback)

---

## References

### Source documents
- **Trigger memo**:`docs/09-analysis/rag_retrieval_quality_investigation_20260525.md`(user-authored investigation brief 2026-05-25 — §3 方向 E 「Parent-document / section-level retrieval」+ §5 academic refs + §6 step 4 escalation path)
- **W26 F1 empirical evidence**:
  - `docs/01-planning/W26-eval-driven-retrieval-tuning/baseline-metrics-W26-D1.md`(RAGAs 13-query baseline — recall-dominant)
  - `docs/01-planning/W26-eval-driven-retrieval-tuning/threshold-probe-W26-D1.json`(25 Cohere v4.0-pro scores — P25=0.83 / min=0.67)
  - `backend/scripts/w26_threshold_probe.py`(probe script — Python direct retrieve.engine.retrieve() bypassing /eval/run aggregated schema)
- **W26 plan**:`docs/01-planning/W26-eval-driven-retrieval-tuning/plan.md` §7 Changelog 2026-05-25 D1 pivot entry

### Spec references(architecture.md v6)
- **§3.1 Query Pipeline**(line 184-219)— pipeline diagram amendment locus(post-Context Expander insertion)
- **§3.5 ChunkRecord schema**(line 314-348)— `section_path: list[str]` semantic + chunker output example
- **§3.6 Azure AI Search Index Schema**(line 350-411)— `section_path` `Collection(Edm.String)` filterable + facetable proof of zero schema change
- **§5.7 V6 Debug View**(line 888-905)— 9-stage scaffold;ADR-0037 implementation may extend to 10-stage(Option A)

### Cross-ref ADRs
- **ADR-0004**(Layout-aware chunking)— section_path origin upstream
- **ADR-0005**(Multi-KB architecture Day 1)— kb_id scoping invariant preserved
- **ADR-0007**(L2 CRAG)— parent-doc context fed into CRAG grade(no threshold change W26 scope)
- **ADR-0018**(Multi-KB kb_id propagation)— `fetch_chunks_by_section_path` per-KB scoping symmetry
- **ADR-0020**(Context Expander)— **structural sibling**:both are post-rerank chunk-aggregation modules;ADR-0037 reuses pattern(duck-typed Chunk + batch fetch + edge case handling + observability stage + V6 stage)
- **ADR-0034**(Query expansion + RAG-Fusion)— feature-flag default-off precedent + framework cohabitation
- **ADR-0035**(Low-value soft-relax + W25.5 BUG-025 symmetric deboost)— `enabled eq true` filter clause baseline preserved;parent-doc respects same baseline

### Behavioral baseline
- **Karpathy §1.1 think-before-coding**:F1 empirical refutation evidence surfaced upfront before code(per BUG-025 postmortem PC3 ADR assumption-language review preventive control — brief 0.3 magic number rejected empirically;parent-doc grounded in section_path metadata that already exists)
- **Karpathy §1.2 simplicity-first**:runtime aggregation chosen over Option C re-chunk(zero re-ingestion);Option D GraphRAG rejected per H4
- **Karpathy §1.3 surgical**:8 file touch list bounded;no spillover into ingestion / index / frontend chat surface(only V6 Debug View 9→10 stage minor update)
- **Karpathy §1.4 goal-driven**:F2 acceptance = RAGAs `context_recall` improvement on Q-W25-I07 + 4 other failed queries(5/13 → expected 2-3/13 post-parent-doc per industry precedent for enumeration queries)

### Industry precedent(per brief §5)
- LangChain `ParentDocumentRetriever`(small-to-big retrieval pattern)
- LlamaIndex `AutoMergingRetriever`(siblings auto-merge to common parent)
- Dify Parent-child chunking mode(re-chunk variant — rejected here per Option C)
- Microsoft RAG patterns docs — query routing + parent context guidance

### Postmortem preventive controls(BUG-025)
- **PC1 ≥ 5-query manual user-test taxonomy**:W26 F2 covers Q-W25-I07 + Q-W25-I01 PASSED control + Q-W25-I02 + Q-W25-I03 + Q-W25-T04 = 5 priority queries minimum + 8 additional eval-set-v0 queries
- **PC3 ADR assumption-language review**:F1 empirically refuted brief §3 方向 A 0.3 magic;ADR-0037 grounded in section_path index field existing + F1 distribution data,not「common-sense」magic
- **PC4 pre-phase regression baseline capture**:F1 baseline-metrics-W26-D1.md serves as regression baseline for F2 RAGAs delta measurement

---

## Implementation Deliverables(W26 F2 — pending ADR Accepted status)

> **Status**:**Proposed** as of 2026-05-25 D1。**Implementation deferred to W26 F2 active flip post Chris AskUserQuestion approval**(rolling per CLAUDE.md §10 R1 + R5)。Below = the implementation contract this ADR commits to;F2 plan revision will source acceptance criteria from this list。

### Code changes(backend Parent-Document Retriever)

- [ ] `backend/generation/parent_doc_retriever.py` — NEW(~200-250 lines)
  - `ParentSectionChunk` dataclass(duck-typed `RetrievedChunk` / `ExpandedChunk` compatible)
  - `async def aggregate_parent_sections(reranked_chunks, kb_id, searcher, *, ...) -> tuple[list[ParentSectionChunk], ParentDocStats]`
  - Anchor selection per `parent_doc_top_k`
  - Section path deduplication
  - Batch fetch via `HybridSearcher.fetch_chunks_by_section_path()`
  - Token budget truncation
  - Cross-doc boundary respect(`doc_id` filter)
  - Shallow section_path fallback to doc-level(`parent_doc_fallback_to_doc_on_shallow`)
- [ ] `backend/retrieval/hybrid.py` — NEW method `fetch_chunks_by_section_path(parent_path: list[str], doc_id: str, kb_id: str) -> list[HybridSearchHit]`
  - OData filter:`kb_id eq '...' and doc_id eq '...' and enabled eq true and section_path/any(s: s eq '<each segment>')` joined
  - OData escaping(double single quotes)
  - Order by `chunk_index ASC`
  - Hard cap `parent_doc_max_chunks_per_parent`
- [ ] `backend/generation/prompt_builder.py` — Dispatch chain extended:`parent_section_text > expanded_text > chunk_text`
- [ ] `backend/generation/crag.py` — Wire parent-doc step between Context Expander + CRAG grade(flag-gated)
- [ ] `backend/api/routes/query.py` — `/query` happy path + `/query/stream` 2 sites(per ADR-0020 precedent pattern)
- [ ] `backend/storage/settings.py` — 6 NEW Settings(per §3 Settings list above)

### Observability

- [ ] `backend/observability/observe.py` — NEW stage name `generation.parent_doc_retrieval`
- [ ] `frontend/app/debug/[traceId]/page.tsx` — V6 Debug View 9→10 stages(Option A explicit insert)+ per-stage data display

### Tests

- [ ] `backend/tests/test_parent_doc_retriever.py` — NEW ~15 unit cases
  - Happy path:1 anchor → 1 parent → 5 siblings aggregated
  - Multi-anchor dedupe:top-2 anchors share parent → fetch once
  - Section depth fallback:shallow `section_path`(len=1)→ doc-level filter
  - Token budget truncation:parent section > 4000 tokens → tail-drop preserving narrative order
  - Cross-doc boundary:parent section bounded to anchor's `doc_id`
  - Empty input:`reranked_chunks=[]` → empty result + empty stats
  - Lookup miss:Azure Search returns 0 hits → graceful empty parent
  - Network error:graceful degradation(per ADR-0020 precedent — log + return without parent expansion)
  - Feature flag off:`enable_parent_doc_retrieval=False` → no-op pass-through
  - Interaction with Context Expander:anchor's prev/next already in parent section → no double-expand
  - Citation invariant:`Citation.chunk_text` unchanged(verified via `prompt_builder` dispatch chain test)
- [ ] `backend/tests/test_hybrid_searcher.py` — extend with `fetch_chunks_by_section_path` cases
- [ ] mypy strict clean on touched code + ruff clean

### RAGAs eval(W26 F2 F2→F3 gate evidence)

- [ ] Re-run RAGAs on same 13-query supplement(W26 F1 baseline cohort)— with `enable_parent_doc_retrieval=True` env override
- [ ] Output:`docs/01-planning/W26-eval-driven-retrieval-tuning/parent-doc-metrics-W26-D{N}.md`
  - 13-query metrics delta(faithfulness / answer_relevancy / context_precision / context_recall)
  - Per-query chunk_id list(diagnostic — verify parent siblings appear)
  - Aggregated delta vs F1 baseline
- [ ] F2 → F3 gate AskUserQuestion(Chris pick:proceed F3 query expansion / W26 closeout PASS / iterate Setting values)

### Documentation

- [ ] `docs/architecture.md` §3.1 pipeline diagram amendment(inline-tagged per §3.4/§3.7 precedent;doc version held — ADR is record)
- [ ] `docs/architecture.md` §5.7 V6 Debug View 9→10 stage amendment(if Option A picked)
- [ ] `docs/02-architecture/components/C04.md` + `C05.md` design notes refresh(deferable per ADR-0020 P1 batch precedent)
- [ ] `docs/02-architecture/COMPONENT_CATALOG.md` C04 + C05 status note

---

## Decision Log(Chris AskUserQuestion picks 2026-05-25 D1 cont)

### Critical 4 Qs — AskUserQuestion approved

| Q | Question | Chris pick | Note |
|---|---|---|---|
| **Q4** | W26 default flag state | **Default OFF — `enable_parent_doc_retrieval=False`** (Recommended) | Measurement experiment via env override;matches ADR-0034 precedent + W26 plan §8 Q5 lock;post-F2 measurable improvement triggers NEW Change for default flip(separate scope) |
| **Q1** | `parent_doc_top_k` initial value | **1 — top-1 reranked anchor only** (Recommended) | Conservative — minimize off-topic leak per F1 evidence Q-W25-I07 top-5 已含 §3.1 chunk #8 topically off;Setting allows W27+ sweep to 2/3 if multi-section coverage needed |
| **Q2** | `section_depth_offset` initial value | **1 — parent = `section_path[:-1]`** (Recommended) | Drop last level;Q-W25-I07 use case 直接 covers(anchor in `[..., §8, Scenario A]` → parent = `[..., §8]` aggregates 5 scenarios);adaptive deferred W27+ |
| **Q6** | Coexistence with ADR-0020 Context Expander | **Both on — parent-doc consumes Context Expander output** (Recommended) | Complement not replace;top-2..top-5 lose prev/next benefit if mode-switch;duck-typed dispatch chain handles fallback |

### Q3 / Q5 / Q7 / Q8 — Proposed defaults batch-locked

| Q | Decision | Rationale |
|---|---|---|
| **Q3** | `max_tokens_per_parent = 4000` | Approximate ~15 sibling chunks;within ADR-0034 P95<5s latency budget;tail-drop truncation by chunk_index ASC preserves narrative start;Setting allows W27+ tune if `faithfulness` regresses on truncated tails |
| **Q5** | V6 Debug View Option A — explicit 10-stage insert | Per ADR-0020 9-stage scaffold precedent;explicit transparency for new step;`architecture.md §5.7` minor inline-tagged amendment trigger;V6 Playwright pixel-diff baseline re-capture per ADR-0020 W16 F4 carry-over pattern(user-deferred) |
| **Q7** | Anchor scope = top-1(same as Q1 — locked together) | Q1 + Q7 同問同 answer — `parent_doc_top_k=1` 即 top-1 anchor only |
| **Q8** | No CRAG threshold retune in W26 | W26 scope-locked(per Chris W26 plan §1.3 out of scope);observe `crag_triggered` shift in F2 RAGAs measurement → W27+ NEW Change if measurable issue;parent-doc may upward-shift confidence judge but threshold retune ≠ this ADR's scope |

### Implementation gate(post-Accepted)

W26 F2 plan rewrite proceeds based on:
- ADR-0037 Implementation Deliverables list(§ above)is the F2 acceptance contract
- 6 NEW Settings default values locked per Decision Log above
- W26 plan §7 Plan Changelog 2026-05-25 D1 cont entry will document ADR-0037 Accepted + F2 deliverable scope rewrite

---

## Amendment 2026-05-26 W28 F4 — Settings default flip per Setting sweep best combo

**Trigger**:W28-parent-doc-setting-sweep phase(per ADR-0038 §Decision #4 W28+ candidate (b) HIGHEST priority)— Sequential one-variable-at-a-time sweep 3 Steps × 6 RAGAs runs(F1 max_tokens 4000/2000/1500 + F2 top_k 1/2/3 + F3 dispatch replace/append cross-check at best combo)on `eval-set-v0-w25-supplement.yaml` 13 queries cohort。

### W28 Best Combo Empirical Evidence

**Run 3.A (dispatch_mode=replace + top_k=2 + max_tokens=2000)** = W28 final best:
- **G1 faithfulness 0.9812** ✅ PASS within F1 baseline ±2pp tolerance [0.9651, 1.0](closer to F1 than Run 2.A append 0.9786)
- **G2 correctness 0.7577** ✅ **PASS + EXCEEDS F1 baseline +1.61pp**(唯一 sweep run 達 above-baseline correctness)
- G3 Q-W25-I07 context_recall=0.40 ⚠️ MISS — borderline judge variance per 8-run cross-config flip(3 PASS / 5 FAIL across W26+W27+W28 with answer_rel in 0.60-0.70 range)treat as noise
- **G4 Q-W25-I01 control FULL PASS** ✅(out of failed_queries list — beat Run 2.A append's context_recall=0 single-metric fail)
- **G5 latency 1249ms** ✅ PASS < 1500ms ideal threshold(~57% reduction vs W27 baseline 2897ms / +24% vs F1 1001ms)

**Versus W27 marginal MISS context**:
- W27 G1 faith MISS 0.6pp → W28 G1 MISS 0.4pp(closer)
- W27 G4 control MISS 0.01pp → W28 G4 FULL PASS
- W27 G2 correctness PASS but BELOW F1 → W28 G2 PASS AND EXCEEDS F1

### Decision

`backend/storage/settings.py` default values amended per W28 Step 1+2 sweep best combo:

| Field | Original W26 default | **W28 amendment default** | Rationale |
|---|---|---|---|
| `parent_doc_max_tokens_per_parent` | 4000 | **2000** | W28 Step 1 sweep evidence — max_tokens=2000 提升 faithfulness vs 4000 + reduce attention dilution per D1.35 H2 |
| `parent_doc_top_k` | 1 | **2** | W28 Step 2 sweep evidence — top_k=2 sweet spot between conservative top-1(coverage 不足)同 aggressive top-3(off-topic leak catastrophic — Q-W25-I01 0.00 + correctness MISS 5.95pp);ADR-0037 §2.1 trade-off empirically verified |
| `parent_doc_dispatch_mode` | "replace"(per W27 ADR-0038 default preserve) | **"replace" 維持不變** | per Karpathy §1.3 surgical — W26+ADR-0038 default preserve;Run 3.A (replace) 達 best combo G1+G2+G4+G5 PASS + G2 超 F1 baseline;append (Run 2.A) 同樣 PASS但 G2 below F1 + G4 single-metric fail |
| `enable_parent_doc_retrieval` | False(measurement experiment) | **False 維持不變** | per Q4 measurement-experiment-fail-policy — G3 Q-W25-I07 marginal MISS 仍 not full PASS = 唔達 production default flip threshold;W28 best combo via env override OR per-KB opt-in remains preferred path |

### W26→W27→W28 Hypothesis Re-evaluation Synthesis

**D1.35 H4 dispatch hypothesis revised**:
- **Original W27 H4**:dispatch=replace catastrophic per W26 F2 G empirical → append mode 修復 by 2-segment LLM input citation invariant preservation
- **W28 revised understanding**:**W26 F2 G catastrophic 根本原因 = wrong Settings combination(top_k=1 + max_tokens=4000)+ dispatch=replace top-priority-wins**。At correct Settings(top_k=2 + max_tokens=2000),dispatch=replace 不單 不 catastrophic,反而 達到 W28 best combo across G1+G2+G4+G5。Settings effect 比 dispatch effect 更 dominant;append + replace at best combo 都 acceptable but replace 略勝 G2 + G4
- **ADR-0038 「Settings default preserve replace」decision VALIDATED by W28 evidence**

**Q-W25-I07 G3 marginal MISS treated as noise**:
- 8 runs cross-config(W26 + W27 + W28 6 runs):3 PASS / 5 FAIL with answer_rel + context_recall + faith all 喺 0.40-0.70 range fluctuation
- Judge LLM 非確定性 dominant signal,settings + dispatch effect 次要
- 唔 drive amendment default flip decision

### Implementation

- `backend/storage/settings.py` line 199-216 默認值 + comments amended W28 F4 commit
- 39/39 existing tests(11 dispatch + 14 synthesizer + 14 parent_doc_retriever)preserved without modification — tests 用 explicit parameter passing,Settings default change 不影響 test behavior
- Backend pytest 1060 regression check — W28 F4 commit landed without breaking change

### Cross-references

- W28 plan + 4 step analysis reports + 6 raw eval JSONs(`docs/01-planning/W28-parent-doc-setting-sweep/`)
- W28 final best combo Run 3.A:`docs/01-planning/W28-parent-doc-setting-sweep/step3-dispatch-cross-check-W28-D3.md` + raw JSON
- ADR-0038 reaffirm note added W28 F4
- ADR-0017 5-amendment precedent pattern applied — same decision family rationale

---

**End of ADR-0037**。
