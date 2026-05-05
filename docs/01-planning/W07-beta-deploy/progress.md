---
phase: W07-beta-deploy
plan_ref: ./plan.md
checklist_ref: ./checklist.md
status: active     # flipped draft→active 2026-05-05 W6 D5 stakeholder approval cycle cascade
---

# Phase W07 — Progress

> Daily progress + 結尾 retro。
> 每 commit 必須對應一個 Day-N entry mention(R2 binding rule per PROCESS.md §5)。
> Status:`active` 自 2026-05-05 W6 D5 stakeholder approval cycle cascade。

---

## Day 0 — 2026-05-05: Kickoff prep(W6 D4 末 closeout prep early-start 同 session)

**Action**:Phase W07 kickoff prep(per PROCESS.md §2.3 rolling-JIT lifecycle + W6 D4 closeout prep early-start per CLAUDE.md §10 R5 — F6 prep buffer for D5)

- Folder `docs/01-planning/W07-beta-deploy/` created
- `plan.md` filled with status=`draft`(6 deliverables F1-F6:Microsoft Entra ID auth integration + rate limiting + audit logging + error handling polish + mobile responsive complete + Phase Gate closeout + W8 kickoff prep)
- `checklist.md` derived from plan deliverables(~33 atomic items)
- `progress.md` Day 0 entry initialized(this file)
- **Carry-over candidates from W06-final-eval-demo**(per W6 retro § Carry-overs C1-C10):
  - C1 F2 final eval Chris SME labeling cascade → background polish if labeling lands W7
  - C2 F3 subset=20 confirmation → ad-hoc trigger if stakeholder approves
  - C3 F4 W4/W5 LIVE smoke remainder → **W7 D1 sync-point with Chris**(PPT E2E + GPT-5.5 latency + Chat UI screenshots)
  - C4 F5.4 demo screenshots → polish window post-Chris dev server availability
  - C5 architecture.md §3.2 + §6.3 amendment → stakeholder approval cycle vNext
  - C6 RAGAs evaluator REFUSAL_PHRASE skip → optional W7+ polish
  - C7 R8 mitigation update entry to `RISK_REGISTER.md` → **W7 D1 housekeeping**(Python httpx probe ground truth pattern documentation)
  - C8 F3 L3 routing conditional → defer Tier 2(STRONG PASS upgrade trigger 唔 fire)
  - C9 Q-deps for Beta:Q7+Q9+Q10+**Q11 W7 critical path**+Q12 — stakeholder approval cycle for W7-W8 kickoff
  - C10 Plan estimate calibration:LIVE deploy 2x;static 0.5x — applied to W7 plan §2 effort estimates
- **W7 critical path identification**:**Q11 Entra ID tenant access** must IT confirm by W7 D1 — blocks F1.1 → F1.7 cascade。Fallback = mock auth dev mode for D1-D3 development;若 W7 D5 仍未 confirm → F1 LIVE smoke defer W8(Beta-blocking)
- **POC closeout context**:W6 closes Tier 1 12-week sprint POC phase(W1-W6 portion);W7-W8 = Beta deploy(Microsoft Entra ID + rate limiting + React polish + Beta deploy);W9-W10 = Beta internal testing;W11-W12 = staged rollout 25% → 100% production launch per architecture.md §6.1 timeline。

**Status update at W6 D5 closeout cascade(2026-05-05 same-session)**:Stakeholder approve 4 points landed → W6 frontmatter `active → closed` + Q11 decision-level approve(Ricoh 統一 tenant via Entra ID;W7 D1 IT operational confirm cascade trigger;fallback mock auth dev mode preserved per F1.1 if IT slips)→ **W07 status `draft → active` 2026-05-05**(this entry)。

---

## Day 0 cont — 2026-05-05: W7 phase activation post-stakeholder approval cycle

**Action**:W6 D5 stakeholder approval cycle cascade landed → W7 phase activation:

- Stakeholder approval cycle outcome(2026-05-05 same-session):
  - **Approval 1+2** architecture.md §3.2 + §6.3 amendment **APPROVED** → architecture.md v5 → v5.1 increment + ADR-0012 formal record(`docs/adr/0012-cohere-v4-pro-upgrade-and-gate2-partial-pass.md`)
  - **Approval 3** 5 OQ Resolved batch:**Q7 Q9 Q10 Q11 Q12** all `Resolved` 2026-05-05 — Q12 explicit Chris as Tier 2 owner;Q11 decision-level approve unblocks W7 active flip
  - **Approval 4** Beta plan v1 **APPROVED** → `docs/03-implementation/beta-plan-v1.md` status `draft → active`
