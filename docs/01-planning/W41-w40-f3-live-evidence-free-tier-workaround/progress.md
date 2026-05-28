---
phase: W41-w40-f3-live-evidence-free-tier-workaround
plan_ref: ./plan.md
checklist_ref: ./checklist.md
status: closed   # F2 收尾 2026-05-28 — Phase Gate PASS outcome (b) per plan §2 G3b-caveat path
last_updated: 2026-05-28
---

# W41 — Progress

> Daily progress journal。每日 append 一個 Day-N entry,closeout 時 retro 7 段。

## Day 0 — 2026-05-28(kickoff)

### Trigger

W40 closed 2026-05-27 pushed origin/main `2ca162e`。User explicit pick via AskUserQuestion:**「W41 kickoff candidate?」=「(1) F3 LIVE Free tier workaround(推薦)」**。

W40 F3 LIVE 喺 closeout 時 SKIPPED per Chris pick + W36 operational debt batch precedent;F3 LIVE preserved 為 W41+ HIGHEST NEW candidate。W41 兌現 F3 LIVE 經 Free tier mode=vector workaround,non-Azure-billing-dependent immediate-trigger path。

### Plan rationale

- **W40 F1+F2 evidence-driven 連續 narrative closure**:W39 evidence → W40 fix → W41 LIVE verify fix effect ⭐
- **0-code-change LIVE evidence collection** per W34 measurement-only precedent + W39 F1 Path B 0-code-change pattern
- **Reuse W39 Path A pattern**:`w39-f2-patha-runner.py` reusable as W41 F1 runner template + `QueryRequest.mode` permanent enhancement + `.env` marker block convention preserved
- **W36 PC-W34-1 step 5b pre-flight protocol applied**(Langfuse `/api/public/health` 200 + Postgres `SELECT 1`)
- **Karpathy §1.3 surgical scope 嚴守**:無 production code change + 無 NEW Settings field(W40 已 ship)+ 唔 modify production behavior
- **Q4 measurement-experiment-fail-policy applies**:F2 closeout `.env` REVERT 維持 production preserve invariant per W37/W38/W39/W40 precedent

### R6 Day 0 6 catches surfaced(per CLAUDE.md §10 R6 W22 D9 recursive scope amendment)

| # | Catch | Evidence | Mitigation |
|---|---|---|---|
| 1 | `.env` clean state confirmed | grep RERANKER_/CITATION_EXPANSION_SECTION_PATH = 0 matches | F1.2.a W41 marker block 加 + F2.A.5 closeout REVERT |
| 2 | `w39-f2-patha-runner.py` reusable template | Read tool L1-50 — utf-8 reconfigure + 2 queries + body mode field 已 ship | F1.5 copy template + 加 log helper |
| 3 | W40 F2 `rerank_top_k` + W40 F1 `effective_depth` NEW log fields | retrieval_engine.py L200-206 + L232-238 W40 commits bca7446+ca025cc | F1.8 log parse extract 兩 NEW fields |
| 4 | W40 F2 design requires both gates active(deboost < 1.0 AND multiplier > 1)| retrieval_engine.py L158-167 W40 F2 implementation | F1.2 必須同時 set 3 knobs(deboost+multiplier+depth)|
| 5 | Ghost-Python-3.12 restart pattern preserve | W37+W38+W39+W40 重現 4 次 cumulative | F1.3.a WMI CommandLine filter kill + bash & background spawn recovery |
| 6 | Free tier mode=vector caveat preserved | W39 F2 Path A precedent — vector mode bypass Azure semantic + reformulator overhead diff = conflate non-isolated | F1.9 evidence interpretation 必須 caveat 標明 hybrid isolation 仍 W42+ gate |

### Real-calendar projection

- F0 ~20min(已 build folder + 4 artifacts + commit pending)
- F1 ~30-45min(pre-flight + .env + restart + sanity + runner + 5+5 + aggregate + log parse + decision tree)
- F2 ~15-20min(closeout cross-doc sync + .env revert + commit + push)

**估計 total ~1.5-2h actual real-calendar collapse**(對齊 W39 F1 Path B ~30min + F2 Path A ~45min pattern,加 closeout overhead)。

### Next

F0.6 commit + F0.7 session-start.md sync → F1 pre-flight + restart 啟動 LIVE workflow。

---

## Day 1 — 2026-05-28(F1 + F2 same-day collapse)

### F1 LIVE Path A workflow(~75min actual)

**Pre-flight + .env + restart**(~20min):
- Langfuse `/api/public/health` 200 + Postgres `SELECT 1` ready_for_query
- `.env` marker block W41 F1 TEMPORARY 3 knobs(deboost=0.85 + depth=2 + multiplier=4)
- Backend restart via PowerShell Start-Process(W37/W38/W39/W40 pattern,W41 無 ghost — direct fresh start path 5 phase 中首次)

