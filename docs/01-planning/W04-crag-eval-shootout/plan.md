---
phase: W04-crag-eval-shootout
name: "CRAG L2 + RAGAs Eval + Reranker Shootout + Gate 2"
sprint_week: W4
start_date: 2026-05-15          # tentative — same Option-A 2-day-shift heuristic as W2/W3 if Chris confirms; otherwise 2026-05-19 per architecture.md §6.1 original schedule
end_date: 2026-05-21            # tentative,5 working days
status: active                  # flipped 2026-05-04 W4 D1 kickoff per user "啟動 W4 D1" signal post W3 closeout
spec_refs:
  - architecture.md §6.1 W4 row
  - architecture.md §3.1       # query pipeline + CRAG loop
  - architecture.md §3.2       # reranker shootout vendor list + Gate 2 4-metric
  - architecture.md §3.6       # eval methodology
  - architecture.md §6.3       # Gate 2 verdict policy
  - components/C04-retrieval.md # reranker swap surface
  - components/C05-generation.md # CRAG correction loop
  - components/C06-eval.md     # RAGAs framework
  - eval-methodology.md        # 4-metric definition + threshold
prior_phase: W03-chat-retrieval-citation
---

# Phase W04 — CRAG L2 + RAGAs Eval + Reranker Shootout + Gate 2

> **Plan version**:1.0(draft 2026-05-04 W3 D5 末 closeout batch)
> **Owner**:Chris(Tech Lead)
> **Approved by**:_(pending Chris W3 D5 closeout sign-off + W4 kickoff approval)_

## 1. Scope

W04 closes the **Gate 2 critical path** by hardening the answer-quality stack:CRAG L2 correction loop on top of W3 hybrid+rerank+synthesis foundation,RAGAs 4-metric eval automation replacing manual smoke,4-way reranker shootout(Cohere v3.5 / Voyage rerank-2.5 / ZeroEntropy zerank-1 / Azure built-in semantic)to validate the Q21 final pick,and a 20-query expansion of the eval set to make `eval-set-v1` production-grade。Wraps with W3 carry-over closure(live cloud verifications + design note bumps + PPT orchestrator wire)+ Gate 2 verdict + W5 conditional path decision。

**Pre-condition for W4 promotion**:W3 D5 PASS(G1 + G3 hard gates) + Chris kickoff sign-off。Fail = HALT,foundation iteration loop per architecture.md §6.3。

**Sprint week origin**:[`architecture.md` §6.1 W4](../../architecture.md)

## 2. Deliverables(F1-F10)

### F1 — CRAG L2 correction loop
- **Component(s)**:**C05** Generation(CRAG)
- **Spec ref**:`architecture.md §3.1 query pipeline §3.5 CRAG`,`components/C05-generation.md §2 CRAG loop`
- **OQ deps**:none(CRAG L2 baseline non L3 routing — L3 conditional on Gate 2 全 pass per architecture.md §6.1 W5 row)
- **Acceptance criteria**:
  - `backend/generation/crag.py` `CragLoop` class wrapping `Synthesizer`:retrieve → grade chunks → if low-confidence → rewrite query / fetch more → re-synthesize
  - Grader uses GPT-5.4-mini(Q4 deployment Resolved W1 D1)`grade_chunks(query, chunks) → list[ConfidenceScore]`
  - Threshold:if `mean(confidence) < 0.6` → trigger correction(query rewrite + re-fetch top_k=20)
  - Max 1 correction iteration(L2 baseline,L3 deferred per §6.1 W5)
  - Wired into `/query` non-stream path(stream path L3-only per §3.5)
  - tenacity retry on grader RateLimitError + APITimeoutError
  - Cost log via structlog(`crag_loop_grader` event:input_tokens / output_tokens / triggered_correction / final_confidence)
  - Unit test:mocked grader → confidence above threshold(skip correction)/ below(trigger)/ correction failure(graceful fallback to original)
- **Effort estimate**:4h
- **Owner**:AI

