---
doc: audit-W15-d5-vs-spec
status: complete
audit_date: 2026-05-09
spec_baseline: architecture.md v6 (frozen 2026-05-09 W11 D2 cont)
code_baseline: HEAD = fc5cae3 (post §3 component status follow-up;W15 D5 closeout cascade)
auditor: AI assistant + Chris (technical lead review)
method: 4 parallel general-purpose agents (read-only) + 5 spot-check verifications
---

# EKP Architecture Audit — W15 D5 closeout vs spec v6

> **Living governance doc**。Re-audit cadence:post-W16 D10 retro(Beta deploy assessment trigger);architecture amendment(v6 → v7+);Tier 2 phase entry;major code refactor。
> **Authority**:此 audit doc 屬 cross-cutting governance artifact(同 `RISK_REGISTER.md` + `COMPONENT_CATALOG.md` 平級)。**Not authoritative over** `architecture.md` v6 + `CLAUDE.md` + ADR(per CLAUDE.md §4 權威排序 7-tier)。**Audit findings 唔自動 trigger spec amendment** — 必須 stakeholder approve + ADR 或 §13.X amendment per CLAUDE.md §4.4。

---

## 0. Executive Summary

### Overall verdict:**⚠️ MINOR DRIFT** (substantial alignment;5 major drifts 屬 actionable + traceable;**0 silent drift**)

呢個 audit 對比 EKP Tier 1 codebase(W1-W15 closed,15 phase)vs `architecture.md` v6 spec + 11 component design notes + 15 ADRs。Conclusion:**項目大致按計劃推進**,所有重大 deviation 都係(a)intentional 而 documented in plan changelog / ADR / code comment;或(b)known carry-over 入 W16+ remediation backlog。

### Drift Cumulative Count

| Severity | Count | Rough characterization |
|---|---|---|
| ✅ **Aligned** | ~50 items | Spec 與 code 一致 |
| 🟢+ **Positive drift**(impl 超前 spec)| ~30 items | Code delivers 比 spec 預期更多 — generally good signal,但 spec 應 catch up so future readers 唔誤解 |
| ⚠️ **Minor drift** | ~25 items | Cosmetic / non-load-bearing / tracked in changelog;不影響 Tier 1 production launch |
| 🚨 **Major drift** | **5 items** | Spec 與 code 結構性 divergence — actionable;非 silent;remediation P0/P1 確定 |

### Top 5 Major Drifts(P0/P1 priority)

| # | Cluster | Drift | Spec ref | Code reality | Severity / Action |
|---|---|---|---|---|---|
| **1** | Backend RAG Core(C01)| **PDF parser 缺失** | architecture.md §3.3(PDF supported)+ ADR-0003 + C01-ingestion.md §1 diagram lists `pdf_parser.py` | `backend/ingestion/parsers/` 只有 `docx_parser.py + pptx_parser.py + base.py + __init__.py`;無 `pdf_parser.py`;`strategies.py:51` 將 `pdf` route 去 layout_aware chunker 但無 parser 餵 chunker | 🚨 P0 — deliver(Docling-based)OR ADR amendment defer Tier 2 |
| **2** | Backend RAG Core(C04)| **Cohere v3.5 → v4.0-pro propagation gap** | ADR-0012 + architecture.md §3.2 v5.1 amendment lock `Cohere-rerank-v4.0-pro` | 7+ code locations hardcode `"rerank-v3.5"` / `"cohere-v3.5"`:`storage/settings.py:59` default;`api/schemas/query.py:41-46`;`routes/query.py:94`;`routes/eval.py:14`;`generation/stream_composer.py:54`;`retrieval/reranker/cohere.py:44`;8+ test files | 🚨 P1 housekeeping — 改 default + read `Settings.cohere_rerank_model` runtime;non-blocking(`.env` override 已 lock v4.0-pro per W5 D1) |
| **3** | Backend RAG Core(C05)| **Context Expander step 缺失** | architecture.md §3.1 line 210-211 explicitly lists `[Context Expander] ← prev/next 相鄰 chunk` | `prev_chunk_id`/`next_chunk_id` 喺 ChunkRecord populate(`orchestrator.py:157-158`)+ index store(`schema.json:16-17`),但 retrieval/generation 無 code consume;C05-generation.md §1 diagram 都唔包括;internal-spec inconsistency | 🚨 P0 — deliver(new `generation/context_expander.py`)OR amend §3.1 pipeline diagram |
| **4** | Backend Application(C02+C04+C08)| **Multi-KB invariant ADR-0005 broken at /query boundary** | architecture.md §3.4 + ADR-0005 `kb_id` 全鏈路 propagate + per-KB index naming `ekp-kb-{kb_id}-v{version}` | `routes/query.py` 唔 read `payload.kb_id`(grep 0 hits);`RetrievalEngine.retrieve()` signature 冇 `kb_id`;`HybridSearcher` filter 冇 `kb_id eq` clause;`app.state.retrieval_engine` 係 single shared instance wired to single index;**single-KB Tier 1 functionally OK**,但加第二個 KB silent misroute 全部去 `ekp-kb-drive-v1` | 🚨 P0 latent — Tier 1 single-KB scope 未 trigger 但需要 explicit decision:(a)stamp single-KB only + ADR-0005 amendment;OR(b)wire per-KB retrieval before 2nd KB lands |
| **5** | Frontend(V4 KB Detail)| **§5.5.4 Retrieval Testing tab 4 controls 缺失** | architecture.md §5.5.4 specifies:Vector / Full-Text / Hybrid mode selector + Top K slider + Score Threshold input + Rerank Model toggle | `RetrievalTab` at `frontend/app/admin/kb/[id]/page.tsx:406` 係 free-form textarea + Run query → SSE stream → answer Card + Citations Card;0 mode selector / 0 slider / 0 threshold input / 0 toggle | 🚨 P2 code remediation W16+ — add `<Tabs>` + `<Slider>` + `<Input>` + `<Switch>` + `<Select>` per spec;**don't amend spec** — these are real-value retrieval-mode test harness controls |

### Positive Signal Highlights

- **Tier 1 UI sprint cycle FINAL marker landed**:9/9 views exist at expected URLs;19 shadcn primitives vs ADR-0015 12-15 target;**0 `[oklch(...)]` hardcodes globally**(W15 D3 milestone holds);Playwright 14 tests baseline scaffolded
- **ADR-0014 + ADR-0016 newest amendment 忠實 implemented**:scrypt verbatim parameters(N=2^17/r=8/p=1);MSAL full chain LIVE-ready;hybrid auth dual-path(SSO + self-register);**0 H4 Tier 2 leak**(forgot password / 2FA / OAuth)
- **Backend ahead of spec timeline**:rate limit + audit log + uniform errors + auth middleware delivered W7-W8 vs spec assigning these to "W7+";cost dashboard + alerts + real-time wire delivered W8/W10 vs spec W4
- **Pydantic schemas §4.5**:100% field-shape aligned(QueryRequest/Citation/QueryResponse/KbConfig/KbStatus/EvalReport)
- **DevOps production-grade**:Bicep multi-file split + Key Vault Managed Identity + OIDC federated GHA login + ACA rollback flag + truststore inject for R8 corp proxy

---

## 1. Cluster 1 — Backend RAG Core(C01+C03+C04+C05+C06)

### 1.1 Cluster verdict

⚠️ **Minor drift overall** with isolated 🚨 4 major drifts in C01 + C04 + C05 + cross-cutting Cohere v3.5 propagation gap

### 1.2 C01 — Ingestion Pipeline

**Spec ref**:architecture.md §3.3 + components/C01-ingestion.md + ADR-0003 + ADR-0004

**Reality**:
- `backend/ingestion/orchestrator.py:57-213` IngestionOrchestrator coordinates parse → chunk → screenshot → embed → ChunkRecord;per-doc atomic with FailureRecord
- `backend/ingestion/parsers/{base.py, docx_parser.py, pptx_parser.py}` — Docling-based docx + python-pptx based pptx
- `backend/ingestion/chunker/{layout_aware.py, strategies.py}` — heading-stack walk;target 500 / hard cap 1500 / floor 100;table-as-chunk;TOC/version low_value patterns
- `backend/ingestion/screenshots/{extractor.py, uploader.py}` — SHA256 dedup;HEAD-check via `get_blob_properties`;tenacity retry
- `backend/ingestion/embedding/azure_openai_embedder.py` — AsyncAzureOpenAI;`dimensions=1024` MRL native param

**✅ Aligned**:
- Orchestrator pipeline matches C01 §1 diagram
- Parser Protocol + ParserResult + EmbeddedImage + Table + ParagraphItem 全部 match design note §2 contract
- Layout-aware chunker preserves heading hierarchy → section_path;table-as-chunk;low_value heuristic per ADR-0004
- SHA256 dedup at uploader level;blob path = `{sha256}.{ext}` flat layout(intentional Karpathy §1.2 — dedup intent over strict path template)
- Embedder MRL truncate via native `dimensions=1024`
- ChunkRecord assembly includes all §3.5 fields(chunk_id / kb_id / doc_id / prev_chunk_id / next_chunk_id / low_value_flag / enabled / source_url / ingested_at / embedding[1024])

**🚨 Major drift**:
- **PDF parser missing** — `backend/ingestion/parsers/pdf_parser.py` 不存在
  - C01 §1 diagram 列;ADR-0003 列 `.pdf (Docling)`;architecture.md §3.3 列 PDF
  - `strategies.py:51` route pdf 去 layout_aware chunker 但 chunker 無 parser 餵
  - C01 status 標 v2-stable 但 feature surface 對唔上
  - **W16+ remediation P0**:create `pdf_parser.py` mirroring DoclingDocxParser pattern OR ADR amendment defer Tier 2 + spec §3.3 PDF row removal

**⚠️ Minor drift**:
- 🟢+ Positive: `doc_order` 比 spec hint "positional" 更 rigorous(monotonic index across all item types per `parsers/base.py:36`)
- Blob path `{sha256}.{ext}` flat ≠ §4.6 stated `{kb_id}/{doc_id}/{img_id}.{ext}` template(intentional but spec 應 catch up)
- DoclingDocxParser handles `level >= 6` TOC anomaly by demoting to text paragraph(`docx_parser.py:78-82`)— defensive but undocumented in spec

### 1.3 C03 — Indexing Service

**Spec ref**:architecture.md §3.4 + §3.6 + components/C03-indexing.md

**Reality**:
- `backend/indexing/schema.json` — full 18-field schema literal matching §3.6
- `backend/indexing/schemas.py` — ChunkRecord + ImageRef Pydantic v2 + `make_chunk_id` factory + `to_search_doc()` rename
- `backend/indexing/populate.py` — IndexPopulator async httpx;batch limit 1000;tenacity retry on 5xx/429;per-doc status inspection
- `scripts/create_index.py` — REST CLI for index lifecycle

**✅ Aligned**:
- schema.json HNSW params 100% match §3.6:m=4 / efConstruction=400 / efSearch=500 / metric=cosine
- All 18 fields present with correct types + flags
- 1024d vector via `vectorSearchProfile: ekp-vector-profile`
- `to_search_doc()` renames embedding → content_vector + embedded_images → embedded_images_json
- ChunkRecord Pydantic schema mirrors §3.5 1:1 + `Literal["docx","pdf","pptx"]` for doc_format
- Action="mergeOrUpload" idempotent re-population
- `chunk_id` factory format `kb-{kb_id}_doc-{doc_id}_chunk-{idx:04d}` matches spec example

