# ADR-0020: Context Expander step Tier 1 deliver(reaffirm architecture.md §3.1 + V6 9-stage spec via code catch-up)

**Date**: 2026-05-09
**Status**: Accepted
**Approver**: Chris(技術 Lead)
**Trigger**: `docs/02-architecture/audit-W15-d5-vs-spec.md` Major Drift #3 + §CC-3 — `prev_chunk_id` / `next_chunk_id` populated 喺 ChunkRecord 但 retrieval/generation code 不 consume;internal-spec inconsistency between architecture.md §3.1(列 Context Expander step)+ C05-generation.md §1 diagram(冇 Context Expander)+ V6 Debug View `/debug/[traceId]` 6-stage scaffold(spec §5.7 9 stages)

---

## Context

### Spec promise(authoritative,frozen v6)

**architecture.md §3.1 Query Pipeline**(lines 184-219,line 210-211 explicit):
```
[Query Preprocessor]
       ↓
[Hybrid Retrieval BM25+vector RRF top 50]
       ↓
[Cohere Rerank → top 5]
       ↓
[Context Expander] ← prev/next 相鄰 chunk        ← 列出
       ↓
[CRAG Confidence Judge]
       ↓
[GPT-5.5 Synthesis with Citation]
       ↓
[Final Response]
```

**architecture.md §5.7 V6 Debug View**(lines 888-905):
> Trace summary + vertical timeline + expandable stages — **9 stages**:Query Preprocessor / Query Rewriter / Hybrid Retrieval / Reranker / CRAG Confidence Judge / Re-retrieve / Context Expander / LLM Synthesis / Final Response

### Code reality(verified spot-check 2026-05-09 audit)

**Schema layer**(✅ aligned):
- `prev_chunk_id` + `next_chunk_id` populated 喺 `ChunkRecord`(`backend/ingestion/orchestrator.py:157-158`)
- Index store 兩個 fields(`backend/indexing/schema.json:16-17`)

**Consumption layer**(❌ broken):
- 冇 retrieval / generation code 讀返兩個 fields
- Top-5 reranked chunks 直接 passed 入 `prompt_builder.build_prompt()`,**冇 prev/next neighbor expansion**
- C05-generation.md §1 internal architecture diagram 都冇 list Context Expander step

**V6 Debug View**(`frontend/app/debug/[traceId]/page.tsx`):
- **6-stage** PipelineStageCollapsible scaffold:Query Preprocessor / Hybrid Retrieval / Reranker / CRAG Confidence Judge / LLM Synthesis / Final Response
- W15 D2 plan §F2.2 §7 changelog explicit log:"design ref §2.6 wireframe + plan F2.2 own enumeration agree on 6 stages... plan internal inconsistency between '9-stage' header + 6-enumerated → align with wireframe 6"
- **Wireframe + design-ref + plan changelog 三個 source align 6 stages**;spec §5.7 9 stages outlier

### Cross-cutting source matrix

呢個 drift cross-cuts **4 個 spec / code locations**:

| Source | Stage count | Position |
|---|---|---|
| architecture.md §3.1 pipeline diagram | **7 implicit + Context Expander = 7** | Spec frozen v6 列 step |
| architecture.md §5.7 V6 Debug View | **9 stages** | Spec frozen v6 explicit |
| components/C05-generation.md §1 internal diagram | **6 stages**(no Context Expander)| Component design note;`last_updated` stale per audit CC-4 |
| `frontend/app/debug/[traceId]/page.tsx` V6 implementation | **6 stages** | Code reality;W15 D2 plan changelog align |
| `backend/generation/` code paths | **No Context Expander module** | Code reality |

→ 4 個 source,2 種 count(6 vs 9 / 7);**spec §3.1 + §5.7 = side A(deliver step);C05 design note + frontend + backend code = side B(no step)**。需要選邊 align,呢個 ADR 確定 **side A(spec)wins,code + design note 跟住 catch up**。

### Quality impact assessment(Drive corpus context)

**Use case 例子**:user 問「點 troubleshoot D365 F&O Sales Order 過唔到 Posting?」

Hybrid retrieval 揀到 chunk #42:
> "Step 3: Click 'Confirm' button to post the sales order."

Context 上下相鄰:
- chunk #41(prev):「Before posting, ensure customer credit limit not exceeded...」(prerequisites)
- chunk #43(next):「If posting fails, check the inventory level for line items...」(troubleshooting)

