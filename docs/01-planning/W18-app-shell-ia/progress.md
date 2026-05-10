---
phase: W18-app-shell-ia
plan_ref: ./plan.md
checklist_ref: ./checklist.md
status: active
last_updated: 2026-05-11
---

# Phase W18 — Progress

> Daily log + decisions + commits + closing retro。每 commit 對應一個 Day-N entry mention(R2;`docs(planning):` / `docs(adr):` housekeeping commits exempt)。
> Plan deviation → `plan.md` §7 changelog（R3）。OQ resolved → `decision-form.md` + Day-N mention（R4）。

---

## Day 0 — Kickoff(2026-05-10)

### Trigger

W17-beta-hardening closeout local-dev-test session(2026-05-10). After the local backend(`:8000`)+ frontend(`:3001`)were brought up in mock-auth mode, the stakeholder evaluated the running platform and surfaced an IA-expectation gap — three points:
1. `http://localhost:3001/` looked like a public marketing webpage;the expectation = unauthenticated → `/login`,then into the platform(usually a dashboard main page).
2. After login(reached via direct URL nav), `/admin` was the landing;navigating thence to `/chat` showed *no* top bar / *no* left side menu — inconsistent chrome.
3. A normal internal platform should have a **unified** page shell — a consistent top bar / menu, a left sidebar / menu, and a right main-content area — across all views.

→ Drafted **ADR-0024**(unified application shell IA)as a Proposed proposal(`112ff20`). Chris then answered Q1-Q5 in the same session — Q1 remove the marketing landing(EKP 非對外)/ Q2 a real overview dashboard / Q3 sidebar = functional modules + top bar = global search·language·theme·profile / Q4 no "admin" → flatten URLs / Q5 its own W18 phase(different content from the prior planning)— and asked that Q6(the ADR-0015 relationship)be explained in the ADR before flipping. The revised ADR reflects Q1-Q5 + the Q6 "Relationship to ADR-0015" section.

This Day-0 entry = the next session's directive: **「開 W18-app-shell-ia phase folder + plan.md(per CLAUDE.md §10 R1)+ amend architecture.md v6 §5(刪 §5.9 Landing + 加 §5.x Application Shell / §5.x Dashboard + re-route §5.2-§5.7)+ ADR-0015 加「amended by ADR-0024」」** — = the post-acceptance implementation authorization for ADR-0024(H1 layout-philosophy change per CLAUDE.md §5.1).

### Kickoff cascade landed(`(this commit)`)

- **ADR-0024 → Accepted** — `docs/adr/0024-unified-application-shell-ia.md` Status「**Proposed**」→「**Accepted**」(Q1-Q6 resolved;Chris directed the post-acceptance cascade);`## Decision` header「proposed」→「accepted」;the Implementation-Deliverables note「folder not pre-created until Accepted」→「created on acceptance 2026-05-10」(F0.1)
- **ADR README** — `docs/adr/README.md` ADR-0024 row status「**Proposed**」→「Accepted」+ context cell updated;footnote「Proposed 2026-05-10」→「Accepted 2026-05-10」;the「Next NNNN」block's 0024 line updated(F0.2)
- **ADR-0015 amended-by note** — `docs/adr/0015-ui-tier-1-expansion-dify-leaning.md` Status line gets「**amended by ADR-0024 2026-05-10**」(3 ways:V7 Landing removed / per-view layout-regime split → single `<AppShell>` / V2「Admin Dashboard」→ real `/dashboard`;preserves V8/V9 auth pages + shadcn/ui foundation + EKP visual identity + W12-W15 impl)+ a References entry for ADR-0024(F0.3)
- **`architecture.md v6 §5` amendment**(inline-tagged, doc version held — same convention as the §3.4 ADR-0023 / §3.7 ADR-0022 tags;F0.4):
  - top-block §5 amendment note added(after the v5.1→v6「註」block)
  - **NEW §5.0 Application Shell** section inserted before §5.1 — the unified shell statement(top bar + collapsible left sidebar + main content;5 sidebar modules Dashboard/Chat/Knowledge Bases/Eval Console/Traces;top-bar contents incl. the disabled language toggle [i18n Tier 2 §11];login-gate;flattened `app/(app)/...` routing)
  - §5.2 Chat header `/`→`/chat` + an in-shell note(focus-mode toggle replaces the full-bleed chrome-less surface)
  - **§5.3「Admin Dashboard」→「Dashboard」** `/admin`→`/dashboard` + body rewritten as a real overview(KB summary / recent queries / latest eval / system health / quick actions)
  - §5.4 KB List `/admin/kb`→`/kb` + in-shell note;§5.5 KB Detail `/admin/kb/[id]`→`/kb/[id]` + in-shell note;§5.6 Eval Console in-shell note(route unchanged)
  - **§5.7「Debug View」→「Traces」** `/debug/[traceId]`→`/traces/[traceId]` + the rename rationale note(operations-facing;9 stages unchanged)
  - **§5.9 V7 Landing → REMOVED tombstone**(EKP internal-only;`/`→redirect `/login`｜`/dashboard`;view-count: out goes Landing, in comes Dashboard;`brand-panel.tsx` kept)
  - §5.10 Login + §5.11 Register redirect target `/chat`→`/dashboard` + "stays outside `<AppShell>`" notes
