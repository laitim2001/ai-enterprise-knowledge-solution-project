---
phase: W29-reformulator-diagnose
name: "Reformulator behavior diagnose — H1 RRF surface / H2 vocab-corpus mismatch / H3 fallback gap audit before any code change (path iii ALREADY shipped per W25 F3 D4)"
sprint_week: W29
start_date: 2026-05-26
end_date: 2026-05-26    # same-day collapse expected per W22-W28 AI compression pattern; extend to 2026-05-27 if F3 surgical fix scope expands
status: active
spec_refs:
  - architecture.md §3.1      # query pipeline (reformulator + RAG-fusion locus per ADR-0034)
  - architecture.md §3.5      # ChunkRecord citation contract preservation
prior_phase: W28-parent-doc-setting-sweep
trigger_memo: |
  W28 closeout `42c699f` + `c20530b` ship parent-doc Setting full default flip but G3 Q-W25-I07 仍 borderline marginal MISS (context_recall 0.40 per 8-run cross-config flip 3 PASS / 5 FAIL = judge noise treated as not config-induced)。
  W19+ candidate (g) NEW Synthesizer enumeration-refuse fix via path (iii) F3 reformulator strengthening originally proposed as path forward。**R6 Day 0 recursive verify catch**:`backend/generation/query_reformulator.py` line 47-89 REFORMULATOR_SYSTEM_PROMPT 已包含 (a) enumeration query shape detection bullet (2) + (b) **EXAMPLE 3 line 78-84 直接 cover Q-W25-I07** specific decomposition(W25 F3 D4 ship)+ `.env` ENABLE_QUERY_EXPANSION=true(2026-05-24 W25 D3 enabled)。即 path (iii) strengthening **已經 ship**;真正未驗證係:**Strengthened reformulator + W28 best combo Settings 下,點解 Q-W25-I07 G3 仍 marginal MISS**。
related_adrs: [0034]   # may amend ADR-0034 if F3 surgical fix touches reformulator behavior; may ship NEW ADR-0039 if F2 H2 hypothesis confirmed needs corpus-aware example tuning policy
---

# Phase W29 — Reformulator Diagnose (audit-first)

> **Plan version**:1.0(initial)
> **Owner**:Chris(技術 Lead)+ AI(implementation)
> **Approved by**:Chris(chat 2026-05-26 — 「執行 (g) Synthesizer enumeration-refuse fix via path (iii)」+ AskUserQuestion 4 Recommended picks:Phase classification / Surgical scope / User-test only primary gate / PARTIAL fallback;**R6 recursive catch 觸發 second AskUserQuestion 2026-05-26**:「W29-reformulator-diagnose H1+H2+H3 audit 先(Recommended)」— scope redirect from「prompt strengthening」to「diagnose before any code change」per Karpathy §1.1 think-before-coding)
> **Trigger memo**:R6 Day 0 catch surfaced path (iii) ALREADY shipped → W29 scope redirect from「strengthening」to「diagnose root cause of Q-W25-I07 G3 marginal MISS under W28 best combo + ENABLE_QUERY_EXPANSION=true config」

## 1. Scope

### 1.1 R6 Day 0 catch (critical context)

**Catch detail**:

| Plan-text 假設(用戶提名「path (iii) reformulator strengthening」)| Code Reality(現有 prompt 已 ship per W25 F3 D4)|
|---|---|
| 加 enumeration query shape detection | ✅ `REFORMULATOR_SYSTEM_PROMPT` Bullet (2) literal:「When the original uses words like "all", "every", "each", "list", or "show me the X" — decompose into variants that target SPECIFIC INSTANCES or categories rather than just rephrasing "all" → "every"」 |
| 加 scenario-specific few-shot example | ✅ **EXAMPLE 3 line 78-84 直接 cover Q-W25-I07**:`Original: "show me all the integration scenarios" / Good variants: ["customer service request submission API integration", "Saga-style multi-system orchestration pattern", "inbound event-driven flow Service Bus"]` |
| 教 LLM 避免「all → every」rephrase | ✅ EXAMPLE 3 Bad variants 已示範:`["all integration scenarios", "every integration pattern", "list integration use cases"]` |

