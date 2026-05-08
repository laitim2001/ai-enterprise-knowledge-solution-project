---
phase: W13-user-facing-views
plan_ref: ./plan.md
status: draft
last_updated: 2026-06-10
---

# Phase W13 — Checklist

> Atomic checkbox(每 item ≤ 0.5–2 hour effort per W6 C10 calibration)。
> Status:`draft` 自 2026-06-10 W12 D5 closeout cascade rolling-JIT。
> 全 unchecked 至 W13 D1 implementation start post stakeholder authorization。

## F1 — Routing restructure + theme provider integration

- [ ] F1.1 Chat path move:`frontend/app/page.tsx` → `frontend/app/chat/page.tsx`(preserve W12 F4.4 tokens migration content;Next.js App Router convention)
- [ ] F1.2 `frontend/app/page.tsx` placeholder for V7 Landing(F1 only ensures path slot ready;F2 fills content)
- [ ] F1.3 Theme provider integration:wire `<ThemeProvider attribute="class">` from `next-themes`(W12 D3 auto-installed via shadcn sonner)into `frontend/app/layout.tsx` root + suppress hydration warning per next-themes convention
- [ ] F1.4 Dark mode toggle UI:add toggle Button(Sun / Moon lucide icons + DropdownMenu)to admin-shell header(desktop)+ mobile header
- [ ] F1.5 Public-vs-protected route convention:Landing / Login / Register routes 唔 require auth(public exclude `_PROTECTED_PREFIXES`);Chat / Admin / Eval / Debug routes require auth(protected per existing W7 D1 baseline)
- [ ] F1.6 Functional smoke:`/chat` renders W12 F4.4 chat content;`/` returns Landing(empty stub if F2 not yet land);dark mode toggle persists via localStorage

## F2 — V7 Landing page implementation

- [ ] F2.1 `frontend/app/page.tsx` rebuild per V7 wireframe(per ui-design-reference-v6.md §2.7):Header + Hero + 3 Feature cards + How-it-works 3-step + Footer
- [ ] F2.2 Header component:logo + nav links(Features / Pricing(disabled — post-launch)/ Sign in / Get started CTA)
- [ ] F2.3 Hero section:tagline + 1-line subheading + primary CTA Button「Start asking →」 → `/login` + secondary Watch demo Button(disabled placeholder)
- [ ] F2.4 Feature highlights — 3 shadcn Card(Multi-format ingestion / Hybrid retrieval + CRAG / Citation-grounded answers)
- [ ] F2.5 How-it-works 3-step indicator(reuse W12 F4.9 Stepper pattern;Upload → Ask → Verify icons)
- [ ] F2.6 Footer stubs:status link / docs / contact / legal(Tier 1 acceptable placeholders)
- [ ] F2.7 Content discipline check per architecture.md v6 §5.9 + H4:no Tier 2 / future feature claims;all features ground 在已實 Tier 1 capability
- [ ] F2.8 Responsive verify:mobile collapse Hero CTA + stack feature cards vertical via Tailwind responsive classes

## F3 — V8 Login page implementation

- [ ] F3.1 `frontend/app/login/page.tsx` create per V8 split layout(per ui-design-reference-v6.md §2.8)
- [ ] F3.2 Brand panel(left):logo + tagline「EKP — Knowledge, on demand.」+ minimal pattern background(CSS gradient OR repeating SVG pattern)
- [ ] F3.3 Form area(right):Email input(shadcn Input + Label)+ Password input(shadcn Input type=password)+ 「Sign in」Button(default variant)
- [ ] F3.4 Auth path separator:shadcn Separator w/ text overlay「or」+ 「Sign in with Microsoft」Button(outline variant + Building lucide icon OR Microsoft SVG)→ MSAL redirect(existing useAuthStore provider)
- [ ] F3.5 Footer links:「Forgot password?」disabled w/ tooltip per Tier 2 defer(ADR-0014 Consequences Neutral)+ 「Don't have an account? Register」link → `/register`
- [ ] F3.6 Auth flow wire:internal Entra ID SSO uses existing useAuthStore;external self-register POST `/auth/login`(F5 endpoint)on form submit
- [ ] F3.7 Error states:`error.code` from backend ApiError envelope → toast variants(invalid_cred / unverified_email / locked_account)per shadcn Sonner
- [ ] F3.8 Loading state:button disabled + spinner icon during auth in-flight(`Loader2` lucide animate-spin)

## F4 — V9 Register 3-step wizard implementation