- **W18 phase folder** — `docs/01-planning/W18-app-shell-ia/{plan,checklist,progress}.md` created;`status: active`(per the Chris directive — not the usual draft→active flip;the directive + ADR-0024 Accepted IS the authorization, same pattern as W17 D0). Plan §2 deliverables F0-F9 = ADR-0024 D1-D10 mapped(F1=D1 / F2=D2+D7 / F3=D3 / F4=D4 / F5=D5 / F6=D6 / F7=D8 / F8=D9+D10-residual / F9=closeout)— D10's `architecture.md v6 §5` part landed at this kickoff → the W18 doc-deliverable narrows to `COMPONENT_CATALOG.md` C09/C10(F8.6)+ `session-start.md` hygiene(F9.6)(F0.5)

### Pre-kickoff state notes(grounding the plan)

- `frontend/components/nav/admin-shell.tsx` already does the hamburger-collapse + responsive + `<UserMenu>` + `<ThemeToggle>` layout — `<AppShell>` generalizes it rather than building from scratch(ADR-0024 D1 / F1).
- The W12-W15 views' *content* is the keeper — KB Detail's 5 tabs(incl. ADR-0021 Retrieval Testing + the `mode` param), Eval's metric cards, the(soon-to-be)Traces 9-stage timeline, the chat streaming + citations, the auth-page split layout — W18 re-parents + re-routes, does NOT rebuild(ADR-0015 (c)+(d) stand;Karpathy §1.3).
- The `/api/backend/*` Next.js rewrite(`next.config.mjs`)is prefix-based, not app-route-specific — the route restructure(`/admin/*` → `/kb/*` etc)doesn't touch it(verify in F3.4 anyway).
- `npx playwright install chromium` is **R8-corp-proxy-blocked**(ECONNRESET — CO_W15_F4_browser_binaries / ADR-0017)— so F8.5's Playwright deliverable = updated specs + `tsc` compile-check + spec review;the actual E2E run stays the user's pre-Beta smoke(the W12-W15 "smoke-user-deferred" caveat shape).
- `pnpm test:unit` baseline = 1 file / 3 tests(W17 F6 scaffold)— F8.4 adds `<AppShell>` + `<GlobalSearch>` tests on top.
- Backend is **untouched** — `/dashboard` v1 consumes existing `/health` + `/kb` + the last cached `/eval/run`;no new endpoint;the W17-deferred 🚧 F1.5b / F3.5b runtime checks stay under CO17, unrelated to W18.

### Carry-overs addressed by W18(from session-start.md §11 + W17 retro)

