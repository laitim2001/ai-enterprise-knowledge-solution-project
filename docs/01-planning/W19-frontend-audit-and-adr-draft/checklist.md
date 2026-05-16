---
phase: W19-frontend-audit-and-adr-draft
plan_ref: ./plan.md
status: closed
last_updated: 2026-05-16
---

# Phase W19 — Checklist

> Atomic checkbox(每 item ≤ 0.5–2 hour effort)。Status:`active` from kickoff 2026-05-16(user directive + AskUserQuestion answer = the authorization)。
> 每 item done 後 `[ ]→[x]` + commit ref;延後項標 🚧 + reason(per CLAUDE.md §10 sacred rule — 唔可以刪未勾選 item)。
> **W19 is audit + ADR drafts + planning only — NO `frontend/` code change in this phase**。

## F0 — Kickoff cascade

- [x] F0.1 NEW `docs/01-planning/W19-frontend-audit-and-adr-draft/{plan,checklist,progress}.md` created with `status: active` — `(this commit)`
- [x] F0.2 NEW `docs/01-planning/W19-frontend-audit-and-adr-draft/audit/` subfolder created with `.gitkeep` — `(this commit)`
- [x] F0.3 `docs/adr/README.md` — reserved ADR-0025 / 0026 / 0027 / 0028 / 0029 slots with `Status: Reserved (W19 F3)`(5 rows added after ADR-0024 + footnote「next available 0025」→「0025–0029 Reserved 2026-05-16, next 0030」)— `(this commit)`
- [x] F0.4 `docs/12-ai-assistant/01-prompts/01-session-start.md` — NEW W19 row in §10(`active 2026-05-16`,Default focus = "audit + ADR drafts,NO `frontend/` code change")+ W18+ → W20+ shift with Wave A/B/C/D candidates;Last-Updated + Prior moved + Update-history entry added — `(this commit)`
- [x] F0.5 Confirmed NO `architecture.md` amendment at W19 kickoff(per F0.5 verify-no-op pattern same as W18 F2.4)— `architecture.md v6 §5` still reflects W18 ADR-0024 amendment state unchanged;F3 ADR drafts will *propose* amendments,actual `architecture.md` inline-tag edits land per-ADR in W20+ kickoffs per the §3.4/§3.7/ADR-0024 precedent — `(this commit)`(verified, no edit)

## F1 — Full mockup audit per `.jsx`(17 files + shell + data + styles + tweaks)

> **F1 verdict = PASS**(2026-05-16)— landed `(this commit)`。`audit/W19-mockup-jsx-audit.md` covers all 14 Tier 1 routes + 8 Tier 2 Labs + shell + 5 foundation files。5 parallel Read batches over 22 files / 11K lines。**5 H1 ADRs confirmed**(0025–0029 per plan F3)+ **3 NEW ADR candidates**(0030 dashboard/visualization polish bundle + 0031 chat advanced surfaces + 0032 topbar/sidebar additive)。**1 Tier 2 leak**(Sidebar Workspace switcher needs disabled state)+ **1 borderline**(Chat Conversation History Beta+ localStorage OK + server-side persistence Tier 2 boundary)。**Backend gap signal**:3 missing schemas(Conversation / DocumentDetail outline / ChunkingComparison)+ 1 massive new schema family(RBAC tables) — feed F2。**Visual identity match**:tokens align with `frontend/lib/theming/tokens.ts` per ADR-0015 W12 D2;**1 NEW token**(`--info: oklch(0.62 0.13 240)`)to add to `tokens.ts` in Wave A。

