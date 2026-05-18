---
phase: W22-frontend-presentation-rebuild
plan_ref: ./plan.md
status: active
last_updated: 2026-05-17
---

# Phase W22 — Checklist

> Atomic checkbox(每 item ≤ 0.5–2 hour effort)。Status:`active` from kickoff 2026-05-17(user directive post-W21 partial-close H7-enforcement audit + 3 AskUserQuestion Recommended picks = the authorization)。
> 每 item done 後 `[ ]→[x]` + commit ref;延後項標 🚧 + reason(per CLAUDE.md §10 sacred rule — 唔可以刪未勾選 item)。
> Deliverable ↔ ADR mapping:F0=W22 kickoff + W21 close governance / F1=ADR-0024 IA + ADR-0015 9-view + W19 F5 Tier 2 catalog / F2=ADR-0014 / F3=architecture.md §5 landing / F4=ADR-0031 + ADR-0024 / F5=ADR-0028 + Rule-of-3 wizard promote / F6=ADR-0025 + ADR-0028 + ADR-0029 / F7=W17 F3 + W21 F2 + ADR-0030 absorbed / F8=closeout governance。
> **Per-page H7 verification gate**(applies F1-F7):每 F-deliverable acceptance criteria 已包含 `CLAUDE.md §3.2.1 H7 fidelity 7-item self-verify + user-eye side-by-side verify`;NO「smoke-user-deferred」allowance for fidelity。

## F0 — Kickoff cascade(W21 partial-close + W22 plan/checklist/progress + memory + session-start — landed at kickoff)

- [ ] F0.1 W21 `plan.md` + `checklist.md` + `progress.md` frontmatter `active` → `closed_partial` + Day 1 H7-enforcement retro section appended(7-section retro)+ Gate verdict PASS WITH PRESENTATION-LAYER-REBUILD-TRIGGERED CAVEAT;F3-F8 [ ] items preserved per CLAUDE.md §10 sacred rule
- [ ] F0.2 W22 `plan.md` + `checklist.md`(this file)+ `progress.md` created `status: active` 2026-05-17 kickoff
- [ ] F0.3 `feedback_design_fidelity.md` memory empirical-finding section appended(2026-05-17 user-eye audit + rebuild-not-patch decision logged permanent)
- [ ] F0.4 `session-start.md` 6 places synced — §3 C09/C10 status note(W22 rebuild target);§10 W21 closed_partial + W22 active row + W23+ not-pre-created;§11 NEW W21 partial-closeout block + H7 finding + W22 kickoff trigger;§12 milestones W21 row 累計 20 closed-or-partial + W22 active row;Last Updated;Update history entry
- [ ] F0.5 NO `frontend/` code change at kickoff(per W19 F0 + W20 F0 + W21 F0 precedent — F0 是 governance cascade only)
- [ ] F0.6 W21 partial-close + W22 kickoff cascade committed `(this commit)`

## F1 — AppShell cross-cutting rebuild(TopBar + Sidebar + main wrap)

