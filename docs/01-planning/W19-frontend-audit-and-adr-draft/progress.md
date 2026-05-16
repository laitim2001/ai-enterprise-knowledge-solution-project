---
phase: W19-frontend-audit-and-adr-draft
plan_ref: ./plan.md
checklist_ref: ./checklist.md
status: active
last_updated: 2026-05-16
---

# Phase W19 — Progress

> Daily log + decisions + commits + closing retro。每 commit 對應一個 Day-N entry mention(R2;`docs(planning):` / `docs(adr):` housekeeping commits exempt)。
> Plan deviation → `plan.md` §7 changelog（R3）。OQ resolved → `decision-form.md` + Day-N mention（R4）。
> **W19 is audit + ADR drafts + planning only — NO `frontend/` code change in this phase**。

---

## Day 0 — Kickoff(2026-05-16)

### Trigger

W18-app-shell-ia closed 2026-05-11(phase Gate PASS WITH SMOKE-USER-DEFERRED CAVEAT)→ `references/design-mockups/` high-fidelity HTML prototype + 17 `ekp-page-*.jsx` + DESIGN_README + PAGE_INVENTORY landed in repo 2026-05-16(commit `08b74af`,with `.gitignore` exception + CLAUDE.md v1.4→v1.5 routing + session-start.md §5 entry + Update history row).

The user(Chris)directive same-day 2026-05-16:「現在我們可以先把 design-mockups 的內容 先進行實作,因為之前即使把項目的規劃內容都準備了大部分,但是前端的部分其實一直都沒有規劃好,而且也不太能夠表達項目所實現了的功能流程,現在可以完整地去運用這些mockup內容,把這些前端的部分都完整地準備出來,之後再逐一把裡面的UIUX流程對應到不同的後端功能部分,當然如果發現是現在的後端功能還不支援,就會思考和規劃如何能夠讓它們能被實現,這就是我們接下來要最高優先去執行的工作」

AI surface(per CLAUDE.md §5.1 H1 + §10 R1)— the design-mockups → real-`frontend/` implementation is a **multi-sprint Phase work** that triggers:
1. **H1 architectural change**:3 known design-stage expansions(KB Detail 5→8 tabs / Settings v1→6 tabs / `/users` NET NEW Tier 1.5) + at audit 2 more(`/kb/new` 5-step vs spec 3-step / `/doc-detail/...` route + 3-pane layout vs spec `/admin/kb/[id]/chunks/[doc_id]` chunk inspector) → 5 ADRs required
2. **Backend gap** larger than frontend code work — esp. Settings → Connections / API Keys / `/users` RBAC have no current backend support
3. **R1 binding**:no multi-day implementation without plan;rolling JIT discipline favors splitting into multiple sub-phases over one big phase

AI proposed phase structure(W19 = audit-and-adr-draft / W20–W22 = Wave A/B/C implementation / W23+ Tier 2 hold) + 2 AskUserQuestion strategic decisions:

1. **First step** — user picked: "W19 audit-and-adr-draft phase folder kickoff(推薦)" → this phase
2. **Track A auth path** — user picked: "Mock-auth 繼續做 default,W22 同時 ship mock + real(推薦)" → W22 Wave C concurrently ships mock-auth + real-MSAL feature-flagged;independent of Track A IT cred landing time

岔口 1 (/users RBAC scope) + 岔口 2 (Settings Connections scope) deferred to F6 Chris review session — ADR-0026 + ADR-0027 will be drafted as option sets,Chris picks at F6 + the picked option becomes the Accepted ADR.

### Kickoff cascade(`(this commit)`)

