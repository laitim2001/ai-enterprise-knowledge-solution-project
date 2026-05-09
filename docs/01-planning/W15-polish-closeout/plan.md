---
phase: W15-polish-closeout
name: "Polish + Closeout — Phase 4 of 4 in W12-W15 UI Tier 1 expansion sprint cycle (V5 Eval Console + V6 Debug View + responsive + a11y polish + Playwright E2E + pixel diff baseline harness + Tier 1 UI sprint cycle final closeout)"
sprint_week: W15
start_date: 2026-07-07             # tentative — assumes W14 closeout 2026-07-04 + 1-day buffer
end_date: 2026-07-11               # 5 working days(possibly +1-2 if F4 Playwright E2E install + golden-path scope absorbs)
status: active                     # `active` — W15 D1 implementation start landed 2026-06-10 (real-calendar same-day collapse cycle 4 of 4 final per pivot momentum continuation of W14 closeout — Tier 1 UI sprint cycle Phase 4 of 4 begins)
spec_refs:
  - architecture.md v6 §5.6           # V5 Eval Console
  - architecture.md v6 §5.7           # V6 Debug View
  - architecture.md v6 §5.8           # Cross-view UX patterns (responsive + a11y)
  - architecture.md v6 §13.12         # v5.1→v6 amendment
  - ADR-0015                          # UI Tier 1 expansion 9 views
prior_phase: W14-admin-views
related_artifacts:
  - docs/01-planning/W14-admin-views/progress.md     # W14 retro § Carry-overs CO_F3a-c + CO_W14_F4_error_boundary + CO_W14_smoke
  - docs/02-architecture/ui-design-reference-v6.md   # §2.5 V5 + §2.6 V6 wireframes + §6 W15 implementation sequencing
  - frontend/components/nav/admin-shell.tsx          # W12 F4 admin shell baseline (preserved)
  - frontend/app/eval/                                # V5 existing barebones (W12 baseline preserved)
  - frontend/components/error/error-boundary.tsx     # CO_W14_F4_error_boundary token cleanup target
---

# Phase W15 — Polish + Closeout(Phase 4 of 4 UI sprint cycle W12-W15 — FINAL)

> **Plan version**:1.0(draft 2026-06-10 W14 D5 F5 closeout cascade — rolling JIT per CLAUDE.md §10 R1)
> **Owner**:Chris(Tech Lead + stakeholder)+ AI(implementation)
> **Approved by**:_(pending W15 D1 active flip post stakeholder authorization)_

---

## 1. Scope(rolling-JIT W14 D5 F5 closeout draft per pivot momentum)

W15 = **Polish + Closeout sprint** — Phase 4 of 4-sprint UI Tier 1 expansion(W12-W15) — **final cycle**。Goals:

- **V5 Eval Console implementation**(`/eval`)— filter bar + Run config card + 4-metric cards(R@5/Faith/CtxRel/AnsRel)+ Failed queries table + W4 Reranker Shootout table per architecture.md v6 §5.6 + design ref §2.5 wireframe
- **V6 Debug View implementation**(`/debug/[traceId]`)— 9-stage timeline accordion(per-stage duration / cost / data preview / expand-collapse + Open in Langfuse link)per architecture.md v6 §5.7 + design ref §2.6 wireframe
- **Responsive + a11y polish across all 9 views** — keyboard nav / ARIA labels / focus-ring consistency / mobile responsive verify across V1-V9
- **Playwright E2E baseline harness** — golden-path E2E tests subsume manual smoke deferred across W12+W13+W14 cycles(CO_W14_smoke systematic subsume)
- **Pixel diff baseline harness** — visual regression detection against tokens.ts ratified Option C "Warm Charcoal + Coral Accent"
- **W14 carry-over absorption**:CO_W14_F4_error_boundary token cleanup pass(`frontend/components/error/error-boundary.tsx` 6 hardcoded oklch values → Tailwind tokens)
- **Tier 1 UI sprint cycle final closeout** + W16+ Beta deploy phase folder rolling JIT trigger

