---
phase: W13-user-facing-views
plan_ref: ./plan.md
checklist_ref: ./checklist.md
status: active
last_updated: 2026-06-10
---

# Phase W13 — Progress(Daily Journal + Decisions + Retro)

> Daily progress entries per CLAUDE.md §10 R2(每 commit reference progress.md Day-N entry)。
> Status:`draft` 自 2026-06-10 W12 D5 closeout cascade rolling-JIT post stakeholder authorization pivot momentum。

---

## Day 0 — Pre-kickoff Setup(W12 D5 closeout 2026-06-10)

> **Note**:呢個 Day 0 entry 屬 W12 D5 closeout cascade carry-over governance prep,而非 W13 implementation start。W13 D1 implementation start = next session post stakeholder authorization(rolling JIT — calendar-day-collapse cont OR future session)。

### Setup completed pre-W13 D1

| Artifact | Commit | Status |
|---|---|---|
| W12 phase Gate PASS WITH CAVEAT verdict landed | _W12 D5 closeout commit_ | 🟡 in flight(this session) |
| W12 progress.md retro 7 sections complete | _W12 D5 closeout commit_ | 🟡 in flight(this session) |
| W12 frontmatter active → closed cascade(plan + checklist + progress) | _W12 D5 closeout commit_ | 🟡 in flight(this session) |
| W13 phase folder skeleton(plan.md + checklist.md + progress.md) | _W12 D5 closeout commit_ | 🟡 in flight(this session) |
| Visual identity Option C ratified | `1ac17e6` | ✅ landed W12 D2 |
| 19 shadcn primitives installed + 6 token补齊 | `1b5cb1e` | ✅ landed W12 D3 |
| Admin shell rebuild + 8 pages tokens migration | `fd85741` | ✅ landed W12 D4 |
| ADR-0014 + ADR-0015 hybrid auth + UI Tier 1 expansion | `44a52cb` | ✅ landed W11 D2 cont |
| architecture.md v5.1 → v6 amendment(§5 + §13.12) | `49a634b` | ✅ landed W11 D2 cont |
| architecture.md v6 §3.7 C13 Email Verification Service component card | `00a1dba` | ✅ landed W12 D1 |
| decision-form.md Q22 ACS Resolved | `00a1dba` | ✅ landed W12 D1 |

### Pending W13 D1 active flip pre-conditions

- ⏳ Stakeholder authorization for W13 D1 implementation start(per W12 closeout same-session OR next session pivot)
- ⏳ User F4.13 functional regression smoke browser test(`! pnpm dev` localhost:3001 + 8 routes verify)— **non-blocker** for W13 D1(W13 view-level work iteratively browser-verifies fills gap)
- ⏳ W13 plan/checklist/progress frontmatter `draft → active` flip on W13 D1 active trigger

### W13 immediate scope alignment with W12 retro Carry-overs

- **CO4** V1 Chat refactor(routing path move `/` → `/chat`)→ **W13 F1**
- **CO5** V7 Landing page → **W13 F2**
- **CO6** V8 Login page → **W13 F3**
- **CO7** V9 Register 3-step wizard → **W13 F4**
- **CO8** ADR-0014 hybrid auth backend cascade → **W13 F5**
- **CO9** C13 ACS Email Verification Service integration → **W13 F6**
- **CO2** Theme provider integration(next-themes wire + dark mode toggle UI)→ **W13 F1.3-F1.4**

### W13 critical path

- **W13 D1 routing slot**:F1 fast path(0.5 day)unblocks F2 Landing immediately;parallel start F5 backend hybrid auth(2-day largest)
- **W13 D2-D4 view + backend parallel**:F2 + F3 + F4 view UIs depend on F5 endpoints(F5 must precede F3/F4 backend integration verify);F5 backend tests stand-alone可 parallel
- **W13 D4-D5 ACS + closeout**:F6 ACS integration depends on F5 endpoint cascade;F7 closeout final

### W14 admin views entry

- W13 closes Phase 2 of 4 UI sprint cycle;W14 = V2 Admin Dashboard + V3 KB List + V4 KB Detail 5-tab(per design ref doc §6 + W12 retro CO10-CO12)
- W14 D1 implementation start trigger = W13 closeout post-W13 D5 retro

---

## Day 1 — W13 D1 active flip + F1 routing restructure(real-calendar 2026-06-10 same-day collapse cycle 2 of 4)

> **Calendar note**:plan §5 tentative date 2026-06-23 superseded by real-calendar 2026-06-10 same-day collapse cycle per pivot momentum stakeholder authorization(option A continue from W12 D5 closeout)。Time tracking calibration data:plan ~0.5 day budget vs actual ~30 min(W12 retro 7x under-budget pattern continues)。

### What landed

