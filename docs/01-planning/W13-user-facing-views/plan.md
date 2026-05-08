---
phase: W13-user-facing-views
name: "User-Facing Views — Phase 2 of 4 in W12-W15 UI Tier 1 expansion sprint cycle (V1 Chat refactor + V7 Landing + V8 Login + V9 Register + ADR-0014 hybrid auth backend cascade + C13 ACS email service)"
sprint_week: W13
start_date: 2026-06-23             # tentative — assumes W12 closeout 2026-06-10 + W13 kickoff next session
end_date: 2026-06-27               # 5 working days(possibly +1-2 if F5 backend hybrid auth ~2-day ADR-0014 cascade absorbs W13 D6)
status: draft                      # `draft` — pending W13 D1 active flip post stakeholder authorization + W12 closeout PASS WITH CAVEAT verdict landed
spec_refs:
  - architecture.md v6 §5.2           # V1 Chat path move (`/` → `/chat`)
  - architecture.md v6 §5.9           # V7 Landing public marketing-style entry
  - architecture.md v6 §5.10          # V8 Login split layout (Entra ID SSO + self-register hybrid)
  - architecture.md v6 §5.11          # V9 Register 3-step wizard
  - architecture.md v6 §3.7           # C13 Email Verification Service (ACS per Q22)
  - architecture.md v6 §13.12         # v5.1→v6 amendment (UI Tier 1 expansion + hybrid auth)
  - ADR-0014                          # Hybrid auth (SSO + self-service register)
  - ADR-0015                          # UI Tier 1 expansion 9 views
prior_phase: W12-ui-foundation-discovery
related_artifacts:
  - docs/01-planning/W12-ui-foundation-discovery/progress.md     # Retro § Carry-overs CO4-CO9 W13 scope
  - docs/02-architecture/ui-design-reference-v6.md               # §2.1 V1 + §2.7 V7 + §2.8 V8 + §2.9 V9 wireframes + §4 component map
  - docs/decision-form.md                                         # Q22 ACS Resolved (W12 D1)
  - frontend/lib/theming/tokens.ts                                # Visual identity Option C (W12 D2)
  - frontend/components/ui/                                       # 19 shadcn primitives (W12 D3)
  - frontend/components/nav/admin-shell.tsx                       # F4 admin shell rebuild reference (W12 D4)
  - frontend/components/auth/user-menu.tsx                        # F4 user-menu DropdownMenu reference (W12 D4)
---

# Phase W13 — User-Facing Views(Phase 2 of 4 UI sprint cycle W12-W15)

> **Plan version**:1.0(draft 2026-06-10 W12 D5 closeout cascade — rolling JIT per CLAUDE.md §10 R1)
> **Owner**:Chris(Tech Lead + stakeholder)+ AI(implementation)
> **Approved by**:_(pending W13 D1 active flip post stakeholder authorization)_

---

## 1. Scope(rolling-JIT W12 D5 closeout draft per pivot momentum)

W13 = **User-Facing Views sprint** — Phase 2 of 4-sprint UI Tier 1 expansion(W12-W15)。Goals:

- **Routing restructure**:V1 Chat 路徑 `/` → `/chat`(architecture.md v6 §5.2 amendment);`/` 變成 V7 Landing public entry
- **3 new public-facing views**:V7 Landing(marketing-style entry)+ V8 Login(SSO + self-register hybrid)+ V9 Register(3-step wizard with email verify)
- **Backend hybrid auth cascade** per ADR-0014:`/auth/register` + `/auth/verify-email` + `/auth/login` endpoints + `users` table + Argon2id password hashing + session token storage
- **C13 ACS email service integration** per Q22 + architecture.md v6 §3.7:`backend/api/auth/email_provider.py` ACS Email Client + verification token sign + email template

