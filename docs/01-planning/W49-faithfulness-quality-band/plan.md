---
phase: W49-faithfulness-quality-band
name: "Config-Test Faithfulness Quality-Axis Noise Hardening (N-run band + N=1 warning) — 決策 7"
sprint_week: W49
start_date: 2026-06-05
end_date:                     # set at closeout
status: active
spec_refs:
  - ROADMAP-per-kb-tunable-config.md §3「候選 — 質素軸抗噪」+ 決策 7 (預設 warning gate;Chris 2026-06-05 揀 Option 1 = 沿用重跑次數做 band)
  - ADR-0040 (per-KB config-scope + config-test 雙軸:presentation + quality)
  - architecture.md §5.5.5 (KB Detail Settings config-test 試跑 panel)
  - backend/api/routes/config_test.py + backend/api/schemas/config_test.py (W43 harness + W48 faithfulness)
  - backend/eval/ragas_evaluator.py (make_faithfulness_evaluator — reuse, NOT modify)
  - memory project_per_kb_tunable_config_vision (註⑤ 抗噪) + feedback_judge_llm_cost_policy + project_synthesizer_overview_refuse_w25_d4 (stochastic over-claim 教訓)
prior_phase: W48-config-test-quality-axis
---

# Phase W49 — Config-Test Faithfulness Quality-Axis Noise Hardening

> **Plan version**:1.0(initial)
> **Owner**:Chris(Tech Lead)
> **Approved by**:Chris(2026-06-05 AskUserQuestion:決策 7 抗噪做法 = **Option 1「沿用重跑次數做 band」** — N≥2 顯示 faithfulness max−min band;N=1 單值 + warning;judge 成本 = 用戶自己揀嘅 N,唔加 toggle)

## 1. Scope

收 **決策 7 / roadmap「質素軸抗噪」候選**:W48 交付嘅 faithfulness **每 config 只算一次**(last-run,為省 judge 成本)→ single-shot 噪音大。2026-06-06 live 實測:同一個 `drive_user_manuals` **SAVED config** 兩次試跑 faithfulness **0.929 ↔ 0.53**(擺動 ~0.4),presentation 軸同期穩定。用戶試跑「撥到滿意」可能基於一次好彩/差彩 judge run 誤判 config(對齊 memory `project_synthesizer_overview_refuse_w25_d4` 嘅 W25 D4 stochastic over-claim 教訓)。

本期令 faithfulness **量化噪音** —— 沿用 config-test 既有嘅 `重跑次數`(runs,1-5)逐 run 計 faithfulness,聚合成 **`MetricBand`(min/max/mean/band)**,同 presentation counters **完全一致**。N≥2 → band 量到噪音(用戶見到 0.53–0.93 即知唔可信);N=1 → 單值 + 「單次方向性、勿單次定論」warning。**judge 成本 = 用戶自己揀嘅 N**(佢已為 presentation band opt-in 咗 N runs),由用戶控制,**唔加新 toggle**(keep H7 surface 細)。

**Scope kickoff R6 grep 已驗**(read config_test.py + schemas/config_test.py):
- `MetricBand`(min/max/mean/band)**已存在**,presentation counters(`citation_count` / `figure_count_raw` / `figure_count_dedup` / `latency_ms`)全部經 `_band()` 用緊 → faithfulness 沿用零新 model。
- W48 `_run_n` 現只 capture `last_answer` + `last_contexts` 做**一次** `asyncio.to_thread(faithfulness_fn, ...)`。W49 改為 capture **每 run** 嘅 answer+contexts → 逐 run judge → `_band`。
- `make_faithfulness_evaluator(settings)` 簽名 `(question, answer, contexts) -> float | None` **不變**(reuse,不改 eval module)。

**Out-of-scope**:judge LLM 升級(維 `gpt-5.4-mini`);faithfulness 以外 RAGAs metric(correctness / context_recall 需標註集 — AUDIT-D (ii) 留未來);ingestion-config 質素(reindex→eval,另一機制);per-document scope(決策 1);N-run band 以外嘅 warning-only 變體(Chris 已揀 Option 1)。

**Sprint week origin**:roadmap 決策 7(2026-06-06 live 證觸發);Chris 2026-06-05 pick(W47 F5 + W48 footer 修正 session 之後)。

## 2. Key Design Decisions(kickoff lock)

