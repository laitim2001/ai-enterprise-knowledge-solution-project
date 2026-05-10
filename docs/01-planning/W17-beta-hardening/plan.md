---
phase: W17-beta-hardening
name: "Beta Hardening — persistent storage (Postgres per ADR-0023) + auth-transport hardening (httpOnly cookie + CSRF + /auth/refresh per ADR-0022) + RAGAs 4-metric integration + frontend hardening bundle + Vitest/RTL infra + a11y/dark-mode verify"
sprint_week: W17
start_date: 2026-05-10            # real-calendar — W16 F1-F4 still blocked on Track A IT cred; W17 runs the AI-controllable Beta-hardening backlog in parallel (does not depend on W16 closeout)
end_date: 2026-05-17              # ~5-7 working days estimate (F1 Postgres + F2 cookie are the two largest deliverables; same-day collapse possible per W12-W15 precedent)
status: active                    # `active` 自 2026-05-10 — user directive 「完整地規劃和處理 類別 1（AI 可即做）+ 類別 2（ADR-first）」; W16 F1-F4 sequence preserved (blocked Track A IT cred populate event per W11 retro CO16)
spec_refs:
  - architecture.md v6 §3.4         # multi-KB + KB storage backend swap point (KBStorageBackend Protocol)
  - architecture.md v6 §3.7         # C13 Email Verification Service / hybrid auth model
  - architecture.md v6 §4.3         # application settings (storage/settings.py)
  - architecture.md v6 §5.6         # V5 Eval Console — RAGAs 4-metric consumer
  - ADR-0012                        # Cohere v4.0-pro production lock (naming-unification reference)
  - ADR-0014                        # hybrid auth model (cookie hardening amends transport layer, not the model)
  - ADR-0016                        # scrypt password hash (auth security baseline preserved)
  - ADR-0022                        # NEW this phase — auth-transport hardening (httpOnly cookie + CSRF + /auth/refresh)
  - ADR-0023                        # NEW this phase — KB Manager + users_repo persistent backing (Postgres via psycopg)
prior_phase: W16-beta-deploy        # W16 status: draft (F1-F4 blocked Track A IT cred; F5 backend stub closure cascade done) — W17 runs in parallel, not strictly after
related_artifacts:
  - docs/02-architecture/audit-W15-d5-vs-spec.md     # §7 future-ADR candidates — 0022 cookie migration / 0023 persistent backing source
  - docs/01-planning/W16-beta-deploy/progress.md     # W16 carry-overs CO_F5_refresh / CO_F5_cookie / CO18 / CO_W15_F2_langfuse_url + audit-tail dev-infra
  - backend/kb_management/storage.py                  # KBStorageBackend Protocol + InMemoryKBBackend — F1 adds PostgresKBBackend satisfying the same Protocol
  - backend/kb_management/service.py                  # KBService — backend injected; F1 dependency-override swap, no call-site change
  - backend/api/auth/users_repo.py                   # F1 adds Postgres-backed user store
  - backend/api/auth/dependency.py                   # F2 get_current_user dual-path (cookie OR Bearer)
  - backend/api/routes/auth.py                       # F2 login/register/refresh set httpOnly Set-Cookie + CSRF
  - backend/eval/                                    # F3 RAGAs 4-metric integration target (ragas already installed)
  - infrastructure/docker-compose.yml                # F1 — dedicated `ekp` Postgres database on the existing postgres service
  - frontend/lib/api-client.ts                       # F2 credentials:'include' + CSRF header
  - frontend/lib/auth/index.ts                       # F2 getBearer() simplification post-cookie
  - frontend/app/admin/kb/[id]/page.tsx              # F4 Documents tab — wire real GET /kb/{id}/documents, drop stale "501 stub" copy
  - frontend/app/admin/page.tsx                      # F4 unused-import (CardTitle) lint fix
  - frontend/.env.example                            # F4 NEXT_PUBLIC_LANGFUSE_URL + Cohere reranker naming canonicalization
---

# Phase W17 — Beta Hardening