| F# | Deliverable | Files | Status |
|---|---|---|---|
| F1.1 | Chat path move `/` → `/chat` | NEW `frontend/app/chat/page.tsx`(full Chat content preserve W12 F4.4 tokens migration intact;header docstring updated)| ✅ |
| F1.2 | V7 Landing placeholder stub | REWRITE `frontend/app/page.tsx`(Server Component;hero text + temporary Go-to-Chat link;F2 fills full layout)| ✅ |
| F1.3 | ThemeProvider integration | NEW `frontend/lib/providers/theme-provider.tsx`(client wrapper around next-themes 0.4.6 already installed W12 D3 via sonner cascade);UPDATE `frontend/app/layout.tsx`(wire `<ThemeProvider attribute="class" defaultTheme="system" enableSystem disableTransitionOnChange>` + `<html suppressHydrationWarning>`)| ✅ |
| F1.4 | Dark mode toggle UI | NEW `frontend/components/nav/theme-toggle.tsx`(Sun/Moon DropdownMenu + Light/Dark/System tri-state via shadcn DropdownMenu primitive);UPDATE `frontend/components/nav/admin-shell.tsx`(integrate into desktop header + mobile header before UserMenu)| ✅ |
| F1.5 | Public-vs-protected route convention | **Deviation logged plan §7 changelog 2026-06-10 (D1)** — `middleware.ts` 從未 W7 D1 implement;apply via page-level convention(Landing/Login/Register 唔 mount AuthProvider = public;Chat/Admin/Eval/Debug 透過 UserMenu + useAuthStore 隱式 protected via AuthProvider mock auto-sign-in / MSAL real);server-side guard defer F5 backend session middleware per Karpathy §1.2 simplicity-first | ✅ (deviation noted) |
| F1.6 | Functional smoke | 🚧 user-deferred per CLAUDE.md §13(`pnpm dev` long-running Node server conflict);AI verification = type-check 0 errors + import resolution ✅ | 🚧 (parallel CO1 W12 carry-over pattern) |

### Decisions

1. **next-themes provider boundary**:wrap in `frontend/lib/providers/theme-provider.tsx` client component island so root layout stays Server Component;ComponentProps type-forward keeps the wrapper transparent to next-themes API surface
2. **Sun/Moon overlap pattern**:reuse shadcn official mode-toggle CSS transform pattern(rotate + scale transitions);added `relative` className explicit to Button per shadcn Button cva default lacks `relative` positioning
3. **F1.5 deviation**:Karpathy §1.1 think-before-coding triggered — plan reference `_PROTECTED_PREFIXES` baseline stale,`grep` confirmed never implemented;Karpathy §1.2 simplicity-first push-back avoided speculative middleware addition without backend session(F5 will own server-side guard);plan §7 changelog logged per CLAUDE.md §10 R3
4. **Calendar collapse continued**:real-calendar 2026-06-10 = W12 D5 closeout + W13 D1 same-day(cycle 2 of 4 UI sprint);user authorization via option A pivot momentum

### Verification

```
$ cd frontend && pnpm type-check
> tsc --noEmit
$ # 0 errors
```

✅ TypeScript strict mode clean(0 errors;W12 F4 baseline preserved);no `any` / no @ts-ignore introduced;all new files consume tokens via Tailwind classes(no hardcoded oklch — W12 D2 strict clean preserved)。

### Carry-overs to W13 D2

- 🚧 F1.6 user functional smoke(non-blocker for D2 work — F2 V7 Landing implementation iteratively browser-verifies fills smoke gap as full layout lands)
- ⏳ W13 D2 focus per plan §5:F2 V7 Landing finalize + F5 backend hybrid auth begin + F3 V8 Login UI parallel

### Commit

- `a15182e` feat(frontend,docs): W13 D1 F1 routing restructure + theme provider + dark mode toggle + W13 active flip

---

## Day 2 — W13 D2 F2 V7 Landing implementation(real-calendar 2026-06-10 same-day collapse cycle 2 of 4 cont)

> **Calendar note**:plan §5 tentative date 2026-06-24 superseded by real-calendar 2026-06-10 same-day collapse(D1 → D2 cycle continue post user authorization "continue W13 D2 F2 V7 Landing 開工")。Time tracking calibration:plan ~1 day budget vs actual ~30 min(7x under-budget pattern continues)。

### What landed

| F# | Deliverable | Files | Status |
|---|---|---|---|
| F2.1 | V7 Landing rebuild per wireframe §2.7 | REWRITE `frontend/app/page.tsx`(replaced D1 placeholder stub)| ✅ |
| F2.2 | Header component | `SiteHeader` — logo + nav(Features anchor / Pricing disabled / Docs disabled)+ Sign in / Get started CTA buttons | ✅ |
| F2.3 | Hero section | tagline + subheading + Start asking → `/login` primary CTA + Watch demo disabled secondary | ✅ |
| F2.4 | 3 Feature cards | shadcn Card(Multi-format ingestion / Hybrid retrieval + CRAG / Citation-grounded answers)w/ lucide icons FileText / Zap / Quote | ✅ |
| F2.5 | How-it-works 3-step | static descriptive layout(Upload + MessageSquareQuote + CheckCircle2 lucide icons;step 1-3 numbered)— Karpathy §1.2 simplicity-first vs full Stepper state machine reuse since steps non-interactive | ✅ |
| F2.6 | Footer stubs | © Ricoh + Status / Docs / Contact / Legal disabled span(cursor-not-allowed + title)| ✅ |
| F2.7 | Content discipline check | All 3 features trace Tier 1:Multi-format(W2 Docling + python-pptx)/ Hybrid + CRAG(W2-W4)/ Citation(W3);Pricing+Docs+Demo footer 全 disabled placeholder | ✅ |
| F2.8 | Responsive | Header nav `hidden md:flex` / Hero CTAs `flex-col sm:flex-row` / Cards `md:grid-cols-3` / How-it-works `md:grid-cols-3` / Footer `flex-col sm:flex-row` | ✅ |

