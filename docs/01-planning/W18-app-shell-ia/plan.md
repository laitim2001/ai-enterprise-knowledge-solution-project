---
phase: W18-app-shell-ia
name: "Unified Application Shell IA — <AppShell> (top bar + left sidebar + main content) across all authenticated views + (app)/ route group + flattened URLs (no /admin/) + /dashboard real overview + /settings + global search Cmd+K + login-gate + V7 Landing removal + login→/dashboard (per ADR-0024)"
sprint_week: W18
start_date: 2026-05-10              # real-calendar — kicked off at W17 closeout per the ADR-0024 acceptance cascade (Chris directive); independent of W16 F1-F4 (Track-A-blocked) and Tier 2 prep per ADR-0024 Q5
end_date: 2026-05-24                # ~1-1.5 weeks per ADR-0024 (F3 route restructure is the largest; same-day / multi-day collapse possible per W12-W15 precedent — frontmatter is a window, not a commitment)
status: active                     # `active` from kickoff 2026-05-10 — the Chris directive ("開 W18 phase folder + plan.md + amend architecture.md v6 §5 + ADR-0015 amended-by note") + ADR-0024 = Accepted IS the authorization (not the usual draft→active flip; same pattern as W17 D0); R1 satisfied once this plan.md is committed
spec_refs:
  - architecture.md v6 §5.0          # NEW Application Shell section (amended in at W18 kickoff per ADR-0024; this phase IMPLEMENTS it)
  - architecture.md v6 §5.2          # Chat — now rendered inside <AppShell>; path /chat (was /; ADR-0015 v6 move)
  - architecture.md v6 §5.3          # Dashboard — was "Admin Dashboard" placeholder /admin → real overview /dashboard (per ADR-0024)
  - architecture.md v6 §5.4-§5.7     # KB List / KB Detail / Eval Console / Traces — re-parented + re-routed (/admin/ prefix dropped, debug→traces)
  - architecture.md v6 §5.9          # V7 Landing — REMOVED (/ → redirect /login | /dashboard)
  - architecture.md v6 §5.10-§5.11   # Login / Register — redirect target → /dashboard (was /chat); pages stay OUTSIDE <AppShell>
  - ADR-0024                         # the architectural decision this phase implements (Accepted 2026-05-10) — D1-D10 deliverables map onto F1-F9 below
  - ADR-0015                         # amended by ADR-0024 — the W12-W15 9-view implementation being re-parented (not rebuilt); shadcn/ui foundation + EKP visual identity preserved
  - ADR-0014                         # hybrid auth model — the login-gate / /login entry interplay
  - ADR-0021                         # V4 Retrieval Testing tab + search-mode param — the KB-detail 5-tab content that moves into the shell unchanged
  - ADR-0022                         # auth-transport hardening (httpOnly cookie + CSRF; cookie OR Bearer dual-path) — the login-gate relies on this
prior_phase: W17-beta-hardening      # closed 2026-05-10 (phase Gate PASS); W16 F1-F4 still Track-A-blocked (parallel, not predecessor); W18 is independent of both per ADR-0024 Q5
related_artifacts:
  - docs/adr/0024-unified-application-shell-ia.md          # the ADR — D1-D10 map onto F1-F9 here
  - frontend/components/nav/admin-shell.tsx                # F1 — generalizes into app-shell.tsx (hamburger collapse + UserMenu + ThemeToggle + responsive reused)
  - frontend/components/nav/user-menu.tsx                  # F1 — UserMenu in the top bar; F5 — its menu links to /settings
  - frontend/app/admin/layout.tsx + eval/layout.tsx + debug/[traceId]/layout.tsx   # F2 — folded into app/(app)/layout.tsx
  - frontend/app/admin/page.tsx                            # F2 — removed (the old "Admin Dashboard" placeholder; role taken by /dashboard)
  - frontend/app/admin/kb/page.tsx + admin/kb/[id]/page.tsx + admin/kb/new/page.tsx + admin/kb/[id]/upload/page.tsx   # F3 — moved to (app)/kb/* (/admin/ dropped)
  - frontend/app/chat/page.tsx                             # F3 — moved to (app)/chat/page.tsx
  - frontend/app/eval/page.tsx                             # F3 — moved to (app)/eval/page.tsx
  - frontend/app/debug/[traceId]/page.tsx                 # F3 — moved to (app)/traces/[traceId]/page.tsx (debug→traces)
  - frontend/app/page.tsx                                  # F7 — V7 Landing markup deleted → thin redirect (/ → /login | /dashboard)
  - frontend/app/login/page.tsx + register/page.tsx       # F7 — success → router.push('/dashboard') (was '/chat'); F2 login-gate interplay
  - frontend/components/auth/brand-panel.tsx               # kept as-is (auth splash, NOT a marketing page) — no edit expected
  - frontend/app/layout.tsx (root)                         # F2 — keeps only <ThemeProvider> + <Toaster> (auth pages get no app chrome)
  - frontend/lib/auth + query-provider                     # F2 — AuthProvider + QueryProvider consolidated into (app)/layout.tsx; login-gate guard added at that boundary (or middleware.ts)
  - frontend/lib/theming/tokens.ts                         # F1 + F8 — 100% token consumption, no hardcoded colours ([oklch(...)]=0 milestone preserved)
  - frontend/tests/e2e/                                    # F3 + F8 — Playwright route refs updated + a "shell present on authed routes / absent on auth pages" assertion
  - frontend/tests/unit/                                   # F8 — Vitest tests for <AppShell> nav + <GlobalSearch> (W17 F6 scaffold)
  - frontend/next.config.mjs                               # F3 — verify no route-specific config breaks (the /api/backend rewrite is path-agnostic; double-check)
  - docs/02-architecture/COMPONENT_CATALOG.md              # F8/F9 — C09/C10 status note (AppShell IA; URL flatten; /dashboard)
  - docs/12-ai-assistant/01-prompts/01-session-start.md    # F9 — §3 C09/C10 status + §10 W18 row + §11 carry-overs + §12 milestones (closeout hygiene catch-up)
---

# Phase W18 — Unified Application Shell IA

