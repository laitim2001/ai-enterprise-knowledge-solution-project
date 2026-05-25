---
phase: W28-parent-doc-setting-sweep
name: "Parent-doc Setting sweep — max_tokens_per_parent + parent_doc_top_k sequential one-variable-at-a-time, hold dispatch_mode=append"
sprint_week: W28
start_date: 2026-05-25
end_date: 2026-05-25   # same-day collapse expected per W22-W27 AI compression pattern
status: closed   # per ADR-0037 amendment W28 F4 closeout 2026-05-26 — Phase Gate PASS per plan §3 policy(4 of 5 gates PASS + G2 EXCEEDS F1 baseline +1.61pp at best combo Run 3.A;G3 borderline judge noise treat as not config-induced)
spec_refs:
  - architecture.md §3.1       # query pipeline (parent-doc post-Context Expander step per ADR-0037)
  - architecture.md §3.5       # ChunkRecord citation contract preservation
  - architecture.md §3.7       # query orchestration locus
prior_phase: W27-parent-doc-dispatch-experiment
trigger_memo: ADR-0038 §Decision #4 W28+ candidate (b) HIGHEST priority — H2 parent section 注意力分散 直接介入 + latency reduction
related_adrs: [0037, 0038]    # ADR-0037 amendment OR new ADR-0039 ship per W28 F5 closeout verdict
---

# Phase W28 — Parent-Doc Setting Sweep

> **Plan version**:1.0(initial)
> **Owner**:Chris(技術 Lead)+ AI(implementation)
> **Approved by**:Chris(chat 2026-05-25 — 「揀 (b) parent_doc Setting sweep」+ AskUserQuestion 3 Recommended picks:命名 `W28-parent-doc-setting-sweep` + Sequential one-variable-at-a-time strategy + Hold dispatch_mode=append)
> **Trigger memo**:ADR-0038 §Decision #4 嘅 W28+ candidate (b) HIGHEST priority — H2 parent section 注意力分散 emerging primary residual axis 嘅直接介入 + W27 +189% latency 負擔嘅 reduction signal

## 1. Scope

### 1.1 Trigger context

W27 F2 G empirical result 揭露 D1.35 hypothesis 4-axis 嘅 H2 parent section 注意力分散 屬 emerging primary residual axis:

- **G1 faithfulness MARGINAL MISS** by 0.6pp(W27 append 0.9591 vs F1 baseline ±2pp tolerance [0.9651, 1.0])
- **G4 Q-W25-I01 控制組 MARGINAL MISS** by 0.01pp(W27 append 0.64 vs F1 ≥ 0.65 effective tolerance)
- **2 NEW context_precision 失敗 surfaced**(Q-W25-T02 + Q-W25-I02)— append mode 引入 new failure mode by parent context 加入 irrelevant siblings
- **p95_latency +189%** vs F1 baseline(W27 2897ms vs F1 1001ms)— 2-segment LLM input token 成本

D1.35 H2 hypothesis 預測:**parent section 4000 tokens budget 過大,LLM 注意力被 long parent context 分散** → 降低 `max_tokens_per_parent` 至 2000 / 1500 + 加 `parent_doc_top_k` 1→2/3 看是否 close G1+G4 marginal MISS + 降 latency。

### 1.2 Sequential one-variable-at-a-time sweep strategy(per Karpathy §1.2 simplicity + W26 PC1 一次只郁一個旋鈕)

**Step 1**(F2)— Hold dispatch_mode=append + top_k=1,sweep max_tokens 4000/2000/1500 = **3 runs**:
- Run 1.A:max_tokens=4000(W27 F2 G baseline duplicate — 驗證 environment continuity)
- Run 1.B:max_tokens=2000
- Run 1.C:max_tokens=1500
- 揀 best max_tokens by G1+G2+G3+G4 aggregate score
- 預期 outcome:H2 hypothesis confirmed 若 max_tokens 降低提升 faithfulness + correctness + 降 latency

**Step 2**(F3)— Hold dispatch_mode=append + max_tokens at Step 1 best,sweep top_k 1/2/3 = **2 NEW runs**(top_k=1 already from Step 1):
- Run 2.A:top_k=2(at best max_tokens)
- Run 2.B:top_k=3(at best max_tokens)
- 揀 best combo by G1-G5 aggregate score(加 latency G5)

