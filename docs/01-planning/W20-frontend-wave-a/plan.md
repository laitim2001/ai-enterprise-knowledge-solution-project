---
phase: W20-frontend-wave-a
name: "Frontend Wave A — Dashboard + Chat advanced + KB cluster (7-tab) + auth/topbar polish (per ADR-0025 KB Detail 7-tab `-Access` / ADR-0028 /kb/new 5-step / ADR-0031 Chat advanced server-side Conversation History + ADR-0030/0032 absorbed scope)"
sprint_week: W20
start_date: 2026-05-16              # real-calendar — kicked off post-W19 closeout (Chris pick AskUserQuestion 4 strategic decisions + 6 ADRs Accepted); independent of W16 F1-F4 (Track-A-blocked, parallel) and W21 Wave B (sequential)
end_date: 2026-05-30                # ~1.5-2 weeks per W19 F4 §1.3 (backend ~8-10 days + frontend ~10-13 days; real-calendar collapse pattern 1.8-4× — actual likely ~3-5 days per W12-W18 trajectory; frontmatter is a window, not a commitment)
status: active                      # `active` from kickoff 2026-05-16 (Chris directive at W19 F6 closeout + 6 ADRs Accepted = the authorization; same pattern as W17 D0 + W18 D0)
spec_refs:
  - architecture.md v6 §5.0          # Application Shell (W18 ADR-0024) — topbar + sidebar polish per ADR-0032 absorb
  - architecture.md v6 §5.2          # Chat — advanced surfaces per ADR-0031
  - architecture.md v6 §5.3          # Dashboard — real cards per ADR-0030 absorb (W18 F4 placeholder → richer cards)
  - architecture.md v6 §5.4          # KB List — polish
  - architecture.md v6 §5.5          # KB Detail — 7-tab refactor per ADR-0025 minus Access
  - architecture.md v6 §5.10-§5.11   # Login + Register — polish per ADR-0014
  - ADR-0025                         # KB Detail 8-tab (Wave A ships 7-tab `-Access`; Access tab activates Wave C after RBAC backend lands)
  - ADR-0026                         # Settings 6-tab fully editable (NOT in Wave A — Wave C)
  - ADR-0027                         # /users Tier 1.5 RBAC full Option A (NOT in Wave A — Wave C1; Wave A only ships KB Detail 7-tab minus Access)
  - ADR-0028                         # /kb/new 5-step wizard + Multimodal Tier 1 active fields
  - ADR-0029                         # /doc-detail 3-pane (NOT in Wave A — Wave B)
  - ADR-0031                         # Chat advanced server-side Conversation History (promotes C10 §7 Tier 2 → Tier 1)
  - ADR-0024                         # Unified application shell (W18) — Wave A topbar/sidebar polish inside the existing <AppShell>
  - ADR-0030                         # SKIPPED per W19 F6 — Dashboard polish + Trace 3 viz + /traces list absorbed into Wave A/B implementation
  - ADR-0032                         # SKIPPED per W19 F6 — Topbar/Sidebar additive scope absorbed into Wave A F1
prior_phase: W19-frontend-audit-and-adr-draft   # closed 2026-05-16 (Gate PASS WITH WAVE-C-SPLIT-TRIGGERED CAVEAT); 6 ADRs Accepted via Chris pick (0025 7-tab consensus / 0026 Option B fully editable / 0027 Option A full RBAC / 0028 5-step consensus / 0029 Option C /kb/[id]/docs/[docId] / 0031 Option B server-side Conversation History); Wave C MUST split into C1+C2 per F4 §3.6 trigger
related_artifacts:
  - docs/01-planning/W19-frontend-audit-and-adr-draft/audit/W19-wave-breakdown.md   # F4 — §1 Wave A scope skeleton
  - docs/01-planning/W19-frontend-audit-and-adr-draft/audit/W19-backend-gap-map.md  # F2 — §3.1 + §3.2 Wave A backend deps (8 items + ADR-0031 Option B 2 items)
  - docs/01-planning/W19-frontend-audit-and-adr-draft/audit/W19-mockup-jsx-audit.md # F1 — design-mockups jsx audit (KB Detail / /kb-new / /chat / /dashboard prototypes)
  - docs/01-planning/W19-frontend-audit-and-adr-draft/audit/W19-tier2-disabled-affordance-catalog.md  # F5 — 27-affordance Tier 2 catalog + <DisabledAffordance> shared component spec
  - references/design-mockups/PAGE_INVENTORY.md                # per-route Cn mapping + Tier 1/2 boundary
  - references/design-mockups/DESIGN_README.md                 # high-fidelity click-through HTML prototype entry
  - docs/adr/0025-kb-detail-8-tabs.md                          # to amend Status Proposed → Accepted at this kickoff
  - docs/adr/0028-kb-new-5-step-wizard.md                      # to amend Status Proposed → Accepted at this kickoff
  - docs/adr/0031-chat-advanced-surfaces.md                    # to amend Status Proposed → Accepted at this kickoff
  - frontend/app/(app)/dashboard/page.tsx                      # F2 — W18 F4 placeholder cards → richer overview per ADR-0030 absorb
  - frontend/app/(app)/chat/page.tsx                           # F3 — Conversation History sidebar + advanced citation modes + image/feedback/CRAG surfaces
  - frontend/app/(app)/kb/page.tsx                             # F4 — list polish (grid + table view + filter bar)
  - frontend/app/(app)/kb/new/page.tsx                         # F4 — 5-step wizard
  - frontend/app/(app)/kb/[id]/page.tsx                        # F5 — 7-tab refactor minus Access
  - frontend/app/(app)/kb/[id]/upload/page.tsx                 # F6 — re-ingestion wizard polish
  - frontend/app/login/page.tsx + register/page.tsx            # F7 — Brand panel + Forgot password disabled affordance polish
  - frontend/components/nav/app-shell.tsx                      # F1 — topbar NotificationsMenu + sidebar Tools sub-section + Labs hidden
  - frontend/components/ui/disabled-affordance.tsx             # NEW per W19 F5 — shared Tier 2 affordance component spec
  - backend/api/schemas/kb.py                                  # F4 backend — KbConfig multimodal fields (extract_embedded_images / slide_screenshots / dedup_strategy / return_images_in_chat)
  - backend/api/schemas/conversation.py                        # F3 backend NEW — Conversation + Message Pydantic schemas (ADR-0031 Option B)
  - backend/api/routes/conversations.py                        # F3 backend NEW — 6 /conversations CRUD endpoints (ADR-0031 Option B)
  - backend/persistence/postgres_conversations.py              # F3 backend NEW — PostgresConversationStore (per ADR-0023 backing pattern)
  - backend/api/routes/health.py                               # F2 backend — /health per-component connectivity payload
  - backend/api/routes/kb.py                                   # F4 backend — POST /kb/{kb_id}/archive + GET /kb/{kb_id}/images enriched
  - backend/api/routes/query.py                                # F3 backend — QueryResponse verify crag_triggered + crag_iterations
  - backend/api/routes/chunking.py                             # F5 backend NEW — POST /chunking-preview (ADR-0025 Chunking Lab tab)
  - docs/architecture.md                                       # F0 — inline-tagged amendments §5.2 + §5.3 + §5.4 + §5.5 per ADR-0025/0028/0031
  - docs/02-architecture/COMPONENT_CATALOG.md                  # F8 — C01/C02/C03/C05/C07/C08/C09/C10 status notes
  - docs/12-ai-assistant/01-prompts/01-session-start.md        # F9 — §3 / §10 / §11 / §12 + Update history catch-up
---

# Phase W20 — Frontend Wave A

