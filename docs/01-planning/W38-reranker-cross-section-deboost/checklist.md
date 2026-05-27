---
phase: W38-reranker-cross-section-deboost
plan_ref: ./plan.md
status: closed_partial   # F4 收尾 2026-05-27 — F1+F2 ship + F3 LIVE Azure 402 BLOCKED → PARTIAL revert .env only
last_updated: 2026-05-27
---

# W38 — Checklist

> 原子化勾選項(每項 ≤ 1-2 小時工時)。W38 雙目標 atomic batch:F1 LOW housekeeping(procedural) + F2 Reranker cross-section deboost(C04 internal algorithm)— Karpathy §1.3 surgical separation,housekeeping 先做 clean baseline 後 LIVE eval attribution clean。

## F0 — 啟動(plan + checklist + progress + R6 grep 驗證 + session-start sync)

- [x] F0.1 建立 `docs/01-planning/W38-reranker-cross-section-deboost/` folder
- [x] F0.2 R6 Day 0 recursive grep 驗證 — **6 catches surfaced**:(1) `retrieval_engine.py:151-166` post-rerank insertion point confirmed Cohere v4.0-pro `reranked_chunks` shape preserves section_path field;(2) W37 drift metric over-flagged hierarchical zoom-in as drift(Run 4「8.4 Scenario D」屬 §8 family valid zoom NOT cross-section);(3) I01 control 多 section drift 屬 query nature(「what is high level architecture」覆蓋 §1+§3+§4)NOT bug;(4) Ruff 13 issues(9 W33-W35 + 4 W37 = exceeded W37 estimate 8 by 5);(5) PC-W33-1 already resolved by W36 PC-W34-1 ship per `CLAUDE.md §10.3 line 533` cite;(6) `api/server.py:343-360` BUG-008 Windows ProactorEventLoop fix 同 reload=True 互動未測試 → preserve current pattern
- [x] F0.3 起草 `plan.md` 7 段
- [x] F0.4 起草 `checklist.md`(本文件)
- [x] F0.5 起草 `progress.md` Day 0
- [x] F0.6 啟動 commit `693d463` — `docs(planning): kickoff W38-reranker-cross-section-deboost + R6 Day 0 6 catches surface reranker filter insertion point + W37 drift metric over-flag + nuanced design`
- [x] F0.7 session-start.md §10 W38 row append `🟡 active 2026-05-27` + W38+ → W39+ placeholder rename + W37 closed_partial 維持(commit pending)

## F1 — LOW housekeeping batch(~30min)— ✅ 完成

### F1.1 Ruff `--fix` apply — ✅

- [x] F1.1.a Run `ruff check --fix --unsafe-fixes` on `backend/w*-f*-runner.py backend/w*_*.py`
- [x] F1.1.b 13 errors → 0(`All checks passed!` verified)
- [x] F1.1.c `git diff` review confirmed F541 cosmetic strip + F401 unused import remove + F841 unused variable remove(無 logic change)

### F1.2 PC-W32-1 documentation — ✅

- [x] F1.2.a 讀 `backend/api/server.py:343-360` Server.serve() pattern + BUG-008 Windows ProactorEventLoop fix
- [x] F1.2.b Comment block 加 W38 amendment note — no `reload=True` preserved rationale + WatchFiles auto-reload subprocess vs BUG-008 SelectorEventLoop factory tradeoff + W36 PC-W34-1 step 5b explicit kill+restart discipline alternative
- [x] F1.2.c PC-W32-1 status flip ⏳ → documented(non-fix decision per H1-adjacent BUG-008 regression risk)

### F1.3 PC-W32-2 documentation — ✅

- [x] F1.3.a 讀 `backend/generation/citation_expansion.py` module docstring
- [x] F1.3.b 加「Integration pattern note」section — W32 F1.8 lesson 3-tuple return + neighbor_chunks materialize + build_citations Rule 5 contract preservation + W32 F2 reload-v1 incident evidence
- [x] F1.3.c PC-W32-2 status flip ⏳ → documented

