---
phase: W22-frontend-presentation-rebuild
name: "Frontend Presentation Layer Rebuild — strict 100% mockup fidelity per CLAUDE.md §5.7 H7 (rebuild not patch when fundamental drift)"
sprint_week: W22
start_date: 2026-05-17              # real-calendar — kicked off same-session as W21 partial-close (user directive 2026-05-17 post-screenshot fidelity audit;immediate per H7 enforcement)
end_date: 2026-05-24                # ~1 week window per page-by-page rebuild cadence;real-calendar collapse pattern 1.8-12× applies — actual likely ~2-4 days per W12-W20 trajectory;frontmatter is a window, not a commitment
status: active                      # `active` from kickoff 2026-05-17 (user directive at W21 partial-close session + 3 AskUserQuestion Recommended picks = the authorization)
spec_refs:
  - CLAUDE.md §5.7                  # H7 Design Fidelity Constraint (hard constraint;promoted v1.7 2026-05-17)
  - CLAUDE.md §3.2.1                # Design Fidelity Rule (7-item checklist:layout / spacing / typography / color tokens / interaction states / responsive / a11y)
  - CLAUDE.md §13                   # When-in-Doubt rows — Mockup vs implementation / Mockup detail 不清晰 / Mockup vs backend contract conflict
  - architecture.md v6 §5           # UI Tier 1 expansion 9 views (per ADR-0015) + §5.5.2a Doc Detail 3-pane (per ADR-0029) + §5.6 Eval Console + §5.7 Traces — presentation rebuild operates ON these surfaces unchanged
  - ADR-0015                        # UI Tier 1 expansion 9 views (Dify-leaning;amended by ADR-0024)
  - ADR-0024                        # Unified application shell IA (W18) — AppShell pattern API preserved;internal rebuilt to match mockup
  - ADR-0025                        # KB Detail 8-tab (Wave A shipped 7-tab `-Access`;W22 rebuild preserves 7-tab + activates Access tab per Wave C1 future)
  - ADR-0026                        # Settings 6-tab fully editable (Wave C2 scope;W22 covers /settings baseline rebuild only — full 6-tab editable in Wave C2)
  - ADR-0028                        # /kb/new 5-step wizard
  - ADR-0029                        # /doc-detail 3-pane (Accepted Option C `/kb/[id]/docs/[docId]` — W21 F3 deferred → W22 KB cluster scope)
  - ADR-0030                        # SKIPPED-absorbed — Trace 3 viz + /traces list (W21 F5+F6 deferred → W22 observability cluster scope)
  - ADR-0031                        # Server-side Conversation History (Wave A shipped backend + frontend;W22 rebuild preserves backend integration + rebuilds presentation)
prior_phase: W21-frontend-wave-b    # closed_partial 2026-05-17 (F1+F2 backend landed `306dbe0` + `55f876b`;F3-F8 frontend deferred per H7 enforcement after user-eye fidelity audit);20 phase milestone with W21-partial counted
related_artifacts:
  - docs/01-planning/W21-frontend-wave-b/progress.md      # Day 1 H7-enforcement retro + W21 partial-close rationale (this phase's authorization)
  - docs/01-planning/W19-frontend-audit-and-adr-draft/audit/W19-mockup-jsx-audit.md  # 22 mockup files / 11K lines audited (W19 F1) — reuse for component spec
  - docs/01-planning/W19-frontend-audit-and-adr-draft/audit/W19-backend-gap-map.md   # 28 endpoints × 38 schemas mapped (W19 F2) — preserve all backend integration points
  - docs/01-planning/W19-frontend-audit-and-adr-draft/audit/W19-tier2-affordance-catalog.md # 27-affordance Tier 2 catalog + DisabledAffordance spec (W19 F5)
  - references/design-mockups/PAGE_INVENTORY.md           # canonical page list — W22 rebuild targets 15 pages (rows #1-15)
  - references/design-mockups/DESIGN_README.md            # mockup entry doc + Warm Charcoal + Coral Accent tokens lock
  - references/design-mockups/EKP\ Platform.html          # mockup HTML entry — served via `python -m http.server 8080` from `references/design-mockups/` for paste-friendly hash routing during fidelity verify
  - references/design-mockups/ekp-page-*.jsx              # 17 per-page React components — canonical visual + interaction spec per page
  - .claude/projects/.../memory/feedback_design_fidelity.md  # H7 standing-instruction memory with W21 empirical-finding appended 2026-05-17
---

# Phase W22 — Frontend Presentation Layer Rebuild Plan

> **Authorization**:User explicit directive 2026-05-17(W21 partial-close session post-screenshot fidelity audit):
>
> 「**我認為應該是重新地去建立和準備所有本項目的頁面,而且是根據 mockup 的所有頁面效果,因為我要的是 presentation layer 的一致,而不是把整個 frontend 架構重構**」
>
> + 3 AskUserQuestion Recommended picks:**(1)** 即時 close W21 + kickoff W22-frontend-presentation-rebuild **(2)** Page rebuild ordering = user-facing impact priority(TopBar+Sidebar 先 → /dashboard → /chat → /kb → /kb-detail → 其他)**(3)** Mockup primitive 用 shadcn primitive 重寫(H2 vendor lock 規限技術,H7 規限 fidelity)
>
> 呢個係 **H7 enforcement**(CLAUDE.md §5.7 promoted v1.7 hard constraint 2026-05-17),**唔係** H1 architectural change。architecture(C01-C13 spine + Next.js App Router + AppShell pattern + shadcn/ui + hybrid auth + Postgres + 28 endpoints + W21 F1+F2 backend)全部 preserved unchanged;rebuild 限於 presentation layer。

