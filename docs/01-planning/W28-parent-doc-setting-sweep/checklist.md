---
phase: W28-parent-doc-setting-sweep
plan_ref: ./plan.md
status: in-progress
last_updated: 2026-05-25
---

# Phase W28 — Checklist

> Atomic checkbox(每 item ≤ 1–2 hour effort)。
> AI tick 完成嘅 item;唔可以 tick 嘅 item 喺 progress Day-N entry 寫原因 + 標 🚧 reason。

## F0 — Kickoff(plan + checklist + progress + R6 grep verify)

- [x] Create `docs/01-planning/W28-parent-doc-setting-sweep/` folder
- [x] R6 pre-active-flip recursive grep verify(per CLAUDE.md §10 R6)— Settings line 198-235 actual default values + ADR-0037 §2.1+§2.3 design rationale + W27 F2 G baseline raw JSON 對齊 verified;0 historical surface contamination + plan-text 命名清空 W26/W27 inherited surface
- [x] Draft `plan.md` per W27 closed-phase template — 7-section structure + frontmatter + §2 F0-F4 deliverables + §3 G1-G6 + §4 R1-R6 + §5 D0-D3 + §6 W27 carry-overs + §7 Changelog
- [x] Draft `checklist.md` per W27 closed-phase template — atomic items derived from plan §2 deliverables
- [x] Draft `progress.md` Day 0 entry — kickoff action + commit hash placeholder
- [x] Commit `docs(planning): kickoff W28-parent-doc-setting-sweep` per CLAUDE.md §10 R1 binding(commit `1fd8806`)
- [x] session-start.md §10 timeline row update — W28 active status entry append + W29+ rolling JIT row 更新

## F1 — Step 1 max_tokens sweep(3 RAGAs runs)

### A. R8 prerequisite gate

- [x] R8 prerequisite check — keys 已 present 喺 `.env`(W27 F2 G same-session environment continuity confirmed by Run 1.A baseline duplicate ~match W27 F2 G metrics)
- [N/A] STOP and ask Chris 若 blocked — R8 green per W27 D2 same-day precedent

### B. Step 1 active flip — 3 runs sequential

- [x] **Run 1.A baseline duplicate**:`.env` append 6-line W28 F1 base block + uvicorn restart via `python -m api.server` + POST /eval/run Bearer dev-token = output `step1-run-1a-metrics-W28-D1-raw.json`(HTTP 200 / 528s runtime)
- [x] **Run 1.B max_tokens=2000**:`.env` Edit line 116 `PARENT_DOC_MAX_TOKENS_PER_PARENT=2000` + uvicorn restart + POST /eval/run = output `step1-run-1b-metrics-W28-D1-raw.json`(HTTP 200 / 476s runtime)
- [x] **Run 1.C max_tokens=1500**:`.env` Edit line 116 `PARENT_DOC_MAX_TOKENS_PER_PARENT=1500` + uvicorn restart + POST /eval/run = output `step1-run-1c-metrics-W28-D1-raw.json`(HTTP 200 / 493s runtime)

### C. Step 1 analysis

- [x] Markdown report `step1-max-tokens-sweep-W28-D1.md` — 3 runs aggregate metrics + per-query 4-metric + Step 1 best max_tokens pick(Run 1.B max_tokens=2000)by G3 critical PASS + G1 closest to F1 tolerance + Step 2 base config
- [x] H2 hypothesis check:**PARTIALLY CONFIRMED + counterintuitive surfaced** — faithfulness 提升 with max_tokens reduction(2000 most)but correctness reverse(coverage truncation)+ latency 唔係 monotonic(1500 lowest,2000 highest)+ failed queries 數 increase with reduction(9→10→11)
- [x] Eval-to-eval variance documented(W27 vs W28 Run 1.A Q-W25-I07 + Q-W25-I01 borderline judge flip)

### D. Commit

- [ ] Commit F1 Step 1 `docs(eval): W28 F1 Step 1 max_tokens sweep — 3 RAGAs runs / best pick max_tokens=2000 / H2 PARTIALLY CONFIRMED`

## F2 — Step 2 top_k sweep(2 NEW RAGAs runs)

### A. Step 2 active flip — 2 NEW runs

- [ ] **Run 2.A top_k=2**:`.env` 改 `PARENT_DOC_TOP_K=2`(holding `PARENT_DOC_MAX_TOKENS_PER_PARENT=<Step 1 best>` + dispatch_mode=append)+ uvicorn restart + POST /eval/run = output `step2-run-2a-metrics-W28-D2-raw.json`
- [ ] **Run 2.B top_k=3**:`.env` 改 `PARENT_DOC_TOP_K=3` + uvicorn restart + POST /eval/run = output `step2-run-2b-metrics-W28-D2-raw.json`

### B. Step 2 analysis

- [ ] Markdown report `step2-top-k-sweep-W28-D2.md` — 2 NEW runs aggregate metrics + cross-reference Step 1 top_k=1 best max_tokens combo + best combo pick by G1-G5 aggregate score(加 latency G5)
- [ ] Hypothesis check:top_k 加大 是否擴大 multi-section coverage benefit 而唔 trigger off-topic leak regression?

### C. Commit

- [ ] Commit F2 Step 2 `docs(eval): W28 F2 Step 2 top_k sweep — 2 NEW RAGAs runs delta + best combo pick`

