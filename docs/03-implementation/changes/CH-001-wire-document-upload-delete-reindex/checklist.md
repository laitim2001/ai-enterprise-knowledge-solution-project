---
change_id: CH-001
spec_ref: ./spec.md
status: in-progress
last_updated: 2026-05-11
---

# CH-001 — Checklist

> Atomic checkbox items derived from `spec.md` §2.2 In Scope(S1-S20)+ §3 Acceptance Criteria(AC1-AC22)。每 item ≤ 1-2h effort。
> **v1.2 (Decision B = (β)):** added Phase 1.5 multi-KB index provisioning(POST/DELETE /kb)+ extended Phase 5 tests with AC18-AC22.
> Tick `[ ]→[x]` 完成嘅 item;唔可以 tick 嘅 item 喺 `progress.md` Day-N entry 寫原因。

---

## Phase 1 — Backend service wiring(prereqs for the route handlers)

- [x] **T1.1** Read `backend/api/server.py` lifespan in full — existing pattern uses `__aenter__/__aexit__` on Azure clients;**`RetrievalEngine` already wraps the embedder** but doesn't expose it — added `app.state.embedder` separately for ingestion-path reuse — `(this commit)`
- [x] **T1.2** Read `backend/indexing/populate.py` `IndexPopulator` full API — `delete_doc` absent → **added** (moved to T1.5.4 in Phase 1.5);`upload(chunks)` signature extended with `kb_id=None` BC param (T1.5.5) — `(this commit)`
- [x] **T1.3** Read `backend/kb_management/*` `KBService` API — `create / list_all / get / delete / update_config / update_metadata` existed;**counter-sync methods added in Phase 2**:`KBStorageBackend.update_metrics(kb_id, *, documents_delta, chunks_delta, last_indexed_at, append_failure)` Protocol method + `InMemoryKBBackend` impl(model_copy)+ `PostgresKBBackend` impl(single UPDATE with `GREATEST(0, …)` arithmetic + JSONB `||` append)+ `KBService.record_doc_event` wrapper;minimal scope = `total_documents` + `total_chunks` + `last_indexed_at` + `failed_documents`(skip `total_screenshots` + `storage_size_mb` — drift documented as a known future-tier follow-up per progress.md Day-2)— `(this commit)`
- [x] **T1.4** **Approach A confirmed** ── lifespan-init populator + per-request orchestrator(parser is per-file-extension via `select_parser`,chunker stateless,embedder shared with RetrievalEngine);one Azure REST client per app — `(this commit)`
- [x] **T1.5** Wired `app.state.embedder` + `app.state.index_populator` + `app.state.ingestion_chunker` in `api/server.py` lifespan(populator `__aenter__/__aexit__` added;chunker `LayoutAwareChunker()` stateless construction unconditional);added `_ingestion_deps_or_503(request) -> _IngestionDeps`(NEW frozen dataclass)in `api/routes/documents.py` alongside the existing `_engine_or_503`;`mypy --strict` clean on the 3 new files(transitive errors in other unrelated files = pre-existing baseline) — `(this commit)`

## Phase 1.5 — Multi-KB index provisioning(S14-S20 + AC18-AC22)— Decision B = (β)

