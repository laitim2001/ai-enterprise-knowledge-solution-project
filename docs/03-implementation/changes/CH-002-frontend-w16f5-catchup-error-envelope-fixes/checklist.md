---
change_id: CH-002
spec_ref: ./spec.md
status: in-progress     # in-progress | done
last_updated: 2026-05-12
---

# CH-002 — Checklist

> Atomic checkbox items derived from `spec.md` §3 acceptance criteria。每 item ≤ 1-2h effort。
> AI tick 完成嘅 item;唔可以 tick 嘅 item 喺 progress Day-N entry 寫原因(per CLAUDE.md sacred rule — 唔可以刪未勾 `[ ]`)。
> Design decisions locked at approval:**F2 = Option A**(route preserves original basename)· **F6 = Option a**(CH-001 spec inline reconcile note, no code).

## Phase 1 — Backend(C08 / C01)  ✅ DONE 2026-05-12

- [x] **T1.1**(F5)— `backend/api/routes/documents.py` `_api_error` detail key `"actionable_hint"` → `"hint"`(matches `error_handlers.py` `exc.detail.get("hint")` convention)
- [x] **T1.2**(F5)— added `test_ch002_f5_route_hint_surfaces_in_error_envelope` (parametrized: `document.duplicate` / `validation.unsupported_format` / `document.not_found` / `reindex.doc_id_mismatch`) — built via `_build_app(..., with_error_handlers=True)`, asserts non-null `actionable_hint` containing the route hint → AC5
- [x] **T1.3**(F8)— `backend/api/error_handlers.py` `validation_exception_handler`: `message` now `"Request payload failed validation: {loc} — {msg}"` via new `_redacted_loc_path` (joins str/int `loc` elements only, never `input`); `string_too_long` → `query_too_long` branch preserved
- [x] **T1.4**(F8)— added `test_ch002_f8_validation_envelope_names_field_without_leaking_input` + `test_ch002_f8_validation_envelope_redacts_structured_input_value` to `backend/tests/test_error_contract.py` (module-level `_FeedbackLike` model + `/feedback-like` route in the `app` fixture — `from __future__ import annotations` needs the model module-level) → AC6
- [x] **T1.5**(F2 Option A)— `_run_ingest_pipeline`: `tempfile.NamedTemporaryFile(suffix=ext)` → write bytes to `<tempfile.mkdtemp()>/<Path(filename.replace("\\","/")).name>`; `shutil.rmtree(tmp_dir, ignore_errors=True)` in `finally`; reindex shares `_run_ingest_pipeline` so it inherits the fix
- [x] **T1.6**(F2)— added `test_ch002_f2_tempfile_named_after_original_basename` (asserts `ingest_mock.await_args.kwargs["source"].name == "My Report 2026.docx"`) + `test_ch002_f2_upload_filename_traversal_stripped` (parametrized `../../etc/passwd.docx` / `..\..\evil.docx` / `/abs/path/leak.docx` → `.name` stripped, `".." not in source.parts`, `source.is_absolute()`) → AC7 + R1
- [x] **T1.7** — `pytest tests/api/test_documents_route.py tests/test_error_contract.py` → **42 passed** (32 documents + 10 error_contract); 0 regression vs CH-001's 24+10 baseline → AC9 (full re-run at closeout)
- [x] **T1.8** — `ruff check` on the 4 changed files → clean; `mypy --strict --explicit-package-bases api/routes/documents.py api/error_handlers.py` → 0 errors on the **changed lines** (the ~50 reported errors are the pre-existing transitive baseline: Docling/langfuse/psycopg missing stubs + `Missing type arguments for generic type "dict"` family + Starlette `add_exception_handler` arg-type quirk + 2 pre-existing `Any`-return spots at `documents.py:80` / `error_handlers.py:102`, none touched by CH-002) → AC10

## Phase 2 — F6 spec reconcile(C08 — doc only)  ✅ DONE 2026-05-12

- [x] **T2.1**(F6 Option a)— `docs/03-implementation/changes/CH-001-.../spec.md` §3 AC4: added inline reconcile note (as-built = `resource.not_found` via shared `_verify_kb_or_404`; acceptable; no code change; CH-001 stays `done`) → AC8 (Option a path)
- [x] **T2.2**(F6)— added the AC4-reconcile row to CH-001 spec.md §7 changelog

## Phase 3 — Frontend Eval Console(C09 / C06)(F3)

- [ ] **T3.1** — frontend API client + TS types: add `evalRun(req: EvalRunRequest): Promise<EvalReport>` (POST `/eval/run`); `EvalReport` type mirrors backend Pydantic(`recall_at_5`, `faithfulness`, `correctness`, `image_association`, `p95_latency_ms`, `failed_queries[]`, `_metrics_deferred_note?`); comment ref to the schema file path
- [ ] **T3.2**(F3)— `frontend/app/(app)/eval/page.tsx`: Run button → `evalRun()` mutation(TanStack `useMutation` or equiv); loading spinner with "this can take a minute"; on success render the 4-metric values + `failed_queries` table(reuse the existing 4-metric display component if present); on error → existing `ApiError` boundary(`message` + `actionable_hint`)→ AC1 + AC2
- [ ] **T3.3**(F3)— `eval/page.tsx`: replace empty-state copy "`/eval/run` is W4 stub — pending implementation" with "Run an eval to see results; eval-set-v0 is a placeholder — real ground truth lands with eval-set-v1 (pending Q14 SME labels)"; update the file-top doc comment(lines ~17-20) to reflect the wired state; remove the `toast.info('pending W4 backend implementation')` path
- [ ] **T3.4**(F3)— default the Run form's `max_main_queries` to a small N(3-5)to avoid browser/proxy timeout(R2)
- [ ] **T3.5** — `grep "W4 stub\|pending implementation per docs/eval" frontend/app/(app)/eval/page.tsx` → 0 hits → AC1 / AC12 (partial)

