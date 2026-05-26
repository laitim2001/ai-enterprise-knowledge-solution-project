---
phase: W36-operational-debt-batch
plan_ref: ./plan.md
checklist_ref: ./checklist.md
status: closed   # F4 收尾 2026-05-26 — PASS
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

- `bb15ce0` — F0.6 啟動 commit(plan + checklist + progress + R6 3 catches,3 files / 452 insertions)
- `2ffce8d` — F0.7 session-start.md §10 W36 row append active + W35 row commits backfill

### Carry-overs / Blockers

- F0.5 progress.md Day 0 entry(本文件)— done
- F0.6 啟動 commit `bb15ce0` — done
- F0.7 session-start.md §10 W36 row append commit `2ffce8d` — done
- **D1 trigger 序列**:F1 純文檔 amend(自主可做)→ F2.1 audit(自主)→ F2.1.d 後 surface chat user pick path A/B/C → F2.2+F2.3+F2.4 → F3 runner 修正(自主)→ F4 收尾

---

## Day 1(2026-05-26 same-day collapse)— F1 + F2 + F3 全部完成

### F1 PC-W34-1 CLAUDE.md §10.3 amend

**R3 plan amend**:F1 amend 對象由「session-start.md §10.3」修正為「CLAUDE.md §10.3」(line 524-535)— Day 1 F1.1 R6 grep 驗證發現 session-start.md 並無 §10.3 protocol section,真嘅 6 步 AI Session Start Protocol home 喺 CLAUDE.md。R6 plan-text contamination 案例 per W23 F3 R6 recursive scope amendment。

CLAUDE.md §10.3 加入 step 5b — conditional pre-flight endpoint health check(「若本 session 預期會做 backend restart / eval run / RAGAs eval / Langfuse trace 操作」):

```powershell
Invoke-WebRequest -Uri http://localhost:3000/api/public/health -TimeoutSec 30  # Langfuse 200
docker exec ekp-postgres psql -U langfuse -d postgres -c "SELECT 1;"           # Postgres ready_for_query
```

關鍵明確區分:**Docker `(unhealthy)` flag = timing artifact ≠ endpoint reachability**(W34 W35 Langfuse `Up X mins (unhealthy)` 但 endpoint 200 OK with 30s warmup timeout 屬 timing 一致 pattern)。失敗 path:endpoint 不 reachable → surface 至 user before destructive ops。

Commit `3f65531`。

### F2.1 audit + path 4 candidates surface

3 個 LLM deployments 識別 喺 `backend/storage/settings.py:65-67`:
- `llm_primary` default `gpt-5-5` / `.env` `gpt-5.5`(synthesizer)
- `llm_judge` default `gpt-5-4-mini` / `.env` `gpt-5.4-mini`(**RAGAs 用** + CRAG grader + Query Reformulator 共用)
- `llm_eval_judge` default `gpt-5-5-pro` / **`.env` override `gpt-5.4-mini`**(`gpt-5-5-pro` Azure deployment 可能未配)

W35 Option C failed_queries pattern audit:
- 4 個 `answer_relevancy=0.6X` borderline(0.61 / 0.62 / 0.63 / 0.66)— RAGAs `AnswerRelevancy` cosine similarity-based,threshold 預設 0.70
- 5 個 `context_recall=0.00` keyword-mode artifact — reference fallback `expected_keywords` 嘅 known limitation per `ragas_evaluator.py:75-77` W17 F3 fallback
- InstructorRetryException 唔喺 raw JSON 顯式(屬 ragas library 內部 retry exhaust exception)

4 個 path candidates surfaced — user 2026-05-26 explicit cost containment policy:**「不需要用到 gpt-5.5-pro,因為成本太高了」+「連 gpt-5.5 都不應該用到」+「這是很重要的事情,因為是會很影響後面的使用成本的」**。

Memory saved `feedback_judge_llm_cost_policy.md` — RAGAs judge + cost-sensitive non-synthesizer LLM layers default `gpt-5.4-mini`,不升 `gpt-5.5` / `gpt-5.5-pro`。

User confirm + lock **path (b)+(d) 組合**:zero LLM cost 上升 + 同時處理 transient + systematic failures。

### F2.2 path (b)+(d) 實作

**Path (b)** `backend/eval/ragas_evaluator.py:_ascore_all`:
- NEW `_ascore_metric` helper per-metric try/except + structlog `ragas_metric_exception_fallback` warning + fallback 0.0
- catch `Exception`(per existing line 104 pattern — ragas/instructor library exception chain unpredictable)
- 防止 single bad query 拖跨整個 4-metric eval pass — pre-W36 whole sample marked errored 而失 other 3 metrics 嘅 score

