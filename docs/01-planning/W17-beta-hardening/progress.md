---
phase: W17-beta-hardening
plan_ref: ./plan.md
checklist_ref: ./checklist.md
status: active
last_updated: 2026-05-10
---

# Phase W17 — Progress

> Daily log + decisions + commits + closing retro。每 commit 對應一個 Day-N entry mention(R2;`docs(planning):` housekeeping exempt)。
> Plan deviation → `plan.md` §7 changelog（R3）。OQ resolved → `decision-form.md` + Day-N mention（R4）。

---

## Day 0 — Kickoff(2026-05-10)

### Trigger

User directive — after the W16 audit-tail browser-smoke session(`84d030e` CORS + `3a509c4` §13 policy + `adb89e5` progress entry,pushed):「先完整地規劃和處理 類別 1（AI 可即做，無 H1/H2，無外部依賴）+ 類別 2（要先決策 / ADR）」。Category-3 Track-A-blocked items explicitly excluded(stay W16 F1-F4). W17 runs in parallel with W16's blocked state — does not depend on W16 closeout.

### H1/H2 decisions(AskUserQuestion 2026-05-10)

- **Persistent storage backend** = **Postgres via `psycopg`**(option C)— docker-compose already has a postgres service(Langfuse);add a dedicated `ekp` database. New dep → H2 + ADR-0023.
- **httpOnly cookie hardening** = **do-now-in-W17**(write ADR + implement)— auth-transport change, touches ADR-0014 → ADR-0022.
- These two answers = the「approved + write ADR」authorization per CLAUDE.md §5.1 H1 / §5.2 H2.

### Pre-kickoff exploration findings(grounding the plan)

- `GET /kb/{id}/documents` is **already implemented** backend-side(W16 F5.1.1 CO_F3a — `engine.list_documents(kb_id)` aggregates Azure AI Search chunks by doc_id → `list[DocumentSummary]`). The「501 stub」text seen in the KB-detail Documents tab is **stale frontend copy** — W17 F4.1 wires the real call + drops the copy. Other doc endpoints(per-doc upload/reindex/delete)remain 501 stub(W2 ingestion + Track A — out of W17).
- `backend/kb_management/storage.py` = `KBStorageBackend` Protocol + `InMemoryKBBackend`(docstring already anticipates a swappable backend)— `PostgresKBBackend` satisfying the same Protocol + dependency-override is the clean path. `backend/api/auth/users_repo.py` similar.
- Backend venv:`ragas` **installed**(RAGAs integration feasible — no H2);`sqlalchemy` installed(transitive);`aiosqlite` / `psycopg` / `azure-cosmos` **missing**(psycopg to be added per ADR-0023).
- `frontend` has `@radix-ui/react-select` / `react-slider` / `react-switch` etc(W17 inherits the ADR-0021 RetrievalTab — no re-work).

### Setup completed Day 0

- `docs/01-planning/W17-beta-hardening/{plan,checklist,progress}.md` created — `status: active`(per user directive, not the usual draft→active flip — the directive *is* the authorization)
- Plan §2 deliverables F0-F7:F0 = ADR-0022 + ADR-0023(H1/H2 gate);F1 = Postgres backing;F2 = cookie/CSRF/refresh;F3 = RAGAs 4-metric;F4 = frontend hardening bundle;F5 = a11y + dark-mode verify;F6 = Vitest/RTL scaffold;F7 = closeout
- W16 F1-F4 sequence preserved — W17 is a parallel track, not a successor phase(rolling-JIT note: W17 folder created at kickoff per R1;W18+ NOT pre-created)

### Carry-overs addressed by W17(from session-start.md §11 + W16 progress)

| Carry-over | W17 deliverable |
|---|---|
| CO18 KB Manager + users_repo persistent backing | F1(ADR-0023)|
| CO_F5_refresh `/auth/refresh` rotation | F2.2 |
| CO_F5_cookie httpOnly cookie hardening | F2(ADR-0022)|
| CO_W15_F1_backend RAGAs deferral | F3 |
| CO_W15_F1_eval_set_v1 file verify | F3.4 |
| CO_W15_F2_langfuse_url Beta env var | F4.3 |
| CO_W15_F3_dark_mode_visual_verify | F5.1 |
| CO_W15_F4_vitest_baseline_gap | F6 |
| `admin/page.tsx` `CardTitle` lint orphan | F4.2 |
| Cohere reranker naming inconsistency | F4.4 |

NOT addressed(stay W16 / W18+ / Tier 2):CO16 Track A IT cred(W16 F1)/ CO19 25% rollout(W16 F2)/ CO17 AF3 fix(ADR-0013 reserved)/ CO_F6a-c ACS email(Track A)/ CO_W15_F3_aria_full_audit + CO_W15_F4_interactive_flow_E2E(Tier 2)/ Azure DELETE cleanup(Track A).

### Pre-condition checks(per CO_W14_process_grep_verify FORMALIZED 5-step — plan-author spec-ref grep verification before active flip)

