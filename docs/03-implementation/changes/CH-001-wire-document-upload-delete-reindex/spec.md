---
change_id: CH-001
title: "Wire document upload + delete + reindex routes + multi-KB Azure AI Search index provisioning on POST /kb / DELETE /kb (close CO_F3a + ADR-0018 Phase 3 upload-side; reindex = (ii) replace-in-place per Decision A; multi-KB scope per Decision B)"
status: approved
created: 2026-05-11
approved: 2026-05-11
target_completion: 2026-05-12
affects_components: [C01, C02, C03, C08]    # C01 Ingestion (orchestrator + parsers) + C02 KB Manager (counter updates + POST/DELETE /kb index provisioning hooks) + C03 Indexing (push/delete in Azure AI Search + create_index_for_kb + delete_index) + C08 API Gateway (the 3 document routes + POST /kb + DELETE /kb additions)
spec_refs:
  - architecture.md v6 §3.3              # Ingestion (parse → chunk → embed → push)
  - architecture.md v6 §3.4              # Index schema (chunk_id / kb_id / doc_id keys for delete-by-filter) + Multi-KB Architecture
  - architecture.md v6 §3.5              # ChunkRecord schema (the orchestrator's emit shape)
  - architecture.md v6 §4.4              # API endpoints (#5 POST /kb + #7 DELETE /kb + #9-#12 documents routes)
  - components/C01-ingestion.md          # IngestionOrchestrator pipeline diagram + atomic-per-doc semantics
  - ADR-0005                             # Multi-KB architecture Day 1 (index name + blob container + chunk_id format)
  - ADR-0018                             # Multi-KB kb_id propagation (Phase 3 upload-side closed by THIS Change)
  - ADR-0019                             # PDF parser (already implemented; select_parser dispatch ready)
  - session-start.md §11 CO_F3a          # The carry-over this Change closes
  - audit-W15-d5-vs-spec.md §CC-1        # Multi-KB invariant gap that triggered ADR-0018
---

# CH-001 — Wire document upload + delete + reindex routes + multi-KB index provisioning (close CO_F3a + ADR-0018 Phase 3)

> **Spec version**:1.2(approved 2026-05-11 — Decision A = (ii) replace-in-place reindex;Decision B = (β) expand scope to include multi-KB index provisioning on POST /kb + DELETE /kb)
> **Owner**:Chris(approver)+ AI(implementation)
> **Approved by**:Chris(2026-05-11)

---

## 1. Context (Why)

### 1.1 Trigger

2026-05-11 dev test session — user attempted to create a new KB via `/kb/new` Pipeline wizard (Step 3 Execute) with `RAPO_Cowork_Pilot_Kickoff_Plan.docx` and hit:

```
POST http://localhost:3001/api/backend/kb/copilot-cowork-document-1/documents 501 (Not Implemented)
{"error":{"code":"internal.server_error",
          "message":"W1-W2 implementation per architecture.md §3.3 (multi-format ingestion)",
          "actionable_hint":"Something went wrong — retry, and report if it persists."}}
```

`POST /kb` (Create KB) succeeded — the failure was at the second step, `POST /kb/{kb_id}/documents` (Upload + Ingest). Screenshot at `Screenshot 2026-05-11 102613.png`.

### 1.2 Diagnosis

The route at `backend/api/routes/documents.py:72-82` is a **hardcoded 501 stub**:

```python
@router.post("/kb/{kb_id}/documents", status_code=status.HTTP_202_ACCEPTED)
async def upload_document(kb_id: str, file: UploadFile) -> dict:
    _ = kb_id, file
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="W1-W2 implementation per architecture.md §3.3 (multi-format ingestion)",
    )
```

So are `DELETE /kb/{kb_id}/documents/{doc_id}` (lines 85-92) and `POST .../{doc_id}/reindex` (lines 95-102). The file's top docstring confirms (W16 F5.1.1 closure note):

> Other endpoints remain 501 stub pending W2 multi-format ingestion + re-index W17+ scope (out of W16 F5 batch per Path A scope decision).

Per `docs/12-ai-assistant/01-prompts/01-session-start.md §11`, this is the **CO_F3a** carry-over:

> **CO_F3a/b/c**(→ KB doc-listing wired W16 F5 + frontend W17 F4.1;**per-doc upload/reindex/delete stays 501 stub — W2 ingestion + Track A**)

### 1.3 The actual W2 machinery already exists

`backend/ingestion/` is fully implemented (per W2 phase closure 2026-05-04 + ADR-0019 PDF parser):

- `parsers/` — `DoclingDocxParser`, `DoclingPdfParser`, `PptxParser`, with **`select_parser(Path)` factory** that dispatches by extension
- `chunker/layout_aware.py` — `LayoutAwareChunker`
- `screenshots/extractor.py` + `uploader.py` — extraction + Azurite blob upload (uploader currently passed `None` per R12 Azurite signature mismatch)
- `embedding/azure_openai_embedder.py` — `AzureOpenAIEmbedder` (async context manager)
- `orchestrator.py` — `IngestionOrchestrator(parser, chunker, embedder, uploader=None).ingest(source: Path, kb_id, doc_id, source_url) → IngestionResult(chunks: list[ChunkRecord], failure: FailureRecord | None, ...)`
- `indexing/populate.py` — `IndexPopulator.upload(chunks) → UploadResult(succeeded, failed)` for Azure AI Search

