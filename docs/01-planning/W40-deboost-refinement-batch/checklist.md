---
phase: W40-deboost-refinement-batch
plan_ref: ./plan.md
status: active
last_updated: 2026-05-27
---

# W40 — Checklist

> 原子化勾選項。雙目標 sequential ship — F1 anchor-prefix length-mismatch fix(W39 insight 2)→ F2 Cohere overfetch fix(W39 insight 1)→ F3 LIVE verify(optional via Free tier workaround)→ F4 closeout。

## F0 — 啟動

- [x] F0.1 建立 `docs/01-planning/W40-deboost-refinement-batch/` folder
- [x] F0.2 R6 Day 0 6 catches — (1) `retrieval_engine.py:172-176` anchor_prefix silent truncate confirmed;(2) `retrieval_engine.py:160-162` reranker.rerank top_k fixed-pass confirmed;(3) existing test gap anchor=['Doc','§8'] length 2 mismatch corpus;(4) F2 Setting naming distinction `reranker_overfetch_multiplier` vs `hybrid_overfetch_for_rerank`;(5) `server.py:156-163` wire path verified;(6) `.env` REVERTED 2026-05-27 production preserve invariant
- [x] F0.3 起草 `plan.md` 7 段
- [x] F0.4 起草 `checklist.md`(本文件)
- [x] F0.5 起草 `progress.md` Day 0
- [ ] F0.6 啟動 commit `docs(planning): kickoff W40-deboost-refinement-batch + R6 Day 0 6 catches surface F1 anchor-prefix length-mismatch fix (insight 2) + F2 Cohere overfetch fix (insight 1) atomic batch`
- [ ] F0.7 session-start.md §10 W40 row append active 2026-05-27 + W40+ → W41+ placeholder rename(commit pending)

## F1 — Anchor-prefix length-mismatch fix(~30min)

### F1.1 Code change `retrieval_engine.py`

- [ ] F1.1.a 修改 line 176 `anchor_prefix = list(anchor_sp[:depth])` → 加 `effective_depth = min(depth, len(anchor_sp))` + `anchor_prefix = list(anchor_sp[:effective_depth])`
- [ ] F1.1.b 修改 line 185 cand_prefix slice 用 effective_depth replace depth
- [ ] F1.1.c 更新 observability log line 200-206 加 `effective_depth` field 對 anchor_prefix scope 顯式可追溯

### F1.2 NEW unit tests

- [ ] F1.2.a NEW test `test_w40_f1_anchor_shorter_than_depth_hierarchical_zoom_preserved`:anchor `['§8. Integration']` length 1 + cand_a `['§8. Integration','§8.1 Scenario A']` length 2 + cand_b `['§7. Other','§7.9 Docuware']` length 2 + depth=2 + deboost=0.85 → cand_a score preserved(zoom-in)+ cand_b deboosted(cross-section)
- [ ] F1.2.b NEW test `test_w40_f1_anchor_empty_section_path_no_deboost_defensive`:anchor `[]` + cand any section_path + depth=2 + deboost=0.85 → all candidates preserve(effective_depth=0,prefix=[] = []match all)

### F1.3 Verify

- [ ] F1.3.a backend pytest 1096 → **1098** PASS(`pytest backend/tests/test_retrieval.py -v -k w40_f1`)
- [ ] F1.3.b ruff PASS(W40 F1 specific edits — `retrieval_engine.py` + `test_retrieval.py`)
- [ ] F1.3.c mypy strict W40 F1 specific edits self-clean

### F1.4 Commit

- [ ] F1.4.a commit:`fix(retrieval): W40 F1 anchor-prefix length-mismatch — effective_depth = min(depth, len(anchor_sp)) preserve hierarchical zoom-in when anchor shorter than depth + 2 NEW unit tests`

## F2 — Cohere overfetch fix(~1h)

### F2.1 Settings NEW knob

- [ ] F2.1.a `storage/settings.py` 加 NEW field `reranker_overfetch_multiplier: int = 1` 位於 line 304 `reranker_section_path_prefix_depth` 之下(W38 block extension)
- [ ] F2.1.b Comment block 解 distinction:multiplier on reranker output(W40 NEW)vs `hybrid_overfetch_for_rerank=50` absolute hybrid pre-rerank fetch(W3 baseline)+ default 1 disabled preserve W38 baseline + W41+ ramp guidance(multiplier=4 + deboost=0.85 combo recommended once Azure billing resolved)

