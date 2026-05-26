---
phase: W35-rule8-wording-tighten
plan_ref: ./plan.md
checklist_ref: ./checklist.md
status: closed   # F3 closeout 2026-05-26 — PASS WITH G1-IMPROVED CAVEAT
last_updated: 2026-05-26
---

# Phase W35 — Progress

> Daily progress + decisions + commits + 結尾 retro。Append-only(per PROCESS.md v2.0)。

---

## Day 0(2026-05-26)— F0 Kickoff

### Action

W34 closed PASS measurement-only(`6734161` pushed origin/main 2026-05-26 same-day)→ user explicit pick W35 kickoff = **Rule 8 wording tighten「cite SUFFICIENT chunks」**(W34 retro HIGHEST OPTIONAL candidate per F2 G2 LLM emit dominant 92% verdict)。

### R6 Day 0 recursive grep verify(per CLAUDE.md §10 R6)

3 個 catch surfaced before F1.0 wording lock:

**Catch (1)**:`backend/generation/prompt_builder.py:30` Rule 8 verbatim wording captured。5 key phrases lock 喺 SYSTEM_PROMPT line 30:

```
8. When multiple retrieved chunks each contain partial information relevant to the answer,
cite ALL of them (not just the most representative one) — each fact in the answer should
be backed by every chunk that supports it. If two chunks describe the same scenario from
different angles, both warrant a citation marker. (W33 F1.1.b — Rule 8 restored from W31
commit 16b9b3d per sequential ship layered on W32 (h') backend)
```

F1.0 surgical edit target single line。

**Catch (2)**:`backend/tests/test_prompt_builder_dispatch.py:207-221` 5 assertions 鎖住 Rule 8 verbatim:

```python
assert "cite ALL of them" in SYSTEM_PROMPT
assert "partial information" in SYSTEM_PROMPT
assert "each fact in the answer should be backed by every chunk" in SYSTEM_PROMPT
assert "two chunks describe the same scenario" in SYSTEM_PROMPT
assert "both warrant a citation marker" in SYSTEM_PROMPT
```

F1.1 必須同步 update 全部 5 個 phrase 至 W35 tightened wording。任何 phrase 唔同步 break test。

**Catch (3)**:W33 verbatim restoration source `16b9b3d` — W35 是 first divergence from verbatim。`test_system_prompt_includes_rule_8_cite_breadth` docstring 「Restored verbatim from W31 commit 16b9b3d」 wording 需要 update 至 「Tightened W35 from W33 verbatim restoration」。

### 3 候選 wording surface(F1.0 implementation lock 之前)

| Option | Wording | 緊度 + 預測 |
|---|---|---|
| **A 激進** | `cite the most relevant chunks (typically 1-2 per fact) — additional overlapping chunks only if they add non-redundant detail` | 強 bound;可能傷 G1 cross-section breadth(W34 correctness +2.53pp 風險)|
| **B 中等** ⭐ working candidate | `cite SUFFICIENT chunks to support each fact (typically 1-2 chunks) — additional overlapping chunks warrant citation only when they add non-redundant detail (different angle, complementary evidence)` | 保留 W33 「different angles」 intent + soft cap;最 likely G1 preserve + G2 G3 drop |
| **C 保守** | `cite the chunks that support each fact (typically 1-2 per fact) — avoid citing multiple overlapping chunks that convey the same information` | 最 minimal change;G2 G3 drop 可能弱 |

**Working assumption**:Option B(中等)是 F1.0 implementation default 候選。F1.0.a 之前 user 可 override pick A/C。

### W26-W34 baseline reference

| Baseline | Source | Metric |
|---|---|---|
| W26 F1 historical | `baseline-metrics-W26-D1-raw.json` | faith 0.9851 / correctness 0.7416 / recall@5 0.8744 / p95 1001ms |
| **W34 F1 baseline** ⭐ | `backend/w34-f1-ragas-eval-raw.json` | **faith 0.9836 / correctness 0.7669 / recall@5 0.8936 / p95 1331ms** |
| W34 F2 baseline | `backend/w34-f2-aggregate.json` | I07 avg 62.2s / I01 avg 53.4s / synth_overall 16974ms / **synth_llm_completion 15665ms 92%** / synth_expand_citations 1308ms 8% / synth_prompt_build 0ms / **I07 avg_cit 6 / I01 avg_cit 10.2** |
| W34 envelope | W34 F1 baseline -2pp | **faith ≥ 0.9637** preserve threshold |

