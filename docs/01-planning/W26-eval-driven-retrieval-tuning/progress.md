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

---

## Day 1 cont 2 — 2026-05-25:F2 implementation start(D Settings + B HybridSearcher leaf extension)

> **Calendar continuity**:Same calendar day as Day 1 + Day 1 cont — Day 1 cont 2 = 3rd session segment per user instruction 2026-05-25「start F2 implementation」per W22-W25 multi-session-per-calendar-day precedent。Implementation cascade begins from dependency leaves(Settings + HybridSearcher extension)inward toward the parent_doc_retriever module + pipeline wire。

### Done

**1. F2.10 D Settings — 6 NEW knobs**(`backend/storage/settings.py`):
- `enable_parent_doc_retrieval: bool = False`(Q4 Recommended — default OFF measurement experiment)
- `parent_doc_section_depth_offset: int = 1`(Q2 Recommended — parent = `section_path[:-1]`)
- `parent_doc_top_k: int = 1`(Q1 Recommended — top-1 anchor only)
- `parent_doc_max_tokens_per_parent: int = 4000`(Q3 proposed — ~15 sibling chunks envelope)
- `parent_doc_max_chunks_per_parent: int = 50`(safety cap)
- `parent_doc_fallback_to_doc_on_shallow: bool = True`(shallow section_path handling)
- Block documented per CLAUDE.md §3.3 (W26 F2 context + ADR-0037 ref + AskUserQuestion pick rationale + W27+ sweep capability noted)

**2. F2.5 B HybridSearcher.fetch_chunks_by_section_path method**(`backend/retrieval/hybrid.py`,~85 lines added between `fetch_by_chunk_ids` and `search`):
- Signature `async def fetch_chunks_by_section_path(parent_path, doc_id, kb_id, *, max_chunks=50) -> list[HybridSearchHit]`
- OData filter composition:`kb_id eq + doc_id eq + enabled eq true + section_path/any(s: s eq '<seg>')` per parent_path segment joined `and`
- OData single-quote escaping(doubled per Azure Search spec)— `Scenario A's intro` → `Scenario A''s intro`
- `orderby chunk_index asc` preserves narrative order
- `top=max_chunks` hard cap (default 50 matches `Settings.parent_doc_max_chunks_per_parent`)
- search="*" + filter + orderby = pure filtering retrieval (no BM25/vector ranking)
- Empty parent_path / empty doc_id → return [] (cost guard, no API call)
- @retry tenacity decorator mirroring `fetch_by_chunk_ids` pattern (3 attempts, exp backoff)
- Response shape transformation:Azure Search `value` items → `list[HybridSearchHit]` with `@search.*` system field stripping
- `enabled eq true` baseline preserved per ADR-0035 W25 F5 D2 (low_value siblings NOT filtered here — caller decides via post-filter applied earlier in pipeline;parent section inclusion is content-aggregation concern, not retrieval-candidacy concern)
- structlog `hybrid_fetch_chunks_by_section_path` debug log with index + kb_id + doc_id + parent_path_depth + returned count + cap

**3. F2.14 + F2.18 B HybridSearcher tests**(NEW `backend/tests/test_hybrid_section_path.py` ~250 LOC,11 cases):
- **11/11 PASSED**(0.89s wall-clock)
- Coverage:empty parent_path guard + empty doc_id guard + filter combines all 5 clauses + OData escaping doubled / 2 sites + orderby chunk_index asc + max_chunks cap parameter + default cap 50 + search="*" filter-only + response shape transform + empty response handling + dynamic index_name per kb_id ADR-0018 invariant

**4. Verify gates**(F2 implementation D1 cont 2 leaf scope):
- ✅ `pytest tests/test_hybrid_section_path.py -v` — 11/11 pass
- ✅ `pytest tests/` full regression — **1035 passed + 25 skipped + 0 failed**(W25 baseline 1024 + 11 NEW = exact match)
- ✅ `mypy --strict --explicit-package-bases retrieval/hybrid.py storage/settings.py tests/test_hybrid_section_path.py` — 0 errors in 3 source files
- ✅ `ruff check` — All checks passed
- G6 backend regression preserved hard gate ✅(satisfied for this atomic piece)

### Decisions(Day 1 cont 2)