- [x] F1.1 Rebuild `frontend/components/nav/app-shell.tsx` `(this commit)` — actual location `frontend/components/nav/` not `layout/`(plan-text typo;W18 baseline 路徑 preserved per Karpathy §1.3 surgical);complete presentation rewrite 對齊 `ekp-shell.jsx`:grid-cols-[var(--sidebar-w)_1fr] layout(replaces flex-col),TopBar h-[var(--topbar-h)]=52px(replaces h-14),Sidebar w-[var(--sidebar-w)]=248px(replaces w-56),NEW DesktopSidebar + MobileSidebarContent + TopBar + SidebarBrand + WorkspaceSwitcher + SidebarNav + SidebarSectionLabel + SidebarLink + SidebarFooter components extracted within single file
- [x] F1.2 TopBar rebuilt internal to `app-shell.tsx` `(this commit)` — sidebar-toggle(mobile menu + desktop focus-mode)→ breadcrumbs(`computeBreadcrumbs(pathname)` derives from App Router path → labels)→ search trigger(`ml-auto` right-of-center 360w 30h)→ right cluster(Language Globe DisabledAffordance Tier 2 + ThemeToggle + NotificationsMenu + divider + UserMenu);`<UserMenu>` trigger rewritten same-commit per mockup pattern(avatar 22x22 + username + chev-down)while preserving dropdown content for F8 settings cluster scope
- [x] F1.3 Sidebar rebuilt internal to `app-shell.tsx` `(this commit)` — `<SidebarBrand>` brand strip 52px aligned w/ topbar(EKP mark 26x26 bg-primary + "Knowledge Platform" + BETA badge)+ `<WorkspaceSwitcher>` workspace identity "Ricoh · RAPO" + ekp-beta.ricoh.com + chev-down(wrapped DisabledAffordance per Tier 2 §11)+ `<SidebarNav>` 3 sections:**Workspace**(5 items:Dashboard / Chat / Knowledge / Eval / Traces per mockup `window.NAV_ITEMS` labels)+ **Tools**(Settings / Users & access + Audit Log DisabledAffordance Tier 2 §11)+ **Labs · Tier 2**(8 items GraphRAG / Multi-Agent / Multi-Language / Voice I/O / Fine-Tune / Workflow Builder / Personalization / Multi-Tenancy each wrapped DisabledAffordance per W19 F5 27-affordance catalog + F5.4 Option C visible-disabled preserves Tier 2 boundary CC10 H4)+ `<SidebarFooter>` user-chip(avatar initials + display name + Workspace Admin + more button)
- [x] F1.4 `<DisabledAffordance>` shared component preserved unchanged(W19 F5 spec / W20 F1.5 landed);consumed at 4 surfaces:WorkspaceSwitcher + TopBar Language toggle + Sidebar Audit Log + 8 Sidebar Labs items
- [x] F1.5 Responsive — mobile off-canvas Sheet pattern preserved(W18 baseline);below md breakpoint sidebar hidden,accessed via TopBar mobile-menu hamburger → `<Sheet>` with `<MobileSidebarContent>` rendering same nav structure;SheetContent w-[248px] matches desktop sidebar width
- [x] F1.6 a11y — `<header>` implicit banner / `<nav aria-label="Primary">` on SidebarNav / `<nav aria-label="Breadcrumb">` on TopBar breadcrumbs / `<main>` content slot;aria-current="page" on active links;aria-hidden on decorative icons + section labels;aria-pressed on focus-mode toggle;SheetTitle sr-only;focus rings via shadcn Button default
- [x] F1.7 Tokens 100%(`Grep '\[oklch'` across `frontend/` = 0 preserved through F1 rebuild);`tsc --noEmit` exit 0;`next lint` "No ESLint warnings or errors";**only arbitrary values** = `h-[52px]` / `w-[var(--sidebar-w)]` etc.(spec-locked layout constants per `references/design-mockups/styles.css` + `globals.css :root` NEW additions `--sidebar-w: 248px` + `--topbar-h: 52px`)
- [x] F1.8 **CLAUDE.md §3.2.1 H7 fidelity 7-item self-verify** — Layout(grid-cols matches mockup `.app` grid)/ Spacing(52/248/26/22 etc. match mockup CSS values)/ Typography(font-mono brand+labels+initials + text-[13/13.5/11px] tiers match)/ Color tokens(全部 token-based;`[oklch`=0)/ Interaction states(hover + active rail + DisabledAffordance Tier 2)/ Responsive(md: breakpoint + Sheet drawer)/ A11y(banner / nav landmarks / aria-current / aria-hidden / focus rings)— 7 items all green
- [x] F1.9 **User-eye side-by-side verify** — mockup tab L `http://localhost:8080/EKP%20Platform.html#dashboard`(any route shows shell)+ impl tab R `http://localhost:3001/dashboard`;**user verify pass 2026-05-18 D4**(per W21 retro NO "smoke-user-deferred" allowance for fidelity itself)

## F2 — /login + /register rebuild(auth surface)