- [x] F1.1 NEW `audit/W19-mockup-jsx-audit.md` §1 — per-route table covering all 14 Tier 1 routes + 8 Tier 2 Labs routes + the shell;columns:Route / File / Top-level component / Mock data deps / Tier / IA compliance / Visual identity / Deviation feed — `(this commit)`
- [x] F1.2 `audit/W19-mockup-jsx-audit.md` §2 — Deviation summary D1–D11 each tagged with F3 ADR feed(D1=0025 / D2=0026 岔口 2 / D3=0027 岔口 1 / D4=0028 / D5=0029)+ 3 NEW ADR candidates(D6+D9+D11→0030 / D7→0031 / D8→0032)+ Tier 2 leak audit table(1 leak found:Sidebar Workspace switcher) — `(this commit)`
- [x] F1.3 `tweaks-panel.jsx` audit — confirmed **design-time only** via `__activate_edit_mode` / `__edit_mode_available` host postMessage protocol。**NOT shipping** to `frontend/`。Wave A note:density toggle don't ship as user-facing — covered in audit §5 — `(this commit)`
- [x] F1.4 `styles.css` audit — Warm Charcoal `oklch(0.20 0.01 285)` primary + Coral `oklch(0.65 0.18 25)` accent + radius 0.25/0.5/0.75rem + Inter + JetBrains Mono all match `frontend/lib/theming/tokens.ts` per ADR-0015 W12 D2。**1 NEW token** `--info: oklch(0.62 0.13 240)` to add — covered in audit §3。Hardcoded `[oklch(`-prefix:4 occurrences in `ekp-page-kb-extras.jsx` + `ekp-page-doc-detail.jsx` ImageThumb color cycles(placeholder thumbnails),mockup-only — real `frontend/` impl uses ImageRef.blob_url so 不會 ship hardcoded values — `(this commit)`
- [x] F1.5 `ekp-data.jsx` audit — 10 sampled shapes vs `backend/api/schemas/*.py`:KbStatus / Document / ChunkRecord / ImageRef / TraceDetail 9-stage / EvalReport / ShootoutReport / FailedQuery / CostSummary 全部 match;**3 NEW schemas needed**(Conversation / DocumentDetail outline / ChunkingComparison)+ **1 massive new schema family**(RBAC `users` / `roles` / `role_permissions` / `groups` / `audit_log`)— covered in audit §4 — `(this commit)`
- [x] F1.6 Spec-ref grep verification per CO_W14_process_grep_verify — cross-ref ADR-0024 §5.0 / §5.5 / §5.5.2 / §5.5.3 / §5.5.4 / §5.6 / §5.7 / §5.10 / §5.11 + `frontend/lib/theming/tokens.ts`(`--info` confirmed absent via grep)+ `backend/api/schemas/*.py`(Conversation / DocumentDetail / ChunkingComparison / RBAC全 confirmed absent via grep)— covered in audit Appendix A — `(this commit)`

## F2 — Backend gap map(14 Tier 1 routes × endpoint × schema)

> **F2 verdict = PASS**(2026-05-16)— landed `(this commit)`。`audit/W19-backend-gap-map.md` covers 14 Tier 1 routes + topbar/sidebar surfaces × backend endpoint × schema check vs 13 route files + 11 schema files in `backend/api/{routes,schemas}/`。**21 ✅ supported / 7 🟡 partial / 13 🔴 missing / 2 🟣 mock-only**。Wave A blockers identified(6 small backend additions + 2 NEW endpoints for ADR-0025 NEW tabs)+ Wave B(2 NEW endpoints)+ Wave C MASSIVE(5-22 backend days depending on ADR-0026 + ADR-0027 option picks)。**Recommendation surface to F3 + F6**:ADR-0026 Option C hybrid + ADR-0027 Option B minimal 3-role → Wave C ~7 backend days,fits single phase;ADR-0030 + ADR-0032 candidates absorb into Wave A scope without separate ADR;ADR-0031 NEW(Chat advanced surfaces with Conversation History) keep as 6th ADR alongside 0025-0029。

- [x] F2.1 NEW `audit/W19-backend-gap-map.md` §2 — per-route table covering all 14 Tier 1 routes + topbar/sidebar surfaces;columns:Route / Surface / Required endpoint / Status / Wave / Owner Cn / Evidence(backend file:line)。Summary by status:21 ✅ / 7 🟡 / 13 🔴 / 2 🟣 — `(this commit)`
- [x] F2.2 `audit/W19-backend-gap-map.md` §3 cumulative backend-work list — grouped by Wave(Wave A blockers 6 items + Wave A ADR-0025 NEW tabs 2 items + Wave B 2 items + Wave C option-set bundled items 11-20 with effort estimates per Option A/B/C)+ Wave A polish 4 items — `(this commit)`
- [x] F2.3 `audit/W19-backend-gap-map.md` §4 "Blocks Wave A/B/C" classification — Wave A 7-tab(`-Access`)recommended,Access tab deferred Wave C;Wave B independent of Wave C 岔口;Wave C strongly recommend Option B+C combo for ~7 backend days vs full Option A+B for ~22 backend days — `(this commit)`
- [x] F2.4 Real backend code grep — every F2.1 row cites `backend/api/routes/<file>.py:<line>` + `backend/api/schemas/<file>.py:<line>` for actual route + schema definition(or absence per `grep ^class \w+\(` returning none)— `(this commit)`