- **faithfulness 沿用既有 `MetricBand`**(非新 model):`ConfigRunSummary.faithfulness: float | None` → **`MetricBand | None`**。同 presentation counters 一致(mean = headline,band = max−min 噪音指標)。**Schema breaking change**(W48 啱加嘅欄),所有 consumer(frontend types + tests)同期更新。
- **逐 run judge,並發聚合**:`_run_n` 主 loop capture 每 run 嘅 `(answer, contexts)` 入 list → loop 完 `asyncio.gather(*[asyncio.to_thread(faithfulness_fn, query, ans, ctx) ...])` 並發跑 N 個 judge(N≤5 bounded,config-test 本身 = 慢 harness 非 hot path)→ 收 `list[float | None]`。
- **Graceful degradation(per-run + 整體)**:每個 judge call 自身 try/except → None(現有行為);filter 走 None → 剩 ≥1 → `_band(floats)`(band 可能 over < N runs);剩 0(全 fail / judge 不可用 / `eval_faithfulness=False`)→ `faithfulness = None`(config-test 照返 presentation 軸,唔 fail)。
- **N=1 行為**:band over [x] → min=max=mean=x、band=0;前端偵測 `runs==1`(由 `result.runs` 或 `summary.runs.length`)→ 顯示單值 + 「單次 judge · 方向性 · 勿單次定論」warning(取代量化 band)。
- **judge 成本 = 用戶 N**(Option 1 核心):無新 toggle;`eval_faithfulness` flag 維持(off → None fast path)。A/B 時 draft+saved 各 N judge → 最多 N=5 × 2 = 10 judge eval(用戶 opt-in,default N=3)。
- **Footer copy 連帶更新**:W48 footer(`16fc51f` 啱改)「faithfulness 質素軸每 config 算一次」→ 已被 W49 取代(N runs band),F2 同步改正(design-first)。
- **judge LLM 不變**:reuse `settings.azure_openai_deployment_llm_judge`(gpt-5.4-mini)。
- **無新 ADR**:extend ADR-0040 已定義雙軸 + 既有 config-test component(非新架構/vendor/storage);fulfill 決策 7。

## 3. Deliverables

### F0 — Phase kickoff
- **Acceptance criteria**:plan/checklist/progress 三件套 committed(R1);scope Option 1 + key design 鎖定;R6 grep 已記 progress
- **Owner**:AI

### F1 — Backend:faithfulness N-run band
- **Spec ref**:`config_test.py` `_run_n` + `schemas/config_test.py` `ConfigRunSummary`;reuse `MetricBand` + `_band()` + `make_faithfulness_evaluator`
- **Acceptance criteria**:
  - `ConfigRunSummary.faithfulness: float | None` → **`MetricBand | None`**(docstring 更新:band over runs;None = 軸關/無 judge/全 fail)
  - `_run_n` capture **每 run** `(answer, [c.chunk_text for c in resp.retrieved_chunks])` → loop 完 `asyncio.gather(asyncio.to_thread(faithfulness_fn, query, ans, ctx) ...)` → `list[float | None]`
  - filter None → ≥1 → `_band(floats)`;0 → None(graceful)
  - `faithfulness_fn is None`(eval_faithfulness=False)→ 唔 judge → None fast path(不變)
  - judge 維 gpt-5.4-mini(reuse settings,不改)
  - mypy --strict clean(新改動零 error;舊 function pre-existing error 不算)+ ruff check+format clean
- **Owner**:AI

### F2 — Frontend:band render + N=1 warning(H7 design-first per ADR-0024)
- **Spec ref**:§5.5.5;mockup `ekp-page-kb.jsx` `KbTestResultCard` faithfulness headline + footer
- **Acceptance criteria**:
  - mockup `ekp-page-kb.jsx` `KbTestResultCard` faithfulness headline 由單值 → **mean + band 指標**(N≥2)/ 單值 + warning(N=1);design-first 先改 mockup;2 call site 更新示例
  - mockup footer copy(`ekp-page-kb.jsx:942`)更新:「faithfulness 質素軸每 config 算一次」→ 反映 N-run band(對齊 presentation band framing)
  - `frontend/lib/api/config-test.ts`:`ConfigRunSummary.faithfulness: number | null` → **`MetricBand | null`**(reuse 既有 presentation `MetricBand` TS type)
  - `ConfigResultCard`(`page.tsx`)render faithfulness mean + band + N=1 warning;footer copy(`page.tsx:2211`)同步;100% match 更新後 mockup(H7 fidelity)
  - tsc --noEmit clean + next lint clean + `[oklch`=0 preserved
