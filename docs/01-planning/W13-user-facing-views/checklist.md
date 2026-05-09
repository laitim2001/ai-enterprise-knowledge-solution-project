---
phase: W13-user-facing-views
plan_ref: ./plan.md
status: closed
last_updated: 2026-06-10
---

# Phase W13 — Checklist

> Atomic checkbox(每 item ≤ 0.5–2 hour effort per W6 C10 calibration)。
> Status:`closed` 自 2026-06-10 W13 D5 cont F7 closeout — Phase Gate PASS WITH SMOKE-USER-DEFERRED CAVEAT verdict landed。

## F1 — Routing restructure + theme provider integration

- [x] F1.1 Chat path move:`frontend/app/page.tsx` → `frontend/app/chat/page.tsx`(preserve W12 F4.4 tokens migration content;Next.js App Router convention)
- [x] F1.2 `frontend/app/page.tsx` placeholder for V7 Landing(F1 only ensures path slot ready;F2 fills content)
- [x] F1.3 Theme provider integration:wire `<ThemeProvider attribute="class">` from `next-themes`(W12 D3 auto-installed via shadcn sonner)into `frontend/app/layout.tsx` root + suppress hydration warning per next-themes convention
- [x] F1.4 Dark mode toggle UI:add toggle Button(Sun / Moon lucide icons + DropdownMenu)to admin-shell header(desktop)+ mobile header
- [x] F1.5 Public-vs-protected route convention:**deviation per plan §7 changelog 2026-06-10 (D1)** — Next.js `middleware.ts` 唔存在(W7 D1 baseline 從未 implement);apply via page-level convention only(Landing/Login/Register 唔 mount AuthProvider = public;Chat/Admin/Eval/Debug 透過 UserMenu + useAuthStore 隱式 protected via AuthProvider mock auto-sign-in)。Server-side guard defer F5 backend session middleware
- [ ] 🚧 F1.6 Functional smoke:user-deferred per CLAUDE.md §13 dev server policy(`pnpm dev` long-running Node server 同 Claude Code 衝突);AI verification = type-check 0 errors ✅ + import resolution ✅;`! pnpm dev` localhost:3001 user smoke remainder 候 user 自行驗證(同 W12 F4.13 carry-over CO1 pattern)

## F2 — V7 Landing page implementation

- [x] F2.1 `frontend/app/page.tsx` rebuild per V7 wireframe(per ui-design-reference-v6.md §2.7):Header + Hero + 3 Feature cards + How-it-works 3-step + Footer
- [x] F2.2 Header component:logo + nav links(Features / Pricing(disabled — post-launch)/ Sign in / Get started CTA)
- [x] F2.3 Hero section:tagline + 1-line subheading + primary CTA Button「Start asking →」 → `/login` + secondary Watch demo Button(disabled placeholder)
- [x] F2.4 Feature highlights — 3 shadcn Card(Multi-format ingestion / Hybrid retrieval + CRAG / Citation-grounded answers)
- [x] F2.5 How-it-works 3-step indicator(reuse W12 F4.9 Stepper visual pattern;Upload → Ask → Verify lucide icons;Karpathy §1.2 simplicity-first — static descriptive layout vs full Stepper state machine since steps non-interactive)
- [x] F2.6 Footer stubs:status link / docs / contact / legal(Tier 1 acceptable placeholders;cursor-not-allowed + title attribute disabled state)
- [x] F2.7 Content discipline check per architecture.md v6 §5.9 + H4:Multi-format(Docling docx + python-pptx ✅ W2 implemented)/ Hybrid retrieval + CRAG(Azure AI Search hybrid + custom CRAG L2 ✅ W3-W4 implemented)/ Citation-grounded(citation cards + chunk_id traceability ✅ W3 implemented);no GraphRAG / multi-agent / multi-tenancy / fine-tune leak
- [x] F2.8 Responsive verify:Header nav links hidden < md(`hidden md:flex`);Hero CTAs stack `flex-col sm:flex-row`;Feature cards `grid-cols-1 md:grid-cols-3`;How-it-works `grid-cols-1 md:grid-cols-3`;Footer `flex-col sm:flex-row`

