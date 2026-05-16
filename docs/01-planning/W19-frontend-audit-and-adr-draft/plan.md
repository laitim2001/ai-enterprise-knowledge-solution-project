---
phase: W19-frontend-audit-and-adr-draft
name: "Frontend Implementation Audit + ADR Drafts — full `references/design-mockups/` audit(17 ekp-page-*.jsx + DESIGN_README + PAGE_INVENTORY)→ backend gap map across 14 Tier 1 routes → 5 H1 ADR drafts(0025–0029)→ Wave A/B/C breakdown(W20–W22) + Tier 2 disabled-affordance catalog → Chris approve → W20+ kickoff. NO code change to `frontend/` in this phase — audit + planning only."
sprint_week: W19
start_date: 2026-05-16              # real-calendar — kicked off post-W18 closeout per user directive 2026-05-16 同 design-mockups landed `08b74af` 同一日(no Track A IT cred dependency — frontend implementation work is mock-auth default per user岔口 2 decision)
end_date: 2026-05-23                # ~1 week — pure audit + ADR drafting + planning;real-calendar collapse possible per W12-W15-W17-W18 precedent(frontend audit + 5 ADR drafts may land in 2–3 days if momentum clean);frontmatter is a window not commitment
status: closed                    # `active` from kickoff 2026-05-16(per user directive + AskUserQuestion answer)→ `closed` 2026-05-16(F6 Chris approval Chris-pick 4 strategic decisions:ADR-0027 Option A + ADR-0026 Option B + ADR-0031 Option B + ADR-0029 Option C;6 ADRs Accepted;Wave C MUST split into C1+C2 per F4 §3.6 trigger due to Option A+B combined ~42 backend days exceeds single phase budget;phase Gate = PASS WITH WAVE-C-SPLIT-TRIGGERED CAVEAT)
spec_refs:
  - architecture.md v6 §5            # UI Specifications — the spec being audited against the mockup;W19 surfaces deviations,does not amend(amendments land in the F3 ADR drafts → W20+ phase implementation)
  - ADR-0024                         # Unified application shell IA(Accepted 2026-05-10)— the IA layer is LOCKED;mockup adheres(5-module sidebar + topbar + main + Cmd+K + flat URLs)
  - ADR-0015                         # UI Tier 1 expansion Dify-leaning(amended by ADR-0024)— the 9-view baseline being expanded by the mockup;the 3 expansion points(KB Detail 5→8 tabs / Settings v1→6 tabs / `/users` NET NEW Tier 1.5)become F3 ADR drafts
  - ADR-0014                         # Hybrid auth — frontend auth flow unchanged;the W22 Wave C "mock + real both ship" decision builds on this
  - ADR-0022                         # auth-transport hardening(cookie + CSRF + `/auth/refresh` rotation)— Settings → Identity & Auth tab reads this for the "transport" sub-section
  - ADR-0023                         # KB Manager + users_repo Postgres persistent backing — RBAC table additions(`/users` Tier 1.5)build on this(new `roles` / `role_permissions` / `groups` / `audit_log` tables)
  - references/design-mockups/DESIGN_README.md   # the prototype's self-document — entry point for F1 audit
  - references/design-mockups/PAGE_INVENTORY.md  # per-route Cn mapping + Tier 1/2 status — entry point for F2 backend gap map
prior_phase: W18-app-shell-ia       # closed 2026-05-11(phase Gate PASS WITH SMOKE-USER-DEFERRED CAVEAT)— provides the LOCKED IA chrome that W20+ implementation work fills in;W16 F1-F4 still Track-A-blocked(parallel,not predecessor;W19+W20-W22 are independent per user 岔口 2 = mock-auth default + W22 ship both)
related_artifacts:
  # source-of-truth for the audit
  - references/design-mockups/EKP Platform.html
  - references/design-mockups/DESIGN_README.md
  - references/design-mockups/PAGE_INVENTORY.md
  - references/design-mockups/ekp-shell.jsx
  - references/design-mockups/ekp-page-dashboard.jsx
  - references/design-mockups/ekp-page-chat.jsx
  - references/design-mockups/ekp-page-kb.jsx
  - references/design-mockups/ekp-page-kb-extras.jsx
  - references/design-mockups/ekp-page-kb-new.jsx
  - references/design-mockups/ekp-page-doc-detail.jsx
  - references/design-mockups/ekp-page-misc.jsx
  - references/design-mockups/ekp-page-eval.jsx
  - references/design-mockups/ekp-page-trace.jsx
  - references/design-mockups/ekp-page-settings-tabs.jsx
  - references/design-mockups/ekp-page-users.jsx
  - references/design-mockups/ekp-page-auth.jsx
  - references/design-mockups/ekp-page-labs-1.jsx
  - references/design-mockups/ekp-page-labs-2.jsx
  - references/design-mockups/ekp-data.jsx           # mock data shape vs `backend/api/schemas/*.py` real shapes — F2 cross-ref
  - references/design-mockups/styles.css             # mock tokens vs `frontend/lib/theming/tokens.ts` real tokens — F1 verify
  - references/design-mockups/tweaks-panel.jsx       # the design-time panel(NOT shipping)— F1 audit confirms it's design-only
  # F1-F5 audit deliverables(W19-owned, NEW)
  - docs/01-planning/W19-frontend-audit-and-adr-draft/audit/W19-mockup-jsx-audit.md
  - docs/01-planning/W19-frontend-audit-and-adr-draft/audit/W19-backend-gap-map.md
  - docs/01-planning/W19-frontend-audit-and-adr-draft/audit/W19-wave-breakdown.md
  - docs/01-planning/W19-frontend-audit-and-adr-draft/audit/W19-tier2-disabled-affordance-catalog.md
  # F3 ADR drafts(W19-owned, NEW — Proposed status, await Chris approval at F6)
  - docs/adr/0025-kb-detail-8-tabs-expansion.md           # KB Detail 5→8 tabs(Images / Chunking Lab / Access)
  - docs/adr/0026-settings-6-tab-hub-and-connections-backend.md   # Settings v1 thin → 6-tab hub + backend management endpoints group
  - docs/adr/0027-users-tier-1-5-rbac.md                # /users NET NEW Tier 1.5(Members / Roles & permissions / Groups / Audit log)+ backend RBAC scope
  - docs/adr/0028-kb-new-5-step-wizard.md                # /kb/new 5-step wizard(Identity / Format & chunking / Multimodal / Retrieval defaults / Review)+ multimodal Tier 1/2 split
  - docs/adr/0029-doc-detail-3-pane-layout.md           # /doc-detail/[kbId]/[docId] 3-pane(outline / chunks / inspector) + route topology change vs spec §5.5.2
  # cross-ref backend & component
  - backend/api/schemas/                              # real Pydantic shapes the mockup aligns against — F2 verify per-schema
  - backend/api/routes/                                # current endpoint inventory — F2 gap analysis
  - docs/02-architecture/COMPONENT_CATALOG.md          # 13 Cn baseline — F3 ADRs may amend(C02 / C09 / C11 + possibly new C14 Settings Service or C16 Users Service)
  - docs/02-architecture/components/C09-admin-ui.md   # W19 audit may amend(8-tab KB Detail / 6-tab Settings / /users)— but C09 design-note updates land in W20+ implementation phases,not here
  - docs/02-architecture/components/C10-chat-ui.md    # Chat features in mockup(conversation-history sidebar = Beta+,inline image cards,Sources strip,Feedback widget)
  - docs/02-architecture/components/C11-identity-access.md  # (if exists)— RBAC + Identity & Auth Settings tab
  # cross-ref planning
  - docs/01-planning/W18-app-shell-ia/                # template for W19 phase folder structure(plan + checklist + progress shapes)
  - docs/01-planning/PROCESS.md                       # R1-R5 binding rules — W19 must satisfy R1(plan committed)+ R5(ADR drafts before any W20+ implementation)
  - CLAUDE.md                                          # §5.1 H1 + §10 R1-R5 governance — W19 = the H1 ADR + R1 plan + R5 ADR-before-closeout fulfillment for the design-mockups implementation work
  - docs/12-ai-assistant/01-prompts/01-session-start.md  # F6 — §10 W19 row added + §11 carry-overs + Last-Updated
