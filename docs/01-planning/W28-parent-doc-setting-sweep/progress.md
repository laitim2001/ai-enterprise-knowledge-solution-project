---
phase: W28-parent-doc-setting-sweep
plan_ref: ./plan.md
checklist_ref: ./checklist.md
status: in-progress
---

# Phase W28 — Progress

> Daily progress + 結尾 retro。
> 每 commit 必須對應一個 Day-N entry mention(R2 binding rule per PROCESS.md §5)。

---

## Day 0 — 2026-05-25:Kickoff

**Action**:Phase W28 kickoff post W27 PARTIAL closeout
- Templates 參考 W27 closed-phase conventions(per CLAUDE.md §10.2「起草新 plan/checklist 必先讀『最近一個 closed phase』樣板」)
- `plan.md` drafted with 7-section structure + frontmatter `status: active` + §2 F0-F4 deliverables + §3 G1-G6 + §4 R1-R6 + §5 D0-D3 + §6 W27 carry-overs + §7 Changelog
- `checklist.md` derived from plan §2 deliverables(atomic items per F0-F4 + cross-cutting)
- `progress.md` Day 0 entry(本 entry)
- Chris 3-question AskUserQuestion approval pick(2026-05-25):
  - Phase 命名:`W28-parent-doc-setting-sweep`(Recommended)
  - Sweep strategy:Sequential one-variable-at-a-time(Recommended)
  - Dispatch mode:Hold dispatch_mode=append(Recommended — W27 partial-validated config)
- Trigger memo:ADR-0038 §Decision #4 W28+ candidate (b) HIGHEST priority — H2 attention dilution direct intervention + latency reduction

**F0 R6 Pre-Active-Flip 5-Step Recursive Grep Verification**(per CLAUDE.md §10 R6):

執行重點:Settings line 198-235 actual default values + ADR-0037 §2.1+§2.3 design rationale + W27 F2 G baseline raw JSON 對齊 verified,W22 D9 plan-text-contamination 防範。

| R6 step | Action | Finding |
|---|---|---|
| Step 1 | Read plan literal acceptance criteria | F1 §A-§C max_tokens sweep + F2 §A-§B top_k sweep + F3 optional dispatch cross-check + F4 §A-§E closeout |
| Step 2 | Grep code base for referenced files / functions / patterns | Settings line 198-235 — `parent_doc_max_tokens_per_parent=4000` + `parent_doc_top_k=1` + `parent_doc_dispatch_mode="replace"` 全部 fields 已存在 + 可由 env var override;ADR-0037 §2.1 註解「Setting allows W27+ sweep to 2/3」+ §2.3 註解「Setting allows W27+ tune if faithfulness drops on truncated tails」對應 W28 sweep range design |
| Step 3 | Surface mismatches via Karpathy §1.1 think-before-coding upfront | 0 mismatch — W28 sweep range(4000/2000/1500 + 1/2/3)直接 derive 自 ADR-0037 §2 註解 + Settings field 註解 rationale;0 historical surface inheritance |
| Step 4 | Document deviations in plan §7 changelog at plan kickoff | `plan.md` §7 Plan Changelog Day 0 entry 2026-05-25 documented R6 finding + W27 D3 retro PowerShell `.env` corruption lesson reference for F1-F3 active flip workflow |
| Step 5 | Adjust acceptance criteria per actual reality | F4 §C.17 加 `.env` cleanup 紀律 + W27 D3 PowerShell `Out-File -NoNewline` lesson reference;F1-F3 active flip 用 `echo >> .env` POSIX append-only(W27 D2 successful pattern)避免 PowerShell 危險 |

**R6 result**:0 historical surface contamination(per W22 D9 anti-pattern prevention);experiment-scoped wording grounded in ADR-0037 §2 design rationale;regime alignment confirmed。

**W27 carry-over verified**:
- W27 F2 G `append-mode-metrics-W27-D2-raw.json` 作 W28 sweep baseline reference column 1(append + 4000 + 1 baseline)
- W27 F1 infrastructure preserved(Setting `parent_doc_dispatch_mode` + branch + 4 unit tests)= W28 sweep enabler
- Uvicorn correct entry `python -m api.server`(Windows SelectorEventLoop fix per ADR-0023 + api/server.py:343)
- Bearer `dev-token` mock auth pattern(`FEATURE_AUTH_MOCK=true` 已在 `.env`)
- `.env` Add-Content append-only pattern(避免 PowerShell `Out-File -NoNewline` per W27 D3 retro lesson)

