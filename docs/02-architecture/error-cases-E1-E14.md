---
component: C08-api-gateway
status: active
created: 2026-05-15
updated: 2026-05-15
spec_refs:
  - architecture.md §7.3 Edge Cases (E1-E14)
  - components/C08-api-gateway.md
  - backend/api/error_handlers.py
  - backend/api/schemas/errors.py
---

# Edge Cases E1-E14 Mapping(W7 D4 F4.3)

> **Lifecycle**:living document(W7 D4 baseline → W7 D5 F4.5 LIVE smoke verification → W8 Beta cascade)
> **Source of truth for E1-E14 spec**:`docs/architecture.md §7.3`(content-locked v5.1)

## 1. Purpose

Each architecture.md §7.3 edge case maps to:
- **API outcome**:HTTP status + ApiError code(F4.1 contract)
- **UI surface**:user-visible message via F4.2 ErrorBoundaryView OR in-flow indicator
- **Observability**:expected structlog event in F3 audit pipeline OR Langfuse trace tag
- **F4.5 LIVE smoke trigger**:how to reproduce on dev server(W7 D4-D5 if dev server avail,else W8 D1+D4 cascade)

## 2. Mapping Table

| # | Case(per architecture.md §7.3)| API outcome | UI surface | Observability | F4.5 trigger |
|---|---|---|---|---|---|
| **E1** | Query 無相關內容 | **200 OK** + `{"answer": "[refusal phrase]", "refused": true, ...}`(grounded refusal,non-error path)| `<ChatMessage>` shows refusal answer + suggestion;**not** ErrorBoundary | Langfuse trace tag `refused=true`;F3 audit `status_code=200` | Type "What is the airspeed velocity of an unladen swallow?" — out of KB scope |
| E2 | Query 涉多 doc | 200 OK + multi-source citations | Citation card lists all source docs | Langfuse trace tag `n_citations > 1` | Type "compare X and Y" where X+Y in different docs |
| E3 | Chunk 無 image | 200 OK + answer + citation `image_url=null` | Citation card shows "(text-only)" badge | Langfuse trace tag `has_image=false` | Query against text-only chunks |
| E4 | Document parse 失敗 | Ingestion side(non-query path) → KB doc state `parse_failed` | Admin Console KB detail shows red flag + "view error" CTA via ErrorBoundary | structlog `parse_failed` + audit pipeline | Upload corrupt .docx |
| **E5** | LLM API timeout | **504** + `code=pipeline.llm_timeout` + retry hint | ErrorBoundary surfaces "The model took too long — retry once" + Retry CTA | structlog `llm_timeout` + Langfuse trace partial | mocked synthesizer raise `TimeoutError`(F4.4 unit test) |
| E6 | Query 過長(> 2000 char)| **422** + `code=validation.query_too_long` | Inline form error "Shorten the query" before submit;ErrorBoundary if bypassed | structlog `validation_failed` field=query | POST /query body 2001 chars |
| **E7** | Cohere outage | **502** + `code=pipeline.reranker_outage` OR fallback Azure semantic ranker silently | ErrorBoundary "Reranker degraded — results may be lower quality" toast(non-blocking;answer 仍 returned)| Langfuse trace tag `reranker=fallback_azure` | Toggle `cohere_endpoint=""` |
| E8 | Image URL 失效 | 200 OK + citation `image_url=null` | UI shows broken-image placeholder | structlog `image_fetch_failed` | Delete blob then query |
| E9 | Word 內嵌 OOXML(equation/SmartArt)| Ingestion → fallback text representation | Admin doc detail "Limited fidelity" badge | structlog `ooxml_fallback` | Upload .docx with equation |
| E10 | PDF scan + handwriting | Ingestion → doc state `requires_ocr`(Tier 2)| Admin doc detail "OCR required (Tier 2)" badge | structlog `ocr_skipped` | Upload scanned PDF |
| E11 | PPT 動畫 only(無文字)| Slide caption / shape title 為 chunk text(degraded)| Citation card "(animation slide)" annotation | structlog `pptx_animation_only` | Upload .pptx with anim-only slide |
| **E12** | Two docs 撞 chunk_id | Ingestion → namespace by `kb_id` + `doc_id`(zero collision)+ retrieval returns correct chunk | Transparent — no UI surface needed | Index integrity test catches at ingestion;Langfuse trace `chunk_id_namespaced=true` | Two docs both author "intro_001" — verify retrieval returns correct one |
| E13 | KB delete 中途失敗 | **409** + `code=resource.conflict` + "soft delete + cleanup" hint | Admin KB list shows "Deleting…" state with retry CTA | structlog `kb_delete_partial` | Kill process during DELETE /kb/{id} |
| E14 | CRAG 進入 infinite loop | 200 OK + `crag_iterations <= 1` + force return | Citation card "Self-correction max reached" badge | Langfuse trace `crag_max_reached=true` | Force `crag_max_reformulations=1` |