> **Plan version**:1.0(draft 2026-05-16 — rolling JIT per CLAUDE.md §10 R1;kicked off post-W19 closeout per Chris's AskUserQuestion 4 strategic picks + 6 ADRs Accepted)
> **Owner**:Chris(Tech Lead + stakeholder)+ AI(implementation)
> **Approved by**:Chris — 6 ADRs **Accepted** 2026-05-16(0025 KB Detail 7-tab consensus / 0026 Settings Option B / 0027 /users Option A / 0028 /kb/new 5-step consensus / 0029 Option C `/kb/[id]/docs/[docId]` / 0031 Option B server-side Conversation History;the「approved + implement now」authorization per CLAUDE.md §5.1 H1 + §10 R5). `architecture.md v6 §5` amendments(§5.2 ADR-0031 Conversation History server-side / §5.3 ADR-0030 absorbed Dashboard polish / §5.4-§5.5 ADR-0025 7-tab refactor / §5.5 ADR-0028 5-step wizard — inline-tagged, doc version held per the W18 ADR-0024 / §3.4 / §3.7 precedent)land alongside this kickoff in F0.

---

## 1. Scope

W20 = **Wave A of the 4-Wave design-mockups → real-`frontend/` implementation roadmap**(per W19 F4 §1)— the largest by file count(8 routes touched)— ships:

- **`/dashboard`** real cards per ADR-0030 absorbed scope:5 cards(Knowledge bases / Recent queries / Latest evaluation / System health / Quick actions)+ 4-stat strip — replaces the W18 F4 placeholder + a richer `/health` per-component connectivity payload
- **`/chat`** advanced surfaces per **ADR-0031 Option B**:server-side Conversation History sidebar(Postgres-backed,promotes C10 §7 Tier 2 → Tier 1)+ 3 citation placement modes(inline / footnote / sidebar)+ InlineImageCard + ImageGallery + CitationPill hover popover + FeedbackBar comment field + CRAG strip indicator
- **`/kb`** list polish:grid + table view + filter bar
- **`/kb/new`** 5-step wizard per **ADR-0028**:Source → Parsing → Chunking → Multimodal(Tier 1 active fields + Tier 2 disabled affordances)→ Review & Create
- **`/kb/[id]`** **7-tab Detail** per **ADR-0025 minus Access**:Documents + Chunks + **Images**(NEW)+ **Chunking Lab**(NEW)+ Pipeline + Retrieval Testing + Settings — **Access tab = disabled affordance** "Tier 1.5 RBAC pending Wave C1"
- **`/kb-upload/[id]`** re-ingestion wizard polish per ADR-0028 §5.5.3b(3-step skeleton stays)
- **`/login` + `/register`** polish per ADR-0014:Brand panel slot + Forgot password disabled affordance(Tier 2 per `architecture.md v6 §11`)
- **Topbar + Sidebar polish** per ADR-0032 absorbed scope:NotificationsMenu(off `GET /notifications` if backend lands per W19 F2 item 21,else mock counter)+ Workspace switcher **disabled affordance**(Tier 2 multi-tenancy per W19 F1 §2.3 leak fix)+ Sidebar Tools sub-section(grouped)+ Labs section **hidden by default**(F5.4 Option C — prototype-only,`/labs/*` routes don't ship)

**The `<AppShell>` foundation from W18 stays unchanged**(top bar + collapsible left sidebar + main content + `<GlobalSearch>` Cmd/Ctrl+K palette);W20 is **additive polish + new view content** inside that shell — NOT a re-layout.

Goals(= ADR-0025/0028/0031 + ADR-0030/0032 absorbed scope mapped onto F1-F9):

- **Backend foundation**(F2-prep + F3-prep + F5-prep)— land the 9 backend items per W19 F2 §3.1 + §3.2(per-component `/health` payload + KbConfig multimodal fields + QueryResponse CRAG fields + `POST /kb/{kb_id}/archive` + `GET /kb/{kb_id}/images` enriched + `POST /chunking-preview` + Postgres `conversations` + `messages` tables + 6 `/conversations` CRUD endpoints + verify `crag_triggered`/`crag_iterations` in QueryResponse). **Q6 + Eval-cache decisions defer = empty-state CTAs**(W18 F4 acceptance pattern preserved — minimum-scope path,~3-4 backend days);if user enables = +3 backend days(query log + eval cache).
- **`<AppShell>` topbar/sidebar polish**(F1 — ADR-0032 absorb)— NotificationsMenu + Workspace switcher disabled affordance + Sidebar Tools sub-section + Labs hidden;reuses `<AppShell>` infrastructure.
- **`/dashboard` real cards**(F2 — ADR-0030 absorb)— rewrite W18 F4 placeholder with `useQuery` off per-component `/health` payload + KB summary + Q6/Eval-cache CTA or data + Quick actions;empty states first-class.
- **`/chat` advanced**(F3 — ADR-0031 Option B)— **NEW backend**:`backend/api/routes/conversations.py`(6 endpoints — `POST/GET/PATCH/DELETE /conversations/{id}` + `POST /conversations/{id}/messages` + `GET /conversations`)+ `backend/persistence/postgres_conversations.py`(`PostgresConversationStore` per ADR-0023 backing pattern + in-memory fallback when `DATABASE_URL` unset)+ `backend/api/schemas/conversation.py`. **Frontend**:Conversation History sidebar(left or right pane;collapsible)+ 3 citation placement modes(tweaks-style toggle per W18 §5.5.4 precedent)+ InlineImageCard + ImageGallery + CitationPill hover popover + FeedbackBar comment + CRAG strip indicator.
- **`/kb` + `/kb/new` 5-step wizard**(F4 — ADR-0028)— `/kb` list polish(grid + table view + filter bar);NEW `/kb/new/page.tsx` rewritten as 5-step wizard(Source → Parsing → Chunking → Multimodal → Review & Create);Multimodal Tier 1 active fields(`extract_embedded_images: bool` + `slide_screenshots: bool` + `dedup_strategy: 'sha256'` + `return_images_in_chat: bool`)+ Tier 2 disabled affordances(`enable_caption_generation` / `image_clustering` / `provenance_blockchain`).
- **`/kb/[id]` 7-tab Detail refactor**(F5 — ADR-0025 minus Access)— rewrite from existing 5-tab into 7-tab:Documents(existing W17 F4.1)+ Chunks(existing)+ **Images NEW**(consume `GET /kb/{kb_id}/images` enriched + ImageGallery filter)+ **Chunking Lab NEW**(consume `POST /chunking-preview` + live preview)+ Pipeline(existing wizard)+ Retrieval Testing(existing W18 ADR-0021)+ Settings(existing + `POST /kb/{kb_id}/archive` Danger zone);**Access tab disabled affordance** "Tier 1.5 RBAC pending Wave C1 — per ADR-0027 Option A backend".
- **`/kb-upload/[id]` re-ingestion**(F6 — ADR-0028 §5.5.3b)— polish existing 3-step skeleton;same Multimodal Tier 1/2 affordance pattern.
- **`/login` + `/register` polish**(F7 — ADR-0014)— Brand panel(reuse `brand-panel.tsx` from W13)+ Forgot password **disabled affordance** "Self-register reset password is Tier 2"(per `architecture.md v6 §11` + ADR-0014 §"Tier 1 scope").
- **Cross-cutting polish**(F8 — A11y + Responsive + Dark-mode + Tests)— `[oklch(`=0 milestone preserved + Vitest expansion(W18 F8.4 baseline 4 files/13 tests → W20 target 6-8 files/20+ tests)+ Playwright E2E route updates + `<DisabledAffordance>` shared component(per W19 F5)+ COMPONENT_CATALOG.md status notes.
- **Phase closeout**(F9)— Gate verdict + retro + frontmatter `closed` + `session-start.md` hygiene + W21+ rolling-JIT trigger(NOT pre-created).

**Out of W20 scope**(stay Wave B / Wave C / Tier 2 / W16 / future):
- `/doc-detail` 3-pane(per ADR-0029)— **Wave B** W21
- `/settings` 6-tab(per ADR-0026)— **Wave C** W22
- `/users` 4-tab Tier 1.5 RBAC(per ADR-0027 Option A)— **Wave C1** W22
- `/kb/[id]` **Access tab activate** — Wave C1(needs ADR-0027 backend infra:6 NEW Postgres tables + Key Vault SDK + Entra Graph SDK + ACL middleware)
- `/traces` index list + `/traces/[traceId]` 3 viz modes — **Wave B** W21(ADR-0030 absorb split — Dashboard part = Wave A;Trace + /traces parts = Wave B)
- `/eval` Eval Console refactor — **Wave B** W21(4-metric stat + Reranker Shootout + Failed queries + Recommendation + Ops Metrics + CRAG Insights)
- Real-MSAL feature-flagged path — **Wave C** W22(mock-auth default through Wave C per user 岔口 2)
- 2 NEW dependencies(Key Vault SDK + Entra Graph SDK)— **Wave C kickoff** per ADR-0017 Plan B sequencing decision
- Track A IT cred items(Azure DELETE cleanup / ACS `pip install` / `.env.production` / Cohere Marketplace billing)— still W16 F1(parallel track,unaffected)
- 25% Beta cohort rollout + daily metric monitor + Q15 weekly signal report — W16 F2-F3(Beta phase)
- Full NVDA/JAWS/VoiceOver screen-reader audit(Tier 2 — CO_W15_F3_aria_full_audit;W20 F8.2 = a11y spot-check on new surfaces only)
- Deep `/settings` notification prefs / API tokens(Wave C)

**Pre-condition for W20 promotion**(satisfied 2026-05-16):
- 6 ADRs **Accepted**(0025 / 0026 / 0027 / 0028 / 0029 / 0031;Chris directed the post-W19-closeout cascade)
- W19 frontend-audit-and-adr-draft = **closed**(Gate PASS WITH WAVE-C-SPLIT-TRIGGERED CAVEAT;6 ADRs Accepted + Wave breakdown + Tier 2 catalog + `<DisabledAffordance>` spec + F5.4 Option C `/labs/*` prototype-only)
- W19 audit/W19-backend-gap-map.md = file:line evidence for 28 endpoints × 38 schemas mapped(backend gaps identified)
- W19 audit/W19-wave-breakdown.md §1 = Wave A scope skeleton signed off(F4 closure)
- W19 audit/W19-tier2-disabled-affordance-catalog.md = 27 affordance catalog + `<DisabledAffordance>` component spec ready
- W16 F1-F4 = Track-A-blocked(parallel track — W20 does not depend on Q11 cred populate event;mock-auth default per user 岔口 2)
- W17-beta-hardening = closed(Postgres backing per ADR-0023 + auth-transport per ADR-0022 + RAGAs 4-metric integrated)— Wave A reuses ADR-0023 backing pattern for ADR-0031 conversations
- W18-app-shell-ia = closed(Unified `<AppShell>` IA per ADR-0024)— Wave A is additive inside the existing shell

## 2. Deliverables(F0-F9)

### F0 — Kickoff cascade(ADR-0025/0028/0031 Status Proposed → Accepted + spec amendment — landed at kickoff)

- **Component(s)**:cross-cutting governance(C01-C13 + frontend + backend + docs)
- **Spec ref**:CLAUDE.md §10 R1(kickoff)+ R5(ADR-before-implement);ADR-0025/0028/0031;`architecture.md v6 §5`
- **OQ deps**:Q6(real query collection — defer empty-state CTA per W18 F4 pattern;Wave A NOT promote);Q11(Track A IT cred — Wave A does NOT block,mock-auth default per user 岔口 2);Q15(weekly signal report — W16 F3,Wave A does NOT block)
- **Acceptance criteria**:
  - F0.1 `docs/adr/0025-kb-detail-8-tabs.md` Status **Proposed → Accepted**(consensus pick + 7-tab `-Access` Wave A scope note added;Implementation Deliverables row added — Wave A ships 7-tab,Wave C1 activates Access)
  - F0.2 `docs/adr/0028-kb-new-5-step-wizard.md` Status **Proposed → Accepted**(consensus pick;Multimodal Tier 1 active fields + Tier 2 disabled affordance scope confirmed)
  - F0.3 `docs/adr/0031-chat-advanced-surfaces.md` Status **Proposed → Accepted**(Option B server-side Conversation History pick + Wave A +3 backend days impact noted;6 NEW `/conversations` CRUD endpoints + Postgres `conversations` + `messages` tables per ADR-0023 backing pattern)
  - F0.4 `docs/adr/README.md` — rows for 0025/0028/0031 Status「Proposed」→「Accepted」+ context cells updated(W19 F6 Chris approval cascade outcome);footnote「Proposed 2026-05-16」→「Accepted 2026-05-16」
  - F0.5 `docs/architecture.md` — inline-tagged §5.x amendments(doc version held per the W18 ADR-0024 / §3.4 / §3.7 precedent):
    - **§5.2 Chat** — "advanced surfaces per ADR-0031" paragraph added(Conversation History server-side + 3 citation modes + InlineImageCard + ImageGallery + CitationPill + FeedbackBar + CRAG strip);C10 §7 Tier 2 → Tier 1 promotion note
    - **§5.3 Dashboard** — "ADR-0030 absorbed polish" paragraph(richer cards + 4-stat strip + per-component `/health` consumer)
    - **§5.4 KB List** — "polish — grid + table + filter bar" paragraph
    - **§5.5 KB Detail** — "7-tab refactor per ADR-0025 (Wave A ships `-Access`)" paragraph + Access tab Tier 1.5 deferral note
    - **§5.5.5 NEW** `/kb/new` 5-step wizard per ADR-0028 paragraph
    - **§5.10 + §5.11 Login + Register** — "Brand panel + Forgot password disabled affordance" paragraph
  - F0.6 `docs/01-planning/W20-frontend-wave-a/{plan,checklist,progress}.md` created — `status: active`(per Chris directive + 6 ADRs Accepted IS the authorization;same pattern as W17 D0 + W18 D0). Plan §2 deliverables F0-F9 = ADR-0025/0028/0031 + ADR-0030/0032 absorbed mapped
  - F0.7 `docs/12-ai-assistant/01-prompts/01-session-start.md` §10 W20 row added(`active`)+ §12 milestones row added(`draft`/`active` at kickoff;`closed` at F9)

- **Effort estimate**:0.5 day(W20 D0 kickoff — same-day as W19 F6 closeout)
- **Owner**:AI(draft)+ Chris(stakeholder verify ADR Status flips)

### F1 — `<AppShell>` topbar + sidebar polish per ADR-0032 absorbed scope(C09)

- **Component(s)**:**C09** Admin Console UI(nav components)
- **Spec ref**:architecture.md v6 §5.0 Application Shell(W18 ADR-0024)+ ADR-0032 absorbed scope(notification + workspace switcher + Tools sub-section + Labs hidden)
- **OQ deps**:none(NotificationsMenu either off backend or mock counter — no new OQ;Workspace switcher disabled affordance = known Tier 2 per architecture.md v6 §11)
- **Acceptance criteria**:
  - F1.1 NEW `frontend/components/nav/notifications-menu.tsx` — dropdown menu(shadcn `<DropdownMenu>`)triggered by `<Bell>` icon in top bar;reads `useQuery(['notifications'])` off `GET /notifications` if backend lands per W19 F2 item 21,else a static mock list(`['New KB document ingested', 'Eval run completed', ...]`)with a small counter badge;"Mark all read" + "See all →" CTA → `/notifications`(disabled affordance if backend absent)
  - F1.2 Workspace switcher **disabled affordance** — a `<DisabledAffordance>` chip in top bar(per W19 F5 catalog item)showing the current workspace name "Ricoh Asia Pacific (default)" with a `<DropdownMenuTrigger disabled>` + tooltip "Multi-workspace support — Tier 2(architecture.md §11)";fixes the W19 F1 §2.3 Tier 2 leak
  - F1.3 Sidebar Tools sub-section — group the existing 5 modules into 2 sections:**Main**(Dashboard / Chat / Knowledge Bases)+ **Tools**(Eval Console / Traces);labelled section headers via `<NavGroupHeader>` sub-component;flat list fallback preserved
  - F1.4 Sidebar Labs section **hidden by default**(per W19 F5.4 Option C);prototype-only `/labs/*` routes don't ship in `frontend/`(none created);if a future Tier 2 sprint enables Labs,the section header + items reactivate via an env flag
  - F1.5 NEW `frontend/components/ui/disabled-affordance.tsx` — shared `<DisabledAffordance>` component per W19 F5 spec:wraps children with `aria-disabled` + `title` + a small `(Tier 2)` badge;props for `tier` + `reason` + `tooltipText`;reused across F1.2 / F4 Multimodal Tier 2 / F7 Forgot password / F5 Access tab / etc.
  - F1.6 100% `tokens.ts`;`Grep '\[oklch'` across `frontend/` stays **0**(W18 milestone preserved);`tsc --noEmit` + `next lint` clean
  - F1.7 File header docstring(NEW files)+ Vitest test for `<DisabledAffordance>` + `<NotificationsMenu>` filter/click(F8 carries full test pass)
- **Effort estimate**:1 day(W20 D1 — small;the `<DisabledAffordance>` spec drives a lot of downstream consistency)
- **Owner**:AI(implementation)+ user(visual review of the new top-bar chips + Tools/Labs sectioning)

### F2 — `/dashboard` real cards per ADR-0030 absorbed scope(C09 + C07 + C02 + C06)

- **Component(s)**:**C09** Admin Console UI(view)+ consumes **C07** Observability(per-component health)+ **C02/C03** KB(summary)+ **C06** Eval(latest run if enabled)
- **Spec ref**:architecture.md v6 §5.3 Dashboard;ADR-0030 absorbed scope;W18 F4 placeholder evolves
- **OQ deps**:Q6 real query collection(Open → CTA per W18 F4 acceptance);eval-cache decision(no cached source → CTA per W18 F4 acceptance)
- **Acceptance criteria**:
  - F2.1 Backend — `backend/api/routes/health.py` extend `GET /health` payload from `{status: "ok"}` to `{status, components: {azure_search: {status, latency_ms?}, azure_openai: {status, latency_ms?}, cohere: {status, latency_ms?}, langfuse: {status, latency_ms?}, postgres: {status, latency_ms?}}}` — per W19 F2 §3.1 item 1;~0.5-1d C07;mypy strict
  - F2.2 Frontend rewrite `frontend/app/(app)/dashboard/page.tsx` — replaces W18 F4 placeholder 5 cards with the richer overview:
    - **(a) Top stat strip** — 4 stat cards(Total KBs / Total Documents / Total Chunks / Total Storage)from `kbApi.list()` aggregate
    - **(b) Knowledge bases** card — top-5 KB list + Σdocs/Σchunks/ΣMB + link → `/kb`(reuse from W18)
    - **(c) Recent queries** — empty-state CTA per Q6 Open(or top-5 list if `/queries/recent` endpoint lands)
    - **(d) Latest evaluation** — empty-state CTA per no-cached-source(or 4-metric stat if `/eval/runs/latest` lands)
    - **(e) System health** — per-component dots(F2.1 payload):Azure Search / OpenAI / Cohere / Langfuse / Postgres + latency badges + a "View details" link → `/admin/health`(disabled affordance Tier 2 if no detail page)
    - **(f) Quick actions** — 4 buttons(New KB / Upload Doc / Run Eval / Open Chat)reuse from W18
  - F2.3 Loading skeletons + error banners per card(reuse W17 F4.1 Documents pattern + W18 F4 pattern);empty states first-class
  - F2.4 Tokens — 100% `tokens.ts`;`tsc` + `next lint` clean;`[oklch`=0 preserved
  - F2.5 Vitest test for the dashboard render(extend W18 F8.4 `dashboard.test.tsx` — 5 cards heading test + 4-stat strip + per-component health dot count)
  - F2.6 File header docstring(rewritten file)
- **Effort estimate**:1.5 days(W20 D1-D2 — backend `/health` extension + frontend rewrite)
- **Owner**:AI(backend + frontend implementation)+ user(visual review — the richer "front door")

### F3 — `/chat` advanced surfaces per ADR-0031 Option B server-side Conversation History(C10 + C08)

- **Component(s)**:**C10** Chat Interface UI(view + sidebar)+ **C08** API Gateway(NEW endpoints)+ **C02** KB Manager(conversations persistence)
- **Spec ref**:architecture.md v6 §5.2 Chat;ADR-0031 Option B(promotes C10 §7 Tier 2 → Tier 1);ADR-0023 Postgres backing pattern
- **OQ deps**:none(ADR-0031 Option B server-side is decided;in-memory fallback per ADR-0023 pattern when `DATABASE_URL` unset)
- **Acceptance criteria**:
  - F3.1 **NEW backend** `backend/api/schemas/conversation.py` — Pydantic v2 schemas:
    - `Conversation`(id: UUID / user_id: str / title: str / kb_id: str | None / created_at: datetime / updated_at: datetime / message_count: int)
    - `Message`(id: UUID / conversation_id: UUID / role: Literal['user', 'assistant'] / content: str / citations: list[Citation] | None / created_at: datetime)
    - `ConversationCreate` / `ConversationUpdate` / `MessageCreate` request schemas
  - F3.2 **NEW backend** `backend/persistence/postgres_conversations.py` — `PostgresConversationStore` per ADR-0023 backing pattern:
    - `conversations` table(id PK / user_id FK to users / title / kb_id FK to kbs nullable / created_at / updated_at)
    - `messages` table(id PK / conversation_id FK to conversations CASCADE / role / content / citations JSONB nullable / created_at)
    - `make_conversation_store()` factory — Postgres backing if `DATABASE_URL` set,else `InMemoryConversationStore` fallback(W17 F1 pattern)
    - Alembic migration if applicable(or raw SQL DDL alongside per W17 F1 precedent)
    - mypy strict clean
  - F3.3 **NEW backend** `backend/api/routes/conversations.py` — 6 endpoints(per W19 F2 §3.2):
    - `POST /conversations` — create + return Conversation(no messages yet)
    - `GET /conversations` — list user's conversations(paginated;default 20)
    - `GET /conversations/{id}` — get with messages
    - `PATCH /conversations/{id}` — update title / kb_id
    - `DELETE /conversations/{id}` — soft delete(or hard — TBD at F3 kickoff)
    - `POST /conversations/{id}/messages` — append message(creates user + assistant messages atomically when used with `/query` flow)
    - All gated by `Depends(get_current_user)` per W17 F2 cookie/Bearer transport
    - pytest coverage ≥ 80%(per CLAUDE.md §3.1 H6;backend test file `tests/api/test_conversations_route.py`)
  - F3.4 **Frontend** `frontend/app/(app)/chat/page.tsx` rewritten with Conversation History sidebar(left collapsible pane,reuses `<AppShell>` focus-mode toggle pattern):
    - `useQuery(['conversations'])` off `GET /conversations` — list previous conversations
    - "New chat" button → `POST /conversations` → new conversation
    - Conversation list item click → loads messages via `GET /conversations/{id}` → renders in chat panel
    - Title auto-generated from first user message(first 50 chars or LLM-summarize — Tier 1 = simple slice)
    - Conversation rename(double-click title)+ delete confirmation modal
    - Existing SSE `/query` streaming logic preserved — only the message persistence layer added(`POST /conversations/{id}/messages` after assistant turn completes)
  - F3.5 **Frontend** 3 citation placement modes — tweaks toggle per W18 §5.5.4 precedent:
    - `inline` — citations appear as `[1] [2]` superscripts inside the assistant text
    - `footnote` — citations listed at bottom of each message
    - `sidebar` — citations panel pinned to right edge of chat view
    - Toggle in `<ChatHeader>` + persisted to `localStorage['ekp-citation-mode']`(W18 sidebar focus-mode pattern)
  - F3.6 **Frontend** `<InlineImageCard>` + `<ImageGallery>` + `<CitationPill>` hover popover:
    - InlineImageCard renders inline within assistant message when `citation.image_url` exists(consume W17 image schema)
    - ImageGallery aggregates all images at message end(grid)+ click → modal
    - CitationPill hover → popover with chunk preview + KB doc link
  - F3.7 **Frontend** `<FeedbackBar>` comment field — extend W17 thumbs-up/down with an optional text comment + tag dropdown(`['inaccurate', 'incomplete', 'off-topic', 'other']`)+ `POST /feedback` writes per existing W8 endpoint
  - F3.8 **Frontend** CRAG strip indicator — small horizontal strip above assistant message when `query.crag_triggered === true` showing "CRAG triggered — N iterations" + tooltip with the CRAG reasoning(consume `query.crag_iterations` + `query.crag_reasoning` from QueryResponse — verified per W19 F2 §3.1 item 5)
  - F3.9 Backend — verify `QueryResponse` schema includes `crag_triggered: bool` + `crag_iterations: int`(per W19 F2 item 5;~0.2d C05;if missing add)
  - F3.10 Tokens — 100% `tokens.ts`;`[oklch`=0 preserved;`tsc` + `lint` clean
  - F3.11 Vitest tests — Conversation list / 3 citation modes / InlineImageCard render / FeedbackBar comment submit / CRAG strip visibility(F8 carries full pass)
  - F3.12 File header docstrings(NEW + rewritten files)
- **Effort estimate**:3-4 days(W20 D2-D5 — largest deliverable;backend ~2 days + frontend ~2 days;ADR-0031 Option B +3 days impact per W19 F6)
- **Owner**:AI(backend + frontend implementation)+ user(UX review on history sidebar + citation mode toggle + image gallery)

### F4 — `/kb` list polish + `/kb/new` 5-step wizard per ADR-0028(C09 + C02 + C01)

- **Component(s)**:**C09** Admin Console UI(views)+ **C02** KB Manager(KbConfig schema)+ **C01** Ingestion(multimodal config consumption)
- **Spec ref**:architecture.md v6 §5.4-§5.5;ADR-0028 5-step wizard;W19 F2 §3.1 item 2(KbConfig multimodal fields)
- **OQ deps**:none(Multimodal Tier 1 active fields are decided per ADR-0028;Tier 2 affordances are documented)
- **Acceptance criteria**:
  - F4.1 Backend — `backend/api/schemas/kb.py` extend `KbConfig`(or new `KbMultimodalConfig` sub-model):
    - Tier 1 active:`extract_embedded_images: bool = False` + `slide_screenshots: bool = True`(PPT default per W3)+ `dedup_strategy: Literal['sha256', 'none'] = 'sha256'` + `return_images_in_chat: bool = False`
    - Tier 2 documented(not in schema yet — disabled affordance frontend-side only):`enable_caption_generation`,`image_clustering`,`provenance_blockchain`
    - `backend/ingestion/orchestrator.py` consume the new fields(per W19 F2 §3.1 item 2;~0.5d C02 + C01)
    - mypy strict + pytest fixture updates
  - F4.2 Frontend `/kb` list polish — `frontend/app/(app)/kb/page.tsx`:
    - **Grid view**(default — current behavior preserved)
    - **Table view** toggle — column headers + rows(`Name / Documents / Chunks / Storage / Last updated / Status / Actions`)
    - **Filter bar** — search by name + status dropdown(`active / archived / all`)+ sort dropdown(`name / created / updated`)
    - View toggle persisted to `localStorage['ekp-kb-list-view']`
  - F4.3 Frontend `/kb/new` 5-step wizard — `frontend/app/(app)/kb/new/page.tsx` rewritten with 5 step components(reuse W3 Stepper pattern from existing `/kb/[id]/upload`):
    - **Step 1 — Source**:Name + Description + optional Tags
    - **Step 2 — Parsing**:Docling profile picker(default / strict / lenient — disabled affordances if profiles not yet implemented;Tier 1 = default profile)
    - **Step 3 — Chunking**:strategy(`semantic / fixed / layout-aware`)+ chunk size + overlap(layout-aware default per ADR-0018)
    - **Step 4 — Multimodal**:Tier 1 active toggles(`extract_embedded_images` + `slide_screenshots` + `dedup_strategy` + `return_images_in_chat`)+ Tier 2 disabled affordances(`enable_caption_generation` / `image_clustering` / `provenance_blockchain` — each wrapped in `<DisabledAffordance tier={2} />` from F1.5)
    - **Step 5 — Review & Create**:summary table + `POST /kb` submit + redirect to `/kb/[id]`
    - Each step has `<Validate>` before "Next" — required fields enforced
    - Stepper navigation:back / next / cancel(per W3 Pipeline wizard pattern)
  - F4.4 100% `tokens.ts`;`[oklch`=0 preserved;`tsc` + `lint` clean
  - F4.5 Vitest tests — list view toggle + filter bar + 5-step wizard step transitions + Tier 2 affordances render disabled
  - F4.6 File header docstrings(rewritten files)
- **Effort estimate**:2 days(W20 D5-D6 — backend ~0.5d + frontend ~1.5d)
- **Owner**:AI(implementation)+ user(UX review on wizard step flow)

### F5 — `/kb/[id]` 7-tab Detail refactor per ADR-0025 minus Access(C09 + C01 + C02 + C03)

- **Component(s)**:**C09** Admin Console UI(7-tab view)+ **C01** Ingestion(Images + Chunking Lab consumers)+ **C02** KB Manager(Settings)+ **C03** Indexing(Chunks)
- **Spec ref**:architecture.md v6 §5.5 KB Detail;ADR-0025 8-tab(Wave A ships `-Access`);W19 F2 §3.1 items 6 + 7 + 8(POST archive + GET images + POST chunking-preview)
- **OQ deps**:Access tab depends on ADR-0027 Option A RBAC backend(Wave C1 — Access tab activates then)
- **Acceptance criteria**:
  - F5.1 Backend — `POST /kb/{kb_id}/archive` endpoint per W19 F2 §3.1 item 6;~0.3d C02;sets `kb.status = 'archived'`;guards user re-ingestion;pytest coverage;mypy strict
  - F5.2 Backend — `GET /kb/{kb_id}/images` enriched per W19 F2 §3.1 item 7;~1d C01 + C02 + C03;returns paginated image list with `{id, url, doc_id, doc_name, page_num, ocr_text, screenshot_type, created_at}`;reuse W2 F3 screenshot pipeline metadata;pytest coverage;mypy strict
  - F5.3 Backend — `POST /chunking-preview` endpoint per W19 F2 §3.1 item 8;~1.5d C01 + C03;takes `{kb_id, sample_doc_id?, strategy, chunk_size, overlap}` + returns N preview chunks(does NOT persist to index);reuses `layout_aware_chunker.py` from W2 F2;pytest coverage;mypy strict
  - F5.4 Frontend `frontend/app/(app)/kb/[id]/page.tsx` rewritten from 5-tab to 7-tab via shadcn `<Tabs>`:
    - **Tab 1 — Documents**(existing W17 F4.1 + CH-001 — preserved unchanged)
    - **Tab 2 — Chunks**(existing — preserved unchanged)
    - **Tab 3 — Images NEW** — consume `GET /kb/{kb_id}/images`;ImageGallery filter(by doc_id / screenshot_type)+ click-to-preview modal + OCR text overlay
    - **Tab 4 — Chunking Lab NEW** — consume `POST /chunking-preview`;controls(strategy + size + overlap)+ "Preview" button + live chunk preview list + "Apply" button(disabled affordance Tier 2 "re-chunking pending — Tier 2";current Tier 1 = preview-only,no destructive action)
    - **Tab 5 — Pipeline**(existing wizard — preserved unchanged per W3)
    - **Tab 6 — Retrieval Testing**(existing W18 ADR-0021 §5.5.4 + search-mode param — preserved unchanged)
    - **Tab 7 — Settings**(existing + NEW Danger zone with `POST /kb/{kb_id}/archive` — confirmation modal + warning text)
    - **Access tab disabled affordance** — 8th tab visible but `<TabsTrigger disabled>` + `<DisabledAffordance tier={1.5} reason="RBAC pending Wave C1 per ADR-0027 Option A backend" />` wrapper;clicking shows tooltip
  - F5.5 100% `tokens.ts`;`[oklch`=0 preserved;`tsc` + `lint` clean
  - F5.6 Vitest tests — 7-tab navigation + Access disabled assertion + Images grid render + Chunking Lab preview render
  - F5.7 File header docstrings(rewritten file + 3 new tab content files if split)
- **Effort estimate**:3.5 days(W20 D6-D8 — backend ~2.8d + frontend ~0.7d;backend is the long pole — 3 NEW endpoints)
- **Owner**:AI(backend + frontend implementation)+ user(UX review on Images + Chunking Lab + Access disabled assertion)

### F6 — `/kb-upload/[id]` re-ingestion wizard polish per ADR-0028 §5.5.3b(C09)

- **Component(s)**:**C09** Admin Console UI(existing 3-step skeleton polish)
- **Spec ref**:architecture.md v6 §5.5 + ADR-0028 §5.5.3b
- **OQ deps**:none
- **Acceptance criteria**:
  - F6.1 Frontend `frontend/app/(app)/kb/[id]/upload/page.tsx` polish — existing 3-step skeleton(Source → Confirm → Run)preserved + apply same Tier 1/Tier 2 Multimodal affordance pattern from F4(Source step add Multimodal toggles per KB's existing config;Tier 2 affordances via `<DisabledAffordance>`)
  - F6.2 Re-uses F4 wizard step components where possible(DRY per Karpathy §1.2)
  - F6.3 100% `tokens.ts`;`[oklch`=0 preserved;`tsc` + `lint` clean
  - F6.4 Vitest test — 3-step navigation + Multimodal toggle render
  - F6.5 File header docstring updated
- **Effort estimate**:0.5 day(W20 D8 — polish + DRY only)
- **Owner**:AI(implementation)+ user(spot-check)

### F7 — `/login` + `/register` polish per ADR-0014(C11 + C09)

- **Component(s)**:**C11** Identity & Access(redirect paths preserved)+ **C09**(visual polish)
- **Spec ref**:architecture.md v6 §5.10-§5.11;ADR-0014 hybrid auth;ADR-0022 cookie/Bearer transport(preserved)
- **OQ deps**:Q11 Track A IT cred — Wave A does NOT block(mock-auth default per user 岔口 2;real-MSAL ship Wave C)
- **Acceptance criteria**:
  - F7.1 `frontend/app/login/page.tsx` polish — Brand panel slot integration(reuse `frontend/components/auth/brand-panel.tsx` from W13)+ Forgot password link **disabled affordance**(`<DisabledAffordance tier={2} reason="Self-register password reset — Tier 2 per architecture.md §11" />` chip + tooltip "Coming in a later tier");redirect target unchanged(`/dashboard` per W18 F7)
  - F7.2 `frontend/app/register/page.tsx` polish — same Brand panel slot pattern + 5-step wizard navigation preserved(W13);Step 3 "Welcome" CTA preserved(`/dashboard` per W18 F7);no other functional change
  - F7.3 100% `tokens.ts`;`[oklch`=0 preserved;`tsc` + `lint` clean
  - F7.4 Vitest test — Forgot password disabled affordance render + Brand panel slot present
  - F7.5 File header docstrings updated
- **Effort estimate**:0.5 day(W20 D8 — small polish only)
- **Owner**:AI(implementation)+ user(visual review on Brand panel placement)

### F8 — Cross-cutting:responsive + a11y + dark-mode + tests + COMPONENT_CATALOG

- **Component(s)**:cross-cutting(C09 + C10 + C11 + test harness + docs)
- **Spec ref**:architecture.md v6 §5.0 + §5.8;CLAUDE.md §3.2 + §3.3 + §12 self-verification
- **OQ deps**:F1-F7 baseline
- **Acceptance criteria**:
  - F8.1 Responsive pass on new surfaces — `<NotificationsMenu>` + `<DisabledAffordance>` chips + `/dashboard` 4-stat strip + `/chat` Conversation History sidebar + `/kb/new` 5-step wizard + `/kb/[id]` 7-tab nav at `sm` / `md` / `lg` / `xl`;multi-viewport browser smoke = user pre-Beta walkthrough(R8 / CO_W15_F4_browser_binaries — same caveat shape as W18)
  - F8.2 a11y pass on **new** surfaces only(full NVDA/JAWS/VoiceOver audit stays Tier 2 / CO_W15_F3_aria_full_audit):
    - `<NotificationsMenu>` `<DropdownMenu>` Radix gives `role="menu"` + `aria-haspopup`(verified)
    - `<DisabledAffordance>` chips have `aria-disabled="true"` + `title` + visible `(Tier 2)` badge
    - `/chat` Conversation History sidebar `<nav aria-label="Conversation history">` + each item `role="link"`
    - `/kb/new` 5-step wizard — each step `role="form"` + step indicator `aria-current="step"`
    - `/kb/[id]` 7-tab `<TabsList role="tablist">` + each `<TabsTrigger role="tab" aria-selected>` + Access disabled `aria-disabled`(Radix Tabs gives this for free)
  - F8.3 Dark-mode re-check — `Grep '\[oklch'` across `frontend/` = **0**(W15/W18 milestone preserved through F1-F7);next-themes mechanism unchanged
  - F8.4 Vitest expansion — W18 F8.4 baseline 4 files/13 tests → W20 target 6-8 files/20+ tests:
    - NEW `tests/unit/notifications-menu.test.tsx`
    - NEW `tests/unit/disabled-affordance.test.tsx`
    - NEW `tests/unit/conversation-history.test.tsx`(extends `<ConversationHistorySidebar>` render)
    - NEW `tests/unit/kb-new-wizard.test.tsx`(extends 5-step navigation)
    - NEW `tests/unit/kb-detail-tabs.test.tsx`(7-tab nav + Access disabled assertion)
    - Existing `dashboard.test.tsx` extended for 4-stat strip + per-component health
    - `pnpm test:unit` → 20+/20+ pass
  - F8.5 Playwright E2E updates:
    - `app-shell-path.spec.ts` — verify `<NotificationsMenu>` + workspace switcher disabled chip present in top bar across all routes
    - `golden-path.spec.ts` — extend chat flow to include "create new conversation → send message → conversation persists in sidebar → reload page → conversation still shown"(server-side persistence test)
    - `visual-baseline.spec.ts` — re-baseline `/dashboard` + `/chat`(new chrome)+ NEW snapshots for `/kb/new` step 1 + `/kb/[id]` Images tab + Chunking Lab tab
    - `tsc --noEmit` compile-check;full run = user pre-Beta smoke(R8)
  - F8.6 `docs/02-architecture/COMPONENT_CATALOG.md` — C01/C02/C03/C05/C07/C08/C09/C10 status notes appended with W20 Wave A amendment(per ADR-0025/0028/0031 + ADR-0030/0032 absorbed scope)
  - F8.7 `references/design-mockups/PAGE_INVENTORY.md` — Cn mapping rows for the 7 W20-implemented routes update from "prototype" to "implemented W20"
- **Effort estimate**:1 day(W20 D9)
- **Owner**:AI(implementation + browser smoke)+ user(keyboard nav + responsive spot-check + the interactive 7-tab walkthrough — the pre-Beta smoke)

### F9 — Phase closeout + W21+ rolling-JIT trigger

- **Component(s)**:cross-cutting governance
- **Spec ref**:CLAUDE.md §10 R1 + R5 closeout
- **OQ deps**:F1-F8 verdict outcomes
- **Acceptance criteria**:
  - F9.1 W20 phase Gate verdict landed(PASS / PARTIAL PASS / FAIL with explicit rationale per the W18 pattern)
  - F9.2 W20 `progress.md` retro — 7 sections(What worked / What didn't & friction / Surprises / Decisions / Carry-overs to W21+ / Time tracking / Spec ref alignment)
  - F9.3 ADR-0025 + ADR-0028 + ADR-0031 Status verified `Accepted`(landed at this phase's kickoff;verify-no-op)+ Implementation Deliverables checkboxes ticked(7-tab `-Access` shipped Wave A per ADR-0025;5-step wizard shipped per ADR-0028;Option B server-side Conversation History shipped per ADR-0031)
  - F9.4 W20 `plan.md` + `checklist.md` + `progress.md` frontmatter `status: active` → `closed`
  - F9.5 W21+ phase folder **NOT pre-created**(rolling-JIT — kickoff post-W20-closeout decision;likely candidate = W21-frontend-wave-b per W19 F4 §2;OR W22-frontend-wave-c1 per F4 §3.6 split decision;OR W16 F1-F4 if Track A IT cred lands;decision at W20 closeout)
  - F9.6 `session-start.md` hygiene catch-up — §3 C01/C02/C03/C05/C07/C08/C09/C10 status(W20 Wave A amendments)+ §10 W20 row(closed, Gate verdict)+ W21+ not-pre-created + §11 carry-overs(W20-closed items + any new 🚧 deferrals)+ §12 milestones row + Last-Updated + Update-history;`COMPONENT_CATALOG.md` + `PAGE_INVENTORY.md` already touched in F8.6 + F8.7
  - F9.7 New OQ surfaced(if any) → sync `decision-form.md` per R4;ADR-0030 + ADR-0032 SKIPPED footnote preserved per W19 F6 closeout
- **Effort estimate**:0.5 day(W20 D10 or absorbed)
- **Owner**:AI(draft)+ user(approve + sign-off)

---

## 3. Success Criteria(Phase Gate)

W20 phase Gate **PASS condition**:
1. F1 `<AppShell>` polish — NotificationsMenu + Workspace switcher disabled affordance + Sidebar Tools sub-section + Labs hidden + `<DisabledAffordance>` shared component;`tsc`+`lint` clean;`[oklch`=0
2. F2 `/dashboard` real cards — per-component `/health` payload + 5 cards + 4-stat strip;no new backend except `/health` extension;empty states first-class
3. F3 `/chat` advanced — Conversation History sidebar server-side(Postgres-backed per ADR-0023)+ 6 NEW `/conversations` CRUD endpoints + 3 citation modes + InlineImageCard + ImageGallery + CitationPill + FeedbackBar comment + CRAG strip;backend test coverage ≥ 80% on new routes
4. F4 `/kb` + `/kb/new` — list polish(grid + table + filter)+ 5-step wizard(Source / Parsing / Chunking / Multimodal Tier 1+2 / Review)+ KbConfig multimodal fields backend-side
5. F5 `/kb/[id]` 7-tab — Documents + Chunks + Images + Chunking Lab + Pipeline + Retrieval Testing + Settings(`-Access` disabled affordance);3 NEW backend endpoints(POST archive + GET images + POST chunking-preview)
6. F6 `/kb-upload/[id]` polish — Multimodal Tier 1/2 affordance pattern applied
7. F7 `/login` + `/register` polish — Brand panel + Forgot password disabled affordance
8. F8 responsive + a11y + dark-mode `[oklch`=0 preserved + Vitest 20+/20+ pass + Playwright route updates + COMPONENT_CATALOG.md + PAGE_INVENTORY.md notes
9. F9 closeout + `session-start.md` hygiene + W21+ rolling-JIT trigger

W20 phase Gate **PARTIAL PASS** acceptable per Karpathy §1.4:
- F2(c) Recent queries / F2(d) Latest evaluation — empty-state CTAs preserved per W18 F4 pattern(no Q6 enable / no eval-cache enable;PARTIAL acceptable)
- F8.1 multi-viewport browser smoke — deferred → user pre-Beta(R8 / CO_W15_F4_browser_binaries)— responsive classes are the deliverable
- F8.5 Playwright full run — same R8 caveat as W18(spec compile-check is the deliverable;run = user pre-Beta smoke)
- F3.4 conversation title auto-gen — first-50-char slice is acceptable(LLM-summarize = Tier 2)
- F5 Chunking Lab "Apply" button — disabled affordance preserved(re-chunking = Tier 2;preview-only Tier 1)
- a11y — spot-check on new surfaces only(full screen-reader audit stays Tier 2)

W20 phase Gate **FAIL condition**:
- Tier 2 leak — implementing real workspace multi-tenancy(Workspace switcher must stay disabled affordance);implementing Labs functionality;promoting Tier 2 multimodal fields(caption gen / image clustering / blockchain)
- Access tab activated without ADR-0027 Option A backend(must stay disabled affordance until Wave C1)
- 7-tab refactor breaks existing 5-tab content(Documents / Chunks / Pipeline / Retrieval Testing / Settings must be preserved unchanged — additive Images + Chunking Lab only)
- ADR-0031 Option B server-side conversation history NOT implemented(localStorage Tier 1 = Option A,was REJECTED per W19 F6 Chris pick;Option C Tier 2 defer = also rejected)
- 2 NEW dependencies(Key Vault SDK / Entra Graph SDK)added in Wave A(they're Wave C — per ADR-0017 Plan B sequencing decision deferred)
- mock-auth default broken — real-MSAL feature flag accidentally enabled(per user 岔口 2 — mock-auth continues through Wave C)
- `frontend tsc --noEmit` / `next lint` regression(must stay clean);`pnpm test:unit` regression below W18 F8.4 baseline 4 files/13 tests
- `[oklch`=0 milestone broken(W15/W18 milestone must hold through Wave A)
- Backend test coverage on new `/conversations` routes < 80%(per CLAUDE.md §3.1 H6)

## 4. Risks(Phase-Specific)

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| `/conversations` Postgres migration breaks local dev w/o `DATABASE_URL` | Medium | Medium | Reuse ADR-0023 in-memory fallback pattern from W17 F1(`make_conversation_store()` factory);unit-test both backings;document the env-var trigger in `docs/setup.md` |
| 7-tab refactor breaks existing 5-tab content | Medium | High | Surgical per Karpathy §1.3 — Tab 1/2/5/6/7 = preserved unchanged(`git mv` if needed);only Tab 3/4 are NEW;grep-verify existing tab content unchanged after refactor;Vitest assertion that the 5 preserved tabs render existing markers |
| F3 advanced chat surfaces sprawl beyond scope(toggle proliferation) | Medium | Medium | Strict per-acceptance-criteria scope;3 citation modes max(inline / footnote / sidebar);no fuzzy semantic search;CRAG strip = info-only chip(no interactive)— same simplicity-first as W18 |
| Multimodal Tier 1 active fields conflict with W2 ingestion default behavior | Low | High | KbConfig defaults preserve W2 behavior(`extract_embedded_images=False` + `slide_screenshots=True` PPT-default);existing KBs pre-W20 get the defaults retroactively via migration default value;backend test asserts old-shape config still parses |
| ADR-0031 Option B server-side persistence + +3 backend days squeezes other Wave A items | High | Medium | F9 PARTIAL PASS allowances above + W19 F4 §1.3 documented the +3d impact;real-calendar collapse pattern(1.8-4× per W12-W18)gives ~3-5 actual days vs ~12 plan-day budget — buffer exists;Wave B is sequential not parallel |
| `<DisabledAffordance>` consistency drift across Wave A surfaces | Medium | Low | F1.5 shared component spec enforced via Vitest test + grep-verify(`<DisabledAffordance>` is the ONLY way to render a Tier 2 chip — no ad-hoc `disabled` + `Tier 2` strings) |
| `npx playwright install chromium` still R8-blocked(W18 same risk) | High | Low | Known(CO_W15_F4_browser_binaries / ADR-0017 Plan B realised W15 D5 + 2026-05-13 via `PW_CHANNEL=chrome`);F8.5 deliverable = spec compile-check + the run via `PW_CHANNEL=chrome pnpm test:e2e`(uses system Chrome per ADR-0017 Plan B (a)) |
| Q6 real query collection backend lands mid-W20 | Low | Low | F2.2(c) empty-state CTA → data wire if `/queries/recent` endpoint becomes available;documented as scope-creep allowance(per Karpathy §1.2 don't pre-build) |
| ADR-0027 Option A RBAC backend leaks into Wave A | Medium | Medium | Access tab MUST stay disabled affordance(F5.4 acceptance criteria);grep-verify no `from backend.api.routes.users import` or `roles` table reference in Wave A code;Wave C1 owns the activation |

## 5. Day-by-Day Breakdown(rough)

| Day | Date(tentative) | Focus |
|---|---|---|
| W20 D0 | 2026-05-16 | Kickoff — 6 ADRs Accepted(0025/0026/0027/0028/0029/0031)+ ADR README sync + `architecture.md v6 §5` inline-tagged amendments(§5.2 + §5.3 + §5.4-§5.5 + §5.10-§5.11)+ this `plan.md` + `checklist.md` + `progress.md` created(`status: active`)+ `session-start.md` §10 W20 row + §12 milestones row added |
| W20 D1 | 2026-05-17 | F1 — `<NotificationsMenu>` + `<DisabledAffordance>` shared component + Workspace switcher disabled chip + Sidebar Tools sub-section + Labs hidden |
| W20 D2 | 2026-05-18 | F2 — `/health` per-component payload(backend)+ `/dashboard` 5 cards + 4-stat strip(frontend) |
| W20 D3-D5 | 2026-05-19 to 2026-05-21 | F3 — `/conversations` Pydantic schemas + `PostgresConversationStore` + 6 CRUD endpoints + Vitest backend ≥ 80% coverage + Frontend Conversation History sidebar + 3 citation modes + InlineImageCard + ImageGallery + CitationPill + FeedbackBar + CRAG strip(largest deliverable) |
| W20 D5-D6 | 2026-05-21 to 2026-05-22 | F4 — KbConfig multimodal fields(backend)+ `/kb` list polish(grid + table + filter)+ `/kb/new` 5-step wizard(frontend) |
| W20 D6-D8 | 2026-05-22 to 2026-05-24 | F5 — 3 NEW backend endpoints(POST archive + GET images + POST chunking-preview)+ `/kb/[id]` 7-tab refactor(Tab 3 Images + Tab 4 Chunking Lab NEW;preserve 5 existing tabs;Access disabled affordance) |
| W20 D8 | 2026-05-24 | F6 — `/kb-upload/[id]` polish + F7 — `/login` + `/register` Brand panel + Forgot password disabled affordance |
| W20 D9 | 2026-05-25 | F8 — responsive + a11y + dark-mode re-check + Vitest expansion 20+ tests + Playwright route updates + COMPONENT_CATALOG.md + PAGE_INVENTORY.md notes |
| W20 D10 | 2026-05-26 | F9 — closeout(Gate verdict + retro + ADR-0025/0028/0031 D-ticked + frontmatter `closed` + `session-start.md` hygiene + W21+ rolling-JIT trigger) |

**Day-by-day caveat**:dates tentative;real-calendar collapse is the W12-W18 pattern(actual ~3-5 days vs ~12 plan-day budget). The `start_date`/`end_date` frontmatter is a window, not a commitment. If overflow:F6/F7/F8 absorb into D10 or W21+ D1;F3 is the long pole(backend + frontend both).

## 6. Dependencies on Prior Phase / Carry-overs Addressed

From `session-start.md` §11 + W19 retro carry-overs — W20 directly addresses:
- **ADR-0025 + ADR-0028 + ADR-0031 implementation** — the whole phase(F0 Status flip Proposed→Accepted + F1-F8 implement the 6 ADRs Accepted scope per W19 F6)
- **Wave A backend foundation** — 9 backend items from W19 F2 §3.1 + §3.2(items 1+2+5+6+7+8 + ADR-0031 Option B items 9+10;items 3+4 Q6/Eval-cache defer per W18 F4 acceptance)
- **`<DisabledAffordance>` shared component** — W19 F5 spec consumed F1.5;reuse across F1.2 Workspace switcher + F4 Multimodal Tier 2 + F5 Access tab + F7 Forgot password
- **F5.4 `/labs/*` Option C prototype-only** — W19 F5 decision enforced(no `/labs/*` routes ship in Wave A `frontend/`)
- **W19 F1 §2.3 Tier 2 leak fix** — Workspace switcher disabled affordance(F1.2)closes the leak

W20 does **NOT** address(stay Wave B / Wave C / Tier 2 / W16 / future):
- ADR-0029 `/doc-detail` 3-pane — **Wave B** W21
- ADR-0026 `/settings` 6-tab — **Wave C** W22
- ADR-0027 `/users` 4-tab Tier 1.5 RBAC — **Wave C1** W22(forces Access tab activation in Wave A's `/kb/[id]`)
- `/traces` index + `/traces/[traceId]` 3 viz modes — **Wave B** W21(ADR-0030 absorb split — Dashboard part = Wave A;Trace + /traces parts = Wave B)
- `/eval` Eval Console refactor — **Wave B** W21
- Real-MSAL feature-flagged ship — **Wave C** W22(mock-auth default through Wave C per user 岔口 2)
- 2 NEW dependencies(Key Vault SDK + Entra Graph SDK)— **Wave C kickoff** per ADR-0017 Plan B sequencing decision
- CO16 Track A IT cred populate event + R-B1 closure(W16 F1 — external dependency;W20 unaffected)
- CO17 — 🚧 F1.5b Postgres-path runtime smoke + 🚧 F3.5b RAGAs live-verify(R8/Azure-key-bound;W20 doesn't touch — F3 uses Postgres backing pattern but in-memory fallback is the dev path)
- CO19 25% Beta cohort rollout activation(W16 F2)
- CO_F6a/b/c ACS email retry / BackgroundTasks / SPF-DKIM(Track A — W16 F1)
- CO_W15_F1_eval_set_v1 — `eval-set-v1.yaml` final still needs Chris's SME reference-answer labels(unrelated to Wave A)
- CO_W15_F3_aria_full_audit — full NVDA/JAWS/VoiceOver audit(Tier 2;W20 F8.2 = new-surface spot-check only)
- CO13 / AF3 code fix(ADR-0013 reserved)— unrelated to Wave A
- ADR-0030 + ADR-0032 — SKIPPED per W19 F6(absorbed scope shipped Wave A F1 + F2;no separate ADR record)

## 7. Plan Changelog

| Date | Change | Reason | Approver |
|---|---|---|---|
| 2026-05-16 | Initial draft + `status: active` + W20 folder created(`plan.md` + `checklist.md` + `progress.md`)| Chris directive at the W19-frontend-audit-and-adr-draft F6 closeout session:「next session 第 1 件事 = W20-frontend-wave-a kickoff cascade」 + AskUserQuestion A1 pick「W20-wave-a 7-tab kickoff (Recommended)」 = the post-Wave-breakdown(W19 F4)+ post-6-ADR-Acceptance(W19 F6)implementation authorization per CLAUDE.md §10 R1 + R5(ADR-before-implement discipline). F1-F9 map onto ADR-0025/0028/0031 scope + ADR-0030/0032 absorbed scope. `architecture.md v6 §5` inline-tagged amendments(§5.2 + §5.3 + §5.4-§5.5 + §5.5.5 NEW + §5.10-§5.11)+ 3 ADR Status flips Proposed→Accepted + ADR README sync + `session-start.md` §10 W20 row + §12 milestones row + Update-history all landed at this kickoff. | Chris(stakeholder + architecture decision owner)|
| 2026-05-17 | **F6 scope adjustment** — plan F6.1 literal「existing 3-step skeleton preserved」實際係 single-step file picker(74-line `kb/[id]/upload/page.tsx` 冇 wizard structure)。AskUserQuestion 三選一 picked **Option 1**:Build 出 3-step wizard skeleton(Source file picker → Multimodal read-only display per KB existing config → Review summary + Stage progress)+ reuse F4 file-local primitives(`<Field>`/`<Stepper>`/`<ToggleRow>`/`<Stage>`/`<Summary>`)inline-redeclared per W13 register page strategy(Karpathy §1.2 rule-of-3 promotion trigger NOW hit — 4th wizard usage observed:F4 KB Pipeline + W13 Register + W18 F5 Pipeline + W20 F6 Re-ingestion — extract to shared `frontend/components/ui/stepper.tsx` 為 **Wave B+ candidate**;Wave A 唔做 ripple change)。Per-doc Multimodal override 唔可行(W20 F4.2 orchestrator `ingest()` 接受 `kb_config: KbConfig | None` per-KB level via `service.get(kb_id)`),所以 Step 2 顯示 read-only KB config snapshot + link 去 `/kb/[id]?tab=settings` 改設定。 | AskUserQuestion 三選一 picked Option 1 by Chris 2026-05-17 |
| 2026-05-17 | **F7 Login visual hierarchy realign** — `references/design-mockups/ekp-page-auth.jsx` mockup vs current(W17 F2 ADR-0022 reordering)顛倒。AskUserQuestion 三選一 picked **Option 2**:strict design fidelity per §3.2.1 — SSO primary(top)+ Divider「OR continue with email」+ email/password secondary;Forgot password 移上 Password label 同一行 right-aligned + Tier 2 badge via shared `<DisabledAffordance>`;底部加 mono dashed-border「Auth modes (Tier 1)」block。Mock-auth-default dev reality 唔變(SSO button 喺 dev mode 仍係 mock signIn — backend handler 唔換)。 | AskUserQuestion 三選一 picked Option 2 by Chris 2026-05-17 |
| 2026-05-17 | **F7 Register mockup-vs-backend conflict resolution** — mockup design-stage `<a>` email-link 2-step verify 同 architecture.md v6 §3.7 + ADR-0014 backend 6-digit code 3-step contract 衝突。權威排序(§4)backend wins。AskUserQuestion 三選一 picked **Option 2**:keep 3-step 6-digit structure,選擇性遷移 visual polish 部分 — Step 1 field 順序改 = Full name → Email → Password + Confirm Password(mockup 冇 confirm 但 backend validation 保留)、加「I agree to Terms of Use + Privacy Policy」checkbox、Hint copy 具體化(scrypt-hashed via ADR-0022 + ≥ 12 chars + @ricoh.com Beta cohort restriction)。Step 3 KB selector disabled affordance 遷移到 shared `<DisabledAffordance>`。 | AskUserQuestion 三選一 picked Option 2 by Chris 2026-05-17 |

---

**Lifecycle reminder**:呢份 plan `status=active`(2026-05-16,per Chris directive + 6 ADRs Accepted + AskUserQuestion A1 pick)。重大 deviation 入第 7 節 changelog(per R3)。Next-phase folder(W21+)**唔會** pre-create(per CLAUDE.md §10 R1 rolling-JIT)。