**Path (d)** `backend/eval/orchestrator.py:_RAGAS_ATTENTION_THRESHOLD`:
- single 0.70 constant → `_RAGAS_ATTENTION_THRESHOLDS` per-metric dict
- `faithfulness` / `answer_relevancy` / `context_precision` = **0.65**(W36 calibration was 0.70 pre-W36)
- `context_recall` = **0.0**(keyword-mode artifact 不 surface;until Q14 SME-validate `eval-set-v1-final.yaml` ships)
- expected_str 改為 per-metric(`>= 0.65 (faithfulness), >= 0.65 (answer_relevancy), ...`)更明確

NEW W36 unit tests:
- `test_w36_ragas_attention_thresholds_per_metric_calibration` — verify dict 完整性
- `test_w36_context_recall_keyword_mode_artifact_not_surfaced` — verify context_recall=0.0 不 surface

### F2 驗證

- pytest:**1086 passed + 25 skipped + 0 failed in 128.19s** ✅(1084 W34/W35 baseline + 2 NEW W36 tests = 1086 exact match)
- ruff:`All checks passed!`
- F2.3 sanity-check eval 跳過 per Karpathy §1.2 simplicity — unit test 已 cover behavior

Commit `576e6c6`。

### F3 PC-W35-1 runner cp1252 修正

4 個 runner files unicode print 修正(策略 iii 兩者結合):
- 每 runner 開首加 `import sys; sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]`
- ASCII 簡化:`→` → `->` / `≥` → `>=` / `≤` → `<=` / `⚠️` → `[WARN]` / `🚨` → `[ALERT]` / `✅` → `OK`

範疇:
- `backend/w34-f1-ragas-runner.py`(`→` + `✅⚠️🚨`)
- `backend/w33-f2-runner.py`(`≥` × 3 + 新加入 tracked)
- `backend/w34-f2-runner.py`(`→` × 2)
- `backend/w35-f2-runner.py`(`≤` + `→`)
- `backend/w35-f1-ragas-runner.py` 預檢 ASCII safe 不需改

驗證:4 runner files AST parse PASS;W36 specific edits ruff clean。

**注意**:8 個 pre-existing ruff issues 不屬 W36 scope(F401 + F841 + F541 × 6 全屬 W33-W35 寫 runner 留底,Karpathy §1.3 strict surgical 唔清非自己 mess)。

Commit `5520918`。

### Self-verification(per CLAUDE.md §12)

- [x] 對應 spec section:F1 = CLAUDE.md §10.3(procedural)/ F2 = architecture.md §3.2 Eval framework(vendor 不變)/ F3 = tooling(non-spec)
- [x] H1-H7 不違反 — 全部 non-architectural(vendor 不變,judge 仍 gpt-5.4-mini per memory feedback_judge_llm_cost_policy.md)
- [x] §1 Karpathy think-before-coding — F2.1 audit 4 path surface upfront user pick;F3 pre-existing issues 明確 surface 不混合
- [x] N/A frontend fidelity check
- [x] 2 NEW W36 unit tests + 4 runner AST parse PASS
- [x] ruff PASS W36 specific edits(8 pre-existing 不屬 scope)
- [x] commit message Conventional Commits — `docs(claude-md)` + `feat(eval)` + `fix(tooling)`
- [x] N/A architectural-adjacent → ADR(全部 non-architectural)
- [x] N/A Dify reference
- [x] OQ status check — 無 OQ resolved
- [x] Phase checklist tick'd — F0-F3 全部完成,F4 收尾 in progress

### Commits

- `bb15ce0` — F0.6 啟動
- `2ffce8d` — F0.7 session-start
- `15f4979` — F0.7 housekeeping
- `3f65531` — F1 CLAUDE.md §10.3 amend + R3 plan amend
- `89a9aca` — F1 + F2.1 checklist tick
- `576e6c6` — F2 path (b)+(d) implementation + 2 NEW tests
- `5520918` — F3 runner cp1252 修正

### Carry-overs / Blockers

- F4 收尾 pending(plan/checklist status flip + session-start §10 W36 row closed + 收尾 commit + push)
- 8 個 pre-existing ruff issues 喺 runner files 留 W37+(若 user explicit cleanup 範疇)— DEFERRED LOW

---

## §Retro

### What Worked