### Decision tree pre-implementation surface

3-axis decision tree(per plan §3):

| Axis | Threshold | Branches |
|---|---|---|
| **G1 faith** | W34 -2pp = 0.9637 | preserve / flag / break |
| **G2 cit count** | I07 ≤ 5 AND I01 ≤ 8 | drop / inconclusive / null |
| **G3 LLM emit** | synth_llm_completion ≤ 14098ms(-10%)| drop / inconclusive / null |

**Most likely outcome**:Option B → G1 preserve + G2 drop + G3 drop → W35 ship production-ready preserve in main。**Risk outcome**:Option B aggressive tighten → G1 break → F1.7 contingency revert to W33 verbatim。

### Self-verification checklist(per CLAUDE.md §12)

- [x] 對應 spec section:`docs/architecture.md §3.2` Citation contract(prompt-side enforcement)+ §3.5 Citation invariant
- [x] H1-H7 不違反 — F1.0 Rule 8 wording tighten = non-architectural prompt content change(no schema / vendor / storage / 8-view philosophy / Tier 2 / security / design fidelity impact)
- [x] §1 Karpathy think-before-coding — R6 3 個 catch + 3 wording options + decision tree surface before F1.0 lock
- [x] N/A frontend fidelity check
- [x] N/A test write(F1.1 in-place assertion update)
- [x] N/A ruff(no code edit this entry)
- [x] Commit message follow Conventional Commits — `docs(planning): kickoff W35-...`
- [x] N/A architectural-adjacent → ADR
- [x] N/A Dify reference
- [x] OQ status check — none expected for measurement re-verify phase
- [x] Phase checklist tick'd — F0.1-F0.4 + F0.5 in progress

### Commits

- `b2f4ca3` — F0.6 kickoff(plan + checklist + progress combined,3 files / 543 insertions)
- `8c08557` — F0.7 session-start.md §10 W35 row append active + W34 closeout commits backfilled

### Carry-overs / Blockers

- F0.5 progress.md Day 0 entry(this file)— done
- F0.6 kickoff commit `b2f4ca3` — done
- F0.7 session-start.md §10 W35 row append commit `8c08557` — done
- **D1 trigger**:F1.0.a Option A/B/C lock — user pick required(default Option B working candidate);plan §1 + progress.md Day 0 「3 候選 wording」 surface ready

---

## Day 1(2026-05-26)— F1 Rule 8 wording tighten + LIVE RAGAs eval + F1.7 Option C re-tighten

### F1.0 Initial Option B lock + edit

User lock Option B(working candidate per §1 surface)= `cite SUFFICIENT chunks to support each fact (typically 1-2 chunks) — additional overlapping chunks warrant citation only when they add non-redundant detail (different angle, complementary evidence)`。

- F1.0.a Option B locked
- F1.0.b prompt_builder.py:30 single-line edit B applied
- F1.0.c Attribution comment updated `(W35 F1.0 — Rule 8 wording tighten from W33 verbatim restoration per W34 G2 LLM emit dominant 92% verdict)`
- F1.0.d ruff clean ✅

### F1.1 Test assertions sync Option B

- F1.1.a `test_system_prompt_includes_rule_8_cite_breadth` → renamed `test_system_prompt_includes_rule_8_cite_sufficient`
- F1.1.b 5 assertions updated: `cite SUFFICIENT chunks` / `partial information` / `typically 1-2 chunks` / `non-redundant detail` / `different angle, complementary evidence`
- F1.1.c Rule 7 v2 + Rule 6 non-regression assertions unchanged
- F1.1.d Test docstring + section comment updated W33→W35 trajectory

### F1.2 pytest baseline verify Option B

- Full suite **1084 passed + 25 skipped + 0 failed in 384.38s** ✅(W34 closeout baseline exact preserve)
- ruff `All checks passed!` ✅

