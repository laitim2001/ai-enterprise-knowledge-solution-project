---
change_id: CH-002
title: "Close W16-F5 frontend gaps (eval run / chunks list / KB identity edit) + restore CH-001 error-envelope hints + 422 field detail + doc-title fix"
status: done              # draft | proposed | approved | active | done | cancelled
created: 2026-05-12
approved: 2026-05-12
completed: 2026-05-12
target_completion: 2026-05-13
affects_components: [C01, C06, C08, C09]   # C01 Ingestion (parser doc_title source) + C06 Eval (frontend Eval Console wiring) + C08 API Gateway (error_handlers hint + 422 detail) + C09 Admin Console UI (eval / chunks / identity views)
spec_refs:
  - architecture.md v6 §3.3              # Ingestion — parser ParserResult.doc_title
  - architecture.md v6 §3.7              # (auth-transport note context for error envelope)
  - architecture.md v6 §4.4              # API endpoints — /eval/run, GET .../chunks, PATCH /kb/{id}, documents upload
  - architecture.md v6 §5                # UI views — Eval Console (V5), KB detail (Chunks + Settings tabs)
  - architecture.md v6 §7.3              # E1-E14 error contract (ApiError envelope shape)
  - components/C01-ingestion.md          # IngestionOrchestrator + parsers
  - CH-001 spec.md §3 (AC4)              # the "kb.not_found" code text this Change reconciles (F6)
  - session-start.md §11                 # W16 F5 backend stub closures + CH-001 closeout context
  - Deep Smoke v2 report 2026-05-12      # findings F2 / F3 / F5 / F6 / F7 / F8 / F10 origin
---

# CH-002 — Close W16-F5 frontend gaps + restore CH-001 error-envelope hints + 422 field detail + doc-title fix

> **Spec version**:1.0(initial)
> **Owner**:AI(implementer)/ Chris(approver)
> **Approved by**:Chris(2026-05-12)— **Decision F2 = Option A**(route preserves original basename)· **Decision F6 = Option a**(CH-001 spec inline reconcile note,no code change)

---

## 1. Context (Why)

### 1.1 Trigger

Deep Smoke v2(2026-05-12,Playwright + curl + Azure-direct + JS-eval pass)揭示 **11 個 minor finding(F1–F11,無 functional blocking bug)**。其中 **7 個**(F2 / F3 / F5 / F6 / F7 / F8 / F10)落入同一個 batch — "**後端 W16 F5 stub-closure 做咗 + CH-001 做咗,但前端對應 view 嘅 copy 未追上 + 冇 wire**,加幾個細 error-envelope/UX 修正"。用戶指示:批 A(frontend catch-up)+ 批 B(backend 小修)一齊做,一個 PR。

> **不在本 Change**:F1(`settings.py` env_file CWD-relative — config/docs,Trivial)、F4(favicon — Trivial)、F9(`/dashboard` 375px 橫向 overflow — 細 responsive bug,屬 Bug-fix BUG-NNN)、F11(chat focus-mode toggle 揾唔到 — 待確認 W18 implementation,可能 descoped)。呢 4 個另外處理。

### 1.2 Diagnosis(逐 finding)

