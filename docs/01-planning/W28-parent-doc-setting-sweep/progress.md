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

## Day 2 — 2026-05-25(planned)

### Done

- (pending — F2 Step 2 top_k sweep 2 NEW runs + Step 2 analysis)

### Decisions / OQ Resolved

- (pending)

### Blockers

- (pending)

### Actual vs Planned Effort

| Deliverable | Planned (h) | Actual (h) | Variance |
|---|---|---|---|

### Commits

- (pending)

---

## Day 3 — 2026-05-25(planned)

### Done

- (pending — F3 Step 3 optional dispatch cross-check + F4 closeout + ADR governance + cross-doc sync)

### Decisions / OQ Resolved

- (pending)

### Blockers

- (pending)

### Actual vs Planned Effort

| Deliverable | Planned (h) | Actual (h) | Variance |
|---|---|---|---|

### Commits

- (pending)

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
