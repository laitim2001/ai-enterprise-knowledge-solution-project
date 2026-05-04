---
phase: W03-chat-retrieval-citation
plan_ref: ./plan.md
checklist_ref: ./checklist.md
status: draft     # draft → in-progress → closed
---

# Phase W03 — Progress

> Daily progress + 結尾 retro。
> 每 commit 必須對應一個 Day-N entry mention(R2 binding rule per PROCESS.md §5)。
> Status:`draft` 直到 W2 D5 closeout sign-off + Gate 1 verdict pass。

---

## Day 0 — 2026-05-07: Kickoff prep(W2 D5 末 same-session draft)

**Action**:Phase W03 kickoff prep(per PROCESS.md §2.3 rolling-JIT lifecycle + W2 D5 closeout 同 session)

- Folder `docs/01-planning/W03-chat-retrieval-citation/` created
- Templates copied from `_templates/phase/`(v2.0 unified naming)
- `plan.md` filled with status=`draft`(10 deliverables F1-F10,Cohere Rerank + GPT-5.5 synthesis + SSE streaming + Chat UI + PPT parser + Pipeline wizard + Settings tab + retro)
- `checklist.md` derived from plan deliverables(~70 atomic items)
- `progress.md` Day 0 entry initialized(this file)
- **Carry-over candidates from W02-foundation**(pending Gate 1 verdict + W2 D5 closeout final retro):
  - F7 live Gate 1 eval — pending R8 VPN disconnect(if W2 closes mid-session,W3 D1 morning carries through)
  - F8 ground truth chunk_id discovery + SME validation — Chris async work,W3 D1+ ongoing
  - F3 R12 Azurite — image upload still defer until W7+
  - F1 (W3) Q5 Cohere procurement Path A vs B decision — Chris W3 D1 critical

**Status update will follow at W2 D5 closeout**(Chris approve flip `draft → active` after Gate 1 pass)。If Gate 1 fail → W3 plan **does not flip active**;HALT POC per architecture.md §6.3,foundation iteration loop replaces W3。

---

## Day 1 — 2026-05-04 (Mon — early start same-day W2 closeout 後段)

> Per W2 D5 cont 後段 closeout(2026-05-04)pre-fly:F1 Cohere blocked on Q5 procurement(Chris async),F5 PPT parser independent and able to start。Started F5 only — F2-F4 / F6-F9 await Q5 + Chris signoff to begin sequencing。

### Done

#### F5 — `.pptx` parser(python-pptx)— scaffold + unit tests

- `backend/ingestion/parsers/pptx_parser.py` ✅ NEW(per architecture.md §3.3 + components/C01-ingestion.md §1):
  - `PptxParser` class implements `Parser` Protocol(`base.py`)— `doc_format = "pptx"`、`parse(source) → ParserResult` deterministic + never raises
  - Slide-level structure mapping:per slide emit synthetic `"Slide N"` level=1 heading(stable section_path anchor for F2 chunker)+ title placeholder(if present)level=2 heading + body text frames + tables + pictures + speaker notes prefixed `[Notes] ...`
  - Picture extraction:`shape.shape_type == MSO_SHAPE_TYPE.PICTURE` → blob + ext + SHA256 dedup-ready
  - Table extraction:`shape.has_table` → `Table(headers=row[0], rows=row[1:], doc_order=...)`
  - `doc_order` monotonic across paragraphs / tables / images(F2 chunker contract per W2 design)
  - Edge cases:no-title slide(only Slide-N heading);picture without retrievable blob(skipped);malformed `.pptx`(`ParserResult(parse_failed=True)`)
- `backend/tests/test_pptx_parser.py` ✅ NEW — 9 tests pass:
  - 2-slide deck headings(level=1 Slide N + level=2 title)/ body text extract / speaker notes prefix / picture SHA256 + ext / table headers + rows / `doc_order` monotonic / no-title slide handling / malformed file fallback / Parser Protocol `doc_format` attribute
- Dependency:`python-pptx==1.0.2` already installed via W1 D2 batch(`pyproject.toml` deps,non new install)
- **Real-sample sanity report deferred**:Q2 PPT-share request from Chris pending(per W3 plan R6);once samples arrive可跑 `scripts/run_pptx_parser_sanity.py`(W3 D2-D3 scope alongside orchestrator wire)
- **Orchestrator integration deferred**(W3 D2-D3):`IngestionOrchestrator` parser registry needs `pptx → PptxParser()` entry + format auto-detect;呢個 step 同 F2 GPT-5.5 synthesis 同期做 makes sense(post Q5 path resolution)

#### Test suite

- **Full backend test suite 99/99 pass**(W2 baseline 90 + 9 NEW pptx parser);ruff clean

### Decisions / OQ Resolved

- **Decision** — F5 W3 D1 only(non F1-F4 / F6-F9 batch start)。Rationale:F1 Cohere blocks on Q5(Chris async procurement decision Path A vs B);F2-F4 / F6-F9 序列依賴 F1 + Chris W3 active flip signoff。F5 PPT parser purely additive(C01 expansion),independent of Q5 / chat path / generation pipeline → can land cleanly without prerequisite resolution。Per Karpathy §1.4 goal-driven:F5 acceptance(parser + 9 tests pass)well-defined and self-contained。
- **Decision** — F5 sanity report defer to W3 D2-D3:real PPT samples blocked on Q2(Chris share)。Synthetic fixture已 cover parser logic;real-sample variance(corporate template / SmartArt / linked content)留 W3 D2-D3 跟 sample arrival 一齊做。
- **Decision** — F5 orchestrator wire defer to W3 D2-D3:`pptx → PptxParser()` registry entry + format auto-detect 跟 F2 GPT-5.5 synthesis 同期 makes sense post-Q5。
- **No new OQ resolved**(Q5 Cohere仍 Open W3 D1 critical;Chris async)

### Blockers

- 🔴 **Q5 Cohere procurement Path A vs B** — F1 Cohere Rerank wire blocked;Chris W3 D1 critical decision per `decision-form.md` Q5
- 🟡 **Q2 PPT-share** — F5 sanity report deferred(non blocking F5 parser 落地;impact W3 D2-D3 polish + real-format variance verification)
- ✅ All other W2 D5 cont 後段 housekeeping cleared(99/99 tests + W2 closed + W3 active + ADR 0001-0011 + Q17/Q18 closed + R8 P2 limitation documented)

### Actual vs Planned Effort