呢段 prompt **完全就係** W29 提議要做嘅 strengthening。即 path (iii) 嘅 fix **已經 in code base** since W25 F3 D4(ADR-0034 ship 2026-05-24)。連帶 verify:

- `.env` 現狀:`ENABLE_QUERY_EXPANSION=true`(W25 D3 enabled,W26-W28 phase eval 都行緊 reformulator path)
- W25 D4 daily log Q-W25-I07 refuse 當時:`.env` 仲未 enable(`grep ENABLE_QUERY_EXPANSION .env` empty) — chat retry 行嘅 single-query baseline,**未行過呢個 strengthened reformulator path**
- W26-W28 eval run 行嘅 reformulator path → 但 Q-W25-I07 G3 仍 marginal MISS(W28 context_recall 0.40)

**核心未答問題**:Strengthened reformulator(EXAMPLE 3 直接 cover Q-W25-I07)+ W28 best combo Settings(replace + top_k=2 + max_tokens=2000)+ ENABLE_QUERY_EXPANSION=true config 下,**actual reformulator behavior + RAG-fusion fan-out + RRF top-5 surface 點解仍未 close G3**?

### 1.2 Diagnose-first scope(per Karpathy §1.1 + §1.4 verifiable goal)

W29 **唔做** code change for path (iii) prompt strengthening(已 ship)。F1 H1+H2+H3 audit 先,F2 root cause confirm,F3 **基於 confirmed root cause** 嘅 surgical fix(若需要),F4 user-test verify + closeout。

### 1.3 Three diagnose hypotheses

| Hypothesis | 描述 | F1 audit handle |
|---|---|---|
| **H1 RRF surface** | Reformulator 生對咗 variants(EXAMPLE 3 effective)但 RAG-fusion RRF k=60 仍 surface intro chunks(chunk-0044 / chunk-0055 / chunk-0008 / chunk-0001 / chunk-0036)而非 §8.1-§8.5 individual walkthrough — 即 fusion 層 problem | F1.1 capture actual variants + F1.3 inspect RRF top-5 chunk_ids surface |
| **H2 vocab-corpus mismatch** | EXAMPLE 3 hypothetical variants(「customer service request submission」/「Saga」/「Batch ETL」)同 actual corpus §8.1-§8.5 chunk vocab **唔啱**(corpus 可能用「Order processing flow」/「Service request handling」之類 terms)— 即 example-corpus alignment 唔啱 | F1.2 grep corpus §8.1-§8.5 chunk text + F1.4 對比 EXAMPLE 3 hypothetical variants vocab |
| **H3 fallback gap** | Reformulator path 偶然會 fallback to `[original]`(timeout / parse error)然後行 single-query baseline → 同 W25 D4 default-off path 一樣 — observability gap | F1.5 check Langfuse `query_reformulator.reformulate` event fallback rate 喺 W26-W28 eval run |

### 1.4 Out of scope(deferred)

- ❌ **path (i) synthesizer system prompt tune**(per user pick Surgical scope — out of W29;留 W30+ if F3 surgical insufficient)
- ❌ **path (ii) CRAG threshold change**(`Settings.crag_confidence_threshold` 0.70 → 0.60)— **H1 boundary trigger** per `architecture.md §3.1` CRAG L2 spec → 若 G1 PARTIAL,elevate W30+ per chose fallback option
- ❌ W28 best combo Settings 改變(`parent_doc_top_k` / `max_tokens` / `dispatch_mode` 維持 W28 amended defaults — preserve W28 PASS gate)
- ❌ Reformulator hyper-param tune(`max_variants` 3→5 / `QUERY_EXPANSION_PER_VARIANT_OVERFETCH` 4→6 / `QUERY_EXPANSION_LATENCY_CAP_S` 8.0 boundary)— 留 F3 candidate if H1 confirmed
- ❌ RAGAs 4-metric full eval re-run(per user pick acceptance「User-test only」)— 若 F3 surgical fix 直接 close G1,毋須 eval delta verification
- ❌ Enumeration corpus expansion(per user pick acceptance — out of W29 scope)
- ❌ `architecture.md` inline-tagged amendment(measurement-experiment policy 唔污染 spec until clear measurable win)