> **Plan version**:1.0(draft 2026-05-10 — rolling JIT per CLAUDE.md §10 R1;triggered by user directive to fully plan + handle the Category-1 / Category-2 Beta-hardening backlog identified from session-start.md §11 carry-overs + audit-W15-d5-vs-spec.md §7)
> **Owner**:Chris(Tech Lead + stakeholder)+ AI(implementation)
> **Approved by**:Chris — storage backend = Postgres via psycopg + cookie hardening = do-now-in-W17(AskUserQuestion 2026-05-10),= the H1/H2「approved + write ADR」authorization for ADR-0022 + ADR-0023

---

## 1. Scope

W17 = **Beta Hardening sprint** — closes the AI-controllable subset of the Beta-hardening backlog so the platform is durable + production-shaped before Beta cohort cutover. **Out-of-scope = anything hard-blocked on the Track A IT cred populate event**(Azure DELETE cleanup / ACS `pip install azure-communication-email` / `.env.production` / Cohere Marketplace billing wiring)— those stay in W16 F1-F4 and are NOT W17 deliverables. W17 runs in parallel with W16's blocked state.

Goals:

- **Persistent storage backing**(per ADR-0023)— KB Manager(`kb_management`)+ `users_repo` move from process-local in-memory to Postgres(via `psycopg`,reusing the docker-compose postgres service with a dedicated `ekp` database). `KBStorageBackend` Protocol satisfied by a new `PostgresKBBackend`;dependency-override swap;in-memory backend preserved as the no-`DATABASE_URL` fallback(local/CI). Closes CO18 — restart no longer wipes KBs + users.
- **Auth-transport hardening**(per ADR-0022)— `/auth/login` + `/auth/register`(verify)+ `/auth/refresh` issue an httpOnly `Set-Cookie` session token + a CSRF token(double-submit pattern);`get_current_user` reads the cookie OR an `Authorization: Bearer` header(dual-path — API clients / mock-auth keep Bearer). Frontend `api-client` sends `credentials:'include'` + the CSRF header;`/auth/refresh` self-register session rotation lands here(closes CO_F5_refresh + CO_F5_cookie). localStorage token retained only as a graceful fallback for the mock-auth dev path.
- **RAGAs 4-metric full integration**(`ragas` already installed)— `backend/eval/` actually computes Recall@5 / Faithfulness / Answer-Correctness / Image-Association against the eval set;`POST /eval/run` returns a real populated `EvalReport`(replaces the W16 F5.4 minimal-impl placeholder per CO_W15_F1_backend RAGAs-deferral note). V5 Eval Console consumes it unchanged.
- **Frontend hardening bundle** — (a) KB-detail Documents tab wires the real `GET /kb/{id}/documents`(W16 F5.1.1 CO_F3a already implemented backend-side)+ drops the stale「501 stub」copy;(b) `frontend/app/admin/page.tsx` unused-import(`CardTitle`)cleanup → `npm run lint` green;(c) `NEXT_PUBLIC_LANGFUSE_URL` formalized in `.env.example`(Debug View already reads it with a fallback — close CO_W15_F2_langfuse_url);(d) Cohere reranker naming canonicalization across `.env` / `.env.example` / `settings.py` / UI labels(one canonical identifier + a separate human display label).
- **a11y + dark-mode verification pass** — browser smoke: dark-mode toggle across V1-V9(verify `tokens.ts` `colorsDark` applied);ARIA spot-check on the W13 auth pages + KB tabs(full NVDA/JAWS/VoiceOver audit stays Tier 2 — CO_W15_F3_aria_full_audit).
- **Vitest + React Testing Library infrastructure scaffold** — `vitest.config.ts` + jsdom + `@testing-library/react`(dev deps — H2 exception per §5.2)+ 1-2 sample component tests + `test:unit` script;closes CO_W15_F4_vitest_baseline_gap(Playwright E2E layer stays for golden-path).
- **Phase closeout** + W18+ rolling-JIT trigger.