### F2.2 RetrievalEngine init param

- [ ] F2.2.a `retrieval_engine.py:__init__` add `reranker_overfetch_multiplier: int = 1` keyword param
- [ ] F2.2.b store `self._reranker_overfetch_multiplier = reranker_overfetch_multiplier`

### F2.3 Rerank call site refinement

- [ ] F2.3.a `retrieval_engine.py:160-162` modify `reranker.rerank(top_k=...)` — 加 `rerank_top_k = top_k * self._reranker_overfetch_multiplier if (self._reranker_cross_section_deboost < 1.0 and self._reranker_overfetch_multiplier > 1) else top_k` + pass `top_k=rerank_top_k`
- [ ] F2.3.b 注意 Cohere v4.0-pro `top_n=min(top_k, len(candidates))` 已 self-cap to fetch_k=50,無 overflow risk

### F2.4 Post-deboost truncate

- [ ] F2.4.a `retrieval_engine.py:198-211` 加 truncate — 喺 `chunks = [RetrievedChunk(...) for r in reranked_chunks]` 之後 加 `chunks = chunks[:top_k]` 確保 final result top_k items invariant
- [ ] F2.4.b 同時更新 `else` branch(no reranker case)line 214-217 維持 `hits[:top_k]` 不變
- [ ] F2.4.c 更新 observability log line 200-206 加 `rerank_top_k` field(顯示 actual reranker top_k vs original top_k)

### F2.5 Server.py wire

- [ ] F2.5.a `api/server.py:156-163` 加一行 `reranker_overfetch_multiplier=settings.reranker_overfetch_multiplier,`

### F2.6 NEW unit tests

- [ ] F2.6.a NEW test `test_w40_f2_overfetch_multiplier_default_no_op`:multiplier=1 + deboost=0.85 → reranker.rerank called with original top_k(spy)
- [ ] F2.6.b NEW test `test_w40_f2_overfetch_multiplier_disabled_with_deboost_disabled`:multiplier=4 + deboost=1.0(disabled)→ reranker.rerank called with original top_k(deboost gate inactive,multiplier dormant)
- [ ] F2.6.c NEW test `test_w40_f2_overfetch_multiplier_with_deboost_swap_in_same_section`:multiplier=4 + deboost=0.85 + anchor `['§8']` + 3 cross-section `['§11']`/`['§7']` candidates positions 2-4 + 2 same-section `['§8','§8.1']`/`['§8','§8.4']` candidates positions 5-6(simulating Cohere overfetch return)+ top_k=3 → post-deboost top-3 chunks include ≥ 1 same-section(swap-in evidence)
- [ ] F2.6.d NEW test `test_w40_f2_overfetch_truncate_to_top_k_invariant`:multiplier=4 + reranker returns 12 RerankedChunk + top_k=3 → final chunks count exactly 3(truncate invariant)

### F2.7 Verify

- [ ] F2.7.a backend pytest 1098 → **1102** PASS(4 NEW tests:F2.6.a-d)
- [ ] F2.7.b ruff PASS(W40 F2 specific edits)
- [ ] F2.7.c mypy strict W40 F2 specific edits self-clean

### F2.8 Commit

- [ ] F2.8.a commit:`feat(retrieval): W40 F2 Cohere overfetch + truncate — reranker_overfetch_multiplier Settings knob + rerank with top_k * multiplier when deboost active + post-deboost truncate to top_k invariant + 4 NEW unit tests`

## F3 — LIVE verify(optional,~30-45min via Free tier workaround per W39 Path A pattern)

### F3.1 Pre-flight per CLAUDE.md §10.3 step 5b

- [ ] F3.1.a Langfuse `/api/public/health` 200 OK
- [ ] F3.1.b Postgres `SELECT 1` ready_for_query

### F3.2 `.env` temporary override