**冇 Context Expander**:LLM 只見 chunk #42,答案只覆蓋 happy path
**有 Context Expander**:LLM 見 #41 + #42 + #43,答案完整覆蓋 prerequisites + steps + troubleshooting

**Tier 1 today**:Gate 1 PASS R@5=0.97 + Gate 2 PARTIAL PASS — current quality acceptable WITHOUT Context Expander。但 W16+ Beta cohort 嘅 D365 corpus(per W11 D2 cont memo)structurally complex — multi-step procedures + prerequisites + troubleshooting 散落 prev/next chunks。Context-dependent question 會 surface。

### prev/next chunk_id storage justification

Schema 已 store 兩個 fields(每 chunk record 加 ~20 bytes overhead × millions of chunks = non-trivial)。
- **Option A**:Context Expander consumes — storage 真正 justified
- **Option B**:Pure citation metadata(frontend display "see also" cross-refs)— storage 用例細,overhead 唔合理

---

## Decision

**1. 重申 architecture.md §3.1 Context Expander step + §5.7 V6 9-stage spec**(reaffirm spec — **NOT amend**)

**2. Code + V6 Debug View + C05 design note catch up to spec via Tier 1 deliver**:

### Implementation contract

#### A. Backend Context Expander module

- **File**:`backend/generation/context_expander.py`(estimated ~100 lines)
- **Logic**:
  ```python
  async def expand_context(
      reranked_chunks: list[Chunk],  # top-5 from Cohere rerank
      kb_id: str,                     # per ADR-0018 kb_id propagation
      searcher: HybridSearcher,       # injected for prev/next lookup
  ) -> list[ExpandedChunk]:
      # 1. Collect all prev/next chunk_ids from top-5
      # 2. Single batch Azure Search call: filter chunk_id in (...)
      # 3. Build prev/next lookup dict
      # 4. For each top-5 chunk: prepend prev text + append next text
      # 5. Skip expansion if prev/next chunk_id is None or cross-doc boundary
      # 6. Return ExpandedChunk dataclass with original + prev_context + next_context fields
  ```
- **ExpandedChunk dataclass**:
  ```python
  @dataclass
  class ExpandedChunk:
      original: Chunk             # the reranked chunk
      prev_context: str | None    # prev chunk text, None if first chunk or cross-doc
      next_context: str | None    # next chunk text, None if last chunk or cross-doc
      expanded_text: str           # combined: prev + original + next
  ```

#### B. CRAG flow integration

- Wire into `backend/generation/crag.py` between Cohere rerank + `prompt_builder.build_prompt()`:
  ```python
  reranked = await reranker.rerank(...)
  expanded = await context_expander.expand_context(reranked, kb_id, searcher)
  prompt = prompt_builder.build_prompt(query, expanded)  # passes ExpandedChunk list
  ```
- `prompt_builder.build_prompt()` signature update accept `ExpandedChunk` instead of raw `Chunk`
- Citation regex `[chunk-{cid}]` 仍 reference `original.chunk_id`(non-citation breakage)

#### C. V6 Debug View 9-stage scaffold expansion

- `frontend/app/debug/[traceId]/page.tsx` 由 6 stages → 9 stages,加 3 個 new PipelineStageCollapsible:
  - Query Rewriter(現 implicit in CRAG;explicit collapse stage)
  - Re-retrieve(CRAG correction loop;explicit collapse stage)
  - Context Expander(NEW step per this ADR;display top-5 + per-chunk prev/next preview + expansion stats)
- Backend `/debug/trace/{trace_id}` endpoint(W16 F5 stub closure cascade)return per-stage data 包括 Context Expander stats:
  - `expansion_count`(how many of top-5 had prev/next merged)
  - `boundary_skip_count`(prev/next null OR cross-doc)
  - `latency_ms`(batch fetch latency)
- Playwright pixel diff baseline re-capture trigger(W16 F4 user smoke first run scope — visual baseline regenerate after 9-stage expansion)

#### D. C05-generation.md §1 design note update

- `last_updated` bump to W15 D5 closeout(2026-05-09)
- §1 internal architecture diagram add Context Expander step
- §2 Outputs section 加 ExpandedChunk reference
- Cross-ref ADR-0020