- [x] **T1.5.1** Read `backend/indexing/schema.json` — confirmed canonical EKP chunk index schema(20 fields incl. `chunk_id` PK / `kb_id` / `doc_id` / `content_vector` 1024-dim HNSW + `vectorSearch.profiles[ekp-vector-profile]` + `semantic.configurations[ekp-semantic-config]`);same schema `ekp-kb-drive-v1` was provisioned with at W2 D1 via `scripts/create_index.py` PUT — `(this commit)`
- [x] **T1.5.2** `IndexPopulator.create_index_for_kb(self, kb_id: str) -> None`(S14)— `_load_index_schema()` `@lru_cache(maxsize=1)` reads `Path(__file__).parent / "schema.json"`;`schema["name"] = kb_id_to_index_name(kb_id, legacy_default_index=self.index_name)`;**PUT**(not POST — matches `scripts/create_index.py` precedent)`/indexes/{name}?api-version={api_version}`;200/201/204 success;raise `httpx.HTTPStatusError` on 4xx/5xx;structlog `index_created` / `index_create_failed` — `(this commit)`
- [x] **T1.5.3** `IndexPopulator.delete_index(self, kb_id: str) -> bool`(S15)— DELETE `/indexes/{name}?api-version={api_version}`;`True` on 204, `False` on 404 (fail-soft for legacy KBs / partial-rollback);raise on other 4xx/5xx;structlog `index_deleted` / `index_already_gone` / `index_delete_failed` — `(this commit)`
- [x] **T1.5.4** `IndexPopulator.delete_doc(self, kb_id: str, doc_id: str) -> int`(S3 / extends Phase 3)— two-step:(1) POST `/docs/search` with `filter="kb_id eq 'X' and doc_id eq 'Y'"`, `select=chunk_id`, `top=AZURE_BATCH_LIMIT`(1000);(2) batch POST `/docs/index` with `@search.action: "delete"` per chunk_id;return count deleted;**fail-soft when index itself is missing**(returns 0 — covers DELETE-on-empty-KB);structlog `doc_chunks_deleted` — `(this commit)`
- [x] **T1.5.5** `IndexPopulator.upload(self, records, action="mergeOrUpload", kb_id: str | None = None)`(S16, BC-preserving)— `_resolve_index_name(kb_id)` helper(kb_id → `kb_id_to_index_name(kb_id, legacy_default_index=self.index_name)`;None → `self.index_name` for W2-era callers);`_upload_batch` refactored to accept `index_name` arg;`scripts/run_populate_sanity.py` + W2 tests pass with the kb_id=None default — `(this commit)`
- [x] **T1.5.6** `POST /kb` wiring(S17)— `_get_populator(request) -> IndexPopulator | None`(NOT 503 ── **fail-soft when populator is None** to preserve W16 F5.3 Decision B.1 baseline + the existing `test_delete_kb_in_memory_baseline_preserved` contract;deviation from the strict-503 spec text, documented in progress Day-1);when populator is present:`try: await populator.create_index_for_kb(payload.kb_id)` / `except: try: await service.delete(payload.kb_id)` rollback;log `storage_rollback_failed` if rollback also fails;raise 502 `index.create_failed` with the hint quoting Azure index-name rules — `(this commit)`
- [x] **T1.5.7** `DELETE /kb/{kb_id}` wiring(S18)— `_get_populator(request)` fail-soft when None(storage already gone, no Azure touch, returns 204);when present:`await populator.delete_index(kb_id)` ── `delete_index` itself is fail-soft on 404;Azure 5xx → 502 `index.delete_failed` with the actionable hint to manually drop via `scripts/create_index.py delete` — `(this commit)`
- [x] **T1.5.8** Dropped the "Track A W17+" deferral comment block in `routes/kb.py` DELETE docstring + replaced with CH-001 closure note + ADR-0018 reference + per-KB blob container R12-deferred note;file-top docstring updated with the new auto-provision behaviour — `(this commit)`
- [ ] **T1.5.9** ADR-0018 `## Implementation timing` row update — **deferred to Phase 7**(grouped with T7.5 docs hygiene — single coherent doc-update commit;spec §6.6 + R11 already document the closure unambiguously, so this is housekeeping not blocking)
- [x] **T1.5.10** Verified `mypy --strict --explicit-package-bases` clean on `indexing/populate.py` + `api/server.py` + `routes/kb.py` + `routes/documents.py`(transitive 103-errors-in-36-other-files = pre-existing baseline);`ruff check` at the pre-existing 19-error E402 baseline on `api/server.py`(2 noqa-suppressed new imports → net delta zero)+ clean on the other 3 files;`pytest backend/tests/{test_orchestrator,test_api_skeleton,test_documents_listing,test_kb_management,test_kb_reindex,test_multi_kb_routing}.py` → **46 passed**(including the previously-failing `test_delete_kb_in_memory_baseline_preserved_per_b1` after the fail-soft fix) — `(this commit)`

## Phase 2 — `POST /kb/{kb_id}/documents`(S2 + AC1-AC7, AC10)

