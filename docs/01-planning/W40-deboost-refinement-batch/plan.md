---
phase: W40-deboost-refinement-batch
status: active   # 2026-05-27 kickoff — W39 closed_partial 2 個架構洞察 atomic batch ship
last_updated: 2026-05-27
component_scope: C04 Retrieval Engine(retrieval_engine.py post-rerank deboost loop refinement + Cohere overfetch trigger)
adr_refs:
  - W39 retro §W40+ HIGHEST NEW (1) Anchor-prefix length-mismatch fix(architectural insight 2 surfaced via Path A LIVE evidence — §8 anchor over-deboosting §8.x zoom-ins)
  - W39 retro §W40+ HIGHEST NEW (2) Cohere overfetch fix(architectural insight 1 surfaced via Path B LIVE evidence — deboost scope-limited to reranker top-K only;唔 pull-in same-section from positions 6-50)
  - W38 commit cea024f — F2 reranker post-rerank deboost infrastructure ship(W40 refinement target)
  - ADR-0035 W25 F5 D2 — symmetric deboost pattern reference(W38+W40 algorithm root)
  - W26 PC1 「一次只郁一個旋鈕」— W40 兩個 fix sequential ship 而非 simultaneous;F1 anchor-prefix 先(less invasive),F2 overfetch 後(adds new Setting + multi-line change)
related_carry_overs:
  - W37 F1 `_find_neighbour_chunks` section_path filter infrastructure preserved enabler
  - W38 F2 reranker deboost infrastructure(W40 直接 refinement target)
  - W39 F2 QueryRequest.mode + fused_retrieve mode propagation permanent enhancement(W40 F3 LIVE 可重用 Free tier workaround)
---

# W40 — Deboost Refinement Batch(Anchor-Prefix Fix + Cohere Overfetch)

## §1 目標 + 範疇

**雙目標 atomic batch ship**(per W36 precedent — 純 algorithmic refinement,non-architectural per H1,兩個 fix 都係 W39 F1+F2 evidence-driven 直接落實架構洞察)。**Sequential ship strategy**:F1 先(simpler,~30min)+ F2 後(more invasive,~1h)— 對齊 W26 PC1「一次只郁一個旋鈕」+ W31 sequential ship strategy validated。