| Finding | Root cause | Fix direction |
|---|---|---|
| **F2** doc-title 顯示 tempfile stem | 3 個 parser(`docx_parser.py:57,150` / `pdf_parser.py:64,157` / `pptx_parser.py:54,134`)都 `doc_title=source.stem`;`POST /kb/{kb}/documents` route 用 `tempfile.NamedTemporaryFile` 寫,`source.stem` = `tmpXXXX`,原 filename 丟失 | route 寫 tempfile 時保留原 basename(Option A,recommended)或 thread `original_filename` 落 orchestrator → parsers(Option B)— see §2.3 |
| **F3** `/eval` Eval Console 仲 show "`/eval/run` is W4 stub — pending implementation" + Run 掣只 `toast.info('pending W4 backend implementation')` | `frontend/app/(app)/eval/page.tsx` 整個 view 建喺「`/eval/run` 返 501 stub」嘅假設上(file-top doc line 18-19);但 backend 已喺 **W16 F5.4 + W17 F3** 真 wire RAGAs 4-metric(`POST /eval/run` → 200 `EvalReport`,smoke C1 真跑驗證 recall_at_5 / faithfulness / correctness / image_association / p95_latency_ms + failed_queries) | wire Run 掣 → `POST /eval/run`;render 真 `EvalReport`(已有 4-metric display component,只需換 data source);移除 "W4 stub" copy + 解釋 eval-set-v0 placeholder 低分原因 |
| **F5** CH-001 `_api_error`-built error codes(`document.duplicate` / `validation.unsupported_format` / `document.not_found` / `reindex.doc_id_mismatch`)`actionable_hint` = `null` | `documents.py:160` 傳 `detail={"code": code, "message": message, "actionable_hint": hint}` — 但 global handler `error_handlers.py:82` 讀 `exc.detail.get("hint")`(key 係 `"hint"` 唔係 `"actionable_hint"`,W13 F5 established convention)→ hint 被 drop → fallback `_HINTS.get(code)` → 呢啲 code 唔喺 `_HINTS` map → `null` | `documents.py:160` `"actionable_hint"` → `"hint"`(one-liner;route 已傳真實 hint,只係 key 寫錯) |
| **F6** CH-001 spec AC4 講 unknown kb → `code: "kb.not_found"`,實際 = `resource.not_found` | document routes 重用 pre-existing `_verify_kb_or_404` helper(`documents.py:105-113`)— raise `HTTPException(404, detail="KB '...' not found")` plain-string detail → global handler `_STATUS_TO_CODE[404]` = `RESOURCE_NOT_FOUND` generic map | **Option (a) recommended**:amend CH-001 spec AC4 inline note 講「actual impl = `resource.not_found` via shared `_verify_kb_or_404`;acceptable — message text already says which KB」;**Option (b)**:document routes 內 explicit `kb.not_found` check(+ add `KB_NOT_FOUND` to `ErrorCodes`)— 但會偏離 surgical-change(`_verify_kb_or_404` 係 shared helper,改佢影響其他 route)— see §2.3 |
| **F7** KB detail **Chunks tab** 仲 show "GET /kb/{id}/documents/{id}/chunks — W2 chunk listing implementation (501 stub)" + "pending backend list endpoint" + 冇 fetch | `frontend/app/(app)/kb/[id]/page.tsx:414-423`(`StubTab` with `stub=` / `issue=` props)— 但 backend `GET /kb/{kb}/documents/{doc_id}/chunks` 已喺 **W16 F5.1.2** 做咗(`chunks.py` replaced 501 stub,返 200 `ChunkSummary` list:chunk_id / section_path / chunk_title / chunk_index / chunk_total / enabled / low_value_flag;smoke A7 驗證 11 chunks correct) | wire Chunks tab → `GET .../chunks`,render `ChunkSummary` list table;移除 "501 stub" copy(可選:listing route 加 `chunk_text` preview — **out of scope**,見 §2.4) |
| **F8** `validation.invalid_payload` 422 把 Pydantic field-level errors collapse 成 generic "Request payload failed validation. Check the request body shape and retry." | `error_handlers.py:106-124` `validation_exception_handler` 故意 drop field 資料(H5 redaction — 避免 leak input value);但連 field **location**(唔係 value)都冇 surface → caller 唔知邊個 field 錯(e.g. `/feedback` `rating` 只能 thumbs_up/thumbs_down) | message 加 field `loc`(path only,非 value — `loc` 唔係 user input,redaction-safe):e.g. `"Request payload failed validation: body.rating — input should be 'thumbs_up' or 'thumbs_down'"`(`first.get("loc")` + `first.get("msg")`,仍唔 echo `first.get("input")`) |
| **F10** KB detail **Settings tab "Identity"** 仲 show "Display fields are read-only Tier 1 — backend `name` / `description` PATCH lands W15+ per CO_W15 follow-up" + 冇 save affordance | `frontend/app/(app)/kb/[id]/page.tsx:964-965` — 但 backend `PATCH /kb/{id}`(metadata,name+description)已喺 **W16 F5.2** 做咗(CO_F3b closed;smoke D1 驗證 partial PATCH 正確) | Settings-Identity section 加 name + description edit field + Save → `PATCH /kb/{id}`;移除 "PATCH lands W15+" copy(Pipeline tab line 449 "Read-only Tier 1 view" **唔改** — 嗰個 tab 設計上 read-only,editable 嘅係 Settings tab) |

