---
phase: W02-multi-format-ingestion
plan_ref: ./plan.md
status: in-progress
last_updated: 2026-05-03
---

# Phase W02 — Checklist

> Atomic checkbox(每 item ≤ 1–2 hour effort)。
> AI tick 完成嘅 item;唔可以 tick 嘅 item 喺 progress Day-N entry 寫原因。
> Status:`in-progress` 由 W2 D1(2026-05-03 Sun,shifted earlier per plan changelog 2026-05-03)起;W1 D4 draft 階段全 unchecked。

## F1 — Docling .docx parser PoC(carry-over from W1)

- [x] **R8 ops decision** ✅ closed 2026-05-03(home network P1 mitigated,non VPN/hotspot;Docling pip installed)
- [x] `backend/ingestion/__init__.py` package marker
- [x] `backend/ingestion/parsers/__init__.py`
- [x] `backend/ingestion/parsers/base.py` — Parser Protocol + `ParserResult` dataclass(+ Heading / EmbeddedImage / Table dataclasses)
- [x] `backend/ingestion/parsers/docx_parser.py` — Docling-based(`DoclingDocxParser` class implementing `Parser` Protocol)
- [x] **Heading style ~3% finding mitigation** ✅ via Docling SECTION_HEADER visual layout heuristic(no standalone font-size code needed — F1 acceptance "OR visual layout heuristic" satisfied;6.3% coverage averaged on 6 sample = 2× W1 F6 raw style baseline)
- [x] Run on 6 sample manuals(`docs/06-reference/01-sample-doc/`)→ extract heading-aware sections + image inventory + table structure(`scripts/run_docx_parser_sanity.py`)
- [x] Sanity check report ✅ `reports/w02_d1_docx_parser_sanity.yaml`(0 failures,217 headings,1018 images,156 tables across 6 docs)
- [x] Update `components/C01-ingestion.md` status `v0-draft → v1-active`(per CC-5)

## F2 — Layout-aware chunker

- [x] `backend/ingestion/chunker/__init__.py`
- [x] `backend/ingestion/chunker/base.py`(NEW)— `ChunkSpec` dataclass + `Chunker` Protocol
- [x] `backend/ingestion/chunker/layout_aware.py` heading-aware section split + token budget(`LayoutAwareChunker`)
- [x] `backend/ingestion/chunker/strategies.py` strategy selector per `KbConfig.chunk_strategy`(`auto`/`layout_aware` impl;`slide_based`/`heading_aware` raise NotImplementedError per W3+ scope)
- [x] `low_value_flag` heuristic(< 100 token per architecture.md §3.3 + TOC + version + revision statement detect)
- [x] Run on 6 sample → **329 chunks total**(text=173 + table=156)— see W2 D2 progress decision §:plan §2 estimate 2000-3000 was based on per-row table chunking,architecture spec §3.3 mandates per-table → revised expectation
- [x] Unit test:`backend/tests/test_chunker.py` 12 tests pass(synthetic ParserResult fixtures cover heading hierarchy / hard cap split / low_value flag / table chunk / image attachment / parse_failed / format / strategy selector branches / ChunkSpec required fields)

## F3 — Screenshot extractor + Blob upload

- [x] `backend/ingestion/screenshots/__init__.py`
- [x] `backend/ingestion/screenshots/extractor.py` — `ScreenshotExtractor` augments F1 EmbeddedImage(已 PIL→PNG by Docling parser)with kb_id+doc_id+blob_path+content_type
- [x] **EMF / WMF conversion via Pillow** — F1 parser 內已用 Docling/PIL normalize all images to PNG(no separate EMF path needed at F3)
- [x] `backend/ingestion/screenshots/uploader.py` — `ScreenshotUploader` async via `azure.storage.blob.aio` + tenacity retry on Conn/Timeout
- [x] SHA256 dedup logic(blob_path = `{sha256}.{ext}` flat per-KB-container layout → cross-doc dedup;`get_blob_properties` HEAD-check before upload)
- [ ] **DEFERRED** Verify Azurite container populated — R12 Azurite SDK signature mismatch blocks live local verification;mocked unit tests 9/9 pass instead;real cloud Azure Blob W7+ will verify
- [ ] Update `components/C12-devops.md` Blob container provision section — defer to W7+ when cloud deploy lands