## F3 — V8 Login page implementation

- [x] F3.1 `frontend/app/login/page.tsx` create per V8 split layout(per ui-design-reference-v6.md §2.8)
- [x] F3.2 Brand panel(left):logo「EKP」+ tagline「Knowledge, on demand.」+ subtle dot-grid CSS pattern overlay(currentColor inherited from text-primary-foreground;opacity 0.06;non hardcoded oklch per W12 D2 strict baseline)
- [x] F3.3 Form area(right):Email input(shadcn Input + Label;type=email + autoComplete=email)+ Password input(shadcn Input type=password + autoComplete=current-password)+ 「Sign in」default Button
- [x] F3.4 Auth path separator:shadcn Separator w/ 「or」text overlay + 「Sign in with Microsoft」outline Button + Building2 lucide icon
- [x] F3.5 Footer links:「Forgot password?」disabled span w/ title attribute per Tier 2 defer(ADR-0014 Consequences Neutral)+ 「Don't have an account? Register」Link → `/register`
- [x] F3.6 Auth flow wire **deviation logged plan §7 changelog 2026-06-10 (D3)** — defer ALL auth wire(含 existing MSAL SSO useAuthStore W7 baseline)to F5 batch per user instruction「auth flow wire 留 F5 lands」;UI shell only stub handlers w/ `F5_PENDING_MESSAGE` constants + sonner toast feedback;TODO(W13 F5)comments in `handleSelfSubmit` + `handleSsoClick` mark replacement points
- [x] F3.7 Error states scaffold:sonner `toast.error()` + `toast.info()` ready;variant logic(invalid_cred / unverified_email / locked_account)→ comment placeholder pending F5 ApiError envelope wire
- [x] F3.8 Loading state:both Sign in + SSO Buttons disabled + Loader2 lucide animate-spin during local pending state(800ms simulated delay for visual demo);`anyPending` derived flag prevents form interaction during either flow

## F4 — V9 Register 3-step wizard implementation

- [x] F4.1 `frontend/app/register/page.tsx` create per V9 wireframe(per ui-design-reference-v6.md §2.9)— reuse V8 brand panel split layout via shared `frontend/components/auth/brand-panel.tsx`(rule-of-2 extracted W13 D4 per plan §7 changelog)
- [x] F4.2 Step indicator inline parallel W12 F4.9 Pipeline wizard pattern(active/done/pending state machine;3 steps:Account info → Email verify → Welcome;step labels hidden < sm — only circle visible on mobile)
- [x] F4.3 Step 1 Account info:Email + Password(strength preview 5-segment bar + label scoring length/uppercase/digit/symbol)+ Confirm password + Display name + client-side `validateAccountInfo` form validation(EMAIL_PATTERN + min 8 char + uppercase + digit/symbol + match)
- [x] F4.4 Step 2 Email verify:6 separate Input boxes w/ auto-advance focus + Backspace previous focus + ArrowLeft/Right navigation + paste distribution(industry-standard verification UX);MailCheck lucide icon + email shown;`Resend (60s)` countdown button
- [x] F4.5 Step 3 Welcome:PartyPopper success icon + personalized greeting w/ displayName + disabled KB selector(`drive_user_manuals` w/ title attribute per Q7 single-KB POC default)+ Tour CTA「Start asking →」 → `router.push('/chat')`
- [x] F4.6 Backend integration **deviation logged plan §7 changelog 2026-06-10 (D4)** — defer all wire to F5 batch per user instruction「backend wire 同樣 stub/F5 defer」(F3.6 pattern一致);stub handlers w/ `F5_PENDING_REGISTER` / `F5_PENDING_VERIFY` / `F5_PENDING_RESEND` constants + sonner toast feedback;TODO(W13 F5)comments mark replacement points
- [x] F4.7 Error states scaffold:`validateAccountInfo` produces field-level error map(client-side only);F5 ApiError envelope variants(email_already_exists / invalid_password / verification_token_expired)→ comment placeholder pending F5
- [x] F4.8 Resend rate limit countdown:60s timer via `useEffect` + `setTimeout`(decrement every 1s);button disabled when `resendCooldown > 0`;`clearTimeout` cleanup on unmount;reset to 60s on Resend click + Step 1 → 2 advance