---

# Phase W19 — Frontend Implementation Audit + ADR Drafts

> **Plan version**:1.0(draft 2026-05-16 — rolling JIT per CLAUDE.md §10 R1;kicked off post-W18-closeout per user directive 2026-05-16 same-day as design-mockups landed commit `08b74af`)
> **Owner**:Chris(Tech Lead + stakeholder)+ AI(audit + ADR draft)
> **Approved by**:Chris — user directive 2026-05-16「現在我們可以先把 design-mockups 的內容 先進行實作」+ AskUserQuestion answer "W19 audit-and-adr-draft phase folder kickoff(推薦)" + "Mock-auth 繼續做 default,W22 同時 ship mock + real(推薦)"= the「approved + write ADR」+「now plan it」authorization per CLAUDE.md §5.1 H1。

---

## 1. Scope

W19 = **the planning phase for the design-mockups → real-`frontend/` implementation work** — full audit of `references/design-mockups/`(17 `ekp-page-*.jsx` + `DESIGN_README.md` + `PAGE_INVENTORY.md`)against `architecture.md v6 §5` spec + `backend/api/schemas/*.py` + `backend/api/routes/*` + the 13-Cn `COMPONENT_CATALOG.md`,**surface every deviation as a draft ADR**(H1 architectural change per §5.1),map backend gaps,break the implementation into W20+ Waves,and catalog the Tier 2 disabled-affordance patterns. **NO code change to `frontend/` in this phase** — audit + planning + ADR drafts only。 Approval gate at F6 — Chris reviews all artifacts + 5 ADR drafts → flips them Proposed → Accepted → authorizes W20-frontend-wave-a kickoff(per §5.1 H1 ADR-before-implement discipline).

Goals(= W19 F0–F6,no ADR-style D1-Dn mapping since W19 is the **plan phase**, not the implementation of any single ADR):