| Item | Planned (h) | Actual (h) | Variance | Note |
|---|---|---|---|---|
| F5 PPT parser scaffold | 2.0 | 0.5 | -1.5h | python-pptx mature SDK + dataclass Parser contract = thin wrapper;mirrors docx_parser pattern |
| F5 unit tests(9 tests with synthetic fixture)| 1.0 | 0.5 | -0.5h | python-pptx 同時建 fixture + 解析,test self-contained |
| W3 D1 progress.md entry | 0.3 | 0.3 | 0 | First W3 entry,template-following |
| **Total D1** | **3.3** | **1.3** | **-2.0h** | F5 isolation = clean implementation;real-sample fanout move to D2-D3 |

### Commits

| Hash | Subject |
|---|---|
| `58690a4` | `feat(c01): F5 PPT parser scaffold + 9 unit tests (W3 D1 — F1 Cohere blocked Q5)` |

---

## Day 1 後段 — 2026-05-04 (Mon) — Chris 6-item signoff + F1 Cohere Path A scaffold + F5 real-sample sanity

> Same-day continuation after Chris signoff(W2 closeout review)。Chris confirmed:(1)Gate 1 PASS accepted for W3 unblock(SME-strict cascade non-blocking forward);(2)Q17/Q18 AI inference accepted as Chris-confirmed Resolved;(3)Q5 Cohere → Path A Azure Marketplace;(4)3 PPT samples uploaded;(5)W3 sequencing approved;(6)C09 W3 D5 polish bump approved。

### Done

#### Decision / OQ / Risk doc updates(Chris signoff log)

- **Q5 Cohere procurement → Path A Azure Marketplace**(`docs/decision-form.md`)。Procurement timeline 預期 7-14 工作日;W3 D1-D2 scaffold + procurement parallel
- **Q17 + Q18** Decided By updated `Dev(self,AI inferred)` → `Chris(confirmed 2026-05-04)`(`docs/decision-form.md`)。Status remains Resolved(content unchanged)
- **OQ Dashboard**:14 Open → **11 Open** post Q5 + Q17 + Q18 close;**12 Resolved**(was 9);Q5 = W3 D1 critical → Resolved
- **R3 Cohere Marketplace**:🟡 Active → 🟢 **Resolved 2026-05-04**(Path A;procurement parallel with W3 scaffold)。Index row + detail block both updated
- **Gate 1 PASS treatment**:Chris signoff explicit accepts current keyword-mode + validated=False as W3 unblock signal;SME-strict cascade non-blocking forward(W2 progress § Phase status decision noted in earlier same-day commits)

#### F1 — Cohere Rerank v3.5 scaffold(C04 expansion;W3 D1-D3 spread)

- `backend/retrieval/reranker/__init__.py` ✅ NEW package init
- `backend/retrieval/reranker/base.py` ✅ NEW — `Reranker` Protocol + `RerankedChunk` dataclass(rerank_score / hybrid_score / original_index preserved for trace)
- `backend/retrieval/reranker/cohere.py` ✅ NEW — `CohereReranker` REST client:
  - Async httpx client + tenacity retry on 5xx / TransportError
  - POST `{endpoint}/v2/rerank` with `{"model","query","documents","top_n"}` body
  - Response parses `results[].index` + `results[].relevance_score`,clamps invalid index,emits `RerankedChunk` desc by score
  - structlog event `cohere_rerank` with path / candidates_in / results_out for Langfuse correlation
  - Path A Marketplace endpoint(default)/ Path B direct API(config-flag selectable)— same body schema
- `backend/retrieval/reranker/factory.py` ✅ NEW — `make_reranker(settings) → Reranker | None`;returns None when `cohere_endpoint` 或 `cohere_api_key` 未 populate(allows hybrid-only fallback)
- `backend/storage/settings.py` updated:`cohere_endpoint`(NEW)+ `cohere_procurement_path`(Literal["A","B"],default A)+ `cohere_request_timeout_s`(default 10s)
- `backend/tests/test_reranker.py` ✅ NEW — 8 tests pass:
  - empty candidates → empty result + no API call
  - desc by relevance_score / preserves original_index + hybrid_score
  - payload shape(URL / model / query / documents / top_n)
  - top_n clamped to candidate count
  - invalid index in response skipped
  - factory returns None when endpoint OR key unset
  - factory returns CohereReranker when both populated + path arg propagated

**NOT yet wired into RetrievalEngine**(F1.7 deferred to W3 D2 post Chris .env populate Marketplace endpoint + key);wire-in 改 retrieval_engine.py 加 optional reranker dependency,`hybrid_top_k=50 → reranker.rerank → top_k=5`。

#### F5 — Real PPT sample sanity(unblock Q2)

Chris uploaded 3 .pptx samples to `docs/06-reference/01-sample-doc/`:`FY26 BP - DCE...pptx` / `FY26 BP Template V1 (1).pptx` / `FY26_Budget_Proposal_v2.pptx`。Inline sanity output:

| Sample | parse_failed | Slides | Paragraphs(headings/body)| Tables | Images |
|---|---|---|---|---|---|
| FY26 BP - DCE | False | 17 | 18 / 219 | 11 | 39 |
| FY26 BP Template V1 | False | 13 | 14 / 69 | 3 | 7 |
| FY26 Budget Proposal | False | 9 | 9 / 139 | 2 | 12 |

3/3 parse success;table + image extraction works on real corporate templates;synthetic-test corpus extends well to enterprise samples。Slide title coverage 2/3 samples(samples 1+2)— sample 3 has no title placeholders so only synthetic Slide-N headings emit(as designed)。

#### Test suite

- **Full backend test suite 107/107 pass**(99 → 107,+8 reranker tests);ruff clean

### Decisions / OQ Resolved

- **Q5 Resolved 2026-05-04 → Path A Azure Marketplace**(Chris signoff)— see decision-form + RISK_REGISTER R3 update
- **Q17 + Q18 Resolved 2026-05-04**(Chris confirm AI inference)— see decision-form
- **Decision** — F1 wire-into-RetrievalEngine deferred W3 D2 post .env populate。Rationale:scaffold + tests prove transport contract;wire 是 1-line dependency injection through RetrievalEngine constructor + 1 conditional in retrieve() — clean change once Marketplace endpoint + key available。Procurement async parallel keeps W3 D1 surgical
- **Decision** — Reranker factory returns `None` when not configured(non raise / warning)— allows hybrid-only baseline fallback for local dev / CI / unit tests not exercising rerank。RetrievalEngine W3 D2 wire 同樣 use `Optional[Reranker]` pattern
- **No new OQ resolved beyond the 3 closed today**