- [ ] F3.2.a `.env` 加 marker block W40 F3 TEMPORARY
- [ ] F3.2.b `RERANKER_CROSS_SECTION_DEBOOST=0.85`
- [ ] F3.2.c `RERANKER_SECTION_PATH_PREFIX_DEPTH=2`
- [ ] F3.2.d `RERANKER_OVERFETCH_MULTIPLIER=4`

### F3.3 Backend restart per W39 pattern

- [ ] F3.3.a Kill api.server PID via WMI CommandLine filter
- [ ] F3.3.b Restart `python -m api.server` via bash & background spawn pattern
- [ ] F3.3.c `/health` 200 within ~25s warmup

### F3.4 Sanity check

- [ ] F3.4.a Direct curl `POST /query` with `{"mode":"vector"}` body → HTTP 200 valid citation answer
- [ ] F3.4.b Backend log inspect `reranker_cross_section_deboost_applied` event 確認 firing + `rerank_top_k` field 顯示 multiplier 生效

### F3.5 LIVE runner

- [ ] F3.5.a `backend/w40-f3-runner.py` ship — POST /query with `{"mode":"vector"}` body field + 5 runs Q-W25-I07 + 5 runs Q-W25-I01 control
- [ ] F3.5.b Aggregate citation metrics + drift count + log inspection

### F3.6 Decision tree intersect

- [ ] F3.6.a G3a(F1 effect)— I07 runs cross-section drift ≤ W39 F2 Path A 1.0 baseline?
- [ ] F3.6.b G3b(F2 effect)— I07 runs cit count ≥ 4.5 marginal(W39 F2 Path A 3.6 baseline)or ≥ 4.8 full W35 baseline recovery?
- [ ] F3.6.c G3 control — I01 non-regression refusals 0/5 + avg_cit ≥ 3.5(W35 baseline floor)

## F4 — 收尾 + 跨文件同步 + commit + push

### A. 跨文件同步

- [ ] A.1 plan.md frontmatter status `active → closed / closed_partial / closed_strong` 視 G3 outcome
- [ ] A.2 checklist.md cross-cutting tick(本文件)
- [ ] A.3 progress.md retro 7 段
- [ ] A.4 session-start.md §10 W40 row `🟡 active` → `✅ closed / closed_partial / closed_strong`
- [ ] A.5 `.env` 移除 W40 F3 marker block(per W37/W38/W39 precedent — production preserve default disabled)
- [ ] A.6 F1 + F2 production code preserved as W41+ enabler(對齊 W37 F1 + W38 F2 + W39 F2 production preserve pattern)
- [ ] A.7 RISK_REGISTER R-W38-1 status update(Azure billing IT-side still environmental block;W41+ hybrid mode billing-resolved re-verify deferred)
- [ ] A.8 ADR README — 無 NEW ADR(F1+F2 純 algorithmic refinement per H1 non-architectural)

### B. W41+ priority queue 評估

- [ ] B.1 W41+ HIGHEST preserved:Hybrid mode billing-resolved re-verify(isolate true W40 F1+F2 effect without mode=vector conflate — Azure billing IT-side gate)
- [ ] B.2 W41+ MEDIUM preserved:`\b\d+\.\d+\b` regex relax for `_find_neighbour_chunks`
- [ ] B.3 W41+ LOW preserved:Ghost-Python-3.12 restart investigate
- [ ] B.4 Long-term carry-over 維持
- [ ] B.5 永久 OUT path (a) judge LLM 升級 per memory

### C. commit + push

- [ ] C.1 F4 收尾 commit `docs(planning): W40 closeout — F1 anchor-prefix length-mismatch fix + F2 Cohere overfetch + truncate landed [outcome description]`
- [ ] C.2 push origin/main confirmed

---

## Cross-Cutting

- [ ] All deliverables committed to git(F4 closeout commit pending)
- [ ] All OQ status changes 反映於 decision-form.md — 無 OQ 變動
- [ ] All architectural-adjacent decisions documented as ADR — N/A(F1+F2 純 algorithmic refinement,non-architectural per H1)
- [ ] progress.md retro section 寫好 7 段 per F4 closeout(pending)
- [ ] progress.md frontmatter status flipped per outcome
- [ ] Phase W41+ kickoff trigger 標記於 retro

---

**Lifecycle reminder**:本 checklist 隨 plan deliverables 衍生。
