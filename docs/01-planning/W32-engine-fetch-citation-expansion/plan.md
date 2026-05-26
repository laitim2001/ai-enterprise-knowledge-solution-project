---
phase: W32-engine-fetch-citation-expansion
status: closed   # per F3 closeout 2026-05-26 — Phase Gate PASS (G1 strict + relaxed + marginal 3/3 PASS at +80pp marginal vs W31 baseline 20%)
last_updated: 2026-05-26
component_scope: C05 Generation Pipeline
adr_refs:
  - ADR-0034 (W25 F3 D4 query expansion + RAG-Fusion — W32 preserves W29 .env tune)
  - ADR-0037 (W26 F2 parent-doc — Settings preserved per W28 best combo + Q4 default OFF)
  - ADR-0038 (W27 dispatch_mode — preserved "replace" per W28 reaffirmation)
  - W25 F5 D1 citation_image_neighbors.py (parallel pattern mirror for engine-fetch)
related_carry_overs:
  - W31 retro W32+ HIGHEST candidate (h') engine-fetch B'.c path 3 — async `engine.list_chunks` from full doc(escapes W31 window=3 constraint per F2 v3 R6 catch (3))
  - W31 F2 3 重 R6 catches catalogued — preventive controls PC-W31-1/2/3 applied
  - W31 sequential ship strategy locked — W32 ship (h') ONLY,no concurrent prompt change(W31 multi-axis trap lesson)
---

# W32 — Engine-Fetch Citation Expansion(B'.c path 3 single-axis ship)

## §1 Goal + Scope

**Single primary goal**:Escape W31 F2 v3 R6 catch (3)`citation_expansion_window=3` architectural constraint by fetching ±N chunks from **full doc**(via `engine.list_chunks(kb_id, doc_id)` async)instead of top-K reranked subset。Goal:walkthrough cite rate 5-run ≥ 60%(3/5)— **expansion CAN fire** regardless of reformulator stochasticity surfacing §X.M walkthroughs in top-K。

**Sequential ship per W31 multi-axis lesson**:**(h') ONLY** this phase — no concurrent prompt change(Rule 7 v2 / Rule 8 reverted per W31 F4)。Single-axis attribution clean — any G1 marginal improvement directly attributable to engine-fetch B'.c path 3。

**Single-axis scope**(per W31 retro priority queue):

**Axis 1 — Engine-fetch B'.c path 3**(backend layer,~1-2 days)
- NEW async `expand_citations(answer_text, citation_ids, chunks, *, engine, kb_id, settings) → (expanded_text, expanded_citation_ids)`
- Mirror W25 F5 D1 `attach_neighbour_images` pattern:`engine.list_chunks(kb_id, doc_id)` async fetch per cited doc + per-doc dedup
- Operate on FULL doc chunks(not top-K reranked subset)— escapes W31 window=3 architectural constraint per F2 v3 R6 catch (3)
- Same §X.M title regex `\b\d+\.\d+\b`(W31 F2 v2 corpus-validated per PC-W31-1)
- Default `citation_expansion_window: int = 10`(W31 F2 evidence — §8.1-§8.5 walkthroughs at idx 46/48/50/51/53 within ±10 of intro idx 44)
- NO `score_threshold` field(W31 PC-W31-2 lesson — `list_chunks` returns raw Azure Search chunks without rerank scores;score filter N/A here)
- Default `citation_expansion_max_aux: int = 2`(W25 F5 D1 parallel cap)

**Non-goals**(out of W32 scope):
- Rule 7 v2 + Rule 8 prompt iteration — W31 reverted,defer W33+ if (h') marginal
- (B'.a) Settings parameter chunk-score threshold pre-pend — defer W34+
- (g') 20-run sample methodology — defer W33+ if (h') metric signal borderline
- (i') reformulator deterministic temp=0 — defer W33+ stochasticity control orthogonal
- (ii) CRAG threshold trial — H1 boundary downgrade preserved low priority
- (k) wire reformulator into eval/orchestrator.py — H4 systemic gap orthogonal axis
- ADR-0037 default flip / parent-doc enable — preserved per Q4 measurement-experiment-fail-policy

**Component scope**:**C05 Generation Pipeline only**(NEW `backend/generation/citation_expansion.py` async module + `backend/storage/settings.py` 3 NEW knobs + `backend/generation/synthesizer.py` wire passing `engine + kb_id`)。Also touches `backend/generation/stream_composer.py` (or similar) to flow `engine + kb_id` to synthesizer if not already plumbed。**No** C04 Retrieval Engine internal change(only consumes existing `list_chunks` API)/ C03 Indexing / C01 Ingestion / C06 Eval / C08 API Gateway / C09-C13 frontend / mockup changes(per Karpathy §1.3 surgical)。

---

## §2 Deliverables F0-F3

### F0 — Kickoff(this session 2026-05-26)

- F0.1 Create `docs/01-planning/W32-engine-fetch-citation-expansion/` folder
- F0.2 R6 Day 0 recursive grep verify(plan-text + code base contamination check per CLAUDE.md §10 R6)
- F0.3 Draft `plan.md` 7-section per W30+W31 closed-phase template
- F0.4 Draft `checklist.md` atomic items per plan deliverables
- F0.5 Draft `progress.md` Day 0 entry — kickoff action + R6 catch report + W31 lessons applied
- F0.6 Commit kickoff `docs(planning): kickoff W32-engine-fetch-citation-expansion + (h') single-axis ship per W31 multi-axis lesson + R6 Day 0 net 0 contamination`
- F0.7 session-start.md §10 W32 row append + W33+ rolling JIT row defer + W31 row 維持 closed_partial

### F1 — Implementation(D1 estimate)

**F1.1 Synthesizer wire signature change**(`backend/generation/synthesizer.py`)
- F1.1.a `Synthesizer.synthesize(query, chunks)` → `Synthesizer.synthesize(query, chunks, *, engine=None, kb_id=None)`(default None for backward compat)
- F1.1.b `Synthesizer.synthesize_stream(query, chunks)` → same kwarg additions
- F1.1.c Caller site update — `backend/api/routes/query.py`(or `pipeline/query_pipeline.py`)passes `engine + kb_id` from existing pipeline state
- F1.1.d Backward compat:if `engine is None or kb_id is None` → skip expansion(W25 F5 D1 attach_neighbour_images pattern at line 61-62 same defensive return)

**F1.2 Backend layer NEW async module**(`backend/generation/citation_expansion.py`)
- F1.2.a `async def expand_citations(answer_text: str, citation_ids: list[str], chunks: list[RetrievedChunk], *, engine: RetrievalEngine, kb_id: str, settings: Settings) → tuple[str, list[str]]` async signature
- F1.2.b Algorithm:
  1. For each `[chunk-{id}]` marker → look up cited chunk in `chunks`(top-K reranked,for `doc_id` + `chunk_index` lookup ONLY)
  2. Group cited chunks by unique `doc_id`(W25 F5 D1 line 65-66 batch pattern)
  3. Parallel `asyncio.gather` `engine.list_chunks(kb_id, doc_id)` per unique doc(W25 F5 D1 line 71-74 pattern)
  4. For each cited chunk + its doc's full chunk list:
     - Find chunks within ±window of cited chunk_index(EXCLUDING self + already cited)
     - Filter to chunks with title regex `\b\d+\.\d+\b`(corpus-validated pattern per W31 PC-W31-1)
     - Sort by absolute distance + take top `max_aux`
- F1.2.c Auto-insert `[chunk-{neighbor_id}]` markers after existing per W31 F1.2.c pattern preserved
- F1.2.d Defensive:per-doc fetch exception → log warning + skip that doc's expansion(W25 F5 D1 line 86-92 graceful degradation pattern)
- F1.2.e Pure function purity preserved at filter logic(`_find_neighbour_chunks` private helper testable without engine,parallel to W25 F5 D1 `_find_neighbour_images`)

**F1.3 Settings NEW knobs**(`backend/storage/settings.py`)
- F1.3.a `enable_citation_post_hoc_expansion: bool = True`(W32 default ON per Karpathy §1.4 goal-driven measurement;F3 will decide preserve/revert per Q4)
- F1.3.b `citation_expansion_window: int = 10`(W31 F2 v3 R6 catch (3) lesson — wider window covers §X.1-§X.5 from intro;tunable F3 per evidence)
- F1.3.c `citation_expansion_max_aux: int = 2`(parallel W25 F5 D1 + W31 reverted convention)
- F1.3.d **NO `citation_expansion_score_threshold`** — `engine.list_chunks` returns raw Azure Search chunks without rerank score;score filter N/A per W31 PC-W31-2 lesson

**F1.4 Caller wire update**(`backend/api/routes/query.py` OR `pipeline/query_pipeline.py`)
- F1.4.a Locate Synthesizer caller — pass `engine + kb_id` through pipeline state(already available since `RetrievalEngine.retrieve` was called earlier with `kb_id`)
- F1.4.b Backward compat:if `engine is None` (legacy callers / tests) → expand_citations no-op gracefully

**F1.5 Unit tests + non-regression coverage**
- F1.5.a NEW `backend/tests/test_citation_expansion.py` — async unit tests covering:
  - disabled flag returns inputs unchanged
  - empty citation_ids OR empty chunks no-op
  - happy path:cited intro + 2 §X.M doc-neighbors via mocked `engine.list_chunks`
  - corpus bare X.M pattern(not just §X.M)
  - window boundary inclusive/exclusive
  - max_aux cap
  - dedupe against existing citation_ids
  - same doc constraint(cited from doc-A,fetched chunks doc-A only)
  - cited chunk not in `chunks` list defensive skip
  - per-doc fetch exception graceful degradation
  - `_find_neighbour_chunks` pure unit(no engine,no async — testable in isolation per W25 F5 D1 line 135-145 pattern)
  - 12+ NEW tests target(>= W31 F1.5.b 15-test baseline,scaled for async complexity)
- F1.5.b `test_synthesizer.py` extend — 2 NEW async tests:
  - `synthesize` wires `expand_citations` when `engine + kb_id` provided
  - `synthesize` skips expansion when refused (no citations)
- F1.5.c backend pytest baseline 1060 → expected ~1072-1075 post-W32 F1(+12-15 NEW tests)
- F1.5.d ruff PASS on touched files
- F1.5.e mypy strict citation_expansion.py clean(pre-existing W26 baseline module-path quirk per CO_W25_mypy_strict_debt unchanged)

**F1.6 commit + progress.md Day 1**
- F1.6.a Commit `feat(generation): W32 F1 engine-fetch citation expansion + async list_chunks per W31 (h') candidate + 12+ NEW unit tests` per CLAUDE.md R2 daily commit binding
- F1.6.b progress.md Day 1 entry — implementation summary + test verdict + ruff/mypy state + commit hash backfill

### F2 — 5-run reproducibility verify Q-W25-I07 + Q-W25-I01 control(D2 estimate)

- F2.1 Backend reload via `touch backend/generation/citation_expansion.py` + WatchFiles trigger + /health=ok verify
- F2.2 curl POST /query Q-W25-I07「show me all the Integration scenarios」5 runs back-to-back — per-run JSON `backend/w32-f2-i07-multi-run-{1-5}.json`
- F2.3 curl POST /query Q-W25-I01「what is the high level architecture」5 runs back-to-back(control)— per-run JSON `backend/w32-f2-i01-multi-run-{1-5}.json`
- F2.4 Aggregate report inline progress.md F2 — Q-I07 walkthrough cite rate vs W29+W30+W31 baselines / Q-I01 G2 no regression / G1-G6 verdict draft
- F2.5 progress.md Day 2 F2 entry — 5-run table + cumulative baseline comparison + expansion fired count + G1 verdict draft

### F3 — Closeout — Phase Gate + cross-doc sync + commit + push

**A. Phase Gate G1-G6 evaluation**

- G1 PRIMARY 5-run walkthrough_cite_rate vs W29+W30+W31 cumulative baseline ~20%(13.3% W31 3-batch avg + 20% W29/W30)
- G2 control Q-W25-I01 no regression
- G3 backend pytest baseline preserved
- G4 ruff + mypy clean
- G5 NEW unit tests PASS
- G6 measurement-experiment-fail-policy per Q4 — G1 fully FAIL → revert per Karpathy §1.3 + W30+W31 precedent

**B. Cross-doc sync per CLAUDE.md §10 R3 + R5 + R6**

- plan.md frontmatter status flip
- checklist.md cross-cutting tick + N/A reason
- progress.md retro 7-section
- session-start.md §10 W32 row + §11 W32 CLOSED block prepend

**C. `.env` cleanup + W33+ priority queue evaluation**

- W29 `.env` env override preserved
- W33+ candidate prioritization per F3 outcome

**D. Commit + push**

- F3 closeout commit
- Push origin/main

---

## §3 Acceptance Criteria(G1-G6)

### G1 PRIMARY — Walkthrough cite rate 5-run vs W31 v3 baseline 20%

| Gate level | Criterion | Verdict logic |
|---|---|---|
| **G1 strict** | ≥ 2 distinct §X.M walkthrough cited in ≥ 1 run | PASS / FAIL |
| **G1 relaxed** | ≥ 1 §X.M walkthrough cited per run for ≥ 3/5 | PASS / FAIL |
| **G1 marginal** | > 40pp improvement vs W31 v3 baseline 20%(target 5-run ≥ 60% = 3/5)| PASS / FAIL |

**G1 decision matrix**:
- **3/3 PASS** → Phase Gate PASS + production ON default + W33+ priority queue re-rank
- **G1 strict OR relaxed PASS,marginal FAIL** → Phase Gate PARTIAL(infrastructure preserve;tune `citation_expansion_window`)
- **G1 marginal PASS only**(strict + relaxed FAIL)→ Phase Gate PARTIAL(behavior improvement detected but未達 target)
- **G1 全 FAIL**(0pp 改善 vs W31 baseline 20%)→ Phase Gate FAIL + revert per Karpathy §1.3 + W30+W31 precedent

### G2 control Q-W25-I01 no regression

faithfulness within W31 v3 baseline F1 0.9851 ±2pp;refusals 0/5;avg_cit ≥ 1.5(W31 v3 I01 baseline 2.2)。

### G3 backend pytest baseline preserved

1060(W31 post-revert baseline)→ expected ~1072-1075 post-W32 F1。No existing test regression。

### G4 ruff PASS + mypy strict module-path quirk preserved

新 touch files clean;pre-existing 11 W26 baseline errors per CO_W25_mypy_strict_debt unchanged。

### G5 NEW unit tests PASS

F1.5.a + F1.5.b all PASS。

### G6 Q4 measurement-experiment-fail-policy

Per ADR-0037 Q4 + W26+W27+W30+W31 precedent:G1 fully FAIL → revert per Karpathy §1.3 surgical(don't accumulate complexity for unproven side-effects);G1 partial PASS → preserve infrastructure。Settings `enable_citation_post_hoc_expansion` default treatment per F3 outcome:
- G1 strict + relaxed PASS → default ON ship(production candidate)
- G1 partial PASS → default OFF preserve infrastructure(measurement-experiment retained)
- G1 fully FAIL → REMOVE module(revert)

---

## §4 R1-R6 Sprint Rules(per CLAUDE.md §10 binding)

- **R1** plan.md committed before F1 code(F0.6 commit kickoff this session)
- **R2** daily commits correspond to progress.md Day-N entries(D1 F1 implementation commit + D2 F2 evidence + F3 closeout commit)
- **R3** plan deviation logged in §7 changelog(no silent drift)
- **R4** OQ resolved → decision-form.md + progress.md Day-N sync(none expected this phase — pure C05 backend module iteration)
- **R5** ADR if architectural decision(per H1)— F1.2 citation_expansion async module = parallel pattern to W25 F5 D1 `attach_neighbour_images`,non-architectural per §1 scope decl
- **R6** Day 0 recursive grep verify(this session F0.2 ✅ — post-W31-revert clean state confirmed,no shipped-pattern conflict)

---

## §5 D0-D1-D2 Day Breakdown Estimate

| Day | Deliverables | Effort | Verify |
|---|---|---|---|
| **D0(this session 2026-05-26)** | F0.1-F0.7 kickoff | ~1-2h | plan/checklist/progress committed + R6 verify |
| **D1** | F1.1 wire(~1h)+ F1.2 async module(~3-4h)+ F1.3 Settings(~20min)+ F1.4 caller wire(~1h)+ F1.5 tests(~2-3h)= ~7-9h | full D1 | backend pytest ~1072-1075 + ruff + mypy clean |
| **D2** | F2 5-run reproducibility(~1h backend reload + 10 curl runs + aggregate)+ F3 phase Gate(~30min)+ F3 closeout(~1-2h)= ~3-5h | full D2 | G1-G6 verdict + commit + push |

**Total**:~11-16h actual work spread across 2-3 calendar days。Real-calendar collapse pattern continues W22-W31(typical 3-5× collapse,W32 likely 3-4× given single-axis simpler scope)。

---

## §6 W31 Carry-overs + Dependencies

### Preserved baseline(W30+W31 inheritance)

- **W29 `.env` env override**:`QUERY_EXPANSION_PER_VARIANT_OVERFETCH=8` + `QUERY_EXPANSION_RRF_K=30`(retrieval-side +40pp Path A tune,W30+W31+ baseline,W32 inherits)
- **W28 `Settings.py` defaults**:`parent_doc_max_tokens_per_parent=2000` + `parent_doc_top_k=2` + `parent_doc_dispatch_mode="replace"`(W28 best combo,W32 inherits)
- **W26 `Settings.py` Q4**:`enable_parent_doc_retrieval=False`(measurement-experiment-fail-policy preserved,W32 NOT toggle)
- **W30+W31 reverts**:Rule 7 + Rule 8 + W31 citation_expansion module + 4 W31 Settings knobs ALL REMOVED(clean post-revert state per W31 F4)
- **W25 F5 D1 baseline**:`enable_citation_neighbour_images=True` + `citation_neighbour_window=3` + `citation_neighbour_max_aux_images=2`(image attach unchanged;W32 adds parallel async chunk-level expansion via `engine.list_chunks`)

### Dependencies on prior infrastructure

- **W25 F5 D1 reference pattern**:`backend/generation/citation_image_neighbors.py` `attach_neighbour_images` async function — DIRECTLY parallel structure(group by doc + parallel asyncio.gather list_chunks + per-doc neighbour-find pure helper + dedup + max_aux cap)
- **RetrievalEngine.list_chunks API**:`backend/retrieval/retrieval_engine.py:258` `list_chunks(kb_id, doc_id, top=1000)` — already wired,no API change
- **HybridSearcher.list_chunks API**:underlying impl returns `list[dict]` with chunk_index + chunk_title fields per Azure Search index schema

### W31 lessons applied as preventive controls

- **PC-W31-1**:LIVE eval on actual corpus chunk_title BEFORE finalizing regex pattern → W32 uses validated `\b\d+\.\d+\b`(bare + §-prefix coverage)+ corpus-realistic test fixtures
- **PC-W31-2**:Settings default values calibrated against LIVE corpus → W32 DROPS score_threshold field(list_chunks no score)+ window=10 corpus-empirical(W31 F2 evidence §X.1-§X.5 idx 46-53)
- **PC-W31-3**:Window-based locality assumption empirically validated → W32 escapes top-K constraint via engine-fetch
- **Sequential ship strategy**:W32 ship (h') ONLY,no concurrent prompt change(W31 multi-axis trap lesson)
- **Multi-batch reproducibility methodology**:F2 5-run continues W31 F2 pattern + retains stochasticity-control awareness

### Out of W32 scope(W33+ candidates)

- **(g')** 20-run sample methodology for stochasticity control — preserve W33+ if W32 G1 borderline
- **(i')** reformulator deterministic temp=0 + fixed seed — preserve W33+ orthogonal stochasticity control
- **Rule 7 v2 + Rule 8 prompt restoration** — preserve W33+ if W32 G1 marginal AND signal attribution to (h') confirmed
- **(B'.a)** Settings parameter chunk-score threshold pre-pend — preserve W34+
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
| 2026-05-26 | initial | Plan drafted F0 D0 kickoff | W31 retro carry-over (h') HIGHEST candidate per user explicit pick 2026-05-26;single-axis ship per W31 multi-axis trap lesson |
| 2026-05-26 | §1 | Single-axis ship (h') ONLY locked,no concurrent prompt change | W31 F4 fully FAIL evidence + Karpathy §1.2 一次只郁一個旋鈕 + sequential ship strategy |
| 2026-05-26 | §6 | W31 reverts confirmed,W25 F5 D1 reference pattern + RetrievalEngine.list_chunks API verified at kickoff | R6 Day 0 recursive grep verify against prompt_builder.py / synthesizer.py / Settings.py current state(W31 axes all REVERTED post commit `09805d6`)|
