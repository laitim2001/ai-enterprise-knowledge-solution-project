---
change_id: CH-002
spec_ref: ./spec.md
checklist_ref: ./checklist.md
status: in-progress     # in-progress | closed
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
| _(pending)_ | `feat(api): CH-002 Phase 1+2 — F5 hint key + F8 422 field detail + F2 tempfile basename + F6 CH-001 spec reconcile + tests` |

---

## Closeout（填於 status=closed）

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
