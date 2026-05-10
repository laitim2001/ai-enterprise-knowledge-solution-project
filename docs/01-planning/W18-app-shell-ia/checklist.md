---
phase: W18-app-shell-ia
plan_ref: ./plan.md
status: active
last_updated: 2026-05-10
---

# Phase W18 — Checklist

> Atomic checkbox(每 item ≤ 0.5–2 hour effort)。Status:`active` from kickoff 2026-05-10(Chris directive + ADR-0024 Accepted = the authorization)。
> 每 item done 後 `[ ]→[x]` + commit ref;延後項標 🚧 + reason(per CLAUDE.md §10 sacred rule — 唔可以刪未勾選 item)。
> Deliverable ↔ ADR-0024 mapping:F1=D1 / F2=D2+D7 / F3=D3 / F4=D4 / F5=D5 / F6=D6 / F7=D8 / F8=D9+D10-residual / F9=closeout。

## F0 — Kickoff cascade(ADR-0024 acceptance + spec amendment — landed at kickoff)

- [x] F0.1 `docs/adr/0024-unified-application-shell-ia.md` Status **Proposed → Accepted**(Q1-Q6 resolved;Chris directed the post-acceptance cascade;`## Decision` header「proposed」→「accepted」;Implementation-Deliverables note「folder not pre-created until Accepted」→「created on acceptance 2026-05-10」)— `(this commit)`
- [x] F0.2 `docs/adr/README.md` — ADR-0024 row status「**Proposed**」→「Accepted」+ context cell updated(post-acceptance cascade);footnote「Proposed 2026-05-10」→「Accepted 2026-05-10」;「Next NNNN」block 0024 line updated — `(this commit)`
- [x] F0.3 `docs/adr/0015-ui-tier-1-expansion-dify-leaning.md` — Status line gets「**amended by ADR-0024 2026-05-10**」note(3 ways:V7 Landing removed / per-view layout-regime split → single `<AppShell>` / V2「Admin Dashboard」→ real `/dashboard`;preserves V8/V9 auth pages + shadcn/ui foundation + EKP visual identity + W12-W15 impl)+ References section gets an ADR-0024 amended-by entry — `(this commit)`
- [x] F0.4 `docs/architecture.md` — top-block §5 amendment note added(after the v5.1→v6「註」block;inline-tagged, doc version held per the §3.4/§3.7 precedent);**NEW §5.0 Application Shell** section inserted(before §5.1 — statement of the unified shell:top bar + collapsible left sidebar + main content;5 sidebar modules;top-bar contents incl. disabled language toggle [i18n Tier 2 §11];login-gate;flattened routing `app/(app)/...`);§5.2 Chat header `/`→`/chat` + in-shell note;**§5.3「Admin Dashboard」→「Dashboard」** `/admin`→`/dashboard` + body rewritten as a real overview(KB summary / recent queries / latest eval / system health / quick actions);§5.4 KB List `/admin/kb`→`/kb`;§5.5 KB Detail `/admin/kb/[id]`→`/kb/[id]`;§5.6 Eval Console in-shell note(route unchanged);**§5.7「Debug View」→「Traces」** `/debug/[traceId]`→`/traces/[traceId]`;**§5.9 V7 Landing → REMOVED tombstone**(EKP internal-only;`/`→redirect);§5.10/§5.11 Login/Register redirect target `/chat`→`/dashboard` + "stays outside `<AppShell>`" note — `(this commit)`
- [x] F0.5 `docs/01-planning/W18-app-shell-ia/{plan,checklist,progress}.md` created — `status: active`(per Chris directive, not the usual draft→active flip — the directive + ADR-0024 Accepted IS the authorization;same pattern as W17 D0). Plan §2 deliverables F0-F9 = ADR-0024 D1-D10 mapped — `(this commit)`

## F1 — `<AppShell>` component(generalize `<AdminShell>`)— ADR-0024 D1