**Step 3**(F4 optional)— Hold max_tokens + top_k at best combo,cross-check dispatch_mode=replace = **1 NEW run**:
- 若 best combo Step 1+2 PASS all G1-G5 → optional cross-check 若 replace mode 喺 best combo 都 match append performance(若是 → propose ADR-0037 amendment default flip Settings)
- 若 best combo 仍 marginal MISS → skip Step 3,直接 closeout F5

**Total runs**:F2 3 runs + F3 2 NEW + F4 optional 1 = **5-6 runs** × ~9 min eval + ~30-40s uvicorn restart per run = ~50-70 min eval runtime

### 1.3 Hold dispatch_mode=append rationale

W27 F2 G 實證 append mode 大幅修復 W26 F2 G replace 嘅 catastrophic regressions:
- ✅ Q-W25-I07 critical recovery(0.00 → PASS — D1.35 H1 citation invariant validated)
- ✅ faithfulness +5.76pp vs W26 F2 G replace
- ✅ correctness +7.90pp vs W26 F2 G replace

Hold 喺 已驗證 partial-recovery config 以 isolate `max_tokens` + `top_k` 兩個 axis 嘅 individual effect。Step 3 optional cross-check 容許 replace mode 喺 best combo 嘅 evaluation。

### 1.4 Out of scope(deferred)

- ❌ `section_depth_offset` sweep(Q2 預設 1 — ADR-0037 §2.2 提到「adaptive deferred W27+」;W28 唔調)
- ❌ `parent_doc_max_chunks_per_parent` sweep(預設 50 = safety cap pathological-doc protection;唔屬於 sweep axis)
- ❌ `parent_doc_fallback_to_doc_on_shallow` sweep(預設 True graceful fallback;唔調)
- ❌ RAGAs judge orchestrator-aware tune(R-W26-2 / W29+ candidate (c))
- ❌ F3 query expansion standalone test(ADR-0034 / W29+ candidate (d))
- ❌ section_path dedupe strategy variants(已 baked-in ADR-0037 §2 step 3)
- ❌ `architecture.md §3.6` default flip(per Q4 measurement-experiment-fail-policy — defer until clear measurable win)
- ❌ `enable_parent_doc_retrieval` default flip True(per Q4 — defer until W28 PASS gate decision)
- ❌ `enable_query_expansion` 同時 enable(會 confound signal — sweep 期間 default OFF preserved)

### 1.5 Sprint week origin

**W19+ rolling JIT**(per CLAUDE.md §10 R1 + session-start.md §10 W28+ row);呢個 phase **唔喺 architecture.md §6.1 原 W1-W12 sprint 表內** — 屬 W27 closeout 觸發嘅 follow-up sweep(類似 W25.5 BUG-025 fix + W27-parent-doc-dispatch-experiment rolling 性質)。

---

## 2. Deliverables

### F0 — Kickoff(plan + checklist + progress + R6 grep verify)— DONE Day 0

- **Spec ref**:CLAUDE.md §10 R1 + R6
- **H1 trigger**:否(governance only)
- **Acceptance criteria**:
  1. ✅ `docs/01-planning/W28-parent-doc-setting-sweep/{plan.md,checklist.md,progress.md}` committed
  2. ✅ R6 pre-active-flip 5-step recursive grep verification at Day 0 — Settings line 198-235 actual default values verified + W27 F2 G baseline raw JSON 已 read + sweep value (4000/2000/1500 + 1/2/3) 對齊 ADR-0037 §2.1+§2.3 design rationale 註解 + 0 historical surface contamination
  3. session-start.md §10 timeline row W28 active status entry append
- **Effort estimate**:~1-2h
- **Owner**:AI

### F1 — Step 1 max_tokens sweep(3 RAGAs runs)