**Out of W13 scope**(absorbed by W14-W15):
- V2 Admin Dashboard polish + V3 KB List card grid refactor + V4 KB Detail 5-tab(W14)
- V5 Eval Console + V6 Debug View(W14-W15)
- Responsive + a11y + Playwright E2E + pixel diff baseline(W15 polish)
- Forgot password / 2FA / OAuth providers(Tier 2 per architecture.md v6 §11)

**Pre-condition for W13 promotion**(等 W13 D1 active flip):
- W12 D5 closeout PASS WITH F4.13 USER-DEFERRED CAVEAT landed(commit pending Phase Gate verdict + retro complete + frontmatter close cascade)
- ADR-0014 + ADR-0015 status `Accepted`(landed W11 D2 cont commit `44a52cb`)
- architecture.md v6 amendment landed(commit `49a634b`)+ §3.7 C13 component card(commit `00a1dba`)
- Visual identity Option C ratified(commit `1ac17e6`)+ 19 shadcn primitives + 6 token补齊(commit `1b5cb1e`)+ admin shell rebuild + 8 pages tokens migration(commit `fd85741`)

## 2. Deliverables(F1-F7)

### F1 — Routing restructure + theme provider integration

- **Component(s)**:**C09** admin views + **C10** chat UI + **C11** identity + governance(routing convention)
- **Spec ref**:architecture.md v6 §5.2 V1 Chat path move + ADR-0014 hybrid auth path conventions
- **OQ deps**:none
- **Acceptance criteria**:
  - F1.1 Chat path move:`frontend/app/page.tsx` → `frontend/app/chat/page.tsx`(preserve W12 F4.4 tokens migration content;move within `app/` structure per Next.js App Router convention)
  - F1.2 `frontend/app/page.tsx` 變成 V7 Landing(per F2 deliverable;F1 only ensures path slot ready)
  - F1.3 Theme provider integration:wire `<ThemeProvider attribute="class">` from `next-themes`(已 W12 D3 auto-installed via shadcn sonner)into `frontend/app/layout.tsx` root
  - F1.4 Dark mode toggle UI:add toggle button(Sun / Moon lucide icons + DropdownMenu)to admin-shell header(desktop)+ mobile header
  - F1.5 Public-vs-protected route convention:Landing / Login / Register routes 唔 require auth(public);Chat / Admin / Eval / Debug routes require auth(protected per `_PROTECTED_PREFIXES` middleware)
  - F1.6 Functional smoke:`/chat` renders W12 F4.4 chat content;`/` returns W13 F2 Landing(empty stub if F2 not yet land);dark mode toggle persists via localStorage
- **Effort estimate**:0.5 day(W13 D1)
- **Owner**:AI(implementation)+ user(browser smoke verify)

### F2 — V7 Landing page implementation

- **Component(s)**:**C10** chat UI(home entry;non Admin scope)
- **Spec ref**:architecture.md v6 §5.9 + ui-design-reference-v6.md §2.7 V7 wireframe
- **OQ deps**:F1 routing slot ready
- **Acceptance criteria**:
  - F2.1 `frontend/app/page.tsx`(was Chat,now Landing)rebuild per V7 wireframe:Header + Hero + 3 Feature highlight cards + How-it-works 3-step indicator + Footer
  - F2.2 Header:logo + nav links(Features / Pricing(disabled — post-launch)/ Sign in / Get started CTA)
  - F2.3 Hero:tagline「Enterprise Knowledge Platform」+ 1-line subheading「Get answers from your documents — with citations」+ CTA Button「Start asking →」 → `/login` + Watch demo(disabled — placeholder)
  - F2.4 Feature highlights(3 shadcn Card):Multi-format ingestion / Hybrid retrieval + CRAG / Citation-grounded answers
  - F2.5 How-it-works:3-step indicator(reuse W12 F4.9 Stepper pattern;Upload → Ask → Verify)
  - F2.6 Footer:status link / docs / contact / legal(stubs OK Tier 1)
  - F2.7 Content discipline per architecture.md v6 §5.9:no Tier 2 / future feature claims;all features ground 在已實 Tier 1 capability per H4
  - F2.8 Responsive:mobile collapse Hero CTA + stack feature cards vertical
