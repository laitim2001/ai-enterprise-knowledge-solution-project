---
phase: W04-crag-eval-shootout
plan_ref: ./plan.md
checklist_ref: ./checklist.md
status: in-progress     # draft → in-progress → closed; flipped 2026-05-04 W4 D1 kickoff
---

# Phase W04 — Progress

> Daily progress + 結尾 retro。
> 每 commit 必須對應一個 Day-N entry mention(R2 binding rule per PROCESS.md §5)。
> Status:`draft` 直到 W3 D5 closeout sign-off + W4 kickoff approval。

---

## Day 0 — 2026-05-04: Kickoff prep(W3 D5 末 closeout 同 session)

**Action**:Phase W04 kickoff prep(per PROCESS.md §2.3 rolling-JIT lifecycle + W3 D5 closeout 同 session per CLAUDE.md §10 R5)

- Folder `docs/01-planning/W04-crag-eval-shootout/` created
- `plan.md` filled with status=`draft`(10 deliverables F1-F10:CRAG L2 + RAGAs eval automation + 4-way reranker shootout + 20-query eval expansion + Cohere/GPT-5.5/SSE live verify + design note bumps + PPT orchestrator wire + Gate 2 verdict)
- `checklist.md` derived from plan deliverables(~70 atomic items)
- `progress.md` Day 0 entry initialized(this file)
- **Carry-over candidates from W03-chat-retrieval-citation**(per W3 retro § Carry-overs C1-C8):
  - C1 Cohere live verify → **F5**(Marketplace endpoint procurement Chris async)
  - C2 GPT-5.5 latency baseline → **F6**(Chris dev server smoke)
  - C3 SSE live verify → **F7**(Chris dev server smoke)
  - C4 Frontend dev server smoke(Chris responsibility — every-day implicit;non explicit deliverable)
  - C5 Reranker per-KB field reconsideration → post **F3** shootout outcome
  - C6 PPT orchestrator wire → **F9**
  - C7 F8 wizard polish → W7+ Beta polish window(unchanged from W3)
  - C8 plan estimates calibration → W4 plan applies 0.5x heuristic(每 deliverable 1.5-2h baseline,vs W3 plan 4-6h estimates)— see plan §2 effort
- **Gate 2 critical context**:Per architecture.md §6.3,Gate 2 4-metric within 5pp 互換 between Cohere baseline + winning shootout reranker = PASS。FAIL = drop L2 CRAG;W5 转 baseline-only scope。This is the most important quality gate of Tier 1
- **Procurement dependencies surfaced for W4 D1**:
  - Cohere Marketplace endpoint(7-14d turnaround from 2026-05-04)
  - Voyage rerank-2.5 API key(direct,non-Azure path)
  - ZeroEntropy zerank-1 API key(direct,non-Azure path)
  - Azure semantic ranker(built-in S1 SKU,no procurement)

**Status update will follow at W3 D5 closeout commit**(W3 frontmatter `active → closed` + Chris approve W4 kickoff → W4 status `draft → active`)。If W3 G2/G3 hard gates FAIL → W4 plan **does not flip active**;HALT POC per architecture.md §6.3,foundation iteration loop replaces W4。

---

## Day 1 — 2026-05-04 (Mon — same-day W3 D5 closeout per "啟動 W4 D1" signal)

> Per plan §5 D1 = F1 CRAG core + F8 component design notes + F9 PPT orchestrator wire。Same-day W3-W4 momentum continues。Procurement carry-overs(Voyage / ZeroEntropy keys + Cohere endpoint populate)remain async — F3 / F5 await keys per plan §4 R1+R2。

### Done

#### F1 — CRAG L2 correction loop(C05 generation)