- [ ] F1.1 NEW `frontend/components/nav/app-shell.tsx` — `<AppShell>` = top bar + collapsible left sidebar + main content slot;extracted/generalized from `admin-shell.tsx`(reuse hamburger-collapse + responsive logic);active-route + nav-items props;file header docstring
- [ ] F1.2 Left sidebar — 5 module items(Dashboard `/dashboard` / Chat `/chat` / Knowledge Bases `/kb` / Eval Console `/eval` / Traces `/traces`)+ active-route highlight(`aria-current="page"`)+ "focus mode" toggle(collapses sidebar, persisted)— flat list
- [ ] F1.3 Top bar — app name/logo(left → `/dashboard`, no marketing tagline)+ global-search trigger(centre — opens `<GlobalSearch>` F6 + Cmd/Ctrl+K binding)+ **disabled** language toggle(tooltip "Multi-language coming soon" — i18n Tier 2 §11)+ `<ThemeToggle>`(reuse)+ `<UserMenu>`(reuse — Profile / Settings → `/settings` / Sign out)
- [ ] F1.4 Responsive — sidebar < `md` → hamburger drawer(reuse `AdminShell` pattern);`aria-expanded` on the hamburger;top bar stays
- [ ] F1.5 Tokens — 100% `tokens.ts`;`Grep '\[oklch'` across `frontend/` = **0**(milestone preserved);`tsc --noEmit` + `next lint` clean

## F2 — `(app)/` route group + consolidated providers + login-gate — ADR-0024 D2 + D7

- [ ] F2.1 NEW `frontend/app/(app)/layout.tsx` — `<AuthProvider><QueryProvider><AppShell>{children}</AppShell></QueryProvider></AuthProvider>`;the single shell-wrapping layout for all authenticated views;file header docstring
- [ ] F2.2 Login-gate — route guard at the `(app)/` `AuthProvider` boundary(or `middleware.ts`)→ unauthenticated → redirect `/login`;mock-auth dev mode = no-redirect(documented in the layout docstring);real MSAL = MSAL's own redirect
- [ ] F2.3 Remove `frontend/app/admin/layout.tsx` + `frontend/app/eval/layout.tsx` + `frontend/app/debug/[traceId]/layout.tsx`(folded into `(app)/layout.tsx`);remove `frontend/app/admin/page.tsx`(old "Admin Dashboard" placeholder — role taken by `/dashboard` F4)
- [ ] F2.4 Root `frontend/app/layout.tsx` — keeps only `<ThemeProvider>` + `<Toaster>`(auth pages get no app chrome);verify no `AuthProvider`/`QueryProvider` leak to root
- [ ] F2.5 Auth pages(`/login` / `/register` / `/verify`)stay OUTSIDE `(app)/`(at `app/login/` etc) — unchanged structurally(F7 only touches the post-success redirect)
- [ ] F2.6 `tsc --noEmit` + `next lint` clean;existing Playwright `webServer` mock-auth smoke still works(no infinite redirect loop — the gate is a no-op in mock mode)

## F3 — Move + re-route pages;flatten URLs;update all links + Playwright — ADR-0024 D3