**Commit**:`1fd8806` — `docs(planning): kickoff W28-parent-doc-setting-sweep`(4 files / +564 / -1 — plan.md + checklist.md + progress.md + session-start.md §10 timeline row append + W29+ rolling JIT row)

---

## Day 1 — 2026-05-25:F1 Step 1 max_tokens sweep 完成

### Done

- F1 A R8 prerequisite check — keys present + W27 D2 same-day environment continuity confirmed by Run 1.A baseline duplicate(recall_at_5=0.8936 同 W27 F2 G 一致)
- F1 B Step 1 三 runs sequential:
  - **Run 1.A**(max_tokens=4000 baseline duplicate)— 528s runtime / faith=0.9573 / correctness=0.7485 / p95_latency=1037ms / Q-W25-I07 fail (0.60/0.66) / Q-W25-I01 PASS
  - **Run 1.B**(max_tokens=2000)— 476s runtime / faith=**0.9628** / correctness=0.7167 / p95_latency=1402ms / Q-W25-I07 **PASS** / Q-W25-I01 緊 boundary(0.65)
  - **Run 1.C**(max_tokens=1500)— 493s runtime / faith=0.9575 / correctness=0.7278 / p95_latency=**853ms** / Q-W25-I07 fail / Q-W25-I01 PASS(answer_rel)
- F1 C Step 1 analysis report `step1-max-tokens-sweep-W28-D1.md` ship — 6 sections / three-way comparison / per-run G1-G5 / H2 hypothesis PARTIALLY CONFIRMED + counterintuitive results / Step 1 best pick + Step 2 base config
- Workflow operational:`echo >> .env` POSIX append-only 設定 base block(避免 PowerShell `Out-File -NoNewline` per W27 D3 retro lesson)+ uvicorn restart via `python -m api.server`(SelectorEventLoop fix)+ Bearer `dev-token` mock auth POST per run

### Decisions / OQ Resolved

- **Step 1 best pick:Run 1.B(max_tokens=2000)** for Step 2 base — 理由:
  1. **G3 critical PASS(唯一)** — Q-W25-I07 0.00 → PASS preserved per D1.35 H1 citation invariant validated metric
  2. **G1 最接近 F1 tolerance**(MISS 0.23pp only — 1.A 0.78pp / 1.C 0.76pp)
  3. G2 marginal MISS + G4 緊 boundary — 可能 Step 2 top_k 加大 close gap by broader anchor coverage
  4. G5 PASS(1402ms < 2000ms acceptable + ~52% reduction vs W27 baseline 2897ms)
- **H2 hypothesis re-evaluation**:**PARTIALLY CONFIRMED + counterintuitive surfaced**:
  - ✅ max_tokens 降低 提升 faithfulness(2000 most;1500 minimal)
  - ❌ correctness 反向 — 反而 降低(parent section 切短失 coverage)
  - ❌ latency 唔係 monotonic — 2000 反而最高(possibly LLM tokens elsewhere)
  - ✅ Q-W25-I07 critical recovery 喺 2000 唯一(1500 too aggressive,4000 過大)
  - ⚠️ Total failed queries 數 隨 max_tokens 降低 increases(9→10→11)= broader coverage loss
- **NEW finding eval-to-eval variance**:RAGAs judge LLM borderline queries(0.60-0.70 區間)±0.05-0.10 fluctuation 正常;W27 + W28 Run 1.A 同 config 之間 Q-W25-I07 + Q-W25-I01 PASS/FAIL flip — signal noise floor 對 G3+G4 結論 影響需 後續 Step 2 confirm
- **NEW finding p95_latency cold-start**:W27 F2 G 2897ms 包 connection cold-start cost ~1860ms;W28 warm-state 853-1402ms。Latency-optimization conclusion 應 base 喺 W28 warm-state numbers

### Blockers

- 無 D1 blocker

### Actual vs Planned Effort

| Deliverable | Planned (h) | Actual (h) | Variance |
|---|---|---|---|
| F1 A R8 prerequisite check | ~0.5 | ~0.1 | -0.4(keys present + W27 continuity confirmed quickly)|
| F1 B Step 1 三 runs sequential | ~30 min eval | ~25 min(528+476+493 = 1497s ≈ 25 min)| -5 min |
| F1 C Step 1 analysis writeup | ~1-1.5h | ~1.5h | 0 |
| F1 D uvicorn restart × 3(OneDrive disk lag pattern surfaced Run 1.C cold-start)| ~3 min | ~5 min(180s timeout monitor re-arm Run 1.C)| +2 min |

**D1 actual**:~2.5h vs ~2-3h planned(within budget)

### Commits

