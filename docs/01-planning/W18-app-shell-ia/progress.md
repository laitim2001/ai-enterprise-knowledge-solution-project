---
phase: W18-app-shell-ia
plan_ref: ./plan.md
checklist_ref: ./checklist.md
status: active
last_updated: 2026-05-10
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
| F1 `<AppShell>` | 1-1.5d | — | — |
| F2 `(app)/` route group + login-gate | 1d | — | — |
| F3 move + re-route + links + Playwright | 1.5d | — | — |
| F4 `/dashboard` | 1d | — | — |
| F5 `/settings` | 0.5d | — | — |
| F6 `<GlobalSearch>` | 0.5-1d | — | — |
| F7 login/register → /dashboard + delete Landing | 0.5d | — | — |
| F8 responsive/a11y + tests + dark-recheck + catalog | 1d | — | — |
| F9 closeout | 0.5d | — | — |

### Next

- F1 — `<AppShell>` component(generalize `admin-shell.tsx`)— wait for the user's go-ahead(directive pattern: explicit per-step).

---

**Lifecycle reminder**:Phase 收尾寫 Retro（What worked / What didn't & friction / Surprises / Decisions / Carry-overs to W19+ / Time tracking / Spec ref alignment）。W19+ phase folder **唔會** pre-create（rolling-JIT per CLAUDE.md §10 R1）。