**Out of W15 scope**(absorbed by W16+):
- Production launch deployment(Track A IT cred + Beta cohort cutover post W16+ R-B1 closure)
- Forgot password / 2FA / OAuth providers(Tier 2 per architecture.md v6 §11)
- Real ACS smoke + sender domain SPF/DKIM(W16+ post Track A)
- CO_F3a-c backend implementation(`GET /kb/{id}/documents` listing + `GET /kb/{id}/documents/{id}/chunks` + name/description PATCH + reindex/delete)— Beta hardening trigger fit;W15 frontend stub mitigation pattern preserved

**Pre-condition for W15 promotion**(等 W15 D1 active flip):
- W14 D5 F5 closeout PASS WITH SMOKE-USER-DEFERRED CAVEAT verdict landed
- ADR-0014 + ADR-0015 + ADR-0016 status `Accepted`(unchanged from W13 baseline)
- W14 frontmatter close cascade complete(plan + checklist + progress active → closed)

## 2. Deliverables(F1-F5)

### F1 — V5 Eval Console implementation

- **Component(s)**:**C09** Admin Console UI + **C06** Eval Framework(consume existing 4-metric eval pipeline)
- **Spec ref**:architecture.md v6 §5.6 V5 Eval Console + ui-design-reference-v6.md §2.5 V5 wireframe
- **OQ deps**:none
- **Acceptance criteria**:
  - F1.1 `frontend/app/eval/page.tsx` rebuild from W12 F4.5 baseline to V5 wireframe — top filter bar(Eval set selector + Run + Run Single buttons)
  - F1.2 Run config card — LLM Select + Reranker Select + Top K Input + CRAG threshold Slider + Intent type Select per design ref §2.5 layout
  - F1.3 4-metric cards(Recall@5 / Faithfulness / Context Relevancy / Answer Relevancy)— each shows score + PASS/FAIL Badge + threshold compare per architecture.md v6 §5.6
  - F1.4 Failed queries table — list query_id / category(OOS refusal / borderline / etc)/ Inspect Link → V6 Debug View
  - F1.5 W4 Reranker Shootout table — 4-way comparison from W4-W6 stable baseline + recommendation(historical read-only display)
  - F1.6 Loading state(Skeleton)+ empty state(no eval runs yet)per design ref §3.4-§3.5
- **Effort estimate**:1 day(W15 D1)
- **Owner**:AI(implementation)+ user(visual review)

### F2 — V6 Debug View implementation

- **Component(s)**:**C09** Admin Console UI + **C07** Observability Stack(consume Langfuse trace API)
- **Spec ref**:architecture.md v6 §5.7 V6 Debug View + ui-design-reference-v6.md §2.6 V6 wireframe
- **OQ deps**:F1 baseline(Failed queries Inspect Link → V6)
- **Acceptance criteria**:
  - F2.1 `frontend/app/debug/[traceId]/page.tsx` NEW route — Trace ID header + Total ms + cost summary
  - F2.2 9-stage timeline accordion — Query Preprocessor / Hybrid Retrieval / Reranker / CRAG Confidence Judge / LLM Synthesis / Final Response per architecture.md v6 §3.5 actual stages;each stage shows duration / cost / key data preview
  - F2.3 Per-stage expand-collapse via shadcn Accordion(W12 D3 installed)— full prompt / raw output for LLM stages
  - F2.4 Open in Langfuse link(stub URL pattern `https://langfuse.example.com/trace/{traceId}` if production endpoint not exposed Tier 1;real integration W16+ post-proxy)
  - F2.5 Loading + error states(trace not found / Langfuse unreachable)
- **Effort estimate**:1 day(W15 D2)
- **Owner**:AI(implementation)+ user(visual review)

### F3 — Responsive + a11y polish across 9 views

- **Component(s)**:cross-cutting(C09 admin shell + C10 chat UI + C11 auth views)
- **Spec ref**:architecture.md v6 §5.8 Cross-view UX patterns + design ref §3 cross-view consistency rules
- **OQ deps**:F1 + F2 baseline
- **Acceptance criteria**:
  - F3.1 Keyboard navigation audit — Tab order across V1-V9 / focus-ring visible per design ref §3.6 / Esc dismisses Dialog/Sheet
  - F3.2 ARIA labels audit — interactive elements / form fields / Dialog title-content link / Tabs role labels / Accordion role labels
  - F3.3 Mobile responsive verify — 320px screens / TabsList horizontal-scroll / Sheet sidebar mobile / Card stack mobile
  - F3.4 CO_W14_F4_error_boundary token cleanup — `frontend/components/error/error-boundary.tsx` lines 36/39/42/49/58/67 6 hardcoded oklch values → Tailwind tokens(`border-border` / `text-destructive` / `bg-muted` etc per Karpathy §1.3 surgical scope expansion now warranted W15 polish phase)
