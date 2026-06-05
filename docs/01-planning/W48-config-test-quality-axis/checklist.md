# W48 — Config-Test Quality Axis (faithfulness) · Checklist

> Atomic items per deliverable。不可刪未勾項(只 `[x]` 或標 🚧 + reason)。
> **F2 frontend = H7 design-first**(mockup 先改再 match);**reuse `eval/ragas_evaluator.py` 不改**。

## F0 — Phase kickoff
- [x] F0.1 plan/checklist/progress 三件套 committed(R1);scope Option A + key design 鎖定

## F1 — Backend:faithfulness 接入 config-test
- [x] F1.1 `ConfigTestRequest` 加 `eval_faithfulness: bool = True`
- [x] F1.2 `ConfigRunSummary` 加 `faithfulness: float | None`(config-level,單次算)
- [x] F1.3 `_run_n` capture last-run `answer` + `[c.chunk_text for c in resp.retrieved_chunks]` → `asyncio.to_thread(faithfulness_fn, query, answer, contexts)` → summary.faithfulness(plain tuple,非 RagasQuerySample)
- [x] F1.4 **additive** `make_faithfulness_evaluator(settings)`(R3 deviation — faithfulness-only,現有 `make_ragas_evaluator` 不動);構造一次 reuse(draft+saved 共用);per-call try/except → None graceful;`eval_faithfulness=False` → 唔 build evaluator → None
- [x] F1.5 judge LLM 維 `gpt-5.4-mini`(reuse `settings.azure_openai_deployment_llm_judge`,不改)
- [x] F1.6 mypy --strict clean(我新 helper + config_test.py 零 error;6 個 pre-existing error 喺舊 function 與改動無關)+ ruff check+format clean

## F2 — Frontend:faithfulness 渲染(H7 design-first)
- [x] F2.1 mockup `ekp-page-kb.jsx` `KbTestResultCard` 加 `faith` prop + 全寬 headline cell「忠實度(faithfulness · 反幻覺 · 0–1)」置 grid 頂(success 色 / null「—未評」);2 call site 加 faith="0.97"/"0.94"
- [x] F2.2 `config-test.ts`:`ConfigRunSummary` 加 `faithfulness: number | null`;`ConfigTestRequest` 加 `eval_faithfulness?: boolean`
- [x] F2.3 `ConfigResultCard`(`page.tsx`)加 faithfulness headline cell `.toFixed(2)`(A/B;null→「—」+「未評」)100% match 更新後 mockup
- [x] F2.4 tsc --noEmit clean + next lint clean(唯一 pre-existing chat `<img>` warning)+ `[oklch`=0 preserved

## F3 — Tests
- [x] F3.1 backend `test_config_test_faithfulness_computed`:mock evaluator → `draft.faithfulness==0.95` + 核 evaluator 收到 last-run answer「ans [chunk-a][chunk-b]」+ contexts `["x","y"]`
- [x] F3.2 backend:`test_..._disabled`(eval_faithfulness=false → None,evaluator 不 build)+ `test_..._graceful_when_evaluator_returns_none`(返 None → 200 + draft/saved faithfulness None)
- [x] F3.3 既有 config_test 4 + eval_ragas 6 = 0 regression(+ autouse `_no_judge` fixture 保護既有 test 唔觸真 Azure);+ `test_make_faithfulness_evaluator_returns_none_without_azure_key`(H6 helper)= backend 14 passed
- [x] F3.4 frontend vitest:kb-settings-tuning 試跑 test 加 faithfulness assert(忠實度 ≥2 + 0.97 + 0.94)+ FAKE_RESULT 補 faithfulness;kb-settings 6 passed 0 regression

## F4 — Doc-sync + closeout
- [ ] F4.1 architecture.md §5.5.5 config-test note 加 faithfulness 質素軸(ADR-0040 雙軸 fulfilled)
- [ ] F4.2 roadmap §3「NEW 並行」+ 決策 6 + AUDIT-D → ✅ done
- [ ] F4.3 session-start §10 W48 row(local-only)
- [ ] F4.4 Phase Gate G1-G5 + retro + checklist tick / 🚧 + W49+ rolling JIT
