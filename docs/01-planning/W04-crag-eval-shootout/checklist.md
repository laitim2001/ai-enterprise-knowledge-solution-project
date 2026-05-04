---
phase: W04-crag-eval-shootout
plan_ref: ./plan.md
status: active
last_updated: 2026-05-04
---

# Phase W04 — Checklist

> Atomic checkbox(每 item ≤ 1–2 hour effort)。
> Status:`draft` 直到 W3 D5 closeout sign-off + W4 kickoff approval。
> 全 unchecked 至 W4 D1 implementation start。

## F1 — CRAG L2 correction loop

- [x] `backend/generation/crag.py` `CragLoop` class skeleton ✅ W4 D1
- [x] Grader via GPT-5.4-mini(`CragGrader.grade(query, chunks) → GradeResult` returning numeric confidence ∈ [0, 1])✅ W4 D1
- [x] Threshold check `confidence < threshold` triggers correction(threshold from `Settings.crag_confidence_threshold`,default 0.70 not 0.6 plan-draft)✅ W4 D1
- [x] Query rewrite(`CragGrader.rewrite_query`)+ re-fetch top_k=20(configurable `expanded_top_k`)+ re-synthesize path ✅ W4 D1
- [x] Max 1 correction iteration(L2 baseline,L3 deferred per §6.1 W5)✅ W4 D1
- [x] tenacity retry on grader RateLimitError + APITimeoutError(3 attempts exponential 1-8s)✅ W4 D1
- [x] structlog `crag_loop` cost log event(grader + rewrite + extra synth tokens + crag_latency_ms)✅ W4 D1
- [x] Wired into `/query` non-stream path(stream path L3-only per architecture.md §3.5;respects `payload.enable_crag` flag)✅ W4 D1
- [x] Unit tests:above-threshold skip / below-threshold trigger / 4 graceful fallback paths(grader failure / rewrite failure / rewrite empty / re-synth failure)✅ W4 D1(14 tests pass)

## F2 — RAGAs eval automation

- [ ] `backend/eval/ragas_runner.py` integrating ragas Python SDK
- [ ] Faithfulness metric impl
- [ ] Answer Relevancy metric impl
- [ ] Context Precision metric impl
- [ ] Context Recall metric impl
- [ ] Judge LLM = GPT-5.4-mini config wire
- [ ] `scripts/run_ragas_eval.py --eval-set eval-set-v1.yaml --output ragas-results.json`
- [ ] Output JSON schema documented(per-query + aggregate + judge cost)
- [ ] tenacity retry on judge transient errors
- [ ] Unit test:mocked ragas SDK assert metric extraction + JSON schema

## F3 — 4-way reranker shootout

- [ ] `backend/retrieval/reranker/voyage.py` impl(REST `voyage-rerank-2.5`)
- [ ] `backend/retrieval/reranker/zeroentropy.py` impl(REST `zerank-1`)
- [ ] `backend/retrieval/reranker/azure_semantic.py` impl(Azure AI Search `@search.semanticConfiguration`)
- [ ] `factory.py` extended:`make_reranker(settings)` switch on `settings.reranker_kind`
- [ ] Vendor procurement Voyage key(Chris,non-Azure path)
- [ ] Vendor procurement ZeroEntropy key(Chris,non-Azure path)
- [ ] `scripts/run_reranker_shootout.py` runs 4 reranker × eval-set-v1
- [ ] Comparison table emit:R@5 / R@10 / 4-RAGAs metric per reranker
- [ ] Unit tests:each new reranker mocked REST(desc by score / top_n clamp / invalid index skip)

## F4 — Eval set v1 expansion(+ 20 real queries)

- [ ] 20 NEW queries collected(Chris source = customer support / Drive Manual support requests)
- [ ] Coverage:financial-software workflow(AR/AP/FA/CB/GL/BM)+ table-data lookups + multi-doc synthesis
- [ ] Ground truth chunk_ids labeled per query(Chris SME)
- [ ] `docs/eval-set-v1.yaml` promoted from `-draft.yaml`
- [ ] `scripts/validate_eval_set.py` runs clean against v1(55 queries)

## F5 — Cohere rerank live verify + lift baseline(W3 C1 close)

- [ ] `.env` `cohere_endpoint` + `cohere_api_key` populated(Chris signoff post Marketplace deploy)
- [ ] `scripts/run_cohere_lift_smoke.py` impl
- [ ] 10 representative eval queries × hybrid-only vs hybrid+Cohere R@5 compare
- [ ] Lift summary logged in W4 progress.md + decision-form Q5 follow-up note
- [ ] **DEFERRED W5/W6 if procurement still pending** — Gate 2 verdict adjusts