- **Effort estimate**:1 day(W13 D1-D2)
- **Owner**:AI(implementation)+ user(content review + browser smoke)

### F3 — V8 Login page implementation

- **Component(s)**:**C10** chat UI + **C11** identity
- **Spec ref**:architecture.md v6 §5.10 + ADR-0014 + ui-design-reference-v6.md §2.8 V8 wireframe
- **OQ deps**:F1 routing + F5 backend `/auth/login` endpoint(parallel work)
- **Acceptance criteria**:
  - F3.1 `frontend/app/login/page.tsx` create per V8 split layout wireframe
  - F3.2 Brand panel(left):logo + tagline「EKP — Knowledge, on demand.」+ minimal pattern background(CSS-only)
  - F3.3 Form area(right):
    - Email input(shadcn `Input` + `Label`)
    - Password input(shadcn `Input` type=password + `Label`)
    - 「Sign in」Button(default variant)→ POST `/auth/login`(self-register path)
    - Separator「or」(shadcn `Separator` w/ text overlay)
    - 「Sign in with Microsoft」Button(outline variant + Microsoft icon — lucide `Building` placeholder OR custom SVG)→ MSAL redirect(Entra ID SSO path)
    - 「Forgot password?」link disabled(Tier 2 defer per ADR-0014 Consequences Neutral)
    - 「Don't have an account? Register」link → `/register`
  - F3.4 Auth flow wire:internal Entra ID SSO uses existing `useAuthStore` MSAL provider;external self-register POST `/auth/login` consumes new endpoint(F5)
  - F3.5 Error states:`error.code` from backend ApiError envelope → toast variants(invalid_cred / unverified_email / locked_account)per shadcn Sonner
  - F3.6 Loading state:button disabled + spinner icon during auth in-flight
- **Effort estimate**:1 day(W13 D2-D3)
- **Owner**:AI(implementation)+ user(SSO smoke verify post Track A IT cred — note Track A IT cred event 仍 W11 carry-over CO16;dev mode path uses mock auth per W7 D1 F1.2.1)

### F4 — V9 Register 3-step wizard implementation

- **Component(s)**:**C10** chat UI + **C11** identity + **C13** Email Verification Service(via F5+F6 backend)
- **Spec ref**:architecture.md v6 §5.11 + ADR-0014 + ui-design-reference-v6.md §2.9 V9 wireframe
- **OQ deps**:F1 routing + F5 backend `/auth/register` + `/auth/verify-email` + F6 ACS integration
- **Acceptance criteria**:
  - F4.1 `frontend/app/register/page.tsx` create per V9 wireframe(reuse V8 brand panel split layout)
  - F4.2 Step indicator(reuse W12 F4.9 Stepper pattern;3 steps:Account info → Email verify → Welcome)
  - F4.3 Step 1 Account info:Email + Password + Confirm password(strength indicator)+ Display name(shadcn Input + Label + form validation)
    - Password strength via inline rules(min 8 char + uppercase + digit OR symbol per Tier 1 baseline;client-side only preview)
  - F4.4 Step 2 Email verify:「Check your inbox at <email>」+ 6-digit code input(6 separate Input boxes OR single Input with auto-format)+ 「Resend(60s rate limit)」Button(disabled w/ countdown)
  - F4.5 Step 3 Welcome:「Account created」+ optional first KB selection(disabled — Tier 1 single-KB POC per Q7 default)+ Tour CTA → `/chat`
  - F4.6 Backend integration:Step 1 submit → POST `/auth/register` + show Step 2 awaiting code;Step 2 submit → POST `/auth/verify-email`+ show Step 3 success;Step 3 「Start asking」→ `/chat`
  - F4.7 Error states:registration failures(email_already_exists / invalid_password / verification_token_expired)→ toast + step rollback if needed
