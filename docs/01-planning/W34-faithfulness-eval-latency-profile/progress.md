---
phase: W34-faithfulness-eval-latency-profile
plan_ref: ./plan.md
checklist_ref: ./checklist.md
status: active
last_updated: 2026-05-26
---

# Phase W34 — Progress

> Daily progress log + R6 Day 0 + decisions + commits + retro。

---

## Day 0 — 2026-05-26(kickoff)

### F0 Kickoff actions

1. **Trigger**:W33-rule7-rule8-restoration closed PASS WITH G1b-DISTINCT-EQUAL + LATENCY-CONCERN CAVEAT(commit `355f58c` pushed origin/main)— W33 retro `priority_queue_locked` 將 **Faithfulness LIVE RAGAs eval HIGHEST** + **Latency profile breakdown #2** elevated 至 W34+ HIGHEST candidates per W33 F2 G2 +143% over-citation concern + W33 F2 latency +57-91% prompt-length cost surface。

2. **User candidate pick**(2026-05-26 same-day as W33 closeout):「現在先執行 A. 立即可做(自主)1. Faithfulness LIVE RAGAs eval(OQ-1 + OQ-3)+ 2. Latency profile breakdown(OQ-2)」— 兩個 measurement-only axes 同 ship 安全(both A.1 + A.2 read-only / instrumentation,no production behavior shift)。

3. **W34 framing — measurement-only phase**:
   - W31-W33 都係 ship 候選 features 然後 measure
   - W34 ship NOTHING — pure measurement + observability instrumentation
   - F1.0 surgical kwargs propagation 係 production-parity restoration(bug-fix-adjacent 非 NEW feature)
   - F2.1 structlog timing 係 pure observability(no production behavior impact)

### R6 Day 0 recursive grep verify(per CLAUDE.md §10 R6 + W23 F3 recursive amendment)

**Plan-text + code base contamination check + integration gap inspection**:

