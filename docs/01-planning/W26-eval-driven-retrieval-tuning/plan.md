---
phase: W26-eval-driven-retrieval-tuning
name: "Eval-driven retrieval quality tuning — RAGAs baseline → rerank score threshold → query expansion (Chris 3-step refinement)"
sprint_week: W26
start_date: 2026-05-25
end_date: TBD          # rolling per W20-W24 real-calendar collapse pattern ~3-7×
status: active
spec_refs:
  - architecture.md §3.1       # query pipeline + L2 CRAG
  - architecture.md §3.2       # vendor lock — Cohere Rerank v4.0-pro production
  - architecture.md §3.6       # hybrid retrieval + low_value
  - architecture.md §3.7       # query orchestration (ADR-0034 reformulator + RRF locus)
prior_phase: W25-image-association-deep-fix
trigger_memo: docs/09-analysis/rag_retrieval_quality_investigation_20260525.md
related_bugs: [BUG-025]    # silent-drop regression closed prior; W26 closes remaining quality gap per brief
---

# Phase W26 — Eval-Driven Retrieval Quality Tuning

> **Plan version**:1.0(initial)
> **Owner**:Chris(Tech Lead)+ AI(implementation)
> **Approved by**:Chris(chat 2026-05-25 — 「同意繼續 (a) commit BUG-025」+「kickoff W26+ phase plan」+ 3-step refinement framing 「Step 0 RAGAs baseline → Step 1 rerank threshold(prerequisite for Step 2)→ Step 2 query expansion gated on Step 1 + eval」)
> **Trigger memo**:`docs/09-analysis/rag_retrieval_quality_investigation_20260525.md`(user-authored investigation brief 2026-05-25 — mid BUG-025 V6 verify cycle surfaced enumeration query quality gap re-framing)

## 1. Scope

### 1.1 Trigger context(per investigation brief)