- **D1.12** — `fetch_chunks_by_section_path` 唔 apply `_apply_low_value_post_filter`(unlike `search()` which does) — semantic split:`search()` is retrieval-candidacy stage(low_value chunks deboosted via post-filter per ADR-0035);`fetch_chunks_by_section_path` is content-aggregation stage(siblings included regardless of low_value flag for parent section completeness)— parent section is about「what's in this logical document section」not「what ranks where」。Documented inline in method docstring per CLAUDE.md §3.3
- **D1.13** — Test file split — NEW `test_hybrid_section_path.py` instead of extending existing `test_hybrid_searcher_image_low_value.py`。Reason:Karpathy §1.3 surgical(test files topic-cohesive per `image_low_value` topic naming convention)+ semantic split per D1.12 — different filter scope different test scope
- **D1.14** — Mypy strict catch corrected mid-session(2 unused `type: ignore` defensive annotations removed)— `unittest.mock.MagicMock` + `AsyncMock` assignment to `searcher._client` 唔需要 explicit type:ignore since mypy infers acceptable type compatibility automatically;dead annotation = mypy strict noise
- **D1.15** — Atomic commit boundary picked(D Settings + B HybridSearcher extension + B tests = single commit `feat(retrieval): W26 F2 D Settings + B HybridSearcher.fetch_chunks_by_section_path per ADR-0037`)— Karpathy §1.3 surgical:leaf primitives are independent + complete + tested + verifiable in isolation;parent_doc_retriever module(F2.4)= next atomic piece consuming these leaves;pipeline wire + observability + V6 frontend + RAGAs re-eval each their own commits

### Blockers

無 — leaf atomic piece complete + verified;next atomic piece = parent_doc_retriever module(F2.4)consuming Settings + HybridSearcher extension。

### Carry-overs(updated Day 1 cont 2)

- 🚧 **F2.4 parent_doc_retriever module**(B core)next atomic commit — consumes Settings + HybridSearcher leaves landed this commit
- 🚧 **F2.6-F2.9 pipeline integration**(C prompt_builder + crag + query routes)— follows F2.4 atomic commit
- 🚧 **F2.11-F2.12 observability**(E observe.py stage + V6 frontend 10-stage)— follows F2.6-F2.9
- 🚧 **F2.13 parent_doc_retriever tests** + **F2.16 final regression** — bundled with F2.4 atomic commit
- 🚧 **F2.19-F2.23 G RAGAs re-eval** — follows full F2 implementation cascade complete
- 🚧 **F2.24 H F2 → F3 gate AskUserQuestion** — terminal step,task #212

### Commits

- `4cdd1bc` `docs(adr): ADR-0037 Accepted — parent-document / section-level retrieval (W26 F2 PIVOTED)` — atomic governance commit(+631 / -1 across 2 files)
- `f9398ec` `docs(planning): W26 F2 PIVOTED scope rewrite + ADR-0037 plan/checklist/progress cascade` — planning cascade commit(+275 / -73 across 3 files)
- `feat(retrieval): W26 F2 D Settings + B HybridSearcher.fetch_chunks_by_section_path per ADR-0037` — atomic leaf implementation commit(pending this entry)

---

**End of Day 1 cont 2 entry** — F2 leaf atomic piece complete(D + B + tests + verify gates ALL green);F2.4 parent_doc_retriever module next atomic commit consuming these primitives。

---

## Day 1 cont 3 — 2026-05-25:F2.4 parent_doc_retriever core module + tests

> **Calendar continuity**:Same calendar day continuation per user instruction「start F2 implementation」— ce8e870 leaf commit landed, immediately followed by F2.4 core module per atomic-commit pacing。

### Done

