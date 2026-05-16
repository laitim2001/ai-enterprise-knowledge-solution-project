---
phase: W19-frontend-audit-and-adr-draft
plan_ref: ./plan.md
checklist_ref: ./checklist.md
status: closed
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
| F3 ADR drafts × 5 + NEW ADR-0031 | ~1.2d(plan)+ 0.2d(NEW) | ~0.5d(this session)| **6 ADR drafts landed**:0025 KB Detail 8-tab(consensus)+ 0026 Settings 6-tab(option set 岔口 2)+ 0027 /users Tier 1.5 RBAC(option set 岔口 1)+ 0028 /kb/new 5-step(consensus)+ 0029 /doc-detail 3-pane(route name pick)+ **NEW 0031 Chat advanced**(option set Conversation History scope per F2 §6 promotion)。ADR-0030 + ADR-0032 SKIPPED per F2 absorb-vs-promote。`docs/adr/README.md` 6 rows + Next NNNN 0030→0033 with 0030/0032 SKIPPED note — `(this commit)` |
| F4 Wave breakdown | ~0.4d | ~0.3d(this session)| `audit/W19-wave-breakdown.md` landed — 4-Wave structure(W20 / W21 / W22 / Wave D Tier 2 hold)+ dep ordering(A+B parallel,C needs A,D requires Beta launch)+ Wave A 7-tab `-Access` decision + Wave C2 split trigger for Option A picks + per-Wave H4 boundary policing + 岔口 → Wave impact ASCII diagram + mock-auth default through Wave C per user 岔口 2 — `(this commit)` |
| F5 Tier 2 catalog | ~0.5d | ~0.3d(this session)| `audit/W19-tier2-disabled-affordance-catalog.md` landed — 27 Tier 2 affordances enumerated + 4 standardized patterns(P1 native disabled / P2 aria-disabled + toast / P3 coral TIER 2 badge / P4 route hidden)+ `<DisabledAffordance>` shared component spec + coral semantics enforcement + F5.4 `/labs/*` routing decision recommended Option C(prototype-only) — `(this commit)` |
| F6 Closeout | ~0.3d(synthesis;Chris review = own time block)| ~0.3d total(synthesis 0.2d + closeout 0.1d this session)| **DONE** — Chris picked 4 strategic decisions via AskUserQuestion 2026-05-16(Option A + Option B + Option B + Option C)+ 6 ADRs flipped `Proposed` → `Accepted` + frontmatter `active` → `closed` + retro 7 sections + session-start.md hygiene + W20+ kickoff candidate flagged。**Wave C MUST split into C1+C2** per F4 §3.6 trigger;**Wave A backend +3 days** per ADR-0031 Option B Conversation History server-side。**Phase Gate = PASS WITH WAVE-C-SPLIT-TRIGGERED CAVEAT** — `(this commit)` |

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

- F4 — Wave breakdown consume F1+F2+F3 outputs → `audit/W19-wave-breakdown.md`
- F5 — Tier 2 disabled-affordance catalog
- F6 — Chris approval(3 option set picks:ADR-0026 + ADR-0027 + ADR-0031)+ route name pick for ADR-0029 + W20+ kickoff trigger

---

## Day 3 — F3 6 ADR drafts landed(2026-05-16)

### Built — 6 NEW ADR drafts(Status `Proposed`) — `(this commit)`

Per plan F3.1-F3.5(5 ADRs)+ F2 §6 recommendation(promote NEW ADR-0031 as 6th):