## F3 — ADR drafts × 5(Status = Proposed,await F6 approval)+ NEW ADR-0031 per F2 §6

> **F3 verdict = PASS**(2026-05-16)— landed `(this commit)`。**6 ADR drafts** Status `Proposed`:0025/0026/0027/0028/0029 per plan + **NEW 0031** Chat advanced surfaces per W19 F2 §6 recommendation。**3 strategic option sets** for Chris pick at W19 F6:ADR-0026 岔口 2(read-only/editable/hybrid)+ ADR-0027 岔口 1(full RBAC/minimal/stage)+ ADR-0031 Conversation History scope(localStorage/server-side/Tier 2 defer)。**ADR-0030 + ADR-0032 SKIPPED** per F2 absorb-vs-promote — Dashboard polish + Topbar/Sidebar additive fold into Wave A scope without separate ADR。`docs/adr/README.md` updated:6 rows added + Next NNNN advance 0030→0033(skip 0030 + 0032)。

- [x] F3.1 NEW `docs/adr/0025-kb-detail-8-tabs-expansion.md` — KB Detail 5→8 tabs(Images + Chunking Lab + Access);consensus decision(no option set);Access tab hard dep on ADR-0027 acceptance documented;Wave A 7-tab `-Access` scope decision per F2 §4;~2.5d backend additions(`GET /kb/{kb_id}/images` + `POST /chunking-preview`)— `(this commit)`
- [x] F3.2 NEW `docs/adr/0026-settings-6-tab-hub-and-connections-backend.md` — Settings 6-tab hub;**option set 岔口 2**(A read-only ~3 endpoints / B fully editable ~22 endpoints + Key Vault SDK new dep / **C hybrid ~10 endpoints RECOMMENDED per F2 §6**)— each option's backend scope + Wave C impact spelled out;`Status: Proposed (option set — Chris pick at F6)` — `(this commit)`
- [x] F3.3 NEW `docs/adr/0027-users-tier-1-5-rbac.md` — /users Tier 1.5 NET NEW;**option set 岔口 1**(A full RBAC ~20 days + 6 new tables + Entra Graph SDK / **B minimal 3-role hard-coded ~5 days RECOMMENDED per F2 §6** / C stage)— each option's table additions + Cn scope + Wave C impact;ADR-0023 users table extension(`users.role` column add)basis;`Status: Proposed (option set — Chris pick at F6)` — `(this commit)`
- [x] F3.4 NEW `docs/adr/0028-kb-new-5-step-wizard.md` — /kb/new 5-step + Multimodal Tier 1/2 split + clarify §5.5.3a new-KB vs §5.5.3b re-ingestion coexistence;Multimodal Tier 1 = extract + slide_screenshots + sha256 + return_images_in_chat;Tier 2 = vision captioning + render PDF pages + perceptual + low_value vision filter;`Status: Proposed`;prototype Step 1 of 4→5 inconsistency fix flagged — `(this commit)`
- [x] F3.5 NEW `docs/adr/0029-doc-detail-3-pane-layout.md` — /doc-detail 3-pane(outline + chunks + inspector with embedding viz);route name 3-option(deferred F6 — recommend `/kb/[id]/docs/[docId]` for IA consistency with ADR-0024 flat URL convention);Wave B backend `GET /kb/{kb_id}/docs/{doc_id}` enriched ~1d;`Status: Proposed (route name pick at F6)` — `(this commit)`
- [x] F3.6 **NEW ADR-0031** `docs/adr/0031-chat-advanced-surfaces.md` — Chat advanced surfaces bundle(Conversation History + 3 citation placement + inline image cards + gallery + citation pill hover + FeedbackBar comment + CRAG strip);**option set on Conversation History scope**(**A localStorage-only Tier 1 RECOMMENDED per F2 §6 + C10 §7 spec** / B server-side Tier 1 ~3 days backend / C Tier 2 defer);per F2 §6 promotion to 6th ADR — `(this commit)`
- [x] F3.7 `docs/adr/README.md` updated — 6 ADR rows replace 5 reserved slots(Status `Reserved` → `Proposed`),context cells summarize each ADR scope + recommendation,"Next NNNN" advances 0030→0033 with `0030`+`0032` SKIPPED note(per F2 absorb-vs-promote decision — Dashboard polish + Topbar/Sidebar additive fold into Wave A scope) — `(this commit)`