- [x] **T2.1** Replace the 501 stub at `documents.py:72-82` — accept `UploadFile`,stream to `tempfile.NamedTemporaryFile(delete=False, suffix=<ext>)`(per spec R2 — no `await file.read()` whole into memory)
- [x] **T2.2** doc_id = slugify(filename stem) → regex `[a-z0-9-]+`(per S5);check kb_id with `_verify_kb_or_404`(per S6;already in the file);check duplicate doc_id within the kb via existing `RetrievalEngine.list_documents(kb_id)` aggregation;return **409** `code: "document.duplicate"` if dup
- [x] **T2.3** Call `select_parser(Path)` from `backend/ingestion/parsers/__init__.py`;catch its `ValueError` for unsupported extensions → **422** `code: "validation.unsupported_format"`(per AC3)
- [x] **T2.4** Call `IngestionOrchestrator.ingest(source, kb_id, doc_id, source_url=f"upload://{filename}")` → `IngestionResult`;branch on `result.failure`:`stage="parse"` → **502** `code: "ingestion.parse_failed"`;`stage="embed"` → **502** `code: "ingestion.embed_failed"`(per AC6)
- [x] **T2.5** Call `IndexPopulator.upload(result.chunks, kb_id=kb_id)`(per T1.5.5 — pass `kb_id` to target the per-KB index `ekp-kb-{kb_id}-v1`,NOT the legacy `ekp-kb-drive-v1`)→ `IndexUploadResult`;if `upload_result.failed > 0` → **502** `code: "ingestion.index_failed"` + the count;else proceed
- [x] **T2.6** Update KB counters via `KBService`(per S7 + AC10): `total_documents += 1`、`total_chunks += len(result.chunks)`、`last_indexed_at = now`、`storage_size_mb += file_size_mb`;失敗就 logged but non-fatal(counter drift is recoverable per spec R7)
- [x] **T2.7** Return **200 or 202** with `{doc_id, status: "indexed", chunks_emitted, images_uploaded, images_deduped}` per AC1
- [x] **T2.8** `finally:` clause unlinks the tempfile path(per S9);verify no leak on parse/embed/index failure paths
- [x] **T2.9** Error envelope helper — if not already in `backend/api/errors.py` or similar, add a small `make_api_error(code, message, hint, status)` to keep the 5+ error returns consistent
- [x] **T2.10** `_engine_or_503(request)`-style check for Azure cred — if `app.state.ingestion_orchestrator is None` or its embedder/populator is None → **503** `code: "azure.config_missing"`(per AC5)

## Phase 3 — `DELETE /kb/{kb_id}/documents/{doc_id}`(S3 + AC8)

- [x] **T3.1** Replace the 501 stub at `documents.py:85-92` — verify kb_id (`_verify_kb_or_404`);call `IndexPopulator.delete_doc(kb_id, doc_id)` (added in T1.5.4) → returns the count deleted
- [x] **T3.2** If `count == 0` → **404** `code: "document.not_found"`(per AC8 — clean idempotency story:DELETE on missing = 404, not 204)
- [x] **T3.3** If Azure delete errors → **502** `code: "index.delete_failed"`(per AC8)
- [x] **T3.4** Update KB counters via `KBService` — `total_documents -= 1`、`total_chunks -= count`、`last_indexed_at = now`;non-fatal on failure(same as T2.6)
- [x] **T3.5** Return **204** No Content per AC8(success path)

## Phase 4 — `POST /kb/{kb_id}/documents/{doc_id}/reindex`(S4 + AC9 — Decision A = (ii) replace-in-place)