`scripts/run_populate_sanity.py` is the canonical reference call site (W2 Gate 1 R@5=0.9722 LIVE eval was driven by this script). The HTTP route just needs to do the same things for a single uploaded file.

### 1.4 Why now / why a Change task

- W18-app-shell-ia closed 2026-05-11. No active phase. Rolling-JIT — W19+ not pre-created.
- This is **not a Phase deliverable** (no active phase plan covers it). It is **not a Bug-fix** (no regression — the spec always said this was pending). It **is** a behavior change (501 stub → real implementation) → **Change classification per PROCESS.md §1**.
- "Track A" in CO_F3a's deferral label was over-broad — Track A blocks **prod deploy** (`.env.production`, prod Azure subscription, Cohere Marketplace billing, R-B1 closure), but the dev-time wiring uses the dev Azure cred that has been in `.env` since W2. So this is unblocked **now**.
- The Pipeline wizard is the user's primary path for adding documents. Keeping it 501 makes the platform un-usable for KB onboarding even in dev — closing this is gating the user's pre-Beta smoke + any local-dev iteration.

### 1.5 Discovered scope gap — multi-KB Azure AI Search index provisioning(post-v1.0 draft, 2026-05-11)

While reading the backend to draft this spec(`backend/api/routes/kb.py:22-31` + `backend/storage/kb_naming.py` + ADR-0018),I surfaced a **hard scope dependency** on the user's actual workflow:

- **ADR-0018**(Accepted 2026-05-09, multi-KB `kb_id` propagation):per-KB Azure AI Search index = `ekp-kb-{kb_id}-v1`(`drive_user_manuals` is the legacy alias mapping to the deployed `ekp-kb-drive-v1`)
- **`POST /kb`(`routes/kb.py:22-31`)only creates the KB storage record**(in-memory / Postgres per ADR-0023). It does **NOT** create the corresponding Azure AI Search index. The `ekp-kb-drive-v1` index that exists was provisioned **once, manually**, at W2 D1 via `scripts/create_index.py` for the single legacy KB.
- **`HybridSearcher.list_documents` already dynamic** uses `kb_id_to_index_name(kb_id)`(part of ADR-0018 Phase 3 already landed for the search-side);**but `IndexPopulator.upload` still hardcodes** `self.index_name`(=`ekp-kb-drive-v1`)
- **`DELETE /kb`(`routes/kb.py:46-71`)`docstring`** explicitly defers the Azure index drop to "Track A W17+"(per W16 F5.3 Decision B.1)— same deferral cause(over-broad "needs admin-key" reading)

**Net consequence for the user's workflow**:the screenshot showed the user creating a **new** KB(`copilot-cowork-document-1`)+ trying to upload. Even if I close the 3 document-route 501s, the **upload still fails** — because there is no `ekp-kb-copilot-cowork-document-1-v1` index in Azure → 502 with a different error message. CH-001 would only have "renamed the wall".

→ Decision B = (β) **expand scope** to include multi-KB index provisioning(per user, 2026-05-11): close ADR-0018 Phase 3 upload-side together with CO_F3a. Rationale per the §7 changelog v1.1 → v1.2 row.

---

## 2. Scope (What)

### 2.1 Behavior Change

**A. Document routes — `backend/api/routes/documents.py` lines 72-102**:

**Before** (3 hardcoded 501 stubs):
- `POST /kb/{kb_id}/documents` → **501** `"W1-W2 implementation per architecture.md §3.3 (multi-format ingestion)"`
- `DELETE /kb/{kb_id}/documents/{doc_id}` → **501** `"W2 implementation per architecture.md §3.4"`
- `POST /kb/{kb_id}/documents/{doc_id}/reindex` → **501** `"W2 implementation per architecture.md §3.4"`