**1. F2.4 B Backend Parent-Document Retriever module**(`backend/generation/parent_doc_retriever.py`,~310 lines):
- Module-level docstring documents the 6-step algorithm + edge cases + Citation invariant + Default Settings cross-ref + ADR-0037 + trigger memo cross-ref
- `_STAGE_NAME = "generation.parent_doc_retrieval"` constant(Langfuse stage prefix for V6 Debug View 10-stage scaffold per Q5 Option A)
- `_estimate_tokens(text)` helper — 4-char-per-token heuristic per ADR-0034 P95<5s budget framing
- `ParentSectionChunk` dataclass — duck-typed `RetrievedChunk` / `ExpandedChunk` compatible(`score: float` + `fields: dict[str, Any]` + `parent_section_text: str | None` + `parent_path: list[str] | None` + `sibling_count: int` + `truncated: bool`)+ `no_aggregation` classmethod for flag-off / shallow / lookup-miss passthrough paths
- `ParentDocStats` dataclass — 6 observability fields(`requested_anchors` / `parents_fetched` / `siblings_aggregated` / `truncated_count` / `skipped_shallow_count` / `fetch_latency_ms`)
- `_emit_parent_doc_stage(stats)` helper — invokes `emit_stage_metadata` with all 6 stats fields per ADR-0020 emit pattern
- `_compute_parent_path` helper — encapsulates Q2 depth_offset + fallback_to_doc_on_shallow logic(`len > offset` → normal drop / `len ≤ offset` + fallback=True → preserve top-1 / else → None skipped)
- `aggregate_parent_sections` async coroutine — 6-step algorithm:
  1. Empty input guard
  2. Anchor selection per `parent_doc_top_k=1` default(top-1 anchor only — Q1 Recommended;passthrough preserves top-2..top-K untouched per Q6 Both on)
  3. Compute parent paths per anchor + dedupe `(doc_id, parent_path)` tuples
  4. Batch fetch each unique `(doc_id, parent_path)` via `HybridSearcher.fetch_chunks_by_section_path` — per-parent `except Exception` graceful degradation log + return empty
  5. Assemble per-anchor `parent_section_text` with token-budget truncation tail-drop(first sibling always included even if alone exceeds budget — degenerate-doc graceful)
  6. Pass through non-anchor chunks unchanged via `no_aggregation` classmethod(preserves `expanded_text` from ADR-0020 Context Expander upstream)

**2. F2.11 E Observability stage wiring**(no `observe.py` modification needed):
- `_STAGE_NAME = "generation.parent_doc_retrieval"` constant defined in retriever module
- `_emit_parent_doc_stage(stats)` helper invokes existing `emit_stage_metadata()` from `observability/observe.py` with stage name + duration_ms + 5 stats fields
- Matches ADR-0020 `backend/generation/context_expander.py` precedent pattern — `_STAGE_NAME` defined per-module, no central registry needed per Karpathy §1.2 simplicity

**3. F2.13 F Tests**(NEW `backend/tests/test_parent_doc_retriever.py` ~430 LOC,14 cases — 11 of plan baseline a/b/c×2/d×2/f/g/h/j/k + 3 defensive edge cases):
- **14/14 PASSED**(1.06s wall-clock)
- Coverage:
  - F2.13a happy path 6-sibling aggregation
  - F2.13b multi-anchor dedupe 1-fetch
  - F2.13c shallow section_path 2-case(fallback on / off)
  - F2.13d token budget 2-case(tail-drop + degenerate single huge)
  - F2.13e cross-doc covered implicitly via F2.13b(different `doc_id` → separate parent_lookup keys)+ F2.14a OData filter test at leaf layer
  - F2.13f empty input → no fetch + zero stats
  - F2.13g lookup miss → anchor passthrough
  - F2.13h network error graceful
  - F2.13j Q6 Both on coexistence(non-anchor `expanded_text` preserved)
  - F2.13k Citation invariant(anchor `chunk_id` + `chunk_text` intact;new `parent_section_text` added)
  - Defensive edges:missing `doc_id` + missing `section_path` + `no_aggregation` classmethod
- F2.13i feature flag deferred to pipeline integration layer per architectural split(retriever module 唔讀 Settings,separation of concerns)

**4. Verify gates**(F2 core module D1 cont 3 scope):
- ✅ `pytest tests/test_parent_doc_retriever.py -v` — 14/14 pass
- ✅ `pytest tests/test_parent_doc_retriever.py tests/test_hybrid_section_path.py -v` — 25/25 combined pass
- ✅ `pytest tests/` full regression — **1049 passed + 25 skipped + 0 failed**(149.52s;W25 baseline 1024 + 11 hybrid_section_path + 14 parent_doc_retriever = 1049 exact match — G6 backend regression preserved hard gate ✅)
- ✅ `mypy --strict --explicit-package-bases generation/parent_doc_retriever.py tests/test_parent_doc_retriever.py` — 0 errors in 2 source files;**5 pre-existing observability/ errors out of scope per Karpathy §1.3 surgical**(W25 CO_W25_mypy_strict_debt territory)
- ✅ `ruff check generation/parent_doc_retriever.py tests/test_parent_doc_retriever.py` — All checks passed(2 import-order auto-fixed during iteration)

