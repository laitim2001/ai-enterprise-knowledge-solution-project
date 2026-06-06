# W52 — Synthetic-QA Recall Harness · Progress

> Daily progress + decisions + commits + 結尾 retro。每 daily commit 對應 Day-N entry(R2)。

---

## Day 1 — 2026-06-06

### Context / kickoff
W51 closed + pushed(`037da22`,completeness proxy「涵蓋章節數」誠實標明非 recall)。決策 7 三期(W49 band / W50 length-bias caveat / W51 coverage proxy)全收。用戶 pick W52 起點 = **兩者合一(synthetic-QA 做 ingestion eval 指標)**。

### 決策
- **AskUserQuestion(W52 起點)**:Chris 揀 **兩者合一** → split 成 **W52 = synthetic-QA recall 基建** → **W53 = reindex strategy 比較**(rolling JIT,W52 收尾先 kickoff,不預寫)。
- **Key design lock**(plan §2):self-supervised synthetic recall(source chunk = ground-truth)→ **reuse EvalRunner strict-mode**(零新 recall 數學)+ judge client pattern(gpt-5.4-mini + patch_for_gpt5,無 cred → None graceful)+ chunk 枚舉(list_documents→list_chunks→fetch_by_chunk_ids,zero C03 modification)。**誠實 framing**:synthetic 非人手 ground-truth recall(R1)。offline 工程閘 → backend-only → **無 H7**。無新 ADR/vendor/dep。

### R6 grep 驗證(plan kickoff)
- `EvalRunner` strict-mode(`runner.py:166-173`)現成:`validated AND acceptable_ids AND not startswith("kb-drive_doc-M0")` → `|retrieved ∩ acceptable| / |acceptable|`。synthetic entries `acceptable_chunk_ids=[source]` + `validated=True` + 真 index chunk_id(唔撞 placeholder prefix)→ strict 生效。
- `make_faithfulness_evaluator` + `patch_for_gpt5`(`ragas_evaluator.py:201/41`)現成 judge client pattern → QA generator 沿用,零新 client 架構。
- chunk 枚舉:`engine.list_documents` + `list_chunks`(返 chunk_id+section_path,**故意唔返 chunk_text**)+ `fetch_by_chunk_ids`(**無 select clause → 返全 fields 含 chunk_text**,hybrid.py:153/426/500)→ list→sample→fetch 攞 text,zero C03 modification。
- **無 plan-text contamination**:plan 引用 function/field/line grep 對齊現 code(R6 recursive scope 過)。

### Done(F0)
- F0 R1 phase 三件套建立(plan/checklist/progress);Phase Gate G1-G4 定義

### F1 backend generator(同日)
- 新檔 `backend/eval/synthetic_qa.py`(C06):`SyntheticQAPair` dataclass;`make_qa_generator(settings)`(judge `AsyncAzureOpenAI` + `patch_for_gpt5`,gpt-5.4-mini;無 cred → None;per-call try/except → None;`max_tokens=512` → patch floor 4096 保 reasoning 留 completion budget);`async generate_qa`(確定性 seeded 抽樣 + sort by chunk_id 穩定 + modest 並發 Semaphore(4) + None/empty 自降);`to_eval_set_payload`(EvalRunner-compatible strict-mode entries;誠實 metadata.note 標明非人手 ground truth)
- 驗:ruff check + format clean

### F2 backend driver + CLI(同日)
- `run_synthetic_recall(engine, kb_id, ...)` driver(`_collect_chunks` 枚舉 → generate_qa → to_eval_set_payload → 寫 YAML artifact → `EvalRunner.run`,zero 新 recall 數學)+ `SyntheticRecallError`(空 KB / 全 judge fail)
- **R3 deviation ①**(plan §7):engine 未 expose `fetch_by_chunk_ids` → 加 3 行 `RetrievalEngine.fetch_by_chunk_ids` passthrough(mirror `list_chunks` delegate;非 architectural additive delegate)。修正 plan「zero C03 modification」
- **R3 deviation ②**(plan §7):live CLI 放 `scripts/run_synthetic_recall.py`(truststore + engine bootstrap mirror run_gate1_eval.py);模組 bootstrap-free
- 驗:ruff clean;mypy --strict 我兩源檔唯一 finding = yaml import-untyped(同 runner.py:22 baseline)+ dict type-arg(同 retrieval_engine line 346/354 風格)→ 無新 logic error

### F3 tests(同日,H6)
- `backend/tests/test_synthetic_qa.py` 5 test:generate_qa 確定性+None自降;to_eval_set_payload strict shape;run_synthetic_recall 整合 round-trip(stub engine 2/3 命中 → recall=2/3 strict-mode 生效,坐實 zero-new-recall-math reuse);make_qa_generator 無 cred → None
- 驗:eval suite **65 passed**(synthetic_qa 5 + eval_runner 11 + eval_ragas/ragas_runner/endpoints/augmentor)+ test_retrieval **31 passed**(engine passthrough regression)= **0 regression**

### F4 doc-sync(同日)
- eval-methodology.md NEW **§10.6**(Synthetic-QA Self-Supervised Recall 非人手 Ground Truth)—— 落 policy-level honesty section;列 3 個 known bias(生成偏差 lexical 樂觀 / 單 chunk grounding 唔覆蓋 multi-chunk / 無人手驗證)+ disclosure rule(label = synthetic recall,用途 = 相對比較非絕對 verdict)
- architecture.md §5.5.5 NEW **W52 amendment**(更新 W51 forward-pointer;清楚標明 W52 = offline harness **非 config-test panel**;reuse EvalRunner strict-mode + judge client + chunk 枚舉 + NEW passthrough;指向 eval-methodology §10.6)
- roadmap:line 112 (d) 更深半邊 → ✅ W52 shipped;修訂史加 2026-06-06 W52 entry
- session-start §10 W52 closed row + W53+ rolling JIT row(local-only,不入 git)
- plan.md status→closed + changelog(含 2 R3 deviation)