- **Effort estimate**:1 day(W13 D3-D4)
- **Owner**:AI(implementation)+ user(end-to-end browser smoke post F5+F6 backend ready)

### F5 — Backend hybrid auth cascade(`/auth/register` + `/auth/verify-email` + `/auth/login` + users table)

- **Component(s)**:**C12** Auth Provider extended + **C08** API Gateway
- **Spec ref**:ADR-0014 §「路徑 B — Self-service register」+ architecture.md v6 §5.10 + §5.11 + CLAUDE.md §3.1(Python 3.12 + FastAPI async + Pydantic v2)
- **OQ deps**:Q22 Resolved(F6 ACS dependency)+ users table schema decision
- **Acceptance criteria**:
  - F5.1 `users` table schema decision + migration:initial in-memory dict mock OR SQLite(Tier 1 per ADR-0014 Consequences Negative — internal `users` table)+ TODO comment for Beta production hardening to Postgres / Cosmos DB(W11 retro CO18 carry-over)
  - F5.2 User Pydantic models:`UserRegister` + `UserLogin` + `UserVerifyEmail` + `User`(exclude password_hash from public model)
  - F5.3 `POST /auth/register` endpoint:validate email format + password strength + check duplicate email + Argon2id hash password + generate verification_token(`secrets.token_urlsafe(32)` 24h expiry)+ store user(verified=False)+ send verification email via F6 service + return success
  - F5.4 `POST /auth/verify-email` endpoint:validate verification_token(non-expired + matches)+ update user verified=True + clear verification_token + return success
  - F5.5 `POST /auth/login` endpoint:lookup user by email + verify Argon2id password match + check verified=True + generate session token(`secrets.token_urlsafe(32)` 7-day expiry)+ store session(httpOnly cookie)+ return user + token
  - F5.6 Session middleware:wire bearer token validation for protected routes(`_PROTECTED_PREFIXES` 已 W7 D1 baseline);self-register users return same `User` shape as MSAL user for downstream consumption parity
  - F5.7 Tests:pytest unit + integration test for each endpoint;coverage ≥ 80% per CLAUDE.md §3.6 H6
  - F5.8 Karpathy §1.3 surgical:non architectural change(ADR-0014 已 covered scope per H1);ADR-0014 default-if-unanswered = Argon2id password hashing per industry standard(non new vendor decision)
- **Effort estimate**:2 days(W13 D2-D4 — largest deliverable;backend most complex piece)
- **Owner**:AI(implementation)+ user(backend test smoke + endpoint integration verify)

### F6 — C13 ACS Email Verification Service integration

- **Component(s)**:**C13** Email Verification Service(NEW per architecture.md v6 §3.7)+ **C12** Auth Provider(consumes via F5)
- **Spec ref**:architecture.md v6 §3.7 + ADR-0014 §「Email Verification Service vendor decision」+ Q22 ACS Resolved
- **OQ deps**:Q22 Resolved + ACS resource provisioning(user / Chris IT engagement parallel — non-blocking for code path since dev mode mock works without real ACS)
- **Acceptance criteria**:
  - F6.1 `backend/api/auth/email_provider.py` create:ACS Email Client wrapper(`azure-communication-email` SDK installed + utility-lib per CLAUDE.md §5.2 H2 example)
  - F6.2 Email template:plain text + HTML alternative(simple template embedded;non template engine Tier 1 per ADR-0014 Consequences Neutral)
  - F6.3 Sender domain config via env var:Tier 1 dev workstation `noreply@dev.ekp-beta.ricoh.com`(SPF/DKIM 自 IT setup post Track A);Beta phase real domain `noreply@ekp-beta.ricoh.com` env switch
  - F6.4 Failure mode handling:ACS API 5xx → `tenacity` retry(已 utility-lib per CLAUDE.md §3.1);fail-soft graceful(register flow surface「verification email pending — please check inbox or resend」per V9 Step 2)
  - F6.5 Mock mode for dev:env var `FEATURE_EMAIL_MOCK=true` → log verification token to backend logs instead of sending(parallel to W7 D1 F1.2.1 mock auth pattern;dev workstation R8 corp proxy or pre-IT-cred)
  - F6.6 Tests:pytest unit test mock send + verify token flow;real ACS smoke deferred Beta phase post sender domain ready
