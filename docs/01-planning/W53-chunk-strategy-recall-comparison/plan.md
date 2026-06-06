---
phase: W53-chunk-strategy-recall-comparison
name: "Chunk-Strategy Recall Comparison (heading_aware 真 strategy + per-config synthetic recall — 兩者合一下半截)"
sprint_week: W53
start_date: 2026-06-06
end_date: 2026-06-06          # actual close (D1; F0-F4 same-day)
status: closed
spec_refs:
  - W52 (synthetic-QA recall 基建 — 本期 reuse run_synthetic_recall 跨 strategy 比較)
  - ROADMAP-per-kb-tunable-config.md (兩者合一:W52 recall 基建 → W53 reindex strategy 比較)
  - architecture.md §3.3 + §3.5 (Multi-Format Strategy + chunking — heading_aware 改 chunking 行為 → H1 → ADR-0044)
  - architecture.md §4.5 (KbConfig.chunk_strategy enum — heading_aware 已列但 deferred)
  - ADR-0041/0042/0043 (chunker lineage:image-density / per-KB cap factory / reindex)
  - backend/ingestion/chunker/strategies.py (select_chunker — heading_aware 現 raise NotImplementedError)
  - backend/ingestion/chunker/layout_aware.py (LayoutAwareChunker — heading_aware reuse section-walk/token/image-cap 基礎設施)
  - backend/api/routes/documents.py (_select_chunker — 現只睇 cap,IGNORE chunk_strategy;本期補 wiring)
  - backend/eval/synthetic_qa.py (W52 run_synthetic_recall — 本期 per-config reuse)
prior_phase: W52-synthetic-qa-recall-harness
combined_vision: "兩者合一(synthetic-QA 做 ingestion eval 指標)— W52 = recall 基建(done);W53 = chunk-strategy 比較(本期,下半截)"
---

# Phase W53 — Chunk-Strategy Recall Comparison

> **Plan version**:1.0(initial)
> **Owner**:Chris(Tech Lead)
> **Approved by**:Chris(2026-06-06 AskUserQuestion:比較軸 = **實作 heading_aware 真 strategy**;Recall 方法學 = **per-config 重生 QA(最大 reuse W52)**)

## 1. Scope

收 **兩者合一願景嘅下半截**:W52 起咗 self-supervised recall 基建,本期用佢**跨 chunk_strategy 比較** ingestion 質素 —— 但 think-before-coding(§1.1)+ R6 grep 揭咗三個 code-reality 令字面「跨 chunk_strategy 比較」唔成立:

1. **`chunk_strategy` 比較係 degenerate**:`auto`/`layout_aware`/`slide_based` 全部 delegate 去同一個 `LayoutAwareChunker`;`heading_aware` `raise NotImplementedError`(W3+ deferred)→ 冇兩個真正唔同嘅 strategy 可比。
2. **`_select_chunker`(reindex 路徑)只睇 `chunker_max_images_per_chunk` cap,IGNORE `chunk_strategy`** → 即使實作 heading_aware,reindex 都唔會用到佢(W46 reindex docstring「chunk_strategy change takes effect」係 over-promise)。
3. **跨 reindex chunk_id 會變** → W52 strict chunk_id recall 唔能跨 strategy 直接 reuse(已由方法學決策解決)。

**Chris 決策(AskUserQuestion 2026-06-06)**:
- **比較軸 = 實作 `heading_aware` 真 strategy**(令 `chunk_strategy` 真正有兩個唔同選項可比)
- **Recall 方法學 = per-config 重生 QA**(每 strategy reindex 後由**它自己 chunks** 重生 synthetic QA → 跑 W52 strict recall;直接 reuse `run_synthetic_recall` 逐 strategy)