## 3. F4.4 Unit-test verification matrix

| Edge case | Test file | Test function |
|---|---|---|
| E1 grounded refusal | (W3 existing) test_synthesizer.py | `test_refuses_when_low_evidence` |
| E5 LLM timeout | tests/test_error_contract.py(W7 D4 NEW)| `test_503_envelope_for_synthesis_unavailable` + monkeypatch raise TimeoutError |
| E6 query too long | tests/test_api_skeleton.py(W2 existing)| `test_query_request_schema_rejects_too_long_query`(now returns ApiError envelope per F4.1)|
| E7 Cohere outage | (W3 existing) test_reranker.py | `test_factory_returns_none_when_endpoint_empty`(fallback path) |
| E12 chunk_id collision | (W2 existing) test_chunker.py | `test_chunk_id_namespaced_by_kb_doc` |
| E14 CRAG force return | (W4 existing) test_crag.py | `test_crag_force_returns_after_max_reformulations` |

## 4. F4.5 LIVE smoke plan(W7 D4-D5 OR W8 D1+D4)

**Scope**(per W7 plan §2 F4.5):trigger E1 + E5 + E12 → verify graceful UX
**Owner**:Chris(dev server availability dependency,W6 C3 carry-over)
**Trigger condition**:Chris dev server up + `feature_auth_mock=True` + LIVE Azure cred populated

| # | Case | Reproduction step | Pass criterion |
|---|---|---|---|
| E1 | Grounded refusal | curl `/query` body=`{"query": "What is the airspeed velocity of an unladen swallow?", "kb_id": "drive_user_manuals"}` | 200 OK + `refused=true` + UI shows refusal message + Langfuse trace tag visible |
| E5 | LLM timeout | Set Settings synth deployment to bogus or kill Azure OpenAI route mid-request(simulator tool)| 504 + ApiError envelope `code=pipeline.llm_timeout` + ErrorBoundary "Retry" CTA + structlog event |
| E12 | chunk_id collision | Pre-state:two docs each with chunk_id="intro_001";query against both KBs;retrieval returns correct one(no cross-KB leak)| 200 OK + `kb_id` namespace prefix in trace;chunk_id zero collision count |

## 5. Cross-component dependencies

| Component | Wired |
|---|---|
| **C07 Observability** | structlog events E1/E5/E7/E8 + Langfuse trace tags |
| **C08 API Gateway** | error_handlers.py F4.1 envelope + middleware 429 + auth 401 + validation 422 |
| **C09 Admin Console** | ErrorBoundary scope="Admin" surfaces E4/E13 |
| **C10 Chat UI** | ErrorBoundary inline + ChatMessage refusal + citation degraded badges(E1/E3/E8/E11)|

## 6. Tier 2 boundaries

- E10 OCR(handwriting / scanned PDF)— Tier 2 trigger;W7 only flag `requires_ocr`
- Multi-modal retrieval(B 類純圖片搜索)— Tier 2 explicit OUT(architecture.md §11)

## 7. Update history

| Date | Change | Reason |
|---|---|---|
| 2026-05-15 | Initial mapping(W7 D4 F4.3)| F4.1 contract landed;baseline before F4.5 LIVE smoke |
