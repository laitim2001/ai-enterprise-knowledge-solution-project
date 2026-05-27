---
phase: W37-section-path-prefix-filter
status: closed_partial   # F3 收尾 2026-05-27 — Phase Gate FAIL outcome (c) per plan §3 (G1a regress -63% I07 cit + G2 regress -48% I01 cit) → PARTIAL revert per Chris pick:`.env` marker block removed,F1 production code preserved as W38+ enabler。Settings default=0 已 preserve W36 baseline,production behavior 100% revert
last_updated: 2026-05-27
component_scope: C04 Retrieval Engine + C05 Generation Pipeline(citation_expansion._find_neighbour_chunks 內 section_path prefix filter — W32 (h') module enhancement)
adr_refs:
  - W32 progress.md §retro lines 327 + 348 — (j') 原始 source「Section_path prefix filter for `_find_neighbour_chunks`」
  - W33 progress.md §retro line 250 — preserved W34+ 「tighter same-section expansion via `_find_neighbour_chunks`」
  - W34 progress.md §retro line 377 — preserved W35+ 「quality-of-cite refinement,independent axis from G1/G2 measurement」
  - W35 progress.md §retro lines 316 / 365 / 392 — preserved W36+ MEDIUM
  - W36 checklist.md §B.2 — preserved W37+ MEDIUM
  - W32 F1 base — `backend/generation/citation_expansion.py:_find_neighbour_chunks` line 63-107(W32 (h') engine-fetch module)
  - architecture.md §3.6 line 364 — `section_path` field 已 indexed `Collection(Edm.String)` filterable
related_carry_overs:
  - W32-W36 累積 MEDIUM (j') 候選持續 preserved — W37 兌現
  - 同 W26 parent_doc_retriever.py 共用 section_path 機制但**用途不同**(parent-doc 係 retrieval-side aggregation;W37 (j') 係 citation-side post-rerank expansion filter)
---

# W37 — (j') section_path Prefix Filter for `_find_neighbour_chunks`

## §1 目標 + 範疇

**單一主要目標**:在 W32 (h') engine-fetch citation expansion(`citation_expansion._find_neighbour_chunks`)加入 **section_path prefix filter**,使 auto-added neighbor citation 限喺 cited anchor 同一 top-level section 內,避免 cross-section drift(per W32 progress.md line 327 + 348 + 348 原始 evidence:Run 1/3/4 cite 出現 mix §3/§6/§7/§9 alongside §8)。

**Karpathy §1.3 surgical scope 嚴守**:
- F1 = `_find_neighbour_chunks` 加 `section_path_prefix_depth` 參數 + Settings NEW knob `citation_expansion_section_path_prefix_depth=1` default + `expand_citations` propagate + 3-5 NEW unit tests
- F2 = 5-run reproducibility Q-W25-I07 + Q-W25-I01 control verify same-section breadth vs W33+W34+W35 cross-section baseline
- F3 = closeout 跨文件同步 + commit + push

**Non-goals**(W37 範疇外):
- 任何 production behavior change beyond `_find_neighbour_chunks` filter logic(無 Rule 變動 / 無 synthesizer / retrieval-engine 改動)
- W26 parent_doc_retriever.py 改動(用途不同,共用 section_path primitive 但 retrieval-side 唔屬本 phase scope)
- RAGAs full eval re-run(W37 屬 quality-of-cite refinement,**independent axis from G1/G2** per W34 retro framing;F2 5-run sanity check 已 sufficient)
- 任何架構 change(per H1,非 architectural)
- prompt token reduction / engine-fetch async pool — W35 F2 evidence DEMOTED LOW
- PC-W33-1 + PC-W32-1/2 — preserved W38+ housekeeping

**Component 範疇**:
- **C04 Retrieval Engine**(`section_path` field 來源 — Azure Search index `Collection(Edm.String)` per architecture.md §3.6 line 364)
- **C05 Generation Pipeline**(`citation_expansion.py:_find_neighbour_chunks` filter logic)
- **不涉及** C01-C03 / C06-C13(無 ingestion / chunker / KB / auth / eval / frontend 改動)

---

## §2 交付物 F0-F3

### F0 — 啟動(本 session 2026-05-27)

- F0.1 建立 `docs/01-planning/W37-section-path-prefix-filter/` folder
- F0.2 R6 Day 0 recursive grep 驗證 — **catch (1)**:`HybridSearcher.fetch_chunks_by_section_path` 已存在(W26 F2 ADR-0037 leaf primitive,屬 parent_doc_retriever 用途,**不重複 build**);**catch (2)**:`_find_neighbour_chunks` 當前 filter 只用 `chunk_title regex \b\d+\.\d+\b`(§X.M)— section_path filter 係 NEW additive constraint;**catch (3)**:`Settings.py:198-228` 已有 4 處 section_path reference 但都屬 W26 parent-doc context(`parent_doc_section_depth_offset` 等),W37 NEW knob 用獨立命名空間 `citation_expansion_section_path_prefix_depth` 避免 confusion;**catch (4)**:`list_chunks` return shape 已含 section_path(`hybrid.py:533`)+ test helper `_doc_chunk` 已有 `"section_path": []` field(line 69 `test_citation_expansion.py`)— W37 implementation 純內部 filter no schema change
- F0.3 起草 `plan.md` 7 段(本文件)
- F0.4 起草 `checklist.md` 原子化勾選項
- F0.5 起草 `progress.md` Day 0 — 啟動行動 + R6 4 catches 報告 + W32-W36 (j') preserved 連鎖 + F-phase pre-implementation surface
- F0.6 啟動 commit `docs(planning): kickoff W37-section-path-prefix-filter + R6 Day 0 4 catches surface (j') quality-of-cite refinement scope confirmed`
- F0.7 session-start.md §10 W37 row append `🟡 active 2026-05-27` + W36 已 closed 維持

### F1 — `_find_neighbour_chunks` 加 section_path prefix filter(~1h)

#### F1.1 Settings NEW knob

- F1.1.a `backend/storage/settings.py:275` 後加 NEW field:
  ```python
  # W37 (j') section_path prefix filter for engine-fetch citation expansion
  # — `_find_neighbour_chunks` 額外要求 neighbor candidate 嘅 section_path[:depth]
  # 同 cited anchor 嘅 section_path[:depth] 完全相同。Default depth=1 = top-level
  # section only(e.g. cited "§8.1" + neighbor 必須都喺 ["Doc", "§8"] tree
  # 內 — 唔可以 jump 到 ["Doc", "§3"])。depth=0 = disabled(W37 baseline
  # preserve;若 G1b cross-section drift = 0 evidence 後 W38+ flip default
  # depth=1 production)。
  citation_expansion_section_path_prefix_depth: int = 0
  ```
- F1.1.b ✅ default 0 = W37 baseline preserve(W26 PC1 「一次只郁一個旋鈕」紀律 — flip default 屬 W38+ separate decision based on F2 outcome)
- F1.1.c 確認 `Settings` 已有 `citation_expansion_window` (line 270) + `citation_expansion_max_aux` (line 274) 即 (h') family knob naming convention 對齊

#### F1.2 `_find_neighbour_chunks` 加 section_path_prefix_depth 參數

- F1.2.a `backend/generation/citation_expansion.py:_find_neighbour_chunks` (line 63-107) signature 加 `cited_section_path: list[str]` + `section_path_prefix_depth: int` 兩 keyword-only params
- F1.2.b 在 chunk_title regex filter(line 99-101)之後加 NEW filter block:
  ```python
  # W37 (j') section_path prefix filter — if depth > 0, require neighbor's
  # section_path[:depth] match cited's section_path[:depth] exactly(避免 cross-
  # section drift,e.g. cited §8.1 唔該擴展去 §3.x 或 §11.x 上下文)。
  # depth=0 = filter disabled(W37 baseline preserve);depth=1 = top-level
  # section match required;depth=2 = top + sub-level match required。
  if section_path_prefix_depth > 0:
      cand_section_path = chunk.get("section_path") or []
      if not isinstance(cand_section_path, list):
          continue  # malformed field — skip defensive
      cand_prefix = cand_section_path[:section_path_prefix_depth]
      cited_prefix = cited_section_path[:section_path_prefix_depth]
      if cand_prefix != cited_prefix:
          continue
  ```
- F1.2.c `expand_citations` (line 110-) propagate — 由 cited chunk's `fields.section_path` 取得 cited_section_path + 從 `settings.citation_expansion_section_path_prefix_depth` 取 depth + 傳入 `_find_neighbour_chunks` call site(line 216-)

#### F1.3 NEW unit tests(~5 個)

- F1.3.a `test_w37_section_path_prefix_filter_disabled_when_depth_0`:depth=0(default)→ 行為 unchanged(neighbor candidate 唔過濾 by section_path,只 by §X.M regex)
- F1.3.b `test_w37_section_path_prefix_depth_1_filters_cross_section_neighbors`:cited 喺 ["Doc", "§8"],neighbor candidate 喺 ["Doc", "§3"] 嘅 §3.5 → filtered out(就算 §X.M regex match)
- F1.3.c `test_w37_section_path_prefix_depth_1_keeps_same_section_neighbors`:cited 喺 ["Doc", "§8", "§8.1"],neighbor candidate 喺 ["Doc", "§8", "§8.4"] → kept(prefix[:1] = ["Doc"]?或 [:1] = "Doc" only?)— **clarify per F1.2 spec**:[:1] = top-level section "Doc" → 所有 same-doc chunks 都 pass top-level filter;**真正 cross-section filter 需 depth=2**(["Doc", "§8"] vs ["Doc", "§3"] 區分)
- F1.3.d `test_w37_section_path_prefix_depth_2_strict_same_subsection`:depth=2 → cited ["Doc", "§8", "§8.1"] vs neighbor ["Doc", "§8", "§8.4"] → kept;vs neighbor ["Doc", "§3", "§3.5"] → filtered
- F1.3.e `test_w37_malformed_section_path_field_skipped_defensive`:neighbor chunk 嘅 `section_path` 不是 list(e.g. None / str / dict)→ skipped defensive

#### F1.4 commit

- F1.4.a pytest baseline 1086 → 1091(+5)maintained;ruff PASS;mypy strict 維持
- F1.4.b commit `feat(generation): W37 F1 (j') section_path prefix filter for _find_neighbour_chunks — additive constraint,depth=0 default preserve W36 baseline + Settings NEW knob`

### F2 — 5-run reproducibility verify(~30-45min)

#### F2.1 Pre-flight per CLAUDE.md §10.3 step 5b(W36 PC-W34-1 amend 已 ship)

- F2.1.a `Invoke-WebRequest -Uri http://localhost:3000/api/public/health -TimeoutSec 30`(預期 200,Langfuse endpoint)
- F2.1.b `docker exec ekp-postgres psql -U langfuse -d postgres -c "SELECT 1;"`(預期 `1 row` ready_for_query)
- F2.1.c Backend uvicorn restart 確認 W37 F1 code loaded(per PC-W32-1 `api/server.py:357` no `reload=True` — WatchFiles inactive)

#### F2.2 5-run I07 + 5-run I01 control measurement(temporary `.env` override)

- F2.2.a `.env` 加 `CITATION_EXPANSION_SECTION_PATH_PREFIX_DEPTH=2`(temporary override,F3 closeout 移除 marker block per W27/W29 pattern)
- F2.2.b Backend restart 確認 override loaded
- F2.2.c `python w37-f2-runner.py`(複用 W35 F2 5-run runner pattern,sys.stdout.reconfigure utf-8 + ASCII fallback per PC-W35-1 W36 ship)— 5 runs Q-W25-I07 + 5 runs Q-W25-I01 control
- F2.2.d Aggregate per-run:`citation_count` + `cross_section_drift_count`(NEW metric:count of citations whose `section_path[:2]` ≠ first citation's `section_path[:2]`)+ `latency_ms`

#### F2.3 G1 + G2 + G1b decision tree intersect

- F2.3.a **G1a strict 5/5** + 100% MAINTAIN(non-regression — citation_count avg ≥ W35 4.8 baseline,refusals 0/5)
- F2.3.b **G1b NEW same-section quality signal**:Run-level `cross_section_drift_count` decrease vs W35 baseline(W33/W34 Run 1/3/4 mix §3/§6/§9 alongside §8 evidence)— ideal = 0 across all 5 runs,acceptable ≤ 1 average
- F2.3.c **G2 control I01 non-regression** — refusals 0/5 + avg_cit ≥ 3.5(W35 baseline 5.4)
- F2.3.d **G3 pytest 1091 + ruff PASS + mypy strict 維持**
- F2.3.e **G4 R6 4 catches verified** at Day 0 + Day 1 active flip

### F3 — 收尾 + 跨文件同步 + commit + push(~30min)

- F3.A.1 plan.md frontmatter `status: active → closed`(F3 commit time)
- F3.A.2 checklist.md cross-cutting tick + N/A reason
- F3.A.3 progress.md retro 7 段(What Worked / What Didn't / Carry-overs / ADR Triggers / Phase Gate Result / W38+ Priority Queue Locked / Actual vs Planned Effort)
- F3.A.4 session-start.md §10 W37 row `🟡 active` → `✅ closed`(F3 commit time)
- F3.A.5 🚧 RISK_REGISTER NEW R 候選 — DEFERRED W38+(若 F2 G1b 真有 drift 殘留)OR N/A(若 G1b 全 PASS)
- F3.A.6 ADR README — 無 NEW ADR(F1 純內部 filter logic,non-architectural per H1)
- F3.B.1 W38+ 候選 promotion per F2 outcome(documented retro §W38+ Priority Queue Locked)
- F3.B.2 PC-W33-1 + PC-W32-1/2 保留低優先級
- F3.B.3 8 個 pre-existing ruff issues 喺 runner files(W33-W35 寫 runner 留底)保留 LOW
- F3.B.4 Q14 SME-validate reference_answer cascade(`eval-set-v1-final.yaml` W15 F1 CO ship)— LONG-TERM
- F3.B.5 W35 DEMOTED LOW 候選 仍 LOW + path (a) judge LLM 升級 永久 OUT per memory feedback_judge_llm_cost_policy.md
- F3.B.6 長期 carry-over(c)(e)(f)/BUG-026+027/W22 D8/W16 F1-F4 Track A IT cred 維持
- F3.C.1 F3 收尾 commit `docs(planning): W37 closeout — (j') section_path prefix filter ship + quality-of-cite refinement <outcome verdict>`
- F3.C.2 push origin/main confirmed

---

## §3 Acceptance Criteria + Phase Gate

### G1a — Production behavior non-regression(MUST PASS)
- G1a.1 backend pytest 1091 ≥ W36 baseline 1086(+5 NEW W37 tests)
- G1a.2 ruff PASS(W37 specific edits)
- G1a.3 mypy strict 維持(W37 specific edits)
- G1a.4 F2 5-run I07 citation_count avg ≥ W35 baseline 4.8(non-regression)
- G1a.5 F2 5-run I07 refusals 0/5(W32 (h') G1 saturated 100% MUST preserve)

### G1b — Same-section quality signal(per W34 retro framing「independent axis from G1/G2 measurement」)
- G1b.1 **GOAL**:F2 5-run I07 `cross_section_drift_count` avg ≤ 1(W33 Run 1/3/4 mix evidence baseline)
- G1b.2 **STRETCH**:F2 5-run I07 `cross_section_drift_count` = 0 across all runs(ideal — production flip default depth=1 trigger)

### G2 — Control I01 non-regression(MUST PASS)
- G2.1 refusals 0/5
- G2.2 avg_cit ≥ 3.5(W35 baseline 5.4)

### G3 — R6 verify
- G3.1 Day 0 4 catches surfaced
- G3.2 Day 1 active flip recursive verify net 0 contamination

### G4 — 跨文件 R3 + R5 + R6 sync
- G4.1 plan.md changelog entry per phase flip
- G4.2 session-start.md §10 W37 row update
- G4.3 R5 — 無 NEW ADR(per H1 non-architectural)

### 3 outcome decision matrix

| 結果 | 判決 | 處置 |
|---|---|---|
| **(a)** G1a MAINTAIN + G1b drift = 0(stretch met) + G2 PASS | **PASS — production flip candidate** | Settings default `citation_expansion_section_path_prefix_depth=0 → 1` 留 W38+ separate decision(per Q4 measurement-experiment-fail-policy + W26 PC1 一次只郁一個旋鈕 — flip 屬另一 phase)|
| **(b)** G1a MAINTAIN + G1b drift > 0 ≤ 1(goal met) + G2 PASS | **PARTIAL — preserve default 0** | Settings default preserve OFF,W37 F1 infrastructure preserved,W38+ candidate tune depth=2 OR cap mechanism |
| **(c)** G1a regress OR G2 regress(refusals > 0 OR avg_cit < 3.5) | **FAIL — full revert** per Karpathy §1.3 surgical + Q4 measurement-experiment-fail-policy(W30 + W31 + W35 precedent)|

---

## §4 Risks + Mitigations

| Risk | Severity | Mitigation |
|---|---|---|
| **R-W37-1** (j') filter 太 aggressive,過濾掉 valid cross-section walkthrough(e.g. §8.1 introduction 提到 §3.2 setup prerequisite — neighbor §3.2 chunk legitimately related)| Medium | depth=0 default preserve;F2 ONLY temporary `.env` override 驗證;F3 closeout 移除 marker;production flip 留 W38+ separate decision |
| **R-W37-2** `section_path` field 喺某啲 chunks empty / malformed → defensive skip 變相 disable filter | Low | F1.3.e unit test `test_w37_malformed_section_path_field_skipped_defensive` 已 cover;F2 用真實 LIVE corpus 驗證 W17 ingestion section_path 落 chunk index 正常 |
| **R-W37-3** depth=1 (top-level) 對 single-doc KB 無實際過濾效果(全部 chunks share `section_path[0]="Doc"`)| Medium | F1.3.c unit test 已 demonstrate;F2 用 depth=2 override(top + sub-level)— per F1.3.d test pattern;若 F2 G1b ≤ 1 即生效。Production flip 候選 depth=2 |
| **R-W37-4** Backend reload 唔生效(PC-W32-1 `api/server.py:357` no `reload=True`)→ F2 stale-code wasted iter pattern(W32 F2 iter 1 trap)| Low | F2.1.c explicit backend kill + restart per W32 lesson;runner 加 `assert citation_expansion_section_path_prefix_depth_loaded_count > 0` Langfuse event check pre-run |
| **R-W37-5** W26 parent_doc_retriever 共用 section_path 機制可能 confuse — naming convention overlap | Low | catch (3) 已 mitigate via 獨立 namespace `citation_expansion_section_path_prefix_depth`(NOT `parent_doc_section_path_*`);plan §1 + progress.md Day 0 明確區分用途 |

---

## §5 Dependencies + 風險矩陣

### Hard dependencies(必須 satisfied 先 ship)
- ✅ W32 (h') `citation_expansion.py` module 已 ship `e9bd188`
- ✅ W32 F1.8 `expand_citations` 3-tuple return + `neighbor_chunks` materialize(W37 propagate same chain)
- ✅ W17 ingestion `section_path` Azure Search filterable per architecture.md §3.6 line 364
- ✅ W36 PC-W34-1 ship — CLAUDE.md §10.3 step 5b pre-flight endpoint health check(F2.1 prerequisite)
- ✅ W36 PC-W35-1 ship — runner cp1252 fix(F2 runner script 複用 W35 F2 pattern)

### Soft dependencies(non-blocking)
- ⚠️ PC-W32-1(backend no reload=True)— F2 必須 explicit kill+restart
- ⚠️ W26 PC1(「一次只郁一個旋鈕」)— W37 single-axis ship,production flip default 留 W38+

### 風險組合矩陣
- **若 R-W37-3 + R-W37-4 同時 trigger** → F2 G1b 結果 inconclusive(filter 形 implement 但實際冇 effect)→ Phase Gate 必須 PARTIAL revert preserve(per outcome (b))避免 false PASS

---

## §6 Changelog

### 2026-05-27 D0 — F0 啟動
- Plan + checklist + progress 起草
- R6 Day 0 4 catches surfaced(`fetch_chunks_by_section_path` primitive 已存在 W26 / `_find_neighbour_chunks` 只用 §X.M regex / Settings.py 4 處 section_path 屬 W26 parent-doc 用途 / `list_chunks` return 已含 section_path field)
- F0.6 commit `65694d6` ship
- F0.7 session-start.md §10 W37 row append `🟡 active 2026-05-27` commit `6cdece6`

### 2026-05-27 D1 — F1 implementation
- Settings NEW knob `citation_expansion_section_path_prefix_depth: int = 0` ship
- `_find_neighbour_chunks` signature 加 `cited_section_path` + `section_path_prefix_depth` 2 keyword-only params + 9-行 filter block
- `expand_citations` 3-tuple propagation
- 5 NEW unit tests + 2 helper extensions PASS
- F1 commit `da557ab`:backend pytest 1086 → **1091 passed** + ruff PASS + mypy strict W37 files clean

### 2026-05-27 D1 cont — F2 LIVE 5+5 run + F3 closeout PARTIAL revert
- F2.1 pre-flight Langfuse 200 + Postgres SELECT 1 PASS
- F2.2 `.env` temporary override `CITATION_EXPANSION_SECTION_PATH_PREFIX_DEPTH=2` + backend restart
- F2.3 5+5=10 LIVE runs Q-W25-I07 + Q-W25-I01
- **Phase Gate FAIL outcome (c)** per plan §3:G1a strict FAIL(I07 avg_cit 1.8 vs W35 baseline 4.8,-63%)+ G2 control FAIL(I01 avg_cit 2.8 vs W35 baseline 5.4,-48%)+ G1b goal PASS(I07 avg_drift 0.75 ≤ 1.0)
- **真正 root cause shift surfaced**(Karpathy §1.1):I07 Run 2/4 cited cross-section §11 / §8.4 chunks**唔係**`_find_neighbour_chunks` expansion 加入,而係 **reranker top-K 直接 surface** — W37 F1 filter 只能 work on `_find_neighbour_chunks` candidates,reranker-introduced cross-section citations **unfiltered by design**;`\b\d+\.\d+\b` regex + depth=2 雙重 filter 過於 conservative,99% candidates 被 over-filtered → cit count crash
- **PARTIAL revert per Chris pick**(per W31 PC-W31-2 + W27 F1 precedent):`.env` marker block removed,production behavior 100% revert W36 baseline(Settings default=0 已 preserve);F1 production code(Settings knob + signature + filter block + 5 unit tests)preserved as W38+ enabler — G1b goal PASS 證明 filter 有 work,bottleneck 在 reranker layer not citation_expansion layer

---

## §7 Schedule Estimate

| Phase | 預估 | 累積 |
|---|---|---|
| F0 啟動(plan + checklist + progress + R6 verify + 啟動 commit + session-start sync) | 30min | 30min |
| F1 Settings + `_find_neighbour_chunks` filter + 5 NEW unit tests + commit | 1h | 1h 30min |
| F2 Pre-flight + `.env` temporary override + backend restart + 5+5 runs + decision tree intersect | 30-45min | 2h - 2h 15min |
| F3 收尾 + 跨文件同步 + commit + push | 30min | 2h 30min - 2h 45min |

**Total**:**~2.5-2.75h**(MEDIUM phase 評估)。Real-calendar collapse 預期 within range(W36 ~4.5h vs 5-6h planned + W35 ~5.5h within 4-6h range pattern)。

---

**End of W37 plan.md**
