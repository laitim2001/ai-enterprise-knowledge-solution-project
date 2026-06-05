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

### F1 backend(同日)
- **R3 deviation**(plan §7 已記):plan 原寫 reuse `make_ragas_evaluator` 不改,但佢算全 4-metric → 改加 **additive** `make_faithfulness_evaluator(settings)`(eval/ragas_evaluator.py;faithfulness-only,復用 `patch_for_gpt5`+`Faithfulness`+threadpool bridge;現有 `make_ragas_evaluator` 0 改動 = 0 regression)。返 None 若無 judge credential;per-call try/except → None graceful。
- `schemas/config_test.py`:`ConfigTestRequest.eval_faithfulness: bool=True` + `ConfigRunSummary.faithfulness: float|None=None`
- `routes/config_test.py`:`config_test()` build evaluator 一次(`make_faithfulness_evaluator` if eval_faithfulness else None;draft+saved 共用)→ `_run_n` capture last-run answer + `[c.chunk_text for c in resp.retrieved_chunks]` → `await asyncio.to_thread(faithfulness_fn, query, answer, contexts)`(sync evaluator off event loop)→ summary.faithfulness
- 驗:ruff check+format clean;mypy --strict 我新 helper + config_test.py 零 error(6 pre-existing error 喺舊 function `patch_for_gpt5`/`make_ragas_evaluator`/`_ascore_*`/`_sync_eval` 與改動無關)

### F2 frontend(同日,H7 design-first)
- mockup `ekp-page-kb.jsx` `KbTestResultCard` 加 `faith` prop + **全寬 headline cell**「忠實度(faithfulness · 反幻覺 · 0–1)」置 grid 頂(質素軸 headline;success 色 / null「—未評」)+ 2 call site faith="0.97"/"0.94"
- `config-test.ts`:types 加 `faithfulness` + `eval_faithfulness`
- `page.tsx` `ConfigResultCard`:加 faithfulness headline cell `.toFixed(2)` 100% match 更新後 mockup

### F3 tests(同日)
- backend `test_config_test_route.py`:autouse `_no_judge` fixture(保護既有 4 test 唔觸真 Azure judge — eval_faithfulness 預設 true + 真 settings)+ 3 新 test(computed 0.95 + 核 answer/contexts / disabled None / graceful None A/B);`test_eval_ragas.py` +1(helper no-key→None H6)
- frontend `kb-settings-tuning.test.tsx`:FAKE_RESULT draft/saved 補 faithfulness + 試跑 test assert 忠實度 ≥2 + 0.97 + 0.94
- 驗:backend **pytest 14 passed**(config_test 7 + eval_ragas 7)0 regression;frontend **vitest 6 passed**(kb-settings)+ tsc clean + lint clean + `[oklch`=0

### Next
- F4 doc-sync(architecture.md §5.5.5 + roadmap 決策6/AUDIT-D + session-start)→ closeout

### Commits
- `e4fcffd` F0 kickoff;_(pending — F1-F3 code+tests)_

### Blockers / carry-over
- 無 blocker。判 LLM cost / graceful-degradation / event-loop 風險已喺 plan §5 + §2 design lock 落地驗證(graceful test pass)。
