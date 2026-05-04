---
phase: W03-chat-retrieval-citation
name: "Chat + Hybrid Retrieval + Citations"
sprint_week: W3
start_date: 2026-05-08          # tentative — see §7 changelog;Option A continues 2-day-earlier shift if approved at W2 closeout
end_date: 2026-05-14            # tentative,5 working days
status: active                  # flipped 2026-05-04 W2 D5 cont — Gate 1 PASS R@5=0.9722 against eval-set-v1-draft
spec_refs:
  - architecture.md §6.1 W3 row
  - architecture.md §3.1       # query pipeline (CRAG loop deferred to W4)
  - architecture.md §3.2       # stack (Cohere Rerank v3.5 + GPT-5.5)
  - architecture.md §3.3       # PPT parser (python-pptx)
  - architecture.md §4.5       # QueryResponse with citations
  - architecture.md §5.2       # Chat UI view spec
  - architecture.md §5.3       # Pipeline wizard view (Dify Image 1)
  - components/C01-ingestion.md # PPT parser stub addition
  - components/C04-retrieval.md # Cohere Rerank wire
  - components/C05-generation.md # GPT-5.5 synthesis + CRAG (W4)
  - components/C10-chat-ui.md   # Chat UI streaming + citation card
prior_phase: W02-multi-format-ingestion
---

# Phase W03 — Chat + Hybrid Retrieval + Citations

> **Plan version**:1.0(draft 2026-05-07 W2 D5 末 prep)
> **Owner**:Chris(Tech Lead)
> **Approved by**:_(pending Chris W2 D5 closeout sign-off + Gate 1 verdict pre-condition)_

## 1. Scope

W03 wires the **end-to-end query path** on top of W2 hybrid retrieval baseline:Cohere Rerank v3.5 (Q5 path A vs B resolution before D1)+ GPT-5.5 synthesis with citation + SSE streaming response + Chat UI(streaming + citation card)+ Pipeline wizard 借 Dify Image 1 layout + Settings tab + .pptx parser(python-pptx for the 30% PPT format share per Q1)。

**Pre-condition for W3 promotion**:Gate 1 R@5 ≥ 80% (W2 D5 F7) **must pass**。Fail → HALT POC,W3 唔啟動,foundation iteration loop per architecture.md §6.3。

**Sprint week origin**:[`architecture.md` §6.1 W3](../../architecture.md)

## 2. Deliverables(F1-F10)

### F1 — Cohere Rerank v3.5 integration
- **Component(s)**:**C04** Retrieval Engine(reranker module)
- **Spec ref**:`architecture.md §3.1, §3.2`,`components/C04-retrieval.md §1, §3`
- **OQ deps**:Q5(Cohere procurement Path A=Marketplace vs Path B=direct API,**Open W3 D1 critical**)
- **Acceptance criteria**:
  - `backend/retrieval/reranker/{__init__, base.py, cohere.py, factory.py}` per C04 §1 layout
  - `Reranker` Protocol with `async rerank(query, candidates, top_k) → list[ChunkRecord]`
  - `CohereReranker` via Cohere Python SDK or HTTP REST (whichever path Q5 resolves to)
  - tenacity retry on RateLimitError + APITimeoutError
  - Wired into `RetrievalEngine.retrieve()` post-hybrid → top-50 → Cohere → top-5
  - Unit test:mocked Cohere → assert order desc by rerank_score + top_k respected
- **Effort estimate**:5h(impl 3h + Q5 Path B contingency wiring 1h + tests 1h)
- **Owner**:AI

### F2 — GPT-5.5 synthesis pipeline
- **Component(s)**:**C05** Generation
- **Spec ref**:`architecture.md §3.1, §3.2`,`components/C05-generation.md §1`
- **OQ deps**:Q4 fully Resolved (W1 D1)
- **Acceptance criteria**:
  - `backend/generation/{__init__, prompt_builder.py, synthesizer.py}`
  - `Synthesizer.synthesize(query, top_chunks) → SynthesisResult{answer, citations}`
  - GPT-5.5 prompt = system + user + chunks-as-context with citation requirement(per architecture.md §3.2 prompt template)
  - Citation extraction:LLM emits `[chunk-{id}]` markers in answer text;parse to Citation list
  - tenacity retry on RateLimitError
  - Cost log via structlog(input_tokens + output_tokens + deployment + latency)
  - Unit test:mocked AsyncAzureOpenAI chat.completions → assert prompt shape + citation parse
- **Effort estimate**:6h
- **Owner**:AI

### F3 — Citation enrichment with image refs(C05)
- **Component(s)**:**C05** Generation
- **Spec ref**:`architecture.md §4.5 Citation`,`§3.5 ChunkRecord embedded_images`
- **OQ deps**:none
- **Acceptance criteria**:
  - Each Citation populates `embedded_images: list[ImageRef]` from cited ChunkRecord
  - W2 D3 R12 deferral note:if citation chunk had no real Blob upload (uploader=None),`embedded_images=[]` graceful
  - QueryResponse.citations list ordered by appearance in answer