### F2 — RAGAs eval automation
- **Component(s)**:**C06** Eval Framework
- **Spec ref**:`architecture.md §3.6 eval methodology`,`eval-methodology.md`,`components/C06-eval.md §2 RAGAs integration`
- **OQ deps**:Q13 ground truth allocation Resolved(W1 D1)
- **Acceptance criteria**:
  - `backend/eval/ragas_runner.py` integrating ragas Python SDK
  - 4 metric implementations:**Faithfulness** / **Answer Relevancy** / **Context Precision** / **Context Recall**(all per `eval-methodology.md` definitions)
  - Judge LLM = GPT-5.4-mini(`azure_openai_deployment_llm_judge`)consistent with grader for cost containment
  - Run mode:`scripts/run_ragas_eval.py --eval-set eval-set-v1.yaml --output ragas-results.json`
  - Output JSON schema:per-query 4-metric scores + aggregate mean / median / p95 + judge cost trace
  - tenacity retry on judge LLM transient errors
  - Unit test:mocked ragas SDK → assert metric extraction + JSON schema
- **Effort estimate**:3h
- **Owner**:AI

### F3 — 4-way reranker shootout
- **Component(s)**:**C04** Retrieval Engine + **C06** Eval Framework
- **Spec ref**:`architecture.md §3.2 vendor table reranker row`,`components/C04-retrieval.md §3 reranker swap surface`
- **OQ deps**:Q5 Resolved(Cohere Path A)+ Q21 final pick deferred to W4 verdict
- **Acceptance criteria**:
  - `backend/retrieval/reranker/{voyage,zeroentropy,azure_semantic}.py` 3 NEW reranker implementations sharing `Reranker` Protocol from W3 D1 base.py
  - Voyage uses `voyage-rerank-2.5` REST(direct API,Q21 procurement TBD)
  - ZeroEntropy uses `zerank-1` REST(direct API,Q21 procurement TBD)
  - Azure semantic uses Azure AI Search `@search.semanticConfiguration` (built-in,no extra procurement;already in S1 SKU)
  - `factory.py` extended:`make_reranker(settings)` switch on `settings.reranker_kind`(literal `"cohere"|"voyage"|"zeroentropy"|"azure"|"off"`)
  - Shootout script `scripts/run_reranker_shootout.py`:run 4 reranker × full eval-set-v1 → emit comparison table(R@5 / R@10 / 4-RAGAs metric per reranker)
  - Result feeds Gate 2 verdict(per §3 G2 below)
  - Unit test:each new reranker mocked REST → desc by score + top_n clamp + invalid index skip
  - Vendor procurement:Voyage + ZeroEntropy keys via Chris;Azure Marketplace cohere already W3 D2 path
- **Effort estimate**:4h(impl 2h + procurement contingency 0.5h + shootout run 1h + comparison analysis 0.5h)
- **Owner**:AI(impl)+ Chris(procurement keys)

### F4 — Eval set v1 expansion(+ 20 real queries)
- **Component(s)**:**C06** Eval Framework
- **Spec ref**:`docs/eval-methodology.md`,`docs/eval-set-v1-draft.yaml`(W2 D5 → 35 corpus-aligned queries)
- **OQ deps**:Q6 real query collection owner(currently Chris;source = customer support tickets / Drive Manual support requests)
- **Acceptance criteria**:
  - `docs/eval-set-v1.yaml`(promoted from `-draft.yaml`,formal v1)contains **55 queries**(35 W2 + 20 NEW real)
  - 20 NEW queries cover:financial-software workflow questions(AR/AP/FA/CB/GL/BM)+ table-data lookups(R4 hallucination test bed)+ multi-document synthesis questions
  - Ground truth chunk_ids labeled per query(Chris async via `scripts/discover_chunk_ids.py` + manual SME review)
  - `eval-set-v1-draft.yaml` deprecated(symlink → v1 OR removed)
  - Validator `scripts/validate_eval_set.py` runs clean against v1
- **Effort estimate**:2h(AI:format/validate;Chris:label)
- **Owner**:Chris(label)+ AI(integration)