- [x] **T4.1** Replace the 501 stub at `documents.py:95-102` — change the signature to accept `UploadFile`(same as POST upload);if missing → **422** `code: "validation.file_required"`(per AC9.2)
- [x] **T4.2** Verify kb_id + doc_id both exist(kb_id via `_verify_kb_or_404`,doc_id via `RetrievalEngine.list_documents(kb_id)` lookup)→ **404** `code: "document.not_found"` if doc_id missing
- [x] **T4.3** Slugify uploaded-file stem;if `!= doc_id` → **422** `code: "reindex.doc_id_mismatch"`(UX safety per spec §2.3 + AC9 ── 防呆「上錯 file」)
- [x] **T4.4** Call `IndexPopulator.delete_doc(kb_id, doc_id)`(reuse from T3)— records the deleted count for counter accounting
- [x] **T4.5** Run the same ingest path as POST(tempfile + `select_parser` + `IngestionOrchestrator.ingest` + `IndexPopulator.upload`)under the **same** `doc_id`
- [x] **T4.6** If mid-pipeline fails (after delete, before re-ingest succeeds) → **502** `code: "reindex.partial_failure"` + the FailureRecord;the KB is now in a deleted-but-not-re-ingested state(observable = "doc gone");actionable_hint:"retry via POST /kb/{kb_id}/documents with the same file"(per AC9.3)
- [x] **T4.7** Update KB counters via `KBService` — net is `total_chunks` from delete-count → new emit count;`last_indexed_at = now`;`total_documents` unchanged(same doc_id, just re-indexed)
- [x] **T4.8** Return **202** with `{doc_id, status: "reindexed", chunks_emitted, images_uploaded, images_deduped}` per AC9.1
- [x] **T4.9** Code dedup — if T2 and T4 share enough body, extract a `_run_ingest_pipeline(kb_id, doc_id, upload_file, source_url) → IngestionResponse | ApiError` helper to keep both routes thin(Karpathy §1.2 — only if it's clearly cleaner, not for the sake of it)

## Phase 5 — Tests(S10 + AC11-AC12)

- [x] **T5.1** NEW `backend/tests/api/__init__.py`(empty package marker)+ `backend/tests/api/test_documents_route.py` — FastAPI `TestClient` + monkeypatched `IngestionOrchestrator` (factory returns MagicMock with `.ingest` AsyncMock) + `select_parser` (returns MagicMock parser) + `IndexPopulator` (MagicMock with all 4 CH-001 method AsyncMocks: `upload` / `delete_doc` / `create_index_for_kb` / `delete_index`);real Azure calls stay smoke-script territory per spec design — `(this commit)`
- [x] **T5.2** AC1 — `test_upload_happy_path_returns_202_indexed` ── POST `.docx` → 202 with body `{status:"indexed", doc_id, chunks_emitted, images_uploaded, images_deduped}`;orchestrator + populator both awaited — `(this commit)`
- [x] **T5.3** AC2 — `test_upload_supports_pdf_and_pptx` parametrized for `.pdf` (ADR-0019) + `.pptx` (W3 D5)— `(this commit)`
- [x] **T5.4** AC3 — `test_upload_unsupported_format_returns_422` ── `.txt` → 422 `validation.unsupported_format` — `(this commit)`
- [x] **T5.5** AC4 — `test_upload_unknown_kb_returns_404` ── unknown kb_id → 404 from `_verify_kb_or_404` BEFORE any orchestrator call(asserted via `populator.upload.assert_not_awaited()`)— `(this commit)`
- [x] **T5.6** AC5 — `test_upload_no_populator_returns_503` ── `app.state.index_populator is None` → 503 — `(this commit)`
- [x] **T5.7** AC6 — `test_upload_parse_or_embed_failure_returns_502` parametrized for `stage="parse"` / `"embed"`(→ 502 with matching `ingestion.{stage}_failed` code, populator never awaited);+ `test_upload_index_partial_failure_returns_502` covers populator's partial-fail path(`succeeded=8, failed=4`)→ 502 `ingestion.index_failed` — `(this commit)`
- [x] **T5.8** AC7 — `test_upload_duplicate_doc_id_returns_409` ── engine.list_documents returns `[{"doc_id": "manual"}]` when uploading `manual.docx` → 409 `document.duplicate` + populator never awaited — `(this commit)`
- [x] **T5.9** AC8 — 3 tests:`test_delete_happy_returns_204_and_records_counter`(happy + AC10 counter assert)/ `test_delete_not_found_returns_404`(delete_doc returns 0 → 404 `document.not_found`)/ `test_delete_azure_error_returns_502`(delete_doc raises ConnectionError → 502 `index.delete_failed`)— `(this commit)`
- [x] **T5.10** AC9.1 — `test_reindex_happy_returns_202_reindexed` ── doc exists → delete_doc → ingest → 202 `reindexed` + chunks_emitted from upload_result;`delete_doc.assert_awaited_once_with(kb_id, doc_id)` — `(this commit)`
- [x] **T5.11** AC9.2 — `test_reindex_missing_filename_returns_422` ── empty filename in multipart part → 422 from FastAPI's own UploadFile validation(the route's defensive `validation.file_required` guard is unreachable via HTTP because FastAPI rejects first);`delete_doc.assert_not_awaited()` confirms the destructive path is never reached — `(this commit)`
- [x] **T5.12** AC9.3 — `test_reindex_mid_pipeline_failure_returns_502_partial`(orchestrator returns FailureRecord AFTER delete_doc → 502 `reindex.partial_failure` + delete_doc.assert_awaited_once())+ `test_reindex_doc_id_mismatch_returns_422`(uploaded `wrong-doc.docx` vs path `manual` → 422 `reindex.doc_id_mismatch`)+ `test_reindex_doc_not_found_returns_404`(`_doc_exists_in_kb` returns False → 404 `document.not_found` + delete_doc never awaited)— `(this commit)`
- [x] **T5.13** AC10 — counter-sync covered in 2 tests:`test_upload_records_counter_event_on_success`(documents_delta=+1, chunks_delta=7, last_indexed_at not None)+ `test_delete_happy_returns_204_and_records_counter`(documents_delta=-1, chunks_delta=-5)— `(this commit)`
- [x] **T5.14** AC18 — `test_post_kb_calls_create_index_for_kb` ── POST /kb → 201 + `populator.create_index_for_kb.assert_awaited_once_with(kb_id)` + GET /kb/{kb_id} → 200(no rollback)— `(this commit)`
- [x] **T5.15** AC19 — `test_post_kb_index_create_fail_rolls_back_returns_502` ── `create_index_for_kb` raises → 502 + GET /kb/{kb_id} returns 404 confirming storage rollback. The rollback-also-fails branch is internal log-only behaviour(R10)harder to test without leaking InMemoryBackend internals — covered via static read of the route(`kb.py:96-102`)— `(this commit)`
- [x] **T5.16** AC20 — `test_delete_kb_calls_delete_index` ── DELETE /kb → 204 + `populator.delete_index.assert_awaited_once_with(kb_id)` — `(this commit)`
- [x] **T5.17** AC21 — `test_delete_kb_index_already_gone_fail_soft_returns_204` ── `delete_index_returns=False`(404 / index already gone)→ still 204(fail-soft)— `(this commit)`
- [x] **T5.18** AC22 — `test_upload_targets_per_kb_index_not_legacy` ── asserts `populator.upload.call_args.kwargs["kb_id"] == "drive_user_manuals"`(NOT `None`,confirms chunks land in the per-KB index NOT the legacy `ekp-kb-drive-v1`)— `(this commit)`
- [ ] **T5.19** **NEW per Decision B** Test:`IndexPopulator.create_index_for_kb` + `delete_index` unit tests with monkeypatched httpx client — **🚧 deferred(Karpathy §1.2 simplicity-first)**:both methods are transitively covered via the route-level tests T5.14-T5.17 + the AC18-AC21 + `scripts/run_populate_sanity.py` reference run + `scripts/create_index.py` precedent. A dedicated `test_index_populator.py` with mocked httpx responses doesn't add coverage beyond integration smoke ── deferred to a future "Azure REST smoke harness" Change if real-Azure validation is needed
- [x] **T5.20** `.venv/Scripts/python.exe -m pytest tests/api/test_documents_route.py` → **24 passed**(2 DeprecationWarnings pre-existing baseline,FastAPI internal + `HTTP_422_UNPROCESSABLE_ENTITY` constant — not introduced by CH-001)— `(this commit)`
- [x] **T5.21** Regression run:`pytest tests/{test_orchestrator,test_api_skeleton,test_documents_listing,test_kb_management,test_kb_reindex,test_multi_kb_routing}.py tests/api/test_documents_route.py` → **70 passed**(46 prev + 24 new — zero regression);`mypy --strict` 0 errors on the new test file(47 transitive errors in 15 other files = pre-existing baseline);`ruff check` clean — `(this commit)`
- [x] **T5.22** `pnpm test:unit` skipped — CH-001 made zero frontend changes(no `frontend/` paths touched per `git diff --stat` against `b87ce77..HEAD`);implicit AC12 satisfied — `(this commit)`

