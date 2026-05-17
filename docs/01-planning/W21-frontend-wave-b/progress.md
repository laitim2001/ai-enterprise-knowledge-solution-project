---
phase: W21-frontend-wave-b
plan_ref: ./plan.md
checklist_ref: ./checklist.md
status: active
last_updated: 2026-05-17
---

# Phase W21 — Progress

> Daily progress + decisions + commits;結尾 retro。Status:`active` from kickoff 2026-05-17(per Chris directive「開 W21-frontend-wave-b kickoff」+ ADR-0029 Accepted + ADR-0030 absorbed)。

---

## Day 0 — 2026-05-17(Kickoff)

### F0 — Kickoff cascade(landed)

**Branch**:`main` post-W20 closeout `50b58fc` + push 2026-05-17。Working tree clean at start;single kickoff commit will land:
- `docs/adr/0029-doc-detail-3-pane-layout.md` — Implementation Note appended at W21 kickoff(same convention as W20 F0 / W18 ADR-0024 Implementation Deliverables;Status verify Accepted Option C no-op since W19 F6 `6a34a41` already flipped)
- `docs/adr/README.md` — ADR-0030 SKIPPED footnote preserved per W19 F6 closeout(no-op verify);ADR-0029 row unchanged(`Accepted` Status maintained — Implementation Status note will be appended at F8.3 closeout per W20 F9.3 precedent)
- `docs/architecture.md` — 4 inline-tagged §5 amendments(§5.5.2 KB Detail Chunks tab unchanged annotation + cross-ref / §5.5.2a NEW Document Detail page 3-pane per ADR-0029 / §5.6 Eval Console 6-section refactor / §5.7 Traces /traces index + /traces/[traceId] 3 viz modes per ADR-0030 absorbed)
- `docs/01-planning/W21-frontend-wave-b/{plan,checklist,progress}.md` — created `status: active`
- `docs/12-ai-assistant/01-prompts/01-session-start.md` — §10 W21 row added(`active`)+ §12 milestones row(`active`)+ Update history + Last-Updated

### Decisions captured at kickoff

| Decision | Rationale | Authority |
|---|---|---|
| **W21 Wave B scope = 4 routes + 2 NEW backend endpoints**(per ADR-0029 + ADR-0030 absorbed) | W19 F4 §2 Wave B scope skeleton signed off;ADR-0029 Accepted Option C `/kb/[id]/docs/[docId]` + ADR-0030 absorbed Dashboard polish shipped Wave A + Trace 3 viz + /traces list ship Wave B | Chris W20 F9 closeout post-push directive 2026-05-17 |
| **Mock-auth default continues through Wave C** | User 岔口 2 W19 — real-MSAL feature-flagged concurrent ship deferred Wave C;Wave B doesn't touch real-MSAL path | Chris W19 F0 kickoff AskUserQuestion(preserved through W20 + W21)|
| **Embedding vector preview feasibility verify at F3.5 implementation time**(not kickoff blocker) | Per ADR-0029 §3 alt #3 default — if Azure Search exposes vectors via `select=*,content_vector`,implement;if expensive,`<DisabledAffordance variant="p3-preview" showBadge>` Tier 2 disabled affordance | ADR-0029 §3 alt #3 default + Karpathy §1.4 goal-driven defer |
| **Rule-of-3 wizard primitive promotion DEFER**(W20 F6.2 carry-over) | Wave B has **NO wizard surface**(doc detail + eval + traces 全部 non-wizard);per Karpathy §1.3 surgical — don't bundle unrelated refactor into Wave B;defer to standalone refactor commit OR Wave C(/settings + /users have wizard surfaces) | AI Karpathy §1.3 self-judgment;Chris confirms via no-objection at kickoff |
| **3 viz modes locked**(vertical default + waterfall + flame) | ADR-0030 absorbed scope per W19 F4 §2.1 + ADR-0030 SKIPPED-but-implemented decision;no semantic search / fuzzy filter / other viz modes | W19 F4 §2.1 |
| **Flame viz visual baseline defer Wave C+** | Wave A trace data is flat(stage list,no nesting);flame mode renders as waterfall-equivalent — visual baseline pixel-diff would just verify waterfall-shape;defer to Wave C+ when nested-stage traces become common(per ADR-0020 Context Expander multi-step traces) | F7.5 PARTIAL PASS allowance + Karpathy §1.2 don't pre-build |
| **No new dependencies**(per CC6) | Wave B uses existing `psycopg>=3.2` + shadcn/ui + tokens;NO Key Vault SDK / NO Entra Graph SDK — those are Wave C kickoff scope per ADR-0017 Plan B sequencing decision | CLAUDE.md §5.2 H2 + ADR-0017 |

### Tier 2 boundary enforcement(Wave B)