**本期交付**:
- **`heading_aware` 真 chunker**(C01):section-bounded 粗粒度 chunking(只喺 `hard_cap_tokens` embedding 安全線 split,**無 target_tokens 平衡 split、無 min-merge**)→ vs `layout_aware`(target-balanced + merge)產生**明顯唔同 chunking**(粗/少 chunk)→ 有意義 recall 比較。設計 = ADR-0044 核心決定。
- **Wire `chunk_strategy` 入 `_select_chunker`**(C01/route):reindex 真正 honor strategy(heading_aware → HeadingAwareChunker;else → LayoutAwareChunker;兩者都 combine image-cap)→ 順帶 close 發現 2 嘅 W46 over-promise gap。
- **Strategy-recall 比較 harness**(C06 eval):per strategy 設 chunk_strategy → reindex → `run_synthetic_recall`(W52 reuse)→ 收集 recall + chunk 數 → 比較報告 + CLI。
- **ADR-0044**(H1 — heading_aware chunking 設計 + chunk_strategy wiring)。

**Recall 方法學誠實 framing(R1 延續)**:per-config 重生 QA → 每 strategy **問題集唔同**(由自己 chunks 生成)→ recall 差異**含問題難度 confounding** → 量度嘅係**「self-retrievability(自檢索性)— 呢個 chunking 之下答案 chunk 幾易被檢索返」**,**非 controlled A/B**(同問題跨 strategy)。報告必須標清係 self-retrievability 比較,非絕對質素 verdict;且建基於 W52 synthetic recall(非人手 ground truth)。

**Out-of-scope(Karpathy simplicity)**:
- **chunk size(target/hard_cap tokens)per-KB exposed**:本期唔開呢個 plumbing(留更未來;比較軸用 heading_aware vs layout_aware)。
- **controlled A/B(shared text-anchored QA)**:Chris 揀 per-config 重生(否決較重 keyword-recall harness);留更未來。
- **slide_based 真分化**:仍同 layout_aware(PPT-specific chunking 未出現,per strategies.py docstring)。
- production v1→v2 atomic 切換(Track A)/ per-document scope(決策 1)。

**Sprint week origin**:兩者合一下半截;Chris 2026-06-06 pick(W52 closeout 後)。

## 2. Key Design Decisions(kickoff lock)

- **heading_aware 語意(ADR-0044 核心)**:**section-bounded** —— 每 heading-bounded section 盡量做一個 chunk,**只喺超 `hard_cap_tokens`(embedding 8191 安全線)先 split**,**無 target_tokens 平衡 split**、**無 min-chunk merge**。對比 `layout_aware`(target ~平衡 + merge tiny)→ heading_aware 產生**更粗、更少** chunk。仍 honor image-cap force-split(保留 W44 圖洪保護)。實作 reuse LayoutAwareChunker 嘅 section-walk / token-count / image-cap 基礎設施(Karpathy:唔重寫 parsing,只換 split/merge policy)。
- **chunk_strategy dispatch 唔需 doc_format**:heading_aware vs layout_aware 都食同一 Docling ParserResult 結構;`auto→slide_based`(pptx)degenerate(==layout_aware)→ `_select_chunker` 純按 `chunk_strategy` dispatch(`heading_aware`→HeadingAware;其餘→LayoutAware),combine cap。
- **per-config 重生 QA(reuse W52)**:比較 harness 逐 strategy:`service` set `chunk_strategy` → `run_kb_reindex` in-place → `run_synthetic_recall`(同 seed/sample,但問題由各自 chunks 生)→ 收 recall + chunk 數。**直接 reuse `run_synthetic_recall`**(零新 recall 數學;零 W52 改動)。
- **harness 依賴可注入**:reindex_fn / recall_fn / generate_fn 注入 → core 可 stub 測試;live CLI bootstrap 同 W52(`scripts/`)。
- **ADR-0044 必寫**(H1):heading_aware chunking 設計 + `_select_chunker` strategy wiring(改 §3.3/§3.5 chunking 行為)。
- **無新 vendor / dep**:reuse 既有 chunker 基礎設施 + W52 harness;openai/yaml 現成。

## 3. Deliverables

### F0 — Phase kickoff
- **Acceptance criteria**:plan/checklist/progress committed(R1);scope(heading_aware 真 strategy / per-config 重生 QA self-retrievability / 三個 R6 發現)+ key design 鎖定;R6 grep 記 progress
- **Owner**:AI