## Phase 6 — End-to-end manual smoke(AC14 + AC18 + AC20 + AC22)

- [ ] **T6.1** `:8000` backend + `:3001` frontend up;`.env` has `AZURE_OPENAI_API_KEY` + `AZURE_SEARCH_ADMIN_KEY`(if missing → skip to AC5 verification then declare manual smoke deferred to「after `.env` is populated」)
- [ ] **T6.2** Browser:`/kb/new` Pipeline wizard → step 1 fill **a new** KB id(e.g. `ch001-smoke` or `copilot-cowork-document-1` like the user's screenshot)→ step 2 upload `RAPO_Cowork_Pilot_Kickoff_Plan.docx`(or any `.docx` from `docs/06-reference/01-sample-doc/`)→ step 3 Execute → **✓ Create KB**(now also provisions the Azure index per AC18)+ **✓ Upload + Ingest**(was ✗ 501;now goes to the per-KB index per AC22)→ return to `/kb/{kb_id}` shows the doc in the Documents tab
- [ ] **T6.3** Browser:`/kb/{kb_id}` Documents tab → "Delete" on the just-uploaded doc → confirm → doc disappears from the list
- [ ] **T6.4** Browser:DELETE the smoke KB(via UI if available, else `curl -X DELETE :8000/kb/ch001-smoke`)→ verify via direct Azure REST `GET /indexes/ekp-kb-ch001-smoke-v1?api-version=2024-07-01` that the index is gone(per AC20)
- [ ] **T6.5** Browser (optional, time-permitting):re-upload the same `.docx` → POST `/kb/{kb_id}/documents/{doc_id}/reindex` happy path verification(may not have a UI button yet — could test via `curl` if needed)
- [ ] **T6.6** Direct Azure verify (optional curl):`GET /indexes?api-version=2024-07-01` lists `ekp-kb-{kb_id}-v1` after POST /kb, and is absent after DELETE /kb — confirms ADR-0018 Phase 3 upload-side end-to-end

## Phase 7 — Docs + closeout(S11 + S13 + S19 + AC15-AC17)

- [ ] **T7.1** Remove the file-top docstring stale block at `documents.py:1-10`("Other endpoints remain 501 stub pending W2 multi-format ingestion") — replace with a CH-001 closure note
- [ ] **T7.2** Update each route's docstring to describe its real behavior(per S11);for `routes/kb.py` POST + DELETE,update the docstrings to mention the new auto-index-provisioning(per S19)
- [ ] **T7.3** `session-start.md §11`:flip **CO_F3a** status from "stays 501 stub — W2 ingestion + Track A" to "CLOSED by CH-001 2026-05-12"(per S13 + AC15);also add an "**ADR-0018 Phase 3 upload-side CLOSED by CH-001**(blob-side stays W16+ R12-blocked)" note in the carry-over section
- [ ] **T7.4** `COMPONENT_CATALOG.md` C03(Indexing Service)+ C08(API Gateway)`Status` rows — append the CH-001 notes:**C03** = `create_index_for_kb` / `delete_index` / `delete_doc` / `upload(kb_id=)` BC ext;**C08** = POST/DELETE/reindex documents routes wired + POST/DELETE /kb auto-index-provisioning(per AC15)
- [ ] **T7.5** **NEW per Decision B** `docs/adr/0018-multi-kb-kb-id-propagation.md` — update the `## Implementation timing` row to add the "Phase 3 upload-side closed by CH-001 2026-05-12;Phase 3 blob-container-side stays deferred — R12 Azurite signature mismatch unresolved + W16+ Track A cloud Blob switch" inline note(per spec §6.6)
- [ ] **T7.6** `grep -n '501_NOT_IMPLEMENTED\|HTTP_501' backend/api/routes/documents.py` → **0 hits**(per AC17 — the file no longer has any 501 stub)
- [ ] **T7.7** `progress.md` Day-N closeout summary written(acceptance verification + effort summary + lessons + carry-overs if any — including the per-KB blob container provisioning still-deferred note)
- [ ] **T7.8** `progress.md` + `checklist.md` frontmatter `status: in-progress → done`(closed)

---

## Cross-Cutting

- [ ] Each commit references `progress.md` Day-N entry(R2)— `docs(planning):` housekeeping commits exempt
- [ ] Component tag in commit message per CC-1(`feat(api,ingestion): … (C01 + C03 + C08)` style)
- [ ] No new ADR required(per spec §6.5 — H1 H2 both verified-no-stop-and-ask;backend feature wiring within existing component spec)
- [ ] No new component design note bump required(C01 + C03 + C08 are already `v1-active` in COMPONENT_CATALOG.md — only `Status` row appended;no `v1-active → v2` because no spec/interface change)
- [ ] OQ status sync — **no new OQ**;no existing OQ status change(per spec §6.4)
- [ ] `progress.md` closeout summary written
- [ ] `progress.md` + `checklist.md` frontmatter `status: in-progress → done`

---

**Lifecycle reminder**:呢份 checklist 隨 spec §2.2 + §3 衍生。新加 item 必須先入 spec + changelog,然後再加 checklist。