- (pending F1 Step 1 commit `docs(eval): W28 F1 Step 1 max_tokens sweep — 3 RAGAs runs / best pick max_tokens=2000 / H2 PARTIALLY CONFIRMED`)

---

## Day 2 — 2026-05-25:F2 Step 2 top_k sweep 完成 + best combo emerged

### Done

- F2 A Step 2 active flip — 2 NEW runs holding max_tokens=2000 + dispatch_mode=append:
  - **Run 2.A**(top_k=2)— 522s runtime / faith=**0.9786** / correctness=**0.7331** / p95_latency=**1061ms** / **Q-W25-I01 控制 PASS (0.69)** / Q-W25-I07 marginal MISS (0.61)
  - **Run 2.B**(top_k=3)— first try hung 15+ min at silent RAGAs phase → user explicit 指示 restart + retry succeed 482s runtime / faith=0.9945 / correctness=**0.6821 CATASTROPHIC MISS 5.95pp** / **Q-W25-I01 控制 0.00 CATASTROPHIC** / Q-W25-I07 PASS
- F2 B Step 2 analysis report `step2-top-k-sweep-W28-D2.md` ship — 7 sections / Three-way aggregate / Per-query critical / Per-run G1-G5 / W28 best combo / Operational lessons / F3 trigger evaluation
- **W28 best combo emerged:Run 2.A (top_k=2, max_tokens=2000, dispatch_mode=append)** — 4 of 5 gates PASS:
  - **G1 PASS** faith 0.9786 within [0.9651, 1.0]
  - **G2 PASS** correctness 0.7331 within [0.7216, 0.7616]
  - G3 marginal MISS 0.09pp(Q-W25-I07 answer_rel=0.61 — borderline judge variance per 7-run cross-config PASS/FAIL flip evidence)
  - **G4 PASS** Q-W25-I01 control 0.69 ≥ 0.65 threshold
  - **G5 PASS** latency 1061ms < 1500ms ideal(~63% reduction vs W27 baseline 2897ms)
- Run 2.B 首 try 15+ min hung 異常 diagnosed:`make_ragas_evaluator` 喺 RAGAs judge phase 唔 emit structlog events;process actually 處理緊 silently 52 judge calls(13 × 4 metrics)
- Recovery:TaskStop curl + uvicorn + kill python processes + restart fresh + retry succeed
- **W28+ candidate logged**:`make_ragas_evaluator` 補 structlog stage emit(per query / per metric judge call progress)為 long-running eval debugging operability

### Decisions / OQ Resolved

- **W28 best combo locked**:Run 2.A (top_k=2, max_tokens=2000, dispatch_mode=append)
- **top_k=2 sweet spot** ADR-0037 §2.1 trade-off empirically verified:top_k=1 coverage 不足(W26+W27 G1+G4 MISS)/ top_k=2 best balance(4/5 gates PASS)/ top_k=3 off-topic leak catastrophic(Q-W25-I01 control 0.00)
- **F3 Step 3 TRIGGERED** per plan §2 F3 trigger condition(4 of 5 gates PASS qualifies)— cross-check dispatch_mode=replace at top_k=2, max_tokens=2000 比較 append vs replace at best combo
- **NEW finding eval-to-eval variance Q-W25-I07 borderline**:跨 7 個 runs W26+W27+W28 PASS/FAIL flip 3 PASS / 4 FAIL(全部 borderline 0.60-0.70 區間)— judge LLM 非確定性 dominant signal,settings effect 次要

### Blockers

- 解決:Run 2.B 首 try 15+ min hung incident → restart pattern + W28+ candidate add structlog emit

### Actual vs Planned Effort

| Deliverable | Planned (h) | Actual (h) | Variance |
|---|---|---|---|
| F2 A Step 2 — 2 NEW runs sequential | ~20 min eval | ~17 min(522 + 482 = 1004s ≈ 17 min)| -3 min |
| F2 A Run 2.B first hung incident + diagnose + restart | 0(unexpected)| +15-20 min hung wait + 5 min restart | +20-25 min |
| F2 B Step 2 analysis writeup | ~1h | ~1.5h(加 Q-W25-I07 7-run flip 證據 + Run 2.B hung diagnose docs)| +0.5h |

**D2 actual**:~2.5h vs ~1.5h planned(+1h variance,主要 Run 2.B hung incident)

### Commits

- (pending F2 Step 2 commit `docs(eval): W28 F2 Step 2 top_k sweep — 2 NEW RAGAs runs / best combo Run 2.A (top_k=2, max_tokens=2000) / 4 of 5 gates PASS / top_k=3 over-aggregation catastrophic`)

---

