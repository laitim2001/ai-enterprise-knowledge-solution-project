---
phase: W02-multi-format-ingestion
name: "Multi-Format Ingestion + Hybrid Retrieval Baseline"
sprint_week: W2
start_date: 2026-05-05
end_date: 2026-05-11          # planned, 5 工作日 (D1=Mon ... D5=Fri)
status: draft                  # draft | active | closed
spec_refs:
  - architecture.md §6.1 W2 row
  - architecture.md §3.3       # multi-format ingestion
  - architecture.md §3.5       # ChunkRecord schema
  - architecture.md §3.6       # AI Search index schema
  - architecture.md §3.1 §3.2  # retrieval pipeline + stack
  - architecture.md §6.3       # Gate 1 W2 末 R@5 ≥ 80%
  - components/C01-ingestion.md
  - components/C03-indexing.md
  - components/C04-retrieval.md
  - components/C06-eval.md
prior_phase: W01-foundation
---

# Phase W02 — Multi-Format Ingestion + Hybrid Retrieval Baseline

> **Plan version**:1.0(initial draft 2026-05-02 — D5 末 W1 retro sign-off 之後 status flips draft → active)
> **Owner**:Chris(Tech Lead)
> **Approved by**:_(Chris when status flips draft → active per PROCESS.md §2.3 R1.phase)_

## 1. Scope

W02 係 EKP Tier 1 嘅 ingestion + retrieval baseline phase。建立 .docx ingestion full pipeline(Docling parser → layout-aware chunker → screenshot extractor → embedding pipeline)+ index population to `ekp-kb-drive-v1` + Hybrid retrieval baseline(Azure AI Search built-in RRF,**no rerank yet**)+ W2 末 Gate 1 evaluation(**R@5 ≥ 80% on 30 條 synthetic eval set**)。

呢個 phase 嘅 critical hard gate(per `architecture.md §6.3`)係 **Gate 1 R@5 ≥ 80%** —— fail = 不 promote 去 W3 generation pipeline,先 fix retrieval quality。

**Sprint week origin**:[`architecture.md` §6.1 W2](../../architecture.md)

## 2. Deliverables

### F1 — Carry-over: F8 Docling .docx parser PoC
- **Component(s)**:**C01** Ingestion Pipeline(parser sub-step)
- **Spec ref**:`architecture.md §3.3`,`components/C01-ingestion.md §1`
- **OQ deps**:Q1(Resolved 40W/30P/30P)、Q2(Resolved D4 — 6 sample arrived)、Q17(W2 D2 finding from F6 inspector run already done D4)
- **Carry-over from**:W1 F8(blocked R10 + R8;R10 unblocked D4,R8 still open)
- **Acceptance criteria**:
  - `backend/ingestion/parsers/docx_parser.py` 用 Docling Python lib(if R8 unblocks)or **fallback 用 python-docx + custom layout extractor**(if R8 仍 block)
  - Parse 6 sample Drive manuals(`docs/06-reference/01-sample-doc/`),extract:heading-aware sections,embedded image inventory,table structure
  - **Heading-aware fallback**:per W1 D4 F6 finding(heading style coverage ~3% only),chunker 必須 add font-size heuristic OR visual layout heuristic detect section boundary
  - Sanity check report on 6 sample
- **Effort estimate**:8h(原計 6h,+ font-size heuristic dev 2h)
- **Owner**:AI

### F2 — Layout-aware chunker
- **Component(s)**:**C01** Ingestion Pipeline(chunker sub-step)
- **Spec ref**:`architecture.md §3.3`,`components/C01-ingestion.md §1`
- **OQ deps**:Q19(embedding dim 1024 vs 3072 — Open W2 D3 decide)
- **Acceptance criteria**:
  - `backend/ingestion/chunker/layout_aware.py` heading-aware section split
  - Token budget per chunk ~500 tokens(adjustable per `KbConfig.chunk_strategy`)
  - Strategy selector(`auto` / `heading_aware` / `layout_aware` / `slide_based`)per `KbConfig`
  - Chunk on 6 sample → 估 ~2000-3000 chunks total(per architecture.md §3.4 baseline)
  - Unit test:known input → expected chunk count + boundaries
- **Effort estimate**:6h
- **Owner**:AI