- **Effort estimate**:0.5 day(W15 D3 first half)
- **Owner**:AI(implementation)+ user(keyboard nav + screen reader smoke)

### F4 — Playwright E2E + pixel diff baseline harness

- **Component(s)**:cross-cutting governance(test harness)
- **Spec ref**:design ref §6 W15 scope + CLAUDE.md §3.2 test framework(Vitest + React Testing Library baseline preserved;Playwright additive)
- **OQ deps**:F1-F3 baseline
- **Acceptance criteria**:
  - F4.1 Playwright install + config(`playwright.config.ts` + `frontend/tests/e2e/` directory)— corp proxy R8 mitigation if needed via personal Azure dev tier OR pre-download wheels(ADR-0017 trigger if vendor-decision pivot needed)
  - F4.2 Golden-path E2E baseline:landing → register → verify → login → /chat → ask query → see citations(W12+W13+W14 manual smoke deferred subsumed)
  - F4.3 Admin golden-path E2E:login → /admin → /admin/kb → click KB Card → /admin/kb/[id]?tab=settings → save → verify toast
  - F4.4 Pixel diff baseline harness(@playwright/test screenshot + maskedDiff)— capture baseline screenshots per view + commit `frontend/tests/e2e/screenshots/baseline/`;mask dynamic regions(timestamp / KB id)via maskedDiff config
  - F4.5 CI integration plan(non-blocking — Beta hardening trigger if Playwright run cost concerns surface;local-only baseline OK Tier 1 per PARTIAL PASS acceptance)
- **Effort estimate**:1.5 day(W15 D3 second half + D4 — largest deliverable)
- **Owner**:AI(implementation)+ user(visual baseline approval)

### F5 — Tier 1 UI sprint cycle final closeout + W16+ Beta deploy phase folder rolling JIT trigger

- **Component(s)**:cross-cutting governance
- **Spec ref**:CLAUDE.md §10 R1 rolling-JIT + R5 phase closeout discipline + design ref §6 implementation sequencing W16+ trigger
- **OQ deps**:F1-F4 verdict outcomes
- **Acceptance criteria**:
  - F5.1 W15 phase Gate verdict landed(PASS / PARTIAL PASS / FAIL with explicit rationale per W12 F5.1 + W13 F7.1 + W14 F5.1 pattern)
  - F5.2 W15 progress.md retro 7 sections complete + **Tier 1 UI sprint cycle final closeout retrospective**(W12+W13+W14+W15 cumulative learnings — 4-sprint cycle final retrospective)
  - F5.3 `docs/01-planning/W16-beta-deploy/{plan,checklist,progress}.md` draft per W11 plan F1+F2+F3 Track A IT cred event-triggered + R-B1 closure trigger(rolling JIT — depends on Track A IT cred populate event)
  - F5.4 W15 plan + checklist + progress frontmatter status flipped to `closed`
  - F5.5 No new OQ surface expected;if surface → sync to decision-form.md per R4
  - F5.6 4-sprint UI Tier 1 expansion 收尾 marker — architecture.md v6 §13.12 amendment 完整 implemented(9 views × 6+ components × hybrid auth × ACS email × responsive/a11y/E2E/pixel diff baseline);**ready for W16+ Beta deploy production launch**
- **Effort estimate**:0.5 day(W15 D5)
- **Owner**:AI(draft)+ user(approve + sign-off)

---

## 3. Success Criteria(Phase Gate to Beta Deploy)

W15 phase Gate **PASS condition**:
1. F1 V5 Eval Console renders + 4-metric cards + Failed queries table + Reranker Shootout table ✅
2. F2 V6 Debug View renders + 9-stage timeline + Open in Langfuse link ✅
3. F3 Responsive + a11y across 9 views verified + CO_W14_F4_error_boundary token cleanup ✅
4. F4 Playwright E2E golden-path + admin path + pixel diff baseline harness ✅
5. F5 Tier 1 UI sprint cycle final closeout + W16+ phase folder kickoff ✅