### 1.5 Sprint week origin

**W19+ rolling JIT**(per CLAUDE.md §10 R1 + session-start.md §10 W29+ row);呢個 phase **唔喺 architecture.md §6.1 原 W1-W12 sprint 表內** — 屬 W28 closeout 觸發嘅 follow-up audit-first fix(類似 W25.5 BUG-025 / W27-dispatch / W28-sweep rolling 性質)。

---

## 2. Deliverables

### F0 — Kickoff(plan + checklist + progress + R6 grep verify)— **DONE Day 0**

- **Spec ref**:CLAUDE.md §10 R1 + R6
- **H1 trigger**:否(governance only)
- **Acceptance criteria**:
  1. ✅ `docs/01-planning/W29-reformulator-diagnose/{plan.md,checklist.md,progress.md}` committed
  2. ✅ R6 Day 0 recursive grep verify — `backend/generation/query_reformulator.py` line 47-89 REFORMULATOR_SYSTEM_PROMPT actual content verified vs plan-text 假設(MISMATCH catch — path iii 已 ship W25 F3 D4 → scope redirect this Day 0)
  3. ✅ session-start.md §10 timeline row W29 active status entry append + W28 closed_block §11 preserved
- **Effort estimate**:~1-2h
- **Owner**:AI

### F1 — H1+H2+H3 Diagnose(audit-only,no code change)

- **Spec ref**:ADR-0034 §Design + REFORMULATOR_SYSTEM_PROMPT line 47-89
- **H1 trigger**:否(diagnose only)
- **OQ deps**:**R8 prerequisite**(Azure OpenAI judge key for reformulator live call;same key as W28)
- **Acceptance criteria**(5 sub-deliverables):

  **F1.1 Capture actual reformulator variants on Q-W25-I07**:
  - Method:Backend running with `ENABLE_QUERY_EXPANSION=true` + W28 amended Settings + `enable_parent_doc_retrieval=False` per Q4 → POST `/query` with Q-W25-I07 「show me all the Integration scenarios」via curl + Bearer dev-token → grep structlog `query_reformulator_complete` event for `variants_text` field
  - Output:`f1-1-reformulator-variants-W29-D0-raw.txt` containing actual reformulator output(N variants generated + reformulator latency_ms + fallback_used flag + variants_text list)

  **F1.2 Grep corpus §8.1-§8.5 chunk text**:
  - Method:Either `/kb/{kb_id}/chunks` listing 過濾 chunk_id range / Azure AI Search direct query / Cosmos DB inspect → extract §8.1-§8.5 individual walkthrough chunks 嘅 first 300 chars + section_path
  - Output:`f1-2-corpus-vocab-W29-D0-raw.txt` containing §8.1-§8.5 chunk text excerpts

  **F1.3 Inspect RRF fusion top-5 surface**:
  - Method:Backend `/query` response JSON 取出 `retrieved_chunks` (or `debug_meta.rrf_top_5` if surface 喺 stream_composer) → 確認 W26-W28 eval 行 Q-W25-I07 嘅 final reranked top-5 chunk_ids
  - Output:`f1-3-rrf-top5-W29-D0-raw.txt` containing top-5 chunk_ids + scores

  **F1.4 對比 EXAMPLE 3 hypothetical variants vs corpus actual vocab**:
  - Method:Manual diff F1.1 actual variants(or EXAMPLE 3 literal「customer service request submission API integration」/「Saga」/「Batch ETL」)vs F1.2 §8.1-§8.5 chunk text actual vocab tokens
  - Output:`f1-4-vocab-mismatch-analysis-W29-D0.md` markdown — overlap rate + missed corpus tokens + alignment verdict

  **F1.5 Check Langfuse `query_reformulator.reformulate` fallback rate W26-W28**:
  - Method:Langfuse UI traces filter 過 `query_reformulator.reformulate` events 喺 W26 F2 G + W27 F2 G + W28 Run 1/2/3 eval batches → 計 fallback_used=True 比率
  - Output:`f1-5-reformulator-fallback-rate-W29-D0-raw.txt` per-eval fallback rate
  - Alternative if Langfuse access blocked:read latest backend.log + grep `query_reformulator_failed_using_original` OR `query_reformulator_timeout` events