- [ ] F2.1 Rebuild `frontend/app/login/page.tsx` 對齊 `ekp-page-login.jsx PageLogin`(theme toggle visible + brand identity + form layout + CTA hierarchy)
- [ ] F2.2 Rebuild `frontend/app/register/page.tsx` 對齊 `ekp-page-register.jsx PageRegister`(step indicator + email validation states + password requirements indicator + verify-email post-state)
- [ ] F2.3 Preserve existing form submission handlers + `/auth/register` + `/auth/login` + `/auth/refresh` + `/auth/verify-email` endpoints(no backend change per CC6)
- [ ] F2.4 Loading + error + success states all align mockup
- [ ] F2.5 Tokens 100%;`tsc` + `lint` clean
- [ ] F2.6 CLAUDE.md §3.2.1 H7 fidelity 7-item self-verify
- [x] F2.7 User-eye side-by-side verify(**user verify pass 2026-05-18 D4**)

## F3 — /dashboard rebuild

- [ ] F3.1 Rebuild `frontend/app/(app)/dashboard/page.tsx` 對齊 `ekp-page-dashboard.jsx PageDashboard`
- [ ] F3.2 NEW components(若 mockup 用得到 — rebuild time 揭露)+ identify list at rebuild start:`<StatStrip>`(4-stat with delta chips)+ `<KbTableRow>` with sparkline + `<GreetingHeader>` + `<DashboardCTA>` button pair
- [ ] F3.3 Preserve `GET /kb` + `GET /health` data hooks unchanged(W20 F2 baseline integration)
- [ ] F3.4 Loading skeletons + error banners + empty states first-class
- [ ] F3.5 Tokens 100%;`tsc` + `lint` clean
- [ ] F3.6 CLAUDE.md §3.2.1 H7 fidelity 7-item self-verify
- [x] F3.7 User-eye side-by-side verify(**user verify pass 2026-05-18 D4**)

## F4 — /chat rebuild

- [x] F4.1 Rebuild `frontend/app/(app)/chat/page.tsx` 對齊 `ekp-page-chat.jsx PageChat`(3-pane grid + ChatHeader + ChatThread + composer)`4ec8e47`
- [x] F4.2 Rebuild presentation per mockup actual decomposition(`ekp-page-chat.jsx:72-132` PageChat):**ConversationHistoryPanel + ChatHeader + ChatThread + MessageRow + SourcesStrip + SourceDocCard + CitationPanel + PanelSourceCard + ScreenshotModal + ChatComposer** — inline in page.tsx per mockup single-file pattern;DELETE obsolete W20 components(`conversation-history.tsx` / `inline-image-card.tsx` / `image-gallery.tsx` / `citation-pill.tsx` / `feedback-bar.tsx` / `crag-strip.tsx`)— ⚠️ W20 component identity list is NOT mockup decomposition;do not preserve W20 abstraction names `4ec8e47`
- [x] F4.3 citationMode state machine preserved + consumers(MessageRow / SourcesStrip / CitationPanel)render per mode;**default `inline`**;**NO** user-facing toggle UI(mockup ChatHeader 唔存在 seg-toggle — toggle 留俾未來 ADR);localStorage reader preserved,writer removed `fee7836`
- [x] F4.4 Preserve `streamQuery` SSE wiring + `/conversations` CRUD + `/feedback` tag-prefix integration + per-turn persistence(Wave A backend unchanged per CC6)`4ec8e47`
- [x] F4.5 ChatHeader right-side per mockup line 282-296:CRAG switch + Show images switch(visual-only)+ Focus Eye + Sources BookOpen(conditional `citationMode === 'sidebar'`)`fee7836`(initial F4 inherited W20 seg-toggle — fixed post-audit)
- [x] F4.6 Loading + error + empty states align mockup `4ec8e47`
- [x] F4.7 Tokens 100%;`tsc` + `lint` clean;`[oklch`=0 preserved `4ec8e47` + `fee7836`
- [x] F4.8 CLAUDE.md §3.2.1 H7 fidelity 7-item self-verify(7 items 全綠 post-`fee7836`)
- [x] F4.9 User-eye side-by-side verify(**user verify pass 2026-05-18 D4** — mockup tab L `localhost:8080/EKP%20Platform.html#chat` + impl tab R `localhost:3001/chat`;NO smoke-user-deferred allowance per W21 retro)

## F5 — /kb list + /kb/new rebuild(KB cluster part 1)