- `backend/generation/crag.py` ✅ NEW(per architecture.md §3.5 + components/C05-generation.md §2):
  - `CragGrader` class wrapping `AsyncAzureOpenAI` chat.completions(deployment=`gpt-5-4-mini` per `Settings.azure_openai_deployment_llm_judge`)
    - `grade(query, chunks) → GradeResult` returns numeric confidence ∈ [0, 1] + raw text + token counts + latency。Empty chunks short-circuit → confidence 0.0 + no API call
    - `rewrite_query(query, chunks) → RewriteResult` generates reformulated query。Multi-line response defensively trimmed to first non-empty line
    - tenacity retry on `RateLimitError` + `APITimeoutError`(3 attempts exponential 1-8s)
  - `CragLoop` orchestrator:`refine(query, initial_result, initial_synth) → CragOutcome`
    - Threshold from `Settings.crag_confidence_threshold`(default 0.70 not 0.6 plan-draft — 0.6 too lenient triggers correction rarely;0.70 better surfaces low-confidence cases for tuning)
    - max_corrections from `Settings.crag_max_reformulations`(default 1 = L2 baseline;L3 routing W5 conditional)
    - `expanded_top_k=20` for re-retrieve(plan §F1 default)
    - 4 graceful fallback paths(grader failure → no-op outcome / rewrite failure / rewrite empty / re-retrieve failure / re-synth failure)— 全部 return initial synthesis with `fallback_used=True` + `error_messages` list for trace
    - Optional second-pass grade for `confidence_after`(non-fatal if fails;informs Gate 2 lift analysis)
  - `_parse_confidence(raw_text)` regex `^\s*([+-]?\d*\.?\d+)\s*$` + fallback any-float-in-text + clamp [0, 1] + 0.0 on parse fail
  - structlog `crag_loop` event:threshold / triggered / iterations / confidence_before / confidence_after / fallback_used / 4 token counts(grader / rewrite / extra synth)/ crag_latency_ms / errors
- `backend/api/server.py` lifespan:`CragGrader` init from same Azure OpenAI endpoint+key but `azure_openai_deployment_llm_judge`(GPT-5.4-mini);`CragLoop` constructed wrapping `app.state.retrieval_engine` + `synthesizer` + `crag_grader`;`app.state.crag_loop` populate when keys present。`__aexit__` cleanup added for grader before synthesizer
- `backend/api/routes/query.py` `/query` non-stream path:if `crag_loop` set AND `payload.enable_crag` → invoke `crag_loop.refine()` after initial synthesize → use outcome.synthesis + outcome.chunks for `QueryResponse.answer/citations`;`crag_triggered` + `crag_iterations` populated from CragOutcome。Stream path unchanged(L3-only per architecture.md §3.5 — token-by-token UX precludes mid-stream rewrite)
- `backend/tests/test_crag.py` ✅ NEW — 14 tests pass:
  - 7 `_parse_confidence` parser tests(simple decimal / leading whitespace+newline / clamps above 1.0 / clamps below 0.0 / first-float-in-text fallback / empty / no-number)
  - 2 `CragGrader.grade` tests(empty chunks short-circuit no API call / parses numeric)
  - 5 `CragLoop.refine` integration tests(above-threshold no-op / below-threshold full correction with grade2 / re-synth failure fallback / grader-outright-failure no-op / rewrite-empty fallback)

#### F8 — Component design note status bumps(W3 G4 close)

- `docs/02-architecture/components/C04-retrieval.md` ✅ `v1-active → v2-stable`:hybrid + Cohere wire + factory + 4-way shootout surface ready W4 D1
- `docs/02-architecture/components/C05-generation.md` ✅ `v0-draft → v1-active`:synthesizer(W3 D2 F2)+ citation enrichment(W3 D2 F3)+ SSE stream composer(W3 D3 F4)+ CRAG L2(W4 D1 F1)
- `docs/02-architecture/components/C08-api-gateway.md` ✅ `v2-stable` updated with W3-W4 deliverables narrative(/query full RAG + /query/stream SSE + CragLoop optional refinement)
- `docs/02-architecture/components/C09-admin-ui.md` ✅ `v0-draft → v1-active`:6 routes scaffold(W1)+ admin views W2 D5 + Pipeline wizard W3 D5 F8 + Settings confirm done。shadcn polish W7+ Beta deferred
- `docs/02-architecture/components/C10-chat-ui.md` ✅ `v0-draft → v1-active`:streaming chat W3 D4 F6 + citation card + screenshot modal W3 D4 F7 + native fetch SSE(non Vercel AI SDK useChat per Karpathy §1.2)
- `docs/02-architecture/COMPONENT_CATALOG.md` ✅ status table rows C04/C05/C08/C09/C10 synced with bump narrative