**After**:
- `POST /kb/{kb_id}/documents` → **200/202** `{doc_id, status:"indexed", chunks_emitted, images_uploaded, images_deduped}` after running parse → chunk → embed → push to **the per-KB Azure AI Search index** `ekp-kb-{kb_id}-v1`(via `kb_id_to_index_name(kb_id)`); **502** with `{code: "ingestion.{stage}_failed", message, actionable_hint}` envelope on parse/embed/upload failure; **404** if `kb_id` not found; **422** if file extension unsupported (handled by `select_parser`'s `ValueError`); **503** if Azure cred missing (`_engine_or_503` pattern already in the file)
- `DELETE /kb/{kb_id}/documents/{doc_id}` → **204** after deleting all chunks where `kb_id eq X and doc_id eq Y` from the per-KB Azure AI Search index; **404** if no chunks match (or if kb_id not found); **502** if Azure delete fails; **503** if Azure cred missing
- `POST /kb/{kb_id}/documents/{doc_id}/reindex` → see §2.3 **Decision A = (ii) replace-in-place** (multipart `file=<file>` body → delete existing chunks for `doc_id` → ingest the new file under the same `doc_id` → **202** with the same response shape as POST)

**B. KB routes — `backend/api/routes/kb.py` lines 22-31 + 46-71**(scope expansion per Decision B = (β), 2026-05-11):

**Before**:
- `POST /kb` → **201** + the KB storage record(in-memory / Postgres);**no Azure index provisioned** — the legacy `ekp-kb-drive-v1` is the only existing index(manual W2 D1 provision via `scripts/create_index.py`)
- `DELETE /kb` → **204** + storage record removed;**Azure index NOT dropped**(deferred to "Track A W17+" per W16 F5.3 Decision B.1)

**After**:
- `POST /kb` → **201** + storage record + **the per-KB Azure AI Search index `ekp-kb-{kb_id}-v1` is now created** via `IndexPopulator.create_index_for_kb(kb_id)` using the schema from `backend/indexing/schema.json`(the canonical EKP chunk index schema since W2);if Azure index-create fails → storage record rolled back via `service.delete(kb_id)` + **502** `code: "index.create_failed"` with the Azure error message
- `DELETE /kb` → **204** + storage record AND the per-KB Azure index dropped via `IndexPopulator.delete_index(kb_id)`;**fail-soft** on Azure 404(index never existed — common for KBs created before this Change lands, or after a partial create-rollback);**logs a warning** but the response is still 204
- **`IndexPopulator.upload(records, kb_id=...)`** — signature extended with an **optional** `kb_id` parameter that overrides `self.index_name` via `kb_id_to_index_name(kb_id)`;omitted `kb_id` preserves the v1.1 backward-compat behaviour(targets `self.index_name` = `ekp-kb-drive-v1` by default — used by `scripts/run_populate_sanity.py` + the W2 tests, none of which need a change)

### 2.2 In Scope

| # | Item | File(s) |
|---|---|---|
| S1 | Add `app.state.ingestion` lifespan service (or reuse `RetrievalEngine`'s embedder + spin up `IndexPopulator`) — see §6 design discussion | `backend/api/server.py` |
| S2 | Wire `POST /kb/{kb_id}/documents` end-to-end (`UploadFile` → `tempfile.NamedTemporaryFile` with the right ext → `select_parser` → `IngestionOrchestrator.ingest` → `IndexPopulator.upload`) | `backend/api/routes/documents.py:72-82` |
| S3 | Wire `DELETE /kb/{kb_id}/documents/{doc_id}` (Azure AI Search index `delete-by-filter` on `kb_id eq X and doc_id eq Y`) | `backend/api/routes/documents.py:85-92` + maybe a new method on `IndexPopulator` (e.g. `delete_doc(kb_id, doc_id)`) |
| S4 | Wire `POST .../{doc_id}/reindex` per the §2.3 decision below | `backend/api/routes/documents.py:95-102` |
| S5 | doc_id derivation:`filename_stem`(slugified to `[a-z0-9-]+`)— traceability over UUID;reject duplicate doc_id within the same kb_id with **409** (`code: "document.duplicate"`,actionable_hint:「DELETE existing first or change the filename」) | route |
| S6 | KB existence check (`_verify_kb_or_404` already in the file) | route |
| S7 | Counter sync — after a successful ingest, update the KB's `total_documents` / `total_chunks` / `storage_size_mb` / `last_indexed_at` / `failed_documents` via `KBService` | `backend/kb_management/*` + route |
| S8 | Error envelope — match the existing `ApiError` `{code, message, actionable_hint}` convention; use `ingestion.parse_failed` / `ingestion.embed_failed` / `ingestion.index_failed` / `validation.unsupported_format` / `document.duplicate` / `azure.config_missing` codes | route + maybe a helper |
| S9 | Tempfile cleanup — use `tempfile.NamedTemporaryFile(delete=False)` + `finally: os.unlink(path)` so parser gets a real path and we don't leak | route |
| S10 | Backend tests — `backend/tests/api/test_documents_route.py` (new) with FastAPI `TestClient` + monkeypatched orchestrator + index populator (real Azure-call tests stay smoke-script territory per existing convention) | `backend/tests/` |
| S11 | Docstring update — the file's top docstring + each route's docstring, removing the 501-stub note + adding the CH-001 closure reference | route file |
| S12 | Frontend response-shape verify — `frontend/lib/api/kb.ts` `uploadDoc` returns `Promise<{ doc_id: string }>`;ensure backend `POST` response includes `doc_id` (it will; richer fields like `chunks_emitted` are additive and ignored by the wizard, which doesn't display them) | _verify only, no expected change_ |
| S13 | Documentation updates — session-start.md §11 (CO_F3a status flip + ADR-0018 Phase 3 upload-side closed note), W2 retro carry-over note if applicable, COMPONENT_CATALOG.md C08 stub-cascade row + C03 indexing note, ADR-0018 "Implementation timing" row updated (Phase 3 upload-side closed by CH-001 2026-05-12) | `docs/12-ai-assistant/01-prompts/01-session-start.md` + `docs/02-architecture/COMPONENT_CATALOG.md` + `docs/adr/0018-multi-kb-kb-id-propagation.md` |
| **S14** | **NEW** `IndexPopulator.create_index_for_kb(kb_id) → None` — POST `/indexes/{name}?api-version=2024-07-01` with the schema loaded from `backend/indexing/schema.json`(the canonical EKP chunk index schema since W2 — fields/dimensions/HNSW params);raise on 4xx/5xx;use `kb_id_to_index_name(kb_id)` for the name | `backend/indexing/populate.py` |
| **S15** | **NEW** `IndexPopulator.delete_index(kb_id) → bool`(returns `True` if dropped, `False` if 404)— DELETE `/indexes/{name}?api-version=2024-07-01`;fail-soft on 404(returns False);raise on other errors | `backend/indexing/populate.py` |
| **S16** | **Signature extension** `IndexPopulator.upload(records, action="mergeOrUpload", kb_id=None)`(BC-preserving)— when `kb_id` is provided, resolve `index_name = kb_id_to_index_name(kb_id, legacy_default_index=self.index_name)` and target that index;when `kb_id` is None,fall back to `self.index_name`(preserves W2-era callers like `scripts/run_populate_sanity.py`);same for any new `delete_doc(kb_id, doc_id)`(from S3)— always uses `kb_id_to_index_name` | `backend/indexing/populate.py` |
| **S17** | **`POST /kb`** — after the existing `service.create(payload)` succeeds(`routes/kb.py:22-31`),call `populator.create_index_for_kb(payload.kb_id)`;on Azure failure → `service.delete(payload.kb_id)` to roll back the storage record + raise `HTTPException(502, code="index.create_failed", actionable_hint="Check kb_id matches Azure index-name rules: 2-128 chars, lowercase a-z + 0-9 + dashes, no leading/trailing dash, no consecutive dashes.")`;**rollback failure is logged but the 502 is still raised**(orphan storage record possible — call out in R10) | `backend/api/routes/kb.py` |
| **S18** | **`DELETE /kb`** — after the existing `service.delete(kb_id)` succeeds(`routes/kb.py:46-71`),call `populator.delete_index(kb_id)`;**fail-soft on `False`**(index never existed — common for legacy KBs / partial-create-rollback)+ structlog.warning;raise 502 `code: "index.delete_failed"` on Azure 5xx | `backend/api/routes/kb.py` |
| **S19** | Drop the "Track A W17+" deferral comment block in `routes/kb.py` DELETE docstring(lines ~50-63)+ replace with a CH-001 closure note + the ADR-0018 reference | `backend/api/routes/kb.py` |
| **S20** | Backend tests — extend the CH-001 test file with tests for `POST /kb` index-create-success + index-create-fail-with-rollback + `DELETE /kb` index-drop-success + index-already-gone(fail-soft);+ `IndexPopulator.create_index_for_kb` + `delete_index` unit tests with monkeypatched httpx client | `backend/tests/api/test_documents_route.py` + maybe `backend/tests/test_index_populator.py` |

### 2.3 Decision A — reindex semantics = (ii) replace-in-place(**APPROVED 2026-05-11**)

```
POST /kb/{kb_id}/documents/{doc_id}/reindex
Content-Type: multipart/form-data
Body: file=<file>

→ 1. Verify kb_id exists + doc_id exists in the KB (via Azure AI Search aggregate) — 404 if either missing
→ 2. Verify the uploaded file's slugified-stem == doc_id (UX safety check — surfaces "you uploaded the wrong file" before destructive delete) — 422 with `code: "reindex.doc_id_mismatch"` if mismatched
→ 3. Delete existing chunks where kb_id eq X and doc_id eq Y (same Azure AI Search delete-by-filter as the DELETE route)
→ 4. Ingest the new file under the SAME doc_id (same orchestrator → populator path as POST)
→ 5. Atomically respond 202 with `{doc_id, status: "reindexed", chunks_emitted, images_uploaded, images_deduped}`

→ Failure mid-pipeline (after delete, before re-ingest succeeds) → 502 with `code: "reindex.partial_failure"` + the FailureRecord;the KB ends up in a deleted-but-not-re-ingested state, which is the same observable outcome as a successful DELETE → user can recover via POST. This is documented in the route docstring + the actionable_hint.
```

**Rationale**:
- Real semantics (atomic replace), one API call (not "DELETE then POST")
- Closes CO_F3a properly (3 routes all do real work, not just route-renamed walls)
- Honest about the source-store gap (the user provides the source — we don't pretend to remember it)
- 90% code reuse with POST + the existing DELETE path (small DRY win)
- The doc_id-match safety check (step 2) catches "user uploaded the wrong file" → no silent destructive replace

**Alternatives considered + rejected**:
- **(i)** 422 + hint("DELETE then POST")── technical-but-not-real close of CO_F3a;rejected per the user's pick (b)「真做晒 POST + DELETE + reindex」
- **(iii)** full source-doc store(Azurite container `kb-{kb_id}-sources/`)── genuinely Tier 2 feature(R12 Azurite signature mismatch still open + prod Blob storage cost + scope creep beyond "close 501 stubs");rejected as out of CH-001 scope, may revisit Tier 2 if the "user shouldn't need to keep the original" UX matters at scale

### 2.4 Out of Scope (explicit — won't change)

- New backend features beyond closing the 501 stubs + ADR-0018 Phase 3 upload-side (no source-doc store unless §2.3 = (iii); no chunk-level inspection; no async/background ingestion — initial = synchronous, response after full ingest finishes)
- Frontend Pipeline wizard redesign (the wizard already handles success / failure envelopes — verify-only)
- R12 Azurite Blob fix for screenshot upload (uploader stays `None` per the existing `scripts/run_populate_sanity.py` pattern — text retrieval works, citation thumbnails will be empty until R12 is fixed at W16+ cloud Azure Blob switch)
- ADR-0023 Postgres KB backend wiring beyond what already exists (KB counter updates use the existing `KBService` interface)
- Per-file size / MIME-strict validation beyond `select_parser`'s extension check (Tier 2 — proper file-type gate)
- Background-task / progress streaming (Tier 2 — Pipeline wizard renders a single success/fail marker, no progress bar yet)
- Multi-file upload in a single request (one file per request — the existing `UploadFile` signature)
- **Pydantic `kb_id` regex validation**(Azure index-name rules:2-128 chars, lowercase a-z + 0-9 + dashes, no leading/trailing dash, no consecutive dashes)— the Azure REST API itself rejects bad names → 502 with the Azure error message is the user-facing surface;a proper input-validation gate is a separate Change(small, follow-up — could also live in `KbCreate.kb_id` Pydantic Field constraint)
- **Per-KB Azurite blob screenshot container provisioning**(`ekp-kb-{kb_id}-screenshots` per ADR-0005)— this is the matching multi-KB Phase 3 deliverable on the blob side, but R12 Azurite signature mismatch is still open, so even the legacy `ekp-kb-drive-screenshots` is `uploader=None`-bypassed. Provisioning per-KB blob containers makes no sense until R12 is fixed → deferred to W16+ Track A cloud Blob switch(documented in S13 + ADR-0018 status update)
- **Migrating `scripts/run_populate_sanity.py` to pass `kb_id`** to `populator.upload`— optional, BC-preserving;the W2-era script targets the legacy KB and works with the default path;may revisit when re-running the script post-CH-001 to validate the new path is wired

---

## 3. Acceptance Criteria

Verifiable list:

- [ ] **AC1** — `POST /kb/{drive_user_manuals}/documents` with a `.docx` file → **200 or 202** with body `{doc_id: string, status: "indexed", chunks_emitted: int, images_uploaded: int, images_deduped: int}` after the full pipeline completes (parse → chunk → embed → Azure AI Search push); the file's chunks are visible in `GET /kb/{drive_user_manuals}/documents` afterwards
- [ ] **AC2** — Same for `.pdf` (per ADR-0019 PDF parser) and `.pptx` (W3 D5 PPT parser)
- [ ] **AC3** — Unsupported extension (`.txt`, `.zip`, …) → **422** `{code: "validation.unsupported_format", message: "<ext> not in {.docx, .pdf, .pptx}", actionable_hint: "Convert to one of the supported formats."}`
- [ ] **AC4** — Unknown `kb_id` → **404** `{code: "kb.not_found", message: "kb_id={kb_id} not registered", actionable_hint: "Create the KB via POST /kb first."}`
- [ ] **AC5** — Azure OpenAI / Azure AI Search cred missing in `.env` → **503** `{code: "azure.config_missing", message: ..., actionable_hint: "Set AZURE_OPENAI_API_KEY + AZURE_SEARCH_ADMIN_KEY in .env"}`
- [ ] **AC6** — Parser returns `parse_failed` → **502** `{code: "ingestion.parse_failed", message: <parse_error>, actionable_hint: "Check the file isn't corrupt / password-protected."}`;same shape for `ingestion.embed_failed` / `ingestion.index_failed`
- [ ] **AC7** — Duplicate `doc_id` (same KB, same filename stem already exists) → **409** `{code: "document.duplicate", message: "doc_id={doc_id} already in kb_id={kb_id}", actionable_hint: "DELETE existing first or upload with a different filename."}`
- [ ] **AC8** — `DELETE /kb/{kb_id}/documents/{doc_id}` → **204** + the chunks where `kb_id eq X and doc_id eq Y` are gone from the Azure AI Search index; **404** if no such chunks (clean idempotency story); **502** if Azure delete fails
- [ ] **AC9** — `POST /kb/{kb_id}/documents/{doc_id}/reindex` per Decision A = (ii) replace-in-place:
   - **AC9.1** multipart `file=<file>` → 1) verify `kb_id`+`doc_id` exist (404 if not) → 2) verify slugified-stem == `doc_id` (422 `code: "reindex.doc_id_mismatch"` if not) → 3) delete existing chunks where `kb_id eq X and doc_id eq Y` → 4) ingest new file under same `doc_id` → 5) **202** with `{doc_id, status: "reindexed", chunks_emitted, images_uploaded, images_deduped}` AND the old chunks are gone + the new ones are queryable via `GET /kb/{kb_id}/documents`
   - **AC9.2** Missing file part → **422** `code: "validation.file_required"`
   - **AC9.3** Mid-pipeline failure (after delete, before re-ingest succeeds) → **502** `code: "reindex.partial_failure"` + the FailureRecord (the KB is now in a deleted-but-not-re-ingested state; the actionable_hint points to "retry via POST /kb/{kb_id}/documents")
