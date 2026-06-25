# W96 checklist — 答案完整度 eval gate

> 對應 `plan.md` §2 deliverables。每完成一項 tick + 喺 `progress.md` 記 Day-N entry(§10 R2)。

## F1 — Pure metric core(零 production 改動)
- [x] `backend/eval/completeness_coverage.py`:`NuggetJudgement` / `CompletenessMetrics` / `compute_metrics` / `aggregate` / `report_to_dict`(mirror `image_recall.py` 風格,frozen slots)
- [x] `backend/tests/test_completeness_coverage.py`:full coverage / partial drop / 全掉 / 空 nugget 邊界 / aggregate 混 scored+errored / report_to_dict 形狀
- [x] pytest 綠
- [x] ruff + mypy clean

## F2 — LLM judge 層
- [x] query-conditioned nugget 抽取(query Q + 檢索 context → atomic 事實/步驟 list)用 `gpt-5.4-mini`
- [x] answer presence 判定(每 nugget present bool)
- [x] 無 credential graceful None(mirror `make_qa_keyword_generator`)
- [x] 容錯 JSON parse(`_parse_nuggets`/`_parse_presence`:fence / text-align / dropped=absent / positional fallback)+ 10 測試綠 + ruff + mypy(my file)

## F3 — Live driver
- [x] `scripts/run_completeness.py`:per query → `/query` → answer + 檢索 context → 抽 nugget → 判 presence → 餵 F1 → 出 report yaml
- [x] denominator = 檢索 context(`retrieved_chunks[].chunk_text` = `result.chunks` reranked,非 answer citation)
- [x] 沿用既有 eval-set query list(`docs/eval-set-completeness-w96.yaml`,GT-free 無新人手 GT)
- [x] 端到端跑 KB `drive-user-manual-kb-20260618` 出 report

## F4 — Baseline 驗證 + construct validity
- [x] pre-flight health check(§10.3 5b):backend 全棧 up + healthy,無需重啟
- [x] baseline run,3 run mean = 0.770 / 0.849 / 0.792
- [~] **construct validity = PARTIAL**:in-run 有區分力(0.18 vs 1.00)+ 正確隔離 synthesizer 層,但**per-answer 不可靠**(C003 0.18↔0.88 / C005 0.25↔1.00);GL C001 案**冇**穩定重現(RMS/RSP 段不在 reranked context = 偏甲類)→ 把尺只可 aggregate 用,未可逐答案診斷
- [x] run-level 多 run 睇 band(3 run;實證 per-answer 不可靠 caveat 成立)

## F5 — Doc-sync
- [x] `docs/eval-methodology.md` §2.5 Answer Completeness(formula + pipeline + 可靠度紀律 MANDATORY caveat)
- [x] memory 新建 `project_completeness_eval_gate_w96` + MEMORY.md 指標
- [x] `DEFERRED_REGISTER.md` DD-15(gate hardening 前置)+ DD-16(緩解 phase blocked on DD-15)
- [x] Phase Gate G-W96 verdict(PARTIAL)寫入 progress.md

## DD-15 gate hardening(F6-F8)
- [x] F6 `completeness_coverage.py` 加 `mean_std` + paired aggregation + 6 測試(14 綠)
- [x] F6 `completeness_judge.py` 重構 `_build_client` + `make_nugget_extractor`/`make_presence_judge`(行為不變,10 綠)
- [x] F7 `scripts/run_completeness_ab.py`(build-nuggets + 固定 nugget K-run paired A/B)+ console cp1252 crash fix
- [x] F8 固定 nugget 建好 + paired A/B 跑完(`gpt-5.4-mini` vs `gpt-5.5`,K=3)
- [~] **G-W96-H = 進步但未完全解決**:固定 nugget 去掉 nugget variance,但答案 variance 主導(K=3 未壓住,std 0.16-0.41)→ gate 解析度 ~±0.15(解大 delta、解唔到 4pp 細 delta);乾淨副信號 = gpt-5.5 答案更穩定
- [x] F8 doc-sync(eval-methodology §2.5 paired + 噪聲底 + DEFERRED DD-15 更新 + memory)
- [ ] **殘餘**:fixed-answer 模式(temperature=0 直呼 synthesizer 去掉答案 variance)— 列 DD-15 殘餘 / 細效果量度先做;大 delta 唔需要