| Carry-over | W18 deliverable |
|---|---|
| ADR-0024 implementation(the whole IA restructure)| F1-F9(= ADR-0024 D1-D10)|
| CO_W15_F3_dark_mode_visual_verify(remainder — interactive 9-view walkthrough)| F8.3 re-checks `[oklch`=0 through the restructure + dark-mode smoke on the new shell surfaces;the interactive walkthrough stays the user's pre-Beta smoke |
| CO_W15_F4_interactive_flow_E2E(partial)| F8.5 — "shell present/absent" Playwright assertion + route-ref updates;full interactive E2E run stays Tier 2(blocked on the browser-binary install)|
| Vitest coverage expansion(W17 F6 left it at 1/3)| F8.4 — `<AppShell>` + `<GlobalSearch>` tests(still short of "deep component coverage" = Tier 2)|

W18 does **NOT** address(stay W16 / Tier 2 / future): CO16 Track A IT cred + R-B1(W16 F1 — W18 is frontend-only);CO17 🚧 F1.5b / F3.5b / `npx playwright install chromium`(personal-Azure-dev-tier umbrella);CO19 25% rollout(W16 F2);CO_F6a/b/c ACS email(Track A);CO_W15_F1_eval_set_v1(needs Chris SME labels per Q14);CO_W15_F3_aria_full_audit(Tier 2 full screen-reader audit);CO13/AF3(ADR-0013 reserved).

### Actual vs Planned Effort(running — fill per day)

