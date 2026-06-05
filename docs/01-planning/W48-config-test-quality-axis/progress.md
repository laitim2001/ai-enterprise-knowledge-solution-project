# W48 — Config-Test Quality Axis (faithfulness) · Progress

> Daily progress + decisions + commits + 結尾 retro。每 daily commit 對應 Day-N entry(R2)。

---

## Day 1 — 2026-06-05

### Context / kickoff
W47 closed + pushed(`ecd9156`)。用戶揀 W48 = **config-test 加 ingestion 質素軸**。

### R6 grep 驗證(plan kickoff)— Explore agent map 揭架構張力
- config-test(ADR-0040)= **query-pipeline-only**:`DraftRetrievalConfig` 12 個 runtime 旋鈕,**零** ingestion 旋鈕;`config_test.py` 注入 `PerQueryOverrides` 試跑同一 query pipeline。
- **config-test 架構上試唔到 ingestion config**(`chunk_strategy`/`chunker_max_images_per_chunk` ingest-time,要 reindex)→ option label「ingestion 質素軸」**自相矛盾**。
- RAGAs faithfulness reference-free 現成(`ragas_evaluator.py:149`,無 ground truth);config-test 每 run 後 `resp.answer` + `resp.retrieved_chunks` 齊 → 質素軸技術上乾淨。

### 決策
- **AskUserQuestion(scope)**:Chris 揀 **Option A** = faithfulness 質素軸加入 **runtime** config-test(收 AUDIT-D / ADR-0040 雙軸);ingestion-config 質素(reindex→eval)out-of-scope 留未來。
- **Key design lock**(plan §2):每 config 只算一次 faithfulness(last-run,非 N-run band,cost-conscious)+ graceful degradation(error→None 唔 fail)+ `asyncio.to_thread`(sync evaluator off event loop)+ `eval_faithfulness: bool=True` flag + judge 維 gpt-5.4-mini + **無新 ADR**(fulfill ADR-0040 雙軸)。

### Done
- F0 R1 phase 三件套建立(plan/checklist/progress);Phase Gate G1-G5 定義

### Next
- F1 backend:`ConfigTestRequest.eval_faithfulness` + `ConfigRunSummary.faithfulness` + `_run_n` 接 RAGAs evaluator(to_thread + try/except graceful)

### Commits
- _(pending — F0 kickoff)_

### Blockers / carry-over
- 無 blocker。判 LLM cost / graceful-degradation / event-loop 風險已喺 plan §5 + §2 design lock 留底。
