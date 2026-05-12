---
change_id: CH-002
spec_ref: ./spec.md
checklist_ref: ./checklist.md
status: closed          # in-progress | closed
---

# CH-002 — Progress

> Day-N entries during execution + 結尾 closeout summary。
> 每 commit 必須對應一個 Day-N entry mention(R2 binding rule per PROCESS.md §5)。

---

## Day 1 — 2026-05-12

### Done
- Deep Smoke v2(2026-05-12)11 findings → triage → batched F2/F3/F5/F6/F7/F8/F10 into CH-002(per user instruction:批 A frontend W16-F5 catch-up + 批 B backend small fixes,one PR)
- Wrote `spec.md` v1.0(§1 context per-finding diagnosis · §2 scope incl. §2.3 design choices · §3 14 AC · §4 7 risks · §5 effort 6-9h · §6 deps + H1/H2/ADR verification)
- Approved by Chris 2026-05-12 — **Decision F2 = Option A**(upload route preserves the original filename basename inside a `mkdtemp()` dir → `source.stem` correct, zero parser/orchestrator signature change)· **Decision F6 = Option a**(CH-001 spec §3 AC4 inline reconcile note — `resource.not_found` is acceptable since the message already names the KB; no code change, CH-001 status stays `done`)
- `spec.md` flipped `proposed → approved`; `checklist.md` + `progress.md` derived
- (commit: `docs(planning): CH-002 spec + checklist + progress — approved (F2=A, F6=a)`)

### Decisions
- **F2 = Option A** over Option B(thread `original_filename` through orchestrator + 3 parsers)— Karpathy §1.2 simplicity; `source.stem` is already the intended `doc_title` semantics, the route just needs to stop discarding the basename. Traversal guard: `Path(filename).name` + write only into a fresh `mkdtemp()`.
- **F6 = Option a** over Option b(route emits `kb.not_found` + new `ErrorCodes.KB_NOT_FOUND`)— `_verify_kb_or_404` is shared by 4 routes; changing it for a code-string the frontend doesn't even branch on is not surgical. The spec text was aspirational; reconcile in docs.
- **Sequencing**(Karpathy §1.4 goal-driven, per spec §5): backend first(F5 → F8 → F2 + tests → `pytest` green)→ F6 doc reconcile → frontend Eval(F3)→ Chunks tab(F7)→ Settings-Identity(F10)→ Vitest/RTL → grep sweep → docs closeout.
- **Out of scope**(separate handling, documented spec §2.4): F1(setup doc + `settings.py` env_file)· F4(favicon)· F9(`/dashboard` 375px overflow → BUG-NNN)· F11(chat focus-mode toggle → W18-impl verification)· Chunks `chunk_text` preview · chunk enable/disable write-path.

### Blockers
- None for backend / frontend code. AC14(browser walkthrough)stays on the user pre-Beta smoke backlog(R8 `npx playwright install chromium` blocked / CO_W15_F4 / ADR-0017)— consistent with the W15-W18 caveat pattern; not blocking CH-002 closeout.

### Effort
- Planned:0.5h(triage + spec + checklist + progress);Actual:~0.75h;Variance:+0.25h

### Commits
| Hash | Subject |
|---|---|
| `30bac99` | `docs(planning): CH-002 spec + checklist + progress — approved (F2=Option A basename, F6=Option a spec reconcile)` |

---

## Day 1 (cont.) — 2026-05-12 — Phase 1 (backend) + Phase 2 (F6 reconcile)

