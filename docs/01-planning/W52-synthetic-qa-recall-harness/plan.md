---
phase: W52-synthetic-qa-recall-harness
name: "Synthetic-QA Recall Harness (self-supervised true recall — 決策 7 Option d 更深半邊 / 兩者合一 W52 基建)"
sprint_week: W52
start_date: 2026-06-06
end_date:                     # actual close
status: active
spec_refs:
  - ROADMAP-per-kb-tunable-config.md line 107 (synthetic-QA auto-gen → 「留工程閘」offline,非自助面)+ line 112 (synthetic-QA 真 recall 留更未來)
  - W51 (completeness proxy「涵蓋章節數」誠實標明 proxy 非 recall — 本期補返真 recall 半邊)
  - eval-methodology.md (RAGAs + 30-50 條 ground truth) + architecture.md §6 (eval framework C06)
  - backend/eval/runner.py (EvalRunner strict-mode Recall@5 — 本期 reuse,zero 新 recall 數學)
  - backend/eval/ragas_evaluator.py (make_faithfulness_evaluator + patch_for_gpt5 — judge LLM client pattern reuse)
  - backend/retrieval/hybrid.py (list_documents / list_chunks / fetch_by_chunk_ids — chunk 枚舉 reuse,zero modification)
prior_phase: W51-config-test-completeness-proxy
combined_vision: "兩者合一(synthetic-QA 做 ingestion eval 指標)— W52 = recall 基建;W53 = reindex strategy 比較(rolling JIT,W52 收尾先 kickoff,不預寫)"
---

# Phase W52 — Synthetic-QA Recall Harness(基建)

> **Plan version**:1.0(initial)
> **Owner**:Chris(Tech Lead)
> **Approved by**:Chris(2026-06-06 AskUserQuestion:W52 起點 = **兩者合一**;split 成 W52 synthetic-QA recall 基建 → W53 reindex strategy 比較)

## 1. Scope

收返 **決策 7 Option (d) 嘅「更深半邊」**:W51 加咗「涵蓋章節數」coverage proxy,但**誠實標明咗佢唔係 ground-truth recall**(無標註集)。本期補返**真 recall 半邊** —— 一個 **self-supervised synthetic-QA recall harness**:由 KB 自己嘅 indexed chunks 生成問題(每條問題嘅答案只喺嗰個 source chunk 入面),source chunk_id 就係 ground-truth,跑 retrieval 量「source chunk 有無被檢索返」= 真正嘅 **Recall@K**(自監督,非人手標註)。

呢個係 **offline 工程 harness**(per ROADMAP line 107「synthetic-QA auto-gen → 留**工程閘**」)—— **唔係**自助面 UI panel。亦係**兩者合一**願景嘅 **W52 基建**:W53 會用呢個 recall 指標跨 chunk strategy reindex 比較。

**Recall 語意(誠實 framing)**:self-supervised / synthetic recall —— 比 W51 coverage proxy **更接近真 recall**(實際量 retrieval 命中 source chunk 嘅比率),但**仍非人手驗證 ground truth**(LLM 生成問題 + 單 chunk grounding 有自身偏差)。文案必須標清係 **synthetic recall**,唔可以當人手標註 ground-truth recall over-claim(對齊 W51 R1 誠實紀律)。

**Reuse-first 設計(Karpathy zero-new-math)**:
- **EvalRunner strict-mode**(`runner.py`)現成計 `|retrieved ∩ acceptable| / |acceptable|` —— synthetic QA 格式化成 EvalRunner-compatible eval-set entries(`acceptable_chunk_ids=[source_chunk_id]` + `validated=True`),直接餵 EvalRunner,**零新 recall 數學**。
- **Judge LLM client**:reuse `AsyncAzureOpenAI` + `azure_openai_deployment_llm_judge`(gpt-5.4-mini per 成本政策)+ `patch_for_gpt5`(GPT-5 reasoning param quirk)—— 同 `make_faithfulness_evaluator` 一脈。無 judge cred → graceful None / 空(同 RAGAs fallback)。
- **Chunk 枚舉**:reuse `engine.list_documents` → `list_chunks`(chunk_ids + section_path)→ `fetch_by_chunk_ids`(攞 chunk_text,呢個方法無 select clause 故返全 fields)。**zero modification to C03 retrieval**。

**Out-of-scope(誠實 + Karpathy simplicity)**:
- **人手標註 ground-truth recall / SME 驗證**:本期係自監督 synthetic,唔做人手標註 cascade。
- **answer correctness / context_recall RAGAs metric**:本期只量 retrieval recall(source chunk 有無返),唔生成答案、唔計 4-metric。
- **reindex strategy 比較 / 臨時 index 生命週期**:W53 候選(用本期 recall 指標跨 strategy)。**不預寫 W53 plan**(rolling JIT)。
- **自助面 UI / config-test panel 整合 / frontend**:本期 backend-only(工程閘)→ **無 H7**。
- multi-hop / 難度分層 / 每 chunk 多問題:1 chunk = 1 問題(simplicity)。
- judge LLM 升級:維 gpt-5.4-mini(per memory `feedback_judge_llm_cost_policy`)。