## F4 — Embedding pipeline first-pass(carry-over from W1 F10)

- [x] `backend/ingestion/embedding/__init__.py`
- [x] `backend/ingestion/embedding/base.py` — `EmbeddingResult` dataclass + `Embedder` Protocol
- [x] `backend/ingestion/embedding/azure_openai_embedder.py` async via openai SDK `AsyncAzureOpenAI`(R8 mitigated W2 D0 home network → SDK path,non HTTP REST fallback needed)
- [x] text-embedding-3-large + MRL truncate via `dimensions=1024` parameter
- [x] Cost log via structlog event `embedding_call`(batch_size + input_tokens + output_dim + latency_ms + deployment)
- [ ] **DEFERRED** Smoke test 1 sample → 1024d vector — R8 reactivated(GlobalProtect VPN metric 1 over home WiFi metric 60;TLS revocation check fails for Azure OpenAI cert)。Mocked test verifies request shape + 1024d response handling
- [ ] **DEFERRED** Parallel batch 100 chunks < 5s benchmark — same R8 cause as smoke;runnable post VPN disconnect via `backend/.venv/Scripts/python.exe -m scripts.run_embedder_smoke`
- [x] Q19 decision logged ✅ Resolved(`docs/decision-form.md` Q19 entry):**W2 baseline 1024d**(per text-embedding-3-large MRL spec retains majority quality at 1/3 cost;index `ekp-kb-drive-v1` already 1024d per W1 D4 commit `349c33e`;3-way shootout deferred to Gate 1 retro if R@5 < 80%)

## F5 — Index population orchestrator

- [ ] `backend/ingestion/orchestrator.py` end-to-end pipeline:parse → chunk → screenshot → embed → emit ChunkRecord
- [ ] `backend/indexing/populate.py` batch upload to `ekp-kb-drive-v1` via REST `/docs/index`
- [ ] Run on 6 sample → ~2000-3000 chunks indexed
- [ ] `python -m scripts.create_index get` → verify doc count
- [ ] Atomic per-doc transaction:if any chunk fail in a doc → rollback all chunks of that doc
- [ ] Update `components/C01-ingestion.md` and `C03-indexing.md` status v1-active → v2-stable post W2 D5

## F6 — Hybrid retrieval baseline(C04 first-touch)

- [ ] `backend/retrieval/__init__.py`
- [ ] `backend/retrieval/hybrid.py` Azure AI Search hybrid query via REST(BM25 + vector + RRF)
- [ ] Filter clause:`enabled eq true and low_value_flag eq false`
- [ ] `backend/retrieval/retrieval_engine.py` public `retrieve(query, kb_id, top_k)` API
- [ ] Wire to `/query` endpoint(replace 501 stub in C08)— top-50 chunks return
- [ ] Unit test:known query → assert non-empty + ranked output
- [ ] Update `components/C04-retrieval.md` status `v0-draft → v1-active`(per CC-5)

## F7 — Gate 1 evaluation(Recall@5 ≥ 80%)★ HARD GATE

- [ ] `backend/eval/runner.py` invoke C04 retrieval against 30-query eval set
- [ ] Compute Recall@5 per query + aggregate
- [ ] `backend/eval/gates.py` Gate 1 decision logic(R@5 ≥ 80% threshold)
- [ ] Generate `reports/gate1_w2.yaml` per-query + aggregate result
- [ ] **Gate 1 verdict**:pass / fail recorded in W2 progress.md retro
- [ ] If fail → trigger W2 末 retro analysis(chunk strategy / index config / query mismatch root cause)
- [ ] Update `components/C06-eval.md` status `v0-draft → v1-active`