**⚠️ Minor drift**:
- Default `azure_search_default_index = "ekp-kb-drive-v1"` 對應 spec §3.6 example 嘅 truncated alias;但 §3.4 KB id example `drive_user_manuals` → spec-consistent name 應 `ekp-kb-drive_user_manuals-v1`(spec 內部 ambiguity)
- `index_service.py` + `azure_search_client.py` 列喺 C03 §1 diagram 但 NOT 存在(consistent with §8 todo "deferred — populate.py + create_index.py covers W2 needs");design note 應 catch up
- `to_search_doc()` 唔 enforce embedding length=1024(只 Pydantic `min_length=1`);spec §3.6 explicit dimensions=1024

**🚨 Major drift**:None

### 1.4 C04 — Retrieval Engine

**Spec ref**:architecture.md §3.1 + §3.2 + components/C04-retrieval.md + ADR-0012

**Reality**:
- `backend/retrieval/hybrid.py` — async REST;`queryType: semantic` + `semanticConfiguration: ekp-semantic-config`;`vectorQueries[].fields = "content_vector"`;default filter `enabled eq true and low_value_flag eq false`
- `backend/retrieval/retrieval_engine.py` — embed query → hybrid search top fetch_k → optional rerank → top_k;`@observe_async` Langfuse trace
- `backend/retrieval/reranker/{base.py, cohere.py, voyage.py, zeroentropy.py, azure_semantic.py, factory.py}` — Reranker Protocol + 4 implementations + factory dispatcher with hybrid-only safety fallback

**✅ Aligned**:
- Hybrid pipeline matches §3.1:BM25 + vector RRF via single search call
- Default filter exactly per §3.6
- Reranker Protocol allows hot-swap per W4 shootout
- Cohere `/v2/rerank` REST shape matches Marketplace contract
- Azure semantic ranker score normalization(0-4 → 0-1)preserves cross-vendor comparability
- Hybrid overfetch:`fetch_k = max(top_k, 50)` when reranker present
- Empty query / empty candidate early returns per C04 §4 edge case

**🟢+ Positive drift**:
- Per-stage latency tracking in `RetrievalResult`(embed/search/rerank latency_ms)beyond spec C04 §2
- `@observe_async` integration with C07 Langfuse beyond C04 §2 spec mention

**🚨 Major drift**:
- **Cohere v3.5 → v4.0-pro propagation gap**(see Cross-cutting CC-2 below for full enumeration)— `Settings.cohere_rerank_model = "rerank-v3.5"` default at `storage/settings.py:59` + 6+ other code locations + 8+ test files
- W16+ remediation P1:update default + replace hardcoded strings with `settings.cohere_rerank_model` runtime + update tests

### 1.5 C05 — Generation Pipeline

**Spec ref**:architecture.md §3.1 + §3.2 + components/C05-generation.md + ADR-0007 + ADR-0011

**Reality**:
- `backend/generation/synthesizer.py` — GPT-5.5 chat.completions wrapper;citation regex `\[chunk-([^\]\s]+)\]` ordered+dedup;tenacity retry;structlog cost log;REFUSAL_PHRASE substring detection;`synthesize_stream()` async generator
- `backend/generation/prompt_builder.py` — `REFUSAL_PHRASE = "I cannot find this in the available documentation"`;SYSTEM_PROMPT enforces citation + refusal + 150 word target + match user language
- `backend/generation/citation_enrichment.py` — `parse_embedded_images` JSON decode + `build_citations` ordered + hallucinated-id silent skip
- `backend/generation/crag.py:117-407` — CragGrader(grade + rewrite_query)using GPT-5.4-mini judge + CragLoop(refine: grade → maybe rewrite + re-fetch top_k=20 + re-synth);threshold 0.70;max_corrections=1;graceful fallback
- `backend/generation/stream_composer.py` — pure-data composer mapping `text-delta*` → passthrough + `result` → citation* + done

**✅ Aligned**:
- Custom CRAG ~530 lines single file `crag.py`;NO LangGraph dependency per ADR-0011
- L2 CRAG loop:grade → rewrite → re-retrieve top_k=20 → re-synth → optional second grade per §3.1 + ADR-0007
- GPT-5.5 synthesizer + GPT-5.4-mini grader split per §3.2
- Threshold 0.70;max_reformulations from `Settings`
- Citation extractor regex matches spec format
- Citation validation skips hallucinated ids(logged warning)per C05 §3
- Refusal phrase substring match
- Streaming SSE async generator
- Graceful CRAG fallback on any sub-stage exception → `fallback_used=True`
- `@observe_async` + `@observe_llm_async` Langfuse coverage

**🟢+ Positive drift**:
- Secondary post-correction grader call(`grade2`)for `confidence_after` field 比 ADR-0007 minimum 更 rigorous
- Per-stage cost trace fields(grader / rewrite / extra_synth / extra_retrieval)richer than C05 §2 outputs spec
- prompt_builder includes section_path in chunk context(`prompt_builder.py:42`)— better grounding signal
- GPT-5 reasoning-style temperature handling fix(`synthesizer.py:74-95`)— defaults None to omit param

**🚨 Major drift**:
- **Context Expander step missing** — architecture.md §3.1 line 210-211 explicit pipeline step `[Context Expander] ← prev/next 相鄰 chunk` between Cohere Rerank 同 GPT-5.5 Synthesis
  - ChunkRecord populates `prev_chunk_id` + `next_chunk_id`;index stores 兩個 fields
  - 但 NO code module reads them at retrieval/generation time
  - top-5 chunks 直接 passed to `build_prompt()` 無 prev/next neighbor expansion
  - C05 §1 internal architecture diagram 都唔 include — internal-spec inconsistency between §3.1 + C05 §1
  - **W16+ remediation P0**:deliver `generation/context_expander.py`(prev/next lookup + prepend/append top-5 chunk text before prompt build)OR amend §3.1 to remove step + repurpose prev/next as citation-render-only metadata

**⚠️ Minor drift**:
- REFUSAL_PHRASE 係 English literal `"I cannot find this in the available documentation"` 而 C05 §3 spec example refusal 係中文 `"信心不足,請聯絡 Admin"`(Tier 1 mixed corpus 觸發風險)
- `stream_composer.py:54` hardcodes `"reranker_used": "cohere-v3.5"`(cross-cutting CC-2)

### 1.6 C06 — Eval Framework

**Spec ref**:eval-methodology.md + architecture.md §6.3 + components/C06-eval.md + ADR-0012

**Reality**:
- `scripts/validate_eval_set.py` — stdlib YAML validator
- `backend/eval/runner.py` — EvalRunner runs YAML eval-set against RetrievalEngine;dual-mode recall@5(strict + keyword fallback)
- `backend/eval/gates.py` — `gate1_recall_at_5()` with threshold 0.80
- `backend/eval/ragas_runner.py` — RagasRunner with 4 metrics;injectable evaluator pattern;mean/median/p95
- `backend/eval/eval_set_augmentor.py` — W10 D1 F4.2 real-query augmentation pipeline
- `scripts/run_reranker_shootout.py` — W4 D3 F3 driver(NOT in `backend/eval/shootout.py`)

**✅ Aligned**:
- EvalRunner pipeline:load YAML → invoke C04 → compute Recall@5 → aggregate report
- Gate 1 threshold 0.80 matches spec §6.3
- RAGAs 4 metrics:faithfulness / answer_relevancy / context_precision / context_recall
- Judge LLM = GPT-5.4-mini(passed as `judge_deployment` to RagasRunner)
- Per-query trace + cost tracking
- YAML report serialization with metadata + aggregate + per_query
- Dual-mode recall(strict + keyword fallback)handles eval-set-v0 placeholder chunk_ids gracefully
- Reports written to `reports/`(gitignored)

**🟢+ Positive drift**:
- `RagasAggregate` includes p95(nearest-rank)beyond spec — useful for tail analysis
- Injectable evaluator pattern makes RagasRunner unit-testable
- `subset_size` knob for cost containment

**⚠️ Minor drift**:
- **Gate 2 decision logic missing** — only `gate1_recall_at_5()` exists;Gate 2(4 metric ±5pp per ADR-0012 + §6.3)verdict driven manually via `reports/ragas-cohere-subset20.json` + `reports/ragas-azure-subset20.json` comparison rather than coded gate function。Acceptable for W6 retro context but C06 §1 spec lists `gates.py — Gate 1 / Gate 2 decision logic`
- `judge.py` standalone module never delivered — judge logic distributed across `crag.py` + ragas evaluator(architectural simplification breaks C06 §1 diagram)
- `shootout.py` 喺 `scripts/run_reranker_shootout.py`(operational driver)而非 `backend/eval/shootout.py`(library module)

**🚨 Major drift**:None(structural drift documented in C06 §8 todos as deferred)

---

## 2. Cluster 2 — Backend Application(C02+C07+C08+C12)

### 2.1 Cluster verdict

⚠️ **Minor drift overall** — mostly **🟢+ positive drift**(impl 比 spec 超前);1 🚨 multi-KB invariant gap(latent today,critical if 2nd KB activates)

### 2.2 Endpoint Inventory(C08 critical sub-task)

**Spec promises 18 endpoints。Reality = 22 endpoints(+6 auth +2 observability post-v5 extensions)**

| # | Endpoint | Method | Spec §4.4 | Status | Code file:line | Notes |
|---|---|---|---|---|---|---|
| meta | `/health` | GET | (implicit) | ✅ wired | `backend/api/server.py:178` | Liveness probe |
| 1 | `/query` | POST | #1 | ✅ wired full RAG | `routes/query.py:52` | Hybrid + rerank + synth + CRAG L2 |
| 2 | `/query/stream` | POST/SSE | #2 | ✅ wired | `routes/query.py:160` | Vercel AI SDK SSE protocol |
| 3 | `/feedback` | POST | #3 | ✅ wired | `routes/feedback.py:27` | Forwards to Langfuse `score()` |
| 4-8 | `/kb` + `/kb/{id}` + `/kb/{id}/settings` | GET POST GET DELETE PATCH | #4-#8 | ✅ wired | `routes/kb.py:15-62` | List/Create/Detail/Delete/Settings |
| 9-13 | `/kb/{id}/documents` + `/chunks` GET | GET POST DELETE POST GET | #9-#13 | 🟡 stub 501 | `routes/documents.py + chunks.py` | **W16 F5 known carry-over**(部分 documented;部分 W2-era deferral) |
| 14 | `/kb/{id}/chunks/{chunk_id}` | PATCH | #14 | 🟡 stub 501 | `routes/chunks.py:26` | W2 deferred |
| 15a | `/eval/run` | POST | #15 | 🟡 stub 501 | `routes/eval.py:18` | **W16 F5 known carry-over** |
| 15b | `/eval/shootout` | POST | #16 | 🟡 stub 501 | `routes/eval.py:28` | **W16 F5 known carry-over** |
| 17 | `/debug/trace/{trace_id}` | GET | #17 | 🟡 stub 501 | `routes/debug.py:8` | **W16 F5 known carry-over** |
| 18 | `/screenshots/{kb_id}/{doc_id}/{img_id}` | GET | #18 | 🟡 stub 501 | `routes/screenshots.py:8` | W2 deferred |
| ext1-6 | `/auth/{refresh, logout, register, verify-email, login, resend-verification}` | POST | (post-v5) | ✅ wired | `routes/auth.py:103-335` | 🟢+ ADR-0014 hybrid auth |
| ext7-8 | `/observability/{cost-summary, alerts}` | GET | (post-v5) | ✅ wired | `routes/observability.py:46, 109` | 🟢+ W8 F5.2/F5.4 + W10 realtime |