1. Read plan literal acceptance criteria ✅
2. Grep code base for referenced files / functions / patterns — done(see「Pre-kickoff exploration findings」above:`GET /kb/{id}/documents` already impl / `KBStorageBackend` Protocol exists / `ragas` installed / etc)
3. Surface mismatches upfront ✅(the「501 stub」stale-copy finding → F4.1 reframed from「implement backend」to「wire frontend + drop stale copy」)
4. Document deviations in plan §7 changelog at kickoff ✅(initial-draft entry)
5. Adjust acceptance criteria per actual reality ✅(F4.1 reframed;F3.2 notes the W16 F5.4 minimal-impl placeholder it replaces)

### Day 0 commits

- **`86a4403`** `docs(planning)` — W17-beta-hardening phase folder kickoff(plan + checklist + progress.md Day 0;rolling-JIT per CLAUDE.md §10 R1)
- **`6edd9ef`** `docs(adr)` — ADR-0022 auth-transport hardening(`Accepted`)+ ADR-0023 KB Manager persistent backing(`Accepted`)+ README index(next NNNN → 0024) — **F0 complete**(H1/H2 gate cleared)

---

## Day 1 — F4 frontend hardening bundle(2026-05-10)

> Same-calendar-day as Day 0 — F4 is the「trivials first」start per the user directive「(A) 直接開工(F4 trivials 先,然後 F1)」。F0 ADRs landed Day 0;F1 Postgres starts after F4.

### F4 — landed `9ee636c` `feat(frontend,api)`

- **F4.1** — KB-detail Documents tab(`frontend/app/admin/kb/[id]/page.tsx`)now calls the real `GET /kb/{id}/documents`(backend already implemented W16 F5.1.1 / CO_F3a — Azure AI Search chunk aggregation by doc_id;the「501 stub」was stale *frontend* copy, not a missing backend route — surfaced upfront per the Day-0 pre-kickoff exploration). NEW `frontend/lib/api/documents.ts`(`DocumentSummary` interface + `documentsApi.list(kbId)`). `DocumentsTab` rewritten:`useQuery(['kb', kb_id, 'documents'])` → `DocumentsTable`(title + tags / format Badge / chunks tabular-nums / last-indexed slice(0,10) / doc_id mono)+ `DocumentsSkeleton` loading + destructive error banner + empty-index Upload prompt(the old「Add a document」CTA, now gated on `data.length === 0`). `BackendStubNote` component preserved(still used by ChunksTab). Top-of-file docstring F3.2 line updated to reflect the W17 wiring.
- **F4.2** — `frontend/app/admin/page.tsx`:removed the unused `CardTitle` import → `npm run lint` now **green globally**(it was the only ESLint error;Karpathy §1.3 surgical — only this orphan).
- **F4.3** — `NEXT_PUBLIC_LANGFUSE_URL` is **already** in `.env.example`(line ~101,added W16 F5.x.2 `1dbcdf3`);`frontend/app/debug/[traceId]/page.tsx` already reads it via `LANGFUSE_FALLBACK_BASE`(ADR-0020 Session 2). No change needed — effectively closed. **CO_W15_F2_langfuse_url → CLOSED.**
- **F4.4** — Cohere reranker naming canonicalized to `Cohere-rerank-v4.0-pro`(the Azure Marketplace deployment name — matches the live `.env` `COHERE_RERANK_MODEL`, which is what actually works per the W16 backend smoke):aligned `backend/storage/settings.py` `cohere_rerank_model` default + `backend/retrieval/reranker/cohere.py` `model` default + both docstrings + `.env.example` `COHERE_RERANK_MODEL`. Human display label `"Cohere v4.0-pro"` kept for UI. Grep-verified no stray `rerank-v4.0-pro`(unqualified)/ `cohere-rerank-v4-pro` in code(empty). ADR / audit-doc historical `cohere-v4.0-pro` references left per anti-pattern「keep historical narrative」. Note:Path B(direct `api.cohere.com`)would need a Cohere-native model name — flagged in the `settings.py` comment, out of W17 scope.
- **Verification**:`tsc --noEmit` clean;`next lint`(whole frontend)green;`ruff check` clean on changed backend files;mypy unaffected(string-literal + docstring changes only — no type changes). Browser smoke of the Documents tab deferred to F5(needs a local backend + seeded KB + a doc actually indexed;the W16 seeded KB had 0 in-memory docs but the Azure index `ekp-kb-drive-v1` has chunks → the real `list_documents` would return the AP/AR/FA manuals — to be confirmed in F5).

### Carry-overs closed by F4

- CO_W15_F2_langfuse_url → CLOSED(F4.3 — already-present env var verified)
- `admin/page.tsx` `CardTitle` lint orphan(W16 progress Day 1 note)→ CLOSED(F4.2)
- Cohere reranker naming inconsistency(session-start.md §11)→ CLOSED(F4.4)

### Day 1 commits

- **`9ee636c`** `feat(frontend,api)` — W17 F4 Documents-tab real backend wire + admin lint fix + Cohere naming canon(6 files;+ NEW `frontend/lib/api/documents.ts`)
- **`(this docs commit)`** `docs(planning)` — W17 checklist F0+F4 ticked + this Day-1 progress entry + Day-0 commit hashes back-filled

---

## Day 2 — F1 part 1: Postgres KB backend(2026-05-10, same-calendar-day)

> User directive「繼續做 F1 Postgres persistent backing」. F1 is the largest deliverable(~2 plan-days)— split:**part 1 = the KB backend**(this entry);part 2 = `users_repo` Postgres path(F1.5)+ doc note(F1.8), held pending the decision below.

