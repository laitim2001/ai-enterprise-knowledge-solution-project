---
phase: W54-controlled-ab-recall-comparison
name: "Controlled Shared-Question A/B Recall Comparison (text-anchored ground truth + keyword-mode recall — W53 self-retrievability 嚴謹版)"
sprint_week: W54
start_date: 2026-06-06
end_date: 2026-06-06          # actual close (D1; F0-F4 same-day)
status: closed
spec_refs:
  - W53 (chunk-strategy self-retrievability 比較 — 本期消除其 per-config 問題集 confounding)
  - W52 (synthetic-QA recall 基建 — reuse generator pattern + _collect_chunks)
  - ROADMAP-per-kb-tunable-config.md (W53 plan §1 明文 deferred「controlled A/B(shared text-anchored QA)」→ 本期收)
  - eval-methodology.md §10.6 (synthetic recall bias disclosure — 本期續寫 controlled-but-lexical 限制)
  - architecture.md §5.5.5 (Eval framework — 本期 W54 amendment;NON-architectural eval extension,無 H1)
  - backend/eval/runner.py (EvalRunner keyword-mode recall:runner.py:166-184 — 本期 reuse,零新 recall 數學)
  - backend/eval/synthetic_qa.py (W52 _collect_chunks + judge generator pattern — reuse)
  - backend/eval/strategy_comparison.py (W53 orchestration shape — parallel loop,但 W54 自有 controlled-framing dataclass)
prior_phase: W53-chunk-strategy-recall-comparison
combined_vision: "誠實 framing 階梯 — W51 coverage proxy → W52 synthetic 非人手 ground truth → W53 self-retrievability 非 controlled A/B → W54 controlled A/B(shared frozen question set;仍 synthetic + lexical-containment proxy)"
---

# Phase W54 — Controlled Shared-Question A/B Recall Comparison

