# W49 — Faithfulness Quality-Axis Noise Band · Checklist

> Atomic items per deliverable。不可刪未勾項(只 `[x]` 或標 🚧 + reason)。
> **F2 frontend = H7 design-first**(mockup 先改再 match);**reuse `eval/ragas_evaluator.py` + 既有 `MetricBand`/`_band()` 不另造**。

## F0 — Phase kickoff
- [ ] F0.1 plan/checklist/progress 三件套 committed(R1);scope Option 1 + key design 鎖定;R6 grep 記 progress

## F1 — Backend:faithfulness N-run band
- [ ] F1.1 `ConfigRunSummary.faithfulness` 由 `float | None` → **`MetricBand | None`**(docstring 更新:band over runs)
- [ ] F1.2 `_run_n` 主 loop capture **每 run** `(answer, [c.chunk_text for c in resp.retrieved_chunks])` 入 list(取代只存 last_*)
- [ ] F1.3 loop 完 `asyncio.gather(*[asyncio.to_thread(faithfulness_fn, qreq.query, ans, ctx) for ans, ctx in per_run])` → `list[float | None]`(並發,off event loop)
- [ ] F1.4 filter None → ≥1 → `_band(floats)`;0(全 fail / 軸關)→ `None`(graceful,config-test 唔 fail)
- [ ] F1.5 `faithfulness_fn is None`(eval_faithfulness=False)→ 唔 judge → None fast path(不變);judge 維 gpt-5.4-mini(reuse settings)
- [ ] F1.6 mypy --strict clean(新改動零 error)+ ruff check+format clean

## F2 — Frontend:band render + N=1 warning(H7 design-first)
- [ ] F2.1 mockup `ekp-page-kb.jsx` `KbTestResultCard` faithfulness headline:單值 → **mean + band 指標**(N≥2)/ 單值 + 「單次 judge · 方向性 · 勿單次定論」warning(N=1);2 call site 更新示例(faith mean + band + runs)
- [ ] F2.2 mockup footer `ekp-page-kb.jsx:942`:「faithfulness 質素軸每 config 算一次」→ 反映 N-run band framing
- [ ] F2.3 `config-test.ts`:`ConfigRunSummary.faithfulness: number | null` → **`MetricBand | null`**(reuse 既有 presentation `MetricBand` TS type)+ `ConfigTestRequest` 不變
- [ ] F2.4 `ConfigResultCard`(`page.tsx`)render faithfulness mean + band + N=1 warning(由 `result.runs`/`summary.runs.length` 判 N=1)+ footer `page.tsx:2211` 同步;100% match 更新後 mockup
- [ ] F2.5 tsc --noEmit clean + next lint clean(唯一 pre-existing chat `<img>` warning)+ `[oklch`=0 preserved

## F3 — Tests
- [ ] F3.1 backend:更新既有 W48 faithfulness test(`draft.faithfulness` float → MetricBand 取 `.mean`/`.band`)
- [ ] F3.2 backend 新 test:band over N runs(mock evaluator 逐 call 返唔同值 [0.9, 0.5, 0.7] → 核 min=0.5/max=0.9/band=0.4)+ 核每 run answer/contexts 傳啱
- [ ] F3.3 backend 新 test:N=1 → band=0(min=max=mean=值)+ 部分 run None → band over 成功 run + 全 None → None + disabled → None graceful
- [ ] F3.4 backend:既有 config_test 7 + eval_ragas 7 = 0 regression(autouse `_no_judge` fixture 保留)
- [ ] F3.5 frontend vitest:`kb-settings-tuning` 試跑 test 更新 faithfulness assert(band 顯示 + N=1 warning)+ FAKE_RESULT 補 MetricBand;0 regression

## F4 — Doc-sync + closeout
- [ ] F4.1 architecture.md §5.5.5 加 W49 amendment(faithfulness N-run band 抗噪;成本 = 用戶 N;graceful)
- [ ] F4.2 roadmap §3「質素軸抗噪」候選行 → ✅ W49 shipped + 決策 7 → ✅ RESOLVED(Option 1)+ 逐期重點 bullet 標 done
- [ ] F4.3 session-start §10 W49 closed row + W50+ rolling JIT(local-only,gitignored)+ plan.md status→closed + changelog
- [ ] F4.4 Phase Gate G1-G5 = **PASS** + retro + carry-overs(見 progress)+ checklist 全 tick(無 🚧)+ W50+ candidates