BUG-025 closeout(commit `4365edb` 2026-05-25 same-day)closed silent-drop regression(`_apply_low_value_post_filter` asymmetric drop → symmetric deboost — 0 citations → 3 citations measurable for Q-W25-I07)。**剩低 quality gap**(5 scenarios 中只 1 named explicitly + 1 topically-off chunk #8 §3.1 cited + control query 仍 work)經 brief 重新框定為:

- **NOT EKP-unique bug**:Dify 用 Cohere v4.0-pro reranker 同 query 都 fail「I'm not sure about that」→ 「enumeration query × 定長 chunking + top-k retrieval」嘅本質 mismatch,非 implementation 細節
- **3 個 separate layer 問題**(brief §2)— problem 1 content recall/precision(本 phase 對焦)+ problem 2 image relevance(out of scope)+ problem 3 UI count(BUG-026 candidate,out of scope)
- **核心方法論 critical insight**(brief §4)— 「冇 baseline 數字下面三個都係盲調」+「一次只郁一個旋鈕」eval-driven 紀律,**呢個 W26 phase 嘅唯一可行路徑**

### 1.2 Chris 3-step refinement(narrower than brief §6 full list)

| Step | Brief 對應 | 屬性 | 為何呢個次序 |
|---|---|---|---|
| **Step 0** RAGAs baseline measurement | §6 step 1 | 🟢 prerequisite(無得跳)| 無 baseline → 後面 1 + 2 嘅 eval delta 冇 reference,變盲調 — 重蹈 W25 D4 mis-diagnosed framing 嘅 detection gap pattern(per BUG-025 postmortem PC1 preventive control)|
| **Step 1** Parent-document retrieval(**PIVOTED 2026-05-25 D1 per F1 empirical refutation** — ORIGINAL「rerank score threshold」refuted by Cohere v4.0-pro score distribution analysis;see §7 Plan Changelog 2026-05-25 D1 entry)| §3 方向 E + §6 step 4 | 🟡 trigger H1(retrieval pipeline architectural change — new step)| Brief §3 方向 A premise(「排第 4/5 低分 chunk 照入」)empirically refuted by W26 F1 threshold-probe(`P25=0.83 / min=0.67 / max=0.97` — Cohere scores cannot differentiate failed vs passed queries on enumeration queries;Q-W25-I01 PASSED min 0.67 = Q-W25-T04 FAILED min 0.67 same-score-opposite-outcome inversion)。Chris pivot pick (C) AskUserQuestion 2026-05-25 D1 → brief §6 step 4 escalation:**section_path-based runtime aggregation post-rerank**(Tier 1 ceiling architecturally targeting the「enumeration query × top-K factoid retrieval」mismatch per brief §1「NOT EKP-unique — Dify same query also fails」)。ADR-0037 Accepted 2026-05-25 D1 cont with 4 critical Qs Recommended picks + 4 proposed defaults batch-locked;F2 implementation gate open。|
| **Step 2** Query expansion enable + eval | §3 方向 B implied(ADR-0034 framework already exists)| 🟢 conditional(gated on Step 1 + eval delta)| ADR-0034 框架已存,`enable_query_expansion: bool = False` default — Step 2 = flip flag for measurement experiment(NOT default flip),量 step 2 RAGAs delta;若 measurable improvement → 後續 sprint 考慮 default flip(自己 NEW Change/Phase);若 no improvement → close W26 with rationale 「query expansion not helpful at this point」|

### 1.3 Out of scope(deferred,per brief §2 separate layers + Chris pick narrower scope)

- **Image relevance**(problem 2 — `attach_neighbour_images` 純位置鄰近,brief §3 方向 C 調參 / 🟡 multimodal embedding 根治)→ W27+ separate phase / NEW BUG-027 candidate
- **UI count discrepancy**(problem 3 — `chat/page.tsx` 3 套計數語意 mismatch,brief §3 problem 3 deterministic frontend bug)→ BUG-026 candidate(Sev3/Sev4 cosmetic,separate workflow per PROCESS.md §4)
- **Parent-document / section-level retrieval**(brief §3 方向 E,§6 step 4)— 🟡 H1 architectural change;Tier 1 ceiling option for「show me all」根治;**若 W26 Step 2 仍唔解 enumeration query** → STOP and ask + NEW ADR phase candidate(W27+)
- **Query intent routing**(brief §3 方向 F)— 🟡 H1 NEW component;留 W26 Step 2 結果決定
- **Multimodal embedding** for query↔image relevance(brief §3 方向 G)— 🟡 H2 NEW vendor;Tier 2 territory
- **`image_weight` empirical tuning**(0.7 → 0.5 / 0.8 / 0.9 per F6 verify)— ADR-0035 R7 risk preserved 但 W26 唔調(eval-driven,需要 baseline + 1-旋鈕 紀律,優先 step 0 + 1 + 2)
- **L3 routing 觸發**(W5 D2 Gate 2 PARTIAL PASS verdict — 未觸 STRONG PASS upgrade)— W26 query expansion 屬 retrieval-side recall 改善,**唔同** L3 routing concept

### 1.4 Sprint week origin

**W19+ rolling JIT**(per CLAUDE.md §10 R1 + session-start.md §10 W26+ row);呢個 phase **唔喺 architecture.md §6.1 原 W1-W12 sprint 表內** — 屬 W25 closeout 觸發嘅 quality-tuning continuation(類似 W17 beta hardening / W22 frontend rebuild / W24a-c Wave C splits / W25 image-association-deep-fix 嘅 rolling 性質)。

---

## 2. Deliverables

### F0 — Kickoff(plan + checklist + progress + R6 grep verify)

- **Spec ref**:CLAUDE.md §10 R1 + R6
- **H1 trigger**:否(governance only)
- **Acceptance criteria**:
  1. `docs/01-planning/W26-eval-driven-retrieval-tuning/{plan.md,checklist.md,progress.md}` committed
  2. R6 pre-active-flip 5-step recursive grep verification at Day 0 — plan-text references catch upfront(see §7 Plan Changelog Day 0 entry)
  3. session-start.md §10 timeline row added(W26 active status);§11 BUG-025 CLOSED block 仍 retained 作 W26 context handoff
- **Effort estimate**:~2-3h(Day 0)
- **Owner**:AI

### F1 — Step 0 RAGAs baseline measurement(Chris Step 0)

- **Spec ref**:`architecture.md §3.1` + Brief §4 eval-driven methodology + Brief §6 step 1
- **H1 trigger**:否(measurement only,no code change)
- **OQ deps**:無新 OQ;**R8 prerequisite**(per §4 R1 risk)— Azure OpenAI judge key + Cohere production-equivalent reranker key 是否可用 / 是否需要 Plan B(see §4 R1 mitigation)
- **Acceptance criteria**:
  1. **R8 prerequisite gate**(STOP and ask before code if blocked):
     - (a) Azure OpenAI judge key available in dev / personal Azure dev tier(per ADR-0017 Plan B (c) precedent W25 F4 deferred reason)
     - (b) Cohere v4.0-pro production reranker key(NOT just `cohere: not_configured` Azure semantic ranker fallback — brief §4 「production-equivalent reranker」 strict reading)
     - 兩者其一 unavailable → STOP and ask Chris before F1 active flip
  2. Baseline measurement script `backend/eval/scripts/w26_baseline_measure.py`(或 reuse existing `make_ragas_evaluator` 經 `/eval/run` endpoint)— run RAGAs 4-metric(faithfulness / answer_relevancy / context_precision / context_recall)on:
     - **Failed query**:Q-W25-I07「show me all the Integration scenarios」(KB `sample-document-with-image-1`)
     - **Control queries**(2-3 個):`what is high level architecture` + 1-2 個 `eval-set-v0.yaml` baseline samples(targeted query class)
     - **Eval-set-v0-w25-supplement.yaml 13 queries subset**(若 R8 prerequisite green + Azure budget allow;若 R8 partial → focus failed query + control 2-3 個 minimum)
  3. Output:`docs/01-planning/W26-eval-driven-retrieval-tuning/baseline-metrics-W26-D1.md` — markdown report containing:
     - Per-query metrics(faithfulness / answer_relevancy / context_precision / context_recall)
     - Per-query retrieved-chunk count + chunk_id list(diagnostic)
     - Aggregated table:**recall-dominant 定 precision-dominant**(per brief §4 step 1 framing)
     - Plain-text interpretation:「baseline 數據顯示 [recall / precision] 主導 → Step 1 / Step 2 邊個 旋鈕 priority」
- **Effort estimate**:~6-8h(R8 prerequisite resolve + eval run + analysis + report);real-calendar may extend if R8 partial
- **Owner**:AI(measurement run)+ Chris(若 R8 partial,提供 personal Azure tier credentials per ADR-0017 Plan B (c))

### F2 — Step 1 parent-document retrieval per ADR-0037(W26 active scope post-pivot 2026-05-25 D1)

> **Status**:**Active scope** post pivot 2026-05-25 D1。**ADR-0037 Accepted 2026-05-25 D1 cont** via Chris AskUserQuestion 4 critical Qs Recommended picks(Q4 Default OFF + Q1 top_k=1 + Q2 depth_offset=1 + Q6 Both on)+ Q3/Q5/Q7/Q8 proposed defaults batch-locked。**This F2 deliverable spec sources from ADR-0037 §Implementation Deliverables list — ADR is the source of truth, this spec is the phase-level orchestration**。

- **Spec ref**:`architecture.md §3.1` query pipeline(post-Context Expander insertion locus)+ `§3.5` ChunkRecord `section_path: list[str]` + `§3.6` Azure Search index schema(`section_path` `Collection(Edm.String)` filterable + facetable — zero schema change)+ Brief §3 方向 E + Brief §6 step 4
- **H1 trigger**:**是** — retrieval pipeline architectural change(new step between Context Expander + CRAG);ADR-0037 已 Accepted closes governance gate per CLAUDE.md §10 R5
- **OQ deps**:無新 OQ;F1 baseline metrics(`baseline-metrics-W26-D1.md`)serves as RAGAs delta reference for F2 measurement
- **Acceptance criteria**(7 categories — 對應 ADR-0037 §Implementation Deliverables):

  **A. ADR governance gate(satisfied 2026-05-25 D1 cont)**:
  1. ✅ `docs/adr/0037-parent-document-section-retrieval.md` Status: Accepted(Chris AskUserQuestion approved Q1 + Q2 + Q4 + Q6 Recommended picks;Q3/Q5/Q7/Q8 proposed defaults batch-locked)
  2. ✅ `docs/adr/README.md` index synced(row + footer next-NNNN 0037→0038)

  **B. Backend Parent-Document Retriever module**:
  3. NEW `backend/generation/parent_doc_retriever.py`(~200-250 lines)— `ParentSectionChunk` dataclass duck-typed `RetrievedChunk` / `ExpandedChunk` compatible;`async def aggregate_parent_sections(reranked_chunks, kb_id, searcher, *, ...) -> tuple[list[ParentSectionChunk], ParentDocStats]`;anchor selection(top-1 per `parent_doc_top_k=1`)+ section path dedup + batch fetch + chunk_index ASC concat + token budget truncation + cross-doc boundary respect + shallow `section_path` fallback to doc-level
  4. `backend/retrieval/hybrid.py` NEW method `fetch_chunks_by_section_path(parent_path: list[str], doc_id: str, kb_id: str) -> list[HybridSearchHit]` — OData filter `kb_id eq '...' and doc_id eq '...' and enabled eq true and section_path/any(s: s eq '<each segment>')` joined;OData escaping(double single quotes);order by `chunk_index ASC`;hard cap `parent_doc_max_chunks_per_parent`

  **C. Pipeline integration**:
  5. `backend/generation/prompt_builder.py` dispatch chain extended:`parent_section_text > expanded_text > chunk_text`
  6. `backend/generation/crag.py` wire parent-doc step between Context Expander + CRAG grade(flag-gated;per Q6 Both on coexistence policy)
  7. `backend/api/routes/query.py` `/query` happy path + `/query/stream` 2 sites(per ADR-0020 precedent pattern)

  **D. Settings(6 NEW knobs,defaults per Chris AskUserQuestion picks)**:
  8. `backend/storage/settings.py`:
     ```python
     enable_parent_doc_retrieval: bool = False              # Q4 Recommended
     parent_doc_section_depth_offset: int = 1               # Q2 Recommended
     parent_doc_top_k: int = 1                              # Q1 Recommended
     parent_doc_max_tokens_per_parent: int = 4000           # Q3 proposed locked
     parent_doc_max_chunks_per_parent: int = 50             # safety cap
     parent_doc_fallback_to_doc_on_shallow: bool = True     # shallow section_path handling
     ```

  **E. Observability**:
  9. `backend/observability/observe.py` NEW stage name `generation.parent_doc_retrieval`
  10. `frontend/app/debug/[traceId]/page.tsx` V6 Debug View 9→10 stages(per Q5 Option A explicit insert)— observation-name prefix in `STAGE_DEFS` + key/value render in stage card(per ADR-0020 precedent)

  **F. Tests**:
  11. NEW `backend/tests/test_parent_doc_retriever.py` ~15 unit cases — happy path / multi-anchor dedupe / shallow section fallback / token budget truncation / cross-doc boundary / empty input / lookup miss / network error graceful / flag-off no-op / Context Expander interaction / Citation invariant preservation
  12. `backend/tests/test_hybrid.py` extension — `fetch_chunks_by_section_path` cases(filter syntax + escaping + ordering + cap)
  13. `pytest tests/` post-W26 count **≥ 1024 + ~15 NEW + ~5 hybrid extension cases = ~1044+**(BUG-025 baseline 1024 preserved per G6)
  14. `mypy --strict --explicit-package-bases generation/parent_doc_retriever.py retrieval/hybrid.py` clean(touched code only per Karpathy §1.3 surgical;pre-existing strict debt out of scope per W25 CO_W25_mypy_strict_debt)
  15. `ruff check` clean on touched files

  **G. RAGAs eval — W26 F2 → F3 gate evidence**:
  16. Restart uvicorn + `/health` 200(new Settings loaded)
  17. Re-run RAGAs on same 13-query supplement(W26 F1 baseline cohort)with `enable_parent_doc_retrieval=True` env override
  18. Output `docs/01-planning/W26-eval-driven-retrieval-tuning/parent-doc-metrics-W26-D{N}.md`:
      - 13-query metrics delta(faithfulness / answer_relevancy / context_precision / context_recall)vs F1 baseline
      - Per-query chunk_id list + parent sibling count diagnostic(verify parent siblings appear)
      - Aggregated delta + interpretation
      - Q-W25-I07 qualitative review:named scenarios count(was 1 post BUG-025;target ≥ 3 — 5 ideal)+ chunk #8 §3.1 leak check
  19. Setting tuning iteration log if RAGAs delta inconclusive(per R3 — max 3 iterations of `parent_doc_top_k` / `parent_doc_max_tokens_per_parent` sweep before STOP and ask Chris)

  **H. F2 → F3 gate decision(MUST surface to Chris before F3 active flip)**:
  20. AskUserQuestion Chris pick — **gate criteria** `context_recall` improvement ≥ TBD pp on 5 failed-cohort queries(per F1 D1 finding 5/13 failed)+ `faithfulness` regression ≤ TBD pp(grounded in parent-doc D{N} delta data)+ **go/no-go decision** F3 proceed query expansion / W26 closeout PASS / iterate Setting values

- **Effort estimate**:~16-20h(B+C ~6h + D 1h + E 3h + F tests 5h + G eval 4h + H gate 1h);real-calendar collapse 1-2 sessions per W22-W25 AI compression pattern
- **Owner**:AI(implementation + tests + eval)+ Chris(F2 → F3 gate AskUserQuestion pick)

### F3 — Step 2 query expansion experiment(Chris Step 2,gated on F2)

- **Spec ref**:`architecture.md §3.7` + ADR-0034(framework already exists)+ Brief §3 方向 B implied
- **H1 trigger**:**否**(`enable_query_expansion` 已存 flag,W26 只 flip for measurement experiment,**NOT** flipping default;若 measurable improvement → 後續 NEW Change/Phase decide default flip。Per Karpathy §1.2 simplicity 唔同時 lock default flip)
- **OQ deps**:**F2 必須 pass**(per Chris ordering + brief §4 step 2 gating)
- **F2 → F3 gate condition**(must surface to Chris for approval before F3 active flip):
  - Precision improvement(F2 → F1 delta)≥ TBD pp(per Chris pick)
  - Recall regression(F2 → F1 delta)≤ TBD pp(per Chris pick)
  - 兩者其一不達 → **STOP and ask Chris**:F3 skip(close W26)/ F2 re-tune threshold and retry / F3 proceed despite gate fail(documented rationale)
- **Acceptance criteria**(若 F2 → F3 gate pass):
  1. F3 run RAGAs eval with `Settings.enable_query_expansion=True`(env var override OR test harness flip)on same queries set
  2. Output:`docs/01-planning/W26-eval-driven-retrieval-tuning/step2-metrics-W26-D{N}.md` — F1 baseline → F2 threshold → F3 expansion 3-state delta
  3. ADR-0034 framework unchanged(no amendment in W26 — F3 屬 measurement experiment,**NOT** default flip);若 F3 measurable improvement 觸發後續 NEW Change 考慮 default flip 屬 separate scope
  4. **Decide closeout direction** based on F3 result:
     - **F3 measurable improvement + 解 Q-W25-I07** → W26 closeout PASS;後續 NEW Change candidate「`enable_query_expansion` default flip」
     - **F3 measurable improvement 但 仍 partial**(Q-W25-I07 仍 < 3 scenarios named) → W26 closeout PASS WITH PARTIAL CAVEAT + escalate brief §6 step 4 parent-doc retrieval ADR proposal W27+
     - **F3 no improvement / regression** → W26 closeout PARTIAL + brief §6 step 4 parent-doc retrieval ADR proposal escalate(同上)
- **Effort estimate**:~4-6h(eval run + analysis + closeout direction decision)
- **Owner**:AI(eval run + analysis)+ Chris(gate decision + closeout direction)

### F4 — Closeout(retro + cross-doc sync)

- **Spec ref**:CLAUDE.md §10 R3-R5 + PROCESS.md §3.4 + brief §6 step 4 escalation if needed
- **H1 trigger**:否(governance)
- **Acceptance criteria**:
  1. `progress.md` Day-N retro section:scope delivered / metric delta summary / decisions / carry-overs / next-phase candidates
  2. `plan.md` frontmatter `status: active → closed`(or `closed_partial` if F3 gate fail)
  3. Cross-doc sync:
     - `docs/architecture.md` §3.6 line 411 後 — 若 F2 ADR-0037 landed,加 inline-tagged amendment(rerank threshold mechanism)
     - `docs/02-architecture/COMPONENT_CATALOG.md` C04 retrieval engine — status note update
     - `docs/01-planning/RISK_REGISTER.md` — 視乎 F2/F3 結果加 new risks 或 close existing R7(image_weight too aggressive)
     - `docs/decision-form.md` — 視乎 Q-W26-* 新 OQ resolved
     - `docs/12-ai-assistant/01-prompts/01-session-start.md` §10 W26 row status + §11 CLOSED block
  4. Carry-overs explicit in retro:**BUG-026**(UI count problem 3)+ **BUG-027**(image relevance problem 2)+ **W27+ parent-doc retrieval ADR**(if F3 gate fail OR PARTIAL)
- **Effort estimate**:~3-5h
- **Owner**:AI(draft retro)+ Chris(approval)

---

## 3. Acceptance Criteria(Phase-Level Hard Gates)

| # | Criterion | Pass Condition | Verify Path | Hard Gate? |
|---|---|---|---|---|
| G1 | **F1 baseline metrics collected** | Q-W25-I07 + control queries RAGAs 4-metric documented in baseline-metrics report | F1 acceptance | **Yes** |
| G2 | **F2 ADR-0037 status Accepted** | Chris approval via chat/AskUserQuestion | F2 D1 review | **Yes** |
| G3 | **F2 `context_recall` improvement on failed-cohort**(rescoped 2026-05-25 D1 cont per F2 PIVOTED — was「precision improvement」under ORIGINAL rerank-threshold scope;parent-doc workload signal = recall is dominant per F1 5/13 `context_recall=0.00` finding)| `context_recall` delta on 5 failed queries(I02 + I03 + I04 + I05 + T04)≥ TBD pp;target ≥ 3/5 lift to non-zero | F2.22 + F2.24 AskUserQuestion gate | **Yes** |
| G4 | **F2 `faithfulness` regression ≤ TBD pp**(rescoped 2026-05-25 D1 cont — was「recall regression」under ORIGINAL scope;parent-doc safety guard = parent section may dilute LLM faithfulness if section too broad / truncated)| `faithfulness` delta vs F1 baseline 0.9851 ≥ -TBD pp(NOT worse beyond tolerance)| F2.22 + F2.24 AskUserQuestion gate | **Yes** |
| G5 | **F3 conditional execution decision** | F2 → F3 gate explicitly evaluated(pass / fail / retry — documented)| F3 D1 gate decision | **Yes** |
| G6 | **Backend regression preserved** | `pytest tests/` post-W26 count ≥ 1024(BUG-025 baseline)| F2/F3 verify | **Yes** |
| G7 | **mypy + ruff clean on touched code** | both clean | F2 verify | **Yes** |

---

## 4. Risks(Phase-Specific)

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| **R1** | **R8/Azure-key-bound prerequisite blocks F1** — Azure OpenAI judge key OR Cohere production reranker key 唔可用 → RAGAs eval cannot run | **Med-High**(per W25 F4 deferred precedent — same blocker pattern)| **High**(Block all of W26 — 無 baseline 後面冇得做)| F1 acceptance #1 explicit prerequisite gate:R8 blocked → STOP and ask Chris before F1 active flip;Plan B options:(a) Chris 提供 personal Azure dev tier credentials per ADR-0017 Plan B (c) precedent W25 F4 deferred;(b) defer W26 W27+ when Track A IT cred lands(W16 F1 dependency);(c) limited scope F1 — run on control queries 只(若 partial keys 可用)+ ML-judge skip faithfulness/answer_relevancy(僅 context_precision/recall via retrieval-only eval — without LLM judge);**首選 (a) Plan B (c) — Chris 已 W25 F4 mention 過 R8/Azure-key-bound umbrella precedent** |
| **R2** | **Cohere fallback to Azure semantic ranker** in dev环境 → not production-equivalent reranker for baseline measurement → numbers 不適用 production | Med | Med-High | F1 acceptance #1 (b) explicit:Cohere v4.0-pro production reranker 必要 — fallback to Azure semantic ranker = invalid baseline;若 Cohere not_configured 持續 → STOP and ask per R1 mitigation (a) Plan B (c) |
| **R3** | **Parent-doc Settings tuning takes multiple eval iterations** — initial values(`parent_doc_top_k=1` / `section_depth_offset=1` / `max_tokens_per_parent=4000`)possibly wrong for EKP corpus enumeration query distribution(R3 rescoped 2026-05-25 D1 cont per F2 pivot — was 「rerank threshold floor value tuning」under ORIGINAL Step 1 scope) | Med | Med(latency to W26 closeout)| F2 acceptance #19 — Settings tuning iteration log;最多 3 次 iteration / setting sweep(`parent_doc_top_k` 1→2→3 OR `max_tokens_per_parent` 4000→6000→2000)然後 surface decisions to Chris;per ADR-0017 Decision-rule #5 ordered fallback precedent — 唔 retry forever |
| **R4** | **Query expansion latency budget overshoot** — F3 measurement may surface P95 > 5s hard cap per ADR-0034 | Low(已 cap 喺 ADR-0034 framework)| Med | F3 measurement script includes latency capture;若 P95 > 5s 喺 measurement env → F3 closeout direction = NOT recommended for default flip(separate concern from quality improvement signal) |
| **R5** | **Eval set noise** for failed query subset(small sample size)→ delta signal noisy / not statistically meaningful | Med-High(per W25 F4 deferred eval-set-v0-w25-supplement.yaml 13 queries premise — small sample)| Med | F1 acceptance #2 — minimum 2-3 control queries + Q-W25-I07 + eval-set-v0 subset(若 R8 OK)= aggregate cohort > 5 queries;若 noise too high → BUG-025 postmortem PC4「pre-phase regression baseline capture protocol」escalate W27+ work item |
| **R6** | **Pre-active-flip recursive grep verification miss** at Day 0 — plan-text references mis-aligned with actual code state | Low(per W23 F3 R6 recursive scope amendment + W25 D0 R6 catch precedent — formalized practice)| Med | F0 acceptance #2 — R6 grep verify before F1 active flip;cumulative findings logged in §7 Plan Changelog |
| **R7** | ~~F2 ADR-0037 governance scope creep~~ — **CLOSED 2026-05-25 D1 cont**:ADR-0037 Accepted 2026-05-25 D1 cont via Chris AskUserQuestion 4 Recommended picks(Q4 Default OFF + Q1 top_k=1 + Q2 depth_offset=1 + Q6 Both on)+ Q3/Q5/Q7/Q8 batch-lock;scope debate moot — parent-doc retrieval per F1 empirical refutation = clear H1 architectural change with ADR Accepted gate satisfied | ~~Low~~ closed | ~~Low~~ closed | N/A — historical reference preserved per R3 binding rule |
| **R8** | **F3 gate criteria 未 pre-defined** in plan(precision improvement ≥ TBD pp / recall regression ≤ TBD pp)→ F2 → F3 transition 時 surface decisions 而非 plan-locked | Med | Low | 由 design — F1 baseline metric 出 distribution 之後先 pick threshold + gate values;plan §3 G3 + G4 用 TBD 標明;F2 D6 RAGAs delta 之後 AskUserQuestion Chris pick gate values |

---

## 5. Day-by-Day Breakdown(rough — eval-driven 紀律 = iteration-heavy,calendar 估算保守)

| Day | Date(planned) | Focus | Deliverables targeted |
|---|---|---|---|
| D0 | 2026-05-25 | Kickoff — plan + checklist + progress + R6 grep verify | F0 meta |
| D1-D3 | 2026-05-26 ~ 2026-05-28 | F1 R8 prerequisite resolve + RAGAs baseline measure on Q-W25-I07 + control + eval-set-v0 subset | F1 |
| D1 cont | 2026-05-25 | **F2 PIVOTED governance** — ADR-0037 designed + drafted + Accepted via Chris AskUserQuestion(4 critical Qs + 4 batch-lock)+ plan §1.2/§2/§4/§5/§7/§8/§9 rewrite + checklist F2 rewrite + progress Day 1 cont entry — **DONE** | F2 governance(A acceptance gate)|
| D4-D7 | 2026-05-29 ~ 2026-06-03 | F2 implementation per ADR-0037 §Implementation Deliverables — `parent_doc_retriever.py` core(~250 LOC)+ `hybrid.py.fetch_chunks_by_section_path` extension + `prompt_builder` dispatch chain + `crag.py` + `query.py` flag-gated wire(2 sites)+ Settings 6 knobs + `observe.py` NEW stage + V6 Debug View 10-stage + `test_parent_doc_retriever.py` ~15 cases + re-eval RAGAs delta + Settings sweep iteration if inconclusive | F2(B-G acceptance) |
| D8 | 2026-06-04 | F2 → F3 gate decision(AskUserQuestion Chris pick gate values + go/no-go)| F2/F3 boundary |
| D9-D10 | 2026-06-05 ~ 2026-06-06 | F3 conditional execution — query expansion experiment + eval delta(if gate pass) | F3 |
| D11-D12 | 2026-06-07 ~ 2026-06-08 | F4 closeout retro + cross-doc sync + carry-overs | F4 |

**Real-calendar collapse note**:per W12-W18 / W20-W25 AI compression pattern(~3-7×),actual elapsed time **likely** ~3-6 calendar days(W25 ~1.5 days vs ~20 plan-day);呢個 plan 嘅 calendar 估算保守 envelope。**eval-driven iteration may extend** if R8 prerequisite resolve slow OR threshold tuning takes 3+ iterations。

---

## 6. Dependencies on Prior Phase

Carry-over from **W25-image-association-deep-fix retro**(per session-start.md §11「CLOSED by W25.5 BUG-025 Sev2 fix」block):

- **CO_W25_F4 LIVE RAGAs eval**(R8/Azure-key-bound)— **consumed by W26 F1**(W26 F1 = expanded scope of CO_W25_F4 across same 13 queries supplement + 2-3 control queries;closes the deferred F4 work item)
- **CO_W25_F6_expansion full 5-query manual user-test** — **consumed by W26 F1**(F1 baseline measurement substantially replaces F6 manual user-test via RAGAs automated metrics + retrieves per-query chunk lists)
- **BUG-025 postmortem PC1 preventive control**(retrieval-policy change → ≥ 5-query manual user-test taxonomy)— **W26 F2 ADR-0037 + F3 gate triggers PC1 application** — F1 RAGAs cohort(failed + control + eval-set-v0)≥ 5 queries satisfies PC1
- **BUG-025 postmortem PC2-PC6**(test naming honest about spec assumptions / ADR assumption-language review / pre-phase regression baseline / R14-style mis-diagnosed framing trigger / spec-implementation divergence detector)— **applied throughout W26**
- **R8 corp-proxy mitigation pattern**(ADR-0017,9 occurrences cumulative)— F1 prerequisite resolve 可能觸 Plan B (c) personal Azure dev tier(per W25 F4 deferred reason)
- **Pre-active-flip 5-step grep verification recursive scope**(per CLAUDE.md §10 R6 W23 F3 amendment + W22 D1+D6+D7+D8+D9 5-pattern catalog + W25 D0 R6 catch precedent)— **applies recursively to W26 plan-text itself**(本 plan 引用 `cohere.py:96-130` / `chat/page.tsx:1228+1797+2126` / brief §X / W25 D4 chunk references — F1 active flip 之前必 grep verify upfront,see Day 0 progress entry)
- **Smoke-user-deferred allowance**(W12-W18 / W20-W25 pattern)— W26 主要 backend + eval work,frontend 不變(無 H7 trigger)— smoke-user-deferred N/A

呢個 phase **唔依賴** Track A IT cred populate event(W16 F1)—— F1-F4 work 屬 AI-controllable backlog,類似 W17 / W25 beta-hardening parallel-track pattern。**唯一 dependency** = R8/Azure-key-bound for RAGAs eval(per R1 mitigation Plan B (c))。

---

## 7. Plan Changelog

| Date | Change | Reason | Approver |
|---|---|---|---|
| 2026-05-25 | Initial plan — Chris 3-step refinement scope:Step 0 RAGAs baseline → Step 1 rerank threshold(ADR-0037 — H1)→ Step 2 query expansion(gated on Step 1 eval delta);F0 + F4 governance;Out of scope = image relevance / UI count BUG-026 / parent-doc ADR W27+;7 risks R1-R8 catalogued | Chris chat 2026-05-25 「同意繼續 (a) commit BUG-025」+「kickoff W26+ phase plan」+ 3-step refinement framing | Chris |
| 2026-05-25 | **R6 pre-active-flip recursive grep verification** at Day 0 kickoff — **net zero contaminations**;5 grep targets all confirmed alignment with plan-text(`cohere.py:84` rerank async def + 5 existing `rerank_*` Settings + `docs/eval-set-v0*.yaml` files exist + `/eval/run`+`make_ragas_evaluator` 8-files reuse-path + ADR-0036 last used → 0037 next available)| R6 recursive scope catch upfront before F1 active flip;applied to plan-text 自己 per W25 cumulative empirical pattern | AI(R6 self-audit at Day 0)|
| 2026-05-25 D1 | **F1 RAGAs baseline + threshold probe empirical finding → MAJOR PIVOT**:Chris 3-step Step 1「rerank score threshold」approach **empirically refuted**。F1 baseline `recall_at_5=0.8744` + `faithfulness=0.9851` + 5/13 queries `context_recall=0.00`(recall-dominant)+ threshold probe 25 scores show Cohere v4.0-pro distribution P25=0.83 / P50=0.90 / P75=0.91 / min=0.67 / max=0.97 + Q-W25-I01(PASSED control)min score 0.67 vs Q-W25-I02(FAILED context_recall=0)min 0.88 → **threshold cutoff cannot differentiate failed vs passed queries**(Cohere confidently rates wrong chunks high for enumeration queries / passes have low-score chunks too)。Brief §3 方向 A premise「排第 4/5 低分 chunk 照入 context」**empirically refuted** — Cohere 排前 5 全 0.67-0.97 高分,問題唔係「低分 leak」而係「Cohere 對 enumeration query × top-k chunking 嘅本質 mismatch」(per brief §1 「NOT EKP-unique bug — Dify same query also fails」)。**Chris pivot pick 2026-05-25 AskUserQuestion (C) parent-document retrieval ADR-0037** — brief §6 step 4 escalation activated。**F2 deliverable scope revised** from「Step 1 rerank score threshold」to「Step 1 parent-document / section-level retrieval(brief §3 方向 E 🟡 H1 Tier 1 ceiling)」— full F2 rewrite deferred next session(architectural design scope warrants fresh attention)| R6 critical refutation surfaced via 25-chunk probe;preserves Q1 locked decision「derive from F1 baseline distribution」discipline;preserves PC1-PC6 BUG-025 postmortem preventive controls(PC1 ≥ 5-query manual cohort satisfied at 13 queries;PC3 ADR assumption-language review = brief recommendation 0.3 magic refuted empirically) | Chris(pick C via AskUserQuestion)+ AI(F1 baseline+probe execution + this changelog entry)|
| 2026-05-25 D1 cont | **ADR-0037 designed + drafted + Accepted via Chris AskUserQuestion + F2 scope rewrite landed**(2nd session segment same calendar day):**(a)** Full ADR-0037 draft `docs/adr/0037-parent-document-section-retrieval.md` ~620 lines per CLAUDE.md §6 format(Context + 8-section Decision + 5 rejected Alternatives B-F + Consequences + References + Implementation Deliverables + Decision Log);**(b)** Chris AskUserQuestion 4 critical Qs 全 Recommended picks(Q4 Default OFF + Q1 top_k=1 + Q2 depth_offset=1 + Q6 Both on)+ Q3+Q5+Q7+Q8 proposed defaults batch-locked;**(c)** ADR Status flipped Proposed → Accepted + Decision Log section appended documenting picks;**(d)** `docs/adr/README.md` row + footer next-NNNN bump 0037→0038;**(e)** ADR + README atomic governance commit `4cdd1bc` (+631/-1);**(f)** this plan §1.2 Step 1 row revised(post-pivot scope reflects parent-doc retrieval per ADR-0037 active spec);**(g)** §2 F2 deliverable spec full rewrite(PIVOTED placeholder → 7-category 20-item active acceptance criteria sourced from ADR §Implementation Deliverables list — A governance gate satisfied + B retriever module + C pipeline integration + D 6 NEW Settings + E observability + F tests + G RAGAs eval + H F2 → F3 gate);**(h)** §4 R3/R6/R7 risks rescoped(R3 threshold iteration → parent-doc Settings sweep iteration;R6 already executed;R7 governance scope creep no longer relevant — ADR Accepted closes scope debate);**(i)** §5 Day-by-Day D4-D7 rescoped(was「ADR draft + threshold code」→ now「F2 impl + tests + re-eval」 since ADR draft+approval already complete);**(j)** §8 Locked Design Decisions extended with Q1-Q8 picks summary | Chris AskUserQuestion approval forms ADR Accepted gate;plan rewrite consumes ADR Implementation Deliverables list as F2 acceptance contract per R3 binding rule;Karpathy §1.3 surgical — 2-commit pattern(governance ADR atomic + planning rewrite atomic)preserves audit trail | Chris(4 Recommended picks)+ AI(ADR draft + plan rewrite + checklist rewrite + progress Day 1 cont entry)|

---

## 8. Locked Design Decisions(from Chris chat 2026-05-25 + brief)

| # | Question | Default(locked)| Rationale |
|---|---|---|---|
| **Q1** | F1 baseline measurement scope | **Q-W25-I07 + 2-3 control queries + eval-set-v0 subset**(若 R8 OK + Azure budget allow,extend to eval-set-v0-w25-supplement.yaml 13 queries)| Per brief §4 「對失敗 query 跑 context recall / precision」+ control queries 設 sanity check;eval-set-v0 baseline keeps continuity with W2 Gate 1 measurement |
| **Q2** | F2 ADR-0037 initial threshold value | **Derive from F1 baseline score distribution analysis**(NOT magic number 0.3 — brief §3 recommendation 但 grounding 需要 EKP-specific data)| Per BUG-025 postmortem PC3 preventive control「ADR review checkpoint for 『assumption』language」— grounded in empirical signal not hand-waved |
| **Q3** | F2 → F3 gate criteria(precision Δ + recall Δ thresholds)| **TBD per F2 D6 RAGAs delta**(AskUserQuestion Chris pick at F2 → F3 transition)| Initial guess attempt would violate eval-driven discipline brief §4(「冇 baseline 數字下面三個都係盲調」)— gate values 由 baseline + step 1 data decide |
| **Q4** | F3 gate fail handling | **Documented closeout direction**:**measurable improvement + 解 Q-W25-I07** → PASS;**measurable improvement 但 partial**(< 3 scenarios named) → PASS WITH PARTIAL CAVEAT + escalate brief §6 step 4 parent-doc ADR W27+;**no improvement / regression** → PARTIAL + escalate same W27+ | 3 closeout direction explicit upfront 避免 W26 末期 ambiguity;brief §6 step 4 escalation 屬 H1 ADR scope(Tier 1 ceiling) |
| **Q5** | F3 expansion default flip in W26? | **NO**(W26 = measurement experiment only via env var override OR test harness flip;若 F3 measurable improvement → 後續 NEW Change considers default flip — separate scope per Karpathy §1.2)| Avoid bundle 2 decisions(measurement + production default change)single phase;measurement signal 出來再 decide |
| **Q6**(ADR-0037 picks 2026-05-25 D1 cont)| F2 parent-doc Settings defaults | **6 knobs locked**:`enable_parent_doc_retrieval=False` / `parent_doc_section_depth_offset=1` / `parent_doc_top_k=1` / `parent_doc_max_tokens_per_parent=4000` / `parent_doc_max_chunks_per_parent=50` / `parent_doc_fallback_to_doc_on_shallow=True` | Chris AskUserQuestion 4 Recommended picks(Q4 Default OFF + Q1 top_k=1 + Q2 depth_offset=1 + Q6 Both on)+ Q3+Q5+Q7+Q8 proposed defaults batch-locked per ADR-0037 Decision Log |
| **Q7**(ADR-0037 batch-lock)| F2 → F3 gate criteria scoping | **TBD per F2 D{N} parent-doc RAGAs delta**(AskUserQuestion Chris pick at F2 → F3 transition based on measurement evidence — preserves Q3 eval-driven discipline) | Same rationale as Q3 — gate values derived from data not hand-waved |

---

## 9. Component Impact Map

| Component | Pre-W26 status | W26 impact | Post-W26 expected |
|---|---|---|---|
| **C04 Retrieval Engine**(`backend/retrieval/hybrid.py`)| ✅ Implemented(W2 baseline + W17 F1 multi-KB kb_id propagation + W25 BUG-025 symmetric deboost 2026-05-25)| **F2** NEW method `fetch_chunks_by_section_path(parent_path, doc_id, kb_id)` — OData filter via `section_path/any()` operator;chunk_index ASC ordering;hard cap `parent_doc_max_chunks_per_parent` | ✅ Implemented(extended;ADR-0037 reference)|
| **C05 Generation**(`backend/generation/parent_doc_retriever.py` NEW)| ❌ N/A pre-W26 | **F2** NEW module `~200-250 LOC` — `ParentSectionChunk` dataclass + `aggregate_parent_sections` async coroutine + anchor selection + section dedupe + batch fetch + token budget truncation + cross-doc boundary + shallow fallback | ✅ NEW component(ADR-0037 implementation core)|
| **C05 Generation**(`backend/generation/prompt_builder.py`)| ✅ Implemented(W3 baseline + W17 ADR-0020 `expanded_text` dispatch)| **F2** dispatch chain extension `parent_section_text > expanded_text > chunk_text` fallback chain | ✅ Implemented(extended;ADR-0037 reference)|
| **C05 Generation**(`backend/generation/crag.py` + `backend/api/routes/query.py`)| ✅ Implemented(W4 CRAG L2 + W17 ADR-0020 wire)| **F2** wire parent-doc step between Context Expander + CRAG grade(flag-gated);`/query` + `/query/stream` 2 sites per ADR-0020 precedent pattern | ✅ Implemented(extended)|
| **C04 Retrieval Engine**(`backend/storage/settings.py`)| ✅ Implemented(BUG-025 `retrieval_image_low_value_weight: float = 0.7`)| **F2** 6 NEW knobs(`enable_parent_doc_retrieval` + `parent_doc_section_depth_offset` + `parent_doc_top_k` + `parent_doc_max_tokens_per_parent` + `parent_doc_max_chunks_per_parent` + `parent_doc_fallback_to_doc_on_shallow`)— defaults per Chris AskUserQuestion picks | ✅ Implemented(extended) |
| **C07 Observability Stack**(`backend/observability/observe.py` + `frontend/app/debug/[traceId]/page.tsx`)| ✅ Implemented(W17 ADR-0020 V6 Debug View 9-stage)| **F2** NEW Langfuse stage name `generation.parent_doc_retrieval` + V6 Debug View 9→10 stages explicit insert(per Q5 Option A)| ✅ Implemented(extended) |
| **C06 Eval Framework**(`make_ragas_evaluator` via `/eval/run` endpoint)| ✅ Implemented(W17 F3 RAGAs 4-metric integrated)| F1 baseline measure DONE(2026-05-25 D1)+ F2 parent-doc re-run + F3 conditional re-run | ✅ Implemented(verified via heavy use)|
| **C05 / C04 query pipeline**(`backend/pipeline/query_pipeline.py` + ADR-0034 reformulator framework)| ✅ Implemented(W25 F3 ADR-0034 landed,`enable_query_expansion: bool = False` default off)| F3 measurement experiment(flag flip via env override OR test harness — **NOT** default flip in W26)| ✅ Implemented(no module change — flag flip for measurement only)|

**H7 design fidelity trigger**:**部分**(per Q5 ADR-0037 Option A explicit 10-stage V6 Debug View insert)— `frontend/app/debug/[traceId]/page.tsx` 加 NEW「Parent-Document Retriever」stage card;**唔涉及** mockup pages(`/chat` / `/dashboard` / `/kb/*` / `/settings` / `/users` 等)— V6 Debug View 系 admin observability surface,`references/design-mockups/` 對應 affordance preserved per ADR-0020 W17 precedent;F2 implementation 需 self-verify per CLAUDE.md §3.2.1 + §5.7 H7(open mockup `ekp-page-debug.jsx` 對住做 — stage card layout / typography / token alignment)。

---

**Lifecycle reminder**:呢份 plan locked after Day 0 kickoff commit landed(R3 binding rule)。重大 deviation(eg. ADR-0037 amendment / F3 gate criteria 重新框定 / scope add)入 §7 Plan Changelog;小 detail 變動(eg. effort estimate update)可直接 inline edit。