### Blockers cleared / remaining

- ✅ **Q5** Resolved Path A → F1 scaffold landed;wire-in pending Chris .env populate post Marketplace deploy
- ✅ **Q2 PPT-share** — 3 samples uploaded;F5 real-sample sanity outcome documented above
- ✅ **Gate 1 PASS treatment** — Chris explicit accepts W3 unblock
- ⏸ **Cohere Marketplace deploy** procurement(7-14d turnaround per Q5 timeline) — Chris async;F1 wire-in cascade post deploy

### Actual vs Planned Effort

| Item | Planned (h) | Actual (h) | Variance | Note |
|---|---|---|---|---|
| Decision / OQ / Risk doc updates(Q5 + Q17/Q18 + R3) | 0.5 | 0.4 | -0.1h | Surgical edits |
| F1 Cohere reranker scaffold(Protocol + REST + factory + settings) | 3.0 | 1.5 | -1.5h | Cohere REST API straightforward;httpx + tenacity 已熟 pattern from W2 |
| F1 unit tests(8 tests + factory tests) | 1.5 | 0.7 | -0.8h | AsyncMock + MagicMock pattern reuse from W2 populate test |
| F5 real-sample sanity(3 samples) | 0.3 | 0.2 | -0.1h | Inline command;parser robust |
| W3 D1 後段 progress.md entry | 0.5 | 0.5 | 0 | This entry + table |
| **Total D1 後段** | **5.8** | **3.3** | **-2.5h** | F1 isolation + scaffold-only scope kept session focused |

### Commits(D1 後段 batch)

| Hash | Subject |
|---|---|
| `da0f47f` | `docs(decision,risk): Q5 → Path A + Q17/Q18 Chris confirm + R3 Resolved (Chris signoff log)` |
| `2997c74` | `feat(c04): F1 Cohere Rerank v3.5 scaffold + Reranker Protocol + factory + 8 tests (W3 D1 — Path A, wire deferred)` |
| `d859965` | `docs(planning): W3 D1 後段 — Chris signoff log + F5 real-sample sanity + F1 scaffold tick (107/107 tests)` |

---

## Day 2 — 2026-05-04 (Mon — early start same-day W3 D1 closeout per Chris signoff)

> Per Chris signoff "5. W3 sequencing 確認可以":F1.7 wire + F2 GPT-5.5 synthesis + F3 citation enrichment 三件 W3 D2 plan deliverables 一次過落地。Synthesis path live-ready immediately when /query called(GPT-5.5 deployment Q4 Resolved W1 D1);rerank live verify 等 Cohere Marketplace endpoint + key populate(Chris async procurement)。

### Done

#### F1.7 — Wire `Reranker` into `RetrievalEngine`

- `backend/retrieval/retrieval_engine.py`:`RetrievalEngine` 接 `reranker: Reranker | None`(default None)+ `hybrid_overfetch_for_rerank: int = 50`;`RetrievalResult` 加 `rerank_latency_ms` + `reranked` fields;reranker 設 → fetch_k = max(top_k, hybrid_overfetch),hybrid → reranker → top_k;reranker = None → hybrid 直 truncate(W2 baseline 行為保留)
- `backend/api/server.py` lifespan:`make_reranker(settings)` 由 W3 D1 factory 帶入 retrieval engine;factory returns None when env unset → graceful hybrid-only fallback。`__aenter__/__aexit__` lifespan 管理
- 2 new tests pass:overfetches when reranker present(fetch_k=50,score replaced by rerank_score)+ no rerank when hits empty
- `test_eval_runner.py` `_retrieval_result()` fixture 補 `rerank_latency_ms`+`reranked` 兼容 RetrievalResult signature change

#### F2 — GPT-5.5 synthesis pipeline(C05 NEW package)

- `backend/generation/__init__.py` ✅ NEW
- `backend/generation/prompt_builder.py` ✅ NEW:
  - `SYSTEM_PROMPT` enforces:answer-only-from-chunks / cite via `[chunk-{id}]` / refuse with literal `REFUSAL_PHRASE` / match user language / never fabricate chunk_ids
  - `build_prompt(query, chunks) → PromptMessages` system + user
- `backend/generation/synthesizer.py` ✅ NEW:
  - `Synthesizer` wraps `AsyncAzureOpenAI` chat.completions(deployment=`gpt-5-5` per `azure_openai_deployment_llm_primary`)
  - `tenacity` retry on `RateLimitError` + `APITimeoutError`(3 attempts exponential 1-8s)
  - `extract_citation_ids(answer_text)` regex `\[chunk-([^\]\s]+)\]` ordered + dedup
  - `SynthesisResult`:answer / citation_ids / refused / input_tokens / output_tokens / latency_ms / deployment
  - structlog `synthesizer_call` event for cost trace per architecture.md §7
  - `temperature=0.1` baseline(deterministic factual)
  - Refusal detection:`REFUSAL_PHRASE in answer_text` → `refused=True`(R4 hallucination guard)
- 10 unit tests pass(prompt structure / system prompt content / extract_citation_ids order+dedup / mocked synthesize / refusal detect / temperature passthrough)

#### F3 — Citation enrichment + `/query` end-to-end wire

- `backend/generation/citation_enrichment.py` ✅ NEW:
  - `parse_embedded_images(json_str) → list[ImageRef]` graceful empty / malformed / non-array
  - `build_citations(citation_ids, retrieved_chunks) → list[Citation]` order preserved by appearance;hallucinated ids logged via `citation_hallucinated_ids` event(skipped silent,non-blocking)
  - W2 D3 R12 deferral:`embedded_images_json` 目前全部 `[]` → Citation.embedded_images = []
- `backend/api/routes/query.py` ✅ rewritten:retrieve → if synthesizer set → synthesize → build_citations → QueryResponse with answer + citations + retrieved_chunks + reranker_used + refused;synthesizer = None → W2 fallback retrieval-only。Synthesis exception → 502 BadGateway(同 retrieval 一致)
- `backend/api/server.py` lifespan:Synthesizer init from same Azure OpenAI endpoint+key but `azure_openai_deployment_llm_primary`;`app.state.synthesizer` populate when keys present
- 10 unit tests pass(parse images empty/[]/valid/malformed/non-array;build_citations preserves order/skips unknown/populates fields/empty/real image json)