## F3 — Step 3 (optional) dispatch_mode cross-check

### A. Trigger evaluation

- [ ] Best combo achieves G1-G5 PASS?If yes → proceed F3;If no → skip F3 直接 F4 closeout

### B. Step 3 active flip — 1 NEW run(if triggered)

- [ ] **Run 3.A dispatch_mode=replace at best combo**:`.env` 改 `PARENT_DOC_DISPATCH_MODE=replace`(holding best max_tokens + best top_k)+ uvicorn restart + POST /eval/run = output `step3-dispatch-cross-check-W28-D3-raw.json`

### C. Step 3 analysis

- [ ] Markdown report `step3-dispatch-cross-check-W28-D3.md` — replace vs append at best combo comparison + final default flip recommendation

### D. Commit

- [ ] Commit F3 Step 3 `docs(eval): W28 F3 Step 3 dispatch_mode cross-check at best combo — replace vs append final delta`

## F4 — Closeout — ADR analysis + W29+ decision tree + cross-doc sync

### A. Phase Gate G1-G6 evaluation against best combo

- [ ] G1 best combo faithfulness vs F1 baseline ±2pp [0.9651, 1.0]
- [ ] G2 best combo correctness vs F1 baseline ±2pp [0.7216, 0.7616]
- [ ] G3 Q-W25-I07 PASS preserved(critical recovery from W26 F2 G 0.00 不可 regress)
- [ ] G4 Q-W25-I01 控制組 ≥ F1 baseline ± 0.05(close W27 marginal MISS 0.01pp)
- [ ] G5 best combo p95_latency reduced vs W27 (2897ms)— target < 1500ms ideal,< 2000ms acceptable
- [ ] G6 measurement-experiment-fail-policy applied

### B. ADR governance per G result

- [ ] G result determination — full PASS / partial / NEW catastrophic regression?
- [ ] **若 full PASS** → ADR-0037 amendment full Settings flip:
  - [ ] `parent_doc_max_tokens_per_parent` default flip 4000 → <best value>
  - [ ] `parent_doc_top_k` default flip 1 → <best value>
  - [ ] `parent_doc_dispatch_mode` default flip per Step 3 result
  - [ ] `enable_parent_doc_retrieval` default flip 評估(若 robust → propose flip True;否則 preserve False)
- [ ] **若 G1+G4 仍 marginal MISS by < 0.5pp** → ADR-0037 amendment partial flip(Settings 改 best values + `enable_parent_doc_retrieval` 仍 OFF)
- [ ] **若 NEW catastrophic regression** → NEW ADR-0039 documents no-improvement finding + W29+ candidate (c) elevated + Settings preserve W27 state

### C. Cross-doc sync per CLAUDE.md §10 R3 + R5 + R6

- [ ] plan.md frontmatter `status: active → closed`(若 PASS)OR `closed_partial`(若 marginal / NEW regression)
- [ ] checklist.md cross-cutting 全 tick + N/A items 標明 reason
- [ ] progress.md retro 7-section + Phase Gate G1-G6 result + What worked / What didn't / Surprises / Carry-overs to W29+ / ADR triggers
- [ ] session-start.md §10 timeline row update — W28 row `🟡 active` → `✅ closed` / `✅ closed_partial 2026-05-25`
- [ ] session-start.md §11 W28 CLOSED block prepend(per W26+W27 PARTIAL precedent)
- [ ] RISK_REGISTER R-W26-1 + R-W26-2 status flip per result
- [ ] COMPONENT_CATALOG.md C05 status note 1-line append
- [ ] ADR README index sync(若 ADR-0037 amendment OR ADR-0039 ship — row + footer next-NNNN update)

### D. `.env` cleanup + W29+ priority queue evaluation

- [ ] `.env` cleanup — W28 F1-F4 env override marker block removed per Karpathy §1.3 surgical(restore post-closeout production state)
- [ ] W29+ candidate prioritization update(per Phase Gate result):
  - 若 W28 full PASS → ADR-0037 amendment ship 完成,W29+ candidate (b) decay → (c) RAGAs orchestrator-aware tune + (d) F3 query expansion + (e) BUG-026/027 cosmetic 重新排序
  - 若 W28 marginal MISS → (c) elevated 為 HIGHEST priority candidate
  - 若 W28 catastrophic regression → (c) MANDATORY next phase

### E. Commit

- [ ] Commit F4 closeout `docs(planning): W28 closeout {PASS|PARTIAL} — F1-F2 sweep best combo + Settings default flip{|preserved} + ADR-0037 amendment{|0039 ship} + cross-doc sync`

---

## Cross-Cutting

- [ ] All deliverables committed to git
- [ ] All OQ status changes reflected in `docs/decision-form.md`(若 任何 OQ resolved — 預期無)
- [ ] All architectural-adjacent decisions documented as ADR — ADR-0037 amendment OR NEW ADR-0039
- [ ] `progress.md` retro section written
- [ ] `progress.md` frontmatter status flipped to `closed` OR `closed_partial`
- [ ] Phase W29+ kickoff trigger noted in retro

---

**Lifecycle reminder**:呢份 checklist 隨 plan deliverables 衍生。新加 deliverable 必須先入 plan + changelog,然後再加 checklist item。
