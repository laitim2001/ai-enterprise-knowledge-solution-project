---
phase: W27-parent-doc-dispatch-experiment
name: "Parent-doc dispatch chain append-vs-replace experiment — W26 F2 G failure mode root-cause hypothesis test"
sprint_week: W27
start_date: 2026-05-25
end_date: 2026-05-25   # same-day collapse expected per W22-W26 AI compression pattern; will extend if R8 Azure-key-bound F2 G eval defers
status: active
spec_refs:
  - architecture.md §3.1       # query pipeline (parent-doc post-Context Expander step per ADR-0037)
  - architecture.md §3.5       # ChunkRecord citation contract preservation
  - architecture.md §3.7       # query orchestration locus (parent-doc + prompt_builder dispatch)
prior_phase: W26-eval-driven-retrieval-tuning
trigger_memo: W26 F2 G RAGAs eval delta FAIL + Chris α pick PARTIAL closeout + W26 retro `Next phase candidates` row (a)
related_adrs: [0037]    # ADR-0037 amendment OR new ADR-0038 supersede triggered post-F2 G result per F3 acceptance gate
---

# Phase W27 — Parent-Doc Dispatch Chain Append-vs-Replace Experiment

> **Plan version**:1.0(initial)
> **Owner**:Chris(Tech Lead)+ AI(implementation)
> **Approved by**:Chris(chat 2026-05-25 — 「揀 (a) dispatch chain append-vs-replace 實驗」+ AskUserQuestion 3 Recommended picks:phase 命名 `W27-parent-doc-dispatch-experiment` + Setting enum `parent_doc_dispatch_mode` "replace"|"append" + Both-baseline G RAGAs delta comparison)
> **Trigger memo**:W26 closeout retro `Next phase candidates` 候選 (a) Dispatch chain append-vs-replace 實驗 — R-W26-1 — 最直接解 RAGAs judge mismatch

## 1. Scope

### 1.1 Trigger context

W26 F2 G RAGAs delta(parent-doc replace mode vs F1 no-parent-doc baseline)**FAIL** 雙 hard gate:

- **faithfulness -8.36pp**(F1 baseline 0.9851 → W26 F2 G replace 0.9015 — SEVERE regression)
- **correctness -6.12pp**(F1 baseline 0.7416 → W26 F2 G replace 0.6804)
- **Q-W25-I01 控制組「what is high level architecture」**被破壞(answer_relevancy=0.54 + context_recall=0)
- **Q-W25-I07 CRITICAL** synthesizer **faithfulness=0.00 + answer_relevancy=0.00**(post-BUG-025 fix all-pass → parent-doc complete failure)

W26 D1.35 hypothesis 4-axis 入面 **dispatch replace-vs-append architectural variable** axis 假設:

- **Current(replace semantics)**:`prompt_builder._format_chunk` line 55-59 用 `chunk.fields.get("parent_section_text") or chunk.fields.get("expanded_text") or chunk.fields.get("chunk_text", "")` — 當 `parent_section_text` 存在,LLM **完全唔見** anchor 嘅 `chunk_text`
- **Failure mechanism**:LLM 喺 parent_section_text 入面 cite parent siblings(`[chunk-X]` markers)→ top-5 reranked **唔包含** 全部 parent siblings(per ADR-0037 Q1 `parent_doc_top_k=1` only)→ RAGAs faithfulness judge 比較「retrieved chunks(top-5)」vs「LLM cite chunks」mismatch → 標 unfaithful
- **Append hypothesis**:`parent_section_text` + delimiter + `chunk_text` 兩段都喺 LLM input → LLM 可以 cite anchor chunk_id(top-5 內)+ 受惠 parent section coverage → citation invariant preserved → RAGAs judge mismatch eliminated

### 1.2 Single-variable experiment scope(per Karpathy §1.2 simplicity + W26 retro PC1 一次只郁一個旋鈕)