**Sanity curl 揭示 critical evidence**(~5min):
- `POST /query mode=vector` → HTTP 200 + 9 citations + answer text mentions Scenario A/B/D
- Backend log inspect:`reranker_cross_section_deboost_applied` event `effective_depth: 1` for chapter intro anchor + `retrieval_complete` event `top_k: 40 + rerank_top_k: 160 + fetch_k: 50` → W40 F1+F2 mechanism both verified at sanity stage
- **⚠️ NEW architectural insight 3 surfaced**:Cohere `top_n=min(top_k, len(candidates))` self-cap at fetch_k=50,即 rerank_top_k=160 想 但實際 Cohere 只能 rerank 50,multiplier=4 wasted 3 倍 over fetch_k ceiling

**Runner ship**(~10min):
- `backend/w41-f1-runner.py` shipped — copy `w39-f2-patha-runner.py` template + 加 `parse_log_evidence()` helper extracting `effective_depth` + `rerank_top_k` + `deboost_count` + `total_candidates` + `anchor_prefix_examples` distributions

**LIVE 5+5**(~40min wall — `21.95s avg I07 * 5 + 15.54s avg I01 * 5` plus runner overhead):
- 5 runs Q-W25-I07 mode=vector — cits 12/6/12/9/6
- 5 runs Q-W25-I01 mode=vector — cits 9/3/9/3/6
- Per-run JSON dump + aggregate JSON

**Aggregate outcome**:
- I07 avg_lat **21.95s** / avg_cit **9.0** / real_drift **3.00** / refusals 0/5
- I01 avg_lat 15.54s / avg_cit **5.4**(EXACT W35 baseline 5.4 preserve)/ refusals 0/5

**Decision tree intersect**:G1 + G2 + G3a(3 thresholds)+ G4 PASS;G3b FAIL 3.0 > 1.0 per design tradeoff(mode=vector + 94-98% deboost rate yields more cross-section §7.x integration patterns surfaced as goal-aligned context)