- **Effort estimate**:1 day(W13 D4-D5;parallel to F5 if AI scoped well)
- **Owner**:AI(implementation)+ user(dev mode mock verify + Beta phase real ACS smoke deferred)

### F7 — Phase Gate closeout + W14-admin-views phase folder kickoff

- **Component(s)**:cross-cutting governance
- **Spec ref**:CLAUDE.md §10 R1(rolling-JIT phase folder)+ §10 R5(architectural-adjacent decision via ADR)+ design ref doc §6 implementation sequencing
- **OQ deps**:F1-F6 verdict outcomes
- **Acceptance criteria**:
  - F7.1 W13 phase Gate verdict landed(per W12 F5.1 pattern;PASS / PARTIAL PASS / FAIL with explicit rationale)
  - F7.2 W13 progress.md retro 7 sections complete(What worked / What didn't / Surprises / Decisions / Carry-overs / Time tracking / Spec ref alignment)
  - F7.3 `docs/01-planning/W14-admin-views/{plan,checklist,progress}.md` draft per architecture.md v6 §5.3-§5.5(V2 Admin Dashboard + V3 KB List + V4 KB Detail 5-tab)+ design ref doc §6 W14 scope
  - F7.4 W13 progress.md frontmatter status flipped to `closed`
  - F7.5 No new OQ surface expected(F5+F6 implementation 屬 ADR-0014 already covered scope);if surface → sync to decision-form.md per R4
- **Effort estimate**:0.5 day(W13 D5 final OR W14 D1 absorb if needed)
- **Owner**:AI(draft)+ user(approve + sign-off)

---

## 3. Success Criteria(Phase Gate to W14)

W13 phase Gate **PASS condition**:
1. F1 routing restructure clean + theme provider + dark mode toggle UI ✅
2. F2 V7 Landing page renders + content discipline preserved + responsive ✅
3. F3 V8 Login page renders + dual auth path UI(SSO + self-register form)+ error states + loading state ✅
4. F4 V9 Register 3-step wizard renders + step indicator + form validation + email verify code input + welcome step ✅
5. F5 backend `/auth/register` + `/auth/verify-email` + `/auth/login` endpoints work + users table populated + tests ≥ 80% coverage ✅
6. F6 C13 ACS email service integration + mock mode + sender domain env var ✅
7. F7 closeout retro + W14 phase folder kickoff ✅

W13 phase Gate **PARTIAL PASS** acceptable per Karpathy §1.4:
- F5 users table backing decision(in-memory vs SQLite Tier 1;non Postgres / Cosmos DB Beta hardening)+ ADR-0013 candidate trigger if persistent backing surface as architectural decision
- F6 ACS real send deferred to Beta phase post sender domain ready(mock mode adequate for W13 dev verification per CLAUDE.md §5.5 H5 security)
- F4.13 W12 carry-over functional regression user-defer continued(W13 view-level work iteratively browser-verifies fills gap)

W13 phase Gate **FAIL condition**:
- ADR-0014 scope creep into Tier 2(forgot password / 2FA / OAuth providers — defer per architecture.md v6 §11)
- F5 backend cascade scope expand beyond plan(e.g. role-based access control extension — defer Tier 2)
- C13 ACS API contract breaking change vs Q22 baseline assumption

## 4. Risks(Phase-Specific)

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| F5 users table backing decision blocks F5 implementation | Low | Medium(F5 critical path)| Default to in-memory dict per W1 KB Manager pattern + TODO Beta hardening per W11 retro CO18;ADR-0013 candidate trigger noted if SQLite needed but in-memory dict survives Tier 1 Beta cohort scale |
| F6 ACS resource provisioning blocks F6 real send | Medium | Low | Mock mode `FEATURE_EMAIL_MOCK=true` adequate for W13 dev verification;real send deferred to Beta phase post Track A IT cred + sender domain SPF/DKIM ready |
| Argon2id password hashing dep adds Python package | Low | Low | `argon2-cffi` 屬 industry standard utility-lib per CLAUDE.md §5.2 H2 example;non new vendor decision |
| Routing restructure introduces unexpected regression | Low | Low(reversible)| Per-route smoke browser verify + git revert if regression;W12 F4 functional logic preserved exactly so /chat content unchanged |
| Step 2 email verify code input UX friction | Medium | Low | shadcn Input pattern + 6-digit auto-format library OR 6 separate Inputs + Tab navigation;defer fancy OTP UX to Tier 2 if overrun |

## 5. Day-by-Day Breakdown(rough)

| Day | Date | Focus |
|---|---|---|
| W13 D1 | 2026-06-23 | F1 routing restructure + theme provider + dark mode toggle UI;F2 V7 Landing page begin |
| W13 D2 | 2026-06-24 | F2 V7 Landing finalize;F5 backend hybrid auth begin(users table + Pydantic models + `/auth/register`);F3 V8 Login UI begin parallel |
| W13 D3 | 2026-06-25 | F5 backend continue(`/auth/verify-email` + `/auth/login` + session middleware);F3 V8 Login complete + auth flow wire;F4 V9 Register 3-step wizard begin |
| W13 D4 | 2026-06-26 | F5 backend tests + coverage;F4 V9 Register complete + backend integration;F6 C13 ACS email service integration |
| W13 D5 | 2026-06-27 | F6 finalize + mock mode test;F7 closeout retro + W14 phase folder kickoff |

**Day-by-day caveat**:plan §5 dates tentative;real-calendar 2026-06-10 W12 closeout cascade momentum may continue into W13 same-calendar-day collapse(per W12 D5 closeout Time tracking calibration data — Tier 1 UI sprint phase capacity 1-2 days per phase if pivot momentum clean)。If W13 D6+ overflow:F7 absorb W14 D1。

## 6. Dependencies on Prior Phase

Carry-overs from `W12-ui-foundation-discovery/progress.md` retro § Carry-overs(W12 D5 closeout):
- CO1 F4.13 functional regression user-deferred(non blocker for W13;W13 view-level work iteratively browser-verifies)
- CO2 Theme provider integration → W13 F1 deliverable
- CO3 W12 plan F4.13 acceptance future-proof note → governance add to design ref doc § Maintenance Protocol(non W13 critical path)
- CO4-CO9 W13 immediate scope(routing + Landing + Login + Register + ADR-0014 backend cascade + C13 ACS)→ W13 F1-F6 deliverables exact match
- CO10-CO15 W14-W15 future scope(non W13 blocker)
- CO16-CO19 W16+ Beta deploy(unchanged from W11)

## 7. Plan Changelog

| Date | Change | Reason | Approver |
|---|---|---|---|
| 2026-06-10 | Initial draft(W12 D5 closeout cascade rolling-JIT)| Per CLAUDE.md §10 R1 rolling-JIT;W12 closeout cascade per F5.3 deliverable;W13 immediate scope = W12 retro carry-overs CO4-CO9 exact match | Chris(stakeholder authorization same-session pivot momentum;W12 closeout PASS WITH CAVEAT verdict landed) |

---

**Lifecycle reminder**:呢份 plan `status=draft`(等 W13 D1 active flip post stakeholder authorization)。重大 deviation 入第 7 節 changelog。Sister sprint W14/W15 phase folders **唔會** pre-create(per CLAUDE.md §10 R1 rolling-JIT — 每 phase kickoff 先建)。