### F5 — Cohere rerank live verify + lift baseline(W3 C1 close)
- **Component(s)**:**C04** Retrieval Engine
- **Spec ref**:W3 plan §3 G5 + W3 retro § Carry-overs C1
- **OQ deps**:Cohere Marketplace endpoint+key populate(Chris async procurement,7-14d turnaround from 2026-05-04)
- **Acceptance criteria**:
  - `.env` populated `cohere_endpoint` + `cohere_api_key`(Chris signoff post-deploy)
  - `scripts/run_cohere_lift_smoke.py` runs 10 representative eval queries,compares hybrid-only vs hybrid+Cohere R@5
  - Lift summary logged in W4 progress entry + decision-form Q5 follow-up note
  - Non-blocking — if procurement still pending,`F5 deferred to W5/W6`,Gate 2 verdict adjusts to "Cohere data-driven verdict pending procurement"
- **Effort estimate**:1h
- **Owner**:Chris(procurement)+ AI(smoke run + analysis)

### F6 — GPT-5.5 live latency baseline + cost trace(W3 C2 close)
- **Component(s)**:**C05** Generation + **C07** Observability
- **Spec ref**:W3 retro § Carry-overs C2
- **OQ deps**:none(Q4 Resolved W1)
- **Acceptance criteria**:
  - Manual `/query` smoke against 5 real queries(post Chris dev server start)
  - Langfuse cost trace verified:input_tokens / output_tokens / latency_ms / refused / citations_count present per call
  - Baseline numbers documented in W4 progress(p50 / p95 latency / per-query cost USD)
  - Feed Gate 2 cost-per-query analysis(non-blocking acceptance for Gate 2 PASS)
- **Effort estimate**:1h
- **Owner**:Chris(dev server)+ AI(analysis)

### F7 — SSE live verify(W3 C3 close)
- **Component(s)**:**C08** API Gateway + **C10** Chat UI
- **Spec ref**:W3 retro § Carry-overs C3
- **OQ deps**:Q4 + Q5 Resolved
- **Acceptance criteria**:
  - End-to-end manual smoke:Chat UI(`/`)→ submit query → token-by-token render + citation card + reranker label + stop button
  - Verify text-delta event ordering matches OpenAI stream
  - Verify Stop button cancels backend stream(asyncio.CancelledError logged)
  - 1-2 screenshots logged in W4 progress(visual evidence;non-binding for Gate 2)
- **Effort estimate**:1h
- **Owner**:Chris(dev server smoke)+ AI(progress entry)

### F8 — Component design note status bumps(W3 G4 close)
- **Component(s)**:cross-cutting governance
- **Spec ref**:CLAUDE.md §10 R5(component design notes per CC-5)
- **OQ deps**:none
- **Acceptance criteria**:
  - `docs/02-architecture/components/C04-retrieval.md` v1 → v2(rerank wire + 4-way shootout extension surface)
  - `docs/02-architecture/components/C05-generation.md` v0 → v1(synthesizer + CRAG L2)
  - `docs/02-architecture/components/C08-api-gateway.md` v1 → v1.1(SSE wire + cancel propagation)
  - `docs/02-architecture/components/C09-admin-ui.md` v1 → v1.1(wizard + Settings baseline)
  - `docs/02-architecture/components/C10-chat-ui.md` v0 → v1(streaming + citation card + screenshot modal)
  - `docs/02-architecture/COMPONENT_CATALOG.md` status row updates synced
- **Effort estimate**:1h
- **Owner**:AI

### F9 — PPT parser orchestrator wire(W3 C6 close)
- **Component(s)**:**C01** Ingestion
- **Spec ref**:`architecture.md §3.3 PPT format share`,`components/C01-ingestion.md §1 parser registry`
- **OQ deps**:Q1 Resolved(30% PPT share)
- **Acceptance criteria**:
  - `IngestionOrchestrator` parser registry adds `pptx → PptxParser()` entry
  - Format auto-detect via file extension(.pptx → PptxParser;.docx → DoclingParser;.pdf → DoclingParser)
  - `chunker/strategies.py` slide_based path no longer NotImplementedError(uses W3 D1 PPT parser slide structure)
  - Smoke run:1 of W3 D1 後段 3 PPT samples → end-to-end ingest → chunks visible via `/kb/{id}/chunks`
  - Unit test:orchestrator selects PptxParser for .pptx file → calls parser → emits chunks
