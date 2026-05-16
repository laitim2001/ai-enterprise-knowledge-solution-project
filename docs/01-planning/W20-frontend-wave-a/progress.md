---
phase: W20-frontend-wave-a
plan_ref: ./plan.md
checklist_ref: ./checklist.md
status: active
last_updated: 2026-05-16
---

# Phase W20 — Progress

> Daily progress + decisions + commits;結尾 retro。Status:`active` from kickoff 2026-05-16(per Chris directive + 6 ADRs Accepted + AskUserQuestion A1 pick — same pattern as W17 D0 + W18 D0)。

---

## Day 0 — 2026-05-16(Kickoff)

### F0 — Kickoff cascade(landed)

**Branch**:`main` post-W19 closeout(`6a34a41` → `origin/main`)。Working tree clean at start;single kickoff commit will land:
- `docs/adr/0025-kb-detail-8-tabs.md` Status Proposed → Accepted + Wave A 7-tab scope note
- `docs/adr/0028-kb-new-5-step-wizard.md` Status Proposed → Accepted
- `docs/adr/0031-chat-advanced-surfaces.md` Status Proposed → Accepted + Option B Wave A +3 backend days note
- `docs/adr/README.md` — 3 ADR rows Status flip(Proposed→Accepted)+ Next NNNN unchanged(0033)+ Update history row
- `docs/architecture.md` — inline-tagged §5.x amendments(§5.2 Chat / §5.3 Dashboard / §5.4-§5.5 KB List+Detail / §5.5.5 NEW /kb/new wizard / §5.10-§5.11 Login+Register)— doc version held per W18 ADR-0024 / §3.4 / §3.7 precedent
- `docs/01-planning/W20-frontend-wave-a/{plan,checklist,progress}.md` — created `status: active`
- `docs/12-ai-assistant/01-prompts/01-session-start.md` — §10 W20 row added(`active`)+ §12 milestones row(`active`)+ Update history + Last-Updated

### Decisions captured at kickoff

| Decision | Rationale | Authority |
|---|---|---|
| Wave A ships **7-tab `-Access`**(not 8-tab) | F4 §3.6 recommend — Wave A backend already +3 days from ADR-0031 Option B;Access tab needs ADR-0027 Option A RBAC infra(~20 backend days)which is Wave C1 scope;7-tab Wave A + Access tab Wave C1 is the realistic split | Chris AskUserQuestion 2026-05-16 A1 pick |
| **Mock-auth default through Wave C** | User 岔口 2 W19 — real-MSAL feature-flagged concurrent ship Wave C;Wave A doesn't touch real-MSAL path | Chris W19 F0 kickoff AskUserQuestion |
| ADR-0031 Option B **server-side** Conversation History | Promotes C10 §7 Tier 2 → Tier 1;Postgres `conversations` + `messages` tables per ADR-0023 backing pattern + in-memory fallback;+3 backend days extends Wave A backend from ~5-7d to ~8-10d | Chris W19 F6 AskUserQuestion(rejected Option A localStorage Tier 1 + Option C Tier 2 defer)|
| ADR-0030 + ADR-0032 **SKIPPED**(absorbed) | Dashboard polish + Trace 3 viz + /traces list + Topbar/Sidebar additive scope = small enough to absorb into Wave A F1+F2 (Dashboard/Topbar parts) + Wave B (Trace/Traces parts) without separate ADR record | W19 F6 closeout decision |
| Wave C **MUST split into C1+C2** per F4 §3.6 trigger | Chris Option A+B picks (ADR-0027 full RBAC ~20 backend days + ADR-0026 Settings fully editable ~22 NEW endpoints) combined ~42 backend days exceeds single Wave C phase budget;C1 + C2 scope concrete split decision at W22 kickoff | W19 F6 closeout |
| **2 NEW dependencies** Plan B sequencing at Wave C kickoff | Key Vault SDK + Entra Graph SDK — triggered by ADR-0026 Option B + ADR-0027 Option A picks;H2 stop-and-ask implicit via Chris pick;R8 corp-proxy mitigation per ADR-0017 applies to both — Plan B sequencing decision deferred to Wave C kickoff per ADR-0017 Decision-rule #5 | W19 F6 |

### Tier 2 boundary enforcement(Wave A)

Per W19 F5 27-affordance Tier 2 catalog + `<DisabledAffordance>` shared component spec:

| Tier 2 leak surface | Wave A treatment |
|---|---|
| Workspace switcher(multi-tenancy)| `<DisabledAffordance tier={2}>` chip in topbar — F1.2 |
| Access tab(KB Detail RBAC)| `<TabsTrigger disabled>` + `<DisabledAffordance tier={1.5}>` — F5.8;Wave C1 activates |
| Multimodal caption gen / image clustering / blockchain | `<DisabledAffordance tier={2}>` rows in `/kb/new` Step 4 + `/kb-upload/[id]` Source step — F4.4 + F6.1 |
| Labs section in sidebar | Hidden by default(F1.4)— prototype-only `/labs/*` routes don't ship per W19 F5.4 Option C |
| Forgot password on `/login` | `<DisabledAffordance tier={2}>` chip — F7.1 |
| Chunking Lab "Apply" button | `<DisabledAffordance tier={2}>` "re-chunking pending" — F5.6;Tier 1 = preview-only |

### Actual vs Planned Effort(Day 0)

| F | Planned | Actual | Δ |
|---|---|---|---|
| F0.1 ADR-0025 Status flip | 5 min | TBD | TBD |
| F0.2 ADR-0028 Status flip | 5 min | TBD | TBD |
| F0.3 ADR-0031 Status flip | 5 min | TBD | TBD |
| F0.4 ADR README sync | 5 min | TBD | TBD |
| F0.5 architecture.md §5.x inline amendments | 30 min | TBD | TBD |
| F0.6 plan/checklist/progress create | 60 min | ~45 min | -25% |
| F0.7 session-start.md §10+§12 sync | 15 min | TBD | TBD |
| **Day 0 total** | **~2 hours** | TBD | TBD |

### Notes / open items at Day 0

- W19 F4 §1.2 backend gap items 3 + 4(Q6 recent queries + Eval-cache decisions)defer = empty-state CTA per W18 F4 acceptance — preserved as Wave A scope-minimum path(can flip to data-wired if user enables at any Day-N — see F2.2(c)/(d))
- ADR-0031 Option B Postgres tables + endpoints decision = reuse W17 F1 / ADR-0023 backing pattern(`make_conversation_store()` factory + in-memory fallback when `DATABASE_URL` unset)— same shape as `make_kb_backend` + `make_users_store`,no new architectural pattern
- W18 milestone `[oklch(`=0 across `frontend/` MUST be preserved through Wave A — F1.6 + F2.5 + F3.14 + F4.6 + F5.9 + F6.3 + F7.3 + F8.3 all gate on it
- F8.4 Vitest target 20+/20+ tests = additive on top of W18 F8.4 baseline(4 files / 13 tests) — no regression on existing tests
- F8.5 Playwright run via `PW_CHANNEL=chrome pnpm test:e2e`(system Chrome — ADR-0017 Plan B (a) realised 2026-05-13)— no longer R8-blocked for the *run*;the `npx playwright install chromium` block remains for fresh bundled Chromium, but unchanged

---

<!-- Day 1+ entries to be appended by AI as F1-F9 land. Each entry follows the template:

## Day N — YYYY-MM-DD

### F<n> — <deliverable> (landed)

**Branch**:...
**Commits this day**:...

#### What landed

- ...

#### Acceptance criteria status (per checklist.md)

- [x] F<n>.1 — ...
- [x] F<n>.2 — ...

#### Deviations(if any)

| F# | Plan said | Actual | Why | Approver |
|---|---|---|---|---|

#### Decisions / new OQ / risk surfaced

- ...

#### Actual vs Planned Effort

| F | Planned | Actual | Δ |
|---|---|---|---|

#### Carry-overs to next Day-N

- ...

---

-->

## Retro(填 at F9 closeout)

> 7 sections per W18 / W19 retro template:
>
> 1. What worked
> 2. What didn't & friction
> 3. Surprises(positive + negative)
> 4. Decisions(architectural / scope / sequencing)
> 5. Carry-overs to W21+(NOT pre-created — items only;next phase folder at W21 kickoff)
> 6. Time tracking(plan-day budget vs actual real-calendar)
> 7. Spec-ref alignment(architecture.md v6 + ADR-0025/0028/0031 verification)
>
> **Phase Gate verdict** = TBD(PASS / PARTIAL PASS / FAIL with explicit rationale)

---

**Lifecycle reminder**:呢份 progress.md `status=active`(2026-05-16,per kickoff)。每 Day-N entry append；retro 喺 F9 closeout 寫。Status flip `active`→`closed` at F9.4。
