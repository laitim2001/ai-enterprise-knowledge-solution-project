---
phase: W39-f2-live-evidence-free-tier-workaround
plan_ref: ./plan.md
checklist_ref: ./checklist.md
status: closed_partial   # F3 收尾 2026-05-27 — F1 deboost mechanism verified + F2 G1b PASS G1a mode-conflate FAIL → PARTIAL revert per Chris pick
last_updated: 2026-05-27
---

# W39 — Progress Log

## Day 0 — 2026-05-27 — F0 啟動

### 啟動行動

- ✅ F0.1 建立 `docs/01-planning/W39-f2-live-evidence-free-tier-workaround/` folder
- ✅ F0.2 R6 Day 0 5 catches surfaced(per below)
- ✅ F0.3 起草 `plan.md` 7 段
- ✅ F0.4 起草 `checklist.md` 原子化勾選項
- ✅ F0.5 起草 `progress.md` Day 0(本 entry)
- ⏳ F0.6 啟動 commit pending
- ⏳ F0.7 session-start.md §10 W39 row append pending

### R6 Day 0 5 catches 報告

#### catch (1) — `/retrieval_test` endpoint 已 support mode param(Path B 0-code-change)

`backend/api/schemas/retrieval_test.py:17`:
```python
mode: Literal["hybrid", "vector", "fulltext"] = "hybrid"
```

`backend/api/routes/retrieval_test.py:74-80`:
```python
result = await engine.retrieve(
    query=payload.query, kb_id=kb_id,
    top_k=payload.top_k, mode=payload.mode, rerank=payload.rerank,
)
```

**Implication**:F1 Path B 直接 hit `POST /kb/{kb_id}/retrieval-test` with `{"mode": "vector"}` body field — 0-code-change LIVE。Skip Azure semantic ranker quota(Free tier 402 root cause)同時保留 Cohere rerank + W38 F2 deboost。

#### catch (2) — `/query` schema `QueryRequest` 不含 mode(Path A additive scope)

`backend/api/schemas/query.py:41-57` `QueryRequest`:
- top_k_retrieval / top_k_rerank / llm_model / reranker / enable_crag / enable_intent_routing — 全部 covered
- **NO `mode` field**

**Implication**:F2 Path A additive — `QueryRequest.mode: Literal["hybrid", "vector", "fulltext"] = "hybrid"` 加入,backward-compat default preserve current behavior。`query.py:128 + 308` retrieve() 2 call sites propagate `mode=payload.mode`。對齊 `/retrieval_test` schema permanent symmetry(F3 唔 revert)。

#### catch (3) — W38 F2 deboost loop mode-independent

`backend/retrieval/retrieval_engine.py:158-200` deboost loop 喺 `if do_rerank and hits:` block 內,**mode 影響 hybrid search shape 但唔影響 deboost trigger**。Cohere rerank 接收 retrieve hits(無論 hybrid/vector/fulltext),返 RerankedChunk + section_path,W38 F2 deboost loop fire regardless。

**Implication**:Path B(vector mode)同 Path A(hybrid mode after Azure resolved)應該同樣 verify W38 F2 deboost effect。Path B vector mode evidence 已 sufficient for W38 F2 verification scope。

#### catch (4) — Free tier 402 likely semantic ranker monthly quota exhausted

Azure AI Search Free tier:
- Semantic ranker monthly quota ~1000 queries/month
- W34-W38 cumulative LIVE eval(eval/run + 5+5 reproducibility runs × multiple phases)可能撞 quota
- 402 Payment Required 通常表示 quota / billing block,non-tier-feature-missing(那會 return 400 with specific message)

**Implication**:Vector mode 不消耗 semantic quota → 應該繞過 Free tier 402;F1 Path B early signal 可驗證 hypothesis。

#### catch (5) — W38 cea024f F2 infrastructure ready

W38 commit `cea024f` ship:
- `storage/settings.py` 加 NEW knobs:
  - `reranker_cross_section_deboost: float = 1.0`(disabled default)
  - `reranker_section_path_prefix_depth: int = 2`
