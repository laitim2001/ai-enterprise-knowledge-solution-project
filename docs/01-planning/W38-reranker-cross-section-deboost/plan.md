---
phase: W38-reranker-cross-section-deboost
status: closed_partial   # F4 收尾 2026-05-27 — F1 LOW housekeeping ship + F2 reranker deboost infrastructure ship + F3 LIVE BLOCKED by Azure AI Search 402 Payment Required environmental issue(per ADR-0017 R8 pattern,W17 F1.5b+F3.5b precedent)— deferred W39+ separate phase trigger after Azure billing resolved
last_updated: 2026-05-27
component_scope: C04 Retrieval Engine(F2 reranker post-rerank cross-section deboost — symmetric pattern per ADR-0035)+ C07 Observability + C12 DevOps(F1 housekeeping ruff cleanup + PC-W32-1/2 documentation + PC-W33-1 reconcile)
adr_refs:
  - W37 progress.md retro §root cause shift — reranker layer cross-section surfacing (real bottleneck per F2 evidence not citation_expansion layer)
  - ADR-0035 W25 F5 D2 — symmetric deboost pattern reference (multiply rerank_score by deboost factor preserving evidence)
  - W36 retro — operational debt batch precedent (atomic batch cleanup procedural/config/tooling)
  - W32 (h') ADR — citation_expansion engine-fetch module precedent (Settings knob + signature additive params + observability log fields)
  - W31 PC-W31-2 — evidence preservation policy (failed experiments leave infrastructure as enabler for next phase)
  - W26 PC1 — 一次只郁一個旋鈕 (deboost default=1.0 disabled,F3 LIVE override only)
related_carry_overs:
  - W37 retro §W38+ HIGHEST NEW — reranker-side cross-section filter pivot,W38 兌現
  - W36 batch precedent — operational debt cleanup pattern reused for F1 housekeeping
  - W34 PC-W34-1+PC-W34-2 + W35 PC-W35-1 — RESOLVED via W36 ship,W38 F1 reconcile any remaining (PC-W32-1 + PC-W32-2 + PC-W33-1 reconcile)
  - W33-W35 留底 8 個 pre-existing ruff issues + W37 F2 runner 4 新增 = 13 total fix
---

# W38 — Reranker Cross-Section Deboost + LOW Housekeeping Batch

## §1 目標 + 範疇

**雙目標 atomic batch**(per W36 precedent + Karpathy §1.3 surgical separation,housekeeping 先做 clean baseline 後 LIVE eval attribution clean):

### F1 LOW housekeeping(procedural,non-production behavior change)
- F1.1 Ruff `--fix` apply — 13 個 issues(1 F401 + 1 F841 + 11 F541 = 12 fixable + 1 hidden)
- F1.2 PC-W32-1 documentation — `api/server.py:357` no `reload=True` rationale 文檔化(WatchFiles auto-reload vs explicit kill+restart discipline tradeoff;decision = preserve current pattern per BUG-008 Windows ProactorEventLoop fix)
- F1.3 PC-W32-2 documentation — citation enrichment integration pattern lesson(future module-level changes affecting citation pipeline must explicitly propagate via SynthesisResult fields)
- F1.4 PC-W33-1 status reconcile — already covered by W36 PC-W34-1 ship per `CLAUDE.md §10.3` line 533「per PC-W33-1 + PC-W34-1」evidence;Azurite extension OPTIONAL additive deferred(image storage non-eval-pipeline-critical)

### F2 Reranker cross-section deboost implementation(C04 internal algorithm change)
- F2.1 Settings 2 NEW knobs:
  - `reranker_cross_section_deboost: float = 1.0`(disabled,1.0 = no-op)
  - `reranker_section_path_prefix_depth: int = 2`(top + sub-level match required when active)
- F2.2 `retrieval/retrieval_engine.py:151-166` post-rerank loop enhancement(symmetric deboost per W25 ADR-0035 pattern;唔 hard filter per W37 F1 -63% precedent)
- F2.3 4-5 NEW unit tests covering disabled default / deboost applied / same-section preserved / re-sort verify / malformed defensive

### F3 LIVE 5+5 verification(`.env` temporary override only)
- F3.1 Pre-flight per `CLAUDE.md §10.3` step 5b(W36 PC-W34-1 ship)
- F3.2 `.env` temp override `RERANKER_CROSS_SECTION_DEBOOST=0.85` + `RERANKER_SECTION_PATH_PREFIX_DEPTH=2`
- F3.3 Backend explicit kill + restart(per PC-W32-1 no `reload=True`)
- F3.4 `backend/w38-f3-runner.py` — 5 runs Q-W25-I07 + 5 runs Q-W25-I01 control + NEW nuanced drift metric(distinguish valid hierarchical zoom-in vs real cross-section drift)
- F3.5 Decision tree intersect — outcome (a) / (b) / (c) per plan §3

**Karpathy §1.3 surgical scope 嚴守**:
- F1 純 procedural / documentation,no production behavior change
- F2 Settings default=1.0 disabled = production behavior preserve W37 baseline(`.env` override 只 F3 LIVE test 用,F4 closeout 移除)
- 唔 fix `api/server.py:357` reload=True(避免 BUG-008 Windows ProactorEventLoop regression risk)

**Non-goals**(W38 範疇外):
- 任何 vendor / API contract / public interface change(Cohere v4.0-pro 維持)
- W37 F1 `_find_neighbour_chunks` 第二輪 tune(preserved as W39+ enabler depth=1 OR cap mechanism)
- Q14 SME-validate `reference_answer` cascade — LONG-TERM non-AI bottleneck
- Enumeration query architectural mismatch research(Tier 2 boundary review trigger)— LONG-TERM stakeholder governance

**Component 範疇**:
- **C04 Retrieval Engine**(F2 `retrieval/retrieval_engine.py` post-rerank loop enhancement)
- **C07 Observability**(F1.1 ruff cleanup runner files tooling)
- **C12 DevOps**(F1.2-F1.4 procedural documentation)
- **不涉及** C01-C03 / C05-C06 / C08-C13(無 ingestion / generation / KB / auth / eval / frontend 改動)

---

## §2 交付物 F0-F4

### F0 — 啟動(本 session 2026-05-27)

- F0.1 建立 `docs/01-planning/W38-reranker-cross-section-deboost/` folder
- F0.2 R6 Day 0 recursive grep 驗證 — **catch (1)** `retrieval_engine.py:151-166` post-rerank insertion point confirmed(Cohere v4.0-pro `reranked_chunks` shape preserves `section_path` field;client-side modification only);**catch (2)** W37 drift metric over-flagged hierarchical zoom-in as drift(Run 4「8.4 Scenario D」屬 §8 family valid zoom NOT cross-section);**catch (3)** I01 control 多 section drift 屬 query nature(「what is high level architecture」覆蓋 §1+§3+§4 summary)NOT bug — W38 F3 metric 需 nuanced distinguish;**catch (4)** Ruff 13 issues(9 W33-W35 留底 + 4 W37 F2 runner)— 比 W37 estimate「8」多 5 個(W37 F2 runner contribution 漏算);**catch (5)** PC-W33-1 已 implicitly resolved by W36 PC-W34-1 ship per `CLAUDE.md §10.3` line 533 cite — W38 F1.4 純 status reconcile;**catch (6)** `api/server.py:343-360` Server.serve() pattern(BUG-008 Windows ProactorEventLoop fix)— `reload=True` 加可能 break SelectorEventLoop factory(asyncio_loop_factory 同 reload mode 互動未測試)— W38 F1.2 decision = preserve current pattern + document rationale
- F0.3 起草 `plan.md`(本文件)
- F0.4 起草 `checklist.md` 原子化勾選項
- F0.5 起草 `progress.md` Day 0 — 啟動行動 + R6 6 catches 報告 + F-phase pre-implementation surface
- F0.6 啟動 commit `docs(planning): kickoff W38-reranker-cross-section-deboost + R6 Day 0 6 catches surface reranker filter insertion point + W37 drift metric over-flag + nuanced design`
- F0.7 session-start.md §10 W38 row append `🟡 active 2026-05-27` + W38+ → W39+ placeholder rename

### F1 — LOW housekeeping batch(~30min)

- F1.1 `ruff check --fix --unsafe-fixes` on runner files(13 errors → 0)— `backend/w33-f2-runner.py` F401 os + F841 cit_ids + `backend/w34-f1-ragas-runner.py` F541 + `backend/w34-f2-runner.py` F541 × 2 + `backend/w35-f1-ragas-runner.py` F541 + `backend/w35-f2-runner.py` F541 × 3 + `backend/w37-f2-runner.py` F541 × 4 = 12 fixable + 1 hidden
- F1.2 PC-W32-1 documentation — `api/server.py:343-360` comment block 加 W38 amendment rationale(no `reload=True` preserved per BUG-008 Windows ProactorEventLoop fix;auto-reload tradeoff vs explicit kill+restart discipline;W36 PC-W34-1 step 5b protocol covers explicit kill verification path)
- F1.3 PC-W32-2 documentation — `generation/citation_expansion.py` module docstring 加 「integration pattern note」section(W32 F1.8 lesson — module-level changes affecting citation pipeline must explicitly propagate via SynthesisResult fields,build_citations Rule 5 contract preservation)
- F1.4 PC-W33-1 status reconcile — RISK_REGISTER OR session-start.md note PC-W33-1 status flip pending → RESOLVED via W36 PC-W34-1 ship(reference CLAUDE.md §10.3 line 533 cite);Azurite extension deferred non-critical
- F1.5 backend pytest 1091 PASS preserve(F1 唔改 production code);ruff 13 issues → 0 clean
- F1.6 commit `chore(tooling): W38 F1 LOW housekeeping batch — ruff 13 fix + PC-W32-1 reload=True rationale doc + PC-W32-2 citation integration pattern note + PC-W33-1 reconcile resolved-via-W36`

### F2 — Reranker cross-section deboost implementation(~1.5h)

#### F2.1 Settings NEW knobs(`backend/storage/settings.py`)

```python
# W38 — Reranker cross-section deboost (per ADR-0035 W25 symmetric pattern reference;
# post-rerank client-side score multiply,non-architectural per H1).
# 1.0 = disabled (W38 baseline preserve W37 production behavior);
# 0.85 = typical 15% rank penalty for cross-section candidates per W25 ADR-0035 deboost
# magnitude;0.5+ aggressive for strong cross-section drift cases.
# 真正 root cause per W37 F2 evidence — I07 Run 2 cited §11 Execution plan + §11.2 Phase 1
# chunks (cross-section §8 → §11) 由 reranker top-K 直接 surface,unfiltered by W32 (h')
# citation_expansion layer (scope-out by design).
reranker_cross_section_deboost: float = 1.0
# Section_path prefix depth match required when deboost active. 1 = top-level only
# (single-doc KB no-op);2 = top + sub-level required (e.g. ["Doc","§8"] vs ["Doc","§11"]
# = different,deboost triggered);3 = strict subsection (rarely needed).
reranker_section_path_prefix_depth: int = 2
```

#### F2.2 `backend/retrieval/retrieval_engine.py:151-166` post-rerank loop

```python
if do_rerank and hits:
    rerank_start = time.perf_counter()
    reranked_chunks = await self._reranker.rerank(
        query=query, candidates=hits, top_k=top_k,
    )
    # W38 reranker cross-section deboost (post-rerank client-side,H1 non-architectural)
    if self._settings.reranker_cross_section_deboost < 1.0 and reranked_chunks:
        anchor_sp = reranked_chunks[0].fields.get("section_path") or []
        depth = self._settings.reranker_section_path_prefix_depth
        anchor_prefix = list(anchor_sp[:depth]) if isinstance(anchor_sp, list) else []
        deboost_count = 0
        for r in reranked_chunks:
            cand_sp = r.fields.get("section_path") or []
            if not isinstance(cand_sp, list):
                continue  # malformed → defensive skip (preserve rank)
            cand_prefix = list(cand_sp[:depth])
            if cand_prefix and cand_prefix != anchor_prefix:
                r.rerank_score *= self._settings.reranker_cross_section_deboost
                deboost_count += 1
        # Re-sort post-deboost — preserves rerank_score ordering invariant
        reranked_chunks.sort(key=lambda r: r.rerank_score, reverse=True)
        logger.info(
            "reranker_cross_section_deboost_applied",
            anchor_prefix=anchor_prefix,
            depth=depth,
            deboost_factor=self._settings.reranker_cross_section_deboost,
            deboost_count=deboost_count,
            total_candidates=len(reranked_chunks),
        )
    rerank_latency_ms = int((time.perf_counter() - rerank_start) * 1000)
    chunks = [
        RetrievedChunk(score=r.rerank_score, fields=r.fields)
        for r in reranked_chunks
    ]
    reranked = True
```

#### F2.3 NEW unit tests(`backend/tests/test_retrieval_engine.py` OR NEW test file)

- F2.3.a `test_w38_reranker_deboost_disabled_default_no_op`(deboost=1.0 → 行為 unchanged W37 baseline)
- F2.3.b `test_w38_reranker_deboost_cross_section_score_reduced`(深度 2,anchor ["Doc","§8"] + 候選 ["Doc","§11"] → score × 0.85)
- F2.3.c `test_w38_reranker_deboost_same_section_preserved`(anchor ["Doc","§8"] + 候選 ["Doc","§8","§8.4"] hierarchical zoom-in → score 不變)
- F2.3.d `test_w38_reranker_deboost_re_sort_invariant`(deboost 後 sort 確認 rank_score descending)
- F2.3.e `test_w38_reranker_deboost_malformed_section_path_defensive`(候選 `section_path` 不是 list → 跳過 preserve rank)

#### F2.4 驗證 + commit

- F2.4.a backend pytest 1091 → 1096(+5 NEW W38 tests minimum)+ ruff PASS + mypy strict W38 files clean
- F2.4.b commit `feat(retrieval): W38 F2 reranker post-rerank cross-section deboost — symmetric pattern per ADR-0035 + Settings 2 NEW knobs + 5 NEW unit tests + observability log`

### F3 — LIVE 5+5 verification(~1h)

#### F3.1 Pre-flight per CLAUDE.md §10.3 step 5b(W36 PC-W34-1 ship)

- F3.1.a `Invoke-WebRequest -Uri http://localhost:3000/api/public/health -TimeoutSec 30`(預期 200 — Langfuse)
- F3.1.b `docker exec ekp-postgres psql -U langfuse -d postgres -c "SELECT 1;"`(預期 `1 row` ready_for_query)

#### F3.2 `.env` temporary override

- F3.2.a `.env` 加 marker block `# --- W38 F3 TEMPORARY override 2026-05-27 — reranker cross-section deboost LIVE test ---`
- F3.2.b `RERANKER_CROSS_SECTION_DEBOOST=0.85`(typical 15% rank penalty per ADR-0035)
- F3.2.c `RERANKER_SECTION_PATH_PREFIX_DEPTH=2`(top + sub-level)
- F3.2.d F4 closeout 移除 marker block per W27/W29 pattern

#### F3.3 Backend explicit kill + restart(per PC-W32-1)

- F3.3.a Kill existing uvicorn process(`Stop-Process -Id <PID> -Force`)
- F3.3.b Restart `python -m api.server`(per ADR-0023 + `api/server.py:343` SelectorEventLoop fix)
- F3.3.c Verify `/health` 200 + Settings override loaded(via Langfuse trace `reranker_cross_section_deboost_applied` event firing post-first-query)

#### F3.4 5+5 LIVE runs + nuanced drift metric

- F3.4.a `backend/w38-f3-runner.py` — 5 runs Q-W25-I07 + 5 runs Q-W25-I01 control
- F3.4.b **NEW nuanced drift metric**(per F0.2 catch (2)+(3)— W37 raw drift over-flagged hierarchical zoom-in):
  - `real_cross_section_drift_count` = count of citations whose top-level section_path[0] differs from anchor's section_path[0](hierarchical zoom-in 屬同 top-level NOT drift)
  - `valid_hierarchical_zoom_count` = count of citations whose section_path 屬 anchor's section family deeper level(e.g. anchor "§8" + candidate "§8.4")
- F3.4.c Aggregate per-run + W37 vs W38 cross-comparison

#### F3.5 Decision tree intersect

- F3.5.a **G1a strict** — refusals 0/5 + I07 avg_cit ≥ 4.8(W35 maintain)
- F3.5.b **G1b real drift reduce** — I07 `real_cross_section_drift_count` reduce vs W37 baseline(specifically Run 2 §11 case)
- F3.5.c **G2 control** — I01 refusals 0/5 + avg_cit ≥ 3.5(I01 multi-section query nature NOT flag as bug)
- F3.5.d **G3 latency** — within W35 +20% budget(deboost re-sort overhead minimal,預期 < 10ms)
- F3.5.e **G4 R6 6 catches** verified at Day 0 + Day 1 active flip
- F3.5.f **G5 pytest 1096+ + ruff PASS + mypy strict** preserve
- F3.5.g Decide outcome — (a) PASS / (b) PARTIAL / (c) FAIL

### F4 — 收尾 + 跨文件同步 + commit + push(~30min)

- F4.A.1 plan.md frontmatter `status: active → closed_partial OR closed`(F4 commit time per outcome)
- F4.A.2 checklist.md cross-cutting tick + N/A reason
- F4.A.3 progress.md retro 7 段(What Worked / What Didn't / Carry-overs / ADR Triggers / Phase Gate Result / W39+ Priority Queue Locked / Actual vs Planned Effort)
- F4.A.4 session-start.md §10 W38 row `🟡 active` → `✅ closed`(F4 commit time)
- F4.A.5 `.env` 移除 W38 F3 marker block(per W27/W29 pattern;production preserve default 1.0)
- F4.A.6 🚧 RISK_REGISTER NEW R 候選 — DEFERRED W39+ OR N/A per F3 outcome
- F4.A.7 ADR README — 無 NEW ADR(F1+F2 純 internal logic / procedural,non-architectural per H1)
- F4.B.1 W39+ 候選 promotion per F3 outcome
- F4.B.2 W37 F1 infrastructure preserved enabler 維持(`_find_neighbour_chunks` section_path filter)
- F4.B.3 `\b\d+\.\d+\b` regex relax 維持 MEDIUM
- F4.B.4 Q14 SME-validate reference_answer cascade — LONG-TERM
- F4.B.5 8 個 pre-existing ruff issues NOW RESOLVED via F1.1(updated W39+ queue)
- F4.B.6 PC-W33-1 + PC-W32-1/2 status reconciled F1.2-F1.4
- F4.C.1 F4 收尾 commit
- F4.C.2 push origin/main confirmed

---

## §3 Acceptance Criteria + Phase Gate

### G1a — Production behavior non-regression(MUST PASS)
- G1a.1 backend pytest 1096+ ≥ W37 baseline 1091(+5 NEW W38 tests)
- G1a.2 ruff PASS(W38 specific edits + F1.1 housekeeping 13 → 0)
- G1a.3 mypy strict 維持(W38 specific edits)
- G1a.4 F3 5-run I07 citation_count avg ≥ W35 baseline 4.8(non-regression)
- G1a.5 F3 5-run I07 refusals 0/5(W32 (h') G1 saturated 100% MUST preserve)

### G1b — Real cross-section drift signal reduce(per W37 retro framing)
- G1b.1 **GOAL**:F3 5-run I07 `real_cross_section_drift_count` ≤ 1 across runs(reduce vs W37 Run 2 §11 case)
- G1b.2 **STRETCH**:F3 5-run I07 `real_cross_section_drift_count` = 0(no §11 / §3 alongside §8;hierarchical zoom-in still kept)

### G2 — Control I01 non-regression(MUST PASS)
- G2.1 refusals 0/5
- G2.2 avg_cit ≥ 3.5(W35 baseline 5.4 — deboost 唔 hard filter,保留 multi-section evidence by query nature)
- G2.3 I01 多 section 由 query nature 觸發 — W38 metric **不** flag as bug(per F0.2 catch (3) corrected)

### G3 — Latency budget
- G3.1 F3 5-run avg latency within W35 +20% budget(deboost re-sort overhead < 10ms expected)

### G4 — R6 verify
- G4.1 Day 0 6 catches surfaced
- G4.2 Day 1 active flip recursive verify net 0 contamination

### G5 — 跨文件 R3 + R5 + R6 sync
- G5.1 plan.md changelog entry per phase flip
- G5.2 session-start.md §10 W38 row update
- G5.3 R5 — 無 NEW ADR(per H1 non-architectural)

### 3 outcome decision matrix

| 結果 | 判決 | 處置 |
|---|---|---|
| **(a)** G1a MAINTAIN + G1b real drift reduce(goal met) + G2 PASS | **PASS — production flip candidate** | Settings default `reranker_cross_section_deboost=1.0 → 0.85` 留 W39+ separate flip decision(per Q4 measurement-experiment-fail-policy + W26 PC1)|
| **(b)** G1a MAINTAIN + G1b partial reduce + G2 PASS | **PARTIAL — preserve default 1.0**(disabled)| F2 infrastructure preserved as W39+ enabler,W39+ tune depth OR deboost factor |
| **(c)** G1a regress OR G2 regress(I07 refusals > 0 OR avg_cit < 4.8 OR I01 refusals > 0) | **FAIL — full revert** per Karpathy §1.3 surgical + Q4 measurement-experiment-fail-policy(W30 + W31 + W37 precedent)|

---

## §4 Risks + Mitigations

| Risk | Severity | Mitigation |
|---|---|---|
| **R-W38-1** Deboost factor 0.85 太溫和,真正 cross-section drift(I07 Run 2 §11)仍 surface | Medium | F2 Settings knob flexibility — F4 closeout 之後 W39+ tune 至 0.5 OR 0.6 if F3 G1b partial PASS;Symmetric deboost approach 風險 lower than W37 hard filter |
| **R-W38-2** Deboost factor 0.85 過 aggressive,有用 cross-section context(I01 multi-section query nature)被 deprioritized | Medium | G2 control measure I01 refusals + avg_cit;若 G2 break 則 F3 FAIL outcome (c) full revert;default 1.0 disabled 安全 |
| **R-W38-3** Re-sort 後 rank order change 影響 build_citations downstream(Rule 5 contract)| Low | Re-sort 保留 `rerank_score` semantic invariance(descending);build_citations 預期 top-K by rerank_score(`citations 順序變化但 valid set 不變`);F2.3.d 已 cover unit test |
| **R-W38-4** Backend restart 又 hit ghost-Python-3.12 issue(W37 F3 precedent)| Low | F3.3 explicit kill PID via `Get-WmiObject Win32_Process` 識別 CommandLine 後 Stop-Process;preserve PowerShell-side工作 dir absolute path |
| **R-W38-5** F1.1 ruff `--unsafe-fixes` 改錯 logic(W37 F2 runner 5 F541 issues)| Low | Manual review post-fix(`git diff` before commit)+ pytest preserve;F541 = f-string without placeholders,純 cosmetic 不會改 logic |

---

## §5 Dependencies + 風險矩陣

### Hard dependencies(必須 satisfied 先 ship)
- ✅ W32 (h') `citation_expansion.py` ship `e9bd188`
- ✅ W33 Rule 7 v2 + Rule 8 ship `149aebd`
- ✅ W35 Option C `prompt_builder.py:30` ship `b2f4ca3...c590a86`
- ✅ W36 PC-W34-1 `CLAUDE.md §10.3 step 5b` ship `3f65531`
- ✅ W36 PC-W35-1 runner cp1252 fix ship `5520918`
- ✅ W37 F1 `_find_neighbour_chunks` section_path filter infrastructure ship `da557ab`(preserved as W39+ enabler)
- ✅ ADR-0035 W25 F5 D2 symmetric deboost pattern reference

### Soft dependencies(non-blocking)
- ⚠️ PC-W32-1(backend no reload=True)— F3 必須 explicit kill+restart per ADR-0023 + Server.serve() Windows fix
- ⚠️ W26 PC1(「一次只郁一個旋鈕」)— W38 single-axis ship deboost factor 0.85,W39+ tune separate phase

---

## §6 Changelog

### 2026-05-27 D0 — F0 啟動
- Plan + checklist + progress 起草
- R6 Day 0 6 catches surfaced
- F0.6 commit `693d463`
- F0.7 session-start.md §10 W38 row append `🟡 active 2026-05-27` commit `d853dbc`

### 2026-05-27 D1 — F1 LOW housekeeping batch ship
- F1.1 Ruff `--fix --unsafe-fixes` apply — 13 errors → 0 fixed clean(9 W33-W35 留底 + 4 W37 F2 runner)
- F1.2 `api/server.py:343-360` PC-W32-1 documentation 加 W38 amendment note(preserve no `reload=True` rationale + WatchFiles subprocess vs BUG-008 SelectorEventLoop tradeoff)
- F1.3 `citation_expansion.py` PC-W32-2 integration pattern note 加入 module docstring(W32 F1.8 lesson)
- F1.4 PC-W33-1 status reconcile RESOLVED via W36 PC-W34-1 ship(per CLAUDE.md §10.3 line 533 cite evidence)
- F1.5 backend pytest 1091 preserve PASS + ruff clean
- F1.6 commit `74ad872`

### 2026-05-27 D1 cont — F2 Reranker deboost infrastructure ship
- F2.1 Settings 2 NEW knobs ship — `reranker_cross_section_deboost: float = 1.0`(disabled default)+ `reranker_section_path_prefix_depth: int = 2`
- F2.2 `retrieval_engine.py:158-200` post-rerank deboost loop ship — RerankedChunk frozen rebuild pattern + re-sort + defensive malformed skip + observability log
- F2.3 5 NEW unit tests PASS — disabled no-op / cross-section reduced / same-section preserved / re-sort invariant / malformed defensive
- F2.4 backend pytest 1091 → 1096 + ruff PASS + mypy strict W38 self-clean
- F2 commit `cea024f`

### 2026-05-27 D1 cont — F3 LIVE BLOCKED by Azure AI Search 402 Payment Required
- F3.1 pre-flight PASS — Langfuse 200 + Postgres SELECT 1 ready_for_query
- F3.2 `.env` temp override `RERANKER_CROSS_SECTION_DEBOOST=0.85` + `RERANKER_SECTION_PATH_PREFIX_DEPTH=2`(112 → 116 lines)
- F3.3 Backend explicit kill (PID 7512 via WMI CommandLine filter) + restart PID 7512 — backend `/health` 200 OK
- F3.4 W38 F3 runner 5+5 LIVE runs — **全 10 runs HTTP 502** — direct curl test 揭示 root cause:`pipeline.retrieval_failed` 由 Azure AI Search `402 Payment Required` 引發(retrieval layer 直接 fail at Azure Search call,根本未到 reranker / W38 F2 deboost logic)
- **Phase Gate INCONCLUSIVE per ADR-0017 R8 environmental block precedent** — W17 F1.5b Postgres-path runtime smoke + F3.5b RAGAs live-verify 同樣 R8-blocked 留 W18+/CO17 pattern reused
- F4 closeout PARTIAL per Chris pick:`.env` marker block removed,production preserve default 1.0 disabled;F2 infrastructure preserved as W39+ enabler trigger after Azure billing resolved
- F4 commit pending

---

## §7 Schedule Estimate

| Phase | 預估 | 累積 |
|---|---|---|
| F0 啟動(plan + checklist + progress + R6 verify + 啟動 commit + session-start sync) | 30min | 30min |
| F1 housekeeping batch(ruff fix + PC-W32-1/2 doc + PC-W33-1 reconcile + commit) | 30min | 1h |
| F2 Settings knobs + retrieval_engine.py post-rerank loop + 5 NEW unit tests + commit | 1.5h | 2.5h |
| F3 Pre-flight + `.env` override + backend restart + 5+5 runs + decision tree intersect | 1h | 3.5h |
| F4 收尾 + 跨文件同步 + commit + push | 30min | 4h |

**Total**:**~4h**(MEDIUM-HIGHEST phase 評估)。Real-calendar collapse 預期 within range(W36 ~4.5h vs 5-6h planned + W37 ~2.5h within 2.5-2.75h range pattern)。

---

**End of W38 plan.md**