- W7 plan/checklist/progress frontmatter status `draft → active`(this batch)
- ~~W7 D1 critical path:Q11 IT operational confirm cascade trigger~~ → **a-revised 2026-05-05 same-session**:Chris IT engagement(Deliverable A Tenant Access + B App Registration + C Owner Identification)moved **W8 D1 Beta deploy phase entry**(per `beta-plan-v1.md §2 W8.F1` alignment);W7 D1 implementation start **不再 IT-blocked**

### a-revised mock auth dev mode strategy(2026-05-05 W6 D5 closeout same-session)

**Karpathy §1.1 think-before-coding outcome**:Q11 IT cred 屬 **W8 deploy-time dependency**,non W7 dev-time dependency。MSAL library + middleware + login flow UI + token refresh logic 全部可以 with **mock identity provider**(`backend/api/auth/mock_msal.py` returning fixed dummy user identity)做 W7 D1-D5。

**Strategy details**:
- `Settings.feature_auth_mock: bool = False`(default production gate)— W7 dev set True via `.env`;W8 D4 切回 False post-IT cred delivery
- FastAPI Depends pattern single switching point:`auth_dependency = get_current_user_mock if settings.feature_auth_mock else get_current_user_msal`
- F1.7-mock W7 closeout substitute(verify mock auth end-to-end on local dev server);LIVE F1.7 推 W8 D4 natural deploy-time gate
- F1.2.1 NEW `backend/api/auth/mock_msal.py` dev-only middleware
- W7 plan §1 + §2 F1 + §3 G1' + §4 R1 + §5 day-by-day + §7 changelog row 全部 updated

**Saved cost**:eliminates W7 D1 IT engagement bottleneck;W7 全 5 deliverable 並行 unblocked;F1.7 LIVE 自然推 W8 D4 deploy-time gate。

**Architecture impact zero**(per CLAUDE.md §5.1 H1 boundary check):Settings flag + FastAPI Depends pattern preserves C11 component design intent;non-architectural change。

### Decisions / OQ summary

- Q7 + Q9 + Q10 + Q11 + Q12 — all `Resolved` 2026-05-05 W6 D5 stakeholder approval cycle
- Q11 decision-level Resolved 2026-05-05;**operational IT cred cascade trigger moved W8 D1**(per a-revised mock auth strategy)
- ADR-0012 — formal record landed(architecture.md v5 → v5.1 amendment + Gate 2 PARTIAL PASS verdict)
- Phase status W07 `draft → active` 2026-05-05;W7 plan + checklist + progress a-revised mock auth path landed same-session

### Open / blocked

- ⏸ W7 D1 implementation start ready(non-blocked per a-revised — F1.2 MSAL library scaffold + F1.2.1 mock middleware + F1.3-F1.6 + F2-F5 全部 並行 unblocked)
- ⏸ W8 D1 Q11 IT operational cascade trigger awaiting beta deploy phase entry(per `beta-plan-v1.md §2 W8.F1`)
- ⏸ R-B1 active monitor:W8 D5 仍未 IT confirm → Beta-blocking escalation

### Commit reference

- W6 D5 stakeholder approval cycle cascade commit `b3a63f0`(architecture amendment + ADR-0012 + 5 OQ resolved + beta-plan active + session-start sync + W7 active)
- _(W7 a-revised mock auth path commit pending — references plan + checklist + progress 3-file batch + plan changelog row 2026-05-05 a-revised)_

---

## Day 1 — 2026-05-12: F1.2 + F1.2.1 mock auth dev mode scaffold

**Action**:W7 D1 implementation kickoff per a-revised mock auth dev mode strategy(plan §2 F1)— `backend/api/auth/` + `frontend/lib/auth/` scaffold + `Settings.feature_auth_mock` flag + 7 unit tests landed。

**Backend deliverables**(C11 component spine):
- `backend/storage/settings.py` — `feature_auth_mock: bool = False` flag(default production gate;W7 dev set True via `.env`;W8 D4 切回 False LIVE switch)+ `auth_mock_oid` / `auth_mock_tid` / `auth_mock_preferred_username` / `auth_mock_bearer_token` mock identity payload Settings(matches real MSAL JWT claim shape)
- `backend/api/auth/__init__.py` NEW — barrel re-export `get_current_user` + `AuthenticatedUser`
- `backend/api/auth/models.py` NEW — `AuthenticatedUser` Pydantic model(`oid` + `tid` + `preferred_username` + `is_mock`)
- `backend/api/auth/mock_msal.py` NEW(F1.2.1) — dev-only middleware,`Settings.auth_mock_bearer_token` accept rule;invalid bearer / missing creds / wrong scheme 各自 401 with `WWW-Authenticate: Bearer` header(real MSAL future contract preserved)
- `backend/api/auth/msal_provider.py` NEW(F1.2 skeleton) — fail-closed 503 stub;real JWKS + signature + audience/issuer + expiry validation 留 W8 D2-D3 IT cred delivery 後 cascade
- `backend/api/auth/dependency.py` NEW(F1.3 pre-wire) — single FastAPI Depends switching point:`get_current_user` flag-guards `authenticate_mock` vs `authenticate_msal`;F1.3 D2 wiring on `backend/api/main.py` lifespan 一行 import edit