---

## §0 Phase identity

**Trigger**:User-eye side-by-side fidelity audit 2026-05-17 揭露 W20 Wave A `/dashboard` 同 mockup 有 4 大 fundamental drift(TopBar / Sidebar / Main content shape / Typography)。Automated gates(`tsc` / `lint` / `[oklch`=0 / pytest)全部 green 但都唔 measure presentation fidelity;visual drift 透過咗自動化 verification。**Decision**:Rebuild not patch when fundamental drift —— Karpathy §1.3 surgical unit = page-level rebuild,not localised token swap。

**Scope**:15 pages 全部 presentation-layer rebuild(W20 8 shipped + W21 4 planned + W18 2 baseline + 1 follow-up)+ AppShell cross-cutting rebuild。

**Out of scope**:
- Backend refactor(F1-F2 backend + all 28 endpoints unchanged)
- Auth flow(hybrid auth + cookie + CSRF + scrypt + ACS Email — Wave A baseline preserved)
- Data fetching hooks / API client layer(`frontend/lib/api/*.ts` preserved unchanged)
- State management(Zustand / React state — preserved unchanged)
- Test infrastructure(Vitest + Playwright — preserved + extended)
- Tier 2 features(GraphRAG / multi-agent / etc.) — Labs section visible in Sidebar with disabled affordance per W19 F5 27-affordance Tier 2 catalog
- New ADR-026 Settings 6-tab fully-editable scope(Wave C2);Wave A `/settings` thin baseline preserved + rebuild presentation only
- New ADR-027 `/users` Tier 1.5 RBAC scope(Wave C1)

**Authorities**:
- **CLAUDE.md §5.7 H7** Design Fidelity Constraint(hard constraint binding level)
- **CLAUDE.md §3.2.1** Design Fidelity Rule 7-item checklist
- **CLAUDE.md §10 R1-R5** rolling JIT phase planning(this phase 即時 kickoff with plan landed before any code)
- **CLAUDE.md §13** When-in-Doubt rows(Mockup vs implementation / Mockup detail 不清晰 / shadcn primitive 缺失 → STOP+ask)

---

## §1 Authorization + spec refs

每個 F-deliverable 嘅 authorization = 對應 mockup `ekp-page-*.jsx` + 對應 architecture.md v6 §5 inline-tagged amendment(W21 kickoff `236376d` 已 land 4 amendments;W19+W20 earlier amendments 仍然 valid)。**Architecture spec 不變;implementation 從「approximate」變「strict reproduction」就係 H7 enforcement core。**

ADR mapping per page-cluster:
- AppShell cross-cutting → ADR-0024 IA unchanged + W19 F5 disabled affordance catalog
- /login + /register → ADR-0014 hybrid auth(presentation rebuild only)
- /dashboard → architecture.md §5(generic landing — has 4-stat strip + KB table + sparklines per mockup `ekp-page-dashboard.jsx`)
- /chat → ADR-0031(server-side Conversation History — Wave A backend preserved;presentation rebuild)
- /kb + /kb/new → ADR-0028(5-step wizard scope unchanged)
- /kb/[id] 7-tab `-Access` → ADR-0025 8-tab + ADR-0027 Access tab Wave C1(W22 ships 7-tab + disabled affordance on Access)
- /kb/[id]/upload → ADR-0028 + Wave A 3-step rebuild preserved
- /kb/[id]/docs/[docId] → ADR-0029 Option C 3-pane(W21 F3 deferred → W22 KB cluster)
- /eval → architecture.md v6 §5.6(W21 F4 deferred → W22 observability cluster;consumes W17 F3 RAGAs)
- /traces index → architecture.md v6 §5.7 + ADR-0030 absorbed(W21 F5 deferred → W22 observability cluster;consumes W21 F2 backend GET /traces shipped)
- /traces/[traceId] → ADR-0030 absorbed 3 viz modes(W21 F6 deferred → W22 observability cluster)
- /settings → ADR-0026 future-Wave-C2 scope;W22 rebuild Wave A baseline `/settings` thin presentation only

---

## §2 F0-F8 deliverables

**Rolling JIT discipline**:F0 + F1 detailed kickoff time;F2-F8 sketched;detail refines per-deliverable at kickoff time per W12-W20 pattern。**Page rebuild ordering = user-facing impact priority** per user pick:AppShell cross-cutting 先(每頁出),然後 dashboard / chat / kb cluster / 觀測 cluster / settings。

### F0 — Kickoff cascade(landed at phase open — `(this commit)`)