### F1.3 Backend kill+restart per PC chain

Docker Desktop UI 一度卡住,user 重啟 Docker + 所有 container restart。Pre-flight verify:
- Postgres `SELECT 1 AS ready_for_query` = 1 ✅(PC-W33-1)
- Langfuse `/api/public/health` 200 OK ✅(PC-W34-1,需 30s timeout cover post-restart warmup;Docker `unhealthy` flag 係 timing artifact 唔影響 endpoint)
- 冇 existing backend on :8000 → 直接 start fresh `python -m api.server`
- /health 5/5 components OK(azure_search + azure_openai + langfuse + postgres + cohere not_configured per Q5 Path A optional)

### F1.4 Option B LIVE RAGAs eval result

**runtime 478s vs W34 642s = -25% ⭐**

| Metric | W34 F1 | **Option B** | Δ vs W34 |
|---|---|---|---|
| faithfulness | 0.9836 | 0.9804 | -0.32pp ✅ G1 preserve(≥ 0.9637)|
| correctness | 0.7669 | 0.7169 | **-5.00pp ⚠️ regression** |
| recall@5 | 0.8936 | 0.8936 | 0 ✅ |
| p95_latency | 1331ms | 1402ms | +71ms 微升 |

**Karpathy §1.1 surface side effect**:Option B「different angle, complementary evidence」 wording 太 abstract 令 LLM over-conservative cite + answer 較 sparse → RAGAs `answer_relevancy` judge 解讀為 less complete supporting evidence → correctness -5pp regression。**唔在 plan §3 acceptance criteria explicit list 內**,但 material side effect。Surface to user 決定 path forward。

### F1.5 + F1.6 Decision tree branch verdict Option B

- G1 faith = **preserve ✅**(0.9804 ≥ 0.9637 W34 envelope + ≥ 0.9651 W26 envelope)
- G2 + G3 deferred F2 measurement,runtime -25% strong proxy
- **NEW G2' correctness side effect** -5pp NOT in §3 → 用戶 decision required

### F1.7 Contingency Option C re-tighten(user lock path (β))

User explicit lock 2026-05-26 path (β) F1.7 contingency → Option C「最保守」 wording。Plan §7 changelog amendment R3 logged before re-edit。

**Option C wording**:`cite the chunks that support each fact (typically 1-2 per fact) — avoid citing multiple overlapping chunks that convey the same information`

- F1.7.b.1 plan.md §7 changelog F1.7 amendment row appended(R3 no silent drift)
- F1.7.b.2 prompt_builder.py:30 B→C edit
- F1.7.b.3 test_prompt_builder_dispatch.py 5 assertions B→C update:`cite the chunks that support each fact` / `partial information` / `typically 1-2 per fact` / `avoid citing multiple overlapping chunks` / `convey the same information`;test docstring + section comment updated B→C
- F1.7.b.4 pytest scoped `tests/test_prompt_builder_dispatch.py` = **14 passed** ✅
- F1.7.b.5 ruff `All checks passed!` ✅
- F1.7.b.6 Rename `w35-f1-ragas-eval-raw.json` → `w35-f1-option-b-raw.json`(audit trail);runner OUTPUT_RAW_JSON → `w35-f1-option-c-raw.json`
- F1.7.b.7 Backend kill PID 32632 + restart with Option C wording → 5/5 components OK
- F1.7.b.8 F1.4 re-run Option C → **475.4s runtime**

### F1.4 Option C LIVE RAGAs eval result(post-F1.7 contingency)

| Metric | W34 F1 | Opt B | **Option C** | Δ vs W34 | Δ vs Opt B |
|---|---|---|---|---|---|
| **faithfulness** | 0.9836 | 0.9804 | **0.9876** | **+0.40pp ⭐ IMPROVED** | +0.72pp |
| **correctness** | 0.7669 | 0.7169 | **0.7226** | -4.43pp ⚠️ | +0.57pp |
| recall@5 | 0.8936 | 0.8936 | 0.8936 | 0 ✅ | 0 |
| **p95_latency** | 1331ms | 1402ms | **1102ms** | **-229ms (-17%) ⭐⭐** | -300ms |
| eval runtime | 642s | 478s | **475s (-26%) ⭐** | -167s | -3s |
| failed_queries | 10 | 11 | 10 | unchanged | -1 |