**Frontend deliverables**(C09 + C10 共用):
- `frontend/lib/auth/types.ts` NEW — `AuthenticatedUser` + `AuthBearer` TS interface(mirrors backend Pydantic shape)
- `frontend/lib/auth/mock_msal.ts` NEW(F1.2.1) — fixed dev-token bearer + `_DEV_USER` claim;`loginMock` / `logoutMock` no-op stubs
- `frontend/lib/auth/msal_provider.ts` NEW(F1.2 skeleton) — fail-closed throw stub;real PublicClientApplication + MsalProvider + redirect flow 留 W8 D2-D3
- `frontend/lib/auth/index.ts` NEW — barrel single switching point:`NEXT_PUBLIC_AUTH_MOCK=true` → mock path;false / unset → msal_provider path(W8 D4 LIVE switch)

**Tests**(F1.6 partial):
- `backend/tests/test_mock_msal.py` NEW — 7 unit tests:accept dev-token + return _DEV_USER;reject missing creds 401;reject wrong scheme 401;reject invalid token 401;msal_provider skeleton fails-closed 503;dependency routes mock when flag True;dependency routes msal when flag False(503 stub)

**Verification**:
- `.venv/Scripts/python.exe -m pytest -q` → **222 passed in 171.24s**(W6 baseline 215 + new 7 mock_msal tests;zero regression)
- `.venv/Scripts/python.exe -m ruff check api/auth tests/test_mock_msal.py storage/settings.py` → All checks passed!
- `npx tsc --noEmit`(frontend)→ exit 0(clean)
- 68 ruff baseline scripts/ truststore E402 unchanged(non-target)

**Karpathy §1 alignment**:
- §1.1 think-before-coding:Annotated dependency pattern matched existing `kb.py:12` repo convention(B008 dodge);MSAL skeleton fail-closed 503 prevents silent auth bypass
- §1.2 simplicity-first:zero new external dep — mock middleware uses existing `fastapi.security.HTTPBearer` + Pydantic;no msal SDK install yet(W8 D2-D3 trigger when LIVE)
- §1.3 surgical:`feature_auth_mock=False` default = zero impact production code path;new files only,no edit to existing routers / lifespan / main.py(F1.3 D2 +1 import line scope)
- §1.4 goal-driven:`mock auth dev mode scaffold + tests + zero regression` = verifiable;222/222 + tsc 0 + ruff 0 closed loop

**Hard constraints check**(per CLAUDE.md §5):
- H1 architecture lock — ✅ no §3 / §4 component change;C11 design intent preserved per plan §2 F1.2.1 explicit boundary check
- H2 vendor lock — ✅ no new dep added(msal SDK install deferred W8 D2-D3 per beta-plan-v1.md §2 W8.F1)
- H3 Dify reference — ✅ untouched
- H4 Tier 1 boundary — ✅ single-tenant mock identity only;multi-tenancy explicit OUT
- H5 security — ✅ `feature_auth_mock=False` default production gate;`.env` gitignored;no hard-code tenant ID / connection string
- H6 test coverage — ✅ critical module(C11 auth)synced 7 tests with code

### Decisions / OQ summary
- No OQ change(Q11 already Resolved 2026-05-05 W6 D5;operational IT cred cascade trigger W8 D1 unchanged per beta-plan-v1.md)
- No ADR triggered(architecture impact zero per plan §2 F1 a-revised CLAUDE.md §5.1 H1 boundary check)

### Open / blocked
- ⏸ F1.3 main.py lifespan auth middleware wire — W7 D2 trigger(use `get_current_user` Depends on protected routes `/query/**` + `/kb/**`;`/health` 公開保留)
- ⏸ F1.4 login flow UI(C09 Admin + C10 Chat hamburger user menu)— W7 D2 trigger
- ⏸ F1.5 token refresh + logout endpoint — W7 D3 trigger
- ⏸ F1.6 full middleware integration tests(reject unauth route + valid token allow + expired token reject mocked MSAL)— W7 D3 trigger(D1 covers F1.2.1 scope only)
- ⏸ F2 + F3 sequential after F1.3 wired(D2-D3)
- ⏸ W6 C7 R8 mitigation `RISK_REGISTER.md` entry — already landed W6 D5 closeout housekeeping per session-start §11(no W7 D1 cascade required)

### Commit reference
- W7 D1 F1.2 + F1.2.1 commit `85269f1`(13 files changed,+446 / -4;9 new files + 4 modified;backend C11 auth scaffold + frontend lib/auth/ scaffold + 7 unit tests + Settings.feature_auth_mock flag)

