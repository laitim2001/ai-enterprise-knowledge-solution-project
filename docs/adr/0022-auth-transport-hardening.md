# ADR-0022: Auth-transport hardening — httpOnly cookie + CSRF double-submit + /auth/refresh rotation

**Date**: 2026-05-10
**Status**: Accepted
**Approver**: Chris (Tech Lead / architecture decision owner — AskUserQuestion 2026-05-10 selected "W17 做 — 寫 ADR + 實作")

## Context

The W13 self-register hybrid-auth cascade (per ADR-0014) issues a session token from `POST /auth/login` and the frontend currently stores it in `localStorage` under `ekp_session_token` (`frontend/lib/auth/index.ts`), reading it back via `getBearer()` for protected API calls. This was a deliberate W13 D5 minimal landing — the W14 D1 F1.5 / W15 D2 carry-overs `CO_F5_refresh` (no `/auth/refresh` self-register session rotation) and `CO_F5_cookie` (httpOnly cookie hardening) explicitly deferred the hardening to "Beta hardening".

`localStorage`-resident bearer tokens are readable by any script on the origin → XSS-token-theft surface. For an internal Beta-cohort tool this is acceptable-but-not-ideal; the audit (`audit-W15-d5-vs-spec.md` §7) pre-reserved an ADR slot for the cookie migration. W17-beta-hardening is the phase that closes it.

Two constraints shape the decision:
1. **The SSO/MSAL path is separate.** `mock_msal.ts` (dev) / `msal_provider.ts` (Beta+ per Q11) acquire tokens for the Microsoft-identity branch; that branch's token handling is not changed here — this ADR is the *self-register* branch's transport.
2. **API clients + `FEATURE_AUTH_MOCK=true` must keep working.** `get_current_user` is wired router-level across all protected routers (`server.py` `_auth = [Depends(get_current_user)]`); the mock-auth dev path injects `Authorization: Bearer dev-token`; CLI/curl/test clients use Bearer. A cookie-only switch would break all of those.

## Decision

**Adopt httpOnly cookie as the primary transport for the self-register session token, with a CSRF double-submit token, and keep `Authorization: Bearer` as a parallel accepted credential.** Add `POST /auth/refresh` session rotation.

Concretely:

1. **Set-Cookie on auth success.** `POST /auth/login` and the email-verify step of `POST /auth/register` set:
   - `ekp_session` — the session token. `HttpOnly`; `Path=/`; `SameSite=Lax` (SSO-redirect-friendly); `Secure` **only when `settings.environment != "local"`** (so local HTTP dev works); `Max-Age` = session TTL.
   - `ekp_csrf` — a random double-submit token. **Not** `HttpOnly` (the SPA must read it to echo it back); same `SameSite`/`Secure`/`Path`.
2. **`POST /auth/refresh`** — requires a valid existing `ekp_session`; rotates both cookies; `401` if absent/invalid (no unauthenticated session bootstrap — matches the existing `/auth/refresh` + `/auth/logout` in-route `Depends(get_current_user)` posture in `server.py`). Closes `CO_F5_refresh`.
3. **`POST /auth/logout`** — clears both cookies.
4. **`get_current_user` dual-path** (`backend/api/auth/dependency.py`): read `ekp_session` cookie if present; else fall back to `Authorization: Bearer` (mock-auth + API clients). When the request is **cookie-authenticated AND state-changing** (POST/PUT/PATCH/DELETE), require `X-CSRF-Token` header == `ekp_csrf` cookie, else `403`. Bearer-authenticated requests are exempt from the CSRF check (Bearer is not auto-sent by browsers — no CSRF vector).
5. **Frontend** (`frontend/lib/api-client.ts`): `credentials: 'include'` on all requests; on non-GET, read the `ekp_csrf` cookie and send `X-CSRF-Token`. `frontend/lib/auth/index.ts` `getBearer()` is simplified — the cookie is the primary credential transport; the `localStorage` `ekp_session_token` is retained **only** behind `NEXT_PUBLIC_AUTH_MOCK` for the mock-auth dev path. `app/login/page.tsx` / `app/register/page.tsx` stop treating `localStorage` as ground truth (the cookie is set by the response).

This **amends the transport layer of ADR-0014, not the hybrid-auth model** — SSO + self-register, scrypt password hash (ADR-0016), email verification (C13 / ADR-0014) are all unchanged.

## Alternatives Considered

- **Keep `localStorage` bearer (status quo)** — rejected: XSS-token-theft surface; the audit pre-reserved this ADR; user explicitly chose "W17 做".
- **`sessionStorage` instead of `localStorage`** — rejected: marginal improvement (still script-readable), no CSRF benefit, doesn't survive tab refresh-on-new-tab; not worth a half-measure.
- **Cookie-only (drop Bearer entirely)** — rejected: breaks `FEATURE_AUTH_MOCK=true` dev path, the Playwright webServer (injects `Bearer dev-token`), curl/CI clients, and the SSO branch's token model. The dual-path keeps all of those working at the cost of a small `dependency.py` branch.
- **Signed/encrypted cookie (e.g. `itsdangerous` / JWT-in-cookie)** — deferred Tier 2: the current session token already comes from `POST /auth/login` via the `users_repo`-validated flow; wrapping it in a signed envelope is an orthogonal hardening that can layer on later. No new dependency now.
- **SameSite=Strict** — rejected: breaks the SSO redirect round-trip (cross-site navigation from `login.microsoftonline.com` back to `ekp-beta.ricoh.com` would drop the cookie). `Lax` is the standard choice for auth cookies that must survive top-level redirects.

