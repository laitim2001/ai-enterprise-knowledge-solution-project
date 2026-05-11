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

- [ ] **T1.1** Read `backend/api/server.py` lifespan in full(`app.state.retrieval_engine` setup);verify whether `RetrievalEngine` already holds an embedder we can reuse,or whether we need a separate `app.state.ingestion_orchestrator` + `app.state.index_populator`
- [ ] **T1.2** Read `backend/indexing/populate.py` `IndexPopulator` full API — confirm `upload(chunks)` signature + look for a `delete_doc(kb_id, doc_id)` method;if absent, add it(delete-by-filter `kb_id eq X and doc_id eq Y` via Azure AI Search Index API);**this might be the only new code outside `documents.py`**
- [ ] **T1.3** Read `backend/kb_management/*` `KBService` API — confirm methods for `total_documents` / `total_chunks` / `storage_size_mb` / `last_indexed_at` / `failed_documents` counter sync;if missing, add(or document the gap and defer to a separate Change)
- [ ] **T1.4** Decide Approach A vs B per spec §6.2(lifespan-init populator vs per-request)— commit to A unless the embedder isn't safely shareable
- [ ] **T1.5** Wire `app.state.ingestion_orchestrator` + `app.state.index_populator`(+ helper `_ingestion_or_503(request)` next to `_engine_or_503` already in `documents.py`) — `mypy --strict` clean

## Phase 1.5 — Multi-KB index provisioning(S14-S20 + AC18-AC22)— Decision B = (β)

- [ ] **T1.5.1** Read `backend/indexing/schema.json` — confirm the canonical EKP chunk index schema(fields / dimensions / HNSW config / vector field name);verify it's the same schema that `ekp-kb-drive-v1` was provisioned with at W2 D1(`scripts/create_index.py` reference)
- [ ] **T1.5.2** **NEW** `IndexPopulator.create_index_for_kb(self, kb_id: str) -> None`(S14)— load `schema.json` once at class-init or method-call;POST `/indexes/{name}?api-version=2024-07-01` with `{"name": kb_id_to_index_name(kb_id), **schema}`(over-write the `"name"` field);raise `httpx.HTTPStatusError` on 4xx/5xx;structlog `index_created` on success
- [ ] **T1.5.3** **NEW** `IndexPopulator.delete_index(self, kb_id: str) -> bool`(S15)— DELETE `/indexes/{name}?api-version=2024-07-01`;return `True` on 204, `False` on 404, raise on other 4xx/5xx;structlog `index_deleted` / `index_already_gone`
- [ ] **T1.5.4** **NEW** `IndexPopulator.delete_doc(self, kb_id: str, doc_id: str) -> int`(S3 / extends Phase 3)— query `/indexes/{name}/docs/search` for chunk_ids matching `kb_id eq X and doc_id eq Y`,then batch-POST `/docs/index` with `@search.action: "delete"` per chunk_id;return count deleted;same `kb_id_to_index_name(kb_id)` resolution
- [ ] **T1.5.5** **Signature extension** `IndexPopulator.upload(self, records, action="mergeOrUpload", kb_id: str | None = None)`(S16, BC-preserving)— when `kb_id is not None` → `index_name = kb_id_to_index_name(kb_id, legacy_default_index=self.index_name)`;when None → `self.index_name`(W2 caller BC);pass through to `_upload_batch` via `self._batch_index_name`(refactor `_upload_batch` to accept the resolved index name)
- [ ] **T1.5.6** **`POST /kb`** wiring(S17)— in `routes/kb.py:23-31`,after `service.create(payload)` success:
   1. Call `_populator_or_503(request)`(new helper, same shape as `_engine_or_503`)
   2. `try: populator.create_index_for_kb(payload.kb_id)`
   3. `except Exception as exc:` → log + `try: await service.delete(payload.kb_id)` rollback + raise `HTTPException(502, …)` with `code: "index.create_failed"`,Azure error in `actionable_hint`
   4. `except` in rollback → log `storage_rollback_failed` + STILL raise the 502(orphan storage record possible — documented in route docstring per R10)
- [ ] **T1.5.7** **`DELETE /kb`** wiring(S18)— in `routes/kb.py:46-71`,after `service.delete(kb_id)` success:
   1. Call `_populator_or_503(request)`
   2. `dropped = await populator.delete_index(kb_id)`
   3. If `dropped is False` → structlog.warning `index_already_gone, kb_id={kb_id}`(fail-soft — common for pre-CH-001 KBs)
   4. If `dropped is True` → structlog.info `index_deleted`
   5. Azure 5xx during delete → raise `HTTPException(502, code: "index.delete_failed", …)` — but storage record is already gone(forward-only;document in route docstring)