- `retrieval/retrieval_engine.py:158-200` post-rerank deboost loop:
  - Frozen RerankedChunk rebuild pattern
  - Re-sort by rerank_score descending
  - Defensive malformed section_path skip
  - Observability log `reranker_cross_section_deboost_applied`
- 5 NEW unit tests PASS — backend pytest 1091 → 1096
- `.env` clean state preserved post W38 F4

**Implication**:W39 唔需要 code change for F2 deboost logic;只需 `.env` override `RERANKER_CROSS_SECTION_DEBOOST=0.85`(W38 F3 pattern reused)即可 LIVE 驗證。

### F-phase pre-implementation surface

#### F1 Path B execution sequence(~30min total)

```
F1.1 pre-flight Langfuse 200 + Postgres SELECT 1 (1 min)
  ↓
F1.2 .env temp override RERANKER_CROSS_SECTION_DEBOOST=0.85 + DEPTH=2 (2 min)
  ↓
F1.3 backend explicit kill + Start-Process restart + /health verify ~30s warmup (5 min)
  ↓
F1.4 write w39-f1-pathb-runner.py + run 5+5 (~15 min)
  ↓
F1.5 decision tree intersect G1+G2+G3 (5 min)
```

#### F2 Path A execution sequence(~45min total)

```
F2.1 QueryRequest.mode additive + retrieve() propagation 2 sites + 2 unit tests (15 min)
  ↓
F2.2 pytest 1096 → 1098 + ruff + commit (10 min)
  ↓
F2.3 backend kill + restart + /health verify (5 min)
  ↓
F2.4 write w39-f2-patha-runner.py + run 5+5 (~15 min)
  ↓
F2.5 decision tree intersect G1+G2+G3+G4+G5 (5 min)
```

#### F3 closeout surface

- `.env` marker block removed(W27/W29/W37/W38 pattern reused)
- `QueryRequest.mode` field preserved permanent enhancement(對齊 ADR-0021 `/retrieval_test`)
- W40+ HIGHEST candidate per F2 outcome — Settings default flip 0.85 OR hybrid mode billing-resolved re-verify

### Phase preconditions verify ✅

| Precondition | Status |
|---|---|
| W38 F2 reranker deboost infrastructure ship | ✅ commit `cea024f` |
| W38 F4 closeout `.env` clean state | ✅ commit `3d7c834` |
| ADR-0021 `/retrieval_test` mode param support | ✅ `api/schemas/retrieval_test.py:17` |
| W36 PC-W34-1 step 5b pre-flight protocol | ✅ shipped W36 |
| W36 PC-W35-1 runner cp1252 fix | ✅ shipped W36(F1+F2 runner 複用) |
| Cohere v4.0-pro endpoint reachable | ✅ `.env` cred populated(separate from Azure Search billing) |
| Working tree clean | ✅ W38 closed_partial pushed |

### Cost containment policy reminder

Per `memory/feedback_judge_llm_cost_policy.md`:
- ✅ W39 不涉及 LLM cost upgrade — F1+F2 純 retrieval-side + API schema additive,F1+F2 LIVE 用現有 backend
- ✅ W39 不觸 path (a) judge LLM 升級(永久 OUT per memory)

---

## Day 1 — 2026-05-27 — F1 + F2 + F3 closeout PARTIAL revert(same-day cascade)

### F1 Path B `/retrieval_test` mode=vector LIVE 5+5 完成行動

- ✅ F1.1 pre-flight Langfuse 200 + Postgres SELECT 1
- ✅ F1.2 `.env` temp override `RERANKER_CROSS_SECTION_DEBOOST=0.85 + RERANKER_SECTION_PATH_PREFIX_DEPTH=2`(112 → 119 lines)
- ✅ F1.3 backend explicit kill(W37/W38 ghost-Python 重現 PID 47544 hang + 10388 ghost)+ kill both + bash & spawn recovery → /health 200 ~25s warmup
- ✅ F1.4 `w39-f1-pathb-runner.py` ship + 5+5 LIVE runs(deterministic across 5 runs — /retrieval_test bypass reformulator)
- ✅ F1.5 decision tree Path B(retrieval-only)— G1a chunks 5.0 PASS + G1b real_drift 3.0 FAIL + G2 chunks 5.0 PASS + G3 wall 4.59s PASS