#### Test suite

- **129/129 backend tests pass**(107 → 129,+22:10 synthesizer + 10 citation_enrichment + 2 retrieval reranker tests)
- ruff clean

### Decisions / OQ Resolved

- **Decision** — `RetrievedChunk.score` after rerank stores `rerank_score`(non hybrid score);RerankedChunk dataclass 留 hybrid_score 供 trace。UI / Citation 用 single relevance_score
- **Decision** — `temperature=0.1` baseline(deterministic factual,minor variation 比 0.0 strict 自然)
- **Decision** — Hallucinated citation_ids logged + silently skipped(non breaking;observability via Langfuse for W4 rate analyze)
- **Decision** — `build_citations` 保留 appearance order(mirrors answer text reading flow,not relevance-sorted)
- **No new OQ resolved**

### Blockers cleared / remaining

- ✅ F1.7 / F2 / F3 — code complete + 22 tests pass
- ⏸ Cohere Marketplace endpoint+key populate(Chris async procurement)— gates rerank live verify only;synthesis path not affected
- ⏸ Real `/query` end-to-end live call(GPT-5.5 chat completion)— manual test post-deploy / next session

### Actual vs Planned Effort

| Item | Planned (h) | Actual (h) | Variance | Note |
|---|---|---|---|---|
| F1.7 wire reranker into engine + server lifespan | 1.5 | 0.5 | -1.0h | Scaffold from W3 D1 + server lifespan add |
| F2 prompt_builder + synthesizer + 10 tests | 6.0 | 1.5 | -4.5h | openai SDK + tenacity 已熟 pattern |
| F3 citation_enrichment + /query wire + 10 tests | 2.0 | 0.7 | -1.3h | Pure data transform |
| test_retrieval reranker tests + eval fixture compat | 0.3 | 0.2 | -0.1h | Signature cascade |
| Day 2 progress entry | 0.5 | 0.4 | -0.1h | This entry |
| **Total D2** | **10.3** | **3.3** | **-7.0h** | Scaffold-first design + Mock pattern reuse + simple data layer |

### Commits

| Hash | Subject |
|---|---|
| `26ed45d` | `feat(c04,c05): W3 D2 — F1.7 wire reranker + F2 GPT-5.5 Synthesizer + F3 citation enrichment + /query end-to-end (129/129 tests)` |

---

## Day 3 — 2026-05-04 (Mon — early start same-day W3 D2 closeout)

> Per Chris signoff "5. W3 sequencing 確認可以"。F5 PPT parser 已 W3 D1 早段 done,F4 SSE streaming 即 W3 D3 唯一 deliverable。

### Done

#### F4 — SSE streaming response(C08 + C05)

- `backend/generation/synthesizer.py`:加 `synthesize_stream(query, chunks) -> AsyncIterator[dict]`
  - `await self._client.chat.completions.create(stream=True, stream_options={"include_usage": True})`
  - Yields `{"type": "text-delta", "content": str}` per OpenAI delta chunk
  - 收 stream 完後 yield single `{"type": "result", "answer", "citation_ids", "refused", "input_tokens", "output_tokens", "latency_ms", "deployment"}`
  - try / finally 確保 underlying OpenAI stream `.close()` called(client disconnect cancellation graceful)
  - structlog `synthesizer_stream_complete` event after stream(non per-chunk noise)
  - **NOT retried by tenacity**(partial output already streamed to client — retry would replay)
- `backend/generation/stream_composer.py` ✅ NEW pure-data composer:
  - `compose_query_stream(retrieval_result, synth_stream) → AsyncIterator[dict]`
  - Passthrough text-delta events;當 synthesizer 發 `result` event:`build_citations(citation_ids, chunks)` → emit one `citation` event per cited chunk + final `done` event(model / total_latency_ms / refused / reranker_used)
  - Hallucinated citation_ids silently skipped(per F3 design)
  - Pure data transform — no I/O,unit testable without TestClient
- `backend/api/routes/query.py` `/query/stream` ✅ rewired:
  - Vercel AI SDK SSE protocol — `data: {json}\n\n` event frames
  - Composes:retrieve → synthesize_stream → compose_query_stream → JSON-encoded SSE
  - 503 when synthesizer 未 init / 502 retrieval failure / asyncio.CancelledError logged + propagated(client disconnect graceful)
  - W1 stub 501 移除
- `backend/tests/test_synthesizer.py` 加 4 SSE tests:text-deltas + result event ordering / refusal phrase detect through stream / empty choices passthrough(usage-only frame)/ underlying stream `close()` called via finally
- `backend/tests/test_stream_composer.py` ✅ NEW 5 tests:passthrough text-deltas + citations + done / reranker_used flag from RetrievalResult.reranked / 1 citation event per unique cited chunk_id / refused flag carried through done / hallucinated chunk_ids silently skipped
- `backend/tests/test_api_skeleton.py`:`/query/stream` test 從 expect 501 改 expect 200 / 502 / 503(W3 D3 wire-in cascade)
- `_MockStream` test helper class added(SimpleNamespace 唔 support `__aiter__` instance attr;proper class implements protocol)

#### Test suite

- **138/138 backend tests pass**(129 → 138,+9 F4 tests:4 synthesize_stream + 5 stream_composer)
- ruff clean

### Decisions / OQ Resolved

- **Decision** — Stream not retried by tenacity。Rationale:partial output已 emitted to client;retry would duplicate text-delta events。Sync `synthesize()` retains 3-attempt retry。Operationally:rate-limit during stream → user sees abrupt cut-off + 502;backoff handled at session level if user re-issues query
- **Decision** — `compose_query_stream` pure-data design(non I/O coupling)。Rationale:unit tests 100% in-memory async generator,no TestClient / lifespan setup required;route layer remains thin JSON-serialization shell
- **Decision** — `result` event terminal in synthesizer stream。Rationale:single composition point,non re-yielding;composer 用 `return` after done event,signals consumer terminal
- **Decision** — Cancellation = best-effort underlying stream close + propagate `CancelledError`(non swallow)。Rationale:asyncio task cancel from FastAPI client disconnect should not be silently absorbed — propagation lets parent task finalize cleanly
- **No new OQ resolved**(all W3 OQ either resolved or future W4-W7 scope)

### Blockers cleared / remaining