- **W19 phase folder created** — `docs/01-planning/W19-frontend-audit-and-adr-draft/{plan,checklist,progress}.md` + `audit/.gitkeep`;`status: active`(per user directive — same Day-0-flip pattern as W17 D0 / W18 D0,not the usual draft→active flip;the directive + AskUserQuestion answers ARE the authorization per CLAUDE.md §5.1 H1)— `(this commit)`
- **Plan §2 deliverables F0–F6** = audit + ADR drafts + planning(NOT ADR-D1-D9 mapping like W18 — W19 is the **plan phase** for the design-mockups work,not the implementation of any single ADR;the 5 ADRs are themselves F3 deliverables)— `(this commit)`
- **Out-of-W19-scope explicit**:NO `frontend/` code change;NO new backend endpoint;NO `architecture.md v6 §5` amendment(F3 ADR drafts *propose* the amendments — actual inline-tag edits land per-ADR in W20+ kickoffs);NO Cn design-note rewrites;NO Tier 2 implementation;NO Track A activation
- **ADR-0025 / 0026 / 0027 / 0028 / 0029 reserved** in `docs/adr/README.md`(F0.3 — landed at kickoff so concurrent AI sessions see the reservations);"Next NNNN" advances 0025 → 0030
- **session-start.md §10 W19 row** — landed at kickoff(not closeout)— per the W17→W18 precedent the active-phase signal needs to be visible Day 0(F0.4)
- **No `architecture.md` amendment** at W19 kickoff — different from the W18 pattern where ADR-0024 amendment landed at W18 kickoff because ADR-0024 was already Accepted before W18 started;W19 starts with ADRs in *Proposed* state — amendments land per-ADR in W20+ kickoff each invokes(F0.5)

### Pre-kickoff state notes(grounding the audit)

