---
phase: W15-polish-closeout
plan_ref: ./plan.md
status: draft
last_updated: 2026-06-10
---

# Phase W15 — Checklist

> Atomic checkbox(每 item ≤ 0.5–2 hour effort per W6 C10 calibration)。
> Status:`draft` — pending W15 D1 active flip post stakeholder authorization。

## F1 — V5 Eval Console implementation

- [ ] F1.1 `frontend/app/eval/page.tsx` rebuild — top filter bar(Eval set Select + Run + Run Single Button)+ replace W12 F4.5 baseline
- [ ] F1.2 Run config card — LLM Select + Reranker Select + Top K Input + CRAG threshold Slider + Intent type Select per design ref §2.5 layout
- [ ] F1.3 4-metric cards(R@5 / Faithfulness / ContextRelevancy / AnswerRelevancy)— score + PASS/FAIL Badge + threshold display per architecture.md v6 §5.6
- [ ] F1.4 Failed queries table — query_id + category Badge + Inspect Link → V6 Debug View
- [ ] F1.5 W4 Reranker Shootout table — 4-way comparison from W4-W6 stable baseline + recommendation(historical read-only display)
- [ ] F1.6 Loading + empty state per design ref §3.4-§3.5

## F2 — V6 Debug View implementation

- [ ] F2.1 `frontend/app/debug/[traceId]/page.tsx` NEW route — Trace ID header + Total ms + cost summary
- [ ] F2.2 9-stage timeline accordion — Query Preprocessor / Hybrid Retrieval / Reranker / CRAG / LLM Synthesis / Final Response stages per arch v6 §3.5
- [ ] F2.3 Per-stage expand-collapse via shadcn Accordion — full prompt / raw output for LLM stages
- [ ] F2.4 Open in Langfuse link(stub URL pattern Tier 1;real integration W16+ post-proxy)
- [ ] F2.5 Loading + error states(trace not found / Langfuse unreachable)

## F3 — Responsive + a11y polish across 9 views

- [ ] F3.1 Keyboard navigation audit — Tab order V1-V9 + focus-ring visible per design ref §3.6 + Esc dismisses Dialog/Sheet
- [ ] F3.2 ARIA labels audit — interactive elements + form fields + Dialog title-content link + Tabs role labels + Accordion role labels
- [ ] F3.3 Mobile responsive verify — 320px screens + TabsList horizontal-scroll + Sheet sidebar + Card stack
- [ ] F3.4 CO_W14_F4_error_boundary token cleanup — `frontend/components/error/error-boundary.tsx` lines 36/39/42/49/58/67 6 hardcoded oklch → Tailwind tokens(`border-border` / `text-destructive` / `bg-muted` etc per Karpathy §1.3 surgical scope expansion warranted W15 polish phase)

## F4 — Playwright E2E + pixel diff baseline harness

- [ ] F4.1 Playwright install + config(`playwright.config.ts` + `frontend/tests/e2e/` directory)— corp proxy R8 mitigation if needed
- [ ] F4.2 Golden-path E2E:landing → register → verify → login → /chat → ask query → citations(W12+W13+W14 manual smoke deferred subsumed)
- [ ] F4.3 Admin golden-path E2E:login → /admin → /admin/kb → click KB Card → /admin/kb/[id]?tab=settings → save toast
- [ ] F4.4 Pixel diff baseline — capture baseline screenshots per view + commit `frontend/tests/e2e/screenshots/baseline/` + maskedDiff for dynamic regions
- [ ] F4.5 CI integration plan(non-blocking;Beta hardening trigger if cost concerns;local-only baseline OK Tier 1 per PARTIAL PASS acceptance)

## F5 — Tier 1 UI sprint cycle final closeout + W16+ Beta deploy phase folder kickoff

- [ ] F5.1 W15 phase Gate verdict landed(PASS / PARTIAL PASS / FAIL per W14 F5.1 pattern)
- [ ] F5.2 W15 progress.md retro 7 sections + **Tier 1 UI sprint cycle final closeout retrospective**(W12+W13+W14+W15 cumulative learnings)
- [ ] F5.3 `docs/01-planning/W16-beta-deploy/{plan,checklist,progress}.md` draft per W11 plan F1+F2+F3 Track A IT cred event-triggered + R-B1 closure
- [ ] F5.4 W15 plan + checklist + progress frontmatter status flipped to `closed`
- [ ] F5.5 No new OQ surface expected;if surface → sync to decision-form.md per R4
- [ ] F5.6 4-sprint UI Tier 1 expansion 收尾 marker — architecture.md v6 §13.12 fully implemented;ready for W16+ Beta deploy

---

## Cross-Cutting

- [ ] Each commit references `progress.md` Day-N entry(R2)
- [ ] Component tag in commit message per CC-1(C09 / C06 / C07 / C10 / C11)
- [ ] OQ status sync to `decision-form.md`(R4)— no W15 critical OQ expected
- [ ] Risk register update if any new risk surface
- [ ] CLAUDE.md §5.1 H1 boundary check:no architectural change without ADR(W15 scope already covered by ADR-0014 + ADR-0015 + ADR-0016)
- [ ] CLAUDE.md §5.2 H2 boundary check:no new vendor / dependency without ADR(Playwright as Tier 1 utility test framework — pre-approved per CLAUDE.md §5.2「dev dependency」example exception OR ADR-0017 if scope expand)
- [ ] CLAUDE.md §3.2 frontend conventions check:no `any` / no @ts-ignore / shadcn/ui only / tokens consumption verified(grep oklch=0 across all touched files including CO_W14_F4_error_boundary post-cleanup)
- [ ] CLAUDE.md §5.5 H5 security check:no secret commit;Langfuse stub URL not real production endpoint

---

**Lifecycle reminder**:呢份 checklist 衍生自 `plan.md` deliverables。新加 deliverable 必須先入 plan + changelog,然後再加 checklist item。