- **Effort estimate**:2h
- **Owner**:AI

### F4 — SSE streaming response
- **Component(s)**:**C08** API Gateway + **C05** Generation
- **Spec ref**:`architecture.md §5.2`,`components/C08-api-gateway.md`(SSE endpoint design)
- **OQ deps**:none
- **Acceptance criteria**:
  - `POST /query/stream` no longer 501 — emits Vercel AI SDK SSE protocol(`data: ...\n\n`)
  - SSE event types:`text-delta`(streaming token),`citation`(per-citation enrichment),`done`(end frame)
  - Backpressure:client disconnect → cancel underlying GPT-5.5 stream
  - Unit test:TestClient stream consumer → assert event format + cancellation
- **Effort estimate**:3h
- **Owner**:AI

### F5 — .pptx parser(python-pptx)
- **Component(s)**:**C01** Ingestion(parsers/pptx_parser.py)
- **Spec ref**:`architecture.md §3.3`,`components/C01-ingestion.md §1`
- **OQ deps**:Q1 Resolved(30% PPT share)
- **Acceptance criteria**:
  - `backend/ingestion/parsers/pptx_parser.py` PptxParser class implementing Parser Protocol
  - Per-slide chunk strategy(slide_based);speaker notes 併入 same chunk
  - Embedded images from slide shapes → ParserResult.embedded_images
  - Update `chunker/strategies.py` slide_based path no longer NotImplementedError
  - Sanity report on 1-2 .pptx samples(blocked Q2 — request PPT samples from Chris)
- **Effort estimate**:4h
- **Owner**:AI

### F6 — Chat UI streaming + citation card
- **Component(s)**:**C10** Chat Interface UI
- **Spec ref**:`architecture.md §5.2`,`components/C10-chat-ui.md`
- **OQ deps**:none
- **Acceptance criteria**:
  - `frontend/app/page.tsx` chat view per architecture.md §5.2 layout(Dify Image 1 layout reference,EKP design tokens)
  - Vercel AI SDK `useChat` hook wired to `/query/stream`
  - Citation card component(shadcn Card + image preview)displays per-citation
  - Reference per CLAUDE.md §7:may borrow Dify chat layout structure but NOT colors/icons
  - PR comment standard reference:`Reference: dify/web/app/components/base/chat/...`
- **Effort estimate**:6h
- **Owner**:AI