| Deliverable | Planned | Actual | Variance / note |
|---|---|---|---|
| F0 Kickoff cascade | (D0, ~0.5d) | (this session) | ADR-0024→Accepted + README + ADR-0015 note + `architecture.md v6 §5` amendment(§5.0 added / §5.3 Dashboard / §5.9 Landing removed / §5.7 Traces / `/admin/*` flatten)+ W18 folder(plan/checklist/progress) — `(this commit)` |
| F1 `<AppShell>` | 1-1.5d | ~0.4d(this session) | NEW `components/nav/app-shell.tsx` — generalized from `admin-shell.tsx`;`tsc --noEmit` + `next lint` clean;`[oklch`=0;not yet wired into a layout (that's F2) — `(this commit)` |
| F2 `(app)/` route group + login-gate | 1d | ~0.3d(this session) | NEW `app/(app)/layout.tsx` + `components/auth/login-gate.tsx`;root layout already chrome-free(verify-no-op);**F2.3 layout-removal deferred into F3**(inseparable from the page move);`tsc`+`lint` clean,`[oklch`=0,dev server up — `(this commit)` |
| F3 move + re-route + links + Playwright | 1.5d | — | — |
| F4 `/dashboard` | 1d | — | — |
| F5 `/settings` | 0.5d | — | — |
| F6 `<GlobalSearch>` | 0.5-1d | — | — |
| F7 login/register → /dashboard + delete Landing | 0.5d | — | — |
| F8 responsive/a11y + tests + dark-recheck + catalog | 1d | — | — |
| F9 closeout | 0.5d | — | — |

---

## Day 1 — F1 — `<AppShell>` component(2026-05-10)

### Built — `frontend/components/nav/app-shell.tsx`(NEW)— `(this commit)`

`<AppShell>` = the single chrome that will wrap **all authenticated views**(Dashboard / Chat / Knowledge Bases / Eval / Traces)— **top bar + collapsible left sidebar + main content slot**(per architecture.md v6 §5.0 / ADR-0024 D1). Generalized from the W12-W15 `<AdminShell>`(reuses its hamburger-collapse pattern + `<UserMenu>` + `<ThemeToggle>` + the token-class layout) rather than built from scratch.

- **Top bar**(`<header sticky top-0 z-30 h-14>`):mobile hamburger(`md:hidden`, opens the off-canvas sidebar, `aria-expanded`)→ desktop focus-mode toggle(`PanelLeftClose`/`PanelLeftOpen`, `aria-pressed`, `aria-label` switches Collapse/Expand)→ **app name "EKP" → `/dashboard`**(no marketing tagline)→ **global-search trigger**(centred search-box-styled `<button>` with a `Ctrl K` `kbd` hint;`aria-label="Search (Ctrl+K)"`)→ right cluster:**disabled language toggle**(`<Languages>` icon, native `disabled` + `title="Multi-language (JP / ZH) — coming in a later tier"` — i18n stays Tier 2 per §11 / CLAUDE.md §5.4 H4)+ `<ThemeToggle>`(reused)+ `<UserMenu>`(reused).
- **Cmd/Ctrl+K** — a `window` keydown listener(`(metaKey||ctrlKey) && key==='k'` → `preventDefault` → `handleOpenSearch()`);`handleOpenSearch` is a **no-op stub with a `// TODO(W18 F6)`** — W18 F6 mounts the real `<GlobalSearch>` palette here and fills the handler. The trigger button + the key binding are both wired now so F6 only supplies the implementation behind one callback.
- **Left sidebar** — 5 flat module items(`/dashboard` `LayoutDashboard` / `/chat` `MessageSquare` / `/kb` `Database` / `/eval` `FlaskConical` / `/traces` `Activity`)via a `NavLinks` sub-component;active route via `usePathname()` + `isActiveRoute(pathname, href)`(exact or `startsWith(href + '/')`)→ `aria-current="page"` + the muted-bg highlight;`<nav aria-label="Primary">`. Desktop:`<aside sticky top-14 h-[calc(100dvh-3.5rem)] overflow-y-auto w-56 md:block>` — **hidden entirely when focus-mode (`collapsed`) is on**. Mobile:rendered inside a controlled shadcn `<Sheet side="left">`(opened by the top-bar hamburger;each `NavLinks` item gets an `onNavigate` that closes the sheet).
- **Focus mode** — `const [collapsed, setCollapsed] = useState(false)`(SSR-stable default)+ a mount-time `useEffect` that reads `localStorage['ekp-sidebar-collapsed']`;`toggleCollapsed` writes it back. Collapsed = the desktop sidebar is not rendered → main goes full-width;the top-bar toggle(always present on desktop)brings it back.
- **Main content** — `<main className="min-w-0 flex-1 overflow-x-hidden p-4 md:p-8">{children}</main>`.
- **Tokens** — 100% token classes(`border-border` / `bg-background` / `bg-muted/40` / `bg-muted` / `text-muted-foreground` / `text-foreground`);**no hardcoded `oklch()`** — `Grep '\[oklch'` across `frontend/` = **0**(W15 milestone preserved). File header docstring per CLAUDE.md §3.2 / session-start §13 #8.

### Verification

- `pnpm exec tsc --noEmit` → exit 0(clean)
- `pnpm exec next lint` → "No ESLint warnings or errors"
- `Grep '\[oklch'` across `frontend/` → **0**(one accidental occurrence in the F1 docstring — "[oklch(...)]=0 milestone" — was reworded to "no hardcoded `oklch()` colour arbitrary-values" before commit)
- **Not browser-tested at F1** — `<AppShell>` is not yet imported by any layout(F2 wires it into `app/(app)/layout.tsx`);`tsc` proves it compiles in isolation;the visual / interactive smoke comes with F2-F3. The existing `next dev` server on `:3001`(left running from a prior session)is unaffected — nothing imports `app-shell.tsx` yet so it isn't compiled by the dev server.

### Deviations from plan(minor — Karpathy §1.2 simplicity)

1. **F1.1「props for the active route + nav items」→ `children`-only.** `usePathname()` supplies the active route(same as `AdminShell`)and `NAV_ITEMS` is a module-level const — a single-shell app doesn't need configurable nav. No `<AppShell>` props beyond `children`.
2. **F1.3「`<UserMenu>` menu: Profile / Settings → `/settings`」not added in F1.** F1 *reuses* the existing `<UserMenu>`(which has display name + `[mock]` badge + Sign out). Adding the "Settings → `/settings`" item is **W18 F5.2's job**(`/settings` doesn't exist until F5)— surfacing it here, not silently dropping it.
3. **Language toggle a11y** — used native `disabled` + `title`(rather than `aria-disabled` + a click-interceptor). Rationale:a natively-`disabled` button is removed from the AT tab order, which is fine — multi-language genuinely doesn't exist in Tier 1;the "coming soon" affordance is for sighted users(`title` tooltip). F8.2 can revisit if a visible-but-announced "Tier 2" hint is wanted.
4. **No breadcrumb in the top bar.** `<AdminShell>` had an auto-derived breadcrumb in its desktop header;the architecture.md §5.0 top-bar spec(app name + search + lang + theme + user)doesn't include one, so `<AppShell>` omits it. If deep-route wayfinding(`/kb/[id]`)wants it back, that's an in-page breadcrumb on those pages — a W18 F3 / F8 polish detail, not a shell concern.
5. **Cmd/Ctrl+K hint shows `Ctrl K`**(not `⌘K`)— the team is Windows-primary;the keydown handler accepts `metaKey || ctrlKey` either way so Mac still works.