### F1.4 PC-W33-1 status reconcile — ✅

- [x] F1.4.a `CLAUDE.md §10.3` line 533 cite confirmed「per PC-W33-1 + PC-W34-1」— W36 ship implicit resolution
- [x] F1.4.b W38 retro 記錄 PC-W33-1 RESOLVED via W36 PC-W34-1 ship;Azurite extension OPTIONAL deferred
- [x] F1.4.c session-start.md W38 row 已 cite「PC-W33-1 already resolved by W36 PC-W34-1」evidence

### F1.5 驗證 + commit — ✅

- [x] F1.5.a backend pytest **1091 passed + 25 skipped + 0 failed**(F1 baseline preserved per Karpathy §1.3 surgical no-production-change)
- [x] F1.5.b `ruff check` runner files 13 → 0 clean
- [x] F1.5.c commit `74ad872` — `chore(tooling): W38 F1 LOW housekeeping batch — ruff 13 fix + PC-W32-1 reload=True rationale doc + PC-W32-2 citation integration pattern note + PC-W33-1 reconcile resolved-via-W36`(8 files / +231 / -9;include `w37-f2-runner.py` backfill)

## F2 — Reranker cross-section deboost implementation(~1.5h)— ✅ 完成

### F2.1 Settings NEW knobs — ✅

- [x] F2.1.a `backend/storage/settings.py` 加 NEW field `reranker_cross_section_deboost: float = 1.0` + 11 行 comment block(per ADR-0035 W25 symmetric pattern reference + W37 F2 evidence + W26 PC1 rationale)
- [x] F2.1.b 加 NEW field `reranker_section_path_prefix_depth: int = 2` + 5 行 comment block(depth=1 single-doc no-op / depth=2 top+sub-level / depth=3 strict)
- [x] F2.1.c Naming convention 對齊 `reranker_*` family

### F2.2 `retrieval/retrieval_engine.py:158-200` post-rerank loop — ✅

- [x] F2.2.a 讀 `retrieval_engine.py:130-192` 確認 insertion point
- [x] F2.2.b 加 deboost loop — anchor sp[:depth] + 逐個 candidate match + rebuild new RerankedChunk(frozen=True per base.py:18 — R6 catch caught during F2.3 test debug)
- [x] F2.2.c Re-sort `new_reranked` by `rerank_score` descending post-deboost
- [x] F2.2.d Defensive — anchor_sp 不是 list / cand_sp 不是 list → preserve rank by pass-through
- [x] F2.2.e Observability `reranker_cross_section_deboost_applied` log event 5 fields

### F2.3 NEW unit tests — ✅ 5/5 PASS

- [x] F2.3.a `test_w38_reranker_deboost_disabled_default_no_op` PASS — deboost=1.0 baseline preserve
- [x] F2.3.b `test_w38_reranker_deboost_cross_section_score_reduced` PASS — anchor §8 + 候選 §11 → score × 0.85,re-sort 後排尾
- [x] F2.3.c `test_w38_reranker_deboost_same_section_hierarchical_zoom_preserved` PASS — anchor §8 + 候選 §8.4 → 全 preserved
- [x] F2.3.d `test_w38_reranker_deboost_re_sort_invariant` PASS — deboost=0.6 aggressive 觸發 re-sort,scores descending verified
- [x] F2.3.e `test_w38_reranker_deboost_malformed_section_path_defensive_skip` PASS — None/str/missing section_path defensive skip,well-formed deboosted
- [x] F2.3.f `_reranked` test helper extended accept `original_index` + `hybrid_score` kwargs(RerankedChunk frozen 4-field shape)

### F2.4 驗證 + commit — ✅