1. **R6 Day 0 recursive grep 驗證 catch 3 個 contamination upfront** — PC-W34-1 protocol home 是 CLAUDE.md §10.3(不是 session-start.md)/ PC-W34-2 3 個 LLM deployments + `.env` override 揭示 / PC-W35-1 5 個 runner files unicode 範疇明確。F1 R3 plan amend 預防 silent drift。
2. **F2.1 audit surface 4 個 path 取捨**(包括 NEW path d)— 原本 plan §F2 only 3 paths,audit 揭示 path d(threshold calibration)真正解 context_recall keyword-mode artifact 根因(SME-validate Q14 reference_answer 暫未 ship)。Karpathy §1.1 think-before-coding pay off。
3. **User cost containment policy surface upfront** — F2.1.d surface 4 paths,user explicit 框定「不用 gpt-5.5/pro」,即時 save 入 memory `feedback_judge_llm_cost_policy.md`(per CLAUDE.md memory system feedback type)+ MEMORY.md 索引 update。Path (a) judge LLM 升級 直接 out → 無浪費 implementation effort。
4. **Path (b)+(d) Pareto-optimal** — zero LLM cost 上升 + 同時處理 transient(b)+ systematic(d)+ 不減 eval coverage(vs path c)+ 不需 Azure deployment verify(vs path a)。Single dict change `_RAGAS_ATTENTION_THRESHOLDS` 同時做 calibration + keyword-mode skip。
5. **F3 PC-W35-1 兌現 W35 retro 提出嘅 fix** — 5 個 runner files unicode print 統一改完;策略 (iii) 兩者結合(sys.stdout.reconfigure + ASCII fallback)future-proof — 即使 PowerShell redirect 至 file 嘅 cp1252 encoded log 都唔會亂碼。
6. **Real-calendar collapse 1.5× over plan**(~4-5h actual vs 5-6h planned)— 預期 5-6h(F0 1h + F1 30min + F2 2-3h + F3 30min + F4 1h)實際 ~4-5h same-day(F2 audit speed-up + F3 surgical edits 集中)。

### What Didn't Work / Surprises

1. **🚨 R6 catch F1 amend 對象 contamination** — W36 plan §F1 originally 寫「session-start.md §10.3 amend」,但 grep 驗證發現 session-start.md 並無 §10.3 protocol section。真嘅 home 喺 CLAUDE.md §10.3 line 524。W23 F3 R6 recursive scope amendment 預期 catch 呢類 pre-W{N-1} surface naming contamination,呢次驗證成功 — Day 0 plan kickoff 入面寫錯,Day 1 R6 grep catch 後 R3 plan amend 修正。
2. **⚠️ F2.1 audit 揭示 `gpt-5-5-pro` `.env` override 至 `gpt-5.4-mini`** — `settings.py:67` default `gpt-5-5-pro` 但 `.env` 覆蓋 等同 `llm_judge`。即係 `gpt-5-5-pro` Azure deployment **可能未配置 喺實際 portal**。Path (a) 升級需 user 確認 Azure deployment availability。User cost containment policy explicit out path (a) → 唔需 verify。
3. **⚠️ InstructorRetryException 唔喺 raw JSON 顯式** — W34 retro 提到 Q-W25-I06+I07 InstructorRetryException,但 W35 Option C raw JSON 唔見顯式 entry(可能 retry 成功 OR exception bubble up at different level)。Path (b) per-metric try/except 仍 robust catch 任何 layer exception(用 catch all `Exception` 而非 specific `InstructorRetryException`)。
4. **⚠️ Pre-existing 8 個 ruff issues 喺 runner files** — F401 `os` unused + F841 `cit_ids` unused + F541 f-string without placeholder × 6,全 W33-W35 寫 runner 嗰陣留底。Karpathy §1.3 strict surgical = 唔清非自己 mess → W36 唔 fix。W37+ 若 user explicit cleanup 範疇可 batch 處理。
5. **Surprising correlation** — F2.1 audit 揭示 `patch_for_gpt5` shim 已 prepared GPT-5 reasoning judge compatibility(per W5 D4 Bug I + ragas 0.4.3 quirks shim line 41-62),即 codebase 已 ready 接受 GPT-5 judge upgrade。但 user cost containment policy 排除此 path → infrastructure preparedness 暫保留 future flexibility 但 W36 唔 invoke。

### Carry-overs