### 1.3 The pattern

F3 / F7 / F10 同根:**W16 F5 backend stub-closure cascade(2026-05-09/10)+ CH-001(2026-05-12)做咗後端,前端 stub-mitigation UI 未拆**。本 Change 統一收。F5 / F8 / F2 / F6 係順手嘅 error-envelope / UX / spec-reconcile 修正,bundle 同一 PR 減 review overhead(用戶指示)。

### 1.4 Why a Change task(not Bug-fix / Trivial)

- F3 / F7 / F10:behavior change(stub UI → real wiring),涉 frontend data-fetch flow + 多文件 → Change,非 Trivial
- F5:雖係 regression(CH-001 引入),但一行 key 名修正,bundle 入呢個 Change 唔開獨立 BUG-NNN(用戶已 group)
- F2 / F8:UX behavior change(顯示更多有用資料)→ Change
- F6:spec/impl reconcile → spec amend 或 micro code change,bundle
- 預估 1-2 日 → CH-NNN workflow(< 3 日 per PROCESS.md §3)✅

---

## 2. Scope (What)

### 2.1 Behavior Change

**A — Frontend(C09 / C06)**:

| View | Before | After |
|---|---|---|
| `/eval` Eval Console(`eval/page.tsx`)| Run 掣 → `toast.info('pending W4 backend implementation')`;empty-state 寫 "`/eval/run` is W4 stub" | Run 掣 → `POST /eval/run {eval_set_id, max_main_queries?, enable_crag?}` → render `EvalReport`(recall_at_5 / faithfulness / correctness / image_association / p95_latency_ms + `failed_queries` table + `_metrics_deferred_note`);error → 既有 `ApiError` boundary;empty-state copy 改為解釋「Run 一次 eval 即見結果;eval-set-v0 係 placeholder,真 ground truth 待 `eval-set-v1` (Q14)」 |
| `/kb/[id]` Chunks tab(`kb/[id]/page.tsx`)| `StubTab stub="GET .../chunks" issue="W2 chunk listing implementation"` + 冇 fetch | `GET /kb/{kb}/documents/{doc_id}/chunks` → table of `ChunkSummary`(chunk_index/chunk_total · chunk_title · section_path breadcrumb · enabled · low_value_flag badge);empty / loading / error states;需要先選一個 document(doc picker 或從 Documents tab deep-link `?doc=<doc_id>`)|
| `/kb/[id]` Settings tab "Identity"(`kb/[id]/page.tsx:~964`)| "read-only Tier 1 — PATCH lands W15+";冇 save | name + description editable input + "Save identity" 掣 → `PATCH /kb/{id} {name?, description?}`(partial)→ optimistic update + toast;copy 移除 "PATCH lands W15+" |

**B — Backend(C08 / C01)**:

| Item | Before | After |
|---|---|---|
| `documents.py:160` `_api_error` detail | `{"code", "message", "actionable_hint": hint}` — key mismatch,hint dropped by handler | `{"code", "message", "hint": hint}` — handler `error_handlers.py:82` 正確讀取 → `actionable_hint` surface |
| `error_handlers.py` `validation_exception_handler` | message = generic "Request payload failed validation." | message = `"Request payload failed validation: {loc} — {msg}"`(`loc` = dotted path e.g. `body.rating`,**唔 echo `input` value** — H5 redaction preserved)|
| 3 parsers `doc_title=source.stem` + `documents.py` upload route tempfile | tempfile `tmpXXXX.docx` → `doc_title = "tmpXXXX"` | route 寫 tempfile 用原 basename(`Path(upload_file.filename).name`,sanitized into a fresh `mkdtemp()` dir)→ `source.stem` = 真 stem → `doc_title` 正確(Option A — see §2.3)|
| CH-001 spec AC4(F6)| spec text 講 `kb.not_found` | **per §2.3 decision**:Option (a) spec inline note reconcile,OR Option (b) route emits `kb.not_found` |

### 2.2 In Scope

