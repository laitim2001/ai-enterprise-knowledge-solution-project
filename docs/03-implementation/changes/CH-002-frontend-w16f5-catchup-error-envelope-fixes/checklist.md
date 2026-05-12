---
change_id: CH-002
spec_ref: ./spec.md
status: done            # in-progress | done
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

## Phase 3 — Frontend Eval Console(C09 / C06)(F3)  ✅ DONE 2026-05-12

> Discovered the eval page was **already wired** to `evalApi.run` (`useMutation` + `MetricCardsGrid` + `FailedQueriesCard`) — F3 was much smaller than scoped: remove a dead 501-stub error branch + fix the empty-state copy + add a `max_main_queries` cap. (Surfaced upfront per Karpathy §1.1; logged in progress.)

- [x] **T3.1** — `lib/api/eval.ts`: `EvalRunRequest` already existed (eval_set_id / llm_model / reranker / enable_crag) — added `max_main_queries?: number`; `EvalReport` type already matches backend Pydantic (no change); file-top NOTE comment updated (no longer a 501 stub)
- [x] **T3.2**(F3)— `eval/page.tsx`: Run button was already wired to `evalApi.run` via `useMutation`; removed the dead `if (err instanceof ApiError && err.status === 501)` branch (→ also removed the now-orphan `ApiError` import); added a "Running RAGAs eval — this can take a minute…" hint next to the Run buttons → AC1 + AC2
- [x] **T3.3**(F3)— `eval/page.tsx`: empty-state copy "`/eval/run` is W4 stub — pending implementation" → "eval-set-v0 is a W1 placeholder … real ground truth lands with eval-set-v1 (pending Q14 SME labels)"; file-top doc comment item 3 updated to the wired state
- [x] **T3.4**(F3 / R2)— added a "Max main queries" number input to `RunConfigCard` (default 5), threaded through `handleRun` → `max_main_queries: config.max_main_queries`
- [x] **T3.5** — `grep "W4 stub\|pending implementation per docs/eval" eval/page.tsx` → only the file-top narrative comment "removed the … 'W4 stub' empty-state copy" (provenance, kept per convention) → AC1 / AC12 (partial)

## Phase 4 — Frontend KB-detail Chunks tab(C09)(F7)  ✅ DONE 2026-05-12

- [x] **T4.1** — `lib/api/documents.ts`: added `ChunkSummary` interface (mirrors backend `api.schemas.listing.ChunkSummary`) + `documentsApi.listChunks(kbId, docId)` (GET `/kb/{kb}/documents/{doc_id}/chunks`); stale "Per-doc upload/reindex/delete remain 501 stubs" comment updated (CH-001 wired them)
- [x] **T4.2**(F7)— `kb/[id]/page.tsx` `ChunksTab`: replaced the `<BackendStubNote stub="…" issue="W2 chunk listing implementation">` placeholder with a real `<ChunksTable>` — columns `#` (chunk_index+1/chunk_total) · Title · Section path (`›`-joined) · Flags (disabled / low-value badges) · Chunk id; loading (`<DocumentsSkeleton>`) + empty + error states; removed the now-orphan `BackendStubNote` component
- [x] **T4.3**(F7 / R3)— doc `<Select>` populated from `documentsApi.list` (already-wired W17 F4.1), defaults to first doc; honours `?doc=<doc_id>` (validated against the doc list) via `useSearchParams`
- [x] **T4.4**(F7)— file-top doc comment F3.3 updated to the wired state; `grep "501 stub\|pending backend list endpoint\|W2 chunk listing" kb/[id]/page.tsx` → 0 hits → AC3 / AC12 (partial)

## Phase 5 — Frontend KB-detail Settings-Identity(C09)(F10)  ✅ DONE 2026-05-12

- [x] **T5.1** — `lib/api/kb.ts`: added `kbApi.patchMetadata(kbId, {name?, description?})` (PATCH `/kb/{id}`, partial; returns `KbStatus`)
- [x] **T5.2**(F10)— `kb/[id]/page.tsx` `SettingsTab` "Identity" section: `name` + `description` are now editable `<Input>`s inside a `<form onSubmit={handleIdentitySubmit}>` + "Save identity" button → `metadataMutation` → `kbApi.patchMetadata`; **true partial PATCH** (only sends changed fields; "No changes to save" toast otherwise); on success → invalidate `['kb', kbId]` + `['kb','list']` + toast; on error → `toast.error`
- [x] **T5.3**(F10)— removed "Display fields are read-only Tier 1 — backend `name`/`description` PATCH lands W15+ per CO_W15 follow-up" (the new copy explains the partial PATCH); **did NOT** touch the Pipeline-tab "Read-only Tier 1 view. Inline tuning lands W15+" copy (that tab is intentionally read-only) → AC4