| 變量 | Value | Holding constant |
|---|---|---|
| `parent_doc_dispatch_mode`(NEW)| "replace"(W26 baseline)→ "append" | 其他 5 個 ADR-0037 Settings(`enable_parent_doc_retrieval` env-overridden to True + `parent_doc_top_k=1` + `parent_doc_section_depth_offset=1` + `parent_doc_max_tokens_per_parent=4000` + `parent_doc_fallback_to_doc_on_shallow=True`)全部 W26 F2 G defaults — 唔同時調 |

**Out of scope**(stricter than R-W26-1 broader umbrella;留下 separate experiments for clean isolation):
- ❌ `max_tokens_per_parent` sweep(2000 / 1500 — W27+ candidate (b) separate phase)
- ❌ `parent_doc_top_k` sweep(2 / 3 — W27+ candidate (b) separate phase)
- ❌ section_path dedupe strategy variants(W27+ candidate (b) separate phase)
- ❌ RAGAs orchestrator-aware judge tune(W27+ candidate (c) separate phase per R-W26-2)
- ❌ F3 query expansion standalone test(W27+ candidate (d) separate phase)
- ❌ `architecture.md §3.6` default flip(per Q4 measurement-experiment-fail-policy — defer until clear measurable win)

### 1.3 Sprint week origin

**W19+ rolling JIT**(per CLAUDE.md §10 R1 + session-start.md §10 W27+ row);呢個 phase **唔喺 architecture.md §6.1 原 W1-W12 sprint 表內** — 屬 W26 closeout 觸發嘅 follow-up experiment(類似 W25.5 BUG-025 fix 嘅 rolling 性質)。

---

## 2. Deliverables

### F0 — Kickoff(plan + checklist + progress + R6 grep verify)— DONE Day 0

- **Spec ref**:CLAUDE.md §10 R1 + R6
- **H1 trigger**:否(governance only)
- **Acceptance criteria**:
  1. ✅ `docs/01-planning/W27-parent-doc-dispatch-experiment/{plan.md,checklist.md,progress.md}` committed
  2. ✅ R6 pre-active-flip 5-step recursive grep verification at Day 0 — ADR-0037 §229 wording vs `prompt_builder.py:55-59` 實作對齊 verified;規模 estimate 由 ~50 LOC adjust upward to ~80-120 LOC + render strategy ambiguity surfaced(see §7 Plan Changelog Day 0 entry)
  3. session-start.md §10 timeline row added(W27 active status);§11 W26 CLOSED block retained 作 context handoff
- **Effort estimate**:~1-2h(Day 0)
- **Owner**:AI

### F1 — Implementation:Setting + prompt_builder branch + unit tests