**Karpathy §1.3 surgical scope 嚴守**:
- F1 — `retrieval_engine.py:172-176` anchor_prefix computation 加 `effective_depth = min(depth, len(anchor_sp))` 一行邏輯;NO Settings change(deboost 仍 needs explicit `< 1.0` to activate);bug 喺 default disabled state hidden,W40 F1 唔改 production behavior
- F2 — NEW Settings knob `reranker_overfetch_multiplier: int = 1`(default 1 disabled preserve W38 baseline)+ `retrieval_engine.py:160-200` rerank `top_k * multiplier` + post-deboost truncate `[:top_k]`;`server.py:160-163` wire new setting
- NO synthesizer prompt change(W33 Rule 7 v2 + Rule 8 baseline preserve)
- NO citation_expansion change(W32 (h') + W37 F1 infrastructure preserve)
- NO LLM cost knobs(per memory `feedback_judge_llm_cost_policy.md`)

**Non-goals**(W40 範疇外):
- LIVE Azure billing resolved hybrid mode re-verify(separate W41+ candidate;dependent on IT-side billing event)
- `\b\d+\.\d+\b` regex relax for `_find_neighbour_chunks`(MEDIUM preserved W41+)
- Ghost-Python-3.12 restart investigate(LOW preserved W41+)
- Q14 SME-validate `reference_answer` cascade — LONG-TERM
- 永久 OUT path (a) judge LLM 升級

**Component 範疇**:
- **C04 Retrieval Engine**(`retrieval_engine.py` deboost loop refinement + overfetch trigger;`server.py` setting wire)
- NO C05 / C07 / C08 / C12 touch(scope clean per Karpathy §1.3)

**Real-calendar estimate**:F1 ~30min + F2 ~1h + F3 ~30-45min(optional)+ F4 ~30min = **~2.5-3h total**(包 plan/checklist/progress + commit cascade)。

---

## §2 範疇 + Non-goals(雙目標執行)

### F1 Anchor-prefix length-mismatch fix(W39 F1 architectural insight 2)

**Bug 性質**:`retrieval_engine.py:172-176` anchor_prefix computation `list(anchor_sp[:depth])` 喺 `len(anchor_sp) < depth` case 下 silently truncates,然後 cand_prefix `list(cand_sp_raw[:depth])` 可以 longer。Comparison `cand_prefix != anchor_prefix` 必然 False positive(length 唔同 = 必然 not equal)。

**實際 W39 F1 evidence**:
- Corpus section_path 真實 shape:`['8. Integration scenarios (end-to-end walkthroughs)']` length 1(chapter intro chunk)+ `['8. Integration scenarios...', '8.1 Scenario A...']` length 2(scenario sub-section)
- depth=2,anchor 係 chapter intro chunk(length 1):anchor_prefix `[:2]` = full list length 1 = `['8. Integration scenarios...']`
- Candidate 係 §8.1 sub-section(length 2):cand_prefix `[:2]` = full list length 2 = `['8. Integration scenarios...', '8.1 Scenario A...']`
- `cand_prefix != anchor_prefix` → True → **DEBOOSTED(錯)** — §8.1 valid zoom-in of §8 anchor 被 over-deboost

**Existing test gap**:`test_w38_reranker_deboost_same_section_hierarchical_zoom_preserved` 用 anchor `['Doc', '§8']` length 2 + depth=2 → 真實 corpus 唔 reproduce 此 bug(W38 F2 test 假設 anchor 永遠 ≥ depth 長度,但 corpus 唔保證)。W40 F1 NEW test corner case anchor length < depth。

**Fix design**:
```python
effective_depth = min(depth, len(anchor_sp))
anchor_prefix = list(anchor_sp[:effective_depth])
# loop:
cand_prefix = list(cand_sp_raw[:effective_depth])  # 同樣用 effective_depth
```

Edge case:`effective_depth = 0`(anchor_sp 完全空)→ anchor_prefix = [] + 所有 cand_prefix = [] = anchor_prefix → no deboost(defensive,合理)。

### F2 Cohere overfetch fix(W39 F1 architectural insight 1)

**Bug 性質**:`retrieval_engine.py:160-162` `reranker.rerank(query, candidates=hits, top_k=top_k)` 返 fixed top-K 但 deboost loop 只能 work on already-returned candidates。Reranker top-K=5 case 下 same-section candidates from positions 6-50 fixed-dropped before deboost gets chance to swap。Per Cohere v4.0-pro API `top_n=min(top_k, len(candidates))` — 可以 safely overfetch up to `len(candidates)=fetch_k=50`。

**實際 W39 F1 evidence**:
- Path B mode=vector 10/10 runs `deboost_count=4 of 5 total_candidates`(symmetric deboost mechanism VERIFIED firing)
- 但 G1b real_drift improvement scope-limited — 真正 same-section walkthroughs(positions 6-50)從未 surfaced
- Run 1 Path A vector mode best case 6 cits across §8.1/§8.3/§8.4/§8.5 + §7.9 — 5 §8.x same-section 全 already in top-5(reranker quality);其他 4 runs 只 3 cits(§7.9 cross-section + §8.1 + §8 chapter intro)— overfetch+deboost 應可 pull-in §8.4+§8.5+其他 §8.x scenarios

**Fix design**:
1. NEW `Settings.reranker_overfetch_multiplier: int = 1`(default disabled preserve W38 baseline)
2. `retrieval_engine.py:160-162` — when `deboost < 1.0 AND multiplier > 1`,pass `top_k * multiplier` to `reranker.rerank()`
3. `retrieval_engine.py:198-211` — post-deboost loop end,truncate `chunks = chunks[:top_k]` to original top_k(invariant preserve — caller 仍 expect top_k items)
4. `server.py:160-163` — wire `reranker_overfetch_multiplier=settings.reranker_overfetch_multiplier`

**Edge case**:`multiplier=1`(default)→ `top_k * 1 = top_k` → exact W38 baseline behavior(NO regression risk per Karpathy §1.3 surgical)。`multiplier > 1 + deboost = 1.0` disabled → top_k * multiplier reranked 然後 truncate to top_k — 等價 over-fetching 然後 drop tail,**slight latency cost** 但 result 唔變(Cohere 同 reranker quality preserve,只係 多 fetch 再 drop)。Production 建議 multiplier=4 + deboost=0.85 combo(W41+ ramp candidate)。

---

## §3 Acceptance Criteria(6 hard gates per Q4 measurement-experiment-fail-policy)

| Gate | Criteria | Source |
|---|---|---|
| **G1 — F1 unit test 通過** | NEW test `test_w40_f1_anchor_shorter_than_depth_hierarchical_zoom_preserved` — anchor `['§8']` length 1 + cand `['§8','§8.6']` length 2 + depth=2 → cand preserved(score 不變)| W40 F1.2 |
| **G2 — F2 unit test 通過** | NEW tests `test_w40_f2_overfetch_multiplier_default_no_op` + `test_w40_f2_overfetch_multiplier_with_deboost_swap_in_same_section` + `test_w40_f2_overfetch_truncate_to_top_k_invariant` 全 PASS | W40 F2.5 |
| **G3 — LIVE 5+5 evidence**(F3 optional)| Free tier workaround W39 Path A pattern;.env temporary enable deboost=0.85 + overfetch=4;5+5 I07+I01;**G3a** F1 effect:I07 runs cross-section drift 進一步降至 ≤ W39 F2 PATH A 1.0;**G3b** F2 effect:I07 runs cit count 提升 vs W39 F2 PATH A baseline 3.6(target ≥ 4.5 marginal,≥ 4.8 W35 baseline = full recovery)— **Free tier 仍 mode=vector conflate caveat preserved**(true hybrid effect 仍 W41+ billing-resolved scope)| W40 F3 |
| **G4 — pytest 全 PASS** | backend pytest 1096 → 1097(F1)→ 1100(F2)+ ruff PASS + mypy strict W40 specific edits self-clean | W40 F1.3 + F2.6 |
| **G5 — R6 Day 0 catches verified** | F0 surface(已 ship below)+ implementation 過程 surface 嘅 new R6 catches 記 progress.md | W40 F0 + F1+F2 |
| **G6 — production preserve safety** | F1 deboost default 1.0 disabled → fix dormant until activate(0 regression risk);F2 multiplier default 1 → exact W38 baseline behavior(NO change in production unless user explicit `.env` flip)| W40 default Settings |

**3 outcome decision matrix**:
- (a) G1+G2+G4+G5+G6 PASS + G3 SKIP / PARTIAL → **Phase Gate PASS** F4 closeout,production preserve default disabled,F1+F2 infrastructure as W41+ enabler
- (b) G1+G2+G4+G5+G6 PASS + G3 LIVE PASS(both G3a + G3b)→ **Phase Gate STRONG PASS** F4 closeout,consider W41+ production default flip ADR
- (c) G1 OR G2 FAIL → STOP and revisit design per Karpathy §1.1

---

## §4 R6 Day 0 Recursive Verification(per CLAUDE.md §10 R6 W22 D9 amendment)

**R6 catch (1)** — `retrieval_engine.py:172-176` deboost loop 結構已 verify(Read tool L172-198);`anchor_prefix` line 176 確定 silent truncate 無 length check;fix 加一行 `effective_depth = min(depth, len(anchor_sp))` 即可

**R6 catch (2)** — `retrieval_engine.py:160-162` reranker.rerank() call site `top_k=top_k` 確定 fixed-pass(無 multiplier wrapper);F2 fix 加 multiplier wrap;`reranker/cohere.py:84-100` API contract `top_n=min(top_k, len(candidates))` 確定 safe upper bound 為 fetch_k=50

**R6 catch (3)** — Existing `test_w38_reranker_deboost_same_section_hierarchical_zoom_preserved`(test_retrieval.py L462-488)用 anchor `['Doc', '§8']` length 2 → **NOT 對應實際 corpus shape**(corpus 唔有 leading "Doc")— W40 F1.2 NEW test 必須用 length-1 anchor reproduce W39 evidence bug 模式

**R6 catch (4)** — `Settings.py:270-303` 現有 `citation_expansion_section_path_prefix_depth`(W37 F1)+ `reranker_section_path_prefix_depth`(W38 F2)— W40 F2 NEW field 命名 `reranker_overfetch_multiplier`(避免 confusion 同 `hybrid_overfetch_for_rerank` engine-init param;前者 multiplier on reranker output,後者 hybrid search overfetch absolute count);comment block 詳細解 distinction

**R6 catch (5)** — `server.py:156-163` RetrievalEngine init 已 wire `reranker_cross_section_deboost` + `reranker_section_path_prefix_depth`(W38 commit cea024f)— W40 F2 加 `reranker_overfetch_multiplier=settings.reranker_overfetch_multiplier` 一行 wire(無 breaking change)

**R6 catch (6)** — W39 F2 `.env` REVERTED 2026-05-27(production preserve);W40 F3 LIVE 若 trigger 需重新 enable(per W37/W38/W39 precedent),F4 closeout 必須再 REVERT(production preserve invariant per W27/W29 precedent + Q4 measurement-experiment-fail-policy)

---

## §5 範疇歸屬 + 違反風險

**C04 Retrieval Engine** — F1 + F2 implementation 全在 `retrieval_engine.py` deboost loop + Settings wire,無跨 component。

H1-H7 verify:
- **H1**:Non-architectural per H1 — post-rerank client-side score multiply algorithm refinement,no vendor swap / no storage layout change / no multi-KB invariant change(對齊 W38 commit cea024f 同 H1 verdict)
- **H2**:Cohere v4.0-pro vendor 不變,Cohere API contract `top_n` param 已 support,NO new dependency
- **H3**:N/A — 不涉 Dify reference
- **H4**:不涉 Tier 2(無 multi-tenancy / GraphRAG / multi-agent)
- **H5**:不涉 PII / secret(deboost factor + multiplier 純算法 knob)
- **H6**:F1 + F2 unit test pytest 寫(C04 critical module per CLAUDE.md §5.6)
- **H7**:N/A — pure backend,無前端 mockup 對應

**ADR-route 觸發條件**(per CLAUDE.md §6):無 — F1 + F2 非 architectural change,延續 W38 commit cea024f H1 verdict(post-rerank algorithm refinement 屬 Tier 1 normal evolution per ADR-0035 W25 D2 reference)。

---

## §6 改動清單(7 deliverables)

### F0 啟動(本 doc)
- [x] D0.1 `docs/01-planning/W40-deboost-refinement-batch/` folder
- [x] D0.2 `plan.md`(本文件)
- [x] D0.3 `checklist.md`
- [x] D0.4 `progress.md` Day 0
- [ ] D0.5 F0 commit:`docs(planning): kickoff W40-deboost-refinement-batch + R6 Day 0 6 catches surface F1 anchor-prefix length-mismatch fix (insight 2) + F2 Cohere overfetch fix (insight 1) atomic batch`
- [ ] D0.6 session-start.md §10 W40 row append active 2026-05-27 + W40+ → W41+ placeholder rename

### F1 Anchor-prefix length-mismatch fix(~30min)
- [ ] F1.1 `retrieval_engine.py:172-176` modify anchor_prefix computation — 加 `effective_depth = min(depth, len(anchor_sp))` + 用 effective_depth replace depth in cand_prefix slice
- [ ] F1.2 NEW unit test `test_w40_f1_anchor_shorter_than_depth_hierarchical_zoom_preserved` — anchor `['§8']` length 1 + cand `['§8','§8.6']` + depth=2 → cand preserved
- [ ] F1.3 NEW unit test `test_w40_f1_anchor_empty_section_path_no_deboost_defensive` — anchor `[]` empty + cand any → no deboost(defensive)
- [ ] F1.4 pytest 1096 → 1098 PASS + ruff PASS + mypy strict W40 specific edits self-clean
- [ ] F1.5 commit:`fix(retrieval): W40 F1 anchor-prefix length-mismatch — effective_depth = min(depth, len(anchor_sp)) preserve hierarchical zoom-in when anchor shorter than depth + 2 NEW unit tests`

### F2 Cohere overfetch fix(~1h)
- [ ] F2.1 `storage/settings.py` NEW field `reranker_overfetch_multiplier: int = 1` + comment block(distinction vs `hybrid_overfetch_for_rerank` + default disabled preserve W38 baseline + W41+ ramp guidance)
- [ ] F2.2 `retrieval_engine.py:__init__` add `reranker_overfetch_multiplier: int = 1` param + store `self._reranker_overfetch_multiplier`
- [ ] F2.3 `retrieval_engine.py:160-162` modify `reranker.rerank(top_k=...)` — when `deboost < 1.0 AND multiplier > 1` pass `top_k * multiplier`,else pass `top_k`(default behavior preserve)
- [ ] F2.4 `retrieval_engine.py:198-211` post-deboost truncate — `chunks = chunks[:top_k]` 確保 final result top_k items invariant preserve(對應 RetrievalResult contract)
- [ ] F2.5 `server.py:156-163` RetrievalEngine init wire `reranker_overfetch_multiplier=settings.reranker_overfetch_multiplier`
- [ ] F2.6 NEW unit test `test_w40_f2_overfetch_multiplier_default_no_op` — multiplier=1 → reranker.rerank called with top_k unchanged
- [ ] F2.7 NEW unit test `test_w40_f2_overfetch_multiplier_with_deboost_swap_in_same_section` — multiplier=4 + deboost=0.85 + anchor §8 + 5 cross-section candidates positions 1-5 + 3 same-section candidates positions 6-8(simulating Cohere overfetch return)→ post-deboost top-5 includes ≥ 1 same-section from positions 6-8
- [ ] F2.8 NEW unit test `test_w40_f2_overfetch_truncate_to_top_k_invariant` — multiplier=4 + reranker returns 20 → final chunks count = top_k(non-multiplier)
- [ ] F2.9 pytest 1098 → 1101 PASS + ruff PASS + mypy strict W40 specific edits self-clean
- [ ] F2.10 commit:`feat(retrieval): W40 F2 Cohere overfetch + truncate — reranker_overfetch_multiplier Settings knob + rerank with top_k * multiplier when deboost active + post-deboost truncate to top_k invariant + 3 NEW unit tests`

### F3 LIVE verify(optional,~30-45min)
- [ ] F3.1 Pre-flight per CLAUDE.md §10.3 step 5b — Langfuse `/api/public/health` 200 + Postgres `SELECT 1`
- [ ] F3.2 `.env` temporary marker block W40 F3 TEMPORARY — `RERANKER_CROSS_SECTION_DEBOOST=0.85` + `RERANKER_SECTION_PATH_PREFIX_DEPTH=2` + `RERANKER_OVERFETCH_MULTIPLIER=4`
- [ ] F3.3 Backend restart per W39 pattern(kill api.server PID via WMI + bash & background spawn recovery)
- [ ] F3.4 Direct curl `/health` 200 + sanity `/query` mode=vector → HTTP 200 valid response
- [ ] F3.5 LIVE runner `backend/w40-f3-runner.py` POST /query with `{"mode": "vector"}` body + 5 runs Q-W25-I07 + 5 runs Q-W25-I01 control
- [ ] F3.6 Aggregate citation metrics + drift count + log inspection `reranker_cross_section_deboost_applied` event firing
- [ ] F3.7 Decision tree intersect per §3 G3a/G3b

### F4 closeout(~30min)
- [ ] F4.1 Cross-cutting tick — checklist.md + progress.md retro + plan.md frontmatter status flip → closed / closed_partial / closed_strong
- [ ] F4.2 session-start.md §10 W40 row flip `active → closed`
- [ ] F4.3 `.env` revert W40 F3 marker block(per W37/W38/W39 precedent — production preserve default disabled)
- [ ] F4.4 F4 closeout commit + push origin/main

---

## §7 Changelog

| Date | Change | Trigger |
|---|---|---|
| 2026-05-27 | Plan v1.0 ship — F0 kickoff via Chris W40+ candidates (1)+(2) atomic batch pick | W39 closed_partial 2026-05-27 + Chris explicit immediate-ship pick(per `/compact` resume final user msg) |