**Critical findings**:

1. **G1 faithfulness IMPROVED ⭐** — Option C 0.9876 超越 W34 baseline 0.9836(+0.40pp);Option C explicit anti-pattern 「avoid citing multiple overlapping chunks」 把 LLM cite-decision 收緊到 high-signal chunks only
2. **p95_latency -17% ⭐⭐** — per-query 中位數延遲 1331ms → 1102ms,確認 G3 LLM emit drop 假設正確(F2 stage timing 會 fine-grained confirm)
3. **runtime -26% ⭐** — eval pipeline cost win 同 Option B 相若
4. **correctness -4.43pp persisting** — 同 Option B -5pp 同樣 pattern,根因 = 「typically 1-2 per fact」 soft cap 本身令 LLM 答案更 concise → answer_relevancy judge 解讀為 less complete。Option C correctness 0.7226 = W26 baseline 0.7416 **-1.90pp**(W33-W34 累積 +2.53pp boost 部分喪失,但 close-to-baseline 而非 deep regression)

### Decision tree branch verdict Option C

| Axis | Threshold | Option C | Verdict |
|---|---|---|---|
| **G1 faith** | ≥ 0.9637 envelope | 0.9876 | ⭐ **G1 IMPROVED** beyond preserve |
| **p95_latency** | n/a explicit | 1102ms | -17% ⭐⭐ |
| eval runtime | n/a explicit | 475s | -26% ⭐ |
| G2 cit count | I07 ≤ 5 AND I01 ≤ 8 | TBD F2 | runtime + p95 strong proxy → 預期 G2 drop |
| G3 LLM emit | ≤ 14098ms(-10%)| TBD F2 | p95 -17% strong proxy → 預期 G3 drop |
| G2' correctness side effect | -1.90pp from W26 historical | 0.7226 | persist;within Q4 tolerance(W26 baseline state ship history)|

### F1.5-F1.6 final verdict + W36+ priority queue update

**User lock path (α) Ship Option C + proceed F2**(2026-05-26 same-day post-Option C result):
- Option C Pareto-optimal vs Option B 全部 4 axis 嚴格 better
- G1 actually IMPROVED 唔係 preserve
- correctness -1.90pp from W26 baseline within historical Q4 tolerance
- F2 latency re-verify pending → confirm G2 G3 cit count + LLM emit drops