> **Plan version**:1.0(initial）
> **Owner**:Chris(Tech Lead)
> **Approved by**:Chris(2026-06-06 — W53 closeout 後 explicit 指示「W54+ 起點 = controlled shared-question A/B（text-anchored ground truth + keyword-mode recall）—— W53 self-retrievability 嘅嚴謹版,消除 per-config 問題集 confounding」)

## 1. Scope

收 **W53 明文 deferred 嘅 controlled A/B**(W53 plan §1:「controlled A/B(shared text-anchored QA):Chris 揀 per-config 重生;留更未來」)。W53 用 **per-config 重生 QA** 比較 chunk_strategy → 每 strategy 問題集唔同 → recall delta **confounded by 問題難度**(量度 self-retrievability,非 controlled A/B)。本期消除呢個 confounding:**同一個 frozen question set 跨所有 strategy 評分**。

**think-before-coding(§1.1)+ R6 grep 揭嘅 code-reality**(令字面「需新 keyword harness」前提部份唔成立):

1. **EvalRunner 已內建 keyword-mode recall**(`runner.py:166-184`):mode 選擇 `use_strict = validated and acceptable_ids and not placeholder` → 否則走 keyword path:`recall = |expected_answer_keywords ∩ top-K chunk_text(case-insensitive substring)| / |expected_answer_keywords|`。**純 chunk_text 文字包含、chunk_id 無關** → 正正係跨 strategy 評分需要嘅 chunk_id-agnostic 指標 → **reuse 佢,零新 recall 數學**(mirror W52 reuse strict mode)。
2. **section_path 係 strategy-invariant**:W53 `HeadingAwareChunker` = `LayoutAwareChunker` subclass,繼承同一 section-walk → 兩個 strategy 對同一文件產生**相同 section_path**(headings 喺 parse 時定,先於 chunking)→ 可作 **strategy-independent 文字錨點**。
3. **W53 `run_strategy_recall_comparison` dataclass 唔可直接 reuse**:`StrategyRecallComparison` docstring 明標「**NOT a controlled A/B**」+ `recall_at_k` 標「self-supervised」→ 套去 W54 controlled A/B 會 **mislabel** → W54 需自己嘅 controlled-framing dataclass + thin loop(orchestration shape parallel 但語意誠實)。

**本期交付**:
- **Text-anchored shared QA 生成**(C06):reference index → `_collect_chunks`(reuse W52)→ 按 `(doc_id, section_path)` group 成 **section passages**(strategy-invariant 文字錨點)→ seeded 抽樣 → judge LLM 逐 passage 生 **一條問題 + 3-5 個 answer keywords** → **freeze** 成 EvalRunner keyword-mode eval-set YAML(`validated=False` + `expected_answer_keywords` 填值 → 保證走 keyword path)。**生成一次,跨 strategy 不變。**
- **Controlled 比較 harness**(C06):shared eval-set 生成一次(loop 前)→ per strategy:reindex → 用 **同一 frozen set** 跑 EvalRunner keyword mode → 收 recall + chunk 數 → `ControlledStrategyComparison`(controlled-A/B framing dataclass)+ best pick。依賴可注入(reindex_fn / score_fn / generate_fn)。
- **thin CLI**(`scripts/`):mirror W53 bootstrap(`async with lifespan(app)` + Request shim);live smoke-deferred。
- **Tests(H6)**+ doc-sync。

**誠實 framing(R1 延續第四期)**:本期 **IS** controlled(shared frozen set,只 chunk_strategy 變 → 消除 W53 per-config 問題集 confounding ✓ 用戶目標)。**但仍有兩個誠實限制必須標清**:
- **仍非人手 ground truth**:LLM 生成問題 + LLM 抽 keywords(承 W52 synthetic bias)。
- **keyword-containment 係 lexical proxy**:某 chunk 含 keyword ≠ 佢就係正確 answer-bearing chunk(較 chunk_id strict recall 粗)—— 係換取 chunk_id-agnostic 跨 strategy 評分嘅必要代價。section-anchored 問題可被多個 chunk 答中 → recall 偏寬鬆 → **相對信號,非絕對質素 verdict**。

**Out-of-scope(Karpathy simplicity)**:
- **人手標註 ground truth recall**(correctness / context_recall 真集)— 需人手標註集,留工程閘(承 AUDIT-D ii)。
- **新 chunk_strategy**(本期沿用 W53 ship 嘅 layout_aware / heading_aware 兩個真選項;slide_based 仍 degenerate)。
- **chunk size per-KB plumbing** / production v1→v2 atomic 切換(Track A)/ per-document scope(決策 1)。
- **改 EvalRunner keyword mode 行為**:純 reuse,唔郁(R4 regression 保護)。

**Sprint week origin**:W53 closeout 後 Chris 2026-06-06 explicit pick(rolling JIT,W53 已收尾才寫 W54 plan)。

## 2. Key Design Decisions(kickoff lock)

- **文字錨點 = strategy-invariant section passages**:按 `(doc_id, tuple(section_path))` group reference chunks,concat 各 section 文字成一個 passage(newline join;唔特別 dedup overlap — 對 LLM passage / keyword 抽取無害)。section_path 喺 parse 時定(R6 發現 2)→ layout_aware / heading_aware 共用 → 同一錨點集。大 section 截斷至 `max_passage_chars`(預設 ~4000)控 judge 成本 + 聚焦;空 / 過短 passage 丟。**選 section-anchored 而非 fixed-char-window**:section 係語意自然錨點 + 零新 windowing code + 直接 reuse `_collect_chunks` 已返嘅 `section_path`(Karpathy simplicity)。
- **keyword-mode recall = reuse EvalRunner**(R6 發現 1):eval-set 每條 `validated=False` + `acceptable_chunk_ids=[]` + `expected_answer_keywords=[…]` → EvalRunner `use_strict=False` → keyword path → `|keywords found in top-K text| / |keywords|`。**零新 recall 數學**(同 W52 reuse strict mode 對稱)。無 keyword 嘅 pair 丟(避免 EvalRunner `if expected_keywords else 0.0` 假 0)。
- **shared set 生成一次 + freeze**:`build_shared_eval_set(...)` 喺 strategy loop **之前** 跑一次,寫 frozen YAML(可審計 artifact)→ 每 strategy 用**同一檔**評分 → controlled。對比 W53(loop 內逐 strategy 重生)。
- **判 LLM 一次返 Q + keywords**(JSON):單次 call 令問題同 keywords 對齊 + 省成本;parse fail → 該 pair 丟(graceful)。judge = `gpt-5.4-mini`(成本政策,維持不升級);無 `azure_openai_api_key` → generator None → harness skip(同 W52 graceful-degradation 契約)。
- **W54 自有 controlled-framing dataclass + thin loop**(R6 發現 3):`ControlledStrategyResult` / `ControlledStrategyComparison`(明標 controlled A/B + lexical-containment proxy);loop shape parallel W53 但唔 reuse W53 dataclass(避免 mislabel)。真正 reuse 點 = EvalRunner keyword mode + `_collect_chunks` + W52 generator pattern。
- **無 H1 / 無新 vendor / dep**:純 C06 eval extension(同 W52,非 §3/§4 component 改動;EvalRunner keyword mode reuse 非改);openai / yaml 現成 → **唔需 ADR**(R5 closeout recheck)。

## 3. Deliverables

### F0 — Phase kickoff
- **Acceptance criteria**:plan/checklist/progress committed(R1);scope(controlled A/B 收 W53 deferred / section-anchored shared QA / keyword-mode reuse / 誠實限制)+ key design 鎖定;R6 grep 三發現記 progress
- **Owner**:AI

### F1 — Text-anchored shared QA 生成(C06)
- **Spec ref**:reuse `eval/synthetic_qa._collect_chunks` + judge generator pattern;EvalRunner keyword-mode eval-set schema(`runner.py`)
- **Acceptance criteria**:
  - NEW `backend/eval/controlled_comparison.py`:
    - `TextAnchoredQAPair`(question / expected_keywords / source_doc_id / source_section_path / source_text)
    - `make_qa_keyword_generator(settings) -> KeywordQAGenerateFn | None`(judge `gpt-5.4-mini` + `patch_for_gpt5`;單 call 返 `(question, keywords)`;JSON parse fail / 無 cred → None;mirror W52)
    - `build_section_passages(chunks) -> list[passage]`(group by doc_id+section_path,concat,截斷 max_passage_chars,丟空)
    - `generate_text_anchored_qa(passages, generate_fn, *, sample_size, seed, max_concurrency) -> list[TextAnchoredQAPair]`(seeded 抽樣 + sorted 穩定;無 keyword pair 丟)
    - `to_keyword_eval_set_payload(pairs, *, kb_id, seed) -> dict`(EvalRunner keyword-mode entries:`validated=False` + `expected_answer_keywords` 填值)
  - mypy --strict(改檔零 error)+ ruff check+format clean
- **Owner**:AI

### F2 — Controlled 比較 harness(C06)
- **Spec ref**:reuse EvalRunner keyword mode;W53 orchestration shape
- **Acceptance criteria**:
  - `controlled_comparison.py` NEW:
    - `build_shared_eval_set(engine, kb_id, *, generate_fn, output_path, sample_size, seed) -> int`(collect chunks → passages → generate → 寫 frozen YAML → 返 pair 數;空 → raise)
    - `ControlledStrategyResult`(strategy / recall_at_k / sample_size / chunk_count / errored)+ `ControlledStrategyComparison`(kb_id / top_k / eval_set_version / results / best_strategy;**docstring 明標 controlled A/B + lexical-containment proxy**)
    - `run_controlled_strategy_comparison(kb_id, strategies, *, reindex_with_strategy_fn, score_fn, top_k) -> ControlledStrategyComparison`(per strategy:reindex → score_fn() 跑同一 frozen set → 收;best=最高 recall;依賴可注入)
  - mypy + ruff clean
- **Owner**:AI

### F3 — CLI driver(scripts)
- **Spec ref**:mirror `scripts/run_strategy_recall_comparison.py`(W53 bootstrap)
- **Acceptance criteria**:
  - thin CLI `scripts/run_controlled_ab_comparison.py`(`async with lifespan(app)` 攞 populated state + Request shim;wire build_shared_eval_set 一次 → per strategy set config → run_kb_reindex → EvalRunner keyword mode 跑 frozen set;輸出 controlled-A/B 報告 + 誠實 caveat)
  - Live run smoke-deferred(judge cred + indexed KB + 原始檔 + Free-tier 402 繞);整合由 F4 stub 全測
  - mypy + ruff clean
- **Owner**:AI

### F4 — Tests(H6 mandatory)+ Doc-sync + closeout
- **Acceptance criteria**:
  - **Tests(H6)**:
    - `test_controlled_comparison.py`:
      - `build_section_passages`:group by doc_id+section_path 正確 / concat / 截斷 / 丟空
      - `generate_text_anchored_qa`:seeded 抽樣穩定 / 無 keyword pair 丟 / stub generator
      - `to_keyword_eval_set_payload`:`validated=False` + `expected_answer_keywords` 填值 → 餵 EvalRunner 真走 **keyword mode**(整合驗:stub engine 返含 keyword 文字 → recall 計算正確)
      - `run_controlled_strategy_comparison`:stub reindex + stub score(同一 frozen set,per strategy 唔同 recall)→ 報告 assemble + best pick + empty case
    - 既有 backend test 0 regression(eval suite + runner)
  - **Doc-sync**:architecture.md §5.5.5 W54 amendment(controlled A/B harness;NON-architectural eval extension 標明無 H1)+ W53 cross-ref;eval-methodology.md §10.6 加 W54 controlled-but-lexical 限制 note(承 synthetic bias + keyword-containment proxy);roadmap line 112 / §3 → ✅ W54 controlled A/B shipped + 修訂史;session-start §10 W54 closed row + W55+ rolling JIT(local-only);plan status→closed + changelog
  - Phase Gate G1-G5 + retro + carry-overs + checklist tick / 🚧 + R5 recheck(無 §3/§4 touch → 無 ADR)
- **Owner**:AI

## 4. Success Criteria(Phase Gate)

| # | Criterion | Target | Measure | Block closeout? |
|---|---|---|---|---|
| G1 | shared frozen question set 跨 strategy 不變(controlled — 消除 W53 per-config confounding)| 同一 eval-set YAML 餵每 strategy | pytest(score_fn 收同一 path)| Yes |
| G2 | keyword-mode recall reuse EvalRunner(零新 recall 數學)| eval-set 真走 keyword path + recall 計算正確 | pytest 整合(stub engine)| Yes |
| G3 | text-anchored section passages strategy-invariant(group by section_path)| build_section_passages test | pytest | Yes |
| G4 | controlled-A/B framing 誠實(明標 shared set 消 confounding;**但仍 synthetic + lexical-containment proxy 非人手 ground truth**)| docstring / 報告 / eval-methodology §10.6 review | review | Yes |
| G5 | pytest+ruff+mypy clean + 0 regression + 無新 vendor/dep + 無 H1(無 ADR)| all green | CI + review | Yes |

## 5. Risks(Phase-Specific)

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | controlled A/B 被當人手 ground-truth recall(誤導,over-claim)| Med | High | docstring / 報告 / eval-methodology §10.6 標清 **仍 synthetic(LLM Q + LLM keyword)+ keyword-containment lexical proxy**;對齊 memory W25 D4 stochastic over-claim 教訓 |
| R2 | keyword-containment 太寬鬆(任何含詞 chunk 算中 → recall 失辨別力)| Med | Med | keywords 取 3-5 個 distinctive answer terms(非 stopword);report 標明 lexical proxy + 相對信號;K 細(top_k=5)限寬鬆度 |
| R3 | section passage 過大 / 過細(問題質素差)| Med | Med | max_passage_chars 截斷 + 丟空/過短;seeded 抽樣可重現複查 |
| R4 | reuse EvalRunner 時 mode 選錯(誤入 strict → 跨 strategy chunk_id 全 miss → 假 0)| Low | High | eval-set `validated=False` + `acceptable_chunk_ids=[]` 保證 `use_strict=False`;F4 test 明確 assert mode=="keyword" |
| R5 | live 比較 run 卡 judge cred / 402 / 原始檔缺 | High | Low | 整合全 stub-test;live smoke-deferred(慣例)|
| R6 | scope creep(寫新 recall 數學 / 改 EvalRunner / 起 fixed-window machinery)| Low | Med | 鎖死 reuse EvalRunner keyword mode + section-anchored(零新 windowing);無 H1 → 唔開 ADR-scope |

## 6. Day-by-Day Breakdown(rough)

| Day | Date | Focus | Deliverables |
|---|---|---|---|
| D1 | 2026-06-06 | F0 kickoff + F1 QA 生成 + F2 harness | F0-F2 |
| D2 | 2026-06-06+ | F3 CLI + F4 tests+doc+closeout | F3-F4 |

## 7. Plan Changelog

| Date | Change | Reason | Approver |
|---|---|---|---|
| 2026-06-06 | Initial plan | W54 kickoff;Chris explicit 指示 controlled shared-question A/B(text-anchored + keyword-mode,W53 嚴謹版)。R6 grep 揭三發現(EvalRunner 已有 keyword mode → reuse 零新數學 / section_path strategy-invariant → 文字錨點 / W53 dataclass self-retrievability framing 不可 reuse → W54 自有 controlled dataclass)。無 H1(純 C06 eval extension,EvalRunner keyword mode reuse 非改)→ 無 ADR | Chris |
| 2026-06-06 | F1 deviation:`TextAnchoredQAPair` drop `source_doc_id`,`build_section_passages` group by `tuple(section_path)` 而非 `(doc_id, section_path)` | F1 R6 grep:reuse 嘅 `synthetic_qa._collect_chunks` 唔返 doc_id(只 chunk_id/chunk_text/section_path);加 doc_id 要改 W52 frozen module → 改為 section_path-only grouping + docstring 標明 multi-doc same-section merge caveat(truncation 保護;controlled 性不受影響)。Karpathy:最大 reuse,minor passage-quality caveat 換零 W52 改動 | AI |
| 2026-06-06 | F3 fix:CLI `run_kb_reindex` call `# type: ignore[arg-type]` 改 per-arg form | ruff format 將單行 call 拆多行 → ignore 移到 closing `)` 行 → mypy 報 line117 arg-type + line118 unused-ignore。per-arg(magic trailing comma 保持展開,ignore 釘 `request=request_shim,` 行)修正 | AI |
| 2026-06-06 | status active → closed;end_date set(D1 全 F0-F4 同日)| Phase Gate G1-G5 PASS;controlled shared-question A/B 落地(shared frozen text-anchored set + keyword-mode reuse + 消除 W53 per-config confounding)。誠實階梯第四期守住 | AI |

---

**Lifecycle reminder**:plan locked after status=active。重大 deviation 入第 7 節 changelog。**收 W53 明文 deferred 嘅 controlled A/B**。**Reuse EvalRunner keyword mode**(零新 recall 數學)+ `_collect_chunks` + W52 generator pattern。**controlled A/B 但仍 synthetic + lexical-containment proxy** 必須誠實 framing(R1,誠實階梯第四期)。**H6**:QA 生成 + harness 同步 test。**無 H1 → 無 ADR**(R5 closeout recheck)。