## F4 — Wave breakdown(W20–W23+ phase skeletons)

> **F4 verdict = PASS**(2026-05-16)— landed `(this commit)`。`audit/W19-wave-breakdown.md` covers 4-Wave structure:Wave A(W20 ~1.5-2w / 8 routes / ~5-7 backend days)+ Wave B(W21 ~1w / 4 routes / ~2 backend days)+ Wave C(W22 ~1.5-2w / 5 routes / ~5-10 backend days per option-set picks)+ Wave D(Tier 2 hold,not pre-created)。**Dep ordering**:A+B parallel,C needs A,D requires Beta launch。**Wave A 7-tab KB Detail**(`-Access`)/ Wave C activates Access tab。**Mock-auth default through Wave C** + real-MSAL concurrent ship per user 岔口 2。**岔口 → Wave impact diagram**:Option A+A combination triggers Wave C split into C1+C2 sub-phases(rolling JIT per CLAUDE.md §10);Option B+C recommended = single phase。

- [x] F4.1 NEW `audit/W19-wave-breakdown.md` — 4 Wave skeletons with scope + backend deps + frontend effort + acceptance criteria + ADR deps per Wave。Wave A includes ADR-0030/0032 absorbed scope(Dashboard polish + Trace 3 viz + /traces list + Topbar/Sidebar additive)— `(this commit)`
- [x] F4.2 Dep ordering — Wave A+B parallel,Wave C needs A close(Settings UserMenu nav + Access tab RBAC infra),Wave D requires Beta launch(Q12 governance trigger)— diagrammed in §5 — `(this commit)`
- [x] F4.3 Per-Wave H4 boundary policing list — Wave A: Shell + Auth + KB cluster disabled affordances(10 items);Wave B: embedding viz conditional;Wave C: Users RBAC + Settings Tier 2 affordances(13 items);Wave D: all `/labs/*` 8 pages — §6 cross-ref F5 catalog — `(this commit)`
- [x] F4.4 岔口 → Wave impact diagram — Option B+C(recommended)~10 backend days single Wave C phase / Option A+A ~42 days must split C1+C2+C3 per rolling JIT — §3.5 with ASCII diagram + Wave C2 trigger conditions documented in §3.6 — `(this commit)`

## F5 — Tier 2 disabled-affordance catalog

