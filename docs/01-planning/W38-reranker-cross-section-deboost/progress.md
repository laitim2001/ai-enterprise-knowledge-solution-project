---
phase: W38-reranker-cross-section-deboost
plan_ref: ./plan.md
checklist_ref: ./checklist.md
status: closed_partial   # F4 收尾 2026-05-27 — F1+F2 ship + F3 LIVE Azure 402 BLOCKED per ADR-0017 R8 environmental block(W17 F1.5b/F3.5b precedent)
last_updated: 2026-05-27
---

# W38 — Progress Log

## Day 0 — 2026-05-27 — F0 啟動

### 啟動行動

- ✅ F0.1 建立 `docs/01-planning/W38-reranker-cross-section-deboost/` folder
- ✅ F0.2 R6 Day 0 recursive grep 驗證 — 6 catches surfaced(per below)
- ✅ F0.3 起草 `plan.md` 7 段
- ✅ F0.4 起草 `checklist.md` 原子化勾選項
- ✅ F0.5 起草 `progress.md` Day 0(本 entry)
- ⏳ F0.6 啟動 commit pending
- ⏳ F0.7 session-start.md §10 W38 row append pending

### R6 Day 0 6 catches 報告

#### catch (1) — `retrieval_engine.py:151-166` post-rerank insertion point confirmed

**Evidence**:
```python
# backend/retrieval/retrieval_engine.py line 151-166
if do_rerank and hits:
    rerank_start = time.perf_counter()
    reranked_chunks = await self._reranker.rerank(
        query=query, candidates=hits, top_k=top_k,
    )
    rerank_latency_ms = int((time.perf_counter() - rerank_start) * 1000)
    chunks = [
        RetrievedChunk(score=r.rerank_score, fields=r.fields)
        for r in reranked_chunks
    ]
    reranked = True
```

**Implication**:
- ✅ Cohere v4.0-pro `reranked_chunks` 已 return `section_path` field(per W17 schema)— W38 implementation 純內部 score multiply,no API contract change
- W38 F2 insertion point clear:`rerank_start = time.perf_counter()` 之後 `rerank_latency_ms` 計算之前
- H1 non-architectural confirmed(post-rerank client-side score modification only)

#### catch (2) — W37 drift metric over-flagged hierarchical zoom-in as drift

**Evidence**(W37 F2 Run 4 raw data):
- chunk 1: sp=['8. Integration scenarios (end-to-end walkthroughs)']
- chunk 2: sp=['8. Integration scenarios (end-to-end walkthroughs)', '8.4 Scenario D — MPS device service alert ...']

W37 runner `_section_prefix(sp, depth=2)` 第二級唔同(`('8.', '8.4')` vs `('8.',)` ),raw count drift=1。**但實際係 valid hierarchical zoom-in,NOT cross-section drift**(都屬 §8 family)。

**Implication**:
- W38 F3 runner 需 **nuanced drift metric** distinguish:
  - `real_cross_section_drift_count` = top-level section[0] 唔同(e.g. §8 vs §11)— W38 真正要 reduce
  - `valid_hierarchical_zoom_count` = top-level section[0] 相同但 deeper level 唔同(e.g. §8 vs §8.4)— **不算 drift**
- W37 F2 真正 cross-section bug 只喺 Run 2(§8 + §11.x)= 1/4 valid runs,非 75% raw drift rate

#### catch (3) — I01 control 多 section drift 屬 query nature NOT bug

**Evidence**(W37 F2 Run 2 I01 raw data):
- chunk 1: sp=['1. Executive summary']
- chunk 2: sp=['4. High-level architecture', '4.1 Component overview']
- chunk 3: sp=['4. High-level architecture', '4.1 Component overview']
- chunk 4: sp=['3. Architectural principles', '3.1 Platform composition over platform construction']