- [ ] **AC10** — After a successful upload, the KB's `total_documents` / `total_chunks` / `last_indexed_at` counters update (`GET /kb/{kb_id}` reflects the new values);failed ingests update `failed_documents`
- [ ] **AC11** — `pytest backend/tests/api/test_documents_route.py` passes (new tests covering AC1-AC10 with monkeypatched orchestrator + populator; real-Azure smoke is `scripts/run_populate_sanity.py` territory, not in CI)
- [ ] **AC12** — Existing tests still pass:`backend/tests/test_orchestrator.py`(no orchestrator change expected),`backend/tests/api/*`(no regression to GET listing / KB CRUD / auth);`pnpm test:unit` 13/13(no frontend change expected)
- [ ] **AC13** — `mypy --strict` clean(`backend/api/routes/documents.py` + `backend/api/server.py` lifespan + any new helpers);`ruff check` clean
- [ ] **AC14** — Frontend Pipeline wizard step 3 on `:3001` shows **✓ Upload + Ingest** instead of **✗ upload failed: 501** when uploading the sample `.docx` to a fresh KB(end-to-end manual smoke)
- [ ] **AC15** — Documentation updated:`session-start.md §11` flips **CO_F3a from "stays 501 stub"** to **"CLOSED by CH-001"**(per §2.2 S13)+ adds an "ADR-0018 Phase 3 upload-side closed by CH-001" note;`COMPONENT_CATALOG.md` C03 + C08 status rows updated;`docs/adr/0018-multi-kb-kb-id-propagation.md` "Implementation timing" row updated to reflect Phase 3 upload-side closed 2026-05-12(while Phase 3 blob-container-side remains W16+ Track A R12-blocked)
- [ ] **AC16** — Commit message follows Conventional Commits + tags affected components(`feat(api,ingestion)` scope + CC tag for C01/C02/C03/C08)
- [ ] **AC17** — `grep -n '501_NOT_IMPLEMENTED\|HTTP_501' backend/api/routes/documents.py` returns 0 hits after the change
- [ ] **AC18** — `POST /kb` with a new `kb_id`(e.g. `ch001-smoke-test`)→ **201** + the KB storage record + the Azure AI Search index `ekp-kb-ch001-smoke-test-v1` exists(verify via direct REST `GET /indexes/ekp-kb-ch001-smoke-test-v1?api-version=2024-07-01` → 200 with the schema body)
- [ ] **AC19** — `POST /kb` with a `kb_id` that Azure rejects(e.g. `Mixed_Case` uppercase, `--leading`, `trailing-`)→ **502** `code: "index.create_failed"` + the Azure error message in the actionable_hint;**`GET /kb/{bad_kb_id}` returns 404**(storage record rolled back per S17 + R10)
- [ ] **AC20** — `DELETE /kb` on a KB created via the new POST → **204** + the storage record is gone + the Azure index `ekp-kb-{kb_id}-v1` is dropped(verify via direct REST `GET /indexes/...` → 404)
- [ ] **AC21** — `DELETE /kb` on a legacy KB that never had an index OR a partially-rolled-back KB → **204**(fail-soft on index 404 per S18);log message indicates "index_already_gone" structlog event
- [ ] **AC22** — `POST /kb` + `POST /kb/{kb_id}/documents` → the chunks land in `ekp-kb-{kb_id}-v1` NOT the legacy `ekp-kb-drive-v1`(verify via direct REST `GET /indexes/ekp-kb-{kb_id}-v1/docs/$count` matches the `chunks_emitted` response)