---

---

## Day 2 — 2026-05-13: F1.3 + F1.4 + F2 wired

**Action**:W7 D2 — auth Depends router-level wire(F1.3)+ frontend bearer injection + login flow UI(F1.4)+ token-bucket rate limiter middleware(F2.1-F2.3)。

**Backend(C08 + C11)**:
- `backend/api/server.py` — `Depends(get_current_user)` router-level wired on `/query/**` + `/kb/**` + `/feedback`(per plan §2 F1.3 字面 scope + feedback rides query workflow);documents/chunks/eval/screenshots/debug 公開保留 W8 cascade scope;`/health` 公開保留 ACA liveness probe target
- `backend/api/middleware/__init__.py` + `rate_limit.py` NEW — `RateLimitMiddleware`(BaseHTTPMiddleware token-bucket + concurrent counter,per-key oid/ip resolution shares auth scaffold validators,zero new external dep per Karpathy §1.2)
- `backend/api/server.py` — `app.add_middleware(RateLimitMiddleware, ...)` scoped to same protected prefixes as auth(`("/query", "/kb", "/feedback")`);F1.3 + F2 lock-step
- `backend/storage/settings.py` — `rate_limit_enabled` / `rate_limit_per_minute=50` / `rate_limit_concurrent=5`(architecture.md §8.1 R5 spec)
- `.env.example` — FEATURE_AUTH_MOCK + RATE_LIMIT_* + NEXT_PUBLIC_AUTH_MOCK 一齊加,backend/frontend single switching point sync hint

**Frontend(C09 admin shell + C11 auth state)**:
- `frontend/lib/api-client.ts` — `buildAuthHeader()` injects Bearer header on every GET/POST/PATCH from `lib/auth/getBearer()` switching point;msal_provider skeleton throw → caller sees backend 401 cleanly
- `frontend/lib/providers/auth-provider.tsx` NEW — Zustand `useAuthStore`(idle/loading/authenticated/error states + signIn / signOut / setUserFromCache);AuthProvider component auto-signs-in mock mode,manual click for MSAL W8+
- `frontend/components/auth/user-menu.tsx` NEW — `<UserMenu>` shows preferredUsername + `[mock]` badge + sign-out CTA;C09 admin shell upper-right header
- `frontend/app/admin/layout.tsx` — wrapped with `<AuthProvider>` outside QueryProvider;new header bar holding `<UserMenu>`

**Tests**:
- `backend/tests/test_auth_routes.py` NEW — 5 integration tests:public route no-auth + protected route reject no-bearer 401 + accept dev-token 200 + reject wrong token 401 + 503 fail-closed when mock disabled
- `backend/tests/test_rate_limit.py` NEW — 9 unit + integration tests:within-budget allowed + burst exceed + concurrent cap + per-key isolation + middleware integration(allow + 429 + skip unprotected + disabled flag + IP fallback + release reset)
- `backend/tests/test_api_skeleton.py` — module-level `app.dependency_overrides[get_current_user]` shim preserves W6 baseline test behavior post-F1.3 wire
- 30/30 W7 D1+D2 tests pass(7 mock_msal + 5 auth_routes + 9 rate_limit + 9 api_skeleton);full suite verified clean

**Verification**:
- `pytest -q` → **237 passed in 55.80s**(W6 baseline 215 + W7 D1 +7 mock_msal + W7 D2 +5 auth_routes + +9 rate_limit + 1 implicit fixture = +22 vs W6;zero regression)
- `ruff check api/middleware api/auth tests/test_rate_limit.py tests/test_auth_routes.py tests/test_mock_msal.py tests/test_api_skeleton.py storage/settings.py` → All checks passed
- `tsc --noEmit`(frontend)→ exit 0
- `eslint --max-warnings=0 lib/auth lib/providers/auth-provider.tsx lib/api-client.ts components/auth app/admin/layout.tsx` → exit 0

**Karpathy §1 alignment**:
- §1.1 think-before-coding:rate limiter middleware vs Depends — chose middleware for clean acquire/release try-finally semantics on exception path;path-prefix scope matches auth scope so F1.3 + F2 stay lock-step
- §1.2 simplicity-first:token bucket implemented from scratch ~50 lines instead of slowapi/limits new dep;zero msal SDK install yet(W8 D2-D3 trigger when LIVE)
- §1.3 surgical:server.py +1 import +1 middleware register +3-line dependencies arg on 3 routers — zero edit to route files (`query.py`/`kb.py`/`feedback.py`);frontend admin layout add 2 wrappers + 1 header bar(other routes untouched W7 D2 scope)
- §1.4 goal-driven:`F1.3+F1.4+F2 wired + 30/30 tests + ruff/tsc/eslint clean + zero regression` = verifiable;closed loop per task