### F1 — ADR-0044(heading_aware chunk strategy + chunk_strategy ingest wiring)
- **Spec ref**:architecture.md §3.3/§3.5/§4.5;ADR-0041/0042/0043 lineage
- **Acceptance criteria**:
  - `docs/adr/0044-heading-aware-chunk-strategy.md`(Context:三個 R6 發現;Decision:heading_aware section-bounded 語意 + `_select_chunker` strategy dispatch;Alternatives:image-cap 軸 / chunk-size plumbing / 維持 degenerate;Consequences;References)
  - ADR README index 加 0044 row;Status = Accepted(Chris AskUserQuestion 已批方向)
- **Owner**:AI

### F2 — heading_aware chunker + chunk_strategy wiring(C01)
- **Spec ref**:`chunker/strategies.py` + `chunker/layout_aware.py` + `routes/documents.py:_select_chunker`
- **Acceptance criteria**:
  - `HeadingAwareChunker`(section-bounded 語意;reuse layout_aware section-walk/token/image-cap;接 `max_images_per_chunk`)
  - `strategies.py select_chunker`:`heading_aware` → HeadingAwareChunker(移除 NotImplementedError)
  - `documents.py _select_chunker(deps, kb_config)`:按 `kb_config.chunk_strategy` dispatch(heading_aware → HeadingAware(cap);else → LayoutAware path)→ reindex 真 honor strategy(close 發現 2 gap)
  - mypy --strict(我改檔零新 error)+ ruff check+format clean
- **Owner**:AI

### F3 — Strategy-recall 比較 harness + CLI(C06 eval)
- **Spec ref**:reuse `eval/synthetic_qa.run_synthetic_recall`;`run_kb_reindex`;KBService set config
- **Acceptance criteria**:
  - `eval/synthetic_qa.py`(或新 module)NEW `run_strategy_recall_comparison(...)`:per strategy set chunk_strategy → reindex → run_synthetic_recall → `StrategyRecallComparison`(per strategy:recall + chunk 數 + sample 數);依賴可注入
  - thin CLI `scripts/run_strategy_recall_comparison.py`(mirror run_synthetic_recall bootstrap)
  - Live run smoke-deferred(judge cred + indexed KB + 原始檔 + 402 繞);整合由 F4 stub 全測
  - mypy + ruff clean
- **Owner**:AI

### F4 — Tests(H6 mandatory)+ Doc-sync + closeout
- **Acceptance criteria**:
  - **Tests(H6)**:
    - `test_heading_aware_chunker`:section-bounded(無 target-split / 無 merge;只 hard_cap split)→ 對同一 ParserResult,heading_aware chunk 數 < layout_aware(粗粒度)+ image-cap 仍生效
    - `_select_chunker` dispatch:chunk_strategy="heading_aware" → HeadingAwareChunker / 其餘 → LayoutAwareChunker(+ cap combine)
    - `run_strategy_recall_comparison`:stub reindex_fn + stub recall(per strategy 唔同 recall)→ 比較報告正確 assemble;既有 backend test 0 regression
  - **Doc-sync**:architecture.md §3.3/§3.5 + §5.5.5(或 §6 相關)W53 amendment(heading_aware 真 strategy + _select_chunker wiring + 比較 harness;標 self-retrievability 非 controlled A/B)+ ADR-0044 cross-ref;eval-methodology.md §10.6 補 per-config 重生 confounding note;roadmap 兩者合一下半截 → ✅ W53 shipped + 修訂史;session-start §10 W53 row + W54+ rolling JIT(local-only);plan status→closed + changelog
  - Phase Gate G1-G5 + retro + carry-overs + checklist tick / 🚧
- **Owner**:AI

## 4. Success Criteria(Phase Gate)

