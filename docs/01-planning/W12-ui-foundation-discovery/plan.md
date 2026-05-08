---
phase: W12-ui-foundation-discovery
name: "UI Foundation & Discovery — Phase 1 of 4 in W12-W15 UI Tier 1 expansion sprint cycle (post architecture.md v5.1→v6 amendment)"
sprint_week: W12
start_date: 2026-06-16             # tentative — assumes W11 D5 closeout 2026-06-13 + 1-day buffer
end_date: 2026-06-20               # 5 working days(possibly +2 if W13 absorb 1-2 days kick-off carry)
status: closed                     # `closed` 自 W12 D5 closeout 2026-06-10 night cont 3 — Phase Gate PASS WITH F4.13 USER-DEFERRED CAVEAT verdict landed;5 phase batches(W11 closeout + W12 D1+D2+D3+D4+D5)collapsed into real-calendar 2026-06-10 single session per pivot momentum stakeholder authorization
spec_refs:
  - architecture.md v6 §5             # UI Specifications expanded(9 views)
  - architecture.md v6 §5.1           # Visual Identity Strategy(tokens.ts pattern)
  - architecture.md v6 §5.9-§5.11     # NEW Landing / Login / Register views
  - architecture.md v6 §13.5          # ADR-0006 shadcn/ui from Day 1(promise being fulfilled)
  - architecture.md v6 §13.12         # v5.1→v6 amendment trigger
  - ADR-0014                          # Hybrid auth(SSO + self-register)
  - ADR-0015                          # UI Tier 1 expansion 9 views
prior_phase: W11-staged-rollout-25
related_artifacts:
  - docs/01-planning/W11-staged-rollout-25/progress.md       # W11 D2 cont UI gap surface entry + stakeholder ack 2026-06-10
  - docs/01-planning/W11-staged-rollout-25/plan.md           # Plan changelog 2026-06-10 F6.3 deviation
  - docs/adr/0014-hybrid-auth-sso-plus-self-register.md      # Sister ADR
  - docs/adr/0015-ui-tier-1-expansion-dify-leaning.md        # Sister ADR
  - docs/architecture.md v6                                   # Spec amendment landed 2026-06-10
  - frontend/.npmrc                                           # W11 D2 cont local dev unblock(hoisted layout)
  - frontend/app/api/backend/[...path]/route.ts               # W11 D2 cont local dev proxy(R8 cert bypass)
  - references/dify/                                          # Layout pattern reference(read-only,per ADR-0010)
---

# Phase W12 — UI Foundation & Discovery(Phase 1 of 4 UI sprint cycle W12-W15)

> **Plan version**:1.0(draft 2026-06-10 W11 D2 cont — rolling JIT per CLAUDE.md §10 R1)
> **Owner**:Chris(stakeholder + tech lead)+ AI(implementation + visual decision proposals per User decision 2026-06-10)
> **Approved by**:_(pending W11 D5 closeout sign-off + ADR-0014/0015 Stakeholder ack land + Q22 email vendor decision land)_

---

## 1. Scope(rolling-JIT W11 D2 cont draft post architecture.md v5.1→v6 amendment)

W12 = **UI Foundation & Discovery sprint** — Phase 1 of 4-sprint UI Tier 1 expansion(W12-W15)。Goals:

- **Discovery**:visual identity finalize(tokens.ts populate from initial proposals)+ design reference doc + per-view wireframe sketches(low-fi)
- **Foundation**:shadcn/ui install + components.json setup + 12-15 base components + admin shell layout + tokens consume migration on existing pages

**Out of W12 scope**(absorbed by W13-W15):
- New view implementation(Landing / Login / Register / Chat refactor)— W13
- Admin views polish(Dashboard / KB List / KB Detail 5-tab)— W14
- Eval Console + Debug View polish + responsive + a11y + E2E — W15

**Pre-condition for W12 promotion**(等 W11 D5 closeout):
- W11 D5 closeout sign-off + W11 retro 7 sections complete
- ADR-0014 + ADR-0015 status `Accepted`(landed 2026-06-10 commit `44a52cb`)
- architecture.md v6 amendment landed(commit `49a634b`)
- Q22 email vendor decision land(W12 D1-D2 sub-deliverable per F1)

## 2. Deliverables(F1-F5)

### F1 — Q22 email vendor decision + W12 phase plan validate