**Sprint week origin**:roadmap 決策 7 Option (d) 更深半邊(synthetic-QA 真 recall);Chris 2026-06-06 揀「兩者合一」→ W52 = recall 基建。

## 2. Key Design Decisions(kickoff lock)

- **Self-supervised recall**:source chunk = ground-truth chunk;recall = retrieval 有無喺 top-K 命中 source chunk。誠實標明 **synthetic / 自監督**,非人手 ground truth。
- **Reuse EvalRunner strict-mode**(零新 recall 數學):synthetic entries `acceptable_chunk_ids=[source]` + `validated=True` + `query_phrasing_source="synthetic_llm_W52"` + `expected_refusal=False`。strict-mode guard(`validated AND acceptable_ids AND not 任何 id startswith "kb-drive_doc-M0"`)—— 真 index chunk_id 唔會撞 placeholder prefix,故 strict 生效。
- **Reuse judge client pattern**:`make_qa_generator(settings)` 建 `AsyncAzureOpenAI` 判 deployment(gpt-5.4-mini)+ `patch_for_gpt5`;無 `azure_openai_api_key` → return None(harness skip,同 faithfulness evaluator)。
- **Deterministic 抽樣**(seed 參數):可重現(W53 跨 strategy run 需穩定);default `sample_size=30`(對齊 eval-methodology「30-50 條 ground truth」)。
- **Driver 寫 synthetic eval-set YAML artifact**:`run_synthetic_recall` 生成 → 寫 `--output` eval-set YAML → `EvalRunner.run(path)` → recall report。YAML artifact 可重用(W53)+ 可審。
- **Backend-only**:無 frontend → **無 H7**。
- **無新 ADR / vendor / dep**:extend C06 eval framework;`openai` / `pyyaml` 現成 dep。synthetic-QA recall = eval methodology extension(§5.1「加 eval/test 唔係 architectural」)→ documented in eval-methodology.md + architecture.md §6 amendment。**R5 closeout recheck**:若實作揭 §3/§4 component touch → STOP+ADR。

## 3. Deliverables

### F0 — Phase kickoff
- **Acceptance criteria**:plan/checklist/progress committed(R1);scope(synthetic 非人手 recall / offline 工程閘 / 兩者合一 W52 基建 / backend-only)+ key design 鎖定;R6 grep 記 progress
- **Owner**:AI

### F1 — Backend:synthetic-QA generator(`backend/eval/synthetic_qa.py`,C06)
- **Spec ref**:reuse `ragas_evaluator.patch_for_gpt5` + judge client pattern;`Citation`/chunk fields
- **Acceptance criteria**:
  - `SyntheticQAPair` dataclass(`question` / `source_chunk_id` / `source_section_path` / `source_chunk_text`)
  - `make_qa_generator(settings) -> Callable[[str], Awaitable[str | None]] | None` —— judge client(gpt-5.4-mini + patch_for_gpt5);無 cred → None;per-call try/except → None(graceful)
  - `async generate_qa(chunks, generate_fn, *, sample_size, seed) -> list[SyntheticQAPair]` —— 確定性抽樣 + 逐 chunk 1 grounded 問題(modest 並發 + None 自降)
  - `to_eval_set_payload(pairs, *, kb_id, seed) -> dict` —— EvalRunner-compatible(`metadata.version` + `queries[]` 含 acceptable_chunk_ids/validated/expected_refusal)
  - mypy --strict clean(我新檔零 error)+ ruff check+format clean
- **Owner**:AI

### F2 — Backend:recall driver + CLI(`backend/eval/synthetic_qa.py`)
- **Spec ref**:reuse `EvalRunner` + `report_to_yaml`;`engine.list_documents`/`list_chunks`/`fetch_by_chunk_ids`
- **Acceptance criteria**:
  - `async run_synthetic_recall(engine, kb_id, *, generate_fn, sample_size, seed, top_k, output_path) -> EvalReport` —— 枚舉 chunks(list_documents→list_chunks→fetch_by_chunk_ids 攞 text)→ generate_qa → to_eval_set_payload → 寫 YAML → `EvalRunner(engine, top_k, kb_id).run(path)` → report
  - 依賴可注入(generate_fn / engine)→ 可 stub 測試
  - 無 judge cred → graceful skip(log + 不 crash)
  - thin CLI `main()`(`python -m eval.synthetic_qa --kb-id ... --sample N --seed S --top-k 5 --output ...`)mirror `eval_set_augmentor.main()` + engine bootstrap mirror `scripts/run_gate1_eval.py`
  - **Live run 對 Azure 屬 smoke-deferred**(需 judge cred + indexed KB + Free-tier semantic 402 繞;同 W15/W17/W18 smoke-deferred 慣例);整合由 F3 stub 全測
