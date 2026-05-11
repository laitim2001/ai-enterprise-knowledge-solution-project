---
change_id: CH-001
spec_ref: ./spec.md
checklist_ref: ./checklist.md
status: in-progress
last_updated: 2026-05-11
---

# CH-001 — Progress

> Day-N entries during execution + 結尾 closeout summary。
> 每 commit 對應一個 Day-N entry mention(R2 binding rule per PROCESS.md §5)。

---

## Day 0 — Kickoff(2026-05-11)

### Trigger
- User trigger:2026-05-11 dev test session — `/kb/new` Pipeline wizard step 3 hit 501 on `POST /kb/{kb_id}/documents`(screenshot `Screenshot 2026-05-11 102613.png`)
- Diagnosis confirmed:`backend/api/routes/documents.py:72-102` is a 3-route hardcoded 501-stub cascade(POST upload + DELETE doc + POST reindex);session-start.md §11 lists this as **CO_F3a** carry-over("per-doc upload/reindex/delete stays 501 stub — W2 ingestion + Track A")
- "Track A" deferral label was over-broad — the actual block is `.env.production` for prod deploy, but the dev `.env` already has Azure OpenAI + AI Search cred(W2 Gate 1 PASS R@5=0.9722 was driven by these);so this is unblocked **now**

### Done(this session)
- ✅ Confirmed diagnosis by reading `backend/api/routes/documents.py` + grepping for the 501 stub text + confirming the W2 ingestion machinery exists(`backend/ingestion/orchestrator.py` + `parsers/{docx,pptx,pdf}_parser.py` + `parsers/__init__.py` `select_parser` factory + `chunker/layout_aware.py` + `embedding/azure_openai_embedder.py` + `indexing/populate.py`)+ `scripts/run_populate_sanity.py` as the canonical caller pattern
- ✅ PROCESS.md §1 classification = **Change**(behavior change 501 stub → real implementation;not a Phase deliverable — no active phase;not a Bug-fix — no regression)
- ✅ Surfaced **Decision A**(reindex semantics)to the user:**(i)** 422 + hint / **(ii)** replace-in-place / **(iii)** source-doc store
- ✅ User picked scope **(b)**(POST + DELETE + reindex 一齊做)+ Decision A = **(ii) replace-in-place reindex**
- ✅ Wrote `spec.md` v1.1 — status `draft` → `approved`(2026-05-11);§2.3 locked to (ii) with the doc_id-match safety check;§3 AC9 broken into AC9.1 (happy path) / AC9.2 (missing file) / AC9.3 (mid-pipeline failure + mismatch);§7 changelog row added
- ✅ Derived `checklist.md` v1.1 from spec §2.2 In Scope + §3 AC — 7 phases × T-items(T1.1-T7.7 ≈ 40 atomic items)+ Cross-Cutting
- ✅ **Decision B discovery + approval**(post Phase 1 read-only investigation):while reading `backend/api/routes/kb.py:22-31` + `backend/storage/kb_naming.py` + ADR-0018 to plan the lifespan wiring,surfaced the **multi-KB Azure AI Search index provisioning gap** ── `POST /kb` only creates the KB storage record but does NOT provision the per-KB index `ekp-kb-{kb_id}-v1`(legacy `drive_user_manuals` was manually provisioned at W2 D1 via `scripts/create_index.py`);user's screenshot workflow(`copilot-cowork-document-1` new KB)would still fail post-CH-001-v1.1 with Azure 404 not 501. **User picked (β) scope expansion**:(1)user's screenshot was a new-KB workflow → (α) didn't solve it;(2)ADR-0018 Phase 3 was over-deferred(Track A blocks prod deploy, not dev `.env` admin-key);(3)同 W16 F5.3 Decision B.1 一齊 unblock;(4)避免 CH-001/CH-002 切割成本。
- ✅ **Updated spec to v1.2** — title extended;§1.5 NEW "discovered scope gap" subsection;§2.1 split into A (document routes) + B (KB routes auto-provisioning);§2.2 added S14-S20(create_index_for_kb / delete_index / delete_doc / upload kb_id-dynamic / POST kb wiring / DELETE kb wiring / docstring cleanup / test extension);§2.4 added 3 new explicit out-of-scopes;§3 added AC18-AC22;§4 added R9-R11;§5 effort 4-6h → 6-9h;§6.5 reaffirmed clean(implementation of existing ADR-0018, not new architecture);§6.6 NEW ADR-0018 status touch note;§7 v1.2 changelog row。
- ✅ **Extended checklist to v1.2** — NEW Phase 1.5(T1.5.1-T1.5.10, multi-KB index provisioning);Phase 2 T2.5 updated(`upload(kb_id=kb_id)` per T1.5.5);Phase 3 T3.1 referenced T1.5.4 not T1.2;Phase 5 added T5.14-T5.19(AC18-AC22 tests);Phase 6 T6.2 changed to use a NEW kb_id(was vague)+ added T6.4 + T6.6 Azure-direct verifies;Phase 7 T7.2/T7.3/T7.4 extended + T7.5 NEW(ADR-0018 update)