#### E. ADR-0018 cross-ref

- Context Expander 用 ADR-0018 嘅 `kb_id` parameter:per-KB lookup of prev/next via dynamic `index_name = f"ekp-kb-{kb_id}-v1"`
- Implementation order:**ADR-0018 implementation MUST land before ADR-0020 implementation**(retrieval pipeline kb_id wiring 係 prerequisite)

### Implementation timing

- **Phase 3 of P0 batch**(W16+ active flip post Track A IT cred populate event)
- **Estimated 1.5 days**:
  - Backend Context Expander code + tests:~5 hours
  - CRAG flow integration:~2 hours
  - V6 Debug View 9-stage expansion(3 new collapsibles + per-stage data wiring):~3 hours
  - C05 design note update:~1 hour
  - Backend `/debug/trace/{trace_id}` Context Expander stats wiring:~1 hour(part of W16 F5 stub closure cascade)
- **Stack with ADR-0018 + ADR-0019** = total ~4.5 days cumulative Phase 3
- **Sequential dependency**:ADR-0018 implementation MUST land first(Context Expander 用 kb_id parameter)

---

## Alternatives Considered

### Option B — Amend architecture.md §3.1 + §5.7(spec catches up to code)

**Action**:
- Amend architecture.md §3.1:移除 `[Context Expander]` step from pipeline diagram
- Amend architecture.md §5.7:9 stages → 6 stages
- Repurpose `prev_chunk_id` / `next_chunk_id` 純粹係 **citation rendering metadata**(俾 frontend display "see also chunk #41 / #43" cross-references)
- C05-generation.md §1 diagram reflect actual 6-stage flow
- (Optional)frontend Citation card 擴展 display prev/next cross-ref links — W17+ scope
- V6 Debug View no code change(已 6-stage,spec catches up)

**Pros**:
- Lowest immediate work(0.5 day pure spec/governance)
- V6 6-stage 立即 reconcile(spec catches up to code + W15 D2 plan changelog 已 align 6)
- 0 new code = 0 new bug surface for W16+ Beta launch
- C05 design note + V6 6-stage + W15 D2 plan changelog 三個 source 已 align(spec §5.7 反而係 outlier)
- Karpathy §1.2 simplicity-first:Tier 1 RAG quality 已 acceptable without Context Expander

**Cons**:
- architecture.md §3.1 + §5.7 amendment = governance debt(2 個 spec promise reversal)
- RAG quality enhancement opportunity 放棄
- prev/next chunk_id storage capacity 用 not justified at retrieval-time level(只係 citation metadata = 細用例;~20 bytes × millions chunk overhead 唔合理)
- Tier 2 仍可加 Context Expander(no permanent block,但 Tier 1 launch quality plateau)
- Karpathy §1.4 goal-driven:RAG quality 係 Drive Project user value driver — Option A 對 W16+ Beta cohort D365 complex corpus 有實質 quality lift

**Rejected because**:D365 corpus structurally complex — Context Expander 真正 useful;prev/next storage 已 invested(~20 bytes × millions)— Option A 真正 consume;spec §3.1 + §5.7 兩個 reversal = governance debt > 1.5 days code work;Tier 2 仍要做 no net saving。

### Option C — Split delivery(Backend Context Expander now,V6 9-stage frontend defer W17+)

**Action**:
- Phase 3 W16+:deliver backend Context Expander module(`backend/generation/context_expander.py`)+ CRAG integration + C05 design note
- V6 Debug View frontend 9-stage expansion → W17+ scope
- architecture.md §3.1 + §5.7 reaffirmed,但 spec ↔ frontend lag temporarily

**Pros**:
- Backend RAG quality lift immediate(W16+ Beta cohort benefit)
- Phase 3 工時 reduce(~1 day instead of 1.5 days)
- V6 frontend expansion 留 W17+ Beta hardening 一齊處理(visual baseline + interactive E2E 同時 update)

**Cons**:
- Spec ↔ V6 frontend lag(W16-W17 之間 V6 顯示 6 stages 但 backend 真有 9 stages metric)
- Stakeholder demo if V6 Debug 牽涉到 — admin 唔會見到 Context Expander stage transparency
- Carry-over `CO_W15_F4_baseline_capture` 需要 W17+ regenerate again post 9-stage(double-work avoided by Option A immediate full delivery)

