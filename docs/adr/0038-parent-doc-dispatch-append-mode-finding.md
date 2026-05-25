# ADR-0038: Parent-Doc Dispatch Chain Append-Mode Finding — Hypothesis Partial Validation + Settings Default Preserve "replace"

**Date**: 2026-05-25
**Status**: Accepted; reaffirmed 2026-05-26 W28 F4 per Setting sweep at correct combo
**Approver**: Chris(技術 Lead)— α pick W27 F3 closeout per Q4 measurement-experiment-fail-policy;**reaffirmed 2026-05-26 W28 F4** by W28 Step 3 dispatch cross-check at best combo(Run 3.A replace vs Run 2.A append at top_k=2 + max_tokens=2000)— replace dispatch achieves W28 best combo G1+G2+G4+G5 PASS + G2 超 F1 baseline,validates ADR-0038 §Decision #1「default preserve replace」(plan §3 Gate verdict PARTIAL → Settings default preserve "replace" 唔觸 revert + W28+ candidates (b) + (c) elevated)
**Trigger**: W27 F2 G RAGAs eval `eval-set-v0-w25-supplement.yaml` 13-query Two-Baseline delta(2026-05-25 D2,544s runtime via Bearer dev-token mock auth)— append mode 大幅修復 W26 F2 G replace 嘅 catastrophic regressions but G1 + G4 marginal MISS by < 1pp 各 vs F1 baseline tolerance ±2pp / ±0.05。Phase Gate PARTIAL per plan §3 policy。

---

## Context

### W27 phase scope(recap)

W26 F2 G replace mode RAGAs delta FAIL on faithfulness -8.36pp + correctness -6.12pp + Q-W25-I07 0.00/0.00 critical synthesizer failure + Q-W25-I01 control regression。**W26 D1.35 hypothesis 4-axis** 其中 H4「dispatch replace-vs-append architectural variable」accuracy 由 W27 F0 R6 code reality verification 確認 — `prompt_builder._format_chunk` line 55-59 `or` chain 即 replace semantics(top-priority-wins:`parent_section_text > expanded_text > chunk_text`),anchor 嘅 `chunk_text` LLM 完全唔見。

W27 phase 唯一 experiment scope = enum `parent_doc_dispatch_mode` "replace" | "append"(per Karpathy §1.2 simplicity + W26 retro PC1「一次只郁一個旋鈕」eval-driven discipline)。Append branch render BOTH anchor `chunk_text` + parent_section_text 兩段(Option (i) single chunk header + `Parent section context:` delimiter sub-section per Chris AskUserQuestion Recommended pick + Karpathy §1.2 simplicity)。

### W27 F2 G empirical result(2026-05-25 D2)

13-query eval cohort 對齊 W26 F1 baseline + W26 F2 G replace baseline。Two-Baseline delta:

| 指標 | F1 baseline(OFF)| W26 F2 G(replace)| **W27 F2 G(append)** | Δ vs F1 | Δ vs W26 F2 G |
|---|---|---|---|---|---|
| recall_at_5 | 0.8744 | 0.8744 | **0.8936** | **+1.92pp** | **+1.92pp** |
| **faithfulness** | **0.9851** | 0.9015 | **0.9591** | **-2.60pp** | **+5.76pp** |
| **correctness**(answer_relevancy)| **0.7416** | 0.6804 | **0.7594** | **+1.78pp** | **+7.90pp** |
| **p95_latency_ms** | 1001 | 1188 | **2897** | **+189.4%** | **+143.9%** |

**Critical per-query**:
- Q-W25-I07 W26 F2 G **0.00/0.00 catastrophic synthesizer failure → W27 F2 G PASS**(out of failed_queries list = D1.35 H1「citation invariant breakage」直接驗證)✅
- Q-W25-I01 控制 W26 F2 G answer_relevancy=0.54 → W27 F2 G answer_relevancy=0.64(+10pp recovery 但仍 < 0.65 F1 ±0.05 tolerance)⚠️