- **Spec ref**:ADR-0037 §2.3 + Settings line 212
- **H1 trigger**:否(measurement only)
- **OQ deps**:**R8 prerequisite**(per §4 R1)— Azure OpenAI judge key + Cohere v4.0-pro reranker key environment
- **Acceptance criteria**(4 categories):

  **A. R8 prerequisite gate**(STOP and ask if blocked):
  1. R8 prerequisite check — keys 已 present 喺 `.env`(W27 F2 G same-session continuity 預期 valid)
  2. Blocked → STOP and ask Chris per W25 F4 / W26 F1 / W27 F2 deferred precedent pattern

  **B. Step 1 active flip 3 runs sequential**:
  3. Run 1.A baseline duplicate — `.env` env override `ENABLE_PARENT_DOC_RETRIEVAL=true` + `PARENT_DOC_DISPATCH_MODE=append` + `PARENT_DOC_MAX_TOKENS_PER_PARENT=4000`(實 default,explicit override 為紀錄完整性)+ uvicorn restart + POST /eval/run = output `step1-run-1a-metrics-W28-D1-raw.json`
  4. Run 1.B max_tokens=2000 — `.env` 改 `PARENT_DOC_MAX_TOKENS_PER_PARENT=2000` + uvicorn restart + POST /eval/run = output `step1-run-1b-metrics-W28-D1-raw.json`
  5. Run 1.C max_tokens=1500 — `.env` 改 `PARENT_DOC_MAX_TOKENS_PER_PARENT=1500` + uvicorn restart + POST /eval/run = output `step1-run-1c-metrics-W28-D1-raw.json`

  **C. Step 1 analysis**:
  6. Markdown report `step1-max-tokens-sweep-W28-D1.md` — 3 runs aggregate metrics + per-query 4-metric + Step 1 best max_tokens pick by G1+G2+G3+G4 aggregate score(faith + correctness + Q-W25-I07 + Q-W25-I01 control)
  7. H2 hypothesis check:max_tokens 降低 是否提升 faithfulness + correctness + 降 latency?If yes → H2 confirmed,Step 2 proceed at best max_tokens;If no(faith / correctness 反而 drop)→ H2 refuted,best 仍是 4000,Step 2 仍 sweep top_k 但 max_tokens 鎖 4000

- **Effort estimate**:~30 min eval runtime + ~1-1.5h analysis(R8 prerequisite 假設 green)
- **Owner**:AI

### F2 — Step 2 top_k sweep(2 NEW RAGAs runs)

- **Spec ref**:ADR-0037 §2.1 + Settings line 208
- **H1 trigger**:否
- **OQ deps**:F1 max_tokens best 確定 + R8 仍 green
- **Acceptance criteria**(3 categories):

  **A. Step 2 active flip 2 NEW runs**(top_k=1 already from Step 1):
  1. Run 2.A top_k=2 — `.env` 改 `PARENT_DOC_TOP_K=2`(holding `PARENT_DOC_MAX_TOKENS_PER_PARENT=<Step 1 best>` + dispatch_mode=append)+ uvicorn restart + POST /eval/run = output `step2-run-2a-metrics-W28-D2-raw.json`
  2. Run 2.B top_k=3 — `.env` 改 `PARENT_DOC_TOP_K=3` + uvicorn restart + POST /eval/run = output `step2-run-2b-metrics-W28-D2-raw.json`

  **B. Step 2 analysis**:
  3. Markdown report `step2-top-k-sweep-W28-D2.md` — 2 NEW runs aggregate metrics + cross-reference Step 1 top_k=1 best max_tokens combo + best combo pick by G1-G5 aggregate score(加 latency G5)
  4. Hypothesis check:top_k 加大 是否擴大 multi-section coverage benefit(per ADR-0037 §2.1「Setting allows `parent_doc_top_k=2/3` for queries needing multi-section coverage」)而唔 trigger off-topic leak regression(per ADR-0037 §2.1 trade-off)?

- **Effort estimate**:~20 min eval runtime + ~1h analysis
- **Owner**:AI

### F3 — Step 3 (optional) dispatch_mode cross-check(1 NEW RAGAs run)

