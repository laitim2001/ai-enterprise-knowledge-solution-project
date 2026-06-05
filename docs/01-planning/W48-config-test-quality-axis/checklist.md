# W48 — Config-Test Quality Axis (faithfulness) · Checklist

> Atomic items per deliverable。不可刪未勾項(只 `[x]` 或標 🚧 + reason)。
> **F2 frontend = H7 design-first**(mockup 先改再 match);**reuse `eval/ragas_evaluator.py` 不改**。

## F0 — Phase kickoff
- [x] F0.1 plan/checklist/progress 三件套 committed(R1);scope Option A + key design 鎖定

## F1 — Backend:faithfulness 接入 config-test
- [ ] F1.1 `ConfigTestRequest` 加 `eval_faithfulness: bool = True`
- [ ] F1.2 `ConfigRunSummary` 加 `faithfulness: float | None`(config-level,單次算)
- [ ] F1.3 `_run_n`/caller capture last-run `answer` + `[c.chunk_text for c in resp.retrieved_chunks]` → `RagasQuerySample` → `asyncio.to_thread(ragas_evaluator, sample)` → summary.faithfulness
- [ ] F1.4 evaluator 構造一次 reuse(draft+saved 共用);error/unavailable → None(try/except + log warning,唔 fail config-test);`eval_faithfulness=False` → None fast path
- [ ] F1.5 judge LLM 維 `gpt-5.4-mini`(reuse `settings.azure_openai_deployment_llm_judge`,不改)
- [ ] F1.6 mypy --strict clean + ruff clean

## F2 — Frontend:faithfulness 渲染(H7 design-first)
- [ ] F2.1 mockup `ekp-page-kb.jsx` 試跑 `KbTestResultCard` 加 faithfulness 質素軸 metric(design-first 先改)
- [ ] F2.2 `frontend/lib/api/config-test.ts`:`ConfigRunSummary` 加 `faithfulness: number | null`;`ConfigTestRequest` 加 `eval_faithfulness?: boolean`
- [ ] F2.3 `ConfigResultCard`(`page.tsx`)render faithfulness(A/B 兩卡;null → 「—」)100% match 更新後 mockup
- [ ] F2.4 tsc + lint clean + `[oklch`=0 preserved

## F3 — Tests
- [ ] F3.1 backend:faithfulness 計算(mock evaluator → summary.faithfulness 有值)
- [ ] F3.2 backend:`eval_faithfulness=False` → None + evaluator error → None graceful
- [ ] F3.3 既有 config-test / kb-settings-tuning test 0 regression
- [ ] F3.4 frontend vitest:config-test panel render faithfulness(有值 + null「—」)

## F4 — Doc-sync + closeout
- [ ] F4.1 architecture.md §5.5.5 config-test note 加 faithfulness 質素軸(ADR-0040 雙軸 fulfilled)
- [ ] F4.2 roadmap §3「NEW 並行」+ 決策 6 + AUDIT-D → ✅ done
- [ ] F4.3 session-start §10 W48 row(local-only)
- [ ] F4.4 Phase Gate G1-G5 + retro + checklist tick / 🚧 + W49+ rolling JIT
