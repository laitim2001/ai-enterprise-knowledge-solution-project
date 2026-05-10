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

- [ ] F0.1 NEW `docs/adr/0022-auth-transport-hardening.md`(httpOnly cookie + CSRF double-submit + `/auth/refresh` rotation;dual-path `get_current_user`;amends ADR-0014 transport layer)— Status `Accepted`
- [ ] F0.2 NEW `docs/adr/0023-kb-manager-persistent-backing.md`(Postgres via `psycopg`;reuse docker-compose postgres + dedicated `ekp` DB;`PostgresKBBackend` satisfies `KBStorageBackend` Protocol;in-memory fallback when `DATABASE_URL` empty)— Status `Accepted`
- [ ] F0.3 `docs/adr/README.md` index — add ADR-0022 + ADR-0023 rows;「Next NNNN」→ `0024`

## F1 — Postgres persistent backing for KB Manager + users_repo(per ADR-0023)

- [ ] F1.1 `backend/pyproject.toml` — add `psycopg[binary]` to deps(H2 — ADR-0023 covers);`uv.lock` regenerated;`uv sync` clean
- [ ] F1.2 `infrastructure/docker-compose.yml` — postgres service inits a dedicated `ekp` database(separate from Langfuse DB — e.g. `POSTGRES_MULTIPLE_DATABASES` init script or a second `postgres-ekp` service;decided in ADR-0023);`docs/setup.md §4.2` service table + `.env` template updated
- [ ] F1.3 `backend/storage/settings.py` — add `database_url: str = ""`(`postgresql://...`);`.env.example` adds `DATABASE_URL=`(commented);empty → in-memory fallback documented
- [ ] F1.4 NEW `backend/kb_management/postgres_backend.py` — `PostgresKBBackend` satisfying `KBStorageBackend` Protocol(create / list_all / get / delete / update_config / update_metadata);async `psycopg` connection or pool;`CREATE TABLE IF NOT EXISTS knowledge_bases (...)` on first connect;raises `KBNotFoundError` / `KBAlreadyExistsError`(reuse `kb_management.storage` exception classes);`KbStatus` ⇄ row mapping(JSONB for `config` + `failed_documents`)
- [ ] F1.5 `backend/api/auth/users_repo.py` — Postgres-backed path(same public interface;`CREATE TABLE IF NOT EXISTS users (...)` — id / email / display_name / password_hash / email_verified / verification_code / created_at);in-memory path preserved when `DATABASE_URL` empty
- [ ] F1.6 Dependency wiring — `kb_management.get_kb_service()` + users_repo factory select Postgres backend when `settings.database_url` set;FastAPI lifespan opens/closes the pool;no route / service call-site change(Protocol contract holds);`make_kb_backend(settings)` factory pattern mirroring `make_reranker(settings)`
- [ ] F1.7 Tests — NEW `backend/tests/test_kb_postgres_backend.py` + users-repo Postgres-path tests(skip-if-no-`DATABASE_URL` marker per existing Azure-dependent test skip pattern;OR transactional fixture if light);`test_kb_*` in-memory tests unchanged + pass;backend pytest total ≥ 593 + new
- [ ] F1.8 `docs/architecture.md` §3.4 + `docs/02-architecture/COMPONENT_CATALOG.md` C02 — status note: in-memory → Postgres-backed(amendment allowed — ADR-0023 covers the H1 storage-layout change);CO18 → CLOSED

## F2 — Auth-transport hardening: httpOnly cookie + CSRF + /auth/refresh(per ADR-0022)

