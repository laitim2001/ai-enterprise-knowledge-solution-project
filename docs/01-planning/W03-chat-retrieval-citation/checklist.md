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

- [x] **Q5 Cohere procurement Path A vs B decision** ✅ Chris signoff 2026-05-04 → **Path A Azure Marketplace**
- [x] `backend/retrieval/reranker/__init__.py` ✅ W3 D1 後段
- [x] `backend/retrieval/reranker/base.py` — `Reranker` Protocol + `RerankedChunk` dataclass ✅ W3 D1 後段
- [x] `backend/retrieval/reranker/cohere.py` — `CohereReranker` REST(Path A or B same body schema) ✅ W3 D1 後段
- [x] `backend/retrieval/reranker/factory.py` — config-flag selector returns None when unconfigured ✅ W3 D1 後段
- [x] tenacity retry on httpx.HTTPStatusError + TransportError ✅ W3 D1 後段
- [ ] **DEFERRED W3 D2** Wire into `RetrievalEngine.retrieve()` post-hybrid → top-50 → Cohere → top-5(pending Chris .env populate Marketplace endpoint + key post procurement deploy)
- [x] 8 unit tests pass(empty / desc by score / payload shape / top_n clamp / invalid index skip / factory None × 2 / factory CohereReranker) ✅ W3 D1 後段

## F2 — GPT-5.5 synthesis pipeline

- [x] `backend/generation/__init__.py` ✅ W3 D2
- [x] `backend/generation/prompt_builder.py` — SYSTEM_PROMPT + build_prompt(query, chunks) ✅ W3 D2
- [x] `backend/generation/synthesizer.py` — `Synthesizer.synthesize(query, top_chunks) → SynthesisResult` async via AsyncAzureOpenAI chat.completions ✅ W3 D2
- [x] Citation marker parse(`[chunk-{id}]` regex `\[chunk-([^\]\s]+)\]` ordered + dedup)✅ W3 D2
- [x] tenacity retry on RateLimitError + APITimeoutError(3 attempts exponential 1-8s)✅ W3 D2
- [x] structlog cost log(input_tokens + output_tokens + deployment + latency + citations_count + refused)✅ W3 D2
- [x] 10 unit tests pass(prompt structure / system prompt content / extract_citation_ids / mocked synthesize / refusal detect / temperature passthrough)✅ W3 D2
- [ ] **DEFERRED W3 D3+** Live verify GPT-5.5 chat call quota / latency baseline against real corpus(post Q4 manual smoke)

## F3 — Citation enrichment with image refs

- [x] Citation populate `embedded_images: list[ImageRef]` from cited ChunkRecord(parse from index `embedded_images_json`)✅ W3 D2
- [x] Graceful empty list when R12 deferral applies(`embedded_images_json` empty / `[]` / malformed → [])✅ W3 D2
- [x] QueryResponse.citations ordered by appearance in answer(preserves Synthesizer emit order)✅ W3 D2
- [x] 10 unit tests pass(parse_embedded_images empty/valid/malformed;build_citations order/skip-unknown/populates/empty/real-image-json)✅ W3 D2
- [x] `/query` endpoint full wire:retrieve → synthesize → build_citations → QueryResponse with answer/citations/retrieved_chunks/refused/reranker_used ✅ W3 D2

## F4 — SSE streaming response

- [x] `POST /query/stream` no longer 501 — Vercel AI SDK SSE protocol(`data: {json}\n\n`)✅ W3 D3
- [x] SSE event types:`text-delta` / `citation` / `done` ✅ W3 D3
- [x] `Synthesizer.synthesize_stream(query, chunks) → AsyncIterator[dict]` yields text-delta + final result;openai chat.completions stream=True with stream_options include_usage ✅ W3 D3
- [x] `stream_composer.compose_query_stream` pure-data composer(text-delta passthrough + citation per cited chunk + final done with cumulative latency / refused / reranker_used)✅ W3 D3
- [x] Client disconnect → asyncio.CancelledError logged + propagated;underlying OpenAI stream closed in finally(non swallow)✅ W3 D3
- [x] 9 unit tests pass(4 synthesize_stream:order / refusal / empty-choices / close-on-finally;5 stream_composer:passthrough+citations+done / reranker_used flag / dedup-citation / refused passthrough / hallucinated-skip)✅ W3 D3
- [ ] **DEFERRED W3 D4-D5** Live verify SSE end-to-end against real Azure OpenAI GPT-5.5 streaming(manual smoke when Chat UI lands)

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

- [x] `frontend/app/page.tsx` chat view ✅ W3 D4(Client Component;message state + AbortController + Stop button)
- [x] **`/query/stream` SSE consumed via native fetch + `streamQuery` async generator**(non Vercel AI SDK `useChat` per Karpathy §1.2 — backend uses custom JSON event protocol;wrap useChat = indirection 0 benefit)✅ W3 D4
- [x] CitationCard inline component(`embedded_images[0]` thumbnail click → ScreenshotModal)✅ W3 D4
- [x] `frontend/lib/api/query.ts` ✅ TypeScript types(discriminated SseEvent union)+ `streamQuery` generator
- [x] EKP design tokens only(`oklch(...)` per `lib/theming/tokens.ts`)— no Dify colors / branding ✅ W3 D4
- [x] Reference comment per CLAUDE.md §7:`Layout reference Dify Image 5 chat + citation card (no code copy per CLAUDE.md §7); EKP design tokens only` ✅ W3 D4
- [ ] **DEFERRED W3 D5 F8 polish** shadcn Card / Form swap;split components into `frontend/components/chat/` directory

