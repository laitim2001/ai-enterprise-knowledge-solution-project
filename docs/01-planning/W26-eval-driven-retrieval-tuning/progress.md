---
phase: W26-eval-driven-retrieval-tuning
plan_ref: ./plan.md
checklist_ref: ./checklist.md
status: active
last_updated: 2026-05-25
---

# W26 — Progress

> Daily progress + closeout retro per PROCESS.md §3.4。
> Every commit must correspond to a Day-N entry mention(R2 binding rule)。

---

## Day 0 — 2026-05-25:Kickoff + R6 grep verify

### Trigger sequence

1. **BUG-025 closeout 2026-05-25**(commit `4365edb` pushed origin/main)— Sev2 silent-drop regression closed(0 citations → 3 citations measurable for Q-W25-I07);Sev2 postmortem 6 preventive controls PC1-PC6 published。
2. **Mid V6 user-eye verify cycle 2026-05-25** — Chris surfaced `docs/09-analysis/rag_retrieval_quality_investigation_20260525.md` user-authored investigation brief(2026-05-25)→ reframed remaining quality gap as **enumeration query × factoid-tuned pipeline architectural mismatch**(Dify same query also fails — NOT EKP-unique bug)。
3. **Chris 3-step refinement chat 2026-05-25** — narrower than brief §6 full list:**Step 0** RAGAs baseline → **Step 1** rerank score threshold(prerequisite — gates noise for Step 2)→ **Step 2** query expansion(gated on Step 1 + eval delta)。Image relevance / UI count BUG-026 / parent-doc ADR Tier 1 ceiling 留 W26 step 2 後 sprint scope。
4. **Chris explicit kickoff instruction 2026-05-25** —「kickoff W26+ phase plan」→ rolling JIT phase folder kickoff per CLAUDE.md §10 R1。

### Done

**1. Plan + checklist + progress kickoff**:
- `docs/01-planning/W26-eval-driven-retrieval-tuning/plan.md` v1.0(§1-§9 — Scope + Deliverables F0-F4 + Acceptance Criteria G1-G7 + 8 Risks R1-R8 + Day-by-Day + Dependencies + Plan Changelog + 5 Locked Design Decisions + Component Impact Map)
- `docs/01-planning/W26-eval-driven-retrieval-tuning/checklist.md`(F0.1-F0.10 + F1.1-F1.8 + F2.1-F2.16 + F3.1-F3.7 + F4.1-F4.10 + G1-G7 verification gates)
- `docs/01-planning/W26-eval-driven-retrieval-tuning/progress.md`(this file — Day 0 entry)

**2. R6 pre-active-flip recursive grep verification**(per CLAUDE.md §10 R6 + W23 F3 amendment + W25 D0 precedent)— **executed Day 0 — net zero contaminations**:

| Grep target | Result | Plan correction needed? |
|---|---|---|
| `backend/retrieval/reranker/cohere.py` rerank signature | `async def rerank` at line 84(brief §7 navigation table 84-130 + §2 narrative 96-130 ranges consistent — body cutoff vs full method)| ❌ No — plan §2 F2 reference within brief-cited range |
| `backend/storage/settings.py` existing `rerank_*` knobs | 5 existing(`cohere_rerank_model` / `voyage_rerank_model` / `zeroentropy_rerank_model` / `cohere_request_timeout_s` / `rerank_top_k: int = 5`)| ❌ No — NEW `rerank_score_threshold` adds clean(no naming collision)|
| `docs/eval-set-v0.yaml` + `eval-set-v0-w25-supplement.yaml` file existence | Both exist at `docs/` root | ❌ No — Q1 locked decision references correct |
| `/eval/run` + `make_ragas_evaluator` reuse-path | 8 files contain reference(`api/routes/eval.py` + `eval/ragas_evaluator.py` + `eval/orchestrator.py` + 5 test files)— reuse confirmed | ❌ No — F1.4 reuse-path correct |
| ADR registry — last used number | `0033-` / `0034-` / `0035-` / `0036-react-markdown-chat-answer-rendering.md` ✅ ADR-0037 is next available | ❌ No — F2.1 ADR-0037 naming correct |

**Net findings = zero contaminations + 5 confirmations**;plan-text clean,Day 0 kickoff governance complete(per W25 D0 R6 precedent — surface findings upfront avoid F1+ active-flip discovery)。