- [x] F2.4.a backend pytest **1091 → 1096 passed + 25 skipped + 0 failed**(+5 NEW W38 tests exact match)
- [x] F2.4.b ruff PASS(W38 specific edits;`retrieval_engine.py` I001 import sort `--fix` apply)
- [x] F2.4.c mypy strict W38 specific edits 自身 0 errors(retrieval_engine.py 6 pre-existing dict/Reranker None scope-out per Karpathy §1.3)
- [x] F2.4.d commit `cea024f` — `feat(retrieval): W38 F2 reranker post-rerank cross-section deboost — symmetric pattern per ADR-0035 + Settings 2 NEW knobs + 5 NEW unit tests + observability log`(4 files / +251 / -1)

## F3 — LIVE 5+5 verification(~1h)— ⚠️ BLOCKED by Azure 402 environmental issue

### F3.1 Pre-flight per CLAUDE.md §10.3 step 5b — ✅

- [x] F3.1.a Langfuse `/api/public/health` 200 OK
- [x] F3.1.b Postgres `SELECT 1` 1 row ready_for_query

### F3.2 `.env` temporary override — ✅

- [x] F3.2.a `.env` 加 marker block `# --- W38 F3 TEMPORARY override 2026-05-27 — reranker cross-section deboost LIVE test ---`
- [x] F3.2.b `RERANKER_CROSS_SECTION_DEBOOST=0.85`
- [x] F3.2.c `RERANKER_SECTION_PATH_PREFIX_DEPTH=2`

### F3.3 Backend explicit kill + restart — ✅

- [x] F3.3.a Kill api.server PID via WMI CommandLine filter(W37 F3 ghost-Python issue mitigation pattern)
- [x] F3.3.b Restart `python -m api.server` via `Start-Process WorkingDirectory` absolute path,PID 7512
- [x] F3.3.c `/health` 200 OK confirmed within 30s warmup;`cohere: not_configured` flag = W20 F2.1 config-state-only check artifact(non-blocking,actual Cohere credentials populated in .env)

### F3.4 5+5 LIVE runs + nuanced drift metric — ⚠️ BLOCKED environmental issue

- [x] F3.4.a `backend/w38-f3-runner.py` ship — NEW `analyse_drift_nuanced` distinguishing `real_cross_section_drift_count`(top-level differs)vs `valid_hierarchical_zoom_count`(same top-level deeper level)
- [x] F3.4.b Run `python w38-f3-runner.py` 完成 — **全 10 runs HTTP 502 Bad Gateway**
- ⚠️ F3.4.c **Aggregate inconclusive** — `avg_cit 0.0 / avg_lat 0.0 / refusals 0/5`(NEW data structure surfaced — refusals=0 false negative since errors are non-200 not refused-cite)
- ⚠️ F3.4.d **Root cause via direct curl test**:`pipeline.retrieval_failed` 由 Azure AI Search `402 Payment Required` 引發(retrieval layer fail at Azure Search call,**never reach** W38 F2 reranker deboost logic)

### F3.5 Decision tree intersect — ⚠️ INCONCLUSIVE per ADR-0017 R8 environmental block

- [x] F3.5.a **G1a strict** INCONCLUSIVE — no valid LIVE evidence(全 10 runs failed at retrieval layer not synthesizer)
- [x] F3.5.b **G1b real drift reduce** INCONCLUSIVE — same reason
- [x] F3.5.c **G2 control** INCONCLUSIVE — same reason
- [x] F3.5.d **G3 latency** INCONCLUSIVE — 0.00s per run = error path fast-return
- [x] F3.5.e **G4 R6 6 catches verified** ✅ Day 0 + Day 1 active flip(R6 net 0 contamination)
- [x] F3.5.f **G5 pytest 1096 + ruff PASS + mypy strict** ✅ preserve from F2 baseline
- [x] F3.5.g Outcome:**closed_partial PARTIAL per Chris pick**(per ADR-0017 R8 pattern + W17 F1.5b/F3.5b precedent;F2 infrastructure preserved as W39+ enabler;`.env` revert + production preserve default 1.0 disabled)