- **Component(s)**:cross-cutting governance(C09 Admin Console UI + C10 Chat Interface UI)
- **Spec ref**:CLAUDE.md §10 R1 rolling JIT + §5.7 H7 + this plan §0
- **OQ deps**:none(reuse W21 spec refs + W19 audit artifacts)
- **Acceptance criteria**:
  - F0.1 W21 partial-close cascade landed(plan + checklist + progress frontmatter `active` → `closed_partial`;Day 1 H7-enforcement retro section appended;Gate verdict PASS WITH PRESENTATION-LAYER-REBUILD-TRIGGERED CAVEAT;F3-F8 [ ] items preserved per CLAUDE.md §10 sacred rule)
  - F0.2 W22 plan + checklist + progress created `status: active`
  - F0.3 `feedback_design_fidelity.md` memory empirical-finding section appended(2026-05-17 user-eye audit + rebuild-not-patch decision logged permanent)
  - F0.4 `session-start.md` 6 places synced(§3 C09/C10 status note;§10 W21 closed_partial + W22 active row;§11 NEW W21 partial-closeout block + H7 finding + W22 kickoff trigger;§12 milestones W21 row 累計 20 closed-or-partial + W22 active row;Last Updated;Update history entry)
  - F0.5 NO `frontend/` code change at kickoff(per W19 F0 + W20 F0 + W21 F0 precedent — F0 是 governance cascade only)

### F1 — AppShell cross-cutting rebuild(TopBar + Sidebar + main wrap)

- **Component(s)**:**C09** Admin Console UI(cross-cutting layout)
- **Spec ref**:`ekp-page-app-shell.jsx`(若有,else inline embed in `EKP Platform.html`)+ ADR-0024 IA API preserved + W19 F5 27-affordance Tier 2 catalog + `<DisabledAffordance>` shared component
- **OQ deps**:none
- **Mockup deviations from W20 implementation that must close**:
  - TopBar:加 Workspace switcher chevron(「Ricoh > RAPO」+ disabled affordance per Tier 2 catalog)+ theme toggle visible + 用戶 full name display(read from auth state)+ search w/ Cmd+K hint visible
  - Sidebar:section headers「WORKSPACE / NAVIGATE / TOOLS」+ Labs section integrated(GraphRAG / Multi-Agent / Multi-Language / Fine-Tune / Workflow Builder / Personalization / Multi Tenancy — all with `<DisabledAffordance>` per Tier 2)+ user card footer
  - Typography:Warm Charcoal + Coral Accent oklch token system per ADR-0015 W12 D2 lock
- **Acceptance criteria**:
  - F1.1 Rebuild `frontend/components/layout/app-shell.tsx`(or wherever current AppShell lives — file path preserved per Karpathy §1.3 surgical;internal 重 build 對齊 mockup)
  - F1.2 Rebuild `frontend/components/layout/top-bar.tsx` — workspace switcher + theme toggle + user name + Cmd+K search trigger 全部對齊 mockup
  - F1.3 Rebuild `frontend/components/layout/sidebar.tsx` — section headers + Labs section + user card footer 全部對齊 mockup
  - F1.4 `<DisabledAffordance>` shared component(W19 F5 spec / W20 F1.5 landed — preserved unchanged;consumed by Labs section + workspace switcher)
  - F1.5 Responsive — mobile drawer behavior per mockup(W18 ADR-0024 `<Sheet>` pattern preserved;internal rebuild)
  - F1.6 a11y — focus ring + aria landmarks + skip-to-content link per mockup
  - F1.7 Tokens 100%(`Grep '\[oklch'` across `frontend/` = 0 preserved);`tsc --noEmit` exit 0;`next lint` clean
  - F1.8 **CLAUDE.md §3.2.1 H7 design fidelity 7-item self-verify**(layout / spacing / typography / color tokens / interaction states / responsive / a11y)+ **user-eye side-by-side verify** before ship
- **Effort estimate**:1-1.5 days(W22 D1-D2 — largest cross-cutting effect;every downstream page inherits)
- **Owner**:AI(implementation)+ user(eye-verify final tick)

### F2 — /login + /register rebuild(auth surface)

- **Component(s)**:**C09** Admin Console UI(auth pages)
- **Spec ref**:`ekp-page-login.jsx PageLogin` + `ekp-page-register.jsx PageRegister` + ADR-0014 hybrid auth(presentation rebuild only — backend / verify-email flow / ACS Email preserved)
- **OQ deps**:none
- **Acceptance criteria**:
  - F2.1 Rebuild `frontend/app/login/page.tsx` 對齊 `PageLogin`(theme toggle visible + brand identity + form layout + CTA hierarchy)
  - F2.2 Rebuild `frontend/app/register/page.tsx` 對齊 `PageRegister`(step indicator 若有 + email validation states + password requirements indicator + verify-email post-state)
  - F2.3 Preserve existing form submission handlers + `/auth/register` + `/auth/login` + `/auth/refresh` + `/auth/verify-email` endpoints(no backend change)
  - F2.4 Loading + error + success states all align mockup
  - F2.5 Tokens 100%;`tsc` + `lint` clean
  - F2.6 CLAUDE.md §3.2.1 H7 fidelity 7-item self-verify + user-eye side-by-side verify
- **Effort estimate**:0.5-1 day(W22 D2)— smaller surface

### F3 — /dashboard rebuild