- **Owner**:AI

### F3 — Tests
- **Spec ref**:§5.6 H6(config_test.py 鼓勵;reuse eval module 不改故不需新 eval test)
- **Acceptance criteria**:
  - backend:更新既有 W48 faithfulness test(`draft.faithfulness` 由 float → MetricBand);新 test:band over N runs(mock evaluator 逐 call 返唔同值 → 核 min/max/mean/band)+ N=1 → band=0 + 核每 run answer/contexts 傳啱 + 部分 run None → band over 成功 run + 全 None → None + disabled → None
  - frontend vitest:`kb-settings-tuning` 試跑 test 更新 faithfulness assert(band 顯示 + N=1 warning)+ FAKE_RESULT 補 MetricBand
  - 既有 config_test 7 + eval_ragas 7 test 0 regression(autouse `_no_judge` fixture 保留)
- **Owner**:AI

### F4 — Doc-sync + closeout
- **Acceptance criteria**:
  - architecture.md §5.5.5 加 W49 amendment(faithfulness N-run band 抗噪;成本 = 用戶 N)
  - roadmap §3「質素軸抗噪」候選行 → ✅ W49 shipped + 決策 7 → ✅ RESOLVED(Option 1)
  - session-start §10 W49 row + plan.md status→closed + changelog
  - Phase Gate G1-G5 + retro + checklist tick / 🚧
- **Owner**:AI

## 4. Success Criteria(Phase Gate)

| # | Criterion | Target | Measure | Block closeout? |
|---|---|---|---|---|
| G1 | faithfulness 返 N-run `MetricBand`(量化噪音)| MetricBand on summary(A/B 各一);band = max−min | pytest + manual | Yes |
| G2 | graceful degradation | per-run None → band over 成功 run;全 None / 軸關 → None,config-test 唔 fail | pytest | Yes |
| G3 | frontend render band + N=1 warning 100% match mockup | H7 fidelity(band 顯示 + N=1 warning + footer 改正)| mockup 對齊 + vitest | Yes |
| G4 | pytest + ruff + mypy + tsc/lint/build clean | all green | CI commands | Yes |
| G5 | judge gpt-5.4-mini + cost = 用戶 N + 無新 ADR/vendor | cost policy + Option 1 + ADR-0040 extend | review | Yes |

## 5. Risks(Phase-Specific)

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | N judge × A/B = 最多 10 judge eval(N=5)→ 成本/延遲 | Med | Med | 用戶控制 N(opt-in,default 3);gather 並發;config-test 本身 = 慢 harness 用戶預期 |
| R2 | N 個並發 judge call 撞 Azure OpenAI rate limit | Low | Med | N≤5 bounded;per-call graceful None(撞 limit → 該 call None,band over 成功 run);必要時退 sequential |
| R3 | schema breaking change(faithfulness float→MetricBand)爆 W48 frontend/test | High | Low | 同期更新所有 consumer(frontend types + page.tsx + vitest + backend test);W48 啱加未對外 |
| R4 | H7 mockup drift(band 視覺 + N=1 warning)| Low | Med | design-first 先改 mockup;不清晰 → STOP+ask(§5.7)|
| R5 | footer copy(`16fc51f` 啱改)又 stale | Low | Low | F2 同步改正(W49 取代「每 config 算一次」framing)|

## 6. Day-by-Day Breakdown(rough)

| Day | Date | Focus | Deliverables |
|---|---|---|---|
| D1 | 2026-06-05 | F0 kickoff + F1 backend N-run band | F0, F1 |
| D2 | 2026-06-06 | F2 frontend(mockup design-first + band/warning render)+ F3 tests | F2, F3 |
| D3 | 2026-06-07 | F4 doc-sync + closeout | F4 |

## 7. Plan Changelog

| Date | Change | Reason | Approver |
|---|---|---|---|
| 2026-06-05 | Initial plan | W49 kickoff;Chris AskUserQuestion 揀決策 7 抗噪 **Option 1**(沿用重跑次數做 band;N=1 warning;judge 成本 = 用戶 N,無新 toggle)| Chris |

---

**Lifecycle reminder**:plan locked after status=active。重大 deviation 入第 7 節 changelog。**F2 frontend = H7 design-first**(mockup 係 canonical spec,先改 mockup 再 match)。**Reuse `eval/ragas_evaluator.py` 不改 + reuse 既有 `MetricBand`/`_band()`**(零新 model)。
