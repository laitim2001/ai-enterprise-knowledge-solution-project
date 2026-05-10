# ADR-0024: Unified application shell IA — `<AppShell>` (top bar + left sidebar + main content) across all authenticated views; no public marketing landing; no "admin" framing; login → `/dashboard`

**Date**: 2026-05-10
**Status**: **Proposed** — Q1–Q5 answered by Chris 2026-05-10 (this revision reflects them); Q6 = the ADR-0015 relationship, explained in detail below; moves to **Accepted** on Chris's confirmation of this revised ADR. H1 layout-philosophy change per CLAUDE.md §5.1; **amends ADR-0015**.
**Approver**: Chris

---

## Context

### Trigger

W17-beta-hardening closeout local-dev-test session (2026-05-10) — after the local backend + frontend were brought up, the stakeholder evaluated the running platform and surfaced an IA (information architecture) expectation gap:

> 為什麼 `http://localhost:3001/` 會像一個公開的網頁風格 — 預期效果應該是未登入先導向 `/login`,登入後進入平台,通常是 dashboard main 頁。而現在登入後導到 `/admin` 頁,再導向 `/chat` 頁時,top bar / 左 side menu 都冇 — 正常平台應該係統一的頁面風格:統一 top bar / menu,左 sidebar / menu,右邊 main content 區域。

And, on the design options:
> 1. 不要 marketing landing page,因為這項目不是對外推銷的 · 2. 真 overview dashboard · 3. 把本項目所包含的功能模組都放到左 sidebar menu,top bar 為全域搜查 / 多語言轉換 / 光暗度轉換 / 用戶 profile·setting · 4. 不需要 admin · 5. 獨立一個 W18 去處理(和之前規劃不一樣的內容)

### Current IA (per architecture.md v6 §5 + ADR-0015 — 9-view, Dify-leaning)

Three distinct layout regimes:

| Route(s) | View | Layout regime | Auth gating |
|---|---|---|---|
| `/` | V7 Landing | **No shell** — public marketing (server component, no `AuthProvider`, no client state); CTA "Start asking" → `/login` | none (public) |
| `/login`, `/register`, `/verify` | V8 / V9 | **BrandPanel split** — left brand panel + right form; no app chrome | none (public) |
| `/chat` | V1 Chat | **Root layout only** (`app/layout.tsx` = `<ThemeProvider>` + `<Toaster>`) — no top bar, no sidebar; a clean full-bleed conversation surface (Dify-chat-leaning) | none (no `AuthProvider` wrapper) |
| `/admin`, `/admin/kb`, `/admin/kb/[id]`, `/admin/kb/[id]/upload`, `/admin/kb/new` | V2 Admin Dashboard / V3 KB List / V4 KB Detail | **`<AdminShell>`** (`app/admin/layout.tsx` wraps `<AuthProvider><QueryProvider><AdminShell>`) — left sidebar (Overview / Knowledge Bases / Eval Console), top bar (theme toggle + `<UserMenu>`), responsive hamburger collapse | `AuthProvider` (mock auto-authenticates in dev; MSAL handles redirect in prod) |
| `/eval` | V5 Eval Console | own `app/eval/layout.tsx` (AdminShell-equivalent) | `AuthProvider` |
| `/debug/[traceId]` | V6 Debug View | own `app/debug/layout.tsx` (AdminShell-equivalent) | `AuthProvider` |

This split is **intentional per ADR-0015** ("Dify-leaning aesthetic … layout 1:1 mirror Dify Image 1-6 patterns") — Dify keeps its chat view as a minimal conversation surface separate from the dataset/admin chrome, and Dify's `/` is an outward-facing marketing site. `login → /chat` (per `app/login/page.tsx` `router.push('/chat')`) — not `/admin`; the stakeholder seeing `/admin` was a direct URL navigation (in mock-auth mode every route is reachable since the mock provider auto-authenticates with no redirect).

### Why this is H1