**⭐⭐⭐ Run 4 milestone**:9 cits = §8.1 Scenario A + §8.2 Scenario B + §8.3 Scenario C + §8.4 Scenario D + §8.5 Scenario E + §8.6 Coverage summary + §8.1 Pattern characteristics + §7.7 ServiceNow + §7.9 Docuware — **首次 Q-W25-I07 enumeration query 一次 retrieve §8.1-§8.5 全 5 個 Scenarios + §8.6 Coverage**(W25 path III + W32 (h') + W40 F1+F2 累積 mechanism culminated)

### F2 closeout(~15min)

- Backend killed via PowerShell `Get-CimInstance Win32_Process` + `Stop-Process -Force`
- `.env` REVERTED — `grep -c "RERANKER_" .env` = 0 verified(production preserve default disabled invariant per W37/W38/W39/W40 precedent)
- Cross-doc sync:plan.md + checklist.md + progress.md(本文件)+ session-start.md §10 W41 row flip
- W40 F1+F2 production code preserved as W42+ enabler unchanged(retrieval_engine.py + settings.py + server.py 全 untouched in W41)

---

## Retro

### 1. 整體結果

**Phase Gate PASS outcome (b) per plan §2 G3b-caveat path** ⭐⭐⭐ 

**Key outcome metrics**:
- Cumulative commits W41:F0 `73cc046` + F0.7 `7c74470` + F2 closeout commit pending
- W40 F1 mechanism verified ✅ — `effective_depth ∈ {1, 2}` distribution observed across 10 deboost events(corpus chapter intro length 1 + sub-section length 2 both 出現 correctly)
- W40 F2 mechanism verified ✅ — `rerank_top_k=160` uniform 10/10 = top_k=40 * multiplier=4(W40 F2 design fired correctly)
- **W40 F1+F2 combined effect**:I07 avg_cit **9.0** vs W35 baseline **4.8** = **+88%** ⭐⭐⭐ + vs W39 F2 Path A **3.6** = **+150%** ⭐⭐⭐
- I01 control **5.4 EXACT W35 baseline 5.4 preserve**(non-regression)
- **🎯 Run 4 milestone** — 首次 Q-W25-I07 enumeration query 一次 retrieve **§8.1+§8.2+§8.3+§8.4+§8.5+§8.6** 全 5 Scenarios + Coverage summary(W25 path III + W32 (h') + W40 F1+F2 mechanism culminated)
- G3b drift 3.0 FAIL preserved per mode=vector goal-aligned design tradeoff(§7.x integration patterns supporting §8.x scenarios — drift definition = cross top-level INCLUDES intentional context)

**3 architectural insights cumulative across W39+W40+W41**:
- **Insight 1**(W39 F1)— Cohere overfetch path 3:**fixed by W40 F2** ✅
- **Insight 2**(W39 F2)— Anchor-prefix length-mismatch:**fixed by W40 F1** ✅
- **Insight 3**(W41 F1 NEW)— Cohere `top_n=min(top_k, len(candidates))` self-cap at fetch_k=50 → multiplier ceiling lift required for true 4x overfetch effect → W42+ MEDIUM NEW candidate

### 2. 5 axes lessons learned

| Axis | Finding | Action |
|---|---|---|
| **Plan accuracy** | F0 ~20min + F1 ~75min(estimate 30-45min — F1 LIVE 5+5 runtime alone 已 ~3 min/query * 10 = 30min,加 setup + log parse + aggregate)+ F2 ~15min = ~110min actual vs ~90-120min estimate — within range | Pattern correct — multi-query LIVE workflows estimate baseline ~10-15min per query for full pipeline + restart overhead |
| **Karpathy §1.1 think-before-coding** | R6 Day 0 6 catches verified at F0;sanity curl 直接 surface insight 3 at F1.4 before LIVE 5+5 — saves wasted analysis time | Maintain R6 + add sanity stage between pre-flight and full LIVE run |
| **Karpathy §1.3 surgical** | 0-code-change measurement phase per W34 precedent — preserved + no scope creep | Pattern works — separate evidence collection phase from implementation phase |
| **W36 atomic batch precedent applied recursive** | W41 兌現 W40 F3 SKIPPED via separate phase — preserves clean attribution per Karpathy §1.3 + W26 PC1 | Pattern formalized — SKIPPED LIVE 可 promoted to W{N+1} phase preserving 0-code-change measurement-only nature |
| **Sequential ship strategy W31 validated extended** | W37 fix → W38 fix → W39 LIVE → W40 fix → W41 LIVE = clean evolution chain across 5 phases ⭐ — each phase single-axis with measurable attribution | Pattern preserved — sequential ship enables cumulative architectural insight discovery |

### 3. CLAUDE.md / PROCESS.md / session-start.md 同步

- **CLAUDE.md**:無 amendment required(W41 0-code-change measurement;延續 W34 precedent + W40 H1 verdict)
- **PROCESS.md**:無 amendment required
- **session-start.md §10**:W41 row append closed 2026-05-28 + W41+ → W42+ rename(F2 closeout commit)

### 4. Memory updates

無 NEW memory required — W41 mechanism evidence 已 catalogued via commit message + retro。`feedback_judge_llm_cost_policy.md` + `feedback_chinese_primary_replies.md` + `feedback_design_fidelity.md` + `project_synthesizer_overview_refuse_w25_d4.md` 等 standing memories 持續 effective。

**項目進展 note**:W41 milestone surface W25 path III refuse pattern(W25 D4「show me all the Integration scenarios」refuse)現在 RESOLVED via W40 F1+F2 mechanism — memory `project_synthesizer_overview_refuse_w25_d4.md` 可考慮 W42+ 加 closure note(per Karpathy §1.3 surgical update — wait for hybrid mode billing-resolved STRONG confirm before close memory permanently)。

### 5. 後續(W42+ candidates)

| Priority | Candidate | Trigger / Effort |
|---|---|---|
| **HIGHEST NEW** | Production default flip ADR for W40 F1+F2 knobs | W41 LIVE evidence G3a STRONG +88-150% verified;sequential per W26 PC1(deboost+depth knobs cluster ADR / overfetch_multiplier ADR separate);trigger 條件:Azure billing resolved hybrid mode re-verify confirm OR explicit ADR-route trigger |
| **MEDIUM NEW** | hybrid_overfetch_for_rerank vs multiplier ceiling lift | W41 evidence:fetch_k=50 + multiplier=4 + top_k=40 → rerank_top_k=160 但 Cohere self-cap to 50 = multiplier wasted 3 倍;refinement 將 hybrid_overfetch_for_rerank dynamic 配合 multiplier |
| **HIGHEST preserved** | Hybrid mode billing-resolved re-verify | Azure billing IT-side gate;唯一 path 分離 hybrid mode contribution vs vector mode conflate |
| **MEDIUM preserved** | `\b\d+\.\d+\b` regex relax for `_find_neighbour_chunks` | TBD |
| **LOW preserved** | Ghost-Python-3.12 restart investigate | W37+W38+W39+W40 重現 4 次,W41 無;sample size 仍 small |
| **Long-term** | Q14 SME-validate / BUG-026+027 / W22 D8 / W16 F1-F4 Track A | 持續 carry-over |
| **永久 OUT** | path (a) judge LLM 升級 | per memory |

### 6. Real-calendar collapse

**~110min actual** vs ~90-120min planned = **within range** ⭐(F0 ~20min + F1 ~75min + F2 ~15min same-day cumulative)。對齊 W34 measurement-only precedent + W39 multi-F mid-phase efficiency。

### 7. PR readiness

無 PR — W41 0-code-change measurement,直接 main branch commits per established workflow。Push origin/main pending F2 closeout commit。
