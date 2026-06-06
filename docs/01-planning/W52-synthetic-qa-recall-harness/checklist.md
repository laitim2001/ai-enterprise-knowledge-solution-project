# W52 — Synthetic-QA Recall Harness · Checklist

> Atomic items per deliverable。不可刪未勾項(只 `[x]` 或標 🚧 + reason)。
> **Backend-only = 無 H7**;**reuse EvalRunner strict-mode / judge client / chunk 枚舉**(零新 recall 數學、零 C03 modification);**synthetic 非人手 ground-truth recall** 誠實 framing(R1)。

## F0 — Phase kickoff
- [x] F0.1 plan/checklist/progress committed(R1);scope(synthetic 自監督 recall / offline 工程閘 / 兩者合一 W52 基建 / backend-only 無 H7)+ key design 鎖定;R6 grep 記 progress

## F1 — Backend:synthetic-QA generator
- [ ] F1.1 `SyntheticQAPair` dataclass(question / source_chunk_id / source_section_path / source_chunk_text)
- [ ] F1.2 `make_qa_generator(settings) -> Callable | None`(judge client gpt-5.4-mini + patch_for_gpt5;無 cred → None;per-call try/except → None)
- [ ] F1.3 `async generate_qa(chunks, generate_fn, *, sample_size, seed)`(確定性抽樣 + 逐 chunk 1 grounded 問題 + None 自降 + modest 並發)
- [ ] F1.4 `to_eval_set_payload(pairs, *, kb_id, seed) -> dict`(EvalRunner-compatible:metadata.version + queries[] acceptable_chunk_ids/validated/expected_refusal)
- [ ] F1.5 mypy --strict clean(新檔零 error;exit 1 純跨模組 pre-existing)+ ruff check+format clean

## F2 — Backend:recall driver + CLI
- [ ] F2.1 `async run_synthetic_recall(engine, kb_id, *, generate_fn, sample_size, seed, top_k, output_path) -> EvalReport`(枚舉 chunks → generate_qa → to_eval_set_payload → 寫 YAML → EvalRunner.run → report)
- [ ] F2.2 依賴可注入(generate_fn / engine)+ 無 judge cred → graceful skip(log,不 crash)
- [ ] F2.3 thin CLI `main()`(`python -m eval.synthetic_qa --kb-id ... --sample N --seed S --top-k 5 --output ...`)+ engine bootstrap(mirror run_gate1_eval.py)
- [ ] F2.4 mypy --strict + ruff clean(同 F1.5)

## F3 — Tests(H6 mandatory)
- [ ] F3.1 `generate_qa` stub generate_fn → 確定性(seed)+ count=sample_size + None 自降過濾
- [ ] F3.2 `to_eval_set_payload` → entries acceptable_chunk_ids=[source] / validated=True / expected_refusal=False
- [ ] F3.3 整合 round-trip:payload → temp YAML → stub engine(部分命中)→ EvalRunner → recall 正確(strict-mode 生效)
- [ ] F3.4 `make_qa_generator` 無 azure_openai_api_key → None(graceful)
- [ ] F3.5 既有 backend test 0 regression(`pytest`)

## F4 — Doc-sync + closeout
- [ ] F4.1 eval-methodology.md 加 synthetic-QA recall 章節(self-supervised + **標明非人手 ground truth**)+ architecture.md §6 W52 amendment
- [ ] F4.2 roadmap line 112「synthetic-QA 真 recall 留更未來」→ ✅ W52 shipped(基建;W53 reindex 比較候選)+ 修訂史 entry
- [ ] F4.3 session-start §10 W52 closed row + W53 rolling JIT(local-only,gitignored)+ plan.md status→closed + changelog
- [ ] F4.4 Phase Gate G1-G4 = PASS + retro + carry-overs(W53 reindex candidate)+ checklist 全 tick(或 🚧 + reason)+ R5 closeout recheck(§3/§4 touch?)
