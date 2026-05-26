---
phase: W29-reformulator-diagnose
plan_ref: ./plan.md
checklist_ref: ./checklist.md
status: active
start_date: 2026-05-26
last_updated: 2026-05-26
---

# Phase W29 — Progress Journal

> Daily progress per CLAUDE.md §10 R2 binding;commit hash ↔ Day-N entry mapping mandatory(except `docs(planning):` housekeeping commits)。

---

## Day 0 — 2026-05-26 (Kickoff + R6 Day 0 catch)

### Action

- W28 closed PASS post-`42c699f` + `c20530b` housekeeping ship。User 提名 W29+ candidate (g) NEW Synthesizer enumeration-refuse fix via path (iii) F3 reformulator strengthening
- AskUserQuestion 第 1 round 4 questions Recommended picks:Phase classification / Surgical scope / User-test only primary gate / PARTIAL fallback
- **R6 Day 0 pre-active-flip recursive grep verify** triggered before any code change(per CLAUDE.md §10 R6 + Karpathy §1.1 think-before-coding)— catch surfaced

### R6 catch detail

讀完 `backend/generation/query_reformulator.py` line 47-89 `REFORMULATOR_SYSTEM_PROMPT` 現狀,**發現 W29 plan-text 同 actual code reality 嚴重唔對齊**:

| Plan-text 假設(用戶提名「path (iii) reformulator strengthening」)| Code Reality(現有 prompt 已 ship per W25 F3 D4 ADR-0034)|
|---|---|
| 加 enumeration query shape detection | ✅ Bullet (2) literal:「When the original uses words like "all", "every", "each", "list", or "show me the X" — decompose into variants that target SPECIFIC INSTANCES or categories rather than just rephrasing "all" → "every"」 |
| 加 scenario-specific few-shot example | ✅ **EXAMPLE 3 line 78-84 直接 cover Q-W25-I07**:`Original: "show me all the integration scenarios" / Good variants: ["customer service request submission API integration", "Saga-style multi-system orchestration pattern", "inbound event-driven flow Service Bus"]` |
| 教 LLM 避免「all → every」rephrase | ✅ Bad variants 已示範:`["all integration scenarios", "every integration pattern", "list integration use cases"]` |

連帶 verify:
- `.env` 現狀:`ENABLE_QUERY_EXPANSION=true`(W25 D3 enabled 2026-05-24);W26-W28 phase eval 都行緊 reformulator path
- W25 D4 daily log Q-W25-I07 refuse 當時:`.env` 仲未 enable → chat retry 行嘅 single-query baseline path,**未行過呢個 strengthened reformulator path**
- W26-W28 eval ENABLE_QUERY_EXPANSION=true confirmed but Q-W25-I07 G3 仍 marginal MISS(W28 context_recall 0.40 borderline judge noise per 8-run flip 3 PASS / 5 FAIL)

### R6 catch consequence

「Path (iii) strengthening」**事實已經 ship 咗** 喺 W25 F3 D4(EXAMPLE 3 cover Q-W25-I07 specific decomposition)。真正未驗證係:**Strengthened reformulator + W28 best combo Settings + ENABLE_QUERY_EXPANSION=true config 下,actual reformulator behavior + RAG-fusion fan-out + RRF top-5 surface 點解仍未 close G3**。

### AskUserQuestion 第 2 round (scope redirect)

User Recommended pick:**W29-reformulator-diagnose — H1+H2+H3 audit 先**(option 1)。

3 hypotheses:
- **H1 RRF surface**:Reformulator 生對咗 variants 但 RRF k=60 仍 surface intro chunks 而非 §8.1-§8.5 individual walkthrough
- **H2 vocab-corpus mismatch**:EXAMPLE 3 hypothetical variants(「customer service request submission」/「Saga」/「Batch ETL」)同 actual corpus §8.1-§8.5 chunk vocab 唔啱
- **H3 fallback gap**:Reformulator 偶然 fallback to `[original]` → 同 W25 D4 default-off path 一樣

### Deliverables Day 0

- ✅ `docs/01-planning/W29-reformulator-diagnose/` folder created
- ✅ `plan.md` v1.0 drafted per W28 closed-phase 7-section template
- ✅ `checklist.md` v1.0 drafted per W28 atomic items pattern
- ✅ `progress.md` Day 0 entry written(this entry)
- ⏳ Commit `docs(planning): kickoff W29-reformulator-diagnose + R6 path (iii) already-shipped catch + scope redirect to audit-first` pending
- ⏳ session-start.md §10 timeline row W29 active append + §11 W28 closed_block preserve pending

### Commits

- pending kickoff commit

### Blockers / 🚧 deferred

- 🚧 D0 R8 prerequisite check defer to F1.1 active flip(W28 same-session continuity 預期 valid;will explicit verify before live curl)

### Carry-overs from W28 closeout retro

- **(c) RAGAs orchestrator-aware judge tune per R-W26-2** 大幅降低 priority(W29 嘗試 close G3 from retrieval-side rather than judge-side)
- **(d) F3 query expansion standalone test** 部分 subsumed by W29 F1.1+F1.2 audit
- NEW (e) `make_ragas_evaluator` structlog stage emit / NEW (f) Settings-default-tests / BUG-026 / BUG-027 / W22 D8 setup.md / W16 Track A IT cred — preserved untouched

### Decisions logged

- **D29.0.1**:W29 phase classification = **Phase** per user pick(multi-deliverable + eval gate + user-test verify analogous to W26/W27/W28 軌跡)
- **D29.0.2**:W29 scope = **Surgical path (iii) reformulator** ONLY per user pick(path (i) synthesizer prompt + path (ii) CRAG threshold deferred W30+ if F3 surgical insufficient)
- **D29.0.3**:W29 acceptance gate = **G1 user-test ≥ 2 A-E walkthrough citations** ONLY per user pick(no RAGAs delta eval + no enumeration corpus expansion in scope)
- **D29.0.4**:W29 G1 FAIL fallback = **PARTIAL closeout + path (ii) elevate W30+ candidate** per user pick(per W26+W27 PARTIAL closeout precedent + Karpathy §1.2 一次只郁一個旋鈕)
- **D29.0.5 R6 SCOPE REDIRECT**:**path (iii) prompt strengthening ALREADY shipped W25 F3 D4** — W29 scope redirect from「strengthen」to「diagnose-first H1+H2+H3 audit before any code change」per Karpathy §1.1 think-before-coding + user 2nd AskUserQuestion Recommended pick

---