### Done
- **T1.1 (F5)** — `documents.py` `_api_error` detail key `"actionable_hint"` → `"hint"` (the key `error_handlers.http_exception_handler` actually reads — the wrong key silently dropped the route's hint, leaving the envelope's `actionable_hint` null). Docstring updated.
- **T1.3 (F8)** — `error_handlers.py` `validation_exception_handler`: new `_redacted_loc_path()` builds a dotted field path from the Pydantic error `loc` (str/int elements only — never `input`/`ctx` values, H5); `message` is now `"Request payload failed validation: {loc} — {msg}"`. `string_too_long` → `query_too_long` (E6) branch preserved.
- **T1.5 (F2 Option A)** — `_run_ingest_pipeline`: tempfile is now written to `<tempfile.mkdtemp()>/<Path(filename.replace("\\","/")).name>` instead of `tempfile.NamedTemporaryFile(suffix=ext)` — so the parser's `doc_title = source.stem` is the real filename stem, not an opaque `tmpXXXX`. `Path(...).name` strips all directory components (traversal-safe on POSIX + Windows). `shutil.rmtree(tmp_dir, ignore_errors=True)` in `finally`. Reindex inherits it (shares `_run_ingest_pipeline`).
- **T1.2 + T1.4 + T1.6 (tests)** — `test_documents_route.py`: `_build_app(with_error_handlers=...)` flag added; `test_ch002_f5_route_hint_surfaces_in_error_envelope` (4-param) + `test_ch002_f2_tempfile_named_after_original_basename` + `test_ch002_f2_upload_filename_traversal_stripped` (3-param, incl. `../../etc/passwd.docx` + `..\..\evil.docx` + `/abs/path/leak.docx`). `test_error_contract.py`: module-level `_FeedbackLike` (Literal) + `/feedback-like` route in the `app` fixture + `test_ch002_f8_validation_envelope_names_field_without_leaking_input` + `test_ch002_f8_validation_envelope_redacts_structured_input_value`.
- **T1.7** — `pytest tests/api/test_documents_route.py tests/test_error_contract.py` → **42 passed**, 0 regression (was 24 + 10 in CH-001; now 32 + 10 — net +8 CH-002 tests, accounting for parametrize expansion: 4 + 1 + 3 + 2 = 10 new test cases).
- **T1.8** — `ruff check` 4 changed files → clean; `mypy --strict --explicit-package-bases api/routes/documents.py api/error_handlers.py` → 0 errors on the changed lines (the ~50 reported errors are the pre-existing transitive baseline — Docling/langfuse/psycopg missing stubs, `dict`-type-arg family, Starlette `add_exception_handler` quirk, 2 pre-existing `Any`-return spots not touched).
- **T2.1 + T2.2 (F6 Option a)** — `docs/03-implementation/changes/CH-001-.../spec.md` §3 AC4 carries an inline reconcile note (as-built = `resource.not_found` via shared `_verify_kb_or_404`; acceptable; no code change; CH-001 stays `done`); §7 changelog row added.
- (commit: `feat(api): CH-002 Phase 1+2 — F5 hint key + F8 422 field detail + F2 tempfile basename + F6 CH-001 spec reconcile + tests`)

### Decisions
- F8 test: the `app` fixture model `_FeedbackLike` must be **module-level** — with `from __future__ import annotations` (PEP 563), a route function's parameter annotation is a string, and FastAPI's `get_type_hints` resolves it in module globals, not the enclosing function's locals; a function-local Pydantic model gets mis-classified (the route param became a `query.body` "Field required" error). First test attempt failed for exactly this reason → moved the model + route to module scope.
- mypy invocation: needs `--explicit-package-bases` because `backend/__init__.py` exists → otherwise "Source file found twice under different module names: backend.api and api".

### Blockers
- None.

### Effort
- Planned (Phase 1+2): ~4.25h;Actual:~2h(F5/F2 trivial; F8 + the test-fixture forward-ref debug took the bulk);Variance:−2.25h

### Commits
| Hash | Subject |
|---|---|
| `69dbe1d` | `feat(api): CH-002 Phase 1+2 — F5 hint key + F8 422 field detail + F2 tempfile basename + F6 CH-001 spec reconcile + tests` |

---

## Day 1 (cont. 2) — 2026-05-12 — Phase 3+4+5 (frontend) + Phase 6 (tests + closeout)