- [ ] F3.1 Move pages into `app/(app)/`:`chat/page.tsx`(from `app/chat/`)/ `kb/page.tsx`(from `app/admin/kb/`)/ `kb/[id]/page.tsx`(from `app/admin/kb/[id]/`)/ `kb/new/page.tsx`(from `app/admin/kb/new/`)/ `kb/[id]/upload/page.tsx`(from `app/admin/kb/[id]/upload/`)/ `eval/page.tsx`(from `app/eval/`)/ `traces/[traceId]/page.tsx`(from `app/debug/[traceId]/`)— contents unchanged except internal route literals(F3.2)
- [ ] F3.2 Update **all** internal route refs — `<Link href="/admin/kb/...">` → `/kb/...`;`router.push('/admin/...')` → `/...`;`/debug/[traceId]` → `/traces/[traceId]`;remove the in-page logo link from `chat/page.tsx`(now in the AppShell top bar);grep `frontend/` for `'/admin` + `/debug/` → only deliberate refs remain
- [ ] F3.3 Update `frontend/tests/e2e/` — Playwright specs navigating to `/admin/...` / `/debug/...` / `/`(landing)→ `/kb/...` / `/traces/...` / `/dashboard`(or `/login` for the redirect test);route-named snapshot baselines if any
- [ ] F3.4 `frontend/next.config.mjs` — verify the `/api/backend/*` rewrite is path-agnostic(it is — prefix-based);confirm no other route-specific config breaks;no change expected but verify
- [ ] F3.5 `tsc --noEmit` + `next lint` clean;`pnpm test:unit` still passes;Playwright spec `tsc` compile-check(full E2E run needs `npx playwright install chromium` = R8-blocked / CO_W15_F4_browser_binaries — verified by `tsc` + spec review;run = user's pre-Beta smoke)

## F4 — `/dashboard` — the real post-login overview — ADR-0024 D4

- [ ] F4.1 NEW `frontend/app/(app)/dashboard/page.tsx` — cards grid(clean internal-tool dashboard, NOT a router-to-chat);file header docstring
- [ ] F4.2 Cards — (a) KB summary(count + total docs/chunks/storage off `GET /kb`);(b) Recent queries(list N, or「Ask something」CTA → `/chat` if none);(c) Latest eval status(R@5/Faithfulness/Correctness from the last cached `POST /eval/run`, or「Run Eval」CTA + link → `/eval`);(d) System health(Azure AI Search / Azure OpenAI / Cohere / Langfuse off `GET /health` + component statuses — up/down/degraded badges);(e) Quick actions(New KB → `/kb/new` / Upload → `/kb` / Run Eval → `/eval` / Open Chat → `/chat`)
- [ ] F4.3 No new backend — `/health` + `/kb` existing(W1/W2);last `/eval/run` result read from wherever cached(if nowhere → empty state, no backend caching added in W18)
- [ ] F4.4 Loading skeletons + error banners per card(reuse the W17 F4.1 Documents-tab pattern);empty states first-class(brand-new install = all CTAs)
- [ ] F4.5 100% `tokens.ts`;`tsc` + `next lint` clean;`[oklch`=0 preserved;a Vitest render-smoke for the dashboard layout(full test pass = F8)

## F5 — `/settings` — small profile/preferences view — ADR-0024 D5

- [ ] F5.1 NEW `frontend/app/(app)/settings/page.tsx` — profile display(display name / email / oid from the `AuthProvider` user context)+ sign-out button(reuse `<UserMenu>` sign-out path)+ theme preference(Light/Dark/System — reuse `<ThemeToggle>` or a radio group bound to next-themes);file header docstring
- [ ] F5.2 `<UserMenu>` "Settings" menu item → `router.push('/settings')`(wire it — currently absent/no-op)
- [ ] F5.3 100% `tokens.ts`;`tsc` + `next lint` clean;`[oklch`=0 preserved
- [ ] F5.4 Tier 1 scope guard — `/settings` v1 = exactly profile display + sign-out + theme preference;NO notification prefs / API tokens / org settings(polish / Tier 2)

## F6 — Global search command palette(`<GlobalSearch>` — Cmd/Ctrl+K)— ADR-0024 D6

- [ ] F6.1 NEW `frontend/components/nav/global-search.tsx` — command-palette dialog(shadcn `Dialog` or a `cmdk`-style component from existing primitives — **no new dep if avoidable;if `cmdk` genuinely needed → stop-and-ask per H2 first**)triggered by Cmd/Ctrl+K(global key handler)+ the top-bar search trigger;file header docstring
- [ ] F6.2 Tier 1 quick-jump scope — filters:(a) KB names(off cached `GET /kb`)→ `/kb/[id]`;(b) recent documents(if available)→ `/kb/[id]`;(c) recent traces(if available)→ `/traces/[traceId]`;(d) always-present「Ask in chat: "<query>"」→ `/chat?q=<encoded>`. NOT in scope:semantic search-as-you-type across chunks(Tier 2 candidate)
- [ ] F6.3 a11y — `role="dialog"` + `aria-modal` + focus trap + Escape-to-close + arrow-key result navigation(`aria-activedescendant` or roving tabindex)
- [ ] F6.4 100% `tokens.ts`;`tsc` + `next lint` clean;`[oklch`=0 preserved;a Vitest test for the filter logic + key binding(full pass = F8)
- [ ] F6.5 `?q=` chat pre-fill — small `chat/page.tsx` tweak(read `?q=` on mount → pre-fill/send);if it needs more than trivial, scope to "navigate with the query in the URL; chat reads it on mount" — don't redesign the chat input

## F7 — login/register redirect → `/dashboard`;delete V7 Landing;`/` → redirect — ADR-0024 D8

- [ ] F7.1 `frontend/app/login/page.tsx` — successful sign-in → `router.push('/dashboard')`(was `/chat`);same for the MSAL callback path if it has an explicit redirect
- [ ] F7.2 `frontend/app/register/page.tsx` — Step 3 "Welcome" CTA / auto-advance → `/dashboard`(was `/chat`);verify-email auto-login(ADR-0022)means Step 3 lands authenticated
- [ ] F7.3 `frontend/app/page.tsx` — **delete the V7 Landing markup**(hero + 3 feature cards + "how it works" + footer)→ thin redirect:session exists → `/dashboard`;else → `/login`(server `redirect()` or the simplest client check that respects auth state)
- [ ] F7.4 Keep `frontend/components/auth/brand-panel.tsx`(auth-page brand splash, NOT a marketing page);grep-verify nothing else imported the deleted Landing components(Landing-only → delete it too, own mess;shared → leave)
- [ ] F7.5 `tsc` + `next lint` clean;Playwright: `/ → /login`(unauthenticated)/ `/ → /dashboard`(authenticated)redirect assertion replaces the old "landing renders" test;re-grep `[oklch`=0

## F8 — responsive + a11y pass;Vitest + Playwright updates;dark-mode re-check;`COMPONENT_CATALOG.md` note — ADR-0024 D9 + D10-residual

- [ ] F8.1 Responsive pass — `<AppShell>` at `sm`/`md`/`lg`/`xl`:sidebar → hamburger drawer < `md`;top bar usable;command palette full-width on mobile;`/dashboard` cards reflow to 1-column on mobile;browser smoke at 2-3 viewports(reuse the W7 F5.4 / W15 F3 approach)
- [ ] F8.2 a11y pass on the **new** surfaces(W18's own mess only — full NVDA/JAWS/VoiceOver stays Tier 2 / CO_W15_F3_aria_full_audit):sidebar nav `aria-current="page"`;hamburger `aria-expanded`;`<GlobalSearch>` `role="dialog"` + `aria-modal` + focus trap + Escape;`/settings` form labels(`<Label htmlFor>`);`/dashboard` cards have headings + links have accessible names;disabled language toggle `aria-disabled` + tooltip
- [ ] F8.3 Dark-mode re-check — `Grep '\[oklch'` across `frontend/` = **0**(milestone preserved through the restructure);browser smoke: dark-mode toggle on `/dashboard` + `/settings` + the shell chrome(top bar + sidebar)— `tokens.ts` `colorsDark` applied;W17 F5 mechanism note still holds
- [ ] F8.4 Vitest unit tests — `<AppShell>` nav(5 items / active-route highlight / focus-mode toggle collapses)+ `<GlobalSearch>`(Cmd+K opens / filter logic / "Ask in chat" navigates);`pnpm test:unit` → all pass(adds to the W17 F6 baseline of 1 file / 3 tests)
- [ ] F8.5 Playwright E2E — the `tests/e2e/` route updates from F3.3 + NEW assertion: "the `<AppShell>` chrome(top bar + sidebar)is present on `/dashboard` / `/chat` / `/kb` / `/eval` / `/traces/...` and absent on `/login` / `/register`";`tsc` compile-check of the specs(full run = user's pre-Beta smoke per the R8 `npx playwright install chromium` block / CO_W15_F4_browser_binaries)
- [ ] F8.6 `docs/02-architecture/COMPONENT_CATALOG.md` — C09(Admin Console UI)+ C10(Chat Interface UI)status note:both now render inside `<AppShell>`;URL flatten `/admin/*` → `/kb/*`;`/dashboard` = new post-login home;V7 Landing removed;`/settings` added — per ADR-0024(`architecture.md v6 §5` already carries the inline-tagged amendment;the catalog mirrors it)

## F9 — Phase closeout + W19+ rolling-JIT trigger

- [ ] F9.1 W18 phase Gate verdict(PASS / PARTIAL PASS / FAIL with explicit rationale per the W12-W15-W17 pattern)— in `progress.md`
- [ ] F9.2 W18 `progress.md` Retro — 7 sections(What worked / What didn't & friction / Surprises / Decisions / Carry-overs to W19+ / Time tracking / Spec ref alignment)
- [ ] F9.3 ADR-0024 status verified `Accepted`(landed at kickoff;verify-no-op)+ ADR-0024 "Implementation Deliverables" D1-D10 checkboxes ticked against the F1-F9 outcomes
- [ ] F9.4 W18 `plan.md` + `checklist.md` + `progress.md` frontmatter `status: active` → `closed`
- [ ] F9.5 W19+ phase folder **NOT pre-created**(rolling-JIT per CLAUDE.md §10 R1)— kickoff candidates noted in `progress.md` Retro(W16 F1-F4 if Track A IT cred lands / Tier 2 prep governance Q12 / Beta-launch readiness pass / the user's local-dev seed-KB convenience task)
- [ ] F9.6 `session-start.md` hygiene catch-up — §3 C09/C10 status(in `<AppShell>`;URL flatten;`/dashboard`;`/settings`;V7 Landing removed)+ §10 W18 row(closed, Gate verdict)+ W19+ not-pre-created + §11 carry-overs + §12 milestones row + Last-Updated + Update-history;`COMPONENT_CATALOG.md` already touched in F8.6
- [ ] F9.7 No new OQ expected(the multi-language affordance is a known §11 Tier 2 item, not a new OQ);if one surfaces → sync `decision-form.md` per R4

---

## Cross-Cutting

- [ ] Each commit references `progress.md` Day-N entry(R2)— `docs(planning):` / `docs(adr):` housekeeping commits exempt(the F0 kickoff cascade = a `docs:` housekeeping-class commit)
- [ ] Component tag in commit message per CC-1 — F1 = C09+C10+C11 / F2 = C09+C10+C11 / F3 = C09+C10 / F4 = C09(+C07/C02/C06 consumers) / F5 = C11+C09 / F6 = C09 / F7 = C09+C11 / F8 = cross-cutting + test harness + docs / F9 = governance
- [ ] OQ status sync to `decision-form.md`(R4)— no new W18 OQ expected(the language toggle is a known §11 Tier 2 disabled affordance)
- [ ] Risk register — no new W18 risk expected;the R8 `npx playwright install chromium` block(CO_W15_F4_browser_binaries / ADR-0017)is pre-existing and only affects F8.5's *run*, not the spec update
- [ ] CLAUDE.md §5.1 H1 check — the IA restructure is **authorized by ADR-0024**(Accepted 2026-05-10);no other architectural change(F1-F8 implement what the ADR + the amended §5.0-§5.11 describe — re-layout + re-route + 2 view changes + Landing removal;NO §3/§4 component change — backend untouched)
- [ ] CLAUDE.md §5.2 H2 check — frontend-only;no new dependency expected(F6 `<GlobalSearch>` — if `cmdk` is genuinely needed → stop-and-ask first;PARTIAL-PASS fallback = shadcn-`Dialog`-based, zero new dep);shadcn/ui + `tokens.ts` unchanged
- [ ] CLAUDE.md §3.2 conventions — `tsc --noEmit` + `next lint` clean on all new/changed files;no `any` / no `@ts-ignore` without a comment;shadcn/ui only;design tokens via `tokens.ts`(no hardcoded colours — `[oklch`=0);App Router only;Server Components default(Client Components have `"use client"` + a comment)
- [ ] CLAUDE.md §5.5 H5 — no secret committed;no hard-coded tenant/subscription/resource;the login-gate uses the existing auth context(no new credential store);no PII / no plaintext-prompt logging changed
- [ ] CLAUDE.md §5.4 H4 — Tier 2 boundary held:the language toggle is a **disabled affordance only**(no i18n machinery);global search is **quick-jump only**(no semantic search-as-you-type);no GraphRAG / multi-agent / multi-tenancy / multi-modal / auto-sync / fine-tune leak
- [ ] Karpathy §1.3 surgical — re-parent + re-route the W12-W15 views;do NOT rebuild their content;do NOT "順手" refactor adjacent code;clean up only W18's own orphans(deleted-Landing components, broken imports from the moves)

---

**Lifecycle reminder**:呢份 checklist 衍生自 `plan.md` deliverables。新加 deliverable 必須先入 plan + §7 changelog,然後再加 checklist item。延後 item 標 🚧 + reason,**唔可以刪**未勾選 `[ ]`。