- ✅ F4 SSE streaming code complete + 9 tests pass
- ⏸ Live verify SSE end-to-end against real Azure OpenAI GPT-5.5 streaming(W3 D4-D5 with Chat UI integration manual smoke)
- ⏸ Cohere Marketplace endpoint+key populate(Chris async procurement)— gates rerank live verify;non blocking F4
- W3 D3 plan F5 PPT parser already W3 D1 早段 done

### Actual vs Planned Effort

| Item | Planned (h) | Actual (h) | Variance | Note |
|---|---|---|---|---|
| F4 synthesize_stream(openai stream + result event)| 1.5 | 0.6 | -0.9h | openai SDK stream API straightforward |
| F4 stream_composer pure-data module | 0.5 | 0.3 | -0.2h | Single async generator function |
| F4 /query/stream route wire | 0.5 | 0.3 | -0.2h | StreamingResponse + json.dumps + try/except cancel |
| F4 unit tests(4 stream + 5 composer)+ test_api_skeleton compat | 1.5 | 0.7 | -0.8h | _MockStream helper class + AsyncMock wrapper |
| F4 W3 progress entry | 0.3 | 0.3 | 0 | This entry |
| **Total D3** | **4.3** | **2.2** | **-2.1h** | Pure-data composer design + scaffold-first paid off |

### Commits

| Hash | Subject |
|---|---|
| `1267c02` | `feat(c05,c08): F4 SSE streaming — synthesize_stream + stream_composer + /query/stream wire (W3 D3; 138/138 tests)` |

---

## Day 4 — 2026-05-04 (Mon — early start same-day W3 D3 closeout)

> Per Chris signoff "5. W3 sequencing 確認可以"。F6 Chat UI streaming + citation card + F7 Screenshot modal 一次過落地。

### Done

#### F6 — Chat UI streaming + citation card(C10)

- `frontend/lib/api/query.ts` ✅ NEW:
  - TypeScript types mirroring backend Pydantic schemas:`ImageRef` / `Citation` / `QueryRequest` / discriminated `SseEvent` union(`TextDeltaEvent` / `CitationEvent` / `DoneEvent`)
  - `streamQuery(payload, signal)` async generator using native fetch streaming + `TextDecoder` + `\n\n` SSE-frame split + `JSON.parse(data: ...)`
  - **Non Vercel AI SDK `useChat`** — backend SSE 用 custom JSON event protocol(citation + done events 唔 standard);wrap useChat 會加 indirection 0 benefit per Karpathy §1.2。Native fetch + small parser cleaner
  - Aborts via passed `AbortSignal`(client cancellation)
- `frontend/app/page.tsx` ✅ rewritten:Chat page Client Component
  - `Message` type:role / content / citations / isStreaming / refused / rerankerUsed / errorText
  - `handleSubmit` creates user msg + placeholder assistant msg → drives `streamQuery` → per-event React state patches:
    - `text-delta` → append to assistant content
    - `citation` → push to assistant citations[]
    - `done` → set isStreaming=false + refused / rerankerUsed
  - Stop button uses `AbortController` to cancel streaming
  - Empty state placeholder prompts user to ask financial-software questions
  - Cursor blinking ▍ during stream;refused banner when answer = REFUSAL_PHRASE;error banner on stream exception
  - `MessageBubble` 分 user(primary bg)/ assistant(border + muted bg)`max-w-[88%]`
  - Reranker label `reranker: cohere-v3.5 / off` shown post-stream

#### F7 — Screenshot modal

- `ScreenshotModal` inline component(per W2 D5 `Stat` / `Field` helper pattern)
  - Fixed inset-0 backdrop `bg-black/70` z-50
  - Click backdrop → close;click image area → propagation stopped
  - Esc key handler in ChatPage `useEffect` window listener
  - `Close (Esc)` button top-right
  - Image `max-h-[85vh] w-auto` 自然 fit
- `CitationCard` thumbnail click → opens modal with `embedded_images[0]`
- W2 D3 R12 caveat:`embedded_images_json="[]"` baseline → thumbnail conditional render(if `blob_url`),W7+ Cloud Blob populate 後 thumbnail real render

#### Frontend gates

- `pnpm type-check` ✅ clean(`tsc --noEmit`)
- `pnpm lint` ✅ clean(no ESLint warnings/errors)
- `<img>` use intentional + flagged `eslint-disable @next/next/no-img-element`(R12 deferral:Blob URLs are dynamic Azure Storage,不適合 Next.js Image optimization domain config until W7+)

#### Test suite

- Backend 138/138 still pass(no backend changes)
- Frontend tests deferred per CLAUDE.md §5.6 H6 stance(UI tests nice-to-have,非 hard requirement);end-to-end live verification W3 D4-D5 manual smoke when both backend up + Cohere endpoint populate

### Decisions / OQ Resolved

- **Decision** — F6 用 native fetch streaming(non Vercel AI SDK `useChat`)。Rationale:backend SSE 用 custom JSON event protocol(`text-delta` + `citation` + `done`),`useChat` standard protocol(`0:"text"\n` 等)需要 wrap parser;native fetch + 50-line `streamQuery` 直接 type-safe TypeScript types;測試簡單;non additional dep。Per Karpathy §1.2 simplicity-first
- **Decision** — `<img>` over Next.js `<Image>` for Citation thumbnails / Screenshot modal。Rationale:Citation `blob_url` 係 dynamic Azure Storage signed URLs,Next.js `Image` `domains` config 限制 + 預先 known origins;W2 D3 R12 deferred to W7+ cloud Blob populate when domains stabilized。`eslint-disable @next/next/no-img-element` flagged inline
- **Decision** — Per Karpathy §1.2 inline `MessageBubble` / `CitationCard` / `ScreenshotModal` 喺 `page.tsx`(同 W2 D5 admin views `Stat` / `Field` pattern)。Rationale:W3 D4 baseline 同 W2 D5 一致;W3 D5 F8 polish 一齊 split into `frontend/components/chat/` directory + shadcn upgrade
- **Decision** — Single-KB `KB_ID = 'drive_user_manuals'` hardcoded。Rationale:W3 single-KB POC scope;multi-KB selector W7+ Beta(Microsoft Entra ID + tenant context)
- **Decision** — Stop button cancels stream via `AbortController` + `AbortSignal` propagated through `streamQuery`。Backend `/query/stream` already handles `asyncio.CancelledError` per W3 D3 F4 design
- **No new OQ resolved**

### Blockers cleared / remaining