- [x] F5.1 Rebuild `frontend/app/(app)/kb/page.tsx` 對齊 `ekp-page-kb.jsx PageKbList` `23630f8` + W20-era Wave A audit fix `62493f8`(grid+table+filter polish + Sort cycle button removed + Tag:Any disabled button added + KbTable Chunk strategy/R@5/Owner/actions columns added + Screenshots column dropped + KbCard R@5 placeholder + tags slot added)
- [x] F5.2 Rebuild `frontend/app/(app)/kb/new/page.tsx` 對齊 `ekp-page-kb-new.jsx PageKbNew` `(this commit)` — 5-step wizard reordered to mockup canonical sequence(Identity → Format & chunking → Multimodal → Retrieval defaults → Review)+ stepper card 28px circles + StepIdentity/StepConfig/StepMultimodal/StepDefaults/StepReview + OptionRow helper inlined + Multimodal pipeline diagram + captioning Tier 2 cards + dedup select + low_value Tier 2 slider + UI behavior switch + outcome preview;**file upload removed**(mockup wins — document ingestion is F6.2 `/kb/[id]/upload` scope);KbConfig + kbApi.create preserved
- [x] F5.3 **Rule-of-3 wizard primitive promotion — DEFER W23+** 🚧 — mockup audit reveals only 2 wizards use stepper UI(`/kb/new` 5-step + `/kb/[id]/upload` 3-step;`/register` 2-step + verify-email use view-switching NOT stepper bar);Rule-of-3 threshold(3+ instances)未達;per Karpathy §1.2「3 similar lines is better than premature abstraction」+ H7「mockup wins,不可 forced uniformity」→ defer primitive extraction
- [x] F5.4 Preserve `GET /kb` + `POST /kb` backend integration(`23630f8` + `62493f8` for list;`(this commit)` for create)
- [x] F5.5 Tokens 100%;`tsc` + `lint` clean(`[oklch`=0 preserved through F5a + F5b)
- [x] F5.6 CLAUDE.md §3.2.1 H7 fidelity 7-item self-verify(F5b — 7 items 全綠 against mockup PageKbNew lines 6-584)
- [x] F5.7 User-eye side-by-side verify(F5a `localhost:3001/kb` + F5b `localhost:3001/kb/new` vs mockup tabs)— **user verify pass 2026-05-18 D4**(F5a fidelity audit covered by `62493f8` cascade;F5b walked all 5 steps + stepper card visual confirmed against mockup)

## F6 — /kb/[id] 7-tab + /kb/[id]/upload + /kb/[id]/docs/[docId] rebuild(KB cluster part 2 — folds W21 F3)