### Done
- **T3.x (F3 — Eval Console)** — discovered the page was **already wired** to `evalApi.run` (`useMutation` + `MetricCardsGrid` + `FailedQueriesCard`); F3 was a copy/dead-code fix, not a re-wire: removed the dead `if (err instanceof ApiError && err.status === 501)` branch (+ the now-orphan `ApiError` import); rewrote the empty-state copy ("eval-set-v0 is a W1 placeholder … eval-set-v1 pending Q14 SME labels"); updated the file-top doc comment; added a "Max main queries" number input (default 5) → `max_main_queries` arg (spec R2); added a "Running RAGAs eval — this can take a minute…" hint. `lib/api/eval.ts`: `EvalRunRequest` += `max_main_queries?`; NOTE comment updated.
- **T4.x (F7 — Chunks tab)** — `kb/[id]/page.tsx` `ChunksTab` rewritten: doc `<Select>` from `documentsApi.list` (honours `?doc=`), `<ChunksTable>` rendering `ChunkSummary` rows (index/total · title · `›`-joined section path · disabled/low-value flag badges · chunk_id), loading/empty/error states; removed the `<BackendStubNote>` placeholder + the now-orphan `BackendStubNote` component. `lib/api/documents.ts`: `ChunkSummary` interface + `documentsApi.listChunks(kbId, docId)`; stale "per-doc routes remain 501 stubs" comment updated.
- **T5.x (F10 — Settings/Identity)** — `kb/[id]/page.tsx` `SettingsTab` "Identity" section: `name` + `description` now editable inside a `<form>` + "Save identity" button → `metadataMutation` → `kbApi.patchMetadata` (true partial PATCH — only changed fields; "No changes to save" toast otherwise); invalidates `['kb', kbId]` + `['kb','list']` on success. `lib/api/kb.ts`: `kbApi.patchMetadata(kbId, {name?, description?})`. Removed the "read-only Tier 1 — PATCH lands W15+" copy; left the Pipeline-tab "Read-only Tier 1 view" copy untouched (that tab is intentionally read-only).
- **T6.x** — `traces/[traceId]/page.tsx` confirmed already-wired (no change; AC13). New Vitest: `tests/unit/eval-page.test.tsx` (3) + `tests/unit/kb-detail.test.tsx` (2). `tests/unit/setup.ts` += `ResizeObserver` stub (Radix Slider on the eval page). Fixed a now-stale parenthetical in `tests/e2e/visual-baseline.spec.ts:69`.
- **Gates** — `pnpm test:unit` → **18 passed / 6 files** (was 13 / 4); `pnpm type-check` → 0; `pnpm lint` → clean; `grep "\[oklch(" frontend/` → 0; `grep` stale-copy sweep → 0 user-facing hits (narrative file-top comments + test assertions only). `pytest tests/api/ tests/test_error_contract.py tests/test_e1_e5_e12_smoke.py tests/test_f1_7_mock_smoke.py tests/test_auth_self_register.py` → **111 passed**, 0 regression (error-handler blast radius).
- (commit: `feat(frontend): CH-002 Phase 3+4+5+6 — eval/run wired (F3) + Chunks tab (F7) + Settings-Identity edit (F10) + Vitest`)

### Decisions
- F3 scope correction: the smoke-report observation "Run 掣只 toast.info('pending W4 backend')" was imprecise — the page already called `evalApi.run` and the toast was only the *501-error branch* (dead now). So F3 became copy + dead-code cleanup + the `max_main_queries` cap, not a re-wire. Surfaced upfront (Karpathy §1.1); checklist T3.x notes reflect the narrower scope.
- F7 doc picker: `?doc=<doc_id>` is validated against the actual doc list before use (an unknown `?doc=` falls back to the first doc) — defensive against stale deep-links.
- `ResizeObserver` polyfill went into the shared `tests/unit/setup.ts` (not just the eval test) — it's standard jsdom infra any future Radix-Slider/Select-using test needs; the W18 tests just hadn't hit it.
- Vitest flake: `kb-detail` chunks test chains 3 mocked async resolutions (KB fetch → doc list → chunk list); `findByText`'s default 1000ms timeout flaked under the full-suite load → bumped to 5000ms for that one assertion.

