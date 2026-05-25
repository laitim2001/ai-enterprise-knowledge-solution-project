---
phase: W26-eval-driven-retrieval-tuning
plan_ref: ./plan.md
status: active
last_updated: 2026-05-25
---

# W26 — Checklist

> Derived from `plan.md §2 Deliverables` + §3 Phase-Level Hard Gates。
> Per Chris 3-step refinement(2026-05-25):Step 0 RAGAs baseline → Step 1 rerank threshold(ADR-0037)→ Step 2 query expansion(gated on Step 1 + eval delta)。
> **PIVOTED 2026-05-25 D1**:Step 1 substance changed from rerank threshold to **parent-document retrieval per ADR-0037**(F1 empirical refutation of brief §3 方向 A premise;Chris pivot pick (C) brief §6 step 4)。F2 items rewritten 2026-05-25 D1 cont per ADR-0037 §Implementation Deliverables list。

## F0 — Kickoff governance

### Plan + checklist + progress
- [x] **F0.1** — `docs/01-planning/W26-eval-driven-retrieval-tuning/plan.md` v1.0 written + frontmatter `status: active`
- [x] **F0.2** — `docs/01-planning/W26-eval-driven-retrieval-tuning/checklist.md` derived from plan §2 + §3(this file)
- [x] **F0.3** — `docs/01-planning/W26-eval-driven-retrieval-tuning/progress.md` Day 0 entry written

### R6 pre-active-flip recursive grep verification(per CLAUDE.md §10 R6 W23 F3 amendment + W25 D0 precedent)
- [x] **F0.4** — Grep `backend/retrieval/reranker/cohere.py` confirmed `async def rerank` at line 84(brief §7 84-130 + §2 96-130 ranges consistent — body cutoff within method)
- [x] **F0.5** — Grep `backend/storage/settings.py` confirmed 5 existing `rerank_*` knobs(`cohere_rerank_model` / `voyage_rerank_model` / `zeroentropy_rerank_model` / `cohere_request_timeout_s` / `rerank_top_k: int = 5`)— NEW `rerank_score_threshold` adds clean
- [x] **F0.6** — Grep confirmed `docs/eval-set-v0.yaml` + `docs/eval-set-v0-w25-supplement.yaml` both exist at `docs/` root
- [x] **F0.7** — Grep `/eval/run` + `make_ragas_evaluator` confirmed 8 files reuse-path(routes/eval.py + eval/ragas_evaluator.py + eval/orchestrator.py + 5 tests)
- [x] **F0.8** — Grep ADR registry confirmed last used `0036-react-markdown-chat-answer-rendering.md` → ADR-0037 next available ✅

### Kickoff commit
- [ ] **F0.9** — Kickoff commit:`docs(planning): kickoff W26-eval-driven-retrieval-tuning + R6 grep verify catch upfront`(NOT push;Chris explicit 「push it」instruction needed)

### session-start.md sync
- [ ] **F0.10** — `docs/12-ai-assistant/01-prompts/01-session-start.md` §10 sprint timeline add W26 row(active status)+ §11 retain BUG-025 CLOSED block as context handoff(deferred to F4 closeout per §10 R2 commit-per-Day-N rule — separate `docs(session-start)` commit OR bundle in F4 closeout commit per W25 precedent)

## F1 — Step 0 RAGAs baseline measurement(Chris Step 0,prerequisite — no skip)— ✅ DONE 2026-05-25 D1

> Updated 2026-05-25 D1 — all F1 acceptance items completed via /eval/run + threshold-probe.py;empirical findings drove pivot to F2 parent-doc retrieval(see plan §7 Plan Changelog 2026-05-25 D1 entry)。F2 ORIGINAL scope superseded;next session ADR-0037 parent-doc draft。