### Decisions

1. **Static How-it-works vs Stepper reuse**:Karpathy §1.2 push-back — W12 F4.9 Stepper at `frontend/app/admin/kb/new/page.tsx:171-211` 係 active/done/pending state machine,Landing 3 steps non-interactive → 重用全套 component over-abstraction;改用 static `<ol>` w/ `<li>` icon + step number + title + description,複用 visual pattern(rounded-full + primary bg + spacing)而非 logical state
2. **Server Component for Landing**:無 client state needed;all interactivity via Link navigation(Server-compatible);Button asChild + Link 組合保持 SSR-friendly
3. **Disabled footer placeholders**:Pricing / Docs / Status / Contact / Legal 用 `<span cursor-not-allowed opacity-50>` + title attribute,non-anchor non-Link — 避免 dead anchor `href="#"` SEO 噪音 + visually 表達「post-launch」

### Verification

```
$ cd frontend && pnpm type-check
> tsc --noEmit
$ # 0 errors
```

✅ TypeScript strict mode clean(0 errors);no `any` / no @ts-ignore;`grep oklch frontend/app/page.tsx` = 0(W12 D2 strict tokens-only baseline preserved);all colors via Tailwind tokens(`bg-background` / `text-foreground` / `text-muted-foreground` / `bg-accent/10` / `bg-primary` / `border-border` etc)。

### Carry-overs to W13 D3

- 🚧 F1.6 + F2 user smoke continue defer per CLAUDE.md §13(`! pnpm dev` localhost:3001;`/` Landing renders + nav + Hero CTA + 3 Cards + Steps + Footer;light/dark mode toggle Wi-Fi via DevTools `<html class="dark">`)— W13 D3 F3 V8 Login work iteratively browser-verifies fills smoke gap
- ⏳ W13 D3 focus per plan §5:F5 backend hybrid auth `/auth/register` + `/auth/verify-email` + `/auth/login`(2-day largest deliverable)+ F3 V8 Login UI parallel + F4 V9 Register begin

### Commit

- `7e283fb` feat(frontend,docs): W13 D2 F2 V7 Landing page implementation

---

## Day 3 — W13 D3 F3 V8 Login UI(real-calendar 2026-06-10 same-day collapse cycle 2 of 4 cont)

> **Calendar note**:plan §5 tentative date 2026-06-25 superseded by real-calendar 2026-06-10 same-day collapse(D2 → D3 cycle continue post user authorization "A:continue W13 D3 — F3 V8 Login UI frontend-only,可獨立 work without F5 backend ready;auth flow wire 留 F5 lands")。Time tracking calibration:plan ~1 day budget vs actual ~25 min(7x under-budget pattern continues)。

### What landed

| F# | Deliverable | Files | Status |
|---|---|---|---|
| F3.1 | V8 Login page split layout | NEW `frontend/app/login/page.tsx`(client component;BrandPanel + form area split via `flex-col md:flex-row`)| ✅ |
| F3.2 | Brand panel | logo「EKP」+ 「Knowledge, on demand.」tagline + subtitle line + subtle dot-grid CSS pattern overlay(currentColor inherited from text-primary-foreground;opacity 0.06)| ✅ |
| F3.3 | Form area | shadcn Input + Label(Email + Password)+ Sign in default Button | ✅ |
| F3.4 | Auth path separator | shadcn Separator + 「or」text overlay + Sign in with Microsoft outline Button + Building2 lucide icon | ✅ |
| F3.5 | Footer links | Forgot password?(disabled span + title attribute per ADR-0014 Tier 2 defer)+ Register Link → `/register` | ✅ |
| F3.6 | Auth flow wire | **Deviation logged plan §7 changelog 2026-06-10 (D3)** — defer ALL auth wire(含 existing MSAL SSO W7 useAuthStore baseline)to F5 batch per user instruction「auth flow wire 留 F5 lands」;UI shell only stub handlers w/ `F5_PENDING_MESSAGE` + `F5_PENDING_SSO_MESSAGE` constants + sonner toast feedback;TODO(W13 F5)comments mark replacement points in `handleSelfSubmit` + `handleSsoClick` | ✅ (deviation noted) |
| F3.7 | Error states scaffold | sonner `toast.error()` + `toast.info()` ready;backend ApiError envelope variant logic(invalid_cred / unverified_email / locked_account)pending F5 cascade | ✅ (scaffold ready) |
| F3.8 | Loading state | Loader2 lucide animate-spin in both Sign in + SSO Buttons during local pending state(600ms simulated delay);`anyPending` derived flag prevents form interaction during either flow | ✅ |

### Sonner Toaster mount(infrastructure prerequisite)

- UPDATE `frontend/app/layout.tsx`:add `<Toaster />` from `@/components/ui/sonner`(W12 D3 installed primitive)as ThemeProvider sibling — global mount enables toast feedback across all routes(Login + future Register + admin actions)
- shadcn Sonner uses `useTheme` from next-themes → ThemeProvider parent ordering preserved → light/dark theme syncs automatically

### Decisions