---

## 4. Risks

| # | Risk | L | I | Mitigation |
|---|---|---|---|---|
| **R1** | Azure cred missing in user's `.env` → ingestion fails at embed step (502 not 501) | M | Med | Surface a **503** with actionable_hint pointing to the `.env` vars (not a 502 — explicit "config missing"); document the env var requirement in the spec + route docstring + the failure envelope's `actionable_hint`; verify the existing `_engine_or_503` pattern can be reused |
| **R2** | `UploadFile` streaming for big PDFs → memory bloat | L | Med | Stream to `tempfile.NamedTemporaryFile` in chunks (`await file.read(8192)` loop or `shutil.copyfileobj(file.file, tmp)`) — don't `await file.read()` whole into memory; Tier 1 = single doc per request, accept M risk |
| **R3** | Reindex semantics gap (§2.3 Decision A) | H | Low-Med | Surface the gap to the user before code — three honest options, no faking; my pick = (ii) replace-in-place |
| **R4** | DELETE on doc_id with chunks across multiple search-index batches → partial delete | L | Med | Use Azure AI Search `Index API delete` with the filter `kb_id eq X and doc_id eq Y` (single atomic delete-by-query); assert delete count > 0 OR fail-soft to 404 if no matches |
| **R5** | Concurrent upload of same `doc_id` → race | L | Med | Tier 1 = accept (no locking); the duplicate-doc_id 409 check happens via a list-documents pre-check (TOCTOU window exists but is small in Tier 1 single-user dev); document; future-tier idempotency key (Tier 2) |
| **R6** | Screenshot blob upload fails (R12 — Azurite SDK signature mismatch, still open) | H | Low | `uploader=None` per the existing `scripts/run_populate_sanity.py` pattern; per architecture.md §3.5 + orchestrator design, text retrieval is unaffected (citation thumbnails will be empty until R12 is fixed at W16+ cloud Azure Blob switch);call out in spec + route docstring |
| **R7** | Counter update race (KB has `total_documents` etc;multiple uploads → counters drift) | L | Low | Tier 1 = accept (the counter is derived from Azure AI Search by-doc aggregation anyway — `total_chunks` is queryable from the index; the KB-level cached counters are an optimization, not source of truth); a follow-up could derive counters from the index on `GET /kb/{kb_id}` if drift matters |
| **R8** | `IndexPopulator` lifespan — opening + closing the Azure Search REST client per request is slow | M | Low | Reuse via `app.state` lifespan-init (one populator instance for the app lifetime — same pattern as `app.state.retrieval_engine`); design in §6 |
| **R9** | Azure rejects a `kb_id` that doesn't match its index-name rules(uppercase / leading dash / consecutive dashes / > 128 chars)→ `POST /kb` 502 | M | Med | The 502 envelope's `actionable_hint` quotes the Azure rules verbatim;the storage record is rolled back per S17 so the user retries with a clean `kb_id`;a proper Pydantic `kb_id` regex is documented in §2.4 Out of Scope as a small follow-up Change |
| **R10** | **Partial-create race**:storage record created → Azure index-create fails → rollback call also fails(e.g. db connection drops) → orphan storage record with no Azure index | L | Med | Catch the rollback exception explicitly + structlog.error("storage_rollback_failed");still raise the 502 to the user with a clearer actionable_hint:「The KB may be in an inconsistent state — DELETE the kb_id manually if it reappears in GET /kb.」 A proper 2-phase-commit storage-index transaction is Tier 2;document this in the route docstring |
| **R11** | ADR-0018 status drift — CH-001 closes Phase 3 **upload-side**(POST `/kb` index-create + populator.upload kb_id-dynamic + delete_index)but leaves Phase 3 **blob-side**(per-KB `ekp-kb-{kb_id}-screenshots` container provisioning + uploader bind)still deferred. Closing ADR-0018 status `Accepted → done` would be premature | L | Low | The `docs/adr/0018-multi-kb-kb-id-propagation.md` Implementation-Timing row is updated to add a "Phase 3 upload-side closed by CH-001 2026-05-12;Phase 3 blob-side stays deferred — R12 Azurite signature mismatch unresolved + Track A cloud Blob switch W16+" note. Status stays `Accepted`(not flipped to `done`)until blob-side closes too |

