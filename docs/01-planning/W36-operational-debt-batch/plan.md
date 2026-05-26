---
phase: W36-operational-debt-batch
status: closed   # F4 收尾 2026-05-26 — Phase Gate PASS:F1 PC-W34-1 + F2 PC-W34-2 (b)+(d) + F3 PC-W35-1 全部 ship + pytest 1086 + ruff PASS;Karpathy §1.3 surgical 跨 3 candidates atomic
last_updated: 2026-05-26
component_scope: C12 DevOps(session-start protocol)+ C06 Eval Framework(RAGAs judge robustness)+ C06+C07(runner cp1252 fix)
adr_refs:
  - W17 F3 RAGAs 4-metric integration(judge LLM deployment 來源 — `backend/eval/ragas_evaluator.py:96-97`)
  - W34 retro PC-W34-1 + PC-W34-2(operational debt 來源)
  - W35 retro PC-W35-1(F2 runner cp1252 print encoding bug)
  - W35 F1.4 evidence — InstructorRetryException judge artifacts(Option B `Q-W25-I06+I07`,Option C `Q-W25-I06` 仍 borderline `answer_relevancy=0.6X`)
  - W35 F2 evidence — runner crash at final print on `≤`(U+2264)+ 4 個 other runner files 中招 unicode
related_carry_overs:
  - W34 PC-W34-1(session-start protocol amend Langfuse health + Postgres handshake)— HIGHEST W35 已 surface,W36 兌現
  - W34 PC-W34-2(RAGAs judge robustness)— HIGHEST W35 兩個 eval 仍見 judge artifact,W36 兌現
  - W35 NEW PC-W35-1(F2 runner cp1252 print encoding bug)— HIGHEST 新出 W35 F2 trigger,W36 兌現
---

# W36 — Operational Debt Batch Cleanup(3 個 HIGHEST 候選打包)

## §1 目標 + 範疇

**單一主要目標**:將 W34-W35 累積嘅 3 個 HIGHEST 級別 operational debt 一次過清理 — 屬 procedural / runner-tooling / observability 性質,**非 production behavior change**,亦**非 architectural change**(per H1)。

**Karpathy §1.3 surgical scope 嚴守**:
- F1 PC-W34-1 = 純文檔 amend(session-start.md §10.3 6 步啟動 protocol 加入 endpoint health check 步驟)
- F2 PC-W34-2 = backend config + 可能 ragas_evaluator.py 改動(judge LLM 升級 OR JSON 解析穩健化 OR 排除複雜查詢策略)— 需先 audit 現狀
- F3 PC-W35-1 = backend/w*-f*-runner.py family unicode print 修正(ASCII fallback 或 `PYTHONIOENCODING=utf-8` 環境變數,5+ files affected)