- [ ] F2.1 `backend/api/routes/auth.py` — `/auth/login` + `/auth/register`(verify step)success → `Response.set_cookie("ekp_session", ..., httponly=True, samesite="lax", secure=<env!=local>, path="/", max_age=<ttl>)` + `set_cookie("ekp_csrf", <token>, httponly=False, samesite="lax", ...)`(double-submit)
- [ ] F2.2 `POST /auth/refresh` — NEW or hardened;requires a valid existing session cookie;rotates `ekp_session` + `ekp_csrf`;returns 401 if no/invalid session(no unauthenticated bootstrap)— closes CO_F5_refresh
- [ ] F2.3 `POST /auth/logout` — `delete_cookie("ekp_session")` + `delete_cookie("ekp_csrf")`
- [ ] F2.4 `backend/api/auth/dependency.py` `get_current_user` — dual-path:`ekp_session` cookie if present, else `Authorization: Bearer`(`FEATURE_AUTH_MOCK=true` + API clients keep Bearer);when cookie-authenticated AND method is state-changing(POST/PUT/PATCH/DELETE)→ require `X-CSRF-Token` header == `ekp_csrf` cookie, else 403
- [ ] F2.5 `frontend/lib/api-client.ts` — `credentials: 'include'` on all requests;on non-GET, read `ekp_csrf` cookie and send `X-CSRF-Token` header;`frontend/lib/auth/index.ts` — `getBearer()` simplified(cookie is primary;localStorage `ekp_session_token` kept only behind `NEXT_PUBLIC_AUTH_MOCK` for the mock-auth dev path)
- [ ] F2.6 `frontend/app/login/page.tsx` + `frontend/app/register/page.tsx` — stop treating localStorage as ground truth(cookie set by response);remove the now-redundant localStorage write OR guard it behind `NEXT_PUBLIC_AUTH_MOCK`;flow still `router.push('/chat')` on success
- [ ] F2.7 Tests — NEW `backend/tests/test_auth_cookie_transport.py`(Set-Cookie shape / dual-path get_current_user cookie+Bearer / CSRF reject on missing-or-mismatched header / refresh rotation / logout clears both cookies / mock-auth Bearer path unaffected);existing `test_auth_*` updated;`tsc --noEmit` clean;backend pytest pass
- [ ] F2.8 `docs/architecture.md` §3.7 transport note + `docs/adr/0014-*.md` References cross-link to ADR-0022;no new OQ(transport detail);CO_F5_refresh + CO_F5_cookie → CLOSED

## F3 — RAGAs 4-metric full integration

- [ ] F3.1 `backend/eval/` — wire `ragas` to compute Faithfulness + Answer-Correctness;keep custom Recall@5(retrieval)+ Image-Association(association)metrics;populate `EvalReport`(`backend/api/schemas/eval.py`)with real scores + per-query breakdown + `failed_queries`
- [ ] F3.2 `backend/api/routes/eval.py` `POST /eval/run` — replace the W16 F5.4 minimal-impl placeholder with the real RAGAs run;keep the W16 F5.4 async/job-id shape if it introduced one(else synchronous with an eval-set-size cap);502 on Azure-OpenAI-judge failure
- [ ] F3.3 `POST /eval/shootout` — reranker shootout uses the same RAGAs path(historical W4-W6 data already inline in V5;the live re-run computes fresh scores per reranker variant)
- [ ] F3.4 `eval-set-v1` verify(CO_W15_F1_eval_set_v1)— Glob `docs/eval-set-v1.yaml`;if exists, confirm 50-query shape;if NOT, surface as a finding in progress.md(don't fabricate ground truth — run RAGAs against `eval-set-v0` for the smoke)
- [ ] F3.5 Tests — NEW `backend/tests/test_eval_ragas.py`(mock the LLM-judge boundary — no live Azure OpenAI in CI;assert score plumbing + EvalReport shape + failed_queries population);existing eval tests pass
- [ ] F3.6 V5 Eval Console — verify in browser smoke(F5)that the 4-metric cards + Failed queries table render real RAGAs data(no frontend code change expected — consumes `EvalReport` already)

## F4 — Frontend hardening bundle

- [ ] F4.1 `frontend/app/admin/kb/[id]/page.tsx` Documents tab — wire `GET /kb/{id}/documents`(real per W16 F5.1.1;add `frontend/lib/api/documents.ts` typed client if absent → `DocumentSummary`);render doc list(title / doc_id / chunk count etc);**drop the stale「Backend status: GET /kb/{id}/documents — W2 listing implementation (501 stub)」copy**;empty state preserved
- [ ] F4.2 `frontend/app/admin/page.tsx` — remove unused `CardTitle` import(`npm run lint` green globally — Karpathy §1.3 only this orphan)
- [ ] F4.3 `frontend/.env.example` — add `NEXT_PUBLIC_LANGFUSE_URL=`(commented Beta-production endpoint placeholder);verify `frontend/app/debug/[traceId]/page.tsx` reads it(already does via `LANGFUSE_FALLBACK_BASE` per ADR-0020 frontend Session 2);CO_W15_F2_langfuse_url → CLOSED
- [ ] F4.4 Cohere reranker naming canonicalization — canonical model identifier = `Cohere-rerank-v4.0-pro`(actual Azure Marketplace deployment name per `.env`);align `backend/storage/settings.py` `cohere_rerank_model` default + `backend/.env.example` to it;keep human display label `"Cohere v4.0-pro"` for UI(`frontend/app/admin/kb/[id]/page.tsx` RetrievalTab + V5 Eval Console);grep-verify no stray code mismatch(`cohere-rerank-v4-pro` / unqualified `rerank-v4.0-pro` in code);ADR / audit doc historical references left per anti-pattern「keep historical narrative」

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