- **Component(s)**:**C09** Admin Console UI(landing page consuming **C02** KB + **C07** health + **C06** eval)
- **Spec ref**:`ekp-page-dashboard.jsx PageDashboard`
- **OQ deps**:none(consumes existing `GET /kb` + `GET /health` per-component dots W20 F2 baseline preserved + future `/eval/latest` if exists else CTA)
- **Mockup deviations from W20 implementation that must close**:全部 4 大 drift(TopBar + Sidebar inherited from F1;Main content shape:「Welcome back, {name}」greeting + view-latest-eval CTA + Ask-the-KB CTA + 4-stat strip with real numbers + KB table with sparklines)
- **Acceptance criteria**:
  - F3.1 Rebuild `frontend/app/(app)/dashboard/page.tsx` 對齊 `PageDashboard`
  - F3.2 NEW components(若 mockup 用得到 — rebuild time 揭露):`<StatStrip>`(4-stat with delta chips)+ `<KbTableRow>` with sparkline + `<GreetingHeader>` + `<DashboardCTA>` button pair
  - F3.3 Preserve `GET /kb` + `GET /health` data hooks unchanged(W20 F2 baseline)
  - F3.4 Loading skeletons + error banners + empty states first-class
  - F3.5 Tokens 100%;`tsc` + `lint` clean
  - F3.6 CLAUDE.md §3.2.1 H7 fidelity 7-item self-verify + user-eye side-by-side verify
- **Effort estimate**:1 day(W22 D3)

### F4 — /chat rebuild

- **Component(s)**:**C10** Chat Interface UI(rebuild presentation;preserve ADR-0031 server-side Conversation History backend integration)
- **Spec ref**:`ekp-page-chat.jsx PageChat`
- **OQ deps**:none(consumes existing `POST /query` SSE + `/conversations` CRUD + `POST /feedback` — all Wave A backend preserved)
- **Acceptance criteria**:
  - F4.1 Rebuild `frontend/app/(app)/chat/page.tsx` 對齊 `PageChat`(3-pane grid + ChatHeader + ChatThread + composer)
  - F4.2 Rebuild presentation per mockup `ekp-page-chat.jsx PageChat` actual decomposition(lines 72-132):**ConversationHistoryPanel + ChatHeader + ChatThread + MessageRow + SourcesStrip + SourceDocCard + CitationPanel + PanelSourceCard + ScreenshotModal + ChatComposer** — mockup uses single-file functions so inline within `page.tsx`(per mockup pattern,not separate component files);DELETE obsolete W20 components that don't match mockup decomposition(`conversation-history.tsx` / `inline-image-card.tsx` / `image-gallery.tsx` / `citation-pill.tsx` / `feedback-bar.tsx` / `crag-strip.tsx`)— ⚠️ **W20 component identity list is NOT the mockup decomposition,do not preserve W20 abstraction names**
  - F4.3 citationMode state machine preserved at PageChat level + consumers(MessageRow / SourcesStrip / CitationPanel)render per mode;**default `inline`**(no user-facing toggle UI per mockup ChatHeader line 257-298 which has CRAG + Show images switches + Focus eye + Sources book ONLY — **NO** seg-toggle);localStorage `ekp-citation-mode` reader preserved(writer removed — future ADR can re-introduce toggle without state-shape change);mode set externally via `tweaks.citationPlacement` per ADR-0031 Decision § Citation modes — **toggle UI 喺 mockup 入面唔存在,本 deliverable 唔可以 invent 一個**
  - F4.4 Preserve `streamQuery` SSE wiring + `/conversations` CRUD + `/feedback` tag-prefix integration + per-turn persistence(Wave A backend unchanged per CC6)
  - F4.5 ChatHeader right-side per mockup line 282-296:`<div className="row">` CRAG `<span className="switch" data-on="true" />` + Show images `<span className="switch" data-on="true" />`(visual-only,mockup parity)`<div className="spacer">` then `<div className="row">` Focus `<Eye>` + Sources `<BookOpen>`(BookOpen conditional on `citationMode === 'sidebar'` per mockup line 290-294)
  - F4.6 Loading + error + empty states align mockup
  - F4.7 Tokens 100%;`tsc` + `lint` clean;`[oklch`=0 preserved
  - F4.8 CLAUDE.md §3.2.1 H7 fidelity 7-item self-verify
  - F4.9 User-eye side-by-side verify before tick(NEW gate per W21 retro;no smoke-user-deferred allowance)
- **Effort estimate**:1.5-2 days(W22 D4-D5)— largest single-page surface(mockup decomposition + SSE + citation modes)
- **Implementation status**:✅ F4.1-F4.4 + F4.6-F4.8 landed `4ec8e47` 2026-05-17;⚠️ F4.5 mockup-divergent originally(W20 seg-toggle inherited)— **fixed `fee7836` 2026-05-18** post user-eye fidelity audit;F4.9 user-eye verify pass pending

### F5 — /kb list + /kb/new rebuild(KB cluster part 1)