- [ ] F4.1 `frontend/app/register/page.tsx` create per V9 wireframe(per ui-design-reference-v6.md §2.9)— reuse V8 brand panel split layout
- [ ] F4.2 Step indicator(reuse W12 F4.9 Stepper pattern;3 steps:Account info → Email verify → Welcome)
- [ ] F4.3 Step 1 Account info:Email + Password + Confirm password + Display name(shadcn Input + Label + form validation;client-side strength preview rules)
- [ ] F4.4 Step 2 Email verify:「Check your inbox at <email>」+ 6-digit code input(6 separate Input boxes w/ Tab navigation OR single Input auto-format)+ 「Resend(60s rate limit)」Button(disabled w/ countdown timer)
- [ ] F4.5 Step 3 Welcome:「Account created」+ optional first KB selection(disabled — Tier 1 single-KB POC per Q7 default)+ Tour CTA Button「Start asking」 → `/chat`
- [ ] F4.6 Backend integration:Step 1 submit → POST `/auth/register`(F5);Step 2 submit → POST `/auth/verify-email`(F5);Step 3 «Start asking» → router.push `/chat`
- [ ] F4.7 Error states:registration failures(email_already_exists / invalid_password / verification_token_expired)→ toast + step rollback if needed
- [ ] F4.8 Resend rate limit countdown:60s timer state + Button disabled while counting + clearTimeout on unmount

## F5 — Backend hybrid auth cascade

- [ ] F5.1 `users` table schema decision:initial in-memory dict mock per W1 KB Manager pattern OR SQLite Tier 1 + TODO Beta hardening Postgres / Cosmos DB(W11 retro CO18 carry-over)
- [ ] F5.2 User Pydantic models:`UserRegister` + `UserLogin` + `UserVerifyEmail` + `User`(public model excludes password_hash)
- [ ] F5.3 `POST /auth/register` endpoint:validate email + password strength + check duplicate + Argon2id hash(`argon2-cffi` utility-lib H2 example)+ verification_token sign(`secrets.token_urlsafe(32)` 24h expiry)+ store user(verified=False)+ trigger F6 send + return success
- [ ] F5.4 `POST /auth/verify-email` endpoint:validate token(non-expired + matches user)+ update user verified=True + clear token + return success
- [ ] F5.5 `POST /auth/login` endpoint:lookup by email + verify Argon2id match + check verified=True + generate session token(7-day expiry)+ store session httpOnly cookie + return user + token
- [ ] F5.6 Session middleware:wire bearer token validation for protected routes(`_PROTECTED_PREFIXES` 已 W7 D1 baseline);self-register users return same `User` shape as MSAL user
- [ ] F5.7 Tests:pytest unit + integration test for each endpoint;coverage ≥ 80% per CLAUDE.md §3.6 H6
- [ ] F5.8 Karpathy §1.3 surgical:non architectural change(ADR-0014 已 covered scope per H1);Argon2id password hashing default per industry standard(non new vendor decision)

## F6 — C13 ACS Email Verification Service integration

- [ ] F6.1 `backend/api/auth/email_provider.py` create:ACS Email Client wrapper(`azure-communication-email` SDK installed + utility-lib per CLAUDE.md §5.2 H2)
- [ ] F6.2 Email template:plain text + HTML alternative(simple template embedded;non template engine Tier 1 per ADR-0014)
- [ ] F6.3 Sender domain config via env var:Tier 1 dev `noreply@dev.ekp-beta.ricoh.com`(SPF/DKIM 自 IT setup post Track A);Beta phase real `noreply@ekp-beta.ricoh.com` env switch
- [ ] F6.4 Failure mode handling:ACS API 5xx → `tenacity` retry(已 utility-lib per CLAUDE.md §3.1);fail-soft graceful(register flow surface「verification email pending — please check inbox or resend」per V9 Step 2)
- [ ] F6.5 Mock mode for dev:env var `FEATURE_EMAIL_MOCK=true` → log verification token to backend logs instead of sending(parallel to W7 D1 F1.2.1 mock auth pattern;dev workstation R8 + pre-IT-cred)
- [ ] F6.6 Tests:pytest unit test mock send + verify token flow;real ACS smoke deferred Beta phase post sender domain SPF/DKIM ready

## F7 — Phase Gate closeout + W14 phase folder kickoff

- [ ] F7.1 W13 phase Gate verdict landed(PASS / PARTIAL PASS / FAIL with explicit rationale per W12 F5.1 pattern)
- [ ] F7.2 W13 progress.md retro 7 sections complete(What worked / What didn't / Surprises / Decisions / Carry-overs / Time tracking / Spec ref alignment)
- [ ] F7.3 `docs/01-planning/W14-admin-views/{plan,checklist,progress}.md` draft per architecture.md v6 §5.3-§5.5 V2/V3/V4 + design ref doc §6 W14 scope
- [ ] F7.4 W13 progress.md frontmatter status flipped to `closed`
- [ ] F7.5 No new OQ surface expected;if surface(F5 users table backing OR F6 ACS unexpected)→ sync to decision-form.md per R4

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
