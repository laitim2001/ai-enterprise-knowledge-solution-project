---
phase: W36-operational-debt-batch
plan_ref: ./plan.md
status: closed   # F4 收尾 2026-05-26 PASS
last_updated: 2026-05-26
---

# W36 — Checklist

> 原子化勾選項(每項 ≤ 1-2 小時工時)。3 個 HIGHEST 操作債一次過清理 — 純 procedural / config / tooling 性質,無 production behavior change。

## F0 — 啟動(plan + checklist + progress + R6 grep 驗證 + session-start sync)

- [x] F0.1 建立 `docs/01-planning/W36-operational-debt-batch/` folder
- [x] F0.2 R6 Day 0 recursive grep 驗證 — **catch (1) PC-W34-1** session-start.md §10.3 步驟 5 缺 endpoint health check;**catch (2) PC-W34-2** `backend/eval/ragas_evaluator.py:96-97` judge LLM deployment 來源確認;**catch (3) PC-W35-1** 5 個 runner files unicode 中招(`→ ≥ ≤ ⚠️ 🚨`)
- [x] F0.3 起草 `plan.md` 7 段 per W35 收尾 phase 模板
- [x] F0.4 起草 `checklist.md` 原子化勾選項(本文件)
- [x] F0.5 起草 `progress.md` Day 0 — 啟動行動 + R6 3 catches 報告 + W35 baseline 參考 + F-phase pre-implementation surface
- [x] F0.6 啟動 commit `bb15ce0` — `docs(planning): kickoff W36-operational-debt-batch + R6 Day 0 catch 3 HIGHEST candidates surface PC-W34-1 session-start protocol + PC-W34-2 RAGAs judge + PC-W35-1 runner cp1252`
- [x] F0.7 session-start.md §10 W36 row append `🟡 active 2026-05-26`(commit `bb15ce0`)+ W35 commits cumulative 7 補入 + W37+ rolling JIT row preserved(commit `2ffce8d`)

## F1 — PC-W34-1 CLAUDE.md §10.3 protocol amend(~30min,純文檔)— ✅ 完成

**R3 amend 2026-05-26**:F1 amend 對象修正為 **`CLAUDE.md §10.3`**(line 524-538)。

- [x] F1.1 讀 `CLAUDE.md` §10.3 line 524-535 — 6 步啟動 protocol 現況確認
- [x] F1.2 step 5b 起草 — pre-flight endpoint health check conditional trigger 「backend restart / eval run / RAGAs eval / Langfuse trace」+ PowerShell command 完整
- [x] F1.3 amend `CLAUDE.md §10.3` 加入 step 5b + 解釋 Docker `(unhealthy)` flag ≠ endpoint reachability + 失敗 path 至 user surface
- [x] F1.4 commit `3f65531` — `docs(claude-md): W36 F1 PC-W34-1 §10.3 pre-flight endpoint health check + R3 plan amend F1 target session-start.md → CLAUDE.md`

## F2 — PC-W34-2 RAGAs judge robustness(~2-3h)

### F2.1 現狀 audit(~30min)— ✅ 完成

- [x] F2.1.a 讀 `backend/eval/ragas_evaluator.py:1-157` 完整實作 — `patch_for_gpt5` shim 已 prepared GPT-5 reasoning judge + `_MIN_MAX_COMPLETION_TOKENS = 4096` floor 防 faithfulness JSON truncate;`_ascore_all` 直接 call ragas metric `ascore` 冇 explicit InstructorRetryException catch
- [x] F2.1.b 讀 `backend/storage/settings.py:65-67` 揭示 3 個 LLM deployments + `.env` 實際 override(`llm_judge=gpt-5.4-mini` / `llm_eval_judge=gpt-5.4-mini` `gpt-5-5-pro` Azure 可能未配)
- [x] F2.1.c 讀 W35 Option C raw JSON failed_queries 識別 pattern — 4 個 `answer_relevancy=0.6X` borderline + 5 個 `context_recall=0.00` keyword-mode artifact;InstructorRetryException 唔喺 raw JSON 顯式
- [x] F2.1.d 識別 **4** 個 fix path 取捨 ROI(新 path d 加入)+ surface 至 chat user pick

### F2.2 Path 選定 + 實作(~1-2h)— ✅ 完成

- [x] F2.2.a User 鎖定 path **(b)+(d) 組合** per cost containment policy(`gpt-5.4-mini` baseline 維持,zero LLM cost 上升)
- [x] F2.2.b 實作 (b) `ragas_evaluator.py:_ascore_all` per-metric try/except + log + fallback 0.0;實作 (d) `orchestrator.py:_RAGAS_ATTENTION_THRESHOLD` single 0.70 → `_RAGAS_ATTENTION_THRESHOLDS` per-metric dict(faithfulness/answer_relevancy/context_precision=0.65;context_recall=0.0 skip keyword-mode artifact)
- [x] F2.2.c 2 個 NEW unit test 加入 `test_eval_ragas.py`(`test_w36_ragas_attention_thresholds_per_metric_calibration` + `test_w36_context_recall_keyword_mode_artifact_not_surfaced`)
- [x] F2.2.d pytest 1086 passed + 25 skipped + 0 failed ✅(1084 baseline + 2 NEW W36 tests);ruff `All checks passed!`

### F2.3 小規模 sanity-check eval(可選)— 跳過