### F7 — Screenshot modal
- **Component(s)**:**C10** Chat Interface UI
- **Spec ref**:`architecture.md §5.2`,`components/C10-chat-ui.md`
- **OQ deps**:F3 R12 acknowledgment — modal works with empty image list(graceful)
- **Acceptance criteria**:
  - Click citation image preview → opens shadcn Dialog modal full-resolution
  - Image source = `/screenshots/{kb_id}/{doc_id}/{img_id}` redirect endpoint(C08 #18 — wire 501 stub to actual SAS URL redirect)
  - W3 baseline:public Azurite URL works without SAS(per architecture.md §4.6 POC public-read mode);W7+ adds SAS expiry
- **Effort estimate**:2h
- **Owner**:AI

### F8 — Pipeline wizard frontend(borrows Dify Image 1)
- **Component(s)**:**C09** Admin Console UI(View 7 wizard)
- **Spec ref**:`architecture.md §5.5`,`components/C09-admin-ui.md`
- **OQ deps**:Q10(neutral tokens W4 designer pass)
- **Acceptance criteria**:
  - `frontend/app/admin/kb/new/page.tsx` per Dify wizard pattern:DATA SOURCE → DOCUMENT PROCESSING → EXECUTE step indicator
  - shadcn Stepper component + form per step
  - POST sequence:create KB → upload doc → start ingestion(orchestrator)
- **Effort estimate**:5h
- **Owner**:AI

### F9 — Settings tab
- **Component(s)**:**C09** Admin Console UI
- **Spec ref**:`architecture.md §5.4 KB Detail / Settings`
- **OQ deps**:none
- **Acceptance criteria**:
  - `frontend/app/admin/kb/[id]/page.tsx` Settings tab — KbConfig form(embedding_model,chunk_strategy,reranker,top_k,rerank_k)
  - PATCH wire to `/kb/{id}/settings`(C02 + C08)
  - Form validation per Pydantic KbConfig schema
- **Effort estimate**:3h
- **Owner**:AI

### F10 — W3 末 retro + W4 kickoff prep
- **Component(s)**:(cross-cutting governance)
- **Spec ref**:`PROCESS.md §2.3 lifecycle closeout`
- **OQ deps**:none
- **Acceptance criteria**:
  - W03 progress.md retro section completed
  - W04 phase folder kickoff:plan.md draft
  - Carry-overs documented
- **Effort estimate**:3h
- **Owner**:AI(draft)+ Chris(approve)

## 3. Success Criteria(Phase Gate to W4)

| # | Criterion | Target | Measure | Block W4? |
|---|---|---|---|---|
| G1 | All 10 deliverables 完成 OR explicit defer | 10/10 | progress closeout | Yes |
| G2 | End-to-end /query → answer + citations + images works on real Drive query | Works | manual smoke | Yes |
| G3 | Backend ruff + frontend lint + type-check 0 errors | All clean | local run | Yes |
| G4 | C04/C05/C08/C10 design notes status updated(v0/v1 → v1/v2) | bumped | review | Yes |
| G5 | Cohere rerank measurable improvement vs hybrid baseline (recall@5 sample on 5 queries) | non-regression | manual check | No (data-driven W4 confirm) |

## 4. Risks(Phase-Specific)

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | Q5 Cohere procurement Path A delayed(Marketplace billing onboarding)| Medium | High | Path B fallback:Cohere direct API + corporate card,unblock W3 D1 immediately;document path-decision in commit;W4 reranker shootout still works in either path |
| R2 | GPT-5.5 hallucination on tables(R4 in `architecture.md §8.2`) | Medium | High | Citation-required prompt(refuse if no chunk citation possible);table-heavy eval queries surface in W4 |
| R3 | SSE protocol drift between Vercel AI SDK frontend + custom backend | Low | Medium | Reference Vercel AI SDK protocol spec exactly;test with `useChat` hook end-to-end;fallback non-streaming POST /query if streaming proves complex |
| R4 | R8 reactivated VPN blocks live W3 development(Cohere + GPT-5.5 both cloud) | High | High | Same mitigation as W2:disconnect GlobalProtect VPN;sanity scripts ready post-disconnect;mock-test code path stays correct regardless |
| R5 | F8 Pipeline wizard scope creep(W2 F9 Admin already had 4 views) | Medium | Low | Lock to wizard skeleton this phase;polish W4-W5 |
| R6 | F5 PPT samples not provided by Chris(Q2 PPT-share)| Medium | Medium | request W3 D1 at latest;fallback synthetic .pptx sample for parser smoke test |

## 5. Day-by-Day Breakdown(rough — pending Option A continuation review at W2 D5 closeout)

| Day | Date | Focus | Deliverables targeted |
|---|---|---|---|
| D1 | 2026-05-08 (Fri) | Q5 path decision + F1 Cohere wire start | F1 |
| D2 | 2026-05-09 (Sat) | F1 cont + F2 synthesis prompt + F3 citation enrichment | F1, F2, F3 |
| D3 | 2026-05-10 (Sun) | F4 SSE streaming + F5 PPT parser | F4, F5 |
| D4 | 2026-05-11 (Mon) | F6 Chat UI + F7 screenshot modal | F6, F7 |
| D5 | 2026-05-12 (Tue) | F8 Pipeline wizard + F9 Settings + F10 retro draft | F8, F9, F10 |

(若 Chris 喺 W2 D5 closeout 揀 keep continuous 2-day-shift,日期上述應用;否則 D1 = 2026-05-12 Tue per architecture.md §6.1 original schedule)

## 6. Dependencies on Prior Phase

Carry-over from `W02-multi-format-ingestion/progress.md` retro(D5 draft pending Gate 1):
- **Gate 1 verdict**(R@5 ≥ 80% pass / fail)— **HARD pre-condition for W3 start**
- F8 ground truth fill — Chris SME effort discovery via `scripts/discover_chunk_ids.py` post-VPN-disconnect
- F7 live Gate 1 eval — pending VPN disconnect
- F3 R12 Azurite signature — image upload deferred to W7+ cloud;F7 in W3 must work with embedded_images=[] gracefully
- F4 R8 reactivation — same mitigation expected for W3 cloud-touching work

## 7. Plan Changelog

| Date | Change | Reason | Approver |
|---|---|---|---|
| 2026-05-07 | Initial draft(W2 D5 末 retro prep)| Per PROCESS.md §2.3 rolling-JIT kickoff;status=draft pending Chris W2 D5 closeout sign-off + Gate 1 verdict | Chris(pending approve to flip active) |
| 2026-05-04 | Status `draft → active`(W2 D5 cont 後段)| Gate 1 PASS R@5=0.9722 against eval-set-v1-draft;W02 closed same day。Caveat:current PASS mode=keyword + validated=False;true SME-strict PASS pending Chris cascade(C9 → C2 — non blocking for W3 forward but informs Gate 2 / production wording)| AI-flipped per W2 closeout decision |

---

**Lifecycle reminder**:呢份 plan `status=active`(flipped 2026-05-04 W2 D5 cont)。重大 deviation 入第 7 節 changelog。