- **Effort estimate**:~2-3h (F1.1+F1.3 single live call ~10 min;F1.2 corpus inspect ~30 min;F1.4 manual diff ~1h;F1.5 Langfuse OR log grep ~30 min)
- **Owner**:AI

### F2 — Root cause confirm + markdown report

- **Spec ref**:F1 outputs aggregated
- **H1 trigger**:否
- **OQ deps**:F1 5 outputs committed
- **Acceptance criteria**:
  1. Markdown report `f2-root-cause-W29-D1.md` — 6 sections:F1.1-F1.5 evidence summary / H1 RRF surface verdict / H2 vocab-corpus mismatch verdict / H3 fallback gap verdict / Confirmed primary root cause / F3 surgical fix path proposal
  2. Root cause classification:**H1 dominant** / **H2 dominant** / **H3 dominant** / **H1+H2 combined** / **None — judge non-determinism alone**(若 reformulator output + RRF surface + fallback rate 全部 looks healthy,Q-W25-I07 G3 marginal MISS 就 confirmed 係 W28 已 caught 嘅 judge noise per 8-run flip evidence — F3 = no-op surgical fix)
- **Effort estimate**:~1-2h
- **Owner**:AI

### F3 — Surgical fix based on confirmed root cause(scope-conditional)

- **Spec ref**:varies by F2 root cause classification
- **H1 trigger**:可能(per root cause — see below)
- **OQ deps**:F2 root cause confirmed

  **若 F2 verdict = H1 RRF dominant** → F3 surgical:
  - Candidate (a) RAG-fusion overfetch tune — `QUERY_EXPANSION_PER_VARIANT_OVERFETCH` 4→6 / 8(目前 .env value=4)
  - Candidate (b) RRF `k` parameter tune in `backend/retrieval/result_fusion.py`(目前 k=60 per ADR-0034)
  - 唔屬 H1 boundary(`result_fusion.py` 屬 ADR-0034 framework 內;tune Setting 唔改 vendor / storage layout)

  **若 F2 verdict = H2 vocab-corpus mismatch dominant** → F3 surgical:
  - Candidate (c) EXAMPLE 3 vocab replace — 用 F1.2 actual corpus tokens 取代 hypothetical「customer service request submission」/「Saga」/「Batch ETL」
  - 唔屬 H1 boundary(prompt tune within ADR-0034 framework)
  - 可能 amend ADR-0034 per ADR-0017 5-amendment precedent + same decision family rationale

  **若 F2 verdict = H3 fallback gap dominant** → F3 surgical:
  - Candidate (d) `QUERY_EXPANSION_LATENCY_CAP_S` 8.0 tune(目前 .env value=8.0)— 增加 → 降低 timeout fallback rate
  - Candidate (e) reformulator error handling strengthen(per `query_reformulator.py` line 225-240 broad exception path)
  - 唔屬 H1 boundary

  **若 F2 verdict = None / judge noise alone** → F3 = **no-op surgical fix**:
  - 文件化 finding;G1 user-test 可能 仍 fail 但 mark PARTIAL closeout per Q4 measurement-experiment-fail-policy
  - W30+ candidate path (ii) CRAG threshold trial elevate(per user chose fallback)

- **Acceptance criteria**(scope-conditional):
  1. F3 fix candidate implementation(若 non-no-op)
  2. F3 unit test 2+ NEW(若 reformulator prompt OR result_fusion touched — covering enumeration query path + W25 D4 Q-W25-I07 baseline)
  3. Backend pytest 1060 baseline preserved(regression 0)
  4. ruff + mypy strict on touched code clean(per existing W26 baseline 18 errors per `CO_W25_mypy_strict_debt` 維持)

- **Effort estimate**:varies — ~30 min (no-op) / ~2-3h (surgical Setting tune) / ~4-6h (prompt/code change + tests)
- **Owner**:AI

### F4 — User-test verify + closeout