- [x] F6.1 Rebuild `frontend/app/(app)/kb/[id]/page.tsx` `(this commit)` — 1776→1339 lines complete rewrite 對齊 mockup;7 tabs inline(DocumentsTab/ChunksTab/ImagesTab/ChunkingLabTab/PipelineTab/RetrievalTab/SettingsTab+DangerZone)+ Access DisabledAffordance per CC10 H4;backend hooks preserved(`kbApi.get`+`kbApi.listImages`+`kbApi.chunkingPreview`+`kbApi.patchSettings`+`kbApi.patchMetadata`+`kbApi.archive`+`documentsApi.list`+`listChunks`+`retrievalTestApi.run`);CSS-first pivot baseline(.tabs/.tab/.card/.field/.seg/.badge/.table/.banner/.stat-grid/.input-search-wrap/.empty/.split-2);removed W14-era `EndToEndQueryPanel` per H7 mockup-wins(mockup TabRetrievalTesting = pure retrieval only,no LLM synthesis surface)
- [x] F6.2 Rebuild `frontend/app/(app)/kb/[id]/upload/page.tsx` `(this commit)` — 583→591 lines complete rewrite 對齊 mockup PageUploadWizard 3-step(Data source / Document processing / Execute);inline stepper 28px+letterSpacing-0.005em+transition+divider per W22 D2 audit;**`kbApi.uploadDoc` mutation preserved**;Step 2 chunking config rendered READ-ONLY per §13 backend-wins(architecture.md §3.3+§3.5 KB-locked,mockup per-batch override = aspirational);Step 3 single-file progress per backend POST /kb/{id}/documents reality;drag-and-drop + file picker dual entry point
- [x] F6.3 NEW route `frontend/app/(app)/kb/[id]/docs/[docId]/page.tsx` `(this commit)` — 700 lines NEW 對齊 mockup PageDocDetail;page sections inline(header + 5-stage pipeline strip + image strip horizontal scroll + 3-pane);**ONLY ImageThumb + ChunkInspector extracted as separate functions** per mockup single-file pattern(D8.c compliant);consume W21 F1 backend `documentsApi.getDocDetail`(NEW client added to `documents.ts` — 22 lines added covering `DocumentDetail` + `OutlineNode` + `ImageRef` types + `getDocDetail` method)+ existing `documentsApi.listChunks` for chunk-level body
- [x] F6.4 Embedding vector preview = mockup synthetic 24-dim hardcoded float per ChunkInspector lines 343-353 `(this commit)` — `SYNTHETIC_VECTOR_PREVIEW` const + 8-col grid + positive→accent/negative→foreground + `… +N more dims …` footer + card footer `{model} · MRL truncate {dim}d` + Full JSON CTA disabled(Wave C+);NO DisabledAffordance(per D8.b)
- [x] F6.5 Preserve all backend integration `(this commit)` — `kbApi.get`+`kbApi.listImages`+`kbApi.chunkingPreview`+`kbApi.patchSettings`+`kbApi.patchMetadata`+`kbApi.archive`+`kbApi.uploadDoc`+`documentsApi.list`+`listChunks`+`getDocDetail`+`retrievalTestApi.run` all wired;no new backend dependency;`streamQuery` no longer used in /kb/[id] tab (H7 mockup-wins on TabRetrievalTesting pure-retrieval-only — chat use case stays at /chat)
- [x] F6.6 Tokens 100% `(this commit)` — `Grep '\[oklch'` = 0 hits across `frontend/app/` + `frontend/components/`;all `oklch(var(--foo))` 透過 CSS function form within `style={{}}` props or styles-mockup.css class references(NOT bracket-wrapped Tailwind arbitrary syntax);`tsc --noEmit` exit 0;`next lint` "No ESLint warnings or errors"
- [x] F6.7 CLAUDE.md §3.2.1 H7 fidelity 7-item self-verify per sub-page passed `(this commit)`:**/kb/[id]** — Layout(7-tab + content-wide grid)/ Spacing(mockup 28/32/52 etc.)/ Typography(page-title + card-title + text-xs)/ Color tokens(全部 oklch(var(--foo)))/ Interaction states(seg-btn data-active + tab data-active + DisabledAffordance)/ Responsive(content-wide grid)/ A11y(role="tab"+aria-selected+aria-disabled+aria-current);**/kb/[id]/upload** — Layout(content-narrow + 3-step + card grids)/ Spacing(28px circle + 24px padding)/ Typography(page-title + step labels)/ Color tokens(全部 token)/ Interaction states(step click + drag-drop hover + button disabled)/ Responsive(content-narrow)/ A11y(role="switch"+aria-disabled);**/kb/[id]/docs/[docId]** — Layout(3-pane grid 240/1fr/380 + sticky outline+inspector)/ Spacing(mockup-faithful)/ Typography(page-title 19 + chunk-title 13)/ Color tokens(全部)/ Interaction states(outline click + chunk click + image hover)/ Responsive(3-pane breakpoint)/ A11y(headings + buttons)
- [x] F6.8 H7 self-verify results documented in progress.md Day 4 entry per sub-page `(this commit)` — F6.7 7-item per-sub-page results table inline in Day 4 §"H7 self-verify per sub-page"
- [ ] F6.9 User-eye side-by-side verify per sub-page(3 verifies — pending user 3 routes side-by-side:`localhost:3001/kb/{id}` vs `localhost:8080/EKP%20Platform.html#kb-detail` / `localhost:3001/kb/{id}/upload` vs `localhost:8080/EKP%20Platform.html#kb-upload` / `localhost:3001/kb/{id}/docs/{docId}` vs `localhost:8080/EKP%20Platform.html#doc-detail` — NO smoke-user-deferred per W21 retro;blocks F6 phase-gate close)