**Implication**:
- 「what is high level architecture」query 本身需要 summary across §1 Executive + §3 Principles + §4 Architecture(non-bug multi-section)
- I01 高 drift count NOT actually cross-section drift — W38 deboost approach **唔可以** hard filter cross-section(否則 I01 break)
- 確認 symmetric deboost approach 正確(per W25 ADR-0035)NOT hard filter(per W37 F1 -63% precedent)

#### catch (4) — Ruff 13 issues(超 W37 estimate 8 by 5)

**Evidence**:
```
F401 [*] `os` imported but unused      w33-f2-runner.py:9          (1)
F841 Local variable `cit_ids` unused   w33-f2-runner.py:60         (1)
F541 [*] f-string no placeholders      w34-f1-ragas-runner.py:50   (1)
F541 [*]                               w34-f2-runner.py:96,97      (2)
F541 [*]                               w35-f1-ragas-runner.py:45   (1)
F541 [*]                               w35-f2-runner.py:111,112,116 (3)
F541 [*]                               w37-f2-runner.py:159,160,161,163 (4)
                                       ─────────────────────────── ───
                                       Total                       13
                                       Fixable                     12 + 1 hidden
```

**Implication**:
- W37 F2 runner 留底 4 個 NEW F541(寫 runner 時 print(f"...") template 但無 variable interpolation)
- W37 retro estimate「8 pre-existing ruff issues」 漏算 W37 自己留底嘅 4 個 = real total 13
- `ruff check --fix --unsafe-fixes` 可一次性 clean 12 + 1 hidden = 13 → 0

#### catch (5) — PC-W33-1 already resolved by W36 PC-W34-1 ship

**Evidence**(`CLAUDE.md §10.3 step 5b` line 533):
> `5b. **若本 session 預期會做 backend restart / eval run / RAGAs eval / Langfuse trace 操作 → 先 pre-flight endpoint health check**(**per PC-W33-1 + PC-W34-1**,W34 F2.3 audit_log 30s gap + W35 F1.3 Docker stuck 經驗驅動)`

**Implication**:
- W36 PC-W34-1 ship 已 cite PC-W33-1 作為 implicit predecessor — step 5b 命名「endpoint health check」covered Langfuse + Postgres
- **Azurite 提及 PC-W33-1 原始 surface 但 NOT in W36 ship** — image storage,non-eval-pipeline-critical(F1.4 status reconcile RESOLVED with optional Azurite extension deferred)
- W38 F1.4 純 status documentation,non-code change

#### catch (6) — `api/server.py:343-360` BUG-008 Windows ProactorEventLoop fix 同 reload=True 互動未測試

**Evidence**(`api/server.py:343-360`):
```python
# ── Server launcher (BUG-008) ──────────────────────────────────────────────
# Run with `python -m api.server` — NOT `python -m uvicorn api.server:app`.
# ...
# uvicorn's `Server.run()` builds its event loop with `loop_factory=
# asyncio.ProactorEventLoop` on Windows — psycopg's async mode rejects ProactorEventLoop.
# So on Windows we bypass `Server.run()` and drive `Server.serve()` through
# `asyncio.run` with an explicit SelectorEventLoop factory.
if __name__ == "__main__":
    _server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=8000))
    if sys.platform == "win32":
        asyncio.run(_server.serve(), loop_factory=asyncio.SelectorEventLoop)
