---
phase: W29-reformulator-diagnose
plan_ref: ./plan.md
status: active
last_updated: 2026-05-26
---

# Phase W29 — Checklist

> Atomic checkbox(每 item ≤ 1–2 hour effort)。
> AI tick 完成嘅 item;唔可以 tick 嘅 item 喺 progress Day-N entry 寫原因 + 標 🚧 reason。

## F0 — Kickoff(plan + checklist + progress + R6 grep verify)

- [x] Create `docs/01-planning/W29-reformulator-diagnose/` folder
- [x] **R6 Day 0 catch surfaced** — `backend/generation/query_reformulator.py` line 47-89 REFORMULATOR_SYSTEM_PROMPT 已包含 (a) enumeration query shape detection bullet (2) + (b) EXAMPLE 3 直接 cover Q-W25-I07 + `.env` ENABLE_QUERY_EXPANSION=true → path (iii) ALREADY shipped W25 F3 D4 → W29 scope redirect from「strengthen」to「diagnose H1+H2+H3 audit-first」
- [x] User AskUserQuestion 2nd round Recommended pick confirmed scope redirect — `W29-reformulator-diagnose` audit-first 2026-05-26
- [x] Draft `plan.md` per W28 closed-phase template — 7-section structure + frontmatter + §2 F0-F4 deliverables + §3 G1-G5 + §4 R1-R6 + §5 D0-D2 + §6 W28+W25 carry-overs + §7 Changelog
- [x] Draft `checklist.md` per W28 closed-phase template — atomic items derived from plan §2 deliverables
- [x] Draft `progress.md` Day 0 entry — kickoff action + R6 catch detail + commit hash placeholder
- [x] Commit `docs(planning): kickoff W29-reformulator-diagnose + R6 path (iii) already-shipped catch + scope redirect to audit-first` per CLAUDE.md §10 R1 binding(commit `51ee31e`)
- [x] session-start.md §10 timeline row update — W29 active status entry append + W30+ rolling JIT row 更新 + W28 row 維持 closed(landed in `51ee31e`)

## F1 — H1+H2+H3 Diagnose(audit-only,no code change)

### A. R8 prerequisite gate

- [x] R8 prerequisite check — Azure OpenAI judge key present + ENABLE_QUERY_EXPANSION=true confirmed via .env earlier read + /health returns 5-component ok(BUG-027 cohere cosmetic — known not blocking)
- [N/A] STOP and ask Chris 若 blocked — R8 green per W28 same-week continuity

### B. F1 5 audit sub-deliverables

- [x] **F1.1 Capture actual reformulator variants on Q-W25-I07**:Standalone test 3 runs all APIConnectionError fallback(corp proxy intercepts new Python httpx);backend `/query` path Langfuse evidence shows 93.3% success rate → `f1-1-reformulator-variants-W29-D0-raw.txt`(via tee from standalone)+ `backend/w29-f1-q-i07-response.json`(curl response)
- [x] **F1.2 Grep corpus §8.1-§8.5 chunk text**:GET /kb/{id}/documents/{id}/chunks → 12 chunks under §8(chunk-0044 to 0055)including §8.1 Customer service request submission / §8.2 Real-time inventory check / §8.3 Order placement saga / §8.4 MPS event-driven / §8.5 Snowflake ETL → `f1-2-corpus-vocab-W29-D0-raw.txt`
- [x] **F1.3 Inspect RRF fusion top-5 surface**:W29 D0 top-5 = chunk-0044/0008/0036/0020/0018 — ZERO §8.1-§8.5 individual walkthrough chunks despite reformulator confirmed working → `f1-3-rrf-top5-W29-D0-raw.txt`
- [x] **F1.4 對比 EXAMPLE 3 hypothetical variants vs corpus actual vocab**:Manual diff revealed EXAMPLE 3 aligns 60-80% token overlap with §8.1 + §8.3 + §8.4 corpus chunk_title vocab → H2 REFUTED → `f1-4-vocab-mismatch-analysis-W29-D0.md`
- [x] **F1.5 Check Langfuse `query_reformulator.reformulate` fallback rate**:Langfuse API 15 obs total spanning ONLY W25 D4 (13) + W29 D0 (2) — ZERO obs during W26-W28 eval batches → **H4 NEW eval coverage gap CONFIRMED** + verify via grep `backend/eval/orchestrator.py:93` direct `engine.retrieve()` bypassing reformulator → `f1-5-reformulator-fallback-rate-W29-D0-raw.txt`

### C. F1 commit

- [ ] Commit F1 diagnose `docs(analysis): W29 F1 H1+H2+H3+H4 diagnose — 5 audit outputs + NEW H4 eval coverage gap found`

## F2 — Root cause confirm + markdown report

### A. F2 report

- [x] Draft `f2-root-cause-W29-D1.md` — 6 sections:F1.1-F1.5 evidence summary / H1 RRF surface verdict CONFIRMED dominant / H2 REFUTED / H3 standalone-only(not backend-dominant)/ **H4 NEW eval coverage gap CONFIRMED dominant** / F3 surgical fix path A/B/C/D/E proposal
- [x] Root cause classification — **H1 + H4 NEW combined dominant**(H1 explains backend `/query` G1 fail;H4 explains W26-W28 eval G3 marginal MISS not reflecting reformulator-path performance)

