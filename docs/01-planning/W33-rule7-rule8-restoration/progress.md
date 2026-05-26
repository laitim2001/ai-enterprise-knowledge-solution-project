---
phase: W33-rule7-rule8-restoration
plan_ref: ./plan.md
checklist_ref: ./checklist.md
status: active
last_updated: 2026-05-26
---

# Phase W33 — Progress

> Daily progress log + R6 Day 0 + decisions + commits + retro。

---

## Day 0 — 2026-05-26(kickoff)

### F0 Kickoff actions

1. **Trigger**:W32-engine-fetch-citation-expansion closed PASS(commit `6b99a93` pushed origin/main)— Phase Gate PASS ⭐⭐⭐(G1 strict + relaxed + marginal 3/3 at +80pp marginal vs W31 baseline 20%;avg_cit 5.4 350% gain;G2 control I01 0 refusals + avg_cit 4.2)。W32 retro `priority_queue_locked` 將 **Rule 7 v2 + Rule 8 restoration** elevated 至 W33+ HIGHEST candidate per sequential ship strategy(W32 (h') baseline established → multi-axis attribution now clean per Karpathy §1.2 序列規律)。

2. **User candidate pick**(2026-05-26 same-day as W32 closeout):**Rule 7 v2 + Rule 8 restoration** explicit confirmed —「現在開始執行 Rule 7 v2 + Rule 8 restoration(sequential ship strategy — W32 (h') baseline established 後 multi-axis layer attribution now clean;~1-2h estimate)」

### R6 Day 0 recursive grep verify(per CLAUDE.md §10 R6 + W23 F3 recursive amendment)

**Plan-text + code base contamination check**:

1. **✅ Rule 7 / Rule 8 absent from `prompt_builder.py`**(post-W31-revert state confirmed):
   - `grep -E "Rule 7|Rule 8|prefer citing|cite ALL|individually-numbered|coverage-summary"` → 0 matches
   - 確認 W31 commit `09805d6` full-revert 後 prompt_builder.py:20-28 SYSTEM_PROMPT 只剩 Rule 1-6(Rule 6 CH-005 partial-coverage W25.5 BUG-025 amendment + W26 R14 mitigation 仍 present)
   - Rule 7 v2 + Rule 8 verbatim source = W31 commit `16b9b3d`(git show 已 verify)

2. **✅ W32 (h') backend baseline 全 intact**:
   - `backend/generation/citation_expansion.py` ~225 lines NEW W32 module 存在
   - `backend/generation/synthesizer.py:31` `from generation.citation_expansion import expand_citations` import 存在
   - `backend/generation/synthesizer.py:57` `expanded_neighbor_chunks: list[RetrievedChunk] = dataclasses_field(default_factory=list)` field 存在
   - `backend/generation/synthesizer.py:135-138` `*, engine=None, kb_id=None` kwargs 存在 + docstring W32 F1.1.a attribution
   - `backend/generation/synthesizer.py:161-197` `synthesize` integration `expand_citations` + `expanded_neighbor_chunks` propagation 存在
   - `backend/generation/synthesizer.py:272-301` `synthesize_stream` integration 存在
   - `backend/storage/settings.py:264` `enable_citation_post_hoc_expansion: bool = True` 存在(default ON ship per W32 G1 PASS)
   - `backend/storage/settings.py:270` `citation_expansion_window: int = 10` 存在(corpus-empirical per W31 F2 v3 R6 catch (3) lesson)
   - `backend/storage/settings.py:274` `citation_expansion_max_aux: int = 2` 存在(parallel W25 F5 D1 convention)
   - **無 W31 `citation_expansion_score_threshold` field**(W32 PC-W31-2 lesson — `list_chunks` returns raw chunks without rerank scores)

3. **✅ W26-W32 inheritance baselines preserved**:
   - W29 `.env` env override `QUERY_EXPANSION_PER_VARIANT_OVERFETCH=8 + QUERY_EXPANSION_RRF_K=30` — NOT toggled
   - W28 `Settings.py` `parent_doc_*` defaults — NOT toggled
   - W26 `Settings.py` `enable_parent_doc_retrieval=False` Q4 — NOT toggled

4. **✅ W31+W32 lessons applied as preventive controls**:
   - **PC-W31-1**(corpus-realistic regex `\b\d+\.\d+\b` validated)— Rule 7 v2 wording 已含 bare X.M + §X.M examples + Scenario A walkthrough + Step 3.2(corpus-realistic per W31 F2 v1 Run 1 evidence)
   - **PC-W32-1**(backend explicit kill+restart for code reload)— F2.1 explicit mandates `python -m api.server` kill+restart(WatchFiles NOT active per `api/server.py:357`)

**Conclusion**:net 0 contamination,clean state confirmed for sequential ship。Rule 7 v2 + Rule 8 verbatim restoration safe from W31 commit `16b9b3d` 上層 W32 (h') backend intact baseline。

### Karpathy §1.1 think-before-coding — G1 acceptance criteria redefinition

**問題 surfaced to user**:W32 (h') 已 saturate G1(strict 5/5 + relaxed 5/5 + avg_cit 5.4)。**G1 baseline 已封頂無得再「improve」**。W31/W32 G1 criteria 不適用 W33。

**Plan §3 G1 redefinition**(per Karpathy §1.4 goal-driven verifiable success criteria):

| Gate | W32 baseline | W33 criterion |
|---|---|---|
| **G1a strict** MAINTAIN | strict 5/5 = 100% | MAINTAIN(NOT regress)|
| **G1a relaxed** MAINTAIN | relaxed 5/5 = 100% | MAINTAIN(NOT regress)|
| **G1b mean** ADDITIVE | avg_cit 5.4 | ≥ 5.4(no regress);ADD value if > 5.4 |
| **G1b coverage** ADDITIVE | non-(h') sourced TBD | ANY evidence Rule 7 v2/Rule 8 added 過 (h') mechanical |

**3 個可能 outcome**(per plan §3 G1 decision matrix):
- (a) **G1a MAINTAIN + G1b ADD value evidence** → Phase Gate PASS + production preserve
- (b) **G1a MAINTAIN + G1b NO additive evidence** → Phase Gate PARTIAL + revert per Karpathy §1.3 complexity-without-benefit
- (c) **G1a regress OR G2 regress** → Phase Gate FAIL + revert per W30+W31 precedent

**Rationale**:G1a 防止 prompt 引發 distraction 導致 walkthrough cite rate 跌(避免 Rule 8 over-citation 引發 LLM diluted attention);G1b 探測 prompt 是否真係 ADD value 過 (h') mechanical baseline。

### F0 next steps

- **F0.5** Draft this progress.md Day 0 entry — ✅ this section
- **F0.6** Commit kickoff `docs(planning): kickoff W33-rule7-rule8-restoration + sequential ship on W32 (h') baseline + R6 Day 0 verify`
- **F0.7** session-start.md §10 W33 row append `🟡 active 2026-05-26` + W34+ rolling JIT row defer + W32 row 維持 closed PASS
- **D1** start:F1 implementation cascade(prompt edit + 3 NEW unit tests + commit)— estimate ~1-1.5h

### Actual vs Planned Effort(D0)

| Item | Planned | Actual | Variance |
|---|---|---|---|
| F0.1 folder + F0.2 R6 verify + F0.3-F0.5 docs + F0.6 commit `c56afa0` + F0.7 sync commit `fd7b550` | ~1h | ~30min | -50% real-calendar collapse |

---

## Day 1 — 2026-05-26(F1 implementation same-day collapse)

### F1.1 prompt edit(`backend/generation/prompt_builder.py:28-30`)

**Rule 7 v2 verbatim restored**(from W31 commit `16b9b3d`,reverted via `09805d6`):
```
7. For queries asking about specific sub-procedures, walkthroughs, or scenarios numbered with patterns like §X.M (e.g. §8.1, §8.2, §8.3, Scenario A walkthrough, Step 3.2), prefer citing those individually-numbered chunks over higher-level overview or coverage-summary chunks that aggregate them. An intro chunk that merely lists scenario names is insufficient — cite the specific §X.M chunks that describe each scenario's actual procedure.
```
Trailing attribution:`(W33 F1.1.a — Rule 7 v2 restored from W31 commit 16b9b3d per sequential ship on W32 (h') baseline)`

**Rule 8 verbatim restored**(from W31 commit `16b9b3d`):
```
8. When multiple retrieved chunks each contain partial information relevant to the answer, cite ALL of them (not just the most representative one) — each fact in the answer should be backed by every chunk that supports it. If two chunks describe the same scenario from different angles, both warrant a citation marker.
```
Trailing attribution:`(W33 F1.1.b — Rule 8 restored from W31 commit 16b9b3d per sequential ship layered on W32 (h') backend)`

Rule 1-6 preserved unchanged(non-regression guard via F1.2.a third test)。

### F1.2 Unit tests(`backend/tests/test_prompt_builder_dispatch.py:177-256`)

**+3 NEW tests post-W27 baseline 11 → 14**:

- `test_system_prompt_includes_rule_7_v2_specificity_preference` — assert key phrases:「§X.M」+「individually-numbered chunks」+「coverage-summary chunks」+「intro chunk」+「lists scenario names is insufficient」+ examples「§8.1」+「Scenario A walkthrough」+「Step 3.2」
- `test_system_prompt_includes_rule_8_cite_breadth` — assert key phrases:「cite ALL of them」+「partial information」+「each fact in the answer should be backed by every chunk」+「two chunks describe the same scenario」+「both warrant a citation marker」
- `test_system_prompt_rule_6_ch005_preserved_non_regression` — assert Rule 6 CH-005 preserved:「Based on available documentation:」+「COMPLETELY off-topic」+ `REFUSAL_PHRASE` interpolated +「(CH-005 — R14 mitigation」attribution

### F1 verify gates state

- **pytest baseline preserved**:W32 1081 passed + 25 skipped + 0 failed → **W33 F1 = 1084 passed + 25 skipped + 0 failed**(+3 NEW exact match plan §F1.2.b expected ~1084)
  - `tests/test_prompt_builder_dispatch.py` isolated:14 passed in 3.00s(11 pre-existing + 3 NEW)
  - Full `tests/` run:1084 passed in 760.29s ≈ 12 min(no existing test regression)
- **ruff PASS**:`ruff check generation/prompt_builder.py tests/test_prompt_builder_dispatch.py` clean
- **mypy strict module-path quirk preserved**:`mypy --strict --follow-imports=silent generation/prompt_builder.py` reports pre-existing `Source file found twice under different module names: "backend.generation" and "generation"` — same baseline error per CO_W25_mypy_strict_debt unchanged through W26-W32 chain;prompt_builder.py 本身無 NEW mypy violation introduced

### F1 next steps

- **F1.3.a** Commit `feat(generation): W33 F1 Rule 7 v2 + Rule 8 prompt restoration on W32 (h') baseline + 3 NEW unit tests`
- **F1.3.b** progress.md Day 1 entry(this section)— ✅ done
- **D2 next**:F2 5-run reproducibility verify — F2.1 explicit kill+restart backend per PC-W32-1(WatchFiles NOT active per `api/server.py:357`)+ F2.2 Q-W25-I07 5 runs + F2.3 Q-W25-I01 control 5 runs + F2.4 aggregate vs W32 baseline 100/100/5.4

### Actual vs Planned Effort(D1)

| Item | Planned | Actual | Variance |
|---|---|---|---|
| F1.1 prompt edit + F1.2 3 NEW tests + F1.3 commit + progress | ~1-1.5h | ~30min(edit + tests + pytest) | -67% real-calendar collapse(short single-axis scope per plan §5) |

---
