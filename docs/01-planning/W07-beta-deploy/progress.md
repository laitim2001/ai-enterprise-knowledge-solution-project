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
- _(W7 D2 commit pending — references progress.md Day 2 + checklist F1.3 + F1.4 + F2.1-F2.3 + F2.4 ticked)_

---

---

## Day 3 — _(pending)_

---

## Day 4 — _(pending)_

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
