---
phase: W31-synthesizer-cite-multi-axis
status: active
last_updated: 2026-05-26
---

# Phase W31 — Progress Journal

> Daily entry style:每日 work session 結束(或單一日 multi-segment trajectory close)時寫一段。Retro section 喺 phase 收尾寫。

---

## Day 0 — 2026-05-26 (kickoff)

### F0 Kickoff actions

1. **Trigger**:W30-synthesizer-prefer-specific closed_partial(commit `e192464`)— Phase Gate PARTIAL per Q4 measurement-experiment-fail-policy(G1 strict 0/5 + G1 relaxed 1/5 + G1 marginal 0pp改善 vs W29 baseline 20% = G1 fully FAIL);Rule 7 REVERTED per Karpathy §1.3 surgical(commit `e192464`)。W30 retro `priority_queue_locked` 將 (B') HIGHEST NEW path (i) Option B「cite-confidence threshold relax」3 mechanism sub-options + Rule 7 v2 wording refinement elevated。

2. **User candidate pick**(2026-05-26 same-day as W30 closeout):候選 3 — **(B') + Rule 7 v2 combined ship**(~2-3 days + 1-2h estimate;Multi-axis ship 增加 G1 marginal improvement 概率;兩個都係 prompt/Settings 層 surgical change(non-architectural,non-H1))。

3. **AskUserQuestion (B') subset clarification 2026-05-26**:User pick **B'.b + B'.c + Rule 7 v2 (full prompt + post-hoc multi-axis)** —— Prompt layer(B'.b 「cite ALL chunks overlap with answer paragraph keywords」 + Rule 7 v2 wording target「§X.M numbering pattern」)+ Backend layer(B'.c post-hoc citation expansion ±N neighbor walkthrough chunks if score ≥ threshold)兩 layer 同 ship;estimate ~2-3 days total;**最大 G1 marginal improvement 概率但違 Karpathy §1.2 一次只郁一個旋鈕 風險 高,debug 難度提升因兩 layer 同時 ship**(user explicit accept multi-axis risk trade-off for max G1 improvement probability)。

### R6 Day 0 recursive grep verify(per CLAUDE.md §10 R6)

3 個關鍵發現:

1. **✅ 無 (B') 已 ship pattern**(避開 W29+W30 R6 Day 0 catch pattern):
   - `backend/storage/settings.py` L163-172 已有 `enable_citation_neighbour_images: bool = True` + `citation_neighbour_window: int = 3` + `citation_neighbour_max_aux_images: int = 2`(W25 F5 D1 — citation neighbour-**images**)— **attach images** 唔係 **expand citation chunks**;B'.c 模式可借鑒 pattern 但需 NEW module 唔同 file
   - `backend/generation/prompt_builder.py:20-28` SYSTEM_PROMPT 只有 Rule 1-6 present(W30 Rule 7 REVERTED per commit `e192464` 2026-05-26)— Rule 7 v2 + Rule 8(B'.b)可同一 SYSTEM_PROMPT edit ship
   - `backend/generation/synthesizer.py` `synthesize`(L120-169)+ `synthesize_stream`(L171-258)— both call `build_prompt(query, chunks, dispatch_mode=get_settings().parent_doc_dispatch_mode)` 之後 `extract_citation_ids` + `refused` detection,**NO** existing post-hoc citation expansion logic between extract_citation_ids 同 return SynthesisResult
   - `backend/generation/citation_image_neighbors.py`(W25 F5 D1 existing)— 已有 `attach_neighbour_images` chunk_index ±3 window + checksum dedup pattern;**可做 B'.c reference pattern**(parallel signature `expand_citations` for citation chunks output type)

2. **Working tree state**:
   - Untracked:6 個 W26-W30 eval artifact JSON + 4 個 uvicorn log.err + `docs/09-analysis/`(未確認內容)+ W29 standalone Python script — preserved untracked(W31 will retain pattern)
   - Last commits trace:`e192464` W30 closeout → `0b36ecf` W30 kickoff → `8e8df12` W29 closeout → `7b6082e` W29 F1+F2 diagnose
   - 0 ahead origin/main(pre-W31 kickoff baseline clean)

3. **Plan-text contamination check**(per W22 D9 R6 recursive scope):
   - W31 plan §1 scope 引用 `prompt_builder.py:28` — verified at L28 SYSTEM_PROMPT current text
   - W31 plan §6 cites W29 `.env` env override `QUERY_EXPANSION_PER_VARIANT_OVERFETCH=8 + QUERY_EXPANSION_RRF_K=30` + W28 Settings defaults `parent_doc_max_tokens_per_parent=2000 + parent_doc_top_k=2 + parent_doc_dispatch_mode="replace"` + W26 Q4 `enable_parent_doc_retrieval=False` — verified against `Settings.py` L198-243 current state
   - W31 plan §1 axis 3 cites `citation_image_neighbors.py` as parallel pattern — verified W25 F5 D1 already-ship at this path

**Net W22 D9 plan-text contamination = 0**(R6 recursive scope per CLAUDE.md §10 R6 confirmed)。

### Karpathy §1.1 think-before-coding upfront — multi-axis risk acknowledgement

**Risk preserved 入 plan §1 + §3 G6 + §6**:

- **Risk 1 — Multi-axis attribution ambiguity**:Prompt layer(B'.b + Rule 7 v2)同 backend layer(B'.c)同 ship,若 G1 marginal PASS 無法清楚 attribute「邊個 axis dominant」。Mitigation:plan §3 G1 decision matrix 分 strict / relaxed / marginal 3 tier verdict,F4 closeout 可 retroactively check 5-run individual citation pattern 推斷 axis source(e.g. 若 5-run citations 全部新增 §X.M numbered chunks 但 keyword overlap 唔強 → 主要 B'.c contribution;若 citations 多 但分布廣 keyword overlap 強 → B'.b contribution dominant)
- **Risk 2 — Over-citation noise**:B'.c post-hoc expansion 可能 introduce spurious citations 損 G2 control Q-W25-I01 faithfulness。Mitigation:plan §3 G2 decision priority FAIL → revert B'.c first(prompt layer 通常 lower risk);`citation_expansion_score_threshold=0.5` empirical baseline,F4 可 tune 0.6 / 0.7 若 G2 marginal
- **Risk 3 — Debug 難度提升**:multi-axis ship,若 F2 5-run unexpected 結果(e.g. Run 1 PASS / Run 2-5 FAIL),isolation 困難。Mitigation:plan §3 G6 + §6 W32+ candidates 預備 axis tune options;F4 closeout 必要時 selective revert(e.g. preserve Rule 7 v2 + revert B'.c,或反之),唔需要 全 revert
- **Risk 4 — Karpathy §1.2 一次只郁一個旋鈕 違反**:user explicit accept,plan §1 + §3 G6 + §7 changelog 已 document trade-off rationale(W29+W30 single-axis PARTIAL trajectory empirical evidence 表明 single-axis attempt empirical risk 高 — multi-axis ship justified per user goal-driven decision)

### F0 next steps

- **F0.5** Draft this progress.md Day 0 entry(this section)— ✅ done
- **F0.6** Commit kickoff `3a838b5` — `docs(planning): kickoff W31-synthesizer-cite-multi-axis + R6 Day 0 no-shipped-pattern confirm + (B'.b + B'.c + Rule 7 v2) multi-axis subset pick` ✅
- **F0.7** session-start.md §10 W31 row append + W32+ rolling JIT row defer + W30 row 維持 closed_partial(active now)
- **D1** start:F1 implementation cascade(prompt + module + Settings + wire + tests)

### Day 0 Actual vs Planned Effort table

| Deliverable | Planned | Actual | Variance |
|---|---|---|---|
| F0.1 folder create | 5min | ~2min | -3min (Write tool fast) |
| F0.2 R6 grep verify | 15-30min | ~10min(3 parallel Read + git status)| -10min ✅ |
| F0.3 plan.md draft | 45-60min | ~20min | -25-40min(Write tool one-shot vs incremental edit)|
| F0.4 checklist.md draft | 20-30min | ~10min | -10-20min ✅ |
| F0.5 progress.md Day 0 | 20-30min | ~15min | -5-15min ✅ |
| F0.6 commit kickoff `3a838b5` | 5min | ~3min | -2min ✅ |
| F0.7 session-start.md sync commit `7178133` | 10min | ~5min | -5min ✅ |

**Cumulative F0 actual**:~1h 全部 F0 done;同 W30 F0 ~1.2h pattern parallel,~15% efficiency 提升 due to 4th-iteration template re-use(W27 → W28 → W29 → W30 → W31 5-phase compounding)。

---

## Day 1 — 2026-05-26 (F1 implementation cascade — same-day post-F0)

### F1 cascade summary

**Trajectory**:F1.3 Settings → F1.1 prompt → F1.2 module + tests → F1.4 wire → F1.5 tests + non-regression → F1.6 commit。Karpathy §1.3 surgical change sequence:dependencies-first(Settings 喺 module 引用之前)+ smallest unit first(prompt edit 喺 module 之前 verify SYSTEM_PROMPT current state),avoiding compound-bug pre-test risk。

### F1.1 prompt edit(`backend/generation/prompt_builder.py:28-31`)

**Rule 7 v2**(replaces W30 abstract「specific subsection」wording):
```
7. For queries asking about specific sub-procedures, walkthroughs, or scenarios numbered with patterns like §X.M (e.g. §8.1, §8.2, §8.3, Scenario A walkthrough, Step 3.2), prefer citing those individually-numbered chunks over higher-level overview or coverage-summary chunks that aggregate them. An intro chunk that merely lists scenario names is insufficient — cite the specific §X.M chunks that describe each scenario's actual procedure.
```

**Rule 8 NEW B'.b prompt instruction**:
```
8. When multiple retrieved chunks each contain partial information relevant to the answer, cite ALL of them (not just the most representative one) — each fact in the answer should be backed by every chunk that supports it. If two chunks describe the same scenario from different angles, both warrant a citation marker.
```

Rule 6 CH-005 preserved unchanged。

### F1.2 NEW citation_expansion.py module(167 lines)

Pure function `expand_citations(answer_text, citation_ids, chunks, *, settings) → (expanded_text, expanded_citation_ids)`:

**Algorithm**:
1. For each existing `[chunk-{id}]` marker in answer_text:
   - Look up cited chunk in `chunks`(top-K reranked set,already retrieved — surgical scope per Karpathy §1.2,no async engine fetch)
   - Find ±window chunk_index neighbors in same doc within `chunks` list
   - Filter:NOT already cited + rerank score ≥ threshold + title regex `§\\d+\\.\\d+`
   - Pick top `max_aux` by absolute chunk_index distance(closer neighbors preferred)
2. Group additions by `after_id`;build replacement string `[chunk-A][chunk-N1][chunk-N2]`
3. Apply single `str.replace(marker, new_marker, 1)` per `after_id`(first occurrence only)
4. Re-extract `citation_ids` from expanded text → ordered final list

**Defensive handling**:
- `enable_citation_post_hoc_expansion=False` → return inputs unchanged(backward compat per F1.4.c)
- Empty `citation_ids` OR empty `chunks` → return inputs unchanged
- Cited `chunk_id` not in `chunks` list(hallucinated)→ skip silently per Rule 5 contract
- Invalid `chunk_index` types → skip via try/except defensive cast
- Distance 0(same chunk_index)→ excluded(self + duplicate-index defensive)

### F1.3 Settings 4 NEW knobs(`backend/storage/settings.py:245-272`)

- `enable_citation_post_hoc_expansion: bool = True`(W31 measurement default ON per Karpathy §1.4)
- `citation_expansion_window: int = 3`(parallel W25 F5 D1)
- `citation_expansion_score_threshold: float = 0.5`(empirical Cohere v4.0-pro range)
- `citation_expansion_max_aux: int = 2`(parallel W25 F5 D1 cap)

### F1.4 synthesizer wire(`backend/generation/synthesizer.py`)

**Import**:`from generation.citation_expansion import expand_citations`(L30 addition)

**`synthesize` method**(L141-148):after `citation_ids = extract_citation_ids(answer_text)` + `refused = REFUSAL_PHRASE in answer_text`,if not refused → `answer_text, citation_ids = expand_citations(answer_text, citation_ids, chunks, settings=get_settings())`。Result `SynthesisResult.answer` + `.citation_ids` carry expanded values。

**`synthesize_stream` method**(L233-241):after stream complete + `accumulated = extract_citation_ids(...)` + `refused = REFUSAL_PHRASE in accumulated`,if not refused → expand applied to `accumulated`。Text-delta partial frames yielded before expansion(unchanged behavior);final `result` event payload carries expanded values per W31 F1.4.b plan §2 acceptance。

### F1.5 unit tests + non-regression coverage

**+20 NEW tests across 3 files**(W30 baseline 1060 → W31 F1 = **1080 passed + 25 skipped + 0 failed**;match plan §2 F1.5.d expected ~1070-1075 lower bound exceeded):

- `test_citation_expansion.py` **15 NEW**:happy path / disabled flag / empty inputs / §X.M filter / score threshold / window boundary / same doc constraint / dedupe / max_aux cap / closer-neighbor-preferred / cited-not-in-chunks defensive / multiple cited independent / self-at-distance-0 exclude / extract_citation_ids ordering / empty text
- `test_prompt_builder_dispatch.py` **+3 NEW**:Rule 7 v2「§X.M numbering」phrases + Rule 8「cite ALL of them」phrases + Rule 6 CH-005 non-regression
- `test_synthesizer.py` **+2 NEW**:expand_citations wire invoked when not refused / skipped when refused

### F1 verify gates state

| Gate | Verdict | Detail |
|---|---|---|
| **pytest tests/ -q** | ✅ PASS | 1080 passed + 25 skipped + 0 failed in 803.87s(W30 baseline 1060 → +20 NEW)|
| **ruff check touched files** | ✅ PASS | 2 errors auto-fixed via `--fix`(unused `pytest` import in test file + import organization)→ all checks passed |
| **mypy strict citation_expansion.py** | ✅ PASS | `Success: no issues found in 1 source file` per --follow-imports=silent isolated check;13 pre-existing errors in other modules per CO_W25_mypy_strict_debt unchanged(non-W31 baseline preserved per Karpathy §1.3 surgical)|
| **Backward compat** | ✅ PASS | `test_disabled_flag_returns_inputs_unchanged` confirms `enable_citation_post_hoc_expansion=False` short-circuit |

### F1 surprises + observations

1. **Karpathy §1.2 simplicity scoping win**:`expand_citations` pure function(no async,no engine fetch)operates only on top-K reranked chunks already in `chunks` list。W29 retrieval-side improvement(§8.x top-5 surface 40%)provides ground 畀 expansion candidate chunks;no need to escalate to W25 F5 D1-style async engine.list_chunks pattern。Reduce LOC + latency overhead + test complexity。

2. **§X.M regex pattern empirical choice**:Title pattern `§\\d+\\.\\d+` matches W25 corpus convention(`§8.1 Scenario A walkthrough`)but **不限於 §**(any pattern with format `§X.M` where X+M are digits)。若 Q-W31-I08 user-test 揭露 corpus uses different numbering convention(e.g. `Step 3.2` / `Scenario A`)而非 `§X.M`,W32+ candidate amend regex pattern。

3. **expand_citations runtime invocation policy**:Default ON `enable_citation_post_hoc_expansion=True` per Karpathy §1.4 goal-driven「make it pass」requires axis enabled to measure。Q4 measurement-experiment-fail-policy 仍 apply at F4 — 若 G1 fully FAIL → revert default to False per W30 Rule 7 precedent。

4. **Score threshold 0.5 empirical baseline**:Cohere v4.0-pro reranked scores empirically [0.5, 1.0] range per W26 F1 D1 evidence。0.5 = top half retain reasonable starting point;若 F2 5-run G2 control regression observed → tune 0.6 / 0.7 per F4 closeout decision matrix。

### Day 1 Actual vs Planned Effort table

| Deliverable | Planned | Actual | Variance |
|---|---|---|---|
| F1.1 prompt edit | 1-2h | ~10min | -50-110min ✅(template-reuse W30 pattern + smaller scope per surgical edit) |
| F1.2 module + 15 unit tests | 3-4h | ~40min | -2.5-3.5h ✅(W25 reference pattern + iteration on same algorithm)|
| F1.3 Settings 4 knobs | 30min | ~5min | -25min ✅ |
| F1.4 synthesizer wire(2 sites)| 1h | ~5min | -55min ✅ |
| F1.5 prompt + synthesizer tests extend | 1-2h | ~15min | -45-105min ✅ |
| F1.5.d full pytest run | 5min wait | 803s(~13.5min)| +8.5min(test suite scale dominant)|
| ruff + mypy verify | 5min | ~3min | -2min |
| **F1 implementation total** | **7-9h estimate** | **~80min hands-on + ~14min pytest wait** | **~6-7h under estimate** ✅(AI compression continues W22-W30 pattern;~5-6× collapse on F1 cascade vs plan-day estimate)|

**Cumulative D0+D1**:~1h(F0)+ ~80min(F1 implementation)+ ~14min(pytest)= ~3.2h actual elapsed for F0-F1 lifecycle vs planned ~10-14h;~3-4× AI compression continues。

### F1.6 + F1.7 next steps

- **F1.6**:commit `feat(generation): W31 F1 multi-axis prompt + post-hoc citation expansion ...` per R2 daily commit
- **F1.7**:this Day 1 entry done + commit hash backfill post-F1.6
- **D2 next**:F2 5-run reproducibility verify Q-W25-I07 + Q-W25-I01 control(背景需 backend uvicorn restart + WatchFiles reload)

