---
phase: W28-parent-doc-setting-sweep
step: 3
day: 3
date: 2026-05-25
cross_check_axis: parent_doc_dispatch_mode
cross_check_values: [append (Run 2.A), replace (Run 3.A)]
held_variables:
  parent_doc_top_k: 2  # Best combo from Step 2
  parent_doc_max_tokens_per_parent: 2000  # Best combo from Step 1
  enable_parent_doc_retrieval: true
  parent_doc_section_depth_offset: 1
  parent_doc_max_chunks_per_parent: 50
  parent_doc_fallback_to_doc_on_shallow: true
runs:
  - id: 2.A (carry-over from Step 2)
    dispatch_mode: append
    runtime_s: 522
    raw_output: ./step2-run-2a-metrics-W28-D2-raw.json
  - id: 3.A
    dispatch_mode: replace
    runtime_s: 499
    raw_output: ./step3-dispatch-cross-check-W28-D3-raw.json
w28_final_best_combo: Run 3.A (dispatch_mode=replace, top_k=2, max_tokens=2000)
breakthrough_finding: |
  W26 F2 G catastrophic regression 根本原因 唔係 dispatch=replace 本身,而是 wrong Settings combination(top_k=1 + max_tokens=4000)。
  At correct Settings(top_k=2 + max_tokens=2000),dispatch=replace 不單 PASS G1+G2+G4+G5,G2 correctness 更超 F1 baseline +1.61pp。
  D1.35 H4 dispatch hypothesis revised:Settings effect 比 dispatch effect 更 dominant;append + replace at best combo 都 acceptable。
---

# W28 Step 3 — dispatch_mode Cross-check at Best Combo(Day 3, 2026-05-25)

> **F3 Step 3 optional dispatch cross-check per plan §2 F3 trigger condition** — Run 2.A best combo (top_k=2, max_tokens=2000, dispatch=append) 4 of 5 gates PASS triggered cross-check at dispatch=replace。

## 1. Two-Way Comparison at Best Combo

| 指標 | Run 2.A (append) | **Run 3.A (replace)** | Δ replace - append | F1 baseline | W27 F2 G (append+4000+1) |
|---|---|---|---|---|---|
| recall_at_5 | 0.8936 | 0.8936 | 0.0 | 0.8744 | 0.8936 |
| **faithfulness** | 0.9786 | **0.9812** | **+0.26pp** | 0.9851 | 0.9591 |
| **correctness** | 0.7331 | **0.7577** | **+2.46pp** ⭐ | 0.7416 | 0.7594 |
| **p95_latency_ms** | **1061** | 1249 | +188 | 1001 | 2897 |
| Failed queries 數 | 9 | 9 | 0 | — | 9 |

## 2. Per-Run Phase Gate G1-G5 Evaluation

### Run 2.A (append, top_k=2, max_tokens=2000) — Step 2 best

| Gate | Actual | Verdict |
|---|---|---|
| G1 faith vs F1 ±2pp | 0.9786 | ✅ PASS within tolerance |
| G2 correct vs F1 ±2pp | 0.7331 | ✅ PASS within tolerance |
| G3 Q-W25-I07 PASS | answer_rel=0.61 | ⚠️ MISS by 0.09pp(borderline)|
| G4 Q-W25-I01 ans_rel ≥ 0.65 | 0.69 | ✅ PASS |
| G5 latency < 1500ms ideal | 1061ms | ✅ PASS ideal |

### Run 3.A (replace, top_k=2, max_tokens=2000) — **W28 FINAL BEST** ⭐⭐⭐