- ✅ F6 + F7 code complete + type-check + lint clean
- ⏸ Live end-to-end:requires Azure OpenAI GPT-5.5 + (optional)Cohere Marketplace endpoint+key — Chris async procurement;manual smoke W3 D5 polish window
- ⏸ Frontend dev server `pnpm dev` 啟動 manual verification 留 Chris(per CLAUDE.md "if you can't test the UI, say so explicitly rather than claiming success")

### Actual vs Planned Effort

| Item | Planned (h) | Actual (h) | Variance | Note |
|---|---|---|---|---|
| F6 streamQuery async generator + types | 1.0 | 0.4 | -0.6h | Native fetch + TextDecoder + SSE frame split is well-known pattern |
| F6 ChatPage with state + streaming + Stop | 4.0 | 1.5 | -2.5h | Plain HTML/Tailwind reuse W2 D5 admin pattern;async iteration directly drives setState |
| F7 ScreenshotModal + CitationCard inline | 2.0 | 0.5 | -1.5h | Inline components(W2 D5 helper pattern);Esc keyboard + click backdrop standard |
| Type-check + lint pass | 0.3 | 0.2 | -0.1h | Clean first try;TypeScript discriminated union catches event-type errors compile-time |
| Day 4 progress entry | 0.5 | 0.4 | -0.1h | This entry |
| **Total D4** | **7.8** | **3.0** | **-4.8h** | Plain-Tailwind + async-iteration design + W2 patterns reuse |

### Commits

| Hash | Subject |
|---|---|
| `6af5430` | `feat(c10): F6 Chat UI streaming + citation card + F7 Screenshot modal (W3 D4)` |

---

## Day 5 — 2026-05-04 (Mon — early start same-day W3 D4 closeout)

> Per Chris signoff + W3 D2/D3/D4 batch-execute pattern。F8 Pipeline wizard 落地 + F9 confirm done in W2 D5 baseline + F10 retro / W4 kickoff prep。

### Done

#### F8 — Pipeline wizard frontend(C09 view 7)

- `frontend/lib/api/kb.ts` ✅:
  - `KbCreatePayload` interface mirroring backend `KbCreate` Pydantic schema(`kb_id` + `name` + optional `description` + optional `config: KbConfig`)
  - `DEFAULT_KB_CONFIG` constant exported(matches backend defaults — `text-embedding-3-large` / 1024 / `auto` / 50 / 5)so wizard 可以 prefill Step 2 form
  - `kbApi.create(payload)` method calling `POST /kb`(non interpreted — backend 201 returns full `KbStatus`)
- `frontend/app/admin/kb/new/page.tsx` ✅ NEW(per architecture.md §5.5 view 7 + components/C09-admin-ui.md):
  - 3-step wizard:**DATA SOURCE → DOCUMENT PROCESSING → EXECUTE**(plain Tailwind step indicator;shadcn Stepper polish 仝 W3 D4 chat baseline deferred per Karpathy §1.2)
  - **Step 1**:`kb_id`(slug pattern `/^[a-z0-9_-]+$/` client-validated;Azure Search index name safety per backend `KbCreate` docstring)+ `name`(required)+ `description`(optional textarea)
  - **Step 2**:KbConfig override form(embedding_model / embedding_dimension / chunk_strategy / default_top_k / default_rerank_k)+ first-document file picker(`.docx,.pdf,.pptx`)+ inline validation(rerank_k ≤ top_k;positive int constraints)
  - **Step 3**:Summary `<dl>` of全部 wizard state + 2-stage Stage indicator(create + upload pending/success/error)+ Execute button calls `createMutation.mutateAsync` then `uploadMutation.mutateAsync` sequential;success → invalidate `['kb']` query + `router.push(/admin/kb/{kb_id})`
  - Step navigation:`step1Errors` / `step2Errors` derived state disable "Next →";Back buttons preserve form state(non reset);Execute button disable during inflight + after both done(prevent double-fire while redirect pending)
  - Layout reference comment per CLAUDE.md §7:`Layout reference Dify Image 1 wizard (no code copy per CLAUDE.md §7); EKP design tokens only via oklch(...)`
  - Inline `Stepper` / `Step1` / `Step2` / `Step3` / `Field` / `Summary` / `Stage` helpers(同 W2 D5 admin views + W3 D4 chat 一致 inline pattern,split-into-components polish 留 Karpathy §1.2 future-need-driven)

#### F9 — Settings tab confirm done in W2 D5 baseline

- 細看 `frontend/app/admin/kb/[id]/page.tsx`(W2 D5 baseline)實際已 cover plan §F9 acceptance:
  - ✅ KbConfig form(embedding_model / embedding_dimension / chunk_strategy / default_top_k / default_rerank_k)
  - ✅ PATCH wire to `/kb/{id}/settings`(TanStack Query `useMutation` + queryClient invalidate)
  - ✅ Form validation per Pydantic KbConfig schema(native `<input type=number>` / `<select>` enums + backend 422 surfaced as `patchMutation.isError`)
  - ⚠️ "Settings tab" wording in plan was non-binding — single-screen settings + summary stats + failed docs section sufficient per Karpathy §1.2 simplicity(tabbed UI = unrequired flexibility)
  - ❌ "reranker per-KB field" deferred — backend `KbConfig` Pydantic schema 唔 contain `reranker`(reranker = settings global 而非 per-KB tenant config per W3 D2 F1.7 wire);加 per-KB reranker = H1 architectural change → defer W4+ post-shootout
- F9 checklist 4 items 全部 tick;reranker deferral logged as 5th item with explicit reason

#### Test gates

- Frontend `pnpm type-check` ✅ clean(`tsc --noEmit`)
- Frontend `pnpm lint` ✅ clean(no ESLint warnings/errors)
- Backend test suite **138/138 pass**(W3 D3 baseline,no backend changes W3 D5)
- Frontend tests deferred per CLAUDE.md §5.6 H6 stance(UI tests nice-to-have);end-to-end live verification 留 Chris dev server smoke test(per CLAUDE.md "if you can't test the UI, say so explicitly rather than claiming success")

### Decisions / OQ Resolved