- [ ] **T1.5.8** Drop the "Track A W17+" deferral comment block in `routes/kb.py` DELETE docstring(lines ~50-63)+ replace with a **CH-001 closure note + ADR-0018 reference**(S19);same for any inline TODO comments in the related code paths
- [ ] **T1.5.9** ADR-0018 `## Implementation timing` row update — add inline note "Phase 3 upload-side closed by CH-001 2026-05-12;blob-container-side stays W16+ Track A R12-blocked"(per §6.6)
- [ ] **T1.5.10** Verify `mypy --strict` + `ruff check` clean on the updated `indexing/populate.py` + `routes/kb.py`

## Phase 2 — `POST /kb/{kb_id}/documents`(S2 + AC1-AC7, AC10)

- [ ] **T2.1** Replace the 501 stub at `documents.py:72-82` — accept `UploadFile`,stream to `tempfile.NamedTemporaryFile(delete=False, suffix=<ext>)`(per spec R2 — no `await file.read()` whole into memory)
- [ ] **T2.2** doc_id = slugify(filename stem) → regex `[a-z0-9-]+`(per S5);check kb_id with `_verify_kb_or_404`(per S6;already in the file);check duplicate doc_id within the kb via existing `RetrievalEngine.list_documents(kb_id)` aggregation;return **409** `code: "document.duplicate"` if dup
- [ ] **T2.3** Call `select_parser(Path)` from `backend/ingestion/parsers/__init__.py`;catch its `ValueError` for unsupported extensions → **422** `code: "validation.unsupported_format"`(per AC3)
- [ ] **T2.4** Call `IngestionOrchestrator.ingest(source, kb_id, doc_id, source_url=f"upload://{filename}")` → `IngestionResult`;branch on `result.failure`:`stage="parse"` → **502** `code: "ingestion.parse_failed"`;`stage="embed"` → **502** `code: "ingestion.embed_failed"`(per AC6)
- [ ] **T2.5** Call `IndexPopulator.upload(result.chunks, kb_id=kb_id)`(per T1.5.5 — pass `kb_id` to target the per-KB index `ekp-kb-{kb_id}-v1`,NOT the legacy `ekp-kb-drive-v1`)→ `IndexUploadResult`;if `upload_result.failed > 0` → **502** `code: "ingestion.index_failed"` + the count;else proceed
- [ ] **T2.6** Update KB counters via `KBService`(per S7 + AC10): `total_documents += 1`、`total_chunks += len(result.chunks)`、`last_indexed_at = now`、`storage_size_mb += file_size_mb`;失敗就 logged but non-fatal(counter drift is recoverable per spec R7)
- [ ] **T2.7** Return **200 or 202** with `{doc_id, status: "indexed", chunks_emitted, images_uploaded, images_deduped}` per AC1
- [ ] **T2.8** `finally:` clause unlinks the tempfile path(per S9);verify no leak on parse/embed/index failure paths
- [ ] **T2.9** Error envelope helper — if not already in `backend/api/errors.py` or similar, add a small `make_api_error(code, message, hint, status)` to keep the 5+ error returns consistent
- [ ] **T2.10** `_engine_or_503(request)`-style check for Azure cred — if `app.state.ingestion_orchestrator is None` or its embedder/populator is None → **503** `code: "azure.config_missing"`(per AC5)

## Phase 3 — `DELETE /kb/{kb_id}/documents/{doc_id}`(S3 + AC8)

- [ ] **T3.1** Replace the 501 stub at `documents.py:85-92` — verify kb_id (`_verify_kb_or_404`);call `IndexPopulator.delete_doc(kb_id, doc_id)` (added in T1.5.4) → returns the count deleted
- [ ] **T3.2** If `count == 0` → **404** `code: "document.not_found"`(per AC8 — clean idempotency story:DELETE on missing = 404, not 204)
- [ ] **T3.3** If Azure delete errors → **502** `code: "index.delete_failed"`(per AC8)
- [ ] **T3.4** Update KB counters via `KBService` — `total_documents -= 1`、`total_chunks -= count`、`last_indexed_at = now`;non-fatal on failure(same as T2.6)
- [ ] **T3.5** Return **204** No Content per AC8(success path)

## Phase 4 — `POST /kb/{kb_id}/documents/{doc_id}/reindex`(S4 + AC9 — Decision A = (ii) replace-in-place)

