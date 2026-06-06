# W52 — Synthetic-QA Recall Harness · Checklist

> Atomic items per deliverable。不可刪未勾項(只 `[x]` 或標 🚧 + reason)。
> **Backend-only = 無 H7**;**reuse EvalRunner strict-mode / judge client / chunk 枚舉**(零新 recall 數學、零 C03 modification);**synthetic 非人手 ground-truth recall** 誠實 framing(R1)。

## F0 — Phase kickoff
- [x] F0.1 plan/checklist/progress committed(R1);scope(synthetic 自監督 recall / offline 工程閘 / 兩者合一 W52 基建 / backend-only 無 H7)+ key design 鎖定;R6 grep 記 progress

## F1 — Backend:synthetic-QA generator
- [x] F1.1 `SyntheticQAPair` dataclass(question / source_chunk_id / source_section_path / source_chunk_text)
- [x] F1.2 `make_qa_generator(settings) -> Callable | None`(judge client gpt-5.4-mini + patch_for_gpt5;無 cred → None;per-call try/except → None)
- [x] F1.3 `async generate_qa(chunks, generate_fn, *, sample_size, seed)`(確定性抽樣 + 逐 chunk 1 grounded 問題 + None 自降 + modest 並發)
- [x] F1.4 `to_eval_set_payload(pairs, *, kb_id, seed) -> dict`(EvalRunner-compatible:metadata.version + queries[] acceptable_chunk_ids/validated/expected_refusal)
- [x] F1.5 ruff check+format clean;mypy --strict 我兩源檔唯一 finding = `yaml import-untyped`(同 runner.py:22/ragas_runner.py:41 codebase baseline,env 缺 types-PyYAML)+ retrieval_engine `dict` type-arg(同現有 line 346/354 bare-dict 風格 §1.3)→ 無新 logic error,exit 1 純跨模組 pre-existing

## F2 — Backend:recall driver + CLI
- [x] F2.1 `async run_synthetic_recall(engine, kb_id, *, generate_fn, sample_size, seed, top_k, output_path) -> EvalReport`(枚舉 chunks → generate_qa → to_eval_set_payload → 寫 YAML → EvalRunner.run → report)
- [x] F2.2 依賴可注入(generate_fn / engine)+ 無 judge cred → make_qa_generator None / SyntheticRecallError graceful;chunk 枚舉用 `engine.fetch_by_chunk_ids` passthrough(R3 deviation,見 plan §7)
- [x] F2.3 thin CLI:**改放 `scripts/run_synthetic_recall.py`**(非 `python -m eval.synthetic_qa`)—— 因 live bootstrap 需 truststore + engine,mirror run_gate1_eval.py;模組保持 bootstrap-free 利 stub 測試(R3 deviation,見 plan §7)
- [x] F2.4 mypy --strict + ruff clean(同 F1.5)

## F3 — Tests(H6 mandatory)
- [x] F3.1 `generate_qa` stub generate_fn → 確定性(seed)+ count=sample_size + None 自降過濾(`test_generate_qa_deterministic_seeded_sample` + `_skips_empty_text_and_drops_none`)
- [x] F3.2 `to_eval_set_payload` → entries acceptable_chunk_ids=[source] / validated=True / expected_refusal=False(`test_to_eval_set_payload_strict_mode_shape`)
- [x] F3.3 整合 round-trip:payload → temp YAML → stub engine(2/3 命中)→ EvalRunner → recall=2/3(strict-mode 生效)(`test_run_synthetic_recall_round_trip`)
- [x] F3.4 `make_qa_generator` 無 azure_openai_api_key → None(graceful)(`test_make_qa_generator_none_without_credential`)
- [x] F3.5 既有 backend test 0 regression:eval suite **65 passed**(synthetic_qa 5 + eval_runner 11 + eval_ragas/ragas_runner/endpoints/augmentor)+ test_retrieval 31 passed(engine passthrough regression)

## F4 — Doc-sync + closeout
- [x] F4.1 eval-methodology.md NEW **§10.6**(synthetic-QA self-supervised recall + **標明非人手 ground truth** + 3 bias disclosure)+ architecture.md **§5.5.5 W52 amendment**(非 §6 — §6 係 Sprint Plan;amendment 落 config-test arc block,標明 W52 = offline harness 非 panel)
- [x] F4.2 roadmap line 112 (d) 更深半邊 → ✅ W52 shipped(基建;W53 reindex 比較候選)+ 修訂史 2026-06-06 entry
- [x] F4.3 session-start §10 W52 closed row + W53+ rolling JIT row(local-only,不入 git)+ plan.md status→closed + changelog(含 2 R3 deviation)
- [x] F4.4 Phase Gate G1-G4 = **PASS** + retro + carry-overs(W53 reindex candidate)+ checklist 全 tick(無 🚧)+ R5 closeout recheck(無 §3/§4 architectural touch;passthrough = additive delegate)
