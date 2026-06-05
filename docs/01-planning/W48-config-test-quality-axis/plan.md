---
phase: W48-config-test-quality-axis
name: "Config-Test Reference-Free Faithfulness Quality Axis (ADR-0040 dual-axis fulfillment)"
sprint_week: W48
start_date: 2026-06-05
end_date: 2026-06-08          # planned, may slip with changelog log
status: active
spec_refs:
  - ADR-0040 (per-KB config-scope + config-test harness 雙軸:presentation + quality)
  - architecture.md §5.5.5 (KB Detail Settings config-test 試跑 panel)
  - backend/api/routes/config_test.py + backend/api/schemas/config_test.py (W43 harness)
  - backend/eval/ragas_evaluator.py (reference-free faithfulness — reuse, NOT modify)
  - roadmap ROADMAP-per-kb-tunable-config.md §3「NEW 並行」+ 決策 6 + AUDIT-D
prior_phase: W47-reindex-live-verification
---

# Phase W48 — Config-Test Reference-Free Faithfulness Quality Axis

> **Plan version**:1.0(initial)
> **Owner**:Chris(Tech Lead)
> **Approved by**:Chris(2026-06-05 AskUserQuestion:W48 方向 = config-test 加 ingestion 質素軸 → scope **Option A**:faithfulness 質素軸加入 runtime config-test)

## 1. Scope

收 **AUDIT-D / ADR-0040 雙軸 gap**:W43 自助 config-test 試跑 harness 只有 **presentation 軸**(citation/image/latency counters),**缺 ADR-0040 自己定義咗嘅 quality 軸**。本期加 **reference-free RAGAs faithfulness**(反幻覺半邊)到 config-test,令用戶試跑時除咗睇「答幾多引用 / 幾多圖」仲睇到「答案有幾貼retrieved chunks(冇幻覺)」。

**Scope kickoff R6 grep 已驗**(Explore agent map):
- config-test 係 **query-pipeline-only**:`DraftRetrievalConfig` = 12 個 runtime 旋鈕(retrieval/citation/image),**零個** ingestion 旋鈕。`config_test.py` 注入 `PerQueryOverrides` 試跑同一條 query pipeline。
- **架構上 config-test 試唔到 ingestion config**(`chunk_strategy` / `chunker_max_images_per_chunk` ingest-time 消耗,要 reindex)→ Chris 拍板 **Option A**:ingestion-config 質素留未來 reindex→eval,本期只做 runtime config-test 質素軸。
- RAGAs **faithfulness reference-free**(`ragas_evaluator.py:149`,無需 ground truth)現成;config-test 每 run 後 `resp.answer` + `resp.retrieved_chunks`(chunk_text)齊 → 質素軸技術上乾淨,**無新 vendor / 無新 ADR**(fulfill ADR-0040 雙軸)。

**Out-of-scope**:ingestion-config 質素(reindex→eval,未來期)、judge LLM 升級(維 `gpt-5.4-mini` per memory `feedback_judge_llm_cost_policy`)、faithfulness 以外 RAGAs metric(answer_relevancy / correctness 需 ground truth or 更貴,本期淨 faithfulness)、frontend faithfulness on/off toggle(成本由「每 config 只算一次」控制,唔加 UI toggle keep H7 surface 最細)。

**Sprint week origin**:roadmap §3「NEW 並行」+ 決策 6 + AUDIT-D(2026-06-05 Chris pick;W47 closeout 後)

## 2. Key Design Decisions(kickoff lock)

- **每個 config 只算一次 faithfulness**(用 last-run `answer` + `retrieved_chunks`,鏡像現有 `per_citation` last-run capture)—— **非** N-run band。理由:RAGAs faithfulness judge 內部多次 LLM 調用,N runs × A/B 會極慢/貴;單次 = 1 judge eval / config(A/B 2 次),interactive UX + cost-conscious(memory judge cost policy)。Trade-off:無 run-to-run 質素 band(presentation band 已示穩定度)。
- **Graceful degradation**:RAGAs evaluator 不可用 / judge 出錯 → `faithfulness = None`(config-test 照返 presentation 軸,唔 fail)。
- **Sync evaluator off event loop**:`make_ragas_evaluator` 返 sync `_sync_eval` → 用 `asyncio.to_thread` 包,唔阻 async pipeline。
- **`eval_faithfulness: bool = True`** request flag:API-level 控制 + 測試 off-path(frontend 預設 true / 省略)。
- **Judge LLM 不變**:reuse `settings.azure_openai_deployment_llm_judge`(gpt-5.4-mini),不升級。
- **無新 ADR**:fulfill ADR-0040 已定義雙軸(extend 現有 §4 component,非新架構/vendor/storage)。

## 3. Deliverables

### F0 — Phase kickoff
- **Acceptance criteria**:plan/checklist/progress 三件套 committed(R1);scope Option A + key design 鎖定
- **Owner**:AI

### F1 — Backend:faithfulness 質素軸接入 config-test
- **Spec ref**:ADR-0040;`config_test.py` + `schemas/config_test.py`;`eval/ragas_evaluator.py`(reuse)
- **Acceptance criteria**:
  - `ConfigTestRequest` 加 `eval_faithfulness: bool = True`
  - `ConfigRunSummary` 加 `faithfulness: float | None`(config-level,單次算)
  - `_run_n`(或 caller)capture last-run `answer` + `[c.chunk_text for c in resp.retrieved_chunks]` → build `RagasQuerySample` → `asyncio.to_thread(ragas_evaluator, sample)` → 取 `faithfulness` 入 summary
  - evaluator 構造一次 reuse(draft + saved 共用);error / unavailable → `None`(try/except,log warning,唔 fail config-test)
  - `eval_faithfulness=False` → 唔調 judge,`faithfulness=None`(presentation-only fast path)
  - judge LLM 維 gpt-5.4-mini(reuse settings,不改)
  - mypy --strict clean + ruff clean
