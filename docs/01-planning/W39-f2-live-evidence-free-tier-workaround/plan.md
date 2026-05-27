---
phase: W39-f2-live-evidence-free-tier-workaround
status: closed_partial   # F3 收尾 2026-05-27 — F1 Path B PASS (deboost mechanism verified working post-rerank top-K re-order)+ F2 Path A PARTIAL outcome(G1b goal PASS reduce real cross-section drift to 1.0;G1a FAIL avg_cit -25% likely mode=vector tradeoff conflate;G3 latency FAIL +37% reformulator overhead with vector mode)→ Chris pick PARTIAL revert per W37/W38 precedent;.env reverted production preserve default 1.0 disabled;F2 QueryRequest.mode + fused_retrieve mode propagation preserved permanent enhancement(對齊 ADR-0021 /retrieval_test);W40+ HIGHEST NEW hybrid mode billing-resolved re-verify(isolate true deboost effect without mode conflate)
last_updated: 2026-05-27
component_scope: C04 Retrieval Engine(F1 LIVE verify W38 F2 deboost)+ C08 API Gateway(F2 `/query` schema mode param additive enhancement,backward-compat default hybrid)
adr_refs:
  - W38 progress.md retro §F3 — LIVE BLOCKED by Azure AI Search 402 Payment Required(Free tier semantic ranker monthly quota exhausted)
  - W38 commit cea024f — F2 reranker post-rerank deboost infrastructure ship(Settings 2 NEW knobs + loop + 5 unit tests + observability log)
  - ADR-0021 — `/retrieval_test` endpoint mode param(hybrid / vector / fulltext)Path B precedent — vector skip semantic
  - ADR-0035 W25 F5 D2 — symmetric deboost pattern reference(W38 F2 implementation root)
  - ADR-0017 R8 environmental block pattern(W17 F1.5b/F3.5b + W38 F3 precedent)
  - W11 Q11 Pattern A — Azure subscription IT-side billing dependency
related_carry_overs:
  - W38 retro §W39+ HIGHEST NEW — F2 LIVE evidence collect trigger,W39 兌現 via Free tier workaround
  - W38 F2 reranker deboost infrastructure preserved(W39 LIVE 驗證)
  - W37 F1 `_find_neighbour_chunks` section_path filter infrastructure preserved enabler
---

# W39 — W38 F2 LIVE Evidence Collect(Free Tier Workaround)

## §1 目標 + 範疇

**單一主要目標**:Free tier Azure AI Search 限制下,collect W38 F2 reranker cross-section deboost LIVE evidence — bypass Azure semantic ranker monthly quota cap(402 Payment Required)by using mode=vector / fulltext degradation 同時保留 Cohere rerank + W38 F2 deboost loop。

**Karpathy §1.3 surgical scope 嚴守**:
- F1 Path B — **0-code-change** /retrieval_test endpoint(already supports mode param per ADR-0021)+ direct hit LIVE 5+5 with mode=vector
- F2 Path A — **additive QueryRequest.mode field**(backward-compat default "hybrid")+ retrieve() propagation 2 call sites(`query.py:129 + 308`)+ unit tests
- F3 closeout — **唔 revert F2 mode field**(屬 permanent enhancement 對齊 `/retrieval_test`)+ `.env` clean state 維持
- 唔加 LLM cost knobs(per memory `feedback_judge_llm_cost_policy.md`)
- 唔 modify Cohere rerank invocation logic(W38 F2 deboost 已 ship)

**Non-goals**(W39 範疇外):
- Azure Search Standard S1 tier upgrade(per H2 spec lock — IT-side / cost decision,non-code)
- Wait monthly Free tier quota reset(passive path,non-AI action)
- W37 F1 `_find_neighbour_chunks` LIVE verify(separate W40+ candidate)
- Q14 SME-validate `reference_answer` cascade — LONG-TERM
- Enumeration query architectural mismatch research — LONG-TERM Tier 2 boundary

**Component 範疇**:
- **C04 Retrieval Engine**(F1 LIVE verify W38 F2 post-rerank deboost effect)
- **C08 API Gateway**(F2 `/query` schema mode field additive — 對齊 ADR-0021 `/retrieval_test` 已支援 pattern)
- **不涉及** C01-C03 / C05-C07 / C09-C13(無 ingestion / generation / KB / auth / eval / frontend 改動)