```

**Implication**:
- 加 `reload=True` 入 `uvicorn.Config(...)` 可能 break SelectorEventLoop factory:
  - WatchFiles reload mode 由 uvicorn 內部管理 subprocess,可能不 honor asyncio.run loop_factory override
  - 風險 BUG-008 regression(psycopg async mode reject ProactorEventLoop)
- W38 F1.2 decision = **preserve current pattern**(no `reload=True`);comment block document W36 PC-W34-1 step 5b explicit kill+restart discipline alternative

### W37 evidence reframed(F0.2 catch (2)+(3) Karpathy §1.1 think-before-coding)

| W37 F2 raw metric | W38 真實判讀 | 推論 |
|---|---|---|
| I07 avg_drift 0.75 | Run 2 §11 real cross-section drift = 1/4 = 25%;Run 4 §8.4 valid hierarchical zoom-in 不算 drift | 真實問題 scope 比 W37 raw 估算嘅 75% 細好多 — 真正只 ~25% I07 runs 有 cross-section bug |
| I01 avg_drift 1.60 | Multi-section by query nature(§1 Executive + §3 Principles + §4 Architecture summary)— NOT bug | W38 deboost approach **必須** symmetric(deboost 0.85 = 15% penalty 保留 evidence)NOT hard filter |
| I07 avg_cit 1.8(-63%) | W37 hard filter `\b\d+\.\d+\b` regex + section_path prefix 雙重 over-filter 99% candidates | W38 nuanced approach — 只 deboost candidate 唔斬,保留 top-K 候選池 |
| I07 latency +101% | W37 Run 4 outlier 32s upstream Azure transient,排除後 avg ~21s(W35 baseline ~11.5s) | W38 deboost re-sort 應 <10ms overhead,latency 主要由 LLM emit dominant(W34 F2 evidence 92%)|

### F-phase pre-implementation surface

#### F1 housekeeping execution sequence(~30min total)

```
F1.1 ruff --fix --unsafe-fixes (5 min)
  ↓
F1.2 api/server.py PC-W32-1 comment block (5 min)
  ↓
F1.3 citation_expansion.py PC-W32-2 integration pattern note (5 min)
  ↓
F1.4 PC-W33-1 reconcile documentation (5 min)
  ↓
F1.5 pytest verify 1091 PASS + ruff 13 → 0 (5 min)
  ↓
F1.6 commit (5 min)
```

#### F2 reranker deboost implementation surface(~1.5h total)

```
F2.1 Settings 2 NEW knobs (10 min)
  ↓
F2.2 retrieval_engine.py:151-166 deboost loop (20 min)
  ↓
F2.3 5 NEW unit tests (40 min)
  ↓
F2.4 pytest 1091 → 1096 + ruff + mypy strict (10 min)
  ↓
