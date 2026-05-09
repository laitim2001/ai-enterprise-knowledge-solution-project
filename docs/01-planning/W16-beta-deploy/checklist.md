---
phase: W16-beta-deploy
plan_ref: ./plan.md
status: active                     # F5 partial-active flip 2026-05-10 — F1-F4 preserved draft pending Track A IT cred trigger
last_updated: 2026-05-10
---

# Phase W16 — Checklist(thin skeleton)

> Atomic checkbox(每 item ≤ 0.5–2 hour effort per W6 C10 calibration)。
> Status:`draft` — pending W16 D1 active flip post Track A IT cred populate event trigger + R-B1 closure。
> **Detailed checkboxes deferred to W16 D1 active flip** per CLAUDE.md §10 R1 rolling-JIT discipline + CO_W14_process_grep_verify FORMALIZED pre-active flip checklist(spec ref grep verification step required before checklist expansion)。

## F1 — Track A IT cred consumption + R-B1 closure verification

- [ ] F1.x Track A IT cred populate event verified received(blocking pre-condition;detail at W16 D1 active flip)
- [ ] F1.x `.env.production` + Azure subscription IDs + Cohere Marketplace billing wiring(detail at W16 D1)
- [ ] F1.x R-B1 closure verification + risk register live update(detail at W16 D1)

## F2 — 25% Beta cohort rollout activation

- [ ] F2.x Cohort definition validation per W6 demo-prep.md beta-plan-v1(internal RAPO + 1-2 friendly departments per Q7 Resolved;detail at W16 D1)
- [ ] F2.x Rollout activation cascade per W11 plan F2.1-F2.4(detail at W16 D1)
- [ ] F2.x Rollback flag-ready per beta-plan-v1(detail at W16 D1)

## F3 — Daily metric monitor + Q15 first weekly signal report

- [ ] F3.x Daily metric monitor — R@5 + Faithfulness + Correctness + Image Association threshold tracking(detail at W16 D1)
- [ ] F3.x Q15 first weekly signal report(manual update frequency baseline measurement;detail at W16 D1)

## F4 — User smoke first run(Playwright E2E baseline capture + browser binary install)

- [ ] F4.1 `npx playwright install chromium` browser binary install(R8 mitigation if needed via personal Azure dev tier per W11 retro CO17 OR ADR-0017 trigger if blocks)
- [ ] F4.2 `pnpm test:e2e:update-snapshots` captures 5 pixel diff baseline screenshots + commits to `tests/e2e/visual-baseline.spec.ts-snapshots/`
- [ ] F4.3 `pnpm test:e2e` 13 tests pass + 0 regression
- [ ] F4.4 W12+W13+W14+W15 manual smoke deferred backlog systematic subsume target actualized

## F5 — Backend stub closure cascade(detail expanded post-grep verification 2026-05-10)

### F5.1 CO_F3a — KB documents/chunks listing

- [ ] F5.1.1 `GET /kb/{kb_id}/documents` — replace 501 stub `documents.py:8` with Azure AI Search index query(filter `kb_id eq` + group by `doc_id`;return list[DocumentSummary])
- [ ] F5.1.2 `GET /kb/{kb_id}/documents/{doc_id}/chunks` — replace 501 stub `chunks.py:16` with index query(filter `kb_id eq + doc_id eq`;return list[ChunkSummary] + pagination if needed)
- [ ] F5.1.3 New schemas `DocumentSummary` + `ChunkSummary` in `api/schemas/documents.py` + `api/schemas/chunks.py`(if not exist)
- [ ] F5.1.4 Unit tests `test_documents_listing.py` + `test_chunks_listing.py`(mock searcher + happy path + empty KB + kb_not_found 404)

### F5.2 CO_F3b — KB name+description PATCH(per Decision A.1 NEW endpoint)

- [ ] F5.2.1 New schema `KbMetadataPatch` in `api/schemas/kb.py`(name + description fields,both Optional for partial PATCH)
- [ ] F5.2.2 New endpoint `PATCH /kb/{kb_id}` in `routes/kb.py`(NOT replace existing `/settings` — separate concern;settings = config / kb-level = metadata)
- [ ] F5.2.3 `KBService.update_metadata(kb_id, patch)` method + `KBStorageBackend.update_metadata` Protocol method + InMemory impl
- [ ] F5.2.4 Unit tests `test_kb_metadata_patch.py`(happy path + 404 + partial fields)

### F5.3 CO_F3c — KB-level reindex(NEW)+ DELETE annotate Azure cleanup defer

- [ ] F5.3.1 New endpoint `POST /kb/{kb_id}/reindex` in `routes/kb.py`(NOT pre-existing — per-doc reindex `documents.py:41` exists separate);202 ACCEPTED per W2 pattern;trigger reindex of all docs in KB
- [ ] F5.3.2 `KBService.trigger_reindex_all(kb_id)` method(returns task_id for tracking;in-memory impl returns mock task_id;real impl = Track A IT cred dependent W17+)
- [ ] F5.3.3 `DELETE /kb/{kb_id}` annotate Decision B.1 docstring(in-memory baseline preserved;Azure AI Search index drop + per-KB Blob container drop **defer Track A IT cred trigger** per W16 plan §3 PARTIAL PASS allow + W17+ candidate)
- [ ] F5.3.4 Unit tests `test_kb_reindex.py`(happy path + 404 + per-doc still-works regression)