**Out of W17 scope**(stay W16 / W18+ / Tier 2):
- Track A IT cred items — Azure DELETE cleanup(KB delete drops Azure index / blob container)/ ACS `pip install azure-communication-email` / `.env.production` / Cohere Marketplace billing(W16 F1)
- 25% Beta cohort rollout activation + daily metric monitor + Q15 first weekly signal report(W16 F2-F3 — Beta phase)
- Full screen-reader audit NVDA/JAWS/VoiceOver(Tier 2 — CO_W15_F3_aria_full_audit)
- Full interactive register/login + KB upload + Pipeline wizard E2E(Tier 2 — CO_W15_F4_interactive_flow_E2E;W17 F6 scaffolds the unit-test layer only)
- Forgot password / 2FA / OAuth providers(Tier 2 per architecture.md v6 §11)
- Per-doc upload/reindex/delete real wiring(W2 multi-format ingestion + Track A — still 501 stub;only `GET /kb/{id}/documents` listing is wired W17 F4)

**Pre-condition for W17 promotion**(satisfied 2026-05-10):
- User directive「先完整地規劃和處理 類別 1 + 類別 2」received
- H1/H2 decisions made — storage = Postgres via psycopg / cookie hardening = do-now(= ADR-0022 + ADR-0023 write authorization)
- W16 F1-F4 remain `draft` blocked Track A — W17 explicitly does not depend on W16 closeout(parallel track)

## 2. Deliverables(F1-F7)

### F1 — Postgres persistent backing for KB Manager + users_repo(per ADR-0023)

- **Component(s)**:**C02** Knowledge Base Manager + **C11** Identity & Access + **C12** DevOps & Infra
- **Spec ref**:architecture.md v6 §3.4 multi-KB + KBStorageBackend Protocol swap point;ADR-0023
- **OQ deps**:none(Q11 operational-Resolved unaffected — auth provider unchanged)
- **Acceptance criteria**:
  - F1.1 `psycopg[binary]` added to `backend/pyproject.toml` deps(H2 — covered by ADR-0023);`uv.lock` regenerated
  - F1.2 `infrastructure/docker-compose.yml` — postgres service exposes / inits a dedicated `ekp` database(separate from the Langfuse DB);`setup.md §4.2` table updated
  - F1.3 `DATABASE_URL` env var added to `storage/settings.py`(`postgresql://...`,default empty)+ `.env.example`;empty → in-memory fallback(local / CI preserve W1 behaviour)
  - F1.4 `backend/kb_management/postgres_backend.py`(NEW)— `PostgresKBBackend` satisfying the `KBStorageBackend` Protocol(create / list_all / get / delete / update_config / update_metadata)+ `CREATE TABLE IF NOT EXISTS knowledge_bases (...)` on first connect;async via `psycopg` async connection / pool;raises the same `KBNotFoundError` / `KBAlreadyExistsError`
  - F1.5 `backend/api/auth/users_repo.py` — Postgres-backed user store path(same public interface;`CREATE TABLE IF NOT EXISTS users (...)`)+ in-memory fallback when `DATABASE_URL` empty
  - F1.6 Dependency wiring — `get_kb_service()` / users_repo factory pick Postgres backend when `DATABASE_URL` set;FastAPI `app.state` / `lru_cache` lifecycle;no change to route or service call-sites(Protocol contract holds)
  - F1.7 Tests — `backend/tests/test_kb_postgres_backend.py` + users-repo Postgres-path tests(use a transactional fixture / `testing.postgresql`-style or skip-if-no-DB marker per existing test patterns);in-memory path tests unchanged + still pass
  - F1.8 `architecture.md` §3.4 / `COMPONENT_CATALOG.md` C02 status note: in-memory → Postgres-backed(amendment is allowed — ADR-0023 covers the storage-layout change per H1)
- **Effort estimate**:2 days(W17 D1-D2 — largest deliverable;DB schema + async psycopg DAL + fixture plumbing)
- **Owner**:AI(implementation)+ user(review)

### F2 — Auth-transport hardening: httpOnly cookie + CSRF + /auth/refresh(per ADR-0022)