W15 phase Gate **PARTIAL PASS** acceptable per Karpathy §1.4:
- F2.4 Open in Langfuse link disabled if Langfuse trace integration deferred(stub URL OK Tier 1)
- F4.5 CI integration deferred to W16+ if Playwright cost surfaces(local-only baseline OK Tier 1)
- F1.5 W4 Reranker Shootout table read-only display(historical W4-W6 baseline;not active rerunnable Tier 2)

W15 phase Gate **FAIL condition**:
- ADR-0014 / ADR-0015 / ADR-0016 scope creep into Tier 2(GraphRAG / multi-agent / multi-tenancy)
- W12 F4 admin shell baseline regression
- E2E harness conflicts with existing test infrastructure(W7 backend pytest baseline preserved)

## 4. Risks(Phase-Specific)

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| F2 Langfuse trace API access blocked R8 corp proxy | Medium | Low | F2.4 stub URL acceptable per PARTIAL PASS;real Langfuse integration W16+ post-proxy |
| F4 Playwright install blocked R8 corp proxy | Medium | Medium | npm install via personal-Azure dev tier OR pre-download wheels;ADR-0017 trigger if vendor-decision pivot needed |
| F4.4 Pixel diff false-positive on dynamic content | Low | Low | Mask dynamic regions(timestamp / KB id)via maskedDiff config |
| F1.5 W4 Reranker Shootout table data source | Low | Low | Static JSON file from W4-W6 stable baseline(`backend/eval/reranker_shootout_results.json` if exists or new artifact) |
| F3 a11y verification scope expand | Low | Low | Karpathy §1.2 simplicity-first — keyboard nav + ARIA labels + focus-ring scope hold;screen reader full audit defer Beta hardening |

## 5. Day-by-Day Breakdown(rough)

| Day | Date | Focus |
|---|---|---|
| W15 D1 | 2026-07-07 | F1 V5 Eval Console — filter bar + Run config + 4-metric cards + Failed queries table |
| W15 D2 | 2026-07-08 | F2 V6 Debug View — 9-stage timeline accordion + Langfuse link;F1.5 W4 Reranker Shootout table |
| W15 D3 | 2026-07-09 | F3 Responsive + a11y polish + CO_W14_F4_error_boundary token cleanup;F4 Playwright install + config |
| W15 D4 | 2026-07-10 | F4 Golden-path E2E + admin path E2E + pixel diff baseline |
| W15 D5 | 2026-07-11 | F5 Tier 1 UI sprint cycle final closeout + W16+ phase folder kickoff |

**Day-by-day caveat**:plan §5 dates tentative;real-calendar W14 D5 F5 closeout cascade momentum may continue into W15 same-calendar-day collapse(per W12+W13+W14 closeout Time tracking calibration data — Tier 1 UI sprint phase capacity ~1-2 hr per phase if pivot momentum clean across cycle 4 of 4 final)。If W15 D6+ overflow:F5 absorb into W16+ D1。

## 6. Dependencies on Prior Phase

Carry-overs from `W14-admin-views/progress.md` retro § Carry-overs(W14 D5 F5 closeout):
- CO_W14_F4_error_boundary(W15 F3.4 token cleanup deliverable)→ W15 F3.4 deliverable exact match
- CO_F3a/b/c backend stub follow-up → defer Beta hardening(non W15 blocker per W15 PARTIAL PASS acceptance)
- CO_W14_smoke end-to-end browser smoke → W15 F4 Playwright E2E systematic subsume(deliverable exact match)
- CO_W15_F1 V5 Eval Console → W15 F1 deliverable exact match
- CO_W15_F2 V6 Debug View → W15 F2 deliverable exact match
- CO_W15_F3 Responsive + a11y + Playwright + pixel diff → W15 F3 + F4 deliverables exact match
- CO_F5_refresh / CO_F5_cookie / CO_F6a-c backend follow-ups(non W15 blocker;defer Beta hardening)
- CO16-CO19 W16+ Beta deploy(unchanged from W11+W12+W13+W14)

## 7. Plan Changelog