### Phase Gate G1-G6 verdict per plan §3

| Gate | Criterion | Actual | Verdict |
|---|---|---|---|
| **G1** | append faithfulness vs F1 ±2pp [0.9651, 1.0] | 0.9591 | ⚠️ **MARGINAL MISS 0.6pp** |
| **G2** | append correctness vs F1 ±2pp [0.7216, 0.7616] | 0.7594 | ✅ **PASS** |
| **G3** | Q-W25-I07 faithfulness > 0.5 | PASS(out of failed_queries) | ✅ **PASS** |
| **G4** | Q-W25-I01 answer_relevancy ≥ F1 ± 0.05 | 0.64 | ⚠️ **MARGINAL MISS 0.01pp** |
| **G5** | pytest 1060 + ruff + dispatch 11/11 | green | ✅ **PASS** |
| **G6** | measurement-experiment-fail-policy applied | (本 ADR governs) | (本 ADR governs) |

**Aggregate verdict**:**Phase Gate PARTIAL** per plan §3 policy(G1 + G4 marginal MISS by < 1pp each)。

### D1.35 hypothesis 4-axis re-evaluation(per W27 F2 D2 analysis report §4)

| Hypothesis | W27 result | Confidence |
|---|---|---|
| H1 Citation invariant breakage(LLM cite parent siblings outside top-5 reranked set → RAGAs judge mismatch)| ✅ **VALIDATED PARTIAL** by Q-W25-I07 critical recovery 0.00 → PASS | High |
| H2 Parent section attention dilution(LLM 注意力被長 parent section context 分散)| ⚠️ **PARTIALLY CONFIRMED** by G4 control regression remains + 2 NEW context_precision fails surfaced(Q-W25-T02, Q-W25-I02)+ p95_latency +189% direct evidence | Medium-High |
| H3 Q-W25-I07 REFUSAL_PHRASE / chunk_id drift | ✅ **REFUTED** — Q-W25-I07 完整 recovery proves chunk_id drift 唔係 root cause(W26 F2 G 0.00 source = citation invariant breakage,not drift)| High |
| H4 Dispatch replace-vs-append architectural variable | ✅ **VALIDATED** — faith +5.76pp / correctness +7.90pp / Q-W25-I07 全 recovery vs W26 F2 G | High |

**Conclusion**:H1 + H4 validated;H2 partially confirmed(emerging as primary residual axis);H3 refuted。Append mode 確認係 W26 F2 G replace 嘅 superior alternative across multiple key metrics but 仍 落後 F1 baseline 邊際 G1 + G4 due to H2 attention dilution side effect 未完整 close。

---

## Decision

### 1. Settings default preserve "replace" per Q4 measurement-experiment-fail-policy

`Settings.parent_doc_dispatch_mode` 默認值 **保留 "replace"** per Karpathy §1.3 surgical 唔觸 revert:

- **Rationale**:Phase Gate PARTIAL(G1 + G4 marginal MISS by < 1pp)— per Q4 ADR-0037 measurement-experiment-fail-policy「fail → default preserve replace 唔觸 revert」applicable to marginal MISS scenarios
- **Backward-compat**:W26 F2 G existing 7 dispatch tests preserved bit-identical(`dispatch_mode="replace"` default behavior unchanged)
- **W27 F1 code preserved**:NEW Setting + prompt_builder branch + 4 NEW unit tests 全部 ship 保留 — append mode 可由 env override 啟用作 W28+ standalone-test 候選 OR opt-in flag for specific KB / query class

### 2. `enable_parent_doc_retrieval` 默認 preserve False(不變)

`Settings.enable_parent_doc_retrieval` 仍維持 ADR-0037 Q4 lock 嘅 `False` default。W27 F2 G eval 唔改變 W26 F2 G measurement-experiment-fail-policy。

### 3. `.env` cleanup at F3 closeout