**Hard constraints check**:
- H1 architecture lock — ✅ no §3 / §4 component change;C08 + C11 design intent preserved;rate limiter per architecture.md §8.1 R5 spec
- H2 vendor lock — ✅ zero new dep added(token bucket from-scratch + zustand + fastapi.security all pre-existing)
- H3 Dify reference — ✅ untouched
- H4 Tier 1 boundary — ✅ single-tenant only(rate-key per-`oid`,Tier 2 multi-tenancy 唔滲入)
- H5 security — ✅ Authorization header secret only flows through Settings flag-guarded code path;no secret commit;`.env.example` placeholder only
- H6 test coverage — ✅ critical modules(C08 middleware + C11 auth)synced 14 new tests with code

### Decisions / OQ summary
- No OQ change(Q11 unchanged decision-level Resolved 2026-05-05;operational IT cred trigger W8 D1)
- No ADR triggered(architecture impact zero — middleware class implements existing §8.1 R5 spec)

### Open / blocked
- ⏸ F1.5 token refresh logic + logout endpoint — W7 D3 trigger
- ⏸ F1.6 full middleware integration tests(unauth 401 + valid token allow + expired token reject mocked MSAL)— W7 D3 trigger(D2 covers F1.3 + auth-routes 401/200/503 paths;F1.6 spec adds explicit "expired token" via mocked JWT exp claim — defer until msal_provider real wire W8 D2-D3)
- ⏸ F3 audit logging — W7 D3 trigger;use mock `oid` + `tid` tags
- ⏸ F4 + F5 — W7 D4-D5

### Commit reference
- W7 D2 F1.3 + F1.4 + F2 commit `5c72bfe`(14 files changed,+794 / -33;6 new files + 8 modified;backend middleware + auth wire + frontend auth provider + UserMenu + 14 new tests)

---

---

## Day 3 — 2026-05-14: F1.5 + F1.6 + F2.5 + F3 audit logging

**Action**:W7 D3 — `/auth/refresh` + `/auth/logout` endpoints(F1.5),F1.6 expanded mocked-MSAL valid + expired token tests,rate-limit Langfuse cost-monitoring tag(F2.5),audit log middleware F3.1 + schema doc F3.2 + redaction policy F3.3 + unit tests F3.4。F3.5 LIVE smoke deferred per W6 C3 dev server availability carry-over。

**Backend(C07 + C08 + C11)**:
- `backend/api/schemas/auth.py` NEW — `RefreshResponse` + `LogoutResponse` Pydantic models
- `backend/api/routes/auth.py` NEW — `POST /auth/refresh`(mock returns same dev-token + 1h expiry;real MSAL skeleton 503 W8 D2-D3 trigger)+ `POST /auth/logout`(stateless mock no-op;real MSAL revoke + Entra ID logout redirect W8+);both endpoints in-route Depends(get_current_user) so unauth 401 reject before route body
- `backend/api/server.py` — `/auth/**` registered + added to `_PROTECTED_PREFIXES`(rate limit + audit scope)
- `backend/api/middleware/rate_limit.py` — F2.5 emit `rate_limit_exceeded` structlog event with identity_key + path + method + retry_after_s on 429 path(W8 cost dashboard data source)
- `backend/api/middleware/audit_log.py` NEW(F3.1)— `AuditLogMiddleware` BaseHTTPMiddleware:request_id(uuid4 if absent or echoed input header)+ user_id(mock/real `oid`)+ tenant_id(`tid`)+ audit_action(METHOD path)+ status_code + duration_ms;outermost in Starlette stack so 429 仍 audited;identity reuse `authenticate_{mock,msal}` matched F1.3 + F2 keys
- `backend/api/middleware/__init__.py` — export `AuditLogMiddleware` + `REQUEST_ID_HEADER`
- `backend/api/server.py` — `app.add_middleware(AuditLogMiddleware, ...)` registered after RateLimitMiddleware so audit sits OUTERMOST per Starlette stacking semantics

**Frontend(C11)**:
- `frontend/lib/auth/mock_msal.ts` — `logoutMock` 加 fetch `/auth/logout`(integration smoke for F1.7-mock W7 D5)+ `refreshMock` returns same dev-token
- `frontend/lib/auth/msal_provider.ts` — `refreshMsal` skeleton throw 503-equivalent
- `frontend/lib/auth/index.ts` — barrel export `refresh()` switching point

**Doc(F3.2)**:
- `docs/02-architecture/audit-log-schema.md` NEW(10 sections)— purpose / schema / field reference / **redaction policy CLAUDE.md §5.5 H5 alignment** / retention / wiring / verification / cross-component deps / Tier 2 boundaries / update history

