---
phase: W37-section-path-prefix-filter
plan_ref: ./plan.md
status: closed_partial   # F3 收尾 2026-05-27 — Phase Gate FAIL outcome (c) → PARTIAL revert (.env removed,F1 code preserved)
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

## F1 — `_find_neighbour_chunks` 加 section_path prefix filter(~1h)— ✅ 完成

### F1.1 Settings NEW knob — ✅

- [x] F1.1.a `backend/storage/settings.py:275-285` 加 NEW field `citation_expansion_section_path_prefix_depth: int = 0` + 11 行 comment block(depth=0 disabled / depth=1 top-level / depth=2 top+sub-level + W26 PC1「一次只郁一個旋鈕」rationale + W38+ separate decision)
- [x] F1.1.b default=0 確認 = W37 baseline preserve(W36 → W37 同 production behavior)
- [x] F1.1.c naming convention 對齊 `citation_expansion_window` + `citation_expansion_max_aux` family

### F1.2 `_find_neighbour_chunks` 加 section_path_prefix_depth 參數 — ✅

- [x] F1.2.a `_find_neighbour_chunks` signature 加 `cited_section_path: list[str] | None = None` + `section_path_prefix_depth: int = 0`(backward-compat default,9+ existing tests 無需改)
- [x] F1.2.b 在 §X.M regex filter 之後加 9-行 filter block:`isinstance` defensive guard + `list(cand[:depth]) != cited_prefix` 比對 + `continue` 跳 cross-section candidate
- [x] F1.2.c `expand_citations` propagate — `cited_by_doc` 3-tuple extension `(cited_id, cited_idx, cited_sp)` + call site 傳 `cited_section_path=cited_sp` + `section_path_prefix_depth=settings.citation_expansion_section_path_prefix_depth`
- [x] F1.2.d Defensive — `cited_sp_raw` `isinstance(..., list)` else `[]` fall back(per W37 F1.2 spec)
- [x] F1.2.e Observability — 兩個 logger event(`citation_expansion_neighbours_found` + `citation_expansion_applied`)加 `section_path_prefix_depth` + `cited_section_path_prefix` fields

### F1.3 NEW unit tests — ✅ 5/5 PASS

- [x] F1.3.a `test_w37_section_path_prefix_filter_disabled_when_depth_0` PASS — depth=0 baseline preserve
- [x] F1.3.b `test_w37_section_path_prefix_depth_2_filters_different_subsection_neighbors` PASS — cited ["Doc","§8","§8.1"] vs neighbor ["Doc","§3"] → filtered;same-section ["Doc","§8"] → kept
- [x] F1.3.c `test_w37_section_path_prefix_depth_2_keeps_same_subsection_neighbors` PASS — 3 個 ["Doc","§8",...] siblings 全 kept
- [x] F1.3.d `test_w37_malformed_section_path_field_defensive_skip` PASS — missing field + non-list `section_path` defensive skip;well-formed 通過
- [x] F1.3.e `test_w37_expand_citations_propagates_section_path_filter` PASS — end-to-end integration,cited ["Doc","§8"] expand 限 same-section neighbors,materialized neighbor_chunks 對齊 filtered set
- [x] F1.3.f 同步 update `_doc_chunk` helper 加 optional `section_path` kwarg + `_settings` helper 加 `section_path_prefix_depth` kwarg(backward-compat defaults preserve 既有 9+ tests)

### F1.4 驗證 + commit — ✅

- [x] F1.4.a backend pytest **1091 passed + 25 skipped + 0 failed**(W36 baseline 1086 + 5 NEW W37 = 1091 exact match);ruff `All checks passed!`(W37 specific edits);mypy strict citation_expansion.py + settings.py 自身 0 errors(13 pre-existing 全屬 observability/retrieval/context_expander W22-W34 wave 留底,Karpathy §1.3 surgical 不屬 W37 scope)
- [x] F1.4.b commit `da557ab` — `feat(generation): W37 F1 (j') section_path prefix filter for _find_neighbour_chunks — additive constraint depth=0 default preserve W36 baseline + Settings NEW knob`(5 files / +274 / -25)