Remove W27 F2 active flip 嘅 3 行 marker block:
- `# W27 F2 active flip per ADR-0037 amendment candidate (2026-05-25) — dispatch mode append-vs-replace experiment`
- `ENABLE_PARENT_DOC_RETRIEVAL=true`
- `PARENT_DOC_DISPATCH_MODE=append`

→ env var override clean state restored to W26 F2 G post-closeout default(per W26 F2 G `.env cleanup` precedent)。

### 4. W28+ candidate prioritization(per F2 D2 analysis report §5)

Phase Gate PARTIAL → W28+ candidates 重新排序:

| Priority | Candidate | Rationale | Effort estimate |
|---|---|---|---|
| **1 HIGHEST** | (b)`max_tokens_per_parent` 4000→2000/1500 sweep | H2 attention dilution direct intervention + latency reduction signal | ~3-5 days |
| **2 Second** | (c)RAGAs orchestrator-aware judge tune per R-W26-2 | H1+H2 address from judge side(judge consume parent_section_text reference)| ~5-7 days |
| **3 Third** | (d)F3 query expansion standalone test per ADR-0034 | orthogonal axis test | ~3 days |

### 5. ADR-0037 NOT amended at W27 closeout

ADR-0037 §229 dispatch chain wording remains 「replace semantics top-priority-wins」base case;W27 F1 NEW `dispatch_mode` enum 屬於 ADR-0037 implementation 嘅 architectural variable extension,默認 preserve "replace" 即與 ADR-0037 原 spec 一致。Marginal MISS 唔達 ADR-0037 amendment threshold(per ADR-0017 5-amendment precedent「same decision family rationale」要求 measurable significant win)。

W28+ candidate (b) OR (c) PASS → 屆時再評估 ADR-0037 amendment vs ADR-0038 supersede。

---

## Alternatives Considered

### Option B — ADR-0037 amendment ship default flip "replace" → "append"

**Action**:
- ADR-0037 Status「Accepted」→「Accepted; amended 2026-05-25 W27 F3 per dispatch chain append-vs-replace experiment」
- NEW "Amendment 2026-05-25 W27 F3 — append dispatch chain" section
- §6.4 Q-NEW append-vs-replace decision documented
- Settings `parent_doc_dispatch_mode` default flip "replace" → "append" + tests update

**Pros**:
- Ship append mode immediate benefit(faith +5.76pp / correctness +7.90pp / Q-W25-I07 critical recovery vs W26 F2 G replace baseline)
- D1.35 H4 validated → 順理成章 update default

**Cons**:
- ❌ **G1 + G4 marginal MISS** vs F1 baseline = production behavior 不及 W2 baseline pre-parent-doc;ADR-0017 5-amendment precedent 要求 measurable significant win 而非 marginal trade-off
- ❌ **+189% p95_latency** = production user experience regression(W26 F2 G already +18.7%;append mode 2.9× slower than F1 baseline)
- ❌ **2 NEW context_precision fails surfaced**(Q-W25-T02, Q-W25-I02)+ 1 control regression remains(Q-W25-I01)= H2 attention dilution side effect 確實 introduce 新 failure modes
- ❌ Per Q4 measurement-experiment-fail-policy 嘅 spirit「fail → default preserve」適用範圍包括 marginal MISS — 唔應 ship marginal improvement as default
- ❌ W28+ candidate (b) `max_tokens_per_parent` sweep likely close G1 + G4 gap;先 ship marginal append + 後續 amendment 屬 churn

**Rejected because**:Phase Gate PARTIAL by both faithfulness G1 + control G4 = production default 不應 ship 含 marginal regression。Karpathy §1.3 surgical「唔觸 revert/flip 除非 measurable significant win」+ Q4 measurement-experiment-fail-policy applicable。等 W28+ candidate (b) close G1 + G4 gap 之後再評估。

### Option C — Revert W27 F1 changes(rollback Setting + prompt_builder branch + tests)

**Action**:Revert commit `50b1db5` + remove `parent_doc_dispatch_mode` Setting + remove append branch + remove 4 NEW unit tests