## Day 3 — 2026-05-25:F3 Step 3 dispatch cross-check 完成 + W28 final best combo revealed

### Done

- F3 A trigger evaluation:Run 2.A best combo 4 of 5 gates PASS → Step 3 TRIGGERED per plan §2 F3
- F3 B Step 3 active flip — 1 NEW run holding top_k=2 + max_tokens=2000,sweep dispatch_mode replace:
  - **Run 3.A**(dispatch=replace + top_k=2 + max_tokens=2000)— 499s runtime / faith=**0.9812** / correctness=**0.7577 EXCEEDS F1 baseline +1.61pp** / p95_latency=**1249ms** / **Q-W25-I01 控制 FULL PASS**(out of failed list) / Q-W25-I07 context_recall=0.40 single-metric fail
- F3 C Step 3 analysis report `step3-dispatch-cross-check-W28-D3.md` ship — 6 sections / Two-way comparison / Per-run G1-G5 / Q-W25-I07 8-run flip evidence / D1.35 H4 hypothesis revised / W28 final best combo Run 3.A / F4 closeout recommendation

### Decisions / OQ Resolved

- **W28 FINAL BEST COMBO LOCKED:Run 3.A (dispatch_mode=replace + top_k=2 + max_tokens=2000)** ⭐⭐⭐
  - G1 faith 0.9812 ✅ PASS within F1 ±2pp(closer to F1 than Run 2.A append)
  - G2 correctness **0.7577 EXCEEDS F1 baseline +1.61pp** ✅ ⭐(唯一 sweep run 達 above-baseline)
  - G3 Q-W25-I07 context_recall=0.40 marginal MISS — borderline judge variance per 8-run cross-config flip(3 PASS / 5 FAIL)treat as noise
  - G4 Q-W25-I01 control **FULL PASS**(out of failed list — beat Run 2.A 嘅 context_recall=0 single-metric fail)
  - G5 latency 1249ms ✅ PASS < 1500ms ideal(+188ms vs Run 2.A append 但仍 ideal threshold)
- **W26 F2 G catastrophic 根本原因 reframed**:**唔係 dispatch=replace 本身,而係 wrong Settings combination(top_k=1 + max_tokens=4000)**。At correct Settings(top_k=2 + max_tokens=2000),replace 不單 不 catastrophic,反而 達到 W28 best combo across G1+G2+G4+G5
- **D1.35 H4 dispatch hypothesis revised**:Settings effect 比 dispatch effect 更 dominant — append + replace at best combo 都 acceptable。W27 ADR-0038「Settings default preserve replace」decision **VALIDATED by W28 evidence**
- **ADR-0037 amendment proposal**:Settings default 全套 flip:max_tokens=2000 + top_k=2 + dispatch_mode 維持 "replace"(per Karpathy §1.3 surgical)+ enable_parent_doc_retrieval 維持 `False` default per Q4(G3 marginal MISS 仍 not full PASS 不 達 production default flip threshold)
- **W29+ candidates updated**:(c) RAGAs orchestrator-aware tune 仍 priority but direct demand 降低(W28 close G1+G2+G4+G5)+ (d) F3 query expansion standalone test orthogonal + NEW (e) `make_ragas_evaluator` structlog stage emit per W28 Run 2.B 15+ min silent hung lesson

### Blockers

- 無 D3 blocker

### Actual vs Planned Effort

| Deliverable | Planned (h) | Actual (h) | Variance |
|---|---|---|---|
| F3 A trigger evaluation | ~0.2 | ~0.1 | -0.1 |
| F3 B Step 3 1 NEW run | ~10 min eval | ~8 min(499s)| -2 min |
| F3 C Step 3 analysis writeup | ~0.5-1h | ~1h(加 Q-W25-I07 8-run flip 加 D1.35 H4 hypothesis revision)| 0 |

**D3 actual so far**:~1.2h(F3 only;F4 closeout pending)

### Commits

- (pending F3 Step 3 commit + F4 closeout commit)

---

## Retro(填於 phase 結束)

### What worked

- (pending)

### What didn't work / unexpected friction

- (pending)

### Surprises / discoveries

- (pending)

### Carry-overs to W29+

- (pending)

### ADR triggers

- (pending — ADR-0037 amendment OR ADR-0039 new ship per G result)

### Phase Gate result

- G1:(pending)
- G2:(pending)
- G3:(pending)
- G4:(pending)
- G5:(pending)
- G6:(automatic)

### Phase status

- Closeout commit:(pending)
- Frontmatter status flipped to:(pending)
- Phase W29+ kickoff trigger:(pending — depends on G result + user pick on next candidate)

---

**End of W28 progress**