- **Component(s)**:**C08** API Gateway + **C11** Identity & Access
- **Spec ref**:architecture.md v6 §3.7 hybrid auth;ADR-0014(model unchanged — transport layer hardened);ADR-0016(scrypt baseline preserved);ADR-0022
- **OQ deps**:Q11(operational-Resolved unaffected — SSO/MSAL path's token handling separate;cookie path is for the self-register branch)
- **Acceptance criteria**:
  - F2.1 `/auth/login` + `/auth/register`(email-verify step)success → set httpOnly `Set-Cookie` `ekp_session`(`Secure` in non-local env / `SameSite=Lax` / `Path=/` / `Max-Age` per session TTL)+ a readable `ekp_csrf` cookie(double-submit token)
  - F2.2 `POST /auth/refresh`(NEW or hardened)— rotates the session cookie + CSRF token;requires a valid existing session(no unauthenticated bootstrap)— closes CO_F5_refresh
  - F2.3 `POST /auth/logout` — clears both cookies
  - F2.4 `get_current_user`(`backend/api/auth/dependency.py`)— dual-path:read `ekp_session` cookie if present, else `Authorization: Bearer`(API clients + `FEATURE_AUTH_MOCK=true` keep Bearer);CSRF check enforced on cookie-authenticated state-changing requests(`X-CSRF-Token` header must match `ekp_csrf` cookie)
  - F2.5 Frontend `lib/api-client.ts` — `credentials:'include'` on requests + send `X-CSRF-Token` from the `ekp_csrf` cookie on non-GET;`lib/auth/index.ts` `getBearer()` simplified(cookie is the primary credential transport;localStorage `ekp_session_token` retained only as the mock-auth dev fallback)
  - F2.6 Frontend `app/login/page.tsx` + `app/register/page.tsx` — stop relying on localStorage as ground truth(cookie is set by the response);keep the localStorage write behind a `NEXT_PUBLIC_AUTH_MOCK` guard or remove if redundant
  - F2.7 Tests — `backend/tests/test_auth_cookie_transport.py`(Set-Cookie shape / dual-path get_current_user / CSRF reject / refresh rotation / logout clears)+ existing `test_auth_*` updated for the new transport;frontend `tsc --noEmit` clean
  - F2.8 `architecture.md` §3.7 transport note + `decision-form.md` — no new OQ(transport detail, not a model decision);ADR-0014 References cross-link to ADR-0022
- **Effort estimate**:1.5 days(W17 D3 + D4 first half)
- **Owner**:AI(implementation)+ user(review — confirm SameSite / Secure policy acceptable for the Beta domain `ekp-beta.ricoh.com`)

### F3 — RAGAs 4-metric full integration

- **Component(s)**:**C06** Eval Framework + **C08** API Gateway(eval/run)
- **Spec ref**:architecture.md v6 §5.6 V5 Eval Console;eval-methodology.md;`ragas` already installed(no H2)
- **OQ deps**:Q8(4-metric replacement deferred Tier 2 — Gate 2 PARTIAL PASS confirmed, not triggered;this delivers the *current* 4 metrics, not a replacement set)
- **Acceptance criteria**:
  - F3.1 `backend/eval/` — wire `ragas` to compute Faithfulness + Answer-Correctness(+ keep the custom Recall@5 retrieval metric + Image-Association association metric)against the eval set;`EvalReport`(`backend/api/schemas/eval.py`)populated with real scores + per-query breakdown + `failed_queries`
  - F3.2 `POST /eval/run` — replaces the W16 F5.4 minimal-impl placeholder with the real RAGAs run(may be slow → keep the existing async/job-id shape if W16 F5.4 introduced one;else synchronous with a reasonable eval-set size cap)
  - F3.3 `POST /eval/shootout` — reranker shootout uses the same RAGAs path(historical W4-W6 data already inline in V5;the live re-run path computes fresh scores)
  - F3.4 `eval-set-v1` file existence verify(CO_W15_F1_eval_set_v1)— confirm / create `docs/eval-set-v1.yaml`(W4+W5 +20 real-query = 50 queries);if the file genuinely doesn't exist, surface that as a finding(don't fabricate ground truth)
  - F3.5 Tests — `backend/tests/test_eval_ragas.py`(RAGAs invocation mocked at the LLM-judge boundary — no live Azure OpenAI in CI;assert score plumbing + EvalReport shape);existing eval tests pass
  - F3.6 V5 Eval Console — no frontend change needed(consumes `EvalReport` already);verify the 4-metric cards + Failed queries table render real data in the browser smoke(F5)
- **Effort estimate**:1.5 days(W17 D4 second half + D5)
- **Owner**:AI(implementation)+ user(review)

### F4 — Frontend hardening bundle

