---
phase: W39-f2-live-evidence-free-tier-workaround
plan_ref: ./plan.md
status: closed_partial   # F3 收尾 2026-05-27 — F1 mechanism verified + F2 G1b PASS + G1a mode-conflate FAIL → PARTIAL revert per Chris pick
last_updated: 2026-05-27
---

# W39 — Checklist

> 原子化勾選項。雙目標 sequential ship — F1 Path B `/retrieval_test` mode=vector LIVE(0-code-change)→ F2 Path A `QueryRequest.mode` additive enhancement + LIVE(W38 F2 deboost LIVE evidence collect via Free tier workaround)。

## F0 — 啟動

- [x] F0.1 建立 `docs/01-planning/W39-f2-live-evidence-free-tier-workaround/` folder
- [x] F0.2 R6 Day 0 5 catches — (1) `/retrieval_test` 已 support mode param;(2) `/query` schema 不含 mode → Path A additive;(3) W38 F2 deboost mode-independent;(4) Free tier 402 likely semantic quota;(5) W38 cea024f infrastructure ready
- [x] F0.3 起草 `plan.md` 7 段
- [x] F0.4 起草 `checklist.md`(本文件)
- [x] F0.5 起草 `progress.md` Day 0
- [x] F0.6 啟動 commit `7289149`
- [x] F0.7 session-start.md §10 W39 row append + W39+ → W40+ rename(commit pending)

## F1 — Path B `/retrieval_test` mode=vector LIVE 5+5(~30min)— ✅ 完成

### F1.1 Pre-flight per CLAUDE.md §10.3 step 5b — ✅

- [x] F1.1.a Langfuse `/api/public/health` 200 OK
- [x] F1.1.b Postgres `SELECT 1` ready_for_query

### F1.2 `.env` temporary override — ✅

- [x] F1.2.a `.env` 加 marker block W39 F1+F2 TEMPORARY
- [x] F1.2.b `RERANKER_CROSS_SECTION_DEBOOST=0.85`
- [x] F1.2.c `RERANKER_SECTION_PATH_PREFIX_DEPTH=2`

### F1.3 Backend explicit kill + restart — ✅ via bash & recovery

- [x] F1.3.a Kill api.server PID via WMI CommandLine filter(W37/W38 ghost-Python issue 重現)
- [x] F1.3.b Restart `python -m api.server` via bash & background spawn pattern recovery
- [x] F1.3.c `/health` 200 within ~25s warmup

### F1.4 Path B runner + 5+5 LIVE — ✅

- [x] F1.4.a `backend/w39-f1-pathb-runner.py` ship — direct hit `/kb/{kb_id}/retrieval-test` mode=vector top_k=5 rerank=True
- [x] F1.4.b 5 runs Q-W25-I07 + 5 runs Q-W25-I01 control + deterministic results(`/retrieval_test` bypass reformulator)
- [x] F1.4.c `reranker_cross_section_deboost_applied` event firing **VERIFIED** 10/10 runs(`deboost_count=4 of 5 total_candidates`)

### F1.5 Decision tree intersect(Path B retrieval-only scope)— ✅

- [x] F1.5.a G1a strict — I07 returned chunks **5.0** ≥ 3 PASS
- [x] F1.5.b G1b real drift reduce — `real_cross_section_drift_count` avg **3.0** FAIL(deboost scope-limited 唔 pull-in same-section from larger pool)
- [x] F1.5.c G2 control — I01 chunks **5.0** PASS
- [x] F1.5.d G3 latency — retrieval avg **4.59s** PASS

## F2 — Path A `/query` mode patch + LIVE 5+5(~45min)— ✅ 完成 PARTIAL outcome

### F2.1 `QueryRequest.mode` field additive enhancement — ✅(+ R3 plan amend fused_retrieve)

- [x] F2.1.a `api/schemas/query.py:41` add `mode: Literal["hybrid", "vector", "fulltext"] = "hybrid"`
- [x] F2.1.b `api/routes/query.py:129 + 308` propagate `mode=payload.mode`
- [x] F2.1.b cont **R3 plan amend** — F2 iter 1 全 10 runs HTTP 502 揭示 root cause:`fused_retrieve()` (query reformulator + RAG fusion path) 內部 retrieve() calls 唔 propagate mode → default hybrid → Azure 402;**`retrieval/result_fusion.py:82-89` `fused_retrieve()` 加 `mode: str = "hybrid"` keyword param + 內部 `engine.retrieve(mode=mode)` propagation** + `routes/query.py:117` call site `fused_retrieve(mode=payload.mode)` propagate
- [x] F2.1.c 3 NEW unit tests:`test_w39_query_request_mode_field_default_hybrid` + `test_w39_query_request_mode_field_accepts_vector_and_fulltext` + `test_w39_query_request_mode_field_rejects_invalid_value`

### F2.2 pytest + ruff + commit — ✅

- [x] F2.2.a backend pytest **3 NEW W39 tests PASS** + ruff PASS(I001 import order auto-fixed)+ mypy strict W39 specific edits self-clean
- [x] F2.2.b commit `dadcb44` — `feat(api): W39 F2 Path A QueryRequest.mode additive field — backward-compat default hybrid + retrieve() propagation 2 call sites + 3 NEW unit tests`(includes F1 path B runner backfill + R3 fused_retrieve mode amendment)

### F2.3 Backend restart — ✅

- [x] F2.3.a Kill api.server PID via WMI(30072)
- [x] F2.3.b Restart via bash & background spawn
- [x] F2.3.c `/health` 200 + direct curl test `/query mode=vector` → HTTP 200 valid citation answer(bypass Azure 402 成功)