- **Spec ref**:`architecture.md §3.1` query pipeline + `§3.5` ChunkRecord citation contract + ADR-0037 §229 dispatch chain(extending from replace to enum-branched)
- **H1 trigger**:否 — `prompt_builder.py` 屬 C05 Generation internal implementation(non-component;no vendor swap;no storage layout change;no 8-view layout philosophy change)
- **OQ deps**:無新 OQ
- **Acceptance criteria**(5 categories):

  **A. Setting addition**:
  1. `backend/storage/settings.py` NEW field:`parent_doc_dispatch_mode: Literal["replace", "append"] = "replace"`(default preserves W26 F2 G semantics per Q4 measurement-experiment-fail-policy 唔污染 production behavior)

  **B. Prompt builder dispatch branching**:
  2. `backend/generation/prompt_builder.py` `_format_chunk` 函數 branch on `Settings.parent_doc_dispatch_mode`:
     - `"replace"` branch:現有 line 55-59 `or` chain semantics 保持不變(W26 F2 G behavioral parity)
     - `"append"` branch:當 `parent_section_text` 存在,render 為 2-segment format —— anchor `chunk_text` 主段 + delimiter + parent section context 段(render strategy 細節 per F1 D1 R6 recursive sub-verify before active flip,defaulting to Option (i) single chunk header + `Parent section context:` sub-section delimiter per Karpathy §1.2 simplicity)
  3. Citation invariant preserved on both branches:`Citation.chunk_text = original_chunk.chunk_text`(unchanged per architecture.md §3.5)— append mode 加 parent context **唔改** citation card display surface

  **C. Tests**:
  4. ≥ 3 NEW unit tests in `backend/tests/test_prompt_builder_dispatch.py`(W26 F2 existing file extension):
     - `test_format_chunk_dispatch_replace_mode_preserves_w26_semantics`(replace branch = current behavior;regression-guard against W26 F2 G existing 7 dispatch tests)
     - `test_format_chunk_dispatch_append_mode_includes_both_segments`(LLM input contains BOTH `chunk_text` raw + parent section context delimiter)
     - `test_format_chunk_dispatch_append_mode_no_parent_section_falls_back_to_replace_chain`(append + 無 `parent_section_text` field → behave as replace chain `expanded_text > chunk_text`)
     - Optional 4th: `test_format_chunk_dispatch_append_mode_citation_chunk_id_preserved`(citation invariant explicit verification)
  5. Existing 7 W26 F2 dispatch tests `test_prompt_builder_dispatch.py` 全部 pass(regression-guard)

  **D. Code quality gates**:
  6. mypy strict delta 0(touched files only — 維持 W26 baseline 13 errors pre-existing `CO_W25_mypy_strict_debt`)
  7. ruff clean delta 0
  8. backend pytest full run regression 0(W26 baseline 1056 → ≥ 1059 W27 F1)

  **E. Observability(optional minor)**:
  9. Langfuse trace existing `generation.parent_doc_retrieval` stage 加 `dispatch_mode` field(append / replace)— `backend/observability/observe.py` 1-line addition;optional per Karpathy §1.3 surgical(若 W26 F2 stage 已存在 `dispatch_mode` evidence 可 skip)
- **Effort estimate**:~3-5h(Setting + prompt_builder + 3-4 tests + R6 sub-verify before active flip)
- **Owner**:AI

### F2 — G RAGAs delta vs F1(W26 D1)+ W26 F2 G(replace)baselines

- **Spec ref**:Brief §4 eval-driven methodology + W26 F1 baseline + W26 F2 G replace baseline
- **H1 trigger**:否(measurement only)
- **OQ deps**:**R8 prerequisite**(per §4 R1 risk — Azure OpenAI judge key + Cohere production reranker key environment)
- **Acceptance criteria**:

  **A. R8 prerequisite gate**(STOP and ask if blocked):
  1. Azure OpenAI judge key + Cohere v4.0-pro reranker key available in dev / personal Azure tier per ADR-0017 Plan B (c) precedent
  2. Blocked → STOP and ask Chris before F2 active flip(per W25 F4 / W26 F1 deferred reason pattern)

  **B. Both-baseline RAGAs eval execution**:
  3. Append mode through `eval-set-v0-w25-supplement.yaml` 13 queries via `/eval/run`(Settings.parent_doc_dispatch_mode="append" + `enable_parent_doc_retrieval=true` env override)
  4. 兩 baseline 對比:
     - **F1 baseline**(W26 D1 no-parent-doc control)— `parent-doc-metrics-W27-D{N}.md` 比較 column 1
     - **W26 F2 G baseline**(replace mode)— `parent-doc-metrics-W27-D{N}.md` 比較 column 2
  5. Per-query 4-metric delta + aggregated mean:faithfulness / answer_relevancy / context_precision / context_recall

  **C. Hard gates G1-G4 evaluation**:
  6. G1 evaluation:append mode aggregate faithfulness 回升至 F1 baseline ±2pp(0.9851 ± 0.02 = [0.9651, 1.0])
  7. G2 evaluation:append mode aggregate correctness 回升至 F1 baseline ±2pp(0.7416 ± 0.02 = [0.7216, 0.7616])
  8. G3 evaluation:Q-W25-I07 faithfulness > 0.5(W26 F2 G replace 0.00 → append > 0.5 minimum bar)
  9. G4 evaluation:Q-W25-I01 控制組 不再 regression(answer_relevancy ≥ F1 baseline ± 0.05)

  **D. Documentation**:
  10. Output:`docs/01-planning/W27-parent-doc-dispatch-experiment/append-mode-metrics-W27-D{N}.md` — markdown report containing per-query 4-metric + aggregated table + plain-text interpretation:「append mode vs replace mode vs no-parent-doc 三方對比 → G1-G4 PASS/FAIL judgement → F3 closeout decision input」
  11. Raw eval payload:`docs/01-planning/W27-parent-doc-dispatch-experiment/append-mode-metrics-W27-D{N}-raw.json`(per W26 D5 precedent)