- **Component(s)**:**C09** Admin Console UI + **C07** Observability Stack(Langfuse URL)+ cross-cutting(naming)
- **Spec ref**:architecture.md v6 §5.x admin views;ADR-0012(Cohere naming reference)
- **OQ deps**:none
- **Acceptance criteria**:
  - F4.1 KB-detail Documents tab(`frontend/app/admin/kb/[id]/page.tsx`)— wire `GET /kb/{id}/documents`(real backend per W16 F5.1.1;add `frontend/lib/api/documents.ts` typed client if not present)→ render a doc list(title / doc_id / chunk count / etc per `DocumentSummary`);drop the stale「Backend status: ... (501 stub)」copy;empty state preserved
  - F4.2 `frontend/app/admin/page.tsx` — remove the unused `CardTitle` import(`npm run lint` → green globally;Karpathy §1.3 surgical — only this orphan)
  - F4.3 `NEXT_PUBLIC_LANGFUSE_URL` — add to `.env.example`(commented, Beta-production endpoint placeholder);verify `frontend/app/debug/[traceId]/page.tsx` reads it(it already does with the `LANGFUSE_FALLBACK_BASE` fallback per ADR-0020 frontend Session 2)→ close CO_W15_F2_langfuse_url
  - F4.4 Cohere reranker naming canonicalization — pick the canonical model-identifier string(the actual Azure Marketplace deployment name `Cohere-rerank-v4.0-pro` per `.env`)and align `settings.py` default + `.env.example` to it;keep a separate human display label `"Cohere v4.0-pro"` for UI;grep-verify no stray `cohere-rerank-v4-pro` / `rerank-v4.0-pro` mismatch remains in code(docs `cohere-v4.0-pro` references in ADRs/audit are historical narrative — left per anti-pattern「keep historical narrative」)
- **Effort estimate**:0.5 day(W17 D5 — small, surgical)
- **Owner**:AI(implementation)+ user(visual review of the Documents tab)

### F5 — a11y + dark-mode verification pass

- **Component(s)**:cross-cutting(C09 + C10 + C11 views)
- **Spec ref**:architecture.md v6 §5.8 cross-view UX;design-ref §3 consistency rules;tokens.ts `colorsDark`
- **OQ deps**:F1-F4 baseline(so the verified state includes the W17 changes)
- **Acceptance criteria**:
  - F5.1 Dark-mode visual verify — browser smoke: toggle dark mode(UserMenu / theme button)across V1 Chat / V2 Admin Dashboard / V3 KB List / V4 KB Detail tabs / V5 Eval Console / V6 Debug View / V7 Landing / V8 Login / V9 Register;confirm `tokens.ts` `colorsDark` applied(no `[oklch(...)]` regressions — global=0 milestone preserved)— close CO_W15_F3_dark_mode_visual_verify
  - F5.2 ARIA spot-check — the W13 auth pages(register 6-box code input / login dual-path)+ the new Documents tab + the RetrievalTab(W17 inherits ADR-0021)— `aria-label` / `aria-expanded` / `role` present on interactive elements;full NVDA/JAWS/VoiceOver audit stays Tier 2(CO_W15_F3_aria_full_audit) — note explicitly
  - F5.3 Any a11y gap found that is W17's own mess(per Karpathy §1.3)→ fixed in scope;pre-existing gaps → mention, defer
- **Effort estimate**:0.5 day(W17 D5)
- **Owner**:AI(browser smoke)+ user(keyboard nav + screen-reader spot-check)

### F6 — Vitest + React Testing Library infrastructure scaffold