F2.4 commit (10 min)
```

#### F3 LIVE verification surface(~1h total)

- F3.1 pre-flight per CLAUDE.md §10.3 step 5b — Langfuse 200 + Postgres SELECT 1
- F3.2 `.env` temporary override `RERANKER_CROSS_SECTION_DEBOOST=0.85` + `RERANKER_SECTION_PATH_PREFIX_DEPTH=2`
- F3.3 Backend explicit kill via WMI CommandLine filter + restart per ADR-0023(W37 ghost-Python-3.12 issue mitigation)
- F3.4 5+5 LIVE runs + nuanced drift metric per F0.2 catch (2)+(3)
- F3.5 decision tree intersect — outcome (a)/(b)/(c)

### Phase preconditions verify ✅

| Precondition | Status |
|---|---|
| W32 (h') `citation_expansion.py` shipped | ✅ commit `e9bd188` |
| W33 Rule 7 v2 + Rule 8 shipped | ✅ commit `149aebd` |
| W35 Option C `prompt_builder.py:30` shipped | ✅ commits `b2f4ca3..c590a86` |
| W36 PC-W34-1 `CLAUDE.md §10.3 step 5b` shipped | ✅ commit `3f65531` |
| W36 PC-W35-1 runner cp1252 fix shipped | ✅ commit `5520918` |
| W37 F1 `_find_neighbour_chunks` section_path filter infrastructure preserved | ✅ commit `da557ab`(W38+ enabler) |
| W37 F3 `.env` clean per PARTIAL revert ship | ✅ commit `31635b6` |
| ADR-0035 W25 F5 D2 symmetric deboost pattern reference | ✅ documented in `docs/adr/` |
| Working tree clean(0 ahead origin/main)| ✅ W37 closed pushed |
| Active phase = W38(rolling JIT)| ✅ W37 closed,W38 唯一 active |

### Cost containment policy reminder

Per `memory/feedback_judge_llm_cost_policy.md`(W36 saved 2026-05-26):
- ✅ W38 不涉及 LLM cost upgrade — F2 純 internal retrieval-side score multiply,F3 LIVE 用現有 backend(synthesizer `llm_primary=gpt-5.5` + judge `llm_judge=gpt-5.4-mini` 維持 H2 lock)
- ✅ W38 不觸 path (a) judge LLM 升級(永久 OUT per memory)

---

## Day 1 — 2026-05-27 — F1 LOW housekeeping batch + F2 Reranker deboost infrastructure + F3 LIVE BLOCKED + F4 closeout

### F1 LOW housekeeping batch — ✅ completed(commit `74ad872`)

- F1.1 Ruff `--fix --unsafe-fixes` 13 errors → 0 fixed clean(9 W33-W35 留底 + 4 W37 F2 runner)
- F1.2 `api/server.py:343-360` PC-W32-1 documentation 加 W38 amendment note(preserve no `reload=True` rationale + BUG-008 SelectorEventLoop factory tradeoff + W36 PC-W34-1 step 5b alternative)
- F1.3 `citation_expansion.py` module docstring PC-W32-2 integration pattern note 加入(W32 F1.8 3-tuple return + neighbor_chunks + build_citations Rule 5 contract preservation + W32 F2 reload-v1 incident evidence cite)
- F1.4 PC-W33-1 status reconcile RESOLVED via W36 PC-W34-1 ship documentation
- F1.5 pytest 1091 preserve PASS + ruff 13 → 0 clean

### F2 Reranker deboost infrastructure — ✅ completed(commit `cea024f`)

- F2.1 Settings 2 NEW knobs ship — `reranker_cross_section_deboost: float = 1.0`(disabled default per W26 PC1)+ `reranker_section_path_prefix_depth: int = 2`
- F2.2 `retrieval_engine.py:158-200` post-rerank deboost loop ship — **frozen RerankedChunk rebuild pattern**(R6 catch caught during F2.3 test debug — `RerankedChunk` per `base.py:18` is `@dataclass(slots=True, frozen=True)`,mutation via `*=` triggers `FrozenInstanceError`)+ re-sort by rerank_score descending + defensive malformed skip + observability log
- F2.3 5 NEW unit tests PASS — disabled no-op / cross-section reduced / hierarchical zoom preserved / re-sort invariant / malformed defensive
- F2.4 pytest 1091 → **1096 passed + 25 skipped + 0 failed**(+5 NEW exact match)+ ruff PASS(I001 import sort `--fix`)+ mypy strict W38 specific edits self-clean

### F3 LIVE 5+5 verification — ⚠️ BLOCKED by Azure 402 Payment Required

- F3.1 Pre-flight per CLAUDE.md §10.3 step 5b ✅ Langfuse 200 + Postgres SELECT 1
- F3.2 `.env` temp override `RERANKER_CROSS_SECTION_DEBOOST=0.85` + `RERANKER_SECTION_PATH_PREFIX_DEPTH=2`(112 → 117 lines)
- F3.3 Backend explicit kill api.server (PID 23260 ghost cleanup) + restart PID 7512(`Start-Process -WorkingDirectory` absolute path 一氣完成 25s warmup,/health 200 + 5 components reported)
- F3.4 `backend/w38-f3-runner.py` ship NEW `analyse_drift_nuanced` helper distinguishing `real_cross_section_drift_count` vs `valid_hierarchical_zoom_count`
- F3.4 Run 5+5 LIVE — **全 10 runs HTTP 502 Bad Gateway**
- F3 Direct curl test diagnose:`pipeline.retrieval_failed` 由 Azure AI Search `402 Payment Required` 引發(retrieval layer fail at Azure Search call,**never reach** W38 F2 reranker deboost logic)
- **Phase Gate INCONCLUSIVE per ADR-0017 R8 environmental block** — W17 F1.5b/F3.5b precedent reused

### F4 closeout — PARTIAL revert per Chris pick(per W17 F1.5b/F3.5b ADR-0017 R8 precedent)

- `.env` marker block + `RERANKER_CROSS_SECTION_DEBOOST=0.85` + `RERANKER_SECTION_PATH_PREFIX_DEPTH=2` removed(117 → 114 lines verified)
- Backend stopped(`Stop-Process` api.server PID 7512 via WMI CommandLine filter)
- F2 infrastructure preserved as W39+ enabler — Settings default=1.0 disabled,Cohere v4.0-pro contract unchanged
- W39+ HIGHEST NEW:F2 LIVE evidence collect trigger after Azure AI Search billing resolved(Chris IT action)
- Real-calendar effort total ~4h actual vs ~4h planned = within range

### Retro 7 段

#### 1. What Worked

- **W36 atomic batch precedent reuse** — F1 LOW housekeeping(procedural)+ F2 reranker deboost(C04 algorithm)雙目標 atomic batch + F-phase separation 成功 — F1 clean baseline + F2 attribution clean(無 confusion)
- **R6 Day 0 6 catches** 100% accurate + nuanced — `retrieval_engine.py:151-166` insertion point / W37 drift metric over-flag / I01 control query nature / ruff 13 not 8 / PC-W33-1 already resolved / `api/server.py` BUG-008 reload risk
- **Karpathy §1.3 surgical** — F2 code footprint:4 production files,Settings default=1.0 preserve production behavior structurally
- **Karpathy §1.1 think-before-coding upfront catch** — W37 raw drift metric 重新 frame(real_cross_section vs hierarchical_zoom 區分),W38 nuanced metric design upfront
- **Karpathy §1.1 mid-implementation catch** — `RerankedChunk` frozen=True 觸發 R6 catch during F2.3 test debug;immediate fix via rebuild pattern instead of mutation
- **Test helper extension backward-compat** — `_reranked` accept `original_index` + `hybrid_score` kwargs default,existing 9+ tests 無需更新
- **ADR-0035 W25 symmetric deboost pattern reference** — non-architectural per H1,non-hard-filter per W37 F1 -63% precedent

#### 2. What Didn't Work

- **F3 LIVE BLOCKED by Azure environmental issue** — 全 10 runs HTTP 502 由 Azure AI Search `402 Payment Required` 引發,Phase Gate INCONCLUSIVE
- **F3 環境 issue 揭示 evaluation infrastructure dependency** — Azure billing IT-side bottleneck(W11 Q11 Pattern A operational committed early June 2026 real-calendar)同樣 affect non-AI-controllable LIVE eval throughput
- **W37 drift metric over-flag pattern leakage** — W37 F3 raw drift count 之後又 reused 喺 W38 F0.5 progress.md retro,直至 W38 F0.2 R6 catch (2)+(3) 才 surface;Karpathy §1.1 think-before-coding 仍有 漏網之魚 across multi-phase carry-over

#### 3. Carry-overs

- **🚧 W39+ HIGHEST NEW** F2 LIVE evidence collect trigger — Azure AI Search billing resolved 之後 backend restart + 5+5 LIVE run + decision tree intersect(F2 infrastructure 已 ready,~30-45min effort)
- **🚧 W37 F1** `_find_neighbour_chunks` section_path filter infrastructure preserved enabler(W37 F2 G1b goal PASS evidence + W38 F2 complementary axis after Azure billing resolved)
- **🚧 W38 F2** reranker deboost infrastructure preserved enabler — Settings default=1.0 disabled,Cohere contract unchanged
- **🚧 W39+ MEDIUM** `\b\d+\.\d+\b` regex relax for `_find_neighbour_chunks`(W37 F2 evidence 雙重 filter over-conservative)
- **🚧 NEW R-W38-1** Azure AI Search 402 Payment Required environmental block(per ADR-0017 R8 umbrella — IT-side credentials populate event trigger)
- **🚧 Q14 SME-validate `reference_answer` cascade** — LONG-TERM(`eval-set-v1-final.yaml` W15 F1 CO ship 真正解 systematic context_recall 根因)
- **🚧 永久 OUT** path (a) judge LLM 升級 per memory `feedback_judge_llm_cost_policy.md`
- **🚧 NOW RESOLVED** via W38 F1.1+F1.4:8 個 pre-existing ruff issues + PC-W32-1 + PC-W32-2 + PC-W33-1(removed from W39+ queue)

#### 4. ADR Triggers

- **無 NEW ADR** — F1+F2 純 internal logic / procedural,non-architectural per H1
- F2 evidence 留 W39+ ADR draft material(如 LIVE F3 outcome (a) PASS production flip default `reranker_cross_section_deboost=1.0 → 0.85` 觸發 W39+ separate phase Settings flip decision)
- **R-W38-1** 加入 W39+ RISK_REGISTER NEW row — Azure billing environmental block(per ADR-0017 R8 umbrella;W11 Q11 Pattern A IT-side dependency)

#### 5. Phase Gate Result

- **PARTIAL closeout per Chris pick** + **per ADR-0017 R8 environmental block precedent**(W17 F1.5b/F3.5b reused)
- **Production behavior 100% revert W37 baseline** via `.env` cleanup + Settings default=1.0
- **F1 LOW housekeeping ship 100%** — ruff clean + 3 PC documentation reconcile
- **F2 reranker deboost infrastructure ship 100%** — Settings + retrieval_engine + 5 unit tests pytest 1091 → 1096 PASS

#### 6. W39+ Priority Queue Locked

| 優先級 | 候選 |
|---|---|
| **HIGHEST NEW** | F2 LIVE evidence collect — Azure AI Search billing resolved 之後 trigger(backend restart + 5+5 LIVE + decision tree;~30-45min effort)|
| **HIGHEST preserved** | W37 F1 + W38 F2 infrastructure preserved enabler(both ready,LIVE evidence collect together?) |
| **MEDIUM preserved** | `\b\d+\.\d+\b` regex relax for `_find_neighbour_chunks` |
| **LONG-TERM** | Q14 SME-validate `reference_answer` cascade(`eval-set-v1-final.yaml`)|
| **永久 OUT** | path (a) judge LLM 升級 |
| **REMOVED from queue** | W38 F1 ship 解 — 8 ruff issues + PC-W32-1 + PC-W32-2 + PC-W33-1 |
| **長期 carry-over** | (c)(e)(f)/BUG-026+027/W22 D8/W16 F1-F4 Track A IT cred |
| **NEW R-W38-1** | Azure AI Search 402 environmental block(W11 Q11 Pattern A IT dependency)|

#### 7. Actual vs Planned Effort

| Phase | Planned | Actual | Δ |
|---|---|---|---|
| F0 | 30min | ~30min | within |
| F1 | 30min | ~30min(including F1.5 pytest ~7min wait + ruff fix + 3 doc edits)| within |
| F2 | 1.5h | ~1h 50min(F2.3 unit test frozen RerankedChunk catch absorbed +20min)| +10% |
| F3 | 1h | ~25min runtime + ~5min curl diagnose = **~30min**(LIVE runs failed fast at retrieval layer,no synthesizer wait time)| -50% absorbed by environmental block |
| F4 | 30min | ~30min | within |
| **Total** | ~4h | **~4h** wall-clock | within range |

Real-calendar collapse ~3-4×(2026-05-26 W37 closed → 2026-05-27 D1 W38 F0-F4 complete same-day per rolling JIT discipline)。

---

**End of W38 progress.md Day 1**