Per W19 F5 27-affordance Tier 2 catalog + `<DisabledAffordance>` shared component(F1.5 W20 Wave A landed):

| Tier 2 leak surface | Wave B treatment |
|---|---|
| Embedding vector preview Tier 2 fallback(if Azure Search vector exposure expensive)| `<DisabledAffordance variant="p3-preview" showBadge>` Tier 2 chip — F3.5 |
| EvalReport Ops Metrics fields missing | `<DisabledAffordance>` "Ops metrics — Wave C+" — F4.6 |
| EvalReport CRAG fields missing(crag_avg_iterations) | Coverage-only fallback display — F4.7 |
| Flame viz nested-stage data missing | Renders as waterfall-equivalent for Wave A flat traces;forward-compat for ADR-0020 nested stages — F6.4 |
| `/settings` link from `/eval` Recommendation card(if exists)| `<DisabledAffordance>` "Edit thresholds — Wave C" — F4.5(advisory only Wave B) |

### Actual vs Planned Effort(Day 0)

| F | Planned | Actual | Δ |
|---|---|---|---|
| F0.1 ADR-0029 Implementation Note appended | 10 min | TBD | TBD |
| F0.2 ADR-0030 SKIPPED footnote verify | 5 min | TBD | TBD |
| F0.3 architecture.md 4 inline amendments | 30 min | TBD | TBD |
| F0.4 plan/checklist/progress create | 60 min | ~40 min(post-W20 pattern reuse + accumulated context) | -33% |
| F0.5 session-start.md §10+§12+Update history | 15 min | TBD | TBD |
| **Day 0 total** | **~2 hours** | TBD | TBD |

### Notes / open items at Day 0

- W19 F4 §2 Wave B scope skeleton signed off — F1-F8 mapped onto ADR-0029 + ADR-0030 absorbed scope
- W17 F3 RAGAs backend endpoints(`POST /eval/run` + `POST /eval/shootout`)= F4 frontend consumes,no new backend
- W16 F5.5 `GET /debug/trace/{trace_id}` = F6 frontend consumes,no new backend(only F2 adds `/traces` list endpoint)
- W18 ADR-0024 unified shell IA + `/traces/[traceId]` flat URL preserved — Wave B routes inherit
- W20 milestone `[oklch(`=0 across `frontend/` MUST be preserved through Wave B — F3.10 + F4.10 + F5.5 + F6.7 + F7.3 all gate on it
- F7.4 Vitest target 16-18 files/45+ tests = additive on top of W20 F8.4 baseline(14 files / 37 tests) — no regression on existing tests
- F7.5 Playwright run via `PW_CHANNEL=chrome pnpm test:e2e`(ADR-0017 Plan B (a) realised 2026-05-13)— no longer R8-blocked for the *run*;the `npx playwright install chromium` block remains for fresh bundled Chromium, but unchanged

### Next

- Day 1 — F1 + F2 backend(`GET /kb/{kb_id}/docs/{doc_id}` enriched + `GET /traces?filter=...&since=...` list)~2 days budget
- Day 2-4 — F3 `/kb/[id]/docs/[docId]` 3-pane(largest deliverable;outline + chunks + inspector + embedding vector feasibility verify)~2-3 days
- Day 4-5 — F4 `/eval` 6-section refactor consuming existing W17 F3 RAGAs ~2 days
- Day 5 — F5 `/traces` index list view ~0.5 days
- Day 5-7 — F6 `/traces/[traceId]` 3 viz modes(vertical + waterfall + flame SVG components)~1.5 days
- Day 7 — F7 cross-cutting verify + F8 closeout

---

<!-- Day 1+ frontend entries to be appended. Template:

## Day N — YYYY-MM-DD

### F<n> — <deliverable> (landed)

**Branch**:...
**Commits this day**:...

#### What landed

- ...

#### Acceptance criteria status (per checklist.md)

- [x] F<n>.1 — ...

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

## Retro(填 at F8 closeout)

> 7 sections per W18 / W19 / W20 retro template:
>
> 1. What worked
> 2. What didn't & friction
> 3. Surprises(positive + negative)
> 4. Decisions(architectural / scope / sequencing)
> 5. Carry-overs to W22+(NOT pre-created — items only;next phase folder at W22 kickoff)
> 6. Time tracking(plan-day budget vs actual real-calendar)
> 7. Spec-ref alignment(architecture.md v6 + ADR-0029 verification + ADR-0030 absorbed footnote)
>
> **Phase Gate verdict** = TBD(PASS / PARTIAL PASS / FAIL with explicit rationale)

---

**Lifecycle reminder**:呢份 progress.md `status=active`(2026-05-17,per kickoff)。每 Day-N entry append;retro 喺 F8 closeout 寫。Status flip `active`→`closed` at F8.4。