- **Component(s)**:cross-cutting governance(frontend test harness)
- **Spec ref**:CLAUDE.md §3.2 test framework(「Vitest + React Testing Library」— never actually set up per W15 D4 finding)
- **OQ deps**:none
- **Acceptance criteria**:
  - F6.1 `vitest` + `@vitejs/plugin-react` + `@testing-library/react` + `@testing-library/jest-dom` + `jsdom` added to `frontend/devDependencies`(dev deps — H2 exception per §5.2);`pnpm install` succeeds(R8 proxy doesn't block npm registry per W15 precedent)
  - F6.2 `frontend/vitest.config.ts`(NEW)— jsdom environment + React plugin + path aliases mirroring `tsconfig.json` + `setup` file
  - F6.3 `frontend/tests/unit/` directory + 1-2 sample component tests(e.g. a token-consuming component + a small form interaction)— proves the harness works
  - F6.4 `package.json` `test:unit` script(`vitest run`);`test:unit:watch`(`vitest`);does not conflict with `test:e2e`(Playwright stays separate)
  - F6.5 `tests/unit/README.md` — what's unit-tested vs E2E vs backend pytest;Tier 2 = expand component coverage
- **Effort estimate**:0.5 day(W17 D5)
- **Owner**:AI(implementation)

### F7 — Phase closeout + W18+ rolling-JIT trigger

- **Component(s)**:cross-cutting governance
- **Spec ref**:CLAUDE.md §10 R1 rolling-JIT + R5 closeout discipline
- **OQ deps**:F1-F6 verdict outcomes
- **Acceptance criteria**:
  - F7.1 W17 phase Gate verdict landed(PASS / PARTIAL PASS / FAIL with explicit rationale per the W12-W15 pattern)
  - F7.2 W17 progress.md retro 7 sections(What worked / What didn't / Surprises / Decisions / Carry-overs / Time tracking / Spec ref alignment)
  - F7.3 ADR-0022 + ADR-0023 status → `Accepted`(landed this phase)
  - F7.4 W17 plan + checklist + progress frontmatter `status` → `closed`
  - F7.5 W18+ phase folder NOT pre-created(rolling-JIT — kickoff post-W17-closeout decision;likely candidates = W16 F1-F4 if Track A IT cred lands, OR Tier 2 prep)
  - F7.6 session-start.md / COMPONENT_CATALOG.md hygiene catch-up(opportunistic): C02 status in-memory → Postgres-backed;§2「v5 frozen」→ v6;W16 status draft→active(F5 done);ADR count + next-NNNN(→ 0024)— done as part of closeout if not already
  - F7.7 No new OQ expected;if surface → sync decision-form.md per R4
- **Effort estimate**:0.5 day(W17 D6 or absorbed into D5)
- **Owner**:AI(draft)+ user(approve + sign-off)

---

## 3. Success Criteria(Phase Gate)

W17 phase Gate **PASS condition**:
1. F1 Postgres backing — KBs + users survive a backend restart;in-memory fallback preserved when `DATABASE_URL` empty;tests pass ✅
2. F2 Auth-transport — httpOnly cookie + CSRF + `/auth/refresh` work;dual-path `get_current_user`(cookie OR Bearer);mock-auth dev path still works;tests pass ✅
3. F3 RAGAs — `POST /eval/run` returns a real populated `EvalReport`;V5 Eval Console renders real 4-metric data;tests pass ✅
4. F4 Frontend bundle — Documents tab shows real docs;`npm run lint` green;`NEXT_PUBLIC_LANGFUSE_URL` formalized;Cohere naming unified ✅
5. F5 a11y + dark-mode verified across V1-V9 ✅
6. F6 Vitest + RTL harness works(1-2 sample tests pass)✅
7. F7 closeout + W18+ rolling-JIT trigger ✅

W17 phase Gate **PARTIAL PASS** acceptable per Karpathy §1.4:
- F1.7 Postgres test fixture deferred to a skip-if-no-DB marker if a clean transactional fixture proves heavy(in-memory path tests + a manual `docker compose up` smoke suffice for Tier 1)
- F3.4 `eval-set-v1.yaml` — if the file genuinely doesn't exist, surface it as a finding + run RAGAs against `eval-set-v0` for the smoke(don't fabricate ground truth)
- F5.2 ARIA — spot-check only;full screen-reader audit stays Tier 2
- F6 — sample tests are render/smoke level;deep component coverage stays Tier 2

W17 phase Gate **FAIL condition**:
- ADR-0022 / ADR-0023 scope creep into Tier 2(multi-tenancy / GraphRAG / OAuth providers)
- In-memory fallback broken(local / CI must still run without Postgres)
- mock-auth dev path broken by the cookie change(browser smoke + Playwright webServer must still work)
- Backend pytest baseline regression(currently 593 passed / 7 skipped)

## 4. Risks(Phase-Specific)

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| `pip install psycopg[binary]` blocked by R8 corp proxy | Medium | High | `psycopg[binary]` ships wheels via PyPI(not a separate CDN like Playwright browsers / ACS SDK);if blocked → 5th cumulative R8 occurrence → ADR-0017 formalization trigger;fallback = `psycopg` pure-python(needs libpq) or stdlib path. If truly blocked, F1 PARTIAL — keep in-memory + add `scripts/seed_dev_kb.py` for dev convenience and re-scope F1 to W18+ |
| Postgres test fixture plumbing heavier than estimated | Medium | Low | skip-if-no-`DATABASE_URL` marker(matches the existing Azure-dependent test skip pattern);in-memory path tests carry the coverage |
| Cookie `Secure` + `SameSite` policy wrong for the Beta domain | Low | Medium | `Secure` gated on `environment != "local"`;`SameSite=Lax`(SSO redirect-friendly);user reviews F2.8 before closeout |
| RAGAs run too slow / Azure OpenAI judge cost in CI | Medium | Low | CI mocks the LLM-judge boundary(F3.5);live runs are user-triggered + eval-set-size-capped per existing eval-methodology.md |
| Cookie change breaks the mock-auth Playwright webServer / browser smoke | Low | High | dual-path `get_current_user` keeps Bearer working;`FEATURE_AUTH_MOCK=true` path explicitly tested(F2.7);browser smoke re-run before closeout |
| Scope balloon — F1 + F2 + F3 are each ~1.5-2 days | High | Medium | Strict per-deliverable acceptance criteria;PARTIAL PASS allowances above;F4-F6 are small/surgical buffers;same-day collapse acceptable per W12-W15 precedent but not forced |

## 5. Day-by-Day Breakdown(rough)

| Day | Date(tentative) | Focus |
|---|---|---|
| W17 D1 | 2026-05-10 | ADR-0022 + ADR-0023 written + README index;F1 start — `psycopg` dep + docker-compose `ekp` DB + `DATABASE_URL` setting + `PostgresKBBackend` skeleton |
| W17 D2 | 2026-05-11 | F1 cont — `PostgresKBBackend` + Postgres users_repo + dependency wiring + tests;F1.8 doc note |
| W17 D3 | 2026-05-12 | F2 — cookie + CSRF + `/auth/refresh` + dual-path `get_current_user`(backend);F2 frontend api-client + auth lib |
| W17 D4 | 2026-05-13 | F2 tests + closeout;F3 start — RAGAs wiring in `backend/eval/` + `POST /eval/run` real impl |
| W17 D5 | 2026-05-14 | F3 cont + tests + eval-set-v1 verify;F4 frontend bundle;F5 a11y + dark-mode browser smoke;F6 Vitest scaffold |
| W17 D6 | 2026-05-15 | F7 closeout — Gate verdict + retro + ADR Accepted + frontmatter close + W18+ trigger + hygiene catch-up |

**Day-by-day caveat**:dates tentative;real-calendar collapse possible per the W12-W15 Time-tracking calibration(phase capacity has run far under plan-day budget when pivot momentum is clean). If overflow:F5/F6/F7 absorb into a later day or W18+ D1. The `start_date`/`end_date` frontmatter is a window, not a commitment.

## 6. Dependencies on Prior Phase / Carry-overs Addressed

From session-start.md §11 + W16 progress.md carry-overs — W17 directly addresses:
- **CO18** KB Manager + users_repo persistent backing → **F1**(exact match;ADR-0023)
- **CO_F5_refresh** `/auth/refresh` self-register session rotation → **F2.2**(exact match)
- **CO_F5_cookie** httpOnly cookie hardening → **F2**(exact match;ADR-0022)
- **CO_W15_F1_backend RAGAs-deferral** RAGAs 4-metric full integration → **F3**(exact match)
- **CO_W15_F1_eval_set_v1** eval-set-v1 file existence verify → **F3.4**
- **CO_W15_F2_langfuse_url** `NEXT_PUBLIC_LANGFUSE_URL` Beta env var → **F4.3**
- **CO_W15_F3_dark_mode_visual_verify** → **F5.1**
- **CO_W15_F4_vitest_baseline_gap** → **F6**
- `admin/page.tsx` `CardTitle` lint orphan(noted W16 progress Day 1)→ **F4.2**
- Cohere reranker naming inconsistency(noted session-start.md §11 / Day-1 follow-up)→ **F4.4**

W17 does **NOT** address(stay W16 / W18+ / Tier 2):
- CO16 Track A IT cred populate event + R-B1 closure(W16 F1 — external dependency)
- CO19 25% Beta cohort rollout activation(W16 F2 — Beta phase)
- CO17 AF3 code fix + personal Azure dev tier formalization(ADR-0013 reserved)
- CO_F6a/b/c ACS email retry / BackgroundTasks / SPF-DKIM(Track A — W16 F1 / IT-side)
- CO_W15_F3_aria_full_audit / CO_W15_F4_interactive_flow_E2E(Tier 2)
- Azure DELETE cleanup(KB delete drop index / blob container — Track A)

## 7. Plan Changelog

| Date | Change | Reason | Approver |
|---|---|---|---|
| 2026-05-10 | Initial draft + `status: active` | User directive「先完整地規劃和處理 類別 1（AI 可即做，無 H1/H2，無外部依賴）+ 類別 2（要先決策 / ADR）」;Category-3 Track-A-blocked items explicitly excluded(stay W16). H1/H2 decisions made via AskUserQuestion 2026-05-10:storage backend = Postgres via psycopg(→ ADR-0023)、cookie hardening = do-now-in-W17(→ ADR-0022)= the「approved + write ADR」authorization per CLAUDE.md §5.1 / §5.2 | Chris(stakeholder + architecture decision owner)|
| 2026-05-10 (D1) | F0 ADRs landed(`6edd9ef`)+ F4 frontend hardening bundle landed(`9ee636c`)— F4.1 reframed from「implement backend」to「wire frontend + drop stale 501-stub copy」(backend `GET /kb/{id}/documents` already implemented W16 F5.1.1 / CO_F3a — surfaced in the Day-0 pre-kickoff grep verification per CO_W14_process_grep_verify);F4.3 NEXT_PUBLIC_LANGFUSE_URL already in `.env.example`(W16 F5.x.2)— no change | Stakeholder authorization「(A) 直接開工(F4 trivials 先,然後 F1)」;technical reframe per Karpathy §1.1 think-before-coding upfront verification | Chris |
| 2026-05-10 (D2) | F1 part 1 — Postgres KB backend landed(`2453a50`). **Deviation 1**:plan §F1.6「lifespan opens/closes the pool」→ connection-per-op via psycopg async(Tier 1 KB ops infrequent + off the query hot path — no pool warranted;`CREATE TABLE IF NOT EXISTS` on connect,race-free)— per Karpathy §1.2 simplicity-first(ADR-0023 already permitted「connection / pool」). **Deviation 2 / blocker**:`pip install psycopg[binary]` is **R8 corp-proxy-blocked**(IncompleteRead / connection-timed-out mid-download of the 3.6 MB wheel — same hard-block pattern as Playwright browsers W15 + ACS SDK W13 + argon2-cffi W13 + Cohere SDK W3)→ **5th cumulative R8 occurrence → ADR-0017 formalization trigger met** + a **vendor-decision pivot point**(the approver chose `psycopg`;if it can't be installed in the dev / deploy environment, the choice may need revisiting). F1 verdict = **PARTIAL** pending the user decision:(A)keep `psycopg` + defer local Postgres verification to W18+ / personal Azure dev tier(CO17)+ formalize ADR-0017 now;(B)pivot storage to stdlib `sqlite3`(zero new dep — no R8 risk;the AI's original recommendation);(C)defer F1 entirely to W18+. F1.5(users_repo Postgres path)+ F1.8(architecture.md / COMPONENT_CATALOG C02 status note)held pending the decision | R8 corp proxy(non-AI-controllable);per CLAUDE.md §5(vendor-decision-affected obstacle)+ §13(when in doubt → ask) → stop-and-ask | Chris(decision pending) |

---

**Lifecycle reminder**:呢份 plan `status=active`(2026-05-10,per user directive)。重大 deviation 入第 7 節 changelog(per R3)。Next-phase folder(W18+)**唔會** pre-create(per CLAUDE.md §10 R1 rolling-JIT)。