#### F9 — PPT parser orchestrator wire(W3 C6 close)

- `backend/ingestion/parsers/__init__.py` ✅ `select_parser(source: Path) → Parser` factory dispatches by extension:`.docx` → `DoclingDocxParser`,`.pdf` → `DoclingDocxParser`(reuse,Docling handles both via same converter),`.pptx` → `PptxParser`,unsupported → `ValueError`。Uppercase extension normalised(`.suffix.lower()`)
- `backend/ingestion/chunker/strategies.py` ✅ `slide_based` 不再 raise NotImplementedError — delegates to `LayoutAwareChunker`(per Karpathy §1.2 simplicity:`PptxParser` emits same heading-paragraph-table-image structure as Docling — synthetic level=1 "Slide N" heading + level=2 title + body paragraphs + tables + pictures。Dedicated `SlideBasedChunker` class redundant)。Module docstring documents the design choice
- `backend/tests/test_parser_factory.py` ✅ NEW — 8 tests pass:select_parser dispatches(pptx / docx / pdf / uppercase / unsupported ValueError)+ select_chunker(pptx, auto/slide_based) returns LayoutAwareChunker + heading_aware standalone still NotImplementedError
- `backend/tests/test_chunker.py` ✅ updated:`test_strategy_selector_pptx_auto_raises_for_w3_scope` renamed to `test_strategy_selector_pptx_auto_returns_layout_aware`(assertion flipped per W4 D1 F9)
- **DEFERRED W4 D2-D3** End-to-end smoke run on W3 D1 後段 3 PPT samples — needs `scripts/run_pptx_ingest_sanity.py` + Azure AI Search index ready;non-blocking F9 unit acceptance

#### Test suite

- **Full backend test suite 159/159 pass**(W3 D5 baseline 138 + 21 NEW:14 crag + 8 parser_factory − 1 chunker test renamed not added)
- ruff clean on all W4 D1 new files

### Decisions / OQ Resolved

- **Decision** — CRAG threshold 0.70 not 0.60 plan-draft。Rationale:0.60 too lenient — eval-set queries rarely score < 0.6 against well-aligned corpus,correction rarely fires;0.70 surfaces more low-confidence cases for empirical tuning。Final value to be calibrated post W4 D2 RAGAs run per plan §4 R6
- **Decision** — `slide_based` chunker delegates to `LayoutAwareChunker` not dedicated `SlideBasedChunker` class。Rationale:per Karpathy §1.2 simplicity-first — PptxParser emits same heading-paragraph-table-image structure as Docling,LayoutAwareChunker walks heading levels generically。If PPT-specific chunking emerges later(e.g. always 1 chunk per slide regardless of size)再 split — currently speculative。`KbConfig.chunk_strategy` Literal preserves "slide_based" for forward extensibility
- **Decision** — `select_parser` reuses `DoclingDocxParser` for `.pdf`(non rename to `DoclingParser` general)。Rationale:per CLAUDE.md §1.3 surgical changes — rename = touching unrelated W2 D1 file + cascade through tests + imports;trigger absent。Class docstring documented W2 D5 .pdf reuse;long-term rename as W7+ Beta polish
- **Decision** — CRAG wired non-stream path only(stream path L3-only per architecture.md §3.5)。Rationale:token-by-token SSE UX precludes mid-stream rewrite — CRAG correction would require buffering tokens + restart,breaking streaming contract。L3 routing(W5 conditional)addresses this differently via intent classification before retrieve
- **Decision** — Component design note status bump uses bullet-list format(W4 D1 deliverables enumerated under Status block)not single sentence。Rationale:each bump compounds 2-4 sprint deliverables;single-sentence status loses traceability。Pattern usable for future v2-stable → v3 cycles
- **No new OQ resolved**(F1 / F8 / F9 不 trigger OQ;Q21 reranker final pick remains W4 D5 critical)