### Next

- F2 — `app/(app)/layout.tsx` route group(`<AuthProvider><QueryProvider><AppShell>{children}</AppShell></QueryProvider></AuthProvider>`)+ login-gate guard + remove `app/admin/layout.tsx` / `eval/layout.tsx` / `debug/[traceId]/layout.tsx` / `admin/page.tsx` + root-layout chrome cleanup — wait for the user's go-ahead(directive pattern: explicit per-step).

---

## Day 2 — F2 — `(app)/` route group + login-gate(2026-05-11)

### Built — `(this commit)`

- **NEW `frontend/app/(app)/layout.tsx`**(server component)— the single layout for all authenticated views:`<AuthProvider><QueryProvider><LoginGate><AppShell>{children}</AppShell></LoginGate></QueryProvider></AuthProvider>`. Folds in what the three W12-W15 per-section layouts(`app/admin/layout.tsx`、`app/eval/layout.tsx`、`app/debug/layout.tsx`)did(AuthProvider + QueryProvider + a shell). File header docstring per §3.2. **Inert until F3** — `app/(app)/` has no `page.tsx` yet, so no URL matches it;F3 moves `chat`/`kb`/`eval`/`traces` in(+ F4/F5 add `dashboard`/`settings`).
- **NEW `frontend/components/auth/login-gate.tsx`**(`'use client'`)— wraps `<AppShell>` inside the `(app)/` layout. Reads `useAuthStatus()` + `authMode` from `auth-provider`(the auth state lives in the Zustand `useAuthStore`, not React context — so `<LoginGate>` works wherever it's nested):
  - **mock-auth dev mode**(`NEXT_PUBLIC_AUTH_MOCK` / `FEATURE_AUTH_MOCK`)→ `return <>{children}</>` immediately. `AuthProvider` auto-signs-in on mount,so the gate never gates;the visible "未登入 → /login" only appears in real MSAL / production builds(per ADR-0024 §"the mock-auth caveat"). This is what the dev `:3001` server runs.
  - **real MSAL**:`status === 'authenticated'` → children;else → a minimal centred splash(`Loader2` spinner,or the error text when `status === 'error'`)+ a `<Link href="/login">Sign in to continue</Link>`. **No auto-redirect** — matching the existing `AuthProvider` design(comment: "no auto-redirect to Entra ID hosted login — user must click sign-in CTA so we never get into an infinite loop on startup if cred wiring is broken"). `/login` is **outside** `app/(app)/` so it's not behind this gate(no loop). A `// TODO(W16)` notes:tighten to `router.replace('/login')` on the definitively-unauthenticated state once Q11 Track A cred wiring is live.
- **Root `frontend/app/layout.tsx`** — checked:**already** only `<html>`/`<body>` + `<ThemeProvider attribute="class" defaultTheme="system" enableSystem disableTransitionOnChange>` + `<Toaster>` + metadata + `globals.css`. No `AuthProvider`/`QueryProvider` leak to root. F2.4 = verify-no-op,no edit.

### Verification

- `pnpm -C frontend exec tsc --noEmit` → exit 0(clean)
- `pnpm -C frontend exec next lint` → "No ESLint warnings or errors"
- `Grep '\[oklch'` across `frontend/` → **0**(milestone preserved)
- Dev server on `:3001`(left running from a prior session)→ `GET /` HTTP 200(the V7 Landing — still present until F7). The new `app/(app)/layout.tsx` being inert(no pages)didn't break any existing route;Next.js tolerates a route group with only a `layout.tsx`(it matches no URL,so it's just unused — F3 makes it live).
- **Not browser-tested at F2** — `app/(app)/layout.tsx` matches no URL until F3 moves the pages in;`tsc` proves the import chain(`AuthProvider`/`QueryProvider`/`LoginGate`/`AppShell`)compiles;the visual / interactive smoke of the shell comes with F3. Playwright `webServer` mock-auth smoke = the server is booted-and-serving;the full E2E run stays the user's pre-Beta smoke per the R8 `npx playwright install chromium` block(CO_W15_F4_browser_binaries).