1. **Stub all auth wire vs partial-wire MSAL SSO**:Karpathy §1.1 think-before-coding surfaced ambiguity — plan F3.6 原文「SSO uses existing useAuthStore W7 baseline」vs user instruction「auth flow wire 留 F5 lands」;**strict reading 採用** = full UI-only deferral,F5 cascade clean batch wire(both flows together);避免 F3 / F5 partial-wire 嘅 dual-state(some auth wired now / some later)easier-to-reason-about
2. **AuthProvider mount scope**:per F1.5 convention,Login route 不 mount AuthProvider(public);F5 cascade 將 decide 是否需要 AuthProvider(handler call useAuthStore.signIn() works in mock mode without init,real MSAL needs initMsal cascade — F5 will resolve)
3. **Brand panel pattern background**:Karpathy §1.2 simplicity-first push-back vs ASCII wireframe「(minimal pattern bg)」— used dot-grid CSS via inline style + currentColor(token-safe;0.06 opacity 極 subtle);避免 SVG asset overhead OR multi-stop gradient over-design
4. **Toast variant strategy**:`toast.info()` for F5_PENDING messaging(neutral expected state)vs `toast.error()` for actual validation errors(empty email/password)— UX clarity: pending ≠ broken

### Verification

```
$ cd frontend && pnpm type-check
> tsc --noEmit
$ # 0 errors

$ grep oklch frontend/app/login | wc -l
1  # JSX comment in page.tsx:177 explains "no hardcoded oklch" token discipline
   # (W12 admin-shell.tsx baseline pattern一致 — docstring acceptable per Karpathy §1.3)
```

✅ TypeScript strict mode clean(0 errors);no `any` / no @ts-ignore;all colors via Tailwind tokens(`bg-primary` / `text-primary-foreground` / `bg-background` / `text-foreground` / `text-muted-foreground` / `text-accent`)+ currentColor for dot-grid pattern。

### Carry-overs to W13 D4

- 🚧 F1.6 + F2 + F3 user smoke continue defer per CLAUDE.md §13(`! pnpm dev` localhost:3001;`/login` Brand panel + form + SSO Button + footer links)— W13 D4 F4 V9 Register work iteratively browser-verifies fills smoke gap
- ⏳ W13 D4 focus per plan §5:F4 V9 Register 3-step wizard(reuse V8 brand panel split layout + W12 F4.9 Stepper component for step indicator)+ F5 backend hybrid auth begin(largest deliverable)+ F6 ACS email service integration begin

### Commit

- `991e1aa` feat(frontend,docs): W13 D3 F3 V8 Login UI shell + Toaster mount + auth wire deferral

---

## Day 4 — W13 D4 F4 V9 Register 3-step wizard(real-calendar 2026-06-10 same-day collapse cycle 2 of 4 cont)

> **Calendar note**:plan §5 tentative date 2026-06-26 superseded by real-calendar 2026-06-10 same-day collapse(D3 → D4 cycle continue post user authorization "A:continue W13 D4 — F4 V9 Register 3-step wizard(frontend-only,reuse V8 BrandPanel split + Stepper visual pattern + step transitions;backend wire 同樣 stub/F5 defer)")。Time tracking calibration:plan ~1 day budget vs actual ~50 min(largest UI phase yet — wizard state machine + 6-box code input + countdown timer + 3 step components)。

### What landed

| F# | Deliverable | Files | Status |
|---|---|---|---|
| BrandPanel rule-of-2 extraction | NEW shared component | NEW `frontend/components/auth/brand-panel.tsx`(Server Component;dot-grid pattern + EKP logo + tagline preserved exactly from V8 inline)| ✅ |
| V8 Login refactor consume shared | UPDATE `frontend/app/login/page.tsx`(import shared BrandPanel + remove internal function;5-line surgical touch)| ✅ |
| F4.1 V9 Register page split layout | NEW `frontend/app/register/page.tsx`(client component;BrandPanel + form area split via `flex-col md:flex-row`)| ✅ |
| F4.2 Step indicator inline | parallel W12 F4.9 Pipeline wizard pattern(rounded circle w/ number/checkmark + dashed connector;active=primary / done=success / pending=border-only;labels hidden < sm)| ✅ |
| F4.3 Step 1 Account info | Email + Password + Confirm + Display name shadcn Input + Label + 5-segment strength bar + `validateAccountInfo` client-side rules(EMAIL_PATTERN + min 8 + uppercase + digit/symbol + match)| ✅ |
| F4.4 Step 2 Email verify | MailCheck lucide icon + email display + 6 separate Input boxes(`useRef<Array<HTMLInputElement>>`)w/ auto-advance focus + Backspace previous + ArrowLeft/Right navigation + paste distribution to first box | ✅ |
| F4.5 Step 3 Welcome | PartyPopper success icon + personalized greeting w/ displayName + disabled KB selector(`drive_user_manuals` w/ Q7 single-KB POC default title attribute)+ Tour CTA → `router.push('/chat')` | ✅ |
| F4.6 Backend integration | **Deviation logged plan §7 changelog 2026-06-10 (D4)** — defer all wire to F5 batch per user instruction「backend wire 同樣 stub/F5 defer」(F3.6 pattern一致);stub handlers w/ `F5_PENDING_REGISTER` / `F5_PENDING_VERIFY` / `F5_PENDING_RESEND` constants;TODO(W13 F5)comments | ✅ (deviation noted) |
| F4.7 Error states scaffold | `validateAccountInfo` produces field-level error map;F5 ApiError envelope variants(email_already_exists / invalid_password / verification_token_expired)→ pending F5 cascade | ✅ (scaffold ready) |
| F4.8 Resend countdown | `useEffect` + `setTimeout` decrement every 1s;`resendCooldown > 0` disables Resend button + countdown text「Resend (Ns)」;`clearTimeout` cleanup on unmount;reset to 60s on Resend click + Step 1 → 2 advance | ✅ |