**Tests**:
- `backend/tests/test_auth_endpoints.py` NEW — 5 tests F1.5(refresh dev-token + reject unauth + 503 mock disabled + logout ok + reject unauth)
- `backend/tests/test_audit_log.py` NEW — 6 tests F3.4(tag presence on protected + skip unscoped /health + null user on unauth + Authorization redaction + request_id round-trip echo + uuid4 generation when missing)
- `backend/tests/test_auth_routes.py` — 2 NEW F1.6 expanded(mocked-MSAL valid token 200 + expired token 401 via monkeypatch authenticate_msal — locks F1.3 contract switching point treats LIVE identical to mock,distinguishes 401 expired from 503 not-yet-wired)

**Verification**:
- `pytest -q` → **250 passed in 153.63s**(W6 baseline 215 + W7 D1 +7 + W7 D2 +15 = 237 + W7 D3 +13 = 250;zero regression)
- `ruff check api/middleware api/auth api/routes/auth.py api/schemas/auth.py tests/test_audit_log.py tests/test_auth_endpoints.py tests/test_auth_routes.py tests/test_rate_limit.py tests/test_mock_msal.py tests/test_api_skeleton.py storage/settings.py` → All checks passed
- `tsc --noEmit`(frontend)→ exit 0
- `eslint --max-warnings=0`(touched files)→ exit 0

**Karpathy §1 alignment**:
- §1.1 think-before-coding:audit middleware ordering — outermost wraps rate limiter so 429 仍 captured;rate-limit Langfuse tag uses structlog(JSON renderer 已 wired via `init_tracer`)而 non Langfuse SDK direct call(W3+ scope per `langfuse_tracer.py:4` baseline);F1.5 `/auth/refresh` 503 fallback distinguishes "not yet wired" vs "expired token 401"
- §1.2 simplicity-first:audit middleware single class ~80 LOC;identity resolution shares same `authenticate_{mock,msal}` validators(no duplicate JWT parsing logic);redaction policy = positive list(only emit allowed fields)not regex denylist
- §1.3 surgical:F1.5 endpoints in dedicated `routes/auth.py`(no edit to existing route files);F2.5 +1 structlog warning call inside existing 429 branch;F3 server.py +1 import +1 add_middleware call
- §1.4 goal-driven:`F1.5 + F1.6 + F2.5 + F3 + 13 new tests + zero regression + ruff/tsc/eslint clean` = verifiable;closed loop

**Hard constraints check**:
- H1 architecture lock — ✅ no §3 / §4 component change;C07 audit-log-schema.md formal record 屬 §7.4 Day-2 Readiness implementation per architecture spec
- H2 vendor lock — ✅ zero new dep added(structlog + uuid + starlette pre-existing)
- H3 Dify reference — ✅ untouched
- H4 Tier 1 boundary — ✅ single-tenant only(audit `tenant_id` 來自 mock single tid;multi-tenant aggregation queries explicit Tier 2 per audit-log-schema.md §9)
- H5 security & privacy — ✅ F3.3 redaction policy enforced:no request body / no response body / no Authorization value / no secret/key/token header in audit event;F3.4 test_audit_redacts_authorization_header verifies
- H6 test coverage — ✅ critical modules(C07 audit + C11 auth endpoints)synced 13 new tests with code

### Decisions / OQ summary
- No OQ change(Q11 unchanged decision-level Resolved 2026-05-05)
- No ADR triggered(audit-log-schema.md 屬 architecture.md §7.4 Day-2 Readiness implementation,non-architectural amendment per CLAUDE.md §5.1 H1 boundary)

### Open / blocked
- ⏸ F1.7-mock(W7 closeout substitute)— W7 D5 trigger per plan §5;curl `/query` Bearer dev-token end-to-end smoke + verify F2 rate-key + F3 audit-tag integration
- ⏸ F3.5 LIVE smoke(5 query through dev server → Langfuse trace 顯示 audit tags + request_id traceable)— deferred per W6 C3 Chris dev server availability carry-over;若 W7 D4-D5 dev server 可用即 trigger,否則 W8 D1+D4 cascade post-IT engagement
- ⏸ F4(error handling polish)— W7 D4 trigger
- ⏸ F5(mobile responsive)— W7 D4-D5
- ⏸ Real Langfuse SDK trace export(currently structlog stub per `langfuse_tracer.py:4`)— W3+ original scope;F2.5 + F3.1 events 已 JSON formatted ready for SDK switch when wired

### Commit reference
- W7 D3 commit `7fc885a`(15 files changed,+791 / -18;6 new files + 9 modified;F1.5 auth endpoints + F2.5 cost tag + F3.1 audit middleware + F3.2 schema doc + F3.3 redaction enforcement + F3.4 unit tests + F1.6 expanded tests + 13 new tests)

---

---

## Day 4 — 2026-05-15: F4 error handling polish + F5 mobile kickoff

