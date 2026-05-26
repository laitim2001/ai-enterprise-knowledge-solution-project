---
phase: W33-rule7-rule8-restoration
status: closed   # per F3 closeout 2026-05-26 — Phase Gate PASS WITH G1b-DISTINCT-EQUAL + LATENCY-CONCERN CAVEAT (G1a MAINTAIN 100/100 + G1b ADDITIVE cross-section breadth + G2 control no refusal regression)
last_updated: 2026-05-26
component_scope: C05 Generation Pipeline
adr_refs:
  - ADR-0034 (W25 F3 D4 query expansion + RAG-Fusion — W33 preserves W29 .env tune)
  - ADR-0037 (W26 F2 parent-doc — Settings preserved per W28 best combo + Q4 default OFF)
  - ADR-0038 (W27 dispatch_mode — preserved "replace" per W28 reaffirmation)
  - W25 F5 D1 citation_image_neighbors.py (image attach pattern unchanged)
  - W32 F1+F1.8 citation_expansion engine-fetch (h') ON default — W33 layered prompt restoration
related_carry_overs:
  - W32 retro W33+ HIGHEST candidate — Rule 7 v2 + Rule 8 restoration per sequential ship strategy(h' baseline established → multi-axis attribution now clean)
  - W31 reverted Rule 7 v2 + Rule 8 wording verbatim from commit `16b9b3d`
  - W30 reverted Rule 7 abstract「specific subsection」wording — W31 v2 corpus-realistic replacement preserved
  - Sequential ship strategy locked — W33 ship prompt layer ONLY on top of W32 (h') backend baseline
---

# W33 — Rule 7 v2 + Rule 8 Restoration(sequential ship on W32 (h') baseline)

## §1 Goal + Scope

**Single primary goal**:Layer prompt-layer cite-decision guidance(Rule 7 v2 specificity preference + Rule 8 multi-cite breadth)on top of **W32 (h') engine-fetch citation expansion** mechanical baseline。**Sequential ship strategy** per W31→W32 lesson — W32 (h') already established +80pp G1 marginal clean attribution(100/100 saturation + avg_cit 5.4),W33 measures whether prompt layer adds **incremental value** over the saturated mechanical baseline OR is **redundant**。

**Critical framing differences vs W31 multi-axis ship**:
- W31 shipped Rule 7 v2 + Rule 8 + B'.c citation_expansion **simultaneously** → multi-axis attribution mess → 3 重 R6 catches + full revert
- W32 shipped (h') engine-fetch **alone** → clean +80pp G1 marginal attribution
- **W33 ships Rule 7 v2 + Rule 8 alone on top of W32 baseline** → clean attribution to prompt layer

**Single-axis scope**(per W32 retro recommendation):

**Axis 1 — Prompt layer Rule 7 v2 + Rule 8 restoration**(prompt layer,~1-2h total estimate)
- Restore verbatim wording from W31 commit `16b9b3d`(reverted via `09805d6` per Karpathy §1.3 full revert)
- Rule 7 v2:specificity preference — cite individually-numbered §X.M chunks over higher-level overview/coverage-summary chunks
- Rule 8:cite breadth — cite ALL retrieved chunks that contain partial information relevant to the answer
- NO Settings change(no NEW knobs;prompt-only edit)
- NO synthesizer change(W32 wire intact)
- NO citation_expansion module change(W32 (h') backend intact)

**Non-goals**(out of W33 scope):
- W32 citation_expansion default flip — preserved ON per W32 G1 PASS evidence
- (B'.a) Settings parameter chunk-score threshold pre-pend — defer W34+
- (g') 20-run sample methodology — defer W34+ if W33 signal borderline
- (i') reformulator deterministic temp=0 — defer W34+ orthogonal axis
- (ii) CRAG threshold trial — preserved low priority
- (k) wire reformulator into eval/orchestrator.py — orthogonal axis
- (j') section_path prefix filter quality-of-cite — defer W34+

**Component scope**:**C05 Generation Pipeline only**(`backend/generation/prompt_builder.py` SYSTEM_PROMPT edit + `backend/tests/test_prompt_builder_dispatch.py` +3 NEW unit tests)。**No** C04 Retrieval Engine / C03 Indexing / C01 Ingestion / C06 Eval / C08 API Gateway / C09-C13 frontend / mockup changes / W32 citation_expansion module change(per Karpathy §1.3 surgical)。

---

## §2 Deliverables F0-F3

### F0 — Kickoff(this session 2026-05-26)

- F0.1 Create `docs/01-planning/W33-rule7-rule8-restoration/` folder
- F0.2 R6 Day 0 recursive grep verify(plan-text + code base contamination check per CLAUDE.md §10 R6)— verify Rule 7/8 absent post-W31-revert + W32 (h') intact + W29/W28/W26 baselines preserved
- F0.3 Draft `plan.md` 7-section per W32 closed-phase template
- F0.4 Draft `checklist.md` atomic items per plan deliverables(this file's siblings)
- F0.5 Draft `progress.md` Day 0 entry — kickoff action + R6 catch report + W32 sequential ship rationale + Karpathy §1.1 think-before-coding G1 redefinition surfaced to user
- F0.6 Commit kickoff `docs(planning): kickoff W33-rule7-rule8-restoration + sequential ship on W32 (h') baseline + R6 Day 0 verify`
- F0.7 session-start.md §10 W33 row append `🟡 active 2026-05-26` + W34+ rolling JIT row defer + W32 row 維持 closed PASS

### F1 — Implementation(D1 estimate — short single-axis ~1-2h)

**F1.1 Prompt layer edit**(`backend/generation/prompt_builder.py:20-28` SYSTEM_PROMPT)

- F1.1.a Add NEW Rule 7 v2 — verbatim from W31 commit `16b9b3d`:
  ```
  7. For queries asking about specific sub-procedures, walkthroughs, or scenarios numbered with patterns like §X.M (e.g. §8.1, §8.2, §8.3, Scenario A walkthrough, Step 3.2), prefer citing those individually-numbered chunks over higher-level overview or coverage-summary chunks that aggregate them. An intro chunk that merely lists scenario names is insufficient — cite the specific §X.M chunks that describe each scenario's actual procedure.
  ```
  Trailing attribution comment:`(W33 F1.1.a — Rule 7 v2 restored from W31 commit 16b9b3d per sequential ship on W32 (h') baseline)`

- F1.1.b Add NEW Rule 8 — verbatim from W31 commit `16b9b3d`:
  ```
  8. When multiple retrieved chunks each contain partial information relevant to the answer, cite ALL of them (not just the most representative one) — each fact in the answer should be backed by every chunk that supports it. If two chunks describe the same scenario from different angles, both warrant a citation marker.
  ```
  Trailing attribution comment:`(W33 F1.1.b — Rule 8 restored from W31 commit 16b9b3d per sequential ship layered on W32 (h') backend)`

- F1.1.c Preserve Rule 1-6 unchanged(citation marker + refusal phrase + 150-word answer + language match + no fabricate + CH-005 partial-coverage Rule 6)

### F1.2 Unit tests + non-regression coverage

- F1.2.a `test_prompt_builder_dispatch.py` +3 NEW tests:
  - `test_system_prompt_includes_rule_7_v2_specificity_preference` — assert Rule 7 v2 key phrases present(「§X.M numbering」+「individually-numbered chunks」+「coverage-summary chunks」+「intro chunk」)
  - `test_system_prompt_includes_rule_8_cite_breadth` — assert Rule 8 key phrases present(「cite ALL of them」+「partial information」+「each fact in the answer should be backed by every chunk」)
  - `test_system_prompt_rule_6_ch005_preserved_non_regression` — assert Rule 6 CH-005 「Based on available documentation:」framing + 「COMPLETELY off-topic」+ refusal phrase reference 仍 present(non-regression guard against accidental Rule 6 wording shift during multi-rule edit)

- F1.2.b backend pytest baseline `1081 passed + 25 skipped + 0 failed`(W32 closeout) → expected ~`1084 passed + 25 skipped + 0 failed` post-W33 F1(+3 NEW prompt tests)

- F1.2.c ruff PASS on touched files

- F1.2.d mypy strict module-path quirk preserved(pre-existing 13 errors per CO_W25_mypy_strict_debt unchanged;prompt_builder.py 已喺 mypy clean baseline per existing W26-W27 dispatch tests)

### F1.3 Commit + progress.md Day 1

- F1.3.a Commit `feat(generation): W33 F1 Rule 7 v2 + Rule 8 prompt restoration on W32 (h') baseline + 3 NEW unit tests` per CLAUDE.md R2 daily commit binding
- F1.3.b progress.md Day 1 entry — implementation summary(verbatim restoration evidence)+ test verdict + ruff/mypy state + commit hash backfill

### F2 — 5-run reproducibility verify Q-W25-I07 + Q-W25-I01 control(D2 estimate)

- F2.1 Backend reload verify — explicit kill + restart `python -m api.server`(per W32 R6 catch (4) lesson — `api/server.py:357` no `reload=True`,WatchFiles NOT active,must explicit kill+restart for code changes to take effect)
- F2.2 curl POST /query Q-W25-I07「show me all the Integration scenarios」5 runs back-to-back — per-run JSON in `backend/w33-f2-i07-multi-run-{1-5}.json`
- F2.3 curl POST /query Q-W25-I01「what is the high level architecture」5 runs back-to-back(control)— per-run JSON `backend/w33-f2-i01-multi-run-{1-5}.json`
- F2.4 Aggregate report inline progress.md F2 — Q-I07 distinct walkthrough cite count vs W32 baseline 5.4 / Q-I01 G2 no regression check / G1a-G1b-G2-G3-G4-G5-G6 verdict draft
- F2.5 progress.md Day 2 F2 entry — 5-run table + cumulative baseline comparison(W31 reverted 20% → W32 (h') 100/100/5.4 → W33 ?)+ G1 verdict draft

### F3 — Closeout — Phase Gate + cross-doc sync + commit + push

**A. Phase Gate G1a-G1b-G2-G3-G4-G5-G6 evaluation**

- G1a MAINTAIN W32 baseline strict 5/5 + relaxed 5/5
- G1b ADDITIVE cite breadth — avg distinct §X.M walkthrough cited per run vs W32 baseline 5.4
- G2 control Q-W25-I01 no regression(refusals 0/5 + avg_cit ≥ 4.2 + faithfulness within W32 baseline)
- G3 backend pytest baseline preserved 1081 → ~1084
- G4 ruff + mypy preserved
- G5 NEW unit tests PASS F1.2.a
- G6 measurement-experiment-fail-policy per Q4 — outcome-driven decision matrix(see §3 below)

**B. Cross-doc sync per CLAUDE.md §10 R3 + R5 + R6**

- plan.md frontmatter status flip(active → closed / closed_partial)
- checklist.md cross-cutting tick + N/A reason
- progress.md retro 7-section
- session-start.md §10 W33 row + §11 W33 CLOSED block prepend
- RISK_REGISTER NEW R candidate evaluate(prompt over-citation risk — if Rule 8 引發 G2 regression)
- COMPONENT_CATALOG C05 status note(no change expected — prompt iteration within existing framework)
- ADR README — no NEW ADR(F1.1 prompt iteration within existing framework parallel to W30/W31 attempts;non-architectural per §1 scope decl)

**C. `.env` cleanup + W34+ priority queue evaluation**

- W29 `.env` env override preserved unchanged
- W34+ candidate prioritization update per F3 outcome — (j') section_path filter / (B'.a) Settings parameter chunk-score / (g') 20-run methodology / (i') reformulator temp=0 / (ii) CRAG threshold / (k) eval-wire / (c)/(e)/(f)/BUG-026+027 carry-overs

**D. Commit + push**

- F3 closeout commit — combined with F2 evidence(per W31+W32 closeout pattern)
- Push origin/main(per W32 pattern)

---

## §3 Acceptance Criteria(G1a-G1b-G2-G3-G4-G5-G6)

### G1a PRIMARY — MAINTAIN W32 baseline(no regression)

| Gate | Criterion | W32 baseline | Verdict logic |
|---|---|---|---|
| **G1a strict** | ≥ 2 distinct §X.M walkthrough cited in ≥ 1 run | strict 5/5 = 100% | PASS / FAIL(MAINTAIN W32 baseline)|
| **G1a relaxed** | ≥ 1 §X.M walkthrough cited per run for ≥ 3/5 | relaxed 5/5 = 100% | PASS / FAIL(MAINTAIN W32 baseline)|

### G1b SECONDARY — ADDITIVE cite breadth(NEW W33 metric)

| Gate | Criterion | W32 baseline | Verdict logic |
|---|---|---|---|
| **G1b mean** | avg distinct §X.M walkthrough cited per run | 5.4 | PASS if ≥ 5.4(no regression);ADD value if > 5.4 |
| **G1b coverage** | non-(h') sourced walkthrough citations(LLM cited §X.M not from engine-fetch expansion)| baseline TBD per F2 evidence | PASS if any evidence Rule 7 v2/Rule 8 added beyond (h') mechanical |

**G1 decision matrix**:
- **G1a MAINTAIN + G1b ADD value evidence** → **Phase Gate PASS** + production ON ship + Rule 7 v2 + Rule 8 preserved
- **G1a MAINTAIN + G1b NO additive evidence**(redundant with (h')) → **Phase Gate PARTIAL** + revert per Karpathy §1.3 complexity-without-benefit
- **G1a regress**(W32 baseline drops below 100/100 strict/relaxed) → **Phase Gate FAIL** + revert per Karpathy §1.3 + W30+W31 precedent
- **G2 regress**(I01 faithfulness drop OR refusals appear OR avg_cit drop) → **Phase Gate FAIL** + revert per Q4 measurement-experiment-fail-policy

### G2 control Q-W25-I01 no regression

| Metric | W32 baseline | Threshold |
|---|---|---|
| refusals | 0/5 | 0/5 strict |
| avg_cit | 4.2 | ≥ 3.5(allow drift)|
| avg_latency | TBD per F2 | within ±20% W32 |

### G3 backend pytest baseline preserved

1081(W32 closeout)→ expected ~1084 post-W33 F1。No existing test regression。

### G4 ruff PASS + mypy strict module-path quirk preserved

新 touch files clean;pre-existing 13 errors per CO_W25_mypy_strict_debt unchanged。

### G5 NEW unit tests PASS

F1.2.a 3 NEW tests all PASS。

### G6 Q4 measurement-experiment-fail-policy

Per ADR-0037 Q4 + W26+W27+W30+W31+W32 precedent:
- **G1a MAINTAIN + G1b ADD value evidence** → preserve infrastructure + production ON ship
- **G1a MAINTAIN + G1b NO additive evidence** → revert per Karpathy §1.3 surgical(complexity-without-benefit — same logic as W30 Rule 7 v1 revert)
- **G1a regress OR G2 regress** → revert per W30+W31 precedent

---

## §4 R1-R6 Sprint Rules(per CLAUDE.md §10 binding)

- **R1** plan.md committed before F1 code(F0.6 commit kickoff this session)
- **R2** daily commits correspond to progress.md Day-N entries(F0.6 D0 + F1.3 D1 + F3 closeout)
- **R3** plan deviation logged in §7 changelog(no silent drift)
- **R4** OQ resolved → decision-form.md + progress.md Day-N sync(none expected — pure C05 prompt iteration)
- **R5** ADR if architectural decision(per H1)— F1.1 prompt iteration within existing framework,non-architectural per §1 scope decl
- **R6** Day 0 recursive grep verify(F0.2 below)+ pre-active-flip 5-step grep verification per W23 F3 amendment(recursive plan-text + code base)

---

## §5 D0-D1-D2 Day Breakdown Estimate

| Day | Deliverables | Effort | Verify |
|---|---|---|---|
| **D0(this session 2026-05-26)** | F0.1-F0.7 kickoff | ~1h | plan/checklist/progress committed + R6 verify |
| **D1** | F1.1 prompt edit(~30min)+ F1.2 tests(~30min)+ F1.3 commit + progress = ~1-1.5h | partial D1 | backend pytest ~1084 + ruff + mypy clean |
| **D2** | F2 5-run reproducibility(~1h backend reload + 10 curl runs + aggregate)+ F3 phase Gate(~30min)+ F3 closeout(~1-2h)= ~2.5-3.5h | partial D2 | G1-G6 verdict + commit + push |

**Total**:~4.5-6h actual work spread across D0-D2 calendar(real-calendar collapse pattern continues — likely same-day 1-2× collapse given simpler scope vs W32's 11-16h estimate)。

---

## §6 W32 Carry-overs + Dependencies

### Preserved baseline(W26-W32 inheritance)

- **W29 `.env` env override**:`QUERY_EXPANSION_PER_VARIANT_OVERFETCH=8` + `QUERY_EXPANSION_RRF_K=30`(retrieval-side +40pp Path A tune,W30+W31+W32+W33 baseline)
- **W28 `Settings.py` defaults**:`parent_doc_max_tokens_per_parent=2000` + `parent_doc_top_k=2` + `parent_doc_dispatch_mode="replace"`(W28 best combo,W33 inherits)
- **W26 `Settings.py` Q4**:`enable_parent_doc_retrieval=False`(measurement-experiment-fail-policy preserved,W33 NOT toggle)
- **W32 (h') Settings**:`enable_citation_post_hoc_expansion=True`(default ON ship per W32 G1 PASS evidence)+ `citation_expansion_window=10` + `citation_expansion_max_aux=2`(W32 production-default,W33 inherits)
- **W25 F5 D1 baseline**:`enable_citation_neighbour_images=True` + `citation_neighbour_window=3` + `citation_neighbour_max_aux_images=2`(image attach unchanged)

### Dependencies on prior infrastructure

- **W32 F1+F1.8 `citation_expansion.py`**:`expand_citations` async function provides mechanical baseline — W33 layered on top
- **W32 `synthesizer.py` wire**:`Synthesizer.synthesize/_stream(..., *, engine=None, kb_id=None)` kwargs already plumbed via `query.py:208/382` + `crag.py:414` — no further wire change
- **W32 `SynthesisResult.expanded_neighbor_chunks`** field provides pre-build_citations integration — no further integration change

### W31+W32 lessons applied as preventive controls

- **PC-W31-1**:Corpus-realistic chunk_title regex `\b\d+\.\d+\b` validated in W31 F2 + W32 F1 reused — W33 prompt wording aligned with corpus (bare X.M + §X.M both mentioned)
- **PC-W31-2**:N/A this phase(no NEW Settings knob)
- **PC-W31-3**:N/A this phase(no NEW window/threshold tuning)
- **PC-W32-1**:**MANDATORY backend explicit kill+restart for code reload** — `api/server.py:357` no `reload=True`,WatchFiles NOT active;F2.1 explicit verify
- **PC-W32-2**:N/A this phase(no NEW citation pipeline integration — Rule 7/8 prompt-only,W32 backend pipeline 不變)
- **Sequential ship strategy**:W33 ships prompt layer ONLY,W32 backend (h') intact — multi-axis attribution clean per W32 closeout lesson

### Out of W33 scope(W34+ candidates)

- **(j')** section_path prefix filter quality-of-cite refinement — preserve W34+ if W33 PASS
- **(B'.a)** Settings parameter chunk-score threshold pre-pend — preserve W34+
- **(g')** 20-run sample methodology — preserve W34+ if W33 borderline
- **(i')** reformulator deterministic temp=0 + fixed seed — preserve W34+ orthogonal axis
- **(ii)** CRAG threshold trial — H1 boundary downgrade preserved low priority
- **(k)** wire reformulator into eval/orchestrator.py — H4 systemic gap orthogonal axis
- (c) RAGAs orchestrator-aware judge tune
- NEW (e) `make_ragas_evaluator` structlog stage
- NEW (f) Settings-default-tests
- BUG-026 + BUG-027 cosmetic
- W22 D8 setup.md §8.6
- W16 F1-F4 Track A IT cred parallel track Q11 operational early June 2026

---

## §7 Changelog

| Date | Section | Change | Reason |
|---|---|---|---|
| 2026-05-26 | initial | Plan drafted F0 D0 kickoff | W32 retro carry-over W33+ HIGHEST candidate Rule 7 v2 + Rule 8 restoration per sequential ship strategy + user explicit pick 2026-05-26 |
| 2026-05-26 | §1 + §3 | G1 redefinition — split into G1a MAINTAIN W32 baseline + G1b ADDITIVE cite breadth(NEW W33 metric) | W32 (h') saturated G1 at 100/100/5.4 — W31/W32 G1 criteria 不適用 W33;Karpathy §1.1 think-before-coding surfaced redefinition to user 2026-05-26 |
| 2026-05-26 | §6 | W32 (h') backend baseline intact + W26-W32 .env/Settings preserved confirmed at kickoff | R6 Day 0 recursive grep verify per CLAUDE.md §10 R6 + W23 F3 amendment(plan-text recursive scope) |
| 2026-05-26 | F2.1 | Backend restart cascade hit Langfuse :3000 down hang | R6 catch (1):`lifespan()` `init_tracer` blocks indefinitely when Langfuse host unreachable;diagnose via 0-byte log file + 477MB python + no port bind = lifespan hang signature;user `docker-compose up -d` restart Langfuse + Postgres restored backend startup。**PC-W33-1 NEW** candidate per session-start protocol amend |
| 2026-05-26 | F3 | Phase Gate **PASS WITH G1b-DISTINCT-EQUAL + LATENCY-CONCERN CAVEAT** | G1a MAINTAIN W32 baseline 100/100 ✅ + G1b ADDITIVE cross-section breadth(Run 2 8 distinct §2/§3/§7/§8 walkthroughs + avg_cit 6.6 vs 5.4 +22%)✅ + G2 control refusals 0/5 + avg_cit 10.2 ≥ 3.5 ✅ + G3-G6 ✅;Caveats:G1b mean EQUAL(5.4 = 5.4 no improvement on distinct count;(h') already saturates)+ avg latency I07 +57% / I01 +91%(prompt-length cost from 2 NEW rules +29% SYSTEM_PROMPT chars)+ I01 over-citation +143%(Rule 8 strict LLM interpretation;faithfulness LIVE eval deferred W34+ R8 envelope)。Production preserve per Q4 G1a + G1b ADD value evidence outcome (a) |