## F6 — GPT-5.5 live latency baseline + cost trace(W3 C2 close)

- [ ] Manual `/query` smoke against 5 real queries(Chris dev server)
- [ ] Langfuse cost trace per call:input_tokens / output_tokens / latency_ms / refused / citations_count
- [ ] Baseline numbers documented:p50 / p95 latency / per-query cost USD
- [ ] Feed Gate 2 cost-per-query analysis(non-blocking)

## F7 — SSE live verify(W3 C3 close)

- [ ] End-to-end manual smoke Chat UI `/` → submit → token render + citation card + reranker label + stop
- [ ] Verify text-delta event ordering matches OpenAI stream
- [ ] Verify Stop button cancels backend stream(asyncio.CancelledError logged)
- [ ] 1-2 screenshots logged in W4 progress(visual evidence)

## F8 — Component design note status bumps(W3 G4 close)

- [x] `docs/02-architecture/components/C04-retrieval.md` v1-active → v2-stable(rerank wire + 4-way shootout surface ready)✅ W4 D1
- [x] `docs/02-architecture/components/C05-generation.md` v0-draft → v1-active(synthesizer + SSE + CRAG L2)✅ W4 D1
- [x] `docs/02-architecture/components/C08-api-gateway.md` v2-stable updated with W3-W4 deliverables(SSE wire + cancel + CragLoop)✅ W4 D1
- [x] `docs/02-architecture/components/C09-admin-ui.md` v0-draft → v1-active(wizard + admin views + Settings baseline)✅ W4 D1
- [x] `docs/02-architecture/components/C10-chat-ui.md` v0-draft → v1-active(streaming + citation + modal)✅ W4 D1
- [x] `docs/02-architecture/COMPONENT_CATALOG.md` status row updates synced ✅ W4 D1

## F9 — PPT parser orchestrator wire(W3 C6 close)

- [x] `backend/ingestion/parsers/__init__.py` `select_parser()` factory dispatches by file extension(.pptx → PptxParser / .docx → DoclingDocxParser / .pdf → DoclingDocxParser)✅ W4 D1
- [x] Format auto-detect via file extension(.pptx / .docx / .pdf;uppercase normalised;unsupported → ValueError)✅ W4 D1
- [x] `chunker/strategies.py` `slide_based` path no longer NotImplementedError — delegates to `LayoutAwareChunker`(per Karpathy §1.2 simplicity:PptxParser emits same heading-para-table-image structure as Docling so chunker reuse natural)✅ W4 D1
- [ ] **DEFERRED W4 D2-D3** Smoke run 1 of W3 D1 後段 3 PPT samples → end-to-end ingest → chunks visible via `/kb/{id}/chunks`(needs `scripts/run_pptx_ingest_sanity.py` + Azure AI Search index ready;non-blocking F9 unit acceptance)
- [x] Unit test:select_parser dispatches correctly(.pptx / .docx / .pdf / uppercase / unsupported)+ select_chunker(pptx, auto/slide_based) returns LayoutAwareChunker + heading_aware standalone still NotImplementedError ✅ W4 D1(8 tests pass + 1 W2 test updated)

## F10 — Gate 2 verdict + W4 retro + W5 kickoff prep

- [ ] **Gate 2 verdict**(4-metric within 5pp互換 between Cohere baseline + winning shootout)
- [ ] If PASS:W5 plan = optimization scope(L3 routing conditional)
- [ ] If FAIL:drop L2 CRAG;W5 plan = baseline-only scope per §6.3
- [ ] W04 progress.md retro section completed
- [ ] W05 phase folder mkdir + plan.md draft
- [ ] W04 carry-overs documented
- [ ] W04 progress.md frontmatter status flipped to `closed`

---

## Cross-Cutting

- [ ] Each commit references `progress.md` Day-N entry(R2)
- [ ] Component tag in commit message per CC-1
- [ ] OQ status sync to `decision-form.md`(R4)— Q21 final pick W4 D5 critical
- [ ] Gate 2 verdict logged in `architecture.md §6.3` decision row(via ADR-0012 if FAIL → drop L2)
- [ ] RISK_REGISTER.md update if R1/R2 procurement persists OR Gate 2 FAIL surfaces as new risk

---

**Lifecycle reminder**:呢份 checklist 衍生自 `plan.md` deliverables。新加 deliverable 必須先入 plan + changelog,然後再加 checklist item。
