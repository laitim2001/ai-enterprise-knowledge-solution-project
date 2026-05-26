---
phase: W35-rule8-wording-tighten
plan_ref: ./plan.md
checklist_ref: ./checklist.md
status: active   # F0 kickoff 2026-05-26
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

(F0.6 commit pending — combined kickoff plan + checklist + progress + R6 catch)

### Carry-overs / Blockers

- F0.5 progress.md Day 0 entry(this file)— in progress
- F0.6 kickoff commit — pending
- F0.7 session-start.md §10 W35 row append — pending(commit hash post-F0.6)

---

## Day 1(TBD)— F1 Rule 8 wording tighten + LIVE RAGAs eval

(pending F0.6 commit + user lock Option A/B/C)

---

## Day 2(TBD)— F2 Latency re-verify + F3 closeout

(pending Day 1 outcome)