### F1 part 1 — landed `2453a50` `feat(infra,api)`

- **`PostgresKBBackend`**(`backend/kb_management/postgres_backend.py`)— satisfies the existing `KBStorageBackend` Protocol(create / list_all / get / delete / update_config / update_metadata). **Connection-per-op** via `psycopg` 3 async — Tier 1 KB ops are infrequent + off the query hot path, so a pool isn't warranted(**deviation from plan §F1.6「lifespan pool」**— Karpathy §1.2 simplicity-first;ADR-0023 already permitted「connection / pool」;logged in plan §7 changelog D2). `CREATE TABLE IF NOT EXISTS knowledge_bases (...)` on each connect — idempotent, microseconds when the table exists, race-free vs a lazy init flag. `knowledge_bases` table:`kb_id` PK / `name` / `description` / `config` JSONB / `total_documents` / `total_chunks` / `total_screenshots` / `failed_documents` JSONB / `last_indexed_at` TIMESTAMPTZ / `storage_size_mb` DOUBLE PRECISION. `KbStatus` ⇄ row mapping(JSONB via `model_dump()` / `model_dump(mode="json")` for the datetime in `FailureRecord`, reconstructed by Pydantic on read). Raises the existing `KBNotFoundError` / `KBAlreadyExistsError`.
- **`make_kb_backend(settings)` factory**(`backend/kb_management/factory.py`)— mirrors `retrieval.reranker.factory.make_reranker`;Postgres when `settings.database_url` set, else `InMemoryKBBackend`(W1 behaviour — local dev / CI unchanged). `PostgresKBBackend`(and `psycopg`)is **lazily imported inside the branch** — an unset `DATABASE_URL` never touches `psycopg`(same graceful-degrade shape as the W13 F6 ACS lazy import;also keeps the in-memory path working if `psycopg` install is R8-blocked). `get_kb_service()` rewired through `make_kb_backend(get_settings())`;`kb_management/__init__.py` exports `make_kb_backend`. **No route / service call-site change**(the Protocol contract holds — this is the swap point the Protocol was designed for);`app.dependency_overrides[get_kb_service]` still works for tests. **No lifespan pool wiring needed**(connection-per-op).
- **Config + infra** — `settings.database_url: str = ""`;`.env.example`「Persistent storage」section with commented `DATABASE_URL=postgresql://langfuse:langfuse_local_dev_only@localhost:5432/ekp`. `docker-compose.yml`:postgres exposes `:5432`(so the host-run backend can connect)+ mounts `./postgres-init/01-create-ekp-db.sql`(`CREATE DATABASE ekp;` — runs on a fresh `ekp-postgres-data` volume;existing volume → `docker compose exec postgres createdb -U langfuse ekp`). `pyproject.toml`:`psycopg[binary]>=3.2`(H2 — ADR-0023 covers;no `uv.lock` in repo so the declaration suffices).
- **Tests** — `test_kb_factory.py`(in-memory selection — always runs;Postgres-selection `importorskip("psycopg")`)+ `test_kb_postgres_backend.py`(full CRUD: create-then-get-roundtrips-all-fields / dup→409 / get-missing→404 / list-all-sorted / update_config / update_config-missing→404 / update_metadata-partial / update_metadata-missing→404 / delete-then-404 / delete-missing→404 — `importorskip("psycopg")` + `skipif(not DATABASE_URL)`,with manual-smoke instructions in the docstring). **Backend pytest 594 passed / 9 skipped**(was 593/7 — +1 pass = the in-memory factory test;+2 skips = the psycopg-gated factory test + the postgres-backend module). `ruff check` clean on new + changed files. `tsc` n/a(no frontend change). `mypy --strict` on `postgres_backend.py` — **can't run locally**(psycopg not installed → import-not-found;works once psycopg is present, psycopg 3 ships `py.typed`).

### 🚨 R8 corp-proxy block — 5th cumulative occurrence — ADR-0017 trigger met + vendor-decision pivot point

`pip install psycopg[binary]>=3.2` **fails under the Ricoh corp proxy** — `IncompleteRead` on the first attempt(178743 bytes / 3.5 MB), then「Connection timed out while downloading」+「Attempting to resume incomplete download (0 bytes/3.6 MB, attempt 1)」on the `--retries 5 --timeout 120` retry. Same hard-block pattern as:Cohere SDK(W3 Marketplace path)、argon2-cffi(W13 → ADR-0016 stdlib switch)、ACS SDK(W13 → lazy-import design)、Playwright browser CDN(W15 D5 → ECONNRESET 0%). `pip config list` empty(no internal PyPI mirror configured).

→ **5th cumulative R8 occurrence** — the ADR-0017 formalization trigger("5th occurrence OR vendor-decision pivot needed" per session-start.md §11 + W17 plan §4 risks)is **met**. AND this is a **vendor-decision pivot point**:the approver chose `psycopg`(AskUserQuestion 2026-05-10);if it can't be installed in the dev environment(and possibly the deploy pipeline), the choice may need revisiting.