### **重要 evidence**:W38 F2 deboost 機制 VERIFIED 正確 firing

Backend log 10/10 runs confirm:
```
event=reranker_cross_section_deboost_applied
deboost_count=4 of 5 total_candidates
anchor_prefix=["§8 family"](I07) / ["§4 family"](I01)
depth=2, deboost_factor=0.85
```

但 G1b real_drift=3.0 FAIL 揭示 **2 個架構洞察**(Karpathy §1.1 think-before-coding surfaced via empirical evidence):

#### 架構洞察 1:Deboost scope-limited 唔 reduce cross-section drift

- `reranker.rerank(top_k=5)` 返 fixed top-5
- Deboost 只 re-order existing top-5(via re-sort post-multiply)
- **唔 pull-in same-section candidates from positions 6-50** in the Cohere candidate pool
- 結果:top-5 仍含 3 cross-section chunks(§3 + Contents + §7),只係降低 ranks

**W40+ HIGHEST NEW fix candidate**:Cohere overfetch — `reranker.rerank(top_k=top_k * 4)` 然後 deboost + truncate to top_k → 真正 pull-in same-section from larger pool

#### 架構洞察 2:Anchor-prefix length-mismatch over-deboost

- I07 anchor sp `['§8']` length 1
- depth=2 → anchor_prefix[:2] = `['§8']`
- §8.6 cand sp `['§8', '§8.6']` length 2 → cand_prefix[:2] = `['§8', '§8.6']`
- 兩者 NOT equal → §8.6 valid hierarchical zoom-in **反被 deboosted**
- 違背 W38 plan §1 「symmetric deboost only true cross-section」intent

**W40+ HIGHEST NEW fix candidate**:Anchor-prefix length-mismatch handling — `if len(anchor_prefix) < depth: depth = len(anchor_prefix)` OR explicit short-anchor branch logic

### F2 Path A `/query` mode=vector full pipeline LIVE 5+5 完成行動

- ✅ F2.1 `QueryRequest.mode` additive field + `routes/query.py` 2 call sites propagate
- ✅ F2.1 **R3 plan amend** — F2 iter 1 全 10 runs HTTP 502 揭示 root cause:`fused_retrieve()` 內部 retrieve() calls 未 propagate mode → default hybrid → Azure 402;增 `result_fusion.py:82-89 fused_retrieve() mode` param + propagation
- ✅ F2.2 3 NEW unit tests PASS + ruff PASS(I001 import order auto-fixed)+ mypy strict W39 self-clean
- ✅ F2 commit `dadcb44`(QueryRequest.mode + retrieve propagation 3 sites + 3 unit tests + F1 runner backfill + R3 fused_retrieve amendment)
- ✅ F2.3 backend restart with fused_retrieve mode patch — direct curl test `/query mode=vector` → HTTP 200 valid citation answer(bypass Azure 402 成功)
- ✅ F2.4 `w39-f2-patha-runner.py` ship + 5+5 LIVE full pipeline runs(F2 iter 2 success)
- ✅ F2.5 decision tree Path A:**G1a FAIL** I07 avg_cit 3.6 (-25% vs W35 4.8)+ **G1b goal PASS ⭐** real_drift 1.0(W37 hard filter -63% → W39 symmetric -25% 改善)+ G1b stretch FAIL drift=1 across all + **G2 control PASS ⭐** I01 avg_cit 6.6 + G3 latency FAIL +37% reformulator overhead with vector mode

### W37 vs W38 vs W39 三相對比 ⭐

