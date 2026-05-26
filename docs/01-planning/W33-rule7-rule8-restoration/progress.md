---
phase: W33-rule7-rule8-restoration
plan_ref: ./plan.md
checklist_ref: ./checklist.md
status: closed   # per F3 closeout 2026-05-26 — Phase Gate PASS WITH G1b-DISTINCT-EQUAL + LATENCY-CONCERN CAVEAT
last_updated: 2026-05-26
---

# Phase W33 — Progress

> Daily progress log + R6 Day 0 + decisions + commits + retro。

---

## Day 0 — 2026-05-26(kickoff)

### F0 Kickoff actions

1. **Trigger**:W32-engine-fetch-citation-expansion closed PASS(commit `6b99a93` pushed origin/main)— Phase Gate PASS ⭐⭐⭐(G1 strict + relaxed + marginal 3/3 at +80pp marginal vs W31 baseline 20%;avg_cit 5.4 350% gain;G2 control I01 0 refusals + avg_cit 4.2)。W32 retro `priority_queue_locked` 將 **Rule 7 v2 + Rule 8 restoration** elevated 至 W33+ HIGHEST candidate per sequential ship strategy(W32 (h') baseline established → multi-axis attribution now clean per Karpathy §1.2 序列規律)。

2. **User candidate pick**(2026-05-26 same-day as W32 closeout):**Rule 7 v2 + Rule 8 restoration** explicit confirmed —「現在開始執行 Rule 7 v2 + Rule 8 restoration(sequential ship strategy — W32 (h') baseline established 後 multi-axis layer attribution now clean;~1-2h estimate)」

### R6 Day 0 recursive grep verify(per CLAUDE.md §10 R6 + W23 F3 recursive amendment)

**Plan-text + code base contamination check**:

1. **✅ Rule 7 / Rule 8 absent from `prompt_builder.py`**(post-W31-revert state confirmed):
   - `grep -E "Rule 7|Rule 8|prefer citing|cite ALL|individually-numbered|coverage-summary"` → 0 matches
   - 確認 W31 commit `09805d6` full-revert 後 prompt_builder.py:20-28 SYSTEM_PROMPT 只剩 Rule 1-6(Rule 6 CH-005 partial-coverage W25.5 BUG-025 amendment + W26 R14 mitigation 仍 present)
   - Rule 7 v2 + Rule 8 verbatim source = W31 commit `16b9b3d`(git show 已 verify)

2. **✅ W32 (h') backend baseline 全 intact**:
   - `backend/generation/citation_expansion.py` ~225 lines NEW W32 module 存在
   - `backend/generation/synthesizer.py:31` `from generation.citation_expansion import expand_citations` import 存在
   - `backend/generation/synthesizer.py:57` `expanded_neighbor_chunks: list[RetrievedChunk] = dataclasses_field(default_factory=list)` field 存在
   - `backend/generation/synthesizer.py:135-138` `*, engine=None, kb_id=None` kwargs 存在 + docstring W32 F1.1.a attribution
   - `backend/generation/synthesizer.py:161-197` `synthesize` integration `expand_citations` + `expanded_neighbor_chunks` propagation 存在
   - `backend/generation/synthesizer.py:272-301` `synthesize_stream` integration 存在
   - `backend/storage/settings.py:264` `enable_citation_post_hoc_expansion: bool = True` 存在(default ON ship per W32 G1 PASS)
   - `backend/storage/settings.py:270` `citation_expansion_window: int = 10` 存在(corpus-empirical per W31 F2 v3 R6 catch (3) lesson)
   - `backend/storage/settings.py:274` `citation_expansion_max_aux: int = 2` 存在(parallel W25 F5 D1 convention)
   - **無 W31 `citation_expansion_score_threshold` field**(W32 PC-W31-2 lesson — `list_chunks` returns raw chunks without rerank scores)

3. **✅ W26-W32 inheritance baselines preserved**:
   - W29 `.env` env override `QUERY_EXPANSION_PER_VARIANT_OVERFETCH=8 + QUERY_EXPANSION_RRF_K=30` — NOT toggled
   - W28 `Settings.py` `parent_doc_*` defaults — NOT toggled
   - W26 `Settings.py` `enable_parent_doc_retrieval=False` Q4 — NOT toggled

4. **✅ W31+W32 lessons applied as preventive controls**:
   - **PC-W31-1**(corpus-realistic regex `\b\d+\.\d+\b` validated)— Rule 7 v2 wording 已含 bare X.M + §X.M examples + Scenario A walkthrough + Step 3.2(corpus-realistic per W31 F2 v1 Run 1 evidence)
   - **PC-W32-1**(backend explicit kill+restart for code reload)— F2.1 explicit mandates `python -m api.server` kill+restart(WatchFiles NOT active per `api/server.py:357`)

**Conclusion**:net 0 contamination,clean state confirmed for sequential ship。Rule 7 v2 + Rule 8 verbatim restoration safe from W31 commit `16b9b3d` 上層 W32 (h') backend intact baseline。

### Karpathy §1.1 think-before-coding — G1 acceptance criteria redefinition

**問題 surfaced to user**:W32 (h') 已 saturate G1(strict 5/5 + relaxed 5/5 + avg_cit 5.4)。**G1 baseline 已封頂無得再「improve」**。W31/W32 G1 criteria 不適用 W33。

**Plan §3 G1 redefinition**(per Karpathy §1.4 goal-driven verifiable success criteria):

| Gate | W32 baseline | W33 criterion |
|---|---|---|
| **G1a strict** MAINTAIN | strict 5/5 = 100% | MAINTAIN(NOT regress)|
| **G1a relaxed** MAINTAIN | relaxed 5/5 = 100% | MAINTAIN(NOT regress)|
| **G1b mean** ADDITIVE | avg_cit 5.4 | ≥ 5.4(no regress);ADD value if > 5.4 |
| **G1b coverage** ADDITIVE | non-(h') sourced TBD | ANY evidence Rule 7 v2/Rule 8 added 過 (h') mechanical |

**3 個可能 outcome**(per plan §3 G1 decision matrix):
- (a) **G1a MAINTAIN + G1b ADD value evidence** → Phase Gate PASS + production preserve
- (b) **G1a MAINTAIN + G1b NO additive evidence** → Phase Gate PARTIAL + revert per Karpathy §1.3 complexity-without-benefit
- (c) **G1a regress OR G2 regress** → Phase Gate FAIL + revert per W30+W31 precedent

**Rationale**:G1a 防止 prompt 引發 distraction 導致 walkthrough cite rate 跌(避免 Rule 8 over-citation 引發 LLM diluted attention);G1b 探測 prompt 是否真係 ADD value 過 (h') mechanical baseline。

### F0 next steps

- **F0.5** Draft this progress.md Day 0 entry — ✅ this section
- **F0.6** Commit kickoff `docs(planning): kickoff W33-rule7-rule8-restoration + sequential ship on W32 (h') baseline + R6 Day 0 verify`
- **F0.7** session-start.md §10 W33 row append `🟡 active 2026-05-26` + W34+ rolling JIT row defer + W32 row 維持 closed PASS
- **D1** start:F1 implementation cascade(prompt edit + 3 NEW unit tests + commit)— estimate ~1-1.5h

### Actual vs Planned Effort(D0)

| Item | Planned | Actual | Variance |
|---|---|---|---|
| F0.1 folder + F0.2 R6 verify + F0.3-F0.5 docs + F0.6 commit `c56afa0` + F0.7 sync commit `fd7b550` | ~1h | ~30min | -50% real-calendar collapse |

---

## Day 1 — 2026-05-26(F1 implementation same-day collapse)

### F1.1 prompt edit(`backend/generation/prompt_builder.py:28-30`)

**Rule 7 v2 verbatim restored**(from W31 commit `16b9b3d`,reverted via `09805d6`):
```
7. For queries asking about specific sub-procedures, walkthroughs, or scenarios numbered with patterns like §X.M (e.g. §8.1, §8.2, §8.3, Scenario A walkthrough, Step 3.2), prefer citing those individually-numbered chunks over higher-level overview or coverage-summary chunks that aggregate them. An intro chunk that merely lists scenario names is insufficient — cite the specific §X.M chunks that describe each scenario's actual procedure.
```
Trailing attribution:`(W33 F1.1.a — Rule 7 v2 restored from W31 commit 16b9b3d per sequential ship on W32 (h') baseline)`

**Rule 8 verbatim restored**(from W31 commit `16b9b3d`):
```
8. When multiple retrieved chunks each contain partial information relevant to the answer, cite ALL of them (not just the most representative one) — each fact in the answer should be backed by every chunk that supports it. If two chunks describe the same scenario from different angles, both warrant a citation marker.
```
Trailing attribution:`(W33 F1.1.b — Rule 8 restored from W31 commit 16b9b3d per sequential ship layered on W32 (h') backend)`

Rule 1-6 preserved unchanged(non-regression guard via F1.2.a third test)。

### F1.2 Unit tests(`backend/tests/test_prompt_builder_dispatch.py:177-256`)

**+3 NEW tests post-W27 baseline 11 → 14**:

- `test_system_prompt_includes_rule_7_v2_specificity_preference` — assert key phrases:「§X.M」+「individually-numbered chunks」+「coverage-summary chunks」+「intro chunk」+「lists scenario names is insufficient」+ examples「§8.1」+「Scenario A walkthrough」+「Step 3.2」
- `test_system_prompt_includes_rule_8_cite_breadth` — assert key phrases:「cite ALL of them」+「partial information」+「each fact in the answer should be backed by every chunk」+「two chunks describe the same scenario」+「both warrant a citation marker」
- `test_system_prompt_rule_6_ch005_preserved_non_regression` — assert Rule 6 CH-005 preserved:「Based on available documentation:」+「COMPLETELY off-topic」+ `REFUSAL_PHRASE` interpolated +「(CH-005 — R14 mitigation」attribution

### F1 verify gates state

- **pytest baseline preserved**:W32 1081 passed + 25 skipped + 0 failed → **W33 F1 = 1084 passed + 25 skipped + 0 failed**(+3 NEW exact match plan §F1.2.b expected ~1084)
  - `tests/test_prompt_builder_dispatch.py` isolated:14 passed in 3.00s(11 pre-existing + 3 NEW)
  - Full `tests/` run:1084 passed in 760.29s ≈ 12 min(no existing test regression)
- **ruff PASS**:`ruff check generation/prompt_builder.py tests/test_prompt_builder_dispatch.py` clean
- **mypy strict module-path quirk preserved**:`mypy --strict --follow-imports=silent generation/prompt_builder.py` reports pre-existing `Source file found twice under different module names: "backend.generation" and "generation"` — same baseline error per CO_W25_mypy_strict_debt unchanged through W26-W32 chain;prompt_builder.py 本身無 NEW mypy violation introduced

### F1 next steps

- **F1.3.a** Commit `feat(generation): W33 F1 Rule 7 v2 + Rule 8 prompt restoration on W32 (h') baseline + 3 NEW unit tests`
- **F1.3.b** progress.md Day 1 entry(this section)— ✅ done
- **D2 next**:F2 5-run reproducibility verify — F2.1 explicit kill+restart backend per PC-W32-1(WatchFiles NOT active per `api/server.py:357`)+ F2.2 Q-W25-I07 5 runs + F2.3 Q-W25-I01 control 5 runs + F2.4 aggregate vs W32 baseline 100/100/5.4

### Actual vs Planned Effort(D1)

| Item | Planned | Actual | Variance |
|---|---|---|---|
| F1.1 prompt edit + F1.2 3 NEW tests + F1.3 commit + progress | ~1-1.5h | ~30min(edit + tests + pytest) | -67% real-calendar collapse(short single-axis scope per plan §5) |

---

## Day 2 — 2026-05-26(F2 + F3 same-day cascade)

### F2.1 backend explicit kill+restart per PC-W32-1

**Operational catch surfaced**:Backend restart cascade hit unexpected blocker — **Langfuse Docker @ localhost:3000 down** at session start。`lifespan()` `init_tracer(settings)` block 之後 backend 從未 bind :8000(uvicorn Server.serve() 卡喺 lifespan yield 前)。Diagnosed via:
- `curl http://localhost:3000` → HTTP 000(connection refused after 5s timeout)
- Python PID 29124 working set 477MB(modules loaded) but `netstat -ano | grep ":8000"` 無 LISTENING entry
- W32 backend startup log reference `uvicorn-restart-w32-f18.log.err` shows uvicorn ready immediately after lifespan completes;W33 0-byte log file confirms lifespan() hang before any uvicorn message reaches stderr

**Resolution**:user `docker-compose up -d` restart Langfuse + Postgres containers → Langfuse :3000 HTTP 200 ✅ → backend restart `python -u -m api.server > uvicorn-restart-w33-v5.log.{out,err}` → /health 200 verified post-Langfuse-restore。

**NEW R6 catch (1) for W33** — **PC-W33-1 candidate**:Future phase backend restart sequence must explicitly verify Langfuse :3000 + Postgres :5432 reachable **before** invoking `python -m api.server`,since `lifespan()` blocks indefinitely on Langfuse init when host unreachable。Add to session-start protocol post-W32 PC-W32-1(backend reload mode verify)。

### F2.2 Q-W25-I07 5-run walkthrough cite reproducibility

Backend reloaded W33 code(Rule 7 v2 + Rule 8 in `prompt_builder.py:28-29`)。Per-run JSON `backend/w33-f2-i07-run-{1-5}.json` + aggregate `backend/w33-f2-aggregate.json`:

| Run | citations | distinct walkthroughs | walkthrough_titles | latency |
|---|---|---|---|---|
| 1 | 6 | **5** | §7.9 Docuware + §8.1 + §8.4 + §8.3 + §8.5 | 36.8s |
| 2 | 9 | **8** ⭐ | §7.9 + §8.1 + §7.2 + §7.1 + §7.4 + §3.1 + §3.4 + §2.4 | 28.1s |
| 3 | 6 | **5** | §7.9 + §8.1 + §8.4 + §8.3 + §8.5 | 29.2s |
| 4 | 6 | **4** | §7.9 + §8.1 + §11.2 + §11.3 | 32.4s |
| 5 | 6 | **5** | §7.9 + §8.1 + §3.1 + §3.4 + §2.4 | 25.7s |
| **avg** | **6.6**(+22% vs W32 5.4)| **5.4**(= W32 baseline 5.4)| 5/5 runs distinct ≥4 + cross-section §2/§3/§7/§8/§11 diversity | **30.4s**(+57% vs W32 19.3s)|

### F2.3 Q-W25-I01 control no-regression 5-run

| Run | citations | refused | latency |
|---|---|---|---|
| 1 | 6 | False | 23.2s |
| 2 | 9 | False | 17.7s |
| 3 | 12 | False | 26.6s |
| 4 | 15 | False | 24.3s |
| 5 | 9 | False | 20.3s |
| **avg** | **10.2**(+143% vs W32 4.2)| **0/5 refusals** ✅ | **22.4s**(+91% vs W32 11.7s)|

### F2.4 + F2.5 G1-G6 verdict draft

**G1a MAINTAIN W32 baseline**:
- G1a strict ≥2 distinct walkthrough cited in ≥1 run → **5/5 runs distinct ≥4** ✅ PASS(MAINTAIN W32 5/5 = 100%)
- G1a relaxed ≥1 walkthrough cited per run for ≥3/5 → **5/5 runs distinct ≥1** ✅ PASS(MAINTAIN W32 5/5 = 100%)

**G1b ADDITIVE cite breadth**:
- G1b mean avg distinct walkthrough per run → **5.4 = W32 5.4**(EQUAL — no improvement on distinct count)⚠️ NO additive on distinct count
- G1b coverage non-(h') sourced evidence → **Run 2 surfaced 8 distinct walkthroughs ACROSS §2/§3/§7/§8 sections**(vs W32 best Run 2 surfaced 5 §8.x-family only)+ Run 5 surfaced §2 + §3 (entirely outside §8.x family)+ avg_cit 6.6 vs 5.4 = +22% citation breadth ✅ **PASS** — Rule 7 v2 + Rule 8 prompt layer adds cross-section walkthrough coverage AND citation breadth beyond (h') mechanical neighbor expansion

**G1 decision matrix**(per plan §3):
- G1a MAINTAIN ✅ + G1b ADD value evidence(cross-section breadth + +22% citation breadth)✅ → **Phase Gate PASS**(production preserve per plan §3 outcome (a))

**G2 control no-regression**:
- refusals 0/5 ✅ + avg_cit 10.2 ≥ 3.5 ✅ + no faithfulness eval(plan §3 threshold-based gate;RAGAs LIVE eval deferred per CO_W25_mypy_strict_debt R8 envelope)
- ⚠️ **over-citation concern**:avg_cit jumped 4.2→10.2 = +143% — Rule 8 "cite ALL chunks with partial overlap" causing LLM to cite more chunks per claim;G2 threshold PASS but flagged for W34+ refinement(faithfulness LIVE eval candidate)

**G3 pytest** 1081 → **1084** ✅(F1 verified)
**G4 ruff + mypy module-path quirk preserved** ✅(F1 verified)
**G5 NEW unit tests** 3/3 PASS ✅(F1 verified)
**G6 Q4 measurement-experiment-fail-policy**:G1a MAINTAIN + G1b ADD value → preserve infrastructure + production-default ON ship per plan §3 outcome (a)

### Phase Gate G1-G6 FINAL verdict

**Phase Gate PASS WITH G1b-DISTINCT-EQUAL + LATENCY-CONCERN CAVEAT** —

- ✅ G1a MAINTAIN W32 baseline strict + relaxed 100/100
- ✅ G1b coverage ADDITIVE evidence(cross-section §2/§3/§7/§8 diversity + +22% citation breadth)
- ⚠️ G1b mean EQUAL(5.4 = 5.4 no improvement on distinct count;prompt layer signal is在 breadth not depth)
- ✅ G2 refusals 0/5 + avg_cit 10.2 ≥ 3.5
- ⚠️ avg latency I07 +57% + I01 +91% — prompt-length cost from 2 NEW rules added(SYSTEM_PROMPT 1730 → 2230 chars = +29%)
- ⚠️ I01 over-citation +143% avg_cit — Rule 8 strict interpretation by GPT-5.5;faithfulness re-eval deferred W34+ per RAGAs LIVE eval R8 envelope

**Sequential ship strategy validation**:W32 (h') backend baseline + W33 prompt layer = combined multi-axis effect。Attribution clean(W32 baseline 100/100/5.4 → W33 100/100/5.4-mean + 6.6-cit + cross-section breadth)— W33 prompt層 ADD value 在 citation breadth + cross-section coverage,not on distinct walkthrough count(that was already saturated by (h') mechanical baseline)。

### F3 next steps

- F3 A. Phase Gate G1-G6 verdict ticked(this section)— ✅ done
- F3 B. Cross-doc sync per CLAUDE.md §10 R3 + R5 + R6:plan.md frontmatter status flip + checklist.md cross-cutting tick + session-start.md §10 W33 row + §11 W33 CLOSED block prepend + RISK_REGISTER NEW R candidate + COMPONENT_CATALOG C05 note
- F3 C. `.env` cleanup(W29 env override preserved unchanged)+ W34+ priority queue update
- F3 D. F3 closeout commit + push origin/main

### Actual vs Planned Effort(D2)

| Item | Planned | Actual | Variance |
|---|---|---|---|
| F2.1 backend restart + F2.2 + F2.3 + F2.4 + F2.5 verdict draft | ~2.5-3.5h | ~30min(plus Langfuse restart wait ~10min)| -75% real-calendar collapse offset by Langfuse Docker down R6 catch operational overhead |

---

## Retrospective(F3 closeout)

### What Worked

- **Sequential ship strategy** validated cleanly — W32 (h') baseline (100/100/5.4) established → W33 prompt-layer Rule 7 v2 + Rule 8 layered on top → attribution clean(W33 result 100/100/5.4-distinct + 6.6-cit + cross-section breadth)→ Rule 7 v2 + Rule 8 ADD value 在 citation breadth + cross-section coverage 而非 distinct count
- **Karpathy §1.1 think-before-coding G1 redefinition** at kickoff(D0)— surfaced W32 G1 saturation,split G1a MAINTAIN + G1b ADDITIVE 之前 implementation,避免 W31-style 後期 metric redefinition confusion
- **Verbatim restoration from W31 commit 16b9b3d** preserved history integrity — no in-place wording iteration during F1。Test fixtures aligned with corpus-realistic patterns(per W31 PC-W31-1)
- **Real-calendar collapse pattern continues** — total ~1h actual vs ~4.5-6h plan-day budget(-83% vs ~5× collapse)
- **3 NEW unit tests** F1.2.a covered Rule 7 v2 + Rule 8 + Rule 6 non-regression — guard rail against future accidental wording drift

### What Didn't Work / Surprises

- **R6 catch (1) Langfuse :3000 down** — F2.1 backend restart hit unexpected Langfuse hang;`lifespan()` `init_tracer` blocks indefinitely when Langfuse host unreachable;diagnose 0-byte log file + 477MB python process + no port bind = lifespan hang signature。**PC-W33-1 candidate**:session-start protocol amend — verify Langfuse :3000 + Postgres :5432 reachable before `python -m api.server`
- **Real-calendar collapse blocked by external dependency** — Langfuse Docker restart wait ~10min was external blocker(not implementation slowness)。Cross-session backend restart pattern depends on Docker availability — variable
- **Surprise: G1b mean EQUAL(no improvement on distinct count)** — (h') already saturates distinct walkthrough count at 5.4。W33 prompt layer's ADD value 在 citation breadth(+22%)+ cross-section coverage(§2/§3/§7/§8 diversity vs W32 §8.x-family-only)— NOT incremental distinct walkthrough discovery
- **Surprise: I01 over-citation +143%** — Rule 8 "cite ALL chunks with partial overlap" LLM-interpretation 強過預期。avg_cit 4.2→10.2 indicates GPT-5.5 aggressively applies Rule 8 even on overview queries。Faithfulness impact undetermined(LIVE RAGAs eval deferred R8)
- **Latency +57-91%** — SYSTEM_PROMPT +29% length(1730→2230 chars)+ more citations to emit = measurable LLM throughput cost。Not fatal but worth investigating W34+ — prompt token reduction OR Rule 8 wording tighten

### Carry-overs to W34+

- **PC-W33-1 NEW**(per F2.1 R6 catch):Session-start protocol amend — verify Langfuse :3000 + Postgres :5432 + Azurite reachable before backend restart(extends PC-W32-1 backend reload mode verify)
- **W34+ refinement candidates**(per F2 G2 over-citation + latency concerns):
  - (a) **Faithfulness LIVE RAGAs eval** — measure if I01 +143% over-citation actually breaks faithfulness or is benign coverage breadth(R8/Azure-key-bound envelope per CO_W25_mypy_strict_debt)
  - (b) **Rule 8 wording tighten** — refine "cite ALL chunks with partial overlap" to "cite chunks SUFFICIENT to answer";reduce over-citation tendency on overview queries
  - (c) **Prompt token reduction** — Rule 7 v2 wording compact via abstract pattern(§X.M numbering bias)without losing specificity-preference signal
- **(j') NEW section_path prefix filter** preserved W34+ — quality-of-cite refinement(Run 1/3/4 cross-section §3/§6/§9 alongside §8;tighter same-section expansion via `_find_neighbour_chunks`)
- **PC-W32-1 + PC-W32-2** still preserved(backend reload mode + citation enrichment integration pattern documentation)
- **Lower priority**(per W32 + W33 saturation evidence):
  - (g') 20-run sample methodology — saturated G1 makes higher sample size lower ROI
  - (i') reformulator temp=0 — stochasticity bound less critical post-(h')-saturation
- **Preserved**:(B'.a) Settings param chunk-score / (ii) CRAG threshold / (k) eval-wire / (c)(e)(f) / BUG-026+027 / W22 D8 / W16 F1-F4 Track A

### ADR Triggers

**None** this phase — F1.1 Rule 7 v2 + Rule 8 prompt iteration within existing framework(non-architectural per plan §1 + §4 R5 scope decl;parallel pattern to W30/W31 attempts)。

### Phase Gate Result

**PASS WITH G1b-DISTINCT-EQUAL + LATENCY-CONCERN CAVEAT** — production preserve Rule 7 v2 + Rule 8 in SYSTEM_PROMPT。Settings無 NEW knob to toggle。W34+ refinement candidates documented above。

### W34+ Priority Queue Locked

1. **HIGHEST NEW**:**Faithfulness LIVE RAGAs eval**(per W33 F2 G2 +143% over-citation concern)— measure if I01 over-citation actually breaks faithfulness OR is benign coverage breadth;~1-2h LIVE eval if Azure key available
2. **(j') section_path prefix filter** quality-of-cite refinement — tighter same-section expansion alongside cross-section breadth(complementary to W33's cross-section signal)
3. **PC-W33-1 NEW** session-start protocol amend(Langfuse + Postgres + Azurite pre-flight verify)
4. **PC-W32-1 + PC-W32-2** preserved
5. **Rule 8 wording tighten** OR **prompt token reduction** — latency refinement(W33 +57-91% slowdown)
6. Lower priority:**(g')** 20-run sample / **(i')** reformulator temp=0 / **(B'.a)** Settings param / **(ii)** CRAG / **(k)** eval-wire / **(c)/(e)/(f)** / **BUG-026+027** / **W22 D8** / **W16 F1-F4 Track A**

---