### Blockers
- None for code. AC14 browser walkthrough = user pre-Beta smoke (R8 / CO_W15_F4 — `npx playwright install chromium` blocked) — not blocking closeout per the W15-W18 caveat pattern.

### Effort
- Planned (Phase 3-6): ~5h;Actual:~3h(F3 was smaller than scoped — already wired; F7/F10 + Vitest the bulk);Variance:−2h

### Commits
| Hash | Subject |
|---|---|
| `c2b489e` | `feat(frontend): CH-002 Phase 3+4+5+6 — eval/run wired (F3) + Chunks tab (F7) + Settings-Identity edit (F10) + Vitest` |
| _(this commit)_ | `docs(planning,catalog): CH-002 closeout — 13/14 AC ✅ + AC14 user-deferred; COMPONENT_CATALOG C08/C09 rows; frontmatter done/closed` |

---

## Closeout（status=closed）

### Acceptance verification

| AC | Status | Evidence |
|---|---|---|
| AC1 (F3 — Run → 4 metrics, no "W4 stub" copy) | ✅ | `eval/page.tsx` Run → `evalApi.run` → `MetricCardsGrid`; empty-state copy rewritten; Vitest `eval-page.test.tsx` (2 tests); grep clean |
| AC2 (F3 — `/eval/run` error → ApiError boundary) | ✅ | `onError` → `toast.error`; Vitest "surfaces a toast on eval-run failure" |
| AC3 (F7 — Chunks tab fetches `.../chunks`, renders ChunkSummary, states) | ✅ | `ChunksTab` + `ChunksTable` + `documentsApi.listChunks`; loading/empty/error states; Vitest "lists a document's chunks" |
| AC4 (F10 — Settings-Identity name/desc + Save → PATCH /kb/{id}, partial; Pipeline copy untouched) | ✅ | `SettingsTab` Identity form + `metadataMutation` + `kbApi.patchMetadata` (changed-fields-only); Vitest "renders editable name/description … PATCHes on save" |
| AC5 (F5 — dup/unsupported/not_found/mismatch → non-null `actionable_hint`) | ✅ | `documents.py` `_api_error` key `"hint"`; `error_handlers.py:82` reads it; `test_ch002_f5_route_hint_surfaces_in_error_envelope` (4-param) |
| AC6 (F8 — 422 message names field + constraint, not the input value) | ✅ | `error_handlers._redacted_loc_path`; `test_ch002_f8_validation_envelope_names_field_without_leaking_input` + `…_redacts_structured_input_value` |
| AC7 (F2 — doc_title = real stem, traversal-safe) | ✅ | `_run_ingest_pipeline` writes `mkdtemp()/<Path(filename.replace("\\","/")).name>`; `test_ch002_f2_tempfile_named_after_original_basename` + `…_upload_filename_traversal_stripped` (3-param) |
| AC8 (F6 — Option a: CH-001 spec AC4 reconcile note, status stays `done`) | ✅ | CH-001 `spec.md` §3 AC4 inline note + §7 changelog row; no code change; CH-001 frontmatter `status: done` unchanged |
| AC9 (backend regression — all green, new tests cover AC5/AC6/AC7) | ✅ | `pytest tests/api/ tests/test_error_contract.py tests/test_e1_e5_e12_smoke.py tests/test_f1_7_mock_smoke.py tests/test_auth_self_register.py` → 111 passed; +10 CH-002 test cases (4 + 1 + 3 + 2) |
| AC10 (`mypy --strict` 0 new errors; `ruff` clean) | ✅ | `ruff check` 4 changed files → clean; `mypy --strict --explicit-package-bases api/routes/documents.py api/error_handlers.py` → 0 errors on changed lines (≈50 reported = pre-existing transitive baseline, unchanged) |
| AC11 (frontend — `pnpm test:unit` green; `tsc`/`lint` clean; `[oklch(`=0) | ✅ | `pnpm test:unit` 18/6; `pnpm type-check` 0; `pnpm lint` clean; `[oklch(` grep 0 |
| AC12 (stale-stub-copy grep sweep → 0) | ✅ | sweep returns only narrative file-top comments (kept per provenance convention) + the new test files' `queryByText(...).toBeNull()` assertions; `visual-baseline.spec.ts:69` parenthetical fixed |
| AC13 (`traces/[traceId]/page.tsx` checked) | ✅ | confirmed already-wired (W16 F5.5 / ADR-0020 / W18 F3); the "501 stub" mention is a historical narrative comment, not user-facing → no change |
| AC14 (manual/Playwright browser walkthrough) | 🟡 user-deferred | backend curl smoke covered by pytest (AC5-AC8); the 3-frontend-flow browser walkthrough = user pre-Beta smoke — R8 `npx playwright install chromium` blocked / CO_W15_F4 / ADR-0017; consistent with the W15-W18 caveat pattern, not blocking closeout |