**Pros**:
- Cleanest codebase state — W26 F2 G baseline preserved
- 唔需要維持 unused code(append branch 喺 default OFF 之下 dead code)

**Cons**:
- ❌ **D1.35 H4 validation 證據 erased** — append mode demonstrable 大幅修復 W26 F2 G catastrophic regressions(Q-W25-I07 critical recovery,faith +5.76pp,correctness +7.90pp)= valuable empirical evidence
- ❌ **W28+ candidate (b) + (c) precondition lost** — W27 F1 infrastructure(Setting + branch + observability)係 W28+ Setting sweep 嘅 baseline(若 revert 要重做)
- ❌ Code preserved 唔影響 production default(`dispatch_mode="replace"` 仍 默認)— Karpathy §1.2 simplicity vs §1.3 surgical trade-off:simplicity 略 lost(NEW Setting + branch unused at default)but surgical wins(可由 env override 啟用 + W28+ candidate accessible)

**Rejected because**:W27 F1 infrastructure 屬於 architectural enabler for W28+;revert = re-implement debt + erase D1.35 H4 empirical validation evidence。Per Karpathy §1.3「surgical changes preserve infrastructure」optimal trade-off:preserve code + preserve default "replace" + document finding via ADR-0038。

### Option D — Ship append + flip Settings default(no ADR)— "silent default flip"

**Action**:Edit `backend/storage/settings.py` `parent_doc_dispatch_mode` default `"replace"` → `"append"` without ADR-0037 amendment(or NEW ADR)

**Pros**:
- Minimum doc overhead
- Immediate Q-W25-I07 production benefit

**Cons**:
- ❌ **Violates CLAUDE.md §10 R5**「Phase closeout 之前任何 architectural-adjacent decision 必須寫 ADR」— Settings default flip 屬 architectural-adjacent
- ❌ **Same G1 + G4 marginal MISS production regression issue as Option B**

**Rejected because**:R5 governance violation + same production regression as Option B。

---

## Consequences

### Positive

- **Q4 measurement-experiment-fail-policy honored**:marginal MISS scenarios 受 same treatment as catastrophic MISS = default preserve 唔觸 revert per Karpathy §1.3 surgical
- **W27 F1 infrastructure preserved**:Setting + branch + 4 NEW tests 全部 ship 保留 — W28+ candidate (b) + (c) precondition + opt-in via env override for specific KB/query class
- **D1.35 hypothesis 4-axis 重新評估留檔**:H1 validated partial + H2 emerging primary residual + H3 refuted + H4 validated = clearer architectural understanding for W28+ candidate selection
- **W28+ priority queue update**:(b) `max_tokens_per_parent` sweep elevated 為 highest signal-to-cost — direct H2 intervention + latency reduction
- **Backward-compat clean**:Settings default unchanged → existing 1060 backend pytest preserved + existing 11 callers behavior bit-identical

### Negative

- **W27 codebase 加 NEW Setting + branch + observability** but default OFF — minor unused-by-default surface area(per Karpathy §1.2 simplicity slight cost;但 §1.3 surgical 維持因 infrastructure 屬 W28+ enabler)
- **Q-W25-I07 production behavior 未改善**:replace mode 仍是 default → Q-W25-I07 production user experience 仍 risk catastrophic failure(若 `enable_parent_doc_retrieval=true` flipped W28+ without dispatch_mode fix)
- **W28+ candidate (b) effort estimate ~3-5 days** mandatory if Q-W25-I07-class production deployment ambition + parent-doc retrieval flip on(short-term staged rollout 仍可 manual flag-off till W28+ closes gap)

### Neutral

- **No vendor change**(H2 unaffected)— same Cohere v4.0-pro / Azure OpenAI / GPT-5.5 stack
- **No multi-tenancy implication**(kb_id scoping per ADR-0018 preserved)
- **No security implication**(Setting enum + dispatch branch 屬 LLM prompt rendering internal — no PII / auth surface change)
- **Component impact**:C05 Generation Pipeline(dispatch chain enum branching)— design notes refresh trigger deferable per ADR-0020 P1 batch precedent
- **Backward compat**:default "replace" 維持 W26 F2 G + ADR-0037 §229 spec 一致;rollback = remove NEW Setting + branch + tests(W27 commits revert)