1. `frontend/app/(app)/eval/page.tsx` — wire `POST /eval/run`,render `EvalReport`,update copy(F3)
2. `frontend/app/(app)/kb/[id]/page.tsx` — Chunks tab wire `GET .../chunks` + render `ChunkSummary` list + update copy(F7);Settings-Identity name/description edit + `PATCH /kb/{id}` + update copy(F10)
3. `frontend` API client / types — add `evalRun()` + `listChunks()` + `patchKbIdentity()` calls + `EvalReport` / `ChunkSummary` TS types(match backend Pydantic schemas)
4. `backend/api/routes/documents.py:160` — `"actionable_hint"` → `"hint"`(F5)
5. `backend/api/error_handlers.py` `validation_exception_handler` — add `loc` + `msg` to message,no `input`(F8)
6. `backend/api/routes/documents.py` upload route — write tempfile with original basename(F2 Option A);if §2.3 picks Option B → also `IngestionOrchestrator.ingest()` + 3 parsers + `base.py` signature change
7. F6 — per §2.3 decision:(a)`docs/03-implementation/changes/CH-001-.../spec.md` §3 AC4 inline reconcile note(does NOT re-open CH-001 status — it's a documentation reconcile),OR (b)`backend/api/routes/documents.py` explicit `kb.not_found` + `ErrorCodes.KB_NOT_FOUND`
8. Tests:add to `backend/tests/api/test_documents_route.py` — F5(upload-dup error has non-null `actionable_hint`)+ F2(doc_title = original stem not tempfile);add to `backend/tests/api/test_error_handlers.py`(或既有 error-handler test file)— F8(422 message includes `loc`, excludes `input`);frontend Vitest — eval-page Run-flow + chunks-tab render + identity-save(RTL,mocked fetch)— scope per §5
9. `frontend/app/(app)/traces/[traceId]/page.tsx` — grep hit on the keyword search; **verify only** whether it has a stale stub copy too(if yes, fold in; if it's already wired per W16 F5.5 `debug/trace/{id}`, skip)

### 2.3 Design choices — RESOLVED at approval (2026-05-12)

> **Decision F2 = Option A**(route preserves original basename). **Decision F6 = Option a**(CH-001 spec inline reconcile note, no code change). The Option-B / Option-b text below is retained for the record only.

**Decision F2 — tempfile basename(recommended Option A)vs thread `original_filename`(Option B)**:
- **(A) recommended**:upload route writes the uploaded bytes to `<mkdtemp()>/<Path(filename).name>` instead of `NamedTemporaryFile(suffix=ext)`. `source.stem` becomes the real stem → `doc_title` correct with **zero parser/orchestrator signature change**(most surgical;`source.stem` is already the intended semantics). Cleanup: `shutil.rmtree(tmpdir)` in `finally`.
- **(B)**:add `original_filename: str | None = None` to `IngestionOrchestrator.ingest()` → pass to each parser's `parse()` → parser uses it for `doc_title` when set. More invasive(orchestrator + 3 parsers + `Parser.parse` signature + `base.py`)but decouples parser from filesystem-path semantics. Probably overkill for Tier 1 per Karpathy §1.2.
- → **default = (A)** unless approver prefers (B).

**Decision F6 — spec reconcile(recommended Option a)vs route emits `kb.not_found`(Option b)**:
- **(a) recommended**:add an inline note to CH-001 spec.md §3 AC4: "实际 impl 用 shared `_verify_kb_or_404` → `resource.not_found`(message text already names the KB);spec's `kb.not_found` 文字 was aspirational — acceptable, no code change". CH-001 status stays `done`(this is a doc reconcile, not a re-open). Surgical — touches nothing in code.
- **(b)**:document routes do an explicit KB-existence check raising `_api_error("kb.not_found", ...)` instead of `_verify_kb_or_404`; add `KB_NOT_FOUND = "kb.not_found"` to `ErrorCodes`. But `_verify_kb_or_404` is shared(used by upload + delete + reindex routes — would need all 4 changed)→ more diff for marginal benefit. Frontend doesn't branch on `kb.not_found` vs `resource.not_found` anyway(both → "verify the id" hint).
- → **default = (a)** unless approver prefers (b).

### 2.4 Out of Scope（explicit — won't change）

- **F1**(`settings.py` env_file CWD-relative + `docs/setup.md` backend-start note)— Trivial, separate commit
- **F4**(favicon)— Trivial, separate commit
- **F9**(`/dashboard` 375px horizontal overflow)— Bug-fix, separate BUG-NNN(CSS audit)
- **F11**(chat focus-mode toggle)— pending W18-impl verification, possibly descoped; separate investigation
- **Chunks listing `chunk_text` preview** — backend `GET .../chunks` returns `ChunkSummary` (no body text); adding a `?include_text=` param or a per-chunk-detail endpoint is a backend Change of its own — NOT in CH-002(Chunks tab shows metadata only, matches current backend contract)
- **Chunk enable/disable toggle write-path**(`PATCH .../chunks/{chunk_id}`)— if not already wired backend-side, that's W16 F5.3 scope, NOT CH-002(CH-002's Chunks tab is read-only render)
- **Backend `/eval/run` behavior** — unchanged; CH-002 only consumes it from the frontend
- **`eval-set-v1.yaml`** — CO_W15_F1_eval_set_v1 still OPEN(needs Q14 SME labels); CH-002 does not fabricate ground truth, only wires the existing eval-set-v0 placeholder run
- **Dashboard "system health" / "recent queries" / "latest evaluation" cards** — W18 closeout follow-ups, not CH-002

---

## 3. Acceptance Criteria

Verifiable "done" conditions:

- [ ] **AC1**(F3)— `/eval` Run 掣 → real `POST /eval/run`;200 → 4-metric values + `failed_queries` table render;`tsc` + `lint` clean;前端再無 "W4 stub" / "pending implementation" copy(grep `frontend/app/(app)/eval/page.tsx` for `W4 stub` → 0 hits)
- [ ] **AC2**(F3)— `/eval/run` error path(e.g. unknown `eval_set_id`)→ existing `ApiError` boundary renders the envelope `message` + `actionable_hint`(no white-screen)
- [ ] **AC3**(F7)— `/kb/[id]` Chunks tab fetches `GET /kb/{kb}/documents/{doc_id}/chunks`;200 → `ChunkSummary` rows(index/total · title · section breadcrumb · enabled · low_value_flag);loading + empty + error states present;grep `kb/[id]/page.tsx` for `501 stub` near Chunks tab → 0 hits
- [ ] **AC4**(F10)— `/kb/[id]` Settings-Identity has name + description inputs + Save → `PATCH /kb/{id}`;partial update works(send only name → description preserved);toast on success;grep for `PATCH lands W15` → 0 hits;Pipeline-tab "read-only" copy **unchanged**
- [ ] **AC5**(F5)— `POST /kb/{kb}/documents` with a duplicate doc_id → 409 envelope where `actionable_hint` is **non-null** and matches the route-supplied hint("doc_id='...' already exists ..."); same for `validation.unsupported_format`(.txt → 422)/ `document.not_found`(DELETE missing)/ `reindex.doc_id_mismatch`(reindex wrong filename)
- [ ] **AC6**(F8)— a 422 from a Pydantic-validated endpoint(e.g. `POST /feedback` with `rating="bad"`)→ envelope `message` contains the field path(`body.rating`)and the constraint(`thumbs_up`/`thumbs_down`)but **does NOT contain the bad value `"bad"`**(H5 redaction grep: response body must not echo `input`)
- [ ] **AC7**(F2)— `POST /kb/{kb}/documents` with `file=("My Report 2026.docx", <bytes>)` → the doc's `doc_title` (visible in `GET /kb/{kb}/documents` listing and in Chunks `section_path` / via the Documents tab "Title" column) is `"My Report 2026"`(or the document's internal title), **never `tmpXXXX`**
- [ ] **AC8**(F6)— per §2.3: if Option (a) → CH-001 spec.md §3 AC4 carries the reconcile note + CH-001 status still `done`; if Option (b) → unknown-kb upload/delete/reindex returns `code: "kb.not_found"` and `ErrorCodes.KB_NOT_FOUND` exists
- [ ] **AC9** — backend regression: `pytest backend/tests/api/` → all green(70 prior CH-001-era + new CH-002 tests), 0 regression; new tests cover AC5 / AC6 / AC7
- [ ] **AC10** — `mypy --strict` on changed backend files → 0 new errors(transitive baseline unchanged); `ruff check` clean
- [ ] **AC11** — frontend: `pnpm test:unit` green(existing 13 + new CH-002 RTL tests per §5); `tsc` + `lint` clean; `[oklch(` grep in `frontend/` → still 0(milestone preserved)
- [ ] **AC12** — verification command sweep: `grep -rn "W4 stub\|501 stub\|PATCH lands W15\|pending backend list endpoint\|pending implementation per docs/eval" frontend/` → 0 hits(all stale stub copy removed)
- [ ] **AC13**(F9 of §2.2 In-Scope item 9)— `traces/[traceId]/page.tsx` checked: either confirmed already-wired(no change)or stale copy folded in
- [ ] **AC14** — manual / Playwright smoke(user pre-Beta backlog — same deferral umbrella as W15-W18): the 3 frontend flows clicked through against a running backend. Backend curl smoke = AC1-AC8 covered by pytest; the browser walkthrough is the user-deferred portion(R8 / CO_W15_F4 — not blocking CH-002 closeout per the established caveat pattern)