1. **🚨 R6 catch (1) `build_ragas_samples` missing W32 (h') wiring**:
   - `backend/eval/orchestrator.py:95` `synth = await synthesizer.synthesize(question, retrieval.chunks)` — **NOT propagating `engine=engine, kb_id=q_kb_id` kwargs**
   - W32 F1.1.a synthesizer signature change(`*, engine=None, kb_id=None`)was wired into `query.py:208 + 382` + `crag.py:414` 3 caller sites
   - **BUT** `build_ragas_samples` callsite never updated — RAGAs eval pipeline 唔會 trigger W32 (h') engine-fetch citation expansion
   - **Implication**:If unmodified `/eval/run` is invoked,RAGAs measures W33 prompt 層 ONLY without (h') backbone → misleading vs production stack
   - **PC-W32-2 realized**:「future module-level changes affecting citation pipeline must explicitly propagate via SynthesisResult fields」— eval orchestrator was the exact integration gap PC-W32-2 warned about(out-of-scope callsite from W32 F1.4 wire scope)
   - **Mitigation per F1.0 surgical patch**:propagate `engine=engine, kb_id=q_kb_id` kwargs into line 95 — minimal,non-architectural per H1(kwargs propagation through call chain matches existing synthesizer signature)

2. **✅ R6 catch (2) `make_ragas_evaluator` Azure key dependency satisfied**:
   - `backend/eval/ragas_evaluator.py:79` `if not settings.azure_openai_api_key: return None`
   - `.env` has `AZURE_OPENAI_API_KEY=DWe4...` ✅
   - Judge LLM = `gpt-5.4-mini`(settings.azure_openai_deployment_llm_judge per W17 F3)
   - Embeddings = `text-embedding-3-large`(Q19 baseline)
   - 4-metric:faithfulness + answer_relevancy + context_precision + context_recall

3. **✅ W33 SYSTEM_PROMPT Rule 7 v2 + Rule 8 verified post-W33 commit**:
   - `backend/generation/prompt_builder.py:28-30` confirmed Rule 7 v2 + Rule 8 lines present(post-W33 F1 commit `149aebd`)
   - F1.5 contingency 若 triggered 可 temporarily revert local-only no commit

4. **✅ W32 (h') Settings + Synthesizer wire intact**:
   - `Settings.py` L264 `enable_citation_post_hoc_expansion=True` + L270 `citation_expansion_window=10` + L274 `citation_expansion_max_aux=2` ✅
   - `synthesizer.py` L31 import + L57 field + L135-138 kwargs + L161-197 synthesize integration + L272-301 stream integration ✅

5. **✅ Eval-set ready**:
   - `docs/eval-set-v0-w25-supplement.yaml` 13 queries against `sample-document-with-image-1` KB
   - Q-W25-I07(line 296)+ Q-W25-I01(line 178)both present
   - 11 other corpus-matched queries(T01-T06 + I02-I06)provide breadth for 4-metric aggregate

6. **✅ W26 F1 baseline reference confirmed**:
   - `docs/01-planning/W26-eval-driven-retrieval-tuning/baseline-metrics-W26-D1-raw.json`:**faith 0.9851 / correctness 0.7416 / recall@5 0.8744 / p95_latency 1001ms**
   - Eval-set used:eval-set-v0-w25-supplement.yaml(same as W34)— direct apples-to-apples comparison

**Conclusion**:F1.0 surgical patch needed per R6 catch (1)。Otherwise net 0 contamination,clean state confirmed for W34 measurement axes。

### W26 F1 baseline + decision tree thresholds(pre-implementation surface)

**Reference baseline**(W26 F1 = pre-W26 parent-doc state = closest pre-W32-W33 historical RAGAs measurement):

| Metric | W26 F1 baseline | Threshold |
|---|---|---|
| faithfulness | 0.9851 | W34 ≥ 0.9651 (-2pp) preserve / 0.9351-0.9651 flag / < 0.9351 break |
| correctness(answer_relevancy)| 0.7416 | informational(decision driven primarily by faithfulness)|
| recall@5 | 0.8744 | informational(retrieval-side unchanged from W26 F1)|

**Decision tree pre-implementation** per Karpathy §1.4 goal-driven verifiable success criteria:

```
W34 RAGAs faith vs W26 F1 baseline 0.9851:
├─ ≥ 0.9651(W26 -2pp envelope) → G1 preserve
│   └─ W33 over-citation BENIGN → preserve Rule 7 v2 + Rule 8 production ship
├─ 0.9351 ≤ faith < 0.9651(W26 -5pp to -2pp) → G1 flag
│   └─ Rule 8 over-citation FLAG → defer ship decision pending W35+ Rule 8 wording tighten test
└─ < 0.9351(W26 -5pp 以下) → G1 break
    └─ trigger F1.5 contingency W32 (h')-only isolation eval
        ├─ W32-only faith ≥ 0.9651 → Rule 7 v2 + Rule 8 caused regression → W35+ revert OR tighten
        └─ W32-only faith < 0.9651 → (h') itself caused regression → re-think W32 ship governance
```

```
W34 latency dominant cost(across 10-run breakdown):
├─ LLM emit cost > 50% of W33-W32 +57-91% slowdown → G2 LLM emit
│   └─ W35+ Rule 8 wording tighten 「cite SUFFICIENT」
├─ Prompt token cost > 50% → G2 prompt token
│   └─ W35+ Rule 7 v2 wording compact 去 examples
├─ Engine-fetch IO cost > 50% → G2 engine-fetch
│   └─ W35+ async connection pool / parallelism enhancement
└─ Mixed(no single > 50%) → G2 mixed
    └─ W35+ multi-axis combined tighten + compact
```

### F0 next steps

- **F0.5** Draft this progress.md Day 0 entry — ✅ this section
- **F0.6** Commit kickoff `docs(planning): kickoff W34-faithfulness-eval-latency-profile + R6 Day 0 catch build_ragas_samples missing W32 (h') wiring + measurement-only phase scope`
- **F0.7** session-start.md §10 W34 row append `🟡 active 2026-05-26` + W35+ rolling JIT row defer + W33 row 維持 closed PASS
- **D1 start**:F1.0 surgical patch(~20min)+ F1.1-F1.4 RAGAs LIVE eval cascade(~2-3h)

### Actual vs Planned Effort(D0)

| Item | Planned | Actual | Variance |
|---|---|---|---|
| F0.1 folder + F0.2 R6 verify + F0.3-F0.5 docs | ~1h | TBD post-commit | TBD |

---