---

## 5. Effort Estimate

**~6-9 hours of focused work**(v1.1 was 4-6h;Decision B = (β) adds ~2-3h for multi-KB provisioning):
- Lifespan wiring + service-instance setup: ~1h
- POST `/kb/{kb_id}/documents` handler + tempfile + parser dispatch + orchestrator + populator: ~1.5h
- DELETE `/kb/{kb_id}/documents/{doc_id}` handler + Azure AI Search delete-by-filter: ~0.5h
- Reindex `/kb/{kb_id}/documents/{doc_id}/reindex` handler per Decision A = (ii) replace-in-place: ~1h
- **(NEW per Decision B)** `IndexPopulator.create_index_for_kb` + `delete_index` + `upload(kb_id=...)` BC signature ext: ~1.5h
- **(NEW per Decision B)** `POST /kb` + `DELETE /kb` route wiring with rollback handling: ~0.5h
- **(NEW per Decision B)** ADR-0018 status update + docs hygiene: ~0.25h
- Backend tests (`test_documents_route.py` + `test_index_populator.py` extension): ~1.5-2h
- Docstring / catalog / session-start hygiene: ~0.5h
- E2E manual smoke + iterations: ~0.5h

Real-calendar collapse window:1-1.5 calendar days(was same-day);real-calendar collapse historical pattern says ~30-40% under plan estimate when momentum is clean(per W12-W18 precedent)— may finish same-day.