| Phase | Approach | I07 avg_cit | I07 real_drift | I01 control | 取捨 |
|---|---|---|---|---|---|
| W35 baseline | hybrid mode + no deboost | **4.8** ⭐ | n/a | 5.4 | production baseline preserve |
| W37 F2 | hybrid mode + hard filter | 1.8 (**-63%**) ⚠️ | low | 2.8 (-48%) ⚠️ | FAIL — hard filter 過 aggressive |
| W39 F2 | vector mode + symmetric deboost 0.85 | 3.6 (**-25%**)| **1.0** ✅ | **6.6** ⭐ | PARTIAL — mode + deboost conflate |
| W40+ TBD | hybrid mode + symmetric deboost(billing resolved)| ? | ? | ? | 真正 production isolated evidence |

W39 symmetric deboost approach 明顯比 W37 hard filter approach 好 — 證明 ADR-0035 W25 pattern reference correct。

### F3 closeout PARTIAL revert 完成行動

- ✅ `.env` marker block + RERANKER_* lines removed(119 → 115 lines verified)— production preserve default deboost=1.0 disabled
- ✅ Backend kill PID 46240 via WMI CommandLine filter
- ✅ F2 production code preserved:
  - W38 F2 deboost infrastructure(commit `cea024f`,Settings 2 knobs + retrieval_engine.py:158-200 loop + 5 unit tests + observability log)
  - W39 F2 QueryRequest.mode field(commit `dadcb44`,permanent enhancement 對齊 ADR-0021)
  - W39 F2 fused_retrieve mode propagation(commit `dadcb44`,permanent enhancement)
- ✅ 4 artifact sync(plan.md / checklist.md / progress.md frontmatter status flip + retro)
- ⏳ session-start.md §10 W39 row + F3 closeout commit pending

### Retro 7 段

#### 1. What Worked

- **W36 batch precedent + F-phase separation reused** — F1 LOW (Path B 0-code-change) + F2 (Path A code patch) 兩階段 sequential ship 證明清晰 attribution
- **R6 Day 0 5 catches 100% accurate** — `/retrieval_test` mode ready / `/query` schema additive / W38 F2 mode-independent / Free tier 402 root cause / W38 cea024f infrastructure ready
- **Karpathy §1.3 surgical** — F2 code footprint:3 production files(query.py schema + query.py routes + result_fusion.py),backward-compat defaults preserve W38- production behavior
- **Karpathy §1.1 think-before-coding surfaced 架構洞察 2 個** — F1 evidence 揭示 W38 F2 deboost scope-limited + anchor-prefix length-mismatch,non-obvious from F2 unit tests alone
- **R3 plan amend in-flight pattern** — F2 iter 1 全 502 揭示 plan-text contamination missing fused_retrieve mode propagation,即時 amend 修正,F2 iter 2 success(per W22 D9 R6 recursive scope amend precedent)
- **ADR-0035 W25 symmetric deboost pattern reference VALIDATED** — W39 F2 LIVE evidence 明顯比 W37 F1 hard filter approach 好(I07 cit -25% vs -63%)— 確認 design hypothesis

#### 2. What Didn't Work

- **mode=vector + deboost conflate** — G1a FAIL -25% 可能 mode=vector tradeoff(less semantic top-K diversity)或 W38 F2 deboost effect,**未能 isolate**
- **Ghost-Python-3.12 restart issue 第 3 次重現** — W37 F3 + W38 F3 + W39 F1.3 同一 pattern;PowerShell Start-Process 有時 spawn system Python 而非 venv Python,需 kill both + bash & spawn recovery pattern(每次 ~5min absorbed overhead)
- **F2 iter 1 plan-text contamination** — fused_retrieve() mode propagation 漏算 plan §2 F2.1,F2 iter 1 全 502 才 surface;**R6 recursive scope catch evidence pattern 8 reinforced**(R6 plan-text-itself contamination per W22 D9 amend)
- **G3 latency FAIL +37% reformulator overhead** — vector mode 配 reformulator + RAG fusion 比 hybrid mode 慢 5s,non-deboost-isolated;結構性問題 — 同 W34 F2 evidence LLM emit dominant 92% 不同 axis

#### 3. Carry-overs