| # | Criterion | Target | Measure | Block closeout? |
|---|---|---|---|---|
| G1 | heading_aware 真 chunker（section-bounded，明顯異於 layout_aware）| chunk 數 < layout_aware；image-cap 仍生效 | pytest | Yes |
| G2 | `_select_chunker` 真 honor chunk_strategy（reindex 用對 chunker）| dispatch test | pytest | Yes |
| G3 | 比較 harness 跨 strategy reuse W52 recall（零新 recall 數學）| stub 比較報告正確 | pytest 整合 | Yes |
| G4 | self-retrievability framing 誠實（非 controlled A/B，建基 synthetic recall）| 文案/docstring/ADR review | review | Yes |
| G5 | ADR-0044 written + pytest+ruff+mypy clean + 0 regression + 無新 vendor/dep | all green | CI + review | Yes |

## 5. Risks(Phase-Specific)

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | heading_aware section 過大爆 embedding token limit | Med | High | hard_cap_tokens split（embedding 8191 安全線）保留；reuse layout_aware hard-cap 機制 |
| R2 | per-config 重生 QA confounding 被當 controlled A/B（誤導）| Med | High | 文案/docstring/報告標清 **self-retrievability 非 controlled A/B**；建基 W52 synthetic recall（非人手 ground truth）|
| R3 | heading_aware 同 layout_aware 差異唔夠大（比較無信號）| Low | Med | section-bounded 無 target-split/merge → 結構性粗化必異於 target-balanced；chunk 數差異 test 驗證 |
| R4 | _select_chunker wiring 爆既有 ingest/reindex（layout_aware/cap regression）| Med | High | dispatch 預設 fall-through 維持 layout_aware + cap 現行為（bit-identical when strategy≠heading_aware）；test_kb_reindex 0 regression |
| R5 | live 比較 run 卡 judge cred / 402 / 原始檔缺 | High | Low | 整合全 stub-test；live smoke-deferred（慣例）|
| R6 | H1 / ADR scope creep（heading_aware 設計過度）| Low | Med | 語意鎖最簡（section-bounded only）；ADR-0044 限 heading_aware + wiring，唔開 chunk-size plumbing |

## 6. Day-by-Day Breakdown(rough)

| Day | Date | Focus | Deliverables |
|---|---|---|---|
| D1 | 2026-06-06 | F0 kickoff + F1 ADR-0044 + F2 chunker+wiring | F0-F2 |
| D2 | 2026-06-06+ | F3 比較 harness+CLI + F4 tests+doc+closeout | F3-F4 |

## 7. Plan Changelog

| Date | Change | Reason | Approver |
|---|---|---|---|
| 2026-06-06 | Initial plan | W53 kickoff;Chris AskUserQuestion(比較軸=實作 heading_aware 真 strategy / Recall=per-config 重生 QA reuse W52)。R6 grep 揭三發現(chunk_strategy degenerate / _select_chunker ignore strategy / chunk_id 跨 reindex 變);heading_aware section-bounded 語意 → ADR-0044(H1);順帶 close W46 reindex strategy-wiring over-promise gap | Chris |
| 2026-06-06 | F2 實作細節:`HeadingAwareChunker` = thin `LayoutAwareChunker` subclass(super().__init__ 後 flip `target_tokens=hard_cap_tokens` + `min_chunk_merge_floor=0`)而非全新 class — Karpathy zero parsing rewrite + 仍係「真 strategy class」(discoverable + 獨立 test) | F2 think-before-coding:LayoutAwareChunker 已用 param 控 split/merge policy → subclass flip 兩個 knob = 最簡達成 section-bounded(記 ADR-0044 Alternatives 已覆蓋)| AI |
| 2026-06-06 | status active → closed;end_date set(D1 全 F0-F4 同日)| Phase Gate G1-G5 PASS;兩者合一下半截 done(heading_aware 真 strategy + chunk-strategy self-retrievability 比較)| AI |

---

**Lifecycle reminder**:plan locked after status=active。重大 deviation 入第 7 節 changelog。**heading_aware 改 chunking 行為 = H1 → ADR-0044 必寫**(F1)。**Reuse W52 `run_synthetic_recall`**(零新 recall 數學)+ LayoutAwareChunker 基礎設施(零重寫 parsing)。**per-config 重生 QA = self-retrievability 非 controlled A/B** 必須誠實 framing(R1/R2)。**H6**:chunker + harness 同步 test。