CLAUDE.md §5.1 H1 lists "改 8/9 個視 view 的其中任何一個的 layout philosophy（可以 polish，但唔可以 redesign）" as an architectural change. Moving from a 3-regime split to a single unified application shell — and removing one view (Landing) + adding one (Dashboard) — is a layout-philosophy redesign affecting all authenticated views → STOP-and-ask + ADR. This ADR is that proposal.

### The mock-auth caveat (orthogonal to the IA decision)

In dev `FEATURE_AUTH_MOCK=true` / `NEXT_PUBLIC_AUTH_MOCK=true` mode, the frontend mock provider auto-authenticates the dev-user with no actual login flow, so there is no enforced redirect-to-login locally regardless of any route guard. Additionally `/chat` currently has **no `AuthProvider` wrapper at all** (it uses only the root layout) — so it is not auth-gated even in principle today. Both are addressed by this proposal's login-gate + shared `(app)/` layout, but the *visible* "未登入 → /login" behaviour will only appear in real MSAL / production builds, not in mock-auth dev.

### Tier 1 / Tier 2 boundary note (multi-language)

`architecture.md §11` lists **"Multi-language (JP / ZH)" as a Tier 2 feature**. This ADR's top bar includes a language toggle *affordance* (per the stakeholder's request), but the actual internationalization implementation — translating the UI chrome and/or the RAG content — stays **Tier 2**. In Tier 1 the toggle is a present-but-disabled / "coming soon" control (same pattern as the login page's disabled "Forgot password?" — ADR-0014). Building i18n machinery in Tier 1 would violate CLAUDE.md §5.4 H4 (no Tier 2 leak); this ADR explicitly does not.

---

## Decision (proposed; reflects Chris's Q1–Q5 answers 2026-05-10)

Adopt a **unified application shell IA**: a single `<AppShell>` chrome — persistent top bar + collapsible left sidebar + right main content — wrapping **all authenticated views**; a login-gate; `login → /dashboard` (a new real overview view); **no public marketing landing** (`/` redirects to `/login`, or `/dashboard` if already authenticated); **no "admin" framing** (the URLs flatten — no `/admin/` prefix; the platform is one thing, not "user area + admin area"). The public auth pages (`/login`, `/register`, `/verify`) stay outside the shell.

### 1. `<AppShell>` component (generalize `<AdminShell>`)

Extract / generalize the existing `frontend/components/nav/admin-shell.tsx` into `frontend/components/nav/app-shell.tsx`:

- **Left sidebar** (per Chris Q3 — "把本項目所包含的功能模組都放到左 sidebar menu") — the platform's functional modules, collapsible (a "focus mode" toggle hides it for chat-immersive use, ChatGPT / Claude.ai pattern). Proposed items (active route highlighted):
  - **Dashboard** (`/dashboard`) — the overview / home
  - **Chat** (`/chat`) — the RAG query interface
  - **Knowledge Bases** (`/kb`) — KB list → detail (the 5-tab detail: Documents / Chunks / Pipeline / Retrieval Testing / Settings — ADR-0021)
  - **Eval Console** (`/eval`) — RAGAs 4-metric runs + reranker shootout
  - **Traces** (`/traces`, formerly "Debug View" `/debug/[traceId]`) — Langfuse trace inspection / per-query 6-stage timeline (rename "Debug" → "Traces" — more accurate for an operations-facing module; or keep "Debug" — minor, Chris-to-confirm)
  - *(grouping into sections is optional — a flat list of 5 modules may read cleaner than headers for so few items; final structure is a polish detail for the W18 phase, not a blocking decision)*
- **Top bar** (per Chris Q3 — "top bar 通常是全域搜查,多語言轉換,光暗度轉換,用戶 profile / setting"):
  - **App name / logo** (left) — link → `/dashboard`. *(no "EKP marketing" tagline — internal tool)*
  - **Global search** (centre) — a command-palette-style input (Cmd/Ctrl+K). **Tier 1 scope**: quick-jump — filter KB names, recent documents, recent traces; an "Ask in chat" action that routes the query to `/chat`. *(Richer "semantic search-as-you-type across all chunks" is a Tier 2 candidate, not Tier 1 — keep it lightweight.)*
  - **Language toggle** — present-but-disabled affordance (i18n is Tier 2 per §11 — see the boundary note above)
  - **Theme toggle** (`<ThemeToggle>` — Light / Dark / System, already built)
  - **User profile / settings** (`<UserMenu>` — avatar + display name; menu: Profile, Settings, Sign out). *(A dedicated `/settings` page is a small new view — Tier 1 scope = profile display + sign-out + maybe theme preference persistence; deeper settings are a polish detail.)*
- **Main content** area (right) — renders the route's page.
- **Responsive**: sidebar collapses to a hamburger drawer < `md` (reuse the existing `AdminShell` hamburger pattern).
- **Tokens**: 100% `tokens.ts` consumption — no hardcoded colours (preserve the W15 `[oklch(...)]`=0 milestone).

### 2. Route group `(app)/` with a single shared layout; flattened URLs (no `/admin/`)

Introduce a Next.js route group `app/(app)/layout.tsx`:

```
app/(app)/layout.tsx          ← <AuthProvider><QueryProvider><AppShell>{children}</AppShell>...  + login-gate
app/(app)/dashboard/page.tsx  ← NEW — the overview / home
app/(app)/chat/page.tsx       ← moved from app/chat/page.tsx
app/(app)/kb/page.tsx         ← moved from app/admin/kb/page.tsx        (/admin/ prefix dropped — Q4)
app/(app)/kb/[id]/page.tsx    ← moved from app/admin/kb/[id]/page.tsx
app/(app)/kb/new/page.tsx     ← moved from app/admin/kb/new/page.tsx
app/(app)/kb/[id]/upload/page.tsx
app/(app)/eval/page.tsx       ← moved from app/eval/page.tsx
app/(app)/traces/[traceId]/page.tsx  ← moved from app/debug/[traceId]/page.tsx  (rename debug→traces; optional)
app/(app)/settings/page.tsx   ← NEW (small) — profile + sign-out + preferences
```

`app/admin/layout.tsx`, `app/eval/layout.tsx`, `app/debug/layout.tsx` are removed (their providers + shell folded into `app/(app)/layout.tsx`). `app/admin/page.tsx` (the old "Admin Dashboard" placeholder) is removed — its role is taken by `/dashboard`. `app/layout.tsx` (root) keeps only `<ThemeProvider>` + `<Toaster>` (so the auth pages don't get the app chrome). `app/page.tsx` becomes a thin redirect (`/` → `/login`, or `/dashboard` if a session exists) — **the V7 marketing landing is removed** (per Chris Q1: EKP 不是對外推銷的). `app/login/`, `app/register/`, `app/verify/` stay outside `(app)/`.

### 3. `/dashboard` — the post-login home, a genuine overview (per Chris Q2: 真 overview dashboard)

Not a router-to-chat. Cards / panels: KB summary (count + total docs / chunks / storage), recent queries (or, if none, an "ask something" CTA → `/chat`), latest eval status (R@5 / Faithfulness / Correctness, link → `/eval`), system health (Azure Search / Azure OpenAI / Cohere / Langfuse connectivity — wired off `/health` + the component statuses), quick actions (New KB / Upload Document / Run Eval / Open Chat). Layout reference: a clean internal-tool dashboard (cards grid). All data comes from existing endpoints (`/health`, `/kb`, last `/eval/run` result if cached) — no new backend work required for a v1 dashboard.

### 4. Login-gate

A route guard for everything under `(app)/`: a client guard in `(app)/layout.tsx`'s `<AuthProvider>` boundary (or Next.js `middleware.ts`) that redirects unauthenticated users to `/login`. In mock-auth dev mode the mock provider auto-authenticates so no redirect fires (documented). In real MSAL mode, MSAL's redirect flow handles it. `/login` on success → `router.push('/dashboard')` (changed from `/chat`). `/register` → after verify-email auto-login (ADR-0022) → `/dashboard` (changed from `/chat`).

### 5. `/` — redirect, no marketing landing (per Chris Q1)

`app/page.tsx` becomes: if a session exists → redirect `/dashboard`; else → redirect `/login`. The V7 Landing page (the hero + 3 feature cards + how-it-works marketing layout) is **deleted** — EKP is an internal tool, not an outward-facing product, so there is no public marketing surface. (The `brand-panel.tsx` used on `/login` / `/register` stays — it's the auth-page brand splash, not a marketing page.)

### 6. Relationship to ADR-0015 (Chris Q6 — "先再說明和解釋一下和 ADR-0015 的關係影響是什麼")

ADR-0015 (W11 D2 cont, `architecture.md` v5.1 → v6 amendment) made four commitments. ADR-0024 touches them as follows:

| ADR-0015 commitment | ADR-0024 effect | Status |
|---|---|---|
| **(a) 6 views → 9 views** (added V7 Landing `/`, V8 Login `/login`, V9 Register `/register`; moved V1 Chat `/`→`/chat`) | **V7 Landing removed**; **a new `/dashboard` view added** (the real overview, which also subsumes the role of the old V2 "Admin Dashboard" placeholder). V8 Login + V9 Register unchanged. V1 Chat stays at `/chat` (the ADR-0015 path move stands). Net: still ≈9 views, but the *set* changed: out goes Landing, in comes Dashboard; V2 "Admin Dashboard" → just "Dashboard". | **AMENDED** — one view dropped, one added/transformed |
| **(b) "Dify-leaning aesthetic — layout 1:1 mirror Dify Image 1-6 patterns"** | This bundles two things. **(b1) the IA / layout-1:1-mirror part** — Dify's IA has a chrome-less chat surface separate from the dataset/admin chrome, and an outward marketing `/`. ADR-0024 replaces that with a *single unified `<AppShell>`* across all authenticated views and *no marketing `/`*. **(b2) the visual-identity / aesthetic part** — the Notion-leaning "Warm Charcoal + Coral Accent" tokens, the editorial direction, the dark-mode inverted-button pattern — **unchanged**. | **PARTIALLY AMENDED** — (b1) IA/layout-mirror replaced; (b2) aesthetic stands |
| **(c) shadcn/ui foundation commit** (install + `components.json` + 12-15 base components, New York style + custom tokens) | **Unchanged.** `<AppShell>` is built from the same shadcn primitives + `tokens.ts`. ADR-0024 builds *on* this foundation. | **UNCHANGED** |
| **(d) W12-W15 multi-sprint implementation roadmap** (the 9 views were built across W12-W15) | **Unchanged + preserved.** ADR-0024's W18 phase does not redo the W12-W15 work — it *re-parents* the existing views under `<AppShell>`, *re-routes* `/admin/*` → `/kb/*` etc, *removes* the Landing page, and *adds* `/dashboard` + a small `/settings`. The views' internal content (KB Detail's 5 tabs, Eval's metric cards, Debug/Traces' 6-stage timeline, the chat streaming + citations, the auth-page split layout) is untouched. | **UNCHANGED** (re-layout + 2 view changes + re-route, not a rebuild) |

**Net statement**: ADR-0024 **amends ADR-0015** in three specific ways — (1) removes V7 Landing (EKP internal-only); (2) replaces ADR-0015's per-view layout-regime split (chat = chrome-less, admin = AdminShell) with a single unified `<AppShell>` + drops the "admin" framing/URL-prefix; (3) replaces V2 "Admin Dashboard" with a real `/dashboard` overview as the post-login home. It **does not supersede** ADR-0015's: the V8/V9 auth-page designs, the shadcn/ui foundation, the EKP-native visual identity (`tokens.ts`, Notion-leaning aesthetic), the W12-W15 implementation. The "Dify-leaning" label narrows to "Dify-inspired *aesthetic ergonomics*" — the *IA* is no longer Dify's (it's a unified-shell IA, closer to Linear / Notion / ChatGPT-app's single-shell model).

**`architecture.md v6 §5` amendment required on approval** (a v6 → v6.1 or inline-tagged amendment, like the §3.4 / §3.7 ADR-tags): **delete §5.9 (V7 Landing)**; **add a new "§5.x Application Shell" section** (top bar contents + left sidebar module list + main content + responsive collapse + focus mode + the multi-language Tier-2 boundary note); **add a new "§5.x Dashboard" view section**; **rewrite §5.2** (Chat = rendered inside the AppShell, not full-bleed) and **§5.3** (the old "Admin Dashboard" → "Dashboard", relocated to `/dashboard`); **re-route §5.4-§5.7** (`/admin/kb/*` → `/kb/*`, `/debug/*` → `/traces/*`, drop the "admin" framing) — content of those view sections otherwise unchanged. ADR-0015's References get an "amended by ADR-0024" note.

---

## Alternatives Considered

### (A) Status quo — keep the ADR-0015 Dify-leaning 3-regime split (incl. the marketing `/`)
**Rejected per the trigger + Chris's answers** — the stakeholder explicitly does not want a marketing landing, does not want an "admin" split, and wants a unified shell + dashboard-first. Pros: zero work, matches the Dify reference 1:1. Cons: doesn't match how an internal platform is expected to work.

### (B) Middle ground — add `<AdminShell>` to `/chat` only, keep the rest (incl. the marketing `/` and the `/admin/` prefix)
**Rejected** — half-measure: still a marketing `/`, still an "admin" section, still no `/dashboard`, still no login-gate, and the existing sidebar ("Overview / Knowledge Bases / Eval Console") wouldn't naturally include Chat. Doesn't address what was asked.

### (C) Full unified application shell + no marketing landing + no admin framing + real dashboard (**this proposal**)
`<AppShell>` across all authenticated views, route group `(app)/`, flattened URLs, `/dashboard` overview as the post-login home, `/` → redirect to `/login`, login-gate. Pros: a consistent internal-platform UX with one nav model; all functional modules in one sidebar; a real overview home; no dead-weight marketing page. Cons: a multi-day phase (~1-1.5 weeks) — `<AppShell>` extract, route-group restructure, URL flatten, `/dashboard` + small `/settings` build, login-gate, login-redirect change, responsive + focus-mode, re-parenting the existing views, removing the Landing page, dark-mode token re-check, Playwright E2E route updates, `architecture.md v6 §5` amendment + the ADR-0015 amends-note. **Recommended / chosen.**

---

## Consequences

**Positive**
- Consistent internal-platform UX — single top bar + sidebar + main content across Dashboard / Chat / Knowledge Bases / Eval / Traces.
- All functional modules discoverable from one sidebar; no "where did the nav go?" on `/chat`.
- A real post-login overview (`/dashboard`) instead of dropping the user into a chat box; no "admin vs user" mental split.
- Login-gate becomes real in production builds; `/chat` finally gets auth-gated.
- Removes a maintained-but-pointless page (the marketing landing — EKP isn't sold).
- Reuses + generalizes the existing `AdminShell` (hamburger collapse, UserMenu, ThemeToggle, responsive — already built) — not a from-scratch build.
- `/dashboard` v1 needs **no new backend** (consumes `/health` + `/kb` + last cached eval).

**Negative**
- A multi-day UI phase (~1-1.5 weeks; the W18 phase). The largest single change in the W12-W15-then-now UI arc.
- Loses the full-bleed Dify-style chat conversation surface — mitigated by the collapsible sidebar / "focus mode" toggle, but a deliberate departure from ADR-0015's "1:1 mirror Dify" IA.
- URL churn: `/admin/kb/*` → `/kb/*`, `/debug/[traceId]` → `/traces/[traceId]`, `/` no longer the landing — existing bookmarks / the Playwright E2E specs / docs referencing those paths need updating (low blast radius — Tier 1, internal).
- ADR-0015 is amended (3 specific ways) — its References + the `architecture.md v6 §5` text need the amendment.
- A small new `/settings` view appears (profile + sign-out + preferences) — minor scope add.

**Neutral**
- The EKP-native visual identity (`tokens.ts`, Notion-leaning "Warm Charcoal + Coral", dark-mode inverted-button) + the shadcn/ui foundation are unchanged — only the *chrome layout / IA* changes.
- The views' *content* (KB Detail's 5 tabs, Eval's metric cards, Traces' 6-stage timeline, chat streaming + citations, auth-page split layout) is unchanged — they render inside the shell.
- Auth pages (`/login`, `/register`, `/verify`) are unchanged — they stay outside the shell (no app chrome pre-auth); `brand-panel.tsx` stays (it's the auth splash, not a marketing page).
- Multi-language is **not** implemented — the top-bar toggle is a disabled affordance; i18n stays Tier 2 per §11 (CLAUDE.md §5.4 H4).
- Per Chris Q5: this is **its own W18 phase**, independent of W16 F1-F4 (Track A IT cred) and Tier 2 prep — not sequenced after them.

---

## Implementation Deliverables (for the W18 phase, on approval)

> Not implemented by this ADR. The `W18-app-shell-ia` phase carries these, with a `plan.md` per CLAUDE.md §10 R1 (folder **not** pre-created until this ADR is Accepted).

- [ ] D1 — `frontend/components/nav/app-shell.tsx` (generalize `admin-shell.tsx`): collapsible left sidebar (5 modules: Dashboard / Chat / Knowledge Bases / Eval Console / Traces) + top bar (app name → `/dashboard`, global search Cmd+K, language toggle [disabled], `<ThemeToggle>`, `<UserMenu>`) + main content slot + responsive hamburger + focus-mode toggle; 100% `tokens.ts`, no hardcoded colours
- [ ] D2 — `app/(app)/layout.tsx` route group: `<AuthProvider><QueryProvider><AppShell>{children}</AppShell></QueryProvider></AuthProvider>` + the login-gate guard; remove `app/admin/layout.tsx` / `app/eval/layout.tsx` / `app/debug/layout.tsx` / `app/admin/page.tsx`
- [ ] D3 — move + re-route pages into `(app)/`: `chat`; `kb` (from `admin/kb`, `/admin/` prefix dropped); `kb/[id]`; `kb/new`; `kb/[id]/upload`; `eval`; `traces/[traceId]` (from `debug/[traceId]`); update **all** internal `<Link href>` + `router.push` + the Playwright E2E `tests/e2e/` route references + `next.config.mjs` if it has route-specific config
- [ ] D4 — NEW `app/(app)/dashboard/page.tsx` — overview cards (KB summary / recent queries / latest eval / system health off `/health`) + quick actions (New KB / Upload / Run Eval / Open Chat); no new backend
- [ ] D5 — NEW (small) `app/(app)/settings/page.tsx` — profile display (display name / email / oid) + sign-out + theme preference; `<UserMenu>` links here
- [ ] D6 — NEW (thin) `frontend/components/nav/global-search.tsx` — Cmd/Ctrl+K command palette: filter KB names + recent docs + recent traces + "Ask in chat: …" action → `/chat?q=…`. Tier 1 scope only (no semantic search-as-you-type)
- [ ] D7 — login-gate: client guard in the `(app)/` `AuthProvider` boundary (or `middleware.ts`) → unauthenticated → `/login`; mock-auth dev mode documented as no-redirect
- [ ] D8 — `app/login/page.tsx` + `app/register/page.tsx`: success → `router.push('/dashboard')` (was `/chat`); `app/page.tsx`: replace the V7 Landing with a redirect (`/` → `/login`, or `/dashboard` if session); **delete** the V7 Landing markup; keep `brand-panel.tsx`
- [ ] D9 — responsive + a11y pass on the new shell (sidebar nav `aria-current`, hamburger `aria-expanded`, command-palette `role="dialog"` + focus trap); dark-mode token consistency re-check (`[oklch(...)]`=0 milestone preserved); Vitest unit tests for `<AppShell>` nav + `<GlobalSearch>`; Playwright E2E updated for the new routes + a "shell present on authenticated routes / absent on auth pages" assertion
- [ ] D10 — `architecture.md v6 §5` amendment (per the "Relationship to ADR-0015" section above): delete §5.9 Landing; add §5.x Application Shell + §5.x Dashboard; rewrite §5.2 Chat (in-shell) + §5.3 Dashboard (was Admin Dashboard); re-route §5.4-§5.7 (drop `/admin/`, `debug`→`traces`); ADR-0015 References get "amended by ADR-0024"; `COMPONENT_CATALOG.md` C09/C10 + `session-start.md §3` C09/C10 + §10 timeline updated; `decision-form.md` — no new OQ expected (the multi-language affordance is a known §11 Tier 2 item, not a new OQ)

---

## Open questions — RESOLVED (Chris 2026-05-10) + the remaining minor ones

- **Q1 — `/` public landing** → **RESOLVED: remove it.** EKP 不是對外推銷的;`/` redirects to `/login` (or `/dashboard` if a session exists). The V7 Landing page is deleted.
- **Q2 — `/dashboard` scope** → **RESOLVED: a genuine overview dashboard** (stats / recent activity / system health / quick actions). v1 needs no new backend.
- **Q3 — sidebar + top bar** → **RESOLVED:** sidebar = the platform's functional modules (Dashboard / Chat / Knowledge Bases / Eval Console / Traces); top bar = global search (Cmd+K, Tier 1 quick-jump scope) + language toggle (disabled — i18n is Tier 2 per §11) + theme toggle + user profile/settings.
- **Q4 — URL prefix** → **RESOLVED: no "admin".** Drop the `/admin/` prefix; flatten (`/kb/*`, `/eval`, `/traces/*`).
- **Q5 — sequencing** → **RESOLVED: its own W18 phase** (independent of W16 F1-F4 and Tier 2 prep — it's a different track from the prior planning).
- **Q6 — ADR-0015 relationship** → **EXPLAINED above** ("Relationship to ADR-0015" section): amends ADR-0015 in 3 specific ways (remove Landing / unified shell + drop "admin" / real Dashboard); preserves the auth-page designs, shadcn/ui foundation, EKP visual identity, and the W12-W15 implementation.
- *Remaining minor (W18-phase polish, not ADR-blocking)*: "Debug View" → "Traces" rename (Chris confirm); sidebar flat-list vs sectioned-headers (5 items — flat may read cleaner); whether `/settings` ships in W18 or is a follow-up; exact `/dashboard` card set; whether the top-bar global search ships in W18 or is a fast-follow.

---

## References

- `docs/architecture.md` v6 §5 (UI specifications — to be amended per "Relationship to ADR-0015" above) + §11 (Tier 2 list — "Multi-language (JP/ZH)" stays Tier 2)
- ADR-0014 — Hybrid auth model (SSO + self-register) — the login-gate / `/login` entry interplay
- ADR-0015 — UI Tier 1 expansion (6→9 views, Dify-leaning, shadcn/ui foundation) — **this ADR amends ADR-0015** (3 specific ways; see the dedicated section)
- ADR-0021 — V4 Retrieval Testing tab + search-mode param — the KB-detail 5-tab content that moves into the shell unchanged
- ADR-0022 — Auth-transport hardening (httpOnly cookie + CSRF) — the cookie/Bearer dual-path the login-gate relies on
- `CLAUDE.md` §5.1 H1 (layout-philosophy change → ADR), §5.4 H4 (no Tier 2 leak — the multi-language toggle is a disabled affordance, i18n stays Tier 2), §10 R1 (rolling-JIT — the W18 phase folder is NOT pre-created until this ADR is Accepted)
- `frontend/components/nav/admin-shell.tsx` — the existing shell `<AppShell>` generalizes
- `frontend/app/page.tsx` (V7 Landing — to be deleted), `frontend/components/auth/brand-panel.tsx` (auth splash — kept)
- W12-W15 UI sprint cycle (ADR-0015 implementation) — the views being re-parented (not rebuilt)
- W17-beta-hardening closeout local-dev-test session 2026-05-10 — the trigger; Chris's Q1–Q5 answers same session