---

## 6. Dependencies

### 6.1 External work (already landed — verify only)
- W2 ingestion machinery — `backend/ingestion/` (orchestrator + parsers + chunker + embedder)
- W2 indexing — `backend/indexing/populate.py` (`IndexPopulator.upload`)
- ADR-0019 PDF parser — `parsers/pdf_parser.py` (`DoclingPdfParser`)
- ADR-0023 Postgres KB backend — `kb_management/` (`KBService.get` / `update` for counter sync)
- W16 F5.1.1 GET `/kb/{kb_id}/documents` — `documents.py:48-69` (the existing route, reused as the post-ingest verification surface)

### 6.2 Lifespan service wiring (design discussion — to be decided in implementation)

Two options:
- **Approach A (recommended)** ── add `app.state.ingestion_orchestrator` + `app.state.index_populator` in `backend/api/server.py` lifespan, alongside the existing `retrieval_engine` / `synthesizer` / `crag_loop`. Reuse the embedder instance if possible (`RetrievalEngine` already has one for query embedding — can we share?). One Azure REST client per app, not per request.
- **Approach B** ── spin up the embedder + populator per request inside the route handler. Simpler code but slower (Azure HTTP client warm-up per request);accept the latency for Tier 1 dev (a few hundred ms extra is fine for a manual upload).

→ I'll commit to A in implementation unless it turns out the embedder isn't safely shareable across query + ingest contexts;then B as fallback.