### Decisions(Day 1 cont 3)

- **D1.16** — Token budget truncation policy:**always include first sibling even if alone exceeds budget**;degenerate single-huge-chunk doc graceful with `truncated=True` flag。Alternative considered:return empty + skipped — rejected because section with even 1 chunk has signal;per Karpathy §1.4 goal-driven「some context > no context」for enumeration queries
- **D1.17** — `no_aggregation` classmethod added on `ParentSectionChunk` for passthrough paths(flag-off / shallow / lookup-miss / non-anchor)— matches `ExpandedChunk.no_expansion` precedent from ADR-0020;simplifies caller code(no dataclass field bookkeeping)+ ensures fields dict copy semantics(`dict(getattr(chunk, "fields", {}) or {})`)
- **D1.18** — Generic `object` typing on `_chunk` parameter of `no_aggregation` classmethod(duck-typed)over `Protocol` typing — Karpathy §1.2 simplicity;getattr fallbacks handle the duck-type;Protocol would force every caller to ensure type-hint conformance unnecessarily
- **D1.19** — `_compute_parent_path` extracted as separate helper from `aggregate_parent_sections` body — Karpathy §1.3 cohesive helper(parent_path computation has 3 branches:normal / shallow fallback / shallow skip);extraction enables clearer test surface + cleaner inline flow + easier future tweaks if Q2 sweep needs adaptive logic
- **D1.20** — F2.11 observability stage wired via `_STAGE_NAME` constant in retriever module(NOT via `observe.py` modification)— matches ADR-0020 `context_expander.py` precedent;`emit_stage_metadata()` accepts arbitrary stage name string;per Karpathy §1.2 simplicity — no central registry needed
- **D1.21** — Mypy strict catch — added `from typing import Any` + `fields: dict[str, Any]` annotation + `from retrieval.hybrid import HybridSearchHit` for parent_lookup type;5 pre-existing `observability/` errors documented in progress as out of W26 F2 scope per Karpathy §1.3 surgical(observable signal:scope-bound + no regression introduced)
- **D1.22** — Ruff auto-fixed 2 import-order errors during iteration(blank line between import groups + import sort)— landed in commit alongside type annotations

### Blockers

無 — F2 core module complete + verified(pending full regression notification)。F2.6-F2.9 pipeline integration next atomic commit。

### Carry-overs(updated Day 1 cont 3)

- 🚧 **F2.6-F2.9 C pipeline integration** next atomic commit — `prompt_builder.py` dispatch chain extension + `crag.py` flag-gated wire + `query.py` 2 sites flag-gated wire
- 🚧 **F2.12 E V6 Debug View 10-stage** — `frontend/app/debug/[traceId]/page.tsx` stage card insert + H7 self-verify(check mockup `ekp-page-debug.jsx` if exists else V6 既存 cards alignment)
- 🚧 **F2.19-F2.23 G RAGAs re-eval** — follows full implementation cascade complete
- 🚧 **F2.24 H F2 → F3 gate AskUserQuestion** — terminal step task #212
- 🚧 **observability/ mypy strict debt** — 5 pre-existing errors in `observability/langfuse_tracer.py` + `observability/observe.py`(W25 CO_W25_mypy_strict_debt territory;out of W26 F2 scope per Karpathy §1.3 surgical;documented for future W27+ cleanup if scope warrants)

### Commits

- `4cdd1bc` `docs(adr): ADR-0037 Accepted` — atomic governance(+631 / -1)
- `f9398ec` `docs(planning): W26 F2 PIVOTED scope rewrite + ADR-0037 plan/checklist/progress cascade` — planning cascade(+275 / -73)
- `ce8e870` `feat(retrieval): W26 F2 D Settings + B HybridSearcher.fetch_chunks_by_section_path per ADR-0037` — atomic leaf(+535 / -17 across 5 files)
- `feat(generation): W26 F2 B parent_doc_retriever module + observability stage + 14 unit tests per ADR-0037` — atomic core module commit pending this entry

---

**End of Day 1 cont 3 entry** — F2 core module + observability + tests complete(14/14 + ruff + mypy strict on touched code all green);F2.6-F2.9 pipeline integration next atomic commit consuming retriever module + Settings flag check at caller layer。