- **Component(s)**:governance(decision-form.md amendment)
- **Spec ref**:ADR-0014 §「Email Verification Service vendor decision(OQ-Q22 NEW)」 + architecture.md v6 §3 component list amendment
- **OQ deps**:Q22 NEW(pending W12 D1-D2 land)
- **Acceptance criteria**:
  - F1.1 Q22 added to `decision-form.md`(Section 1 Stakeholder Decisions)w/ Azure Communication Services vs SendGrid trade-off table
  - F1.2 Q22 default-if-unanswered = Azure Comm Service(per ADR-0014 + spec §13 Azure-native preference per §5.2 H2)
  - F1.3 Q22 Resolved by W12 D2(decision via stakeholder approve cycle OR default activate)
  - F1.4 architecture.md v6 §3 amend C13 Email Verification Service component card per Q22 outcome
  - F1.5 W12 plan.md `status: draft → active` flip + Stakeholder ack 2026-06-10 W11 D2 cont referenced
- **Definition of Done**:Q22 status `Resolved` in decision-form.md;architecture.md v6 §3 reflects vendor pick;W12 plan active;0 governance gap
- **Estimated effort**:0.5-1 day(W12 D1-D2)

### F2 — Visual identity tokens.ts finalize + design reference doc

- **Component(s)**:**C10** chat UI primitives(infrastructure-only;no view changes)+ governance
- **Spec ref**:architecture.md v6 §5.1 Visual Identity Strategy + ADR-0015 §「Dify-leaning aesthetic commit」
- **OQ deps**:none(internal visual decisions per User decision 2026-06-10「I propose, you approve」)
- **Acceptance criteria**:
  - F2.1 `frontend/lib/theming/tokens.ts` populate per architecture.md v6 §5.1 example structure:
    - `colors`:primary / accent / background / foreground / muted / border / success / warning / destructive(全部 oklch values per spec preference)
    - `radius`:sm 0.25 / md 0.5 / lg 0.75rem(per spec — "更銳利感 vs Dify default")
    - `fontFamily`:Inter sans + JetBrains Mono(per spec — distinct from Dify SF Pro)
    - `spacing`:Tailwind default
    - shadow / motion tokens(extend per shadcn/ui v0 default)
  - F2.2 Design reference doc `docs/02-architecture/ui-design-reference-v6.md` create:
    - 9 views layout sketches(low-fi ASCII diagrams + key component inventory per view)
    - Cross-view consistency rules(sidebar pattern / breadcrumb pattern / toast pattern / empty state pattern)
    - Component-to-view mapping table(which shadcn primitives used where)
    - Dify reference path index(layout patterns to mirror per architecture.md v6 §5.5.1-§5.5.5 + §5.8 + spec sections;Dify branding NEVER copied per ADR-0010)
  - F2.3 AI propose visual decisions → User approve cycle:
    - Primary color(EKP-distinct;not Dify blue)
    - Accent color(supplementary brand)
    - Typography hierarchy(heading scale)
    - Initial dark mode strategy(W12 dark mode 暫 deferred 到 W15 polish — confirm acceptable)
- **Definition of Done**:tokens.ts production-ready w/ visual decision rationale comments;design reference doc 9 sections complete;User explicit approve recorded(progress.md Day-N entry)
- **Estimated effort**:2-3 days(W12 D2-D4)

### F3 — shadcn/ui foundation setup + 12-15 base components

- **Component(s)**:**C10** chat UI + **C09** admin views shared infrastructure
- **Spec ref**:architecture.md v6 §13.5 + ADR-0006 + ADR-0015 §「shadcn/ui foundation commit」+ CLAUDE.md §3.2(shadcn/ui only)
- **OQ deps**:none(F2 tokens.ts must land first for theme integration)
- **Acceptance criteria**:
  - F3.1 `pnpm dlx shadcn@latest init` run in `frontend/` w/ New York style + Tailwind CSS variables + tokens.ts integration
  - F3.2 `frontend/components.json` 配置 → tracked in git
  - F3.3 12-15 base components installed via `pnpm dlx shadcn@latest add`:
    - **Form**:Button、Input、Textarea、Label、Select、Switch、Slider、Checkbox
    - **Layout**:Card、Separator、Sheet、Dialog、Tabs
    - **Feedback**:Badge、Toast(via sonner per shadcn default)、Skeleton
    - **Nav**:Dropdown、Breadcrumb(if shadcn支援;else custom)
  - F3.4 全部 shadcn components 在 `frontend/components/ui/` 目錄;tokens.ts 整合 via Tailwind CSS variable layer
  - F3.5 Smoke verify:Render `<Button variant="default">Test</Button>` 喺 admin page → visual match tokens primary
  - F3.6 Type-check pass(`pnpm type-check` clean — no shadcn-introduced TS error)