- **Effort estimate**:~4-6h(eval run ~10min + analysis + report)+ may extend if R8 partial
- **Owner**:AI(measurement run)+ Chris(若 R8 partial 提供 personal Azure tier credentials)

### F3 — Closeout — ADR amendment OR ADR-0038 supersede + cross-doc sync

- **Spec ref**:CLAUDE.md §10 R3 + R5 + R6
- **H1 trigger**:可能(若 G3+G4 PASS → ADR-0037 amendment default mode flip;若 FAIL → NEW ADR-0038 documents finding)
- **OQ deps**:無
- **Acceptance criteria**:

  **A. ADR governance per G result**:
  1. **若 G3 + G4 雙 PASS**(append mode 解 RAGAs judge mismatch confirmed)→ **ADR-0037 amendment** per ADR-0017 5-amendment precedent + same decision family rationale:
     - `parent_doc_dispatch_mode` default flip "replace" → "append"(per measurement-experiment-fail-policy "win" branch)
     - Status「Accepted」→「Accepted; amended 2026-05-25 W27 F3 per dispatch chain append-vs-replace experiment」
     - NEW "Amendment 2026-05-25 W27 F3 — append dispatch chain" section
     - §6.4 Q-NEW append-vs-replace decision documented
  2. **若 G3 + G4 任一 FAIL**(append mode 唔解 RAGAs judge mismatch)→ **NEW ADR-0038** documents finding:
     - ADR-0038: "Parent-doc dispatch chain append mode — no-improvement finding;W27+ escalate to candidate (b) Setting sweep + (c) RAGAs orchestrator-aware tune"
     - Status: Accepted
     - Decision: parent-doc dispatch chain default mode preserves "replace"(W26 F2 G baseline);append mode tested + measurably no-improvement;next iteration scope = `max_tokens_per_parent` + `parent_doc_top_k` sweep OR RAGAs judge orchestrator-aware tune

  **B. Cross-doc sync per CLAUDE.md §10 R3 + R5 + R6**:
  3. plan.md frontmatter `status: draft → closed`(若 PASS)OR `closed_partial`(若 FAIL — measurement-experiment-fail-policy applicable)
  4. checklist.md cross-cutting 全 tick + 標明 deferred items per 🚧 reason
  5. progress.md retro 7-section + Phase Gate G1-G6 result + What worked / What didn't / Surprises / Carry-overs to W28+ / ADR triggers
  6. session-start.md §10 timeline row update(W27 closed status)+ §11 W27 CLOSED block prepend(若 PASS)OR W27 PARTIAL closed_partial block prepend(若 FAIL — per W26 PARTIAL precedent)
  7. RISK_REGISTER R-W26-1 update:status flip per result(Mitigated 若 PASS / Confirmed-hypothesis-rejected 若 FAIL — W27+ candidates (b) + (c) elevated)
  8. COMPONENT_CATALOG.md C05 status note 1-line append:「W27 F3 dispatch_mode `replace|append` enum landed;default per G result」

  **C. Measurement-experiment-fail-policy applicable per Q4**:
  9. G result FAIL → Settings default preserve "replace" + flag `enable_parent_doc_retrieval=False` 唔觸 revert per Karpathy §1.3 surgical(同 W26 F2 G FAIL precedent)