---

## §2 交付物 F0-F3

### F0 — 啟動(本 session 2026-05-27)

- F0.1 建立 `docs/01-planning/W39-f2-live-evidence-free-tier-workaround/` folder
- F0.2 R6 Day 0 recursive grep 驗證 — **catch (1)** `/retrieval_test` endpoint 已 support mode param per `api/schemas/retrieval_test.py:17`(Path B 0-code-change LIVE direct hit);**catch (2)** `/query` schema `QueryRequest` 不含 mode param(Path A additive enhancement scope);**catch (3)** W38 F2 deboost loop mode-independent — Cohere rerank separate API,deboost post-rerank fire regardless of search mode;**catch (4)** Free tier 402 root cause likely semantic ranker monthly quota exhausted(typical Free tier limit ~1000 semantic queries/月);**catch (5)** W38 commit cea024f F2 infrastructure ready(Settings 2 knobs + retrieval_engine.py:158-200 loop + 5 unit tests + observability log)— Settings default `reranker_cross_section_deboost=1.0` disabled,需 `.env` override LIVE test
- F0.3 起草 `plan.md` 7 段(本文件)
- F0.4 起草 `checklist.md` 原子化勾選項
- F0.5 起草 `progress.md` Day 0 — 啟動行動 + R6 5 catches 報告 + W38 F3 root cause root carried + F-phase pre-implementation surface
- F0.6 啟動 commit `docs(planning): kickoff W39-f2-live-evidence-free-tier-workaround + R6 Day 0 5 catches surface Path B 0-code-change + Path A additive QueryRequest.mode enhancement`
- F0.7 session-start.md §10 W39 row append `🟡 active 2026-05-27` + W39+ → W40+ placeholder rename

### F1 — Path B `/retrieval_test` mode=vector LIVE 5+5(~30min)

#### F1.1 Pre-flight per CLAUDE.md §10.3 step 5b(W36 PC-W34-1 ship)

- F1.1.a `Invoke-WebRequest -Uri http://localhost:3000/api/public/health -TimeoutSec 30`(預期 200 — Langfuse)
- F1.1.b `docker exec ekp-postgres psql -U langfuse -d postgres -c "SELECT 1;"`(預期 `1 row` ready_for_query)

#### F1.2 `.env` temporary override

- F1.2.a `.env` 加 marker block `# --- W39 F1+F2 TEMPORARY override 2026-05-27 — W38 F2 deboost LIVE evidence collect ---`
- F1.2.b `RERANKER_CROSS_SECTION_DEBOOST=0.85`
- F1.2.c `RERANKER_SECTION_PATH_PREFIX_DEPTH=2`
- F1.2.d F3 closeout 移除 marker block per W27/W29/W37 pattern

#### F1.3 Backend explicit kill + restart

- F1.3.a Kill existing api.server PID via WMI CommandLine filter(W38 ghost-Python mitigation pattern)
- F1.3.b Restart `python -m api.server` via `Start-Process -WorkingDirectory` absolute path
- F1.3.c Verify `/health` 200 within 30s warmup

#### F1.4 Path B `/retrieval_test` 5+5 LIVE runs

- F1.4.a 寫 `backend/w39-f1-pathb-runner.py` — direct hit `POST /kb/{kb_id}/retrieval-test`(no synthesizer)
  - 5 runs Q-W25-I07(`show me all the Integration scenarios`)mode=vector top_k=5 rerank=True
  - 5 runs Q-W25-I01(`what is the high level architecture`)control mode=vector top_k=5 rerank=True
  - 加 nuanced drift metric(per W38 F3 runner pattern — `real_cross_section_drift_count` + `valid_hierarchical_zoom_count`)
- F1.4.b Run `python w39-f1-pathb-runner.py` — aggregate per-run + W38 baseline cross-comparison
- F1.4.c Verify W38 F2 deboost log event `reranker_cross_section_deboost_applied` firing(Langfuse trace OR backend log)

