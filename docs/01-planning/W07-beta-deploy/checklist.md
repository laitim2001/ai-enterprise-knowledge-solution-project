---
phase: W07-beta-deploy
plan_ref: ./plan.md
status: active
last_updated: 2026-05-15
---

# Phase W07 — Checklist

> Atomic checkbox(每 item ≤ 0.5–2 hour effort per W6 C10 calibration:LIVE deploy days × 2;static days × 0.5)。
> Status:`active` 自 2026-05-05 W6 D5 stakeholder approval cycle cascade。
> 全 unchecked 至 W7 D1 implementation start。

## F1 — Microsoft Entra ID auth integration(C11,W7 mock auth dev mode path per a-revised 2026-05-05)

- [ ] ~~**CRITICAL Q11 IT** F1.1 IT confirm Ricoh Entra ID tenant access~~ → **DEFERRED W8 D1** per a-revised mock auth strategy(Q11 decision-level Resolved 2026-05-05;operational IT cred cascade trigger moved Beta deploy phase entry per `beta-plan-v1.md §2 W8.F1`)
- [x] F1.2 MSAL Python SDK + msal-react integration scaffold(`backend/api/auth/` + `frontend/lib/auth/`)— **W7 D1 done 2026-05-12** — library skeleton + import + barrel re-export(msal SDK install 推 W8 D2-D3 per Karpathy §1.2 — current scaffold uses fastapi.security.HTTPBearer + Pydantic only,zero new dep);msal_provider.py / .ts fail-closed 503 / throw stub
- [x] **F1.2.1 NEW** `backend/api/auth/mock_msal.py` dev-only middleware + `Settings.feature_auth_mock: bool = False` flag — **W7 D1 done 2026-05-12** — `auth_mock_oid` / `auth_mock_tid` / `auth_mock_preferred_username` / `auth_mock_bearer_token` Settings;7 unit tests pass
- [x] F1.3 Auth middleware — **W7 D2 done 2026-05-13** — wired router-level on `server.py` `/query/**` + `/kb/**` + `/feedback`(feedback rides query workflow);`/health` 公開保留;`Depends(get_current_user)` from `api.auth.dependency` single switching point;documents/chunks/eval/screenshots/debug 公開保留 W8 cascade scope per beta-plan-v1.md §2 W8.F1
- [x] F1.4 Login flow UI(C09 Admin + C10 Chat)— **W7 D2 done 2026-05-13** — `frontend/lib/api-client.ts` Authorization Bearer header injection on every request via `lib/auth/getBearer()`;`frontend/lib/providers/auth-provider.tsx` Zustand store(idle/loading/authenticated/error)+ `<AuthProvider>` auto-signs-in mock mode;`frontend/components/auth/user-menu.tsx` UserMenu component shown in admin layout header(name + [mock] badge + sign out);Chat UI integration W7 D3 cascade if needed
- [x] F1.5 Token refresh logic + logout endpoints — **W7 D3 done 2026-05-14** — `backend/api/routes/auth.py` `POST /auth/refresh`(mock returns same dev-token + 1h expiry;real MSAL skeleton 503 W8 D2-D3)+ `POST /auth/logout`(mock no-op + real MSAL skeleton 留 W8);`/auth/**` rate-limited + audited;5 unit tests pass
- [x] F1.6 Unit tests — **W7 D3 done 2026-05-14** — `tests/test_auth_routes.py` 7 tests(public no-auth + reject no-bearer + accept dev-token + reject wrong token + 503 mock-disabled + mocked-MSAL valid 200 + mocked-MSAL expired 401);`tests/test_mock_msal.py` 7 unit tests(W7 D1);`tests/test_auth_endpoints.py` 5 tests(W7 D3 F1.5)— covers reject unauth + valid token allow + expired token reject contract
- [ ] ~~F1.7 LIVE smoke:dev tenant Entra ID end-to-end login flow on local dev server~~ → **DEFERRED W8 D4** post-IT cred delivery cascade(`Settings.feature_auth_mock=False` switch + real Entra ID redirect flow)
- [ ] **F1.7-mock NEW W7 closeout substitute** — verify mock auth dev mode end-to-end:`Settings.feature_auth_mock=True` + curl `/query` Bearer dev-token → middleware accept → return `_DEV_USER`;invalid bearer reject 401;F2 rate-key + F3 audit tag 用 mock `oid` 完整 trace

## F2 — Rate limiting middleware per-user concurrency cap(C08 + C11)