- [ ] **T4.1** Replace the 501 stub at `documents.py:95-102` — change the signature to accept `UploadFile`(same as POST upload);if missing → **422** `code: "validation.file_required"`(per AC9.2)
- [ ] **T4.2** Verify kb_id + doc_id both exist(kb_id via `_verify_kb_or_404`,doc_id via `RetrievalEngine.list_documents(kb_id)` lookup)→ **404** `code: "document.not_found"` if doc_id missing
- [ ] **T4.3** Slugify uploaded-file stem;if `!= doc_id` → **422** `code: "reindex.doc_id_mismatch"`(UX safety per spec §2.3 + AC9 ── 防呆「上錯 file」)
- [ ] **T4.4** Call `IndexPopulator.delete_doc(kb_id, doc_id)`(reuse from T3)— records the deleted count for counter accounting
- [ ] **T4.5** Run the same ingest path as POST(tempfile + `select_parser` + `IngestionOrchestrator.ingest` + `IndexPopulator.upload`)under the **same** `doc_id`
- [ ] **T4.6** If mid-pipeline fails (after delete, before re-ingest succeeds) → **502** `code: "reindex.partial_failure"` + the FailureRecord;the KB is now in a deleted-but-not-re-ingested state(observable = "doc gone");actionable_hint:"retry via POST /kb/{kb_id}/documents with the same file"(per AC9.3)
- [ ] **T4.7** Update KB counters via `KBService` — net is `total_chunks` from delete-count → new emit count;`last_indexed_at = now`;`total_documents` unchanged(same doc_id, just re-indexed)
- [ ] **T4.8** Return **202** with `{doc_id, status: "reindexed", chunks_emitted, images_uploaded, images_deduped}` per AC9.1
- [ ] **T4.9** Code dedup — if T2 and T4 share enough body, extract a `_run_ingest_pipeline(kb_id, doc_id, upload_file, source_url) → IngestionResponse | ApiError` helper to keep both routes thin(Karpathy §1.2 — only if it's clearly cleaner, not for the sake of it)

## Phase 5 — Tests(S10 + AC11-AC12)

- [ ] **T5.1** NEW `backend/tests/api/test_documents_route.py` — FastAPI `TestClient` + monkeypatched `IngestionOrchestrator.ingest` / `IndexPopulator.upload` / `IndexPopulator.delete_doc`(real Azure calls = smoke-script territory, not unit tests)
- [ ] **T5.2** Test:AC1 — POST `.docx` happy path → 200/202 + the response shape
- [ ] **T5.3** Test:AC2 — POST `.pdf` + `.pptx` happy paths(monkeypatch `select_parser` to return the same mock parser)
- [ ] **T5.4** Test:AC3 — POST `.txt` → 422 `validation.unsupported_format`
- [ ] **T5.5** Test:AC4 — POST to unknown kb_id → 404 `kb.not_found`
- [ ] **T5.6** Test:AC5 — `app.state.ingestion_orchestrator is None` → 503 `azure.config_missing`
- [ ] **T5.7** Test:AC6 — monkeypatch orchestrator to return `FailureRecord(stage="parse")` → 502 `ingestion.parse_failed`;same for `stage="embed"`;index failure → 502 `ingestion.index_failed`
- [ ] **T5.8** Test:AC7 — POST with a doc_id that already exists in the KB → 409 `document.duplicate`
- [ ] **T5.9** Test:AC8 — DELETE happy path → 204;DELETE on missing doc_id → 404 `document.not_found`;DELETE on Azure error → 502 `index.delete_failed`
- [ ] **T5.10** Test:AC9.1 — reindex happy path → 202 + the response shape + verify the orchestrator + populator + `delete_doc` got called in the right order
- [ ] **T5.11** Test:AC9.2 — reindex missing file → 422 `validation.file_required`
- [ ] **T5.12** Test:AC9.3 — reindex mid-pipeline failure (orchestrator returns FailureRecord AFTER delete_doc was called) → 502 `reindex.partial_failure`;reindex with mismatched file stem → 422 `reindex.doc_id_mismatch`
- [ ] **T5.13** Test:AC10 — KB counters update after successful upload (mock `KBService` to capture the calls)
- [ ] **T5.14** **NEW per Decision B** Test:AC18 — `POST /kb` happy path → 201 + `populator.create_index_for_kb(kb_id)` is called(monkeypatch + assert call args);no rollback called
- [ ] **T5.15** **NEW per Decision B** Test:AC19 — `POST /kb` when `create_index_for_kb` raises → 502 `index.create_failed` + `service.delete(kb_id)` was called(rollback verified);and if rollback also fails → still 502 + `storage_rollback_failed` log
- [ ] **T5.16** **NEW per Decision B** Test:AC20 — `DELETE /kb` happy path → 204 + `populator.delete_index(kb_id)` called + returns `True` + `index_deleted` log
- [ ] **T5.17** **NEW per Decision B** Test:AC21 — `DELETE /kb` when `delete_index` returns `False`(index already gone) → still 204(fail-soft)+ `index_already_gone` log
- [ ] **T5.18** **NEW per Decision B** Test:AC22 — POST /kb + POST /kb/{kb_id}/documents → `populator.upload` called with `kb_id=<kb_id>`(not `None`)— assert via monkeypatch capture
- [ ] **T5.19** **NEW per Decision B** Test:`IndexPopulator.create_index_for_kb` + `delete_index` unit tests with monkeypatched httpx client(may live in `backend/tests/test_index_populator.py` if it doesn't exist yet,or extend an existing file)
- [ ] **T5.20** `pytest backend/tests/api/test_documents_route.py` + `pytest backend/tests/test_index_populator.py`(if added)→ all pass
- [ ] **T5.21** `pytest backend/tests/test_orchestrator.py` + `backend/tests/api/test_*` → no regression(per AC12)
- [ ] **T5.22** `pnpm test:unit` → still 4 files / 13 tests pass(no frontend change expected, per AC12)

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