### R8 prerequisite gate(STOP and ask if blocked)
- [x] **F1.1** — Azure OpenAI judge key availability check in dev / personal Azure dev tier(per ADR-0017 Plan B (c) precedent)
- [x] **F1.2** — Cohere v4.0-pro production reranker key check(NOT just Azure semantic ranker fallback per brief §4 strict reading)
- [x] **F1.3** — STOP and ask Chris if EITHER blocked — Plan B options:(a) Chris 提供 personal Azure dev tier credentials;(b) defer W26 → W27+ when Track A IT cred lands;(c) limited scope F1(retrieval-only metrics without LLM judge)

### Baseline measurement
- [x] **F1.4** — Decide on measurement script approach:reuse existing `/eval/run` endpoint(W17 F3 RAGAs 4-metric integration)OR new minimal `backend/eval/scripts/w26_baseline_measure.py`(per brief §6 step 1 simpler harness)
- [x] **F1.5** — Run RAGAs 4-metric(faithfulness / answer_relevancy / context_precision / context_recall)on:
  - [x] **F1.5a** — Q-W25-I07「show me all the Integration scenarios」on KB `sample-document-with-image-1`(failed query)
  - [x] **F1.5b** — `what is high level architecture` on same KB(control query — W25 D4 milestone)
  - [x] **F1.5c** — 1-2 additional `eval-set-v0.yaml` baseline samples(targeted query class control)
  - [x] **F1.5d** — `eval-set-v0-w25-supplement.yaml` 13 queries subset(若 R8 OK + Azure budget allow)
- [x] **F1.6** — Capture per-query metadata:retrieved chunk count + chunk_id list + reranked scores(for F2 threshold derivation analysis)

### Baseline report
- [x] **F1.7** — Write `docs/01-planning/W26-eval-driven-retrieval-tuning/baseline-metrics-W26-D1.md`:
  - [x] **F1.7a** — Per-query metric table(faithfulness / answer_relevancy / context_precision / context_recall)
  - [x] **F1.7b** — Per-query retrieved chunk list + reranked scores(diagnostic)
  - [x] **F1.7c** — Aggregated score distribution analysis(used for F2 threshold derivation Q2)
  - [x] **F1.7d** — Recall-dominant vs precision-dominant interpretation(per brief §4 step 1 framing)
  - [x] **F1.7e** — F2 threshold initial value recommendation(NOT magic 0.3 — grounded in F1 distribution)

### F1 closeout
- [x] **F1.8** — Surface F1 result to Chris(AskUserQuestion or chat)— confirm proceed to F2 with derived initial threshold

## F2 — Step 1 parent-document retrieval per ADR-0037(PIVOTED 2026-05-25 D1)

> Rewritten 2026-05-25 D1 cont post F1 empirical refutation + Chris AskUserQuestion pivot pick (C);items 對齊 ADR-0037 §Implementation Deliverables list 7 categories(A governance + B retriever module + C pipeline integration + D Settings + E observability + F tests + G eval + H gate)。

### A. ADR governance gate(satisfied 2026-05-25 D1 cont)
- [x] **F2.1** — `docs/adr/0037-parent-document-section-retrieval.md` v1.0 drafted per CLAUDE.md §6 ADR format(~620 lines:Context + 8-section Decision + 5 rejected Alternatives B-F + Consequences + References + Implementation Deliverables + Decision Log)
- [x] **F2.2** — Chris approval via AskUserQuestion(4 critical Qs Recommended picks:Q4 Default OFF + Q1 top_k=1 + Q2 depth_offset=1 + Q6 Both on)+ Q3/Q5/Q7/Q8 proposed defaults batch-locked;ADR Status flipped Proposed → Accepted
- [x] **F2.3** — `docs/adr/README.md` index synced(row + footer next-NNNN 0037→0038);atomic governance commit `4cdd1bc` 2026-05-25 D1 cont