- **Owner**:AI

### F3 — Tests(H6 mandatory — backend/eval/)
- **Acceptance criteria**:
  - `backend/tests/test_synthetic_qa.py`:
    - `generate_qa` stub generate_fn → 確定性(seed)+ count = sample_size + None 自降過濾
    - `to_eval_set_payload` → entries acceptable_chunk_ids=[source] / validated=True / expected_refusal=False
    - **整合 round-trip**:build payload → 寫 temp YAML → stub engine(命中部分 source chunks)餵 EvalRunner → recall 正確(e.g. 3 條 synthetic,2 命中 → aggregate_recall_at_5 ≈ 0.667;strict-mode 生效)
    - `make_qa_generator` 無 `azure_openai_api_key` → None(graceful,mirror faithfulness evaluator test)
  - 既有 backend test 0 regression
- **Owner**:AI

### F4 — Doc-sync + closeout
- **Acceptance criteria**:
  - eval-methodology.md 加 synthetic-QA recall 章節(self-supervised 方法 + **誠實標明非人手 ground truth**)+ architecture.md §6 W52 amendment
  - roadmap line 112「synthetic-QA 真 recall 留更未來」→ ✅ W52 shipped(基建;兩者合一 → W53 reindex 比較候選)+ 修訂史 entry
  - session-start §10 W52 row + plan.md status→closed + changelog
  - Phase Gate G1-G4 + retro + carry-overs(W53 reindex candidate)+ checklist tick / 🚧
- **Owner**:AI

## 4. Success Criteria(Phase Gate)

| # | Criterion | Target | Measure | Block closeout? |
|---|---|---|---|---|
| G1 | synthetic-QA generator 生成 grounded QA + EvalRunner-compatible eval-set payload | `to_eval_set_payload` strict-mode 可消費 | pytest | Yes |
| G2 | recall driver 跨 generator→EvalRunner 算出 self-supervised Recall@K(zero 新 recall 數學)| stub round-trip recall 正確 | pytest 整合 test | Yes |
| G3 | recall framing 誠實(synthetic / 自監督,非人手 ground-truth recall)| 文案 / docstring / eval-methodology review | review | Yes |
| G4 | pytest + ruff + mypy clean;0 regression;無新 ADR/vendor/dep | all green | CI commands | Yes |

## 5. Risks(Phase-Specific)

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | over-claim synthetic recall 做人手 ground-truth recall(誤導)| Med | High | 文案/docstring/eval-methodology 標清 **self-supervised synthetic**;承認 LLM 生成問題 + 單 chunk grounding 偏差;非人手驗證 |
| R2 | LLM 生成問題太泛/跨 chunk(source chunk 唔係唯一答案 → recall 失真)| Med | Med | prompt 明確要求「答案只喺呢段、self-contained、specific」;sample 抽查屬後評(同 W49 R5)|
| R3 | chunk 枚舉漏 chunk_text(`list_chunks` 故意唔返 text)| Low(已驗)| Med | 用 `fetch_by_chunk_ids`(無 select → 返全 fields 含 chunk_text);R6 grep 已確認 |
| R4 | live judge cred / Free-tier 402 阻 live run | High | Low | 整合全 stub-test;live run smoke-deferred(慣例);graceful None |
| R5 | judge 成本(每 chunk 1 call × sample_size)| Low | Low | default sample_size=30;維 gpt-5.4-mini;offline 非 hot path |

## 6. Day-by-Day Breakdown(rough)

| Day | Date | Focus | Deliverables |
|---|---|---|---|
| D1 | 2026-06-06 | F0 kickoff + F1 generator + F2 driver/CLI | F0-F2 |
| D2 | 2026-06-06+ | F3 tests + F4 closeout | F3-F4 |

## 7. Plan Changelog

| Date | Change | Reason | Approver |
|---|---|---|---|
| 2026-06-06 | Initial plan | W52 kickoff;Chris AskUserQuestion 揀「兩者合一」→ split W52 synthetic-QA recall 基建 / W53 reindex 比較;synthetic 自監督 recall offline 工程閘;reuse EvalRunner + judge client + chunk 枚舉;無新 ADR/vendor/dep | Chris |

---

**Lifecycle reminder**:plan locked after status=active。重大 deviation 入第 7 節 changelog。**Backend-only — 無 H7**。**Reuse EvalRunner strict-mode**(零新 recall 數學)+ judge client pattern + chunk 枚舉(zero C03 modification)。**synthetic recall ≠ 人手 ground-truth recall** 必須誠實 framing(R1)。**R5 closeout**:若揭 §3/§4 touch → STOP+ADR。