### F3 — Screenshot extractor + Blob upload
- **Component(s)**:**C01** Ingestion Pipeline(screenshot sub-step)+ **C12** DevOps & Infra(Blob via Azurite)
- **Spec ref**:`architecture.md §3.3`,`components/C01-ingestion.md §1`
- **OQ deps**:Q18(image format inventory — finding from F6 D4:868 PNG + 18 SVG + 4 EMF)
- **Acceptance criteria**:
  - `backend/ingestion/screenshots/extractor.py` extract embedded images → PIL Image
  - `backend/ingestion/screenshots/uploader.py` async Blob upload to per-KB container
  - SHA256 dedup(same image multiple docs → 1 Blob upload)
  - **EMF conversion via Pillow**(4 EMF found in samples per F6 finding)
  - Local dev:Azurite container `ekp-kb-drive-screenshots`(via C12)
- **Effort estimate**:5h
- **Owner**:AI

### F4 — Embedding pipeline first-pass(carry-over F10)
- **Component(s)**:**C01** Ingestion Pipeline(embedding sub-step)
- **Spec ref**:`architecture.md §3.2`,`components/C01-ingestion.md §1`
- **OQ deps**:Q4(Resolved full D2)、Q19(MRL truncate 1024 vs 3072 — decide W2 D3)、Q5(Cohere Path A vs B for W3 — Open)
- **Carry-over from**:W1 F10(blocked R8; partially mitigated by direct Azure OpenAI HTTP REST call,no SDK needed)
- **Acceptance criteria**:
  - `backend/ingestion/embedding/azure_openai_embedder.py` async embedding call(prefer SDK if R8 unblocks,fallback HTTP REST)
  - text-embedding-3-large + MRL truncate to 1024d
  - Cost log via structlog(per chunk:input tokens + output dim)
  - Smoke test:1 條 sample text → 1024d vector ✅
  - Parallel batch on 100 chunks → < 5s(per C01 design §5)
- **Effort estimate**:5h
- **Owner**:AI

### F5 — Index population(populate.py)
- **Component(s)**:**C01** Ingestion Pipeline(orchestrator final step)+ **C03** Indexing Service(consumer)
- **Spec ref**:`architecture.md §3.5`(ChunkRecord),`§3.6`(index schema),`components/C03-indexing.md`
- **OQ deps**:none(Q3 + Q4 全 Resolved;index ready per F9 W1 D4)
- **Acceptance criteria**:
  - `backend/ingestion/orchestrator.py` end-to-end:parse → chunk → screenshot → embed → emit ChunkRecord
  - `backend/indexing/populate.py` batch upload to `ekp-kb-drive-v1` via REST API
  - 6 sample → ~2000-3000 chunks indexed
  - GET index doc count via REST → match expected
  - Failure handling per ChunkRecord:atomic per-doc(no half-indexed)
- **Effort estimate**:5h
- **Owner**:AI

### F6 — Hybrid retrieval baseline(C04 first-touch heavy build)
- **Component(s)**:**C04** Retrieval Engine
- **Spec ref**:`architecture.md §3.1`,`§3.2`,`components/C04-retrieval.md`
- **OQ deps**:none(Q3 ready)
- **Acceptance criteria**:
  - `backend/retrieval/hybrid.py` Azure AI Search built-in RRF(BM25 + vector via REST)
  - Filter clause:`enabled eq true and low_value_flag eq false`
  - `backend/retrieval/retrieval_engine.py` public `retrieve(query, kb_id, top_k)` API
  - Wired to `/query` endpoint stub(C08)— query → top-50 chunks return
  - **NO RERANK YET**(W3 wires Cohere)
  - Unit test:known query → assert non-empty + ranked output
- **Effort estimate**:4h
- **Owner**:AI

### F7 — Gate 1 evaluation(Recall@5 ≥ 80%)
- **Component(s)**:**C06** Eval Framework + **C04** Retrieval Engine(consumer)
- **Spec ref**:`architecture.md §6.3`(Gate 1 criterion),`eval-methodology.md`,`components/C06-eval.md`
- **OQ deps**:Q14(Resolved D2 — Chris SME),Q2(F11 ground truth fill prerequisite — see F11 below)
- **Acceptance criteria**:
  - `backend/eval/runner.py` run hybrid retrieval against 30 條 eval set
  - Compute Recall@5 per query + aggregate
  - `backend/eval/gates.py` Gate 1 decision logic
  - Generate `reports/gate1_w2.yaml`(per-query result + aggregate)
  - **Gate 1 verdict**:R@5 ≥ 80% pass → W3 promote;< 80% → fail-fast,W3 prep blocked,W2 末 retro 處理