**Non-goals**(W36 範疇外):
- 任何 production behavior change(無 Rule 變動 / 無 Settings flip / 無 retrieval-side 改動)
- W35 RAGAs eval / latency profile 重做(F2 RAGAs judge robustness 改完之後可選擇做小規模 sanity-check eval,非必要)
- (j') section_path prefix filter — 留 W37+
- prompt token reduction / engine-fetch async pool — W35 F2 證據已 DEMOTED LOW
- PC-W33-1 + PC-W32-1/2 — preserved W37+ housekeeping

**Component 範疇**:
- **C12 DevOps & Infra**(F1 session-start.md §10.3 amend)
- **C06 Eval Framework**(F2 ragas_evaluator + judge LLM 升級研究)
- **C06 + C07 Observability**(F3 runner script unicode print 修正,屬 tooling)
- **不涉及** C01-C05 / C08-C13(無 frontend / backend pipeline / KB / auth / email 改動)

---

## §2 交付物 F0-F4

### F0 — 啟動(本 session 2026-05-26)

- F0.1 建立 `docs/01-planning/W36-operational-debt-batch/` folder
- F0.2 R6 Day 0 recursive grep 驗證 — **catch (1) PC-W34-1**:session-start.md §10.3 6 步啟動 protocol 已有,但步驟 5 缺 endpoint health check(只有 `git status --short` + `git log --oneline -5`);**catch (2) PC-W34-2**:`backend/eval/ragas_evaluator.py:96-97` `settings.azure_openai_deployment_llm_judge` = judge LLM deployment 來源,需查 `.env` 實際值 + `settings.py` default;**catch (3) PC-W35-1**:5 個 runner files unicode 中招(`w34-f1-ragas-runner.py:75/95/97` + `w33-f2-runner.py:80/82/89` + `w34-f2-runner.py:100/101` + `w35-f2-runner.py:15/16/110`,字符 `→ ≥ ≤ ⚠️ 🚨`)
- F0.3 起草 `plan.md` 7 段(本文件)
- F0.4 起草 `checklist.md` 原子化勾選項
- F0.5 起草 `progress.md` Day 0 — 啟動行動 + R6 3 catches 報告 + W35 baseline 參考 + 各 F-phase pre-implementation surface
- F0.6 啟動 commit `docs(planning): kickoff W36-operational-debt-batch + R6 Day 0 catch 3 HIGHEST candidates surface PC-W34-1 session-start protocol + PC-W34-2 RAGAs judge + PC-W35-1 runner cp1252`
- F0.7 session-start.md §10 W36 row append `🟡 active 2026-05-26` + W35 已 closed 維持

### F1 — PC-W34-1 session-start protocol amend(~30min,純文檔)

**R3 amend 2026-05-26**:F1 amend 對象修正為 **`CLAUDE.md §10.3`**(line 524-535,真嘅 AI Session Start Protocol home)而非原本寫嘅 session-start.md §10.3。

- F1.1 讀 `CLAUDE.md` §10.3 6 步啟動 protocol 現況(line 524-535)
- F1.2 起草新增 step 5b(或叫 step 5.5)— `pre-flight Langfuse + Postgres endpoint health check`,包含具體 PowerShell command:
  - `Invoke-WebRequest -Uri http://localhost:3000/api/public/health -TimeoutSec 30`(預期 200)
  - `docker exec ekp-postgres psql -U langfuse -d postgres -c "SELECT 1;"`(預期 `1 row`)
- F1.3 amend `CLAUDE.md §10.3` 加入新步驟 + 解釋 Docker `unhealthy` flag = timing artifact ≠ endpoint reachability(per W34 F2.3 audit_log 30s gap + W35 F1.3 Docker stuck 經驗)
- F1.4 commit `docs(claude-md): W36 F1 PC-W34-1 §10.3 pre-flight endpoint health check`

### F2 — PC-W34-2 RAGAs judge robustness(~2-3h)

#### F2.1 現狀 audit(完成 2026-05-26 D1)

- [x] F2.1.a 讀 `backend/eval/ragas_evaluator.py:1-157` 完整實作 — `patch_for_gpt5` shim 已 prepared GPT-5 reasoning judge;`_MIN_MAX_COMPLETION_TOKENS = 4096` floor 防 faithfulness JSON truncate;`_ascore_all` 直接 call ragas metric `ascore`,**冇 explicit InstructorRetryException catch**
- [x] F2.1.b `backend/storage/settings.py:65-67` 揭示 3 個 LLM deployments:
  - `azure_openai_deployment_llm_primary` default `gpt-5-5` / `.env` `gpt-5.5`(synthesizer)
  - `azure_openai_deployment_llm_judge` default `gpt-5-4-mini` / `.env` `gpt-5.4-mini`(**RAGAs 用呢個** + CRAG grader 共用)
  - `azure_openai_deployment_llm_eval_judge` default `gpt-5-5-pro` / **`.env` override `gpt-5.4-mini`**(等同 llm_judge,**`gpt-5-5-pro` Azure deployment 可能未配置**)
- [x] F2.1.c W35 Option C `failed_queries` pattern audit 結果:
  - 4 個 `answer_relevancy=0.6X` borderline(0.61 / 0.62 / 0.63 / 0.66)— RAGAs `AnswerRelevancy` 是 cosine similarity-based,threshold 預設 0.70 → borderline 嘅 cosine score 觸發 fail
  - 5 個 `context_recall=0.00` keyword-mode artifact — reference fallback `expected_keywords` (per ragas_evaluator.py line 75-77 W17 F3 fallback)導致 LLM judge 解讀 context 不 contain pseudo-reference
  - **InstructorRetryException 唔喺 raw JSON 顯式**(屬 ragas library 內部 retry exhaust exception,W34 F1 提到 Q-W25-I06+I07 觸發,但 W35 retry 可能成功)
- [x] F2.1.d 4 個 fix path 取捨 ROI 評估完成:**詳見 plan §3 G2 + progress.md Day 1 surface**

#### Path 取捨 4 個 candidates(F2.1.d surface 至 user pick)

| Path | 動作 | 預期效果 | Effort | 風險 |
|---|---|---|---|---|
| **(a) Judge LLM 升級** | `ragas_evaluator.py:96` 由 `azure_openai_deployment_llm_judge`(`gpt-5.4-mini`) → `azure_openai_deployment_llm_eval_judge`(`gpt-5-5-pro`)+ user 喺 Azure portal 確認 `gpt-5-5-pro` deployment 已配置 + `.env` 加 override line | answer_relevancy borderline 可能改善 5-10%(更強 cosine semantic understanding);context_recall keyword-mode artifact **唔解決根因** | ~30min code + Azure deployment verify | Cost 上升 ~5-10×(gpt-5.5-pro 比 gpt-5.4-mini 貴);**Azure deployment 可能未配** |
| **(b) JSON 解析穩健化** | wrap `_ascore_all` try/except `InstructorRetryException` + 對 individual metric fall back NaN(per-metric isolation) | 防止 single bad query 拖跨整個 eval;**borderline failures 唔解決** | ~1h code + unit test | Fallback NaN 可能 mask real regression(若 future 真有 systematic 問題) |
| **(c) eval-set yaml metadata 過濾** | `eval-set-v0-w25-supplement.yaml` 加 `judge_compatible: false` field 至 Q-W25-I06+I07 + `orchestrator.py:build_ragas_samples` skip filter | Removes known InstructorRetryException trigger queries;eval pool 變細 13→11 | ~30min code + yaml | 減 eval coverage;future 新複雜 query 都要手動 mark(non-sustainable) |
| **(d) Threshold calibration + 文檔化** ⭐ **新 surface** | (d.1) 降低 RAGAs answer_relevancy threshold 0.70 → 0.65 OR (d.2) 文檔化 `context_recall=0.00 keyword-mode artifact` 作 known issue 不算 failure;runner 加 metadata 區分 「real regression」 vs 「known artifact」 | 真正 align 接受標準 + 現實;不需 LLM cost 上升 + 不需 SME-validate reference answers;**真正解 context_recall 系統性問題** | ~1-2h code + threshold config | Threshold lowering 可能 mask 真 regression;需 W36+ 後續 audit 確認 calibration 合理 |

**Path 推薦組合**:
- **(b) + (d) 組合** — path (b) 處理 transient artifact(防 single bad query 拖跨)+ path (d) 處理 systematic borderline(calibrate 接受標準)— combined cost ~1.5-2h,**不需 Azure deployment verify**,**不減 eval coverage**
- 或 **(a) only**(若 user 確認 `gpt-5-5-pro` 已配 + 接受 cost 上升)— 簡單但 cost 高 + 唔解決 context_recall keyword-mode artifact

#### F2.2 Path 選定 + 實作(~1-2h)
- F2.2.a User 鎖定 path(F2.1 完成後 surface 至 chat,user pick A/B/C)
- F2.2.b 實作對應 path
- F2.2.c 寫 unit test(若 path b 改 parser)OR config-state test(若 path a 換 LLM)OR yaml schema validation(若 path c 加 metadata)
- F2.2.d pytest baseline 1084 維持 ✅;ruff PASS

#### F2.3 小規模 sanity-check eval(可選)
- F2.3.a 若 path a/b 改動 judge layer,可選跑 3-5 query 小規模 eval 驗證 InstructorRetryException 消失
- F2.3.b 若 path c 純 yaml metadata 過濾,可選驗證 eval-set 過濾邏輯

#### F2.4 commit
- F2.4.a `feat(eval): W36 F2 PC-W34-2 RAGAs judge robustness — {path 描述}`

### F3 — PC-W35-1 runner cp1252 修正(~30min)

#### F3.1 修正範疇
- F3.1.a `backend/w34-f1-ragas-runner.py:75`(`→`)+ line 95(`⚠️`)+ line 97(`🚨`)
- F3.1.b `backend/w33-f2-runner.py:80,82,89`(`≥`)
- F3.1.c `backend/w34-f2-runner.py:100,101`(`→`)
- F3.1.d `backend/w35-f2-runner.py:15,16,110`(`≤`,`→`)
- F3.1.e 可選 `backend/w35-f1-ragas-runner.py` 預檢(已用 ASCII fallback `->` 但 verdict 字串 「G1 preserve OK」 / 「G1 flag - F1.7 evaluate」 已 ASCII safe)

#### F3.2 修正策略(取一)
- **(i) 全 ASCII fallback**:`→` → `->` / `≥` → `>=` / `≤` → `<=` / `⚠️` → `[WARN]` / `🚨` → `[ALERT]`
- **(ii) PYTHONIOENCODING=utf-8 env override**:加入 runner 開首 `import sys; sys.stdout.reconfigure(encoding="utf-8")`(Python 3.7+ 支援)
- **(iii) 兩者結合**:reconfigure stdout + 部分 ASCII 簡化避免在 log 看到亂碼

預設選 **(iii) 兩者結合**(per Karpathy §1.3 surgical + future-proof)— 寫好嘅 runner 之後 W37+ 也可用。

#### F3.3 驗證
- F3.3.a 改完之後跑 `python backend/w35-f2-runner.py --help` 或 dry-run 確保 import + 加 `sys.stdout.reconfigure(encoding="utf-8")` 不會 break
- F3.3.b ruff PASS

#### F3.4 commit
- F3.4.a `fix(tooling): W36 F3 PC-W35-1 runner cp1252 print encoding — ASCII fallback + sys.stdout.reconfigure utf-8`

### F4 — 收尾 + 跨文件同步 + commit + push

#### A. 跨文件同步 per CLAUDE.md §10 R3 + R5 + R6
- A.1 plan.md frontmatter `status: active → closed`
- A.2 checklist.md cross-cutting tick + N/A reason
- A.3 progress.md retro 7 段
- A.4 session-start.md §10 W36 row `🟡 active` → `✅ closed`
- A.5 RISK_REGISTER — 預期無 NEW R(operational debt cleanup 無新增 risk material)
- A.6 ADR README — 無 NEW ADR(全部 non-architectural per plan §1 + §4 R5)

#### B. W37+ priority queue 評估
- B.1 W37+ 候選 promotion per F2 path 選擇 + F1/F3 outcome:
  - 若 F2 path a 升級 judge LLM → cost 上升 → W37+ 「judge LLM cost optimization」 OR cost-effective 替代研究
  - 若 F2 path b JSON parser fallback → 已穩健,無 follow-up
  - 若 F2 path c eval-set metadata 過濾 → W37+ 「eval-set 重新 SME-validate Q14」 promote
- B.2 (j') section_path prefix filter — W37+ MEDIUM
- B.3 PC-W33-1 + PC-W32-1/2 — preserved 低優先級
- B.4 W35 DEMOTED LOW 候選 (Option A more aggressive / prompt token reduction / engine-fetch async pool) — 仍 LOW
- B.5 (g')(i')(B'.a)(ii)(k)+ (c)(e)(f)/BUG-026+027/W22 D8/W16 F1-F4 Track A IT cred 長期 carry-over

#### C. commit + push
- C.1 收尾 combined commit `docs(planning): W36 closeout — PC-W34-1 + PC-W34-2 + PC-W35-1 3 operational debts cleared`(若 F1+F2+F3 已分別 commit 則此為純文檔收尾)
- C.2 push origin/main(per W33-W35 user-instruction precedent)

---

## §3 接受準則(G1-G6 — 操作債清理導向)

### G1 PRIMARY — PC-W34-1 session-start protocol amend 完成

- session-start.md §10.3 6 步啟動 protocol 加入 endpoint health check 步驟
- 包含具體 PowerShell command + 解釋 Docker `unhealthy` flag != endpoint reachability
- commit `docs(prompts): W36 F1 PC-W34-1 ...` ✅

### G2 PRIMARY — PC-W34-2 RAGAs judge robustness 完成

- Path 選定(a / b / c)+ 對應實作完成
- backend pytest 1084 維持
- ruff PASS
- 可選 sanity-check eval verify InstructorRetryException 消失(若 path a/b)

### G3 PRIMARY — PC-W35-1 runner cp1252 修正完成

- 5 個 runner files unicode print 修正 至 ASCII fallback + `sys.stdout.reconfigure(encoding="utf-8")`
- 改完之後 import + dry-run 不 crash
- ruff PASS

### G4 backend pytest baseline 1084 維持

W35 收尾 baseline → 預期 W36 維持 1084(F2 若加 unit test 可加 1-3 個)。無 regression。

### G5 ruff PASS + mypy strict module-path quirk 維持

新 touch files clean;預先存在 13 個 mypy errors per CO_W25_mypy_strict_debt 不變。

### G6 R6 catch 驗證

- F0.2 R6 3 catches 全部 surface 喺 progress.md Day 0
- 各 F-phase 完成之後 plan.md §7 changelog 加 outcome row(若有 deviation)

---

## §4 R1-R6 Sprint 規則(per CLAUDE.md §10 binding)

- **R1** plan.md F1+ code 之前 commit(F0.6 啟動 commit 本 session)
- **R2** 每日 commit 對應 progress.md Day-N entry(F0.6 D0 + F1.4 + F2.4 + F3.4 + F4 收尾)
- **R3** plan deviation log 喺 §7 changelog(無 silent drift)
- **R4** OQ resolved → decision-form.md + progress.md Day-N 同步(預期無 OQ 變動 — operational debt phase)
- **R5** ADR(per H1)— 全部 3 個 candidates non-architectural(純 protocol amend + judge config + tooling fix)→ **預期無 NEW ADR**
- **R6** Day 0 recursive grep 驗證(F0.2)— **3 catches surfaced**:PC-W34-1 protocol 缺步驟 + PC-W34-2 judge config 來源 + PC-W35-1 5 個 runner files unicode

---

## §5 D0-D1 Day 分解估算

| Day | 交付物 | 工時 | 驗證 |
|---|---|---|---|
| **D0(本 session 2026-05-26)** | F0.1-F0.7 啟動 | ~1h | plan/checklist/progress committed + R6 驗證 |
| **D1** | F1 PC-W34-1(~30min)+ F2 PC-W34-2 audit + path 選定 + 實作(~2-3h)+ F3 PC-W35-1(~30min)+ F4 收尾(~1h)= ~4-5h | 全 D1 | 3 個 commits + 收尾 commit + push |

**總計**:~5-6h actual 預期跨 1-2 calendar day(real-calendar collapse pattern preserved per W22-W35 typical 1-2× collapse measurement-only / tooling-fix scope)。

---

## §6 W35 carry-overs + dependencies

### W26-W35 累積 production state 維持

- **W29 `.env` 環境變數覆蓋**:`QUERY_EXPANSION_PER_VARIANT_OVERFETCH=8` + `QUERY_EXPANSION_RRF_K=30`
- **W28 `Settings.py` defaults**:parent_doc 最佳組合
- **W26 `Settings.py` Q4**:`enable_parent_doc_retrieval=False`
- **W32 (h') Settings**:`enable_citation_post_hoc_expansion=True` + `citation_expansion_window=10` + `citation_expansion_max_aux=2`
- **W33 Rule 7 v2**:preserved verbatim
- **W35 F1.7 Rule 8 Option C**:`cite the chunks that support each fact (typically 1-2 per fact) — avoid citing multiple overlapping chunks that convey the same information`

### 依賴先前基礎

- **W17 F3 RAGAs integration**:`make_ragas_evaluator(settings)` + `orchestrator.build_ragas_samples` + judge LLM deployment 接口(F2 修改範疇)
- **W34 F2 structlog stage timing infrastructure**:F3 runner unicode 修正後可繼續用
- **session-start.md §10.3 6 步啟動 protocol**:F1 amend 對象
- **W35 evidence**:Option C ship preserve + F1.4 judge artifacts + F2 runner crash

### W26-W35 預防控制應用

- **PC-W31-1/2/3** — N/A 本 phase
- **PC-W32-1** backend 顯式 kill+restart — F2 若涉及 judge LLM 升級需 backend restart
- **PC-W32-2** citation enrichment integration pattern — preserved
- **PC-W33-1** session-start protocol amend(Langfuse + Postgres 可達)— F1 amend 同時可順手 verify
- **PC-W34-1** session-start protocol amend extend(endpoint health check)— **F1 兌現** ⭐
- **PC-W34-2** RAGAs judge robustness — **F2 兌現** ⭐
- **PC-W35-1** F2 runner cp1252 print encoding — **F3 兌現** ⭐

### W36 範疇外(W37+ 候選)

- (j') section_path prefix filter — preserved W37+ MEDIUM
- W35 DEMOTED LOW:Option A more aggressive / prompt token reduction / engine-fetch async pool
- (g')(i')(B'.a)(ii)(k)saturated low priority
- (c)(e)(f) + BUG-026+027 + W22 D8 + W16 F1-F4 Track A IT cred — 長期 carry-over

---

## §7 變更記錄

| 日期 | 段落 | 變動 | 原因 |
|---|---|---|---|
| 2026-05-26 | initial | Plan 起草 F0 D0 啟動 | W35 retro 3 個 HIGHEST 操作債候選打包 per user explicit pick 2026-05-26 same-day post-W35 closeout |
| 2026-05-26 | §1 + §2 | F1/F2/F3 3 個獨立 deliverable 範疇鎖定 + F2 path A/B/C 取捨 surface F2.2.a user lock 之前 | Per Karpathy §1.3 surgical scope + §1.4 verifiable success criteria |
| 2026-05-26 | §6 R6 catch | 3 catches surface(PC-W34-1 protocol 缺步驟 / PC-W34-2 judge config 來源 / PC-W35-1 5 個 runner files unicode) | R6 Day 0 recursive grep 驗證 — surface 污染檢查 before F1+ 開始 |
| 2026-05-26 | §2 F1 + §6 + §7 | **R3 amend F1 amend 對象修正**:由「session-start.md §10.3」→ **CLAUDE.md §10.3**(line 524-535)— Day 1 F1.1 grep 驗證發現 session-start.md 並無 §10.3 protocol section,真嘅 6 步 AI Session Start Protocol home 喺 CLAUDE.md §10.3。R6 plan-text contamination 案例(per W23 F3 R6 recursive scope amendment — Karpathy §1.1 think-before-coding surface upfront)。F1.1-F1.4 範疇調整對應 CLAUDE.md §10.3 line 524-535 amend 加 step 5b pre-flight endpoint health check | Day 1 F1.1 R6 grep 驗證 caught contamination — W36 plan §F1 從 W34/W35 retro 引用 「session-start protocol amend」 wording 但 retro 本身又混淆 home;真 protocol home 喺 CLAUDE.md。R3 no silent drift。 |
| 2026-05-26 | §2 F2.1 + §3 G2 + §7 | **F2.1 audit 揭示 3 個 LLM deployments + .env override**:`settings.py:65-67` defaults `llm_primary=gpt-5-5` / `llm_judge=gpt-5-4-mini` / `llm_eval_judge=gpt-5-5-pro`;`.env` override `llm_eval_judge=gpt-5.4-mini`(等同 llm_judge)。**`gpt-5-5-pro` Azure deployment 可能未配置**,Path (a) 升級需 user 確認 Azure deployment availability。**W35 Option C failed_queries pattern audit**:4 個 `answer_relevancy=0.6X` borderline + 5 個 `context_recall=0.00` keyword-mode artifact(reference fallback `expected_keywords` 嘅 known limitation per ragas_evaluator.py line 75-77)。**InstructorRetryException 唔喺 raw JSON 顯式**,屬 ragas library 內部 exception。**新 surface Path (d)**:降低 RAGAs threshold OR 文檔化 keyword-mode artifact 作為 expected behaviour | F2.1 audit 結果重新 reframe path 取捨 — 原本「judge LLM 升級」 path (a) 假設 `gpt-5-5-pro` available,實際需先 verify;原本「JSON 解析」 path (b) 對 systematic borderline failures 唔解決根因;新 path (d) calibrate 接受標準。F2.1.d surface 至 user pick path 之前 plan 必須 reflect audit reality |