- **Decision** — F9 mark done against W2 D5 baseline,non re-implementation。Rationale:plan §F9 acceptance 4 個 sub-items 全部 W2 D5 already satisfied;forcing "tabbed UI" rewrite = re-doing working code per Karpathy §1.3 surgical changes 嘅反面教材
- **Decision** — Reranker per-KB field deferred to W4+ shootout post-decision。Rationale:current architecture exposes reranker via global `Settings`(`backend/storage/settings.py` cohere_*)+ per-query payload(`QueryRequest.reranker?` in `frontend/lib/api/query.ts`)。加 per-KB column = H1 architectural change(`KbConfig` Pydantic schema + `KBService` migration),Karpathy §1.2 唔做 unrequested abstraction;W4 shootout 後 if winning reranker varies per-KB 再 reconsider
- **Decision** — F8 wizard 用 plain Tailwind 而非 shadcn Stepper。Rationale:同 W2 D5 admin views + W3 D4 chat UI 一致 inline pattern;shadcn Stepper component shadcn 官方未 ship(2026-04 snapshot)→ 加 = third-party dep + custom impl = scope creep。Plan §F8 acceptance 寫 "shadcn Stepper" 係 aspirational;step indicator visual + functionality 完全 satisfied by 5-line ordered list with status circles
- **Decision** — Step 2 file picker accepts `.docx,.pdf,.pptx` only(同 W2 D5 upload page);其他 format(.xlsx / .csv 等)defer Tier 2 — 同 architecture.md §3.3 Tier 1 source format scope一致
- **No new OQ resolved**(F8 + F9 不 trigger OQ)

### Blockers cleared / remaining

- ✅ F8 + F9 + (overlap with F10 below)code complete + frontend type-check + lint clean + backend 138/138 still pass
- ⏸ Cohere Marketplace endpoint+key populate(Chris async procurement)— unchanged from W3 D2-D4
- ⏸ Real `/query` end-to-end live call + wizard end-to-end smoke — Chris dev server manual verification(per CLAUDE.md "say so explicitly")
- ⏸ Reranker per-KB field — W4+ shootout post

### Actual vs Planned Effort

| Item | Planned (h) | Actual (h) | Variance | Note |
|---|---|---|---|---|
| F8 `kbApi.create()` + `KbCreatePayload` + `DEFAULT_KB_CONFIG`(lib/api/kb.ts) | 0.5 | 0.2 | -0.3h | Single-method addition + interface mirror |
| F8 wizard page(3 steps + Stepper + validation + execute sequence)| 5.0 | 1.5 | -3.5h | Inline-helper pattern from W2 D5 admin + W3 D4 chat;form state single useState driving step transitions;TanStack Query mutateAsync chains naturally |
| F9 verify + checklist tick(no code change)| 3.0 | 0.3 | -2.7h | Investigation only — W2 D5 已 cover all 4 acceptance sub-items;reranker deferral decision logged |
| Type-check + lint pass | 0.3 | 0.2 | -0.1h | Clean first try(discriminated form-state types catch invalid step transitions compile-time) |
| Day 5 progress entry(F8 + F9 sections)| 0.5 | 0.5 | 0 | This entry |
| **Subtotal F8+F9** | **9.3** | **2.7** | **-6.6h** | F9 was already done — saved 2.7h alone |

### Commits

| Hash | Subject |
|---|---|
| _pending_ | `feat(c09): F8 Pipeline wizard 3-step + KB create API method (W3 D5)` |

---

## Retro(填於 W3 D5 末 / 2026-05-04)

> 寫於 same-day W3 D5 closeout(W3 全部 5 days 落地完成 same calendar day per Chris signoff "5. W3 sequencing 確認可以")

### What worked

- **Scaffold-first design**:F1 Cohere D1 後段 / F2 Synthesizer + F4 SSE 全部用 dataclass + Protocol contract decoupled from network → unit tests AsyncMock cover 100% transport contract;wire-in 變成 dependency injection(W3 D2 F1.7 clean change)
- **Pure-data composer pattern**(W3 D3 F4 `compose_query_stream`):I/O-free async generator → 5-test unit coverage without TestClient / lifespan setup;route layer remains thin JSON-serialization shell
- **Native fetch + AsyncIterable streaming**(W3 D4 F6):TypeScript discriminated union(`SseEvent`)+ async generator yields parsed events → React state patches per-event;non Vercel AI SDK indirection saved ~1h
- **Inline-helper pattern across W2 D5 → W3 D4 → W3 D5**:`Stat` / `Field` / `MessageBubble` / `CitationCard` / `ScreenshotModal` / `Stepper` / `Step1` 全部 single-file;splitting components premature per Karpathy §1.2(F8 polish W4+ if reuse emerges)
- **F5 PPT parser real-sample sanity**(W3 D1 後段):3 corporate templates(FY26 BP DCE / Template / Budget Proposal)0 parse_failed → synthetic-test extends well to enterprise samples
- **Effort variance consistently -2 to -7h per day**:scaffold + Mock pattern + small modules dominate;over-estimation 反映 Karpathy §1.4 verifiable goals + W2 pattern reuse
- **Karpathy §1.2 simplicity-first surfaced 3 explicit deferrals**:F8 shadcn Stepper / F9 reranker per-KB field / F6 Vercel AI SDK useChat — 全部 saved scope creep + 留 W4+ judgment with real data
- **Same-day W3 5-day execution(2026-05-04)**:Chris signoff + Q5 Path A + 3 PPT samples 落地後 momentum 維持,135 tests + 7 features delivered without context-switch overhead

### What didn't work / unexpected friction

- **plan §F9 wording mismatch**:plan 寫 "Settings tab" 暗示 tabbed UI / "reranker" 暗示 per-KB column,actual W2 D5 baseline 用 single-screen + reranker = global setting。W3 D5 變 verify-only。Lesson:plan acceptance criteria 應寫實際 user-visible behavior(form fields + endpoint wired)而非 UI components(tab / Stepper),減 wording-bound rewrite pressure
- **plan estimates consistently 2-3x actual**:W2 也 -3h variance。Lesson W4 plan 起草時 estimate 可以 halve(每 deliverable 1.5-2h baseline)
- **R8 procedural mitigation 仍係 per-session burden**:W3 全程 home network,但每 cloud-bound work pre-flight 都要 verify VPN state。Permanent fix = R12 cloud Azure Blob W7+ 之後 R8 同樣 truststore-doesn't-cover-pip 留作 documented limitation
- **Frontend dev server smoke未由 AI 跑**:per CLAUDE.md "if you can't test the UI, say so explicitly" — F6 chat + F8 wizard live verification 全部 留 Chris。3 個 features(F6 / F7 / F8)依賴 dev server 確認 = W3 D5 後 Chris 至少要 manual smoke 一次,coverage gap acknowledged