> **Plan version**:1.0(draft 2026-05-10 — rolling JIT per CLAUDE.md §10 R1;kicked off at W17 closeout per the ADR-0024 acceptance cascade — Chris directed「開 W18-app-shell-ia phase folder + plan.md + amend architecture.md v6 §5 + ADR-0015 amended-by note」)
> **Owner**:Chris(Tech Lead + stakeholder)+ AI(implementation)
> **Approved by**:Chris — ADR-0024 = **Accepted** 2026-05-10(Q1-Q6 resolved;the「approved + write ADR」+「now implement it」authorization per CLAUDE.md §5.1 H1)。`architecture.md v6 §5` amendment (§5.0 Application Shell added / §5.3「Admin Dashboard」→「Dashboard」/ §5.9 Landing removed / §5.7「Debug View」→「Traces」/ `/admin/*` → `/kb/*` flatten — inline-tagged, doc version held) landed alongside this kickoff.

---

## 1. Scope

W18 = **the UI IA restructure phase per ADR-0024** — replace the ADR-0015 Dify-leaning 3-regime layout split (V7 marketing landing / chrome-less chat / `<AdminShell>` admin) with a **single unified `<AppShell>`** (top bar + collapsible left sidebar + main content) wrapping **all authenticated views**, plus a login-gate, flattened URLs (no `/admin/` prefix), a real `/dashboard` overview as the post-login home, a small `/settings` view, and a Tier-1-scoped global search (Cmd+K quick-jump). **This is a re-layout + re-route + 2-view-change + Landing-removal — NOT a rebuild**: the W12-W15 views' internal content (KB Detail's 5 tabs incl. ADR-0021 Retrieval Testing, Eval's metric cards, Traces' 9-stage timeline, the chat streaming + citations, the auth-page split layout) is untouched; they render inside the new shell. The shadcn/ui foundation + EKP-native visual identity (`tokens.ts`, Notion-leaning aesthetic, dark-mode inverted-button) are unchanged (ADR-0015 (c) + (d) stand).

Goals (= ADR-0024 D1-D10 mapped onto F1-F9):