### Decisions
- **Decision A = (ii) replace-in-place reindex**(per user 2026-05-11). Rationale per spec §2.3:real semantics(atomic replace, one API call), honest about the source-store gap(user provides the source), 90% code reuse with POST + DELETE, closes CO_F3a properly. (i) rejected as technical-but-not-real close;(iii) rejected as genuinely Tier 2(R12 Azurite mismatch + scope creep).
- **Decision B = (β) scope expansion**(per user 2026-05-11):include multi-KB index provisioning(`POST /kb` auto-creates Azure index;`DELETE /kb` drops it;`IndexPopulator.upload(kb_id=)` BC-preserving signature;close ADR-0018 Phase 3 upload-side). Rationale per spec §1.5 + §7 changelog v1.2 row:user's screenshot workflow needs it,ADR-0018 was over-deferred,dev cred is already there,avoid CH-001/CH-002 split cost. (α) rejected because it doesn't solve the user's actual workflow ── only renames the wall.
- **Approach A vs B** for lifespan(spec §6.2):commit to **A** in implementation unless the embedder isn't safely shareable across query + ingest contexts(then B as fallback). Lifespan-init for `app.state.embedder`(exposed for ingestion)+ `app.state.index_populator` + `app.state.ingestion_chunker` alongside the existing `app.state.retrieval_engine` etc.
- **`uploader=None`** per the existing `scripts/run_populate_sanity.py` precedent(R12 Azurite signature mismatch still open;screenshots extracted but blob upload skipped;text retrieval unaffected per architecture.md §3.5). Per-KB blob container provisioning(ADR-0018 Phase 3 blob-side)stays deferred per R11 + spec §6.6 — needs R12 resolution first.
- **doc_id derivation = slugified filename stem**(not UUID)— traceability over opacity;duplicate doc_id within the same KB → 409 with hint.
- **`upload` signature BC**:keep `kb_id=None` optional default(falls back to `self.index_name` legacy behavior)so existing W2-era callers like `scripts/run_populate_sanity.py` + W2 tests don't break. Karpathy §1.3 surgical.
- **POST /kb storage rollback on Azure failure**:storage record deleted via `service.delete(kb_id)` if `populator.create_index_for_kb` raises;rollback failure itself is logged but the user-facing 502 still surfaces(R10 documented).
- **No new ADR + no new dep**(spec §6.4 + §6.5 — H1/H2 both verified clean;Decision B = implementation of existing ADR-0018, not a new architectural decision).
- **ADR-0018 stays `Accepted`** post-CH-001(NOT `done`)— Phase 3 upload-side closed,blob-side still R12-deferred(R11 + spec §6.6)

### Blockers
- None at kickoff — all W2 machinery already implemented, Azure dev cred presumed in `.env`(if missing → spec AC5 surfaces the 503 cleanly, not a CH-001 blocker)

### Effort
- Planned (today, kickoff + Decision B scope-expansion + spec/checklist/progress v1.1 → v1.2):~2.5h(initial 1.5h + ~1h for Decision B discovery + spec/checklist/progress update)
- Actual:~2.5h(this session)
- Variance:0

### Commits
| Hash | Subject |
|---|---|
| `671a925` | docs(planning): CH-001 spec + checklist + progress — approved Decision A = (ii) replace-in-place reindex (close CO_F3a) |
| _(pending)_ | docs(planning): CH-001 spec v1.2 + checklist + progress — Decision B = (β) scope expansion (multi-KB index provisioning; close ADR-0018 Phase 3 upload-side) |

### Next
- Commit the v1.2 pre-doc bundle update;then start **Phase 1**(T1.1-T1.5 backend service wiring)+ **Phase 1.5**(T1.5.1-T1.5.10 multi-KB index provisioning ── `IndexPopulator.create_index_for_kb` + `delete_index` + `delete_doc` + `upload(kb_id=)` BC ext + POST/DELETE /kb wiring)+ **Phase 2-4**(documents.py routes);commit per phase or per logical chunk;run `pytest` + `mypy --strict` + `ruff check` after each phase

---

## Day 1 — Phase 1 + 1.5 backend service wiring + multi-KB index provisioning(2026-05-11)