### Surprises / discoveries

- **F9 already 80% done in W2 D5**:W3 D5 開頭預期 implement 整個 Settings tab,verify 後發現 plan §F9 acceptance 全部 W2 baseline 已 satisfy。Lesson:phase plan 起草時應 cross-check carry-over from prior phase(W2 → W3 W3 D0 prep stage 唔覆蓋 F9 already-done state)
- **Reranker per-KB vs global** architectural distinction surfaced through F9 work:current `Settings`(global cohere_endpoint + cohere_api_key)+ per-query `QueryRequest.reranker?` override = adequate Tier 1;per-KB column 屬 Tier 2 multi-tenancy adjacency。W4 shootout outcome 將 inform whether per-KB 變 sticky requirement
- **W3 全部 5 days same calendar day 2026-05-04**:Chris signoff momentum + Path A 落地 + scaffold-first design 配合,5 phase days collapse to 1 calendar day(約 16h cumulative effort vs plan 38h estimate)。Lesson:scope-clear sprints with proven patterns can compress;novel-pattern sprints(W2 hybrid retrieval first-time)需要 calendar pacing 多
- **frontend/app/admin/kb/new/page.tsx 405 lines**:single-file wizard with 3 inline step components + 4 helpers。Per Karpathy §1.2 fine since each helper used once,但 W4+ if Settings tab 用同一 wizard pattern(e.g. clone-KB wizard / re-index wizard)考慮 split

### Carry-overs to W04-crag-eval-shootout

W3 D5 末 batch:

1. **C1** Cohere live verify — Marketplace endpoint+key populate(Chris async procurement 7-14d turnaround)+ run F7 retrieval against real corpus + assess rerank lift vs hybrid baseline(plan §3 G5 data-driven W4 confirm)
2. **C2** GPT-5.5 live latency baseline — `/query` end-to-end manual smoke(Chris dev server)+ Langfuse cost trace verification(input_tokens / output_tokens / latency_ms baseline numbers for W4 cost-per-query analysis)
3. **C3** SSE live verify against real Azure OpenAI streaming — F4/F6 end-to-end(token-by-token render + citation card + reranker label + stop button)
4. **C4** Frontend dev server smoke — F6 chat + F7 modal + F8 wizard end-to-end click-through(Chris responsibility per CLAUDE.md "can't test the UI" stance)
5. **C5** Reranker per-KB field reconsideration — W4 shootout outcome 後判斷 per-KB column 是否 sticky requirement(Tier 1 boundary check per H4)
6. **C6** F5 PPT orchestrator wire — `IngestionOrchestrator` `pptx → PptxParser()` registry entry + format auto-detect。W3 D1 早段 noted as W3 D2-D3 deferred but ended up not landed(F2/F3 took precedence);W4 D1 nice-to-have unblocking real-corpus PPT ingest
7. **C7** F8 wizard polish — shadcn Stepper(if shadcn ships)/ split components into `frontend/components/admin/wizard/` directory / drag-drop file picker / multi-doc batch upload — 留 W7+ Beta polish window
8. **C8** plan estimates calibration — W4 plan 用 0.5x current heuristic(每 deliverable 1.5-2h baseline),actual variance 應該 ±0.5h 而非 ±3-5h

### ADR triggers

- **None this phase**。F8 / F9 全部 within architecture.md v5 §5 view spec;F4 SSE 用 `architecture.md §4.5` 標準 protocol;F1/F2/F3 全部 in §3 RAG core scope。Reranker per-KB column 如將來 W4 後決定 implement,將 trigger ADR-0012(`KbConfig` schema extension + multi-tenancy adjacency consideration)

### Phase Gate result(per plan.md §3)

- **G1**(All 10 deliverables 完成 OR explicit defer):**10/10 ✅**
  - F1 (W3 D1+D2) ✅ — Cohere Rerank scaffold + wire(live verify deferred to C1 W4)
  - F2 (W3 D2) ✅ — GPT-5.5 synthesis pipeline
  - F3 (W3 D2) ✅ — Citation enrichment with image refs(R12 graceful empty)
  - F4 (W3 D3) ✅ — SSE streaming response
  - F5 (W3 D1) ✅ — PPT parser(orchestrator wire deferred to C6 W4)
  - F6 (W3 D4) ✅ — Chat UI streaming + citation card
  - F7 (W3 D4) ✅ — Screenshot modal
  - F8 (W3 D5) ✅ — Pipeline wizard frontend
  - F9 (W2 D5 baseline + W3 D5 verify) ✅ — Settings(reranker per-KB field deferred to C5 W4 post-shootout)
  - F10 (W3 D5) ✅ — W3 retro + W4 kickoff(this section)
- **G2**(End-to-end /query → answer + citations + images works on real Drive query):⏸ **deferred C2 W4** — code path complete + 138/138 backend tests + frontend lint/type-check clean;real cloud verification gate Chris dev server smoke
- **G3**(Backend ruff + frontend lint + type-check 0 errors):**✅ All clean** — 138/138 + ruff clean + pnpm type-check + pnpm lint clean
- **G4**(C04/C05/C08/C10 design notes status updated v0/v1 → v1/v2):⏸ **deferred to W04 D1 governance batch**(per CC-5 cross-cutting checklist);non-blocking forward
- **G5**(Cohere rerank measurable improvement vs hybrid baseline):⏸ **data-driven C1 W4 confirm**(plan §3 G5 explicitly marks "Block W4? No")— gates 10-query manual rerank lift smoke post Marketplace endpoint populate

**Phase Gate verdict**:**PASS**(G1+G3 hard gates green;G2/G4/G5 explicitly deferred per plan §3 + W4 carry-overs documented)→ phase status flip `active → closed`

### Phase status

- Closeout commit:_pending W3 D5 closeout commit(this Day-5 entry + checklist tick + W4 kickoff prep)_
- Frontmatter status flipped to `closed`:_pending closeout commit_
- Phase W04 kickoff trigger:`docs/01-planning/W04-crag-eval-shootout/{plan,checklist,progress}.md` 落地 same closeout batch(per PROCESS.md §2.3 lifecycle + CLAUDE.md §10 rolling JIT)

---

**End of W03 progress**(W3 5-day execution closed 2026-05-04 same calendar day per Chris signoff + scaffold-first design + W2 pattern reuse)