- **`<AppShell>` component**(D1 → F1)— generalize `frontend/components/nav/admin-shell.tsx` into `app-shell.tsx`:collapsible left sidebar(5 modules:Dashboard / Chat / Knowledge Bases / Eval Console / Traces)+ top bar(app name → `/dashboard`, global search Cmd+K, language toggle [disabled — i18n Tier 2 §11], `<ThemeToggle>`, `<UserMenu>`)+ main content slot + responsive hamburger + focus-mode toggle;100% `tokens.ts`, no hardcoded colours.
- **`(app)/` route group + login-gate**(D2 + D7 → F2)— `app/(app)/layout.tsx` = `<AuthProvider><QueryProvider><AppShell>{children}</AppShell></QueryProvider></AuthProvider>` + a route guard(client guard at the `AuthProvider` boundary, or `middleware.ts`)→ unauthenticated → `/login`(mock-auth dev mode = no-redirect, documented);remove `app/admin/layout.tsx` / `app/eval/layout.tsx` / `app/debug/[traceId]/layout.tsx` / `app/admin/page.tsx`;root `app/layout.tsx` keeps only `<ThemeProvider>` + `<Toaster>`.
- **Move + re-route pages, flatten URLs**(D3 → F3)— move `chat`, `kb`(from `admin/kb` — `/admin/` prefix dropped), `kb/[id]`, `kb/new`, `kb/[id]/upload`, `eval`, `traces/[traceId]`(from `debug/[traceId]`)into `app/(app)/`;update **all** internal `<Link href>` + `router.push` + the Playwright `tests/e2e/` route references + verify `next.config.mjs` has no route-specific breakage.
- **`/dashboard` real overview**(D4 → F4)— NEW `app/(app)/dashboard/page.tsx`:cards grid — KB summary(count + total docs/chunks/storage off `GET /kb`)/ recent queries(or an「Ask something」CTA → `/chat`)/ latest eval status(R@5 / Faithfulness / Correctness off the last cached `POST /eval/run`)+ link → `/eval` / system health(Azure Search / Azure OpenAI / Cohere / Langfuse off `GET /health` + component statuses)/ quick actions(New KB / Upload / Run Eval / Open Chat). **No new backend** — all data from existing endpoints.
- **`/settings` small view**(D5 → F5)— NEW `app/(app)/settings/page.tsx`:profile display(display name / email / oid)+ sign-out + theme preference;`<UserMenu>` "Settings" links here.
- **Global search command palette**(D6 → F6)— NEW `frontend/components/nav/global-search.tsx`:Cmd/Ctrl+K — filter KB names + recent docs + recent traces + an「Ask in chat: …」action → `/chat?q=…`. **Tier 1 scope only**(no semantic search-as-you-type across chunks — that's a Tier 2 candidate).
- **login/register redirect + V7 Landing removal**(D8 → F7)— `app/login/page.tsx` + `app/register/page.tsx`:success → `router.push('/dashboard')`(was `/chat`);`app/page.tsx`:**delete the V7 Landing markup** → thin redirect(`/` → `/login`, or `/dashboard` if a session exists);keep `brand-panel.tsx`(auth splash).
- **responsive + a11y + tests + docs hygiene**(D9 + D10-residual → F8)— responsive + a11y pass on the new shell(sidebar `aria-current`, hamburger `aria-expanded`, command-palette `role="dialog"` + focus trap);dark-mode token consistency re-check(`[oklch(...)]`=0 milestone preserved);Vitest unit tests for `<AppShell>` nav + `<GlobalSearch>`;Playwright E2E updated for the new routes + a "shell present on authenticated routes / absent on auth pages" assertion;`COMPONENT_CATALOG.md` C09/C10 status note(`architecture.md v6 §5` already amended at kickoff;`session-start.md` hygiene done in F9 closeout).
- **Phase closeout**(F9)— Gate verdict + retro + frontmatter `closed` + `session-start.md` hygiene catch-up + W19+ rolling-JIT trigger(NOT pre-created).

**Out of W18 scope**(stay Tier 2 / W16 / future):
- Multi-language / i18n machinery — the top-bar language toggle is a **disabled affordance only**;translating the chrome and/or the RAG content stays Tier 2 per architecture.md v6 §11(CLAUDE.md §5.4 H4 — no Tier 2 leak)
- Semantic "search-as-you-type across all chunks" — global search is Tier 1 quick-jump scope only;the richer search is a Tier 2 candidate
- Track A IT cred items(Azure DELETE cleanup / ACS `pip install` / `.env.production` / Cohere Marketplace billing)— still W16 F1, unaffected by W18
- 25% Beta cohort rollout activation + daily metric monitor + Q15 weekly signal report — W16 F2-F3(Beta phase)
- Full NVDA/JAWS/VoiceOver screen-reader audit(Tier 2 — CO_W15_F3_aria_full_audit;W18 F8 = a11y spot-check + the new-shell-specific ARIA only)
- Deep `/settings`(notification prefs / API tokens / etc)— Tier 1 `/settings` = profile display + sign-out + theme preference;deeper settings are a polish detail
- Backend changes — `/dashboard` v1 consumes `/health` + `/kb` + last cached eval;no new endpoint;the W17-deferred 🚧 F1.5b / F3.5b runtime verifications stay under CO17 (R8 / Azure-key-bound, unrelated to W18)
- Reset password / 2FA / OAuth providers — Tier 2(per architecture.md v6 §11 + ADR-0014);the login-page "Forgot password?" stays a disabled affordance

**Pre-condition for W18 promotion**(satisfied 2026-05-10):
- ADR-0024 = **Accepted**(Q1-Q6 resolved;Chris directed the post-acceptance cascade)
- `architecture.md v6 §5` amendment landed at kickoff(inline-tagged per the §3.4/§3.7 precedent)
- ADR-0015 References get the amended-by note(landed at kickoff)
- W17-beta-hardening = closed(phase Gate PASS);W16 F1-F4 = Track-A-blocked(parallel track — W18 does not depend on either)

## 2. Deliverables(F1-F9)

### F1 — `<AppShell>` component(generalize `<AdminShell>`)(ADR-0024 D1)

- **Component(s)**:**C09** Admin Console UI + **C10** Chat Interface UI(the shell now wraps both)+ **C11** Identity & Access(`<UserMenu>` in the top bar)
- **Spec ref**:architecture.md v6 §5.0 Application Shell;ADR-0024 D1
- **OQ deps**:none(the language toggle is a known §11 Tier 2 disabled affordance — not a new OQ;Q10 visual identity unaffected — tokens.ts unchanged)
- **Acceptance criteria**:
  - F1.1 NEW `frontend/components/nav/app-shell.tsx` — extracted / generalized from `admin-shell.tsx`:`<AppShell>` = top bar + collapsible left sidebar + main content slot;props for the active route + nav items;reuses the existing hamburger-collapse + responsive logic
  - F1.2 Left sidebar — 5 module items(Dashboard `/dashboard` / Chat `/chat` / Knowledge Bases `/kb` / Eval Console `/eval` / Traces `/traces`)with active-route highlighting(`aria-current="page"`);a "focus mode" toggle that collapses the sidebar(persisted, e.g. localStorage or a context)— ChatGPT/Claude.ai pattern;flat list(sectioned headers are an optional polish detail — start flat)
  - F1.3 Top bar — app name/logo(left, link → `/dashboard`, no marketing tagline)+ global search trigger(centre — opens `<GlobalSearch>` F6;Cmd/Ctrl+K binding)+ language toggle(**disabled** affordance — tooltip "Multi-language coming soon";i18n Tier 2 §11)+ `<ThemeToggle>`(reuse existing)+ `<UserMenu>`(reuse existing — avatar + display name;menu: Profile / Settings → `/settings` / Sign out)
  - F1.4 Responsive — sidebar < `md` collapses to a hamburger drawer(reuse the `AdminShell` pattern);top bar stays;`aria-expanded` on the hamburger
  - F1.5 Tokens — 100% `tokens.ts` consumption;`Grep '\[oklch'` across `frontend/` stays **0**(milestone preserved);`tsc --noEmit` + `next lint` clean
  - F1.6 File header docstring per CLAUDE.md §3.2 / session-start §13 #8(NEW file)
- **Effort estimate**:1-1.5 days(W18 D1 — largest single component;the focus-mode + Cmd+K wiring is the new bit, the rest generalizes `AdminShell`)
- **Owner**:AI(implementation)+ user(visual review of the shell chrome)

### F2 — `(app)/` route group + consolidated providers + login-gate(ADR-0024 D2 + D7)

- **Component(s)**:**C09** + **C10** + **C11**(the auth boundary)
- **Spec ref**:architecture.md v6 §5.0(Login-gate + Routing paragraphs);ADR-0014(hybrid auth — the `/login` entry);ADR-0022(cookie/Bearer dual-path);ADR-0024 D2 + D7
- **OQ deps**:Q11(operational-Resolved unaffected — the login-gate just redirects to `/login`;real MSAL redirect handled by MSAL;mock-auth = no redirect)
- **Acceptance criteria**:
  - F2.1 NEW `frontend/app/(app)/layout.tsx` — `<AuthProvider><QueryProvider><AppShell>{children}</AppShell></QueryProvider></AuthProvider>`;this is the single shell-wrapping layout for all authenticated views
  - F2.2 Login-gate — a route guard at the `(app)/` `AuthProvider` boundary(or `middleware.ts`)→ unauthenticated user → redirect `/login`;**mock-auth dev mode**(`NEXT_PUBLIC_AUTH_MOCK=true` / `FEATURE_AUTH_MOCK=true`)= mock provider auto-authenticates → no redirect(documented in the layout's docstring);real MSAL = MSAL's own redirect flow
  - F2.3 Remove `frontend/app/admin/layout.tsx`、`frontend/app/eval/layout.tsx`、`frontend/app/debug/[traceId]/layout.tsx`(their providers + shell folded into `(app)/layout.tsx`);remove `frontend/app/admin/page.tsx`(the old "Admin Dashboard" placeholder — role taken by `/dashboard` F4)
  - F2.4 Root `frontend/app/layout.tsx` — keeps only `<ThemeProvider>` + `<Toaster>`(so the auth pages `/login` / `/register` / `/verify` get no app chrome);verify no `AuthProvider`/`QueryProvider` leaks to the root
  - F2.5 Auth pages(`/login` / `/register` / `/verify`)stay OUTSIDE `(app)/`(at `app/login/` etc) — unchanged structurally;F7 only touches their post-success redirect target
  - F2.6 Tests — `tsc --noEmit` + `next lint` clean;the existing Playwright `webServer` smoke(mock-auth)still works(no infinite redirect loop;the gate is a no-op in mock mode)
  - F2.7 File header docstring updates on the moved/new layout files
- **Effort estimate**:1 day(W18 D2)
- **Owner**:AI(implementation)+ user(confirm the login-gate behaviour is acceptable for the Beta domain)

### F3 — Move + re-route pages;flatten URLs(no `/admin/`;`debug`→`traces`);update all links + Playwright(ADR-0024 D3)

- **Component(s)**:**C09** + **C10**(all the view pages)+ cross-cutting(routing)
- **Spec ref**:architecture.md v6 §5.2-§5.7(the re-routed views)+ §5.0(flattened routing paragraph);ADR-0024 D3
- **OQ deps**:none
- **Acceptance criteria**:
  - F3.1 Move pages into `app/(app)/`:`chat/page.tsx`(from `app/chat/`)/ `kb/page.tsx`(from `app/admin/kb/`)/ `kb/[id]/page.tsx`(from `app/admin/kb/[id]/`)/ `kb/new/page.tsx`(from `app/admin/kb/new/`)/ `kb/[id]/upload/page.tsx`(from `app/admin/kb/[id]/upload/`)/ `eval/page.tsx`(from `app/eval/`)/ `traces/[traceId]/page.tsx`(from `app/debug/[traceId]/`)。The page **contents** are unchanged except internal route literals(see F3.2)
  - F3.2 Update **all** internal route references — `<Link href="/admin/kb/...">` → `href="/kb/..."`;`router.push('/admin/...')` → `router.push('/...')`;`/debug/[traceId]` → `/traces/[traceId]`;the in-page logo link removed from `chat/page.tsx`(now in the AppShell top bar — keeps the KB selector dropdown in the in-page header per §5.2 amendment note);grep `frontend/` for `'/admin` and `/debug/` to confirm none remain except deliberate historical/comment refs
  - F3.3 Update `frontend/tests/e2e/` — Playwright specs that navigate to `/admin/...` / `/debug/...` / `/`(landing)→ updated to `/kb/...` / `/traces/...` / `/dashboard`(or `/login` for the redirect test);snapshot baselines if any are route-named
  - F3.4 `frontend/next.config.mjs` — verify the `/api/backend/*` rewrite is path-agnostic(it is — it rewrites by prefix, not by app-route);confirm no other route-specific config breaks;no change expected, but verify
  - F3.5 Tests — `tsc --noEmit` + `next lint` clean;`pnpm test:unit` still passes(the W17 F6 sample test is component-level, route-agnostic);Playwright spec compile-check(running the full E2E needs `npx playwright install chromium` which is R8-blocked — CO_W15_F4_browser_binaries — so the E2E *update* is verified by `tsc` + the spec-file review;the actual run stays the user's pre-Beta smoke per the W12-W15 caveat)
- **Effort estimate**:1.5 days(W18 D3 — touches the most files;mechanical but wide;the grep-verify + Playwright update are the careful parts)
- **Owner**:AI(implementation)+ user(spot-check a few routes in the browser)

### F4 — `/dashboard` — the real post-login overview view(ADR-0024 D4)

- **Component(s)**:**C09** Admin Console UI(new view)+ consumes **C07** Observability(health)+ **C02/C03** KB(summary)+ **C06** Eval(latest run)
- **Spec ref**:architecture.md v6 §5.3 Dashboard;ADR-0024 D4
- **OQ deps**:none(Q6 real-query-collection still Open — the "recent queries" card shows whatever's available / a CTA if none;not blocking)
- **Acceptance criteria**:
  - F4.1 NEW `frontend/app/(app)/dashboard/page.tsx` — cards grid(clean internal-tool dashboard;**not** a router-to-chat)
  - F4.2 Cards — (a) **KB summary**(KB count + total documents / chunks / storage size — `useQuery` off `GET /kb` → aggregate);(b) **Recent queries**(if a recent-query source exists, list N;else an「Ask something」CTA → `/chat`);(c) **Latest eval status**(R@5 / Faithfulness / Correctness from the last cached `POST /eval/run` result if available — else "no eval run yet" + a "Run Eval" CTA;link → `/eval`);(d) **System health**(Azure AI Search / Azure OpenAI / Cohere / Langfuse — off `GET /health` + the component-status payload;up/down/degraded badges);(e) **Quick actions**(New KB → `/kb/new` / Upload Document → `/kb` / Run Eval → `/eval` / Open Chat → `/chat`)
  - F4.3 No new backend — `/health`, `/kb` are existing(W1/W2);the last `/eval/run` result is read from wherever it's cached(if nowhere, show the empty state — don't add backend caching in W18;a "Run Eval" CTA is the v1 fallback)
  - F4.4 Loading skeletons + error banners per card(reuse the W17 F4.1 Documents-tab pattern);empty states are first-class(brand-new install = empty everything → all CTAs)
  - F4.5 Tokens — 100% `tokens.ts`;`tsc` + `next lint` clean;`[oklch`=0 preserved;Vitest test for the dashboard card layout(at least a render smoke)— F8 carries the full test pass
  - F4.6 File header docstring(NEW file)
- **Effort estimate**:1 day(W18 D4)
- **Owner**:AI(implementation)+ user(visual review — this is the new "front door")

### F5 — `/settings` — small profile/preferences view(ADR-0024 D5)

- **Component(s)**:**C11** Identity & Access(profile display)+ **C09**(the view)
- **Spec ref**:architecture.md v6 §5.0(`<UserMenu>` → Settings → `/settings`);ADR-0024 D5
- **OQ deps**:none
- **Acceptance criteria**:
  - F5.1 NEW `frontend/app/(app)/settings/page.tsx` — profile display(display name / email / oid — read from the `AuthProvider` user context)+ sign-out button(reuse the `<UserMenu>` sign-out path)+ theme preference(Light / Dark / System — reuse `<ThemeToggle>` or a radio group bound to next-themes)
  - F5.2 `<UserMenu>` "Settings" menu item → `router.push('/settings')`(currently it may be a no-op or absent — wire it)
  - F5.3 Tokens / lint / `tsc` clean;`[oklch`=0 preserved;file header docstring(NEW file)
  - F5.4 Tier 1 scope guard — no notification prefs / API tokens / org settings(those are polish / Tier 2);`/settings` v1 = exactly the 3 things above
- **Effort estimate**:0.5 day(W18 D4 second half — small)
- **Owner**:AI(implementation)+ user(review)

### F6 — Global search command palette(`<GlobalSearch>` — Cmd/Ctrl+K)(ADR-0024 D6)

- **Component(s)**:**C09** Admin Console UI(top-bar component)+ consumes **C02** KB list + **C07** traces
- **Spec ref**:architecture.md v6 §5.0(Top bar — global search paragraph;**Tier 1 scope = quick-jump**);ADR-0024 D6
- **OQ deps**:none
- **Acceptance criteria**:
  - F6.1 NEW `frontend/components/nav/global-search.tsx` — a command-palette dialog(shadcn `Dialog` or a `cmdk`-style component built from existing shadcn primitives — no new dependency if avoidable;if `cmdk` is genuinely needed it's a small util lib but **stop-and-ask first** per H2)triggered by Cmd/Ctrl+K(global key handler)+ the top-bar search trigger
  - F6.2 **Tier 1 scope** — the palette filters:(a) KB names(off the cached `GET /kb` list)→ select → `/kb/[id]`;(b) recent documents(if available)→ `/kb/[id]`;(c) recent traces(if available)→ `/traces/[traceId]`;(d) an always-present「Ask in chat: "<query>"」action → `/chat?q=<encoded>`(the chat page reads `?q=` and pre-fills/sends — small `chat/page.tsx` tweak). **NOT in scope**:semantic search-as-you-type across all chunks(Tier 2 candidate)
  - F6.3 a11y — `role="dialog"` + `aria-modal` + focus trap + Escape-to-close + arrow-key navigation of results(`aria-activedescendant` or roving tabindex)
  - F6.4 Tokens / lint / `tsc` clean;`[oklch`=0 preserved;file header docstring(NEW file);Vitest test for the palette's filter logic + key binding(F8 carries the pass)
  - F6.5 If `?q=` chat pre-fill needs more than a trivial `chat/page.tsx` change, scope it to "navigate to `/chat` with the query in the URL; chat reads it on mount" — don't redesign the chat input
- **Effort estimate**:0.5-1 day(W18 D5 — the dialog + key handler + filter logic;`?q=` chat tweak is the small dependency)
- **Owner**:AI(implementation)+ user(review the quick-jump UX)

### F7 — login/register redirect → `/dashboard`;delete V7 Landing;`/` → redirect(ADR-0024 D8)

- **Component(s)**:**C09**(`app/page.tsx`)+ **C11**(`login`/`register` redirect)
- **Spec ref**:architecture.md v6 §5.9(Landing — REMOVED)+ §5.10/§5.11(Login/Register redirect target)+ §5.0(Login-gate `/` redirect);ADR-0024 D8
- **OQ deps**:none
- **Acceptance criteria**:
  - F7.1 `frontend/app/login/page.tsx` — on successful sign-in → `router.push('/dashboard')`(was `/chat`);same for the MSAL callback path if it has an explicit redirect
  - F7.2 `frontend/app/register/page.tsx` — Step 3 "Welcome" CTA / auto-advance → `/dashboard`(was `/chat`);the verify-email auto-login(ADR-0022)means Step 3 lands authenticated → `/dashboard` works
  - F7.3 `frontend/app/page.tsx` — **delete the V7 Landing markup**(the hero + 3 feature cards + "how it works" + footer);replace with a thin redirect:if a session exists → `redirect('/dashboard')`;else → `redirect('/login')`(server component `redirect()` from `next/navigation`, or a client-side check — pick the simplest that respects the auth state)
  - F7.4 Keep `frontend/components/auth/brand-panel.tsx`(it's the auth-page brand splash on `/login` / `/register` — NOT a marketing page);grep-verify nothing else imported the deleted Landing components(if a shared component was Landing-only, delete it too — it's W18's own mess per Karpathy §1.3;if it's shared, leave it)
  - F7.5 Tests — `tsc` + `next lint` clean;Playwright: a `/ → /login`(unauthenticated)or `/ → /dashboard`(authenticated)redirect assertion replaces the old "landing page renders" test;`[oklch`=0 preserved(deleting markup can't add hardcoded colours, but re-grep to be safe)
- **Effort estimate**:0.5 day(W18 D5 — small;the careful part is the orphan-check after deleting the Landing markup)
- **Owner**:AI(implementation)+ user(confirm the `/` redirect behaviour)

### F8 — responsive + a11y pass;Vitest + Playwright updates;dark-mode re-check;`COMPONENT_CATALOG.md` note(ADR-0024 D9 + D10-residual)

- **Component(s)**:cross-cutting(C09 + C10 + C11 + test harness + docs)
- **Spec ref**:architecture.md v6 §5.0 + §5.8(cross-view UX);ADR-0024 D9 + D10(D10's `architecture.md v6 §5` part already landed at kickoff — only the `COMPONENT_CATALOG.md` / `session-start.md` parts remain;`session-start.md` is in F9 closeout)
- **OQ deps**:F1-F7 baseline(so the verified state includes the W18 changes)
- **Acceptance criteria**:
  - F8.1 Responsive pass — the new `<AppShell>` at `sm` / `md` / `lg` / `xl`:sidebar collapses to hamburger drawer < `md`;top bar stays usable;the command palette is full-width on mobile;`/dashboard` cards reflow to 1-column on mobile;browser smoke at 2-3 viewports(reuse the W7 F5.4 / W15 F3 viewport-check approach)
  - F8.2 a11y pass on the **new** surfaces(W18's own mess only — full NVDA/JAWS/VoiceOver audit stays Tier 2 / CO_W15_F3_aria_full_audit):sidebar nav `aria-current="page"` on the active item;hamburger `aria-expanded`;`<GlobalSearch>` `role="dialog"` + `aria-modal` + focus trap + Escape;`/settings` form labels(`<Label htmlFor>`);`/dashboard` cards have headings(`<h2>`/`<h3>`)+ links have accessible names;the disabled language toggle has an `aria-disabled` + a tooltip explaining "Tier 2"
  - F8.3 Dark-mode re-check — `Grep '\[oklch'` across `frontend/` = **0**(milestone preserved through the restructure);browser smoke: dark-mode toggle on `/dashboard` + `/settings` + the shell chrome(top bar + sidebar)— `tokens.ts` `colorsDark` applied;the W17 F5 mechanism note still holds(next-themes `attribute="class"` → `.dark` vars → tailwind `oklch(var(--token))` → utility classes)
  - F8.4 Vitest unit tests — `<AppShell>` nav(renders 5 items / active-route highlight / focus-mode toggle collapses)+ `<GlobalSearch>`(Cmd+K opens / filter logic / "Ask in chat" action navigates);`pnpm test:unit` → all pass(adds to the W17 F6 baseline of 1 file / 3 tests)
  - F8.5 Playwright E2E — the `tests/e2e/` route updates from F3.3 + a NEW assertion: "the `<AppShell>` chrome(top bar + sidebar)is present on `/dashboard` / `/chat` / `/kb` / `/eval` / `/traces/...` and absent on `/login` / `/register`";`tsc` compile-check of the specs(full run = user's pre-Beta smoke per the R8 `npx playwright install chromium` block / CO_W15_F4_browser_binaries)
  - F8.6 `docs/02-architecture/COMPONENT_CATALOG.md` — C09(Admin Console UI)+ C10(Chat Interface UI)status note: now both render inside `<AppShell>`;URL flatten(`/admin/*` → `/kb/*`);`/dashboard` is the new post-login home;V7 Landing removed;`/settings` added — per ADR-0024(`architecture.md v6 §5` already carries the inline-tagged amendment;the catalog mirrors it)
- **Effort estimate**:1 day(W18 D6)
- **Owner**:AI(implementation + browser smoke)+ user(keyboard nav + responsive spot-check + the interactive 9-view-in-the-shell walkthrough — the pre-Beta smoke)

### F9 — Phase closeout + W19+ rolling-JIT trigger

- **Component(s)**:cross-cutting governance
- **Spec ref**:CLAUDE.md §10 R1 rolling-JIT + R5 closeout discipline
- **OQ deps**:F1-F8 verdict outcomes
- **Acceptance criteria**:
  - F9.1 W18 phase Gate verdict landed(PASS / PARTIAL PASS / FAIL with explicit rationale per the W12-W15-W17 pattern)
  - F9.2 W18 `progress.md` retro — 7 sections(What worked / What didn't & friction / Surprises / Decisions / Carry-overs to W19+ / Time tracking / Spec ref alignment)
  - F9.3 ADR-0024 status verified `Accepted`(landed at this phase's kickoff;verify-no-op)+ ADR-0024 "Implementation Deliverables" D1-D10 checkboxes ticked against the F1-F9 outcomes
  - F9.4 W18 `plan.md` + `checklist.md` + `progress.md` frontmatter `status: active` → `closed`
  - F9.5 W19+ phase folder **NOT pre-created**(rolling-JIT — kickoff post-W18-closeout decision;likely candidates = W16 F1-F4 if Track A IT cred lands / Tier 2 prep governance Q12 / a Beta-launch readiness pass / the user's local-dev seed-KB convenience task)
  - F9.6 `session-start.md` hygiene catch-up — §3 C09/C10 status(rendered inside `<AppShell>`;URL flatten;`/dashboard` post-login home;`/settings` added;V7 Landing removed)+ §10 W18 row added(closed, Gate verdict)+ W19+ not-pre-created + §11 carry-overs(W18-closed items + any new 🚧 deferrals)+ §12 milestones row + Last-Updated + Update-history;`COMPONENT_CATALOG.md` already touched in F8.6
  - F9.7 No new OQ expected(the multi-language affordance is a known §11 Tier 2 item, not a new OQ);if one surfaces → sync `decision-form.md` per R4
- **Effort estimate**:0.5 day(W18 D7 or absorbed)
- **Owner**:AI(draft)+ user(approve + sign-off)

---

## 3. Success Criteria(Phase Gate)

W18 phase Gate **PASS condition**:
1. F1 `<AppShell>` — top bar + collapsible sidebar(5 modules)+ main content;focus-mode toggle works;responsive hamburger;100% `tokens.ts`;`tsc`+`lint` clean
2. F2 `(app)/` route group — single shell-wrapping layout;login-gate redirects unauthenticated → `/login`(no-op in mock-auth dev, documented);old per-section layouts + `admin/page.tsx` removed;root layout chrome-free for auth pages;mock-auth Playwright `webServer` smoke still works
3. F3 routes — all pages moved into `(app)/`;`/admin/*` → `/kb/*`、`/debug/*` → `/traces/*`;every internal `<Link>`/`router.push` updated;Playwright route refs updated;`grep '/admin'` / `'/debug/'` in `frontend/` shows only deliberate refs
4. F4 `/dashboard` — real overview cards(KB summary / recent queries / latest eval / system health / quick actions);no new backend;empty states first-class
5. F5 `/settings` — profile display + sign-out + theme preference;`<UserMenu>` links here
6. F6 `<GlobalSearch>` — Cmd+K palette;Tier 1 quick-jump(KB names / recent docs / recent traces / "Ask in chat")
7. F7 login/register → `/dashboard`;V7 Landing markup deleted;`/` → redirect(`/login` | `/dashboard`);`brand-panel.tsx` kept
8. F8 responsive + a11y pass on the new shell;dark-mode `[oklch`=0 preserved;Vitest tests for `<AppShell>` + `<GlobalSearch>` pass;Playwright route updates + "shell present/absent" assertion;`COMPONENT_CATALOG.md` C09/C10 note
9. F9 closeout + `session-start.md` hygiene + W19+ rolling-JIT trigger

W18 phase Gate **PARTIAL PASS** acceptable per Karpathy §1.4:
- F6 `<GlobalSearch>` — if a clean `cmdk`-style palette proves heavy and a new dep is undesired(H2), a simpler shadcn-`Dialog`-based "quick switcher" with the same 4 result types is acceptable;the richer fuzzy-match stays a polish detail
- F8.5 Playwright — the full E2E *run* is blocked on `npx playwright install chromium`(R8 / CO_W15_F4_browser_binaries);"updated specs + `tsc` compile-check + spec review" is the W18 deliverable;the actual run stays the user's pre-Beta smoke(W12-W15 caveat)
- F4.2(b) Recent queries / F4.2(c) Latest eval — if no cached source exists, the empty-state CTA *is* the v1 deliverable(don't add backend caching in W18)
- a11y — spot-check on the new surfaces only;full screen-reader audit stays Tier 2(CO_W15_F3_aria_full_audit)

W18 phase Gate **FAIL condition**:
- Tier 2 leak — actually implementing i18n machinery(the language toggle must stay a disabled affordance);semantic search-as-you-type(global search stays quick-jump)
- A view's *content* got rebuilt instead of re-parented(KB Detail's 5 tabs / Eval's metric cards / Traces' 9-stage timeline / chat streaming+citations / auth-page split layout must be unchanged — re-route + re-layout only)
- The shadcn/ui foundation or `tokens.ts` visual identity changed(ADR-0015 (c)+(d) must stand;`[oklch`=0 must hold)
- mock-auth dev path broken(infinite redirect loop / Playwright `webServer` smoke fails)
- Backend changed(W18 is frontend-only;`/dashboard` consumes existing endpoints)
- `frontend tsc --noEmit` / `next lint` regression(must stay clean);`pnpm test:unit` regression

## 4. Risks(Phase-Specific)

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Route move breaks internal links / Playwright specs in non-obvious places | High | Medium | F3.2 grep-verify(`'/admin'` + `/debug/`)across `frontend/`;F3.3 explicit Playwright spec review;`tsc` catches broken imports;browser spot-check a few routes before closeout |
| `<GlobalSearch>` wants a new dep (`cmdk`) | Medium | Low | **Stop-and-ask first** per H2;the PARTIAL-PASS fallback = a shadcn-`Dialog`-based quick switcher(zero new dep)— functionally equivalent for Tier 1 quick-jump scope |
| Login-gate causes an infinite redirect loop in mock-auth dev | Low | High | The gate is a *no-op* when the mock provider auto-authenticates(it never reports "unauthenticated");explicitly test the mock path before closeout;Playwright `webServer` smoke is the canary |
| `npx playwright install chromium` still R8-blocked → can't run the updated E2E | High | Low | Known(CO_W15_F4_browser_binaries / ADR-0017);W18 deliverable = updated specs + `tsc` + spec review;the run stays the user's pre-Beta smoke(W12-W15 caveat — accepted) |
| `/dashboard` "latest eval" / "recent queries" have no cached source | Medium | Low | Empty-state CTA is the v1 deliverable;no backend caching added in W18(out of scope) |
| Scope balloon — F1 + F3 + F4 are each ~1-1.5 days | Medium | Medium | Strict per-deliverable acceptance criteria;F5/F6/F7 are small;PARTIAL-PASS allowances above;same-day/multi-day collapse acceptable per W12-W15 precedent but not forced;`end_date` frontmatter is a window |
| Deleting V7 Landing orphans a shared component | Low | Low | F7.4 grep-verify imports;if Landing-only → delete(own mess);if shared → leave;`brand-panel.tsx` is the known keeper |

## 5. Day-by-Day Breakdown(rough)

| Day | Date(tentative) | Focus |
|---|---|---|
| W18 D0 | 2026-05-10 | Kickoff — ADR-0024 → Accepted + README + ADR-0015 amended-by note + `architecture.md v6 §5` amendment(§5.0 added / §5.3 Dashboard / §5.9 Landing removed / §5.7 Traces / `/admin/*` flatten)+ this `plan.md` + `checklist.md` + `progress.md` created(`status: active`)|
| W18 D1 | 2026-05-11 | F1 — `<AppShell>` component(generalize `AdminShell`;sidebar 5 modules + focus-mode + top bar + Cmd+K trigger + responsive hamburger)|
| W18 D2 | 2026-05-12 | F2 — `app/(app)/layout.tsx` route group(`<AuthProvider><QueryProvider><AppShell>`)+ login-gate guard + remove old per-section layouts + `admin/page.tsx` + root-layout chrome cleanup |
| W18 D3 | 2026-05-13 | F3 — move + re-route all pages into `(app)/`;flatten `/admin/*` → `/kb/*`、`/debug/*` → `/traces/*`;update all `<Link>`/`router.push` + Playwright route refs;grep-verify;`tsc`+`lint` |
| W18 D4 | 2026-05-14 | F4 — `/dashboard` overview cards(KB summary / recent queries / latest eval / system health / quick actions);F5 — `/settings`(profile + sign-out + theme pref)|
| W18 D5 | 2026-05-15 | F6 — `<GlobalSearch>` Cmd+K palette(quick-jump 4 result types + `?q=` chat tweak);F7 — login/register → `/dashboard` + delete V7 Landing markup + `/` redirect + orphan-check |
| W18 D6 | 2026-05-16 | F8 — responsive + a11y pass on the new shell;dark-mode `[oklch`=0 re-check;Vitest tests(`<AppShell>` + `<GlobalSearch>`);Playwright route updates + "shell present/absent" assertion;`COMPONENT_CATALOG.md` C09/C10 note |
| W18 D7 | 2026-05-17 | F9 — closeout(Gate verdict + retro + ADR-0024 D1-D10 ticked + frontmatter `closed` + `session-start.md` hygiene + W19+ rolling-JIT trigger)|

**Day-by-day caveat**:dates tentative;real-calendar collapse is the W12-W15-W17 pattern(phase capacity has run far under the plan-day budget when momentum is clean). If overflow:F8/F9 absorb into a later day or W19+ D1. The `start_date`/`end_date` frontmatter is a window, not a commitment.

## 6. Dependencies on Prior Phase / Carry-overs Addressed

From session-start.md §11 + the W17 retro carry-overs — W18 directly addresses:
- **ADR-0024 implementation** — the whole phase(D1-D10 → F1-F9;the ADR was a W17-closeout-session decision, the implementation is W18 per Q5)
- **CO_W15_F3_dark_mode_visual_verify(remainder)** — F8.3 re-checks `[oklch`=0 through the restructure + dark-mode smoke on the new shell surfaces;the interactive 9-view walkthrough stays the user's pre-Beta smoke(W12-W15 caveat shape)
- **CO_W15_F4_interactive_flow_E2E(partial)** — F8.5 adds the "shell present/absent" Playwright assertion + updates the route refs;the full interactive register/login + KB upload + Pipeline wizard E2E run stays Tier 2(blocked on the browser-binary install — CO_W15_F4_browser_binaries / ADR-0017)
- Vitest coverage expansion(W17 F6 left it at 1 file / 3 tests)— F8.4 adds `<AppShell>` + `<GlobalSearch>` tests(still well short of "deep component coverage" which stays Tier 2 per `tests/unit/README.md`)

W18 does **NOT** address(stay W16 / Tier 2 / future):
- CO16 Track A IT cred populate event + R-B1 closure(W16 F1 — external dependency;W18 is frontend-only, unaffected)
- CO17 — 🚧 F1.5b(Postgres-path runtime smoke, `pip install psycopg` R8-blocked)+ 🚧 F3.5b(RAGAs live-verify, Azure-key-bound)+ `npx playwright install chromium`(CO_W15_F4_browser_binaries)— all under the "personal Azure dev tier / non-proxy env" umbrella;W18 doesn't touch them(F8.5's Playwright update is spec-level, not a run)
- CO19 25% Beta cohort rollout activation(W16 F2 — Beta phase)
- CO_F6a/b/c ACS email retry / BackgroundTasks / SPF-DKIM(Track A — W16 F1 / IT-side)
- CO_W15_F1_eval_set_v1 — `eval-set-v1.yaml` final still needs Chris's SME reference-answer labels per Q14(unrelated to W18)
- CO_W15_F3_aria_full_audit — full NVDA/JAWS/VoiceOver audit(Tier 2;W18 F8.2 = new-surface spot-check only)
- CO13 / AF3 code fix(ADR-0013 reserved)— unrelated to W18

## 7. Plan Changelog

| Date | Change | Reason | Approver |
|---|---|---|---|
| 2026-05-10 | Initial draft + `status: active` + W18 folder created(`plan.md` + `checklist.md` + `progress.md`)| Chris directive at the W17-closeout session:「開 W18-app-shell-ia phase folder + plan.md(per CLAUDE.md §10 R1)+ amend architecture.md v6 §5(刪 §5.9 Landing + 加 §5.x Application Shell / §5.x Dashboard + re-route §5.2-§5.7)+ ADR-0015 加「amended by ADR-0024」」— = the post-acceptance implementation authorization for ADR-0024(Accepted same session;Q1-Q6 resolved). `architecture.md v6 §5` amendment(§5.0 Application Shell added / §5.3「Admin Dashboard」→「Dashboard」/ §5.9 V7 Landing removed / §5.7「Debug View」→「Traces」/ `/admin/*` → `/kb/*` flatten — inline-tagged, doc version held per the §3.4/§3.7 precedent)+ ADR-0015 amended-by note + ADR-0024 → Accepted + ADR README update all landed at this kickoff. F1-F9 map onto ADR-0024 D1-D10(D10's `architecture.md v6 §5` part done at kickoff → the W18 doc-deliverable narrows to `COMPONENT_CATALOG.md` C09/C10 + `session-start.md` hygiene). | Chris(stakeholder + architecture decision owner)|
| 2026-05-11 (D2) | F2 — `(app)/` route group + login-gate landed(NEW `frontend/app/(app)/layout.tsx` = `<AuthProvider><QueryProvider><LoginGate><AppShell>{children}</AppShell></LoginGate></QueryProvider></AuthProvider>` + NEW `frontend/components/auth/login-gate.tsx`). F2 verdict = **PASS(F2.3 deferred into F3)**. **Deviation 1 / scope re-sequencing**:plan **F2.3**(remove `app/admin/layout.tsx`、`app/eval/layout.tsx`、`app/debug/[traceId]/layout.tsx`、`app/admin/page.tsx`)→ **deferred into F3**. Reason:that removal is physically inseparable from the F3.1 page move — those layouts currently supply `AuthProvider`+`QueryProvider`+shell to `app/admin/kb/*`、`app/eval/page.tsx`、`app/debug/[traceId]/page.tsx`;removing them before the pages move into `app/(app)/`(which supplies the same)would strand those pages → runtime crash. So the removals land atomically with the F3 move(Karpathy §1.4 "make it actually work" — don't break the app between commits). Tracked as 🚧 F2.3 in checklist.md, not dropped. **Deviation 2 / login-gate shape**:plan F2.2「route guard ... → redirect `/login`」→ implemented as a gate-screen(`<LoginGate>`)that, in mock-auth dev mode, is a **no-op pass-through**(AuthProvider auto-signs-in;the visible "未登入→/login" only appears in real MSAL/prod per ADR-0024), and in real MSAL mode shows a splash(spinner / error text)+ a `<Link href="/login">` rather than an auto-`redirect()` — matching the existing AuthProvider design that avoids an infinite loop if cred wiring is broken(not live until W16 Track A;`/login` is outside `(app)/` so a redirect would be safe, but the "msal-init-done-no-account" state isn't cleanly detectable from `status` alone — a `// TODO(W16)` flags the tightening). **Deviation 3 / no-op**:F2.4「root layout keeps only ThemeProvider + Toaster」was **already true**(since W13)— verified, no edit. The `(app)/layout.tsx` is **inert until F3**(no `page.tsx` under `app/(app)/` yet — Next.js tolerates a route group with only a layout). `tsc --noEmit` + `next lint` clean,`[oklch`=0,dev server `:3001` up(`/` HTTP 200). | Plan F2 acceptance criteria;Karpathy §1.4(make it actually work — atomic removals)+ §1.2(simplicity — gate-screen over a fragile init-timing redirect)| Chris |
| 2026-05-10 (D1) | F1 — `<AppShell>` component landed(NEW `frontend/components/nav/app-shell.tsx`). F1 verdict = **PASS**. **5 minor deviations**(all Karpathy §1.2 simplicity / scope-precision — see progress Day-1):(1) plan F1.1「props for the active route + nav items」→ `children`-only(`usePathname()` + `NAV_ITEMS` module const — a single-shell app needs no configurable nav);(2) plan F1.3「`<UserMenu>` menu: Profile / Settings → `/settings`」→ deferred to **F5.2**(`/settings` doesn't exist until F5;F1 reuses the existing `<UserMenu>` as-is — surfaced not silently dropped);(3) language toggle uses native `disabled` + `title`(not `aria-disabled` — a natively-disabled button is removed from the AT tab order, fine since multi-language doesn't exist Tier 1;F8.2 can revisit);(4) no top-bar breadcrumb(`<AdminShell>` had one;the §5.0 top-bar spec — app name + search + lang + theme + user — doesn't include one;deep-route wayfinding → in-page breadcrumb, a F3/F8 polish detail);(5) Cmd/Ctrl+K hint shows `Ctrl K`(Windows-primary team;the handler accepts `metaKey \|\| ctrlKey` either way). The global-search trigger + the Cmd/Ctrl+K listener are both wired now but `handleOpenSearch` is a `// TODO(W18 F6)` no-op stub — **F6 mounts `<GlobalSearch>` + fills the handler**. `<AppShell>` is **not yet consumed by any layout**(F2 wires it into `app/(app)/layout.tsx`)— component-only delivery at F1;`tsc --noEmit` + `next lint` clean,`[oklch`=0. | Plan F1 acceptance criteria;Karpathy §1.2 simplicity-first | Chris |

---

**Lifecycle reminder**:呢份 plan `status=active`(2026-05-10,per Chris directive + ADR-0024 Accepted)。重大 deviation 入第 7 節 changelog(per R3)。Next-phase folder(W19+)**唔會** pre-create(per CLAUDE.md §10 R1 rolling-JIT)。