- **Definition of Done**:`frontend/components/ui/` populated w/ 12-15 components;type-check clean;smoke render verified;tokens.ts driving theme
- **Estimated effort**:1-2 days(W12 D4-D5)

### F4 — Admin shell foundation + existing pages tokens migration

- **Component(s)**:**C09** admin views + **C10** chat UI
- **Spec ref**:architecture.md v6 §5.3(Admin Dashboard sidebar pattern reference Dify Image 4)+ CLAUDE.md §3.2(no hardcoded colors)
- **OQ deps**:F2 + F3 must land first
- **Acceptance criteria**:
  - F4.1 `frontend/components/nav/admin-shell.tsx` rebuild w/ shadcn primitives(replace existing 3-component placeholder):
    - Sidebar nav(persistent on `/admin/*`)using shadcn `Sheet` (mobile) + flat sidebar (desktop)
    - Header w/ breadcrumb + user-menu(reuse existing `auth/user-menu.tsx`,wrap in shadcn Dropdown)
    - Main content area outlet
  - F4.2 Existing pages refactor to use tokens.ts(NO logic change,只 visual primitive substitution):
    - `frontend/app/page.tsx`(Chat,322 lines)— replace hardcoded `oklch(...)` with tokens-referenced classes;keep functional logic(streamQuery / MessageBubble / CitationCard / ScreenshotModal)
    - `frontend/app/admin/page.tsx`、`frontend/app/admin/kb/page.tsx`、`frontend/app/admin/kb/[id]/page.tsx`、`frontend/app/admin/kb/[id]/upload/page.tsx`、`frontend/app/admin/kb/new/page.tsx`、`frontend/app/eval/page.tsx`、`frontend/app/debug/[traceId]/page.tsx`
  - F4.3 Visual sanity check after refactor:
    - All views render w/ tokens-driven colors(no inline `oklch` strings)
    - No regression in functional behavior(KB list / chat stream / KB detail / etc still work)
    - Browser smoke test through `localhost:3001`(per W11 D2 cont local dev workflow)
- **Definition of Done**:admin-shell production-ready w/ shadcn primitives;all 8 pages tokens-driven;0 hardcoded oklch leakage(grep clean);no functional regression
- **Estimated effort**:1-2 days(W12 D5 - W13 D1 absorb if needed)

### F5 — Phase Gate closeout + W13-user-facing-views phase folder kickoff