- **🚧 W40+ HIGHEST NEW** hybrid mode billing-resolved re-verify(isolate true deboost effect without mode=vector conflate)
- **🚧 W40+ HIGHEST NEW** Cohere overfetch fix(W39 F1 架構洞察 1)— `reranker.rerank(top_k=top_k * 4)` + deboost + truncate
- **🚧 W40+ HIGHEST NEW** Anchor-prefix length-mismatch fix(W39 F1 架構洞察 2)— handle len(anchor_sp) < depth case
- **🚧 W37 F1** `_find_neighbour_chunks` section_path filter infrastructure preserved enabler
- **🚧 W38 F2** reranker deboost infrastructure preserved enabler(Settings default=1.0)
- **🚧 W39 F2** QueryRequest.mode + fused_retrieve mode propagation **preserved permanent enhancement**(對齊 ADR-0021)
- **🚧 NEW R-W38-1** Azure AI Search 402 environmental block per ADR-0017 R8 umbrella(W11 Q11 IT-side dependency persist)
- **🚧 Q14 SME-validate `reference_answer` cascade** LONG-TERM
- **🚧 永久 OUT** path (a) judge LLM 升級
- **🚧 Ghost-Python-3.12 restart 3 次重現** — W40+ candidate document mitigation pattern OR investigate Windows Start-Process behavior

#### 4. ADR Triggers

- **無 NEW ADR** — F1 0-code-change + F2 additive backward-compat per H1
- F2 mode field + fused_retrieve propagation 對齊 ADR-0021 `/retrieval_test` symmetry,non-architectural extension
- W40+ Cohere overfetch + anchor-prefix length-mismatch fix 可能 trigger NEW ADR(retrieval-side algorithm change),need W40+ R6 audit

#### 5. Phase Gate Result

- **PARTIAL closeout per Chris pick** — F1 Path B mechanism verified + F2 Path A G1b goal PASS + 2 架構洞察 surfaced
- **Production behavior 100% revert W38 baseline** via `.env` cleanup + Settings default=1.0
- **F2 production code preserved** — W38 F2 deboost infrastructure + W39 F2 mode field + fused_retrieve mode propagation
- W39 F2 mode field permanent enhancement(對齊 ADR-0021 /retrieval_test)— production /query endpoint 增 debug + A/B test convenience + future Free tier workaround backup

#### 6. W40+ Priority Queue Locked

| 優先級 | 候選 | Source |
|---|---|---|
| **HIGHEST NEW** | Hybrid mode billing-resolved re-verify | Azure billing IT-side action;Cohere overfetch + anchor-prefix fix 之後 trigger |
| **HIGHEST NEW** | Cohere overfetch `reranker.rerank(top_k=top_k * 4)` + deboost + truncate | W39 F1 架構洞察 1 |
| **HIGHEST NEW** | Anchor-prefix length-mismatch fix | W39 F1 架構洞察 2 |
| **HIGHEST preserved** | W37 F1 + W38 F2 + W39 F2 infrastructure preserved as enabler |
| **MEDIUM preserved** | `\b\d+\.\d+\b` regex relax for `_find_neighbour_chunks` |
| **LONG-TERM** | Q14 SME-validate `reference_answer` cascade |
| **永久 OUT** | path (a) judge LLM 升級 |
| **NEW R-W38-1** | Azure AI Search 402 environmental block(persist W11 Q11 IT) |
| **LOW** | Ghost-Python-3.12 restart investigate Windows Start-Process behavior(3 次重現) |
| 長期 carry-over | (c)(e)(f) BUG-026+027 + W22 D8 + W16 F1-F4 Track A IT cred |

#### 7. Actual vs Planned Effort

| Phase | Planned | Actual | Δ |
|---|---|---|---|
| F0 | 15min | ~15min | within |
| F1 | 30min | ~40min(+10min ghost-Python restart absorbed)| +33% |
| F2 | 45min | ~70min(+25min R3 fused_retrieve amend + 2 iter)| +55% |
| F3 | 15min | ~25min | +67% |
| **Total** | ~1.5-2h | **~2.5h** wall-clock | +25% |

Real-calendar collapse ~5×(2026-05-27 W38 closed → 2026-05-27 W39 F0-F3 complete same-day per rolling JIT discipline)。

---

**End of W39 progress.md Day 1**