---

## 4. Risks

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | F2 Option A — writing tempfile with the original basename re-introduces a path-traversal vector if `filename` contains `../` or absolute path | Low | Med | `Path(upload_file.filename).name` strips all directory components; write only into a fresh `tempfile.mkdtemp()` dir; `shutil.rmtree` in `finally`. Add a test with `filename="../../etc/passwd.docx"` → must land as `passwd.docx` in the temp dir, never escape |
| R2 | `/eval/run` against the real `ekp-kb-drive-v1` Azure index takes seconds-to-minutes(LLM-judge per query) — a synchronous frontend `fetch` may hit a browser/proxy timeout | Med | Low | `max_main_queries` is a request param — default the frontend form to a small N(e.g. 3-5); show a loading spinner with "this can take a minute"; the backend already returns the full report when done(no streaming needed for Tier 1) |
| R3 | Chunks tab needs a `doc_id` to query — if the route group has no doc picker, the tab is dead unless deep-linked | Med | Low | Add a lightweight doc `<Select>` populated from `GET /kb/{kb}/documents`(already wired W17 F4.1), default to first doc; also honor `?doc=<doc_id>` from a Documents-tab "View chunks" link |
| R4 | Frontend `EvalReport` / `ChunkSummary` TS types drift from backend Pydantic schemas | Low | Med | Hand-mirror the Pydantic fields exactly(name + type); reference the schema file path in a comment; covered by the RTL test asserting the rendered fields |
| R5 | F8 — including `loc` in 422 messages accidentally leaks input on some Pydantic error types where `loc` embeds a value(rare, e.g. discriminated unions) | Low | Low | Only join `loc` elements that are `str` or `int`(field names / list indices), never dict/value fragments; the test asserts the bad `input` string is absent from the response body |
| R6 | Touching `eval/page.tsx` / `kb/[id]/page.tsx` tempts adjacent refactor(Karpathy §1.3 surgical) | Med | Low | Diff discipline: only the stub→wire delta + copy edits; no restyle, no component extraction unless the wiring genuinely needs it; reviewer checks every line traces to a finding |
| R7 | `pnpm test:e2e` / Playwright browser walkthrough still R8-blocked → AC14 stays user-deferred | High | Low | Accept the established caveat pattern(W15-W18): backend curl/pytest covers the contract; the browser pass is the user's pre-Beta smoke. Phase Gate = PASS WITH SMOKE-USER-DEFERRED CAVEAT if that's the only open AC |