> **F5 verdict = PASS**(2026-05-16)— landed `(this commit)`。`audit/W19-tier2-disabled-affordance-catalog.md` enumerates **27 Tier 2 disabled affordances**(4 Shell + 1 Auth + 7 KB cluster + 2 KB Access + 5 /users + 10 /settings + 3 Chat + 1 Dashboard = 27 surface);4 standardized patterns(**P1 native disabled + tooltip / P2 aria-disabled + click-toast / P3 coral TIER 2 badge + non-interactive / P4 route hidden**)+ NEW `<DisabledAffordance>` shared component spec for Wave A implementation。Coral semantics enforcement(coral reserved for brand emphasis + Tier 2 preview + citation pill — NOT for selected/active states / destructive / warning / info)。**F5.4 `/labs/*` routing decision — recommended Option C(prototype-only,don't ship `frontend/`)**。

- [x] F5.1 NEW `audit/W19-tier2-disabled-affordance-catalog.md` §1 — 27 affordances enumerated(Shell S1-S4 + Auth A1 + KB K1-K7 + KB Access KA1-KA2 + Users U1-U5 + Settings ST1-ST10 + Chat C1-C3 + Dashboard D1)cross-ref F1 audit §2.3 leak findings(Sidebar Workspace switcher must fix Wave A polish + Chat Conversation History server-side persistence boundary explicit) — `(this commit)`
- [x] F5.2 §2 4 standardized patterns + per-affordance handling spec — P1 native disabled / P2 aria-disabled + toast / P3 coral TIER 2 badge / P4 route hidden;each pattern's implementation code + when-to-use + a11y notes — `(this commit)`
- [x] F5.3 §4 `<DisabledAffordance>` shared component design sketch — NEW `frontend/components/ui/disabled-affordance.tsx` spec with `variant` prop(p1-strict / p3-preview) + `reason` + `tier2Trigger` + `showBadge` + usage examples for S1 (P1) + U1 (P3);Wave A acceptance criterion = grep `<DisabledAffordance` count matches catalog count(~10 Wave A scope) — `(this commit)`
- [x] F5.4 §5 `/labs/*` routing decision option set — A visible in sidebar / B feature-flag-gated / **C prototype-only RECOMMENDED**;Wave A action = `<AppShell>` sidebar nav NOT include Labs section + documented rationale comment in `frontend/components/nav/app-shell.tsx` — `(this commit)`

## F6 — Phase closeout + Chris approve + W20+ kickoff trigger

> **F6 status = AWAITING CHRIS REVIEW**(2026-05-16)— F1+F2+F3+F4+F5 deliverables landed;F6 = Chris review of 4 strategic decisions + ADR Status flips + frontmatter close + retro + session-start.md hygiene。**Synthesis for Chris async review** prepared `(this commit)` in this checklist + summarized in `progress.md` Day 4 entry。

- [x] F6.1 Chris review session **DONE** — 4 strategic decisions picked via AskUserQuestion 2026-05-16:
  - **岔口 1**(ADR-0027 /users RBAC scope):**Option A full RBAC** picked(over recommended Option B minimal 3-role)— ~20 backend days + 6 NEW Postgres tables + Entra Graph SDK new dep + audit_log + new C16 Users Service
  - **岔口 2**(ADR-0026 Settings Connections scope):**Option B fully editable** picked(over recommended Option C hybrid)— ~22 NEW backend endpoints + Key Vault SDK new dep
  - **ADR-0031 NEW Conversation History scope**:**Option B server-side Tier 1** picked(over recommended Option A localStorage)— promotes C10 §7 Tier 2 to Tier 1;+3 backend days extends Wave A
  - **ADR-0029 /doc-detail route name**:**Option C `/kb/[id]/docs/[docId]`** picked(matches recommendation)— IA consistency with ADR-0024 — `(this commit)`
- [x] F6.2 ADR Status flips per Chris pick **DONE** — 6 ADRs `Proposed` → `Accepted`:0025 consensus / 0026 Accepted (Option B fully editable) / 0027 Accepted (Option A full RBAC) / 0028 consensus / 0029 Accepted (Option C) / 0031 Accepted (Option B server-side Tier 1);each ADR header note documenting Chris pick + implications — `(this commit)`
- [x] F6.3 W19 phase Gate verdict = **PASS WITH WAVE-C-SPLIT-TRIGGERED CAVEAT**(all F0-F6 deliverables landed + Chris signs off 4 strategic decisions;Wave C2 split is a downstream implementation impact per F4 §3.6 trigger,not a F6 deliverable shortfall) — `(this commit)`
- [x] F6.4 W19 `plan.md` + `checklist.md` + `progress.md` frontmatter `status: active` → `closed` — `(this commit)`
- [x] F6.5 W19 `progress.md` Day 5 entry + retro 7 sections written(What worked / What didn't & friction / Surprises / Decisions / Carry-overs to W20+ / Time tracking / Spec-ref alignment)— `(this commit)`
- [x] F6.6 `session-start.md` hygiene catch-up — §10 W19 row → closed with Gate verdict + Wave C C1+C2 split note + W20+ candidates noted + §11 carry-overs(6 Accepted ADRs + Wave A scope re-confirm decision at W20 kickoff)+ §12 milestones row(累計 17→18)+ Last-Updated + Update-history — `(this commit)`
- [x] F6.7 W20-frontend-wave-a kickoff candidate flagged in session-start §10 W19 row(actual W20 phase folder created in **separate kickoff cascade** per rolling JIT — NOT in this commit per R1 discipline)— `(this commit)` flag
- [x] F6.8 Confirm no new W19 OQ — option-set picks resolved via Accepted ADR options,not new OQs;`decision-form.md` untouched(R4 no-op)— `(this commit)`

## F5 — Tier 2 disabled-affordance catalog

- [ ] F5.1 NEW `audit/W19-tier2-disabled-affordance-catalog.md` — enumerate every disabled-affordance instance(topbar language / Forgot password / Multimodal Vision / Slide screenshots / Perceptual hash / Public KB / Anonymous API key / Power User role / Custom role / Power User mapping / Distributed token cache / Anonymous API keys / Add provider / `/labs/*` 8 pages)
- [ ] F5.2 Per-affordance handling spec — for each item:affordance pattern(native disabled / aria-disabled+toast / coral badge / route hidden);tooltip text(consistent voice);coral accent usage guard;H4 rationale;Tier 2 trigger condition
- [ ] F5.3 `<DisabledAffordance>` or `<Tier2Affordance>` component design sketch — single shared component for consistent wiring across Waves;design pattern only,not built in W19
- [ ] F5.4 `/labs/*` routing decision option set — A:Labs in `<AppShell>` sidebar section;B:flag-gated;C:prototype only;recommend C for Wave A-C ship,A for post-Beta governance

## F6 — Phase closeout + Chris approve + W20+ kickoff trigger

- [ ] F6.1 Chris review session — go through 4 audit files + 5 ADR drafts;answer:岔口 1(ADR-0027 Option A/B/C)+ 岔口 2(ADR-0026 Option A/B/C)+ F5.4(/labs/* routing A/B/C)+ F3.5(/doc-detail route name)
- [ ] F6.2 Each ADR(0025–0029) Status `Proposed` → `Accepted` per Chris approval(iterate if needed);ADR README slot status updates
- [ ] F6.3 W19 phase Gate verdict landed in progress.md(PASS / PARTIAL / FAIL with explicit rationale per the W12-W18 pattern)
- [ ] F6.4 W19 `plan.md` + `checklist.md` + `progress.md` frontmatter `status: active` → `closed`
- [ ] F6.5 W19 `progress.md` retro — 7 sections(What worked / What didn't & friction / Surprises / Decisions / Carry-overs to W20+ / Time tracking / Spec-ref alignment)
- [ ] F6.6 `session-start.md` hygiene catch-up — §3(no Cn status change,flag "5 ADRs Accepted, W20+ pending");§10 W19 row → closed verdict;W20+ NOT pre-created(rolling JIT);§11 carry-overs(5 Accepted ADRs become W20+ tracking);§12 Milestones row(累計 17→18);Last-Updated + Update-history
- [ ] F6.7 W20-frontend-wave-a kickoff candidate flagged in session-start.md §10 W19 row;actual W20 phase folder created in a separate kickoff cascade(NOT at W19 closeout — rolling JIT precedent W17→W18 / W18→W19)
- [ ] F6.8 No new W19 OQ expected — confirm `decision-form.md` untouched(strategic 岔口 → Accepted ADR options,not new OQs)

---

## Cross-Cutting

- [ ] Each commit references `progress.md` Day-N entry(R2)— `docs(planning):` housekeeping commits exempt
- [ ] Component tag in commit message — F1/F2/F3 = governance + audit / F4 = governance / F5 = cross-Cn UI pattern / F6 = governance
- [ ] OQ status sync to `decision-form.md`(R4)— expected no-op(strategic 岔口 → ADR options, not new OQs);confirm at F6
- [ ] CLAUDE.md §5.1 H1 — W19 = the H1 ADR drafting phase(F3) + R1 plan(F0) + R5 ADR-before-implementation(W20+ kickoffs gated on F6 ADR acceptance)
- [ ] CLAUDE.md §5.2 H2 — NO new dependency in W19(audit only);F3 ADR-0026 Option B may surface Key Vault SDK as a new dep — flagged in that ADR not introduced
- [ ] CLAUDE.md §5.4 H4 — Tier 2 boundary policing is the F5 deliverable
- [ ] CLAUDE.md §3 conventions — NO `frontend/` or `backend/` code change in W19;all output = .md audit + .md ADRs;Plan / checklist / progress markdown follow the W18 template structure
- [ ] Karpathy §1.1 think-before-coding — W19 is itself the "think" phase for the design-mockups implementation work,by-design
- [ ] Karpathy §1.2 simplicity — W19 audit aims for the **minimum** set of ADRs(5);if F1 surfaces a 6th deviation,flag + decide whether it's ADR-worthy or covered by an existing ADR's "Consequences"
- [ ] Karpathy §1.3 surgical — NO mockup edits;NO `architecture.md` edits;NO `COMPONENT_CATALOG.md` Cn design-note rewrites;all editorial work lands in W20+ kickoffs

---

**Lifecycle reminder**:呢份 checklist 衍生自 `plan.md` deliverables。新加 deliverable 必須先入 plan + §7 changelog,然後再加 checklist item。延後 item 標 🚧 + reason,**唔可以刪**未勾選 `[ ]`。