## F8 — F11 ground truth fill(carry-over from W1)

- [ ] `scripts/discover_chunk_ids.py` helper(query populated index,find chunk_id for each eval query expected_answer)
- [ ] Chris(SME)review + validate 30 main queries → mark `annotation.validated: true`
- [ ] Replace placeholder chunk_id with real ones from `ekp-kb-drive-v1`
- [ ] `docs/eval-set-v1.yaml`(rename from v0)
- [ ] `python -m scripts.validate_eval_set docs/eval-set-v1.yaml` → exit 0

## F9 — Admin Console KB views(C09 first-touch)

- [ ] View 2 `/admin` overview component:aggregate KB stats(GET /kb count + total chunks)
- [ ] View 3 `/admin/kb` KB list with shadcn DataTable + TanStack Query useQuery hook
- [ ] View 4 `/admin/kb/[id]` KB detail page + KbConfig form
- [ ] View 4 PATCH wire to `PATCH /kb/{id}/settings`(C02 + C08)
- [ ] View 5 `/admin/kb/[id]/upload` multipart form to C01 ingestion endpoint
- [ ] pnpm lint + type-check clean
- [ ] Update `components/C09-admin-ui.md` status `v0-draft → v1-active`

## F10 — F2 + F7 unit tests retry(carry-over from W1,depends R8)

- [x] **Pre-condition**:R8 mitigated 2026-05-03(Path P1 home network direct;corp proxy SSL inspection / VPN tunnel was the actual interception layer,non corp proxy itself)
- [x] `pip install -e backend[dev]` success(home network ~5min,mypy 10.9MB @ 15.5 MB/s + 其他 dev deps + Docling + Azure SDK + OpenAI SDK 全部 installed)
- [x] `pytest tests/test_api_skeleton.py` → **8/8 pass**(commit `0a2673d`,unblock W1 F2 verification)— surfaced + fixed Pydantic v2.13 compat issue across 5 stub routes(commit `c38710f`)
- [ ] `pytest tests/kb_management/` → CRUD unit tests pass(unblock W1 F7 unit tests)— **tests not yet written** per W1 F7 deferred,W2 D2-D3 implementation 期間補
- [ ] Coverage ≥ 80% on F2/F7 modules per CLAUDE.md H6 — pending F7 unit tests written
- [ ] Update C02 + C08 design notes status to `v2-stable` — pending F7 unit tests + W2 implementation completion

## F11 — W2 末 retro + W3 kickoff prep

- [ ] W02 progress.md retro section completed(per `_templates/phase/progress.md.tpl`)
- [ ] Gate 1 verdict explicit + analysis if fail
- [ ] W03 phase folder mkdir + plan.md draft(per PROCESS.md §2.3 kickoff lifecycle)
- [ ] W03 carry-overs documented
- [ ] W02 progress.md frontmatter status flipped to `closed`

---

## Cross-Cutting

- [ ] Each commit references `progress.md` Day-N entry(R2)
- [ ] Component tag in commit message per CC-1(`feat(scope): description (Cn)`)
- [ ] All architectural-adjacent decisions documented as ADR(per CLAUDE.md §5.1 H1)— W2 暫無 expected
- [ ] OQ status sync to `decision-form.md`(R4)— Q19 W2 D3,Q5 W2 末 if Path A/B decided
- [ ] Component design note status bumps(per CC-5)
- [ ] RISK_REGISTER.md update if R8 mitigation lands or new risk surfaces
- [ ] `progress.md` retro section written W2 D5 末
- [ ] `progress.md` frontmatter status flipped to `closed`
- [ ] Phase W03-chat-retrieval-citation kickoff trigger noted in retro

---

**Lifecycle reminder**:呢份 checklist 隨 plan deliverables 衍生。新加 deliverable 必須先入 plan + changelog,然後再加 checklist item。