---

## 5. Effort Estimate

**~6-9 hours of focused work**:
- Backend F5(key fix)+ test — 0.5h
- Backend F8(422 detail)+ test — 1h
- Backend F2 Option A(tempfile basename)+ test(incl. traversal test)— 1h
- F6 Option (a) spec reconcile note — 0.25h(Option (b) would be ~1h instead)
- Frontend F3(eval wire + render + copy)— 2-3h(depends on how much of the 4-metric display component is reusable as-is)
- Frontend F7(chunks tab wire + doc picker + render + copy)— 1.5-2h
- Frontend F10(identity edit + PATCH + copy)— 1h
- Frontend Vitest/RTL — eval Run-flow happy + error, chunks-tab render, identity-save — 1-1.5h
- Docs(checklist tick + progress Day-N + COMPONENT_CATALOG note if warranted)— 0.5h

Sequencing(per Karpathy §1.4 goal-driven):
1. Backend F5 + F8 + F2 + tests → verify: `pytest backend/tests/api/` green
2. F6 reconcile → verify: CH-001 spec note in place(or `kb.not_found` test green)
3. Frontend F3 → verify: Run real `/eval/run`, report renders; `tsc`/`lint` clean
4. Frontend F7 → verify: chunks list renders for a real doc; states present
5. Frontend F10 → verify: partial PATCH works, copy gone
6. Vitest/RTL → verify: `pnpm test:unit` green
7. Grep sweep AC12 → verify: 0 stale-copy hits
8. Docs closeout

