# W49 — Faithfulness Quality-Axis Noise Band · Progress

> Daily progress + decisions + commits + 結尾 retro。每 daily commit 對應 Day-N entry(R2)。

---

## Day 1 — 2026-06-05

### Context / kickoff
本 session 連收 W47 F5(reindex UI live-verify RESOLVED,`6db270e`)+ W48 footer copy 修正(`16fc51f`)。用戶問「W43 開始嘅 vision 仲有幾多未做」→ 我據 `ROADMAP-per-kb-tunable-config.md` 給全圖(per-KB 主幹 W43→W48 已交付;未做 = per-document / 質素軸深化 / production reindex / Tier 2 / 操作期)。用戶揀**先做決策 7 faithfulness 抗噪**。

### 決策
- **AskUserQuestion(抗噪做法)**:Chris 揀 **Option 1「沿用重跑次數做 band」** — N≥2 顯示 faithfulness max−min band(同 presentation band 一致量化噪音);N=1 單值 + 「單次方向性」warning;judge 成本 = 用戶自己揀嘅 N(已為 presentation band opt-in),**唔加 toggle**。否決 Option 2(warning-only,唔量化噪音)+ Option 3(固定 N,脫鈎用戶 N + 強制成本)。
- **Key design lock**(plan §2):faithfulness 沿用既有 `MetricBand`(零新 model)+ 逐 run judge `asyncio.gather` 並發 + graceful(per-run None → band over 成功 run;全 None → None)+ N=1 → band=0 + warning + judge 維 gpt-5.4-mini + **無新 ADR**(extend ADR-0040 雙軸)。

### R6 grep 驗證(plan kickoff)— config_test 結構確認
- `MetricBand`(min/max/mean/band)**已存在**(`schemas/config_test.py:74`),presentation counters 全部經 `_band()`(`config_test.py:58`)用緊 → faithfulness 沿用零新 model。
- W48 `_run_n`(`config_test.py:67`)現只 capture `last_answer`+`last_contexts` 做**一次** `asyncio.to_thread(faithfulness_fn,...)`(line 113-117)→ W49 改 capture 每 run + gather N judge。
- `make_faithfulness_evaluator` 簽名 `(question, answer, contexts) -> float | None` 不變(reuse)。
- **無 plan-text contamination**:plan 引用嘅 function/field 全部 grep 對齊現 code(R6 recursive scope 過)。

### Done
- F0 R1 phase 三件套建立(plan/checklist/progress);Phase Gate G1-G5 定義

### F1 backend(同日)
- `schemas/config_test.py`:`ConfigRunSummary.faithfulness` `float | None` → **`MetricBand | None`**(docstring 更新:band over runs + 2026-06-06 noise 證據)
- `routes/config_test.py`:NEW `_faithfulness_band(faithfulness_fn, query, per_run_qa)` helper —— `asyncio.gather(*[asyncio.to_thread(faithfulness_fn, query, ans, ctx) ...])` 並發逐 run judge → filter None → `_band(ok)` if ok else None;`_run_n` 主 loop 改 capture **每 run** `(answer, [c.chunk_text for c in resp.retrieved_chunks])` 入 `per_run_qa`(取代只存 last_*)→ call `_faithfulness_band`
- 驗:ruff check+format clean;mypy --strict **我兩個檔零 error**(exit 1 純跨模組 pre-existing,同 W48 一樣)

### F2 frontend(同日,H7 design-first)
- mockup `ekp-page-kb.jsx` `KbTestResultCard`:signature 加 `faithBand` + `runs`;headline 由單值 → mean + `±{faithBand}`(N≥2)/ 單值 + 「單次 judge · 方向性 · 重跑次數調高至 ≥2 先見穩定度 band」warning(N=1);2 call site 更新(DRAFT faith 0.78 ±0.16 runs 3 揭噪音 / SAVED 0.92 ±0.05)
- mockup footer(`:942`,`16fc51f` 改過嗰句)→「忠實度質素軸 + presentation counters 逐 run 算 band · N=1 只方向性」
- `config-test.ts`:`faithfulness: number | null` → **`MetricBand | null`**(reuse 既有 presentation `MetricBand` TS type)
- `page.tsx` `ConfigResultCard`:headline `summary.faithfulness.mean.toFixed(2)` + `±band`(`summary.runs.length >= 2`)+ N=1 warning(`summary.runs.length === 1`);footer(`:2211`)同步
- 驗:tsc --noEmit clean

### F3 tests(同日)
- backend `test_config_test_route.py`:`_computed` 改 MetricBand 斷言(mean=0.95 + band=0);NEW `_band_over_runs`(threadsafe iter [0.9,0.5,0.7] → min .5/max .9/band .4/mean .7,order-independent)+ `_n1_band_zero`(runs=1 → `{min:.8,max:.8,mean:.8,band:0}`)+ `_partial_none`(iter [0.9,None,0.5] → band over 成功 run);`_disabled`+`_graceful` None case 不變
- frontend `kb-settings-tuning.test.tsx`:FAKE_RESULT draft/saved runs 補至 3 entries + faithfulness → MetricBand(draft ±0.16 / saved ±0.05);主 A/B test 改驗 `±0.16`/`±0.05` band span + 無「單次 judge」warning;NEW N=1 test(`mockResolvedValueOnce` runs=1 → 「單次 judge」warning + mean 0.80 無 band span)
- 驗:backend **pytest 17 passed**(config_test 10 + eval_ragas 7)0 regression;frontend **kb-settings-tuning 4 passed** + full vitest **106 passed**(kb-detail/kb-settings-reindex full-suite flaky timeout = loaded machine,隔離單跑 5 passed 證非 regression;「Error: boom」= intentional pre-existing)+ tsc + lint(唯一 pre-existing chat `<img>` warning)+ `[oklch`=0

### Commits
- (F0 kickoff `05019c7`;F1-F3 code+tests commit pending)

### Blockers / carry-over
- 無 blocker。infra 已起(azurite 23252 / backend 8000 **跑緊 W48 code,W49 改動未 reload** / frontend 46364 clean .next)。**注**:F4 後若要 live 驗 W49 band,要 restart backend(同 W48→W47F5 一樣)。