## F7 — Screenshot modal

- [x] Click citation thumbnail → inline `ScreenshotModal` component opens(fixed inset-0 backdrop;`max-h-[85vh]` image)✅ W3 D4
- [x] Esc keyboard handler → close modal(window keydown listener in ChatPage useEffect)✅ W3 D4
- [x] Click backdrop → close;click image area → propagation stopped(intuitive close interaction)✅ W3 D4
- [ ] **DEFERRED W7+** `/screenshots/{kb_id}/{doc_id}/{img_id}` redirect endpoint(currently `<img src={blob_url}>` direct;public Azurite path 暫 Tier 1 baseline,SAS expiry W7+ Beta+)
- [ ] **DEFERRED W7+** Real thumbnail render once Cloud Blob populated(W2 D3 R12 deferral — `embedded_images_json="[]"` 暫 baseline)

## F8 — Pipeline wizard frontend

- [x] `frontend/app/admin/kb/new/page.tsx` 3-step wizard ✅ W3 D5
- [x] DATA SOURCE → DOCUMENT PROCESSING → EXECUTE step indicator(plain Tailwind;**shadcn Stepper deferred** per Karpathy §1.2 同 W3 D4 chat baseline 一致)✅ W3 D5
- [x] POST sequence wired:create KB → upload doc → trigger ingestion(`kbApi.create()` + `kbApi.uploadDoc()` sequential mutateAsync)✅ W3 D5
- [x] Reference Dify Image 1 wizard layout(EKP `oklch(...)` tokens only;header comment per CLAUDE.md §7)✅ W3 D5

## F9 — Settings tab

- [x] `frontend/app/admin/kb/[id]/page.tsx` Settings ✅ W2 D5 baseline(plain page,non tabbed — single-screen settings + summary + failed docs sufficient per Karpathy §1.2;tabbed UI = unrequired flexibility)
- [x] KbConfig form(embedding_model / embedding_dimension / chunk_strategy / default_top_k / default_rerank_k)✅ W2 D5
- [x] PATCH wire to `/kb/{id}/settings`(TanStack Query `useMutation` + invalidate `['kb', kbId]` + `['kb', 'list']`)✅ W2 D5
- [x] Form validation per Pydantic KbConfig schema(native `<input type=number>` + `<select>` enums + backend 422 surfaced as `patchMutation.isError`)✅ W2 D5
- [ ] **DEFERRED W4+** `reranker` per-KB field — current `KbConfig` Pydantic schema 唔 contain reranker(reranker = settings global 而非 per-KB)。加 = H1 architectural change → 留 W4 reranker shootout 後 reconsider

## F10 — W3 末 retro + W4 kickoff prep

- [x] W03 progress.md retro section completed ✅ W3 D5(7 sub-sections + Phase Gate verdict PASS + carry-overs C1-C8)
- [x] W04 phase folder mkdir + plan.md draft ✅ W3 D5 closeout batch(`docs/01-planning/W04-crag-eval-shootout/{plan,checklist,progress}.md`)
- [x] W03 carry-overs documented ✅ W3 D5(retro § Carry-overs C1-C8 → W4 plan §6 Dependencies on Prior Phase)
- [x] W03 progress.md frontmatter status flipped to `closed` ✅ W3 D5 closeout commit

---

## Cross-Cutting

- [x] Each commit references `progress.md` Day-N entry(R2)✅ W3 D1-D5 全部 commits 都 ref Day-N section
- [x] Component tag in commit message per CC-1 ✅ feat(c01) / feat(c04) / feat(c05,c08) / feat(c10) / feat(c09)
- [x] OQ status sync to `decision-form.md`(R4)— Q5 W3 D1 critical ✅ W3 D1 後段 commit `da0f47f`(Q5 → Path A + Q17/Q18 Chris confirm)
- [ ] **DEFERRED W4 D1** Component design note status bumps(per CC-5):C04 v1→v2(rerank wire),C05 v0→v1,C08 v1→v1.1(SSE wire),C09 v1→v1.1(wizard),C10 v0→v1 — phase Gate G4 explicitly defer non-blocking;batch with W4 kickoff governance
- [x] RISK_REGISTER.md update — R3 🟢 Resolved 2026-05-04(Q5 → Path A,procurement parallel)+ R8 P2 truststore-doesn't-cover-pip documented + R12 Azurite SDK signature deferred to W7+ cloud Blob ✅ W3 D1 後段 batch

---

**Lifecycle reminder**:呢份 checklist 衍生自 `plan.md` deliverables。新加 deliverable 必須先入 plan + changelog,然後再加 checklist item。
