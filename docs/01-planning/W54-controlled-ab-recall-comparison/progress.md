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

### F4 doc-sync(同日)
- architecture.md §5.5.5 NEW **W54 amendment**(controlled shared-question A/B;標明 backend-only **無 H7 無 H1** 純 C06 eval extension;三 R6 發現 + 誠實階梯第四期限制)
- eval-methodology.md §10.6 加 **W54 controlled-but-lexical note**(承 W53 note:IS controlled 消 confounding,但仍 synthetic + keyword-containment lexical proxy → 相對信號非 production verdict;真 ground-truth recall 留 W55+)
- roadmap line 112 lineage → ✅ W54 shipped + 修訂史 2026-06-06 W54 entry(置頂)
- session-start §10 W54 closed row + W55+ rolling JIT row(local-only,不入 git)
- plan.md status→closed + changelog(F1 deviation / F3 type:ignore fix / closeout)

### Phase Gate G1-G5 — **PASS**

| # | Criterion | Verdict | Evidence |
|---|---|---|---|
| G1 | shared frozen question set 跨 strategy 不變(controlled — 消除 W53 per-config confounding)| ✅ PASS | `run_controlled_strategy_comparison` score_fn 跑同一 frozen path;`test_run_controlled_strategy_comparison`:同一 score stub 跨 strategy;CLI `build_shared_eval_set` loop 前一次寫 frozen YAML |
| G2 | keyword-mode recall reuse EvalRunner(零新 recall 數學)| ✅ PASS | `test_keyword_eval_set_scores_keyword_mode`:payload 餵 `EvalRunner` → **assert mode=="keyword"** + recall=(1.0+0.5)/2 正確(R4 保護,確認唔誤入 strict)|
| G3 | text-anchored section passages strategy-invariant(group by section_path)| ✅ PASS | `test_build_section_passages_groups_by_section`(group/concat)+ section_path 由 parse 定 strategy-invariant(R6 發現 2)|
| G4 | controlled-A/B framing 誠實(消 confounding;**但仍 synthetic + lexical-containment proxy 非人手 ground truth**)| ✅ PASS | module docstring + dataclass docstring + `to_keyword_eval_set_payload` metadata note + eval-methodology §10.6 + arch/roadmap amendment + CLI output caveat 多處標明 |
| G5 | pytest+ruff+mypy clean + 0 regression + 無新 vendor/dep + 無 H1(無 ADR)| ✅ PASS | 廣 eval suite 82 passed(含 W54 13)0 regression;ruff clean;mypy 改檔唯 yaml baseline;無新 dep;純 C06 eval extension 無 §3/§4 touch |

**判決:Phase Gate 通過(PASS)**。controlled shared-question A/B 落地 —— shared frozen text-anchored(section_path strategy-invariant)question set + reuse EvalRunner keyword-mode recall + `run_controlled_strategy_comparison`,消除 W53 per-config 問題集 confounding,完成 W51→W52→W53→W54 誠實階梯。

### R5 closeout recheck(§3/§4 touch?)
- **無 architectural touch → 無 ADR**(同 W52):controlled_comparison.py = C06 eval;CLI = script;EvalRunner keyword mode = **reuse 非改**(runner.py 一行未郁)。無 §3 RAG core / §4 app architecture component 改動。無新 vendor/dep(openai/yaml 現成)。確認無未記 ADR 嘅 architectural 改動。

### Retro
- **R6 grep 揭穿「需新 keyword harness」前提(§1.1 + R6 — 本期最大價值)**:W53 summary 講 controlled A/B「需新 keyword harness」,但 R6 grep 揭 `EvalRunner` 早已內建 keyword-mode recall(`runner.py:166-184`)→ W54 只需 reuse(同 W52 reuse strict mode 對稱),**零新 recall 數學**。真正新嘅只係 strategy-invariant text-anchored QA 生成。think-before-coding 避免重寫已有嘅 recall 邏輯。
- **section_path strategy-invariant = 乾淨文字錨點(R6 發現 2)**:`HeadingAwareChunker` 係 `LayoutAwareChunker` subclass 繼承同一 section-walk → 兩 strategy 同 section_path → 按 section group passages 天然 strategy-independent,零新 windowing machinery(Karpathy simplicity vs fixed-char-window)。
- **誠實階梯連續第四期守住(R1)**:W51 coverage proxy → W52 synthetic 非人手 → W53 self-retrievability 非 controlled → W54 **IS controlled**(消 confounding)**但仍** synthetic + lexical-containment proxy。每期明標當期成就 + 殘餘限制,唔 over-claim;真人手 ground-truth recall 留 W55+。
- **零改現有檔 = 零 regression 風險**:W54 純新增(module + test + script),import `_collect_chunks` + EvalRunner 皆 read-only → 82 passed 廣 eval suite 0 regression(對比 W53 改 chunker 需 bit-identical fall-through 保護)。
- **formatter 移位坑(F3)**:ruff format 拆多行 call 令 `# type: ignore` 移到無 error 嘅 closing 行 → arg-type + unused-ignore 雙報。教訓:多行 call 嘅 type:ignore 用 per-arg form(magic trailing comma 鎖展開)。
- **Watch(carry W55+)**:人手標註 ground-truth recall(eval-set-v1 SME — 三期 synthetic 之終極升級);controlled A/B live eval 對真 KB(smoke-deferred);section-anchored 問題嘅 lexical-proxy 寬鬆度喺真 KB 嘅實際表現(live 後評)。

### Carry-overs → W55+(rolling JIT)
- **人手標註 ground-truth recall**(eval-set-v1 SME 標註集 — AUDIT-D ii correctness+context_recall;W52/W53/W54 皆 synthetic 之升級)
- controlled A/B + heading_aware **live eval 對真 KB**(smoke-deferred;judge cred + indexed KB + 原始檔 + 402 繞)+ lexical-proxy 寬鬆度實測
- (前期 carry 不變)per-document scope(決策 1 + AUDIT-E)/ production v1→v2(Track A 決策 4)/ Fork B query-intent gate / presets+config 版本史(決策 5)/ Layer C 視覺內容揀圖(Tier 2 決策 3)/ W16 F1-F4 Track A IT cred / LLM-profiler 願景(Tier 2)

### Blockers / carry-over
- 無 blocker。live 比較 run 對 Azure 屬 smoke-deferred(judge cred + indexed KB + 原始檔 + Free-tier 402 繞;整合由 F4 stub 全測)。

### Commits
- `dec9373` F0 kickoff + `dda0574` F1 QA 生成 + `5eb1baf` F2 harness + `0d2a243` F3-F4 CLI+tests + F4 closeout commit(pending)