## F2 — 5-run reproducibility verify(~30-45min)— ✅ 完成 PARTIAL outcome (c) FAIL

### F2.1 Pre-flight per CLAUDE.md §10.3 step 5b — ✅

- [x] F2.1.a Langfuse `/api/public/health` 200 OK
- [x] F2.1.b Postgres `SELECT 1` 1 row ready_for_query
- [x] F2.1.c Backend uvicorn explicit kill (PID 23260) + restart (PID 30340) 確認 W37 F1 code loaded(per PC-W32-1 W32 F2 iter 1 stale-code trap lesson)

### F2.2 `.env` temporary override + 5-run runner — ✅

- [x] F2.2.a `.env` 加 marker block `# --- W37 F2 TEMPORARY override 2026-05-27` + `CITATION_EXPANSION_SECTION_PATH_PREFIX_DEPTH=2`(112 → 117 lines)
- [x] F2.2.b Backend restart 確認 override loaded(F2 runner 5+5 LIVE runs 確認 filter active via Langfuse event firing)
- [x] F2.2.c `backend/w37-f2-runner.py` shipped(複用 W35 F2 pattern + W36 PC-W35-1 utf-8 fix + NEW `analyse_drift` helper)
- [x] F2.2.d Runner 加 per-run metric:`cross_section_drift_count` + `unique_section_prefixes`
- [x] F2.2.e Run `python w37-f2-runner.py` — 5 runs Q-W25-I07 + 5 runs Q-W25-I01 control(Run 3 I07 HTTP 502 Azure transient,4/5 valid)

### F2.3 G1 + G2 + G1b decision tree intersect — ✅ FAIL outcome (c)

| Gate | 結果 | Evidence |
|---|---|---|
| **G1a strict** refusals=0 + avg_cit ≥ 4.8 | ⚠️ FAIL | I07 avg_cit **1.8**(W35 baseline 4.8,**-63%**)+ refusals 0/5 ✅ partial |
| **G1b goal** I07 avg_drift ≤ 1.0 | ✅ PASS | I07 avg_drift **0.75** ≤ 1.0 |
| **G1b stretch** I07 drift = 0 across all runs | ⚠️ FAIL | Run 2 drift=2 + Run 4 drift=1 |
| **G2 control** I01 refusals=0 + avg_cit ≥ 3.5 | ⚠️ FAIL | I01 avg_cit **2.8**(W35 baseline 5.4,**-48%**)+ refusals 0/5 ✅ partial |
| **G3 pytest 1091 + ruff + mypy strict** | ✅ PASS | maintained from F1 |
| **G4 R6 4 catches** | ✅ PASS | Day 0 4 catches + Day 1 active flip |

- [x] F2.3.f Decide outcome — **(c) FAIL** Phase Gate per plan §3 outcome matrix → User pick **PARTIAL revert**(per W31 PC-W31-2 + W27 F1 precedent;F1 code preserved as W38+ enabler,evidence value 高 — G1b goal PASS 證明 filter 有 work,bottleneck shifted to reranker layer not citation_expansion)

## F3 — 收尾 + 跨文件同步 + commit + push — ✅ 進行中

### A. 跨文件同步 per CLAUDE.md §10 R3 + R5 + R6