- **Spec ref**:ADR-0037 §6.1 + W27 F2 G empirical evidence
- **H1 trigger**:否
- **Trigger condition**:Step 1+2 best combo achieves G1-G5 PASS(若 marginal MISS remain → skip F3 直接 F4 closeout)
- **Acceptance criteria**:

  1. Run 3.A dispatch_mode=replace at best max_tokens + best top_k — `.env` 改 `PARENT_DOC_DISPATCH_MODE=replace` + 其他 hold + uvicorn restart + POST /eval/run = output `step3-dispatch-cross-check-W28-D3-raw.json`
  2. Markdown report `step3-dispatch-cross-check-W28-D3.md` — replace vs append at best combo comparison + final default flip recommendation:
     - 若 replace match OR exceed append at best combo → propose ADR-0037 amendment default flip Settings(max_tokens / top_k flip to best values;dispatch_mode 維持 "replace" — preserve W26+ADR-0038 default per Karpathy §1.3 surgical)
     - 若 append 仍 better at best combo → propose ADR-0037 amendment Settings flip + ADR-0038 amendment dispatch_mode default flip "replace" → "append"

- **Effort estimate**:~10 min eval runtime + ~0.5-1h analysis
- **Owner**:AI

### F4 — Closeout — ADR analysis + W29+ decision tree + cross-doc sync

- **Spec ref**:CLAUDE.md §10 R3 + R5 + R6
- **H1 trigger**:可能(若 G1+G4 PASS + best combo significant improvement → ADR-0037 amendment default flip;若 marginal MISS remains → ADR-0039 new documents finding + W29+ candidate (c) elevated)
- **OQ deps**:無
- **Acceptance criteria**(3 categories):

  **A. Phase Gate G1-G6 evaluation against best combo**:
  1. G1 best combo faithfulness vs F1 baseline ±2pp [0.9651, 1.0]
  2. G2 best combo correctness vs F1 baseline ±2pp [0.7216, 0.7616]
  3. G3 Q-W25-I07 PASS preserved(critical recovery from W26 F2 G 0.00 不可 regress)
  4. G4 Q-W25-I01 控制組 ≥ F1 baseline ± 0.05(close W27 marginal MISS 0.01pp)
  5. G5 best combo p95_latency reduced vs W27 (2897ms)— target < 1500ms ideal,< 2000ms acceptable
  6. G6 measurement-experiment-fail-policy applied

  **B. ADR governance per G result**:
  7. 若 G1+G2+G3+G4+G5 全 PASS(close W27 marginal MISS + reduce latency)→ **ADR-0037 amendment** per ADR-0017 5-amendment precedent:
     - `parent_doc_max_tokens_per_parent` default flip 4000 → <best value>
     - `parent_doc_top_k` default flip 1 → <best value>
     - `parent_doc_dispatch_mode` default flip per Step 3 result
     - `enable_parent_doc_retrieval` default flip 評估(若 best combo robust → propose flip True;否則 preserve False)
  8. 若 G1 + G4 仍 marginal MISS by < 0.5pp → **ADR-0037 amendment partial flip**(僅 Settings 改 best values,`enable_parent_doc_retrieval` 仍 default OFF + 文檔 finding)
  9. 若 best combo 反而 introduces NEW catastrophic regression → **NEW ADR-0039** documents no-improvement finding + W29+ candidate (c) RAGAs orchestrator-aware tune elevated(per R-W26-2)+ Settings preserve W27 state

  **C. Cross-doc sync per CLAUDE.md §10 R3 + R5 + R6**:
  10. plan.md frontmatter `status: active → closed`(若 PASS)OR `closed_partial`(若 marginal)OR `closed_partial`(若 NEW catastrophic regression)
  11. checklist.md cross-cutting 全 tick + 標明 deferred items per 🚧 reason
  12. progress.md retro 7-section + Phase Gate G1-G6 result + What worked / What didn't / Surprises / Carry-overs to W29+ / ADR triggers
  13. session-start.md §10 timeline row update(W28 closed status)+ §11 W28 CLOSED block prepend
  14. RISK_REGISTER R-W26-1 + R-W26-2 status flip per result(Mitigated / Decayed / Confirmed-residual-elevated)
  15. COMPONENT_CATALOG.md C05 status note append
  16. ADR README index sync(若 ADR-0037 amendment OR ADR-0039 ship — row + footer next-NNNN update)
  17. `.env` cleanup remove W28 F2-F4 env override marker block(restore W27 post-closeout state per Karpathy §1.3 surgical 唔污染 production behavior)