### F5.4 CO_W15_F1_backend — eval/run + eval/shootout(per Decision C.1 both full)

- [ ] F5.4.1 `POST /eval/run` — wire `backend/eval/runner.py` + `backend/eval/ragas_runner.py`(existing modules);accept `EvalRunRequest`(eval_set_id + llm_model + reranker + enable_crag);return `EvalReport`(R@5 + faithfulness + correctness + image_assoc + p95_latency + failed_queries + crag_trigger_rate + cost)
- [ ] F5.4.2 `POST /eval/shootout` — multi-reranker comparison(cohere-v4.0-pro + cohere-v3.5 + azure-semantic + off);return `ShootoutReport` schema with per-reranker `EvalReport` + delta table
- [ ] F5.4.3 New schema `ShootoutReport` in `api/schemas/eval.py`(per-reranker EvalReport + winner declaration)
- [ ] F5.4.4 Unit tests `test_eval_run.py`(happy path + invalid eval_set_id + reranker validation)+ `test_eval_shootout.py`(2-way comparison min;dual-rate cost preserved per ADR-0012)
- [ ] F5.4.5 Background task option(eval run can take minutes;FastAPI BackgroundTasks OR poll-based async result)— **decision per F5.4.5 implementation**:synchronous initial(simpler;Beta cohort 50 queries × ~5s = ~4 min OK);background W17+ if scale issue

### F5.5 CO_W15_F2_backend — debug/trace Langfuse correlation(per Decision D.2 full SDK)

- [ ] F5.5.1 `GET /debug/trace/{trace_id}` — replace 501 stub `debug.py:8` with Langfuse SDK trace fetch
- [ ] F5.5.2 New module `backend/observability/langfuse_trace.py` — `fetch_trace(trace_id)` async function + stage extraction(retrieval / rerank / context_expansion / synthesis / crag stages per V6 9-stage model)
- [ ] F5.5.3 New schema `TraceDetail` in `api/schemas/observability.py`(or new `debug.py`)— per-stage timing + tokens + status + raw langfuse data ref
- [ ] F5.5.4 Unit tests `test_debug_trace.py`(happy path + 404 trace_not_found + Langfuse client unavailable graceful degrade)
- [ ] F5.5.5 **UNBLOCKS Drift #3 ADR-0020 frontend Session 2** — V6 6→9 stage `PipelineStageCollapsible` expansion can wire to this endpoint

### F5.x sub-items

- [x] F5.x.1 ~~CO_W15_F1_eval_set_v1 `eval-set-v1` file existence verify~~ — **finding 2026-05-10**:`docs/eval-set-v1.yaml` does NOT exist;`docs/eval-set-v1-draft.yaml` exists(draft only)→ **W17+ candidate**(eval-set-v1 finalization post Beta cohort real-query collection per Q6 + Q15 trigger)
- [ ] F5.x.2 CO_W15_F2_langfuse_url `NEXT_PUBLIC_LANGFUSE_URL` env var configuration:add to `.env.example` + frontend `.env.local.example`(if frontend consumes);backend may also need `LANGFUSE_HOST` env(F5.5 dependency)

---

## Cross-Cutting

- [ ] Each commit references `progress.md` Day-N entry(R2)
- [ ] Component tag in commit message per CC-1(C12 / C03 / C09 / C10 / C11 / C06 / C07 / C02)
- [ ] OQ status sync to `decision-form.md`(R4)— Q15 first weekly signal report W16 F3 trigger
- [ ] Risk register update — R-B1 closure verification(F1 deliverable)+ ADR-0017 reservation candidate(R8 corp proxy mitigation pattern formalization)
- [ ] CLAUDE.md §5.1 H1 boundary check:no architectural change without ADR(W16 scope already covered by ADR-0014 + ADR-0015 + ADR-0016)
- [ ] CLAUDE.md §5.2 H2 boundary check:no new vendor / dependency without ADR(ADR-0017 trigger candidate if R8 mitigation requires personal Azure dev tier formalization)
- [ ] CLAUDE.md §3.2 frontend conventions check:no `any` / no @ts-ignore / **MAJOR MILESTONE entire frontend oklch=0 globally preserved**(W15 D3 F3.4 baseline);Playwright E2E baseline harness preserved
- [ ] CLAUDE.md §5.5 H5 security check:no secret commit;`.env.production` properly gitignored(per root .gitignore §4 secrets)
- [ ] **CO_W14_process_grep_verify FORMALIZED pre-active flip checklist applied** — (1)Read plan literal acceptance criteria;(2)Grep code base for referenced files / functions / patterns;(3)Surface mismatches via Karpathy §1.1 think-before-coding upfront;(4)Document deviations in plan §7 changelog at plan kickoff;(5)Adjust acceptance criteria per actual reality

---

**Lifecycle reminder**:呢份 checklist 衍生自 `plan.md` deliverables。新加 deliverable 必須先入 plan + changelog,然後再加 checklist item。**Detailed checkboxes deferred to W16 D1 active flip** per rolling JIT discipline。