- **Spec ref**:CLAUDE.md §12 self-verification + §10 R3+R5
- **H1 trigger**:否
- **OQ deps**:F3 done(or F3 no-op decision committed)
- **Acceptance criteria**:

  **A. Q-W25-I07 user-test verify**(PRIMARY gate G1):
  1. Backend restart via `python -m api.server` per W27 D2 lesson
  2. curl POST `/query` 「show me all the Integration scenarios」+ Bearer dev-token + assert response JSON `citations` array 包含 ≥ 2 distinct chunk_ids 對應 §8.1-§8.5 A-E walkthrough sections(non-intro chunk-0044 / non-TOC chunk-0001 / non-by-system chunk-0036)
  3. Chat UI retry verify(secondary user-eye surface)— user 親自 retry Q-W25-I07 確認 2 A-E walkthrough citations rendered

  **B. Phase Gate G1-G5 evaluation**(per §3 below):
  4. G1 user-test ≥ 2 distinct A-E walkthrough citations
  5. G2 backend pytest 1060 baseline preserved
  6. G3 ruff + mypy strict on touched code clean
  7. G4 F1 5 audit outputs + F2 root cause report committed(evidence base)
  8. G5 measurement-experiment-fail-policy applied — 若 G1 FAIL → PARTIAL closeout

  **C. Cross-doc sync per CLAUDE.md §10 R3+R5**:
  9. plan.md frontmatter `status: active → closed`(若 PASS)/ `closed_partial`(若 G1 FAIL)
  10. checklist.md cross-cutting tick + N/A standout reason
  11. progress.md retro 7-section(What worked / didn't / Surprises / Carry-overs to W30+ / ADR triggers / Phase Gate G1-G5 result / Phase status)
  12. session-start.md §10 W29 row `🟡 active` → `✅ closed` / `✅ closed_partial 2026-05-26`
  13. session-start.md §11 W29 CLOSED block prepend
  14. RISK_REGISTER R15(若 G1 PASS → flip 🟢 Mitigated)/(若 G1 FAIL → preserve current state + log W30+ candidate)
  15. COMPONENT_CATALOG.md C05 status note 1-line append(若 F3 touched reformulator / result_fusion)
  16. ADR README index sync(若 ADR-0034 amendment OR NEW ADR ship)

  **D. `.env` cleanup**:
  17. `.env` restore — 任何 F1 audit env override 移除(W29 audit 預期 read-only,但若 F1.1 加 debug env var 要清乾淨)

  **E. Commit**:
  18. F4 closeout commit `docs(planning): W29 closeout {PASS|PARTIAL} — F1-F2 diagnose + F3 {surgical fix|no-op} + Q-W25-I07 user-test {PASS|FAIL} + cross-doc sync`

- **Effort estimate**:~2-3h
- **Owner**:AI

---

## 3. Phase Gates (G1-G5)

| Gate | 描述 | Pass criteria | Fail action |
|---|---|---|---|
| **G1 (PRIMARY)** | Q-W25-I07 user-test ≥ 2 distinct A-E walkthrough citations | curl /query response citations array contains ≥ 2 chunk_ids from §8.1-§8.5 range (exclude chunk-0044 intro / chunk-0001 TOC / chunk-0008 platform composition / chunk-0036 by-system patterns) | PARTIAL closeout per G5 |
| **G2** | Backend pytest regression 0 | `pytest tests/` = 1060 + 25 skipped + 0 failed (W28 baseline preserved) | STOP and fix |
| **G3** | ruff + mypy strict on touched code clean | `ruff check` + `mypy --strict` on touched files = 0 NEW errors (W26 baseline 18 pre-existing per `CO_W25_mypy_strict_debt` 維持) | STOP and fix |
| **G4** | F1 5 audit outputs + F2 root cause report committed | F1.1-F1.5 raw outputs + F2 markdown report exist in `docs/01-planning/W29-reformulator-diagnose/` + committed to git | STOP — F2 cannot conclude without F1 evidence |
| **G5** | Measurement-experiment-fail-policy applied if G1 FAIL | 若 G1 FAIL → PARTIAL closeout + path (ii) CRAG threshold elevate W30+ candidate (per user chose fallback) + 唔自動 revert W28 best combo Settings + ADR-0034 reaffirm | proceed PARTIAL closeout per Q4 |

---

## 4. Rules (R1-R6 per CLAUDE.md §10 + EKP discipline)

- **R1** Plan committed before any code change(this commit landing = R1 satisfied for W29)
- **R2** Daily commit ↔ progress.md Day-N entry mapping
- **R3** Plan deviation → §7 changelog mandatory(no silent drift)
- **R4** OQ resolved → decision-form.md + progress Day-N mention(W29 no OQ deps expected)
- **R5** Architectural-adjacent → ADR(F3 may amend ADR-0034 if prompt tune;ship NEW ADR if F2 H2 confirms structural example-corpus alignment policy needed)
- **R6** Pre-active-flip 5-step grep verify(per CLAUDE.md §10 R6)— **already applied Day 0** to surface path (iii) shipped catch;reapply at F1+F2+F3 active flip per recursive scope

---

## 5. Dependencies

- **D0** Azure OpenAI judge key(`AZURE_OPENAI_API_KEY` + `AZURE_OPENAI_DEPLOYMENT_LLM_JUDGE` per .env)present for live reformulator call(F1.1)
- **D1** Backend running with `ENABLE_QUERY_EXPANSION=true` + W28 amended Settings active(default `parent_doc_top_k=2` + `parent_doc_max_tokens_per_parent=2000` + `parent_doc_dispatch_mode="replace"` + `enable_parent_doc_retrieval=False`)— current .env confirms
- **D2** drive_user_manuals KB indexed in Azure AI Search `ekp-kb-drive-v1`(for /query + corpus chunk listing)

---

## 6. Prior Phase Carry-overs

### From W28 closeout retro

- **(c) RAGAs orchestrator-aware judge tune per R-W26-2** — 大幅降低 priority per W28 close G1+G2+G4+G5;W29 G3-targeting alternative(via reformulator audit)— **W29 嘗試 close G3 from retrieval-side rather than judge-side**
- **(d) F3 query expansion standalone test** per ADR-0034 — overlap with W29 F1.1+F1.2(W29 audit subsumes standalone test enumeration scope)
- **NEW (e) `make_ragas_evaluator` structlog stage emit** — orthogonal axis,W30+ candidate retain
- **NEW (f) Settings-default-tests** — orthogonal axis,W30+ candidate retain
- **BUG-026 + BUG-027** cosmetic — preserved untouched
- **W22 D8 setup.md §8.6 uvicorn entry doc completion** — preserved untouched
- **W16 F1-F4 Track A IT cred** parallel track — preserved untouched

### From W25 D4 daily log + memory `project_synthesizer_overview_refuse_w25_d4.md`

- R14 → R15 supersede(W25.5 BUG-025)trajectory preserved
- 3 mitigation paths catalogued:(i) synthesizer prompt / (ii) CRAG threshold / (iii) reformulator
- W25 F3 D4 EXAMPLE 3 ship already covers Q-W25-I07 specific decomposition(R6 Day 0 catch)
- W26-W28 eval ENABLE_QUERY_EXPANSION=true confirmed but G3 仍 marginal — W29 audit-first to confirm WHY

---

## 7. Changelog

| Version | Date | Author | Change |
|---|---|---|---|
| 1.0 | 2026-05-26 | AI + Chris | Initial plan committed Day 0;**R6 Day 0 catch** — path (iii) prompt strengthening ALREADY shipped W25 F3 D4 + EXAMPLE 3 cover Q-W25-I07 + `.env` ENABLE_QUERY_EXPANSION=true → scope redirect from「strengthen reformulator」to「diagnose-first H1+H2+H3 audit before any code change」per Karpathy §1.1 think-before-coding + user AskUserQuestion 2nd Recommended pick;**path (i) synthesizer prompt + path (ii) CRAG threshold deferred W30+** per user chose Surgical scope option |

---

**Plan binding**:per CLAUDE.md §10 R1 — no W29 code change until this plan committed + checklist + progress kickoff Day 0 entry committed in same housekeeping commit per W22-W28 same-day kickoff pattern。