### 6.3 Environment
- `AZURE_OPENAI_*` + `AZURE_SEARCH_*` keys in `.env` (existing W2-era dev cred)
- Docker-compose's Azurite **doesn't need to be up** — `uploader=None` means we skip blob upload (screenshots extracted but not uploaded)
- Backend `:8000` (uvicorn) + frontend `:3001` (next dev) for the manual AC14 smoke

### 6.4 No new dependency (H2 — verified)
This Change adds zero new package — all `pip install`-able pieces (Docling, python-pptx, openai-async, azure-search-documents) are already in `pyproject.toml` since W2. **No H2 stop-and-ask.**

### 6.5 No architectural change (H1 — verified)
No `architecture.md §3 / §4` component added/removed/swapped;no vendor change. The Change *uses* the existing components per their spec(including ADR-0018 multi-KB invariant, ADR-0005 multi-KB Day 1 naming, ADR-0019 PDF parser, ADR-0023 Postgres KB backend). **No H1 stop-and-ask;no new ADR required.** Decision B = (β) scope expansion completes the **upload-side** of ADR-0018 Phase 3 ── this is **implementation of an existing accepted ADR**, not a new architectural decision.

### 6.6 ADR-0018 status touch
- ADR-0018 stays **`Accepted`**(NOT flipped to `done`)— Phase 3 has both upload-side(closed by CH-001) AND blob-container-side(per-KB `ekp-kb-{kb_id}-screenshots` provisioning, still R12-Azurite-blocked); a future CH-NNN can close blob-side when R12 is resolved at W16+ Track A cloud Blob switch
- ADR-0018 `## Implementation timing` row gets an inline `"Phase 3 upload-side closed by CH-001 2026-05-12 — POST /kb auto-creates ekp-kb-{kb_id}-v1; populator.upload accepts kb_id; DELETE /kb drops the index; documents route family wired end-to-end. Blob-container-side remains W16+ Track A R12-blocked."` note(per spec §2.2 S13 + AC15)

---

## 7. Spec Changelog (deviation log)

| Date | Change | Reason | Approver |
|---|---|---|---|
| 2026-05-11 | Initial draft | User trigger:Pipeline wizard 501 on `/kb/new` Step 3 Execute(screenshot 102613.png);classification = Change(per PROCESS.md §1 signals "modify Z" / "501 stub → real implementation");scope = (b) per user's pick(POST + DELETE + reindex 一齊做);Decision A on reindex pending user pick(i/ii/iii) | Chris(pending approval) |
| 2026-05-11 | **Decision A = (ii) replace-in-place reindex approved**;status `draft` → `approved`;§2.1 + §2.3 + §3 AC9 locked to the (ii) semantics(multipart re-upload → delete-existing-chunks → ingest-new-under-same-doc_id → atomic 202);(i) and (iii) recorded as "alternatives considered + rejected" in §2.3;spec version bumped 1.0 → 1.1;ready to derive `checklist.md` + `progress.md` and start implementation | Chris(approved 2026-05-11) |
| 2026-05-11 | **Decision B = (β) scope expansion approved** ── while reading the backend to draft Phase 1, surfaced that `POST /kb` does NOT create the per-KB Azure AI Search index(only the storage record;ADR-0018 Phase 3 upload-side was deferred to "W16+ Track A");the user's actual workflow(create `copilot-cowork-document-1` + upload)would still fail post-CH-001-v1.1 with Azure 404. User picked (β) for the rationale:(1)user's screenshot was a new-KB workflow → (α) didn't solve it;(2)ADR-0018 Phase 3 was over-deferred — Track A blocks **prod deploy**, dev `.env` has admin-key;(3)同 W16 F5.3 Decision B.1 (DELETE /kb index drop deferred) 一齊 unblock;(4)避免 CH-001/CH-002 切割成本。Spec v1.1 → v1.2:title extended;§1.5 new "discovered scope gap" subsection;§2.1 split into A (document routes) + B (KB routes);§2.2 added S14-S20(create_index_for_kb / delete_index / upload kb_id-dynamic / POST kb wiring / DELETE kb wiring / docstring cleanup / test extension);§2.4 added 3 new explicit out-of-scopes(Pydantic kb_id regex / per-KB blob container / `scripts/run_populate_sanity.py` migration);§3 added AC18-AC22(POST /kb index-create / kb_id rejection-rollback / DELETE /kb index-drop / fail-soft on already-gone / chunks land in per-KB index);§4 added R9-R11(Azure rejection + partial-create rollback + ADR-0018 status drift);§5 effort 4-6h → 6-9h;§6.5 H1/H2 reaffirmed clean(implementation of existing ADR-0018, not a new architectural decision);§6.6 NEW ADR-0018 status touch note. checklist.md + progress.md to be updated post-this-commit to derive the new Phase 1.5(multi-KB provisioning) + extend Phase 5 tests. | Chris(approved 2026-05-11) |

---

**Lifecycle reminder**:呢份 spec 喺 `status=approved` 之後 locked。重大 deviation 入 §7 changelog(R3 per PROCESS.md §5)。Approve 前請揀定 §2.3 Decision A(reindex i/ii/iii)。