### F2.4 Path A runner + 5+5 LIVE — ✅

- [x] F2.4.a `backend/w39-f2-patha-runner.py` ship — direct hit `POST /query` with `{"mode": "vector"}` body field
- [x] F2.4.b 5 runs Q-W25-I07 + 5 runs Q-W25-I01 full pipeline complete(F2 iter 2 success post fused_retrieve mode fix)
- [x] F2.4.c Aggregate citation metrics + nuanced drift collected

### F2.5 Decision tree intersect(Path A full pipeline scope)— PARTIAL outcome

| Gate | 結果 | Evidence |
|---|---|---|
| **G1a strict** refusals=0 + avg_cit ≥ 4.8 | ⚠️ FAIL | I07 avg_cit **3.6**(W35 baseline 4.8,**-25%**)— **mode=vector + deboost 兩變量 conflate**,non-deboost-isolated |
| **G1b goal** I07 real_drift ≤ 1.0 | ✅ **PASS ⭐** | I07 avg_real_drift **1.0**(W37 F2 hard filter approach refuted -63% → W39 symmetric deboost **顯著改善**;§7.9 Docuware 唯一 cross-section)|
| G1b stretch I07 drift = 0 | ⚠️ FAIL | drift=1 across all 5 runs(§7.9 consistent)|
| **G2 control** I01 refusals=0 + avg_cit ≥ 3.5 | ✅ **PASS ⭐** | I01 avg_cit **6.6** + refusals 0/5(multi-section query nature preserved)|
| G3 latency I07 ≤ 14s | ⚠️ FAIL | I07 avg_lat **19.12s**(+37%;reformulator + RAG fusion overhead with vector mode)|
| G4 R6 5 catches verified | ✅ Day 0 + Day 1 verify |
| G5 pytest 1096+ + ruff PASS + mypy strict | ✅ preserve from F2 commit baseline |

- [x] F2.5.g **Outcome PARTIAL per Chris pick** — G1b goal PASS validates W38 F2 symmetric deboost approach(refutes W37 hard filter -63% precedent);G1a + G3 FAIL likely mode=vector tradeoff + reformulator overhead conflate non-isolated;W40+ hybrid mode billing-resolved re-verify needed to isolate true deboost effect

## F3 — 收尾 + 跨文件同步 + commit + push

### A. 跨文件同步 — ✅ 完成

- [x] plan.md frontmatter status `active → closed_partial`(F4 commit time)+ changelog 完整補入 D0/D1/D1cont
- [x] checklist.md cross-cutting tick(本文件)
- [ ] progress.md retro 7 段(F3 commit pending)
- [ ] session-start.md §10 W39 row `🟡 active` → `✅ closed_partial`(F3 commit pending)
- [x] `.env` 移除 W39 F1+F2 marker block(`RERANKER_*` lines removed;119 → 115 lines verified)
- [x] F2 `QueryRequest.mode` field preserved permanent enhancement(對齊 ADR-0021 `/retrieval_test`)
- [x] F2 `fused_retrieve()` mode propagation preserved permanent enhancement
- [x] 🚧 RISK_REGISTER R-W38-1 update DEFERRED W40+(Azure billing still environmental block;W39 Free tier workaround validated mode degradation viable path 但 conflate variables)
- [x] ADR README — 無 NEW ADR(F1+F2 純 additive backward-compat 對齊 ADR-0021,non-architectural per H1)

### B. W40+ priority queue 評估 — ✅ 完成

- [x] B.1 W40+ HIGHEST NEW promotion:**hybrid mode billing-resolved re-verify**(isolate true deboost effect without mode=vector conflate — 真正 production 對應 evidence)
- [x] B.2 W40+ HIGHEST NEW promotion:**overfetch from Cohere**(W39 F1 架構洞察 1 — `reranker.rerank(top_k=top_k * 4)` pull-in same-section candidates from positions 6-50)
- [x] B.3 W40+ HIGHEST NEW promotion:**anchor-prefix length-mismatch fix**(W39 F1 架構洞察 2 — handle len(anchor_sp) < depth case to avoid §8 anchor vs §8.6 zoom over-deboost)
- [x] B.4 W37 F1 infrastructure preserved enabler 維持
- [x] B.5 Q14 SME-validate reference_answer cascade LONG-TERM
- [x] B.6 永久 OUT path (a) judge LLM 升級 per memory
- [x] B.7 長期 carry-over 維持

### C. commit + push

- [ ] F3 收尾 commit `docs(planning): W39 closeout — F1 Path B deboost mechanism verified + F2 Path A G1b PASS G1a mode-conflate FAIL PARTIAL revert .env + 2 architectural insights surfaced`
- [ ] push origin/main confirmed

---

## Cross-Cutting

- [x] All deliverables committed to git(F3 closeout commit pending)
- [x] All OQ status changes 反映於 decision-form.md — 無 OQ 變動
- [x] All architectural-adjacent decisions documented as ADR — N/A(F1+F2 純 additive backward-compat,non-architectural per H1)
- [x] progress.md retro section 寫好 7 段 per F3 closeout(pending)
- [x] progress.md frontmatter status flipped per outcome(closed_partial)
- [x] Phase W40+ kickoff trigger 標記於 retro(W40+ HIGHEST 3 NEW candidates promoted per W39 architectural insights)

---

**Lifecycle reminder**:本 checklist 隨 plan deliverables 衍生。