**Coverage**:9 / 18 spec endpoints fully wired;9 stubs(4 W16 F5 documented + 5 W2-era deferrals not explicitly framed in W15 carry-over);+8 post-v5 extensions

**⚠️ Minor drift**:Stub coverage mismatch with W15 carry-over framing — 5 extra stubs(`#10/#11/#12/#13/#14/#18`)需要 W16 F5 plan explicit enumeration 或 W17+ carry-over

### 2.3 Pydantic Schema Inventory(C08 §4.5 verify)

**Verdict**:Spec §4.5 schemas 全部 present + field-shape exact

| Schema | Fields match | Code file:line |
|---|---|---|
| QueryRequest | ✅ 8/8 | `api/schemas/query.py:34` |
| Citation | ✅ 8/8 | `api/schemas/query.py:23` |
| QueryResponse | ✅ 10/10 | `api/schemas/query.py:51` |
| ImageRef / ChunkPreview | ✅ implicit | `api/schemas/query.py:8, 16` |
| KbConfig | ✅ 5/5 | `api/schemas/kb.py:9` |
| KbStatus | ✅ 10/10 | `api/schemas/kb.py:37` |
| KbCreate / FailureRecord | ✅ implicit | `api/schemas/kb.py:17, 31` |
| EvalReport / FailedQueryDetail | ✅ 8/8 + implicit | `api/schemas/eval.py:14, 6` |
| FeedbackRequest / FeedbackResponse | ✅ implicit | `api/schemas/feedback.py:8, 14` |
| ApiErrorBody / ApiErrorResponse / ErrorCodes | 🟢+ post-v5 | `api/schemas/errors.py:13, 28` — uniform error contract W7 D4 F4.1 |
| auth schemas(9 total)| 🟢+ post-v5 | `api/schemas/auth.py` ADR-0014 |
| observability schemas(5 total)| 🟢+ post-v5 | `api/schemas/observability.py` W8/W10 |

### 2.4 C02 — Knowledge Base Manager

**✅ Aligned**:Filename override(`service.py + storage.py + __init__.py` vs spec `kb_service.py + kb_models.py`)documented in C02 §1;in-memory `InMemoryKBBackend` + `KBStorageBackend` Protocol + lru_cache singleton + Annotated DI + domain exceptions + 5 endpoints + 14 unit tests

**Verdict**:✅ Aligned no drift

### 2.5 C07 — Observability Stack

**🟢+ Major positive drift** — implementation 比 spec 超前 1-2 phase:
- 7 files vs spec single `langfuse_tracer.py`(`alerts.py + cost_estimator.py + realtime_cost.py + query_collector.py + weekly_signal_report.py + observe.py + langfuse_tracer.py`)
- Real lazy SDK init with degrade-graceful behavior
- `@observe_async` + `@observe_llm_async` + `@observe_streaming` decorators wired on `/query`, RetrievalEngine, synthesizer, CRAG stages
- 6 declarative AlertRule(api_latency_p95 / api_error_rate / cost_spike / crag_trigger_rate / rate_limit_saturation / langfuse_export_lag)
- Cost dashboard real-time wire(W8 D5 / W10 D3 vs spec W4)
- H5-compliant scrubbing(only token COUNTS,no prompt/answer content)
- `flush_tracer()` shutdown drain

**⚠️ Minor drift**:`trace_id=""` placeholder in `QueryResponse`(`routes/query.py:105, 153`)— `@observe_async` 內部 emit Langfuse 但 client-facing trace_id 唔 surface;debug view stub `/debug/trace/{id}` 冇 anchor(closure expected with W16 F5)

### 2.6 C08 — API Gateway

**🟢+ Significant positive drift**:
- 22 endpoints registered vs 18 spec
- Lifespan() pattern + Annotated[Service, Depends()] modern DI
- Rate limit middleware(`middleware/rate_limit.py:166`)50/min + 5 concurrent W7 D2 F2
- Hybrid auth middleware(`middleware/dependency.py:35`)session + mock + MSAL 3-tier
- Audit log middleware(`middleware/audit_log.py:84`)with H5 redaction
- Uniform `ApiError` envelope(`error_handlers.py`)W7 D4 F4.1
- Streaming `/query/stream` with `asyncio.CancelledError` handling
- truststore.inject_into_ssl()`server.py:9-11` R8 corp proxy mitigation

**⚠️ Minor drift**:
- CORS middleware NOT registered(may be handled by Front Door / SWA upstream;local dev needs verify)
- `/health` serves both liveness + readiness probes(spec 暗示 separate `/ready`)
- `auth_routes.router` register WITHOUT router-level auth Depends(correct for public auth endpoints,但 inconsistent style;documented in `server.py:188-189` comment)

### 2.7 C12 — DevOps & Infra

**🟢+ Production-grade delivery**:
- Multi-stage Dockerfile(uv + non-root UID 10001 + HEALTHCHECK)
- Bicep IaC multi-file split(`backend.bicep + networking.bicep`)
- Key Vault Managed Identity 6 secret refs
- OIDC federated GHA login(no client secrets)
- ACA rollback flag via `workflow_dispatch.inputs.rollback`
- Front Door / SWA upstream(ADR-0009 + `infrastructure/swa/README.md`)

**⚠️ Minor drift**:
- docker-compose 唔 include `fastapi` + `nextjs` services(deliberate per file comment §1 — uses `uv run` + `pnpm dev` for hot reload;但 spec §4.3 列咗 → 應 spec catch up)
- ACA scale `minReplicas:1 maxReplicas:5`(spec hint 10 — Beta cohort calibration)
- Bicep filename `aca/backend.bicep` vs spec §4.2 `containerapp.bicep`(spec 應 catch up)

---

## 3. Cluster 3 — Frontend UI(C09+C10)— 9 Views

### 3.1 Cluster verdict

⚠️ **Minor drift overall** — substantial alignment;**0 silent drift**(所有 deviation tracked in code/plan changelog);1 🚨 V4 Retrieval Testing tab structural mismatch

### 3.2 Route Inventory

**9 / 9 views exist at expected URLs。✅ No missing routes。**

| Route | View | Spec § | Status | Code path |
|---|---|---|---|---|
| `/` | V7 Landing | §5.9 | ✅ | `app/page.tsx` (240 L) |
| `/chat` | V1 Chat | §5.2 | ✅ | `app/chat/page.tsx` (328 L) — Path moved per ADR-0015 |
| `/admin` | V2 Admin Dashboard | §5.3 | ✅ | `app/admin/page.tsx` (319 L) |
| `/admin/kb` | V3 KB List | §5.4 | ✅ | `app/admin/kb/page.tsx` (311 L) |
| `/admin/kb/[id]` | V4 KB Detail | §5.5 | ✅ | `app/admin/kb/[id]/page.tsx` (881 L) — 5-tab structure |
| `/admin/kb/new` | V4 Pipeline Wizard | §5.5.3 | ✅ | `app/admin/kb/new/page.tsx` (557 L) — 3-step wizard |
| `/eval` | V5 Eval Console | §5.6 | ✅ | `app/eval/page.tsx` (618 L) |
| `/debug/[traceId]` | V6 Debug View | §5.7 | ✅ | `app/debug/[traceId]/page.tsx` (401 L) — 6-stage |
| `/login` | V8 Login | §5.10 | ✅ | `app/login/page.tsx` (204 L) |
| `/register` | V9 Register | §5.11 | ✅ | `app/register/page.tsx` (653 L) — 3-step inline wizard |

### 3.3 Visual Identity Adherence

**✅ MILESTONE held**:
- shadcn/ui only:**0 Material UI / Ant Design / Chakra / styled-components / emotion**(verified `package.json:18-28` pure `@radix-ui/*`)
- **`[oklch(...)]` hardcode count = 0**(W15 D3 MILESTONE preserved)
- Design tokens flow:`lib/theming/tokens.ts:18 ekpTokens` "Warm Charcoal + Coral Accent" → `tailwind.config.ts:3 import` → `globals.css:15-69 :root + .dark CSS vars` → utility classes consumed
- shadcn `components.json`:`style: "new-york"`,`rsc: true`,`cssVariables: true`,`iconLibrary: "lucide"`
- 19 shadcn primitives populated(Avatar/Badge/Breadcrumb/Button/Card/Checkbox/Dialog/Dropdown/Input/Label/Select/Separator/Sheet/Skeleton/Slider/Sonner/Switch/Tabs/Textarea)— **🟢+ exceeds ADR-0015 12-15 target**

### 3.4 V1-V9 Per-View Audit

#### V1 Chat(`/chat`)— ⚠️ Minor drift × 2(intentional)

**🟢+ Aligned**:`MessageBubble` user/assistant differentiation;`CitationCard` chunk_title + doc_title + section_path + embedded_images thumbnail + relevance score;`ScreenshotModal` Esc + click-backdrop close;refusal banner + reranker badge

**⚠️ Minor drift**(intentional documented):
- `streamQuery` async generator over native fetch + TextDecoder + SSE-frame split(`lib/api/query.ts:82`)— **NOT** Vercel AI SDK `useChat`;rationale per W3 D4 docstring:custom JSON event protocol → wrap = indirection 0 benefit per Karpathy §1.2;**spec §5.2 應 catch up**
- KB selector dropdown absent;`KB_ID = 'drive_user_manuals'` hardcoded(`chat/page.tsx:47`)— "W3 single-KB POC;multi-KB selector W7+ Beta" inline comment

#### V2 Admin Dashboard(`/admin`)— ✅ Aligned

AdminShell sidebar 3 NAV_ITEMS(Settings deferred per W7+);4-card stats(Knowledge Bases / Documents / Chunks / **System status** instead of "Last Activity");Failed ingestion table 替代 Recent log(operational signal wins per W14 D1 F1 design ref §2.2)

#### V3 KB List(`/admin/kb`)— ⚠️ Minor drift × 2

**🟢+ Beyond spec**:Search Input + Sort Select(Last indexed / Name / Documents)

**⚠️ Minor drift**:
- Card 缺 `storage_size` 同 `last_query_rate`(只喺 Detail page Documents tab)
- W16+ remediation:once backend exposes query-rate metric,加 cards

#### V4 KB Detail(`/admin/kb/[id]`)— 🚨 1 Major drift + ⚠️ 2 Minor drift

**5-tab structure**(Documents / Chunks / Pipeline / Retrieval Testing / Settings)+ URL `?tab=` state