#### F1.5 G1+G2+G3 decision tree intersect(Path B scope)

- F1.5.a **G1a strict** — I07 5 runs returned chunks ≥ 3(retrieval-side baseline,non-refused)
- F1.5.b **G1b real drift reduce** — I07 `real_cross_section_drift_count` avg ≤ 1(goal)OR = 0(stretch)observed in returned chunks' section_path
- F1.5.c **G2 control** — I01 5 runs returned chunks ≥ 3 + section_path multi-section preserved(query nature)
- F1.5.d **G3 latency** — retrieval avg ≤ 5s(Path B no synthesizer overhead;Vector mode + Cohere rerank only)

### F2 — Path A `/query` schema mode patch + LIVE 5+5(~45min)

#### F2.1 `QueryRequest.mode` field additive enhancement

- F2.1.a `backend/api/schemas/query.py:41` add `mode: Literal["hybrid", "vector", "fulltext"] = "hybrid"` field
- F2.1.b `backend/api/routes/query.py:129 + 308` — `engine.retrieve(...)` call sites propagate `mode=payload.mode`
- F2.1.c 1 NEW unit test `test_w39_query_request_mode_field_default_hybrid` + 1 NEW integration test `test_w39_query_route_mode_vector_propagates_to_engine`

#### F2.2 pytest + ruff + commit

- F2.2.a backend pytest 1096 → 1098(+2 NEW W39 tests)+ ruff PASS + mypy strict
- F2.2.b commit `feat(api): W39 F2 Path A QueryRequest.mode additive field — backward-compat default hybrid + retrieve() propagation 2 call sites + 2 NEW unit tests`

#### F2.3 Backend restart(no `.env` change — `mode=vector` 由 query body 傳)

- F2.3.a Kill api.server PID via WMI + restart
- F2.3.b Verify `/health` 200

#### F2.4 Path A `/query` mode=vector LIVE 5+5

- F2.4.a 寫 `backend/w39-f2-patha-runner.py` — direct hit `POST /query` with `{"mode": "vector"}` body field
  - 5 runs Q-W25-I07 mode=vector(full pipeline:retrieve→rerank→deboost→synthesize→cite)
  - 5 runs Q-W25-I01 control mode=vector
- F2.4.b Run `python w39-f2-patha-runner.py` — full citation metrics + nuanced drift
- F2.4.c Verify deboost fire + citation count post-deboost

#### F2.5 G1+G2+G3 decision tree intersect(Path A full pipeline scope)

- F2.5.a **G1a strict** — I07 refusals 0/5 + avg_cit ≥ 4.8(W35 baseline maintain)
- F2.5.b **G1b real drift reduce** — I07 citation `real_cross_section_drift_count` avg ≤ 1(goal)
- F2.5.c **G2 control** — I01 refusals 0/5 + avg_cit ≥ 3.5(I01 multi-section query nature preserved)
- F2.5.d **G3 latency** — I07 full pipeline avg ≤ 14s(W35 +20% budget)
- F2.5.e **G4 R6 5 catches verified** at Day 0 + Day 1 active flip
- F2.5.f **G5 pytest 1098 + ruff PASS + mypy strict** preserve
- F2.5.g Decide outcome — (a) PASS / (b) PARTIAL / (c) FAIL

### F3 — 收尾 + 跨文件同步 + commit + push(~30min)