### B. F2 commit

- [ ] Commit F2 root cause `docs(analysis): W29 F2 root cause confirm — H1 RRF surface + H4 NEW eval coverage gap combined dominant + F3 Path A/C/E proposal`

## F3 — Surgical fix based on confirmed root cause(scope-conditional)

### A. Scope-conditional fix

- [ ] **若 F2 = H1 RRF dominant** → Candidate (a) `QUERY_EXPANSION_PER_VARIANT_OVERFETCH` tune OR Candidate (b) RRF `k` parameter tune
- [ ] **若 F2 = H2 vocab-corpus mismatch dominant** → Candidate (c) EXAMPLE 3 vocab replace with F1.2 actual corpus tokens
- [ ] **若 F2 = H3 fallback gap dominant** → Candidate (d) `QUERY_EXPANSION_LATENCY_CAP_S` tune OR Candidate (e) reformulator error handling strengthen
- [ ] **若 F2 = None / judge noise alone** → F3 = no-op surgical fix(文件化 finding;G1 user-test predicted FAIL → PARTIAL closeout path)

### B. F3 tests

- [ ] F3 unit test 2+ NEW(若 reformulator prompt OR result_fusion touched — covering enumeration query path + W25 D4 Q-W25-I07 baseline)
- [ ] Backend pytest 1060 baseline preserved(regression 0)
- [ ] ruff + mypy strict on touched code clean(W26 baseline 18 pre-existing 維持)

### C. F3 commit

- [ ] Commit F3 surgical fix `feat/fix({scope}): W29 F3 {candidate} — {root cause} surgical fix + {N} NEW tests`

## F4 — User-test verify + closeout

### A. Q-W25-I07 user-test verify (PRIMARY G1)

- [ ] Backend restart via `python -m api.server` per W27 D2 lesson
- [ ] curl POST `/query` 「show me all the Integration scenarios」+ Bearer dev-token + assert citations ≥ 2 distinct chunk_ids 對應 §8.1-§8.5 A-E walkthrough(exclude intro chunk-0044 / TOC chunk-0001 / chunk-0008 / chunk-0036 by-system)
- [ ] Chat UI retry verify(user-eye secondary surface)

### B. Phase Gate G1-G5 evaluation

- [ ] G1 user-test ≥ 2 distinct A-E walkthrough citations
- [ ] G2 backend pytest 1060 baseline preserved
- [ ] G3 ruff + mypy strict on touched code clean
- [ ] G4 F1 5 audit outputs + F2 root cause report committed (evidence base)
- [ ] G5 measurement-experiment-fail-policy applied — 若 G1 FAIL → PARTIAL closeout + path (ii) CRAG threshold elevate W30+ + ADR-0034 reaffirm

### C. Cross-doc sync per CLAUDE.md §10 R3 + R5 + R6

- [ ] plan.md frontmatter `status: active → closed`(若 PASS)OR `closed_partial`(若 G1 FAIL)
- [ ] checklist.md cross-cutting 全 tick + N/A items 標明 reason
- [ ] progress.md retro 7-section + Phase Gate G1-G5 result + What worked / What didn't / Surprises / Carry-overs to W30+ / ADR triggers
- [ ] session-start.md §10 timeline row update — W29 row `🟡 active` → `✅ closed` / `✅ closed_partial 2026-05-26`
- [ ] session-start.md §11 W29 CLOSED block prepend (per W26-W28 precedent)
- [ ] RISK_REGISTER R15 status flip per result (G1 PASS → 🟢 Mitigated / G1 FAIL → preserve current + W30+ candidate log)
- [ ] COMPONENT_CATALOG.md C05 status note 1-line append (若 F3 touched reformulator / result_fusion)
- [ ] ADR README index sync (若 ADR-0034 amendment OR NEW ADR ship)

### D. `.env` cleanup + W30+ priority queue evaluation

- [ ] `.env` cleanup — 任何 F1 audit env override 移除(W29 audit 預期 read-only,但仍 sanity check)
- [ ] W30+ candidate prioritization update:
  - 若 W29 G1 PASS → path (i)(ii) decay W30+ candidates;NEW (h) Q-W25-I07-like enumeration corpus expansion candidate elevate
  - 若 W29 G1 FAIL → path (ii) CRAG threshold trial elevate per Q4 fallback(H1 boundary route — STOP+ask + ADR governance)

### E. Commit

- [ ] Commit F4 closeout `docs(planning): W29 closeout {PASS|PARTIAL} — F1-F2 diagnose + F3 {surgical fix|no-op} + Q-W25-I07 user-test {PASS|FAIL} + cross-doc sync`

---

## Cross-Cutting

- [ ] All deliverables committed to git
- [ ] All OQ status changes reflected in `docs/decision-form.md`(W29 no OQ deps expected — likely N/A)
- [ ] All architectural-adjacent decisions documented as ADR(F3 may amend ADR-0034;ship NEW ADR if F2 H2 confirms structural example-corpus alignment policy needed)
- [ ] `progress.md` retro section written
- [ ] `progress.md` frontmatter status flipped to `closed` / `closed_partial`
- [ ] Phase W30+ kickoff trigger noted in retro

---

**Lifecycle reminder**:呢份 checklist 隨 plan deliverables 衍生。新加 deliverable 必須先入 plan + changelog,然後再加 checklist item。