## Phase 4 — Frontend KB-detail Chunks tab(C09)(F7)

- [ ] **T4.1** — frontend API client + TS types: add `listChunks(kbId, docId): Promise<ChunkSummary[]>` (GET `/kb/{kb}/documents/{doc_id}/chunks`); `ChunkSummary` type mirrors backend(`chunk_id`, `section_path[]`, `chunk_title`, `chunk_index`, `chunk_total`, `enabled`, `low_value_flag`)
- [ ] **T4.2**(F7)— `frontend/app/(app)/kb/[id]/page.tsx` Chunks tab: replace `StubTab stub="GET .../chunks" issue="W2 chunk listing implementation"` with a real table — columns: `chunk_index/chunk_total` · `chunk_title` · `section_path` breadcrumb · `enabled` · `low_value_flag` badge; loading + empty + error states
- [ ] **T4.3**(F7 / R3)— Chunks tab needs a `doc_id`: add a doc `<Select>` populated from `GET /kb/{kb}/documents`(already wired W17 F4.1), default to first doc; honor `?doc=<doc_id>` query param(and optionally add a "View chunks" link from the Documents tab rows)
- [ ] **T4.4**(F7)— update the file-top doc comment(line ~14-15 "F3.3 Chunks tab: backend ... returns 501 — surface placeholder")to the wired state; `grep "501 stub\|pending backend list endpoint\|W2 chunk listing" frontend/app/(app)/kb/[id]/page.tsx` near Chunks tab → 0 hits → AC3 / AC12 (partial)

## Phase 5 — Frontend KB-detail Settings-Identity(C09)(F10)

- [ ] **T5.1** — frontend API client: add `patchKbIdentity(kbId, {name?, description?}): Promise<KbDetail>` (PATCH `/kb/{id}`, partial)
- [ ] **T5.2**(F10)— `frontend/app/(app)/kb/[id]/page.tsx` Settings tab "Identity" section: add `name` + `description` editable inputs + "Save identity" button → `patchKbIdentity()` mutation; optimistic update + toast on success; error → `ApiError` boundary
- [ ] **T5.3**(F10)— remove "Display fields are read-only Tier 1 — backend `name`/`description` PATCH lands W15+ per CO_W15 follow-up"(line ~964-965); **do NOT** touch the Pipeline-tab "Read-only Tier 1 view. Inline tuning lands W15+" copy(line ~449 — that tab is intentionally read-only)→ AC4

## Phase 6 — Cross-check + Frontend tests + closeout

- [ ] **T6.1**(In-Scope item 9)— check `frontend/app/(app)/traces/[traceId]/page.tsx`: confirm it's already wired per W16 F5.5 `debug/trace/{id}`(no change)or fold in any stale stub copy → AC13
- [ ] **T6.2** — frontend Vitest/RTL: eval-page Run-flow happy(mocked `evalRun` → metrics render)+ error(→ ApiError boundary); chunks-tab render(mocked `listChunks` → rows); identity-save(mocked `patchKbIdentity` → toast)→ AC11 (partial)
- [ ] **T6.3** — `pnpm test:unit` green(existing 13 + new); `tsc` clean; `lint` clean; `grep -rn "\[oklch(" frontend/` → 0(milestone preserved)→ AC11
- [ ] **T6.4** — `grep -rn "W4 stub\|501 stub\|PATCH lands W15\|pending backend list endpoint\|pending implementation per docs/eval" frontend/` → 0 hits → AC12
- [ ] **T6.5** — re-run `pytest backend/tests/api/` → all green → AC9 (final)
- [ ] **T6.6**(AC14)— dev-env curl smoke of AC1-AC8(backend); the browser walkthrough of the 3 frontend flows = user pre-Beta smoke(R8 / CO_W15_F4 deferral umbrella — not blocking closeout per the W15-W18 caveat pattern)

## Verification

- [ ] Run all acceptance criteria from `spec.md §3`(AC1–AC14)
- [ ] Smoke test in dev env(backend `:8000` `--env-file ../.env` + frontend `:3001`)
- [ ] (user-facing)manual / Playwright verify per spec scenario — deferred to user pre-Beta smoke per AC14

## Cross-Cutting

- [ ] Each commit references `progress.md` Day-N entry(R2)
- [ ] Component tag in commit message per CC-1(`feat(api,frontend): ... (C01,C08,C09)` / `docs(...)`)
- [ ] No ADR needed(H1 verified — see spec §6.6)
- [ ] (if affects component)Update `components/Cn-*.md` design note — **only if a note exists**; C01/C06/C08/C09 notes are rolling JIT, likely no update needed(verify at closeout)
- [ ] OQ status sync — N/A(no OQ resolved by CH-002)
- [ ] COMPONENT_CATALOG.md — append a C08/C09 status row noting CH-002 frontend catch-up(if warranted at closeout)
- [ ] `progress.md` closeout summary written
- [ ] `progress.md` + this `checklist.md` frontmatter status flipped to `done` / `closed`

---

**Lifecycle reminder**:呢份 checklist 隨 spec acceptance criteria 衍生。新加 item 必須先入 spec + changelog,然後再加 checklist。延後 item 標 🚧 + reason 喺 progress Day-N entry,**唔可以刪**。