- **Effort estimate**:1h
- **Owner**:AI

### F10 — Gate 2 verdict + W4 retro + W5 kickoff prep
- **Component(s)**:cross-cutting governance
- **Spec ref**:`architecture.md §6.3 Gate 2`,`PROCESS.md §2.3 closeout`
- **OQ deps**:F2 + F3 + F4 results feed verdict
- **Acceptance criteria**:
  - **Gate 2 verdict**:4-metric within 5pp互換 between Cohere(W3 baseline)+ winning shootout reranker → PASS = continue Tier 1 W5+ optimization;FAIL = drop L2 CRAG,Tier 1 收尾轉 baseline-only(per §6.3)
  - W04 progress.md retro section completed(7 sub-sections + Phase Gate verdict + carry-overs + ADR triggers)
  - W05 phase folder kickoff:`docs/01-planning/W05-optimization/{plan,checklist,progress}.md` draft(W5 conditional on Gate 2 全 pass per §6.1;if Gate 2 FAIL → W5 plan 寫 baseline-only optimization scope instead of L3 routing)
  - W04 carry-overs documented(reranker procurement remainder / RAGAs eval set growth / CRAG iteration-count tuning)
  - W04 progress.md frontmatter status flipped to `closed`
- **Effort estimate**:2h
- **Owner**:AI(draft)+ Chris(approve)

## 3. Success Criteria(Phase Gate 2 to W5)

> **Gate 2 is the most important quality gate of Tier 1**(per architecture.md §6.3)。FAIL = drop L2 CRAG,Tier 1 收尾轉 baseline-only。

| # | Criterion | Target | Measure | Block W5? |
|---|---|---|---|---|
| G1 | All 10 deliverables 完成 OR explicit defer | 10/10 | progress closeout | Yes |
| G2 | **Gate 2 4-metric within 5pp互換** between Cohere baseline + winning shootout reranker | 4 of 4 metrics within 5pp | RAGAs eval-set-v1 run | **Yes — drop L2 if FAIL** |
| G3 | RAGAs eval automation runs end-to-end on eval-set-v1 | clean run + JSON output | scripts/run_ragas_eval.py | Yes |
| G4 | Backend ruff + frontend lint + type-check 0 errors | All clean | local run | Yes |
| G5 | Component design notes C04/C05/C08/C09/C10 status bumped | bumped | review | Yes |
| G6 | eval-set-v1 promoted from draft + 55 queries labeled | 55/55 | YAML count + validator | No(Chris async,partial OK if 45+) |

## 4. Risks(Phase-Specific)

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | Cohere Marketplace endpoint procurement still pending W4 D1(blocks F3 baseline + F5 lift)| Medium | High | F3 shootout 用 hybrid-only baseline如 Cohere endpoint pending;F5 explicitly defers to W5/W6 if not unblocked;Gate 2 verdict adjusts to "Cohere baseline pending,N-way shootout based on available rerankers" |
| R2 | Voyage / ZeroEntropy procurement uncertain(non Azure Marketplace path)| Medium | Medium | F3 shootout 可以 partial:Cohere + Azure semantic baseline minimum;Voyage/ZeroEntropy comparison留 W5 if keys arrive |
| R3 | Gate 2 4-metric FAIL within 5pp(rerankers diverge)| Medium | High | Drop L2 CRAG per §6.3;W5 转 baseline-only scope;document specific failing metric + trigger ADR-0012(Tier 1 quality threshold revision) |
| R4 | RAGAs judge LLM cost spike(GPT-5.4-mini 4 metric × 55 queries × shootout 4-way = 880+ judge calls)| Low | Medium | Cap eval set to subset(20 queries × 4 reranker = 320 calls)for shootout phase;full 55 only for winning reranker post-shootout |
| R5 | 20 real query labeling slips(Chris SME bandwidth)| High | Medium | Accept partial labeling — Gate 2 G6 explicitly allows 45+/55(non-blocking);15 queries minimum acceptable;backfill W5-W6 |
| R6 | CRAG threshold 0.6 too aggressive / lenient(false-correction or missed-correction)| Medium | Medium | W4 D1 unit test multiple thresholds against eval-set sample;baseline empirical 0.5-0.7 range;final value tuned post W4 D2 RAGAs run |
| R7 | R8 Ricoh corp proxy reactivation during W4 cloud-heavy work(rerank API + judge LLM)| High | High | Same mitigation as W2/W3:disconnect GlobalProtect VPN;sanity scripts ready post-disconnect;mock-test code path stays correct regardless |

