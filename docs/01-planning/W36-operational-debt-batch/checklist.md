---
phase: W36-operational-debt-batch
plan_ref: ./plan.md
status: active   # F0 啟動 2026-05-26
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
- [ ] F0.6 啟動 commit — `docs(planning): kickoff W36-operational-debt-batch + R6 Day 0 catch 3 HIGHEST candidates surface PC-W34-1 session-start protocol + PC-W34-2 RAGAs judge + PC-W35-1 runner cp1252`
- [ ] F0.7 session-start.md §10 W36 row append `🟡 active 2026-05-26`(commit hash post F0.6)+ W35 已 closed 維持 + W37+ rolling JIT row defer

## F1 — PC-W34-1 session-start protocol amend(~30min,純文檔)

- [ ] F1.1 讀 `docs/12-ai-assistant/01-prompts/01-session-start.md` §10.3 6 步啟動 protocol 現況
- [ ] F1.2 起草新增 step 5b(或 6c)pre-flight endpoint health check 含具體 PowerShell command(`Invoke-WebRequest /api/public/health` + `docker exec ekp-postgres psql SELECT 1`)
- [ ] F1.3 amend §10.3 加入新步驟 + 解釋 Docker `unhealthy` flag = timing artifact ≠ endpoint reachability
- [ ] F1.4 commit `docs(prompts): W36 F1 PC-W34-1 session-start §10.3 pre-flight endpoint health check`

## F2 — PC-W34-2 RAGAs judge robustness(~2-3h)

### F2.1 現狀 audit(~30min)

- [ ] F2.1.a 讀 `backend/eval/ragas_evaluator.py:65-100` `make_ragas_evaluator` 完整實作
- [ ] F2.1.b 讀 `backend/storage/settings.py` `azure_openai_deployment_llm_judge` default + `.env` 實際值
- [ ] F2.1.c 讀 W35 F1.4 Option B + Option C raw JSON failed_queries 識別 InstructorRetryException pattern + answer_relevancy 0.6X 邊緣失敗
- [ ] F2.1.d 識別 3 個 fix path 取捨 ROI(path a judge LLM 升級 / path b JSON 解析穩健化 / path c yaml metadata 過濾)+ surface 至 chat user pick

### F2.2 Path 選定 + 實作(~1-2h)

- [ ] F2.2.a User 鎖定 path(F2.1 完成 surface 後 user pick A/B/C)
- [ ] F2.2.b 實作對應 path
- [ ] F2.2.c 寫 unit test / config-state test / yaml schema validation(視乎 path)
- [ ] F2.2.d pytest baseline 1084 維持 + ruff PASS

### F2.3 小規模 sanity-check eval(可選)

- [ ] F2.3.a 若 path a/b 改 judge layer,可選跑 3-5 query 小規模 eval 驗證 InstructorRetryException 消失
- [ ] F2.3.b 若 path c 純 yaml metadata 過濾,可選驗證 eval-set 過濾邏輯

### F2.4 commit

- [ ] F2.4.a commit `feat(eval): W36 F2 PC-W34-2 RAGAs judge robustness — {path 描述}`

## F3 — PC-W35-1 runner cp1252 修正(~30min)

### F3.1 修正範疇識別

- [ ] F3.1.a `backend/w34-f1-ragas-runner.py:75`(`→`)+ line 95(`⚠️`)+ line 97(`🚨`)
- [ ] F3.1.b `backend/w33-f2-runner.py:80,82,89`(`≥`)
- [ ] F3.1.c `backend/w34-f2-runner.py:100,101`(`→`)
- [ ] F3.1.d `backend/w35-f2-runner.py:15,16,110`(`≤`,`→`)
- [ ] F3.1.e 可選 `backend/w35-f1-ragas-runner.py` 預檢(已 ASCII safe 但 confirm)

### F3.2 修正策略(預設 path iii 兩者結合)

- [ ] F3.2.a 每 runner 開首加 `import sys; sys.stdout.reconfigure(encoding="utf-8")`(Python 3.7+ 支援)
- [ ] F3.2.b 部分 unicode 字符 ASCII 簡化避免 log 亂碼:`→` → `->` / `≥` → `>=` / `≤` → `<=` / `⚠️` → `[WARN]` / `🚨` → `[ALERT]`

### F3.3 驗證

- [ ] F3.3.a 改完 runner dry-run(不需實際 hit backend,只 import + main 開首 print 確保唔 crash)
- [ ] F3.3.b ruff PASS 所有 5 個 modified files

### F3.4 commit

- [ ] F3.4.a commit `fix(tooling): W36 F3 PC-W35-1 runner cp1252 print encoding — ASCII fallback + sys.stdout.reconfigure utf-8`

## F4 — 收尾 + 跨文件同步 + commit + push

### A. 跨文件同步 per CLAUDE.md §10 R3 + R5 + R6

- [ ] plan.md frontmatter `status: active → closed`(F4 commit time)
- [ ] checklist.md cross-cutting tick + N/A reason(本文件)
- [ ] progress.md retro 7 段(What Worked + What Didn't / Surprises + Carry-overs + ADR Triggers + Phase Gate Result + W37+ Priority Queue Locked + Actual vs Planned Effort)
- [ ] session-start.md §10 W36 row `🟡 active` → `✅ closed`(F4 commit time)
- [ ] 🚧 RISK_REGISTER NEW R 候選 — DEFERRED W37+(operational debt cleanup 預期無新 risk material)
- [ ] ADR README — 無 NEW ADR(F1+F2+F3 全部 non-architectural per plan §1 + §4 R5)

### B. W37+ priority queue 評估

- [ ] B.1 W37+ 候選 promotion per F2 path 選擇 + F1/F3 outcome
- [ ] B.2 (j') section_path prefix filter 保留 MEDIUM
- [ ] B.3 PC-W33-1 + PC-W32-1/2 保留低優先級
- [ ] B.4 W35 DEMOTED LOW 候選 仍 LOW
- [ ] B.5 長期 carry-over(c)(e)(f)/BUG-026+027/W22 D8/W16 F1-F4 Track A IT cred

### C. commit + push

- [ ] F4 收尾 commit `docs(planning): W36 closeout — PC-W34-1 + PC-W34-2 + PC-W35-1 3 operational debts cleared`(若 F1+F2+F3 已分別 commit,則此純文檔收尾)
- [ ] push origin/main(per W33-W35 user-instruction precedent)

---

## Cross-Cutting

- [ ] All deliverables committed to git(F0.6 啟動 + F1.4 + F2.4 + F3.4 + F4 收尾)
- [ ] All OQ status changes 反映於 `docs/decision-form.md` — 預期無 OQ 變動
- [ ] All architectural-adjacent decisions documented as ADR — N/A 全部 3 個 candidates non-architectural per plan §1 + §4 R5
- [ ] `progress.md` retro section 寫好 — 7 段 per closeout commit
- [ ] `progress.md` frontmatter status flipped to `closed` per outcome
- [ ] Phase W37+ kickoff trigger 標記於 retro — 候選 list update per F2 path 選擇

---

**Lifecycle reminder**:本 checklist 隨 plan deliverables 衍生。新加 deliverable 必須先入 plan + changelog 然後再加 checklist item。