### Done
- ✅ **T1.1** Read `api/server.py` lifespan in full ── existing pattern: `embedder` / `searcher` / `reranker` / `synthesizer` / `crag_grader` all `__aenter__`ed inside the `if azure_cred:` block. App.state already has `retrieval_engine` / `synthesizer` / `crag_loop`. **No `IndexPopulator` or ingestion services on app.state yet** ── added.
- ✅ **T1.2 / T1.5.2-1.5.5** `backend/indexing/populate.py` — added 3 new methods + extended `upload` signature(`12bfd3f` will commit):
   - `IndexPopulator.create_index_for_kb(kb_id)` ── PUT `/indexes/{name}?api-version=2024-07-01` with `_load_index_schema()` from `backend/indexing/schema.json`(`@lru_cache(maxsize=1)` so the read is once-per-process);override `schema["name"]` with `kb_id_to_index_name(kb_id, legacy_default_index=self.index_name)`;accept 200/201/204 as success;raise `httpx.HTTPStatusError` on 4xx/5xx;structlog `index_created` on success
   - `IndexPopulator.delete_index(kb_id) -> bool` ── DELETE `/indexes/{name}?api-version=2024-07-01`;**True on 204, False on 404 (fail-soft)**, raise on other errors;structlog `index_deleted` / `index_already_gone` / `index_delete_failed`
   - `IndexPopulator.delete_doc(kb_id, doc_id) -> int` ── two-step:(1) POST `/docs/search` with `filter=kb_id eq X and doc_id eq Y`, `select=chunk_id`, `top=1000` to collect chunk_ids;(2) batch POST `/docs/index` with `@search.action: "delete"` per chunk_id;return count deleted. Fail-soft when the index itself is missing(returns 0)── covers the "DELETE on a doc in a KB never populated" edge case
   - `IndexPopulator.upload(records, action, kb_id=None)` ── BC-preserving signature ext;`_resolve_index_name(kb_id)` helper resolves dynamically(falls back to `self.index_name` when kb_id None;works for existing W2-era callers like `scripts/run_populate_sanity.py`);`_upload_batch` now takes `index_name` arg
- ✅ **T1.4 / T1.5** `backend/api/server.py` lifespan — added `app.state.embedder` + `app.state.index_populator` + `app.state.ingestion_chunker` alongside the existing `app.state.retrieval_engine` etc;`populator` ── `__aenter__`ed inside the `if azure_cred:` block + `__aexit__`ed in `finally`;`LayoutAwareChunker()` (stateless) constructed unconditionally(works without Azure cred — chunking is offline);**Approach A confirmed**(lifespan-init, not per-request)── one Azure REST client per app lifetime
- ✅ **T1.5.6-1.5.7** `backend/api/routes/kb.py` POST + DELETE wiring(`12bfd3f` will commit):
   - POST `/kb` ── after `service.create(payload)` success → resolve `_get_populator(request)`;**fail-soft when populator is None**(no Azure cred → log warning + return 201 with storage record only, preserving W16 F5.3 Decision B.1 baseline + the existing `test_delete_kb_in_memory_baseline_preserved` contract);Azure call failure → `service.delete(payload.kb_id)` rollback + 502 `index.create_failed` with the actionable hint quoting Azure index-name rules;rollback failure logged but the original 502 still raised(R10)
   - DELETE `/kb/{kb_id}` ── after `service.delete(kb_id)` success → resolve `_get_populator(request)`;**fail-soft when populator is None**(returns 204 with storage already gone, no Azure touch);populator's `delete_index` itself is fail-soft on 404(common for pre-CH-001 KBs / partial-rollback orphans);Azure 5xx → 502 with hint to manually drop the index via `scripts/create_index.py delete`
   - **Deviation discovered**:initial `_populator_or_503` (strict 503) broke `test_delete_kb_in_memory_baseline_preserved_per_b1` ── pytest failed with `503 != 204`. Fixed by replacing with `_get_populator -> IndexPopulator | None` + fail-soft branches in both routes. **Karpathy §1.3 "don't break what wasn't part of the change"**;the test surfaced the regression early
