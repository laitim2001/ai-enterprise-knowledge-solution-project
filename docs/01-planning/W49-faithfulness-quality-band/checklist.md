# W49 — Faithfulness Quality-Axis Noise Band · Checklist

> Atomic items per deliverable。不可刪未勾項(只 `[x]` 或標 🚧 + reason)。
> **F2 frontend = H7 design-first**(mockup 先改再 match);**reuse `eval/ragas_evaluator.py` + 既有 `MetricBand`/`_band()` 不另造**。

## F0 — Phase kickoff
- [x] F0.1 plan/checklist/progress 三件套 committed(R1);scope Option 1 + key design 鎖定;R6 grep 記 progress

## F1 — Backend:faithfulness N-run band
- [x] F1.1 `ConfigRunSummary.faithfulness` 由 `float | None` → **`MetricBand | None`**(docstring 更新:band over runs)
- [x] F1.2 `_run_n` 主 loop capture **每 run** `(answer, [c.chunk_text for c in resp.retrieved_chunks])` 入 list(取代只存 last_*)
- [x] F1.3 loop 完 `asyncio.gather(*[asyncio.to_thread(faithfulness_fn, qreq.query, ans, ctx) for ans, ctx in per_run])` → `list[float | None]`(並發,off event loop;抽成 `_faithfulness_band` helper)
- [x] F1.4 filter None → ≥1 → `_band(floats)`;0(全 fail / 軸關)→ `None`(graceful,config-test 唔 fail)
- [x] F1.5 `faithfulness_fn is None`(eval_faithfulness=False)→ 唔 judge → None fast path(不變);judge 維 gpt-5.4-mini(reuse settings)
- [x] F1.6 mypy --strict clean(我兩個檔零 error;exit 1 純跨模組 pre-existing)+ ruff check+format clean

## F2 — Frontend:band render + N=1 warning(H7 design-first)
- [x] F2.1 mockup `ekp-page-kb.jsx` `KbTestResultCard` faithfulness headline:單值 → **mean + band 指標**(N≥2)/ 單值 + 「單次 judge · 方向性 · 重跑次數調高至 ≥2 先見穩定度 band」warning(N=1);2 call site 更新示例(faith mean + faithBand + runs)
- [x] F2.2 mockup footer `ekp-page-kb.jsx:942`:「faithfulness 質素軸每 config 算一次」→「忠實度質素軸 + presentation counters 逐 run 算 band · N=1 只方向性」
- [x] F2.3 `config-test.ts`:`ConfigRunSummary.faithfulness: number | null` → **`MetricBand | null`**(reuse 既有 presentation `MetricBand` TS type)+ `ConfigTestRequest` 不變
- [x] F2.4 `ConfigResultCard`(`page.tsx`)render faithfulness mean + band + N=1 warning(由 `summary.runs.length` 判 N=1)+ footer `page.tsx:2211` 同步;100% match 更新後 mockup
- [x] F2.5 tsc --noEmit clean + next lint clean(唯一 pre-existing chat `<img>` warning)+ `[oklch`=0 preserved

## F3 — Tests
- [x] F3.1 backend:更新既有 W48 faithfulness test(`_computed` `draft.faithfulness` float → MetricBand 取 `.mean`/`.band`)
- [x] F3.2 backend 新 test:`_band_over_runs`(threadsafe iter [0.9,0.5,0.7] → min=0.5/max=0.9/band≈0.4/mean≈0.7,order-independent)+ 核每 run answer/contexts 傳啱(`_computed`)
- [x] F3.3 backend 新 test:`_n1_band_zero`(runs=1 → `{min:.8,max:.8,mean:.8,band:0}`)+ `_partial_none`(iter [0.9,None,0.5] → band over 成功 run)+ `_disabled`/`_graceful` None case 不變
- [x] F3.4 backend:既有 config_test 7 + eval_ragas 7 = 0 regression(autouse `_no_judge` fixture 保留)→ **17 passed**
- [x] F3.5 frontend vitest:`kb-settings-tuning` 主 A/B test 改驗 band span(±0.16/±0.05)+ 無 warning;NEW N=1 test(`mockResolvedValueOnce` → 「單次 judge」warning + mean 0.80 無 band);FAKE_RESULT 補 MetricBand + runs 3 entries;**4 passed** + full vitest 106 passed(flaky timeout 隔離證非 regression)

## F4 — Doc-sync + closeout
- [ ] F4.1 architecture.md §5.5.5 加 W49 amendment(faithfulness N-run band 抗噪;成本 = 用戶 N;graceful)
- [ ] F4.2 roadmap §3「質素軸抗噪」候選行 → ✅ W49 shipped + 決策 7 → ✅ RESOLVED(Option 1)+ 逐期重點 bullet 標 done
- [ ] F4.3 session-start §10 W49 closed row + W50+ rolling JIT(local-only,gitignored)+ plan.md status→closed + changelog
- [ ] F4.4 Phase Gate G1-G5 = **PASS** + retro + carry-overs(見 progress)+ checklist 全 tick(無 🚧)+ W50+ candidates