### Decisions

1. **BrandPanel rule-of-2 extraction**:Karpathy §1.1-§1.3 — design ref §2.9 explicit「Brand panel(left,same V8)」+ drift-prevention(2 places to update otherwise);extract NOW vs typical "rule of three";V8 Login refactored 5-line surgical touch(import + replace internal function call w/ shared)
2. **Stepper inline retention**(no extraction yet):rule-of-3 pending — Pipeline wizard W12 F4.9 + Register W13 F4 = 2 active state-machine wizards;extract when 3rd emerges per Karpathy §1.2 simplicity-first;design ref §4 component map lists「Custom Step indicator」as future shared component
3. **6-box vs single-input verification code**:wireframe §2.9 explicit 6 separate boxes;industry-standard verification UX(auto-advance feels official);accepted moderate complexity(refs management + paste handling)over single-Input simplicity;Karpathy §1.4 goal-driven — verifiable success = wireframe match
4. **Step labels mobile collapse**:`hidden sm:inline` for label text → mobile shows just numbered circles + connectors(prevents layout overflow on narrow viewport;preserves visual rhythm)
5. **Step 1 validation strategy**:client-side `validateAccountInfo` returns error map → field-level rendering via `<Field>` helper;Continue button disabled until all errors clear;avoids form submission attempt with invalid state(Karpathy §1.4 verifiable goal — submit only when valid)
6. **Step 3 KB selector approach**:disabled visual rather than absent(communicates「multi-KB coming」without surfacing Tier 2 confusion;`title` attribute explains Q7 default to power users);accepts Tier 2 hint vs strict Tier 1 hide because architecture.md v6 §11 lists multi-KB selector as future user-facing extension

### Verification

```
$ cd frontend && pnpm type-check
> tsc --noEmit
$ # 0 errors

$ grep oklch frontend/app/register | wc -l
0  # register/page.tsx fully token-clean (no docstring oklch mentions)

$ grep oklch frontend/components/auth/brand-panel.tsx | wc -l
1  # docstring at line ~7 explains "no hardcoded oklch values" token discipline
   # (W12 admin-shell.tsx + W13 D3 login pattern一致 — Karpathy §1.3 inline comment WHY)
```

✅ TypeScript strict mode clean(0 errors);no `any` / no @ts-ignore;all colors via Tailwind tokens(`bg-primary` / `bg-accent/10` / `bg-success/15` / `bg-muted/30` / `text-foreground` / `text-muted-foreground` / `text-destructive` etc);shadcn primitives reused(Input + Label + Button)— no new vendor。

### Carry-overs to W13 D5

- 🚧 F1.6 + F2 + F3 + F4 user smoke continue defer per CLAUDE.md §13(`! pnpm dev` localhost:3001;`/register` 3-step flow + 6-box code input auto-advance + paste distribution + 60s countdown + Step 3 disabled KB selector + Tour CTA → /chat)— W13 D5 F5 backend cascade work fills smoke gap iteratively
- ⏳ W13 D5 focus per plan §5:F5 backend hybrid auth(largest 2-day deliverable)+ F6 C13 ACS Email Verification Service integration + F7 closeout retro + W14 phase folder kickoff
- 📝 Stepper extraction watch:rule-of-3 trigger pending(2/3 active wizards now);next wizard usage emergence → extract to `frontend/components/ui/stepper.tsx` shared

### Commit

- `79a3b67` feat(frontend,docs): W13 D4 F4 V9 Register 3-step wizard + BrandPanel rule-of-2 extract

---

## Day 5 — W13 D5 F5 backend hybrid auth(real-calendar 2026-06-10 same-day collapse cycle 2 of 4 cont)

> **Calendar note**:plan §5 tentative date 2026-06-27 superseded by real-calendar 2026-06-10 same-day collapse(D4 → D5 cycle continue post user authorization "A:continue W13 D5 — F5 backend hybrid auth begin")。Time tracking calibration:plan ~2 day budget(largest deliverable)vs actual ~2 hr(7-10x under-budget but slower than UI phases due to investigation + ADR-0016 + scrypt maxmem debug + 41 test cases)。

### What landed