- ✅ **T1.5.8** Dropped the "Track A W17+" deferral comment block in `routes/kb.py` DELETE docstring + replaced with the CH-001 closure note + ADR-0018 reference
- ✅ **T1.5(documents helper)** `backend/api/routes/documents.py` — added `_ingestion_deps_or_503(request) -> _IngestionDeps`(NEW frozen dataclass bundling embedder + populator + chunker)alongside the existing `_engine_or_503`;**strict 503** for upload/reindex routes(uploads can't function without Azure cred);file-top docstring updated with the CH-001 closure narrative;imports for `IndexPopulator` / `Embedder` / `Chunker` Protocols added
- ✅ Verified `mypy --strict` clean on the 4 changed files(`indexing/populate.py` + `api/server.py` + `api/routes/kb.py` + `api/routes/documents.py`);transitive mypy errors exist in OTHER unrelated files(eval/ragas_evaluator, api/routes/query, etc — pre-existing baseline, not introduced by this Change)
- ✅ Verified `ruff check` at the pre-existing 19-error baseline on `api/server.py`(my 2 new imports added 2 noqa-suppressed entries — net delta zero)+ clean on the other 3 files
- ✅ Verified `pytest backend/tests/test_orchestrator.py tests/test_api_skeleton.py tests/test_documents_listing.py tests/test_kb_management.py tests/test_kb_reindex.py tests/test_multi_kb_routing.py` — **46 tests pass**(including the previously-failing `test_delete_kb_in_memory_baseline_preserved_per_b1` after the fail-soft fix)
- ✅ Verified `python -c "import api.server"` clean(no startup error)

### Decisions
- **Fail-soft when populator is None**(both POST + DELETE /kb)── necessary to preserve the W16 F5.3 Decision B.1 in-memory baseline + the existing test contract. Spec §2.1 wasn't explicit about this case;documented in the route docstrings + this Day-1 entry. Strict Azure-required would be wrong for dev/CI where `.env` may not have Azure cred. Upload routes(documents.py)remain strict-503 because they genuinely can't function without Azure.
- **Per-request `IngestionOrchestrator` construction**(not lifespan)── because `select_parser(Path)` resolves the parser per-file-extension;orchestrator holds parser reference;cheap to construct(just dataclass-ish). Embedder + populator are lifespan-shared.
- **Embedder shared between RetrievalEngine + ingestion path** ── `app.state.embedder = embedder` exposed alongside the existing `RetrievalEngine(embedder=embedder, …)` wrapping. Safe because the embedder is a stateless async httpx client(no per-call state). Saves one Azure OpenAI client.
- **`_load_index_schema()` cached via `lru_cache(maxsize=1)`** ── schema.json is small + immutable per-process;cache the parsed dict once;cheap.
- **`# noqa: E402` on the 2 new `server.py` imports** ── same truststore-after-imports pattern as the 19 pre-existing E402 errors in the file. Not refactoring the whole file's noqa (Karpathy §1.3 — don't refactor what isn't broken from your edit's perspective).

### Blockers
- None

### Effort
- Planned (Phase 1 + 1.5):~2.5h (T1.1-T1.5.10)
- Actual:~2.5h (this session)
- Variance:0

### Commits
| Hash | Subject |
|---|---|
| _(pending — committing now)_ | feat(backend,api,ingestion): CH-001 Phase 1 + 1.5 — IndexPopulator multi-KB lifecycle + lifespan wiring + POST/DELETE /kb auto-provisioning (close ADR-0018 Phase 3 upload-side) |

### Next
- **Phase 2** T2.1-T2.10 ── wire `POST /kb/{kb_id}/documents`(UploadFile → tempfile → select_parser → IngestionOrchestrator → IndexPopulator.upload(kb_id=) → KB counter sync)
- **Phase 3** T3.1-T3.5 ── wire `DELETE /kb/{kb_id}/documents/{doc_id}`(IndexPopulator.delete_doc → 404 / 502 / 204)
- **Phase 4** T4.1-T4.9 ── wire `POST /kb/{kb_id}/documents/{doc_id}/reindex`(replace-in-place per Decision A = (ii))
- Likely commit Phase 2-4 as one logical chunk(same file, same lifespan deps, atomic CO_F3a closure)
- Then Phase 5 backend tests + Phase 7 docs

---

## Closeout(填於 status=done)

### Acceptance verification(against spec §3 AC1-AC17)
- _(verify each AC ✅ / ⚠️ partial / ❌ failed at closeout)_

### Effort summary
| Day | Planned (h) | Actual (h) | Variance |
|---|---|---|---|
| Day 0 (kickoff) | 1.5 | 1.5 | 0 |
| Day 1 (impl) | TBD | — | — |

### Lessons
- **What worked**:_(fill at closeout)_
- **What didn't / unexpected friction**:_(fill at closeout)_
- **Carry-overs**:_(if any deferred to other tasks)_

### Component design note status updates
- **C01**(Ingestion):`v1-active`(orchestrator path now also exercised via HTTP route, not just `scripts/run_populate_sanity.py` — no spec/interface change → no version bump)
- **C03**(Indexing):if `IndexPopulator.delete_doc` was added — note in components/C03-*.md;else no change
- **C08**(API Gateway):`v1-active`(stub-cascade fully closed — POST/DELETE/reindex all real;append `Status` row note)

### CO_F3a status flip
- session-start.md §11 — flip from "stays 501 stub — W2 ingestion + Track A" to **"CLOSED by CH-001 YYYY-MM-DD"**

---

**End of CH-001 progress**