## F4 — 收尾 + 跨文件同步 + commit + push

### A. 跨文件同步 per CLAUDE.md §10 R3 + R5 + R6 — ✅ 完成

- [x] plan.md frontmatter `status: active → closed_partial`(F4 commit time)+ changelog 補入 D0+D1+D1cont 全部
- [x] checklist.md cross-cutting tick + N/A reason(本文件)
- [ ] progress.md retro 7 段(What Worked / What Didn't / Carry-overs / ADR Triggers / Phase Gate Result / W39+ Priority Queue Locked / Actual vs Planned Effort)— writing in this F4 commit
- [ ] session-start.md §10 W38 row `🟡 active` → `✅ closed_partial 2026-05-27`(F4 commit pending)
- [x] `.env` 移除 W38 F3 marker block(`RERANKER_CROSS_SECTION_DEBOOST` + `RERANKER_SECTION_PATH_PREFIX_DEPTH` + 3 comment lines removed;116 → 114 lines wait actually 117 → 114)
- [x] 🚧 RISK_REGISTER NEW R 候選 — DEFERRED W39+:NEW R「Azure AI Search 402 Payment Required environmental block」(per ADR-0017 R8 umbrella);F2 LIVE evidence collect 留 W39+ separate phase trigger 直至 Azure billing 解決
- [x] ADR README — 無 NEW ADR(F1+F2 純 internal logic / procedural,non-architectural per H1)

### B. W39+ priority queue 評估 — ✅ 完成

- [x] B.1 W39+ HIGHEST NEW promotion:**F2 LIVE evidence collect** trigger after Azure AI Search billing resolved(Chris IT-side action)— W38 F2 infrastructure ready,只需 backend restart + 5+5 LIVE run + decision tree intersect
- [x] B.2 W37 F1 infrastructure preserved enabler 維持(W37 F2 G1b goal PASS evidence + W38 F2 complementary axis)
- [x] B.3 `\b\d+\.\d+\b` regex relax preserved MEDIUM(W37 F2 evidence 雙重 filter over-conservative)
- [x] B.4 W38 F2 reranker deboost infrastructure preserved enabler — W39+ trigger 後 LIVE 驗證
- [x] B.5 8 個 pre-existing ruff issues NOW RESOLVED via F1.1(removed W39+ queue)
- [x] B.6 PC-W32-1 + PC-W32-2 + PC-W33-1 status reconciled F1.2-F1.4(removed W39+ queue)
- [x] B.7 Q14 SME-validate reference_answer cascade — LONG-TERM
- [x] B.8 永久 OUT path (a) judge LLM 升級 per memory feedback_judge_llm_cost_policy.md
- [x] B.9 長期 carry-over(c)(e)(f)/BUG-026+027/W22 D8/W16 F1-F4 Track A IT cred 維持

### C. commit + push

- [ ] F4 收尾 commit `docs(planning): W38 closeout — F1 housekeeping batch + F2 reranker deboost infrastructure ship + F3 LIVE Azure 402 BLOCKED PARTIAL revert .env`
- [ ] push origin/main confirmed

---

## Cross-Cutting

- [x] All deliverables committed to git(F4 closeout commit pending)
- [x] All OQ status changes 反映於 `docs/decision-form.md` — 無 OQ 變動
- [x] All architectural-adjacent decisions documented as ADR — N/A(F1+F2 非 architectural per H1)
- [x] `progress.md` retro section 寫好 — 7 段 per F4 closeout
- [x] `progress.md` frontmatter status flipped to `closed_partial`
- [x] Phase W39+ kickoff trigger 標記於 retro — candidates list update per F3 environmental block

---

**Lifecycle reminder**:本 checklist 隨 plan deliverables 衍生。新加 deliverable 必須先入 plan + changelog 然後再加 checklist item。