---

## References

### Source documents
- **W27 plan**:`docs/01-planning/W27-parent-doc-dispatch-experiment/plan.md` §3 Phase Gate G1-G6 verdict policy + §4 R5 risk
- **W27 F1 implementation commit**:`50b1db5` `feat(generation): W27 F1 dispatch mode enum + append branch + 4 NEW unit tests`
- **W27 F2 G eval evidence**:
  - `docs/01-planning/W27-parent-doc-dispatch-experiment/append-mode-metrics-W27-D2.md`(6-section analysis report with two-baseline delta + per-query 比較 + Phase Gate G1-G6 + D1.35 hypothesis 4-axis re-evaluation + W28+ priority)
  - `docs/01-planning/W27-parent-doc-dispatch-experiment/append-mode-metrics-W27-D2-raw.json`(raw 13-query eval payload — 544s runtime)
- **W26 F2 G replace baseline**:`docs/01-planning/W26-eval-driven-retrieval-tuning/parent-doc-metrics-W26-D5.md` + raw JSON
- **W26 F1 no-parent-doc baseline**:`docs/01-planning/W26-eval-driven-retrieval-tuning/baseline-metrics-W26-D1.md` + raw JSON

### Spec references(architecture.md v6)
- **§3.1 Query Pipeline**(line 184-219)— parent-doc retrieval post-Context Expander step(unchanged from ADR-0037 — W27 唔改 pipeline structure,只 modify `_format_chunk` LLM prompt rendering)
- **§3.5 Citation Contract** — `Citation.chunk_text = original_chunk.chunk_text` preserved on both replace + append branches

### Cross-ref ADRs
- **ADR-0017** R8 mitigation pattern 5-amendment precedent — append mode marginal MISS 唔達 "measurable significant win" threshold for amendment;W28+ candidate (b) may meet threshold
- **ADR-0020** Context Expander — structural sibling pattern + observability emit precedent
- **ADR-0037** Parent-Document Section Retrieval — W27 F1 dispatch mode enum 屬 implementation 嘅 architectural variable extension(default 與 ADR-0037 §229 wording 一致)
- **ADR-0034** Query expansion + RAG-Fusion — same feature-flag default-off precedent + W28+ candidate (d) framework existing

### Behavioral baseline
- **Karpathy §1.1 think-before-coding**:W27 F0 R6 recursive verify ADR-0037 §229 vs `prompt_builder.py:55-59` 對齊 = replace semantics confirmed by code reality(no assumption)
- **Karpathy §1.2 simplicity-first**:single-variable experiment scope vs broader R-W26-1 umbrella(Setting sweep + dedupe);Option (i) single chunk header + delimiter sub-section vs Option (ii) 2 chunk entries
- **Karpathy §1.3 surgical**:Settings default preserve "replace" 唔觸 revert per measurement-experiment-fail-policy;W27 F1 infrastructure preserved as W28+ enabler;no ripple change to existing 11 callers
- **Karpathy §1.4 goal-driven**:F2 acceptance G1-G5 verifiable success criteria → 4 pass + 2 marginal MISS = clear Phase Gate PARTIAL verdict

### Postmortem preventive controls(BUG-025 + W27 retro)
- **PC1 ≥ 5-query manual user-test taxonomy**:W27 F2 G 13-query cohort 對齊 W26 F1 + W26 F2 G baseline = consistent comparison surface(Q-W25-I01 control + Q-W25-I02 + Q-W25-I03 + Q-W25-I07 + Q-W25-T04 priority queries covered)
- **PC3 ADR assumption-language review**:本 ADR-0038 explicit refuted H3(chunk_id drift)+ validated H1 + H4 + partially confirmed H2 = grounded in W27 empirical evidence,not assumption
- **PC4 pre-phase regression baseline capture**:W26 F1 baseline + W26 F2 G replace baseline 雙 reference 為 W27 append delta measurement