- **Component(s)**:**C09** Admin Console UI(KB list + creation wizard)
- **Spec ref**:`ekp-page-kb.jsx PageKbList` + `PageKbNew`(5-step wizard per ADR-0028)
- **OQ deps**:none
- **Acceptance criteria**:
  - F5.1 Rebuild `frontend/app/(app)/kb/page.tsx` 對齊 `PageKbList`(grid+table+filter polish)
  - F5.2 Rebuild `frontend/app/(app)/kb/new/page.tsx` 對齊 `PageKbNew`(5-step wizard per ADR-0028 + KbConfig +4 multimodal fields per Wave A)
  - F5.3 **Rule-of-3 wizard primitive promotion — CONDITIONAL on mockup styling 一致 verify**(W20 F6.2 carry-over candidate;4 candidate wizard surfaces:F5.2 `/kb/new` 5-step + F6.2 `/kb/[id]/upload` 3-step + F2.2 `/register` 2-step + W13 verify-email)。Per CLAUDE.md §5.7 H7:**先打開 mockup 4 個 wizard 並排對比 stepper header styling**;若 4 個 styling identical → extract shared `frontend/components/ui/stepper.tsx` + `<Stepper.Stage>` + `<Stepper.Field>` + refactor 4 wizards to consume;若任何一個 wizard 嘅 stepper header 有 bespoke styling → **defer primitive extraction 去 W23+**(per Karpathy §1.2「3 similar lines is better than premature abstraction」+ H7「mockup wins,不可 forced uniformity」)
  - F5.4 Preserve `GET /kb` + `POST /kb` backend integration
  - F5.5 Tokens 100%;`tsc` + `lint` clean
  - F5.6 CLAUDE.md §3.2.1 H7 fidelity 7-item self-verify + user-eye side-by-side verify
- **Effort estimate**:1 day(W22 D5-D6)

### F6 — /kb/[id] 7-tab + /kb/[id]/upload + /kb/[id]/docs/[docId] rebuild(KB cluster part 2 — folds W21 F3)