### B. Backend Parent-Document Retriever module
- [x] **F2.4** — NEW `backend/generation/parent_doc_retriever.py` — **DONE 2026-05-25 D1 cont 3**(~310 lines / under 350 envelope):
  - [x] **F2.4a** — `ParentSectionChunk` dataclass duck-typed `RetrievedChunk` / `ExpandedChunk` compatible ✅(`score: float` + `fields: dict[str, Any]` + `parent_section_text` + `parent_path` + `sibling_count` + `truncated`;`no_aggregation` classmethod for flag-off / shallow / lookup-miss passthrough paths)
  - [x] **F2.4b** — `async def aggregate_parent_sections(reranked_chunks, kb_id, searcher, *, section_depth_offset=1, parent_doc_top_k=1, max_tokens_per_parent=4000, max_chunks_per_parent=50, fallback_to_doc_on_shallow=True) -> tuple[list[ParentSectionChunk], ParentDocStats]` ✅
  - [x] **F2.4c** — Anchor selection per `parent_doc_top_k` ✅(default 1 — top-1 only per Q1 Recommended;passthrough preserves top-2..top-K untouched per Q6 Both on coexistence policy)
  - [x] **F2.4d** — Section path deduplication ✅(ordered dict `parent_fetch_specs: dict[tuple[str, tuple[str, ...]], None]` — multiple anchors sharing parent → fetch once)
  - [x] **F2.4e** — Batch fetch via `HybridSearcher.fetch_chunks_by_section_path()` ✅(per-parent loop;@retry decorator on the searcher handles transient errors transparently)
  - [x] **F2.4f** — Token budget truncation ✅(`max_tokens_per_parent` cap via `_estimate_tokens` 4-char-per-token heuristic;tail-drop preserving narrative start;`chunk_index` ASC order from searcher's `orderby` payload;first sibling always included even if alone exceeds budget — degenerate-doc graceful)
  - [x] **F2.4g** — Cross-doc boundary respect ✅(anchor's `doc_id` extracted + passed to searcher;different anchors with different `doc_id` → separate parent_lookup keys → separate fetches;no cross-doc spill)
  - [x] **F2.4h** — Shallow `section_path` fallback to doc-level ✅(via `_compute_parent_path` helper:`len > section_depth_offset` → normal drop;`len ≤ section_depth_offset` + `fallback_to_doc_on_shallow=True` → preserve top-1 segment;else → None + `skipped_shallow_count++`)
  - [x] **F2.4i** — Graceful network error handling ✅(per ADR-0020 precedent — `except Exception` log + return anchors unchanged;`# noqa: BLE001` documented + W26 F2.13h test verifies no exception bubbles up)
- [x] **F2.5** — `backend/retrieval/hybrid.py` NEW method `fetch_chunks_by_section_path(parent_path: list[str], doc_id: str, kb_id: str) -> list[HybridSearchHit]` — **DONE 2026-05-25 D1 cont 2**(~85 lines added between `fetch_by_chunk_ids` + `search`):
  - [x] **F2.5a** — OData filter:`kb_id eq '...' and doc_id eq '...' and enabled eq true and section_path/any(s: s eq '<each segment>')` joined `and` ✅
  - [x] **F2.5b** — OData escaping(double single quotes for `'`)✅
  - [x] **F2.5c** — Order by `chunk_index ASC`(preserves narrative order)✅
  - [x] **F2.5d** — Hard cap `parent_doc_max_chunks_per_parent=50`(防 pathological doc)✅

### C. Pipeline integration
- [ ] **F2.6** — `backend/generation/prompt_builder.py` dispatch chain extension:`parent_section_text > expanded_text > chunk_text` fallback chain(Q6 Both on — coexistence with ADR-0020 Context Expander)
- [ ] **F2.7** — `backend/generation/crag.py` wire parent-doc step between Context Expander + CRAG grade(flag-gated `enable_parent_doc_retrieval`)
- [ ] **F2.8** — `backend/api/routes/query.py` `/query` happy path wire(1st site per ADR-0020 precedent pattern)
- [ ] **F2.9** — `backend/api/routes/query.py` `/query/stream` wire(2nd site per ADR-0020 precedent pattern)

### D. Settings(6 NEW knobs,defaults per Chris AskUserQuestion picks)
- [x] **F2.10** — `backend/storage/settings.py` 6 NEW knobs — **DONE 2026-05-25 D1 cont 2**:
  ```python
  enable_parent_doc_retrieval: bool = False              # Q4 Recommended ✅
  parent_doc_section_depth_offset: int = 1               # Q2 Recommended ✅
  parent_doc_top_k: int = 1                              # Q1 Recommended ✅
  parent_doc_max_tokens_per_parent: int = 4000           # Q3 proposed locked ✅
  parent_doc_max_chunks_per_parent: int = 50             # safety cap ✅
  parent_doc_fallback_to_doc_on_shallow: bool = True     # shallow section_path handling ✅
  ```

### E. Observability
- [x] **F2.11** — Langfuse stage `generation.parent_doc_retrieval` wired — **DONE 2026-05-25 D1 cont 3**(per ADR-0020 precedent — stage name defined as `_STAGE_NAME` constant in `backend/generation/parent_doc_retriever.py` + `emit_stage_metadata` invocation in `_emit_parent_doc_stage` helper with `duration_ms` + `requested_anchors` + `parents_fetched` + `siblings_aggregated` + `truncated_count` + `skipped_shallow_count` metadata;**no `observe.py` modification needed** — `emit_stage_metadata` accepts arbitrary stage name parameter,matches existing context_expander stage pattern per Karpathy §1.2 simplicity)
- [ ] **F2.12** — `frontend/app/debug/[traceId]/page.tsx` V6 Debug View 9→10 stages(per Q5 Option A — explicit insert「Parent-Document Retriever」stage card between Context Expander + CRAG):
  - [ ] **F2.12a** — Observation-name prefix add in `STAGE_DEFS` array(`generation.parent_doc_retrieval`)
  - [ ] **F2.12b** — Per-stage data display key/value list(stats keys:`requested_anchors` / `parents_fetched` / `siblings_aggregated` / `truncated_count` / `skipped_shallow_count`)
  - [ ] **F2.12c** — H7 self-verify per CLAUDE.md §3.2.1 + §5.7 — open mockup `ekp-page-debug.jsx`(if exists)或 V6 Debug View 既存 stage cards 對住 typography / token / layout align(ADR-0020 precedent reuse)

### F. Tests
- [x] **F2.13** — NEW `backend/tests/test_parent_doc_retriever.py` 14 unit cases — **DONE 2026-05-25 D1 cont 3 — 14/14 pass 1.06s**(F2.13e cross-doc verified implicitly via F2.13b + F2.14a OData filter doc_id clause;F2.13i feature flag scope moved to pipeline integration layer per architectural split — retriever assumes caller has checked flag):
  - [x] **F2.13a** — Happy path:1 anchor → parent ["DCE Document", "§8: Integration Scenarios"] → 6 siblings aggregated ✅ via `test_happy_path_single_anchor_aggregates_parent_siblings`
  - [x] **F2.13b** — Multi-anchor dedupe(`parent_doc_top_k=2`):2 anchors share parent → `fetch_mock.await_count == 1` ✅ via `test_multi_anchor_dedupe_fetches_shared_parent_once`
  - [x] **F2.13c** — Section depth fallback:shallow `section_path=["DocOnly"]` + flag=True → parent=["DocOnly"] / flag=False → skipped ✅ via 2 cases(`test_shallow_section_path_falls_back_to_top_segment_with_flag_on` + `test_shallow_section_path_skipped_with_flag_off`)
  - [x] **F2.13d** — Token budget truncation:`max_tokens=20` + 4×40-char siblings → tail-drop + `truncated=True` ✅ via `test_token_budget_truncates_with_tail_drop`;+ degenerate single-huge-sibling preserved ✅ via `test_token_budget_includes_first_sibling_even_if_over_budget`
  - [x] **F2.13e** — Cross-doc boundary ✅ covered implicitly via `test_multi_anchor_dedupe`(different `doc_id` → separate parent_lookup keys → separate fetches)+ `test_filter_combines_kb_doc_enabled_and_section_any_clauses`(W26 F2.14a verifies `doc_id eq` clause in OData filter at leaf primitive layer)
  - [x] **F2.13f** — Empty input:`reranked_chunks=[]` → empty result + zero stats + no fetch ✅ via `test_empty_input_returns_empty_result_and_zero_stats`
  - [x] **F2.13g** — Lookup miss:Azure Search returns 0 hits → anchor passthrough + `stats.parents_fetched=0` ✅ via `test_lookup_miss_returns_anchor_unchanged`
  - [x] **F2.13h** — Network error:fetch raises `RuntimeError("Azure 503")` → graceful + anchor preserved ✅ via `test_network_error_falls_back_gracefully`
  - [⏭️] **F2.13i** — Feature flag off:`enable_parent_doc_retrieval=False` scope deferred to pipeline integration tests(F2.6-F2.9)— retriever module assumes caller has checked flag per Karpathy §1.2 simplicity(retriever doesn't read Settings;separation of concerns)
  - [x] **F2.13j** — Coexist with Context Expander Q6 Both on:non-anchor chunks pass through with `expanded_text` preserved ✅ via `test_non_anchor_chunks_passthrough_with_expanded_text_preserved`
  - [x] **F2.13k** — Citation invariant preservation:`Citation.chunk_text` unchanged(anchor `chunk_id` + `chunk_text` intact;new `parent_section_text` key added for `prompt_builder` dispatch chain)✅ via `test_citation_invariant_anchor_chunk_id_and_text_preserved`
  - [x] **F2.13 extra** — Missing `doc_id` ✅ + Missing `section_path` ✅ + `no_aggregation` classmethod ✅(3 additional cases beyond plan baseline — defensive edge case coverage)
- [x] **F2.14** — NEW `backend/tests/test_hybrid_section_path.py`(separate file per D1.13 surgical;not extending `test_hybrid_searcher_image_low_value.py`)— **DONE 2026-05-25 D1 cont 2 — 11/11 pass 0.89s**:
  - [x] **F2.14a** — OData filter syntax correctness(`section_path/any(s: s eq '<segment>')` joined `and`)✅ via `test_filter_combines_kb_doc_enabled_and_section_any_clauses`
  - [x] **F2.14b** — OData escaping(`Scenario A's intro` → `Scenario A''s intro` double single quote)✅ via `test_odata_single_quote_escaped_doubled`
  - [x] **F2.14c** — `chunk_index ASC` ordering verified ✅ via `test_payload_uses_orderby_chunk_index_asc`
  - [x] **F2.14d** — Hard cap `parent_doc_max_chunks_per_parent=50` enforced ✅ via `test_payload_top_uses_max_chunks_cap` + `test_payload_default_max_chunks_is_50`
  - [x] **F2.14e** — Empty input guards(empty parent_path / empty doc_id)✅ via 2 additional cases
  - [x] **F2.14f** — Response shape transform + `@search.*` system field strip ✅ via `test_response_transformed_to_hybrid_search_hits`
  - [x] **F2.14g** — Dynamic index_name per kb_id per ADR-0018 invariant ✅ via `test_url_uses_dynamic_index_name_per_kb_id`
- [ ] **F2.15** — `pytest tests/test_parent_doc_retriever.py tests/test_hybrid.py -v` pass(NEW ~15 + extension ~5 = ~20 cases)
- [ ] **F2.16** — `pytest tests/` full regression — count **≥ 1024 baseline + ~20 NEW** = **~1044+**(BUG-025 baseline preserved per G6 hard gate)
- [ ] **F2.17** — `mypy --strict --explicit-package-bases generation/parent_doc_retriever.py retrieval/hybrid.py` clean(touched code only per Karpathy §1.3 surgical;W25 CO_W25_mypy_strict_debt 11 pre-existing errors out of scope)
- [ ] **F2.18** — `ruff check generation/parent_doc_retriever.py retrieval/hybrid.py tests/test_parent_doc_retriever.py` clean

### G. Re-eval — W26 F2 → F3 gate evidence
- [ ] **F2.19** — Restart uvicorn + `/health` 200(6 NEW Settings loaded)+ env var override `ENABLE_PARENT_DOC_RETRIEVAL=true`
- [ ] **F2.20** — Re-run RAGAs `POST /eval/run` eval_set_id=`eval-set-v0-w25-supplement` same 13 queries as F1 baseline
- [ ] **F2.21** — Capture per-query metadata:retrieved anchor chunk + parent siblings count + parent_section_text length + truncated flag(for delta diagnostic)
- [ ] **F2.22** — Write `docs/01-planning/W26-eval-driven-retrieval-tuning/parent-doc-metrics-W26-D{N}.md`:
  - [ ] **F2.22a** — Per-query metrics delta vs F1 baseline(faithfulness / answer_relevancy / context_precision / context_recall)
  - [ ] **F2.22b** — Per-query chunk_id list + parent sibling count diagnostic
  - [ ] **F2.22c** — Aggregated delta + interpretation(recall ↑ expected per parent-doc 解 enumeration scope;faithfulness 觀察是否 holds)
  - [ ] **F2.22d** — Q-W25-I07「show me all the Integration scenarios」qualitative review:named scenarios count(was 1 post BUG-025;target ≥ 3 — 5 ideal)+ chunk #8 §3.1 leak check(parent-doc 是否 reduce off-topic content)
  - [ ] **F2.22e** — Q-W25-I02 + Q-W25-I03 + Q-W25-I04 + Q-W25-I05 + Q-W25-T04(5 failed-cohort F1 queries with `context_recall=0`)review:improvement quantified
- [ ] **F2.23** — Settings tuning iteration log if RAGAs delta inconclusive(per R3 — max 3 iterations of `parent_doc_top_k` 1→2→3 OR `parent_doc_max_tokens_per_parent` 4000→6000→2000 sweep before STOP and ask Chris)

### H. F2 → F3 gate decision(MUST surface to Chris before F3 active flip)
- [ ] **F2.24** — AskUserQuestion Chris pick — **gate criteria** `context_recall` improvement ≥ TBD pp on 5 failed-cohort queries + `faithfulness` regression ≤ TBD pp(grounded in F2 D{N} parent-doc delta data per Q3 + Q7 eval-driven discipline);**go/no-go decision** F3 proceed query expansion / W26 closeout PASS / iterate Setting values

## F3 — Step 2 query expansion experiment(conditional on F2 → F3 gate pass)

### Gate decision documentation
- [ ] **F3.1** — Document F2 → F3 gate decision outcome:pass(proceed F3)/ fail(close W26 with rationale)/ retry F2(loop back)

### Conditional execution(if gate pass)
- [ ] **F3.2** — Flip `Settings.enable_query_expansion=True` via env var override OR test harness(NOT default flip in W26 — measurement experiment only per Q5 locked decision)
- [ ] **F3.3** — Run RAGAs same queries set as F1/F2
- [ ] **F3.4** — Capture latency metric(P95 wall-clock per query — verify within ADR-0034 < 5s hard cap)
- [ ] **F3.5** — Write `docs/01-planning/W26-eval-driven-retrieval-tuning/step2-metrics-W26-D{N}.md` — F1 baseline → F2 threshold → F3 expansion 3-state delta + latency analysis
- [ ] **F3.6** — Per-query qualitative review:Q-W25-I07 named scenarios count(was 1 post BUG-025;target ≥ 3 — 5 ideal)

### Closeout direction(based on F3 result)
- [ ] **F3.7** — Decide closeout direction per Q4 locked decision:
  - [ ] **F3.7a** — F3 measurable improvement + 解 Q-W25-I07(≥ 3 scenarios named)→ W26 closeout PASS;後續 NEW Change candidate「`enable_query_expansion` default flip」
  - [ ] **F3.7b** — F3 measurable improvement 但 partial(< 3 scenarios named)→ W26 closeout PASS WITH PARTIAL CAVEAT + escalate brief §6 step 4 parent-doc retrieval ADR W27+ proposal
  - [ ] **F3.7c** — F3 no improvement / regression → W26 closeout PARTIAL + escalate same W27+ parent-doc ADR proposal

## F4 — Closeout(retro + cross-doc sync)

### Retro
- [ ] **F4.1** — `progress.md` Day-N retro section:
  - [ ] **F4.1a** — Scope delivered summary(F0-F3 完成 items)
  - [ ] **F4.1b** — Metric delta summary table(F1 baseline / F2 threshold / F3 expansion)
  - [ ] **F4.1c** — Decisions D1.* taken during phase(grouped + numbered)
  - [ ] **F4.1d** — Carry-overs explicit(BUG-026 / BUG-027 / W27+ parent-doc ADR per F3 closeout direction)
  - [ ] **F4.1e** — Lessons learned + 6 preventive controls PC1-PC6(BUG-025 postmortem)application status reflection
- [ ] **F4.2** — `plan.md` frontmatter `status: active → closed`(or `closed_partial` if F3 gate fail)

### Cross-doc sync
- [ ] **F4.3** — `docs/architecture.md` §3.6 line 411 之後 — 若 F2 ADR-0037 landed,加 inline-tagged amendment for rerank threshold mechanism
- [ ] **F4.4** — `docs/02-architecture/COMPONENT_CATALOG.md` C04 retrieval engine — status note update
- [ ] **F4.5** — `docs/01-planning/RISK_REGISTER.md` — 視乎 F2/F3 結果加 new risks OR close existing R7(image_weight too aggressive)
- [ ] **F4.6** — `docs/decision-form.md` — 視乎 Q-W26-* 新 OQ resolved
- [ ] **F4.7** — `docs/12-ai-assistant/01-prompts/01-session-start.md` §10 W26 row status + §11 CLOSED block with W26 retro summary

### Closeout commit
- [ ] **F4.8** — Closeout commit:`docs(planning): close W26-eval-driven-retrieval-tuning retro + cross-doc sync`
- [ ] **F4.9** — `git status` clean check post-commit
- [ ] **F4.10** — Phase gate verdict surface to Chris(PASS / PASS WITH PARTIAL CAVEAT / PARTIAL with escalation rationale per F3.7 decision)

## Verification gates(Phase-Level Hard Gates,per plan §3)

> Gate references updated 2026-05-25 D1 cont per F2 PIVOTED rewrite — item numbering shifted F2.* per new parent-doc scope。

- [x] **G1** — F1 baseline metrics collected(satisfied via F1.7 — `baseline-metrics-W26-D1.md` published 2026-05-25 D1)
- [x] **G2** — F2 ADR-0037 Accepted by Chris(satisfied via F2.2 — AskUserQuestion 4 Recommended picks + 4 batch-lock 2026-05-25 D1 cont)
- [ ] **G3** — F2 `context_recall` improvement ≥ TBD pp on 5 failed-cohort queries(rescoped from「precision improvement」per parent-doc workload signal — recall is the dominant per F1 evidence;satisfied via F2.22 + F2.24 AskUserQuestion gate decision)
- [ ] **G4** — F2 `faithfulness` regression ≤ TBD pp(rescoped from「recall regression」per parent-doc safety guard — parent section context may dilute LLM faithfulness if truncated;satisfied via F2.22 + F2.24)
- [ ] **G5** — F3 conditional execution decision documented(satisfied via F3.1)
- [ ] **G6** — Backend regression preserved(satisfied via F2.16 pytest count ≥ 1024)
- [ ] **G7** — mypy + ruff clean(satisfied via F2.17 + F2.18)