---

## Reaffirmation 2026-05-26 W28 F4 — dispatch=replace VALIDATED at correct Settings

**Trigger**:W28-parent-doc-setting-sweep phase Step 3 (F3) dispatch cross-check at best combo(per plan §2 F3 trigger condition — Run 2.A best combo 4 of 5 gates PASS triggered Step 3)。

### W28 Step 3 Cross-check Evidence

**Run 2.A (append + top_k=2 + max_tokens=2000)** vs **Run 3.A (replace + top_k=2 + max_tokens=2000)** at W28 best combo:

| Gate | Run 2.A (append) | Run 3.A (replace) | Verdict |
|---|---|---|---|
| G1 faithfulness | 0.9786 | **0.9812** | replace 略勝(+0.26pp closer to F1)|
| G2 correctness | 0.7331(PASS within F1)| **0.7577(EXCEEDS F1 +1.61pp)** | **replace 大勝** ⭐ |
| G3 Q-W25-I07 | answer_rel=0.61 MISS | context_recall=0.40 MISS | 兩者都 marginal MISS(borderline judge variance — 8-run cross-config flip noise)|
| G4 Q-W25-I01 control | 0.69 PASS(but context_recall=0 single-metric fail)| **FULL PASS**(out of failed list)| **replace 略勝** ⭐ |
| G5 latency | **1061ms** | 1249ms | append 略勝 latency(but 兩者都 within ideal < 1500ms)|

### Decision Reaffirmation

**ADR-0038 §Decision #1「`Settings.parent_doc_dispatch_mode` default preserve "replace" per Q4 measurement-experiment-fail-policy」VALIDATED**:
- W28 Run 3.A(replace at correct Settings)achieves W28 final best combo across G1+G2+G4+G5
- W26 F2 G catastrophic root cause reframed:**wrong Settings combination(top_k=1 + max_tokens=4000)+ dispatch=replace**,非 dispatch=replace 本身
- At correct Settings(top_k=2 + max_tokens=2000),replace dispatch:
  - G2 correctness 0.7577 EXCEEDS F1 baseline by +1.61pp(append 0.7331 below F1)
  - G4 Q-W25-I01 control FULL PASS(append context_recall=0 single-metric fail)
  - G1 faithfulness 0.9812 closer to F1 than append 0.9786
- Karpathy §1.3 surgical preserve W26+ADR-0038 default Settings amendment 唔需要 改 dispatch_mode default

### D1.35 H4 Hypothesis Refinement

**Original W27 H4**:dispatch=replace catastrophic per W26 F2 G empirical → append mode 修復 by 2-segment LLM input citation invariant preservation。

**W28 revised**:**Settings effect dominant over dispatch effect** — append + replace at correct Settings 都 acceptable但 replace 略勝 G2+G4。D1.35 H1 citation invariant breakage hypothesis 由 W27 partial validate(Q-W25-I07 W26→W27 critical recovery 由 append 觸發);但 W28 8-run flip evidence 顯示 Q-W25-I07 borderline judge variance 主導 signal,settings + dispatch effect 次要。

### W28+ Implication

- ADR-0037 amendment full Settings flip(max_tokens=2000 + top_k=2)proceeded per W28 F4 closeout
- `parent_doc_dispatch_mode` default remain "replace"(per ADR-0038 §Decision #1 reaffirmed)
- W27 F1 dispatch_mode enum infrastructure preserved for W29+ adaptive routing OR opt-in for query-class fine-tuning(both append/replace acceptable at correct Settings)

### Cross-references

- ADR-0037 amendment 2026-05-26 W28 F4(full Settings default flip)
- W28 Step 3 analysis:`docs/01-planning/W28-parent-doc-setting-sweep/step3-dispatch-cross-check-W28-D3.md`

---

**End of ADR-0038**。
