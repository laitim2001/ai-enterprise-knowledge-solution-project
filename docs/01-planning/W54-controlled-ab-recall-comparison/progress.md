# W54 — Controlled Shared-Question A/B Recall Comparison · Progress

> Daily progress + decisions + commits + 結尾 retro。每 daily commit 對應 Day-N entry(R2)。

---

## Day 1 — 2026-06-06

### Context / kickoff
W53 closed + pushed(`505a2de`,heading_aware 真 strategy + chunk-strategy self-retrievability 比較)。用戶 explicit 指示 **W54 起點 = controlled shared-question A/B**(text-anchored ground truth + keyword-mode recall)—— **W53 self-retrievability 嘅嚴謹版,消除 per-config 問題集 confounding**。正正收 W53 plan §1 明文 deferred 嘅「controlled A/B(shared text-anchored QA)」。

### 決策(Chris explicit 指示 2026-06-06)
- **方法學 = controlled shared-question A/B**:同一個 **frozen question set** 跨所有 strategy 評分(對比 W53 per-config 重生 → 消除問題難度 confounding)
- **Ground truth = text-anchored**:錨喺文字(非 chunk_id;chunk_id 跨 reindex 變)
- **Recall = keyword-mode**:chunk_id-agnostic,跨 strategy 可比

### R6 grep 驗證(plan kickoff — 揭三個令字面前提部份唔成立嘅 code-reality)
1. **EvalRunner 已內建 keyword-mode recall**(`runner.py:166-184`):mode 選擇 `use_strict = validated and acceptable_ids and not placeholder-prefix`;否則走 keyword path → `recall = |expected_answer_keywords ∩ top-K chunk_text(case-insensitive substring)| / |expected_answer_keywords|`。**純文字包含、chunk_id 無關** = 跨 strategy 評分需要嘅指標 → **W53 summary 講「需新 keyword harness」前提部份唔成立** → reuse EvalRunner keyword mode,**零新 recall 數學**(mirror W52 reuse strict mode)。
2. **section_path 係 strategy-invariant**:W53 `HeadingAwareChunker` = `LayoutAwareChunker` subclass,繼承同一 section-walk → layout_aware / heading_aware 對同一文件產生**相同 section_path**(headings 喺 parse 定,先於 chunking)→ 可作 **strategy-independent 文字錨點**(按 section group passages)。
3. **W53 `run_strategy_recall_comparison` dataclass 不可直接 reuse**:`StrategyRecallComparison` docstring 明標「**NOT a controlled A/B**」+ `StrategyRecallResult.recall_at_k` 標「W52 self-supervised」→ 套去 W54 controlled A/B 會 **mislabel** → W54 自己嘅 `ControlledStrategyResult` / `ControlledStrategyComparison`(controlled-framing)+ thin loop;真正 reuse 點 = EvalRunner keyword mode + `_collect_chunks`(synthetic_qa)+ W52 generator pattern。

- `_collect_chunks(engine, kb_id)`(synthetic_qa.py)已返 `{chunk_id, chunk_text, section_path}` → 直接 reuse(同 package import)。
- 下一個 ADR = **0045**(W54 無 H1 → 唔用)。

### Key design lock(plan §2)
- **文字錨點 = strategy-invariant section passages**:group by `(doc_id, tuple(section_path))` → concat section 文字 → 截斷 `max_passage_chars`(~4000)→ 丟空/過短。選 section-anchored 而非 fixed-char-window(語意自然 + 零新 windowing code + reuse 已返 section_path;Karpathy simplicity)。
- **keyword-mode = reuse EvalRunner**:eval-set `validated=False` + `acceptable_chunk_ids=[]` + `expected_answer_keywords` 填值 → 保證 `use_strict=False` → keyword path。無 keyword pair 丟(避 `if expected_keywords else 0.0` 假 0)。
- **shared set 生成一次 + freeze**:`build_shared_eval_set(...)` 喺 strategy loop **前**跑一次,寫 frozen YAML(可審計)→ 每 strategy 用同一檔評分。
- **判 LLM 單 call 返 Q + keywords**(JSON);judge `gpt-5.4-mini`(成本政策);無 cred → None graceful。

### 誠實 framing(R1 — 誠實階梯第四期)
W51 coverage proxy → W52 synthetic 非人手 ground truth → W53 self-retrievability 非 controlled A/B → **W54 controlled A/B**(shared frozen set ✓ 消 confounding)。**但兩個限制仍要標清**:(1) 仍非人手 ground truth(LLM Q + LLM keyword);(2) keyword-containment 係 lexical proxy(含詞 chunk ≠ 正確 answer-bearing chunk;section-anchored 問題可被多 chunk 答中 → 偏寬鬆)→ **相對信號非絕對 verdict**。docstring / 報告 / eval-methodology §10.6 三處標。