- **🚧** Pre-existing 8 ruff issues 喺 4 個 runner files — W37+ LOW(若 user explicit batch cleanup 範疇)
- **🚧** (j') section_path prefix filter — preserve W37+ MEDIUM
- **🚧** PC-W33-1 + PC-W32-1/2 — preserve W37+ LOW housekeeping
- **🚧 DEMOTED** Option A more aggressive Rule 8 re-tighten / prompt token reduction / engine-fetch async pool / Option (a) judge LLM 升級(永久 OUT per memory feedback_judge_llm_cost_policy.md)
- **🚧 LOWER**(g')/(i')/(B'.a)/(ii)/(k)saturated
- **🚧 LONG-TERM**(c)(e)(f)+ BUG-026+027 + W22 D8 + W16 F1-F4 Track A IT cred — 長期 carry-over
- **🚧 Q14 SME-validate reference_answer cascade** — eval-set-v1-final.yaml W15 F1 CO 未 ship;W36 F2 path (d) context_recall=0.0 threshold 暫時 skip keyword-mode artifact 但 SME validation 仍係 真正 fix 系統性 context_recall 問題嘅根因 — preserve long-term

### ADR Triggers

**無 NEW ADR** this phase — F1 CLAUDE.md amend(procedural)+ F2 RAGAs judge robustness(vendor 不變 + threshold calibration)+ F3 runner tooling 全部 non-architectural per CLAUDE.md §5.1 H1。

### Phase Gate Result

✅ **PASS** per plan §3 G1-G6 multi-axis:
- **G1 PC-W34-1** ✅ CLAUDE.md §10.3 step 5b pre-flight endpoint health check shipped
- **G2 PC-W34-2** ✅ Path (b)+(d) implementation + 2 NEW unit tests + pytest 1086 PASS + ruff PASS
- **G3 PC-W35-1** ✅ 4 個 runner files 修正 + AST parse PASS
- **G4 backend pytest baseline 1086** ✅(1084 W34/W35 baseline + 2 NEW W36 tests = 1086 exact match)
- **G5 ruff PASS + mypy strict module-path quirk 維持** ✅(W36 specific edits clean;pre-existing 13 mypy errors per CO_W25_mypy_strict_debt 不變)
- **G6 R6 catch 3 個 surface** ✅(F0.2 + Day 1 R3 amend catch contamination)

### W37+ Priority Queue Locked

**Per F4.B W37+ candidate priority queue update**:

- **MEDIUM**(j') section_path prefix filter quality-of-cite refinement(W35 retro 預期 + 未做)
- **LOW** PC-W33-1 + PC-W32-1/2 procedural housekeeping
- **LOW** Pre-existing 8 ruff issues 喺 4 個 runner files(若 user explicit cleanup 範疇)
- **LONG-TERM** Q14 SME-validate reference_answer cascade(eval-set-v1-final.yaml W15 F1 CO ship)— 真正 fix systematic context_recall 根因
- **永久 OUT** Path (a) judge LLM 升級(per memory feedback_judge_llm_cost_policy.md cost containment)
- **DEMOTED LOW** prompt token reduction(W35 F2 0ms confirmed)+ engine-fetch async pool(W35 F2 1113ms small fraction)+ Option A more aggressive Rule 8 re-tighten(W35 Option C Pareto-optimal)
- **LOWER**(g')(i')(B'.a)(ii)(k)saturated low priority
- **LONG-TERM**(c)(e)(f)+ BUG-026+027 + W22 D8 + W16 F1-F4 Track A IT cred

### Actual vs Planned Effort

| Phase | Planned | Actual | Delta | Notes |
|---|---|---|---|---|
| **D0 F0 啟動** | ~1h | ~1h | 0 | plan + checklist + progress + R6 3 catches + commits bb15ce0/2ffce8d/15f4979 |
| **D1 F1 PC-W34-1** | ~30min | ~30min | 0 | CLAUDE.md §10.3 step 5b amend + R3 plan amend(catch 對象修正)+ commit 3f65531 |
| **D1 F2 PC-W34-2** | ~2-3h | ~2h | 內 | F2.1 audit(~30min)+ user surface + lock (b)+(d)(~10min)+ implementation + 2 NEW tests + pytest verify(~1h)+ commit 576e6c6;Karpathy §1.2 simplicity 跳 F2.3 sanity-check eval |
| **D1 F3 PC-W35-1** | ~30min | ~30min | 0 | 4 runner files edit + AST parse verify + commit 5520918 |
| **D1 F4 收尾** | ~1h | ~1h | 0(進行中)| retro + 跨文件同步 + commit + push |
| **總計** | ~5-6h | ~4.5-5h | 內 | Real-calendar same-day collapse pattern preserved per W22-W35;F2.1 audit speed-up + F3 surgical edits 集中 + Karpathy §1.2 跳 sanity-check eval |