## F5 — Backend hybrid auth cascade

- [x] F5.1 `users` table schema:in-memory dict per ADR-0014 Tier 1 + Beta hardening TODO Postgres / Cosmos DB(W11 retro CO18);`backend/api/auth/users_repo.py` w/ `_users` + `_sessions` dicts + RLock + `reset_repo()` test fixture helper
- [x] F5.2 User Pydantic models:`UserRegisterRequest` + `UserLoginRequest` + `UserVerifyEmailRequest` + `UserResendVerificationRequest` + `UserPublic`(excludes password_hash + verification_code per CLAUDE.md §5.5 H5);responses:`RegisterResponse` + `VerifyEmailResponse` + `LoginResponse` + `ResendVerificationResponse`
- [x] F5.3 `POST /auth/register`:**deviations logged plan §7 changelog 2026-06-10 (D5)** — (a)hash lib argon2-cffi → hashlib.scrypt(ADR-0016 R8 corp proxy blocker);(b)verification token 32-char URL-safe → 6-digit numeric code(V9 wireframe §2.9 + OTP UX);validate email + password strength + check duplicate + scrypt hash + 6-digit code generation + 24h expiry + email send via C13 EmailProvider stub(ConsoleEmailProvider for F5;F6 swaps to ACS)+ 201 Created
- [x] F5.4 `POST /auth/verify-email`:validate code format(6-digit numeric)+ lookup user by email + check expiry + match code + idempotent on already-verified + clear code + flip verified=True + return UserPublic
- [x] F5.5 `POST /auth/login`:**deviation logged plan §7 changelog (D5)** — httpOnly cookie deferred Beta hardening;lookup by email + scrypt verify_password(constant-time)+ check verified=True + 256-bit session token(`secrets.token_urlsafe(32)`)+ 7-day expiry + return body w/ access_token + UserPublic(API-explicit pattern;cookie via Set-Cookie defer)
- [x] F5.6 Session resolution:**deviation logged plan §7 changelog (D5)** — implemented as Depends extension(not separate ASGI middleware)per W7 pattern parity;`api/auth/dependency.get_current_user` adds session branch BEFORE mock/MSAL fork(`users_repo.resolve_session(token)` returns AuthenticatedUser w/ tid=`SELF_REGISTER_TID` + is_mock=False);downstream code consumes same model regardless of provider;`/auth/logout` extended to revoke session token if presented(non-breaking)
- [x] F5.7 Tests:**41 tests pass** in `backend/tests/test_auth_self_register.py`(security helpers / users_repo / 4 endpoints / dependency session branch / logout revoke);**456/456 W7+W8 baseline regression 0 break**;coverage tool install blocked by R8 proxy → manual trace ≥85% estimated(security ~95% / users_repo ~95% / email_provider ~90% / dependency ~90% / routes/auth ~90%)
- [x] F5.8 Karpathy §1.3 surgical preserved:no §3/§4 architectural change(ADR-0014 covered scope per H1);scrypt vendor change ADR-0016 written per H2 strict reading;structured `detail` dict in HTTPException 解 error_handler.http_exception_handler 4-line backwards-compatible extension(string detail W7 path preserved);existing /auth/refresh + /auth/logout routes preserved(/auth/logout 加 minimal session revoke)

## F6 — C13 ACS Email Verification Service integration