- **Owner**:AI

### F2 — Frontend:faithfulness 渲染(H7 design-first per ADR-0024)
- **Spec ref**:§5.5.5;mockup `ekp-page-kb.jsx` config-test 試跑 card(`KbTestResultCard`)
- **Acceptance criteria**:
  - mockup `ekp-page-kb.jsx` 試跑 result card 加 faithfulness 質素軸 metric(design-first 先改 mockup)
  - `frontend/lib/api/config-test.ts`:`ConfigRunSummary` 加 `faithfulness: number | null`;`ConfigTestRequest` 加 `eval_faithfulness?: boolean`
  - `ConfigResultCard`(`page.tsx`)render faithfulness(A/B 兩卡;null → 「—」/「未評」)100% match 更新後 mockup(H7 fidelity)
  - tsc + lint clean + `[oklch`=0 preserved
- **Owner**:AI

### F3 — Tests
- **Spec ref**:§5.6 H6(config_test.py 非強制 list 但鼓勵;reuse eval module 不改故不需新 eval test)
- **Acceptance criteria**:
  - backend:config-test faithfulness 計算(mock ragas evaluator → summary.faithfulness 有值)+ `eval_faithfulness=False` → None + evaluator error → None graceful(既有 config_test test 0 regression)
  - frontend:vitest config-test panel render faithfulness(有值 + null「—」)
  - 既有 `kb-settings-tuning` / config-test 相關 test 0 regression
- **Owner**:AI

### F4 — Doc-sync + closeout
- **Acceptance criteria**:
  - architecture.md §5.5.5 config-test note 加 faithfulness 質素軸(ADR-0040 雙軸 fulfilled)
  - roadmap §3「NEW 並行」+ 決策 6 + AUDIT-D → ✅ done(質素軸已交付)
  - session-start §10 W48 row
  - Phase Gate G1-G5 + retro + checklist tick / 🚧
- **Owner**:AI

## 4. Success Criteria(Phase Gate)

| # | Criterion | Target | Measure | Block closeout? |
|---|---|---|---|---|
| G1 | config-test 返 faithfulness 質素軸 | float on summary(A/B 各一)| pytest + manual | Yes |
| G2 | graceful degradation | evaluator error/off → None,config-test 唔 fail | pytest | Yes |
| G3 | frontend render faithfulness 100% match mockup | H7 fidelity(有值 + null)| mockup 對齊 + vitest | Yes |
| G4 | pytest + ruff + mypy + frontend tsc/lint/build clean | all green | CI commands | Yes |
| G5 | judge LLM 維 gpt-5.4-mini + 無新 ADR/vendor | cost policy + ADR-0040 fulfill | review | Yes |

## 5. Risks(Phase-Specific)

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | faithfulness judge 慢/貴(interactive UX)| Med | Med | 每 config 只算一次(非 N-run band);A/B 最多 2 judge eval;gpt-5.4-mini |
| R2 | RAGAs evaluator 不可用 / judge error 令 config-test fail | Med | High | try/except → None graceful;presentation 軸照返 |
| R3 | sync evaluator 阻 async event loop | Med | Med | `asyncio.to_thread` 包 |
| R4 | H7 frontend mockup 偏離(faithfulness 視覺)| Low | Med | design-first 先改 mockup;不清晰 → STOP+ask(§5.7) |
| R5 | faithfulness 數值對 KB 配置不敏感(質素軸無用)| Low | Low | 本期只交付軸 + 渲染;敏感度分析屬後評 |

## 6. Day-by-Day Breakdown(rough)

| Day | Date | Focus | Deliverables |
|---|---|---|---|
| D1 | 2026-06-05 | F0 kickoff + F1 backend faithfulness 接入 | F0, F1 |
| D2 | 2026-06-06 | F2 frontend(mockup design-first + render)+ F3 tests | F2, F3 |
| D3 | 2026-06-07 | F4 doc-sync + closeout | F4 |

## 7. Plan Changelog

| Date | Change | Reason | Approver |
|---|---|---|---|
| 2026-06-05 | Initial plan | W48 kickoff;Chris 揀 config-test 質素軸 scope Option A(runtime config-test faithfulness;ingestion-config 質素 out-of-scope per 架構限制)| Chris |
| 2026-06-05 | F1 deviation:plan 原寫「reuse `make_ragas_evaluator` 不改 eval module」,但 `make_ragas_evaluator` 算**全 4-metric**(faithfulness + answer_relevancy + 2 context),棄 3 個違反 faithfulness-only 成本意圖 → 改加 **additive** `make_faithfulness_evaluator(settings)`(faithfulness-only,復用 `patch_for_gpt5`+`Faithfulness`+threadpool bridge;現有 `make_ragas_evaluator` 不動 = 0 regression)+ 為新 helper 加 H6 unit test | cost-conscious(R6 catch:plan-text 假設 reuse 路徑與 code 不符)| AI |

---

**Lifecycle reminder**:plan locked after status=active。重大 deviation 入第 7 節 changelog。**F2 frontend = H7 design-first**(mockup 係 canonical spec,先改 mockup 再 match)。**Reuse `eval/ragas_evaluator.py` 不改**(H6 eval module 不動,只 config-test 接入)。