- [ ] F2.1 Token-bucket rate limiter middleware(per-user + per-IP fallback)— configurable via Settings
- [ ] F2.2 Rate limit thresholds Settings:50 req/min per user + 5 concurrent active queries(architecture.md §8.1 R5 spec)
- [ ] F2.3 429 response with Retry-After header on exceed
- [ ] F2.4 Unit tests:burst within budget OK + burst exceed → 429;concurrent cap enforce
- [x] F2.5 Cost monitoring — **W7 D3 done 2026-05-14** — `rate_limit.py` emits `rate_limit_exceeded` structlog warning(identity_key + path + method + retry_after_s)on 429 path;structlog JSON renderer(`langfuse_tracer.init_tracer`)→ Langfuse SDK W3+ wire pickup ready;W8 cost dashboard data source

## F3 — Audit logging per-query trail(C07)

- [x] F3.1 Audit log middleware — **W7 D3 done 2026-05-14** — `backend/api/middleware/audit_log.py` `AuditLogMiddleware`:request_id(uuid4 if absent or echo input X-Request-ID header)+ user_id(mock/real `oid`)+ tenant_id(`tid`)+ audit_action(METHOD path)+ status_code + duration_ms;outermost in Starlette stack so 429 仍 audited
- [x] F3.2 Audit-specific tag schema document — **W7 D3 done 2026-05-14** — `docs/02-architecture/audit-log-schema.md` NEW(10 sections:purpose / schema example / field reference / **F3.3 redaction policy CLAUDE.md §5.5 H5** / retention W7→Beta→Prod / wiring / verification / cross-component deps / Tier 2 boundaries / update history)
- [x] F3.3 Sensitive data redaction — **W7 D3 done 2026-05-14** — middleware emits ONLY allowed positive-list fields(request_id / user_id / tenant_id / audit_action / status_code / duration_ms);NEVER request body / response body / Authorization header value / secret/key/token/password headers;F3.4 test_audit_redacts_authorization_header verifies enforcement
- [x] F3.4 Unit tests — **W7 D3 done 2026-05-14** — `tests/test_audit_log.py` 6 tests:tag presence on protected + skip unscoped /health + null user on unauth + Authorization redaction + request_id round-trip echo input header + uuid4 generation when missing
- [ ] ~~F3.5 LIVE smoke~~ → **DEFERRED post-W7 D4-D5 dev server availability** — Chris dev server availability per W6 C3 carry-over;F3.5 5-query LIVE through dev server + Langfuse trace 顯示 audit tags + request_id traceable;若 W7 D4-D5 dev server 可用 trigger,否則 W8 D1+D4 cascade post-IT engagement(non-W7-blocking — F3.1-F3.4 unit-test verified)

## F4 — Error handling polish(C08 + C09 + C10)

- [x] F4.1 API error contract — **W7 D4 done 2026-05-15** — `backend/api/schemas/errors.py` `ApiErrorBody` + `ErrorCodes`(13 codes);`backend/api/error_handlers.py` `register_error_handlers` wires HTTPException + RequestValidationError + Exception → `{"error":{"code","message","actionable_hint"}}` envelope;rate limit middleware 429 emits envelope shape inline;NO raw stack trace leaks(unhandled_exception_handler logs server-side via structlog,client-side generic 500)
- [x] F4.2 UI error boundary — **W7 D4 done 2026-05-15** — `frontend/components/error/error-boundary.tsx` `<ErrorBoundaryView>` with code/status/message/actionable_hint + Retry CTA + Report CTA;`frontend/app/error.tsx` root + `frontend/app/admin/error.tsx` segment scoped;`frontend/lib/api-client.ts` `ApiError` enriched with `code` + `actionableHint` parsed from envelope
- [x] F4.3 14 edge cases mapping — **W7 D4 done 2026-05-15** — `docs/02-architecture/error-cases-E1-E14.md` NEW(7 sections)maps E1-E14 → API outcome + UI surface + observability + F4.5 LIVE smoke trigger;F4.4 unit-test verification matrix
- [x] F4.4 Unit tests — **W7 D4 done 2026-05-15** — `backend/tests/test_error_contract.py` 10 tests:401 / 404 / 409 / 502 / 503 / **504 E5 LLM timeout** / unhandled exception redacts internals(no "RuntimeError" / no "secret_password" in response)/ **422 E6 query too long** / 422 generic invalid payload / actionable_hint present;UI snapshot tests deferred(no Vitest/Playwright harness — see F5.5)
- [ ] ~~F4.5 LIVE smoke~~ → **DEFERRED post-W7 D4-D5 dev server availability** — Chris dev server availability per W6 C3 carry-over;若 W7 D5 dev server 可用 trigger E1+E5+E12,否則 W8 D1+D4 cascade post-IT engagement(non-W7-blocking — F4.1-F4.4 unit-test verified)