- [x] F2.3.a 跳過 — path (b) 唔改 judge LLM,只 wrap per-metric exception isolation;unit test 已 cover behavior
- [x] F2.3.b N/A — 唔 select path (c)

### F2.4 commit

- [ ] F2.4.a commit `feat(eval): W36 F2 PC-W34-2 RAGAs judge robustness — path (b) per-metric exception isolation + path (d) per-metric thresholds dict + context_recall keyword-mode artifact skip`

## F3 — PC-W35-1 runner cp1252 修正(~30min)

### F3.1 修正範疇識別 — ✅ 完成

- [x] F3.1.a `backend/w34-f1-ragas-runner.py:75`(`→` → `->`)+ line 93/95/97(`✅⚠️🚨` → `OK [WARN] [ALERT]`)
- [x] F3.1.b `backend/w33-f2-runner.py:80,82,89`(`≥` → `>=`)
- [x] F3.1.c `backend/w34-f2-runner.py:100,101`(`→` → `->`)
- [x] F3.1.d `backend/w35-f2-runner.py:15,16,110`(`≤` → `<=`,`→` → `->`)
- [x] F3.1.e `backend/w35-f1-ragas-runner.py` 預檢 — 已 ASCII safe 不需改

### F3.2 修正策略(預設 path iii 兩者結合)— ✅ 完成

- [x] F3.2.a 4 個 runner 開首全部加 `import sys; sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]`
- [x] F3.2.b ASCII 簡化全部完成:`→` → `->` / `≥` → `>=` / `≤` → `<=` / `⚠️` → `[WARN]` / `🚨` → `[ALERT]` / `✅` → `OK`

### F3.3 驗證 — ✅ 完成

- [x] F3.3.a 4 個 runner AST parse PASS — `ast.parse(open(f).read())` 驗證 syntactic valid
- [x] F3.3.b W36 嘅 specific edits 全部 ruff clean — 沒 introduce 新 errors;**8 個 pre-existing ruff issues 不屬 W36 scope**(F401 os unused + F841 cit_ids unused + F541 f-string × 6,全屬 W33-W35 寫 runner 留底)— Karpathy §1.3 strict 唔清非自己 mess

### F3.4 commit

- [ ] F3.4.a commit `fix(tooling): W36 F3 PC-W35-1 runner cp1252 print encoding — ASCII fallback + sys.stdout.reconfigure utf-8(4 runner files)`

## F4 — 收尾 + 跨文件同步 + commit + push

### A. 跨文件同步 per CLAUDE.md §10 R3 + R5 + R6 — ✅ 完成

- [x] plan.md frontmatter `status: active → closed`(F4 commit time)
- [x] checklist.md cross-cutting tick + N/A reason(本文件)
- [x] progress.md retro 7 段(What Worked / What Didn't / Carry-overs / ADR Triggers / Phase Gate Result / W37+ Priority Queue Locked / Actual vs Planned Effort)
- [x] session-start.md §10 W36 row `🟡 active` → `✅ closed`(F4 commit time)
- [x] 🚧 RISK_REGISTER NEW R 候選 — DEFERRED W37+(無新 risk material per F1+F2+F3 outcome)
- [x] ADR README — 無 NEW ADR(F1+F2+F3 全部 non-architectural per plan §1 + §4 R5)

### B. W37+ priority queue 評估 — ✅ 完成

- [x] B.1 W37+ 候選 promotion per F2 path (b)+(d) ship + F1/F3 outcome(documented retro §W37+ Priority Queue Locked)
- [x] B.2 (j') section_path prefix filter 保留 MEDIUM
- [x] B.3 PC-W33-1 + PC-W32-1/2 保留低優先級
- [x] B.4 W35 DEMOTED LOW 候選 仍 LOW + path (a) judge LLM 升級 永久 OUT per memory feedback_judge_llm_cost_policy.md
- [x] B.5 長期 carry-over(c)(e)(f)/BUG-026+027/W22 D8/W16 F1-F4 Track A IT cred + Q14 SME-validate reference_answer cascade

### C. commit + push

- [ ] F4 收尾 commit `docs(planning): W36 closeout — PC-W34-1 + PC-W34-2 (b)+(d) + PC-W35-1 3 operational debts cleared atomic`(純 docs sync;F1+F2+F3 已分別 commit per W31-W35 atomic pattern)
- [ ] push origin/main(per W33-W35 user-instruction precedent)

---

## Cross-Cutting

- [x] All deliverables committed to git(`bb15ce0` F0 啟動 + `3f65531` F1 + `576e6c6` F2 + `5520918` F3 + F4 收尾 commit pending)
- [x] All OQ status changes 反映於 `docs/decision-form.md` — 無 OQ 變動
- [x] All architectural-adjacent decisions documented as ADR — N/A 全部 3 candidates non-architectural per plan §1 + §4 R5
- [x] `progress.md` retro section 寫好 — 7 段 per F4 closeout
- [x] `progress.md` frontmatter status flipped to `closed`
- [x] Phase W37+ kickoff trigger 標記於 retro — candidates list update per F2 path 選擇 + 新 NEW user policy memory `feedback_judge_llm_cost_policy.md`

---

**Lifecycle reminder**:本 checklist 隨 plan deliverables 衍生。新加 deliverable 必須先入 plan + changelog 然後再加 checklist item。