## Phase 6 — Cross-check + Frontend tests + closeout  ✅ DONE 2026-05-12

- [x] **T6.1**(In-Scope item 9)— `traces/[traceId]/page.tsx` confirmed **already wired** (W16 F5.5 / ADR-0020 / W18 F3 — `useQuery(debugApi.getTrace)`, status-branching); the "501 stub mitigation" mention at line ~13-14 is a historical narrative in the file-top comment, not user-facing copy → no change → AC13
- [x] **T6.2** — `tests/unit/eval-page.test.tsx` (3 tests: empty state without W4-stub copy / Run → 4 metric cards + `max_main_queries` arg / error → `toast.error`) + `tests/unit/kb-detail.test.tsx` (2 tests: Chunks tab renders ChunkSummary rows + no stale copy / Settings-Identity editable + PATCH on save); `tests/unit/setup.ts` got a `ResizeObserver` polyfill (Radix Slider on the eval page) → AC11 (partial)
- [x] **T6.3** — `pnpm test:unit` → **18 passed (6 files)** (was 13 / 4 files; +5 / +2); `pnpm type-check` → 0 errors; `pnpm lint` → clean; `grep -rn "\[oklch(" frontend/` → 0 (milestone preserved) → AC11
- [x] **T6.4** — `grep -rn "W4 stub\|501 stub\|PATCH lands W15\|pending backend list endpoint\|pending implementation per docs/eval\|W2 chunk listing" frontend/ --include=*.tsx --include=*.ts` → only narrative file-top comments + the new test files' `queryByText(...).toBeNull()` assertions; also fixed the now-stale parenthetical in `tests/e2e/visual-baseline.spec.ts:69` → AC12
- [x] **T6.5** — `pytest tests/api/ tests/test_error_contract.py tests/test_e1_e5_e12_smoke.py tests/test_f1_7_mock_smoke.py tests/test_auth_self_register.py` → all green (error-handler blast-radius + api routes) → AC9 (final)
- [ ] **T6.6**(AC14)— dev-env curl smoke of AC1-AC8 covered by pytest; the **browser walkthrough** of the 3 frontend flows = user pre-Beta smoke(R8 / CO_W15_F4 deferral umbrella — not blocking closeout per the W15-W18 caveat pattern) 🚧 user-deferred

## Verification

- [x] Run all acceptance criteria from `spec.md §3`(AC1–AC14)— 13/14 ✅ + AC14 🟡 user-deferred(see progress Closeout)
- [x] Smoke test in dev env — backend `pytest` (111 passed across the error-handler blast radius) + `pnpm test:unit` (18 passed) cover AC1-AC13; the interactive browser walkthrough = user pre-Beta smoke per AC14
- [ ] (user-facing)manual / Playwright verify per spec scenario — 🚧 deferred to user pre-Beta smoke per AC14(R8 `npx playwright install chromium` blocked / CO_W15_F4 / ADR-0017 — same umbrella as W15-W18)

## Cross-Cutting

- [x] Each commit references `progress.md` Day-N entry(R2)— `30bac99` Day 1, `69dbe1d` Day 1 cont., `c2b489e` Day 1 cont. 2, closeout commit Day 1 cont. 2
- [x] Component tag in commit message per CC-1 — `feat(api): … (C01,C08)`, `feat(frontend): … (C06,C09)`, `docs(planning,catalog): …`
- [x] No ADR needed(H1 verified — see spec §6.6;F6 was a spec-text reconcile, not an architecture decision)
- [x] `components/Cn-*.md` design note — none exists for C01/C06/C08/C09(rolling JIT;none created)→ no update
- [x] OQ status sync — N/A(no OQ resolved by CH-002)
- [x] COMPONENT_CATALOG.md — C08 + C09 status rows appended with the CH-002 note
- [x] `progress.md` closeout summary written(14-AC verification table + effort summary + lessons)
- [x] `progress.md` `status: closed` + `checklist.md` `status: done` + `spec.md` `status: done`

---

**Lifecycle reminder**:呢份 checklist 隨 spec acceptance criteria 衍生。新加 item 必須先入 spec + changelog,然後再加 checklist。延後 item 標 🚧 + reason 喺 progress Day-N entry,**唔可以刪**。