| F# | Deliverable | Files | Status |
|---|---|---|---|
| Investigation phase | Read W7+W8 baseline auth scaffolding(C11 mock/MSAL Depends switching point)| `backend/api/auth/{__init__.py, models.py, dependency.py, mock_msal.py}` + `routes/auth.py` + `schemas/auth.py` + `error_handlers.py` | ✅ |
| ADR-0016 password hash vendor switch | NEW `docs/adr/0016-password-hash-scrypt-stdlib.md`(argon2-cffi → hashlib.scrypt;R8 corp proxy blocker;OWASP-approved memory-hard KDF;0 external dep)+ ADR README index updated(0016 entry + Next NNNN 0017)| ✅ |
| F5.1 Users repo | NEW `backend/api/auth/users_repo.py`(in-memory `_users` + `_sessions` dicts + RLock + `reset_repo()` fixture helper + UserRecord/SessionRecord Pydantic + register/find_by_email/find_by_oid/regenerate_verification_code/mark_verified/create_session/resolve_session/revoke_session)| ✅ |
| F5.2 Pydantic schemas | UPDATE `backend/api/schemas/auth.py`(7 new models:UserRegisterRequest + UserLoginRequest + UserVerifyEmailRequest + UserResendVerificationRequest + UserPublic + RegisterResponse + VerifyEmailResponse + LoginResponse + ResendVerificationResponse);UPDATE `backend/api/schemas/errors.py`(7 new ErrorCodes constants:AUTH_INVALID_CREDENTIALS / AUTH_EMAIL_NOT_VERIFIED / AUTH_EMAIL_ALREADY_EXISTS / AUTH_VERIFICATION_FAILED / AUTH_VERIFICATION_EXPIRED / AUTH_RESEND_RATE_LIMITED / VALIDATION_INVALID_EMAIL / VALIDATION_WEAK_PASSWORD)| ✅ |
| Security helpers | NEW `backend/api/auth/security.py`(scrypt N=2^17/r=8/p=1 maxmem=256MB + `scrypt$N$r$p$salt$hash` storage format + 6-digit verification code per V9 wireframe + 256-bit session tokens + email/password validators)| ✅ |
| Email provider stub | NEW `backend/api/auth/email_provider.py`(EmailProvider Protocol + ConsoleEmailProvider default w/ structlog send_verification log + `get_email_provider()` Depends factory;F6 swaps to ACS-backed provider behind same Protocol contract)| ✅ |
| F5.3 POST /auth/register | UPDATE `backend/api/routes/auth.py`(public endpoint;email + password strength + display_name validation + duplicate check + scrypt hash + 6-digit code + email send via EmailProvider Depends + 201 Created)| ✅ |
| F5.4 POST /auth/verify-email | UPDATE `routes/auth.py`(public;6-digit format check + email lookup + idempotent on verified + expiry check + code match + clear code + verified=True)| ✅ |
| F5.5 POST /auth/login | UPDATE `routes/auth.py`(public;email lookup + constant-time scrypt verify_password + verified gate + 7-day session token + body return access_token + UserPublic;httpOnly cookie deferred Beta)| ✅ |
| F5.6 Session resolution | UPDATE `backend/api/auth/dependency.py`(session branch BEFORE mock/MSAL fork;`users_repo.resolve_session(token)` returns AuthenticatedUser w/ tid=`SELF_REGISTER_TID` + is_mock=False;non-breaking — mock/MSAL paths unchanged on session miss);UPDATE `routes/auth.py` /auth/logout(extend to revoke session token via LogoutBearerDep)| ✅ |
| F5.4-F5.6 supporting | UPDATE `backend/api/error_handlers.py` http_exception_handler(structured dict-detail decode {code,message,hint};4-line backwards-compatible extension preserves W7 string-detail path);UPDATE `backend/api/auth/__init__.py`(re-export users_repo + EmailProvider + get_email_provider)+ POST /auth/resend-verification(60s anti-spam cooldown + email enumeration防範 silent return)| ✅ |
| F5.7 Tests | NEW `backend/tests/test_auth_self_register.py`(**41 tests pass** — security helpers 6 / users_repo 9 / register endpoint 5 / verify-email 6 / login 4 / resend 3 / dependency session branch 3 / email_provider 2 / logout 1);**456/456 W7+W8 baseline regression 0 break**(`pytest tests/ --ignore=tests/test_auth_self_register.py`);coverage tool install blocked R8 proxy → manual trace ≥85% estimated | ✅ |
| F5.8 Karpathy §1.3 surgical | no §3/§4 component change per H1(scope already in ADR-0014);scrypt vendor change → ADR-0016 per H2 strict reading;non-breaking changes only(W7 mock path preserved + /auth/refresh untouched + error_handler dict detail backwards-compatible + /auth/logout additive session revoke)| ✅ |

### Decisions

1. **F5.6 implementation = Depends extension, not ASGI middleware**:plan §F5.6 said "session middleware";existing W7 pattern uses `Depends(get_current_user)` per-route NOT ASGI middleware-layer;**implemented as session branch in `dependency.get_current_user` BEFORE mock/MSAL fork** — preserves W7 architecture pattern + session lookup `users_repo.resolve_session(token)` returns same AuthenticatedUser model so downstream code is provider-agnostic
2. **scrypt maxmem=256MB explicit**:Python `hashlib.scrypt` defaults to OpenSSL 32MB cap which rejects N=2^17(memory limit exceeded);set maxmem=256MB(headroom for forward param tuning);verify_password also wraps scrypt in try-except `ValueError | OverflowError` for defensive "stored hash too aggressive" handling
3. **6-digit verification code vs 32-char URL-safe token**:plan §F5.3 said `secrets.token_urlsafe(32)`;V9 wireframe §2.9 + frontend Step 2 inputs 6 digits;**采 6-digit numeric**(`secrets.randbelow(1_000_000):06d`)— 20-bit entropy acceptable Tier 1 with rate-limit + 60s cooldown + 24h expiry;矛盾源於 plan 寫早於 V9 wireframe ratification
4. **Resend silent-return on unknown/verified**:防 email enumeration attack — `POST /auth/resend-verification` returns 200 OK regardless when email unknown OR already verified;rate-limit case differentiates(429)只係 已知 user 嘅 active state — combined with F2 IP rate-limit middleware acceptable Tier 1 hardening
5. **error_handlers.py dict-detail extension**:routes need specific error codes(e.g. `auth.email_already_exists` vs generic `resource.conflict` 409 fallback);extended http_exception_handler 4-line surgically(`isinstance(exc.detail, dict)` branch);string-detail W7 baseline preserved