---

## Day 1 cont 4 — 2026-05-25:F2.6-F2.9 Pipeline 整合 + dispatch chain 測試

> **日曆連續性**:同日 4th session 段,user instruction「continue F2.6-F2.9 pipeline integration」+ 提醒「中文對答為主」(memory `feedback_chinese_primary_replies.md` 已記第 3 次違反 + 強化紀律)。

### 完成項目

**1. F2.6 `prompt_builder.py` dispatch chain 擴展**:
- `_format_chunk` 函式內 `text` 計算改為 3 級 fallback 鏈:`parent_section_text > expanded_text > chunk_text`
- Docstring 更新引用 ADR-0037 + Citation invariant 保留說明(LLM 見 parent_section_text 但 citation 引用原 anchor chunk_id)
- 對齊 ADR-0020 既有 dispatch 模式 — 純優先級擴展非結構改動

**2. F2.7+ `retrieval_engine.py` NEW `aggregate_parent_sections_for_chunks` wrapper**:
- 公開 wrapper 封裝 `self._searcher` 訪問(對齊 ADR-0020 `expand_context_for_chunks` precedent)
- 解 circular import via local `from generation.parent_doc_retriever import aggregate_parent_sections`
- 簽名:`chunks: list[RetrievedChunk]` + 6 kwargs 對應 ADR-0037 6 NEW Settings + 預設值對齊 Chris AskUserQuestion 2026-05-25 D1 cont 4 Recommended picks
- Mypy delta = 0(對齊 line 194 `expand_context_for_chunks` 既有風格;return type 省略屬 W25 CO_W25_mypy_strict_debt 一致 — 不引入 new debt per Karpathy §1.3 surgical)

**3. F2.7 `crag.py` re-synthesis path flag-gated 整合**:
- NEW import `from storage.settings import get_settings`
- `refine()` 內 re-retrieval + Context Expander 後 + `synthesizer.synthesize()` 前加 `if crag_settings.enable_parent_doc_retrieval:` block
- 經 `engine.aggregate_parent_sections_for_chunks` wrapper(non breaking encapsulation)
- Graceful `try/except` errors append + warning log;exception 不 raise 至 outer scope — 維持 expanded_new_chunks 作 fallback(no degradation vs ADR-0020 baseline)
- 6 settings knobs 由 `crag_settings.parent_doc_*` 傳入

**4. F2.8 `query.py /query` happy path 整合**:
- Context Expander block(line ~178)之後 + `synthesizer.synthesize()` 之前加 `if settings.enable_parent_doc_retrieval:` block
- 經 `engine.aggregate_parent_sections_for_chunks` wrapper + graceful try/except
- `expanded_chunks` 變數 in-place 替換 — duck-typed `prompt_builder` 全部接受(ExpandedChunk OR ParentSectionChunk 兩者都有 `.score + .fields`)

**5. F2.9 `query.py /query/stream` 同 pattern 整合**:
- `stream_settings = get_settings()` 由 line 299 提前到 line ~295 一次過 lookup;parent-doc gate + 後續 neighbour-image augmentation 兩者 reuse
- Block 結構完全 mirror `/query` happy path,保持 happy path / stream path 對稱性

**6. F2.13 補充 — NEW `tests/test_prompt_builder_dispatch.py` 7 案例**:
- baseline 無 expansion → 用 chunk_text
- ADR-0020 expanded_text > chunk_text
- ADR-0037 parent_section_text > expanded_text(兩者並存)
- ADR-0037 parent_section_text > chunk_text(無 expanded_text)
- Citation invariant 保留 — chunk_id reference 仍 anchor's id 不論 dispatch 結果
- 空字符串 parent_section_text → fallback 跌落 expanded_text
- 缺失 parent_section_text 鍵 → fallback 同 ADR-0020 baseline 一致
- 7/7 pass(1.22s)