- **Effort estimate**:~2-3h(ADR + cross-doc)
- **Owner**:AI

---

## 3. Success Criteria(Phase Gate)

| # | Criterion | Target | Measure | Block phase closeout? |
|---|---|---|---|---|
| G1 | append mode aggregate faithfulness vs F1 baseline ±2pp | 0.9651 ≤ x ≤ 1.0 | `eval/run` 13-query | Yes |
| G2 | append mode aggregate correctness vs F1 baseline ±2pp | 0.7216 ≤ x ≤ 0.7616 | `eval/run` 13-query | Yes |
| G3 | Q-W25-I07 faithfulness recovery | > 0.5(W26 F2 G replace 0.00 → > 0.5)| `eval/run` per-query | Yes |
| G4 | Q-W25-I01 控制組不再 regression | answer_relevancy ≥ F1 ± 0.05 | `eval/run` per-query | Yes |
| G5 | pytest delta + code gates green | ≥ 3 NEW dispatch tests pass + mypy strict delta 0 + ruff clean + 1059 ≥ existing W26 baseline | `pytest tests/` + `mypy --strict` + `ruff check` | Yes |
| G6 | Measurement-experiment-fail-policy applied(若 FAIL → default preserve replace 唔觸 revert)| 唔回滾 W26 F2 ship | Settings default value verification + ADR-0037 amended OR ADR-0038 new ship | Yes |

**Gate verdict policy**:
- G1 + G2 + G3 + G4 + G5 全 PASS → **Phase Gate PASS** → ADR-0037 amendment + default flip
- G1 + G2 + G3 + G4 任一 FAIL → **Phase Gate PARTIAL** per W26 F2 G precedent + ADR-0038 new(documents finding) + W27+ candidates (b) + (c) elevated + Settings default preserve "replace"
- G5 FAIL → **Phase Gate FAIL** → block closeout(code-quality issue must resolve before measurement gate)
- G6 FAIL → impossible by construction(automatic per Q4 policy)

---

## 4. Risks(Phase-Specific)

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | R8 Azure-key-bound F2 G eval defers(per W25 F4 / W26 F1 deferred precedent — corp proxy / Azure key environment unavailable)| **High** | **Medium**(blocks G1-G4 measurement;Settings + prompt_builder + tests F1 still landable;F3 G result defer W28+)| Per ADR-0017 Plan B (c)precedent — Chris personal Azure tier credentials;若 仍 blocked → STOP and ask Chris;F2 deferred caveat trigger PARTIAL closeout(F1 ship + F2/F3 W28+) |
| R2 | Append mode regress G5 backend pytest(現有 W26 F2 G existing 7 dispatch tests rely on `or` chain `parent_section_text` 優先 semantics)| **Low** | **Medium** | Per F1 acceptance B.2 — `replace` branch preserves W26 F2 G semantics by construction;regression-guard existing 7 tests in F1 D1 active flip;若 fail → rollback + R6 recursive re-verify before re-flip |
| R3 | Append mode 加 parent context + chunk_text 雙段 token cost growth(per query 加 ~30-40% LLM input tokens vs replace mode)| **Medium** | **Low**(GPT-5.5 input rate low;within ADR-0034 P95<5s latency budget per W26 F2 measurement)| F2 G report 量度 per-query latency + token cost delta + ADR-0034 latency budget conformance;若 budget exceed → log W27+ candidate (b) `max_tokens_per_parent` 2000/1500 sweep |
| R4 | F1 D1 render strategy ambiguity(Option (i) single chunk header w/ delimiter sub-section vs Option (ii) 2 chunk entries)— wrong pick may surface only at F2 G result and require re-iterate | **Low** | **Medium** | R6 sub-verify before active flip(F1 D1):read existing 7 W26 dispatch tests + Karpathy §1.2 simplicity favors (i);若 F2 G FAIL 且 root-cause-traceable 到 render confusion → W28+ NEW phase test Option (ii) |
| R5 | RAGAs judge orchestrator-aware mismatch root cause **wider** than dispatch chain(per W26 D1.35 hypothesis 4-axis — append mode 唔修 root cause)→ G3 + G4 仍 FAIL despite append | **Medium** | **Medium**(對 W27 PARTIAL — 但 confirms judge mechanism is the architectural issue,not dispatch chain;W27+ candidate (c) RAGAs orchestrator-aware tune elevated 為 W28+ priority candidate)| F2 G result root cause framing 寫入 ADR-0038 + retro carry-over to W28+ candidate (c) per R-W26-2 |