**Rejected because**:0.5 day saved 唔足以 justify 兩段 spec ↔ frontend lag;Phase 3 stack with ADR-0018 + ADR-0019 = ~4.5 days 可以 fit 一次過 batch process;Karpathy §1.3 surgical:一次過 deliver 全套 vs split 兩 phase 兩個 carry-over。

---

## Consequences

### Positive

- **architecture.md §3.1 + §5.7 honored**(no governance debt;reaffirm not amend)
- **prev/next chunk_id storage 真正 consumed**(~20 bytes × millions overhead justified)
- **RAG quality ceiling raised**:D365 complex corpus benefits + W16+ Beta cohort context-dependent question coverage
- **Internal-spec inconsistency resolved**:4 sources align 9-stage(§3.1 + §5.7 + C05 design note update + V6 frontend update + backend code add module)
- **V6 9-vs-6 stage reconcile via code catch-up**(spec wins;W15 D2 plan changelog reframed as interim wireframe scope before full deliver)
- **Stakeholder demo enriched**:V6 Debug 9-stage transparency for retrieval engineering review
- **Karpathy §1.4 goal-driven**:RAG quality enhancement = EKP platform value lift core

### Negative

- **W16 schedule +1.5 days**(stack with ADR-0018 + ADR-0019 = ~4.5 days cumulative Phase 3)
- **New code = new risk surface**:mitigated via batch fetch latency optimization(`chunk_id in (...)` single Azure Search call)+ edge case handling(first/last chunk + cross-doc boundary)
- **Per-query latency overhead**:~30-50ms batch fetch add(non-Cohere call,純 BM25 ID filter);measured + monitored via Langfuse trace
- **V6 Playwright pixel diff baseline re-capture trigger**:W16 F4 user smoke first run scope post 9-stage expansion(carry-over already)

### Neutral

- **Sequential dependency on ADR-0018**:Context Expander 用 kb_id parameter,所以 ADR-0018 implementation 必須先 land(~1.5-2 days)→ ADR-0020 implementation(~1.5 days)。Phase 3 順序 P0.1 → P0.2 → P0.3。
- **C05 design note `last_updated` bump**:同 P1 Phase 4C design notes refresh batch
- **Feature flag option**:`crag.py` 可 add `enable_context_expansion` flag(default True;test override False)allow A/B test if quality regression surfaced post Beta launch

---

## References

- **Reaffirmed(NOT amended)**:`docs/architecture.md` §3.1 Query Pipeline(line 210-211 Context Expander step)+ §5.7 V6 Debug View(9-stage spec)
- **Internal-spec inconsistency resolution targets**:
  - `docs/02-architecture/components/C05-generation.md` §1 diagram update
  - `frontend/app/debug/[traceId]/page.tsx` 6 → 9 stages
  - W15 D2 plan §F2.2 §7 changelog reframe(6-stage scope was interim wireframe alignment;9-stage full deliver post-ADR-0020)
- **Audit trigger**:`docs/02-architecture/audit-W15-d5-vs-spec.md` §1.5 C05 Major drift #3 + §CC-3(2026-05-09 W15 D5 closeout)
- **Cross-ref(sequential dependency)**:[ADR-0018 Multi-KB kb_id propagation](./0018-multi-kb-kb-id-propagation.md)— Context Expander 用 kb_id parameter
- **Sister ADRs**:[ADR-0018](./0018-multi-kb-kb-id-propagation.md)+ [ADR-0019](./0019-pdf-parser-tier-1-deliver.md)— P0 batch decision triple
- **Code citations**:
  - `backend/ingestion/orchestrator.py:157-158`(prev/next chunk_id populated)
  - `backend/indexing/schema.json:16-17`(prev/next stored)
  - `backend/generation/crag.py`(Context Expander integration target)
  - `backend/generation/prompt_builder.py:18-67`(prompt building uses raw chunks today)
  - `frontend/app/debug/[traceId]/page.tsx`(V6 6-stage current scaffold)
- **Behavioral baseline**:Karpathy §1.4 goal-driven(RAG quality = platform value core)+ §1.3 surgical(reject Option C split delivery — full deliver one phase)+ §1.2 simplicity-first(reject Option B amendment — storage 已 invested)

---

## Implementation Deliverables(W16+ Phase 3)

### Code changes(backend Context Expander)