- **Component(s)**:**C09** Admin Console UI(KB detail + upload + doc detail)
- **Spec ref**:`ekp-page-kb-detail.jsx PageKbDetail` + `ekp-page-kb-upload.jsx PageUploadWizard` + `ekp-page-doc-detail.jsx PageDocDetail`(per ADR-0025 8-tab + ADR-0028 + ADR-0029 Option C)
- **OQ deps**:**Embedding vector preview feasibility verify**(per ADR-0029 §3 alt #3 — Wave B carry-over)— if Azure Search vector exposure expensive,`<DisabledAffordance variant="p3-preview" showBadge>` Tier 2 chip per `<ChunkInspector>` rebuild time decide
- **Acceptance criteria**:
  - F6.1 Rebuild `frontend/app/(app)/kb/[id]/page.tsx` 對齊 `PageKbDetail` 7-tab `-Access`(Documents + Chunks + Images + Chunking Lab + Pipeline + Retrieval Testing + Settings;Access tab disabled affordance — Wave C1 activates)
  - F6.2 Rebuild `frontend/app/(app)/kb/[id]/upload/page.tsx` 對齊 `PageUploadWizard` 3-step(consume shared `<Stepper>` per F5.3)
  - F6.3 NEW route + rebuild `frontend/app/(app)/kb/[id]/docs/[docId]/page.tsx` 對齊 `PageDocDetail` 3-pane(outline + chunks + inspector)— W21 F3 deferred here。Consume W21 F1 backend `GET /kb/{kb_id}/docs/{doc_id}` enriched endpoint shipped(`306dbe0`)
  - F6.4 NEW components per mockup(rebuild time):`<DocumentOutline>` + `<ChunkList>` + `<ChunkInspector>` + `<ImageStripScroller>` + per-tab content components
  - F6.5 Preserve all backend integration:`GET /kb/[id]` + 7-tab endpoints(documents / chunks / images / pipeline / retrieval-testing / settings)+ W21 F1 doc-detail endpoint
  - F6.6 Tokens 100%;`tsc` + `lint` clean
  - F6.7 CLAUDE.md §3.2.1 H7 fidelity 7-item self-verify + user-eye side-by-side verify per sub-page
- **Effort estimate**:2-3 days(W22 D6-D8)— largest cluster

### F7 — /eval + /traces index + /traces/[traceId] rebuild(observability cluster — folds W21 F4+F5+F6)

- **Component(s)**:**C09** Admin Console UI(eval + traces)+ **C06** Eval Framework(consume only)+ **C07** Observability(consume only)
- **Spec ref**:`ekp-page-eval.jsx PageEval` + `ekp-page-traces.jsx PageTracesList + PageTraceDetail` + W17 F3 RAGAs 4-metric integration + W21 F2 GET /traces backend shipped
- **OQ deps**:**Ops Metrics + CRAG fields fallback decision**(per W21 plan §F4.6+F4.7 — verify field per W19 F2 line 118;if missing fields → `<DisabledAffordance>` "Ops metrics — Wave C+" / coverage-only display)
- **Acceptance criteria**:
  - F7.1 Rebuild `frontend/app/(app)/eval/page.tsx` 對齊 `PageEval` 6 sections per W21 F4 plan(4-metric stat strip + Reranker Shootout table + Failed queries inspector + Recommendation card + Ops Metrics + CRAG Insight)
  - F7.2 Rebuild `frontend/app/(app)/traces/page.tsx` 對齊 `PageTracesList` 9-col table view(consume W21 F2 backend `GET /traces?filter=...&since=...&kb_id=...` shipped `55f876b`)
  - F7.3 Rebuild `frontend/app/(app)/traces/[traceId]/page.tsx` 對齊 `PageTraceDetail` 3 viz modes(vertical default + waterfall SVG + flame SVG)+ viz mode toggle `<ToggleGroup>` persisted to `localStorage['ekp-trace-viz-mode']`
  - F7.4 NEW typed clients:`frontend/lib/api/eval.ts` + `frontend/lib/api/traces.ts` consuming W17 F3 + W21 F2 backend
  - F7.5 NEW viz components:`frontend/components/traces/trace-viz-vertical.tsx`(extract W18 inline)+ `trace-viz-waterfall.tsx`(SVG ~80 lines)+ `trace-viz-flame.tsx`(SVG ~100 lines)
  - F7.6 Preserve W17 F3 RAGAs `POST /eval/run` + `POST /eval/shootout` backend integration
  - F7.7 Tokens 100%;`tsc` + `lint` clean
  - F7.8 CLAUDE.md §3.2.1 H7 fidelity 7-item self-verify + user-eye side-by-side verify per sub-page
- **Effort estimate**:1.5-2 days(W22 D8-D9)

### F8 — /settings + cross-cutting closeout

- **Component(s)**:**C09** Admin Console UI(settings baseline + cross-cutting governance)
- **Spec ref**:W18 `/settings` baseline + Wave A user menu integration;**NOT** ADR-0026 6-tab fully-editable(Wave C2 scope)
- **OQ deps**:none
- **Acceptance criteria**:
  - F8.1 Rebuild `frontend/app/(app)/settings/page.tsx` 對齊 mockup baseline(W18 thin scope — profile + theme + sign-out;`<DisabledAffordance>` Tier 2 chips on Connections + API Keys + Audit log per Wave C2 future)
  - F8.2 W22 phase Gate verdict landed(PASS / PARTIAL PASS / FAIL with explicit rationale per W18-W21 pattern)
  - F8.3 W22 `progress.md` Retro — 7 sections(What worked / What didn't & friction / Surprises / Decisions / Carry-overs to W23+ / Time tracking / Spec-ref alignment)
  - F8.4 W22 `plan.md` + `checklist.md` + `progress.md` frontmatter `status: active` → `closed`
  - F8.5 W23+ phase folder **NOT pre-created** per CLAUDE.md §10 R1 rolling JIT — kickoff candidates noted in retro
  - F8.6 `session-start.md` hygiene catch-up — §3 C09/C10 W22 rebuild Status notes + §10 W22 closed row + §11 carry-overs(Wave C1+C2 / Track A IT cred / etc.) + §12 milestones row 累計 21 closed + Last-Updated + Update history
  - F8.7 Vitest expansion target — W21 baseline 14 files / 37 tests → W22 target **maintained**(rebuild doesn't add new test surface;adjust render-smoke tests to new component DOM)
  - F8.8 Playwright E2E update — `app-shell-path.spec.ts` + `golden-path.spec.ts` + `visual-baseline.spec.ts` capture NEW pixel baselines for ALL 15 rebuilt pages(`pnpm test:e2e:update-snapshots` via `PW_CHANNEL=chrome`);user pre-Beta smoke remains the interactive walkthrough
  - F8.9 `references/design-mockups/PAGE_INVENTORY.md` Cn mapping update — 15 rebuilt routes status flip「Implemented Wave A drift」→「Rebuilt W22 strict-fidelity」
  - F8.10 `docs/02-architecture/COMPONENT_CATALOG.md` C09 + C10 Status row appended — W22 rebuild milestone
- **Effort estimate**:0.5-1 day(W22 D9-D10 — closeout governance)

---

## §3 Success Criteria + Gate verdict

**Phase Gate = PASS** requires:
1. F0-F8 all `[ ]` items in checklist.md flipped `[x]`(or `🚧` with explicit deferral reason)
2. **Per-page H7 7-item self-verify ALL passed**(layout / spacing / typography / color tokens / interaction states / responsive / a11y for each of 15 pages)
3. **Per-page user-eye side-by-side verify ALL passed**(NEW gate per W21 retro decision — no more "smoke-user-deferred caveat" allowing fidelity drift through;user-eye verify 必須喺 page ship 之前 hit,NOT delayed to Beta pre-smoke)
4. `tsc --noEmit` exit 0
5. `next lint` clean(No ESLint warnings or errors)
6. `Grep '\[oklch'` across `frontend/` = 0(milestone preserved through 15-page rebuild)
7. `pnpm test:unit` Vitest all pass(test count may shift +/- per component DOM rewrite — render-smoke tests update is OK,coverage not regress)
8. `pnpm test:e2e` via `PW_CHANNEL=chrome` — render-smoke 15/15 green;pixel baselines re-captured + checked-in
9. **Backend 99/99 pytest regression** — 0 backend regression(W22 doesn't touch backend except integration verification)

**PARTIAL PASS** allowance:if 1-2 pages hit H7 mockup-detail-unclear or shadcn primitive-missing trigger,STOP+ask per H7;defer that page to W23+ with explicit `🚧` reason in checklist。**Not allowed**:fidelity drift through。

**FAIL** triggers:fundamental presentation drift discovered post-ship(repeat of W20 pattern)— immediate STOP and re-rebuild that page。

---

## §4 Risks

| R# | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| **R-W22-1** | Mockup primitive 嗰個 shadcn 冇對應(e.g. custom popover animation / custom badge variant)| Medium | Medium | Per H7 trigger:STOP+ask immediately;options = add custom primitive / write vanilla `<div>` / 改 mockup;don't approximate。Logged per-occurrence in progress.md |
| **R-W22-2** | Mockup detail unclear(font weight / exact spacing / hover state shade)| High | Low | Per H7 trigger:STOP+ask;options = pick conservative interpretation + log decision;don't silently approximate |
| **R-W22-3** | Mockup vs backend contract conflict(e.g. mockup expects field X that backend schema doesn't return)| Medium | Medium | Per CLAUDE.md §13 When-in-Doubt:**backend wins**(architecture.md > design-mockups per authority ordering);visual-polish-only migrate(W20 F7.2 precedent);log decision in progress.md changelog |
| **R-W22-4** | Rebuild scope creep(順手 refactor backend integration / state mgmt / auth flow)| Medium | High | Per Karpathy §1.3 surgical:**preserve** list is explicit + locked at kickoff;每 commit verify diff stays in `frontend/app/` + `frontend/components/` presentation files only(unless explicit deviation logged in §7 changelog) |
| **R-W22-5** | Real-calendar collapse not as fast as W20(15 pages > 8 pages Wave A scope)| High | Low | Rolling JIT + collapse uncertainty acceptable;`end_date: 2026-05-24` is window not commitment;closeout when last F-deliverable ticks |
| **R-W22-6** | Cumulative `[oklch` regressions(rebuild introduces hardcoded oklch via copy-paste from mockup stripped components)| Medium | Medium | Pre-commit `Grep '\[oklch'` check per F-deliverable;commit-time fail if non-zero;`tokens.ts` is the only oklch source allowed |

---

## §5 Dependencies / OQ deps

- **No new OQ**(Q1-Q22 status preserved per W21 closeout)
- **No new ADR**(W22 implements existing ADR-0014 / 0015 / 0024 / 0025 / 0028 / 0029 / 0031 + skipped-absorbed 0030;ADR-0026 + 0027 Wave C scope unchanged)
- **No new dependency**(per CC6 H2 lock — **F1 mid-session CSS-first pivot landed**:mockup `styles.css` 1073 lines verbatim adopted as `frontend/app/styles-mockup.css`(1048 lines after `@tailwind` directive elision);visual layer driven by mockup CSS classes(`.btn .btn-primary .btn-lg .card .field .label .input .hint .seg .badge` etc.);shadcn primitives consumed where Radix a11y benefits(Dialog / DropdownMenu / Sheet / Toast / Tabs etc.);Tailwind utility classes for one-off layout;existing `psycopg` backing all preserved;Wave C 2 new deps Key Vault SDK + Entra Graph SDK 仍然 Wave C scope)
- **No new R8 occurrence expected**(no new package install;W22 limited to existing codebase rewrite + shadcn primitive consumption)
- **Existing W22 dev workflow:**
  - Frontend dev server `localhost:3001`(`pnpm dev`)
  - Backend `localhost:8000`(`uvicorn`)
  - Mockup HTTP server `localhost:8080`(`python -m http.server 8080` from `references/design-mockups/` — established this phase as standard fidelity-verify workflow)
  - 2 Chrome tab side-by-side:mockup hash route + implementation URL path

---

## §6 Carry-overs from W21 partial-close

W21 progress.md retro Day 1 §5 carry-over list:
- W21 F3 `/kb/[id]/docs/[docId]` 3-pane Doc Detail per ADR-0029 Option C → **W22 F6.3**
- W21 F4 `/eval` 6-section refactor per W17 F3 RAGAs → **W22 F7.1**
- W21 F5 `/traces` index list view per ADR-0030 absorbed → **W22 F7.2**(consumes F2 backend shipped `55f876b`)
- W21 F6 `/traces/[traceId]` 3 viz modes refactor → **W22 F7.3**
- W21 F7 cross-cutting + F8 closeout → **W22 F8** governance
- Embedding vector preview feasibility verify(ADR-0029 §3 alt #3)→ **W22 F6.4** decide time
- CO_W14_process_grep_verify 10+ cumulative → **W22 plan §7 5-step formalized**(see §7 below)
- Rule-of-3 wizard primitive promotion(now Rule-of-4 with W22 wizard surfaces)→ **W22 F5.3** realize

Earlier carry-overs from W12-W20 that affect W22:
- **CO16 / Track A IT cred consumption** → W16 F1-F4 still Track-A-blocked;parallel track to W22(mock-auth default continues through Wave C per user 岔口 2)
- **CO17 R8 mitigation Plan B sequencing** → R8 not triggered by W22(no new package install)
- **CO_W15_F1_eval_set_v1** → still OPEN(needs Q14 SME labels;not W22 scope)
- **CO_W15_F3_dark_mode_visual_verify** → W22 H7 self-verify includes dark-mode token verification per page;new pixel baselines via `PW_CHANNEL=chrome`
- **CO_W15_F4_interactive_flow_E2E** → user pre-Beta smoke;not W22 blocker
- **W21 partial-close F1+F2 backend retained** — `306dbe0` + `55f876b` shipped + 99/99 backend pytest green

---

## §7 Changelog

| Date | Author | Change |
|---|---|---|
| **2026-05-17 D0** | AI per Chris directive | **W22 phase kickoff cascade landed** — `plan.md` + `checklist.md` + `progress.md` created `status: active`;authorization = user explicit directive 2026-05-17 post-screenshot fidelity audit「我認為應該是重新地去建立和準備所有本項目的頁面...presentation layer 的一致,而不是把整個 frontend 架構重構」+ 3 AskUserQuestion Recommended picks(immediate close W21 + page ordering by user-facing impact + shadcn primitive 重寫);per CLAUDE.md §10 R1 rolling JIT + §5.7 H7 enforcement;no `frontend/` code change at kickoff(F0 governance only per W19+W20+W21 F0 precedent);F1-F8 detailed in §2 with rolling-JIT detail-refine cadence。**Pre-active-flip grep verification 5-step formalized** for W22 per CO_W14_process_grep_verify 10+ cumulative:(1)Read plan literal acceptance criteria;(2)Grep code base for referenced files / functions / patterns;(3)Surface mismatches via Karpathy §1.1 think-before-coding upfront;(4)Document deviations in plan §7 changelog at plan kickoff;(5)Adjust acceptance criteria per actual reality。**Per-page H7 verification gate formalized** — every F-deliverable acceptance criteria 包含 `CLAUDE.md §3.2.1 H7 fidelity 7-item self-verify + user-eye side-by-side verify`;NO「smoke-user-deferred」allowance for fidelity itself(only multi-viewport responsive細項 / dark-mode drift / Playwright interactive flow can be deferred)。 |
| **2026-05-18 D1** | AI per user directive | **W20-era residual planning audit landed** post user-eye `/chat` fidelity audit catching the F4 ChatHeader silent drift(`fee7836` 2026-05-18 ChatHeader right-side `Citations seg-toggle` → mockup CRAG switch + Show images switch + Focus Eye + Sources BookOpen)。7 contamination signals(D1-D7)identified in W22 plan + checklist text — all inherited from W20/W21 plan文字 without per-line mockup grep verify at W22 kickoff(meta-irony:`Pre-active-flip 5-step` formalized D0 but not applied to plan-text itself,only to code-vs-spec at active-flip time)。 **Fixes landed this changelog entry**:F4.3 "toggle UI 對齊 mockup" → "**NO** user-facing toggle UI per mockup ChatHeader" + state-machine-preserved + reader-only localStorage + default `inline`;F4.2 W20 component identity list `<ConversationHistory>...<CragStrip>` → mockup actual decomposition `ConversationHistoryPanel + ChatHeader + ChatThread + MessageRow + SourcesStrip + CitationPanel + ScreenshotModal + ChatComposer` inlined per mockup single-file pattern;F4.2 obsolete W20 components DELETE list explicit;F5.3 Rule-of-3 wizard primitive promotion **conditionalize** on mockup-4-wizards styling 一致 verify(else defer W23+);§5 dependency text + per-page workflow standard updated:**F1 mid-session CSS-first pivot baseline**(mockup `styles.css` 1073 lines verbatim as `styles-mockup.css` 1048 lines + mockup CSS classes drive visual layer + shadcn primitives only where Radix a11y benefits + Tailwind utility for one-off layout)— previous "shadcn primitives + Tailwind tokens" only-mention under-represented actual approach;Per-page workflow #6 NEW explicit「mockup is canonical;do not invent a UI surface mockup doesn't have」guard with F4 ChatHeader as named example。**Process amendment**:Pre-active-flip 5-step now applies **recursively** to plan-text at plan kickoff,not just at code time(catch W20-era residual text before it propagates to implementation)。**Cross-page propagation risk acknowledged**:F5-F8 acceptance criteria may have similar W20-inheritance — D6(F1.2 UserMenu dropdown content「preserving」)deferred to F1.9 user-eye verify;F5b-F8 each F-deliverable kickoff must read mockup decomposition first before kickoff plan-text refinement。 |

---

**Plan ready for F1 kickoff.** F0 cascade landed at this commit;F1 AppShell rebuild starts next session(or continuation per user direction)。每 F-deliverable kickoff time refine acceptance criteria + identify NEW components per mockup component list inspection。

**Per-page workflow standard**(applies F1-F7,F1 mid-session CSS-first pivot baseline):
1. Open `references/design-mockups/EKP Platform.html#<route>` in Chrome tab L(via `localhost:8080`)
2. Open `localhost:3001/<route>` in Chrome tab R
3. Read `references/design-mockups/ekp-page-*.jsx` corresponding file for **mockup's actual decomposition**(⚠️ NOT W20 / W21 abstraction names — mockup decomposition wins per H7)
4. Read existing `frontend/app/(app)/<route>/page.tsx` to identify PRESERVE(data hooks + API client + state)vs REBUILD(presentation);DELETE existing components that don't match mockup decomposition(per Karpathy §1.3 surgical — orphans manufactured by your rebuild get cleaned)
5. Rebuild presentation 100% 對齊 mockup using **mockup CSS classes**(`styles-mockup.css` verbatim adoption — `.btn .card .field .input .label .hint .seg .badge` etc.)+ **shadcn primitives** where Radix a11y benefits + **Tailwind utility** for one-off layout + inline `style={{}}` for one-off mockup details not covered by CSS classes
6. **Mockup is canonical**:if mockup ChatHeader has CRAG switch + Show images switch + Focus Eye + Sources BookOpen,that's the ChatHeader — do NOT add a W20-inherited Citations seg-toggle because "preserving W20 surface" was in some earlier plan text
7. H7 7-item self-verify each item(layout / spacing / typography / color tokens / interaction states / responsive / a11y)
8. User-eye side-by-side verify before tick checklist(NEW gate per W21 retro;NO smoke-user-deferred)
9. Commit
10. Day-N entry in progress.md
