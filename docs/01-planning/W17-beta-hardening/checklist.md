---
phase: W17-beta-hardening
plan_ref: ./plan.md
status: active
last_updated: 2026-05-10
---

# Phase W17 — Checklist

> Atomic checkbox(每 item ≤ 0.5–2 hour effort)。Status:`active` 2026-05-10 per user directive。
> 每 item done 後 `[ ]→[x]` + commit ref;延後項標 🚧 + reason(per CLAUDE.md §10 sacred rule — 唔可以刪未勾選 item)。

## F0 — ADRs(H1/H2 gate — must land before F1/F2 implementation)

- [x] F0.1 NEW `docs/adr/0022-auth-transport-hardening.md`(httpOnly cookie + CSRF double-submit + `/auth/refresh` rotation;dual-path `get_current_user`;amends ADR-0014 transport layer)— Status `Accepted` — `6edd9ef`
- [x] F0.2 NEW `docs/adr/0023-kb-manager-persistent-backing.md`(Postgres via `psycopg`;reuse docker-compose postgres + dedicated `ekp` DB;`PostgresKBBackend` satisfies `KBStorageBackend` Protocol;in-memory fallback when `DATABASE_URL` empty)— Status `Accepted` — `6edd9ef`
- [x] F0.3 `docs/adr/README.md` index — add ADR-0022 + ADR-0023 rows;「Next NNNN」→ `0024` — `6edd9ef`

## F1 — Postgres persistent backing for KB Manager + users_repo(per ADR-0023)

> **F1 verdict = PARTIAL**(2026-05-10)— all code landed(KB backend `2453a50` D2;users-repo path + doc notes `5c5df92` D3),but `pip install psycopg[binary]` is **R8 corp-proxy-blocked**(5th cumulative R8 occurrence → **ADR-0017 landed `fb0253a`**;vendor-decision pivot point — **decision = Option A**:keep psycopg, defer local Postgres-path *verification* to W18+ / CO17). Code is shippable regardless(dep declared,lazy-imported,in-memory path unaffected;CI 595 passed / 11 skipped — Postgres-path tests skip cleanly). **CO18 → CLOSED**(persistent backing implemented;in-memory remains the no-`DATABASE_URL` fallback). Only the literal `pip install` + manual `docker compose up` smoke remains(🚧 F1.5b).

## F0b — ADR-0017(R8 mitigation pattern — formalized at the 5th occurrence + vendor-decision pivot trigger)

- [x] F0b.1 NEW `docs/adr/0017-r8-corp-proxy-mitigation-pattern.md`(dependency-add discipline:stdlib > managed-REST > lazy-imported optional dep + graceful fallback;declare-but-defer-install for binary-heavy assets;stop-and-ask when unavoidable)— Status `Accepted` — `fb0253a`
- [x] F0b.2 `docs/adr/README.md` — 0017 row added;ADR-0017 reservation cleared(only 0013 AF3 remains);next NNNN → 0024 — `fb0253a`