### Deviations from plan(R3)

1. **F2.3(remove the old per-section layouts + `app/admin/page.tsx`)→ deferred into F3.** Reason:that removal is **physically inseparable** from the F3.1 page move — `app/admin/kb/*`、`app/eval/page.tsx`、`app/debug/[traceId]/page.tsx` currently get their `AuthProvider`+`QueryProvider`+shell from those layouts;removing the layouts before the pages move into `app/(app)/`(which provides the same)would strand them → runtime crash(`useQuery` with no `QueryProvider`,etc). And `app/admin/page.tsx`'s role is taken by `/dashboard`(F4). So the removals land atomically with the F3 move(Karpathy §1.4 "make it actually work" — don't break the app between commits). Tracked in `checklist.md` as 🚧 F2.3, not dropped.
2. **F2.2「route guard ... → redirect `/login`」→ a gate-screen with a sign-in link, not an auto-`redirect()`.** Rationale:the existing `AuthProvider` deliberately avoids auto-redirects in MSAL mode(infinite-loop risk if cred wiring is broken — and it isn't live until W16 Track A);a "Sign in to continue" splash with a `<Link>` is functionally equivalent + safer for Tier 1. The `// TODO(W16)` flags the tightening. In mock mode(what dev uses)it's a no-op either way.
3. **F2.4 was already done** — root `app/layout.tsx` has been chrome-free(ThemeProvider + Toaster only)since W13;"keeps only ..." is satisfied as-is. No edit;noted so it's not mistaken for skipped work.

### Next

- F3 — move + re-route the page tree into `app/(app)/`(`chat` ← `app/chat/`;`kb` ← `app/admin/kb/`,`/admin/` prefix dropped;`kb/[id]`、`kb/new`、`kb/[id]/upload`;`eval` ← `app/eval/`;`traces/[traceId]` ← `app/debug/[traceId]/`)+ **the F2.3 removals**(`app/admin/layout.tsx`、`eval/layout.tsx`、`debug/[traceId]/layout.tsx`、`app/admin/page.tsx`)+ update all internal `<Link>`/`router.push` + the Playwright `tests/e2e/` route refs + `next.config.mjs` check + grep-verify `'/admin'`/`/debug/` only-deliberate-refs-remain — wait for the user's go-ahead(directive pattern: explicit per-step). **After F3 the shell becomes browser-visible** — F3 is when the IA actually flips.

---

**Lifecycle reminder**:Phase 收尾寫 Retro（What worked / What didn't & friction / Surprises / Decisions / Carry-overs to W19+ / Time tracking / Spec ref alignment）。W19+ phase folder **唔會** pre-create（rolling-JIT per CLAUDE.md §10 R1）。