**3. Tasks created for W26 lifecycle**:
- BUG-025 tasks (#204-#209) all completed in prior session
- NEW W26 tasks pending creation via TaskCreate(F1-F4 phase milestones)

### Decisions(Day 0)

- **D0.1** — Phase folder name `W26-eval-driven-retrieval-tuning` adopted(per Chris explicit「kickoff W26+ phase plan」+ 「eval-driven」嘅 methodology focus + 「retrieval tuning」scope description)
- **D0.2** — Chris 3-step refinement narrower than brief §6 full list(per Chris explicit ordering insight:rerank threshold IS prerequisite for query expansion — uncovered methodological clarity > brief §6)。**F0-F4** 5 deliverables;**out of scope** explicitly enumerated in plan §1.3
- **D0.3** — F2 屬 🟡 H1 trigger ADR-0037(brief §3 標 🟢 Tier-1-safe 但 W25 cumulative governance precedent ADR-0033 + 0034 + 0035 + 0036 = retrieval scoring change 都寫 ADR — symmetric pattern over brief recommendation lean)
- **D0.4** — F1 R8 prerequisite gate explicit STOP-and-ask point(per BUG-025 postmortem PC1 + W25 F4 deferred precedent — Azure OpenAI judge key + Cohere production reranker key 兩者必要,fallback 唔 acceptable)
- **D0.5** — F3 W26 內 **NOT** default flip(measurement experiment via env var override only;若 measurable improvement → 後續 NEW Change considers default flip — separate scope per Karpathy §1.2 simplicity 唔 bundle 2 decisions)
- **D0.6** — F2 → F3 gate criteria TBD per F2 D6 RAGAs delta(AskUserQuestion Chris pick at transition — eval-driven discipline 唔 hand-wave initial values per brief §4 critical insight)
- **D0.7** — Single phase W26 covers F0-F4(NOT split W26a + W26b)— eval-driven iteration tight feedback loop;若 F3 closeout direction = PARTIAL/skip → W27+ candidate(parent-doc ADR)separate phase per rolling JIT

### Blockers

- ⚠️ **R8 potential prerequisite**(R1 plan risk)— Azure OpenAI judge key + Cohere v4.0-pro production reranker key availability。F1 R8 prerequisite gate(F1.1-F1.3)** must resolve before F1 active flip**;若 blocked → Plan B (c) Chris personal Azure dev tier credentials 必要(per W25 F4 deferred precedent + ADR-0017 amended)

### Carry-overs

無 — Day 0 kickoff scope clean。

### Commits

- `docs(planning): kickoff W26-eval-driven-retrieval-tuning + Chris 3-step refinement scope`(本 commit pending — plan + checklist + progress + session-start.md sync per F0.10 may bundle OR separate)

---

**End of Day 0 entry** — Kickoff done;F0.4-F0.8 R6 grep verify deferred to D1;F1 R8 prerequisite resolve 緊接 next。

---

## Day 1 — 2026-05-25:F1 baseline measurement + empirical pivot to parent-doc retrieval

### Trigger sequence

1. Chris explicit「kickoff W26+ phase plan」(post-W25 BUG-025 push)+「同意繼續 (a)」per session continuation
2. F1 R8 prerequisite gate diagnostic:`/health` reported `cohere: not_configured` but `make_reranker(get_settings())` confirmed CohereReranker created with aenter SUCCESS。Root cause = `/health._check_cohere:103` 用 `getattr(engine, "reranker", None)` 而 RetrievalEngine 內部係 `self._reranker`(private)— attribute access drift。**Actual Cohere v4.0-pro 一直 operational**;`/health` cohere status 屬 cosmetic observability misreport(post-W20 F2.1 extraction)— Chris pick (a) **proceed F1 immediately + open BUG-027 candidate W27+**(per Karpathy §1.3 surgical envelope)
3. F1 measurement scope refined per supplement file header reading:`eval-set-v0.yaml` 35 queries 對 current dev KB `sample-document-with-image-1`(DCE Integration Platform doc)corpus-mismatch — F1 cohort = **`eval-set-v0-w25-supplement.yaml` 13 queries**(consume W25 CO_W25_F4 deferred work)

### Done

**1. R6 pre-active-flip grep verification**(F0.4-F0.8)— **net zero contaminations**:
- `cohere.py` `async def rerank` at line 84(brief §7 84-130 + §2 96-130 ranges consistent)
- 5 existing `rerank_*` Settings;NEW `rerank_score_threshold` no naming collision
- `docs/eval-set-v0.yaml` + `docs/eval-set-v0-w25-supplement.yaml` both exist
- `/eval/run` + `make_ragas_evaluator` reuse-path confirmed across 8 files
- ADR-0036 last used → ADR-0037 next available ✓

**2. F1 RAGAs baseline measurement**(`POST /eval/run` eval_set_id=`eval-set-v0-w25-supplement` + cohere-v4.0-pro + CRAG enabled,runtime 558s ~9.3min):
- `recall_at_5=0.8744`(above Gate 1 floor 0.80,dropped ~10pp from W2 baseline 0.9722)
- `faithfulness=0.9851`(very high — LLM 唔 hallucinate)
- `correctness=0.7416`(moderate,approx via answer_relevancy per CO_W15_F1_eval_set_v1)
- `p95_latency_ms=1001`(5x under budget)
- **8/13 queries** with at least 1 metric fail;**5 queries context_recall=0.00**(I02 + I03 + I04 + I05 + T04)— **recall-dominant failure mode**
- Raw output:`baseline-metrics-W26-D1-raw.json`(2130 bytes EvalReport)
- Analysis:`baseline-metrics-W26-D1.md`(§1-§6 metrics + failure distribution + interpretation + critical reframing surfaced)

**3. F1 augmentation per Q2 locked decision** — per-chunk reranker score probe via `backend/scripts/w26_threshold_probe.py`(reuses retrieval_engine.retrieve() directly with truststore inject + sys.path bootstrap;runtime ~10s):
- 5 priority queries × 5 chunks = 25 Cohere v4.0-pro relevance scores
- Distribution:**min 0.67 / P25 0.83 / P50 0.90 / P75 0.91 / max 0.97 / mean 0.85**
- **Critical finding**:per-query score patterns refute brief §3 方向 A premise — **Cohere score CANNOT differentiate failed vs passed queries**:
  - Q-W25-I01(PASSED control)min score 0.67 vs Q-W25-I02(FAILED context_recall=0)min 0.88
  - Q-W25-I07(PASSED post-BUG-025)min 0.90 vs Q-W25-T04(FAILED both=0)min 0.67
  - Score range overlap highly between pass / fail cohorts
- Raw output:`threshold-probe-W26-D1.json`

**4. Strategic pivot per F1 empirical refutation** — Chris AskUserQuestion pick (C):
- F2 deliverable scope **PIVOTED** from「Step 1 rerank score threshold」(brief §3 方向 A + Chris 3-step initial framing)to「**Step 1 parent-document retrieval ADR-0037**」(brief §6 step 4 escalation,🟡 H1 Tier 1 ceiling)
- Reason:Cohere score distribution refutes threshold approach;parent-doc directly解 enumeration completeness(brief §1 「NOT EKP-unique bug — Dify same query fails」)
- Plan §7 Changelog 2026-05-25 D1 entry landed;Plan §2 F2 section header marked ⚠️ PIVOTED + ORIGINAL spec preserved as superseded reference

**5. F2 full rewrite deferred next session** — architectural design scope warrants fresh attention per Karpathy §1.2 simplicity-first(token budget consideration + ADR-0037 parent-doc design is non-trivial:section_path traversal pattern / aggregation strategy / token budget implications / pre-existing context_expander.py interaction analysis)

### Decisions(Day 1)

- **D1.1** — `/health` `cohere: not_configured` 屬 cosmetic observability misreport — Cohere actually operational(per get_settings() + make_reranker() + aenter diagnostic chain)— root cause `engine.reranker` public name vs `engine._reranker` private attr mismatch;BUG-027 candidate W27+ per Chris pick (a) Karpathy §1.3 surgical
- **D1.2** — F1 cohort = `eval-set-v0-w25-supplement.yaml` 13 queries only(NOT eval-set-v0 35 placeholder queries — corpus-mismatch confirmed via supplement file header reading)— consumes CO_W25_F4 deferred work
- **D1.3** — F1 augmentation via standalone script `w26_threshold_probe.py`(NOT orchestrator extension)— truststore inject + sys.path bootstrap + direct retrieval_engine.retrieve() — Karpathy §1.3 surgical(no production code touch);probe 5 priority queries × 5 chunks
- **D1.4** — F1 empirical finding **invalidates Chris 3-step Step 1 threshold approach** — Cohere score distribution(P25=0.83 / min=0.67 / max=0.97)cannot differentiate failed vs passed queries;threshold cutoff at any value would either gate nothing(< 0.67)or harm passed queries(I01 min 0.67 dropped)
- **D1.5** — Chris pivot pick (C) parent-document retrieval ADR-0037(brief §6 step 4 escalation)— root-cause solve for enumeration completeness;F2 ORIGINAL rerank-threshold scope superseded
- **D1.6** — F2 full design + ADR-0037 draft + code + tests + re-eval **deferred next session** per architectural scope + token budget consideration;preserved per W23 / W25 D0 cumulative AI compression pattern(non-trivial scope warrants fresh session attention)

### Blockers

無 — F1 deliverable complete,F2 pivot scope clarified;next-session ADR-0037 parent-doc draft 緊接。

### Verify gates results(F1)

| Gate | Result |
|---|---|
| F1.1-F1.3 R8 prerequisite gate | ✅ MET(diagnostic confirmed Cohere operational)|
| F1.4-F1.6 RAGAs run on 13 queries | ✅ done(`/eval/run` HTTP 200,558s runtime)|
| F1.7 baseline-metrics-W26-D1.md report | ✅ written |
| Per-chunk threshold probe | ✅ done(25 scores,distribution captured)|
| F1.8 F2 direction surface to Chris | ✅ AskUserQuestion 2-step:(1) recall-dominant strategy direction → (A) initial → (2) F1 empirical refutation → Chris pivot (C) parent-doc ADR |

### Carry-overs

- 🚧 **F2 PIVOTED scope full rewrite** next session — ADR-0037 parent-document retrieval draft + code + tests + re-eval
- 🚧 **F3 conditional gate** — depends on F2 parent-doc result(may not need query expansion if parent-doc解 enumeration completeness)
- 🚧 **BUG-027 candidate** —`/health._check_cohere` `engine.reranker` 應該係 `engine._reranker`(or `RetrievalEngine` expose `.reranker` @property)— Sev3/Sev4 cosmetic;W27+ separate BUG-fix scope per Chris pick (a) 2026-05-25
- 🚧 **CO_W26_threshold_probe_script** — `backend/scripts/w26_threshold_probe.py` 屬 dev script;若需 production audit / CI integration → 後續 promote;暫保留 backend/scripts/ 作為 measurement artifact

### Commits

- `feat(eval): W26 F1 RAGAs baseline + threshold probe + empirical pivot to parent-doc retrieval`(本 commit pending — baseline-raw + report + probe-script + probe-json + plan amendment + checklist update + progress Day 1 entry)

---

**End of Day 1 entry** — F1 baseline complete + critical empirical refutation surfaced → pivot to parent-doc ADR-0037;F2 architectural design deferred next session per Karpathy §1.2 + token budget。

---

## Day 1 cont — 2026-05-25:F2 ADR-0037 design + draft + Accepted + plan/checklist rewrite

> **Calendar continuity**:Same calendar day as Day 1 — Day 1 cont 標明係 2nd session segment(Day 1 F1 baseline + threshold-probe ran in session 1;ADR design + draft + Accepted + plan rewrite ran in session 2 per user instruction 「直接 F2 ADR-0037 parent-doc 設計 + draft」)。Per W22-W25 multi-session-per-calendar-day precedent pattern(real-calendar collapse ~3-7×)。

### Trigger sequence

1. **User explicit instruction 2026-05-25**:「直接 F2 ADR-0037 parent-doc 設計 + draft」— F2 architectural design scope authorized post Day 1 baseline + probe + pivot decision
2. **Reading list executed**:`docs/09-analysis/rag_retrieval_quality_investigation_20260525.md`(user brief — §3 方向 E + §6 step 4)+ `backend/retrieval/retrieval_engine.py`(existing structure)+ `backend/generation/context_expander.py`(ADR-0020 precedent structural sibling)+ `backend/retrieval/hybrid.py`(`fetch_by_chunk_ids` batch fetch pattern + `_apply_low_value_post_filter` BUG-025 amendment context)+ `docs/architecture.md` §3.5 + §3.6(`section_path` field schema + Collection(Edm.String) filterable proof)+ `docs/adr/0020-context-expander-tier-1-deliver.md`(full structural model)+ `docs/adr/0035-low-value-image-deboost-not-drop.md`(latest ADR format reference)+ `docs/adr/README.md`(next-NNNN confirmation = 0037)
3. **8 design questions identified** during reading + context synthesis(Q1 anchor top_k / Q2 section depth offset / Q3 token budget / Q4 default flag state / Q5 V6 stage display / Q6 Context Expander coexist / Q7 anchor scope / Q8 CRAG retune)— proposed defaults derived from ADR-0020 + ADR-0034 precedents + F1 empirical evidence

### Done

**1. ADR-0037 v1.0 full draft**(`docs/adr/0037-parent-document-section-retrieval.md` ~620 lines per CLAUDE.md §6 format):
- Header(Date 2026-05-25 + Status Accepted + Approver Chris AskUserQuestion + Trigger memo cross-ref)
- Context(7 subsections):spec promise + W26 F1 empirical refutation evidence(`baseline-metrics-W26-D1.md` + `threshold-probe-W26-D1.json` per-query distribution table)+ architectural root cause(per brief §1 + §3 + F1)+ Tier 1 ceiling rationale(既有 mitigation comparison table)+ Tier 1 vs Tier 2 boundary check + H1 trigger confirmation
- Decision(7 subsections):pipeline locus(post-Context Expander insertion)+ section-path aggregation algorithm(2.1 anchor / 2.2 depth / 2.3 token budget / 2.4 citation invariant)+ 6 NEW Settings spec + pipeline integration locus(file touch list of 8 files)+ Azure Search OData filter syntax(`section_path/any(s: s eq '...')`)+ interaction policy(6.1 Context Expander coexist Q6 / 6.2 CRAG L2 Q8 / 6.3 citation_image_neighbors Q9)+ observability(NEW Langfuse stage + V6 Debug View 10-stage)
- Alternatives Considered(5 rejected):Option B query intent routing / Option C re-chunk(Dify Parent-child mode)/ Option D GraphRAG(H4 Tier 2)/ Option E ADR-0034 alone / Option F manual section index — each with Pros/Cons + Rejected because rationale
- Consequences(Positive 7 / Negative 6 / Neutral 5)
- References(source docs + spec sections + cross-ref ADRs 8 + behavioral baseline + industry precedent + BUG-025 postmortem PC1/PC3/PC4 application)
- Implementation Deliverables(6 categories — backend module / observability / tests / RAGAs eval / docs)— **此 list 直接 sourced 落 W26 plan §2 F2 acceptance criteria**
- Open Design Questions(initial 8 Qs for AskUserQuestion)

**2. Chris AskUserQuestion 4 critical Qs**(per user pick (b) 2026-05-25):
- **Q4** default flag state → **Default OFF — W26 F2 measurement** (Recommended)
- **Q1** `parent_doc_top_k` initial → **1 — top-1 reranked anchor only** (Recommended)
- **Q2** `section_depth_offset` initial → **1 — parent = `section_path[:-1]`** (Recommended)
- **Q6** Coexistence with Context Expander → **Both on — parent-doc consumes Context Expander output** (Recommended)

**3. Q3+Q5+Q7+Q8 proposed defaults batch-locked**(`max_tokens_per_parent=4000` / V6 Option A 10-stage / anchor scope=top-1 同 Q1 同義 / W26 NOT retune CRAG threshold)— all match ADR draft proposed defaults

**4. ADR Status flip Proposed → Accepted**:
- Header Status line updated:`**Status**: Accepted` + `**Approver**: Chris(技術 Lead)— AskUserQuestion approved 2026-05-25 D1 cont(Q4 Default OFF + Q1 top_k=1 + Q2 depth_offset=1 + Q6 Both on — all Recommended picks;Q3+Q5+Q7+Q8 proposed defaults batch-locked at same approval)`
- Open Design Questions section replaced with **Decision Log** section documenting picks + 6 NEW Settings defaults locked summary

**5. ADR + README atomic governance commit `4cdd1bc`**(+631 / -1):
- `docs/adr/0037-parent-document-section-retrieval.md` NEW(631 insertions)
- `docs/adr/README.md` row add + footer next-NNNN bump 0037 → 0038
- Commit message follows Conventional Commits + HEREDOC + Co-Authored-By per CLAUDE.md §4.2

**6. Plan rewrite cascade**(W26 plan.md per R3 binding rule):
- §1.2 Step 1 row revised(post-pivot scope reflects parent-doc retrieval per ADR-0037 active spec;cross-ref §7 Plan Changelog)
- §2 F2 deliverable spec full rewrite(PIVOTED placeholder ORIGINAL/superseded removed → 7-category 20-item active acceptance criteria sourced from ADR §Implementation Deliverables list — A governance gate satisfied + B retriever module + C pipeline integration + D 6 NEW Settings + E observability + F tests + G RAGAs eval + H F2 → F3 gate)
- §3 Hard Gates G3 + G4 rescoped(was「precision improvement」+「recall regression」→ now「`context_recall` improvement on failed-cohort」+「`faithfulness` regression」per parent-doc workload signal — recall is dominant per F1 5/13 finding;faithfulness is safety guard)
- §4 R3 + R7 risks rescoped(R3 threshold iteration → parent-doc Settings sweep iteration `parent_doc_top_k` 1→2→3 OR `max_tokens_per_parent` 4000→6000→2000;R7 governance scope creep CLOSED 2026-05-25 D1 cont — ADR Accepted gate satisfied)
- §5 Day-by-Day D1 cont row inserted + D4-D7 rescoped(was「ADR draft + threshold code」→ now「F2 impl + tests + re-eval」since ADR draft+approval already complete)
- §7 Plan Changelog 2026-05-25 D1 cont entry landed(10 sub-items (a)-(j) cataloged)
- §8 Locked Design Decisions extended with Q6 + Q7 rows(Q6 = ADR-0037 6 Settings defaults summary;Q7 = F2 → F3 gate criteria scoping TBD per F2 D{N} delta + Q3 eval-driven preserve)
- §9 Component Impact Map rewrite — C04(`hybrid.py` `fetch_chunks_by_section_path` method + `settings.py` 6 NEW knobs)+ C05(NEW `parent_doc_retriever.py` module + `prompt_builder.py` dispatch chain + `crag.py` + `query.py` wire)+ C07(`observe.py` NEW stage + `debug/[traceId]/page.tsx` V6 10-stage);**partial H7 trigger** per V6 Debug View frontend stage card update

**7. Checklist rewrite**(`W26 checklist.md` F2 items):
- Header note PIVOTED 2026-05-25 D1 cont
- F2.1-F2.3 governance gate(已 satisfied — [x] checked ✅ for ADR drafted + AskUserQuestion approved + README synced)
- F2.4-F2.5 backend B retriever module(F2.4a-i parent_doc_retriever + F2.5a-d hybrid extension)
- F2.6-F2.9 C pipeline integration(prompt_builder + crag + query routes 2 sites)
- F2.10 D 6 NEW Settings
- F2.11-F2.12 E observability(observe stage + V6 frontend 10-stage with H7 self-verify in F2.12c)
- F2.13-F2.18 F tests(15 cases parent_doc_retriever + 5 cases hybrid extension + regression 1044+ + mypy + ruff)
- F2.19-F2.23 G RAGAs re-eval(env override + 13-query re-run + per-query diagnostic + Q-W25-I07 qualitative review + Q-W25-I02-I05+T04 5-failed-cohort review + Settings sweep iteration log per R3)
- F2.24 H F2 → F3 gate AskUserQuestion
- Verification gates G1+G2 marked [x] DONE(G1 F1.7 satisfied + G2 F2.2 Chris AskUserQuestion satisfied 2026-05-25 D1 cont)+ G3+G4 wording rescoped + G6 + G7 cross-ref updated to new F2.* numbering

### Decisions(Day 1 cont)

- **D1.7** — User pick (c) 分 2 commits per session-end decision tree(ADR governance commit `4cdd1bc` atomic + planning commit pending this Day 1 cont entry)— matches Karpathy §1.3 surgical + W25 single-commit precedent reversed for ADR governance separation;ADR Accepted = immutable artifact while plan rewrite continues phase-evolution
- **D1.8** — ADR-0037 Q6 「Both on coexistence」 vs 「Mode-switch replace」 picked Both on(Recommended)per top-2..top-5 non-anchor chunks 仍 benefit from ADR-0020 prev/next expansion;Mode-switch would lose those benefits — net regression vs marginal simplicity gain
- **D1.9** — ADR-0037 Q1 top_k=1 conservative pick(Recommended)per F1 evidence Q-W25-I07 top-5 已含 §3.1 chunk #8 topically off — top-K anchor parent-doc aggressive 化 會 aggregate §3 整 section 入 context = 反效果;Setting 允許 W27+ sweep 至 2/3 if multi-section queries 需要
- **D1.10** — V6 Debug View frontend touch 細範圍 (~30 LOC observation-name prefix + stage card render)= **partial H7 trigger** per CLAUDE.md §5.7 — H7 self-verify item F2.12c added but mockup `ekp-page-debug.jsx` 可能未存(若 not exist → V6 既存 stage cards 作為 alignment reference per ADR-0020 W17 precedent)— defer to F2 implementation 階段先 trigger;若 mockup exist 即 follow §3.2.1 7-item fidelity checklist
- **D1.11** — G3 + G4 hard gate criteria rescope(precision↑/recall↓ → `context_recall`↑/`faithfulness`↓)reflects parent-doc workload semantic shift — recall is the dominant signal per F1 5/13 `context_recall=0.00` finding;faithfulness preserves safety net against parent section over-broadening dilution

### Blockers

無 — F2 governance complete(ADR Accepted + plan rewrite landed);F2 implementation gate open per ADR §Implementation Deliverables list as acceptance contract。

### Verify gates results(F2 governance — A category)

| Gate | Result |
|---|---|
| F2.1 ADR drafted | ✅ DONE(~620 lines per CLAUDE.md §6 format)|
| F2.2 Chris AskUserQuestion approval | ✅ DONE(4 Recommended picks + 4 batch-lock 2026-05-25 D1 cont)|
| F2.3 README index synced | ✅ DONE(row + footer next-NNNN 0038)|
| G1 F1 baseline metrics | ✅ DONE(F1.7 satisfied — `baseline-metrics-W26-D1.md` 2026-05-25 D1)|
| G2 ADR-0037 Accepted | ✅ DONE(2026-05-25 D1 cont)|
| G3-G7 | ⏸ pending F2.4-F2.24 implementation cascade |

### Carry-overs

- 🚧 **F2 implementation cascade**(F2.4-F2.24)next session — backend `parent_doc_retriever.py` module + `hybrid.py` extension + pipeline wire + Settings 6 knobs + observability stage + V6 frontend 10-stage + 15+ tests + RAGAs re-eval + F2 → F3 gate AskUserQuestion
- 🚧 **session-start.md sync**(F0.10 deferred to F4 closeout per original plan — bundle in F4 closeout commit OR separate `docs(session-start)` commit per W25 precedent)
- 🚧 **CO_W26_BUG-027_health_reranker_attr**(D1.1 carry-over preserved — `/health._check_cohere:103` `engine.reranker` public name vs `engine._reranker` private attr drift;Sev3/Sev4 cosmetic;W27+ separate BUG-fix scope per Chris pick (a) 2026-05-25 D1)
- 🚧 **CO_W26_threshold_probe_script**(D1 carry-over — `backend/scripts/w26_threshold_probe.py` measurement artifact)— preserved for F2 implementation 階段可能 reuse as parent-doc Settings sweep iteration tool

### Commits

- `4cdd1bc` `docs(adr): ADR-0037 Accepted — parent-document / section-level retrieval (W26 F2 PIVOTED)` — atomic governance commit(+631 / -1 across 2 files)
- `docs(planning): W26 F2 PIVOTED scope rewrite + ADR-0037 plan/checklist/progress cascade` — pending this Day 1 cont entry commit(plan §1.2/§2/§3/§4/§5/§7/§8/§9 + checklist F2 + progress Day 1 cont)

---

**End of Day 1 cont entry** — F2 governance complete(A category satisfied G2 hard gate)+ plan rewrite cascade per R3 binding rule + checklist F2 rewrite + progress Day 1 cont entry;F2 implementation gate open per ADR-0037 §Implementation Deliverables list as acceptance contract for next session impl cascade。