**Action**:W7 D4 — uniform ApiError envelope contract(F4.1)+ UI error boundary(F4.2)+ E1-E14 mapping doc(F4.3)+ error contract unit tests(F4.4)+ mobile responsive kickoff(F5.1 audit + F5.2 hamburger nav);F4.5 LIVE smoke + F5.4 viewport smoke deferred per dev server / W7 D5 schedule。

**Backend(C08)**:
- `backend/api/schemas/errors.py` NEW — `ApiErrorBody` + `ApiErrorResponse` Pydantic models + `ErrorCodes` constants(13 codes covering auth / rate-limit / validation / resource / pipeline / refusal / generic)
- `backend/api/error_handlers.py` NEW — F4.1 unified handlers:
  - `http_exception_handler` maps Starlette/FastAPI HTTPException → envelope(401/403/404/409/429/502/503/504 → corresponding ErrorCodes)
  - `validation_exception_handler` maps RequestValidationError → 422 + `validation.invalid_payload` OR `validation.query_too_long`(E6 detection via `string_too_long` Pydantic type)without leaking input values(CLAUDE.md §5.5 H5 redaction)
  - `unhandled_exception_handler` server-side structlog `unhandled_exception` event;client-side generic 500 + safe message(NO stack trace / NO exception detail leak)
- `backend/api/server.py` — `register_error_handlers(app)` wired before middleware so middleware-raised HTTPException all flow through envelope
- `backend/api/middleware/rate_limit.py` — 429 path now emits envelope shape directly(matches F4.1 contract)

**Frontend(C09 + C10 共用)**:
- `frontend/lib/api-client.ts` — `ApiErrorEnvelope` interface;`ApiError` 加 `code` / `actionableHint` fields;`buildApiError()` parses backend envelope or falls back to generic;all GET/POST/PATCH error path routed
- `frontend/components/error/error-boundary.tsx` NEW(F4.2)— `<ErrorBoundaryView>` reusable component:title / code / status / message / actionable_hint / Retry CTA(reset)/ Report CTA(GitHub for now,W8 EKP support channel cascade)
- `frontend/app/error.tsx` NEW — App Router root error UI;catches client-side rendering + unhandled API failures
- `frontend/app/admin/error.tsx` NEW — `/admin` segment scoped error UI(scope="Admin" without tearing down auth state)

**Frontend(C09 mobile shell)**:
- `frontend/components/nav/admin-shell.tsx` NEW(F5.2)— mobile-aware admin shell client component:sidebar `< md` off-canvas drawer + hamburger button + dimmed overlay + auto-close on nav tap;`>= md` static W2 D5 desktop layout preserved verbatim;touch targets `min-h-[40px]`;`aria-expanded` accessibility
- `frontend/app/admin/layout.tsx` — extracted shell to `<AdminShell>` keeping providers(Auth + Query)on server component side per Next.js convention

**Doc(F4.3 + F5.1)**:
- `docs/02-architecture/error-cases-E1-E14.md` NEW(7 sections)— mapping E1-E14 architecture.md §7.3 → API outcome / UI surface / observability / F4.5 LIVE smoke trigger;F4.4 unit-test verification matrix;F4.5 LIVE smoke plan(E1+E5+E12 priority);Tier 2 boundaries
- `docs/02-architecture/responsive-audit-W7.md` NEW(8 sections)— Tailwind breakpoints / per-view audit / F5.2 hamburger implementation / F5.3 citation card mobile UX **DEFERRED** rationale(C10 not yet built)/ F5.4 viewport smoke plan W7 D5(5 viewports)/ F5.5 pixel diff snapshots **DEFERRED W8** rationale(no Vitest/Playwright snapshot harness)

**Tests**:
- `backend/tests/test_error_contract.py` NEW — 10 tests F4.4(401 auth / 404 not found / 409 conflict / 502 retrieval / 503 synthesis / **504 LLM timeout E5** / unhandled exception redacts internals / **422 query too long E6** / 422 invalid payload generic / actionable_hint present)
- 53/53 W7 D1-D4 tests pass(7 mock_msal + 7 auth_routes + 5 auth_endpoints + 6 audit_log + 9 rate_limit + 9 api_skeleton + 10 error_contract);full suite verified clean

**Verification**:
- `pytest -q` → **260 passed in 142.93s**(W7 D3 baseline 250 + F4.4 +10 = 260;zero regression)
- `ruff check api/error_handlers.py api/middleware api/auth api/routes/auth.py api/schemas/auth.py api/schemas/errors.py tests/{test_error_contract,test_audit_log,test_auth_endpoints,test_auth_routes,test_rate_limit,test_mock_msal,test_api_skeleton}.py storage/settings.py` → All checks passed
- `tsc --noEmit`(frontend)→ exit 0
- `eslint --max-warnings=0`(touched files)→ exit 0