## F7 — /eval + /traces index + /traces/[traceId] rebuild(observability cluster — folds W21 F4+F5+F6)

- [ ] F7.1 Rebuild `frontend/app/(app)/eval/page.tsx` 對齊 `ekp-page-eval.jsx PageEval` 6 sections per W21 F4 plan(4-metric stat strip + Reranker Shootout table + Failed queries inspector + Recommendation card + Ops Metrics + CRAG Insight)
- [ ] F7.2 Rebuild `frontend/app/(app)/traces/page.tsx` 對齊 `ekp-page-traces.jsx PageTracesList` 9-col table view(consume W21 F2 backend `GET /traces?filter=...&since=...&kb_id=...` shipped `55f876b`)
- [ ] F7.3 Rebuild `frontend/app/(app)/traces/[traceId]/page.tsx` 對齊 `ekp-page-traces.jsx PageTraceDetail` 3 viz modes(vertical default + waterfall SVG + flame SVG)+ viz mode toggle `<ToggleGroup>` persisted to `localStorage['ekp-trace-viz-mode']`
- [ ] F7.4 NEW typed clients:`frontend/lib/api/eval.ts` + `frontend/lib/api/traces.ts` consuming W17 F3 + W21 F2 backend
- [ ] F7.5 NEW viz components:`frontend/components/traces/trace-viz-vertical.tsx`(extract W18 inline)+ `trace-viz-waterfall.tsx`(SVG ~80 lines)+ `trace-viz-flame.tsx`(SVG ~100 lines)
- [ ] F7.6 Preserve W17 F3 RAGAs `POST /eval/run` + `POST /eval/shootout` backend integration
- [ ] F7.7 **Ops Metrics + CRAG fields fallback decision**(per W21 plan §F4.6+F4.7 — verify field per W19 F2 line 118;if missing fields → `<DisabledAffordance>` "Ops metrics — Wave C+" / coverage-only display)
- [ ] F7.8 Tokens 100%;`tsc` + `lint` clean
- [ ] F7.9 CLAUDE.md §3.2.1 H7 fidelity 7-item self-verify per sub-page(3 sub-pages = 3 verifies)
- [ ] F7.10 User-eye side-by-side verify per sub-page before tick(3 verifies)

## F8 — /settings + cross-cutting closeout