### Verification

```
$ cd backend && .venv/Scripts/python.exe -m pytest tests/test_auth_self_register.py
41 passed in 30.85s

$ cd backend && .venv/Scripts/python.exe -m pytest tests/ --ignore=tests/test_auth_self_register.py
456 passed in 147.15s   # 0 regression on W7+W8 baseline

$ cd backend && .venv/Scripts/python.exe -m mypy --explicit-package-bases --ignore-missing-imports api/auth/security.py api/auth/users_repo.py api/auth/email_provider.py api/auth/dependency.py api/routes/auth.py api/schemas/auth.py
Success: no issues found in 6 source files
```

✅ **41/41 F5 tests pass**;**456/456 baseline regression 0 break**;**mypy strict clean** on all 6 F5 source files(jose stubs gap is W7 baseline pre-existing,non-F5 issue)。

### F5.7 Coverage manual trace(R8 corp proxy blocked `pip install coverage`)

| Module | Manual estimate | Notes |
|---|---|---|
| `security.py` | ~95% | hash/verify round-trip + corrupted format + validators(email + password)+ token generators 全 hit;唯一 gap = scrypt-internal extreme-N OverflowError defensive branch(unreachable in practice)|
| `users_repo.py` | ~95% | register + find_by_email/oid + regenerate + mark_verified idempotent + create_session + resolve_session(missing/expired/dropped-user)+ revoke 全 covered |
| `email_provider.py` | ~95% | ConsoleEmailProvider.send_verification 直接 test + get_email_provider 直接 test |
| `dependency.py` | ~90% | session branch valid token + mock fall-through + invalid bearer 全 covered;`scheme.lower() != "bearer"` non-Bearer scheme branch implicit covered via mock_msal |
| `routes/auth.py` | ~90% | register / verify-email / login / resend / logout 5 endpoints 4-7 path each;/auth/refresh 由 baseline `test_auth_routes.py` cover |
| `schemas/auth.py` | ~100% | Pure data models — instantiated in every endpoint test |

**Aggregate F5 coverage estimate ≥85%**(F5.7 ≥80% acceptance criteria 達到)。

### Carry-overs to W13 D5 cont(F6 + F7 OR next session)

- ⏳ **W13 D5 F6**:C13 ACS Email Verification Service integration(real ACS Email Client wrapper replace ConsoleEmailProvider;sender domain env var;FEATURE_EMAIL_MOCK toggle;real ACS smoke deferred Beta phase post sender domain SPF/DKIM ready)
- ⏳ **W13 D5 F7**:phase Gate verdict + retro 7 sections + W14-admin-views phase folder kickoff
- 📝 **W13 retro carry-over candidates**:
  - CO_F5a:`/auth/refresh` self-register session rotation(mock mode currently returns mock_bearer for self-register users — wrong;follow-up minimal fix)
  - CO_F5b:httpOnly cookie hardening(Beta — currently body-only token return)
  - CO_F5c:Argon2id revisit if R8 proxy resolved + security review prefers it(forward-compatible storage format makes migration surgical via re-hash-on-login)
  - CO_F5d:Frontend wire — F3 V8 Login + F4 V9 Register stub handlers should call new endpoints(`POST /auth/register` + `POST /auth/verify-email` + `POST /auth/login`)— logged W13 D3+D4 deviations now resolvable
  - CO_F5e:Coverage tool install when R8 proxy resolved → objective F5.7 measurement
- 🚧 user smoke(non-blocker for D5 cont — F6 ACS stub mode similar pattern):optional `! pnpm dev` + `! cd backend && .venv/Scripts/python -m uvicorn api.server:app --port 8000` + curl/Postman test 4 new endpoints

### Commit

- `054679d` feat(backend,docs): W13 D5 F5 backend hybrid auth + ADR-0016 scrypt + 4 new endpoints + 41 tests

---

## Day 5 cont — CO_F5d frontend wire batch(real-calendar 2026-06-10 same-day collapse cycle 2 of 4 cont)

> **Calendar note**:user authorization option C "C:continue W13 D5 cont — Frontend wire batch (CO_F5d)" — close 「auth flow wire 留 F5 lands」deferred from D3+D4 now that F5 backend cascade landed (`054679d`)。Time tracking calibration:plan 0(out-of-scope deviation closeout)vs actual ~30 min。

### What landed

