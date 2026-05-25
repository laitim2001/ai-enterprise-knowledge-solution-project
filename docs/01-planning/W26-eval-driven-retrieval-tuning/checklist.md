---
phase: W26-eval-driven-retrieval-tuning
plan_ref: ./plan.md
status: active
last_updated: 2026-05-25
---

# W26 — Checklist

> Derived from `plan.md §2 Deliverables` + §3 Phase-Level Hard Gates。
> Per Chris 3-step refinement(2026-05-25):Step 0 RAGAs baseline → Step 1 rerank threshold(ADR-0037)→ Step 2 query expansion(gated on Step 1 + eval delta)。

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

## F1 — Step 0 RAGAs baseline measurement(Chris Step 0,prerequisite — no skip)

### R8 prerequisite gate(STOP and ask if blocked)
- [ ] **F1.1** — Azure OpenAI judge key availability check in dev / personal Azure dev tier(per ADR-0017 Plan B (c) precedent)
- [ ] **F1.2** — Cohere v4.0-pro production reranker key check(NOT just Azure semantic ranker fallback per brief §4 strict reading)
- [ ] **F1.3** — STOP and ask Chris if EITHER blocked — Plan B options:(a) Chris 提供 personal Azure dev tier credentials;(b) defer W26 → W27+ when Track A IT cred lands;(c) limited scope F1(retrieval-only metrics without LLM judge)

### Baseline measurement
- [ ] **F1.4** — Decide on measurement script approach:reuse existing `/eval/run` endpoint(W17 F3 RAGAs 4-metric integration)OR new minimal `backend/eval/scripts/w26_baseline_measure.py`(per brief §6 step 1 simpler harness)
- [ ] **F1.5** — Run RAGAs 4-metric(faithfulness / answer_relevancy / context_precision / context_recall)on:
  - [ ] **F1.5a** — Q-W25-I07「show me all the Integration scenarios」on KB `sample-document-with-image-1`(failed query)
  - [ ] **F1.5b** — `what is high level architecture` on same KB(control query — W25 D4 milestone)
  - [ ] **F1.5c** — 1-2 additional `eval-set-v0.yaml` baseline samples(targeted query class control)
  - [ ] **F1.5d** — `eval-set-v0-w25-supplement.yaml` 13 queries subset(若 R8 OK + Azure budget allow)
- [ ] **F1.6** — Capture per-query metadata:retrieved chunk count + chunk_id list + reranked scores(for F2 threshold derivation analysis)

### Baseline report
- [ ] **F1.7** — Write `docs/01-planning/W26-eval-driven-retrieval-tuning/baseline-metrics-W26-D1.md`:
  - [ ] **F1.7a** — Per-query metric table(faithfulness / answer_relevancy / context_precision / context_recall)
  - [ ] **F1.7b** — Per-query retrieved chunk list + reranked scores(diagnostic)
  - [ ] **F1.7c** — Aggregated score distribution analysis(used for F2 threshold derivation Q2)
  - [ ] **F1.7d** — Recall-dominant vs precision-dominant interpretation(per brief §4 step 1 framing)
  - [ ] **F1.7e** — F2 threshold initial value recommendation(NOT magic 0.3 — grounded in F1 distribution)

### F1 closeout
- [ ] **F1.8** — Surface F1 result to Chris(AskUserQuestion or chat)— confirm proceed to F2 with derived initial threshold

## F2 — Step 1 rerank score threshold(Chris Step 1,ADR-0037)

### ADR
- [ ] **F2.1** — `docs/adr/0037-rerank-score-threshold.md` v1.0 draft per CLAUDE.md §6 ADR format
- [ ] **F2.2** — Chris approval via chat/AskUserQuestion(ADR Status: Proposed → Accepted)

### Code
- [ ] **F2.3** — `backend/retrieval/reranker/cohere.py` add score floor cutoff in `rerank()` method(filter response scores < `rerank_score_threshold`)
- [ ] **F2.4** — Cutoff fallback graceful design Q1(STOP and ask Chris):cutoff 後 < 1 chunk remaining 點處理?fallback to 1 chunk above threshold / fallback to top_n original / return empty
- [ ] **F2.5** — `backend/storage/settings.py` NEW `rerank_score_threshold: float = X.X`(initial value from F1.7e recommendation)
- [ ] **F2.6** — Module header + docstring updates(brief §7 navigation references + ADR-0037 cross-ref)

### Tests
- [ ] **F2.7** — NEW `backend/tests/test_rerank_threshold.py`:threshold cutoff filter behavior + empty result fallback + image_weight × threshold interaction(BUG-025 deboost × threshold cutoff combined scenarios)
- [ ] **F2.8** — `pytest tests/test_rerank_threshold.py -v` pass
- [ ] **F2.9** — `pytest tests/` full regression pass(1024 baseline preserved + new test count addition)
- [ ] **F2.10** — `mypy --strict --explicit-package-bases retrieval/reranker/cohere.py` clean
- [ ] **F2.11** — `ruff check retrieval/reranker/cohere.py tests/test_rerank_threshold.py` clean

### Re-eval
- [ ] **F2.12** — Restart uvicorn + `/health` 200(new threshold settings loaded)
- [ ] **F2.13** — Re-run RAGAs same queries set as F1
- [ ] **F2.14** — Write `docs/01-planning/W26-eval-driven-retrieval-tuning/step1-metrics-W26-D{N}.md` — F2 → F1 delta + interpretation(precision up / recall down quantified)
- [ ] **F2.15** — Threshold tuning iteration log(if recall regression > 5pp —降 threshold + re-eval up to 3 iterations per R3 mitigation;若 3 iter 仍 fail → STOP and ask Chris)

### F2 → F3 gate decision(MUST surface to Chris before F3 active flip)
- [ ] **F2.16** — AskUserQuestion Chris pick:**gate criteria** precision improvement ≥ TBD pp + recall regression ≤ TBD pp(grounded in F2 D6 delta data);**go/no-go decision** F3 proceed / skip / F2 re-tune

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

- [ ] **G1** — F1 baseline metrics collected(satisfied via F1.7)
- [ ] **G2** — F2 ADR-0037 Accepted by Chris(satisfied via F2.2)
- [ ] **G3** — F2 precision improvement ≥ TBD pp(satisfied via F2.14 + F2.16 gate decision)
- [ ] **G4** — F2 recall regression ≤ TBD pp(satisfied via F2.14 + F2.16 gate decision)
- [ ] **G5** — F3 conditional execution decision documented(satisfied via F3.1)
- [ ] **G6** — Backend regression preserved(satisfied via F2.9 pytest count ≥ 1024)
- [ ] **G7** — mypy + ruff clean(satisfied via F2.10 + F2.11)