**Karpathy §1 alignment**:
- §1.1 think-before-coding:envelope wired via FastAPI exception_handler(applies retroactively to all routes,including middleware-raised HTTPException via 401/403)而 non-route-level adapter — single source of truth;rate limit middleware's direct Response build matches envelope shape inline(non-HTTPException path)
- §1.2 simplicity-first:F5.3 + F5.5 honestly DEFERRED with rationale instead of building a stubbed CitationCard or installing Playwright snapshot harness — defer-with-reason 比 partial-build cleaner per W6 C10 calibration(static work 0.5x);F4.5 LIVE smoke deferred per dev server availability(W6 C3 carry-over)
- §1.3 surgical:server.py +1 import +1 call;rate_limit.py inline-replace 429 Response body;layout.tsx replaces inline shell with `<AdminShell>` component import 而非 in-place rewrite;每 deferred item 標明 trigger condition
- §1.4 goal-driven:`F4.1+F4.2+F4.3+F4.4+F5.1+F5.2 + 10 new tests + zero regression + ruff/tsc/eslint clean` = verifiable;closed loop per task

**Hard constraints check**:
- H1 architecture lock — ✅ no §3 / §4 component change;error-cases-E1-E14 + responsive-audit 屬 §7.3 + §6.1 implementation living docs(non-architectural amendment per CLAUDE.md §5.1 H1 boundary)
- H2 vendor lock — ✅ zero new dep added(structlog + uuid + starlette + lucide-react pre-existing,actually inline-svg hamburger 唔 import lucide for snapshot stability per Karpathy §1.2)
- H3 Dify reference — ✅ untouched(layout.tsx Dify Image 4 注釋 preserved as reference-only)
- H4 Tier 1 boundary — ✅ E10 OCR Tier 2 explicit;multi-modal retrieval explicit OUT
- H5 security & privacy — ✅ F4.1 redaction enforced:unhandled_exception_handler structured-logs server-side full repr but client-side returns generic message;F4.4 test_unhandled_exception_envelope_redacts_internals verifies "RuntimeError" + "secret_password" 不出現 in response
- H6 test coverage — ✅ critical module(C08 error_handlers + middleware)synced 10 new tests with code

### Decisions / OQ summary
- No OQ change(Q11 unchanged decision-level Resolved 2026-05-05)
- No ADR triggered(error_handlers + responsive-audit 屬 architecture.md §7.3 + §6.1 implementation,non-architectural amendment)

### Open / blocked
- ⏸ F4.5 LIVE smoke(E1 grounded refusal + E5 LLM timeout + E12 chunk_id collision)— deferred per W6 C3 dev server availability carry-over;若 W7 D5 dev server 可用 trigger,否則 W8 D1+D4 cascade post-IT engagement
- ⏸ F5.3 citation card mobile UX — deferred until C10 Chat UI built(rolling-JIT scope per session-start §3 status `⏳ Not started`)
- ⏸ F5.4 viewport smoke 5 widths — W7 D5 trigger
- ⏸ F5.5 pixel diff snapshots — DEFERRED W8(no Vitest/Playwright snapshot harness;adding = scope creep;W6 C10 calibration applied)
- ⏸ F1.7-mock(W7 closeout substitute)— W7 D5 trigger per plan §5
- ⏸ F6 closeout — W7 D5

### Commit reference
- _(W7 D4 commit pending — references progress.md Day 4 + checklist F4.1 + F4.2 + F4.3 + F4.4 + F5.1 + F5.2 ticked + F5.3 + F5.5 deferred 標明)_

---

---

## Day 5 — _(pending)_

---

## Retro(填於 W7 D5 末)

### What worked
_(W7 D5 末 fill)_

### What didn't work / unexpected friction
_(W7 D5 末)_

### Surprises / discoveries
_(W7 D5 末)_

### Carry-overs to W08-beta-deploy-sprint2
_(W7 D5 末)_

### ADR triggers
_(W7 D5 末 — ADR-0012 reserved for(a)architecture.md §3.2 amendment formal record stakeholder approval cycle outcome OR(b)Tier 2 reranker swap if real-query distribution diverges)_

### Phase Gate result(per plan.md §3 + architecture.md §7 acceptance)
- G1-G7:_(W7 D5 末)_
- **W7 Beta hardening verdict**:_(W7 D5 末)_ → ready for W8 Azure Container Apps + Static Web Apps deploy / require additional polish

### Phase status
- Closeout commit:_(W7 D5 末)_
- Frontmatter status flipped to `closed`:_(W7 D5 末)_
- Phase W08 kickoff trigger:_(W7 D5 末 — W8 plan = Azure Container Apps + Static Web Apps + cost monitoring + user feedback dashboard + Beta smoke test per architecture.md §6.1 W8 row)_

---