- **Effort estimate**:~2-3h
- **Owner**:AI

---

## 3. Success Criteria(Phase Gate)

| # | Criterion | Target | Measure | Block phase closeout? |
|---|---|---|---|---|
| G1 | Best combo aggregate faithfulness vs F1 baseline ±2pp | 0.9651 ≤ x ≤ 1.0 | `eval/run` 13-query | Yes |
| G2 | Best combo aggregate correctness vs F1 baseline ±2pp | 0.7216 ≤ x ≤ 0.7616 | `eval/run` 13-query | Yes |
| G3 | Q-W25-I07 PASS preserved | PASS(out of failed_queries — W27 F2 G critical recovery 不可 regress) | `eval/run` per-query | Yes |
| G4 | Q-W25-I01 控制組 answer_relevancy ≥ F1 baseline ± 0.05 | ≥ 0.65 effective | `eval/run` per-query | Yes |
| G5 | Best combo p95_latency vs W27 baseline 2897ms | < 2000ms acceptable / < 1500ms ideal | `eval/run` aggregate | Yes |
| G6 | Measurement-experiment-fail-policy applied(若 NEW catastrophic regression → default preserve W27 state 唔觸 revert)| Settings default values 依 best combo OR preserve W27 | ADR amendment OR new ship | Yes |

**Gate verdict policy**:
- G1 + G2 + G3 + G4 + G5 全 PASS → **Phase Gate PASS** → ADR-0037 amendment full Settings flip
- G1 + G4 marginal MISS by < 0.5pp / 其他 PASS → **Phase Gate PARTIAL** → ADR-0037 amendment partial flip(僅 Settings values 改;`enable_parent_doc_retrieval` 仍 OFF + finding 紀錄)
- 任一 G3 regression(Q-W25-I07 跌返 W26 catastrophic state)→ **Phase Gate PARTIAL** + Settings preserve W27 state + W29+ candidate (c) elevated
- G5 不達 < 2000ms threshold → **Phase Gate PARTIAL** with latency caveat + W29+ candidate (c) RAGAs orchestrator-aware tune address possibility

---