**7. 驗證閘**(F2 pipeline 整合 D1 cont 4 範圍):
- ✅ `pytest tests/test_prompt_builder_dispatch.py` — 7/7 pass(1.22s)
- ✅ `pytest tests/test_prompt_builder_dispatch.py tests/test_parent_doc_retriever.py tests/test_hybrid_section_path.py` — **32/32 W26 F2 全套 pass**(1.99s)
- ✅ `pytest tests/` full regression — **1056 passed + 25 skipped + 0 failed**(130.23s;1049 baseline + 7 NEW dispatch = 1056 exact match — G6 backend regression preserved hard gate ✅)
- ✅ `mypy --strict` on touched files — 我嘅 delta = 0(剩 13 errors 全 pre-existing W25 CO_W25_mypy_strict_debt:observability + retrieval_engine line 51/153/194/250/258 + context_expander line 74 + prompt_builder line 35 — 全部 pre-existing,我嘅整合 0 NEW error)
- ✅ `ruff check` — All checks passed(test 檔 import order 1 個 ruff auto-fixed during iteration)

### 決定(Day 1 cont 4)

- **D1.23** — `crag.py` settings injection pattern 選 inline `get_settings()` lookup(選項 B)非 constructor injection(選項 A — 改 `CragLoop.__init__` 簽名)— Karpathy §1.3 surgical 最小 blast radius;對齊 query.py `/query/stream` `stream_settings = get_settings()` 既有 pattern;CragLoop wiring(`server.py` lifespan)0 改動
- **D1.24** — `aggregate_parent_sections_for_chunks` wrapper 簽名對齊 `expand_context_for_chunks` style(param typed + return untyped)— 一致 codebase 樣式;mypy strict delta = 0(對齊 line 194 pre-existing pattern,非加新 W25 mypy debt)
- **D1.25** — Test fixture `_chunk_with_fields(**overrides: object)` `base: dict[str, object]` explicit annotation 解決 mypy 推斷 `dict[str, Sequence[str]]` 型別衝突(由 `section_path: ["Doc", "§1"]` list[str] 推斷)— 1 行 minimal 修正
- **D1.26** — Pipeline 整合 4 sites(`/query` + `/query/stream` + `crag.py refine` + `prompt_builder._format_chunk`)全部 graceful fallback policy 統一:**任何 parent-doc exception 都 NOT raise** —— `expanded_chunks`(query paths)OR `expanded_new_chunks`(crag.py)維持 ADR-0020 expansion 結果作 fallback;`synthesize()` 永遠 run 不會因 parent-doc 失敗而中斷整條 pipeline。對齊 ADR-0020 + ADR-0035 graceful 規律
- **D1.27** — `stream_settings = get_settings()` 由 line 299 提前到 line ~295 一次過 lookup — 避免 parent-doc + neighbour-image two double-call;同一 settings instance 服務兩個 downstream consumer。Minimal rename(stream_settings 變數名保留 — 避免無謂改動下游 reference per Karpathy §1.3)

### 阻塞

無 — pipeline 整合完整 + 32/32 W26 F2 套 tests 全綠;全 regression background 跑緊。

### Carry-over 更新(Day 1 cont 4)

- 🚧 **F2.12 V6 Debug View 10-stage** — `frontend/app/debug/[traceId]/page.tsx` 加 NEW「Parent-Document Retriever」stage card + H7 self-verify(對 mockup `ekp-page-debug.jsx` 若存在,否則跟 V6 既有 stage cards 對齊)
- 🚧 **F2.19-F2.23 G RAGAs 重跑** — 待完整 F2 implementation cascade 後;R8/Azure-key-bound 仍 prerequisite
- 🚧 **F2.24 H F2 → F3 gate AskUserQuestion** — 終極步驟 task #212

### Commits

- `4cdd1bc` ADR-0037 Accepted(governance)
- `f9398ec` Plan + checklist + progress rewrite cascade
- `ce8e870` Leaf — D Settings + B HybridSearcher extension + 11 tests
- `48f7460` Core — B parent_doc_retriever module + E observability stage + 14 tests
- `feat(generation): W26 F2 C pipeline integration — prompt_builder dispatch + crag.py + query.py 2 sites + 7 NEW dispatch tests per ADR-0037` — atomic pipeline 整合 commit pending(本 entry)

---

**End of Day 1 cont 4 entry** — F2 pipeline 整合 4 sites 完成(prompt_builder + crag.py + query.py × 2 + retrieval_engine.py wrapper)+ 7 NEW dispatch tests(32/32 W26 F2 全套 pass)+ mypy 0 delta + ruff clean。F2.12 V6 Debug View 10-stage 為下一個 atomic piece(前端 H7 fidelity 自驗範圍)。