| ADR | Title | Type | Recommended pick |
|---|---|---|---|
| 0025 | KB Detail 5→8 tabs expansion | Consensus | Accept as-is |
| 0026 | Settings 6-tab hub + Connections backend | **Option set 岔口 2**(A/B/C) | **Option C hybrid**(per F2 §6 — ~5 backend days,no new dep) |
| 0027 | /users Tier 1.5 RBAC NET NEW | **Option set 岔口 1**(A/B/C) | **Option B minimal 3-role**(per F2 §6 — `users.role` column add only,~5 backend days) |
| 0028 | /kb/new 5-step + Multimodal Tier 1/2 split | Consensus | Accept + clarify `slide_screenshots` Tier 1 promotion |
| 0029 | /doc-detail 3-pane layout | Consensus + **route name pick** | Recommend `/kb/[id]/docs/[docId]` |
| **0031 NEW** | Chat advanced surfaces(Conversation History + 3 citation modes + image cards + FeedbackBar + CRAG strip)| **Option set on Conversation History scope** | **Option A localStorage-only Tier 1**(per F2 §6 + C10 §7 spec — 0 backend days) |

### ADR README updated

- 6 ADR rows added with full context cell summaries(scope + recommendation + Wave dep)
- Status `Reserved (W19 F3)` → `Proposed`(or `Proposed (option set/route name — Chris pick at F6)`)
- "Next NNNN" advances 0030→0033 with **ADR-0030 + ADR-0032 SKIPPED note**(per F2 §6 — Dashboard richer + Trace 3 viz + /traces list + Topbar/Sidebar additive folded into Wave A scope without separate ADR)

### Deviations from plan(R3)

- **F3 ADR draft count 5→6**(ADR-0031 NEW per F2 §6 recommendation)— plan §2 F3.1-F3.5 stable + F3.6 NEW added。Plan changelog entry added at F3 close:「F3 promoted ADR-0031 Chat advanced surfaces from F2 §6 recommendation;ADR-0030 + ADR-0032 SKIPPED per absorb-into-Wave A decision;net effect 5→6 ADRs」
- F3 collapsed ~0.5d actual vs ~1.2d planned(W12-W18 real-calendar collapse pattern continues)
- **3 strategic option-set decisions deferred to F6**(rolling JIT R5)— ADR-0026 + ADR-0027 + ADR-0031 await Chris pick;F4 + F5 + F6 implementable in parallel without blocking on picks

### Next

- F6 — **AWAIT Chris async review** of 4 strategic decisions:岔口 1 (ADR-0027 RBAC) + 岔口 2 (ADR-0026 Settings) + ADR-0031 NEW (Conversation History scope) + ADR-0029 route name pick;then ADR Status flips + W19 phase Gate + frontmatter close + retro + session-start.md hygiene + W20+ kickoff trigger

---

## Day 4 — F4 + F5 landed + F6 ready for Chris review(2026-05-16)

### Built — F4 Wave breakdown + F5 Tier 2 catalog + F6 prep — `(this commit)`

**F4 Wave breakdown**(`audit/W19-wave-breakdown.md`):
- 4-Wave structure:Wave A(W20 / 8 routes / ~5-7 backend days)+ Wave B(W21 / 4 routes / ~2 backend days)+ Wave C(W22 / 5 routes / ~5-10 backend days per option picks)+ Wave D Tier 2 hold(NOT pre-created)
- Dep ordering:Wave A+B parallel,Wave C needs A close(Settings nav + Access tab activation),Wave D requires Beta launch(Q12 governance trigger)
- Wave A ships 7-tab KB Detail(`-Access`),Access tab activates Wave C with ADR-0027 RBAC infra
- Wave C2 split trigger:if Chris picks Option A for ADR-0026 OR ADR-0027 → Wave C scope ~22 days exceeds single phase budget,split into C1+C2 sub-phases per CLAUDE.md §10 rolling JIT
- 岔口 → Wave impact ASCII diagram + per-Wave H4 boundary policing(cross-ref F5 catalog)
- Mock-auth default through Wave C + real-MSAL feature-flagged concurrent ship per user 岔口 2

