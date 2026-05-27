---
phase: W39-f2-live-evidence-free-tier-workaround
plan_ref: ./plan.md
status: active   # F0 啟動 2026-05-27
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
- [ ] F0.6 啟動 commit
- [ ] F0.7 session-start.md §10 W39 row append + W39+ → W40+ rename

## F1 — Path B `/retrieval_test` mode=vector LIVE 5+5(~30min)

### F1.1 Pre-flight per CLAUDE.md §10.3 step 5b

- [ ] F1.1.a Langfuse `/api/public/health` 200
- [ ] F1.1.b Postgres `SELECT 1` ready_for_query

### F1.2 `.env` temporary override

- [ ] F1.2.a `.env` 加 marker block W39 F1+F2 TEMPORARY
- [ ] F1.2.b `RERANKER_CROSS_SECTION_DEBOOST=0.85`
- [ ] F1.2.c `RERANKER_SECTION_PATH_PREFIX_DEPTH=2`

### F1.3 Backend explicit kill + restart

- [ ] F1.3.a Kill api.server PID via WMI CommandLine filter
- [ ] F1.3.b Restart `python -m api.server` via Start-Process absolute path
- [ ] F1.3.c Verify `/health` 200 within 30s warmup

### F1.4 Path B runner + 5+5 LIVE

- [ ] F1.4.a 寫 `backend/w39-f1-pathb-runner.py` direct hit `/kb/{kb_id}/retrieval-test` mode=vector top_k=5 rerank=True
- [ ] F1.4.b 5 runs Q-W25-I07 + 5 runs Q-W25-I01 control
- [ ] F1.4.c Verify `reranker_cross_section_deboost_applied` event firing

### F1.5 Decision tree intersect(Path B retrieval-only scope)

- [ ] F1.5.a G1a strict — I07 returned chunks ≥ 3
- [ ] F1.5.b G1b real drift reduce — `real_cross_section_drift_count` avg ≤ 1
- [ ] F1.5.c G2 control — I01 chunks ≥ 3 + multi-section preserved
- [ ] F1.5.d G3 latency — retrieval avg ≤ 5s

## F2 — Path A `/query` mode patch + LIVE 5+5(~45min)

### F2.1 `QueryRequest.mode` field additive enhancement

- [ ] F2.1.a `api/schemas/query.py:41` add `mode: Literal["hybrid", "vector", "fulltext"] = "hybrid"`
- [ ] F2.1.b `api/routes/query.py:129 + 308` propagate `mode=payload.mode`
- [ ] F2.1.c 2 NEW unit tests:`test_w39_query_request_mode_field_default_hybrid` + `test_w39_query_route_mode_vector_propagates_to_engine`

### F2.2 pytest + ruff + commit

- [ ] F2.2.a backend pytest 1096 → 1098 + ruff PASS + mypy strict W39 self-clean
- [ ] F2.2.b commit `feat(api): W39 F2 Path A QueryRequest.mode additive field — backward-compat default hybrid + retrieve() propagation 2 call sites + 2 NEW unit tests`

### F2.3 Backend restart

- [ ] F2.3.a Kill api.server PID via WMI
- [ ] F2.3.b Restart via Start-Process absolute path
- [ ] F2.3.c Verify /health 200

### F2.4 Path A runner + 5+5 LIVE

- [ ] F2.4.a 寫 `backend/w39-f2-patha-runner.py` direct hit `POST /query` with `{"mode": "vector"}` body field
- [ ] F2.4.b 5 runs Q-W25-I07 + 5 runs Q-W25-I01 full pipeline
- [ ] F2.4.c Aggregate citation metrics + nuanced drift

### F2.5 Decision tree intersect(Path A full pipeline scope)

- [ ] F2.5.a G1a strict — refusals 0/5 + I07 avg_cit ≥ 4.8
- [ ] F2.5.b G1b real drift reduce — citation drift ≤ 1
- [ ] F2.5.c G2 control — I01 refusals 0/5 + avg_cit ≥ 3.5
- [ ] F2.5.d G3 latency — I07 ≤ 14s
- [ ] F2.5.e G4 R6 5 catches + Day 1 verify
- [ ] F2.5.f G5 pytest 1098 + ruff PASS + mypy strict preserve
- [ ] F2.5.g Decide outcome (a) / (b) / (c)

## F3 — 收尾 + 跨文件同步 + commit + push

### A. 跨文件同步

- [ ] plan.md frontmatter status flip per outcome
- [ ] checklist.md cross-cutting tick(本文件)
- [ ] progress.md retro 7 段
- [ ] session-start.md §10 W39 row update + W40+ rename
- [ ] `.env` 移除 W39 F1+F2 marker block(production preserve default 1.0)
- [ ] F2 `QueryRequest.mode` field preserved permanent enhancement(對齊 `/retrieval_test`)
- [ ] RISK_REGISTER R-W38-1 update — Free tier workaround validated
- [ ] ADR README — 無 NEW ADR

### B. W40+ priority queue 評估

- [ ] B.1 W40+ HIGHEST candidate per F2 outcome — Settings default flip 0.85 OR hybrid mode billing-resolved verify
- [ ] B.2 W37 F1 infrastructure preserved enabler 維持
- [ ] B.3 W38 F2 production flip decision(若 outcome (a))W40+ separate phase per W26 PC1
- [ ] B.4 Q14 SME-validate reference_answer cascade LONG-TERM
- [ ] B.5 永久 OUT path (a) judge LLM 升級 per memory
- [ ] B.6 長期 carry-over 維持

### C. commit + push

- [ ] F3 收尾 commit
- [ ] push origin/main confirmed

---

## Cross-Cutting

- [ ] All deliverables committed to git
- [ ] All OQ status changes 反映於 decision-form.md — 預期無 OQ 變動
- [ ] All architectural-adjacent decisions documented as ADR — N/A(F1 0-code-change + F2 additive backward-compat per H1)
- [ ] progress.md retro section 寫好 7 段 per F3 closeout
- [ ] progress.md frontmatter status flipped per outcome
- [ ] Phase W40+ kickoff trigger 標記於 retro

---

**Lifecycle reminder**:本 checklist 隨 plan deliverables 衍生。