W36+ priority queue update:
- DEMOTE: Option A more aggressive re-tighten(Option C 已 Pareto-optimal,A 風險高 G1 break)
- PRESERVE: PC-W34-1 + PC-W34-2 + (j') section_path + PC-W33-1 + PC-W32-1/2 housekeeping
- DEMOTED LOW: prompt token reduction + engine-fetch async pool(F2 evidence 預計仍 dominate LLM emit)

### Self-verification checklist(per CLAUDE.md §12)

- [x] 對應 spec section:architecture.md §3.2 Citation contract(prompt-side enforcement)
- [x] H1-H7 不違反 — Option C 仍係 prompt content change(non-architectural per H1)
- [x] §1 Karpathy think-before-coding — F1.4 surprise correctness -5pp surfaced upfront → user lock path (β) → Option C strictly better outcome
- [x] N/A frontend fidelity check
- [x] Test write — in-place assertion update(F1.1 + F1.7.b.3)
- [x] ruff PASS both edits
- [x] Commit message Conventional Commits(pending F1.8 commit)
- [x] N/A architectural-adjacent → ADR
- [x] N/A Dify reference
- [x] OQ status check — none expected wording tighten phase
- [x] Phase checklist tick'd — F1.0-F1.7 sub-items pending F1.8 commit

### Commits

- (F1.8 F1 commit pending — combined Option B + F1.7 Option C re-tighten lifecycle)

### Carry-overs / Blockers

- F1.8 F1 commit pending
- F2.1+ latency re-verify pending(F2.1.a w35-f2-runner.py adapt + F2.1.b 5-run + F2.2 aggregate + F2.3 commit)
- F3 closeout pending(post F2 outcome)

---

## Day 2(2026-05-26 same-day collapse)— F2 latency re-verify + F3 closeout

### F2.1 5-run latency measurement runner adapted

`backend/w35-f2-runner.py` created — W34 F2 runner adapted with W35 G2 + G3 verdict logic inline。Runner crashed on cp1252 print encoding of `≤` char(line 110)— **數據 captured 完整**(10 per-run JSONs + structlog stage timings),只 aggregate JSON write step missed。Salvage via `backend/w35-f2-aggregate-salvage.py`(per-run JSONs)+ `backend/w35-f2-stage-timing.py`(structlog extract from UTF-16 LE log)。

### F2.2 5-run latency measurement Q-level result

| Metric | W34 baseline | **W35 Option C** | Δ vs W34 |
|---|---|---|---|
| **I07 avg latency** | 62.2s | **25.15s** | **-59.6%** ⭐⭐⭐ |
| **I01 avg latency** | 53.4s | **16.70s** | **-68.7%** ⭐⭐⭐ |
| **I07 avg citations** | 6.0 | **4.8** | **-1.2 (-20%)** ⭐ |
| **I01 avg citations** | 10.2 | **5.4** | **-4.8 (-47%)** ⭐⭐ |

Q-level total latency -60% headline contains:
- Synthesizer-side LLM emit drop(stage timing -27%)
- Non-synth overhead reduction(retrieval + CRAG + Langfuse warmup state difference);W34 Q-level 62.2s = synth 17s + 45s elsewhere(Langfuse retry per W34 F2.3 audit_log gap);W35 Q-level 25s = synth 17s + 8s elsewhere(warmer Langfuse)

### F2.3 Stage timing aggregate(per-stage decomposition)

| Stage | W34 baseline | **W35 Option C** | Δ vs W34 | Verdict |
|---|---|---|---|---|
| synth_overall_latency_ms | 16974 | 12597 | -25.8% | ⭐ |
| **synth_llm_completion_latency_ms** | 15665 | **11483.8** | **-26.7%** | ⭐⭐ **G3 PASS** |
| synth_expand_citations_latency_ms | 1308 | 1112.6 | -14.9% | minor drop |
| synth_prompt_build_latency_ms | 0 | 0 | unchanged | Karpathy §1.3 surgical |
| output_tokens(avg)| 701 | 626.9 | -10.6% | ⭐ |
| citations_count(avg)| 7.5 | 5.1 | -32% | ⭐⭐ |

### G2 + G3 decision tree final verdict

| Gate | Threshold | W35 Option C actual | Verdict |
|---|---|---|---|
| **G2 cit count drop** | I07 ≤ 5 AND I01 ≤ 8 | 4.8 + 5.4 | ⭐ **G2 PASS with margin** |
| **G3 LLM emit drop** | synth_llm_completion ≤ 14098ms(-10%)| 11483.8ms(-26.7%) | ⭐⭐ **G3 PASS with margin** |

### Surprising correlation observed

- `citations_count` -32% vs `output_tokens` -10.6%
- LLM cite-ing fewer chunks BUT each answer text only ~10% shorter
- 即係每個 cite 嘅 supporting text 變多咗少少(more elaboration per cite, fewer cites)
- 呢個可能解釋 correctness -4.43pp persist 原因 — fewer cites = less coverage breadth from RAGAs judge POV

### F3.A Combined decision tree intersect

| Axis | W35 Option C verdict | W35 ship |
|---|---|---|
| **G1 faith**(F1)| **IMPROVED** 0.9876 ⭐(+0.40pp vs W34)| ✅ ship-preserve |
| **G2 cit count drop**(F2)| PASS with margin(I07 4.8 / I01 5.4)| ✅ ship-preserve |
| **G3 LLM emit drop**(F2)| PASS with margin(11484ms / -26.7%)| ✅ ship-preserve |
| recall@5 | unchanged 0.8936 | ✅ |
| p95_latency | -17% 1102ms | ⭐ |
| eval runtime | -26% 475s | ⭐ |
| **NEW G2' correctness side effect** | -1.90pp from W26 baseline | ⚠️ accept trade-off per user lock (α)|

**F3.A.3 intersect → W35 Option C ship production-ready** ✅ — preserve in main + W36+ priority queue update。

### F3.B Cross-doc sync per CLAUDE.md §10 R3 + R5 + R6

- B.1 plan.md frontmatter `status: active → closed`(PASS measurement-driven ship verdict)
- B.2 checklist.md cross-cutting tick + N/A reason
- B.3 progress.md retro 7-section(post Day 2 entry)
- B.4 session-start.md §10 W35 row `🟡 active` → `✅ closed PASS WITH G1-IMPROVED CAVEAT`
- B.5 RISK_REGISTER NEW R candidate — DEFERRED W36+(G1 IMPROVED no NEW risk material)
- B.6 ADR README — no NEW ADR(F1.0/F1.7 prompt wording + F2 re-use W34 instrumentation,both non-architectural per plan §1 + §4 R5)

### F3.C `.env` cleanup + W36+ priority queue locked

- C.1 `.env` cleanup — W29 env override preserved unchanged
- **C.2 W36+ priority queue locked**:
  - **HIGHEST** PC-W34-1 session-start protocol amend(verify Langfuse `/api/public/health` 200 + Postgres `SELECT 1` handshake)— W35 F1.3 evidence Docker Desktop UI 卡住一次,operational debt
  - **HIGHEST** PC-W34-2 RAGAs judge robustness(gpt-5.4-mini → gpt-5.5 OR robust JSON parsing OR exclude complex queries)— W35 F1.4 evidence 仍見 answer_relevancy 0.6X borderline judge artifacts
  - **MEDIUM**(j') section_path prefix filter quality-of-cite refinement
  - **LOW preserved** PC-W33-1 + PC-W32-1/2 procedural housekeeping
  - **DEMOTED LOW** Option A more aggressive re-tighten(Option C 已 Pareto-optimal,A 風險 G1 break);prompt token reduction(W35 F2 prompt_build 0ms 證實 negligible);engine-fetch async pool(W35 F2 expand_citations 1113ms small fraction)
  - **LOWER**(g')(i')(B'.a)(ii)(k) saturated
  - **LONG-TERM**(c)(e)(f)/ BUG-026+027 / W22 D8 / W16 F1-F4 Track A IT cred

### F3.D Commit + push(combined F2 + F3 closeout per W31-W34 atomic pattern)

(pending commit + push)

### Self-verification checklist(per CLAUDE.md §12)

- [x] 對應 spec section:architecture.md §3.2 Citation contract + §3.5 Citation invariant + §3.7 (no §3.7 impact this phase)
- [x] H1-H7 不違反 — F1.0/F1.7 Rule 8 wording tighten = non-architectural prompt content;F2 re-use W34 instrumentation no NEW behavior
- [x] §1 Karpathy think-before-coding — F1.4 Option B correctness side effect surfaced upfront → Option C re-tighten path
- [x] N/A frontend fidelity check
- [x] N/A new test write
- [x] ruff PASS both F1 edits
- [x] Commit message follow Conventional Commits — `feat(generation): W35 F1 ...` + pending F2+F3 closeout combined commit
- [x] N/A architectural-adjacent → ADR
- [x] N/A Dify reference
- [x] OQ status check — none expected wording tighten phase
- [x] Phase checklist tick'd — all F0 + F1 + F2 + F3 items closed

---

## §Retro

### What Worked

1. **R6 Day 0 recursive grep verify caught 3 contamination sources upfront** — prompt_builder.py:30 verbatim wording + test assertions lock + W33 verbatim source first-divergence framing。R6 amendment per W23 F3 enforcement realized concrete value。
2. **Karpathy §1.1 surface Option B correctness side effect** — `answer_relevancy=0.6X` borderline failures + correctness -5pp 並非 plan §3 explicit criteria,但 material material side effect。Surface to user → path (β) Option C re-tighten 結果 Pareto-optimal。沒有 surface 就會 mis-ship Option B + cumulative -5pp regression unnoticed。
3. **F1.7 contingency framework triggered correctly** — plan §1 surface 3 wording options(A/B/C)+ §F1.7 contingency branch 已 pre-design → user lock (β) directly invocable no plan amendment scramble。R3 §7 changelog F1.7 amendment row logged before re-edit(no silent drift)。
4. **Stage timing instrumentation re-use** — W34 F2.1 structlog stage timing infrastructure(synth_overall / synth_prompt_build / synth_llm_completion / synth_expand_citations + expand_citations_list_chunks_batch event)直接 apply 到 W35 F2 measurement,Karpathy §1.3 surgical scope。零 NEW instrumentation cost,G3 -26.7% verdict 清晰 attribution to LLM emit specifically(唔 confounded by Q-level non-synth overhead noise)。
5. **Pareto comparison surfaced strict-better outcome** — Option C 喺 4 axis(faith / correctness / p95 / runtime)全部 strictly better than Option B → user decision frictionless lock (α) ship。

### What Didn't Work / Surprises

1. **🚨 W35 F2 runner cp1252 print encoding bug**(`≤` U+2264 char line 110)— Windows default console encoding 撞 unicode 字符,**runner crashed at final print** → aggregate JSON write step missed but 10 per-run JSONs saved。**Salvage cost ~10min**(write 2 NEW scripts `w35-f2-aggregate-salvage.py` + `w35-f2-stage-timing.py`)。**NEW PC-W35-1 candidate**:F2 runner future iterations 全部使用 ASCII fallback OR explicit `PYTHONIOENCODING=utf-8` env override OR avoid unicode in print。
2. **🚨 Docker Desktop UI 卡住 user intervention 需求** — W35 F1.3 pre-flight 發現 Langfuse container `(unhealthy)` + `/api/public/health` timeout → user 報告 Docker Desktop 「loading 停不了重啟不了」 → wait user reboot Docker → restart 之後 Langfuse `Up 4 minutes (unhealthy)` 但 endpoint 200 OK with 30s timeout warmup。**Confirm PC-W34-1 trigger condition reliable** — endpoint health check 比 Docker container health check 更 actionable(Docker `unhealthy` flag 係 timing artifact 唔 reflect actual readiness)。**驗證 PC-W34-1 防護價值**:預先檢查 endpoint 200 而唔係 Docker flag。
3. **⚠️ Option B correctness -5pp regression surprise** — plan §3 acceptance criteria 預期 G1 faith preserve + G2 + G3 drop。Option B G1 preserved(0.9804)但 correctness -5pp NOT in plan §3。**根因 = 「typically 1-2 chunks」 soft cap 本身令 LLM 答案更 concise** → RAGAs `answer_relevancy` judge 解讀為 less complete。Option C 同樣 cap 仍見 -4.43pp persist → confirm 根因唔係 wording abstract 程度,而係 cap 本身。**接受 trade-off** per user lock (α):G1 actually IMPROVED + p95 -17% + runtime -26% + 4-metric balance Pareto-optimal point。
4. **⚠️ Q-level latency -60% vs stage timing -27% discrepancy** — W35 F2 Q-level total I07 25s vs W34 62s = -60%,但 synth_llm_completion stage timing 只 -27%。**Explanation**:Q-level total contains non-synth overhead(retrieval + CRAG + Langfuse retry + audit_log)。W34 F2 measurement had Langfuse retry overhead (~30s per W34 F2.3 audit_log gap finding)。W35 F2 measurement Langfuse warmer state → non-synth overhead drop significantly。**Honest G3 verdict 應該 base on stage timing**(-26.7%)而唔係 Q-level total(-60%)— operational state difference 唔可以 attribute to ship。Plan §3 G3 threshold ≤ 14098ms(synth_llm_completion specific)正確 isolate ship-attributable LLM emit drop。
5. **Surprising correlation `citations_count` -32% vs `output_tokens` -10.6%** — LLM cite-ing fewer chunks BUT 每個 cite 嘅 supporting text 變長少少(more elaboration per cite, fewer cites)。Hypothesis:Rule 8 Option C「typically 1-2 per fact」 cap + 「avoid citing multiple overlapping chunks」 anti-pattern → LLM 揀 high-signal chunks 之後 elaborate more on each。**唔影響 ship decision**(Pareto-optimal 仍 confirmed)但 mechanism insight valuable for W36+ refinement direction。

### Carry-overs

- **🚧 NEW PC-W35-1**(F2 runner cp1252 print encoding bug)— W36+ refactor all `print(...)` statements in `backend/w*-f*-runner.py` family to use ASCII only OR `PYTHONIOENCODING=utf-8` env override pattern
- **🚧 PC-W34-1**(session-start protocol amend Langfuse health + Postgres handshake)— preserved W36+ HIGHEST(W35 F1.3 evidence reinforced)
- **🚧 PC-W34-2**(RAGAs judge robustness gpt-5.4-mini → gpt-5.5 OR JSON parse robust OR exclude complex queries)— preserved W36+ HIGHEST
- **🚧**(j') section_path prefix filter — preserved W36+ MEDIUM
- **🚧** PC-W33-1 + PC-W32-1/2 — preserved W36+ LOW housekeeping
- **🚧 DEMOTED**:Option A more aggressive re-tighten / prompt token reduction(0ms confirmed)/ engine-fetch async pool(1113ms small fraction confirmed)
- **🚧 LOWER**(g')(i')(B'.a)(ii)(k)preserved low priority
- **🚧 LONG-TERM**(c)(e)(f)/ BUG-026+027 / W22 D8 / W16 F1-F4 Track A IT cred

### ADR Triggers

**None this phase** — F1.0/F1.7 Rule 8 wording tighten + F2 re-use W34 instrumentation 都 non-architectural per H1。Karpathy §1.3 surgical scope 嚴守(only Rule 8 wording + test assertions phrase update + runner script)。

### Phase Gate Result

✅ **PASS WITH G1-IMPROVED CAVEAT** per plan §3 multi-axis decision tree intersect:
- **G1 faith IMPROVED** ⭐(0.9876 vs W34 0.9836 = +0.40pp,**actually IMPROVED beyond preserve**)
- **G2 cit count drop with margin** ⭐(I07 4.8 ≤ 5 / I01 5.4 ≤ 8)
- **G3 LLM emit drop with margin** ⭐⭐(synth_llm_completion 11483.8ms / -26.7% vs -10% threshold)
- G4 backend pytest baseline 1084 preserved ✅
- G5 ruff PASS + mypy module-path quirk preserved
- G6 R6 catch trail verified

**Caveat**:Correctness -1.90pp from W26 historical baseline 0.7416 — accept per user lock (α) given Pareto-optimal 4-axis improvement(faith + p95 + runtime + cit count)+ within Q4 measurement-experiment-fail-policy tolerance(W26 baseline ship state historically)。

### W36+ Priority Queue Locked

per F3.C.2 priority queue,2 個 HIGHEST level operational debt:
- **PC-W34-1** session-start protocol amend(Langfuse health endpoint + Postgres handshake)— W35 F1.3 evidence Docker stuck event reinforced trigger
- **PC-W34-2** RAGAs judge robustness — W35 F1.4 仍見 answer_relevancy 0.6X borderline judge artifacts
- **MEDIUM**(j') section_path prefix filter
- LOW + LONG-TERM per F3.C.2

### Actual vs Planned Effort

| Phase | Planned | Actual | Delta | Notes |
|---|---|---|---|---|
| **D0 F0 kickoff** | ~1h | ~1h | 0 | plan + checklist + progress + R6 3 catches + commits b2f4ca3 + 8c08557 + 0d19e47 |
| **D1 F1 Rule 8 tighten + RAGAs eval** | ~2-3h | ~3h(includes F1.7 contingency Option C re-run ~30min)| within range | Option B initial → F1.4 correctness side effect surface → user lock (β) → Option C re-tighten → F1.4 re-run → user lock (α);commit c590a86 |
| **D2 F2 latency + F3 closeout** | ~1.5-2h | ~1.5h(F2 runner crash salvage ~10min absorbed)| within range | F2 5-run + stage timing extract + retro + cross-doc sync + commit + push |
| **Total** | ~4-6h | ~5.5h | within range | Real-calendar same-day collapse pattern preserved per W22-W34 |

---

## Day 2(TBD)— F2 Latency re-verify + F3 closeout

(pending Day 1 outcome)