### Done(F0)
- F0 R1 phase 三件套建立(plan/checklist/progress);Phase Gate G1-G5 定義;無 H1 → 無 ADR

### F1 text-anchored shared QA 生成(同日,C06)
- NEW `backend/eval/controlled_comparison.py`:`TextAnchoredQAPair`(question/expected_keywords/source_section_path/source_text)+ `KeywordQAGenerateFn` + `ControlledRecallError`
- `make_qa_keyword_generator`(judge `gpt-5.4-mini` + `patch_for_gpt5`;單 call 返 `(question, keywords)` JSON;`_parse_qa_keywords` pure 函式 — tolerant markdown ```json fence + validate question/keywords;parse fail/無 cred → None graceful)
- `build_section_passages`(group by `tuple(section_path)` → concat → 截斷 max_passage_chars=4000 → 丟 < min_passage_chars=40)
- `generate_text_anchored_qa`(seeded 抽樣 + sorted by section_path 穩定;無 keyword pair 丟)
- `to_keyword_eval_set_payload`(`validated=False` + `acceptable_chunk_ids=[]` + `expected_answer_keywords` 填值 → 保證 EvalRunner keyword path;metadata note 標 controlled-but-synthetic+lexical-proxy)
- **F1 deviation(R3,記 plan changelog)**:drop `source_doc_id` + section_path-only grouping(`_collect_chunks` 唔返 doc_id;避免改 W52 frozen module;multi-doc same-section merge caveat docstring 標明)
- ruff clean + auto-format;mypy controlled_comparison.py 零 error(exit 1 純 ragas_* 跨模組 pre-existing,同 W52 baseline)

### F2 controlled 比較 harness(同日,C06)
- `build_shared_eval_set`(reuse `_collect_chunks` → `build_section_passages` → `generate_text_anchored_qa` → `to_keyword_eval_set_payload` → 寫 frozen YAML 可審計 artifact → 返 pair 數;空 → `ControlledRecallError`)—— **loop 前跑一次,frozen set = controlled invariant**
- `ControlledStrategyResult` + `ControlledStrategyComparison`(controlled-framing dataclass;docstring 明標**對比 W53 `StrategyRecallComparison` self-retrievability** + 仍 synthetic + lexical-containment proxy);`ReindexWithStrategyFn` / `ScoreFn` type alias
- `run_controlled_strategy_comparison`:per strategy reindex → `score_fn()` 跑**同一 frozen set** → 收 recall+chunk數;best=最高 keyword recall;依賴可注入(W53 loop shape parallel,W54 自有 controlled dataclass + score_fn 取代 W53 per-config recall_fn)
- **真正 reuse 點**:EvalRunner keyword mode(零新 recall 數學)+ `_collect_chunks`(同 package import)+ W52 generator pattern
- ruff clean;mypy controlled_comparison.py 唯一 finding = `yaml import-untyped`(W52/runner.py:22 同款 baseline)

### F3 CLI driver(同日,scripts)
- NEW `scripts/run_controlled_ab_comparison.py`:mirror W53 bootstrap(`async with lifespan(app)` + Request shim);**關鍵差異** = `build_shared_eval_set` 喺 loop 前跑一次(讀回 version)→ per strategy `update_config`→`run_kb_reindex`→`EvalRunner` keyword mode 跑**同一 frozen set**;輸出報告 + controlled-but-synthetic+lexical caveat;live smoke-deferred
- **F3 formatter 坑修正**:ruff format 將 `run_kb_reindex` call 拆多行,`# type: ignore[arg-type]` 移到 closing `)` 行 → mypy 報 line117 arg-type + line118 unused-ignore。改 per-arg form(magic trailing comma 保持展開,ignore 釘 `request=request_shim,` 行)→ 修正後唯一 finding = yaml baseline

### F4 tests(同日,H6)
- `test_controlled_comparison.py` 13 test:`_parse_qa_keywords`(JSON/markdown fence+dedupe/7 malformed reject)+ `build_section_passages`(group/concat/截斷/丟空丟短)+ `generate_text_anchored_qa`(seeded 穩定/丟 keyword-less)+ `to_keyword_eval_set_payload` shape + **EvalRunner keyword-mode 整合(R4:assert mode=="keyword" + recall=(1.0+0.5)/2)** + `build_shared_eval_set` round-trip + `run_controlled_strategy_comparison`(assemble+best pick+empty)+ generator None guard
- 驗:test_controlled_comparison+synthetic_qa+strategy_comparison+eval_runner **31 passed**;廣 eval suite(8 檔)**82 passed**(cold 95s)= **0 regression**(無改任何現有檔,純新增)
- ruff clean;mypy controlled_comparison.py + script 唯一 finding = yaml import-untyped baseline

### Commits
- `dec9373` F0 kickoff + `dda0574` F1 QA 生成 + `5eb1baf` F2 harness + `<pending>` F3-F4 CLI+tests