- [x] F1.1 `backend/pyproject.toml` — added `psycopg[binary]>=3.2` to deps(H2 — ADR-0023 covers);no `uv.lock` in repo so `pyproject.toml` declaration suffices;**local `pip install` R8-blocked** — `2453a50`
- [x] F1.2 `infrastructure/docker-compose.yml` — postgres service exposes `:5432` + mounts `./postgres-init/01-create-ekp-db.sql`(creates the dedicated `ekp` DB on a fresh volume;existing volume → `docker compose exec postgres createdb -U langfuse ekp`);`.env.example` + docker-compose comments updated(`docs/setup.md §4.2` table update folded into F1.8 / closeout)— `2453a50`
- [x] F1.3 `backend/storage/settings.py` — added `database_url: str = ""`;`.env.example`「Persistent storage」section with commented `DATABASE_URL=postgresql://langfuse:langfuse_local_dev_only@localhost:5432/ekp`;empty → in-memory fallback documented — `2453a50`
- [x] F1.4 NEW `backend/kb_management/postgres_backend.py` — `PostgresKBBackend` satisfying `KBStorageBackend` Protocol(create / list_all / get / delete / update_config / update_metadata);**connection-per-op** via psycopg async(deviation from「pool」— plan §7 changelog D2);`CREATE TABLE IF NOT EXISTS knowledge_bases (...)` on connect;raises `KBNotFoundError` / `KBAlreadyExistsError`;`KbStatus` ⇄ row mapping(JSONB for `config` + `failed_documents` via `model_dump(mode="json")`)— `2453a50`
- [x] F1.5 `backend/api/auth/users_repo.py` Postgres-backed path — done. `UsersStore` Protocol split(NEW `backend/api/auth/users_store.py` = `UserRecord`/`SessionRecord` models + `UsersStore` Protocol + `InMemoryUsersStore` + `make_users_store(settings)` factory;NEW `backend/api/auth/postgres_users_store.py` = `PostgresUsersStore` — **sync** `psycopg` connection-per-op, because `users_repo`'s public surface is sync(consumed by the sync `get_current_user` dependency)— differs from the async `PostgresKBBackend`;`CREATE TABLE IF NOT EXISTS users (... email UNIQUE ...)` + `sessions (... user_oid FK→users ON DELETE CASCADE ...)` on connect);`users_repo.py` → thin facade keeping the same 9 public functions + business logic(oid/code/scrypt-hash gen,expiry,`AuthenticatedUser` projection)+ re-exports `UserRecord`/`SessionRecord`/`SELF_REGISTER_TID`;`make_users_store` selects Postgres when `database_url` set,else in-memory;`psycopg` lazily imported(unset `DATABASE_URL` never touches it — R8-safe,same shape as the KB backend);`reset_repo()` preserved → `_store.reset()`(in-memory clear / Postgres `TRUNCATE`);4 test-only `users_repo._users/_sessions` direct writes in `test_auth_self_register.py` retargeted to `users_repo._store._users/._sessions` — `5c5df92`
- [ ] 🚧 F1.5b Postgres `users_repo` path local verification(CRUD + session)— **deferred W18+ / CO17**(R8 — `pip install psycopg[binary]` not installable under the proxy;same caveat as F1.4's CRUD tests). Test scaffold IS committed:NEW `backend/tests/test_users_store_factory.py`(in-memory selection always runs ✅;Postgres selection `importorskip("psycopg")`)+ NEW `backend/tests/test_auth_users_postgres_store.py`(`importorskip("psycopg")` module-level + `skipif(not DATABASE_URL)` — 8 CRUD/session/FK-cascade cases;skips cleanly in CI;manual `docker compose up` + `DATABASE_URL=...` smoke instructions in the docstring)— `5c5df92`. Also defers:`mypy postgres_users_store.py`(`-p api.auth` shows the 2 psycopg `import-not-found` errors — documented R8 PARTIAL-PASS per ADR-0017)
- [x] F1.6 Dependency wiring — NEW `backend/kb_management/factory.py` `make_kb_backend(settings)`(mirrors `make_reranker`)— Postgres when `database_url` set, else in-memory;`PostgresKBBackend` lazily imported(unset `DATABASE_URL` never touches psycopg — same graceful shape as ACS lazy import + keeps in-memory working under R8);`get_kb_service()` wired through it;`kb_management/__init__.py` exports `make_kb_backend`;no route / service call-site change(Protocol holds;dependency-override still works for tests)— **connection-per-op so no lifespan pool wiring needed**(deviation from plan §F1.6)— `2453a50`
- [x] F1.7 Tests — NEW `backend/tests/test_kb_factory.py`(in-memory selection — always runs;Postgres-selection `importorskip("psycopg")`)+ NEW `backend/tests/test_kb_postgres_backend.py`(full CRUD — `importorskip("psycopg")` + `skipif(not DATABASE_URL)` → skips otherwise per Tier 1 PARTIAL PASS;manual-smoke instructions in the docstring);existing `test_kb*` in-memory tests unchanged + pass;**backend pytest 594 passed / 9 skipped**(was 593/7)— `2453a50`
- [x] F1.8 `docs/architecture.md` §3.4(NEW「KB metadata 持久化」note — per ADR-0023,inline-tagged amendment;doc version not bumped — same convention as §3.7's ADR-0014 tag)+ `docs/02-architecture/COMPONENT_CATALOG.md` C02(table row + Tech / Phase plan / Risks / Status / Interface lines → Postgres-backed via `make_kb_backend`,in-memory fallback,R8 verification-deferral note)+ `docs/setup.md §4.2`(postgres service purpose row + NEW `ekp` DB note:`createdb` one-liner + `DATABASE_URL` env var + in-memory fallback)— **CO18 → CLOSED**;C11 catalog entry left as-is(stale「Beta+ scope」predates W7-W15 hybrid auth — separate housekeeping,not in F1.8 scope)— `5c5df92`

## F2 — Auth-transport hardening: httpOnly cookie + CSRF + /auth/refresh(per ADR-0022)

> **F2 verdict = PASS**(2026-05-10 D4)— landed `7cca23e`. **CO_F5_refresh + CO_F5_cookie → CLOSED**. One scope note:`/auth/verify-email`'s verified-transition now also sets the cookie + auto-logs-in(per ADR-0022 §1「the email-verify step ... set ekp_session」)→ `VerifyEmailResponse` gained `access_token`/`expires_in`(None on the idempotent already-verified branch);this fixes the prior register-flow gap(Step-3 → `/chat` was hitting `/chat` unauthenticated). `register/page.tsx` needed no edit(never wrote localStorage). `server.py` CORS gained `allow_credentials=True`(cookie-transport correctness — same local-dev-gap category as the `84d030e` CORS add,not H1).

- [x] F2.1 `backend/api/routes/auth.py` — `/auth/login` + `/auth/verify-email`(verified-transition)success → set `ekp_session`(httpOnly,SameSite=Lax,Secure when `environment != "local"`,Path=/,Max-Age=session TTL)+ `ekp_csrf`(readable double-submit)via NEW `backend/api/auth/cookies.py` `set_session_cookies()`;token still in the JSON body for API/CLI(Bearer transport parity)— `7cca23e`
- [x] F2.2 `POST /auth/refresh` — rotates the session token + both cookies(revokes the old token);401 via the `Depends(get_current_user)` gate if no valid session(no unauthenticated bootstrap);mock dev mode keeps returning the fixed dev-token(no cookie);real MSAL still 503 — **closes CO_F5_refresh** — `7cca23e`
- [x] F2.3 `POST /auth/logout` — revokes the session token(cookie token + any bearer)+ `clear_session_cookies()`(`ekp_session` + `ekp_csrf` Max-Age=0)— **closes CO_F5_cookie** — `7cca23e`
- [x] F2.4 `backend/api/auth/dependency.py` `get_current_user` — dual-path:`ekp_session` cookie(precedence)→ bearer session → mock → MSAL;a present-but-invalid cookie falls through to the bearer paths;CSRF double-submit(`X-CSRF-Token` header == `ekp_csrf` cookie,constant-time)enforced on cookie-authenticated state-changing requests(POST/PUT/PATCH/DELETE)→ 403 on missing/mismatch;GET + Bearer-authenticated requests CSRF-exempt;now takes `request: Request`(test callers updated)— `7cca23e`
- [x] F2.5 `frontend/lib/api-client.ts` — `credentials:'include'` on all requests + `X-CSRF-Token`(from the `ekp_csrf` cookie via `getCsrfHeaders()`, exported)on non-GET;raw-fetch callers `lib/api/query.ts` `streamQuery` + `lib/api/kb.ts` `uploadDoc` also send credentials + CSRF;`frontend/lib/auth/index.ts` — `SESSION_TOKEN_STORAGE_KEY` + `readSessionBearer` removed(cookie is the self-register credential;`getBearer()` = mock dev-token / MSAL JWT only);`lib/api/auth.ts` drops the re-export + adds `VerifyEmailResponse.access_token`/`expires_in` — `7cca23e`
- [x] F2.6 `frontend/app/login/page.tsx` — drops the `localStorage.setItem(SESSION_TOKEN_STORAGE_KEY, …)` write + the now-unused import(cookie set by the response);flow still `router.push('/chat')`. `frontend/app/register/page.tsx` — no edit needed(never wrote localStorage;verify-email auto-login cookie makes Step-3 → `/chat` work)— `7cca23e`
- [x] F2.7 Tests — NEW `backend/tests/test_auth_cookie_transport.py`(17 cases:Set-Cookie shape + httpOnly/SameSite/no-Secure-in-local / verify-email auto-login + idempotent / cookie GET no-CSRF / cookie POST 403 without header / 200 with matching header / 403 mismatch / Bearer + mock-Bearer CSRF-exempt / invalid-cookie fallthrough / refresh rotation + revoke-old + 401-no-creds + mock-mode-no-cookie / logout clear+revoke);`test_auth_self_register.py::test_logout_revokes_session_token` + `test_mock_msal.py` 2 dependency tests updated for the new `get_current_user(request, …)` signature;**backend pytest 609 passed / 11 skipped**(was 607 passed / 2 failed — the 2 were the mock_msal sig mismatch, now fixed;+17 new cookie-transport tests);`tsc --noEmit` + `next lint` clean — `7cca23e`
- [x] F2.8 `docs/architecture.md` §3.7「Auth transport」note(per ADR-0022,inline-tagged amendment)+ `docs/adr/0014-*.md` References cross-link to ADR-0022(+ADR-0016, ADR-0023)+ ADR-0022 「Implementation Deliverables」F0.1+F2.1-F2.8 ticked;no new OQ(transport detail);CO_F5_refresh + CO_F5_cookie → CLOSED — `7cca23e`

## F3 — RAGAs 4-metric full integration

- [ ] F3.1 `backend/eval/` — wire `ragas` to compute Faithfulness + Answer-Correctness;keep custom Recall@5(retrieval)+ Image-Association(association)metrics;populate `EvalReport`(`backend/api/schemas/eval.py`)with real scores + per-query breakdown + `failed_queries`
- [ ] F3.2 `backend/api/routes/eval.py` `POST /eval/run` — replace the W16 F5.4 minimal-impl placeholder with the real RAGAs run;keep the W16 F5.4 async/job-id shape if it introduced one(else synchronous with an eval-set-size cap);502 on Azure-OpenAI-judge failure
- [ ] F3.3 `POST /eval/shootout` — reranker shootout uses the same RAGAs path(historical W4-W6 data already inline in V5;the live re-run computes fresh scores per reranker variant)
- [ ] F3.4 `eval-set-v1` verify(CO_W15_F1_eval_set_v1)— Glob `docs/eval-set-v1.yaml`;if exists, confirm 50-query shape;if NOT, surface as a finding in progress.md(don't fabricate ground truth — run RAGAs against `eval-set-v0` for the smoke)
- [ ] F3.5 Tests — NEW `backend/tests/test_eval_ragas.py`(mock the LLM-judge boundary — no live Azure OpenAI in CI;assert score plumbing + EvalReport shape + failed_queries population);existing eval tests pass
- [ ] F3.6 V5 Eval Console — verify in browser smoke(F5)that the 4-metric cards + Failed queries table render real RAGAs data(no frontend code change expected — consumes `EvalReport` already)

## F4 — Frontend hardening bundle — `9ee636c`

- [x] F4.1 `frontend/app/admin/kb/[id]/page.tsx` Documents tab — wired `GET /kb/{id}/documents`(real per W16 F5.1.1);NEW `frontend/lib/api/documents.ts`(`DocumentSummary` + `documentsApi.list`);renders a doc table(title + tags / format / chunks / last-indexed / doc_id)via `useQuery`;loading skeleton + error banner + empty-index Upload prompt;**dropped the stale「Backend status: GET /kb/{id}/documents — W2 listing implementation (501 stub)」copy**(`BackendStubNote` component itself preserved — still used by ChunksTab);top-of-file docstring F3.2 line updated to reflect W17 wiring — `9ee636c`
- [x] F4.2 `frontend/app/admin/page.tsx` — removed unused `CardTitle` import;`npm run lint` now green globally(it was the only ESLint error)— `9ee636c`
- [x] F4.3 `NEXT_PUBLIC_LANGFUSE_URL` — **already present** in `.env.example`(line ~101,added W16 F5.x.2 `1dbcdf3`);`frontend/app/debug/[traceId]/page.tsx` reads it via `LANGFUSE_FALLBACK_BASE`(ADR-0020 Session 2);effectively closed — no change needed;CO_W15_F2_langfuse_url → CLOSED
- [x] F4.4 Cohere reranker naming canonicalization — canonical model identifier = `Cohere-rerank-v4.0-pro`(Azure Marketplace deployment name,matches the live `.env`);aligned `backend/storage/settings.py` `cohere_rerank_model` default + `backend/retrieval/reranker/cohere.py` default + docstrings + `.env.example` `COHERE_RERANK_MODEL`;human display label `"Cohere v4.0-pro"` kept for UI;grep-verified no stray code mismatch(`cohere-rerank-v4-pro` / unqualified `rerank-v4.0-pro` — empty);ADR / audit doc historical references left per anti-pattern「keep historical narrative」— `9ee636c`

## F5 — a11y + dark-mode verification pass

- [ ] F5.1 Dark-mode visual verify — browser smoke: toggle dark mode across V1-V9;confirm `tokens.ts` `colorsDark` applied;grep `\[oklch` across `frontend/` still = 0(milestone preserved);CO_W15_F3_dark_mode_visual_verify → CLOSED
- [ ] F5.2 ARIA spot-check — register 6-box code input / login dual-path / new Documents tab / RetrievalTab(W17 inherits ADR-0021)— `aria-label` / `aria-expanded` / `role` present on interactive elements;full NVDA/JAWS/VoiceOver audit stays Tier 2(CO_W15_F3_aria_full_audit — noted, not closed)
- [ ] F5.3 Any W17-own-mess a11y gap → fixed in scope(Karpathy §1.3);pre-existing gaps → mention + defer

## F6 — Vitest + React Testing Library infrastructure scaffold

- [ ] F6.1 `frontend/package.json` devDependencies — add `vitest` + `@vitejs/plugin-react` + `@testing-library/react` + `@testing-library/jest-dom` + `jsdom`(dev deps — H2 exception per §5.2);`pnpm install` succeeds
- [ ] F6.2 NEW `frontend/vitest.config.ts` — jsdom environment + React plugin + path aliases mirroring `tsconfig.json` + `setupFiles` (jest-dom matchers)
- [ ] F6.3 NEW `frontend/tests/unit/` + 1-2 sample component tests(e.g. a token-consuming UI component renders + a small form-interaction test)— proves the harness works
- [ ] F6.4 `frontend/package.json` — `test:unit` (`vitest run`) + `test:unit:watch` (`vitest`) scripts;no conflict with `test:e2e`
- [ ] F6.5 NEW `frontend/tests/unit/README.md` — unit vs E2E vs backend-pytest boundary;Tier 2 = expand component coverage;CO_W15_F4_vitest_baseline_gap → CLOSED

## F7 — Phase closeout + W18+ rolling-JIT trigger

- [ ] F7.1 W17 phase Gate verdict landed(PASS / PARTIAL PASS / FAIL + explicit rationale per W12-W15 pattern)— plan §3 7-criterion evaluation
- [ ] F7.2 W17 progress.md retro 7 sections(What worked / What didn't / Surprises / Decisions / Carry-overs / Time tracking / Spec ref alignment)
- [ ] F7.3 ADR-0022 + ADR-0023 status → `Accepted`(landed this phase)
- [ ] F7.4 W17 plan + checklist + progress frontmatter `status` → `closed`(same commit cycle as F7 closeout)
- [ ] F7.5 W18+ phase folder NOT pre-created(rolling-JIT — kickoff post-closeout)
- [ ] F7.6 Hygiene catch-up(opportunistic, may be in-scope per F7)— `session-start.md`:C02 status / §2「v5 frozen」→ v6 / W16 status draft→active / ADR count + next-NNNN→0024 / §11 carry-overs CO18+CO_F5_*+CO_W15_F1/F2/F3/F4 → CLOSED;`COMPONENT_CATALOG.md` §11 stale「C13 Workflow Engine」note(if not already)
- [ ] F7.7 No new OQ expected;if surface → sync `decision-form.md` per R4

---

## Cross-Cutting

- [ ] Each commit references `progress.md` Day-N entry(R2)— `docs(planning):` housekeeping commits exempt
- [ ] Component tag in commit message per CC-1 — F1 = C02+C11+C12 / F2 = C08+C11 / F3 = C06+C08 / F4 = C09+C07 / F5 = cross-cutting / F6 = test harness
- [ ] OQ status sync to `decision-form.md`(R4)— no W17 critical OQ surfaced expected(Q8 4-metric-replacement note: F3 delivers the *current* 4 metrics, not a replacement set — Q8 stays deferred Tier 2)
- [ ] Risk register update — `psycopg[binary]` install vs R8 corp proxy outcome(if blocked → 5th cumulative R8 occurrence → ADR-0017 formalization trigger);R12 Azurite mismatch unchanged
- [ ] CLAUDE.md §5.1 H1 check — F1 storage-layout change covered by ADR-0023;F2 transport change covered by ADR-0022;no other architectural change
- [ ] CLAUDE.md §5.2 H2 check — `psycopg[binary]`(F1)covered by ADR-0023;Vitest/RTL/jsdom(F6)= dev-dependency exception per §5.2;no other new vendor
- [ ] CLAUDE.md §3.1/§3.2 conventions — `mypy --strict` clean on new backend modules;`tsc --noEmit` clean;ruff/eslint clean on changed files;no `any`
- [ ] CLAUDE.md §5.5 H5 — no secret commit;`DATABASE_URL` + cookie-signing-key (if any) only in `.env`(gitignored);`Secure` cookie gated on env;no PII in logs

---

**Lifecycle reminder**:呢份 checklist 衍生自 `plan.md` deliverables。新加 deliverable 必須先入 plan + §7 changelog,然後再加 checklist item。延後 item 標 🚧 + reason,**唔可以刪**未勾選 `[ ]`。