## 5. Day-by-Day Breakdown(rough — pending Option A continuation review at W3 D5 closeout)

| Day | Date | Focus | Deliverables targeted |
|---|---|---|---|
| D1 | 2026-05-15 (Fri) | F1 CRAG core + F8 design notes + F9 PPT orchestrator wire | F1, F8, F9 |
| D2 | 2026-05-16 (Sat) | F2 RAGAs setup + F4 20-query eval-set expansion(Chris async label) | F2, F4 |
| D3 | 2026-05-17 (Sun) | F3 reranker shootout(Voyage + ZeroEntropy + Azure impl + run + compare) | F3 |
| D4 | 2026-05-18 (Mon) | F5 Cohere live verify + F6 GPT-5.5 latency baseline + F7 SSE live verify | F5, F6, F7 |
| D5 | 2026-05-19 (Tue) | Gate 2 verdict + F10 retro + W5 kickoff prep | F10 |

(W3 same-day pattern likely 唔 repeat — F3 reranker shootout requires Voyage/ZeroEntropy procurement keys which are async vendor onboarding;F4 20-query labeling requires Chris SME cycles。Calendar pacing returns)

## 6. Dependencies on Prior Phase

Carry-overs from `W03-chat-retrieval-citation/progress.md` retro:
- **W3 G2** end-to-end /query → Cohere live verify gates F5(Marketplace endpoint procurement pending)
- **W3 G4** component design note bumps → F8 close
- **W3 G5** Cohere rerank lift smoke → F5 close
- **W3 C1** Cohere live verify → **F5**
- **W3 C2** GPT-5.5 latency baseline → **F6**
- **W3 C3** SSE live verify → **F7**
- **W3 C4** Frontend dev server smoke(Chris responsibility)— continues each day Chris runs `pnpm dev`
- **W3 C5** Reranker per-KB field reconsideration → post F3 shootout outcome
- **W3 C6** PPT orchestrator wire → **F9**
- **W3 C7** F8 wizard polish → W7+ Beta polish window(unchanged)
- **W3 C8** plan estimates calibration → W4 plan applies 0.5x heuristic(每 deliverable 1.5-2h baseline)— see §2 effort estimates above

## 7. Plan Changelog

| Date | Change | Reason | Approver |
|---|---|---|---|
| 2026-05-04 | Initial draft(W3 D5 末 closeout batch)| Per PROCESS.md §2.3 rolling-JIT kickoff;status=draft pending Chris W3 D5 closeout sign-off + W4 kickoff approval | Chris(pending approve to flip active) |
| 2026-05-04 | Status `draft → active`(same calendar day W3 closeout → W4 kickoff per user "啟動 W4 D1" signal)| Same-day momentum continues from W3;Chris signoff implicit via "啟動 W4 D1" command;procurement carry-overs (Voyage / ZeroEntropy keys + Cohere endpoint populate) remain async — F3 / F5 plans accommodate via partial shootout fallback per §4 R1+R2 | User-flipped per W4 D1 kickoff |

---

**Lifecycle reminder**:呢份 plan `status=draft`(flipped from W4 kickoff approve to `active`)。重大 deviation 入第 7 節 changelog。