**Verdict**: 13/14 ✅ + 1/14 🟡 (AC14 user-deferred, same umbrella as W15-W18). No ❌. CH-002 **CLOSED 2026-05-12**.

### Effort summary
| Day | Planned (h) | Actual (h) | Variance |
|---|---|---|---|
| Day 1 (triage + spec + checklist + progress) | 0.5 | 0.75 | +0.25 |
| Day 1 cont. (Phase 1+2 backend) | 4.25 | 2 | −2.25 |
| Day 1 cont. 2 (Phase 3-6 frontend + tests + closeout) | 5 | 3 | −2 |
| **Total** | **~9.75** | **~5.75** | **−4** |

(Under the spec §5 6-9h estimate's upper bound — F3 was already-wired so it collapsed to copy/dead-code; F5/F2 were near-trivial; F8 + the Vitest forward-ref/ResizeObserver debugging took the most actual time.)

### Lessons
- **What worked**: reading the target files before scoping (Karpathy §1.1) — caught that the eval page was already wired, so F3 didn't balloon; the `with_error_handlers=True` flag on `_build_app` let F5 be tested end-to-end without rewriting CH-001's 24 tests.
- **What didn't / friction**: `from __future__ import annotations` + a function-local Pydantic model used as a FastAPI route param annotation → FastAPI's `get_type_hints` can't resolve the forward ref → the param gets mis-classified (`query.body — Field required`); fix = module-level model. `ResizeObserver` missing in jsdom (Radix Slider). mypy needs `--explicit-package-bases` (there's a `backend/__init__.py`). All one-time gotchas, now documented here.
- **Carry-overs**: none new from CH-002. Out-of-scope items (F1 setup-doc / `settings.py` env_file, F4 favicon, F9 `/dashboard` 375px overflow → BUG-NNN, F11 chat focus-mode toggle → W18-impl verify) remain per spec §2.4 — separate handling.

### Component design note status updates
- C01 / C06 / C08 / C09 — no `components/Cn-*.md` design-note file exists for any of them (rolling JIT; none was created). No status bump. `COMPONENT_CATALOG.md` got a C08 + C09 status row appended (see closeout commit).

---

**End of CH-002 progress**

### Acceptance verification
_(All §3 acceptance criteria from spec.md verified ✅ / partial ⚠️ / failed ❌ — fill at closeout)_

### Effort summary
| Day | Planned (h) | Actual (h) | Variance |
|---|---|---|---|

### Lessons
- _(fill at closeout)_

### Component design note status updates
- _(fill at closeout — likely none; C01/C06/C08/C09 notes rolling JIT)_

---

**End of CH-002 progress**