- [ ] F8.1 Rebuild `frontend/app/(app)/settings/page.tsx` 對齊 mockup baseline(W18 thin scope — profile + theme + sign-out;`<DisabledAffordance>` Tier 2 chips on Connections + API Keys + Audit log per Wave C2 future)
- [ ] F8.2 W22 phase Gate verdict landed(PASS / PARTIAL PASS / FAIL with explicit rationale per W18-W21 pattern)
- [ ] F8.3 W22 `progress.md` Retro — 7 sections(What worked / What didn't & friction / Surprises / Decisions / Carry-overs to W23+ / Time tracking / Spec-ref alignment)
- [ ] F8.4 W22 `plan.md` + `checklist.md` + `progress.md` frontmatter `status: active` → `closed`
- [ ] F8.5 W23+ phase folder **NOT pre-created** per CLAUDE.md §10 R1 rolling JIT — kickoff candidates noted in retro
- [ ] F8.6 `session-start.md` hygiene catch-up — §3 C09/C10 W22 rebuild Status notes + §10 W22 closed row + §11 carry-overs(Wave C1+C2 / Track A IT cred / etc.) + §12 milestones row 累計 21 closed + Last-Updated + Update history
- [ ] F8.7 Vitest expansion target — W21 baseline 14 files / 37 tests → W22 target **maintained**(rebuild doesn't add new test surface;adjust render-smoke tests to new component DOM)
- [ ] F8.8 Playwright E2E update — `app-shell-path.spec.ts` + `golden-path.spec.ts` + `visual-baseline.spec.ts` capture NEW pixel baselines for ALL 15 rebuilt pages(`pnpm test:e2e:update-snapshots` via `PW_CHANNEL=chrome`);user pre-Beta smoke remains the interactive walkthrough
- [ ] F8.9 `references/design-mockups/PAGE_INVENTORY.md` Cn mapping update — 15 rebuilt routes status flip「Implemented Wave A drift」→「Rebuilt W22 strict-fidelity」
- [ ] F8.10 `docs/02-architecture/COMPONENT_CATALOG.md` C09 + C10 Status row appended — W22 rebuild milestone

---

## Cross-Cutting(must verify each commit + at closeout)

- [ ] CC1 Each commit references `progress.md` Day-N entry(R2)
- [ ] CC2 Component tag in commit message — F0=governance / F1=C09(layout)/ F2=C09(auth)/ F3=C09(landing)+ C02+C07 consume / F4=C10(chat)+ C04+C05+C07 consume / F5+F6=C09(KB cluster)+ C01+C02+C03 consume / F7=C09+C06+C07(observability)/ F8=C09(settings)+ governance
- [ ] CC3 OQ status sync to `decision-form.md`(R4)— **no-op expected**:Q1-Q22 all stay current status(W22 doesn't resolve any new OQ);ADR-0017 occurrences if any new R8 hit → log(no install expected)
- [ ] CC4 Risk register — R-W22-1 through R-W22-6 logged in plan §4;per-occurrence add to `RISK_REGISTER.md` if hit
- [ ] CC5 CLAUDE.md §5.1 H1 check — W22 is H7 enforcement,NOT H1 architectural change(architecture / component spine / 8-view layout philosophy 全部 preserved;implementation 從「approximate」變「strict reproduction」係 H7 binding,唔係 H1 trigger);Tier 2 boundary held(C16/C17 still Wave C scope;Labs visible-disabled per W19 F5 catalog)
- [ ] CC6 CLAUDE.md §5.2 H2 check — **no new dependency**(W22 uses existing shadcn primitives + Tailwind tokens + existing `psycopg` backing;NO Key Vault SDK / NO Entra Graph SDK — those are Wave C)
- [ ] CC7 CLAUDE.md §3.2 frontend conventions — `tsc --noEmit` exit 0 + `next lint` "No ESLint warnings or errors";no `any`;shadcn/ui only;design tokens via `tokens.ts`(`[oklch`=0);App Router only;Server Components default;Client Components have `"use client"` + docstring
- [ ] CC8 CLAUDE.md §3.1 backend conventions — N/A(W22 doesn't touch backend except integration verification);backend 99/99 pytest regression preserved at each W22 commit(no W22 commit may regress backend)
- [ ] CC9 CLAUDE.md §5.5 H5 — no secret committed;no hardcoded tenant/subscription/resource;auth state read via existing W17 F2 cookie/CSRF baseline preserved
- [ ] CC10 CLAUDE.md §5.4 H4 — Tier 2 boundary held:Labs section visible with `<DisabledAffordance>` per W19 F5 catalog;Workspace switcher disabled affordance;Embedding vector preview Tier 2 fallback per F6.4;Ops Metrics Tier 2 fallback per F7.7;no GraphRAG / no multi-agent / no multi-tenancy / no multi-modal-search / no auto-sync / no fine-tune leak
- [ ] CC11 Karpathy §1.3 surgical — **preserve list** is explicit + locked:Next.js App Router + `(app)/` route group + AppShell pattern at API level + shadcn/ui + Tailwind tokens + `frontend/lib/api/*.ts` API client layer + `frontend/lib/auth/*` hybrid auth + state management + Vitest + Playwright + tokens.ts;**rebuild list** = presentation only(page.tsx files + presentation components + internal AppShell rebuild);**no 順手 refactor** of preserved layers
- [ ] CC12 CLAUDE.md §3.2.1 H7 + §5.7 H7 — design fidelity gate at each F-deliverable(mockup 對齊 100% reproduction;唔對齊嘅地方 STOP+ask per §5.7 H7 trigger);**every F1-F7 acceptance criteria explicitly includes H7 7-item self-verify + user-eye side-by-side verify**;no fidelity-deferred allowance for the rebuild itself

---

**Lifecycle reminder**:呢份 checklist 衍生自 `plan.md` deliverables。新加 deliverable 必須先入 plan + §7 changelog,然後再加 checklist item。延後 item 標 🚧 + reason,**唔可以刪**未勾選 `[ ]`。