- **Component(s)**:governance
- **Spec ref**:CLAUDE.md §10 R1(rolling-JIT phase folder)+ §10 R5(architectural-adjacent decision via ADR)
- **OQ deps**:F1-F4 complete
- **Acceptance criteria**:
  - F5.1 W12 phase Gate verdict landed(per W11 plan F6.1 pattern;PASS / PARTIAL PASS / FAIL with explicit rationale)
  - F5.2 W12 progress.md retro 7 sections complete(What worked / What didn't / Surprises / Decisions / Carry-overs / Time tracking / Spec ref alignment)
  - F5.3 `docs/01-planning/W13-user-facing-views/{plan,checklist,progress}.md` draft per architecture.md v6 §5.9-§5.11 Landing/Login/Register + §5.2 Chat path move + ADR-0014 hybrid auth backend cascade
  - F5.4 W12 progress.md frontmatter status flipped to `closed`
  - F5.5 OQ Q22 sync to decision-form.md per outcome
- **Definition of Done**:W12 closeout per CLAUDE.md §10 phase lifecycle;W13 folder kickoff;0 unfinished W12 items carry over without R3 changelog entry
- **Estimated effort**:0.5 day(W12 D5 final OR W13 D1 if W12 absorb extra)

---

## 3. Success Criteria(Phase Gate to W13)

W12 phase Gate **PASS condition**:
1. F1 Q22 Resolved + decision-form.md sync ✅
2. F2 tokens.ts production-ready + design reference doc 9 sections complete ✅
3. F3 shadcn/ui installed + 12-15 base components + type-check clean ✅
4. F4 admin shell + existing pages tokens-driven + 0 hardcoded oklch leak + no functional regression ✅
5. F5 closeout retro + W13 phase folder kickoff ✅

W12 phase Gate **PARTIAL PASS** acceptable per Karpathy §1.4:
- Visual decision needs more iteration → Q22-equivalent visual OQ created + W13 absorb 1-2 days
- shadcn integration friction(rare;known to work on hoisted layout per W11 D2 cont)→ `node-linker=hoisted` 已 verified
- Existing pages tokens migration partial(7-of-8 pages)→ remaining absorb W13 D1

W12 phase Gate **FAIL condition**:
- F3 shadcn install fails irreparably(Windows env block beyond `.npmrc` hoisted workaround;needs OneDrive remediation)
- F2 visual decisions blocked on user availability(>3 days no decision)— surface to retro
- Q22 vendor decision blocked(both candidates rejected — needs ADR-0016)

## 4. Risks(Phase-Specific)

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| shadcn install on Windows OneDrive 又 fail | Low | High(W12 blocked)| `.npmrc` hoisted layout 已 verified working W11 D2 cont;`pnpm dlx shadcn` should respect hoisted layout |
| tokens.ts visual decisions iterate too long | Medium | Medium(F2 blocks F3 + F4)| AI propose 1-2 round + User approve;若 third iteration needed → freeze v0 → W13 absorb refinement |
| Existing pages tokens migration introduce visual regression | Medium | Low(reversible)| Per-page commit + browser smoke after each;if regression → revert that page only |
| Q22 email vendor decision blocked | Low | Medium(W13 ADR-0014 backend cascade affected)| Default-if-unanswered = Azure Comm Service;W12 D2 deadline force decision OR default activate |
| W11 D5 closeout sign-off delayed | Low | Low(W12 D1 deferred only)| W12 D1-D2 governance work(F1 + F2 design doc)can run parallel without code |

## 5. Day-by-Day Breakdown(rough)

| Day | Date | Focus |
|---|---|---|
| W12 D1 | 2026-06-16 | F1 Q22 decision-form.md amendment + AI propose Azure Comm Service rationale + User decide / default activate |
| W12 D2 | 2026-06-17 | F1 Q22 land + architecture.md v6 §3 amend C13 + F2 design reference doc layout drafts begin |
| W12 D3 | 2026-06-18 | F2 tokens.ts populate + AI propose visual decisions(primary color / typography / radius)+ User approve cycle 1 |
| W12 D4 | 2026-06-19 | F2 tokens.ts finalize + design reference doc 9 view layout sections complete + F3 shadcn `init` |
| W12 D5 | 2026-06-20 | F3 12-15 components installed + F4 admin-shell rebuild + 1-2 page tokens migration |
| W12 D5+ overflow | 2026-06-23+ | F4 remaining pages tokens migration + F5 closeout(absorb W13 D1 if needed) |

## 6. Dependencies on Prior Phase

- **W11 D5 closeout**:Track A IT cred event NOT prerequisite for W12(UI sprint independent of LIVE deploy);W11 phase Gate PASS / PARTIAL PASS pose no blocker
- **architecture.md v6 amendment**:landed 2026-06-10 commit `49a634b` ✅
- **ADR-0014 + ADR-0015**:landed 2026-06-10 commit `44a52cb` ✅
- **W11 D2 cont local dev unblock**:`.npmrc` hoisted layout + `/api/backend` proxy route landed commit `1431e73` ✅(reused for W12 dev workflow)
- **References/dify/**:read-only reference unchanged(per ADR-0010)
- **Q22 email vendor**:NEW pending W12 D1-D2 land(default-if-unanswered = Azure Comm Service)

## 7. Plan Changelog

| Date | Change | Reason | Approver |
|---|---|---|---|
| 2026-06-10 | Initial draft(W11 D2 cont rolling-JIT post stakeholder approve cycle for v5.1→v6 amendment + ADR-0014/0015)| Per CLAUDE.md §10 R1 rolling-JIT;W12 phase pivot from `production-launch` → `ui-foundation-discovery` per W11 plan changelog 2026-06-10 deviation entry;UI gap surface during W11 D2 cont Mode B local dev unblock | Chris(acting as Stakeholder per past sessions authorization pattern;explicit ack 2026-06-10 evening session)|
| 2026-06-10 evening | Status `draft → active` flip + W12 D1 implementation start | W11 D2 cont evening early closeout cascade(commit `4ec56d5`)— W11 PARTIAL PASS landed + ADR-0014/0015 sister ADR cycle landed(`44a52cb`)+ architecture.md v6 amendment landed(`49a634b`)→ 3 pre-conditions cleared;W12 D1 F1 Q22 email vendor decision implementation start same-session per stakeholder authorization 2026-06-10 evening | Chris(stakeholder authorization 2026-06-10 evening session;same-session cascade per pivot momentum)|
| 2026-06-10 evening cont | **Dark mode parallel implement override**(W12 D4 land light + dark variants concurrently)+ W12 D2 plan-day collapse into W12 D1 calendar-day | User explicit override decision per F2 visual identity proposal cycle 1(2026-06-10 evening cont approval cycle):W13-W14 user-facing views(Landing / Login / Register / Chat refactor)build dark-aware avoid W15 polish window 大幅 retrofit;scope expand ~0.5 day acceptable per stakeholder authorization。W12 D2 plan-day F2 work(visual decisions + tokens.ts populate + design reference doc)collapsed into W12 D1 calendar-day per pivot momentum(non plan deviation per W12 plan §5 caveat tentative dates)。**Visual identity Option C "Warm Charcoal + Coral Accent"** ratified W12 D2 cycle 1(achromatic primary hue 285 + warm coral accent hue 25;Notion-leaning editorial direction;distinct from Dify blue + most SaaS achromatic primary signature)| Chris(stakeholder authorization;F2 visual identity ratification cycle 1)|
| 2026-06-10 night | **F3 scope adjustment — 12-15 base components target → actual 19 components installed** + W12 D3 plan-day collapse into W12 D1 calendar-day | Design reference doc §4 component-to-view mapping table(W12 D2 commit `1ac17e6`)identifies 19 essential primitives across 9 views(plan F3.3 "12-15" 為 estimation rough cap;design ref doc 為 authoritative count post architecture analysis)。Scope add Avatar(V1/V2/V3/V4/V5/V7 user-menu cross-view essential)+ confirm Breadcrumb / Dropdown-menu(originally counted)。Effort delta minimal(`pnpm dlx shadcn@latest add` batch);tokens.ts integration 6 missing tokens(secondary / card / popover pairs)補齊 audit-driven 屬 F3.7 acceptance scope。W12 D3 F3 work collapsed into W12 D1 calendar-day per pivot momentum(plan §5 caveat tentative dates)| Chris(stakeholder authorization same-session pivot momentum)|
| 2026-06-10 night cont 2 | **F4 admin shell rebuild + 8 pages tokens migration complete** + F4.13 functional regression test user-deferred + W12 D4 plan-day collapse into W12 D1 calendar-day | F4.1-F4.12 全部 acceptance met(admin-shell + user-menu rewrite with shadcn Sheet/Breadcrumb/DropdownMenu/Avatar;8 pages oklch hardcoded → token classes;Send/Stop/Create/Save/Upload Buttons → shadcn Button variants;grep oklch=0 in frontend/app/** strict clean;type-check 0 errors)。F4.13 functional regression user-deferred per CLAUDE.md §13 dev server policy(`pnpm dev` 屬 long-running Node server 同 Claude Code 衝突)— alternative AI verification = type-check + grep + import resolution clean。W12 D4 work collapsed into W12 D1 calendar-day per pivot momentum;W12 D5 (F5 Phase Gate closeout + W13 phase folder kickoff) advanced into next iteration | Chris(stakeholder authorization same-session pivot momentum;F4.13 user-deferred per CLAUDE.md §13)|
| 2026-06-10 night cont 3 | **W12 phase Gate PASS WITH F4.13 USER-DEFERRED CAVEAT verdict landed + retro 7 sections complete + W13-user-facing-views phase folder kickoff + W12 frontmatter active → closed cascade** + W12 D5 plan-day collapse into W12 D1 calendar-day | F5.1-F5.6 全部 acceptance met(Phase Gate verdict 5 conditions evaluation per plan §3 + caveat明示;retro 7 sections complete with 5 What worked / 4 What didn't / 5 Surprises / 7 Decisions / 19 Carry-overs categorized W13/W14/W15/W16+/external + Time tracking 7x under-budget calibration + Spec ref alignment table;W13 phase folder skeleton plan + checklist + progress.md draft per CLAUDE.md §10 R1 rolling-JIT;W12 frontmatter close cascade plan + checklist + progress)。W12 D5 work collapsed into W12 D1 calendar-day per pivot momentum;5 phase batches(W11 closeout + W12 D1+D2+D3+D4+D5)full single calendar-day single session 2026-06-10 final closeout。W13 D1 implementation start trigger = next session OR same-day cont per pivot momentum | Chris(stakeholder authorization;W12 closeout PASS WITH CAVEAT verdict)|

---

**Lifecycle reminder**:呢份 plan `status=closed` 自 2026-06-10 night cont 3 W12 D5 closeout(Phase Gate PASS WITH F4.13 USER-DEFERRED CAVEAT verdict per progress.md retro § F5.1)。重大 deviation 已入第 7 節 changelog。W13-user-facing-views phase folder kickoff(per CLAUDE.md §10 R1 rolling-JIT)→ `docs/01-planning/W13-user-facing-views/{plan,checklist,progress}.md` draft `status=draft` ready for W13 D1 active flip post stakeholder authorization。Sister sprint W14/W15 phase folders **唔會** pre-create(rolling JIT discipline preserved)。