## F5 — Mobile responsive baseline complete(C09 + C10)

- [x] F5.1 Tailwind responsive breakpoints audit — **W7 D4 done 2026-05-15** — `docs/02-architecture/responsive-audit-W7.md` NEW(8 sections):breakpoints sm/md/lg/xl reference;per-view audit(KB list 🟡 / KB detail 🟡 / Eval Console ⏳ skeleton / Chat ⏳ C10 not started);F5.2 hamburger implementation note;F5.3 deferred reason;F5.4 viewport plan;F5.5 deferred reason
- [x] F5.2 Mobile-only adjustments — **W7 D4 done 2026-05-15** — `frontend/components/nav/admin-shell.tsx` NEW client component:sidebar `< md` off-canvas drawer with hamburger button + dimmed overlay + auto-close on nav tap;`>= md` static W2 D5 desktop layout preserved;touch targets `min-h-[40px]`;`aria-expanded` / `aria-label` accessibility
- [ ] ~~F5.3 Citation card mobile UX~~ → **DEFERRED W7+ until C10 Chat UI built** — C10 status `⏳ Not started` per session-start §3;rolling-JIT trigger when C10 lands(citation card MUST be `< md` full-width + screenshot modal `max-h-[80vh] w-full`,`>= md` 320px right rail per architecture.md §5.4 Chat layout;rationale documented in responsive-audit-W7.md §4)
- [ ] F5.4 Manual smoke test 5 viewports — W7 D5 trigger
- [ ] ~~F5.5 Pixel diff snapshots~~ → **DEFERRED W8** — no Vitest/Playwright snapshot harness installed(W7 D2 frontend audit confirmed `package.json` scripts only `lint`/`type-check`/`dev`/`build`/`start`);adding = scope creep;W6 C10 calibration applied(static work 0.5x not in budget);rationale documented in responsive-audit-W7.md §6

## F6 — Phase Gate closeout + W7 retro + W8 kickoff prep

- [ ] F6.1 W7 phase Gate verdict landed(F1-F5 outcomes documented + carry-overs to W8 — **F1.1 + F1.7 W8 carry-over per a-revised mock auth strategy**)
- [ ] F6.2 W07 progress.md retro 7 sections complete(per W6 retro structure precedent)
- [ ] F6.3 W08 phase folder kickoff:`docs/01-planning/W08-beta-deploy-sprint2/{plan,checklist,progress}.md` draft(scope = Azure Container Apps + Static Web Apps deploy + cost monitoring + user feedback dashboard + **W8 D1 Q11 IT engagement** + **W8 D4 F1.7 LIVE smoke real Entra ID switch**)
- [ ] F6.4 W07 progress.md frontmatter status flipped to `closed`
- [ ] ~~F6.5 OQ Q11 final Resolved sync to `decision-form.md`~~ → **already met W6 D5**(decision-level Resolved 2026-05-05);W6 D5 stakeholder approval cycle landed
- [ ] F6.5-revised OQ Q11 IT operational cascade trigger documented in W7 retro carry-over to W8(Chris IT engagement W8 D1 timeline)
- [ ] F6.6 R-B1 risk status update to `RISK_REGISTER.md`(Entra ID delay → mitigated W7 全程 mock-auth-decoupled vs W8 D1 IT engagement trigger active 監察)

---

## Cross-Cutting

- [ ] Each commit references `progress.md` Day-N entry(R2)
- [ ] Component tag in commit message per CC-1
- [ ] OQ status sync to `decision-form.md`(R4)— Q11 W7 D1 critical
- [ ] Risk register update if R-B1 (Entra ID delay) status changes
- [ ] CLAUDE.md §5.5 H5 security check:no secret commit;Cohere/Azure key in `.env` gitignored;Entra ID client secret only in `.env`(POC)→ Key Vault W8+

---

**Lifecycle reminder**:呢份 checklist 衍生自 `plan.md` deliverables。新加 deliverable 必須先入 plan + changelog,然後再加 checklist item。