## Consequences

- **Positive**: session token no longer script-readable (httpOnly); CSRF double-submit closes the cookie-auth CSRF vector; `/auth/refresh` rotation closes `CO_F5_refresh`; production-shaped auth transport before Beta cutover; dual-path means zero disruption to mock-auth / API-client / SSO flows; no new dependency (uses FastAPI/Starlette cookie + header primitives only — H2 not triggered, this is an H1-only ADR).
- **Negative**: `dependency.py` `get_current_user` gains a cookie-vs-Bearer branch + a CSRF check branch (small, well-tested); frontend `api-client` must read a cookie and set a header on non-GET (small); the `localStorage` fallback path being mock-only is a slight asymmetry that must be clearly commented; existing `test_auth_*` tests need transport-layer updates.
- **Neutral**: `Secure` is env-gated, so local HTTP dev is unaffected; the SSO/MSAL branch's token model is untouched (this ADR is the self-register branch only); forgot-password / 2FA / OAuth-providers remain Tier 2 (architecture.md v6 §11).

## Implementation Deliverables

Tracked in `docs/01-planning/W17-beta-hardening/{plan,checklist}.md` **F2** (+ **F0.1** for this ADR). Status appended at W17 closeout.

- [x] F0.1 — this ADR landed `Accepted`; README index updated (`6edd9ef`)
- [x] F2.1 — `Set-Cookie` `ekp_session` (httpOnly, SameSite=Lax, Secure=env!=local, Max-Age=session TTL) + `ekp_csrf` (double-submit, readable) on `POST /auth/login` + the verified-transition of `POST /auth/verify-email` — via `api/auth/cookies.set_session_cookies`
- [x] F2.2 — `POST /auth/refresh` rotates the session token + both cookies (revokes the old token); 401 via the `Depends(get_current_user)` gate if no valid session; mock dev mode keeps returning the fixed dev-token (no cookie). Closes CO_F5_refresh
- [x] F2.3 — `POST /auth/logout` revokes the session (cookie token + any bearer) + clears both cookies
- [x] F2.4 — `get_current_user` dual-path (cookie precedence → bearer session → mock → MSAL) + CSRF double-submit (`X-CSRF-Token` == `ekp_csrf` cookie) enforced on cookie-authenticated state-changing requests (POST/PUT/PATCH/DELETE); GET + Bearer-authenticated requests are CSRF-exempt
- [x] F2.5 — frontend `api-client.ts` `credentials:'include'` on all requests + `X-CSRF-Token` (from the `ekp_csrf` cookie) on non-GET; `getCsrfHeaders()` exported for the raw-fetch callers (`lib/api/query.ts` SSE stream, `lib/api/kb.ts` upload); `auth/index.ts` `getBearer()` simplified — the `SESSION_TOKEN_STORAGE_KEY` / `readSessionBearer` localStorage path removed (the cookie is the credential; mock dev-token + MSAL JWT are the only Bearers)
- [x] F2.6 — `login/page.tsx` drops the `localStorage.setItem(SESSION_TOKEN_STORAGE_KEY, …)` write + the now-unused import (cookie is set by the response). `register/page.tsx` needed no change — it never wrote localStorage, and the verify-email auto-login cookie makes its Step-3 → `/chat` work
- [x] F2.7 — `backend/tests/test_auth_cookie_transport.py` (17 cases: Set-Cookie shape / cookie GET / CSRF reject + accept + mismatch / Bearer + mock CSRF-exempt / invalid-cookie fallthrough / refresh rotation + 401 + mock / logout clear); `test_auth_self_register.py::test_logout_revokes_session_token` + `test_mock_msal.py` dependency tests updated for the new `get_current_user(request, …)` signature; backend pytest 609 passed / 11 skipped; `tsc --noEmit` + `next lint` clean
- [x] F2.8 — `architecture.md` §3.7「Auth transport」note (per this ADR); ADR-0014 References cross-link to ADR-0022 (+ ADR-0016, ADR-0023); `server.py` CORS gained `allow_credentials=True` (cookie transport correctness); CO_F5_refresh + CO_F5_cookie → CLOSED (W17 checklist/progress)

## References

- ADR-0014 — Hybrid auth model (SSO + self-register) — this ADR amends its transport layer
- ADR-0016 — scrypt password hash (auth security baseline, unchanged)
- `architecture.md` v6 §3.7 — C13 Email Verification Service / hybrid auth
- `docs/02-architecture/audit-W15-d5-vs-spec.md` §7 — pre-reserved ADR slot "0022 cookie migration W17+"
- `docs/01-planning/W17-beta-hardening/plan.md` §2 F2
- W14 D1 F1.5 / W15 D2 carry-overs `CO_F5_refresh` + `CO_F5_cookie`
- `frontend/lib/auth/index.ts`, `frontend/lib/api-client.ts`, `backend/api/auth/dependency.py`, `backend/api/routes/auth.py`