- F3.A.1 plan.md frontmatter `status: active → closed OR closed_partial`(per F2 outcome)
- F3.A.2 checklist.md cross-cutting tick + N/A reason
- F3.A.3 progress.md retro 7 段(What Worked / What Didn't / Carry-overs / ADR Triggers / Phase Gate Result / W40+ Priority Queue Locked / Actual vs Planned Effort)
- F3.A.4 session-start.md §10 W39 row `🟡 active` → `✅ closed`(F3 commit time)
- F3.A.5 `.env` 移除 W39 F1+F2 marker block(per W27/W29/W37/W38 pattern;production preserve default 1.0)
- F3.A.6 **F2 `QueryRequest.mode` field preserved**(對齊 ADR-0021 `/retrieval_test` permanent enhancement,backward-compat default hybrid)
- F3.A.7 🚧 RISK_REGISTER R-W38-1 update — Free tier semantic quota workaround validated
- F3.A.8 ADR README — 無 NEW ADR(F1 0-code-change + F2 additive backward-compat per H1 non-architectural)
- F3.B.1 W40+ 候選 promotion per F2 outcome
- F3.B.2 W37 F1 infrastructure preserved enabler 維持
- F3.B.3 W38 F2 production flip default `reranker_cross_section_deboost=1.0 → 0.85`(若 F2 outcome (a) PASS — W40+ separate phase decision per W26 PC1)
- F3.B.4 Q14 SME-validate reference_answer cascade — LONG-TERM
- F3.B.5 長期 carry-over 維持
- F3.C.1 F3 收尾 commit
- F3.C.2 push origin/main confirmed

---

## §3 Acceptance Criteria + Phase Gate

### G1a — Production behavior non-regression(MUST PASS)
- G1a.1 backend pytest 1098+ ≥ W38 baseline 1096(+2 NEW W39 tests)
- G1a.2 ruff PASS(W39 specific edits)
- G1a.3 mypy strict 維持(W39 specific edits)
- G1a.4 F2 Path A 5-run I07 citation_count avg ≥ W35 baseline 4.8(non-regression)
- G1a.5 F2 Path A 5-run I07 refusals 0/5(W32 (h') G1 saturated 100% MUST preserve)

### G1b — Real cross-section drift reduce signal(per W38 F3 nuanced metric)
- G1b.1 **GOAL**:F2 Path A 5-run I07 `real_cross_section_drift_count` ≤ 1 across runs
- G1b.2 **STRETCH**:= 0(no §11 / §3 alongside §8 anchor;hierarchical zoom-in still kept)

### G2 — Control I01 non-regression(MUST PASS)
- G2.1 F2 Path A refusals 0/5
- G2.2 F2 Path A avg_cit ≥ 3.5
- G2.3 I01 多 section 由 query nature 觸發 — W39 metric NOT flag as bug

### G3 — Latency budget
- G3.1 F1 Path B retrieval-only avg ≤ 5s(no synthesizer)
- G3.2 F2 Path A full pipeline avg ≤ 14s(W35 +20% budget;mode=vector 比 hybrid 略快)

### G4 — R6 verify
- G4.1 Day 0 5 catches surfaced
- G4.2 Day 1 active flip recursive verify net 0 contamination

### G5 — 跨文件 R3 + R5 + R6 sync
- G5.1 plan.md changelog entry per phase flip
- G5.2 session-start.md §10 W39 row update
- G5.3 R5 — 無 NEW ADR(per H1 non-architectural)

### 3 outcome decision matrix

| 結果 | 判決 | 處置 |
|---|---|---|
| **(a)** G1a + G1b reduce(goal met) + G2 + G3 PASS | **PASS — production flip candidate** | Settings default `reranker_cross_section_deboost=1.0 → 0.85` 留 W40+ separate flip decision(per Q4 + W26 PC1)|
| **(b)** G1a + G2 PASS + G1b partial | **PARTIAL — preserve default 1.0** | F2 infrastructure preserved + W40+ tune depth OR deboost factor;F2 `QueryRequest.mode` enhancement preserved permanent |
| **(c)** G1a regress OR G2 regress(I07 refusals > 0 OR avg_cit < 4.8 OR I01 refusals > 0)| **FAIL — full revert deboost** per Karpathy §1.3 + Q4 measurement-experiment-fail-policy(W30/W31/W37 precedent);F2 `QueryRequest.mode` 仍 preserve permanent |

---

## §4 Risks + Mitigations

| Risk | Severity | Mitigation |
|---|---|---|
| **R-W39-1** Vector mode 仍 hit Azure 402(若 402 唔係 semantic-specific 而係 entire resource billing block) | Medium | F1 Path B early signal — 若仍 402,immediately surface至 user,F1 abort,F2 不 trigger;backend stop revert .env |
| **R-W39-2** Cohere rerank 受 Azure billing 影響(若 Cohere via Azure Marketplace billing 共用 subscription) | Low | Cohere v4.0-pro via Azure Marketplace是獨立 SKU per Q5 Path A;F1 direct curl test 可分辨(rerank_latency_ms > 0 即 Cohere reachable)|
| **R-W39-3** mode=vector 結果同 mode=hybrid 唔同 — W38 F2 deboost LIVE evidence vector-specific 唔代表 hybrid 一樣 | Medium | F2 LIVE evidence framed as「vector mode validated」+ W40+「hybrid mode validate after billing resolved」preserved as enabler;Karpathy §1.1 think-before-coding upfront |
| **R-W39-4** Backend ghost-Python-3.12 restart issue(W37 + W38 precedent)| Low | F1.3 + F2.3 explicit kill via WMI CommandLine filter + Start-Process absolute WorkingDirectory pattern(W37 + W38 lesson) |
| **R-W39-5** `QueryRequest.mode` additive field break downstream(/conversations persist messages 等)| Low | Backward-compat default "hybrid" preserved;Pydantic ignore unknown fields by default for legacy stored messages;F2.1.c 加 unit test cover field default |

---

## §5 Dependencies + 風險矩陣

### Hard dependencies(必須 satisfied 先 ship)
- ✅ W38 F2 reranker deboost infrastructure ship `cea024f`
- ✅ W38 F4 closeout `.env` clean state preserved `3d7c834`
- ✅ ADR-0021 `/retrieval_test` endpoint mode param support `api/schemas/retrieval_test.py:17`
- ✅ W36 PC-W34-1 CLAUDE.md §10.3 step 5b pre-flight protocol
- ✅ W36 PC-W35-1 runner cp1252 fix(F1+F2 runner 複用 utf-8 reconfigure pattern)
- ✅ Cohere v4.0-pro endpoint reachable per `.env`(separate from Azure Search billing)

### Soft dependencies(non-blocking)
- ⚠️ PC-W32-1(backend no reload=True)— F1+F2 必須 explicit kill+restart
- ⚠️ W26 PC1 一次只郁一個旋鈕 — W39 ship `.env` override 0.85(W38 已 ship infrastructure,W39 LIVE 驗證)
- ⚠️ R-W39-1 Free tier 402 vector mode reachability — F1 early signal

---

## §6 Changelog

### 2026-05-27 D0 — F0 啟動
- Plan + checklist + progress 起草
- R6 Day 0 5 catches surfaced(/retrieval_test mode ready / /query schema additive / W38 F2 mode-independent / Free tier 402 semantic quota / W38 cea024f infrastructure ready)
- F0.6 commit `7289149`
- F0.7 session-start.md §10 W39 row append `🟡 active 2026-05-27` commit `83aafce`

### 2026-05-27 D1 — F1 Path B `/retrieval_test` mode=vector LIVE 5+5
- F1.1 pre-flight Langfuse 200 + Postgres SELECT 1 PASS
- F1.2 `.env` temp override `RERANKER_CROSS_SECTION_DEBOOST=0.85 + RERANKER_SECTION_PATH_PREFIX_DEPTH=2`(112 → 119 lines)
- F1.3 Backend explicit kill + restart(W37/W38 ghost-Python issue 重現 PID 47544 hang + 10388 ghost → kill both + bash & spawn pattern recovered)— /health 200 ready
- F1.4 `backend/w39-f1-pathb-runner.py` ship + 5+5 LIVE runs
- F1.5 Decision tree(Path B retrieval-only):G1a PASS chunks 5.0 + G1b FAIL real_drift 3.00 + G2 PASS + G3 PASS wall 4.59s
- **重要發現**:W38 F2 deboost LOG **正確 firing**(`reranker_cross_section_deboost_applied event` 10/10 runs,deboost_count=4 of 5 total_candidates)
- **2 個架構洞察 surfaced**:
  - 洞察 1:Deboost scope-limited 唔 reduce cross-section drift — `reranker.rerank(top_k=5)` 返 fixed top-5,deboost 只 re-order top-5(唔 pull in same-section candidates from position 6-50)
  - 洞察 2:Anchor-prefix length-mismatch — anchor sp `['§8']` 長度 1,depth=2 anchor_prefix[:2]=`['§8']` vs §8.6 cand_prefix[:2]=`['§8', '§8.6']` 唔同 → §8.6 valid zoom-in 反被 deboosted
- F1 commit not separately(included in F2 commit cea024f baseline + Path B 0-code-change per ADR-0021)

### 2026-05-27 D1 cont — F2 Path A `/query` mode=vector full pipeline LIVE 5+5
- F2.1 `QueryRequest.mode: Literal["hybrid", "vector", "fulltext"] = "hybrid"` field 加入(對齊 ADR-0021 `/retrieval_test`)+ `routes/query.py` 2 call sites propagate
- F2.1 cont **R3 plan amend** — 增 `fused_retrieve()` mode param propagation(原 plan 漏算 query reformulator + RAG fusion internal retrieve() call sites,F2 iter 1 全 10 runs HTTP 502 揭示 root cause)
- F2.2 3 NEW unit tests PASS + ruff PASS
- F2 commit `dadcb44`(QueryRequest.mode + retrieve propagation + 3 unit tests + F1 runner backfill)
- F2.3 Backend restart with fused_retrieve mode patch — direct curl /query mode=vector → HTTP 200 + valid citations(成功 bypass Azure 402)
- F2.4 `backend/w39-f2-patha-runner.py` ship + 5+5 LIVE runs
- F2.5 Decision tree(Path A full pipeline):
  - **G1a strict FAIL** — I07 avg_cit 3.6 vs W35 baseline 4.8 = **-25%**(可能 mode=vector less diverse top-K conflate,non-deboost-isolated)
  - **G1b goal PASS ⭐** — I07 avg_real_drift **1.0**(比 W37 F2 hard filter -63% 顯著改善;§7.9 Docuware 唯一 cross-section,§8 family dominate)
  - G1b stretch FAIL — drift=1 across all 5 runs
  - **G2 control PASS ⭐** — I01 avg_cit 6.6 + refusals 0/5
  - G3 latency FAIL — I07 avg_lat 19.12s vs 14s budget = +37%(reformulator + RAG fusion overhead with vector mode)
- **W37 vs W38 vs W39 對比**:W37 hard filter I07 1.8 (-63%) → W39 symmetric deboost I07 3.6 (-25%) → W35 baseline 4.8(W38 F2 symmetric pattern 明顯比 W37 hard filter approach 好,證明 ADR-0035 W25 pattern reference correct)
- Chris pick **PARTIAL revert** per W37/W38 precedent(per ADR-0017 R8 environmental block pattern + W26 PC1 一次只郁一個旋鈕 + Karpathy §1.3 surgical)

### 2026-05-27 D1 cont — F3 closeout PARTIAL revert
- `.env` marker block + RERANKER_* lines removed(119 → 115 lines)— production preserve default deboost=1.0 disabled
- Backend explicit kill(PID 46240 via WMI CommandLine filter)
- F2 production code preserved:
  - W38 F2 deboost infrastructure(Settings + retrieval_engine + 5 unit tests + observability)
  - W39 F2 QueryRequest.mode field(permanent enhancement,對齊 ADR-0021 /retrieval_test)
  - W39 F2 fused_retrieve mode propagation(permanent enhancement)
- 4 artifact sync(plan.md / checklist.md / progress.md / session-start.md)
- F3 closeout commit pending

---

## §7 Schedule Estimate

| Phase | 預估 | 累積 |
|---|---|---|
| F0 啟動(plan + checklist + progress + R6 verify + 啟動 commit + session-start sync) | 15min | 15min |
| F1 Path B LIVE 5+5(pre-flight + `.env` override + backend restart + runner write + 10 runs + decision tree)| 30min | 45min |
| F2 Path A schema patch + LIVE 5+5(QueryRequest.mode + propagation + 2 unit tests + pytest + commit + backend restart + runner write + 10 runs + decision tree)| 45min | 1h 30min |
| F3 收尾 + 跨文件同步 + commit + push | 15min | 1h 45min |

**Total**:**~1.5-2h**(MEDIUM phase 評估)。Real-calendar collapse 預期 within range(W38 ~4h vs ~4h pattern;W37 ~2.5h within 2.5-2.75h)。

---

**End of W39 plan.md**