- **W18 IA chrome locked** — `<AppShell>` top bar + collapsible sidebar(5 modules)+ main content + Cmd+K + flat URLs + login-gate + `/dashboard` + `/settings` are the LOCKED ground for W20+ implementation;W19 audit confirms the prototype adheres + W20+ work fills in,not re-IA
- **Design tokens locked** — `tokens.ts` Warm Charcoal + Coral Accent oklch + Inter + JetBrains Mono + radius 0.25/0.5/0.75rem — per ADR-0015 W12 D2;prototype `styles.css` mirrors this;F1.4 audits the match
- **shadcn/ui + Lucide locked**(H2)— prototype DESIGN_README acknowledges + ships its own stripped components for portability;**Wave A-C real implementation must use shadcn/ui + Lucide**(not the prototype's stripped components)
- **Backend baseline state** — W17 F3 RAGAs 4-metric integrated into `/eval/run`+`/eval/shootout`(real backend Wave B-ready);W16 F5 stub closure cascade done(`debug/trace/{id}` + KB doc listing real Wave B-ready);CH-001(per-doc upload/reindex/delete 24 backend tests) closed 2026-05-12 — `/kb/[id]/upload` + Pipeline tab fundamentally backed;**Settings + /users + per-component `/health` = the big backend gaps F2 maps**
- **Mock-auth default** — `FEATURE_AUTH_MOCK=true` / `NEXT_PUBLIC_AUTH_MOCK=true` continues default through W22(per user 岔口 2 decision);real MSAL feature-flagged + ready-to-flip when Track A IT cred lands
- **R8 corp-proxy state** — 7 cumulative occurrences;3 Plan B realised(Playwright system-Chrome 2026-05-13 / Azurite native npm 2026-05-14 / Langfuse SDK mobile hotspot 2026-05-16);no R8 dependency for W19(audit-only,no install needed)

### Carry-overs addressed by W19(from session-start.md §11 + W18 retro)

| Carry-over | W19 deliverable |
|---|---|
| design-mockups landed implementation kickoff(user directive 2026-05-16)| F0-F6 = the audit + ADR + plan phase that authorizes W20+ implementation |
| `<LoginGate>` `// TODO(W16)` tightening(real-MSAL `router.replace('/login')` once Q11 Track A cred wiring is live)| F3 ADR-0027 RBAC scope decision influences when this flips;user 岔口 2 = Wave C ships mock+real both,independent of Track A timing |
| Dashboard "recent queries" + "latest evaluation" empty-state CTAs | F2 backend gap map identifies the missing endpoints(Q6 query log + eval-run cache);Wave A may or may not fill,depending on ADR-0026 Option scope |
| Dashboard "system health" → richer `/health`(per-component connectivity)| F2 documents the gap;Wave A `/dashboard` System health stays backend-up/down liveness until Wave C Settings → Connections "test connection" lands |
| CO_W15_F3_dark_mode_visual_verify + CO_W15_F4_interactive_flow_E2E | NOT advanced by W19(audit-only);Wave A E2E picks them up;user pre-Beta smoke caveat preserved |

W19 does **NOT** address(stay W16 / Tier 2 / parallel track):

- CO16 Track A IT cred + R-B1(W16 F1 — parallel,Wave C ships mock+real per user 岔口 2)
- CO17 🚧 F1.5b(Postgres-path runtime smoke)+ 🚧 F3.5b(RAGAs live-verify Azure-key-bound)— W19 audit-only,no install
- CO19 25% Beta cohort rollout(W16 F2 — Beta phase parallel)
- CO_F6a/b/c ACS email retry / BackgroundTasks / SPF-DKIM(Track A)
- CO_W15_F1_eval_set_v1 — needs Chris SME labels per Q14(unrelated)
- CO_W15_F3_aria_full_audit — Tier 2 full screen-reader audit(W19 audit-only)
- CO13 / AF3(ADR-0013 reserved)

### Actual vs Planned Effort(running — fill per day)

| Deliverable | Planned | Actual | Variance / note |
|---|---|---|---|
| F0 Kickoff cascade | ~0.3d | ~0.2d(this session) | F0.1 Phase folder + plan/checklist/progress — `(this commit)`;F0.2 `audit/.gitkeep` — `(this commit)`;F0.3 `docs/adr/README.md` 5 reserved slots(0025-0029) + Next NNNN advance 0025→0030 — `(this commit)`;F0.4 `session-start.md` §10 W19 row + W18+→W20+ shift + Last-Updated + Update-history entry — `(this commit)`;F0.5 verified no `architecture.md` amendment at kickoff(F3 ADR drafts propose,per-ADR amendments land in W20+ kickoffs)— `(this commit)` |
| F1 Mockup `.jsx` audit | ~0.8d | ~0.4d(this session) | `audit/W19-mockup-jsx-audit.md` landed:per-route table 14 Tier 1 + 8 Tier 2 + shell + 5 foundation files;deviation summary D1–D11 with F3 ADR feed;Tier 2 leak audit(1 leak Sidebar Workspace switcher + 1 borderline Chat Conversation History);visual identity verify(tokens match,1 NEW `--info` token);mock data schema match(3 NEW schemas needed + RBAC family massive)。5 parallel Read batches over 22 files / 11K lines。**5 H1 ADRs confirmed**(0025–0029)+ **3 NEW ADR candidates surface**(0030 polish bundle / 0031 chat advanced / 0032 topbar additive)— F2/F3/F4 take it forward — `(this commit)` |
| F2 Backend gap map | ~0.8d | ~0.4d(this session)| `audit/W19-backend-gap-map.md` landed:28 endpoints across 13 route files inventoried + 38 schemas across 11 schema files mapped + per-route table 14 Tier 1 × surface × endpoint × status × Wave × Cn × backend file:line evidence + cumulative work list by Wave/Cn with effort estimates per ADR-0026/0027 option set。21 ✅ supported(KB CRUD + Docs + Chunks + Retrieval Test + Eval + Trace + Feedback + Auth + Cost + Query)+ 7 🟡 partial(/health enrich + KbConfig multimodal + Archive KB + crag_* fields verify + auth/me verify + Pipeline viz + embedding preview)+ 13 🔴 missing(Recent queries + Latest eval cache + Conversations + KB Images + Chunking preview + Doc detail enriched + Settings × 3 + /users + RBAC + Audit log + Notifications + /traces list)+ 2 🟣 mock-only(Workspace switcher + Labs sidebar)。Wave A blocker count = 6 small + 2 NEW endpoints;Wave B = 2 NEW;Wave C = MASSIVE option set scope。**Recommend F3+F6 picks**:ADR-0026 Option C hybrid + ADR-0027 Option B minimal 3-role → Wave C ~7 backend days fits single phase。ADR-0030/0032 candidates absorb into Wave A scope without separate ADR;ADR-0031 NEW(Chat advanced + Conversation History) keep as 6th ADR — `(this commit)` |
| F3 ADR drafts × 5 | ~1.2d | — | — |
| F4 Wave breakdown | ~0.4d | — | — |
| F5 Tier 2 catalog | ~0.5d | — | — |
| F6 Closeout | ~0.3d(synthesis;Chris review = own time block)| — | — |

### Next

- F2 — backend gap map per route × endpoint × schema → `audit/W19-backend-gap-map.md`
- F3 — 5 ADR drafts(0025-0029)with option sets for ADR-0026 + ADR-0027 strategic 岔口
- F4 — Wave breakdown(W20-frontend-wave-a / W21-frontend-wave-b / W22-frontend-wave-c with mock+real auth concurrent ship per user 岔口 2 / Wave D Tier 2 hold)
- F5 — Tier 2 disabled-affordance catalog(consume F1 §2.3 leak findings)
- F6 — Chris approval + W20+ kickoff trigger

---

## Day 1 — F1 audit landed(2026-05-16)

### Built — `audit/W19-mockup-jsx-audit.md` NEW — `(this commit)`

Full audit of `references/design-mockups/` 22 files / 11K lines via 5 parallel Read batches:

- **Batch 1 foundation**(`ekp-shell.jsx` + `ekp-data.jsx` + `styles.css` + `tweaks-panel.jsx` + `icons.jsx`) — IA chrome confirms ADR-0024 5-module sidebar + Cmd+K palette + flat URLs;tokens match `frontend/lib/theming/tokens.ts` per ADR-0015 W12 D2(Warm Charcoal + Coral Accent);tweaks panel confirmed design-time only(`__activate_edit_mode` postMessage host protocol)
- **Batch 2 KB cluster**(dashboard + kb + kb-extras + kb-new) — KB Detail confirmed 8 tabs;Dashboard 4-stat strip + 5 cards bigger than spec;Chunking Lab + Images NEW tabs;5-step new-KB wizard with Tier 1/2 Multimodal split
- **Batch 3 Views**(doc-detail + misc + chat + eval) — 3-pane doc detail with embedding vector preview;3-step kb-upload wizard COEXISTS with 5-step new-KB(re-ingest vs new);Chat with 3 citation placement modes + Conversation History sidebar Beta+ + SyntheticScreenshot mockups + FeedbackBar;Eval 4-metric + 5+2-dropped shootout + CRAG insight card
- **Batch 4 Platform**(trace + settings-tabs + users + auth) — Trace 3 viz modes;Settings 6 tabs with 9-provider Connections + Identity & Auth Entra/MSAL + API Keys quotas + RBAC role mapping;Users 4 tabs with 3-role + 1-Tier2 + 5-area × 24-permission matrix + Entra group sync + Audit log;Auth Login + Register with brand panel + ACS verify-email step
- **Batch 5 Labs**(labs-1 + labs-2) — 8 Tier 2 preview pages with consistent LabsHeader pattern(accent gradient banner + "NOT IMPLEMENTED" badge + Cn slot citation)

### Key findings(see audit §2 for full table)

**H1 architectural changes — 5 confirmed ADRs(plan F3.1–F3.5)**:
- D1 ADR-0025 KB Detail 5→8 tabs(Images + Chunking Lab + Access — Access hard dep on ADR-0027)
- D2 ADR-0026 Settings 6-tab + Connections backend(**岔口 2** option set:read-only / fully editable / hybrid)
- D3 ADR-0027 /users Tier 1.5 RBAC(**岔口 1** option set:full RBAC / minimal 3-role / stage)
- D4 ADR-0028 /kb/new 5-step + Multimodal Tier 1/2 split(coexists with 3-step re-ingestion `/kb-upload/[id]`)
- D5 ADR-0029 /doc-detail 3-pane layout(route topology + embedding vector preview)

**3 NEW ADR candidates surface**:
- D6+D9+D11 → ADR-0030 candidate "Dashboard richer overview + Trace 3 viz + /traces list view"(polish bundle)— or absorb as Wave A/B scope without separate ADR(F4 decides)
- D7 → ADR-0031 candidate "Chat advanced surfaces"(Conversation History Beta+ / 3 citation placement modes / FeedbackBar comment)
- D8 → ADR-0032 candidate "Topbar + Sidebar additive"(NotificationsMenu / Workspace switcher disabled affordance / Sidebar Tools + Labs sections)

**Tier 2 boundary audit**:✅ **most disabled affordances correct**(language toggle / Forgot password / Multimodal Vision options / Public KB visibility / Power User role / Custom roles / Anonymous API keys / etc)。🔴 **1 leak**:Sidebar Workspace switcher 未 add disabled state — Tier 2 multi-tenancy 應 disabled。🟡 **1 borderline**:Chat Conversation History 'BETA+' badge — localStorage Tier 1 OK,server-side persistence Tier 2 boundary 需 F5 explicit。

**Backend gap signal**(feeds F2):3 missing schemas(Conversation / DocumentDetail outline / ChunkingComparison)+ 1 massive new schema family(RBAC `users` / `roles` / `role_permissions` / `groups` / `audit_log` + `kb_acl` per-KB ACL)。

**Visual identity**:Tokens match;**1 NEW token** `--info: oklch(0.62 0.13 240)` to add to `frontend/lib/theming/tokens.ts` in Wave A。No Dify color leak per H3。`[oklch(...)]=0` hardcoded milestone:4 occurrences in mockup color-cycle placeholders are mockup-only,real `frontend/` impl uses ImageRef.blob_url so don't ship。

### Deviations from plan(R3)

- **F1 scope adjustment**:plan F1.1–F1.6 5 sub-items + F1.6 grep verification = expected ~0.8d;actual landed in single session ~0.4d。Same real-calendar collapse pattern as W12-W18(per session-start §12)。
- **3 NEW ADR candidates surface during audit**(0030 / 0031 / 0032)— plan F3 5 ADRs(0025–0029)remains spec;the 3 NEW candidates noted in audit §2.2 with decision deferred to F4 Wave breakdown(可 absorb as Wave scope without ADR if smaller, or promote to ADR-0030+ if H1 weight)。**Plan changelog entry will be added at F4 close** documenting the absorb-vs-promote decision per ADR candidate。

### Next

- F3 — 5 ADR drafts(0025-0029)+ ADR-0031(NEW per F2 recommendation)with option sets for ADR-0026 + ADR-0027 strategic 岔口
- F4 — Wave breakdown consume F1+F2+F3
- F5 — Tier 2 disabled-affordance catalog
- F6 — Chris approval

---

## Day 2 — F2 audit landed(2026-05-16)

### Built — `audit/W19-backend-gap-map.md` NEW — `(this commit)`

Backend gap map per Tier 1 route × surface × required endpoint × current status × Wave × Cn,with file:line evidence。28 endpoints across 13 route files inventoried(per `git grep "@router\."`) + 38 schemas across 11 schema files mapped(per `git grep "^class \w+\("`).

### Key findings(audit §2-§3)

**Status distribution**:
- ✅ **21 supported** — KB CRUD + Documents CRUD(per CH-001)+ Chunks CRUD + Retrieval Test(per ADR-0021)+ Eval(per W17 F3 RAGAs)+ Trace detail(per W16 F5.5)+ Feedback + Auth(per ADR-0022)+ Query SSE + Cost Summary + Appearance
- 🟡 **7 partial** — `/health` per-component(currently liveness only)+ KbConfig multimodal fields + Archive KB + QueryResponse `crag_*` field verify + `GET /auth/me` verify + Pipeline visualization + embedding vector preview
- 🔴 **13 missing** — Recent queries(Q6)+ Latest eval cache + Conversations(Beta+)+ KB Images + Chunking preview + Doc detail enriched + Settings Connections × 9 + Settings Identity & Auth + Settings API Keys & Quotas + /users RBAC + Audit log + Notifications + /traces list
- 🟣 **2 mock-only** — Workspace switcher + Labs sidebar(don't ship Tier 1)

**Wave A blockers**(6 small + 2 NEW endpoints):
1. `GET /health` per-component connectivity payload
2. `KbConfig` schema multimodal ACTIVE fields(`extract_embedded_images` + `slide_screenshots` + `dedup_strategy` + `return_images_in_chat`)
3. `QueryResponse.crag_triggered` + `crag_iterations` fields verify
4. `POST /kb/{kb_id}/archive` for KB Settings Danger zone
5. Q6 recent queries decision OR keep empty-state CTA(W18 F4 already accepted CTA approach)
6. Eval cached run decision OR keep empty-state CTA
7. `GET /kb/{kb_id}/images`(ADR-0025 Images tab)
8. `POST /chunking-preview`(ADR-0025 Chunking Lab tab)

**Wave B blockers**:`GET /kb/{kb_id}/docs/{doc_id}` enriched(ADR-0029)+ `GET /traces` list view。

**Wave C MASSIVE**(option-set scope):
- **ADR-0026 Settings Connections**:Option A read-only ~3 endpoints / Option C hybrid ~10 / Option B fully editable ~27
- **ADR-0027 /users RBAC**:Option B minimal 3-role(`users.role` column add only)~5 backend days / Option C stage ~12 / Option A full RBAC ~20
- **Combined**:Option A+B = ~22 backend days(Wave C must split into C1+C2) vs Option B+C = ~7 days(single phase)

**Recommendations to F3 + F6**:
- **ADR-0026 pick Option C hybrid** — Profile + Appearance + Account editable;Connections + Identity + API Keys read-only with「Edit coming Tier 2」 affordance。Trade-off:Beta operators rotate secrets via `.env` + Azure Portal,UI status only。
- **ADR-0027 pick Option B minimal 3-role** — `users.role` column on existing `users` table per ADR-0023 + ACL middleware checks role only。NO new tables(roles/groups/audit_log defer Tier 2)。Members tab read-only listing + invite/suspend;Roles tab read-only matrix;Groups + Audit log = disabled affordance「Tier 2」。
- **ADR-0030 fold into Wave A scope** — `/health` enrich + `/traces` list + Trace 3 viz are polish-grade,no separate ADR
- **ADR-0031 NEW as 6th ADR** — Chat advanced surfaces with Conversation History(Beta+ localStorage Tier 1 scope decision)
- **ADR-0032 fold into Wave A polish** — Workspace switcher disable + Sidebar Labs section + NotificationsMenu(`/notifications` mock acceptable)

**Wave A scope decision**:7-tab KB Detail(`-Access`),Access tab deferred to Wave C alongside `/users` RBAC ship。Wave A 6-tab(`-Access -Chunking Lab`)would defeat ADR-0025 acceptance — not recommended。

### Deviations from plan(R3)

- F2 collapsed ~0.4d actual vs ~0.8d planned(same W12-W18 real-calendar collapse pattern as F1)
- **ADR draft count recommendation:6 instead of 5**(0025/0026/0027/0028/0029 + NEW 0031)— 0030 + 0032 candidates absorbed into Wave A scope per F2 §6 recommendations。Plan F3.1-F3.5 5 ADRs stable + add F3.6 NEW ADR-0031 to checklist at F3 kickoff。**Plan changelog entry will be added at F3 close** documenting the 5→6 promotion。

### Next

- F3 — 5 ADR drafts(0025-0029)+ NEW ADR-0031 Chat advanced surfaces with option set;ADR-0026 + ADR-0027 carry option sets for Chris pick at F6

---

**Lifecycle reminder**:呢個 phase `status=active`(2026-05-16,per user directive)。重大 deviation 入 plan.md §7 changelog(per R3)。W20+ phase folder **唔會** pre-create(per CLAUDE.md §10 R1 rolling-JIT — W20-frontend-wave-a kickoff post-W19-F6 closeout decision per ADR-0025 + Wave A scope authorization)。