| Date | Change | Reason | Approver |
|---|---|---|---|
| 2026-06-10 | Initial draft(W14 D5 F5 closeout cascade rolling-JIT)| Per CLAUDE.md §10 R1 rolling-JIT;W14 closeout cascade per F5.3 deliverable;W15 immediate scope = W14 retro CO_W14_F4_error_boundary + CO_W15_F1-F3 + CO_W14_smoke exact match | Chris(stakeholder authorization same-session pivot momentum;W14 closeout PASS WITH SMOKE-USER-DEFERRED CAVEAT verdict landed)|
| 2026-06-10 (D1) | `status: draft → active` flip + W15 D1 F1 V5 Eval Console — 6 deviations:(1)F1.1 baseline mismatch(W12 F4.5 → W1 skeleton 15-line placeholder);(2)F1.3 metric naming mismatch(plan literal "Context Relevancy / Answer Relevancy" vs schema + wireframe "Correctness / Image Association");(3)F1.3 4-metric data display backend 501 stub mitigation pattern;(4)F1.5 static JSON file missing(inline RERANKER_SHOOTOUT const from W6 demo-prep.md §107-114 actual data);(5)F1.5 4-way comparison(W4 Karpathy §1.2 simplicity drop = effective 2-way + 2 dropped rows);(6)/eval admin shell wrap NEW `frontend/app/eval/layout.tsx` mirror admin layout | (1)Stakeholder authorization landed(user instruction option A "F1 V5 Eval Console implementation" pivot momentum cycle 4 of 4 final cont)。(2)`frontend/app/eval/page.tsx` actual = W1 skeleton 15-line placeholder + plan literal "rebuild from W12 F4.5 baseline" stale per Karpathy §1.1 think-before-coding upfront grep verification(**5th occurrence of plan literal vs actual code verification gap pattern**:W13 F1.5 + W14 F1.1 + W14 F2.2 + W15 F1.1 baseline + W15 F1.3 metric naming;CO_W14_process_grep_verify call-out reinforced — process improvement candidate accelerated)。(3)EvalReport schema in `backend/api/schemas/eval.py` defines 4 metrics as recall_at_5/faithfulness/correctness/image_association + design ref §2.5 wireframe codes "R@5/FFul/CRct/IAss" agree → align UI naming with schema+wireframe(plan literal "Context Relevancy / Answer Relevancy" outlier pre-W4 RAGAs redesign era)。(4)Backend `POST /eval/run` returns 501 NOT_IMPLEMENTED;采 W14 backend stub mitigation pattern(empty state Card + AlertCircle + Run CTA + stub note);ApiError.status === 501 → toast.info hint "docs/eval-methodology.md" non-breaking。(5)No `reranker_shootout*` artifact file exists per Glob check;采 inline `RERANKER_SHOOTOUT` const populated from W6 demo-prep.md §107-114 Q-A2 actual W6 D1 LIVE data(Cohere 1.000/0.841 + Azure 0.882/0.743 + Voyage/ZeroEntropy null status=dropped per W4 simplicity drop);3 status variants(recommended/fallback/dropped)preserve "ranking" semantics per design ref §3.6 PASS/FAIL color discipline。(6)design ref §2.5 wireframe shows admin sidebar but `/eval` was standalone W1 skeleton no layout;NEW eval/layout.tsx mirror admin/layout.tsx pattern(AuthProvider + QueryProvider + AdminShell)5-line non-invasive Karpathy §1.3 surgical;admin-shell NAV_ITEMS already lists `/eval` + SEGMENT_LABELS already covers `eval` for breadcrumb | Chris(user instruction option A "F1 V5 Eval Console implementation" + technical decisions per Karpathy §1.1 think-before-coding upfront verification cycle)|
| 2026-06-10 (D2) | W15 D2 F2 V6 Debug View — 4 deviations:(1)F2.1 "NEW route" file actually exists as W1 skeleton 15-line placeholder;(2)F2.2 "9-stage timeline" plan literal inconsistent with own 6-enumeration + design ref §2.6 wireframe;(3)F2.3 "shadcn Accordion (W12 D3 installed)" Accordion NOT in 19-primitive install list — 采 custom Collapsible per design ref §2.6 explicit permit;(4)F2.1+F2.5 trace data display backend 501 stub mitigation pattern + retry: false on useQuery | (1)`frontend/app/debug/[traceId]/page.tsx` actual = W1 skeleton 15-line placeholder per Glob check;plan literal "NEW route" stale(**6th occurrence of plan literal vs actual code grep verification gap pattern**:W13 F1.5 + W14 F1.1 + W14 F2.2 + W15 F1.1 baseline + W15 F1.3 metric naming + W15 F2.1 NEW route + W15 F2.2 9-vs-6 stage + W15 F2.3 Accordion not installed = pattern accelerating in W15;CO_W14_process_grep_verify call-out further reinforced — process improvement candidate W15 retro decision)。(2)Plan F2.2 internally inconsistent("9-stage timeline" header + 6-enumerated stages "Query Preprocessor / Hybrid Retrieval / Reranker / CRAG / LLM Synthesis / Final Response");design ref §2.6 wireframe shows 6 stages explicitly;采 wireframe-aligned 6-stage(plan enumeration also wins over plan header per spec internal consistency)。(3)Glob check `frontend/components/ui/accordion.tsx` returned 0 results;W12 D3 install list verified 19 primitives no Accordion(button/input/textarea/label/select/switch/slider/checkbox/card/separator/sheet/dialog/tabs/badge/sonner/skeleton/dropdown-menu/breadcrumb/avatar);design ref §2.6 explicitly permits "shadcn Accordion **OR custom Collapsible** primitive" — 采 custom Collapsible(useState + ChevronDown rotation transition + aria-expanded)per Karpathy §1.2 simplicity-first(2 use sites = stage cards repeating 6 times within same page;custom 1-component < new vendor + npm install + radix-ui peer + new shadcn registry file);H2 vendor lock preserved。(4)Backend `GET /debug/trace/{trace_id}` returns 501 NOT_IMPLEMENTED(W3+ implementation per Langfuse correlation per architecture.md §5.7);采 W14 BackendStubNote stub mitigation pattern(AlertCircle alert + stub note "Backend `GET /debug/trace/{trace_id}` is W3+ stub — pending Langfuse correlation per architecture.md §5.7" + 6-stage scaffold "—" duration + "Stage details pending backend trace API + Langfuse correlation");retry: false on useQuery避免 4-retry waste against 501 stub;Open in Langfuse link works independently(uses traceId from URL params);non-501 error states show destructive-bordered error banner | Chris(user instruction option A "F2 V6 Debug View implementation" + technical decisions per Karpathy §1.1 think-before-coding upfront verification cycle continued cycle 4 of 4 final cont)|
| 2026-06-10 (D3) | W15 D3 F3 Responsive + a11y polish + CO_W14_F4_error_boundary token cleanup — F3.1 Keyboard nav audit(1 a11y gap fixed:V6 Collapsible custom button focus-visible ring W15 D2 own mess Karpathy §1.3 surgical);F3.2 ARIA labels audit(0 new gaps;shadcn primitives via radix-ui automatically include role + aria-*);F3.3 Mobile responsive verify(0 regressions across 9 views;comprehensive sm:/md:/lg: coverage 18+ occurrences across admin/* + W15 D1+D2 eval+debug responsive intact);F3.4 error-boundary.tsx token cleanup REWRITE(6 hardcoded oklch → Tailwind tokens + native button/anchor → shadcn Button + automatic dark mode + focus-visible ring);**MAJOR MILESTONE** — grep `\[oklch` across **entire `frontend/`** now = 0 hits | F3 = pure polish phase per Karpathy §1.4 goal-driven verifiable success criteria(F3.1-F3.3 verification + F3.4 surgical token migration);F3.1 a11y gap = W15 D2 own mess per Karpathy §1.3「only clean your own mess」(custom Collapsible button missing focus-visible ring W15 D2 own miss → W15 D3 fix appropriate scope);F3.4 token cleanup map verified per design ref §1.1 swatches(L=0.88 light coral border → destructive/30;L=0.98 very light coral bg → destructive/10;L=0.45 chroma=0.18 hue=25 coral → text-destructive;L=0.55+L=0.45 neutral grey → muted-foreground;L=0.92 grey border → border via shadcn Button outline default;L=0.94 grey hover → muted via shadcn Button hover default);native `<button>` + `<a>` → shadcn Button + Button asChild = visual consistency with admin UI + automatic dark mode + focus-visible ring(a11y double-win)。**Major milestone**:W12 D2 strict baseline `grep \[oklch frontend/app/admin/` 0 hits NOW EXTENDS to entire `frontend/`(global token discipline complete vs previously confined to admin scope per W14 F4.3 audit boundary);CO_W14_F4_error_boundary closed | Chris(user instruction option A "F3 Responsive + a11y polish + CO_W14_F4_error_boundary token cleanup" + technical decisions per Karpathy §1.1 think-before-coding upfront verification + §1.3 surgical scope completion)|
| 2026-06-10 (D4) | W15 D4 F4 Playwright E2E + pixel diff baseline harness — 2 deviations:(1)plan F4 spec ref note "CLAUDE.md §3.2 test framework Vitest + React Testing Library baseline preserved;Playwright additive" stale per Glob check(no Vitest infrastructure exists);(2)plan F4.4 "frontend/tests/e2e/screenshots/baseline/" custom path → Playwright convention `*.spec.ts-snapshots/` next to test files(simpler + tool-default per Karpathy §1.2);Playwright @playwright/test 1.59.1 installed(R8 proxy 唔 block npm registry);Tier 1 baseline scope = Chromium-only + sequential exec + 4 golden-path tests + 5 admin-path tests + 5 visual baseline tests;`npx playwright install chromium` browser binaries deferred to user smoke per CLAUDE.md §13 + plan F4.5 PARTIAL PASS;CI integration deferred W16+ Beta hardening per plan F4.5 | (1)`frontend/tests/` Glob returned 0 results + no vitest config + no @vitest/* in devDependencies → CLAUDE.md §3.2 "Vitest + React Testing Library" 從未 set up;**9th occurrence of plan literal vs actual code grep verification gap pattern**(W13 F1.5 + W14 F1.1 + W14 F2.2 + W15 F1.1 baseline + W15 F1.3 metric naming + W15 F2.1 NEW route + W15 F2.2 9-vs-6 stage + W15 F2.3 Accordion not installed + W15 F4 Vitest baseline);CO_W14_process_grep_verify call-out continued reinforcement;Playwright independent setup per Karpathy §1.3 surgical scope hold(Vitest infrastructure out of W15 F4 strict scope per plan literal "additive")。(2)Plan F4.4 custom screenshots/baseline/ path vs Playwright tool default `*.spec.ts-snapshots/` next to test files;采 tool default per Karpathy §1.2 simplicity-first(Playwright auto-organizes snapshots vs custom directory layer)。`@playwright/test ^1.59.1` install via `pnpm add -D` succeeded 1m 3s w/ 4 packages added(R8 proxy 唔 block npm registry — different endpoint vs azure-communication-email which IS blocked per W13 F6 lazy import design);webServer config auto-starts `pnpm dev` w/ NEXT_PUBLIC_AUTH_MOCK=true env so MSAL bypasses real Entra ID round-trip;backend uvicorn = user-driven separately per CLAUDE.md §13;Tier 1 baseline scope explicit:Chromium only(simplicity drop firefox/webkit per plan §4 risk mitigation),sequential test exec(in-memory KB state race),trace/screenshot/video retain-on-failure(debug aid),5 representative pixel diff baseline views(V7+V8+V9+V2+V5 vs all 9 = scope manageable + Tier 1 acceptance preserved);CI integration `forbidOnly` + `reuseExistingServer` flags ready for W16+ flip when Beta hardening triggers;**subsumes manual smoke deferred backlog across W12+W13+W14 cycles** per plan §F4 systematic subsume goal | Chris(user instruction option A "F4 Playwright E2E + pixel diff baseline harness" + technical decisions per Karpathy §1.1 think-before-coding upfront verification + §1.2 simplicity-first scope discipline)|

---

**Lifecycle reminder**:呢份 plan `status=draft`(等 W15 D1 active flip post stakeholder authorization)。重大 deviation 入第 7 節 changelog。Sister sprint W16-beta-deploy phase folder **唔會** pre-create(per CLAUDE.md §10 R1 rolling-JIT — 每 phase kickoff 先建)。