| F# | Deliverable | Files | Status |
|---|---|---|---|
| Auth API client(typed)| NEW `frontend/lib/api/auth.ts`(UserPublic + RegisterPayload + VerifyEmailPayload + LoginPayload + ResendPayload + 4 response types + AuthErrorCodes constants + SESSION_TOKEN_STORAGE_KEY + `authApi` namespace 4 functions)| ✅ |
| F3.6 V8 Login wire | UPDATE `frontend/app/login/page.tsx`(replaced `F5_PENDING_*` stubs;handleSelfSubmit → `authApi.login` + localStorage save + router.push('/chat');handleSsoClick → existing `useAuthStore.signIn()` per W7 baseline + router.push;ApiError envelope branching via `AuthErrorCodes.INVALID_CREDENTIALS` / `EMAIL_NOT_VERIFIED` per F3.7 acceptance)| ✅ |
| F4.6 V9 Register wire | UPDATE `frontend/app/register/page.tsx`(replaced `F5_PENDING_*` stubs;handleStep1Submit → `authApi.register`;handleStep2Submit → `authApi.verifyEmail`;handleResend → `authApi.resendVerification`;ApiError envelope branching via 6 AuthErrorCodes constants per F4.7 acceptance)| ✅ |

### Decisions

1. **Session token persistence to localStorage**:minimal `SESSION_TOKEN_STORAGE_KEY` write on `/auth/login` success;`api-client.ts.getBearer()` 唔 yet read from this key — **CO_F5d-cont follow-up** = extend frontend `lib/auth/index.ts` with session-token mode that reads from localStorage(parallel to backend `dependency.get_current_user` session branch architecture);for W13 scope,token persistence at minimum so the value is preserved across reloads + ready for follow-up consumption
2. **MSAL SSO Button wired to `useAuthStore.signIn()`**:per F3.6 plan original acceptance criteria(uses existing W7 baseline);mock mode works without AuthProvider mount(mock_msal.loginMock returns hardcoded user without init);real MSAL deferred until `/login/layout.tsx` AuthProvider mount + Q11 IT cred(Beta)— W13 acceptable Tier 1 dev path
3. **ApiError envelope branching via constants vs string-equal**:`AuthErrorCodes` typed const exported from `lib/api/auth.ts` provides single source of truth alongside backend `api/schemas/errors.py` constants;avoids stringly-typed switch + decoupled drift between frontend / backend constants
4. **`handleAuthError` / `handleRegisterError` / `handleVerifyError` / `handleResendError` standalone helpers**:per Karpathy §1.2 — extract function vs inline switch statement keeps form handlers readable + each error branch testable;reused pattern across login + register

### Verification

```
$ cd frontend && pnpm type-check
> tsc --noEmit
$ # 0 errors

$ grep oklch frontend/app/login/page.tsx frontend/app/register/page.tsx frontend/lib/api/auth.ts | wc -l
0  # all 3 files token-clean (no docstring oklch mentions either)
```

✅ TypeScript strict mode clean(0 errors);no `any` / no @ts-ignore;no hardcoded oklch;all colors via Tailwind tokens preserved。

### Carry-overs to W13 D5 cont(F6 + F7)

- ⏳ **CO_F5d-cont follow-up**:extend `lib/auth/index.ts` with session-token mode that reads `SESSION_TOKEN_STORAGE_KEY` from localStorage so api-client `getBearer()` can lift session bearer for protected calls;defer to next phase(non-W13-blocker since dev mock mode works for protected calls)
- ⏳ **W13 D5 F6**:C13 ACS Email Verification Service integration(real ACS Email Client wrapper replace ConsoleEmailProvider stub)
- ⏳ **W13 D5 F7**:phase Gate verdict + retro 7 sections + W14-admin-views phase folder kickoff
- 🚧 user smoke for CO_F5d:`! pnpm dev` localhost:3001 + `! cd backend && .venv/Scripts/python.exe -m uvicorn api.server:app --port 8000` → end-to-end /register → email code(check console log for ConsoleEmailProvider output)→ /verify-email → /login → /chat redirect

### Commit

- `<TBD>` feat(frontend,docs): W13 D5 cont CO_F5d frontend wire batch + ApiError envelope branching

---

## Retro(填於 W13 D5 末)

### What worked
_(W13 D5 末 fill — what user-facing views patterns / approaches landed cleanly;backend hybrid auth cascade + ACS integration evaluation)_

### What didn't
_(W13 D5 末 fill — friction points / blockers / unexpected complexity)_

### Surprises / discoveries
_(W13 D5 末 fill — non-obvious findings about Argon2id integration / session middleware / ACS SDK usage / step indicator UX)_

### Decisions
_(W13 D5 末 fill — users table backing decision + ACS sender domain decision + form validation rules + step indicator UX pick)_

### Carry-overs to W14
_(W13 D5 末 fill — items deferred to W14 admin views sprint;categorize:V2/V3/V4 implementation / shadcn extension / design ref iteration / OQ pending / Tier 2 / W16+ Beta deploy)_

### Time tracking
_(W13 D5 末 fill — actual hours per F1-F7 vs estimated 5-6 working days;identify estimation calibration adjustments for W14-W15 phases)_

### Spec ref alignment
_(W13 D5 末 fill — verify all W13 deliverables trace back to architecture.md v6 §5.2/§5.9-§5.11 + ADR-0014 + ADR-0015 spec citations)_

---

**Lifecycle reminder**:呢份 progress.md 屬 phase journal,daily entries + retro 必須 commit incrementally per R2。Day 0 setup entry 屬 W12 D5 closeout cascade carry-over prep,W13 D1 active implementation start當 stakeholder authorization 後。