- **Effort estimate**:6h
- **Owner**:AI

### F8 — F11 ground truth fill(carry-over)
- **Component(s)**:**C06** Eval Framework
- **Spec ref**:`architecture.md §6.1 W1`,`docs/eval-set-v0.yaml`
- **OQ deps**:Q14(Resolved Chris)、Q2(Resolved D4)、cascade dependency on F1+F2+F5(need real chunk_id)
- **Carry-over from**:W1 F11(was blocked Q2/R10;cascade also need F1+F2+F5 done first to discover chunk_ids)
- **Acceptance criteria**:
  - All 30 main queries `annotation.validated: true`
  - Real chunk_id from `ekp-kb-drive-v1` populated index replace placeholder
  - `docs/eval-set-v1.yaml`(rename from v0 once SME-validated by Chris)
  - Pass `python -m scripts.validate_eval_set docs/eval-set-v1.yaml`
- **Effort estimate**:2 工作日 SME effort by Chris,spread W2 D3-D5
- **Owner**:Chris + (AI assist for chunk_id discovery automation)

### F9 — Admin Console KB views wire(C09 first-touch heavy build)
- **Component(s)**:**C09** Admin Console UI
- **Spec ref**:`architecture.md §5.1-§5.4`,`components/C09-admin-ui.md`
- **OQ deps**:Q10(Open — using neutral tokens until W4 designer pass)
- **Acceptance criteria**:
  - View 2 `/admin` overview wire to `GET /kb` aggregate stats
  - View 3 `/admin/kb` KB list with shadcn DataTable + TanStack Query
  - View 4 `/admin/kb/[id]` KB detail + KbConfig form + PATCH wire
  - View 5 `/admin/kb/[id]/upload` doc upload form(multipart)to C01 + C08
- **Effort estimate**:8h
- **Owner**:AI

### F10 — F2 + F7 unit tests retry(carry-over,depends on R8 mitigation)
- **Component(s)**:**C08** API Gateway + **C02** KB Manager
- **Spec ref**:`CLAUDE.md §5.6 H6`(critical pipeline test coverage)
- **OQ deps**:none
- **Carry-over from**:W1 F2 + F7(blocked R8 corp proxy)
- **Acceptance criteria**:
  - **Pre-condition**:R8 mitigated via P1(VPN/hotspot)or P2(IT whitelist)
  - `pip install -e backend[dev]` success
  - `pytest tests/test_api_skeleton.py` → 8 smoke tests pass
  - `pytest tests/kb_management/` → CRUD tests pass(coverage ≥ 80%)
  - Update C02 + C08 design notes status `v0/v1 → v2-stable`(per CC-5)
- **Effort estimate**:3h(post-pip-unblock window)
- **Owner**:AI(Chris ops for R8 unblock)

### F11 — W2 末 retro + W3 kickoff prep
- **Component(s)**:(cross-cutting governance)
- **Spec ref**:`PROCESS.md §2.3` lifecycle closeout
- **OQ deps**:none
- **Acceptance criteria**:
  - W02 progress.md retro section 完成
  - Phase Gate 1 verdict explicit(R@5 ≥ 80% pass / fail)
  - W03 phase folder kickoff:`W03-chat-retrieval-citation/{plan, checklist, progress}.md` draft
  - Carry-overs documented
- **Effort estimate**:3h
- **Owner**:AI(draft)+ Chris(approve)

## 3. Success Criteria(Phase Gate to W3)

| # | Criterion | Target | Measure | Block W3? |
|---|---|---|---|---|
| **G1** | Gate 1 R@5 ≥ 80% on 30-query eval set(`§6.3` hard gate)| ≥ 80% | `reports/gate1_w2.yaml` aggregate | **YES — fail-fast,W3 paused** |
| G2 | All 11 deliverables 完成 OR explicit defer | 11/11 | progress closeout | Yes |
| G3 | F11 ground truth ≥ 30 SME-validated | ≥ 30 | `docs/eval-set-v1.yaml` | Yes |
| G4 | 6 sample 全 ingested(parse + chunk + embed + index)| 6/6 | populated index doc count | Yes |
| G5 | Backend ruff + frontend lint + type-check 0 errors | All clean | local run | Yes |
| G6 | All component design notes status updated(v0-draft → v1-active where touched W2)| C01/C03/C04/C06/C09 bumped | review | Yes |

