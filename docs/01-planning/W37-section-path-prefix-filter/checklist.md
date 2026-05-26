---
phase: W37-section-path-prefix-filter
plan_ref: ./plan.md
status: active   # F0 啟動 2026-05-27
last_updated: 2026-05-27
---

# W37 — Checklist

> 原子化勾選項(每項 ≤ 1-2 小時工時)。(j') section_path prefix filter quality-of-cite refinement — W32 (h') module enhancement,additive constraint,depth=0 default preserve W36 baseline。

## F0 — 啟動(plan + checklist + progress + R6 grep 驗證 + session-start sync)

- [x] F0.1 建立 `docs/01-planning/W37-section-path-prefix-filter/` folder
- [x] F0.2 R6 Day 0 recursive grep 驗證 — **catch (1)** `HybridSearcher.fetch_chunks_by_section_path` 已存在 W26 F2 ADR-0037(parent_doc 用途,**不**重複 build);**catch (2)** `_find_neighbour_chunks` 當前 filter 只用 `chunk_title regex \b\d+\.\d+\b`(W37 加 NEW additive section_path constraint);**catch (3)** `Settings.py:198-228` 4 處 section_path 屬 W26 parent-doc context — W37 NEW knob 用獨立命名空間 `citation_expansion_section_path_prefix_depth` 避免 confusion;**catch (4)** `list_chunks` return shape 已含 section_path(`hybrid.py:533`)+ test helper `_doc_chunk` 已有 `"section_path": []` field — W37 implementation 純內部 filter no schema change
- [x] F0.3 起草 `plan.md` 7 段
- [x] F0.4 起草 `checklist.md` 原子化勾選項(本文件)
- [x] F0.5 起草 `progress.md` Day 0 — 啟動行動 + R6 4 catches 報告 + W32-W36 (j') preserved 連鎖 + F-phase pre-implementation surface
- [x] F0.6 啟動 commit `65694d6` — `docs(planning): kickoff W37-section-path-prefix-filter + R6 Day 0 4 catches surface (j') quality-of-cite refinement scope confirmed`
- [x] F0.7 session-start.md §10 W37 row append `🟡 active 2026-05-27` + W37+ → W38+ placeholder rename + W36 已 closed 維持(commit `6cdece6`)

## F1 — `_find_neighbour_chunks` 加 section_path prefix filter(~1h)

### F1.1 Settings NEW knob

- [ ] F1.1.a `backend/storage/settings.py:275` 後加 NEW field `citation_expansion_section_path_prefix_depth: int = 0` + comment block 解釋 depth=0 disabled / depth=1 top-level / depth=2 top+sub-level + 為何 default 0 preserve W36 baseline(per W26 PC1「一次只郁一個旋鈕」)
- [ ] F1.1.b 確認 default 0 = W37 baseline preserve(W36 → W37 同 production behavior)
- [ ] F1.1.c 確認 naming convention 對齊 `citation_expansion_window` + `citation_expansion_max_aux` family

### F1.2 `_find_neighbour_chunks` 加 section_path_prefix_depth 參數

- [ ] F1.2.a `backend/generation/citation_expansion.py:_find_neighbour_chunks` (line 63-107) signature 加 `cited_section_path: list[str]` + `section_path_prefix_depth: int` 兩 keyword-only params
- [ ] F1.2.b 在 chunk_title regex filter(line 99-101)之後加 NEW filter block(per plan §2 F1.2.b 5 行 implementation snippet)
- [ ] F1.2.c `expand_citations` (line 110-) propagate — 由 cited chunk's `fields.section_path` 取得 cited_section_path + 從 `settings.citation_expansion_section_path_prefix_depth` 取 depth + 傳入 `_find_neighbour_chunks` call site(line 216-)
- [ ] F1.2.d Defensive — cited chunk 嘅 `section_path` 不是 list(e.g. None / str / dict)→ fall back to `[]`(depth 0 vs N 都會 trivially match empty prefix)

### F1.3 NEW unit tests(~5 個 + 1-2 個 expand_citations integration test)

- [ ] F1.3.a `test_w37_section_path_prefix_filter_disabled_when_depth_0` — depth=0(default)→ 行為 unchanged
- [ ] F1.3.b `test_w37_section_path_prefix_depth_1_filters_cross_section_neighbors` — top-level "Doc" same but second-level different(實際係 depth=2 case;F1.2 spec 確認 depth=1 對 single-doc KB 幾乎 no-op)— 改寫成 depth=2 case
- [ ] F1.3.c `test_w37_section_path_prefix_depth_2_keeps_same_subsection_neighbors` — depth=2,cited + neighbor 都喺 ["Doc", "§8"] tree → kept
- [ ] F1.3.d `test_w37_section_path_prefix_depth_2_filters_different_subsection_neighbors` — depth=2,cited ["Doc", "§8"] vs neighbor ["Doc", "§3"] → filtered
- [ ] F1.3.e `test_w37_malformed_section_path_field_defensive_skip` — neighbor chunk `section_path` 不是 list → skipped
- [ ] F1.3.f(optional)`test_w37_expand_citations_integration_passes_cited_section_path` — integration test 驗證 `expand_citations` 正確 propagate cited_section_path + depth 至 `_find_neighbour_chunks`(mock engine.list_chunks)

### F1.4 驗證 + commit

- [ ] F1.4.a pytest 1086 → 1091(+5 minimum)maintained;ruff PASS;mypy strict 維持
- [ ] F1.4.b commit `feat(generation): W37 F1 (j') section_path prefix filter for _find_neighbour_chunks — additive constraint depth=0 default preserve W36 baseline + Settings NEW knob`

## F2 — 5-run reproducibility verify(~30-45min)

### F2.1 Pre-flight per CLAUDE.md §10.3 step 5b(W36 PC-W34-1 amend 已 ship)

- [ ] F2.1.a `Invoke-WebRequest -Uri http://localhost:3000/api/public/health -TimeoutSec 30`(預期 200 — Langfuse endpoint)
- [ ] F2.1.b `docker exec ekp-postgres psql -U langfuse -d postgres -c "SELECT 1;"`(預期 `1 row` ready_for_query)
- [ ] F2.1.c Backend uvicorn explicit kill + restart 確認 W37 F1 code loaded(per PC-W32-1 `api/server.py:357` no `reload=True` — WatchFiles inactive,W32 F2 iter 1 stale-code trap lesson)

### F2.2 `.env` temporary override + 5-run runner

- [ ] F2.2.a `.env` 加 marker block `# W37 F2 TEMPORARY override — F3 closeout 移除` + `CITATION_EXPANSION_SECTION_PATH_PREFIX_DEPTH=2`(per W27/W29 pattern)
- [ ] F2.2.b Backend restart 確認 override loaded(`Settings().citation_expansion_section_path_prefix_depth == 2`)
- [ ] F2.2.c 寫 `backend/w37-f2-runner.py`(複用 W35 F2 5-run runner pattern,sys.stdout.reconfigure utf-8 + ASCII fallback per PC-W35-1 W36 ship)
- [ ] F2.2.d Runner 加 NEW per-run metric:`cross_section_drift_count`(count of citations whose `section_path[:2]` ≠ first citation's `section_path[:2]`)
- [ ] F2.2.e Run `python w37-f2-runner.py` — 5 runs Q-W25-I07 + 5 runs Q-W25-I01 control

### F2.3 G1 + G2 + G1b decision tree intersect

- [ ] F2.3.a **G1a strict 5/5** — citation_count avg ≥ W35 baseline 4.8 + refusals 0/5(W32 (h') saturated 100% MUST preserve)
- [ ] F2.3.b **G1b NEW same-section quality signal** — `cross_section_drift_count` avg ≤ 1(goal)OR = 0 across all runs(stretch)
- [ ] F2.3.c **G2 control I01 non-regression** — refusals 0/5 + avg_cit ≥ 3.5
- [ ] F2.3.d **G3 pytest 1091 + ruff PASS + mypy strict 維持**
- [ ] F2.3.e **G4 R6 4 catches verified** at Day 0 + Day 1 active flip
- [ ] F2.3.f Decide outcome — (a) PASS / (b) PARTIAL / (c) FAIL revert

## F3 — 收尾 + 跨文件同步 + commit + push

### A. 跨文件同步 per CLAUDE.md §10 R3 + R5 + R6

- [ ] plan.md frontmatter `status: active → closed`(F3 commit time)
- [ ] checklist.md cross-cutting tick + N/A reason(本文件)
- [ ] progress.md retro 7 段(What Worked / What Didn't / Carry-overs / ADR Triggers / Phase Gate Result / W38+ Priority Queue Locked / Actual vs Planned Effort)
- [ ] session-start.md §10 W37 row `🟡 active` → `✅ closed`(F3 commit time)
- [ ] `.env` 移除 W37 F2 marker block(per W27/W29 pattern;production preserve depth=0)
- [ ] 🚧 RISK_REGISTER NEW R 候選 — DEFERRED W38+(若 F2 outcome (b) drift > 0 殘留)OR N/A(若 outcome (a) drift = 0)
- [ ] ADR README — 無 NEW ADR(F1 純內部 filter logic,non-architectural per H1)

### B. W38+ priority queue 評估

- [ ] B.1 W38+ 候選 promotion per F2 outcome(documented retro §W38+ Priority Queue Locked)
- [ ] B.2 PC-W33-1 + PC-W32-1/2 保留低優先級
- [ ] B.3 8 個 pre-existing ruff issues 喺 runner files(W33-W35 寫 runner 留底)保留 LOW
- [ ] B.4 Q14 SME-validate reference_answer cascade(eval-set-v1-final.yaml W15 F1 CO ship)— LONG-TERM
- [ ] B.5 W35 DEMOTED LOW 候選 仍 LOW + path (a) judge LLM 升級 永久 OUT per memory feedback_judge_llm_cost_policy.md
- [ ] B.6 長期 carry-over(c)(e)(f)/BUG-026+027/W22 D8/W16 F1-F4 Track A IT cred 維持

### C. commit + push

- [ ] F3 收尾 commit `docs(planning): W37 closeout — (j') section_path prefix filter ship + quality-of-cite refinement <outcome verdict>`
- [ ] push origin/main confirmed

---

## Cross-Cutting

- [ ] All deliverables committed to git
- [ ] All OQ status changes 反映於 `docs/decision-form.md` — 預期無 OQ 變動
- [ ] All architectural-adjacent decisions documented as ADR — N/A(F1 非 architectural per H1)
- [ ] `progress.md` retro section 寫好 — 7 段 per F3 closeout
- [ ] `progress.md` frontmatter status flipped to `closed`
- [ ] Phase W38+ kickoff trigger 標記於 retro — candidates list update per F2 outcome

---

**Lifecycle reminder**:本 checklist 隨 plan deliverables 衍生。新加 deliverable 必須先入 plan + changelog 然後再加 checklist item。
