---
phase: W03-chat-retrieval-citation
plan_ref: ./plan.md
status: draft
last_updated: 2026-05-07
---

# Phase W03 — Checklist

> Atomic checkbox(每 item ≤ 1–2 hour effort)。
> Status:`draft` 直到 W2 D5 closeout sign-off + Gate 1 verdict pass。
> 全 unchecked 至 W3 D1 implementation start。

## F1 — Cohere Rerank v3.5 integration

- [ ] **Q5 Cohere procurement Path A vs B decision**(Chris W3 D1 morning critical;Path A=Marketplace,Path B=direct API)
- [ ] `backend/retrieval/reranker/__init__.py`
- [ ] `backend/retrieval/reranker/base.py` — `Reranker` Protocol(`async rerank(query, candidates, top_k) → list[ChunkRecord]`)
- [ ] `backend/retrieval/reranker/cohere.py` — `CohereReranker` via SDK(Path A)or HTTP REST(Path B)
- [ ] `backend/retrieval/reranker/factory.py` — config-flag based selector(Cohere baseline,W4 swap targets)
- [ ] tenacity retry on RateLimitError + APITimeoutError
- [ ] Wire into `RetrievalEngine.retrieve()` post-hybrid → top-50 → Cohere → top-5
- [ ] Unit test:mocked Cohere → assert order desc by rerank_score + top_k respected

## F2 — GPT-5.5 synthesis pipeline

- [ ] `backend/generation/__init__.py`
- [ ] `backend/generation/prompt_builder.py` — system + user + chunks-as-context per spec §3.2
- [ ] `backend/generation/synthesizer.py` — `Synthesizer.synthesize(query, top_chunks)` async via AsyncAzureOpenAI chat.completions
- [ ] Citation marker parse(`[chunk-{id}]` regex extraction)
- [ ] tenacity retry on RateLimitError
- [ ] structlog cost log(input_tokens + output_tokens + deployment + latency)
- [ ] Unit test:mocked AsyncAzureOpenAI → assert prompt shape + citation parse

## F3 — Citation enrichment with image refs

- [ ] Citation populate `embedded_images: list[ImageRef]` from cited ChunkRecord
- [ ] Graceful empty list when R12 deferral applies(uploader=None ingestion)
- [ ] QueryResponse.citations ordered by appearance in answer
- [ ] Unit test:synthetic chunks with images → citation has image refs;chunks without images → empty

## F4 — SSE streaming response

- [ ] `POST /query/stream` no longer 501 — Vercel AI SDK SSE protocol(`data: ...\n\n`)
- [ ] SSE event types:`text-delta` / `citation` / `done`
- [ ] Client disconnect cancels GPT-5.5 stream(asyncio cancel)
- [ ] Unit test:TestClient SSE consumer asserts event format + cancellation

## F5 — .pptx parser(python-pptx)

- [x] python-pptx 1.0.2 already installed via W1 D2 batch(non new install — pyproject deps already)
- [x] `backend/ingestion/parsers/pptx_parser.py` `PptxParser` impl Parser Protocol(W3 D1 2026-05-04)
- [x] Per-slide structure mapping:`Slide N` level=1 heading + title placeholder level=2 + body text + speaker notes prefixed `[Notes] ...`
- [x] Embedded images from slide shapes(`MSO_SHAPE_TYPE.PICTURE` → blob + ext + SHA256 dedup-ready)
- [ ] **DEFERRED W3 D2-D3** `chunker/strategies.py` slide_based path → SlideBasedChunker(currently NotImplementedError;orchestrator wire post Q5 / F2 sequence)
- [ ] **DEFERRED Q2** Chris provides 1-2 .pptx samples(`docs/06-reference/01-sample-doc/`)
- [ ] **DEFERRED W3 D2-D3** Sanity report on .pptx samples(post Q2 sample arrival)
- [x] Unit test:9 tests pass against synthetic Presentation fixtures(`backend/tests/test_pptx_parser.py`)— title / body / table / picture / notes / doc_order / no-title / malformed / Protocol attr

## F6 — Chat UI streaming + citation card

- [ ] `frontend/app/page.tsx` chat view per architecture.md §5.2
- [ ] Vercel AI SDK `useChat` wired to `/query/stream`
- [ ] CitationCard component(shadcn Card)+ image preview
- [ ] EKP design tokens only(non Dify colors per CLAUDE.md §7)
- [ ] PR comment standard:`Reference: dify/web/app/components/base/chat/...`(layout reference only)

## F7 — Screenshot modal

- [ ] Click citation image → shadcn Dialog modal full-resolution
- [ ] `/screenshots/{kb_id}/{doc_id}/{img_id}` redirect endpoint(replace 501)
- [ ] W3 baseline:public Azurite/Blob direct URL(SAS expiry W7+)

## F8 — Pipeline wizard frontend

- [ ] `frontend/app/admin/kb/new/page.tsx` 3-step wizard
- [ ] DATA SOURCE → DOCUMENT PROCESSING → EXECUTE step indicator(shadcn Stepper)
- [ ] POST sequence wired:create KB → upload doc → trigger ingestion
- [ ] Reference Dify wizard layout(EKP tokens only)

## F9 — Settings tab

- [ ] `frontend/app/admin/kb/[id]/page.tsx` Settings tab
- [ ] KbConfig form(embedding_model / chunk_strategy / reranker / top_k / rerank_k)
- [ ] PATCH wire to `/kb/{id}/settings`
- [ ] Form validation per Pydantic KbConfig schema

## F10 — W3 末 retro + W4 kickoff prep

- [ ] W03 progress.md retro section completed
- [ ] W04 phase folder mkdir + plan.md draft
- [ ] W03 carry-overs documented
- [ ] W03 progress.md frontmatter status flipped to `closed`

---

## Cross-Cutting

- [ ] Each commit references `progress.md` Day-N entry(R2)
- [ ] Component tag in commit message per CC-1
- [ ] OQ status sync to `decision-form.md`(R4)— Q5 W3 D1 critical
- [ ] Component design note status bumps(per CC-5):C04 v1→v2(rerank wire),C05 v0→v1,C08 v1→v1.1(SSE wire),C10 v0→v1
- [ ] RISK_REGISTER.md update if R8 reactivation pattern persists OR Q5 path A delays surface as new risk

---

**Lifecycle reminder**:呢份 checklist 衍生自 `plan.md` deliverables。新加 deliverable 必須先入 plan + changelog,然後再加 checklist item。
