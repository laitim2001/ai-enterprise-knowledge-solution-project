---
phase: W36-operational-debt-batch
plan_ref: ./plan.md
checklist_ref: ./checklist.md
status: active   # F0 啟動 2026-05-26
last_updated: 2026-05-26
---

# W36 — Progress

> 每日進度 + 決定 + commits + 收尾 retro。Append-only(per PROCESS.md v2.0)。

---

## Day 0(2026-05-26)— F0 啟動

### 行動

W35 收尾 PASS WITH G1-IMPROVED CAVEAT(`bf1bee4` + `fe2f30a` pushed origin/main 2026-05-26 same-day)→ user 明確 pick W36 啟動 = **batch operational debt cleanup**(W34 + W35 累積 3 個 HIGHEST 操作債候選)。

3 個 HIGHEST 候選打包:
1. **PC-W34-1** session-start protocol amend(Langfuse + Postgres endpoint health check pre-flight)— W35 F1.3 Docker Desktop 卡住事件 reinforced
2. **PC-W34-2** RAGAs judge 穩健性(gpt-5.4-mini → gpt-5.5 / JSON 解析穩健 / 排除複雜查詢)— W35 F1.4 Option B + Option C 兩個 eval 仍見 answer_relevancy 0.6X borderline judge artifacts
3. **PC-W35-1** F2 runner cp1252 print encoding bug — W35 F2 runner crash event trigger,5 個 runner files 中招 unicode

### R6 Day 0 recursive grep 驗證(per CLAUDE.md §10 R6)

3 個 catches 喺 F1+ 開始之前 surface:

**Catch (1) PC-W34-1**:`docs/12-ai-assistant/01-prompts/01-session-start.md` §10.3 6 步啟動 protocol 已存在(每 session 必執行),但**步驟 5 缺**「Langfuse `/api/public/health` 200 + Postgres `SELECT 1` ready_for_query 握手」endpoint 級別驗證 — 目前只有 `git status --short` + `git log --oneline -5`(working tree state)+ 1-4 步 docs 讀取。F1 範疇 = amend §10.3 加入 step 5b(或 6c)pre-flight endpoint health check。

**Catch (2) PC-W34-2**:`backend/eval/ragas_evaluator.py:96-97` 顯示 `settings.azure_openai_deployment_llm_judge` 為 judge LLM deployment 來源;`backend/eval/orchestrator.py:130` `judge_deployment` parameter 從 settings 提取。F2.1 audit 需查 `backend/storage/settings.py` default + `.env` 實際值,再決定 path:
- **Path (a)** judge LLM 升級 gpt-5.4-mini → gpt-5.5(cost 上升 + robustness 預期改善)
- **Path (b)** JSON 解析穩健化 catch InstructorRetryException + fallback parser
- **Path (c)** `eval-set-v0-w25-supplement.yaml` 加 metadata 過濾複雜查詢(Q-W25-I06/I07 multi-step queries judge 不兼容)

3 個 path ROI 取捨需 F2.1.d surface 至 chat user pick。

**Catch (3) PC-W35-1**:5 個 runner files 中招 unicode print,字符範圍:`→`(U+2192)/ `≥`(U+2265)/ `≤`(U+2264)/ `⚠️`(emoji)/ `🚨`(emoji)。具體位置:

| File | Line | Char |
|---|---|---|
| `backend/w34-f1-ragas-runner.py` | 75 / 95 / 97 | `→` / `⚠️` / `🚨` |
| `backend/w33-f2-runner.py` | 80 / 82 / 89 | `≥` |
| `backend/w34-f2-runner.py` | 100 / 101 | `→` |
| `backend/w35-f2-runner.py` | 15 / 16 / 110 | `≤` / `→` |

F3 修正策略預設 = **(iii) 兩者結合**(per Karpathy §1.3 surgical + future-proof):runner 開首加 `import sys; sys.stdout.reconfigure(encoding="utf-8")` + 部分字符 ASCII 簡化避免 log 亂碼。

### W26-W35 baseline 參考

| Baseline | 用途 |
|---|---|
| **W35 production state** | Rule 8 Option C wording shipped per `bf1bee4`;`prompt_builder.py:30` Option C verbatim,`test_prompt_builder_dispatch.py:207-228` Option C assertions;W36 範疇外 — 純 production preserve |
| **W35 F1.4 raw JSON** | `backend/w35-f1-option-b-raw.json` + `w35-f1-option-c-raw.json` — F2.1.c failed_queries judge artifact 樣本來源 |
| **W34 session-start.md §10.3** | F1 amend 對象 — 現況 6 步啟動 protocol |
| **W17 F3 RAGAs integration** | F2 範疇 — `make_ragas_evaluator(settings)` + `orchestrator.build_ragas_samples` 已 wired,production-ready when Azure key + judge LLM available |

### 各 F-phase pre-implementation surface

| F-phase | 工時估算 | 預期 surface user decision? |
|---|---|---|
| F1 PC-W34-1 | ~30min(純文檔)| 無 — 直接 amend |
| F2 PC-W34-2 | ~2-3h | **F2.1.d 之後 surface user pick path A/B/C** ⭐ |
| F3 PC-W35-1 | ~30min | 無 — 直接修正,預設策略 (iii) 兩者結合 |
| F4 收尾 | ~1h | 無 — 跨文件同步 + commit + push |

### Self-verification checklist(per CLAUDE.md §12)

- [x] 對應 spec section:F1 = session-start.md §10.3 protocol(non-spec procedural)/ F2 = architecture.md §3.2 RAGAs eval framework(judge LLM 是 vendor table H2 lock 內 OpenAI deployment,W36 範疇可能涉及 deployment 切換,但 vendor 不變即非 H2 violation)/ F3 = tooling 屬 C06+C07 但不屬 spec(屬 dev/ops surface)
- [x] H1-H7 不違反 — F1/F2/F3 全部 non-architectural(無 component schema / vendor / storage / 8-view philosophy / Tier 2 / security / design fidelity 影響)
- [x] §1 Karpathy think-before-coding — R6 3 catches surface upfront + F2 3 path 取捨 explicit surface before lock
- [x] N/A frontend fidelity check
- [x] 預期測試:F2 path 視乎(unit test / config test / yaml schema test);F3 ruff PASS
- [x] N/A 本 entry 無 code change
- [x] commit message follow Conventional Commits — `docs(planning): kickoff W36-...`
- [x] N/A architectural-adjacent → ADR
- [x] N/A Dify reference
- [x] OQ status check — 預期無 OQ resolved(operational debt phase)
- [x] Phase checklist tick'd — F0.1-F0.4 done + F0.5 in progress

### Commits

(F0.6 commit pending — combined kickoff plan + checklist + progress + R6 3 catches)

### Carry-overs / Blockers

- F0.5 progress.md Day 0 entry(本文件)— done
- F0.6 啟動 commit — pending
- F0.7 session-start.md §10 W36 row append — pending(commit hash post F0.6)
- D1 trigger:F1 純文檔 amend + F2.1 audit + F2.1.d user pick path A/B/C + F3 runner 修正 + F4 收尾

---

## Day 1(TBD)— F1 + F2 + F3 + F4 收尾

(pending F0.6 commit + D1 sequence)