### Blockers cleared / remaining

- ✅ F1 + F8 + F9 code complete + 159/159 backend tests + ruff clean
- ⏸ Cohere Marketplace endpoint+key populate(Chris async procurement)— gates F5 lift smoke;non blocking F1
- ⏸ Voyage + ZeroEntropy procurement keys(Chris)— gates F3 shootout;non blocking F1
- ⏸ F9 end-to-end PPT smoke run on real samples — deferred W4 D2-D3 + needs Azure AI Search index ready
- ⏸ CRAG threshold empirical calibration — post W4 D2 RAGAs run per plan §4 R6

### Actual vs Planned Effort

| Item | Planned (h) | Actual (h) | Variance | Note |
|---|---|---|---|---|
| F1 CRAG `crag.py`(grader + loop + parse_confidence + fallback paths)| 3.0 | 1.5 | -1.5h | tenacity + AsyncAzureOpenAI 已熟 pattern from W3 Synthesizer;CragOutcome dataclass single-pass design |
| F1 server lifespan + /query route wire | 0.5 | 0.3 | -0.2h | Surgical addition next to synthesizer |
| F1 14 unit tests(parser + grader + 4 fallback paths)| 1.0 | 0.7 | -0.3h | _MockCompletion helper + AsyncMock side_effect queue |
| F8 5 component design note bumps + COMPONENT_CATALOG sync | 1.0 | 0.5 | -0.5h | Frontmatter + Status block bullet expansion;pre-existing structure clean |
| F9 select_parser factory + chunker delegation + 8 unit tests + 1 W2 test update | 1.0 | 0.4 | -0.6h | Karpathy §1.2 LayoutAwareChunker reuse saved dedicated SlideBasedChunker class |
| W4 D1 progress entry | 0.5 | 0.5 | 0 | This entry |
| **Total D1** | **7.0** | **3.9** | **-3.1h** | W4 plan calibrated 0.5x heuristic per W3 C8 carry-over;variance now ±0.5-1h(was ±3-5h W3) |

### Commits

| Hash | Subject |
|---|---|
| `a7552dc` | `feat(c05): F1 CRAG L2 correction loop + grader + 14 tests (W4 D1)` |
| `f7e415b` | `feat(c01): F9 PPT orchestrator wire — select_parser factory + slide_based chunker delegation (W4 D1)` |
| `e6e1b61` | `docs(components): F8 design note status bumps + catalog sync (W4 D1)` |
| _pending_ | `docs(planning): W4 D1 progress + checklist tick (F1 + F8 + F9 + plan active flip)` |

---

## Day 2 — _(pending)_

---

## Day 3 — _(pending)_

---

## Day 4 — _(pending)_

---

## Day 5 — _(pending)_

---

## Retro(填於 W4 D5 末)

### What worked
_(W4 D5 末 fill)_

### What didn't work / unexpected friction
_(W4 D5 末)_

### Surprises / discoveries
_(W4 D5 末)_

### Carry-overs to W05-optimization
_(W4 D5 末)_

### ADR triggers
_(W4 D5 末 — ADR-0012 reserved for Gate 2 FAIL outcome OR per-KB reranker column decision per W3 C5 carry)_

### Phase Gate 2 verdict(per plan.md §3 + architecture.md §6.3)
- G1-G6:_(W4 D5 末)_
- **Gate 2 4-metric within 5pp**:_(W4 D5 末)_ → PASS continues Tier 1 W5+ optimization;FAIL drops L2 CRAG → baseline-only

### Phase status
- Closeout commit:_(W4 D5 末)_
- Frontmatter status flipped to `closed`:_(W4 D5 末)_
- Phase W05 kickoff trigger:_(W4 D5 末 — W5 plan scope contingent on Gate 2 verdict)_

---

**End of W04 progress**(Day 0 prep stage,daily entries to follow W4 D1 onwards pending W3 D5 closeout sign-off + Chris W4 kickoff approval)