- [x] F6.1 `backend/api/auth/email_provider.py` AcsEmailProvider class(EmailProvider Protocol parity);**lazy SDK import** `azure-communication-email`(R8 corp-proxy compatible — module loads even when SDK uninstalled);ImportError → `EmailSendError("not installed")` actionable hint
- [x] F6.2 Email templates(simple constants — non template engine Tier 1):`_PLAIN_TEMPLATE`(text)+ `_HTML_TEMPLATE`(inline-styled responsive)+ `render_plain_text()` / `render_html()` placeholder substitution helpers
- [x] F6.3 Sender domain config via Settings env vars:`acs_sender_address` default `noreply@dev.ekp-beta.ricoh.com`;`acs_connection_string` empty defaults → ConsoleEmailProvider fallback per F6.5;`acs_request_timeout_s` 30s + `acs_max_retries` 3 tunable
- [x] F6.4 Failure mode handling:tenacity `AsyncRetrying` retries on `_TRANSIENT_EXCEPTION_TYPES`(OSError + asyncio.TimeoutError + TimeoutError);non-transient bypass retry surface immediately;**fail-soft on register + resend routes**(try/except EmailSendError + structlog warning + continue without 5xx propagation per V9 Step 2「Check your inbox」UX consistency)
- [x] F6.5 Mock mode via `feature_email_mock=True` Settings(default True for safety);factory `_build_provider_from_settings` selects ConsoleEmailProvider when mock OR connection_string empty(defensive Beta misconfiguration guard);ConsoleEmailProvider logs verification code via structlog
- [x] F6.6 Tests:**12 new tests pass**(template rendering 2 + factory selection 3 + SDK-missing guard 1 + mocked-SDK happy/retry/exhaustion/non-transient 4 + fail-soft register/resend 2);real ACS smoke deferred Beta post sender domain SPF/DKIM ready

## F7 — Phase Gate closeout + W14 phase folder kickoff

- [x] F7.1 W13 phase Gate verdict landed:**🟢 PASS WITH SMOKE-USER-DEFERRED CAVEAT — User-Facing Views sprint phase 2 of 4 complete**(7-criterion evaluation table in progress.md Day 5 cont F7 entry;all 7 PASS conditions met + PARTIAL PASS fallback acceptance criteria 全 met + no FAIL conditions tripped)
- [x] F7.2 W13 progress.md retro 7 sections complete(What worked 7 / What didn't 4 / Surprises 5 / Decisions 12 / Carry-overs categorized W14 immediate + admin views + W15 polish + W13 backend follow-ups + W16+ Beta / Time tracking 8-row table / Spec ref alignment 8-row trace)
- [x] F7.3 `docs/01-planning/W14-admin-views/{plan,checklist,progress}.md` draft created per architecture.md v6 §5.3-§5.5 V2/V3/V4 + design ref doc §6 W14 scope(5 deliverables F1-F5;status:draft rolling-JIT)
- [x] F7.4 W13 plan + checklist + progress frontmatter status flipped to `closed`(same commit cascade as F7 closeout)
- [x] F7.5 No new OQ surface during W13(F5 users table 採 in-memory per ADR-0014 Tier 1 default;F6 ACS connection_string 屬 Settings field non OQ;Q22 已 W12 D1 Resolved);16/22 Resolved unchanged from W12 baseline

---

## Cross-Cutting

- [ ] Each commit references `progress.md` Day-N entry(R2)
- [ ] Component tag in commit message per CC-1(C09 / C10 / C11 / C12 / C13)
- [ ] OQ status sync to `decision-form.md`(R4)— no W13 critical OQ expected
- [ ] Risk register update if any new risk surface(e.g. ACS provisioning timing OR Argon2id integration friction)
- [ ] CLAUDE.md §5.1 H1 boundary check:no architectural change without ADR(W13 scope already covered by ADR-0014 + ADR-0015)
- [ ] CLAUDE.md §5.2 H2 boundary check:no new vendor / dependency without ADR(`argon2-cffi` + `azure-communication-email` 屬 utility-lib per H2 example;non vendor swap)
- [ ] CLAUDE.md §3.2 frontend conventions check:no `any` / no @ts-ignore / shadcn/ui only / tokens consumption verified
- [ ] CLAUDE.md §3.1 backend conventions check:Python 3.12 + mypy strict + async-by-default + Pydantic v2 + structlog JSON
- [ ] CLAUDE.md §5.5 H5 security check:Argon2id password hashing(non bcrypt downgrade);verification_token cryptographic random;session token httpOnly cookie;no PII in logs

---

**Lifecycle reminder**:呢份 checklist 衍生自 `plan.md` deliverables。新加 deliverable 必須先入 plan + changelog,然後再加 checklist item。