**F5 Tier 2 disabled-affordance catalog**(`audit/W19-tier2-disabled-affordance-catalog.md`):
- 27 Tier 2 affordances enumerated:Shell S1-S4 + Auth A1 + KB K1-K7 + KB Access KA1-KA2 + Users U1-U5 + Settings ST1-ST10 + Chat C1-C3 + Dashboard D1
- 4 standardized patterns:P1 native disabled + tooltip / P2 aria-disabled + click-toast / P3 coral TIER 2 badge + non-interactive / P4 route hidden
- `<DisabledAffordance>` shared component spec for Wave A implementation(`frontend/components/ui/disabled-affordance.tsx`)
- Coral semantics enforcement(brand emphasis + Tier 2 preview + citation pill — NOT for selected/active / destructive / warning / info)
- F1 audit §2.3 leak fixes called out:Sidebar Workspace switcher MUST disable Wave A + Chat Conversation History server-side persistence boundary explicit
- F5.4 `/labs/*` routing decision — recommended Option C(prototype-only,don't ship `frontend/`)

**F6 Chris review synthesis prepared**:

### 4 strategic decisions awaiting Chris pick

| # | Decision | Options | Recommendation per F2 §6 |
|---|---|---|---|
| 1 | **ADR-0027 /users RBAC scope** | A full RBAC ~20 days + 6 new tables + Entra Graph SDK / **B minimal 3-role ~5 days** / C stage | **Option B minimal 3-role** |
| 2 | **ADR-0026 Settings Connections scope** | A read-only ~3 endpoints / B fully editable ~22 endpoints + Key Vault SDK / **C hybrid ~10 endpoints** | **Option C hybrid** |
| 3 | **ADR-0031 NEW Conversation History scope** | **A localStorage-only Tier 1 0 backend days** / B server-side Tier 1 ~3 days / C Tier 2 defer | **Option A localStorage-only Tier 1** |
| 4 | **ADR-0029 /doc-detail route name** | A `/doc-detail/[kbId]/[docId]` / B `/doc/[kbId]/[docId]` / **C `/kb/[id]/docs/[docId]`** | **Option C `/kb/[id]/docs/[docId]`** for IA consistency with ADR-0024 flat URL |

**Combined recommendation outcomes**:
- Wave A 7-tab KB Detail(`-Access`)+ Multimodal Tier 1 active per ADR-0028 + Chat advanced with localStorage Conversation History
- Wave B 3-pane `/kb/[id]/docs/[docId]` doc detail + Eval Console + Traces 3 viz
- Wave C 6-tab Settings hybrid + `/users` 4-tab minimal RBAC + Access tab activation + real-MSAL concurrent ship
- Wave D NOT pre-created per rolling JIT

**F6 closeout sequence**(awaiting Chris pick):

1. Chris pick 4 decisions(this turn or separate session)
2. ADR Status flips:0025/0028 consensus → `Accepted`;0026/0027/0031 per option pick → `Accepted (Option X)`;0029 per route name pick → `Accepted (Option Y)`
3. W19 phase Gate verdict PASS / PARTIAL / FAIL with rationale
4. W19 frontmatter `active` → `closed` + checklist F6.x ticked
5. W19 retro 7 sections in progress.md
6. `session-start.md` hygiene catch-up:§10 W19 row → closed + W20+ candidates + §11 carry-overs(6 Accepted ADRs)+ §12 milestones row 17→18 + Last-Updated + Update-history
7. W20-frontend-wave-a kickoff candidate flagged(actual W20 phase folder created in separate kickoff cascade per rolling JIT)

### Deviations from plan(R3)

- **F4 collapsed ~0.3d / F5 ~0.3d**(W12-W18 real-calendar collapse pattern continues)
- F6 sequence intentionally bifurcated:F6.1 Chris review + F6.2 ADR flips await user action;F6.3-F6.8 housekeeping = post-approval finalize(separate commit)
- **3 ADR option-set decisions + 1 route name pick = 4 strategic decisions for Chris**(per plan F6.1 4-decision list now explicit in checklist)

### Next

- W20-frontend-wave-a phase folder kickoff(separate cascade per rolling JIT R1)— **needs Wave A scope re-confirm**:per ADR-0027 Option A acceptance,Wave A KB Detail可以 ship 8-tab(包含 Access)如果 backend RBAC infra 同 Wave A 一齊 land;或 ship 7-tab Wave A + Access tab Wave C1。Depends on backend phase split decision at W20 kickoff
- W22+ Wave C must split per F4 §3.6 trigger — W22-frontend-wave-c1(~5-7 backend days subset)+ W22b-frontend-wave-c2(remaining ~30+ days)or different split per kickoff
- Track A IT cred populate event(W16 F1)still parallel track — independent of W20-W22

---

## Day 5 — F6 closeout + W19 phase Gate PASS WITH WAVE-C-SPLIT-TRIGGERED CAVEAT(2026-05-16)

### Phase Gate verdict — **PASS WITH WAVE-C-SPLIT-TRIGGERED CAVEAT** — `(this commit)`

**Verdict rationale**(per the W12-W18 pattern):

- **All 6 F-deliverables landed**(F0 Kickoff + F1 Mockup audit + F2 Backend gap map + F3 6 ADR drafts + F4 Wave breakdown + F5 Tier 2 catalog + F6 Chris approval cascade)
- **Success-criteria checklist**(plan §3) — all 7 met:
  - F0 phase folder + ADR README slots + session-start W19 row ✅
  - F1 22 files / 11K lines audited + D1-D11 deviations + Tier 2 leak ✅
  - F2 14 routes × endpoint × schema + cumulative work list + Wave blockers + grep evidence ✅
  - F3 6 ADR drafts(0025/0026/0027/0028/0029/0031)Proposed → Accepted with option picks ✅
  - F4 4-Wave skeletons + dep ordering + Wave C2 split trigger + 岔口 impact diagram ✅
  - F5 27 affordances + 4 patterns + `<DisabledAffordance>` spec + coral semantics + Labs Option C ✅
  - F6 Chris approves 4 strategic decisions + ADR Status flips + session-start hygiene + W20+ trigger flag ✅
- **The "WAVE-C-SPLIT-TRIGGERED CAVEAT"**(why not a clean PASS — Wave C scope expansion implication):Chris picked Option A(full RBAC ~20 days)+ Option B(fully editable Settings ~22 days)= **~42 combined Wave C backend days exceeds single-phase budget per F4 §3.6 trigger**。Wave C MUST split into C1+C2 sub-phases per CLAUDE.md §10 rolling JIT。This is a **downstream implementation impact, not a F6 deliverable shortfall** — Wave C2 trigger was anticipated + documented in F4 §3.6 + plan §6 Risk row 2(F2 backend gap may be deeper than estimated)before the Chris picks。Per Karpathy §1.4 goal-driven,Wave C split + W22 kickoff scope decision = post-W19 R5 ADR-before-implement discipline applies。

→ **PASS WITH WAVE-C-SPLIT-TRIGGERED CAVEAT**。The 4 strategic decisions are Chris's authority + per the rolling JIT discipline,W22 kickoff(post-Wave A close)will make the C1/C2 split decision concrete based on actual backend implementation pace through Wave A。

### Retrospective(7 sections per PROCESS.md / session-start §13)

**1. What worked**

- **F1+F2 parallel-Read batching pattern**(5 batches over 22 files in F1 + grep + schema inventory in F2)reused the W18 F3 atomic re-parent + re-route precedent — single-session collapse from ~1.6 plan-days to ~0.8 actual days(per W12-W18 real-calendar collapse pattern)。
- **F2 §6 recommendations + F3 NEW ADR-0031 promotion** —  surfacing the absorb-vs-promote decision in F2 audit + F3 incorporating that as 6th ADR(0031)— eliminated the ambiguity that would have plagued F4 if 0030/0032 were left as TBD ADRs;Wave A polish scope clear from F3 onwards。
- **Option-set ADR draft pattern**(0026 / 0027 / 0031)— explicit option sets with cost-benefit + recommendation in each ADR draft made Chris's F6 pick session efficient(AskUserQuestion 4 questions × 3 options each = 1 turn)。
- **Wave C2 split trigger documented in F4 §3.6 _before_ Chris pick** — preemptive risk mitigation per plan §6 Risk row 2(F2 gap deeper than estimated);Chris's actual picks(Option A + B)triggered the split as anticipated — graceful handling rather than mid-Wave-C scramble。
- **27-affordance catalog + 4 standardized patterns + `<DisabledAffordance>` component spec** — F5 reusable across Wave A/B/C implementations,eliminates per-Wave Tier 2 boundary policing inconsistency。

**2. What didn't work / friction**

- **F3 ADR drafting context drain** — 6 ADRs × ~150-300 lines each = ~1500 lines single-session NEW md;option-set ADRs(0026/0027/0031)需 careful nuanced option presentation,context pressure noticeable mid-F3。Wave A实现 phase 唔可能similar single-session collapse — 实际 implementation 6+ files × test + lint cycles = substantial context budget per file。
- **Chris picks 3-of-4 against recommendation** — Chris explicitly chose maximum scope(Option A + B + B)over F2 §6 minimum-recommend(Option B + C + A)— substantial Wave C scope expansion;documented in plan §7 changelog as a deviation acknowledgment但 fully respected per stakeholder authority。
- **`docs/12-ai-assistant/01-prompts/01-session-start.md` `.gitignore` directory-pattern ignored warning** — recurring warning across F0/F1/F2/F3/F4/F5/F6 commits;`git add` succeeds for already-tracked file modification but pollutes stage output。Mitigation: stays per-file modification(not directory)— same as W17/W18 pattern。

**3. Surprises**

- **F1 audit surfaced 3 NEW ADR candidates beyond plan F3 5 ADRs**(0030/0031/0032)— plan §6 Risk row 1 anticipated"audit may surface more deviations than 5"with medium likelihood/impact;actual: 3 surfaced + 1 promoted(0031) + 2 absorbed into Wave A scope(0030/0032)— graceful handling matched the mitigation。
- **Chris picks 3-of-4 against W19 F2 §6 minimum-recommend** — anticipated as plan §6 Risk row 3("岔口 stay un-resolved at F6")but actually opposite — Chris resolved with **maximum** scope。Risk row 2(F2 gap deeper than estimated)更适合 — actual outcome = Wave C scope expansion forces split per F4 §3.6 anticipated trigger。
- **Per F1 audit + F2 grep, mostly schemas match backend Pydantic shapes very precisely** — KB / Document / Chunk / Image / Trace / Eval / Shootout / Cost 全部 shape match;只有 Conversation + DocumentDetail + ChunkingComparison + RBAC missing(per F2 §3 cumulative gap list)— prototype design demonstrates high backend Pydantic awareness。

**4. Decisions**(the ones that'll matter later — see plan §7 changelog for the full Chris pick context)

- **Wave C MUST split C1+C2** per F4 §3.6 trigger due to Option A+B combined ~42 backend days exceeds single-phase budget per CLAUDE.md §10 rolling JIT。W22 kickoff(post-Wave A close)will decide concrete C1/C2 scope split based on actual Wave A backend pace。
- **Wave A scope re-confirm at W20 kickoff** — per ADR-0027 Option A acceptance,Wave A KB Detail可以 ship 8-tab(包含 Access)如果 backend RBAC infra 同 Wave A 一齊 land(but Option A RBAC ~20 days,Wave A budget ~5-7 days backend — likely NOT achievable),或 ship 7-tab Wave A + Access tab Wave C1(more realistic);decision at W20 kickoff per F2 + Wave A backend phase split。
- **Wave A backend +3 days** per ADR-0031 Option B Conversation History server-side(~5-7 → ~8-10 days)— substantial but within Wave A phase budget。
- **Key Vault SDK + Entra Graph SDK NEW dependencies** per ADR-0026 Option B + ADR-0027 Option A — H2 stop-and-ask implicit acceptance via Chris pick;R8 corp-proxy risk per ADR-0017 mitigation pattern(Plan B (a) system binary / (b) native package manager / (c) defer to non-proxy env)applies to both new deps installation。
- **ADR-0030 + ADR-0032 SKIPPED preserved** — F2 §6 absorb-vs-promote decision unchanged by Chris picks;Wave A polish covers these without separate ADR。

**5. Carry-overs to W20+**(the 6 Accepted ADRs become W20+ tracking items)

- **ADR-0025 KB Detail 8-tab** — Wave A `+` Wave C1(Access tab needs ADR-0027 RBAC infra activation)
- **ADR-0026 Settings 6-tab fully editable Option B** — Wave C1 + C2(per scope split decision)+ Key Vault SDK new dep + ~22 backend endpoints + provider CRUD + Test connection + secret rotation
- **ADR-0027 /users Tier 1.5 full RBAC Option A** — Wave C1 + C2 + 6 NEW Postgres tables + Entra Graph SDK new dep + ACL middleware + audit log writes + new C16 Users Service
- **ADR-0028 /kb/new 5-step + Multimodal** — Wave A backend KbConfig +4 multimodal fields + Multimodal Tier 2 disabled affordance(captioning + render PDF + perceptual dedup + low_value vision filter)
- **ADR-0029 /doc-detail 3-pane `/kb/[id]/docs/[docId]`** — Wave B + GET enriched endpoint
- **ADR-0031 Chat advanced surfaces + Conversation History server-side Tier 1 Option B** — Wave A frontend + 6 `/conversations` CRUD endpoints + Postgres conversations + messages tables + ~3 backend days extends Wave A
- **Wave A scope re-confirm at W20 kickoff** — Access tab Wave A vs Wave C1 decision
- **Wave C C1/C2 scope split decision at W22 kickoff** — per F4 §3.6 trigger activation
- **27-affordance Tier 2 catalog enforcement** — Wave A/B/C implementations consume `<DisabledAffordance>` component per F5 §4 spec
- **F5.4 `/labs/*` routing Option C** — `<AppShell>` sidebar nav NOT include Labs section in Wave A

**6. Time tracking**

- Plan-day budget(per plan §5):F0 0.3d + F1 0.8d + F2 0.8d + F3 1.2d + F4 0.4d + F5 0.5d + F6 0.3d = **~4.3 plan-days budget**(window 2026-05-16 → 2026-05-23 per frontmatter)
- Actual:F0 0.2d + F1 0.4d + F2 0.4d + F3 0.5d + F4 0.3d + F5 0.3d + F6 0.3d = **~2.4 actual days** condensed in **single calendar day 2026-05-16**。Real-calendar collapse ≈ 2× under plan-day budget — consistent with W12-W18 pattern(W18 was 4× collapse)。 Frontmatter end_date 2026-05-23 was a window not a commitment(per W18 precedent)。

**7. Spec-ref alignment**

- **`architecture.md v6 §5` amendments NOT done in W19**(F0.5 verify-no-op pattern)— per CLAUDE.md §6 ADR-before-implement,the 6 Accepted ADRs propose amendments;actual inline-tag edits land per-ADR at respective W20+ kickoffs(W20 for ADR-0025/0028/0031 / W21 for ADR-0029 / W22-C1 + W22-C2 for ADR-0026/0027)— same convention as ADR-0024 W18 kickoff inline-tag pattern + §3.4/§3.7 W17 precedent。
- **`COMPONENT_CATALOG.md` C09/C10/C11 + new C16 Users Service rows** to land at W20+ phase implementations(W19 audit-only,no Cn design-note edit)
- **`decision-form.md` untouched**(F6.8 R4 no-op confirmed)— 4 strategic decisions resolved via Accepted ADR options + Wave C scope decision per F4 §3.6 + Wave A scope re-confirm at W20 kickoff,not new OQs。
- **CLAUDE.md §5.1 H1 check**:6 ADRs Accepted with Chris approval before any W20+ implementation = R5 ADR-before-implement discipline satisfied。Option A + B picks trigger H2 new dependency note(Key Vault SDK + Entra Graph SDK);R8 corp-proxy mitigation per ADR-0017 applies to both new deps + W20+ phase plans should explicit Plan B sequencing per ADR-0017 Decision-rule #5。
- **CLAUDE.md §10 R5 trigger**:Wave C2 split per F4 §3.6 anticipates the split per rolling JIT — W22 kickoff cascade(post-Wave A close)will make concrete decision per W22 phase plan。

### W19 phase Gate verdict = **PASS WITH WAVE-C-SPLIT-TRIGGERED CAVEAT**

All F0-F6 deliverables landed + Chris approves 4 strategic decisions + 6 ADRs Accepted。Wave C2 split is a downstream implementation impact requiring W22 kickoff scope decision,not a F6 deliverable shortfall。Same shape as W18 "PASS WITH SMOKE-USER-DEFERRED CAVEAT" — phase Gate PASS,but with an explicit caveat that future-phase work is impacted。

### Closeout housekeeping landed(`(this commit)`)

- 6 ADRs(0025/0026/0027/0028/0029/0031)Status `Proposed` → `Accepted` per Chris pick + header note documenting decisions + implications
- `docs/adr/README.md` 6 rows + footnote updated to Accepted state + Next NNNN unchanged at `0033`(0030/0032 still SKIPPED)
- W19 `plan.md` + `checklist.md` + `progress.md` frontmatter `status: active` → `closed`
- W19 `plan.md` §7 changelog 3 entries(initial draft + F3 5→6 promotion + F6 Chris approval cascade)
- W19 `checklist.md` F6.1-F6.8 all ticked
- W19 `progress.md` Day 5 entry + retro 7 sections + lifecycle reminder unchanged
- `session-start.md` hygiene catch-up — §10 W19 row → closed + Wave C C1+C2 split note + W20+ candidates + §11 carry-overs + §12 milestones 17→18 + Last-Updated + Update-history
- W20-frontend-wave-a phase folder **NOT pre-created**(rolling JIT — kickoff post-W19 closeout decision per ADR-0025/0028/0031 + Wave A scope re-confirm)

### Next phase kickoff candidates(post-W19)

1. **W20-frontend-wave-a**(primary candidate per F4 §1) — `/dashboard` + `/chat` advanced + `/kb` cluster + `/kb/[id]` 7-tab OR 8-tab + `/kb-upload` + `/login` + `/register` polish + topbar polish。Backend additions ~8-10 days + frontend ~10-13 days。Window ~1.5-2 weeks。
2. **W21-frontend-wave-b**(parallel candidate per F4 §2) — can start concurrent with W20 if backend capacity supports;`/doc-detail` 3-pane + `/eval` + `/traces` list + `/traces/[traceId]` 3 viz modes。 ~2 backend days + ~6.5-7.5 frontend days。 Window ~1 week。
3. **W22-frontend-wave-c1**(sequential post-Wave-A per F4 §3) — Wave C scope split decision at W22 kickoff per F4 §3.6 trigger activated by Chris Option A+B picks。
4. **W22b-frontend-wave-c2**(after W22-c1 close per rolling JIT) — remainder of Wave C scope。
5. **W23+ Tier 2** — Q12 post-Beta governance trigger,not pre-created。

---

**Lifecycle reminder**:呢個 phase `status=closed`(2026-05-16,per F6 Chris approval cascade)。重大 deviation 入 plan.md §7 changelog(per R3 — F6 decisions logged)。W20+ phase folder **唔會** pre-create(per CLAUDE.md §10 R1 rolling-JIT — W20-frontend-wave-a kickoff is a separate cascade)。