---

## 5. Day-by-Day Breakdown(rough)

| Day | Date | Focus | Deliverables targeted |
|---|---|---|---|
| D0 | 2026-05-25 | Kickoff + R6 grep verify + plan/checklist/progress drafts + commit | F0 |
| D1 | 2026-05-25 | F1 D1 R6 sub-verify(render strategy)+ F1 implementation(Setting + prompt_builder branch + 3-4 unit tests)+ commit | F1 |
| D2 | 2026-05-25 | F2 R8 prerequisite check + F2 G RAGAs eval run + report + R8 partial → STOP and ask Chris(若 blocked)| F2 |
| D3 | 2026-05-25 | F3 closeout — ADR amendment OR ADR-0038 + cross-doc sync per R3 + R5 + R6 | F3 |

**Real-calendar collapse expectation**:~25-30× per W22-W26 AI compression pattern — ~1 actual day 條件下 condensed across 2026-05-25 vs ~3-day plan-day budget。

---

## 6. Dependencies on Prior Phase

Carry-over from `W26-eval-driven-retrieval-tuning/progress.md` retro:
- **R-W26-1** Dispatch chain append-vs-replace experiment(最直接解 RAGAs judge mismatch — 本 phase 直接 address)
- **R-W26-2** RAGAs faithfulness judge orchestrator-aware tune(W28+ candidate (c) — 本 phase F2 G result FAIL 觸發 elevate)
- W26 F1 baseline `baseline-metrics-W26-D1.md` 作 F2 G baseline reference column 1
- W26 F2 G replace mode `parent-doc-metrics-W26-D5.md` 作 F2 G baseline reference column 2
- W26 ADR-0037 §229 dispatch chain wording + `prompt_builder.py:55-59` 實作對齊(F0 R6 verified)
- W26 F2 existing 7 dispatch tests(F1 regression-guard)

---

## 7. Plan Changelog

| Date | Change | Reason | Approver |
|---|---|---|---|
| 2026-05-25 | Initial plan | W27 kickoff post W26 PARTIAL closeout — Chris pick (a) dispatch chain append-vs-replace experiment + 3 AskUserQuestion Recommended picks(phase 命名 + Setting enum + Both-baseline G eval) | Chris |
| 2026-05-25 | F0 R6 recursive grep verify Day 0 — ADR-0037 §229 dispatch chain wording vs `prompt_builder.py:55-59` 實作 verified 一致 = replace semantics(top-priority-wins `or` chain;top-1 anchor 嘅 `chunk_text` LLM 完全唔見);W26 D1.35 hypothesis「dispatch replace-vs-append architectural variable」accuracy 由 code reality 確認;**規模 estimate adjust upward** by ~30-70 LOC(~50 → ~80-120 LOC,反映 conditional rendering + 3-4 unit tests + 可選 observability emit field);**render strategy ambiguity surfaced** F1 D1 R6 sub-verify 待 verify(Option (i) single chunk header + `Parent section context:` delimiter sub-section per Karpathy §1.2 simplicity defaulting vs Option (ii) 2 chunk entries — 細節 F1 D1 active flip 前 lock)| W22 D9 plan-text-contamination prevention | AI(R6 recursive scope per CLAUDE.md §10 R6) |

---

**Lifecycle reminder**:呢份 plan locked after status=active。重大 deviation 入第 7 節 changelog,小 detail 變動可直接 inline edit。