## 4. Risks(Phase-Specific,延伸 RISK_REGISTER.md)

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | **Gate 1 R@5 < 80%** → W3 promotion blocked | Medium | High | Hybrid baseline 通常足夠;若 fail,W2 末 retro 分析:chunk strategy / index field config / query type mismatch;W3 加 query expansion or rerank early |
| R2 | F1 Docling install 仍撞 R8 corp proxy | Confirmed | Medium | Fallback python-docx + custom layout(per F1 acceptance);Docling pip install via P1 ops window if available |
| R3 | F2 chunker heading-aware fallback heuristic 唔 robust(per W1 D4 finding heading style ~3%)| Medium | Medium | Multi-heuristic:font size + bold + paragraph spacing;manual sanity check on 6 sample |
| R4 | F11 SME bandwidth(Chris multi-role)| Medium | High | LLM-judge first pass + Chris verify pattern(per `§8.1 R2`);最壞 deferred to W3 但 G1 Gate 1 必須 met |
| R5 | F4 embedding cost runaway(2000+ chunks × cost)| Low | Medium | Pre-flight cost estimate;~2000 chunks × 1024d × $0.13/M tokens ≈ $0.50-1 total,low risk |
| R6 | F9 Admin UI scope creep(8 views vs 4 in W2)| Medium | Low | Lock to View 2/3/4/5 only this phase;View 6/7/8 W3-W4 per heatmap |
| R7 | Carry-over F10 pytest 仍 blocked R8 W2 末 | Medium | Medium | If still blocked W2 D5,re-defer to W3 D1 + escalate IT ticket urgent |

## 5. Day-by-Day Breakdown(rough)

| Day | Date | Focus | Deliverables targeted |
|---|---|---|---|
| D1 | 2026-05-05 (Mon) | F1 Docling parser PoC start + Q3 tier/region cleanup | F1 |
| D2 | 2026-05-06 (Tue) | F1 cont + F2 chunker + F3 screenshot extractor | F1, F2, F3 |
| D3 | 2026-05-07 (Wed) | F2 cont + F4 embedding + F8 ground truth start | F2, F4, F8 |
| D4 | 2026-05-08 (Thu) | F5 populate + F6 hybrid baseline + F8 cont | F5, F6, F8 |
| D5 | 2026-05-09 (Fri) | F7 Gate 1 eval + F8 close + F9 Admin UI + F11 retro | F7, F8, F9, F11 |

(F10 F2/F7 pytest retry — opportunistic if R8 unblocks any time during W2)

## 6. Dependencies on Prior Phase

Carry-over from `W01-foundation/progress.md` retro(D4 draft):

- **F1 Docling parser PoC**(was W1 F8) — prerequisites Q2 ✅(D4)+ R8 mitigation(may use python-docx fallback)
- **F4 embedding pipeline**(was W1 F10) — Q4 ✅(D2)+ HTTP REST fallback if R8 blocks SDK
- **F8 ground truth fill**(was W1 F11) — Q2 ✅(D4)+ Q14 ✅(D2)+ cascade after F1+F2+F5 for chunk_id
- **F10 unit tests**(was W1 F2 + F7 deferred) — R8 mitigation hard prerequisite
- **Q3 outstanding minor**(tier confirm + region confirm)— Chris W2 D1 cleanup
- **R8 mitigation P1/P2 ops decision** — Chris ops
- **Component design note bumps**:C01 v0→v1 W2 D2(post F1 finding),C03 already v1-active,C04/C06/C09 v0→v1 per first-touch

## 7. Plan Changelog

| Date | Change | Reason | Approver |
|---|---|---|---|
| 2026-05-02 | Initial draft(W1 D4 prep)| Per Chris W1 D4 strategic call to prepare W2 kickoff during W1 D4-D5 capacity;status=draft pending W1 D5 retro sign-off | Chris(pending approve to flip active) |

---

**Lifecycle reminder**:呢份 plan 而家 `status=draft`。W1 D5 末 Chris review retro 之後 sign-off + flip status `draft → active`,然後 W2 D1(2026-05-05)正式 start implementation per `PROCESS.md §2.3` daily execution lifecycle。