| Gate | Actual | Verdict |
|---|---|---|
| G1 faith vs F1 ±2pp | 0.9812 | ✅ **PASS within tolerance**(closer to F1 than append)|
| G2 correct vs F1 ±2pp | **0.7577** | ✅ **PASS within tolerance + EXCEEDS F1 baseline +1.61pp** ⭐ |
| G3 Q-W25-I07 PASS | context_recall=0.40 | ⚠️ MISS(different metric fail than 2.A;Q-W25-I07 仍 not full PASS)|
| G4 Q-W25-I01 ans_rel ≥ 0.65 | **PASS**(out of failed list) | ✅ **PASS**(full PASS — beat 2.A's single-metric fail)|
| G5 latency < 1500ms ideal | 1249ms | ✅ PASS ideal |

**Aggregate**:**4 of 5 gates PASS,G2 超 F1 baseline,G4 full PASS without single-metric caveat** — W28 final best combo。

## 3. Q-W25-I07 cross-config 8-run flip evidence(extended)

| Phase / Run | dispatch / top_k / max_tokens | Q-W25-I07 verdict | metric details |
|---|---|---|---|
| W26 F2 G | replace / 1 / 4000 | **0.00 CATASTROPHIC** | faith=0.00 + answer_rel=0.00 |
| W27 F2 G | append / 1 / 4000 | **PASS** | all metrics ≥ 0.7 |
| W28 Run 1.A | append / 1 / 4000 | FAIL | faith=0.60 + answer_rel=0.66 |
| W28 Run 1.B | append / 1 / 2000 | **PASS** | all metrics ≥ 0.7 |
| W28 Run 1.C | append / 1 / 1500 | FAIL | answer_rel=0.66 |
| W28 Run 2.A | append / 2 / 2000 | FAIL | answer_rel=0.61 |
| W28 Run 2.B | append / 3 / 2000 | **PASS** | all metrics ≥ 0.7 |
| W28 Run 3.A | replace / 2 / 2000 | FAIL | context_recall=0.40 |

**8 runs:3 PASS / 5 FAIL** — borderline judge variance dominant signal,settings + dispatch effect 次要。Q-W25-I07 G3 marginal MISS across multiple runs treat as noise — DOES NOT drive amendment decision。

## 4. D1.35 H4 dispatch hypothesis revised

**Original W27 H4 hypothesis**:dispatch=replace catastrophic(per W26 F2 G empirical)→ append mode 修復 by 2-segment LLM input citation invariant preservation。

**W28 revised understanding**:
- **W26 F2 G catastrophic 根本原因 = wrong Settings combination**(top_k=1 conservative + max_tokens=4000 too long)+ dispatch=replace top-priority-wins
- **At correct Settings(top_k=2 + max_tokens=2000),dispatch=replace 不單 不 catastrophic,反而 達到 W28 best combo across G1+G2+G4+G5**
- **dispatch=append mode 喺 wrong Settings (top_k=1 + max_tokens=4000) 嘅 W27 partial recovery** = 雖然 modest improvement,但係 **wrong axis fix** — the real axis 係 Settings tuning(top_k 同 max_tokens)
- D1.35 H1 citation invariant breakage 嘅 hypothesis 仍部份 validated — W26→W27 嘅 Q-W25-I07 critical recovery 由 append 觸發,但 W28 evidence 顯示 **Settings tuning 比 dispatch tuning 更 dominant**

**Implications for ADR-0037 amendment**:
- Settings default flip max_tokens=2000 + top_k=2 = mandatory(both append/replace 都 benefit)
- dispatch_mode default = pick replace OR append — 兩個 都 PASS G1+G2+G4+G5 at best combo,**replace 略勝 G2 + G4**(超 F1 + full PASS Q-W25-I01)
- ADR-0038 W27 closeout decision「default preserve replace」**仍 valid** — replace at correct Settings 確實 是 W28 best combo

## 5. W28 final best combo: Run 3.A (replace + top_k=2 + max_tokens=2000)

**Decision rationale**:

1. **G2 correctness 超 F1 baseline +1.61pp** — 唯一 sweep run 達到 above-baseline correctness
2. **G4 Q-W25-I01 full PASS** — Q-W25-I01 control 完全 out of failed_queries list(不像 Run 2.A 仍 context_recall=0 single-metric fail)
3. **G1 faithfulness closer to F1** — 0.9812 vs 2.A 0.9786 = 略勝
4. **G3 marginal MISS** Q-W25-I07 context_recall=0.40 — borderline judge variance per 8-run cross-config flip evidence
5. **G5 PASS within ideal** — 1249ms < 1500ms(latency 比 append 略 +188ms 但仍 ideal threshold)
6. **ADR-0038 W27 closeout「default preserve replace」decision validated** — W26 F2 G catastrophic 嘅 root cause 由 Settings combination wrong 引起,replace dispatch 本身 acceptable

## 6. F4 Closeout — ADR-0037 amendment proposal

Per W28 best combo + plan §2 F4 acceptance:

**ADR-0037 amendment full Settings flip**:
- `parent_doc_max_tokens_per_parent`:4000 → **2000** ✅
- `parent_doc_top_k`:1 → **2** ✅
- `parent_doc_dispatch_mode`:remain "replace"(W26+ADR-0038 default preserved per Karpathy §1.3 surgical;replace at best combo 達到 best gates)
- `enable_parent_doc_retrieval`:remain `False` default per Q4 measurement-experiment-fail-policy 唔觸 revert(W28 G3 Q-W25-I07 marginal MISS 屬 borderline noise but 仍 NOT full PASS = 唔達 ADR-0037 Q4 production default flip threshold)

**ADR-0038 verdict update**:
- W27 closeout「Settings default preserve replace」decision **VALIDATED by W28 evidence**
- W27 F1 dispatch_mode enum infrastructure preserved(both append/replace acceptable at correct Settings — append remains as W28+ adaptive routing OR opt-in for query-class fine-tuning)

**W29+ candidate prioritization update**:
- ✅ **(b) parent_doc Setting sweep COMPLETED** — W28 ship + ADR-0037 amendment ship
- 仍 priority(c)RAGAs orchestrator-aware judge tune per R-W26-2 — H1+H2 judge side address(but 直接 demand 降低,因 W28 已 close G1+G2+G4+G5)
- 仍 priority(d)F3 query expansion standalone test per ADR-0034 — orthogonal axis
- **NEW W29+ candidate**:`make_ragas_evaluator` 補 structlog stage emit(per query / per metric judge call progress)為 long-running eval debugging operability(per W28 Run 2.B 15+ min silent hung incident)
- 仍 BUG-026 UI count + BUG-027 `/health._check_cohere` engine.reranker private attr drift