### Phase Gate G1-G4 — **PASS**

| # | Criterion | Verdict | Evidence |
|---|---|---|---|
| G1 | synthetic-QA generator 生成 grounded QA + EvalRunner-compatible payload | ✅ PASS | `test_to_eval_set_payload_strict_mode_shape`:acceptable_chunk_ids=[source]/validated/expected_refusal;`generate_qa` 確定性 + None 自降 test 過 |
| G2 | recall driver 跨 generator→EvalRunner 算 self-supervised Recall@K(零新 recall 數學)| ✅ PASS | `test_run_synthetic_recall_round_trip`:stub engine 2/3 命中 → aggregate Recall@5=0.667 + per_query mode=strict(證 synthetic entries 真係行 EvalRunner strict path)|
| G3 | recall framing 誠實(synthetic / 自監督,非人手 ground-truth recall)| ✅ PASS | docstring + metadata.note + eval-methodology §10.6 bias disclosure + roadmap/arch amendment 三處標明「非人手 ground truth」 |
| G4 | pytest+ruff+mypy clean;0 regression;無新 ADR/vendor/dep | ✅ PASS | eval suite 65 passed + test_retrieval 31(engine passthrough)= 0 regression;ruff clean;mypy 我兩源檔唯一 finding = yaml import-untyped(codebase baseline)+ dict type-arg(現有風格)→ 無新 logic error;無新 dep/ADR |

**判決:Phase Gate 通過(PASS)**。決策 7 Option (d) 更深半邊 done —— synthetic-QA self-supervised recall 基建落地(offline 工程閘),補返 W51 留低嘅真 recall 半邊。兩者合一 W52 基建完成 → W53 reindex strategy 比較有 recall 指標可用。

### R5 closeout recheck(§3/§4 touch?)
- **無 architectural touch**:synthetic_qa.py = C06 eval methodology extension(§5.1「加 eval/test 唔係 architectural」);唯一 existing-file 改動 = `RetrievalEngine.fetch_by_chunk_ids` **additive passthrough delegate**(mirror 現有 list_chunks/list_documents,無 interface/vendor/storage/schema 改)→ 非 H1。**無新 ADR**(eval methodology,documented in eval-methodology.md §10.6)。

### Retro
- **誠實 framing 守得住(R1)— 比 W51 更進一步**:W51 standard 係「proxy 非 recall」;W52 真係量 recall,但仍標明 **self-supervised synthetic 非人手 ground-truth**(LLM 生成問題偏差 + 單 chunk grounding)。三處(docstring / eval-methodology §10.6 / arch+roadmap amendment)標清「用途 = 相對比較非絕對 verdict」,唔 over-claim。
- **Karpathy zero-new-math reuse**:R6 grep 早發現 `EvalRunner` strict-mode 現成 → synthetic 只需 format 成 `acceptable_chunk_ids=[source]`+`validated=True` entries 餵落去,**零新 recall 數學**;judge client(`patch_for_gpt5`)+ chunk 枚舉全 reuse。整個 backend 新邏輯極窄(1 generator module + 1 passthrough + 1 driver)。
- **think-before-coding 揭 passthrough 缺口(§1.1 + R6)**:plan 寫「zero C03 modification」,F1 摸 code 揭 engine 未 expose `fetch_by_chunk_ids`(只喺 _searcher)→ upfront surface + 加 additive delegate（避免 C06 reach into C03 private）+ R3 changelog,而非 post-hoc 補。
- **offline 工程閘 vs config-test panel 分清**:W49-W51 喺 config-test panel(ADR-0040),W52 揭 synthetic recall 屬 offline(ROADMAP line 107 工程閘 framing)→ 落 scripts/ + eval/ 而非 panel,避免錯放 UI surface。
- **Watch(carry W53+)**:W53 reindex strategy 比較(用此 recall 指標跨 chunk_strategy);synthetic 問題質素抽查(R2 敏感度後評);live judge run 對真 KB(smoke-deferred,需 cred+402 繞)。

### Carry-overs → W53+(rolling JIT)
- **W53 = reindex strategy 比較**(用 W52 synthetic recall 跨 chunk_strategy reindex→eval — 兩者合一下半截,Chris 已揀方向)
- synthetic recall **live run 對真 KB**(smoke-deferred;judge cred + indexed KB + Free-tier 402 繞)+ 生成問題質素抽查(R2)
- (前期 carry 不變)per-document scope(決策 1 + AUDIT-E)/ AUDIT-D (ii) correctness+context_recall(需人手標註集)/ production v1→v2(Track A 決策 4)/ presets+config 版本史(決策 5)/ Layer C 視覺內容揀圖(Tier 2 決策 3)/ heading_aware footgun

### Blockers / carry-over
- 無 blocker。live judge run 對 Azure 屬 smoke-deferred(judge cred + indexed KB + Free-tier 402 繞;整合由 F3 stub 全測)。

### Commits
- `a791cdb` F0 kickoff + `97acd8b` F1-F3 code+tests + F4 closeout commit(pending)