- [x] plan.md frontmatter `status: active → closed_partial` + changelog D0+D1+D1 cont 追加
- [x] checklist.md cross-cutting tick(本文件 frontmatter status 同步 + F2 tick + F3 entry)
- [x] progress.md retro 7 段(What Worked / What Didn't / Carry-overs / ADR Triggers / Phase Gate Result / W38+ Priority Queue Locked / Actual vs Planned Effort)
- [x] session-start.md §10 W37 row `🟡 active` → `✅ closed_partial 2026-05-27`(commit pending);W38+ placeholder row 同步 update reranker-side filter HIGHEST + regex relax MEDIUM
- [x] `.env` 移除 W37 F2 marker block(`CITATION_EXPANSION_SECTION_PATH_PREFIX_DEPTH=2` line + 3 comment lines removed;117 → 113 lines;production preserve depth=0 Settings default ship)
- [x] 🚧 RISK_REGISTER NEW R 候選 — DEFERRED W38+(F2 evidence:bottleneck reranker-side cross-section surfacing,citation_expansion filter scope-out per design;W38+ candidate = reranker-side filter OR `\b\d+\.\d+\b` regex relax)
- [x] ADR README — 無 NEW ADR(F1 純內部 filter logic,non-architectural per H1)

## F3 — 收尾 + 跨文件同步 + commit + push

### A. 跨文件同步 per CLAUDE.md §10 R3 + R5 + R6

- [ ] plan.md frontmatter `status: active → closed`(F3 commit time)
- [ ] checklist.md cross-cutting tick + N/A reason(本文件)
- [ ] progress.md retro 7 段(What Worked / What Didn't / Carry-overs / ADR Triggers / Phase Gate Result / W38+ Priority Queue Locked / Actual vs Planned Effort)
- [ ] session-start.md §10 W37 row `🟡 active` → `✅ closed`(F3 commit time)
- [ ] `.env` 移除 W37 F2 marker block(per W27/W29 pattern;production preserve depth=0)
- [ ] 🚧 RISK_REGISTER NEW R 候選 — DEFERRED W38+(若 F2 outcome (b) drift > 0 殘留)OR N/A(若 outcome (a) drift = 0)
- [ ] ADR README — 無 NEW ADR(F1 純內部 filter logic,non-architectural per H1)

### B. W38+ priority queue 評估 — ✅ 完成

- [x] B.1 W38+ HIGHEST NEW reranker-side cross-section filter promotion per F2 root cause shift evidence(documented retro §W38+ Priority Queue Locked)
- [x] B.2 W38+ MEDIUM NEW `\b\d+\.\d+\b` regex relax for `_find_neighbour_chunks`
- [x] B.3 W37 F1 infrastructure MEDIUM preserved enabler
- [x] B.4 PC-W33-1 + PC-W32-1/2 保留低優先級
- [x] B.5 8 個 pre-existing ruff issues 喺 runner files(W33-W35 寫 runner 留底)保留 LOW
- [x] B.6 Q14 SME-validate reference_answer cascade(eval-set-v1-final.yaml W15 F1 CO ship)— LONG-TERM
- [x] B.7 W35 DEMOTED LOW 候選 仍 LOW + path (a) judge LLM 升級 永久 OUT per memory feedback_judge_llm_cost_policy.md
- [x] B.8 長期 carry-over(c)(e)(f)/BUG-026+027/W22 D8/W16 F1-F4 Track A IT cred 維持

### C. commit + push

- [ ] F3 收尾 commit `docs(planning): W37 closeout — (j') section_path prefix filter ship F1 preserved + F2 FAIL outcome (c) PARTIAL revert .env + W38+ reranker-side filter pivot`
- [ ] push origin/main confirmed

---

## Cross-Cutting

- [x] All deliverables committed to git(F3 closeout commit pending)
- [x] All OQ status changes 反映於 `docs/decision-form.md` — 無 OQ 變動
- [x] All architectural-adjacent decisions documented as ADR — N/A(F1 非 architectural per H1)
- [x] `progress.md` retro section 寫好 — 7 段 per F3 closeout
- [x] `progress.md` frontmatter status flipped to `closed_partial`
- [x] Phase W38+ kickoff trigger 標記於 retro — candidates list update per F2 outcome

---

**Lifecycle reminder**:本 checklist 隨 plan deliverables 衍生。新加 deliverable 必須先入 plan + changelog 然後再加 checklist item。