Per CLAUDE.md §5(vendor-decision-affected obstacle)+ §13(when in doubt → ask)→ **stop-and-ask**. F1 verdict = **PARTIAL**. F1.5(users_repo Postgres path)+ F1.8(architecture.md / COMPONENT_CATALOG C02 / setup.md §4.2 doc note)held pending the user decision. Options surfaced:
- **(A)** keep `psycopg` — code is shippable as-is(dep declared,lazy-imported,in-memory path unaffected);defer the local Postgres-path verification(CRUD tests + `mypy postgres_backend.py` + manual smoke)to W18+ / a personal Azure dev tier(CO17 — where the corp proxy isn't in the path);**formalize ADR-0017 now**(R8 mitigation pattern). Then proceed with F1.5(users_repo)+ F2/F3/F5/F6.
- **(B)** pivot storage to **stdlib `sqlite3`**(zero new dep — no R8 risk;the AI's original Day-0 recommendation). Lose the「production-grade Postgres」alignment but Beta could still adopt Postgres via a different driver later. Would supersede / amend ADR-0023.
- **(C)** defer F1 entirely to W18+(when R8 is worked around);proceed with F2/F3/F5/F6 only this phase.

### Decision (2026-05-10, same-calendar-day) — Option A taken

User chose **(A)**:keep `psycopg` + defer local Postgres-path verification(CRUD tests + `mypy postgres_backend.py` + manual smoke)to W18+ / personal Azure dev tier(CO17)+ **formalize ADR-0017 now**. No pivot to sqlite3;ADR-0023 stands. → **ADR-0017 landed `fb0253a`**(R8 corp-proxy mitigation pattern — dependency-add discipline;ADR-0017 reservation cleared,only 0013 AF3 remains reserved;next NNNN → 0024). F1.5(`users_repo` Postgres path)+ F1.8(architecture.md §3.4 / COMPONENT_CATALOG C02 / setup.md §4.2 doc note)now **unblocked → pending implementation**(next). Then F2 cookie/CSRF → F3 RAGAs → F5 a11y → F6 Vitest → F7 closeout. F1 verdict stays **PARTIAL**(code shipped + ADR-0017 written;the Postgres-path runtime verification is the deferred part).

### Day 2 commits

- **`2453a50`** `feat(infra,api)` — W17 F1 part 1 Postgres KB backend(11 files;+ NEW `kb_management/postgres_backend.py` + `factory.py` + `tests/test_kb_factory.py` + `tests/test_kb_postgres_backend.py` + `infrastructure/postgres-init/01-create-ekp-db.sql`)
- **`3806777`** `docs(planning)` — W17 checklist F1 part-1 ticked(F1.5 / F1.8 → 🚧)+ Day-2 progress entry + plan §7 changelog D1+D2(F4 landed + F1 deviations + R8 block)
- **`fb0253a`** `docs(adr)` — ADR-0017 R8 corp-proxy mitigation pattern + README index(0017 row;reservation cleared;next NNNN → 0024)
- **`(this docs commit)`** `docs(planning)` — Day-2 「Decision: Option A taken」addendum + checklist F1.5/F1.8 🚧-reason updated(held-pending-decision → pending-implementation)

---

## Day 3 — F1 part 2: `users_repo` Postgres path + KB metadata persistence doc notes(2026-05-10, same-calendar-day)

> Continues from the Day-2 Option-A decision. F1 part 2 = `users_repo` Postgres-backed path(F1.5)+ the architecture.md / COMPONENT_CATALOG / setup.md doc notes(F1.8). After this F1 is implementation-complete(verdict stays PARTIAL — only the R8-blocked `pip install` + manual smoke is deferred).

### F1.5 — `users_repo` Postgres path — landed `5c5df92` `feat(api)`

- **`UsersStore` Protocol split**(mirrors `KBStorageBackend`)— NEW `backend/api/auth/users_store.py`:`UserRecord` / `SessionRecord` Pydantic models(moved here from `users_repo.py`)+ `UsersStore` Protocol(`reset` / `add_user` / `get_user_by_oid` / `get_user_by_email` / `replace_user` / `add_session` / `get_session` / `delete_session`)+ `InMemoryUsersStore`(process-local dicts + `RLock`)+ `make_users_store(settings)` factory(Postgres when `database_url` set, else in-memory;`PostgresUsersStore` lazily imported inside the branch — unset `DATABASE_URL` never touches `psycopg`, R8-safe — same shape as `make_kb_backend` / the ACS lazy import).
- **NEW `backend/api/auth/postgres_users_store.py`** — `PostgresUsersStore`,**sync `psycopg` connection-per-op**. Why sync(≠ the async `PostgresKBBackend`):`users_repo`'s public surface is sync — consumed by the sync `get_current_user` FastAPI dependency(threadpool-run)+ sync calls in the async `/auth/*` route bodies — so an async DAL would ripple through `dependency.py` / `auth.py` / the test suite, violating「same public interface」. Auth ops are infrequent + off the hot path so connection-per-op(no pool)is fine — same trade as `PostgresKBBackend`(logged plan §7 D2). `CREATE TABLE IF NOT EXISTS` on connect:`users`(`oid` PK / `email` TEXT UNIQUE / `display_name` / `password_hash` / `verified` / `verification_code` / `verification_code_expires_at` TIMESTAMPTZ / `last_resend_at` TIMESTAMPTZ / `created_at` TIMESTAMPTZ)+ `sessions`(`token` PK / `user_oid` FK→`users(oid)` ON DELETE CASCADE / `expires_at` / `created_at`). `add_user` catches `psycopg.errors.UniqueViolation` → `ValueError("email_already_exists: …")`(matches the existing contract);`reset()` = `TRUNCATE TABLE sessions, users`.
- **`users_repo.py` → thin facade** — keeps the 9 public functions(`reset_repo` / `find_by_email` / `find_by_oid` / `register` / `regenerate_verification_code` / `mark_verified` / `create_session` / `resolve_session` / `revoke_session`)+ all the business logic(`generate_user_oid` / `generate_verification_code` / `hash_password`, 24h expiry math, email normalization, the `AuthenticatedUser` projection in `resolve_session`)+ re-exports `UserRecord` / `SessionRecord` / `SELF_REGISTER_TID`(so `from api.auth.users_repo import UserRecord` in `routes/auth.py` + `from api.auth.users_repo import SELF_REGISTER_TID` in the tests keep working). `_store: UsersStore = make_users_store(get_settings())` selected once at import. **No call-site change**(`routes/auth.py` / `dependency.py` / `__init__.py` untouched). Locking moved into `InMemoryUsersStore`(per-method `RLock`)— the small check-then-add TOCTOU in `register` is covered by `add_user` re-checking + raising;triple-defended(route 409 pre-check + module pre-check + store).
- **Tests** — NEW `backend/tests/test_users_store_factory.py`(in-memory selection always runs ✅;Postgres selection `importorskip("psycopg")` — skips)+ NEW `backend/tests/test_auth_users_postgres_store.py`(module-level `importorskip("psycopg")` + `skipif(not DATABASE_URL)` → whole module skips in CI;8 cases:add-then-get-roundtrips-all-fields / get-missing→None / dup-email→ValueError / replace-user-overwrites / reset-truncates-both / session-add-get-delete / get-missing-session→None / session-FK-cascade-when-user-deleted;manual `docker compose up` + `DATABASE_URL=…` smoke instructions in the docstring). 4 test-only `users_repo._users/_sessions` direct writes in `test_auth_self_register.py`(force-expiry / simulate-admin-delete / bypass-cooldown ×2)retargeted to `users_repo._store._users/._sessions` + `# type: ignore[attr-defined]`. **Backend pytest 595 passed / 11 skipped**(was 594/9 — +1 pass = the in-memory users-store factory test;+2 skips = the psycopg-gated factory test + the postgres-users-store module). `ruff check` clean on all new + changed files. `mypy -p api.auth` clean on `users_store.py` + `users_repo.py`(the 2 `psycopg` `import-not-found` errors in `postgres_users_store.py` are the documented R8 PARTIAL-PASS per ADR-0017;the `azure.communication.email` / `jose` stub errors are pre-existing).

### F1.8 — doc notes(in-memory → Postgres-backed)— same commit `5c5df92`

- `docs/architecture.md` **§3.4** — NEW「KB metadata 持久化」note(`KbStatus` records + `users_repo` users/sessions via `KBStorageBackend` / `UsersStore` Protocol → default backend Postgres on a dedicated `ekp` DB;in-memory fallback when `DATABASE_URL` unset;chunk/doc/screenshot still in each KB's Azure AI Search index + Blob container — only the KB *metadata table* changed). Inline-tagged「(W17 F1 amendment — per ADR-0023)」— doc version **not** bumped(same convention as §3.7's「v6 amendment per ADR-0014」tag;ADR is the decision record).
- `docs/02-architecture/COMPONENT_CATALOG.md` **C02** — table row → "Postgres-backed per ADR-0023; in-memory fallback when `DATABASE_URL` unset";detail block Tech / Depends-on / Phase-plan / Risks / Status / Interface lines updated(`make_kb_backend` swap point;`psycopg[binary]` H2 dep;R8 verification-deferral note;`5c5df92` commit ref). The stale C03-era "W2 swap to AzureSearchKBBackend" planned-name removed. **C11 entry left as-is**(its "⏳ Beta+ scope / W1-W6 zero touch" predates the whole W7-W15 hybrid-auth build — a much larger drift than F1.8 scopes;flagged for separate housekeeping, same bucket as the §11「C13 Workflow Engine」stale-Tier-2-card note).
- `docs/setup.md` **§4.2** — postgres service purpose row now mentions the EKP `ekp` DB;NEW callout box:`createdb -U langfuse ekp` one-liner(for an existing volume)+ `DATABASE_URL=postgresql://langfuse:langfuse_local_dev_only@localhost:5432/ekp` env var → `make_kb_backend` / `make_users_store` switch to Postgres + restart no longer wipes;unset → in-memory fallback(no migration step — backend `CREATE TABLE IF NOT EXISTS` self-builds).
- **CO18 → CLOSED** — KB Manager + `users_repo` persistent backing is implemented(in-memory remains the no-`DATABASE_URL` fallback). The remaining 🚧 is only F1.5b(the literal `pip install psycopg[binary]` + manual `docker compose up` smoke + `mypy postgres_*` — R8-blocked, deferred W18+/CO17).

### Day 3 commits

- **`5c5df92`** `feat(api)` — W17 F1 part 2 users_repo Postgres path(`UsersStore` Protocol split + `postgres_users_store.py` + `users_store.py` + facade rewrite + 2 NEW test files + 4 test retargets)+ F1.8 doc notes(architecture.md §3.4 + COMPONENT_CATALOG C02 + setup.md §4.2)— 9 files
- **`(this docs commit)`** `docs(planning)` — W17 checklist F1.5/F1.8 ticked + F1.5b 🚧-scope updated(test scaffold committed;only pip/smoke/mypy deferred)+ F1 verdict note updated(CO18 CLOSED)+ Day-3 progress entry + plan §7 changelog D3

---

## Day 4 — F2: auth-transport hardening (httpOnly cookie + CSRF + /auth/refresh)(2026-05-10, same-calendar-day)

> Per ADR-0022. F2 verdict = **PASS** — landed `7cca23e` `feat(api,frontend)`. CO_F5_refresh + CO_F5_cookie → CLOSED.

### Backend (C08 API Gateway + C11 Identity)

- **NEW `backend/api/auth/cookies.py`** — `set_session_cookies(response, settings, token)` sets `ekp_session`(httpOnly, `SameSite=Lax`, `Secure` when `environment != "local"`, `Path=/`, `Max-Age=` session TTL)+ `ekp_csrf`(readable double-submit, same attrs minus httpOnly), returns the CSRF token; `clear_session_cookies()` expires both; `csrf_token_ok(header, cookie)` constant-time double-submit check; `SESSION_COOKIE`/`CSRF_COOKIE`/`CSRF_HEADER`/`STATE_CHANGING_METHODS` constants.
- **`dependency.get_current_user` → dual-path** — resolution order: (1) `ekp_session` cookie (precedence) → `users_repo.resolve_session`; on a state-changing request (POST/PUT/PATCH/DELETE) the CSRF double-submit is enforced (`X-CSRF-Token` == `ekp_csrf` cookie, else 403); (2) `Authorization: Bearer` — session bearer (legacy / API clients) → mock dev-token → MSAL JWT (Bearer-auth is CSRF-exempt — a Bearer is never auto-attached by a browser). A present-but-invalid cookie falls through to (2). Now takes `request: Request` (the 2 `test_mock_msal.py` direct-call tests updated with a `_bare_request()` helper).
- **`routes/auth.py`** — `/auth/login` + the verified-transition of `/auth/verify-email` call `set_session_cookies` (verify-email now **auto-logs-in** per ADR-0022 §1 — fixes the prior register-flow gap where Step-3 "Start asking" landed on `/chat` unauthenticated; `VerifyEmailResponse` gained `access_token`/`expires_in`, None on the idempotent already-verified branch). `/auth/refresh` — for a self-register session (cookie or legacy bearer): revoke the old token, mint a new one, re-set both cookies, return `RefreshResponse(is_mock=False)`; mock mode keeps the fixed dev-token (no cookie); real MSAL still 503 — **closes CO_F5_refresh**. `/auth/logout` — revoke the cookie token + any bearer + `clear_session_cookies` — **closes CO_F5_cookie**. `/auth/register` unchanged (user not verified yet).
- **`server.py`** — CORS gained `allow_credentials=True` (cookie-transport correctness for any direct cross-origin browser→backend dev call — the same-origin `/api/backend` proxy path forwards `Cookie`/`Set-Cookie` regardless via `route.ts`; a regex origin, not `*`, is required when credentials are allowed). Same local-dev-gap category as the `84d030e` CORS add — not H1.

### Frontend (C09 Admin UI + C10 Chat UI)

- **`lib/api-client.ts`** — `credentials:'include'` on get/post/patch; `getCsrfHeaders()` (reads the `ekp_csrf` cookie via `document.cookie`, returns `{'X-CSRF-Token': …}` or `{}`) — exported and applied on post/patch; also wired into the raw-fetch callers `lib/api/query.ts` `streamQuery` (POST `/query/stream`) + `lib/api/kb.ts` `uploadDoc` (POST `/kb/{id}/documents`) — both are cookie-authenticated state-changing requests so they need the CSRF header (the `/api/backend` proxy → `dependencies=_auth` → CSRF check).
- **`lib/auth/index.ts`** — `SESSION_TOKEN_STORAGE_KEY` + `readSessionBearer()` removed; the self-register session is the httpOnly cookie now, so `getBearer()` is just `getMockBearer()` (mock dev-token) / `getMsalBearer()` (SSO JWT). `lib/api/auth.ts` drops the `SESSION_TOKEN_STORAGE_KEY` re-export + adds `VerifyEmailResponse.access_token`/`expires_in`. `app/login/page.tsx` drops the `localStorage.setItem(SESSION_TOKEN_STORAGE_KEY, …)` write + the now-unused import. `app/register/page.tsx` — no edit needed (never wrote localStorage; the verify-email auto-login cookie makes its Step-3 → `/chat` work).

### Docs

- `architecture.md` §3.7 — NEW「Auth transport」note (cookie + CSRF + dual-path + refresh rotation + verify-email auto-login; inline-tagged「W17 F2 amendment — per ADR-0022」; doc version not bumped — same convention as the §3.4 / §3.7 ADR-tag style). `docs/adr/0014-*.md` References — cross-link to ADR-0022 (+ ADR-0016, ADR-0023). `docs/adr/0022-*.md` "Implementation Deliverables" — F0.1 + F2.1–F2.8 ticked.

### Verification

`ruff check` clean on all new + changed files (pre-existing `server.py` 19×E402 from the truststore-must-run-first pattern + `test_auth_self_register.py` 5×UP037 untouched — not my mess). **Backend pytest 609 passed / 11 skipped** (the previous full run was 607 passed / 2 failed — the 2 were `test_mock_msal.py` calling `get_current_user(credentials=…, settings=…)` positionally → broke when `request` was added; fixed; +17 new `test_auth_cookie_transport.py` cases). `mypy -p api.auth` — `cookies.py` / `dependency.py` / `routes/auth.py` add no errors (the 5 in `api.auth` are pre-existing: `postgres_users_store.py` psycopg ×2 [R8/ADR-0017] + `email_provider.py` azure stub + `msal_provider.py` jose stubs ×2). Frontend `tsc --noEmit` + `next lint` clean.

### Day 4 commits

- **`7cca23e`** `feat(api,frontend)` — W17 F2 auth-transport hardening (17 files; + NEW `backend/api/auth/cookies.py` + `backend/tests/test_auth_cookie_transport.py`)
- **`(this docs commit)`** `docs(planning)` — W17 checklist F2 ticked (verdict PASS, CO_F5_* CLOSED) + Day-4 progress entry + plan §7 changelog D4

---

## Day 5 — F3: RAGAs 4-metric integration into /eval/run + /eval/shootout(2026-05-10, same-calendar-day)

> F3 verdict = **PASS (structural; live-verify deferred)** — landed `7f446fb` `feat(eval,api)`. C06 Eval Framework + C08 API Gateway. **CO_W15_F1_eval_set_v1 stays OPEN** (F3.4 finding).

### What landed

- **NEW `backend/eval/ragas_evaluator.py`** — `make_ragas_evaluator(settings) -> Callable[[RagasQuerySample], dict] | None` + `patch_for_gpt5(client)`. Extracted from `scripts/run_ragas_eval.py`'s `_make_real_evaluator` + `_patch_for_gpt5` so `/eval/*` can reuse them (`backend/` can't import from `scripts/`). The evaluator builds the 4 RAGAs 0.4.3 `collections` metrics (`Faithfulness` / `AnswerRelevancy` / `ContextPrecision` / `ContextRecall`) bound to the Azure OpenAI judge (`azure_openai_deployment_llm_judge`, same model as the CRAG grader) + embeddings (Q19 `text-embedding-3-large` for AnswerRelevancy cosine sim); `patch_for_gpt5` is the GPT-5-reasoning-judge shim (`max_tokens → max_completion_tokens` floor 4096 — so faithfulness statement-extraction JSON doesn't truncate — + drop `temperature`/`logprobs`; patches the live instance so `instructor.from_openai`'s `isinstance` check still matches). The sync `RagasRunner` contract is preserved (the async `ascore` calls are bridged via `asyncio.run` in a worker thread). **Returns `None` when no Azure judge key** → callers fall back to the Recall@5-only `EvalReport` (same shape as the existing `_engine_or_503` 503-without-Azure pattern). `scripts/run_ragas_eval.py` now re-exports `patch_for_gpt5` (back-compat alias `_patch_for_gpt5` — `test_run_ragas_eval_patch.py` unchanged) and `_make_real_evaluator` is a thin wrapper of `make_ragas_evaluator`.
- **`backend/eval/orchestrator.py`** — `run_eval_pipeline` gains optional `synthesizer` + `ragas_evaluator` (+ `judge_deployment`). NEW `build_ragas_samples(eval_set_path, engine, synthesizer, kb_id, max_main_queries)` — runs the RAG pipeline per main (non-OOS) query (`engine.retrieve(query, kb_id, top_k=5)` per ADR-0018 → `synthesizer.synthesize(question, chunks).answer`) to assemble `RagasQuerySample`s. When `synthesizer` AND `ragas_evaluator` are both supplied: build samples → `RagasRunner(judge_deployment, ragas_evaluator).evaluate(samples)` → `EvalReport.faithfulness` ← `faithfulness` mean, `EvalReport.correctness` ← `answer_relevancy` mean (**「Answer-Correctness」approximated by RAGAs answer-relevancy** — proper `answer_correctness` needs SME reference answers per Q14, which the eval-set doesn't carry yet, see F3.4); per-query RAGAs errors + below-`0.70`-attention-threshold scorers → `failed_queries`. `image_association` / `crag_trigger_rate` / `avg_cost_per_query_usd` stay `0.0` (custom image-text-correlation metric + CRAG-loop integration + cost-table — out of F3 scope; documented `_metrics_deferred_note` in `failed_queries`). When `synthesizer`/`ragas_evaluator` are `None` → Recall@5-only report + `_ragas_not_run` note. **The W16 F5.4「RAGAs deferred to W17+」placeholder is gone.**
- **`backend/api/routes/eval.py`** — `_ragas_wiring(request) -> (synthesizer, ragas_evaluator, judge_deployment)` reads `request.app.state.synthesizer` (None unless server booted with Azure keys) + `make_ragas_evaluator(get_settings())` (None unless Azure judge key) and threads them through `/eval/run` + `/eval/shootout`'s `run_eval_pipeline` calls — synchronous, bounded by the existing `max_main_queries` cap (no job-id shape was introduced W16, so synchronous-with-cap stays). 502 on eval failure / 503 on no `RetrievalEngine` unchanged. Module docstring records the **F3.4 finding** (eval-set ids: `eval-set-v0` real + `eval-set-v1-draft` WIP; `docs/eval-set-v1.yaml` final does NOT exist).
- **NEW `backend/tests/test_eval_ragas.py`** — 4 cases: `make_ragas_evaluator` → `None` without Azure key (always runs); `run_eval_pipeline` Recall@5-only fallback shape (`faithfulness == 0.0`, `correctness is None`, `_ragas_not_run` + `_metrics_deferred_note` in `failed_queries`); `run_eval_pipeline` populates RAGAs metrics with a stub `ragas_evaluator` + fake engine + fake synthesizer (`faithfulness == 0.92`, `correctness == 0.88`); below-threshold queries surface in `failed_queries` (mixed-score stub). **The stub `ragas_evaluator` IS the LLM-judge boundary — no live Azure in CI.** Existing `test_orchestrator.py` / `test_eval_endpoints.py` / `test_ragas_runner.py` / `test_run_ragas_eval_patch.py` / `test_eval_runner.py` unchanged + pass.

### F3.4 finding — eval-set-v1

`docs/eval-set-v1.yaml` (final) does **NOT** exist. `docs/eval-set-v1-draft.yaml` is the WIP. Finalizing v1 = adding Chris's SME **reference answers** per Q14 — without those, RAGAs `answer_correctness` proper can't be scored (hence the answer-relevancy approximation for `EvalReport.correctness`). **CO_W15_F1_eval_set_v1 stays OPEN** pending the SME label cascade. No ground truth fabricated (per the plan F3.4 directive). The orchestrator + routes happily run RAGAs against `eval-set-v0` (the validated subset) when an Azure judge is available.

### 🚧 Deferred — F3.5b RAGAs live-verify

The structural integration is complete + CI-tested at the LLM-judge boundary, but the **real judge run** (`scripts/run_ragas_eval.py` or `POST /eval/run` against a populated Azure index + judge) needs Azure OpenAI keys + a populated `ekp-kb-drive-v1` index — **deferred to a non-proxy env / personal Azure dev tier (same CO17 pattern as F1.5b)**. So F3, like F1, is "PASS structural / live-verify deferred".

### Verification

`ruff check` clean on `backend/eval/` + `backend/api/routes/eval.py` + the new test (the `scripts/run_ragas_eval.py` E402 + `import json` orphan are pre-existing — `scripts/` isn't in the `backend/pyproject.toml` ruff scope; not touched). `mypy -p eval` — my files add only an `import yaml` `import-untyped` in `orchestrator.py` (consistent with `runner.py` / `ragas_runner.py`; no `types-PyYAML` installed); the prior `ragas_evaluator.py:55` `int()` overload error fixed by matching the original untyped-`**kwargs` shape. **Backend pytest 613 passed / 11 skipped** (was 609/11 — +4 new `test_eval_ragas` cases).

### Day 5 commits

- **`7f446fb`** `feat(eval,api)` — W17 F3 RAGAs integration (5 files; + NEW `backend/eval/ragas_evaluator.py` + `backend/tests/test_eval_ragas.py`)
- **`(this docs commit)`** `docs(planning)` — W17 checklist F3.1–F3.6 ticked (verdict PASS structural / F3.5b 🚧 / F3.4 finding) + Day-5 progress entry + plan §7 changelog D5

---

## Day 6 — _(implementation entries appended below as work lands)_

_(Next:F5 a11y/dark-mode browser smoke V1-V9 → F6 Vitest+RTL scaffold → F7 closeout + hygiene catch-up;each commit ↔ Day-N entry per R2.)_

---

## Retro(填於 W17 closeout — F7)

### What worked

_(TBD)_

### What didn't

_(TBD)_

### Surprises / discoveries

_(TBD)_

### Decisions

_(TBD — will include: storage = Postgres rationale / cookie SameSite+Secure policy / RAGAs CI-mock boundary / Cohere canonical identifier pick)_

### Carry-overs to W18+

_(TBD)_

### Time tracking

| Deliverable | Plan estimate | Actual | Variance |
|---|---|---|---|
| F0 ADRs | 0.5 day | _TBD_ | _TBD_ |
| F1 Postgres backing | 2 days | _TBD_ | _TBD_ |
| F2 auth-transport | 1.5 days | _TBD_ | _TBD_ |
| F3 RAGAs | 1.5 days | _TBD_ | _TBD_ |
| F4 frontend bundle | 0.5 day | _TBD_ | _TBD_ |
| F5 a11y/dark-mode | 0.5 day | _TBD_ | _TBD_ |
| F6 Vitest scaffold | 0.5 day | _TBD_ | _TBD_ |
| F7 closeout | 0.5 day | _TBD_ | _TBD_ |

### Spec ref alignment

_(TBD — F1 → architecture.md v6 §3.4 + ADR-0023;F2 → §3.7 + ADR-0014 + ADR-0022;F3 → §5.6 + eval-methodology.md;F4 → §5.x + ADR-0012;F6 → CLAUDE.md §3.2)_