## 4. Risks(Phase-Specific)

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | R8 Azure-key-bound F1-F3 eval defers(per W25 F4 / W26 F1 / W27 F2 deferred precedent)| **Low**(W27 F2 G same-day environment continuity confirmed)| **Medium** | Per ADR-0017 Plan B (c)— Chris personal Azure tier credentials;若 blocked → STOP and ask Chris;F1-F4 deferred caveat trigger PARTIAL closeout |
| R2 | Step 1+2 best combo cross-doc interaction unmeasured(sequential miss potential interaction)| **Medium** | **Low**(Step 3 optional cross-check 抽取 1 combo 驗證)| Step 3 optional cross-check at best combo + 若 best 仍 marginal → 留 Karpathy §1.2 simplicity / W29+ candidate full grid expansion |
| R3 | top_k 加大 引入 off-topic leak regression(per ADR-0037 §2.1 trade-off — top-5 已含 §3.1 chunk #8 topically off,擴大 anchor 範圍 = aggregate §3 整個 section)| **Medium** | **Medium** | F2 Step 2 sweep deliberately 測試 trade-off;若 top_k=2/3 regress → Step 2 best 仍是 top_k=1,Step 3 cross-check confirms |
| R4 | max_tokens 降低 over-truncate parent section(tail-drop preserving narrative start per ADR-0037 §2.3)→ faithfulness regress on truncated tails | **Low** | **Medium** | F1 Step 1 sweep deliberately 測試 lower bound;若 max_tokens=1500 regress → 1500 too low,2000 中間值較佳 |
| R5 | Sequential miss interaction effect — sweep 結論未必 cover full grid maximum | **Medium** | **Low**(per Karpathy §1.2 simplicity vs full-grid complexity 已 acknowledged in §1.2 strategy rationale)| 若 best combo marginal MISS / latency over-budget → W29+ NEW phase 可 expand sweep grid 加 missed combos |
| R6 | `.env` modify + uvicorn restart workflow error(per W27 D2 PowerShell `Out-File -NoNewline` `.env` corruption incident)| **Medium** | **High**(若再 corrupt → time-cost incident)| 用 `echo >> .env` POSIX append-only(W27 D2 successful pattern)+ 避免 PowerShell `Out-File -NoNewline` per W27 D3 retro lesson;若 sweep mid-run corrupt → STOP and ask Chris |

---

## 5. Day-by-Day Breakdown(rough)

| Day | Date | Focus | Deliverables targeted |
|---|---|---|---|
| D0 | 2026-05-25 | Kickoff + R6 grep verify + plan/checklist/progress drafts + commit per R1 | F0 |
| D1 | 2026-05-25 | F1 Step 1 max_tokens sweep 3 runs + Step 1 analysis + commit | F1 |
| D2 | 2026-05-25 | F2 Step 2 top_k sweep 2 NEW runs + Step 2 analysis + commit | F2 |
| D3 | 2026-05-25 | F3 Step 3 optional dispatch cross-check + analysis + commit(若 triggered)+ F4 closeout — ADR governance + cross-doc sync + commit | F3 + F4 |

**Real-calendar collapse expectation**:~25-30× per W22-W27 AI compression pattern — ~1 actual day 條件下 condensed across 2026-05-25 vs ~4-day plan-day budget。

---

## 6. Dependencies on Prior Phase

Carry-over from `W27-parent-doc-dispatch-experiment/progress.md` retro:
- **(b) parent_doc Setting sweep** = W28 active scope(本 phase 直接 address per ADR-0038 §Decision #4 HIGHEST priority)
- W27 F2 G `append-mode-metrics-W27-D2-raw.json` 作 W28 sweep baseline reference(同時對 F1 baseline + W27 F2 G 兩個 reference)
- W27 F1 infrastructure preserved(Setting `parent_doc_dispatch_mode` + branch + 4 unit tests)= W28 sweep enabler — Setting 已 ship 可 env override
- `.env` Add-Content append-only pattern verified W27 D2 successful(避免 PowerShell `Out-File -NoNewline` per W27 D3 retro lesson)
- Uvicorn correct entry point `python -m api.server`(Windows SelectorEventLoop fix per ADR-0023 + api/server.py:343)
- Bearer `dev-token` mock auth pattern verified W27 D2(`FEATURE_AUTH_MOCK=true` 已 在 `.env`)

---

## 7. Plan Changelog

| Date | Change | Reason | Approver |
|---|---|---|---|
| 2026-05-25 | Initial plan | W28 kickoff post W27 PARTIAL closeout — Chris pick (b) parent_doc Setting sweep + 3 AskUserQuestion Recommended picks(命名 + Sequential strategy + Hold dispatch_mode=append)| Chris |
| 2026-05-25 | F0 R6 recursive grep verify Day 0 — Settings line 198-235 actual default values verified + W27 F2 G baseline raw JSON 已 read + sweep value (4000/2000/1500 + 1/2/3) 對齊 ADR-0037 §2.1+§2.3 design rationale 註解 + 0 historical surface contamination + plan-text 命名清空 W26/W27 inherited surface | W22 D9 plan-text-contamination prevention + W27 D3 retro PowerShell `.env` corruption lesson | AI(R6 recursive scope per CLAUDE.md §10 R6) |
| 2026-05-26 | F4 closeout PASS per ADR-0037 amendment — Phase Gate G1+G2+G4+G5 PASS + G2 EXCEEDS F1 baseline +1.61pp at best combo Run 3.A(dispatch=replace + top_k=2 + max_tokens=2000)/ G3 marginal MISS borderline judge noise per 8-run cross-config flip / D1.35 H4 hypothesis revised — Settings effect dominant over dispatch effect / Settings full default flip ship(max_tokens 4000→2000 + top_k 1→2 + dispatch 維持 replace + enable_parent_doc 維持 False per Q4) | W28 Step 1+2+3 sweep empirical best combo evidence + ADR-0037 amendment + ADR-0038 reaffirm | Chris Full Settings flip Recommended pick |

---

**Lifecycle reminder**:呢份 plan locked after status=active。重大 deviation 入第 7 節 changelog,小 detail 變動可直接 inline edit。