---

## 6. Dependencies

### 6.1 External work — already landed, verify only
- `POST /eval/run` real RAGAs 4-metric(W16 F5.4 + W17 F3)— verified live in Deep Smoke v2 C1 ✅
- `GET /kb/{kb}/documents/{doc_id}/chunks` → 200 `ChunkSummary` list(W16 F5.1.2)— verified live A7 ✅
- `PATCH /kb/{id}` metadata(W16 F5.2)— verified live D1 ✅
- `GET /kb/{kb}/documents` listing(W17 F4.1)— used by the Chunks-tab doc picker
- CH-001 document routes(POST upload / DELETE / reindex)— closed, the F5/F2 fixes touch `documents.py` which CH-001 wired

### 6.2 OQ
- No Open OQ blocks CH-002. `eval-set-v0` placeholder is used as-is(CO_W15_F1_eval_set_v1 OPEN — not a blocker, explicitly out of scope §2.4).

### 6.3 No new dependency(H2 — verified)
- Backend: `shutil` / `tempfile` / `pathlib` are stdlib. No vendor change.
- Frontend: `useChat` / TanStack Query / shadcn already in stack — eval Run uses a plain `fetch`/TanStack `useMutation`, no new lib.

### 6.4 No architectural change(H1 — verified)
- No §3 / §4 component added/removed/swapped; no storage layout change; no KB-id namespacing change; no view redesigned(Eval Console / KB-detail tabs already exist per architecture.md v6 §5 — this is wiring + copy, not a layout change). Error envelope shape `{code, message, actionable_hint}` unchanged — F5/F8 only change *which value* fills `actionable_hint`/`message`, not the schema.

### 6.5 Components touched(per COMPONENT_CATALOG CC-1)
- **C01** Ingestion — parser `doc_title` source(F2)
- **C06** Eval Framework — frontend Eval Console consumes `/eval/run`(no backend change)
- **C08** API Gateway — `error_handlers.py`(F5/F8)+ `documents.py`(F5/F2)
- **C09** Admin Console UI — eval / kb-detail views(F3/F7/F10)

### 6.6 No ADR
- Nothing here is architectural-adjacent per H1 — no ADR required(F6 is a spec-text reconcile, not an architecture decision). If approver picks F6 Option (b)(new `kb.not_found` code), that's still within the existing error-contract — a `docs(...)` note in CH-001 spec changelog suffices, no ADR.

---

## 7. Spec Changelog（deviation log）

| Date | Change | Reason | Approver |
|---|---|---|---|
| 2026-05-12 | Initial draft(v1.0)— bundle Deep Smoke v2 findings F2/F3/F5/F6/F7/F8/F10 | User instruction: batch A(frontend W16-F5 catch-up)+ B(backend small fixes)in one PR | — |
| 2026-05-12 | Approved — `status: proposed → approved`; **Decision F2 = Option A**, **Decision F6 = Option a** | Approver pick | Chris |

---

**Lifecycle reminder**:呢份 spec 由 2026-05-12 起 locked(`status=approved`)。重大 deviation 入 §7 changelog(R3 per PROCESS.md §5)。Design decisions locked:**F2 = Option A**,**F6 = Option a**。