- [ ] `backend/generation/context_expander.py` — NEW file ~100 lines
  - `ExpandedChunk` dataclass:original + prev_context + next_context + expanded_text
  - `async def expand_context(reranked_chunks, kb_id, searcher) -> list[ExpandedChunk]`
  - Batch fetch prev/next chunks via single Azure Search call(`chunk_id in ('{id1}', '{id2}', ...)`)
  - Edge case handling:first chunk(no prev)+ last chunk(no next)+ cross-doc boundary
- [ ] `backend/generation/prompt_builder.py` — `build_prompt()` signature accept `list[ExpandedChunk]`(passes `expanded_text` to LLM)
- [ ] `backend/generation/crag.py` — wire Context Expander between rerank + prompt build
- [ ] (Optional)Feature flag `crag.enable_context_expansion`(default True)— A/B test capability post Beta

### Code changes(frontend V6 9-stage expansion)

- [ ] `frontend/app/debug/[traceId]/page.tsx` — 6 → 9 stages PipelineStageCollapsible
  - Query Rewriter(currently implicit in CRAG)
  - Re-retrieve(CRAG correction loop)
  - **Context Expander NEW**(top-5 + per-chunk prev/next preview + expansion stats)
- [ ] Per-stage data display:`expansion_count` / `boundary_skip_count` / `latency_ms`

### Backend `/debug/trace/{trace_id}` extension(W16 F5 stub closure cascade)

- [ ] Return per-stage data 包括 Context Expander stats(synergy with W16 F5 deliverable)

### Tests

- [ ] Unit tests `backend/tests/test_context_expander.py`(~10 cases):
  - Basic 5-chunk expansion happy path
  - First chunk no prev → skip prev
  - Last chunk no next → skip next
  - Cross-doc boundary(prev/next chunk in different doc)→ skip
  - Empty top-5 → return empty list
  - All chunks have prev/next → 5 expansions
  - Mixed scenario(some have prev/next,some don't)
  - Batch fetch latency assertion(< 50ms typical)
  - kb_id parameter propagation(per ADR-0018 cross-ref)
  - Feature flag disabled → return reranked_chunks as ExpandedChunk with no prev/next
- [ ] Integration test:end-to-end query → expanded context → LLM synthesis → verify answer quality lift on test query

### Documentation

- [ ] `components/C05-generation.md` update(P1 Phase 4C):
  - `last_updated` bump to 2026-05-09
  - §1 internal architecture diagram add Context Expander step
  - §2 Outputs add ExpandedChunk reference
  - Cross-ref ADR-0020
- [ ] (Optional)architecture.md §3.1 + §5.7 no amendment needed(spec already correct;reality catch-up only)

### Eval / observability

- [ ] Langfuse trace tag stage `context_expansion`(per-stage cost / latency attribution)
- [ ] Per-query expansion stats in trace metadata
- [ ] (Optional)A/B test with `enable_context_expansion=False` baseline → measure quality delta(faithfulness / answer_relevancy / context_precision / context_recall via RAGAs subset run)

---

**Implementation timing**:W16 active flip Phase 3 deliverable post Track A IT cred populate event trigger(rolling JIT per CLAUDE.md §10 R1)。**Estimated 1.5 days work**;**sequential dependency on ADR-0018**(Context Expander 用 kb_id parameter,Multi-KB kb_id wiring 必須先 land)。

**Phase 3 implementation order**:
1. **ADR-0018 Multi-KB kb_id wiring**(~1.5-2 days)— retrieval pipeline kb_id propagation
2. **ADR-0019 PDF parser**(~1 day)— independent;可 parallel with ADR-0018 OR after
3. **ADR-0020 Context Expander**(~1.5 days)— **after ADR-0018**(uses kb_id)

**Total Phase 3 cumulative**:~4.5 days(ADR-0018 + ADR-0019 + ADR-0020),fit W16 active flip schedule。

**Re-audit trigger**:Post-implementation audit re-run on §1.5 C05 + §CC-3 specifically — verify:
- `backend/generation/context_expander.py` exists + Tier 1 wired into crag.py
- V6 Debug View 9 stages(spec §5.7 alignment)
- C05 design note `last_updated` bumped + §1 diagram Context Expander listed
- Internal-spec consistency restored(§3.1 + §5.7 + C05 design note + V6 frontend + backend code 5 sources align 9-stage)