**⚠️ Minor drift × 2**(blocked by backend 501 stubs):
- Documents tab:3 stat cards + BackendStubNote("GET /kb/{id}/documents 501")+ FailuresSection + Upload CTA — **document table missing because backend stub returns 501**
- Chunks tab:2 stat cards + BackendStubNote + cross-link to Retrieval — **per-chunk inspector missing same reason**
- 兩個 surfaced via BackendStubNote pattern;NOT silent
- W16+ remediation:Backend wire `GET /kb/{id}/documents` + `/chunks` per spec §5.5.1 + §5.5.2

**🚨 Major drift**:
- **§5.5.4 Retrieval Testing tab 4 controls 缺失**:
  - Spec lists Vector / Full-Text / Hybrid mode selector + Top K slider + Score Threshold input + Rerank Model toggle
  - Reality(`page.tsx:406 RetrievalTab`):free-form textarea + Run query → SSE stream → answer Card + Citations Card sorted by score + reranker badge + refusal banner
  - 0 mode selector / 0 slider / 0 threshold input / 0 rerank toggle
  - Functional substitute("test query" panel)but spec violation("retrieval-mode test harness")
  - **W16+ remediation P2**:add `<Tabs>` + `<Slider>` + `<Input>` + `<Switch>` + `<Select>` per §5.5.4(spec wins;don't amend)

**⚠️ Minor drift**:Pipeline tab 係 read-only config visualization;wizard 喺 standalone `/admin/kb/new`(intentional per W14 D3 plan §7 "Tier 1 read-only");spec §5.5.3 implies wizard inside Pipeline tab — defensible split but spec amendment OR PipelineTab wizard reuse

**Settings tab**:✅ Identity(read-only)+ Indexing config(editable embedding/dim/chunk_strategy/top_k/rerank_k)PATCH wire + Danger Zone(Re-index / Delete confirmation Dialog)

#### V5 Eval Console(`/eval`)— ⚠️ Minor drift × 1

**✅ Aligned**:Top filter bar(eval set + Run + Run Single)+ Grid `md:grid-cols-[280px_1fr]`(RunConfigCard + main panel);RunConfigCard(LLM + Reranker + Top K + CRAG threshold Slider 🟢+ + Intent type);MetricCardsGrid 4 cards w/ PASS/FAIL/N/A badges + threshold display + empty state with Run CTA;`/eval/run` 501 → toast.info;RerankerShootoutCard 4-row(Cohere v4.0-pro RECOMMENDED / Azure built-in Fallback / Voyage DROPPED / ZeroEntropy DROPPED)

**🟢+ Beyond spec**:CRAG Slider(threshold 0-1)vs spec "on/off";per-row recommendation badges with status semantics

**⚠️ Minor drift**:Failed Queries table 4-col(Query ID / Query / Failed metrics / Inspect)vs spec §5.6 5-col(添 Expected / Got)

#### V6 Debug View(`/debug/[traceId]`)— ⚠️ Minor drift(documented)

**✅ Aligned**:Header + Back to Eval + traceId mono + Open in Langfuse;SummaryCard(Latency / Cost / Query 3 metric cards);stub mode placeholder when API 501;PipelineStageCollapsible custom impl with ChevronDown rotation + duration_ms/cost label + expandable JSON preview

**⚠️ Minor drift**:**6 stages** vs spec §5.7 "9 stages"
- Plan F2.2 §7 changelog(D2)logs:"design ref §2.6 wireframe + plan F2.2 own enumeration agree on 6 stages... plan internal inconsistency between '9-stage' header + 6-enumerated → align with wireframe 6"
- Wireframe + design-ref won;spec §5.7 lagging
- **Reconciliation needed**:spec edit §5.7 9 → 6 OR code expansion 6 → 9(missing:Query Rewriter / Re-retrieve / Context Expander — these are conditional sub-stages)
- Cross-ref to C05 Major drift #3(Context Expander)— 兩個一齊 reconcile

#### V7 Landing(`/`)— ✅ Aligned

Server Component + SiteHeader + Hero + 3 FeatureHighlights + HowItWorks 3-step + SiteFooter;Pricing/Docs disabled(post-launch);**No Tier 2 leak** in feature copy

#### V8 Login(`/login`)— ✅ Aligned

Split layout `flex-col md:flex-row` + `<BrandPanel>`;email/password Input + Sign in Button(`authApi.login` POST + localStorage session-token);Separator "or" + "Sign in with Microsoft" SSO redirect;Forgot password = **disabled** with `title="Tier 2 (post-Beta)"` ✅;Register link → `/register`;handleAuthError switch for INVALID_CREDENTIALS / EMAIL_NOT_VERIFIED toast

#### V9 Register(`/register`)— ✅ Aligned + 🟢+ enhancements

Split layout reuse `<BrandPanel>` + Stepper(1→2→3);Step 1 account info(email/password/confirm/display name + 5-bar strength indicator);Step 2 email verify(6-digit code 6 separate digit boxes with auto-advance + Backspace + Arrow keys + Paste distribution + Resend 60s cooldown);Step 3 welcome(default-KB read-only + "Start asking" → `/chat`)— **6-box paste + arrow-key UX exceeds spec wording**

### 3.5 Streaming + Citation(C10)

✅ SSE streaming wired via `streamQuery` async generator + ReadableStream reader + `\n\n` SSE-frame split + JSON.parse per frame;Discriminated union `SseEvent = TextDeltaEvent | CitationEvent | DoneEvent`;Citation inline rendering grid 2-col;ScreenshotModal click thumbnail → modal;AbortController Stop button clean cancellation

**⚠️ Minor drift**:`ai`(Vercel AI SDK)package in deps `package.json:30` 但 unused;C10 swap → native generator(`chat/page.tsx:13` + `lib/api/query.ts:11` documented);cleanup candidate W16+

### 3.6 Component Reuse

| Component | Status | Notes |
|---|---|---|
| AdminShell sidebar | ✅ Single source `components/nav/admin-shell.tsx` consumed by 3 layouts | |
| UserMenu | ✅ `components/auth/user-menu.tsx` | mobile + desktop AdminShell |
| Breadcrumb | ✅ `BreadcrumbNav` in admin-shell auto-derives from `usePathname()` | SEGMENT_LABELS dict |
| Pipeline Stepper | ⚠️ Duplicated 2x(register + kb/new) | Rule of 3 NOT yet triggered per Karpathy §1.2;defensible |
| Collapsible(V6)| ⚠️ Bespoke `PipelineStageCollapsible` inlined custom | shadcn Accordion NOT installed;single-use defensible |
| BrandPanel | ✅ Shared by V8 + V9 | |
| BackendStubNote | ⚠️ Local def at V4(`kb/[id]/page.tsx:867`)| Extraction candidate once V5+V6 stub-aware UI patterns evolve |
| **StatCard** | ⚠️ **Duplicated 3x(V2/V4/V5)— rule-of-3 reached** | Extraction candidate `components/ui/stat-card.tsx` |

### 3.7 Playwright E2E Baseline

- W15 D4 plan target:13 tests(4 golden-path + 5 admin-path + 5 visual baseline)
- **Actual count:14 tests**(4 + 5 + 5)— 🟢+ plan arithmetic error;sums to 14 not 13
- Coverage:V7/V8/V9/V1 golden-path + V2/V3/V5/V6/Sidebar admin-path + V7/V8/V9/V2/V5 visual baseline
- Mock auth via `NEXT_PUBLIC_AUTH_MOCK=true` env in `playwright.config.ts` webServer
- Visual baseline assertion `toHaveScreenshot()` with Playwright default `maxDiffPixelRatio`
- **Coverage gaps acceptable per W15 plan**:V3 KB List + V4 KB Detail 5-tab flow + V6 Debug pixel baseline absent(covered by render-only assertions);no interactive flow tests(Beta hardening deferred)

---

## 4. Cluster 4 — Identity + Email Verification(C11+C13)

### 4.1 Cluster verdict

✅ **Aligned overall**(with 2 known carry-overs CO_F5_cookie + CO_F6a/c)— **0 🚨 major drift**;newest ADR-0014 + ADR-0016 amendment 忠實 implemented

### 4.2 Auth Endpoint Inventory

| Endpoint | Spec ref | Status | Notes |
|---|---|---|---|
| POST `/auth/register` | ADR-0014 + §3.7 + §5.11 | ✅ wired | scrypt hash + EmailProvider dispatch + fail-soft per §3.7 |
| POST `/auth/verify-email` | ADR-0014 + §3.7 + §5.11 Step 2 | ✅ wired | Idempotent + 6-digit numeric match + expiry check |
| POST `/auth/login` | ADR-0014 + §5.10 | ✅ wired | scrypt verify + verified-email gate(403 vs 401)+ 7-day session token |
| POST `/auth/resend-verification` | §5.11 Step 2 Resend | ✅ wired | 60s cooldown + identity-leak-resistant response |
| POST `/auth/refresh` | §4.4 | 🟡 stub partial | Mock returns dev-token;real MSAL refresh 503 fail-closed;**self-register session refresh = CO_F5_refresh** |
| POST `/auth/logout` | §4.4 | ✅ wired | Revokes session token if present;mock + MSAL paths preserved |
| MSAL JWT validation Depends path | ADR-0014 路徑 A + Q11 | ✅ wired LIVE-ready | Full chain JWKS + RS256 + iss/aud/exp/nbf + oid/tid;503 fail-closed when Track A IT cred pending |
| Mock auth bridge | W7 D1 F1.2.1 | ✅ preserved | `feature_auth_mock=True` activated |
| Session resolution(3rd path)| ADR-0014 路徑 B + W13 F5.6 | ✅ wired | Hybrid switching;session token branch sits in front of mock/MSAL fork |

### 4.3 Frontend Auth Route Inventory

| Route | View | Status | Notes |
|---|---|---|---|
| `/login` | §5.10 V8 | ✅ | Split layout + dual paths(SSO via `useAuthStore.signIn` + self-register via `authApi.login`)|
| `/register` | §5.11 V9 | ✅ | 3-step state machine + 6-digit OTP boxes + 60s resend |
| `/verify-email` | §3.7 + §5.11 | N/A by design | In-wizard Step 2(industry standard OTP UX);no token-link landing |
| MSAL provider lib | ADR-0014 路徑 A | ✅ wired LIVE-ready | `@azure/msal-browser ^5.9.0` + `@azure/msal-react ^5.3.2`;loginRedirect + handleRedirectPromise + acquireTokenSilent ~50min refresh;lazy SSR-safe singleton |
| Mock MSAL bridge | W7 dev mode | ✅ preserved | `NEXT_PUBLIC_AUTH_MOCK=true` activated |
| Single switching point | parallel to backend | ✅ wired | `lib/auth/index.ts:39-78` 3-tier:session bearer → mock → MSAL;precedence matches backend |

### 4.4 Tier Boundary Check(critical — H4 enforcement)

**✅ ALL CLEAN**:
- Forgot password leak:**none** in implementation。Login page 有 visually-disabled `<span>` with `title="Forgot password — Tier 2 (post-Beta) per ADR-0014"`(`app/login/page.tsx:162-167`)— no route, no handler, no `/auth/forgot-password` endpoint
- 2FA / TOTP leak:**none**。Zero TOTP/2FA code anywhere
- OAuth Google/GitHub leak:**none**。Zero references except docs(intentional Tier 2 deferral notes)

### 4.5 ADR-0016 scrypt switch verification

- **`argon2` package import count**:✅ **0** — 0 references in `pyproject.toml` deps;0 across `.py` files(only docstring/comment references in `security.py:3-5` + `email_provider.py:15` documenting ADR-0016 switch)
- **`hashlib.scrypt` usage**:✅ wired at `backend/api/auth/security.py:42-80`
  - **Parameters**:**N=2^17(131072)/ r=8 / p=1 / dklen=64 / salt=16 bytes / maxmem=256 MB**(raised from OpenSSL default 32 MB to support N=2^17)
  - **Storage format**:`scrypt$N$r$p$salt_hex$hash_hex` — matches ADR-0016 §Decision verbatim(forward-compatible)
  - **Constant-time compare**:`secrets.compare_digest`(line 80)
  - **Defensive parsing**:malformed hash → False(line 60-67)instead of raising

### 4.6 C11 — Identity & Access

✅ **Aligned**:全部 7 expectation 落地(MSAL full chain + self-register 4 endpoints + mock bridge + single switching point + scrypt + H4 boundary clean)

**⚠️ Minor drift × 2(known carry-overs)**:
- **CO_F5_refresh** — `/auth/refresh` self-register session 唔 handle;`auth.py:115-117` 明確 noted as W13 retro carry-over
- **CO_F5_cookie** — current localStorage(`ekp_session_token`)vs ADR-0014 line 43 mandates httpOnly cookie;XSS exposure widened(Tier 1 in-memory POC scope acceptable;Beta hardening trigger)

### 4.7 C13 — Email Verification Service

✅ **Aligned**:Lazy SDK import + ConsoleEmailProvider + AcsEmailProvider Protocol-based factory + tenacity retry + asyncio.to_thread wrap + plain text + HTML alt templates + sender default `noreply@dev.ekp-beta.ricoh.com`(matches §3.7 line 396)+ `feature_email_mock=True` default + `acs_connection_string=""` default → ConsoleEmailProvider fallback

**⚠️ Spec drift × 2(intentional per W13 plan changelog)**:
- **architecture.md §3.7 line 394** says `secrets.token_urlsafe(32)` for cryptographic randomness。Impl 用 **6-digit numeric OTP** via `secrets.randbelow(1_000_000)`(`security.py:83-85`)。Documented in `W13-user-facing-views/checklist.md:59`:"verification token 32-char URL-safe → 6-digit numeric code(V9 wireframe §2.9 + OTP UX)";**UI-driven decision**(V9 wireframe shows 6 separate digit boxes);crypto randomness preserved via `secrets`;24h expiry preserved(`VERIFICATION_TOKEN_TTL_SEC = 24 * 60 * 60`)
- **column naming**:spec `verification_token`;impl `verification_code` + `verification_code_expires_at` + `last_resend_at`(`users_repo.py:33-44`)— same semantic,cosmetic drift only;W11 retro CO18 Postgres/Cosmos migration 觸發 reconcile

**⚠️ Minor drift × 2(known carry-overs)**:
- **CO_F6a** — `azure-communication-email` NOT in `pyproject.toml`(R8 corp proxy install blocker;同 ADR-0016 argon2-cffi precedent);ConsoleEmailProvider operational fallback active
- **CO_F6c** — sender domain `noreply@dev.ekp-beta.ricoh.com` 係 dev-stub;LIVE switch awaits IT cred event(SPF/DKIM IT-side post Track A)

### 4.8 Hybrid Model Invariant Status

- **SSO path(Entra ID)**:✅ wired LIVE-ready(awaits W16 F1 IT cred event)
- **Self-register path**:✅ wired(Tier 1 in-memory backing;Beta migration trigger = W11 retro CO18)
- **Mock auth bridge**:✅ preserved as fallback

---

## 5. Cross-cutting findings(spanning multiple clusters)

### CC-1:Multi-KB invariant ADR-0005 broken at /query boundary 🚨

**Flagged by**:Agent 2(C08 cross-cutting)+ Agent 1(C03 cross-cutting)

**Spec promise**:
- ADR-0005:`kb_id` 全鏈路 propagate
- architecture.md §3.4:per-KB index naming `ekp-kb-{kb_id}-v{version}` + per-KB blob containers

**Code reality**:
- `QueryRequest.kb_id` field exists(`api/schemas/query.py:36`)✅
- `routes/query.py` 唔 read `payload.kb_id`(grep 0 hits)❌
- `RetrievalEngine.retrieve()` signature `(query, top_k, filter_clause)` 冇 `kb_id` parameter ❌
- `HybridSearcher` filter default `_DEFAULT_FILTER = "enabled eq true and low_value_flag eq false"`(`hybrid.py:33`)— **no `kb_id eq` clause** ❌
- `app.state.retrieval_engine` 係 single shared instance wired to single `azure_search_default_index = "ekp-kb-drive-v1"` — there is no per-KB engine ❌
- `azure_blob_container_screenshots = "ekp-kb-drive-screenshots"` single hardcoded(`screenshots/uploader.py:8` 註明 single-KB Tier 1)❌

**Impact**:
- **Tier 1 single-KB(Drive only)today functionally OK**(only 1 index exists)
- **Latent risk**:加第二個 KB silent misroute 全部 → `ekp-kb-drive-v1` 唔分 `kb_id`

**Remediation P0 — explicit decision needed**:
- **Option A**:Tier 1 single-KB scope 確認 + ADR-0005 amendment(`kb_id` field on QueryRequest reserved for Tier 2 activation)
- **Option B**:wire `kb_id` from QueryRequest through to(b1)per-KB `HybridSearcher` instance map keyed by `kb_id`,or(b2)dynamic `index_name` injection on each retrieve call。**必須 land before 2nd KB activation**

### CC-2:Cohere v3.5 → v4.0-pro propagation gap 🚨

**Flagged by**:Agent 1(C04 cross-cutting)

**Spec lock**:ADR-0012(W6 D5 2026-05-05)+ architecture.md §3.2 v5.1 amendment lock `Cohere-rerank-v4.0-pro`

**Code drift inventory**(7+ hardcoded `v3.5` strings + 8+ test files):
| File:line | Drift |
|---|---|
| `backend/storage/settings.py:59` | `cohere_rerank_model: str = "rerank-v3.5"` default ❌ |
| `backend/api/schemas/query.py:41-46` | request field default `"cohere-v3.5"` |
| `backend/api/routes/query.py:94` | response field literal `"cohere-v3.5"` |
| `backend/api/routes/eval.py:14` | reranker label `"cohere-v3.5"` |
| `backend/generation/stream_composer.py:54` | SSE done frame `"reranker_used": "cohere-v3.5"` |
| `backend/retrieval/reranker/cohere.py:44` | constructor default |
| 8+ test files | `test_observe.py / test_observe_query_route.py / test_stream_composer.py / test_reranker.py / test_realtime_cost.py` assert `"cohere-v3.5"` |
| `backend/observability/realtime_cost.py:91-114` | ✅ correctly has BOTH v3.5 + v4-pro pricing rows(positive — graceful migration)|

**Impact**:
- `.env` 已 lock `Cohere-rerank-v4.0-pro` per W5 D1 — runtime correct
- **但 default 落 code = v3.5**;如果 future deploy 唔 set `.env`,會 silent regress

**Remediation P1 — housekeeping cleanup**:
- Update `Settings.cohere_rerank_model` default → `"Cohere-rerank-v4.0-pro"`
- Replace hardcoded strings with `settings.cohere_rerank_model` runtime
- Update 8+ test files to read settings rather than literal assertion
- Add comment in `cohere.py:44` noting v3.5 default is legacy / pre-ADR-0012
- **No new ADR** — ADR-0012 already covers;this is execution gap

### CC-3:`prev_chunk_id` / `next_chunk_id` populated but unconsumed 🚨

**Flagged by**:Agent 1(C05 Major drift #3)

**Spec promise**:architecture.md §3.1 line 210-211 explicit pipeline step `[Context Expander] ← prev/next 相鄰 chunk`

**Code reality**:
- Orchestrator computes(`ingestion/orchestrator.py:157-158`)✅
- Index stores(`indexing/schema.json:16-17`)✅
- **No retrieval/generation code reads them** ❌
- `C05-generation.md §1` diagram 都唔 include — internal-spec inconsistency

**Cross-ref**:V6 Debug 6 stages vs spec 9 stages reconciliation(missing stages = Query Rewriter / Re-retrieve / **Context Expander**)

**Remediation P0**:
- **Option A**:deliver `generation/context_expander.py`(prev/next lookup + prepend/append top-5 chunk text before prompt build)+ V6 Debug 9-stage scaffold expansion
- **Option B**:amend §3.1 pipeline diagram remove `[Context Expander]` step + repurpose prev/next as citation-render-only metadata + V6 spec edit 9 → 6 stages

### CC-4:Stale component design notes ⚠️

**Flagged by**:Agent 3(Frontend cross-cutting)+ implicit per session-start.md §3 footnote

| Component note | last_updated | Drift | Severity |
|---|---|---|---|
| `C09-admin-ui.md` | 2026-05-04 | mentions `v0-draft → v1-active W4 D1`;`shadcn DataTable / Stepper / Form polish deferred to W7+`;**8-view table not 9-view**(post-W12 amendment lag)| ⚠️ Low impact(architecture.md v6 §5 authoritative per H1)|
| `C10-chat-ui.md` | (similar)| states "Vercel AI SDK `useChat()`" as Critical Design Decision while actual impl uses native generator(intentional per W3 D4 docstring)| ⚠️ |
| `C07-observability.md` | (similar)| status `v0-draft`;actual implementation includes all §7 "Future Evolution" items already(cost dashboard / alerts / real-time attribution)| ⚠️ |
| `C11-identity.md` | **MISSING** | No design note exists for hybrid auth model | ⚠️ |
| `C13-email-verification.md` | **MISSING** | No design note exists | ⚠️ |

**Remediation P1**:
- C09 + C10:bump `last_updated` to W15 close + reflect 9-view + native-generator decisions
- C07:bump status v0-draft → v2-stable + reflect actual delivery
- C11 + C13:create new design notes per `components/Cn-*.md` rolling JIT pattern

### CC-5:`trace_id` placeholder + debug view stub coupling ⚠️

**Flagged by**:Agent 2(C07 minor drift)

`routes/query.py:105, 153` hardcodes `trace_id=""` in QueryResponse;`@observe_async` emits to Langfuse 但 client never receives trace ID;`/debug/trace/{trace_id}` stub 冇 anchor

**Remediation**:closure expected with W16 F5 `/debug/trace/{id}` impl — must include trace_id capture upstream

---

## 6. W16+ Remediation Prioritization

### P0(decision-blocking + spec-vs-code-divergence)

| # | Item | Cross-ref |
|---|---|---|
| P0.1 | **PDF parser delivery decision** — deliver `backend/ingestion/parsers/pdf_parser.py`(Docling-based)OR ADR amendment defer Tier 2 + spec §3.3 PDF row removal | C01 Major drift |
| P0.2 | **Context Expander step decision** — deliver `generation/context_expander.py` + 9-stage V6 OR amend §3.1 + V6 spec 9 → 6 + cross-link prev/next as citation metadata only | CC-3 + V6 ⚠️ + C05 Major drift |
| P0.3 | **Multi-KB invariant decision** — Option A(Tier 1 single-KB stamp + ADR-0005 amendment)OR Option B(wire per-KB before 2nd KB activation)| CC-1 |

### P1(housekeeping cleanup — no new ADR needed,executes existing decisions)

| # | Item | Cross-ref |
|---|---|---|
| P1.1 | **Cohere v3.5 → v4.0-pro propagation cleanup** — settings default + 7+ hardcoded strings + 8+ test files | CC-2 |
| P1.2 | **C09 + C10 design notes refresh** — bump `last_updated` + reflect 9-view + native generator decisions | CC-4 |
| P1.3 | **C07 design note** — status v0-draft → v2-stable + reflect actual delivery | CC-4 |
| P1.4 | **C11 + C13 design notes creation** — new files per rolling JIT pattern | CC-4 |
| P1.5 | **architecture.md §3.7 line 394 amend** — `secrets.token_urlsafe(32)` → 6-digit OTP wording | C13 ⚠️ |
| P1.6 | **architecture.md §4.4 endpoint count** — 18 → 22(+8 new rows for 6 auth + 2 observability) | C08 |
| P1.7 | **architecture.md §4.2 repository structure** — `kb_management` 3-file / `observability` 7 files / `api/auth` + `api/middleware` directories / Bicep multi-file split / `.github/workflows/` | C02 / C07 / C08 / C12 |
| P1.8 | **architecture.md §4.3** — reconcile docker-compose listing(remove fastapi+nextjs services OR document divergence)| C12 ⚠️ |
| P1.9 | **architecture.md §5.2** — "Vercel AI SDK `useChat`" → "Native fetch + TextDecoder generator" | V1 ⚠️ |
| P1.10 | **architecture.md §5.7** — 9 stages → 6 OR cross-link with CC-3 reconciliation | V6 ⚠️ + CC-3 |
| P1.11 | **architecture.md §4.5** — add §4.5.1 post-v5 schema extensions(ApiError + auth + observability)| C08 |

### P2(infrastructure / sustainability — actionable when capacity allows)

| # | Item | Cross-ref |
|---|---|---|
| P2.1 | **V4 Retrieval Testing tab redesign §5.5.4** — 4 controls(Vector/Full-Text/Hybrid + Top K + Score Threshold + Rerank Model)+ Reranker vendor Select | V4 🚨 |
| P2.2 | **Gate 2 decision logic formalization** — `gate2_four_metric_within_5pp(report, baseline)` to `backend/eval/gates.py` for ADR-0012 verdict regression-testable | C06 ⚠️ |
| P2.3 | **C03 lifecycle wrapper decision** — `IndexService` + `azure_search_client.py` deliver OR amend C03 §1 to declare populate.py + create_index.py canonical | C03 ⚠️ |
| P2.4 | **V3 KB List card** — surface `storage_size_mb` + `last_query_rate` once backend telemetry exposes | V3 ⚠️ |
| P2.5 | **V5 Failed Queries 5-col schema** — add Expected + Got columns | V5 ⚠️ |
| P2.6 | **CORS middleware decision** — wire in `server.py` OR document upstream(Front Door / SWA / Next.js rewrite)handles | C08 ⚠️ |
| P2.7 | **REFUSAL_PHRASE multi-language** — multi-phrase detection list per "Match user's language" | C05 ⚠️ |
| P2.8 | **Stub coverage W16 F5 plan enumeration** — explicit which of 9 stubs vs 4 documented | C08 ⚠️ |
| P2.9 | **StatCard rule-of-3 extraction** — V2 + V4 + V5 → shared `components/ui/stat-card.tsx` | Frontend ⚠️ |
| P2.10 | **Embedding length validation** — `Field(..., min_length=1024, max_length=1024)` on ChunkRecord | C03 ⚠️ |
| P2.11 | **`ai`(Vercel AI SDK)package removal** — unused dep cleanup | Frontend ⚠️ |
| P2.12 | **Pipeline tab vs `/admin/kb/new` wizard** — defensible split but spec §5.5.3 amendment OR PipelineTab wizard reuse | V4 ⚠️ |

### W17+ candidates(Beta hardening + Tier 2 evaluation)

- ARIA full audit(NVDA/JAWS/VoiceOver per CO_W15_F3_aria_full_audit)
- Dark mode visual verify post-tokens.ts colorsDark
- Vitest baseline gap(beyond Playwright E2E layer per CO_W15_F4_vitest_baseline_gap)
- Interactive flow E2E(register/login + KB upload + Pipeline wizard per CO_W15_F4_interactive_flow_E2E)
- Multi-tenancy / persistent backing(W11 retro CO18 — KB Manager + users_repo SQLite/Postgres/Cosmos DB)
- httpOnly cookie migration(CO_F5_cookie + CSRF token bundle decision)
- Self-register session refresh(CO_F5_refresh)
- ACS SDK install + SPF/DKIM IT-side(CO_F6a + CO_F6c post Track A)
- KB selector dropdown wire(V1 Chat multi-KB activation)
- Reranker Shootout V5 dynamic load from eval-set artifact

---

## 7. ADR Trigger Recommendations

### ADR-0017 reservation(R8 corp proxy mitigation pattern formalization)

**Trigger threshold(per W15 plan §F4 risks)**:5th cumulative R8 occurrence OR vendor-decision pivot needed

**Current cumulative count**:**4 confirmed**
1. Cohere W3 — Marketplace billing redirect
2. argon2-cffi W13 — ADR-0016 stdlib switch
3. ACS SDK W13 — lazy import design preempts SDK install
4. Playwright browser CDN W15 D5 — ECONNRESET 0% of 179.4 MiB(this audit session)

**Status**:Reservation candidate strengthened;NOT yet triggered。Defer formal write-up until 5th occurrence OR explicit vendor pivot

### Proposed new ADRs(W16+ candidates)

| ADR # | Trigger | Decision content |
|---|---|---|
| **ADR-0018**(if Option A taken)| CC-1 multi-KB invariant decision | Tier 1 single-KB scope confirmed;Q22 / `kb_id` field on QueryRequest reserved for Tier 2 activation;ADR-0005 amendment cross-ref |
| **ADR-0019**(if PDF defer)| C01 PDF parser deferral | Amend ADR-0003 multi-format → defer PDF to Tier 2 |
| **ADR-0020**(if Context Expander defer)| C05 Context Expander deferral | Amend §3.1 pipeline diagram remove step + repurpose prev/next as citation metadata only |
| **ADR-0021**(future,if triggered)| httpOnly cookie + SameSite + CSRF token bundle migration(CO_F5_cookie)| 3 sub-decisions warrant ADR territory |
| **ADR-0022**(future,if triggered)| W11 retro CO18 KB Manager + users_repo persistent backing | Vendor decision(SQLite vs Postgres vs Cosmos DB)|

ADR-0013 reserved status preserved per W11 D5 retro carry-over #1(AF3 lifespan gate split fix);未 promote。

---

## 8. Audit Methodology + Limitations

### Method
- 4 parallel general-purpose agents(NOT Explore agents — Explore documented unsuitable for design-doc auditing per its description)
- Each agent self-contained brief + scoped to 1 cluster
- Output format:structured drift report per cluster(Aligned/Minor/Major + ADR recommendations)
- Parent agent post-processing:5 sanity spot-checks via grep + read against agent claims;all 5 ✅ confirmed
- Total wall clock:~30 minutes(parallel)+ ~15 minutes consolidation

### Spot-check verifications performed
1. ✅ C01 `pdf_parser.py` missing — `backend/ingestion/parsers/` listing confirmed
2. ✅ C04 Cohere v3.5 default — `backend/storage/settings.py:59` confirmed
3. ✅ Multi-KB `kb_id` 唔 propagate — `routes/query.py` grep 0 hits + `retrieval_engine.py:87 def retrieve(` signature 冇 `kb_id` confirmed
4. ✅ V4 Retrieval Testing 缺 4 controls — `RetrievalTab` at line 406;grep `Vector|Full-Text|Hybrid|Top K|Score Threshold|Rerank Model` 0 hits confirmed
5. ✅ C11 scrypt N=2^17 — `backend/api/auth/security.py:22 _SCRYPT_N = 2**17` + ADR-0016 reference comments confirmed

### Limitations
- **Read-only static audit** — no code execution / no runtime UX verification(W16 F4 user smoke first run scope)/ no test execution / no LIVE eval rerun
- **Snapshot at HEAD `fc5cae3`** — doesn't capture future drift between this audit + next re-audit
- **Spec amendment flow** — audit findings 唔自動 trigger spec amendment per CLAUDE.md §4.4 architecture content-lock;必須 stakeholder approve + ADR 或 §13.X amendment
- **Coverage gaps**:scripts/ folder partial coverage(only `validate_eval_set.py` + `run_reranker_shootout.py` examined);infrastructure/ partial(deep Bicep template review out of scope)
- **Cross-cutting items may have additional instances**:CC-2 Cohere propagation likely has more than 7 hardcoded locations(only spot-checked Agent 1 enumeration)

### Re-audit Cadence

| Trigger | Action |
|---|---|
| Post-W16 D10 retro(Beta deploy assessment trigger)| Targeted re-audit on cluster with W16+ remediation actions |
| Architecture amendment(v6 → v7+)| Full re-audit of touched sections |
| Tier 2 phase entry | Full audit + Tier 2 boundary re-verification |
| Major code refactor | Targeted re-audit on touched cluster |

---

## 9. Conclusion

### Summary

EKP Tier 1 codebase 整體 **alignment substantial**:
- 9 / 9 frontend views landed;backend 22 endpoints(+4 vs spec 18);Pydantic schemas 100% field-shape match;0 oklch hardcodes;ADR-0014/0015/0016 newest amendment 忠實 implemented
- Implementation 比 spec timeline 超前(C07 cost dashboard W8 vs W4 + C08 rate limit/audit/uniform errors W7 vs W7+ + C11 hybrid auth W12-W15 vs W7 baseline)
- 0 H4 Tier 2 leak;0 silent drift(所有 deviation tracked in plan changelog / ADR / code comment / known carry-over)

### 5 Major Drifts(Action Required)

1. 🚨 PDF parser missing(C01)— P0 deliver OR defer
2. 🚨 Cohere v3.5 propagation gap(C04)— P1 housekeeping
3. 🚨 Context Expander missing(C05)— P0 deliver OR amend §3.1
4. 🚨 Multi-KB invariant gap(CC-1)— P0 explicit decision
5. 🚨 V4 Retrieval Testing tab structural mismatch §5.5.4 — P2 code remediation

### Stakeholder Surface

呢個 audit 對 **stakeholder review** 提供:
- ✅ Confirmation:項目按計劃推進,0 silent drift
- ⚠️ Action items:5 major drifts 需要 W16+ resolve(3 件 P0 explicit decision + 1 件 P1 housekeeping + 1 件 P2 code)
- 🟢+ Positive signal:implementation 比 spec timeline 超前 1-2 phase(ahead of schedule)

### Living Doc Status

此 audit doc 屬 **complete** for W15 D5 closeout snapshot。下次 re-audit trigger:post-W16 D10 retro(Beta deploy assessment)。新一輪 audit 結果 append 入此 doc 嘅 §11 Re-audit Log section(future)而非 overwrite。`§10 Remediation Campaign Log`(below)tracks the post-closeout ADR + implementation cascade triggered by this audit's 5 major drifts。

---

## 10. Remediation Campaign Log(post-W15 D5 closeout 2026-05-09)

> **Purpose**:本 session(2026-05-09)post-W15 D5 closeout 觸發 audit-driven remediation cascade — **16 commits** 跨 governance + audit + ADR + implementation + governance-closure + P1-housekeeping 多層(初版 10 commits 入 `91a09a1`;Phase 4 P1 housekeeping batch 5 commits append `a14f1fe`),closure 5 major drifts 之 4(1 partial — #3 frontend V6 9-stage Session 2 deferred)。Log 入此 doc 而非 W16 progress.md 因為:(1)remediation 性質係 audit verdict closure,trace 直接綁 §6 5 major drifts;(2)W16 D1 active flip 仍未發生(等 Track A IT cred populate event),呢 16 commits 屬 W15 closeout cascade extension 而非 W16 implementation。
>
> **Governance posture**:per CLAUDE.md §10 R1/R2 紀律 spirit,本 log 補 governance gap — 過去 W2 D5 cont ADR-0001-0011 batch creation governance prep 為先例;本 cascade 依循同樣 pattern。
>
> **Append history**:
> - `91a09a1` 2026-05-09 — initial §10 NEW(commits 1-10 ledger + 5 drifts pre-Phase-4-P1 status)
> - `(this commit)` 2026-05-09 — Phase 4 P1 housekeeping batch closure append(commits 11-16 + Drift #2 closure status + verdict strengthening)

### Commits ledger(時序)

| # | Commit | Layer | Subject | Drift closure |
|---|---|---|---|---|
| 1 | `d099bcb` | Governance | session-start.md §9-§12 catch-up(OQ 16/21→17/22 + W7-W16+ extend + carry-overs W6→W15 + milestones +9 rows)| — |
| 2 | `fc5cae3` | Governance | session-start.md §3 component status 12→13(C13 NEW + post-W15 status update)| — |
| 3 | `63cd0f1` | Audit | `audit-W15-d5-vs-spec.md` NEW 782 lines(4 parallel agents + 5 spot-checks;verdict ⚠️ MINOR DRIFT,5 major + 0 silent)| — |
| 4 | `5536a7d` | ADR | ADR-0018 Multi-KB kb_id dynamic injection(Option B b2 reaffirm ADR-0005)| Drift **#4**(decision)|
| 5 | `371b0bb` | ADR | ADR-0019 PDF parser Tier 1 deliver(Option A reaffirm ADR-0003;text-extractable scope)| Drift **#1**(decision)|
| 6 | `ac826a3` | ADR | ADR-0020 Context Expander deliver(Option A reaffirm §3.1 + §5.7)| Drift **#3**(decision)|
| 7 | `c6acb3d` | Implementation | ADR-0019 Phase 3 Session 1:`backend/ingestion/parsers/pdf_parser.py` NEW + `__init__.py` route fix(13 passed/7 skipped)| Drift **#1**(80% — Session 2 sample PDF blocked Chris)|
| 8 | `08fc25e` | Implementation | ADR-0018 Phase 3 Session 1:`kb_naming.py` NEW + `Settings.kb_id_default` + `HybridSearcher.search(kb_id)` + `RetrievalEngine.retrieve(kb_id)` + `routes/query.py` + `eval/runner.py` + `crag.refine(kb_id)`(47 tests passed)| Drift **#4**(retrieval-side closure)|
| 9 | `3387a4f` | Implementation | ADR-0018 Phase 3 Session 2:`uploader.py` per-record dynamic container + `extractor.py` docstring + `test_multi_kb_routing.py` 4 integration tests(77 full regression)| Drift **#4**(ingestion-side **CLOSURE**)|
| 10 | `cffb391` | Implementation | ADR-0020 Phase 3 Session 1:`context_expander.py` NEW + `HybridSearcher.fetch_by_chunk_ids()` + `RetrievalEngine.expand_context_for_chunks()` + `prompt_builder` expanded_text fallback + `routes/query.py` 兩處 wire + `crag.py` re-retrieve wire + 11 new unit tests(68 passed,0 regressions)| Drift **#3**(backend closure;frontend V6 9-stage Session 2 deferred)|
| 11 | `91a09a1` | Governance closure | `audit-W15-d5-vs-spec.md` §10 Remediation Campaign Log NEW + W15 retro cross-ref pointer(post-closeout governance gap closure;CLAUDE.md §10 R2 spirit)| — |
| 12 | `aedf1d0` | **P1 Step 1+3** | Backend code + tests fidelity + ADR-0018 cascade leftover fix:`storage/settings.py` + `api/schemas/query.py` Literal expand + `routes/query.py` + `routes/eval.py` + `stream_composer.py` + `reranker/cohere.py` + `reranker/__init__.py` + 3 test files(2 assertions update + 4 mock kb_id signatures)— **543 passed + 7 skipped 0 regressions** | Drift **#2**(backend layer)|
| 13 | `34c848a` | **P1 Step 2** | Frontend Literal expand + `.env.example` refresh:`frontend/lib/api/query.ts` v4.0-pro Literal add(B1 keep-both)+ `.env.example` `COHERE_RERANK_MODEL` default(tsc EXIT_CODE=0 strict clean)| Drift **#2**(frontend + infra layer)|
| 14 | `dff24f0` | **P1 Step 4** | Observability label refresh + dual-rate preserved:`realtime_cost.py` source comment refresh + `cost_estimator.py` ServiceCostRow label;**dual-rate v3.5 + v4-pro `_PRICING_TABLE` rows preserved unchanged**(intentional ADR-0012 +5% bump verification)| Drift **#2**(observability layer)|
| 15 | `af0d6c2` | **P1 Step 5** | Architecture spec H1 catch-up — retroactive v5.1 file content sync(stakeholder approved W6 D5 cycle for ADR-0012;file content drift since 2026-05-05 freeze closed):§3.1 line 200 + §4.5 lines 648-649 + §9 line 1158 + §13.10 line 1391 + §14 line 1474(ASCII alignment preserved length=57)| Drift **#2**(architecture spec layer)|
| 16 | `a14f1fe` | **P1 Step 6** | Standing instructions + onboarding docs + design notes:CLAUDE.md §5.2 H2 vendor table + README.md + `docs/setup.md` ×2 + `docs/eval-methodology.md` ×3 + `C04-retrieval.md` ×2 + `scripts/run_cohere_lift_smoke.py` docstring;`decision-form.md` Q5 + Q21 historical narrative preserved | Drift **#2**(docs + standing instructions layer **CLOSURE**)|
| 17 | `742f6f8` | Audit log fidelity append | §10 ledger 11-16 + Drift #2 fully-closed status + verdict strengthening + Karpathy §1 baseline + handoff section update | — |
| 18 | `61eba52` | **W16 F5 governance** | W16 plan/checklist/progress F5 partial-active flip + CO_W14_process_grep_verify FORMALIZED 5-step findings + scope decisions A.1+B.1+C.1+D.2+E.1 + checklist 7→22 atomic sub-items expansion | — |
| 19 | `507cbff` | **W16 F5.1** | KB documents/chunks listing CO_F3a closure(10 tests passed):`api/schemas/listing.py` NEW + `HybridSearcher.list_documents/list_chunks` + `RetrievalEngine` delegates + routes refactored Depends pattern + 503/404/502 envelopes | — |
| 20 | `cb30e8e` | **W16 F5.2** | KB name+description PATCH CO_F3b closure(6 tests passed;Decision A.1 NEW endpoint):`KbMetadataPatch` schema + `KBStorageBackend.update_metadata` Protocol + InMemory impl + `PATCH /kb/{kb_id}` separate from `/settings` | — |
| 21 | `5a357e7` | **W16 F5.3** | KB-level reindex(NEW)+ DELETE Decision B.1 annotate CO_F3c closure(4 tests passed):`POST /kb/{kb_id}/reindex` 202 + mock task_id;DELETE Azure cleanup defer Track A IT cred per W17+ candidate | Drift #3 partial closure(F5.5 frontend Session 2 unblocker via /debug/trace endpoint cascading)|
| 22 | `4046b24` | **W16 F5.4** | eval/run + eval/shootout CO_W15_F1 closure(9 tests passed;Decision C.1 both full):NEW `eval/orchestrator.py` + `RerankerShootoutEntry` + `ShootoutReport` schemas;Tier 1 baseline Recall@5 + RAGAs 4-metric W17+ deferral note in failed_queries per W16 plan §3 PARTIAL PASS | — |
| 23 | `1dbcdf3` | **W16 F5.5** | debug/trace Langfuse SDK CO_W15_F2 closure(6 tests passed;Decision D.2 full SDK):NEW `observability/langfuse_trace.py` + `TraceStage` + `TraceDetail` schemas + 5-status-enum graceful degrade + `NEXT_PUBLIC_LANGFUSE_URL` env var(F5.x.2)+ skeleton test fixups(2 stub-asserting tests cascaded) | **Drift #3 frontend Session 2 UNBLOCKED** — ADR-0020 V6 6→9 stage can wire to `/debug/trace/{trace_id}` |
| 24 | `cb15c3d` | Implementation | **ADR-0020 Phase 3 Session 2** — V6 Debug View 6→9 stage + Context Expander Langfuse trace wiring(5 new tests;583 passed + 7 skipped 0 regressions;tsc EXIT_CODE=0 + eslint clean changed files + browser smoke):`observe.py` `emit_stage_metadata()` + `context_expander.py` emits `generation.context_expansion` stage(duration_ms + requested/expanded/boundary_skip counts;happy path + empty-top-K early return)+ `langfuse_trace.py` `_extract_stage` reads `observation.metadata`→`TraceStage.details`(+ duration_ms latency fallback)+ `TraceStage.details: dict\|None` schema + `lib/api/debug.ts` contract sync(`TraceData`→`TraceDetail`,`PipelineStageMetric`→`TraceStage`,drop backend-absent fields,flat list)+ `page.tsx` 9 conceptual stages(adds Query Rewriter / Re-retrieve / Context Expander)+ observation-name→stage prefix bucketing + status-field branching(replaces 501-stub-mitigation)+ `details` key/value render + `trace_url` CTA fallback `NEXT_PUBLIC_LANGFUSE_URL` | Drift **#3** — **FULLY CLOSED**(backend module Session 1 + Langfuse trace wiring + V6 9-stage frontend;pixel baseline re-capture = W16 F4 scope per ADR-0020 §C)|
| 25 | `1ea08b0` | ADR | **ADR-0021** — V4 Retrieval Testing tab §5.5.4 deliver + `HybridSearcher` search-mode param(Option A deliver code,reaffirm not amend;`mode` param touches C04 §3 RAG Core interface → H1 ADR per strict reading;user-approved 2026-05-10)+ README index updated(next NNNN now 0022) | Drift **#5**(decision)|
| 26 | `9582fa4` | Implementation | **ADR-0021 implementation** — `HybridSearcher.search()` + `RetrievalEngine.retrieve()` gain `mode`("hybrid" default unchanged / "vector" / "fulltext")+ `rerank: bool`;NEW `POST /kb/{kb_id}/retrieval-test`(pure retrieval — no CRAG / no synthesis;404 / 503 / 502;score_threshold filter vector/hybrid only)+ NEW `api/schemas/retrieval_test.py`;V4 `RetrievalTab` rewritten into "Retrieval test" panel(mode Select + Top K Slider + Score Threshold Slider + Rerank Switch → ranked chunks + scores)+ "End-to-end query" panel(CRAG Switch + LLM Select → synthesis,reuses `/query/stream`);Reranker dropdown lists only Cohere v4.0-pro + "None"(Voyage/ZeroEntropy dropped per ADR-0012;§5.5.4 not amended,historical narrative preserved)+ 10 new tests(2 hybrid mode payload-shape + 8 retrieval-test endpoint)— **593 passed + 7 skipped 0 regressions** + tsc EXIT_CODE=0 + eslint clean changed files | Drift **#5** — **FULLY CLOSED**(all spec §5.5.4 controls delivered;Vector/Full-Text/Hybrid modes real via `HybridSearcher` `mode` param;RetrievalTab interactive browser smoke limited — local dev server's Azure backend has no seeded KB so the KB-detail page can't render the tab there;coverage = tsc/eslint + endpoint route/schema/error-path tests)|

### 5 major drifts closure status(post-cascade)

| Drift | Severity | Pre-cascade state | Post-cascade state | Open work |
|---|---|---|---|---|
| **#1 C01 PDF parser missing** | 🚨 P0 | spec ADR-0003 multi-format reference;parser absent | ✅ ADR-0019 Option A landed + parser code landed + 13 unit tests passed | 🚧 ADR-0019 Session 2 sample PDF blocked Chris(W16 D1 dependency;7 skipped tests)|
| **#2 C04 Cohere v3.5 propagation gap** | 🚨 P1 | 7+ hardcoded `v3.5` references in spec / settings / docs;production = v4.0-pro per Q21 + ADR-0012 | ✅ **FULLY CLOSED** Phase 4 P1 housekeeping batch(5 commits `aedf1d0` + `34c848a` + `dff24f0` + `af0d6c2` + `a14f1fe`)— backend code + frontend Literal + observability label + architecture v5.1 retroactive catch-up + standing instructions + onboarding docs;dual-rate pricing preserved + historical narratives preserved per Karpathy §1.3 surgical | — |
| **#3 C05 Context Expander missing** | 🚨 P0 | spec §3.1 mentions step;`prev_chunk_id` + `next_chunk_id` populated but never consumed | ✅ **FULLY CLOSED** — ADR-0020 Option A:backend module Session 1(`cffb391`,11 unit tests)+ Langfuse trace wiring + V6 9-stage frontend Session 2(`cb15c3d`,5 new tests):`generation.context_expansion` stage emitted + `TraceStage.details` carries `expanded_count`/`boundary_skip_count`/`requested_count` + `page.tsx` 6→9 conceptual stages with observation-name→stage bucketing | 🚧 Playwright pixel diff baseline re-capture for the 9-stage layout = W16 F4 user smoke first run scope per ADR-0020 §C(R8 corp-proxy blocked;not a Drift #3 gap)|
| **#4 CC-1 Multi-KB invariant gap** | 🚨 P0 | `kb_id` field on `QueryRequest` schema only;not propagated through retrieval / ingestion | ✅ ADR-0018 Option B b2 landed + retrieval-side + ingestion-side **CLOSURE**(2 sessions)| — |
| **#5 V4 Retrieval Testing tab structural mismatch** | 🚨 P2 | spec §5.5.4 lists 4 controls + score panel + Vector/Full-Text/Hybrid radios;tab missing all | ✅ **FULLY CLOSED** — ADR-0021(`1ea08b0`)+ implementation(`9582fa4`):`HybridSearcher.search()` + `RetrievalEngine.retrieve()` `mode` param("hybrid" default unchanged / "vector" / "fulltext")+ `POST /kb/{kb_id}/retrieval-test` pure-retrieval endpoint + V4 `RetrievalTab` rewrite("Retrieval test" panel:mode Select + Top K Slider + Score Threshold Slider + Rerank Switch → ranked chunks + scores;"End-to-end query" panel:CRAG Switch + LLM Select → synthesis)+ 10 new tests | 🚧 RetrievalTab interactive browser smoke deferred(local dev server's Azure backend has no seeded KB);Reranker dropdown lists only Cohere v4.0-pro + "None"(Voyage/ZeroEntropy dropped per ADR-0012 — §5.5.4 not amended,historical narrative preserved)|

**Closure verdict**:**5 / 5 major drifts fully closed**(or near-fully — #1 only the sample-PDF Session 2 gap, blocked Chris;#2 + #3 + #4 + #5 FULLY CLOSED)。Audit verdict ⚠️ MINOR DRIFT post-cascade strengthened to **MINOR DRIFT (substantially remediated;5/5 major drifts closed, #1 sample-PDF un-skip pending Chris)**。

### Reservation candidates updated

- **ADR-0017** reservation candidate(R8 corp proxy mitigation pattern)— **status unchanged**:4 cumulative occurrences(Cohere W3 + argon2-cffi W13 + ACS lazy import W13 + Playwright CDN W15);本 cascade(含 ADR-0020 Session 2 + ADR-0021)並無 install 新 dependency / 觸發第 5 次 / vendor pivot,reservation 保持(仍 4)
- **ADR-0021** httpOnly cookie + SameSite + CSRF token bundle — **status unchanged**(W17+ candidate per §7 proposed new ADRs;CO_F5_cookie 觸發點未到)
- **ADR-0022** KB Manager + users_repo persistent backing — **status unchanged**(W17+ Beta hardening per CO18)
- **next available NNNN**:0022(0013 + 0017 reserved;0014-0016 + 0018-0021 landed;0022 cookie migration / 0023 KB persistent backing future candidates per §7,renumbered)

### Karpathy §1 baseline check(本 cascade)

- **§1.1 think-before-coding** ✅ — 每個 ADR 都先 surface 多個 Option(A/B);實作前讀 spec section + grep code base 對齊 acceptance criteria(per CO_W14_process_grep_verify);Phase 4 P1 batch 預先 grep 全部 48 files 嘅 v3.5 occurrences + categorize Group A-J + H1 boundary explicit surface 然後 user approve 先 edit
- **§1.2 simplicity-first** ✅ — ADR-0018 Option B b2 dynamic injection(NOT per-KB instance map);ADR-0019 Tier 1 narrow scope(text-extractable only,OCR + decryption defer Tier 2);ADR-0020 single batch fetch via `search.in()`(NOT 2K calls);duck-type ExpandedChunk(NOT new abstraction layer);Phase 4 P1 B1 keep-both Literal(backwards-compat preserved over premature drop)+ D1 keep historical CLAUDE.md §4.2 example commit message + dual-rate `_PRICING_TABLE` rows preserved unchanged + decision-form.md historical narratives preserved
- **§1.3 surgical** ✅ — `HybridSearcher.__init__` signature 唔變;EvalRunner kb_id default preserved;prompt_builder fallback `expanded_text or chunk_text`;backwards-compat preserved across all 4 implementation commits;Phase 4 P1 14 surgical edits across 6 files Step 6 + ASCII alignment preserved §14 vendor table line 1474 length=57 + pre-existing E402 errors NOT touched(scripts/ truststore inject pattern out-of-scope);ADR-0020 Session 2 `emit_stage_metadata` at source(DRY,not duplicated in 2 callers)+ `@observe_async` decorator rejected(tuple result;`capture_attrs` reads off the result object)+ frontend contract sync **drops** backend-absent fields(`query`/`kb_id`/`total_cost_usd`)rather than keeping the stale W15 D2 forward-looking shape + pre-existing `admin/page.tsx` unused-import lint error NOT touched(out of scope;noted for W17+ housekeeping)
- **§1.4 goal-driven** ✅ — verifiable success criteria per ADR(unit tests + integration tests);0 regressions across 87 cumulative test runs;ruff All checks passed;Phase 4 P1 final verify pytest 543 passed + 7 skipped(155s)+ tsc EXIT_CODE=0 frontend strict clean per commit gate;ADR-0020 Session 2 verify 583 passed + 7 skipped + ADR-0021 verify 593 passed + 7 skipped(0 regressions each)+ ruff clean + tsc EXIT_CODE=0 + eslint clean on changed files + browser smoke(dev server,user-authorized):ADR-0020 `/debug/{id}` renders the 9-stage scaffold + vendor tags + collapsible toggle(`aria-expanded`)+ error-banner branch + Open-in-Langfuse fallback URL;ADR-0021 RetrievalTab interactive smoke limited(local dev server's Azure backend has no seeded KB so the KB-detail page can't render the tab — `/admin/kb` list renders fine,page.tsx module loads) — interactive visual/pixel verification deferred W16 F4(R8 corp-proxy blocked Playwright browser install)per ADR-0020 §C / ADR-0021

### Handoff to next governance step

- ~~**Phase 4 P1 housekeeping candidate**(this session OR W16 D5)~~ — ✅ **DONE**(5 commits `aedf1d0` + `34c848a` + `dff24f0` + `af0d6c2` + `a14f1fe`;Drift #2 FULLY CLOSED)
- ~~**ADR-0020 Session 2 frontend V6 6→9 stage expansion**~~ — ✅ **DONE 2026-05-10**(`cb15c3d`;Drift #3 FULLY CLOSED;ledger #24)
- ~~**Drift #5 V4 Retrieval Testing tab §5.5.4 P2 code remediation**~~ — ✅ **DONE 2026-05-10**(ADR-0021 `1ea08b0` + impl `9582fa4`;Drift #5 FULLY CLOSED;ledger #25-26)— **all 5 audit major drifts now closed**
- **W17+ candidate**(remaining):pre-existing `admin/page.tsx` unused-import lint error(`CardTitle`;trivial,W17+ housekeeping)+ ADR-0021 RetrievalTab interactive browser smoke once a KB is seeded in a reachable dev backend
- **Chris-blocked**(remaining):ADR-0019 Session 2 sample PDF activation(7 skipped tests un-skip when sample PDF lands)
- **Re-audit cadence trigger preserved**:post-W16 D10 retro per §8.4 — 屆時 re-audit cluster 應反映本 cascade 之 closure(避免 stale drift report);**Drift #2 + #3 + #4 + #5 已 closed** 應 confirm post-W16 re-audit;**Drift #1** 應 verify sample-PDF Session 2 progress

---

**End of audit doc — W15 D5 closeout vs spec v6**(post-cascade remediation log initial 2026-05-09 + Phase 4 P1 closure append 2026-05-09 + ADR-0020 Session 2 closure append 2026-05-10 + ADR-0021 / Drift #5 closure append 2026-05-10)