- **F0 Kickoff cascade** — `plan.md` + `checklist.md` + `progress.md` + `audit/` subfolder + `session-start.md` §10 W19 row added at kickoff(not at closeout — the active-phase signal needs to land Day 0 so concurrent AI sessions see the in-progress state)+ ADR-0025 through ADR-0029 reserved entries in `docs/adr/README.md`(slots only — content drafted in F3).
- **F1 Full mockup audit per `.jsx`** — read all 17 `ekp-page-*.jsx` files + `ekp-shell.jsx` + `ekp-data.jsx` + `styles.css` + `tweaks-panel.jsx`;for each route extract:(a) component structure + state shape;(b) backend dependency(every `fetch` / `useQuery`-equivalent / mock data source);(c) Tier 1 vs Tier 2 boundary(prototype's own "TIER 2 PREVIEW" badges + the implicit `/labs/*` separation);(d) IA-compliance check(every authed route inside `<AppShell>` per ADR-0024;every auth page outside)+ (e) visual identity check(`oklch()` tokens only, no Dify colours per H3, no hardcoded hex);(f) anything that deviates from `architecture.md v6 §5` or `COMPONENT_CATALOG.md`. Output = `audit/W19-mockup-jsx-audit.md`(per-route table + deviation summary).
- **F2 Backend gap map** — 14 Tier 1 routes(per `PAGE_INVENTORY.md`)× backend endpoint dependency check vs `backend/api/routes/*` + Pydantic schemas in `backend/api/schemas/*.py`. Each surface gets one of:(a) **supported**(real endpoint + matching schema);(b) **partial**(endpoint exists, schema gaps or stub data);(c) **missing**(no endpoint yet — surface is the gap, e.g. `/health` per-component connectivity / Settings → Connections / Settings → API Keys / `/users` RBAC tables);(d) **mock-only**(prototype mock data, no real backend planned for Tier 1 — e.g. Conversation History sidebar = Beta+ per PAGE_INVENTORY). Output = `audit/W19-backend-gap-map.md`(per-route table + cumulative backend-work-needed list classified by "blocks Wave A/B/C" vs "Tier 2 / deferred").
- **F3 ADR drafts × 5**(Status = `Proposed`,await F6 Chris approval):
  - **ADR-0025 KB Detail 5→8 tabs expansion** — Images / Chunking Lab / Access tabs;amends `architecture.md v6 §5.5`;C02 / C03 scope expansion notes;Access tab depends on `/users` RBAC(ADR-0027)so a hard dep order documented
  - **ADR-0026 Settings v1 thin → 6-tab hub + Connections backend** — Profile / Appearance / Connections / Identity & Auth / API Keys & Quotas / Account;the **Connections + API Keys + Identity & Auth** tabs are the H1 weight(secret management UI + Key Vault rotation + connection-test endpoints + API key CRUD);likely new Cn or scope expansion on C12 DevOps;the 2 strategic岔口 unresolved(read-only view vs fully-editable)= ADR draft option set,Chris picks one at F6
  - **ADR-0027 /users Tier 1.5 RBAC** — Members + Roles & permissions matrix(3 roles per prototype:Admin / Editor / User;Power User = Tier 2 disabled)+ Groups + Audit log;new Postgres tables(`roles` + `role_permissions` + `groups` + `group_members` + `audit_log`);C11 scope expansion + possibly new C16 Users Service;the strategic岔口 unresolved(full RBAC vs 3-role hard-coded minimum)= ADR draft option set,Chris picks one at F6
  - **ADR-0028 /kb/new 5-step wizard + multimodal Tier 1/2 split** — Identity → Format & chunking → Multimodal → Retrieval defaults → Review;amends `architecture.md v6 §5.5.3`(spec was 3-step IN the KB Detail Pipeline tab — prototype 5-step is its own route);the **Multimodal step** mixes Tier 1(embedded image extract + SHA256 dedup + "off — use source alt_text only")+ Tier 2(Vision captioning / slide screenshots / perceptual hash dedup)— enumerate the Tier 1/2 boundary explicitly + H4 disabled-affordance pattern
  - **ADR-0029 /doc-detail 3-pane layout** — outline / chunks / inspector;amends `architecture.md v6 §5.5.2`(spec was `/admin/kb/[id]/chunks/[doc_id]` chunk inspector — prototype has its own `/doc-detail/[kbId]/[docId]` 3-pane route with richer content);C09 §5.5.2 scope notes
- **F4 Wave breakdown** — W20 Wave A / W21 Wave B / W22 Wave C / W23+ Wave D scope drafts per `PAGE_INVENTORY.md` "Implementation priority (suggested)";per Wave list:routes + components + backend deps from F2 + ADR refs from F3 + acceptance criteria sketch + estimated phase budget;**explicit "Wave C ships mock + real auth both" note per user岔口 2 decision**;**W23+ Tier 2 Labs hold for post-Beta-launch governance per Q12**. Output = `audit/W19-wave-breakdown.md`(4 Wave skeleton + dep ordering + which岔口 unblocks which Wave).
- **F5 Tier 2 disabled-affordance catalog** — enumerate every "TIER 2 PREVIEW" badge + disabled element in the prototype(per PAGE_INVENTORY.md "What's NOT in the prototype" + "Tier 1 + Tier 2 mixed routes" + the explicit `/labs/*` set);for each:the **affordance pattern**(native `disabled` + tooltip / `aria-disabled` + click-intercept toast / coral-badge present-but-noninteractive),the **H4 boundary rationale**,the **Tier 2 trigger condition**(per `architecture.md §11` trigger matrix). Output = `audit/W19-tier2-disabled-affordance-catalog.md`. This becomes a **reusable spec** for every Wave-A/B/C implementation to consult,so we don't reinvent the affordance shape per surface.
- **F6 Phase closeout — Chris approve + W20+ kickoff trigger**:Chris reviews `audit/W19-mockup-jsx-audit.md` + `audit/W19-backend-gap-map.md` + `audit/W19-wave-breakdown.md` + `audit/W19-tier2-disabled-affordance-catalog.md` + 5 ADR drafts;answers the 2 strategic岔口(/users RBAC scope + Settings Connections scope);flips ADR-0025–0029 Status = Proposed → Accepted(if changes needed, Chris pushes revisions before flip);authorizes W20-frontend-wave-a phase folder kickoff. W19 frontmatter `active` → `closed`. W19 retro + 7 sections;`session-start.md` §3 / §10 / §11 / §12 / Last-Updated / Update-history catch-up.

**Out of W19 scope**(stay W20+ / Tier 2 / future):

- **NO code change to `frontend/`** — W19 is plan + audit + ADR drafts only;the moment any `.tsx` lands under `frontend/` is W20 Wave A kickoff
- **NO new backend endpoint or table** — the **gap map identifies them**,implementation is W20–W22 sub-phases
- **NO amendment to `architecture.md v6 §5`** — the F3 ADR drafts will *propose* the amendments;the actual `architecture.md` inline-tag edit lands when each ADR is Accepted in the corresponding W20+ phase kickoff(per the §3.4 / §3.7 / ADR-0024 W18 inline-tag pattern)
- **NO `COMPONENT_CATALOG.md` C09 / C10 / C11 design-note rewrite** — those land per-Wave in W20+ implementation phases
- **NO Tier 2 implementation** — `/labs/*` 8 pages stay prototype reference;Q12 governance trigger post-Beta launch
- **NO Track A IT cred activation** — independent of W19(W16 F1 / R-B1 closure remain in their own track);real MSAL path stays mock until W22 Wave C(per user岔口 2 decision)
- **NO `users_repo` / Postgres schema migration** — ADR-0027 *specifies* the table additions,migration lands in W22 Wave C backend work
- **NO Vitest / Playwright test work** — W19 audit reads existing test state;new tests land per-Wave in W20+

**Pre-condition for W19 promotion**(satisfied 2026-05-16):

- W18-app-shell-ia = closed(phase Gate PASS WITH SMOKE-USER-DEFERRED CAVEAT;ADR-0024 D1-D10 all landed)— the IA chrome that W20+ work fills is LOCKED
- `references/design-mockups/` = landed in repo(commit `08b74af` 2026-05-16)— the source-of-truth for the audit is reachable
- User directive 2026-05-16 = the W19 authorization(Phase classification confirmed via PROCESS.md §1;岔口 1 strategic call deferred to F6 — see Risks below;岔口 2 = "mock-auth default + W22 ship both" already resolved)
- CLAUDE.md v1.5 + session-start.md routing entries for `references/design-mockups/` landed `08b74af`(F1 audit reads from a stable reference path)

## 2. Deliverables(F0-F6)

### F0 — Kickoff cascade(phase folder + ADR README slot reservations)

- **Component(s)**:governance only(no Cn touched in this phase)
- **Spec ref**:CLAUDE.md §10 R1(plan committed before any implementation);PROCESS.md §2(per-phase artifacts)
- **OQ deps**:none
- **Acceptance criteria**:
  - F0.1 NEW `docs/01-planning/W19-frontend-audit-and-adr-draft/{plan,checklist,progress}.md` created with `status: active`(per user directive — the same Day-0-flip pattern as W17 D0 / W18 D0,not the usual draft→active flip)
  - F0.2 NEW `docs/01-planning/W19-frontend-audit-and-adr-draft/audit/` subfolder created(F1–F5 output paths exist before F1 starts → `audit/.gitkeep` if no other file yet)
  - F0.3 `docs/adr/README.md` — reserve ADR-0025 / 0026 / 0027 / 0028 / 0029 slots with Status = `Reserved (W19 F3)`(content empty until F3 fills them;the "Next NNNN" block updates from 0025 → 0030);same pattern as ADR-0013 reservation
  - F0.4 `docs/12-ai-assistant/01-prompts/01-session-start.md` — §10 Sprint Awareness table gets a NEW W19 row(`status: active 2026-05-16`,Default focus = "audit + ADR drafts,no `frontend/` code change"); §12 Milestones table NOT touched at kickoff(milestones row added at F6 closeout per the W18 pattern);Last-Updated + Update-history get the W19-kickoff entry
  - F0.5 No `architecture.md` amendment at W19 kickoff — the F3 ADR drafts *propose* amendments,the amendments land per-ADR in the W20+ kickoff each invokes(different from the W18 pattern where ADR-0024 amendment landed at W18 kickoff because ADR-0024 was already Accepted)
- **Effort estimate**:0.3 day(small — folder + 3 .md skeleton + README slot reservation + `session-start.md` row)
- **Owner**:AI(implementation)+ user(sanity-check the kickoff commit)

### F1 — Full mockup audit per `.jsx`(17 files + shell + data + styles + tweaks)

- **Component(s)**:cross-cutting audit;every Cn the mockup touches(C01–C13 + potentially new C14 Settings / C16 Users)
- **Spec ref**:architecture.md v6 §5 + `references/design-mockups/DESIGN_README.md`(per-file map) + `PAGE_INVENTORY.md`(per-route Cn mapping);CLAUDE.md §1.3 surgical(audit-only,no edit);H3 disambiguation(EKP self-owned prototype,read but don't copy)
- **OQ deps**:none(audit is read-only)
- **Acceptance criteria**:
  - F1.1 `audit/W19-mockup-jsx-audit.md` NEW — per-route table covering all 14 Tier 1 routes + 8 Tier 2 Labs routes + the shell:
    - Route + file
    - Component structure(top-level components + nested components,`useState` shape,key `useEffect`s)
    - Mock data dependencies(every `ekp-data.jsx` reference + ad-hoc inline data)
    - Tier 1 / 1.5 / 2 classification(prototype's own badge + cross-ref `PAGE_INVENTORY.md` "Tier 1 + Tier 2 mixed routes" table)
    - IA compliance(inside `<AppShell>` per ADR-0024 or pre-auth — flag any deviation)
    - Visual identity(tokens via `styles.css`'s `oklch()` Warm Charcoal + Coral Accent — flag any hardcoded hex / RGB / non-token colour)
    - Deviation from `architecture.md v6 §5`(new tab / new view / new route topology / new view widget)→ feed into F3 ADR draft
  - F1.2 Summary section at end of `W19-mockup-jsx-audit.md` — "All deviations identified" list,one bullet per deviation,each tagged with the F3 ADR it feeds(0025–0029)or "no ADR needed — covered by ADR-0024" or "Tier 2 — Lab page,no Tier 1 implementation"
  - F1.3 `tweaks-panel.jsx` audit — explicitly confirm this is a **design-time tool only**(theme / density / retrieval viz / citation placement / trace viz toggles);NOT shipping to `frontend/`;Wave A docs that the `/dashboard` "Tweaks" affordance is the user's design-iteration surface, gone in real app
  - F1.4 `styles.css` audit — confirm `oklch()` tokens match `frontend/lib/theming/tokens.ts`(Warm Charcoal `oklch(0.20 0.01 285)` primary + Coral Accent `oklch(0.65 0.18 25)` per ADR-0015 W12 D2);flag any divergence;flag any class name not present in `frontend/` shadcn convention
  - F1.5 `ekp-data.jsx` audit — sample 5–10 mock data shapes and grep them against `backend/api/schemas/*.py`(KbStatus / RetrievalTestResult / TraceDetail / EvalReport / FeedbackRequest / Citation / ImageRef / etc.);flag any shape mismatch → feed into F2 backend gap or F3 ADR amend
- **Effort estimate**:0.8 day(17 files × ~5 min careful reading + cross-ref + write-up;the table writing is the largest single chunk)
- **Owner**:AI(audit + write-up)+ user(skim the deviation summary)

### F2 — Backend gap map(14 Tier 1 routes × endpoint × schema)

- **Component(s)**:C08 API Gateway primarily;feeds into ADRs that may need C02 / C09 / C11 / C12 + new C14 / C16 scope notes
- **Spec ref**:architecture.md v6 §4 application architecture + §3 RAG core(for retrieval-side endpoints);`backend/api/routes/*` actual file map;`backend/api/schemas/*.py` Pydantic shapes;`PAGE_INVENTORY.md` Backend schema column
- **OQ deps**:none for the mapping itself;岔口 2 (Settings Connections scope) affects how the gap is classified — the F2 map enumerates the gap regardless,F3 ADR-0026 picks the scope
- **Acceptance criteria**:
  - F2.1 `audit/W19-backend-gap-map.md` NEW — per-route table:
    - Route
    - Frontend data needs(from F1 audit summary)
    - Backend endpoint required(method + path)
    - Status:`supported`(real endpoint + matching schema) / `partial`(endpoint exists,schema/feature gap) / `missing`(no endpoint) / `mock-only`(stays mock for Tier 1)
    - Wave block(`Wave A` / `Wave B` / `Wave C` / `Tier 2 deferred`)
    - Owner Cn for the implementation
  - F2.2 Cumulative backend-work list — extracted from F2.1's `missing` + `partial` rows,grouped by Cn + Wave:
    - C02 KB Manager — what new fields/endpoints
    - C07 Observability — `/health` per-component connectivity payload(supports `/dashboard` System health card + Settings → Connections "test connection")
    - C08 API Gateway — every NEW endpoint group: Settings → Connections / Identity & Auth / API Keys + /users RBAC + /eval/run cached result + recent-queries store(Q6)
    - C11 Identity & Access — RBAC tables + role-gated route guard
    - C12 DevOps — Key Vault secret rotation API surface
    - Potentially new C14 Settings Service + C16 Users Service(F3 ADR-0026 / ADR-0027 decide)
  - F2.3 "Blocks Wave A/B/C" classification — explicit list of "Wave A cannot start without this" / "Wave B cannot start without this" / "Wave C only" / "Tier 2 only"
  - F2.4 Real backend code grep — Per F2.1 row,grep `backend/api/routes/` + `backend/api/schemas/` for the actual route + schema definition(or its absence) → cite line numbers as evidence;avoid over-relying on `PAGE_INVENTORY.md` which is itself a derived doc
- **Effort estimate**:0.8 day(14 routes × grep + map + write-up + cumulative list extraction)
- **Owner**:AI(implementation)+ user(review the cumulative backend-work list — scope sanity check)

### F3 — ADR drafts × 5(Status = Proposed,await F6 approval)

- **Component(s)**:ADR governance — each draft tags the Cn(s) it amends
- **Spec ref**:CLAUDE.md §6 ADR Format(Context / Decision / Alternatives Considered / Consequences / References);CLAUDE.md §5.1 H1(architectural change requires ADR);ADR-0024 amendment-pattern precedent(W18 kickoff cascade)
- **OQ deps**:**岔口 1 (/users RBAC scope) + 岔口 2 (Settings Connections scope)** — these are documented in the ADR drafts as **option sets**;Chris picks at F6 + the picked option becomes the Accepted ADR;the unpicked option becomes the Alternatives Considered + rejection rationale
- **Acceptance criteria**:
  - F3.1 ADR-0025 KB Detail 5→8 tabs expansion — NEW `docs/adr/0025-kb-detail-8-tabs-expansion.md`:
    - Context:prototype `/kb/[id]` has 8 tabs(Documents / Chunks / Images / Chunking Lab / Pipeline / Retrieval Testing / Access / Settings);spec `§5.5` has 5(Documents / Chunks / Pipeline / Retrieval Testing / Settings);3 new tabs Images + Chunking Lab + Access expand C02 / C03 scope + Access depends on RBAC(ADR-0027)
    - Decision:adopt the 8-tab layout;the 3 new tabs amend `§5.5` with new `§5.5.6 Images` + `§5.5.7 Chunking Lab` + `§5.5.8 Access`(or similar numbering);Access tab implementation is **blocked on ADR-0027 acceptance**(hard dep)
    - Alternatives:stay 5-tab(reject — prototype mockup explicitly covers `Images` + `Chunking Lab` content + Access is a real per-KB ACL requirement,not aspirational);split Images + Chunking Lab into a separate `/kb/[id]/images` page(reject — fragments KB Detail nav for Tier 1 scope)
    - Consequences:C02 scope expansion(per-KB image listing endpoint + chunking strategy preview endpoint);C09 §5.5 amend;ADR-0027 dep documented;`PAGE_INVENTORY.md` already reflects this
    - References:architecture.md v6 §5.5;`references/design-mockups/ekp-page-kb.jsx`;`references/design-mockups/ekp-page-kb-extras.jsx`;PAGE_INVENTORY.md route #5
  - F3.2 ADR-0026 Settings v1 thin → 6-tab hub + Connections backend — NEW `docs/adr/0026-settings-6-tab-hub-and-connections-backend.md`:
    - Context:prototype `/settings` has 6 tabs(Profile / Appearance / Connections / Identity & Auth / API Keys & Quotas / Account);spec `§5.0` v1 = profile display + theme + sign-out;the **Connections + Identity & Auth + API Keys** tabs are H1 weight(secret management UI + Key Vault rotation + connection-test endpoints + API key CRUD)
    - Decision options(**岔口 2** — Chris picks at F6):
      - **Option A — Read-only view**(Tier 1 ship):display current connection state + last-tested timestamp;rotation stays ops-side `.env` operation;UI-driven edit defers to Tier 2;**low backend scope:** `GET /admin/connections/status` + `GET /admin/api-keys/list` only
      - **Option B — Fully editable**(Tier 1 ship):UI-driven secret rotation + Key Vault wire + API key CRUD + connection-test endpoint per service;**high backend scope:** ~10 new endpoints + Key Vault SDK + role-gated(needs ADR-0027 Accepted)
      - **Option C — Hybrid**:Profile + Appearance + Account = fully editable Tier 1;Connections + Identity & Auth + API Keys = read-only Tier 1 + "edit coming Tier 2" affordance;**medium backend scope:** read-only endpoints only
    - Alternatives:keep v1 thin Settings(reject — operator pain in production + the prototype already designs the surface;a regression);split into `/admin/connections` separate route(reject — Settings is the natural hub)
    - Consequences(per option):C08 new endpoint group;C12 Key Vault SDK wire(Option B);ADR-0027 dep(Identity & Auth tab role mappings need RBAC)
    - References:architecture.md v6 §5.0;`references/design-mockups/ekp-page-settings-tabs.jsx`;PAGE_INVENTORY.md route #11 + "Tier 1 + Tier 2 mixed routes" Settings rows
  - F3.3 ADR-0027 /users Tier 1.5 RBAC — NEW `docs/adr/0027-users-tier-1-5-rbac.md`:
    - Context:prototype `/users` 4 tabs(Members / Roles & permissions matrix / Groups / Audit log)= NET NEW Tier 1.5 surface;spec only mentions RBAC as Tier 2 hook;promoting to Tier 1.5 enables per-KB ACL(ADR-0025 Access tab) + role-mapping(ADR-0026 Identity & Auth tab)
    - Decision options(**岔口 1** — Chris picks at F6):
      - **Option A — Full RBAC**(Tier 1.5 ship):3 roles(Admin / Editor / User) + full per-KB ACL + Groups + Audit log + role-gated route guard;**high backend scope:** new `roles` + `role_permissions` + `groups` + `group_members` + `audit_log` Postgres tables + ACL middleware + auth-time role claim + frontend `useRole()` hook;C11 scope expansion + new C16 Users Service
      - **Option B — Minimal 3-role hard-coded**(Tier 1 ship):3 roles in a `users.role` column(per ADR-0023 users table)+ ACL middleware checks `role` only;no Groups, no Audit log, no Roles & permissions matrix(those tabs become disabled affordance);**low backend scope:** 1 column add + middleware
      - **Option C — Stage**(Tier 1 = Option B + Tier 2 governance flips to A):initial ship = Option B;Q12 post-Beta governance trigger flips to A;Members + Audit log tabs are read-only Tier 1,Roles & permissions matrix + Groups stay disabled
    - Alternatives:reject Tier 1.5 surface entirely(reject — Access tab + Identity & Auth tab content has nowhere to live)
    - Consequences(per option):C11 scope;new C16 Users Service(Options A/C);Postgres migration(W22 Wave C);frontend `useRole()` hook + role-gated view rendering
    - References:architecture.md §3.7;ADR-0023(`users_repo` Postgres backing);`references/design-mockups/ekp-page-users.jsx`;PAGE_INVENTORY.md route #12
  - F3.4 ADR-0028 /kb/new 5-step wizard + multimodal Tier 1/2 split — NEW `docs/adr/0028-kb-new-5-step-wizard.md`:
    - Context:prototype `/kb/new` 5-step wizard(Identity → Format & chunking → Multimodal → Retrieval defaults → Review);spec `§5.5.3` was 3-step IN the KB Detail Pipeline tab(DATA SOURCE → DOCUMENT PROCESSING → EXECUTE);prototype promotes to **its own route** + adds Multimodal + Retrieval defaults + Review steps
    - Decision:adopt the 5-step layout as a dedicated `/kb/new` route;the Pipeline tab inside KB Detail keeps the 3-step DATA SOURCE → DOCUMENT PROCESSING → EXECUTE wizard for re-ingestion / re-indexing;Multimodal step **mixes Tier 1**(embedded image extract via Docling / python-pptx + SHA256 dedup + "off — use source alt_text only" captioning + render inline in chat)**and Tier 2**(Vision captioning GPT-5.5 Vision / Azure DI / slide screenshots for .pptx / render PDF pages / low_value image filter / perceptual hash dedup)→ Tier 2 options stay disabled affordance with coral "TIER 2" badge per the prototype + F5 catalog
    - Alternatives:keep 3-step IN Pipeline tab(reject — creating a brand-new KB vs re-ingesting an existing KB are different flows;the 5-step covers identity + retrieval-defaults config which the in-tab 3-step skips);drop Multimodal step(reject — the multimodal pipeline is Tier 1 supported via C01 embedded image extraction)
    - Consequences:`§5.5.3` amend(distinguish "new KB wizard" vs "Pipeline tab re-ingestion");C09 scope note(NEW `/kb/new` route layout);Multimodal step's Tier 1/2 boundary documented in F5 catalog
    - References:architecture.md v6 §5.5.3 + §3.3 multi-format ingestion;`references/design-mockups/ekp-page-kb-new.jsx`;PAGE_INVENTORY.md route #4 + "Tier 1 + Tier 2 mixed routes" Multimodal row
  - F3.5 ADR-0029 /doc-detail 3-pane layout — NEW `docs/adr/0029-doc-detail-3-pane-layout.md`:
    - Context:prototype `/doc-detail/[kbId]/[docId]` 3-pane(outline / chunks / inspector);spec `§5.5.2` is `/admin/kb/[id]/chunks/[doc_id]` chunk inspector(ADR-0024 flattened to `/kb/[id]/chunks/[doc_id]`)— prototype changes route topology + 3-pane content
    - Decision:adopt the 3-pane layout;rename the route to `/doc/[kbId]/[docId]` or keep prototype's `/doc-detail/[kbId]/[docId]` — pick the simpler one(Chris feedback at F6);amends `§5.5.2`(distinguishes "document detail" from the "chunks tab inside KB Detail")
    - Alternatives:keep §5.5.2 chunk-inspector single-view(reject — the 3-pane outline + chunks + inspector pattern is the Notion / Linear-grade information density the prototype is going for);split into separate routes(reject — 3-pane is the unit of value)
    - Consequences:`§5.5.2` amend;C09 §5.5.2 scope note;additional `<ResizablePanelGroup>` or split-pane shadcn component(verify not new dep)
    - References:architecture.md v6 §5.5.2;`references/design-mockups/ekp-page-doc-detail.jsx`;PAGE_INVENTORY.md route #6
  - F3.6 Each ADR draft has `Status: Proposed`(NOT `Accepted` — that flip is F6);each draft has a "Decision Pending User Approval" placeholder at the top + the option-set choice points highlighted;each draft cross-refs the F1 audit + F2 gap map entries
  - F3.7 `docs/adr/README.md` — fill the 5 reserved slots(F0.3) with `Status: Proposed`,context cell summarizing the change,`Next NNNN = 0030`
- **Effort estimate**:1.2 days(5 ADRs × ~0.2-0.3 day each;the option-set ADRs(0026 + 0027) are larger than the consensus ADRs(0025 + 0028 + 0029))
- **Owner**:AI(draft)+ user(F6 = approve / revise / pick option for the 2 option-set ADRs)

### F4 — Wave breakdown(W20–W23+ phase skeletons)

- **Component(s)**:planning governance;F4 outputs reference every Cn touched per Wave
- **Spec ref**:CLAUDE.md §10 R1 rolling-JIT(W20 / W21 / W22 / W23+ folders NOT pre-created until each Wave's own kickoff);PAGE_INVENTORY.md "Implementation priority (suggested)" Wave A-D
- **OQ deps**:F3 ADR drafts(Wave scope needs the ADR option choices)— so F4 is sequenced after F3
- **Acceptance criteria**:
  - F4.1 `audit/W19-wave-breakdown.md` NEW — 4 Wave skeletons:
    - **Wave A — W20-frontend-wave-a**(Dashboard polish + Chat polish + KB list + KB Detail 8-tab base):routes `/dashboard` + `/chat` + `/kb` + `/kb/[id]`;ADR-0025 dep;backend deps from F2(per-component `/health` payload + ad-hoc dashboard endpoint as needed);estimated phase budget ~3-5 days;acceptance criteria sketch
    - **Wave B — W21-frontend-wave-b**(Doc Detail + Eval + Traces):routes `/doc-detail/...` + `/eval` + `/traces/[traceId]`;ADR-0029 dep;backend = mostly supported(W17 F3 RAGAs integrated + W16 F5.5 trace endpoint);estimated phase budget ~2-3 days
    - **Wave C — W22-frontend-wave-c**(Settings 6-tab + /users + Auth polish + real-MSAL ship):routes `/settings` + `/users` + `/login` polish + `/register` polish;ADR-0026 + ADR-0027 + ADR-0014 / ADR-0022 dep;**Wave C concurrently ships mock-auth path + real-MSAL path**(per user岔口 2 decision 2026-05-16);if Track A IT cred lands by W22 start = real MSAL lights up;if not = mock stays default + real path stays feature-flagged + W22 partial;backend = HIGH scope per F2(Settings + RBAC + /users tables);estimated phase budget ~5-8 days(largest Wave)
    - **Wave D — Tier 2 hold**:8 `/labs/*` pages stay prototype reference;post-Beta launch governance Q12 trigger;**NOT pre-created**(rolling JIT discipline)
  - F4.2 Dep ordering — explicit "Wave A must close before Wave B?" etc.;current draft = Waves A + B can run in parallel(disjoint surfaces, both depend on W18 chrome + F3 ADRs);Wave C needs A done(Settings + /users link from `<AppShell>` `<UserMenu>` + share `<AppShell>` chrome verified live);Wave D requires Beta launch first
  - F4.3 Per-Wave `H4 boundary policing` — list of features that surface as disabled affordance in that Wave per the F5 Tier 2 catalog
  - F4.4 The2 strategic岔口 → Wave impact diagram — Option A vs B vs C for each岔口 → Wave C scope changes summarized(e.g. RBAC Option A doubles Wave C backend scope,Option B adds only `users.role` column)
- **Effort estimate**:0.4 day(no new content — synthesis of F1 + F2 + F3)
- **Owner**:AI(write-up)+ user(F6 review)

### F5 — Tier 2 disabled-affordance catalog

- **Component(s)**:cross-Cn UI pattern spec
- **Spec ref**:architecture.md v6 §11 Tier 2 trigger matrix;CLAUDE.md §5.4 H4 Tier boundary;PAGE_INVENTORY.md "Tier 1 + Tier 2 mixed routes" + "What's NOT in the prototype";the prototype's existing "TIER 2 PREVIEW" badge pattern
- **OQ deps**:none(catalog enumerates the prototype's existing pattern + standardizes for Wave A/B/C)
- **Acceptance criteria**:
  - F5.1 `audit/W19-tier2-disabled-affordance-catalog.md` NEW — enumerate every disabled-affordance instance:
    - **`<AppShell>` topbar language toggle**(per ADR-0024 + W18 F1)— native `disabled` + `title="Multi-language..."`;Tier 2 i18n trigger
    - **/login Forgot password? link**(per ADR-0014 + W18 F7)— disabled affordance;Tier 2 reset-password
    - **/kb/new Step 3 Multimodal — Vision captioning select option**(Tier 2 per PAGE_INVENTORY)— native `<option disabled>` + coral "TIER 2" badge
    - **/kb/new Step 3 — Slide screenshots for .pptx**(Tier 2)— disabled checkbox + coral badge
    - **/kb/new Step 3 — Perceptual hash dedup**(Tier 2)— disabled select option
    - **/kb/[id] Access tab — Public visibility radio**(Tier 2)— disabled radio + tooltip
    - **/kb/[id] Access tab — Anonymous API key**(Tier 2)— disabled toggle
    - **/users Roles tab — Power User role**(Tier 2)— disabled row + coral badge
    - **/users Roles tab — Custom role creation**(Tier 2)— disabled "Create role" button
    - **/settings → Identity & Auth — Power User mapping**(Tier 2)— disabled field
    - **/settings → Identity & Auth — Distributed token cache (Redis)**(Tier 2)— disabled select option
    - **/settings → API Keys & Quotas — Anonymous API keys**(Tier 2)— disabled toggle
    - **/settings → Connections → "Add provider" custom integration**(Tier 2)— disabled button + coral badge
    - **`/labs/*` 8 pages**(Tier 2)— routes navigable from sidebar Labs section?(or hidden? — F5.2 decision);"TIER 2 PREVIEW · NOT IMPLEMENTED" banner per page
  - F5.2 **Per-affordance handling spec** — for each item above,define:
    - Affordance pattern:`native disabled` / `aria-disabled + click-intercept toast` / `coral badge + present-but-noninteractive` / `route hidden from sidebar`(`/labs/*` only)
    - Tooltip / title text(consistent voice — "Coming in a later tier" or specific "Tier 2 reset-password — not in Tier 1 scope")
    - Coral accent usage guard(per `DESIGN_README.md` Color semantics — coral reserved for Tier 2 preview only,NOT for selected/active states)
    - H4 boundary rationale(why this isn't smuggled into Tier 1)
    - Tier 2 trigger condition(per `architecture.md v6 §11`,which one of the trigger matrix rows enables this)
  - F5.3 Standardize the implementation pattern — single shared `<DisabledAffordance>` or `<Tier2Affordance>` component spec(NEW component to add in W20 Wave A or W22 Wave C — design pattern only,not built in W19);each Wave references this catalog to wire their disabled items consistently
  - F5.4 `/labs/*` routing decision — option A:Labs accessible from a `<AppShell>` sidebar section "Tier 2 Preview"(visible to all roles?or only Admin?);option B:Labs routes are removed from production builds entirely(behind a `NEXT_PUBLIC_TIER2_PREVIEW_ENABLED` flag);option C:Labs stays in prototype only,never lands in `frontend/`. Recommend C for Wave A-C ship,A for post-Beta governance(per ADR-0024 sidebar 5-module list LOCKED — Labs would amend ADR-0024 again, deliberate)
- **Effort estimate**:0.5 day(enumeration + per-item spec + cross-ref + the `<DisabledAffordance>` component design sketch)
- **Owner**:AI(catalog)+ user(F6 = decision on F5.4 routing option)

### F6 — Phase closeout + Chris approve + W20+ kickoff trigger

- **Component(s)**:governance + closeout cascade
- **Spec ref**:CLAUDE.md §10 R5(Phase closeout ADR discipline)+ R1 rolling-JIT
- **OQ deps**:F1–F5 all done
- **Acceptance criteria**:
  - F6.1 Chris review session — go through `audit/W19-mockup-jsx-audit.md` + `audit/W19-backend-gap-map.md` + `audit/W19-wave-breakdown.md` + `audit/W19-tier2-disabled-affordance-catalog.md` + 5 ADR drafts;answer:
    - 岔口 1 (/users RBAC scope) — pick ADR-0027 Option A / B / C
    - 岔口 2 (Settings Connections scope) — pick ADR-0026 Option A / B / C
    - F5.4 (/labs/* routing) — pick A / B / C
    - F3.5 (/doc-detail route name) — pick `/doc-detail/...` or `/doc/...`
  - F6.2 Each ADR(0025–0029) Status `Proposed` → `Accepted` per Chris approval(if changes needed, AI revises + re-submits before flip;the F6 session may iterate);ADR README slot status updates accordingly
  - F6.3 W19 phase Gate verdict landed — **PASS** if all 6 deliverables done + 5 ADRs Accepted + Chris signs off W20 kickoff;**PARTIAL** if 1-2 ADRs need significant revision but Wave A scope is clear enough to kick off;**FAIL** if F1-F2 audit surfaces a Tier 2 leak or H1 conflict that requires re-spec
  - F6.4 W19 `plan.md` + `checklist.md` + `progress.md` frontmatter `status: active` → `closed`
  - F6.5 W19 `progress.md` retro — 7 sections(What worked / What didn't & friction / Surprises / Decisions / Carry-overs to W20+ / Time tracking / Spec-ref alignment)
  - F6.6 `session-start.md` hygiene catch-up — §3 (no Cn status change at W19 closeout — only flag "5 ADRs Accepted, W20+ implementation pending"); §10 W19 row → closed,verdict;W20+ NOT pre-created(rolling JIT);§11 carry-overs(the 5 Accepted ADRs become W20+ tracking items);§12 Milestones row(累計 17→18 phase closed);Last-Updated + Update-history
  - F6.7 W20-frontend-wave-a kickoff candidate — flag in session-start.md §10 W19 row "next kickoff = W20-frontend-wave-a per ADR-0025 + F4.1 Wave A scope";the actual W20 phase folder created **in a separate kickoff cascade**(not at W19 closeout — per the rolling JIT precedent W17→W18 / W18→W19)
  - F6.8 No new W19 OQ expected(the strategic 岔口 are resolved by F6 + become Accepted ADR options,not new OQs in `decision-form.md`)
- **Effort estimate**:0.3 day(synthesis + frontmatter flips + session-start.md hygiene + retro;assumes the Chris review session is its own time block,not absorbed)
- **Owner**:AI(synthesis + retro)+ user(approval + sign-off)

---

## 3. Success Criteria(Phase Gate)

W19 phase Gate **PASS condition**:

1. F0 — Phase folder + ADR README slots + session-start.md W19 row landed at kickoff
2. F1 — `audit/W19-mockup-jsx-audit.md` covers all 17 `.jsx` files + shell + data + styles + tweaks;every deviation feeds into F3
3. F2 — `audit/W19-backend-gap-map.md` covers all 14 Tier 1 routes;cumulative backend-work list classified by Cn + Wave;real backend grep cited
4. F3 — 5 ADR drafts(0025–0029)written with `Status: Proposed`;each has Context / Decision(with option sets where applicable) / Alternatives / Consequences / References;cross-refs F1+F2
5. F4 — `audit/W19-wave-breakdown.md` covers 4 Wave skeletons;dep ordering explicit;岔口 impact diagram drawn
6. F5 — `audit/W19-tier2-disabled-affordance-catalog.md` enumerates every Tier 2 affordance instance + handling spec + `<DisabledAffordance>` component sketch
7. F6 — Chris approves all 5 ADRs(option picks for 0026 + 0027 + F5.4 + F3.5 done);frontmatter `closed`;session-start.md hygiene catch-up;W20 kickoff candidate flagged

W19 phase Gate **PARTIAL PASS** acceptable per Karpathy §1.4:

- F3 — 1-2 ADRs need revision after F6 review;AI revises + re-submits;PARTIAL acceptable if Wave A scope is clear enough to kick off W20 even with ADR-0026 + ADR-0027 still in revision(those affect Wave C, not Wave A)
- F4 — Wave C scope un-finalized until ADR-0026 + ADR-0027 land;Wave A + B scope sealed = enough to authorize W20 kickoff
- F2 — some `partial` rows may need deeper backend audit;defer the deepest dive to the corresponding W20+ phase

W19 phase Gate **FAIL condition**:

- Audit surfaces a **Tier 2 leak**(prototype quietly implements a Tier 2 feature without disabled affordance)— remediation = halt + amend mockup before any Wave kickoff
- Audit surfaces a **non-trivial H1 conflict**(prototype + spec disagree in a way that breaks ADR-0024 or undoes a W18 Accepted decision)— remediation = re-spec session before continuing
- F3 ADR drafts surface a backend scope that **exceeds reasonable Tier 1 budget**(e.g. ADR-0026 Option B + ADR-0027 Option A together = 15+ new backend endpoints + Postgres migration + Key Vault SDK wire — may need a "scope cut" governance call before W22 Wave C kickoff)
- Chris does not approve(or needs major revisions to) 3+ of the 5 ADRs — remediation = AI revises + re-submits;F6 re-runs

## 4. Risks(Phase-Specific)

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| F1 audit surfaces more deviations than 5 → need ADR-0030+ | Medium | Medium | F3 ADR scope flexes — if 6th+ deviation found, add ADR-0030 to F3.1 list at F1 mid-point;notify user;don't silently extend |
| F2 backend gap is much deeper than estimated(Settings Connections + RBAC together = 15+ endpoints) | High | High | F4.4 岔口 impact diagram makes the scope visible early;Chris can pick ADR-0026 Option A + ADR-0027 Option B at F6 to cut Wave C scope by ~60%;alternatively split Wave C into Wave C1 + Wave C2 |
| 岔口 1 + 岔口 2 stay un-resolved at F6 → ADR-0026 + ADR-0027 stuck in Proposed | Medium | High | F3 ADR drafts present option sets with cost/benefit + recommended option;F6 review session AI brings the cost/benefit table to drive decision;PARTIAL-PASS path allows Wave A kickoff without ADR-0026/0027 sealed(those affect Wave C only) |
| Audit work uncovers a deviation from ADR-0024 W18 lock(IA chrome) | Low | High | DESIGN_README.md explicitly honors ADR-0024(AppShell + 5 modules + flat URLs);F1 audit confirms;if a deviation found → STOP and report (H1 violation in the prototype itself) |
| Tier 2 leak in prototype(e.g. a "TIER 2" badge missing on an aspirational feature) | Medium | Medium | F5 catalog enumeration is the canary;if missing badge found,document + propose mockup amendment as a separate Change(per PROCESS.md §3)not silently absorbed |
| Wave A backend deps from F2 reveal `/health` per-component connectivity is a substantial scope item | Medium | Low | The current `/health` `{status:"ok"}` is enough for Wave A `/dashboard` System health card to show backend-up/down;richer payload defers to Wave C(Settings → Connections "test connection" is the natural surface);documented in F4 |
| Audit + ADR drafting takes longer than 1 week | Medium | Low | Real-calendar collapse precedent(W12-W18 routinely under plan-day budget when momentum clean);F2/F3 are the largest;PARTIAL-PASS path allows time-box at the F6 review without re-spinning |
| R8 corp-proxy block surfaces during audit(e.g. need to install a new tool to inspect mock HTML) | Low | Low | Audit is read-only on existing files;no install needed;mitigated |
| Chris is unavailable for F6 review within W19 window | Medium | Low | F6 review can be async(written response on the 4 audit files + 5 ADR drafts);frontmatter `end_date` is a window not commitment |
| Frontend implementation work surfaces design questions the mockup doesn't answer(emerges in W20+) | High | Low | Out of W19 scope — those become per-Wave Change items per PROCESS.md §3,not retroactive W19 work |

## 5. Day-by-Day Breakdown(rough)

| Day | Date(tentative) | Focus |
|---|---|---|
| W19 D0 | 2026-05-16 | Kickoff — `plan.md` + `checklist.md` + `progress.md` + `audit/` subfolder + ADR-0025–0029 reserved slots in README + session-start.md §10 W19 row(`status: active`)|
| W19 D1 | 2026-05-16 / 2026-05-17 | F1 — full mockup audit per `.jsx`(17 files + shell + data + styles + tweaks) → `audit/W19-mockup-jsx-audit.md` |
| W19 D2 | 2026-05-17 / 2026-05-18 | F2 — backend gap map(14 Tier 1 routes × endpoint × schema) → `audit/W19-backend-gap-map.md` |
| W19 D3 | 2026-05-18 / 2026-05-19 | F3 — ADR drafts 0025 + 0028 + 0029(consensus ADRs first — no option sets) + start 0026 + 0027 |
| W19 D4 | 2026-05-19 / 2026-05-20 | F3 — finish ADR drafts 0026(Settings options) + 0027(/users RBAC options)|
| W19 D5 | 2026-05-20 / 2026-05-21 | F4 — Wave breakdown(4 Wave skeletons + dep ordering + 岔口 impact diagram) → `audit/W19-wave-breakdown.md`. F5 — Tier 2 catalog → `audit/W19-tier2-disabled-affordance-catalog.md` |
| W19 D6 | 2026-05-21 / 2026-05-22 | F6 prep — synthesis presentation for Chris review(cost/benefit table for option sets, dep diagram, scope-cut recommendations) |
| W19 D7 | 2026-05-22 / 2026-05-23 | F6 — Chris review session;ADRs Accepted;frontmatter `closed`;session-start.md hygiene;W20 kickoff candidate flagged |

**Day-by-day caveat**:dates tentative;real-calendar collapse is the W12-W18 pattern(phase capacity routinely runs under plan-day budget when momentum is clean);if F1+F2 collapse into D1, F3 starts earlier;if Chris available sooner, F6 collapses too. The `start_date`/`end_date` frontmatter is a window, not a commitment.

## 6. Dependencies on Prior Phase / Carry-overs Addressed

From session-start.md §11 + the W18 retro carry-overs — W19 directly addresses:

- **design-mockups landed implementation kickoff** — user directive 2026-05-16(after `08b74af` commit);W19 = the plan + audit + ADR phase that authorizes W20+ implementation
- **`<LoginGate>` `// TODO(W16)` tightening** — W19 ADR-0027 RBAC scope decision influences when the login-gate's real-MSAL `router.replace('/login')` flip happens(Wave C / W22 per user岔口 2 decision = mock + real both ship)
- **Dashboard "recent queries" + "latest evaluation" empty-state CTAs** — W19 F2 backend gap map identifies the missing endpoints(Q6 query log + eval-run cache);Wave A may or may not fill them depending on ADR-0026 Option scope
- **Dashboard "system health" → richer `/health`** — W19 F2 documents the gap;Wave A `/dashboard` system-health card stays backend-up/down liveness until a richer endpoint lands(Wave C Settings → Connections "test connection" is the natural surface)
- **CO_W15_F3_dark_mode_visual_verify** + **CO_W15_F4_interactive_flow_E2E** — W19 does NOT advance these(audit-only phase);Wave A E2E updates pick them up;the user's pre-Beta interactive smoke stays the W12-W18 caveat shape

W19 does **NOT** address(stay W16 / Tier 2 / parallel track):

- **CO16 Track A IT cred populate event + R-B1 closure**(W16 F1) — external dependency,parallel to W19;user岔口 2 decision = Wave C ships mock + real both, so Wave C is independent of Track A landing time
- **CO17 — 🚧 F1.5b**(Postgres-path runtime smoke)**+ 🚧 F3.5b**(RAGAs live-verify Azure-key-bound)— audit-only phase;Wave A/B/C may surface a chance to verify, but W19 doesn't
- **CO19 25% Beta cohort rollout activation**(W16 F2 — Beta phase parallel)
- **CO_F6a/b/c ACS email retry / BackgroundTasks / SPF-DKIM**(Track A — W16 F1 / IT-side)
- **CO_W15_F1_eval_set_v1** — `eval-set-v1.yaml` final still needs Chris's SME reference-answer labels per Q14(unrelated to W19)
- **CO_W15_F3_aria_full_audit** — Tier 2 full NVDA/JAWS/VoiceOver audit(W19 audit-only, no a11y work)
- **CO13 / AF3 code fix**(ADR-0013 reserved) — unrelated to W19

## 7. Plan Changelog

| Date | Change | Reason | Approver |
|---|---|---|---|
| 2026-05-16 | Initial draft + `status: active` + W19 folder created(`plan.md` + `checklist.md` + `progress.md` + `audit/`)| User directive 2026-05-16(after design-mockups landed `08b74af`):「現在我們可以先把 design-mockups 的內容 先進行實作」+ AskUserQuestion answer "W19 audit-and-adr-draft phase folder kickoff(推薦)" + "Mock-auth 繼續做 default,W22 同時 ship mock + real(推薦)"= the post-design-mockups-landed implementation authorization per CLAUDE.md §5.1 H1 / §10 R1 / R5. F0–F6 = audit + ADR drafts + planning only,NO `frontend/` code change in this phase. | Chris(stakeholder + architecture decision owner) |
| 2026-05-16 | F3 ADR draft count 5 → 6 promotion(NEW ADR-0031 Chat advanced surfaces per F2 §6 recommendation;ADR-0030 + ADR-0032 SKIPPED absorbed into Wave A scope)| F2 backend gap map analysis identified Conversation History + 3 citation placement modes + InlineImageCard/Gallery/CitationPill/FeedbackBar/CRAG strip as substantial Tier 1 enhancement bundle warranting dedicated ADR(per W19 F2 §6 recommendation #4);D6/D9/D11 Dashboard + Trace 3 viz + /traces list deemed polish-grade for Wave A scope absorb;D8 Topbar/Sidebar additive(Workspace switcher disable + NotificationsMenu)同 polish-grade for Wave A scope absorb。Net effect:6 ADRs(0025/0026/0027/0028/0029/0031)+ 0 SKIPPED slots(0030 + 0032 vacancies preserved with skip note in `docs/adr/README.md` footnote). | Chris(implicit via AskUserQuestion option-set acceptance + F4 cadence answer)|
| 2026-05-16 | **F6 Chris approval cascade — 4 strategic decisions picked + 6 ADRs flipped Proposed → Accepted** | AskUserQuestion F6 4-decision pick 2026-05-16:**(1) ADR-0027 Option A full RBAC**(over recommended Option B minimal 3-role)— ~20 backend days + 6 NEW Postgres tables(roles + role_permissions + groups + group_members + audit_log + kb_acl)+ Entra Graph SDK new dep(H2 trigger + R8 mitigation per ADR-0017)+ ACL middleware + audit log writes + new C16 Users Service;**(2) ADR-0026 Option B fully editable**(over recommended Option C hybrid)— ~22 NEW backend endpoints + Key Vault SDK new dep(H2 trigger + R8 mitigation per ADR-0017)+ provider CRUD + Test connection + secret rotation;**(3) ADR-0031 Option B server-side Tier 1**(over recommended Option A localStorage)— promotes C10 §7 Tier 2 to Tier 1;Postgres conversations + messages tables + 6 /conversations CRUD endpoints + ~3 backend days extends Wave A budget;**(4) ADR-0029 Option C `/kb/[id]/docs/[docId]` route name**(matches recommendation)— IA consistency with ADR-0024 flat URL convention。**Combined Wave C scope per Option A+B picks = ~42 backend days exceeds single-phase budget → Wave C MUST split into C1+C2 sub-phases** per F4 §3.6 trigger + CLAUDE.md §10 rolling JIT。**Wave A backend extends ~5-7 → ~8-10 days** due to Option B Conversation History server-side。**Wave A KB Detail ships 8-tab including Access**(was planned 7-tab `-Access` per Option B RBAC recommendation,but Option A full RBAC unlocks Wave A Access tab activation IF backend RBAC infra lands Wave A — needs F4 amendment + Wave A scope re-confirm at W20 kickoff)。**6 ADRs Status `Proposed` → `Accepted`**:0025 consensus / 0026 Accepted (Option B) / 0027 Accepted (Option A) / 0028 consensus / 0029 Accepted (Option C) / 0031 Accepted (Option B)。 **Phase Gate = PASS WITH WAVE-C-SPLIT-TRIGGERED CAVEAT**(all F0-F6 deliverables landed;Wave C2 split is a downstream implementation impact,not a F6 deliverable shortfall). | Chris |

---

**Lifecycle reminder**:呢份 plan `status=active`(2026-05-16,per user directive)。重大 deviation 入第 7 節 changelog(per R3)。Next-phase folder(W20-frontend-wave-a)**唔會** pre-create(per CLAUDE.md §10 R1 rolling-JIT — kickoff post-W19-F6 closeout decision per ADR-0025 + F4.1 Wave A scope authorization)。
